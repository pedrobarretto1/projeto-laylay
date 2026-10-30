"""Cortesia temporal não concede encerramento; intenção explícita domina a moldura."""
import json

import pytest

from mente_laylay.autonomia.pre_fluxo_contextual import processar_encerramento_conversa
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.presenca_conversacional import realizacoes_presenca
from mente_laylay.memoria_mental.encerramento_assunto import classificar_encerramento_assunto
from mente_laylay.memoria_mental.sessao_conversa import texto_encerra_conversa
from scripts.tests.test_autoria_despedida_canonica import quadro
from scripts.tests.test_encerramento_sessao_ocorrencia import preparar


@pytest.mark.parametrize('texto', ['boa noite', 'boa noite, Laylay', 'Boa noite!',
    'bom dia, Lay', 'boa tarde, Laylay'])
@pytest.mark.parametrize('ativa', [None, False, True])
def test_cortesia_temporal_sem_intencao_explicita_preserva_sessao(texto, ativa):
    anterior = {'sessao_conversa_ativa': ativa, 'foco_conversacional_topico': 'notas',
                'pendencia_atual': {'id': 'p', 'status': 'ativa'}}
    assert classificar_encerramento_assunto(texto, anterior) == ''
    assert not texto_encerra_conversa(texto)
    estado, runtime = preparar(texto)
    estado.atualizar('mental', lambda atual: {**atual, **anterior})
    antes = estado.snapshot()
    assert processar_encerramento_conversa({'_renovar_sessao_conversa': runtime.renovar_sessao_conversa},
        texto, emitir_fala=False) == (False, '')
    assert estado.snapshot() == antes, 'cortesia sem autoridade apagou contexto/pendência'
    plano, pacote = quadro(texto)
    contrato = plano['contrato_fala']
    assert contrato.get('encerramento_assunto') != 'sessao'
    assert contrato['permite_pergunta'] is False
    opcoes = realizacoes_presenca(texto, contrato=contrato, turno_id=plano['id'])
    assert opcoes and all('?' not in f and 'Até mais' not in f for f in opcoes)
    assert pacote.contexto_fechado
    for fala in opcoes:
        assert verificar_fala_turno(fala, plano=plano)['aceita']
        assert pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':fala, 'fontes':[]}]}))['fala'] == fala
    assert not verificar_fala_turno('Até mais!', plano=plano)['aceita']


@pytest.mark.parametrize('saudacao', ['boa noite', 'bom dia', 'boa tarde', 'oi'])
@pytest.mark.parametrize('encerramento', ['vou dormir', 'por hoje é só', 'até mais'])
def test_intencao_de_encerrar_domina_saudacao_sem_descartar_outros_atos(saudacao, encerramento):
    texto = f'{saudacao}, {encerramento}'
    assert texto_encerra_conversa(texto), 'primeira fronteira: moldura esconde o encerramento explícito'
    assert classificar_encerramento_assunto(texto) == 'sessao'
    plano, pacote = quadro(texto)
    assert plano['contrato_fala']['atos'] == ['encerramento_sessao']
    assert pacote.contexto_fechado
    fala = realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])[0]
    assert verificar_fala_turno(fala, plano=plano)['aceita']
    assert not verificar_fala_turno('Boa noite! Como você está?', plano=plano)['aceita']


@pytest.mark.parametrize('texto', ['vou dormir, boa noite', 'por hoje é só. Boa tarde!',
    'até mais, bom dia', 'vou sair, olá'])
def test_cortesia_final_tambem_nao_oculta_intencao_explicita(texto):
    assert texto_encerra_conversa(texto)
    assert classificar_encerramento_assunto(texto) == 'sessao'


@pytest.mark.parametrize('texto', ['boa noite, como você está?', 'boa tarde, tudo bem?',
    'boa noite, quero conversar', 'boa noite, vou continuar minhas notas',
    'boa noite, vou dormir depois de terminar os slides', 'boa noite, não vou dormir',
    'boa noite, ela disse que vai dormir', 'boa noite, "vou dormir"',
    'repita "boa noite"', 'a frase "boa noite" é uma despedida?',
    'boa noite, abra o navegador', 'boa noite, vou dormir e abra o navegador',
    'vou dormir, boa noite e abre o navegador', 'não encerre a conversa, boa noite',
    'boa noite, vou dormir?', 'vou dormir, boa noite?', 'boa noite?'])
def test_ato_adicional_citacao_negacao_e_comando_nao_sao_consumidos(texto):
    assert not texto_encerra_conversa(texto)
    assert classificar_encerramento_assunto(texto) != 'sessao'
    renovacoes = []
    assert processar_encerramento_conversa({'_renovar_sessao_conversa': lambda *a: renovacoes.append(a)},
        texto, emitir_fala=False) == (False, '')
    assert not renovacoes


@pytest.mark.parametrize('texto', ['boa noite, como você está?', 'oi lay'])
def test_saudacao_com_abertura_inequivoca_preserva_reciprocidade(texto):
    plano, _ = quadro(texto)
    opcoes = realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert any('?' in f for f in opcoes)
    assert plano['contrato_fala']['permite_pergunta']


@pytest.mark.parametrize('texto', ['bom dia, Lay', 'boa tarde', 'boa noite, Laylay'])
def test_reparo_de_cortesia_indeterminada_nao_inventa_abertura_ou_encerramento(texto):
    from mente_laylay.cognicao.qualidade_comunicacao import (
        avaliar_qualidade_comunicacao, montar_pacote_reparo_comunicacao,
    )
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    plano, _ = quadro(texto)
    ruim = 'Até mais! Quer conversar mais um pouco?'
    avaliacao = avaliar_qualidade_comunicacao(texto, ruim, plano=plano)
    assert avaliacao['problemas_bloqueantes']
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_reparo_comunicacao(texto, ruim,
        avaliacao, plano=plano, mensagens=[{'role':'assistant','content':ruim}]))
    assert pacote.contexto_fechado and ruim not in str(pacote.mensagens)
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':ruim, 'fontes':[]}]}))
    for fala in realizacoes_presenca(texto, contrato=plano['contrato_fala'], turno_id=plano['id']):
        assert pacote.contrato_saida.decodificar_json(json.dumps({'comandos':[],
            'suporte_proposicoes':[{'texto':fala, 'fontes':[]}]}))['fala'] == fala


@pytest.mark.parametrize('texto', ['boa noite, vou dormir', 'bom dia, vou sair',
    'boa tarde, por hoje é só', 'vou dormir, boa noite'])
def test_limpeza_do_encerramento_explicito_preserva_ocorrencia_em_conclusao(texto):
    estado, runtime = preparar(texto)
    antes = estado.snapshot()['mental']
    assert antes['turno_atual']['encerramento_assunto'] == 'sessao'
    assert processar_encerramento_conversa({'_renovar_sessao_conversa': runtime.renovar_sessao_conversa},
        texto, emitir_fala=False) == (False, 'encerramento_conversa')
    depois = estado.snapshot()['mental']
    assert depois['sessao_conversa_ativa'] is False
    assert depois['turno_atual'] == antes['turno_atual']
    assert depois['plano_turno_atual'] == antes['plano_turno_atual']
    assert depois['contrato_fala_atual'] == antes['contrato_fala_atual']
    assert not depois['pendencia_atual']
