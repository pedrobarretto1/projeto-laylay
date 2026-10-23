"""Motivo da indisponibilidade pertence ao contrato, não à proposta da LLM."""
import os
from copy import deepcopy
from dataclasses import asdict, replace, FrozenInstanceError
from pathlib import Path

import pytest

from scripts.tests.test_expectativa_ocorrencia import expectativas_instaladas as _expectativas
from scripts.tests.test_comparacao_resultado import episodio_comparavel, realizar
from mente_laylay.memoria_mental.decisao_observada import (
    AvaliacaoComparacaoResultado, avaliar_comparacoes_resultado, comparacoes_resultado, ExplicacaoOcorrencia,
)
from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica, realizacoes_explicacao_ocorrencia


@pytest.fixture(scope='module')
def limites_instalados(tmp_path_factory):
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_LIMITES_COMPARACAO', '1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_EXPECTATIVAS'):
            destino = Path(pasta) / 'limites'
            destino.mkdir(parents=True, exist_ok=True)
            ambiente.setenv('LAYLAY_EVIDENCIA_EXPECTATIVAS', str(destino))
        return _expectativas.__wrapped__(tmp_path_factory)


MOTIVOS = {
    'sem_meta': 'Não há valor solicitado registrado nesta fonte para comparação.',
    'sem_medicao': 'Não há medição qualificada nesta fonte para comparar com o valor solicitado.',
    'sem_referencial': 'A meta não tem referencial registrado para comparação.',
    'referencial_distinto': 'Meta e medições não têm um referencial comum registrado para comparação.',
    'unidade_distinta': 'Não há medição na mesma unidade da meta; não vou converter as unidades para comparar.',
    'grandeza_distinta': 'Não há medição da mesma grandeza da meta para comparação.',
    'sem_fontes': 'Não há valor solicitado nem medição qualificada nesta fonte para comparação.',
}


@pytest.mark.parametrize('nome', tuple(MOTIVOS))
def test_composicao_explica_limite_da_comparacao_sem_inventar_causa(nome, limites_instalados):
    assert all(limites_instalados['owners'].values())
    c = limites_instalados['medidas_ocorrencias'][nome]
    episodio = c['fonte']['episodios'][0]
    assert episodio['id'] == c['experiencia']['id']
    if nome not in ('sem_medicao', 'sem_fontes'): assert episodio['medicoes'][0]['valor'] == 23.75
    assert 'Diferença aritmética' not in c['fala_owner']
    assert MOTIVOS[nome] in c['fala_owner'], 'primeira perda: ausência de comparação chega sem motivo explícito à entrega'
    assert c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    for turno in c['turnos']:
        assert turno['codec_integral'] and turno['contexto_fechado']
        assert turno['textos'] == [c['fala_owner']] and not turno['executores']


def test_composicao_com_fontes_compativeis_preserva_calculo(limites_instalados):
    c = limites_instalados['medidas_ocorrencias']['comparavel']
    assert 'medido menos solicitado): -66.25 "graus".' in c['fala_owner']
    assert not any(motivo in c['fala_owner'] for motivo in MOTIVOS.values())


ESTADOS = {
    'sem_fontes': 'fontes_ausentes', 'sem_meta': 'meta_ausente', 'sem_medicao': 'medicao_ausente',
    'grandeza_distinta': 'grandeza_sem_correspondencia', 'unidade_distinta': 'unidade_distinta',
    'sem_referencial': 'referencial_meta_ausente', 'referencial_medicao': 'referencial_medicao_ausente',
    'referencial_distinto': 'referencial_distinto', 'ambigua': 'medicao_ambigua', 'comparavel': 'comparavel',
}
FALAS = MOTIVOS | {
    'referencial_medicao': 'Não há medição com o referencial da meta; há medição sem referencial registrado.',
    'ambigua': 'Há mais de uma medição compatível; esta fonte não define qual usar na comparação.',
}


def cenario(nome, **campos):
    e = episodio_comparavel(**campos)
    if nome in ('sem_fontes', 'sem_meta'): e = replace(e, expectativas=())
    if nome in ('sem_fontes', 'sem_medicao'): e = replace(e, medicoes=())
    if nome == 'sem_referencial': e = replace(e, expectativas=(replace(e.expectativas[0], referencial=''),))
    if nome == 'referencial_medicao': e = replace(e, medicoes=(replace(e.medicoes[0], referencial=''),))
    if nome == 'referencial_distinto': e = replace(e, medicoes=(replace(e.medicoes[0], referencial='outro_inicio'),))
    if nome == 'unidade_distinta': e = replace(e, medicoes=(replace(e.medicoes[0], unidade='outra unidade'),))
    if nome == 'grandeza_distinta': e = replace(e, medicoes=(replace(e.medicoes[0], grandeza='outra grandeza'),))
    if nome == 'ambigua': e = replace(e, medicoes=(*e.medicoes, replace(e.medicoes[0], metodo='outro_metodo')))
    return e


@pytest.mark.parametrize('nome', tuple(ESTADOS))
@pytest.mark.parametrize('owner,grandeza,unidade', [('executor_corpo', 'rotação relativa', 'graus'),
    ('executor_arquivos', 'tamanho solicitado', 'bytes'), ('executor_volume', 'volume configurado', 'percentual')])
