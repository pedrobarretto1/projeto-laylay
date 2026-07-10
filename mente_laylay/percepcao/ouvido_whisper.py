"""Ouvido Whisper da Laylay.

Este modulo concentra limpeza de diccao e transcricao de voz, mantendo o
`laylay.py` como orquestrador em vez de carregar detalhes do ouvido.
"""

from __future__ import annotations

import os
import re
from typing import Any


def limpar_diccao_e_ruido(texto_falado: str) -> str:
    """Filtro anti-ruido + corretor de diccao para reduzir alucinacoes do Whisper."""
    texto = str(texto_falado or "").lower().strip()

    alucinacoes = [
        "obrigado por assistir",
        "inscreva-se",
        "legendas",
        "amém",
        "obrigado.",
        "com legendas",
        "obrigado",
        "editado por",
        "amara.org",
        "transmissão ao vivo",
    ]
    for alucinacao in alucinacoes:
        if texto == alucinacao or texto == alucinacao + ".":
            return ""

    dicionario_correcao = {
        "canista minha terra": "organiza minha tela",
        "o canista minha terra": "organiza minha tela",
        "orcaniça": "organiza",
        "ocaniça": "organiza",
        "organisa": "organiza",
        "organaiza": "organiza",
        "mi yaya": "minha tela",
        "adiata": "tela",
        "opede": "opera",
        "opeditor": "opera",
        "whatsappi": "whatsapp",
        "whatsapi": "whatsapp",
        "what": "whatsapp",
        "pedu": "pelo",
        "teta cheia": "tela cheia",
        "teta": "tela",
        "coloco": "coloca",
        "troco": "troca",
        "coco": "código",
        "coigo": "código",
        "muica": "música",
        "muisca": "música",
        "próima": "próxima",
        "proxima": "próxima",
    }

    for errado, certo in dicionario_correcao.items():
        texto = texto.replace(errado, certo)

    return texto.strip()


def transcrever_com_whisper(audio: Any, *, modelo_whisper: Any) -> str:
    """Transcreve com Whisper + filtro anti-alucinacao + initial_prompt."""
    try:
        temp_file = "temp_voz.wav"
        with open(temp_file, "wb") as f:
            f.write(audio.get_wav_data())

        lista_negra = [
            "legendas pela comunidade",
            "amara.org",
            "obrigado por assistir",
            "curta o vídeo",
            "inscreva-se no canal",
            "fiquem com deus",
            "transcrição",
            "legenda por",
            "edited by",
        ]

        segments, _info = modelo_whisper.transcribe(
            temp_file,
            language="pt",
            initial_prompt=(
                "Organiza a tela, Laylay, YouTube, Spotify, VS Code, WhatsApp, "
                "Opera, Chrome, toca música, pausa, próxima, abre, fecha, clica, "
                "tela cheia, minha área, música"
            ),
            beam_size=5,
            best_of=5,
            no_speech_threshold=0.6,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        texto = " ".join([seg.text for seg in segments]).strip()
        texto_limpo = texto.lower()
        if any(frase in texto_limpo for frase in lista_negra) or len(texto) < 3:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return ""

        correcoes = {
            "cloco": "coloca",
            "clo co": "coloca",
            "eda": "editor",
            "dinh sa lõin": "dance alone",
            "dinhsa loin": "dance alone",
            "dança alone": "dance alone",
            "fita": "VS Code",
            "fita editor": "VS Code",
        }
        for errado, certo in correcoes.items():
            texto = texto.replace(errado, certo)

        texto = re.sub(r"\s+", " ", texto).strip()

        if os.path.exists(temp_file):
            os.remove(temp_file)
        return texto

    except Exception as e:
        print(f"❌ Erro no Whisper: {e}")
        return ""
