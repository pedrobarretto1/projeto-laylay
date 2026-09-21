from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from cliente.terminal_2.desenvolvedor import (
    CORES_CATEGORIA,
    EventoDesenvolvedor,
    PaginaDesenvolvedor,
    _categoria_evento,
)
from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    sanitizar_evento_dev,
    sanitizar_retrato_dev,
)
from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
from mente_laylay.integracao.eventos_dev import (
    CATEGORIAS_DEV,
    classificar_categoria_evento_dev,
)
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.diagnostico_mente import (
    DiagnosticoMenteRuntime,
    construir_diagnostico_mente,
    formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.observabilidade import (
    ObservabilidadeMenteRuntime,
    classificar_falha_tecnica,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)


def _runtime_observabilidade(estado, agora=lambda: 100.0):
    def atualizar(**campos):
        estado.update(campos)

    return ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=atualizar,
        clock=agora,
    )


def test_metricas_guardam_ultimo_media_maximo_e_falhas() -> None:
    estado = {}
    runtime = _runtime_observabilidade(estado)

    runtime.registrar_metrica("interpretação", 100.0, True)
    runtime.registrar_metrica("interpretação", 300.0, False)

    metrica = estado["diagnostico_metricas"]["interpretação"]
    assert metrica["ultimo_ms"] == 300.0
    assert metrica["media_ms"] == 200.0
    assert metrica["max_ms"] == 300.0
    assert metrica["amostras"] == 2
    assert metrica["falhas"] == 1


def test_metricas_marcam_orcamento_sem_cancelar_o_fluxo() -> None:
    estado = {}
    runtime = _runtime_observabilidade(estado)

    metrica = runtime.registrar_metrica("dispatcher", 150.0, True)

    assert metrica["orcamento_ms"] == 120.0
    assert metrica["excedeu_orcamento"] is True
    assert metrica["excessos"] == 1


def test_metrica_preserva_instante_do_ultimo_sucesso_apos_falha() -> None:
    estado, agora = {}, [100.0]
    runtime = _runtime_observabilidade(estado, agora=lambda: agora[0])

    runtime.registrar_metrica("llm_http", 10.0, True)
    agora[0] = 105.0
    runtime.registrar_metrica("llm_http", 20.0, False)

    metrica = estado["diagnostico_metricas"]["llm_http"]
    assert metrica["ts"] == 105.0
    assert metrica["ts_ultimo_sucesso"] == 100.0


def test_tamanho_de_prompt_guarda_so_contagens_por_origem() -> None:
    estado = {}
    runtime = _runtime_observabilidade(estado)

    medida = runtime.registrar_tamanho_prompt("prompt_memoria", 321)

    assert medida["ultimo_chars"] == 321
    assert estado["diagnostico_prompts"]["prompt_memoria"]["max_chars"] == 321
    assert "conteudo" not in repr(estado["diagnostico_prompts"]).casefold()


def test_historico_de_falhas_remove_url_caminho_e_mensagem_do_erro() -> None:
    estado = {}
    runtime = _runtime_observabilidade(estado)

    runtime.registrar_falha(
        "TTS https://privado.test/token",
        r"falha em C:\Users\Pedro\segredo.txt",
        erro=RuntimeError("senha=123 e conteúdo privado"),
    )

    falha = estado["diagnostico_falhas"][-1]
    serializado = repr(falha).casefold()
    assert "privado.test" not in serializado
    assert "users" not in serializado
    assert "senha" not in serializado
    assert falha["tipo"] == "runtimeerror"


def test_falha_operacional_guarda_apenas_metadados_sanitizados_do_turno() -> None:
    estado = {}
    runtime = _runtime_observabilidade(estado)

    runtime.registrar_falha(
        "executor arquivos",
        "falha escrita",
        erro=RuntimeError("conteúdo secreto"),
        dominio="Arquivos locais",
        fase="Pós criação",
        turno_id=r"C:\privado\turno-42",
    )

    falha = estado["diagnostico_falhas"][-1]
    assert falha["dominio"] == "arquivos_locais"
    assert falha["fase"] == "pós_criação"
    assert "privado" not in falha["turno_id"]
    assert "secreto" not in repr(falha).casefold()


