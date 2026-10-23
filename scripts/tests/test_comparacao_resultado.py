"""Diferença entre fontes vinculadas não é prova de efeito ou causa física."""
import pytest
from copy import deepcopy
from dataclasses import asdict, replace, FrozenInstanceError
from decimal import Decimal, localcontext

from mente_laylay.memoria_mental.decisao_observada import (
    ExpectativaResultado, MedicaoObservada, ExplicacaoOcorrencia, ComparacaoResultado, comparacoes_resultado,
)
from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia, avaliar_fala_historica

from scripts.tests.test_expectativa_ocorrencia import expectativas_instaladas as _expectativas_instaladas


@pytest.fixture(scope='module')
def expectativas_instaladas(tmp_path_factory):
    import os
    from pathlib import Path
    with pytest.MonkeyPatch.context() as ambiente:
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_EXPECTATIVAS'):
            destino = Path(pasta) / 'comparacao'
            destino.mkdir(parents=True, exist_ok=True)
            ambiente.setenv('LAYLAY_EVIDENCIA_EXPECTATIVAS', str(destino))
        return _expectativas_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,diferenca', [('meta90', '-66.25'), ('meta180', '-156.25'), ('meta_direita', '113.75')])
def test_composicao_deriva_diferenca_sem_perder_fontes_ou_concluir_causa(nome, diferenca, expectativas_instaladas):
    assert all(expectativas_instaladas['owners'].values())
    c = expectativas_instaladas['medidas_ocorrencias'][nome]
    episodio = c['fonte']['episodios'][0]
    assert episodio['expectativas'] == c['inicio_ocorrencia']['ocorrencia']['expectativas']
    assert episodio['medicoes'][0]['valor'] == 23.75
    assert episodio['confirmado'] is False
    assert f'Diferença aritmética (medido menos solicitado): {diferenca} "graus".' in c['fala_owner'], 'fronteira: fontes presentes, mas relação quantitativa não é realizada'
    assert 'não comprova conclusão nem explica a causa do resultado' in c['fala_owner']
    assert c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    for turno in c['turnos']:
        assert turno['textos'] == [c['fala_owner']] and not turno['executores']
        assert turno['codec_integral'] and turno['contexto_fechado']


@pytest.mark.parametrize('nome', ['sem_leitura', 'pulso'])
def test_composicao_sem_duas_fontes_nao_completa_comparacao(nome, expectativas_instaladas):
    c = expectativas_instaladas['medidas_ocorrencias'][nome]
    assert not c['fonte']['episodios'][0]['medicoes']
    assert 'Diferença aritmética' not in c['fala_owner']


def episodio_comparavel(*, owner='executor_corpo', grandeza='rotação relativa', unidade='graus',
        solicitado=90, medido=23.75, confirmado=False):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e = episodio(owner=owner, confirmado=confirmado)
    meta = ExpectativaResultado(e.id, e.owner, grandeza, solicitado, unidade,
        'captura_validada_do_owner', e.iniciada_em, referencial='referencia_do_owner_v1')
    medida = MedicaoObservada(e.id, e.owner, grandeza, medido, unidade,
        'retorno_qualificado_do_owner', 'Leitura parcial; não comprova conclusão.', referencial=meta.referencial)
    return replace(e, expectativas=(meta,), medicoes=(medida,))


def realizar(e):
    return realizacoes_explicacao_ocorrencia(ExplicacaoOcorrencia('c', 'Por que fez essa ação?', (e,), 'unica'))[0]


@pytest.mark.parametrize('owner,grandeza,unidade', [('executor_corpo', 'rotação relativa', 'graus'),
    ('executor_arquivos', 'tamanho solicitado', 'bytes'), ('executor_volume', 'volume configurado', 'percentual')])
@pytest.mark.parametrize('confirmado', [True, False, None])
def test_contrato_compartilhado_conserva_fontes_e_confirmacao(owner, grandeza, unidade, confirmado):
    e = episodio_comparavel(owner=owner, grandeza=grandeza, unidade=unidade, confirmado=confirmado)
    antes = deepcopy(e)
    c, = comparacoes_resultado(e)
    assert c.expectativa is e.expectativas[0] and c.medicao is e.medicoes[0]
    assert c.diferenca == Decimal('-66.25')
    assert not c.autoriza_execucao and not c.confirma_efeito
    assert e.confirmado is confirmado and e == antes
    fala = realizar(e)
    assert '-66.25' in fala and unidade in fala and 'não comprova conclusão nem explica a causa' in fala
    with pytest.raises(FrozenInstanceError): c.medicao = replace(c.medicao, valor=999)


@pytest.mark.parametrize('solicitado,medido,esperado', [
    (90, 0, '-90'), (90, -17.25, '-107.25'), (90, 110.5, '20.5'),
    (-90, -23.75, '66.25'), (-90, 23.75, '113.75'), (90, 90, '0'),
    (0.1, 0.3, '0.2'), (0, -0.0, '0'), (2048, 1024, '-1024'),
    (1e308, -1e308, '-2e308'), (1e-300, 1e300, None),
])
def test_diferenca_tem_sinal_operacao_e_aritmetica_decimal_explicitos(solicitado, medido, esperado):
    e = episodio_comparavel(solicitado=solicitado, medido=medido)
    c, = comparacoes_resultado(e)
    with localcontext() as contexto:
        contexto.prec = 1000
        exato = Decimal(str(medido)) - Decimal(str(solicitado))
    assert c.diferenca == exato
    if esperado is not None: assert c.diferenca == Decimal(esperado)
    fala = realizar(e)
    assert 'medido menos solicitado' in fala and 'não comprova conclusão' in fala
    assert 'faltaram' not in fala and 'atingiu a meta' not in fala
    assert e.confirmado is False, 'diferença zero não substitui receipt de conclusão'


