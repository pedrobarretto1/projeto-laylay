"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_context_components() -> str:
    """Contexto, Inspector, diagn?sticos e cards compactos compartilhados."""
    return f"""
                #pageTitle {{ font-size: 28px; font-weight: 650; }}
                #pageDescription {{ color: {PALETA['secundario']}; font-size: 14px; max-width: 700px; }}
                #sectionTitle {{ font-size: 17px; font-weight: 650; padding-top: 4px; }}
                #fieldLabel {{ color: {PALETA['secundario']}; font-size: 11px; font-weight: 650; }}
                QPushButton[provider="true"] {{ background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 10px; padding: 13px 15px; text-align: left; color: {PALETA['secundario']}; }}
                QPushButton[provider="true"]:hover {{ background: {PALETA['elevada']}; }}
                QPushButton[provider="true"]:checked {{ background: #292332; border-color: {PALETA['violeta']}; color: {PALETA['texto']}; }}
                #settingsField {{ background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 8px; padding: 10px 12px; selection-background-color: #5D497A; }}
                #settingsField:focus {{ border-color: {PALETA['violeta']}; }}
                #settingsField:read-only {{ color: {PALETA['apagado']}; background: #19171C; }}
                #keyState {{ color: {PALETA['ciano']}; font-size: 11px; }}
                #settingsBanner {{ background: #22202A; border-left: 3px solid {PALETA['ciano']}; padding: 11px 13px; color: {PALETA['secundario']}; }}
                #settingsBanner[kind="success"] {{ border-left-color: {PALETA['sucesso']}; }}
                #settingsBanner[kind="error"] {{ border-left-color: {PALETA['erro']}; }}
                #settingsNote {{ color: {PALETA['secundario']}; background: {PALETA['superficie']}; padding: 13px; border-radius: 8px; }}
                #primaryButton {{ background: {PALETA['violeta']}; color: #161219; border: 0; border-radius: 8px; padding: 10px 16px; font-weight: 700; }}
                #primaryButton:hover {{ background: #B99AF0; }}
                #secondaryButton {{ background: {PALETA['elevada']}; border: 1px solid {PALETA['borda']}; border-radius: 8px; padding: 10px 15px; font-weight: 600; }}
                #diagnosticValue {{ background: {PALETA['superficie']}; border-left: 2px solid {PALETA['ciano']}; padding: 12px 15px; font-family: 'Cascadia Code'; font-size: 12px; }}
                #eventLog {{ font-family: 'Cascadia Code'; background: {PALETA['superficie']}; border: 1px solid {PALETA['borda']}; border-radius: 9px; color: {PALETA['secundario']}; padding: 14px; font-size: 11px; }}

                #intelligenceTitle {{
                    color: #F6F2F4;

                    font-size: 18px;
                    font-weight: 700;
                }}


                /* indicador vivo */

                #liveBadge {{
                    background: #321D23;

                    border: 1px solid #64313C;
                    border-radius: 11px;

                    padding: 4px 9px;

                    color: #FF7186;

                    font-size: 9px;
                    font-weight: 600;
                }}


                /* seções internas da central */

                #dashboardCard[centralSection="true"] {{
                    background: transparent;

                    border: 0;
                    border-radius: 0;
                }}

                #dashboardCard[centralSection="true"]
                #dashboardCardTitle {{
                    color: #F0ECEE;

                    font-size: 13px;
                    font-weight: 700;
                }}


                /* detalhes tipo "sanitizado" */

                #dashboardCardHint {{
                    background: transparent;
                    border: 0;

                    color: #737A83;

                    font-size: 8px;
                }}


                /* =========================================
                AÇÕES RÁPIDAS
                ========================================= */

                QPushButton[dashboardAction="true"] {{
                    background: #191E24;

                    border: 1px solid #30363D;
                    border-radius: 10px;

                    min-height: 40px;

                    padding: 7px 10px;

                    text-align: left;

                    color: #C9C5C8;

                    font-size: 10px;
                    font-weight: 550;
                }}

                QPushButton[dashboardAction="true"]:hover {{
                    background: #251B20;

                    border-color: #75404B;

                    color: #FFF4F6;
                }}

                QPushButton[dashboardAction="true"]:pressed {{
                    background: #301D24;

                    border-color: #954859;
                }}

                QPushButton[dashboardAction="true"]:disabled {{
                    background: #15191E;

                    border-color: #252B31;

                    color: #555C64;
                }}


                /* =========================================
                CONTEXTO ATUAL
                ========================================= */

                #contextItem {{
                    background: #191E24;

                    border: 1px solid #2C3239;
                    border-radius: 9px;
                }}

                #contextItem:hover {{
                    background: #1D2228;

                    border-color: #3B343A;
                }}

                #contextLabel {{
                    background: transparent;
                    border: 0;

                    color: #747C85;

                    font-size: 8px;
                }}

                #contextValue {{
                    background: transparent;
                    border: 0;

                    color: #D8D4D7;

                    font-size: 9px;
                    font-weight: 650;
                }}


                /* =========================================
                MEMÓRIA / ATIVIDADE
                ========================================= */

                #dashboardEmpty {{
                    background: #171C21;

                    border: 1px solid #282F36;
                    border-radius: 9px;

                    padding: 8px 10px;

                    color: #888F97;

                    font-size: 9px;
                }}

                #dashboardActivity {{
                    background: #171C21;

                    border: 1px solid #282F36;
                    border-radius: 9px;

                    padding: 8px 10px;

                    color: #888F97;

                    font-size: 9px;
                }}

                /* =========================================
                   HOME — CARD SISTEMA
                   ========================================= */

                #dashboardCard[railCard="system"] {{
                    background: #14191E;
                    border: 1px solid #2B3239;
                    border-radius: 14px;
                }}

                #dashboardCard[railCard="system"] #dashboardCardTitle {{
                    color: #F3EFF1;
                    font-size: 13px;
                    font-weight: 700;
                }}

                #dashboardCard[railCard="system"] #dashboardCardHint {{
                    background: #2A1A20;
                    border: 1px solid #55303A;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #E96379;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railSystemMetric {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                }}

                #railSystemMetric[state="stale"] {{
                    background: #1C1B1B;
                    border-color: #54442D;
                }}

                #railSystemMetric[state="unavailable"] {{
                    background: #15191D;
                    border-color: #23292F;
                }}

                #railSystemMetricLabel {{
                    background: transparent;
                    border: 0;
                    color: #858D96;
                    font-size: 9px;
                    font-weight: 600;
                }}

                #railSystemMetricValue {{
                    background: transparent;
                    border: 0;
                    color: #F0ECEE;
                    font-size: 11px;
                    font-weight: 700;
                }}

                #railSystemMetricValue[state="stale"] {{
                    color: #D4AE6A;
                }}

                #railSystemMetricValue[state="unavailable"] {{
                    color: #5D656D;
                }}

                #railSystemProgress {{
                    background: #242A30;
                    border: 0;
                    border-radius: 2px;
                    min-height: 4px;
                    max-height: 4px;
                }}

                #railSystemProgress::chunk {{
                    background: #CF485E;
                    border-radius: 2px;
                }}

                #railSystemProgress[available="false"]::chunk {{
                    background: #343A40;
                }}

                #railSystemFooter {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                }}

                #railSystemFooter[state="stale"] {{
                    border-color: #54442D;
                }}

                #railSystemFooter[state="unavailable"] {{
                    background: #15191D;
                    border-color: #23292F;
                }}

                #railSystemFooterIcon {{
                    background: #241B20;
                    border: 1px solid #49313A;
                    border-radius: 11px;
                    color: #D35469;
                    font-size: 10px;
                }}

                #railSystemStatus {{
                    background: transparent;
                    border: 0;
                    padding: 2px 1px;
                    color: #737B84;
                    font-size: 8px;
                }}

                #railSystemStatus[state="ok"] {{
                    color: #68C79A;
                }}

                #railSystemStatus[state="partial"] {{
                    color: #C6A05E;
                }}

                #railSystemStatus[state="unavailable"] {{
                    color: #7A8189;
                }}

                #railSystemStatus[state="pending"] {{
                    color: #69717A;
                }}


                /* =========================================
                   HOME — CARD MÚSICA
                   ========================================= */

                #dashboardCard[railCard="music"] {{
                    background: #14191E;
                    border: 1px solid #2B3239;
                    border-radius: 14px;
                }}

                #dashboardCard[railCard="music"][musicState="playing"] {{
                    border-color: #5A3039;
                }}

                #dashboardCard[railCard="music"][musicState="stale"] {{
                    border-color: #54442D;
                }}

                #dashboardCard[railCard="music"][musicState="unavailable"] {{
                    border-color: #252B31;
                }}

                #dashboardCard[railCard="music"] #dashboardCardTitle {{
                    color: #F3EFF1;
                    font-size: 13px;
                    font-weight: 700;
                }}

                #railMusicBadge {{
                    background: #20262C;
                    border: 1px solid #323940;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #858D96;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railMusicBadge[state="playing"] {{
                    background: #2A1A20;
                    border-color: #5B303B;
                    color: #FF6D82;
                }}

                #railMusicBadge[state="paused"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #A9B0B7;
                }}

                #railMusicBadge[state="ended"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #8C949C;
                }}

                #railMusicBadge[state="stale"] {{
                    background: #272116;
                    border-color: #5A4827;
                    color: #D3AA61;
                }}

                #railMusicBadge[state="unavailable"] {{
                    background: #181C20;
                    border-color: #282E34;
                    color: #646C74;
                }}

                #railMusicTitle {{
                    background: transparent;
                    border: 0;
                    color: #F1EDEF;
                    font-size: 11px;
                    font-weight: 700;
                }}

                #railMusicMeta {{
                    background: transparent;
                    border: 0;
                    color: #777F88;
                    font-size: 8px;
                }}

                #railMusicProgress {{
                    background: #242A30;
                    border: 0;
                    border-radius: 2px;
                    min-height: 4px;
                    max-height: 4px;
                }}

                #railMusicProgress::chunk {{
                    background: #D24A60;
                    border-radius: 2px;
                }}

                #railMusicTime {{
                    background: transparent;
                    border: 0;
                    color: #6F7780;
                    font-size: 8px;
                }}

                #dashboardCard[railCard="music"] #railMusicControl {{
                    background: #191E23;
                    border: 1px solid #30363D;
                    border-radius: 17px;
                    min-width: 34px;
                    max-width: 34px;
                    min-height: 34px;
                    max-height: 34px;
                }}

                #dashboardCard[railCard="music"] #railMusicControl:hover {{
                    background: #251C21;
                    border-color: #69404A;
                }}

                #dashboardCard[railCard="music"] #railMusicControl:pressed {{
                    background: #301D24;
                    border-color: #8D4250;
                }}

                #dashboardCard[railCard="music"] #railMusicControl:disabled {{
                    background: #171B1F;
                    border-color: #252B31;
                }}

                #dashboardCard[railCard="music"]
                #railMusicControl[primary="true"] {{
                    background: #B9384D;
                    border: 1px solid #EC5A70;
                    border-radius: 20px;
                    min-width: 40px;
                    max-width: 40px;
                    min-height: 40px;
                    max-height: 40px;
                }}

                #dashboardCard[railCard="music"]
                #railMusicControl[primary="true"]:hover {{
                    background: #D3455B;
                    border-color: #FF7488;
                }}

                #dashboardCard[railCard="music"]
                #railMusicControl[primary="true"]:disabled {{
                    background: #221C20;
                    border-color: #3C3035;
                }}


                /* =========================================
                   HOME — ROTINAS + MODO JOGO
                   ========================================= */

                #dashboardCard[railCard="routines"],
                #dashboardCard[railCard="game"] {{
                    background: #14191E;
                    border: 1px solid #2B3239;
                    border-radius: 14px;
                }}

                #dashboardCard[railCard="routines"][routineState="active"],
                #dashboardCard[railCard="game"][gameState="active"] {{
                    border-color: #57303A;
                }}

                #dashboardCard[railCard="routines"][routineState="stale"],
                #dashboardCard[railCard="game"][gameState="stale"] {{
                    border-color: #574728;
                }}

                #dashboardCard[railCard="routines"][routineState="unavailable"],
                #dashboardCard[railCard="game"][gameState="unavailable"] {{
                    border-color: #252B31;
                }}

                #dashboardCard[railCard="routines"] #dashboardCardTitle,
                #dashboardCard[railCard="game"] #dashboardCardTitle {{
                    color: #F3EFF1;
                    font-size: 13px;
                    font-weight: 700;
                }}

                /* Rotinas */

                #railRoutineBadge {{
                    background: #20262C;
                    border: 1px solid #323940;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #858D96;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railRoutineBadge[state="active"] {{
                    background: #2A1A20;
                    border-color: #5B303B;
                    color: #FF6D82;
                }}

                #railRoutineBadge[state="empty"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #929AA2;
                }}

                #railRoutineBadge[state="stale"] {{
                    background: #272116;
                    border-color: #5A4827;
                    color: #D3AA61;
                }}

                #railRoutineBadge[state="unavailable"] {{
                    background: #181C20;
                    border-color: #282E34;
                    color: #646C74;
                }}

                #railRoutineRow {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                }}

                #railRoutineRow:hover {{
                    background: #1C2127;
                    border-color: #3C343A;
                }}

                #railRoutineIcon {{
                    background: #241B20;
                    border: 1px solid #49313A;
                    border-radius: 12px;
                    color: #D35469;
                    font-size: 11px;
                    font-weight: 700;
                }}

                #railRoutineName {{
                    background: transparent;
                    border: 0;
                    color: #DDD9DB;
                    font-size: 9px;
                    font-weight: 650;
                }}

                #railRoutineMeta {{
                    background: transparent;
                    border: 0;
                    color: #747C85;
                    font-size: 8px;
                }}

                #railRoutineEmpty {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                    padding: 8px 10px;
                    color: #777F88;
                    font-size: 8px;
                }}

                /* Modo jogo */

                #railGamePanel {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 10px;
                }}

                #railGamePanel[state="active"] {{
                    background: #20191D;
                    border-color: #493039;
                }}

                #railGamePanel[state="stale"] {{
                    background: #1E1B16;
                    border-color: #514326;
                }}

                #railGamePanel[state="unavailable"] {{
                    background: #15191D;
                    border-color: #252B31;
                }}

                #railGameIcon {{
                    background: #20262C;
                    border: 1px solid #30373E;
                    border-radius: 14px;
                    color: #69717A;
                    font-size: 12px;
                    font-weight: 700;
                }}

                #railGameIcon[state="active"] {{
                    background: #382027;
                    border-color: #67313C;
                    color: #FF7186;
                }}

                #railGameIcon[state="stale"] {{
                    background: #342B19;
                    border-color: #66532D;
                    color: #D5AD62;
                }}

                #railGameTitle {{
                    background: transparent;
                    border: 0;
                    color: #E5E1E3;
                    font-size: 10px;
                    font-weight: 700;
                }}

                #railGameMeta {{
                    background: transparent;
                    border: 0;
                    color: #747C85;
                    font-size: 8px;
                }}

                #railGameBadge {{
                    background: #1B2025;
                    border: 1px solid #323940;
                    border-radius: 7px;
                    padding: 3px 6px;
                    color: #858D96;
                    font-size: 8px;
                    font-weight: 700;
                }}

                #railGameBadge[state="active"] {{
                    background: #2A1A20;
                    border-color: #5B303B;
                    color: #FF6D82;
                }}

                #railGameBadge[state="inactive"] {{
                    background: #1B2025;
                    border-color: #333A42;
                    color: #8E969E;
                }}

                #railGameBadge[state="stale"] {{
                    background: #272116;
                    border-color: #5A4827;
                    color: #D3AA61;
                }}

                #railGameBadge[state="unavailable"] {{
                    background: #181C20;
                    border-color: #282E34;
                    color: #646C74;
                }}

                #musicTitle {{ font-size: 13px; font-weight: 700; }}
                #musicControlsPlaceholder {{ color: #5F646B; font-size: 15px; padding: 5px; }}
                #musicPage, #musicScroll, #musicScroll > QWidget > QWidget,
                #musicPageBody {{ background: #0D1115; }}
                #musicPageTitle {{ color: #F8F4F6; font-size: 29px; font-weight: 700; }}
                #musicPageDescription {{ color: {PALETA['secundario']}; font-size: 15px; }}
                #musicHeaderButton, #musicMoreButton {{ background: #15191E; border: 1px solid #2D333A; border-radius: 10px; padding: 10px 15px; color: {PALETA['secundario']}; font-size: 12px; }}
                #musicHeaderButton:hover {{ background: #211A1F; border-color: #713541; color: {PALETA['texto']}; }}
                #musicHero, #musicModule, #musicQueue, #musicLyrics {{ background: #14191E; border: 1px solid #293039; border-radius: 14px; }}
                #musicHero {{ min-height: 306px; }}
                #musicPageTitle, #musicHeroTitle, #musicModuleTitle {{ font-family: 'Segoe UI Variable', 'Segoe UI'; }}
                #musicHeroTitle {{ color: #F8F4F6; font-size: 27px; font-weight: 700; }}
                #musicHeroSubtitle {{ color: {PALETA['secundario']}; font-size: 15px; }}
                #musicNowBadge {{ color: {PALETA['rosa']}; background: #29191E; border: 1px solid #54303A; border-radius: 7px; padding: 5px 9px; font-size: 10px; font-weight: 700; }}
                #musicVolumeReadout {{ color: {PALETA['apagado']}; font-size: 10px; font-weight: 700; }}
                #musicVolumeSlider {{ min-width: 22px; max-width: 22px; }}
                #musicVolumeSlider::groove:vertical {{ background: #2A3037; width: 5px; border-radius: 2px; }}
                #musicVolumeSlider::sub-page:vertical {{ background: #2A3037; border-radius: 2px; }}
                #musicVolumeSlider::add-page:vertical {{ background: {PALETA['rosa']}; border-radius: 2px; }}
                #musicVolumeSlider::handle:vertical {{ background: #F5F1F3; border: 1px solid #C84A5F; height: 15px; margin: 0 -5px; border-radius: 7px; }}
                #musicVolumeSlider:disabled {{ opacity: 0.45; }}
                #musicAudioDevice {{
                    background: #171C21;
                    border: 1px solid #2A3138;
                    border-radius: 10px;
                }}

                #musicAudioDevice[available="true"] {{
                    background: #181C21;
                    border-color: #3A3238;
                }}

                #musicAudioDeviceIcon {{
                    color: #565E67;
                    font-size: 10px;
                }}

                #musicAudioDevice[available="true"] #musicAudioDeviceIcon {{
                    color: {PALETA['rosa']};
                }}

                #musicAudioOutput {{
                    color: #F2EEF0;
                    background: transparent;
                    border: 0;
                    padding: 0;
                    font-size: 12px;
                    font-weight: 650;
                }}

                #musicAudioOutputMeta {{
                    color: #7E8690;
                    font-size: 9px;
                }}

                #musicAudioManage {{
                    background: transparent;
                    border: 0;
                    border-radius: 7px;
                    padding: 5px 8px;
                    color: #737B84;
                    font-size: 10px;
                }}

                #musicAudioManage:hover {{
                    background: #221C20;
                    color: #D9D4D7;
                }}

                #musicAudioManage:disabled {{
                    background: transparent;
                    color: #525960;
                }}
                #musicWaveform {{ background: transparent; }}
                #musicHeroProgress {{ background: #232930; border: 0; border-radius: 2px; min-height: 4px; max-height: 4px; }}
                #musicHeroProgress::chunk {{ background: {PALETA['rosa']}; border-radius: 2px; }}
                #musicTime {{ color: {PALETA['apagado']}; font-size: 12px; }}
                #musicTransportControl {{ background: transparent; border: 0; border-radius: 23px; min-width: 46px; min-height: 46px; }}
                #musicTransportControl:hover {{ background: #281C22; }}
                #musicTransportControl[activeControl="true"] {{ background: #321C24; color: {PALETA['rosa']}; border: 1px solid #8D3C4C; }}
                #musicPrimaryControl {{ background: #B9384D; border: 1px solid #F05B72; border-radius: 29px; min-width: 58px; min-height: 58px; }}
                #musicPrimaryControl:hover {{ background: #D9455D; }}
                #musicPrimaryControl:disabled, #musicTransportControl:disabled {{ background: #1B2025; border-color: #30363D; }}
                #musicObservedState {{ color: {PALETA['apagado']}; font-size: 11px; }}
                #musicModuleTitle {{
                    color: #F1EDEF;

                    font-size: 14px;
                    font-weight: 700;
                }}

                #musicModuleHint {{ color: {PALETA['apagado']}; font-size: 10px; }}
                #musicSideRail {{ background: transparent; min-width: 265px; max-width: 315px; }}
                #musicSideLabel {{ color: {PALETA['secundario']}; font-size: 12px; }}
                #musicSideValue {{ color: #F4F1F3; font-size: 12px; font-weight: 700; }}
                #musicFutureState {{ color: #9298A1; font-size: 12px; line-height: 1.4; }}
                #musicQueuePlaceholder {{ background: #191E24; border: 1px solid #272E35; border-radius: 9px; }}
                #musicQueueScroll,
                #musicQueueScroll > QWidget > QWidget,
                #musicQueueList {{
                    background: transparent;
                    border: 0;
                }}

                #musicQueueNumber {{
                    color: #777F89;
                    font-size: 10px;
                    min-width: 18px;
                }}

                #musicQueueText {{
                    color: #E9E6E8;
                    font-size: 11px;
                    font-weight: 600;
                }}
                #musicFutureButton {{ background: #191E23; border: 1px solid #303740; border-radius: 9px; padding: 10px 12px; color: #9298A1; text-align: left; font-size: 11px; }}
                #musicFutureButton:hover {{ background: #241D22; border-color: #75404B; color: #E7E1E4; }}

                #musicSessionAction {{
                background: #151A1F;

                border: 1px solid #30363E;
                border-radius: 18px;

                min-height: 36px;
                max-height: 36px;

                padding: 0 12px;

                color: #AEB4BC;

                font-size: 10px;
                font-weight: 550;
            }}

            /* indisponíveis */

            #musicSessionAction:disabled {{
                background: #15191E;

                border-color: #2B2B31;

                color: #686E76;
            }}

            #musicSessionAction[actionRole="future"]:disabled {{
                background: transparent;

                border-color: #21272D;

                color: #454C53;
            }}

            #musicSessionAction[actionRole="primary"] {{
                background: #1D181C;

                border-color: #4A323A;

                color: #F0EAED;
            }}

            #musicSessionAction[actionRole="primary"]:hover {{
                background: #2D1C22;

                border-color: #914553;

                color: #FFF7F9;
            }}


            /* utilitários — quase iguais, mas um pouco mais discretos */

            #musicSessionAction[actionRole="utility"] {{
                background: #19191E;

                border-color: #393239;

                color: #D0CBD0;
            }}

            #musicSessionAction[actionRole="utility"]:hover {{
                background: #291B21;

                border-color: #85404D;

                color: #FFF5F7;
            }}


            /* futuro — continua propositalmente apagado */

            #musicSessionAction[actionRole="future"] {{
                background: transparent;

                border-color: #252B31;

                color: #555D65;
            }}

            #musicSessionAction[actionRole="future"]:disabled {{
                background: transparent;

                border-color: #21272D;

                color: #454C53;
            }}


                /* desabilitados */

                #musicSessionAction:disabled {{
                    background: #15191E;

                    border-color: #2B2B31;

                    color: #686E76;
                }}

                #musicSessionAction[actionRole="future"]:disabled {{
                    background: transparent;

                    border-color: #21272D;

                    color: #454C53;
                }}
                #musicPreset {{
                    background: #171C21;
                    border: 1px solid #292F36;
                    border-radius: 9px;
                    padding: 0;
                    text-align: left;
                }}

                #musicPreset:hover {{
                    background: #1D2228;
                    border-color: #4A353C;
                }}

                #musicPreset[activePlaylist="true"] {{
                    background: #24191E;
                    border-color: #8B3C4B;
                }}

                #musicPresetTitle {{
                    background: transparent;
                    border: 0;

                    color: #E8E4E6;
                    font-size: 11px;
                    font-weight: 650;
                }}

                #musicPresetTitle[activePlaylist="true"] {{
                    color: #FF647B;
                }}

                #musicPresetCount {{
                    background: transparent;
                    border: 0;

                    color: #7F8790;
                    font-size: 9px;
                }}

                #musicPresetIcon {{
                    background: transparent;
                    border: 0;

                    color: #F5F1F3;
                    font-size: 16px;
                    font-weight: 700;
                }}


                /* caixas coloridas */

                #musicPresetIconBox[presetTone="0"] {{
                    background: #472326;
                    border: 1px solid #713239;
                    border-radius: 7px;
                }}

                #musicPresetIconBox[presetTone="1"] {{
                    background: #302651;
                    border: 1px solid #55428A;
                    border-radius: 7px;
                }}

                #musicPresetIconBox[presetTone="2"] {{
                    background: #183C2E;
                    border: 1px solid #28634A;
                    border-radius: 7px;
                }}

                #musicPresetIconBox[presetTone="3"] {{
                    background: #1C2E4B;
                    border: 1px solid #325387;
                    border-radius: 7px;
                }}

                #musicPresetIconBox[presetTone="4"] {{
                    background: #40243A;
                    border: 1px solid #6C3B61;
                    border-radius: 7px;
                }}

                #musicPresetIconBox[presetTone="5"] {{
                    background: #46351D;
                    border: 1px solid #74562A;
                    border-radius: 7px;
                }}
                #musicQueueDetail {{
                    color: #777F89;
                    font-size: 9px;
                }}

                #musicQueueDuration {{
                    color: #9299A2;
                    font-size: 10px;
                    min-width: 31px;
                }}

                #musicCatalogState {{
                    color: #89919B;
                    font-size: 10px;
                }}

                #musicQueueItem {{
                    background: transparent;
                    border: 0;
                    border-radius: 7px;
                    text-align: left;
                    padding: 0;
                }}

                #musicQueueItem:hover {{
                    background: #1B2026;
                    border: 0;
                }}

                #musicQueueItem:focus {{
                    background: #211A1F;
                    border: 0;
                }}

                #musicQueueItem:disabled {{
                    background: transparent;
                    border: 0;
                }}
                #musicQueueItem[queueTop="true"] {{
                    background: #21181D;
                    border: 0;
                }}

                #musicQueueItem[queueTop="true"]:hover {{
                    background: #281B21;
                }}

                #musicQueueNumber[queueTop="true"] {{
                    color: {PALETA['rosa']};
                    font-size: 12px;
                    font-weight: 700;
                    letter-spacing: -1px;
                }}
                #musicContextSummary {{
                    background: transparent;
                    border: 0;

                    color: #9DA4AC;
                    font-size: 11px;

                    padding: 2px 1px;
                }}


                /* recomendação principal */

                #musicSuggestion {{
                    background: #21181D;

                    border: 1px solid #4A2B34;
                    border-radius: 9px;

                    padding: 8px 10px;

                    color: #E88A9A;

                    font-size: 11px;
                    font-weight: 550;
                }}


                /* área dos chips */

                #musicContextChips {{
                    background: transparent;
                    border: 0;
                }}


                #musicContextChip {{
                    background: #171C21;

                    border: 1px solid #2A3138;
                    border-radius: 8px;

                    padding: 5px 7px;

                    color: #858D96;

                    font-size: 9px;
                }}
                #musicLyrics {{
                    border-color: #382B31;
                }}

                #musicLyricsText {{
                    background: #101519;
                    border: 1px solid #272E35;
                    border-radius: 11px;
                    padding: 21px 26px;
                    color: #C9C5C8;
                    selection-background-color: #66313D;
                }}

                #musicLyricsProgress {{
                    background: #22282E;
                    border: 0;
                    border-radius: 1px;
                    min-height: 3px;
                    max-height: 3px;
                }}

                #musicLyricsProgress::chunk {{
                    background: #FF5C76;
                    border: 0;
                    border-radius: 1px;
                }}

                #musicLyricsSource {{
                    color: #747C85;
                    font-size: 9px;
                }}
                #musicAudioDevice {{
                background: #171C21;
                border: 1px solid #292F36;
                border-radius: 9px;
                }}

                #musicAudioDevice[available="true"] {{
                    background: #191D22;
                    border-color: #393139;
                }}


                /* caixinha do ícone */

                #musicAudioIconBox {{
                    background: #20262C;
                    border: 1px solid #30373F;
                    border-radius: 8px;
                }}

                #musicAudioIconBox[available="true"] {{
                    background: #2B1C22;
                    border-color: #67313C;
                }}

                #musicAudioDeviceIcon {{
                    background: transparent;
                    border: 0;

                    color: #737B84;
                    font-size: 17px;
                    font-weight: 700;
                }}

                #musicAudioIconBox[available="true"]
                #musicAudioDeviceIcon {{
                    color: #FF647B;
                }}


                /* textos */

                #musicAudioOutput {{
                    background: transparent;
                    border: 0;
                    padding: 0;

                    color: #E9E5E7;
                    font-size: 11px;
                    font-weight: 650;
                }}

                #musicAudioOutputMeta {{
                    background: transparent;
                    border: 0;

                    color: #777F88;
                    font-size: 9px;
                }}


                /* check de selecionado */

                #musicAudioSelected {{
                    background: #1D2227;
                    border: 1px solid #30373E;
                    border-radius: 12px;

                    color: #686F77;
                    font-size: 11px;
                    font-weight: 700;
                }}

                #musicAudioSelected[selected="true"] {{
                    background: #382027;
                    border-color: #763746;

                    color: #FF647B;
                }}

                #musicAudioDeviceList {{
                    min-height: 30px;
                    padding: 4px 9px;
                    background: #171C21;
                    border: 1px solid #30363D;
                    border-radius: 7px;
                    color: #D9D5D7;
                    font-size: 10px;
                }}

                #musicAudioDeviceList:hover,
                #musicAudioDeviceList:focus {{
                    border-color: #7A3847;
                    background: #1B1F24;
                }}

                #musicAudioDeviceList:disabled {{
                    color: #646B73;
                    border-color: #292F35;
                }}

                #musicAudioDeviceList QAbstractItemView {{
                    background: #171B20;
                    border: 1px solid #483039;
                    color: #DDD8DA;
                    selection-background-color: #3A232A;
                    selection-color: #FF7388;
                    outline: 0;
                }}


                /* botão inferior */

                #musicAudioManage {{
                    background: transparent;
                    border: 0;
                    border-radius: 7px;

                    padding: 4px 5px;

                    color: #747C85;
                    font-size: 9px;

                    text-align: left;
                }}

                #musicAudioManage:hover {{
                    background: #1C2025;
                    color: #C7C2C5;
                }}

                #musicAudioManage:disabled {{
                    background: transparent;
                    color: #555D65;
                }}
                #musicSideRail {{
                background: transparent;

                min-width: 265px;
                max-width: 315px;
            }}


            /* =========================================
            SISTEMA
            ========================================= */

            #musicSystemMetric {{
                background: transparent;
                border: 0;
            }}

            #musicSideLabel {{
                color: #8E969F;
                font-size: 10px;
            }}

            #musicSideValue {{
                color: #E8E5E7;
                font-size: 10px;
                font-weight: 650;
            }}

            #musicSystemBar {{
                background: #22282E;

                border: 0;
                border-radius: 2px;

                min-height: 4px;
                max-height: 4px;
            }}

            #musicSystemBar::chunk {{
                background: #C84C61;
                border-radius: 2px;
            }}

            #musicSystemBar[available="false"]::chunk {{
                background: #343A41;
            }}


            /* =========================================
            MODO DE AUDIÇÃO
            ========================================= */

            #musicListeningRow {{
                background: #171C21;

                border: 1px solid #292F36;
                border-radius: 8px;
            }}

            #musicListeningRow[available="true"] {{
                background: #191D22;
                border-color: #393139;
            }}

            #musicListeningIcon {{
                background: transparent;
                border: 0;

                color: #B15A6B;
                font-size: 14px;
            }}

            #musicListeningName {{
                background: transparent;
                border: 0;

                color: #D9D5D8;
                font-size: 10px;
                font-weight: 600;
            }}

            #musicListeningValue {{
                background: transparent;
                border: 0;

                color: #FF647B;
                font-size: 10px;
                font-weight: 700;
            }}

            #musicListeningFuture {{
                background: transparent;
                border: 0;

                color: #626A73;
                font-size: 8px;
            }}


            /* =========================================
            ROTINAS
            ========================================= */

            #musicRoutineEmpty {{
                background: transparent;
                border: 0;

                color: #757D86;
                font-size: 10px;
            }}

            #musicRoutineRow {{
                background: #171C21;

                border: 1px solid #282F35;
                border-radius: 8px;
            }}

            #musicRoutineDot {{
                background: transparent;
                border: 0;

                color: #BD5366;
                font-size: 8px;
            }}

            #musicRoutineName {{
                background: transparent;
                border: 0;

                color: #D8D4D7;
                font-size: 10px;
            }}

            #musicRoutineTime {{
                background: #20262C;

                border: 0;
                border-radius: 6px;

                padding: 2px 5px;

                color: #969DA5;
                font-size: 8px;
            }}


            /* =========================================
            LUZES
            ========================================= */

            #musicLightsDevice {{
                background: #171C21;

                border: 1px solid #292F36;
                border-radius: 8px;
            }}

            #musicLightsDevice[configured="true"] {{
                background: #1C1B21;
                border-color: #48323A;
            }}

            #musicLightsIcon {{
                background: transparent;
                border: 0;

                color: #555D65;
                font-size: 10px;
            }}

            #musicLightsDevice[configured="true"]
            #musicLightsIcon {{
                color: #FF647B;
            }}

            #musicLightsName {{
                background: transparent;
                border: 0;

                color: #DCD8DA;
                font-size: 10px;
                font-weight: 600;
            }}

            #musicLightsState {{
                background: transparent;
                border: 0;

                color: #767E87;
                font-size: 8px;
            }}

            #musicLightsBadge {{
                background: #20262C;

                border: 1px solid #30373E;
                border-radius: 7px;

                padding: 3px 6px;

                color: #696F77;
                font-size: 8px;
            }}

            #musicLightsBadge[configured="true"] {{
                background: #352027;
                border-color: #69333E;

                color: #FF7186;
            }}

            /* =========================================
            MEMÓRIA RECENTE
            ========================================= */

            #memoryRecentCard {{
                background: #171C21;

                border: 1px solid #292F36;
                border-radius: 9px;
            }}


            /* lembrete */

            #memoryRecentCard[memoryKind="reminder"] {{
                background: #20191D;

                border-color: #493039;
            }}


            /* preferência */

            #memoryRecentCard[memoryKind="preference"] {{
                background: #1D191E;

                border-color: #40303A;
            }}


            /* tarefa */

            #memoryRecentCard[memoryKind="task"] {{
                background: #171D1B;

                border-color: #294138;
            }}


            /* ícone */

            #memoryRecentIcon {{
                background: #20262C;

                border: 1px solid #30373E;
                border-radius: 14px;

                color: #969DA5;

                font-size: 13px;
                font-weight: 700;
            }}

            #memoryRecentCard[memoryKind="reminder"]
            #memoryRecentIcon {{
                background: #382027;

                border-color: #67313C;

                color: #FF7186;
            }}

            #memoryRecentCard[memoryKind="preference"]
            #memoryRecentIcon {{
                background: #342029;

                border-color: #623544;

                color: #EE708B;
            }}

            #memoryRecentCard[memoryKind="task"]
            #memoryRecentIcon {{
                background: #192A24;

                border-color: #345746;

                color: #68C79A;
            }}


            /* textos */

            #memoryRecentSummary {{
                background: transparent;
                border: 0;

                color: #DCD8DA;

                font-size: 9px;
                font-weight: 600;
            }}

            #memoryRecentDetail {{
                background: transparent;
                border: 0;

                color: #737B84;

                font-size: 8px;
            }}

            /* =========================================
            ATIVIDADE RECENTE
            ========================================= */

            #activityRecentEmpty {{
                background: #171C21;

                border: 1px solid #282F36;
                border-radius: 9px;

                padding: 8px 10px;

                color: #747C85;

                font-size: 9px;
            }}


            /* evento */

            #activityRecentRow {{
                background: #171C21;

                border: 1px solid #282F36;
                border-radius: 8px;
            }}

            #activityRecentRow:hover {{
                background: #1C2127;

                border-color: #3A343A;
            }}


            /* ponto */

            #activityRecentDot {{
                background: transparent;
                border: 0;

                color: #C64E62;

                font-size: 7px;
            }}


            /* texto */

            #activityRecentText {{
                background: transparent;
                border: 0;

                color: #D5D1D4;

                font-size: 9px;
                font-weight: 550;
            }}


            /* horário */

            #activityRecentTime {{
                background: #20252B;

                border: 0;
                border-radius: 6px;

                padding: 2px 5px;

                color: #777F88;

                font-size: 8px;
            }}

                #musicSystemBar {{ background: #252B32; border: 0; border-radius: 3px; min-height: 6px; max-height: 6px; }}
                #musicSystemBar::chunk {{ background: #C64257; border-radius: 3px; }}
                #musicSystemBar[available="false"]::chunk {{ background: #343A41; }}
                #railMusicControl {{ background: transparent; border: 0; border-radius: 18px; min-width: 36px; min-height: 36px; color: {PALETA['texto']}; font-size: 16px; }}
                #railMusicControl:hover {{ background: #2B2025; color: {PALETA['rosa']}; }}
                QPushButton[dashboardAction="true"][actionState="sending"],
                QPushButton[dashboardAction="true"][actionState="received"],
                QPushButton[dashboardAction="true"][actionState="executing"] {{ background: #241D22; border-color: #8B4352; color: {PALETA['rosa']}; }}
                QPushButton[dashboardAction="true"][actionState="confirmed"] {{ background: #16231F; border-color: #356E5A; color: {PALETA['sucesso']}; }}
                QPushButton[dashboardAction="true"][actionState="partial"] {{ background: #282219; border-color: #806233; color: #E5B965; }}
                QPushButton[dashboardAction="true"][actionState="failed"] {{ background: #28191C; border-color: #7A303B; color: {PALETA['erro']}; }}
                QProgressBar {{ background: #15191E; border: 1px solid #30363E; border-radius: 4px; min-height: 7px; max-height: 7px; }}
                QProgressBar::chunk {{ background: {PALETA['violeta']}; border-radius: 3px; }}
                #systemSparkline {{ color: {PALETA['rosa']}; font-size: 18px; letter-spacing: 1px; }}

                /* Sistema — dashboard operacional */
                #systemPageContent {{ background: #0C1116; }}
                #systemHero {{
                    background: #10161C;
                    border: 1px solid #252E36;
                    border-radius: 14px;
                }}
                #systemHeroTitle {{ font-size: 24px; font-weight: 760; color: #F7F3F5; }}
                #systemHeroDescription {{ font-size: 11px; color: #A2A8AF; }}
                #systemUpdated {{ font-size: 10px; color: #949BA3; }}

                #systemPerformanceCard,
                #systemModulesCard,
                #systemEventsCard,
                #systemCompactCard,
                #systemRailActionsCard {{
                    background: #11171C;
                    border: 1px solid #283139;
                    border-radius: 14px;
                }}
                #systemPerformanceCard #dashboardCardTitle,
                #systemModulesCard #dashboardCardTitle,
                #systemEventsCard #dashboardCardTitle,
                #systemCompactCard #dashboardCardTitle,
                #systemRailActionsCard #dashboardCardTitle {{
                    color: #F3EFF1;
                    font-size: 14px;
                    font-weight: 740;
                }}
                #systemPerformanceCard #dashboardCardHint,
                #systemModulesCard #dashboardCardHint,
                #systemEventsCard #dashboardCardHint,
                #systemCompactCard #dashboardCardHint,
                #systemRailActionsCard #dashboardCardHint {{
                    color: #737D86;
                    font-size: 8px;
                }}
                #systemPerformanceLegend {{
                    color: #78828B;
                    font-size: 8px;
                    background: transparent;
                    border: 0;
                }}
                #systemMetricCard {{
                    background: #151B21;
                    border: 1px solid #29323B;
                    border-radius: 10px;
                    min-width: 96px;
                    min-height: 104px;
                }}
                #systemMetricProgress {{ min-height: 3px; max-height: 3px; }}
                #systemMetricSparkline {{ background: transparent; border: 0; }}

                #systemModelCard {{ min-width: 300px; max-width: 330px; }}
                #systemModelRow {{ min-height: 27px; }}
                #systemModelRow #dashboardMetricLabel,
                #systemModelRow #dashboardMetricValue {{ padding: 4px 7px; font-size: 9px; }}

                #systemAudioCard {{ min-width: 220px; }}
                #systemModulesCard {{ min-width: 340px; }}
                #systemStorageCard {{ min-width: 250px; }}
                #systemTableHeader {{
                    color: #737C85;
                    font-size: 8px;
                    font-weight: 700;
                    background: transparent;
                    border: 0;
                }}
                #systemModuleRow {{
                    background: #151B20;
                    border: 1px solid #252E36;
                    border-radius: 7px;
                }}
                #systemModuleName {{ color: #DBD8DA; font-size: 9px; font-weight: 650; }}
                #systemModuleState {{ color: #879099; font-size: 8px; }}
                #systemModuleState[state="online"], #systemModuleState[state="ready"] {{ color: #65C891; }}
                #systemModuleState[state="degraded"] {{ color: #D6A04F; }}
                #systemModuleState[state="unavailable"] {{ color: #C96573; }}
                #systemModuleMetric {{ color: #747D85; font-size: 8px; }}

                #systemBottomRow {{ background: transparent; border: 0; }}
                #systemActionsCard {{ min-width: 300px; }}
                #systemEventsEmpty {{
                    color: #737C85;
                    font-size: 9px;
                    padding: 16px 8px;
                }}
                #systemEventItem {{
                    background: #151B20;
                    border: 1px solid #252E36;
                    border-radius: 8px;
                    color: #B7BDC3;
                    font-size: 9px;
                    padding: 6px 9px;
                }}

                #systemCompactCard,
                #systemLaylayCard,
                #systemRailActionsCard,
                #systemAlertsCard {{ min-width: 264px; max-width: 280px; }}
                #systemRailMetric {{ background: transparent; border: 0; min-height: 23px; }}
                #systemRailMetricName {{ color: #B7BDC3; font-size: 9px; }}
                #systemRailMetricValue {{ color: #F3EFF1; font-size: 9px; font-weight: 700; }}
                #systemCompactCard #systemMetricSparkline {{ min-height: 18px; max-height: 23px; }}
                #systemRailActionsCard QPushButton[systemQuickAction="true"] {{ min-height: 31px; }}

                /* Sistema — geometria de três faixas */
                #systemAudioRow #dashboardMetricLabel,
                #systemAudioRow #dashboardMetricValue {{ padding: 2px 5px; font-size: 8px; }}
                #systemAudioStatus {{ padding: 4px 6px; font-size: 9px; }}
                #systemAudioLevelHeader {{ min-height: 13px; max-height: 16px; }}
                #systemStorageMetric {{ min-height: 35px; max-height: 40px; }}
                #systemStorageHint {{ padding: 3px 6px; font-size: 8px; }}
                #systemModuleRow {{ min-height: 24px; max-height: 28px; }}
                #systemEventsEmpty {{ padding: 7px 6px; }}
                #systemRailMetric {{ min-height: 17px; max-height: 19px; }}
                #systemCompactCard #systemMetricSparkline {{ min-height: 14px; max-height: 17px; }}
                #systemLaylayRow #dashboardMetricLabel,
                #systemLaylayRow #dashboardMetricValue {{ padding: 3px 5px; font-size: 8px; }}
                #systemLaylayStatus {{ padding: 4px 6px; }}
                #systemLaylayPulse {{ padding: 3px 6px; font-size: 8px; }}

                /* Sistema universal — o mesmo pulso visual em todos os rails */
                #compactSystemCard {{
                    background: #11171C;
                    border: 1px solid #2A333B;
                    border-radius: 12px;
                    min-width: 250px;
                    max-width: 310px;
                }}
                #compactSystemTitle {{
                    background: transparent;
                    border: 0;
                    color: #F4F0F2;
                    font-size: 12px;
                    font-weight: 740;
                }}
                #compactSystemHint {{
                    background: transparent;
                    border: 0;
                    color: #73818B;
                    font-size: 7px;
                }}
                #compactSystemHint[state="dados_antigos"] {{ color: #D39A4A; }}
                #compactSystemHint[state="indisponível"] {{ color: #69737C; }}
                #compactSystemMetric {{
                    background: transparent;
                    border: 0;
                    min-height: 18px;
                    max-height: 18px;
                }}
                #compactSystemMetricName {{
                    background: transparent;
                    border: 0;
                    color: #B7C0C8;
                    font-size: 8px;
                }}
                #compactSystemMetricValue {{
                    background: transparent;
                    border: 0;
                    color: #F2EEF0;
                    font-size: 8px;
                    font-weight: 700;
                }}
                #compactSystemMetric[state="stale"] #compactSystemMetricValue {{
                    color: #D5A45B;
                }}
                #compactSystemMetric[state="unavailable"] #compactSystemMetricValue {{
                    color: #68737C;
                }}
                QWidget[compactSystemGraph="true"],
                #musicSystemBar[compactSystemGraph="true"],
                #railSystemProgress[compactSystemGraph="true"] {{
                    background: transparent;
                    border: 0;
                    min-height: 18px;
                    max-height: 18px;
                }}

    """

__all__ = ['qss_context_components']
