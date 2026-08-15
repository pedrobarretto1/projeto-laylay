#!/usr/bin/env python3
"""P0.2A v4.2 r2 — identidade causal da aba + janela Chrome realmente focada.

Baseado no teste de caos de 2026-08-15 (teste 2.0), em que:
- ``Volta para a anterior.`` deixou de travar e passou a responder;
- porém voltou para ``Tuya Smart Developer Center`` em vez de ``Wikipédia``.

A v4.1 já provou que o estado Python e o executor conseguem manter/usar
``aba_anterior_id`` corretamente quando recebem eventos corretos. Esta v4.2
corrige a fronteira da extensão Chrome:

1. ``tabs.onActivated`` passa a usar o ``tabId``/``windowId`` do próprio evento,
   em vez de descartá-los e consultar ``currentWindow`` depois.
2. Mudanças de foco entre janelas passam a ser observadas por
   ``windows.onFocusChanged``.
3. A leitura canônica de aba ativa passa a usar a última janela realmente
   focada (``windows.getLastFocused``) e consulta a aba por ``windowId``.
4. ``get_active_tab_url`` reutiliza essa mesma leitura canônica, portanto a
   confirmação de ``focus_tab`` não usa uma noção diferente de janela ativa.
5. ``onUpdated`` só publica metadados da aba se ela pertencer à janela que é a
   última focada, evitando que uma aba ``active`` de uma janela em segundo plano
   sobrescreva o histórico global.

O script altera somente:
- extençao_google/background.js
- mente_laylay/autonomia/executor_navegador.py (aceita histórico causal entre janelas)
- tests/test_p0_2a_navegador_v4.py (migra uma asserção de implementação para o novo contrato)
- tests/test_p0_2a_navegador_v4_2.py (novo)

Ele valida âncoras, cria backup, checa a forma do JavaScript, usa ``node --check``
quando Node estiver disponível, executa as regressões v4/v4.1/v4.2 e restaura
os arquivos automaticamente se alguma validação falhar.

Também localiza a raiz tanto quando executado dentro de ``laylay/`` quanto a
partir da pasta pai que contém ``laylay/``.
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable


MARCADOR = "P0_NAVEGADOR_JANELA_FOCADA_V4_2_20260815"
MARCADOR_TESTE = "P0_NAVEGADOR_TESTES_V4_2_20260815"
MARCADOR_MIGRACAO_V4 = "P0_NAVEGADOR_TESTE_V4_MIGRADO_V4_2_20260815"
MARCADOR_EXECUTOR_V42 = "P0_NAVEGADOR_ANTERIOR_ENTRE_JANELAS_V4_2_20260815"
MARCADOR_V41 = "P0_NAVEGADOR_HISTORICO_CANONICO_V4_1_20260815"

ARQUIVO_JS = Path("extençao_google/background.js")
ARQUIVO_ESTADO = Path("mente_laylay/integracao/chrome_estado.py")
ARQUIVO_EXECUTOR = Path("mente_laylay/autonomia/executor_navegador.py")
ARQUIVO_TESTE = Path("tests/test_p0_2a_navegador_v4_2.py")
TESTE_V4 = Path("tests/test_p0_2a_navegador_v4.py")
TESTE_V41 = Path("tests/test_p0_2a_navegador_v4_1.py")


TESTE_V4_ASSERCAO_ANTIGA = "        self.assertIn('active: true, currentWindow: true', bloco)\n"
TESTE_V4_ASSERCAO_NOVA = f"""        # {MARCADOR_MIGRACAO_V4}
        # A v4 exigia identidade real (tabId/windowId/active). A v4.2 mantém
        # esse contrato, mas a origem passa a ser a leitura canônica da última
        # janela focada, então ``currentWindow`` não pode mais ser obrigatório.
        self.assertIn('const t = await activeTab();', bloco)
        self.assertNotIn('currentWindow: true', bloco)
