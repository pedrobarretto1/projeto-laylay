"""Orquestracao das intencoes de navegador e pesquisa web."""

from __future__ import annotations

import urllib.parse
import re
import time
import unicodedata
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
    "LIST_TABS",
    "SWITCH_PREVIOUS_TAB",
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
    dono = getattr(fechar, "__self__", None) if callable(fechar) else None
    sugeridas = getattr(dono, "abas_sugeridas", None)
    havia_sugestoes = bool(sugeridas) if isinstance(sugeridas, list) else None
    alvos_sugeridos = (
        [str(item) for item in sugeridas if str(item).strip()]
        if isinstance(sugeridas, list)
        else []
    )
    ok = bool(fechar()) if callable(fechar) else False
    if havia_sugestoes is False:
        deps.marcar_resultado(
            "nenhuma_aba_parada",
            executou=False,
            confirmado=True,
            alvo_resolvido="abas paradas sugeridas",
            params_resolvidos={"abas_sugeridas": [], "quantidade": 0},
            detalhe="a lista canônica de abas sugeridas estava vazia",
        )
        return ResultadoDespacho.concluido()
    deps.marcar_resultado(
        "abas_paradas_fechadas" if ok else "falha_execucao",
        executou=ok,
        confirmado=ok,
        alvo_resolvido="abas paradas sugeridas",
        params_resolvidos={
            "abas_sugeridas": alvos_sugeridos,
            "quantidade": len(alvos_sugeridos),
        },
        detalhe=(
            "o porteiro confirmou o fechamento de cada aba previamente sugerida"
            if ok else
            "ao menos uma aba sugerida não devolveu confirmação de fechamento"
        ),
    )
    return ResultadoDespacho.concluido(ok)


