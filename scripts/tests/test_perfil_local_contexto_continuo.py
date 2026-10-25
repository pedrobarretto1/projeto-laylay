"""Perfil compacto não pode depender da grafia nem apagar fontes do turno."""
from copy import deepcopy

import pytest

from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT, BASE_SYSTEM_PROMPT_COMPACTO


@pytest.mark.parametrize("texto", [
    "o que voce esta fazendo?", "como estão as coisas no computador?", "qual a diferença entre os exemplos?",
])
def test_perfil_local_normal_seleciona_base_compacta_sem_cortar_contexto(texto):
    fonte = "\nFONTE DO TURNO: valor solicitado=90; medido=87; autorização=false."
    mensagens = [{"role": "system", "content": BASE_SYSTEM_PROMPT + fonte},
        {"role": "user", "content": "estou estudando hoje"},
        {"role": "assistant", "content": "Que assunto você está estudando?"},
        {"role": "system", "content": "CONTRATO ATUAL INTEGRAL: manter todos os atos e referências."},
        {"role": "user", "content": texto}]
    antes = deepcopy(mensagens)
    p = preparar_payload_llm(mensagens, model="qwen3:4b-instruct", max_tokens=1024,
                            endpoint_local=True, modo_rapido=False)
    assert p["messages"][0]["content"] == BASE_SYSTEM_PROMPT_COMPACTO + fonte
    assert p["messages"][1:] == mensagens[1:]
    assert mensagens == antes


@pytest.mark.parametrize("opcoes", [
    {"endpoint_local": False}, {"endpoint_local": True, "contexto_fechado": True},
    {"endpoint_local": True, "otimizacao_prompt_ativa": False},
])
def test_pacote_fechado_ou_perfil_nao_selecionado_continuam_atomicos(opcoes):
    mensagens = [{"role": "system", "content": BASE_SYSTEM_PROMPT}, {"role": "user", "content": "oi"}]
    p = preparar_payload_llm(mensagens, model="modelo", max_tokens=1024, **opcoes)
    assert p["messages"][0] == mensagens[0]


def test_prompt_personalizado_nao_e_substituido_por_marcador_textual():
    personalizado = "Você é Laylay. Esta instrução não é o perfil canônico. Fonte indispensável."
    p = preparar_payload_llm([{"role": "system", "content": personalizado},
                             {"role": "user", "content": "oi"}], model="modelo", endpoint_local=True)
    assert p["messages"][0]["content"] == personalizado


def test_instrucao_prioritaria_anteposta_nao_vira_perfil_simples():
    sistema = "INSTRUÇÃO DO OWNER: preservar os dois atos.\n" + BASE_SYSTEM_PROMPT
    p = preparar_payload_llm([{"role": "system", "content": sistema},
                             {"role": "user", "content": "dois atos"}], model="modelo", endpoint_local=True)
    assert p["messages"][0]["content"] == sistema


@pytest.mark.parametrize('texto', ['explica a diferença entre eu e mim',
    'agora explica a diferença entre eu e mim', 'então me ensina a usar vírgulas',
    'ensina a diferença entre esses dois exemplos'])
def test_pedido_de_ensino_no_imperativo_nao_herda_resposta_rapida(texto):
    from mente_laylay.personalidade.proporcao_resposta import classificar_proporcao
    from mente_laylay.autonomia.fluxos_conversa import usar_modo_rapido_conversa
    assert classificar_proporcao(texto) == 'explicativa'
    assert not usar_modo_rapido_conversa(texto)


@pytest.mark.parametrize('texto', ['pode colocar ele para mim ouvir',
    'abre esse aplicativo', 'salva isso no arquivo'])
def test_compactacao_normal_preserva_proposta_operacional_condicionada_ao_turno(texto):
    p = preparar_payload_llm([{'role': 'system', 'content': BASE_SYSTEM_PROMPT},
        {'role': 'system', 'content': 'Turno atual: autoriza_execucao=True; sem receipt.'},
        {'role': 'user', 'content': texto}], model='qwen3:4b-instruct', endpoint_local=True)
    sistema = p['messages'][0]['content']
    assert 'Retorne comandos vazios.' not in sistema
    assert 'Pedido real gera um comando' in sistema
    assert 'Não conclua antes do executor' in sistema


def test_rota_rapida_conversacional_continua_sem_propor_operacao():
    from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT_RAPIDO
    assert 'Retorne comandos vazios.' in BASE_SYSTEM_PROMPT_RAPIDO
