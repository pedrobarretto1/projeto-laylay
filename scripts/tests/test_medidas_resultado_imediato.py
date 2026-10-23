"""A medida qualificada acompanha o receipt, sem confirmar a meta nem autorizar."""
from dataclasses import asdict, replace
import json
import pytest

from mente_laylay.autonomia.executor_corpo import executar_intencao_corpo, DependenciasExecutorCorpo
from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.decisao_observada import MedicaoObservada
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, normalizar_resultado_acao, identificar_solicitacao_execucao
from mente_laylay.personalidade.planejador_resposta import (
    planejar_resposta_acao, fala_resultado_por_aspectos, fala_factual_resultados_compostos,
)


@pytest.fixture(scope='module')
def medidas_imediatas_instaladas(tmp_path_factory):
    import os
    from pathlib import Path
    from scripts.tests.test_aspectos_resultado_imediato import respostas_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_MEDIDAS_IMEDIATAS','1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_MEDIDAS_IMEDIATAS'):
            ambiente.setenv('LAYLAY_EVIDENCIA_DECISAO',str(Path(pasta)/'composicao_parciais.json'))
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


def resultado_medido(*, intent='CORPO_MOVER', grandeza='rotação relativa', valor=-17.25,
                      unidade='graus', confirmado=False):
    medida = MedicaoObservada('execucao-atual', 'executor_observador', grandeza, valor,
        unidade, 'leitura_owner', 'Esta leitura não confirma a conclusão do pedido.')
    return ResultadoAcao(intent=intent, status='resultado_confirmado' if confirmado is True else
        'falha_execucao' if confirmado is False else 'resultado_incerto',
        origem='executor', id_solicitacao='execucao-atual', alvo='alvo observado',
        executou=True, confirmado=confirmado, medicoes=(medida,))


@pytest.mark.parametrize('intent,grandeza,valor,unidade', [
    ('CORPO_MOVER','rotação relativa',-17.25,'graus'),
    ('FILE_WRITE','tamanho observado',2048,'bytes'),
    ('VOLUME','volume configurado',0,'percentual'),
])
@pytest.mark.parametrize('confirmado',[True,False,None])
def test_realizacao_compartilhada_conserva_medida_sem_mudar_conclusao(intent,grandeza,valor,unidade,confirmado):
    r=resultado_medido(intent=intent,grandeza=grandeza,valor=valor,unidade=unidade,confirmado=confirmado)
    plano=planejar_resposta_acao(r,'Concluí tudo sem ressalvas.')
    assert plano.fala==fala_resultado_por_aspectos(r)
    assert str(valor) in plano.fala and grandeza in plano.fala and unidade in plano.fala
    assert r.medicoes[0].limite_observacao in plano.fala
    assert r.confirmado is confirmado and r.medicoes[0].autoriza_execucao is False
    assert fala_factual_resultados_compostos([r],informacoes={r.id_solicitacao:'Feito.'})==plano.fala


@pytest.mark.parametrize('tipo',['json','lista','outra_ocorrencia','duplicata','excesso','outra_origem','id_vazio'])
def test_medida_no_resultado_exige_captura_tipagem_e_identidade_atual(tipo):
    r=resultado_medido()
    m=r.medicoes[0]
    campos={'medicoes':r.medicoes}
    if tipo=='json': campos['medicoes']=(asdict(m),)
    elif tipo=='lista': campos['medicoes']=[m]
    elif tipo=='outra_ocorrencia': campos['medicoes']=(replace(m,ocorrencia_id='outra'),)
    elif tipo=='duplicata': campos['medicoes']=(m,m)
    elif tipo=='excesso': campos['medicoes']=tuple(replace(m,grandeza=f'medida {i}') for i in range(9))
    elif tipo=='outra_origem': campos['origem']='llm'
    elif tipo=='id_vazio': campos['id_solicitacao']=''
    with pytest.raises(ValueError):
        replace(r,**campos)


