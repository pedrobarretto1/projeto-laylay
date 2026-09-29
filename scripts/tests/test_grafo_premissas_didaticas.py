"""Premissas anteriores à fala devem preservar fonte, escopo e condições."""

from dataclasses import replace

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.grafo_premissas_didaticas import (
    CondicaoDidatica, FonteDidatica, PremissaDidatica, ReferenteAncorado,
    RegraDidatica, auditar_vinculos_literais, conferir_grafo_premissas,
    conferir_vinculo_qualificacao, conferir_qualificacao_na_conversa,
)


ESCOPO = "cenario:ensino"


def _fonte(identificador, texto, *, escopo=ESCOPO, origem="usuario"):
    return FonteDidatica(identificador, origem, escopo, texto)


def _referente(identificador, tipo, grandeza, fonte_id, citacao, *, escopo=ESCOPO):
    return ReferenteAncorado(
        ReferenteContextual(identificador, tipo, grandeza, "usuario", escopo),
        fonte_id, citacao,
    )


def _sensor():
    fontes = (
        _fonte("cenario", "Há um sensor de umidade do solo e um sensor de umidade do ar."),
        _fonte("leitura", "O sensor de umidade do solo leu 15%."),
        _fonte("regra", "No modo automático, se a umidade do solo cair abaixo de 20%, a bomba liga."),
    )
    referentes = (
        _referente("solo", "sensor", "umidade do solo", "cenario", "sensor de umidade do solo"),
        _referente("ar", "sensor", "umidade do ar", "cenario", "sensor de umidade do ar"),
        _referente("modo", "modo", "automático", "regra", "modo automático"),
        _referente("bomba", "atuador", "ligar", "regra", "bomba liga"),
    )
    premissas = (
        PremissaDidatica("p_leitura", "solo", "umidade do solo", "15", "%",
                         "leitura", "O sensor de umidade do solo leu 15%"),
    )
    regras = (
        RegraDidatica(
            "r_bomba", (
                CondicaoDidatica("solo", "umidade do solo", "<", "20", "%",
                                 "regra", "umidade do solo cair abaixo de 20%"),
                CondicaoDidatica("modo", "modo", "=", "automático", "",
                                 "regra", "modo automático"),
            ), "bomba", "estado", "liga", "regra",
            "No modo automático, se a umidade do solo cair abaixo de 20%, a bomba liga.",
        ),
    )
    return fontes, referentes, premissas, regras


def _qualificacao_solo(*, valor="15", limite="20", referente_premissa="solo",
                       referente_regra="solo", atributo_regra="umidade do solo",
                       rotulo_regra="seco", direcao="condicoes_suficientes"):
    fontes = (
        _fonte("cenario", "O solo e o ar são os ambientes medidos por sensores distintos."),
        _fonte("leitura", f"O sensor de umidade do solo leu {valor}%."),
        _fonte("criterio", f"Se a umidade do solo estiver abaixo de {limite}%, "
               f"o solo é {rotulo_regra}."),
    )
    referentes = (
        # Alvo da medição não é o instrumento: não usar a identidade do
        # sensor como atalho para a identidade do ambiente qualificado.
        _referente("solo", "ambiente", "umidade do solo", "cenario", "solo"),
        _referente("ar", "ambiente", "umidade do ar", "cenario", "ar"),
    )
    premissas = (PremissaDidatica(
        "p_leitura", referente_premissa, "umidade do solo", valor, "%",
        "leitura", f"O sensor de umidade do solo leu {valor}%",
    ),)
    regras = (RegraDidatica(
        "r_qualificacao", (CondicaoDidatica(
            referente_regra, atributo_regra, "<", limite, "%",
            "criterio", f"umidade do solo estiver abaixo de {limite}%",
        ),), "solo", "estado", rotulo_regra, "criterio",
        fontes[2].texto, conectivo_condicoes="unico",
        direcao_implicacao=direcao,
    ),)
    return fontes, referentes, premissas, regras


def _vinculo_qualificacao(grafo, *, rotulo="seco"):
    return conferir_vinculo_qualificacao(
        *grafo, escopo=ESCOPO, premissa_id="p_leitura",
        regra_id="r_qualificacao", rotulo=rotulo,
    )


