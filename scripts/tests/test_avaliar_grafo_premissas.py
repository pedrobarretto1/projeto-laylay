"""Cenários novos, com rótulos manuais separados do auditor literal."""

import json
from pathlib import Path

from mente_laylay.cognicao.contrato_inventario_contextual import ReferenteContextual
from scripts.analises.avaliar_grafo_premissas import (
    confrontar_condicoes_revisadas, confrontar_gabarito,
)
from scripts.analises.grafo_premissas_didaticas import (
    CondicaoDidatica, FonteDidatica, PremissaDidatica, ReferenteAncorado,
    RegraDidatica, auditar_vinculos_literais,
)


GABARITO = json.loads((Path(__file__).parents[1] / "analises" / "dados" /
                      "gabarito_grafo_didatico_v1.json").read_text(encoding="utf-8"))["casos"]


def _caso(id_caso, fontes, referentes, premissas, regras):
    escopo = f"avaliacao:{id_caso.lower()}"
    fontes_t = tuple(FonteDidatica(nome, "usuario", escopo, texto)
                     for nome, texto in fontes)
    referentes_t = tuple(ReferenteAncorado(
        ReferenteContextual(nome, tipo, grandeza, "usuario", escopo), fonte, citacao,
    ) for nome, tipo, grandeza, fonte, citacao in referentes)
    regras_t = tuple(regras)
    auditoria = auditar_vinculos_literais(
        fontes_t, referentes_t, tuple(premissas), regras_t, escopo=escopo,
    )
    gabarito = GABARITO[id_caso]
    regras_revisadas = tuple(RegraDidatica(
        **{**item, "condicoes": tuple(CondicaoDidatica(**condicao)
                                     for condicao in item["condicoes"])}
    ) for item in gabarito["regras_revisadas"])
    cobertura = confrontar_condicoes_revisadas(
        fontes_t, referentes_t, regras_t, regras_revisadas, escopo=escopo,
    )
    return confrontar_gabarito(auditoria, gabarito, cobertura=cobertura)


def test_camara_contraste_positivo_explicito_sem_declarar_alarme_real():
    resultado = _caso(
        "CAMARA",
        (("cenario", "Há um sensor da câmara e um sensor do corredor."),
         ("leitura", "O sensor da câmara marcou 3°C."),
         ("regra", "Se a temperatura da câmara ficar acima de 5°C, o alarme toca.")),
        (("camara", "sensor", "temperatura da câmara", "cenario", "sensor da câmara"),
         ("corredor", "sensor", "temperatura do corredor", "cenario", "sensor do corredor"),
         ("alarme", "atuador", "tocar", "regra", "alarme toca")),
        (PremissaDidatica("p_leitura", "camara", "temperatura", "3", "°C",
                           "leitura", "O sensor da câmara marcou 3°C"),),
        (RegraDidatica("r_alarme", (
            CondicaoDidatica("camara", "temperatura", ">", "5", "°C",
                             "regra", "temperatura da câmara ficar acima de 5°C"),
        ), "alarme", "estado", "toca", "regra",
            "Se a temperatura da câmara ficar acima de 5°C, o alarme toca.",
            "unico", "condicoes_suficientes"),),
    )
    assert resultado["estado"] == "confronto_diagnostico", (
        resultado.get("slots_faltantes"), resultado.get("slots_extras"), resultado)
    assert resultado["contagens"]["pista_compatível"] == 4
    assert resultado["relacao_condicional"] == "slots_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_caixas_pista_literal_enganosa_com_mesma_frase():
    resultado = _caso(
        "CAIXAS",
        (("pesos", "A caixa azul pesa 8 kg; a caixa vermelha pesa 5 kg."),
         ("regra", "Se a caixa vermelha pesar acima de 7 kg, o selo aparece.")),
        (("azul", "caixa", "peso azul", "pesos", "caixa azul"),
         ("vermelha", "caixa", "peso vermelho", "pesos", "caixa vermelha"),
         ("selo", "indicador", "mostrar", "regra", "selo aparece")),
        (PremissaDidatica("p_peso", "vermelha", "peso", "8", "kg",
                           "pesos", "A caixa azul pesa 8 kg; a caixa vermelha pesa 5 kg"),),
        (RegraDidatica("r_selo", (
            CondicaoDidatica("vermelha", "peso", ">", "7", "kg",
                             "regra", "caixa vermelha pesar acima de 7 kg"),
        ), "selo", "estado", "aparece", "regra",
            "Se a caixa vermelha pesar acima de 7 kg, o selo aparece.",
            "unico", "condicoes_suficientes"),),
    )
    assert resultado["contagens"]["pista_falso_positivo"] == 1
    assert resultado["slots"]["premissa:p_peso"] == "pista_falso_positivo"
    assert resultado["relacao_condicional"] == "slots_e_relacao_alinhados_revisao_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_medidor_correfencia_correta_nao_repetida_na_citacao_curta():
    resultado = _caso(
        "MEDIDOR",
        (("contexto", "O medidor do quarto é o equipamento citado a seguir."),
         ("leitura", "O equipamento registrou 30°C."),
         ("regra", "Se a temperatura do quarto ficar acima de 28°C, o ventilador liga.")),
        (("quarto", "medidor", "temperatura do quarto", "contexto", "medidor do quarto"),
         ("ventilador", "atuador", "ligar", "regra", "ventilador liga")),
        (PremissaDidatica("p_temperatura", "quarto", "temperatura", "30", "°C",
                           "leitura", "O equipamento registrou 30°C"),),
        (RegraDidatica("r_ventilador", (
            CondicaoDidatica("quarto", "temperatura", ">", "28", "°C",
                             "regra", "temperatura do quarto ficar acima de 28°C"),
        ), "ventilador", "estado", "liga", "regra",
            "Se a temperatura do quarto ficar acima de 28°C, o ventilador liga.",
            "unico", "condicoes_suficientes"),),
    )
    assert resultado["contagens"].get("abstencao_em_correto") == 1, (
        resultado.get("slots_faltantes"), resultado.get("slots_extras"), resultado)
    assert resultado["slots"]["premissa:p_temperatura"] == "abstencao_em_correto"
    assert resultado["relacao_condicional"] == "slots_e_relacao_alinhados_revisao_pendente"