def test_classificacao_distingue_degradacao_de_defeito_sem_ler_mensagem() -> None:
    timeout = classificar_falha_tecnica(
        "llm_http", "timeout_resposta",
        erro=TimeoutError("prompt privado não pode ser classificado"),
        fallback="contingencia_conversacional",
    )
    defeito = classificar_falha_tecnica(
        "turno", "erro_resposta_ia", erro=TypeError("conteúdo secreto"),
    )

    assert timeout == {
        "classe": "degradacao",
        "impacto": "turno",
        "fallback": "contingencia_conversacional",
    }
    assert defeito == {
        "classe": "defeito",
        "impacto": "turno",
        "fallback": "nenhum",
    }
    assert "privado" not in repr(timeout)
    assert "secreto" not in repr(defeito)


def test_falha_registra_se_classificacao_foi_explicita_ou_heuristica() -> None:
    estado = {}
    runtime = _runtime_observabilidade(estado)

    inferida = runtime.registrar_falha("llm_http", "timeout_resposta")
    explicita = runtime.registrar_falha(
        "politica",
        "acao_bloqueada",
        classe="esperada",
        impacto="nenhum",
    )

    assert inferida["classe_origem"] == "heuristica"
    assert inferida["impacto_origem"] == "heuristica"
    assert explicita["classe_origem"] == "explicita"
    assert explicita["impacto_origem"] == "explicita"


def test_relator_de_falhas_auxiliares_suprime_repeticao_sem_perder_diagnostico() -> None:
    estado, agora, logs = {}, [100.0], []
    runtime = ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=lambda **campos: estado.update(campos),
        clock=lambda: agora[0],
        log=logs.append,
        janela_repeticao_s=30,
    )

    primeira = runtime.relatar_falha(
        "pesquisa jogos", "cache leitura", erro=RuntimeError("segredo"),
    )
    repetida = runtime.relatar_falha(
        "pesquisa jogos", "cache leitura", erro=RuntimeError("outro segredo"),
    )
    agora[0] += 31
    posterior = runtime.relatar_falha(
        "pesquisa jogos", "cache leitura", erro=RuntimeError("segredo final"),
    )

    assert primeira["registrada"] is True
    assert repetida == {
        "registrada": False, "suprimidas": 1,
        "componente": "pesquisa_jogos", "codigo": "cache_leitura",
        "tipo": "runtimeerror",
        "classe": "defeito", "impacto": "servico", "fallback": "nenhum",
    }
    assert posterior["registrada"] is True
    assert posterior["suprimidas"] == 1
    assert len(estado["diagnostico_falhas"]) == 2
    assert len(logs) == 2
    assert "segredo" not in repr(logs).casefold()
    assert "1 repetição" in logs[-1]


def test_repeticao_suprimida_permanece_contabilizada_no_estado_compartilhado() -> None:
    estado, agora = {}, [100.0]
    runtime = ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=lambda **campos: estado.update(campos),
        clock=lambda: agora[0],
        janela_repeticao_s=30,
    )

    runtime.relatar_falha("llm_http", "timeout_resposta", erro=TimeoutError())
    agora[0] = 105.0
    runtime.relatar_falha("llm_http", "timeout_resposta", erro=TimeoutError())

    falhas = estado["diagnostico_falhas"]
    assert len(falhas) == 1
    assert falhas[0]["ocorrencias"] == 2
    assert falhas[0]["ts_primeira"] == 100.0
    assert falhas[0]["ts_ultima"] == 105.0


def test_historicos_sao_curtos_e_nao_persistem_texto_da_sugestao() -> None:
    estado = {}
    runtime = ObservabilidadeMenteRuntime(
        estado_getter=lambda chave, padrao=None: estado.get(chave, padrao),
        estado_setter=lambda **campos: estado.update(campos),
        clock=lambda: 100.0,
        limite_eventos=5,
    )
    for indice in range(9):
        runtime.registrar_decisao(
            "proatividade", "adiar", (f"motivo {indice}",), categoria="musica",
        )

    assert len(estado["diagnostico_decisoes"]) == 5
    assert all("texto" not in item for item in estado["diagnostico_decisoes"])


