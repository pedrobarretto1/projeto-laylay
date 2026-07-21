"""Leitura de contexto imediato da mente da Laylay."""

from __future__ import annotations

import re
import time
import random
from typing import Any, Callable, Dict, Iterable, Tuple

from mente_laylay.memoria_mental.reparacao_conversacional import (
    detectar_reparacao_conversacional,
    registrar_correcao_alvo,
)
from mente_laylay.memoria_mental.musica_conversacional import sugestao_musical_nova_conversacional
from mente_laylay.memoria_mental.contexto_compartilhado import foco_por_dominio
from mente_laylay.memoria_mental.continuidade_semantica import (
    aprender_correcao_semantica,
    interpretar_continuidade_semantica_llm,
    registrar_decisao_semantica,
    resolver_continuidade_semantica,
)


def _normalizar_com_callback(valor: str, normalizar_texto: Callable[[str], str] | None) -> str:
    if callable(normalizar_texto):
        try:
            return str(normalizar_texto(valor) or "").strip()
        except Exception:
            pass
    return str(valor or "").strip().lower()


def referencia_contextual_imediata(
    *,
    mente_integrada_estado: Dict[str, Any] | None,
    foco_vivo: Dict[str, Any] | None,
    texto_atual: str = "",
    alvo_corrigido: str = "",
    ultima_playlist: str = "",
    normalizar_texto: Callable[[str], str] | None = None,
    ttl_s: float = 300.0,
) -> Dict[str, Any]:
    estado = dict(mente_integrada_estado or {})

    try:
        ts_mente = float(estado.get("ts") or 0.0)
    except Exception:
        ts_mente = 0.0
    if not ts_mente or (time.time() - ts_mente > ttl_s):
        return {}

    foco = dict(foco_vivo or {})
    ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultimo_params = estado.get("ultima_acao_params") if isinstance(estado.get("ultima_acao_params"), dict) else {}
    alvo_corrigido = str(alvo_corrigido or "").strip()
    ultimo_app = str(estado.get("ultimo_app_janela") or "").strip()
    ultimo_site = str(estado.get("ultimo_site_aba") or "").strip()
    ultimo_iot = str(estado.get("ultimo_dispositivo_iot") or "").strip()
    ultima_playlist = str(
        ultima_playlist
        or ultimo_params.get("nome_playlist")
        or ultimo_params.get("playlist")
        or ""
    ).strip()

    texto_norm = _normalizar_com_callback(texto_atual, normalizar_texto)
    dominio_pedido = ""
    if re.search(r"\b(foco|na frente|pra frente|para frente|tela cheia|fullscreen|maximiza|maximizar)\b", texto_norm):
        dominio_pedido = "app"
    elif re.search(r"\b(aba|guia|site|pagina|página)\b", texto_norm):
        dominio_pedido = "site"
    elif re.search(r"\b(pausa|despausa|proxima|próxima|anterior|musica|música|faixa|playlist|toca|replay)\b", texto_norm):
        dominio_pedido = "musica"
    elif re.search(r"\b(arquivo|pasta|diretorio|diretório|texto|\.txt)\b", texto_norm):
        dominio_pedido = "arquivo"
    elif re.search(r"\b(liga|ligar|desliga|desligar|estado|status)\b", texto_norm) and re.search(
        r"\b(ele|ela|isso|dispositivo|aparelho|tomada|ventilador|luz|lampada|lâmpada)\b", texto_norm
    ):
        dominio_pedido = "iot"

    if dominio_pedido:
        foco_dominio = foco_por_dominio(estado, dominio_pedido, ttl_s=ttl_s)
        alvo_dominio = str(foco_dominio.get("alvo") or foco_dominio.get("topico") or "").strip()
        if alvo_dominio:
            tipo_ref = "midia" if dominio_pedido == "musica" else dominio_pedido
            return {
                "tipo": tipo_ref,
                "alvo": alvo_dominio,
                "intencao": str(foco_dominio.get("intencao") or ultima_intencao),
                "params": ultimo_params,
                "dominio_explicito": True,
            }

    if alvo_corrigido:
        if ultimo_site and _normalizar_com_callback(alvo_corrigido, normalizar_texto) == _normalizar_com_callback(ultimo_site, normalizar_texto):
            return {"tipo": "site", "alvo": alvo_corrigido, "intencao": ultima_intencao, "params": ultimo_params}
        return {"tipo": "app", "alvo": alvo_corrigido, "intencao": ultima_intencao, "params": ultimo_params}

    # A ação prática mais recente define a referência. O foco visual pode ainda
    # apontar para o navegador depois que um site novo foi aberto.
    if ultima_intencao in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"}:
        alvo_site = str(ultimo_params.get("alvo") or ultimo_params.get("url") or ultimo_site or "").strip()
        if alvo_site:
            return {"tipo": "site", "alvo": alvo_site, "intencao": ultima_intencao, "params": ultimo_params}
    if ultima_intencao in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        alvo_app = str(ultimo_params.get("nome_app") or ultimo_params.get("app") or ultimo_app or "").strip()
        if alvo_app:
            return {"tipo": "app", "alvo": alvo_app, "intencao": ultima_intencao, "params": ultimo_params}
    if ultima_intencao in {"PLAYLIST_PLAY", "PLAYLIST_ADD", "PLAYLIST_LIST", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE"}:
        if ultima_playlist:
            return {"tipo": "playlist", "alvo": ultima_playlist, "intencao": ultima_intencao, "params": ultimo_params}
    if ultima_intencao == "MEDIA_CONTROL":
        return {"tipo": "midia", "alvo": "musica", "intencao": ultima_intencao, "params": ultimo_params}
    if ultima_intencao == "VOLUME":
        return {"tipo": "volume", "alvo": "volume", "intencao": ultima_intencao, "params": ultimo_params}
    if ultima_intencao in {"IOT_CONTROL", "IOT_STATUS"} or ultimo_iot:
        alvo_iot = str(ultimo_params.get("alvo") or ultimo_iot).strip()
        if alvo_iot:
            return {"tipo": "iot", "alvo": alvo_iot, "intencao": ultima_intencao, "params": ultimo_params}

    habilidade_foco = str(foco.get("habilidade") or "").strip().lower()
    alvo_foco = str(foco.get("alvo") or "").strip()
    if habilidade_foco == "janela" and alvo_foco:
        return {"tipo": "app", "alvo": alvo_foco, "intencao": ultima_intencao, "params": ultimo_params}
    if habilidade_foco == "site" and alvo_foco:
        return {"tipo": "site", "alvo": alvo_foco, "intencao": ultima_intencao, "params": ultimo_params}
    if habilidade_foco in {"playlist", "musica", "midia"}:
        if ultima_playlist:
            return {"tipo": "playlist", "alvo": ultima_playlist, "intencao": ultima_intencao, "params": ultimo_params}
        return {"tipo": "midia", "alvo": "musica", "intencao": ultima_intencao, "params": ultimo_params}
    if habilidade_foco == "iot" and (alvo_foco or ultimo_iot):
        return {"tipo": "iot", "alvo": alvo_foco or ultimo_iot, "intencao": ultima_intencao, "params": ultimo_params}

    if ultima_playlist and ultima_intencao == "MUSIC_SEARCH":
        return {"tipo": "playlist", "alvo": ultima_playlist, "intencao": ultima_intencao, "params": ultimo_params}
    return {}


def resolver_comando_acao_geral_contextual(
    texto_normalizado: str,
    contexto_ref: Dict[str, Any] | None,
    *,
    ultima_playlist: str = "",
) -> Dict[str, Any] | None:
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    contexto_ref = dict(contexto_ref or {})
    if not contexto_ref:
        return None

    if "playlist" in t and re.search(
        r"\b(?:coloca|coloque|bota|salva|salve|guarda|guarde|adiciona|adicione|add)\b",
        t,
    ) and re.search(r"\b(?:na|nessa|nesta|para a|pra|em)\s+(?:minha\s+)?playlist\b", t):
        # Deixa o detector explícito extrair o destino e executar PLAYLIST_ADD.
        return None

    ultimo_params = contexto_ref.get("params") if isinstance(contexto_ref.get("params"), dict) else {}
    tipo_ref = str(contexto_ref.get("tipo") or "").strip().lower()
    alvo_ref = str(contexto_ref.get("alvo") or "").strip()
    ultima_playlist = str(ultima_playlist or "").strip()

    if tipo_ref == "volume":
        if re.fullmatch(r"(?:desmuta|desmutar|tira do mudo|volta o som)", t):
            return {"intent": "VOLUME", "params": {"acao": "unmute", "referencia_contextual": True}}
        if re.fullmatch(r"(?:muta|mutar|mute|deixa mudo|fica sem som)", t):
            return {"intent": "VOLUME", "params": {"acao": "mute", "referencia_contextual": True}}
        nivel = re.fullmatch(
            r"(?:(?:coloca|coloque|bota|deixa|poe|põe)\s+)?(?:o\s+)?(?:em|no|para|pra)?\s*(\d{1,3})\s*%?",
            t,
        )
        if nivel:
            valor = max(0, min(100, int(nivel.group(1))))
            print(f"🔊 [CONTEXTO-GERAL] ajustando volume recente -> {valor}%")
            return {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": valor, "referencia_contextual": True}}

    tem_referencia = bool(re.search(r"\b(?:ela|ele|isso|aquilo|essa|esse|esta|este)\b", t))
    tem_repeticao = bool(re.search(r"\b(?:novamente|repete|repetir)\b|\bde\s+novo\b|\boutra\s+vez\b", t))
    tem_reversao = bool(re.search(r"\b(?:restaur\w*|recuper\w*|desfaz\w*|traz\w*|volt\w*)\b", t))
    verbo_abrir = bool(re.search(r"\b(?:abr\w*|coloc\w*|bot\w*|toc\w*|quer\w*)\b", t))
    verbo_fechar = bool(re.search(r"\b(?:fech\w*|encerr\w*)\b", t))
    pedido_de_volta = bool(
        tem_reversao
        or verbo_abrir and (tem_referencia or tem_repeticao)
    )
    pedido_fechar_ref = bool(verbo_fechar and (tem_referencia or tem_repeticao))
    pedido_fechar_aba = bool(verbo_fechar and re.search(r"\b(?:aba|guia)\b", t))
    pedido_retomar_musica = bool(
        re.search(r"\b(?:coloc\w*|bot\w*|toc\w*)\b", t)
        and (tem_referencia or tem_repeticao)
        and "playlist" not in t
    )
    pedido_add_playlist_ref = bool(
        re.search(r"\b(?:tambem|também)\b", t)
        and tem_referencia
    )

    if not (pedido_de_volta or pedido_fechar_ref or pedido_fechar_aba or pedido_retomar_musica or pedido_add_playlist_ref):
        return None

    # Uma referencia explicita a aba nunca deve encerrar o navegador inteiro.
    if pedido_fechar_aba:
        alvo_site = str(
            alvo_ref if tipo_ref == "site" else ultimo_params.get("alvo") or ultimo_params.get("url") or ""
        ).strip()
        if alvo_site:
            print(f"🧠 [CONTEXTO-GERAL] fechando aba por referencia -> '{alvo_site}'")
            return {"intent": "CLOSE_TAB", "params": {"alvo": alvo_site}}

    if pedido_add_playlist_ref and tipo_ref == "playlist":
        nome_playlist = str(
            alvo_ref
            or ultimo_params.get("nome_playlist")
            or ultimo_params.get("playlist")
            or ultima_playlist
            or ""
        ).strip()
        if nome_playlist:
            print(f"🎵 [CONTEXTO-GERAL] adicionando faixa atual na playlist recente -> '{nome_playlist}'")
            return {"intent": "PLAYLIST_ADD", "params": {"nome_playlist": nome_playlist, "referencia_contextual": True}}

    # "Essa também" só continua uma ação de playlist. Em contexto de site ou
    # aplicativo, não deve ser confundido com pedido para reabrir o último alvo.
    if pedido_add_playlist_ref:
        return None

    if pedido_retomar_musica and tipo_ref in {"playlist", "midia"}:
        print("🧠 [CONTEXTO-GERAL] retomando faixa atual por repeticao natural")
        return {"intent": "MEDIA_CONTROL", "params": {"acao": "replay", "platform": "music", "referencia_contextual": True}}

    if tipo_ref == "app":
        nome_app = str(alvo_ref or ultimo_params.get("nome_app") or ultimo_params.get("app") or "").strip()
        if nome_app:
            if pedido_fechar_ref:
                print(f"🧠 [CONTEXTO-GERAL] fechando app por referencia -> '{nome_app}'")
                return {"intent": "CLOSE_APP", "params": {"nome_app": nome_app}}
            print(f"🧠 [CONTEXTO-GERAL] retomando app -> '{nome_app}'")
            return {"intent": "APP_OPEN", "params": {"nome_app": nome_app, "modo": "focus"}}

    if tipo_ref == "site":
        alvo = str(alvo_ref or ultimo_params.get("alvo") or ultimo_params.get("url") or "").strip()
        if alvo:
            if pedido_fechar_ref:
                print(f"🧠 [CONTEXTO-GERAL] fechando site por referencia -> '{alvo}'")
                return {"intent": "CLOSE_TAB", "params": {"alvo": alvo}}
            print(f"🧠 [CONTEXTO-GERAL] retomando site -> '{alvo}'")
            return {"intent": "OPEN_URL", "params": {"alvo": alvo}}

    if tipo_ref == "playlist":
        nome_playlist = str(
            alvo_ref
            or ultimo_params.get("nome_playlist")
            or ultimo_params.get("playlist")
            or ultima_playlist
            or ""
        ).strip()
        if nome_playlist:
            if pedido_fechar_ref:
                return {"intent": "MEDIA_CONTROL", "params": {"acao": "pause", "platform": "music", "referencia_contextual": True}}
            print(f"🧠 [CONTEXTO-GERAL] retomando playlist -> '{nome_playlist}'")
            return {"intent": "PLAYLIST_PLAY", "params": {"nome_playlist": nome_playlist}}

    if tipo_ref == "midia" and (pedido_fechar_ref or pedido_de_volta):
        return {"intent": "MEDIA_CONTROL", "params": {"acao": "pause" if pedido_fechar_ref else "play", "platform": "music", "referencia_contextual": True}}

    return None


def extrair_app_explicito_em_comando_janela(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> str:
    """Identifica quando o usuario citou explicitamente um app em comando de janela."""
    if callable(normalizar_texto):
        try:
            t = str(normalizar_texto(texto) or "").strip()
        except Exception:
            t = str(texto or "").strip().lower()
    else:
        t = str(texto or "").strip().lower()
    if not t:
        return ""

    aliases_apps = {
        "steam": {"steam"},
        "opera": {"opera", "ópera", "operagx", "opera gx"},
        "vscode": {"vscode", "vs code", "visual studio code", "code"},
        "chrome": {"chrome", "google chrome"},
        "edge": {"edge", "msedge", "microsoft edge"},
        "brave": {"brave", "brave browser"},
        "firefox": {"firefox", "mozilla firefox"},
        "microsoft store": {"microsoft store", "ms store", "store", "loja microsoft"},
    }

    for app, aliases in aliases_apps.items():
        if any(alias in t for alias in aliases):
            return app
    return ""


def resolver_comando_contextual(
    texto: str,
    candidatos: Iterable[Tuple[str, Callable[[str], Dict[str, Any] | None]]],
) -> Dict[str, Any] | None:
    for rota, resolver in candidatos:
        rota_txt = str(rota or "GERAL").upper()
        try:
            resultado = resolver(texto)
        except Exception as e:
            print(f"⚠️ [CONTEXTO-{rota_txt}] falha ao resolver: {e}")
            continue
        if isinstance(resultado, dict) and str(resultado.get("intent") or "").strip():
            saida = dict(resultado)
            saida["_rota_contextual"] = rota_txt
            return saida
    return None


def resolver_comando_arquivo_contextual(
    texto_normalizado: str,
    *,
    mente_integrada_estado: Dict[str, Any] | None,
    estrutura_recente: Dict[str, Any] | None,
    ttl_s: float = 300.0,
) -> Dict[str, Any] | None:
    t = str(texto_normalizado or "").strip()
    if not t:
        return None

    estado = dict(mente_integrada_estado or {})
    ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultima_habilidade = str(estado.get("ultima_habilidade") or "").strip().lower()
    try:
        ts_mente = float(estado.get("ts") or 0.0)
    except Exception:
        ts_mente = 0.0
    if not (
        (ultima_intencao in {"CREATE_FOLDER", "DELETE_ITEM", "CREATE_FILE", "MOVE_ITEM"} or ultima_habilidade in {"arquivo", "arquivos"})
        and ts_mente
        and (time.time() - ts_mente <= ttl_s)
    ):
        return None

    estrutura = dict(estrutura_recente or {})
    if not estrutura:
        return None

    if re.fullmatch(
        r"(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:ela|ele|isso|essa|esse|essa\s+pasta|esse\s+arquivo)",
        t,
        flags=re.IGNORECASE,
    ):
        nome = str(estrutura.get("nome") or estrutura.get("pasta") or estrutura.get("alvo") or "").strip()
        arquivo_nome = str(estrutura.get("arquivo_nome") or estrutura.get("nome_arquivo") or "").strip()
        alvo = nome or arquivo_nome
        tipo = "pasta" if nome else ("arquivo" if arquivo_nome else "")
        if alvo:
            print(f"📁 [ARQUIVO:CONTEXTO] apagando referencia curta -> '{alvo}'")
            params = {"alvo": alvo}
            if tipo:
                params["tipo"] = tipo
            return {"intent": "DELETE_ITEM", "params": params}

    return None


def resolver_comando_midia_contextual(
    texto_normalizado: str,
    *,
    mente_integrada_estado: Dict[str, Any] | None,
    contexto_musical: bool,
    ttl_s: float = 240.0,
) -> Dict[str, Any] | None:
    t = str(texto_normalizado or "").strip()
    if not t:
        return None

    t_limpo = re.sub(r"\b(?:h+m+|hmm+|hum+|ahn+|ah+|tipo|entao|então|agora|lay|laylay|por favor|pfv)\b", " ", t)
    t_limpo = re.sub(r"\s+", " ", t_limpo).strip() or t

    # Um pedido explícito para guardar/adicionar em playlist pertence ao
    # roteador de playlist. Herdar o último contexto musical aqui transformava
    # "coloca essa música na playlist X" em replay.
    if "playlist" in t_limpo and re.search(
        r"\b(?:coloca|coloque|bota|salva|salve|guarda|guarde|adiciona|adicione|add)\b",
        t_limpo,
    ):
        return None

    estado = dict(mente_integrada_estado or {})
    ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultima_habilidade = str(estado.get("ultima_habilidade") or "").strip().lower()
    try:
        ts_mente = float(estado.get("ts") or 0.0)
    except Exception:
        ts_mente = 0.0
    midia_recente = (
        ultima_intencao == "MEDIA_CONTROL"
        or ultima_habilidade in {"midia", "musica", "playlist"}
    ) and ts_mente and (time.time() - ts_mente <= ttl_s)
    referencia_contextual = any(x in t_limpo for x in ["ela", "ele", "isso", "essa", "esse", "anterior", "antes"])
    menciona_midia = any(x in t_limpo for x in ["musica", "música", "som", "faixa", "trilha", "youtube", "playlist"])
    if not (contexto_musical or menciona_midia or (referencia_contextual and midia_recente)):
        return None

    def _params(acao: str) -> Dict[str, Any]:
        params = {"acao": acao, "platform": "music"}
        if referencia_contextual:
            params["referencia_contextual"] = True
        return {"intent": "MEDIA_CONTROL", "params": params}

    # Ordem importa: "despausa" contem "pausa", entao vem primeiro.
    if any(x in t_limpo for x in ["toca ela de novo", "toca ele de novo", "toca isso de novo", "toca essa de novo", "recomeca", "recomeça", "reinicia a musica", "reinicia a música", "repete essa", "repete ela"]):
        print(f"🎵 [MIDIA:CONTEXTO] replay detectado -> '{t_limpo}'")
        return _params("replay")
    if any(x in t_limpo for x in ["despausa", "despausar", "despusa", "despusar", "depausa", "depausar", "retoma", "retomar", "continua tocando", "continua ela", "continua ele", "volta a tocar"]):
        print(f"🎵 [MIDIA:CONTEXTO] play detectado -> '{t_limpo}'")
        return _params("play")
    if any(x in t_limpo for x in ["pausa", "pausar", "pause", "para ela", "para ele", "para isso", "para a musica", "para música"]):
        print(f"🎵 [MIDIA:CONTEXTO] pause detectado -> '{t_limpo}'")
        return _params("pause")
    if "playlist" not in t_limpo and any(x in t_limpo for x in ["proxima", "próxima", "proximo", "próximo", "pula", "passa ela", "passa essa"]):
        print(f"🎵 [MIDIA:CONTEXTO] next detectado -> '{t_limpo}'")
        return _params("next")
    if any(x in t_limpo for x in ["musica anterior", "música anterior", "anterior", "volta ela", "volta essa", "volta a musica", "volta a música", "volta para a de antes", "volta pra de antes", "volta para a anterior", "volta pra anterior", "vai para a anterior"]):
        print(f"🎵 [MIDIA:CONTEXTO] prev detectado -> '{t_limpo}'")
        return _params("prev")
    return None


def resolver_comando_janela_contextual(
    texto_normalizado: str,
    *,
    mente_integrada_estado: Dict[str, Any] | None,
    app_explicito: str = "",
    alvo_corrigido: str = "",
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any] | None:
    t = str(texto_normalizado or "").strip()
    if not t:
        return None

    quer_fechar = any(x in t for x in ["fecha", "fechar", "encerra", "encerrar", "mata", "derruba"])
    quer_maximizar = any(x in t for x in ["tela cheia", "fullscreen", "maximiza", "maximizar"])

    app_explicito = str(app_explicito or "").strip()
    if app_explicito:
        if quer_fechar:
            return {"intent": "CLOSE_APP", "params": {"nome_app": app_explicito}, "_alvo_corrigido": app_explicito}
        if quer_maximizar:
            return {"intent": "MAXIMIZE_WINDOW", "params": {"nome_app": app_explicito}, "_alvo_corrigido": app_explicito}
        return {"intent": "APP_OPEN", "params": {"nome_app": app_explicito, "modo": "focus"}, "_alvo_corrigido": app_explicito}

    if not any(x in t for x in ["ele", "ela", "isso", "esse", "essa"]):
        return None
    if not any(x in t for x in ["foco", "na frente", "pra frente", "para frente", "tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return None

    estado = dict(mente_integrada_estado or {})
    apps_sem_janela_contextual = {
        "microsoft store",
        "store",
        "ms store",
        "loja microsoft",
        "loja",
    }

    ultima_intencao_ctx = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultimo_app = str(alvo_corrigido or estado.get("ultimo_app_janela") or "").strip()
    if not ultimo_app and ultima_intencao_ctx in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        candidato = str(
            (estado.get("ultima_acao_params") or {}).get("nome_app")
            or (estado.get("ultima_acao_params") or {}).get("app")
            or ""
        ).strip()
        if _normalizar_com_callback(candidato, normalizar_texto) not in apps_sem_janela_contextual:
            ultimo_app = candidato

    if not ultimo_app:
        return None

    if quer_maximizar:
        return {"intent": "MAXIMIZE_WINDOW", "params": {"nome_app": ultimo_app}}
    return {"intent": "APP_OPEN", "params": {"nome_app": ultimo_app, "modo": "focus"}}


def fala_contexto_janela_indisponivel(
    texto_normalizado: str,
    *,
    mente_integrada_estado: Dict[str, Any] | None,
) -> str:
    t = str(texto_normalizado or "").strip()
    if not t:
        return ""
    if not any(x in t for x in ["ele", "ela", "isso", "esse", "essa"]):
        return ""
    if not any(x in t for x in ["foco", "na frente", "pra frente", "para frente", "tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return ""

    estado = dict(mente_integrada_estado or {})
    ultimo_site = str(estado.get("ultimo_site_aba") or "").strip()
    ultimo_app = str(estado.get("ultimo_app_janela") or "").strip()
    if ultimo_app:
        return ""

    ultima_intencao_ctx = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    if ultima_intencao_ctx not in {"APP_OPEN", "OPEN_URL", "MAXIMIZE_WINDOW"} and not ultimo_site:
        return ""

    alvo = ultimo_site or str((estado.get("ultima_acao_params") or {}).get("nome_app") or "").strip() or "isso"
    if any(x in t for x in ["tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return random.choice([
            f"{alvo} não me virou uma janela normal pra maximizar. Se quiser, me pede um app ou janela de verdade.",
            f"Isso abriu por outro caminho, então eu não tenho uma janela comum de {alvo} pra deixar em destaque.",
            f"Eu entendi o alvo, mas {alvo} não apareceu como janela normal pra eu colocar em tela cheia.",
        ])
    return random.choice([
        f"Eu peguei a referência, mas {alvo} não virou uma janela comum pra eu focar.",
        f"Isso aí não apareceu como janela normal, então não deu pra puxar {alvo} pro foco.",
        f"Entendi o 'ele', só que {alvo} não me deu uma janela real pra trazer pra frente.",
    ])


class ContextoImediatoRuntime:
    """Liga os resolvedores puros à memória viva sem criar outro roteador."""

    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        estado_runtime_getter: Callable[[], Any],
    ) -> None:
        self.namespace_getter = namespace_getter
        self.estado_runtime_getter = estado_runtime_getter

    def _namespace(self) -> Dict[str, Any]:
        return self.namespace_getter() or {}

    def _estado(self) -> Any:
        return self.estado_runtime_getter()

    def extrair_app_explicito(self, texto: str) -> str:
        return extrair_app_explicito_em_comando_janela(
            texto,
            normalizar_texto=self._namespace()["_normalizar_texto_com_apelidos"],
        )

    def resolver_janela(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        t = ns["_normalizar_texto_com_apelidos"](texto)
        if not t:
            return None
        resultado = resolver_comando_janela_contextual(
            t,
            mente_integrada_estado=self._estado().mental,
            app_explicito=self.extrair_app_explicito(t),
            alvo_corrigido=ns["_alvo_corrigido_atual"](),
            normalizar_texto=ns["_normalizar_texto_com_apelidos"],
        )
        alvo_corrigido = str(
            (resultado or {}).get("_alvo_corrigido") or ""
        ).strip()
        if alvo_corrigido:
            ns["_registrar_alvo_corrigido"](alvo_corrigido)
            resultado = dict(resultado or {})
            resultado.pop("_alvo_corrigido", None)
        return resultado

    def resolver_iot(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        detector = ns.get("_detectar_intencao_iot")
        if not callable(detector):
            return None
        t = ns["_normalizar_texto_com_apelidos"](texto)
        if not t:
            return None
        if re.search(r"\b(apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir|cria|criar|move|mover)\b", t) and re.search(
            r"\b(pasta|arquivo|documento|txt)\b", t
        ):
            return None
        try:
            resultado = detector(t, self._estado().mental)
        except Exception:
            return None
        if not isinstance(resultado, dict):
            return None
        if str(resultado.get("intent") or "").upper().strip() not in {"IOT_CONTROL", "IOT_STATUS", "IOT_LIST", "SUGGEST_ACTION"}:
            return None
        params = dict(resultado.get("params") or {})
        if re.search(r"\b(ele|ela|isso|esse|essa|dele|dela)\b", t):
            params["referencia_contextual"] = True
        return {"intent": str(resultado.get("intent") or "").upper(), "params": params}

    def responder_janela_indisponivel(self, texto: str) -> bool:
        ns = self._namespace()
        t = ns["_normalizar_texto_com_apelidos"](texto)
        if not t:
            return False
        fala = fala_contexto_janela_indisponivel(
            t,
            mente_integrada_estado=self._estado().mental,
        )
        if not fala:
            return False
        ns["falar_com_lipsync"](fala, "calma", 1)
        return True

    def resolver_midia(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        t = ns["_normalizar_texto_com_apelidos"](texto)
        if not t:
            return None
        mente = self._estado().mental
        ultimo_intent = str(mente.get("ultima_acao_intent") or mente.get("ultima_intencao") or "").upper()
        if ultimo_intent == "MUSIC_SEARCH" and re.search(r"\b(?:tenta|manda|coloca|toca)\s+outr[ao]\b", t):
            ultimos_params = mente.get("ultima_acao_params") if isinstance(mente.get("ultima_acao_params"), dict) else {}
            query_anterior = str(ultimos_params.get("query") or mente.get("ultimo_alvo") or "musica").strip()
            nova = sugestao_musical_nova_conversacional(
                f"{query_anterior} diferente",
                normalizar_texto=ns["_normalizar_texto_com_apelidos"],
            )
            return {"intent": "MUSIC_SEARCH", "params": {"query": nova, "origem": "continuacao_busca"}}
        return resolver_comando_midia_contextual(
            t,
            mente_integrada_estado=self._estado().mental,
            contexto_musical=ns["_contexto_musical_ativo"](),
            ttl_s=240.0,
        )

    def resolver_arquivo(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        t = ns["_normalizar_texto_com_apelidos"](texto)
        if not t:
            return None
        return resolver_comando_arquivo_contextual(
            t,
            mente_integrada_estado=self._estado().mental,
            estrutura_recente=ns["_estrutura_arquivo_recente"](900.0),
            ttl_s=300.0,
        )

    def referencia(self, ttl_s: float = 300.0, texto_atual: str = "") -> Dict[str, Any]:
        ns = self._namespace()
        estado = self._estado()
        return referencia_contextual_imediata(
            mente_integrada_estado=estado.mental,
            foco_vivo=ns["_foco_vivo_atual"](ttl_s=ttl_s),
            texto_atual=texto_atual,
            alvo_corrigido=ns["_alvo_corrigido_atual"](),
            ultima_playlist=estado.musica_get("ultima_playlist"),
            normalizar_texto=ns["_normalizar_texto_com_apelidos"],
            ttl_s=ttl_s,
        )

    def resolver_acao_geral(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        t = ns["_normalizar_texto_com_apelidos"](texto)
        if not t:
            return None
        return resolver_comando_acao_geral_contextual(
            t,
            self.referencia(300.0, texto_atual=t),
            ultima_playlist=self._estado().musica_get("ultima_playlist"),
        )

    def resolver_semantico(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        estrutura = ns["_estrutura_arquivo_recente"](900.0)
        decisao = resolver_continuidade_semantica(
            texto,
            mente=self._estado().mental,
            estrutura_arquivo=estrutura,
        )
        resultado = decisao.para_intencao()
        if resultado is None and 0.20 <= decisao.confianca < 0.60:
            decisao_ia = interpretar_continuidade_semantica_llm(
                texto,
                mente=self._estado().mental,
                estrutura_arquivo=estrutura,
                enviar_mensagem=ns.get("enviar_mensagem"),
            )
            resultado = decisao_ia.para_intencao()
            if resultado is not None:
                decisao = decisao_ia
        if isinstance(resultado, dict):
            estado_runtime = self._estado()
            estado_runtime.substituir(
                "mental",
                registrar_decisao_semantica(estado_runtime.mental, decisao, texto),
            )
            print(
                "🧭 [CONTINUIDADE:SEMANTICA] "
                f"dominio={decisao.dominio} operacao={decisao.operacao} "
                f"intent={decisao.intent} confianca={decisao.confianca:.2f}"
            )
        return resultado

    def resolver_reparacao(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        estado_runtime = self._estado()
        estado_aprendido, correcao = aprender_correcao_semantica(
            estado_runtime.mental,
            texto,
        )
        if correcao:
            estado_runtime.substituir("mental", estado_aprendido)
            print(
                "🧠 [CONTINUIDADE:APRENDIZADO] "
                f"{correcao.get('dominio_escolhido')} -> {correcao.get('dominio_correto')}"
            )
        reparacao = detectar_reparacao_conversacional(
            texto,
            estado_runtime.mental,
            normalizar_texto=ns["_normalizar_texto_com_apelidos"],
            extrair_app_explicito=self.extrair_app_explicito,
        )
        if not isinstance(reparacao, dict):
            return None
        alvo_novo = str(reparacao.get("alvo_novo") or "").strip()
        estado_runtime.atualizar_campos(
            "mental",
            ultima_reparacao_alvo_anterior=str(reparacao.get("alvo_anterior") or ""),
            ultima_reparacao_alvo_novo=alvo_novo,
            ultima_reparacao_tipo=str(reparacao.get("tipo") or ""),
            ultima_reparacao_ts=time.time(),
        )
        if reparacao.get("tipo") == "operacional":
            estado_runtime.substituir(
                "mental",
                registrar_correcao_alvo(estado_runtime.mental, reparacao),
            )
            if alvo_novo:
                ns["_registrar_alvo_corrigido"](alvo_novo)
            print(
                "🧠 [CONTINUIDADE:ALVO] "
                f"dominio={reparacao.get('dominio')} "
                f"{reparacao.get('alvo_anterior')} -> "
                f"{reparacao.get('resumo_correcao') or alvo_novo}"
            )
        return reparacao

    def resolver(self, texto: str) -> Dict[str, Any] | None:
        ns = self._namespace()
        t = ns["_normalizar_texto_com_apelidos"](texto)
        if re.search(
            r"\b(?:daqui|em)\s+\d{1,4}\s*(?:segundos?|seg|minutos?|min|horas?)\b",
            t,
        ) or re.search(r"\b(?:as|às)\s+\d{1,2}:\d{2}\b", t):
            return None
        estrutura = ns["_estrutura_arquivo_recente"](900.0)
        mente = self._estado().mental
        verbo_arquivo = bool(re.search(
            r"\b(apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir|cria|criar|move|mover|renomeia|renomear)\b",
            t,
        ))
        contexto_arquivo = bool(
            re.search(r"\b(pasta|arquivo|documento|txt)\b", t)
            or estrutura
            or str(mente.get("ultima_habilidade") or "").lower() in {"arquivo", "arquivos"}
            or str(mente.get("ultima_intencao") or "").upper() in {"CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "MOVE_ITEM"}
        )
        if verbo_arquivo and contexto_arquivo:
            resolvedores = [
                ("SEMANTICA", self.resolver_semantico),
                ("ARQUIVO", self.resolver_arquivo),
                ("IOT", self.resolver_iot),
                ("JANELA", self.resolver_janela),
                ("MIDIA", self.resolver_midia),
                ("GERAL", self.resolver_acao_geral),
            ]
        else:
            resolvedores = [
                # O resolvedor de domínio preserva propriedades explícitas
                # (ex.: "deixa ela rosa") antes de reutilizar a ação anterior.
                ("IOT", self.resolver_iot),
                ("SEMANTICA", self.resolver_semantico),
                ("JANELA", self.resolver_janela),
                ("MIDIA", self.resolver_midia),
                ("ARQUIVO", self.resolver_arquivo),
                ("GERAL", self.resolver_acao_geral),
            ]
        return resolver_comando_contextual(
            texto,
            resolvedores,
        )


def criar_contexto_imediato_runtime(**kwargs: Any) -> ContextoImediatoRuntime:
    return ContextoImediatoRuntime(**kwargs)
