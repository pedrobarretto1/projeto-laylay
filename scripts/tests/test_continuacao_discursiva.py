"""Continuar/contar discurso no canal atual não pede efeito externo."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import tipo_transformacao_conversacional
from mente_laylay.cognicao.plano_turno import planejar_turno

CASOS=json.loads((Path(__file__).parent/'fixtures/biblioteca_20261031.json').read_text(encoding='utf8'))


@pytest.mark.parametrize('texto',[
    CASOS[0]['entrada'],
    'Continue essa mesma cena com duas falas, uma sua e uma minha, em tom brincalhão.',
    'Continue nossa história com três parágrafos.',
    'Apenas conte as falas, sem executar comandos.',
    'Conte a história aqui.',
    'Pode continuar essa narrativa com quatro frases?',
    'Continue o conto em tom divertido.',
])
def test_continuar_e_contar_discurso_nao_autorizam_executor(texto):
    t=classificar_modalidade_turno(texto,texto_tem_comando_explicito=lambda _:True)
    assert not t['autoriza_execucao'] and not t['texto_operacional']
    p=planejar_turno(texto,turno=t,mente={})
    assert not p['requer_execucao'] and not p['comandos']


@pytest.mark.parametrize('texto',[
    'Continue essa história no arquivo roteiro.txt.',
    'Continue a música.',
    'Conte os arquivos da pasta Downloads.',
    'Conte a história por e-mail.',
])
def test_destino_ou_recurso_externo_nao_e_transformacao(texto):
    assert not tipo_transformacao_conversacional(texto)


@pytest.mark.parametrize('texto',[
    'Continue essa cena e abra a Calculadora.',
    'Apenas conte as falas; liga a luz.',
])
def test_continuacao_nao_apaga_ordem_independente(texto):
    t=classificar_modalidade_turno(texto)
    assert t['autoriza_execucao']
    assert any(s['natureza_acao']=='transformacao_conversacional' and not s['autoriza_execucao'] for s in t['segmentos'])
    assert any(s['autoriza_execucao'] for s in t['segmentos'])


def test_composicao_publica_continuacao_sem_exigir_executor():
    from tests.test_autoria_operacao_composicao import coletar_autoria
    from tests.test_papo_casual_composicao import proposta
    fala = ('Eu diria: "Seu telescópio de papelão precisa de um manual para enxergar o chão." '
            'Você responderia: "Pelo menos ele não cobra ingresso!"')
    d = coletar_autoria(CASOS[0], [proposta(fala)])
    assert not d['execucao_exigida'] and not d['operacional']
    assert d['resposta']['texto'] == fala and len(d['publicacoes']) == 1
    assert d['http'] == 1 and not d['resposta']['degradada']
    assert not d['resposta']['encerrada']


@pytest.mark.parametrize('intent,params', [('APP_OPEN', {'nome_app': 'Opera'}),
    ('MEDIA_CONTROL', {'action': 'pause'})])
def test_composicao_continuacao_nao_aceita_efeito_proposto(intent, params):
    from tests.test_autoria_operacao_composicao import coletar_autoria
    from tests.test_papo_casual_composicao import proposta
    falsa = 'Consegui abrir o Opera.' if intent == 'APP_OPEN' else 'Consegui pausar a música.'
    receipt = {'intent': intent, 'params': params, 'executou': True,
               'confirmado': True, 'origem': 'executor'}
    d = coletar_autoria(CASOS[0], [proposta(falsa, [receipt]), proposta('Não executei nenhuma ação.')])
    assert not d['execucao_exigida'] and falsa not in d['resposta']['texto']
