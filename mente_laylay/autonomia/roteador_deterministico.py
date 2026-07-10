"""Detectores determinísticos pequenos e reutilizáveis da Laylay."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict


def preparar_entrada_deterministica(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str],
    texto_conversa_casual_sem_acao: Callable[[str], bool],
    texto_bloqueia_playlist_agora: Callable[[str], bool],
    texto_social_curto: Callable[[str], bool],
    ignorar_token_solto: Callable[[str], bool],
    fluxo_prioritario_da_ia: Callable[[str], bool],
    texto_expresso_melhor_no_deterministico: Callable[[str], bool],
    texto_depende_de_contexto: Callable[[str], bool],
    limpar_destino_pc_b: Callable[[str], str],
) -> Dict[str, Any]:
    """Prepara e filtra a entrada antes da sequencia de detectores determinísticos."""
    bruto = str(texto or "").strip()
    if not bruto:
        return {"status": "ignorar"}

    if callable(texto_conversa_casual_sem_acao) and texto_conversa_casual_sem_acao(bruto):
        return {"status": "ignorar"}
    if callable(texto_bloqueia_playlist_agora) and texto_bloqueia_playlist_agora(bruto):
        return {"status": "intent", "resultado": {"intent": "STOP_PLAYLIST_CONTEXT", "params": {}}}
    if callable(texto_social_curto) and texto_social_curto(bruto):
        return {"status": "ignorar"}

    normalizar = normalizar_texto if callable(normalizar_texto) else (lambda valor: str(valor or "").strip().lower())
    t = normalizar(bruto)
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    if not t:
        return {"status": "ignorar"}
    if callable(ignorar_token_solto) and ignorar_token_solto(t):
        return {"status": "ignorar"}

    if (
        callable(fluxo_prioritario_da_ia)
        and fluxo_prioritario_da_ia(t)
        and not (callable(texto_expresso_melhor_no_deterministico) and texto_expresso_melhor_no_deterministico(t))
    ):
        return {"status": "ignorar"}

    if callable(texto_depende_de_contexto) and texto_depende_de_contexto(t):
        comandos_contextuais = [
            "fecha", "fechar", "mata", "derruba", "cancela", "cancelar",
            "volume", "tela cheia", "fullscreen", "em foco", "abrir", "abre",
            "coloca", "coloque", "salva", "salve", "guarda", "guarde",
            "adiciona", "adicione", "lista", "listar", "mostra", "mostrar",
            "essa tambem", "essa também", "esse tambem", "esse também",
            "apaga", "apagar", "deleta", "deletar", "remove", "remover", "exclui", "excluir",
        ]
        if not any(x in t for x in comandos_contextuais):
            return {"status": "ignorar"}

    limpar_destino = limpar_destino_pc_b if callable(limpar_destino_pc_b) else (lambda valor: str(valor or ""))
    return {
        "status": "ok",
        "bruto": bruto,
        "texto_normalizado": t,
        "texto_sem_destino": limpar_destino(t),
    }


def detectar_volume_ou_midia(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    contexto_musical_ativo: bool = False,
) -> Dict[str, Any] | None:
    """Reconhece volume e controles de mídia sem depender da IA."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if "volume" in t or any(p in t for p in ["mudo", "mute", "sem som", "silencio", "silêncio", "mais alto", "mais baixo"]):
        m_vol = re.search(r"\b(?:volume|som)\s*(?:em|no|para|pra)?\s*(\d{1,3})\s*%?\b", t)
        if m_vol:
            return {"intent": "VOLUME", "params": params(acao="set", nivel_volume=int(m_vol.group(1)))}
        if any(p in t for p in ["mudo", "mute", "sem som", "silencio", "silêncio", "silenciar"]):
            return {"intent": "VOLUME", "params": params(acao="mute")}
        if any(p in t for p in ["aumenta", "aumentar", "sobe", "subir", "mais alto"]):
            return {"intent": "VOLUME", "params": params(acao="up")}
        if any(p in t for p in ["abaixa", "baixa", "baixar", "diminui", "diminuir", "mais baixo"]):
            return {"intent": "VOLUME", "params": params(acao="down")}

    if contexto_musical_ativo and any(x in t for x in ["pausa ela", "pausa ele", "pausa isso", "para ela", "para ele", "para isso"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="pause", platform="music")}
    if contexto_musical_ativo and any(x in t for x in ["despausa ela", "despausa ele", "retoma ela", "retoma ele", "continua ela", "continua ele"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="play", platform="music")}
    if any(x in t for x in ["despausa", "despausar", "retoma a musica", "retoma a música", "continua a musica", "continua a música", "volta a tocar", "continua tocando"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="play")}
    if any(x in t for x in ["pausa", "pause", "pausar", "para a musica", "para música", "para musica", "play pause"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="pause")}
    if ("playlist" not in t) and any(x in t for x in ["proxima musica", "próxima música", "proxima", "próxima", "pula", "proximo", "próximo"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="next")}
    if any(x in t for x in ["volta a musica", "música anterior", "musica anterior", "anterior"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="prev")}

    return None


