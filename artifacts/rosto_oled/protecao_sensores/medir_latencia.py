"""Medição no ESP real sem comandos de motor; amostra fria e olhos acordados."""
import sys, time, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import serial
linhas=[]
modo=sys.argv[1] if len(sys.argv)>1 else 'parado'
with serial.Serial('COM4',115200,timeout=.05,write_timeout=.5) as s:
    s.write(b'STOP\n'); time.sleep(.15); s.reset_input_buffer()
    for acordada in (False,True):
        if acordada: s.write(b'HELLO 1 aabbaabb\n')
        inicio=time.monotonic(); seq=0; nextface=0; nextperf=0
        while time.monotonic()-inicio<4:
            agora=time.monotonic()-inicio
            if acordada and agora>=nextface:
                seq+=1; s.write(f'FACE 1 aabbaabb {seq} 0 1 0 3500\n'.encode()); nextface=agora+.5
            if agora>=nextperf:
                s.write(b'PERF\n'); s.write(f'DIST 1 {seq+1}\n'.encode()); nextperf=agora+1
            if modo=='reflexo' and acordada and seq==1 and agora<.1:
                s.write(b'MOTOR 1 aabbaabb 1 140 140 3000\n')
                modo='enviado' # Uma ordem apenas; mantém os heartbeats sem retentar.
            l=s.readline().decode('ascii',errors='replace').strip()
            if l.startswith(('PERF','DIST')):
                linhas.append({'acordada':acordada,'t':round(agora,3),'linha':l}); print(l,flush=True)
    s.write(b'STOP\nGOODNIGHT 1 aabbaabb 1\n')
(Path(__file__).parent/('latencia_reflexo.json' if modo=='enviado' else 'latencia_atual.json')).write_text(json.dumps(linhas,indent=2),encoding='utf-8')
