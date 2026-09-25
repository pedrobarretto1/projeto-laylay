"""Parte modular do tema do Terminal Laylay 3.0."""

from .tokens import PALETA

def qss_tabs_refresh() -> str:
    """Linguagem visual compartilhada pelas páginas funcionais do Terminal."""
    p = PALETA
    return f"""
    /* PÁGINAS FUNCIONAIS */
    #systemPage, #systemPageContent, #automationPage, #automationPageContent,
    #musicPage, #musicPageBody {{
        background: {p["fundo"]};
        border: 0;
    }}

    #systemHero, #automationHero {{
        background: transparent;
        border: 0;
    }}
    #systemHeroTitle, #automationHeroTitle,
    #musicPageTitle {{
        color: {p["texto"]};
        font-size: 22px;
        font-weight: 650;
    }}
    #systemHeroDescription, #automationHeroDescription,
    #musicPageDescription {{
        color: {p["secundario"]};
        font-size: 11px;
    }}
    #systemUpdated, #automationUpdated {{
        color: {p["apagado"]};
        font-size: 9px;
    }}

    #systemSectionCard, #systemPerformanceCard, #systemModelCard,
    #systemStorageCard, #systemAudioCard, #systemModulesCard,
    #systemActionsCard, #systemEventsCard, #systemLaylayCard,
    #systemRailActionsCard, #systemAlertsCard,
    #automationDevicesCard, #automationRoutinesCard, #automationSummaryCard,
    #automationContextCard, #automationSafetyCard,
    #musicModule, #musicQueue, #musicHero {{
        background: {p["superficie"]};
        border: 1px solid #1E252D;
        border-radius: 13px;
    }}

    #systemMetricCard, #systemStorageMetric, #systemModuleRow,
    #automationSummaryMetric, #automationRoutineRow,
    #automationDeviceCard {{
        background: {p["elevada"]};
        border: 1px solid {p["borda"]};
        border-radius: 10px;
    }}

    #automationHeroEyebrow {{
        color: {p["rosa"]};
        font-size: 9px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    #automationRail, #musicSideRail {{
        background: transparent;
        border: 0;
    }}

    #musicHero {{
        border-color: #2A242C;
    }}
    #musicQueue, #musicModule {{
        border-color: #202832;
    }}

    /* CONTROLES COMPARTILHADOS */
    QPushButton[systemQuickAction="true"],
    #automationPowerButton, #automationRefreshButton,
    #musicHeaderButton {{
        background: {p["superficie"]};
        color: {p["secundario"]};
        border: 1px solid {p["borda"]};
        border-radius: 8px;
        min-height: 30px;
        padding: 0 12px;
    }}
    QPushButton[systemQuickAction="true"]:hover,
    #automationPowerButton:hover, #automationRefreshButton:hover,
    #musicHeaderButton:hover {{
        background: {p["hover"]};
        color: {p["texto"]};
        border-color: #4A535D;
    }}
    QPushButton[systemQuickAction="true"]:focus,
    #automationPowerButton:focus, #automationRefreshButton:focus,
    #automationRoutineRow:focus, #musicHeaderButton:focus,
    #musicTransportControl:focus, #musicPrimaryControl:focus {{
        border-color: {p["rosa"]};
    }}
    QPushButton[systemQuickAction="true"]:disabled,
    #automationPowerButton:disabled, #automationRefreshButton:disabled,
    #automationRoutineRow:disabled, #musicHeaderButton:disabled,
    #musicTransportControl:disabled, #musicPrimaryControl:disabled {{
        color: #59616B;
        background: #11161B;
        border-color: #20262D;
    }}

    #automationRoutineRow {{
        text-align: left;
        padding: 9px 11px;
    }}
    #automationRoutineRow:hover {{
        background: {p["hover"]};
        border-color: #4A535D;
    }}

    #musicTransportControl {{
        background: {p["elevada"]};
        border: 1px solid transparent;
        border-radius: 18px;
    }}
    #musicTransportControl:hover {{
        background: {p["hover"]};
        border-color: {p["borda"]};
    }}
    #musicPrimaryControl {{
        background: #251920;
        border: 1px solid #49303A;
        border-radius: 24px;
    }}
    #musicPrimaryControl:hover {{
        background: #332028;
        border-color: {p["rosa"]};
    }}
    """

def qss_product_polish() -> str:
    """Estados de interação e carregamento compartilhados pelo Terminal."""
    p = PALETA
    return f"""
    #lazyPage {{
        background: {p["fundo"]};
        border: 0;
    }}
    #lazyCard {{
        background: {p["superficie"]};
        border: 1px solid #1E252D;
        border-radius: 14px;
    }}
    #lazyDot {{
        color: {p["rosa"]};
        font-size: 9px;
    }}
    #lazyTitle {{
        color: {p["texto"]};
        font-size: 13px;
        font-weight: 650;
    }}
    #lazyText {{
        color: {p["apagado"]};
        font-size: 10px;
    }}
    #lazySkeleton {{
        background: #252C35;
        border: 0;
        border-radius: 4px;
    }}

    QPushButton[nav="true"]:pressed,
    QPushButton[systemQuickAction="true"]:pressed,
    #automationPowerButton:pressed, #automationRefreshButton:pressed,
    #automationRoutineRow:pressed, #musicHeaderButton:pressed,
    #secondaryButton:pressed, #profileAvatarButton:pressed {{
        background: #252C35;
        border-color: #59636D;
    }}

    #musicTransportControl:pressed {{
        background: #2A323C;
        border-color: #59636D;
    }}
    #musicPrimaryControl:pressed {{
        background: #3A232C;
        border-color: #FF7B8E;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #39424C;
        min-height: 30px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #4B5661;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border-color: {p["rosa"]};
    }}
    """

__all__ = ['qss_tabs_refresh', 'qss_product_polish']
