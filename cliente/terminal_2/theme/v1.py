"""Acabamento nativo da interface V1, inspirado na prévia aprovada.

Somente apresentação: as páginas, estados semânticos e controles continuam
pertencendo aos componentes reais. Aplicar após o tema de base.
"""

from .tokens import FONTE_INTERFACE_QSS, PALETA


def _qss_musica() -> str:
    p = PALETA
    return f"""
    #musicPage, #musicPageBody, #musicScroll, #musicInnerStack {{
        background: {p['fundo']}; border: 0;
    }}
    #musicHero {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #201F2D, stop:1 #141920);
        border: 1px solid #393144; border-radius: 20px;
    }}
    #musicQueue, #musicModule, #musicSessionActions, #musicLyrics {{
        background: {p['superficie']}; border: 1px solid {p['borda']};
        border-radius: 16px;
    }}
    #musicPageTitle {{ font-size: 24px; font-weight: 650; }}
    #musicHeroTitle {{ font-size: 26px; font-weight: 650; }}
    #musicHeroSubtitle, #musicPageDescription {{
        color: {p['secundario']}; font-size: 12px;
    }}
    #musicModuleTitle {{ font-size: 14px; font-weight: 650; }}
    #musicNowBadge {{ color: #C8B6FF; background: transparent; border: 0; }}
    #musicQueueItem {{
        background: transparent; border: 1px solid transparent; border-radius: 10px;
    }}
    #musicQueueItem:hover {{ background: #1D2230; border-color: #353342; }}
    #musicQueueText {{ color: {p['texto']}; font-size: 12px; }}
    #musicQueueDetail, #musicQueueDuration, #musicModuleHint {{
        color: {p['secundario']}; font-size: 11px;
    }}
    #musicPreset {{
        background: {p['superficie']}; border: 1px solid {p['borda']};
        border-radius: 13px;
    }}
    #musicPreset[activePlaylist="true"] {{
        background: #211E30; border-color: #77609F;
    }}
    #musicPresetBody:hover {{ background: #202331; border-radius: 12px; }}
    #musicPresetPlay:hover, #musicPresetPlay:focus {{
        background: #29243B; border: 1px solid {p['violeta']};
    }}
    #musicPrimaryControl {{
        background: #B39AF1; border: 1px solid #C8B6FF;
        border-radius: 24px; color: #201A30;
    }}
    #musicPrimaryControl:hover {{ background: #C4AEFF; border-color: #D9CAFF; }}
    #musicPrimaryControl:pressed {{ background: #9D7CDB; border-color: #C8B6FF; }}
    #musicTransportControl {{
        background: #202431; border: 1px solid #343342; border-radius: 18px;
    }}
    #musicTransportControl:hover {{ background: #2C283D; border-color: #77609F; }}
    #musicHeaderButton:focus, #musicTransportControl:focus,
    #musicPrimaryControl:focus {{ border-color: {p['ciano']}; }}
    #musicPrimaryControl:disabled, #musicTransportControl:disabled {{
        background: #20232C; border-color: #30333C; color: #747B87;
    }}
    #musicHeroProgress::chunk, #musicVolumeSlider::sub-page:horizontal {{
        background: {p['violeta']}; border-radius: 2px;
    }}
    #musicVolumeSlider::handle:horizontal {{
        background: #D7C8FF; border: 1px solid #BDA6FF; border-radius: 6px;
    }}
    """


def _qss_sistema() -> str:
    p = PALETA
    return f"""
    #systemSectionCard, #systemPerformanceCard, #systemModelCard,
    #systemStorageCard, #systemAudioCard, #systemModulesCard,
    #systemActionsCard, #systemEventsCard, #systemLaylayCard,
    #systemRailActionsCard, #systemAlertsCard,
    #systemRightRail #systemLaylayCard, #systemRightRail #systemActionsCard,
    #systemRightRail #systemAlertsCard {{
        background: {p['superficie']}; border: 1px solid {p['borda']};
        border-radius: 16px;
    }}
    #systemSectionCard[summaryCard="true"] {{
        background: {p['superficie']}; border-color: #353343; border-radius: 16px;
    }}
    #systemHeroTitle {{ color: {p['texto']}; font-size: 24px; }}
    #systemHeroDescription, #systemSpecValue {{ font-size: 12px; }}
    #systemModelRow #dashboardMetricLabel,
    #systemAudioRow #dashboardMetricLabel,
    #systemLaylayRow #dashboardMetricLabel {{ font-size: 11px; }}
    #systemModelRow #dashboardMetricValue,
    #systemAudioRow #dashboardMetricValue,
    #systemLaylayRow #dashboardMetricValue {{ font-size: 12px; }}
    #systemLaylayCard #dashboardCardHint {{
        color: #C8B6FF; background: #242031; border-color: #4E3D67;
    }}
    QPushButton[systemQuickAction="true"]:hover,
    #systemRightRail QPushButton[systemQuickAction="true"]:hover,
    #dashboardActionButton:hover, #dashboardQuickAction:hover,
    #dashboardMiniAction:hover {{
        background: #262136; border-color: #8971B8; color: {p['texto']};
    }}
    QPushButton[systemQuickAction="true"]:pressed {{
        background: #332846; border-color: #B59AEF; color: #E5D9FF;
    }}
    #systemStorageProgress::chunk {{ background: {p['violeta']}; }}
    """


