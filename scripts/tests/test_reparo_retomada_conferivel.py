"""A geração de reparo negocia somente realizações já conferíveis pelo host."""
import copy
import hashlib
import json

import pytest

from scripts.tests.test_retomada_usuario_preserva_autoria import CASOS, plano_com_fonte
from mente_laylay.cognicao.fundamentacao_factual import avaliar_nucleo_retomada_usuario, LIMITE_CONFERENCIA_RELATO_USUARIO
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao, montar_pacote_reparo_comunicacao


def pacote(fonte, pedido, ruim, *, alterar=None):
    plano = plano_com_fonte(fonte, pedido, ruim)
    if alterar:
        alterar(plano)
    avaliacao = avaliar_qualidade_comunicacao(pedido, ruim, plano=plano)
    return plano, montar_pacote_reparo_comunicacao(pedido, ruim, avaliacao, plano=plano,
        mensagens=[{'role': 'user', 'content': fonte}])


@pytest.mark.parametrize('fonte,pedido,ruim,boa', CASOS)
def test_reparo_negocia_realizacao_conferivel_em_vez_de_parafrase_livre(fonte, pedido, ruim, boa):
    plano, p = pacote(fonte, pedido, ruim)
    assert p.contexto_fechado and p.contrato_saida is not None, 'reparo ainda pede prosa livre fora do contrato de conferência'
    schema = p.contrato_saida.response_format['json_schema']['schema']
    opcoes = schema['properties']['fala']['enum']
    assert opcoes == [f'Você contou: «{fonte}».', LIMITE_CONFERENCIA_RELATO_USUARIO]
    assert p.reserva_saida_tokens == 0
    for fala in opcoes:
        assert avaliar_nucleo_retomada_usuario(fala, plano=plano)['admissivel']
        assert p.contrato_saida.decodificar_json(json.dumps({'fala': fala, 'comandos': []}))['fala'] == fala
    for dados in ({'fala': ruim, 'comandos': []}, {'fala': boa, 'comandos': []},
                  {'fala': opcoes[0], 'comandos': [{'acao': 'OPEN_APP'}]},
                  {'fala': opcoes[0], 'comandos': [], 'semantica_verificada': True}):
        with pytest.raises(ValueError):
            p.contrato_saida.decodificar_json(json.dumps(dados))


@pytest.mark.parametrize('invalido', ['autor', 'hash', 'contestado', 'fala_atual', 'alegacao', 'aspas', 'quebra', 'longo'])
def test_fonte_sem_identidade_literal_historica_nao_e_oferecida(invalido):
    fonte, pedido, ruim, _ = CASOS[0]
    def alterar(plano):
        item = plano['relatos_usuario'][0]
        if invalido == 'autor': item['autor'] = 'laylay'
        elif invalido == 'hash': item['id'] = 'dialogo:usuario:1:' + '0' * 64
        elif invalido == 'contestado': item['status'] = 'contestado'
        elif invalido == 'fala_atual': item['origem'] = 'fala_atual'
        elif invalido == 'alegacao': item['id'] = 'alegacao:1'
        else:
            item['texto'] = {'aspas': 'eu disse «oi»', 'quebra': 'eu disse\noi', 'longo': 'a' * 500}[invalido]
            item['id'] = 'dialogo:usuario:1:' + hashlib.sha256(item['texto'].encode()).hexdigest()
    _, p = pacote(fonte, pedido, ruim, alterar=alterar)
    assert p.contrato_saida is not None, 'ausência de fonte não pode reabrir autoria livre'
    assert p.contrato_saida.response_format['json_schema']['schema']['properties']['fala']['enum'] == [LIMITE_CONFERENCIA_RELATO_USUARIO]


def test_fonte_valida_de_outra_categoria_nao_e_opcao_para_a_lacuna_perguntada():
    fonte, pedido, ruim, _ = CASOS[0]
    def alterar(plano):
        outra = copy.deepcopy(plano['relatos_usuario'][0])
        outra['texto'] = 'eu trabalho no hospital'
        outra['id'] = 'dialogo:usuario:9:' + hashlib.sha256(outra['texto'].encode()).hexdigest()
        plano['relatos_usuario'] += [outra, copy.deepcopy(outra)]
    plano, p = pacote(fonte, pedido, ruim, alterar=alterar)
    opcoes = p.contrato_saida.response_format['json_schema']['schema']['properties']['fala']['enum']
    assert opcoes == [f'Você contou: «{fonte}».', LIMITE_CONFERENCIA_RELATO_USUARIO]
    r = avaliar_nucleo_retomada_usuario('Você contou: «eu trabalho no hospital».', plano=plano)
    assert not r['admissivel'] and not r['semantica_verificada'] and not r['prova_implicacao']
    assert not r['autoriza_execucao'] and not r['pode_confirmar_fato_externo']


def test_feedback_proposto_nao_ativa_contrato_de_outro_turno():
    fonte, pedido, ruim, _ = CASOS[0]
    plano = plano_com_fonte(fonte, pedido, ruim)
    plano['comandos'] = [{'acao': 'OPEN_APP'}]
    p = montar_pacote_reparo_comunicacao(pedido, ruim,
        {'contrato_reparo': {'retomada_usuario': {'autoriza_execucao': False}}}, plano=plano)
    assert not p.contexto_fechado and p.contrato_saida is None


def test_codec_autoral_composto_conserva_escolhas_e_recusa_mescla_e_comandos():
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    fonte, pedido, ruim, _ = CASOS[0]
    _, p = pacote(fonte, pedido, ruim)
    codec = exigir_suporte_no_pacote_autoral(p).contrato_saida
    boa = f'Você contou: «{fonte}».'
    d = {'suporte_proposicoes': [{'texto': boa, 'fontes': []}], 'comandos': []}
    assert codec.decodificar_json(json.dumps(d))['fala'] == boa
    for textos, comandos in [([ruim], []), ([boa, LIMITE_CONFERENCIA_RELATO_USUARIO], []),
                              ([boa], [{'acao': 'OPEN_APP'}])]:
        with pytest.raises(ValueError):
            codec.decodificar_json(json.dumps({'suporte_proposicoes': [
                {'texto': t, 'fontes': []} for t in textos], 'comandos': comandos}))


@pytest.mark.parametrize('fonte', ['a' * 499, 'a' * 498, 'a ' * 248 + 'abc'])
def test_realizacoes_historicas_precisam_ser_representaveis_no_transporte_autoral(fonte):
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral, segmentar_realizacao_autoral
    _, p = pacote(fonte, CASOS[0][1], CASOS[0][2])
    opcoes = p.contrato_saida.response_format['json_schema']['schema']['properties']['fala']['enum']
    assert all(segmentar_realizacao_autoral(f) for f in opcoes), 'opção literal aceita pelo owner aborta codec composto'
    codec = exigir_suporte_no_pacote_autoral(p).contrato_saida
    assert codec.decodificar_json(json.dumps({'suporte_proposicoes': [
        {'texto': LIMITE_CONFERENCIA_RELATO_USUARIO, 'fontes': []}], 'comandos': []}))['fala'] == LIMITE_CONFERENCIA_RELATO_USUARIO
