"""main real, serviços e interface reais; observação corporal e fim em 65s.

Não cria concessões nem simula leituras, voz, modelo ou executores.
"""
from pathlib import Path
import json
import sys
import time

RAIZ=Path(__file__).resolve().parents[1]
DESTINO=RAIZ/"artifacts/rosto_oled/admissao_motor_reflexo"
sys.path.insert(0,str(RAIZ))
import laylay

c=laylay._corpo_motor_runtime.companhia
r=laylay._rosto_oled_runtime
inicio=time.monotonic();registros=[];ultimo=None
processar=c.processar
def observar():
    global ultimo
    retorno=processar()
    d=r.diagnostico();a=c.diagnostico()
    p=(d.get("sensores") or {}).get("protecao") or {}
    chave=(a["ativa"],a["motivo"],retorno.get("ok"),retorno.get("motivo"),
        p.get("incidente_id"),p.get("fase"),p.get("risco"),p.get("vigia_ativa"))
    if chave!=ultimo:
        registros.append({"t":round(time.monotonic()-inicio,3),"companhia":a,"retorno":retorno,
            "transporte":d,"experiencia":laylay._estado_compartilhado_runtime.obter_copia("mental","experiencia_corporal",{})})
        ultimo=chave
    return retorno
c.processar=observar
manter=laylay._inicializacao_runtime.manter_ativo
def manter_limitado(**kwargs):
    prazo=time.monotonic()+65
    original=kwargs.get("deve_encerrar")
    kwargs["deve_encerrar"]=lambda:time.monotonic()>=prazo or (bool(original()) if original else False)
    return manter(**kwargs)
laylay._inicializacao_runtime.manter_ativo=manter_limitado
try:
    laylay.main()
finally:
    # O encerramento normal já chama o owner; a guarda cobre falha de startup.
    laylay._encerrar_laylay()
    final={"companhia":c.diagnostico(),"transporte":r.diagnostico()}
    (DESTINO/"main_real.json").write_text(json.dumps({"registros":registros,"final":final,
        "main_real":True,"prova_deslocamento":False},ensure_ascii=False,indent=2),encoding="utf-8")
    print("DIAGNOSTICO_MAIN_ENCERRADO",flush=True)
