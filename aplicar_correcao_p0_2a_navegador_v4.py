#!/usr/bin/env python3
"""P0.2A v4 — aba ativa real do navegador + confirmação de efeito do focus_tab.

Escopo deliberadamente pequeno:
- chrome_ws_transport.py: aba_ativa deixa de consultar get_youtube_data;
- chrome_ws_handlers.py: ACTIVE_TAB_URL preserva identidade da aba;
- chrome_comandos.py: focus_tab exige COMMAND_RESULT, não só entrega no socket;
- extençao_google/background.js: ACTIVE_TAB_URL devolve tabId/windowId/active;
- tests/test_p0_2a_navegador_v4.py: regressões puras para a integração.

O script faz backup em <raiz>/backups/p0_2a_navegador_v4/<timestamp>/,
valida tudo antes/depois da escrita, executa apenas testes unitários focados e
faz rollback automático se qualquer etapa falhar.
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


MARCADOR_TRANSPORTE = "P0_NAVEGADOR_ABA_ATIVA_REAL_V4_20260815"
MARCADOR_HANDLER = "P0_NAVEGADOR_IDENTIDADE_ATIVA_V4_20260815"
MARCADOR_FOCO = "P0_NAVEGADOR_FOCO_CONFIRMADO_V4_20260815"
MARCADOR_EXTENSAO = "P0_NAVEGADOR_ACTIVE_TAB_PAYLOAD_V4_20260815"
MARCADOR_TESTE = "P0_NAVEGADOR_TESTES_V4_20260815"

ARQUIVO_TRANSPORTE = Path("mente_laylay/integracao/chrome_ws_transport.py")
ARQUIVO_HANDLER = Path("mente_laylay/integracao/chrome_ws_handlers.py")
ARQUIVO_COMANDOS = Path("mente_laylay/integracao/chrome_comandos.py")
ARQUIVO_EXTENSAO = Path("extençao_google/background.js")
ARQUIVO_TESTE = Path("tests/test_p0_2a_navegador_v4.py")

ARQUIVOS_PRODUCAO = (
    ARQUIVO_TRANSPORTE,
    ARQUIVO_HANDLER,
    ARQUIVO_COMANDOS,
    ARQUIVO_EXTENSAO,
)


NOVO_SOLICITAR_ABA_ATIVA = '''    def solicitar_aba_ativa(self, timeout_s: float = 4.0) -> Dict[str, Any]:
        # P0_NAVEGADOR_ABA_ATIVA_REAL_V4_20260815
        # Estado geral do navegador não pode depender do seletor de player do
        # YouTube: a aba audível pode estar em segundo plano.
        vazio = {
            "url": "",
            "title": "",
            "tabId": None,
            "windowId": None,
            "active": False,
        }
        if not self.conectado():
            return vazio
        loop = self._obter_loop()
        if loop is None:
            return vazio

        async def _solicitar() -> Dict[str, Any]:
            request_id = self._novo_request_id()
            futuro = asyncio.get_running_loop().create_future()
            with self.pendencias_lock:
                self.pendencias_aba_ativa[request_id] = futuro
            try:
                await self._transmitir(json.dumps({
                    "action": "get_active_tab_url",
                    "requestId": request_id,
                }))
                resposta = await asyncio.wait_for(
                    futuro,
                    timeout=max(0.0, float(timeout_s)),
                )
                if not isinstance(resposta, dict):
                    return vazio
                tab_id = resposta.get("tabId")
                window_id = resposta.get("windowId")
                return {
                    "url": str(resposta.get("url") or ""),
                    "title": str(resposta.get("title") or ""),
                    "tabId": (
                        tab_id
                        if isinstance(tab_id, int) and not isinstance(tab_id, bool)
                        else None
                    ),
                    "windowId": (
                        window_id
                        if isinstance(window_id, int) and not isinstance(window_id, bool)
                        else None
                    ),
                    "active": resposta.get("active") is True,
                }
            except Exception as erro:
                self._registrar_erro("consulta_aba_ativa", erro)
                return vazio
            finally:
                with self.pendencias_lock:
                    self.pendencias_aba_ativa.pop(request_id, None)

        try:
            futuro = asyncio.run_coroutine_threadsafe(_solicitar(), loop)
            return futuro.result(timeout=max(0.0, float(timeout_s)) + 0.5)
        except Exception as erro:
            self._registrar_erro("espera_aba_ativa", erro)
            return vazio

'''


NOVO_HANDLER_ABA_ATIVA = '''def handle_active_tab_url(
    data: Dict[str, Any], pending_active_url_requests: Dict[str, Any],
) -> None:
    # P0_NAVEGADOR_IDENTIDADE_ATIVA_V4_20260815
    rid = str(data.get("requestId") or "")
    tab_id = data.get("tabId")
    window_id = data.get("windowId")
    payload = {
        "url": str(data.get("url") or ""),
        "title": str(data.get("title") or ""),
        "tabId": (
            tab_id
            if isinstance(tab_id, int) and not isinstance(tab_id, bool)
            else None
        ),
        "windowId": (
            window_id
            if isinstance(window_id, int) and not isinstance(window_id, bool)
            else None
        ),
        "active": data.get("active") is True,
    }
    if rid and rid in pending_active_url_requests:
        entry = pending_active_url_requests.get(rid)
        if isinstance(entry, asyncio.Future):
            if not entry.done():
                entry.set_result(dict(payload))
        elif isinstance(entry, dict):
            entry.update(payload)
            _set_event(entry)


'''


BLOCO_CONFIRMACAO_FOCO = '''        # P0_NAVEGADOR_FOCO_CONFIRMADO_V4_20260815
        # focus_tab já devolve COMMAND_RESULT pela extensão. Para mudança de
        # foco, "bytes chegaram ao socket" não é evidência de efeito.
        if acao_msg in _ACOES_CONFIRMAM_EFEITO:
            return bool(
                callable(executar_confirmado)
                and executar_confirmado(msg, timeout_s=3.0)
            )
        if callable(enviar_confirmado):
            return bool(enviar_confirmado(msg, timeout_s=1.5))
'''


TESTE_V4 = r'''"""Regressões P0.2A v4: navegador ativo não é o player do YouTube."""

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
        self.assertIn('active: true, currentWindow: true', bloco)
        self.assertIn('tabId:', bloco)
        self.assertIn('windowId:', bloco)
        self.assertIn('active:', bloco)
        self.assertIn('type: "ACTIVE_TAB_URL"', bloco)


if __name__ == "__main__":
    unittest.main()
'''


def _raiz_valida(candidato: Path) -> bool:
    return all((candidato / relativo).is_file() for relativo in ARQUIVOS_PRODUCAO)


def localizar_raiz(explicita: str | None) -> Path:
    candidatos: list[Path] = []
    if explicita:
        candidatos.append(Path(explicita).expanduser())

    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd()
    candidatos.extend((script_dir, script_dir / "laylay", cwd, cwd / "laylay"))
    candidatos.extend(script_dir.parents)
    candidatos.extend(cwd.parents)

    vistos: set[Path] = set()
    for candidato in candidatos:
        try:
            resolvido = candidato.resolve()
        except OSError:
            continue
        if resolvido in vistos:
            continue
        vistos.add(resolvido)
        if _raiz_valida(resolvido):
            return resolvido
    raise FileNotFoundError(
        "Não encontrei a raiz do projeto. Use --root CAMINHO se necessário."
    )


def ler(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def substituir_entre(
    texto: str,
    inicio: str,
    fim: str,
    novo: str,
    *,
    rotulo: str,
) -> str:
    if texto.count(inicio) != 1:
        raise RuntimeError(
            f"{rotulo}: âncora inicial esperada exatamente 1 vez; "
            f"encontrei {texto.count(inicio)}."
        )
    pos_inicio = texto.index(inicio)
    pos_fim = texto.find(fim, pos_inicio + len(inicio))
    if pos_fim < 0:
        raise RuntimeError(f"{rotulo}: âncora final não encontrada.")
    return texto[:pos_inicio] + novo + texto[pos_fim:]


def substituir_unico(texto: str, antigo: str, novo: str, *, rotulo: str) -> str:
    quantidade = texto.count(antigo)
    if quantidade != 1:
        raise RuntimeError(
            f"{rotulo}: trecho esperado exatamente 1 vez; encontrei {quantidade}."
        )
    return texto.replace(antigo, novo, 1)


def validar_python(texto: str, rotulo: str) -> None:
    try:
        ast.parse(texto, filename=rotulo)
    except SyntaxError as erro:
        raise RuntimeError(f"{rotulo}: Python inválido após correção: {erro}") from erro


def validar_estado_v4(conteudos: dict[Path, str]) -> None:
    transporte = conteudos[ARQUIVO_TRANSPORTE]
    handler = conteudos[ARQUIVO_HANDLER]
    comandos = conteudos[ARQUIVO_COMANDOS]
    extensao = conteudos[ARQUIVO_EXTENSAO]

    if MARCADOR_TRANSPORTE not in transporte:
        raise RuntimeError("marcador v4 ausente no transporte")
    bloco_aba = transporte[
        transporte.index("    def solicitar_aba_ativa"):
        transporte.index("    async def solicitar_conteudo_pagina")
    ]
    if '"action": "get_active_tab_url"' not in bloco_aba:
        raise RuntimeError("aba_ativa ainda não consulta get_active_tab_url")
    if '"action": "get_youtube_data"' in bloco_aba:
        raise RuntimeError("aba_ativa continua acoplada ao get_youtube_data")
    for chave in ('"tabId"', '"windowId"', '"active"'):
        if chave not in bloco_aba:
            raise RuntimeError(f"identidade ativa ausente no transporte: {chave}")

    if MARCADOR_HANDLER not in handler:
        raise RuntimeError("marcador v4 ausente no handler")
    bloco_handler = handler[
        handler.index("def handle_active_tab_url"):
        handler.index("def handle_youtube_data")
    ]
    for chave in ('"tabId"', '"windowId"', '"active"'):
        if chave not in bloco_handler:
            raise RuntimeError(f"handler ACTIVE_TAB_URL perdeu {chave}")

    if '_ACOES_CONFIRMAM_EFEITO = {"focus_tab"}' not in comandos:
        raise RuntimeError("focus_tab não está tipado como ação com confirmação de efeito")
    if MARCADOR_FOCO not in comandos:
        raise RuntimeError("bloco de confirmação forte de focus_tab ausente")
    if 'executar_confirmado(msg, timeout_s=3.0)' not in comandos:
        raise RuntimeError("focus_tab não usa executar_confirmado")

    if MARCADOR_EXTENSAO not in extensao:
        raise RuntimeError("marcador v4 ausente na extensão")
    inicio = extensao.index('if (cmd.action === "get_active_tab_url")')
    fim = extensao.index('if (cmd.action === "get_youtube_data")', inicio)
    bloco_extensao = extensao[inicio:fim]
    if 'active: true, currentWindow: true' not in bloco_extensao:
        raise RuntimeError("extensão deixou de consultar a aba ativa real")
    for chave in ("tabId:", "windowId:", "active:"):
        if chave not in bloco_extensao:
            raise RuntimeError(f"payload ACTIVE_TAB_URL perdeu {chave}")


def preparar_modificacoes(raiz: Path) -> dict[Path, str]:
    atuais = {rel: ler(raiz / rel) for rel in ARQUIVOS_PRODUCAO}

    marcadores = {
        MARCADOR_TRANSPORTE: atuais[ARQUIVO_TRANSPORTE],
        MARCADOR_HANDLER: atuais[ARQUIVO_HANDLER],
        MARCADOR_FOCO: atuais[ARQUIVO_COMANDOS],
        MARCADOR_EXTENSAO: atuais[ARQUIVO_EXTENSAO],
    }
    presentes = [marcador for marcador, texto in marcadores.items() if marcador in texto]
    if presentes:
        if len(presentes) != len(marcadores):
            raise RuntimeError(
                "Estado v4 parcial detectado; não vou completar uma correção pela metade. "
                "Restaure/commit as alterações e rode novamente."
            )
        validar_estado_v4(atuais)
        return atuais

    transporte = atuais[ARQUIVO_TRANSPORTE]
    inicio_transporte = "    def solicitar_aba_ativa(self, timeout_s: float = 4.0) -> Dict[str, Any]:\n"
    fim_transporte = "    async def solicitar_conteudo_pagina(self, timeout_s: float = 15.0) -> Dict[str, Any]:\n"
    bloco_antigo = transporte[
        transporte.index(inicio_transporte):
        transporte.index(fim_transporte)
    ] if inicio_transporte in transporte and fim_transporte in transporte else ""
    if '"action": "get_youtube_data"' not in bloco_antigo:
        raise RuntimeError(
            "chrome_ws_transport.py não corresponde ao pré-v4 esperado: "
            "solicitar_aba_ativa já não usa get_youtube_data."
        )
    transporte = substituir_entre(
        transporte,
        inicio_transporte,
        fim_transporte,
        NOVO_SOLICITAR_ABA_ATIVA,
        rotulo=str(ARQUIVO_TRANSPORTE),
    )

    handler = atuais[ARQUIVO_HANDLER]
    handler = substituir_entre(
        handler,
        "def handle_active_tab_url(data: Dict[str, Any], pending_active_url_requests: Dict[str, Any]) -> None:\n",
        "def handle_youtube_data(data: Dict[str, Any], pending_active_url_requests: Dict[str, Any]) -> None:\n",
        NOVO_HANDLER_ABA_ATIVA,
        rotulo=str(ARQUIVO_HANDLER),
    )

    comandos = atuais[ARQUIVO_COMANDOS]
    comandos = substituir_unico(
        comandos,
        '_ACOES_FIXADAS_NA_ABA = {"click", "type", "press", "scroll", "search_in_page"}\n',
        '_ACOES_FIXADAS_NA_ABA = {"click", "type", "press", "scroll", "search_in_page"}\n'
        '_ACOES_CONFIRMAM_EFEITO = {"focus_tab"}\n',
        rotulo=f"{ARQUIVO_COMANDOS}: contrato de efeito",
    )
    comandos = substituir_unico(
        comandos,
        '        if callable(enviar_confirmado):\n'
        '            return bool(enviar_confirmado(msg, timeout_s=1.5))\n',
        BLOCO_CONFIRMACAO_FOCO,
        rotulo=f"{ARQUIVO_COMANDOS}: envio genérico",
    )

    extensao = atuais[ARQUIVO_EXTENSAO]
    extensao = substituir_unico(
        extensao,
        '        websocket.send(JSON.stringify({ type: "ACTIVE_TAB_URL", requestId, url, title }));\n',
        '        // P0_NAVEGADOR_ACTIVE_TAB_PAYLOAD_V4_20260815\n'
        '        websocket.send(JSON.stringify({\n'
        '          type: "ACTIVE_TAB_URL",\n'
        '          requestId,\n'
        '          url,\n'
        '          title,\n'
        '          tabId: Number.isInteger(t?.id) ? t.id : null,\n'
        '          windowId: Number.isInteger(t?.windowId) ? t.windowId : null,\n'
        '          active: t?.active === true,\n'
        '        }));\n',
        rotulo=f"{ARQUIVO_EXTENSAO}: ACTIVE_TAB_URL",
    )

    novos = {
        ARQUIVO_TRANSPORTE: transporte,
        ARQUIVO_HANDLER: handler,
        ARQUIVO_COMANDOS: comandos,
        ARQUIVO_EXTENSAO: extensao,
    }
    for relativo in (ARQUIVO_TRANSPORTE, ARQUIVO_HANDLER, ARQUIVO_COMANDOS):
        validar_python(novos[relativo], str(relativo))
    validar_python(TESTE_V4, str(ARQUIVO_TESTE))
    validar_estado_v4(novos)
    return novos


def criar_backup(
    raiz: Path,
    relativos: Iterable[Path],
) -> tuple[Path, dict[Path, bool]]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = raiz / "backups" / "p0_2a_navegador_v4" / timestamp
    existia: dict[Path, bool] = {}
    for relativo in relativos:
        origem = raiz / relativo
        existia[relativo] = origem.exists()
        if not origem.exists():
            continue
        alvo = destino / relativo
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, alvo)
    return destino, existia


def restaurar_backup(
    raiz: Path,
    backup: Path,
    relativos: Iterable[Path],
    existia: dict[Path, bool],
) -> None:
    for relativo in relativos:
        alvo = raiz / relativo
        copia = backup / relativo
        if existia.get(relativo):
            if not copia.is_file():
                raise RuntimeError(f"backup ausente para restaurar {relativo}")
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(copia, alvo)
        elif alvo.exists():
            alvo.unlink()


def validar_arquivos_escritos(raiz: Path) -> None:
    conteudos = {rel: ler(raiz / rel) for rel in ARQUIVOS_PRODUCAO}
    validar_estado_v4(conteudos)
    for relativo in (ARQUIVO_TRANSPORTE, ARQUIVO_HANDLER, ARQUIVO_COMANDOS):
        validar_python(conteudos[relativo], str(relativo))
    teste = ler(raiz / ARQUIVO_TESTE)
    validar_python(teste, str(ARQUIVO_TESTE))
    if MARCADOR_TESTE not in teste:
        raise RuntimeError("arquivo de teste v4 escrito sem marcador esperado")


def rodar_testes(raiz: Path) -> None:
    comando = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        ARQUIVO_TESTE.name,
        "-v",
    ]
    print("🧪 Executando regressões focadas P0.2A v4...")
    concluido = subprocess.run(comando, cwd=raiz, check=False)
    if concluido.returncode != 0:
        raise RuntimeError(
            f"Testes focados falharam (código {concluido.returncode}); "
            "as alterações serão revertidas."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="raiz do projeto Laylay")
    args = parser.parse_args()

    raiz = localizar_raiz(args.root)
    print(f"📁 Projeto: {raiz}")

    novos = preparar_modificacoes(raiz)
    ja_aplicado = all(
        marcador in novos[arquivo]
        for marcador, arquivo in (
            (MARCADOR_TRANSPORTE, ARQUIVO_TRANSPORTE),
            (MARCADOR_HANDLER, ARQUIVO_HANDLER),
            (MARCADOR_FOCO, ARQUIVO_COMANDOS),
            (MARCADOR_EXTENSAO, ARQUIVO_EXTENSAO),
        )
    ) and all(
        marcador in ler(raiz / arquivo)
        for marcador, arquivo in (
            (MARCADOR_TRANSPORTE, ARQUIVO_TRANSPORTE),
            (MARCADOR_HANDLER, ARQUIVO_HANDLER),
            (MARCADOR_FOCO, ARQUIVO_COMANDOS),
            (MARCADOR_EXTENSAO, ARQUIVO_EXTENSAO),
        )
    )

    if ja_aplicado:
        teste_path = raiz / ARQUIVO_TESTE
        if not teste_path.is_file() or MARCADOR_TESTE not in ler(teste_path):
            raise RuntimeError(
                "Produção já está em v4, mas o teste v4 está ausente/diferente. "
                "Não vou sobrescrever estado parcial automaticamente."
            )
        validar_arquivos_escritos(raiz)
        rodar_testes(raiz)
        print("✅ P0.2A v4 já estava aplicada e as regressões continuam passando.")
        return 0

    relativos_backup = (*ARQUIVOS_PRODUCAO, ARQUIVO_TESTE)
    backup, existia = criar_backup(raiz, relativos_backup)
    print(f"🛟 Backup: {backup}")

    try:
        for relativo, texto in novos.items():
            caminho = raiz / relativo
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(texto, encoding="utf-8")
        teste_path = raiz / ARQUIVO_TESTE
        teste_path.parent.mkdir(parents=True, exist_ok=True)
        teste_path.write_text(TESTE_V4, encoding="utf-8")

        validar_arquivos_escritos(raiz)
        rodar_testes(raiz)
    except Exception:
        print("↩️ Alterações revertidas a partir do backup.")
        restaurar_backup(raiz, backup, relativos_backup, existia)
        raise

    print("✅ P0.2A v4 aplicada com sucesso.")
    print("   - aba_ativa agora consulta a aba ativa real do Chrome")
    print("   - ACTIVE_TAB_URL preserva tabId/windowId/active")
    print("   - focus_tab exige COMMAND_RESULT da extensão")
    print("   - get_youtube_data continua exclusivo do subsistema de mídia")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as erro:
        print(f"❌ P0.2A v4 não aplicada: {type(erro).__name__}: {erro}")
        raise SystemExit(1)
