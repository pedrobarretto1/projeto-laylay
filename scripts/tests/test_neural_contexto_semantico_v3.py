from copy import deepcopy

import numpy as np
import pytest
from tokenizers import Tokenizer, models, pre_tokenizers

from mente_laylay.neural.comparar_contexto_semantico_v3 import representar_contexto, conferir_comprimentos
from mente_laylay.neural.diagnosticar_head_relacional import representar


def entrada():
    return {"texto_entrada": "não abra um; abra outro", "segmentos": [
        {"indice": 5, "texto": "não abra um"}, {"indice": 8, "texto": "abra outro"}]}


def vetores(e):
    return {texto: np.full(384, n + 1, dtype=np.float32) for n, texto in enumerate(
        [e["texto_entrada"], *[s["texto"] for s in e["segmentos"]]])}


def test_controle_lexical_permanece_identico_sem_consultar_encoder():
    e = entrada()
    assert representar_contexto(e, 1, ("APP_OPEN", "open"), {}, "lexical") == representar(e, 1, ("APP_OPEN", "open"), "cruzada")


def test_posicao_distingue_segmento_sem_alterar_contexto_global_ou_entrada():
    e = entrada()
    antes = deepcopy(e)
    a, b = [representar_contexto(e, p, ("APP_OPEN", "open"), vetores(e), "semantico") for p in (0, 1)]
    assert a["semantica:global:0"] == b["semantica:global:0"]
    assert a["semantica:local:0"] != b["semantica:local:0"]
    assert e == antes


def test_hibrido_preserva_lexico_e_aplica_interacao_a_variante_proposta():
    e = entrada()
    for variante in (("APP_OPEN", "open"), ("FILE_READ", "read")):
        base = representar(e, 0, variante, "cruzada")
        r = representar_contexto(e, 0, variante, vetores(e), "hibrido")
        assert {k: r[k] for k in base} == base
        assert r[f'semantica:{"/".join(variante)}:global:0'] == r["semantica:global:0"]


@pytest.mark.parametrize("modo", ["lexical", "semantico", "hibrido"])
def test_metadados_de_gabarito_nao_entram_em_nenhuma_representacao(modo):
    e = entrada()
    e["anotacao"] = {"ato": "pedido"}
    with pytest.raises(ValueError):
        representar_contexto(e, 0, ("APP_OPEN", "open"), {}, modo)


@pytest.mark.parametrize("vetor", [np.zeros(384), np.ones(383), np.full(384, np.nan), np.full(384, np.inf)])
def test_vetor_invalido_nao_aciona_fallback_lexical(vetor):
    e = entrada()
    vs = vetores(e)
    vs[e["texto_entrada"]] = vetor
    with pytest.raises(ValueError, match="vetor"):
        representar_contexto(e, 0, ("APP_OPEN", "open"), vs, "hibrido")


def test_vetor_ausente_nao_e_zero_ou_omitido():
    with pytest.raises(KeyError):
        representar_contexto(entrada(), 0, ("APP_OPEN", "open"), {}, "semantico")


def test_preflight_detecta_truncamento_mesmo_se_tokenizer_tinha_limite():
    t = Tokenizer(models.WordLevel({"[UNK]": 0, "a": 1}, unk_token="[UNK]"))
    t.pre_tokenizer = pre_tokenizers.Whitespace()
    t.enable_truncation(8)
    assert conferir_comprimentos([" ".join(["a"] * 128)], t) == [128]
    with pytest.raises(ValueError, match="truncamento"):
        conferir_comprimentos([" ".join(["a"] * 129)], t)
