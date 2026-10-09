"""Primeira fronteira é presença/escopo, nunca só o alvo final."""

import pytest

from scripts.analises import sonda_operacao_antes_alvo_v1 as sonda
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


CASOS, OURO = sonda.carregar_painel()


def caso(id_caso):
    return next(c for c in CASOS if c["id"] == id_caso)


def test_mencao_sem_operacao_nao_chama_selecao_de_alvo(monkeypatch):
    chamadas = []
    def proibida(*a, **k):
        raise AssertionError("modelo nunca registra vigencia")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    def consulta(*a, **k):
        chamadas.append(a)
        assert len(chamadas) == 1
        return {"presenca": "sem_operacao", "trecho": ""}
    r = sonda.medir_estagiada(caso("O01"), consulta=consulta)
    assert r["proposta"] == {"referente_id": "nenhum"}
    assert r["chamadas_modelo"] == 1
    assert sonda.aferir(caso("O01"), r, OURO["O01"])["todas_fronteiras_alinhadas"] is True
    assert all(r[k] is False for k in sonda.nominal.BASE)
    assert "tratado" not in r  # Não consome um turno de produção.


def test_operacao_ancorada_propoe_alvo_sem_descartar_contexto_ou_negar_pergunta():
    chamadas = []
    c = caso("O04")
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, entrada, formato))
        if len(chamadas) == 1:
            assert set(formato["properties"]) == {"presenca", "trecho"}
            return {"presenca": "operacao_mencionada", "trecho": "Pode retirar a regra do cofre"}
        assert entrada["fonte"] == c["fonte"]
        assert entrada["operacao_em_analise"]["semantica_verificada"] is False
        assert entrada["operacao_em_analise"]["citacao"] == "Pode retirar a regra do cofre"
        assert formato["properties"]["referente_id"]["enum"] == ["r47", "r08", "nenhum", "indeterminado"]
        return {"referente_id": "r08"}
    r = sonda.medir_estagiada(c, consulta=consulta)
    assert r["chamadas_modelo"] == 2
    entrada_segunda = dict(chamadas[1][1])
    entrada_segunda.pop("operacao_em_analise")
    assert entrada_segunda == chamadas[0][1]
    assert sonda.aferir(c, r, OURO["O04"])["todas_fronteiras_alinhadas"] is True
    assert r["autoriza_efeito"] is False


@pytest.mark.parametrize("proposta", [
    None, {}, {"presenca": "sem_operacao", "trecho": "regra"},
    {"presenca": "operacao_mencionada", "trecho": ""},
    {"presenca": "inventada", "trecho": ""},
    {"presenca": "operacao_mencionada", "trecho": "cancele a regra de um planeta"},
    {"presenca": "operacao_mencionada", "trecho": "Cancele a regra da oficina", "autoriza": True},
])
def test_primeira_fronteira_invalida_interrompe_chamadas_dependentes(proposta):
    chamadas = []
    def consulta(*a, **k):
        chamadas.append(1)
        return proposta
    r = sonda.medir_estagiada(caso("O02"), consulta=consulta)
    assert len(chamadas) == 1
    assert "erro" in r and "proposta" not in r
    assert r["pode_registrar_vigencia"] is False


def test_trecho_repetido_nao_e_localizado_por_primeira_ocorrencia():
    r = sonda.conferir_presenca("Cancele a regra. Cancele a regra.", {
        "presenca": "operacao_mencionada", "trecho": "Cancele a regra",
    })
    assert r["estado"] == "trecho_sem_ancora_unica"


def test_helper_real_conserva_grafia_e_nao_admite_parafrase():
    r = sonda.conferir_presenca("Retire a regra da oficina.", {
        "presenca": "operacao_mencionada", "trecho": "retire a regra da oficina",
    })
    assert r["trecho_literal"] == "Retire a regra da oficina"
    assert r["inicio"] == 0
    assert r["fim"] == len("Retire a regra da oficina")
    assert sonda.conferir_presenca("Retire a regra da oficina.", {
        "presenca": "operacao_mencionada", "trecho": "Revogue a regra da oficina",
    })["estado"] == "trecho_sem_ancora_unica"


def test_alvo_correto_nao_mascara_presenca_errada():
    c = caso("O13")
    r = sonda.medir_estagiada(c, consulta=lambda *a, **k: {"presenca": "indeterminado", "trecho": ""})
    a = sonda.aferir(c, r, OURO["O13"])
    assert a["alvo_alinhado"] is True
    assert a["presenca_alinhada"] is False
    assert a["todas_fronteiras_alinhadas"] is False


def test_alvo_correto_nao_mascara_escopo_de_outra_regra():
    c = caso("O07")
    respostas = iter([{"presenca": "operacao_mencionada", "trecho": "A regra da oficina não foi revogada"},
                      {"referente_id": "r08"}])
    r = sonda.medir_estagiada(c, consulta=lambda *a, **k: next(respostas))
    a = sonda.aferir(c, r, OURO["O07"])
    assert a["presenca_alinhada"] is True and a["alvo_alinhado"] is True
    assert a["escopo_alinhado"] is False and a["todas_fronteiras_alinhadas"] is False


