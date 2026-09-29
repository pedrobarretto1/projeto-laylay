"""O mapa proposto não pode omitir caudas nem transformar citação em prova."""

from scripts.analises.contrato_alegacoes_didaticas import conferir_mapa_alegacoes


def _parte(inicio, fim, papel, evidencias=()):
    return {"inicio": inicio, "fim": fim, "papel": papel,
            "evidencias": list(evidencias)}


def _evidencia(fonte_id, citacao):
    return {"fonte_id": fonte_id, "citacao": citacao}


def test_cobertura_integral_nao_esconde_cauda_sem_fonte():
    fala = "A leitura foi 15%. Isso garante flores amanhã."
    corte = fala.index(" Isso")
    resultado = conferir_mapa_alegacoes(
        fala,
        fontes={"u": {"origem": "usuario", "texto": "A leitura foi 15%."}},
        propostas=[
            _parte(0, corte, "premissa_usuario", [_evidencia("u", "A leitura foi 15%")]),
            _parte(corte, len(fala), "conclusao_derivada"),
        ],
    )
    assert resultado["cobertura_textual"] is True
    assert resultado["alegacoes"][0]["estado"] == "revisao_semantica_pendente"
    assert resultado["alegacoes"][1]["estado"] == "sem_fonte"
    assert resultado["aprovado_para_compor"] is False


def test_proposta_que_omite_cauda_nao_tem_cobertura():
    fala = "O motor gira. Ele nunca falha."
    resultado = conferir_mapa_alegacoes(
        fala, fontes={}, propostas=[_parte(0, 13, "fato_externo")],
    )
    assert resultado["cobertura_textual"] is False
    assert resultado["estado"] == "cobertura_invalida"


def test_sobreposicao_ou_salto_tambem_invalidam_cobertura():
    fala = "Uma regra. Outra alegação."
    for segundo_inicio in (8, 11):
        resultado = conferir_mapa_alegacoes(
            fala, fontes={}, propostas=[
                _parte(0, 10, "regra_hipotetica"),
                _parte(segundo_inicio, len(fala), "conclusao_derivada"),
            ],
        )
        assert resultado["estado"] == "cobertura_invalida"
        assert resultado["cobertura_textual"] is False


def test_fonte_registrada_nao_pode_ser_forjada_pela_proposta():
    fala = "A muda floresce amanhã."
    resultado = conferir_mapa_alegacoes(
        fala, fontes={"u": {"origem": "usuario", "texto": "A muda recebeu luz."}},
        propostas=[_parte(0, len(fala), "fato_externo",
                         [_evidencia("u", "floresce amanhã")])],
    )
    assert resultado["alegacoes"][0]["estado"] == "citacao_invalida"


def test_fala_da_assistente_nao_vira_fonte_de_evidencia():
    fala = "O motor dura eternamente."
    resultado = conferir_mapa_alegacoes(
        fala, fontes={"a": {"origem": "assistente", "texto": fala}},
        propostas=[_parte(0, len(fala), "fato_externo", [_evidencia("a", fala)])],
    )
    assert resultado["alegacoes"][0]["estado"] == "fonte_sem_autoridade"


def test_citacao_literal_condicional_nao_certifica_afirmacao_incondicional():
    fala = "A bomba liga."
    resultado = conferir_mapa_alegacoes(
        fala, fontes={"regra": {"origem": "usuario", "texto":
            "Se a umidade ficar abaixo de 20%, a bomba liga."}},
        propostas=[_parte(0, len(fala), "conclusao_derivada",
                         [_evidencia("regra", "a bomba liga")])],
    )
    assert resultado["alegacoes"][0]["estado"] == "revisao_semantica_pendente"
    assert resultado["condicoes_verificadas"] is False
    assert resultado["aprovado_para_compor"] is False


def test_citacao_de_pesquisa_validada_so_prova_texto_nao_verdade_da_alegacao():
    fala = "A peça suporta 50 kg."
    resultado = conferir_mapa_alegacoes(
        fala, fontes={"manual": {"origem": "pesquisa_verificada", "texto": fala}},
        propostas=[_parte(0, len(fala), "fato_externo",
                         [_evidencia("manual", fala)])],
    )
    assert resultado["alegacoes"][0]["fontes_literalmente_conferidas"] is True
    assert resultado["alegacoes"][0]["estado"] == "revisao_semantica_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_campos_malformados_falham_fechados_sem_excecao():
    fala = "A água ferve."
    malformadas = [
        _parte(True, len(fala), "fato_externo"),
        _parte(0, len(fala), ["fato_externo"]),
    ]
    for proposta in malformadas:
        resultado = conferir_mapa_alegacoes(fala, fontes={}, propostas=[proposta])
        assert resultado["cobertura_textual"] is False
        assert resultado["aprovado_para_compor"] is False
    resultado = conferir_mapa_alegacoes(
        fala, fontes={"x": {"origem": ["usuario"], "texto": fala}},
        propostas=[_parte(0, len(fala), "fato_externo", [_evidencia("x", fala)])],
    )
    assert resultado["alegacoes"][0]["estado"] == "fonte_sem_autoridade"


