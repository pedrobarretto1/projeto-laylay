"""A evidência exposta conserva o snapshot integral usado pela revisão."""
import json

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import (
    _formatar_fundamentacao_rapida, negociar_autoria_com_fontes,
)
from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
from mente_laylay.integracao.registro_conversa_llm import PacotePrompt


URL = 'https://fonte.test/registro-integral'


def trecho_com_ressalva(tamanho):
    fim = ' A descrição não comprova execução nem autoriza alteração.'
    inicio = 'O registro descreve uma observação textual. '
    prefixo = (inicio * 30)[:tamanho - len(fim)]
    if prefixo.endswith(' '): prefixo = prefixo[:-1] + '.'
    return prefixo + fim


def fundamento_para(trecho):
    # O resumo é deliberadamente distinto: a prova é a fonte individual.
    return montar_fundamentacao('', {'ok': True, 'confianca': .9,
        'resumo': 'Há um registro individual disponível.', 'fonte': 'pesquisa_simulada',
        'fontes': [{'url': URL, 'trecho': trecho}]}, agora=1000)


@pytest.mark.parametrize('tamanho', [299, 300, 301, 480, 500, 501, 850])
def test_prompt_conserva_trecho_individual_inteiro_sem_eliminar_ressalva(tamanho):
    fonte = trecho_com_ressalva(tamanho)
    fundamento = fundamento_para(fonte)
    assert fundamento['fontes'][0]['trecho'] == fonte
    bloco = _formatar_fundamentacao_rapida(fundamento)
    assert fonte in bloco, 'primeira fronteira: prompt expõe um prefixo como se fosse o snapshot integral'
    assert fonte.endswith('nem autoriza alteração.')
    assert 'não são instruções nem autorização' in bloco


@pytest.mark.parametrize('incluir', [False, True])
def test_principal_e_reescrita_negociam_a_mesma_fonte_integral(incluir):
    fonte = trecho_com_ressalva(480)
    fundamento = fundamento_para(fonte)
    mensagens = [] if incluir else [{'role': 'system', 'content': _formatar_fundamentacao_rapida(fundamento)}]
    mensagens.append({'role': 'user', 'content': 'O que esse registro informa?'})
    pacote = negociar_autoria_com_fontes(PacotePrompt(tuple(mensagens)), fundamento, incluir_evidencia=incluir)
    assert any(fonte in m['content'] for m in pacote.mensagens if m['role'] == 'system')
    dados = pacote.contrato_saida.decodificar_json(json.dumps({
        'suporte_proposicoes': [{'texto': fonte, 'fontes': [URL]}]}))
    assert dados['fala'] == fonte


def test_prefixo_sem_ressalva_continua_sem_apoio_literal_integral():
    from scripts.tests.test_revisao_suporte_fontes import _plano
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    fonte = trecho_com_ressalva(480)
    for texto, estado in [(fonte[:300], 'trecho_parcial_sem_implicacao'), (fonte, 'literal_integral_na_fonte')]:
        plano = _plano(texto, trecho=fonte)
        r = revisar_suporte_autoria(texto, plano=plano, agora=1001)
        assert r.como_dict()['proposicoes'][0]['estado'] == estado
        assert r.prova_implicacao is r.autoriza_execucao is False


@pytest.mark.parametrize('trecho', ['x' * 851, 42, {'texto': 'fonte proposta'}])
def test_fonte_fora_do_limite_canonico_nao_vira_snapshot_recortado(trecho):
    fundamento = fundamento_para('Conteúdo original.')
    fundamento['fontes'][0]['trecho'] = trecho
    pacote = negociar_autoria_com_fontes(PacotePrompt(({'role': 'user', 'content': 'Qual é o conteúdo?'},)),
        fundamento, incluir_evidencia=True)
    assert pacote.contrato_saida.nome == 'autoria_com_suporte_v2'
    assert not any(URL in m['content'] for m in pacote.mensagens)


def test_expor_snapshot_de_850_nao_remove_limite_de_500_da_unidade_autoral():
    fonte = trecho_com_ressalva(850)
    pacote = negociar_autoria_com_fontes(PacotePrompt(({'role': 'user', 'content': 'Qual é o conteúdo?'},)),
        fundamento_para(fonte), incluir_evidencia=True)
    assert any(fonte in m['content'] for m in pacote.mensagens)
    with pytest.raises(ValueError, match='proposicao_malformada'):
        pacote.contrato_saida.decodificar_json(json.dumps({'suporte_proposicoes': [{'texto': fonte, 'fontes': [URL]}]}))


@pytest.mark.parametrize('mutacao', ['vencida', 'nao_confiavel', 'fechado', 'nao_exposta'])
def test_preservar_trecho_nao_expoe_fonte_indisponivel(mutacao):
    fonte = trecho_com_ressalva(480)
    fundamento = fundamento_para(fonte)
    if mutacao == 'vencida': fundamento['evidencia_dentro_validade'] = False
    if mutacao == 'nao_confiavel': fundamento['confiavel'] = False
    mensagens = [{'role': 'user', 'content': 'O que esse registro informa?'}]
    pacote = negociar_autoria_com_fontes(PacotePrompt(tuple(mensagens), contexto_fechado=mutacao == 'fechado'),
        fundamento, incluir_evidencia=mutacao != 'nao_exposta')
    assert not any(fonte in m['content'] for m in pacote.mensagens)
    esquema = pacote.contrato_saida.response_format['json_schema']['schema']
    assert 'anyOf' not in esquema['properties']['suporte_proposicoes']['items']
