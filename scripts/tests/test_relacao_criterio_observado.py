"""Consulta avaliativa precisa do critério observado, sem inferir regra ou receipt."""
from dataclasses import replace
import time
import pytest
from scripts.tests.test_projecao_evidencia_autoral import registro_autoral
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao, criterio_para_publicacao
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, selecionar_fala_observada


def preparar(texto, registro=None):
    mente={'registro_semantico':registro if registro is not None else registro_autoral()}
    turno=classificar_modalidade_turno(texto)
    plano=planejar_turno(texto,turno=turno,mente=mente)
    plano['contrato_fala']=construir_contrato_semantico_fala(texto,turno=turno,plano=plano,mente=mente)
    return plano,mente


@pytest.mark.parametrize('texto', [
    'essa descrição justifica o seu critério?',
    'por que esse critério?',
    'qual a relação entre essa descrição e o seu critério?',
    'essa fonte sustenta esse critério?',
    'como essa informação se relaciona ao seu critério?',
])
def test_consulta_de_criterio_publicado_nao_e_auditoria_de_execucao(texto):
    plano,_=preparar(texto)
    contrato=plano['contrato_fala']
    assert 'opiniao_autoral' in contrato, 'referente foi enviado ao owner de resultados de ação'
    assert contrato['opiniao_autoral'].modo=='relacao_criterio'
    assert 'evidencia_fala_historica' not in contrato and 'explicacao_ocorrencia' not in contrato
    opcoes=realizacoes_opiniao(texto,contrato=contrato,turno_id=plano['id'])
    assert len(opcoes)==1 and 'curiosidade' in opcoes[0]
    assert 'Não registrei uma regra' in opcoes[0]
    assert 'Esta descrição vale somente no cenário simulado.' in opcoes[0]
    assert 'resultado operacional' not in opcoes[0]
    assert verificar_fala_turno(opcoes[0],plano=plano)['aceita']
    assert not verificar_fala_turno('Isso prova que eu gosto de indie porque me emocionei.',plano=plano)['aceita']


@pytest.mark.parametrize('texto', [
    'essa descrição justifica o critério de João?',
    'essa descrição justifica o critério de execução?',
    'essa descrição justifica o seu critério? abre a calculadora',
    'repita "por que esse critério?"',
    'por que você abriu esse arquivo?',
])
def test_criterio_nao_captura_outro_agente_operacao_citacao_ou_composto(texto):
    plano,_=preparar(texto)
    fonte=plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is None or fonte.modo!='relacao_criterio'


@pytest.mark.parametrize('invalido',['sem_criterio','dict','origem_ausente','expirado'])
def test_consulta_sem_criterio_nativo_vigente_nao_herda_avaliacao(invalido):
    from dataclasses import asdict
    registro=registro_autoral()
    fala=registro['falas_observadas'][0]
    if invalido=='sem_criterio':fala.pop('criterio_autoral')
    elif invalido=='dict':fala['criterio_autoral']=asdict(fala['criterio_autoral'])
    elif invalido=='origem_ausente':fala['criterio_autoral']=replace(fala['criterio_autoral'],origem_id='nao_publicada')
    else:
        fala['ts']=time.time()-901
        fala['criterio_autoral']=replace(fala['criterio_autoral'],ts_origem=fala['ts'],ts_portadora=fala['ts'])
    plano,_=preparar('por que esse critério?',registro)
    fonte=plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is None or fonte.modo!='relacao_criterio'


def test_repeticao_da_relacao_preserva_origem_sem_criar_regra_posterior():
    registro=registro_autoral()
    original=selecionar_fala_observada(registro)['criterio_autoral']
    for n,texto in enumerate(['por que esse critério?','essa descrição justifica o seu critério?',
                              'qual a relação entre essa descrição e o seu critério?']):
        plano,_=preparar(texto,registro)
        opcao=realizacoes_opiniao(texto,contrato=plano['contrato_fala'],turno_id=plano['id'])[0]
        plano['ultima_verificacao']=verificar_fala_turno(opcao,plano=plano)
        assert plano['ultima_verificacao']['aceita']
        criterio=criterio_para_publicacao(plano,opcao)
        assert criterio and criterio.origem_id==original.origem_id and criterio.ts_origem==original.ts_origem
        registro=registrar_fala_observada(registro,ocorrencia_id='relacao-'+str(n),turno_id=str(plano['id']),
            fala=opcao,resultados=(),canal='texto_publicado',criterio_autoral=criterio)
        assert 'Não registrei uma regra' in opcao and 'resultado operacional' not in opcao


def test_fonte_vencida_limita_descricao_mas_preserva_consulta_de_criterio():
    registro=registro_autoral()
    f=registro['falas_observadas'][0]
    c=f['criterio_autoral']
    f['criterio_autoral']=replace(c,fundamento=replace(c.fundamento,expira_em=time.time()-1))
    plano,_=preparar('por que esse critério?',registro)
    opcoes=realizacoes_opiniao(plano['texto_usuario'],contrato=plano['contrato_fala'],turno_id=plano['id'])
    assert len(opcoes)==1 and 'Não tenho uma descrição factual vigente' in opcoes[0]
    assert 'Esta descrição vale somente' not in opcoes[0]


def test_composicao_instalada_distingue_relacao_avaliativa_de_execucao(tmp_path):
    import json,os,subprocess,sys
    from pathlib import Path
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo=CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    folha="if 'criterio_autoral' in schema.get('properties',{}):proposta['criterio_autoral']='nao_declarado'"
    assert codigo.count(folha)==1
    codigo=codigo.replace(folha,"""unidade=schema.get('properties',{}).get('suporte_proposicoes',{}).get('items',{})
    opcoes=unidade.get('properties',{}).get('texto',{}).get('enum',[])
    if opcoes:proposta['suporte_proposicoes'][0]['texto']=opcoes[0]
    if 'criterio_autoral' in schema.get('properties',{}):proposta['criterio_autoral']='curiosidade'""")
    codigo+='''
passos=[]
for pergunta in ['você gosta de indie?','você prefere Windows ou Linux?','você prefere chá ou café?']:
    root._resposta_ia_runtime.processar(pergunta,origem='teste_relacao')
    ini=len(falas)
    for pedido in ['por que esse critério?','essa descrição justifica o seu critério?',
                   'qual a relação entre essa descrição e o seu critério?']:
        root._resposta_ia_runtime.processar(pedido,origem='teste_relacao')
        p=estado.snapshot()['mental']['plano_turno_atual']
        fonte=p['contrato_fala'].get('opiniao_autoral')
        passos.append({'pedido':pedido,'modo':fonte.modo if fonte else None,'resposta':falas[-1],
            'comandos':p['comandos'],'autoriza':p['autoriza_execucao']})
    assert len(falas)-ini==3
sys.__stdout__.write('RELACAO_JSON='+json.dumps({'passos':passos,'efeitos':efeitos,'voz':False},ensure_ascii=False)+'\\n')
'''
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path),'[]'],
        cwd=Path(__file__).resolve().parents[2],env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=90)
    assert r.returncode==0,r.stdout[-2200:]+r.stderr[-1500:]
    d=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('RELACAO_JSON=')))
    assert not d['efeitos'] and not d['voz'] and len(d['passos'])==9
    for p in d['passos']:
        assert p['modo']=='relacao_criterio'
        assert 'Não registrei uma regra' in p['resposta'] and 'resultado operacional' not in p['resposta']
        assert not p['comandos'] and not p['autoriza']