def test_estado_e_realizacao_compartilhados_conservam_fontes_e_receipt(nome, owner, grandeza, unidade):
    e = cenario(nome, owner=owner, grandeza=grandeza, unidade=unidade)
    antes = deepcopy(e)
    a, = avaliar_comparacoes_resultado(e)
    assert a.episodio is e and a.estado == ESTADOS[nome]
    assert not a.autoriza_execucao and not a.confirma_efeito
    assert e.confirmado is False and e == antes
    assert bool(a.comparacao) is (nome == 'comparavel')
    assert comparacoes_resultado(e) == ((a.comparacao,) if nome == 'comparavel' else ())
    fala = realizar(e)
    if nome != 'comparavel':
        assert FALAS[nome] in fala and 'Diferença aritmética' not in fala
    else:
        assert 'medido menos solicitado): -66.25' in fala
    if e.medicoes: assert 'Medição registrada' in fala and '23.75' in fala
    if e.expectativas: assert 'Valor solicitado' in fala and '90' in fala
    assert 'sensor falhou' not in fala and 'não houve movimento' not in fala


@pytest.mark.parametrize('nome', ['sem_medicao', 'sem_meta', 'sem_fontes', 'ambigua', 'unidade_distinta'])
@pytest.mark.parametrize('confirmado', [True, None])
def test_indisponibilidade_numerica_nao_reescreve_confirmacao_do_owner(nome, confirmado):
    e = cenario(nome, confirmado=confirmado)
    assert avaliar_comparacoes_resultado(e)[0].estado == ESTADOS[nome]
    realizar(e)
    assert e.confirmado is confirmado


@pytest.mark.parametrize('alteracao', ['json_episodio', 'json_meta', 'outra_meta', 'copia_meta', 'ausencia_falsa'])
def test_avaliacao_nao_recebe_fontes_reidratadas_ou_meta_estranha(alteracao):
    e = episodio_comparavel()
    episodio, meta = e, e.expectativas[0]
    if alteracao == 'json_episodio': episodio = asdict(e)
    if alteracao == 'json_meta': meta = asdict(meta)
    if alteracao == 'outra_meta': meta = replace(meta, ocorrencia_id='outra')
    if alteracao == 'copia_meta': meta = replace(meta)
    if alteracao == 'ausencia_falsa': meta = None
    with pytest.raises(ValueError): AvaliacaoComparacaoResultado(episodio, meta)


@pytest.mark.parametrize('nome', tuple(ESTADOS))
def test_estado_derivado_nao_pode_ser_fornecido_ou_alterado_pela_autoria(nome):
    e = cenario(nome)
    a, = avaliar_comparacoes_resultado(e)
    with pytest.raises(TypeError): AvaliacaoComparacaoResultado(e, a.expectativa, estado='comparavel')
    with pytest.raises(FrozenInstanceError): a.episodio = episodio_comparavel()
    assert not avaliar_comparacoes_resultado(asdict(e))


def test_metas_distintas_tem_limites_proprios_sem_emprestar_medicao_ou_falha():
    e = episodio_comparavel()
    outra = replace(e.expectativas[0], grandeza='distância', unidade='metros')
    e = replace(e, expectativas=(*e.expectativas, outra))
    a, b = avaliar_comparacoes_resultado(e)
    assert a.estado == 'comparavel' and b.estado == 'grandeza_sem_correspondencia'
    assert len(comparacoes_resultado(e)) == 1
    fala = realizar(e)
    assert 'Comparação de "rotação relativa" em "graus":' in fala
    assert 'Comparação de "distância" em "metros":' in fala
    assert fala.count('Diferença aritmética') == 1 and FALAS['grandeza_distinta'] in fala


@pytest.mark.parametrize('ordem', [False, True])
def test_ambiguidade_de_medicoes_iguais_nao_e_resolvida_por_ordem_ou_valor(ordem):
    e = cenario('ambigua')
    if ordem: e = replace(e, medicoes=e.medicoes[::-1])
    assert avaliar_comparacoes_resultado(e)[0].estado == 'medicao_ambigua'
    assert not comparacoes_resultado(e)


def test_medicao_incompativel_extra_nao_apaga_unica_compativel_nem_impede_controle_legitimo():
    e = episodio_comparavel()
    extra = replace(e.medicoes[0], referencial='outro_inicio', metodo='outro_metodo')
    for medidas in ((e.medicoes[0], extra), (extra, e.medicoes[0])):
        a, = avaliar_comparacoes_resultado(replace(e, medicoes=medidas))
        assert a.estado == 'comparavel' and a.comparacao.medicao is e.medicoes[0]


@pytest.mark.parametrize('nome', ['sem_meta', 'sem_medicao', 'sem_referencial', 'referencial_distinto',
    'unidade_distinta', 'grandeza_distinta', 'ambigua', 'referencial_medicao', 'sem_fontes'])
@pytest.mark.parametrize('alteracao', ['troca_motivo', 'causa', 'conclusao', 'remocao_limite'])
def test_revisao_recusa_limite_trocado_ou_causa_inventada_sem_promover_proposta_a_prova(nome, alteracao):
    from scripts.tests.test_explicacao_ocorrencia import plano
    e = cenario(nome)
    f = ExplicacaoOcorrencia('consulta', 'Por que você fez esse gesto?', (e,), 'unica')
    p = plano(f)
    antes = deepcopy(p)
    fiel = realizacoes_explicacao_ocorrencia(f)[0]
    propostas = {'troca_motivo': fiel.replace(FALAS[nome], 'Não comparei porque o sensor falhou.'),
        'causa': fiel + ' O motor travou.', 'conclusao': fiel + ' Portanto, concluí tudo.',
        'remocao_limite': fiel.replace(FALAS[nome], '')}
    proposta = propostas[alteracao]
    assert proposta != fiel
    revisao = avaliar_fala_historica(proposta, plano=p)
    assert revisao['fala'] == fiel and revisao['problemas'] and not revisao['autoriza_execucao']
    assert p == antes
