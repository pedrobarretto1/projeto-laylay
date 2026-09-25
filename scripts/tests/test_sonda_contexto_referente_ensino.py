"""Contexto localiza candidatos; não prova medição nem autoriza fala."""

from scripts.analises.revisao_referencias_ensino import carregar_painel
import json

from scripts.analises.sonda_contexto_referente_ensino import conferir_vinculos, medir_caso


def _caso(identificador: str) -> dict:
    return next(item for item in carregar_painel() if item["id"] == identificador)


def _vinculo(expressao: str, grandeza: str, trecho: str) -> dict[str, str]:
    return {"expressao_exemplo": expressao, "grandeza": grandeza,
            "trecho_contexto": trecho}


def test_contexto_unico_e_so_candidato_pendente() -> None:
    resultado = conferir_vinculos(_caso("REF-05"), {"vinculos": [
        _vinculo("o sensor", "umidade do solo",
                 "um único sensor, que mede exclusivamente a umidade do solo"),
    ]})
    assert resultado["estado"] == "candidato_contextual_unico_revisao_pendente"
    assert resultado["referente_resolvido"] is False
    assert resultado["contexto_autorizou_efeito"] is False
    assert resultado["aprovado_para_compor"] is False


def test_expressao_proposta_pode_incluir_acao_e_valor_sem_trocar_medidor() -> None:
    caso = _caso("REF-05")
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor leu 15% de umidade", "umidade do solo",
                 "um único sensor, que mede exclusivamente a umidade do solo"),
    ]})
    assert resultado["estado"] == "candidato_contextual_unico_revisao_pendente"
    assert resultado["referente_resolvido"] is False


def test_dois_referentes_para_mesma_expressao_sao_ambiguos() -> None:
    trecho = "um mede a umidade do solo e o outro mede a umidade do ar"
    resultado = conferir_vinculos(_caso("REF-06"), {"vinculos": [
        _vinculo("o sensor", "umidade do solo", trecho),
        _vinculo("o sensor", "umidade do ar", trecho),
    ]})
    assert resultado["estado"] == "referencia_ambigua"
    assert resultado["aprovado_para_compor"] is False


def test_contexto_inventado_e_contexto_ausente_nao_passam() -> None:
    inventado = _vinculo("o sensor", "umidade do solo",
                         "o sensor mágico mede a umidade do solo")
    assert conferir_vinculos(_caso("REF-05"), {"vinculos": [inventado]})[
        "estado"] == "trecho_contexto_sem_origem"
    assert conferir_vinculos(_caso("REF-01"), {"vinculos": [inventado]})[
        "estado"] == "trecho_contexto_sem_origem"


def test_qualificador_explicito_do_exemplo_nao_e_sobrescrito() -> None:
    caso = _caso("REF-07")
    trecho = "um sensor de umidade do solo e um sensor de umidade do ar"
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor", "umidade do solo", trecho),
    ]})
    assert resultado["estado"] == "referencia_qualificada_na_fala"
    assert resultado["aprovado_para_compor"] is False


def test_qualificador_dentro_da_expressao_proposta_nao_e_ignorado() -> None:
    caso = _caso("REF-07")
    contexto = "Existe um único sensor que mede a umidade do solo."
    caso = {**caso, "contexto": [contexto]}
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor do ar leu 15% de umidade", "umidade do solo", contexto),
    ]})
    assert resultado["estado"] == "referencia_qualificada_na_fala"
    assert resultado["referente_resolvido"] is False


def test_qualificador_compativel_na_expressao_nao_e_bloqueado() -> None:
    caso = _caso("REF-05")
    caso = {**caso, "exemplo": caso["exemplo"].replace(
        "o sensor leu", "o sensor do solo leu")}
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor do solo leu 15% de umidade", "umidade do solo",
                 "um único sensor, que mede exclusivamente a umidade do solo"),
    ]})
    assert resultado["estado"] == "candidato_contextual_unico_revisao_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_grandeza_explicita_divergente_bloqueia_inferencia_contextual() -> None:
    caso = _caso("REF-03")
    caso = {**caso, "contexto": ["O sensor mede a umidade do solo."]}
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor", "umidade do solo", "O sensor mede a umidade do solo"),
    ]})
    assert resultado["estado"] == "rotulo_explicito_divergente"
    assert resultado["aprovado_para_compor"] is False


