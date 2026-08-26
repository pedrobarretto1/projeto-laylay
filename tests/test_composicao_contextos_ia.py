from __future__ import annotations

import pytest

from mente_laylay.integracao.composicao_contextos_ia import (
    ComposicaoContextosIARuntime,
    _DISPATCHER_GRUPOS,
    _EXECUCAO,
    _FINALIZACAO_GRUPOS,
)
from mente_laylay.integracao.registro_conversa_llm import (
    PedidoModelo,
    ResultadoModelo,
)
from tests.fakes_navegador import NavegadorLeituraFake, NavegadorOperacoesFake
from tests.fakes_visao_jogo import VisaoJogoAnaliseFake, VisaoJogoLeituraFake


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


class _MusicaOperacoesFake:
    def __init__(self, estado=None): self.estado_mutavel = estado if estado is not None else {}
    def criar_playlist(self, nome): return {"ok": True, "criada": True, "nome": nome}
    def apagar_playlist(self, _nome): return True
    def adicionar_faixa(self, *_args): return True
    def mover_faixa(self, origem, destino, _musica=""): return {"ok": True, "origem": origem, "destino": destino}
    def tocar_playlist(self, _nome): return True
    def preparar_shuffle(self, _nome): return {"url": "https://youtube.com/1"}
    def primeira_url(self, _nome): return "https://youtube.com/1"
    def avancar_proxima(self): return True
    def voltar_anterior(self): return True
    def definir_ultima_playlist(self, nome): self.estado_mutavel["ultima_playlist"] = nome
    def definir_ultima_url(self, url): self.estado_mutavel["ultima_url"] = url
    def faixa_atual(self): return {}
    def copiar_curadoria(self, _origem, _musica, _destino): return {"ok": True}
    def estado(self): return {"playlist_ativa": ""}
    def diagnostico(self): return {"mutacao_disponivel": True}


class _ModeloFake:
    def executar(self, pedido: PedidoModelo) -> ResultadoModelo:
        assert isinstance(pedido, PedidoModelo)
        return ResultadoModelo("resposta tipada", True)

    def diagnostico(self):
        return {"disponivel": True, "autoriza_execucao": False}


def _servicos_completos():
    nomes = {
        "_resumo_mente_integrada_para_prompt",
        "get_status_humor_prompt",
        "_executar_captura_tela_intent",
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

    class PromptFake:
        def preparar_pacote(self, _texto):
            from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
            return PacotePrompt(())
        def diagnostico(self): return {"disponivel": True}

    prompt = PromptFake()

    def prompt_factory(**kwargs):
        capturado["prompt"] = kwargs
        return prompt
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
        musica_operacoes=_MusicaOperacoesFake(musica),
        navegador_leitura=NavegadorLeituraFake(),
        navegador_operacoes=NavegadorOperacoesFake(),
        visao_jogo_leitura=VisaoJogoLeituraFake(),
        visao_jogo_analise=VisaoJogoAnaliseFake(),
        modelo_llm=_ModeloFake(),
        gmail_cache_getter=lambda: estado["gmail"],
        falhas_getter=lambda: estado["falhas"],
        verificar_fala_turno=lambda *_args, **_kwargs: True,
        executar_conteudo_cb=lambda *_args, **_kwargs: False,
        mapa_habilidades_prompt=lambda texto, **_kwargs: f"habilidades:{texto}",
        mapa_recursos_prompt=lambda texto: f"recursos:{texto}",
        registrar_tamanho_prompt=lambda *_args: None,
        registrar_falha=lambda *_args, **_kwargs: None,
        prompt_factory=prompt_factory,
        exec_factory=exec_factory,
        dispatcher_factory=dispatcher_factory,
        finalizacao_factory=finalizacao_factory,
        log=lambda *_: None,
    )
    return runtime, capturado, estado, musica, (prompt, execucao, dispatcher, finalizacao)


def test_composicao_cria_quatro_contextos_e_descarta_servicos_externos() -> None:
    runtime, capturado, _, _, retornos = _montar()

    prompt, execucao, dispatcher, finalizacao = retornos
    assert runtime.prompt.servico is prompt
    assert (runtime.execucao, runtime.dispatcher, runtime.finalizacao) == (
        execucao, dispatcher, finalizacao,
    )
    assert "SEGREDO_FORA_DO_CONTEXTO" not in runtime.servicos_registrados
    assert capturado["prompt"]["base_system_prompt"] == "prompt base"
    assert callable(capturado["prompt"]["mapa_habilidades_prompt"])
    assert callable(capturado["prompt"]["mapa_recursos_prompt"])
    assert callable(capturado["prompt"]["registrar_tamanho_prompt"])
    assert callable(capturado["dispatcher"]["registrar_falha"])
    assert callable(capturado["finalizacao"]["registrar_falha"])
    assert capturado["prompt"]["formatar_playlists"]() == (
        "Playlists salvas: 'rock' (0)."
    )
    contexto_exec = capturado["execucao"]["contexto_getter"]()
    assert contexto_exec["_registro_musica_leitura_runtime"].indice_usuario() == {
        "rock": 0
    }
    assert "_listar_playlists_salvas" not in contexto_exec
    assert "_registro_visao_jogo_leitura_runtime" in contexto_exec
    assert "_registro_visao_jogo_analise_runtime" in contexto_exec
    assert "_executar_visao_jogo_intent" not in contexto_exec
    assert "_formatar_playlists_para_prompt" not in runtime.servicos_registrados
    assert capturado["dispatcher"]["arquivos"]["executar_intencao"] is not None
    assert capturado["finalizacao"]["autoaprimoramento"][
        "MAX_TENTATIVAS_AUTOCORRECAO"
    ] == 2
    resultado = capturado["finalizacao"]["ia"]["modelo_llm"].executar(
        PedidoModelo.criar([], com_tools=False)
    )
    assert resultado.texto == "resposta tipada"
    assert "enviar_mensagem" not in capturado["finalizacao"]["ia"]
    assert "enviar_mensagem" not in runtime.servicos_registrados


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
    contexto_exec["_registro_musica_operacoes_runtime"].definir_ultima_playlist("rock")
    assert musica == {"ultima_playlist": "rock"}

    capturar = capturado["dispatcher"]["percepcao"]["_executar_captura_tela_intent"]
    nome, args, kwargs = capturar("tela")
    assert nome == "_executar_captura_tela_intent"
    assert args == ("tela",)
    assert kwargs == {"registrar_memoria": True}
    percepcao = capturado["dispatcher"]["percepcao"]
    assert "_registro_visao_jogo_leitura_runtime" in percepcao
    assert "_registro_visao_jogo_analise_runtime" in percepcao
    assert "_executar_visao_jogo_intent" not in percepcao


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
                musica_operacoes=_MusicaOperacoesFake(),
                navegador_leitura=NavegadorLeituraFake(),
                navegador_operacoes=NavegadorOperacoesFake(),
                visao_jogo_leitura=VisaoJogoLeituraFake(),
                visao_jogo_analise=VisaoJogoAnaliseFake(),
                modelo_llm=_ModeloFake(),
            gmail_cache_getter=lambda: [],
            falhas_getter=lambda: {},
            verificar_fala_turno=lambda *_: True,
            executar_conteudo_cb=lambda *_: False,
        )
