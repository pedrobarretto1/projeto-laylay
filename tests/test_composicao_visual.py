from __future__ import annotations

import pytest

from mente_laylay.integracao.composicao_visual import ComposicaoVisualLaylayRuntime


class _GameBarFake:
    def __init__(self):
        self.barras = []
        self.paradas = 0

    def conectado(self):
        return True

    def publicar_barra(self, visivel, texto=""):
        self.barras.append((visivel, texto))

    def parar(self):
        self.paradas += 1


class _AvatarFake:
    def __init__(self):
        self.paradas = 0

    def parar(self):
        self.paradas += 1


def test_composicao_visual_compartilha_gamebar_entre_avatar_e_barra(tmp_path) -> None:
    criacoes = {}
    gamebar = _GameBarFake()
    avatar = _AvatarFake()
    barra = object()

    def criar_gamebar(**kwargs):
        criacoes["gamebar"] = kwargs
        return gamebar

    def criar_avatar(**kwargs):
        criacoes["avatar"] = kwargs
        return avatar

    def criar_barra(**kwargs):
        criacoes["barra"] = kwargs
        return barra

    ambiente = {
        "LAYLAY_GAMEBAR_PORTA": "19001",
        "LAYLAY_BARRA_SEM_FOCO_JOGO": "0",
    }
    runtime = ComposicaoVisualLaylayRuntime(
        raiz_projeto=tmp_path,
        estado_getter=lambda: {"emotion": "feliz"},
        env_getter=lambda nome, padrao="": ambiente.get(nome, padrao),
        gamebar_factory=criar_gamebar,
        avatar_factory=criar_avatar,
        barra_factory=criar_barra,
        log=lambda *_: None,
    )

    criada = runtime.conectar_barra(
        processar_texto=lambda _texto: None,
        keyboard_mod=object(),
        hotkey="f10",
        modo_jogo_ativo=lambda: True,
    )

    assert criada is barra
    assert runtime.barra is barra
    assert criacoes["gamebar"]["porta"] == 19001
    assert criacoes["avatar"]["visual_externo_disponivel"]() is True
    assert criacoes["barra"]["estado_visual_cb"] == gamebar.publicar_barra
    assert criacoes["barra"]["visual_externo_disponivel"]() is True
    assert criacoes["barra"]["sobreposicao_sem_foco_jogo"] is False
    assert runtime.conectar_barra(
        processar_texto=lambda _texto: None,
        keyboard_mod=object(), hotkey="outra", modo_jogo_ativo=lambda: False,
    ) is barra


def test_composicao_visual_valida_porta_e_relata_configuracao_invalida(tmp_path) -> None:
    falhas, logs, capturado = [], [], {}

    def criar_gamebar(**kwargs):
        capturado.update(kwargs)
        return _GameBarFake()

    ComposicaoVisualLaylayRuntime(
        raiz_projeto=tmp_path,
        estado_getter=lambda: {},
        env_getter=lambda nome, padrao="": "porta-invalida"
        if nome == "LAYLAY_GAMEBAR_PORTA" else padrao,
        gamebar_factory=criar_gamebar,
        avatar_factory=lambda **_kwargs: _AvatarFake(),
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        log=logs.append,
    )

    assert capturado["porta"] == 18766
    assert falhas[0][0] == (
        "composicao_visual", "configuracao_laylay_gamebar_porta",
    )
    assert "usando 18766" in logs[0]


def test_composicao_visual_exige_conexao_da_barra_e_encerra_visuais(tmp_path) -> None:
    gamebar, avatar = _GameBarFake(), _AvatarFake()
    runtime = ComposicaoVisualLaylayRuntime(
        raiz_projeto=tmp_path,
        estado_getter=lambda: {},
        gamebar_factory=lambda **_kwargs: gamebar,
        avatar_factory=lambda **_kwargs: avatar,
        log=lambda *_: None,
    )

    with pytest.raises(RuntimeError, match="ainda não conectada"):
        _ = runtime.barra

    runtime.parar()

    assert avatar.paradas == 1
    assert gamebar.paradas == 1
