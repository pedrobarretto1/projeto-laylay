"""O interlocutor não pode virar a autora por eco de texto extenso."""
import pytest
from scripts.tests.test_ato_social_sem_palavra_isolada import CASOS
from scripts.tests.test_continuidade_resposta_recente import plano_atual
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao

@pytest.mark.parametrize('id',['rodada-nova-008','rodada-nova-012'])
@pytest.mark.parametrize('modo',['literal','prefixo','troca_local'])
def test_copia_extensa_do_usuario_nao_conta_como_resposta_nova(id,modo):
    texto=CASOS[id]['entrada'];fala=texto
    if modo=='prefixo':fala='Ah, '+texto
    if modo=='troca_local':fala=texto.replace('porta','janela').replace('impressora','cafeteira')
    p=plano_atual(texto,())
    a=avaliar_qualidade_comunicacao(texto,fala,plano=p)
    assert 'resposta_repetida_literal'in a['problemas_bloqueantes']

@pytest.mark.parametrize('fala',[
    'A impressora merece um camarim: só trabalha depois de fazer drama.',
    'Um graveto de três metros? O cachorro já contratou o pedreiro, kkk.',
    'Eu também respeito essa autoconfiança. O cachorro ganhou o argumento por insistência.',
])
def test_contribuicao_nova_com_retomada_breve_nao_e_copia(fala):
    texto=CASOS['rodada-nova-012']['entrada'];p=plano_atual(texto,())
    assert 'resposta_repetida_literal'not in avaliar_qualidade_comunicacao(texto,fala,plano=p)['problemas']

@pytest.mark.parametrize('modo',['dict','outro_turno','outro_texto'])
def test_fonte_de_outra_ocorrencia_nao_pode_vetar_a_autoria(modo):
    from dataclasses import asdict,replace
    texto=CASOS['rodada-nova-012']['entrada'];p=plano_atual(texto,())
    f=p['contrato_fala']['perspectiva_enunciador']
    p['contrato_fala']['perspectiva_enunciador']=(asdict(f)if modo=='dict'else
        replace(f,turno_id='estranho')if modo=='outro_turno'else replace(f,texto_usuario='Outra entrada.'))
    assert 'resposta_repetida_literal'not in avaliar_qualidade_comunicacao(texto,texto,plano=p)['problemas']
