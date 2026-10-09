from __future__ import annotations

from copy import deepcopy
import json
import time

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import (
    extrair_leitura_semantica_da_ia,
    preparar_resposta_para_execucao,
)
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import atualizar_plano_turno, planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.emocoes.contrato_causal import criar_evento_leitura_semantica_usuario
from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime
from mente_laylay.memoria_mental.trilha_turno import registrar_etapa_turno
from mente_laylay.personalidade import prompt_voz_unica


NEUTRO_COMPLETO = {
    "estado_usuario": "nenhum", "intensidade": 0,
    "causa_expressa": "", "trecho_evidencia": "",
    "natureza_evidencia": "inferencia", "hipotetica": False,
    "alvo": "estado_geral", "confianca": 0.0,
}
NEUTRO_COMPACTO = {"estado_usuario": "nenhum", "intensidade": 0}


def _bruto(emocional: dict | None, *, atos: list[str]) -> str:
    dados = {
        "fala": (
            "Bom saber que está bem. Sobre Slipknot, gosto da energia das músicas."
            if len(atos) > 1 else "Uma playlist reúne músicas numa lista."
        ),
        "emocao": "alegre", "nivel_emocao": 2,
        "tipo_interacao": "conversa", "leitura_turno": atos,
        "comandos": [], "aprendizados": [],
    }
    if emocional is not None:
        dados["leitura_emocional"] = emocional
    return json.dumps(dados, ensure_ascii=False)


def _preparar(texto: str, bruto: str) -> dict:
    return preparar_resposta_para_execucao(
        texto, bruto, enviar_mensagem_cb=None,
        limpar_texto_fala_cb=lambda fala: fala, fallback_fala="Estou aqui.",
        memoria_sqlite=None, log=lambda *_args: None,
    )


def _composicao(texto: str) -> tuple[EstadoCompartilhadoRuntime, ComposicaoTurnoRuntime]:
    turno = classificar_modalidade_turno(texto)
    retrato, _ = construir_retrato_turno(
        texto, turno=turno, mente={}, contexto_perceptivo={},
    )
    turno["retrato_id"] = retrato["id"]
    estado = EstadoCompartilhadoRuntime(mental={
        "turno_atual": turno, "retrato_turno_atual": retrato,
        "plano_turno_atual": planejar_turno(texto, turno=turno, mente={}),
    })
    composicao = ComposicaoTurnoRuntime(servicos={
        "_estado_compartilhado_runtime": estado,
        "_atualizar_plano_turno_mente": atualizar_plano_turno,
        "_registrar_etapa_turno_mente": registrar_etapa_turno,
        "time": time, "print": lambda *_args: None,
    })
    return estado, composicao


@pytest.mark.parametrize("texto,atos", [
    ("O que é uma playlist?", ["pergunta"]),
    ("eu estou bem, você gosta de Slipknot?", ["resposta_social", "pergunta_opiniao"]),
    ("liga a luz", ["pedido_acao"]),
])
@pytest.mark.parametrize("forma", [NEUTRO_COMPACTO, {"estado_usuario": "nenhum"}, {}, None])
def test_neutro_compacto_preserva_leitura_emocao_da_laylay_e_autoridade(texto, atos, forma):
    completa = _bruto(NEUTRO_COMPLETO, atos=atos)
    compacta = _bruto(forma, atos=atos)
    esperada = extrair_leitura_semantica_da_ia(completa, texto)
    leitura = extrair_leitura_semantica_da_ia(compacta, texto)
    assert leitura == esperada
    assert leitura["valida"] is True
    assert leitura["leitura_emocional"]["valida"] is False
    assert leitura["operacional"]["autoriza_execucao"] is False
    assert criar_evento_leitura_semantica_usuario(leitura, turno_id="neutro") == {}

    preparada = _preparar(texto, compacta)
    preparada_completa = _preparar(texto, completa)
    for campo in ("fala", "comandos", "aprendizados", "leitura_semantica", "emocao", "nivel_emocao"):
        assert preparada[campo] == preparada_completa[campo]
    assert preparada["emocao"] == "alegre"
    assert preparada["nivel_emocao"] == 2

    estado, composicao = _composicao(texto)
    plano_antes = estado.obter_copia("mental", "plano_turno_atual")
    autoridade_antes = estado.mental["turno_atual"]["autoriza_execucao"]
    proposta = ContratoPropostaPrincipal(
        turno_id=estado.mental["turno_atual"]["id"],
        texto_usuario=texto, resposta_bruta=compacta,
    )
    publicada = composicao.registrar_leitura_proposta(texto, leitura, proposta)
    assert publicada["leitura_emocional"] == esperada["leitura_emocional"]
    assert estado.obter_copia("mental", "plano_turno_atual") == plano_antes
    assert estado.mental["turno_atual"]["autoriza_execucao"] == autoridade_antes


@pytest.mark.parametrize("campo", ["causa_expressa", "trecho_evidencia", "confianca"])
def test_emocao_positiva_incompleta_continua_fail_closed(campo):
    texto = "Finalmente tirei esse peso das costas; entreguei o projeto."
    emocional = {
        "estado_usuario": "alivio", "intensidade": 2,
        "causa_expressa": "entrega do projeto",
        "trecho_evidencia": "tirei esse peso das costas",
        "natureza_evidencia": "inferencia", "hipotetica": False,
        "alvo": "estado_geral", "confianca": 0.94,
    }
    completa = extrair_leitura_semantica_da_ia(_bruto(emocional, atos=["relato"]), texto)
    assert completa["leitura_emocional"]["valida"] is True
    incompleta = deepcopy(emocional)
    del incompleta[campo]
    leitura = extrair_leitura_semantica_da_ia(_bruto(incompleta, atos=["relato"]), texto)
    assert leitura["leitura_emocional"]["valida"] is False
    assert criar_evento_leitura_semantica_usuario(leitura, turno_id="incompleta") == {}


@pytest.mark.parametrize("prompt", [
    prompt_voz_unica.BASE_SYSTEM_PROMPT,
    prompt_voz_unica.BASE_SYSTEM_PROMPT_RAPIDO,
], ids=["normal", "rapido"])
def test_prompt_exemplifica_contrato_emocional_completo_e_sem_acao_vazia(prompt):
    assert "Sem evidência: nenhum/0" in prompt
    exemplo = json.loads(prompt.rsplit("Retorne somente JSON válido, sem markdown nem texto externo:", 1)[1].strip())
    # O 4B copiou o exemplo mínimo também para emoções positivas no A/B.
    # A representação completa protege os campos que tornam essa leitura válida.
    assert set(exemplo["leitura_emocional"]) == set(NEUTRO_COMPLETO)
    assert '"comandos":[]' in prompt
    assert '"leitura_turno":[' in prompt
    assert '"emocao":"calma"' in prompt
    assert '"nivel_emocao":1' in prompt
    assert "quando o usuário nomeia emoção" in prompt
    assert "menor cópia literal sem mudar conjugação" in prompt
    assert "confiança >=0.72 só com suporte" in prompt
