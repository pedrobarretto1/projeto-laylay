"""Conservar palavras não basta para conferir o escopo de uma paráfrase."""
import pytest

from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
from scripts.tests.test_revisao_suporte_fontes import _plano


CASOS = [
    ('Se o teste falha, então o alarme toca。 a escrita foi concluída.',
     'o alarme toca。 a escrita foi concluída, se o teste falha.'),
    ('Se o modo de teste está ativo, então o motor funciona a menos que a trava esteja acionada.',
     'o motor funciona a menos que a trava esteja acionada, se o modo de teste está ativo.'),
    ('Se o teste falha, então „o alarme toca‟.',
     '„o alarme toca‟, se o teste falha.'),
]


@pytest.mark.parametrize('fonte,fala', CASOS)
@pytest.mark.parametrize('invertida', [False, True])
def test_apoio_nao_e_conferido_sem_provar_fronteiras_e_escopo_das_clausulas(fonte, fala, invertida):
    if invertida:
        fonte, fala = fala, fonte
    r = revisar_suporte_autoria(fala, plano=_plano(fala, trecho=fonte), agora=1001)
    unidade = r.como_dict()['proposicoes'][0]
    assert unidade['estado'] == 'apoio_semantico_pendente'
    assert all('derivacao' not in f for f in unidade['fontes'])
    assert fala not in r.fala_realizada
    assert r.semantica_verificada is r.prova_implicacao is r.autoriza_execucao is False


@pytest.mark.parametrize('fonte,fala', CASOS[:2])
def test_citacao_integral_nao_e_proibida_por_conter_condicoes(fonte, fala):
    r = revisar_suporte_autoria(fonte, plano=_plano(fonte, trecho=fonte), agora=1001)
    assert r.como_dict()['proposicoes'][0]['estado'] == 'literal_integral_na_fonte'
    assert '«' + fonte + '»' in r.fala_realizada
    assert r.prova_implicacao is r.autoriza_execucao is False
