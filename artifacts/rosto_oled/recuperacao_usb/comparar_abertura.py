"""Compara abertura padrão e sem DTR/RTS, sem HELLO/FACE/MOTOR."""
import json,time,serial
from pathlib import Path
saida=Path(__file__).resolve().parent
registros=[]
for indice,modo in enumerate(('sem_linhas','sem_linhas','padrao','padrao','sem_linhas','sem_linhas'),1):
    if modo=='padrao':
        s=serial.Serial('COM4',115200,timeout=.15)
    else:
        s=serial.Serial(port=None,baudrate=115200,timeout=.15)
        s.dtr=False; s.rts=False; s.port='COM4'; s.open()
    recebidas=[]
    try:
        limite=time.monotonic()+2
        while time.monotonic()<limite:
            s.write(f'HEALTH 1 {indice}\n'.encode())
            linhas=s.read(2000).decode(errors='replace').splitlines()
            recebidas.extend(linhas)
            if any(l.startswith(f'HEALTH 1 {indice} ') for l in linhas):break
            time.sleep(.1)
    finally:s.close()
    registros.append({'modo':modo,'linhas':recebidas})
    time.sleep(.3)
(saida/'abertura_serial.json').write_text(json.dumps(registros,indent=2),encoding='utf-8')
for r in registros:
    for l in r['linhas']:
        if l.startswith('HEALTH '):
            p=l.split();print(r['modo'],p[4:7]) # Sem imprimir identidade física.
