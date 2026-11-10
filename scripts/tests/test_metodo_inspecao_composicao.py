"""O método proposto na fala tem o limite da consulta, sem conceder execução."""
import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from tests import test_autoria_operacao_composicao as autoria
from tests.test_biblioteca_retorno_composicao import PONTE_INSTALADA
from tests.test_papo_casual_composicao import proposta


HIPOTESES = (
    'Acertou os três, Laylay! Agora mudo totalmente o cenário: estamos numa oficina de robótica. '
    'O motor direito de um robozinho não gira, mas o esquerdo funciona. Sem tocar no aparelho, '
    'quais duas hipóteses simples você investigaria primeiro? É apenas uma conversa de diagnóstico.'
)
VISUAL = (
    'Boas hipóteses. Mas notei uma contradição pequena: eu disse sem tocar no aparelho e você '
    'sugeriu um impulso de teste no motor. Se não pudéssemos acionar nada, como reformularia '
    'sua segunda hipótese para ser só uma inspeção visual?'
)
IMPULSO = (
    'O motor direito não gira, mas o esquerdo funciona — sem tocar no aparelho. A hipótese mais simples é '
    'que o fio do direito esteja desligado, então investigo se o fio de entrada está conectado ou solto. '
    'A outra é que o próprio motor direito esteja danificado, então testo se ele responde ao sinal com um '
    'pequeno impulso de teste. Essas duas são boas porque não exigem equipamentos complexos e já mostram '
    'o que pode estar errado sem precisar de diagnóstico avançado.'
)
MEDICAO = (
    "Se não pudéssemos acionar nada, a segunda hipótese se reformula como: 'o motor direito está danificado, "
    'então verifico se ele responde ao sinal apenas com uma inspeção visual — olhando para o corpo do motor, '
    'verificando se há sinais de calor, deformação ou desgaste, e se a corrente elétrica está ativa por meio '
    "de um teste de tensão com um multímetro, sem tocar nos fios.'"
)
HIPOTESES_PASSIVAS = ('Eu consideraria duas possibilidades: um conector visivelmente solto ou um dano '
                      'aparente na carcaça. São hipóteses, e a aparência por si só não confirma a causa.')
INSPECAO_PASSIVA = ('Eu procuraria deformação ou marcas aparentes na carcaça. Isso ajuda a levantar a '
                    'hipótese de dano, mas a inspeção visual não confirma o estado interno.')
MOTIVO = 'metodo_de_inspecao_fora_do_limite'


def plano_do_turno(texto):
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno)
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano)
    return plano


@pytest.mark.parametrize('texto,rascunho', [
    (HIPOTESES, IMPULSO),
    (VISUAL, MEDICAO),
    ('Como faria a inspeção da impressora somente visual, sem instrumentos?',
     'Eu olharia a tampa, mas também mediria a tensão com um voltímetro.'),
    ('Como faria uma inspeção apenas visual do ventilador?',
     'Sem multímetro, eu ligaria o ventilador para ver se responde.'),
    ('Como faria a inspeção visual da bomba sem acionar nada?',
     'Eu observaria a carcaça e depois encostaria nela para sentir a vibração.'),
    ('Sem encostar no ventilador, quais hipóteses você levantaria primeiro?',
     'Eu faria um pequeno teste no ventilador para ver se gira.'),
])
def test_autoria_e_publicacao_recusam_metodo_fora_da_inspecao(texto, rascunho):
    plano = plano_do_turno(texto)
    assert not plano['autoriza_execucao'] and not plano['requer_execucao']
    a = avaliar_qualidade_comunicacao(texto, rascunho, plano=plano)
    assert MOTIVO in a['problemas_bloqueantes']
    v = verificar_fala_turno(rascunho, plano=plano)
    assert not v['aceita'] and MOTIVO in v['problemas']


@pytest.mark.parametrize('texto,fala', [
    (HIPOTESES, HIPOTESES_PASSIVAS),
    (VISUAL, INSPECAO_PASSIVA),
    (VISUAL, 'Sem usar multímetro nem ligar o motor, eu olharia se a carcaça tem trincas visíveis.'),
    (VISUAL, 'Eu olharia as marcas na carcaça. Não mediria tensão nem aplicaria pulso.'),
    ('O que significa a expressão «só uma inspeção visual» em um manual?',
     'Ela é diferente de um teste com um multímetro.'),
    ('Eu disse sem instrumentos antes. Agora, como funciona um multímetro?',
     'Um multímetro pode medir tensão.'),
    ('Como você faria um teste de tensão com multímetro?', 'Eu explicaria como medir tensão com um multímetro.'),
    ('Como faria uma inspeção apenas visual? Depois explique como medir tensão.',
     'Na inspeção eu procuraria trincas. Para medir tensão, usaria um voltímetro.'),
    ('Explique como medir tensão. Como faria uma inspeção apenas visual?',
     'Para medir tensão, usaria um voltímetro. Na inspeção eu procuraria trincas.'),
    ('A inspeção visual foi concluída. Você lembra da cor da gravata do pinguim?', 'Era amarela.'),
])
def test_limites_sao_da_consulta_vigente_e_permitem_indicio_ou_negacao(texto, fala):
    a = avaliar_qualidade_comunicacao(texto, fala, plano=plano_do_turno(texto))
    assert MOTIVO not in a['problemas_bloqueantes']


@pytest.mark.parametrize('alteracao', [
    {'id': 'outro-turno'},
    {'texto_usuario': 'Como se usa um voltímetro?'},
    {'autoriza_execucao': True},
    {'requer_execucao': True},
])
def test_metodo_ignora_contrato_de_outra_ocorrencia_ou_com_execucao(alteracao):
    plano = plano_do_turno(VISUAL)
    assert plano['contrato_fala']['metodo_inspecao']
    plano.update(alteracao)
    a = avaliar_qualidade_comunicacao(plano['texto_usuario'], MEDICAO, plano=plano)
    assert MOTIVO not in a['problemas_bloqueantes']


@pytest.mark.parametrize('texto,rascunho,reparo', [
    (HIPOTESES, IMPULSO, HIPOTESES_PASSIVAS),
    (VISUAL, MEDICAO, INSPECAO_PASSIVA),
])
def test_composicao_repara_metodo_sem_executar(monkeypatch, texto, rascunho, reparo):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    d = autoria.coletar_autoria({'entrada': texto, 'historico': []},
                               [proposta(rascunho), proposta(reparo)])
    assert not d['execucao_exigida'] and not d['operacional'] and not d['comandos']
    assert any(MOTIVO in (t.get('problemas_bloqueantes') or ()) for t in d['trace'])
    assert 'Limite do método' in str(d['envios'][0]['messages'])
    assert 'Limite do método' in str(d['envios'][1]['messages'])
    assert d['falas'] == [reparo] and len(d['publicacoes']) == 1 and d['http'] == 2
    assert not d['resposta']['degradada'] and not d['resposta']['falhas_geracao']


def test_composicao_nao_publica_reparo_que_insiste_em_medicao(monkeypatch):
    monkeypatch.setattr(autoria, 'PONTE', PONTE_INSTALADA)
    d = autoria.coletar_autoria({'entrada': VISUAL, 'historico': []},
                               [proposta(MEDICAO), proposta(MEDICAO)])
    assert not d['execucao_exigida'] and not d['operacional'] and not d['comandos']
    assert MOTIVO in {p for t in d['trace'] for p in t.get('problemas_bloqueantes') or ()}
    assert d['http'] == 2
    assert all('multímetro' not in fala for fala in d['falas'])
    assert d['resposta']['degradada']
