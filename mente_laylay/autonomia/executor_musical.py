"""Pesquisa musical e curadoria de playlists próprias da Laylay."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.integracao.registro_musica import PortaMusicaLeitura
from mente_laylay.integracao.registro_operacoes_musicais import PortaMusicaOperacoes
from mente_laylay.personalidade.falas_variadas import escolher as escolher_fala_variada


INTENCOES_MUSICAIS = frozenset({"MUSIC_SEARCH", "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_COPY"})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorMusical:
    marcar_resultado: Callable[..., Any]
    abrir_url_musical: Callable[..., bool]
    registrar_mente: Callable[..., Any] | None = None
    falar_por_status: Callable[..., Any] | None = None
    musica_leitura: PortaMusicaLeitura | None = None
    musica_operacoes: PortaMusicaOperacoes | None = None


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _pesquisar(
    params: Dict[str, Any],
    texto_original: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorMusical,
) -> ResultadoDespacho:
    origem = str(params.get("origem") or "").strip().lower()
    confirmado = origem in {"continuacao_busca", "sugestao_conversacional"}
    permitir = _get(ctx, "_autonomia_permite_execucao_musical")
    if callable(permitir) and not permitir("MUSIC_SEARCH", texto_original, confirmado=confirmado):
        print("🎵 [AUTONOMIA] MUSIC_SEARCH bloqueado: sem pedido musical explícito.")
        return ResultadoDespacho.concluido(False)

    query = str(
        params.get("query") or params.get("musica") or params.get("nome") or texto_original
    ).strip()
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
        except Exception:
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
    buscar_video = _get(ctx, "_buscar_primeiro_video_youtube")
    link = ""
    if callable(buscar_video):
        try:
            link = buscar_video(query, tipo_resultado=tipo_resultado)
        except TypeError:
            link = buscar_video(query)
    url = link or ("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query))
    ok = deps.abrir_url_musical(url, query=query if not link else "")
    deps.marcar_resultado("musica_aberta" if ok else "falha_execucao", executou=ok)
    fala_resultado = escolher_fala_variada([
            f"Sintonizando o melhor do {query} no YouTube agora.",
            f"Botando {query} pra tocar agora.",
            f"Já achei {query}.",
        ] if ok else [
            f"Tentei puxar {query}, mas a rota musical falhou agora.",
            f"Fui atrás de {query}, mas não consegui abrir esse som direito.",
            f"Quase puxei {query}, mas a trilha não respondeu do jeito certo.",
        ])
    if callable(deps.falar_por_status):
        deps.falar_por_status(
            "musica_aberta" if ok else "falha_execucao",
            fala_resultado,
            alvo=query,
            executou=ok,
            confirmado=True if ok else False,
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
    fala = (
        deps.musica_leitura.listar_laylay(nome)
        if deps.musica_leitura is not None
        else "Ainda não montei playlists minhas por aqui."
    )
    _falar(ctx, fala)
    return ResultadoDespacho.concluido()


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
    return _copiar_curadoria(params, ctx, deps)
