"""Executa protocolo do .ino em host e exporta prévia dos seus frames reais.

Hardware/rotinas gráficas são dublês. Não substitui inspeção no OLED físico.
"""
from __future__ import annotations
import argparse
import io
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

from mente_laylay.especialistas.rosto_oled_runtime import EMOCOES_ROSTO


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default="artifacts/rosto_oled")
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parents[1]
    saida = Path(args.saida).resolve()
    saida.mkdir(parents=True, exist_ok=True)
    compiler = shutil.which("clang++") or r"C:\Program Files\Windhawk\Compiler\bin\clang++.exe"
    if not Path(compiler).is_file():
        raise SystemExit("clang++ necessário para validar o .ino em host")
    host = raiz / "firmware/rosto_laylay/validacao_host"
    with tempfile.TemporaryDirectory(prefix="laylay-rosto-") as temporario:
        pasta = Path(temporario)
        executavel = pasta / "validar.exe"
        subprocess.run([compiler, "-std=c++17", "-static", "-I" + str(host),
                        str(host / "validar.cpp"), "-o", str(executavel)], check=True)
        subprocess.run([str(executavel), str(pasta / "frames")], check=True)
        fonte_path = Path("C:/Windows/Fonts/segoeui.ttf")
        fonte = ImageFont.truetype(str(fonte_path), 18) if fonte_path.exists() else ImageFont.load_default()
        frames = []
        for frame in range(96):
            painel = Image.new("RGB", (1248, 1000), "#10151d")
            desenho = ImageDraw.Draw(painel)
            desenho.text((24, 12), "LAYLAY · prévia do firmware · hardware simulado", font=fonte, fill="#b4bac6")
            for indice, emocao in enumerate((*EMOCOES_ROSTO, "Dormindo · sem conexão")):
                x, y = 24 + (indice % 3) * 408, 52 + (indice // 3) * 232
                dados = (pasta / "frames" / f"emo_{indice}_{frame:03d}.pgm").read_bytes()
                with Image.open(io.BytesIO(dados)) as bruto:
                    imagem = bruto.convert("RGB").resize((384, 192), Image.Resampling.NEAREST)
                painel.paste(imagem, (x, y))
                desenho.text((x, y + 198), emocao.capitalize(), font=fonte, fill="#dbe4f2")
            frames.append(painel)
        frames[30].save(saida / "expressoes.png")
        frames[80].save(saida / "expressoes_frame80.png")
        frames[0].save(saida / "expressoes.gif", save_all=True, append_images=frames[1:], duration=33, loop=0)
        transicoes = []
        roteiro = (0, 1, 6, 5, 3, 4, 2, 7, 8, 9, 0)
        nomes = (*EMOCOES_ROSTO, "Dormindo")
        for frame in range(704):
            painel = Image.new("RGB", (432, 254), "#10151d")
            desenho = ImageDraw.Draw(painel)
            with Image.open(io.BytesIO((pasta / "frames" / f"troca_{frame:03d}.pgm").read_bytes())) as bruto:
                painel.paste(bruto.convert("RGB").resize((384, 192), Image.Resampling.NEAREST), (24, 18))
            trecho = frame // 64
            legenda = nomes[roteiro[trecho]].capitalize()
            if trecho in (4, 5) and 24 <= frame % 64 < 52:
                legenda += " · falando"
            desenho.text((24, 220), legenda, font=fonte, fill="#dbe4f2")
            transicoes.append(painel)
        transicoes[0].save(saida / "transicoes.gif", save_all=True, append_images=transicoes[1:], duration=33, loop=0)
        contatos = Image.new("RGB", (1296, 508), "#10151d")
        for i, frame in enumerate((63, 67, 71, 75, 83, 95)):
            contatos.paste(transicoes[frame], ((i % 3) * 432, (i // 3) * 254))
        contatos.save(saida / "transicao_calma_alegre.png")
    print("Prévia:", saida / "expressoes.gif")


if __name__ == "__main__":
    main()
