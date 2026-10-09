"""Nome registrado é pista literal, nunca decisão de alvo ou vigência."""

from dataclasses import replace

import pytest

from mente_laylay.cognicao.contrato_inventario_contextual import (
    InventarioContextual, ReferenteContextual, avaliar_referencia_nominal_contextual,
)
from scripts.analises import sonda_alvo_inventariado_v1 as sonda
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


ORIGEM = "cadastro_offline_do_painel"
ORIGENS = frozenset({ORIGEM})
I = InventarioContextual(ORIGEM, "infra_a", 1000., 60., "completa", "enumeracao_da_fonte", (
    ReferenteContextual("r17", "regra", "servidor", ORIGEM, "infra_a"),
    ReferenteContextual("r42", "regra", "cache", ORIGEM, "infra_a"),
))
NOMES = {"r17": ("a regra do servidor",), "r42": ("a regra do cache",)}


def ancorar(texto, inventario=I, nomes=NOMES, origens=ORIGENS, agora=1001.):
    return sonda.ancorar_nomes(texto, inventario, nomes, agora=agora, origens_enumeradoras=origens)


def test_ambiguo_canonico_nao_deve_ser_relaxado_para_fazer_piloto_passar():
    real = avaliar_referencia_nominal_contextual(
        "Cancele a regra do servidor", I, tipo="regra", grandeza_requerida="servidor",
        agora=1001., origens_enumeradoras=ORIGENS,
    )
    assert real["estado"] == "referentes_concorrentes"
    assert real["referente_resolvido"] is False
    pistas = ancorar("Cancele a regra do servidor")
    assert pistas["ancoras"][0]["referente_id"] == "r17"
    assert pistas["referente_resolvido"] is False


def test_todas_as_mencoes_incluindo_negacao_e_citacao_sao_preservadas():
    texto = "Retire a regra do cache; a regra do servidor não mudou. Citei 'a regra do cache'."
    r = ancorar(texto)
    assert r["estado"] == "nomes_ancorados_revisao_pendente"
    assert [a["referente_id"] for a in r["ancoras"]] == ["r42", "r17", "r42"]
    for a in r["ancoras"]:
        assert texto[a["inicio"]:a["fim"]] == a["citacao"]
        assert a["origem"] == ORIGEM and a["escopo"] == "infra_a"
    assert all(r[k] is False for k in sonda.BASE)


def test_pronome_nome_ausente_e_substring_nao_ganham_identidade():
    for texto in ("Cancele essa regra", "Retire a regra do roteador", "a regra do servidorzinho"):
        r = ancorar(texto)
        assert r["ancoras"] == []
        assert sonda.conferir_alvo({"referente_id": "r17"}, r)["estado"] == "id_sem_ancora_literal"


@pytest.mark.parametrize("inventario,origens,estado", [
    (replace(I, capturado_em=900.), ORIGENS, "inventario_expirado"),
    (replace(I, cobertura="parcial"), ORIGENS, "cobertura_nao_demonstrada"),
    (replace(I, metodo_cobertura="selecao_de_trechos"), ORIGENS, "cobertura_nao_demonstrada"),
    (I, frozenset(), "fonte_nao_registrada"),
    (replace(I, referentes=(I.referentes[0], I.referentes[0])), ORIGENS, "identificadores_duplicados"),
    (replace(I, escopo="outro"), ORIGENS, "proveniencia_invalida"),
    (replace(I, referentes=(replace(I.referentes[0], origem="llm"),)), ORIGENS, "proveniencia_invalida"),
])
def test_guardas_reais_do_inventario_vetam_ancoragem(inventario, origens, estado):
    r = ancorar("Retire a regra do servidor", inventario=inventario, origens=origens)
    assert r["estado"] == estado
    assert r["ancoras"] == []


def test_duplicatas_de_nome_e_ancoras_sobrepostas_nao_escolhem_por_ordem():
    duplicados = {"r17": ("a regra do cache",), "r42": ("a regra do cache",)}
    assert ancorar("a regra do cache", nomes=duplicados)["estado"] == "nome_duplicado"
    sobrepostos = {"r17": ("a regra do servidor",), "r42": ("a regra do servidor auxiliar",)}
    assert ancorar("a regra do servidor auxiliar", nomes=sobrepostos)["estado"] == "ancoras_sobrepostas"
    assert ancorar("a regra do servidor", nomes={"r17": NOMES["r17"]})[
        "estado"] == "nomes_sem_proveniencia"


def test_mesmo_contrato_literal_funciona_sem_parser_privado_de_regra():
    inventario = replace(I, referentes=(
        replace(I.referentes[0], tipo="sensor", grandeza="solo"),
        replace(I.referentes[1], tipo="sensor", grandeza="ar"),
    ))
    r = ancorar("O sensor do ar leu 15%", inventario, {"r17": ("o sensor do solo",), "r42": ("o sensor do ar",)})
    assert r["ancoras"][0]["referente_id"] == "r42"
    assert r["referente_resolvido"] is False


@pytest.mark.parametrize("proposta", [None, {}, {"referente_id": "r17", "autoriza": True}, {"referente_id": []}])
def test_proposta_malformada_e_recusada(proposta):
    assert sonda.conferir_alvo(proposta, ancorar("a regra do servidor"))["estado"] == "proposta_invalida"


def test_id_valido_mas_alvo_errado_nao_e_certificado_semanticamente():
    a = ancorar("A regra do cache foi retirada; a regra do servidor não mudou.")
    r = sonda.conferir_alvo({"referente_id": "r17"}, a)
    assert r["estado"] == "alvo_ancorado_revisao_pendente"
    assert all(r[k] is False for k in sonda.BASE)


def test_contraste_muda_somente_ancoras_nunca_schema_gabarito_ou_fontes(monkeypatch):
    casos, ouro = sonda.carregar_painel()
    chamadas = []
    def proibida(*a, **k):
        raise AssertionError("modelo nao escreve vigencia")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, entrada, formato, kwargs))
        assert "B02" not in str(entrada) and "revisao" not in entrada
        return {"referente_id": "r42"}
    r0 = sonda.medir_caso(casos[1], com_ancoras=False, consulta=consulta)
    r1 = sonda.medir_caso(casos[1], com_ancoras=True, consulta=consulta)
    a, b = chamadas
    entrada_b = dict(b[1])
    ancoras = entrada_b.pop("ancoras_literais")
    assert a[0] == b[0] and a[2:] == b[2:] and a[1] == entrada_b
    assert {m["referente_id"] for m in ancoras} == {"r17", "r42"}
    assert all(m["fonte_id"] == "u1" for m in ancoras)
    assert r0["proposta"] == r1["proposta"] == {"referente_id": ouro["B02"]}
    assert r1["conferencia"]["pode_registrar_vigencia"] is False


def test_fonte_invalida_nao_chama_modelo():
    casos, _ = sonda.carregar_painel()
    caso = {**casos[0], "agora": 1100.}
    def proibida(*a, **k):
        raise AssertionError("modelo nao deveria receber inventario expirado")
    with pytest.raises(ValueError, match="expirado"):
        sonda.medir_caso(caso, com_ancoras=True, consulta=proibida)


def test_congelamento_do_painel_recusa_alteracao(tmp_path, monkeypatch):
    caminho = tmp_path / "painel.json"
    caminho.write_bytes(sonda.ENTRADAS.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "ENTRADAS", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        sonda.carregar_painel()
