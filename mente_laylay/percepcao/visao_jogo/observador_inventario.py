"""Observação proativa e limitada do inventário durante uma sessão de jogo."""

from __future__ import annotations

import base64
import io
import threading
import time
from typing import Any, Callable, Mapping


def assinatura_perceptual(imagem_base64: str) -> str:
    if not imagem_base64:
        return ""
    try:
        from PIL import Image

        imagem = Image.open(io.BytesIO(base64.b64decode(imagem_base64))).convert("L")
        resample = getattr(Image, "Resampling", Image).BILINEAR
        reduzida = imagem.resize((16, 9), resample)
        obter_pixels = getattr(reduzida, "get_flattened_data", reduzida.getdata)
        pixels = list(obter_pixels())
        media = sum(pixels) / max(1, len(pixels))
        bits = "".join("1" if pixel >= media else "0" for pixel in pixels)
        return f"{int(bits, 2):036x}"
    except Exception:
        return ""


def distancia_assinaturas(a: str, b: str) -> int:
    try:
        return (int(a, 16) ^ int(b, 16)).bit_count()
    except (TypeError, ValueError):
        return 999


class ObservadorInventarioJogoRuntime:
    def __init__(
        self,
        *,
        contexto_jogo: Callable[[], Mapping[str, Any]],
        capturar: Callable[[Mapping[str, Any]], str],
        executar_visao: Callable[[Mapping[str, Any]], bool],
        jogo_chave_atual: Callable[[Mapping[str, Any]], str] | None = None,
        visao_ocupada: Callable[[], bool] = lambda: False,
        habilitado: bool = True,
        intervalo_s: float = 25.0,
        duracao_s: float = 600.0,
        max_analises: int = 12,
        limiar_mudanca: int = 10,
        sleep: Callable[[float], Any] = time.sleep,
        clock: Callable[[], float] = time.time,
        log: Callable[[str], Any] = print,
        stop_event: threading.Event | None = None,
    ) -> None:
        self.contexto_jogo = contexto_jogo
        self.capturar = capturar
        self.executar_visao = executar_visao
        self.jogo_chave_atual = jogo_chave_atual
        self.visao_ocupada = visao_ocupada
        self.habilitado = bool(habilitado)
        self.intervalo_s = max(8.0, float(intervalo_s))
        self.duracao_s = max(60.0, float(duracao_s))
        self.max_analises = max(1, int(max_analises))
        self.limiar_mudanca = max(1, int(limiar_mudanca))
        self.sleep = sleep
        self.clock = clock
        self.log = log
        self.stop_event = stop_event or threading.Event()
        self._lock = threading.RLock()
        self._ativo_ate = 0.0
        self._assinatura = ""
        self._analises = 0
        self._jogo_chave = ""

    def armar(self, *, jogo_chave: str, imagem: str = "") -> None:
        if not self.habilitado or not jogo_chave:
            return
        with self._lock:
            self._jogo_chave = str(jogo_chave)
            self._ativo_ate = self.clock() + self.duracao_s
            self._analises = 0
            self._assinatura = assinatura_perceptual(imagem) or self._assinatura
        self.log(
            f"👁️ [JOGO:PROATIVO] inventário observado por {self.duracao_s / 60:.0f} min "
            f"| intervalo={self.intervalo_s:.0f}s | máximo={self.max_analises} análises"
        )

    def desarmar(self, motivo: str = "") -> None:
        with self._lock:
            estava_ativo = self._ativo_ate > self.clock()
            self._ativo_ate = 0.0
            self._assinatura = ""
            self._analises = 0
        if estava_ativo:
            self.log(f"👁️ [JOGO:PROATIVO] observação encerrada ({motivo or 'fim'}).")

    @property
    def ativo(self) -> bool:
        with self._lock:
            return bool(
                self.habilitado and self.clock() < self._ativo_ate
                and self._analises < self.max_analises
            )

    def verificar_uma_vez(self) -> bool:
        if not self.ativo or self.visao_ocupada():
            return False
        contexto = dict(self.contexto_jogo() or {})
        if not contexto.get("ativo"):
            self.desarmar("jogo encerrado")
            return False
        if callable(self.jogo_chave_atual):
            chave_atual = str(self.jogo_chave_atual(contexto) or "")
            with self._lock:
                chave_armada = self._jogo_chave
            if chave_atual and chave_armada and chave_atual != chave_armada:
                self.desarmar("outro jogo entrou em foco")
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
            f"👁️ [JOGO:PROATIVO] mudança relevante={distancia} | análise={numero}/{self.max_analises}"
        )
        return bool(self.executar_visao({
            "pergunta": (
                "Observe silenciosamente se o inventário mudou e só recomende algo "
                "quando houver uma oportunidade concreta para o personagem."
            ),
            "tipo": "observacao_inventario_proativa",
            "_proativo": True,
            "_imagem_pre_capturada": imagem,
        }))

    def executar(self) -> None:
        while not self.stop_event.wait(self.intervalo_s):
            self.verificar_uma_vez()

    def encerrar(self) -> None:
        self.stop_event.set()


def criar_observador_inventario_jogo_runtime(**kwargs: Any) -> ObservadorInventarioJogoRuntime:
    return ObservadorInventarioJogoRuntime(**kwargs)
