"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_memory_refresh() -> str:
    """Composição dedicada da memória: leitura longa, busca e contexto lateral."""
    p = PALETA
    return f"""
    #memoryPage, #memoryPageContent, #memoryScroll,
    #memoryScroll > QWidget > QWidget, #memoryMain, #memoryBody {{
        background: {p["fundo"]};
        border: 0;
    }}
    #memoryPage #eyebrow {{
        color: {p["rosa"]};
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    #memoryPage #pageTitle {{
        color: {p["texto"]};
        font-size: 24px;
        font-weight: 650;
    }}
    #memoryPage #pageDescription {{
        color: {p["secundario"]};
        font-size: 12px;
    }}
    #memoryStatusDot {{
        color: {p["apagado"]};
        font-size: 9px;
    }}
    #memoryStatusDot[state="online"] {{
        color: {p["sucesso"]};
    }}
    #memoryStatusDot[state="unavailable"] {{
        color: {p["aviso"]};
    }}
    #memoryStatusValue {{
        color: {p["secundario"]};
        font-size: 10px;
        font-weight: 600;
    }}
    #memoryCount {{
        color: {p["apagado"]};
        font-size: 9px;
    }}
    #memoryToolbar {{
        background: {p["superficie"]};
        border: 1px solid #1E252D;
        border-radius: 12px;
    }}
    #memorySearch {{
        background: {p["elevada"]};
        border: 1px solid {p["borda"]};
        border-radius: 9px;
        min-height: 30px;
        padding: 4px 10px;
        color: {p["texto"]};
        selection-background-color: #6B3947;
    }}
    #memorySearch:hover {{
        border-color: #3B444E;
    }}
    #memorySearch:focus {{
        border-color: {p["rosa"]};
    }}
    #memorySearch:disabled {{
        color: #59616B;
        background: #11161B;
        border-color: #20262D;
    }}
    #memorySearchCount {{
        color: {p["apagado"]};
        font-size: 9px;
        min-width: 52px;
    }}
    #memorySectionTitle {{
        color: {p["texto"]};
        font-size: 13px;
        font-weight: 650;
        padding: 5px 2px 2px 2px;
    }}

    #memoryItem {{
        background: {p["superficie"]};
        border: 1px solid #1E252D;
        border-radius: 12px;
    }}
    #memoryItem:hover {{
        background: #171D24;
        border-color: #39434D;
    }}
    #memoryItem[memoryKind="preference"] {{
        border-left: 3px solid #C4556A;
    }}
    #memoryItem[memoryKind="reminder"] {{
        border-left: 3px solid {p["aviso"]};
    }}
    #memoryItem[memoryKind="task"] {{
        border-left: 3px solid {p["sucesso"]};
    }}
    #memoryItemType {{
        color: {p["rosa"]};
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    #memoryItemMeta {{
        color: {p["apagado"]};
        font-size: 8px;
    }}
    #memoryItemSummary {{
        color: {p["texto"]};
        font-size: 13px;
        font-weight: 550;
    }}
    #memoryItemDetail {{
        color: {p["secundario"]};
        font-size: 10px;
    }}
    #memoryEmpty {{
        background: {p["superficie"]};
        border: 1px dashed #2D3540;
        border-radius: 12px;
    }}
    #memoryEmptyTitle {{
        color: {p["texto"]};
        font-size: 12px;
        font-weight: 650;
    }}
    #memoryEmptyText {{
        color: {p["apagado"]};
        font-size: 10px;
    }}
    #memoryRail {{
        background: transparent;
        border: 0;
    }}
    #memoryRailCard, #memoryPrivacyCard {{
        background: {p["superficie"]};
        border: 1px solid #1E252D;
        border-radius: 12px;
    }}
    #memoryPrivacyCard {{
        background: #12171D;
    }}
    #memoryRailTitle {{
        color: {p["texto"]};
        font-size: 10px;
        font-weight: 700;
    }}
    #memoryRailText {{
        color: {p["secundario"]};
        font-size: 9px;
    }}
    #memoryCategoryName {{
        color: {p["secundario"]};
        font-size: 9px;
    }}
    #memoryCategoryValue {{
        color: {p["texto"]};
        font-size: 9px;
        font-weight: 650;
    }}
    """

__all__ = ['qss_memory_refresh']
