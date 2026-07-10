"""Validadores de continuidade conversacional da Laylay."""

from __future__ import annotations

import random
import re
import time
from typing import Callable, Iterable


def topico_memoria_valido(topico: str, normalizar_texto_curto: Callable[[str], str]) -> bool:
    t = normalizar_texto_curto(topico)
    if not t:
        return False
    genericos = {
        "playlist", "musica", "música", "youtube", "netflix", "ia", "pc",
        "conversa", "chat", "hora", "hoje", "agora", "isso", "essa", "esse",
    }
    if t in genericos:
        return False
    if len(re.findall(r"[a-z0-9_-]{3,}", t)) <= 1 and t not in {"anime", "manga", "filme", "serie", "jogo", "trabalho"}:
        return False
    return True


def extrair_topico_conversa(texto: str, topico_anterior: str = "", *, normalizar_texto_curto: Callable[[str], str]) -> str:
    """Extrai um tema curto para manter a memória de conversa viva."""
    t = normalizar_texto_curto(texto)
    if not t:
        return str(topico_anterior or "").strip()

    if any(p in t for p in [
        "homem aranha", "spider man", "spiderman", "peter parker", "marvel", "dc",
        "anime", "manga", "filme", "serie", "série", "jogo", "games", "gaming",
        "trabalho", "pc", "ia", "inteligencia artificial", "inteligência artificial",
        "musica", "música", "playlist", "youtube", "netflix", "homem-aranha",
    ]):
        for tema in [
            "homem aranha", "peter parker", "marvel", "anime", "manga", "filme", "serie",
            "jogo", "trabalho", "pc", "ia", "música", "youtube", "netflix",
        ]:
            if tema in t:
                return tema

    if any(p in t for p in ["ele", "ela", "isso", "fato", "verdade", "kkk", "haha", "rs", "boa", "verdade"]):
        return str(topico_anterior or "").strip()

    if any(p in t for p in ["playlist", "musica", "música", "youtube", "netflix", "ia", "pc"]):
        if len(re.findall(r"[a-z0-9_-]{3,}", t)) <= 2:
            return str(topico_anterior or "").strip()

    stop = {
        "voce", "você", "gosta", "curte", "acha", "pensa", "prefere", "me", "disso",
        "daquilo", "sobre", "mais", "muito", "bem", "tipo", "qual", "como", "porque",
        "pq", "pra", "para", "que", "isso", "essa", "esse", "aquela", "aquele",
        "hoje", "ontem", "agora", "aqui", "ali", "pra", "pro", "vai", "ser", "tem",
        "tenho", "tá", "ta", "bom", "ok", "certo", "verdade", "fato",
    }
    tokens = [tok for tok in re.findall(r"[a-z0-9_-]{3,}", t) if tok not in stop]
    if not tokens:
        return str(topico_anterior or "").strip()
    topico = " ".join(tokens[:3]).strip()
    if len(topico) < 3:
        return str(topico_anterior or "").strip()
    return topico


def atualizar_memoria_topicos(
    *,
    texto_usuario: str,
    topicos_recentes: list,
    ultimo_topico: str,
    normalizar_texto_curto: Callable[[str], str],
    limite: int = 8,
) -> tuple[list, str, float]:
    """Atualiza a memória curta de tópicos recentes."""
    texto_base = str(texto_usuario or "").strip()
    topico = extrair_topico_conversa(
        texto_base,
        ultimo_topico,
        normalizar_texto_curto=normalizar_texto_curto,
    )
    if not topico:
        return list(topicos_recentes or []), str(ultimo_topico or "").strip(), 0.0

    agora = time.time()
    recentes = [t for t in list(topicos_recentes or []) if str(t).strip().lower() != topico.lower()]
    recentes.append(topico)
    if len(recentes) > limite:
        recentes = recentes[-limite:]
    return recentes, topico, agora


def formatar_topicos_conversa(ultimo_topico: str, topicos_recentes: list) -> str:
    linhas = []
    if ultimo_topico:
        linhas.append(f"Tópico ativo: {ultimo_topico}")
    if topicos_recentes:
        linhas.append("Tópicos recentes: " + "; ".join(topicos_recentes[-5:]))
    return "\n".join(linhas)


def texto_responde_pergunta_aberta(
    texto_usuario: str,
    *,
    pergunta_aberta: dict | None,
    normalizar_texto_curto: Callable[[str], str],
    texto_parece_resposta_curta_a_pergunta: Callable[[str, Callable[[str], str]], bool],
    bloqueadores: Iterable[Callable[[str], object]] = (),
) -> bool:
    """Decide se a fala atual responde uma pergunta recente em vez de iniciar comando."""
    if not pergunta_aberta:
        return False

    t = str(texto_usuario or "").strip()
    if not t:
        return False

    for bloqueador in bloqueadores or ():
        if not callable(bloqueador):
            continue
        try:
            if bloqueador(t):
                return False
        except Exception:
            continue

    try:
        return bool(texto_parece_resposta_curta_a_pergunta(t, normalizar_texto_curto))
    except Exception:
        return False


