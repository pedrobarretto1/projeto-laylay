"""Sonda finita instalada: sensores/modelo/voz reais, nenhuma tração concedida."""
import json
import os
from pathlib import Path
import sys
import threading
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))


def main():
    os.environ.update(LAYLAY_TERMINAL_2='0',LAYLAY_MASCOT_ENABLED='0',LAYLAY_AVATAR_ATIVO='0',
        LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR='0',LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR='0')
    import laylay as root
    root.carregar_memoria()
    rosto=root._rosto_oled_runtime
    corpo=root._corpo_motor_runtime
    diretor=root._diretor_presenca_runtime
    voz=root._voz_runtime
    rosto.companhia_getter=lambda:{}
    rosto.busca_obstaculos_getter=lambda _:False
    original=rosto._escrever
    trilha=[]; amostras=[]; decisoes=[]; erros=[]; fim=threading.Event()
    def escrever(linha):
        if linha.startswith(('MOTOR ','TURN ')) or (linha.startswith('SENTRY ') and linha.split()[-2]!='0'):
            raise AssertionError('Sonda não autoriza tração nem vigia ativa')
        trilha.append(linha.split()[0])
        return original(linha)
    rosto._escrever=escrever
    def observar():
        while not fim.is_set():
            try:
                ok=rosto.sincronizar()
                d=rosto.diagnostico()
                if ok:
                    corpo.experiencias.observar_sensores(d,perfil='diagnostico_sem_motores')
                amostras.append({'ts':time.time(),'ok':ok,'motivo':d.get('motivo'),
                    'sessao':d.get('sessao'),'sensores':d.get('sensores'),'imu':d.get('imu')})
            except Exception as e:
                erros.append(type(e).__name__+':'+str(e))
            fim.wait(.2)
    thread=threading.Thread(target=observar,daemon=True)
    thread.start()
    conclusao_voz=[]
    try:
        prazo=time.monotonic()+45
        while time.monotonic()<prazo:
            r=diretor.executar_ciclo()
            if r.get('status')!='observando':
                decisoes.append(r)
            fim.wait(2)
        # Prova separada de disponibilidade do áudio, sem inventar evento
        # corporal se a montagem ficou quieta durante todo o ensaio.
        if not any(d.get('proposta_comunicativa',{}).get('agendada') for d in decisoes):
            voz.falar('Teste de voz da Laylay.',_ao_concluir_entrega=lambda ok,motivo:conclusao_voz.append(
                {'entregue':ok,'motivo':motivo}))
        espera=time.monotonic()+35
        while not conclusao_voz and time.monotonic()<espera and not decisoes:
            fim.wait(.3)
    finally:
        fim.set();thread.join(5)
        with voz.proativa_lock:
            itens=list(voz.proativa_buffer);voz.proativa_buffer=[]
            if voz.proativa_timer is not None:voz.proativa_timer.cancel()
        voz._concluir_itens_proativos(itens,False,'fim_sonda',voz.log)
        rosto.encerrar()
        resultado={'tipo':'sonda_instalada_sensores_e_voz_reais','eventos_fabricados':False,
            'amostras':amostras,'decisoes':decisoes,'voz_diagnostico':conclusao_voz,
            'erros':erros,'comandos':sorted(set(trilha)), 'motores_enviados':0,
            'porta_produtor_instalada':diretor.candidato_observado_getter==corpo.experiencias.candidato_presenca,
            'presenca':root._estado_compartilhado_runtime.mental.get('presenca_contextual'),
            'voice':voz.voice,'ui_aberta':False,'conexao_encerrada':not rosto.diagnostico().get('conectado')}
        Path(__file__).with_name('marcos_runtime.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2,default=str),encoding='utf8')
        root._encerrar_laylay()
        print('SONDA_FINALIZADA '+json.dumps({'amostras':len(amostras),'decisoes':len(decisoes),
            'voz_diagnostico':conclusao_voz,'erros':erros},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