def _qss_configuracoes() -> str:
    p = PALETA
    return f"""
    #settingsPage #pageTitle {{ font-size: 25px; font-weight: 650; }}
    #settingsPage #pageDescription, #settingsPage #fieldLabel,
    #settingsPage #keyState, #settingsPage #settingsProfileTitle {{ font-size: 12px; }}
    #settingsPage #eyebrow {{ color: #BAA5ED; }}
    #settingsPage #sectionTitle {{ font-size: 16px; }}
    #settingsPage QPushButton[provider="true"] {{
        background: {p['superficie']}; border-color: {p['borda']};
        border-radius: 13px; font-size: 13px;
    }}
    #settingsPage QPushButton[provider="true"]:checked {{
        background: #242033; border-color: #8B72B8; color: #D6C5FF;
    }}
    #settingsPage QPushButton[provider="true"]:focus,
    #settingsPage #settingsField:focus {{ border-color: {p['ciano']}; }}
    #settingsPage #settingsField {{
        border-radius: 11px; font-size: 13px; selection-background-color: #59477B;
    }}
    #settingsPage #primaryButton {{
        background: #AA8BE9; border: 1px solid #C2A8FF;
        color: #191323; border-radius: 11px; font-size: 13px;
    }}
    #settingsPage #primaryButton:hover {{ background: #BCA0FF; }}
    #settingsPage #primaryButton:focus {{ border-color: {p['ciano']}; }}
    #settingsPage #primaryButton:disabled {{
        background: #282430; border-color: #3A3347; color: #888191;
    }}
    #settingsPage #settingsNote, #settingsPage #settingsProfileCard {{
        background: {p['superficie']}; border-color: {p['borda']}; border-radius: 15px;
    }}
    #settingsPage #settingsNote, #settingsPage #settingsBanner {{ font-size: 12px; }}
    #settingsPage QCheckBox::indicator:checked {{
        background: {p['violeta']}; border-color: #BEA6FF;
    }}
    """


def qss_pagina_v1(nome: str) -> str:
    """Override opcional para páginas ou componentes com stylesheet local."""
    pagina = nome.strip().casefold()
    if pagina in {"musica", "música", "music"}:
        return _qss_musica()
    if pagina in {"sistema", "system"}:
        return _qss_sistema()
    if pagina in {"configuracoes", "configurações", "settings"}:
        return _qss_configuracoes()
    if pagina in {"memoria", "memória", "memory", "automacao", "automação", "automation"}:
        return """
        #memoryEntry, #memoryRailCard, #memoryPrivacyCard,
        #automationDevicesCard, #automationRoutinesCard, #automationSummaryCard,
        #automationContextCard, #automationSafetyCard {
            background: #141920; border: 1px solid #252C35; border-radius: 16px;
        }
        #automationHeroEyebrow { color: #BAA5ED; }
        #automationPowerButton:hover, #automationRefreshButton:hover {
            background: #272237; border-color: #8B72B8;
        }
        #automationPowerButton:focus, #automationRefreshButton:focus,
        #automationRoutineRow:focus { border-color: #66BBD0; }
        """
    return ""


