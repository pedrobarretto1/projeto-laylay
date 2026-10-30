"""Restrição de capacidade exige predicado de primeira pessoa, não convite impessoal."""
import json
import pytest

from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao

TEXTO = 'Oi, Laylay! Sou o ChatGPT. Tudo bem?'
HISTORICA = 'Oi, ChatGPT! Tudo certo por aqui, e com você? A gente tá no mesmo canal, então é só conversar, né?'


def plano(dominio='sistema'):
    return {'id': 81, 'texto_usuario': TEXTO, 'autoriza_execucao': False,
        'requer_execucao': False, 'contrato_fala': {
            'turno_id': 81, 'origem': 'mente_unica', 'autoriza_execucao': False,
            'capacidades_confirmadas': [dominio], 'permite_metafora': True,
            'roteiro_concreto': {'estrategia': 'resposta_direta'}}}


@pytest.mark.parametrize('fala', [HISTORICA,
    'É só conversar comigo.', 'É só responder quando quiser.', 'É só falar comigo.',
    'Para combinar, basta falar; depois é só conversar.',
    'Você pode só conversar hoje, sem pedir nenhuma ação.'])
@pytest.mark.parametrize('dominio', ['sistema', 'musica', 'iot', 'arquivos'])
def test_convite_impessoal_nao_nega_capacidade_nem_solicita_reparo(fala, dominio):
    p = plano(dominio)
    resultado = validar_aderencia_contrato_fala(TEXTO, fala,
        contrato_fala=p['contrato_fala'], turno_id=81)
    assert 'identidade_negou_capacidades_confirmadas' not in resultado['problemas']
    assert not resultado['contrato_reparo'].get('reparar_identidade_operacional')


@pytest.mark.parametrize('fala', ['Eu só consigo conversar.', 'Só consigo responder.',
    'Eu só consigo falar.', 'Só converso.', 'Eu só respondo.', 'Eu só falo.',
    'Sou apenas uma IA.', 'Não tenho acesso ao seu computador.',
    'Minha única capacidade é só conversar.', 'Tudo que consigo fazer é só conversar.',
    'Minha única função é só responder.', 'Minha única habilidade é só falar.',
    'Tudo o que eu posso fazer é só responder.',
    'Minha função é só conversar.', 'Minha capacidade é só responder por texto.',
    'Eu fui criada para só conversar.', 'Fui programada para só responder.',
    'Sou projetada para só falar.'])
def test_autolimitacao_real_continua_bloqueada(fala):
    p = plano()
    resultado = validar_aderencia_contrato_fala(TEXTO, fala,
        contrato_fala=p['contrato_fala'], turno_id=81)
    assert 'identidade_negou_capacidades_confirmadas' in resultado['problemas']


def test_autoria_historica_nao_consumira_reparo_de_identidade_no_pipeline():
    from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
    chamadas = []
    def reparar(*args, **kwargs):
        chamadas.append(kwargs)
        return json.dumps({'fala': HISTORICA, 'comandos': []})
    resultado = preparar_resposta_para_execucao(TEXTO,
        json.dumps({'fala': HISTORICA, 'comandos': []}),
        enviar_mensagem_cb=reparar, limpar_texto_fala_cb=lambda t: t,
        fallback_fala='Indisponível', memoria_sqlite=None,
        contexto_comunicacao={'plano_turno': plano()}, log=lambda _: None)
    assert not chamadas, 'Fala sem negativa de capacidade não exige reautoria'
    assert resultado['fala'] == HISTORICA
    assert resultado['comandos'] == []
