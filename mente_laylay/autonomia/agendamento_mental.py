"""Agenda contextual e tentativa de intencao pela IA da Laylay."""

from __future__ import annotations

import ctypes
import datetime as _dt
import json
import os
import re
import threading
import time
from typing import Any, Callable, Dict, Optional


class AgendaRuntime:
    """Runtime da agenda mantendo execucao, persistencia e loop em um modulo."""

    def __init__(
        self,
        arquivo: str,
        *,
        falar_cb: Callable[[str, str, int], Any],
        abrir_programa_cb: Callable[[str], Any],
        enviar_pc_b_cb: Callable[[dict], Any],
        enviar_chrome_local_cb: Callable[[dict], Any],
        executar_exec_cb: Callable[[str, str], Any],
        time_cb: Callable[[], float] = time.time,
        now_cb: Callable[[], _dt.datetime] = _dt.datetime.now,
        sleep_cb: Callable[[float], Any] = time.sleep,
        thread_factory: Callable[..., Any] = threading.Thread,
        log: Callable[[str], Any] = print,
    ):
        self.arquivo = arquivo
        self.falar_cb = falar_cb
        self.abrir_programa_cb = abrir_programa_cb
        self.enviar_pc_b_cb = enviar_pc_b_cb
        self.enviar_chrome_local_cb = enviar_chrome_local_cb
        self.executar_exec_cb = executar_exec_cb
        self.time_cb = time_cb
        self.now_cb = now_cb
        self.sleep_cb = sleep_cb
        self.thread_factory = thread_factory
        self.log = log
        self._dia_map = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4, "sab": 5, "dom": 6}
        self._disparados: set[str] = set()

    def load(self) -> list:
        try:
            if os.path.exists(self.arquivo):
                with open(self.arquivo, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
        except Exception as e:
            self.log(f"[AGENDA] Erro ao carregar: {e}")
        return []

    def save(self, lista: list):
        try:
            os.makedirs(os.path.dirname(self.arquivo), exist_ok=True)
            with open(self.arquivo, "w", encoding="utf-8") as f:
                json.dump(lista, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"[AGENDA] Erro ao salvar: {e}")

    def disparar(self, ag: dict):
        """Executa um agendamento: fala o texto e roda os comandos opcionais."""
        descricao = str(ag.get("descricao") or "Pedro, chegou a hora!").strip()
        comandos_disparo = ag.get("comandos_no_disparo") or []
        nome = str(ag.get("nome") or ag.get("id", ""))[:30]
        self.log(f"\n⏰ [AGENDA] Disparando: '{nome}' — {descricao}")
        try:
            self.falar_cb(descricao, "calma", 1)
        except Exception as e:
            self.log(f"[AGENDA] Erro ao falar: {e}")

        if isinstance(comandos_disparo, list) and comandos_disparo:
            th = self.thread_factory(target=lambda: self._executar_comandos(comandos_disparo), daemon=True)
            th.start()

    def _executar_comandos(self, comandos_disparo: list):
        for cmd in comandos_disparo:
            if not isinstance(cmd, dict):
                continue
            acao = str(cmd.get("acao", "")).strip()
            alvo = str(cmd.get("alvo", "")).strip()
            try:
                destino = str(cmd.get("target", "pc_a")).lower().strip()

                if acao == "open_app":
                    if destino == "pc_b":
                        self.enviar_pc_b_cb({"action": "open_app", "app": alvo})
                    else:
                        self.abrir_programa_cb(alvo)

                elif acao in ("open_url", "youtube_search"):
                    if acao == "youtube_search":
                        msg_payload = {"action": "youtube_search", "query": alvo}
                        if destino == "pc_b":
                            url_yt = "https://www.youtube.com/results?search_query=" + alvo.replace(" ", "+")
                            self.enviar_pc_b_cb({"action": "open_url", "url": url_yt})
                        else:
                            self.enviar_chrome_local_cb(msg_payload)
                    else:
                        msg_payload = {"action": "open_url", "url": alvo}
                        if destino == "pc_b":
                            self.enviar_pc_b_cb(msg_payload)
                        else:
                            self.enviar_chrome_local_cb(msg_payload)

                elif acao == "notificar":
                    if destino == "pc_b":
                        self.enviar_pc_b_cb({"action": "notificar", "alvo": alvo})
                    else:
                        ctypes.windll.user32.MessageBoxW(0, alvo, "Laylay", 64)

                elif acao == "tocar_playlist":
                    if destino == "pc_b":
                        alvo = alvo + " no pc b"
                    self.executar_exec_cb("TOCAR_PLAYLIST", alvo)

            except Exception as exc:
                self.log(f"[AGENDA] Erro ao executar cmd '{acao}': {exc}")

    def processar_ciclo(self) -> bool:
        agora = self.now_cb()
        hora_atual = agora.strftime("%H:%M")
        dia_semana = agora.weekday()
        lista = self.load()
        modificado = False

        for ag in list(lista):
            if not isinstance(ag, dict) or not ag.get("ativo", True):
                continue
            tipo = str(ag.get("tipo", "once"))
            ag_id = str(ag.get("id", ""))

            if tipo == "once":
                ts_exec = ag.get("ts_execucao", 0)
                if ts_exec and self.time_cb() >= ts_exec and ag_id not in self._disparados:
                    self._disparados.add(ag_id)
                    self.disparar(ag)
                    ag["ativo"] = False
                    modificado = True
            elif tipo in ("daily", "weekly"):
                hora_ag = str(ag.get("hora", "")).strip()
                if hora_ag != hora_atual:
                    continue
                chave = f"{ag_id}_{agora.strftime('%Y-%m-%d')}"
                if chave in self._disparados:
                    continue
                dias = ag.get("dias", "todos")
                if dias == "todos" or tipo == "daily":
                    disparar = True
                elif isinstance(dias, list):
                    disparar = dia_semana in [self._dia_map.get(str(d).lower(), -1) for d in dias]
                else:
                    disparar = True
                if disparar:
                    self._disparados.add(chave)
                    self.disparar(ag)

        if modificado:
            self.save(lista)
        return modificado

    def daemon(self):
        """Thread daemon que verifica agendamentos a cada 30 segundos."""
        self.log("⏰ [AGENDA] Thread de agendamentos iniciada.")
        while True:
            try:
                self.processar_ciclo()
            except Exception as exc:
                self.log(f"[AGENDA] Erro no daemon: {exc}")
            self.sleep_cb(30)


def criar_agenda_runtime(*args, **kwargs) -> AgendaRuntime:
    return AgendaRuntime(*args, **kwargs)


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
