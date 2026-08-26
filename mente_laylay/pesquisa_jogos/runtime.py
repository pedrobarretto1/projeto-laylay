"""Coordena fontes por jogo com cache em memória e SQLite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from contextlib import closing
from typing import Any, Callable, Mapping

from .contratos import normalizar_item_visual, planejar_pesquisa_item
from .poe2 import FontePoe2Wiki, MAXROLL_POE2


class PesquisaJogosRuntime:
    def __init__(
        self,
        *,
        db_path: str = "",
        fonte_poe2: Any = None,
        ttl_s: float = 21600.0,
        clock: Callable[[], float] = time.time,
        log: Callable[[str], Any] = print,
        registrar_falha: Callable[..., Any] | None = None,
    ) -> None:
        self.db_path = str(db_path or "")
        self.fonte_poe2 = fonte_poe2 or FontePoe2Wiki(clock=clock)
        self.ttl_s = max(60.0, float(ttl_s))
        self.clock = clock
        self.log = log
        self.registrar_falha = registrar_falha
        self._lock = threading.RLock()
        self._cache: dict[str, dict[str, Any]] = {}
        if self.db_path:
            self._inicializar_cache()

    def _falha(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("pesquisa_jogos", codigo, erro=erro)

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _inicializar_cache(self) -> None:
        try:
            with closing(self._conectar()) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS jogos_pesquisa_cache (
                        chave TEXT PRIMARY KEY, payload_json TEXT NOT NULL,
                        obtido_em REAL NOT NULL, expira_em REAL NOT NULL
                    )
                """)
                conn.commit()
        except Exception as erro:
            self.log(f"⚠️ [PESQUISA JOGO:CACHE] SQLite indisponível: {type(erro).__name__}")
            self._falha("cache_inicializacao", erro)

    @staticmethod
    def _jogo_poe2(identidade: Mapping[str, Any]) -> bool:
        texto = " ".join((
            str(identidade.get("nome_candidato") or ""),
            str(identidade.get("titulo") or ""),
            str(identidade.get("processo") or ""),
        )).casefold()
        return "path of exile 2" in texto or "poe2" in texto

    @staticmethod
    def _chave(
        identidade: Mapping[str, Any], item: Mapping[str, Any],
        plano: Mapping[str, Any] | None = None,
    ) -> str:
        plano = dict(plano or planejar_pesquisa_item(item))
        base = json.dumps({
            "jogo": str(identidade.get("chave") or identidade.get("nome_candidato") or ""),
            "estrategia": plano.get("estrategia"),
            "consultas": [
                {"termo": consulta.get("termo"), "tipo": consulta.get("tipo")}
                for consulta in list(plano.get("consultas") or [])
            ],
        }, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def _obter_cache(self, chave: str) -> dict[str, Any]:
        agora = float(self.clock())
        with self._lock:
            memoria = dict(self._cache.get(chave) or {})
            if memoria and float(memoria.get("expira_em") or 0.0) > agora:
                return {**dict(memoria.get("payload") or {}), "cache": True}
        if not self.db_path:
            return {}
        try:
            with closing(self._conectar()) as conn:
                row = conn.execute(
                    "SELECT payload_json, expira_em FROM jogos_pesquisa_cache WHERE chave = ?",
                    (chave,),
                ).fetchone()
            if row and float(row[1]) > agora:
                payload = json.loads(row[0])
                if isinstance(payload, dict):
                    return {**payload, "cache": True}
        except Exception as erro:
            self._falha("cache_leitura", erro)
        return {}

    def _salvar_cache(self, chave: str, payload: Mapping[str, Any]) -> None:
        agora, expira = float(self.clock()), float(self.clock()) + self.ttl_s
        seguro = dict(payload or {})
        with self._lock:
            self._cache[chave] = {"payload": seguro, "expira_em": expira}
        if not self.db_path:
            return
        try:
            with closing(self._conectar()) as conn:
                conn.execute("""
                    INSERT INTO jogos_pesquisa_cache(chave, payload_json, obtido_em, expira_em)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(chave) DO UPDATE SET payload_json=excluded.payload_json,
                    obtido_em=excluded.obtido_em, expira_em=excluded.expira_em
                """, (chave, json.dumps(seguro, ensure_ascii=False), agora, expira))
                conn.commit()
        except Exception as erro:
            self._falha("cache_escrita", erro)

    def pesquisar_item(
        self,
        item: Mapping[str, Any],
        contexto: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        item_limpo = normalizar_item_visual(item)
        plano = planejar_pesquisa_item(item_limpo)
        dados_contexto = dict(contexto or {})
        identidade = dict(dados_contexto.get("identidade") or {})
        confianca_visual = float(item_limpo.get("confianca") or 0.0)
        if confianca_visual < 0.45:
            return {"ok": False, "motivo": "leitura_visual_incerta", "fontes": []}
        if not self._jogo_poe2(identidade):
            return {"ok": False, "motivo": "jogo_sem_adaptador", "fontes": []}
        if not plano.get("consultas"):
            return {"ok": False, "motivo": "item_sem_termos_confiaveis", "fontes": []}
        chave = self._chave(identidade, item_limpo, plano)
        cache = self._obter_cache(chave)
        if cache:
            self.log(
                f"⚡ [PESQUISA JOGO] cache local usado | "
                f"estratégia={plano.get('estrategia')}"
            )
            return cache
        inicio = time.perf_counter()
        item_pesquisa = {
            **item_limpo,
            "consultas_pesquisa": list(plano.get("consultas") or []),
        }
        fontes = list(self.fonte_poe2.pesquisar(item_pesquisa) or [])
        resultado = {
            "ok": bool(fontes),
            "jogo": "Path of Exile 2",
            "item": item_limpo,
            "fontes": fontes[:3],
            "estrategia": plano.get("estrategia"),
            "consultas": list(plano.get("consultas") or []),
            "nome_procedural_ignorado": bool(plano.get("nome_procedural_ignorado")),
            "leitura_visual_incerta": confianca_visual < 0.55,
            "fonte_editorial_manual": {
                "nome": "Maxroll", "url": MAXROLL_POE2,
                "motivo": "acesso automatizado bloqueado; não usada como evidência automática",
            },
            "obtido_em": float(self.clock()),
            "latencia_ms": round((time.perf_counter() - inicio) * 1000, 1),
            "cache": False,
        }
        if fontes:
            self._salvar_cache(chave, resultado)
        self.log(
            f"🔎 [PESQUISA JOGO] estratégia={plano.get('estrategia')} "
            f"consultas={len(plano.get('consultas') or [])} fontes={len(fontes)} "
            f"latência={resultado['latencia_ms']:.0f}ms"
        )
        return resultado


def criar_pesquisa_jogos_runtime(**kwargs: Any) -> PesquisaJogosRuntime:
    return PesquisaJogosRuntime(**kwargs)
