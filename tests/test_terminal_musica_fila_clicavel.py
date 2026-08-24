from __future__ import annotations

import json
from pathlib import Path

import pytest

from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.integracao.acoes_painel_runtime import (
    comando_tipado_acao_painel,
)
from mente_laylay.integracao.acoes_terminal import definicao_acao_terminal
from mente_laylay.integracao.desktop_bridge import (
    ErroProtocoloDesktop,
    sanitizar_dashboard_estado,
    validar_mensagem_cliente,
)
from mente_laylay.integracao.navegador_runtime import NavegadorOperacoesRuntime


ITEM_ID = "abcdefghijk"


def test_fila_publica_preserva_so_identificador_youtube_valido() -> None:
    publico = sanitizar_dashboard_estado({
        "generated_at": 1_000,
        "music": {
            "title": "Atual", "state": "playing", "freshness": "fresh",
            "observed_at": 1_000, "queue_freshness": "fresh",
            "queue_observed_at": 1_000, "queue_source": "youtube",
            "queue": [
                {"title": "Válida", "item_id": ITEM_ID},
                {"title": "Inválida", "item_id": "https://segredo.local/x"},
            ],
        },
    })

    assert publico["music"]["queue"][0]["item_id"] == ITEM_ID
    assert "item_id" not in publico["music"]["queue"][1]
    assert "segredo" not in json.dumps(publico)


def test_controle_tipado_da_fila_e_fechado_e_nao_usa_llm() -> None:
    assert comando_tipado_acao_painel(
        "queue_play", {"item_id": ITEM_ID, "queue_index": 2},
    ) == ({
        "intent": "MEDIA_CONTROL",
        "params": {
            "acao": "queue_select", "queue_item_id": ITEM_ID,
            "queue_index": 2, "platform": "youtube",
            "_execucao_silenciosa": True, "origem": "terminal_panel",
        },
    }, "controle manual da fila: item 3")
    assert comando_tipado_acao_painel(
        "queue_play", {"item_id": "invalido", "queue_index": 0},
    ) is None
    assert definicao_acao_terminal("queue_play")["intent"] == "MEDIA_CONTROL"


def test_ponte_rejeita_item_ou_posicao_adulterados() -> None:
    base = {
        "type": "input_submit", "id": "fila-1",
        "text": "toca a faixa da fila", "kind": "panel_action",
        "action": "queue_play",
    }
    valido = validar_mensagem_cliente(
        {**base, "payload": {"item_id": ITEM_ID, "queue_index": 0}},
        token="x", autenticado=True,
    )
    assert valido["payload"] == {"item_id": ITEM_ID, "queue_index": 0}

    for payload in (
        {"item_id": "invalido", "queue_index": 0},
        {"item_id": ITEM_ID, "queue_index": 8},
        {"item_id": ITEM_ID, "queue_index": 0, "url": "https://x"},
    ):
        with pytest.raises(ErroProtocoloDesktop):
            validar_mensagem_cliente(
                {**base, "payload": payload}, token="x", autenticado=True,
            )


def test_clique_na_faixa_emite_acao_direta_com_identidade_observada(
    monkeypatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr("cliente.terminal_2.musica_m1.time.time", lambda: 1_000)
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.resize(1_420, 820)
    pagina.show()
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard({
        "music": {
            "title": "Atual", "state": "playing", "freshness": "fresh",
            "observed_at": 1_000, "controls_available": True,
            "queue_freshness": "fresh", "queue_observed_at": 1_000,
            "queue_source": "youtube", "queue": [{
                "title": "Próxima observada", "channel": "Canal",
                "item_id": ITEM_ID,
            }],
        }, "system": {}, "routines": {},
    })
    pedidos: list[tuple[str, str, dict]] = []
    pagina.acao_fila_solicitada.connect(
        lambda acao, texto, dados: pedidos.append((acao, texto, dict(dados))),
    )
    app.processEvents()

    botao = pagina.fila_linhas[0]["widget"]
    assert botao.isEnabled()
    assert "Próxima observada" in botao.accessibleName()
    botao.click()

    assert pedidos == [(
        "queue_play", "toca Próxima observada da fila",
        {"item_id": ITEM_ID, "queue_index": 0},
    )]
    pagina.close()
    app.processEvents()


def test_fila_interna_ou_sem_identidade_nao_ganha_execucao_visual(
    monkeypatch,
) -> None:
    pytest.importorskip("PySide6")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from cliente.terminal_2.musica_m1 import PaginaMusicaM1

    app = QApplication.instance() or QApplication([])
    pagina = PaginaMusicaM1()
    pagina.definir_conectada(True)
    pagina.aplicar_dashboard({
        "music": {
            "state": "playing", "freshness": "fresh", "observed_at": 1_000,
            "controls_available": True, "queue_freshness": "fresh",
            "queue_observed_at": 1_000, "queue_source": "laylay_playlist",
            "queue": [{"title": "Apenas estimada", "item_id": ITEM_ID}],
        }, "system": {}, "routines": {},
    })

    assert not pagina.fila_linhas[0]["widget"].isEnabled()
    pagina.close()
    app.processEvents()


def test_executor_seleciona_item_exato_e_preserva_confirmacao() -> None:
    chamadas: list[tuple] = []
    resultados: list[tuple] = []

    class Navegador:
        def controlar_youtube_detalhado(self, comando, **kwargs):
            chamadas.append((comando, kwargs))
            return {
                "ok": True, "confirmado": True, "status": "success",
                "message": "", "evidence": {"requestedId": ITEM_ID},
            }

    ok = executar_media_control(
        {
            "acao": "queue_select", "queue_item_id": ITEM_ID,
            "queue_index": 1, "platform": "youtube",
        },
        "controle manual da fila: item 2", "local",
        {"_registro_navegador_operacoes_runtime": Navegador()},
        marcar_resultado=lambda *args, **kwargs: resultados.append((args, kwargs)),
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=dict,
    )

    assert ok is True
    assert chamadas == [(
        "queue_select",
        {"tab_id": None, "queue_item_id": ITEM_ID, "queue_index": 1},
    )]
    assert resultados[-1][0][:2] == ("midia_queue_select", True)
    assert resultados[-1][1]["confirmado"] is True


def test_navegador_e_extensao_transportam_selecao_sem_url_livre() -> None:
    class Comandos:
        def __init__(self) -> None:
            self.chamadas: list[tuple[str, dict]] = []

        def enviar_detalhado(self, action: str, payload: dict) -> dict:
            self.chamadas.append((action, dict(payload)))
            return {"ok": True, "confirmado": True, "status": "success"}

    comandos = Comandos()
    navegador = NavegadorOperacoesRuntime(comandos=comandos, ambiente=object())
    retorno = navegador.controlar_youtube_detalhado(
        "queue_select", tab_id=7, queue_item_id=ITEM_ID, queue_index=3,
    )

    assert retorno["confirmado"] is True
    assert comandos.chamadas == [(
        "youtube_control",
        {
            "command": "queue_select", "target_tab_id": 7,
            "queue_item_id": ITEM_ID, "queue_index": 3,
        },
    )]
    raiz = Path(__file__).parents[1]
    script = (raiz / "extençao_google" / "content_script.js").read_text(
        encoding="utf-8",
    )
    manifesto = json.loads((
        raiz / "extençao_google" / "manifest.json"
    ).read_text(encoding="utf-8"))
    assert 'cmd === "queue_select"' in script
    assert 'status: "stale_context"' in script
    assert "observedId !== requestedId" in script
    assert manifesto["version"] == "2.7"