def detectar_email_notificacao_briefing(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece pedidos diretos de email, notificacao e briefing."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if "email" in t or "emails" in t or "e-mail" in t:
        if any(p in t for p in ["calar a boca", "silencia esse remetente", "silencia a shein", "manda a shein", "manda o remetente", "silenciar esse email", "ignorar esse email", "não me enche"]):
            alvo = ""
            m_alvo = re.search(r"manda a\s+(?P<alvo>[a-z0-9\s]+?)\s+calar a boca", t, flags=re.IGNORECASE)
            if m_alvo:
                alvo = str(m_alvo.group("alvo") or "").strip()
            return {"intent": "NOTIFICATIONS", "params": params(acao="silenciar_remetente", alvo=alvo)}
        if any(p in t for p in ["sincroniza", "sincronizar", "atualiza", "atualizar"]):
            return {"intent": "EMAIL_SYNC", "params": params()}
        if any(p in t for p in ["urgente", "urgentes", "importante", "importantes", "prioritario", "prioritários", "prioritarios"]):
            return {"intent": "EMAIL_READ", "params": params(urgentes=True)}
        if any(p in t for p in ["le", "lê", "ler", "mostra", "ver", "verifica", "checa", "quantos", "fale", "falar", "resuma", "resumo", "me fala", "me fale", "o que eles me falam", "o que falam"]):
            return {"intent": "EMAIL_READ", "params": params()}

    if "briefing" in t and any(p in t for p in ["fala", "fale", "mostra", "mostrar", "repete", "repetir", "diz", "diga", "conta", "contar"]):
        return {"intent": "BRIEFING_REPEAT", "params": params()}

    if "notificacao" in t or "notificacoes" in t or "notificação" in t or "notificações" in t:
        if any(p in t for p in ["silencia", "silenciar", "desativa", "desativar", "mute"]):
            return {"intent": "NOTIFICATIONS", "params": params(acao="silenciar")}
        if any(p in t for p in ["ativa", "ativar", "reativa", "reativar"]):
            return {"intent": "NOTIFICATIONS", "params": params(acao="ativar")}
        if any(p in t for p in ["le", "lê", "ler", "mostra", "ver", "verifica"]):
            return {"intent": "NOTIFICATIONS", "params": params(acao="ler")}

    return None


def detectar_url_visual(
    texto_normalizado: str,
    texto_bruto: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece URLs diretas e pedidos de visão/captura."""
    t = str(texto_normalizado or "").strip()
    bruto = str(texto_bruto or "")
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if any(x in t for x in ["instagram.com/direct", "instagram.com", "www.instagram.com", "instagram direct", "direct/t/"]):
        return {"intent": "OPEN_URL", "params": params(alvo="instagram")}
    if re.search(r"https?://\S+", bruto) and "instagram" in t:
        return {"intent": "OPEN_URL", "params": params(alvo="instagram")}

    if any(p in t for p in [
        "o que voce ve na tela", "o que você vê na tela", "o que ta na tela", "o que tá na tela",
        "olha minha tela", "olha a tela", "ver minha tela", "captura a tela", "tira print",
        "screenshot", "print da tela",
        "guarda esse momento", "salva esse momento", "memoriza isso", "lembra dessa tela",
        "guarda essa tela", "salva essa tela", "faz memoria disso", "faz memória disso",
    ]):
        return {"intent": "SCREEN_CAPTURE", "params": params()}

    return None


def detectar_playlist_contextual_musica_atual(
    texto_sem_destino: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    limpar_nome_playlist: Callable[[str], str],
    ultima_playlist: Any = "",
) -> Dict[str, Any] | None:
    """Reconhece salvar a musica atual em playlist e continuacoes como 'essa tambem'."""
    t = str(texto_sem_destino or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    limpar_nome = limpar_nome_playlist if callable(limpar_nome_playlist) else (lambda valor: str(valor or "").strip())

    m_add_musica_playlist = re.search(
        r"\b(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b"
        r".{0,60}?\b(?:essa|esta|a)?\s*(?:musica|música|faixa|canção|cancao)?\b"
        r".{0,30}?\b(?:na|nessa|nesta|para a|pra|em)\s+playlist\s+(?P<nome>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_add_musica_playlist:
        pl = limpar_nome(m_add_musica_playlist.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_ADD", "params": params(nome_playlist=pl)}

    if re.fullmatch(r"(essa|esta|isso|essa aqui|esta aqui)\s+(tambem|também)", t, flags=re.IGNORECASE):
        ultima_pl = str(ultima_playlist or "").strip()
        if ultima_pl:
            return {
                "intent": "PLAYLIST_ADD",
                "params": params(nome_playlist=ultima_pl, referencia_contextual=True),
            }

    return None


def detectar_confirmacao_porteiro(
    texto_sem_destino: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    ha_abas_sugeridas: bool = False,
) -> Dict[str, Any] | None:
    """Confirma a limpeza de abas sugeridas pelo Porteiro do navegador."""
    if not ha_abas_sugeridas:
        return None
    t = str(texto_sem_destino or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if re.fullmatch(
        r"(sim|pode|pode fechar|fecha|fecha as abas|limpa|limpa as abas|vai la|vai lá|faz o que sugeriu|manda ver)",
        t,
        flags=re.IGNORECASE,
    ):
        return {"intent": "CLOSE_IDLE_TABS", "params": params()}

    return None


def detectar_playlist_laylay(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    limpar_nome_playlist: Callable[[str], str],
) -> Dict[str, Any] | None:
    """Reconhece comandos sobre as playlists próprias da Laylay."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    limpar_nome = limpar_nome_playlist if callable(limpar_nome_playlist) else (lambda valor: str(valor or "").strip())

    if not any(x in t for x in [
        "sua playlist",
        "suas playlists",
        "playlist da laylay",
        "playlists da laylay",
        "playlist dela",
        "playlists dela",
    ]):
        return None

    m_copy = re.search(
        r"(?:coloca|bota|adiciona|salva|guarda)\s+(?P<musica>.+?)\s+da\s+(?:sua|da\s+laylay|dela)\s+playlist\s+(?P<origem>.+?)\s+(?:na|minha|para a|pra)\s+playlist\s+(?P<destino>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_copy:
        return {
            "intent": "LAYLAY_PLAYLIST_COPY",
            "params": params(
                musica=str(m_copy.group("musica") or "").strip(),
                origem=limpar_nome(m_copy.group("origem") or ""),
                destino=limpar_nome(m_copy.group("destino") or ""),
            ),
        }

    m_nome = re.search(r"playlist\s+(?P<nome>[a-z0-9\s_]+)$", t, flags=re.IGNORECASE)
    return {
        "intent": "LAYLAY_PLAYLIST_LIST",
        "params": params(nome_playlist=limpar_nome(m_nome.group("nome") if m_nome else "")),
    }


def detectar_playlist_usuario(
    texto_normalizado: str,
    texto_bruto: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
    limpar_nome_playlist: Callable[[str], str],
    extrair_nome_playlist: Callable[[str], str],
) -> Dict[str, Any] | None:
    """Reconhece comandos diretos sobre playlists salvas do Pedro."""
    t = str(texto_normalizado or "").strip()
    bruto = str(texto_bruto or "")
    if "playlist" not in t:
        return None

    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    limpar_nome = limpar_nome_playlist if callable(limpar_nome_playlist) else (lambda valor: str(valor or "").strip())
    extrair_nome = extrair_nome_playlist if callable(extrair_nome_playlist) else (lambda valor: "")

    m_delete = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir|tira|tirar)\s+"
        r"(?:a|o|uma|um)?\s*playlist\s+(?:chamada|com nome|de nome)?\s*(?P<nome>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_delete:
        pl = limpar_nome(m_delete.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_DELETE", "params": params(nome_playlist=pl)}

    m_create_add = re.search(
        r"\b(?:cria|criar|crie)\s+(?:uma\s+)?playlist\s+(?:chamada|com nome|de nome)?\s*(?P<nome>.+?)\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b.*$",
        t,
        flags=re.IGNORECASE,
    )
    if m_create_add:
        pl = limpar_nome(m_create_add.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_ADD", "params": params(nome_playlist=pl)}

    if re.search(r"\b(quais|lista|listar|mostra|mostrar|mostre|fale|falar|diga|dizer|o que tem|oque tem)\b", t):
        pl = extrair_nome(bruto)
        if not pl:
            m = re.search(r"playlist\s+(.+)$", t)
            pl = limpar_nome(m.group(1) if m else "")
        return {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}

    quer_salvar = (
        re.search(r"\b(coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b", t)
        and re.search(r"\b(na|nessa|nesta|para a|pra)\s+playlist\b", t)
    )
    if quer_salvar:
        pl = extrair_nome(bruto)
        return {"intent": "PLAYLIST_ADD", "params": params(nome_playlist=pl)}

    quer_tocar = re.search(r"\b(toca|toque|coloca|coloque|abre|abra|ouvir|escuta|escute)\b", t)
    if quer_tocar:
        m = re.search(r"playlist\s+(.+)$", t)
        pl = limpar_nome(m.group(1) if m else "")
        if pl:
            return {"intent": "PLAYLIST_PLAY", "params": params(nome_playlist=pl)}

    return None


def detectar_organizacao_desktop(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece o pedido direto de organizar janelas/area de trabalho."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if any(v in t for v in ["organiza", "organizar", "arruma", "arrumar"]) and any(
        alvo in t for alvo in ["area de trabalho", "área de trabalho", "desktop", "tela", "janelas", "janela"]
    ):
        return {"intent": "ORGANIZAR_DESKTOP", "params": params(left="vscode", right="opera")}

    return None


def detectar_janela_contextual(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    estado_mental: Dict[str, Any] | None = None,
    texto_depende_de_contexto: Callable[[str], bool] | None = None,
) -> Dict[str, Any] | None:
    """Resolve comandos de janela que dependem do ultimo app citado."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    depende_contexto = texto_depende_de_contexto if callable(texto_depende_de_contexto) else (lambda valor: False)

    referencia_janela_contextual = (
        bool(depende_contexto(t))
        or any(v in t for v in ["ele", "ela", "isso"])
    )
    if not referencia_janela_contextual:
        return None
    if not any(v in t for v in ["foco", "na frente", "pra frente", "para frente", "tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return None

    estado = dict(estado_mental or {})
    ultima_intencao_ctx = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultimo_app = str(estado.get("ultimo_app_janela") or "").strip()
    if not ultimo_app and ultima_intencao_ctx in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        ultimos_params = estado.get("ultima_acao_params") if isinstance(estado.get("ultima_acao_params"), dict) else {}
        ultimo_app = str(
            ultimos_params.get("nome_app")
            or ultimos_params.get("app")
            or estado.get("ultimo_alvo")
            or ""
        ).strip()

    if not ultimo_app:
        return None
    if any(v in t for v in ["tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return {"intent": "MAXIMIZE_WINDOW", "params": params(nome_app=ultimo_app)}
    return {"intent": "APP_OPEN", "params": params(nome_app=ultimo_app, modo="focus")}


def detectar_janela_explicita(
    texto_normalizado: str,
    texto_sem_destino: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece foco/maximizacao quando o app aparece explicitamente na frase."""
    t = str(texto_normalizado or "").strip()
    base = str(texto_sem_destino or t).strip()
    if not t or not base:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    m_max_posposto = re.search(
        r"\b(?:coloca|coloque|bota|deixa|poe|põe)\s+(?:o|a|os|as)?\s*(?P<app>.+?)\s+(?:em|no|na)\s+(?P<modo>tela cheia|fullscreen|full screen|foco|primeiro plano)$",
        base,
        flags=re.IGNORECASE,
    )
    if m_max_posposto:
        app = str(m_max_posposto.group("app") or "").strip()
        modo_txt = str(m_max_posposto.group("modo") or "").strip().lower()
        app = app.replace("pra frente", "").replace("para frente", "").strip()
        if app:
            if modo_txt in {"tela cheia", "fullscreen", "full screen"}:
                return {"intent": "MAXIMIZE_WINDOW", "params": params(nome_app=app)}
            return {"intent": "APP_OPEN", "params": params(nome_app=app, modo="focus")}

    m_max = re.search(r"\b(maximiza|maximizar|tela cheia|fullscreen|coloca em foco|bota em foco|deixa em foco|traz)\s+(?:o|a)?\s*(.+)$", base)
    if m_max:
        app = re.sub(r"^(o|a|os|as|um|uma)\s+", "", (m_max.group(2) or "").strip())
        app = app.replace("em foco", "").replace("pra frente", "").replace("para frente", "").strip()
        if app:
            modo = "fullscreen" if any(p in t for p in ["tela cheia", "fullscreen"]) else "focus"
            if modo == "fullscreen":
                return {"intent": "MAXIMIZE_WINDOW", "params": params(nome_app=app)}
            return {"intent": "APP_OPEN", "params": params(nome_app=app, modo="focus")}

    return None


def detectar_abrir_app_ou_site(
    texto_bruto: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    extrair_intencao_abrir_app: Callable[[str], Dict[str, Any] | None],
) -> Dict[str, Any] | None:
    """Adapta a extracao existente de abrir app/site para o roteador modular."""
    bruto = str(texto_bruto or "").strip()
    if not bruto:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    extrair = extrair_intencao_abrir_app if callable(extrair_intencao_abrir_app) else (lambda valor: None)

    intent_abrir = extrair(bruto)
    if not intent_abrir:
        return None
    if intent_abrir.get("intent") == "OPEN_URL":
        return {"intent": "OPEN_URL", "params": params(**intent_abrir.get("params", {}))}

    nome_app = str(intent_abrir.get("params", {}).get("nome_app") or "").strip()
    if nome_app:
        return {"intent": "APP_OPEN", "params": params(nome_app=nome_app)}

    return None


def detectar_fechar_alvo(
    texto_sem_destino: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    sites_diretos: Any,
    apps_map: Any,
) -> Dict[str, Any] | None:
    """Reconhece pedidos de fechar aba, site, janela, programa ou app."""
    base = str(texto_sem_destino or "").strip()
    if not base:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    sites = sites_diretos if sites_diretos is not None else set()
    apps = apps_map if apps_map is not None else {}

    m_close = re.search(r"\b(fecha|fechar|mata|derruba|encerra|encerrar)\s+(?:o|a|os|as|um|uma|essa|esse)?\s*(.+)$", base)
    if not m_close:
        return None

    alvo = re.sub(r"^(aba|site|janela|programa|app|aplicativo)\s+(do|da|de)?\s*", "", (m_close.group(2) or "").strip()).strip()
    alvo = re.sub(r"^(o|a|os|as|um|uma)\s+", "", alvo).strip()
    if not alvo or alvo in {"aba", "essa aba", "site", "janela"}:
        return {"intent": "CLOSE_TAB", "params": params()}

    alvo_norm = alvo.lower()
    if "aba" in base or "site" in base or alvo_norm in sites or alvo_norm in {"youtube", "netflix", "google", "spotify", "whatsapp", "chatgpt"}:
        return {"intent": "CLOSE_TAB", "params": params(alvo=alvo)}

    for app in sorted(apps.keys(), key=len, reverse=True):
        if alvo_norm == app or app in alvo_norm:
            return {"intent": "CLOSE_APP", "params": params(nome_app=app)}

    return {"intent": "CLOSE_APP", "params": params(nome_app=alvo)}


def detectar_web_e_youtube(
    texto_normalizado: str,
    texto_sem_destino: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
    sites_diretos: Any,
) -> Dict[str, Any] | None:
    """Reconhece pesquisa web, abertura de site e comandos diretos de YouTube."""
    t = str(texto_normalizado or "").strip()
    base = str(texto_sem_destino or t).strip()
    if not t or not base:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    sites = sites_diretos if sites_diretos is not None else set()

    m_google = re.search(r"\b(pesquisa|pesquisar|busca|buscar|procura|procurar)\s+(?:no google\s+)?(?:sobre\s+)?(.+)$", base)
    if m_google and "youtube" not in t:
        query = (m_google.group(2) or "").strip()
        if query:
            return {"intent": "SEARCH", "params": params(query=query, engine="google")}

    m_site = re.search(r"\b(entra|entrar|abre|abra|abrir|vai)\s+(?:no|na|em|para|pra)?\s*(?:site\s+)?(.+)$", base)
    if m_site:
        alvo = re.sub(r"^(o|a|os|as|um|uma)\s+", "", (m_site.group(2) or "").strip()).strip()
        alvo_norm = alvo.lower()
        if alvo_norm in sites or "." in alvo_norm or alvo_norm.startswith(("http://", "https://")):
            return {"intent": "OPEN_URL", "params": params(alvo=alvo)}

    if "youtube" in t:
        m_yt = re.search(r"(?:procura|pesquisa|busca|buscar|coloca|toca|toque)\s+(.*?)\s+(?:no|na)\s+youtube", t)
        if m_yt and m_yt.group(1).strip():
            return {"intent": "MUSIC_SEARCH", "params": params(query=m_yt.group(1).strip())}
        if any(p in t for p in ["abre", "abrir", "entra", "entrar"]):
            return {"intent": "OPEN_URL", "params": params(alvo="youtube")}

    return None


def detectar_musica_ou_playlist_direta(
    texto_normalizado: str,
    texto_sem_destino: str = "",
    texto_bruto: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
    detectar_playlist_nome_direto: Callable[[str], str],
    normalizar_query_musical: Callable[[str], str],
) -> Dict[str, Any] | None:
    """Resolve comandos diretos de tocar música ou playlist pelo nome."""
    t = str(texto_normalizado or "").strip()
    base = str(texto_sem_destino or t).strip()
    bruto = str(texto_bruto or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    detectar_playlist = detectar_playlist_nome_direto if callable(detectar_playlist_nome_direto) else (lambda valor: "")
    normalizar_musica = normalizar_query_musical if callable(normalizar_query_musical) else (lambda valor: str(valor or "").strip())

    if re.match(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b", t):
        if any(x in t for x in ["música", "musica", "youtube", "no youtube", "no yt", "no you tube"]):
            q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b\s*", "", t).strip()
            q = re.sub(r"^(a|o|as|os|uma|um|essa|esse|essa música|essa musica|essa canção|essa cancao)\s+", "", q).strip()
            if q:
                return {"intent": "MUSIC_SEARCH", "params": params(query=q)}

        pl_direta = detectar_playlist(bruto)
        if pl_direta:
            if any(x in t for x in ["playlist", "lista", "listar", "quais", "mostra", "o que tem", "oque tem"]):
                return {"intent": "PLAYLIST_LIST", "params": params(nome_playlist=pl_direta)}
            return {"intent": "PLAYLIST_PLAY", "params": params(nome_playlist=pl_direta)}

        if not any(x in t for x in ["playlist", "música", "musica", "youtube", "yt"]):
            q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b\s*", "", t).strip()
            q = re.sub(r"^(a|o|as|os|uma|um|essa|esse)\s+", "", q).strip()
            if q:
                return {"intent": "MUSIC_SEARCH", "params": params(query=q)}

    pl_direta = detectar_playlist(bruto)
    if pl_direta and not any(x in t for x in ["música", "musica", "youtube", "yt"]):
        if any(x in t for x in ["playlist", "lista", "listar", "quais", "mostra", "o que tem", "oque tem"]):
            return {"intent": "PLAYLIST_LIST", "params": params(nome_playlist=pl_direta)}
        return {"intent": "PLAYLIST_PLAY", "params": params(nome_playlist=pl_direta)}

    if re.match(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute)\b", t) and "playlist" not in t:
        q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute)\b", " ", base).strip()
        q = re.sub(r"^(a|o|uma|um)\s+", "", q).strip()
        q = q.replace("música", " ").replace("musica", " ").replace("no youtube", " ").replace("na youtube", " ")
        q = re.sub(r"\s+", " ", q).strip()
        q = normalizar_musica(q)
        if q and q not in {"playlist"}:
            return {"intent": "MUSIC_SEARCH", "params": params(query=q)}

    return None


def detectar_trava_pc(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece pedidos explicitos para bloquear/travar o computador."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if any(p in t for p in ["trava o pc", "travar o pc", "bloqueia o pc", "lock pc", "bloquear computador"]):
        return {"intent": "LOCK_PC", "params": params()}

    return None
