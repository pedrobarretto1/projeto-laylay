from __future__ import annotations

import io
import json
import socket
import sys

import pytest

from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    ErroProtocoloDesktop,
    validar_mensagem_cliente,
)
from mente_laylay.integracao.dev_console_runtime import (
    DevConsoleRuntime,
    EspelhoStreamDev,
    instalar_espelhos_stream_dev,
)
from mente_laylay.personalidade.terminal_laylay import criar_print_filtrado


def _linha(sock: socket.socket, timeout: float = 1.5) -> dict:
    sock.settimeout(timeout)
    dados = b""
    while not dados.endswith(b"\n"):
        dados += sock.recv(1)
    return json.loads(dados.decode("utf-8"))


def _ate_tipo(sock: socket.socket, tipo: str) -> dict:
    while True:
        mensagem = _linha(sock)
        if mensagem.get("type") == tipo:
            return mensagem


def test_runtime_normaliza_log_e_remove_credencial() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 1_700_000_000.25)

    evento = runtime.registrar_linha(
        "⚠️ [ROTEADOR:ARQUIVOS] falha token=segredo-absoluto | duração=31ms",
        origem="stderr",
    )

    assert evento["category"] == "ROUTER"
    assert evento["level"] == "error"
    assert evento["duration_ms"] == 31.0
    assert "segredo-absoluto" not in evento["message"]
    assert "[protegido]" in evento["message"]
    assert runtime.snapshot()["events"] == [evento]


def test_espelho_preserva_terminal_e_reconstitui_linhas_parciais() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 10.0)
    original = io.StringIO()
    espelho = EspelhoStreamDev(original, runtime, origem="stdout")

    espelho.write("[SYSTEM] inici")
    assert runtime.snapshot()["events"] == []
    espelho.write("ado\nsegunda linha\n")

    assert original.getvalue() == "[SYSTEM] iniciado\nsegunda linha\n"
    assert [item["message"] for item in runtime.snapshot()["events"]] == [
        "[SYSTEM] iniciado",
        "segunda linha",
    ]


@pytest.mark.parametrize("prompt", ["💬 Você:", ">", "> 💬 Você:", "\x1b[36m💬 Você:\x1b[0m"])
def test_prompt_sem_entrada_nao_e_evento_dev(prompt):
    runtime = DevConsoleRuntime()
    assert runtime.registrar_linha(prompt, origem="stdout") == {}
    assert runtime.registrar_log_oculto(prompt, origem="stdout") == {}
    assert runtime.snapshot()["sequence"] == 0
    assert runtime.snapshot()["events"] == []
    # Não descartar conteúdo real nem erros por semelhança com um prompt.
    for texto, origem in [
        ("💬 Você: 'pode ligar a luz' | origem=desktop", "stdout"),
        ("> pode ligar a luz", "stdout"),
        ("Falha ao exibir 💬 Você:", "stdout"),
        (prompt, "stderr"),
    ]:
        assert runtime.registrar_linha(texto, origem=origem)


def test_leitor_real_mantem_prompt_no_console_sem_publicar_fala_vazia(monkeypatch):
    from functools import partial
    from types import SimpleNamespace
    from mente_laylay.personalidade.terminal_laylay import (
        escutar_texto_terminal, ler_linha_terminal_interrompivel,
    )
    dev = DevConsoleRuntime()
    console = io.StringIO()
    espelho = EspelhoStreamDev(console, dev, origem="stdout")
    continuar = [True]
    recebidas = []
    entrada = SimpleNamespace(isatty=lambda: True)
    monkeypatch.setattr(sys, "stdin", entrada)
    def ler(prompt, **kwargs):
        try:
            return ler_linha_terminal_interrompivel(
                prompt, **kwargs,
                msvcrt_mod=SimpleNamespace(kbhit=lambda: True, getwch=lambda: "\r"),
            )
        finally:
            continuar[0] = False
    escutar_texto_terminal(
        estado_ativo=lambda: True, processar_texto=recebidas.append,
        stdin=entrada,
        raw_print=partial(print, file=espelho),
        deve_continuar=lambda: continuar[0], ler_linha_fn=ler,
    )
    assert console.getvalue() == "\n💬 Você:\n> \n"
    assert recebidas == []
    assert dev.snapshot()["events"] == []