def test_ciclo_de_vida_do_servico_e_agregado_sem_historico_infinito() -> None:
    estado = {}
    runtime = _runtime_observabilidade(estado)

    runtime.registrar_evento_servico("Ouvido C:/privado", "ativo", tentativa=1)
    runtime.registrar_evento_servico(
        "Ouvido C:/privado", "queda", tentativa=1,
        fallback="reinicio_agendado",
    )
    runtime.registrar_evento_servico(
        "Ouvido C:/privado", "reiniciando", tentativa=2,
    )
    runtime.registrar_evento_servico(
        "Ouvido C:/privado", "orfao", tentativa=2,
        fallback="encerramento_do_processo",
    )
    final = runtime.registrar_evento_servico(
        "Ouvido C:/privado", "ativo", tentativa=2,
    )

    assert len(estado["diagnostico_servicos"]) == 1
    assert final["quedas"] == 1
    assert final["reinicios"] == 1
    assert final["orfaos"] == 1
    assert final["estado"] == "ativo"
    assert "privado" not in repr(estado["diagnostico_servicos"]).casefold()


def test_diagnostico_consolida_protecoes_sem_recontar_eventos() -> None:
    estado = {
        "mental": {
            "diagnostico_servicos": {
                "ouvido": {
                    "estado": "orfao", "orfaos": 2, "quedas": 2,
                    "reinicios": 1, "falhas_inicializacao": 0,
                },
            },
        },
        "conversacional": {}, "percepcao": {}, "continuidades": {},
    }
    runtime = DiagnosticoMenteRuntime(
        estado_getter=lambda: estado,
        saude_getter=lambda: {},
        linguagem_natural_getter=lambda: {
            "reutilizadas_no_turno": 3,
            "execucao_turno": {"reutilizadas": 4, "aguardadas": 2},
        },
        fala_operacional_getter=lambda: {"duplicadas_suprimidas": 5},
        falar=lambda *_args: None,
        log=lambda *_args: None,
    )

    diagnostico = runtime.snapshot()
    texto = formatar_diagnostico_terminal(diagnostico)

    assert diagnostico["protecoes_ciclo"] == {
        "reentradas_evitadas": 3,
        "execucoes_duplicadas_convergidas": 6,
        "falas_duplicadas_suprimidas": 5,
        "servicos_orfaos_atuais": 1,
        "servicos_orfaos_detectados": 2,
    }
    assert "reentradas_evitadas=3" in texto
    assert "execuções_duplicadas_convergidas=6" in texto
    assert "órfãos_atuais=1 órfãos_detectados=2" in texto


def test_porteiro_registra_por_que_sugestao_foi_descartada() -> None:
    decisoes = []
    runtime = PorteiroProatividadeRuntime(
        contexto_getter=lambda: {"modo_jogo_ativo": True},
        agora=lambda: 100.0,
        registrar_decisao_cb=lambda *args, **kwargs: decisoes.append((args, kwargs)),
    )

    runtime.avaliar(tipo="musica", texto="Esta frase privada não pode ir ao diagnóstico")

    assert decisoes
    args, kwargs = decisoes[-1]
    assert args[0:2] == ("proatividade", "descartar")
    assert kwargs["categoria"] == "musica"
    assert "frase privada" not in repr(decisoes).casefold()
    assert "jogo em andamento" in args[2]


