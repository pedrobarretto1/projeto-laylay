"""Captura em memória da janela de jogo, sem criar arquivos."""

from __future__ import annotations

import base64
import io
from typing import Any, Callable, Mapping

from mente_laylay.percepcao.imagens_multimodais import empacotar_imagens


def _codificar_jpeg(imagem: Any, qualidade: int) -> str:
    buffer = io.BytesIO()
    imagem.convert("RGB").save(
        buffer, format="JPEG", quality=max(70, min(96, int(qualidade))),
        subsampling=0, optimize=True,
    )
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _recorte_adaptativo(
    imagem: Any,
    cursor_x: int,
    cursor_y: int,
    *,
    largura_alvo: int,
    altura_alvo: int,
    margem_externa: int,
) -> Any:
    """Preserva mais espaço no lado onde tooltips normalmente se abrem."""
    largura, altura = imagem.size
    rw, rh = min(largura, largura_alvo), min(altura, altura_alvo)
    if cursor_x < largura / 2:
        esquerda = cursor_x - margem_externa
    else:
        esquerda = cursor_x - rw + margem_externa
    topo = cursor_y - int(rh * 0.56)
    esquerda = max(0, min(largura - rw, int(esquerda)))
    topo = max(0, min(altura - rh, int(topo)))
    return imagem.crop((esquerda, topo, esquerda + rw, topo + rh))


def _empacotar_foco_cursor(
    imagem: Any, cursor_x: int, cursor_y: int, qualidade: int,
) -> str:
    """Envia contexto e texto em imagens separadas, sem esmagar o tooltip."""
    from PIL import Image, ImageDraw

    largura, altura = imagem.size
    geral = imagem.copy()
    draw = ImageDraw.Draw(geral)
    raio = max(10, int(min(largura, altura) * 0.014))
    draw.ellipse(
        (cursor_x - raio, cursor_y - raio, cursor_x + raio, cursor_y + raio),
        outline=(255, 45, 45), width=max(3, raio // 5),
    )
    resample = getattr(Image, "Resampling", Image).LANCZOS
    # O quadro geral serve para contexto, não para OCR. Mantê-lo em 1080p
    # consumia quase todo o orçamento TPM antes da leitura dedicada do tooltip.
    geral.thumbnail((1280, 720), resample)

    regiao = _recorte_adaptativo(
        imagem, cursor_x, cursor_y,
        largura_alvo=1200, altura_alvo=900, margem_externa=200,
    )
    detalhe = _recorte_adaptativo(
        imagem, cursor_x, cursor_y,
        largura_alvo=900, altura_alvo=900, margem_externa=140,
    )
    return empacotar_imagens([
        {
            "label": "Quadro geral da janela do jogo; o círculo vermelho marca o cursor.",
            "mime": "image/jpeg", "width": geral.width, "height": geral.height,
            "data": _codificar_jpeg(geral, min(90, qualidade)),
        },
        {
            "label": "Região ampla ao redor do cursor, preservada para incluir o tooltip inteiro.",
            "mime": "image/jpeg", "width": regiao.width, "height": regiao.height,
            "data": _codificar_jpeg(regiao, max(92, qualidade)),
        },
        {
            "label": "Recorte próximo em resolução nativa para ler nome, requisitos e atributos.",
            "mime": "image/jpeg", "width": detalhe.width, "height": detalhe.height,
            "data": _codificar_jpeg(detalhe, max(94, qualidade)),
        },
    ])


def capturar_janela_jogo_base64(
    contexto_jogo: Mapping[str, Any] | None,
    *,
    qualidade: int = 90,
    image_grab: Callable[..., Any] | None = None,
) -> str:
    contexto = dict(contexto_jogo or {})
    limites = dict(contexto.get("limites") or {})
    esquerda = int(limites.get("left") or 0)
    topo = int(limites.get("top") or 0)
    largura = int(limites.get("width") or 0)
    altura = int(limites.get("height") or 0)
    if largura < 160 or altura < 120:
        return ""

    if image_grab is None:
        from PIL import ImageGrab

        image_grab = ImageGrab.grab
    imagem = image_grab(
        bbox=(esquerda, topo, esquerda + largura, topo + altura),
        all_screens=True,
    )
    if imagem is None:
        return ""
    imagem = imagem.convert("RGB")
    tons = imagem.resize((32, 18)).convert("L")
    extremos = tons.getextrema()
    if not extremos or int(extremos[1]) <= 8:
        return ""

    cursor = dict(contexto.get("cursor") or {})
    cursor_x_tela = cursor.get("x")
    cursor_y_tela = cursor.get("y")
    if cursor_x_tela is not None and cursor_y_tela is not None:
        cursor_x = int(cursor_x_tela) - esquerda
        cursor_y = int(cursor_y_tela) - topo
        if 0 <= cursor_x < largura and 0 <= cursor_y < altura:
            return _empacotar_foco_cursor(imagem, cursor_x, cursor_y, qualidade)

    from PIL import Image

    reamostragem = getattr(Image, "Resampling", Image).LANCZOS
    imagem.thumbnail((1920, 1080), reamostragem)
    return _codificar_jpeg(imagem, qualidade)
