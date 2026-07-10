"""Runtime de voz, fila de fala e fala dinamica da Laylay."""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
import threading
import time
from queue import Empty, Queue
from typing import Any, Callable, Optional


class VozRuntime:
    def __init__(
        self,
        *,
        fallback_fala: str,
        voice: str,
        edge_tts_mod: Any,
        sounddevice_mod: Any,
        soundfile_mod: Any,
        pyttsx3_mod: Any,
        limpar_para_voz_cb: Callable[[str], str],
        formatar_mensagem_cb: Callable[..., str],
        ducking_volume_cb: Callable[[bool], Any],
        enviar_mensagem_cb: Callable[..., str],
        normalizar_texto_cb: Callable[[str], str],
        compor_fala_proativa_cb: Callable[[list], tuple[str, str, int]],
        ajustar_estado_fala_cb: Callable[[str, Any], Any],
        mente_estado_getter: Callable[[], dict],
        interrupt_event: Any,
        thread_factory: Callable[..., Any] = threading.Thread,
        timer_factory: Callable[..., Any] = threading.Timer,
        log: Callable[[str], Any] = print,
        batch_window: float = 0.0,
        batch_max_items: int = 1,
        proativa_delay: float = 1.0,
        proativa_janela_startup: float = 18.0,
    ):
        self.fallback_fala = fallback_fala
        self.voice = voice
        self.edge_tts = edge_tts_mod
        self.sd = sounddevice_mod
        self.sf = soundfile_mod
        self.pyttsx3 = pyttsx3_mod
        self.limpar_para_voz = limpar_para_voz_cb
        self.formatar_mensagem = formatar_mensagem_cb
        self.ducking_volume = ducking_volume_cb
        self.enviar_mensagem = enviar_mensagem_cb
        self.normalizar_texto = normalizar_texto_cb
        self.compor_fala_proativa_cb = compor_fala_proativa_cb
        self.ajustar_estado_fala_cb = ajustar_estado_fala_cb
        self.mente_estado_getter = mente_estado_getter
        self.interrupt_event = interrupt_event
        self.thread_factory = thread_factory
        self.timer_factory = timer_factory
        self.log = log
        self.batch_window = batch_window
        self.batch_max_items = batch_max_items

        self.fila = Queue()
        self.worker_started = False
        self.worker_lock = threading.Lock()
        self.fala_dinamica_cache: dict[tuple[str, str, int], str] = {}
        self.fala_dinamica_falhou_ate = 0.0

        self.proativa_lock = threading.Lock()
        self.proativa_buffer: list[dict] = []
        self.proativa_timer = None
        self.proativa_delay = proativa_delay
        self.proativa_inicio_sistema = time.time()
        self.proativa_janela_startup = proativa_janela_startup

    def iniciar_worker(self):
        with self.worker_lock:
            if self.worker_started:
                return
            self.thread_factory(target=self.worker_de_falas, daemon=True, name="Laylay-SpeechQueue").start()
            self.worker_started = True

    def combinar_falas_batch(self, itens: list) -> tuple[str, str, int]:
        falas = []
        emo = "calma"
        nivel = 1
        for idx, item in enumerate(itens):
            if not isinstance(item, dict):
                continue
            texto = self.limpar_para_voz(str(item.get("texto") or "")).strip()
            if not texto:
                continue
            texto = re.sub(r"\s+", " ", texto).strip()
            if not texto:
                continue
            if idx == 0:
                emo = str(item.get("emocao") or "calma")
                try:
                    nivel = int(item.get("nivel") or 1)
                except Exception:
                    nivel = 1
            if texto[-1] not in ".!?…":
                texto += "."
            falas.append(texto)

        if not falas:
            return self.fallback_fala, emo, nivel

        texto_final = re.sub(r"\s+", " ", " ".join(falas)).strip()
        return texto_final, emo, nivel

    def reproduzir_fala(self, texto: str, emocao: str, nivel: int):
        temp_file = None
        try:
            texto_voz = self.limpar_para_voz(texto) or self.fallback_fala
            self.log("")
            self.log(self.formatar_mensagem(texto_voz, emocao=emocao, nivel=nivel))

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_file = f.name

            communicate = self.edge_tts.Communicate(texto_voz, voice=self.voice)
            asyncio.run(communicate.save(temp_file))

            data, samplerate = self.sf.read(temp_file)

            self.ducking_volume(True)
            try:
                self.sd.play(data, samplerate)
                while self.sd.get_stream().active:
                    if self.interrupt_event.is_set():
                        self.sd.stop()
                        self.log("🛑 [BARGE-IN] Fala interrompida pelo Pedro!")
                        break
                    time.sleep(0.03)
            finally:
                self.ducking_volume(False)

        except Exception as e:
            self.log(f"❌ [FALA] Erro no áudio: {type(e).__name__} → {e}")
            try:
                self.fallback_pyttsx(texto, emocao)
            except Exception:
                pass
        finally:
            self.ajustar_estado_fala_cb("is_speaking", False)
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass

    def worker_de_falas(self):
        while True:
            item = self.fila.get()
            if item is None:
                continue

            lote = [item]
            prazo = time.time() + self.batch_window
            while len(lote) < self.batch_max_items:
                restante = prazo - time.time()
                if restante <= 0:
                    break
                try:
                    prox = self.fila.get(timeout=restante)
                except Empty:
                    break
                if prox is None:
                    continue
                lote.append(prox)
                prazo = time.time() + self.batch_window

            texto_final, emocao, nivel = self.combinar_falas_batch(lote)
            self.ajustar_estado_fala_cb("current_emotion", emocao)
            self.ajustar_estado_fala_cb("emotion_level", nivel)
            self.ajustar_estado_fala_cb("is_speaking", True)
            try:
                self.reproduzir_fala(texto_final, emocao, nivel)
            finally:
                for pedido in lote:
                    if isinstance(pedido, dict):
                        ev = pedido.get("done_event")
                        if ev is not None:
                            try:
                                ev.set()
                            except Exception:
                                pass

    def normalizar_segmento_fala(self, texto: str) -> str:
        t = self.limpar_para_voz(str(texto or "")).strip()
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            return ""
        if t[-1] not in ".!?…":
            t += "."
        return t

    def flush_fala_proativa(self):
        with self.proativa_lock:
            itens = list(self.proativa_buffer)
            self.proativa_buffer = []
            self.proativa_timer = None

        if not itens:
            return

        texto, emocao, nivel = self.compor_fala_proativa_cb(itens)
        self.falar(texto, emocao, nivel)

    def agendar_fala_proativa(self, tipo: str, texto: str, emocao: str = "calma", nivel: int = 1):
        tipo_norm = str(tipo or "").strip().lower()
        item = {
            "tipo": tipo_norm,
            "texto": str(texto or "").strip(),
            "emocao": emocao,
            "nivel": nivel,
            "ts": time.time(),
        }
        with self.proativa_lock:
            self.proativa_buffer.append(item)
            if self.proativa_timer and self.proativa_timer.is_alive():
                return
            atraso = self.proativa_delay
            idade_sistema = time.time() - self.proativa_inicio_sistema
            if tipo_norm in {"briefing", "emails", "rotina", "musica"} and idade_sistema < self.proativa_janela_startup:
                atraso = max(self.proativa_delay, self.proativa_janela_startup - idade_sistema)
                self.log(f"🧠 [FALA PROATIVA] aguardando {atraso:.1f}s para unificar falas iniciais")
            self.proativa_timer = self.timer_factory(atraso, self.flush_fala_proativa)
            self.proativa_timer.daemon = True
            self.proativa_timer.start()

    async def gerar_audio_edge(self, texto: str, arquivo: str):
        communicate = self.edge_tts.Communicate(texto, voice=self.voice)
        await communicate.save(arquivo)

    def extrair_json_fala_dinamica(self, raw: str) -> str:
        bruto = str(raw or "").strip()
        if not bruto:
            return ""
        try:
            data = json.loads(bruto)
            return str(data.get("fala") or "").strip() if isinstance(data, dict) else ""
        except Exception:
            pass
        m = re.search(r"\{.*\}", bruto, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                return str(data.get("fala") or "").strip() if isinstance(data, dict) else ""
            except Exception:
                return ""
        return ""

    def fala_dinamica_deve_tentar(self, texto: str) -> bool:
        t = str(texto or "").strip()
        if not t or len(t) < 8 or len(t) > 220:
            return False
        baixo = t.lower()
        if baixo.startswith(("suas playlists são:", "suas playlists sao:")):
            return False
        if t.count(",") >= 3 or (":" in t and ";" in t):
            return False
        if "http://" in baixo or "https://" in baixo or "```" in baixo or "{" in t or "}" in t:
            return False
        if baixo.startswith(("erro na api", "traceback", "warning", "⚠️", "❌")):
            return False
        if any(x in baixo for x in [
            "cérebro desconectou", "cerebro desconectou",
            "circuitos de comunicacao", "circuitos de comunicação",
            "recomendação musical", "recomendacao musical",
            "não achei", "nao achei",
            "não consegui", "nao consegui",
            "não respondeu", "nao respondeu",
            "falhou", "não colaborou", "nao colaborou",
        ]):
            return False
        gatilhos_template = [
            "abrindo", "fechando", "pronto", "colocando", "não vou", "nao vou",
            "quer ouvir", "quer que", "deixei", "fechado", "beleza", "tentei",
            "não consegui", "nao consegui", "achei", "minha aposta", "eu iria",
            "tô", "to",
        ]
        if any(x in baixo for x in ["chat ligado", "conversa aberta", "modo chat", "modo de urgência", "modo de urgencia"]):
            return False
        if any(g in baixo for g in gatilhos_template):
            return True
        return len(t.split()) <= 16 and not baixo.endswith("?")

    def fala_dinamica_preserva_sentido(self, original: str, nova: str) -> bool:
        o = self.normalizar_texto(original)
        n = self.normalizar_texto(nova)
        if not n or len(nova) > 240:
            return False
        if any(x in n for x in ["json", "comandos", "open_url", "youtube_search"]):
            return False
        if "?" not in original and "?" in nova:
            return False
        negativos = ["nao consegui", "não consegui", "tentei", "falhou", "nao achei", "não achei"]
        positivos = ["consegui", "feito", "pronto", "abri", "fechei", "salvei", "toquei"]
        if any(x in o for x in negativos) and any(x in n for x in positivos) and not any(x in n for x in negativos):
            return False
        confirmacoes = ["abrindo", "abri", "fechando", "fechei", "pronto", "feito", "maximizei", "maximizado"]
        condicionais = ["se abriu", "se abrir", "se fechou", "se fechar", "talvez", "acho que", "parece que"]
        if any(x in o for x in confirmacoes) and any(x in n for x in condicionais):
            return False
        if "?" in original and "?" not in nova:
            return False
        if any(x in o for x in ["quer ouvir", "posso", "quer que"]) and not any(x in n for x in ["quer", "posso", "quer que"]):
            return False
        grupos_acao = [
            ("abr", ["abri", "abrindo", "abrir", "abriu"]),
            ("fech", ["fechei", "fechando", "fechar", "fechado", "encerrei", "encerrado"]),
            ("maximiz", ["maximizei", "maximizado", "maximizar", "tela cheia", "destaque"]),
            ("foco", ["foco", "frente", "destaque"]),
            ("playlist", ["playlist"]),
            ("volume", ["volume", "som"]),
        ]
        for marcador, equivalentes in grupos_acao:
            if marcador in o and not any(eq in n for eq in equivalentes):
                return False
        return True

    def temperar_fala_com_ia(self, texto: str, emocao: str = "calma", nivel: int = 1) -> str:
        base = str(texto or "").strip()
        if not self.fala_dinamica_deve_tentar(base):
            return base
        if time.time() < self.fala_dinamica_falhou_ate:
            return base
        cache_key = (base, str(emocao or ""), int(nivel or 1))
        if cache_key in self.fala_dinamica_cache:
            return self.fala_dinamica_cache[cache_key]

        try:
            estado = dict(self.mente_estado_getter() or {})
        except Exception:
            estado = {}
        contexto_curto = (
            f"emocao={emocao or 'calma'}({nivel or 1}); "
            f"ultima_habilidade={estado.get('ultima_habilidade') or ''}; "
            f"ultima_intencao={estado.get('ultima_intencao') or estado.get('ultima_acao_intent') or ''}; "
            f"ultimo_alvo={estado.get('ultimo_alvo') or ''}"
        )
        prompt = (
            "Você é a Laylay. Reescreva a fala base com mais naturalidade, liberdade e personalidade.\n"
            "Preserve exatamente o sentido prático: não invente ação, não mude sucesso para falha nem falha para sucesso.\n"
            "Não invente presentes, lembranças, hábitos, promessas ou fatos sobre Pedro e Laylay.\n"
            "Se a fala base pergunta algo, mantenha como pergunta. Se confirma uma ação, confirme sem exagerar.\n"
            "Pode ser amiga, divertida, debochada leve, carinhosa ou estranhar o pedido, conforme o contexto.\n"
            "Evite formato repetido tipo sempre começar com Pronto/Beleza/Fechado.\n"
            "Nao alongue. Uma frase curta basta. Sem discurso, sem conselho extra.\n"
            "Responda APENAS JSON válido: {\"fala\":\"...\"}\n\n"
            f"Contexto: {contexto_curto}\n"
            f"Fala base: {base!r}\n"
        )
        try:
            raw = self.enviar_mensagem(
                [{"role": "system", "content": prompt}],
                _com_tools=False,
                max_tokens=90,
                modo_rapido=True,
            )
            if "Erro na API" in str(raw) or "circuitos de comunicacao" in str(raw) or "circuitos de comunicação" in str(raw):
                self.fala_dinamica_falhou_ate = time.time() + 60.0
                return base
            nova = self.limpar_para_voz(self.extrair_json_fala_dinamica(raw))
            if self.fala_dinamica_preserva_sentido(base, nova):
                self.fala_dinamica_cache[cache_key] = nova
                if len(self.fala_dinamica_cache) > 80:
                    self.fala_dinamica_cache.clear()
                self.log(f"🗣️ [FALA DINAMICA] {base[:55]!r} -> {nova[:75]!r}")
                return nova
        except Exception as e:
            self.log(f"⚠️ [FALA DINAMICA] falha ao variar fala: {e}")
            self.fala_dinamica_falhou_ate = time.time() + 30.0
        return base

    def falar(self, texto: str, emocao: str = "calma", nivel: Optional[int] = None, wait: bool = False):
        self.iniciar_worker()
        nivel_final = nivel if nivel is not None else 1
        texto_final = self.temperar_fala_com_ia(texto, emocao, nivel_final)
        done_event = threading.Event()
        pedido = {
            "texto": texto_final,
            "emocao": emocao,
            "nivel": nivel_final,
            "done_event": done_event,
        }
        self.fila.put(pedido)
        if wait:
            done_event.wait()

    def fallback_pyttsx(self, texto: str, emocao_atual: str):
        try:
            texto_voz = self.limpar_para_voz(texto) or self.fallback_fala
            engine = self.pyttsx3.init()
            engine.setProperty("rate", 150 if "calma" in str(emocao_atual).lower() else 170)
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            caminho = temp.name
            temp.close()
            engine.save_to_file(texto_voz, caminho)
            engine.runAndWait()
            data, sr_val = self.sf.read(caminho)

            self.ducking_volume(True)
            try:
                self.sd.play(data, sr_val)
                self.sd.wait()
            finally:
                self.ducking_volume(False)

            os.unlink(caminho)
        except Exception as e:
            self.log(f"❌ Erro no fallback TTS: {e}")
            self.log(texto)


def criar_voz_runtime(**kwargs) -> VozRuntime:
    return VozRuntime(**kwargs)