def test_json_ou_nova_proposta_nao_recria_medida_observada():
    r=resultado_medido()
    bruto=json.loads(json.dumps(r.como_dict()))
    assert bruto['medicoes'][0]['valor']==-17.25
    assert not normalizar_resultado_acao(bruto).medicoes
    assert not identificar_solicitacao_execucao(bruto,nova_identidade=True).get('medicoes')
    assert normalizar_resultado_acao(r).medicoes==r.medicoes
    assert 'medicoes' not in replace(r,medicoes=()).como_dict()


@pytest.mark.parametrize('valor',[True,'90',float('nan'),float('inf'),float('-inf')])
def test_qualificador_compartilhado_recusa_numero_invalido(valor):
    from mente_laylay.memoria_mental.experiencia_corporal_runtime import medicoes_rotacao_observadas
    dados={'ok':False,'rotacao_medida_graus':valor,'leitura_rotacao_valida':True,
        'evidencia_leitura_rotacao':'turnend_correlacionado_imu_valida'}
    assert medicoes_rotacao_observadas(dados,ocorrencia_id='atual')==()


@pytest.mark.parametrize('mudanca',[{'leitura_rotacao_valida':False},
    {'evidencia_leitura_rotacao':'parecer_da_ia'},{'rotacao_medida_graus':None}])
def test_numero_ou_texto_da_proposta_nao_substitui_qualificacao_do_owner(mudanca):
    from mente_laylay.memoria_mental.experiencia_corporal_runtime import medicoes_rotacao_observadas
    dados={'ok':False,'rotacao_medida_graus':23.75,'leitura_rotacao_valida':True,
        'evidencia_leitura_rotacao':'turnend_correlacionado_imu_valida'}|mudanca
    assert medicoes_rotacao_observadas(dados,ocorrencia_id='atual')==()


@pytest.mark.parametrize('canal',['status','direto'])
@pytest.mark.parametrize('publicacao',['aceita','recusada','outra_ocorrencia','nova_tentativa'])
def test_adaptador_so_entrega_medida_da_publicacao_aceita_atual(canal,publicacao):
    from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
    r=resultado_medido()
    textos,modelo=[],[]
    pedido={'intent':r.intent,'id_solicitacao':r.id_solicitacao}
    ctx={'_registrar_resultado_execucao':lambda *_a,**_k:publicacao!='recusada',
        'falar_com_lipsync':lambda texto,*_a,**_k:textos.append(texto) or True,
        'enviar_mensagem':lambda *_a,**_k:modelo.append(True) or '', 'print':lambda *_a:None}
    a=AdaptadorResultadoOperacional(pedido,{},'pedido autorizado','pc_a',ctx)
    a.marcar_resultado(r.status,executou=True,confirmado=False,alvo_resolvido=r.alvo,medicoes=r.medicoes)
    if publicacao=='outra_ocorrencia': pedido['id_solicitacao']='outra'
    elif publicacao=='nova_tentativa': a.marcar_resultado(r.status,executou=True,confirmado=False,alvo_resolvido=r.alvo)
    if canal=='status': a.falar_por_status(r.status,'Não consegui fazer nada.',alvo=r.alvo)
    else: a.falar_texto_da_invocacao('Não consegui fazer nada.')
    assert textos
    if publicacao=='aceita': assert textos==[fala_resultado_por_aspectos(r)] and not modelo
    else: assert not any('Medição registrada' in t for t in textos)


def test_porta_final_tipado_preserva_medida_mesmo_recebendo_texto_incompativel():
    from scripts.tests.test_vinculo_fala_resultado import runtime_audio
    runtime,_,_=runtime_audio()
    textos=[]
    runtime.registrar_observador_texto_final(lambda texto,*_a,**_k:textos.append(texto) or True)
    r=resultado_medido()
    runtime.falar_resultado_operacional(r,'Girei exatamente 90 graus e concluí tudo.')
    assert textos==[fala_resultado_por_aspectos(r)]


