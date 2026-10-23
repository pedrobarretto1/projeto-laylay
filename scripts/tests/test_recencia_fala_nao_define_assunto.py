"""Recência preserva histórico; não cria referência para uma pergunta nova."""
from copy import deepcopy
import time

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.seletor_contexto import selecionar_contexto_turno


@pytest.mark.parametrize("texto", [
    "e o que voce esta fazendo?", "como estão as coisas no computador?",
    "qual sua opinião sobre estudar de manhã?", "como funciona uma playlist?",
])
@pytest.mark.parametrize("anterior", [
    "Oi! Tudo bem aqui, obrigada por perguntar.",
    "A lâmpada do quarto está desligada.",
    "Estou esperando você voltar com a conversa.",
])
def test_pergunta_autossuficiente_nao_promove_fala_recente_a_assunto(texto, anterior):
    mente = {"ultima_resposta": anterior, "continuidade_fala_ts": time.time()}
    antes = deepcopy(mente)
    r = selecionar_contexto_turno(texto, turno=classificar_modalidade_turno(texto), mente=mente)
    assert r["novo_assunto"] is True
    assert not any(c["origem"] == "ultima_fala" for c in r["selecionados"])
    assert mente == antes


@pytest.mark.parametrize("texto", [
    "como assim?", "o que você quis dizer?", "explica melhor", "não entendi", "repete isso",
    "por que você disse isso?", "e você?",
])
def test_retomada_e_esclarecimento_preservam_a_fonte_anterior(texto):
    anterior = "Falta uma leitura atual para conferir o estado do computador."
    r = selecionar_contexto_turno(texto, turno=classificar_modalidade_turno(texto),
        mente={"ultima_resposta": anterior, "continuidade_fala_ts": time.time()})
    assert any(c["origem"] == "ultima_fala" and c["conteudo"] == anterior for c in r["selecionados"])


def test_pergunta_nova_nao_apaga_pendencia_ou_historico():
    mente = {"ultima_resposta": "Como foi sua aula?", "continuidade_fala_ts": time.time(),
             "pergunta_aberta_texto": "Como foi sua aula?", "pergunta_aberta_ts": time.time()}
    r = selecionar_contexto_turno("como está o computador?", turno={"modalidade": "pergunta"}, mente=mente)
    assert any(c["origem"] == "pergunta_aberta" for c in r["selecionados"])
    assert mente["pergunta_aberta_texto"] == "Como foi sua aula?"


@pytest.mark.parametrize("anterior,texto", [
    ("Para recuperar a matéria, tente fazer cinco exercícios por dia.", "Preciso fazer quantos exercícios por dia?"),
    ("Prática distribuída ajuda a estudar matemática.", "Prática distribuída funciona para matemática?"),
    ("Você pode organizar as notas por data.", "Como organizar as notas por data?"),
    ("Matemática exige atenção.", "Matemática cansa?"),
])
def test_continuidade_lexical_forte_nao_depende_de_pronome(anterior, texto):
    r = selecionar_contexto_turno(texto, turno=classificar_modalidade_turno(texto),
        mente={"ultima_resposta": anterior, "continuidade_fala_ts": time.time()})
    assert any(c["origem"] == "ultima_fala" for c in r["selecionados"])


@pytest.mark.parametrize("anterior,texto", [
    ("Como foi sua aula de matemática?", "Como está o computador?"),
    ("O arquivo foi revisado com cuidado.", "Como foi sua aula?"),
])
def test_termo_generico_em_comum_nao_faz_recencia_provar_vinculo(anterior, texto):
    r = selecionar_contexto_turno(texto, turno=classificar_modalidade_turno(texto),
        mente={"ultima_resposta": anterior, "continuidade_fala_ts": time.time()})
    assert not any(c["origem"] == "ultima_fala" for c in r["selecionados"])
