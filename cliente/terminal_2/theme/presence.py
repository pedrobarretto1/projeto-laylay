"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_live_presence() -> str:
    """Estados vivos da Laylay sem competir com o conteúdo principal."""
    p = PALETA
    return f"""
    #presencePill {{
        background: {p["superficie"]};
        border: 1px solid #202832;
        border-radius: 12px;
    }}
    #statusLabel {{
        color: {p["secundario"]};
        font-size: 10px;
        font-weight: 650;
    }}
    #connectionDot {{
        color: {p["apagado"]};
        font-size: 8px;
    }}

    #presencePill[activity="idle"] {{
        background: {p["superficie"]};
        border-color: #202832;
    }}
    #connectionDot[activity="idle"] {{
        color: {p["sucesso"]};
    }}

    #presencePill[activity="listening"] {{
        background: #132026;
        border-color: #28515A;
    }}
    #connectionDot[activity="listening"],
    #statusLabel[activity="listening"] {{
        color: {p["ciano"]};
    }}

    #presencePill[activity="thinking"] {{
        background: #1C1828;
        border-color: #4D3E71;
    }}
    #connectionDot[activity="thinking"],
    #statusLabel[activity="thinking"] {{
        color: {p["violeta"]};
    }}

    #presencePill[activity="executing"] {{
        background: #241E15;
        border-color: #5F4B2C;
    }}
    #connectionDot[activity="executing"],
    #statusLabel[activity="executing"] {{
        color: {p["aviso"]};
    }}

    #presencePill[activity="speaking"] {{
        background: #25181E;
        border-color: #623442;
    }}
    #connectionDot[activity="speaking"],
    #statusLabel[activity="speaking"] {{
        color: {p["rosa"]};
    }}

    #presencePill[activity="reconnecting"],
    #presencePill[activity="error"] {{
        background: #24171B;
        border-color: #64333D;
    }}
    #connectionDot[activity="reconnecting"],
    #statusLabel[activity="reconnecting"],
    #connectionDot[activity="error"],
    #statusLabel[activity="error"] {{
        color: {p["erro"]};
    }}

    #presencePill[activity="success"] {{
        background: #142019;
        border-color: #315846;
    }}
    #connectionDot[activity="success"],
    #statusLabel[activity="success"] {{
        color: {p["sucesso"]};
    }}

    #presencePill[activity="warning"] {{
        background: #241E15;
        border-color: #5F4B2C;
    }}
    #connectionDot[activity="warning"],
    #statusLabel[activity="warning"] {{
        color: {p["aviso"]};
    }}

    #profileStatus[state="idle"] {{
        color: {p["sucesso"]};
    }}
    #profileStatus[state="listening"] {{
        color: {p["ciano"]};
    }}
    #profileStatus[state="thinking"] {{
        color: {p["violeta"]};
    }}
    #profileStatus[state="executing"],
    #profileStatus[state="warning"] {{
        color: {p["aviso"]};
    }}
    #profileStatus[state="speaking"] {{
        color: {p["rosa"]};
    }}
    #profileStatus[state="success"] {{
        color: {p["sucesso"]};
    }}
    #profileStatus[state="reconnecting"],
    #profileStatus[state="error"] {{
        color: {p["erro"]};
    }}

    #thinkingIndicator {{
        background: {p["elevada"]};
        border: 1px solid {p["borda"]};
        border-radius: 14px;
    }}
    #thinkingIndicator[activity="thinking"] {{
        background: #1B1826;
        border-color: #4D3E71;
    }}
    #thinkingIndicator[activity="executing"] {{
        background: #241E15;
        border-color: #5F4B2C;
    }}
    #thinkingMeta {{
        color: {p["apagado"]};
        font-size: 8px;
        font-weight: 700;
    }}
    #thinkingState {{
        color: {p["violeta"]};
        font-size: 9px;
        font-weight: 650;
    }}
    #thinkingState[activity="executing"] {{
        color: {p["aviso"]};
    }}
    #thinkingDots {{
        color: {p["violeta"]};
        font-size: 8px;
    }}
    #thinkingIndicator[activity="executing"] #thinkingDots {{
        color: {p["aviso"]};
    }}
    """

__all__ = ['qss_live_presence']
