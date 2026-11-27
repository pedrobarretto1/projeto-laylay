"""Conecta a saída do rosto aos owners compartilhados já existentes."""
from __future__ import annotations
import os
import socket
from typing import Any
from mente_laylay.especialistas.rosto_oled_runtime import criar_rosto_oled_runtime, RostoOledRuntime
from mente_laylay.especialistas.corpo_wifi_transporte import FluxoCorpoTcp


def _abrir_corpo_simulado(_porta: str) -> FluxoCorpoTcp:
    try:
        porta = int(os.environ["LAYLAY_CORPO_SIMULADOR_PORTA"])
        token = bytes.fromhex(os.environ["LAYLAY_CORPO_SIMULADOR_SESSAO"])
        if not 1 <= porta <= 65535 or len(token) != 32:
            raise ValueError
    except (KeyError, ValueError):
        raise ConnectionError("Bancada virtual sem sessão local válida") from None
    conexao = socket.create_connection(("127.0.0.1", porta), timeout=.5)
    try:
        conexao.sendall(token)
        if conexao.recv(1) != b"+":
            raise ConnectionError("A bancada virtual não aceitou a sessão")
        return FluxoCorpoTcp(conexao)
    except OSError:
        conexao.close()
        raise


def criar_composicao_rosto_oled_runtime(*, estado: Any, observabilidade: Any, **kwargs: Any) -> RostoOledRuntime:
    if "LAYLAY_CORPO_SIMULADOR_PORTA" in os.environ:
        kwargs.pop("config_wifi_path", None)
        kwargs.pop("wifi_alternativo_path", None)
        kwargs.pop("config_ble_path", None)
        kwargs.update(porta="CORPO_VIRTUAL", autodetectar=False, abrir_serial=_abrir_corpo_simulado,
                      identidade_usb_getter=lambda: {})
    return criar_rosto_oled_runtime(
        estado_getter=lambda: estado.retrato_dominio("conversacional"),
        atividade_getter=lambda: estado.obter_copia("mental", "atividade_operacional", {}),
        publicar_diagnostico=lambda dados: estado.atualizar_campos("mental", rosto_oled=dados),
        relatar_falha=observabilidade.relatar_falha,
        **kwargs,
    )
