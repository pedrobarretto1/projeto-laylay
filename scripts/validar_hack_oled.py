"""Valida o .ino e gera prévia do terminal com seu raster real de pixels.

GPIO, PWM, relógio e I2C são simulados: não abre COM nem prova o OLED físico.
A fonte 5x7 é compartilhada pelo firmware/host, sem depender do print do stub.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="artifacts/rosto_oled/hack")
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    saida = Path(args.saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("clang++") or r"C:\Program Files\Windhawk\Compiler\bin\clang++.exe"
    if not Path(compiler).is_file():
        raise SystemExit("clang++ necessário para validar o .ino em host")
    host = raiz / "firmware/rosto_laylay/validacao_host"
    fonte = Path("C:/Windows/Fonts/segoeui.ttf")
    legenda = ImageFont.truetype(str(fonte), 15) if fonte.exists() else ImageFont.load_default()
    with tempfile.TemporaryDirectory(prefix="laylay-hack-") as temporario:
        pasta = Path(temporario)
        executavel = pasta / "validar.exe"
        subprocess.run([compiler, "-std=c++17", "-static", "-I" + str(host),
                        str(host / "validar.cpp"), "-o", str(executavel)], check=True)
        resultado = subprocess.run([str(executavel), str(pasta / "frames"), "HACK"],
                                   check=True, capture_output=True, text=True)
        print(resultado.stdout.strip())
        quadros = []
        for indice in range(300):
            quadro = Image.new("RGB", (544, 322), "#10151d")
            desenho = ImageDraw.Draw(quadro)
            # BytesIO evita que um decoder retenha handles Windows da pasta temporária.
            dados = (pasta / "frames" / f"hack_{indice:03d}.pgm").read_bytes()
            with Image.open(io.BytesIO(dados)) as bruto:
                nativo = bruto.convert("RGB")
                quadro.paste(nativo.resize((512, 256), Image.Resampling.NEAREST), (16, 12))
                if indice == 117:
                    nativo.save(saida / "hack_nativo.png")
            estado = "Rosto" if indice < 45 else "Processando · animação decorativa" if indice < 225 else "Voltando ao rosto"
            desenho.text((16, 274), estado, font=legenda, fill="#dbe4f2")
            desenho.text((16, 296), "Pixels do firmware · hardware simulado", font=legenda, fill="#b4bac6")
            quadros.append(quadro)
        quadros[117].save(saida / "hack.png")
        quadros[0].save(saida / "hack.gif", save_all=True, append_images=quadros[1:],
                       duration=33, loop=0, optimize=True)
        contatos = Image.new("RGB", (1632, 644), "#10151d")
        for posicao, indice in enumerate((44, 48, 54, 117, 230, 239)):
            contatos.paste(quadros[indice], ((posicao % 3) * 544, (posicao // 3) * 322))
        contatos.save(saida / "hack_transicao.png")
    arquivos = [host.parent / "rosto_laylay.ino", host.parent / "fonte_terminal.h", host / "validar.cpp"]
    receipt = {
        "hardware_simulado": True, "prova_optica": False, "motores_reais_acionados": False,
        "saida_host": resultado.stdout.splitlines(),
        "fontes_sha256": {str(arquivo.relative_to(raiz)): hashlib.sha256(arquivo.read_bytes()).hexdigest()
                          for arquivo in arquivos},
        "preview": str(saida / "hack.gif"),
    }
    (saida / "receipt_host.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Prévia:", saida / "hack.gif")


if __name__ == "__main__":
    main()
