"""Amostragem visual conservadora para presença contextual durante jogos."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Mapping

from .observador_inventario import assinatura_perceptual, distancia_assinaturas


class ObservadorPresencaJogoRuntime:
    def __init__(
        self, *, contexto_jogo: Callable[[], Mapping[str, Any]],
        capturar: Callable[[Mapping[str, Any]], str],
        executar_visao: Callable[[Mapping[str, Any]], bool],
        jogo_chave_atual: Callable[[Mapping[str, Any]], str],
        visao_ocupada: Callable[[], bool] = lambda: False,
        permitido: Callable[[], bool] = lambda: True,
        interacao_iniciada: Callable[[], bool] = lambda: True,
        habilitado: bool = True, intervalo_s: float = 45.0,
        max_analises_sessao: int = 8, limiar_mudanca: int = 18,
        janela_analises_s: float = 900.0,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Any] = time.sleep,
        log: Callable[[str], Any] = print,
        stop_event: threading.Event | None = None,
    ) -> None:
        self.contexto_jogo = contexto_jogo
        self.capturar = capturar
        self.executar_visao = executar_visao
        self.jogo_chave_atual = jogo_chave_atual
        self.visao_ocupada = visao_ocupada
        self.permitido = permitido
        self.interacao_iniciada = interacao_iniciada
        self.habilitado = bool(habilitado)
        self.intervalo_s = max(30.0, float(intervalo_s))
        self.max_analises_sessao = max(1, int(max_analises_sessao))
        self.limiar_mudanca = max(1, int(limiar_mudanca))
        self.janela_analises_s = max(300.0, float(janela_analises_s))
        self.clock = clock
        self.sleep = sleep
        self.log = log
        self.stop_event = stop_event or threading.Event()
        self._lock = threading.RLock()
        self._jogo = ""
        self._assinatura = ""
        self._analises = 0
        self._inicio_sessao = 0.0

    def verificar_uma_vez(self) -> bool:
        # O próprio modo jogo já exige processo elegível, tela cheia e
        # estabilidade antes de publicar ``ativo=True``. Exigir também uma
        # fala anterior de Pedro transformava conversa em permissão para
        # perceber e deixava toda sessão recém-iniciada artificialmente muda.
        if not self.habilitado or self.visao_ocupada() or not self.permitido():
            return False
        contexto = dict(self.contexto_jogo() or {})
        if not contexto.get("ativo"):
            with self._lock:
                self._jogo, self._assinatura, self._analises = "", "", 0
            return False
        jogo = str(self.jogo_chave_atual(contexto) or "")
        agora = float(self.clock())
        with self._lock:
            if jogo != self._jogo or agora - self._inicio_sessao > self.janela_analises_s:
                self._jogo, self._assinatura, self._analises = jogo, "", 0
                self._inicio_sessao = agora
            if self._analises >= self.max_analises_sessao:
                return False
        imagem = str(self.capturar(contexto) or "")
        assinatura = assinatura_perceptual(imagem)
        if not assinatura:
            return False
        with self._lock:
            distancia = distancia_assinaturas(self._assinatura, assinatura)
            if self._assinatura and distancia < self.limiar_mudanca:
                return False
            self._assinatura = assinatura
            self._analises += 1
            numero = self._analises
        self.log(
            f"👀 [PRESENÇA:JOGO] quadro relevante={distancia} "
            f"| amostra={numero}/{self.max_analises_sessao} "
            f"por {self.janela_analises_s / 60:.0f}min"
        )
        return bool(self.executar_visao({
            "pergunta": (
                "Você ficou curiosa sobre o que está acontecendo no jogo. Observe esta captura nova "
                "em silêncio e decida por conta própria se vale acompanhar o momento, perguntar algo "
                "curto sem cobrar resposta, dar uma dica realmente fundamentada, comemorar, motivar "
                "ou recomendar algo. Se não houver valor real, apenas continue observando."
            ),
            "tipo": "observacao_presenca_proativa",
            "_proativo": True,
            "_origem_presenca": "curiosidade_visual",
            "_imagem_pre_capturada": imagem,
        }))

    def executar(self) -> None:
        while not self.stop_event.wait(self.intervalo_s):
            try:
                self.verificar_uma_vez()
            except Exception as exc:
                self.log(f"⚠️ [PRESENÇA:JOGO] amostra ignorada: {type(exc).__name__}: {exc}")

    def encerrar(self) -> None:
        self.stop_event.set()


def criar_observador_presenca_jogo_runtime(**kwargs: Any) -> ObservadorPresencaJogoRuntime:
    return ObservadorPresencaJogoRuntime(**kwargs)
