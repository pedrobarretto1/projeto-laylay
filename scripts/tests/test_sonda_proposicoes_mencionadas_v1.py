"""Gabarito posterior à proposta; cada fronteira medida sem compensação."""

from copy import deepcopy

import pytest

from scripts.analises import sonda_proposicoes_mencionadas_v1 as sonda


CASOS, OURO = sonda.carregar_painel()


def caso(id_caso):
    return next(c for c in CASOS if c["id"] == id_caso)


def proposta_local(id_caso):
    # Fixture de contrato, não resposta de modelo nem evidência de extração.
    c, ouro = caso(id_caso), OURO[id_caso]
    molduras = [{"id": f"m{i}", "fonte_id": "f1", "tipo": m["tipo"], "trecho": m["escopo"],
                 "pai_id": f"m{i+1}" if i+1 < len(ouro["molduras"]) else ""}
                for i, m in enumerate(ouro["molduras"])]
    return {"molduras": molduras, "proposicoes": [{"id": "p1", "fonte_id": "f1", "tipo": "acao",
            "trecho": molduras[0]["trecho"], "predicado": ouro["predicado"], "objeto": ouro["objeto"],
            "papel_objeto": ouro["papel_objeto"], "polaridade": ouro["polaridade"], "moldura_id": "m0"}]}


def medir_local(id_caso, proposta):
    return sonda.medir_caso(caso(id_caso), consulta=lambda *a, **k: proposta)


@pytest.mark.parametrize("id_caso", [c["id"] for c in CASOS])
def test_revisao_local_e_representavel_sem_certificar_semantica(id_caso):
    r = medir_local(id_caso, proposta_local(id_caso))
    a = sonda.aferir(caso(id_caso), r, OURO[id_caso])
    assert a["todas_fronteiras_alinhadas"] is True
    assert all(a[k] is False and r[k] is False for k in sonda.contrato.BASE)


def test_gabarito_id_de_caso_e_domino_nao_entram_no_prompt_ou_schema():
    def consulta(sistema, entrada, formato, **kwargs):
        assert set(entrada) == {"fonte", "aspas_sintaticas"}
        assert entrada["fonte"]["texto"] == caso("F02")["texto"]
        assert "F02" not in str(entrada) and "molduras" not in entrada
        assert formato == sonda.formato_proposta()
        assert kwargs["modelo"] == "qwen3:4b-instruct"
        return {"proposicoes": [], "molduras": []}
    r = sonda.medir_caso(caso("F02"), consulta=consulta)
    a = sonda.aferir(caso("F02"), r, OURO["F02"])
    assert a["estrutura_ancorada"] is True
    assert a["quantidade_alinhada"] is False and a["todas_fronteiras_alinhadas"] is False


@pytest.mark.parametrize("id_caso", ["F02", "F03", "I02", "I03"])
def test_objeto_correto_nao_mascara_moldura_externa_perdida(id_caso):
    proposta = proposta_local(id_caso)
    proposta["molduras"] = proposta["molduras"][:1]
    proposta["molduras"][0]["pai_id"] = ""
    r = medir_local(id_caso, proposta)
    a = sonda.aferir(caso(id_caso), r, OURO[id_caso])
    assert a["predicado_alinhado"] is True and a["objeto_alinhado"] is True
    assert a["cadeia_molduras_alinhada"] is False and a["todas_fronteiras_alinhadas"] is False


@pytest.mark.parametrize("id_caso,objeto_subordinado", [("F04", "o arquivo croqui.md"), ("I04", "a tomada da bancada")])
def test_nome_subordinado_ancorado_nao_e_o_objeto_correspondente(id_caso, objeto_subordinado):
    proposta = proposta_local(id_caso)
    proposta["proposicoes"][0]["objeto"] = objeto_subordinado
    r = medir_local(id_caso, proposta)
    a = sonda.aferir(caso(id_caso), r, OURO[id_caso])
    assert a["estrutura_ancorada"] is True and a["predicado_alinhado"] is True
    assert a["objeto_alinhado"] is False and a["todas_fronteiras_alinhadas"] is False


def test_rotulo_de_pergunta_correto_nao_mascara_envelope_incompleto():
    proposta = proposta_local("F03")
    proposta["molduras"][1]["trecho"] = "Se eu removesse o arquivo croqui.md"
    r = medir_local("F03", proposta)
    a = sonda.aferir(caso("F03"), r, OURO["F03"])
    assert a["estrutura_ancorada"] is True
    assert a["objeto_alinhado"] is True and a["cadeia_molduras_alinhada"] is False


def test_polaridade_errada_nao_e_compensada_pelo_objeto():
    proposta = proposta_local("I01")
    proposta["proposicoes"][0]["polaridade"] = "negativa"
    r = medir_local("I01", proposta)
    a = sonda.aferir(caso("I01"), r, OURO["I01"])
    assert a["objeto_alinhado"] is True and a["polaridade_alinhada"] is False
    assert a["todas_fronteiras_alinhadas"] is False


def test_duplicar_proposicao_nao_melhora_cobertura_do_piloto():
    proposta = proposta_local("F01")
    proposta["proposicoes"].append({**deepcopy(proposta["proposicoes"][0]), "id": "p2"})
    r = medir_local("F01", proposta)
    a = sonda.aferir(caso("F01"), r, OURO["F01"])
    assert a["estrutura_ancorada"] is True and a["quantidade_alinhada"] is False
    assert a["todas_fronteiras_alinhadas"] is False


def test_loader_nao_aceita_edicao_silenciosa_do_gabarito(tmp_path, monkeypatch):
    caminho = tmp_path / "revisao.json"
    caminho.write_bytes(sonda.REVISAO.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "REVISAO", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        sonda.carregar_painel()


def test_erro_de_estrutura_nao_vira_acerto_semantico():
    r = medir_local("F01", {"molduras": [], "proposicoes": [], "autoriza_efeito": True})
    a = sonda.aferir(caso("F01"), r, OURO["F01"])
    assert a["estrutura_ancorada"] is False and a["todas_fronteiras_alinhadas"] is False
    assert all(a[k] is False for k in sonda.contrato.BASE)
