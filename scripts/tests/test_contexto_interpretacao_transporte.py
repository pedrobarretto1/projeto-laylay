"""Contexto semântico não é dump diagnóstico; contingência não é intenção."""
from copy import deepcopy
import json
import threading

import pytest

from mente_laylay.cognicao.interpretacao_intencao import InterpretacaoIntencaoRuntime
from mente_laylay.cognicao.estado_tecnico_llm import eh_estado_tecnico_llm
from mente_laylay.integracao.llm_http import (
    RespostaLLMFallback, conteudo_fallback_llm_local, conteudo_fallback_modo_jogo,
    executar_chat_llm, post_chat_llm,
)
from mente_laylay.integracao.resposta_llm import interpretar_payload_llm
from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
from mente_laylay.integracao.registro_conversa_llm import RequisicaoTransporteLLM
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from scripts.tests.test_publicacao_ocorrencia_turno import _frame


@pytest.mark.parametrize("intent,params,alvo", [
    ("VOLUME", {"acao":"set","nivel_volume":90}, ""),
    ("APP_OPEN", {"nome_app":"Calculadora"}, "Calculadora"),
    ("PLAYLIST_ADD", {"nome_playlist":"novidades"}, "novidades"),
])
def test_prompt_semantico_independe_do_volume_de_diagnostico_preservando_fontes(intent, params, alvo):
    mental = _frame("pedido atual")
    mental.update(ultima_acao_contrato={"id_solicitacao":"efeito-anterior", "intent":intent,
        "alvo":alvo,"confirmado":True,"executou":True,"evidencia_confirmacao":"observação fixture"},
        ultima_acao_params=params, ultima_acao_intent=intent, ultimo_alvo=alvo,
        continuidade_geral={"dominio_ativo":"app", "dominios":{"app":{"params":params,"ts":1,"expira_em":2}}},
        pendencia_acao_canonica={"id":"pendente","autoridade":{"turno_id":"anterior"}},
        ultima_resposta="Resposta anterior contextual.", ultimo_app_janela="Calculadora")
    estado = EstadoCompartilhadoRuntime(mental=mental)
    payloads = []
    def enviar(mensagens, **kwargs):
        payloads.append(json.loads(mensagens[1]["content"]))
        return '{"intent":"NONE","params":{}}'
    ctx = {"estado":{"mente_integrada_estado":estado.mental}, "enviar_mensagem":enviar}
    runtime = InterpretacaoIntencaoRuntime(contexto_getter=lambda:ctx, log=lambda *_a:None)
    runtime.analisar("cuida desse pedido")
    antes = estado.snapshot()
    estado.atualizar_campos("mental", diagnostico_metricas={"dump":"x"*60000})
    plano = estado.obter_copia("mental","plano_turno_atual")
    plano["dump_diagnostico"] = "y"*60000
    estado.atualizar_campos("mental", plano_turno_atual=plano)
    ctx["estado"]["mente_integrada_estado"] = estado.mental
    runtime._cache_analise.clear()
    runtime.analisar("cuida desse pedido")
    assert payloads[1] == payloads[0], "primeira RED: árvores internas não podem inflar a mensagem semântica"
    projetada = payloads[0]["contexto_conversas"]["mente_curta"]
    assert projetada["ultima_acao_contrato"] == antes["mental"]["ultima_acao_contrato"]
    assert projetada["ultima_acao_params"] == params
    assert projetada["pendencia_acao_canonica"] == antes["mental"]["pendencia_acao_canonica"]
    assert projetada["retrato_turno_atual"] == antes["mental"]["retrato_turno_atual"]
    assert projetada["turno_atual"]["id"] == antes["mental"]["turno_atual"]["id"]
    assert projetada["ultima_resposta"] == "Resposta anterior contextual."
    assert estado.mental["diagnostico_metricas"]["dump"] == "x"*60000, "projeção não limpa o estado real"


def _pedido():
    return {"model":"fixture", "messages":[{"role":"system","content":"Retorne JSON com intent e params."},
        {"role":"user","content":"pode pausar a música"}],"max_tokens":140}


