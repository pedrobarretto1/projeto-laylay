"""Memoria curta de paginas vistas pela Laylay."""

from __future__ import annotations

import time
from typing import Any, Callable, Dict


class ContextoPaginas:
    def __init__(self, *, limite_paginas: int = 6, limite_contexto_chars: int = 10000) -> None:
        self.paginas: Dict[str, Dict[str, Any]] = {}
        self.cache: Dict[str, Any] = {"versao": -1, "texto": ""}
        self.versao = 0
        self.ultimo_conteudo = ""
        self.limite_paginas = int(limite_paginas)
        self.limite_contexto_chars = int(limite_contexto_chars)

    def definir_ultimo_conteudo(self, conteudo: str) -> None:
        self.ultimo_conteudo = str(conteudo or "")

    def atual(self) -> Dict[str, Any]:
        if not self.paginas:
            return {}
        url, info = max(self.paginas.items(), key=lambda item: float(item[1].get("ts") or 0.0))
        return {"url": url, **dict(info or {})}

    def armazenar(self, url: str, title: str, content: str) -> None:
        agora = time.time()
        conteudo_limpo = str(content or "")[:6000].strip()

        self.paginas[str(url or "")] = {
            "title": str(title or ""),
            "content": conteudo_limpo,
            "ts": agora,
            "resumo": "",
        }

        if len(self.paginas) > self.limite_paginas:
            mais_antiga = min(self.paginas.items(), key=lambda x: x[1]["ts"])
            del self.paginas[mais_antiga[0]]

        self.versao += 1
        self.cache["versao"] = -1
        self.cache["texto"] = ""

        print(f"📖 [VISÃO] Página salva no dicionário: {str(title or '')[:60]}... ({len(conteudo_limpo)} chars)")

    def texto_contexto(self) -> str:
        if not self.paginas:
            return ""

        if self.cache.get("texto") and int(self.cache.get("versao", -1)) == int(self.versao):
            return str(self.cache.get("texto") or "")

        ordenado = sorted(self.paginas.items(), key=lambda x: x[1]["ts"], reverse=True)

        texto = "\n\n📖 **DICIONÁRIO DE CONTEXTO ATUAL** (Páginas recentes abertas):\n"
        chars_usados = 0

        for url, info in ordenado:
            if chars_usados >= self.limite_contexto_chars:
                break

            idade_min = int((time.time() - info["ts"]) / 60)
            resumo = info.get("resumo", "")
            conteudo = info.get("content", "")
            pode_usar = self.limite_contexto_chars - chars_usados
            conteudo_poda = conteudo[:pode_usar]

            texto += f"• {info['title']}\n  📍 {url}\n  ⏱️ há {idade_min}min\n"
            if resumo:
                texto += f"  📝 Resumo: {resumo}\n"
            texto += f"  📄 Conteúdo:\n{conteudo_poda}\n\n"

            chars_usados += len(conteudo_poda)

        texto = texto.strip()
        self.cache = {"versao": self.versao, "texto": texto}
        return texto

    def resumir(self, url: str, *, enviar_mensagem: Callable[..., Any] | None) -> None:
        if url not in self.paginas:
            return

        conteudo = self.paginas[url]["content"]
        prompt_resumo = f"""
    Resuma em NO MÁXIMO 2 frases o conteúdo principal desta página.
    Foque apenas no que realmente importa para o usuário.
    Página: {self.paginas[url]['title']}

    CONTEÚDO:
    {conteudo[:4000]}
    """

        mensagens = [
            {"role": "system", "content": "Você é um resumidor extremamente conciso."},
            {"role": "user", "content": prompt_resumo},
        ]

        try:
            resumo = enviar_mensagem(mensagens, _com_tools=False) if callable(enviar_mensagem) else ""
            self.paginas[url]["resumo"] = str(resumo or "").strip()
            self.versao += 1
            self.cache = {"versao": -1, "texto": ""}
            print(f"📝 [VISÃO] Resumo gerado para {self.paginas[url]['title'][:50]}...")
        except Exception:
            pass
