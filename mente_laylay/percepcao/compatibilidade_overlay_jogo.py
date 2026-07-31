"""Compatibilidade segura de overlays com jogos em tela cheia exclusiva.

Não injeta DLL, não lê memória do jogo e não cria hooks gráficos. A adaptação
usa apenas a própria janela Win32 do jogo: pede a transição para modo janela e
a cobre sobre o monitor sem bordas. Assim avatar e barra continuam sendo
janelas normais do Windows e também funcionam em jogos com anti-cheat.
"""

from __future__ import annotations

import os
import inspect
import threading
import time
from typing import Any, Callable, Mapping


_MASCARA_BORDAS = (
    0x00C00000  # WS_CAPTION
    | 0x00040000  # WS_THICKFRAME
    | 0x00020000  # WS_MINIMIZEBOX
    | 0x00010000  # WS_MAXIMIZEBOX
    | 0x00080000  # WS_SYSMENU
)


def calcular_estilo_sem_bordas(estilo: int) -> int:
    """Remove somente moldura e botões; preserva visibilidade e flags do jogo."""
    return int(estilo) & ~_MASCARA_BORDAS


def estrategia_alternancia_tela(retrato: Mapping[str, Any] | None) -> str:
    """Escolhe a tecla pública do jogo sem depender de injeção gráfica."""
    dados = dict(retrato or {})
    identidade = " ".join(
        str(dados.get(chave) or "")
        for chave in ("exe", "title", "process_path")
    ).casefold()
    # O Hytale usa F11 para Toggle Fullscreen. Alt+Enter não altera o modo do
    # renderizador e fazia o Windows aceitar a geometria sem liberar overlays.
    if "hytale" in identidade:
        return "f11"
    return "alt_enter"


def pressionar_f11_global_seguro(hwnd: int, user32: Any) -> bool:
    """Envia F11 ao jogo focado e garante o key-up mesmo se algo falhar."""
    if int(hwnd or 0) <= 0 or int(user32.GetForegroundWindow() or 0) != int(hwnd):
        return False
    pressionou = False
    try:
        user32.keybd_event(0x7A, 0x57, 0, 0)  # VK_F11 down
        pressionou = True
        return True
    finally:
        # KEYEVENTF_KEYUP; F11 não usa Ctrl/Shift/Alt e não deixa modificador
        # preso caso o jogo recrie a janela durante a alternância.
        try:
            user32.keybd_event(0x7A, 0x57, 0x0002, 0)
        except Exception:
            if pressionou:
                raise


