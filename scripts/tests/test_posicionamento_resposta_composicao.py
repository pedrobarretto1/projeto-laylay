"""Roteamento real da ponte, sem Qwen/voz/efeitos e com persistência privada."""
import pytest
from tests.test_escopo_atos_composicao import coletar_ponte
from tests.test_resultado_perifrastico_composicao import proposta
from tests.test_confirmacao_escopo_ato import ABERTURA
from tests.test_posicionamento_resposta import POSICOES


@pytest.mark.parametrize('pergunta,fala', [(ABERTURA,'Oi! '+POSICOES[0][1]),
    POSICOES[1],POSICOES[3],POSICOES[4],POSICOES[5],POSICOES[9],POSICOES[10]])
def test_posicao_natural_chega_a_publicacao_sem_reparo_lexical(tmp_path,pergunta,fala):
    d = coletar_ponte(tmp_path,{'entrada':pergunta,'propostas':[proposta(fala)]})
    assert not d['autoriza'] and not d['comandos']
    assert d['falas']==[fala],d
    assert d['http']==1 and not d['orcamento']['chamadas_bloqueadas']


@pytest.mark.parametrize('intent,params,falsa', [
    ('APP_OPEN',{'nome_app':'Opera'},'Entendo que consegui abrir o Opera.'),
    ('MEDIA_CONTROL',{'action':'pause'},'Na minha opinião, consegui pausar a música.'),
])
def test_posicao_nao_confere_receipt_proposto_ou_ordem_do_modelo(tmp_path,intent,params,falsa):
    segura = POSICOES[4][1]
    recibo = {'intent':intent,'params':params,'origem':'executor','executou':True,
              'confirmado':True,'status':'aberto','detalhe':falsa}
    d = coletar_ponte(tmp_path,{'entrada':POSICOES[4][0],
        'propostas':[proposta(falsa,[recibo]),proposta(segura)]})
    assert not d['autoriza'] and not d['comandos']
    assert len(d['falas'])==1 and d['falas'][0].endswith(segura) and falsa not in d['falas'][0]
    assert d['http']==2 and not d['orcamento']['chamadas_bloqueadas']
