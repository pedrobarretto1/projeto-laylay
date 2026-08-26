"""Fonte automatizada permitida para Path of Exile 2.

Maxroll é mantida no catálogo editorial, mas não é coletada automaticamente:
o site bloqueia esse tipo de acesso. A API MediaWiki da comunidade fornece
conteúdo estruturado e URLs de procedência sem abrir um navegador.
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from typing import Any, Callable, Mapping

import requests


POE2_WIKI_API = "https://www.poe2wiki.net/w/api.php"
MAXROLL_POE2 = "https://maxroll.gg/poe2"


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", base).strip()


def _pontuar(termo: str, titulo: str) -> int:
    consulta, nome = _normalizar(termo), _normalizar(titulo)
    if consulta == nome:
        return 100
    tokens = set(consulta.split())
    presentes = sum(token in nome.split() for token in tokens)
    return int(70 * presentes / max(1, len(tokens)))


class FontePoe2Wiki:
    nome = "poe2wiki"

    def __init__(
        self,
        *,
        requests_get: Callable[..., Any] = requests.get,
        timeout_s: float = 2.4,
        clock: Callable[[], float] = time.time,
        thread_factory: Callable[..., Any] = threading.Thread,
    ) -> None:
        self.requests_get = requests_get
        self.timeout_s = max(0.3, float(timeout_s))
        self.clock = clock
        self.thread_factory = thread_factory
        self.headers = {
            "User-Agent": "LaylayAssistant/2.5 (personal game research; local)",
            "Accept": "application/json",
        }

    def _get(self, params: Mapping[str, Any]) -> dict[str, Any]:
        resposta = self.requests_get(
            POE2_WIKI_API, params=dict(params), headers=self.headers,
            timeout=self.timeout_s,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        return dict(dados) if isinstance(dados, dict) else {}

    @staticmethod
    def _pagina_para_fonte(pagina: Mapping[str, Any], termo: str) -> dict[str, Any]:
        titulo = str(pagina.get("title") or termo).strip()
        resumo = re.sub(r"\s+", " ", str(pagina.get("extract") or "")).strip()
        if not resumo:
            return {}
        url = str(pagina.get("fullurl") or "").strip()
        if not url:
            url = "https://www.poe2wiki.net/wiki/" + titulo.replace(" ", "_")
        return {
            "fonte": "poe2wiki",
            "titulo": titulo[:160],
            "url": url[:500],
            "resumo": resumo[:1100],
            "confianca": round(min(0.94, 0.55 + _pontuar(termo, titulo) / 260), 3),
            "correspondencia": _pontuar(termo, titulo),
            "consulta": termo,
        }

    def consultar(self, termo: str) -> dict[str, Any]:
        termo = re.sub(r"\s+", " ", str(termo or "")).strip()[:100]
        if len(termo) < 2:
            return {}
        comum = {
            "action": "query", "format": "json", "prop": "extracts|info",
            "exintro": 1, "explaintext": 1, "redirects": 1, "inprop": "url",
        }
        direto = self._get({**comum, "titles": termo})
        paginas = list(dict((direto.get("query") or {}).get("pages") or {}).values())
        for pagina in paginas:
            if isinstance(pagina, Mapping) and "missing" not in pagina:
                fonte = self._pagina_para_fonte(pagina, termo)
                if fonte:
                    return fonte
        busca = self._get({
            **comum, "generator": "search", "gsrsearch": termo, "gsrlimit": 3,
        })
        candidatas = [
            pagina for pagina in dict((busca.get("query") or {}).get("pages") or {}).values()
            if isinstance(pagina, Mapping)
        ]
        candidatas.sort(key=lambda pagina: _pontuar(termo, pagina.get("title")), reverse=True)
        if not candidatas or _pontuar(termo, candidatas[0].get("title")) < 45:
            return {}
        return self._pagina_para_fonte(candidatas[0], termo)

    def pesquisar(self, item: Mapping[str, Any]) -> list[dict[str, Any]]:
        consultas_brutas = list(item.get("consultas_pesquisa") or [])
        consultas: list[dict[str, Any]] = []
        if consultas_brutas:
            for consulta in consultas_brutas[:5]:
                if not isinstance(consulta, Mapping):
                    continue
                termo = str(consulta.get("termo") or "").strip()
                if termo:
                    consultas.append({
                        "termo": termo,
                        "tipo": str(consulta.get("tipo") or "geral"),
                        "prioridade": int(consulta.get("prioridade") or 0),
                    })
        else:
            termos = list(item.get("termos_pesquisa") or [])
            termos.extend((item.get("base"), item.get("categoria")))
            termos = list(dict.fromkeys(
                str(valor or "").strip() for valor in termos if str(valor or "").strip()
            ))[:3]
            consultas = [
                {"termo": termo, "tipo": "geral", "prioridade": 50}
                for termo in termos
            ]
        if not consultas:
            return []
        resultados: list[dict[str, Any]] = []
        lock_resultados = threading.Lock()

        def consultar_protegido(consulta: Mapping[str, Any]) -> None:
            termo = str(consulta.get("termo") or "")
            try:
                fonte = dict(self.consultar(termo) or {})
            except Exception:
                return
            if not fonte:
                return
            tipo = str(consulta.get("tipo") or "geral")
            minimo = 70 if tipo == "nome_unico" else 60 if tipo in {
                "base", "base_candidata", "nome_candidato",
            } else 35
            correspondencia = int(fonte.get("correspondencia") or _pontuar(
                termo, fonte.get("titulo"),
            ))
            if correspondencia < minimo:
                return
            fonte["tipo_evidencia"] = tipo
            fonte["consulta"] = termo
            fonte["correspondencia"] = correspondencia
            fonte["prioridade_pesquisa"] = int(consulta.get("prioridade") or 0)
            with lock_resultados:
                urls = {resultado.get("url") for resultado in resultados}
                if fonte.get("url") not in urls:
                    resultados.append(fonte)

        # Threads daemon preservam a pesquisa paralela, mas não são registradas
        # pelo atexit de concurrent.futures. Assim uma requisição de rede que
        # esteja terminando não prende o encerramento da Laylay.
        threads = [
            self.thread_factory(
                target=lambda consulta=consulta: consultar_protegido(consulta),
                name=f"Laylay-Pesquisa-PoE2-{indice}",
                daemon=True,
            )
            for indice, consulta in enumerate(consultas, start=1)
        ]
        for thread in threads:
            thread.start()
        prazo = time.monotonic() + self.timeout_s * 2 + 0.5
        for thread in threads:
            restante = max(0.0, prazo - time.monotonic())
            if restante <= 0:
                break
            thread.join(timeout=restante)
        resultados.sort(key=lambda fonte: (
            int(fonte.get("prioridade_pesquisa") or 0),
            int(fonte.get("correspondencia") or 0),
            float(fonte.get("confianca") or 0.0),
        ), reverse=True)
        return resultados[:3]
