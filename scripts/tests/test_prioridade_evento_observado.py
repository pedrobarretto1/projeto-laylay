"""Evento em composição não toma posse da prioridade da fala humana."""
from types import SimpleNamespace
import pytest
from mente_laylay.integracao.ponte_iniciativa_aplicacao import PonteIniciativaAplicacaoRuntime


def montar(mental,conversa=None,claim=None):
    return PonteIniciativaAplicacaoRuntime(estado_mental_getter=lambda:mental,
        percepcao_getter=lambda _k,p=None:p,conversa_getter=lambda k,p=None:(conversa or {}).get(k,p),
        modo_jogo=SimpleNamespace(ativo=False),visao_leitura_getter=lambda:None,
        identificar_jogo=lambda _: {},salvar_memoria=lambda:None,falar=lambda *_:None,
        env_getter=lambda _k,p:p,prioridade_interacao_getter=claim or (lambda:False))


def estado_evento():
    return {'turno_atual':{'id':'e1','natureza_entrada':'evento','autoriza_execucao':False},
        'plano_turno_atual':{'id':'e1','fase':'planejado','natureza_entrada':'evento',
                           'autoriza_execucao':False}}


@pytest.mark.parametrize('origem',['experiencia_corporal','observador_janelas'])
def test_evento_canonico_nao_vira_turno_humano_ativo(origem):
    mental=estado_evento()
    mental['turno_atual']['origem']=origem
    ponte=montar(mental)
    assert ponte.turno_em_andamento() is False, 'o evento impede a própria geração como se fosse fala de Pedro'
    assert ponte.contexto()['turno_ativo'] is False


@pytest.mark.parametrize('fase',['planejado','resposta_planejada'])
@pytest.mark.parametrize('natureza',[None,'usuario'])
def test_turno_humano_ou_legado_mantem_prioridade(fase,natureza):
    mental={'turno_atual':{'id':'u1'},'plano_turno_atual':{'id':'u1','fase':fase}}
    if natureza:mental['plano_turno_atual']['natureza_entrada']=natureza
    assert montar(mental).turno_em_andamento()


@pytest.mark.parametrize('invalido',['id','autoridade_turno','autoridade_plano','natureza_turno'])
def test_isencao_de_prioridade_nao_aceita_evento_incoerente(invalido):
    mental=estado_evento()
    if invalido=='id':mental['turno_atual']['id']='outro'
    elif invalido=='autoridade_turno':mental['turno_atual']['autoriza_execucao']=True
    elif invalido=='autoridade_plano':mental['plano_turno_atual']['autoriza_execucao']=True
    else:mental['turno_atual']['natureza_entrada']='usuario'
    assert montar(mental).turno_em_andamento()


def test_composicao_instalada_nao_autobloqueia_corpo_e_preserva_claim_humano(tmp_path,monkeypatch):
    from scripts.tests.test_corpo_motor import _root_instalado
    root,_,_=_root_instalado(monkeypatch,tmp_path)
    evento=root._diretor_presenca_runtime._evento_cognitivo({
        'origem':'experiencia_corporal','conteudo':'Meu corpo esteve inclinado.',
        'evidencias':['Meu corpo esteve inclinado.'],
        'observacao_corporal':{'fase_manuseio':'DESCONFIADA','autoriza_execucao':False}},
        dominio='corpo',categoria='companhia',chave='ensaio',agora=1000)
    turno=root._composicao_turno_runtime.iniciar(evento,origem='presenca')
    try:
        assert turno['publicacao_evento_confirmada'] and turno['contrato_fala']['observacao_corporal']
        cliente=root._composicao_inteligencia_externa_runtime._transporte
        assert not cliente.interacao_ativa(), 'primeira fronteira: callback real bloqueou o evento que acabou de publicar'
        claim=root._prioridade_interacao_usuario_runtime.adquirir('usuario_no_meio_do_evento')
        try:assert cliente.interacao_ativa()
        finally:root._prioridade_interacao_usuario_runtime.liberar(claim)
    finally:root._composicao_turno_runtime.concluir_evento(turno,resultado='teste_sem_fala')
