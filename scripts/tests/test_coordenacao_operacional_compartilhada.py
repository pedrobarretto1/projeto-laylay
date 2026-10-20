"""Fronteira textual comum; cada ato conserva modalidade, fonte e autoridade."""
import pytest

from mente_laylay.cognicao.modalidade_turno import (
    classificar_modalidade_turno, autoriza_execucao_efetiva, fontes_textuais_dos_segmentos,
)
from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia

CONECTORES = [' e ', ' e depois ', ' em seguida ', ' depois ', ' então ', ' e então ', ' e em seguida ']


@pytest.mark.parametrize('conector', CONECTORES)
@pytest.mark.parametrize('esquerda,direita', [
    ('abre a calculadora', 'gire 90 graus para a esquerda'),
    ('cria a pasta Pesquisa', 'pausa a música'),
    ('liga a lâmpada', 'abre o navegador'),
])
def test_coordenacao_inteira_chega_aos_atos_e_etapas_sem_sobra_de_conector(conector, esquerda, direita):
    texto = esquerda + conector + direita
    turno = classificar_modalidade_turno(texto)
    assert [s['texto'] for s in turno['segmentos']] == [esquerda.lower(), direita.lower()]
    assert all(autoriza_execucao_efetiva(s) for s in turno['segmentos'])
    assert segmentar_comandos_em_cadeia(texto) == [esquerda, direita]


@pytest.mark.parametrize('conector', CONECTORES)
def test_condicao_da_segunda_oracao_nao_vira_autorizacao_ao_remover_conector(conector):
    turno = classificar_modalidade_turno('abre a calculadora' + conector + 'se eu confirmar, gire 90 graus para a esquerda')
    assert len(turno['segmentos']) == 2
    assert turno['segmentos'][0]['texto'] == 'abre a calculadora'
    assert autoriza_execucao_efetiva(turno['segmentos'][0])
    segundo = turno['segmentos'][1]
    assert segundo['texto'].startswith('se eu confirmar,')
    assert not autoriza_execucao_efetiva(segundo), 'a condição deve continuar vinculada ao giro'


@pytest.mark.parametrize('conector', CONECTORES)
@pytest.mark.parametrize('moldura', [
    'Se eu confirmar, {comando}',
    '{comando} só se eu confirmar',
    'Não {comando}',
    'Explica a frase "{comando}"',
    'Ontem eu disse "{comando}"',
    'Você consegue abrir a calculadora{conector}girar 90 graus para a esquerda?',
])
def test_conector_nao_transforma_condicao_negacao_relato_ou_capacidade_em_ordem(conector, moldura):
    comando = 'abre a calculadora' + conector + 'gire 90 graus para a esquerda'
    turno = classificar_modalidade_turno(moldura.format(comando=comando, conector=conector))
    assert not any(autoriza_execucao_efetiva(s) for s in turno['segmentos'])


@pytest.mark.parametrize('conector', CONECTORES)
def test_literal_com_conector_e_fonte_original_preservados(conector):
    esquerda = 'Abre o arquivo "Meu E Depois.txt"'
    direita = 'pausa a música'
    texto = esquerda + conector + direita
    turno = classificar_modalidade_turno(texto)
    assert len(turno['segmentos']) == 2
    fontes = [f.como_dict() for f in fontes_textuais_dos_segmentos(texto, turno['segmentos'])]
    assert [f['texto_original'] for f in fontes] == [esquerda, direita]
    for fonte in fontes:
        inicio, fim = fonte['intervalo']
        assert texto[inicio:fim] == fonte['texto_original']
        assert not fonte['autoriza_execucao'] and not fonte['comprova_efeito']
    assert segmentar_comandos_em_cadeia(texto) == [esquerda, direita]


@pytest.mark.parametrize('conector', CONECTORES)
def test_literal_malformado_nao_libera_etapa_externa(conector):
    texto = 'Abre o arquivo "Meu E Depois.txt' + conector + 'gire 90 graus para a esquerda'
    turno = classificar_modalidade_turno(texto)
    assert not autoriza_execucao_efetiva(turno)
    assert len(segmentar_comandos_em_cadeia(texto)) == 1


