"""Parte modular do tema do Terminal Laylay 3.0."""

def qss_system_components() -> str:
    """Componentes operacionais e geometria da p?gina Sistema."""
    return f"""
/* =========================================
   — NOVA ABA SISTEMA
   ========================================= */

#systemPage {{
    background: transparent;
}}

#systemHero {{
    background: #10151A;
    border: 1px solid #272E35;
    border-radius: 14px;
}}

#systemHeroTitle {{
    background: transparent;
    border: 0;
    color: #F7F3F5;
    font-size: 24px;
    font-weight: 720;
}}

#systemHeroDescription {{
    background: transparent;
    border: 0;
    color: #8D949C;
    font-size: 11px;
}}

#systemUpdated {{
    background: transparent;
    border: 0;
    color: #777F88;
    font-size: 9px;
    padding: 4px 2px;
}}

#systemSectionCard {{
    background: #11161B;
    border: 1px solid #282F36;
    border-radius: 13px;
}}

#systemSectionCard #dashboardCardTitle {{
    color: #F0ECEE;
    font-size: 13px;
    font-weight: 700;
}}

#systemSectionCard #dashboardCardHint {{
    background: transparent;
    border: 0;
    color: #68717A;
    font-size: 8px;
}}

#systemSummaryRow {{
    background: #151A1F;
    border: 1px solid #232A31;
    border-radius: 8px;
}}

#systemSummaryRow #dashboardMetricLabel {{
    background: transparent;
    border: 0;
    padding: 7px 9px;
    color: #8D949C;
    font-size: 9px;
    font-weight: 600;
}}

#systemSummaryRow #dashboardMetricValue {{
    background: transparent;
    border: 0;
    padding: 7px 9px;
    color: #F0ECEE;
    font-size: 10px;
    font-weight: 700;
}}

#systemSummarySeparator {{
    background: #252C33;
    border: 0;
}}

#systemSummarySensor {{
    background: transparent;
    border: 0;
    padding: 2px 3px;
    color: #BBB7BB;
    font-size: 10px;
}}

#systemSummaryState {{
    background: #171C21;
    border: 1px solid #292F36;
    border-radius: 8px;
    padding: 8px 9px;
    color: #777F88;
    font-size: 8px;
}}

#systemSummaryState[state="ok"] {{
    border-color: #315242;
    color: #79CFA4;
}}

#systemSummaryState[state="partial"] {{
    border-color: #51452F;
    color: #C6A05E;
}}

#systemMetricCard {{
    background: #151A1F;
    border: 1px solid #282F36;
    border-radius: 10px;
    min-width: 125px;
}}

#systemMetricCard:hover {{
    background: #181D22;
    border-color: #40343A;
}}

#systemMetricTitle {{
    background: transparent;
    border: 0;
    color: #AAAEB4;
    font-size: 9px;
    font-weight: 650;
}}

#systemMetricValue {{
    background: transparent;
    border: 0;
    color: #F4F0F2;
    font-size: 15px;
    font-weight: 720;
}}

#systemMetricProgress {{
    background: #242A30;
    border: 0;
    border-radius: 2px;
    min-height: 4px;
    max-height: 4px;
}}

#systemMetricProgress::chunk {{
    background: #D94C63;
    border-radius: 2px;
}}

#systemMetricCard[metricTone="gpu"] #systemMetricProgress::chunk {{
    background: #65B978;
}}

#systemMetricCard[metricTone="ram"] #systemMetricProgress::chunk {{
    background: #D68A35;
}}

#systemMetricCard[metricTone="vram"] #systemMetricProgress::chunk {{
    background: #9A58D2;
}}

#systemMetricCard[metricTone="network"] #systemMetricProgress::chunk {{
    background: #48AFC0;
}}

#systemMetricCard[metricTone="disk"] #systemMetricProgress::chunk {{
    background: #4F8CC9;
}}

#systemMetricSparkline {{
    background: transparent;
    border: 0;
    color: #D94C63;
    font-family: 'Cascadia Code';
    font-size: 16px;
}}

#systemMetricCard[metricTone="gpu"] #systemMetricSparkline {{
    color: #65B978;
}}

#systemMetricCard[metricTone="ram"] #systemMetricSparkline {{
    color: #D68A35;
}}

#systemMetricCard[metricTone="vram"] #systemMetricSparkline {{
    color: #9A58D2;
}}

#systemMetricCard[metricTone="network"] #systemMetricSparkline {{
    color: #48AFC0;
}}

#systemMetricCard[metricTone="disk"] #systemMetricSparkline {{
    color: #4F8CC9;
}}

#systemMetricFooter {{
    background: #12171C;
    border: 1px solid #252C33;
    border-radius: 7px;
    padding: 5px 7px;
    color: #7EABB3;
    font-size: 8px;
}}


                /* =========================================
                   — SISTEMA FASE 3
                   ========================================= */

                #systemLowerRow {{
                    background: transparent;
                    border: 0;
                }}

                #systemModelCard,
                #systemStorageCard {{
                    background: #11161B;
                    border: 1px solid #282F36;
                    border-radius: 13px;
                }}

                #systemModelCard #dashboardCardTitle,
                #systemStorageCard #dashboardCardTitle {{
                    color: #F0ECEE;
                    font-size: 13px;
                    font-weight: 700;
                }}

                #systemModelStatus {{
                    background: #17201C;
                    border: 1px solid #294838;
                    border-radius: 8px;
                    padding: 7px 9px;
                    color: #72C99D;
                    font-size: 9px;
                    font-weight: 650;
                }}

                #systemModelStatus[state="pending"] {{
                    background: #1B1C1C;
                    border-color: #4E432D;
                    color: #C5A05D;
                }}

                #systemModelStatus[state="error"] {{
                    background: #21171B;
                    border-color: #5C3039;
                    color: #E67386;
                }}

                #systemModelStatus[state="unavailable"] {{
                    background: #15191D;
                    border-color: #252B31;
                    color: #707880;
                }}

                #systemModelRow {{
                    background: #151A1F;
                    border: 1px solid #232A31;
                    border-radius: 8px;
                }}

                #systemModelRow #dashboardMetricLabel {{
                    background: transparent;
                    border: 0;
                    padding: 7px 9px;
                    color: #858D96;
                    font-size: 9px;
                    font-weight: 600;
                }}

                #systemModelRow #dashboardMetricValue {{
                    background: transparent;
                    border: 0;
                    padding: 7px 9px;
                    color: #ECE8EA;
                    font-size: 9px;
                    font-weight: 650;
                }}

                #systemStorageMetric {{
                    background: #151A1F;
                    border: 1px solid #232A31;
                    border-radius: 9px;
                }}

                #systemStorageMetricLabel {{
                    background: transparent;
                    border: 0;
                    color: #A5AAB0;
                    font-size: 9px;
                    font-weight: 650;
                }}

                #systemStorageMetricValue {{
                    background: transparent;
                    border: 0;
                    color: #F1EDEF;
                    font-size: 10px;
                    font-weight: 700;
                }}

                #systemStorageProgress {{
                    background: #242A30;
                    border: 0;
                    border-radius: 2px;
                    min-height: 5px;
                    max-height: 5px;
                }}

                #systemStorageProgress::chunk {{
                    background: #D94C63;
                    border-radius: 2px;
                }}

                #systemStorageMetric[resource="ram"]
                #systemStorageProgress::chunk {{
                    background: #D68A35;
                }}

                #systemStorageMetric[resource="vram"]
                #systemStorageProgress::chunk {{
                    background: #9A58D2;
                }}

                #systemStorageHint {{
                    background: #14191E;
                    border: 1px solid #252C33;
                    border-radius: 8px;
                    padding: 7px 9px;
                    color: #707881;
                    font-size: 8px;
                }}


/* Áudio, ações e alertas do Sistema */

#systemAudioCard,
#systemActionsCard,
#systemAlertsCard {{
    background: #11161B;
    border: 1px solid #282F36;
    border-radius: 13px;
}}

#systemAudioCard #dashboardCardTitle,
#systemActionsCard #dashboardCardTitle,
#systemAlertsCard #dashboardCardTitle {{
    color: #F0ECEE;
    font-size: 13px;
    font-weight: 700;
}}

#systemAudioStatus {{
    background: #171C21;
    border: 1px solid #2B3239;
    border-radius: 8px;
    padding: 7px 9px;
    color: #858D96;
    font-size: 9px;
    font-weight: 650;
}}

#systemAudioStatus[state="ok"] {{
    background: #17201C;
    border-color: #294838;
    color: #72C99D;
}}

#systemAudioStatus[state="pending"] {{
    background: #1B1C1C;
    border-color: #4E432D;
    color: #C5A05D;
}}

#systemAudioStatus[state="error"] {{
    background: #21171B;
    border-color: #5C3039;
    color: #E67386;
}}

#systemAudioStatus[state="unavailable"] {{
    background: #15191D;
    border-color: #252B31;
    color: #707880;
}}

#systemAudioRow {{
    background: #151A1F;
    border: 1px solid #232A31;
    border-radius: 8px;
}}

#systemAudioRow #dashboardMetricLabel {{
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #858D96;
    font-size: 8px;
    font-weight: 600;
}}

#systemAudioRow #dashboardMetricValue {{
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #ECE8EA;
    font-size: 9px;
    font-weight: 650;
}}

#systemAudioLevelHeader {{
    background: transparent;
    border: 0;
}}

#systemAudioLevelLabel {{
    background: transparent;
    border: 0;
    color: #858D96;
    font-size: 8px;
    font-weight: 600;
}}

#systemAudioLevelValue {{
    background: transparent;
    border: 0;
    color: #F0ECEE;
    font-size: 9px;
    font-weight: 700;
}}

#systemAudioLevel {{
    background: #242A30;
    border: 0;
    border-radius: 2px;
    min-height: 5px;
    max-height: 5px;
}}

#systemAudioLevel::chunk {{
    background: #68C79A;
    border-radius: 2px;
}}

QPushButton[systemQuickAction="true"] {{
    background: #151A1F;
    border: 1px solid #292F36;
    border-radius: 9px;
    min-height: 34px;
    padding: 7px 10px;
    text-align: left;
    color: #C7C3C6;
    font-size: 9px;
    font-weight: 600;
}}

QPushButton[systemQuickAction="true"]:hover {{
    background: #241A1F;
    border-color: #713541;
    color: #FFF3F5;
}}

QPushButton[systemQuickAction="true"]:pressed {{
    background: #2D1C22;
    border-color: #A54355;
    color: #FF7588;
}}

#systemActionsHint {{
    background: #14191E;
    border: 1px solid #252C33;
    border-radius: 8px;
    padding: 7px 9px;
    color: #707881;
    font-size: 8px;
}}

#systemAlertStatus {{
    background: #171C21;
    border: 1px solid #2B3239;
    border-radius: 8px;
    padding: 8px 9px;
    color: #858D96;
    font-size: 9px;
    font-weight: 650;
}}

#systemAlertStatus[state="ok"] {{
    background: #17201C;
    border-color: #294838;
    color: #72C99D;
}}

#systemAlertStatus[state="warning"] {{
    background: #201C16;
    border-color: #59462A;
    color: #D1A660;
}}

#systemAlertItem {{
    background: #151A1F;
    border: 1px solid #252C33;
    border-radius: 8px;
    padding: 7px 9px;
    color: #A8AEB4;
    font-size: 8px;
}}

#systemAlertItem[kind="warning"] {{
    background: #1E1A16;
    border-color: #4F402B;
    color: #C9A15E;
}}

/* =========================================
   — SISTEMA FASE 5 / RIGHT RAIL
   ========================================= */

#systemWorkbench {{
    background: transparent;
    border: 0;
}}

#systemMainColumn,
#systemRightRail {{
    background: transparent;
    border: 0;
}}

#systemLaylayCard {{
    background: #12161B;
    border: 1px solid #60313B;
    border-radius: 14px;
}}

#systemLaylayCard #dashboardCardTitle {{
    color: #F4F0F2;
    font-size: 14px;
    font-weight: 720;
}}

#systemLaylayCard #dashboardCardHint {{
    background: #2A1A20;
    border: 1px solid #55303A;
    border-radius: 7px;
    padding: 3px 6px;
    color: #E96379;
    font-size: 8px;
    font-weight: 700;
}}

#systemLaylayStatus {{
    background: #17201C;
    border: 1px solid #315442;
    border-radius: 9px;
    padding: 8px 9px;
    color: #78CFA4;
    font-size: 9px;
    font-weight: 700;
}}

#systemLaylayStatus[state="partial"] {{
    background: #201C16;
    border-color: #59462A;
    color: #D1A660;
}}

#systemLaylayStatus[state="unavailable"] {{
    background: #17191C;
    border-color: #292F36;
    color: #747C84;
}}

#systemLaylayRow {{
    background: #171C21;
    border: 1px solid #292F36;
    border-radius: 8px;
}}

#systemLaylayRow #dashboardMetricLabel {{
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #818992;
    font-size: 8px;
    font-weight: 600;
}}

#systemLaylayRow #dashboardMetricValue {{
    background: transparent;
    border: 0;
    padding: 6px 8px;
    color: #ECE8EA;
    font-size: 9px;
    font-weight: 650;
}}

#systemLaylayPulse {{
    background: #181D22;
    border: 1px solid #2B3239;
    border-radius: 9px;
    padding: 7px 9px;
    color: #9BA2A9;
    font-size: 8px;
}}

#systemRightRail #systemActionsCard,
#systemRightRail #systemAlertsCard {{
    background: #12171C;
    border-color: #292F36;
}}

#systemRightRail QPushButton[systemQuickAction="true"] {{
    min-height: 31px;
    padding: 6px 9px;
}}

#systemRightRail #systemAlertItem {{
    padding: 6px 8px;
}}

#systemMainColumn #systemAudioCard {{
    min-height: 170px;
}}

/* =========================================
   — SISTEMA FASE 6 / LEGIBILIDADE
   ========================================= */

#systemHeroTitle {{
    font-size: 17px;
    font-weight: 760;
    color: #F3EFF1;
}}

#systemHeroDescription {{
    font-size: 10px;
    color: #A7ADB4;
}}

#systemUpdated {{
    font-size: 10px;
    color: #8A919A;
}}

#systemSectionCard #dashboardCardTitle,
#systemModelCard #dashboardCardTitle,
#systemStorageCard #dashboardCardTitle,
#systemAudioCard #dashboardCardTitle,
#systemLaylayCard #dashboardCardTitle,
#systemActionsCard #dashboardCardTitle,
#systemAlertsCard #dashboardCardTitle {{
    font-size: 14px;
    font-weight: 740;
    color: #F3EFF1;
}}

#systemSectionCard #dashboardCardHint,
#systemModelCard #dashboardCardHint,
#systemStorageCard #dashboardCardHint,
#systemAudioCard #dashboardCardHint,
#systemLaylayCard #dashboardCardHint,
#systemActionsCard #dashboardCardHint,
#systemAlertsCard #dashboardCardHint {{
    font-size: 8px;
    font-weight: 650;
}}

#systemSummaryRow #dashboardMetricLabel {{
    font-size: 9px;
    font-weight: 620;
    color: #9AA1A9;
}}

#systemSummaryRow #dashboardMetricValue {{
    font-size: 10px;
    font-weight: 700;
    color: #F1EDF0;
}}

#systemSummarySensor {{
    font-size: 10px;
    color: #A8AFB6;
    padding-top: 2px;
}}

#systemSummaryState {{
    font-size: 9px;
    line-height: 1.3;
    padding-top: 5px;
    color: #99BCA8;
}}

#systemMetricTitle {{
    font-size: 9px;
    font-weight: 700;
    color: #ADB3BA;
}}

#systemMetricValue {{
    font-size: 15px;
    font-weight: 760;
    color: #FFF8FA;
}}

#systemMetricFooter {{
    font-size: 8px;
    color: #8F97A0;
}}

#systemMetricSparkline {{
    font-size: 9px;
}}

#systemModelStatus,
#systemAudioStatus,
#systemLaylayStatus,
#systemAlertStatus {{
    font-size: 10px;
    font-weight: 700;
}}

#systemModelRow #dashboardMetricLabel,
#systemAudioRow #dashboardMetricLabel,
#systemLaylayRow #dashboardMetricLabel {{
    font-size: 9px;
    font-weight: 620;
    color: #99A0A8;
}}

#systemModelRow #dashboardMetricValue,
#systemAudioRow #dashboardMetricValue,
#systemLaylayRow #dashboardMetricValue {{
    font-size: 10px;
    font-weight: 700;
    color: #F1EDF0;
}}

#systemStorageMetricLabel {{
    font-size: 9px;
    font-weight: 650;
    color: #A7ADB4;
}}

#systemStorageMetricValue {{
    font-size: 10px;
    font-weight: 740;
    color: #FFF8FA;
}}

#systemStorageHint,
#systemActionsHint,
#systemLaylayPulse,
#systemAlertItem {{
    font-size: 9px;
    line-height: 1.35;
}}

#systemAudioLevelLabel {{
    font-size: 9px;
    font-weight: 620;
    color: #A1A8B0;
}}

#systemAudioLevelValue {{
    font-size: 10px;
    font-weight: 720;
    color: #F4F0F2;
}}

QPushButton[systemQuickAction="true"] {{
    min-height: 38px;
    padding: 8px 11px;
    font-size: 10px;
    font-weight: 680;
}}

#systemRightRail #systemLaylayCard,
#systemRightRail #systemActionsCard,
#systemRightRail #systemAlertsCard {{
    border-radius: 15px;
}}

#systemRightRail #systemAlertItem {{
    padding: 8px 9px;
}}

#systemAudioCard,
#systemModelCard,
#systemStorageCard,
#systemLaylayCard,
#systemActionsCard,
#systemAlertsCard,
#systemSectionCard {{
    border-radius: 14px;
}}

/* =========================================
   — SISTEMA RESPONSIVO
   ========================================= */

QScrollArea#systemScroll {{
    background: transparent;
    border: 0;
}}

QScrollArea#systemScroll > QWidget > QWidget {{
    background: transparent;
}}

#systemPageContent {{
    background: transparent;
}}

#systemHero,
#systemSectionCard,
#systemModelCard,
#systemStorageCard,
#systemAudioCard,
#systemLaylayCard,
#systemActionsCard,
#systemAlertsCard {{
    min-height: 0px;
}}

#systemAudioCard,
#systemModelCard,
#systemStorageCard {{
    min-width: 0px;
}}

#systemSummarySensor,
#systemStorageHint,
#systemActionsHint,
#systemLaylayPulse,
#systemAlertItem {{
    padding-top: 4px;
    padding-bottom: 4px;
}}


/* =========================================
   — REFINO VISUAL DA ABA SISTEMA
   ========================================= */

#systemSectionCard[summaryCard="true"] {{
    background: #11161B;
    border: 1px solid #2B3239;
    border-radius: 16px;
}}

#systemSpecRow {{
    background: transparent;
    border: 0;
    border-bottom: 1px solid #252D35;
    padding: 0;
}}

#systemSpecIcon {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #191F25,
        stop:1 #14191E
    );
    border: 1px solid #2D3540;
    border-radius: 8px;
    color: #E7EAEE;
    font-size: 13px;
    font-weight: 800;
}}

#systemSpecTitle {{
    background: transparent;
    border: 0;
    color: #C2C8CF;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}

#systemSpecValue {{
    background: transparent;
    border: 0;
    color: #F6F7FA;
    font-size: 11px;
    font-weight: 760;
    line-height: 1.15em;
}}

#systemSpecDetail {{
    background: transparent;
    border: 0;
    color: #8A939D;
    font-size: 9px;
    font-weight: 650;
    line-height: 1.15em;
}}

#dashboardCardTitle {{
    color: #F4F0F2;
    font-size: 13px;
    font-weight: 780;
    letter-spacing: 0.15px;
}}

#dashboardCardDetail,
#dashboardCardMeta,
#dashboardSectionMeta {{
    color: #7C858F;
    font-size: 9px;
    font-weight: 650;
}}

#dashboardInfoRow,
#dashboardMetricCard,
#dashboardListRow,
#dashboardActionRow {{
    border-radius: 13px;
}}

#dashboardMetricCard {{
    min-height: 116px;
    padding: 2px;
}}

#dashboardMetricLabel,
#dashboardSmallLabel,
#dashboardInfoLabel {{
    color: #AEB4BC;
    font-size: 9px;
    font-weight: 700;
}}

#dashboardMetricValue,
#dashboardSmallValue,
#dashboardInfoValue {{
    color: #F5F7FA;
    font-size: 11px;
    font-weight: 780;
}}

#dashboardMetricSpark,
#dashboardSparkline {{
    font-size: 13px;
    letter-spacing: 0.2px;
}}

#dashboardHint,
#dashboardInfoHint,
#dashboardEmpty {{
    color: #7E8791;
    font-size: 9px;
    font-weight: 620;
}}

#dashboardActionButton,
#dashboardQuickAction,
#dashboardMiniAction {{
    min-height: 48px;
    border-radius: 14px;
    padding: 0 14px;
}}

#dashboardActionButton:hover,
#dashboardQuickAction:hover,
#dashboardMiniAction:hover {{
    border-color: #F05D7A;
    background: rgba(240, 93, 122, 0.10);
}}

#dashboardStatusBadge,
#dashboardLiveBadge {{
    min-height: 24px;
    padding: 0 10px;
    border-radius: 11px;
    font-size: 9px;
    font-weight: 760;
}}

#dashboardScrollArea {{
    background: transparent;
    border: 0;
}}



/* =========================================
   — REFINO DO BLOCO DE DESEMPENHO
   ========================================= */

#systemPerformanceCard {{
    background: #11161C;
    border: 1px solid #2A3138;
    border-radius: 16px;
}}

#dashboardMetricCard {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1A2027,
        stop:1 #151A20
    );
    border: 1px solid #313944;
    border-radius: 12px;
    min-height: 86px;
    padding: 0px;
}}

#dashboardMetricCard:hover {{
    border-color: #434D59;
}}

#dashboardMetricCard[metricKey="cpu"] {{
    border-color: #4A343C;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(255, 95, 120, 0.11),
        stop:1 rgba(255, 95, 120, 0.03)
    );
}}

#dashboardMetricCard[metricKey="ram"] {{
    border-color: #534630;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(255, 170, 36, 0.10),
        stop:1 rgba(255, 170, 36, 0.03)
    );
}}

#dashboardMetricCard[metricKey="gpu"] {{
    border-color: #2E4A39;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(90, 225, 130, 0.10),
        stop:1 rgba(90, 225, 130, 0.03)
    );
}}

#dashboardMetricCard[metricKey="vram"] {{
    border-color: #4A3480;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(178, 101, 255, 0.10),
        stop:1 rgba(178, 101, 255, 0.03)
    );
}}

#dashboardMetricCard[metricKey="disk"] {{
    border-color: #355E8E;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(89, 167, 255, 0.10),
        stop:1 rgba(89, 167, 255, 0.03)
    );
}}

#dashboardMetricCard[metricKey="network"],
#dashboardMetricCard[metricKey="rede"] {{
    border-color: #2E666C;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 rgba(72, 227, 239, 0.10),
        stop:1 rgba(72, 227, 239, 0.03)
    );
}}

#dashboardMetricLabel {{
    background: transparent;
    border: 0;
    color: #F1F4F7;
    font-size: 11px;
    font-weight: 760;
    letter-spacing: 0.1px;
}}

#dashboardMetricValue {{
    background: transparent;
    border: 0;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 820;
}}

#dashboardMetricSpark {{
    background: transparent;
    border: 0;
    color: #C8D0D7;
    font-size: 15px;
    line-height: 1.0em;
}}

#dashboardHint {{
    background: transparent;
    border: 0;
    color: #A5AFB9;
    font-size: 9px;
    font-weight: 650;
}}

#dashboardMetricBar {{
    background: #27303A;
    border: 0;
    border-radius: 2px;
    min-height: 4px;
    max-height: 4px;
}}

#dashboardMetricBar::chunk {{
    border-radius: 2px;
}}

#dashboardMetricBar[metricKey="cpu"]::chunk {{
    background: #FF5B78;
}}

#dashboardMetricBar[metricKey="ram"]::chunk {{
    background: #F2A22A;
}}

#dashboardMetricBar[metricKey="gpu"]::chunk {{
    background: #67D784;
}}

#dashboardMetricBar[metricKey="vram"]::chunk {{
    background: #B46BFF;
}}

#dashboardMetricBar[metricKey="disk"]::chunk {{
    background: #64AEFF;
}}

#dashboardMetricBar[metricKey="network"]::chunk,
#dashboardMetricBar[metricKey="rede"]::chunk {{
    background: #58E6EE;
}}

#systemPerformanceSamples {{
    color: #7B8692;
    font-size: 9px;
    font-weight: 700;
}}

    """

__all__ = ['qss_system_components']
