"""Inventario, reproducao e mutacoes das playlists locais do usuario."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_comum import falar_ctx as _falar
from mente_laylay.integracao.registro_musica import PortaMusicaLeitura
from mente_laylay.integracao.registro_operacoes_musicais import PortaMusicaOperacoes
from mente_laylay.personalidade.falas_variadas import (
    escolher as escolher_fala_variada,
    fala_de_confirmacao,
)
from mente_laylay.personalidade.higiene_fala import limpar_titulo_musical_para_fala


INTENCOES_PLAYLISTS = frozenset({
    "PLAYLIST_CREATE", "PLAYLIST_DELETE", "PLAYLIST_ADD", "PLAYLIST_LIST", "PLAYLIST_PLAY",
    "PLAYLIST_MOVE",
})


@dataclass(frozen=True, slots=True)
class DependenciasExecutorPlaylists:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    abrir_url_musical: Callable[..., bool]
    contexto_fala: Callable[[], Dict[str, Any]]
    musica_leitura: PortaMusicaLeitura | None = None
    musica_operacoes: PortaMusicaOperacoes | None = None


def _get(ctx: Dict[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default)


def _nome_playlist(params: Dict[str, Any]) -> str:
    return str(
        params.get("nome_playlist") or params.get("playlist") or params.get("nome") or ""
    ).strip()


def _nome_explicito_incompleto(texto: str, ctx: Dict[str, Any]) -> bool:
    verificar = _get(ctx, "_playlist_nome_explicito_na_frase")
    return bool(verificar(texto)) if callable(verificar) else False


def _definir_ultima(deps: DependenciasExecutorPlaylists, nome: str) -> None:
    if deps.musica_operacoes is not None:
        deps.musica_operacoes.definir_ultima_playlist(nome)


def _sugerir_criacao(ctx: Dict[str, Any], nome: str) -> None:
    definir_pendente = _get(ctx, "set_playlist_sugestao_pendente")
    if callable(definir_pendente):
        definir_pendente({"playlist": nome, "ts": time.time()})
    _falar(ctx, escolher_fala_variada([
        f"Você ainda não criou a playlist {nome}. Quer que eu salve essa música nela?",
        f"{nome} ainda não existe. Quer que eu salve essa música lá?",
        f"Não achei a playlist {nome}. Posso guardar essa música nela?",
    ]))


def _marcar_com_alvo(
    deps: DependenciasExecutorPlaylists,
    status: str,
    nome: str,
    *,
    executou: bool | None,
    confirmado: bool | None = None,
) -> None:
    """Devolve à mente o nome que o executor realmente resolveu."""
    kwargs: Dict[str, Any] = {
        "executou": executou,
        "alvo_resolvido": nome,
        "params_resolvidos": {"nome_playlist": nome},
    }
    if confirmado is not None:
        kwargs["confirmado"] = confirmado
    try:
        deps.marcar_resultado(status, **kwargs)
    except TypeError:
        # Compatibilidade com portas antigas que ainda aceitam só o estado.
        kwargs.pop("alvo_resolvido", None)
        kwargs.pop("params_resolvidos", None)
        deps.marcar_resultado(status, **kwargs)


def _criar(
    params: Dict[str, Any], ctx: Dict[str, Any], deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    nome = _nome_playlist(params)
    if not nome:
        deps.marcar_resultado("alvo_ausente", executou=False)
        _falar(ctx, escolher_fala_variada([
            "Qual nome você quer dar à playlist?",
            "Faltou o nome da playlist.",
            "Me diz como essa playlist vai se chamar.",
        ]))
        return ResultadoDespacho.concluido(False)
    criar = getattr(deps.musica_operacoes, "criar_playlist", None)
    resultado = dict(criar(nome) or {}) if callable(criar) else {}
    nome_real = str(resultado.get("nome") or nome).strip()
    ok = bool(resultado.get("ok"))
    criada = bool(resultado.get("criada"))
    if not ok:
        _marcar_com_alvo(
            deps, str(resultado.get("status") or "falha_execucao"), nome_real,
            executou=False, confirmado=False,
        )
        _falar(ctx, f"Não consegui criar a playlist {nome_real} agora.")
        return ResultadoDespacho.concluido(False)
    _definir_ultima(deps, nome_real)
    status = "playlist_criada" if criada else "playlist_ja_existia"
    _marcar_com_alvo(deps, status, nome_real, executou=criada, confirmado=True)
    _falar(ctx, escolher_fala_variada(
        [
            f"Criei a playlist {nome_real}. Ela está vazia e pronta para receber músicas.",
            f"Playlist {nome_real} criada. Agora falta alimentar a criatura.",
            f"Pronto, {nome_real} já existe e está vazia.",
        ] if criada else [
            f"A playlist {nome_real} já existia. Não criei outra por cima.",
            f"{nome_real} já estava nas suas playlists.",
            f"Essa eu não dupliquei: {nome_real} já existe.",
        ]
    ))
    return ResultadoDespacho.concluido(True)


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
    ok = bool(
        deps.musica_operacoes.apagar_playlist(nome)
    ) if deps.musica_operacoes is not None else False
    status = "playlist_deletada" if ok else "falha_execucao"
    _marcar_com_alvo(deps, status, nome, executou=ok)
    if ok:
        _definir_ultima(deps, "")
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


def _adicionar(
    params: Dict[str, Any], texto: str, ctx: Dict[str, Any], deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    nome = _nome_playlist(params)
    if not nome:
        if _nome_explicito_incompleto(texto, ctx):
            deps.marcar_resultado(
                "alvo_ausente", executou=False, confirmado=False,
            )
            _falar(ctx, escolher_fala_variada([
                "Qual playlist é essa? Me diz o nome certo ou me ensina o apelido.",
                "Essa playlist veio meio torta. Me passa o nome certo.",
                "Preciso do nome da playlist ou do apelido que eu já conheço.",
            ]))
            return ResultadoDespacho.concluido(False)
        nome = str(_get(ctx, "ultima_playlist", "") or "").strip()
    if not nome:
        deps.marcar_resultado(
            "alvo_ausente", executou=False, confirmado=False,
        )
        _falar(ctx, escolher_fala_variada([
            "Me diz o nome da playlist.", "Qual playlist você quer?", "Faltou o nome da playlist.",
        ]))
        return ResultadoDespacho.concluido(False)

    info = (
        deps.musica_operacoes.faixa_atual()
        if deps.musica_operacoes is not None else {}
    )
    url = str(info.get("url") or "") if isinstance(info, dict) else ""
    titulo = str(info.get("title") or "") if isinstance(info, dict) else ""
    canal = str(info.get("canal") or "") if isinstance(info, dict) else ""
    if not url:
        _marcar_com_alvo(
            deps, "faixa_atual_indisponivel", nome,
            executou=False, confirmado=False,
        )
        _falar(ctx, escolher_fala_variada([
            "Ih, perdi o sinal do Chrome e não consegui salvar.",
            "Perdi a janela do Chrome e não consegui salvar.",
            "Não achei a aba certa para salvar isso.",
        ]))
        return ResultadoDespacho.concluido(False)
    if "youtube.com" not in url:
        _marcar_com_alvo(
            deps, "fonte_musical_invalida", nome,
            executou=False, confirmado=False,
        )
        _falar(ctx, escolher_fala_variada([
            "Não achei música aberta pra salvar aqui.",
            "Não vi nenhuma música aberta para guardar.",
            "Faltou uma música aberta no navegador.",
        ]))
        return ResultadoDespacho.concluido(False)

    adicionar_detalhado = getattr(
        deps.musica_operacoes, "adicionar_faixa_resultado", None,
    )
    if callable(adicionar_detalhado):
        resultado_adicao = dict(
            adicionar_detalhado(nome, url, titulo, canal) or {}
        )
    else:
        ok_legado = bool(
            deps.musica_operacoes.adicionar_faixa(nome, url, titulo, canal)
        ) if deps.musica_operacoes is not None else False
        resultado_adicao = {
            "ok": ok_legado,
            "added": ok_legado,
            "duplicated": False,
        }
    ok = bool(resultado_adicao.get("ok"))
    adicionada = bool(resultado_adicao.get("added"))
    duplicada = bool(resultado_adicao.get("duplicated")) or (ok and not adicionada)
    status = (
        "playlist_musica_ja_existia"
        if duplicada
        else "playlist_musica_adicionada"
        if ok
        else str(resultado_adicao.get("status") or "falha_execucao")
    )
    if duplicada:
        # O estado desejado está confirmado, mas nenhuma nova mutação ocorreu.
        _marcar_com_alvo(
            deps, status, nome, executou=False, confirmado=True,
        )
    else:
        _marcar_com_alvo(deps, status, nome, executou=ok)
    if ok:
        _definir_ultima(deps, nome)
        limpar_titulo = _get(ctx, "_yt_clean_title", lambda valor: valor)
        titulo_limpo = (
            limpar_titulo_musical_para_fala(limpar_titulo(titulo))
            or "essa música"
        )
        if duplicada:
            fala = escolher_fala_variada([
                f"{titulo_limpo} já estava na playlist {nome}; não dupliquei.",
                f"Essa já estava em {nome}. Mantive uma única cópia de {titulo_limpo}.",
                f"{titulo_limpo} já tinha sido salva em {nome}.",
            ])
        else:
            fala = escolher_fala_variada([
                f"Beleza, guardando {titulo_limpo} na playlist {nome}.",
                f"Pronto, {titulo_limpo} foi pra playlist {nome}.",
                f"Salvei {titulo_limpo} em {nome}.",
            ])
        deps.falar_por_status(
            status,
            fala,
            alvo=nome,
            executou=False if duplicada else True,
            confirmado=True,
        )
    else:
        deps.falar_por_status(status, escolher_fala_variada([
            "Ih, deu erro no meu caderninho aqui. Não consegui salvar essa porcaria não.",
            "Meu caderninho travou e não salvou agora.",
            "Deu ruim no registro da playlist. Tenta de novo.",
        ]), alvo=nome)
    return ResultadoDespacho.concluido(ok)


def _mover(
    params: Dict[str, Any], ctx: Dict[str, Any], deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    musica = str(params.get("musica") or params.get("faixa") or "").strip()
    origem = str(params.get("origem") or params.get("playlist_origem") or "").strip()
    destino = str(params.get("destino") or params.get("playlist_destino") or "").strip()
    if not musica or not origem or not destino:
        _falar(ctx, escolher_fala_variada([
            "Me diz a música, a playlist de origem e a de destino.",
            "Essa mudança veio incompleta. De qual playlist ela sai e pra qual vai?",
            "Faltou a faixa ou uma das playlists nessa mudança.",
        ]))
        deps.marcar_resultado("alvo_ausente", executou=False)
        return ResultadoDespacho.concluido(False)

    resultado = (
        deps.musica_operacoes.mover_faixa(origem, destino, musica)
        if deps.musica_operacoes is not None else {}
    )
    resultado = resultado if isinstance(resultado, dict) else {}
    if resultado.get("ok"):
        titulo = limpar_titulo_musical_para_fala(
            str(resultado.get("titulo") or musica or "essa música").strip()
        ) or "essa música"
        origem_real = str(resultado.get("origem") or origem).strip()
        destino_real = str(resultado.get("destino") or destino).strip()
        status = "playlist_faixa_movida"
        _marcar_com_alvo(
            deps, status, destino_real, executou=True, confirmado=True,
        )
        _definir_ultima(deps, destino_real)
        fala = f"Movi {titulo} da playlist {origem_real} pra {destino_real}."
        if resultado.get("duplicated"):
            fala = (
                f"Tirei {titulo} da playlist {origem_real}; "
                f"ela já estava em {destino_real}."
            )
        deps.falar_por_status(status, fala, alvo=destino_real)
        return ResultadoDespacho.concluido(True)

    erro = str(resultado.get("error") or "").strip()
    status = "playlist_origem_vazia" if erro == "source_empty" else "falha_execucao"
    _marcar_com_alvo(
        deps, status, origem, executou=False, confirmado=False,
    )
    if erro == "source_empty":
        fala = f"Não achei nada na playlist {origem} pra mover."
    else:
        fala = "Não consegui confirmar essa mudança entre as playlists."
    deps.falar_por_status(status, fala, alvo=origem)
    return ResultadoDespacho.concluido(False)


def _listar(
    params: Dict[str, Any], texto: str, ctx: Dict[str, Any],
    deps: DependenciasExecutorPlaylists,
) -> ResultadoDespacho:
    nome = _nome_playlist(params)
    pedido_geral = _get(ctx, "_pedido_lista_geral_playlist")
    if callable(pedido_geral) and pedido_geral(texto, params):
        if deps.musica_leitura is None:
            deps.marcar_resultado(
                "executor_indisponivel", executou=False, confirmado=False,
            )
            _falar(ctx, "Não consegui acessar suas playlists agora.")
            return ResultadoDespacho.concluido(False)
        _falar(
            ctx,
            deps.musica_leitura.listar_usuario(),
        )
        deps.marcar_resultado(
            "playlists_listadas", executou=True, confirmado=True,
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
            deps.marcar_resultado(
                "alvo_ausente", executou=False, confirmado=False,
            )
            _falar(ctx, escolher_fala_variada([
                "Qual playlist você quer ver? Esse nome veio pela metade.",
                "Me fala o nome completo da playlist.",
                "Esse nome ficou incompleto. Me dá a playlist certa.",
            ]))
            return ResultadoDespacho.concluido()
        nome = str(_get(ctx, "ultima_playlist", "") or "").strip()
    if not nome:
        deps.marcar_resultado(
            "alvo_ausente", executou=False, confirmado=False,
        )
        _falar(ctx, escolher_fala_variada([
            "Tá, mas qual playlist? Eu não leio pensamento. Ainda.",
            "Me diz qual playlist você quer ver.",
            "Faltou o nome da playlist.",
        ]), "debochada", 2)
        return ResultadoDespacho.concluido()

    if deps.musica_leitura is None:
        _marcar_com_alvo(
            deps, "executor_indisponivel", nome,
            executou=False, confirmado=False,
        )
        _falar(ctx, "Não consegui acessar suas playlists agora.")
        return ResultadoDespacho.concluido(False)

    info = deps.musica_leitura.consultar_usuario(nome)
    nome_real = str(info.get("name") or nome).strip()
    total = int(info.get("total", 0) or 0)
    estilizar = _get(ctx, "_fala_playlist_conteudo_estilosa")
    if info.get("ok") and total > 0 and callable(estilizar):
        _falar(ctx, estilizar(info, nome))
    elif info.get("ok"):
        _falar(ctx, escolher_fala_variada([
            f"A playlist {nome_real} existe, mas está vazia.",
            f"{nome_real} está salva, só ainda não tem músicas.",
            f"Achei {nome_real}; por enquanto ela tem zero faixas.",
        ]))
    else:
        _falar(ctx, escolher_fala_variada([
            f"Não achei a playlist {nome}. Se quiser, eu listo as que estão salvas.",
            f"{nome} não apareceu. Posso listar as que estão salvas.",
            f"Não encontrei {nome}. Quer que eu mostre as playlists salvas?",
        ]))
    # Consultar uma playlist é uma operação de leitura. Encontrá-la vazia ou
    # confirmar que ela não existe ainda é um resultado final observado no
    # armazenamento; não pode deixar o plano em estado pendente para sempre.
    _marcar_com_alvo(
        deps, "playlists_listadas", nome_real or nome,
        executou=True, confirmado=True,
    )
    _definir_ultima(deps, nome_real or nome)
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

    info_playlist = (
        deps.musica_leitura.consultar_usuario(nome)
        if deps.musica_leitura is not None else {}
    )
    total_playlist = (
        deps.musica_leitura.contar_usuario(nome)
        if deps.musica_leitura is not None else 0
    )
    playlist_encontrada = bool(info_playlist.get("ok")) or total_playlist > 0
    if deps.musica_leitura is not None and not playlist_encontrada:
        _marcar_com_alvo(
            deps, "playlist_nao_encontrada", nome,
            executou=False, confirmado=False,
        )
        _sugerir_criacao(ctx, nome)
        return ResultadoDespacho.concluido()
    if (
        deps.musica_leitura is not None
        and int(info_playlist.get("total") or total_playlist) <= 0
    ):
        _marcar_com_alvo(
            deps, "playlist_vazia", nome, executou=False, confirmado=False,
        )
        _falar(ctx, escolher_fala_variada([
            f"A playlist {nome} existe, mas está vazia.",
            f"{nome} está criada, só ainda não tem música para tocar.",
            f"Achei {nome}, mas ela está sem faixas por enquanto.",
        ]))
        return ResultadoDespacho.concluido()

    modo = str(params.get("modo") or "").strip().lower()
    if modo == "shuffle":
        info = (
            deps.musica_operacoes.preparar_shuffle(nome)
            if deps.musica_operacoes is not None else {}
        )
        if not info or not str(info.get("url") or ""):
            _falar(ctx, escolher_fala_variada([
                f"Essa playlist {nome} tá vazia. Quer que eu invente música também?",
                f"{nome} tá vazia por enquanto.",
                f"Não tem música em {nome} ainda.",
            ]), "debochada", 2)
            return ResultadoDespacho.concluido()
        url = str(info.get("url") or "")
        ok = deps.abrir_url_musical(url)
        if deps.musica_operacoes is not None:
            deps.musica_operacoes.definir_ultima_url(url)
        _definir_ultima(deps, nome)
        status = "playlist_aberta" if ok else "falha_execucao"
        _marcar_com_alvo(deps, status, nome, executou=ok)
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
        url = (
            deps.musica_operacoes.primeira_url(nome)
            if deps.musica_operacoes is not None else ""
        )
        if not url:
            _sugerir_criacao(ctx, nome)
            return ResultadoDespacho.concluido()
        ok = deps.abrir_url_musical(str(url or ""))
        _definir_ultima(deps, nome)
        status = "playlist_aberta_pc_b" if ok else "falha_execucao"
        _marcar_com_alvo(deps, status, nome, executou=ok)
        deps.falar_por_status(status, fala_de_confirmacao(
            "playlist_play",
            fallback=f"Abrindo sua playlist de {nome} no PC B."
            if ok else f"Tentei abrir {nome} no PC B, mas a rota falhou.",
            alvo=nome,
            contexto=deps.contexto_fala(),
            texto_usuario=texto,
        ), alvo=nome)
        return ResultadoDespacho.concluido(ok)

    ok = bool(
        deps.musica_operacoes.tocar_playlist(nome)
    ) if deps.musica_operacoes is not None else False
    if not ok:
        _marcar_com_alvo(deps, "falha_execucao", nome, executou=False)
        deps.falar_por_status(
            "falha_execucao",
            f"A playlist {nome} existe, mas o navegador não conseguiu abrir a primeira faixa.",
            alvo=nome,
        )
        return ResultadoDespacho.concluido()
    _definir_ultima(deps, nome)
    total = total_playlist
    obter_estado = getattr(deps.musica_operacoes, "estado", None)
    estado_reproducao = dict(obter_estado() or {}) if callable(obter_estado) else {}
    sem_confirmacao = (
        str(estado_reproducao.get("status_avanco") or "").strip()
        == "enviado_sem_confirmacao"
    )
    status = "playlist_enviada_sem_confirmacao" if sem_confirmacao else "playlist_aberta"
    if sem_confirmacao:
        # A primeira faixa foi entregue e a fila ficou ativa. O estado do
        # áudio é desconhecido, não uma falha nem uma autorização pendente.
        _marcar_com_alvo(deps, status, nome, executou=True, confirmado=None)
    else:
        _marcar_com_alvo(deps, status, nome, executou=True)
    deps.falar_por_status(status, fala_de_confirmacao(
        "playlist_play",
        fallback=(
            f"Abri a primeira faixa de {nome} e mantive a fila com {total} músicas ativa, "
            "mas o player não confirmou o áudio."
            if sem_confirmacao else
            f"Abrindo sua playlist de {nome}. Você já tem {total} músicas guardadas comigo."
        ),
        alvo=nome,
        contexto=deps.contexto_fala(),
        texto_usuario=texto,
    ), alvo=nome, executou=True, confirmado=None if sem_confirmacao else True)
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
    if intent == "PLAYLIST_CREATE":
        return _criar(params, ctx, deps)
    if intent == "PLAYLIST_DELETE":
        return _apagar(params, ctx, deps)
    if intent == "PLAYLIST_ADD":
        return _adicionar(params, texto_original, ctx, deps)
    if intent == "PLAYLIST_MOVE":
        return _mover(params, ctx, deps)
    if intent == "PLAYLIST_LIST":
        return _listar(params, texto_original, ctx, deps)
    return _tocar(params, texto_original, destino, ctx, deps)
