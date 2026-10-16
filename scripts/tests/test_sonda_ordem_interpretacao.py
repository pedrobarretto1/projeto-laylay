from scripts.analises.sonda_ordem_interpretacao import avaliar_campos, painel, projetar_contexto_diagnostico


def test_avaliacao_separa_operacao_alvo_e_cobertura_sem_inventar_prova():
    gold = [{"intent":"VOLUME","params":{"acao":"set","nivel_volume":40}}]
    assert avaliar_campos(gold, gold)["aderencia_campos"] is True
    erro = avaliar_campos(gold,[{"intent":"VOLUME","params":{"acao":"set","nivel_volume":90}}])
    assert erro["ausentes"] and erro["indevidos"]
    assert erro["prova_autorizacao"] is erro["prova_efeito"] is False


def test_painel_nao_confunde_remocao_de_faixa_com_exclusao_da_colecao():
    casos = painel()
    assert len({c["id"] for c in casos}) == len(casos) == 14
    assert sum(c["remocao_nao_conectada"] for c in casos) == 3
    for caso in casos:
        if caso["remocao_nao_conectada"]:
            assert caso["esperados"] == []  # Não habilitar operação ainda ausente.
            erro = avaliar_campos([], [{"intent":"PLAYLIST_DELETE","params":{"nome_playlist":"novidades"}}])
            assert erro["indevidos"]


def test_resolucao_singular_nao_prova_cobertura_de_comando_composto():
    composto = next(c for c in painel() if c["id"] == "composto")
    erro = avaliar_campos(composto["esperados"],composto["esperados"][:1])
    assert not erro["indevidos"] and len(erro["ausentes"]) == 1
    assert erro["aderencia_campos"] is False


def test_ablacao_preserva_receipt_identidade_referencia_sem_mutar_fonte():
    from copy import deepcopy
    ctx = {"estado":{"mente_integrada_estado":{
        "turno_atual":{"id":123,"texto":"fecha ela","autoriza_execucao":True,"especialistas":{"duplicata":"x"*10000}},
        "plano_turno_atual":{"duplicata":"x"*10000},"ultima_acao_contrato":{"id_solicitacao":"abc","confirmado":True},
        "retrato_turno_atual":{"referencia_resolvida":{"nome":"Calculadora","tipo":"app"}},
        "continuidade_geral":{"ativa":True},"pendencia_acao_canonica":{"id":"pendente"}},
        "messages":[{"role":"user","content":"pedido anterior"}]}}
    antes = deepcopy(ctx)
    novo = projetar_contexto_diagnostico(ctx)
    mental = novo["estado"]["mente_integrada_estado"]
    assert ctx == antes and "plano_turno_atual" not in mental
    assert mental["turno_atual"] == {"id":123,"texto":"fecha ela","autoriza_execucao":True}
    for chave in ("ultima_acao_contrato","retrato_turno_atual","continuidade_geral","pendencia_acao_canonica"):
        assert mental[chave] == antes["estado"]["mente_integrada_estado"][chave]
    mental["ultima_acao_contrato"]["confirmado"] = False
    assert ctx == antes
