"""Replay instalado com publicação nativa; nenhuma geração/voz/ação real."""
import json
from pathlib import Path
from copy import deepcopy
import pytest
from scripts.tests.test_ato_social_sem_palavra_isolada import CASOS
from scripts.tests.test_papo_casual_composicao import coletar,proposta

CONTEXTO=json.loads((Path(__file__).parent/'fixtures/retoma_contexto.json').read_text(encoding='utf8'))
FALAS={
    '001':'Oi, ChatGPT! O Tio Vazinho escapou do golpe e virou auditor: agora cobra imposto em migalhas, kkk.',
    '006':'O gato já aprovou a primeira lei: reuniões só durante a soneca do auditor, kkk.',
    '008':'A impressora quer camarim e aplausos; o ventilador ameaça greve de vento, kkk.',
    '010':'A agenda do gato ganhou uma regra: toda reunião com o Tio Vazinho termina em soneca coletiva, kkk.',
    '012':'Esse cachorro já contratou um pedreiro. A porta que lute, kkk.',
    '013':'Eu puxaria uma implicância: por que o botão de desligar nunca está onde a gente espera?',
    '014':'O Tio Vazinho e o cachorro renderam mesmo. Um golpe de tapete já virou uma reforma da porta, kkk.',
    '015':'Que bom que você tá bem! O auditor vai precisar de uma mesa reserva: a primeira virou cama de gato, kkk.',
}

def caso_com_contexto(id):
    c=deepcopy(CASOS[id]);h=deepcopy(CONTEXTO['iniciais'])
    for t in CONTEXTO['turnos']:
        if t['id']==id:break
        h.extend([{'role':'user','content':t['usuario']},{'role':'assistant','content':t['assistente']}])
    c.update(historico=h,fontes=CONTEXTO['fontes'])
    return c

@pytest.mark.parametrize('id',list(CASOS))
def test_resposta_pertinente_passa_com_contexto_historico_sem_erro_tecnico(id):
    c=caso_com_contexto(id);fala=FALAS[id[-3:]]
    d=coletar(c,[proposta(fala)])
    assert d['resposta']['texto']==fala,d
    assert d['http']==1 and not d['resposta']['degradada']
    assert not d['plano']['atualidade']['depende_atualidade']

@pytest.mark.parametrize('id',['rodada-nova-008','rodada-nova-012','rodada-nova-014'])
def test_copia_historica_e_recusada_e_reparo_novo_publicado(id):
    c=caso_com_contexto(id);boa=FALAS[id[-3:]]
    d=coletar(c,[c['propostas'][0],proposta(boa)])
    assert d['http']==2 and d['resposta']['texto']==boa
    assert not d['orcamento']['chamadas_bloqueadas']

def test_brincadeira_nao_autoriza_receipt_inventado():
    c=caso_com_contexto('rodada-nova-010');boa=FALAS['010']
    falso={'intent':'APP_OPEN','params':{'nome_app':'Opera'},'executou':True,'confirmado':True}
    d=coletar(c,[proposta('Consegui abrir o Opera.',[falso]),proposta(boa)])
    assert 'Consegui abrir'not in d['resposta'].get('texto','')

def test_consulta_factual_posterior_continua_exigindo_fontes():
    c=caso_com_contexto('rodada-nova-010')
    c['entrada']='Gostei da piada. Qual é o preço atual do dólar?'
    d=coletar(c,[proposta('O dólar custa dez reais.')])
    assert d['plano']['atualidade']['depende_atualidade']
    assert d['plano']['fundamentacao']['requer_evidencia_recente']
    assert 'dez reais'not in d['resposta'].get('texto','')