@pytest.mark.parametrize('campo,valor', [('ocorrencia_id', 'outra'), ('owner', 'outro'),
    ('grandeza', 'posição absoluta'), ('unidade', 'radianos'), ('referencial', 'outro_inicio'), ('referencial', '')])
def test_comparacao_nao_relaciona_fontes_incompativeis(campo, valor):
    e = episodio_comparavel()
    with pytest.raises(ValueError): ComparacaoResultado(e.expectativas[0], replace(e.medicoes[0], **{campo: valor}))


@pytest.mark.parametrize('campo,valor', [('grandeza', 'posição absoluta'), ('unidade', 'radianos'),
    ('referencial', 'outro_inicio'), ('referencial', '')])
def test_realizador_preserva_fontes_incompativeis_sem_converter_ou_subtrair(campo, valor):
    e = episodio_comparavel()
    e = replace(e, medicoes=(replace(e.medicoes[0], **{campo: valor}),))
    assert not comparacoes_resultado(e)
    fala = realizar(e)
    assert 'Valor solicitado' in fala and 'Medição registrada' in fala
    assert 'Diferença aritmética' not in fala


@pytest.mark.parametrize('fonte', ['meta', 'medicao'])
@pytest.mark.parametrize('valor', [None, True, 1, ' referencial', 'ref ', 'x' * 241])
def test_referencial_invalido_nao_e_promovido_a_compatibilidade(fonte, valor):
    e = episodio_comparavel()
    with pytest.raises(ValueError): replace(e.expectativas[0] if fonte == 'meta' else e.medicoes[0], referencial=valor)


@pytest.mark.parametrize('ausente', ['meta', 'medicao', 'ambas', 'referencial_meta', 'referenciais', 'json'])
def test_sem_fontes_vinculadas_ou_referencial_legado_nao_ha_derivacao(ausente):
    e = episodio_comparavel()
    if ausente in ('meta', 'ambas'): e = replace(e, expectativas=())
    if ausente in ('medicao', 'ambas'): e = replace(e, medicoes=())
    if ausente in ('referencial_meta', 'referenciais'): e = replace(e, expectativas=(replace(e.expectativas[0], referencial=''),))
    if ausente == 'referenciais': e = replace(e, medicoes=(replace(e.medicoes[0], referencial=''),))
    assert not comparacoes_resultado(asdict(e) if ausente == 'json' else e)
    if ausente != 'json': assert 'Diferença aritmética' not in realizar(e)


def test_duas_observacoes_compativeis_nao_escolhem_numero_por_ordem():
    e = episodio_comparavel()
    m = replace(e.medicoes[0], metodo='outro_metodo', valor=88)
    for medidas in ((e.medicoes[0], m), (m, e.medicoes[0])):
        fonte = replace(e, medicoes=medidas)
        assert not comparacoes_resultado(fonte)
        fala = realizar(fonte)
        assert '23.75' in fala and '88' in fala and 'Diferença aritmética' not in fala


def test_json_das_fontes_nao_constroi_derivacao_tipada():
    e = episodio_comparavel()
    for a, b in ((asdict(e.expectativas[0]), e.medicoes[0]), (e.expectativas[0], asdict(e.medicoes[0]))):
        with pytest.raises(ValueError): ComparacaoResultado(a, b)


@pytest.mark.parametrize('referencial', [None, 'outro_inicio', ''])
def test_historico_nao_reconstitui_referencial_da_meta_pelo_metodo_ou_estado_vivo(referencial):
    from scripts.tests.test_expectativa_ocorrencia import historico_com_meta
    estado, runtime, _, registro = historico_com_meta()
    historico = estado.obter_copia('mental', 'historico_corporal', [])
    if referencial is None: historico[0]['expectativas'][0].pop('referencial')
    else: historico[0]['expectativas'][0]['referencial'] = referencial
    estado.atualizar_campos('mental', historico_corporal=historico)
    antes = estado.retrato_dominio('mental')
    f = runtime.recuperar_explicacao(f"Por que fez esse gesto {registro['id']}?", turno={'id': 'consulta'})
    assert f.episodios[0].expectativas[0].valor == 90
    assert f.episodios[0].medicoes[0].valor == 23.75
    assert not comparacoes_resultado(f.episodios[0])
    assert estado.retrato_dominio('mental') == antes


@pytest.mark.parametrize('adulteracao', ['numero', 'sinal', 'conclusao', 'causa', 'ressalva'])
def test_revisao_compartilhada_recusa_derivacao_adulterada_sem_tratar_autoria_como_prova(adulteracao):
    from scripts.tests.test_explicacao_ocorrencia import plano
    e = episodio_comparavel()
    fonte = ExplicacaoOcorrencia('consulta', 'Por que você fez esse gesto?', (e,), 'unica')
    p = plano(fonte)
    fiel = realizacoes_explicacao_ocorrencia(fonte)[0]
    proposta = {'numero': fiel.replace('-66.25', '-60'), 'sinal': fiel.replace('-66.25', '66.25'),
        'conclusao': fiel + ' Portanto, concluí a operação.', 'causa': fiel + ' Isso ocorreu porque o motor travou.',
        'ressalva': fiel.replace('Esta diferença não comprova conclusão nem explica a causa do resultado.', '')}[adulteracao]
    assert proposta != fiel
    antes = deepcopy(p)
    avaliacao = avaliar_fala_historica(proposta, plano=p)
    assert avaliacao['fala'] == fiel and avaliacao['autoriza_execucao'] is False
    assert p == antes
    assert avaliar_fala_historica(fiel, plano=p)['fala'] == fiel
