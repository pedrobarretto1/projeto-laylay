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
