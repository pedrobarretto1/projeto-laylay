"""Runtime de voz, fila de fala e fala dinamica da Laylay."""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
import threading
import time
from collections import deque
from queue import Empty, Queue
from typing import Any, Callable, Mapping, Optional

from mente_laylay.personalidade.ritmo_natural import (
    ajustar_abertura_repetida,
    ajustar_uso_natural_nome,
)
from mente_laylay.percepcao.dispositivos_audio import selecionar_dispositivo_audio
from mente_laylay.memoria_mental.observabilidade import relatar_falha_opcional


VOZ_TTS_PADRAO = "pt-BR-FranciscaNeural"
VOZ_TTS_FALLBACK = "pt-BR-ThalitaMultilingualNeural"


def resolver_vozes_tts(environ: Mapping[str, str] | None = None) -> tuple[str, str]:
    """Resolve as vozes neurais sem prender a configuração ao arquivo principal."""
    ambiente = os.environ if environ is None else environ
    principal = str(ambiente.get("LAYLAY_TTS_VOICE", "") or "").strip()
    fallback = str(ambiente.get("LAYLAY_TTS_VOICE_FALLBACK", "") or "").strip()
    return principal or VOZ_TTS_PADRAO, fallback or VOZ_TTS_FALLBACK


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
        preparar_tts_cb: Callable[[str], str] | None = None,
        formatar_mensagem_cb: Callable[..., str],
        ducking_volume_cb: Callable[[bool], Any],
        modular_audio_params_cb: Callable[[str, int], tuple[str, str, str]],
        compor_fala_proativa_cb: Callable[[list], tuple[str, str, int]],
        ajustar_estado_fala_cb: Callable[[str, Any], Any],
        proativa_permitida_cb: Callable[[], bool] | None = None,
        nome_usuario_cb: Callable[[], str] | None = None,
        avaliar_proatividade_cb: Callable[..., dict] | None = None,
        chave_turno_cb: Callable[[], float] | None = None,
        interrupt_event: Any,
        registrar_fala_emitida_cb: Callable[[str, list], Any] | None = None,
        registrar_metrica_cb: Callable[[str, float, bool], Any] | None = None,
        registrar_falha_cb: Callable[..., Any] | None = None,
        fallback_voice: str = "",
        thread_factory: Callable[..., Any] = threading.Thread,
        timer_factory: Callable[..., Any] = threading.Timer,
        log: Callable[[str], Any] = print,
        batch_window: float = 0.0,
        batch_max_items: int = 1,
        proativa_delay: float = 1.0,
        proativa_janela_startup: float = 18.0,
        tts_timeout_s: float = 8.0,
        stop_event: threading.Event | None = None,
        iniciar_servico_cb: Callable[[str, Callable[[], Any]], bool] | None = None,
    ):
        self.fallback_fala = fallback_fala
        self.nome_usuario_cb = nome_usuario_cb
        self.voice = str(voice or "").strip() or VOZ_TTS_PADRAO
        self.fallback_voices = [
            item.strip()
            for item in str(fallback_voice or "").split(",")
            if item.strip()
        ]
        # Mantém o atributo singular por compatibilidade com integrações antigas.
        self.fallback_voice = self.fallback_voices[0] if self.fallback_voices else ""
        self.edge_tts = edge_tts_mod
        self.sd = sounddevice_mod
        self.sf = soundfile_mod
        self.pyttsx3 = pyttsx3_mod
        self.limpar_para_voz = limpar_para_voz_cb
        self.preparar_tts = preparar_tts_cb or (lambda texto: texto)
        self.formatar_mensagem = formatar_mensagem_cb
        self.ducking_volume = ducking_volume_cb
        self.modular_audio_params = modular_audio_params_cb
        self.compor_fala_proativa_cb = compor_fala_proativa_cb
        self.ajustar_estado_fala_cb = ajustar_estado_fala_cb
        self.proativa_permitida_cb = proativa_permitida_cb
        self.avaliar_proatividade_cb = avaliar_proatividade_cb
        self.chave_turno_cb = chave_turno_cb
        self.registrar_fala_emitida_cb = registrar_fala_emitida_cb
        self.registrar_metrica_cb = registrar_metrica_cb
        self.registrar_falha_cb = registrar_falha_cb
        self._ultima_chave_turno_emitida = 0.0
        self._pedido_turno_pendente: dict | None = None
        self._ultima_fala_normal_ts = 0.0
        self._turno_lock = threading.Lock()
        self._turno_resposta_ativo = False
        self._chave_turno_ativo = 0.0
        self.interrupt_event = interrupt_event
        self.thread_factory = thread_factory
        self.timer_factory = timer_factory
        self.log = log
        self.batch_window = batch_window
        self.batch_max_items = batch_max_items

        self.fila = Queue()
        self.worker_started = False
        self.worker_lock = threading.Lock()
        self.stop_event = stop_event or threading.Event()
        self.iniciar_servico_cb = iniciar_servico_cb
        self._worker_thread: Any = None
        self.aberturas_fala_recentes: deque[str] = deque(maxlen=5)
        self.ultimo_uso_nome_ts = 0.0
        self._ultima_saida_audio: tuple[int, str] | None = None
        self._ultima_solicitacao_fala = ""
        self._ultima_solicitacao_fala_ts = 0.0
        self._fallback_tts_disponivel = pyttsx3_mod is not None

        self.proativa_lock = threading.Lock()
        self.proativa_buffer: list[dict] = []
        self.proativa_timer = None
        self.proativa_delay = proativa_delay
        self.proativa_inicio_sistema = time.time()
        self.proativa_janela_startup = proativa_janela_startup
        self.tts_timeout_s = max(0.05, float(tts_timeout_s))

    def _relatar_falha(
        self,
        codigo: str,
        erro: BaseException,
        *,
        classe: str = "degradacao",
        impacto: str = "fala",
        fallback: str = "nenhum",
        fase: str = "entrega_fala",
    ) -> bool:
        return relatar_falha_opcional(
            self.registrar_falha_cb,
            "voz",
            codigo,
            erro=erro,
            classe=classe,
            impacto=impacto,
            fallback=fallback,
            dominio="audio",
            fase=fase,
        )

    def iniciar_turno_resposta(self) -> None:
        """Reserva o canal de voz até a mente concluir a resposta do usuário."""
        chave = 0.0
        if callable(self.chave_turno_cb):
            try:
                chave = float(self.chave_turno_cb() or 0.0)
            except Exception as erro:
                self._relatar_falha(
                    "falha_chave_turno",
                    erro,
                    impacto="servico",
                    fallback="turno_sem_chave",
                    fase="iniciar_turno",
                )
                chave = 0.0
        with self._turno_lock:
            self._turno_resposta_ativo = True
            self._chave_turno_ativo = chave

    def sincronizar_chave_turno_resposta(self) -> float:
        """Atualiza a reserva depois que o plano do novo turno foi criado."""
        chave = 0.0
        if callable(self.chave_turno_cb):
            try:
                chave = float(self.chave_turno_cb() or 0.0)
            except Exception as erro:
                self._relatar_falha(
                    "falha_chave_turno",
                    erro,
                    impacto="servico",
                    fallback="turno_sem_chave",
                    fase="sincronizar_turno",
                )
                chave = 0.0
        with self._turno_lock:
            if self._turno_resposta_ativo:
                self._chave_turno_ativo = chave
        return chave

    def finalizar_turno_resposta(self) -> None:
        """Libera o canal e resolve observações que ficaram sem fala principal."""
        with self._turno_lock:
            self._turno_resposta_ativo = False
            self._chave_turno_ativo = 0.0
        with self.proativa_lock:
            pendente = bool(self.proativa_buffer)
            timer_ativo = bool(self.proativa_timer and self.proativa_timer.is_alive())
            if pendente and not timer_ativo:
                self.proativa_timer = self.timer_factory(self.proativa_delay, self.flush_fala_proativa)
                self.proativa_timer.daemon = True
                self.proativa_timer.start()

    def _concluir_itens_proativos(
        self, itens: list[dict], entregue: bool, motivo: str, log=None,
    ) -> None:
        log_fn = log or self.log
        for item in itens:
            callback = item.get("ao_concluir") if isinstance(item, dict) else None
            if callable(callback):
                try:
                    callback(bool(entregue), str(motivo or ""))
                except Exception as erro:
                    log_fn(f"⚠️ [FALA PROATIVA] callback falhou: {erro}")
                    self._relatar_falha(
                        "falha_callback_conclusao_proativa",
                        erro,
                        impacto="servico",
                        fallback="conclusao_sem_callback",
                        fase="finalizar_fala_proativa",
                    )

    def _iniciar_itens_proativos(self, itens: list[dict], log=None) -> None:
        """Ativa o contexto da fala antes de ela ficar audível ao usuário."""
        log_fn = log or self.log
        for item in itens:
            if not isinstance(item, dict) or item.get("_inicio_notificado"):
                continue
            callback = item.get("ao_iniciar")
            item["_inicio_notificado"] = True
            if callable(callback):
                try:
                    callback()
                except Exception as erro:
                    log_fn(f"⚠️ [FALA PROATIVA] callback de início falhou: {erro}")
                    self._relatar_falha(
                        "falha_callback_inicio_proativa",
                        erro,
                        impacto="servico",
                        fallback="fala_sem_callback_inicio",
                        fase="iniciar_fala_proativa",
                    )

    def _retirar_proativas_do_turno(self, chave: float) -> list[dict]:
        with self.proativa_lock:
            escolhidas = []
            restantes = []
            for item in self.proativa_buffer:
                chave_item = float(item.get("turno_chave") or 0.0) if isinstance(item, dict) else 0.0
                if (
                    isinstance(item, dict)
                    and item.get("mesclar_turno")
                    and (not chave_item or not chave or chave_item == chave)
                ):
                    escolhidas.append(item)
                else:
                    restantes.append(item)
            self.proativa_buffer = restantes
        return escolhidas

    def _mesclar_fala_do_turno(self, principal: str, itens: list[dict]) -> str:
        if not itens:
            return principal
        try:
            proativa, _emocao, _nivel = self.compor_fala_proativa_cb(itens)
        except Exception as erro:
            self._relatar_falha(
                "falha_compor_fala_mesclada",
                erro,
                fallback="concatenacao_segura",
                fase="compor_fala",
            )
            proativa = " ".join(str(item.get("texto") or "") for item in itens)
        principal_norm = self.normalizar_segmento_fala(principal)
        proativa_norm = self.normalizar_segmento_fala(proativa)
        if not proativa_norm:
            return principal
        proativa_norm = proativa_norm[0].lower() + proativa_norm[1:]
        return f"{principal_norm} Ah, e uma coisa que notei por aqui: {proativa_norm}".strip()

    def _selecionar_saida_audio(self) -> int:
        pedido = str(os.getenv("LAYLAY_SAIDA_AUDIO", "") or "").strip()
        indice, info, origem = selecionar_dispositivo_audio(self.sd, "saida", pedido)
        nome = str(info.get("name") or "saída de áudio")
        assinatura = (indice, nome)
        if assinatura != self._ultima_saida_audio:
            self.log(f"🔊 [ÁUDIO] Saída: {nome} (índice {indice}, {origem}).")
            self._ultima_saida_audio = assinatura
        return indice

    @staticmethod
    def _normalizar_percentual_edge(valor: Any, padrao: str = "+0%") -> str:
        """Converte percentuais tolerantes para o formato estrito do edge-tts."""
        texto = str(valor or "").strip()
        if re.fullmatch(r"[+-]\d+%", texto):
            return texto
        if re.fullmatch(r"\d+%", texto):
            return f"+{texto}"
        return padrao

    @staticmethod
    def _prioridade_candidato_fala(texto: str) -> int:
        """Prioriza resultado/correção e rebaixa respostas vazias de contexto."""
        base = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
        if not base:
            return 0
        if any(termo in base for termo in (
            "corrigi", "foi mal", "desculpa", "não respondeu", "nao respondeu",
            "não consegui", "nao consegui", "falhou", "não alterei", "nao alterei",
        )):
            return 95
        if any(termo in base for termo in (
            "pronto", "liguei", "desliguei", "abri ", "fechei", "criei ",
            "apaguei", "removi", "agendei", "confirmei", "coloquei", "toquei",
        )):
            return 85
        if any(termo in base for termo in (
            "estou aqui", "tô aqui", "to aqui", "me fala o próximo passo",
            "me fala o proximo passo", "não fechei tua frase", "nao fechei tua frase",
        )):
            return 10
        if "?" in base:
            return 45
        return 30

    def iniciar_worker(self):
        with self.worker_lock:
            if self.worker_started:
                return
            if callable(self.iniciar_servico_cb):
                iniciado = self.iniciar_servico_cb(
                    "Laylay-SpeechQueue", self._executar_worker_supervisionado,
                )
                self.worker_started = bool(iniciado)
                return
            thread = self.thread_factory(
                target=self._executar_worker_supervisionado,
                daemon=True,
                name="Laylay-SpeechQueue",
            )
            self._worker_thread = thread
            self.worker_started = True
            thread.start()

    def _executar_worker_supervisionado(self) -> None:
        with self.worker_lock:
            self.worker_started = True
        try:
            self.worker_de_falas()
        finally:
            with self.worker_lock:
                self.worker_started = False

    def _criar_comunicacao_edge(
        self,
        texto: str,
        *,
        voice: str,
        rate: str,
        pitch: str,
        volume: str,
    ):
        try:
            return self.edge_tts.Communicate(
                texto,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
        except TypeError:
            # Compatibilidade com versões antigas do edge-tts.
            return self.edge_tts.Communicate(texto, voice=voice)

    def _sintetizar_edge(
        self,
        texto: str,
        caminho: str,
        *,
        rate: str,
        pitch: str,
        volume: str,
    ) -> str:
        """Sintetiza com a voz principal e tenta a reserva antes do TTS local."""
        vozes = []
        for voice in [self.voice, *self.fallback_voices]:
            if voice and voice not in vozes:
                vozes.append(voice)

        ultimo_erro: Exception | None = None
        prazo = time.monotonic() + self.tts_timeout_s
        for indice, voice in enumerate(vozes):
            try:
                communicate = self._criar_comunicacao_edge(
                    texto,
                    voice=voice,
                    rate=rate,
                    pitch=pitch,
                    volume=volume,
                )
                restante = prazo - time.monotonic()
                if restante <= 0:
                    raise TimeoutError("tempo total da sintese neural esgotado")
                asyncio.run(asyncio.wait_for(communicate.save(caminho), timeout=restante))
                return voice
            except Exception as erro:
                ultimo_erro = erro
                if isinstance(erro, (TimeoutError, asyncio.TimeoutError)):
                    self.log(
                        f"⚠️ [VOZ] síntese neural excedeu {self.tts_timeout_s:.1f}s; "
                        "usando o fallback local."
                    )
                    break
                if indice + 1 < len(vozes):
                    self.log(
                        f"⚠️ [VOZ] A voz {voice} não respondeu; "
                        f"tentando {vozes[indice + 1]}."
                    )

        if ultimo_erro is not None:
            raise ultimo_erro
        raise RuntimeError("nenhuma voz neural foi configurada")

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
                except (TypeError, ValueError):
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
        inicio_total = time.perf_counter()
        sucesso = False
        try:
            texto_exibicao = self.limpar_para_voz(texto) or self.fallback_fala
            try:
                texto_voz = self.preparar_tts(texto_exibicao) or texto_exibicao
            except Exception as erro_oralidade:
                self.log(f"⚠️ [VOZ] adaptação oral ignorada: {erro_oralidade}")
                self._relatar_falha(
                    "falha_adaptacao_oral",
                    erro_oralidade,
                    fallback="texto_original",
                    fase="preparar_tts",
                )
                texto_voz = texto_exibicao
            self.log("")
            self.log(self.formatar_mensagem(texto_exibicao, emocao=emocao, nivel=nivel))

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_file = f.name

            rate, pitch, volume = self.modular_audio_params(emocao, nivel)
            # A fronteira do TTS também valida os parâmetros. Assim, uma
            # emoção nova ou um perfil externo não consegue derrubar a voz
            # inteira por devolver ``0%`` ou uma string vazia.
            rate = self._normalizar_percentual_edge(rate)
            volume = self._normalizar_percentual_edge(volume)
            inicio_sintese = time.perf_counter()
            self._sintetizar_edge(
                texto_voz,
                temp_file,
                rate=rate,
                pitch=pitch,
                volume=volume,
            )
            if callable(self.registrar_metrica_cb):
                self.registrar_metrica_cb(
                    "tts_sintese", (time.perf_counter() - inicio_sintese) * 1000.0, True,
                )

            data, samplerate = self.sf.read(temp_file)

            self.ducking_volume(True)
            try:
                self.sd.play(data, samplerate, device=self._selecionar_saida_audio())
                # A fila fica ocupada durante a síntese, mas o avatar só deve
                # mexer a boca quando o dispositivo realmente recebeu o áudio.
                self.ajustar_estado_fala_cb("audio_playing", True)
                while self.sd.get_stream().active:
                    if self.interrupt_event.is_set():
                        self.sd.stop()
                        self.log("🛑 [BARGE-IN] Fala interrompida pelo usuário!")
                        break
                    time.sleep(0.03)
                sucesso = True
            finally:
                self.ducking_volume(False)

        except Exception as e:
            self.ajustar_estado_fala_cb("audio_playing", False)
            self.log(f"❌ [FALA] Erro no áudio: {type(e).__name__} → {e}")
            if callable(self.registrar_falha_cb):
                self.registrar_falha_cb(
                    "tts", "falha_audio", erro=e,
                    classe="degradacao", impacto="fala",
                    fallback="tts_local_pyttsx",
                )
            try:
                self.fallback_pyttsx(texto, emocao)
            except Exception as erro_fallback:
                self.log(
                    f"❌ [FALA:FALLBACK] {type(erro_fallback).__name__}: {erro_fallback}"
                )
                if callable(self.registrar_falha_cb):
                    self.registrar_falha_cb(
                        "tts", "falha_fallback", erro=erro_fallback,
                        classe="defeito", impacto="fala", fallback="nenhum",
                    )
        finally:
            if callable(self.registrar_metrica_cb):
                self.registrar_metrica_cb(
                    "tts_total", (time.perf_counter() - inicio_total) * 1000.0, sucesso,
                )
            self.ajustar_estado_fala_cb("audio_playing", False)
            self.ajustar_estado_fala_cb("is_speaking", False)
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except OSError:
                    # Limpeza best-effort: o áudio já foi encerrado e o SO
                    # pode manter o arquivo temporário bloqueado por instantes.
                    pass

    def worker_de_falas(self):
        while not self.stop_event.is_set():
            try:
                item = self.fila.get(timeout=0.25)
            except Empty:
                continue
            if item is None:
                continue

            # Cada item representa uma fala já consolidada pelo turno canônico.
            # Agrupar itens só porque chegaram perto no relógio misturava
            # respostas independentes (por exemplo, uma falha IoT com a
            # confirmação de abertura de um app).
            lote = [item]

            for pedido in lote:
                if not isinstance(pedido, dict) or not pedido.get("dinamizar", True):
                    continue
                with self._turno_lock:
                    pedido["em_reproducao"] = True
                pedido["texto"] = ajustar_abertura_repetida(
                    pedido.get("texto", ""),
                    self.aberturas_fala_recentes,
                )
                pedido["texto"], self.ultimo_uso_nome_ts = ajustar_uso_natural_nome(
                    pedido.get("texto", ""),
                    pedido.get("emocao", "calma"),
                    self.ultimo_uso_nome_ts,
                    nome_usuario=(
                        str(self.nome_usuario_cb() or "")
                        if callable(self.nome_usuario_cb)
                        else ""
                    ),
                )

            texto_final, emocao, nivel = self.combinar_falas_batch(lote)
            for pedido in lote:
                if isinstance(pedido, dict):
                    self._iniciar_itens_proativos(
                        list(pedido.get("proativas_mescladas") or []), self.log,
                    )
            self.ajustar_estado_fala_cb("current_emotion", emocao)
            self.ajustar_estado_fala_cb("emotion_level", nivel)
            self.ajustar_estado_fala_cb("is_speaking", True)
            try:
                self.reproduzir_fala(texto_final, emocao, nivel)
            finally:
                for pedido in lote:
                    if isinstance(pedido, dict):
                        itens_mesclados = list(pedido.get("proativas_mescladas") or [])
                        if itens_mesclados:
                            if callable(self.registrar_fala_emitida_cb):
                                try:
                                    self.registrar_fala_emitida_cb(pedido.get("texto", ""), itens_mesclados)
                                except Exception as erro_registro:
                                    self.log(f"⚠️ [FALA PROATIVA] falha ao registrar contexto: {erro_registro}")
                                    self._relatar_falha(
                                        "falha_registrar_contexto_proativo",
                                        erro_registro,
                                        impacto="servico",
                                        fallback="fala_entregue_sem_registro",
                                        fase="finalizar_fala",
                                    )
                            self._concluir_itens_proativos(itens_mesclados, True, "mesclada_ao_turno", self.log)
                        with self._turno_lock:
                            if pedido is self._pedido_turno_pendente:
                                self._pedido_turno_pendente = None
                        ev = pedido.get("done_event")
                        if ev is not None:
                            try:
                                ev.set()
                            except Exception as erro:
                                self._relatar_falha(
                                    "falha_sinalizar_fala_concluida",
                                    erro,
                                    classe="defeito",
                                    impacto="servico",
                                    fallback="espera_expira_pelo_chamador",
                                    fase="finalizar_fala",
                                )

    def encerrar(self, timeout_s: float = 1.0) -> None:
        self.stop_event.set()
        try:
            self.fila.put_nowait(None)
        except Exception as erro:
            self.log(f"⚠️ [FALA] fila não aceitou sinal de encerramento: {erro}")
            self._relatar_falha(
                "falha_encerrar_fila",
                erro,
                impacto="servico",
                fallback="encerramento_por_evento",
                fase="encerrar_servico",
            )
        thread = self._worker_thread
        if (
            thread is not None
            and callable(getattr(thread, "join", None))
            and thread is not threading.current_thread()
        ):
            try:
                thread.join(timeout=max(0.0, float(timeout_s)))
            except (RuntimeError, TypeError):
                pass

    def normalizar_segmento_fala(self, texto: str) -> str:
        t = self.limpar_para_voz(str(texto or "")).strip()
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            return ""
        if t[-1] not in ".!?…":
            t += "."
        return t

    def _reagendar_itens_proativos(
        self,
        itens: list[dict],
        *,
        motivo: str,
        atraso_s: float = 8.0,
    ) -> None:
        """Adia sinais ainda úteis e encerra os que perderam a validade."""
        agora = time.time()
        ativos = []
        expirados = []
        for item in itens:
            if not isinstance(item, dict):
                continue
            expira_ts = float(item.get("expira_ts") or 0.0)
            if expira_ts and agora >= expira_ts:
                expirados.append(item)
                continue
            item["nao_antes_ts"] = agora + max(0.5, float(atraso_s))
            item["adiamentos"] = int(item.get("adiamentos") or 0) + 1
            ativos.append(item)
        if expirados:
            self._concluir_itens_proativos(expirados, False, f"expirada:{motivo}", self.log)
        if not ativos:
            return
        with self.proativa_lock:
            self.proativa_buffer.extend(ativos)
            timer_ativo = bool(self.proativa_timer and self.proativa_timer.is_alive())
            if not timer_ativo:
                self.proativa_timer = self.timer_factory(
                    max(0.5, float(atraso_s)), self.flush_fala_proativa,
                )
                self.proativa_timer.daemon = True
                self.proativa_timer.start()
        self.log(
            f"🧠 [FALA PROATIVA] {len(ativos)} item(ns) adiado(s) | motivo={motivo}"
        )

    def flush_fala_proativa(self):
        with self._turno_lock:
            turno_ativo = self._turno_resposta_ativo
            chave_ativa = self._chave_turno_ativo
        agora = time.time()
        with self.proativa_lock:
            itens = []
            retidos = []
            for item in self.proativa_buffer:
                chave_item = float(item.get("turno_chave") or 0.0) if isinstance(item, dict) else 0.0
                nao_antes = float(item.get("nao_antes_ts") or 0.0) if isinstance(item, dict) else 0.0
                if nao_antes > agora:
                    retidos.append(item)
                elif (
                    turno_ativo
                    and isinstance(item, dict)
                    and item.get("mesclar_turno")
                    and (not chave_item or not chave_ativa or chave_item == chave_ativa)
                ):
                    retidos.append(item)
                else:
                    itens.append(item)
            self.proativa_buffer = retidos
            self.proativa_timer = None
            if retidos:
                prazos = [
                    float(item.get("nao_antes_ts") or 0.0) - agora
                    for item in retidos
                    if isinstance(item, dict) and float(item.get("nao_antes_ts") or 0.0) > agora
                ]
                if prazos:
                    atraso = max(0.5, min(prazos))
                    self.proativa_timer = self.timer_factory(atraso, self.flush_fala_proativa)
                    self.proativa_timer.daemon = True
                    self.proativa_timer.start()

        if not itens:
            return

        persistentes = [
            item for item in itens
            if isinstance(item, dict) and item.get("preservar_ate_entrega")
        ]
        comuns = [item for item in itens if item not in persistentes]
        if persistentes and comuns:
            # A permissao excepcional do briefing pendente nao pode carregar
            # junto sugestoes comuns que o porteiro ainda mandaria esperar.
            self._reagendar_itens_proativos(
                comuns, motivo="aguardando_entrega_persistente", atraso_s=8.0,
            )
            itens = persistentes

        def concluir(entregue: bool, motivo: str) -> None:
            self._concluir_itens_proativos(itens, entregue, motivo, self.log)

        inicio_forcado = any(bool(item.get("forcar_inicio")) for item in itens if isinstance(item, dict))
        entrega_persistente = any(
            bool(item.get("preservar_ate_entrega"))
            for item in itens if isinstance(item, dict)
        )
        presenca_jogo_validada = any(
            str(item.get("tipo") or "").strip().casefold() == "presenca_jogo"
            for item in itens if isinstance(item, dict)
        )
        # Um briefing que perdeu a corrida para a primeira entrada do usuario
        # deixa de ser uma abertura, mas continua sendo uma entrega pendente.
        # Ele nunca pode falar enquanto a resposta desse turno ainda esta sendo
        # construida ou reproduzida.
        if entrega_persistente and turno_ativo:
            self._reagendar_itens_proativos(
                itens, motivo="turno_usuario_ativo", atraso_s=2.0,
            )
            return
        if inicio_forcado and callable(self.proativa_permitida_cb):
            try:
                inicio_ainda_pertinente = bool(self.proativa_permitida_cb())
            except Exception as erro:
                self._relatar_falha(
                    "falha_porteiro_inicio",
                    erro,
                    impacto="servico",
                    fallback="abertura_descartada",
                    fase="avaliar_fala_proativa",
                )
                inicio_ainda_pertinente = False
            if not inicio_ainda_pertinente:
                # O briefing/abertura pode ter sido preparado enquanto os
                # controles já aceitavam entrada. Se Pedro falou ou abriu o
                # chat nesse intervalo, a saudação deixou de ser inicial e
                # não deve atravessar a conversa que já começou.
                self.log("🧠 [FALA INICIAL] descartada porque a conversa já começou")
                concluir(False, "interacao_iniciada")
                return
        intervalo_pos_fala = 2.0 if entrega_persistente else 30.0
        if not inicio_forcado and time.time() - float(self._ultima_fala_normal_ts or 0.0) < intervalo_pos_fala:
            if callable(self.avaliar_proatividade_cb):
                self._reagendar_itens_proativos(
                    itens,
                    motivo="fala_recente",
                    atraso_s=2.0 if entrega_persistente else 8.0,
                )
                return
            self.log("🧠 [FALA PROATIVA] descartada por fala recente")
            concluir(False, "fala_recente")
            return

        if (
            not inicio_forcado
            and not entrega_persistente
            and not presenca_jogo_validada
            and callable(self.proativa_permitida_cb)
        ):
            try:
                if not self.proativa_permitida_cb():
                    if callable(self.avaliar_proatividade_cb):
                        self._reagendar_itens_proativos(
                            itens, motivo="conversa_ativa", atraso_s=10.0,
                        )
                        return
                    self.log("🧠 [FALA PROATIVA] descartada para não atravessar a conversa")
                    concluir(False, "conversa_ativa")
                    return
            except Exception as erro:
                self._relatar_falha(
                    "falha_porteiro_proativo",
                    erro,
                    impacto="servico",
                    fallback="fala_proativa_descartada",
                    fase="avaliar_fala_proativa",
                )
                concluir(False, "falha_porteiro")
                return

        try:
            texto, emocao, nivel = self.compor_fala_proativa_cb(itens)
        except Exception as erro:
            self.log(f"⚠️ [FALA PROATIVA] falha ao compor lote: {type(erro).__name__}: {erro}")
            self._relatar_falha(
                "falha_compor_lote_proativo",
                erro,
                fallback="ultimo_item_valido",
                fase="compor_fala_proativa",
            )
            ultimo = next(
                (item for item in reversed(itens) if isinstance(item, dict) and str(item.get("texto") or "").strip()),
                {},
            )
            texto = str(ultimo.get("texto") or self.fallback_fala).strip()
            emocao = str(ultimo.get("emocao") or "calma")
            nivel = int(ultimo.get("nivel") or 1)
        try:
            self._iniciar_itens_proativos(itens, self.log)
            entregue = bool(self.falar(texto, emocao, nivel, wait=True, _proativa=True))
            if entregue:
                # Uma fala unificada também ocupa o espaço conversacional.
                # Sem isso, outra habilidade proativa poderia falar logo após
                # o lote e recriar a fragmentação que o árbitro acabou de evitar.
                self._ultima_fala_normal_ts = time.time()
                if callable(self.registrar_fala_emitida_cb):
                    try:
                        self.registrar_fala_emitida_cb(texto, itens)
                    except Exception as erro_registro:
                        self.log(f"⚠️ [FALA PROATIVA] falha ao registrar contexto: {erro_registro}")
                        self._relatar_falha(
                            "falha_registrar_contexto_proativo",
                            erro_registro,
                            impacto="servico",
                            fallback="fala_entregue_sem_registro",
                            fase="finalizar_fala_proativa",
                        )
            concluir(entregue, "entregue" if entregue else "fila_recusou")
        except Exception as erro:
            self.log(f"⚠️ [FALA PROATIVA] falha ao entregar lote: {type(erro).__name__}: {erro}")
            self._relatar_falha(
                "falha_entregar_lote_proativo",
                erro,
                fallback="lote_descartado",
                fase="entregar_fala_proativa",
            )
            concluir(False, "falha_entrega")

    def agendar_fala_proativa(
        self,
        tipo: str,
        texto: str,
        emocao: str = "calma",
        nivel: int = 1,
        *,
        ao_iniciar: Callable[[], Any] | None = None,
        ao_concluir: Callable[[bool, str], Any] | None = None,
        forcar_inicio: bool = False,
        mesclar_turno: bool = False,
        preservar_ate_entrega: bool = False,
    ):
        tipo_norm = str(tipo or "").strip().lower()
        texto_limpo = str(texto or "").strip()
        if not texto_limpo:
            self.log("⚠️ [FALA PROATIVA] item vazio ignorado")
            if callable(ao_concluir):
                ao_concluir(False, "item_vazio")
            return False
        inicio_forcado = bool(forcar_inicio) and (
            time.time() - self.proativa_inicio_sistema <= self.proativa_janela_startup + 5.0
        )
        with self._turno_lock:
            turno_ativo = self._turno_resposta_ativo
            chave_turno = self._chave_turno_ativo
        politica = {}
        if callable(self.avaliar_proatividade_cb):
            try:
                politica = self.avaliar_proatividade_cb(
                    tipo=tipo_norm,
                    texto=texto_limpo,
                    turno_ativo=turno_ativo,
                    mesclar_turno=bool(mesclar_turno),
                    inicio_forcado=inicio_forcado,
                    ultima_fala_normal_ts=float(self._ultima_fala_normal_ts or 0.0),
                ) or {}
            except Exception as erro:
                self.log(f"⚠️ [FALA PROATIVA] porteiro falhou: {erro}")
                self._relatar_falha(
                    "falha_politica_proativa",
                    erro,
                    impacto="servico",
                    fallback="politica_compatibilidade",
                    fase="agendar_fala_proativa",
                )
                politica = {}
        acao_politica = str(politica.get("acao") or "").strip().lower()
        if preservar_ate_entrega:
            # A politica pode adiar o briefing, mas nao apagar uma entrega
            # diaria que ja foi preparada e ainda nao chegou ao usuario. O
            # proprio turno ativo ja funciona como barreira; depois dele, dois
            # segundos bastam para a fala nao parecer colada na resposta.
            acao_politica = "adiar"
            politica = {
                **politica,
                "acao": "adiar",
                "adiar_s": 2.0,
                "validade_s": max(21600.0, float(politica.get("validade_s") or 0.0)),
            }
        if acao_politica == "descartar":
            self.log(
                "🧠 [FALA PROATIVA] descartada pelo porteiro | "
                f"tipo={tipo_norm} | pontos={politica.get('pontuacao')} | "
                f"motivos={politica.get('motivos') or []}"
            )
            if callable(ao_concluir):
                ao_concluir(False, "politica_descartou")
            return False
        reservar_para_turno = bool(
            turno_ativo
            and (
                acao_politica == "mesclar"
                or (not politica and mesclar_turno)
            )
        )
        adiar_pela_politica = acao_politica == "adiar"
        if politica:
            self.log(
                "🧠 [FALA PROATIVA] decisão do porteiro | "
                f"tipo={tipo_norm} | acao={acao_politica or 'compatibilidade'} | "
                f"pontos={politica.get('pontuacao')}"
            )
        if not preservar_ate_entrega and not politica and not inicio_forcado and not reservar_para_turno and time.time() - float(self._ultima_fala_normal_ts or 0.0) < 30.0:
            if callable(ao_concluir):
                ao_concluir(False, "fala_recente")
            return False
        if not preservar_ate_entrega and not politica and not inicio_forcado and not reservar_para_turno and callable(self.proativa_permitida_cb):
            try:
                if not self.proativa_permitida_cb():
                    if callable(ao_concluir):
                        ao_concluir(False, "conversa_ativa")
                    return False
            except Exception as erro:
                self._relatar_falha(
                    "falha_porteiro_proativo",
                    erro,
                    impacto="servico",
                    fallback="fala_proativa_descartada",
                    fase="agendar_fala_proativa",
                )
                if callable(ao_concluir):
                    ao_concluir(False, "falha_porteiro")
                return False
        item = {
            "tipo": tipo_norm,
            "texto": texto_limpo,
            "emocao": emocao,
            "nivel": nivel,
            "ts": time.time(),
            "ao_iniciar": ao_iniciar,
            "ao_concluir": ao_concluir,
            "forcar_inicio": inicio_forcado,
            "preservar_ate_entrega": bool(preservar_ate_entrega),
            "mesclar_turno": reservar_para_turno,
            "turno_chave": chave_turno if reservar_para_turno else 0.0,
            "politica": dict(politica),
            "nao_antes_ts": time.time() + float(politica.get("adiar_s") or 0.0)
            if adiar_pela_politica else 0.0,
            "expira_ts": time.time() + (
                max(21600.0, float(politica.get("validade_s") or 0.0))
                if preservar_ate_entrega
                else float(politica.get("validade_s") or 180.0)
            )
            if politica and not inicio_forcado else 0.0,
        }
        if reservar_para_turno:
            with self._turno_lock:
                pedido_pendente = self._pedido_turno_pendente
                if isinstance(pedido_pendente, dict) and not pedido_pendente.get("em_reproducao"):
                    pedido_pendente["texto"] = self._mesclar_fala_do_turno(
                        pedido_pendente.get("texto", ""),
                        [item],
                    )
                    pedido_pendente.setdefault("proativas_mescladas", []).append(item)
                    self.log("🧠 [FALA] observação da autonomia anexada à resposta já enfileirada")
                    return True
        with self.proativa_lock:
            self.proativa_buffer.append(item)
            # A resposta principal recolhe este item. Um timer concorrente não
            # pode fazê-lo falar sozinho no meio da geração da IA.
            if reservar_para_turno:
                return True
            if self.proativa_timer and self.proativa_timer.is_alive():
                # O item entrou no lote existente. Retornar ``None`` fazia o
                # chamador acreditar que a entrega tinha falhado, embora a
                # fala ainda fosse sair no flush.
                return True
            atraso = max(
                self.proativa_delay,
                float(politica.get("adiar_s") or 0.0) if adiar_pela_politica else 0.0,
            )
            idade_sistema = time.time() - self.proativa_inicio_sistema
            if tipo_norm in {"briefing", "emails", "rotina", "musica"} and idade_sistema < self.proativa_janela_startup:
                atraso = max(self.proativa_delay, self.proativa_janela_startup - idade_sistema)
                self.log(f"🧠 [FALA PROATIVA] aguardando {atraso:.1f}s para unificar falas iniciais")
            self.proativa_timer = self.timer_factory(atraso, self.flush_fala_proativa)
            self.proativa_timer.daemon = True
            self.proativa_timer.start()
        return True

    def falar(self, texto: str, emocao: str = "calma", nivel: Optional[int] = None, wait: bool = False, _proativa: bool = False) -> bool:
        # Algumas rotas convergem na mesma confirmação operacional. Se ambas
        # chegarem quase juntas, a fila não deve reproduzir a frase duas vezes.
        # A janela curta não interfere num pedido posterior de "repete".
        assinatura_fala = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
        agora = time.monotonic()
        if not _proativa and assinatura_fala:
            with self._turno_lock:
                if (
                    assinatura_fala == self._ultima_solicitacao_fala
                    and agora - self._ultima_solicitacao_fala_ts <= 3.0
                ):
                    self.log("🧠 [FALA] duplicata idêntica do turno descartada")
                    return False
                self._ultima_solicitacao_fala = assinatura_fala
                self._ultima_solicitacao_fala_ts = agora
        pedido_existente = None
        chave = 0.0
        if not _proativa and callable(self.chave_turno_cb):
            try:
                chave = float(self.chave_turno_cb() or 0.0)
            except Exception as erro:
                self._relatar_falha(
                    "falha_chave_turno",
                    erro,
                    impacto="servico",
                    fallback="turno_sem_chave",
                    fase="enfileirar_fala",
                )
                chave = 0.0
            if chave > 0:
                itens_mesclados = self._retirar_proativas_do_turno(chave)
                with self._turno_lock:
                    if chave == self._ultima_chave_turno_emitida:
                        pedido_existente = self._pedido_turno_pendente
                        if isinstance(pedido_existente, dict):
                            prioridade_nova = self._prioridade_candidato_fala(texto)
                            prioridade_atual = int(pedido_existente.get("prioridade") or 0)
                            if prioridade_nova >= prioridade_atual:
                                if itens_mesclados:
                                    texto = self._mesclar_fala_do_turno(texto, itens_mesclados)
                                pedido_existente.update({
                                    "texto": texto,
                                    "emocao": emocao,
                                    "nivel": nivel if nivel is not None else 1,
                                    "prioridade": prioridade_nova,
                                })
                                pedido_existente.setdefault("proativas_mescladas", []).extend(itens_mesclados)
                                self.log("🧠 [FALA] candidato do turno substituído por resposta mais útil")
                            else:
                                if itens_mesclados:
                                    pedido_existente["texto"] = self._mesclar_fala_do_turno(
                                        pedido_existente.get("texto", ""),
                                        itens_mesclados,
                                    )
                                    pedido_existente.setdefault("proativas_mescladas", []).extend(itens_mesclados)
                                self.log("🧠 [FALA] candidato inferior do mesmo turno descartado")
                                return False
                        else:
                            self.log("🧠 [FALA] resposta tardia do mesmo turno descartada")
                            return False
                        return True
                    self._ultima_chave_turno_emitida = chave
            else:
                itens_mesclados = self._retirar_proativas_do_turno(chave)
        else:
            itens_mesclados = []
        if itens_mesclados:
            texto = self._mesclar_fala_do_turno(texto, itens_mesclados)
            self.log(f"🧠 [FALA] {len(itens_mesclados)} observação(ões) da autonomia mesclada(s) ao turno")
        if not _proativa:
            self._ultima_fala_normal_ts = time.time()
        self.iniciar_worker()
        nivel_final = nivel if nivel is not None else 1
        done_event = threading.Event()
        pedido = {
            "texto": texto,
            "emocao": emocao,
            "nivel": nivel_final,
            "done_event": done_event,
            "dinamizar": True,
            "prioridade": self._prioridade_candidato_fala(texto),
            "proativas_mescladas": itens_mesclados,
        }
        if not _proativa and callable(self.chave_turno_cb):
            with self._turno_lock:
                self._pedido_turno_pendente = pedido
        self.fila.put(pedido)
        if wait:
            done_event.wait()
        return True

    def fallback_pyttsx(self, texto: str, emocao_atual: str):
        if not self._fallback_tts_disponivel:
            return False
        caminho = None
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
                self.sd.play(data, sr_val, device=self._selecionar_saida_audio())
                self.ajustar_estado_fala_cb("audio_playing", True)
                self.sd.wait()
            finally:
                self.ajustar_estado_fala_cb("audio_playing", False)
                self.ducking_volume(False)

            return True
        except Exception as e:
            # Alguns ambientes Windows ficam com o cache COM gerado inválido
            # (por exemplo, um arquivo SpeechLib com IndentationError). Não
            # tente importar o mesmo fallback quebrado a cada fala.
            self._fallback_tts_disponivel = False
            self.log(
                "⚠️ [FALA] fallback local desativado nesta execução: "
                f"{type(e).__name__}: {e}"
            )
            self._relatar_falha(
                "falha_fallback_local",
                e,
                classe="defeito",
                fallback="nenhum",
                fase="fallback_tts",
            )
            return False
        finally:
            if caminho and os.path.exists(caminho):
                try:
                    os.unlink(caminho)
                except OSError:
                    # Mesma fronteira best-effort da limpeza do TTS neural.
                    pass


def criar_voz_runtime(**kwargs) -> VozRuntime:
    return VozRuntime(**kwargs)