def test_cache_omite_condicao_apesar_de_pistas_locais_positivas():
    texto = "O cache devolve a resposta somente quando a chave coincide e o registro está válido."
    chave = CondicaoDidatica("chave", "estado", "=", "coincide", "",
                              "regra", "a chave coincide")
    proposta = RegraDidatica(
        "r_cache", (chave,), "cache", "resultado", "devolve", "regra", texto,
    )
    resultado = _caso(
        "CACHE",
        (("regra", texto),),
        (("cache", "servico", "devolver", "regra", "O cache"),
         ("chave", "identificador", "coincidencia", "regra", "a chave"),
         ("registro", "item", "validade", "regra", "registro")),
        (),
        (proposta,),
    )
    assert resultado["contagens"]["pista_compatível"] == 2
    assert resultado["contagens"]["abstencao_em_correto"] == 1
    assert resultado["cobertura_condicoes"] == "condicao_omitida"
    assert resultado["relacao_condicional"] == "nao_avaliada_por_condicoes"
    assert resultado["aprovado_para_compor"] is False


def test_gabarito_incompleto_nao_gera_placar_parcial():
    auditoria = {
        "estado": "pistas_literais_revisao_pendente",
        "premissas": {"p": "referente_literal_localizado"},
        "condicoes": {}, "efeitos": {},
    }
    resultado = confrontar_gabarito(
        auditoria, {"slots": {}, "condicoes_completas": True},
    )
    assert resultado["estado"] == "avaliacao_invalida"
    assert resultado["contagens"] == {}
    assert resultado["aprovado_para_compor"] is False


def test_fonte_invalida_nao_pode_ser_avaliada_como_vinculo():
    auditoria = {"estado": "citacao_invalida", "premissas": {},
                 "condicoes": {}, "efeitos": {}}
    resultado = confrontar_gabarito(
        auditoria, {"slots": {"premissa:p": True}, "condicoes_completas": True},
    )
    assert resultado["estado"] == "avaliacao_invalida"
    assert resultado["aprovado_para_compor"] is False


def test_auditoria_malformada_falha_fechada():
    resultado = confrontar_gabarito(
        {"estado": "pistas_literais_revisao_pendente", "premissas": {}},
        {"slots": {"premissa:p": True}, "condicoes_completas": True},
    )
    assert resultado["estado"] == "avaliacao_invalida"
    assert resultado["aprovado_para_compor"] is False


def test_placar_separa_condicoes_completas_de_conectivo_errado():
    auditoria = {
        "estado": "pistas_literais_revisao_pendente",
        "premissas": {"p": "referente_literal_localizado"},
        "condicoes": {}, "efeitos": {},
    }
    resultado = confrontar_gabarito(
        auditoria,
        {"slots": {"premissa:p": True}, "condicoes_completas": True},
        cobertura={"estado": "conectivo_divergente",
                   "slots_condicoes_alinhados": True},
    )
    assert resultado["estado"] == "confronto_diagnostico"
    assert resultado["cobertura_condicoes"] == "slots_alinhados_revisao_pendente"
    assert resultado["relacao_condicional"] == "conectivo_divergente"
    assert resultado["aprovado_para_compor"] is False
