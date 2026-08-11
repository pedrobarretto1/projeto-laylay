import time

from mente_laylay.autonomia.roteador_deterministico import detectar_fechar_alvo
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.coordenador_intencao import executar_fluxo_intencao
from mente_laylay.memoria_mental.contexto_imediato import resolver_comando_janela_contextual
from mente_laylay.memoria_mental.musica_conversacional_runtime import (
    MusicaConversacionalRuntime,
)
from mente_laylay.memoria_mental.pendencia_acao import (
    CHAVE_PENDENCIA_ACAO,
    PendenciaAcaoRuntime,
)


def _pendencia(estado: dict) -> PendenciaAcaoRuntime:
    def atualizar(mutador):
        novo = mutador(dict(estado))
        estado.clear()
        estado.update(novo)
        return dict(estado)

    return PendenciaAcaoRuntime(
        estado_getter=lambda: estado,
        estado_atualizar=atualizar,
        log=lambda *_args: None,
    )


def test_fecha_programa_que_acabou_de_abrir_resolve_ultima_janela() -> None:
    estado = {
        "ultima_acao_intent": "APP_OPEN",
        "ultima_acao_params": {"nome_app": "bloco de notas"},
        "ultimo_app_janela": "bloco de notas",
    }

    assert resolver_comando_janela_contextual(
        "fecha o programa que voce acabou de abrir",
        mente_integrada_estado=estado,
    ) == {
        "intent": "CLOSE_APP",
        "params": {
            "nome_app": "bloco de notas",
            "referencia_contextual": True,
        },
    }


def test_detector_nao_trata_referencia_de_janela_como_nome_literal() -> None:
    assert detectar_fechar_alvo(
        "fecha o programa que voce acabou de abrir",
        params_cb=lambda **params: params,
        sites_diretos=set(),
        apps_map={},
    ) is None


def test_roteador_completo_bloqueia_iot_negado_mesmo_com_detector_permissivo() -> None:
    chamadas = []

    def detector(texto, _estado):
        chamadas.append(texto)
        return {"intent": "IOT_CONTROL", "params": {"acao": "desligar", "alvo": "lampada_quarto"}}

    ctx = {
        "detectar_intencao_iot": detector,
        "normalizar_texto": lambda texto: str(texto).casefold().strip(),
        "mente_integrada_estado": {},
    }
    assert detectar_intencao_deterministica_mente("não desliga a luz", ctx) is None
    assert chamadas


def test_roteador_completo_bloqueia_pergunta_sobre_como_controlar_iot() -> None:
    ctx = {
        "detectar_intencao_iot": lambda *_: {
            "intent": "IOT_CONTROL",
            "params": {"acao": "desligar", "alvo": "lampada_quarto"},
        },
        "normalizar_texto": lambda texto: str(texto).casefold().strip(),
        "mente_integrada_estado": {},
    }
    assert detectar_intencao_deterministica_mente(
        "como eu faria para desligar a luz?", ctx
    ) is None


def test_nome_da_faixa_resolve_pendencia_de_musica_sem_alvo() -> None:
    falas = []
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda fala, *_: falas.append(fala),
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )

    assert runtime.responder_pedido_direcao("coloca uma música") is True
    assert runtime.processar_confirmacao("Remember The Time") is True
    assert execucoes[-1][0] == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "Remember The Time", "origem": "continuacao_busca"},
    }


def test_vontade_natural_de_ouvir_musica_cria_pendencia_sem_inventar_playlist() -> None:
    falas = []
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda fala, *_: falas.append(fala),
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )

    assert runtime.responder_pedido_direcao("eu queria ouvir uma música na verdade") is True
    assert execucoes == []
    assert "qual" in falas[-1].casefold()

    assert runtime.processar_confirmacao("Remember The Time") is True
    assert execucoes[-1][0] == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "Remember The Time", "origem": "continuacao_busca"},
    }


def test_novo_comando_iot_nao_vira_titulo_de_musica_pendente() -> None:
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda *_: None,
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )
    runtime.responder_pedido_direcao("coloca uma música")
    assert runtime.processar_confirmacao("liga a luz") is False
    assert execucoes == []


def test_agradecimento_nao_vira_titulo_de_musica_pendente() -> None:
    execucoes = []
    estado: dict = {}
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda *_: None,
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )
    runtime.responder_pedido_direcao("coloca uma música")

    for agradecimento in ("obrigado lay", "valeu Laylay", "perfeito"):
        assert runtime.processar_confirmacao(agradecimento) is False
    assert execucoes == []


def test_execucao_musical_confirmada_invalida_copia_local_da_pendencia() -> None:
    estado = {}
    execucoes = []
    runtime = MusicaConversacionalRuntime(
        estado_mental_getter=lambda: estado,
        normalizar_texto=lambda texto: str(texto).casefold().strip(),
        falar=lambda *_: None,
        registrar_mente_curta=lambda *_args, **_kwargs: None,
        executar_intencao=lambda resultado, texto: execucoes.append((resultado, texto)) or True,
        registrar_resultado_execucao=lambda *_args, **_kwargs: None,
        pendencia_runtime=_pendencia(estado),
    )
    runtime.responder_pedido_direcao("coloca uma música")
    estado.update({
        "ultima_acao_intent": "MUSIC_SEARCH",
        "ultima_acao_ts": time.time(),
        "ultima_acao_contrato": {
            "intent": "MUSIC_SEARCH",
            "executou": True,
            "confirmado": True,
        },
    })

    assert runtime.processar_confirmacao("obrigado lay") is False
    assert estado.get(CHAVE_PENDENCIA_ACAO, {}) == {}
    assert execucoes == []


def test_mencao_iot_sem_autorizacao_e_respondida_sem_roteador_nem_llm() -> None:
    falas = []
    chamadas_roteador = []
    namespace = {
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "detectar_intencao_deterministica": lambda texto: chamadas_roteador.append(texto),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("como eu faria para desligar a luz?") is True
    assert "não alterei nada" in falas[-1]
    assert chamadas_roteador == []

    assert runtime.processar_prioritarios("não desliga a luz") is True
    assert falas[-1] == "Pode deixar. Não vou alterar a luz."
    assert chamadas_roteador == []

    assert runtime.processar_prioritarios(
        "Talvez fosse legal desligar a luz."
    ) is True
    assert "possibilidade" in falas[-1]
    assert "deixei a luz como está" in falas[-1]
    assert chamadas_roteador == []


def test_recusa_musical_e_instrucao_de_exclusao_nao_caem_na_llm() -> None:
    falas = []
    bloqueios = []
    namespace = {
        "falar_com_lipsync": lambda fala, *_: falas.append(fala),
        "_bloquear_playlist_temporariamente": lambda segundos: bloqueios.append(segundos),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("Não coloca música agora.") is True
    assert falas[-1] == "Pode deixar, não vou tocar nada agora."
    assert bloqueios == [600.0]

    assert runtime.processar_prioritarios(
        "Como eu faria para apagar uma pasta?"
    ) is True
    assert "envio para a lixeira" in falas[-1]
    assert "restaurar" in falas[-1]
    assert "permanente" not in falas[-1]


def test_coordenador_nao_classifica_segmento_iot_amputado_da_fala_original() -> None:
    assert executar_fluxo_intencao(
        "desligar a luz",
        "pre-ia",
        {},
        texto_original="como eu faria para desligar a luz?",
    ) is False
