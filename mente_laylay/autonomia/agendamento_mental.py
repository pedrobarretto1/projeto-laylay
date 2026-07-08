"""Agenda contextual e tentativa de intencao pela IA da Laylay."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict, Optional


def resumo_agendamentos_para_prompt(
    agendamentos_load_cb: Callable[[], list],
    limit: int = 6,
) -> str:
    try:
        lista = agendamentos_load_cb()
        ativos = [a for a in lista if isinstance(a, dict) and a.get("ativo", True)]
        if not ativos:
            return "Agendamentos ativos: nenhum."

        agora = time.time()
        itens = []
        for ag in ativos:
            nome = str(ag.get("nome") or ag.get("descricao") or ag.get("id") or "compromisso").strip()
            tipo = str(ag.get("tipo") or "once").strip().lower()
            if tipo == "once" and ag.get("ts_execucao"):
                try:
                    delta_min = max(0, int((float(ag.get("ts_execucao")) - agora) / 60))
                    itens.append(f"{nome} em {delta_min} min")
                except Exception:
                    itens.append(nome)
            elif ag.get("hora"):
                dias = ag.get("dias")
                if isinstance(dias, list) and dias:
                    itens.append(f"{nome} às {ag.get('hora')} ({','.join(map(str, dias))})")
                else:
                    itens.append(f"{nome} às {ag.get('hora')}")
            else:
                itens.append(nome)
        itens = itens[:limit]
        return "Agendamentos ativos: " + "; ".join(itens)
    except Exception:
        return "Agendamentos ativos: indisponível."


def extrair_agendamento_local(texto: str, normalizar_texto_cb: Callable[[str], str]) -> Optional[dict]:
    bruto = str(texto or "").strip()
    if not bruto:
        return None
    t = normalizar_texto_cb(bruto)
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return None
    t = re.sub(r"\b(\d{1,2})\s*[h:]\s*(\d{2})\b", r"\1:\2", t)
    t = re.sub(r"\b(\d{1,2})\s*horas?\s*(\d{2})\b", r"\1:\2", t)

    if any(p in t for p in ["tenho algum compromisso", "tem algum compromisso", "meu compromisso", "compromissos de hoje", "agenda de hoje", "ver agenda", "mostrar agenda", "listar agenda", "me mostra os compromissos", "pode ver se tem", "ver se tem"]):
        return {"intent": "LISTAR_AGENDAMENTOS", "params": {}}

    if any(p in t for p in ["cancela", "cancelar", "remove", "remover", "apaga", "apagar"]) and any(p in t for p in ["agendamento", "lembrete", "compromisso", "compromissos", "agenda"]):
        alvo = re.sub(r"^(cancela|cancelar|remove|remover|apaga|apagar)\s+", "", t).strip()
        alvo = re.sub(r"\b(agendamento|lembrete|compromisso|compromissos|agenda)\b", " ", alvo).strip()
        return {"intent": "CANCELAR_AGENDAMENTO", "params": {"alvo": alvo or ""}}

    if any(p in t for p in ["me lembra", "lembra de", "lembra pra", "lembra às", "lembra as", "me avisa", "avisa", "marca", "agende", "agendar", "agenda"]):
        minutos = None
        hora_alvo = ""
        texto_evento = t

        m_min = re.search(r"\b(?:em\s+)?(\d{1,3})\s*(?:min|mins|minuto|minutos)\b", t)
        if m_min:
            try:
                minutos = int(m_min.group(1))
            except Exception:
                minutos = None
            texto_evento = re.sub(r"\b(?:em\s+)?\d{1,3}\s*(?:min|mins|minuto|minutos)\b", " ", texto_evento).strip()

        if minutos is None:
            m_hora = re.search(r"\b(?:às|as|a)\s*(\d{1,2}:\d{2})\b", t)
            if not m_hora:
                m_hora = re.search(r"\b(\d{1,2}:\d{2})\b", t)
            if m_hora:
                hora_alvo = m_hora.group(1)
                texto_evento = texto_evento.replace(hora_alvo, " ")
                texto_evento = re.sub(r"\b(?:às|as|a)\s*", " ", texto_evento).strip()

        for prefixo in [
            "me lembra de", "lembra de", "me lembra pra", "lembra pra",
            "me avisa de", "me avisa pra", "agende", "agenda", "marca",
            "marca pra mim", "agendar", "lembra às", "lembra as",
        ]:
            texto_evento = re.sub(rf"^\s*{re.escape(prefixo)}\s*", " ", texto_evento, flags=re.IGNORECASE)
        texto_evento = re.sub(r"\b(de|do|da|para|pra|pro|no|na|em)\b", " ", texto_evento)
        texto_evento = re.sub(r"\s+", " ", texto_evento).strip(" .,!?:;")
        descricao = texto_evento or "lembrete"

        if minutos is not None or hora_alvo:
            params = {"descricao": descricao}
            if minutos is not None:
                params["minutos"] = minutos
            if hora_alvo:
                params["hora_alvo"] = hora_alvo
            return {"intent": "AGENDAR_LEMBRETE", "params": params}

    return None


def tentar_intencao_contextual_ai(
    texto: str,
    contexto_mental_ativo_cb: Callable[[], bool],
    texto_depende_de_contexto_cb: Callable[[str], bool],
    analisar_intencao_cb: Callable[[str], Any],
) -> Optional[dict]:
    t = str(texto or "").strip()
    if not t:
        return None
    if not contexto_mental_ativo_cb():
        return None
    if len(t.split()) > 10 and not texto_depende_de_contexto_cb(t):
        return None

    resultado = analisar_intencao_cb(t)
    if not isinstance(resultado, dict):
        return None

    intent = str(resultado.get("intent") or "").upper().strip()
    if intent in {"PLAYLIST_ADD", "PLAYLIST_LIST", "PLAYLIST_PLAY", "MUSIC_SEARCH", "OPEN_URL", "AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO"}:
        return resultado
    return None
