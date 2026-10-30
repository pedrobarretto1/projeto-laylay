"""Fala observada conserva credenciais no host e projeta só descrição ao modelo."""
from dataclasses import dataclass, replace
import hashlib
import json
import time
import pytest

from mente_laylay.cognicao.criterio_autoral import (
    CriterioAutoralEmissao, CriterioAutoralPublicado, FundamentoCriterioAutoral,
    criterio_publicado_da_fala,
)
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, selecionar_fala_observada, recuperar_evidencia_da_fala,
    formatar_evidencia_da_fala,
)


def registro_autoral(fala='Eu gosto de indie.', *, com_base=True):
    url='https://exemplo.test/descricao'
    trecho='Esta descrição vale somente no cenário simulado.'
    base=FundamentoCriterioAutoral(hashlib.sha256((url+'\0'+trecho).encode()).hexdigest(),
        'indie',url,trecho,time.time()+600) if com_base else None
    proposta=CriterioAutoralEmissao('origem','você gosta de indie?',fala,'curiosidade','a'*64,base)
    return registrar_fala_observada(None,ocorrencia_id='publicacao',turno_id='origem',
        fala=fala,resultados=(),canal='texto_publicado',criterio_autoral=proposta)


def decodificar(prompt):
    assert prompt.startswith('EVIDÊNCIA HISTÓRICA DA PRÓPRIA FALA: ')
    return json.loads(prompt.split(': ',1)[1].split('\n',1)[0])


@pytest.mark.parametrize('fala', ['Eu gosto de indie.','Eu prefiro linux.','Eu prefiro chá.'])
@pytest.mark.parametrize('com_base',[False,True])
def test_projecao_historica_transporta_descricao_sem_serializar_credencial_nativa(fala,com_base):
    registro=registro_autoral(fala,com_base=com_base)
    mente={'registro_semantico':registro}
    texto='Quando disse "'+fala+'", por que aconteceu?'
    evidencia=recuperar_evidencia_da_fala(texto,mente)
    assert len(evidencia['falas'])==1
    assert type(evidencia['falas'][0]['criterio_autoral']) is CriterioAutoralPublicado
    prompt=formatar_evidencia_da_fala(texto,mente)
    descritiva=decodificar(prompt)
    observada=descritiva['falas'][0]
    assert observada['id']=='publicacao' and observada['turno_id']=='origem' and observada['fala']==fala
    criterio=observada['criterio_autoral']
    assert type(criterio) is dict and criterio['codigo']=='curiosidade'
    assert not criterio['prova_factual'] and not criterio['prova_causal'] and not criterio['autoriza_execucao']
    assert not descritiva['autoriza_execucao']
    if com_base:
        assert criterio['fundamento']['trecho']=='Esta descrição vale somente no cenário simulado.'
        assert not criterio['fundamento']['adequacao_avaliativa_comprovada']
    else:assert criterio['fundamento'] is None
    assert criterio_publicado_da_fala({'falas_observadas':descritiva['falas']},observada) is None
    assert criterio_publicado_da_fala(registro,selecionar_fala_observada(registro)) is not None


def test_prompt_nao_muda_snapshot_nativo_nem_receipts_da_publicacao():
    from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
    recibo=ResultadoAcao(intent='APP_OPEN',alvo='calculadora',status='simulado_sem_efeito',
        executou=False,confirmado=False,origem='executor',id_solicitacao='simulacao')
    fala='Eu prefiro linux.'
    proposta=CriterioAutoralEmissao('origem','você prefere Windows ou Linux?',fala,'simplicidade','b'*64)
    registro=registrar_fala_observada(None,ocorrencia_id='publicacao',turno_id='origem',fala=fala,
        resultados=(recibo,),canal='texto_publicado',criterio_autoral=proposta)
    anterior=selecionar_fala_observada(registro)
    fonte=anterior['criterio_autoral']
    prompt=formatar_evidencia_da_fala('Quando disse "'+fala+'", houve efeito?',{'registro_semantico':registro})
    descricao=decodificar(prompt)['falas'][0]
    assert descricao['resultados'][0]['id_solicitacao']=='simulacao'
    assert descricao['resultados'][0]['executou'] is False and descricao['resultados'][0]['confirmado'] is False
    descricao['criterio_autoral']['codigo']='afinidade_estetica'
    assert type(selecionar_fala_observada(registro)['criterio_autoral']) is CriterioAutoralPublicado
    assert selecionar_fala_observada(registro)['criterio_autoral'] == fonte
    assert fonte.codigo=='simplicidade' and anterior['resultados'][0]['executou'] is False


