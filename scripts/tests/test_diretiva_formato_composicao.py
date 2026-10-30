"""Composição instalada: diretiva da fala, sem voz ou execução real."""
import pytest
from tests.test_diretiva_formato_resposta import HISTORICA
from tests.test_resultado_perifrastico_composicao import coletar, proposta

CASOS = [
    (HISTORICA, 'Reconhecer capacidades reais não exige fingir humanidade.'),
    ('Como você definiria respeito? Responda em duas frases.',
     'Eu relaciono respeito à disposição de ouvir e rever uma posição.'),
    ('Qual é sua posição sobre discordar? Responda brevemente.',
     'Prefiro discordar com cuidado e continuar aberta a rever minha posição.'),
    ('Como você definiria respeito? Responda em poucas frases, sem metáforas.',
     'Eu relaciono respeito à disposição de ouvir e rever uma posição.'),
    ('Como você definiria respeito? Responda de forma breve e objetiva.',
     'Eu relaciono respeito à disposição de ouvir e rever uma posição.'),
    ('Como você definiria respeito? Responda em poucas frases no chat, sem metáforas.',
     'Eu relaciono respeito à disposição de ouvir e rever uma posição.'),
]


@pytest.mark.parametrize('pedido,fala', CASOS)
def test_pedido_de_forma_publica_resposta_sem_exigir_receipt(tmp_path,pedido,fala):
    d = coletar(tmp_path,{'entrada':pedido,'propostas':[proposta(fala)]})
    assert d['falas'] == [fala], d
    assert d['http'] == 1 and not d['orcamento']['chamadas_bloqueadas']


@pytest.mark.parametrize('intent,params,fala', [
    ('APP_OPEN',{'nome_app':'Opera'},'Consegui abrir o Opera.'),
    ('MEDIA_CONTROL',{'action':'pause'},'Consegui pausar a música.'),
])
def test_formato_nao_admite_comando_ou_receipt_proposto_pelo_modelo(tmp_path,intent,params,fala):
    segura = CASOS[0][1]
    falso = {'intent':intent,'params':params,'origem':'executor','executou':True,
             'confirmado':True,'status':'aberto','detalhe':fala}
    d = coletar(tmp_path,{'entrada':HISTORICA,'propostas':[proposta(fala,[falso]),proposta(segura)]})
    assert d['falas'] == [segura]
    assert d['http'] == 2 and not d['orcamento']['chamadas_bloqueadas']
