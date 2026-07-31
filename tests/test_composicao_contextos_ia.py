from __future__ import annotations

import pytest

from mente_laylay.integracao.composicao_contextos_ia import (
    ComposicaoContextosIARuntime,
    _DISPATCHER_GRUPOS,
    _EXECUCAO,
    _FINALIZACAO_GRUPOS,
)


class _MusicaLeituraFake:
    def listar_usuario(self): return "rock"
    def consultar_usuario(self, nome): return {"ok": True, "name": nome, "total": 0}
    def contar_usuario(self, _nome): return 0
    def formatar_prompt(self): return "Playlists salvas: 'rock' (0)."
    def retrato_usuario(self, _texto=""): return {"playlists": [{"nome": "rock", "total": 0}], "detalhe": {}}
    def indice_usuario(self): return {"rock": 0}
    def listar_laylay(self, _nome=""): return "Sem curadorias."
    def retrato_laylay(self, _texto=""): return {"playlists": [], "detalhe": {}}
    def estado(self): return {"playlist_ativa": ""}
    def diagnostico(self): return {"somente_leitura": True}


def _servicos_completos():
    nomes = {
        "_resumo_mente_integrada_para_prompt",
        "get_status_humor_prompt",
        "_executar_captura_tela_intent",
        "_executar_visao_jogo_intent",
    }
    nomes.update(_EXECUCAO)
    for grupo in (*_DISPATCHER_GRUPOS.values(), *_FINALIZACAO_GRUPOS.values()):
        nomes.update(grupo)
    return {nome: (lambda *args, _nome=nome, **kwargs: (_nome, args, kwargs)) for nome in nomes}


def _montar():
    capturado = {}
    servicos = _servicos_completos()
    servicos["APPS_MAP"] = {"code": "code"}
    servicos["MAX_TENTATIVAS_AUTOCORRECAO"] = 2
    servicos["SEGREDO_FORA_DO_CONTEXTO"] = "não reter"
    estado = {
        "messages": [{"role": "user", "content": "oi"}],
        "current_emotion": "calma",
        "emotion_level": 1,
        "humor_level": 0,
        "turno_atual": {"modalidade": "conversa"},
        "playlists": {"rock": []},
        "gmail": [{"uid": "1"}],
        "falhas": {},
        "aba": ("Inicial", "https://example.com"),
    }
    musica = {}

    def factory(nome):
        retorno = object()

        def criar(**kwargs):
            capturado[nome] = kwargs
            return retorno
        return criar, retorno

    prompt_factory, prompt = factory("prompt")
    exec_factory, execucao = factory("execucao")
    dispatcher_factory, dispatcher = factory("dispatcher")
    finalizacao_factory, finalizacao = factory("finalizacao")
    runtime = ComposicaoContextosIARuntime(
        memoria_sqlite=object(),
        base_system_prompt="prompt base",
        servicos=servicos,
        messages_getter=lambda: estado["messages"],
        conversa_getter=lambda nome, padrao=None: estado.get(nome, padrao),
        mente_getter=lambda: {"turno_atual": estado["turno_atual"]},
        aba_getter=lambda: estado["aba"],
        musica_leitura=_MusicaLeituraFake(),
        gmail_cache_getter=lambda: estado["gmail"],
        falhas_getter=lambda: estado["falhas"],
        musica_estado_set=lambda chave, valor: musica.__setitem__(chave, valor),
        verificar_fala_turno=lambda *_args, **_kwargs: True,
        executar_conteudo_cb=lambda *_args, **_kwargs: False,
        executar_legado_cb=lambda *_args, **_kwargs: False,
        mapa_habilidades_prompt=lambda texto, **_kwargs: f"habilidades:{texto}",
        mapa_recursos_prompt=lambda texto: f"recursos:{texto}",
        prompt_factory=prompt_factory,
        exec_factory=exec_factory,
        dispatcher_factory=dispatcher_factory,
        finalizacao_factory=finalizacao_factory,
        log=lambda *_: None,
    )
    return runtime, capturado, estado, musica, (prompt, execucao, dispatcher, finalizacao)


def test_composicao_cria_quatro_contextos_e_descarta_servicos_externos() -> None:
    runtime, capturado, _, _, retornos = _montar()

    assert (runtime.prompt, runtime.execucao, runtime.dispatcher, runtime.finalizacao) == retornos
    assert "SEGREDO_FORA_DO_CONTEXTO" not in runtime.servicos_registrados
    assert capturado["prompt"]["base_system_prompt"] == "prompt base"
    assert callable(capturado["prompt"]["mapa_habilidades_prompt"])
    assert callable(capturado["prompt"]["mapa_recursos_prompt"])
    assert capturado["prompt"]["formatar_playlists"]() == (
        "Playlists salvas: 'rock' (0)."
    )
    contexto_exec = capturado["execucao"]["contexto_getter"]()
    assert contexto_exec["_registro_musica_leitura_runtime"].indice_usuario() == {
        "rock": 0
    }
    assert "_listar_playlists_salvas" not in contexto_exec
    assert "_formatar_playlists_para_prompt" not in runtime.servicos_registrados
    assert capturado["dispatcher"]["arquivos"]["executar_intencao"] is not None
    assert capturado["finalizacao"]["autoaprimoramento"][
        "MAX_TENTATIVAS_AUTOCORRECAO"
    ] == 2


def test_estados_dos_contextos_continuam_vivos() -> None:
    _, capturado, estado, _, _ = _montar()
    estado["messages"] = [{"role": "user", "content": "mudou"}]
    estado["current_emotion"] = "animada"
    estado["aba"] = ("Nova aba", "https://nova.example")
    estado["falhas"] = {"llm": 1}

    prompt = capturado["prompt"]["estado_getter"]()
    dispatcher = capturado["dispatcher"]["estado_getter"]()
    finalizacao = capturado["finalizacao"]["estado_getter"]()
    assert prompt["messages"][0]["content"] == "mudou"
    assert prompt["aba_titulo_atual"] == "Nova aba"
    assert dispatcher["current_emotion"] == "animada"
    assert finalizacao["_falhas_consecutivas"] == {"llm": 1}


def test_contexto_execucao_mantem_setter_musical_e_captura_visual_segura() -> None:
    _, capturado, _, musica, _ = _montar()
    contexto_exec = capturado["execucao"]["contexto_getter"]()
    contexto_exec["set_ultima_playlist"]("rock")
    assert musica == {"ultima_playlist": "rock"}

    capturar = capturado["dispatcher"]["percepcao"]["_executar_captura_tela_intent"]
    nome, args, kwargs = capturar("tela")
    assert nome == "_executar_captura_tela_intent"
    assert args == ("tela",)
    assert kwargs == {"registrar_memoria": True}


def test_composicao_falha_cedo_quando_servico_obrigatorio_esta_ausente() -> None:
    servicos = _servicos_completos()
    servicos.pop("falar_com_lipsync")
    with pytest.raises(RuntimeError, match="falar_com_lipsync"):
        ComposicaoContextosIARuntime(
            memoria_sqlite=object(),
            base_system_prompt="base",
            servicos=servicos,
            messages_getter=lambda: [],
            conversa_getter=lambda _nome, padrao=None: padrao,
            mente_getter=lambda: {},
            aba_getter=lambda: ("", ""),
            musica_leitura=_MusicaLeituraFake(),
            gmail_cache_getter=lambda: [],
            falhas_getter=lambda: {},
            musica_estado_set=lambda *_: None,
            verificar_fala_turno=lambda *_: True,
            executar_conteudo_cb=lambda *_: False,
            executar_legado_cb=lambda *_: False,
        )
