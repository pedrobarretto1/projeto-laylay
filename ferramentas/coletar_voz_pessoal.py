"""Coleta privada de exemplos da voz de Pedro e avalia o Whisper atual."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from mente_laylay.percepcao.treino_voz_pessoal import (  # noqa: E402
    DatasetVozPessoal,
    FRASES_TREINO_PADRAO,
    capturar_frase,
    distancia_edicao_palavras,
    frases_pendentes,
    selecionar_entrada_treino,
)


def avaliar(dataset: DatasetVozPessoal, modelo_nome: str) -> int:
    from faster_whisper import WhisperModel

    registros = dataset.registros()
    if not registros:
        print("Ainda não existem gravações para avaliar.")
        return 1
    print(f"Carregando Whisper {modelo_nome} para avaliação...")
    modelo = WhisperModel(modelo_nome, device="cpu", compute_type="int8")
    erros_total = palavras_total = 0
    acertos_frase = 0
    for indice, item in enumerate(registros, 1):
        caminho = dataset.raiz / item["audio"]
        segmentos, _ = modelo.transcribe(
            str(caminho), language="pt", beam_size=5, condition_on_previous_text=False,
        )
        reconhecido = " ".join(segmento.text.strip() for segmento in segmentos).strip()
        erros, palavras = distancia_edicao_palavras(item["texto"], reconhecido)
        erros_total += erros
        palavras_total += palavras
        acerto = erros == 0
        acertos_frase += int(acerto)
        marcador = "✅" if acerto else "❌"
        print(f"{marcador} {indice:03d} esperado={item['texto']!r} ouvido={reconhecido!r}")
    wer = erros_total / max(1, palavras_total)
    print(
        f"\nResultado: {acertos_frase}/{len(registros)} frases exatas; "
        f"WER={wer:.1%} ({erros_total}/{palavras_total} palavras)."
    )
    return 0


def coletar(dataset: DatasetVozPessoal, repeticoes: int, microfone: str) -> int:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf

    pendentes = frases_pendentes(dataset, FRASES_TREINO_PADRAO, repeticoes)
    if not pendentes:
        print("A coleta solicitada já está completa. Use --avaliar para medir o Whisper.")
        return 0
    indice, info, taxa = selecionar_entrada_treino(sd, microfone)
    print(f"Microfone: {info.get('name')} (índice {indice}, {taxa} Hz)")
    print(f"Dados locais: {dataset.raiz}")
    print("Fique em silêncio durante a calibração. Use Ctrl+C para pausar com segurança.\n")
    total = len(pendentes)
    try:
        for numero, frase in enumerate(pendentes, 1):
            print(f"[{numero}/{total}] Fale naturalmente: {frase}")
            input("Pressione Enter quando estiver pronto...")
            audio = capturar_frase(
                sounddevice_mod=sd, numpy_mod=np, indice=indice, taxa=taxa,
            )
            if not len(audio):
                print("Nenhuma fala foi capturada; essa frase continuará pendente.\n")
                continue
            registro = dataset.salvar(audio, taxa, frase, soundfile_mod=sf)
            print(f"Salvo como exemplo {registro['repeticao']} ({registro['divisao']}).\n")
    except (KeyboardInterrupt, EOFError):
        print("\nColeta pausada. O progresso já foi salvo e será retomado depois.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--avaliar", action="store_true", help="avalia as gravações no Whisper atual")
    parser.add_argument("--repeticoes", type=int, default=5, help="exemplos desejados por frase")
    parser.add_argument("--microfone", default=os.getenv("LAYLAY_MICROFONE", ""))
    parser.add_argument("--modelo", default=os.getenv("LAYLAY_WHISPER_MODELO", "turbo"))
    parser.add_argument(
        "--dados", default=str(RAIZ_PROJETO / "dados" / "voz_pessoal"),
        help="pasta privada das gravações",
    )
    args = parser.parse_args()
    dataset = DatasetVozPessoal(args.dados)
    return avaliar(dataset, args.modelo) if args.avaliar else coletar(
        dataset, max(1, args.repeticoes), args.microfone,
    )


if __name__ == "__main__":
    raise SystemExit(main())

