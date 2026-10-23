"""Meta anterior, leitura observada e conclusão pertencem à mesma ocorrência."""
import pytest
from dataclasses import asdict, replace, FrozenInstanceError
from mente_laylay.memoria_mental.decisao_observada import (
    ExpectativaResultado, MedicaoObservada, ExplicacaoOcorrencia,
)
from mente_laylay.cognicao.explicacao_fala_historica import realizacoes_explicacao_ocorrencia


@pytest.fixture(scope='module')
def expectativas_instaladas(tmp_path_factory):
    import os
    from pathlib import Path
    from scripts.tests.test_leituras_parciais_corpo import parciais_instaladas
    with pytest.MonkeyPatch.context() as ambiente:
        ambiente.setenv('LAYLAY_COLETAR_EXPECTATIVAS_OCORRENCIA','1')
        if pasta := os.environ.get('LAYLAY_EVIDENCIA_EXPECTATIVAS'):
            ambiente.setenv('LAYLAY_EVIDENCIA_DECISAO',str(Path(pasta)/'composicao.json'))
        return parciais_instaladas.__wrapped__(tmp_path_factory)


@pytest.mark.parametrize('nome,meta',[('meta90',90),('meta180',180),('meta_direita',-90),('sem_leitura',45)])
def test_meta_validada_ja_existe_antes_do_efeito_e_chega_a_fonte(nome,meta,expectativas_instaladas):
    assert all(expectativas_instaladas['owners'].values())
    c=expectativas_instaladas['medidas_ocorrencias'][nome]
    inicio=c['inicio_ocorrencia']['ocorrencia']
    esperado=inicio.get('expectativas',[])
    assert len(esperado)==1, 'primeira perda: parâmetro conhecido não foi capturado na ocorrência antes do efeito'
    assert esperado[0]['valor']==meta and esperado[0]['ocorrencia_id']==inicio['id']
    assert c['experiencia']['expectativas']==esperado
    aprendidos=[evento['contexto']['experiencia'] for evento in c['eventos_aprendizado']
        if evento.get('contexto',{}).get('experiencia',{}).get('id')==inicio['id']]
    assert aprendidos and all(e['expectativas']==esperado for e in aprendidos)
    episodio=c['fonte']['episodios'][0]
    assert episodio['expectativas']==esperado
    assert str(meta) in c['fala_owner'] and 'Valor solicitado' in c['fala_owner']
    assert c['experiencia']['confirmado'] is False
    assert c['sem_novos_efeitos'] and c['sem_mutacao_historico']
    for turno in c['turnos']:
        assert turno['textos']==[c['fala_owner']] and not turno['executores']
        assert turno['codec_integral'] and turno['contexto_fechado']


def test_leitura_igual_nao_apaga_a_diferenca_entre_metas_historicas(expectativas_instaladas):
    casos=expectativas_instaladas['medidas_ocorrencias']
    a,b=casos['meta90'],casos['meta180']
    assert a['experiencia']['rotacao_medida_graus']==b['experiencia']['rotacao_medida_graus']==23.75
    metas=[c['fonte']['episodios'][0].get('expectativas',[]) for c in (a,b)]
    assert all(metas), 'fonte perdeu a meta, embora a medição de ambas exista'
    assert metas[0][0]['valor']==90 and metas[1][0]['valor']==180
    assert a['fala_owner']!=b['fala_owner']


def test_pulso_sem_meta_angular_nao_ganha_expectativa_pelo_nome_ou_turno(expectativas_instaladas):
    c=expectativas_instaladas['medidas_ocorrencias']['pulso']
    assert not c['inicio_ocorrencia']['ocorrencia'].get('expectativas')
    assert not c['fonte']['episodios'][0].get('expectativas')


def expectativa(episodio, **alteracoes):
    campos=dict(ocorrencia_id=episodio.id,owner=episodio.owner,grandeza='rotação relativa',
        valor=90,unidade='graus',fonte='parametros_validados_antes_da_execucao',
        registrada_em=episodio.iniciada_em)
    return ExpectativaResultado(**(campos|alteracoes))


@pytest.mark.parametrize('owner,grandeza,valor,unidade',[
    ('executor_corpo','rotação relativa',-90,'graus'),
    ('executor_volume','volume configurado',25,'percentual'),
    ('executor_arquivos','tamanho solicitado',2048,'bytes'),
])
@pytest.mark.parametrize('confirmado',[True,False,None])
def test_meta_compartilhada_nao_e_medicao_causa_ou_confirmacao(owner,grandeza,valor,unidade,confirmado):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e=episodio(owner=owner,confirmado=confirmado)
    meta=expectativa(e,grandeza=grandeza,valor=valor,unidade=unidade)
    e=replace(e,expectativas=(meta,))
    f=ExplicacaoOcorrencia('consulta','Por que fez essa ação?',(e,),'unica')
    fala=realizacoes_explicacao_ocorrencia(f)[0]
    assert grandeza in fala and str(valor) in fala and unidade in fala
    assert 'A meta registrada não comprova que a operação foi concluída.' in fala
    assert e.confirmado is confirmado and not e.medicoes
    assert meta.autoriza_execucao is False and meta.confirma_efeito is False
    with pytest.raises(FrozenInstanceError): meta.valor=999


