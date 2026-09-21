# -*- coding: utf-8 -*-
"""Regressão R1.1 — autoridade, cadeia e navegação contextual.

Objetivo:
- provar o vocabulary drift entre classificação/P0 e o segmentador de cadeia;
- provar que um efeito contextual/repetido não pode executar com autoridade False;
- provar que ``volta para a aba anterior`` mantém a semântica canônica
  SWITCH_PREVIOUS_TAB em vez de reabrir o último site com OPEN_URL;
- preservar consultas read-only e o consumo seguro de cadeias já reconhecidas;
- provar defesa em profundidade nos corredores prioritários após uma falha da P0.

Contrato:
- consultas/read-only não ganham barreiras de mutação;
- ações com efeito nunca ganham autoridade ao mudar de rota;
- a gramática de aba anterior permanece única entre classificador, detector e contexto.

Deliberadamente fora deste snapshot:
- qualquer mudança em executor de navegador;
- aumento artificial de prioridade de SWITCH_PREVIOUS_TAB;
- autorização global no executor;
- gramática genérica para todo verbo de movimento;
- fases de arquivo R1/R2 já cobertas pelo Patch 2.0.
"""

from __future__ import annotations

import pytest

import mente_laylay.autonomia.comandos_imediatos as comandos_imediatos_mod
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.analise_comandos import (
    processar_comandos_em_cadeia,
    segmentar_comandos_em_cadeia,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_consulta_abas
from mente_laylay.cognicao.arbitro_turno import CandidatoDecisao, arbitrar_turno
from mente_laylay.cognicao.modalidade_turno import (
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.especialistas.capacidades import INTENTS_SOMENTE_LEITURA
from mente_laylay.memoria_mental.contexto_imediato import (
    resolver_comando_acao_geral_contextual,
)


FRASE_CAOS = "Volta para a aba anterior e depois me diz qual aba está aberta."


def _params(**kwargs):
    return kwargs


def _turno(*, autoriza: bool, modalidade: str = "comando", turno_id: int = 4101) -> dict:
    return {
        "id": turno_id,
        "texto": "",
        "modalidade": modalidade,
        "modalidade_geral": modalidade,
        "ato_principal": modalidade,
        "atos": [modalidade],
        "segmentos": [],
        "acao_explicita": bool(autoriza),
        "autoriza_execucao": bool(autoriza),
        "requer_esclarecimento": False,
        "depende_contexto": not bool(autoriza),
        "natureza_acao": "pedido_direto" if autoriza else "nenhuma",
    }


def _contexto_site() -> dict:
    return {
        "tipo": "site",
        "alvo": "documentacao oficial do python",
        "intencao": "SEARCH",
        "params": {
            "alvo": "documentacao oficial do python",
            "query": "documentacao oficial do python",
        },
    }


def _intent(resultado: dict | None) -> str:
    return str((resultado or {}).get("intent") or "").upper().strip()


# ---------------------------------------------------------------------------
# GUARDS — fatos já corretos no teste 3.2.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        "volta para a aba anterior",
        "volte pra aba anterior",
        "retorna para a aba anterior",
    ],
)
def test_guard__detector_navegador_ja_sabe_trocar_para_aba_anterior(texto: str) -> None:
    resultado = detectar_consulta_abas(texto, params_cb=_params)
    assert _intent(resultado) == "SWITCH_PREVIOUS_TAB"


@pytest.mark.parametrize(
    "texto",
    [
        "volta para a anterior",
        "volte pra anterior",
        "retorna para anterior",
        "vai pra anterior",
    ],
)
def test_guard__detector_sem_contexto_nao_promove_elipse_para_aba(texto: str) -> None:
    resultado = detectar_consulta_abas(texto, params_cb=_params)
    assert _intent(resultado) != "SWITCH_PREVIOUS_TAB", (
        "sem uma referência de site já resolvida, 'anterior' continua ambíguo "
        "e não pode virar navegação de aba por gramática global"
    )


