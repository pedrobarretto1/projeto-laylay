"""O servidor é TCP real; sessão, corpo e confirmações usam o owner instalado."""
import json
import socket
import subprocess
import sys
from threading import Event, Thread
import time

import pytest

from mente_laylay.especialistas.rosto_oled_runtime import criar_rosto_oled_runtime


TOKEN_TESTE = "a7" * 32


def configurar(tmp_path, monkeypatch, **campos):
    caminho = tmp_path / "corpo_wifi.json"
    dados = {"version": 1, "ativo": True, "host": "127.0.0.1",
             "hostname": "laylay-corpo.local", "porta": 8765, "token": TOKEN_TESTE}
    dados.update(campos)
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    monkeypatch.setenv("LAYLAY_CORPO_WIFI_CONFIG", str(caminho))
    monkeypatch.delenv("LAYLAY_ROSTO_PORTA", raising=False)
    return caminho


def proibido(*_args, **_kwargs):
    pytest.fail("configuração de rede não pode abrir USB nem iniciar conexão na composição")


def test_factory_auto_seleciona_rede_configurada_sem_abrir_socket_ou_usb(tmp_path, monkeypatch):
    configurar(tmp_path, monkeypatch)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido,
                                      listar_portas=proibido)
    dados = runtime.diagnostico()
    assert dados.get("transporte") == "tcp", "primeira fronteira: factory ignora servidor configurado"
    assert dados["modo_conexao"] == "rede" and dados["configurado"]
    assert dados["endpoint"] == "127.0.0.1:8765"
    assert not dados["conectado"] and not dados["aplicacao_confirmada"]
    assert TOKEN_TESTE not in str(dados)


@pytest.mark.parametrize("porta", ["AUTO", "OFF", "COM8"])
def test_preferencia_usb_companhia_respeita_selecao_explicita_sem_abrir_dispositivo(tmp_path, monkeypatch, porta):
    configurar(tmp_path, monkeypatch)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido,
        listar_portas=proibido, porta=porta, preferir_usb=True)
    diag = runtime.diagnostico()
    assert diag["transporte"] == "serial" and not diag["conectado"]
    assert runtime.autodetectar is (porta == "AUTO")
    assert runtime.porta == ("COM8" if porta == "COM8" else "")


def test_configuracao_wifi_corrompida_falha_antes_do_usb(tmp_path, monkeypatch):
    caminho = configurar(tmp_path, monkeypatch)
    caminho.write_text('{"ativo": true,', encoding="utf-8")
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido,
                                      listar_portas=proibido)
    assert not runtime.sincronizar()
    assert runtime.diagnostico()["motivo"] == "configuracao_wifi_invalida"


@pytest.mark.parametrize("porta", ["OFF", "COM4"])
def test_selecao_serial_ou_off_explicita_preserva_prioridade(tmp_path, monkeypatch, porta):
    configurar(tmp_path, monkeypatch)
    monkeypatch.setenv("LAYLAY_ROSTO_PORTA", porta)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido)
    assert runtime.diagnostico().get("transporte") == "serial"
    assert runtime.diagnostico()["configurado"] is (porta != "OFF")