def test_instalacao_real_preserva_stdout_stderr_e_seus_canais(monkeypatch) -> None:
    stdout_original = io.StringIO()
    stderr_original = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout_original)
    monkeypatch.setattr(sys, "stderr", stderr_original)
    runtime = DevConsoleRuntime(clock=lambda: 10.0)

    instalar_espelhos_stream_dev(runtime)
    sys.stdout.write("[SYSTEM] saída comum\n")
    sys.stderr.write("falha direta\n")

    assert stdout_original.getvalue() == "[SYSTEM] saída comum\n"
    assert stderr_original.getvalue() == "falha direta\n"
    eventos = runtime.snapshot()["events"]
    assert [(item["source"], item["level"]) for item in eventos] == [
        ("stdout", "info"),
        ("stderr", "error"),
    ]


def test_espelho_continua_capturando_sem_terminal_externo() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 10.0)
    espelho = EspelhoStreamDev(None, runtime, origem="stdout")

    escrito = espelho.write("[SYSTEM] processo sem console\n")
    espelho.flush()

    assert escrito == len("[SYSTEM] processo sem console\n")
    assert runtime.snapshot()["events"][0]["message"] == (
        "[SYSTEM] processo sem console"
    )


def test_print_oculto_vai_para_debug_sem_aparecer_no_terminal() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 10.0)
    exibidas: list[str] = []
    imprimir = criar_print_filtrado(
        should_log=lambda texto: "visível" in texto,
        raw_print=lambda *args, **_kwargs: exibidas.append(" ".join(map(str, args))),
        print_lock=runtime.lock,
        observador_oculto=runtime.registrar_log_oculto,
    )

    imprimir("detalhe interno")
    imprimir("aviso visível")

    assert exibidas == ["aviso visível"]
    eventos = runtime.snapshot()["events"]
    assert len(eventos) == 1
    assert eventos[0]["message"] == "detalhe interno"
    assert eventos[0]["depth"] == "debug"


def test_print_oculto_em_stderr_preserva_canal_e_nivel_de_erro() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 10.0)
    imprimir = criar_print_filtrado(
        should_log=lambda _texto: False,
        raw_print=print,
        print_lock=runtime.lock,
        observador_oculto=runtime.registrar_log_oculto,
    )

    imprimir("diagnóstico interno", file=sys.stderr)

    eventos = runtime.snapshot()["events"]
    assert len(eventos) == 1
    assert eventos[0]["message"] == "diagnóstico interno"
    assert eventos[0]["source"] == "stderr"
    assert eventos[0]["level"] == "error"


def test_trace_identifica_primeira_fronteira_vermelha() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 10.0)
    runtime.configurar_estado_getter(lambda: {
        "diagnostico_traces_turno": [{
            "turno_id": "turno-000151",
            "origem": "desktop",
            "rota": "arquivos",
            "fase": "resposta",
            "finalizado": True,
            "sucesso": False,
            "etapas": {
                "interpretacao": {"duracao_ms": 8.0, "sucesso": True},
                "dispatcher": {"duracao_ms": 12.0, "sucesso": False},
                "execucao": {"duracao_ms": 1.0, "sucesso": False},
            },
        }],
    })

    resultado = runtime.consultar("trace last")

    assert resultado["ok"] is True
    assert resultado["kind"] == "trace"
    texto = "\n".join(resultado["lines"])
    assert "interpretacao" in texto
    assert "PRIMEIRA FRONTEIRA RED: dispatcher" in texto
    assert texto.index("dispatcher") < texto.index("execucao")


def test_central_de_erros_conta_ocorrencias_e_nao_inventa_causa() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 200.0)
    runtime.configurar_estado_getter(lambda: {
        "diagnostico_falhas": [
            {
                "componente": "llm_http",
                "codigo": "timeout_resposta",
                "error_code": "timeout_resposta",
                "tipo": "timeouterror",
                "classe": "degradacao",
                "impacto": "turno",
                "fallback": "resposta_local",
                "turno_id": "turno-000002",
                "ts_primeira": 100.0,
                "ts_ultima": 105.0,
                "ocorrencias": 2,
            },
            {
                "componente": "llm_http",
                "codigo": "timeout_resposta",
                "tipo": "timeouterror",
                "classe": "degradacao",
                "impacto": "turno",
                "fallback": "resposta_local",
                "turno_id": "turno-000003",
                "ts": 140.0,
            },
        ],
        "diagnostico_traces_turno": [{
            "turno_id": "turno-000003",
            "etapas": {
                "interpretacao": {"sucesso": True},
                "llm_http": {"sucesso": False},
                "resposta": {"sucesso": False},
            },
        }],
        "diagnostico_metricas": {
            "llm_http": {"ts_ultimo_sucesso": 90.0},
        },
    })

    resultado = runtime.consultar("errors")
    texto = "\n".join(resultado["lines"])

    assert "error_code=timeout_resposta" in texto
    assert "ocorrencias=3" in texto
    assert "trace=turno-000003" in texto
    assert "primeira_red=llm_http" in texto
    assert "ultimo_sucesso=" in texto
    assert "ultimo_sucesso=desconhecido" not in texto
    assert "causa=NAO_PROVADA" in texto