@pytest.mark.parametrize(
    "texto",
    [
        "A volta às aulas é amanhã.",
        "Meu irmão volta amanhã.",
        "O site retorna erro.",
        "Ela retorna daqui a pouco.",
    ],
)
def test_guard__movimento_narrativo_nao_autoriza_execucao(texto: str) -> None:
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is False


def test_guard__segmentador_ja_enxerga_volta_como_etapa_operacional() -> None:
    partes = segmentar_comandos_em_cadeia(FRASE_CAOS)
    assert len(partes) == 2
    assert partes[0].casefold().startswith("volta para a aba anterior")
    assert "qual aba" in partes[1].casefold()


def test_guard__switch_previous_tab_e_efeito_mas_list_tabs_e_readonly() -> None:
    assert "SWITCH_PREVIOUS_TAB" not in INTENTS_SOMENTE_LEITURA
    assert "OPEN_URL" not in INTENTS_SOMENTE_LEITURA
    assert "LIST_TABS" in INTENTS_SOMENTE_LEITURA


def test_guard__arbitro_preserva_consulta_readonly_sem_autorizacao_de_efeito() -> None:
    resultado = arbitrar_turno(
        "me diz qual aba está aberta",
        [
            CandidatoDecisao(
                tipo="comando_explicito",
                valor={"intent": "LIST_TABS", "params": {"somente_ativa": True}},
                origem="guard-readonly",
                confianca=0.99,
            )
        ],
        turno=_turno(autoriza=False, modalidade="comando", turno_id=4102),
        retrato={},
    )
    assert _intent(resultado.get("decisao")) == "LIST_TABS"


@pytest.mark.parametrize(
    "texto",
    [
        "Como eu volto para a aba anterior?",
        "Estou só dizendo a frase volta para a aba anterior.",
    ],
)
def test_guard__pergunta_e_metalinguagem_nao_autorizam_troca_de_aba(texto: str) -> None:
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is False


def test_guard__cadeia_reconhecida_e_consumida_mesmo_se_primeira_etapa_falha() -> None:
    executadas: list[str] = []

    def executar(trecho: str, _origem: str) -> bool:
        executadas.append(trecho)
        return False

    consumiu = processar_comandos_em_cadeia(
        FRASE_CAOS,
        executar_trecho=executar,
    )
    assert consumiu is True
    assert len(executadas) == 1
    assert executadas[0].casefold().startswith("volta para a aba anterior")


def test_guard__com_autoridade_candidato_explicito_correto_vence_fallback_contextual() -> None:
    resultado = arbitrar_turno(
        "volta para a aba anterior",
        [
            CandidatoDecisao(
                tipo="comando_contextual",
                valor={
                    "intent": "OPEN_URL",
                    "params": {"alvo": "documentacao oficial do python"},
                },
                origem="fallback-contextual",
                confianca=0.99,
            ),
            CandidatoDecisao(
                tipo="comando_explicito",
                valor={"intent": "SWITCH_PREVIOUS_TAB", "params": {}},
                origem="deterministico-abas",
                confianca=0.90,
            ),
        ],
        turno=_turno(autoriza=True, modalidade="comando", turno_id=4103),
        retrato={},
    )
    assert _intent(resultado.get("decisao")) == "SWITCH_PREVIOUS_TAB"


# ---------------------------------------------------------------------------
# CONTRATO 1 — o ato explícito deve nascer com autoridade própria.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        "Volta para a aba anterior.",
        "Volte pra aba anterior.",
        "Retorna para a aba anterior.",
    ],
)
def test_regressao__pedido_explicito_de_aba_anterior_autoriza_o_turno(texto: str) -> None:
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True, (
        "ordem explícita de navegação não pode nascer como conversa sem autoridade"
    )


def test_regressao__turno_composto_do_caos_nao_nasce_como_conversa_sem_autoridade() -> None:
    turno = classificar_modalidade_turno(FRASE_CAOS)
    assert turno["autoriza_execucao"] is True, (
        "a cadeia contém uma ação explícita e uma leitura; o pai precisa carregar a autorização real"
    )
    assert str(turno.get("modalidade_geral") or turno.get("modalidade") or "") in {
        "comando", "misto"
    }


