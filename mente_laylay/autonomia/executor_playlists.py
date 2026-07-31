"""Inventario, reproducao e mutacoes das playlists locais do usuario."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.integracao.registro_musica import PortaMusicaLeitura
from mente_laylay.personalidade.falas_variadas import (
    escolher as escolher_fala_variada,
    fala_de_confirmacao,
)


INTENCOES_PLAYLISTS = frozenset({"PLAYLIST_DELETE", "PLAYLIST_ADD", "PLAYLIST_LIST", "PLAYLIST_PLAY"})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorPlaylists:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    abrir_url_musical: Callable[..., bool]
    contexto_fala: Callable[[], Dict[str, Any]]
    musica_leitura: PortaMusicaLeitura | None = None


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _nome_playlist(params: Dict[str, Any]) -> str:
    return str(
        params.get("nome_playlist") or params.get("playlist") or params.get("nome") or ""
    ).strip()


def _nome_explicito_incompleto(texto: str, ctx: Dict[str, Any]) -> bool:
    verificar = _get(ctx, "_playlist_nome_explicito_na_frase")
    return bool(verificar(texto)) if callable(verificar) else False


def _definir_ultima(ctx: Dict[str, Any], nome: str) -> None:
    definir = _get(ctx, "set_ultima_playlist")
    if callable(definir):
        definir(nome)


def _sugerir_criacao(ctx: Dict[str, Any], nome: str) -> None:
    definir_pendente = _get(ctx, "set_playlist_sugestao_pendente")
    if callable(definir_pendente):
        definir_pendente({"playlist": nome, "ts": time.time()})
    _falar(ctx, escolher_fala_variada([
        f"Você ainda não criou a playlist {nome}. Quer que eu salve essa música nela?",
        f"{nome} ainda não existe. Quer que eu salve essa música lá?",
        f"Não achei a playlist {nome}. Posso guardar essa música nela?",
    ]))


def _apagar(
    params: Dict[str, Any], ctx: Dict[str, Any], deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    nome = str(
        params.get("nome_playlist") or params.get("playlist") or params.get("nome")
        or params.get("alvo") or ""
    ).strip()
    if not nome:
        _falar(ctx, escolher_fala_variada([
            "Qual playlist eu apago?",
            "Me fala o nome da playlist antes de eu sair cortando coisa.",
            "Faltou o nome da playlist.",
        ]))
        return ResultadoDespacho.concluido()
    apagar = _get(ctx, "delete_playlist")
    ok = bool(apagar(nome)) if callable(apagar) else False
    status = "playlist_deletada" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    if ok:
        _definir_ultima(ctx, "")
    deps.falar_por_status(status, escolher_fala_variada([
        f"Apaguei a playlist {nome}. Ela saiu do palco.",
        f"Playlist {nome} deletada.",
        f"Pronto, removi {nome} das suas playlists.",
    ] if ok else [
        f"Tentei apagar a playlist {nome}, mas não encontrei ela.",
        f"{nome} não apareceu nas playlists pra eu apagar.",
        f"Procurei a playlist {nome}, mas ela não deu as caras.",
    ]), alvo=nome)
    return ResultadoDespacho.concluido()


def _resolver_faixa_atual(ctx: Dict[str, Any]) -> dict:
    obter_estado = _get(ctx, "_musica_estado_get")
    if callable(obter_estado):
        try:
            instante = float(obter_estado("musica_atual_ts", 0.0) or 0.0)
            status = str(obter_estado("musica_atual_status", "") or "").strip().casefold()
            url = str(obter_estado("musica_atual_url", "") or "").strip()
            titulo = str(obter_estado("musica_atual_titulo", "") or "").strip()
            recente = bool(instante and time.time() - instante <= 7200.0)
            utilizavel = status not in {"finalizada", "encerrada", "parada"}
            if recente and utilizavel and "youtube.com" in url:
                return {"url": url, "title": titulo, "canal": "", "origem": "player_atual"}
        except Exception as erro:
            log = _get(ctx, "log", print)
            if callable(log):
                log(
                    "⚠️ [PLAYLIST:CONTEXTO] estado da música atual indisponível: "
                    f"{type(erro).__name__}: {erro}"
                )
    solicitar_aba = _get(ctx, "solicitar_aba_ativa")
    return solicitar_aba() if callable(solicitar_aba) else {}


def _adicionar(
    params: Dict[str, Any], texto: str, ctx: Dict[str, Any], deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    nome = _nome_playlist(params)
    if not nome:
        if _nome_explicito_incompleto(texto, ctx):
            _falar(ctx, escolher_fala_variada([
                "Qual playlist é essa? Me diz o nome certo ou me ensina o apelido.",
                "Essa playlist veio meio torta. Me passa o nome certo.",
                "Preciso do nome da playlist ou do apelido que eu já conheço.",
            ]))
            return ResultadoDespacho.concluido()
        nome = str(_get(ctx, "ultima_playlist", "") or "").strip()
    if not nome:
        _falar(ctx, escolher_fala_variada([
            "Me diz o nome da playlist.", "Qual playlist você quer?", "Faltou o nome da playlist.",
        ]))
        return ResultadoDespacho.concluido()

    info = _resolver_faixa_atual(ctx)
    url = str(info.get("url") or "") if isinstance(info, dict) else ""
    titulo = str(info.get("title") or "") if isinstance(info, dict) else ""
    canal = str(info.get("canal") or "") if isinstance(info, dict) else ""
    if not url:
        _falar(ctx, escolher_fala_variada([
            "Ih, perdi o sinal do Chrome e não consegui salvar.",
            "Perdi a janela do Chrome e não consegui salvar.",
            "Não achei a aba certa para salvar isso.",
        ]))
        return ResultadoDespacho.concluido()
    if "youtube.com" not in url:
        _falar(ctx, escolher_fala_variada([
            "Não achei música aberta pra salvar aqui.",
            "Não vi nenhuma música aberta para guardar.",
            "Faltou uma música aberta no navegador.",
        ]))
        return ResultadoDespacho.concluido()

    adicionar = _get(ctx, "ADD_TO_PLAYLIST")
    ok = bool(adicionar(nome, url, titulo, canal)) if callable(adicionar) else False
    status = "playlist_musica_adicionada" if ok else "falha_execucao"
    deps.marcar_resultado(status, executou=ok)
    if ok:
        _definir_ultima(ctx, nome)
        limpar_titulo = _get(ctx, "_yt_clean_title", lambda valor: valor)
        titulo_limpo = limpar_titulo(titulo) or "essa música"
        deps.falar_por_status(status, escolher_fala_variada([
            f"Beleza, guardando {titulo_limpo} na playlist {nome}.",
            f"Pronto, {titulo_limpo} foi pra playlist {nome}.",
            f"Salvei {titulo_limpo} em {nome}.",
        ]), alvo=nome)
    else:
        deps.falar_por_status(status, escolher_fala_variada([
            "Ih, deu erro no meu caderninho aqui. Não consegui salvar essa porcaria não.",
            "Meu caderninho travou e não salvou agora.",
            "Deu ruim no registro da playlist. Tenta de novo.",
        ]), alvo=nome)
    return ResultadoDespacho.concluido()


def _listar(
    params: Dict[str, Any], texto: str, ctx: Dict[str, Any],
    deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    nome = _nome_playlist(params)
    pedido_geral = _get(ctx, "_pedido_lista_geral_playlist")
    if callable(pedido_geral) and pedido_geral(texto, params):
        _falar(
            ctx,
            deps.musica_leitura.listar_usuario()
            if deps.musica_leitura is not None else "Sem playlists.",
        )
        return ResultadoDespacho.concluido()
    extrair = _get(ctx, "extrair_nome_playlist")
    if not nome and callable(extrair):
        try:
            nome = str(extrair(texto) or "").strip()
        except Exception:
            nome = ""
    if not nome:
        if _nome_explicito_incompleto(texto, ctx):
            _falar(ctx, escolher_fala_variada([
                "Qual playlist você quer ver? Esse nome veio pela metade.",
                "Me fala o nome completo da playlist.",
                "Esse nome ficou incompleto. Me dá a playlist certa.",
            ]))
            return ResultadoDespacho.concluido()
        nome = str(_get(ctx, "ultima_playlist", "") or "").strip()
    if not nome:
        _falar(ctx, escolher_fala_variada([
            "Tá, mas qual playlist? Eu não leio pensamento. Ainda.",
            "Me diz qual playlist você quer ver.",
            "Faltou o nome da playlist.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()

    info = deps.musica_leitura.consultar_usuario(nome) if deps.musica_leitura else {
        "ok": False, "name": nome, "total": 0,
    }
    nome_real = str(info.get("name") or nome).strip()
    estilizar = _get(ctx, "_fala_playlist_conteudo_estilosa")
    if info.get("ok") and int(info.get("total", 0) or 0) > 0 and callable(estilizar):
        _falar(ctx, estilizar(info, nome))
    else:
        _falar(ctx, escolher_fala_variada([
            f"Não achei a playlist {nome}. Se quiser, eu listo as que estão salvas.",
            f"{nome} não apareceu. Posso listar as que estão salvas.",
            f"Não encontrei {nome}. Quer que eu mostre as playlists salvas?",
        ]))
    _definir_ultima(ctx, nome_real or nome)
    return ResultadoDespacho.concluido()


def _tocar(
    params: Dict[str, Any], texto: str, destino: str, ctx: Dict[str, Any],
    deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    permitir = _get(ctx, "_autonomia_permite_execucao_musical")
    if callable(permitir) and not permitir("PLAYLIST_PLAY", texto):
        print("🎵 [AUTONOMIA] PLAYLIST_PLAY bloqueado: sem pedido explícito de playlist.")
        return ResultadoDespacho.concluido(False)
    nome = _nome_playlist(params)
    if not nome:
        if _nome_explicito_incompleto(texto, ctx):
            _falar(ctx, escolher_fala_variada([
                "Qual playlist é essa? Fala o nome completo ou o apelido que eu já conheço.",
                "Essa playlist veio pela metade. Me fala o nome certo.",
                "Preciso do nome completo ou do apelido conhecido.",
            ]))
            return ResultadoDespacho.concluido()
        nome = str(_get(ctx, "ultima_playlist", "") or "").strip()
    if not nome:
        _falar(ctx, escolher_fala_variada([
            "Tá, mas qual playlist? Eu não leio pensamento. Ainda.",
            "Me diz qual playlist você quer tocar.",
            "Faltou o nome da playlist.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()

    modo = str(params.get("modo") or "").strip().lower()
    if modo == "shuffle":
        iniciar_shuffle = _get(ctx, "_playlist_shuffle_start")
        info = iniciar_shuffle(nome) if callable(iniciar_shuffle) else None
        if not info or not str(info.get("url") or ""):
            _falar(ctx, escolher_fala_variada([
                f"Essa playlist {nome} tá vazia. Quer que eu invente música também?",
                f"{nome} tá vazia por enquanto.",
                f"Não tem música em {nome} ainda.",
            ]), "debochada", 2)
            return ResultadoDespacho.concluido()
        url = str(info.get("url") or "")
        ok = deps.abrir_url_musical(url)
        definir_url = _get(ctx, "set_playlist_state_last_url")
        if callable(definir_url):
            definir_url(url)
        _definir_ultima(ctx, nome)
        status = "playlist_aberta" if ok else "falha_execucao"
        deps.marcar_resultado(status, executou=ok)
        deps.falar_por_status(status, fala_de_confirmacao(
            "playlist_play",
            fallback=f"Abrindo sua playlist de {nome}."
            if ok else f"Tentei abrir a playlist {nome}, mas a rota musical falhou.",
            alvo=nome,
            contexto=deps.contexto_fala(),
            texto_usuario=texto,
        ), alvo=nome)
        return ResultadoDespacho.concluido(ok)

    if destino == "pc_b":
        primeira_url = _get(ctx, "_playlist_primeira_url")
        url = primeira_url(nome) if callable(primeira_url) else None
        if not url:
            _sugerir_criacao(ctx, nome)
            return ResultadoDespacho.concluido()
        ok = deps.abrir_url_musical(str(url or ""))
        _definir_ultima(ctx, nome)
        status = "playlist_aberta_pc_b" if ok else "falha_execucao"
        deps.marcar_resultado(status, executou=ok)
        deps.falar_por_status(status, fala_de_confirmacao(
            "playlist_play",
            fallback=f"Abrindo sua playlist de {nome} no PC B."
            if ok else f"Tentei abrir {nome} no PC B, mas a rota falhou.",
            alvo=nome,
            contexto=deps.contexto_fala(),
            texto_usuario=texto,
        ), alvo=nome)
        return ResultadoDespacho.concluido(ok)

    tocar = _get(ctx, "play_playlist")
    ok = bool(tocar(nome)) if callable(tocar) else False
    if not ok:
        deps.marcar_resultado("falha_execucao", executou=False)
        _sugerir_criacao(ctx, nome)
        return ResultadoDespacho.concluido()
    _definir_ultima(ctx, nome)
    total = deps.musica_leitura.contar_usuario(nome) if deps.musica_leitura else 0
    deps.marcar_resultado("playlist_aberta", executou=True)
    deps.falar_por_status("playlist_aberta", fala_de_confirmacao(
        "playlist_play",
        fallback=f"Abrindo sua playlist de {nome}. Você já tem {total} músicas guardadas comigo.",
        alvo=nome,
        contexto=deps.contexto_fala(),
        texto_usuario=texto,
    ), alvo=nome)
    return ResultadoDespacho.concluido()


def executar_intencao_playlists(
    intent: str,
    params: Dict[str, Any],
    texto_original: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    intent = str(intent or "").upper().strip()
    if intent not in INTENCOES_PLAYLISTS:
        return ResultadoDespacho.nao_tratado()
    if intent == "PLAYLIST_DELETE":
        return _apagar(params, ctx, deps)
    if intent == "PLAYLIST_ADD":
        return _adicionar(params, texto_original, ctx, deps)
    if intent == "PLAYLIST_LIST":
        return _listar(params, texto_original, ctx, deps)
    return _tocar(params, texto_original, destino, ctx, deps)
