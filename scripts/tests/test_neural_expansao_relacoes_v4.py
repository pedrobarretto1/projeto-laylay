from collections import Counter
from copy import deepcopy

import pytest

from mente_laylay.neural.candidato_relacional import validar_entrada
from mente_laylay.neural.expandir_relacoes_v4 import expandir, preparar_dobras, auditar_grupos
from mente_laylay.neural.revalidar_perfil_v4 import carregar_base_reprojetada


@pytest.fixture(scope="module")
def lote():
    base = carregar_base_reprojetada()
    return base, expandir(base)


def grupos(casos):
    return {c["id"]: c.get("grupo_validacao", c["grupo_construcao"]) for c in casos}


def test_base_conectada_continua_sem_divisao_valida(lote):
    base, _ = lote
    with pytest.raises(ValueError, match="menos de três"):
        preparar_dobras(base, grupos(base))


def test_expansao_aditiva_preserva_fonte_e_nao_consulta_modelo(lote):
    base, novos = lote
    assert base == carregar_base_reprojetada()
    assert len(novos) == 504
    assert len({c["fonte"]["texto_entrada"] for c in base + novos}) == 1176
    for c in novos:
        validar_entrada(c["alinhado"]["entrada"])
        assert c["particao"] == "desenvolvimento"
        assert all(c["alinhado"][k] is False for k in ("treino_permitido", "autoriza_execucao", "autoriza_promocao"))


def test_dobras_candidatas_cobrem_casos_uma_vez_e_mantem_irmaos(lote):
    base, novos = lote
    casos = base + novos
    ds = preparar_dobras(casos, grupos(casos))
    assert len(ds) == 4  # ainda requer auditoria lexical; não equivale a aprovado
    teste = Counter(i for d in ds for i in d["teste"])
    assert teste == Counter({c["id"]: 1 for c in casos})
    for d in ds:
        assert not set(d["treino"]) & set(d["teste"])
        assert len(d["treino"]) + len(d["teste"]) == len(casos)


def test_recusa_nao_desaparece_em_topicalizacao(lote):
    _, novos = lote
    c = next(c for c in novos if c["id"] == "rel_v4_alvo_topicalizado_apps_e0_t0_q0_recusa_pedido")
    nos = c["alinhado"]["supervisao"]["nos"]
    assert [n["ato"] for n in nos] == ["recusa", "pedido"]
    assert nos[0]["alvos_excluidos"][0]["texto"] == "pelvora"
    assert nos[1]["alvos_solicitados"][0]["texto"] == "zafrin"
    assert c["alinhado"]["supervisao"]["relacoes"][0]["origem"] == "n0"


def test_catalogo_e_atos_incompletos_barram_comparacao(lote):
    base, novos = lote
    casos = deepcopy(base + novos)
    for c in casos:
        if c["grupo_construcao"] == "alvo_topicalizado":
            c["alinhado"]["supervisao"]["nos"] = [n for n in c["alinhado"]["supervisao"]["nos"] if n["ato"] != "recusa"]
    with pytest.raises(ValueError, match="cobertura"):
        preparar_dobras(casos, grupos(casos))


def test_nao_separa_irmaos_para_fabricar_dobras(lote):
    base, novos = lote
    casos = base + novos
    gs = grupos(casos)
    gs[casos[0]["id"]] = "grupo_artificial"
    with pytest.raises(ValueError, match="irmãos"):
        preparar_dobras(casos, gs)


def test_auditor_compartilhado_une_parafrases_proximas_sem_treinar():
    casos = [{"id": "a", "fonte": {"texto_entrada": "abra o aplicativo zafrin"}},
             {"id": "b", "fonte": {"texto_entrada": "abre o aplicativo zafrin"}},
             {"id": "c", "fonte": {"texto_entrada": "estou apenas contando uma história"}}]
    gs, pares = auditar_grupos(casos, {"a": "f1", "b": "f2", "c": "f3"})
    assert gs["a"] == gs["b"] != gs["c"]
    assert any(p["id_a"] == "a" and p["id_b"] == "b" for p in pares)
