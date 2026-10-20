from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def janela_v1(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LAYLAY_REDUZIR_MOVIMENTO", "1")
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from cliente import terminal_laylay_2 as modulo

    preferencias = QSettings(str(tmp_path / "interface.ini"), QSettings.IniFormat)
    monkeypatch.setattr(modulo, "QSettings", lambda *_args: preferencias)
    app = QApplication.instance() or QApplication([])
    worker = modulo.PonteWorker("127.0.0.1", 1, "teste-interface")
    enviadas = []
    monkeypatch.setattr(worker, "enfileirar", lambda msg: enviadas.append(msg) or True)
    janela = modulo.JanelaLaylay(worker, Path(__file__).parents[2])
    janela.resize(1100, 760)
    janela.show()
    app.processEvents()
    yield app, worker, janela, enviadas
    janela.close()
    app.processEvents()


def test_tres_apresentacoes_preservam_sessao_feed_rascunho_e_modo(janela_v1):
    app, worker, janela, enviadas = janela_v1
    janela.estado_conexao(True)
    janela.selecionar_pagina("conversa")
    mensagem = janela.adicionar_mensagem("assistant", "Mensagem da sessão real", animar=False)
    janela.composer.editor.setPlainText("Meu rascunho")
    identidade = (janela.worker, janela.feed, janela.composer, janela.composer.editor)
    antes = list(enviadas)

    for modo in ("painel", "ilha", "painel", "completa"):
        janela.apresentacao.definir_modo(modo)
        app.processEvents()
        assert janela.apresentacao.modo == modo
        assert identidade == (worker, janela.feed, janela.composer, janela.composer.editor)
        assert janela.composer.editor.toPlainText() == "Meu rascunho"
        assert janela._modo == "chat"
        assert mensagem.parent() is not None
    assert enviadas == antes
    assert janela.paginas.currentIndex() == 0
    assert janela._pagina_principal == "conversa"


def test_recolher_guarda_pagina_e_recebe_resposta_sem_novo_worker(janela_v1):
    from cliente.terminal_laylay_2 import MensagemWidget

    app, worker, janela, enviadas = janela_v1
    janela.estado_conexao(True)
    janela.selecionar_pagina("configuracoes")
    antes = list(enviadas)
    janela.apresentacao.definir_modo("ilha")
    worker.mensagem.emit({"type": "assistant_message", "text": "Resposta recebida na ilha."})
    app.processEvents()
    janela.apresentacao.definir_modo("painel")
    app.processEvents()
    assert janela.paginas.currentIndex() == 0
    assert janela.composer.isVisible()
    assert any("Resposta recebida" in item.texto for item in janela.feed.findChildren(MensagemWidget))
    janela.apresentacao.definir_modo("completa")
    app.processEvents()
    assert janela.paginas.currentWidget() is janela.configuracoes
    assert enviadas == antes


def test_navegacao_expande_e_controles_permanecem_filhos(janela_v1):
    app, _worker, janela, _enviadas = janela_v1
    janela.apresentacao.definir_modo("ilha")
    janela.selecionar_pagina("configuracoes")
    app.processEvents()
    assert janela.apresentacao.modo == "completa"
    assert janela.paginas.currentWidget() is janela.configuracoes
    for botao in janela.apresentacao.botoes:
        assert botao.window() is janela
        assert not botao.isWindow()


def test_ilha_cabe_no_monitor_e_desconexao_conserva_conclusao(janela_v1):
    app, _worker, janela, enviadas = janela_v1
    janela.apresentacao.definir_modo("ilha")
    janela.estado_conexao(False)
    app.processEvents()
    disponivel = janela.screen().availableGeometry()
    assert disponivel.contains(janela.geometry())
    assert janela.height() < 160
    assert janela.apresentacao.rotulo_estado.text() == janela.status.text()
    assert "Reconectando" in janela.apresentacao.rotulo_estado.text()
    assert not enviadas


def test_pedido_em_andamento_recebe_ack_e_resposta_na_ilha(janela_v1, monkeypatch):
    app, worker, janela, enviadas = janela_v1
    paradas = []
    monkeypatch.setattr(worker, "parar", lambda: paradas.append(True))
    janela.estado_conexao(True)
    janela.enviar_texto("Me explica essa ideia")
    pedido = enviadas[-1]
    assert pedido["type"] == "input_submit"
    mensagem_id = pedido["id"]
    pendente = janela._envios[mensagem_id]
    janela.apresentacao.definir_modo("painel")
    janela.apresentacao.definir_modo("ilha")
    assert janela._envios[mensagem_id] is pendente
    worker.mensagem.emit({"type": "input_ack", "id": mensagem_id, "accepted": True})
    assert janela._fases_envio[mensagem_id] == "resposta"
    worker.mensagem.emit({"type": "assistant_message", "id": mensagem_id, "text": "A resposta chegou.", "emotion": "feliz"})
    app.processEvents()
    assert mensagem_id not in janela._envios
    assert mensagem_id not in janela._timeouts_envio
    assert not paradas
    janela.apresentacao.definir_modo("completa")
    assert janela.apresentacao.mascote_ilha._emocao == "feliz"
    janela.close()
    assert paradas == [True]


def test_voz_real_e_reducao_local_nao_se_confundem_com_apresentacao(janela_v1):
    app, worker, janela, enviadas = janela_v1
    janela.estado_conexao(True)
    worker.mensagem.emit({"type": "state", "activity": "listening", "activity_label": "Ouvindo", "emotion": "curiosa", "voice_available": True, "interaction_mode": "voice"})
    antes = list(enviadas)
    janela.apresentacao.definir_modo("painel")
    app.processEvents()
    assert janela._modo == "voice"
    assert janela.voice_surface.isVisible()
    assert janela.composer.microfone.isEnabled()
    assert not janela.composer.editor.isEnabled()
    janela.apresentacao.definir_modo("ilha")
    janela.apresentacao.definir_modo("completa")
    assert janela._modo == "voice"
    assert enviadas == antes


def test_fechar_encerra_todos_os_mascotes_e_modo_invalido_e_fail_closed(janela_v1):
    _app, _worker, janela, enviadas = janela_v1
    with pytest.raises(ValueError, match="desconhecida"):
        janela.apresentacao.definir_modo("inventado")
    assert janela.apresentacao.modo == "completa"
    assert not enviadas
    janela.apresentacao.definir_modo("ilha")
    janela.close()
    for mascote in (janela.mascote_inicio, janela.mascote_cabecalho, janela.apresentacao.mascote_ilha):
        assert mascote._encerrado
        assert not mascote.animacao_ativa


def test_preferencia_movimento_e_apresentacao_sao_locais(janela_v1):
    _app, _worker, janela, enviadas = janela_v1
    janela.configuracoes.reduzir_movimento.setChecked(False)
    assert janela._reduzir_movimento is True  # variável de ambiente tem precedência
    janela.configuracoes.mascote_integrado.setChecked(False)
    assert janela.mascote_inicio.isHidden()
    assert janela.preferencias.value("v1/mascote_integrado", type=bool) is False
    assert not enviadas


def test_recolher_streaming_interrompe_captura_local_e_preserva_pagina(janela_v1):
    app, _worker, janela, enviadas = janela_v1
    janela.selecionar_pagina("streaming")
    streaming = janela._garantir_pagina_carregada("streaming")
    app.processEvents()
    geracao = streaming.captura._geracao
    janela.apresentacao.definir_modo("ilha")
    app.processEvents()
    assert streaming.captura._geracao > geracao
    assert streaming.captura._captura is None
    assert streaming.captura._confirmada is False
    janela.apresentacao.definir_modo("completa")
    app.processEvents()
    assert janela.paginas.currentWidget() is streaming
    assert streaming.captura._captura is None
    assert not enviadas


def test_geometria_e_janela_maximizada_retornam_ao_expandir(janela_v1):
    app, _worker, janela, _enviadas = janela_v1
    janela.showMaximized()
    app.processEvents()
    janela.apresentacao.definir_modo("painel")
    app.processEvents()
    assert not janela.isMaximized()
    disponivel = janela.screen().availableGeometry()
    assert disponivel.contains(janela.geometry())
    janela.apresentacao.definir_modo("completa")
    app.processEvents()
    assert janela.isMaximized()
