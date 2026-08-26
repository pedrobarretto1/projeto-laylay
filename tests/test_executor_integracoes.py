from __future__ import annotations

import mente_laylay.autonomia.executor_integracoes as modulo
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_integracoes import (
    DependenciasExecutorIntegracoes,
    executar_intencao_integracoes,
)
from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.integracao.registro_iot import registrar_iot


class _IoTExecutavel:
    def __init__(self, executar):
        self._executar = executar

    def detectar(self, _texto, _estado=None): return None
    def executar(self, resultado, texto=""): return self._executar(resultado, texto)
    def retrato_para_mente(self, _texto=""): return {"dispositivos": []}


def _dependencias(
    eventos: list[tuple], executar_iot=None, iot=None,
) -> DependenciasExecutorIntegracoes:
    return DependenciasExecutorIntegracoes(
        marcar_resultado=lambda status, *args, **kwargs: eventos.append(
            ("resultado", status, args, kwargs)
        ),
        falar_por_status=lambda *args, **kwargs: eventos.append(
            ("fala_status", args, kwargs)
        ),
        contexto_fala=lambda: {"origem": "teste"},
        iot=(iot or (registrar_iot(_IoTExecutavel(executar_iot)) if executar_iot else None)),
    )


def _executar(
    intent: str,
    *,
    resultado: dict | None = None,
    params: dict | None = None,
    ctx: dict | None = None,
    eventos: list[tuple] | None = None,
) -> ResultadoDespacho:
    eventos = eventos if eventos is not None else []
    resultado = resultado or {"intent": intent, "params": params or {}}
    return executar_intencao_integracoes(
        intent,
        resultado,
        params or {},
        "texto de teste",
        "pc_a",
        ctx or {},
        _dependencias(
            eventos,
            (ctx or {}).get("_executar_intencao_iot"),
            (ctx or {}).get("_registro_iot_runtime"),
        ),
    )


def test_executor_integracoes_ignora_dominio_desconhecido() -> None:
    assert _executar("PLAYLIST_PLAY") == ResultadoDespacho.nao_tratado()


def test_sugestao_repassa_resultado_e_texto_originais() -> None:
    chamadas: list[tuple] = []
    resultado = {
        "intent": "SUGGEST_ACTION",
        "params": {"intent_sugerido": "IOT_CONTROL"},
    }

    despacho = executar_intencao_integracoes(
        "SUGGEST_ACTION",
        resultado,
        resultado["params"],
        "talvez ligar a luz",
        "pc_a",
        {
            "_registrar_sugestao_indireta": lambda *args: chamadas.append(args) or True
        },
        _dependencias([]),
    )

    assert despacho == ResultadoDespacho.concluido()
    assert chamadas == [(resultado, "talvez ligar a luz")]


def test_sugestao_sem_integracao_retorna_falso_mas_permanece_tratada() -> None:
    despacho = _executar("SUGGEST_ACTION")

    assert despacho.tratado is True
    assert despacho.retorno is False


def test_iot_ausente_ou_nao_tratado_nao_inventa_execucao() -> None:
    ausente = _executar("IOT_CONTROL")
    recusado = _executar(
        "IOT_CONTROL",
        ctx={"_executar_intencao_iot": lambda *_args: {"handled": False}},
    )

    assert ausente == ResultadoDespacho.concluido(False)
    assert recusado == ResultadoDespacho.concluido(False)


def test_iot_repassa_confirmacao_erro_e_plano_de_resposta() -> None:
    eventos: list[tuple] = []
    falas: list[tuple] = []

    despacho = _executar(
        "IOT_CONTROL",
        eventos=eventos,
        ctx={
            "_registro_iot_runtime": registrar_iot(_IoTExecutavel(lambda *_args: {
                "handled": True,
                "ok": False,
                "status": "indisponivel",
                "confirmado": False,
                "erro": "timeout",
                "plano_resposta": {
                    "fala": "A luz não respondeu.",
                    "emocao": "preocupada",
                    "nivel": 2,
                },
            })),
            "falar_com_lipsync": lambda *args: falas.append(args),
        },
    )

    assert despacho == ResultadoDespacho.concluido()
    assert eventos == [(
        "resultado",
        "indisponivel",
        (),
        {"executou": False, "confirmado": False, "detalhe": "timeout"},
    )]
    assert falas == [("A luz não respondeu.", "preocupada", 2)]


def test_arquivos_repassa_todas_as_dependencias_ao_executor_existente(
    monkeypatch,
) -> None:
    chamadas: list[tuple] = []

    def falso_executor(*args, **kwargs):
        chamadas.append((args, kwargs))
        return True

    monkeypatch.setattr(modulo, "executar_intencao_arquivos", falso_executor)
    eventos: list[tuple] = []
    deps = _dependencias(eventos)
    despacho = executar_intencao_integracoes(
        "CREATE_FOLDER",
        {"intent": "CREATE_FOLDER", "params": {"nome": "teste"}},
        {"nome": "teste"},
        "cria uma pasta teste",
        "pc_b",
        {},
        deps,
    )

    assert despacho == ResultadoDespacho.concluido()
    args, kwargs = chamadas[0]
    assert args[:3] == ("CREATE_FOLDER", {"nome": "teste"}, "pc_b")
    assert kwargs["texto_original"] == "cria uma pasta teste"
    assert kwargs["marcar_resultado"] is deps.marcar_resultado
    assert callable(kwargs["registrar_arquivo"])
    assert callable(kwargs["item_local_existe"])
    assert callable(kwargs["resolver_caminho_local"])
    assert callable(kwargs["resolver_referencia_arquivo_contextual"])


def test_midia_repassa_callbacks_ao_executor_existente(monkeypatch) -> None:
    chamadas: list[tuple] = []

    def falso_executor(*args, **kwargs):
        chamadas.append((args, kwargs))
        return False

    monkeypatch.setattr(modulo, "executar_media_control", falso_executor)
    deps = _dependencias([])
    despacho = executar_intencao_integracoes(
        "MEDIA_CONTROL",
        {"intent": "MEDIA_CONTROL", "params": {"acao": "next"}},
        {"acao": "next"},
        "próxima música",
        "ambos",
        {},
        deps,
    )

    assert despacho == ResultadoDespacho.concluido(False)
    args, kwargs = chamadas[0]
    assert args[:3] == ({"acao": "next"}, "próxima música", "ambos")
    assert kwargs["falar_por_status"] is deps.falar_por_status
    assert kwargs["ctx_fala"] is deps.contexto_fala


def test_roteador_principal_delega_iot_e_registra_contrato() -> None:
    resultados = []
    falas: list[tuple] = []

    retorno = executar_intencao(
        {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "luz"}},
        "liga a luz",
        {
            "_target_from_params": lambda *_args: "pc_a",
            "_registro_iot_runtime": registrar_iot(_IoTExecutavel(lambda *_args: {
                "handled": True,
                "ok": True,
                "status": "ligado",
                "confirmado": True,
                "plano_resposta": {"fala": "Luz ligada."},
            })),
            "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: (
                resultados.append(contrato)
            ),
            "falar_com_lipsync": lambda *args: falas.append(args),
        },
    )

    assert retorno is True
    assert resultados and resultados[0].status == "ligado"
    assert resultados[0].confirmado is True
    assert falas == [("Luz ligada.", "calma", 1)]
