"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_music_preset() -> str:
    """Preset de playlist coerente com o restante do design system."""
    p = PALETA
    return f"""
    #musicPreset {{
        background: {p["superficie"]};
        border: 1px solid {p["borda"]};
        border-radius: 8px;
    }}
    #musicPreset[activePlaylist="true"] {{
        border-color: #71404C;
        background: #18171D;
    }}
    #musicPresetBody {{
        background: transparent;
        border: 0;
        text-align: left;
        padding: 0;
    }}
    #musicPresetBody:hover {{
        background: {p["hover"]};
        border-radius: 6px;
    }}
    #musicPresetPlay {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 7px;
        padding: 0;
    }}
    #musicPresetPlay:hover {{
        background: {p["hover"]};
        border-color: #71404C;
    }}
    #musicPresetPlay:focus {{
        background: {p["hover"]};
        border: 1px solid {p["rosa"]};
    }}
    #musicPresetPlay:disabled {{
        color: {p["apagado"]};
        border-color: transparent;
    }}
    """

__all__ = ['qss_music_preset']
