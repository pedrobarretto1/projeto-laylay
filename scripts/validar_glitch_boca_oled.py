"""Exporta pixels reais do .ino para boca/glitch e valida ambos os perfis.

GPIO, PWM, I2C e relógio são simulados. Não usa COM nem prova o efeito físico.
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
    parser.add_argument("--saida", default="artifacts/rosto_oled/glitch_boca")
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    saida = Path(args.saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("clang++") or r"C:\Program Files\Windhawk\Compiler\bin\clang++.exe"
    if not Path(compiler).is_file():
        raise SystemExit("clang++ necessário para validar o .ino em host")
    host = raiz / "firmware/rosto_laylay/validacao_host"
    fonte_path = Path("C:/Windows/Fonts/segoeui.ttf")
    fonte = ImageFont.truetype(str(fonte_path), 16) if fonte_path.exists() else ImageFont.load_default()
    nomes = ("Calma", "Alegre", "Triste", "Brava", "Irritada", "Surpresa", "Envergonhada", "Debochada", "Acalmando-se")
    resultados: dict[str, list[str]] = {}
    with tempfile.TemporaryDirectory(prefix="laylay-glitch-boca-") as temporario:
        pasta = Path(temporario)
        for perfil in (0, 1):
            executavel = pasta / f"validar_{perfil}.exe"
            subprocess.run([compiler, "-std=c++17", "-static",
                            f"-DLAYLAY_HABILITAR_MOTORES_BANCADA={perfil}", "-I" + str(host),
                            str(host / "validar_glitch_boca.cpp"), "-o", str(executavel)], check=True)
            comando = [str(executavel)]
            if perfil == 0:
                comando.append(str(pasta / "frames"))
            resultado = subprocess.run(comando, check=True, capture_output=True, text=True)
            resultados[str(perfil)] = resultado.stdout.splitlines()
            print(f"Perfil {perfil}:\n{resultado.stdout.strip()}")

        def quadro(nome: str) -> Image.Image:
            with Image.open(io.BytesIO((pasta / "frames" / nome).read_bytes())) as bruto:
                return bruto.convert("RGB")

        bocas = []
        for frame in range(120):
            painel = Image.new("RGB", (1248, 760), "#10151d")
            desenho = ImageDraw.Draw(painel)
            estado = "Falando" if 15 <= frame < 95 else "Em repouso"
            desenho.text((24, 10), f"Boca · {estado.lower()} · pixels do firmware, hardware simulado", font=fonte, fill="#b4bac6")
            for indice, nome in enumerate(nomes):
                x, y = 24 + (indice % 3) * 408, 48 + (indice // 3) * 232
                painel.paste(quadro(f"fala_{indice}_{frame:03d}.pgm").resize((384, 192), Image.Resampling.NEAREST), (x, y))
                desenho.text((x, y + 196), nome, font=fonte, fill="#dbe4f2")
            bocas.append(painel)
        bocas[0].save(saida / "boca.gif", save_all=True, append_images=bocas[1:], duration=33, loop=0)
        bocas[35].save(saida / "boca.png")
        fases = Image.new("RGB", (1632, 464), "#10151d")
        amostras = []
        for emocao in (0, 3):
            def abertura(indice: int) -> int:
                imagem = quadro(f"fala_{emocao}_{indice:03d}.pgm")
                brancos = [y for y in range(43, 62) if imagem.getpixel((64, y))[0]]
                return max(brancos) - min(brancos) if brancos else 0
            pico = max(range(24, 95), key=abertura)
            amostras.extend(((emocao, 14), (emocao, max(15, pico - 3)), (emocao, pico), (emocao, 102)))
        for posicao, (emocao, frame) in enumerate(amostras):
            x, y = (posicao % 4) * 408 + 12, (posicao // 4) * 232 + 12
            fases.paste(quadro(f"fala_{emocao}_{frame:03d}.pgm").resize((384, 192), Image.Resampling.NEAREST), (x, y))
            ImageDraw.Draw(fases).text((x, y + 196), f"{nomes[emocao]} · quadro {frame}", font=fonte, fill="#dbe4f2")
        fases.save(saida / "boca_fases.png")
        glitches = []
        for frame in range(120):
            painel = Image.new("RGB", (544, 322), "#10151d")
            desenho = ImageDraw.Draw(painel)
            nativo = quadro(f"glitch_{frame:03d}.pgm")
            painel.paste(nativo.resize((512, 256), Image.Resampling.NEAREST), (16, 12))
            if frame == 40:
                nativo.save(saida / "glitch_nativo.png")
            estado = "Rosto" if frame < 30 else "Glitch decorativo" if frame < 58 else "Recuperação do rosto"
            desenho.text((16, 274), estado, font=fonte, fill="#dbe4f2")
            desenho.text((16, 296), "Pixels do firmware · hardware simulado", font=fonte, fill="#b4bac6")
            glitches.append(painel)
        glitches[0].save(saida / "glitch.gif", save_all=True, append_images=glitches[1:], duration=33, loop=0)
        glitches[40].save(saida / "glitch.png")
        contatos = Image.new("RGB", (1632, 644), "#10151d")
        for posicao, frame in enumerate((29, 33, 40, 48, 54, 59)):
            contatos.paste(glitches[frame], ((posicao % 3) * 544, (posicao // 3) * 322))
        contatos.save(saida / "glitch_fases.png")
    arquivos = (host.parent / "rosto_laylay.ino", host / "Adafruit_SSD1306.h", host / "validar_glitch_boca.cpp")
    receipt = {
        "hardware_simulado": True, "prova_optica": False, "motores_reais_acionados": False,
        "perfil_0": resultados["0"], "perfil_1": resultados["1"],
        "fontes_sha256": {str(arquivo.relative_to(raiz)): hashlib.sha256(arquivo.read_bytes()).hexdigest() for arquivo in arquivos},
        "previas": [str(saida / "boca.gif"), str(saida / "glitch.gif")],
    }
    (saida / "receipt_host.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Prévias:", saida / "boca.gif", saida / "glitch.gif")


if __name__ == "__main__":
    main()
