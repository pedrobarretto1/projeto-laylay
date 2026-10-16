"""Ensaio limitado da composição instalada; USB/IMU/voz reais, sem motores."""
import json
from pathlib import Path
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def main():
    import laylay as app
    # Autorização humana deste ensaio finito, sem iniciar produtores gerais.
    # Não salva preferências nem habilita executor/serviços autônomos.
    modo_anterior = app._motor_iniciativa_runtime.modo_padrao
    app._motor_iniciativa_runtime.modo_padrao = 'sugestao'
    estado_iniciativa_anterior = app._estado_compartilhado_runtime.mental.get('iniciativa_autonoma')
    rosto = app._rosto_oled_runtime
    exp = app._corpo_motor_runtime.experiencias
    diretor = app._diretor_presenca_runtime
    voz = app._voz_runtime
    registros = []
    stop = threading.Event()
    escrever = rosto._escrever

    def escrever_sem_movimento(linha):
        partes = linha.split()
        if partes[0] in {'MOTOR', 'TURN', 'DEMO'} or (
            partes[0] == 'SENTRY' and (len(partes) != 6 or partes[4] != '0')
        ):
            raise RuntimeError('ensaio_proibe_movimento:' + partes[0])
        escrever(linha)

    rosto._escrever = escrever_sem_movimento
    publicar = voz.publicar_texto_proativo_cb
    emitida = voz.registrar_fala_emitida_cb

    def texto(*args, **kwargs):
        registros.append({'ts': time.time(), 'texto_publicado': args, 'kw': kwargs})
        return publicar(*args, **kwargs)

    def entregue(*args, **kwargs):
        registros.append({'ts': time.time(), 'receipt_fala_emitida': args, 'kw': kwargs})
        return emitida(*args, **kwargs)

    voz.publicar_texto_proativo_cb = texto
    voz.registrar_fala_emitida_cb = entregue

    def ler():
        anterior = None
        while not stop.is_set():
            try:
                ok = rosto.sincronizar()
                diag = rosto.diagnostico()
                exp.observar_sensores(diag, perfil=app._corpo_motor_runtime.companhia.perfil_corporal)
                imu = diag.get('imu') or {}
                chave = (ok, diag.get('sessao'), imu.get('recente'), imu.get('manuseio'), imu.get('fase_manuseio'), imu.get('evento_manuseio'))
                if chave != anterior:
                    registros.append({'ts': time.time(), 'leitura': chave, 'erro': diag.get('erro')})
                    anterior = chave
            except Exception as exc:
                registros.append({'ts': time.time(), 'erro_leitura': repr(exc)})
            stop.wait(.12)

    thread = threading.Thread(target=ler, daemon=True)
    try:
        voz.iniciar_worker()
        thread.start()
        inicio = time.monotonic()
        while time.monotonic() - inicio < 100:
            resultado = diretor.executar_ciclo()
            if resultado != {'status': 'observando'}:
                registros.append({'ts': time.time(), 'diretor': resultado})
            stop.wait(2)
    finally:
        stop.set()
        thread.join(5)
        rosto.encerrar()
        voz.encerrar()
        app._motor_iniciativa_runtime.modo_padrao = modo_anterior
        app._estado_compartilhado_runtime.atualizar_campos('mental', iniciativa_autonoma=estado_iniciativa_anterior)
        registros.append({'ts': time.time(), 'fim': 'USB encerrada; nenhum serviço de companhia iniciado'})
        nome = 'ensaio_vivo_voz.json' if '--voz' in sys.argv else 'ensaio_vivo.json'
        Path(__file__).with_name(nome).write_text(json.dumps(registros, ensure_ascii=False, indent=2, default=str), encoding='utf8')


if __name__ == '__main__':
    main()
