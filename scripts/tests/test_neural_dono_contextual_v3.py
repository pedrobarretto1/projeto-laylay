from copy import deepcopy

import numpy as np
import pytest

from mente_laylay.neural.comparar_dono_contextual_v3 import contexto_marcado, representar_dono
from mente_laylay.neural.comparar_contexto_semantico_v3 import representar_contexto


def entrada():
    return {"texto_entrada": "não abra um; abra outro", "segmentos": [
        {"indice": 2, "texto": "não abra um"}, {"indice": 9, "texto": "abra outro"}]}


def test_local_nao_le_nem_precisa_de_vetor_global():
    e = entrada()
    vs = {e["segmentos"][0]["texto"]: np.ones(384)}
    r = representar_dono(e, 0, ("APP_OPEN", "open"), vs, "local")
    assert not any(":global:" in k for k in r)
    assert r["semantica:local:0"] == 1


def test_controle_global_local_e_identico_ao_anterior():
    e = entrada()
    vs = {e["texto_entrada"]: np.ones(384), e["segmentos"][0]["texto"]: np.full(384, 2)}
    assert representar_dono(e, 0, ("APP_OPEN", "open"), vs, "global_local") == representar_contexto(
        e, 0, ("APP_OPEN", "open"), vs, "semantico")


def test_marcacao_preserva_textos_ordem_e_nao_recebe_gabarito():
    e = entrada()
    antes = deepcopy(e)
    a, b = [contexto_marcado(e, i) for i in (0, 1)]
    assert a != b
    assert "1 [trecho em análise]: não abra um" in a
    assert "2 [trecho em análise]: abra outro" in b
    assert a.index("1 [trecho") < a.index("2:")
    assert e["texto_entrada"] in a and e == antes
    vs = {b: np.ones(384), e["segmentos"][1]["texto"]: np.full(384, 2)}
    r = representar_dono(e, 1, ("APP_OPEN", "open"), vs, "marcado")
    assert r["semantica:global:0"] == 1 and r["semantica:local:0"] == 2


@pytest.mark.parametrize("posicao", [-1, True, 2])
def test_marcacao_rejeita_posicao_invalida(posicao):
    with pytest.raises(ValueError):
        contexto_marcado(entrada(), posicao)


@pytest.mark.parametrize("modo", ["local", "global_local", "marcado"])
def test_gabarito_ou_autoridade_no_input_aborta(modo):
    e = entrada()
    e["autoriza_execucao"] = True
    with pytest.raises(ValueError):
        representar_dono(e, 0, ("APP_OPEN", "open"), {}, modo)
