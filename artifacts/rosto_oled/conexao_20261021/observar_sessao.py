"""Ensaio finito do transporte de produção, sem autorizar motores."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

from mente_laylay.especialistas.rosto_oled_runtime import RostoOledRuntime, _abrir_serial


def main() -> None:
    inicio = time.monotonic()
    trilha: list[dict] = []
    amostras: list[dict] = []
    proibidos: list[str] = []
    duracao = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
    nome_saida = sys.argv[2] if len(sys.argv) > 2 else "sessao.json"
    if Path(nome_saida).name != nome_saida or not nome_saida.endswith(".json"):
        raise ValueError("nome_saida_invalido")

    def registrar(tipo: str, **dados) -> None:
        trilha.append({"t": round(time.monotonic() - inicio, 4), "tipo": tipo, **dados})

    class PortaObservada:
        def __init__(self, nome: str) -> None:
            registrar("abrir", porta=nome)
            self.serial = _abrir_serial(nome)

        def write(self, dados: bytes) -> int:
            linha = dados.decode("ascii").strip()
            campos = linha.split()
            if campos[0] in {"MOTOR", "TURN", "DEMO"} or (
                campos[0] == "SENTRY" and campos[4] != "0"
            ):
                proibidos.append(linha)
                raise AssertionError("movimento_proibido_neste_ensaio")
            registrar("tx", linha=linha)
            return self.serial.write(dados)

        def read(self, tamanho: int) -> bytes:
            dados = self.serial.read(tamanho)
            if dados:
                registrar("rx", texto=dados.decode("ascii", errors="replace"))
            return dados

        def close(self) -> None:
            registrar("fechar")
            self.serial.close()

    runtime = RostoOledRuntime(
        estado_getter=lambda: {}, porta="COM4", abrir_serial=PortaObservada,
        companhia_getter=lambda: {"ativa": False},
        busca_obstaculos_getter=lambda _: False,
    )
    fontes = ["mente_laylay/especialistas/rosto_oled_runtime.py",
              "firmware/rosto_laylay/rosto_laylay.ino"]
    resultado = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=RAIZ, text=True).strip(),
        "status": subprocess.check_output(["git", "status", "--short"], cwd=RAIZ, text=True),
        "fontes": {p: hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in fontes},
        "escopo": "transporte de producao isolado; sem autorizacao de movimento; nao e main completo",
    }
    try:
        while time.monotonic() - inicio < duracao:
            antes = time.monotonic()
            ok = runtime.sincronizar()
            diagnostico = runtime.diagnostico()
            amostra = {"t": round(time.monotonic() - inicio, 3), "ok": ok,
                       "duracao_ms": round((time.monotonic() - antes) * 1000, 2),
                       "diagnostico": diagnostico}
            amostras.append(amostra)
            print(json.dumps({"t": amostra["t"], "ok": ok,
                              "duracao_ms": amostra["duracao_ms"],
                              "motivo": diagnostico.get("motivo"),
                              "saude": diagnostico.get("saude")}, ensure_ascii=False), flush=True)
            time.sleep(.25 if ok else 3)
    finally:
        runtime.encerrar()
        resultado.update(amostras=amostras, trilha=trilha, proibidos=proibidos,
                         final=runtime.diagnostico())
        destino = Path(__file__).with_name(nome_saida)
        destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"arquivo": str(destino), "amostras": len(amostras),
                          "falhas": sum(not a["ok"] for a in amostras),
                          "movimentos_enviados": len(proibidos)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
