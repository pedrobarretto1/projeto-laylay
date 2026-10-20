"""Root e modelo reais; observação controlada, sem hardware/voz/GUI.

Mede publicação -> cognição -> autoria -> fila. Não representa manuseio real
nem confirma áudio. Nenhuma preferência ou peso de modelo é alterado.
"""
import json
import os
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))


def main():
    from mente_laylay.integracao import instancia_unica
    adquirir=instancia_unica.adquirir_instancia_unica
    instancia_unica.adquirir_instancia_unica=lambda nome,**k:adquirir(str(nome)+'.latencia-'+str(os.getpid()),**k)
    import laylay as root
    from scripts.tests.test_porteiro_proatividade import TimerControlado
    d=root._diretor_presenca_runtime
    p=root._corpo_motor_runtime.experiencias
    v=root._voz_runtime
    p.aprendizado=None
    root._motor_iniciativa_runtime.ativar_perfil_seguro_padrao()
    v.timer_factory=TimerControlado
    v.worker_started=True
    instante={}; resultado={}; pronto=threading.Event(); concluiu=threading.Event()
    diag={'aplicacao_confirmada':True,'sessao':'diagnostico-latencia','imu':{
        'origem':'imu_esp','recente':True,'autoriza_execucao':False,
        'manuseio':'INCLINADA','fase_manuseio':'DESCONFIADA','evento_manuseio':1}}
    p.diagnostico_getter=lambda:diag
    original=d.candidato_observado_getter
    def candidato():
        pronto.set()
        return original()
    d.candidato_observado_getter=candidato
    cogitar=d.processar_evento_cognitivo
    def cognicao(e):
        instante['cognicao']=time.perf_counter()
        return cogitar(e)
    d.processar_evento_cognitivo=cognicao
    modelo=root._resposta_evento_runtime.modelo_llm
    def gerar(pedido):
        instante['modelo_inicio']=time.perf_counter()
        resultado['prompt_chars']=sum(len(str(m.get('content',''))) for m in pedido.mensagens)
        r=modelo.executar(pedido)
        instante['modelo_fim']=time.perf_counter()
        resultado['modelo_sucesso']=r.sucesso
        resultado['rota']=r.rota
        return r
    root._resposta_evento_runtime.modelo_llm=SimpleNamespace(executar=gerar)
    processar=d.processar_proposta_comunicativa
    def proposta(*a,**k):
        try:
            r=processar(*a,**k);resultado['proposta']=r
            instante['proposta_fim']=time.perf_counter()
            return r
        finally:concluiu.set()
    d.processar_proposta_comunicativa=proposta
    thread=threading.Thread(target=d.executar,daemon=True);thread.start()
    try:
        assert pronto.wait(2)
        instante['publicacao']=time.perf_counter()
        p.observar_inercial(diag,perfil='diagnostico_sem_hardware')
        resultado['concluiu']=concluiu.wait(40)
        resultado['instalacao_sinal']=d.notificacao_observada is p.notificacao_observada
        resultado['fila']=len(v.proativa_buffer)
        resultado['tempos_s']={k:round(t-instante['publicacao'],4) for k,t in instante.items()}
        resultado['sem_hardware_sem_audio']=True
    finally:
        d.encerrar();thread.join(3)
        with v.proativa_lock:
            itens=list(v.proativa_buffer);v.proativa_buffer=[]
        v._concluir_itens_proativos(itens,False,'fim_diagnostico_latencia',v.log)
        Path(__file__).with_name('latencia_observada.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2,default=str),encoding='utf8')
        print('LATENCIA '+json.dumps(resultado,ensure_ascii=False,default=str),flush=True)


if __name__=='__main__':main()
