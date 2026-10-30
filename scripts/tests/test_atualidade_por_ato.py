"""Uma pergunta em outro ato não torna todo o turno uma consulta atual."""
import json
from pathlib import Path
import pytest
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual

CASOS=json.loads((Path(__file__).parent/'fixtures/papo_casual.json').read_text(encoding='utf8'))
DESPEDIDA=next(c['entrada']for c in CASOS if c['id']=='papo-015')

@pytest.mark.parametrize('texto',[
    DESPEDIDA,
    next(c['entrada']for c in CASOS if c['id']=='papo-005'),
    next(c['entrada']for c in CASOS if c['id']=='papo-009'),
    'Você perguntou o que quero fazer agora?',
    'Você disse quem é o presidente atual?',
    'Não pedi para fazer nada no PC.',
    'Eu só mencionei o Xbox. Você acha engraçado?',
    'O tapete vai ser prefeito na nossa história. Gostou da brincadeira?',
    'O personagem era presidente de um reino de papel. Você acha engraçado?',
    'Falei da versão do personagem. Gostou do nome?',
    'Hoje vou descansar. Quem inventaria um mascote de meia?',
    'Qual seria um título divertido para a nossa conversa de hoje?',
    'Que nome você daria à nossa história de hoje?',
    'Como você chamaria esta conversa de hoje?',
    'Qual título você escolheria para essa história de hoje?',
    'Vamos fazer uma última brincadeira para encerrar bem: qual seria um título divertido para a nossa conversa de hoje?',
    'Vamos fechar por hoje: como você chamaria esta história de hoje?',
])
def test_dominio_e_interrogacao_em_atos_distintos_nao_exigem_atualizacao(texto):
    turno=classificar_modalidade_turno(texto)
    assert not classificar_atualidade_factual(texto,turno=turno)['depende_atualidade']

@pytest.mark.parametrize('texto',[
    'Gostei da história. Quem é o presidente atual do Brasil?',
    'Boa noite. Qual é a versão atual do Python?',
    'Já vou dormir. Como está o clima agora?',
    'O tapete fictício é prefeito. O navegador ainda está aberto?',
    'Foi uma ótima história. O jogo vai sair só para PS5?',
    'O GTA 6 não vai ter versão para PS4.',
    'A atualização é exclusiva do PC.',
    'A versão atual é a mesma que você disse?',
    'O presidente atual do Brasil é Fulano, certo?',
    'O preço é cem reais, confere?',
    'O clima está quente hoje, né?',
    'O preço é cem reais, não é?',
    'O preço atual é cem reais, é isso mesmo?',
    'O preço é cem reais, não é verdade?',
    'Qual é o título do filme lançado hoje?',
    'Na nossa conversa, quem é o presidente atual do Brasil?',
    'Qual seria um título com o preço atual do dólar?',
    'O que saiu hoje?',
])
def test_consulta_atual_independente_continua_exigindo_evidencia(texto):
    turno=classificar_modalidade_turno(texto)
    assert classificar_atualidade_factual(texto,turno=turno)['depende_atualidade']


def test_lookup_fonte_tem_limite_proprio_sem_ampliar_contrato_de_oito_atos():
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
    t=classificar_modalidade_turno(DESPEDIDA)
    assert len(t['segmentos'])>8
    assert not fontes_textuais_dos_segmentos(DESPEDIDA,t['segmentos'])
    fontes=fontes_textuais_dos_segmentos(DESPEDIDA,t['segmentos'],limite_segmentos=32)
    assert len(fontes)==len(t['segmentos'])
    for f in fontes:
        d=f.como_dict();a,b=d['intervalo']
        assert DESPEDIDA[a:b]==d['texto_original']
        assert d['autoriza_execucao'] is d['comprova_efeito'] is False


def test_segmentacao_adulterada_nao_pode_dispensar_fonte_atual():
    from copy import deepcopy
    t=classificar_modalidade_turno(DESPEDIDA)
    t=deepcopy(t);t['segmentos'][4]['texto_estrutural']='outra conversa'
    assert classificar_atualidade_factual(DESPEDIDA,turno=t)['depende_atualidade']


def test_fonte_integral_do_ato_e_reutilizada_sem_adivinhar_cauda_truncada():
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
    texto=next(c['entrada']for c in CASOS if c['id']=='papo-009')
    t=classificar_modalidade_turno(texto)
    assert not fontes_textuais_dos_segmentos(texto,t['segmentos'])
    fs=fontes_textuais_dos_segmentos(texto,t['segmentos'],limite_segmentos=32,limite_trecho=4000)
    assert len(fs)==len(t['segmentos'])
    assert fs[-1].como_dict()['texto_original'].endswith('KKKKK.')
