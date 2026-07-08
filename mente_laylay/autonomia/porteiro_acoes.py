"""Porteiro central para autorizar acoes praticas da Laylay.

Este modulo nao executa nada. Ele apenas decide se uma acao pratica
parece autorizada pelo pedido atual, por confirmacao recente ou por
contexto forte. A ideia e manter as habilidades existentes, mas evitar
que memoria antiga ou rotina solta virem execucao automatica.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable


ACOES_MUSICA = {
    "music_search",
    "musica",
    "youtube_search",
    "youtube_play",
    "playlist_play",
    "tocar_playlist",
    "tocar_playlist_shuffle",
    "playlist_shuffle",
}


def normalizar_texto(texto: str) -> str:
    bruto = str(texto or "").lower()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    sem_acento = re.sub(r"[^\w\s?]", " ", sem_acento)
    return re.sub(r"\s+", " ", sem_acento).strip()


def _parece_agradecimento_ou_elogio_curto(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    variantes = [
        "obrigado", "obrigada", "brigado", "brigada", "orbigado", "orbrigado",
        "obigado", "obridago", "valeu", "valew", "vlw", "perfeito", "amei",
        "gostei", "maravilhoso", "maravilhosa", "lindo", "linda", "fofo",
        "fofa", "incrivel", "estou te elogiando", "to te elogiando",
        "apenas um elogio", "so um elogio",
        "voce e legal", "voce e bem legal", "voce e muito legal",
        "vc e legal", "vc e bem legal", "te acho legal",
    ]
    return any(v in t for v in variantes)


def _parece_meta_conversa_curta(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    padroes = [
        r"^(ta de boa|tudo de boa|ta suave|tudo suave)(\s+lay|\s+laylay)?\??$",
        r"^(voce ta de boa|voce esta de boa|c voce ta de boa)(\s+lay|\s+laylay)?\??$",
        r"^(nao|não)\s+lay,?\s+(eu\s+)?to\s+te\s+perguntando\s+se\s+voce\s+esta\s+bem\??$",
        r"^(nao|não)\s+lay,?\s+(eu\s+)?to\s+te\s+falando\s+o\s+que\??$",
        r"^apenas\s+estou\s+te\s+perguntando\s+se\s+voce\s+esta\s+bem\??$",
        r"^o\s+que\s+eu\s+estou\s+te\s+perguntando\??$",
    ]
    return any(re.fullmatch(p, t) for p in padroes) or (
        ("estou te perguntando" in t or "to te perguntando" in t)
        and any(p in t for p in ["voce esta bem", "ta tudo bem", "tudo bem", "ta de boa", "de boa"])
    )


def texto_social_curto(texto: str) -> bool:
    """Reconhece conversa curta que nao deve herdar comando antigo."""
    t = normalizar_texto(texto)
    if not t:
        return False

    if _parece_meta_conversa_curta(t):
        return True

    palavras = t.split()
    if len(palavras) > 8:
        return False

    comandos = {
        "playlist", "musica", "toca", "toque", "coloca", "coloque",
        "abre", "abrir", "entra", "fecha", "fechar", "apaga", "apagar",
        "cria", "criar", "arquivo", "pasta", "volume", "pausa", "proxima",
        "anterior", "youtube", "google", "email", "emails",
    }
    if any(p in t for p in comandos):
        return False

    if _parece_agradecimento_ou_elogio_curto(t):
        if len(palavras) <= 8:
            return True

    padroes = [
        r"^(oi|ola|e ai|salve|bom dia|boa tarde|boa noite)(\s+lay|\s+laylay)?$",
        r"^(como voce esta|como voce ta|como ta|voce esta bem|voce ta bem|esta bem|ta bem|tudo bem|tudo numa boa|tudo na boa|de boa|ta de boa|tudo de boa|tudo na paz)(\s+lay|\s+laylay)?\??$",
        r"^(lay|laylay)\??$",
        r"^(obrigado|obrigada|valeu|vlw|brigado|brigada)(\s+lay|\s+laylay)?$",
        r"^(perfeito|amei|gostei|maravilhoso|maravilhosa|fofo|fofa|lindo|linda|incrivel|incrível)(\s+lay|\s+laylay)?$",
        r"^(perfeito\s+obrigado|perfeito\s+obrigada|valeu\s+lay|obrigado\s+lay|obrigada\s+lay|valeu\s+laylay)$",
        r"^(estou te elogiando|to te elogiando|tava te elogiando)(\s+lay|\s+laylay)?$",
        r"^(nao|não)\s+lay\s+(e|é)\s+(so|s[oó])\s+um\s+elogio$",
        r"^(nao|não)\s+lay\s+(e|é)\s+apenas\s+um\s+elogio$",
        r"^(era so|era só)\s+um\s+elogio$",
        r"^(kk+|haha+|rs+|kkkk+|relaxa|de boa|tranquilo|beleza|blz|ok|certo)$",
        r"^(nao|não)\s+lay,?\s+to\s+perguntando\s+se\s+ta\s+tudo\s+bem",
    ]
    return any(re.fullmatch(p, t) for p in padroes)


def texto_conversa_casual_sem_acao(texto: str) -> bool:
    """Reconhece falas de conversa que nao devem disparar roteadores de comando."""
    t = normalizar_texto(texto)
    if not t:
        return False
    if any(p in t for p in ["em foco", "foco", "tela cheia", "fullscreen", "maximiza", "maximizar", "pra frente", "para frente", "primeiro plano"]):
        return False
    if texto_social_curto(t):
        return True

    comandos = {
        "playlist", "musica", "toca", "toque", "coloca", "coloque", "abre", "abrir",
        "fecha", "fechar", "apaga", "apagar", "cria", "criar", "volume", "youtube",
        "google", "site", "aba", "janela", "programa", "app", "arquivo", "pasta",
        "email", "emails", "notificacao", "notificacoes", "agenda", "lembrete",
        "agendamento", "netflix", "spotify", "pesquisa", "buscar", "procura",
        "foco", "fullscreen", "maximiza", "maximizar",
    }
    if any(p in t for p in comandos):
        return False

    padroes = [
        r"^(ta de boa|tudo na paz|tudo de boa|tudo suave|ta suave)\??$",
        r"^(essa|esse)\s+.+\s+(e|eh)\s+.+$",
        r"^(eu to|eu estou)\s+te\s+perguntando\s+.+\??$",
        r"^o que eu estou te perguntando\??$",
        r"^(nao|não)\s+lay,?\s+.+$",
    ]
    if any(re.fullmatch(p, t) for p in padroes):
        return True

    palavras = t.split()
    if (
        len(palavras) <= 5
        and "http" not in t
        and not any(ch.isdigit() for ch in t)
    ):
        return True

    if re.fullmatch(r"^(eu to|eu estou)\s+.+$", t):
        return True
    if re.fullmatch(r"^(entao|então)\s+.+$", t):
        return True
    if re.fullmatch(r"^(como assim|ue|u[eé]|oxi|ata|ah ta|ah tá)\??$", t):
        return True

    if "?" in str(texto or "") and len(t.split()) <= 10:
        return True
    return False


def texto_tem_comando_explicito(texto: str) -> bool:
    """Detecta quando ha pedido pratico claro o bastante para nao ser tratado como papo."""
    t = normalizar_texto(texto)
    if not t:
        return False

    if texto_pede_playlist_explicitamente(t) or texto_pede_musica_explicitamente(t):
        return True

    if "http" in t or "www " in t:
        return True

    verbos = [
        "abre", "abrir", "abra", "fecha", "fechar", "feche", "coloca", "coloque",
        "bota", "poe", "põe", "toca", "toque", "cria", "criar", "crie",
        "apaga", "apagar", "deleta", "deletar", "remove", "remover", "exclui", "excluir",
        "maximiza", "maximizar", "organiza", "organizar", "silencia", "silenciar",
        "sincroniza", "sincronizar", "aumenta", "aumentar", "abaixa", "baixar",
        "diminui", "diminuir", "pausa", "pausar", "despausa", "retoma", "continua",
    ]
    alvos = [
        "playlist", "musica", "música", "som", "volume", "email", "emails",
        "notificacao", "notificacoes", "site", "aba", "janela", "programa", "app",
        "arquivo", "pasta", "desktop", "area de trabalho", "área de trabalho",
        "steam", "opera", "chrome", "edge", "vscode", "visual studio code",
        "youtube", "netflix", "spotify", "instagram", "whatsapp", "ifood",
        "microsoft store", "google",
    ]
    if any(v in t for v in verbos) and any(a in t for a in alvos):
        return True

    if any(x in t for x in ["tela cheia", "fullscreen", "em foco", "pra frente", "para frente", "primeiro plano"]):
        return True

    if any(x in t for x in [
        "pausa ela",
        "pausa ele",
        "pausa isso",
        "despausa ela",
        "despausa ele",
        "retoma ela",
        "retoma ele",
        "continua ela",
        "continua ele",
        "proxima musica",
        "próxima música",
        "musica anterior",
        "música anterior",
        "volta a musica",
        "volta a música",
        "volta para a de antes",
        "volta pra de antes",
        "volta pra anterior",
        "toca ela de novo",
        "repete ela",
        "repete essa",
    ]):
        return True

    if re.search(
        r"\b(?:traz|trazer|abre|abrir|coloca|colocar|bota|botar|toca|tocar|restaura|restaurar|refaz|refazer)\b.*\b(?:de volta|de novo|novamente)\b",
        t,
    ):
        return True

    if re.search(r"\b(?:pode\s+ler|pode\s+ver|le\s+eles|l[eê]\s+eles|ler\s+eles)\b", t):
        return True

    if re.search(
        r"\b(?:traz|trazer|cria|criar|faz|refaz|restaura|restaurar)\b.*\b(?:de volta|de novo|novamente)\b",
        t,
    ):
        return True

    if re.search(
        r"^\s*(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:o|a|os|as|um|uma)?\s*[a-z0-9_\-.][a-z0-9_\-.\s]{0,40}$",
        t,
    ):
        return True

    return False


def texto_conversa_contextual_sem_comando(texto: str, contexto: Dict[str, Any] | None = None) -> bool:
    """Protege continuidades de conversa para nao virarem comando por heranca torta."""
    t = normalizar_texto(texto)
    if not t:
        return False

    if texto_tem_comando_explicito(t):
        return False

    if texto_social_curto(t) or texto_conversa_casual_sem_acao(t):
        return True

    contexto = contexto if isinstance(contexto, dict) else {}
    mente = contexto.get("mente") or {}
    foco = contexto.get("foco_vivo") or {}
    ultima_habilidade = str((mente.get("ultima_habilidade") if isinstance(mente, dict) else "") or "").strip().lower()
    ultima_intencao = str((mente.get("ultima_intencao") if isinstance(mente, dict) else "") or "").strip().upper()
    ultimo_topico = normalizar_texto(str(contexto.get("ultimo_topico") or foco.get("topico") or foco.get("alvo") or "").strip())
    foco_tipo = normalizar_texto(str(foco.get("tipo") or "").strip())

    contexto_conversa = (
        foco_tipo in {"conversa", "opiniao", "opinião"}
        or ultima_habilidade in {"conversa", "opiniao", "opinião", "pesquisa"}
        or ultima_intencao in {"OPINION", "QUESTION", "CONTINUE", "WELLBEING", "PRAISE", "SEARCH"}
    )

    if any(p in t for p in [
        "faz o l", "como assim", "e porque", "e por que", "o que voce acha",
        "o que voce sacha", "qual sua opiniao", "qual sua opinião", "o que voce pensa",
    ]):
        return True

    if any(p in t for p in ["nao lay", "não lay", "a nao lay", "ah nao lay", "eu to falando", "eu estou falando"]):
        return True

    if any(p in t for p in ["lula", "presidente", "politica", "política"]) and not texto_tem_comando_explicito(t):
        return True

    respostas_humanas = [
        "sim", "claro", "claro que sim", "aham", "uhum", "isso", "isso mesmo",
        "foi sim", "veio sim", "veiuo sim", "é sim", "e sim", "nao gostei", "não gostei",
        "quero outra", "mas eu to falando", "mas eu estou falando",
    ]
    if any(t == r or t.startswith(f"{r} ") for r in respostas_humanas):
        return True if (contexto_conversa or ultimo_topico) else False

    if contexto_conversa and len(t.split()) <= 10:
        return True

    if ultimo_topico and len(t.split()) <= 10 and any(p in t for p in ["ele", "ela", "isso", "dele", "dela", "desse", "dessa"]):
        return True

    return False


def texto_bloqueia_playlist_agora(texto: str) -> bool:
    t = normalizar_texto(texto)
    if "playlist" not in t:
        return False
    negativos = [
        "sem playlist",
        "nao playlist",
        "nao quero playlist",
        "nao toca playlist",
        "nao coloca playlist",
        "chega de playlist",
        "para de playlist",
        "para com playlist",
        "corta playlist",
        "deixa playlist quieta",
        "sem musica agora",
    ]
    return any(p in t for p in negativos) or ("nao" in t and "playlist" in t)


def texto_pede_playlist_explicitamente(texto: str) -> bool:
    t = normalizar_texto(texto)
    verbos = [
        "toca", "toque", "coloca", "coloque", "abre", "abra", "abrir",
        "ouvir", "escuta", "escute", "pode playlist", "volta playlist",
    ]
    if "playlist" in t:
        return any(v in t for v in verbos)
    return bool(re.match(r"^\s*(toca|toque|coloca|coloque|abre|abra|ouvir|escuta|escute)\b\s+.+", t))


def texto_pede_musica_explicitamente(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    verbos = [
        "toca", "toque", "coloca", "coloque", "bota", "botar", "poe",
        "abre", "abra", "ouvir", "escuta", "escute", "da play",
        "procura", "pesquisa", "busca",
    ]
    termos = ["musica", "som", "playlist", "youtube", "faixa", "cancao"]
    if any(v in t for v in verbos) and any(m in t for m in termos):
        return True
    if texto_pede_playlist_explicitamente(t):
        return True
    return bool(re.match(r"^\s*(toca|toque|coloca|coloque|bota|poe|escuta|escute)\b\s+.+", t))


def texto_bem_estar_pede_musica(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    sinais = [
        "to cansado", "estou cansado", "cansado", "cansada",
        "triste", "ansioso", "ansiosa", "estressado", "estressada",
        "preciso relaxar", "quero relaxar", "dia pesado", "to mal",
    ]
    return any(s in t for s in sinais)


def texto_pede_repeticao_curta(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    if len(t.split()) > 6:
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


def _ultimas_mensagens_usuario(mensagens: Iterable[Any], limite: int = 4) -> list[str]:
    users: list[str] = []
    try:
        for msg in list(mensagens or [])[-12:]:
            if isinstance(msg, dict) and msg.get("role") == "user":
                conteudo = str(msg.get("content") or "").strip()
                if conteudo:
                    users.append(conteudo)
    except Exception:
        return []
    return users[-limite:]


def _ultima_intencao_contextual(contexto: Dict[str, Any]) -> str:
    mente = contexto.get("mente") or {}
    if isinstance(mente, dict):
        return str(mente.get("ultima_intencao") or "").strip().upper()
    return ""


def _ultima_habilidade_contextual(contexto: Dict[str, Any]) -> str:
    mente = contexto.get("mente") or {}
    if isinstance(mente, dict):
        return str(mente.get("ultima_habilidade") or "").strip().lower()
    return ""


def _continua_pedido_musical_recente(texto: str, contexto: Dict[str, Any]) -> bool:
    if not texto_pede_repeticao_curta(texto):
        return False
    ultima_intencao = _ultima_intencao_contextual(contexto)
    ultima_habilidade = _ultima_habilidade_contextual(contexto)
    if ultima_intencao in {"PLAYLIST_PLAY", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE", "MUSIC_SEARCH"}:
        return True
    if ultima_habilidade in {"playlist", "midia"}:
        return True
    users = _ultimas_mensagens_usuario(contexto.get("messages") or [])
    if not users:
        return False
    ultimo_pedido = users[-1]
    return texto_pede_playlist_explicitamente(ultimo_pedido) or texto_pede_musica_explicitamente(ultimo_pedido)


def pode_sugerir_musica(contexto: Dict[str, Any]) -> bool:
    """Sugestao musical precisa nascer do momento, nao de rotina solta."""
    if bool(contexto.get("playlist_bloqueada")):
        return False
    users = _ultimas_mensagens_usuario(contexto.get("messages") or [])
    if not users:
        return False
    if texto_social_curto(users[-1]):
        return False
    return any(texto_pede_musica_explicitamente(u) or texto_bem_estar_pede_musica(u) for u in users)


def autorizar_acao_pratica(
    acao: str,
    texto: str = "",
    contexto: Dict[str, Any] | None = None,
    *,
    confirmado: bool = False,
    origem: str = "",
) -> Dict[str, Any]:
    """Autoriza ou bloqueia uma acao sem executar nada."""
    contexto = contexto if isinstance(contexto, dict) else {}
    acao_norm = str(acao or "").strip().lower()
    texto_atual = str(texto or "").strip()

    if confirmado:
        return {"permitido": True, "motivo": "confirmacao explicita", "categoria": "confirmado"}

    if contexto.get("playlist_bloqueada") and acao_norm in ACOES_MUSICA:
        return {"permitido": False, "motivo": "playlist bloqueada pelo usuario", "categoria": "musica"}

    if acao_norm in {"playlist_play", "tocar_playlist", "tocar_playlist_shuffle", "playlist_shuffle"}:
        permitido = texto_pede_playlist_explicitamente(texto_atual) or _continua_pedido_musical_recente(texto_atual, contexto)
        return {
            "permitido": permitido,
            "motivo": "pedido explicito de playlist" if permitido else "sem pedido explicito de playlist ou continuidade recente",
            "categoria": "playlist",
        }

    if acao_norm in {"music_search", "musica", "youtube_search"}:
        permitido = texto_pede_musica_explicitamente(texto_atual) or _continua_pedido_musical_recente(texto_atual, contexto)
        return {
            "permitido": permitido,
            "motivo": "pedido explicito de musica" if permitido else "sem pedido explicito de musica ou continuidade recente",
            "categoria": "musica",
        }

    if acao_norm == "youtube_play":
        if contexto.get("playlist_ativa") or contexto.get("auto_next_playlist"):
            return {"permitido": True, "motivo": "continuidade de playlist ativa", "categoria": "playlist"}
        permitido = (
            texto_pede_musica_explicitamente(texto_atual)
            or texto_pede_playlist_explicitamente(texto_atual)
            or _continua_pedido_musical_recente(texto_atual, contexto)
        )
        return {
            "permitido": permitido,
            "motivo": "pedido explicito de reproducao" if permitido else "sem pedido explicito de reproducao ou continuidade recente",
            "categoria": "musica",
        }

    return {"permitido": True, "motivo": "acao fora do escopo sensivel atual", "categoria": "geral"}
