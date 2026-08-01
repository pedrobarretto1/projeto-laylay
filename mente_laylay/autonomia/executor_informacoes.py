"""Consultas informativas de e-mail, clima e briefing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_INFORMACOES = frozenset({
    "EMAIL_READ", "EMAIL_SYNC", "BRIEFING_REPEAT", "WEATHER", "LEARNING_QUERY",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorInformacoes:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    registrar_mente: Callable[..., Any]


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _ler_emails(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    configurado = _get(ctx, "_gmail_configurado")
    if callable(configurado) and not configurado():
        _falar(
            ctx,
            "Meu acesso ao Gmail não está configurado neste PC. Configure as variáveis do email e me reinicie para eu voltar a acompanhar a caixa.",
        )
        deps.marcar_resultado("falha_execucao", executou=False)
        return ResultadoDespacho.concluido()
    somente = bool(params.get("urgentes") or params.get("prioritarios"))
    remetente = str(
        params.get("remetente") or params.get("alvo") or params.get("query") or ""
    ).strip().lower()
    buscar = _get(ctx, "_gmail_buscar_nao_lidos")
    emails = _get(ctx, "_gmail_nao_lidos_cache", []) or (buscar() if callable(buscar) else [])
    if somente:
        emails = [email for email in emails if email.get("prioritario")]
    if remetente:
        filtrados = []
        for email in emails if isinstance(emails, list) else []:
            origem = str((email or {}).get("remetente") or "").strip().lower()
            if origem and (remetente == origem or remetente in origem or origem in remetente):
                filtrados.append(email)
        emails = filtrados or emails

    resumir = _get(ctx, "_gmail_falar_resumo_estiloso")
    fala = ""
    if callable(resumir):
        try:
            fala = str(resumir(
                emails,
                somente_prioritarios=somente,
                emitir_proativa=False,
            ) or "").strip()
        except TypeError:
            fala = str(resumir(emails, somente_prioritarios=somente) or "").strip()
    if fala:
        _falar(ctx, fala)
    deps.marcar_resultado("emails_lidos")
    return ResultadoDespacho.concluido()


def _sincronizar_emails(
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    configurado = _get(ctx, "_gmail_configurado")
    if callable(configurado) and not configurado():
        deps.marcar_resultado("falha_execucao", executou=False)
        _falar(
            ctx,
            "Ainda não tenho acesso configurado ao Gmail neste PC. Depois de configurar as variáveis, preciso ser reiniciada.",
        )
        return ResultadoDespacho.concluido()
    buscar = _get(ctx, "_gmail_buscar_nao_lidos")
    ok = False
    if callable(buscar):
        try:
            ok = isinstance(buscar(), list)
        except Exception:
            ok = False
    status = "emails_sincronizados" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    deps.falar_por_status(
        status,
        "Atualizando a caixa de entrada."
        if ok else "Tentei atualizar teus emails, mas a caixa não respondeu direito.",
        alvo="emails",
    )
    return ResultadoDespacho.concluido()


def _repetir_briefing(
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    repetir = _get(ctx, "repetir_briefing")
    fala = ""
    if callable(repetir):
        retorno = repetir()
        if isinstance(retorno, str):
            fala = retorno.strip()
    if fala:
        deps.registrar_mente(
            texto_original,
            fala,
            "BRIEFING_REPEAT",
            "briefing do clima",
            "conversa",
            "briefing",
        )
    deps.marcar_resultado("briefing_repetido")
    return ResultadoDespacho.concluido()


def _consultar_clima(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    local = str(
        params.get("local") or params.get("cidade") or params.get("bairro")
        or params.get("query") or _get(ctx, "cidade_padrao_clima", "Boituva")
    ).strip()
    obter = _get(ctx, "obter_clima_localidade")
    info = obter(local) if callable(obter) else {"ok": False, "localidade": local}
    if not info.get("ok"):
        _falar(ctx, escolher_fala_variada([
            f"Tentei sentir o clima de {local}, mas minha antena do tempo falhou agora.",
            f"Fui olhar o tempo em {local}, mas não consegui puxar essa informação agora.",
            f"O clima de {local} escapou de mim por enquanto. Se quiser, tenta de novo em instantes.",
        ]))
        return ResultadoDespacho.concluido()

    cidade = str(info.get("localidade") or local).strip()
    cidade_fala = cidade.title() if cidade.islower() else cidade
    temperatura = str(info.get("temperatura_c") or "").strip()
    sensacao = str(info.get("sensacao_c") or "").strip()
    descricao = str(info.get("descricao") or "").strip()
    umidade = str(info.get("umidade") or "").strip()
    base = f"Agora em {cidade_fala} está {temperatura} graus"
    if descricao:
        base += f", e o tempo está {descricao.casefold()}"
    if sensacao:
        base += f". Sensação de {sensacao} graus"
    if umidade:
        base += f" e umidade em {umidade}%"
    base += "."
    _falar(ctx, escolher_fala_variada([
        base,
        f"Dei uma espiada no tempo: {base}",
        f"Clima na mesa. {base}",
    ]))
    deps.marcar_resultado("clima_consultado")
    return ResultadoDespacho.concluido()


def _consultar_aprendizados(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    recuperar = _get(ctx, "_recuperar_aprendizados")
    try:
        limite = max(1, min(5, int(params.get("limit") or 3)))
    except (TypeError, ValueError):
        limite = 3
    if not callable(recuperar):
        deps.marcar_resultado("habilidade_indisponivel", executou=False)
        _falar(ctx, "Minha memória de aprendizados não está disponível agora.")
        return ResultadoDespacho.concluido(False)
    try:
        aprendizados = [
            str(item).strip() for item in (recuperar(limit=limite) or [])
            if str(item or "").strip()
        ]
    except Exception:
        deps.marcar_resultado("falha_execucao", executou=False)
        _falar(ctx, "Tentei puxar o que aprendi, mas minha memória não respondeu direito.")
        return ResultadoDespacho.concluido(False)

    deps.marcar_resultado("aprendizados_consultados", executou=True, confirmado=True)
    if not aprendizados:
        _falar(ctx, "Ainda não tenho nenhum aprendizado confiável seu guardado por aqui.")
        return ResultadoDespacho.concluido(True)
    recortes = [item if len(item) <= 140 else item[:137] + "..." for item in aprendizados]
    if len(recortes) == 1:
        fala = f"Lembro disso que você me ensinou: {recortes[0]}"
    else:
        fala = "Lembro destas coisas que você me ensinou: " + "; ".join(recortes) + "."
    _falar(ctx, fala)
    return ResultadoDespacho.concluido(True)


def executar_intencao_informacoes(
    intent: str,
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorInformacoes,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_INFORMACOES:
        return ResultadoDespacho.nao_tratado()
    if intent == "EMAIL_READ":
        return _ler_emails(params, ctx, deps)
    if intent == "EMAIL_SYNC":
        return _sincronizar_emails(ctx, deps)
    if intent == "BRIEFING_REPEAT":
        return _repetir_briefing(texto_original, ctx, deps)
    if intent == "LEARNING_QUERY":
        return _consultar_aprendizados(params, ctx, deps)
    return _consultar_clima(params, ctx, deps)