def test_qualificacao_exige_mesmo_referente_atributo_e_regra_ancorada():
    alinhado = _vinculo_qualificacao(_qualificacao_solo())
    assert alinhado["estado"] == "condicao_numerica_satisfeita_relacao_pendente"
    assert alinhado["comparacao_numerica"] is True
    assert alinhado["relacao_semantica_verificada"] is False
    assert alinhado["aprovado_para_compor"] is False
    for grafo in (
        _qualificacao_solo(referente_premissa="ar"),
        _qualificacao_solo(referente_regra="ar"),
        _qualificacao_solo(atributo_regra="temperatura"),
    ):
        resultado = _vinculo_qualificacao(grafo)
        assert resultado["estado"] != "condicao_numerica_satisfeita_relacao_pendente"
        assert resultado["comparacao_numerica"] is False


def test_fixture_historica_nao_pode_tratar_sensor_como_solo():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    fontes = (replace(fontes[0], texto="Há um sensor de umidade do solo e ar."),
              *fontes[1:])
    instrumento = _referente("solo", "sensor", "umidade do solo", "cenario",
                             "sensor de umidade do solo")
    resultado = _vinculo_qualificacao((
        fontes, (instrumento, referentes[1]), premissas, regras,
    ))
    assert resultado["estado"] == "sujeito_efeito_pendente"
    assert resultado["comparacao_numerica"] is False
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_aceita_citacao_longa_com_virgula_apos_limiar():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    condicao = replace(regras[0].condicoes[0], citacao=fontes[2].texto)
    regra = replace(regras[0], condicoes=(condicao,))
    resultado = _vinculo_qualificacao(
        (fontes, referentes, premissas, (regra,)),
    )
    assert resultado["estado"] == "condicao_numerica_satisfeita_relacao_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_efeito_auditado_na_fonte_integral_nao_no_recorte_do_proponente():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    # O grafo mantém uma citação válida, mas omite a ressalva da mesma fonte.
    fonte = replace(fontes[-1], texto=fontes[-1].texto + " Exceto no modo manual.")
    resultado = _vinculo_qualificacao((
        (*fontes[:-1], fonte), referentes, premissas, regras,
    ))
    assert resultado["estado"] == "efeito_qualificativo_pendente"
    assert resultado["comparacao_numerica"] is False
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_nao_usa_regra_de_outro_rotulo_ou_direcao():
    rotulo = _vinculo_qualificacao(
        _qualificacao_solo(rotulo_regra="úmido"), rotulo="seco",
    )
    assert rotulo["estado"] == "rotulo_divergente"
    direcao = _vinculo_qualificacao(
        _qualificacao_solo(direcao="condicoes_necessarias"),
    )
    assert direcao["estado"] == "direcao_implicacao_pendente"
    assert not rotulo["aprovado_para_compor"]
    assert not direcao["aprovado_para_compor"]


def test_qualificacao_nao_marca_condicao_numerica_quando_limiar_falha():
    resultado = _vinculo_qualificacao(_qualificacao_solo(valor="15", limite="10"))
    assert resultado["estado"] == "condicao_numerica_nao_satisfeita"
    assert resultado["comparacao_numerica"] is False
    assert resultado["aprovado_para_compor"] is False