def test_diagnostico_exibe_latencias_falhas_e_ultima_decisao_sanitizadas() -> None:
    estado = {
        "mental": {
            "diagnostico_metricas": {
                "tts_total": {"ultimo_ms": 450, "media_ms": 400, "max_ms": 600, "amostras": 3},
            },
            "diagnostico_falhas": [
                {
                    "componente": "tts", "codigo": "falha_audio",
                    "tipo": "RuntimeError", "classe": "degradacao",
                    "impacto": "fala", "fallback": "tts_local_pyttsx",
                },
            ],
            "diagnostico_decisoes": [
                {
                    "componente": "proatividade", "acao": "adiar", "categoria": "rotina",
                    "motivos": ["momento de foco"],
                },
            ],
            "diagnostico_servicos": {
                "ouvido": {
                    "estado": "reinicio_agendado", "tentativa": 2,
                    "atraso_s": 5, "fallback": "reinicio_automatico",
                    "quedas": 1, "reinicios": 0, "falhas_inicializacao": 0,
                },
            },
        },
        "conversacional": {}, "percepcao": {}, "continuidades": {},
        "memoria_conversa": {"messages": [{"content": "não pode aparecer"}]},
    }

    diagnostico = construir_diagnostico_mente(estado, {})
    texto = formatar_diagnostico_terminal(diagnostico)

    assert diagnostico["latencias"]["tts_total"]["media_ms"] == 400.0
    assert "tts_total=450ms" in texto
    assert "proatividade=adiar" in texto
    assert "tts=falha_audio" in texto
    assert "degradações=1" in texto
    assert "classe=degradacao impacto=fala fallback=tts_local_pyttsx" in texto
    assert "serviços de fundo: total=1 ativos=0 degradados=1 quedas=1 reinícios=0 órfãos=0" in texto
    assert "serviço: ouvido=reinicio_agendado tentativa=2 fallback=reinicio_automatico" in texto
    assert "não pode aparecer" not in texto


def test_queda_de_servico_recuperada_nao_permanece_como_falha_atual() -> None:
    estado = {
        "mental": {
            "diagnostico_falhas": [{
                "componente": "servico_laylay-ouvido",
                "codigo": "queda_background",
                "tipo": "RuntimeError",
                "classe": "degradacao",
                "impacto": "servico",
                "fallback": "reinicio_agendado",
                "ts": 100.0,
            }],
            "diagnostico_servicos": {
                "laylay-ouvido": {
                    "estado": "ativo", "tentativa": 2,
                    "quedas": 1, "reinicios": 1, "ts": 110.0,
                },
            },
        },
        "conversacional": {}, "percepcao": {}, "continuidades": {},
    }

    diagnostico = construir_diagnostico_mente(estado, {})
    texto = formatar_diagnostico_terminal(diagnostico)

    assert diagnostico["falhas_recentes"] == []
    assert diagnostico["falhas_recuperadas"] == 1
    assert "falhas técnicas recentes: 0" in texto
    assert "recuperadas=1" in texto


def test_estado_mental_inicial_possui_telemetria_vazia() -> None:
    mente = estado_mental_inicial()

    assert mente["diagnostico_metricas"] == {}
    assert mente["diagnostico_falhas"] == []
    assert mente["diagnostico_decisoes"] == []
    assert mente["diagnostico_servicos"] == {}


def test_inspetor_le_snapshot_do_estado_compartilhado_real_sem_segunda_copia() -> None:
    estado = EstadoCompartilhadoRuntime(
        mental={
            "ultima_entrada_ts": 140.0,
            "turno_atual": {
                "intencao": "OPEN_URL",
                "autoriza_execucao": False,
                "referencia_resolvida": {"alvo": "example.com"},
            },
            "pendencia_acao_canonica": {
                "id": "acao-real", "origem": "navegador",
                "acao": "OPEN_URL", "status": "ativa",
                "criada_em": 145.0, "expira_em": 200.0,
            },
            "diagnostico_servicos": {
                "ouvido": {"estado": "ativo", "tentativa": 1},
            },
        },
        memoria_conversa={
            "messages": [{"role": "user", "content": "conteúdo privado"}],
            "memoria_fatos": [], "memoria_eventos": [],
        },
    )
    runtime = DevConsoleRuntime(clock=lambda: 150.0, estado_getter=estado.snapshot)

    contexto = "\n".join(runtime.consultar("inspect context")["lines"])
    pendencia = "\n".join(runtime.consultar("inspect pending")["lines"])
    memoria = "\n".join(runtime.consultar("inspect memory used")["lines"])
    status = "\n".join(runtime.consultar("status all")["lines"])

    assert "INTENÇÃO RECONHECIDA: OPEN_URL" in contexto
    assert "AUTORIZAÇÃO EXPLÍCITA: NÃO" in contexto
    assert "owner=mental.pendencia_acao_canonica" in pendencia
    assert "ttl_restante_s=50.0" in pendencia
    assert "owner=memoria_conversa.messages" in memoria
    assert "conteúdo privado" not in memoria
    assert "ouvido" in status and "ativo" in status


