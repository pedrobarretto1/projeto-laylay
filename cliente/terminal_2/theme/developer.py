"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA, FONTE_INTERFACE_QSS, FONTE_MONO_QSS

def qss_dev_console() -> str:
    """Estilo técnico do DEV Console usando os mesmos tokens do Terminal."""
    p = PALETA
    return f"""
    QWidget#developerPage {{
        background: {p["fundo"]};
        color: {p["texto"]};
        font-family: {FONTE_INTERFACE_QSS};
    }}
    QFrame#devToolbar, QFrame#devTelemetryBar {{
        background: {p["sidebar"]};
        border: 1px solid {p["borda"]};
        border-radius: 12px;
    }}
    QLabel#devPromptMark {{
        color: {p["rosa"]};
        font: 700 16px {FONTE_MONO_QSS};
    }}
    QLabel#devTitle {{
        color: {p["texto"]};
        font: 700 12px {FONTE_INTERFACE_QSS};
    }}
    QLabel#devObservedState {{
        color: {p["apagado"]};
        font: 600 9px {FONTE_INTERFACE_QSS};
    }}
    QLabel#devObservedState[connected="true"] {{
        color: {p["sucesso"]};
    }}
    QLabel#devControlLabel {{
        color: {p["apagado"]};
        font: 600 8px {FONTE_INTERFACE_QSS};
    }}
    QFrame#devVerticalSeparator {{
        color: {p["borda"]};
        max-width: 1px;
    }}
    QPushButton#devFilterButton, QPushButton#devLevelButton,
    QPushButton#devStateButton {{
        min-height: 25px;
        padding: 0 10px;
        border: 1px solid {p["borda"]};
        border-radius: 7px;
        background: {p["superficie"]};
        color: {p["apagado"]};
        font: 600 8px {FONTE_INTERFACE_QSS};
    }}
    QPushButton#devFilterButton:hover, QPushButton#devLevelButton:hover,
    QPushButton#devStateButton:hover {{
        border-color: #59636B;
        color: {p["texto"]};
        background: {p["hover"]};
    }}
    QPushButton#devFilterButton:focus, QPushButton#devLevelButton:focus,
    QPushButton#devStateButton:focus {{
        border-color: {p["rosa"]};
    }}
    QPushButton#devFilterButton:checked, QPushButton#devLevelButton:checked {{
        border-color: #B63C50;
        color: {p["rosa"]};
        background: #28151B;
    }}
    QPushButton#devStateButton:checked {{
        border-color: #394752;
        color: {p["rosa"]};
        background: #172029;
    }}
    QPushButton#devLevelButton:disabled {{
        color: #48515A;
        border-color: #202A32;
        background: #101419;
    }}

    QFrame#devConsoleFrame {{
        background: #020405;
        border: 1px solid #354049;
        border-radius: 11px;
    }}
    QTextEdit#devConsole {{
        background: #020304;
        color: #D7DBE0;
        border: 0;
        border-radius: 10px 10px 0 0;
        padding: 12px 15px;
        selection-background-color: #713443;
        font: 10pt {FONTE_MONO_QSS};
    }}
    QFrame#devCommandBar {{
        background: #070B0E;
        border: 0;
        border-top: 1px solid #1D272E;
        border-radius: 0 0 10px 10px;
    }}
    QLabel#devCommandPrompt {{
        color: {p["secundario"]};
        font: 10pt {FONTE_MONO_QSS};
    }}
    QLineEdit#devCommandInput {{
        color: {p["texto"]};
        background: transparent;
        border: 0;
        padding: 3px;
        font: 10pt {FONTE_MONO_QSS};
    }}
    QLineEdit#devCommandInput:focus {{
        color: #FFFFFF;
    }}
    QFrame#devTelemetryCell {{
        background: transparent;
        border: 0;
        border-right: 1px solid {p["borda"]};
        border-radius: 0;
    }}
    QLabel#devTelemetryTitle {{
        color: {p["secundario"]};
        font: 600 8px {FONTE_INTERFACE_QSS};
    }}
    QLabel#devTelemetryValue {{
        color: {p["texto"]};
        font: 600 9px {FONTE_MONO_QSS};
    }}
    QLabel#devTelemetryValue[available="false"] {{
        color: {p["apagado"]};
    }}
    QScrollArea#devRail {{
        background: transparent;
        border: 0;
    }}
    QWidget#devRailContent {{
        background: transparent;
    }}
    QFrame#devMaintenanceCard {{
        background: {p["superficie"]};
        border: 1px solid #513039;
        border-radius: 12px;
    }}
    QLabel#devMaintenanceIcon {{
        color: {p["rosa"]};
        font: 700 18px 'Segoe UI Symbol';
    }}
    QLabel#devMaintenanceTitle {{
        color: {p["texto"]};
        font: 600 10px {FONTE_INTERFACE_QSS};
    }}
    QLabel#devMaintenanceDescription {{
        color: {p["apagado"]};
        font: 8px {FONTE_INTERFACE_QSS};
    }}

    QPushButton#devMaintenanceStatus:disabled {{
        min-height: 22px;
        color: #C76775;
        background: #26171C;
        border: 1px solid #61313C;
        border-radius: 6px;
        font: 600 8px {FONTE_INTERFACE_QSS};
    }}
    QScrollBar:vertical {{
        background: #090D10;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: #34404A;
        min-height: 28px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #47545E;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    """

__all__ = ['qss_dev_console']
