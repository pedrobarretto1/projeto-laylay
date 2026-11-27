"""Regressões de autoria, proporção e despedida com a composição da ponte."""

import json

import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala, formatar_contrato_fala_para_prompt
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.presenca_conversacional import (
    despedida_social, realizar_despedida_social, retribui_despedida_social,
)
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.memoria_mental.sessao_conversa import texto_encerra_conversa
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import proposta


DESPEDIDA = (
    "Kkkkk, qualquer dia a gente disputa uma partida então. Gostei muito do papo de hoje, Laylay. "
    "Vou seguir com o resto da manhã, até mais!"
)
DESVIO_DESPEDIDA = (
    "Kkkkk, é verdade — a gente já tá falando de jogadas malucas e cachorros com cabeça inclinada. "
    "Acho que o melhor jogo de tabuleiro do mundo é o da conversa."
)
RELATO_JOGO = (
    "Aí sim, uma adversária perigosa kkkk. Eu sou daqueles que tenta planejar tudo e acaba "
    "perdendo por causa de uma jogada que nem tinha considerado. O mais divertido é quando "
    "a partida rende umas boas risadas."
)
RESPOSTA_JOGO = "Perigosa nada, teu tabuleiro só não tem seguro contra imprevistos, kkk."
ESCOLHA = (
    "Bom dia de novo, Laylay! Tava pensando aqui: tem dias em que a melhor coisa é sair pra "
    "caminhar sem destino, só pra espairecer. Você iria por uma rua movimentada ou por um parque tranquilo?"
)
RESPOSTA_ESCOLHA = "Bom dia! Eu escolheria o parque, porque lá dá pra espairecer sem buzina."


def _plano(entrada):
    turno = classificar_modalidade_turno(entrada)
    plano = {"id": turno["id"], "texto_usuario": entrada, "autoriza_execucao": False, "comandos": []}
    return {**plano, "contrato_fala": construir_contrato_semantico_fala(entrada, turno=turno, plano=plano)}


@pytest.mark.parametrize("entrada", [DESPEDIDA, "Valeu pela conversa, Laylay, até logo!",
                                    "Gostei do papo. Tenho que ir, te vejo amanhã. Até mais!"])
def test_fecho_social_reconhece_despedida_composta_sem_fechar_sessao(entrada):
    assert despedida_social(entrada)
    assert not texto_encerra_conversa(entrada)
    assert "despedida_social" in _plano(entrada)["contrato_fala"]["atos"]
    assert retribui_despedida_social("Gostei do papo também, até a próxima!")


@pytest.mark.parametrize("entrada", [
    "No roteiro ela diz: «Gostei do papo de hoje, até mais!»",
    "O passeio vai até mais tarde!",
    "Gostei do papo. Até mais! Qual jogo você escolhe?",
    "Gostei do papo. No roteiro ela diz, até mais!",
])
def test_fecho_social_preserva_pergunta_citacao_e_sentido_do_adverbio(entrada):
    assert not despedida_social(entrada)


def test_fecho_local_nao_substitui_pedido_antes_da_virgula():
    entrada = "Gostei do papo. Resuma nossa conversa, até mais!"
    assert not realizar_despedida_social(entrada, plano=_plano(entrada))


def test_ponte_exige_despedida_apos_reparar_repeticao(monkeypatch):
    monkeypatch.setattr(autoria, "PONTE", PONTE_INSTALADA)
    historico = [{"role": "user", "content": RELATO_JOGO}, {"role": "assistant", "content": RESPOSTA_JOGO}]
    dados = autoria.coletar_autoria({"entrada": DESPEDIDA, "historico": historico},
                                  [proposta(RESPOSTA_JOGO), proposta(DESVIO_DESPEDIDA)])
    assert "despedida_social" in dados["plano"]["contrato"]["atos"]
    assert dados["http"] == 2 and len(dados["publicacoes"]) == 1
    assert retribui_despedida_social(dados["resposta"]["texto"])
    assert not dados["resposta"]["encerrada"] and not dados["resposta"]["degradada"]


def test_ponte_reparo_de_autoria_entrega_a_fala_atual_uma_vez(monkeypatch):
    monkeypatch.setattr(autoria, "PONTE", PONTE_INSTALADA)
    historico = [
        {"role": "user", "content": "Você prefere arriscar ou jogar no seguro?"},
        {"role": "assistant", "content": "Eu prefiro arriscar uma jogada maluca."},
    ]
    copiada = RELATO_JOGO + " Assim também dá pra fazer uma jogada que ninguém esperava."
    dados = autoria.coletar_autoria({"entrada": RELATO_JOGO, "historico": historico},
                                  [proposta(copiada), proposta(RESPOSTA_JOGO)])
    mensagens = dados["envios"][-1]["messages"]
    reparo = json.loads(mensagens[-1]["content"])
    assert any("resposta_repetida_literal" in (t.get("problemas_bloqueantes") or []) for t in dados["trace"])
    assert sum(m["content"].count(RELATO_JOGO) for m in mensagens) == 1
    assert reparo["mensagem_atual"] == RELATO_JOGO
    assert "Eu prefiro arriscar uma jogada maluca." in mensagens[-1]["content"]
    assert "preservar_autoria_do_interlocutor" in reparo["contrato_de_reparo"]
    assert dados["resposta"]["texto"] == RESPOSTA_JOGO and len(dados["publicacoes"]) == 1


def test_escolha_nominal_simples_orienta_ritmo_sem_perder_humor():
    entrada = "Você escolheria um cachorro ou um gato?"
    plano = _plano(entrada)
    contrato = plano["contrato_fala"]
    assert "em uma frase com um detalhe concreto" in formatar_contrato_fala_para_prompt(contrato, compacto=True)
    assert not contrato["permite_pergunta"]
    curta = "Eu escolheria um cachorro. Parceiro oficial de passeio."
    assert avaliar_qualidade_comunicacao(entrada, curta, plano=plano)["aceita"]


def test_ponte_orienta_ritmo_da_escolha_com_saudacao_sem_descartar_autoria(monkeypatch):
    monkeypatch.setattr(autoria, "PONTE", PONTE_INSTALADA)
    longa = RESPOSTA_ESCOLHA + " Um passeio assim também dá espaço para ouvir a chuva e reparar nas folhas."
    dados = autoria.coletar_autoria({"entrada": ESCOLHA, "historico": []}, [proposta(longa)])
    assert any("em uma frase com um detalhe concreto" in m["content"] for m in dados["envios"][0]["messages"])
    assert dados["http"] == len(dados["publicacoes"]) == 1
    assert dados["resposta"]["texto"] == longa and not dados["resposta"]["degradada"]


@pytest.mark.parametrize("entrada", [
    "Você escolheria um cachorro ou um gato? Explique a escolha em detalhes.",
    "Você escolheria um cachorro ou um gato que te faz lembrar da infância?",
    "Qual foi o bicho da história? Você escolheria um cachorro ou um gato?",
    "Escreva uma história. Você escolheria um cachorro ou um gato?",
])
def test_escolha_nominal_nao_impede_desenvolver_outros_pedidos(entrada):
    assert not any("em uma frase com um detalhe concreto" in item
                   for item in _plano(entrada)["contrato_fala"]["conteudos_obrigatorios"])
