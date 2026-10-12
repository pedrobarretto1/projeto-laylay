"""Pareia o corpo pela USB e confirma o servidor local antes de salvar a conexão.

Execute com ``python -m scripts.configurar_corpo_wifi``. A senha é digitada
na janela e enviada somente à placa; não vai para argumentos, logs ou JSON.
"""
from __future__ import annotations

import ipaddress
import json
import os
from pathlib import Path
import secrets
import time
from typing import Any, Callable

RAIZ = Path(__file__).resolve().parents[1]
CONFIG_PADRAO = RAIZ / "memoria" / "corpo_wifi.json"


def preparar_pacote_wifi(ssid: str, senha: str, token: str) -> bytes:
    nome, chave = ssid.encode("utf-8"), senha.encode("utf-8")
    if (b"\0" in nome or b"\0" in chave or not 1 <= len(nome) <= 32
            or not (len(chave) == 0 or 8 <= len(chave) <= 63)):
        raise ValueError("Nome de rede deve ter até 32 bytes; senha deve ter de 8 a 63 bytes.")
    if len(token) != 64 or any(c not in "0123456789abcdef" for c in token):
        raise ValueError("Chave de pareamento inválida.")
    return f"WIFI_CONFIG 1 {nome.hex()} {chave.hex() or '-'} {token}\n".encode("ascii")


def salvar_conexao_wifi(arquivo: Path, host: str, token: str) -> None:
    # O JSON guarda o pareamento, nunca a senha do roteador.
    from mente_laylay.especialistas.corpo_wifi_transporte import ConfiguracaoCorpoWifi
    configuracao = ConfiguracaoCorpoWifi(host=host, porta=8765, token=token)
    dados = {"version": 1, "ativo": True, "host": configuracao.host,
             "hostname": "laylay-corpo.local", "porta": 8765, "token": token}
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temporario = arquivo.with_name(arquivo.name + ".tmp")
    try:
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporario, arquivo)
    finally:
        temporario.unlink(missing_ok=True)


def aguardar_linha(porta: Any, aceitar: Callable[[str], bool], prazo: float) -> str:
    buffer = bytearray()
    while time.monotonic() < prazo:
        buffer.extend(porta.read(128))
        if len(buffer) > 2048:
            raise ConnectionError("Resposta excessiva da placa.")
        while b"\n" in buffer:
            linha, _, resto = buffer.partition(b"\n")
            buffer = bytearray(resto)
            texto = linha.rstrip(b"\r").decode("ascii", errors="replace")
            if aceitar(texto):
                return texto
            if texto.startswith("ERROR "):
                raise ConnectionError("A placa recusou a configuração; confira o firmware instalado.")
    raise TimeoutError("A placa não confirmou dentro do prazo.")


