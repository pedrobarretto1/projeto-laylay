"""Material de fundo nativo opcional para a ilha, sem alterar o sistema.

Windows 11 22621+: DWMWA_SYSTEMBACKDROP_TYPE = 38.
A aceitação do DWM não garante que o Acrylic fique visível pelo Qt WebEngine:
a pintura HTML, regiões mascaradas e composição podem cobrir o material.
"""
from __future__ import annotations

import os
import sys


def _dwm_set(hwnd: int, attribute: int, value: int) -> bool:
    """Tenta alterar apenas atributos da janela autorizada."""
    if sys.platform != 'win32' or not hwnd:
        return False
    try:
        import ctypes
        dwm = ctypes.WinDLL('dwmapi', use_last_error=True)
        fn = dwm.DwmSetWindowAttribute
        fn.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
        fn.restype = ctypes.c_long
        valor = ctypes.c_int(value)
        return int(fn(ctypes.c_void_p(hwnd), attribute, ctypes.byref(valor), ctypes.sizeof(valor))) == 0
    except (OSError, AttributeError, ValueError):
        return False


def aplicar_material_windows(hwnd: int, preferencia: str | None = None) -> str:
    """Retorna 'acrylic', 'mica' ou 'fallback'. Nunca instala efeitos globais.

    O Qt usa máscara arredondada, mas o Acrylic nativo desenha um retângulo
    cinza atrás da cápsula. Por isso, o padrão seguro é 'off'.
    LAYLAY_WINDOWS_BACKDROP=acrylic permite testar novamente, se desejado.
    """
    modo = (preferencia if preferencia is not None else
            os.environ.get('LAYLAY_WINDOWS_BACKDROP', 'off')).strip().lower()
    if modo in {'off', 'false', '0', 'none'}:
        return 'fallback'
    if modo not in {'acrylic', 'mica'} or sys.platform != 'win32' or not hwnd:
        return 'fallback'
    try:
        if sys.getwindowsversion().build < 22621:
            return 'fallback'
    except AttributeError:
        return 'fallback'

    # Material transiente = Acrylic (3); material principal = Mica (2).
    # Sucesso significa que o DWM aceitou o atributo, não prova blur visível.
    if not _dwm_set(hwnd, 38, 3 if modo == 'acrylic' else 2):
        return 'fallback'
    _dwm_set(hwnd, 20, 1)  # Preferência visual escura, somente neste HWND.
    _dwm_set(hwnd, 33, 2)  # Cantos arredondados, respeitando a máscara Qt.
    return modo


def restaurar_material_windows(hwnd: int) -> None:
    """Restaura o padrão DWM ao sair do modo desktop."""
    if sys.platform != 'win32' or not hwnd:
        return
    _dwm_set(hwnd, 38, 0)  # DWMSBT_AUTO
    _dwm_set(hwnd, 33, 0)  # DWMWCP_DEFAULT
