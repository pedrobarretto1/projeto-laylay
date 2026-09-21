from __future__ import annotations

from types import SimpleNamespace
from functools import partial

import pytest

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.porteiro_acoes import (
    texto_bloqueia_playlist_agora,
    texto_conversa_casual_sem_acao,
    texto_social_curto,
)
from mente_laylay.autonomia.processamento_resposta_ia import salvar_aprendizados_da_ia
from mente_laylay.autonomia.roteador_deterministico import (
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.cognicao.linguagem_aprendida import LinguagemAprendidaRuntime
from mente_laylay.memoria_mental.busca_youtube import normalizar_query_musical
from mente_laylay.integracao.composicao_entrada_interacao import (
    ComposicaoEntradaInteracaoRuntime,
)
from mente_laylay.integracao.registro_memoria_pessoas import (
    registrar_memoria_pessoas,
)
from mente_laylay.integracao.registro_iot import registrar_iot


class _MemoriaPessoasNula:
    def processar(self, _texto): return False
    def contexto_para_prompt(self, _texto): return ""
    def diagnostico(self): return {}
    def retrato_para_mente(self, _texto=""): return {}
    def reexecutar(self, _resultado, _texto): return False


class _IoTNulo:
    def detectar(self, _texto, _estado=None): return None
    def executar(self, _resultado, _texto=""): return {"handled": False}
    def retrato_para_mente(self, _texto=""): return {"dispositivos": []}


def _com_memoria(servicos=None):
    resultado = dict(servicos or {})
    resultado.setdefault("resolver_comando_natural", lambda _texto, _origem: (None, ""))
    resultado["_registro_memoria_pessoas_runtime"] = registrar_memoria_pessoas(
        _MemoriaPessoasNula()
    )
    resultado["_registro_iot_runtime"] = registrar_iot(_IoTNulo())
    return resultado


def test_deteccao_recebe_registro_filtrado_congelado_e_estado_vivo() -> None:
    capturado = {}
    estado = {"turno": 1}
    original = lambda texto: texto  # noqa: E731
    resolver_referencia = lambda referencia, categoria="": {  # noqa: E731
        "valor": "Lua de Neon da Anny",
        "categoria": categoria,
    }
    servicos = {
        "_normalizar_texto_com_apelidos": original,
        "_resolver_referencia_pessoal": resolver_referencia,
        "SEGREDO_FORA_DO_CONTRATO": "não reter",
    }
    detector = object()

    def deteccao_factory(**kwargs):
        capturado.update(kwargs)
        return detector

    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos=servicos,
        estado_mental_getter=lambda: estado,
        sites_diretos={"site": "https://example.com"},
        apps_map={"editor": "code"},
        deteccao_factory=deteccao_factory,
    )
    servicos["_normalizar_texto_com_apelidos"] = lambda _texto: "alterado"
    servicos["novo_servico"] = object()
    snapshot = capturado["namespace_getter"]()

    assert runtime.deteccao is detector
    assert snapshot["_normalizar_texto_com_apelidos"] is original
    assert snapshot["_resolver_referencia_pessoal"] is resolver_referencia
    assert "SEGREDO_FORA_DO_CONTRATO" not in snapshot
    assert "novo_servico" not in snapshot
    assert capturado["estado_getter"]() is estado
    estado["turno"] = 2
    assert capturado["estado_getter"]()["turno"] == 2


