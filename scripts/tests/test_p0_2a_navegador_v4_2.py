"""Regressões P0.2A v4.2: evento causal e janela Chrome focada."""

from __future__ import annotations

# P0_NAVEGADOR_TESTES_V4_2_20260815

from pathlib import Path
from typing import Any

from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    _executar_aba_anterior,
)
from mente_laylay.integracao.chrome_estado import ChromeEstadoRuntime
from mente_laylay.integracao.chrome_ws_handlers import handle_action


RAIZ = Path(__file__).resolve().parents[1]
BACKGROUND = RAIZ / "extençao_google" / "background.js"


def _fonte() -> str:
    return BACKGROUND.read_text(encoding="utf-8")


def _bloco(fonte: str, inicio: str, fim: str) -> str:
    pos_inicio = fonte.index(inicio)
    pos_fim = fonte.index(fim, pos_inicio)
    return fonte[pos_inicio:pos_fim]


def test_active_tab_canonica_parte_da_ultima_janela_focada() -> None:
    fonte = _fonte()
    bloco = _bloco(fonte, "// P0_NAVEGADOR_JANELA_FOCADA_V4_2_20260815", "function sendToTab")
    assert "chrome.windows.getLastFocused" in bloco
    assert "activeTabInWindow(win.id)" in bloco
    assert "chrome.tabs.query({ active: true, windowId }" in bloco
    assert "currentWindow: true" not in bloco


def test_on_activated_usa_a_identidade_entregue_pelo_proprio_evento() -> None:
    fonte = _fonte()
    bloco = _bloco(
        fonte,
        "chrome.tabs.onActivated.addListener",
        "chrome.tabs.onUpdated.addListener",
    )
    assert "addListener((activeInfo)" in bloco
    assert "activeInfo.tabId" in bloco
    assert "activeInfo.windowId" in bloco
    assert "sendActiveTabInfoById" in bloco
    assert "currentWindow: true" not in bloco


def test_troca_de_janela_focada_tambem_sincroniza_a_aba_ativa() -> None:
    fonte = _fonte()
    assert "chrome.windows.onFocusChanged.addListener((windowId)" in fonte
    assert "sendActiveTabInfoForWindow(windowId)" in fonte
    assert "chrome.windows.WINDOW_ID_NONE" in fonte


def test_on_updated_nao_reconsulta_current_window_para_publicar_metadados() -> None:
    fonte = _fonte()
    bloco = _bloco(
        fonte,
        "chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab)",
        "chrome.tabs.onRemoved.addListener",
    )
    assert "sendActiveTabInfoById(tabId, tab.windowId)" in bloco
    assert "currentWindow: true" not in bloco


def test_get_active_tab_url_reusa_a_leitura_canonica() -> None:
    fonte = _fonte()
    bloco = _bloco(
        fonte,
        'if (cmd.action === "get_active_tab_url")',
        'if (cmd.action === "get_youtube_data")',
    )
    assert "const t = await activeTab();" in bloco
    assert "currentWindow: true" not in bloco
    assert 'type: "ACTIVE_TAB_URL"' in bloco
    assert "windowId:" in bloco


def test_payload_proativo_preserva_identidade_de_janela_e_aba() -> None:
    fonte = _fonte()
    bloco = _bloco(
        fonte,
        "function publishActiveTabInfo",
        "async function sendActiveTabInfo(includeSnapshot",
    )
    assert 'action: "active_tab_changed"' in bloco
    assert "tabId: t.id" in bloco
    assert "windowId:" in bloco
    assert "active: t.active === true" in bloco


def _evento(
    estado: ChromeEstadoRuntime,
    *,
    tab_id: int,
    window_id: int,
    titulo: str,
    url: str,
) -> dict[str, Any]:
    updates = handle_action(
        {
            "action": "active_tab_changed",
            "tabId": tab_id,
            "windowId": window_id,
            "active": True,
            "title": titulo,
            "url": url,
        },
        estado.contexto_handler(),
    )
    estado.aplicar_updates(updates)
    return updates


