"""Pesquisa musical e curadoria de playlists próprias da Laylay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict
from urllib.parse import urlparse

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import (
    falar_ctx as _falar,
    relatar_falha_ctx,
)
from mente_laylay.integracao.registro_musica import PortaMusicaLeitura
from mente_laylay.integracao.registro_operacoes_musicais import PortaMusicaOperacoes
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_MUSICAIS = frozenset({
    "MUSIC_SEARCH", "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY",
    "LAYLAY_PLAYLIST_COPY",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorMusical:
    marcar_resultado: Callable[..., Any]
    abrir_url_musical: Callable[..., Any]
    registrar_mente: Callable[..., Any] | None = None
    falar_por_status: Callable[..., Any] | None = None
    musica_leitura: PortaMusicaLeitura | None = None
    musica_operacoes: PortaMusicaOperacoes | None = None


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _url_video_youtube(url: str) -> bool:
    try:
        parsed = urlparse(str(url or "").strip())
        host = parsed.netloc.casefold().removeprefix("www.")
        return bool(
            host == "youtu.be"
            or (host.endswith("youtube.com") and parsed.path == "/watch")
        )
    except Exception:
        return False


def _normalizar_evidencia_execucao(retorno: Any) -> dict[str, Any]:
    if isinstance(retorno, dict):
        dados = dict(retorno)
        ok = bool(dados.get("ok"))
        confirmado = dados.get("confirmado")
        return {
            **dados,
            "ok": ok,
            "confirmado": (
                bool(confirmado) if confirmado is not None else None
            ),
        }
    return {
        "ok": bool(retorno),
        "confirmado": True if retorno is True else False,
        "status": "confirmacao_legada" if retorno is True else "falha_execucao",
    }


def _pesquisar(
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorMusical,
) -> ResultadoDespacho:
    origem = str(params.get("origem") or "").strip().lower()
    pedido_confirmado = origem in {"continuacao_busca", "sugestao_conversacional"}
    permitir = _get(ctx, "_autonomia_permite_execucao_musical")
    if callable(permitir) and not permitir(
        "MUSIC_SEARCH", texto_original, confirmado=pedido_confirmado,
    ):
        print("🎵 [AUTONOMIA] MUSIC_SEARCH bloqueado: sem pedido musical explícito.")
        return ResultadoDespacho.concluido(False)

    consulta_pedida = str(
        params.get("query") or params.get("musica") or params.get("nome") or texto_original
    ).strip()
    query = consulta_pedida
    normalizar = _get(ctx, "_normalizar_query_musical")
    if callable(normalizar):
        query = normalizar(query or texto_original)
    resolver_estilo = _get(ctx, "_resolver_query_musical_por_estilo")
    perfil: Dict[str, Any] = {}
    if callable(resolver_estilo):
        try:
            try:
                perfil = resolver_estilo(query, texto_original, params)
            except TypeError:
                # Compatibilidade com adaptadores antigos e integrações externas.
                perfil = resolver_estilo(query, texto_original)
            if isinstance(perfil, dict) and str(perfil.get("query") or "").strip():
                query = str(perfil.get("query") or query).strip()
        except Exception as erro:
            relatar_falha_ctx(
                ctx,
                "executor_musical",
                "falha_resolucao_estilo",
                erro=erro,
                classe="degradacao",
                impacto="servico",
                fallback="consulta_original",
                dominio="musica",
                fase="refinar_pesquisa",
            )
            perfil = {}
    if not query:
        fala = escolher_fala_variada([
            "Tá, mas tocar o quê? Fala a música direito.",
            "Me diz a música.",
            "Qual faixa você quer?",
        ])
        _falar(ctx, fala, "debochada", 2)
        deps.marcar_resultado("alvo_ausente", executou=False)
        if callable(deps.registrar_mente):
            deps.registrar_mente(
                texto_original,
                fala,
                "MUSIC_SEARCH",
                "",
                "music",
                "musica",
            )
        # A ação não ocorreu; o fluxo conversacional ainda pode acrescentar
        # uma sugestão, mas a pendência operacional permanece prioritária.
        return ResultadoDespacho.concluido(False)

    tipo_resultado = str(perfil.get("tipo_resultado") or "faixa").strip()
    origem_pesquisa = str(perfil.get("origem") or "").strip()
    if origem_pesquisa and origem_pesquisa not in {"explicita", "nao_resolvida"}:
        print(
            f"🧭 [PESQUISA:MUSICA] origem={origem_pesquisa} "
            f"tipo={tipo_resultado} consulta={query!r}"
        )
    resolver_video = _get(ctx, "_resolver_primeiro_video_youtube")
    buscar_video = _get(ctx, "_buscar_primeiro_video_youtube")
    selecao: Dict[str, Any] = {}
    if callable(resolver_video):
        try:
            selecao_bruta = resolver_video(query, tipo_resultado=tipo_resultado)
        except TypeError:
            selecao_bruta = resolver_video(query)
        if isinstance(selecao_bruta, dict):
            selecao = dict(selecao_bruta)
    elif callable(buscar_video):
        try:
            link_legado = buscar_video(query, tipo_resultado=tipo_resultado)
        except TypeError:
            link_legado = buscar_video(query)
        if str(link_legado or "").strip():
            selecao = {"url": str(link_legado).strip(), "title": query}

    link = str(selecao.get("url") or "").strip()
    titulo_resolvido = str(
        selecao.get("title") or selecao.get("titulo") or query
    ).strip()
    canal_resolvido = str(
        selecao.get("channel") or selecao.get("canal") or ""
    ).strip()
    params["consulta_pedida"] = consulta_pedida
    params["consulta_resolvida"] = query

    if not _url_video_youtube(link):
        params["alvo_executado"] = ""
        fala_resultado = escolher_fala_variada([
            f"Não achei uma faixa reproduzível para {query}; não abri uma busca fingindo que era música.",
            f"A busca por {query} não chegou a um vídeo confiável, então não toquei nada.",
            f"Não consegui resolver {query} em uma faixa concreta. Parei antes de abrir qualquer resultado duvidoso.",
        ])
        deps.marcar_resultado(
            "musica_nao_resolvida", executou=False, confirmado=False,
            detalhe="nenhum_video_reproduzivel",
        )
        if callable(deps.falar_por_status):
            deps.falar_por_status(
                "musica_nao_resolvida",
                fala_resultado,
                alvo=query,
                executou=False,
                confirmado=False,
                detalhe="nenhum_video_reproduzivel",
            )
        else:
            _falar(ctx, fala_resultado, "calma", 1)
        return ResultadoDespacho.concluido(False)

    params["alvo_executado"] = titulo_resolvido
    params["alvo_executado_url"] = link
    if canal_resolvido:
        params["alvo_executado_canal"] = canal_resolvido
    # O alvo do contrato e da autoria passa a ser a seleção real, enquanto a
    # formulação original continua disponível em ``consulta_pedida``.
    params["query"] = titulo_resolvido
    evidencia = _normalizar_evidencia_execucao(
        deps.abrir_url_musical(link, query="")
    )
    ok = bool(evidencia.get("ok"))
    confirmado_execucao = evidencia.get("confirmado")
    if ok and confirmado_execucao is True:
        status = "musica_reproduzindo"
    elif ok:
        status = "musica_enviada_sem_confirmacao"
    else:
        status = "falha_execucao"
    detalhe_execucao = str(
        evidencia.get("message") or evidencia.get("mensagem")
        or evidencia.get("status") or ""
    ).strip()
    deps.marcar_resultado(
        status,
        executou=ok,
        confirmado=confirmado_execucao if ok else False,
        detalhe=detalhe_execucao,
    )
    fala_resultado = escolher_fala_variada([
            f"{titulo_resolvido} está tocando agora.",
            f"Pronto, confirmei {titulo_resolvido} em reprodução.",
            f"Achei {titulo_resolvido} e o player confirmou o som.",
        ] if ok and confirmado_execucao is True else [
            f"Abri {titulo_resolvido}, mas o player não confirmou a reprodução. "
            "Não vou fingir que o áudio já começou.",
            f"Abri {titulo_resolvido}, só não vou fingir que ouvi o player começar.",
        ] if ok else [
            f"Tentei tocar {titulo_resolvido}, mas o navegador não confirmou a reprodução.",
            f"Achei {titulo_resolvido}, porém o player não respondeu; não repeti o comando.",
            f"A seleção foi {titulo_resolvido}, mas a reprodução falhou de forma explícita.",
        ])
    if callable(deps.falar_por_status):
        deps.falar_por_status(
            status,
            fala_resultado,
            alvo=titulo_resolvido,
            executou=ok,
            confirmado=confirmado_execucao if ok else False,
            detalhe=detalhe_execucao,
        )
    else:
        _falar(
            ctx,
            fala_resultado,
            "calma" if ok else "irritada",
            1 if ok else 2,
        )
    return ResultadoDespacho.concluido(ok)


def _listar_curadoria(
    params: Dict[str, Any], ctx: Dict[str, Any], deps: DependenciasExecutorMusical,
) -> ResultadoDespacho:
    nome = str(
        params.get("nome_playlist") or params.get("playlist") or params.get("nome") or ""
    ).strip()
    nome_resolvido = nome
    selecionar = getattr(deps.musica_operacoes, "selecionar_curadoria", None)
    if nome and callable(selecionar):
        selecao = dict(selecionar(nome, 0) or {})
        nome_resolvido = str(selecao.get("playlist") or nome).strip()
    fala = (
        deps.musica_leitura.listar_laylay(nome_resolvido)
        if deps.musica_leitura is not None
        else "Ainda não montei playlists minhas por aqui."
    )
    _falar(ctx, fala)
    try:
        deps.marcar_resultado(
            "curadoria_listada",
            executou=True,
            confirmado=True,
            alvo_resolvido=nome_resolvido or "playlists da Laylay",
            params_resolvidos={"nome_playlist": nome_resolvido},
        )
    except TypeError:
        deps.marcar_resultado("curadoria_listada", executou=True, confirmado=True)
    return ResultadoDespacho.concluido()


def _tocar_curadoria(
    params: Dict[str, Any], ctx: Dict[str, Any], deps: DependenciasExecutorMusical,
) -> ResultadoDespacho:
    nome = str(
        params.get("nome_playlist") or params.get("playlist") or params.get("nome") or ""
    ).strip()
    selecionar = getattr(deps.musica_operacoes, "selecionar_curadoria", None)
    selecao = dict(selecionar(nome, 0) or {}) if callable(selecionar) else {}
    playlist = str(selecao.get("playlist") or nome or "uma das minhas playlists").strip()
    faixa_bruta = selecao.get("faixa")
    faixa = dict(faixa_bruta) if isinstance(faixa_bruta, dict) else {}
    url = str(faixa.get("url") or "").strip()
    titulo = str(faixa.get("titulo") or "a primeira faixa").strip()
    if not selecao.get("ok") or not _url_video_youtube(url):
        try:
            deps.marcar_resultado(
                "curadoria_nao_encontrada", executou=False, confirmado=False,
                alvo_resolvido=playlist,
            )
        except TypeError:
            deps.marcar_resultado("curadoria_nao_encontrada", executou=False, confirmado=False)
        _falar(ctx, f"Não achei uma faixa reproduzível na minha playlist {playlist}.")
        return ResultadoDespacho.concluido(False)

    evidencia = _normalizar_evidencia_execucao(deps.abrir_url_musical(url, query=""))
    ok = bool(evidencia.get("ok"))
    confirmado = evidencia.get("confirmado") if ok else False
    status = (
        "playlist_laylay_reproduzindo" if ok and confirmado is True
        else "playlist_laylay_enviada_sem_confirmacao" if ok
        else "falha_execucao"
    )
    try:
        deps.marcar_resultado(
            status,
            executou=ok,
            confirmado=confirmado,
            alvo_resolvido=playlist,
            params_resolvidos={
                "nome_playlist": playlist,
                "alvo_executado": titulo,
                "alvo_executado_url": url,
            },
        )
    except TypeError:
        deps.marcar_resultado(status, executou=ok, confirmado=confirmado)
    if ok and confirmado is True:
        fala = f"Escolhi {titulo} da minha playlist {playlist} e confirmei a reprodução."
    elif ok:
        fala = (
            f"Abri {titulo} da minha playlist {playlist}, mas o player ainda não "
            "confirmou o áudio."
        )
    else:
        fala = f"Tentei abrir {titulo} da minha playlist {playlist}, mas o navegador recusou."
    if callable(deps.falar_por_status):
        deps.falar_por_status(
            status, fala, alvo=playlist, executou=ok, confirmado=confirmado,
        )
    else:
        _falar(ctx, fala)
    return ResultadoDespacho.concluido(ok)


def _copiar_curadoria(
    params: Dict[str, Any],
    ctx: Dict[str, Any],
    deps: DependenciasExecutorMusical,
) -> ResultadoDespacho:
    musica = str(params.get("musica") or params.get("nome") or "").strip()
    origem = str(params.get("origem") or params.get("playlist_origem") or "").strip()
    destino = str(params.get("destino") or params.get("playlist_destino") or "").strip()
    if not musica or not origem or not destino:
        _falar(ctx, escolher_fala_variada([
            "Me fala qual música da minha playlist vai para qual playlist tua.",
            "Faltou dizer a música, a minha playlist e a tua playlist de destino.",
            "Preciso da faixa, da minha playlist e da tua playlist pra copiar certinho.",
        ]))
        return ResultadoDespacho.concluido()

    retorno = (
        deps.musica_operacoes.copiar_curadoria(origem, musica, destino)
        if deps.musica_operacoes is not None else {"ok": False}
    )
    resultado: Dict[str, Any] = (
        dict(retorno) if isinstance(retorno, dict) else {"ok": bool(retorno)}
    )
    if bool(resultado.get("ok")):
        faixa_bruta = resultado.get("faixa")
        faixa = dict(faixa_bruta) if isinstance(faixa_bruta, dict) else {}
        titulo = str(faixa.get("titulo") or musica).strip() or musica
        if deps.musica_operacoes is not None:
            deps.musica_operacoes.definir_ultima_playlist(destino)
        fala_resultado = escolher_fala_variada([
            f"Pronto, puxei {titulo} da minha playlist {origem} pra tua playlist {destino}.",
            f"Beleza, {titulo} saiu da minha curadoria e foi pra {destino}.",
            f"Já coloquei {titulo} da minha playlist {origem} em {destino}.",
        ])
        deps.marcar_resultado("playlist_musica_adicionada", executou=True)
        if callable(deps.falar_por_status):
            deps.falar_por_status(
                "playlist_musica_adicionada",
                fala_resultado,
                alvo=destino,
                executou=True,
                confirmado=True,
            )
        else:
            _falar(ctx, fala_resultado, "debochada", 2)
    else:
        fala_resultado = escolher_fala_variada([
            f"Não achei essa faixa na minha playlist {origem}.",
            f"A minha playlist {origem} não me entregou essa música agora.",
            f"Procurei na minha playlist {origem}, mas essa faixa não apareceu.",
        ])
        deps.marcar_resultado("nao_encontrado", executou=False)
        if callable(deps.falar_por_status):
            deps.falar_por_status(
                "nao_encontrado", fala_resultado, alvo=musica,
                executou=False, confirmado=False,
            )
        else:
            _falar(ctx, fala_resultado)
    return ResultadoDespacho.concluido()


def executar_intencao_musical(
    intent: str,
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorMusical,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_MUSICAIS:
        return ResultadoDespacho.nao_tratado()
    if intent == "MUSIC_SEARCH":
        return _pesquisar(params, texto_original, ctx, deps)
    if intent == "LAYLAY_PLAYLIST_LIST":
        return _listar_curadoria(params, ctx, deps)
    if intent == "LAYLAY_PLAYLIST_PLAY":
        return _tocar_curadoria(params, ctx, deps)
    return _copiar_curadoria(params, ctx, deps)
