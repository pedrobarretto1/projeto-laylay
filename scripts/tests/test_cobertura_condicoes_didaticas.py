"""Condições requeridas são anotadas fora da proposta e do auditor literal."""

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.avaliar_grafo_premissas import confrontar_condicoes_revisadas
from scripts.analises.grafo_premissas_didaticas import (
    CondicaoDidatica, FonteDidatica, ReferenteAncorado, RegraDidatica,
)


ESCOPO = "revisao:condicoes"


def _referente(identificador, tipo, grandeza, citacao):
    return ReferenteAncorado(
        ReferenteContextual(identificador, tipo, grandeza, "usuario", ESCOPO),
        "regra", citacao,
    )


def _cache():
    texto = "O cache devolve a resposta somente quando a chave coincide e o registro está válido."
    fontes = (FonteDidatica("regra", "usuario", ESCOPO, texto),)
    referentes = (
        _referente("cache", "servico", "devolver", "O cache"),
        _referente("chave", "identificador", "coincidencia", "a chave"),
        _referente("registro", "item", "validade", "registro"),
    )
    chave = CondicaoDidatica("chave", "estado", "=", "coincide", "",
                              "regra", "a chave coincide")
    registro = CondicaoDidatica("registro", "estado", "=", "válido", "",
                                 "regra", "registro está válido")

    def regra(condicoes, *, conectivo="indeterminado", implicacao="indeterminado"):
        return RegraDidatica("r_cache", condicoes, "cache", "resultado",
                             "devolve", "regra", texto,
                             conectivo, implicacao)

    return fontes, referentes, regra, chave, registro


def test_cache_omissao_da_validade_eh_primeira_divergencia():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra((chave,)),),
        (regra((chave, registro)),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "condicao_omitida"
    assert resultado["ausentes"][0]["referente_id"] == "registro"
    assert resultado["extras"] == []
    assert resultado["aprovado_para_compor"] is False


def test_condicoes_reordenadas_nao_viram_falha():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra((registro, chave)),),
        (regra((chave, registro)),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "slots_condicoes_alinhados_revisao_pendente"
    assert resultado["conectivo_verificado"] is False
    assert resultado["aprovado_para_compor"] is False


def test_condicao_duplicada_nao_faz_o_conjunto_parecer_completo():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra((chave, chave, registro)),),
        (regra((chave, registro)),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "condicao_extra"
    assert resultado["extras"][0]["referente_id"] == "chave"


def test_revisao_inventada_ou_de_outro_escopo_nao_serve_de_gabarito():
    fontes, referentes, regra, chave, registro = _cache()
    inventada = CondicaoDidatica(
        "registro", "estado", "=", "expirado", "", "regra",
        "registro está expirado",
    )
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra((chave,)),),
        (regra((chave, inventada)),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "referencia_invalida"
    assert resultado["aprovado_para_compor"] is False


def test_regra_com_outro_efeito_nao_compara_condicoes_isoladas():
    fontes, referentes, regra, chave, registro = _cache()
    efeito_trocado = RegraDidatica(
        "r_cache", (chave,), "registro", "resultado", "devolve", "regra",
        fontes[0].texto,
    )
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (efeito_trocado,),
        (regra((chave, registro)),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "efeito_ou_fonte_divergente"


def test_regra_de_sensor_com_modo_e_limiar_preserva_ambas_as_condicoes():
    texto = "No modo automático, se a umidade do solo cair abaixo de 20%, a bomba liga."
    fontes = (FonteDidatica("regra", "usuario", ESCOPO, texto),)
    referentes = (
        _referente("modo", "estado", "automatico", "modo automático"),
        _referente("solo", "sensor", "umidade do solo", "umidade do solo"),
        _referente("bomba", "atuador", "ligar", "bomba liga"),
    )
    modo = CondicaoDidatica("modo", "modo", "=", "automático", "",
                             "regra", "modo automático")
    limiar = CondicaoDidatica("solo", "umidade do solo", "<", "20", "%",
                               "regra", "umidade do solo cair abaixo de 20%")
    proposta = RegraDidatica("r_bomba", (limiar,), "bomba", "estado", "liga",
                              "regra", texto)
    revisada = RegraDidatica("r_bomba", (modo, limiar), "bomba", "estado",
                              "liga", "regra", texto)
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (proposta,), (revisada,), escopo=ESCOPO,
    )
    assert resultado["estado"] == "condicao_omitida"
    assert resultado["ausentes"][0]["referente_id"] == "modo"


def test_cultivo_condicional_nao_perde_a_sombra_parcial():
    texto = "Em climas frios e com sombra parcial, a begônia pode ser cultivada como anual."
    fontes = (FonteDidatica("regra", "usuario", ESCOPO, texto),)
    referentes = (
        _referente("clima", "ambiente", "temperatura", "climas frios"),
        _referente("sombra", "ambiente", "luminosidade", "sombra parcial"),
        _referente("begonia", "planta", "cultivo", "begônia"),
    )
    clima = CondicaoDidatica("clima", "faixa", "=", "frios", "",
                              "regra", "climas frios")
    sombra = CondicaoDidatica("sombra", "faixa", "=", "parcial", "",
                               "regra", "sombra parcial")
    proposta = RegraDidatica("r_cultivo", (clima,), "begonia", "cultivo",
                              "anual", "regra", texto)
    revisada = RegraDidatica("r_cultivo", (clima, sombra), "begonia", "cultivo",
                              "anual", "regra", texto)
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (proposta,), (revisada,), escopo=ESCOPO,
    )
    assert resultado["estado"] == "condicao_omitida"
    assert resultado["ausentes"][0]["referente_id"] == "sombra"
    assert resultado["aprovado_para_compor"] is False


