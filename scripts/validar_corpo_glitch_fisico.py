"""Validação instalada com transporte real, pulsos autorizados e erro controlado.

Não mede giro/deslocamento. A falha visual é uma exceção da demonstração,
não um receipt inventado de uma habilidade externa. --demo alterna fala/glitch.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from threading import Event, Thread


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    import laylay as root
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    runtime = root._rosto_oled_runtime
    pela_rede = runtime.diagnostico().get("transporte") == "tcp"
    if args.demo and pela_rede:
        raise ValueError("As demonstrações locais são exclusivas da USB; use sem --demo para validar Wi-Fi.")
    abrir = runtime.abrir_tcp if pela_rede else runtime.abrir_serial
    enviados, recebidos = [], []
    class PortaObservada:
        def __init__(self, porta):
            self.porta = abrir(porta)
            self.buffer = bytearray()
        def write(self, dados):
            enviados.append(dados.decode("ascii").strip())
            return self.porta.write(dados)
        def read(self, tamanho):
            dados = self.porta.read(tamanho)
            self.buffer.extend(dados)
            while b"\n" in self.buffer:
                linha, _, resto = self.buffer.partition(b"\n")
                self.buffer = bytearray(resto)
                recebidos.append(linha.decode("ascii", errors="replace").strip())
            return dados
        def close(self):
            self.porta.close()
    if pela_rede:
        runtime.abrir_tcp = PortaObservada
    else:
        runtime.abrir_serial = PortaObservada
    pasta = Path(__file__).resolve().parents[1]
    instante = datetime.now(timezone.utc)
    prova = {"ts_utc": instante.isoformat(), "composicao_instalada": True,
             "hardware_simulado": False, "entrega_de_voz": False,
             "transporte": "tcp" if pela_rede else "serial",
             "prova_rotacao": False, "prova_optica": False,
             "autorizacao": "Pedro autorizou integração e testes dos motores de bancada sem rodas",
             "fonte_sha256": hashlib.sha256((pasta / "firmware/rosto_laylay/rosto_laylay.ino").read_bytes()).hexdigest(),
             "enviados": enviados, "recebidos": recebidos, "acoes": []}
    destino = pasta / ("artifacts/rosto_oled/wifi" if pela_rede else "artifacts/rosto_oled/glitch_boca") / f"receipt_fisico_{instante:%Y%m%d_%H%M%S}.json"
    parar_servico = Event()
    servico = None
    try:
        if pela_rede:
            # A composicao importa o servico, mas o import sozinho nao inicia
            # seu heartbeat. Reproduzir o executar() registrado em producao.
            servico = Thread(target=lambda: runtime.executar(deve_parar=parar_servico.is_set,
                                                            aguardar_fn=parar_servico.wait), daemon=True)
            servico.start()
            prazo = time.monotonic() + 10
            while not runtime.diagnostico()["aplicacao_confirmada"] and time.monotonic() < prazo:
                time.sleep(.1)
            prova["heartbeat_real_ativo"] = True
        assert runtime.sincronizar(), runtime.diagnostico()
        assert root._corpo_motor_runtime.diagnostico()["disponivel"]
        prova["porta"] = runtime.diagnostico()["porta_ativa"]
        ciclo = root._composicao_ciclo_comandos_runtime.ciclo
        for texto in ("ande para frente", "ande para trás", "vire para a esquerda", "vire para a direita", "pare os motores"):
            root._estado_compartilhado_runtime.atualizar_campos("mental", turno_atual=classificar_modalidade_turno(texto))
            pedido, rota = ciclo.resolver_comando_natural(texto, "validacao_corpo_fisico")
            assert pedido, rota
            pedido.setdefault("params", {})["_execucao_silenciosa"] = True
            retorno = ciclo.executar_intencao(pedido, texto)
            tratamento = dict(pedido.get("_laylay_tratamento_operacional") or {})
            prova["acoes"].append({"texto": texto, "rota": rota, "retorno": retorno, "tratamento": tratamento,
                                   "receipt": root._estado_compartilhado_runtime.obter_copia("mental", "corpo_motor", {})})
            assert tratamento.get("confirmado") is True, tratamento
            print(texto + ": receipt corporal confirmado", flush=True)
            time.sleep(1.0)
        def falha_controlada():
            raise RuntimeError("falha_controlada_da_demonstracao_visual")
        try:
            root._atividade_operacional_runtime.executar(falha_controlada)
        except RuntimeError:
            pass
        assert runtime.sincronizar(), runtime.diagnostico()
        assert runtime.diagnostico()["glitch"]["aplicacao_confirmada"]
        prova["glitch_excecao_controlada"] = runtime.diagnostico()["glitch"]
        prova["falha_de_habilidade_externa_real"] = False
        print("Glitch: GACK após exceção controlada observada", flush=True)
        if args.demo:
            prova["demos"] = []
            for comando in ("DEMO_FALA", "DEMO_GLITCH", "DEMO_FALA", "DEMO_GLITCH"):
                with runtime._lock:
                    runtime._escrever(comando)
                    assert runtime._esperar(f"{comando} 1 ATIVA", 1.0)
                prova["demos"].append(comando)
                print(comando + " ativo por 16 s; motores cortados pelo firmware", flush=True)
                time.sleep(16)
            runtime._ultimo_ack = float("-inf")
            assert runtime.sincronizar()
        prova["confirmado"] = True
    except Exception as erro:
        prova["erro"] = type(erro).__name__ + ":" + str(erro)
        raise
    finally:
        prova["parada_final"] = runtime.parar_corpo()
        parar_servico.set()
        if servico is not None:
            servico.join(5)
            prova["heartbeat_encerrado"] = not servico.is_alive()
        runtime.encerrar()
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(prova, ensure_ascii=False, indent=2), encoding="utf-8")
        print(str(destino), flush=True)


if __name__ == "__main__":
    main()
