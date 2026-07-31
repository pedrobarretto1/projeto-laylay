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


def _limpar_continuidades(ctx: Dict[str, Any]) -> None:
    """Limpa a fonte compartilhada e mantém o retrato local coerente."""
    atualizar = _get(ctx, "update_continuidades")
    definir = _get(ctx, "set_continuidade")

    if callable(atualizar):
        try:
            atualizar(**_CONTINUIDADES_CANCELADAS)
        except Exception:
            pass
    elif callable(definir):
        for chave, valor in _CONTINUIDADES_CANCELADAS.items():
            try:
                definir(chave, valor)
            except Exception:
                continue

    # Compatibilidade com contextos antigos e com testes que usam um retrato
    # mutável sem fornecer acesso à memória compartilhada.
    try:
        ctx.update(_CONTINUIDADES_CANCELADAS)
        ctx["_playlist_sugestao_pendente"] = None
        ctx["_rotina_sugestao_pendente"] = None
    except Exception:
        pass


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

    _bloquear_playlist(ctx, 0.0)
    _limpar_continuidades(ctx)
    _falar(ctx, [
        "Beleza, cancelei isso.",
        "Certo, deixei pra lá.",
        "Tá, descartei a ação anterior.",
    ])
    deps.marcar_resultado("cancelado")
    return ResultadoDespacho.concluido()
