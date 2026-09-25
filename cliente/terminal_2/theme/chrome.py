"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_chrome_components() -> str:
    """Chrome, sidebar, topbar e navega??o global do Terminal."""
    return f"""
                * {{ font-family: 'Segoe UI Variable', 'Segoe UI', Arial; color: {PALETA['texto']}; font-size: 14px; }}
                #root, #mainSurface, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {PALETA['fundo']}; }}
                #sidebar {{ background: #11151A; border-right: 1px solid #2B3037; }}
                #brand {{ font-size: 21px; font-weight: 700; }}
                #brandCaption {{ color: {PALETA['apagado']}; font-size: 10px; }}
                #sideSection, #eyebrow {{ color: {PALETA['apagado']}; font-size: 10px; font-weight: 700; letter-spacing: 1.2px; }}
                QPushButton[nav="true"] {{ background: transparent; border: 0; border-radius: 9px; text-align: left; padding: 12px 14px; min-height: 22px; color: {PALETA['secundario']}; }}
                QPushButton[nav="true"]:hover {{ background: {PALETA['elevada']}; color: {PALETA['texto']}; }}
                QPushButton[nav="true"]:checked {{ background: #2A1C22; color: {PALETA['texto']}; }}
                #navIndicator {{ background: {PALETA['rosa']}; border: 0; border-radius: 1px; }}
                QPushButton:focus, QToolButton:focus, QTextEdit:focus, QComboBox:focus, QCheckBox:focus {{ border: 1px solid {PALETA['rosa']}; outline: 0; }}
                #recentItem {{ color: {PALETA['secundario']}; padding: 9px 12px; background: transparent; border: 0; border-radius: 8px; text-align: left; }}
                #recentItem:hover {{ color: {PALETA['texto']}; background: {PALETA['elevada']}; }}
                #conversationList, #conversationListContent {{ background: transparent; border: 0; }}
                #conversationTools {{ background: transparent; border: 0; }}
                #conversationSearch {{ background: #151A20; border: 1px solid #2B323A; border-radius: 8px; padding: 6px 8px; color: {PALETA['texto']}; font-size: 10px; min-height: 20px; }}
                #conversationSearch:focus {{ border-color: #6E3C4B; }}
                #archivedConversationsButton {{ min-width: 30px; max-width: 30px; min-height: 30px; max-height: 30px; border: 1px solid #2B323A; background: #151A20; }}
                #archivedConversationsButton:checked {{ color: {PALETA['rosa']}; border-color: #6E3C4B; background: #281C22; }}
                #conversationSection {{ color: {PALETA['apagado']}; font-size: 9px; font-weight: 700; padding: 5px 7px 2px 7px; }}
                #conversationEmpty {{ color: {PALETA['apagado']}; font-size: 10px; padding: 9px 7px; }}
                #conversationRow {{ background: transparent; border: 0; border-radius: 8px; }}
                #conversationRow[active="true"] {{ background: #251B20; }}
                #conversationRow[archived="true"] {{ background: #12161B; }}
                #conversationItem {{ color: {PALETA['secundario']}; background: transparent; border: 0; border-radius: 7px; padding: 7px 7px; text-align: left; font-size: 11px; }}
                #conversationItem:hover {{ color: {PALETA['texto']}; background: #1B2026; }}
                #conversationItem:checked {{ color: {PALETA['texto']}; font-weight: 650; }}
                #conversationItem[archived="true"] {{ color: {PALETA['apagado']}; font-style: italic; }}
                #conversationMenu {{ min-width: 24px; max-width: 24px; min-height: 24px; max-height: 24px; color: {PALETA['apagado']}; }}
                #mindStatus {{ color: {PALETA['apagado']}; padding: 8px; font-size: 11px; }}
                #footerSettings {{ background: transparent; border: 0; border-radius: 8px; text-align: left; padding: 10px; color: {PALETA['secundario']}; }}
                #footerSettings:hover {{ background: {PALETA['elevada']}; color: {PALETA['texto']}; }}
                #collapseButton, QToolButton {{ background: transparent; border: 1px solid transparent; border-radius: 7px; min-width: 34px; min-height: 32px; color: {PALETA['secundario']}; }}
                QToolButton:hover {{ background: {PALETA['elevada']}; border-color: {PALETA['borda']}; color: {PALETA['texto']}; }}
                /* HOME — BASE VISUAL */
                #topbar {{ background: #0C1014; border-bottom: 1px solid #242A31; min-height: 62px; }}
                #headerTitle {{ font-weight: 650; }}
                #statusChip {{ background: #11151A; border: 1px solid {PALETA['borda']}; border-radius: 9px; }}
                #statusChipText {{ color: {PALETA['secundario']}; font-size: 11px; }}
                #statusChipDot {{ color: {PALETA['apagado']}; font-size: 9px; }}
                #statusChipDot[state="online"] {{ color: {PALETA['sucesso']}; }}
                #statusChipDot[state="error"] {{ color: {PALETA['erro']}; }}
                #statusChipDot[state="unavailable"] {{ color: #9A7E4C; }}

                #sidebarBrandBar {{
                    background: transparent;
                    border: 0;
                    border-bottom: 1px solid #1E252C;
                }}

                #brand {{
                    color: #F7F3F5;
                    font-size: 19px;
                    font-weight: 720;
                }}

                #brandCaption {{
                    color: #747C85;
                    font-size: 8px;
                }}

                #collapseButton {{
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 9px;
                    min-width: 30px;
                    max-width: 30px;
                    min-height: 30px;
                    max-height: 30px;
                }}

                #collapseButton:hover {{
                    background: #191E23;
                    border-color: #2D343B;
                }}

                QPushButton[nav="true"] {{
                    background: transparent;
                    border: 0;
                    border-left: 3px solid transparent;
                    border-radius: 9px;
                    text-align: left;

                    padding: 11px 11px;
                    min-height: 25px;

                    color: #C5C2C5;
                    font-size: 13px;
                    font-weight: 500;
                }}

                QPushButton[nav="true"]:hover {{
                    background: #181D22;
                    color: #F5F1F3;
                }}

                QPushButton[nav="true"]:checked {{
                    background: qlineargradient(
                        x1: 0, y1: 0,
                        x2: 1, y2: 0,
                        stop: 0 #312027,
                        stop: 1 #241A1F
                    );

                    border-left: 3px solid #FF5C73;
                    color: #F8F4F6;
                }}

                #sidebarProfile {{
                    background: #12171C;
                    border: 1px solid #20272E;
                    border-radius: 13px;
                }}

                #profileName {{
                    background: transparent;
                    border: 0;
                    color: #E9E5E7;
                    font-size: 11px;
                    font-weight: 650;
                }}

                #profileStatus {{
                    background: transparent;
                    border: 0;
                    color: #8A929A;
                    font-size: 8px;
                }}

                #profileStatus[state="online"] {{
                    color: #68C79A;
                }}

                #profileStatus[state="offline"] {{
                    color: #9A7E4C;
                }}

                #profileVersion {{
                    background: transparent;
                    border: 0;
                    color: #656D75;
                    font-size: 8px;
                }}

                #profileHeart {{
                    background: transparent;
                    border: 0;
                    color: #E44B62;
                    font-size: 13px;
                }}

                #topbar {{
                    background: #0B0F13;
                    border-bottom: 1px solid #222931;
                    min-height: 64px;
                }}

                #statusChip {{
                    background: #10151A;
                    border: 1px solid #293038;
                    border-radius: 10px;
                }}

                #statusChipText {{
                    color: #C9C5C8;
                    font-size: 11px;
                    font-weight: 520;
                }}

                #statusChipDot {{
                    color: #687079;
                    font-size: 9px;
                }}

                #modeSwitch {{
                    background: #11161B;
                    border: 1px solid #293038;
                    border-radius: 10px;
                }}

                QPushButton[segment="true"] {{
                    background: transparent;
                    border: 0;
                    border-radius: 7px;

                    padding: 7px 12px;

                    color: #777F88;
                    font-size: 10px;
                    font-weight: 650;
                }}

                QPushButton[segment="true"]:checked {{
                    background: #1C2127;
                    color: #F2EEF0;
                }}



                /* =========================================
                   TOPBAR — GEOMETRIA FINAL
                   ========================================= */

                #topbar {{
                    background: #0B0F13;
                    border-bottom: 1px solid #20272E;
                    min-height: 66px;
                }}

                #statusChip {{
                    background: #10151A;
                    border: 1px solid #2A3138;
                    border-radius: 10px;
                    min-height: 32px;
                }}

                #statusChipText {{
                    color: #D0CCD0;
                    font-size: 11px;
                    font-weight: 540;
                }}

                #statusChipDot {{
                    font-size: 9px;
                }}

                #modeSwitch {{
                    background: #10151A;
                    border: 1px solid #2A3138;
                    border-radius: 10px;
                    min-height: 32px;
                }}

                QPushButton[segment="true"] {{
                    background: transparent;
                    border: 0;
                    border-radius: 7px;
                    padding: 7px 12px;
                    color: #777F88;
                    font-size: 10px;
                    font-weight: 650;
                }}

                QPushButton[segment="true"]:checked {{
                    background: #1D2228;
                    color: #F4F0F2;
                }}




                /* =========================================
                   PERFIL DO USUÁRIO
                   ========================================= */





                /* =========================================
                   BOTÃO DE PERFIL
                   ========================================= */





                #emptyState {{ background: transparent; }}
                #emptyMark {{ color: {PALETA['violeta']}; font-size: 28px; }}
                #emptyTitle {{ font-size: 23px; font-weight: 650; }}
                #emptyCopy {{ color: {PALETA['secundario']}; font-size: 14px; }}
    """

__all__ = ['qss_chrome_components']