def test_regressao_real_wikipedia_prime_volta_para_wikipedia() -> None:
    # A extensão pode ter observado uma aba antiga antes do roteiro; isso não
    # pode vencer os eventos causais seguintes.
    estado = ChromeEstadoRuntime()
    _evento(
        estado,
        tab_id=91,
        window_id=1,
        titulo="Tuya Smart Developer Center",
        url="https://auth.tuya.com/",
    )
    _evento(
        estado,
        tab_id=114,
        window_id=7,
        titulo="Wikipédia",
        url="https://pt.wikipedia.org/",
    )
    _evento(
        estado,
        tab_id=115,
        window_id=7,
        titulo="Prime Video",
        url="https://primevideo.com/",
    )

    retrato = estado.snapshot()
    assert retrato["aba_ativa_id"] == 115
    assert retrato["aba_anterior_id"] == 114


class _LeituraEntreJanelas:
    def __init__(self) -> None:
        self.ativo = 115

    def conectado(self) -> bool:
        return True

    def aba_anterior_id(self) -> int:
        return 114

    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        dados = {
            91: ("Tuya Smart Developer Center", "https://auth.tuya.com/", 8),
            114: ("Wikipédia", "https://pt.wikipedia.org/", 7),
            115: ("Prime Video", "https://primevideo.com/", 8),
        }
        titulo, url, window_id = dados[self.ativo]
        return {
            "tabId": self.ativo,
            "windowId": window_id,
            "active": True,
            "title": titulo,
            "url": url,
        }

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return [
            {
                "id": 91, "windowId": 8, "active": self.ativo == 91,
                "title": "Tuya Smart Developer Center",
                "url": "https://auth.tuya.com/", "lastAccessed": 9999,
            },
            {
                "id": 114, "windowId": 7, "active": self.ativo == 114,
                "title": "Wikipédia",
                "url": "https://pt.wikipedia.org/", "lastAccessed": 100,
            },
            {
                "id": 115, "windowId": 8, "active": self.ativo == 115,
                "title": "Prime Video",
                "url": "https://primevideo.com/", "lastAccessed": 500,
            },
        ]


class _OperacoesEntreJanelas:
    def __init__(self, leitura: _LeituraEntreJanelas) -> None:
        self.leitura = leitura
        self.focados: list[int] = []

    def focar_aba(self, tab_id: int) -> bool:
        self.focados.append(tab_id)
        self.leitura.ativo = tab_id
        return True


def test_volta_para_anterior_canonica_pode_atravessar_janelas() -> None:
    leitura = _LeituraEntreJanelas()
    operacoes = _OperacoesEntreJanelas(leitura)
    resultados: list[dict[str, Any]] = []
    falas: list[str] = []

    deps = DependenciasExecutorNavegador(
        marcar_resultado=lambda status, **dados: resultados.append(
            {"status": status, **dados}
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        abrir_url_com_validacao=lambda *_args, **_kwargs: False,
        alvo_preciso_para_aba=lambda valor: str(valor),
        esperar_aba_fechar=lambda *_args, **_kwargs: False,
        esperar_programa_fechar=lambda *_args, **_kwargs: False,
        executar_recursivo=lambda *_args, **_kwargs: False,
    )

    retorno = _executar_aba_anterior(
        {
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": operacoes,
            "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
        },
        deps,
    )

    assert retorno.tratado is True
    # Mesmo com Tuya tendo lastAccessed muito maior na janela atual, a
    # evidência causal deve vencer e restaurar Wikipédia na outra janela.
    assert operacoes.focados == [114]
    assert resultados[-1]["status"] == "aba_anterior_focada"
    assert resultados[-1]["confirmado"] is True
    assert falas == ["Voltei para Wikipédia — pt.wikipedia.org."]
