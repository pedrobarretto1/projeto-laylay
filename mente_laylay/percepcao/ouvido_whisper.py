"""Ouvido Whisper da Laylay.

Este modulo concentra limpeza de diccao e transcricao de voz, mantendo o
`laylay.py` como orquestrador em vez de carregar detalhes do ouvido.
"""

from __future__ import annotations

from collections import deque
from difflib import SequenceMatcher
import os
import queue
import re
import threading
import time
from typing import Any, Callable

from mente_laylay.percepcao.normalizacao_fonetica import (
    corrigir_entrada_fonetica,
    extrair_ensino_pronuncia,
    normalizar_fonetico,
)
from mente_laylay.percepcao.dispositivos_audio import selecionar_dispositivo_audio
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)

def limpar_diccao_e_ruido(texto_falado: str) -> str:
    """Filtro anti-ruido + corretor de diccao para reduzir alucinacoes do Whisper."""
    texto = str(texto_falado or "").lower().strip()

    alucinacoes = [
        "obrigado por assistir",
        "inscreva-se",
        "editado por",
        "amara.org",
        "transmissão ao vivo",
    ]
    for alucinacao in alucinacoes:
        if texto == alucinacao or texto == alucinacao + ".":
            return ""

    dicionario_correcao = {
        "canista minha terra": "organiza minha tela",
        "o canista minha terra": "organiza minha tela",
        "orcaniça": "organiza",
        "ocaniça": "organiza",
        "organisa": "organiza",
        "organaiza": "organiza",
        "mi yaya": "minha tela",
        "adiata": "tela",
        "opede": "opera",
        "opeditor": "opera",
        "whatsappi": "whatsapp",
        "whatsapi": "whatsapp",
        "pedu": "pelo",
        "teta cheia": "tela cheia",
        "coigo": "código",
        "muica": "música",
        "muisca": "música",
        "próima": "próxima",
        "proxima": "próxima",
        "lica": "liga",
    }

    for errado, certo in sorted(dicionario_correcao.items(), key=lambda item: len(item[0]), reverse=True):
        texto = re.sub(
            rf"(?<!\w){re.escape(errado)}(?!\w)",
            certo,
            texto,
            flags=re.IGNORECASE,
        )

    # Flexões comuns produzidas pelo reconhecimento de voz são corrigidas
    # somente quando têm formato operacional, sem alterar conversa comum.
    texto = re.sub(
        r"\bdesligo(?=\s+(?:a|o|as|os)?\s*(?:luz|lampada|lâmpada|ventilador|tomada)\b)",
        "desliga",
        texto,
        flags=re.IGNORECASE,
    )
    texto = re.sub(
        r"\b((?:liga|desliga|acende|apaga)\s+(?:a|o)?\s*)luis\b",
        r"\1luz",
        texto,
        flags=re.IGNORECASE,
    )
    return texto.strip()


def extrair_comando_com_ativacao(texto: str) -> tuple[bool, str]:
    """Aceita Lay/Laylay no começo e devolve somente o comando posterior."""
    t = re.sub(r"\s+", " ", str(texto or "").casefold()).strip(" .!?;:")
    match = re.match(
        r"^(?:(?:ei|oi|ol[áa]|ok|okay)\s+)?(?:laylay|lay|lai|leilei|lelei|leil[eêií]|l[eê]i?\s*[,.-]?\s*l[eê]i?)\b[\s,;:.-]*(.*)$",
        t,
    )
    if not match:
        return False, ""
    return True, str(match.group(1) or "").strip()


