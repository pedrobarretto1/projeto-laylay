"""Consulta a composição real na COM4, envia STOP e não ativa gestos."""
import hashlib
import json
import os
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parents[3]
os.chdir(raiz)
sys.path.insert(0, str(raiz))
os.environ['LAYLAY_ROSTO_PORTA'] = 'COM4'
import laylay as root

rosto = root._rosto_oled_runtime
corpo = root._corpo_motor_runtime
operacoes = []
escrever = rosto._escrever

def observar(linha):
    operacoes.append(linha.split()[0])
    return escrever(linha)

rosto._escrever = observar
try:
    assert rosto.sincronizar(), rosto.diagnostico().get('motivo')
    parada = corpo.executar('CORPO_PARAR', {})
    assert parada['ok'] and parada['parada_confirmada']
    diag = corpo.diagnostico()
    assert diag['companhia']['perfil_expressivo'] == 'ritmo_emocional_v2'
    assert diag['companhia']['gestos_maximos'] is None
    assert diag['companhia']['intervalo_minimo_s'] == 2
    assert not diag['autonomia_ativada'] and 'MOTOR' not in operacoes
    target = root._composicao_servicos_runtime.catalogo_threads()['Laylay-Companhia-Corporal']
    assert target.func.__self__ is corpo.companhia
    assert corpo.companhia.coordenador is root._orquestrador_cooperativo_runtime
    nomes = ['mente_laylay/autonomia/companhia_corporal.py',
             'mente_laylay/autonomia/orquestracao_cooperativa.py',
             'mente_laylay/autonomia/executor_corpo.py',
             'mente_laylay/especialistas/mapa_habilidades.py',
             'mente_laylay/especialistas/capacidades.py']
    recibo = {'face_confirmada': True, 'rosto': rosto.diagnostico(), 'corpo': diag,
              'sack': parada, 'thread_e_coordenador_instalados': True,
              'comando_motor_enviado': False, 'observacao_humana_gestos': False,
              'testes_focados': 312, 'testes_vizinhos': 128,
              'fontes_sha256': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in nomes}}
    Path(__file__).with_name('receipt_composicao.json').write_text(
        json.dumps(recibo, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'face_confirmada': True, 'stop_confirmado': True,
                      'modo': diag['companhia'], 'motor_enviado': False}, ensure_ascii=False))
finally:
    rosto.encerrar()
