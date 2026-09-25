from copy import deepcopy
import json
from types import SimpleNamespace

import numpy as np
import pytest

from mente_laylay.neural.comparar_ocorrencias_v4 import (
    alinhar_subtokens, medir, representar_tokens, rotular_ocorrencias, estado_ajuste,
)
from mente_laylay.neural.revalidar_perfil_v4 import carregar_perfil_revalidado


@pytest.fixture(scope="module")
def casos():
    # Contratos dos algoritmos atuais, não reprodução do classificador antigo.
    return carregar_perfil_revalidado(reprojetar=True)[0]


def test_loss_float32_do_treino_pode_ser_publicada_em_json():
    r = estado_ajuste(SimpleNamespace(n_iter_=np.int64(10), loss_=np.float32(.125)))
    assert json.loads(json.dumps(r, allow_nan=False)) == {"iteracoes": 10, "loss": .125}


def test_subtoken_compartilhado_nao_descarta_pontuacao():
    h = np.ones((1, 384), dtype=np.float32)
    r = alinhar_subtokens('\";', [(0, 2)], [1], [0], h)
    assert r.shape == (2, 384)
    assert np.allclose(r[0], r[1])


def test_offset_sem_cobertura_nao_vira_fallback():
    with pytest.raises(ValueError, match="cobre"):
        alinhar_subtokens("abra", [(0, 2)], [1], [0], np.ones((1, 384)))


@pytest.mark.parametrize("valor", [0.0, float("nan"), float("inf")])
def test_vetor_invalido_aborta(valor):
    with pytest.raises(ValueError):
        alinhar_subtokens("abra", [(0, 4)], [1], [0], np.full((1, 384), valor))


def test_especiais_e_padding_nao_entram_na_media():
    h = np.zeros((3, 384)); h[0, 0] = 1; h[1, 1] = 1; h[2, 2] = 1
    r = alinhar_subtokens("abra", [(0, 4)] * 3, [1, 1, 0], [1, 0, 0], h)
    assert r[0, 1] == 1 and np.count_nonzero(r) == 1


def test_todos_tokens_sao_candidatos_sem_ancora_gold(casos):
    c = next(c for c in casos if c["id"] == "rel_v4_direto_apps_e0_t0_q0_pedido_recusa")
    ts, xs = representar_tokens(c["alinhado"]["entrada"])
    ys = rotular_ocorrencias(c)
    assert len(ts) == len(xs) == len(ys)
    assert sum(y != "ausente" for y in ys) == 2
    assert [ys[i] for i, t in enumerate(ts) if t[0] == "abra"] == ["APP_OPEN|open|pedido", "APP_OPEN|open|recusa"]
    assert not any("ato" == k or "ancora" in k for x in xs for k in x)
    e = deepcopy(c["alinhado"]["entrada"]); e["supervisao"] = c["alinhado"]["supervisao"]
    with pytest.raises(ValueError):
        representar_tokens(e)


def test_metrica_perfeita_e_controle_tudo_ausente(casos):
    cs = casos[:7]
    ys = [rotular_ocorrencias(c) for c in cs]
    r = medir(cs, ys)
    assert r["casos_exatos_acao_sem_alvos"] == len(cs)
    assert r["acoes_esperadas"] == 11
    r = medir(cs, [["ausente"] * len(y) for y in ys])
    assert r["casos_exatos_acao_sem_alvos"] == 0 and r["acoes_ausentes"] == 11


def test_recusa_transformada_em_pedido_nao_some_do_denominador(casos):
    c = next(c for c in casos if c["id"] == "rel_v4_direto_apps_e0_t0_q0_pedido_recusa")
    ys = rotular_ocorrencias(c)
    ys[ys.index("APP_OPEN|open|recusa")] = "APP_OPEN|open|pedido"
    r = medir([c], [ys])
    assert r["casos_exatos_acao_sem_alvos"] == 0 and r["pedidos_inventados"] == 1
    assert r["acoes_extras"] == 0  # erro de ato, não nova âncora


def test_mencao_de_alvo_nao_pode_ser_ancora_inventada(casos):
    c = casos[0]
    ys = rotular_ocorrencias(c)
    ts, _ = representar_tokens(c["alinhado"]["entrada"])
    ys[next(i for i, t in enumerate(ts) if t[0] == "zafrin")] = "APP_OPEN|open|pedido"
    r = medir([c], [ys])
    assert r["acoes_extras"] == r["pedidos_inventados"] == 1


def test_predicao_parcial_aborta(casos):
    with pytest.raises(ValueError, match="incompleta"):
        medir(casos[:1], [[]])


def test_ancora_multi_token_nao_e_reduzida_silenciosamente(casos):
    c = deepcopy(casos[0]); a = c["alinhado"]["supervisao"]["nos"][0]["ancora"]
    a["fim"] += 2; a["texto"] += " o"
    with pytest.raises(ValueError, match="incompatível"):
        rotular_ocorrencias(c)
