"""Acoes operacionais de sistema, notificacoes e percepcao visual."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_SISTEMA = frozenset({
    "SCREEN_CAPTURE", "VISION_QUERY", "GAME_VISION", "NOTIFICATIONS", "LOCK_PC",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorSistema:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _capturar_tela(
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorSistema,
) -> ResultadoDespacho:
    executar = _get(ctx, "_executar_captura_tela_intent")
    if not callable(executar):
        deps.marcar_resultado(
            "falha_execucao", executou=False, confirmado=False,
        )
        return ResultadoDespacho.concluido(False)

    acao = str(params.get("acao") or "capturar").strip().casefold()
    modo = str(params.get("modo") or "identificar").strip().casefold()
    try:
        if acao == "consultar_contexto_visual":
            retorno = executar(destino, acao=acao, modo=modo)
        else:
            retorno = executar(destino)
    except TypeError:
        # Compatibilidade com a porta booleana anterior somente para captura;
        # uma consulta nunca pode disparar nova imagem por acidente.
        retorno = executar(destino) if acao != "consultar_contexto_visual" else {}
    except Exception:
        retorno = {}

    aguardar = getattr(retorno, "aguardar", None)
    if callable(aguardar):
        try:
            retorno = aguardar(timeout_s=45.0)
        except TypeError:
            retorno = aguardar(45.0)
        except Exception:
            retorno = {
                "ok": False,
                "status": "falha_analise_visual",
                "confirmado": False,
            }

    if isinstance(retorno, dict):
        dados = dict(retorno)
        ok = bool(dados.get("ok"))
        status = str(
            dados.get("status")
            or ("captura_concluida" if ok else "falha_execucao")
        ).strip()
        confirmado = dados.get("confirmado")
        if confirmado is None:
            confirmado = ok
        deps.marcar_resultado(
            status,
            executou=ok,
            confirmado=bool(confirmado),
            detalhe=str(dados.get("origem") or ""),
        )
        if acao == "consultar_contexto_visual":
            descricao = str(dados.get("descricao") or "").strip()
            if ok and descricao:
                _falar(ctx, descricao)
            else:
                _falar(
                    ctx,
                    "Ainda não tenho uma análise visual recente para consultar.",
                )
        return ResultadoDespacho.concluido(ok)

    # Porta legada: confirma apenas que a solicitação foi aceita. Ela não
    # recebe ``confirmado=True`` porque não carrega o resultado visual final.
    ok = bool(retorno)
    deps.marcar_resultado(
        "captura_solicitada" if ok else "falha_execucao",
        executou=ok,
    )
    return ResultadoDespacho.concluido(ok)


def _visao_jogo(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorSistema,
) -> ResultadoDespacho:
    analise = _get(ctx, "_registro_visao_jogo_analise_runtime")
    executar = getattr(analise, "executar", None)
    ok = bool(executar(params)) if callable(executar) else False
    deps.marcar_resultado("analise_visual_solicitada" if ok else "falha_execucao", executou=ok)
    return ResultadoDespacho.concluido(ok)


def _notificacoes(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorSistema,
) -> ResultadoDespacho:
    falar = _get(ctx, "falar_com_lipsync")
    if not callable(falar):
        return ResultadoDespacho.concluido()
    acao = str(params.get("acao") or "ler").strip().lower()
    alvo = str(params.get("alvo") or params.get("remetente") or params.get("query") or "").strip()
    if acao in {"silenciar_remetente", "silenciar_email", "silenciar_remetente_email"}:
        silenciar = _get(ctx, "_gmail_silenciar_remetente")
        if alvo and callable(silenciar):
            try:
                silenciar(alvo)
            except Exception:
                pass
        deps.marcar_resultado("remetente_silenciado")
        deps.falar_por_status(
            "remetente_silenciado",
            f"Pronto, silenciei {alvo or 'esse remetente'}.",
            alvo=alvo or "esse remetente",
        )
        return ResultadoDespacho.concluido(True)

    central = _get(ctx, "_central_notificacoes_executar")
    if callable(central):
        try:
            retorno = central(params)
        except Exception:
            retorno = {"ok": False, "status": "falha_execucao", "fala": "A central de avisos tropeçou agora. Nada foi perdido; tenta novamente daqui a pouco."}
        if not isinstance(retorno, dict):
            retorno = {}
        ok = bool(retorno.get("ok"))
        status = str(retorno.get("status") or ("notificacoes_lidas" if ok else "falha_execucao"))
        fala_central = str(retorno.get("fala") or "").strip()
        deps.marcar_resultado(status, executou=ok, confirmado=ok)
        if fala_central:
            # A fala precisa usar o mesmo resultado observado pela central.
            # Sem estes campos, o adaptador reconstruía um contrato incerto e
            # dizia que a leitura não fora confirmada apesar do retorno válido.
            deps.falar_por_status(
                status,
                fala_central,
                alvo=alvo or "notificacoes",
                executou=ok,
                confirmado=ok,
            )
        return ResultadoDespacho.concluido(ok)

    if acao in {"silenciar", "mute", "desativar"}:
        deps.marcar_resultado("notificacoes_sem_suporte")
        deps.falar_por_status(
            "notificacoes_sem_suporte",
            "Ainda não tenho a alavanca do silêncio total.",
            alvo="notificacoes",
        )
    elif acao in {"ativar", "reativar"}:
        deps.marcar_resultado("notificacoes_sem_suporte")
        deps.falar_por_status(
            "notificacoes_sem_suporte",
            "Notificações ainda são com o Windows, por enquanto.",
            alvo="notificacoes",
        )
    else:
        deps.marcar_resultado("notificacoes_sem_suporte")
        deps.falar_por_status(
            "notificacoes_sem_suporte",
            "Leitura de notificações ainda depende do Windows.",
            alvo="notificacoes",
        )
    return ResultadoDespacho.concluido()


def _bloquear_pc(
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorSistema,
) -> ResultadoDespacho:
    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    if destino == "pc_b" and callable(enviar_pc_b):
        enviar_pc_b({"action": "lock_pc"})
        deps.marcar_resultado("bloqueio_solicitado", executou=True)
        _falar(ctx, "Enviei o pedido de bloqueio ao PC B, mas ele não confirmou o estado final.")
        return ResultadoDespacho.concluido()
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception:
        deps.marcar_resultado("falha_execucao", executou=False)
        _falar(ctx, escolher_fala_variada([
            "Não consegui travar o Windows agora.",
            "Ainda não deu pra bloquear o Windows.",
            "O bloqueio do Windows não quis colaborar.",
        ]))
        return ResultadoDespacho.concluido()
    deps.marcar_resultado("bloqueio_solicitado", executou=True)
    _falar(ctx, "Solicitei o bloqueio do PC; a chamada foi aceita, mas não consigo reler a tela depois disso.")
    return ResultadoDespacho.concluido()


def executar_intencao_sistema(
    intent: str,
    params: Dict[str, Any],
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorSistema,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_SISTEMA:
        return ResultadoDespacho.nao_tratado()
    if intent in {"SCREEN_CAPTURE", "VISION_QUERY"}:
        return _capturar_tela(params, destino, ctx, deps)
    if intent == "GAME_VISION":
        return _visao_jogo(params, ctx, deps)
    if intent == "NOTIFICATIONS":
        return _notificacoes(params, ctx, deps)
    return _bloquear_pc(destino, ctx, deps)
