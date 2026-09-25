"""A continuidade tipada escolhe candidato, mas não inventa efeito."""

from dataclasses import asdict, replace

from mente_laylay.cognicao.contrato_inventario_contextual import (
    AntecedenteContextual, InventarioContextual, ReferenteContextual,
    antecedente_de_mencao_explicita, antecedente_do_foco_guardado,
    antecedente_do_retrato,
    atualizar_foco_contextual_inventariado, avaliar_referente_contextual,
    avaliar_referencia_nominal_contextual,
)
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_entidade
from mente_laylay.memoria_mental.registro_semantico import atualizar_registro_turno
from mente_laylay.memoria_mental.registro_semantico import (
    guardar_candidato_foco_contextual, renovar_registro_semantico_sessao,
)


AGORA = 1002.0


def _inventario(*, cobertura: str = "completa") -> InventarioContextual:
    origem, escopo = "cadastro_sensores", "estufa_a"
    return InventarioContextual(
        origem, escopo, 1000.0, 60.0, cobertura, "enumeracao_da_fonte",
        (
            ReferenteContextual("solo_1", "sensor", "umidade do solo", origem, escopo),
            ReferenteContextual("ar_1", "sensor", "umidade do ar", origem, escopo),
        ),
    )


def _registro(*, fonte: str = "cadastro_sensores",
              id_inventario: str = "solo_1", escopo: str = "estufa_a") -> dict:
    return registrar_entidade(
        {}, {"tipo": "sensor", "nome": "sensor de umidade do solo",
             "dados": {"inventario_id": id_inventario,
                       "inventario_escopo": escopo,
                       "inventario_origem": "cadastro_sensores"}},
        fonte=fonte, agora=1000.5,
    )


def _retrato(registro: dict, texto: str = "Esse sensor leu 15% de umidade.") -> dict:
    retrato, _ = construir_retrato_turno(
        texto, turno={"id": 9, "modalidade": "conversa"},
        mente={"registro_semantico": registro}, contexto_perceptivo={},
        agora=1001.0,
    )
    return retrato


def _avaliar(*, antecedente: AntecedenteContextual | None,
             inventario: InventarioContextual | None = None,
             origens_antecedente: frozenset[str] = frozenset({"registro_semantico_tipado"})) -> dict:
    return avaliar_referente_contextual(
        inventario or _inventario(), tipo="sensor",
        grandeza_requerida="umidade do solo", agora=AGORA,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
        antecedente=antecedente, origens_antecedente=origens_antecedente,
    )