def test_rotulo_nao_factual_proposto_nao_pode_limpar_enunciado_declarativo():
    fala = "A função retorna True se x > 0."
    resultado = conferir_mapa_alegacoes(
        fala, fontes={"u": {"origem": "usuario", "texto": fala}},
        propostas=[_parte(0, len(fala), "nao_factual")],
    )
    assert resultado["alegacoes"][0]["estado"] == "nao_factual_proposto_revisao_pendente"
    assert resultado["estado"] == "papeis_semanticos_pendentes"
    assert resultado["aprovado_para_compor"] is False


def test_medida_sem_criterio_nao_sustenta_qualificacao_qualitativa():
    fala = "Isso é bastante seco."
    resultado = conferir_mapa_alegacoes(
        fala,
        fontes={"leitura": {"origem": "usuario", "texto":
                            "O sensor do solo leu 15% de umidade."}},
        propostas=[{
            **_parte(0, len(fala), "conclusao_derivada",
                     [_evidencia("leitura", "15% de umidade")]),
            "derivacao": {"tipo": "qualificacao_qualitativa",
                          "referente_id": "solo", "atributo": "umidade",
                          "valor": "15", "unidade": "%", "rotulo": "seco",
                          "medida_fonte_id": "leitura", "criterio_fonte_id": ""},
        }],
    )
    assert resultado["alegacoes"][0]["estado"] == "qualificacao_sem_criterio"
    assert resultado["condicoes_verificadas"] is False
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_de_outro_dominio_tambem_precisa_de_criterio():
    fala = "A viga é segura."
    resultado = conferir_mapa_alegacoes(
        fala,
        fontes={"medida": {"origem": "usuario", "texto":
                           "A viga suportou 2 kN."}},
        propostas=[{
            **_parte(0, len(fala), "conclusao_derivada",
                     [_evidencia("medida", "2 kN")]),
            "derivacao": {"tipo": "qualificacao_qualitativa",
                          "referente_id": "viga", "atributo": "carga",
                          "valor": "2", "unidade": "kN", "rotulo": "segura",
                          "medida_fonte_id": "medida", "criterio_fonte_id": ""},
        }],
    )
    assert resultado["alegacoes"][0]["estado"] == "qualificacao_sem_criterio"
    assert resultado["aprovado_para_compor"] is False


def test_criterio_qualitativo_citado_ainda_nao_certifica_relacao():
    fala = "O solo está seco."
    fontes = {
        "medida": {"origem": "usuario", "texto": "O solo marcou 15% de umidade."},
        "criterio": {"origem": "usuario", "texto":
                     "Neste ensaio, 15% de umidade do solo é classificado como seco."},
    }
    proposta = {
        **_parte(0, len(fala), "conclusao_derivada", [
            _evidencia("medida", "15% de umidade"),
            _evidencia("criterio", "15% de umidade do solo é classificado como seco"),
        ]),
        "derivacao": {"tipo": "qualificacao_qualitativa",
                      "referente_id": "solo", "atributo": "umidade",
                      "valor": "15", "unidade": "%", "rotulo": "seco",
                      "medida_fonte_id": "medida",
                      "criterio_fonte_id": "criterio"},
    }
    resultado = conferir_mapa_alegacoes(
        fala, fontes=fontes, propostas=[proposta],
    )
    assert resultado["alegacoes"][0]["estado"] \
        == "criterio_candidato_revisao_pendente"
    assert resultado["alegacoes"][0]["fontes_literalmente_conferidas"] is True
    assert resultado["condicoes_verificadas"] is False
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_nao_aceita_valor_ou_rotulo_forjados():
    fala = "O solo está seco."
    fonte = {"medida": {"origem": "usuario", "texto": "O solo marcou 15%."}}
    proposta = {
        **_parte(0, len(fala), "conclusao_derivada",
                 [_evidencia("medida", "O solo marcou 15%")]),
        "derivacao": {"tipo": "qualificacao_qualitativa",
                      "referente_id": "solo", "atributo": "umidade",
                      "valor": "15", "unidade": "%", "rotulo": "úmido",
                      "medida_fonte_id": "medida", "criterio_fonte_id": ""},
    }
    assert conferir_mapa_alegacoes(
        fala, fontes=fonte, propostas=[proposta],
    )["alegacoes"][0]["estado"] == "rotulo_nao_literal"
    proposta["derivacao"] = {**proposta["derivacao"],
                             "rotulo": "seco", "valor": "50"}
    assert conferir_mapa_alegacoes(
        fala, fontes=fonte, propostas=[proposta],
    )["alegacoes"][0]["estado"] == "medida_sem_ancora_literal"


