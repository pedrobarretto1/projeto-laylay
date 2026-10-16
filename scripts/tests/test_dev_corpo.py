"""Corpo → DEV → bridge → página, observacional e sem comandos."""
from mente_laylay.integracao.dev_console_runtime import DevConsoleRuntime
from mente_laylay.integracao.desktop_bridge import sanitizar_retrato_dev


def dados_corpo(fase="aguardando"):
    return {"transporte": {"transporte": "serial", "porta_ativa": "COM4", "aplicacao_confirmada": True},
            "corpo": {"disponivel": True, "em_andamento": False,
                "companhia": {"ativa": True, "perfil_corporal": "rodas_suspensas",
                    "intencao": {"id": "i1", "objetivo_id": "o1", "turno_id": "t1",
                        "nome": "interagir", "motivo": "conversa_em_andamento", "fase": fase,
                        "estado": "proposta", "emocao": 6, "nivel": 2}},
                "experiencia": {"historico_recente": [{"id": "e1", "resultado": "pwm_e_parada_confirmados",
                    "confirmado": True, "prova_deslocamento": False}]}}}


def test_dev_publica_resumo_e_transicoes_sem_flood_ou_mutacao():
    dados = dados_corpo()
    dev = DevConsoleRuntime()
    dev.configurar_corpo_getter(lambda: dados)
    s = dev.snapshot()
    assert s["body"]["fase"] == "aguardando"
    assert s["body"]["porta"] == "COM4"
    assert s["body"]["deslocamento"] == "nao_medido"
    assert s["body"]["autoriza_execucao"] is False
    sequencia = s["sequence"]
    for _ in range(10): assert dev.snapshot()["sequence"] == sequencia
    dados["corpo"]["companhia"]["intencao"]["fase"] = "gesticulando"
    novo = dev.snapshot()
    assert novo["sequence"] == sequencia + 1
    assert "gesticulando" in novo["events"][-1]["message"]
    assert novo["events"][-1]["category"] == "AUTONOMY"
    assert novo["body"]["trace_id"] == "t1"


def test_bridge_preserva_body_allowlist_sem_credenciais_ou_autoridade():
    dev = DevConsoleRuntime()
    dados = dados_corpo()
    dados["token"] = "segredo"
    dados["corpo"]["companhia"]["intencao"]["motivo"] = "senha=oculta <b>literal</b>"
    dev.configurar_corpo_getter(lambda: dados)
    publico = sanitizar_retrato_dev(dev.snapshot())
    assert publico["body"]["conexao"] == "conectada"
    assert "oculta" not in str(publico) and "segredo" not in str(publico)
    assert publico["body"]["autoriza_execucao"] is False
    consulta = dev.consultar("inspect corpo")
    assert consulta["ok"] and "nao_medido" in " ".join(consulta["lines"])


def test_getter_falhou_invalida_estado_sem_anunciar_movimento():
    dev = DevConsoleRuntime()
    dev.configurar_corpo_getter(lambda: dados_corpo("gesticulando"))
    assert dev.snapshot()["body"]["conexao"] == "conectada"
    def falhar(): raise OSError("sem serial")
    dev.configurar_corpo_getter(falhar)
    atual = dev.snapshot()["body"]
    assert atual["conexao"] == "indisponivel" and atual["fase"] == "desconhecida"


def test_revogacao_da_companhia_aparece_no_dev_sem_ser_mascarada_pela_intencao():
    dados = dados_corpo("interrompida")
    c = dados["corpo"]["companhia"]
    c.update(ativa=False, motivo="gesto_nao_confirmado")
    c["intencao"].update(motivo_termino="gesto_nao_confirmado", resultado={
        "ok": False, "motivo": "sem_confirmacao_expressao"})
    dev = DevConsoleRuntime()
    dev.configurar_corpo_getter(lambda: dados)
    s = sanitizar_retrato_dev(dev.snapshot())
    assert s["body"]["motivo_companhia"] == "gesto_nao_confirmado"
    assert s["body"]["motivo"] == "gesto_nao_confirmado"
    assert s["body"]["erro"] == "sem_confirmacao_expressao"