def test_retrato_canonico_com_id_e_fonte_seleciona_so_candidato_pendente() -> None:
    registro = _registro()
    retrato = _retrato(registro)
    antecedente = antecedente_do_retrato(
        retrato, registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    assert antecedente.identificador == "solo_1"
    resultado = _avaliar(antecedente=antecedente)
    assert resultado["estado"] == "candidato_focal_pendente"
    assert resultado["identificador_candidato"] == "solo_1"
    assert resultado["referente_resolvido"] is False
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


def test_texto_sem_id_ou_qualificador_conflitante_nao_cria_antecedente() -> None:
    registro = _registro()
    for texto in (
        "O sensor leu 15% de umidade.",
        "Esse sensor do ar leu 15% de umidade.",
    ):
        assert antecedente_do_retrato(
            _retrato(registro, texto), registro, _inventario(), agora=AGORA,
        ) is None
    assert _avaliar(antecedente=None)["estado"] == "referentes_concorrentes"


def test_mencao_textual_anterior_nao_fabrica_id_de_inventario() -> None:
    primeiro, _ = construir_retrato_turno(
        "Estamos falando do sensor de umidade do solo.",
        turno={"id": 8, "modalidade": "conversa"}, mente={},
        contexto_perceptivo={}, agora=1000.0,
    )
    registro = atualizar_registro_turno(
        {}, primeiro["texto"], retrato=primeiro, agora=1000.0,
    )
    segundo, _ = construir_retrato_turno(
        "O sensor leu 15% de umidade.",
        turno={"id": 9, "modalidade": "conversa"},
        mente={"registro_semantico": registro},
        contexto_perceptivo={}, agora=1001.0,
    )
    assert primeiro["entidade_explicita"] == {}
    assert segundo["referencia_resolvida"] == {}
    assert antecedente_do_retrato(
        segundo, registro, _inventario(), agora=AGORA,
    ) is None


def test_mencao_explicita_com_fonte_unica_cria_foco_candidato_para_proximo_turno() -> None:
    primeiro, _ = construir_retrato_turno(
        "Estamos falando do sensor de umidade do solo.",
        turno={"id": 8, "modalidade": "conversa"}, mente={},
        contexto_perceptivo={}, agora=1000.5,
    )
    antecedente = antecedente_de_mencao_explicita(
        primeiro, _inventario(), agora=1000.5,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )
    assert antecedente is not None
    assert antecedente.identificador == "solo_1"
    assert antecedente.origem_inventario == "cadastro_sensores"
    resultado = _avaliar_exemplo(
        "O sensor leu 15% de umidade.", antecedente=antecedente,
        origens_antecedente=frozenset({"mencao_explicita_inventariada"}),
    )
    assert resultado["estado"] == "candidato_focal_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_mencao_vaga_ou_fonte_incompleta_nao_cria_foco() -> None:
    for texto, inventario, origens in (
        ("Estamos falando do sensor.", _inventario(), frozenset({"cadastro_sensores"})),
        ("Estamos falando do sensor de umidade do solo.",
         _inventario(cobertura="parcial"), frozenset({"cadastro_sensores"})),
        ("Estamos falando do sensor de umidade do solo.",
         _inventario(), frozenset()),
        ("O manual menciona sensor de umidade do solo.",
         _inventario(), frozenset({"cadastro_sensores"})),
    ):
        retrato, _ = construir_retrato_turno(
            texto, turno={"id": 8, "modalidade": "conversa"},
            mente={}, contexto_perceptivo={}, agora=1000.5,
        )
        assert antecedente_de_mencao_explicita(
            retrato, inventario, agora=1000.5,
            origens_enumeradoras=origens,
        ) is None


def test_foco_explicito_sobrevive_turno_no_registro_sem_virar_entidade_ativa() -> None:
    primeiro, _ = construir_retrato_turno(
        "Estamos falando do sensor de umidade do solo.",
        turno={"id": 8, "modalidade": "conversa"}, mente={},
        contexto_perceptivo={}, agora=1000.5,
    )
    foco = antecedente_de_mencao_explicita(
        primeiro, _inventario(), agora=1000.5,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )
    assert foco is not None
    registro = atualizar_foco_contextual_inventariado(
        {}, primeiro, _inventario(), agora=1000.5,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )
    assert registro["entidade_ativa_id"] == ""
    segundo, _ = construir_retrato_turno(
        "O sensor leu 15% de umidade.",
        turno={"id": 9, "modalidade": "conversa"},
        mente={"registro_semantico": registro},
        contexto_perceptivo={}, agora=1001.0,
    )
    registro = atualizar_registro_turno(
        registro, segundo["texto"], retrato=segundo, agora=1001.0,
    )
    recuperado = antecedente_do_foco_guardado(
        registro, _inventario(), agora=AGORA,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )
    assert recuperado == foco
    assert _avaliar_exemplo(
        segundo["texto"], antecedente=recuperado,
        origens_antecedente=frozenset({"mencao_explicita_inventariada"}),
    )["estado"] == "candidato_focal_pendente"


def test_foco_guardado_vencido_ou_de_outra_fonte_nao_reaparece() -> None:
    primeiro, _ = construir_retrato_turno(
        "Estamos falando do sensor de umidade do solo.",
        turno={"id": 8, "modalidade": "conversa"}, mente={},
        contexto_perceptivo={}, agora=1000.5,
    )
    foco = antecedente_de_mencao_explicita(
        primeiro, _inventario(), agora=1000.5,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )
    assert foco is not None
    registro = guardar_candidato_foco_contextual({}, asdict(foco), agora=1000.5)
    outra_fonte = InventarioContextual(
        "cenario_usuario", "estufa_a", 1000.0, 300.0,
        "completa", "enumeracao_da_fonte",
        (ReferenteContextual("solo_1", "sensor", "umidade do solo",
                             "cenario_usuario", "estufa_a"),),
    )
    assert antecedente_do_foco_guardado(
        registro, outra_fonte, agora=AGORA,
        origens_enumeradoras=frozenset({"cenario_usuario"}),
    ) is None
    assert antecedente_do_foco_guardado(
        registro, replace(_inventario(), ttl_s=300.0), agora=1201.0,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    ) is None
    renovado = renovar_registro_semantico_sessao(registro, agora=1002.0)
    assert renovado["foco_contextual_tipado"] == {}


def test_tentativa_de_troca_de_foco_ambigua_descarta_foco_anterior() -> None:
    primeiro, _ = construir_retrato_turno(
        "Estamos falando do sensor de umidade do solo.",
        turno={"id": 8, "modalidade": "conversa"}, mente={},
        contexto_perceptivo={}, agora=1000.5,
    )
    foco = antecedente_de_mencao_explicita(
        primeiro, _inventario(), agora=1000.5,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )
    assert foco is not None
    registro = guardar_candidato_foco_contextual({}, asdict(foco), agora=1000.5)
    ambigua, _ = construir_retrato_turno(
        "Estamos falando do sensor.",
        turno={"id": 9, "modalidade": "conversa"},
        mente={"registro_semantico": registro},
        contexto_perceptivo={}, agora=1001.0,
    )
    registro = atualizar_foco_contextual_inventariado(
        registro, ambigua, _inventario(), agora=1001.0,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    )
    assert antecedente_do_foco_guardado(
        registro, _inventario(), agora=AGORA,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    ) is None


def test_contrato_de_foco_tambem_vale_para_outro_dominio() -> None:
    inventario = InventarioContextual(
        "catalogo_playlists", "conta_1", 1000.0, 60.0,
        "completa", "enumeracao_da_fonte",
        (
            ReferenteContextual("jazz_1", "playlist", "jazz",
                                 "catalogo_playlists", "conta_1"),
            ReferenteContextual("rock_1", "playlist", "rock",
                                 "catalogo_playlists", "conta_1"),
        ),
    )
    retrato, _ = construir_retrato_turno(
        "Estamos falando da playlist de jazz.",
        turno={"id": 11, "modalidade": "conversa"}, mente={},
        contexto_perceptivo={}, agora=1000.5,
    )
    foco = antecedente_de_mencao_explicita(
        retrato, inventario, agora=1000.5,
        origens_enumeradoras=frozenset({"catalogo_playlists"}),
    )
    assert foco is not None
    assert foco.identificador == "jazz_1"
    assert foco.origem_inventario == "catalogo_playlists"


def test_descricao_repetida_em_itens_diferentes_nao_cria_foco_arbitrario() -> None:
    inventario = replace(
        _inventario(),
        referentes=(
            _inventario().referentes[0],
            ReferenteContextual("solo_2", "sensor", "umidade do solo",
                                 "cadastro_sensores", "estufa_a"),
        ),
    )
    retrato, _ = construir_retrato_turno(
        "Estamos falando do sensor de umidade do solo.",
        turno={"id": 8, "modalidade": "conversa"}, mente={},
        contexto_perceptivo={}, agora=1000.5,
    )
    assert antecedente_de_mencao_explicita(
        retrato, inventario, agora=1000.5,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
    ) is None


def test_qualificador_atual_pode_apontar_ar_sem_virar_solo_da_definicao() -> None:
    registro = _registro()
    registro = registrar_entidade(
        registro, {"tipo": "sensor", "nome": "sensor de umidade do ar",
                   "dados": {"inventario_id": "ar_1",
                             "inventario_escopo": "estufa_a",
                             "inventario_origem": "cadastro_sensores"}},
        fonte="cadastro_sensores", agora=1000.6,
    )
    registro["entidade_ativa_id"] = "sensor:sensor_de_umidade_do_solo"
    for texto in (
        "Esse sensor do ar leu 15% de umidade.",
        "Esse sensor de umidade do ar leu 15%.",
    ):
        antecedente = antecedente_do_retrato(
            _retrato(registro, texto), registro, _inventario(), agora=AGORA,
        )
        assert antecedente is not None
        assert antecedente.identificador == "ar_1"
        assert _avaliar(antecedente=antecedente)["estado"] == "grandeza_divergente"


def test_nome_generico_registrado_nao_sobrepoe_qualificador_atual() -> None:
    registro = registrar_entidade(
        {}, {"tipo": "sensor", "nome": "Sensor A",
             "dados": {"inventario_id": "solo_1",
                       "inventario_escopo": "estufa_a",
                       "inventario_origem": "cadastro_sensores"}},
        fonte="cadastro_sensores", agora=1000.5,
    )
    retrato = _retrato(registro, "Esse sensor do ar leu 15% de umidade.")
    assert retrato["referencia_resolvida"]["nome"] == "Sensor A"
    assert antecedente_do_retrato(
        retrato, registro, _inventario(), agora=AGORA,
    ) is None


def test_fonte_usuario_escopo_ou_id_sem_vinculo_nao_sao_promovidos() -> None:
    for registro in (
        _registro(fonte="usuario"),
        _registro(escopo="estufa_b"),
        _registro(id_inventario="sensor_fantasma"),
    ):
        assert antecedente_do_retrato(
            _retrato(registro), registro, _inventario(), agora=AGORA,
        ) is None


def test_antecedente_nao_registrado_ou_inventario_parcial_falha_fechado() -> None:
    registro = _registro()
    antecedente = antecedente_do_retrato(
        _retrato(registro), registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    assert _avaliar(antecedente=antecedente,
                    origens_antecedente=frozenset())["estado"] == "antecedente_nao_registrado"
    assert _avaliar(antecedente=antecedente,
                    inventario=_inventario(cobertura="parcial"))[
                        "estado"] == "cobertura_nao_demonstrada"


def test_antecedente_expirado_escopo_diferente_ou_item_ausente_bloqueia() -> None:
    registro = _registro()
    antecedente = antecedente_do_retrato(
        _retrato(registro), registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    for candidato in (
        replace(antecedente, registrado_em=AGORA - 200),
        replace(antecedente, escopo="estufa_b"),
    ):
        assert _avaliar(antecedente=candidato)["estado"] == "antecedente_invalido"
    assert _avaliar(antecedente=replace(
        antecedente, identificador="sensor_fantasma"))[
            "estado"] == "antecedente_sem_item"


def test_antecedente_nao_atravessa_fontes_com_mesmo_id_e_escopo() -> None:
    registro = _registro()
    antecedente = antecedente_do_retrato(
        _retrato(registro), registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    outro = InventarioContextual(
        "cenario_usuario", "estufa_a", 1000.0, 60.0,
        "completa", "enumeracao_da_fonte",
        (ReferenteContextual(
            "solo_1", "sensor", "umidade do solo", "cenario_usuario", "estufa_a",
        ),),
    )
    resultado = avaliar_referente_contextual(
        outro, tipo="sensor", grandeza_requerida="umidade do solo",
        agora=AGORA,
        origens_enumeradoras=frozenset({"cadastro_sensores", "cenario_usuario"}),
        antecedente=antecedente,
        origens_antecedente=frozenset({"registro_semantico_tipado"}),
    )
    assert resultado["estado"] == "antecedente_invalido"


def test_pontuacao_malformada_do_retrato_falha_fechado() -> None:
    registro = _registro()
    retrato = _retrato(registro)
    retrato["referencia_candidatos"][0]["pontuacao"] = "valor inválido"
    assert antecedente_do_retrato(
        retrato, registro, _inventario(), agora=AGORA,
    ) is None


def _avaliar_exemplo(texto: str, *, antecedente: AntecedenteContextual | None,
                     inventario: InventarioContextual | None = None,
                     origens_antecedente: frozenset[str] = frozenset({
                         "registro_semantico_tipado",
                     })) -> dict:
    return avaliar_referencia_nominal_contextual(
        texto, inventario or _inventario(), tipo="sensor",
        grandeza_requerida="umidade do solo", agora=AGORA,
        origens_enumeradoras=frozenset({"cadastro_sensores"}),
        antecedente=antecedente,
        origens_antecedente=origens_antecedente,
    )


def test_o_sensor_em_exemplo_so_aponta_foco_tipado_sem_aprovar_fala() -> None:
    registro = _registro()
    antecedente = antecedente_do_retrato(
        _retrato(registro), registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    resultado = _avaliar_exemplo(
        "No modo automático, o sensor leu 15% de umidade e o controlador ligou a bomba.",
        antecedente=antecedente,
    )
    assert resultado["estado"] == "candidato_focal_pendente"
    assert resultado["identificador_candidato"] == "solo_1"
    assert resultado["referente_resolvido"] is False
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


def test_o_sensor_sem_foco_com_dois_itens_permanece_indeterminado() -> None:
    resultado = _avaliar_exemplo(
        "No modo automático, o sensor leu 15% de umidade.", antecedente=None,
    )
    assert resultado["estado"] == "referentes_concorrentes"
    assert "identificador_candidato" not in resultado


def test_o_sensor_unico_so_e_candidato_com_enumeracao_completa() -> None:
    unico = replace(_inventario(), referentes=(_inventario().referentes[0],))
    resultado = _avaliar_exemplo(
        "O sensor leu 15% de umidade.", antecedente=None, inventario=unico,
    )
    assert resultado["estado"] == "candidato_unico_pendente"
    assert resultado["identificador_candidato"] == "solo_1"
    assert resultado["aprovado_para_compor"] is False
    parcial = replace(unico, cobertura="parcial")
    assert _avaliar_exemplo(
        "O sensor leu 15% de umidade.", antecedente=None, inventario=parcial,
    )["estado"] == "cobertura_nao_demonstrada"


def test_qualificador_expresso_no_exemplo_veta_foco_anterior() -> None:
    registro = _registro()
    antecedente = antecedente_do_retrato(
        _retrato(registro), registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    for texto in (
        "O sensor do ar leu 15% de umidade.",
        "O sensor de umidade do ar leu 15%.",
    ):
        resultado = _avaliar_exemplo(texto, antecedente=antecedente)
        assert resultado["estado"] == "qualificador_divergente"
        assert "identificador_candidato" not in resultado


def test_mencao_ausente_ou_multipla_nao_herda_foco_por_acaso() -> None:
    registro = _registro()
    antecedente = antecedente_do_retrato(
        _retrato(registro), registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    for texto, estado in (
        ("Um sensor leu 15% de umidade.", "referencia_nominal_ausente"),
        ("O sensor leu 15% e o sensor repetiu a leitura.", "referencia_nominal_multipla"),
        ("O sensor leu 15%. Esse sensor do ar leu 40%.", "referencia_nominal_multipla"),
        ("O sensor leu 15%. Um sensor do ar leu 40%.", "referencia_nominal_multipla"),
    ):
        resultado = _avaliar_exemplo(texto, antecedente=antecedente)
        assert resultado["estado"] == estado
        assert "identificador_candidato" not in resultado


def test_foco_vencido_nao_e_reativado_pela_mencao_definida() -> None:
    registro = _registro()
    antecedente = antecedente_do_retrato(
        _retrato(registro), registro, _inventario(), agora=AGORA,
    )
    assert antecedente is not None
    resultado = _avaliar_exemplo(
        "O sensor leu 15% de umidade.",
        antecedente=replace(antecedente, registrado_em=AGORA - 200),
    )
    assert resultado["estado"] == "antecedente_invalido"
    assert "identificador_candidato" not in resultado