def converter_janela_para_borderless(
    hwnd: int,
    *,
    retrato: Mapping[str, Any] | None = None,
    user32: Any = None,
    sleep: Callable[[float], Any] = time.sleep,
) -> bool:
    """Converte a janela focada para borderless sem simular teclas globais."""
    if os.name != "nt" or int(hwnd or 0) <= 0:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        user32 = user32 or ctypes.windll.user32
        hwnd = int(hwnd)
        if not bool(user32.IsWindow(hwnd)):
            return False
        # Nunca altere uma janela que deixou de ser a janela em primeiro plano.
        if int(user32.GetForegroundWindow() or 0) != hwnd:
            return False

        class MonitorInfo(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
        info = MonitorInfo(cbSize=ctypes.sizeof(MonitorInfo))
        if not monitor or not bool(user32.GetMonitorInfoW(monitor, ctypes.byref(info))):
            return False

        rect_antes = wintypes.RECT()
        if not bool(user32.GetWindowRect(hwnd, ctypes.byref(rect_antes))):
            return False
        estilo_antes = int(user32.GetWindowLongW(hwnd, -16))
        geometria_antes = (
            int(rect_antes.left), int(rect_antes.top),
            int(rect_antes.right), int(rect_antes.bottom),
        )

        estrategia = estrategia_alternancia_tela(retrato)
        if estrategia == "f11":
            # O Hytale usa entrada bruta e ignora WM_KEYDOWN via PostMessage.
            # keybd_event alcança essa rota, mas só é usado com o jogo focado.
            if not pressionar_f11_global_seguro(hwnd, user32):
                return False
            sleep(0.9)
        else:
            # WM_SYSKEY* com o contexto ALT evita SendInput e, portanto, não
            # deixa Alt/Shift/Ctrl presos se a Laylay for interrompida.
            lparam_down = 1 | (0x1C << 16) | (1 << 29)
            lparam_up = lparam_down | (1 << 30) | (1 << 31)
            user32.PostMessageW(hwnd, 0x0104, 0x0D, lparam_down)
            user32.PostMessageW(hwnd, 0x0105, 0x0D, lparam_up)
            sleep(0.45)

        # SetWindowPos também retorna sucesso quando o renderizador ignora a
        # tecla e continua exclusivo. Exigimos uma mudança real de estilo ou
        # geometria para não marcar um falso positivo e bloquear novas tentativas.
        estilo = int(user32.GetWindowLongW(hwnd, -16))  # GWL_STYLE
        rect_depois = wintypes.RECT()
        if not bool(user32.GetWindowRect(hwnd, ctypes.byref(rect_depois))):
            return False
        geometria_depois = (
            int(rect_depois.left), int(rect_depois.top),
            int(rect_depois.right), int(rect_depois.bottom),
        )
        if estilo == estilo_antes and geometria_depois == geometria_antes:
            return False

        # O jogo pode recriar o estilo ao sair do exclusivo; por isso ele é
        # relido somente depois da tecla correta.
        estilo_sem_bordas = calcular_estilo_sem_bordas(estilo)
        if estilo_sem_bordas != estilo:
            user32.SetWindowLongW(hwnd, -16, estilo_sem_bordas)

        rect = info.rcMonitor
        largura = int(rect.right - rect.left)
        altura = int(rect.bottom - rect.top)
        if largura <= 0 or altura <= 0:
            return False
        flags = 0x0020 | 0x0010 | 0x0040  # FRAMECHANGED | NOACTIVATE | SHOWWINDOW
        return bool(
            user32.SetWindowPos(
                hwnd, 0, int(rect.left), int(rect.top), largura, altura, flags,
            )
        )
    except Exception:
        return False


class CompatibilidadeOverlayJogoRuntime:
    """Aplica a adaptação uma única vez por janela, fora do monitor principal."""

    def __init__(
        self,
        *,
        habilitado: bool = True,
        converter: Callable[[int], bool] = converter_janela_para_borderless,
        thread_factory: Callable[..., Any] = threading.Thread,
        clock: Callable[[], float] = time.monotonic,
        intervalo_nova_tentativa_s: float = 3.0,
        max_tentativas_por_janela: int = 3,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.habilitado = bool(habilitado)
        self.converter = converter
        self.thread_factory = thread_factory
        self.clock = clock
        self.intervalo_nova_tentativa_s = max(0.2, float(intervalo_nova_tentativa_s))
        self.max_tentativas_por_janela = max(1, int(max_tentativas_por_janela))
        self.log = log
        self._lock = threading.Lock()
        self._adaptados: set[int] = set()
        self._em_andamento: set[int] = set()
        self._ultima_tentativa: dict[int, float] = {}
        self._proxima_tentativa: dict[int, float] = {}
        self._falhas: dict[int, int] = {}

    def _converter_aceita_retrato(self) -> bool:
        try:
            assinatura = inspect.signature(self.converter)
            return "retrato" in assinatura.parameters or any(
                parametro.kind == inspect.Parameter.VAR_KEYWORD
                for parametro in assinatura.parameters.values()
            )
        except (TypeError, ValueError):
            return False

    def preparar(self, retrato: Mapping[str, Any] | None) -> bool:
        if not self.habilitado:
            return False
        try:
            hwnd = int(dict(retrato or {}).get("hwnd") or 0)
        except (TypeError, ValueError):
            return False
        if hwnd <= 0:
            return False
        agora = float(self.clock())
        with self._lock:
            if hwnd in self._adaptados or hwnd in self._em_andamento:
                return True
            if int(self._falhas.get(hwnd, 0)) >= self.max_tentativas_por_janela:
                return False
            if agora < float(self._proxima_tentativa.get(hwnd, float("-inf"))):
                return True
            self._ultima_tentativa[hwnd] = agora
            self._em_andamento.add(hwnd)

        def trabalhar() -> None:
            try:
                if self._converter_aceita_retrato():
                    sucesso = bool(self.converter(hwnd, retrato=dict(retrato or {})))
                else:
                    sucesso = bool(self.converter(hwnd))
                if sucesso:
                    with self._lock:
                        self._adaptados.add(hwnd)
                        self._falhas.pop(hwnd, None)
                        self._proxima_tentativa.pop(hwnd, None)
                    self.log(
                        "🪟 [OVERLAY JOGO] tela cheia sem bordas ativada"
                        f" via {estrategia_alternancia_tela(retrato)}; "
                        "avatar e barra podem aparecer sem roubar o foco."
                    )
                else:
                    with self._lock:
                        falhas = int(self._falhas.get(hwnd, 0)) + 1
                        self._falhas[hwnd] = falhas
                        espera = self.intervalo_nova_tentativa_s * (2 ** (falhas - 1))
                        self._proxima_tentativa[hwnd] = float(self.clock()) + espera
                    if falhas < self.max_tentativas_por_janela:
                        self.log(
                            "⚠️ [OVERLAY JOGO] o jogo não aceitou a conversão segura; "
                            f"nova tentativa em {espera:.0f}s ({falhas}/{self.max_tentativas_por_janela})."
                        )
                    else:
                        self.log(
                            "⚠️ [OVERLAY JOGO] conversão automática interrompida após "
                            f"{falhas} tentativas; não vou continuar enviando teclas ao jogo."
                        )
            finally:
                with self._lock:
                    self._em_andamento.discard(hwnd)

        try:
            self.thread_factory(
                target=trabalhar,
                name="Laylay-Overlay-Jogo",
                daemon=True,
            ).start()
            return True
        except Exception:
            with self._lock:
                self._em_andamento.discard(hwnd)
            return False


def criar_compatibilidade_overlay_jogo_runtime(**kwargs: Any) -> CompatibilidadeOverlayJogoRuntime:
    return CompatibilidadeOverlayJogoRuntime(**kwargs)