"""


EXECUTOR_CANONICO_ANTIGO = '''    anterior = next(
        (
            aba for aba in abas
            if _id_aba(aba) == anterior_id_canonico
            and anterior_id_canonico != ativa_id
            and (
                janela_ativa is None
                or aba.get("windowId") == janela_ativa
            )
        ),
        {},
    )
'''

EXECUTOR_CANONICO_NOVO = (
    "    # " + MARCADOR_EXECUTOR_V42 + "\n"
    + '''    # ``aba_anterior_id`` é histórico causal de foco do navegador inteiro.
    # Se a ação anterior focou uma aba existente em outra janela, restringir
    # pelo ``windowId`` atual destrói justamente essa evidência e força o
    # fallback heurístico por ``lastAccessed``. O fallback continua limitado à
    # janela atual; apenas o histórico canônico pode atravessar janelas.
    anterior = next(
        (
            aba for aba in abas
            if _id_aba(aba) == anterior_id_canonico
            and anterior_id_canonico != ativa_id
        ),
        {},
    )
'''
)

ACTIVE_TAB_ANTIGO = '''function activeTab() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => resolve(tabs?.[0] || null));
  });
}
'''

ACTIVE_TAB_NOVO = f'''// {MARCADOR}
// ``currentWindow`` no service worker não é sinônimo de janela visualmente em
// foco. Toda leitura operacional de "aba ativa" parte da última janela focada
// e consulta a aba com um windowId explícito.
function lastFocusedWindow() {{
  return new Promise((resolve) => {{
    chrome.windows.getLastFocused({{}}, (win) => {{
      const error = chrome.runtime.lastError?.message || "";
      resolve(error ? null : (win || null));
    }});
  }});
}}

function tabById(tabId) {{
  return new Promise((resolve) => {{
    if (!Number.isInteger(tabId)) {{
      resolve(null);
      return;
    }}
    chrome.tabs.get(tabId, (tab) => {{
      const error = chrome.runtime.lastError?.message || "";
      resolve(error ? null : (tab || null));
    }});
  }});
}}

function activeTabInWindow(windowId) {{
  return new Promise((resolve) => {{
    if (!Number.isInteger(windowId) || windowId === chrome.windows.WINDOW_ID_NONE) {{
      resolve(null);
      return;
    }}
    chrome.tabs.query({{ active: true, windowId }}, (tabs) => {{
      resolve(tabs?.[0] || null);
    }});
  }});
}}

async function activeTab() {{
  const win = await lastFocusedWindow();
  if (!Number.isInteger(win?.id)) return null;
  return activeTabInWindow(win.id);
}}
'''

GET_ACTIVE_ANTIGO = '''  if (cmd.action === "get_active_tab_url") {
    const requestId = cmd.requestId ?? null;
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const t = tabs && tabs[0] ? tabs[0] : null;
      const url = t?.url || "";
      const title = t?.title || "";
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        // P0_NAVEGADOR_ACTIVE_TAB_PAYLOAD_V4_20260815
        websocket.send(JSON.stringify({
          type: "ACTIVE_TAB_URL",
          requestId,
          url,
          title,
          tabId: Number.isInteger(t?.id) ? t.id : null,
          windowId: Number.isInteger(t?.windowId) ? t.windowId : null,
          active: t?.active === true,
        }));
      }
    });
    return;
  }
'''

GET_ACTIVE_NOVO = '''  if (cmd.action === "get_active_tab_url") {
    const requestId = cmd.requestId ?? null;
    // A confirmação usa a mesma definição de aba ativa do monitor proativo:
    // aba ativa da última janela Chrome focada, nunca ``currentWindow``.
    const t = await activeTab();
    const url = t?.url || "";
    const title = t?.title || "";
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      // P0_NAVEGADOR_ACTIVE_TAB_PAYLOAD_V4_20260815
      websocket.send(JSON.stringify({
        type: "ACTIVE_TAB_URL",
        requestId,
        url,
        title,
        tabId: Number.isInteger(t?.id) ? t.id : null,
        windowId: Number.isInteger(t?.windowId) ? t.windowId : null,
        active: t?.active === true,
      }));
    }
    return;
  }
'''

MONITOR_ANTIGO = '''// --- MONITORAMENTO PROATIVO DA ABA ATIVA ---
function sendActiveTabInfo(includeSnapshot = false) {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const t = tabs && tabs[0] ? tabs[0] : null;
      if (t && t.url && !t.url.startsWith("chrome://") && !t.url.startsWith("edge://")) {
        sendWs({
          action: "active_tab_changed", 
          tabId: t.id,
          url: t.url, 
          title: t.title || "Sem título" 
        });
        if (includeSnapshot && t.id != null) {
          chrome.tabs.sendMessage(t.id, { action: "GET_PAGE_SNAPSHOT" }, (response) => {
            if (!chrome.runtime.lastError && response?.success) {
              sendWs({ type: "PAGE_SNAPSHOT", payload: response.data || {} });
            }
          });
        }
      }
    });
  }
}

chrome.tabs.onActivated.addListener(() => {
  sendActiveTabInfo();
  schedulePlayerDiscovery(80);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.url || changeInfo.title)) {
    sendActiveTabInfo();
  }
  if (
    String(tab?.url || "").includes("youtube.com") &&
    (changeInfo.url || changeInfo.title || changeInfo.audible !== undefined || changeInfo.status === "complete")
  ) {
    schedulePlayerDiscovery(180);
  }
}); 
'''

MONITOR_NOVO = '''// --- MONITORAMENTO PROATIVO DA ABA ATIVA ---
function publishActiveTabInfo(t, includeSnapshot = false) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN) return false;
  if (!t || !Number.isInteger(t.id)) return false;

  const url = String(t.url || "");
  if (!url || url.startsWith("chrome://") || url.startsWith("edge://")) return false;

  sendWs({
    action: "active_tab_changed",
    tabId: t.id,
    windowId: Number.isInteger(t.windowId) ? t.windowId : null,
    active: t.active === true,
    url,
    title: t.title || "Sem título",
  });

  if (includeSnapshot) {
    chrome.tabs.sendMessage(t.id, { action: "GET_PAGE_SNAPSHOT" }, (response) => {
      if (!chrome.runtime.lastError && response?.success) {
        sendWs({ type: "PAGE_SNAPSHOT", payload: response.data || {} });
      }
    });
  }
  return true;
}

async function sendActiveTabInfo(includeSnapshot = false) {
  const t = await activeTab();
  return publishActiveTabInfo(t, includeSnapshot);
}

async function sendActiveTabInfoForWindow(windowId, includeSnapshot = false) {
  const t = await activeTabInWindow(windowId);
  return publishActiveTabInfo(t, includeSnapshot);
}

async function sendActiveTabInfoById(tabId, windowId, includeSnapshot = false) {
  if (!Number.isInteger(tabId) || !Number.isInteger(windowId)) return false;

  // ``tabs.onActivated`` também pode ser disparado por uma ativação
  // programática numa janela que ainda não ganhou foco. Só aceitamos o evento
  // como estado global se ele pertence à última janela focada. Quando a janela
  // ganhar foco, ``windows.onFocusChanged`` fará a sincronização definitiva.
  const win = await lastFocusedWindow();
  if (!Number.isInteger(win?.id) || win.id !== windowId) return false;

  const t = await tabById(tabId);
  if (!t || t.windowId !== windowId || t.active !== true) return false;
  return publishActiveTabInfo(t, includeSnapshot);
}

chrome.tabs.onActivated.addListener((activeInfo) => {
  void sendActiveTabInfoById(activeInfo.tabId, activeInfo.windowId);
  schedulePlayerDiscovery(80);
});

chrome.windows.onFocusChanged.addListener((windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) return;
  void sendActiveTabInfoForWindow(windowId);
  schedulePlayerDiscovery(80);
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (tab.active && (changeInfo.url || changeInfo.title)) {
    void sendActiveTabInfoById(tabId, tab.windowId);
  }
  if (
    String(tab?.url || "").includes("youtube.com") &&
    (changeInfo.url || changeInfo.title || changeInfo.audible !== undefined || changeInfo.status === "complete")
  ) {
    schedulePlayerDiscovery(180);
  }
}); 
'''

TESTE_V42 = f'''"""Regressões P0.2A v4.2: evento causal e janela Chrome focada."""

from __future__ import annotations

# {MARCADOR_TESTE}

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
    bloco = _bloco(fonte, "// {MARCADOR}", "function sendToTab")
    assert "chrome.windows.getLastFocused" in bloco
    assert "activeTabInWindow(win.id)" in bloco
    assert "chrome.tabs.query({{ active: true, windowId }}" in bloco
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
        {{
            "action": "active_tab_changed",
            "tabId": tab_id,
            "windowId": window_id,
            "active": True,
            "title": titulo,
            "url": url,
        }},
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
        dados = {{
            91: ("Tuya Smart Developer Center", "https://auth.tuya.com/", 8),
            114: ("Wikipédia", "https://pt.wikipedia.org/", 7),
            115: ("Prime Video", "https://primevideo.com/", 8),
        }}
        titulo, url, window_id = dados[self.ativo]
        return {{
            "tabId": self.ativo,
            "windowId": window_id,
            "active": True,
            "title": titulo,
            "url": url,
        }}

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return [
            {{
                "id": 91, "windowId": 8, "active": self.ativo == 91,
                "title": "Tuya Smart Developer Center",
                "url": "https://auth.tuya.com/", "lastAccessed": 9999,
            }},
            {{
                "id": 114, "windowId": 7, "active": self.ativo == 114,
                "title": "Wikipédia",
                "url": "https://pt.wikipedia.org/", "lastAccessed": 100,
            }},
            {{
                "id": 115, "windowId": 8, "active": self.ativo == 115,
                "title": "Prime Video",
                "url": "https://primevideo.com/", "lastAccessed": 500,
            }},
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
            {{"status": status, **dados}}
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        abrir_url_com_validacao=lambda *_args, **_kwargs: False,
        alvo_preciso_para_aba=lambda valor: str(valor),
        esperar_aba_fechar=lambda *_args, **_kwargs: False,
        esperar_programa_fechar=lambda *_args, **_kwargs: False,
        executar_recursivo=lambda *_args, **_kwargs: False,
    )

    retorno = _executar_aba_anterior(
        {{
            "_registro_navegador_leitura_runtime": leitura,
            "_registro_navegador_operacoes_runtime": operacoes,
            "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
        }},
        deps,
    )

    assert retorno.tratado is True
    # Mesmo com Tuya tendo lastAccessed muito maior na janela atual, a
    # evidência causal deve vencer e restaurar Wikipédia na outra janela.
    assert operacoes.focados == [114]
    assert resultados[-1]["status"] == "aba_anterior_focada"
    assert resultados[-1]["confirmado"] is True
    assert falas == ["Voltei para Wikipédia — pt.wikipedia.org."]
'''


def localizar_raiz(inicio: Path) -> Path:
    """Encontra a raiz real sem depender do diretório de execução.

    Aceita os dois usos comuns do projeto:
    - PowerShell já dentro de ``.../projeto lay/laylay``;
    - PowerShell em ``.../projeto lay`` com o projeto no filho ``laylay``.

    A pasta do próprio patcher também entra na busca, evitando que ``cwd`` e
    localização do script precisem coincidir.
    """
    origens = [inicio.resolve(), Path(__file__).resolve().parent]
    vistos: set[Path] = set()
    for origem in origens:
        for base in (origem, *origem.parents):
            for raiz in (base, base / "laylay"):
                raiz = raiz.resolve()
                if raiz in vistos:
                    continue
                vistos.add(raiz)
                if (
                    (raiz / "laylay.py").is_file()
                    and (raiz / ARQUIVO_JS).is_file()
                    and (raiz / "tests").is_dir()
                ):
                    return raiz
    raise RuntimeError(
        "Não encontrei a raiz da Laylay. Procurei no diretório atual, na pasta "
        "do patcher, nos pais de ambos e em um filho chamado 'laylay'."
    )


def substituir_unico(texto: str, antigo: str, novo: str, nome: str) -> str:
    quantidade = texto.count(antigo)
    if quantidade != 1:
        raise RuntimeError(
            f"Âncora {nome!r} deveria aparecer exatamente 1 vez, mas apareceu {quantidade}. "
            "Recusei a alteração para não editar uma versão diferente do código."
        )
    return texto.replace(antigo, novo, 1)


def validar_javascript(texto: str) -> None:
    obrigatorios = (
        MARCADOR,
        "chrome.windows.getLastFocused",
        "async function activeTab()",
        "activeTabInWindow(win.id)",
        "chrome.tabs.onActivated.addListener((activeInfo)",
        "sendActiveTabInfoById(activeInfo.tabId, activeInfo.windowId)",
        "chrome.windows.onFocusChanged.addListener((windowId)",
        "sendActiveTabInfoForWindow(windowId)",
        "const t = await activeTab();",
        'type: "ACTIVE_TAB_URL"',
    )
    ausentes = [item for item in obrigatorios if item not in texto]
    if ausentes:
        raise RuntimeError(f"JavaScript gerado perdeu contratos esperados: {ausentes}")

    bloco_ativacao = texto.split(
        "chrome.tabs.onActivated.addListener", 1,
    )[1].split("chrome.tabs.onUpdated.addListener", 1)[0]
    if "currentWindow: true" in bloco_ativacao:
        raise RuntimeError("onActivated ainda depende de currentWindow")

    bloco_get_active = texto.split(
        'if (cmd.action === "get_active_tab_url")', 1,
    )[1].split('if (cmd.action === "get_youtube_data")', 1)[0]
    if "currentWindow: true" in bloco_get_active:
        raise RuntimeError("get_active_tab_url ainda depende de currentWindow")

    # Garantias simples de balanceamento contra edições acidentais do patch.
    if texto.count("{") != texto.count("}"):
        raise RuntimeError("JavaScript ficou com chaves desbalanceadas")
    if texto.count("(") != texto.count(")"):
        raise RuntimeError("JavaScript ficou com parênteses desbalanceados")


def validar_teste_python(texto: str) -> None:
    ast.parse(texto)
    if MARCADOR_TESTE not in texto:
        raise RuntimeError("Marcador da regressão v4.2 ausente")


def validar_executor(texto: str) -> None:
    ast.parse(texto)
    if MARCADOR_EXECUTOR_V42 not in texto:
        raise RuntimeError("Marcador da correção entre janelas ausente no executor")
    inicio = texto.index(MARCADOR_EXECUTOR_V42)
    trecho = texto[inicio:inicio + 1200]
    if 'aba.get("windowId") == janela_ativa' in trecho:
        raise RuntimeError("Histórico canônico ainda está restrito à janela atual")
    # O fallback heurístico deve continuar conservador e preso à janela atual.
    if 'if janela_ativa is not None and aba.get("windowId") != janela_ativa:' not in texto:
        raise RuntimeError("Fallback lastAccessed perdeu a restrição segura de janela")


def migrar_teste_v4(texto: str) -> str:
    if MARCADOR_MIGRACAO_V4 in texto:
        if "self.assertNotIn('currentWindow: true', bloco)" not in texto:
            raise RuntimeError("Teste v4 marcado como migrado, mas perdeu a nova asserção")
        return texto
    quantidade = texto.count(TESTE_V4_ASSERCAO_ANTIGA)
    if quantidade != 1:
        raise RuntimeError(
            "Não encontrei exatamente a asserção antiga do teste v4 que exigia "
            "currentWindow. Recusei alterar um teste com formato inesperado."
        )
    novo = texto.replace(TESTE_V4_ASSERCAO_ANTIGA, TESTE_V4_ASSERCAO_NOVA, 1)
    ast.parse(novo)
    return novo


def validar_teste_v4_migrado(texto: str) -> None:
    ast.parse(texto)
    if MARCADOR_MIGRACAO_V4 not in texto:
        raise RuntimeError("Marcador da migração da regressão v4 ausente")
    if "self.assertIn('const t = await activeTab();', bloco)" not in texto:
        raise RuntimeError("Teste v4 não verifica mais a leitura canônica activeTab")
    if "self.assertNotIn('currentWindow: true', bloco)" not in texto:
        raise RuntimeError("Teste v4 não protege contra regressão para currentWindow")
    for contrato in ("self.assertIn('tabId:', bloco)", "self.assertIn('windowId:', bloco)", "self.assertIn('active:', bloco)"):
        if contrato not in texto:
            raise RuntimeError(f"Teste v4 perdeu contrato de identidade: {contrato}")


def executar(comando: list[str], *, cwd: Path) -> None:
    print("$", " ".join(comando))
    subprocess.run(comando, cwd=cwd, check=True)


def executar_validacoes(raiz: Path) -> None:
    for arquivo in (raiz / ARQUIVO_EXECUTOR, raiz / TESTE_V4, raiz / ARQUIVO_TESTE):
        if arquivo.is_file():
            executar([sys.executable, "-m", "py_compile", str(arquivo)], cwd=raiz)

    node = shutil.which("node")
    if node:
        executar([node, "--check", str(raiz / ARQUIVO_JS)], cwd=raiz)
    else:
        print("ℹ️ Node não encontrado; validação estrutural do JavaScript foi usada.")

    testes: list[str] = []
    for caminho in (TESTE_V4, TESTE_V41, ARQUIVO_TESTE):
        if (raiz / caminho).is_file():
            testes.append(str(caminho))
    if not testes:
        raise RuntimeError("Nenhum teste P0.2A foi encontrado para executar")
    executar([sys.executable, "-m", "pytest", "-q", *testes], cwd=raiz)


def copiar_backup(raiz: Path, arquivos: Iterable[Path], destino: Path) -> None:
    for relativo in arquivos:
        origem = raiz / relativo
        if not origem.exists():
            continue
        alvo = destino / relativo
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, alvo)


def restaurar_backup(raiz: Path, arquivos: Iterable[Path], backup: Path) -> None:
    for relativo in arquivos:
        salvo = backup / relativo
        atual = raiz / relativo
        if salvo.exists():
            atual.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(salvo, atual)
        elif relativo == ARQUIVO_TESTE and atual.exists():
            atual.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="valida âncoras e conteúdo gerado sem escrever arquivos",
    )
    args = parser.parse_args()

    raiz = localizar_raiz(Path.cwd())
    js_path = raiz / ARQUIVO_JS
    estado_path = raiz / ARQUIVO_ESTADO
    executor_path = raiz / ARQUIVO_EXECUTOR
    teste_path = raiz / ARQUIVO_TESTE
    teste_v4_path = raiz / TESTE_V4

    if not teste_v4_path.is_file():
        raise RuntimeError(f"Regressão base ausente: {TESTE_V4}")

    if not estado_path.is_file() or MARCADOR_V41 not in estado_path.read_text(encoding="utf-8"):
        raise RuntimeError(
            "A v4.1 não foi detectada em chrome_estado.py. A v4.2 depende dela e não será aplicada isoladamente."
        )

    original_js = js_path.read_text(encoding="utf-8")
    original_executor = executor_path.read_text(encoding="utf-8")
    original_teste_v4 = teste_v4_path.read_text(encoding="utf-8")
    teste_existente = teste_path.read_text(encoding="utf-8") if teste_path.exists() else ""

    aplicado_js = MARCADOR in original_js
    aplicado_teste = MARCADOR_TESTE in teste_existente
    aplicado_migracao_v4 = MARCADOR_MIGRACAO_V4 in original_teste_v4
    aplicado_executor = MARCADOR_EXECUTOR_V42 in original_executor
    estados = (aplicado_js, aplicado_teste, aplicado_migracao_v4, aplicado_executor)
    if len(set(estados)) != 1:
        raise RuntimeError(
            "Estado parcial da v4.2 detectado (JS/teste v4.2/migração do teste v4 divergentes). "
            "Restaure o backup ou revise antes de continuar."
        )

    if all(estados):
        print("ℹ️ P0.2A v4.2 já está aplicada. Revalidando...")
        validar_javascript(original_js)
        validar_teste_python(teste_existente)
        validar_teste_v4_migrado(original_teste_v4)
        validar_executor(original_executor)
        if not args.dry_run:
            executar_validacoes(raiz)
        print("✅ P0.2A v4.2 já estava aplicada e continua válida.")
        return 0

    novo_js = substituir_unico(
        original_js, ACTIVE_TAB_ANTIGO, ACTIVE_TAB_NOVO, "activeTab/currentWindow",
    )
    novo_js = substituir_unico(
        novo_js, GET_ACTIVE_ANTIGO, GET_ACTIVE_NOVO, "get_active_tab_url",
    )
    novo_js = substituir_unico(
        novo_js, MONITOR_ANTIGO, MONITOR_NOVO, "monitor proativo de abas",
    )

    novo_executor = substituir_unico(
        original_executor,
        EXECUTOR_CANONICO_ANTIGO,
        EXECUTOR_CANONICO_NOVO,
        "aba anterior canônica entre janelas",
    )
    novo_teste_v4 = migrar_teste_v4(original_teste_v4)

    validar_javascript(novo_js)
    validar_executor(novo_executor)
    validar_teste_python(TESTE_V42)
    validar_teste_v4_migrado(novo_teste_v4)

    if args.dry_run:
        print("✅ Dry-run concluído. A v4.2 pode ser aplicada com segurança nesta árvore.")
        print(f"- alteraria: {ARQUIVO_JS}")
        print(f"- alteraria: {ARQUIVO_EXECUTOR}")
        print(f"- migraria:  {TESTE_V4}")
        print(f"- criaria:   {ARQUIVO_TESTE}")
        return 0

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = raiz / "backups" / "p0_2a_navegador_v4_2" / timestamp
    arquivos = (ARQUIVO_JS, ARQUIVO_EXECUTOR, TESTE_V4, ARQUIVO_TESTE)
    copiar_backup(raiz, arquivos, backup)

    try:
        js_path.write_text(novo_js, encoding="utf-8")
        executor_path.write_text(novo_executor, encoding="utf-8")
        teste_v4_path.write_text(novo_teste_v4, encoding="utf-8")
        teste_path.parent.mkdir(parents=True, exist_ok=True)
        teste_path.write_text(TESTE_V42, encoding="utf-8")
        executar_validacoes(raiz)
    except Exception:
        print("❌ Falha durante validação. Restaurando automaticamente o estado anterior...")
        restaurar_backup(raiz, arquivos, backup)
        raise

    print()
    print("✅ P0.2A v4.2 aplicada e validada.")
    print("- histórico canônico pode voltar para aba anterior em outra janela")
    print("- fallback lastAccessed continua limitado à janela atual")
    print("- regressão v4 foi migrada sem perder tabId/windowId/active")
    print("- onActivated usa tabId/windowId causais do evento")
    print("- troca entre janelas é observada por windows.onFocusChanged")
    print("- aba ativa/confirmacao usam a última janela Chrome focada")
    print("- onUpdated não deixa janela em segundo plano corromper o histórico")
    print(f"- backup: {backup}")
    print()
    print("Regressão manual principal:")
    print("  Abre a Wikipédia.")
    print("  Abre o Prime Video.")
    print("  Volta para a anterior.")
    print("Esperado: Wikipédia volta ao foco e a Laylay publica a confirmação normalmente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
