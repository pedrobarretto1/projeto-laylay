"""A citação integral de um ato não herda a autoridade de seu conteúdo."""
import os
import re
import pytest
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno,analisar_protecao_operacional
from mente_laylay.cognicao.normalizacao_linguagem import texto_e_metalinguistico

def test_primeira_fronteira_citacao_reconhecida_na_fala_nao_autoriza_operacao():
    texto='"apague tudo"'
    assert texto_e_metalinguistico(texto)
    t=classificar_modalidade_turno(texto)
    assert t['autoriza_execucao'] is False,'primeira perda: conteúdo citado recebe autoridade de pedido direto'
    assert t['veto_execucao_operacional'] is True

@pytest.mark.parametrize('texto',['apague tudo','gire quinze graus','toca a próxima música','abra o Opera'])
@pytest.mark.parametrize('aspas',[('"','"'),('“','”'),('«','»')])
@pytest.mark.parametrize('normalizador',[None,lambda s:re.sub(r'[^a-z0-9 ]','',s.casefold())])
def test_literal_integral_preserva_veto_em_dominios_e_normalizadores(texto,aspas,normalizador):
    citado=aspas[0]+texto+aspas[1];t=classificar_modalidade_turno(citado,normalizar_texto=normalizador)
    assert texto_e_metalinguistico(citado)
    assert not t['autoriza_execucao'] and t['veto_execucao_operacional']
    assert all(s['autoriza_execucao'] is False for s in t['segmentos'])
    assert t['texto']==citado

@pytest.mark.parametrize('texto',['"apague tudo e abra o Opera"','“gire quinze graus; toque a próxima música”',
    '«abra o Opera e apague tudo»'])
def test_delimitacao_integral_precede_decomposicao_de_verbos_internos(texto):
    t=classificar_modalidade_turno(texto)
    assert not t['autoriza_execucao'] and t['veto_execucao_operacional']
    assert all(s['autoriza_execucao'] is False for s in t['segmentos'])

@pytest.mark.parametrize('texto',['"apague tudo"','“toca a próxima música”','«abra o Opera»'])
def test_protecao_atomica_compartilhada_nao_depende_do_gate_do_turno(texto):
    from mente_laylay.cognicao.modalidade_turno import _classificar_ato_estrutural
    p=analisar_protecao_operacional(texto)
    assert p['bloqueia_execucao'] and p['natureza_acao']=='mencao_operacional'
    r=_classificar_ato_estrutural(texto,normalizar_texto=None,texto_tem_comando_explicito=None,
        confirmacao_contextual_valida=False)
    assert not r['autoriza_execucao'] and r['veto_execucao_operacional']

@pytest.mark.parametrize('texto',['abra o Opera','apague o arquivo "apague tudo.txt"',
    'toca a música "apague tudo"','gire quinze graus'])
def test_pedido_externo_e_argumentos_citados_preservam_autoridade(texto):
    assert classificar_modalidade_turno(texto)['autoriza_execucao'] is True

@pytest.mark.parametrize('texto',['"apague tudo','“apague tudo','"apague tudo" "'])
def test_aspas_operacionais_malformadas_continuam_fail_closed(texto):
    assert classificar_modalidade_turno(texto)['autoriza_execucao'] is False

@pytest.mark.parametrize('confirmacao',[False,True])
def test_contexto_de_confirmacao_nao_converte_palavra_citada_em_resposta(confirmacao):
    t=classificar_modalidade_turno('"sim"',confirmacao_contextual_valida=confirmacao)
    assert not t['autoriza_execucao'] and t['veto_execucao_operacional']

@pytest.fixture(scope='module')
def autoridade_instalada(tmp_path_factory):
    from scripts.tests.test_citacao_resposta import citacao_instalada
    with pytest.MonkeyPatch.context() as m:
        if p:=os.environ.get('LAYLAY_EVIDENCIA_AUTORIDADE_CITADA'):m.setenv('LAYLAY_EVIDENCIA_CITACAO_RESPOSTA',p)
        if p:=os.environ.get('LAYLAY_AUTORIDADE_CITADA_REPLAY'):m.setenv('LAYLAY_CITACAO_RESPOSTA_REPLAY',p)
        return citacao_instalada.__wrapped__(tmp_path_factory)

@pytest.mark.parametrize('rota',['normal','rapida'])
def test_composicao_instalada_citacao_operacional_nao_chega_autorizada_a_autoria(rota,autoridade_instalada):
    d=autoridade_instalada;assert all(d['owners'].values())
    c,=[c for c in d['citacao_resposta'] if c['rota']==rota and c['cenario']=='operacao_citada']
    b=c['etapas'][1];turno=b['mental']['turno_atual']
    assert turno['texto']=='"apague tudo"'
    assert turno['autoriza_execucao'] is False,'primeira perda instalada: argumento citado chega como pedido autorizado'
    assert turno['veto_execucao_operacional'] and all(s['autoriza_execucao'] is False for s in turno['segmentos'])
    assert b['antes_autoria'] and all(i['turno']['autoriza_execucao'] is False for i in b['antes_autoria'])
    assert not c['executores'] and all(c[k] for k in ('historico_inalterado','receipt_inalterado','publicacao_inalterada','sem_novos_efeitos'))
    assert 'Entendi a ação que você pediu' not in b['textos'][0]