# ---------------------------------------------------------------------------
# CONTRATO 2 — se a classificação falhar, o P0 ainda precisa falhar fechado.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        "volta para a aba anterior",
        "volte pra aba anterior",
        "retorna para a aba anterior",
    ],
)
def test_regressao__p0_bloqueia_verbo_de_navegacao_quando_turno_nao_autorizou(texto: str) -> None:
    classificacao_congelada = _turno(
        autoriza=False,
        modalidade="conversa",
        turno_id=4201,
    )
    assert bloqueia_execucao_operacional_prioritaria(
        texto,
        classificacao=classificacao_congelada,
    ) is True, (
        "vocabulary drift não pode transformar autoridade False em corredor operacional"
    )


# ---------------------------------------------------------------------------
# CONTRATO 3 — a mesma semântica de navegador não pode virar OPEN_URL por contexto.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        "volta para a aba anterior",
        "volte pra aba anterior",
        "retorna para a aba anterior",
    ],
)
def test_regressao__contexto_site_preserva_switch_previous_tab_em_vez_de_reabrir_site(texto: str) -> None:
    resultado = resolver_comando_acao_geral_contextual(
        texto,
        _contexto_site(),
    )
    assert _intent(resultado) == "SWITCH_PREVIOUS_TAB", (
        f"pedido de aba anterior virou {_intent(resultado) or 'NONE'} em vez da operação canônica"
    )


@pytest.mark.parametrize(
    "texto",
    [
        "volta para a anterior",
        "volte pra anterior",
    ],
)
def test_regressao__contexto_site_preserva_elipse_que_ja_funcionava_no_3_2(
    texto: str,
) -> None:
    resultado = resolver_comando_acao_geral_contextual(
        texto,
        _contexto_site(),
    )
    assert _intent(resultado) == "SWITCH_PREVIOUS_TAB", (
        "a correção da forma explícita não pode apagar a elipse contextual "
        "de site já válida no teste 3.2"
    )


# ---------------------------------------------------------------------------
# CONTRATO 4 — mudar a rota/categoria do candidato nunca aumenta autoridade.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("tipo_candidato", "intent"),
    [
        ("comando_contextual", "OPEN_URL"),
        ("comando_contextual", "SWITCH_PREVIOUS_TAB"),
        ("comando_contextual", "CLOSE_APP"),
        ("comando_contextual", "MEDIA_CONTROL"),
        ("repeticao", "OPEN_URL"),
        ("repeticao", "SWITCH_PREVIOUS_TAB"),
        ("repeticao", "CLOSE_APP"),
        ("repeticao", "MEDIA_CONTROL"),
    ],
)
def test_regressao__arbitro_rejeita_todo_efeito_contextual_sem_autoridade_do_turno(
    tipo_candidato: str,
    intent: str,
) -> None:
    candidato = CandidatoDecisao(
        tipo=tipo_candidato,
        valor={
            "intent": intent,
            "params": (
                {"alvo": "documentacao oficial do python"}
                if intent == "OPEN_URL"
                else {"nome_app": "opera"}
                if intent == "CLOSE_APP"
                else {"acao": "pause", "platform": "music"}
                if intent == "MEDIA_CONTROL"
                else {}
            ),
        },
        origem="red-autoridade-contextual",
        confianca=0.99,
    )
    resultado = arbitrar_turno(
        "volta para a aba anterior",
        [candidato],
        turno=_turno(autoriza=False, modalidade="comando", turno_id=4301),
        retrato={},
    )
    assert resultado.get("decisao") is None, (
        f"{tipo_candidato}/{intent} não pode executar efeito quando autoriza_execucao=False"
    )
    assert resultado.get("rejeitados"), "a recusa precisa permanecer explicável"


# ---------------------------------------------------------------------------
# CONTRATO 5 — P0 é a primeira barreira, não a única autoridade de dispatch.
# ---------------------------------------------------------------------------