def test_projecao_nao_adota_tipo_desconhecido_como_texto_de_prova():
    @dataclass
    class PropostaSemContrato:
        prova_factual: bool=True
    registro=registro_autoral()
    registro['falas_observadas'][0]['anexo_sem_contrato']=PropostaSemContrato()
    with pytest.raises(TypeError):
        formatar_evidencia_da_fala('Quando disse "Eu gosto de indie.", por quê?',{'registro_semantico':registro})


def test_controle_fala_sem_anexo_nativo_ja_passa_pela_projecao_historica():
    registro=registrar_fala_observada(None,ocorrencia_id='simples',turno_id='anterior',
        fala='O texto continua disponível.',resultados=(),canal='texto_publicado')
    prompt=formatar_evidencia_da_fala('Quando disse "O texto continua disponível.", por quê?',{'registro_semantico':registro})
    assert decodificar(prompt)['falas'][0]['id']=='simples'


def test_controle_persistencia_ja_descreve_anexo_e_recuperacao_conserva_owner_nativo():
    from mente_laylay.memoria_mental.registro_semantico import projetar_registro_semantico_persistivel
    registro=registro_autoral()
    descrito=json.loads(json.dumps(projetar_registro_semantico_persistivel(registro)))
    assert descrito['falas_observadas'][0]['criterio_autoral']['codigo']=='curiosidade'
    recuperada=recuperar_evidencia_da_fala('Quando disse "Eu gosto de indie.", por quê?',{'registro_semantico':registro})
    assert type(recuperada['falas'][0]['criterio_autoral']) is CriterioAutoralPublicado
    assert criterio_publicado_da_fala(registro,selecionar_fala_observada(registro))


def test_composicao_instalada_continua_envio_generico_apos_publicar_criterio(tmp_path):
    import os,subprocess,sys
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
from mente_laylay.cognicao.criterio_autoral import CriterioAutoralPublicado
passos=[]
rascunho='Não registrei uma relação entre essa descrição e o critério.'
for pergunta in ['você gosta de indie?','você prefere Windows ou Linux?','você prefere chá ou café?']:
    root._resposta_ia_runtime.processar(pergunta,origem='teste_projecao')
    nativas=estado.snapshot()['mental']['registro_semantico']['falas_observadas']
    assert type(nativas[-1]['criterio_autoral']) is CriterioAutoralPublicado
    antes_http=len(envios);antes_falas=len(falas)
    root._resposta_ia_runtime.processar('essa descrição justifica o seu critério?',origem='teste_projecao')
    passos.append({'pergunta':pergunta,'envios':envios[antes_http:],'falas':falas[antes_falas:]})
sys.__stdout__.write('PROJECAO_JSON='+json.dumps({'passos':passos,'efeitos':efeitos,'voz':False},ensure_ascii=False,default=str)+'\\n')
'''
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path),'[]'],
        cwd=Path(__file__).resolve().parents[2],env=dict(os.environ,PYTHONIOENCODING='utf-8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=90)
    assert r.returncode==0,r.stdout[-2000:]+r.stderr[-1500:]
    d=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('PROJECAO_JSON=')))
    assert not d['efeitos'] and not d['voz']
    for passo in d['passos']:
        assert passo['envios'],passo
        assert len(passo['falas'])==1,passo
        conteudo='\n'.join(m['content'] for m in passo['envios'][0]['messages'])
        # O preparador pode escolher uma projeção histórica fechada depois
        # de construir o contexto. Esta prova é de continuidade de envio e
        # publicação; o conteúdo descritivo é conferido na fronteira acima.
        assert 'CriterioAutoralPublicado(' not in conteudo
