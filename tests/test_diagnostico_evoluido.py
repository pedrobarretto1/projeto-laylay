from __future__ import annotations

from mente_laylay.autonomia.porteiro_proatividade import PorteiroProatividadeRuntime
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.diagnostico_mente import (
    construir_diagnostico_mente,
    formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.observabilidade import ObservabilidadeMenteRuntime


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
                {"componente": "tts", "codigo": "falha_audio", "tipo": "RuntimeError"},
            ],
            "diagnostico_decisoes": [
                {
                    "componente": "proatividade", "acao": "adiar", "categoria": "rotina",
                    "motivos": ["momento de foco"],
                },
            ],
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
    assert "não pode aparecer" not in texto


def test_estado_mental_inicial_possui_telemetria_vazia() -> None:
    mente = estado_mental_inicial()

    assert mente["diagnostico_metricas"] == {}
    assert mente["diagnostico_falhas"] == []
    assert mente["diagnostico_decisoes"] == []
