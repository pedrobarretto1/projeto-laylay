"""Composition root real, perfil privado, receipt do navegador simulado e voz vedada."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from scripts.tests.instalacao_privada import isolar_base_do_codigo
from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY


CODIGO = CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
CODIGO = CODIGO.replace(
    'coordenador_intencao.executar_intencao=roteador_intencao.executar_intencao=lambda *a,**k:efeitos.append(str(a))or False',
    '# Dispatcher real preservado; só a fronteira externa é simulada.',
)
CODIGO += '''
from copy import deepcopy
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
url='https://www.youtube.com/watch?v=cxSzri346W0'
assert root._playlist_runtime.save({'alternativo':[{'url':url,'titulo':'Faixa simulada'}]})
assert root._operacoes_musicais_runtime.playlist_state is root._playlist_runtime.playlist_state
chamadas=[];receipts=[];estado_antes=deepcopy(dict(root._playlist_runtime.playlist_state))
def navegador(action,payload):
    assert action=='youtube_play', ('efeito inesperado',action,payload)
    chamadas.append((action,deepcopy(payload)))
    return {'ok':False,'confirmado':False,'status':casos.get('status','playing_muted'),
        'request_id':'browser-simulado','tab':{'id':42,'url':url},
        'evidence':{'playing':True,'audible':False,'muted':True,'volume':1}}
root._chrome_comandos_runtime.enviar_detalhado=navegador
servicos=root._contexto_intencao_runtime._servicos_estaticos
vincular=servicos['_vincular_registro_resultado_execucao']
def observar_vinculo():
    registrar=vincular()
    def observar(receipt,*a,**k):
        receipts.append(receipt)
        return registrar(receipt,*a,**k)
    return observar
# Delega ao registro vinculado da ocorrência real, sem substituir sua decisão.
servicos['_vincular_registro_resultado_execucao']=observar_vinculo
root._resposta_ia_runtime.processar(casos.get('pedido','coloca a playlist alternativo'),origem='desktop')
sys.__stdout__.write('PLAYLIST_JSON='+json.dumps({
    'falas':falas,'http':len(envios),'chamadas':chamadas,
    'estado':root._playlist_runtime.playlist_state,'estado_antes':estado_antes,
    'receipts':[r.como_dict() if isinstance(r,ResultadoAcao) else r for r in receipts],
    'mental':estado.mental,'voz':False},ensure_ascii=False,default=str)+'\\n')
'''
CODIGO = isolar_base_do_codigo(CODIGO)


def coletar(tmp_path, caso):
    resultado = subprocess.run(
        [sys.executable, '-B', '-c', CODIGO, str(tmp_path), json.dumps(caso,ensure_ascii=False)],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=60,
    )
    assert resultado.returncode == 0, resultado.stdout[-5000:] + resultado.stderr[-3500:]
    dados = json.loads(next(l.split('=',1)[1] for l in resultado.stdout.splitlines() if l.startswith('PLAYLIST_JSON=')))
    (tmp_path / 'resultado.json').write_text(json.dumps(dados,ensure_ascii=False,indent=2),encoding='utf8')
    return dados


@pytest.mark.parametrize('pedido', ['coloca a playlist alternativo', 'toca a playlist alternativo'])
def test_publicacao_preserva_parcial_sem_confirmar_audio(tmp_path, pedido):
    dados = coletar(tmp_path, {'pedido':pedido})
    assert len(dados['chamadas']) == 1
    assert dados['estado']['name'] == 'alternativo'
    assert dados['estado']['last_play_confirmed'] is False
    assert dados['receipts'], dados
    receipt = dados['receipts'][-1]
    assert receipt['executou'] is True and receipt['confirmado'] is None
    aspectos = {a['escopo']:a for a in receipt['aspectos']}
    assert aspectos['início da reprodução do vídeo']['confirmado'] is True
    assert aspectos['áudio audível']['confirmado'] is None
    assert all(a['id_solicitacao']==receipt['id_solicitacao'] for a in aspectos.values())
    assert len(dados['falas']) == 1
    assert 'início da reprodução do vídeo' in dados['falas'][0]
    assert 'áudio audível' in dados['falas'][0]
    assert dados['http'] == 0 and dados['voz'] is False


def test_falha_real_nao_publica_aspectos_de_execucao(tmp_path):
    dados = coletar(tmp_path, {'status':'error'})
    assert len(dados['chamadas']) == 1
    receipt = dados['receipts'][-1]
    assert receipt['executou'] is False and receipt['confirmado'] is False
    assert not receipt.get('aspectos')
    assert dados['estado'] == dados['estado_antes']
    assert len(dados['falas']) == 1


def test_negacao_nao_autoriza_reproducao_parcial(tmp_path):
    dados = coletar(tmp_path, {'pedido':'não toca a playlist alternativo'})
    assert dados['chamadas'] == []
    assert not any(r.get('executou') for r in dados['receipts'])
