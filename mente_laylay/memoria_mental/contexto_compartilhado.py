"""Funcoes de contexto compartilhado entre as habilidades da Laylay."""

from __future__ import annotations

import time
import re
from typing import Any, Dict


def estado_mental_inicial() -> Dict[str, Any]:
    return {
        "ultima_entrada": "",
        "ultimas_entradas": [],
        "ultima_intencao": "",
        "ultimo_alvo": "",
        "ultimo_app_janela": "",
        "ultimo_site_aba": "",
        "ultima_pasta": "",
        "ultimo_arquivo": "",
        "ultimo_caminho_arquivo": "",
        "ultima_estrutura_arquivo_params": {},
        "ultima_estrutura_arquivo_ts": 0.0,
        "ultimo_escopo": "",
        "ultima_habilidade": "",
        "ultima_resposta": "",
        "ultima_acao_status": "",
        "ultima_acao_reexecutavel": False,
        "ultima_acao_intent": "",
        "ultima_acao_params": {},
        "ultima_acao_origem": "",
        "ultima_acao_texto": "",
        "ultima_promessa_tipo": "",
        "ultima_promessa_texto": "",
        "ultima_promessa_alvo": "",
        "ultima_promessa_ts": 0.0,
        "alvo_corrigido": "",
        "alvo_corrigido_ts": 0.0,
        "pergunta_aberta_texto": "",
        "pergunta_aberta_topico": "",
        "pergunta_aberta_origem": "",
        "pergunta_aberta_ts": 0.0,
        "foco_vivo_tipo": "",
        "foco_vivo_alvo": "",
        "foco_vivo_topico": "",
        "foco_vivo_habilidade": "",
        "foco_vivo_intencao": "",
        "foco_vivo_texto": "",
        "foco_vivo_resposta": "",
        "foco_vivo_ts": 0.0,
        "ts": 0.0,
    }


def texto_parece_pergunta_aberta(texto: str) -> bool:
    """Detecta perguntas que esperam uma resposta curta do Pedro."""
    fala = str(texto or "").strip()
    if not fala or "?" not in fala:
        return False

    fala_low = fala.lower()
    bloqueios = [
        "quer que eu explique",
        "quer que eu repita",
        "quer que eu abra",
    ]
    # Mesmo esses casos ainda sao perguntas, mas costumam ter feedback proprio.
    if any(b in fala_low for b in bloqueios):
        return False

    sinais = [
        "quer",
        "pode",
        "prefere",
        "qual",
        "quais",
        "quando",
        "onde",
        "como",
        "por que",
        "porque",
        "o que",
        "e voce",
        "e você",
        "como voce",
        "como você",
        "voce esta",
        "você está",
        "ta bem",
        "tá bem",
        "tudo bem",
        "tudo na paz",
    ]
    return any(s in fala_low for s in sinais)


