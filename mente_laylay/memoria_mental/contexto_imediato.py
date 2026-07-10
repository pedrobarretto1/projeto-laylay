"""Leitura de contexto imediato da mente da Laylay."""

from __future__ import annotations

import re
import time
import random
from typing import Any, Callable, Dict, Iterable, Tuple


def referencia_contextual_imediata(
    *,
    mente_integrada_estado: Dict[str, Any] | None,
    foco_vivo: Dict[str, Any] | None,
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
    ultima_playlist = str(
        ultima_playlist
        or ultimo_params.get("nome_playlist")
        or ultimo_params.get("playlist")
        or ""
    ).strip()

    def _norm(valor: str) -> str:
        if callable(normalizar_texto):
            try:
                return str(normalizar_texto(valor) or "").strip()
            except Exception:
                pass
        return str(valor or "").strip().lower()

    if alvo_corrigido:
        if ultimo_site and _norm(alvo_corrigido) == _norm(ultimo_site):
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

    ultimo_params = contexto_ref.get("params") if isinstance(contexto_ref.get("params"), dict) else {}
    tipo_ref = str(contexto_ref.get("tipo") or "").strip().lower()
    alvo_ref = str(contexto_ref.get("alvo") or "").strip()
    ultima_playlist = str(ultima_playlist or "").strip()

    pedido_de_volta = any(p in t for p in [
        "traz de volta",
        "traz ela de volta",
        "traz ele de volta",
        "traz isso de volta",
        "restaura isso",
        "restaura ela",
        "restaura ele",
        "abre de novo",
        "abre isso de novo",
        "abre ela de novo",
        "abre ele de novo",
        "coloca de novo",
        "bota de novo",
        "toca de novo",
        "quero isso de novo",
        "abre ela",
        "abre ele",
        "abre isso",
        "coloca ela",
        "coloca ele",
        "coloca isso",
    ])
    pedido_fechar_ref = any(p in t for p in [
        "fecha ela",
        "fecha ele",
        "fecha isso",
        "fecha essa",
        "fecha esse",
        "fecha ele ai",
        "fecha ela ai",
        "fecha de novo",
        "fecha isso de novo",
        "fecha ela de novo",
        "fecha ele de novo",
    ])
    pedido_retomar_musica = any(p in t for p in [
        "coloca de novo",
        "coloca ela de novo",
        "coloca isso de novo",
        "bota de novo",
        "bota ela de novo",
        "toca de novo",
        "toca ela de novo",
    ])
    pedido_add_playlist_ref = any(p in t for p in [
        "essa tambem",
        "essa também",
        "esta tambem",
        "esta também",
        "isso tambem",
        "isso também",
        "essa aqui tambem",
        "essa aqui também",
    ])

    if not (pedido_de_volta or pedido_fechar_ref or pedido_retomar_musica or pedido_add_playlist_ref):
        return None

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

    if any(p in t for p in [
        "traz ela de volta",
        "traz ele de volta",
        "traz isso de volta",
        "restaura isso",
        "restaura ela",
        "restaura ele",
        "refaz isso",
        "faz isso de novo",
        "cria de novo",
        "cria isso de novo",
        "faz de novo",
    ]):
        nome = str(estrutura.get("nome") or estrutura.get("pasta") or estrutura.get("alvo") or "").strip()
        if not nome:
            return None
        params = {"nome": nome}
        for chave in ["pasta_pai", "pasta_interna", "mover_item", "arquivo_nome", "arquivo_conteudo", "target"]:
            valor = estrutura.get(chave)
            if str(valor or "").strip():
                params[chave] = valor
        print(f"📁 [ARQUIVO:CONTEXTO] recriando estrutura -> '{nome}'")
        return {"intent": "CREATE_FOLDER", "params": params}

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
    if any(x in t_limpo for x in ["despausa", "despausar", "depausa", "depausar", "retoma", "retomar", "continua tocando", "continua ela", "continua ele", "volta a tocar"]):
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

    def _norm(valor: str) -> str:
        if callable(normalizar_texto):
            try:
                return str(normalizar_texto(valor) or "").strip()
            except Exception:
                pass
        return str(valor or "").strip().lower()

    ultima_intencao_ctx = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultimo_app = str(alvo_corrigido or estado.get("ultimo_app_janela") or "").strip()
    if not ultimo_app and ultima_intencao_ctx in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        candidato = str(
            (estado.get("ultima_acao_params") or {}).get("nome_app")
            or (estado.get("ultima_acao_params") or {}).get("app")
            or ""
        ).strip()
        if _norm(candidato) not in apps_sem_janela_contextual:
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
