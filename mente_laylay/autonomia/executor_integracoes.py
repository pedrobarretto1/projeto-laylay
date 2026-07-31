"""Adapta integrações operacionais já implementadas fora do roteador central."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos
from mente_laylay.arquivos.contexto_execucao import (
    item_local_existe,
    registrar_arquivo,
    resolver_caminho_local,
    resolver_referencia_arquivo_contextual,
)
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.cognicao.evidencia_operacional import (
    bloqueia_controle_iot_por_modalidade,
)
from mente_laylay.integracao.registro_iot import PortaIoT
from mente_laylay.integracao.registro_arquivos import PortaArquivosLeitura
from mente_laylay.integracao.registro_mutacoes_arquivos import PortaArquivosMutacao


INTENCOES_IOT = frozenset({"IOT_CONTROL", "IOT_STATUS", "IOT_LIST"})
INTENCOES_ARQUIVOS = frozenset({
    "CREATE_FOLDER",
    "CREATE_FILE",
    "DELETE_ITEM",
    "CONFIRM_DELETE_ITEM",
    "CANCEL_DELETE_ITEM",
    "RESTORE_DELETED_ITEM",
    "FILE_TRANSACTION",
    "FILE_SEARCH",
    "FILE_OPEN_RESULT",
})
INTENCOES_INTEGRACOES = frozenset(
    {"SUGGEST_ACTION", "MEDIA_CONTROL"} | INTENCOES_IOT | INTENCOES_ARQUIVOS
)


@dataclass(frozen=True, slots=True)
class DependenciasExecutorIntegracoes:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    contexto_fala: Callable[[], Dict[str, Any]]
    iot: PortaIoT | None = None
    arquivos_leitura: PortaArquivosLeitura | None = None
    arquivos_mutacao: PortaArquivosMutacao | None = None


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _executar_sugestao(
    resultado: dict, texto: str, ctx: Dict[str, Any]
) -> ResultadoDespacho:
    registrar = _get(ctx, "_registrar_sugestao_indireta")
    retorno = bool(registrar(resultado, texto)) if callable(registrar) else False
    return ResultadoDespacho.concluido(retorno)


def _executar_iot(
    resultado: dict,
    texto: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorIntegracoes,
) -> ResultadoDespacho:
    executar = getattr(deps.iot, "executar", None)
    if not callable(executar):
        return ResultadoDespacho.concluido(False)
    retorno = executar(resultado, texto)
    if not isinstance(retorno, dict) or not retorno.get("handled"):
        return ResultadoDespacho.concluido(False)

    deps.marcar_resultado(
        str(retorno.get("status") or "falha_execucao"),
        executou=bool(retorno.get("ok")),
        confirmado=retorno.get("confirmado"),
        detalhe=str(retorno.get("erro") or ""),
    )
    plano = retorno.get("plano_resposta")
    if isinstance(plano, dict):
        if callable(_get(ctx, "enviar_mensagem")):
            contrato = retorno.get("resultado_acao")
            alvo = str(getattr(contrato, "alvo", "") or retorno.get("alvo") or "")
            deps.falar_por_status(
                str(retorno.get("status") or "falha_execucao"),
                str(plano.get("fala") or "Não consegui concluir a ação IoT."),
                alvo=alvo,
                executou=bool(retorno.get("ok")),
                confirmado=retorno.get("confirmado"),
                detalhe=str(retorno.get("erro") or ""),
            )
        else:
            falar = _get(ctx, "falar_com_lipsync")
            if callable(falar):
                falar(
                    str(plano.get("fala") or "Não consegui concluir a ação IoT."),
                    str(plano.get("emocao") or "calma"),
                    int(plano.get("nivel") or 1),
                )
    return ResultadoDespacho.concluido()


def _executar_arquivos(
    intent: str,
    params: Dict[str, Any],
    texto: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorIntegracoes,
) -> ResultadoDespacho:
    retorno = executar_intencao_arquivos(
        intent,
        params,
        destino,
        ctx,
        texto_original=texto,
        marcar_resultado=deps.marcar_resultado,
        registrar_arquivo=lambda alvo, tipo="arquivos": registrar_arquivo(
            ctx, alvo, tipo
        ),
        item_local_existe=lambda valor, tipo="": item_local_existe(
            ctx, valor, tipo, deps.arquivos_mutacao
        ),
        resolver_caminho_local=lambda valor: resolver_caminho_local(
            ctx, valor, deps.arquivos_mutacao
        ),
        resolver_referencia_arquivo_contextual=lambda alvo, tipo="": (
            resolver_referencia_arquivo_contextual(ctx, alvo, tipo)
        ),
        arquivos_leitura=deps.arquivos_leitura,
        arquivos_mutacao=deps.arquivos_mutacao,
    )
    return ResultadoDespacho.concluido(bool(retorno))


def _executar_midia(
    params: Dict[str, Any],
    texto: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorIntegracoes,
) -> ResultadoDespacho:
    retorno = executar_media_control(
        params,
        texto,
        destino,
        ctx,
        marcar_resultado=deps.marcar_resultado,
        falar_por_status=deps.falar_por_status,
        ctx_fala=deps.contexto_fala,
    )
    return ResultadoDespacho.concluido(bool(retorno))


def executar_intencao_integracoes(
    intent: str,
    resultado: dict,
    params: Dict[str, Any],
    texto_original: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorIntegracoes,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_INTEGRACOES:
        return ResultadoDespacho.nao_tratado()
    if intent == "SUGGEST_ACTION":
        return _executar_sugestao(resultado, texto_original, ctx)
    if intent in INTENCOES_IOT:
        # Última barreira antes do dispositivo real. Mesmo que algum caminho
        # externo ou a IA produza IOT_CONTROL por engano, perguntas de
        # capacidade e negações nunca chegam ao runtime físico.
        if intent == "IOT_CONTROL" and bloqueia_controle_iot_por_modalidade(texto_original):
            log = _get(ctx, "print") or _get(ctx, "log")
            if callable(log):
                log("🛡️ [IOT] controle bloqueado pela modalidade da fala original")
            return ResultadoDespacho.concluido(False)
        return _executar_iot(resultado, texto_original, ctx, deps)
    if intent in INTENCOES_ARQUIVOS:
        return _executar_arquivos(
            intent, params, texto_original, destino, ctx, deps
        )
    return _executar_midia(params, texto_original, destino, ctx, deps)
