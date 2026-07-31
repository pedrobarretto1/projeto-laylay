"""Transporte de buscas e URLs musicais entre o PC local e o PC B."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import urlparse

from mente_laylay.percepcao.modo_jogo import pedido_foco_explicito


@dataclass(slots=True)
class RotaMusical:
    ctx: Dict[str, Any]
    destino: str = "pc_a"
    texto_original: str = ""

    def abrir(self, url: str, *, query: str = "") -> bool:
        url_limpa = str(url or "").strip()
        if not url_limpa:
            return False
        enviar_pc_b = self.ctx.get("_enviar_pc_b")
        enviar_chrome = self.ctx.get("enviar_comando_chrome")
        abrir_url = self.ctx.get("abrir_url_com_reciclagem")
        permitir_foco = pedido_foco_explicito(self.texto_original)

        if self.destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "open_url", "url": url_limpa})
            return True

        eh_video_youtube = self._eh_video_youtube(url_limpa)

        if self.destino == "ambos":
            ok_local = False
            if eh_video_youtube and callable(enviar_chrome):
                ok_local = bool(enviar_chrome(
                    "youtube_play",
                    {"url": url_limpa, "permitir_foco": permitir_foco},
                ))
            elif query and callable(enviar_chrome):
                ok_local = bool(enviar_chrome(
                    "youtube_search",
                    {"query": query, "permitir_foco": permitir_foco},
                ))
            elif callable(abrir_url):
                try:
                    retorno = abrir_url(
                        url_limpa,
                        auto_click=False,
                        permitir_foco=permitir_foco,
                    )
                    ok_local = retorno is not False
                except Exception:
                    ok_local = False
            if callable(enviar_pc_b):
                enviar_pc_b({"action": "open_url", "url": url_limpa})
            return ok_local

        if eh_video_youtube and callable(enviar_chrome):
            return bool(enviar_chrome(
                "youtube_play",
                {"url": url_limpa, "permitir_foco": permitir_foco},
            ))
        if query and callable(enviar_chrome):
            return bool(enviar_chrome(
                "youtube_search",
                {"query": query, "permitir_foco": permitir_foco},
            ))
        if callable(abrir_url):
            try:
                retorno = abrir_url(
                    url_limpa,
                    auto_click=False,
                    permitir_foco=permitir_foco,
                )
                return retorno is not False
            except Exception:
                return False
        return False

    @staticmethod
    def _eh_video_youtube(url: str) -> bool:
        try:
            parsed = urlparse(str(url or ""))
            host = parsed.netloc.casefold().removeprefix("www.")
            return (
                host == "youtu.be"
                or (host.endswith("youtube.com") and parsed.path.startswith("/watch"))
            )
        except Exception:
            return False
