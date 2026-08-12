from __future__ import annotations

import json
from pathlib import Path
import socket
import time

import pytest

from mente_laylay.autonomia.roteador_intencao import executar_intencao
from mente_laylay.integracao.acoes_painel_runtime import (
    comando_tipado_acao_painel,
)
from mente_laylay.integracao.dashboard_terminal import DashboardTerminalRuntime
from mente_laylay.integracao.desktop_bridge import (
    DesktopBridgeRuntime,
    ErroProtocoloDesktop,
    sanitizar_dashboard_estado,
    validar_mensagem_cliente,
)
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


class _Percentual:
    percent = 20.0


class _Psutil:
    @staticmethod
    def cpu_percent(*, interval=None): return 10.0

    @staticmethod
    def virtual_memory(): return _Percentual()

    @staticmethod
    def disk_usage(_raiz): return _Percentual()

    @staticmethod
    def boot_time(): return 500.0


def _playlist_runtime(cache: dict, estado: dict | None = None) -> PlaylistRuntime:
    return PlaylistRuntime(
        state_file="nao_usado.json",
        legacy_file="nao_usado_legado.json",
        cache=cache,
        ultima_playlist_getter=lambda: "",
        playlist_state=estado or {},
    )


def _dashboard(**trocas) -> DashboardTerminalRuntime:
    dados = {
        "configuracao_getter": dict,
        "llm_getter": dict,
        "interacao_getter": dict,
        "memoria_saude_getter": dict,
        "agenda_getter": list,
        "aprendizados_getter": lambda **_kwargs: [],
        "estado_mental_getter": dict,
        "contexto_jogo_getter": dict,
        "capacidade_getter": lambda intent: {
            "disponivel": intent in {
                "MEDIA_CONTROL", "PLAYLIST_PLAY", "TOCAR_PLAYLIST_SHUFFLE",
            },
            "estado": "disponivel",
        },
        "musica_getter": lambda: {"player": {
            "title": "Atual", "state": "playing", "observed_at": 1_000,
            "controls_available": True,
        }, "playlist": "Rock"},
        "psutil_mod": _Psutil,
        "clock": lambda: 1_000.0,
        "log": lambda _texto: None,
    }
    dados.update(trocas)
    return DashboardTerminalRuntime(**dados)


def test_catalogo_publico_nao_para_em_doze_nem_vinte_e_quatro() -> None:
    cache = {
        f"Playlist {indice:02d}": [{
            "titulo": f"Faixa {indice}",
            "url": f"https://youtube.com/watch?v={indice:011d}",
        }]
        for indice in range(30)
    }

    catalogo = _playlist_runtime(cache).catalogo_publico()

    assert len(catalogo) == 30
    assert catalogo[-1]["name"] == "Playlist 29"


def test_fila_publica_comeca_depois_da_faixa_atual_e_nao_expoe_url() -> None:
    cache = {"Rock": [
        {"titulo": "Atual", "canal": "A", "url": "https://youtu.be/abcdefghijk"},
        {"titulo": "Próxima", "canal": "B", "url": "https://youtu.be/lmnopqrstuv"},
        {"titulo": "Depois", "canal": "C", "url": "https://youtu.be/zyxwvutsrqp"},
    ]}
    runtime = _playlist_runtime(cache, {"name": "Rock", "index": 0})

    fila = runtime.fila_publica()

    assert [item["title"] for item in fila] == ["Próxima", "Depois"]
    assert fila[0]["artwork_video_id"] == "lmnopqrstuv"
    assert "url" not in json.dumps(fila)


def test_dashboard_usa_fila_interna_quando_youtube_nao_publica_proximas() -> None:
    runtime = _dashboard(playlist_queue_getter=lambda: [{
        "title": "Próxima interna", "channel": "Canal",
        "artwork_video_id": "abcdefghijk",
    }])

    musica = runtime._musica(1_000.0)

    assert musica["queue_source"] == "laylay_playlist"
    assert musica["queue_freshness"] == "fresh"
    assert musica["queue"][0]["title"] == "Próxima interna"