def configurar_rede(*, ssid: str, senha: str, porta: str,
                    arquivo: Path = CONFIG_PADRAO,
                    somente_associacao: bool = False,
                    progresso: Callable[[str], Any] = lambda _texto: None) -> dict[str, Any]:
    import serial
    from mente_laylay.especialistas.corpo_wifi_transporte import ConfiguracaoCorpoWifi, abrir_corpo_tcp
    from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime
    token = secrets.token_hex(32)
    pacote = preparar_pacote_wifi(ssid, senha, token)
    host = ""
    progresso("Enviando configuração à placa pela USB…")
    with serial.Serial(porta, 115200, timeout=.1, write_timeout=.5) as usb:
        if usb.write(b"STOP\n") != 5:
            raise ConnectionError("A USB não completou a escrita.")
        aguardar_linha(usb, lambda s: s == "STOPPED 1", time.monotonic() + 2)
        if usb.write(pacote) != len(pacote):
            raise ConnectionError("A USB não completou a configuração.")
        aguardar_linha(usb, lambda s: s == "WIFI_CONFIGURED 1", time.monotonic() + 3)
        progresso("ESP32 entrando no Wi‑Fi; o PC continua na rede atual…")
        prazo = time.monotonic() + 35
        while time.monotonic() < prazo:
            consulta = b"WIFI_STATUS 1\n"
            if usb.write(consulta) != len(consulta):
                raise ConnectionError("A USB não completou a consulta.")
            status = aguardar_linha(usb, lambda s: s.startswith("WIFI_STATUS 1 "),
                                   min(prazo, time.monotonic() + 2))
            campos = status.split()
            if len(campos) == 5 and campos[2] == "CONNECTED" and campos[4] == "8765":
                host = str(ipaddress.IPv4Address(campos[3]))
                break
            time.sleep(.3)
    if not host:
        raise ConnectionError("O ESP32 não entrou na rede. Confira o nome, a senha e o Wi‑Fi de 2,4 GHz.")
    if somente_associacao:
        return {"host": host, "porta": 8765, "somente_associacao": True,
                "rosto_confirmado": False, "parada_confirmada": False}
    progresso("Verificando pareamento, rosto e parada pelo Wi‑Fi…")
    configuracao = ConfiguracaoCorpoWifi(host=host, porta=8765, token=token)
    runtime = RostoOledRuntime(estado_getter=lambda: {}, porta=f"tcp://{host}:8765",
                               abrir_serial=lambda _porta: abrir_corpo_tcp(configuracao))
    try:
        confirmado = False
        # IP recebido nao prova servidor acessivel. Reconectar antes do primeiro
        # receipt e seguro: somente handshake/FACE; nenhum MOTOR e reenviado.
        for tentativa in range(3):
            confirmado = runtime.sincronizar()
            if confirmado:
                break
            if tentativa < 2:
                time.sleep(1)
        if not confirmado:
            raise ConnectionError("O servidor não confirmou o rosto; a conexão ainda não foi ativada na Laylay.")
        parada = runtime.parar_corpo()
        if not parada.get("parada_confirmada"):
            raise ConnectionError("A parada não foi confirmada pela rede; a conexão não foi ativada.")
        salvar_conexao_wifi(arquivo, host, token)
        return {"host": host, "porta": 8765, "rosto_confirmado": True,
                "parada_confirmada": True, "arquivo": str(arquivo)}
    finally:
        runtime.encerrar()