def test_criterio_com_origem_malformada_falha_fechado_sem_excecao():
    fala = "O solo está seco."
    fontes = {
        "medida": {"origem": "usuario", "texto": "O solo marcou 15%."},
        "criterio": {"origem": ["usuario"], "texto": "15% significa seco."},
    }
    proposta = {
        **_parte(0, len(fala), "conclusao_derivada",
                 [_evidencia("medida", "15%")]),
        "derivacao": {"tipo": "qualificacao_qualitativa",
                      "referente_id": "solo", "atributo": "umidade",
                      "valor": "15", "unidade": "%", "rotulo": "seco",
                      "medida_fonte_id": "medida", "criterio_fonte_id": "criterio"},
    }
    resultado = conferir_mapa_alegacoes(
        fala, fontes=fontes, propostas=[proposta],
    )
    assert resultado["alegacoes"][0]["estado"] == "criterio_sem_fonte_valida"
    assert resultado["aprovado_para_compor"] is False


def _qualificacao_com_regra_numerica(
    *, criterio: str, valor: str = "15", unidade: str = "%",
    rotulo: str = "seco", fala: str = "O solo está seco.",
    referente: str = "solo", atributo: str = "umidade",
):
    medida = f"O {referente} marcou {valor}{unidade}."
    return conferir_mapa_alegacoes(
        fala,
        fontes={
            "medida": {"origem": "usuario", "texto": medida},
            "criterio": {"origem": "usuario", "texto": criterio},
        },
        propostas=[{
            **_parte(0, len(fala), "conclusao_derivada", [
                _evidencia("medida", f"{valor}{unidade}"),
                _evidencia("criterio", criterio),
            ]),
            "derivacao": {"tipo": "qualificacao_qualitativa",
                          "referente_id": referente, "atributo": atributo,
                          "valor": valor, "unidade": unidade,
                          "rotulo": rotulo, "medida_fonte_id": "medida",
                          "criterio_fonte_id": "criterio"},
        }],
    )


def test_citacao_com_rotulo_nao_basta_quando_limiar_contradiz_medida():
    resultado = _qualificacao_com_regra_numerica(
        criterio="Neste ensaio, abaixo de 10% é seco.",
    )
    assert resultado["alegacoes"][0]["estado"] \
        == "criterio_numerico_nao_satisfeito"
    assert resultado["estado"] == "alegacoes_criterio_incompativel"
    assert resultado["aprovado_para_compor"] is False


def test_limiar_compativel_so_confere_numero_e_nao_implicacao():
    for criterio, valor, unidade, rotulo, fala in (
        ("Neste ensaio, abaixo de 20% é seco.", "15", "%",
         "seco", "O solo está seco."),
        ("Neste ensaio, a partir de 30°C é quente.", "32", "°C",
         "quente", "O solo está quente."),
    ):
        resultado = _qualificacao_com_regra_numerica(
            criterio=criterio, valor=valor, unidade=unidade,
            rotulo=rotulo, fala=fala,
        )
        assert resultado["alegacoes"][0]["estado"] \
            == "criterio_numerico_satisfeito_relacao_pendente"
        assert resultado["condicoes_verificadas"] is False
        assert resultado["aprovado_para_compor"] is False


def test_unidade_divergente_ou_negacao_nao_validam_regra_qualitativa():
    divergente = _qualificacao_com_regra_numerica(
        criterio="Neste ensaio, abaixo de 20°C é seco.",
    )
    assert divergente["alegacoes"][0]["estado"] \
        == "criterio_unidade_divergente"
    negada = _qualificacao_com_regra_numerica(
        criterio="Neste ensaio, abaixo de 20% não é seco.",
    )
    assert negada["alegacoes"][0]["estado"] \
        == "criterio_relacao_indeterminada"
    assert not divergente["aprovado_para_compor"]
    assert not negada["aprovado_para_compor"]


def test_limiar_estrito_e_inclusivo_respeitam_fronteira_em_outro_dominio():
    base = {"valor": "12", "unidade": "V", "rotulo": "fraca",
            "fala": "A bateria está fraca.", "referente": "bateria",
            "atributo": "tensao"}
    abaixo = _qualificacao_com_regra_numerica(
        criterio="Neste ensaio, abaixo de 12 V é fraca.", **base,
    )
    ate = _qualificacao_com_regra_numerica(
        criterio="Neste ensaio, até 12 V é fraca.", **base,
    )
    assert abaixo["alegacoes"][0]["estado"] \
        == "criterio_numerico_nao_satisfeito"
    assert ate["alegacoes"][0]["estado"] \
        == "criterio_numerico_satisfeito_relacao_pendente"
    assert not ate["aprovado_para_compor"]


def test_multiplos_limiares_na_mesma_citacao_nao_selecionam_um_conveniente():
    resultado = _qualificacao_com_regra_numerica(
        criterio="Abaixo de 10% é seco, mas acima de 20% também é seco.",
    )
    assert resultado["alegacoes"][0]["estado"] \
        == "criterio_relacao_indeterminada"
    assert resultado["aprovado_para_compor"] is False
