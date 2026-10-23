"""O getter instalado do terminal usa o retrato visual canônico, não estado cru."""
from __future__ import annotations

import ast
from functools import partial
from pathlib import Path
from types import SimpleNamespace

import pytest

from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from mente_laylay.emocoes.estado_emocional import aplicar_evento_emocional
from mente_laylay.integracao.desktop_bridge import sanitizar_estado
from mente_laylay.integracao.politicas_composicao import construir_estado_visual
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.personalidade.retrato_entrega import criar_retrato_entrega_fala


def _composicao(conversa: dict, agora: float):
    estado = EstadoCompartilhadoRuntime(conversacional=conversa)
    raiz = Path(__file__).resolve().parents[2] / "laylay.py"
    arvore = ast.parse(raiz.read_text(encoding="utf-8"))
    atribuicoes = {"_conversa_estado_get", "_estado_visual_laylay"}
    nos = [no for no in arvore.body if (
        isinstance(no, ast.Assign) and any(isinstance(alvo, ast.Name) and alvo.id in atribuicoes for alvo in no.targets)
    ) or (isinstance(no, ast.FunctionDef) and no.name == "_estado_terminal_2")]
    assert len(nos) == 3, "A composição real mudou; revisar o alvo em vez de montar outra composição"
    # Apenas dependências de hardware são amostras inertes. Estado compartilhado,
    # reader de validade e o wiring do composition root continuam os reais.
    nomes = {
        "partial": partial,
        "_estado_compartilhado_runtime": estado,
        "_construir_estado_visual_mente": partial(construir_estado_visual, time_fn=lambda: agora),
        "_ouvido_whisper_runtime": SimpleNamespace(ativo=lambda: True, nivel_microfone=lambda: .37),
        "_servicos_background_runtime": SimpleNamespace(ativos=lambda: ["Laylay-Ouvido"]),
    }
    exec(compile(ast.Module(body=nos, type_ignores=[]), str(raiz), "exec"), nomes)
    return nomes["_estado_terminal_2"], nomes["_estado_visual_laylay"]


def _estado_causal():
    evento = criar_evento_emocional_causal(
        origem="resultado_operacional", causa="resultado confirmado para validação",
        evidencia_ref="resultado:teste:1", natureza_evidencia="fato_observado",
        responsabilidade="sistema", confianca=.97, relevancia=.95, novidade=.8,
        intensidade=3, sensibilidade="normal", alvo="teste", validade_s=120,
        permite_expressao=True, emocao="brava", nivel=3, arco="reacao", ts=1000,
    )
    return aplicar_evento_emocional({"modo_chat": True}, evento, agora=1000)


@pytest.mark.parametrize("caso", ["vigente", "expirado", "sem_episodio", "contido", "preparando_fala", "audio_com_retrato"])
def test_terminal_e_overlay_compartilham_validade_nivel_e_entrega(caso):
    conversa = _estado_causal()
    agora = 1010
    if caso == "expirado":
        agora = 1300
    elif caso == "sem_episodio":
        conversa["episodio_emocional"] = {}
    elif caso == "contido":
        conversa["episodio_emocional"]["permite_expressao"] = False
    elif caso == "preparando_fala":
        conversa.update(is_speaking=True, audio_playing=False)
    elif caso == "audio_com_retrato":
        retrato = criar_retrato_entrega_fala(conversa, mensagem_id="entrega:1", agora=1010)
        conversa.update(current_emotion="calma", emotion_level=1, audio_playing=True,
                        retrato_entrega_fala=retrato.como_dict())
    terminal, visual = _composicao(conversa, agora)
    esperado = visual()
    recebido = sanitizar_estado(terminal())
    assert (recebido["emotion"], recebido["emotion_level"]) == (esperado["emotion"], esperado["level"])
    assert recebido["activity"] == esperado["activity"]
    assert recebido["interaction_mode"] == "chat"
    assert recebido["voice_available"] is True
    assert recebido["microphone_level"] == pytest.approx(.37)