def test_central_abre_ocorrencias_retidas_por_seletor_allowlist() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 200.0)
    runtime.configurar_estado_getter(lambda: {
        "diagnostico_falhas": [{
            "componente": "llm_http",
            "error_code": "timeout_resposta",
            "tipo": "timeouterror",
            "classe": "degradacao",
            "impacto": "turno",
            "fallback": "resposta_local",
            "ocorrencias": 3,
            "ts_primeira": 100.0,
            "ts_ultima": 105.0,
            "ocorrencias_recentes": [
                {"ts": 100.0, "turno_id": "turno-000001"},
                {"ts": 105.0, "turno_id": "turno-000002"},
            ],
        }],
    })

    validada = validar_mensagem_cliente(
        {
            "type": "dev_query",
            "id": "d-erros",
            "command": "errors llm_http:timeout_resposta",
        },
        token="x",
        autenticado=True,
    )
    resultado = runtime.consultar(validada["command"])
    texto = "\n".join(resultado["lines"])

    assert resultado["ok"] is True
    assert "OCCURRENCE 1" in texto
    assert "trace=turno-000001" in texto
    assert "OCCURRENCE 2" in texto
    assert "NAO_RETIDAS=1" in texto


@pytest.mark.parametrize(
    ("confirmado", "codigo_esperado"),
    [
        (False, "UNVERIFIED_SUCCESS"),
        (None, "RECEIPT_MISSING"),
    ],
)
def test_central_detecta_inconsistencia_explicita_no_contrato_da_acao(
    confirmado,
    codigo_esperado,
) -> None:
    runtime = DevConsoleRuntime(clock=lambda: 200.0)
    runtime.configurar_estado_getter(lambda: {
        "ultima_acao_ts": 190.0,
        "ultima_acao_contrato": {
            "intent": "DELETE_FILE",
            "status": "executado",
            "executou": True,
            "confirmado": confirmado,
            "evidencia_confirmacao": "",
            "id_solicitacao": "turno-000010",
        },
    })

    texto = "\n".join(runtime.consultar("errors")["lines"])

    assert f"error_code={codigo_esperado}" in texto
    assert "evidencia=CONTRATO_ACAO" in texto
    assert "causa=NAO_PROVADA" in texto


def test_central_nao_cria_alerta_semantico_quando_receipt_confirma_efeito() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 200.0)
    runtime.configurar_estado_getter(lambda: {
        "ultima_acao_contrato": {
            "intent": "DELETE_FILE",
            "status": "executado",
            "executou": True,
            "confirmado": True,
            "evidencia_confirmacao": "arquivo_ausente_apos_delete",
        },
    })

    texto = "\n".join(runtime.consultar("errors")["lines"])

    assert "UNVERIFIED_SUCCESS" not in texto
    assert "RECEIPT_MISSING" not in texto
    assert "Nenhuma falha técnica observada" in texto


def test_inspect_pending_separa_conversa_de_autorizacao_operacional() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 10.0)
    runtime.configurar_estado_getter(lambda: {
        "pendencia_atual": {
            "id": "fala-1", "tipo": "esclarecimento", "status": "ativa",
            "foi_falada": True,
        },
        "pendencia_acao_canonica": {
            "id": "acao-1", "acao": "DELETE_FILE", "status": "ativa",
            "dominio": "arquivos", "referencia": "alvo-confirmado",
        },
    })

    resultado = runtime.consultar("inspect pending")
    texto = "\n".join(resultado["lines"])

    assert "CONVERSACIONAL" in texto
    assert "AÇÃO CANÔNICA" in texto
    assert "fala-1" in texto
    assert "acao-1" in texto