def test_mesmos_slots_nao_provam_conjuncao_da_fonte():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra((chave, registro)),),
        (regra((chave, registro)),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "slots_condicoes_alinhados_revisao_pendente"
    assert resultado["conectivo_verificado"] is False
    assert resultado["revisao_independente_autenticada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_mesmas_condicoes_com_e_no_lugar_de_ou_divergem():
    texto = "Se a chave coincide ou o registro está válido, o cache devolve a resposta."
    fontes = (FonteDidatica("regra", "usuario", ESCOPO, texto),)
    referentes = (
        _referente("cache", "servico", "devolver", "cache devolve"),
        _referente("chave", "identificador", "coincidencia", "a chave"),
        _referente("registro", "item", "validade", "registro"),
    )
    chave = CondicaoDidatica("chave", "estado", "=", "coincide", "",
                              "regra", "a chave coincide")
    registro = CondicaoDidatica("registro", "estado", "=", "válido", "",
                                 "regra", "registro está válido")

    def regra(conectivo):
        return RegraDidatica("r_cache", (chave, registro), "cache", "resultado",
                             "devolve", "regra", texto, conectivo,
                             "condicoes_suficientes")

    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra("e"),), (regra("ou"),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "conectivo_divergente"
    assert resultado["ausentes"] == []
    assert resultado["extras"] == []
    assert resultado["aprovado_para_compor"] is False


def test_somente_quando_nao_significa_que_condicoes_bastam():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes,
        (regra((chave, registro), conectivo="e",
               implicacao="condicoes_suficientes"),),
        (regra((chave, registro), conectivo="e",
               implicacao="condicoes_necessarias"),),
        escopo=ESCOPO,
    )
    assert resultado["estado"] == "implicacao_divergente"
    assert resultado["aprovado_para_compor"] is False


def test_relacao_nao_declarada_na_proposta_permanece_pendente():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra((chave, registro)),),
        (regra((chave, registro), conectivo="e",
               implicacao="condicoes_necessarias"),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "conectivo_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_relacao_declarada_igual_ao_gabarito_ainda_nao_aprova_fala():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes,
        (regra((chave, registro), conectivo="e",
               implicacao="condicoes_necessarias"),),
        (regra((chave, registro), conectivo="e",
               implicacao="condicoes_necessarias"),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "slots_e_relacao_alinhados_revisao_pendente"
    assert resultado["conectivo_alinhado_revisao"] is True
    assert resultado["implicacao_alinhada_revisao"] is True
    assert resultado["conectivo_verificado"] is False
    assert resultado["aprovado_para_compor"] is False


def test_sensor_com_e_na_fonte_nao_aceita_ou_na_proposta():
    texto = "No modo automático, se a umidade do solo cair abaixo de 20%, a bomba liga."
    fontes = (FonteDidatica("regra", "usuario", ESCOPO, texto),)
    referentes = (
        _referente("modo", "estado", "automatico", "modo automático"),
        _referente("solo", "sensor", "umidade do solo", "umidade do solo"),
        _referente("bomba", "atuador", "ligar", "bomba liga"),
    )
    modo = CondicaoDidatica("modo", "modo", "=", "automático", "",
                             "regra", "modo automático")
    limiar = CondicaoDidatica("solo", "umidade do solo", "<", "20", "%",
                               "regra", "umidade do solo cair abaixo de 20%")

    def regra(conectivo):
        return RegraDidatica("r_bomba", (modo, limiar), "bomba", "estado",
                             "liga", "regra", texto, conectivo,
                             "condicoes_suficientes")

    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra("ou"),), (regra("e"),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "conectivo_divergente"
    assert resultado["aprovado_para_compor"] is False


def test_se_e_somente_se_na_programacao_nao_e_apenas_suficiencia():
    texto = "A função retorna True se e somente se x > 0."
    fontes = (FonteDidatica("regra", "usuario", ESCOPO, texto),)
    referentes = (
        _referente("x", "variavel", "valor", "x"),
        _referente("saida", "funcao", "retorno", "função retorna"),
    )
    condicao = CondicaoDidatica("x", "valor", ">", "0", "", "regra", "x > 0")

    def regra(implicacao):
        return RegraDidatica("r_saida", (condicao,), "saida", "retorno",
                             "True", "regra", texto, "unico", implicacao)

    resultado = confrontar_condicoes_revisadas(
        fontes, referentes, (regra("condicoes_suficientes"),),
        (regra("equivalencia"),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "implicacao_divergente"
    assert resultado["aprovado_para_compor"] is False


def test_conectivo_nao_suportado_falha_antes_da_comparacao():
    fontes, referentes, regra, chave, registro = _cache()
    resultado = confrontar_condicoes_revisadas(
        fontes, referentes,
        (regra((chave, registro), conectivo="xor"),),
        (regra((chave, registro), conectivo="e"),), escopo=ESCOPO,
    )
    assert resultado["estado"] == "proposta_invalida"
    assert resultado["motivo"] == "regra_invalida"