class ServidorCorpo:
    """Somente o ESP é simulado: socket, fluxo TCP e owner Python são reais."""
    def __init__(self, *, autenticar=True, fragmentar=False, mack=True, sack=True,
                 ack=True, receipt_estranho="", desconectar_motor=False):
        self.autenticar, self.fragmentar = autenticar, fragmentar
        self.mack, self.sack, self.ack = mack, sack, ack
        self.receipt_estranho, self.desconectar_motor = receipt_estranho, desconectar_motor
        self.enviados = []
        self.autenticacoes = self.conexoes = 0
        self.motor_recebido = Event()
        self.parar = Event()
        self._clientes = []
        self.erros = []
        self._servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._servidor.bind(("127.0.0.1", 0))
        self.porta = self._servidor.getsockname()[1]
        self._servidor.listen()
        self._servidor.settimeout(.1)
        self._thread = Thread(target=self._executar, daemon=True)
        self._thread.start()

    def _responder(self, cliente, resposta):
        dados = (resposta + "\r\n").encode()
        if self.fragmentar:
            for inicio in range(0, len(dados), 3):
                cliente.sendall(dados[inicio:inicio + 3])
                time.sleep(.001)
        else:
            cliente.sendall(dados)

    def _executar(self):
        try:
            while not self.parar.is_set():
                try:
                    cliente, _ = self._servidor.accept()
                except socket.timeout:
                    continue
                self.conexoes += 1
                self._clientes.append(cliente)
                cliente.settimeout(.1)
                with cliente:
                    autenticado = False
                    rx = bytearray()
                    desconectado = False
                    while not self.parar.is_set() and not desconectado:
                        try:
                            dados = cliente.recv(128)
                        except socket.timeout:
                            continue
                        except OSError:
                            break
                        if not dados:
                            break
                        rx.extend(dados)
                        while b"\n" in rx:
                            linha, _, resto = rx.partition(b"\n")
                            rx = bytearray(resto)
                            texto = linha.rstrip(b"\r").decode()
                            if not autenticado:
                                self.autenticacoes += 1
                                autenticado = self.autenticar and texto == f"AUTH 1 {TOKEN_TESTE}"
                                self._responder(cliente, "AUTH_OK 1" if autenticado else "AUTH_ERROR 1")
                                if not autenticado:
                                    desconectado = True
                                    break
                                continue
                            self.enviados.append(texto)
                            p = texto.split()
                            resposta = ""
                            if p[0] == "HELLO":
                                resposta = f"READY 1 {p[2]} SSD1306 128 64"
                            elif p[0] == "CAPS":
                                resposta = f"CAPS 1 {p[2]} HACK1"
                            elif p[0] == "GCAPS":
                                resposta = f"GCAPS 1 {p[2]} GLITCH1"
                            elif p[0] == "MCAPS":
                                resposta = f"MCAPS 1 {p[2]} MOTOR1"
                            elif p[0] == "FACE" and self.ack:
                                resposta = "ACK " + " ".join(p[1:-1])
                            elif p[0] == "ACTIVITY":
                                resposta = "AACK " + " ".join(p[1:-1])
                            elif p[0] == "GLITCH":
                                resposta = "GACK " + " ".join(p[1:])
                            elif p[0] == "MOTOR":
                                self.motor_recebido.set()
                                if self.desconectar_motor:
                                    self.desconectar_motor = False
                                    desconectado = True
                                    break
                                if self.mack:
                                    resposta = "MACK " + " ".join(p[1:])
                            elif p[0] == "STOP" and self.sack:
                                resposta = "SACK " + " ".join(p[1:]) if len(p) == 4 else "STOPPED 1"
                            if resposta:
                                if resposta.startswith(self.receipt_estranho + " "):
                                    campos = resposta.split()
                                    campos[3] = "999"
                                    resposta = " ".join(campos)
                                self._responder(cliente, resposta)
        except OSError:
            if not self.parar.is_set():
                self.erros.append("socket_servidor")
        except Exception as erro:
            self.erros.append(type(erro).__name__)

    def close(self):
        self.parar.set()
        for cliente in self._clientes:
            cliente.close()
        self._servidor.close()
        self._thread.join(2)
        assert not self._thread.is_alive() and not self.erros


@pytest.fixture
def servidor():
    abertos = []
    def criar(**kwargs):
        esp = ServidorCorpo(**kwargs)
        abertos.append(esp)
        return esp
    yield criar
    for esp in abertos:
        esp.close()


def runtime_rede(tmp_path, monkeypatch, esp, **kwargs):
    configurar(tmp_path, monkeypatch, porta=esp.porta)
    return criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido,
                                   listar_portas=proibido, **kwargs)