def test_inspect_pending_explica_owner_idade_ttl_e_ciclo_sem_mutar_estado() -> None:
    estado = {
        "pendencia_atual": {
            "id": "fala-ttl", "origem": "conversa", "tipo": "confirmacao",
            "status": "ativa", "foi_falada": True,
            "criada_em": 100.0, "expira_em": 200.0,
        },
        "pendencia_acao_canonica": {
            "id": "acao-ttl", "origem": "arquivos", "acao": "DELETE_FILE",
            "status": "em_processamento", "dominio": "arquivos",
            "criada_em": 120.0, "expira_em": 180.0,
        },
    }
    antes = {
        chave: dict(valor) for chave, valor in estado.items()
    }
    runtime = DevConsoleRuntime(clock=lambda: 150.0, estado_getter=lambda: estado)

    texto = "\n".join(runtime.consultar("inspect pending")["lines"])

    assert "owner=mental.pendencia_atual" in texto
    assert "idade_s=50.0" in texto
    assert "ttl_restante_s=50.0" in texto
    assert "ciclo=ATIVA" in texto
    assert "owner=mental.pendencia_acao_canonica" in texto
    assert "idade_s=30.0" in texto
    assert "ttl_restante_s=30.0" in texto
    assert "ciclo=EM_PROCESSAMENTO" in texto
    assert "confiabilidade=ESTADO_CANONICO" in texto
    assert estado == antes


def test_inspector_le_snapshot_canonico_e_explica_contexto_acao_e_receipt() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 150.0, estado_getter=lambda: {
        "mental": {
            "ultima_entrada_ts": 140.0,
            "turno_atual": {
                "intencao": "DELETE_FILE",
                "autoriza_execucao": True,
                "referencia_resolvida": {"alvo": "relatorio.txt"},
            },
            "ultima_acao_ts": 145.0,
            "ultima_acao_contrato": {
                "intent": "DELETE_FILE", "alvo": "relatorio.txt",
                "status": "executado", "origem": "executor_arquivos",
                "executou": True, "confirmado": True,
                "evidencia_confirmacao": "arquivo_ausente_apos_delete",
            },
        },
        "memoria_conversa": {"messages": []},
    })

    contexto = "\n".join(runtime.consultar("inspect context")["lines"])
    acao = "\n".join(runtime.consultar("inspect action last")["lines"])
    receipt = "\n".join(runtime.consultar("inspect receipt last")["lines"])

    assert "owner=mental.turno_atual" in contexto
    assert "idade_s=10.0" in contexto
    assert "INTENÇÃO RECONHECIDA: DELETE_FILE" in contexto
    assert "AUTORIZAÇÃO EXPLÍCITA: SIM" in contexto
    assert "ALVO RESOLVIDO: relatorio.txt" in contexto
    assert "owner=mental.ultima_acao_contrato" in acao
    assert "EXECUTOR CHAMADO: SIM" in acao
    assert "owner=mental.ultima_acao_contrato" in receipt
    assert "RECEIPT RECEBIDO: SIM" in receipt
    assert "EFEITO CONFIRMADO: SIM" in receipt
    assert "RESPOSTA DE SUCESSO PERMITIDA: SIM" in receipt


def test_inspect_memory_used_distingue_contexto_temporario_de_memoria_duravel() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 150.0, estado_getter=lambda: {
        "mental": {
            "fundamentacao_factual_turno": {
                "fonte": "wikipedia_pt", "confiavel": True,
                "ts": 148.0, "evidencia_dentro_validade": True,
            },
        },
        "memoria_conversa": {
            "messages": [{"role": "user", "content": "token=segredo"}],
            "memoria_fatos": [{"texto": "email pedro@example.com"}],
            "memoria_eventos": [{"texto": "evento privado"}],
        },
    })

    texto = "\n".join(runtime.consultar("inspect memory used")["lines"])

    assert "owner=memoria_conversa.messages tipo=CONTEXTO_TEMPORÁRIO itens=1" in texto
    assert "owner=memoria_conversa.memoria_fatos tipo=MEMÓRIA_DURÁVEL itens=1" in texto
    assert "owner=memoria_conversa.memoria_eventos tipo=MEMÓRIA_DURÁVEL itens=1" in texto
    assert "uso_no_turno=NAO_PROVADO" in texto
    assert "owner=mental.fundamentacao_factual_turno" in texto
    assert "fonte=wikipedia_pt" in texto
    assert "segredo" not in texto
    assert "pedro@example.com" not in texto
    assert "evento privado" not in texto