def _normalizar_alvo_aba(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def _id_aba(aba: Dict[str, Any] | None) -> int | None:
    aba = aba if isinstance(aba, dict) else {}
    valor = aba.get("tabId") if isinstance(aba.get("tabId"), int) else aba.get("id")
    return int(valor) if isinstance(valor, int) and not isinstance(valor, bool) else None


def _selecionar_aba_observada(
    abas: list[Dict[str, Any]],
    alvo: str,
) -> Dict[str, Any]:
    alvo_norm = _normalizar_alvo_aba(alvo)
    alvo_compacto = alvo_norm.replace(" ", "")
    if not alvo_norm:
        return {}
    candidatos: list[tuple[int, int, Dict[str, Any]]] = []
    for aba in abas:
        if not isinstance(aba, dict) or _id_aba(aba) is None:
            continue
        titulo = _normalizar_alvo_aba(aba.get("title") or aba.get("titulo"))
        url = str(aba.get("url") or "").strip()
        try:
            host = _normalizar_alvo_aba(urllib.parse.urlsplit(url).hostname or "")
        except (TypeError, ValueError):
            host = ""
        host_compacto = host.replace(" ", "")
        url_norm = _normalizar_alvo_aba(url)

        # P0_NAVEGADOR_ROTULO_CANONICO_ROUNDTRIP_V4_3_20260815
        # O rótulo publicado no contexto ("Título — host") precisa reencontrar
        # a mesma aba antes do fallback textual. Assim preservamos a identidade
        # observada e o fechamento segue por tabId.
        rotulo_canonico = _normalizar_alvo_aba(_rotulo_aba(aba))

        score = 0
        if rotulo_canonico == alvo_norm:
            score = 130
        elif titulo == alvo_norm:
            score = 120
        elif host == alvo_norm or host.endswith(" " + alvo_norm):
            score = 115
        elif alvo_compacto and alvo_compacto in host_compacto:
            score = 105
        elif alvo_norm in titulo:
            score = 95
        elif alvo_norm in url_norm:
            score = 85
        if score:
            candidatos.append((score, 1 if aba.get("active") is True else 0, aba))
    if not candidatos:
        return {}
    candidatos.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return dict(candidatos[0][2])


def _rotulo_aba(aba: Dict[str, Any]) -> str:
    titulo = re.sub(
        r"\s+", " ", str(aba.get("title") or aba.get("titulo") or "").strip()
    )
    url = str(aba.get("url") or "").strip()
    try:
        host = str(urllib.parse.urlsplit(url).hostname or "").removeprefix("www.")
    except (TypeError, ValueError):
        host = ""
    if titulo and host and host.casefold() not in titulo.casefold():
        return f"{titulo} — {host}"
    return titulo or host or "aba sem título"


def _executar_listar_abas(
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    navegador = _get(ctx, "_registro_navegador_leitura_runtime")
    try:
        conectado = bool(navegador is not None and navegador.conectado())
    except Exception as erro:
        relatar_falha_ctx(
            ctx,
            "executor_navegador",
            "falha_consultar_conexao_abas",
            erro=erro,
            impacto="turno",
            fallback="listagem_indisponivel",
            dominio="navegador",
            fase="listar_abas",
        )
        conectado = False
    if not conectado:
        deps.marcar_resultado(
            "navegador_indisponivel", executou=False, confirmado=False,
        )
        _falar(ctx, "Não consegui consultar as abas: a extensão não está conectada.", "calma", 1)
        return ResultadoDespacho.concluido(False)
    try:
        brutas = navegador.listar_abas(timeout_s=5.0) or []
    except Exception as erro:
        relatar_falha_ctx(
            ctx,
            "executor_navegador",
            "falha_listar_abas",
            erro=erro,
            impacto="turno",
            fallback="listagem_indisponivel",
            dominio="navegador",
            fase="listar_abas",
        )
        deps.marcar_resultado(
            "falha_execucao",
            executou=False,
            confirmado=False,
            detalhe="a extensão falhou antes de devolver a lista de abas",
        )
        _falar(
            ctx,
            "Não consegui ler as abas agora; a extensão não devolveu uma lista verificável.",
            "calma",
            1,
        )
        return ResultadoDespacho.concluido(False)
    abas = [dict(aba) for aba in brutas if isinstance(aba, dict)]
    if not abas:
        deps.marcar_resultado(
            "abas_listadas", executou=True, confirmado=True,
            detalhe="a extensão devolveu uma lista vazia",
        )
        _falar(ctx, "A extensão não observou nenhuma aba aberta agora.", "calma", 1)
        return ResultadoDespacho.concluido()
    rotulos = [_rotulo_aba(aba) for aba in abas]
    limite = 12
    fala = "Abas abertas observadas: " + "; ".join(
        f"{indice}. {rotulo}"
        for indice, rotulo in enumerate(rotulos[:limite], start=1)
    )
    if len(rotulos) > limite:
        fala += f"; e mais {len(rotulos) - limite}."
    else:
        # Não encerre a fala num host como ``primevideo.com``: a higiene
        # final trataria ``com.`` como um conector truncado. O total factual
        # também deixa explícito que a lista veio inteira da extensão.
        fala += f"; total de {len(rotulos)} aba(s)."
    deps.marcar_resultado(
        "abas_listadas",
        executou=True,
        confirmado=True,
        detalhe=f"{len(abas)} aba(s) devolvida(s) pela extensão",
    )
    # A lista é evidência observada. Ela não passa por autoria da LLM, que
    # poderia acrescentar abas inexistentes ou retirar títulos relevantes.
    _falar(ctx, fala, "calma", 1)
    return ResultadoDespacho.concluido()


def _executar_aba_anterior(
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    leitura = _get(ctx, "_registro_navegador_leitura_runtime")
    operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    focar = getattr(operacoes, "focar_aba", None)
    try:
        conectado = bool(leitura is not None and leitura.conectado())
    except Exception:
        conectado = False
    if not conectado or not callable(focar):
        deps.marcar_resultado(
            "navegador_indisponivel", executou=False, confirmado=False,
        )
        _falar(
            ctx,
            "Não consegui voltar de aba porque a extensão não está disponível agora.",
            "calma",
            1,
        )
        return ResultadoDespacho.concluido(False)

    try:
        ativa = dict(leitura.aba_ativa(timeout_s=4.0) or {})
        abas = [
            dict(aba) for aba in (leitura.listar_abas(timeout_s=5.0) or [])
            if isinstance(aba, dict)
        ]
    except Exception as erro:
        relatar_falha_ctx(
            ctx,
            "executor_navegador",
            "falha_observar_aba_anterior",
            erro=erro,
            impacto="turno",
            fallback="aba_anterior_indisponivel",
            dominio="navegador",
            fase="aba_anterior",
        )
        deps.marcar_resultado(
            "falha_execucao", executou=False, confirmado=False,
        )
        _falar(ctx, "Não consegui identificar qual era a aba anterior.", "calma", 1)
        return ResultadoDespacho.concluido(False)

    ativa_id = _id_aba(ativa)
    if ativa_id is None:
        ativa_observada = next(
            (aba for aba in abas if aba.get("active") is True),
            {},
        )
        ativa_id = _id_aba(ativa_observada)
    janela_ativa = next(
        (
            aba.get("windowId") for aba in abas
            if _id_aba(aba) == ativa_id and isinstance(aba.get("windowId"), int)
        ),
        None,
    )

    # P0_NAVEGADOR_ANTERIOR_CANONICO_V4_1_20260815
    # A ordem de foco é publicada pelo WebSocket. ``lastAccessed`` continua
    # apenas como fallback para estado legado, inicialização ou aba já fechada.
    obter_anterior = getattr(leitura, "aba_anterior_id", None)
    try:
        anterior_id_canonico = (
            obter_anterior() if callable(obter_anterior) else None
        )
    except Exception:
        anterior_id_canonico = None
    if not (
        isinstance(anterior_id_canonico, int)
        and not isinstance(anterior_id_canonico, bool)
    ):
        anterior_id_canonico = None

    # P0_NAVEGADOR_ANTERIOR_ENTRE_JANELAS_V4_2_20260815
    # ``aba_anterior_id`` é histórico causal de foco do navegador inteiro.
    # Se a ação anterior focou uma aba existente em outra janela, restringir
    # pelo ``windowId`` atual destrói justamente essa evidência e força o
    # fallback heurístico por ``lastAccessed``. O fallback continua limitado à
    # janela atual; apenas o histórico canônico pode atravessar janelas.
    anterior = next(
        (
            aba for aba in abas
            if _id_aba(aba) == anterior_id_canonico
            and anterior_id_canonico != ativa_id
        ),
        {},
    )

    if not anterior:
        candidatos: list[tuple[float, Dict[str, Any]]] = []
        for aba in abas:
            tab_id = _id_aba(aba)
            if tab_id is None or tab_id == ativa_id or aba.get("active") is True:
                continue
            if janela_ativa is not None and aba.get("windowId") != janela_ativa:
                continue
            try:
                recencia = float(aba.get("lastAccessed") or 0.0)
            except (TypeError, ValueError):
                recencia = 0.0
            candidatos.append((recencia, aba))
        if not candidatos:
            deps.marcar_resultado(
                "aba_anterior_indisponivel", executou=False, confirmado=True,
            )
            _falar(
                ctx,
                "Não encontrei outra aba observada para voltar.",
                "calma",
                1,
            )
            return ResultadoDespacho.concluido(False)

        candidatos.sort(key=lambda item: item[0], reverse=True)
        anterior = candidatos[0][1]
    anterior_id = _id_aba(anterior)
    ok = bool(anterior_id is not None and focar(anterior_id))
    confirmado = False
    if ok:
        # O comando e o evento ``active_tab_changed`` atravessam o WebSocket
        # em mensagens diferentes. Uma leitura imediata criava falso negativo
        # mesmo quando o Chrome já tinha aceitado o foco. Relemos por uma
        # janela curta, sem repetir o comando.
        for tentativa in range(6):
            try:
                confirmado = (
                    _id_aba(leitura.aba_ativa(timeout_s=1.0)) == anterior_id
                )
            except Exception:
                confirmado = False
            if confirmado:
                break
            if tentativa < 5:
                time.sleep(0.08)
    rotulo = _rotulo_aba(anterior)
    status = "aba_anterior_focada" if confirmado else "falha_execucao"
    deps.marcar_resultado(
        status,
        executou=ok,
        confirmado=confirmado,
        alvo_resolvido=rotulo,
        detalhe=(
            "a extensão releu a aba como ativa"
            if confirmado else "a extensão não confirmou a troca de aba"
        ),
    )
    _falar(
        ctx,
        f"Voltei para {rotulo}." if confirmado else "Tentei voltar, mas a extensão não confirmou a aba anterior.",
        "calma",
        1,
    )
    return ResultadoDespacho.concluido(confirmado)


def _executar_fechar_aba(
    params: Dict[str, Any],
    texto_original: str,
    destino: str,
    ctx: Dict[str, Any],
    deps: DependenciasExecutorNavegador,
) -> ResultadoDespacho:
    navegador_leitura = _get(ctx, "_registro_navegador_leitura_runtime")
    navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
    enviar_pc_b = _get(ctx, "_enviar_pc_b")

    info = navegador_leitura.aba_ativa() if navegador_leitura is not None else {}
    try:
        abas_observadas = (
            navegador_leitura.listar_abas(timeout_s=5.0)
            if navegador_leitura is not None
            and callable(getattr(navegador_leitura, "listar_abas", None))
            else []
        )
    except Exception:
        abas_observadas = []
    alvo = str(params.get("alvo") or params.get("site") or params.get("nome") or "").strip()
    alvo_preciso = deps.alvo_preciso_para_aba(alvo) if alvo else ""

    # CLOSE_TAB autoriza somente o fechamento de uma aba. O resolvedor de
    # janelas pode enxergar o título da aba dentro do título do navegador e
    # concluir, por engano, que o alvo é um programa aberto. Escalar esse
    # comando para ``fechar_programa`` encerrava o navegador inteiro (por
    # exemplo, "fecha a aba do Prime Video" fechava o Opera). Fechar um app
    # continua sendo responsabilidade exclusiva de CLOSE_APP.

    aba_resolvida: Dict[str, Any] = {}
    confirmacao_resultado: bool | None = False
    remoto_sem_evidencia = False
    ok = False
    if destino == "pc_b" and callable(enviar_pc_b):
        payload = (
            {"action": "close_specific_tab", "target": alvo_preciso or alvo}
            if alvo else {"action": "close_current_tab"}
        )
        retorno_remoto = enviar_pc_b(payload)
        ok = retorno_remoto is not False
        remoto_sem_evidencia = ok
        confirmacao_resultado = None if ok else False
    elif alvo and navegador_operacoes is not None:
        aba_resolvida = _selecionar_aba_observada(
            [dict(aba) for aba in abas_observadas if isinstance(aba, dict)],
            alvo_preciso or alvo,
        ) or _selecionar_aba_observada(
            [dict(aba) for aba in abas_observadas if isinstance(aba, dict)],
            alvo,
        )
        tab_id = _id_aba(aba_resolvida)
        if tab_id is not None:
            ok = bool(navegador_operacoes.fechar_abas([tab_id]))
        else:
            # A extensão antiga ainda pode resolver por título/URL e, após a
            # atualização do protocolo, devolve confirmação real. Não usamos
            # Ctrl+W como fallback: o foco pode ter mudado e fechar outra aba.
            ok = bool(navegador_operacoes.fechar_aba(alvo_preciso or alvo))
        confirmacao_resultado = ok
    elif navegador_operacoes is not None:
        tab_id = _id_aba(info)
        if tab_id is None:
            aba_resolvida = next(
                (
                    dict(aba) for aba in abas_observadas
                    if isinstance(aba, dict) and aba.get("active") is True
                ),
                {},
            )
            tab_id = _id_aba(aba_resolvida)
        else:
            aba_resolvida = dict(info or {})
        ok = (
            bool(navegador_operacoes.fechar_abas([tab_id]))
            if tab_id is not None
            else bool(navegador_operacoes.fechar_aba_atual())
        )
        confirmacao_resultado = ok

    status = (
        "fechamento_aba_solicitado"
        if remoto_sem_evidencia
        else "aba_fechada" if ok else "falha_execucao"
    )
    titulo_resolvido = str(
        aba_resolvida.get("title") or aba_resolvida.get("titulo") or ""
    ).strip()
    alvo_resolvido = titulo_resolvido or alvo or "essa aba"
    params_resolvidos: Dict[str, Any] = {}
    tab_id_resolvido = _id_aba(aba_resolvida)
    if tab_id_resolvido is not None:
        params_resolvidos["tab_id"] = tab_id_resolvido
    if str(aba_resolvida.get("url") or "").strip():
        params_resolvidos["url_aba"] = str(aba_resolvida.get("url") or "").strip()
    if titulo_resolvido:
        params_resolvidos["titulo_aba"] = titulo_resolvido
    deps.marcar_resultado(
        status,
        executou=ok,
        confirmado=confirmacao_resultado,
        alvo_resolvido=alvo_resolvido,
        params_resolvidos=params_resolvidos,
        detalhe=(
            "o cliente remoto recebeu a solicitação, mas não devolveu o estado final da aba"
            if remoto_sem_evidencia else
            "a extensão confirmou a remoção da aba observada"
            if ok else "nenhuma remoção de aba foi confirmada"
        ),
    )
    deps.falar_por_status(
        status,
        "Enviei o pedido para fechar a aba no outro computador; ele não devolveu o estado final."
        if remoto_sem_evidencia else
        "Fechado. Já vai tarde."
        if ok else f"Tentei fechar {alvo or 'essa aba'}, mas não consegui confirmar se ela saiu de cena.",
        alvo=alvo_resolvido,
        executou=ok,
        confirmado=confirmacao_resultado,
    )
    return ResultadoDespacho.concluido(ok)


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
    abrir_resultado = params.get("abrir_resultado")
    if (
        isinstance(abrir_resultado, int)
        and not isinstance(abrir_resultado, bool)
        and abrir_resultado == 1
    ):
        abrir_primeiro = getattr(
            navegador_operacoes, "abrir_primeiro_resultado", None,
        ) if navegador_operacoes is not None else None
        ok = bool(abrir_primeiro(query)) if callable(abrir_primeiro) else False
        status = "resultado_web_aberto" if ok else "falha_execucao"
        deps.marcar_resultado(
            status,
            executou=ok,
            confirmado=ok,
            detalhe=(
                "a extensão selecionou e abriu o primeiro resultado orgânico observado"
                if ok else "a extensão não confirmou um primeiro resultado observável"
            ),
        )
        deps.falar_por_status(
            status,
            (
                f"Abri o primeiro resultado observado da busca por {query}."
                if ok else
                "Não consegui confirmar um primeiro resultado nessa busca."
            ),
            alvo=query,
            executou=ok,
            confirmado=ok,
        )
        return ResultadoDespacho.concluido(ok)
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
            bot_raw = ""
            if callable(enviar_mensagem):
                try:
                    bot_raw = enviar_mensagem(
                        messages,
                        _tipo_chamada="principal",
                        _classe_timeout="normal",
                    )
                except TypeError:
                    # Compatibilidade com portas antigas e dublês mínimos.
                    bot_raw = enviar_mensagem(messages)
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
        enviar_pc_b({"action": "open_url", "url": url, "auto_click": False})
        ok = False  # o cliente remoto não devolve a aba final nesta rota
    else:
        ok = deps.abrir_url_com_validacao(
            url,
            alvo=query,
            auto_click=False,
        )
    status = "busca_aberta" if ok else "falha_execucao"
    fala = escolher_fala_variada([
        f"Abri os resultados da busca por {query}.",
        f"A busca por {query} está aberta.",
        f"Mostrei os resultados de {query}.",
    ]) if ok else f"Não consegui confirmar a busca por {query}."
    deps.marcar_resultado(
        status,
        executou=ok,
        confirmado=ok,
        detalhe=(
            "a página de resultados foi relida no navegador"
            if ok else "a página de resultados não foi observada"
        ),
    )
    deps.falar_por_status(
        status, fala, alvo=query, executou=ok, confirmado=ok,
    )
    if ok and callable(registrar):
        registrar(texto_original, fala, "SEARCH", query, "", "pesquisa")
    return ResultadoDespacho.concluido(ok)


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
    if intent == "LIST_TABS":
        return _executar_listar_abas(ctx, deps)
    if intent == "SWITCH_PREVIOUS_TAB":
        return _executar_aba_anterior(ctx, deps)
    if intent == "CLOSE_TAB":
        return _executar_fechar_aba(params, texto_original, destino, ctx, deps)
    if intent == "SITE_ENTER":
        return _executar_entrar_site(params, texto_original, ctx, deps)
    return _executar_search(params, texto_original, destino, ctx, deps)
