"""Relato atribuído tem fonte pessoal; não confirma características do mundo."""
import pytest
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.memoria_mental.registro_semantico import registrar_interacao_semantica


def verificar(fonte,fala,*,autor='usuario',status=None):
    registro=registrar_interacao_semantica({},texto_usuario=fonte,agora=100)
    for a in registro.get('alegacoes')or[]:
        a['autor']=autor
        if status:a['status']=status
    pergunta='e qual banda eu falei que gosto, lá no começo?'
    plano=planejar_turno(pergunta,turno=classificar_modalidade_turno(pergunta),mente={'registro_semantico':registro})
    return verificar_fala_turno(fala,plano=plano),plano


@pytest.mark.parametrize('fonte,fala',[
    ('pra descansar eu gosto de rock, principalmente Nirvana',
     'Lá no começo, você falou que gostava de rock, especialmente Nirvana.'),
    ('eu gosto de jazz','Você disse que gostava de jazz.'),
    ('eu prefiro música instrumental','Você contou que preferia música instrumental.'),
])
def test_retoma_preferencia_com_relacao_e_valores_da_fonte(fonte,fala):
    r,p=verificar(fonte,fala)
    assert r['fala']==fala,'relato pessoal com fonte foi trocado por desconhecimento factual'


@pytest.mark.parametrize('fonte,fala,autor,status',[
    ('eu gosto de rock','Você disse que gostava de jazz.','usuario',None),
    ('eu gosto de rock','Você disse que adorava rock.','usuario',None),
    ('eu gosto de rock, principalmente Nirvana','Você disse que gostava de rock, especialmente Metallica.','usuario',None),
    ('eu gosto de rock','Você disse que gostava de rock.','laylay',None),
    ('eu gosto de rock','Você disse que gostava de rock.','usuario','contestado'),
    ('se estiver cansado, eu gosto de rock','Você disse que gostava de rock.','usuario',None),
    ('eu não gosto de rock','Você disse que gostava de rock.','usuario',None),
    ('eu gosto de rock','Você disse que gostava de rock porque é comprovadamente o melhor estilo.','usuario',None),
])
def test_nao_toma_proposta_da_ia_ou_troca_de_predicado_por_prova(fonte,fala,autor,status):
    r,p=verificar(fonte,fala,autor=autor,status=status)
    assert r['fala']!=fala


def test_fonte_pessoal_nao_certifica_fato_externo_adicionado():
    fala='Você disse que gostava de rock. Nirvana ganhou cinco prêmios em 1997.'
    r,p=verificar('eu gosto de rock',fala)
    assert 'ganhou cinco' not in r['fala']
    assert 'data_sem_evidencia' in r['problemas']


def test_relato_passado_na_fonte_nao_vira_preferencia_presente():
    from mente_laylay.cognicao.fundamentacao_factual import conferir_relato_preferencia_usuario
    fonte={'id':'alegacao:100','autor':'usuario','status':'relatado_pelo_usuario',
        'texto':'eu gostava de rock'}
    assert conferir_relato_preferencia_usuario('Você disse que gosta de rock.',[fonte]) is None


def test_relato_nao_transfere_preferencia_para_primeira_pessoa_da_ia():
    from mente_laylay.cognicao.fundamentacao_factual import conferir_relato_preferencia_usuario
    fonte={'id':'alegacao:100','autor':'usuario','status':'relatado_pelo_usuario','texto':'eu gosto de rock'}
    assert conferir_relato_preferencia_usuario('Você disse que gosto de rock.',[fonte]) is None


@pytest.mark.parametrize('segunda',['adoro jazz','prefiro jazz','quero ouvir jazz'])
def test_coordenacao_nao_vira_valor_nominal_opaco(segunda):
    from mente_laylay.cognicao.fundamentacao_factual import conferir_relato_preferencia_usuario
    fonte={'id':'alegacao:100','autor':'usuario','status':'relatado_pelo_usuario',
        'texto':'eu gosto de rock e '+segunda}
    assert conferir_relato_preferencia_usuario('Você disse que gostava de rock e '+segunda+'.',[fonte]) is None


def test_fonte_literal_do_dialogo_nao_e_substituida_pela_normalizacao_semantica():
    fonte='pra descansar eu gosto de rock, principalmente Nirvana'
    registro=registrar_interacao_semantica({},texto_usuario='pra descansar eu gosto de rock principalmente nirvana',agora=100)
    pergunta='e qual banda eu falei que gosto, lá no começo?'
    plano=planejar_turno(pergunta,turno=classificar_modalidade_turno(pergunta),mente={
        'registro_semantico':registro,'messages':[{'role':'user','content':fonte}]})
    fala='Lá no começo você falou que gosta de rock, principalmente Nirvana.'
    r=verificar_fala_turno(fala,plano=plano)
    assert r['fala']==fala


@pytest.mark.parametrize('fala',['Você disse no início que gostava de rock.',
    'Você falou lá no começo que gostava de rock.'])
def test_adjuntos_temporais_do_relato_nao_trocam_a_relacao(fala):
    r,_=verificar('eu gosto de rock',fala)
    assert r['fala']==fala


@pytest.mark.parametrize('status',['contestado','corrigido'])
def test_historia_literal_nao_reabilita_alegacao_revisada(status):
    fonte='eu gosto de rock'
    registro=registrar_interacao_semantica({},texto_usuario=fonte,agora=100)
    for a in registro['alegacoes']:a['status']=status
    t='qual banda eu falei que gosto?'
    plano=planejar_turno(t,turno=classificar_modalidade_turno(t),mente={
        'registro_semantico':registro,'messages':[{'role':'user','content':fonte}]})
    fala='Você disse que gostava de rock.'
    assert verificar_fala_turno(fala,plano=plano)['fala']!=fala
