"""O tempo da situação imaginada não equivale ao tempo da consulta factual."""
import pytest

from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import proposta


ENTRADA = (
    'Terraria então! Boa escolha. Se nós dois começássemos um mundo novo agora, qual seria '
    'nosso plano para o primeiro dia? Eu ficaria com a construção e você com a exploração. '
    'Você toparia essa divisão ou prefere outra?'
)


@pytest.mark.parametrize('texto', [
    ENTRADA,
    'Se improvisássemos uma peça hoje, que papel você escolheria?',
    'Se montássemos uma horta agora, como organizaríamos o primeiro dia?',
    'Se você pudesse convidar nós dois para uma atividade agora — uma conversa, jogo ou desafio criativo — qual seria sua proposta, Laylay?',
    'Se pudéssemos improvisar hoje, qual seria sua proposta?',
    'Se pudéssemos criar algo hoje (um desenho ou uma música), qual seria nossa ideia?',
])
def test_tempo_no_antecedente_hipotetico_nao_solicita_fonte_recente(texto):
    assert not classificar_atualidade_factual(texto)['depende_atualidade']


@pytest.mark.parametrize('texto', [
    'Se começássemos agora, quem está conosco?',
    'Se improvisássemos hoje, que papel você escolheria? Quem está online agora?',
    'Se planejássemos a viagem hoje, qual seria a previsão do tempo?',
    'Se estivéssemos na oficina hoje, qual seria o requisito atual?',
    'Se tivéssemos tempo agora, como você verificaria quem trabalha hoje?',
    'Se ensaiássemos hoje, qual papel você escolheria e quem está na sala?',
    'Se a classe sair hoje, quem fica na secretaria?',
    'Se eu fosse ao aeroporto agora, que portão eu usaria para o voo 1130?',
    'Se eu fosse ao posto agora, qual o valor que eu pagaria pela gasolina?',
    'Se eu fosse ao caixa agora, quanto eu teria na minha conta?',
    'Se viajássemos hoje, qual seria nosso plano de saúde?',
    'Se fôssemos ao aeroporto agora, como você organizaria a conexão e o voo 1130 mudou de portão?',
    'Se eu fosse ao aeroporto agora, qual seria nosso plano para a conexão ou será que o portão do voo 1130 mudou?',
    'Se eu fosse ao aeroporto agora, qual seria nosso plano para a conexão ou o voo 1130 já decolou?',
    'Se fôssemos ao aeroporto agora — um passeio ou uma visita — que portão usaríamos?',
    'Se você pudesse propor algo agora — a loja abriu ou ainda está fechada? — qual seria sua proposta?',
    'Se pudéssemos improvisar hoje — um jogo ou um conto — qual seria nossa proposta ou o voo já decolou?',
    'Se eu pudesse sugerir algo agora — um jogo ou um conto — qual seria sua proposta, Laylay? O voo 1130 saiu?',
    'Se eu pudesse sugerir algo agora — um jogo ou um conto — qual seria sua proposta, Laylay? Quem está na sala?',
    'Se eu pudesse decidir algo agora — um jogo ou um conto — qual seria sua proposta para começar pois o voo 1130 mudou de portão?',
    'Se eu pudesse sugerir algo agora — um jogo ou um conto — que papel você escolheria — o voo 1130 saiu?',
    'Se ensaiássemos hoje, como você organizaria o espaço e a porta está trancada?',
    'Quem está conosco agora?',
])
def test_tempo_hipotetico_nao_dispensa_consulta_atual_independente(texto):
    assert classificar_atualidade_factual(texto)['depende_atualidade']


def test_deliberacao_imaginativa_publica_sem_exigir_fonte_recente(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    fala = 'Eu topo. No primeiro dia eu exploraria os arredores enquanto você monta um abrigo.'
    d = autoria.coletar_autoria({'entrada': ENTRADA, 'historico': []}, [proposta(fala)])
    assert not d['plano']['atualidade']['depende_atualidade']
    assert not d['plano']['fundamentacao'].get('requer_evidencia_recente')
    assert d['resposta']['texto'] == fala
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']
    assert len(d['publicacoes']) == d['http'] == 1
