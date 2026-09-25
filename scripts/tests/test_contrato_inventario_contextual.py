"""Um trecho relevante não certifica cardinalidade dos referentes."""

import time

from mente_laylay.cognicao.contrato_inventario_contextual import (
    InventarioContextual,
    ReferenteContextual,
    avaliar_referente_contextual,
)
from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno


AGORA = 1000.0


def _item(identificador: str, grandeza: str, *,
          origem: str = "cadastro_sensores", escopo: str = "estufa_a",
          tipo: str = "sensor") -> ReferenteContextual:
    return ReferenteContextual(identificador, tipo, grandeza, origem, escopo)


def _inventario(*itens: ReferenteContextual, cobertura: str = "completa",
                origem: str = "cadastro_sensores", escopo: str = "estufa_a",
                capturado_em: float = AGORA - 1,
                metodo: str = "enumeracao_da_fonte") -> InventarioContextual:
    return InventarioContextual(
        origem, escopo, capturado_em, 60.0, cobertura,
        metodo, tuple(itens),
    )


def _avaliar(inventario: InventarioContextual | None) -> dict[str, object]:
    return avaliar_referente_contextual(
        inventario, tipo="sensor", grandeza_requerida="umidade do solo",
        agora=AGORA, origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )


def test_um_sensor_em_inventario_completo_e_apenas_candidato() -> None:
    resultado = _avaliar(_inventario(_item("solo_1", "umidade do solo")))
    assert resultado["estado"] == "candidato_unico_pendente"
    assert resultado["identificador_candidato"] == "solo_1"
    assert resultado["referente_resolvido"] is False
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


def test_fonte_nao_registrada_nao_pode_autodeclarar_cobertura() -> None:
    resultado = avaliar_referente_contextual(
        _inventario(_item("solo_1", "umidade do solo")),
        tipo="sensor", grandeza_requerida="umidade do solo", agora=AGORA,
    )
    assert resultado["estado"] == "fonte_nao_registrada"
    assert resultado["aprovado_para_compor"] is False


def test_dois_sensores_sao_ambiguos_mesmo_com_grandezas_diferentes() -> None:
    resultado = _avaliar(_inventario(
        _item("solo_1", "umidade do solo"),
        _item("ar_1", "temperatura do ar"),
    ))
    assert resultado["estado"] == "referentes_concorrentes"
    assert resultado["identificadores_candidatos"] == ["ar_1", "solo_1"]
    assert resultado["aprovado_para_compor"] is False


def test_outro_tipo_de_medidor_nao_inventa_segundo_sensor() -> None:
    resultado = _avaliar(_inventario(
        _item("solo_1", "umidade do solo"),
        _item("termometro_1", "temperatura do ar", tipo="termômetro"),
    ))
    assert resultado["estado"] == "candidato_unico_pendente"
    assert resultado["referente_resolvido"] is False


def test_ausencia_de_concorrente_em_inventario_parcial_nao_prova_unicidade() -> None:
    resultado = _avaliar(_inventario(
        _item("solo_1", "umidade do solo"), cobertura="parcial",
    ))
    assert resultado["estado"] == "cobertura_nao_demonstrada"
    assert resultado["referente_resolvido"] is False


def test_escopo_origem_duplicata_e_idade_invalidam_o_recibo() -> None:
    assert _avaliar(_inventario(_item("solo_1", "umidade do solo", escopo="estufa_b")))[
        "estado"] == "proveniencia_invalida"
    assert _avaliar(_inventario(_item("solo_1", "umidade do solo", origem="fala_modelo")))[
        "estado"] == "proveniencia_invalida"
    assert _avaliar(_inventario(_item("solo_1", "umidade do solo"),
                                _item("solo_1", "umidade do solo")))[
        "estado"] == "identificadores_duplicados"
    assert _avaliar(_inventario(_item("solo_1", "umidade do solo"),
                                capturado_em=AGORA - 120))[
        "estado"] == "inventario_expirado"


def test_sem_enumeracao_da_fonte_nao_ha_cobertura_confirmada() -> None:
    resultado = _avaliar(_inventario(
        _item("solo_1", "umidade do solo"), metodo="selecao_de_trechos",
    ))
    assert resultado["estado"] == "cobertura_nao_demonstrada"


def test_inventario_com_campos_malformados_falha_fechado() -> None:
    malformado = InventarioContextual(
        123, "estufa_a", AGORA - 1, 60.0, "completa",
        "enumeracao_da_fonte", (_item("solo_1", "umidade do solo"),),
    )
    resultado = _avaliar(malformado)
    assert resultado["estado"] == "proveniencia_invalida"
    assert resultado["aprovado_para_compor"] is False


def test_inventario_completo_sem_sensor_nao_inventa_referente() -> None:
    resultado = _avaliar(_inventario(_item(
        "termometro_1", "temperatura do ar", tipo="termômetro",
    )))
    assert resultado["estado"] == "referente_ausente"
    assert resultado["referente_resolvido"] is False


def test_selecao_relevante_nao_vira_inventario_por_ser_dict() -> None:
    selecao = selecionar_contexto_turno(
        "o sensor", turno={"modalidade": "pergunta", "texto": "o sensor"},
        mente={"ultima_resposta": "O sensor mede a umidade do solo.",
               "continuidade_fala_ts": time.time()},
        contexto_perceptivo={},
    )
    assert any("sensor" in item["conteudo"].casefold()
               for item in selecao["selecionados"])
    resultado = _avaliar(selecao)  # type: ignore[arg-type]
    assert resultado["estado"] == "inventario_nao_tipado"
    assert resultado["aprovado_para_compor"] is False