@pytest.mark.parametrize("causa", ["400", "500", "circuito"])
def test_falha_do_transporte_nao_produz_intencao_none_gerada(causa):
    from types import SimpleNamespace
    import time
    data = _pedido()
    chamadas = []
    def post(*a, **k):
        chamadas.append(True)
        return SimpleNamespace(status_code=400 if causa == "400" else 500,text="falha fixture")
    response, _ = post_chat_llm({},data,base_url="http://localhost:11434/v1",local_timeout=8,
        remote_timeout=30,bad_request_until=time.time()+20 if causa == "circuito" else 0,
        lock=threading.Lock(),requests_post=post,print_fn=lambda *_a:None)
    assert isinstance(response, RespostaLLMFallback)
    raw = executar_chat_llm(data, post_chat=lambda *_a,**_k:response,
        interpretar_payload=interpretar_payload_llm,api_key="",http_referer="",app_title="",
        endpoint_local=True,log=lambda *_a:None)
    assert eh_estado_tecnico_llm(raw), "primeira RED: contingência de transporte não vira JSON semântico válido"
    runtime = InterpretacaoIntencaoRuntime(contexto_getter=lambda:{"enviar_mensagem":lambda *_a,**_k:raw},log=lambda *_a:None)
    assert runtime.analisar("pode pausar a música") is None


def test_none_real_continua_decisao_semantica_valida():
    runtime = InterpretacaoIntencaoRuntime(contexto_getter=lambda:{
        "enviar_mensagem":lambda *_a,**_k:'{"intent":"NONE","params":{}}'},log=lambda *_a:None)
    assert runtime.analisar("conversa sem pedido") == {"intent":"NONE","params":{}}


def test_modo_jogo_adiado_nao_finge_analise_semantica():
    assert eh_estado_tecnico_llm(conteudo_fallback_modo_jogo(_pedido()))


def test_cliente_tipado_nao_conta_fallback_de_intencao_como_sucesso():
    cliente = ClienteLLMRuntime(post_chat=lambda *_a,**_k:RespostaLLMFallback(
        conteudo_fallback_llm_local(_pedido()),motivo="requisicao_invalida_persistente"),
        endpoint_local_getter=lambda:True,
        log=lambda *_a:None)
    resultado = cliente.executar(RequisicaoTransporteLLM(payload=_pedido()))
    assert resultado.sucesso is False and eh_estado_tecnico_llm(resultado.texto)


def test_projecao_preserva_pendencias_validade_falha_e_isola_aliases():
    from mente_laylay.memoria_mental.contexto_integrado import projetar_mente_para_interpretacao
    mental = {"turno_atual":{"id":12,"texto":"essa última","autoriza_execucao":False},
        "ultima_acao_contrato":{"id_solicitacao":"falhou","executou":False,"confirmado":False},
        "pendencia_atual":{"id":"a","ts":1,"expira_em":2,"status":"ativa"},
        "esclarecimento_operacional_ativo":{"campo":"nome_app","pendencia_id":"a","params_base":{}},
        "focos_por_dominio":{"app":{"nome":"Calculadora","ts":1,"expira_em":2}},
        "pergunta_aberta_texto":"Qual aplicativo?", "pergunta_aberta_ts":1,
        "ultima_promessa_texto":"Sugestão anterior", "ultima_promessa_ts":1,
        "foco_operacional_alvo":"Calculadora", "foco_operacional_ts":1,
        "diagnostico_metricas":{"dump":"não enviar"}}
    antes = deepcopy(mental)
    projetada = projetar_mente_para_interpretacao(mental)
    assert "diagnostico_metricas" not in projetada
    for chave in antes:
        if chave != "diagnostico_metricas": assert projetada[chave] == antes[chave]
    projetada["pendencia_atual"]["status"] = "cancelada"
    assert mental == antes, "projeção não promove, renova nem consome as fontes"


