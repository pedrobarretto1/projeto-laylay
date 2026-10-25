"""Uma fonte atual presente não vira alegação de contexto ausente."""
import pytest
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno,verificar_fala_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala


def plano_atual(texto):
    turno=classificar_modalidade_turno(texto)
    retrato,_=construir_retrato_turno(texto,turno=turno,mente={},contexto_perceptivo={})
    turno['referencia_resolvida']=retrato['referencia_resolvida']
    p=planejar_turno(texto,turno=turno)
    p['contrato_fala']=construir_contrato_semantico_fala(texto,turno=turno,plano=p)
    return p


@pytest.mark.parametrize('texto,candidata',[
    ('agora vamos falar de jogos: eu e o Leo estamos montando um jogo chamado Ponte de Papel',
     'O horário ficou às 16h. O jogo Ponte de Papel está sendo montado por você e o Leo.'),
    ('a minha parte é o desenho dos cenários e a dele é a música',
     'Você desenha os cenários e o Leo cria a música para o jogo Ponte de Papel.'),
])
def test_revisao_que_nao_confere_parafrase_preserva_relato_atribuido(texto,candidata):
    p=plano_atual(texto)
    p['fundamentacao_factual']={'tema':'Ponte de Papel','confiavel':False,'resumo':''}
    r=verificar_fala_turno(candidata,plano=p,origem='ia_final')
    assert r['fala']==f'Você contou: «{texto}».'
    assert r['aceita'] and r['conclusao']=='relato_usuario_atual_citado'
    assert r['autoriza_execucao'] is r['comprova_fato'] is False
    # A mesma realização é estável numa segunda revisão da entrega.
    assert verificar_fala_turno(r['fala'],plano=p,origem='ia_final')['fala']==r['fala']


def test_comando_ou_fonte_antiga_nao_ganha_realizacao_literal_de_conversa():
    for texto in ['abre o navegador','agora vou contar que estou lendo o livro chamado Duna']:
        p=plano_atual(texto)
        if not p['requer_execucao']:
            p['contrato_fala']['turno_id']='antigo'
        r=verificar_fala_turno(f'Você contou: «{texto}».',plano=p,origem='ia_final')
        assert r.get('conclusao')!='relato_usuario_atual_citado'
