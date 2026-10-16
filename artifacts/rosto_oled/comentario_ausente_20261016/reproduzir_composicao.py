"""Reprodução da composição real com episódio histórico; sem USB/voz/motores."""
import json
from pathlib import Path
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))

def main():
    import laylay as app
    db=sqlite3.connect('file:memoria/laylay_memoria.sqlite?mode=ro',uri=True)
    ts,contexto=db.execute("select criado_em,contexto_json from aprendizado_eventos where chave like 'corpo_inercial:%' and contexto_json like '%DESCONFIADA%' order by id desc limit 1").fetchone()
    e=json.loads(contexto)['experiencia']
    dados={'origem':'experiencia_corporal','dominio':'corpo','categoria':'companhia',
        'conteudo':'Meu corpo permaneceu inclinado por mais de um segundo.',
        'evidencias':['Meu corpo permaneceu inclinado por mais de um segundo.'],
        'observacao_corporal':{'sessao':e['sessao'],'evento_manuseio':e['evento_manuseio'],
            'fase_manuseio':e['fase_manuseio'],'autoriza_execucao':False,
            'relato_de_episodio_recente':True},
        'timestamp':time.time(),'confianca':.94,'utilidade':80,
        'executavel':False,'autoriza_execucao':False}
    d=app._diretor_presenca_runtime
    evento=d._evento_cognitivo(dados,dominio='corpo',categoria='companhia',chave='replay_diagnostico',agora=time.time())
    turno=app._composicao_turno_runtime.iniciar(evento,origem='presenca')
    cf=turno.get('contrato_fala') or {}
    resultado={'head':__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'historico_original_em':ts,'replay_offline':True,'turno':{k:turno.get(k) for k in ('natureza_entrada','autoriza_execucao','publicacao_evento_confirmada')},
        'contrato':cf,'contexto_iniciativa':app._contexto_motor_iniciativa(),
        'proibidos':{'usb_aberto':False,'motores':False,'fila_de_voz':False}}
    transporte=app._composicao_inteligencia_externa_runtime._transporte
    resultado['cliente_bloqueia_evento']=transporte.interacao_ativa()
    if resultado['cliente_bloqueia_evento']:
        from mente_laylay.integracao.registro_conversa_llm import RequisicaoTransporteLLM
        r=transporte.executar(RequisicaoTransporteLLM(payload={'messages':[
            {'role':'system','content':'Evento corporal de diagnóstico, sem execução.'}]},
            tipo_chamada='presenca_evento',prioridade_interativa=False,permitir_durante_interacao=False))
        resultado['resultado_transporte']={'sucesso':r.sucesso,'rota':r.rota}
    elif '--depois' in sys.argv:
        # Reapresentação histórica offline. O sink captura a proposta; não há
        # validador de leitura viva ou entrega física fingindo conexão atual.
        capturadas=[]
        autor=app._resposta_evento_runtime
        autor.agendar_fala_proativa=lambda *a,**kw:capturadas.append({'args':a,'tipo':kw.get('tipo')}) or True
        chamadas=[]
        post=transporte.post_chat
        def observado(*a,**kw):
            payload=kw.get('json') or (a[0] if a and isinstance(a[0],dict) else {})
            chamadas.append({'model':payload.get('model'),'max_tokens':payload.get('max_tokens'),
                'mensagens':len(payload.get('messages') or []),'timeout':kw.get('timeout'),
                'caracteres':sum(len(m.get('content') or '') for m in payload.get('messages',[]))})
            return post(*a,**kw)
        transporte.post_chat=observado
        inicio=time.monotonic()
        r=autor.processar(turno,dominio='corpo',categoria='companhia')
        resultado['autoria_real']={'duracao_s':time.monotonic()-inicio,'resultado':r,
            'propostas_capturadas':capturadas,'fonte':'replay_historico_offline',
            'validacao_sensor_ao_vivo':False,'emissao_fisica':False,'chamadas':chamadas}
    app._composicao_turno_runtime.concluir_evento(turno,resultado='diagnostico_sem_fala')
    nome='composicao_depois.json' if '--depois' in sys.argv else 'composicao_antes.json'
    if '--nova-tentativa' in sys.argv:nome='composicao_depois_2.json'
    Path(__file__).with_name(nome).write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'turno':resultado['turno'],'contrato':{k:cf.get(k) for k in ('funcao','autoriza_execucao','observacao_corporal','motivo_supressao_reacao')}},ensure_ascii=False))

if __name__=='__main__':main()
