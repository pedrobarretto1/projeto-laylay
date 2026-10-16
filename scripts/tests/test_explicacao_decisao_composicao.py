"""Fonte do owner deve limitar também o julgamento da revisão instalada."""
import pytest

from scripts.tests.test_motivo_decisao_composicao import decisao_instalada


def test_composicao_vincula_ocorrencia_ao_contrato_de_explicacao(decisao_instalada):
    caso = decisao_instalada["casos"]["gesto_causal"]
    assert caso["experiencia"]["decisao_origem"]["motivo"] == "mudanca_emocional_causal"
    assert "mudanca_emocional_causal" in caso["normal"]
    contrato = caso["plano_consulta"]["contrato_fala"]
    assert contrato.get("explicacao_ocorrencia"), "Fonte no prompt não chega ao contrato que julga a explicação."


def test_revisao_instalada_nao_admite_outra_causa_sem_fonte(decisao_instalada):
    revisoes = decisao_instalada.get("revisoes_controladas")
    if revisoes is None:
        pytest.skip("Coleta exige LAYLAY_COLETAR_REVISAO_CAUSA=1.")
    assert len(revisoes) == 2
    for revisao in revisoes:
        fala = revisao["preparada"]["fala"]
        assert fala != revisao["candidata"], "A revisão admitiu causa sem vínculo à fonte do owner."
        assert "mudanca emocional causal" in fala or "mudanca_emocional_causal" in fala
        assert not revisao["preparada"]["comandos"]
        assert revisao["guarda_final"]["fala"] == fala


@pytest.mark.parametrize("modo", ["normal", "rapido"])
def test_turno_instalado_publica_uma_explicacao_com_fonte_sem_novo_efeito(modo, decisao_instalada):
    if "turnos_revisao" not in decisao_instalada:
        pytest.skip("Coleta exige LAYLAY_COLETAR_REVISAO_CAUSA=1.")
    turno = next(t for t in decisao_instalada["turnos_revisao"] if t["modo"] == modo)
    # A rota normal pode consultar também o classificador canônico da entrada.
    # O que este contrato impede é outra geração de justificativa/reparo.
    autorias = [m for m in turno["modelos"] if any("EXPLICAÇÃO HISTÓRICA VINCULADA AO OWNER" in str(x.get("content"))
                for x in m["mensagens"])]
    assert len(autorias) == 1
    assert not any(m["tipo_chamada"] in {"reparo_factual", "reparo_comunicacao"} for m in turno["modelos"])
    assert len(turno["textos"]) == 1, "O ciclo deve concluir com uma publicação."
    fala = turno["textos"][0]
    assert "mudanca emocional causal" in fala and "PWM e parada elétrica" in fala
    assert "Não há medição de deslocamento" in fala
    assert not turno["executores"] and turno["motores_antes"] == turno["motores_depois"]
    assert not turno["mental"]["plano_turno_atual"]["autoriza_execucao"]


def test_inferencia_real_preserva_mesma_fonte_na_conclusao(decisao_instalada):
    if "qwen_real" not in decisao_instalada:
        pytest.skip("Sonda opcional exige LAYLAY_DECISAO_QWEN_REAL=1.")
    for geracao in decisao_instalada["qwen_real"]["geracoes"]:
        assert geracao["modelos"] and geracao["modelos"][0]["resultado"]["sucesso"]
        assert any(h.get("status") == 200 for h in geracao["http"])
        assert not geracao["porta_executor"]
        assert len(geracao["finais_isolados"]) == 1
        final = geracao["finais_isolados"][0]
        assert "mudanca emocional causal" in final["fala"]
        assert "PWM e parada elétrica" in final["fala"]
        assert "Não há medição de deslocamento" in final["fala"]
        assert not final["comandos"]


def test_composicao_separa_falha_ambiguidade_e_referencia_ausente(decisao_instalada):
    if "consultas_limites" not in decisao_instalada:
        pytest.skip("Coleta exige LAYLAY_COLETAR_REVISAO_CAUSA=1.")
    falha, ambigua, ausente = decisao_instalada["consultas_limites"]
    fala = falha["preparada"]["fala"]
    assert "mudanca emocional causal" in fala and "sem confirmação" in fala
    assert "confirmação registrada" not in fala
    assert "qual delas" in ambigua["preparada"]["fala"]
    assert "não prova que a ação não aconteceu" in ausente["preparada"]["fala"]
    assert all(not c["preparada"]["comandos"] for c in (falha, ambigua, ausente))
