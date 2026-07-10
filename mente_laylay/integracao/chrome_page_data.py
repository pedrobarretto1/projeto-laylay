"""Tratamento de PAGE_DATA vindo da extensao Chrome."""

from __future__ import annotations

import threading
from typing import Any, Dict


def processar_page_data(data: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Processa conteudo de pagina recebido e devolve updates ao orquestrador."""
    updates: Dict[str, Any] = {"handled": False}
    if data.get("type") != "PAGE_DATA":
        return updates

    payload = data.get("payload")
    if not payload or not isinstance(payload, dict):
        updates["handled"] = True
        return updates

    url = payload.get("url", "")
    title = payload.get("title", "Sem titulo")
    content = payload.get("content", "")

    ultimo_conteudo = f"SITIO: {title}\nCONTEUDO: {content}"
    updates["ULTIMO_CONTEUDO_PAGINA"] = ultimo_conteudo

    armazenar_contexto_pagina = ctx.get("armazenar_contexto_pagina")
    resumir_pagina_no_dicionario = ctx.get("resumir_pagina_no_dicionario")
    evento_pagina = ctx.get("EVENTO_PAGINA")

    if callable(armazenar_contexto_pagina):
        armazenar_contexto_pagina(url, title, content)
    if callable(resumir_pagina_no_dicionario):
        threading.Thread(target=resumir_pagina_no_dicionario, args=(url,), daemon=True).start()
    if evento_pagina is not None:
        try:
            evento_pagina.set()
        except Exception:
            pass

    print(f"[VISAO] Pagina recebida: {title}")
    updates["handled"] = True
    return updates
