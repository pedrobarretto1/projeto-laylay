"""Política local de geometria e ativação da ilha do desktop.

Adaptação de Coucou Windows 0.5.0: petit/home, ancoragem e janela
não ativável. Copyright (c) 2026 Louis Raillé, MIT; ver licencas/Coucou-MIT.txt.
Não recebe contexto da mente e não executa comandos operacionais.
"""
from __future__ import annotations

import sys
from PySide6.QtCore import QRect, QPoint, Qt


TAMANHOS_PAGINAS_DESKTOP = {
    pagina: (1100, 730)
    for pagina in ('home', 'chat', 'music', 'system', 'settings', 'memory', 'lamp', 'dev', 'streaming')
}


def geometria_desktop(disponivel: QRect, expandida: bool = False, pagina: str | None = None, ancora: QPoint | None = None) -> QRect:
    """Projeta uma âncora lógica sem promover o clamp a posição escolhida.

    O padrão reserva 120 DIP acima da ilha, inclusive no painel ampliado.
    Uma posição explícita mantém sua identidade; só a superfície é limitada.
    """
    tamanho = TAMANHOS_PAGINAS_DESKTOP.get(pagina, (640, 320)) if expandida else (272, 54)
    largura = min(tamanho[0], max(1, disponivel.width()))
    folga = min(120, max(0, disponivel.height() - min(54, disponivel.height()))) if ancora is None else 0
    altura = min(tamanho[1], max(1, disponivel.height() - folga))
    centro = disponivel.center().x() if ancora is None else ancora.x()
    topo = disponivel.top() + folga if ancora is None else ancora.y()
    x = min(max(centro - (largura - 1) // 2, disponivel.left()), disponivel.right() - largura + 1)
    y = min(max(topo, disponivel.top()), disponivel.bottom() - altura + 1)
    return QRect(x, y, largura, altura)


def botao_esquerdo_pressionado() -> bool:
    """Leitura somente durante arrasto local; detecta soltura fora da janela."""
    if sys.platform == 'win32':
        import ctypes
        return bool(ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000)
    from PySide6.QtGui import QGuiApplication
    return bool(QGuiApplication.mouseButtons() & Qt.LeftButton)


def permitir_ativacao_desktop(hwnd: int, permitir: bool) -> None:
    """Equivalente Qt do WS_EX_NOACTIVATE/WS_EX_TOOLWINDOW do Coucou.

    A flag é alterada no HWND existente, sem recriar a WebView em cada gesto.
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