def test_vinculo_tipado_tambem_funciona_para_tensao_de_bateria():
    fontes = (
        _fonte("cenario", "Há uma bateria; sua tensão será medida."),
        _fonte("leitura", "A tensão da bateria mediu 11 V."),
        _fonte("criterio", "Se a tensão da bateria ficar abaixo de 12 V, "
               "a bateria é fraca."),
    )
    referentes = (_referente(
        "bateria", "dispositivo", "tensão da bateria", "cenario", "bateria",
    ),)
    premissas = (PremissaDidatica(
        "leitura_bateria", "bateria", "tensão da bateria", "11", "V",
        "leitura", "A tensão da bateria mediu 11 V",
    ),)
    regras = (RegraDidatica(
        "faixa_bateria", (CondicaoDidatica(
            "bateria", "tensão da bateria", "<", "12", "V", "criterio",
            "tensão da bateria ficar abaixo de 12 V",
        ),), "bateria", "estado", "fraca", "criterio", fontes[2].texto,
        conectivo_condicoes="unico",
        direcao_implicacao="condicoes_suficientes",
    ),)
    resultado = conferir_vinculo_qualificacao(
        fontes, referentes, premissas, regras, escopo=ESCOPO,
        premissa_id="leitura_bateria", regra_id="faixa_bateria",
        rotulo="fraca",
    )
    assert resultado["estado"] == "condicao_numerica_satisfeita_relacao_pendente"
    assert resultado["relacao_semantica_verificada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_regra_de_ligar_bomba_nao_define_por_si_o_rotulo_seco():
    resultado = conferir_vinculo_qualificacao(
        *_sensor(), escopo=ESCOPO, premissa_id="p_leitura",
        regra_id="r_bomba", rotulo="seco",
    )
    assert resultado["estado"] == "rotulo_divergente"
    assert resultado["relacao_semantica_verificada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_na_conversa_abstem_sem_criterio_observado():
    fontes, referentes, premissas, _ = _qualificacao_solo()
    resultado = conferir_qualificacao_na_conversa(
        fontes[:2], referentes, premissas, (), escopo=ESCOPO,
        premissa_id="p_leitura", regra_id="r_qualificacao", rotulo="seco",
        texto_atual=fontes[1].texto,
        mensagens=[{"role": "user", "content": fontes[0].texto}],
    )
    assert resultado["estado"] == "qualificacao_sem_criterio_observado"
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_na_conversa_recusa_criterio_inventado_ou_de_assistente():
    grafo = _qualificacao_solo()
    fontes = grafo[0]
    for mensagens in (
        [{"role": "user", "content": fontes[0].texto}],
        [{"role": "user", "content": fontes[0].texto},
         {"role": "assistant", "content": fontes[2].texto}],
    ):
        resultado = conferir_qualificacao_na_conversa(
            *grafo, escopo=ESCOPO, premissa_id="p_leitura",
            regra_id="r_qualificacao", rotulo="seco",
            texto_atual=fontes[1].texto, mensagens=mensagens,
        )
        assert resultado["estado"] == "fonte_nao_observada"
        assert resultado["comparacao_numerica"] is False
        assert resultado["aprovado_para_compor"] is False


def test_qualificacao_na_conversa_exige_fonte_integral_para_nao_esconder_condicao():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    texto_integral = fontes[2].texto + " Apenas se houver irrigação ativa."
    resultado = conferir_qualificacao_na_conversa(
        fontes, referentes, premissas, regras, escopo=ESCOPO,
        premissa_id="p_leitura", regra_id="r_qualificacao", rotulo="seco",
        texto_atual=fontes[1].texto, mensagens=[
            {"role": "user", "content": fontes[0].texto},
            {"role": "user", "content": texto_integral},
        ],
    )
    assert resultado["estado"] == "fonte_nao_observada"
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_na_conversa_ancorada_ainda_requer_revisao_semantica():
    for grafo, premissa_id, regra_id, rotulo in (
        (_qualificacao_solo(), "p_leitura", "r_qualificacao", "seco"),
        (_sensor(), "p_leitura", "r_bomba", "seco"),
    ):
        fontes = grafo[0]
        resultado = conferir_qualificacao_na_conversa(
            *grafo, escopo=ESCOPO, premissa_id=premissa_id,
            regra_id=regra_id, rotulo=rotulo,
            texto_atual=fontes[-1].texto,
            mensagens=[{"role": "user", "content": item.texto}
                       for item in fontes[:-1]],
        )
        esperado = ("condicao_numerica_satisfeita_relacao_pendente"
                    if regra_id == "r_qualificacao" else "rotulo_divergente")
        assert resultado["estado"] == esperado
        assert resultado["aprovado_para_compor"] is False


def test_qualificacao_na_conversa_nao_aceita_pesquisa_autodeclarada():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    fontes = (*fontes[:-1], replace(fontes[-1], origem="pesquisa_verificada"))
    resultado = conferir_qualificacao_na_conversa(
        fontes, referentes, premissas, regras, escopo=ESCOPO,
        premissa_id="p_leitura", regra_id="r_qualificacao", rotulo="seco",
        texto_atual=fontes[1].texto,
        mensagens=[{"role": "user", "content": item.texto}
                   for item in (fontes[0], fontes[2])],
    )
    assert resultado["estado"] == "fonte_sem_registro_confiavel"
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_na_conversa_nao_recupera_regra_de_sessao_expirada():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    mensagens = [{"role": "user", "content": fontes[2].texto}]
    mensagens.extend(
        {"role": "user", "content": f"Turno intermediário {indice}."}
        for indice in range(7)
    )
    mensagens.append({"role": "user", "content": fontes[0].texto})
    resultado = conferir_qualificacao_na_conversa(
        fontes, referentes, premissas, regras, escopo=ESCOPO,
        premissa_id="p_leitura", regra_id="r_qualificacao", rotulo="seco",
        texto_atual=fontes[1].texto,
        mensagens=mensagens,
    )
    assert resultado["estado"] == "fonte_nao_observada"
    assert resultado["aprovado_para_compor"] is False


def test_qualificacao_na_conversa_generaliza_para_tensao_de_bateria():
    fontes = (
        _fonte("contexto", "A bateria tem um medidor de tensão."),
        _fonte("leitura", "A tensão da bateria mediu 11 V."),
        _fonte("criterio", "Se a tensão da bateria ficar abaixo de 12 V, "
               "a bateria é fraca."),
    )
    referentes = (_referente(
        "bateria", "dispositivo", "tensão da bateria", "contexto", "bateria",
    ),)
    premissas = (PremissaDidatica(
        "medicao", "bateria", "tensão da bateria", "11", "V",
        "leitura", "tensão da bateria mediu 11 V",
    ),)
    regras = (RegraDidatica(
        "faixa", (CondicaoDidatica(
            "bateria", "tensão da bateria", "<", "12", "V", "criterio",
            "tensão da bateria ficar abaixo de 12 V",
        ),), "bateria", "estado", "fraca", "criterio", fontes[2].texto,
        conectivo_condicoes="unico", direcao_implicacao="condicoes_suficientes",
    ),)
    argumentos = dict(
        escopo=ESCOPO, premissa_id="medicao", regra_id="faixa", rotulo="fraca",
        texto_atual=fontes[1].texto,
    )
    sem_regra = conferir_qualificacao_na_conversa(
        fontes, referentes, premissas, regras,
        mensagens=[{"role": "user", "content": fontes[0].texto}], **argumentos,
    )
    com_regra = conferir_qualificacao_na_conversa(
        fontes, referentes, premissas, regras,
        mensagens=[{"role": "user", "content": fontes[0].texto},
                   {"role": "user", "content": fontes[2].texto}], **argumentos,
    )
    assert sem_regra["estado"] == "fonte_nao_observada"
    assert com_regra["estado"] == "condicao_numerica_satisfeita_relacao_pendente"
    assert not com_regra["aprovado_para_compor"]


def test_qualificacao_na_conversa_falha_fechada_com_fonte_malformada():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    fontes = (*fontes[:-1], replace(fontes[-1], texto=["regra inventada"]))
    resultado = conferir_qualificacao_na_conversa(
        fontes, referentes, premissas, regras, escopo=ESCOPO,
        premissa_id="p_leitura", regra_id="r_qualificacao", rotulo="seco",
        texto_atual=fontes[1].texto,
        mensagens=[{"role": "user", "content": fontes[0].texto}],
    )
    assert resultado["estado"] == "entrada_invalida"
    assert resultado["aprovado_para_compor"] is False


def test_direcao_proposta_nao_pode_inverter_apenas_se_da_fonte():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    texto = "O solo é seco apenas se a umidade do solo estiver abaixo de 20%."
    regra = replace(regras[0], citacao=texto)
    resultado = _vinculo_qualificacao((
        (*fontes[:-1], replace(fontes[-1], texto=texto)),
        referentes, premissas, (regra,),
    ))
    assert resultado["estado"] == "direcao_literal_divergente"
    assert resultado["comparacao_numerica"] is False
    assert resultado["aprovado_para_compor"] is False


def test_campos_malformados_do_grafo_falham_fechados_sem_excecao():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    condicao = regras[0].condicoes[0]
    variantes = (
        ((fontes[0], fontes[1], replace(fontes[2], origem=["usuario"])),
         referentes, premissas, regras),
        (fontes, referentes, premissas,
         (replace(regras[0], direcao_implicacao=["condicoes_suficientes"]),)),
        (fontes, referentes, premissas,
         (replace(regras[0], condicoes=(replace(condicao, operador=["<"]),)),)),
        (fontes, (replace(referentes[0], fonte_id=["cenario"]), referentes[1]),
         premissas, regras),
        (fontes, referentes, (replace(premissas[0], fonte_id=["leitura"]),),
         regras),
        (fontes, referentes, (replace(premissas[0], referente_id=["solo"]),),
         regras),
        (fontes, referentes, premissas,
         (replace(regras[0], fonte_id=["criterio"]),)),
        (fontes, referentes, premissas,
         (replace(regras[0], efeito_referente_id=["solo"]),)),
        (fontes, referentes, premissas,
         (replace(regras[0], condicoes=(replace(
             condicao, fonte_id=["criterio"]),)),)),
        (fontes, referentes, premissas,
         (replace(regras[0], condicoes=(replace(
             condicao, referente_id=["solo"]),)),)),
    )
    for grafo in variantes:
        resultado = _vinculo_qualificacao(grafo)
        assert resultado["estado"] == "grafo_invalido"
        assert resultado["aprovado_para_compor"] is False


def test_sensor_dois_referentes_regra_condicional_sem_inferir_modo_ativo():
    fontes, referentes, premissas, regras = _sensor()
    resultado = conferir_grafo_premissas(
        fontes, referentes, premissas, regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "estrutura_ancorada_revisao_pendente"
    assert resultado["referentes"] == ["solo", "ar", "modo", "bomba"]
    assert resultado["condicoes_por_regra"]["r_bomba"] == 2
    assert resultado["condicoes_satisfeitas"] is False
    assert resultado["consequencias_observadas"] is False
    assert resultado["aprovado_para_compor"] is False
    assert resultado["autoriza_efeito"] is False


def test_citacao_inventada_nao_ancora_premissa():
    fontes, referentes, premissas, regras = _sensor()
    alterada = PremissaDidatica("p_leitura", "solo", "umidade do solo", "15", "%",
                                "leitura", "O sensor leu 15% de glicose")
    resultado = conferir_grafo_premissas(
        fontes, referentes, (alterada,), regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "citacao_invalida"


def test_referente_de_outro_escopo_nao_pode_entrar_na_regra():
    fontes, referentes, premissas, regras = _sensor()
    outro = _referente("solo", "sensor", "umidade do solo", "cenario",
                      "sensor de umidade do solo", escopo="cenario:anterior")
    resultado = conferir_grafo_premissas(
        fontes, (outro, *referentes[1:]), premissas, regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "escopo_divergente"


def test_texto_da_assistente_nao_vira_fonte_de_regra():
    fontes, referentes, premissas, regras = _sensor()
    fonte_assistente = _fonte("regra", fontes[-1].texto, origem="assistente")
    resultado = conferir_grafo_premissas(
        (*fontes[:-1], fonte_assistente), referentes, premissas, regras,
        escopo=ESCOPO,
    )
    assert resultado["estado"] == "origem_sem_autoridade"


def test_programacao_tambem_mantem_condicao_antes_da_resposta():
    fontes = (
        _fonte("funcao", "A função retorna True se x > 0; caso contrário False."),
        _fonte("valor", "Nesta chamada, x vale 3."),
    )
    referentes = (
        _referente("x", "variavel", "valor", "funcao", "x"),
        _referente("saida", "funcao", "retorno", "funcao", "função retorna"),
    )
    premissas = (PremissaDidatica("p_x", "x", "valor", "3", "", "valor", "x vale 3"),)
    regras = (RegraDidatica(
        "r_funcao", (CondicaoDidatica("x", "valor", ">", "0", "",
                                       "funcao", "x > 0"),),
        "saida", "retorno", "True", "funcao", "A função retorna True se x > 0",
    ),)
    resultado = conferir_grafo_premissas(
        fontes, referentes, premissas, regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "estrutura_ancorada_revisao_pendente"
    assert resultado["condicoes_por_regra"] == {"r_funcao": 1}
    assert resultado["aprovado_para_compor"] is False


def test_valor_numerico_ausente_da_citacao_nao_vira_premissa():
    fontes, referentes, _, regras = _sensor()
    premissa = PremissaDidatica(
        "p_leitura", "solo", "umidade do solo", "20", "%",
        "leitura", "O sensor de umidade do solo leu 15%",
    )
    resultado = conferir_grafo_premissas(
        fontes, referentes, (premissa,), regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "valor_sem_ancora_literal"


def test_valor_com_espaco_antes_da_unidade_permanece_ancorado():
    fontes, referentes, _, regras = _sensor()
    fonte = _fonte("leitura", "O sensor de umidade do solo leu 15 %.")
    premissa = PremissaDidatica(
        "p_leitura", "solo", "umidade do solo", "15", "%",
        "leitura", "O sensor de umidade do solo leu 15 %",
    )
    resultado = conferir_grafo_premissas(
        (fontes[0], fonte, fontes[2]), referentes, (premissa,), regras,
        escopo=ESCOPO,
    )
    assert resultado["estado"] == "estrutura_ancorada_revisao_pendente"


def test_condicao_numerica_ancorada_admite_pontuacao_apos_unidade():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    condicao = replace(regras[0].condicoes[0], citacao=fontes[2].texto)
    regra = replace(regras[0], condicoes=(condicao,))
    resultado = conferir_grafo_premissas(
        fontes, referentes, premissas, (regra,), escopo=ESCOPO,
    )
    assert resultado["estado"] == "estrutura_ancorada_revisao_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_limiar_sem_unidade_admite_virgula_da_oracao_sem_aceitar_decimal():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    fonte = replace(fontes[2], texto=fontes[2].texto.replace("20%", "20"))
    condicao = replace(
        regras[0].condicoes[0], unidade="", citacao=fonte.texto,
    )
    regra = replace(regras[0], citacao=fonte.texto, condicoes=(condicao,))
    resultado = conferir_grafo_premissas(
        (*fontes[:2], fonte), referentes, premissas, (regra,), escopo=ESCOPO,
    )
    assert resultado["estado"] == "estrutura_ancorada_revisao_pendente"


def test_ancora_numerica_nao_aceita_prefixo_de_unidade_ou_decimal():
    fontes, referentes, premissas, regras = _qualificacao_solo()
    fonte_extensao = replace(
        fontes[2], texto=fontes[2].texto.replace("20%", "20%2"),
    )
    regra_extensao = replace(
        regras[0], citacao=fonte_extensao.texto,
        condicoes=(replace(
            regras[0].condicoes[0], citacao=fonte_extensao.texto,
        ),),
    )
    extensao = conferir_grafo_premissas(
        (*fontes[:2], fonte_extensao), referentes, premissas,
        (regra_extensao,), escopo=ESCOPO,
    )
    assert extensao["estado"] == "valor_sem_ancora_literal"

    fonte_decimal = replace(
        fontes[2], texto=fontes[2].texto.replace("20%", "20,5"),
    )
    regra_decimal = replace(
        regras[0], citacao=fonte_decimal.texto,
        condicoes=(replace(
            regras[0].condicoes[0], unidade="", citacao=fonte_decimal.texto,
        ),),
    )
    decimal = conferir_grafo_premissas(
        (*fontes[:2], fonte_decimal), referentes, premissas,
        (regra_decimal,), escopo=ESCOPO,
    )
    assert decimal["estado"] == "valor_sem_ancora_literal"


def test_valor_20_nao_casa_com_120_mesmo_com_espaco_na_unidade():
    fontes, referentes, _, regras = _sensor()
    fonte = _fonte("leitura", "O sensor de umidade do solo leu 120 %.")
    premissa = PremissaDidatica(
        "p_leitura", "solo", "umidade do solo", "20", "%",
        "leitura", "O sensor de umidade do solo leu 120 %",
    )
    resultado = conferir_grafo_premissas(
        (fontes[0], fonte, fontes[2]), referentes, (premissa,), regras,
        escopo=ESCOPO,
    )
    assert resultado["estado"] == "valor_sem_ancora_literal"


def test_referente_nao_declarado_nao_pode_ser_usado_pela_regra():
    fontes, referentes, premissas, regras = _sensor()
    resultado = conferir_grafo_premissas(
        fontes, referentes[:-1], premissas, regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "referente_desconhecido"


def test_floricultura_preserva_clima_como_condicao_nao_como_fato_atual():
    fontes = (_fonte(
        "cultivo", "Em climas frios, begônias podem ser cultivadas como anuais."
    ),)
    referentes = (
        _referente("clima", "ambiente", "temperatura", "cultivo", "climas frios"),
        _referente("flor", "planta", "cultivo", "cultivo", "begônias"),
    )
    regras = (RegraDidatica(
        "r_cultivo", (CondicaoDidatica(
            "clima", "faixa", "=", "frios", "", "cultivo", "climas frios"
        ),), "flor", "cultivo", "anuais", "cultivo",
        "Em climas frios, begônias podem ser cultivadas como anuais.",
    ),)
    resultado = conferir_grafo_premissas(
        fontes, referentes, (), regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "estrutura_ancorada_revisao_pendente"
    assert resultado["condicoes_por_regra"] == {"r_cultivo": 1}
    assert resultado["condicoes_satisfeitas"] is False
    assert resultado["aprovado_para_compor"] is False


def test_ancora_literal_nao_prova_que_leitura_pertence_ao_sensor_certo():
    fontes, referentes, _, regras = _sensor()
    premissa = PremissaDidatica(
        "p_leitura", "ar", "umidade", "15", "%",
        "leitura", "O sensor de umidade do solo leu 15%",
    )
    resultado = conferir_grafo_premissas(
        fontes, referentes, (premissa,), regras, escopo=ESCOPO,
    )
    # A âncora passa; o vínculo semântico falso continua pendente e não
    # recebe permissão de entrar na fala.
    assert resultado["estado"] == "estrutura_ancorada_revisao_pendente"
    assert resultado["anotacao_semantica_revisada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_auditoria_localiza_leitura_e_direcao_explicitas_sem_inferir_efeito():
    resultado = auditar_vinculos_literais(*_sensor(), escopo=ESCOPO)
    assert resultado["estado"] == "pistas_literais_revisao_pendente"
    assert resultado["premissas"]["p_leitura"] == "referente_literal_localizado"
    assert resultado["condicoes"]["r_bomba"][0]["referente"] == "referente_literal_localizado"
    assert resultado["condicoes"]["r_bomba"][0]["direcao"] == "direcao_literal_coerente"
    assert resultado["condicoes"]["r_bomba"][1]["direcao"] == "direcao_indeterminada"
    assert resultado["anotacao_semantica_revisada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_auditoria_nao_aceita_o_sensor_de_ar_por_citacao_do_solo():
    fontes, referentes, _, regras = _sensor()
    trocada = PremissaDidatica(
        "p_leitura", "ar", "umidade", "15", "%",
        "leitura", "O sensor de umidade do solo leu 15%",
    )
    resultado = auditar_vinculos_literais(
        fontes, referentes, (trocada,), regras, escopo=ESCOPO,
    )
    assert resultado["premissas"]["p_leitura"] == "referente_sem_ancora_literal"
    assert resultado["aprovado_para_compor"] is False


def test_auditoria_detecta_inversao_explicita_do_limiar():
    fontes, referentes, premissas, regras = _sensor()
    condicao = regras[0].condicoes[0]
    invertida = CondicaoDidatica(
        condicao.referente_id, condicao.atributo, ">", condicao.valor,
        condicao.unidade, condicao.fonte_id, condicao.citacao,
    )
    regra = RegraDidatica(
        regras[0].identificador, (invertida, regras[0].condicoes[1]),
        regras[0].efeito_referente_id, regras[0].efeito_atributo,
        regras[0].efeito_valor, regras[0].fonte_id, regras[0].citacao,
    )
    resultado = auditar_vinculos_literais(
        fontes, referentes, premissas, (regra,), escopo=ESCOPO,
    )
    assert resultado["condicoes"]["r_bomba"][0]["direcao"] == "direcao_literal_divergente"


def test_auditoria_nao_confunde_regra_condicional_com_estado_observado():
    fontes = (_fonte("flora", "Em climas frios, begônias podem ser cultivadas como anuais."),)
    referentes = (
        _referente("clima", "ambiente", "temperatura", "flora", "climas frios"),
        _referente("flor", "planta", "cultivo", "flora", "begônias"),
    )
    regras = (RegraDidatica(
        "r_flora", (CondicaoDidatica(
            "clima", "faixa", "=", "frios", "", "flora", "climas frios",
        ),), "flor", "cultivo", "anuais", "flora",
        "Em climas frios, begônias podem ser cultivadas como anuais.",
    ),)
    resultado = auditar_vinculos_literais(
        fontes, referentes, (), regras, escopo=ESCOPO,
    )
    assert resultado["condicoes"]["r_flora"][0]["referente"] == "referente_literal_localizado"
    assert resultado["condicoes"]["r_flora"][0]["direcao"] == "direcao_indeterminada"
    assert resultado["condicoes_satisfeitas"] is False
    assert resultado["consequencias_observadas"] is False


def test_auditoria_preserva_direcao_explicita_em_programacao():
    fontes = (_fonte("codigo", "A função retorna True se x > 0."),)
    referentes = (
        _referente("x", "variavel", "valor", "codigo", "x"),
        _referente("retorno", "funcao", "saida", "codigo", "função retorna"),
    )
    regras = (RegraDidatica(
        "r_codigo", (CondicaoDidatica(
            "x", "valor", ">", "0", "", "codigo", "x > 0",
        ),), "retorno", "retorno", "True", "codigo",
        "A função retorna True se x > 0.",
    ),)
    resultado = auditar_vinculos_literais(
        fontes, referentes, (), regras, escopo=ESCOPO,
    )
    assert resultado["condicoes"]["r_codigo"][0] == {
        "referente": "referente_literal_localizado",
        "direcao": "direcao_literal_coerente",
    }
    assert resultado["aprovado_para_compor"] is False


def test_negacao_de_abaixo_nao_confirma_direcao_da_regra():
    fontes, referentes, premissas, regras = _sensor()
    fonte = _fonte(
        "regra", "No modo automático, se a umidade do solo não cair abaixo de 20%, a bomba liga."
    )
    regra = RegraDidatica(
        "r_bomba", (
            CondicaoDidatica(
                "solo", "umidade do solo", "<", "20", "%", "regra",
                "umidade do solo não cair abaixo de 20%",
            ),
            regras[0].condicoes[1],
        ), "bomba", "estado", "liga", "regra", fonte.texto,
    )
    resultado = auditar_vinculos_literais(
        (*fontes[:-1], fonte), referentes, premissas, (regra,), escopo=ESCOPO,
    )
    assert resultado["condicoes"]["r_bomba"][0]["direcao"] == "direcao_indeterminada"
    assert resultado["aprovado_para_compor"] is False


def test_auditoria_nao_trabalha_sobre_fonte_invalida():
    fontes, referentes, premissas, regras = _sensor()
    alterada = PremissaDidatica(
        "p_leitura", "solo", "umidade do solo", "15", "%",
        "leitura", "O sensor leu 15% de glicose",
    )
    resultado = auditar_vinculos_literais(
        fontes, referentes, (alterada,), regras, escopo=ESCOPO,
    )
    assert resultado["estado"] == "citacao_invalida"
    assert resultado["premissas"] == {}
