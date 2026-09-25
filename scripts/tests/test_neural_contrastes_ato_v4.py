from copy import deepcopy

import pytest

from mente_laylay.neural.auditar_contrastes_ato_v4 import comparar_pares, medir_colisoes, reconstruir_previsoes
from mente_laylay.neural.comparar_ocorrencias_v4 import medir, rotular_ocorrencias
from mente_laylay.neural.revalidar_perfil_v4 import carregar_perfil_revalidado


@pytest.fixture(scope="module")
def casos():
    return carregar_perfil_revalidado(reprojetar=True)[0]


def test_reconstrucao_preserva_erro_sem_nova_inferencia(casos):
    cs = casos[:7]
    ps = [rotular_ocorrencias(c) for c in cs]
    i = ps[1].index("APP_OPEN|open|recusa")
    ps[1][i] = "APP_OPEN|open|pedido"
    m = medir(cs, ps)
    assert reconstruir_previsoes(cs, m) == ps


def test_erro_removido_do_relatorio_nao_vira_acerto(casos):
    cs = casos[:1]
    ps = [["ausente"] * len(rotular_ocorrencias(cs[0]))]
    m = medir(cs, ps)
    m["erros"] = []
    with pytest.raises(ValueError, match="incompleto"):
        reconstruir_previsoes(cs, m)


def test_contagem_adulterada_nao_e_aceita(casos):
    cs = casos[:1]
    m = medir(cs, [rotular_ocorrencias(cs[0])])
    m["pedidos_inventados"] = 50
    with pytest.raises(ValueError, match="incompleto"):
        reconstruir_previsoes(cs, m)


def test_pares_cobrem_todas_as_ocorrencias_compostas(casos):
    ps = {c["id"]: rotular_ocorrencias(c) for c in casos}
    gs = {c["id"]: c["grupo_validacao"] for c in casos}
    r = comparar_pares(casos, ps, gs)
    assert len(r["pares"]) == 1344
    assert all(p["previsao_isolada"] == p["previsao_composta"] for p in r["pares"])


def test_par_em_dobras_diferentes_nao_sustenta_comparacao(casos):
    ps = {c["id"]: rotular_ocorrencias(c) for c in casos}
    gs = {c["id"]: c["grupo_validacao"] for c in casos}
    gs[casos[0]["id"]] = "outra_dobra"
    with pytest.raises(ValueError, match="outra dobra"):
        comparar_pares(casos, ps, gs)


def test_janela_identica_com_rotulos_distintos_tem_erro_irredutivel(casos):
    selecionados = [c for c in casos if c["id"] in {
        "rel_v4_vontade_apps_e0_t0_q0_pedido_recusa", "rel_v4_vontade_apps_e0_t0_q0_recusa_pedido"}]
    r = medir_colisoes(selecionados)
    assert r["assinaturas_conflitantes"] > 0
    assert r["erros_minimos_tokens"] > 0
    assert any(set(c["rotulos"]) == {"APP_OPEN|open|recusa", "APP_OPEN|open|pedido"} for c in r["conflitos"])


def test_mesmo_rotulo_repetido_nao_e_colisao(casos):
    c = deepcopy(casos[0]); c["id"] = "copia_apenas_para_teste"
    assert medir_colisoes([casos[0], c])["erros_minimos_tokens"] == 0
