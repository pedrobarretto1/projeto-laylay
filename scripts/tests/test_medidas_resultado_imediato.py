"""A medida qualificada acompanha o receipt, sem confirmar a meta nem autorizar."""
from dataclasses import asdict, replace
import pytest

from mente_laylay.autonomia.executor_corpo import executar_intencao_corpo, DependenciasExecutorCorpo
from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.decisao_observada import MedicaoObservada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, normalizar_resultado_acao, identificar_solicitacao_execucao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


@pytest.fixture(scope='module')
def medidas_imediatas_instaladas(tmp_path_factory):
    from scripts.tests.test_aspectos_resultado_imediato import respostas_instaladas
    return respostas_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,valor', [('parcial',23.75),('zero',0.0),('divergente',-17.25),('ultrapassou',110.5),('sem_parada',23.75)])
def test_medida_do_receipt_alcanca_publicacao_e_fala_instaladas(nome,valor,medidas_imediatas_instaladas):
    c=medidas_imediatas_instaladas['medidas_ocorrencias'][nome]
    r=c['publicacoes'][0]
    assert r['contexto']['receipt_corpo']['leitura_rotacao_valida'] is True
    assert r['contexto']['receipt_corpo']['rotacao_medida_graus']==valor
    medidas=r.get('medicoes',[])
    assert len(medidas)==1, 'primeira perda: receipt qualificado não chega ao contrato imediato'
    assert medidas[0]['valor']==valor and medidas[0]['ocorrencia_id']==r['id_solicitacao']
    fala=c['textos_imediatos'][0]
    assert str(valor) in fala and 'rotação relativa' in fala and 'graus' in fala
    assert medidas[0]['limite_observacao'] in fala
    assert r['confirmado'] is False and c['sem_novos_efeitos'] and c['sem_mutacao_historico']


@pytest.mark.parametrize('nome',['imu_invalida','saturacao','protecao','interrompido','outra_sequencia'])
def test_receipt_nao_qualificado_nao_cria_medida_imediata(nome,medidas_imediatas_instaladas):
    c=medidas_imediatas_instaladas['medidas_ocorrencias'][nome]
    assert not c['publicacoes'][0].get('medicoes')
    assert 'Medição registrada' not in c['textos_imediatos'][0]


@pytest.mark.parametrize('ok,valor',[(True,90.0),(True,-90.75),(False,23.75),(False,0.0)])
def test_executor_adapta_medida_da_invocacao_sem_inferir_do_pedido(ok,valor):
    from types import SimpleNamespace
    texto='gire 90 graus para a esquerda'
    pedido=detectar_intencao_corpo(texto)
    receipt={'ok':ok,'aplicacao_pwm_confirmada':True,'parada_confirmada':True,
        'prova_rotacao':ok,'rotacao_medida_graus':valor,
        'evidencia':'imu_relativa_turnend_e_sack' if ok else '',
        'leitura_rotacao_valida':True,'evidencia_leitura_rotacao':'turnend_correlacionado_imu_valida'}
    publicados=[]
    executar_intencao_corpo(pedido['intent'],pedido['params'],texto,
        {'turno_atual':classificar_modalidade_turno(texto),'_corpo_motor_runtime':SimpleNamespace(executar=lambda *_a:receipt)},
        DependenciasExecutorCorpo(lambda status,**k:publicados.append(k),lambda *_a,**_k:None,'pedido-atual'))
    medidas=publicados[0].get('medicoes',())
    assert len(medidas)==1 and type(medidas[0]) is MedicaoObservada
    assert medidas[0].valor==valor and medidas[0].ocorrencia_id=='pedido-atual'
    assert publicados[0]['confirmado'] is ok
