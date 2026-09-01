"""RT1 — prova de identidade do bootstrap acústico da Laylay.

Objetivo:
- NÃO testa ainda VAD/STT nem a corrida de ownership.
- Prova que o catálogo de serviços usado pelo bootstrap de produção aponta
  para os MESMOS objetos montados pelo root `laylay.py`.
- Prova que as únicas bordas que precisaremos controlar no próximo teste
  (sounddevice / numpy / model_factory) podem ser substituídas no próprio
  objeto do root antes de `executar()`.

Se este arquivo ficar verde, o próximo teste pode usar o serviço
"Laylay-Ouvido" do catálogo sem remontar o grafo interno.
"""

from __future__ import annotations

import importlib


def _carregar_root():
    return importlib.import_module("laylay")


def _catalogo(root):
    composicao = getattr(root, "_composicao_servicos_runtime", None)
    assert composicao is not None, (
        "root não publicou _composicao_servicos_runtime"
    )
    catalogo = composicao.catalogo_threads()
    assert isinstance(catalogo, dict)
    return catalogo


def test_rt1_bootstrap_publica_o_mesmo_ouvido_montado_pelo_root():
    root = _carregar_root()
    catalogo = _catalogo(root)

    ouvido = getattr(root, "_ouvido_whisper_runtime", None)
    assert ouvido is not None, "root não publicou _ouvido_whisper_runtime"

    target = catalogo.get("Laylay-Ouvido")
    assert callable(target), "catálogo não publicou o serviço Laylay-Ouvido"

    assert getattr(target, "__self__", None) is ouvido, (
        "Laylay-Ouvido não aponta para a instância de OuvidoWhisperRuntime "
        "montada pelo próprio root"
    )
    assert getattr(target, "__func__", None) is getattr(type(ouvido), "executar"), (
        "Laylay-Ouvido não aponta para OuvidoWhisperRuntime.executar"
    )


def test_rt1_bootstrap_publica_o_mesmo_diretor_presenca_montado_pelo_root():
    root = _carregar_root()
    catalogo = _catalogo(root)

    diretor = getattr(root, "_diretor_presenca_runtime", None)
    assert diretor is not None, "root não publicou _diretor_presenca_runtime"

    target = catalogo.get("Laylay-Diretor-Presença")
    assert callable(target), (
        "catálogo não publicou o serviço Laylay-Diretor-Presença"
    )

    assert getattr(target, "__self__", None) is diretor, (
        "Laylay-Diretor-Presença não aponta para a instância montada pelo root"
    )
    assert getattr(target, "__func__", None) is getattr(type(diretor), "executar"), (
        "Laylay-Diretor-Presença não aponta para DiretorPresencaRuntime.executar"
    )


def test_rt1_ouvido_do_root_entrega_na_entrada_de_voz_do_root():
    root = _carregar_root()

    ouvido = getattr(root, "_ouvido_whisper_runtime", None)
    entrada_voz = getattr(root, "_processar_entrada_voz", None)

    assert ouvido is not None
    assert callable(entrada_voz)

    assert getattr(ouvido, "processar_texto", None) is entrada_voz, (
        "Ouvido do root não está ligado à entrada de voz publicada pelo root; "
        "um teste acústico poderia atravessar outro caminho"
    )


def test_rt1_dependencias_externas_podem_ser_controladas_no_mesmo_objeto():
    root = _carregar_root()
    catalogo = _catalogo(root)

    ouvido = root._ouvido_whisper_runtime
    target = catalogo["Laylay-Ouvido"]

    antigos = (
        getattr(ouvido, "sd", None),
        getattr(ouvido, "np", None),
        getattr(ouvido, "model_factory", None),
    )

    fake_sd = object()
    fake_np = object()

    def fake_model_factory(*_args, **_kwargs):
        return object()

    try:
        ouvido.sd = fake_sd
        ouvido.np = fake_np
        ouvido.model_factory = fake_model_factory

        assert getattr(target, "__self__", None) is ouvido
        assert target.__self__.sd is fake_sd
        assert target.__self__.np is fake_np
        assert target.__self__.model_factory is fake_model_factory
    finally:
        ouvido.sd, ouvido.np, ouvido.model_factory = antigos
