"""Memoria visual da Laylay.

Este modulo guarda capturas e metadados em uma pasta própria, com limite diário,
para que a experiencia visual possa ser reutilizada depois sem virar captura contínua.
"""

from __future__ import annotations

import base64
import json
import os
import re
import unicodedata
import uuid
from datetime import datetime
from typing import Optional

MAX_MEMORIAS_VISUAIS_DIA = 5

_PASTA_MEMORIA = ""
_PASTA_MEMORIA_VISUAL = ""
_ARQUIVO_INDICE = ""


def configurar_memoria_visual(pasta_memoria: str, max_por_dia: int = 5) -> None:
    """Define onde a memoria visual sera salva."""
    global MAX_MEMORIAS_VISUAIS_DIA, _PASTA_MEMORIA, _PASTA_MEMORIA_VISUAL, _ARQUIVO_INDICE
    _PASTA_MEMORIA = str(pasta_memoria or "").strip()
    _PASTA_MEMORIA_VISUAL = os.path.join(_PASTA_MEMORIA, "memoria_visual")
    _ARQUIVO_INDICE = os.path.join(_PASTA_MEMORIA, "memoria_visual_indice.json")
    MAX_MEMORIAS_VISUAIS_DIA = int(max_por_dia or 5)
    os.makedirs(_PASTA_MEMORIA_VISUAL, exist_ok=True)


def _normalizar_texto_visual(texto: str) -> str:
    t = str(texto or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _carregar_indice_memoria_visual() -> dict:
    try:
        if _ARQUIVO_INDICE and os.path.exists(_ARQUIVO_INDICE):
            with open(_ARQUIVO_INDICE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("dias", {})
                    return data
    except Exception:
        pass
    return {"dias": {}}


def _salvar_indice_memoria_visual(indice: dict) -> None:
    if not _ARQUIVO_INDICE:
        return
    os.makedirs(os.path.dirname(_ARQUIVO_INDICE), exist_ok=True)
    with open(_ARQUIVO_INDICE, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)


def _contar_memorias_visuais_no_dia(data_dia: str) -> int:
    indice = _carregar_indice_memoria_visual()
    dias = indice.get("dias") if isinstance(indice.get("dias"), dict) else {}
    registros = dias.get(data_dia) if isinstance(dias, dict) else []
    return len(registros) if isinstance(registros, list) else 0


def _classificar_importancia_memoria_visual(descricao: str, motivo: str, contexto: str) -> int:
    texto = _normalizar_texto_visual(" ".join([descricao or "", motivo or "", contexto or ""]))
    if any(k in texto for k in ["terminou", "concluiu", "finalizou", "ganhou", "vitoria", "vitória", "derrota", "novo jogo", "projeto", "render", "exportou", "salvou"]):
        return 9
    if any(k in texto for k in ["música", "musica", "show", "filme", "video", "vídeo", "assistiu", "playlist"]):
        return 8
    if any(k in texto for k in ["focado", "concentrado", "trabalho", "programando", "código", "codigo", "estudo"]):
        return 7
    if any(k in texto for k in ["curioso", "curiosidade", "pedido", "lembrar", "memória", "memoria"]):
        return 6
    return 5


def capturar_tela_base64(qualidade: int = 60) -> str:
    """Tira screenshot da tela atual e retorna Base64."""
    try:
        from PIL import Image
        import io as _io
        import pyautogui

        img = pyautogui.screenshot()
        _resample = getattr(Image, "Resampling", Image).LANCZOS
        img.thumbnail((1280, 720), _resample)
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=qualidade)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return ""


def analisar_com_groq(imagem_b64: str, pergunta: str, api_key: str, model: str) -> str:
    """Analisa uma imagem com Groq Vision."""
    max_tentativas = 3
    for tentativa in range(max_tentativas):
        try:
            from groq import Groq  # type: ignore[import-untyped]

            client = Groq(api_key=str(api_key or "").strip())
            resposta = client.chat.completions.create(
                model=str(model or "").strip(),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": pergunta},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagem_b64}"}},
                        ],
                    }
                ],
                temperature=0.8,
                max_tokens=512,
            )
            texto = resposta.choices[0].message.content.strip()
            return texto
        except Exception as e:
            erro_str = str(e).lower()
            if "429" in erro_str or "rate limit" in erro_str or "quota" in erro_str:
                if tentativa < max_tentativas - 1:
                    import time

                    time.sleep(8 * (tentativa + 1))
                    continue
                return "Groq tá lotado agora, Pedro. Me dá uns 20 segundos ou usa o modo texto por enquanto."
            if tentativa == max_tentativas - 1:
                return f"Não consegui analisar a tela com Groq: {str(e)[:100]}"
    return "Erro desconhecido no Groq Vision."


