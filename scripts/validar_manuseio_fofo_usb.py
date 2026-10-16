"""Ensaio finito na composição instalada, sem UI, motores ou preferências novas."""
from pathlib import Path
import argparse
import json
import sys
import threading
import time

RAIZ=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(RAIZ))
DESTINO=RAIZ/'artifacts/rosto_oled/manuseio_fofo_v1'
from mente_laylay.integracao import instancia_unica
adquirir=instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica=lambda _:adquirir(DESTINO/'instancia_ensaio')


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--segundos',type=float,default=60)
    parser.add_argument('--main',action='store_true',help='Abre a aplicação real e encerra ao final')
    args=parser.parse_args()
    if not 3<=args.segundos<=180:raise SystemExit('Ensaio de 3 a 180 segundos')
    import laylay
    print('ENSAIO INICIADO: IMU, olhos, bips e presença por '+str(args.segundos)+'s; sem motores.',flush=True)
    rosto=laylay._rosto_oled_runtime
    corpo=laylay._corpo_motor_runtime
    diretor=laylay._diretor_presenca_runtime
    voz=laylay._voz_runtime
    fim=threading.Event();trilha=[];leituras=[];decisoes=[];erros=[]
    escrever=rosto._escrever
    def somente_expressao(linha):
        if linha.startswith(('MOTOR ','TURN ','SENTRY ')):
            raise AssertionError('Ensaio não concede tração ou vigia')
        trilha.append(linha);return escrever(linha)
    rosto._escrever=somente_expressao
    if args.main:
        processar=corpo.companhia.processar
        materializar=laylay._resposta_evento_runtime.processar
        def observar_companhia():
            r=processar();d=rosto.diagnostico()
            leituras.append({'ts':time.time(),'imu':d.get('imu'),'retorno':r})
            return r
        def observar_autoria(*a,**k):
            r=materializar(*a,**k)
            if k.get('dominio')=='corpo':decisoes.append(r)
            return r
        corpo.companhia.processar=observar_companhia
        laylay._resposta_evento_runtime.processar=observar_autoria
        manter=laylay._inicializacao_runtime.manter_ativo
        def limitado(**kwargs):
            prazo=time.monotonic()+args.segundos
            original=kwargs.get('deve_encerrar')
            kwargs['deve_encerrar']=lambda:time.monotonic()>=prazo or bool(original and original())
            return manter(**kwargs)
        laylay._inicializacao_runtime.manter_ativo=limitado
        sys.argv=[str(RAIZ/'laylay.py')]
        try:
            laylay.main()
        finally:
            laylay._encerrar_laylay()
            saida={'main_real':True,'leituras':leituras,'autorias':decisoes,'trilha':trilha,
                'presenca':laylay._estado_compartilhado_runtime.mental.get('presenca_contextual'),
                'governanca':laylay._motor_iniciativa_runtime.permissoes_atuais(),
                'serial_fechada':not rosto.diagnostico().get('conectado'),'motores_enviados':0}
            (DESTINO/'main_real.json').write_text(json.dumps(saida,ensure_ascii=False,indent=2,default=str),encoding='utf8')
        return
    rosto.companhia_getter=lambda:{}
    rosto.busca_obstaculos_getter=lambda _:False
    def observar():
        while not fim.is_set():
            try:
                if rosto.sincronizar():
                    d=rosto.diagnostico()
                    corpo.experiencias.observar_sensores(d,perfil='diagnostico_sem_motores')
                    leituras.append({'ts':time.time(),'imu':d.get('imu')})
                else:erros.append(rosto.diagnostico().get('motivo'))
            except Exception as erro:erros.append(type(erro).__name__+':'+str(erro))
            fim.wait(.15)
    supervisor=threading.Thread(target=observar,daemon=True)
    inicio=time.monotonic();supervisor.start()
    try:
        while time.monotonic()-inicio<args.segundos:
            # Mesmo diretor, cognição, modelo e voz. Sem liberar políticas para
            # fabricar uma fala; registrar bloqueios e separar fila de audição.
            r=diretor.executar_ciclo()
            if r.get('status')!='observando':
                decisoes.append(r)
                print(json.dumps({'presenca':r.get('status'),'motivo':r.get('motivo'),
                    'proposta':r.get('proposta_comunicativa')},ensure_ascii=False),flush=True)
            fim.wait(2)
    finally:
        fim.set();supervisor.join(timeout=4)
        with voz.proativa_lock:
            pendentes=list(voz.proativa_buffer);voz.proativa_buffer=[]
            if voz.proativa_timer is not None:voz.proativa_timer.cancel()
        voz._concluir_itens_proativos(pendentes,False,'ensaio_encerrado',voz.log)
        rosto.encerrar()
        saida={'leituras':leituras,'decisoes':decisoes,'erros':erros,'trilha':trilha,
            'presenca':laylay._estado_compartilhado_runtime.mental.get('presenca_contextual'),
            'mesmo_owner':corpo.transporte is rosto,
            'porta_produtor_instalada':diretor.candidato_observado_getter==corpo.experiencias.candidato_presenca,
            'serial_fechada':not rosto.diagnostico().get('conectado'),
            'motores_enviados':0,'ui_aberta':False}
        (DESTINO/'composicao_usb.json').write_text(json.dumps(saida,ensure_ascii=False,indent=2,default=str),encoding='utf8')
        print(json.dumps({'amostras':len(leituras),'erros':len(erros),'decisoes':len(decisoes),
            'fases':sorted({r['imu'].get('fase_manuseio','') for r in leituras}),'serial_fechada':saida['serial_fechada']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