@pytest.mark.parametrize("id_caso,trecho", [
    ("O04", "retirar a regra do cofre"),
    ("O06", "revogasse a regra da oficina"),
    ("O11", "Troque a regra do museu"),
])
def test_trecho_que_perde_modalidade_ou_complemento_falha_na_revisao(id_caso, trecho):
    c = caso(id_caso)
    respostas = iter([{"presenca": "operacao_mencionada", "trecho": trecho},
                      {"referente_id": OURO[id_caso]["referente_id"]}])
    r = sonda.medir_estagiada(c, consulta=lambda *a, **k: next(respostas))
    a = sonda.aferir(c, r, OURO[id_caso])
    assert a["alvo_alinhado"] is True and a["escopo_alinhado"] is False


def test_nome_literal_nao_prova_operacao():
    c = caso("O01")
    respostas = iter([{"presenca": "operacao_mencionada", "trecho": "A regra da oficina"},
                      {"referente_id": "r47"}])
    r = sonda.medir_estagiada(c, consulta=lambda *a, **k: next(respostas))
    assert r["conferencia_presenca"]["estado"] == "operacao_ancorada_revisao_pendente"
    assert r["relacao_semantica_verificada"] is False
    assert sonda.aferir(c, r, OURO["O01"])["todas_fronteiras_alinhadas"] is False


def test_gabarito_e_id_do_caso_nao_chegam_ao_modelo():
    chamadas = []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append(entrada)
        assert set(entrada) == {"fonte", "inventario", "nomes", "ancoras_literais"}
        assert "O10" not in str(entrada) and "referente_id" not in formato["properties"]
        return {"presenca": "sem_operacao", "trecho": ""}
    r = sonda.medir_estagiada(caso("O10"), consulta=consulta)
    assert len(chamadas) == 1 and r["proposta"] == {"referente_id": "nenhum"}


def test_gate_de_regra_nao_confunde_com_comando_operacional_independente():
    c = caso("O09")
    assert "Abra a calculadora" in c["fonte"]["texto"]
    r = sonda.medir_estagiada(c, consulta=lambda *a, **k: {"presenca": "sem_operacao", "trecho": ""})
    assert r["proposta"] == {"referente_id": "nenhum"}
    assert "tratado" not in r and r["autoriza_efeito"] is False


def test_inventario_expirado_nao_chama_nem_primeiro_estagio():
    c = {**caso("O02"), "agora": 1200.}
    def proibida(*a, **k):
        raise AssertionError("inventario invalido nao chega ao modelo")
    with pytest.raises(ValueError, match="expirado"):
        sonda.medir_estagiada(c, consulta=proibida)


def test_loader_recusa_alteracao_silenciosa_da_revisao(tmp_path, monkeypatch):
    caminho = tmp_path / "revisao.json"
    caminho.write_bytes(sonda.REVISAO.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "REVISAO", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        sonda.carregar_painel()


def test_baseline_nao_recebe_classificacao_de_presenca_ou_gabarito():
    c = caso("O02")
    chamadas = []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, entrada, formato))
        return {"referente_id": "r47"}
    r = sonda.nominal.medir_caso(c, com_ancoras=True, consulta=consulta)
    assert chamadas[0][0] == sonda.nominal.SISTEMA
    assert "operacao_em_analise" not in chamadas[0][1]
    a = sonda.aferir(c, r, OURO["O02"])
    assert a["alvo_alinhado"] is True and a["presenca_aferida"] is False


def test_contraste_de_presenca_muda_apenas_exposicao_do_cadastro():
    chamadas = []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, entrada, formato, kwargs))
        return {"presenca": "sem_operacao", "trecho": ""}
    a = sonda.diagnosticar_presenca(caso("O01"), isolar_fonte=False, consulta=consulta)
    b = sonda.diagnosticar_presenca(caso("O01"), isolar_fonte=True, consulta=consulta)
    full, isolada = chamadas
    assert full[0] == isolada[0] and full[2:] == isolada[2:]
    assert isolada[1] == {"fonte": full[1]["fonte"]}
    assert full[1]["fonte"] == caso("O01")["fonte"]
    assert "proposta" not in a and "proposta" not in b
    assert b["diagnostico_em_painel_conhecido"] is True


def test_cadastro_invalido_bloqueia_ate_diagnostico_sem_exposicao_de_ids():
    c = {**caso("O01"), "agora": 1200.}
    def proibida(*a, **k):
        raise AssertionError("nao ignorar guarda quando isolar entrada")
    with pytest.raises(ValueError, match="expirado"):
        sonda.diagnosticar_presenca(c, isolar_fonte=True, consulta=proibida)