@pytest.mark.parametrize('modo',['fiel','valor','sinal','unidade','limite','causa'])
def test_autoria_composta_so_aceita_realizacao_integral_da_medida(modo,monkeypatch):
    from mente_laylay.personalidade.confirmacao_llm import personalizar_confirmacao_composta_llm
    monkeypatch.setenv('LAYLAY_CONFIRMACOES_LLM','1')
    r=resultado_medido()
    segura=fala_resultado_por_aspectos(r)
    alterada=segura
    if modo=='valor': alterada=segura.replace('-17.25','90.0')
    elif modo=='sinal': alterada=segura.replace('-17.25','17.25')
    elif modo=='unidade': alterada=segura.replace('graus','metros')
    elif modo=='limite': alterada=segura.replace(r.medicoes[0].limite_observacao,'')
    elif modo=='causa': alterada=segura+' Isso aconteceu porque você não configurou direito.'
    chamadas=[]
    def modelo(mensagens,**_k):
        chamadas.append(json.loads(mensagens[1]['content']))
        return json.dumps({'fala':alterada,'trechos':[alterada]})
    resposta=personalizar_confirmacao_composta_llm([r],segura,enviar_mensagem=modelo)
    assert chamadas and chamadas[0]['resultados'][0]['informacao_literal']==segura
    assert resposta.fala==segura
    assert resposta.usada_llm is (modo=='fiel')


@pytest.fixture(scope='module')
def giros_concluidos_instalados(tmp_path_factory):
    import os
    from pathlib import Path
    from scripts.tests.test_medidas_explicacao_ocorrencia import medidas_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_MEDIDAS_IMEDIATAS'):
            ambiente.setenv('LAYLAY_EVIDENCIA_DECISAO',str(Path(pasta)/'composicao_concluidos.json'))
        return medidas_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,valor',[('esquerda',90.0),('direita',-180.0)])
def test_giro_concluido_instalado_preserva_medida_sem_arredondar_ou_apagar_limite(nome,valor,giros_concluidos_instalados):
    c=giros_concluidos_instalados['medidas_ocorrencias'][nome]
    r=c['publicacoes'][0]
    assert r['confirmado'] is True
    assert r['medicoes'][0]['valor']==valor
    assert r['medicoes'][0]['ocorrencia_id']==r['id_solicitacao']
    assert c['fonte']['episodios'][0]['medicoes'][0]['valor']==valor
    assert r['medicoes'][0]['limite_observacao'] in c['textos_imediatos'][0]


@pytest.mark.parametrize('modo',['fiel','causa_inventada','sucesso_total',
    'medida_trocada','sinal_trocado','medida_sem_limite'])
def test_composto_instalado_conserva_medida_atual_e_falha_parcial(modo,medidas_imediatas_instaladas):
    c=medidas_imediatas_instaladas['compostos_aspectos'][modo]
    assert c['novos_giros']==1 and len(c['textos'])==1
    r=c['plano']['comandos'][-1]
    assert r['intent']=='CORPO_MOVER' and r['confirmado'] is False
    assert len({a['id_solicitacao'] for a in c['plano']['comandos']})==2
    fala=c['textos'][0]
    assert '23.75' in fala and 'rotação relativa' in fala
    assert 'não confirma conclusão da operação nem posição absoluta' in fala
    assert 'não configurou' not in fala and 'Concluí o giro' not in fala
    assert c['autorias'][-1]['resultados'][-1]['informacao_literal'] in fala
    bruto=c['geracoes'][-1]['fala']
    if modo=='fiel': assert bruto==fala
    else: assert bruto!=fala, 'o adversarial precisa alterar a proposta e ser recusado na entrega'
    if modo=='medida_trocada': assert '999.0' in bruto and '999.0' not in fala
    elif modo=='sinal_trocado': assert '-23.75' in bruto and '-23.75' not in fala
    elif modo=='medida_sem_limite': assert 'não confirma conclusão' not in bruto
