"""Diagnóstico P21 projeta validade/expressão sem alterar estado ou expor relato."""
from copy import deepcopy
import hashlib
import time

import pytest

from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional, retrato_emocional_expressavel
from mente_laylay.memoria_mental.diagnostico_mente import construir_diagnostico_mente
from mente_laylay.memoria_mental.formatacao_diagnostico import formatar_diagnostico_terminal


def _estado(*, permitido=True, idade=0):
    agora = time.time()
    evento = criar_evento_emocional_causal(
        origem="controle_p21", causa="relato pessoal que não deve aparecer no diagnóstico",
        evidencia_ref="controle:p21:ocorrencia", natureza_evidencia="fato_observado",
        responsabilidade="usuario", confianca=.97, relevancia=.95, intensidade=2,
        permite_expressao=permitido, emocao="alegre", nivel=2,
        motivo_expressao="expressao_confirmada" if permitido else "vulnerabilidade_sem_deboche",
        ts=agora-idade, validade_s=120,
    )
    conversa = aplicar_evento_emocional({}, evento, agora=agora-idade)
    return {"mental":{"eventos_emocionais_causais":{"atual":evento}}, "conversacional":conversa}


@pytest.mark.parametrize("permitido,idade", [(True,0), (False,0), (True,150)])
def test_diagnostico_revela_intensidade_e_mesma_projecao_da_voz_sem_escrever(permitido,idade):
    estado = _estado(permitido=permitido, idade=idade)
    antes = deepcopy(estado)
    retrato = construir_diagnostico_mente(estado, {})["estado_emocional_causal"]
    assert "intensidade" in retrato
    assert retrato["causa_ref"].startswith("causa:")
    assert (retrato["emocao_expressavel"], retrato["nivel_expressavel"]) == retrato_emocional_expressavel(estado["conversacional"])
    assert retrato["autoriza_execucao"] is False
    assert estado == antes
    assert "relato pessoal" not in str(retrato)


def test_causa_valida_com_expressao_contida_tem_motivo_de_supressao():
    retrato = construir_diagnostico_mente(_estado(permitido=False), {})["estado_emocional_causal"]
    assert retrato["validade"] is True and retrato["expressao"] is False
    assert retrato["supressao"] == "vulnerabilidade_sem_deboche"


def test_evento_expirado_nao_usa_motivo_otimista_como_supressao():
    retrato = construir_diagnostico_mente(_estado(idade=150), {})["estado_emocional_causal"]
    assert retrato["validade"] is False
    assert retrato["supressao"] == "evento_fora_da_validade"
    assert retrato["emocao_expressavel"] == "calma"


def test_texto_do_diagnostico_expoe_decisao_e_supressao_sem_relato_pessoal():
    diagnostico = construir_diagnostico_mente(_estado(permitido=False), {})
    texto = formatar_diagnostico_terminal(diagnostico)
    for campo in ("intensidade=2", "expressável=calma", "supressão=vulnerabilidade_sem_deboche", "decisão=expressao_contida"):
        assert campo in texto
    assert "relato pessoal" not in texto


def test_diagnostico_nao_atribui_episodio_forte_a_causa_nova_sem_prioridade():
    agora = time.time()
    forte = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="repetição comprovada", evidencia_ref="controle:forte",
        natureza_evidencia="fato_observado", responsabilidade="usuario", confianca=.97,
        relevancia=.95, intensidade=3, permite_expressao=True, emocao="brava", nivel=3, ts=agora,
    )
    fraco = criar_evento_emocional_causal(
        origem="observador_janela", causa="novidade menor", evidencia_ref="controle:fraco",
        natureza_evidencia="fato_observado", responsabilidade="sistema", confianca=.95,
        relevancia=.7, intensidade=1, permite_expressao=True, emocao="surpresa", nivel=1, ts=agora,
    )
    conversa = aplicar_evento_emocional({}, forte, agora=agora)
    conversa = aplicar_evento_emocional(conversa, fraco, agora=agora)
    assert conversa["episodio_emocional"] == forte, "controle: prioridade já funciona antes do diagnóstico"
    estado = {"mental":{"eventos_emocionais_causais":{"atual":fraco}}, "conversacional":conversa}
    antes = deepcopy(estado)
    retrato = construir_diagnostico_mente(estado, {})["estado_emocional_causal"]
    ref = "causa:" + hashlib.sha256(forte["evidencia_ref"].encode()).hexdigest()[:16]
    assert retrato["emocao_expressavel"] == "brava"
    assert retrato["causa_ref"] == ref, "primeira fronteira: diagnóstico atribuiu emoção à última proposta"
    assert retrato["responsabilidade"] == "usuario" and retrato["intensidade"] == 3
    assert estado == antes


def test_evento_elegivel_sem_episodio_nao_e_anunciado_como_expressao_atual():
    estado = _estado()
    estado["conversacional"] = {"current_emotion":"calma", "emotion_level":1}
    retrato = construir_diagnostico_mente(estado, {})["estado_emocional_causal"]
    assert retrato["validade"] and retrato["expressao"], "evento observado continua elegível"
    assert retrato["emocao_expressavel"] == "calma"
    assert retrato["decisao_expressao"] == "expressao_contida"
    assert retrato["supressao"] == "episodio_nao_expressavel"