def qss_interface_v1() -> str:
    """Acabamento final do shell e páginas, sem criar estados ou ações."""
    p = PALETA
    return f"""
    /* LAYLAY — INTERFACE V1.0 */
    * {{ font-family: {FONTE_INTERFACE_QSS}; selection-background-color: #59477B; }}
    #root, #mainSurface {{ background: {p['fundo']}; color: {p['texto']}; }}
    #sidebar {{
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 #171923, stop:0.45 #10141A, stop:1 #10141A);
        border-right: 1px solid {p['borda']};
    }}
    #sidebarBrandBar {{ border-bottom: 1px solid #252733; }}
    #brand {{ color: #F1EDF9; font-size: 22px; font-weight: 650; }}
    #brandCaption, #profileVersion {{ color: #939AA8; font-size: 10px; }}
    #sideSection, #eyebrow {{ color: #939BAA; font-size: 10px; }}
    QPushButton[nav="true"] {{
        background: transparent; border: 1px solid transparent;
        border-left: 3px solid transparent; border-radius: 11px;
        padding: 11px 12px; color: #ACB3C2; font-size: 13px; font-weight: 500;
    }}
    QPushButton[nav="true"]:hover {{ background: #1F2130; color: #EFEAF9; }}
    QPushButton[nav="true"]:checked {{
        background: #252135; border: 1px solid #353046;
        border-left: 3px solid #AD92FF; color: #D5C4FF;
    }}
    QPushButton[nav="true"]:pressed {{ background: #2F2840; }}
    #navIndicator {{ background: {p['violeta']}; }}
    #conversationRow[active="true"] {{ background: #242033; }}
    #conversationSearch:focus {{ border-color: {p['ciano']}; }}
    #archivedConversationsButton:checked {{
        background: #282138; border-color: #73608F; color: #C8B6FF;
    }}
    #conversationItem {{ font-size: 12px; }}
    #conversationSection, #conversationEmpty {{ color: #929AA8; font-size: 10px; }}
    #topbar {{
        background: #10131A; border-bottom: 1px solid #252733; min-height: 62px;
    }}
    #headerTitle {{ color: #C6CCD5; font-size: 13px; font-weight: 550; }}
    #sidebarProfile {{ background: #171A23; border: 1px solid #30303E; border-radius: 15px; }}
    #profileName {{ color: #E6E4EE; font-size: 12px; }}
    #profileHeart {{ color: #BFA3ED; }}
    #statusChip, #modeSwitch {{
        background: #171B24; border: 1px solid #30313E; border-radius: 11px;
    }}
    QPushButton[segment="true"]:checked {{ background: #30273F; color: #D9C8FF; }}
    #chatSurface {{ background: transparent; border: 0; }}
    #chatHeader {{ background: transparent; border: 0; }}
    #chatHeader[conversationMode="true"] {{ border-bottom: 1px solid #292C36; }}
    #chatGreeting {{ color: #F3EFFB; font-size: 27px; font-weight: 550; }}
    #chatGreetingSub {{ color: #ABB1C1; font-size: 12px; }}
    #messageLaylay {{
        background: #191D27; border: 1px solid #2C303C; border-radius: 18px;
    }}
    #messageUser {{
        background: #2B2340; border: 1px solid #4A3B63; border-radius: 18px;
    }}
    #messageText {{ color: #EFEDF7; font-size: 14px; }}
    #messageMeta, #messageTime, #messageTime[owner="user"] {{ color: #B0A8BE; font-size: 10px; }}
    #messageStatus {{ color: #A0A8B8; font-size: 10px; }}
    #messageStatus[delivery="pending"] {{ color: #C0ACEE; }}
    #messageStatus[delivery="failed"] {{ color: {p['erro']}; }}
    #composer {{
        background: #191C26; border: 1px solid #494054; border-radius: 20px;
    }}
    #composerEdit {{
        background: transparent; border: 1px solid transparent;
        color: #F0EDF7; border-radius: 12px; padding: 7px 10px; font-size: 14px;
    }}
    #composerEdit:focus {{ background: #1C1F2A; border-color: #73608F; }}
    #composerHint {{ color: #9A9FAF; font-size: 10px; }}
    #composerMic {{ background: #2A233C; border: 1px solid #776091; border-radius: 23px; }}
    #composerMic:hover {{ background: #3B2D50; border-color: #AD92DD; }}
    #composerMic:pressed {{ background: #4D3768; }}
    #sendButton {{ background: #AC90ED; border: 1px solid #C0A7FB; border-radius: 21px; }}
    #sendButton:hover {{ background: #C3A9FF; border-color: #D2BEFF; }}
    #sendButton:pressed {{ background: #9372D1; border-color: #AD92DD; }}
    #sendButton:disabled {{ background: #252331; border-color: #393242; }}
    #dashboardCard, #lazyCard {{
        background: {p['superficie']}; border: 1px solid {p['borda']}; border-radius: 16px;
    }}
    #dashboardCardTitle {{ font-size: 14px; }}
    #dashboardCardDetail, #dashboardCardMeta, #dashboardHint {{ color: #9BA5B3; font-size: 10px; }}
    #inspectorShell {{ background: #11151C; border-left: 1px solid #292C36; }}
    #lazyDot {{ color: {p['violeta']}; }}
    #v1PresentationControls {{
        background: #171A24; border: 1px solid #34303F; border-radius: 12px;
    }}
    QToolButton[presentationMode] {{
        background: transparent; border: 1px solid transparent;
        border-radius: 8px; color: #ADA5BD; min-height: 26px; min-width: 30px;
    }}
    QToolButton[presentationMode]:hover {{ background: #2D253D; color: #E5D8FF; }}
    QToolButton[presentationMode]:checked {{
        background: #382D4C; border-color: #786093; color: #E5D8FF;
    }}
    #v1Brand {{ color: #CDB9FF; font-size: 16px; font-weight: 650; }}
    #v1MascotHero {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #252233, stop:1 #181C25);
        border: 1px solid #403449; border-radius: 20px;
    }}
    #v1Island {{
        background: #1A1B26; border: 1px solid #51415F; border-radius: 23px;
    }}
    #v1IslandTitle {{ color: #EFE9FA; background: transparent; font-size: 13px; font-weight: 650; }}
    #v1IslandStatus {{ color: #B3ACC2; background: transparent; font-size: 11px; }}
    QPushButton:focus, QToolButton:focus, QTextEdit:focus, QLineEdit:focus,
    QComboBox:focus, QCheckBox:focus {{ border: 1px solid {p['ciano']}; outline: 0; }}
    QToolTip {{ background: #242332; color: #F0EDF7; border: 1px solid #635076; padding: 6px; }}
    """ + "".join(qss_pagina_v1(nome) for nome in (
        "musica", "sistema", "configuracoes", "memoria",
    ))


__all__ = ["qss_interface_v1", "qss_pagina_v1"]
