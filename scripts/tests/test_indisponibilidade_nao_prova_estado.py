"""Limite de capacidade, estado observado e autoridade são contratos distintos."""
import pytest
from tests.test_coerencia_capacidade_documentada import avaliar,CASOS


@pytest.mark.parametrize('texto,dominio,negativa,limite',CASOS)
def test_indisponibilidade_nao_ganha_predicado_de_capacidade_disponivel(texto,dominio,negativa,limite):
    r=avaliar(texto,dominio,negativa,disponivel=False)
    assert 'capacidade_documentada_negada' not in r['problemas']
    # Testar a declaração de limite sozinha, sem emprestar a ela o estado de
    # um aplicativo que a segunda oração da fixture possa pressupor.
    declaracao=negativa.split(',',1)[0].rstrip('.')+'.'
    assert avaliar(texto,dominio,declaracao,disponivel=False)['aceita']


def test_resposta_historica_sobre_midia_nao_prova_que_um_player_esta_tocando():
    texto,dominio,negativa,_=CASOS[0]
    r=avaliar(texto,dominio,negativa,disponivel=False)
    assert r['problemas']==['resultado_operacional_sem_evidencia']
    assert not r['aceita']
    assert r['contrato_reparo']['resultado_operacional_desconhecido'] is True
    assert 'indisponivel' in r['contrato_reparo']['documentacao_capacidades']
    assert r['contrato_reparo']['autoriza_execucao'] is False


@pytest.mark.parametrize('texto,dominio,negativa,estado',[
    ('como eu poderia retomar a música?','musica','A Laylay não controla o áudio diretamente.',
     'O aplicativo está tocando agora.'),
    ('como eu poderia abrir a calculadora?','sistema','Não consigo abrir programas no seu computador.',
     'A Calculadora está aberta.'),
    ('como eu poderia fechar a aba?','navegador','Não consigo fechar abas do navegador.',
     'A aba está aberta.'),
])
def test_limite_documentado_nao_isenta_alegacao_de_estado_atual(texto,dominio,negativa,estado):
    r=avaliar(texto,dominio,negativa+' '+estado,disponivel=False)
    assert 'resultado_operacional_sem_evidencia' in r['problemas']
    assert 'capacidade_documentada_negada' not in r['problemas'] and not r['aceita']


def test_condicao_explicita_nao_afirma_estado_atual_do_player():
    texto,dominio,_,_=CASOS[0]
    fala='A Laylay não controla o áudio diretamente. Se o aplicativo está tocando, isso é apenas uma hipótese.'
    r=avaliar(texto,dominio,fala,disponivel=False)
    assert 'resultado_operacional_sem_evidencia' not in r['problemas']
