from __future__ import annotations

from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
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
