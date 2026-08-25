"""Cancelamento de ações e interrupção do contexto musical temporário."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.personalidade.falas_variadas import escolher


INTENCOES_CANCELAMENTO = frozenset({"STOP_PLAYLIST_CONTEXT", "CANCELAR_ACAO"})

_CONTINUIDADES_CANCELADAS = {
    "playlist_sugestao_pendente": None,
    "rotina_sugestao_pendente": None,
    "comando_sugerido": None,
    "comando_sugerido_payload": None,
    "comando_sugerido_estado": "NONE",
    "comando_sugerido_ts": 0.0,
    "comando_pendente": None,
    "comando_pendente_payload": None,
}


@dataclass(frozen=True, slots=True)
class DependenciasExecutorCancelamentos:
    marcar_resultado: Callable[..., Any]


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _falar(ctx: Dict[str, Any], opcoes: list[str]) -> None:
    falar = _get(ctx, "falar_com_lipsync")
    if callable(falar):
        falar(escolher(opcoes), "calma", 1)


def _bloquear_playlist(ctx: Dict[str, Any], duracao: float | None = None) -> None:
    bloquear = _get(ctx, "_bloquear_playlist_temporariamente")
    if not callable(bloquear):
        return
    if duracao is None:
        bloquear()
    else:
        bloquear(duracao)


def _pendencia_canonica(ctx: Dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Lê a fonte oficial e informa se a ausência pôde ser observada."""
    runtime = _get(ctx, "_pendencia_acao_runtime")
    if runtime is None or not callable(getattr(runtime, "obter", None)):
        return {}, False
    try:
        return dict(runtime.obter() or {}), True
    except Exception:
        return {}, False


def _tem_pendencia_legada(ctx: Dict[str, Any]) -> bool:
    """Reconhece ofertas antigas ainda não migradas para a fonte canônica."""
    for chave in (
        "playlist_sugestao_pendente",
        "_playlist_sugestao_pendente",
        "rotina_sugestao_pendente",
        "_rotina_sugestao_pendente",
        "comando_sugerido",
        "comando_sugerido_payload",
        "comando_pendente",
        "comando_pendente_payload",
    ):
        if _get(ctx, chave) not in (None, "", False, {}, []):
            return True

    estado = str(_get(ctx, "comando_sugerido_estado", "") or "").upper().strip()
    return bool(estado and estado not in {"NONE", "CANCELADO", "CANCELLED", "CONCLUIDO"})


def _limpar_continuidades(ctx: Dict[str, Any]) -> bool:
    """Limpa a fonte compartilhada e mantém o retrato local coerente."""
    atualizar = _get(ctx, "update_continuidades")
    definir = _get(ctx, "set_continuidade")
    fonte_atualizada = False

    if callable(atualizar):
        try:
            atualizar(**_CONTINUIDADES_CANCELADAS)
            fonte_atualizada = True
        except Exception:
            fonte_atualizada = False
    elif callable(definir):
        fonte_atualizada = True
        for chave, valor in _CONTINUIDADES_CANCELADAS.items():
            try:
                definir(chave, valor)
            except Exception:
                fonte_atualizada = False

    # Compatibilidade com contextos antigos e com testes que usam um retrato
    # mutável sem fornecer acesso à memória compartilhada.
    retrato_atualizado = False
    try:
        ctx.update(_CONTINUIDADES_CANCELADAS)
        ctx["_playlist_sugestao_pendente"] = None
        ctx["_rotina_sugestao_pendente"] = None
        retrato_atualizado = True
    except Exception:
        retrato_atualizado = False
    return fonte_atualizada if callable(atualizar) or callable(definir) else retrato_atualizado


def executar_intencao_cancelamentos(
    intent: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorCancelamentos,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_CANCELAMENTO:
        return ResultadoDespacho.nao_tratado()

    if intent == "STOP_PLAYLIST_CONTEXT":
        _bloquear_playlist(ctx)
        deps.marcar_resultado("playlist_contexto_bloqueado")
        _falar(ctx, [
            "Fechado, sem playlist agora. Guardei a caixinha de som.",
            "Tá, corto playlist por enquanto. Ela fica quietinha no canto.",
            "Entendi. Nada de playlist agora, pode falar comigo normal.",
        ])
        return ResultadoDespacho.concluido()

    pendencia, fonte_canonica_observada = _pendencia_canonica(ctx)
    pendencia_legada = _tem_pendencia_legada(ctx)
    if not pendencia and not pendencia_legada:
        if fonte_canonica_observada:
            _falar(ctx, [
                "Não havia nenhuma ação pendente para cancelar.",
                "Não encontrei nenhuma ação pendente; não cancelei nada.",
                "Não havia nenhuma ação pendente; mantive tudo como estava.",
            ])
            deps.marcar_resultado("sem_pendencia", executou=False, confirmado=True)
        else:
            _falar(ctx, [
                "Não consegui conferir se havia uma ação pendente; não vou dizer que cancelei.",
                "A fonte de pendências não respondeu, então não alterei nada.",
            ])
            deps.marcar_resultado("sem_confirmacao", executou=False, confirmado=False)
        return ResultadoDespacho.concluido()

    _bloquear_playlist(ctx, 0.0)
    legado_limpo = _limpar_continuidades(ctx)
    canonica_concluida = True
    if pendencia:
        runtime = _get(ctx, "_pendencia_acao_runtime")
        try:
            canonica_concluida = bool(
                runtime.concluir(str(pendencia.get("id") or ""), "cancelada")
            )
        except Exception:
            canonica_concluida = False

    confirmado = canonica_concluida and (legado_limpo or not pendencia_legada)
    if confirmado:
        _falar(ctx, [
            "Beleza, cancelei isso.",
            "Certo, deixei pra lá.",
            "Tá, descartei a ação anterior.",
        ])
        deps.marcar_resultado("cancelado", executou=True, confirmado=True)
    else:
        _falar(ctx, [
            "Não consegui confirmar o cancelamento; não vou fingir que deu certo.",
            "A ação pendente não confirmou o cancelamento.",
        ])
        deps.marcar_resultado("falha_execucao", executou=False, confirmado=False)
    return ResultadoDespacho.concluido()