def test_composicao_real_entrega_snapshot_completo_ao_inspetor() -> None:
    fonte = (Path(__file__).resolve().parents[2] / "laylay.py").read_text(
        encoding="utf-8",
    )

    assert (
        "_dev_console_runtime.configurar_estado_getter(\n"
        "    _estado_compartilhado_runtime.snapshot\n"
        ")"
    ) in fonte
    assert (
        "_dev_console_runtime.configurar_pressao_getter(\n"
        "    _desktop_bridge_runtime.diagnostico\n"
        ")"
    ) in fonte
    assert 'snapshot().get("mental", {})' not in fonte


def test_perf_memory_expoe_janela_orcamento_e_trace_da_propria_fronteira() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 200.0, estado_getter=lambda: {
        "mental": {
            "diagnostico_metricas": {
                "preparacao_prompt": {
                    "ultimo_ms": 180.0, "p50_ms": 90.0, "p95_ms": 180.0,
                    "max_ms": 210.0, "orcamento_ms": 120.0,
                    "amostras": 3, "excessos": 2,
                    "excedeu_orcamento": True,
                },
                "dispatcher": {
                    "ultimo_ms": 900.0, "p50_ms": 800.0, "p95_ms": 900.0,
                    "max_ms": 900.0, "orcamento_ms": 120.0,
                    "amostras": 2, "excessos": 2,
                    "excedeu_orcamento": True,
                },
            },
            "diagnostico_traces_turno": [{
                "turno_id": "turno-000007",
                "etapas": {
                    "preparacao_prompt": {
                        "duracao_ms": 180.0, "sucesso": True,
                    },
                    "dispatcher": {"duracao_ms": 900.0, "sucesso": True},
                },
            }],
        },
    })

    texto = "\n".join(runtime.consultar("perf memory")["lines"])

    assert "preparacao_prompt" in texto
    assert "dispatcher" not in texto
    assert "MÁXIMO" in texto
    assert "amostras=3" in texto
    assert "excessos=2" in texto
    assert "FRONTEIRA_LENTA=preparacao_prompt" in texto
    assert "trace=turno-000007" in texto


def test_perf_publica_pressao_e_descartes_dos_buffers_reais() -> None:
    dev = DevConsoleRuntime(
        clock=lambda: 200.0,
        limite_eventos=100,
        estado_getter=lambda: {"mental": {}},
    )
    ponte = DesktopBridgeRuntime(
        enviar_entrada=lambda _texto: True,
        historico_getter=list,
        estado_getter=dict,
        log=lambda _texto: None,
    )
    for indice in range(105):
        dev.registrar_linha(f"[SYSTEM] evento dev {indice}")
    for indice in range(125):
        ponte.publicar_evento(f"evento bridge {indice}")

    dev.configurar_pressao_getter(ponte.diagnostico)
    retrato_dev = dev.snapshot()
    retrato_ponte = ponte.diagnostico()
    texto = "\n".join(dev.consultar("perf")["lines"])

    assert retrato_dev["events_dropped"] == 5
    assert retrato_ponte["eventos_retidos"] == 120
    assert retrato_ponte["eventos_descartados"] == 5
    assert "PRESSÃO DOS BUFFERS" in texto
    assert "dev_console eventos=100/100 descartados=5" in texto
    assert "desktop_bridge eventos=120/120 descartados=5" in texto