def _runtime_com_turno_forcado(
    *,
    detector=None,
    resolver_contextual=None,
    autoriza: bool = False,
):
    executados: list[dict] = []
    registros: list[tuple] = []

    class Estado:
        mental = {
            "turno_atual": _turno(
                autoriza=autoriza,
                modalidade="comando" if autoriza else "conversa",
                turno_id=4401,
            )
        }

    ns = {
        "_estado_compartilhado_runtime": Estado(),
        "detectar_intencao_deterministica": detector or (lambda _texto: None),
        "_resolver_comando_contextual_forcado": resolver_contextual,
        "executar_intencao": (
            lambda comando, _texto: executados.append(dict(comando)) or True
        ),
        "_registrar_resultado_execucao": (
            lambda *args, **kwargs: registros.append((args, kwargs))
        ),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: ns,
        loop_getter=lambda: None,
    )
    return runtime, executados, registros


def test_regressao__corredor_deterministico_pos_p0_nao_executa_efeito_sem_autoridade(
    monkeypatch,
) -> None:
    """Mesmo se a P0 lexical falhar, o dispatch não pode inventar permissão."""
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "bloqueia_execucao_operacional_prioritaria",
        lambda *_args, **_kwargs: False,
    )
    runtime, executados, _registros = _runtime_com_turno_forcado(
        detector=lambda _texto: {
            "intent": "SWITCH_PREVIOUS_TAB",
            "params": {},
        },
    )

    runtime.processar_prioritarios("volta para a aba anterior")

    assert executados == [], (
        "o corredor determinístico pós-P0 precisa respeitar a autoridade congelada "
        "mesmo quando a primeira barreira falha"
    )


def test_regressao__corredor_referencia_tipificada_pos_p0_nao_executa_efeito_sem_autoridade(
    monkeypatch,
) -> None:
    """A referência resolve alvo/intent; ela não concede autoridade."""
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "bloqueia_execucao_operacional_prioritaria",
        lambda *_args, **_kwargs: False,
    )
    runtime, executados, _registros = _runtime_com_turno_forcado(
        detector=lambda _texto: None,
        resolver_contextual=lambda _texto: {
            "intent": "OPEN_URL",
            "params": {"alvo": "documentacao oficial do python"},
        },
    )

    runtime.processar_prioritarios("volta para a anterior")

    assert executados == [], (
        "o corredor de referência tipificada não pode transformar contexto "
        "resolvido em permissão de efeito"
    )


@pytest.mark.parametrize("tipo_candidato", ["comando_contextual", "repeticao"])
def test_guard__arbitro_readonly_contextual_continua_livre_sem_autoridade(
    tipo_candidato: str,
) -> None:
    resultado = arbitrar_turno(
        "me diz qual aba está aberta",
        [
            CandidatoDecisao(
                tipo=tipo_candidato,
                valor={"intent": "LIST_TABS", "params": {"somente_ativa": True}},
                origem="guard-readonly-contextual",
                confianca=0.99,
            )
        ],
        turno=_turno(autoriza=False, modalidade="comando", turno_id=4501),
        retrato={},
    )
    assert _intent(resultado.get("decisao")) == "LIST_TABS"


def test_guard__corredor_deterministico_com_autoridade_continua_executando(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "bloqueia_execucao_operacional_prioritaria",
        lambda *_args, **_kwargs: False,
    )
    runtime, executados, _registros = _runtime_com_turno_forcado(
        detector=lambda _texto: {
            "intent": "SWITCH_PREVIOUS_TAB",
            "params": {},
        },
        autoriza=True,
    )

    assert runtime.processar_prioritarios("volta para a aba anterior") is True
    assert [item["intent"] for item in executados] == ["SWITCH_PREVIOUS_TAB"]


def test_guard__corredor_referencia_tipificada_com_autoridade_continua_executando(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        comandos_imediatos_mod,
        "bloqueia_execucao_operacional_prioritaria",
        lambda *_args, **_kwargs: False,
    )
    runtime, executados, _registros = _runtime_com_turno_forcado(
        detector=lambda _texto: None,
        resolver_contextual=lambda _texto: {
            "intent": "OPEN_URL",
            "params": {"alvo": "documentacao oficial do python"},
        },
        autoriza=True,
    )

    assert runtime.processar_prioritarios("volta para a anterior") is True
    assert [item["intent"] for item in executados] == ["OPEN_URL"]