def test_ponte_preserva_catalogo_e_fila_completos_e_remove_campos_privados() -> None:
    publico = sanitizar_dashboard_estado({
        "generated_at": 1_000,
        "music": {
            "title": "Atual", "state": "playing", "freshness": "fresh",
            "observed_at": 1_000,
            "queue_freshness": "fresh", "queue_observed_at": 1_000,
            "queue_source": "laylay_playlist",
            "queue": [
                {"title": f"Faixa {i}", "url": "segredo"} for i in range(15)
            ],
            "catalog_available": True, "catalog_observed_at": 1_000,
            "catalog": [
                {"name": f"Playlist {i}", "count": i, "items": ["segredo"]}
                for i in range(30)
            ],
        },
    })

    assert len(publico["music"]["queue"]) == 15
    assert len(publico["music"]["catalog"]) == 30
    assert publico["music"]["queue_source"] == "laylay_playlist"
    assert "segredo" not in json.dumps(publico)


def test_controle_tipado_nao_aceita_texto_livre_como_parametro() -> None:
    assert comando_tipado_acao_painel(
        "playlist_play", {"playlist": "Rock"},
    ) == ({
        "intent": "PLAYLIST_PLAY",
        "params": {
            "nome_playlist": "Rock", "_execucao_silenciosa": True,
            "origem": "terminal_panel",
        },
    }, "toca a playlist Rock")
    assert comando_tipado_acao_painel(
        "playlist_play", {"playlist": "Rock; apaga tudo"},
    ) is None
    with pytest.raises(ErroProtocoloDesktop, match="reprodução inválido"):
        validar_mensagem_cliente({
            "type": "input_submit", "id": "x", "text": "ignorado",
            "kind": "panel_action", "action": "media_toggle",
            "payload": {"command": "executa"},
        }, token="x", autenticado=True)


def test_execucao_silenciosa_registra_resultado_sem_chamar_llm_ou_fala() -> None:
    falas: list[str] = []
    llm: list[str] = []
    contexto_curto: list[str] = []
    contratos: list[object] = []
    ctx = {
        "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
        "enviar_mensagem": lambda *_args, **_kwargs: llm.append("chamada"),
        "ajustar_volume_sistema": lambda _nivel: True,
        "_registrar_resultado_execucao": (
            lambda contrato, *_args, **_kwargs: contratos.append(contrato)
        ),
        "_registrar_mente_curta": lambda *_args: contexto_curto.append("mudou"),
        "_target_from_params": lambda _params, _texto="": "pc_a",
    }

    ok = executar_intencao({
        "intent": "VOLUME",
        "params": {
            "acao": "set", "nivel_volume": 55,
            "_execucao_silenciosa": True, "origem": "terminal_panel",
        },
    }, "controle manual de volume", ctx)

    assert ok is True
    assert falas == []
    assert llm == []
    assert contexto_curto == []
    assert contratos and contratos[-1].status == "volume_ajustado"


def _linha(sock: socket.socket, timeout: float = 1.0) -> dict:
    sock.settimeout(timeout)
    dados = b""
    while not dados.endswith(b"\n"):
        dados += sock.recv(1)
    return json.loads(dados.decode("utf-8"))


def _linha_tipo(sock: socket.socket, tipo: str) -> dict:
    limite = time.monotonic() + 2.0
    while time.monotonic() < limite:
        item = _linha(sock, max(0.05, limite - time.monotonic()))
        if item.get("type") == tipo:
            return item
    raise AssertionError(f"não chegou {tipo}")


