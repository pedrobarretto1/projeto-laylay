"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA, FONTE_INTERFACE_QSS

def qss_home_refresh() -> str:
    """Tema canônico da Home e da conversa."""
    p = PALETA
    return f"""
    /* HOME E CONVERSA */
    * {{
        font-family: {FONTE_INTERFACE_QSS};
    }}
    #root, #mainSurface, QScrollArea,
    QScrollArea > QWidget > QWidget {{
        background: {p["fundo"]};
    }}
    #chatSurface {{
        background: transparent;
        border: 0;
        border-radius: 0;
    }}
    #chatHeader {{
        background: transparent;
        border: 0;
    }}
    #chatHeader[conversationMode="true"] {{
        border-bottom: 1px solid #1E252D;
    }}
    #chatGreeting {{
        color: {p["texto"]};
        font-size: 22px;
        font-weight: 650;
    }}

    #chatGreetingSub {{
        color: {p["secundario"]};
        font-size: 12px;
    }}
    #messageLaylay {{
        background: {p["elevada"]};
        border: 1px solid {p["borda"]};
        border-radius: 16px;
    }}
    #messageUser {{
        background: #261A20;
        border: 1px solid #422833;
        border-radius: 16px;
    }}
    #composer {{
        background: {p["superficie"]};
        border: 1px solid #4A2A34;
        border-radius: 20px;
    }}
    #composerEdit {{
        background: {p["elevada"]};
        border: 1px solid #202832;
        border-radius: 14px;
        color: {p["texto"]};
    }}

    #inspectorShell {{
        background: {p["sidebar"]};
        border-left: 1px solid #1E252D;
        border-radius: 0;
    }}
    #inspectorHeader {{
        background: transparent;
        border: 0;
    }}
    #inspectorTitle {{
        color: {p["texto"]};
        font-size: 12px;
        font-weight: 700;
    }}
    #inspectorSubtitle {{
        color: {p["apagado"]};
        font-size: 9px;
    }}
    #inspectorScroll {{
        background: transparent;
        border: 0;
    }}
    #inspectorContent {{
        background: transparent;
        border: 0;
    }}

    #intelligencePanel, #dashboardRail {{
        background: transparent;
        border: 0;
    }}
    #dashboardCard {{
        background: {p["superficie"]};
        border: 1px solid #1E252D;
        border-radius: 13px;
    }}
    #topbar {{
        background: {p["fundo"]};
        border-bottom: 1px solid #1E252D;
    }}
    #sidebar {{
        background: {p["sidebar"]};
        border-right: 1px solid #1E252D;
    }}
    #statusChip, #modeSwitch {{
        background: {p["superficie"]};
        border-color: {p["borda"]};
    }}
    """

__all__ = ['qss_home_refresh']