def test_composicao_real_resolve_musica_favorita_aprendida(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.sqlite"))
    salvar_aprendizados_da_ia(
        '{"fala":"Entendi.","comandos":[]}',
        memoria,
        "minha música favorita é Lua de Neon da Anny",
    )
    normalizar = lambda texto: str(texto or "").casefold().strip()  # noqa: E731
    linguagem = LinguagemAprendidaRuntime(
        memoria_sqlite=memoria,
        normalizar_texto=normalizar,
        texto_social_curto=lambda _texto: False,
        falar=lambda *_args: None,
    )
    estado = {"turno_atual": {"autoriza_execucao": True}}
    servicos = _com_memoria({
        "_normalizar_texto_com_apelidos": linguagem.normalizar_com_apelidos,
        "_resolver_referencia_pessoal": linguagem.resolver_referencia_pessoal,
        "_texto_conversa_casual_sem_acao": texto_conversa_casual_sem_acao,
        "_texto_bloqueia_playlist_agora": texto_bloqueia_playlist_agora,
        "_texto_social_curto": texto_social_curto,
        "_ignorar_token_solto": lambda _texto: False,
        "_fluxo_prioritario_da_ia": lambda _texto: False,
        "_texto_expresso_melhor_no_deterministico": partial(
            texto_expresso_melhor_no_deterministico,
            normalizar_texto=normalizar,
        ),
        "_texto_depende_de_contexto": lambda _texto: False,
        "_limpar_destino_pc_b": lambda texto: texto,
        "_target_from_params": lambda _params, _texto: "pc_a",
        "_limpar_nome_playlist": lambda texto: str(texto).strip(),
        "_musica_estado_get": lambda *_args: "",
        "_contexto_musical_ativo": lambda: False,
        "_detectar_playlist_nome_direto": lambda _texto: "",
        "_normalizar_query_musical": partial(
            normalizar_query_musical,
            normalizar_texto_cb=normalizar,
        ),
    })
    composicao = ComposicaoEntradaInteracaoRuntime(
        servicos=servicos,
        estado_mental_getter=lambda: estado,
        sites_diretos={},
        apps_map={},
    )

    resultado = composicao.deteccao.detectar("coloca minha música favorita")

    assert resultado["intent"] == "MUSIC_SEARCH"
    assert resultado["params"]["query"] == "Lua de Neon da Anny"
    assert resultado["params"]["referencia_pessoal_fonte"] == "memoria_duravel_confirmada"


def test_interacao_conecta_tarde_filtra_servicos_e_preserva_estado_chat() -> None:
    capturado = {}
    estado_chat = {"messages": ["antes"], "current_emotion": "calma"}
    executar_original = lambda *_: True  # noqa: E731
    servicos = _com_memoria({
        "executar_intencao": executar_original,
        "_estado_compartilhado_runtime": object(),
        "SEGREDO_FORA_DO_CONTRATO": "não reter",
    })
    comandos = object()
    chat = object()

    def comandos_factory(**kwargs):
        capturado["comandos"] = kwargs
        return comandos

    def chat_factory(**kwargs):
        capturado["chat"] = kwargs
        return chat

    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos={},
        estado_mental_getter=dict,
        sites_diretos={},
        apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
        comandos_factory=comandos_factory,
        chat_factory=chat_factory,
    )
    conectados = runtime.conectar(
        servicos=servicos,
        loop_getter=lambda: "loop-vivo",
        estado_chat_getter=lambda: estado_chat,
        memoria_sqlite="memoria",
    )
    servicos["executar_intencao"] = lambda *_: False
    snapshot = capturado["comandos"]["namespace_getter"]()

    assert conectados == (comandos, chat)
    assert snapshot["executar_intencao"] is executar_original
    assert "SEGREDO_FORA_DO_CONTRATO" not in snapshot
    assert capturado["comandos"]["loop_getter"]() == "loop-vivo"
    assert capturado["chat"]["memoria_sqlite"] == "memoria"
    estado_chat["messages"].append("depois")
    assert capturado["chat"]["estado_getter"]()["messages"] == ["antes", "depois"]
    assert runtime.conectar(
        servicos={}, loop_getter=lambda: None,
        estado_chat_getter=dict, memoria_sqlite=None,
    ) == (comandos, chat)


def test_registros_expostos_nao_incluem_nomes_estranhos() -> None:
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos=_com_memoria({
            "_texto_social_curto": object(),
            "qualquer_coisa": object(),
        }),
        estado_mental_getter=dict,
        sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
        comandos_factory=lambda **_kwargs: object(),
        chat_factory=lambda **_kwargs: object(),
    )
    runtime.conectar(
        servicos=_com_memoria({
            "_texto_social_curto": object(),
            "qualquer_coisa": object(),
        }),
        loop_getter=lambda: None, estado_chat_getter=dict,
        memoria_sqlite=None,
    )

    assert runtime.servicos_deteccao_registrados == ("_texto_social_curto",)
    assert runtime.servicos_interacao_registrados == (
        "_texto_social_curto", "resolver_comando_natural",
    )
    assert runtime.servicos_tipados_registrados == ("iot", "memoria_pessoas")


def test_composicao_entrega_consulta_natural_ao_runtime_prioritario() -> None:
    executadas = []

    class Estado:
        mental = {
            "turno_atual": {
                "modalidade": "pergunta",
                "modalidade_geral": "pergunta",
                "autoriza_execucao": False,
            },
        }

    servicos = _com_memoria({
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "resolver_comando_natural": lambda _texto, _origem: ({
            "intent": "PLAYLIST_LIST", "params": {"nome_playlist": "trap"},
        }, "recurso"),
        "executar_intencao": lambda intent, _texto: executadas.append(intent) or True,
        "_estado_compartilhado_runtime": Estado(),
    })
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos=servicos,
        estado_mental_getter=lambda: Estado.mental,
        sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
        chat_factory=lambda **_kwargs: object(),
    )
    comandos, _chat = runtime.conectar(
        servicos=servicos, loop_getter=lambda: None,
        estado_chat_getter=dict, memoria_sqlite=None,
    )

    assert comandos.processar_prioritarios("o que tem em trap?") is True
    assert executadas == [{
        "intent": "PLAYLIST_LIST",
        "params": {"nome_playlist": "trap"},
    }]
    assert "resolver_comando_natural" in runtime.servicos_interacao_registrados


