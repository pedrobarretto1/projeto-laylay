"""Orquestracao das intencoes de navegador e pesquisa web."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import (
    falar_ctx as _falar,
    relatar_falha_ctx,
)
from mente_laylay.cognicao.refinamento_pesquisa import refinar_consulta_web
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_NAVEGADOR = frozenset({
    "OPEN_URL",
    "CLOSE_IDLE_TABS",
    "CLOSE_TAB",
    "SITE_ENTER",
    "SEARCH",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorNavegador:
    """Callbacks do roteador necessarios ao dominio web."""

    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    abrir_url_com_validacao: Callable[..., bool]
    alvo_preciso_para_aba: Callable[[str], str]
    esperar_aba_fechar: Callable[..., bool]
    esperar_programa_fechar: Callable[[str], bool]
    executar_recursivo: Callable[[dict, str, Dict[str, Any]], bool]


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _url_http_absoluta(valor: Any) -> str:
    """Retorna uma URL web completa sem submetê-la à normalização de linguagem."""
    texto = str(valor or "").strip()
    if not texto:
        return ""
    try:
        partes = urllib.parse.urlsplit(texto)
    except (TypeError, ValueError):
        return ""
    if partes.scheme.casefold() not in {"http", "https"} or not partes.netloc:
        return ""
    return texto


def _executar_open_url(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    alvo = str(params.get("url") or params.get("alvo") or params.get("site") or params.get("query") or "").strip()
    url_absoluta = _url_http_absoluta(alvo)
    if url_absoluta:
        # Query strings, fragmentos e caracteres escapados fazem parte do endereço.
        # Normalizadores linguísticos são usados somente para apelidos como "youtube".
        url = url_absoluta
    else:
        contexto_site = _get(ctx, "_contexto_aponta_site_web")
        normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
        montar_url = _get(ctx, "_montar_url_site_ou_busca")
        if callable(contexto_site) and contexto_site(alvo):
            alvo = normalizar(alvo) if callable(normalizar) else alvo
        url = montar_url(alvo) if callable(montar_url) else alvo
    if not url:
        _falar(ctx, escolher_fala_variada([
            "Abrir o quê? Me dá um site ou assunto.",
            "Me diz o que você quer abrir.",
            "Faltou o site ou o assunto.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()
    ok = deps.abrir_url_com_validacao(url, alvo=alvo or url, auto_click=False)
    status = "url_aberta" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    deps.falar_por_status(
        status,
        f"Abrindo {alvo or url}." if ok else f"Tentei abrir {alvo or url}, mas não consegui confirmar a rota.",
        alvo=alvo or url,
    )
    return ResultadoDespacho.concluido()


def _executar_fechar_abas_paradas(
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    fechar = _get(ctx, "_executar_fechar_abas_paradas")
    ok = bool(fechar()) if callable(fechar) else False
    deps.marcar_resultado(
        "fechamento_abas_solicitado" if ok else "falha_execucao",
        executou=ok,
    )
    return ResultadoDespacho.concluido(ok)


def _executar_fechar_aba(
    params: Dict[str, Any],
    texto_original: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    navegador_leitura = _get(ctx, "_registro_navegador_leitura_runtime")
    navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    resolver_alvo = _get(ctx, "_resolver_alvo_ambiente")
    eh_site = _get(ctx, "_eh_alvo_site_web")
    contexto_site = _get(ctx, "_contexto_aponta_site_web")
    fechar_programa = _get(ctx, "fechar_programa")
    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    apps_map = _get(ctx, "APPS_MAP", {}) or {}

    info = navegador_leitura.aba_ativa() if navegador_leitura is not None else {}
    alvo = str(params.get("alvo") or params.get("site") or params.get("nome") or "").strip()
    alvo_preciso = deps.alvo_preciso_para_aba(alvo) if alvo else ""
    leitura = resolver_alvo(alvo) if alvo and callable(resolver_alvo) else {}
    alvo_web = bool(callable(eh_site) and eh_site(alvo))
    if alvo and not alvo_web and bool((leitura or {}).get("programa_aberto")) and callable(fechar_programa):
        mapped = apps_map.get(alvo.lower(), alvo)
        try:
            fechar_programa(mapped)
        except Exception as erro:
            relatar_falha_ctx(
                ctx,
                "executor_navegador",
                "falha_fechar_programa",
                erro=erro,
                impacto="comando",
                fallback="confirmar_estado_janela",
                dominio="navegador",
                fase="fechar_aba",
            )
        ok = deps.esperar_programa_fechar(alvo)
        status = "app_fechado_em_vez_de_aba" if ok else "falha_execucao"
        deps.marcar_resultado(status, executou=ok)
        deps.falar_por_status(
            status,
            f"{alvo} estava aberto como programa. Fechei ele, não a aba."
            if ok else f"Tentei fechar {alvo} como programa, mas ele resistiu.",
            alvo=alvo,
        )
        return ResultadoDespacho.concluido()

    if not alvo and callable(contexto_site) and contexto_site(texto_original):
        alvo = str(params.get("nome_app") or params.get("query") or params.get("alvo") or "site").strip()

    ok = False
    if destino == "pc_b" and callable(enviar_pc_b):
        payload = (
            {"action": "close_specific_tab", "target": alvo_preciso or alvo}
            if alvo else {"action": "close_current_tab"}
        )
        enviar_pc_b(payload)
        ok = True
    elif alvo and navegador_operacoes is not None:
        enviado = bool(navegador_operacoes.fechar_aba(alvo_preciso or alvo))
        if enviado:
            ok = deps.esperar_aba_fechar(alvo_preciso or alvo, info)
        else:
            ok = bool(navegador_operacoes.fechar_aba_nativa(alvo_preciso or alvo))
    elif navegador_operacoes is not None:
        enviado = bool(navegador_operacoes.fechar_aba_atual())
        if enviado:
            ok = deps.esperar_aba_fechar("", info)
        else:
            ok = bool(navegador_operacoes.fechar_aba_nativa(""))

    status = "aba_fechada" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    deps.falar_por_status(
        status,
        "Fechado. Já vai tarde."
        if ok else f"Tentei fechar {alvo or 'essa aba'}, mas não consegui confirmar se ela saiu de cena.",
        alvo=alvo or "essa aba",
    )
    return ResultadoDespacho.concluido()


def _executar_entrar_site(
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    tema = str(
        params.get("tema") or params.get("topic") or params.get("assunto")
        or params.get("query") or ""
    ).strip() or str(texto_original or "").strip()
    if not tema:
        _falar(ctx, escolher_fala_variada([
            "Entrar onde? Fala o tema do site.",
            "Qual site você quer?",
            "Me fala o assunto do site.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()
    url = f"https://www.google.com/search?q={urllib.parse.quote(tema)}&laylay_auto=true"
    ok = deps.abrir_url_com_validacao(url, alvo=tema, auto_click=True)
    status = "busca_site_iniciada" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    deps.falar_por_status(
        status,
        f"Vou entrar no melhor site de {tema}."
        if ok else f"Tentei abrir uma busca de {tema}, mas a rota web falhou.",
        alvo=tema,
    )
    return ResultadoDespacho.concluido()


def _executar_search(
    params: Dict[str, Any],
    texto_original: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    texto_lower = str(texto_original or "").lower()
    clima_like = any(trecho in texto_lower for trecho in (
        "quantos graus", "temperatura", "clima", "como está o tempo",
        "como esta o tempo", "vai chover", "tempo em",
    ))
    if clima_like:
        local = str(
            params.get("local") or params.get("cidade") or params.get("query") or texto_original
        ).strip()
        retorno = deps.executar_recursivo(
            {"intent": "WEATHER", "params": {"local": local}}, texto_original, ctx
        )
        return ResultadoDespacho.concluido(retorno)

    falar = _get(ctx, "falar_com_lipsync")
    registrar = _get(ctx, "_registrar_mente_curta")
    if "playlist" in texto_lower:
        extrair_playlist = _get(ctx, "extrair_nome_playlist")
        pl = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
        if not pl and callable(extrair_playlist):
            try:
                pl = str(extrair_playlist(texto_original) or "").strip()
            except Exception as erro:
                relatar_falha_ctx(
                    ctx,
                    "executor_navegador",
                    "falha_extrair_playlist",
                    erro=erro,
                    classe="degradacao",
                    impacto="servico",
                    fallback="playlist_recente",
                    dominio="navegador",
                    fase="abrir_playlist",
                )
                pl = ""
        if not pl:
            pl = str(_get(ctx, "ultima_playlist", "") or "").strip()
        if pl:
            retorno = deps.executar_recursivo(
                {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}},
                texto_original,
                ctx,
            )
            return ResultadoDespacho.concluido(retorno)
        _falar(ctx, escolher_fala_variada([
            "Isso é playlist. Eu leio arquivo local, não o Google. Me diz qual playlist.",
            "Me diz qual playlist você quer ver.",
            "Playlist é comigo, mas preciso do nome certo.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()

    query = str(params.get("query") or params.get("termo") or params.get("q") or texto_original).strip()
    perfil_pesquisa = refinar_consulta_web(query, texto_original, params)
    query_refinada = str(perfil_pesquisa.get("query") or query).strip()
    if query_refinada and query_refinada != query:
        print(f"🧭 [PESQUISA:WEB] consulta refinada={query_refinada!r}")
        query = query_refinada
    texto_limpo = str(texto_original or "").strip().lower()
    permitir_google = (
        "pesquisa" in texto_limpo
        or texto_limpo.startswith("o que é")
        or texto_limpo.startswith("o que eh")
    )
    engine = str(
        params.get("engine") or params.get("site") or ("google" if permitir_google else "")
    ).strip().lower()
    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    if engine == "youtube":
        if destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({
                "action": "open_url",
                "url": "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query),
            })
        elif navegador_operacoes is not None:
            navegador_operacoes.pesquisar_youtube(query)
        fala = escolher_fala_variada([
            f"Sintonizando o melhor do {query} no YouTube agora.",
            f"Botando {query} pra tocar agora.",
            f"Já achei {query}.",
        ])
        _falar(ctx, fala)
        if callable(registrar):
            registrar(texto_original, fala, "SEARCH", query, "", "pesquisa")
        return ResultadoDespacho.concluido()

    if not permitir_google:
        messages = _get(ctx, "messages")
        enviar_mensagem = _get(ctx, "enviar_mensagem")
        remover_prefixo = _get(ctx, "_remover_prefixo_exec")
        limpar_resposta = _get(ctx, "limpar_resposta")
        try:
            if isinstance(messages, list):
                messages.append({"role": "user", "content": texto_original})
            bot_raw = enviar_mensagem(messages) if callable(enviar_mensagem) else ""
            bot = (
                remover_prefixo(limpar_resposta(bot_raw))
                if callable(remover_prefixo) and callable(limpar_resposta)
                else str(bot_raw)
            )
            if bot and isinstance(messages, list):
                messages.append({"role": "assistant", "content": bot})
            fallback = escolher_fala_variada(["Oi.", "Fala comigo.", "Tô por aqui."])
            _falar(
                ctx,
                bot or fallback,
                str(_get(ctx, "current_emotion", "calma")),
                _get(ctx, "emotion_level", 1),
            )
            if bot and callable(registrar):
                registrar(texto_original, bot, "SEARCH", query, "", "pesquisa")
        except Exception as erro:
            relatar_falha_ctx(
                ctx,
                "executor_navegador",
                "falha_resposta_conversacional",
                erro=erro,
                impacto="turno",
                fallback="saudacao_local",
                dominio="navegador",
                fase="pesquisa_conversacional",
            )
            _falar(ctx, escolher_fala_variada(["Oi.", "Fala comigo.", "Tô por aqui."]))
        return ResultadoDespacho.concluido()

    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    if destino == "pc_b" and callable(enviar_pc_b):
        enviar_pc_b({"action": "open_url", "url": url + "&laylay_auto=true", "auto_click": True})
    elif navegador_operacoes is not None:
        navegador_operacoes.abrir_url(url + "&laylay_auto=true", auto_click=True)
    fala = escolher_fala_variada([
        f"Abrindo a busca para {query}.",
        f"Já procurei {query}.",
        f"Abri a busca de {query}.",
    ])
    _falar(ctx, fala)
    if callable(registrar):
        registrar(texto_original, fala, "SEARCH", query, "", "pesquisa")
    return ResultadoDespacho.concluido()


def executar_intencao_navegador(
    intent: str,
    params: Dict[str, Any],
    texto_original: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    """Executa uma intencao web ou devolve ``nao_tratado`` sem efeitos."""

    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_NAVEGADOR:
        return ResultadoDespacho.nao_tratado()
    if intent == "OPEN_URL":
        return _executar_open_url(params, ctx, deps)
    if intent == "CLOSE_IDLE_TABS":
        return _executar_fechar_abas_paradas(ctx, deps)
    if intent == "CLOSE_TAB":
        return _executar_fechar_aba(params, texto_original, destino, ctx, deps)
    if intent == "SITE_ENTER":
        return _executar_entrar_site(params, texto_original, ctx, deps)
    return _executar_search(params, texto_original, destino, ctx, deps)
