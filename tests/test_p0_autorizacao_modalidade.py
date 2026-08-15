# -*- coding: utf-8 -*-
"""P0.1 — regressões de autorização/modalidade no caminho real da Laylay."""

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)

NAO_EXECUTAR = (
    "Me explica como pausar uma música sem pausar agora.",
    "Abrir o Opera é uma boa ideia?",
    "Maximizar uma janela muda a resolução?",
    "Estou apenas escrevendo: abre o Opera.",
    "A palavra fecha não é um pedido para fechar nada.",
    "Ignore a palavra abre nesta frase.",
    "Desconsidere a frase fecha a Calculadora.",
    "Não abra a Calculadora.",
    "Talvez eu abra a Calculadora depois.",
    "Como eu apagaria um arquivo?",
)

EXECUTAR = (
    "Pausa a música.",
    "Abre o Opera.",
    "Maximiza a Calculadora.",
    "Fecha a Calculadora.",
    "Pode abrir o Opera?",
    "Continua a música.",
)


def test_matriz_p0_nao_autoriza_mencao_pergunta_hipotese_ou_negacao():
    for texto in NAO_EXECUTAR:
        turno = classificar_modalidade_turno(texto)
        assert turno["autoriza_execucao"] is False, (texto, turno)
        assert bloqueia_execucao_operacional_prioritaria(
            texto, classificacao=turno,
        ) is True, (texto, turno)


def test_matriz_p0_preserva_comandos_reais_e_pedido_polido():
    for texto in EXECUTAR:
        turno = classificar_modalidade_turno(texto)
        assert turno["autoriza_execucao"] is True, (texto, turno)
        assert bloqueia_execucao_operacional_prioritaria(
            texto, classificacao=turno,
        ) is False, (texto, turno)


def _runtime_para(texto, *, detector=None, resolver_app=None):
    executados, registros, falas = [], [], []

    class Estado:
        mental = {"turno_atual": classificar_modalidade_turno(texto)}

    ns = {
        "_estado_compartilhado_runtime": Estado(),
        "detectar_intencao_deterministica": detector or (lambda _texto: None),
        "executar_intencao": lambda comando, _texto: executados.append(dict(comando)) or True,
        "_registrar_resultado_execucao": lambda *args, **kwargs: registros.append((args, kwargs)),
        "_emitir_resposta_curta": lambda _texto, fala, **_kwargs: falas.append(fala),
    }
    if resolver_app is not None:
        ns["_resolver_alvo_ambiente"] = resolver_app
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: ns,
        loop_getter=lambda: None,
    )
    return runtime, executados, registros, falas


def test_runtime_imediato_nao_executa_detector_agressivo_sem_autorizacao():
    texto = "Me explica como pausar uma música sem pausar agora."
    runtime, executados, _registros, _falas = _runtime_para(
        texto,
        detector=lambda _texto: {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}},
    )
    assert runtime.processar_prioritarios(texto) is False
    assert executados == []


def test_runtime_imediato_executa_comando_real():
    texto = "Pausa a música."
    runtime, executados, _registros, _falas = _runtime_para(
        texto,
        detector=lambda _texto: {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}},
    )
    assert runtime.processar_prioritarios(texto) is True
    assert [item["intent"] for item in executados] == ["MEDIA_CONTROL"]


def test_consulta_read_only_do_opera_continua_passando_pela_barreira_existente():
    texto = "O Opera continua aberto?"
    runtime, executados, registros, falas = _runtime_para(
        texto,
        detector=lambda _texto: {"intent": "APP_OPEN", "params": {"programa": "opera"}},
        resolver_app=lambda _nome: {"programa_aberto": True, "programa_em_foco": False},
    )
    assert runtime.processar_prioritarios(texto) is True
    assert executados == []
    assert falas == ["Opera está aberto, mas não está em foco."]
    assert registros
    contrato = registros[-1][0][0]
    assert contrato["intent"] == "LIST_WINDOWS"
    assert contrato["status"] == "estado_app_consultado"


def test_inventario_read_only_tambem_passa_antes_da_barreira():
    texto = "Quais programas estão abertos?"
    falas = []

    class Estado:
        mental = {"turno_atual": classificar_modalidade_turno(texto)}

    ns = {
        "_estado_compartilhado_runtime": Estado(),
        "observar_programas_abertos": lambda: {
            "janelas_visiveis": ["Opera", "Calculadora"],
            "processos_segundo_plano": [],
        },
        "_emitir_resposta_curta": (
            lambda _texto, fala, **_kwargs: falas.append(fala)
        ),
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
        "detectar_intencao_deterministica": lambda _texto: {
            "intent": "APP_OPEN",
            "params": {"programa": "opera"},
        },
        "executar_intencao": lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("rota mutante não deveria ser alcançada")
        ),
    }

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: ns,
        loop_getter=lambda: None,
    )
    assert runtime.processar_prioritarios(texto) is True
    assert falas


def test_metalinguagem_nao_e_segmentada_como_comando():
    turno = classificar_modalidade_turno("Estou apenas escrevendo: abre o Opera.")
    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""
    assert turno["atos"] == ["conversa"]
    assert turno["natureza_acao"] == "mencao_operacional"

def test_runtime_imediato_bloqueia_ignore_palavra_com_detector_agressivo():
    texto = "Ignore a palavra abre nesta frase."
    runtime, executados, _registros, _falas = _runtime_para(
        texto,
        detector=lambda _texto: {
            "intent": "APP_OPEN",
            "params": {"nome_app": "nesta frase"},
        },
    )
    assert runtime.processar_prioritarios(texto) is False
    assert executados == []


def test_ignore_palavra_e_metalinguagem_no_turno_inteiro():
    turno = classificar_modalidade_turno(
        "Ignore a palavra abre nesta frase."
    )
    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""
    assert turno["atos"] == ["conversa"]
    assert turno["natureza_acao"] == "mencao_operacional"

