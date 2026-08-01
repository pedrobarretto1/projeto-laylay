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
        executar_comando_conteudo_cb: Callable[[str, str], Any],
        executar_intencao_cb: Callable[[Dict[str, Any], str], Any] | None = None,
        time_cb: Callable[[], float] = time.time,
        now_cb: Callable[[], _dt.datetime] = _dt.datetime.now,
        sleep_cb: Callable[[float], Any] = time.sleep,
        thread_factory: Callable[..., Any] = threading.Thread,
        log: Callable[[str], Any] = print,
        tolerancia_recorrente_s: float = 3600.0,
        retry_base_s: float = 15.0,
        sincronizar_despertares_cb: Callable[[list], Any] | None = None,
        notificar_evento_cb: Callable[[dict, str], bool] | None = None,
        stop_event: threading.Event | None = None,
    ):
        self.arquivo = arquivo
        self.falar_cb = falar_cb
        self.abrir_programa_cb = abrir_programa_cb
        self.enviar_pc_b_cb = enviar_pc_b_cb
        self.enviar_chrome_local_cb = enviar_chrome_local_cb
        self.executar_comando_conteudo_cb = executar_comando_conteudo_cb
        self.executar_intencao_cb = executar_intencao_cb
        self.time_cb = time_cb
        self.now_cb = now_cb
        self.sleep_cb = sleep_cb
        self.thread_factory = thread_factory
        self.log = log
        self.tolerancia_recorrente_s = max(60.0, float(tolerancia_recorrente_s))
        self.retry_base_s = max(1.0, float(retry_base_s))
        self.sincronizar_despertares_cb = sincronizar_despertares_cb
        self.notificar_evento_cb = notificar_evento_cb
        self._arquivo_lock = threading.RLock()
        self._dia_map = {"seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4, "sab": 5, "dom": 6}
        self._disparados: set[str] = set()
        self.stop_event = stop_event or threading.Event()
        self._diagnostico = {
            "leituras": 0,
            "gravacoes": 0,
            "falhas_persistencia": 0,
            "disparos_confirmados": 0,
            "disparos_falhos": 0,
            "retries": 0,
            "daemon_ativo": False,
            "ultimo_erro": "",
            "ultimo_disparo_ts": 0.0,
        }

    def load(self) -> list:
        with self._arquivo_lock:
            self._diagnostico["leituras"] += 1
            try:
                if os.path.exists(self.arquivo):
                    with open(self.arquivo, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return data if isinstance(data, list) else []
            except Exception as e:
                self._diagnostico["falhas_persistencia"] += 1
                self._diagnostico["ultimo_erro"] = type(e).__name__
                self.log(f"[AGENDA] Erro ao carregar: {e}")
        return []

    def save(self, lista: list) -> bool:
        with self._arquivo_lock:
            temporario = ""
            try:
                pasta = os.path.dirname(self.arquivo) or "."
                os.makedirs(pasta, exist_ok=True)
                temporario = os.path.join(
                    pasta,
                    f".{os.path.basename(self.arquivo)}.{os.getpid()}.{threading.get_ident()}.tmp",
                )
                with open(temporario, "w", encoding="utf-8") as f:
                    json.dump(lista, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temporario, self.arquivo)
                self._diagnostico["gravacoes"] += 1
                if callable(self.sincronizar_despertares_cb):
                    try:
                        self.sincronizar_despertares_cb(lista)
                    except Exception as erro_despertar:
                        self.log(f"[AGENDA:WINDOWS] Agenda salva, mas o despertar não foi sincronizado: {erro_despertar}")
                return True
            except Exception as e:
                self._diagnostico["falhas_persistencia"] += 1
                self._diagnostico["ultimo_erro"] = type(e).__name__
                self.log(f"[AGENDA] Erro ao salvar: {e}")
                return False
            finally:
                if temporario and os.path.exists(temporario):
                    try:
                        os.remove(temporario)
                    except OSError:
                        pass

    def transacionar(self, mutador: Callable[[list], Any]) -> bool:
        """Aplica leitura, alteração e gravação sob um único lock."""
        if not callable(mutador):
            return False
        with self._arquivo_lock:
            lista = self.load()
            mutador(lista)
            return self.save(lista)

    def fala_estilosa(self, ativos: list) -> str:
        lista = ativos if isinstance(ativos, list) else []
        if not lista:
            return "Nenhum agendamento ativo. Sua agenda está limpa, o que é suspeito vindo de você."
        nomes = []
        for agendamento in lista[:4]:
            if not isinstance(agendamento, dict):
                continue
            nome = str(
                agendamento.get("nome")
                or agendamento.get("descricao")
                or agendamento.get("id")
                or "compromisso misterioso"
            ).strip()
            hora = str(agendamento.get("hora") or "").strip()
            nomes.append(f"{nome} às {hora}" if hora else nome)
        if len(lista) == 1:
            item = nomes[0] if nomes else "compromisso misterioso"
            return f"Você tem um agendamento ativo: {item}. Pouco caos, por enquanto."
        extra = len(lista) - len(nomes)
        fim = f" E mais {extra} no rodapé da bagunça." if extra > 0 else ""
        return f"Você tem {len(lista)} agendamentos ativos. Os principais: {', '.join(nomes)}.{fim}"

    def retrato_para_mente(self, _texto: str = "") -> dict[str, Any]:
        """Resume a agenda sem expor payloads executáveis ou estrutura bruta."""
        lista = self.load()
        ativos = []
        inativos = 0
        for item in lista:
            if not isinstance(item, dict):
                continue
            if not bool(item.get("ativo", True)):
                inativos += 1
                continue
            nome = str(
                item.get("nome") or item.get("descricao") or "compromisso"
            ).strip()[:100]
            tipo = str(item.get("tipo") or "once").strip().lower()
            quando = str(item.get("hora") or "").strip()
            if tipo == "once" and item.get("ts_execucao"):
                try:
                    quando = _dt.datetime.fromtimestamp(
                        float(item["ts_execucao"])
                    ).strftime("%d/%m/%Y às %H:%M")
                except (TypeError, ValueError, OSError):
                    quando = "horário registrado"
            dias = item.get("dias")
            if isinstance(dias, list) and dias:
                quando = (quando + " em " + ", ".join(map(str, dias))).strip()
            ativos.append({"nome": nome, "tipo": tipo, "quando": quando})
        return {
            "agendamentos": ativos[:20],
            "total_ativos": len(ativos),
            "total_inativos": inativos,
        }

    def disparar(self, ag: dict) -> bool:
        """Executa um agendamento: fala o texto e roda os comandos opcionais."""
        descricao = str(ag.get("descricao") or "Chegou a hora!").strip()
        comandos_disparo = ag.get("comandos_no_disparo") or []
        intencao_disparo = ag.get("intencao_no_disparo")
        nome = str(ag.get("nome") or ag.get("id", ""))[:30]
        self.log(f"\n⏰ [AGENDA] Disparando: '{nome}' — {descricao}")
        if isinstance(intencao_disparo, dict) and callable(self.executar_intencao_cb):
            texto_original = str(ag.get("texto_original") or descricao).strip()
            return self._executar_intencao_agendada(intencao_disparo, texto_original)
        entregue_central = False
        if callable(self.notificar_evento_cb):
            try:
                entregue_central = bool(self.notificar_evento_cb(dict(ag), descricao))
            except Exception as e:
                self.log(f"[AGENDA] Central de notificações indisponível: {type(e).__name__}")
        if not entregue_central:
            try:
                self.falar_cb(descricao, "calma", 1)
            except Exception as e:
                self.log(f"[AGENDA] Erro ao falar: {e}")
                return False

        if isinstance(comandos_disparo, list) and comandos_disparo:
            th = self.thread_factory(target=lambda: self._executar_comandos(comandos_disparo), daemon=True)
            th.start()
        return True

    def _executar_intencao_agendada(self, intencao: Dict[str, Any], texto_original: str) -> bool:
        try:
            ok = bool(self.executar_intencao_cb(dict(intencao), texto_original))
            self.log(f"⏰ [AGENDA:RESULTADO] intent={intencao.get('intent')} executou={ok}")
            return ok
        except Exception as exc:
            self.log(f"[AGENDA] Erro ao executar intenção agendada: {exc}")
            return False

    def _registrar_falha(self, ag: dict, agora_ts: float) -> None:
        tentativas = max(0, int(ag.get("tentativas_falhas") or 0)) + 1
        atraso = min(300.0, self.retry_base_s * (2 ** min(tentativas - 1, 5)))
        ag["tentativas_falhas"] = tentativas
        ag["proxima_tentativa_ts"] = agora_ts + atraso
        ag["ultimo_erro_ts"] = agora_ts
        self._diagnostico["disparos_falhos"] += 1
        self._diagnostico["retries"] += 1
        self._diagnostico["ultimo_erro"] = "disparo_nao_confirmado"
        self.log(f"⏰ [AGENDA] execução não confirmada; nova tentativa em {int(atraso)}s")

    @staticmethod
    def _limpar_falhas(ag: dict) -> None:
        for chave in ("tentativas_falhas", "proxima_tentativa_ts", "ultimo_erro_ts"):
            ag.pop(chave, None)

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
                    self.executar_comando_conteudo_cb("TOCAR_PLAYLIST", alvo)

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
                agora_ts = self.time_cb()
                proxima = float(ag.get("proxima_tentativa_ts") or 0.0)
                if ts_exec and agora_ts >= ts_exec and agora_ts >= proxima and ag_id not in self._disparados:
                    if self.disparar(ag):
                        self._diagnostico["disparos_confirmados"] += 1
                        self._diagnostico["ultimo_disparo_ts"] = agora_ts
                        self._disparados.add(ag_id)
                        self._limpar_falhas(ag)
                        ag["ativo"] = False
                    else:
                        self._registrar_falha(ag, agora_ts)
                    modificado = True
            elif tipo in ("daily", "weekly"):
                hora_ag = str(ag.get("hora", "")).strip()
                try:
                    hora, minuto = map(int, hora_ag.split(":"))
                    instante_agendado = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
                    atraso_s = (agora - instante_agendado).total_seconds()
                except (TypeError, ValueError):
                    continue
                if atraso_s < 0 or atraso_s > self.tolerancia_recorrente_s:
                    continue
                data_atual = agora.strftime("%Y-%m-%d")
                chave = f"{ag_id}_{data_atual}"
                if chave in self._disparados or str(ag.get("ultimo_disparo_data") or "") == data_atual:
                    continue
                dias = ag.get("dias", "todos")
                if dias == "todos" or tipo == "daily":
                    disparar = True
                elif isinstance(dias, list):
                    disparar = dia_semana in [self._dia_map.get(str(d).lower(), -1) for d in dias]
                else:
                    disparar = True
                if disparar:
                    proxima = float(ag.get("proxima_tentativa_ts") or 0.0)
                    if self.time_cb() < proxima:
                        continue
                    if self.disparar(ag):
                        self._diagnostico["disparos_confirmados"] += 1
                        self._diagnostico["ultimo_disparo_ts"] = self.time_cb()
                        self._disparados.add(chave)
                        self._limpar_falhas(ag)
                        ag["ultimo_disparo_data"] = data_atual
                    else:
                        self._registrar_falha(ag, self.time_cb())
                    modificado = True

        if modificado:
            self.save(lista)
        return modificado

    def daemon(self):
        """Thread daemon que verifica agendamentos com precisão de poucos segundos."""
        self._diagnostico["daemon_ativo"] = True
        self.log("⏰ [AGENDA] Thread de agendamentos iniciada.")
        try:
            while not self.stop_event.is_set():
                try:
                    self.processar_ciclo()
                except Exception as exc:
                    self._diagnostico["ultimo_erro"] = type(exc).__name__
                    self.log(f"[AGENDA] Erro no daemon: {exc}")
                if self.stop_event.wait(5):
                    break
        finally:
            self._diagnostico["daemon_ativo"] = False

    def encerrar(self) -> None:
        self.stop_event.set()

    def diagnostico(self) -> dict[str, Any]:
        """Expõe somente saúde e contadores; nunca payloads dos lembretes."""
        lista = self.load()
        ativos = [item for item in lista if isinstance(item, dict) and item.get("ativo", True)]
        proximos = []
        for item in ativos:
            try:
                ts_execucao = float(item.get("ts_execucao") or 0.0)
            except (TypeError, ValueError):
                ts_execucao = 0.0
            if ts_execucao:
                proximos.append(ts_execucao)
        return {
            **dict(self._diagnostico),
            "disponivel": self._diagnostico["falhas_persistencia"] == 0 or bool(lista),
            "persistencia_local": True,
            "agendamentos_ativos": len(ativos),
            "proximo_evento_ts": min(proximos) if proximos else 0.0,
            "conteudo_exposto": False,
            "autoriza_execucao": False,
        }


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


def texto_pede_lembrete_explicito(texto: str, normalizar_texto_cb: Callable[[str], str] | None = None) -> bool:
    """Distingue um pedido de lembrete de um simples relato sobre o futuro."""
    normalizar = normalizar_texto_cb or (lambda valor: str(valor or "").casefold())
    t = str(normalizar(texto) or "").strip()
    return bool(re.search(
        r"\b(?:me\s+lembra|lembra\s+(?:de|pra|para)|me\s+avisa|avisa\s+(?:de|pra|para)|"
        r"agende|agendar|cria(?:r)?\s+(?:um\s+)?lembrete|marca\s+(?:um\s+)?lembrete)\b",
        t,
    ))


def resolver_instante_lembrete(
    hora_alvo: str,
    referencia_data: str = "",
    *,
    agora: _dt.datetime | None = None,
) -> tuple[_dt.datetime, str]:
    """Converte hora + referência humana em um instante futuro real."""
    base = agora or _dt.datetime.now()
    hora_match = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", str(hora_alvo or ""))
    if not hora_match:
        raise ValueError("horário inválido")
    hora, minuto = map(int, hora_match.groups())
    if not (0 <= hora <= 23 and 0 <= minuto <= 59):
        raise ValueError("horário inválido")

    ref = str(referencia_data or "").casefold().strip()
    ref = re.sub(r"\s+", " ", ref)
    destino = base.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    rotulo_data = ""
    if re.search(r"\bamanh[ãa]\b", ref):
        destino += _dt.timedelta(days=1)
        rotulo_data = "amanhã"
    elif re.search(r"\bhoje\b", ref):
        rotulo_data = "hoje"
    else:
        dias = {
            "segunda": 0, "segunda-feira": 0,
            "terça": 1, "terca": 1, "terça-feira": 1, "terca-feira": 1,
            "quarta": 2, "quarta-feira": 2,
            "quinta": 3, "quinta-feira": 3,
            "sexta": 4, "sexta-feira": 4,
            "sábado": 5, "sabado": 5,
            "domingo": 6,
        }
        dia_encontrado = next((nome for nome in dias if re.search(rf"\b{re.escape(nome)}\b", ref)), "")
        if dia_encontrado:
            delta = (dias[dia_encontrado] - base.weekday()) % 7
            if delta == 0 and destino <= base:
                delta = 7
            destino += _dt.timedelta(days=delta)
            rotulo_data = dia_encontrado.replace("-feira", "")
        else:
            data_match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", ref)
            if data_match:
                dia, mes = int(data_match.group(1)), int(data_match.group(2))
                ano_txt = data_match.group(3)
                ano = int(ano_txt) if ano_txt else base.year
                if ano < 100:
                    ano += 2000
                destino = destino.replace(year=ano, month=mes, day=dia)
                if not ano_txt and destino <= base:
                    destino = destino.replace(year=ano + 1)
                rotulo_data = destino.strftime("%d/%m")
            elif destino <= base:
                destino += _dt.timedelta(days=1)
                rotulo_data = "amanhã"

    rotulo = f"{rotulo_data} às {hora:02d}:{minuto:02d}" if rotulo_data else f"às {hora:02d}:{minuto:02d}"
    return destino, rotulo


def resolver_referencia_contextual_lembrete(
    descricao: str,
    referencia_data: str,
    entradas_recentes: list | None,
) -> tuple[str, str]:
    """Resolve ``isso/disso`` apenas contra um relato futuro recente."""
    descricao_limpa = str(descricao or "").strip()
    generica = descricao_limpa.casefold() in {
        "", "lembrete", "isso", "disso", "desse evento", "do evento",
    }
    if not generica:
        return descricao_limpa, str(referencia_data or "").strip()

    for entrada in reversed(list(entradas_recentes or [])[-4:]):
        texto = re.sub(r"\s+", " ", str(entrada or "")).strip(" .,!?:;")
        baixo = texto.casefold()
        if not texto or texto_pede_lembrete_explicito(baixo):
            continue
        data_match = re.search(
            r"\b(hoje|amanh[ãa]|segunda(?:-feira)?|ter[çc]a(?:-feira)?|quarta(?:-feira)?|"
            r"quinta(?:-feira)?|sexta(?:-feira)?|s[áa]bado|domingo|\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b",
            baixo,
        )
        if not data_match or not re.search(r"\b(?:vou|irei|tenho|terei|vai|acontece|ser[áa])\b", baixo):
            continue

        evento = re.split(r"\bsabia que\b", texto, maxsplit=1, flags=re.IGNORECASE)[-1]
        evento = re.sub(re.escape(data_match.group(0)), " ", evento, count=1, flags=re.IGNORECASE)
        evento = re.sub(r"^\s*eu\s+vou\s+participa(?:r)?\s+", "participar ", evento, flags=re.IGNORECASE)
        evento = re.sub(r"^\s*eu\s+(?:vou|irei)\s+", "", evento, flags=re.IGNORECASE)
        evento = re.sub(r"^\s*eu\s+(?:tenho|terei)\s+", "", evento, flags=re.IGNORECASE)
        evento = re.sub(r"\s+", " ", evento).strip(" .,!?:;")
        if evento:
            return evento, str(referencia_data or data_match.group(1)).strip()
    return descricao_limpa, str(referencia_data or "").strip()


def extrair_agendamento_local(texto: str, normalizar_texto_cb: Callable[[str], str]) -> Optional[dict]:
    bruto = str(texto or "").strip()
    if not bruto:
        return None
    # O relógio é evidência estrutural. A normalização canônica remove ``:``,
    # então ele precisa ser lido do texto original antes da limpeza lexical.
    hora_bruta = ""
    m_hora_bruta = re.search(
        r"\b(?:às|as|a)?\s*(\d{1,2})\s*(?::|h)\s*(\d{2})\b",
        bruto.casefold(),
    )
    if m_hora_bruta:
        hora, minuto = map(int, m_hora_bruta.groups())
        if 0 <= hora <= 23 and 0 <= minuto <= 59:
            hora_bruta = f"{hora:02d}:{minuto:02d}"
    t = normalizar_texto_cb(bruto)
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return None
    t = re.sub(r"\b(\d{1,2})\s*[h:]\s*(\d{2})\b", r"\1:\2", t)
    t = re.sub(r"\b(\d{1,2})\s*horas?\s*(\d{2})\b", r"\1:\2", t)

    if any(p in t for p in ["tenho algum compromisso", "tem algum compromisso", "meu compromisso", "compromissos de hoje", "agenda de hoje", "ver agenda", "mostrar agenda", "listar agenda", "me mostra os compromissos", "pode ver se tem", "ver se tem"]):
        return {"intent": "LISTAR_AGENDAMENTOS", "params": {}}

    # Perguntar, formular hipótese ou negar uma ação não é autorização. A lista
    # acima é somente leitura; mutações e novos lembretes param aqui.
    if re.search(
        r"^(?:nao|não)\b|\b(?:como\s+(?:eu\s+)?(?:faria|faço|faco)|"
        r"voce\s+(?:consegue|pode)|você\s+(?:consegue|pode)|"
        r"se\s+eu\s+(?:pedir|mandar)|seria\s+possivel|seria\s+possível)\b",
        t,
    ):
        return None

    if any(p in t for p in ["cancela", "cancelar", "remove", "remover", "apaga", "apagar"]) and any(p in t for p in ["agendamento", "lembrete", "compromisso", "compromissos", "agenda"]):
        alvo = re.sub(
            r"^(?:cancela|cancelar|remove|remover|apaga|apagar)\s+"
            r"(?:(?:o|a|um|uma|os|as)\s+)?"
            r"(?:agendamento|lembrete|compromisso|compromissos|agenda)"
            r"(?:\s+(?:de|do|da|dos|das))?\s*",
            "",
            t,
            count=1,
        ).strip()
        return {"intent": "CANCELAR_AGENDAMENTO", "params": {"alvo": alvo or ""}}

    if texto_pede_lembrete_explicito(t, normalizar_texto_cb=lambda valor: valor):
        minutos = None
        hora_alvo = ""
        gatilho = re.search(
            r"\b(?:me\s+lembra|lembra\s+(?:de|pra|para)|me\s+avisa|"
            r"avisa\s+(?:de|pra|para)|agende|agendar|cria(?:r)?\s+(?:um\s+)?"
            r"lembrete|marca\s+(?:um\s+)?lembrete)\b",
            t,
        )
        texto_evento = t[gatilho.start():] if gatilho else t
        referencia_data = ""

        m_data = re.search(
            r"\b(hoje|amanh[ãa]|segunda(?:-feira)?|ter[çc]a(?:-feira)?|quarta(?:-feira)?|"
            r"quinta(?:-feira)?|sexta(?:-feira)?|s[áa]bado|domingo|\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b",
            t,
        )
        if m_data:
            referencia_data = m_data.group(1)
            texto_evento = texto_evento.replace(m_data.group(0), " ")

        padrao_minutos = r"\b(?:(?:daqui(?:\s+a)?|em)\s+)?(\d{1,3})\s*(?:min|mins|minuto|minutos)\b"
        m_min = re.search(padrao_minutos, t)
        if m_min:
            try:
                minutos = int(m_min.group(1))
            except Exception:
                minutos = None
            texto_evento = re.sub(padrao_minutos, " ", texto_evento).strip()

        if minutos is None:
            m_hora = re.search(r"\b(?:às|as|a)\s*(\d{1,2}:\d{2})\b", t)
            if not m_hora:
                m_hora = re.search(r"\b(\d{1,2}:\d{2})\b", t)
            if m_hora:
                hora_alvo = m_hora.group(1)
                texto_evento = texto_evento.replace(hora_alvo, " ")
                texto_evento = re.sub(r"\b(?:às|as|a)\s*", " ", texto_evento).strip()
            elif hora_bruta:
                hora_alvo = hora_bruta
                texto_evento = re.sub(
                    r"\b(?:as|a)?\s*\d{1,2}\s+\d{2}\b",
                    " ",
                    texto_evento,
                    count=1,
                ).strip()

        for prefixo in [
            "me lembra de", "lembra de", "me lembra pra", "lembra pra",
            "me avisa de", "me avisa pra", "agende", "agenda", "marca",
            "marca pra mim", "agendar", "lembra às", "lembra as",
            "me lembra", "lembra", "me avisa", "avisa",
        ]:
            texto_evento = re.sub(rf"^\s*{re.escape(prefixo)}\s*", " ", texto_evento, flags=re.IGNORECASE)
        texto_evento = re.sub(r"\b(de|do|da|para|pra|pro|no|na|em)\b", " ", texto_evento)
        texto_evento = re.sub(r"\s+", " ", texto_evento).strip(" .,!?:;")
        descricao = texto_evento or "lembrete"

        params = {"descricao": descricao}
        if minutos is not None:
            params["minutos"] = minutos
        if hora_alvo:
            params["hora_alvo"] = hora_alvo
        if referencia_data:
            params["data_hora"] = referencia_data
        return {"intent": "AGENDAR_LEMBRETE", "params": params}

    return None


def extrair_complemento_temporal_lembrete(texto: str) -> Optional[dict[str, Any]]:
    """Extrai apenas tempo/data para completar uma pendência já autorizada."""
    bruto = re.sub(r"\s+", " ", str(texto or "").casefold()).strip()
    if not bruto:
        return None
    m_min = re.search(
        r"\b(?:(?:daqui(?:\s+a)?|em)\s+)?(\d{1,3})\s*(?:min|mins|minuto|minutos)\b",
        bruto,
    )
    if m_min:
        return {"minutos": int(m_min.group(1)), "complemento_pendente": True}
    m_hora = re.search(
        r"\b(?:pode\s+ser\s+)?(?:às|as|a)?\s*(\d{1,2})\s*(?::|h|\s)\s*(\d{2})\b",
        bruto,
    )
    if not m_hora:
        return None
    hora, minuto = map(int, m_hora.groups())
    if not (0 <= hora <= 23 and 0 <= minuto <= 59):
        return None
    params: dict[str, Any] = {
        "hora_alvo": f"{hora:02d}:{minuto:02d}",
        "complemento_pendente": True,
    }
    data = re.search(
        r"\b(hoje|amanh[ãa]|segunda(?:-feira)?|ter[çc]a(?:-feira)?|quarta(?:-feira)?|"
        r"quinta(?:-feira)?|sexta(?:-feira)?|s[áa]bado|domingo|\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b",
        bruto,
    )
    if data:
        params["data_hora"] = data.group(1)
    return params


def extrair_acao_agendada_local(texto: str, normalizar_texto_cb: Callable[[str], str]) -> Optional[dict]:
    """Separa uma ação prática de um prazo no fim da frase."""
    bruto = str(texto or "").strip()
    if not bruto:
        return None
    t = str(normalizar_texto_cb(bruto) or "").strip()
    if not t or any(p in t for p in ["me lembra", "me avisa", "lembrete", "agende", "agendar"]):
        return None

    m_rel = re.search(
        r"\b(?:daqui(?:\s+a)?|em)\s+(\d{1,4})\s*(segundo|segundos|minuto|minutos|hora|horas)\s*$",
        t,
    )
    if m_rel:
        valor = int(m_rel.group(1))
        unidade = m_rel.group(2)
        if valor <= 0:
            return None
        fator = 1 if unidade.startswith("segundo") else (60 if unidade.startswith("minuto") else 3600)
        texto_acao = t[:m_rel.start()].strip(" ,.;:-")
        if texto_acao:
            return {"texto_acao": texto_acao, "atraso_segundos": valor * fator}

    # A normalização geral remove ':'; por isso o relógio é extraído do texto
    # bruto e só a parte da ação é normalizada depois.
    m_hora = re.search(
        r"\b(?:às|as|a)\s+(\d{1,2})\s*(?::|h|\s)\s*(\d{2})\s*$",
        bruto.casefold(),
    )
    if m_hora:
        hora_alvo = f"{m_hora.group(1)}:{m_hora.group(2)}"
        try:
            hora, minuto = map(int, hora_alvo.split(":"))
        except Exception:
            return None
        if hora > 23 or minuto > 59:
            return None
        texto_acao = str(normalizar_texto_cb(bruto[:m_hora.start()]) or "").strip(" ,.;:-")
        if texto_acao:
            return {"texto_acao": texto_acao, "hora_alvo": f"{hora:02d}:{minuto:02d}"}
    return None


def descrever_intencao_agendada(intencao: Dict[str, Any]) -> str:
    intent = str((intencao or {}).get("intent") or "").upper().strip()
    params = dict((intencao or {}).get("params") or {})
    alvo = str(
        params.get("alvo")
        or params.get("nome_app")
        or params.get("nome_playlist")
        or params.get("query")
        or ""
    ).strip()
    if intent == "IOT_CONTROL":
        verbo = str(params.get("acao") or "controlar").strip().lower()
    else:
        verbo = {
            "APP_OPEN": "abrir",
            "OPEN_URL": "abrir",
            "SITE_ENTER": "abrir",
            "CLOSE_APP": "fechar",
            "CLOSE_TAB": "fechar",
            "MAXIMIZE_WINDOW": "maximizar",
            "MUSIC_SEARCH": "tocar",
            "PLAYLIST_PLAY": "tocar playlist",
            "MEDIA_CONTROL": str(params.get("acao") or "controlar mídia").strip().lower(),
            "VOLUME": "ajustar volume",
        }.get(intent, intent.lower().replace("_", " ") or "executar ação")
    return f"{verbo} {alvo}".strip()
