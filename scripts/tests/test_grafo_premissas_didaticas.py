"""Premissas anteriores à fala devem preservar fonte, escopo e condições."""

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.grafo_premissas_didaticas import (
    CondicaoDidatica, FonteDidatica, PremissaDidatica, ReferenteAncorado,
    RegraDidatica, auditar_vinculos_literais, conferir_grafo_premissas,
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
