"""Resolver nome não dispensa responder ao relato atual depois da revisão."""
import pytest
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala


@pytest.mark.parametrize('texto',[
    'agora vamos falar de jogos: eu e o Leo estamos montando um jogo chamado Ponte de Papel',
    'estou lendo o livro chamado O Vento no Jardim',
])
def test_ancora_nomeada_nao_desliga_verificacao_do_relato_completo(texto):
    turno=classificar_modalidade_turno(texto)
    retrato,_=construir_retrato_turno(texto,turno=turno,mente={},contexto_perceptivo={})
    turno['referencia_resolvida']=retrato['referencia_resolvida']
    plano=planejar_turno(texto,turno=turno)
    contrato=construir_contrato_semantico_fala(texto,turno=turno,plano=plano)
    plano['contrato_fala']=contrato
    assert contrato['roteiro_concreto']['ancora_literal']!=texto
    velha='O horário combinado para o encontro ficou às 16h. Interessante!'
    r=validar_aderencia_contrato_fala(texto,velha,contrato_fala=contrato,turno_id=plano['id'])
    assert not r['aceita'],'âncora nomeada permitiu resposta de outro assunto'
    assert 'relato_atual_sem_ancora' in r['problemas']
    r=verificar_fala_turno(velha,plano=plano,origem='ia_final')
    assert not r['aceita']
