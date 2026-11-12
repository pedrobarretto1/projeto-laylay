"""Política local de geometria e ativação da ilha do desktop.

Adaptação de Coucou Windows 0.5.0: petit/home e janela
não ativável. Copyright (c) 2026 Louis Raillé, MIT; ver licencas/Coucou-MIT.txt.
Não recebe contexto da mente e não executa comandos operacionais.
"""
from __future__ import annotations

import sys
from PySide6.QtCore import QRect


TAMANHOS_PAGINAS_DESKTOP = {
    pagina: (1100, 730)
    for pagina in ('home', 'chat', 'music', 'system', 'settings', 'memory', 'lamp', 'dev', 'streaming')
}
TAMANHO_ILHA_COMPACTA = (272, 36)
TAMANHO_ILHA_RECOLHIDA = (48, 4)


def geometria_desktop(
    disponivel: QRect,
    expandida: bool = False,
    pagina: str | None = None,
    recolhida: bool = False,
) -> QRect:
    """Projeta a ilha fixa no centro superior da área utilizável do display.

    Compacta e expandida compartilham a mesma ancoragem; recolhida limita a
    superfície à barra preta de interação.
    """
    if recolhida:
        tamanho = TAMANHO_ILHA_RECOLHIDA
    else:
        tamanho = TAMANHOS_PAGINAS_DESKTOP.get(pagina, (640, 320)) if expandida else TAMANHO_ILHA_COMPACTA
    largura = min(tamanho[0], max(1, disponivel.width()))
    altura = min(tamanho[1], max(1, disponivel.height()))
    centro = disponivel.center().x()
    topo = disponivel.top()
    x = min(max(centro - (largura - 1) // 2, disponivel.left()), disponivel.right() - largura + 1)
    y = min(max(topo, disponivel.top()), disponivel.bottom() - altura + 1)
    return QRect(x, y, largura, altura)


def permitir_ativacao_desktop(hwnd: int, permitir: bool) -> None:
    """Equivalente Qt do WS_EX_NOACTIVATE/WS_EX_TOOLWINDOW do Coucou.

    A flag é alterada no HWND existente, sem recriar a WebView em cada transição.
    """
    if sys.platform != 'win32':
        return
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    obter = user32.GetWindowLongPtrW
    obter.argtypes = [wintypes.HWND, ctypes.c_int]
    obter.restype = ctypes.c_ssize_t
    definir = user32.SetWindowLongPtrW
    definir.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
    definir.restype = ctypes.c_ssize_t
    estilo = obter(hwnd, -20)
    estilo = (estilo & ~0x08000000) if permitir else (estilo | 0x08000000)
    definir(hwnd, -20, estilo | 0x00000080)