def test_composicao_entrega_caixa_de_entrada_ao_fluxo_prioritario() -> None:
    recebidos = []

    class Caixa:
        def processar(self, texto):
            recebidos.append(texto)
            return True

    caixa = Caixa()
    servicos = _com_memoria({"_caixa_entrada_pessoal_runtime": caixa})
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos={},
        estado_mental_getter=dict,
        sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
        chat_factory=lambda **_kwargs: object(),
    )
    comandos, _chat = runtime.conectar(
        servicos=servicos,
        loop_getter=lambda: None,
        estado_chat_getter=dict,
        memoria_sqlite=None,
    )

    assert comandos.processar_prioritarios("anota essa ideia") is True
    assert recebidos == ["anota essa ideia"]
    assert "_caixa_entrada_pessoal_runtime" in runtime.servicos_interacao_registrados


def test_composicao_aguarda_resumo_e_publica_resultado_antes_de_encerrar_turno(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chamadas_resumo: list[str] = []
    registros: list[tuple[bool, str]] = []
    esperas: list[float | None] = []
    callbacks: list[object] = []
    loop = object()

    async def resumir() -> bool:
        chamadas_resumo.append("executado")
        return True

    class FuturoControlado:
        def result(self, timeout=None):
            esperas.append(timeout)
            # O teste não substitui a habilidade compartilhada; apenas faz o
            # papel do agendamento entre threads. A corrotina ainda é fechada
            # abaixo porque este futuro controlado não possui um event loop.
            corrotina.close()
            chamadas_resumo.append("agendado")
            return True

        def add_done_callback(self, callback):
            callbacks.append(callback)

    corrotina = None

    def agendar(recebida, loop_recebido):
        nonlocal corrotina
        assert loop_recebido is loop
        corrotina = recebida
        return FuturoControlado()

    monkeypatch.setattr(
        "mente_laylay.autonomia.comandos_imediatos."
        "asyncio.run_coroutine_threadsafe",
        agendar,
    )
    servicos = _com_memoria({
        "_estado_compartilhado_runtime": SimpleNamespace(mental={}),
        "resumir_pagina_ou_video": resumir,
        "falar_com_lipsync": lambda *_args: None,
        "_registrar_resultado_execucao": (
            lambda _intent, _texto, executou, **kwargs:
            registros.append((executou, kwargs.get("status", "")))
        ),
    })
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos=servicos,
        estado_mental_getter=dict,
        sites_diretos={},
        apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
        chat_factory=lambda **_kwargs: object(),
    )
    comandos, _chat = runtime.conectar(
        servicos=servicos,
        loop_getter=lambda: loop,
        estado_chat_getter=dict,
        memoria_sqlite=None,
    )

    assert comandos.processar_prioritarios("Resume a página atual") is True
    assert esperas == [45.0]
    assert callbacks == []
    assert chamadas_resumo == ["agendado"]
    assert registros == [(True, "resumo_concluido")]
    assert "resumir_pagina_ou_video" in runtime.servicos_interacao_registrados


def test_composicao_falha_cedo_sem_memoria_de_pessoas_obrigatoria() -> None:
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos={}, estado_mental_getter=dict, sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
    )

    try:
        runtime.conectar(
            servicos={}, loop_getter=lambda: None,
            estado_chat_getter=dict, memoria_sqlite=None,
        )
    except RuntimeError as erro:
        assert "memória de pessoas" in str(erro)
    else:
        raise AssertionError("a composição aceitou uma dependência obrigatória ausente")


def test_composicao_rejeita_contrato_incompleto_antes_da_conversa() -> None:
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos={}, estado_mental_getter=dict, sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
    )

    try:
        runtime.conectar(
            servicos={"_registro_memoria_pessoas_runtime": object()},
            loop_getter=lambda: None, estado_chat_getter=dict, memoria_sqlite=None,
        )
    except RuntimeError as erro:
        assert "operações ausentes" in str(erro)
    else:
        raise AssertionError("a composição aceitou um contrato incompleto")


def test_composicao_falha_cedo_sem_iot_obrigatorio() -> None:
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos={}, estado_mental_getter=dict, sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
    )
    servicos = _com_memoria()
    servicos.pop("_registro_iot_runtime")

    with pytest.raises(RuntimeError, match="IoT"):
        runtime.conectar(
            servicos=servicos, loop_getter=lambda: None,
            estado_chat_getter=dict, memoria_sqlite=None,
        )


def test_composicao_rejeita_contrato_iot_incompleto() -> None:
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos={}, estado_mental_getter=dict, sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
    )
    servicos = _com_memoria()
    servicos["_registro_iot_runtime"] = object()

    with pytest.raises(RuntimeError, match="operações ausentes"):
        runtime.conectar(
            servicos=servicos, loop_getter=lambda: None,
            estado_chat_getter=dict, memoria_sqlite=None,
        )


def test_composicao_falha_cedo_sem_coordenador_canonico() -> None:
    runtime = ComposicaoEntradaInteracaoRuntime(
        servicos={}, estado_mental_getter=dict, sites_diretos={}, apps_map={},
        deteccao_factory=lambda **_kwargs: object(),
    )
    servicos = _com_memoria()
    servicos.pop("resolver_comando_natural")

    with pytest.raises(RuntimeError, match="coordenador canônico"):
        runtime.conectar(
            servicos=servicos, loop_getter=lambda: None,
            estado_chat_getter=dict, memoria_sqlite=None,
        )
