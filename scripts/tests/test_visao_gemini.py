"""Gemini troca somente o provedor; evidência e autoridade continuam canônicas."""
import json

import pytest

from mente_laylay.integracao.composicao_inteligencia_externa import ComposicaoInteligenciaExternaRuntime
from mente_laylay.percepcao.imagens_multimodais import empacotar_imagens
from mente_laylay.percepcao.visao_jogo.presenca_visual import criar_contrato_saida_presenca_visual, extrair_presenca_visual


def compor(*, chave='segredo-teste', gratuito='1', status=200, conteudo=None, finish='stop', modelo=''):
    chamadas = []
    dados = dict(evidencias=[], foco_evidencia='', proposta_reacao=None, relevante=False,
                 categoria='nenhuma', fala='', motivo='Sem evento marcante.', confianca=0,
                 momento_seguro=False, clima_musical='')
    class Resposta:
        status_code = status
        def json(self):
            return {'choices': [{'message': {'content': conteudo if conteudo is not None else json.dumps(dados)}, 'finish_reason': finish}]}
    def post(url, **kwargs):
        chamadas.append((url, kwargs))
        return Resposta()
    env = {'LAYLAY_VISAO_BACKEND': 'gemini', 'GEMINI_API_KEY': chave,
           'LAYLAY_GEMINI_FREE_TIER_CONFIRMADO': gratuito,
           'LAYLAY_CONVERSA_JOGO_REMOTA_ATIVA': '0', 'GROQ_API_KEY': 'outra-chave',
           'LAYLAY_VISAO_MODEL': 'qwen3-vl:4b-instruct'}
    if modelo:
        env['GEMINI_VISION_MODEL'] = modelo
    runtime = ComposicaoInteligenciaExternaRuntime(
        base_url='http://localhost:11434/v1', model='qwen3-vl:4b-instruct',
        api_key='local', http_referer='http://localhost', app_title='Laylay',
        normalizar_texto_curto=str.casefold, requests_get=lambda *a, **k: None,
        requests_post=post, ao_finalizar_conversa_modo_jogo=lambda: None,
        env_getter=lambda k, d='': env.get(k, d), log=lambda *a: None)
    return runtime, chamadas


def test_gemini_preserva_dois_quadros_schema_e_conversa_local():
    runtime, chamadas = compor()
    assert runtime.credencial_visual_disponivel
    assert runtime.model == 'qwen3-vl:4b-instruct'
    assert not runtime.conversa_jogo.disponivel
    pacote = empacotar_imagens([{'label': 'antes', 'data': 'YWJj'}, {'label': 'depois', 'data': 'ZGVm'}])
    contrato = criar_contrato_saida_presenca_visual()
    resposta = runtime.analisar_imagem_jogo(pacote, 'Compare os quadros.', contrato_saida=contrato)
    assert extrair_presenca_visual(resposta)[1]['relevante'] is False
    assert len(chamadas) == 1
    url, opcoes = chamadas[0]
    assert url == 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions'
    assert opcoes['headers']['Authorization'] == 'Bearer segredo-teste'
    payload = opcoes['json']
    assert payload['model'] == 'gemini-3.5-flash-lite'
    assert payload['response_format'] == contrato.response_format
    assert payload['reasoning_effort'] == 'minimal'
    assert 'não autoriza ações' in payload['messages'][0]['content']
    assert not any(k.startswith('_laylay') for k in payload)
    assert len([p for p in payload['messages'][1]['content'] if p['type'] == 'image_url']) == 2
    assert opcoes['timeout'] == 12


@pytest.mark.parametrize('chave,gratuito', [('', '1'), ('segredo', '0'), ('segredo', '')])
def test_sem_chave_ou_confirmacao_free_tier_nao_envia_imagem(chave, gratuito):
    runtime, chamadas = compor(chave=chave, gratuito=gratuito)
    assert not runtime.credencial_visual_disponivel
    assert runtime.analisar_imagem('YWJj', 'Leia.').startswith('Falha visual:')
    assert chamadas == []


@pytest.mark.parametrize('status,conteudo,finish', [(429, None, 'stop'), (400, None, 'stop'),
    (200, '{"fala":"feito"}', 'stop'), (200, None, 'length')])
def test_falha_gemini_nao_reenvia_a_outro_provedor_nem_vira_evidencia(status, conteudo, finish):
    runtime, chamadas = compor(status=status, conteudo=conteudo, finish=finish)
    resposta = runtime.analisar_imagem_jogo('YWJj', 'Observe.', contrato_saida=criar_contrato_saida_presenca_visual())
    assert resposta.startswith('Falha visual:')
    assert not extrair_presenca_visual(resposta)[1]
    assert len(chamadas) == 1


def test_sintese_cooperativa_usa_gemini_e_conserva_fontes():
    runtime, chamadas = compor(conteudo='A tela mostra uma porta azul; pesquisa indisponível.')
    assert runtime.sintetizar_pesquisa_jogo('Tela: porta azul. Pesquisa falhou.') == 'A tela mostra uma porta azul; pesquisa indisponível.'
    assert 'Pesquisa falhou.' in chamadas[0][1]['json']['messages'][1]['content'][1]['text']


def test_modelo_gemini_explicitamente_selecionado_nao_altera_conversa_nem_faz_fallback():
    runtime, chamadas = compor(modelo='gemini-3.1-flash-lite', status=503)
    assert runtime.visao_model == 'gemini-3.1-flash-lite'
    assert runtime.model == 'qwen3-vl:4b-instruct'
    assert runtime.analisar_imagem('YWJj', 'Observe.').startswith('Falha visual:')
    assert len(chamadas) == 1
    assert chamadas[0][1]['json']['model'] == 'gemini-3.1-flash-lite'