def test_perf_llm_expoe_orcamento_canonico_sem_conteudo_do_modelo() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 200.0, estado_getter=lambda: {
        "mental": {
            "diagnostico_orcamento_llm": {
                "modo": "orcamento_unico",
                "limite_chamadas_turno": 2,
                "turno_atual": {
                    "turno_id": "turno-000009", "classe": "normal",
                    "ativo": True, "chamadas": 2,
                    "tipos": ["principal", "reparo_json"],
                },
                "chamadas_autorizadas": 7,
                "chamadas_bloqueadas": 3,
                "bloqueios_por_motivo": {"limite_chamadas": 3},
                "falhas_consecutivas": 1,
                "circuito_aberto": False,
                "conteudo_persistido": False,
                "autoriza_execucao": False,
                "prompt": "segredo que não pode vazar",
            },
        },
    })

    texto = "\n".join(runtime.consultar("perf llm")["lines"])

    assert "ORÇAMENTO LLM" in texto
    assert "turno=turno-000009" in texto
    assert "chamadas=2/2" in texto
    assert "autorizadas=7 bloqueadas=3" in texto
    assert "limite_chamadas=3" in texto
    assert "circuito_aberto=não" in texto
    assert "segredo que não pode vazar" not in texto


def test_perf_actions_seleciona_orcamentos_de_decisao_e_execucao() -> None:
    runtime = DevConsoleRuntime(estado_getter=lambda: {"mental": {
        "diagnostico_metricas": {
            "dispatcher": {
                "ultimo_ms": 100.0, "p50_ms": 90.0, "p95_ms": 110.0,
                "max_ms": 110.0, "orcamento_ms": 120.0, "amostras": 4,
            },
            "execucao": {
                "ultimo_ms": 1600.0, "p50_ms": 800.0, "p95_ms": 1600.0,
                "max_ms": 1600.0, "orcamento_ms": 1500.0,
                "amostras": 2, "excessos": 1,
                "excedeu_orcamento": True,
            },
            "preparacao_prompt": {
                "ultimo_ms": 40.0, "orcamento_ms": 120.0, "amostras": 1,
            },
        },
    }})

    texto = "\n".join(runtime.consultar("perf actions")["lines"])

    assert "dispatcher" in texto
    assert "execucao" in texto
    assert "preparacao_prompt" not in texto
    assert "FRONTEIRA_LENTA=execucao" in texto


def test_captura_normal_e_limitada_nao_consulta_fontes_externas() -> None:
    chamadas = {"estado": 0, "pressao": 0}

    def estado():
        chamadas["estado"] += 1
        return {}

    def pressao():
        chamadas["pressao"] += 1
        return {}

    runtime = DevConsoleRuntime(limite_eventos=100, estado_getter=estado)
    runtime.configurar_pressao_getter(pressao)

    for indice in range(150):
        runtime.registrar_linha(f"[SYSTEM] evento {indice}")

    assert chamadas == {"estado": 0, "pressao": 0}
    assert len(runtime.snapshot()["events"]) == 100
    assert runtime.snapshot()["events_dropped"] == 50


def test_bridge_preserva_contadores_publicos_e_sanitiza_valores_invalidos() -> None:
    retrato = sanitizar_retrato_dev({
        "sequence": 9,
        "event_limit": "100",
        "events_dropped": "7",
        "events": [],
    })
    invalido = sanitizar_retrato_dev({
        "event_limit": "não-numérico",
        "events_dropped": object(),
    })

    assert retrato["event_limit"] == 100
    assert retrato["events_dropped"] == 7
    assert invalido["event_limit"] == 0
    assert invalido["events_dropped"] == 0


