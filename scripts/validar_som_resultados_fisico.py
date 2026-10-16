"""Receipts de leituras diagnósticas reais → owner instalado → bips na USB.

Não abre interface, não executa motores nem muda arquivos/configuração.
Uma leitura existente e uma inexistente exercitam sucesso/falha próximos ao
bip anterior. Confirmação serial não substitui audição humana.
"""
from pathlib import Path
import json
import sys
import time
import uuid
import argparse

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
parser = argparse.ArgumentParser()
parser.add_argument("--testar-envio", action="store_true", help="Também testa SOUND8 diretamente, sem simular receipt de ação no PC")
args = parser.parse_args()
DESTINO = RAIZ / ("artifacts/rosto_oled/som_resultados/envio" if args.testar_envio else "artifacts/rosto_oled/som_resultados")
DESTINO.mkdir(parents=True, exist_ok=True)
from mente_laylay.integracao import instancia_unica
adquirir = instancia_unica.adquirir_instancia_unica
instancia_unica.adquirir_instancia_unica = lambda _: adquirir(DESTINO / "instancia_sonda")
import laylay
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao

rosto = laylay._rosto_oled_runtime
owner = laylay._atividade_operacional_runtime
trilha, etapas = [], []
abrir = rosto.abrir_serial

class CapturaSerial:
    def __init__(self, porta):
        self.serial = abrir(porta)
        self.pendente = bytearray()
    def write(self, dados):
        texto = dados.decode().strip()
        assert not texto.startswith(("MOTOR ", "MOTOR2 "))
        trilha.append({"direcao": "tx", "pacote": texto, "monotonic": time.monotonic()})
        return self.serial.write(dados)
    def read(self, tamanho):
        dados = self.serial.read(tamanho)
        self.pendente.extend(dados)
        while b"\n" in self.pendente:
            linha, _, resto = self.pendente.partition(b"\n")
            self.pendente = bytearray(resto)
            texto = linha.decode(errors="replace").strip()
            if texto.startswith(("SOUNDACK ", "ERROR 1 SOM_", "ACK ", "SACK ", "NACK ")):
                trilha.append({"direcao": "rx", "pacote": texto, "monotonic": time.monotonic()})
        return dados
    def close(self):
        self.serial.close()

def ler_arquivo(caminho: Path) -> ResultadoAcao:
    identificador = uuid.uuid4().hex
    try:
        dados = caminho.read_bytes()
        assert dados, "leitura vazia"
        return ResultadoAcao(intent="FILE_READ", status="leitura_confirmada", origem="executor",
            executou=True, confirmado=True, ok=True, id_solicitacao=identificador)
    except FileNotFoundError:
        return ResultadoAcao(intent="FILE_READ", status="falha_execucao", origem="executor",
            executou=False, confirmado=False, ok=False, id_solicitacao=identificador)

def esperar_som(tipo: int) -> None:
    prazo = time.monotonic() + 5
    while time.monotonic() < prazo:
        assert rosto.sincronizar(), rosto.diagnostico()
        if any(t["direcao"] == "rx" and t["pacote"].startswith("SOUNDACK ") and t["pacote"].endswith(f" {tipo}") for t in trilha):
            return
        time.sleep(.05)
    raise AssertionError(f"sem SOUNDACK da melodia {tipo}")

falha = ""
rosto.abrir_serial = CapturaSerial
try:
    laylay._interacao_chat_runtime.atualizar_estado(True)
    assert rosto.sincronizar()
    assert rosto.diagnostico()["som"]["suportado"]
    assert laylay._corpo_motor_runtime.companhia.processar()["ok"]
    assert laylay._corpo_motor_runtime.companhia.diagnostico()["ativa"]
    sucesso = owner.executar(ler_arquivo, RAIZ / "mente_laylay/especialistas/rosto_oled_runtime.py")
    assert sucesso.confirmado
    esperar_som(1)
    etapas.append({"resultado": "sucesso", "id_solicitacao": sucesso.id_solicitacao, "diagnostico": rosto.diagnostico()})
    inexistente = DESTINO / ("inexistente_" + uuid.uuid4().hex + ".txt")
    resultado_falho = owner.executar(ler_arquivo, inexistente)
    assert resultado_falho.ok is False
    esperar_som(2)
    etapas.append({"resultado": "falha", "id_solicitacao": resultado_falho.id_solicitacao, "diagnostico": rosto.diagnostico()})
    if args.testar_envio:
        assert rosto.diagnostico()["som"]["envio_suportado"]
        prazo = time.monotonic() + 2.1
        while time.monotonic() < prazo:
            assert rosto.sincronizar()
            time.sleep(.05)
        # Diagnóstico explícito do transdutor: nenhuma ação/receipt fabricado.
        rosto._seq_som += 1
        campos = f"{rosto._sessao} {rosto._seq_som} 8"
        rosto._escrever(f"SOUND 1 {campos}")
        assert rosto._esperar(f"SOUNDACK 1 {campos}", .3, opcional=True)
        rosto._ultimo_envio_som = time.monotonic()
        etapas.append({"resultado": "som_envio_diagnostico_direto", "receipt_acao_pc": False})
    quantidade = sum(t["direcao"] == "tx" and t["pacote"].startswith("SOUND ") for t in trilha)
    prazo = time.monotonic() + 2.3
    while time.monotonic() < prazo:
        assert rosto.sincronizar()
        time.sleep(.05)
    assert sum(t["direcao"] == "tx" and t["pacote"].startswith("SOUND ") for t in trilha) == quantidade
except Exception as erro:
    falha = type(erro).__name__ + ": " + str(erro)
finally:
    laylay._corpo_motor_runtime.companhia.revogar("fim_sonda_som_resultados")
    rosto.encerrar()
    rosto.abrir_serial = abrir
    dados = {"falha": falha, "etapas": etapas, "trilha": trilha, "interface_aberta": False,
        "motor_enviado": False, "audicao_humana": "pendente", "origem": "leituras locais de diagnostico reais, owner e composicao de producao"}
    destino = DESTINO / "receipt_fisico.json"
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"receipt": str(destino), "falha": falha}, ensure_ascii=False), flush=True)
if falha:
    raise SystemExit(1)
