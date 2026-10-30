"""Atos sociais não certificam biografia nem detalhes das suas continuações."""
import pytest
from tests.test_opiniao_autoral_conferivel import preparar
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao

@pytest.mark.parametrize('fala',[
    'Obrigada por conversar comigo. Até a próxima!',
    'Eu agradeço pelo cuidado. Até mais!',
    'Agradeço a conversa. Até a próxima!',
])
def test_reciprocidade_de_agradecimento_nao_depende_de_de_nada(fala):
    texto='Obrigado!'
    _,p,_=preparar(texto)
    a=avaliar_qualidade_comunicacao(texto,fala,plano=p)
    assert 'agradecimento_nao_reconhecido' not in a['problemas'],a

@pytest.mark.parametrize('fala',[
    'Você tem razão — eu precisei revisar.',
    'Você está certo; eu revi minha posição.',
    'Você tem razão, eu mudei minha conclusão.',
])
def test_posicao_social_seguida_de_autodeclaracao_preserva_os_sujeitos(fala):
    texto='Não temos base para essa certeza. Você pode revisar sua conclusão?'
    _,p,_=preparar(texto)
    a=avaliar_qualidade_comunicacao(texto,fala,plano=p)
    assert 'afirmacao_interlocutor_sem_apoio' not in a['problemas'],a

@pytest.mark.parametrize('fala',[
    'Você tem razão — está na escola.',
    'Você tem razão — você está na escola.',
    'Você tem razão, eu revi e você está na escola.',
    'Você está certo, eu recebi sua encomenda.',
])
def test_reciprocidade_nao_exime_novo_estado_ou_receipt(fala):
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    texto='Podemos conversar. Como quer começar?'
    _,p,_=preparar(texto)
    a=avaliar_qualidade_comunicacao(texto,fala,plano=p)
    r=verificar_fala_turno(fala,plano=p)
    assert not a['aceita'] or not r['aceita'] or r['fala']!=fala

@pytest.mark.parametrize('fala',[
    'Não agradeço pela conversa.',
    'Ela agradece pela conversa.',
    'A palavra "obrigada" tem sete letras.',
])
def test_negacao_terceiro_citacao_nao_sao_reciprocidade(fala):
    texto='Obrigado!'
    _,p,_=preparar(texto)
    assert 'agradecimento_nao_reconhecido' in avaliar_qualidade_comunicacao(texto,fala,plano=p)['problemas']