def test_tcp_real_fragmentado_sincroniza_face_hack_glitch_e_pulso_sem_falar_texto(tmp_path, monkeypatch, servidor):
    esp = servidor(fragmentar=True)
    atividade = {"origem": "atividade_operacional_observada", "falha_id": 1,
                 "falha_monotonic": time.monotonic(), "ativos": 1}
    runtime = runtime_rede(tmp_path, monkeypatch, esp, atividade_getter=lambda: atividade)
    try:
        assert runtime.sincronizar(), "fronteira AUTH/HELLO/FACE no TCP"
        diagnostico = runtime.diagnostico()
        assert diagnostico["aplicacao_confirmada"] and diagnostico["hack"]["ativo"]
        assert diagnostico["glitch"]["aplicacao_confirmada"] and diagnostico["motor"]["disponivel"]
        assert not any(p.startswith("MOTOR ") for p in esp.enviados)
        receipt = runtime.mover_corpo(255, -255, 50)
        assert receipt["ok"] and receipt["aplicacao_pwm_confirmada"] and receipt["parada_confirmada"]
        assert not receipt["prova_rotacao"] and not receipt["prova_parada_fisica"]
        assert esp.autenticacoes == 1
        assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
    finally:
        runtime.encerrar()


def test_auth_rejeitada_nao_envia_hello_face_ou_motor_e_nao_vaza_token(tmp_path, monkeypatch, servidor):
    esp = servidor(autenticar=False)
    falhas = []
    runtime = runtime_rede(tmp_path, monkeypatch, esp,
                          relatar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)))
    assert not runtime.sincronizar()
    assert not esp.enviados, "comando saiu antes da autenticação"
    assert not runtime.diagnostico()["motor"]["disponivel"]
    assert TOKEN_TESTE not in str(runtime.diagnostico()) + str(falhas)


def test_token_de_outro_pareamento_nao_autoriza_sessao_tcp(tmp_path, monkeypatch, servidor):
    esp = servidor()
    configurar(tmp_path, monkeypatch, porta=esp.porta, token="c3" * 32)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido)
    assert not runtime.sincronizar()
    assert esp.autenticacoes == 1 and not esp.enviados
    assert "c3" * 32 not in str(runtime.diagnostico())


@pytest.mark.parametrize("campos", [
    {"token": "segredo-invalido"}, {"host": "laylay-corpo.local"},
    {"porta": True}, {"version": True}, {"ativo": "true"}, {"hostname": "outra.local"},
])
def test_schema_wifi_invalido_nao_admite_dns_ou_usb(tmp_path, monkeypatch, campos):
    configurar(tmp_path, monkeypatch, **campos)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido,
                                      listar_portas=proibido)
    assert not runtime.sincronizar()
    assert runtime.diagnostico()["motivo"] == "configuracao_wifi_invalida"
    assert "segredo-invalido" not in str(runtime.diagnostico())


def test_wifi_desativado_preserva_autodeteccao_usb(tmp_path, monkeypatch):
    configurar(tmp_path, monkeypatch, ativo=False)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, listar_portas=lambda: ())
    assert runtime.diagnostico()["transporte"] == "serial"
    assert runtime.diagnostico()["modo_conexao"] == "automatico"
    assert not runtime.sincronizar()


@pytest.mark.parametrize("tipo", ["MACK", "SACK"])
def test_receipt_tcp_estrangeiro_nao_confirma_efeito(tmp_path, monkeypatch, servidor, tipo):
    esp = servidor(receipt_estranho=tipo)
    runtime = runtime_rede(tmp_path, monkeypatch, esp)
    try:
        receipt = runtime.mover_corpo(255, 0, 50)
        assert not receipt["ok"]
        assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
        assert any(p.startswith("STOP 1 ") for p in esp.enviados)
    finally:
        runtime.encerrar()


@pytest.mark.parametrize("opcoes,motivo,pwm", [
    ({"mack": False}, "sem_confirmacao_pwm", False),
    ({"sack": False}, "sem_confirmacao_parada", True),
])
def test_falha_parcial_tcp_preserva_receipt_sem_repetir_motor(tmp_path, monkeypatch, servidor, opcoes, motivo, pwm):
    esp = servidor(**opcoes)
    runtime = runtime_rede(tmp_path, monkeypatch, esp)
    try:
        receipt = runtime.mover_corpo(255, 0, 50)
        assert not receipt["ok"] and receipt["motivo"] == motivo
        assert receipt["aplicacao_pwm_confirmada"] is pwm
        assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
    finally:
        runtime.encerrar()