def registrar_pergunta_aberta(
    estado_atual: Dict[str, Any] | None,
    pergunta: str,
    *,
    topico: str = "",
    origem: str = "",
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    pergunta_limpa = str(pergunta or "").strip()
    if not texto_parece_pergunta_aberta(pergunta_limpa):
        return limpar_pergunta_aberta(estado)

    estado["pergunta_aberta_texto"] = pergunta_limpa[:240]
    estado["pergunta_aberta_topico"] = str(topico or "").strip()[:120]
    estado["pergunta_aberta_origem"] = str(origem or "").strip()[:80]
    estado["pergunta_aberta_ts"] = time.time()
    return estado


def limpar_pergunta_aberta(estado_atual: Dict[str, Any] | None) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["pergunta_aberta_texto"] = ""
    estado["pergunta_aberta_topico"] = ""
    estado["pergunta_aberta_origem"] = ""
    estado["pergunta_aberta_ts"] = 0.0
    return estado


def registrar_promessa_conversacional(
    estado_atual: Dict[str, Any] | None,
    resposta: str,
    *,
    alvo: str = "",
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    fala = str(resposta or "").strip()
    base = fala.lower()
    tipo = ""
    if any(p in base for p in [
        "quer que eu abra minha opinião",
        "quer que eu abrir minha opinião",
        "quer que eu abra melhor",
        "quer que eu explique",
        "quer que eu detalhe",
        "posso explicar melhor",
        "posso abrir minha opinião",
    ]):
        tipo = "explicar_opiniao"
    elif any(p in base for p in [
        "quer que eu te explique",
        "quer que eu explique melhor",
        "quer que eu detalhe isso",
        "posso te explicar",
    ]):
        tipo = "explicar"

    if not tipo:
        return estado

    estado["ultima_promessa_tipo"] = tipo
    estado["ultima_promessa_texto"] = fala[:240]
    estado["ultima_promessa_alvo"] = str(alvo or estado.get("ultimo_alvo") or "").strip()[:160]
    estado["ultima_promessa_ts"] = time.time()
    return estado


def limpar_promessa_conversacional(estado_atual: Dict[str, Any] | None) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["ultima_promessa_tipo"] = ""
    estado["ultima_promessa_texto"] = ""
    estado["ultima_promessa_alvo"] = ""
    estado["ultima_promessa_ts"] = 0.0
    return estado


def promessa_conversacional_ativa(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 180.0,
) -> Dict[str, Any] | None:
    estado = dict(estado_atual or {})
    tipo = str(estado.get("ultima_promessa_tipo") or "").strip()
    if not tipo:
        return None
    try:
        ts = float(estado.get("ultima_promessa_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return None
    return {
        "tipo": tipo,
        "texto": str(estado.get("ultima_promessa_texto") or "").strip(),
        "alvo": str(estado.get("ultima_promessa_alvo") or "").strip(),
        "idade_s": max(0.0, time.time() - ts),
    }


def registrar_alvo_corrigido(estado_atual: Dict[str, Any] | None, alvo: str) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["alvo_corrigido"] = str(alvo or "").strip()[:160]
    estado["alvo_corrigido_ts"] = time.time()
    return estado


def alvo_corrigido_ativo(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 120.0,
) -> str:
    estado = dict(estado_atual or {})
    alvo = str(estado.get("alvo_corrigido") or "").strip()
    if not alvo:
        return ""
    try:
        ts = float(estado.get("alvo_corrigido_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return ""
    return alvo


def registrar_estrutura_arquivo_recente(
    estado_atual: Dict[str, Any] | None,
    params: Dict[str, Any] | None,
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    dados = dict(params or {}) if isinstance(params, dict) else {}
    estado["ultima_estrutura_arquivo_params"] = dados
    estado["ultima_estrutura_arquivo_ts"] = time.time() if dados else 0.0
    return estado


def estrutura_arquivo_recente(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 900.0,
) -> Dict[str, Any] | None:
    estado = dict(estado_atual or {})
    dados = estado.get("ultima_estrutura_arquivo_params")
    if not isinstance(dados, dict) or not dados:
        return None
    try:
        ts = float(estado.get("ultima_estrutura_arquivo_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return None
    return dict(dados)


def pergunta_aberta_ativa(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 120.0,
) -> Dict[str, Any] | None:
    estado = dict(estado_atual or {})
    pergunta = str(estado.get("pergunta_aberta_texto") or "").strip()
    if not pergunta:
        return None
    try:
        ts = float(estado.get("pergunta_aberta_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return None
    return {
        "pergunta": pergunta,
        "topico": str(estado.get("pergunta_aberta_topico") or "").strip(),
        "origem": str(estado.get("pergunta_aberta_origem") or "").strip(),
        "idade_s": max(0.0, time.time() - ts),
    }


def texto_parece_resposta_curta_a_pergunta(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(str(texto or ""))
    if not t:
        return False
    palavras = t.split()
    if len(palavras) > 12:
        return False
    if "?" in str(texto or ""):
        return False
    sinais_comando = [
        "abre", "abrir", "abra", "entra", "entrar", "fecha", "fechar",
        "coloca", "colocar", "toca", "tocar", "playlist", "musica", "música",
        "volume", "spotify", "youtube", "netflix",
        "cria", "criar", "apaga", "apagar", "move", "mover", "email",
        "le ", "lê ", "ler ", "site", "aba", "janela", "foco",
        "pausa", "pause", "despausa", "retoma", "continua", "próxima", "proxima",
        "anterior", "maximiza", "maximizar", "tela cheia", "fullscreen",
    ]
    if any(s in f" {t} " for s in sinais_comando):
        return False
    return True


def intencao_reexecutavel(intent: str) -> bool:
    return str(intent or "").upper().strip() in {
        "APP_OPEN",
        "CLOSE_APP",
        "OPEN_URL",
        "CLOSE_TAB",
        "PLAYLIST_PLAY",
        "MUSIC_SEARCH",
        "VOLUME",
        "MEDIA_CONTROL",
        "WEATHER",
        "EMAIL_READ",
        "EMAIL_SYNC",
        "NOTIFICATIONS",
        "BRIEFING_REPEAT",
        "SITE_ENTER",
        "LAYLAY_PLAYLIST_LIST",
        "PLAYLIST_LIST",
    }


def registrar_resultado_execucao(
    estado_atual: Dict[str, Any] | None,
    resultado: Dict[str, Any] | None = None,
    texto: str = "",
    executou: bool = True,
    *,
    origem: str = "",
    status: str = "",
) -> Dict[str, Any]:
    if not isinstance(resultado, dict):
        return dict(estado_atual or {})

    estado = dict(estado_atual or {})
    intent = str(resultado.get("intent") or resultado.get("acao") or "").strip().upper()
    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
    status_final = str(status or "").strip().lower()
    texto_curto = str(texto or "").strip()[:200]

    if not status_final:
        mesmo_intent = str(estado.get("ultima_acao_intent") or "").strip().upper() == intent
        mesmo_texto = str(estado.get("ultima_acao_texto") or "").strip() == texto_curto
        status_anterior = str(estado.get("ultima_acao_status") or "").strip().lower()
        if mesmo_intent and mesmo_texto and status_anterior:
            status_final = status_anterior
        else:
            status_final = "executado" if executou else "falhou"

    estado["ultima_acao_status"] = status_final
    estado["ultima_acao_reexecutavel"] = bool(intencao_reexecutavel(intent))
    estado["ultima_acao_intent"] = intent
    estado["ultima_acao_params"] = dict(params)
    estado["ultima_acao_origem"] = str(origem or "").strip()
    estado["ultima_acao_texto"] = texto_curto
    estado["ts"] = time.time()
    return estado


def enriquecer_resultado_execucao_contextual(
    estado_atual: Dict[str, Any] | None,
    resultado: Dict[str, Any] | None,
    texto: str = "",
    executou: bool = True,
    *,
    status: str = "",
    normalizar_texto_cb=None,
    atualizar_foco_vivo_cb=None,
) -> Dict[str, Any]:
    """Atualiza alvos recentes e foco vivo depois de uma ação prática."""
    estado = dict(estado_atual or {})
    if not executou or not isinstance(resultado, dict):
        return estado

    try:
        intent = str(resultado.get("intent") or resultado.get("acao") or "").strip().upper()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        apps_sem_janela_contextual = {
            "microsoft store",
            "store",
            "ms store",
            "loja microsoft",
            "loja",
        }

        def normalizar(valor: str) -> str:
            if callable(normalizar_texto_cb):
                return normalizar_texto_cb(valor)
            return str(valor or "").strip().lower()

        if intent in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
            app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
            if app and normalizar(app) not in apps_sem_janela_contextual:
                estado["ultimo_app_janela"] = app
                estado["ultimo_alvo"] = app
            elif app:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = app
                estado["ultimo_alvo"] = app
        elif intent in {"OPEN_URL", "CLOSE_TAB"}:
            alvo_web = str(params.get("alvo") or params.get("url") or params.get("nome_app") or "").strip()
            if alvo_web:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = alvo_web
        elif intent == "MEDIA_CONTROL":
            estado["ultima_habilidade"] = "midia"
            estado["ultimo_alvo"] = str(params.get("platform") or params.get("acao") or "musica").strip() or "musica"
            estado["ultimo_escopo"] = str(params.get("platform") or "music").strip()
        elif intent == "PLAYLIST_ADD":
            playlist = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
            if playlist:
                estado["ultimo_alvo"] = playlist
                estado["ultima_habilidade"] = "playlist"
                estado["ultimo_escopo"] = "playlist"

        alvo_foco = str(
            params.get("alvo")
            or params.get("nome_app")
            or params.get("nome_playlist")
            or params.get("query")
            or params.get("nome")
            or params.get("arquivo_nome")
            or params.get("item")
            or estado.get("ultimo_alvo")
            or ""
        ).strip()
        habilidade_foco = {
            "APP_OPEN": "janela",
            "CLOSE_APP": "janela",
            "MAXIMIZE_WINDOW": "janela",
            "OPEN_URL": "site",
            "CLOSE_TAB": "site",
            "SITE_ENTER": "site",
            "SEARCH": "pesquisa",
            "WEATHER": "clima",
            "PLAYLIST_PLAY": "playlist",
            "PLAYLIST_ADD": "playlist",
            "PLAYLIST_LIST": "playlist",
            "MUSIC_SEARCH": "musica",
            "MEDIA_CONTROL": "midia",
            "CREATE_FOLDER": "arquivos",
            "DELETE_ITEM": "arquivos",
            "EMAIL_READ": "email",
            "EMAIL_SYNC": "email",
            "AGENDAR_LEMBRETE": "agenda",
            "LISTAR_AGENDAMENTOS": "agenda",
            "BRIEFING_REPEAT": "conversa",
        }.get(intent, str(estado.get("ultima_habilidade") or "").strip())

        if callable(atualizar_foco_vivo_cb):
            estado = atualizar_foco_vivo_cb(
                estado,
                texto=texto,
                resposta=status or ("executado" if executou else "falhou"),
                intencao=intent,
                alvo=alvo_foco,
                habilidade=habilidade_foco,
            )
    except Exception:
        return estado

    return estado


def registrar_mente_curta(
    estado_atual: Dict[str, Any] | None,
    *,
    texto_usuario: str = "",
    resposta_ia: str = "",
    intencao: str = "",
    alvo: str = "",
    escopo: str = "",
    habilidade: str = "",
    ultimo_topico_conversa: str = "",
    normalizar_texto_cb=None,
    eh_alvo_site_web_cb=None,
    texto_parece_pergunta_aberta_cb=None,
    registrar_pergunta_aberta_cb=None,
    limpar_pergunta_aberta_cb=None,
    registrar_promessa_conversacional_cb=None,
    atualizar_foco_vivo_cb=None,
    log: Any = print,
) -> Dict[str, Any]:
    """Registra entrada/resposta recentes sem isolar a mente dos callbacks centrais."""
    try:
        estado = dict(estado_atual or {})
    except Exception:
        estado = {}

    texto_usuario = str(texto_usuario or "").strip()
    resposta_ia = str(resposta_ia or "").strip()
    intencao = str(intencao or "").strip()
    alvo = str(alvo or "").strip()
    escopo = str(escopo or "").strip()
    habilidade = str(habilidade or "").strip()

    if texto_usuario:
        estado["ultima_entrada"] = texto_usuario
        entradas = list(estado.get("ultimas_entradas") or [])
        entradas.append(texto_usuario[:160])
        estado["ultimas_entradas"] = entradas[-8:]
    if resposta_ia:
        estado["ultima_resposta"] = resposta_ia[:180]
        try:
            if callable(texto_parece_pergunta_aberta_cb) and texto_parece_pergunta_aberta_cb(resposta_ia):
                if callable(registrar_pergunta_aberta_cb):
                    estado = registrar_pergunta_aberta_cb(
                        estado,
                        resposta_ia,
                        topico=alvo or habilidade or intencao or ultimo_topico_conversa,
                        origem=habilidade or intencao or "conversa",
                    )
                    log(f"🧠 [PERGUNTA ABERTA] registrada: {estado.get('pergunta_aberta_texto', '')[:90]}")
            elif callable(limpar_pergunta_aberta_cb):
                estado = limpar_pergunta_aberta_cb(estado)
        except Exception as e:
            log(f"⚠️ [PERGUNTA ABERTA] falha ao atualizar memória: {e}")
        try:
            if callable(registrar_promessa_conversacional_cb):
                estado = registrar_promessa_conversacional_cb(
                    estado,
                    resposta_ia,
                    alvo=alvo or estado.get("ultimo_alvo") or "",
                )
        except Exception as e:
            log(f"⚠️ [PROMESSA] falha ao registrar promessa conversacional: {e}")
    if intencao:
        estado["ultima_intencao"] = intencao
    if alvo:
        estado["ultimo_alvo"] = alvo
        alvo_norm = normalizar_texto_cb(alvo) if callable(normalizar_texto_cb) else alvo.lower()
        if any(x in alvo_norm for x in ["steam", "opera", "chrome", "edge", "vscode", "vs code", "visual studio code"]):
            estado["ultimo_app_janela"] = alvo
        if callable(eh_alvo_site_web_cb) and eh_alvo_site_web_cb(alvo_norm):
            estado["ultimo_site_aba"] = alvo
        if habilidade.lower() in {"arquivo", "arquivos", "sistema"} or intencao.upper() in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"}:
            alvo_limpo = str(alvo or "").strip()
            if alvo_limpo:
                import os
                if "." in os.path.basename(alvo_limpo):
                    estado["ultimo_arquivo"] = os.path.basename(alvo_limpo)
                    estado["ultimo_caminho_arquivo"] = alvo_limpo
                else:
                    estado["ultima_pasta"] = alvo_limpo
    if escopo:
        estado["ultimo_escopo"] = escopo
    if habilidade:
        estado["ultima_habilidade"] = habilidade
    if callable(atualizar_foco_vivo_cb):
        estado = atualizar_foco_vivo_cb(
            estado,
            texto=texto_usuario,
            resposta=resposta_ia,
            intencao=intencao,
            alvo=alvo,
            habilidade=habilidade,
            escopo=escopo,
        )
    estado["ts"] = time.time()
    return estado


def extrair_refino_contexto_mental(texto: str, resultado: Dict[str, Any] | None = None) -> Dict[str, str]:
    """Extrai campos curtos para refinar a memória mental compartilhada."""
    txt = str(texto or "").strip()
    dados = {
        "texto": txt,
        "intencao": "",
        "alvo": "",
        "escopo": "",
        "habilidade": "",
    }
    if not txt:
        return dados
    if isinstance(resultado, dict):
        dados["intencao"] = str(resultado.get("intent") or resultado.get("acao") or "").strip()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        dados["alvo"] = str(
            params.get("nome_playlist")
            or params.get("nome_app")
            or params.get("query")
            or params.get("url")
            or params.get("alvo")
            or ""
        ).strip()
        dados["escopo"] = str(params.get("target") or params.get("modo") or params.get("platform") or "").strip()
        dados["habilidade"] = str(resultado.get("habilidade") or resultado.get("skill") or "").strip()
    return dados


def inferir_tipo_foco_vivo(
    intencao: str = "",
    habilidade: str = "",
    alvo: str = "",
    texto: str = "",
    resposta: str = "",
    *,
    normalizar_texto_cb=None,
) -> str:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else lambda v: str(v or "").lower().strip()
    base = normalizar(" ".join([
        str(intencao or ""),
        str(habilidade or ""),
        str(alvo or ""),
        str(texto or ""),
        str(resposta or ""),
    ]))
    intent = str(intencao or "").upper().strip()
    hab = str(habilidade or "").lower().strip()
    if intent in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"} or hab in {"arquivo", "arquivos"} or any(p in base for p in ["arquivo", "pasta", ".txt"]):
        return "arquivo"
    if intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"} or hab in {"janela", "app"}:
        return "janela"
    if intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"} or hab in {"site", "navegador"}:
        return "site"
    if intent in {"SEARCH"} or hab in {"pesquisa", "search"}:
        return "pesquisa"
    if intent in {"WEATHER"} or hab in {"clima", "tempo"}:
        return "clima"
    if intent in {"EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS"} or "email" in base:
        return "email"
    if intent in {"PLAYLIST_PLAY", "PLAYLIST_ADD", "PLAYLIST_LIST", "MUSIC_SEARCH", "MEDIA_CONTROL"} or hab in {"musica", "música", "playlist", "midia"}:
        return "musica"
    if intent in {"AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO"} or hab == "agenda":
        return "agenda"
    if hab == "conversa" or not intent:
        if any(p in base for p in ["opini", "acha", "presidente", "lula", "política", "politica"]):
            return "opiniao"
        return "conversa"
    return hab or "conversa"


def extrair_topico_foco_vivo(
    texto: str = "",
    resposta: str = "",
    alvo: str = "",
    habilidade: str = "",
    intencao: str = "",
    *,
    normalizar_texto_cb=None,
) -> str:
    alvo_limpo = str(alvo or "").strip()
    if alvo_limpo:
        return alvo_limpo[:120]
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else lambda v: str(v or "").lower().strip()
    t = normalizar(texto)
    for padrao in [
        r"(?:o que voce acha|o que você acha|voce acha|você acha|qual sua opiniao|qual sua opinião)\s+(?:do|da|de|sobre)?\s*(?P<tema>.+)$",
        r"(?:quem\s+e|quem\s+é|o\s+que\s+e|o\s+que\s+é|como\s+funciona|como\s+que\s+funciona|me\s+explica|explica|me\s+fala\s+sobre|fala\s+sobre|me\s+fala\s+de|fala\s+de)\s+(?P<tema>.+)$",
        r"(?:como assim|por que|porque|pq)\s+(?P<tema>.+)$",
    ]:
        m = re.search(padrao, t, flags=re.IGNORECASE)
        if m:
            tema = str(m.group("tema") or "").strip(" ?!.:,;")
            if tema:
                return tema[:120]
    if "lula" in t:
        return "presidente Lula"
    if "presidente" in t:
        return "presidente"
    hab = str(habilidade or "").strip()
    intent = str(intencao or "").strip()
    if hab:
        return hab[:120]
    if intent:
        return intent[:120]
    resp = str(resposta or "").strip()
    return resp[:120]


def atualizar_foco_vivo(
    estado: Dict[str, Any] | None,
    *,
    texto: str = "",
    resposta: str = "",
    intencao: str = "",
    alvo: str = "",
    habilidade: str = "",
    escopo: str = "",
    normalizar_texto_cb=None,
) -> Dict[str, Any]:
    estado = dict(estado or {})
    tipo = inferir_tipo_foco_vivo(
        intencao,
        habilidade,
        alvo,
        texto,
        resposta,
        normalizar_texto_cb=normalizar_texto_cb,
    )
    topico = extrair_topico_foco_vivo(
        texto,
        resposta,
        alvo,
        habilidade,
        intencao,
        normalizar_texto_cb=normalizar_texto_cb,
    )
    estado["foco_vivo_tipo"] = tipo
    estado["foco_vivo_alvo"] = str(alvo or topico or "").strip()[:160]
    estado["foco_vivo_topico"] = str(topico or "").strip()[:160]
    estado["foco_vivo_habilidade"] = str(habilidade or tipo or "").strip()[:80]
    estado["foco_vivo_intencao"] = str(intencao or "").strip()[:80]
    estado["foco_vivo_texto"] = str(texto or "").strip()[:180]
    estado["foco_vivo_resposta"] = str(resposta or "").strip()[:180]
    estado["foco_vivo_escopo"] = str(escopo or "").strip()[:80]
    estado["foco_vivo_ts"] = time.time()
    return estado


def foco_vivo_atual(estado_atual: Dict[str, Any] | None, *, ttl_s: float = 480.0) -> Dict[str, Any]:
    try:
        estado = dict(estado_atual or {})
        ts = float(estado.get("foco_vivo_ts") or 0.0)
        if not ts or time.time() - ts > ttl_s:
            return {}
        return {
            "tipo": str(estado.get("foco_vivo_tipo") or "").strip(),
            "alvo": str(estado.get("foco_vivo_alvo") or "").strip(),
            "topico": str(estado.get("foco_vivo_topico") or "").strip(),
            "habilidade": str(estado.get("foco_vivo_habilidade") or "").strip(),
            "intencao": str(estado.get("foco_vivo_intencao") or "").strip(),
            "texto": str(estado.get("foco_vivo_texto") or "").strip(),
            "resposta": str(estado.get("foco_vivo_resposta") or "").strip(),
            "idade_s": max(0.0, time.time() - ts),
        }
    except Exception:
        return {}


def texto_pede_repeticao_curta(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(str(texto or ""))
    if not t or len(t.split()) > 8:
        return False
    gatilhos = [
        "tenta de novo",
        "de novo",
        "tenta novamente",
        "novamente",
        "vai de novo",
        "faz de novo",
        "outra vez",
        "mais uma vez",
        "tenta outra vez",
    ]
    return any(g in t for g in gatilhos)


def resolver_repeticao_ultima_acao(
    texto: str,
    estado_atual: Dict[str, Any] | None,
    normalizar_texto_cb,
):
    if not texto_pede_repeticao_curta(texto, normalizar_texto_cb):
        return None
    estado = dict(estado_atual or {})
    if not bool(estado.get("ultima_acao_reexecutavel")):
        return None
    intent = str(estado.get("ultima_acao_intent") or "").strip().upper()
    params = estado.get("ultima_acao_params")
    if not intent or not isinstance(params, dict):
        return None
    return {"intent": intent, "params": dict(params)}


def contexto_musical_ativo(ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        if str(ultima_playlist or "").strip():
            return True
        if str(playlist_state.get("name") or "").strip():
            return True
        if str(playlist_state.get("last_url") or "").strip():
            return True
    except Exception:
        pass
    return False


def contexto_mental_ativo(mente_integrada_estado: Dict[str, Any], ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        estado = dict(mente_integrada_estado or {})
        if str(estado.get("ultima_entrada") or "").strip():
            return True
        if str(estado.get("ultima_intencao") or "").strip():
            return True
        if str(estado.get("ultimo_alvo") or "").strip():
            return True
        if str(estado.get("ultima_habilidade") or "").strip():
            return True
    except Exception:
        pass
    return contexto_musical_ativo(ultima_playlist, playlist_state)


def texto_depende_de_contexto(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(texto)
    if not t:
        return False
    palavras = t.split()
    if len(palavras) > 7:
        return False
    gatilhos = [
        "essa", "esse", "isso", "ele", "ela", "aqui", "ali", "tambem", "também",
        "de novo", "mais uma", "mais um", "essa tambem", "esse tambem",
        "essa também", "esse também", "essa aqui", "esse aqui", "essa ai", "esse ai",
    ]
    return any(g in t for g in gatilhos)


def fluxo_prioritario_da_ia(texto: str, normalizar_texto_cb, texto_depende_de_contexto_cb) -> bool:
    t = normalizar_texto_cb(texto)
    if not t:
        return False
    if any(p in t for p in ["playlist", "música", "musica", "site", "web", "aba", "janela", "foco", "tela cheia", "fullscreen", "opera", "chrome", "edge", "vscode"]):
        if texto_depende_de_contexto_cb(t):
            return True
        if any(p in t for p in ["coloca", "toca", "abre", "abra", "entra", "vai", "mostra", "lista", "quais"]):
            return True
    return False