def test_ponte_executa_painel_tipado_sem_enviar_para_entrada_conversacional() -> None:
    conversas: list[str] = []
    diretas: list[tuple[str, dict]] = []
    runtime = DesktopBridgeRuntime(
        enviar_entrada=lambda texto: conversas.append(texto),
        executar_acao_painel=lambda acao, payload: (
            diretas.append((acao, dict(payload))) or True
        ),
        historico_getter=list,
        estado_getter=dict,
        resultado_acao_getter=lambda: {"comandos": [{
            "intent": "MEDIA_CONTROL", "executou": True, "confirmado": True,
        }]},
        log=lambda _texto: None,
    )
    runtime.iniciar()
    try:
        with socket.create_connection(runtime.endereco, timeout=1.0) as cliente:
            cliente.sendall((json.dumps({
                "type": "hello", "token": runtime.token,
            }) + "\n").encode())
            assert _linha(cliente)["type"] == "snapshot"
            cliente.sendall((json.dumps({
                "type": "input_submit", "id": "controle-1",
                "text": "vai para a próxima música",
                "kind": "panel_action", "action": "media_next", "payload": {},
            }) + "\n").encode())
            assert _linha_tipo(cliente, "input_ack")["accepted"] is True
            final = None
            limite = time.monotonic() + 2.0
            while time.monotonic() < limite:
                item = _linha(cliente, max(0.05, limite - time.monotonic()))
                if item.get("type") == "action_state" and item.get("state") in {
                    "confirmed", "partial", "failed",
                }:
                    final = item
                    break
            assert final is not None and final["direct"] is True
        assert conversas == []
        assert diretas == [("media_next", {})]
    finally:
        runtime.parar()


def test_clique_manual_nao_cria_balao_nem_indicador_de_llm(monkeypatch) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_laylay_2 import JanelaLaylay

    class Worker(QObject):
        mensagem = Signal(dict)
        conectado = Signal(bool)
        falha = Signal(str)

        def __init__(self) -> None:
            super().__init__()
            self.enviadas: list[dict] = []

        def enfileirar(self, mensagem: dict) -> bool:
            self.enviadas.append(dict(mensagem))
            return True

        def parar(self) -> None:
            pass

    app = QApplication.instance() or QApplication([])
    worker = Worker()
    janela = JanelaLaylay(worker, Path(__file__).parents[1])
    worker.conectado.emit(True)
    app.processEvents()

    janela.enviar_acao_painel("media_next", "vai para a próxima música")
    app.processEvents()

    assert worker.enviadas[-1]["kind"] == "panel_action"
    assert worker.enviadas[-1]["payload"] == {}
    assert janela._envios == {}
    assert janela._indicador_pensando is None
    janela.close()
    app.processEvents()


def test_pagina_mostra_todas_as_playlists_e_toda_a_fila_ao_expandir(
    monkeypatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_000)
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard({
        "music": {
            "title": "Atual", "channel": "Canal", "state": "playing",
            "freshness": "fresh", "observed_at": 1_000,
            "controls_available": True,
            "queue_freshness": "fresh", "queue_observed_at": 1_000,
            "queue_source": "laylay_playlist",
            "queue": [{"title": f"Faixa {i}"} for i in range(15)],
            "catalog_available": True, "catalog_play_available": True,
            "catalog_observed_at": 1_000,
            "catalog": [
                {"name": f"Playlist {i}", "count": i} for i in range(30)
            ],
        },
        "system": {}, "routines": {},
    })
    pagina.show()
    app.processEvents()

    assert len(pagina.preset_botoes) == 30
    assert sum(botao.isVisible() for botao in pagina.preset_botoes) == 6
    pagina._alternar_catalogo()
    app.processEvents()
    assert sum(botao.isVisible() for botao in pagina.preset_botoes) == 30

    assert len(pagina.fila_linhas) == 15
    assert sum(linha["widget"].isVisible() for linha in pagina.fila_linhas) == 5
    pagina._alternar_fila()
    app.processEvents()
    assert sum(linha["widget"].isVisible() for linha in pagina.fila_linhas) == 15
    pagina.close()
    app.processEvents()
