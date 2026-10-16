"""Canal de conversa aberto não equivale a turno ativo em nenhum domínio."""
import pytest
from scripts.tests.test_motor_iniciativa import _motor


@pytest.mark.parametrize('dominio',['corpo','rotina'])
def test_observacao_real_pode_ser_considerada_apos_conversa_ociosa(dominio):
    r,_=_motor(contexto={'modo_chat':True,'conversa_ativa':True,'ultima_entrada_ts':900.0},agora=1000)
    r.ativar_perfil_seguro_padrao()
    d=r.registrar({'chave':f'observacao:{dominio}','tipo':'presenca_contexto_util',
        'dominio':dominio,'origem':'experiencia_corporal' if dominio=='corpo' else 'observador_janelas',
        'utilidade':80,'confianca':.94,'risco':'baixo','executavel':False})
    assert d['decisao']=='sugerir',d
    assert 'conversa_ativa' not in d['motivos']


@pytest.mark.parametrize('campo,valor',[('turno_ativo',True),('interacao_usuario_ativa',True),
    ('usuario_falando',True),('is_speaking',True),('ultima_entrada_ts',995.0)])
def test_atividade_real_continua_tendo_prioridade(campo,valor):
    r,_=_motor(contexto={'modo_chat':True,'ultima_entrada_ts':900.0,campo:valor},agora=1000)
    r.ativar_perfil_seguro_padrao()
    d=r.registrar({'chave':'corpo:evento','tipo':'presenca_contexto_util','dominio':'corpo',
        'origem':'experiencia_corporal','utilidade':80,'confianca':.94,'risco':'baixo','executavel':False})
    assert d['decisao']!='sugerir',d
