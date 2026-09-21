from collections import Counter
from copy import deepcopy

import pytest

from mente_laylay.neural.preparar_relacoes_v4 import gerar_contrastes, agrupar_projecoes
from mente_laylay.neural.preparar_lote_relacional_v3 import VARIANTES
from mente_laylay.neural.supervisao_relacoes_v4 import alinhar_relacoes, validar_fonte_relacional
from mente_laylay.neural.candidato_relacional import validar_entrada


@pytest.fixture(scope="module")
def casos():
    return gerar_contrastes()


def fonte(casos, sufixo="pedido_recusa", dominio="apps"):
    return deepcopy(next(c["fonte"] for c in casos
                         if c["id"] == f"rel_v4_direto_{dominio}_e0_t0_q0_{sufixo}"))


def test_mesmo_segmento_e_mesma_variante_preservam_pedido_e_recusa(casos):
    f = fonte(casos)
    r = alinhar_relacoes(f, variantes_permitidas=VARIANTES)
    assert len(r["entrada"]["segmentos"]) == 1  # linguagem real, não resegmentação artificial
    a, b = r["supervisao"]["nos"]
    assert a["ancora"]["segmento"] == b["ancora"]["segmento"] == 0
    assert a["ato"] == "pedido" and b["ato"] == "recusa"
    assert a["alvos_solicitados"][0]["texto"] == "zafrin"
    assert b["alvos_excluidos"][0]["texto"] == "pelvora"
    assert r["supervisao"]["relacoes"] == [{"tipo": "restringe", "origem": "n1", "destino": "n0"}]


def test_ordem_inversa_nao_apaga_recusa_em_segmento_separado(casos):
    r = alinhar_relacoes(fonte(casos, "recusa_pedido"), variantes_permitidas=VARIANTES)
    assert len(r["entrada"]["segmentos"]) == 2
    assert [n["ato"] for n in r["supervisao"]["nos"]] == ["recusa", "pedido"]
    assert [n["ancora"]["segmento"] for n in r["supervisao"]["nos"]] == [0, 1]


def test_relato_nao_vira_restricao_ou_pedido(casos):
    r = alinhar_relacoes(fonte(casos, "relato_pedido"), variantes_permitidas=VARIANTES)
    assert r["supervisao"]["relacoes"] == []
    relato = r["supervisao"]["nos"][0]
    assert relato["ato"] == "relato" and relato["alvos_mencionados"]
    assert not relato["alvos_excluidos"] and not relato["alvos_solicitados"]


@pytest.mark.parametrize("dominio", ["apps", "musica", "arquivos"])
def test_alvos_opacos_ancoras_e_input_sem_gold_na_composicao_real(casos, dominio):
    f = fonte(casos, dominio=dominio)
    antes = deepcopy(f)
    r = alinhar_relacoes(f, variantes_permitidas=VARIANTES)
    validar_entrada(r["entrada"])
    assert f == antes and r["entrada"]["texto_entrada"] == f["texto_entrada"]
    textos = {s["indice"]: s["texto"] for s in r["entrada"]["segmentos"]}
    for n in r["supervisao"]["nos"]:
        for span in [n["ancora"], *n["alvos_solicitados"], *n["alvos_excluidos"], *n["alvos_mencionados"]]:
            assert textos[span["segmento"]][span["inicio"]:span["fim"]] == span["texto"]
    assert r["treino_permitido"] is r["autoriza_execucao"] is r["autoriza_promocao"] is False


@pytest.mark.parametrize("campo", ["autoriza_execucao", "autoriza_promocao", "treino_permitido"])
def test_supervisao_nao_concede_autoridade(casos, campo):
    f = fonte(casos)
    f[campo] = True
    with pytest.raises(ValueError, match="isolada"):
        alinhar_relacoes(f, variantes_permitidas=VARIANTES)


@pytest.mark.parametrize("erro", ["id", "ancora", "alvo", "catalogo", "extra", "relato", "link", "duplicado"])
def test_falha_de_uma_ocorrencia_ou_relacao_rejeita_todo_o_composto(casos, erro):
    f = fonte(casos)
    if erro == "id": f["nos"][1]["id"] = "n0"
    elif erro == "ancora": f["nos"][0]["ancora"]["inicio"] = True
    elif erro == "alvo": f["nos"][0]["alvos"][0]["texto"] = "outro"
    elif erro == "catalogo": f["nos"][0]["intent"] = "APAGAR_TUDO"
    elif erro == "extra": f["nos"][0]["autoriza_execucao"] = True
    elif erro == "relato": f["nos"][1]["ato"] = "relato"
    elif erro == "link": f["relacoes"][0]["destino"] = "inexistente"
    elif erro == "duplicado": f["relacoes"] *= 2
    with pytest.raises(ValueError):
        alinhar_relacoes(f, variantes_permitidas=VARIANTES)


def test_grade_troca_nomes_papeis_e_ordem_sem_duplicar_textos(casos):
    assert len(casos) == 672
    assert len({c["fonte"]["texto_entrada"] for c in casos}) == len(casos)
    contagem = Counter()
    for c in casos:
        validar_fonte_relacional(c["fonte"], variantes_permitidas=VARIANTES)
        for n in c["fonte"]["nos"]:
            contagem[n["alvos"][0]["texto"], n["ato"]] += 1
    for a, b in (("zafrin", "pelvora"), ("mezdar", "tuvlen")):
        for ato in ("pedido", "recusa", "relato"):
            assert contagem[a, ato] == contagem[b, ato] > 0


def test_projecoes_iguais_unem_grupos_sem_usar_rotulos():
    def c(i, texto):
        return {"id": i, "alinhado": {"entrada": {"segmentos": [{"indice": 0, "texto": texto}]}}}
    grupos, repeticoes = agrupar_projecoes([c("a", "abra um"), c("b", "abra um"), c("c", "leia outro")],
                                         {"a": "f1", "b": "f2", "c": "f3"})
    assert grupos["a"] == grupos["b"] != grupos["c"]
    assert repeticoes == 1
