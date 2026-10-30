"""Registro da fala não é segunda geração da resposta atual."""
from datetime import datetime
import json,os,subprocess,sys
from pathlib import Path


def test_composicao_diario_persiste_cinco_e_seis_sem_consumir_orcamento(tmp_path):
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo=CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]+'''
orcamento=root._orcamento_llm_turno_runtime
modelo=root._cliente_llm_runtime.servico
original=modelo.executar;chamadas=[]
def executar(pedido):
    chamadas.append({'tipo':pedido.tipo_chamada,'mensagens':pedido.mensagens})
    return original(pedido)
modelo.executar=executar
memoria=root.memoria_inteligente
for i in range(6):
    orcamento.iniciar_turno(f'conversa-{i}')
    d=orcamento.autorizar_chamada(tipo_chamada='principal');assert d.permitida
    orcamento.concluir_chamada(d,sucesso=True)
    memoria.adicionar_interacao(f'entrada {i}',f'resposta {i}')
    orcamento.finalizar_turno()
arquivo=Path(memoria.arquivo_diario).read_text(encoding='utf8')
sys.__stdout__.write('DIARIO_JSON='+json.dumps({'chamadas':chamadas,'contador':memoria.contador,
    'lote':memoria.historico_recente,'arquivo':arquivo,'budget':orcamento.diagnostico(),
    'efeitos':efeitos,'worker_novo':'Laylay-Consolidacao-Memoria' in root._composicao_servicos_runtime.catalogo_threads()})+'\\n')
'''
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path),'[]'],
        cwd=Path(__file__).resolve().parents[2],env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=40)
    assert r.returncode==0,r.stdout[-1500:]+r.stderr[-1500:]
    d=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('DIARIO_JSON=')))
    assert d['contador']==6 and len(d['lote'])==6
    assert all(f'entrada {i}' in d['arquivo'] for i in range(6))
    assert d['chamadas']==[], 'Registro diário iniciou geração auxiliar no turno da resposta.'
    assert d['budget']['chamadas_bloqueadas']==0
    assert d['budget']['chamadas_por_tipo']=={'principal':6}
    assert not d['efeitos'] and not d['worker_novo']


def test_admissao_negada_nao_gasta_retentativa_e_preserva_consolidacao_explicita(tmp_path):
    from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
    permitido=[False];chamadas=[]
    memoria=MemoriaLaylay(pasta_memoria=str(tmp_path),
        enviar_mensagem=lambda m:chamadas.append(m) or 'Resumo após a conversa.',
        agora=lambda:datetime(2026,10,28,20,0),log=lambda *_:None,
        pode_consolidar=lambda:permitido[0])
    for i in range(6):memoria.adicionar_interacao(str(i),'resposta')
    memoria.atualizar_resumo_diario()
    assert chamadas==[] and memoria.contador==6
    permitido[0]=True
    memoria.atualizar_resumo_diario()
    assert len(chamadas)==1 and memoria.contador==0
    assert memoria.resumo_do_dia=='Resumo após a conversa.'


def test_lote_adiado_maior_que_janela_nao_perde_registro_e_consolida_em_lotes(tmp_path):
    from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
    permitido=[False];pedidos=[];agora=[datetime(2026,10,28,20,0)]
    m=MemoriaLaylay(pasta_memoria=str(tmp_path),pode_consolidar=lambda:permitido[0],
        enviar_mensagem=lambda msgs:pedidos.append(msgs) or 'Resumo parcial.',
        agora=lambda:agora[0],log=lambda *_:None)
    for i in range(55):m.adicionar_interacao(f'FONTE-{i:03d}',f'resposta {i}')
    arquivo=Path(m.arquivo_diario).read_text(encoding='utf8')
    assert all(f'FONTE-{i:03d}' in arquivo for i in range(55))
    n=MemoriaLaylay(pasta_memoria=str(tmp_path),pode_consolidar=lambda:permitido[0],
        enviar_mensagem=lambda msgs:pedidos.append(msgs) or 'Resumo parcial.',
        agora=lambda:agora[0],log=lambda *_:None)
    assert n.contador==55 and len(n.historico_recente)==55
    permitido[0]=True;n.atualizar_resumo_diario()
    assert len(pedidos)==1 and 'FONTE-049' in pedidos[0][0]['content']
    assert 'FONTE-050' not in pedidos[0][0]['content']
    assert n.contador==5 and len(n.historico_recente)==5
    assert 'FONTE-050' in Path(n.arquivo_diario).read_text(encoding='utf8')