def resolver_pergunta_curta_contextual_intencao(
    texto_usuario: str,
    *,
    normalizar_texto_curto: Callable[[str], str],
    contexto_recente_indica_email: Callable[[], bool] | None = None,
) -> dict | None:
    """Converte respostas curtas dependentes do contexto em intencoes seguras."""
    try:
        t = str(normalizar_texto_curto(texto_usuario) or "").strip()
    except Exception:
        t = str(texto_usuario or "").strip().lower()
    if not t or len(t.split()) > 10:
        return None

    pergunta_email = any(p in t for p in [
        "o que eles falam",
        "o que eles me falam",
        "o que os emails falam",
        "o que falam",
        "me fala deles",
        "fala deles",
        "pode ler",
        "pode ver",
        "le eles",
        "lê eles",
        "ler eles",
    ])
    if pergunta_email and callable(contexto_recente_indica_email):
        try:
            if contexto_recente_indica_email():
                return {"intent": "EMAIL_READ", "params": {}}
        except Exception:
            return None

    return None


def responder_pergunta_aberta(
    texto_usuario: str,
    *,
    pergunta_aberta: dict | None,
    foco_vivo: dict | None = None,
    normalizar_texto_curto: Callable[[str], str],
    responder_conversa_curta_por_tipo: Callable[[str, str], str] | None = None,
    ajustar_fala_por_horario: Callable[[str, str], str] | None = None,
) -> str:
    """Gera uma resposta coerente para a pendencia de pergunta aberta."""
    pergunta = dict(pergunta_aberta or {})
    pergunta_txt = str(pergunta.get("pergunta") or "").strip()
    topico = str(pergunta.get("topico") or "").strip()
    try:
        t = str(normalizar_texto_curto(texto_usuario) or "").strip()
    except Exception:
        t = str(texto_usuario or "").strip().lower()

    def _ajustar(fala: str) -> str:
        if callable(ajustar_fala_por_horario):
            try:
                return str(ajustar_fala_por_horario(fala, texto_usuario) or fala)
            except Exception:
                pass
        return fala

    if any(p in t for p in ["sim", "pode", "quero", "bora", "vai", "manda", "claro", "aham", "uhum", "isso", "isso mesmo", "é sim", "e sim", "pode ser"]):
        foco = dict(foco_vivo or {})
        foco_tipo = str(foco.get("tipo") or "").lower()
        foco_topico = str(foco.get("topico") or foco.get("alvo") or topico or "").strip()
        if foco_tipo in {"opiniao", "opinião", "conversa"} and foco_topico and callable(responder_conversa_curta_por_tipo):
            try:
                return str(responder_conversa_curta_por_tipo("OPINION", f"o que voce acha de {foco_topico}?") or "").strip()
            except Exception:
                pass
        if topico:
            return _ajustar(random.choice([
                f"Fechado. Então seguimos por {topico}.",
                f"Beleza, peguei: é {topico}. Vou nessa linha.",
                f"Aí sim. Continuo por {topico}, sem largar o fio.",
            ]))
        return _ajustar(random.choice([
            "Fechado. Peguei tua resposta e sigo nesse caminho.",
            "Beleza, então vamos por aí.",
            "Tá, entendi o sim. Vou continuar nessa linha.",
        ]))

    if any(p in t for p in ["nao", "não", "agora nao", "agora não", "melhor nao", "melhor não"]):
        return _ajustar(random.choice([
            "Tranquilo, deixo isso de lado então.",
            "Beleza, sem forçar. Guardei a ideia no bolso.",
            "Tá, não mexo nisso agora.",
        ]))

    if any(p in t for p in ["bem", "de boa", "tranquilo", "tranquila", "suave", "otimo", "ótimo", "legal"]):
        return _ajustar(random.choice([
            "Que bom. Aí meu circuito até respira mais leve.",
            "Aí sim, gosto de te ouvir assim.",
            "Bom saber. Então seguimos com a energia um pouco mais bonita.",
        ]))

    if any(p in t for p in ["mal", "cansado", "cansada", "triste", "mais ou menos", "indo"]):
        return _ajustar(random.choice([
            "Entendi. Então eu baixo um pouco o ritmo e fico contigo sem apertar.",
            "Pego o clima. Se quiser, a gente vai mais devagar agora.",
            "Tá, senti esse peso aí. Posso ficar no modo companhia, sem te cobrar nada.",
        ]))

    if pergunta_txt:
        return _ajustar(random.choice([
            "Peguei tua resposta para o que eu perguntei. Vou considerar isso no assunto.",
            "Entendi. Isso responde aquela minha pergunta, então não vou puxar outro caminho do nada.",
            "Tá, conectei com minha pergunta anterior. Seguimos por esse fio.",
        ]))

    return _ajustar("Entendi. Vou seguir por esse fio.")