def test_proposta_do_modelo_ve_contexto_sem_gabarito_e_fica_pendente() -> None:
    caso = _caso("REF-05")
    enviado = {}

    class Resposta:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"message": {"content": json.dumps({"vinculos": [
                _vinculo("o sensor", "umidade do solo",
                         "um único sensor, que mede exclusivamente a umidade do solo"),
            ]})}}

    def post(_url: str, **kwargs):
        enviado.update(kwargs)
        return Resposta()

    resultado = medir_caso(caso, post=post)
    entrada = enviado["json"]["messages"][1]["content"]
    assert caso["exemplo"] in entrada
    assert caso["contexto"][0] in entrada
    assert "esperado" not in entrada and "rotulo" not in entrada
    assert resultado["conferencia"]["estado"] == "candidato_contextual_unico_revisao_pendente"
    assert resultado["conferencia"]["cobertura_contexto_verificada"] is False
    assert resultado["aprovado_para_producao"] is False


def test_proposta_unica_nao_apaga_outro_sensor_citado_no_contexto() -> None:
    caso = _caso("REF-06")
    trecho = "um mede a umidade do solo e o outro mede a umidade do ar"
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor", "umidade do solo", trecho),
    ]})
    assert resultado["estado"] == "contexto_com_grandezas_concorrentes"
    assert resultado["cobertura_contexto_verificada"] is False
    assert resultado["aprovado_para_compor"] is False


def test_concorrencia_de_grandezas_nao_depende_da_palavra_umidade() -> None:
    caso = _caso("REF-09")
    caso = {**caso, "contexto": [
        "Um termômetro mede a temperatura da água e outro mede a temperatura do ar."
    ]}
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("O termômetro", "temperatura da água",
                 "Um termômetro mede a temperatura da água"),
    ]})
    assert resultado["estado"] == "contexto_com_grandezas_concorrentes"
    assert resultado["aprovado_para_compor"] is False


def test_sensor_extra_de_outra_grandeza_nao_parece_candidato_unico() -> None:
    caso = _caso("REF-05")
    caso = {**caso, "contexto": [
        "Neste cenário há dois sensores: um mede a umidade do solo e "
        "o outro mede temperatura do ar."
    ]}
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor", "umidade do solo", "um mede a umidade do solo"),
    ]})
    assert resultado["estado"] == "unicidade_do_medidor_nao_demonstrada"
    assert resultado["referente_resolvido"] is False


def test_sensor_unico_nao_pode_ser_inferido_de_ausencia_de_concorrente() -> None:
    caso = _caso("REF-05")
    caso = {**caso, "contexto": ["O sensor mede a umidade do solo."]}
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("o sensor", "umidade do solo", "O sensor mede a umidade do solo"),
    ]})
    assert resultado["estado"] == "unicidade_do_medidor_nao_demonstrada"
    assert resultado["referente_resolvido"] is False


def test_termometro_unico_declarado_permanece_so_candidato() -> None:
    caso = _caso("REF-09")
    resultado = conferir_vinculos(caso, {"vinculos": [
        _vinculo("O termômetro", "temperatura da água",
                 "há apenas um termômetro e ele mede a temperatura da água"),
    ]})
    assert resultado["estado"] == "candidato_contextual_unico_revisao_pendente"
    assert resultado["aprovado_para_compor"] is False


def test_unicidade_negada_ou_contradita_nao_cria_candidato() -> None:
    caso = _caso("REF-05")
    for contexto in (
        "Não existe um único sensor. O sensor mede a umidade do solo.",
        "Existe um único sensor que mede a umidade do solo, mas há outro sensor.",
    ):
        resultado = conferir_vinculos({**caso, "contexto": [contexto]}, {
            "vinculos": [_vinculo("o sensor", "umidade do solo", contexto)],
        })
        assert resultado["estado"] == "unicidade_do_medidor_nao_demonstrada"