@pytest.mark.parametrize('alteracao',[{'valor':True},{'valor':'90'},{'valor':float('nan')},
    {'valor':float('inf')},{'registrada_em':float('nan')},{'registrada_em':True},
    {'registrada_em':-1},{'ocorrencia_id':''},{'owner':''},{'unidade':''},{'fonte':''}])
def test_expectativa_recusa_dados_sem_qualificacao_estrutural(alteracao):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    with pytest.raises(ValueError): expectativa(episodio(),**alteracao)


@pytest.mark.parametrize('tipo',['json','lista','outra_ocorrencia','outro_owner','posterior','duplicada','excesso'])
def test_episodio_recusa_meta_sem_vinculo_anterior_do_owner(tipo):
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e=episodio();meta=expectativa(e);metas=(meta,)
    if tipo=='json': metas=(asdict(meta),)
    elif tipo=='lista': metas=[meta]
    elif tipo=='outra_ocorrencia': metas=(replace(meta,ocorrencia_id='outra'),)
    elif tipo=='outro_owner': metas=(replace(meta,owner='outro_owner'),)
    elif tipo=='posterior': metas=(replace(meta,registrada_em=e.iniciada_em+1),)
    elif tipo=='duplicada': metas=(meta,meta)
    elif tipo=='excesso': metas=tuple(replace(meta,grandeza=f'meta {i}') for i in range(9))
    with pytest.raises(ValueError): replace(e,expectativas=metas)


def historico_com_meta(*, capturar=True):
    from scripts.tests.test_decisao_observada import experiencia
    estado,runtime=experiencia()
    inicio=runtime.iniciar(nome='giro_medido_180',origem_intencao='pedido_usuario',perfil='bancada',
        **({'angulo_solicitado_graus':90} if capturar else {}))
    retorno={'ok':False,'angulo_solicitado_graus':180,'rotacao_medida_graus':23.75,
        'leitura_rotacao_valida':True,'evidencia_leitura_rotacao':'turnend_correlacionado_imu_valida'}
    e=runtime.registrar(inicio,retorno,[{'ok':False,'aplicacao_pwm_confirmada':True,'parada_confirmada':True}])
    return estado,runtime,inicio,e


def test_retorno_divergente_e_turno_posterior_nao_reescrevem_meta_original():
    estado,runtime,inicio,e=historico_com_meta()
    assert e['expectativas'][0]['valor']==90, 'retorno posterior não substitui a captura original'
    inicio['expectativas'][0]['valor']=999
    estado.atualizar_campos('mental',turno_atual={'id':'outra','texto':'agora faça 999 graus'},
        intencao_corporal={'angulo_graus':999})
    f=runtime.recuperar_explicacao(f"Por que fez esse gesto {e['id']}?",turno={'id':'consulta'})
    assert f.episodios[0].expectativas[0].valor==90
    assert f.episodios[0].medicoes[0].valor==23.75
    assert f.episodios[0].confirmado is False


def test_legado_nao_reconstroi_meta_por_nome_receipt_ou_consulta_atual():
    _,runtime,_,e=historico_com_meta(capturar=False)
    f=runtime.recuperar_explicacao(f"Por que fez esse gesto {e['id']} de 999 graus?",turno={'id':'consulta'})
    assert not f.episodios[0].expectativas and f.episodios[0].medicoes[0].valor==23.75
    fala=realizacoes_explicacao_ocorrencia(f,agora=101)[0]
    assert 'Não há valor solicitado registrado nesta fonte para comparação.' in fala
    assert 'Valor solicitado de' not in fala


@pytest.mark.parametrize('alteracao',[{'ocorrencia_id':'outra'},{'owner':'outro'},
    {'fonte':'proposta_ia'},{'registrada_em':102.0},{'autoriza_execucao':True},
    {'confirma_efeito':True},{'valor':'90'}])
def test_meta_historica_invalida_nao_apaga_medicao_valida(alteracao):
    estado,runtime,_,e=historico_com_meta()
    historico=estado.obter_copia('mental','historico_corporal',[])
    historico[0]['expectativas'][0].update(alteracao)
    estado.atualizar_campos('mental',historico_corporal=historico)
    f=runtime.recuperar_explicacao(f"Por que fez esse gesto {e['id']}?",turno={'id':'consulta'})
    assert f and not f.episodios[0].expectativas
    assert f.episodios[0].medicoes[0].valor==23.75 and f.episodios[0].confirmado is False


def test_unidades_diferentes_nao_geram_subtracao_ou_conversao_implicita():
    from scripts.tests.test_explicacao_ocorrencia import episodio
    e=episodio()
    e=replace(e,expectativas=(expectativa(e),),medicoes=(MedicaoObservada(e.id,e.owner,
        'rotação relativa',1.5,'radianos','leitura_owner','Não confirma posição absoluta.'),))
    fala=realizacoes_explicacao_ocorrencia(ExplicacaoOcorrencia('q','Por que fez esse gesto?',(e,),'unica'))[0]
    assert '90 "graus"' in fala and '1.5 "radianos"' in fala
    assert 'diferença de' not in fala and 'faltaram' not in fala
