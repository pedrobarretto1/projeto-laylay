"""Conteúdo e formato modificam a autoria; não pedem executor externo."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import tipo_transformacao_conversacional
from mente_laylay.cognicao.plano_turno import planejar_turno

CASOS = json.loads((Path(__file__).parent / 'fixtures/biblioteca_retorno_20261101.json').read_text(encoding='utf8'))


@pytest.mark.parametrize('texto', [*[c['entrada'] for c in CASOS if c['rodada'] in [3,5]],
    'Continue nossa história com uma reviravolta divertida, em três frases.',
    'Continue esse conto em duas frases e com um detalhe estranho.',
    'Escreva uma mini-história divertida sobre uma bibliotecária que vira uma bolinha de gude. Duas frases, por favor.',
    'Escreva um conto sobre um gato.',
    'Tente assim: escreva uma história sobre uma princesa.',
    'Agora tente assim: escreva um conto sobre um robô.',
])
def test_autoria_com_modificadores_e_reformulacao_nao_exige_executor(texto):
    turno = classificar_modalidade_turno(texto, texto_tem_comando_explicito=lambda _: True)
    assert not turno['autoriza_execucao'] and not turno['texto_operacional']
    plano = planejar_turno(texto, turno=turno, mente={})
    assert not plano['requer_execucao'] and not plano['comandos']


@pytest.mark.parametrize('texto', [
    'Continue nossa história com uma reviravolta no arquivo roteiro.txt.',
    'Escreva uma história no arquivo roteiro.txt.',
    'Escreva uma história sobre uma princesa por e-mail.',
    'Tente assim: abra o navegador.',
    'Escreva um conto sobre um gato e abra o navegador.',
    'Escreva um conto sobre um gato; apague o arquivo notas.txt.',
    'Escreva uma história sobre um gato que mia: abra o navegador.',
    'Escreva uma história sobre um gato que mia no bloco de notas.',
    'Escreva uma história sobre um gato que mia por e-mail.',
    'Escreva uma história sobre um gato que mia, salve no arquivo roteiro.txt.',
])
def test_destino_ou_pedido_externo_nao_e_consumido_pelo_ato_discursivo(texto):
    assert not tipo_transformacao_conversacional(texto)


@pytest.mark.parametrize('texto', [
    'Continue nossa história com um detalhe engraçado. Abra a Calculadora.',
    'Escreva uma história sobre um gato. Liga a luz.',
])
def test_modificador_discursivo_nao_apaga_ordem_independente(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao']
    assert any(s['natureza_acao']=='transformacao_conversacional' and not s['autoriza_execucao'] for s in turno['segmentos'])
    assert any(s['autoriza_execucao'] for s in turno['segmentos'])


@pytest.mark.parametrize('formato', ['numa frase', 'num parágrafo', 'numa palavra'])
def test_contracao_de_formato_tem_o_mesmo_contrato_da_forma_plena(formato):
    assert tipo_transformacao_conversacional(f'Responda {formato}.') == 'formato_resposta'
    turno = classificar_modalidade_turno(f'Qual você escolheria e por quê? Responda {formato}.')
    assert not turno['autoriza_execucao'] and not turno['texto_operacional']


def test_contracao_de_formato_preserva_destino_e_ordem_independente():
    assert not tipo_transformacao_conversacional('Responda num arquivo.')
    turno = classificar_modalidade_turno('Responda numa frase e abra o Chrome.')
    assert turno['autoriza_execucao'] and 'abra o chrome' in turno['texto_operacional']
    assert 'responda' not in turno['texto_operacional']
