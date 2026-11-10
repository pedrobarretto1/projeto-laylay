"""CMD de teste: TCP autenticado existente, sem iniciar a mente da Laylay."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import queue
import sys
import threading
import time

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from mente_laylay.especialistas.corpo_wifi_transporte import (
    CAMINHO_CONFIGURACAO_WIFI, ConexaoCorpoIndisponivel, RedeLocalCorpoWindows,
    abrir_corpo_tcp, carregar_configuracao_corpo_wifi,
)


class ControleRodas:
    def __init__(self, fluxo) -> None:
        self.fluxo = fluxo
        self.seq = 0
        self.buffer = bytearray()
        self.pendentes: dict[int, tuple[str, float]] = {}
        self.estado: dict = {}
        self.trilha: list[dict] = []

    def enviar(self, acao: str) -> int:
        if acao not in {"STATUS", "FRENTE", "PARAR"}:
            raise ValueError("acao_de_teste_invalida")
        self.seq += 1
        linha = f"TESTE 1 {self.seq} {acao}\n".encode("ascii")
        if self.fluxo.write(linha) != len(linha):
            raise ConnectionError("escrita_incompleta")
        self.pendentes[self.seq] = (acao, time.monotonic() + 1.5)
        self.trilha.append({"seq": self.seq, "acao": acao})
        return self.seq

    def ler(self) -> list[tuple[int, str]]:
        self.buffer.extend(self.fluxo.read(256))
        if len(self.buffer) > 2048:
            raise ConnectionError("resposta_excessiva")
        respostas = []
        while b"\n" in self.buffer:
            linha, _, resto = self.buffer.partition(b"\n")
            self.buffer = bytearray(resto)
            p = linha.decode("ascii").strip().split()
            if len(p) < 4 or p[1] != "1" or not p[2].isdecimal():
                raise ConnectionError("firmware_nao_e_o_teste_wifi")
            seq = int(p[2])
            if seq not in self.pendentes:
                raise ConnectionError("receipt_sem_comando_correlacionado")
            acao, _ = self.pendentes.pop(seq)
            if p[0] == "TESTERROR":
                if len(p) != 4:
                    raise ConnectionError("receipt_de_erro_invalido")
                raise ConnectionError("ESP: " + p[3])
            if len(p) != 6 or not p[4].isdecimal() or not p[5].isdecimal():
                raise ConnectionError("receipt_de_teste_invalido")
            ms, pwm = int(p[4]), int(p[5])
            if not 0 <= ms <= 5000 or not 0 <= pwm <= 255:
                raise ConnectionError("limites_do_receipt_invalidos")
            if acao == "STATUS":
                if p[0] != "TESTSTATUS" or p[3] not in {"PARADO", "ANDANDO", "ERRO_PWM"}:
                    raise ConnectionError("status_invalido")
                if p[3] != "ANDANDO" and ms != 0:
                    raise ConnectionError("status_incoerente")
                self.estado = {"estado": p[3], "restante_ms": ms, "pwm": pwm}
            else:
                esperado = "FRENTE" if acao == "FRENTE" else "PARADO"
                if p[0] != "TESTACK" or p[3] != esperado or ms != (5000 if acao == "FRENTE" else 0):
                    raise ConnectionError("confirmacao_nao_corresponde_ao_comando")
                self.estado = {"estado": "ANDANDO" if acao == "FRENTE" else "PARADO",
                               "restante_ms": ms, "pwm": pwm}
            self.trilha.append({"seq": seq, "receipt": " ".join(p)})
            respostas.append((seq, acao))
        if any(time.monotonic() >= prazo for _, prazo in self.pendentes.values()):
            raise TimeoutError("ESP_nao_confirmou_comando; movimento_nao_sera_reenviado")
        return respostas

    def aguardar(self, seq: int) -> None:
        while seq in self.pendentes:
            self.ler()

    def encerrar(self) -> None:
        try:
            seq = self.enviar("PARAR")
            self.aguardar(seq)
        finally:
            self.fluxo.close()


def abrir():
    config = carregar_configuracao_corpo_wifi(CAMINHO_CONFIGURACAO_WIFI)
    if config is None:
        raise ConnectionError("Configuracao Wi-Fi do corpo ausente ou desativada.")
    print(f"Conectando ao teste em {config.endpoint}...", flush=True)
    try:
        return abrir_corpo_tcp(config)
    except ConexaoCorpoIndisponivel:
        print("Preparando a rede local ja configurada do corpo...", flush=True)
        RedeLocalCorpoWindows().preparar(config)
        prazo = time.monotonic() + 20
        while True:
            try:
                return abrir_corpo_tcp(config)
            except ConexaoCorpoIndisponivel:
                if time.monotonic() >= prazo:
                    raise
                time.sleep(.5)


def teclado(fila: queue.Queue[str]) -> None:
    while True:
        try:
            comando = input("> ").strip().upper()
        except EOFError:
            comando = "SAIR"
        fila.put(comando)
        if comando == "SAIR":
            return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="consulta e para; nao envia frente")
    args = parser.parse_args()
    controle = None
    erro = ""
    try:
        controle = ControleRodas(abrir())
        controle.aguardar(controle.enviar("STATUS"))
        print("Teste autenticado. ESP:", controle.estado, flush=True)
        if args.verificar:
            return 0
        print("F = frente por 5 segundos | S = parar | STATUS = consultar | SAIR = encerrar", flush=True)
        print("O ESP para ao perder a conexao ou o heartbeat; F nunca e repetido automaticamente.", flush=True)
        fila: queue.Queue[str] = queue.Queue()
        threading.Thread(target=teclado, args=(fila,), daemon=True).start()
        proximo_status = 0.0
        ultimo_estado = controle.estado["estado"]
        consultas_manuais: set[int] = set()
        while True:
            try:
                comando = fila.get_nowait()
            except queue.Empty:
                comando = ""
            if comando == "SAIR":
                break
            if comando == "F":
                if controle.estado.get("estado") == "ANDANDO" or any(a == "FRENTE" for a, _ in controle.pendentes.values()):
                    print("Teste em andamento; o prazo nao sera prolongado.", flush=True)
                else:
                    controle.enviar("FRENTE")
            elif comando == "S":
                controle.enviar("PARAR")
            elif comando == "STATUS":
                consultas_manuais.add(controle.enviar("STATUS"))
            elif comando:
                print("Use F, S, STATUS ou SAIR.", flush=True)
            if time.monotonic() >= proximo_status and not any(a == "STATUS" for a, _ in controle.pendentes.values()):
                controle.enviar("STATUS")
                proximo_status = time.monotonic() + .4
            for seq, acao in controle.ler():
                if acao == "FRENTE":
                    print("ESP confirmou aplicacao de PWM por 5 s; observe as rodas.", flush=True)
                elif acao == "PARAR":
                    print("ESP confirmou o comando de parada.", flush=True)
                if seq in consultas_manuais or controle.estado["estado"] != ultimo_estado:
                    print("ESP:", controle.estado, flush=True)
                consultas_manuais.discard(seq)
                ultimo_estado = controle.estado["estado"]
    except KeyboardInterrupt:
        print("Encerrando e solicitando parada...", flush=True)
    except (ConnectionError, TimeoutError, OSError, ValueError) as exc:
        erro = str(exc)
        print("Falha:", erro, "Nenhum movimento sera repetido automaticamente.", flush=True)
        return 1
    finally:
        if controle is not None:
            try:
                controle.encerrar()
            except (ConnectionError, TimeoutError, OSError, ValueError):
                print("Sem confirmacao final; o ESP corta pelo limite local/perda da conexao.", flush=True)
            destino = RAIZ / "artifacts/teste_rodas_wifi_20261103/ultimo_controle.json"
            destino.write_text(json.dumps({"erro": erro, "estado": controle.estado,
                "trilha": controle.trilha, "prova_rotacao": False}, ensure_ascii=False, indent=2), encoding="utf8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
