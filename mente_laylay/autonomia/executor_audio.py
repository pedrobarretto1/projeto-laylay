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
) -> ResultadoDespacho:
    status = status_ok if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    deps.falar_por_status(status, fala_ok if ok else fala_falha, alvo=alvo)
    return ResultadoDespacho.concluido()


def _executar_volume(
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorAudio,
) -> ResultadoDespacho:
    acao = str(params.get("acao") or params.get("modo") or "").strip().lower()
    nivel = params.get("nivel_volume") if "nivel_volume" in params else params.get("value")
    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    ajustar_volume = _get(ctx, "ajustar_volume_sistema")
    ajustar_relativo = _get(ctx, "ajustar_volume_sistema_relativo")
    definir_mudo = _get(ctx, "definir_mudo_sistema")

    if acao in {"up", "aumentar", "aumenta"}:
        ok = False
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "volume_up", "delta": 10})
            ok = True
        elif callable(ajustar_relativo):
            ajustar_relativo(10)
            ok = True
        return _registrar_e_falar(
            ok,
            "volume_aumentado",
            "Aumentei o volume.",
            "Tentei aumentar o volume, mas o controle não respondeu.",
            deps,
        )

    if acao in {"down", "baixar", "baixa"}:
        ok = False
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "volume_down", "delta": 10})
            ok = True
        elif callable(ajustar_relativo):
            ajustar_relativo(-10)
            ok = True
        return _registrar_e_falar(
            ok,
            "volume_baixado",
            "Baixei o volume.",
            "Tentei baixar o volume, mas o controle não respondeu.",
            deps,
        )

    if acao in {"mute", "mudo"}:
        ok = False
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "set_volume", "nivel": 0})
            ok = True
        elif callable(definir_mudo):
            ok = bool(definir_mudo(True))
        return _registrar_e_falar(
            ok,
            "volume_mudo",
            "Mudo ligado.",
            "Tentei mutar o som, mas o controle não respondeu.",
            deps,
        )

    if acao in {"unmute", "desmudo", "desmutar"}:
        ok = False
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "volume_unmute"})
            ok = True
        elif callable(definir_mudo):
            ok = bool(definir_mudo(False))
        return _registrar_e_falar(
            ok,
            "volume_desmutado",
            "Som de volta.",
            "Tentei tirar do mudo, mas o controle não confirmou.",
            deps,
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
            ok = False
            if destino == "pc_b" and callable(enviar_pc_b):
                enviar_pc_b({"action": "set_volume", "nivel": nivel_inteiro})
                ok = True
            elif callable(ajustar_volume):
                ajustar_volume(nivel_inteiro)
                ok = True
            return _registrar_e_falar(
                ok,
                "volume_ajustado",
                f"Deixei o volume em {nivel_inteiro}%.",
                "Tentei ajustar o volume, mas o controle não respondeu.",
                deps,
                alvo=f"volume em {nivel_inteiro}%",
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