def test_eof_tcp_invalida_sessao_e_reconexao_nao_reenvia_motor(tmp_path, monkeypatch, servidor):
    esp = servidor(desconectar_motor=True)
    runtime = runtime_rede(tmp_path, monkeypatch, esp)
    receipt = runtime.mover_corpo(255, 0, 50)
    assert not receipt["ok"] and not receipt["aplicacao_pwm_confirmada"]
    assert not runtime.diagnostico()["conectado"]
    assert not runtime.diagnostico()["aplicacao_confirmada"]
    assert runtime._sessao == ""
    try:
        assert runtime.sincronizar()
        assert esp.autenticacoes == 2
        hellos = [p for p in esp.enviados if p.startswith("HELLO ")]
        assert len(hellos) == 2 and hellos[0] != hellos[1]
        assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
    finally:
        runtime.encerrar()


def test_stop_tcp_interrompe_espera_de_mack_e_nao_enfileira_movimento(tmp_path, monkeypatch, servidor):
    esp = servidor(mack=False)
    runtime = runtime_rede(tmp_path, monkeypatch, esp)
    resultados = []
    worker = Thread(target=lambda: resultados.append(runtime.mover_corpo(255, 0, 500)))
    worker.start()
    try:
        assert esp.motor_recebido.wait(3)
        inicio = time.monotonic()
        assert runtime.parar_corpo()["ok"]
        assert time.monotonic() - inicio < .3
        worker.join(2)
        assert not worker.is_alive()
        assert resultados[0]["cancelado"] and not resultados[0]["ok"]
        assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
    finally:
        runtime.encerrar()
        worker.join(2)


def test_movimento_tcp_concorrente_nao_e_enfileirado(tmp_path, monkeypatch, servidor):
    esp = servidor()
    runtime = runtime_rede(tmp_path, monkeypatch, esp)
    resultados = []
    worker = Thread(target=lambda: resultados.append(runtime.mover_corpo(255, 0, 500)))
    worker.start()
    try:
        assert esp.motor_recebido.wait(3)
        assert runtime.mover_corpo(255, 0, 50)["motivo"] == "motor_ocupado"
        assert runtime.parar_corpo()["ok"]
        worker.join(2)
        assert not worker.is_alive()
        assert len([p for p in esp.enviados if p.startswith("MOTOR ")]) == 1
    finally:
        runtime.encerrar()
        worker.join(2)


def test_adapter_tcp_timeout_e_eof_sao_estados_distintos(servidor):
    from mente_laylay.especialistas.corpo_wifi_transporte import ConfiguracaoCorpoWifi, abrir_corpo_tcp
    esp = servidor()
    config = ConfiguracaoCorpoWifi("127.0.0.1", esp.porta, TOKEN_TESTE)
    assert TOKEN_TESTE not in repr(config)
    fluxo = abrir_corpo_tcp(config)
    try:
        inicio = time.monotonic()
        assert fluxo.read(128) == b""
        assert .07 < time.monotonic() - inicio < .3
        esp._clientes[-1].shutdown(socket.SHUT_RDWR)
        with pytest.raises(ConnectionError, match="conexao_corpo_encerrada"):
            fluxo.read(128)
    finally:
        fluxo.close()


def test_escrita_tcp_tem_prazo_e_falha_nao_vira_receipt():
    from mente_laylay.especialistas.corpo_wifi_transporte import FluxoCorpoTcp
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    cliente.connect(listener.getsockname())
    servidor, _ = listener.accept()
    fluxo = FluxoCorpoTcp(cliente)
    try:
        # O buffer do Windows pode absorver uma escrita grande inteira.
        # Alcançar congestionamento real antes de medir a escrita que expirou.
        bloqueou = False
        for _ in range(512):
            inicio = time.monotonic()
            try:
                fluxo.write(b"x" * (512 * 1024))
            except TimeoutError as erro:
                assert str(erro) == "escrita_corpo_expirada"
                assert time.monotonic() - inicio < .3
                bloqueou = True
                break
        assert bloqueou, "o servidor sem leitura deve alcançar backpressure"
    finally:
        fluxo.close()
        servidor.close()
        listener.close()