@pytest.mark.parametrize('texto', [
    'Liga a luz e o ventilador', 'cria a pasta E Depois',
    'abre o arquivo depois.txt', 'coloca vermelho, azul e verde',
])
def test_token_em_nome_ou_enumeracao_nao_cria_etapa(texto):
    assert len(classificar_modalidade_turno(texto)['segmentos']) == 1
    assert len(segmentar_comandos_em_cadeia(texto)) == 1


@pytest.mark.parametrize('inicio', ['Depois', 'Em seguida', 'Então', 'E depois'])
def test_modificador_inicial_nao_e_apagado_como_se_fosse_coordenacao(inicio):
    from mente_laylay.cognicao.normalizacao_linguagem import remover_conector_discursivo_inicial
    texto = inicio + ' gire 90 graus para a esquerda'
    # O contrato lexical de coordenação exige dois núcleos. A projeção do
    # "e" inicial existente continua limitada a esse token, sem apagar tempo.
    projetado = remover_conector_discursivo_inicial(texto)
    assert projetado.lower().startswith(inicio.lower().removeprefix('e '))
    assert len(classificar_modalidade_turno(texto)['segmentos']) == 1
    assert not autoriza_execucao_efetiva(classificar_modalidade_turno(texto))


@pytest.fixture(scope='module', params=['dispatcher', 'cadeia'])
def coordenacao_instalada(request, tmp_path_factory):
    import os
    from pathlib import Path
    from scripts.tests.test_aspectos_resultado_imediato import respostas_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_CONECTOR_COMPOSTO_TESTE', ' e depois ')
        ambiente.setenv('LAYLAY_ROTA_COMPOSTO_TESTE', request.param)
        ambiente.setenv('LAYLAY_COLETAR_GUARDAS_COORDENACAO', '1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_COORDENACAO'):
            ambiente.setenv('LAYLAY_EVIDENCIA_DECISAO', str(Path(pasta) / f'composicao_{request.param}.json'))
        return request.param, respostas_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('modo', ['fiel', 'causa_inventada', 'sucesso_total'])
def test_coordenacao_real_chega_ao_receipt_sem_forcar_autoridade_agregada(modo, coordenacao_instalada):
    rota, dados = coordenacao_instalada
    assert all(dados['owners'].values())
    c = dados['compostos_aspectos'][modo]
    turno = c['turno_antes_execucao']
    assert [s['texto'] for s in turno['segmentos']] == ['abre a calculadora', 'gire 90 graus para a esquerda']
    resultados = c['plano']['comandos']
    assert [r['intent'] for r in resultados] == ['APP_OPEN', 'CORPO_MOVER']
    assert [r['confirmado'] for r in resultados] == [True, False]
    assert resultados[-1]['status'] == 'falha_execucao', 'deve chegar ao receipt, sem recusa anterior de autorização'
    assert c['novos_giros'] == 1 and len(c['textos']) == 1
    assert 'Confirmação registrada de "parada elétrica"' in c['textos'][0]
    assert 'não configurou' not in c['textos'][0] and 'Concluí o giro' not in c['textos'][0]


def test_coordenacao_real_nao_empresta_autorizacao_do_aplicativo_ao_giro_condicionado(coordenacao_instalada):
    _, dados = coordenacao_instalada
    assert all(dados['owners'].values())
    c = dados['guarda_coordenacao']
    assert [s['texto'] for s in c['turno']['segmentos']] == [
        'abre a calculadora', 'se eu confirmar, gire 90 graus para a esquerda']
    assert [autoriza_execucao_efetiva(s) for s in c['turno']['segmentos']] == [True, False]
    assert c['novos_giros'] == 0, 'pedido proposto não substitui autorização atual'
    assert all(r['confirmado'] is not True for r in c['plano']['comandos'] if r['intent'] == 'CORPO_MOVER')
    assert c['textos'], 'entrada consumida precisa de conclusão observável'
