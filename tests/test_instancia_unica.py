from __future__ import annotations

import os
import pytest

from mente_laylay.integracao.instancia_unica import (
    ERRO_MUTEX_JA_EXISTE,
    adquirir_instancia_unica,
    nome_mutex_instancia,
)


def test_mutex_e_estavel_por_projeto_e_distinto_entre_instalacoes(tmp_path) -> None:
    projeto = tmp_path / "projeto lay" / "laylay.py"
    mesmo = nome_mutex_instancia(projeto)

    assert mesmo == nome_mutex_instancia(projeto)
    assert mesmo != nome_mutex_instancia(tmp_path / "outra" / "laylay.py")
    assert mesmo.startswith("Local\\Laylay_")


def test_segunda_instancia_e_recusada_e_handle_extra_e_fechado(tmp_path) -> None:
    fechados = []
    runtime = adquirir_instancia_unica(
        tmp_path / "laylay.py",
        sistema="nt",
        criar_mutex=lambda _nome: 42,
        fechar_mutex=fechados.append,
        obter_ultimo_erro=lambda: ERRO_MUTEX_JA_EXISTE,
    )

    assert runtime.adquirida is False
    assert fechados == [42]


def test_instancia_adquirida_libera_mutex_uma_unica_vez(tmp_path) -> None:
    fechados = []
    runtime = adquirir_instancia_unica(
        tmp_path / "laylay.py",
        sistema="nt",
        criar_mutex=lambda _nome: 84,
        fechar_mutex=fechados.append,
        obter_ultimo_erro=lambda: 0,
    )

    assert runtime.adquirida is True
    runtime.liberar()
    runtime.liberar()
    assert fechados == [84]


@pytest.mark.skipif(os.name != "nt", reason="mutex nomeado específico do Windows")
def test_mutex_windows_real_bloqueia_segunda_aquisicao_e_libera(tmp_path) -> None:
    identificador = tmp_path / "laylay.py"
    primeira = adquirir_instancia_unica(identificador)
    segunda = adquirir_instancia_unica(identificador)

    try:
        assert primeira.adquirida is True
        assert segunda.adquirida is False
    finally:
        primeira.liberar()

    terceira = adquirir_instancia_unica(identificador)
    try:
        assert terceira.adquirida is True
    finally:
        terceira.liberar()
