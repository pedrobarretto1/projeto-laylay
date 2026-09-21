"""Ausência de prova de efeito não altera o ato nem a fonte da resposta."""
import json

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import (
    avaliar_qualidade_comunicacao, montar_mensagens_reparo_comunicacao,
)
from tests.test_explicacao_capacidades_sem_execucao import preparar
from tests.test_reconhecimento_relato_explicito import preparar as preparar_relato


def plano_explicacao(texto):
    estado, _, _ = preparar(texto)
    plano = planejar_turno(texto, turno=estado["turno_atual"], mente={})
    plano["contrato_fala"] = estado["contrato_fala_atual"]
    assert estado["turno_atual"]["autoriza_execucao"] is False
    assert plano["contrato_fala"]["roteiro_concreto"]["estrategia"] == "explicacao_capacidades"
    return plano


@pytest.mark.parametrize("texto", [
    "como eu poderia aumentar o volume?",
    "como eu poderia pausar a música?",
    "como eu poderia abrir a calculadora?",
    "como eu poderia ligar a lâmpada?",
    "como eu faria para criar um arquivo?",
    "como eu poderia fechar a aba?",
])
def test_reparo_de_resultado_inventado_preserva_pergunta_e_documento(texto):
    plano = plano_explicacao(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, "O arquivo foi salvo.", plano=plano)
    assert "resultado_operacional_sem_evidencia" in avaliacao["problemas"]
    assert not avaliacao["aceita"]
    contrato = avaliacao["contrato_reparo"]
    assert contrato["estrategia"] == "explicacao_capacidades"
    assert contrato["atos_obrigatorios"] == ["pergunta"]
    mensagens = montar_mensagens_reparo_comunicacao(texto, "O arquivo foi salvo.", avaliacao)
    sistema = mensagens[0]["content"]
    assert "O usuário relatou um pedido" not in sistema
    assert "Pode perguntar como foi" not in sistema
    assert "contrato_de_reparo" in sistema
    assert "exemplos" in sistema
    payload = json.loads(mensagens[1]["content"])
    assert payload["mensagem_atual"] == texto
    assert payload["contrato_de_reparo"]["documentacao_capacidades"] == plano["contrato_fala"]["documentacao_capacidades"]
    assert payload["contrato_de_reparo"]["autoriza_execucao"] is False


def test_documentacao_nao_vem_do_rascunho_nem_do_historico():
    texto = "Ontem pedi para abrir o Opera; estou só relatando."
    plano = preparar_relato(texto)
    # Documento sem estratégia compatível não deve virar fonte do reparo.
    plano["contrato_fala"]["documentacao_capacidades"] = "FONTE_INDEVIDA"
    avaliacao = avaliar_qualidade_comunicacao(texto, "O Opera não abriu.", plano=plano)
    mensagens = montar_mensagens_reparo_comunicacao(texto, "O Opera não abriu.", avaliacao)
    payload = json.loads(mensagens[1]["content"])
    assert not payload["contrato_de_reparo"].get("documentacao_capacidades")
    assert "sem perguntar" in mensagens[0]["content"]
    assert payload["contrato_de_reparo"]["autoriza_execucao"] is False


def test_projecao_do_reparo_nao_perde_documentacao_viva():
    texto = "como eu poderia aumentar o volume?"
    plano = plano_explicacao(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, "O arquivo foi salvo.", plano=plano)
    assert avaliacao["contrato_reparo"].get("documentacao_capacidades") == plano["contrato_fala"]["documentacao_capacidades"]


@pytest.mark.parametrize("reparada", [
    "Para aumentar o volume, você pode dizer 'aumenta o volume'.",
    "O arquivo foi salvo.",
])
def test_pipeline_preserva_tarefa_do_reparo_e_revalida_efeito(reparada):
    texto = "como eu poderia aumentar o volume?"
    plano = plano_explicacao(texto)
    chamadas = []

    def modelo(mensagens, **opcoes):
        chamadas.append((mensagens, opcoes))
        return json.dumps({"fala": reparada, "comandos": []})

    resultado = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": "O arquivo foi salvo.", "comandos": []}),
        enviar_mensagem_cb=modelo, limpar_texto_fala_cb=lambda t: t,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano}, log=lambda _: None,
    )
    mensagens, opcoes = chamadas[0]
    assert "O usuário relatou um pedido" not in mensagens[0]["content"]
    contrato = json.loads(mensagens[1]["content"])["contrato_de_reparo"]
    assert contrato["documentacao_capacidades"] == plano["contrato_fala"]["documentacao_capacidades"]
    assert opcoes["_com_tools"] is False
    assert resultado["comandos"] == []
    if reparada.startswith("Para aumentar"):
        assert len(chamadas) == 1
        assert resultado["fala"] == reparada
        assert verificar_fala_turno(reparada, plano=plano, origem="ia_final")["aceita"]
    else:
        assert resultado["fala"] != reparada
