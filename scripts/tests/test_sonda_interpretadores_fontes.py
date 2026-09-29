"""Diagnóstico de cobertura do componente, não validação do loop da Laylay."""

import json

from scripts.analises.sonda_interpretadores_fontes import medir_componentes


def _resposta(mensagens, **kwargs):
    return json.dumps({"atos": [{"tipo": "pedido_acao"}], "modalidade_geral": "comando",
                       "operacional": {"pedido_real": True, "autoriza_execucao": True}})


def test_auditoria_mostra_historia_disponivel_mas_ausente_da_entrada_modelo():
    caso = {"id": "auditoria", "alvo": "Regra original da estufa.",
            "posteriores": ["A regra está revogada.", "Reative aquela regra."]}
    resultado = medir_componentes(caso, enviar=_resposta)
    segunda = resultado["falas"][1]
    assert len(segunda["contexto_disponivel"]["mensagens"]) == 2
    payload = json.loads(segunda["chamadas"][0]["mensagens"][1]["content"])
    assert payload["contexto"] == segunda["contexto_resumido"]
    assert "Regra original" not in json.dumps(payload, ensure_ascii=False)
    assert "revogada" not in json.dumps(payload, ensure_ascii=False)
    assert payload["fala_atual"] == "Reative aquela regra."
    # Mesmo uma proposta maliciosa do modelo perde autorização no normalizador real.
    assert segunda["leitura_semantica"]["operacional"]["autoriza_execucao"] is False
    assert resultado["pode_registrar_vigencia"] is False


def test_historicos_opostos_geram_mesmo_payload_neste_componente():
    def obter(alvo):
        caso = {"id": "teste", "alvo": alvo, "posteriores": ["Pode restaurar aquela regra?"]}
        return medir_componentes(caso, enviar=_resposta)["falas"][0]["chamadas"][0]["mensagens"]
    assert obter("A regra da estufa foi revogada.") == obter("A regra do servidor foi revogada.")


def test_contexto_capturado_nao_muda_quando_historico_avanca():
    caso = {"id": "teste", "alvo": "Regra", "posteriores": ["Primeira fala", "Segunda fala"]}
    resultado = medir_componentes(caso)
    assert [len(f["contexto_disponivel"]["mensagens"]) for f in resultado["falas"]] == [1, 2]
    assert all(not f["chamadas"] for f in resultado["falas"])


def test_falha_de_modelo_nao_vira_leitura_valida():
    def falhar(*args, **kwargs):
        raise TimeoutError("teste")
    caso = {"id": "teste", "alvo": "Regra", "posteriores": ["Cancele"]}
    resultado = medir_componentes(caso, enviar=falhar)
    assert resultado["falas"][0]["leitura_semantica"] == {}
    assert resultado["falas"][0]["chamadas"][0]["erro"] == "TimeoutError"
    assert resultado["autoriza_efeito"] is False