class OuvidoWhisperRuntime:
    """Captura voz com sounddevice e entrega a transcrição à mente única."""

    def __init__(
        self,
        *,
        processar_texto: Callable[[str], Any],
        esta_falando: Callable[[], bool],
        escuta_permitida: Callable[[], bool] | None = None,
        modo_chat_ativo: Callable[[], bool] | None = None,
        modo_jogo_ativo: Callable[[], bool] | None = None,
        ultima_fala_laylay: Callable[[], str] | None = None,
        vocabulario_dinamico: Callable[[], Any] | None = None,
        pronuncias_aprendidas: Callable[[], dict[str, str]] | None = None,
        salvar_pronuncia: Callable[[str, str], bool] | None = None,
        reconhecer_comando_pessoal: Callable[[Any, int], dict[str, Any] | None] | None = None,
        solicitar_confirmacao: Callable[[str, str, int], Any] | None = None,
        sounddevice_mod: Any = None,
        numpy_mod: Any = None,
        model_factory: Callable[..., Any] | None = None,
        limpar_texto: Callable[[str], str] = limpar_diccao_e_ruido,
        log: Callable[..., Any] = print,
        env_getter: Callable[[str, str], str] | None = None,
        deve_continuar: Callable[[], bool] | None = None,
        atividade_visual: Callable[[str], Any] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        entrega_assincrona: bool = True,
    ) -> None:
        self.processar_texto = processar_texto
        self.esta_falando = esta_falando
        self.escuta_permitida = escuta_permitida or (lambda: True)
        self.modo_chat_ativo = modo_chat_ativo or (lambda: False)
        self.modo_jogo_ativo = modo_jogo_ativo or (lambda: False)
        self.ultima_fala_laylay = ultima_fala_laylay or (lambda: "")
        self.vocabulario_dinamico = vocabulario_dinamico or (lambda: [])
        self.pronuncias_aprendidas = pronuncias_aprendidas or (lambda: {})
        self.salvar_pronuncia = salvar_pronuncia
        self.reconhecer_comando_pessoal = reconhecer_comando_pessoal
        self.solicitar_confirmacao = solicitar_confirmacao
        self.sd = sounddevice_mod
        self.np = numpy_mod
        self.model_factory = model_factory
        self.limpar_texto = limpar_texto
        self.log = log
        self.env_getter = env_getter or (lambda nome, padrao="": os.getenv(nome, padrao))
        self.deve_continuar = deve_continuar or (lambda: True)
        self.atividade_visual = atividade_visual
        self.monotonic = monotonic
        self.entrega_assincrona = bool(entrega_assincrona)
        self._lock_transcricao = threading.Lock()
        self._fila_audio: queue.Queue[Any] = queue.Queue(maxsize=2)
        self._worker_audio: threading.Thread | None = None
        self._worker_lock = threading.Lock()
        self._ativado_ate = 0.0
        self._ultima_fala_laylay_ts = 0.0
        self._confirmacao_pendente: dict[str, Any] = {}
        self._ultimo_comando_assinatura = ""
        self._ultimo_comando_ts = 0.0
        self._ultima_metricas_transcricao: dict[str, Any] = {}
        self._nivel_microfone = 0.0
        self.modelo = None
        self.dispositivo: int | None = None
        self.taxa_captura = 16000
        self.taxa_whisper = 16000

    def _env(self, nome: str, padrao: str = "") -> str:
        try:
            return str(self.env_getter(nome, padrao) or padrao).strip()
        except Exception:
            return str(padrao or "").strip()

    def ativo(self) -> bool:
        return self._env("LAYLAY_MICROFONE_ATIVO", "1").casefold() not in {
            "0", "false", "nao", "não", "off", "desligado",
        }

    def nivel_microfone(self) -> float:
        """Nível normalizado e efêmero para visualização; não expõe áudio."""
        try:
            return max(0.0, min(1.0, float(self._nivel_microfone)))
        except (TypeError, ValueError):
            return 0.0

    def _dependencias(self) -> tuple[Any, Any]:
        sd = self.sd
        np = self.np
        if sd is None:
            import sounddevice as sd_importado

            sd = sd_importado
            self.sd = sd
        if np is None:
            import numpy as np_importado

            np = np_importado
            self.np = np
        return sd, np

    @staticmethod
    def _nome_dispositivo(info: Any) -> str:
        try:
            return str(info.get("name") or "microfone")
        except Exception:
            return "microfone"

    def selecionar_dispositivo(self) -> tuple[int, dict[str, Any]]:
        sd, _ = self._dependencias()
        pedido = self._env("LAYLAY_MICROFONE", "")
        indice, info, origem = selecionar_dispositivo_audio(sd, "entrada", pedido)
        taxa_desejada = int(float(self._env("LAYLAY_MICROFONE_SAMPLE_RATE", "16000")))
        try:
            sd.check_input_settings(
                device=indice, channels=1, dtype="float32", samplerate=taxa_desejada,
            )
            taxa = taxa_desejada
        except Exception:
            taxa = int(float(info.get("default_samplerate") or 44100))
            sd.check_input_settings(device=indice, channels=1, dtype="float32", samplerate=taxa)
        self.dispositivo = indice
        self.taxa_captura = taxa
        self._origem_dispositivo = origem
        return indice, info

    def carregar_modelo(self) -> Any:
        if self.modelo is not None:
            return self.modelo
        factory = self.model_factory
        if factory is None:
            from faster_whisper import WhisperModel

            factory = WhisperModel
        modelo = self._env("LAYLAY_WHISPER_MODELO", "turbo")
        self.log(f"🎙️ [OUVIDO] Carregando Whisper {modelo}...")
        self.modelo = factory(
            modelo,
            device=self._env("LAYLAY_WHISPER_DEVICE", "cpu"),
            compute_type=self._env("LAYLAY_WHISPER_COMPUTE_TYPE", "int8"),
        )
        return self.modelo

    def _reamostrar(self, audio: Any) -> Any:
        _, np = self._dependencias()
        vetor = np.asarray(audio, dtype=np.float32).reshape(-1)
        if self.taxa_captura == self.taxa_whisper or not len(vetor):
            return vetor
        tamanho = max(1, round(len(vetor) * self.taxa_whisper / self.taxa_captura))
        origem = np.linspace(0.0, 1.0, num=len(vetor), endpoint=False)
        destino = np.linspace(0.0, 1.0, num=tamanho, endpoint=False)
        return np.interp(destino, origem, vetor).astype(np.float32)

    def _vocabulario(self) -> list[str]:
        try:
            itens = list(self.vocabulario_dinamico() or [])
        except Exception:
            itens = []
        try:
            itens.extend(dict(self.pronuncias_aprendidas() or {}).values())
        except Exception:
            pass
        unicos = []
        vistos = set()
        for item in itens:
            texto = re.sub(r"\s+", " ", str(item or "")).strip()
            chave = normalizar_fonetico(texto)
            if not chave or chave in vistos or len(texto) > 60:
                continue
            vistos.add(chave)
            unicos.append(texto)
        return unicos[:60]

    def _pronuncias(self) -> dict[str, str]:
        try:
            return {
                str(chave): str(valor)
                for chave, valor in dict(self.pronuncias_aprendidas() or {}).items()
                if str(chave).strip() and str(valor).strip()
            }
        except Exception:
            return {}

    @staticmethod
    def _comando_sensivel(texto: str) -> bool:
        t = normalizar_fonetico(texto)
        exclusao = bool(
            re.search(r"\b(?:apaga|apagar|deleta|deletar|exclui|excluir|remove|remover)\b", t)
            and re.search(r"\b(?:arquivo|pasta|documento|foto|video|download|desktop|area de trabalho)\b", t)
        )
        comunicacao = bool(re.search(
            r"\b(?:envia|enviar|manda|mandar)\b.*\b(?:mensagem|email|e-mail|whatsapp)\b",
            t,
        ))
        compromisso = bool(re.search(
            r"\b(?:compra|comprar|paga|pagar|agenda|agendar|lembra|lembrar|"
            r"cancela agendamento|cancelar agendamento)\b",
            t,
        ))
        return exclusao or comunicacao or compromisso

    def _duplicado_recente(self, comando: str, agora: float) -> bool:
        assinatura = normalizar_fonetico(comando)
        try:
            janela = max(0.2, float(self._env("LAYLAY_VOZ_DEDUP_SEGUNDOS", "2.0")))
        except ValueError:
            janela = 2.0
        if assinatura and assinatura == self._ultimo_comando_assinatura and agora - self._ultimo_comando_ts <= janela:
            return True
        self._ultimo_comando_assinatura = assinatura
        self._ultimo_comando_ts = agora
        return False

    def _pedir_confirmacao(self, comando: str, confianca: float, motivo: str) -> None:
        agora = self.monotonic()
        self._confirmacao_pendente = {
            "comando": comando,
            "confianca": confianca,
            "motivo": motivo,
            "expira": agora + 15.0,
        }
        self._ativado_ate = agora + 15.0
        fala = f"Eu entendi: {comando}. Foi isso?"
        self.log(
            f"🎙️ [OUVIDO:CONFIRMAÇÃO] motivo={motivo} confiança={confianca:.2f} comando={comando!r}"
        )
        if callable(self.solicitar_confirmacao):
            try:
                self.solicitar_confirmacao(fala, "calma", 1)
            except Exception as erro:
                self.log(f"⚠️ [OUVIDO] Não consegui pedir confirmação: {erro}")

    def _resolver_confirmacao(self, comando: str, agora: float) -> bool:
        pendente = dict(self._confirmacao_pendente or {})
        if not pendente:
            return False
        if agora > float(pendente.get("expira") or 0.0):
            self._confirmacao_pendente = {}
            return False
        resposta = normalizar_fonetico(comando)
        original = str(pendente.get("comando") or "").strip()
        decisao = classificar_confirmacao_local(resposta)
        if decisao is True:
            self._confirmacao_pendente = {}
            self._ativado_ate = 0.0
            if original and not self._duplicado_recente(original, agora):
                self.log(f"🎙️ [OUVIDO] Comando confirmado pelo usuário: {original}")
                self.processar_texto(original)
            return True
        # Repetir o mesmo comando é uma confirmação natural, especialmente
        # quando Pedro está corrigindo a dicção em vez de responder "sim".
        if original and SequenceMatcher(
            None, normalizar_fonetico(original), resposta,
        ).ratio() >= 0.88:
            self._confirmacao_pendente = {}
            self._ativado_ate = 0.0
            if not self._duplicado_recente(original, agora):
                self.log(f"🎙️ [OUVIDO] Comando confirmado pela repetição: {original}")
                self.processar_texto(original)
            return True
        if decisao is False:
            self._confirmacao_pendente = {}
            self._ativado_ate = 0.0
            self.log("🎙️ [OUVIDO] Transcrição rejeitada pelo usuário.")
            return True
        return False

    def transcrever_com_confianca(self, audio: Any) -> tuple[str, float]:
        modelo = self.carregar_modelo()
        vetor = self._reamostrar(audio)
        vocabulario = self._vocabulario()
        prompt_dinamico = ", ".join(vocabulario[:40])
        segmentos, info = modelo.transcribe(
            vetor,
            language="pt",
            initial_prompt=(
                "Laylay, lâmpada, ventilador, YouTube, Spotify, VS Code, WhatsApp, "
                "Opera, Chrome, música, brilho, vermelho, rosa, desligar e ligar. "
                + (f"Vocabulário atual: {prompt_dinamico}." if prompt_dinamico else "")
            ),
            beam_size=3,
            best_of=3,
            condition_on_previous_text=False,
            no_speech_threshold=0.65,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400},
        )
        segmentos = list(segmentos)
        bruto = " ".join(str(segmento.text or "").strip() for segmento in segmentos).strip()
        reprocessado = False
        if not bruto:
            # O VAD interno às vezes elimina comandos muito curtos de headsets
            # Bluetooth. A captura já passou pelo nosso VAD, então uma segunda
            # leitura sem esse filtro é segura e ocorre apenas no resultado vazio.
            segmentos_retry, info_retry = modelo.transcribe(
                vetor,
                language="pt",
                initial_prompt=(
                    "Comando curto dito pelo usuário para Laylay. Ligar, desligar, luz, "
                    "lâmpada, ventilador, brilho, volume. "
                    + (f"Vocabulário atual: {prompt_dinamico}." if prompt_dinamico else "")
                ),
                beam_size=3,
                best_of=3,
                condition_on_previous_text=False,
                no_speech_threshold=0.85,
                vad_filter=False,
            )
            segmentos = list(segmentos_retry)
            bruto = " ".join(str(segmento.text or "").strip() for segmento in segmentos).strip()
            info = info_retry
            reprocessado = True
        texto_limpo = re.sub(r"\s+", " ", self.limpar_texto(bruto)).strip()
        texto, correcoes = corrigir_entrada_fonetica(
            texto_limpo,
            entidades=vocabulario,
            pronuncias=self._pronuncias(),
        )
        probabilidades = []
        probabilidades_fala = []
        for segmento in segmentos:
            try:
                import math
                probabilidades.append(max(0.0, min(1.0, math.exp(float(segmento.avg_logprob)))))
            except (AttributeError, TypeError, ValueError, OverflowError):
                continue
            try:
                probabilidades_fala.append(1.0 - max(0.0, min(1.0, float(segmento.no_speech_prob))))
            except (AttributeError, TypeError, ValueError):
                pass
        confianca_log = sum(probabilidades) / len(probabilidades) if probabilidades else 0.75
        confianca_fala = sum(probabilidades_fala) / len(probabilidades_fala) if probabilidades_fala else 1.0
        try:
            valor_idioma = getattr(info, "language_probability", 1.0)
            confianca_idioma = float(1.0 if valor_idioma is None else valor_idioma)
        except (TypeError, ValueError):
            confianca_idioma = 1.0
        confianca = max(0.0, min(1.0, confianca_log * confianca_fala * max(0.65, confianca_idioma)))
        self._ultima_metricas_transcricao = {
            "original": bruto,
            "corrigido": texto,
            "confianca": round(confianca, 3),
            "confianca_log": round(confianca_log, 3),
            "confianca_fala": round(confianca_fala, 3),
            "confianca_idioma": round(confianca_idioma, 3),
            "correcoes": correcoes,
            "reprocessado": reprocessado,
        }
        return (texto if len(texto) >= 2 else ""), confianca

    def transcrever(self, audio: Any) -> str:
        return self.transcrever_com_confianca(audio)[0]

    def _parece_eco(self, texto: str) -> bool:
        if self.monotonic() - self._ultima_fala_laylay_ts > 3.0:
            return False
        referencia = re.sub(r"\W+", " ", str(self.ultima_fala_laylay() or "").casefold()).strip()
        ouvido = re.sub(r"\W+", " ", str(texto or "").casefold()).strip()
        if len(referencia) < 8 or len(ouvido) < 8:
            return False
        return ouvido in referencia or SequenceMatcher(None, ouvido, referencia).ratio() >= 0.78

    def _entregar(self, audio: Any) -> None:
        if callable(self.atividade_visual):
            self.atividade_visual("listening")
        try:
            self._entregar_impl(audio)
        finally:
            if callable(self.atividade_visual):
                self.atividade_visual("idle")

    def _entregar_impl(self, audio: Any) -> None:
        with self._lock_transcricao:
            if not bool(self.escuta_permitida()):
                return
            try:
                texto, confianca = self.transcrever_com_confianca(audio)
            except Exception as erro:
                self.log(f"⚠️ [OUVIDO] Falha ao transcrever: {erro}")
                return
            if not texto:
                metricas = dict(self._ultima_metricas_transcricao or {})
                bruto = re.sub(r"\s+", " ", str(metricas.get("original") or "")).strip()
                if bruto:
                    self.log(f"🗣️ [VOCÊ DISSE] {bruto}")
                    self.log("🎙️ [OUVIDO] A transcrição foi removida pelo filtro de ruído ou ficou curta demais.")
                else:
                    try:
                        duracao = len(audio) / float(self.taxa_captura or 16000)
                    except (TypeError, ValueError, ZeroDivisionError):
                        duracao = 0.0
                    self.log(
                        "🎙️ [OUVIDO] Ouvi áudio, mas o Whisper não formou texto "
                        f"({duracao:.1f}s, mesmo após nova tentativa)."
                    )
                return
            metricas = dict(self._ultima_metricas_transcricao or {})
            fala_ouvida = re.sub(
                r"\s+",
                " ",
                str(metricas.get("original") or texto),
            ).strip()
            if fala_ouvida:
                self.log(f"🗣️ [VOCÊ DISSE] {fala_ouvida}")
            ativou_pre, comando_pre = extrair_comando_com_ativacao(texto)
            if ativou_pre and comando_pre and callable(self.reconhecer_comando_pessoal):
                try:
                    pessoal = self.reconhecer_comando_pessoal(audio, self.taxa_captura)
                except Exception as erro:
                    pessoal = None
                    self.log(f"⚠️ [VOZ PESSOAL] Falha ao comparar comando: {erro}")
                comando_pessoal = str((pessoal or {}).get("comando") or "").strip()
                similaridade_textual = SequenceMatcher(
                    None,
                    normalizar_fonetico(comando_pre),
                    normalizar_fonetico(comando_pessoal),
                ).ratio() if comando_pessoal else 0.0
                if bool((pessoal or {}).get("aceito")) and similaridade_textual >= 0.46:
                    texto = f"laylay, {comando_pessoal}"
                    confianca = max(confianca, 0.90)
                    metricas["corrigido"] = texto
                    metricas.setdefault("correcoes", []).append({
                        "original": comando_pre,
                        "corrigido": comando_pessoal,
                        "motivo": "voz_pessoal",
                        "score": round(similaridade_textual, 3),
                    })
                    self.log(
                        "🎙️ [VOZ PESSOAL] "
                        f"comando={comando_pessoal!r} distância={pessoal.get('distancia')} "
                        f"margem={pessoal.get('margem')}"
                    )
            try:
                confianca_minima = float(self._env("LAYLAY_WHISPER_CONFIANCA_MINIMA", "0.30"))
            except ValueError:
                confianca_minima = 0.30
            try:
                confianca_alta = float(self._env("LAYLAY_WHISPER_CONFIANCA_ALTA", "0.62"))
            except ValueError:
                confianca_alta = 0.62
            if confianca < max(0.0, min(1.0, confianca_minima)):
                self.log(f"🎙️ [OUVIDO] Transcrição descartada por baixa confiança ({confianca:.2f}).")
                return
            self.log(
                "🎙️ [OUVIDO:LEITURA] "
                f"original={metricas.get('original', texto)!r} | corrigido={texto!r} | "
                f"confiança={confianca:.2f} | correções={metricas.get('correcoes') or []} | "
                f"nova_tentativa={bool(metricas.get('reprocessado'))}"
            )
            if self._parece_eco(texto):
                self.log("🎙️ [OUVIDO] Eco provável da voz da Laylay descartado.")
                return
            ativou, comando = extrair_comando_com_ativacao(texto)
            agora = self.monotonic()
            if ativou and not comando:
                self._ativado_ate = agora + 6.0
                self.log("🎙️ [OUVIDO] Palavra de ativação reconhecida; aguardando comando.")
                return
            if not ativou:
                if agora > self._ativado_ate:
                    self.log("🎙️ [OUVIDO] Fala ignorada por não começar com Lay ou Laylay.")
                    return
                comando = texto
            self._ativado_ate = 0.0
            if self._resolver_confirmacao(comando, agora):
                return

            ensino = extrair_ensino_pronuncia(comando)
            if ensino and callable(self.salvar_pronuncia):
                ouvido, correto = ensino
                try:
                    salvo = bool(self.salvar_pronuncia(ouvido, correto))
                except Exception as erro:
                    salvo = False
                    self.log(f"⚠️ [OUVIDO] Falha ao salvar pronúncia: {erro}")
                if salvo:
                    self.log(f"🎙️ [OUVIDO] Pronúncia aprendida: {ouvido!r} -> {correto!r}")
                    if callable(self.solicitar_confirmacao):
                        self.solicitar_confirmacao(
                            f"Entendi. Quando eu ouvir {ouvido}, vou considerar {correto}.",
                            "calma",
                            1,
                        )
                return

            if confianca < max(0.0, min(1.0, confianca_alta)):
                self._pedir_confirmacao(comando, confianca, "confianca_media")
                return
            if self._comando_sensivel(comando):
                self._pedir_confirmacao(comando, confianca, "acao_sensivel")
                return
            # O modo pode ter mudado enquanto o Whisper processava a frase.
            if not bool(self.escuta_permitida()):
                return
            if self._duplicado_recente(comando, agora):
                self.log("🎙️ [OUVIDO] Comando duplicado recente descartado.")
                return
            self.log(f"🎙️ [OUVIDO] Usuário: {comando}")
            try:
                if callable(self.atividade_visual):
                    self.atividade_visual("thinking")
                self.processar_texto(comando)
            except Exception as erro:
                self.log(f"⚠️ [OUVIDO] Falha ao entregar a fala para a mente: {erro}")
            finally:
                if callable(self.atividade_visual):
                    self.atividade_visual("idle")

    def _agendar_entrega(self, audio: Any) -> None:
        if not self.entrega_assincrona:
            self._entregar(audio)
            return
        with self._worker_lock:
            if self._worker_audio is None or not self._worker_audio.is_alive():
                self._worker_audio = threading.Thread(
                    target=self._consumir_fila_audio,
                    daemon=True,
                    name="Laylay-Whisper-Transcricao",
                )
                self._worker_audio.start()
        if self._fila_audio.full():
            try:
                self._fila_audio.get_nowait()
                self._fila_audio.task_done()
                self.log("🎙️ [OUVIDO] Áudio antigo descartado para manter comandos atuais.")
            except queue.Empty:
                pass
        self._fila_audio.put_nowait(audio)

    def _consumir_fila_audio(self) -> None:
        while self.deve_continuar():
            try:
                audio = self._fila_audio.get(timeout=0.25)
            except queue.Empty:
                continue
            try:
                self._entregar(audio)
            finally:
                self._fila_audio.task_done()

    def executar(self) -> None:
        if not self.ativo():
            self.log("🎙️ [OUVIDO] Microfone desativado por configuração.")
            return
        try:
            sd, np = self._dependencias()
            indice, info = self.selecionar_dispositivo()
            carregar_no_inicio = self._env(
                "LAYLAY_WHISPER_CARREGAR_NO_INICIO", "0"
            ).casefold() in {"1", "true", "sim", "yes", "on", "ligado"}
            if carregar_no_inicio:
                self.carregar_modelo()
        except Exception as erro:
            if bool(self.modo_chat_ativo()):
                return
            self.log(f"⚠️ [OUVIDO] Não consegui iniciar o microfone: {erro}")
            raise RuntimeError("falha ao iniciar captura do microfone") from erro

        bloco_s = 0.10
        bloco = max(160, int(self.taxa_captura * bloco_s))
        limiar_minimo = max(0.001, float(self._env("LAYLAY_MICROFONE_LIMIAR", "0.012")))
        calibracao_s = max(0.3, float(self._env("LAYLAY_MICROFONE_CALIBRACAO", "1.0")))
        silencio_final_s = max(0.4, float(self._env("LAYLAY_MICROFONE_SILENCIO", "0.9")))
        duracao_maxima_s = max(3.0, float(self._env("LAYLAY_MICROFONE_MAX_SEGUNDOS", "15")))
        preroll = deque(maxlen=max(2, round(0.3 / bloco_s)))
        gravando: list[Any] = []
        blocos_voz = 0
        silencio = 0.0
        ruido = limiar_minimo / 3.0
        amostras_calibracao: list[float] = []
        blocos_calibracao = max(3, round(calibracao_s / bloco_s))
        calibrado = False
        pico_sem_fala = 0.0
        ultimo_log_nivel = self.monotonic()
        ultimo_fim_fala = 0.0
        pausado_por_contexto = False
        calibracao_anunciada = False
        entrada_anunciada = False

        nome = self._nome_dispositivo(info)
        origem = str(getattr(self, "_origem_dispositivo", "padrão do sistema"))
        try:
            with sd.InputStream(
                device=indice,
                channels=1,
                samplerate=self.taxa_captura,
                dtype="float32",
                blocksize=bloco,
            ) as stream:
                while self.deve_continuar():
                    dados, overflow = stream.read(bloco)
                    chunk = np.asarray(dados, dtype=np.float32).reshape(-1).copy()
                    agora = self.monotonic()
                    if not bool(self.escuta_permitida()):
                        self._nivel_microfone = 0.0
                        gravando.clear()
                        preroll.clear()
                        blocos_voz = 0
                        silencio = 0.0
                        if not pausado_por_contexto:
                            self.log("🎙️ [OUVIDO] Pausado enquanto o modo chat está ativo.")
                            pausado_por_contexto = True
                        continue
                    if pausado_por_contexto:
                        self.log("🎙️ [OUVIDO] Retomado após sair do modo chat.")
                        pausado_por_contexto = False
                        ultimo_fim_fala = agora
                    if not calibrado and not calibracao_anunciada:
                        self.log(
                            f"🎙️ [OUVIDO] Calibrando o ruído ambiente por {calibracao_s:.1f} segundo..."
                        )
                        calibracao_anunciada = True
                    falando = bool(self.esta_falando())
                    if falando:
                        self._nivel_microfone = 0.0
                        self._ultima_fala_laylay_ts = agora
                        gravando.clear()
                        preroll.clear()
                        blocos_voz = 0
                        silencio = 0.0
                        ultimo_fim_fala = agora
                        continue
                    if agora - ultimo_fim_fala < 0.45:
                        continue
                    if overflow:
                        self.log("⚠️ [OUVIDO] O buffer do microfone perdeu um trecho de áudio.")

                    rms = float(np.sqrt(np.mean(np.square(chunk), dtype=np.float64))) if len(chunk) else 0.0
                    if not calibrado:
                        amostras_calibracao.append(rms)
                        if len(amostras_calibracao) < blocos_calibracao:
                            continue
                        # O percentil baixo evita que uma batida ou palavra isolada
                        # durante a partida seja aprendida como ruído permanente.
                        ruido = max(0.0001, float(np.percentile(amostras_calibracao, 30)))
                        calibrado = True
                        ultimo_log_nivel = agora
                        limiar_calibrado = max(limiar_minimo, ruido * 1.7)
                        self.log(
                            "🎙️ [OUVIDO:NÍVEL] "
                            f"calibrado ruído={ruido:.4f} início_de_fala={limiar_calibrado:.4f}"
                        )
                        continue

                    limiar = max(limiar_minimo, ruido * 1.7)
                    self._nivel_microfone = max(
                        0.0, min(1.0, rms / max(limiar * 1.8, 0.001)),
                    )
                    if not gravando:
                        pico_sem_fala = max(pico_sem_fala, rms)
                        # Só adapte o piso com blocos que já parecem silêncio. Antes,
                        # uma voz baixa elevava o limiar continuamente e sumia do VAD.
                        if rms < limiar * 0.82:
                            ruido = ruido * 0.98 + rms * 0.02
                        preroll.append(chunk)
                        blocos_voz = blocos_voz + 1 if rms >= limiar else 0
                        if blocos_voz >= 2:
                            gravando = list(preroll)
                            silencio = 0.0
                            pico_sem_fala = 0.0
                            if not entrada_anunciada and not bool(self.modo_chat_ativo()):
                                if not carregar_no_inicio:
                                    self.log(
                                        "🎙️ [OUVIDO] Whisper será carregado somente na primeira fala."
                                    )
                                self.log(
                                    f"🎙️ [OUVIDO] Entrada: {nome} "
                                    f"(índice {indice}, {self.taxa_captura} Hz, {origem})."
                                )
                                entrada_anunciada = True
                            self.log(
                                f"🎙️ [OUVIDO] Voz detectada (nível={rms:.4f}, limiar={limiar:.4f})."
                            )
                        elif agora - ultimo_log_nivel >= 15.0:
                            self.log(
                                "🎙️ [OUVIDO:NÍVEL] aguardando voz | "
                                f"pico={pico_sem_fala:.4f} limiar={limiar:.4f}"
                            )
                            pico_sem_fala = 0.0
                            ultimo_log_nivel = agora
                        continue

                    gravando.append(chunk)
                    duracao = len(gravando) * bloco_s
                    limiar_silencio = max(limiar_minimo, ruido * 1.25)
                    silencio = silencio + bloco_s if rms < limiar_silencio else 0.0
                    terminou = silencio >= silencio_final_s and duracao >= 0.6
                    if terminou or duracao >= duracao_maxima_s:
                        audio = np.concatenate(gravando)
                        gravando.clear()
                        preroll.clear()
                        blocos_voz = 0
                        silencio = 0.0
                        self._agendar_entrega(audio)
        except Exception as erro:
            self._nivel_microfone = 0.0
            if bool(self.modo_chat_ativo()):
                return
            self.log(f"⚠️ [OUVIDO] Captura do microfone encerrada: {erro}")
            raise RuntimeError("captura do microfone foi interrompida") from erro


def criar_ouvido_whisper_runtime(**kwargs: Any) -> OuvidoWhisperRuntime:
    return OuvidoWhisperRuntime(**kwargs)