def registrar_memoria_visual(
    imagem_b64: str,
    descricao: str,
    motivo: str = "captura manual",
    contexto: str | dict = "",
    emocao: str = "",
    intensidade: int = 1,
    tags: Optional[list] = None,
    origem: str = "pc_a",
) -> Optional[str]:
    """Salva uma memoria visual com limite diário e metadados."""
    if not imagem_b64:
        return None
    if not _PASTA_MEMORIA_VISUAL:
        return None

    hoje = datetime.now().strftime("%Y-%m-%d")
    agora = datetime.now()
    if _contar_memorias_visuais_no_dia(hoje) >= MAX_MEMORIAS_VISUAIS_DIA:
        print(f"🧠 [VISÃO] Limite diário de {MAX_MEMORIAS_VISUAIS_DIA} memórias visuais atingido em {hoje}.")
        return None

    try:
        pasta_dia = os.path.join(_PASTA_MEMORIA_VISUAL, hoje)
        os.makedirs(pasta_dia, exist_ok=True)

        uid = uuid.uuid4().hex[:12]
        nome_base = agora.strftime("%H%M%S") + f"_{uid}"
        img_path = os.path.join(pasta_dia, f"{nome_base}.jpg")
        meta_path = os.path.join(pasta_dia, f"{nome_base}.json")

        dados_img = base64.b64decode(str(imagem_b64).split(",")[-1])
        with open(img_path, "wb") as f_img:
            f_img.write(dados_img)

        indice = _carregar_indice_memoria_visual()
        if not isinstance(indice.get("dias"), dict):
            indice["dias"] = {}
        lista_dia = list(indice["dias"].get(hoje) or [])
        importancia = _classificar_importancia_memoria_visual(descricao, motivo, contexto)
        reg = {
            "id": uid,
            "data": hoje,
            "horario": agora.strftime("%H:%M:%S"),
            "imagem": img_path,
            "programa": str((contexto or {}).get("exe") if isinstance(contexto, dict) else "").strip(),
            "contexto": contexto if isinstance(contexto, dict) else {"texto": str(contexto or "")},
            "descricao": str(descricao or "").strip(),
            "emocao": str(emocao or "").strip(),
            "intensidade": int(intensidade or 1),
            "motivo": str(motivo or "").strip(),
            "tags": list(tags or []),
            "importancia": int(importancia),
            "origem": str(origem or "pc_a").strip(),
        }

        with open(meta_path, "w", encoding="utf-8") as f_meta:
            json.dump(reg, f_meta, ensure_ascii=False, indent=2)

        lista_dia.append(reg)
        indice["dias"][hoje] = lista_dia[-MAX_MEMORIAS_VISUAIS_DIA:]
        indice["ultimo_registro"] = reg
        indice["atualizado_em"] = agora.isoformat(" ")
        _salvar_indice_memoria_visual(indice)

        print(f"🖼️ [VISÃO] Memória visual salva: {img_path}")
        return img_path
    except Exception as e:
        print(f"⚠️ [VISÃO] Falha ao registrar memória visual: {e}")
        return None
