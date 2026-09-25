"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_settings_refresh() -> str:
    """Configurações com a mesma linguagem visual da Home."""
    p = PALETA
    return f"""
    #settingsPage, #settingsContent, #settingsScroll,
    #settingsScroll > QWidget > QWidget {{
        background: {p["fundo"]};
        border: 0;
    }}
    #settingsPage #eyebrow {{
        color: {p["rosa"]};
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    #settingsPage #pageTitle {{
        color: {p["texto"]};
        font-size: 24px;
        font-weight: 650;
    }}
    #settingsPage #pageDescription {{
        color: {p["secundario"]};
        font-size: 12px;
    }}
    #settingsPage #sectionTitle {{
        color: {p["texto"]};
        font-size: 14px;
        font-weight: 650;
        padding-top: 6px;
    }}
    #settingsPage #fieldLabel {{
        color: {p["secundario"]};
        font-size: 10px;
        font-weight: 650;
    }}
    #settingsPage QPushButton[provider="true"] {{
        background: {p["superficie"]};
        border: 1px solid {p["borda"]};
        border-radius: 10px;
        padding: 13px 15px;
        text-align: left;
        color: {p["secundario"]};
    }}
    #settingsPage QPushButton[provider="true"]:hover {{
        background: {p["hover"]};
        color: {p["texto"]};
        border-color: #48515B;
    }}
    #settingsPage QPushButton[provider="true"]:checked {{
        background: #271920;
        border-color: #70404B;
        color: {p["texto"]};
    }}
    #settingsPage QPushButton[provider="true"]:focus {{
        border-color: {p["rosa"]};
    }}

    #settingsPage #settingsField {{
        background: {p["superficie"]};
        border: 1px solid {p["borda"]};
        border-radius: 9px;
        padding: 10px 12px;
        selection-background-color: #6B3947;
    }}
    #settingsPage #settingsField:hover {{
        border-color: #3A434D;
    }}
    #settingsPage #settingsField:focus {{
        border-color: {p["rosa"]};
        background: {p["elevada"]};
    }}
    #settingsPage #settingsField:read-only {{
        color: {p["apagado"]};
        background: #12171D;
    }}
    #settingsPage #keyState {{
        color: {p["ciano"]};
        font-size: 10px;
    }}
    #settingsPage #settingsBanner {{
        background: {p["superficie"]};
        border: 1px solid {p["borda"]};
        border-left: 3px solid {p["ciano"]};
        border-radius: 8px;
        padding: 11px 13px;
        color: {p["secundario"]};
    }}
    #settingsPage #settingsBanner[kind="success"] {{
        border-left-color: {p["sucesso"]};
    }}
    #settingsPage #settingsBanner[kind="error"] {{
        border-left-color: {p["erro"]};
    }}
    #settingsPage #settingsNote {{
        color: {p["secundario"]};
        background: {p["superficie"]};
        border: 1px solid #1E252D;
        padding: 13px;
        border-radius: 9px;
    }}
    #settingsPage #primaryButton {{
        background: #D94B62;
        color: #FFFFFF;
        border: 1px solid #E25D72;
        border-radius: 9px;
        padding: 10px 16px;
        font-weight: 700;
    }}
    #settingsPage #primaryButton:hover {{
        background: {p["rosa"]};
    }}
    #settingsPage #primaryButton:focus {{
        border-color: #FF9AAA;
    }}
    #settingsPage #primaryButton:disabled {{
        color: #7C7378;
        background: #2A2024;
        border-color: #3A2A30;
    }}
    #settingsPage #secondaryButton, #settingsPage #profileAvatarButton {{
        background: {p["superficie"]};
        border: 1px solid {p["borda"]};
        border-radius: 9px;
        padding: 10px 15px;
        font-weight: 600;
        color: {p["secundario"]};
    }}
    #settingsPage #secondaryButton:hover, #settingsPage #profileAvatarButton:hover {{
        background: {p["hover"]};
        border-color: #48515B;
        color: {p["texto"]};
    }}

    #settingsPage #settingsProfileCard {{
        background: {p["superficie"]};
        border: 1px solid {p["borda"]};
        border-radius: 12px;
    }}
    #settingsPage #settingsProfileTitle {{
        color: {p["texto"]};
        font-size: 11px;
        font-weight: 650;
    }}
    #settingsPage #settingsProfileHint {{
        color: {p["apagado"]};
        font-size: 9px;
    }}
    #settingsPage QCheckBox {{
        color: {p["secundario"]};
        spacing: 8px;
        padding: 4px 0;
    }}
    #settingsPage QCheckBox:hover {{
        color: {p["texto"]};
    }}
    #settingsPage QCheckBox::indicator {{
        width: 15px;
        height: 15px;
        border: 1px solid {p["borda"]};
        border-radius: 4px;
        background: {p["superficie"]};
    }}
    #settingsPage QCheckBox::indicator:checked {{
        background: #D94B62;
        border-color: {p["rosa"]};
    }}
    """

__all__ = ['qss_settings_refresh']
