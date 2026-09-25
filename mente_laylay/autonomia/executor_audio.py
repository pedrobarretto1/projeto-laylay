"""Orquestracao das intencoes de audio da Laylay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_AUDIO = frozenset({"VOLUME"})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorAudio:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _registrar_e_falar(
    ok: bool,
    status_ok: str,
    fala_ok: str,
    fala_falha: str,
    deps: DependenciasExecutorAudio,
    *,
    alvo: str = "volume",
    executou: bool | None = None,
    confirmado: bool | None = None,
    detalhe: str = "",
    contexto_resultado: Dict[str, Any] | None = None,
    evidencia_confirmacao: str = "",
) -> ResultadoDespacho:
    executou_final = bool(ok) if executou is None else bool(executou)
    status = status_ok if ok else "falha_execucao"
    resultado_kwargs: Dict[str, Any] = {"executou": executou_final}
    if confirmado is not None:
        resultado_kwargs["confirmado"] = bool(confirmado)
    if detalhe:
        resultado_kwargs["detalhe"] = detalhe
    if contexto_resultado:
        resultado_kwargs["contexto_resultado"] = dict(contexto_resultado)
    if evidencia_confirmacao:
        resultado_kwargs["evidencia_confirmacao"] = evidencia_confirmacao
    deps.marcar_resultado(status, **resultado_kwargs)

    fala_kwargs: Dict[str, Any] = {"alvo": alvo}
    if confirmado is not None or detalhe or contexto_resultado:
        fala_kwargs["executou"] = executou_final
        if confirmado is not None:
            fala_kwargs["confirmado"] = bool(confirmado)
        if detalhe:
            fala_kwargs["detalhe"] = detalhe
    deps.falar_por_status(
        status,
        fala_ok if ok else fala_falha,
        **fala_kwargs,
    )
    return ResultadoDespacho.concluido()


def _enviar_volume_remoto(
    payload: Dict[str, Any],
    ctx: Dict[str, Any],
) -> Dict[str, Any]:
    """Preserva o receipt do PC B sem quebrar a porta booleana legada."""
    enviar = _get(ctx, "_enviar_pc_b")
    enviar_detalhado = _get(ctx, "_enviar_pc_b_detalhado")
    if not callable(enviar_detalhado) and callable(enviar):
        runtime = getattr(enviar, "__self__", None)
        enviar_detalhado = getattr(runtime, "enviar_detalhado", None)

    if callable(enviar_detalhado):
        try:
            retorno = enviar_detalhado(dict(payload))
        except Exception as erro:
            retorno = {
                "status": "error",
                "executed": False,
                "confirmed": False,
                "error": f"{type(erro).__name__}: {erro}",
            }
        if isinstance(retorno, dict):
            dados = dict(retorno)
            executou = dados.get("executed")
            confirmado = dados.get("confirmed")
            return {
                "executou": None if executou is None else bool(executou),
                "confirmado": (
                    None if confirmado is None else bool(confirmado)
                ),
                "erro": str(dados.get("error") or ""),
                "volume_observado": dados.get("volume"),
                "request_id": str(dados.get("requestId") or ""),
                "fonte_evidencia": "pc_b_status",
            }

    if callable(enviar):
        try:
            enviado = bool(enviar(dict(payload)))
        except Exception:
            enviado = False
        return {
            "executou": enviado,
            "confirmado": None if enviado else False,
            "erro": "" if enviado else "O PC B não confirmou a solicitação.",
            "volume_observado": None,
            "request_id": "",
            "fonte_evidencia": "",
        }

    return {
        "executou": False,
        "confirmado": False,
        "erro": "Canal do PC B indisponível.",
        "volume_observado": None,
        "request_id": "",
        "fonte_evidencia": "pc_b_status",
    }


def _registrar_volume_remoto(
    payload: Dict[str, Any],
    status_ok: str,
    fala_ok: str,
    fala_falha: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorAudio,
    *,
    alvo: str = "volume",
) -> ResultadoDespacho:
    receipt = _enviar_volume_remoto(payload, ctx)
    executou = receipt.get("executou")
    confirmado = receipt.get("confirmado")
    ok = executou is True and confirmado is not False
    contexto_resultado: Dict[str, Any] = {}
    fonte_evidencia = str(receipt.get("fonte_evidencia") or "")
    if fonte_evidencia:
        contexto_resultado["fonte_evidencia"] = fonte_evidencia
    request_id = str(receipt.get("request_id") or "")
    if request_id:
        contexto_resultado["request_id_remoto"] = request_id
    volume_observado = receipt.get("volume_observado")
    if volume_observado is not None:
        contexto_resultado["volume_observado"] = volume_observado
    evidencia = ""
    if confirmado is True:
        evidencia = "pc_b_status confirmou o estado observado no Windows remoto"
    return _registrar_e_falar(
        ok,
        status_ok,
        fala_ok,
        fala_falha,
        deps,
        alvo=alvo,
        executou=executou,
        confirmado=confirmado,
        detalhe=str(receipt.get("erro") or ""),
        contexto_resultado=contexto_resultado,
        evidencia_confirmacao=evidencia,
    )


def _ler_volume_local(ctx: Dict[str, Any]) -> int | None:
    obter_volume = _get(ctx, "obter_volume_sistema")
    if not callable(obter_volume):
        return None
    try:
        observado = obter_volume()
    except Exception:
        return None
    if observado is None:
        return None
    try:
        return max(0, min(100, int(round(float(observado)))))
    except (TypeError, ValueError):
        return None


def _registrar_volume_local(
    *,
    executou: bool,
    esperado: int | None,
    status_ok: str,
    fala_ok: str,
    fala_falha: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorAudio,
    alvo: str = "volume",
) -> ResultadoDespacho:
    """Relê o volume mestre quando a API perceptiva está disponível."""
    confirmado: bool | None = False if not executou else None
    detalhe = ""
    contexto_resultado: Dict[str, Any] = {}
    evidencia = ""
    if executou and callable(_get(ctx, "obter_volume_sistema")):
        observado_int = _ler_volume_local(ctx)
        if observado_int is not None:
            contexto_resultado = {
                "fonte_evidencia": "api_audio_windows",
                "volume_observado": observado_int,
            }
            if esperado is not None:
                confirmado = abs(observado_int - int(esperado)) <= 2
                if confirmado:
                    evidencia = (
                        "API de áudio do Windows releu o volume mestre "
                        f"em {observado_int}%"
                    )
                else:
                    detalhe = (
                        f"Volume observado em {observado_int}%, "
                        f"esperado {int(esperado)}%."
                    )
        else:
            detalhe = "A execução ocorreu, mas a releitura do volume falhou."

    ok = executou and confirmado is not False
    return _registrar_e_falar(
        ok,
        status_ok,
        fala_ok,
        fala_falha,
        deps,
        alvo=alvo,
        executou=executou,
        confirmado=confirmado,
        detalhe=detalhe,
        contexto_resultado=contexto_resultado,
        evidencia_confirmacao=evidencia,
    )


def _executar_volume(
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorAudio,
) -> ResultadoDespacho:
    acao = str(params.get("acao") or params.get("modo") or "").strip().lower()
    nivel = params.get("nivel_volume") if "nivel_volume" in params else params.get("value")
    ajustar_volume = _get(ctx, "ajustar_volume_sistema")
    ajustar_relativo = _get(ctx, "ajustar_volume_sistema_relativo")
    definir_mudo = _get(ctx, "definir_mudo_sistema")

    if acao in {"up", "aumentar", "aumenta"}:
        if destino == "pc_b":
            return _registrar_volume_remoto(
                {"action": "volume_up", "delta": 10},
                "volume_aumentado",
                "Aumentei o volume.",
                "Tentei aumentar o volume, mas o controle não respondeu.",
                ctx,
                deps,
            )
        antes = _ler_volume_local(ctx)
        executou = False
        if callable(ajustar_relativo):
            try:
                ajustar_relativo(10)
                executou = True
            except Exception:
                executou = False
        esperado = min(100, antes + 10) if antes is not None else None
        return _registrar_volume_local(
            executou=executou,
            esperado=esperado,
            status_ok="volume_aumentado",
            fala_ok="Aumentei o volume.",
            fala_falha="Tentei aumentar o volume, mas o controle não respondeu.",
            ctx=ctx,
            deps=deps,
        )

    if acao in {"down", "baixar", "baixa"}:
        if destino == "pc_b":
            return _registrar_volume_remoto(
                {"action": "volume_down", "delta": 10},
                "volume_baixado",
                "Baixei o volume.",
                "Tentei baixar o volume, mas o controle não respondeu.",
                ctx,
                deps,
            )
        antes = _ler_volume_local(ctx)
        executou = False
        if callable(ajustar_relativo):
            try:
                ajustar_relativo(-10)
                executou = True
            except Exception:
                executou = False
        esperado = max(0, antes - 10) if antes is not None else None
        return _registrar_volume_local(
            executou=executou,
            esperado=esperado,
            status_ok="volume_baixado",
            fala_ok="Baixei o volume.",
            fala_falha="Tentei baixar o volume, mas o controle não respondeu.",
            ctx=ctx,
            deps=deps,
        )

    if acao in {"mute", "mudo"}:
        if destino == "pc_b":
            return _registrar_volume_remoto(
                {"action": "set_volume", "nivel": 0},
                "volume_mudo",
                "Mudo ligado.",
                "Tentei mutar o som, mas o controle não respondeu.",
                ctx,
                deps,
            )
        ok = False
        if callable(definir_mudo):
            ok = bool(definir_mudo(True))
        return _registrar_e_falar(
            ok,
            "volume_mudo",
            "Mudo ligado.",
            "Tentei mutar o som, mas o controle não respondeu.",
            deps,
            executou=ok,
            confirmado=ok,
            contexto_resultado=(
                {"fonte_evidencia": "api_audio_windows"} if ok else None
            ),
            evidencia_confirmacao=(
                "API de áudio do Windows releu o estado de mudo"
                if ok else ""
            ),
        )

    if acao in {"unmute", "desmudo", "desmutar"}:
        if destino == "pc_b":
            return _registrar_volume_remoto(
                {"action": "volume_unmute"},
                "volume_desmutado",
                "Som de volta.",
                "Tentei tirar do mudo, mas o controle não confirmou.",
                ctx,
                deps,
            )
        ok = False
        if callable(definir_mudo):
            ok = bool(definir_mudo(False))
        return _registrar_e_falar(
            ok,
            "volume_desmutado",
            "Som de volta.",
            "Tentei tirar do mudo, mas o controle não confirmou.",
            deps,
            executou=ok,
            confirmado=ok,
            contexto_resultado=(
                {"fonte_evidencia": "api_audio_windows"} if ok else None
            ),
            evidencia_confirmacao=(
                "API de áudio do Windows releu o estado de mudo"
                if ok else ""
            ),
        )

    if isinstance(nivel, (int, float, str)):
        try:
            valor = float(nivel)
        except Exception:
            valor = -1.0
        if 0.0 <= valor <= 1.0:
            valor *= 100.0
        if 0.0 <= valor <= 100.0:
            nivel_inteiro = int(valor)
            if destino == "pc_b":
                return _registrar_volume_remoto(
                    {"action": "set_volume", "nivel": nivel_inteiro},
                    "volume_ajustado",
                    f"Deixei o volume em {nivel_inteiro}%.",
                    "Tentei ajustar o volume, mas o controle não respondeu.",
                    ctx,
                    deps,
                    alvo=f"volume em {nivel_inteiro}%",
                )
            executou = False
            if callable(ajustar_volume):
                try:
                    retorno_ajuste = ajustar_volume(nivel_inteiro)
                    executou = (
                        bool(retorno_ajuste)
                        if isinstance(retorno_ajuste, bool)
                        else True
                    )
                except Exception:
                    executou = False
            return _registrar_volume_local(
                executou=executou,
                esperado=nivel_inteiro,
                status_ok="volume_ajustado",
                fala_ok=f"Deixei o volume em {nivel_inteiro}%.",
                fala_falha=(
                    "Tentei ajustar o volume, mas o controle não respondeu."
                ),
                ctx=ctx,
                deps=deps,
                alvo=f"volume em {nivel_inteiro}%",
            )

    deps.marcar_resultado(
        "acao_invalida",
        executou=False,
        confirmado=False,
    )
    _falar(ctx, escolher_fala_variada([
        "Volume como? No talo, baixinho, mudo...",
        "Como você quer o volume?",
        "Me diz o nível do som.",
    ]), "debochada", 2)
    return ResultadoDespacho.concluido()


def executar_intencao_audio(
    intent: str,
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorAudio,
) -> ResultadoDespacho:
    """Executa uma intencao de audio ou nao interfere em outros dominios."""

    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_AUDIO:
        return ResultadoDespacho.nao_tratado()
    return _executar_volume(params, destino, ctx, deps)
