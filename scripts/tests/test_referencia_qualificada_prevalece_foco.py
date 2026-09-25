"""Qualificador atual não pode herdar outra entidade do registro."""

from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_entidade, resolver_referencia_pontuada,
)


def _registro(*, incluir_ar: bool = False) -> dict:
    registro = registrar_entidade(
        {}, {"tipo": "sensor", "nome": "sensor de umidade do solo"},
        fonte="cadastro_sensores", agora=1000.0,
    )
    if incluir_ar:
        registro = registrar_entidade(
            registro, {"tipo": "sensor", "nome": "sensor de umidade do ar"},
            fonte="cadastro_sensores", agora=1000.1,
        )
        registro["entidade_ativa_id"] = "sensor:sensor_de_umidade_do_solo"
    return registro


def test_qualificador_atual_nao_herda_sensor_de_outro_meio() -> None:
    resolucao = resolver_referencia_pontuada(
        "Esse sensor do ar leu 15% de umidade.",
        entidades_recentes={}, registro=_registro(), agora=1001.0,
    )
    assert resolucao["resolvida"] == {}


def test_qualificador_atual_escolhe_item_compativel_mesmo_com_foco_antigo() -> None:
    resolucao = resolver_referencia_pontuada(
        "Esse sensor do ar leu 15% de umidade.",
        entidades_recentes={}, registro=_registro(incluir_ar=True), agora=1001.0,
    )
    assert resolucao["resolvida"]["nome"] == "sensor de umidade do ar"


def test_cadeia_de_qualificadores_preserva_o_meio_explicito() -> None:
    resolucao = resolver_referencia_pontuada(
        "Esse sensor de umidade do ar leu 15%.",
        entidades_recentes={}, registro=_registro(incluir_ar=True), agora=1001.0,
    )
    assert resolucao["resolvida"]["nome"] == "sensor de umidade do ar"


def test_sem_qualificador_e_qualificador_compativel_preservam_continuidade() -> None:
    for texto in (
        "Esse sensor leu 15% de umidade.",
        "Esse sensor do solo leu 15% de umidade.",
    ):
        resolucao = resolver_referencia_pontuada(
            texto, entidades_recentes={}, registro=_registro(), agora=1001.0,
        )
        assert resolucao["resolvida"]["nome"] == "sensor de umidade do solo"


def test_composicao_retrato_nao_publica_referente_qualificado_incompativel() -> None:
    retrato, _ = construir_retrato_turno(
        "Esse sensor do ar leu 15% de umidade.",
        turno={"id": 2, "modalidade": "conversa"},
        mente={"registro_semantico": _registro()}, contexto_perceptivo={},
        agora=1001.0,
    )
    assert retrato["referencia_resolvida"] == {}
    assert retrato["entidade_explicita"] == {}


def test_mesmo_contrato_protege_playlist_sem_excecao_de_sensor() -> None:
    registro = registrar_entidade(
        {}, {"tipo": "playlist", "nome": "playlist de jazz"}, agora=1000.0,
    )
    registro = registrar_entidade(
        registro, {"tipo": "playlist", "nome": "playlist de rock"},
        agora=1000.1,
    )
    registro["entidade_ativa_id"] = "playlist:playlist_de_jazz"
    resolucao = resolver_referencia_pontuada(
        "Essa playlist de rock ficou boa.",
        entidades_recentes={}, registro=registro, agora=1001.0,
    )
    assert resolucao["resolvida"]["nome"] == "playlist de rock"


def test_qualificador_descritivo_sem_atributo_registrado_nao_veta_jogo() -> None:
    registro = registrar_entidade(
        {}, {"tipo": "jogo", "nome": "Forza Horizon"}, agora=1000.0,
    )
    resolucao = resolver_referencia_pontuada(
        "Esse jogo de corrida está bonito.",
        entidades_recentes={}, registro=registro, agora=1001.0,
    )
    assert resolucao["resolvida"]["nome"] == "Forza Horizon"
