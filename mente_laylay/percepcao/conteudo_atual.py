"""Resolve o conteúdo que está no centro da atenção atual da Laylay."""

from __future__ import annotations

import re
import time
from typing import Any, Dict


def perceber_conteudo_atual(
    *,
    texto_usuario: str = "",
    mente: Dict[str, Any] | None = None,
    contexto_perceptivo: Dict[str, Any] | None = None,
    pagina: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    estado = dict(mente or {})
    perceptivo = dict(contexto_perceptivo or {})
    pagina_atual = dict(pagina or {})
    texto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip().casefold()
    agora = time.time()
    candidatos: Dict[str, Dict[str, Any]] = {}

    titulo_musica = str(estado.get("musica_atual_titulo") or "").strip()
    if titulo_musica:
        candidatos["musica"] = {
            "tipo": "musica",
            "titulo": titulo_musica,
            "descricao": "",
            "url": str(estado.get("musica_atual_url") or "").strip(),
            "status": str(estado.get("musica_atual_status") or "").strip(),
            "fonte": "player_navegador",
            "ts": float(estado.get("musica_atual_ts") or 0.0),
            "confianca": 0.98,
        }

    titulo_pagina = str(pagina_atual.get("title") or "").strip()
    if titulo_pagina:
        candidatos["pagina"] = {
            "tipo": "pagina",
            "titulo": titulo_pagina,
            "descricao": str(pagina_atual.get("content") or "").strip()[:1200],
            "url": str(pagina_atual.get("url") or "").strip(),
            "status": "visivel",
            "fonte": "extensao_chrome",
            "ts": float(pagina_atual.get("ts") or 0.0),
            "confianca": 0.96,
        }

    titulo_janela = str(perceptivo.get("title") or "").strip()
    if titulo_janela:
        candidatos["app"] = {
            "tipo": "app",
            "titulo": titulo_janela,
            "descricao": str(perceptivo.get("assunto") or "").strip(),
            "url": "",
            "status": "janela_ativa",
            "fonte": str(perceptivo.get("exe") or "sistema").strip(),
            "ts": agora,
            "confianca": 0.92,
        }

    estrutura = dict(estado.get("ultima_estrutura_arquivo_params") or {})
    arquivo = str(
        estado.get("ultimo_caminho_arquivo")
        or estado.get("ultimo_arquivo")
        or estado.get("ultima_pasta")
        or estrutura.get("arquivo_nome")
        or estrutura.get("nome")
        or ""
    ).strip()
    if arquivo:
        candidatos["arquivo"] = {
            "tipo": "arquivo",
            "titulo": arquivo,
            "descricao": str(estrutura.get("arquivo_conteudo") or "").strip()[:800],
            "url": "",
            "status": "recente",
            "fonte": "memoria_arquivos",
            "ts": float(estado.get("ultima_estrutura_arquivo_ts") or estado.get("ts") or 0.0),
            "confianca": 0.9,
        }

    dispositivo = str(estado.get("ultimo_dispositivo_iot") or "").strip()
    if dispositivo:
        candidatos["iot"] = {
            "tipo": "iot",
            "titulo": dispositivo,
            "descricao": str(estado.get("ultimo_ambiente_iot") or "").strip(),
            "url": "",
            "status": str(estado.get("ultimo_estado_iot") or "desconhecido"),
            "fonte": "estado_iot",
            "ts": float(estado.get("ts") or 0.0),
            "confianca": 0.94,
        }

    dominio = ""
    if re.search(r"\b(musica|música|faixa|som|tocando|ouvindo)\b", texto):
        dominio = "musica"
    elif re.search(r"\b(pagina|página|site|aba|guia|artigo|video|vídeo)\b", texto):
        dominio = "pagina"
    elif re.search(r"\b(app|aplicativo|programa|janela|tela)\b", texto):
        dominio = "app"
    elif re.search(r"\b(arquivo|pasta|documento|texto)\b", texto):
        dominio = "arquivo"
    elif re.search(r"\b(dispositivo|ventilador|tomada|luz|lampada|lâmpada)\b", texto):
        dominio = "iot"

    escolhido = dict(candidatos.get(dominio) or {}) if dominio else {}
    if not escolhido and candidatos:
        escolhido = dict(max(candidatos.values(), key=lambda item: float(item.get("ts") or 0.0)))
    if not escolhido:
        return {}
    escolhido["idade_s"] = max(0.0, agora - float(escolhido.get("ts") or agora))
    escolhido["pedido_explicito"] = bool(dominio)
    return escolhido

