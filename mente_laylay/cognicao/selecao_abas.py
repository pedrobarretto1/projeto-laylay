"""Selecao cognitiva de abas do navegador para a Laylay."""

from __future__ import annotations

import json
import re
import os
from typing import Any, Callable, Dict


def parsear_ids_lista(texto: str) -> list[int]:
    if not isinstance(texto, str):
        return []
    candidato = texto.strip()
    trecho = re.search(r"\[[^\]]*\]", candidato)
    if trecho:
        candidato = trecho.group(0)
    try:
        dados = json.loads(candidato)
    except Exception:
        return []
    if not isinstance(dados, list):
        return []

    ids: list[int] = []
    for valor in dados:
        try:
            numero = int(valor)
        except (TypeError, ValueError):
            continue
        if numero > 0:
            ids.append(numero)
    return ids


def selecionar_abas_para_fechar(
    comando_usuario: str,
    abas: Any,
    *,
    post_chat: Callable[[dict, dict], Any],
    api_key: str,
    model: str,
    http_referer: str,
    app_title: str,
) -> list[int]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": http_referer,
        "X-Title": app_title,
    }
    abas_filtradas: list[dict] = []
    for aba in abas if isinstance(abas, list) else []:
        if not isinstance(aba, dict):
            continue
        tab_id = aba.get("id")
        url = str(aba.get("url") or "")
        titulo = str(aba.get("title") or "")
        if isinstance(tab_id, int) and ("netflix.com" in url or "Netflix" in titulo):
            continue
        abas_filtradas.append({"id": tab_id, "url": url, "title": titulo})

    prompt = (
        f'Você é um gerente de abas. O usuário quer: "{comando_usuario}". '
        f"Analise esta lista de abas: {json.dumps(abas_filtradas, ensure_ascii=False)}. "
        "Retorne APENAS uma lista de IDs (ex: [102, 144]) das abas que correspondem ao pedido. "
        'Se o pedido for "vazias", foque em URLs como "chrome://newtab", "about:blank" ou abas sem título. '
        'Se for "música", procure por termos de artistas ou "watch?v=" em abas de mídia.'
    )
    data = {
        "model": model,
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.0,
    }
    try:
        response = post_chat(headers, data)
        response.raise_for_status()
        payload = response.json()
        resposta = str(payload["choices"][0]["message"]["content"] or "")
        return parsear_ids_lista(resposta)
    except Exception:
        return []


class SelecaoAbasRuntime:
    def __init__(self, *, namespace_getter: Callable[[], Dict[str, Any]]) -> None:
        self.namespace_getter = namespace_getter

    def selecionar(self, comando_usuario: str, abas: Any) -> list[int]:
        ns = self.namespace_getter() or {}
        return selecionar_abas_para_fechar(
            comando_usuario,
            abas,
            post_chat=ns["post_chat"],
            api_key=os.environ.get("OPENROUTER_API_KEY") or ns.get("api_key", ""),
            model=ns["model"],
            http_referer=ns.get("http_referer", ""),
            app_title=ns.get("app_title", ""),
        )


def criar_selecao_abas_runtime(**kwargs: Any) -> SelecaoAbasRuntime:
    return SelecaoAbasRuntime(**kwargs)
