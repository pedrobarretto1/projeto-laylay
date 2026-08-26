"""Confirma efeitos observáveis de comandos de janelas e navegação."""

from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Callable, Dict

from mente_laylay.percepcao.modo_jogo import pedido_foco_explicito


@dataclass(slots=True)
class ValidadorAmbiente:
    ctx: Dict[str, Any]
    destino: str = "pc_a"
    texto_original: str = ""
    sleep_cb: Callable[[float], Any] = field(default=time.sleep, repr=False)

    def _get(self, nome: str, default: Any = None) -> Any:
        return self.ctx.get(nome, default)

    def _navegador_leitura(self) -> Any:
        return self._get("_registro_navegador_leitura_runtime")

    def _navegador_operacoes(self) -> Any:
        return self._get("_registro_navegador_operacoes_runtime")

    def resolver_estado_alvo(self, nome: str) -> dict:
        resolver = self._get("_resolver_alvo_ambiente")
        if not nome or not callable(resolver):
            return {}
        try:
            return resolver(nome) or {}
        except Exception:
            return {}

    def esperar_programa_fechar(
        self, nome: str, tentativas: int = 5, intervalo: float = 0.2
    ) -> bool:
        if not nome:
            return False
        for _ in range(max(1, tentativas)):
            if not bool(self.resolver_estado_alvo(nome).get("programa_aberto")):
                return True
            try:
                self.sleep_cb(intervalo)
            except Exception:
                pass
        return not bool(self.resolver_estado_alvo(nome).get("programa_aberto"))

    def esperar_aba_fechar(
        self,
        alvo: str,
        aba_antes: dict | None = None,
        tentativas: int = 5,
        intervalo: float = 0.2,
    ) -> bool:
        alvo_limpo = str(alvo or "").strip()
        aba_antes = aba_antes if isinstance(aba_antes, dict) else {}
        navegador = self._navegador_leitura()
        for _ in range(max(1, tentativas)):
            if alvo_limpo:
                if not bool(
                    self.resolver_estado_alvo(alvo_limpo).get("aba_aberta")
                ):
                    return True
            elif navegador is not None:
                try:
                    aba_depois = navegador.aba_ativa() or {}
                except Exception:
                    aba_depois = {}
                url_antes = str(aba_antes.get("url") or "").strip().lower()
                titulo_antes = str(aba_antes.get("title") or "").strip().lower()
                url_depois = str(aba_depois.get("url") or "").strip().lower()
                titulo_depois = str(aba_depois.get("title") or "").strip().lower()
                if (url_antes and url_antes != url_depois) or (
                    titulo_antes and titulo_antes != titulo_depois
                ):
                    return True
            try:
                self.sleep_cb(intervalo)
            except Exception:
                pass
        if alvo_limpo:
            return not bool(
                self.resolver_estado_alvo(alvo_limpo).get("aba_aberta")
            )
        return False

    @staticmethod
    def host_para_alvo_web(valor: str) -> str:
        try:
            bruto = str(valor or "").strip()
            if not bruto:
                return ""
            host = str(urllib.parse.urlparse(bruto).netloc or "").strip().lower()
            return host[4:] if host.startswith("www.") else host
        except Exception:
            return ""

    def alvo_preciso_para_aba(self, alvo: str) -> str:
        alvo_limpo = str(alvo or "").strip()
        if not alvo_limpo:
            return ""
        montar_url = self._get("_montar_url_site_ou_busca")
        url_ref = montar_url(alvo_limpo) if callable(montar_url) else alvo_limpo
        host = self.host_para_alvo_web(url_ref)
        try:
            partes = urllib.parse.urlparse(str(url_ref or ""))
            consulta = urllib.parse.parse_qs(partes.query)
            host_busca = host in {
                "google.com", "google.com.br", "bing.com",
                "duckduckgo.com", "search.yahoo.com",
            }
            # Um nome livre como "Prime Video" pode ser convertido pelo
            # montador em uma busca do Google. Nesse caso, ``google.com`` não
            # é o alvo da aba: o título/nome original é. Preservá-lo permite
            # que a extensão encontre a aba correta por URL ou título.
            if host_busca and (
                str(partes.path or "").casefold().startswith("/search")
                or "q" in consulta
            ):
                return alvo_limpo
        except (TypeError, ValueError):
            pass
        return host or alvo_limpo

    def aba_corresponde_url(
        self, alvo: str, url_esperada: str, aba: dict | None
    ) -> bool:
        aba = aba if isinstance(aba, dict) else {}
        url_atual = str(aba.get("url") or "").strip().lower()
        titulo_atual = str(
            aba.get("title") or aba.get("titulo") or ""
        ).strip().lower()
        alvo_ref = str(alvo or "").strip().lower()
        url_ref = str(url_esperada or "").strip().lower()
        host_ref = self.host_para_alvo_web(url_ref) or self.host_para_alvo_web(
            alvo_ref
        )
        if url_ref and url_atual.startswith(url_ref):
            return True
        if host_ref and (host_ref in url_atual or host_ref in titulo_atual):
            return True
        return bool(alvo_ref and (alvo_ref in url_atual or alvo_ref in titulo_atual))

    def esperar_url_abrir(
        self,
        url: str,
        *,
        alvo: str = "",
        tentativas: int = 12,
        intervalo: float = 0.25,
    ) -> bool:
        url_limpa = str(url or "").strip()
        alvo_ref = self.alvo_preciso_para_aba(alvo or url_limpa)
        navegador = self._navegador_leitura()
        for _ in range(max(1, tentativas)):
            if alvo_ref and bool(
                self.resolver_estado_alvo(alvo_ref).get("aba_aberta")
            ):
                return True
            if navegador is not None:
                try:
                    aba_atual = navegador.aba_ativa() or {}
                except Exception:
                    aba_atual = {}
                if self.aba_corresponde_url(alvo_ref, url_limpa, aba_atual):
                    return True
            try:
                self.sleep_cb(intervalo)
            except Exception:
                pass
        return False

    def abrir_url_com_validacao(
        self, url: str, *, alvo: str = "", auto_click: bool = False
    ) -> bool:
        url_limpa = str(url or "").strip()
        if not url_limpa:
            return False
        enviar_pc_b = self._get("_enviar_pc_b")
        if self.destino == "pc_b" and callable(enviar_pc_b):
            enviar_pc_b({"action": "open_url", "url": url_limpa})
            return True
        navegador = self._navegador_operacoes()
        if navegador is None:
            return False
        try:
            retorno = navegador.abrir_url(
                url_limpa,
                auto_click=auto_click,
                permitir_foco=pedido_foco_explicito(self.texto_original),
            )
            if retorno is False:
                return False
            return self.esperar_url_abrir(url_limpa, alvo=alvo or url_limpa)
        except Exception:
            return False
