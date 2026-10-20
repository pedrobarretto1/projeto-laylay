"""Main real, ensaio finito: uma perda de EACK induzida, sem replay do gesto."""
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))


def main():
    # Preferências corporais reais permanecem; só a interface/saudação/escuta
    # ficam fora deste ensaio, que encerra todos os serviços ao final.
    os.environ.update(LAYLAY_TERMINAL_2='0',LAYLAY_MASCOT_ENABLED='0',LAYLAY_AVATAR_ATIVO='0',
        LAYLAY_MICROFONE_ATIVO='0',LAYLAY_BRIEFING_INICIAL='0',LAYLAY_FALAS_INICIAIS='0')
    import laylay as root
    rosto=root._rosto_oled_runtime
    c=root._corpo_motor_runtime.companhia
    expressar=rosto.expressar_gesto
    executar=c.processar
    injetada=[]; registros=[]; comandos=[]
    escrever=rosto._escrever
    def observar_escrita(linha):
        if linha.startswith(('MOTOR ','STOP ','SENTRY ')):
            comandos.append({'ts':time.time(),'comando':linha})
        return escrever(linha)
    rosto._escrever=observar_escrita
    def perder_confirmacao(*args,**kwargs):
        r=expressar(*args,**kwargs)
        if not injetada and len(args)>1 and args[1]==0 and kwargs.get('validar_inicio') and r.get('ok'):
            injetada.append({'ts':time.time(),'tipo':'EACK_ignorado_apenas_pelo_diagnostico',
                'nota':'render ocorreu; sem falsa confirmação de gesto/motor'})
            return {**r,'ok':False,'confirmado':False,'motivo':'sem_confirmacao_expressao','evidencia':''}
        return r
    rosto.expressar_gesto=perder_confirmacao
    def observar_companhia():
        r=executar(); d=rosto.diagnostico()
        registros.append({'ts':time.time(),'resultado':r,'companhia':c.diagnostico(),
            'sensores':d.get('sensores'),'saude':d.get('saude'),'sessao':d.get('sessao')})
        return r
    c.processar=observar_companhia
    manter=root._inicializacao_runtime.manter_ativo
    def limitado(**kwargs):
        prazo=time.monotonic()+55
        original=kwargs.get('deve_encerrar')
        kwargs['deve_encerrar']=lambda:time.monotonic()>=prazo or bool(original and original())
        return manter(**kwargs)
    root._inicializacao_runtime.manter_ativo=limitado
    sys.argv=[str(ROOT/'laylay.py')]
    try:
        root.main()
    finally:
        root._encerrar_laylay()
        resultado={'tipo':'main_real_perda_eack_induzida','injetada':injetada,
            'registros':registros,'comandos':comandos,'companhia_final':c.diagnostico(),
            'conexao_encerrada':not rosto.diagnostico().get('conectado'), 'ui_aberta':False}
        Path(__file__).with_name('recuperacao_main.json').write_text(
            json.dumps(resultado,ensure_ascii=False,indent=2,default=str),encoding='utf8')
        print('RECUPERACAO_MAIN_FINAL '+json.dumps({'injetada':bool(injetada),
            'amostras':len(registros),'conexao_encerrada':resultado['conexao_encerrada']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
