"""Observação finita do owner instalado; proíbe movimento na escrita real."""
import collections
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
DESTINO = pathlib.Path(__file__).parent


def main():
    import laylay
    from mente_laylay.especialistas.rosto_oled_runtime import _abrir_serial
    runtime = laylay._rosto_oled_runtime
    trilha = collections.deque(maxlen=100)
    erros, amostras, proibidos = [], [], []

    class Porta:
        def __init__(self, nome):
            self.serial = _abrir_serial(nome)
        def write(self, dados):
            linha = dados.decode('ascii').strip()
            if linha.startswith(('MOTOR ', 'TURN ', 'DEMO')) or (
                    linha.startswith('SENTRY ') and linha.split()[4] != '0'):
                proibidos.append(linha)
                raise AssertionError('movimento_proibido_nesta_observacao')
            trilha.append({'tx': linha})
            return self.serial.write(dados)
        def read(self, tamanho):
            dados = self.serial.read(tamanho)
            if dados:
                trilha.append({'rx': dados.decode('ascii', errors='replace')})
            return dados
        def close(self):
            self.serial.close()

    runtime.abrir_serial = Porta
    inicio = time.monotonic()
    try:
        while time.monotonic() - inicio < 60:
            ok = runtime.sincronizar()
            diag = runtime.diagnostico()
            amostras.append({'t': round(time.monotonic()-inicio, 3), 'ok': ok, 'd': diag})
            if not ok:
                erros.append({'motivo': diag.get('motivo'), 'trilha': list(trilha)})
            time.sleep(.12)
    finally:
        runtime.encerrar()
        fontes = ['firmware/rosto_laylay/imu_corporal.h',
                  'firmware/rosto_laylay/rosto_laylay.ino',
                  'mente_laylay/especialistas/rosto_oled_runtime.py']
        resultado = {'head': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                     'fontes': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in fontes},
                     'amostras': amostras, 'erros': erros, 'proibidos': proibidos,
                     'final': runtime.diagnostico(), 'ultima_trilha': list(trilha)}
        nome = 'usb_depois.json' if '--depois' in sys.argv else 'usb_antes.json'
        (DESTINO/nome).write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf8')
        print(json.dumps({'amostras': len(amostras), 'falhas': len(erros), 'proibidos': proibidos,
                          'motivos': [e['motivo'] for e in erros]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
