from copy import deepcopy

import pytest

from mente_laylay.neural.sonda_ambiente_encoder import conferir_resultados, conferir_modelo, executar


def resultados():
    return [{"treinar_encoder": modo, "encoder_inicial_sha256": "encoder", "cabeca_inicial_sha256": "cabeca",
             "logits_iniciais_sha256": "logits", "gradientes_finitos": True, "cabeca_mudou": True,
             "encoder_mudou": modo, "encoder_com_gradiente": modo} for modo in (False, True)]


def test_dois_bracos_pareados_com_efeitos_corretos():
    r = resultados(); antes = deepcopy(r)
    conferir_resultados(r)
    assert r == antes


@pytest.mark.parametrize("chave", ["encoder_inicial_sha256", "cabeca_inicial_sha256", "logits_iniciais_sha256"])
def test_condicoes_iniciais_diferentes_rejeitadas(chave):
    r = resultados(); r[1][chave] = "outro"
    with pytest.raises(ValueError, match="começaram"):
        conferir_resultados(r)


@pytest.mark.parametrize("chave", ["gradientes_finitos", "cabeca_mudou", "encoder_mudou", "encoder_com_gradiente"])
def test_tentativa_sem_efeito_nao_prova_viabilidade(chave):
    r = resultados(); r[1][chave] = False
    with pytest.raises(ValueError): conferir_resultados(r)


def test_braco_congelado_nao_pode_mudar():
    r = resultados(); r[0]["encoder_mudou"] = True
    with pytest.raises(ValueError): conferir_resultados(r)


def test_incompleto_nao_fica_verde():
    with pytest.raises(ValueError): conferir_resultados(resultados()[:1])


def test_zero_nao_substitui_bool_de_protocolo():
    r = resultados(); r[0]["treinar_encoder"] = 0
    with pytest.raises(ValueError): conferir_resultados(r)


def test_pesos_ausentes_nao_acionam_fallback(tmp_path):
    with pytest.raises(FileNotFoundError): conferir_modelo(tmp_path)


def test_saida_existente_aborta_antes_de_importar_torch(tmp_path):
    with pytest.raises(FileExistsError): executar(tmp_path, baixar=True)
