"""Composição instalada, seleção AUTO e reflexo real; ensaio finito autorizado."""
import json
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def main():
    import laylay as app
    app.carregar_memoria()
    r = app._rosto_oled_runtime
    c = app._corpo_motor_runtime.companhia
    registros = []
    parar = threading.Event()

    def amostrar():
        while not parar.is_set():
            ok = r.sincronizar()
            registros.append({'ts': time.time(), 'ok': ok, 'rosto': r.diagnostico(),
                              'companhia': c.diagnostico()})
            parar.wait(.15)

    thread = threading.Thread(target=amostrar, daemon=True)
    try:
        # Só ativa a concessão quando a montagem preparada pelo usuário é medida.
        prazo = time.monotonic() + 120
        while time.monotonic() < prazo:
            ok = r.sincronizar()
            registros.append({'conexao': r.diagnostico(), 'ok': ok, 'ts': time.time()})
            if ok:
                break
            time.sleep(1)
        d = r.diagnostico()
        registros.append({'inicial': d, 'companhia': c.diagnostico()})
        inferior = (d.get('sensores', {}).get('leituras', {}).get('borda') or {})
        assert d['aplicacao_confirmada'] and d['selecao_automatica_usb_wifi'], d['motivo']
        assert inferior.get('estado') == 'VALIDA' and inferior.get('mm', 999) <= 120, inferior
        thread.start()
        inicio = time.monotonic()
        while time.monotonic() - inicio < 35:
            resultado = c.processar()
            registros.append({'ts': time.time(), 'resultado': resultado, 'companhia': c.diagnostico()})
            parar.wait(.3)
    finally:
        c.revogar('fim_ensaio_sensorial_autorizado')
        parar.set()
        if thread.is_alive():
            thread.join(5)
        registros.append({'parada': r.parar_corpo()})
        r.encerrar()
        registros.append({'final': r.diagnostico(), 'companhia': c.diagnostico()})
        Path(__file__).with_name('ensaio_sensores.json').write_text(
            json.dumps(registros, ensure_ascii=False, indent=2, default=str), encoding='utf8')


if __name__ == '__main__':
    main()