def test_reconexao_relendo_configuracao_atual_sem_replay_de_movimento(tmp_path, monkeypatch, servidor):
    primeiro, segundo = servidor(), servidor()
    caminho = configurar(tmp_path, monkeypatch, porta=primeiro.porta)
    runtime = criar_rosto_oled_runtime(estado_getter=lambda: {}, abrir_serial=proibido)
    assert runtime.mover_corpo(255, 0, 50)["ok"]
    runtime.encerrar()
    dados = json.loads(caminho.read_text())
    dados["porta"] = segundo.porta
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    try:
        assert runtime.sincronizar()
        assert runtime.diagnostico()["endpoint"] == f"127.0.0.1:{segundo.porta}"
        assert not any(p.startswith("MOTOR ") for p in segundo.enviados)
    finally:
        runtime.encerrar()


def test_composicao_instalada_le_config_tcp_e_catalogo_so_disponivel_com_receipts(tmp_path, monkeypatch, servidor):
    import os
    from pathlib import Path
    esp = servidor()
    configurar(tmp_path, monkeypatch, porta=esp.porta)
    arquivo_saida = tmp_path / "composicao_tcp.json"
    ambiente = dict(os.environ, LAYLAY_TESTE_CORPO_SAIDA=str(arquivo_saida))
    codigo = """
import importlib, json, os
from pathlib import Path
from mente_laylay.integracao import instancia_unica
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
adquirir = instancia_unica.adquirir_instancia_unica
saida = Path(os.environ['LAYLAY_TESTE_CORPO_SAIDA'])
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(saida.parent / 'mutex_tcp')
# Perfil TCP isolado: a preferência USB pessoal do usuário não é fixture.
from mente_laylay.integracao.configuracao_aplicacao import ConfiguracaoAplicacaoRuntime
ConfiguracaoAplicacaoRuntime.companhia_bancada_ao_iniciar = lambda self: False
root = importlib.import_module('laylay')
runtime = root._rosto_oled_runtime
assert root._corpo_motor_runtime.transporte is runtime
assert root._composicao_ciclo_comandos_runtime.contexto.montar()['_corpo_motor_runtime'] is root._corpo_motor_runtime
assert runtime.diagnostico()['transporte'] == 'tcp' and not runtime.diagnostico()['conectado']
assert not root._mapa_habilidades_runtime.consultar('CORPO_MOVER')['disponivel']
assert runtime.sincronizar()
assert root._mapa_habilidades_runtime.consultar('CORPO_MOVER')['disponivel']
pergunta = 'você consegue andar?'
turno = classificar_modalidade_turno(pergunta)
root._estado_compartilhado_runtime.atualizar_campos('mental', turno_atual=turno)
assert 'pulso' in root._mapa_habilidades_runtime.responder_pergunta_capacidade(pergunta, turno=turno)
pedido, _ = root._composicao_ciclo_comandos_runtime.ciclo.resolver_comando_natural(pergunta, 'teste_wifi')
assert pedido is None
assert root._estado_compartilhado_runtime.obter_copia('mental', 'rosto_oled', {})['transporte'] == 'tcp'
runtime.encerrar()
assert not root._mapa_habilidades_runtime.consultar('CORPO_MOVER')['disponivel']
saida.write_text(json.dumps({'owner_unico': True, 'catalogo_vivo': True, 'pergunta_nao_executa': True}), encoding='utf-8')
"""
    processo = subprocess.run([sys.executable, "-c", codigo], env=ambiente,
                              cwd=Path(__file__).resolve().parents[2], capture_output=True,
                              text=True, timeout=30)
    assert processo.returncode == 0, processo.stderr[-2000:]
    assert json.loads(arquivo_saida.read_text())["owner_unico"]
    assert not any(p.startswith("MOTOR ") for p in esp.enviados)