def main() -> None:
    import sys
    from PySide6.QtCore import QThread, Signal
    from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QFormLayout,
                                  QLabel, QLineEdit, QPushButton, QVBoxLayout)
    from serial.tools.list_ports import comports

    class Configurador(QThread):
        progresso = Signal(str)
        concluido = Signal(object)
        falhou = Signal(str)

        def __init__(self, ssid: str, senha: str, porta: str, somente_associacao: bool) -> None:
            super().__init__()
            self.ssid, self.senha, self.porta = ssid, senha, porta
            self.somente_associacao = somente_associacao

        def run(self) -> None:
            try:
                resultado = configurar_rede(ssid=self.ssid, senha=self.senha, porta=self.porta,
                                             somente_associacao=self.somente_associacao,
                                             progresso=self.progresso.emit)
                self.concluido.emit(resultado)
            except Exception as erro:
                # Nunca mostrar repr da porta/pacote, token ou senha, mesmo numa falha.
                pasta = RAIZ / "artifacts" / "rosto_oled" / "wifi"
                pasta.mkdir(parents=True, exist_ok=True)
                mensagem = str(erro) if isinstance(erro, (ConnectionError, TimeoutError, ValueError)) else "usb_indisponivel"
                (pasta / "configuracao_falhou.json").write_text(
                    json.dumps({"tipo": type(erro).__name__, "motivo": mensagem}, ensure_ascii=False, indent=2), encoding="utf-8")
                self.falhou.emit("Não consegui concluir (" + type(erro).__name__ + "). "
                                 + mensagem)
            finally:
                self.senha = ""

    app = QApplication(sys.argv)
    trabalho: list[Configurador] = []
    class JanelaConfiguracao(QDialog):
        def reject(self) -> None:
            # Esc segue reject(), não closeEvent(). Não sair com USB/QThread vivos.
            if any(t.isRunning() for t in trabalho):
                status.setText("Aguarde a configuração terminar antes de fechar.")
                return
            super().reject()

        def closeEvent(self, evento: Any) -> None:
            if any(t.isRunning() for t in trabalho):
                status.setText("Aguarde a configuração terminar antes de fechar.")
                evento.ignore()
            else:
                super().closeEvent(evento)

    janela = JanelaConfiguracao()
    janela.setWindowTitle("Laylay — conectar o corpo ao Wi‑Fi")
    janela.resize(510, 300)
    layout = QVBoxLayout(janela)
    aviso = QLabel("Digite a rede de 2,4 GHz e sua senha.\n"
                   "Seu PC continua conectado à rede atual. A senha vai somente à placa.")
    aviso.setWordWrap(True)
    layout.addWidget(aviso)
    form = QFormLayout()
    ssid = QLineEdit(os.environ.get("LAYLAY_WIFI_REDE", ""))
    ssid.setPlaceholderText("Nome da sua rede de 2,4 GHz")
    senha = QLineEdit()
    senha.setEchoMode(QLineEdit.EchoMode.Password)
    portas = QComboBox()
    candidatas = [p.device for p in comports() if p.vid == 0x303A and p.pid == 0x1001]
    portas.addItems(candidatas)
    form.addRow("Rede Wi‑Fi", ssid)
    form.addRow("Senha", senha)
    form.addRow("ESP32 na USB", portas)
    layout.addLayout(form)
    teste_rede = QCheckBox("Testar somente associação (hotspot; não ativar na Laylay)")
    teste_rede.setChecked(os.environ.get("LAYLAY_WIFI_TESTE_REDE") == "1")
    layout.addWidget(teste_rede)
    status = QLabel("A placa deve permanecer conectada à USB durante a configuração.")
    status.setWordWrap(True)
    layout.addWidget(status)
    botao = QPushButton("Conectar e testar")
    botao.setEnabled(bool(candidatas))
    layout.addWidget(botao)

    def iniciar() -> None:
        try:
            preparar_pacote_wifi(ssid.text(), senha.text(), "0" * 64)
        except ValueError as erro:
            status.setText(str(erro))
            return
        botao.setEnabled(False)
        ssid.setEnabled(False)
        portas.setEnabled(False)
        tarefa = Configurador(ssid.text(), senha.text(), portas.currentText(), teste_rede.isChecked())
        teste_rede.setEnabled(False)
        senha.clear()
        senha.setEnabled(False)
        trabalho.append(tarefa)
        tarefa.progresso.connect(status.setText)

        def terminou(resultado: dict[str, Any]) -> None:
            if resultado.get("somente_associacao"):
                status.setText(f"Associação confirmada! ESP32 recebeu {resultado['host']}.\n"
                               "Teste de rede concluído; conexão da Laylay não foi ativada.")
            else:
                status.setText(f"Conectado em {resultado['host']}:8765. Rosto e parada confirmados pelo Wi‑Fi.\n"
                               "Pode abrir a Laylay: ela usará a rede automaticamente.")
            botao.setText("Conexão configurada")
            # Receipt local sem SSID/senha/token para validar sem capturar a janela.
            pasta = RAIZ / "artifacts" / "rosto_oled" / "wifi"
            pasta.mkdir(parents=True, exist_ok=True)
            nome = "associacao_confirmada.json" if resultado.get("somente_associacao") else "configuracao_confirmada.json"
            (pasta / nome).write_text(
                json.dumps({k: v for k, v in resultado.items() if k != "arquivo"}, indent=2), encoding="utf-8")

        def falhou(texto: str) -> None:
            status.setText(texto)
            botao.setEnabled(True)
            ssid.setEnabled(True)
            portas.setEnabled(True)
            senha.setEnabled(True)
            teste_rede.setEnabled(True)

        tarefa.concluido.connect(terminou)
        tarefa.falhou.connect(falhou)
        tarefa.start()

    botao.clicked.connect(iniciar)
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
