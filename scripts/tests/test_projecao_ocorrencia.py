"""Correlação textual idempotente não concede autorização ou efeito."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.decisao_turno import motivo_incoerencia_contratos_turno
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from tests.test_vinculo_proposta_turno import _atribuir_id, _filtrar, _frame, _principal
from tests.test_publicacao_ocorrencia_turno import _publicar
from tests.test_papo_casual_composicao import coletar, proposta

CASO = json.loads((Path(__file__).parent / 'fixtures/publicacao_rodada18.json').read_text(encoding='utf8'))


@pytest.mark.parametrize('fim', [' ', '\t', '\n', '\u00a0', 'x'])
@pytest.mark.parametrize('tamanho', [499, 500, 501, 650])
def test_recorte_publico_da_mesma_ocorrencia_preserva_vinculo_e_writer(fim, tamanho):
    inicio = 'Podemos imaginar uma história? '
    borda = min(499, tamanho - 1)
    texto = inicio.ljust(borda, 'a') + fim + 'b' * (tamanho - borda - 1)
    frame = _frame(texto)
    principal = _principal(frame, texto)
    assert motivo_incoerencia_contratos_turno(*[frame[k] for k in (
        'turno_atual', 'plano_turno_atual', 'retrato_turno_atual')]) == ''
    resultado = _filtrar(frame, [], principal)
    assert resultado['ocorrencia_vinculada'] and resultado['proposta_vinculada']
    assert not resultado['comandos'] and not principal.autoriza_execucao
    estado = EstadoCompartilhadoRuntime(mental=frame)
    assert _publicar(estado, 'resposta_planejada', principal, fala='Podemos imaginar.')['fase'] == 'resposta_planejada'


@pytest.mark.parametrize('alteracao', ['id', 'caractere', 'espaco_interno', 'operacional'])
def test_normalizacao_da_borda_nao_apaga_divergencias_reais(alteracao):
    texto = 'Podemos imaginar? '.ljust(499, 'a') + ' ' + 'continuação'
    frame = _frame(texto)
    principal = _principal(frame, texto)
    if alteracao == 'id':
        _atribuir_id(frame, str(frame['turno_atual']['id']) + '-outro')
    elif alteracao == 'operacional':
        frame['turno_atual']['texto_operacional_efetivo'] = 'abre a Calculadora'
    else:
        original = frame['plano_turno_atual']['texto_usuario']
        frame['plano_turno_atual']['texto_usuario'] = original.replace(
            'Podemos imaginar', 'Podemos  imaginar' if alteracao == 'espaco_interno' else 'Podemos desenhar')
    resultado = _filtrar(frame, [{'intent': 'APP_OPEN', 'params': {'nome_app': 'Calculadora'}}], principal)
    assert not resultado['ocorrencia_vinculada'] and not resultado['comandos']
    estado = EstadoCompartilhadoRuntime(mental=frame)
    antes = estado.snapshot()
    assert _publicar(estado, 'resposta_planejada', principal, fala='Outra resposta.') == {}
    assert estado.snapshot() == antes


@pytest.mark.parametrize('intent', ['APP_OPEN', 'IOT_CONTROL', 'DELETE_ITEM', 'PLAYLIST_CREATE'])
def test_sufixo_fora_da_projecao_nao_concede_autorizacao(intent):
    texto = 'Podemos imaginar? '.ljust(499, 'a') + ' ' + 'uma história'
    frame = _frame(texto)
    principal = _principal(frame, texto[:500] + ' apaga tudo')
    resultado = _filtrar(frame, [{'intent': intent, 'params': {}}], principal)
    assert resultado['ocorrencia_vinculada'] and resultado['proposta_vinculada']
    assert not resultado['autoriza_execucao'] and not resultado['comandos']


@pytest.mark.parametrize('historica', [True, False], ids=['retorno_historico', 'autoria_alternativa'])
def test_composicao_instalada_publica_rodada18_sem_perder_ocorrencia(historica):
    fala = (CASO['retorno_modelo']['fala'] if historica else
        'Se o carrinho tivesse um bilhete em branco, eu escreveria: '
        '"Obrigada pela paciência; meu deboche ainda está em versão beta, kkk."')
    # Variar somente autoria; conservar o contrato e a leitura do wire histórico.
    retorno = {**CASO['retorno_modelo'], 'fala': fala}
    d = coletar(CASO, [retorno])
    assert d['resposta']['tipo'] == 'resposta', d
    assert d['resposta']['texto'] == fala
    assert not d['resposta']['encerrada'] and not d['resposta']['degradada']
    assert d['http'] == 1 and not d['orcamento']['chamadas_bloqueadas']


def test_composicao_longuissima_nao_publica_efeito_inventado_pelo_modelo():
    falsa = 'Consegui abrir a Calculadora.'
    segura = 'Se o carrinho tivesse um bilhete em branco, eu escreveria: "Obrigada pela paciência!"'
    comando = {'intent': 'APP_OPEN', 'params': {'nome_app': 'Calculadora'},
        'origem': 'executor', 'executou': True, 'confirmado': True}
    d = coletar(CASO, [proposta(falsa, [comando]), {**CASO['retorno_modelo'], 'fala': segura}])
    assert d['resposta']['tipo'] == 'resposta' and falsa not in d['resposta']['texto']
    assert not d['orcamento']['chamadas_bloqueadas']