def test_falha_tecnica_nao_entra_no_decoder_e_eh_observavel():
    logs, decodificacoes = [], []
    runtime = InterpretacaoIntencaoRuntime(contexto_getter=lambda:{
        "enviar_mensagem":lambda *_a,**_k:"__LAYLAY_LLM_INDISPONIVEL__",
        "extrair_json_da_ia":lambda bruto: decodificacoes.append(bruto) or '{"intent":"NONE","params":{}}'},
        log=logs.append)
    assert runtime.analisar("pode pausar a música") is None
    assert not decodificacoes
    assert any("geração não concluída" in log and "indisponivel" in log for log in logs)


@pytest.mark.parametrize('texto', ['pode colocar ele para mim ouvir',
    'abre esse aplicativo', 'salva isso no arquivo'])
def test_interpretacao_do_turno_atual_nao_e_adiada_como_tarefa_secundaria(texto):
    import requests
    from mente_laylay.integracao.orcamento_llm_turno import OrcamentoLLMTurnoRuntime
    transportes, pedidos = [], []
    def post(*a, **k):
        transportes.append(True)
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps({'choices': [{'message': {'content': '{"intent":"NONE","params":{}}'}}]}).encode()
        return r
    orcamento = OrcamentoLLMTurnoRuntime(max_chamadas_turno=2)
    orcamento.iniciar_turno('turno-atual')
    cliente = ClienteLLMRuntime(endpoint_local_getter=lambda: True, interacao_ativa=lambda: True,
        post_chat=post, orcamento_turno=orcamento, log=lambda *a: None)
    def enviar(mensagens, **opcoes):
        pedidos.append(opcoes)
        return cliente.executar(RequisicaoTransporteLLM(payload={'messages': mensagens},
            prioridade_interativa=bool(opcoes.get('_prioridade_interativa')),
            tipo_chamada=opcoes.get('_tipo_chamada', 'principal'))).texto
    turno = {'id': 'turno-atual', 'texto': texto, 'autoriza_execucao': True}
    ctx = {'estado': {'mente_integrada_estado': {'turno_atual': turno}}, 'enviar_mensagem': enviar}
    r = InterpretacaoIntencaoRuntime(contexto_getter=lambda: ctx, log=lambda *a: None)
    assert r.analisar(texto) == {'intent': 'NONE', 'params': {}}
    assert len(transportes) == 1
    assert pedidos[0]['_tipo_chamada'] == 'interpretacao'
    principal = cliente.executar(RequisicaoTransporteLLM(payload={'messages': []},
        prioridade_interativa=True, tipo_chamada='principal'))
    assert principal.sucesso and len(transportes) == 2


@pytest.mark.parametrize('turno', [{}, {'id': 'antigo', 'texto': 'outro pedido'}])
def test_interpretacao_sem_vinculo_ao_turno_nao_ganha_prioridade(turno):
    pedidos = []
    def enviar(*a, **opcoes):
        pedidos.append(opcoes)
        return '{"intent":"NONE","params":{}}'
    ctx = {'estado': {'mente_integrada_estado': {'turno_atual': turno}}, 'enviar_mensagem': enviar}
    InterpretacaoIntencaoRuntime(contexto_getter=lambda: ctx).analisar('pedido diferente')
    assert not pedidos[0].get('_prioridade_interativa')


@pytest.mark.parametrize('variante, esperado', [('atual', True), ('sufixo_divergente', False),
    ('plano_de_outro_turno', False)])
def test_prioridade_de_pedido_longo_exige_fonte_integral_do_mesmo_turno(variante, esperado):
    texto = 'pode colocar ele para mim ouvir ' + 'detalhes do pedido ' * 36
    atual = texto if variante != 'sufixo_divergente' else texto + 'sem tocar agora'
    pedidos = []
    def enviar(*a, **opcoes):
        pedidos.append(opcoes)
        return '{"intent":"NONE","params":{}}'
    mental = {'turno_atual': {'id': 12, 'texto': texto[:500]},
        'plano_turno_atual': {'id': 13 if variante == 'plano_de_outro_turno' else 12,
            'texto_usuario': texto}}
    ctx = {'estado': {'mente_integrada_estado': mental}, 'enviar_mensagem': enviar}
    InterpretacaoIntencaoRuntime(contexto_getter=lambda: ctx).analisar(atual)
    assert pedidos[0]['_prioridade_interativa'] is esperado
