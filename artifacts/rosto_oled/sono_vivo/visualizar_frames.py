"""Prévia dos pixels produzidos pelo firmware real compilado para host."""
from pathlib import Path
from PIL import Image, ImageDraw

raiz = Path(__file__).resolve().parent
arquivos = sorted((raiz / "frames_v2").glob("sono_*.pgm"), key=lambda p: int(p.stem.split("_")[-1]))
quadros = [Image.open(p).convert("RGB").resize((512, 256), Image.Resampling.NEAREST) for p in arquivos]
quadros[0].save(raiz / "sono_vivo_v2.gif", save_all=True, append_images=quadros[1:], duration=100, loop=0)
folha = Image.new("RGB", (1048, 4 * 294), "#161a23")
texto = ImageDraw.Draw(folha)
for i, segundos in enumerate((2, 10, 16, 25, 34, 44, 54, 63)):
    frame = min(len(quadros) - 1, int(segundos / .1))
    x, y = 8 + (i % 2) * 524, 8 + (i // 2) * 294
    folha.paste(quadros[frame], (x, y))
    texto.text((x + 8, y + 264), f"Sono: {segundos}s", fill="white")
folha.save(raiz / "poses_sono_v2.png")
print(f"{len(quadros)} frames; previa e poses geradas")
