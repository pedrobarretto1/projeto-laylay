"""Cada campo avaliado em sua fronteira; sucesso composto não mascara erro."""

import pytest

from scripts.analises import sonda_relacoes_dimensoes_v1 as sonda
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


CASOS, RELACOES, REVISAO = sonda.carregar_revisao()


def test_propostas_independentes_recebem_as_mesmas_fontes_sem_gabarito(monkeypatch):
    caso = next(c for c in CASOS if c["id"] == "N10")
    chamadas = []
    def proibida(*a, **k):
        raise AssertionError("sonda nao pode registrar vigencia")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    def consultar(sistema, entrada, formato, **kwargs):
        campo = formato["required"][0]
        assert set(entrada) == {"alvo_id", "fontes_em_ordem", "fonte_em_analise"}
        assert len(entrada["fontes_em_ordem"]) == 3
        assert len(formato["properties"]) == 1
        indice = int(entrada["fonte_em_analise"]["id"][1:]) - 1
        chamadas.append((campo, entrada))
        return {campo: REVISAO["N10"][indice][campo][0]}
    resultado = sonda.propor_campos(caso, consulta=consultar)
    assert len(chamadas) == 6
    assert [c[0] for c in chamadas] == ["ato", "alvo", "operacao"] * 2
    assert chamadas[0][1] == chamadas[1][1] == chamadas[2][1]
    assert sonda.aferir_campos(caso, resultado, REVISAO["N10"])["todos_campos_alinhados"] is True
    assert resultado["conferencia"]["pode_registrar_vigencia"] is False


def test_relacao_correta_por_ato_errado_continua_com_campo_vermelho():
    caso = next(c for c in CASOS if c["id"] == "N11")
    # Relato foi chamado de pergunta, mas a primeira relação sai sem alteração.
    respostas = iter([{"ato": "pergunta"}, {"alvo": "nenhum"}, {"operacao": "nenhuma"},
                      {"ato": "relato"}, {"alvo": "indeterminado"}, {"operacao": "revoga"}])
    resultado = sonda.propor_campos(caso, consulta=lambda *a, **k: next(respostas))
    assert [r["relacao"] for r in resultado["proposta"]["relacoes"]] == RELACOES["N11"]
    afericao = sonda.aferir_campos(caso, resultado, REVISAO["N11"])
    assert afericao["campos"]["ato"] == [False, True]
    assert afericao["todos_campos_alinhados"] is False


@pytest.mark.parametrize("resposta", [None, {}, {"ato": "relato", "autoriza": True}, {"ato": "invalido"}])
def test_resposta_invalida_nao_avanca_para_campos_dependentes(resposta):
    chamadas = []
    def consultar(*a, **k):
        chamadas.append(1)
        return resposta
    r = sonda.propor_campos(CASOS[0], consulta=consultar)
    assert r["erro"] == "campo_invalido"
    assert len(chamadas) == 1
    assert r["aprovado_para_producao"] is False


def test_observacao_canonica_usa_componente_real_e_nao_exporta_autorizacao():
    caso = CASOS[1]
    real = classificar_modalidade_turno(caso["posteriores"][0])
    observado = sonda.observar_canonico(caso)[0]
    assert observado["modalidade"] == real["modalidade_geral"]
    assert observado["atos"] == real["atos"]
    assert observado["alvo_de_regra_comparavel"] is False
    assert "autoriza_execucao" not in observado


def test_painel_antigo_e_revisao_por_campo_permanecem_separados():
    assert len(CASOS) == 12
    assert sum(len(c["posteriores"]) for c in CASOS) == 14
    assert RELACOES["N01"] == ["sem_alteracao"]
    assert REVISAO["N01"][0]["operacao"] == ["revoga"]


def test_loader_recusa_mudanca_na_revisao_por_campo(tmp_path, monkeypatch):
    caminho = tmp_path / "revisao.json"
    caminho.write_bytes(sonda.REVISAO.read_bytes() + b" ")
    monkeypatch.setattr(sonda, "REVISAO", caminho)
    with pytest.raises(ValueError, match="congelamento"):
        sonda.carregar_revisao()


def test_contraste_alvo_muda_somente_exposicao_do_mesmo_objeto():
    caso = CASOS[0]
    chamadas = []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, entrada, formato, kwargs))
        return {"alvo": "regra_alvo"}
    sonda.propor_alvos(caso, explicitar_alvo=False, consulta=consulta)
    r = sonda.propor_alvos(caso, explicitar_alvo=True, consulta=consulta)
    a, b = chamadas
    assert a[0] == b[0] and a[2:] == b[2:]
    entrada_b = dict(b[1])
    alvo = entrada_b.pop("regra_comparada")
    assert a[1] == entrada_b
    assert alvo == a[1]["fontes_em_ordem"][0]
    assert r["pode_registrar_vigencia"] is False