def test_interface_inicia_normal_e_so_exibe_trace_quando_solicitado() -> None:
    pagina = SimpleNamespace(
        _categoria_ativa="ALL",
        _profundidade_ativa="normal",
    )
    normal = EventoDesenvolvedor(
        "normal", "", "info", "SYSTEM", datetime.now(),
        profundidade="normal",
    )
    trace = EventoDesenvolvedor(
        "trace", "", "info", "TRACE", datetime.now(),
        profundidade="trace",
    )

    assert PaginaDesenvolvedor._evento_visivel(pagina, normal) is True
    assert PaginaDesenvolvedor._evento_visivel(pagina, trace) is False

    pagina._profundidade_ativa = "trace"
    assert PaginaDesenvolvedor._evento_visivel(pagina, trace) is True


def test_perf_integra_observabilidade_real_e_aponta_primeira_fronteira_lenta() -> None:
    estado = {}
    observabilidade = _runtime_observabilidade(estado)
    observabilidade.iniciar_trace_turno(
        "turno-000012", origem="terminal", rota="acao",
    )
    observabilidade.registrar_metrica("dispatcher", 80.0, True)
    observabilidade.registrar_metrica("execucao", 1750.0, True)
    runtime = DevConsoleRuntime(estado_getter=lambda: {"mental": estado})

    texto = "\n".join(runtime.consultar("perf actions")["lines"])

    assert "FRONTEIRA_LENTA=dispatcher" not in texto
    assert "FRONTEIRA_LENTA=execucao" in texto
    assert "trace=turno-000012" in texto
    assert "evidencia=TRACE_ETAPA" in texto


def test_categoria_dev_distingue_fala_plano_e_transporte_pelo_owner() -> None:
    runtime = DevConsoleRuntime(clock=lambda: 100.0)

    fala = runtime.registrar_linha(
        "╭─ ◕‿◕ Laylay: O tempo continua encoberto.",
    )
    plano = runtime.registrar_linha(
        "🧠 [PLANO:FASE] fase=tratado_prioritario",
    )
    fala_inicial = runtime.registrar_linha(
        "⚠️ [FALA INICIAL] entrega não foi confirmada em 45s",
    )
    transporte = runtime.registrar_linha(
        "[SYSTEM] Mensagem enviada à ponte",
    )

    assert fala["category"] == "IA"
    assert plano["category"] == "ROUTER"
    assert fala_inicial["category"] == "IA"
    assert fala_inicial["level"] == "warning"
    assert transporte["category"] == "SYSTEM"


def test_categoria_ui_distingue_autoria_estado_e_receipt_de_acao() -> None:
    assert _categoria_evento(
        "Resposta entregue", "A fala final chegou à conversa.", "success",
    ) == "IA"
    assert _categoria_evento(
        "Falando", "Estado da mente · emoção calma.", "info",
    ) == "IA"
    assert _categoria_evento(
        "Ação confirmada", "Resultado confirmado pela mente", "success",
    ) == "AUTONOMY"
    assert _categoria_evento(
        "Pedido recebido", "A mente confirmou a entrada.", "success",
    ) == "SYSTEM"


def test_categoria_explicita_e_owner_vencem_severidade_e_heuristica() -> None:
    assert classificar_categoria_evento_dev(
        "[SYSTEM] conteúdo menciona Laylay",
        "resposta da IA",
        "error",
    ) == "SYSTEM"
    assert classificar_categoria_evento_dev(
        "Falha ao sintetizar fala",
        nivel="warning",
        categoria_explicita="VOZ",
    ) == "IA"
    assert classificar_categoria_evento_dev(
        "Falha sem owner conhecido",
        nivel="error",
    ) == "ERRORS"


def test_taxonomia_do_nucleo_e_paleta_da_interface_sao_a_mesma() -> None:
    assert set(CORES_CATEGORIA) == set(CATEGORIAS_DEV)


def test_bridge_preserva_categoria_canonica_sem_reclassificar_evento() -> None:
    evento = sanitizar_evento_dev({
        "id": "dev-ia-1",
        "sequence": 1,
        "timestamp": 100.0,
        "level": "warning",
        "category": "IA",
        "event": "fala_inicial",
        "message": "Entrega da fala ainda não confirmada.",
        "source": "runtime",
        "depth": "normal",
    })

    assert evento["category"] == "IA"
    assert evento["level"] == "warning"
