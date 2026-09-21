from __future__ import annotations

import inspect
import os

import pytest

import mente_laylay.autonomia.comandos_sistema as comandos_sistema


class ProcessoFalso:
    def __init__(self, pid: int, nome: str):
        self.pid = pid
        self._nome = nome
        self.info = {"pid": pid, "name": nome}
        self.kill_chamado = False

    def name(self):
        return self._nome

    def kill(self):
        self.kill_chamado = True


def test_nome_protegido_com_exe_e_normalizado():
    assert comandos_sistema._normalizar_nome_processo_fechamento("python.exe") == "python"
    processo = ProcessoFalso(999_001, "python.exe")
    protegido, motivo = comandos_sistema._processo_protegido_fechamento(
        processo,
        pids_autoprotegidos=set(),
    )
    assert protegido is True
    assert "processo_protegido" in motivo


def test_pid_atual_e_incondicionalmente_protegido():
    processo = ProcessoFalso(os.getpid(), "opera.exe")
    protegido, motivo = comandos_sistema._processo_protegido_fechamento(
        processo,
        pids_autoprotegidos={os.getpid()},
    )
    assert protegido is True
    assert motivo == "processo_da_laylay_ou_ancestral"


def test_pid_ancestral_e_incondicionalmente_protegido():
    processo = ProcessoFalso(424_242, "opera.exe")
    protegido, motivo = comandos_sistema._processo_protegido_fechamento(
        processo,
        pids_autoprotegidos={424_242},
    )
    assert protegido is True
    assert motivo == "processo_da_laylay_ou_ancestral"


def test_opera_nao_pode_fechar_launcher_generico():
    assert comandos_sistema._NOMES_CANONICOS_FECHAMENTO["opera"] == ("opera.exe",)
    assert "launcher.exe" not in comandos_sistema._NOMES_CANONICOS_FECHAMENTO["opera"]


def test_processo_exato_normal_pode_passar_preflight():
    processo = ProcessoFalso(777_777, "opera.exe")
    protegido, motivo = comandos_sistema._processo_protegido_fechamento(
        processo,
        pids_autoprotegidos={os.getpid()},
    )
    assert protegido is False
    assert motivo == ""
    assert comandos_sistema._processo_corresponde_fechamento(
        processo,
        {"opera.exe"},
    ) is True


def test_fechamento_do_proprio_pid_nunca_chama_kill(monkeypatch):
    processo = ProcessoFalso(os.getpid(), "opera.exe")

    monkeypatch.setattr(comandos_sistema, "gw", None)
    monkeypatch.setattr(
        comandos_sistema.psutil,
        "process_iter",
        lambda _attrs: [processo],
    )
    monkeypatch.setattr(
        comandos_sistema,
        "_pids_autoprotegidos_fechamento",
        lambda: {os.getpid()},
    )

    with pytest.raises(Exception):
        comandos_sistema.fechar_programa("opera")

    assert processo.kill_chamado is False


def test_executor_destrutivo_nao_usa_match_closest():
    fonte = inspect.getsource(comandos_sistema.fechar_programa)
    assert "match_closest=True" not in fonte
    assert "close_app(" not in fonte


def test_kill_fica_centralizado_atras_da_barreira():
    fonte_modulo = inspect.getsource(comandos_sistema)
    fonte_guard = inspect.getsource(comandos_sistema._encerrar_processo_validado)
    assert "proc.kill()" in fonte_guard

    bloco_p0 = fonte_modulo.split(
        "# P0_AUTOPRESERVACAO_EXECUTOR_20260814",
        1,
    )[1]
    assert bloco_p0.count(".kill()") == 1
    assert "_processo_protegido_fechamento(" in fonte_guard
