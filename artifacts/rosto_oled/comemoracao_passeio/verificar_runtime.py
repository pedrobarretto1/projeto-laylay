"""Instrumenta callbacks reais na COM4; não substitui transporte ou receipt."""
import json
import os
import sys
import threading
import time
from pathlib import Path

raiz = Path(__file__).resolve().parents[3]
os.chdir(raiz)
sys.path.insert(0, str(raiz))
os.environ["LAYLAY_ROSTO_PORTA"] = "COM4"
import laylay as root
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno

eventos = []
aplicacao = "--aplicacao" in sys.argv
if aplicacao:
    sys.argv.remove("--aplicacao")
def registrar(evento):
    eventos.append(evento)
    if aplicacao and ("etapa" in evento or "gesto" in evento):
        with Path(__file__).with_name("trace_aplicacao.jsonl").open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(evento, ensure_ascii=False) + "\n")
rosto, corpo = root._rosto_oled_runtime, root._corpo_motor_runtime
original_escrever = rosto._escrever
def escrever(linha):
    eventos.append({"em": time.monotonic(), "serial": linha})
    return original_escrever(linha)
rosto._escrever = escrever
coordenador = corpo.companhia.coordenador
original_gesto = coordenador.executar_gesto_corporal
def observar_gesto(meta, confirmar_rosto, executar_motor):
    def observar_callback(nome, callback):
        retorno = callback()
        registrar({"em": time.monotonic(), "etapa": nome, "retorno": retorno})
        return retorno
    retorno = original_gesto(meta, lambda: observar_callback("rosto", confirmar_rosto),
                             lambda: observar_callback("motor", executar_motor))
    registrar({"em": time.monotonic(), "gesto": meta["gesto"], "resultado": retorno,
               "idade_proposta_s": time.monotonic() - meta["proposto_em"],
               "rosto": rosto.diagnostico(), "atividade": root._atividade_operacional_runtime.retrato(),
               "ultima_etapa": coordenador.quadro.snapshot()["planos_recentes"][-1]})
    return retorno
coordenador.executar_gesto_corporal = observar_gesto
if aplicacao:
    root.main()
    sys.exit(0)
parar = threading.Event()
supervisor = threading.Thread(target=lambda: rosto.executar(
    deve_parar=parar.is_set, aguardar_fn=parar.wait), daemon=True)
try:
    assert rosto.sincronizar()
    supervisor.start()
    texto = "ative modo passeio na mesa com barreiras"
    ciclo = root._composicao_ciclo_comandos_runtime.ciclo
    root._estado_compartilhado_runtime.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
    pedido, _ = ciclo.resolver_comando_natural(texto, "verificacao_a_pedido_pedro")
    assert pedido and ciclo.executar_intencao(pedido, texto)
    inicio = time.monotonic()
    consultou = False
    while time.monotonic() - inicio < 30:
        if not consultou and time.monotonic() - inicio > 12:
            consultou = True
            texto = "liste os dispositivos"
            root._estado_compartilhado_runtime.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
            pedido, _ = ciclo.resolver_comando_natural(texto, "verificacao_leitura")
            assert pedido and ciclo.executar_intencao(pedido, texto)
        corpo.companhia.processar()
        time.sleep(.2)
finally:
    diagnostico = corpo.diagnostico()
    corpo.companhia.revogar("fim_da_consulta_instrumentada")
    parada = rosto.parar_corpo()
    parar.set()
    supervisor.join(3)
    rosto.encerrar()
    Path(__file__).with_name("receipt_runtime.json").write_text(json.dumps({
        "eventos": eventos, "diagnostico_final": diagnostico, "parada": parada,
        "observacao_fisica_humana": False,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