def test_terminal_recebe_body_antes_de_abrir_aba_e_invalida_na_desconexao(monkeypatch):
    from scripts.tests.test_terminal_aba_desenvolvedor import _janela
    app, janela = _janela(monkeypatch)
    janela.estado_conexao(True)
    dev = DevConsoleRuntime()
    dev.configurar_corpo_getter(lambda: dados_corpo())
    janela.receber({"type": "dev_events", **sanitizar_retrato_dev(dev.snapshot())})
    pagina = janela.pagina_desenvolvedor
    assert "interagir" in pagina.corpo_detalhes.text()
    assert "não medido" in pagina.corpo_detalhes.text()
    janela.estado_conexao(False)
    assert "Ponte desconectada" in pagina.corpo_detalhes.text()
    assert not janela._corpo_dev_mais_recente
    janela.close()


def test_resumo_corporal_permanece_visivel_em_janelas_menores(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont
    from cliente.terminal_laylay_2 import carregar_fontes_interface
    from cliente.terminal_2.desenvolvedor import PaginaDesenvolvedor
    app = QApplication.instance() or QApplication([])
    fonte_anterior = app.font()
    # Mesmo bootstrap de fontes do terminal real; Sans Serif no offscreen
    # produz minimumSizeHint de 1494px e impede o resize que se quer testar.
    app.setFont(QFont(carregar_fontes_interface(), 10))
    pagina = PaginaDesenvolvedor()
    pagina.definir_conectada(True)
    dev = DevConsoleRuntime()
    dev.configurar_corpo_getter(lambda: dados_corpo())
    pagina.aplicar_corpo(dev.snapshot()["body"])
    pagina.resize(900, 850)
    pagina.show()
    app.processEvents()
    assert not pagina.corpo_compacto.isVisible()
    pagina.botoes_categoria["CORPO"].click()
    app.processEvents()
    # O Qt respeita o mínimo da toolbar; o contrato é mostrar o resumo
    # em toda largura efetiva abaixo do limite de 1320px da lateral.
    assert pagina.width() < 1320
    assert pagina.corpo_compacto.isVisible() and not pagina.rail.isVisible()
    assert "CORPO" in pagina.corpo_resumo.text() and "COM4" in pagina.corpo_resumo.text()
    pagina.resize(1600, 850)
    app.processEvents()
    assert pagina.rail.isVisible() and not pagina.corpo_compacto.isVisible()
    assert "interagir" in pagina.corpo_detalhes.text()
    pagina.close()
    app.setFont(fonte_anterior)


def test_corpo_so_aparece_ao_selecionar_opcao_sem_perder_eventos(monkeypatch):
    from scripts.tests.test_terminal_aba_desenvolvedor import _janela
    app, janela = _janela(monkeypatch)
    janela.selecionar_pagina("desenvolvedor")
    pagina = janela.pagina_desenvolvedor
    dev = DevConsoleRuntime()
    dev.configurar_corpo_getter(lambda: dados_corpo())
    janela.receber({"type": "dev_events", **sanitizar_retrato_dev(dev.snapshot())})
    pagina.registrar_evento("Controle de música", "música confirmada", categoria="AUTONOMY")
    app.processEvents()
    assert "AUTONOMIA:CORPO" not in pagina.console.toPlainText()
    assert "Controle de música" in pagina.console.toPlainText()
    assert pagina.corpo_compacto.isHidden() and pagina.card_corpo.isHidden()
    pagina.botoes_categoria["CORPO"].click()
    app.processEvents()
    assert "AUTONOMIA:CORPO" in pagina.console.toPlainText()
    assert "Controle de música" not in pagina.console.toPlainText()
    assert not (pagina.corpo_compacto.isHidden() and pagina.card_corpo.isHidden())
    dados = dados_corpo("gesticulando")
    dev.configurar_corpo_getter(lambda: dados)
    pagina.botoes_categoria["ALL"].click()
    janela.receber({"type": "dev_events", **sanitizar_retrato_dev(dev.snapshot())})
    assert "AUTONOMIA:CORPO" not in pagina.console.toPlainText()
    pagina.botoes_categoria["AUTONOMY"].click()
    assert "AUTONOMIA:CORPO" not in pagina.console.toPlainText()
    assert "Controle de música" in pagina.console.toPlainText()
    pagina.botoes_categoria["CORPO"].click()
    assert "gesticulando" in pagina.console.toPlainText()
    assert "gesticulando" in pagina.corpo_detalhes.text()
    janela.close()


def test_bridge_autenticado_entrega_corpo_ao_vivo_e_consulta_sem_entrada():
    import socket, json
    from mente_laylay.integracao.desktop_bridge import DesktopBridgeRuntime
    from scripts.tests.test_dev_console_runtime import _linha, _ate_tipo
    dados = dados_corpo()
    dev = DevConsoleRuntime()
    dev.configurar_corpo_getter(lambda: dados)
    entradas = []
    ponte = DesktopBridgeRuntime(enviar_entrada=lambda texto: entradas.append(texto),
        historico_getter=list, estado_getter=dict, dev_console_getter=dev.snapshot,
        dev_console_consultar=dev.consultar, dev_console_interval_s=.05, log=lambda _: None)
    ponte.iniciar()
    try:
        with socket.create_connection(ponte.endereco, timeout=1) as cliente:
            cliente.sendall((json.dumps({"type": "hello", "token": ponte.token}) + "\n").encode())
            inicial = _linha(cliente)
            assert inicial["dev_console"]["body"]["fase"] == "aguardando"
            dados["corpo"]["companhia"]["intencao"]["fase"] = "gesticulando"
            while True:
                lote = _ate_tipo(cliente, "dev_events")
                if lote["body"]["fase"] == "gesticulando": break
            assert any("gesticulando" in e["message"] for e in lote["events"])
            cliente.sendall((json.dumps({"type": "dev_query", "id": "corpo-1", "command": "inspect corpo"}) + "\n").encode())
            resposta = _ate_tipo(cliente, "dev_query_result")
            assert resposta["result"]["ok"]
            assert "nao_medido" in " ".join(resposta["result"]["lines"])
            assert not entradas, "consulta DEV não é entrada da mente nem autoridade motora"
    finally:
        ponte.parar()


def test_observacao_dev_nao_altera_receipts_quando_getter_falha(monkeypatch):
    from scripts.tests.test_companhia_corporal import montar, ativar, emocao
    estado, _, rosto, corpo, _, _ = montar()
    def quebrar(): raise OSError("DEV indisponível")
    corpo.observar_corpo_cb = quebrar
    assert ativar(corpo)["ok"]
    emocao(estado, rosto, "alegre")
    monkeypatch.setattr(corpo.companhia, "_aguardar_gesto", lambda ms, validar: validar())
    assert corpo.companhia.processar()["ok"]
    assert estado.mental["experiencia_corporal"]["confirmado"]


def test_composicao_instalada_projeta_decisoes_corpo_no_dev(tmp_path):
    import subprocess, sys
    codigo = f'''
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir({str(tmp_path/'instancia')!r})
import laylay
from mente_laylay.cognicao.decisao_corporal import IntencaoCorporal
corpo, dev = laylay._corpo_motor_runtime, laylay._dev_console_runtime
corpo.companhia._registrar_intencao(IntencaoCorporal("atenta", "atividade_pc_em_andamento", 100, 0, 1))
s = dev.snapshot()
assert s["body"]["intencao"] == "atenta" and s["body"]["deslocamento"] == "nao_medido"
assert s["body"]["autoriza_execucao"] is False
assert any("AUTONOMIA:CORPO" in e["message"] for e in s["events"])
assert dev.consultar("inspect corpo")["ok"]
'''
    r = subprocess.run([sys.executable, "-"], input=codigo, text=True, capture_output=True, timeout=40)
    assert r.returncode == 0, r.stdout + r.stderr
