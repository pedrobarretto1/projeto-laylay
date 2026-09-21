"""Contratos do experimento, não certificação de acurácia ou execução."""
from copy import deepcopy
import json

import pytest

from mente_laylay.neural.candidato_relacional import (
    CandidatoRelacional, atributos_acao, decodificar_bio, rotulos_bio, validar_entrada,
)
from mente_laylay.neural.avaliacao_escopo import PAPEIS
from mente_laylay.neural.treinar_relacional_isolado import (
    BASE, FONTES, carregar_desenvolvimento, exportar_supervisao, particoes_por_grupo,
)


@pytest.fixture(scope="module")
def dados():
    return carregar_desenvolvimento()


def test_perfil_deriva_somente_desenvolvimento_e_preserva_proibicoes_originais(dados):
    exemplos, sidecars = dados
    assert len(exemplos) == len(sidecars) == 96
    assert all(e["papel_dataset"] == "desenvolvimento" for e in exemplos)
    assert all(c["treino_permitido"] is False for c in sidecars)
    assert all(e["autoriza_execucao"] is e["autoriza_promocao"] is False for e in exemplos)
    assert all(set(e["entrada"]) == {"texto_entrada", "segmentos"} for e in exemplos)


@pytest.mark.parametrize("indice", range(96))
def test_supervisao_bio_preserva_mencoes_literais_e_vinculos(dados, indice):
    e = dados[0][indice]
    for dono in e["segmentos_anotados"]:
        for acao in dono["acoes"]:
            for s in e["entrada"]["segmentos"]:
                resultado = decodificar_bio(s["texto"], s["indice"],
                                           rotulos_bio(s["texto"], s["indice"], acao))
                for papel in PAPEIS:
                    assert resultado[papel] == [m for m in acao[papel] if m["segmento"] == s["indice"]]


@pytest.mark.parametrize("eixo", ["grupo_construcao", "grupo_entidades"])
def test_dobras_nao_compartilham_grupo_nem_irmaos_com_aspas(dados, eixo):
    exemplos = dados[0]
    vistos = []
    for treino, teste in particoes_por_grupo(exemplos, eixo):
        assert len(treino) == len(teste) == 48
        assert not set(treino) & set(teste)
        assert not {exemplos[i][eixo] for i in treino} & {exemplos[i][eixo] for i in teste}
        assert not {exemplos[i]["grupo_contraste"] for i in treino} & {
            exemplos[i]["grupo_contraste"] for i in teste}
        vistos.extend(teste)
    assert sorted(vistos) == list(range(96))


@pytest.mark.parametrize("erro", ["reserva_fonte", "reserva_alinhada", "texto", "duplicata", "permissao"])
def test_exportacao_rejeita_mistura_ou_desvio_sem_mutar_fontes(dados, erro):
    fontes = json.loads((BASE / next(iter(FONTES))).read_text(encoding="utf-8"))["casos"]
    sidecars = deepcopy(dados[1])
    if erro == "reserva_fonte":
        fontes[0]["particao"] = "reserva_entidades"
    elif erro == "reserva_alinhada":
        sidecars[0]["papel_dataset"] = "reserva_independente"
    elif erro == "texto":
        fontes[0]["texto_entrada"] = "outro texto"
    elif erro == "duplicata":
        fontes.append(fontes[0])
    else:
        sidecars[0]["autoriza_execucao"] = True
    antes = deepcopy((fontes, sidecars))
    with pytest.raises(ValueError):
        exportar_supervisao(fontes, sidecars)
    assert (fontes, sidecars) == antes


@pytest.mark.parametrize("campo", ["anotacao", "alvos_solicitados", "variante_esperada", "autoriza_execucao", "id"])
def test_inferencia_rejeita_gabarito_e_autoridade_na_entrada(dados, campo):
    entrada = deepcopy(dados[0][0]["entrada"])
    entrada[campo] = True
    with pytest.raises(ValueError):
        CandidatoRelacional().prever(entrada)


def test_segmentos_nao_podem_vazar_modalidade_ou_veto(dados):
    entrada = deepcopy(dados[0][0]["entrada"])
    entrada["segmentos"][0]["modalidade"] = "pedido"
    with pytest.raises(ValueError):
        validar_entrada(entrada)


def test_texto_novo_nao_precisa_de_nome_cadastrado():
    entrada = {"texto_entrada": "abra Zyré-984", "segmentos": [{"indice": 8, "texto": "abra Zyré-984"}]}
    validar_entrada(entrada)
    assert "entrada:zyré" in atributos_acao(entrada, 0, ("APP_OPEN", "open"))
    # Reconstrução de offsets, NÃO teste de acerto de modelo.
    r = decodificar_bio("abra Zyré-984", 8, ["O", "B:alvos_solicitados",
                                                   "I:alvos_solicitados", "I:alvos_solicitados"])
    assert r["alvos_solicitados"] == [{"segmento": 8, "inicio": 5, "fim": 13, "texto": "Zyré-984"}]


def test_bio_invalido_falha_sem_inventar_inicio_ou_trocar_papel():
    with pytest.raises(ValueError, match="sem início"):
        decodificar_bio("nome", 0, ["I:alvos_solicitados"])
    with pytest.raises(ValueError, match="sem início"):
        decodificar_bio("nome outro", 0, ["B:alvos_excluidos", "I:alvos_solicitados"])


def test_sidecar_protegido_nao_e_entrada_direta_de_treino(dados):
    with pytest.raises(ValueError, match="exportação explícita"):
        CandidatoRelacional().ajustar(dados[1])
    exemplos = deepcopy(dados[0])
    exemplos[0]["papel_dataset"] = "reserva_independente"
    with pytest.raises(ValueError, match="exportação explícita"):
        CandidatoRelacional().ajustar(exemplos)


def test_hash_divergente_aborta_antes_de_exportar(tmp_path):
    fonte = tmp_path / next(iter(FONTES))
    fonte.parent.mkdir(parents=True)
    fonte.write_bytes(b"{}")
    with pytest.raises(ValueError, match="congelada divergiu"):
        carregar_desenvolvimento(tmp_path)
