"""Runtime de busca musical da Laylay.

Guarda a fila de tentativas e a verificacao leve de resultado, mas recebe
callbacks do cerebro principal para falar, chamar IA e executar Chrome.
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Callable

import requests


class BuscaMusicalRuntime:
    def __init__(
        self,
        *,
        extrair_resultados_youtube: Callable[[str, str, int], list],
        abrir_url: Callable[[str], Any],
        youtube_play: Callable[[str], Any] | None = None,
        falar: Callable[[str, str, int], Any] | None = None,
        enviar_mensagem: Callable[..., str] | None = None,
        log: Callable[[str], None] | None = None,
    ) -> None:
        self.extrair_resultados_youtube = extrair_resultados_youtube
        self.abrir_url = abrir_url
        self.youtube_play = youtube_play
        self.falar = falar
        self.enviar_mensagem = enviar_mensagem
        self.log = log or print
        self.fila: list[str] = []
        self.query: str = ""
        self.ultima_verificada: str = ""

    def tentar_proxima(self) -> bool:
        if self.fila:
            prox_link = self.fila.pop(0)
            self.log(f"[CORRETOR] Tentando proximo link para '{self.query}': {prox_link}")
            self.abrir_url(prox_link)
            return True
        self.log("[CORRETOR] Fila esgotada.")
        if callable(self.falar):
            self.falar("Não consegui achar a música certa mesmo tentando os 5 primeiros resultados.", "triste", 1)
        self.query = ""
        return False

    def verificar_autonoma(self, titulo_tocado: str) -> None:
        if not self.query:
            return

        query = self.query
        prompt = f"""
Você é um juiz de buscas de música. O usuário pediu a música: "{query}"
O vídeo que começou a tocar no YouTube se chama: "{titulo_tocado}"
Esta é a música correta (ou clipe oficial, lyric video etc)? Atenção a nomes de artistas/feats.
Responda APENAS "SIM" se for a música certa, ou "NAO" se for o vídeo errado.
"""
        mensagens = [{"role": "system", "content": prompt}]
        try:
            resp = self.enviar_mensagem(mensagens, _com_tools=False) if callable(self.enviar_mensagem) else "SIM"
            if "NAO" in str(resp).upper() or "NÃO" in str(resp).upper():
                self.log(f"[IA-CORRETOR] '{titulo_tocado}' NÃO é a musica pedida ({query}).")
                if callable(self.falar):
                    self.falar("Ihh, tocou o vídeo errado. Vou pular pro próximo da busca.", "irritada", 1)
                self.tentar_proxima()
            else:
                self.log(f"[IA-CORRETOR] Aprovado '{titulo_tocado}' para '{query}'.")
                self.query = ""
                self.fila.clear()
        except Exception as e:
            self.log(f"Erro no verificador: {e}")

    def buscar_primeiro_video(self, query: str, *, tipo_resultado: str = "faixa") -> str | None:
        """Scraper leve para encontrar o primeiro video valido do YouTube."""
        candidatos = self.buscar_resultados(query, limite=8, tipo_resultado=tipo_resultado)
        if candidatos:
            link = str(candidatos[0].get("url") or "").strip()
            if link:
                self.log(f"✅ [YT-SCRAPER] Encontrado: {link}")
                return link
        return None

    def buscar_resultados(
        self,
        query: str,
        limite: int = 5,
        *,
        tipo_resultado: str = "faixa",
    ) -> list[dict[str, Any]]:
        """Consulta títulos sem abrir ou reproduzir nenhum resultado."""
        try:
            self.log(f"🔍 [YT-SCRAPER] Procurando para: '{query}'")
            url_busca = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(str(query or ''))}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            res = requests.get(url_busca, headers=headers, timeout=5)
            if res.status_code == 200:
                try:
                    resultados = self.extrair_resultados_youtube(
                        res.text,
                        query,
                        max(1, int(limite)),
                        tipo_resultado=tipo_resultado,
                    )
                except TypeError:
                    resultados = self.extrair_resultados_youtube(
                        res.text, query, max(1, int(limite))
                    )
                return list(resultados)
        except Exception as e:
            self.log(f"⚠️ [YT-SCRAPER] Erro: {e}")
        return []

def criar_busca_musical_runtime(**kwargs: Any) -> BuscaMusicalRuntime:
    return BuscaMusicalRuntime(**kwargs)
