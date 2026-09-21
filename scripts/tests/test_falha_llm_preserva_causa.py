"""Falha de geração não fornece evidência de ambiguidade do pedido."""
import json

import pytest

from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural
from tests.test_reparo_preserva_objetivo_turno import plano_explicacao


FALHAS = [
    ("__LAYLAY_LLM_TIMEOUT__", "tempo"),
    ("__LAYLAY_LLM_INDISPONIVEL__", "indisponível"),
    ("__LAYLAY_LLM_OCUPADA__", "disponível"),
]


def preparar(texto, bruto, callback):
    return preparar_resposta_para_execucao(
        texto, bruto, enviar_mensagem_cb=callback,
        limpar_texto_fala_cb=lambda t: t, fallback_fala="Contingência",
        memoria_sqlite=None, contexto_comunicacao={"plano_turno": plano_explicacao(texto)},
        log=lambda _: None,
    )


@pytest.mark.parametrize("texto", ["como eu poderia pausar a música?", "como eu poderia abrir a calculadora?"])
@pytest.mark.parametrize("sentinela,indicador", FALHAS)
def test_falha_principal_preserva_categoria_sem_pedir_reformulacao(texto, sentinela, indicador):
    chamadas = []
    resultado = preparar(texto, sentinela, lambda *a, **kw: chamadas.append(kw))
    assert chamadas == []
    assert resultado["comandos"] == []
    assert indicador in resultado["fala"].lower()
    assert "?" not in resultado["fala"]
    assert "__LAYLAY" not in resultado["fala"]
    final = verificar_fala_turno(resultado["fala"], plano=plano_explicacao(texto), origem="ia_final")
    assert final["fala"] == resultado["fala"]


@pytest.mark.parametrize("sentinela,indicador", FALHAS)
def test_falha_do_reparo_nao_vira_duvida_do_usuario(sentinela, indicador):
    chamadas = []
    def modelo(*a, **kw):
        chamadas.append(kw)
        return sentinela
    resultado = preparar("como eu poderia abrir a calculadora?",
                         json.dumps({"fala": "Não consigo abrir programas.", "comandos": []}), modelo)
    assert len(chamadas) == 1
    assert indicador in resultado["fala"].lower()
    assert "?" not in resultado["fala"]
    assert resultado["comandos"] == []


def test_reparo_e_autoria_rejeitados_nao_inventam_timeout_ou_ambiguidade():
    resultado = preparar("como eu poderia abrir a calculadora?",
                         '{"fala":"Não consigo abrir programas.","comandos":[]}',
                         lambda *a, **kw: '{"fala":"Não consigo abrir programas.","comandos":[]}')
    assert "resposta confiável" in resultado["fala"]
    assert "?" not in resultado["fala"]
    assert "tempo" not in resultado["fala"]
    assert resultado["comandos"] == []


def test_sem_evidencia_tecnica_preserva_contingencia_contextual():
    fala = fala_contingencia_natural("essa bota é boa?").lower()
    assert any(t in fala for t in ("detalhe", "completa", "explica"))


@pytest.mark.parametrize("sentinela,indicador", FALHAS)
def test_falha_da_autoria_final_preserva_categoria(sentinela, indicador):
    chamadas = []
    def modelo(*a, **kw):
        chamadas.append(kw)
        return '{"fala":"Não consigo abrir programas.","comandos":[]}' if len(chamadas) == 1 else sentinela
    resultado = preparar("como eu poderia abrir a calculadora?",
                         '{"fala":"Não consigo abrir programas.","comandos":[]}', modelo)
    assert len(chamadas) == 2
    assert indicador in resultado["fala"].lower()
    assert "?" not in resultado["fala"]
    assert resultado["comandos"] == []


def test_excecao_sem_categoria_nao_inventa_timeout_nem_insiste_no_modelo():
    chamadas = []
    def modelo(*a, **kw):
        chamadas.append(kw)
        raise RuntimeError("detalhe privado")
    resultado = preparar("como eu poderia abrir a calculadora?",
                         '{"fala":"Não consigo abrir programas.","comandos":[]}', modelo)
    assert len(chamadas) == 1
    assert resultado["fala"] == "Houve uma falha ao gerar minha resposta."
    assert "privado" not in resultado["fala"]
    assert resultado["comandos"] == []


@pytest.mark.parametrize("sentinela,indicador", FALHAS)
def test_recuperacao_de_vazio_preserva_falha_subsequente(sentinela, indicador):
    chamadas = []
    def modelo(*a, **kw):
        chamadas.append(kw)
        return "{}" if len(chamadas) == 1 else sentinela
    resultado = preparar("como eu poderia abrir a calculadora?",
                         '{"fala":"Não consigo abrir programas.","comandos":[]}', modelo)
    assert len(chamadas) == 2
    assert indicador in resultado["fala"].lower()
    assert resultado["comandos"] == []
    assert "?" not in resultado["fala"]


def test_recuperacao_vazia_nao_inventa_contexto_ausente():
    resultado = preparar("como eu poderia abrir a calculadora?",
                         '{"fala":"Não consigo abrir programas.","comandos":[]}',
                         lambda *a, **kw: "{}")
    assert "resposta confiável" in resultado["fala"]
    assert resultado["comandos"] == []


@pytest.mark.parametrize("motivo", [
    "limite_chamadas", "principal_duplicada", "reparo_duplicado", "prazo_esgotado",
    "turno_obsoleto", "turno_finalizado", "fatia_secundaria_insuficiente",
    "circuito_aberto", "probe_em_andamento",
])
def test_estado_de_orcamento_nao_vaza_e_preserva_categoria_na_recuperacao(motivo):
    from mente_laylay.cognicao.estado_tecnico_llm import (
        estado_bloqueio_orcamento_llm, categoria_estado_tecnico_llm, eh_estado_tecnico_llm,
    )
    from mente_laylay.personalidade.contingencia_natural import fala_falha_geracao
    sentinela = estado_bloqueio_orcamento_llm(motivo)
    categoria = "orcamento_" + motivo
    assert categoria_estado_tecnico_llm(sentinela) == categoria
    assert eh_estado_tecnico_llm(sentinela.replace("_", " "))
    texto = "como eu poderia abrir a calculadora?"
    assert verificar_fala_turno(sentinela, plano=plano_explicacao(texto))["acao"] == "bloqueada"
    chamadas = []
    def modelo(*a, **kw):
        chamadas.append(kw)
        return "{}" if len(chamadas) == 1 else sentinela
    resultado = preparar(texto, '{"fala":"Não consigo abrir programas.","comandos":[]}', modelo)
    assert resultado["fala"] == fala_falha_geracao(categoria)
    assert resultado["comandos"] == []
    assert verificar_fala_turno(resultado["fala"], plano=plano_explicacao(texto))["fala"] == resultado["fala"]


def test_motivo_desconhecido_nao_expoe_detalhe_nem_inventa_causa():
    from mente_laylay.cognicao.estado_tecnico_llm import estado_bloqueio_orcamento_llm, categoria_estado_tecnico_llm
    sentinela = estado_bloqueio_orcamento_llm("detalhe privado")
    assert "privado" not in sentinela
    assert categoria_estado_tecnico_llm(sentinela) == "chamada_nao_disponivel"
