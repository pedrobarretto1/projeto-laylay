"""Regressões P0.2A v4: navegador ativo não é o player do YouTube."""

from __future__ import annotations

# P0_NAVEGADOR_TESTES_V4_20260815

import asyncio
import json
import threading
import unittest
from pathlib import Path

from mente_laylay.integracao.chrome_comandos import validar_e_enviar_comando
from mente_laylay.integracao.chrome_ws_handlers import handle_active_tab_url
from mente_laylay.integracao.chrome_ws_transport import ChromeSolicitacoesRuntime


class _LoopEmThread:
    def __init__(self) -> None:
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._rodar, daemon=True)
        self.thread.start()
        pronto = threading.Event()

        def _marcar() -> None:
            pronto.set()

        self.loop.call_soon_threadsafe(_marcar)
        if not pronto.wait(2.0):
            raise RuntimeError("loop de teste não iniciou")

    def _rodar(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def fechar(self) -> None:
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(timeout=2.0)
        if not self.loop.is_running():
            self.loop.close()


class TestP02ANavegadorV4(unittest.TestCase):
    def test_aba_ativa_consulta_chrome_real_e_nao_youtube_background(self) -> None:
        runner = _LoopEmThread()
        runtime = None
        acoes: list[str] = []

        async def transmitir(mensagem: str) -> int:
            nonlocal runtime
            payload = json.loads(mensagem)
            acao = str(payload.get("action") or "")
            acoes.append(acao)
            rid = str(payload.get("requestId") or "")
            futuro = runtime.pendencias_aba_ativa[rid]
            if acao == "get_active_tab_url":
                futuro.set_result({
                    "url": "https://www.primevideo.com/",
                    "title": "Prime Video",
                    "tabId": 42,
                    "windowId": 3,
                    "active": True,
                })
            elif acao == "get_youtube_data":
                # Reproduz exatamente o bug antigo: YouTube audível em background.
                futuro.set_result({
                    "url": "https://www.youtube.com/watch?v=abcdefghijk",
                    "title": "Música",
                    "tabId": 7,
                    "source": "audible_youtube_tab",
                    "playingConfirmed": True,
                    "audibleConfirmed": True,
                })
            return 1

        try:
            runtime = ChromeSolicitacoesRuntime(
                obter_loop=lambda: runner.loop,
                obter_extensoes=lambda: {"extensao-fake"},
                transmitir=transmitir,
                log=lambda _msg: None,
            )
            observado = runtime.solicitar_aba_ativa(timeout_s=1.0)
        finally:
            runner.fechar()

        self.assertEqual(acoes, ["get_active_tab_url"])
        self.assertEqual(observado.get("tabId"), 42)
        self.assertEqual(observado.get("windowId"), 3)
        self.assertTrue(observado.get("active"))
        self.assertEqual(observado.get("title"), "Prime Video")

    def test_handler_active_tab_preserva_identidade_da_aba(self) -> None:
        evento = threading.Event()
        entrada = {"event": evento}
        pendencias = {"req-1": entrada}
        handle_active_tab_url({
            "type": "ACTIVE_TAB_URL",
            "requestId": "req-1",
            "url": "https://pt.wikipedia.org/",
            "title": "Wikipédia",
            "tabId": 55,
            "windowId": 9,
            "active": True,
        }, pendencias)
        self.assertTrue(evento.is_set())
        self.assertEqual(entrada.get("tabId"), 55)
        self.assertEqual(entrada.get("windowId"), 9)
        self.assertTrue(entrada.get("active"))

    def test_focus_tab_exige_command_result_em_vez_de_confirmacao_socket(self) -> None:
        chamadas = {"efeito": 0, "socket": 0}

        def executar_confirmado(msg, timeout_s=0.0):
            chamadas["efeito"] += 1
            self.assertEqual(msg.get("action"), "focus_tab")
            self.assertEqual(msg.get("tabId"), 42)
            self.assertGreaterEqual(float(timeout_s), 3.0)
            return True

        def enviar_confirmado(_msg, timeout_s=0.0):
            chamadas["socket"] += 1
            return True

        contexto = {
            "ALLOWED_ACTIONS": {"focus_tab"},
            "connected_extensions": {"extensao-fake"},
            "ws_loop": object(),
            "broadcast_command": lambda _msg: None,
            "executar_chrome_confirmado": executar_confirmado,
            "enviar_chrome_confirmado": enviar_confirmado,
        }
        ok = validar_e_enviar_comando(
            contexto,
            "focus_tab",
            {"tabId": 42},
        )
        self.assertTrue(ok)
        self.assertEqual(chamadas["efeito"], 1)
        self.assertEqual(chamadas["socket"], 0)

    def test_focus_tab_falha_fechado_quando_nao_ha_confirmacao_de_efeito(self) -> None:
        chamadas = {"socket": 0}

        def enviar_confirmado(_msg, timeout_s=0.0):
            chamadas["socket"] += 1
            return True

        contexto = {
            "ALLOWED_ACTIONS": {"focus_tab"},
            "connected_extensions": {"extensao-fake"},
            "ws_loop": object(),
            "broadcast_command": lambda _msg: None,
            "executar_chrome_confirmado": lambda _msg, timeout_s=0.0: False,
            "enviar_chrome_confirmado": enviar_confirmado,
        }
        ok = validar_e_enviar_comando(contexto, "focus_tab", {"tabId": 42})
        self.assertFalse(ok)
        self.assertEqual(chamadas["socket"], 0)

    def test_extensao_publica_identidade_da_aba_ativa_real(self) -> None:
        raiz = Path(__file__).resolve().parents[1]
        fonte = (raiz / "extençao_google" / "background.js").read_text(
            encoding="utf-8",
        )
        inicio = fonte.index('if (cmd.action === "get_active_tab_url")')
        fim = fonte.index('if (cmd.action === "get_youtube_data")', inicio)
        bloco = fonte[inicio:fim]
        # P0_NAVEGADOR_TESTE_V4_MIGRADO_V4_2_20260815
        # A v4 exigia identidade real (tabId/windowId/active). A v4.2 mantém
        # esse contrato, mas a origem passa a ser a leitura canônica da última
        # janela focada, então ``currentWindow`` não pode mais ser obrigatório.
        self.assertIn('const t = await activeTab();', bloco)
        self.assertNotIn('currentWindow: true', bloco)
        self.assertIn('tabId:', bloco)
        self.assertIn('windowId:', bloco)
        self.assertIn('active:', bloco)
        self.assertIn('type: "ACTIVE_TAB_URL"', bloco)


if __name__ == "__main__":
    unittest.main()
