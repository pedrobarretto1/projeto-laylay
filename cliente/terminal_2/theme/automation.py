"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_automation_components() -> str:
    """Componentes visuais restantes da p?gina Automa??o."""
    return f"""
                /* Automação — casa conectada com a linguagem visual da Laylay */
                #automationPageContent {{ background: #0C1116; }}
                #automationScroll,
                #automationScroll > QWidget > QWidget,
                #automationMainColumn,
                #automationRail {{ background: transparent; border: 0; }}
                #automationHero {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #18151B, stop: 0.58 #13171D, stop: 1 #111820
                    );
                    border: 1px solid #352D36;
                    border-radius: 16px;
                    min-height: 130px;
                }}
                #automationHeroArt {{ background: transparent; border: 0; }}
                #automationHeroEyebrow {{
                    background: transparent;
                    color: #D95C75;
                    font-size: 8px;
                    font-weight: 800;
                    letter-spacing: 1.6px;
                }}
                #automationHeroTitle {{
                    background: transparent;
                    color: #FCF7F9;
                    font-size: 26px;
                    font-weight: 780;
                }}
                #automationHeroDescription {{
                    background: transparent;
                    color: #A9A5AA;
                    font-size: 10px;
                }}
                #automationLiveBadge {{
                    background: #171E22;
                    border: 1px solid #2A373A;
                    border-radius: 9px;
                    padding: 6px 10px;
                    color: #9AA4AA;
                    font-size: 8px;
                    font-weight: 700;
                }}
                #automationLiveBadge[state="confirmed"] {{
                    background: #17231F;
                    border-color: #356A58;
                    color: #69D09B;
                }}
                #automationLiveBadge[state="partial"] {{
                    background: #282219;
                    border-color: #715A34;
                    color: #DDB464;
                }}
                #automationUpdated {{
                    background: transparent;
                    color: #7E858D;
                    font-size: 8px;
                }}

                #automationDevicesCard,
                #automationRoutinesCard,
                #automationSummaryCard,
                #automationContextCard,
                #automationSafetyCard {{
                    background: #11171C;
                    border: 1px solid #283139;
                    border-radius: 14px;
                }}
                #automationDevicesCard #dashboardCardTitle,
                #automationRoutinesCard #dashboardCardTitle,
                #automationSummaryCard #dashboardCardTitle,
                #automationContextCard #dashboardCardTitle,
                #automationSafetyCard #dashboardCardTitle {{
                    color: #F5F0F3;
                    font-size: 14px;
                    font-weight: 760;
                }}
                #automationDevicesCard #dashboardCardHint,
                #automationRoutinesCard #dashboardCardHint,
                #automationSummaryCard #dashboardCardHint,
                #automationContextCard #dashboardCardHint,
                #automationSafetyCard #dashboardCardHint {{
                    color: #7B838B;
                    font-size: 8px;
                    font-weight: 700;
                    letter-spacing: 0.8px;
                }}
                #automationSectionLead {{
                    background: transparent;
                    border: 0;
                    color: #90979E;
                    font-size: 9px;
                    padding: 0 1px 4px 1px;
                }}

                #automationDeviceCard {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 #171D23, stop: 1 #13191E
                    );
                    border: 1px solid #2A343D;
                    border-radius: 13px;
                    min-height: 264px;
                }}
                #automationDeviceCard:hover {{ border-color: #4B3A43; }}
                #automationDeviceCard[deviceState="on"] {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 #211920, stop: 0.55 #171B20, stop: 1 #141B1F
                    );
                    border-color: #4B3440;
                }}
                #automationDeviceCard[deviceState="offline"] {{
                    background: #15171A;
                    border-color: #3A3439;
                }}
                #automationDeviceCard[actionPending="true"] {{ border-color: #825063; }}
                #automationDeviceIcon {{
                    background: transparent;
                    border: 0;
                }}
                #automationDeviceCard[deviceState="on"] #automationDeviceIcon {{
                    background: transparent;
                    border: 0;
                }}
                #automationDeviceName {{
                    background: transparent;
                    color: #F3EFF1;
                    font-size: 12px;
                    font-weight: 750;
                }}
                #automationDeviceType {{
                    background: transparent;
                    color: #777F87;
                    font-size: 8px;
                }}
                #automationRoomBadge {{
                    background: #1C2228;
                    border: 1px solid #303942;
                    border-radius: 8px;
                    padding: 4px 7px;
                    color: #8E98A1;
                    font-size: 7px;
                    font-weight: 750;
                    letter-spacing: 0.7px;
                }}
                #automationDeviceState {{
                    background: #1C2227;
                    border: 1px solid #2B353C;
                    border-radius: 7px;
                    padding: 3px 7px;
                    color: #838C94;
                    font-size: 8px;
                    font-weight: 800;
                    letter-spacing: 0.8px;
                }}
                #automationDeviceState[deviceState="on"] {{ color: #67D19D; }}
                #automationDeviceState[deviceState="off"] {{ color: #C2A1AA; }}
                #automationDeviceState[deviceState="offline"] {{ color: #CA6B78; }}
                #automationDeviceObservation {{
                    background: transparent;
                    color: #747D85;
                    font-size: 8px;
                }}
                #automationCapabilities {{
                    background: transparent;
                    border: 0;
                    padding: 0;
                    color: #89929A;
                    font-size: 8px;
                }}
                #automationControlLabel {{
                    background: transparent;
                    border: 0;
                    color: #D7D1D5;
                    font-size: 9px;
                    font-weight: 650;
                }}
                #automationControlValue {{
                    background: transparent;
                    border: 0;
                    color: #A9A1A7;
                    font-size: 9px;
                }}
                #automationBrightnessControl {{ background: transparent; border: 0; }}
                #automationBrightnessSlider {{ min-height: 18px; max-height: 18px; }}
                #automationBrightnessSlider::groove:horizontal {{
                    background: #31343A;
                    border: 0;
                    border-radius: 3px;
                    height: 5px;
                }}
                #automationBrightnessSlider::sub-page:horizontal {{
                    background: #EC4E76;
                    border-radius: 3px;
                }}
                #automationBrightnessSlider::add-page:horizontal {{
                    background: #30343A;
                    border-radius: 3px;
                }}
                #automationBrightnessSlider::handle:horizontal {{
                    background: #FFD3DE;
                    border: 3px solid #F15B81;
                    border-radius: 8px;
                    width: 10px;
                    margin: -5px 0;
                }}
                #automationBrightnessSlider:disabled::sub-page:horizontal {{ background: #67404B; }}
                #automationBrightnessSlider:disabled::handle:horizontal {{
                    background: #777D83;
                    border-color: #43484D;
                }}
                #automationPowerButton {{
                    background: #D94B66;
                    border: 1px solid #E15C75;
                    border-radius: 9px;
                    min-height: 28px;
                    padding: 0 15px;
                    color: #FFF8FA;
                    font-size: 9px;
                    font-weight: 760;
                    min-width: 78px;
                }}
                #automationPowerButton:hover {{ background: #EB5872; }}
                #automationPowerButton:disabled {{
                    background: #24272C;
                    border-color: #30353B;
                    color: #666E76;
                }}
                #automationRefreshButton {{
                    background: #191F25;
                    border: 1px solid #313A43;
                    border-radius: 9px;
                    min-height: 28px;
                    padding: 0 12px;
                    color: #B3BAC0;
                    font-size: 9px;
                    font-weight: 650;
                    min-width: 128px;
                }}
                #automationRefreshButton:hover {{
                    background: #20272E;
                    border-color: #5B4550;
                    color: #EF7990;
                }}
                #automationRefreshButton:disabled {{ color: #626A72; border-color: #2A3036; }}

                #automationRoutineRow {{
                    background: #151B20;
                    border: 1px solid #29323A;
                    border-radius: 9px;
                    min-height: 34px;
                    padding: 0 11px;
                    text-align: left;
                    color: #C7C3C6;
                    font-size: 9px;
                }}
                #automationRoutineEmpty {{
                    background: #10161B;
                    border: 1px dashed #3A454E;
                    border-radius: 11px;
                    padding: 14px 15px;
                    color: #A9B0B6;
                    font-size: 9px;
                }}
                #automationRoutineRow:hover {{
                    background: #211B20;
                    border-color: #66404E;
                    color: #EF8297;
                }}
                #automationSummaryMetric {{
                    background: #151B20;
                    border: 1px solid #252E36;
                    border-radius: 9px;
                }}
                #automationSummaryLabel {{ color: #929AA2; font-size: 9px; }}
                #automationSummaryValue {{ color: #F1EDF0; font-size: 14px; font-weight: 780; }}
                #automationContextState {{
                    background: #181E24;
                    border: 1px solid #2C363E;
                    border-radius: 9px;
                    padding: 8px 10px;
                    color: #D9D5D7;
                    font-size: 10px;
                    font-weight: 700;
                }}
                #automationContextHint,
                #automationSafetyHint {{
                    background: transparent;
                    color: #7E878F;
                    font-size: 8px;
                }}
                #automationSafetyFlow {{
                    background: #211920;
                    border: 1px solid #523644;
                    border-radius: 9px;
                    padding: 8px 9px;
                    color: #DF6E85;
                    font-size: 7px;
                    font-weight: 800;
                    letter-spacing: 0.5px;
                }}

                QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
                QScrollBar::handle:vertical {{ background: #49424F; min-height: 32px; border-radius: 4px; }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
                QComboBox QAbstractItemView {{ background: {PALETA['superficie']}; selection-background-color: {PALETA['elevada']}; border: 1px solid {PALETA['borda']}; }}
                QCheckBox {{ color: {PALETA['secundario']}; spacing: 8px; }}
    """

__all__ = ['qss_automation_components']