def test_inspect_event_por_id_le_buffer_sem_expor_segredo() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 150.0)
    evento = runtime.registrar_linha(
        "[SYSTEM] autenticação pedro@example.com token=segredo falhou",
        origem="stderr",
    )

    texto = "\n".join(
        runtime.consultar(f"inspect event {evento['id']}")["lines"]
    )

    assert f"INSPECT EVENT {evento['id'].upper()}" in texto
    assert "owner=dev_console.events" in texto
    assert "idade_s=0.0" in texto
    assert "source" in texto and "stderr" in texto
    assert "segredo" not in texto
    assert "pedro@example.com" not in texto
    assert "[protegido]" in texto


def test_consultas_dev_sao_allowlist_e_nao_terminal_shell() -> None:
    validada = validar_mensagem_cliente(
        {"type": "dev_query", "id": "d1", "command": "trace last"},
        token="x",
        autenticado=True,
    )
    assert validada == {"type": "dev_query", "id": "d1", "command": "trace last"}

    memoria = validar_mensagem_cliente(
        {"type": "dev_query", "id": "d-memory", "command": "inspect memory used"},
        token="x", autenticado=True,
    )
    evento = validar_mensagem_cliente(
        {"type": "dev_query", "id": "d-event", "command": "inspect event dev-00000001"},
        token="x", autenticado=True,
    )
    assert memoria["command"] == "inspect memory used"
    assert evento["command"] == "inspect event dev-00000001"

    with pytest.raises(ErroProtocoloDesktop, match="consulta DEV"):
        validar_mensagem_cliente(
            {"type": "dev_query", "id": "d2", "command": "python -c calc"},
            token="x",
            autenticado=True,
        )

    with pytest.raises(ErroProtocoloDesktop, match="consulta DEV"):
        validar_mensagem_cliente(
            {
                "type": "dev_query", "id": "d4",
                "command": "inspect event dev-00000001; calc",
            },
            token="x", autenticado=True,
        )

    with pytest.raises(ErroProtocoloDesktop, match="consulta DEV"):
        validar_mensagem_cliente(
            {
                "type": "dev_query",
                "id": "d3",
                "command": "errors llm_http:timeout_resposta; calc",
            },
            token="x",
            autenticado=True,
        )


def test_ponte_entrega_buffer_live_e_consulta_dev() -> None:
    dev = DevConsoleRuntime(clock=lambda: 10.0)
    espelho = EspelhoStreamDev(io.StringIO(), dev, origem="stdout")
    espelho.write("💬 Você:\n> \n")
    dev.registrar_linha("[SYSTEM] evento anterior")
    dev.configurar_estado_getter(lambda: {})
    ponte = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        dev_console_getter=dev.snapshot,
        dev_console_consultar=dev.consultar,
        dev_console_interval_s=0.05,
        log=lambda _texto: None,
    )
    ponte.iniciar()
    try:
        with socket.create_connection(ponte.endereco, timeout=1.0) as cliente:
            cliente.sendall((json.dumps({
                "type": "hello",
                "token": ponte.token,
            }) + "\n").encode())
            snapshot = _linha(cliente)
            assert snapshot["dev_console"]["events"][0]["message"] == (
                "[SYSTEM] evento anterior"
            )
            assert len(snapshot["dev_console"]["events"]) == 1

            espelho.write(
                "💬 Você:\n> \n"
                "💬 Você: 'pode ligar a luz' | origem=desktop\n"
            )
            entrada = _ate_tipo(cliente, "dev_events")
            assert [e["message"] for e in entrada["events"]] == [
                "💬 Você: 'pode ligar a luz' | origem=desktop"
            ]
            dev.registrar_linha("[ROUTER] evento ao vivo")
            lote = _ate_tipo(cliente, "dev_events")
            assert lote["events"][-1]["category"] == "ROUTER"

            cliente.sendall((json.dumps({
                "type": "dev_query",
                "id": "consulta-1",
                "command": "status",
            }) + "\n").encode())
            resultado = _ate_tipo(cliente, "dev_query_result")
            assert resultado["id"] == "consulta-1"
            assert resultado["result"]["kind"] == "status"
    finally:
        ponte.parar()
