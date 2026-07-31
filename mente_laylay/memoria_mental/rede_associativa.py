"""Rede associativa segura da mente única da Laylay.

Esta primeira versão trabalha em modo sombra: observa conceitos estruturados,
forma associações e mede ativações, mas não altera prompts, falas ou comandos.
O texto bruto da conversa nunca é persistido nesta camada.
"""

from __future__ import annotations

import json
import math
import os
import queue
import re
import sqlite3
import threading
import time
import unicodedata
from itertools import combinations
from typing import Any, Callable, Iterable, Mapping


MODOS_VALIDOS = frozenset({"desligado", "sombra", "continuidade", "ativo"})
_FEEDBACK_VALIDOS = frozenset({"aceita", "recusa", "silencio", "correcao"})
_TIPOS_VALIDOS = frozenset({
    "aplicativo", "contexto", "dominio", "emocao", "escopo", "intencao",
    "periodo", "resultado", "alvo", "topico",
})
_RE_SENSIVEL = re.compile(
    r"(?:https?://|www\.|\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b|"
    r"\b(?:api[_ -]?key|token|password|senha)\b|[a-z]:[\\/]|[\\/]{2,})",
    re.IGNORECASE,
)


def _texto_seguro(valor: Any, limite: int = 96) -> str:
    texto = re.sub(r"\s+", " ", str(valor or "").strip())
    if not texto or _RE_SENSIVEL.search(texto):
        return ""
    texto = "".join(ch for ch in texto if ch.isprintable())
    return texto[:limite].strip()


def _codigo(valor: Any, limite: int = 96) -> str:
    seguro = _texto_seguro(valor, limite)
    if not seguro:
        return ""
    base = unicodedata.normalize("NFKD", seguro.casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9_. -]+", " ", base)
    return re.sub(r"\s+", "_", base).strip("_.-")[:limite]


def _numero(valor: Any, padrao: float, minimo: float, maximo: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        numero = padrao
    return max(minimo, min(maximo, numero))


class RepositorioRedeAssociativa:
    """Persistência bounded e concorrente no SQLite principal da mente."""

    def __init__(
        self,
        db_path: str,
        *,
        clock: Callable[[], float] = time.time,
        max_nos: int = 4000,
        max_conexoes: int = 12000,
    ) -> None:
        self.db_path = str(db_path)
        self.clock = clock
        self.max_nos = max(200, int(max_nos))
        self.max_conexoes = max(500, int(max_conexoes))
        self._init_db()

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 15000")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._conectar() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS rede_associativa_nos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave TEXT NOT NULL UNIQUE,
                    tipo TEXT NOT NULL,
                    rotulo TEXT NOT NULL,
                    confianca REAL NOT NULL DEFAULT 0.5,
                    ativacao_base REAL NOT NULL DEFAULT 0.1,
                    proveniencia TEXT NOT NULL DEFAULT 'observacao_estruturada',
                    criado_ts REAL NOT NULL,
                    atualizado_ts REAL NOT NULL,
                    ultimo_uso_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rede_associativa_conexoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origem_id INTEGER NOT NULL,
                    destino_id INTEGER NOT NULL,
                    relacao TEXT NOT NULL DEFAULT 'coocorre',
                    peso REAL NOT NULL DEFAULT 0.1,
                    confianca REAL NOT NULL DEFAULT 0.5,
                    evidencias INTEGER NOT NULL DEFAULT 1,
                    contradicoes INTEGER NOT NULL DEFAULT 0,
                    proveniencia TEXT NOT NULL DEFAULT 'observacao_estruturada',
                    status TEXT NOT NULL DEFAULT 'observando',
                    criado_ts REAL NOT NULL,
                    atualizado_ts REAL NOT NULL,
                    UNIQUE(origem_id, destino_id, relacao),
                    FOREIGN KEY(origem_id) REFERENCES rede_associativa_nos(id) ON DELETE CASCADE,
                    FOREIGN KEY(destino_id) REFERENCES rede_associativa_nos(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS rede_associativa_ativacoes (
                    no_id INTEGER PRIMARY KEY,
                    intensidade REAL NOT NULL DEFAULT 0.0,
                    origem_evento TEXT NOT NULL DEFAULT '',
                    contexto_json TEXT NOT NULL DEFAULT '{}',
                    vezes INTEGER NOT NULL DEFAULT 1,
                    atualizado_ts REAL NOT NULL,
                    FOREIGN KEY(no_id) REFERENCES rede_associativa_nos(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS rede_associativa_feedback (
                    assinatura TEXT PRIMARY KEY,
                    contexto_json TEXT NOT NULL DEFAULT '{}',
                    aceitas INTEGER NOT NULL DEFAULT 0,
                    recusas INTEGER NOT NULL DEFAULT 0,
                    silencios INTEGER NOT NULL DEFAULT 0,
                    correcoes INTEGER NOT NULL DEFAULT 0,
                    aplicadas_aceitas INTEGER NOT NULL DEFAULT 0,
                    aplicadas_recusas INTEGER NOT NULL DEFAULT 0,
                    aplicadas_silencios INTEGER NOT NULL DEFAULT 0,
                    aplicadas_correcoes INTEGER NOT NULL DEFAULT 0,
                    criado_ts REAL NOT NULL,
                    atualizado_ts REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_rede_conexoes_origem
                    ON rede_associativa_conexoes(origem_id, status, peso DESC);
                CREATE INDEX IF NOT EXISTS idx_rede_conexoes_destino
                    ON rede_associativa_conexoes(destino_id, status, peso DESC);
                CREATE INDEX IF NOT EXISTS idx_rede_nos_tipo
                    ON rede_associativa_nos(tipo, ultimo_uso_ts DESC);
                CREATE INDEX IF NOT EXISTS idx_rede_feedback_atualizado
                    ON rede_associativa_feedback(atualizado_ts DESC);
                """
            )
            # A versão inicial ligava todos os elementos do turno entre si.
            # Mantemos esses dados para auditoria, mas eles não podem participar
            # da propagação nova porque contexto genérico virava uma ponte falsa.
            conn.execute(
                """
                UPDATE rede_associativa_conexoes
                SET status = 'legado_sombra'
                WHERE relacao = 'coocorre' AND status = 'observando'
                """
            )

    def registrar_feedback(
        self,
        conceitos: Iterable[Mapping[str, Any]],
        *,
        resultado: str,
        evidencias_minimas: int = 3,
    ) -> dict[str, Any]:
        """Registra plasticidade contextual sem transformar associação em fato.

        Os dois primeiros sinais são somente acumulados. A partir da terceira
        amostra, apenas feedbacks ainda não aplicados ajustam conexões já
        observadas, o que torna o processo gradual e idempotente.
        """
        resultado_norm = _codigo(resultado, 24)
        if resultado_norm not in _FEEDBACK_VALIDOS:
            return {"status": "ignorado", "resultado": resultado_norm}
        itens = self._normalizar_conceitos(conceitos)
        if len(itens) < 2:
            return {"status": "ignorado", "resultado": resultado_norm}

        # O episódio de feedback é também uma observação estruturada. Isso
        # garante que os nós existam, sem persistir a frase original do usuário.
        self.registrar_contexto(
            itens,
            origem_evento="feedback_associativo",
            proveniencia="feedback_estruturado",
        )
        chaves = sorted(item["chave"] for item in itens)
        assinatura = "|".join(chaves)
        contexto_json = json.dumps(
            {"chaves": chaves[:8]}, ensure_ascii=False, separators=(",", ":"),
        )
        campo = {
            "aceita": "aceitas", "recusa": "recusas",
            "silencio": "silencios", "correcao": "correcoes",
        }[resultado_norm]
        agora = float(self.clock())
        with self._conectar() as conn:
            conn.execute(
                """
                INSERT INTO rede_associativa_feedback(
                    assinatura, contexto_json, criado_ts, atualizado_ts
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(assinatura) DO UPDATE SET
                    contexto_json=excluded.contexto_json,
                    atualizado_ts=excluded.atualizado_ts
                """,
                (assinatura, contexto_json, agora, agora),
            )
            conn.execute(
                f"UPDATE rede_associativa_feedback SET {campo} = {campo} + 1 WHERE assinatura = ?",
                (assinatura,),
            )
            perfil = conn.execute(
                "SELECT * FROM rede_associativa_feedback WHERE assinatura = ?",
                (assinatura,),
            ).fetchone()
            amostras = sum(int(perfil[nome]) for nome in ("aceitas", "recusas", "silencios", "correcoes"))
            if amostras < max(3, int(evidencias_minimas)):
                return {
                    "status": "observando", "resultado": resultado_norm,
                    "amostras": amostras, "conexoes_ajustadas": 0,
                }

            pendentes = {
                nome: int(perfil[nome]) - int(perfil[f"aplicadas_{nome}"])
                for nome in ("aceitas", "recusas", "silencios", "correcoes")
            }
            if not any(pendentes.values()):
                return {
                    "status": "sem_novidade", "resultado": resultado_norm,
                    "amostras": amostras, "conexoes_ajustadas": 0,
                }
            ids = [
                int(row[0]) for row in conn.execute(
                    f"SELECT id FROM rede_associativa_nos WHERE chave IN ({','.join('?' for _ in chaves)})",
                    tuple(chaves),
                ).fetchall()
            ]
            if len(ids) < 2:
                return {
                    "status": "sem_conexoes", "resultado": resultado_norm,
                    "amostras": amostras, "conexoes_ajustadas": 0,
                }
            positivos = pendentes["aceitas"]
            negativos = pendentes["recusas"] + pendentes["correcoes"]
            silencios = pendentes["silencios"]
            delta_peso = 0.020 * positivos - 0.030 * pendentes["recusas"] - 0.050 * pendentes["correcoes"] - 0.005 * silencios
            delta_confianca = 0.010 * positivos - 0.015 * negativos - 0.002 * silencios
            placeholders = ",".join("?" for _ in ids)
            cursor = conn.execute(
                f"""
                UPDATE rede_associativa_conexoes
                SET peso=MIN(0.95, MAX(0.03, peso + ?)),
                    confianca=MIN(0.95, MAX(0.20, confianca + ?)),
                    contradicoes=contradicoes + ?,
                    atualizado_ts=?
                WHERE status='observando'
                  AND origem_id IN ({placeholders})
                  AND destino_id IN ({placeholders})
                """,
                (
                    delta_peso, delta_confianca, negativos, agora,
                    *ids, *ids,
                ),
            )
            conn.execute(
                """
                UPDATE rede_associativa_feedback SET
                    aplicadas_aceitas=aceitas,
                    aplicadas_recusas=recusas,
                    aplicadas_silencios=silencios,
                    aplicadas_correcoes=correcoes
                WHERE assinatura=?
                """,
                (assinatura,),
            )
        return {
            "status": "ajustado_sombra", "resultado": resultado_norm,
            "amostras": amostras, "conexoes_ajustadas": max(0, int(cursor.rowcount)),
            "delta_peso": round(delta_peso, 4),
        }

    @staticmethod
    def _normalizar_conceitos(conceitos: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        unicos: dict[str, dict[str, Any]] = {}
        for bruto in conceitos or ():
            item = dict(bruto or {})
            tipo = _codigo(item.get("tipo"), 32)
            rotulo = _texto_seguro(item.get("rotulo") or item.get("valor"))
            codigo = _codigo(rotulo)
            if tipo not in _TIPOS_VALIDOS or not codigo:
                continue
            chave = f"{tipo}:{codigo}"
            unicos[chave] = {
                "chave": chave,
                "tipo": tipo,
                "rotulo": rotulo,
                "confianca": _numero(item.get("confianca"), 0.55, 0.05, 1.0),
            }
            if len(unicos) >= 8:
                break
        return list(unicos.values())

    def registrar_contexto(
        self,
        conceitos: Iterable[Mapping[str, Any]],
        *,
        origem_evento: str,
        proveniencia: str = "observacao_estruturada",
    ) -> dict[str, Any]:
        itens = self._normalizar_conceitos(conceitos)
        if not itens:
            return {"nos": 0, "conexoes": 0, "ativados": []}
        agora = float(self.clock())
        origem = _codigo(origem_evento, 48) or "evento"
        procedencia = _codigo(proveniencia, 48) or "observacao_estruturada"
        ids: dict[str, int] = {}
        with self._conectar() as conn:
            for item in itens:
                conn.execute(
                    """
                    INSERT INTO rede_associativa_nos(
                        chave, tipo, rotulo, confianca, ativacao_base,
                        proveniencia, criado_ts, atualizado_ts, ultimo_uso_ts
                    ) VALUES (?, ?, ?, ?, 0.1, ?, ?, ?, ?)
                    ON CONFLICT(chave) DO UPDATE SET
                        rotulo=excluded.rotulo,
                        confianca=MAX(rede_associativa_nos.confianca, excluded.confianca),
                        atualizado_ts=excluded.atualizado_ts,
                        ultimo_uso_ts=excluded.ultimo_uso_ts
                    """,
                    (
                        item["chave"], item["tipo"], item["rotulo"],
                        item["confianca"], procedencia, agora, agora, agora,
                    ),
                )
                row = conn.execute(
                    "SELECT id FROM rede_associativa_nos WHERE chave = ?",
                    (item["chave"],),
                ).fetchone()
                if row:
                    ids[item["chave"]] = int(row["id"])

            conexoes = 0
            itens_por_chave = {item["chave"]: item for item in itens}
            for chave_esquerda, chave_direita in combinations(sorted(ids), 2):
                especificacao = self._relacao_entre(
                    itens_por_chave[chave_esquerda],
                    itens_por_chave[chave_direita],
                )
                if not especificacao:
                    continue
                esquerda, direita = sorted((ids[chave_esquerda], ids[chave_direita]))
                relacao, peso_inicial, confianca_inicial = especificacao
                conn.execute(
                    """
                    INSERT INTO rede_associativa_conexoes(
                        origem_id, destino_id, relacao, peso, confianca,
                        evidencias, contradicoes, proveniencia, status,
                        criado_ts, atualizado_ts
                    ) VALUES (?, ?, ?, ?, ?, 1, 0, ?, 'observando', ?, ?)
                    ON CONFLICT(origem_id, destino_id, relacao) DO UPDATE SET
                        peso=MIN(0.95, rede_associativa_conexoes.peso + 0.025),
                        confianca=MIN(0.95, rede_associativa_conexoes.confianca + 0.015),
                        evidencias=rede_associativa_conexoes.evidencias + 1,
                        atualizado_ts=excluded.atualizado_ts
                    """,
                    (
                        esquerda, direita, relacao, peso_inicial,
                        confianca_inicial, procedencia, agora, agora,
                    ),
                )
                conexoes += 1

            pesos_semente = {
                "intencao": 1.0, "alvo": 1.0, "dominio": 0.9,
                "topico": 0.85, "escopo": 0.7, "resultado": 0.65,
                "periodo": 0.3, "aplicativo": 0.3, "contexto": 0.3,
                "emocao": 0.25,
            }
            sementes = {
                ids[item["chave"]]: pesos_semente.get(item["tipo"], 0.4)
                for item in itens if item["chave"] in ids
            }
            ativacoes = self._espalhar_conn(conn, sementes, saltos=2, decaimento=0.55)
            contexto_json = json.dumps(
                {"chaves": sorted(ids)[:8]}, ensure_ascii=False, separators=(",", ":"),
            )
            for no_id, intensidade in ativacoes.items():
                conn.execute(
                    """
                    INSERT INTO rede_associativa_ativacoes(
                        no_id, intensidade, origem_evento, contexto_json, vezes, atualizado_ts
                    ) VALUES (?, ?, ?, ?, 1, ?)
                    ON CONFLICT(no_id) DO UPDATE SET
                        intensidade=MAX(
                            excluded.intensidade,
                            rede_associativa_ativacoes.intensidade * 0.65
                        ),
                        origem_evento=excluded.origem_evento,
                        contexto_json=excluded.contexto_json,
                        vezes=rede_associativa_ativacoes.vezes + 1,
                        atualizado_ts=excluded.atualizado_ts
                    """,
                    (no_id, intensidade, origem, contexto_json, agora),
                )
        return {
            "nos": len(ids),
            "conexoes": conexoes,
            "ativados": self.listar_ativados(limit=12),
        }

    @staticmethod
    def _relacao_entre(
        esquerda: Mapping[str, Any], direita: Mapping[str, Any],
    ) -> tuple[str, float, float] | None:
        """Cria somente vínculos com papel cognitivo explícito."""
        tipos = frozenset((str(esquerda.get("tipo")), str(direita.get("tipo"))))
        contextuais = {"periodo", "aplicativo", "contexto", "emocao"}
        nucleares = {"intencao", "alvo", "dominio", "escopo", "resultado", "topico"}
        if tipos == {"intencao", "alvo"}:
            return "refere_se_a", 0.16, 0.62
        if tipos == {"dominio", "intencao"}:
            return "pertence_ao_dominio", 0.14, 0.60
        if tipos == {"dominio", "alvo"}:
            return "envolve_alvo", 0.13, 0.58
        if tipos == {"intencao", "resultado"}:
            return "produziu_resultado", 0.18, 0.68
        if tipos == {"alvo", "resultado"}:
            return "resultado_do_alvo", 0.16, 0.64
        if tipos == {"dominio", "resultado"}:
            return "resultado_no_dominio", 0.14, 0.60
        if tipos == {"topico", "dominio"}:
            dominio = esquerda if esquerda.get("tipo") == "dominio" else direita
            # "conversa" é amplo demais e ligaria assuntos sem relação entre
            # si. Somente habilidades específicas podem organizar tópicos.
            if _codigo(dominio.get("rotulo"), 48) not in {
                "", "conversa", "conversacional", "pergunta", "explicacao",
            }:
                return "assunto_do_dominio", 0.12, 0.58
            return None
        if tipos == {"topico", "alvo"}:
            return "descreve_alvo", 0.12, 0.58
        if "escopo" in tipos and tipos & {"intencao", "alvo", "dominio"}:
            return "no_escopo", 0.10, 0.55
        if tipos & contextuais and tipos & nucleares:
            # Contexto serve como filtro, nunca como ponte de propagação.
            return "contextualiza", 0.06, 0.50
        return None

    @staticmethod
    def _espalhar_conn(
        conn: sqlite3.Connection,
        sementes: Mapping[int, float],
        *,
        saltos: int,
        decaimento: float,
        limite: int = 40,
    ) -> dict[int, float]:
        ativacoes = {
            int(no_id): _numero(valor, 0.0, 0.0, 1.0)
            for no_id, valor in sementes.items()
        }
        fronteira = dict(ativacoes)
        for passo in range(max(0, min(3, int(saltos)))):
            proxima: dict[int, float] = {}
            fator = float(decaimento) ** (passo + 1)
            for no_id, intensidade in sorted(
                fronteira.items(), key=lambda item: item[1], reverse=True,
            )[:limite]:
                rows = conn.execute(
                    """
                    SELECT origem_id, destino_id, peso, confianca
                    FROM rede_associativa_conexoes
                    WHERE status = 'observando' AND relacao != 'contextualiza'
                      AND (origem_id = ? OR destino_id = ?)
                    ORDER BY peso * confianca DESC LIMIT 24
                    """,
                    (no_id, no_id),
                ).fetchall()
                for row in rows:
                    vizinho = int(row["destino_id"] if row["origem_id"] == no_id else row["origem_id"])
                    propagada = intensidade * float(row["peso"]) * float(row["confianca"]) * fator
                    if propagada < 0.025:
                        continue
                    proxima[vizinho] = min(1.0, proxima.get(vizinho, 0.0) + propagada)
            for no_id, intensidade in proxima.items():
                ativacoes[no_id] = min(1.0, ativacoes.get(no_id, 0.0) + intensidade)
            fronteira = proxima
            if not fronteira:
                break
        return dict(sorted(ativacoes.items(), key=lambda item: item[1], reverse=True)[:limite])

    def simular_memoria_trabalho(
        self,
        conceitos: Iterable[Mapping[str, Any]],
        *,
        limit: int = 5,
        evidencias_minimas: int = 3,
    ) -> list[dict[str, Any]]:
        """Compara associações maduras sem entregá-las ao modelo de linguagem."""
        itens = self._normalizar_conceitos(conceitos)
        if not itens:
            return []
        chaves = [item["chave"] for item in itens]
        placeholders = ",".join("?" for _ in chaves)
        with self._conectar() as conn:
            rows = conn.execute(
                f"SELECT id, chave FROM rede_associativa_nos WHERE chave IN ({placeholders})",
                tuple(chaves),
            ).fetchall()
            sementes_ids = {int(row["id"]) for row in rows}
            if not sementes_ids:
                return []
            ativacoes = self._espalhar_conn(
                conn, {no_id: 1.0 for no_id in sementes_ids},
                saltos=2, decaimento=0.55,
            )
            candidatos = []
            for no_id, intensidade in ativacoes.items():
                if no_id in sementes_ids:
                    continue
                no = conn.execute(
                    "SELECT chave, tipo, rotulo, confianca FROM rede_associativa_nos WHERE id = ?",
                    (no_id,),
                ).fetchone()
                if not no or no["tipo"] not in {
                    "intencao", "alvo", "dominio", "escopo", "topico",
                }:
                    continue
                ligacoes = conn.execute(
                    f"""
                    SELECT MAX(evidencias) AS evidencias,
                           MAX(confianca) AS confianca,
                           MAX(contradicoes) AS contradicoes
                    FROM rede_associativa_conexoes
                    WHERE status = 'observando' AND relacao != 'contextualiza'
                      AND (
                        (origem_id = ? AND destino_id IN ({placeholders})) OR
                        (destino_id = ? AND origem_id IN ({placeholders}))
                      )
                    """,
                    (no_id, *sementes_ids, no_id, *sementes_ids),
                ).fetchone()
                evidencias = int((ligacoes or {})["evidencias"] or 0)
                if evidencias < max(2, int(evidencias_minimas)):
                    continue
                confianca_aresta = float((ligacoes or {})["confianca"] or 0.0)
                contradicoes = int((ligacoes or {})["contradicoes"] or 0)
                score = intensidade * confianca_aresta * min(1.0, evidencias / 6.0)
                candidatos.append({
                    "chave": no["chave"], "tipo": no["tipo"], "rotulo": no["rotulo"],
                    "score": round(score, 4), "evidencias": evidencias,
                    "confianca": round(min(float(no["confianca"]), confianca_aresta), 3),
                    "contradicoes": contradicoes,
                    "status": "candidato_sombra",
                })
        return sorted(candidatos, key=lambda item: item["score"], reverse=True)[: max(1, int(limit))]

    def listar_ativados(self, *, limit: int = 12, meia_vida_s: float = 1800.0) -> list[dict[str, Any]]:
        agora = float(self.clock())
        with self._conectar() as conn:
            rows = conn.execute(
                """
                SELECT n.chave, n.tipo, n.rotulo, n.confianca,
                       a.intensidade, a.origem_evento, a.atualizado_ts, a.vezes
                FROM rede_associativa_ativacoes a
                JOIN rede_associativa_nos n ON n.id = a.no_id
                ORDER BY a.intensidade DESC, a.atualizado_ts DESC LIMIT ?
                """,
                (max(1, min(50, int(limit) * 3)),),
            ).fetchall()
        saida = []
        for row in rows:
            idade = max(0.0, agora - float(row["atualizado_ts"]))
            intensidade = float(row["intensidade"]) * math.pow(0.5, idade / max(60.0, meia_vida_s))
            if intensidade < 0.02:
                continue
            saida.append({
                "chave": row["chave"], "tipo": row["tipo"], "rotulo": row["rotulo"],
                "intensidade": round(intensidade, 4),
                "confianca": round(float(row["confianca"]), 3),
                "origem_evento": row["origem_evento"], "vezes": int(row["vezes"]),
            })
        return sorted(saida, key=lambda item: item["intensidade"], reverse=True)[:limit]

    def consolidar(self, *, retencao_ativacao_dias: int = 7) -> dict[str, int]:
        agora = float(self.clock())
        corte_ativacao = agora - max(1, int(retencao_ativacao_dias)) * 86400
        corte_fraco = agora - 30 * 86400
        with self._conectar() as conn:
            ativacoes = conn.execute(
                "DELETE FROM rede_associativa_ativacoes WHERE atualizado_ts < ?",
                (corte_ativacao,),
            ).rowcount
            fracas = conn.execute(
                """
                DELETE FROM rede_associativa_conexoes
                WHERE atualizado_ts < ? AND evidencias <= 1 AND peso <= 0.10
                """,
                (corte_fraco,),
            ).rowcount
            conn.execute(
                """
                DELETE FROM rede_associativa_conexoes
                WHERE status = 'legado_sombra' AND atualizado_ts < ?
                """,
                (agora - 7 * 86400,),
            )
            total_conexoes = int(conn.execute(
                "SELECT COUNT(*) FROM rede_associativa_conexoes",
            ).fetchone()[0])
            excedente_conexoes = max(0, total_conexoes - self.max_conexoes)
            if excedente_conexoes:
                conn.execute(
                    """
                    DELETE FROM rede_associativa_conexoes WHERE id IN (
                        SELECT id FROM rede_associativa_conexoes
                        ORDER BY (peso * confianca) ASC, atualizado_ts ASC LIMIT ?
                    )
                    """,
                    (excedente_conexoes,),
                )
            total_nos = int(conn.execute(
                "SELECT COUNT(*) FROM rede_associativa_nos",
            ).fetchone()[0])
            excedente_nos = max(0, total_nos - self.max_nos)
            if excedente_nos:
                conn.execute(
                    """
                    DELETE FROM rede_associativa_nos WHERE id IN (
                        SELECT n.id FROM rede_associativa_nos n
                        LEFT JOIN rede_associativa_conexoes c
                          ON c.origem_id = n.id OR c.destino_id = n.id
                        WHERE c.id IS NULL
                        ORDER BY n.ultimo_uso_ts ASC LIMIT ?
                    )
                    """,
                    (excedente_nos,),
                )
        return {"ativacoes_expiradas": ativacoes, "conexoes_fracas": fracas}

    def diagnostico(self) -> dict[str, Any]:
        with self._conectar() as conn:
            nos = int(conn.execute("SELECT COUNT(*) FROM rede_associativa_nos").fetchone()[0])
            conexoes = int(conn.execute("SELECT COUNT(*) FROM rede_associativa_conexoes").fetchone()[0])
            ativacoes = int(conn.execute("SELECT COUNT(*) FROM rede_associativa_ativacoes").fetchone()[0])
            feedback = conn.execute(
                """
                SELECT COUNT(*) AS perfis,
                       COALESCE(SUM(aceitas + recusas + silencios + correcoes), 0) AS amostras,
                       COALESCE(SUM(aceitas), 0) AS aceitas,
                       COALESCE(SUM(recusas), 0) AS recusas,
                       COALESCE(SUM(silencios), 0) AS silencios,
                       COALESCE(SUM(correcoes), 0) AS correcoes
                FROM rede_associativa_feedback
                """
            ).fetchone()
        return {
            "nos": nos, "conexoes": conexoes, "ativacoes": ativacoes,
            "limite_nos": self.max_nos, "limite_conexoes": self.max_conexoes,
            "mais_ativos": self.listar_ativados(limit=8),
            "plasticidade": {
                "perfis": int(feedback["perfis"] or 0),
                "amostras": int(feedback["amostras"] or 0),
                "aceitas": int(feedback["aceitas"] or 0),
                "recusas": int(feedback["recusas"] or 0),
                "silencios": int(feedback["silencios"] or 0),
                "correcoes": int(feedback["correcoes"] or 0),
            },
        }


class RedeAssociativaRuntime:
    """Fila não bloqueante e isolada para observação associativa."""

    def __init__(
        self,
        *,
        db_path: str,
        contexto_getter: Callable[[], Mapping[str, Any]] = lambda: {},
        modo: str | None = None,
        log: Callable[[str], Any] = print,
        queue_max: int = 512,
        repositorio: RepositorioRedeAssociativa | None = None,
    ) -> None:
        modo_env = str(modo or os.getenv("LAYLAY_REDE_ASSOCIATIVA_MODO", "sombra")).strip().casefold()
        self.modo = modo_env if modo_env in MODOS_VALIDOS else "sombra"
        # A primeira influência real é restrita a priorizar contexto já
        # conhecido; ela nunca injeta rótulos, fatos ou ações no prompt.
        self.influencia_habilitada = self.modo in {"continuidade", "ativo"}
        self.contexto_getter = contexto_getter
        self.log = log
        self.repositorio = repositorio or RepositorioRedeAssociativa(db_path)
        self._fila: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=max(32, int(queue_max)))
        self._parar = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._metricas = {
            "recebidos": 0, "processados": 0, "descartados_fila": 0,
            "duplicados": 0, "falhas": 0, "comparacoes_sombra": 0,
            "candidatos_sombra": 0, "feedbacks": 0,
            "ajustes_plasticidade": 0,
            "sinais_continuidade": 0, "influencias_continuidade": 0,
        }
        self._eventos_recentes: dict[str, float] = {}
        self._ultima_comparacao: dict[str, Any] = {}
        self._cache_continuidade: dict[str, Any] = {}

    def iniciar(self) -> None:
        if self.modo == "desligado":
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._parar.clear()
            self._thread = threading.Thread(
                target=self._executar, name="Laylay-Rede-Associativa", daemon=True,
            )
            self._thread.start()
        influencia = "continuidade" if self.influencia_habilitada else "desativada"
        self.log(f"🧠 [REDE ASSOCIATIVA] modo={self.modo} | influência={influencia}")

    def encerrar(self, timeout_s: float = 1.5) -> None:
        self._parar.set()
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=max(0.0, float(timeout_s)))

    def _contexto(self) -> dict[str, Any]:
        try:
            recebido = self.contexto_getter() or {}
            return dict(recebido) if isinstance(recebido, Mapping) else {}
        except Exception:
            return {}

    def _enfileirar(self, evento: dict[str, Any]) -> bool:
        if self.modo == "desligado":
            return False
        with self._lock:
            self._metricas["recebidos"] += 1
            agora = time.monotonic()
            self._eventos_recentes = {
                chave: ts for chave, ts in self._eventos_recentes.items()
                if agora - ts <= 3.0
            }
            assinatura = self._assinatura_evento(evento)
            if assinatura and assinatura in self._eventos_recentes:
                self._metricas["duplicados"] += 1
                return False
            if assinatura:
                self._eventos_recentes[assinatura] = agora
        try:
            self._fila.put_nowait(dict(evento))
            return True
        except queue.Full:
            with self._lock:
                self._metricas["descartados_fila"] += 1
            return False

    @staticmethod
    def _assinatura_evento(evento: Mapping[str, Any]) -> str:
        partes = [
            f"evento:{_codigo(evento.get('tipo'), 24)}",
            f"resultado:{_codigo(evento.get('resultado'), 24)}",
        ]
        for item in evento.get("conceitos") or ():
            if not isinstance(item, Mapping):
                continue
            tipo = _codigo(item.get("tipo"), 24)
            rotulo = _codigo(item.get("rotulo") or item.get("valor"), 64)
            if tipo and rotulo:
                partes.append(f"{tipo}:{rotulo}")
        return "|".join(sorted(set(parte for parte in partes if not parte.endswith(":"))))

    @staticmethod
    def _conceitos_base(
        *,
        intencao: str = "",
        alvo: str = "",
        escopo: str = "",
        habilidade: str = "",
        contexto: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        ctx = dict(contexto or {})
        temporal = ctx.get("ritmo_temporal") if isinstance(ctx.get("ritmo_temporal"), Mapping) else {}
        intencao_codigo = _codigo(intencao, 48)
        habilidade_codigo = _codigo(habilidade, 48)
        conversa_sem_acao = (
            not intencao_codigo
            and habilidade_codigo in {
                "", "conversa", "conversacional", "pergunta", "explicacao",
            }
        )
        # O tópico vem da interpretação estruturada da mente única, nunca do
        # texto bruto. Em turnos operacionais ele é deliberadamente ignorado:
        # um assunto antigo não pode contaminar o comando atual.
        topico = (
            ctx.get("ultimo_topico_conversa") or ctx.get("topico_ativo")
            if conversa_sem_acao else ""
        )
        conceitos = [
            {"tipo": "intencao", "rotulo": intencao, "confianca": 0.8},
            {"tipo": "alvo", "rotulo": alvo, "confianca": 0.65},
            {"tipo": "escopo", "rotulo": escopo, "confianca": 0.7},
            {"tipo": "dominio", "rotulo": habilidade, "confianca": 0.75},
            {"tipo": "periodo", "rotulo": temporal.get("periodo") or ctx.get("periodo"), "confianca": 0.8},
            {"tipo": "aplicativo", "rotulo": ctx.get("exe") or ctx.get("aplicativo"), "confianca": 0.65},
            {"tipo": "contexto", "rotulo": "jogo" if ctx.get("modo_jogo") or ctx.get("modo_jogo_ativo") else "cotidiano", "confianca": 0.8},
            {"tipo": "topico", "rotulo": topico, "confianca": 0.72},
        ]
        return [item for item in conceitos if _texto_seguro(item.get("rotulo"))]

    def observar_interacao(
        self,
        *,
        intencao: str = "",
        alvo: str = "",
        escopo: str = "",
        habilidade: str = "",
    ) -> bool:
        # Sinais internos de infraestrutura não representam uma associação
        # cognitiva do usuário e poluiriam a memória de trabalho.
        if _codigo(intencao, 48) in {"fala_proativa", "abertura_inicial"}:
            return False
        # Deliberadamente não recebe nem persiste o texto bruto.
        conceitos = self._conceitos_base(
            intencao=intencao, alvo=alvo, escopo=escopo,
            habilidade=habilidade, contexto=self._contexto(),
        )
        return self._enfileirar({
            "tipo": "contexto", "conceitos": conceitos,
            "origem_evento": "interacao", "proveniencia": "turno_estruturado",
        })

    def observar_resultado(
        self,
        *,
        intencao: str,
        alvo: str = "",
        status: str = "",
        executou: bool | None = None,
        confirmado: bool | None = None,
    ) -> bool:
        resultado = (
            "sucesso_confirmado" if confirmado is True
            else "sucesso" if executou is True
            else "falha" if executou is False
            else status
        )
        conceitos = self._conceitos_base(
            intencao=intencao, alvo=alvo, habilidade="execucao",
            contexto=self._contexto(),
        )
        if _texto_seguro(resultado):
            conceitos.append({"tipo": "resultado", "rotulo": resultado, "confianca": 0.9})
        return self._enfileirar({
            "tipo": "contexto", "conceitos": conceitos,
            "origem_evento": "resultado_execucao",
            "proveniencia": "resultado_observado",
        })

    def observar_feedback(self, *, categoria: str, resultado: str) -> bool:
        """Enfileira apenas a leitura estruturada do feedback proativo."""
        resultado_norm = _codigo(resultado, 24)
        categoria_segura = _texto_seguro(categoria, 48)
        if resultado_norm not in _FEEDBACK_VALIDOS or not categoria_segura:
            return False
        conceitos = self._conceitos_base(
            intencao="SUGESTAO_PROATIVA",
            alvo=categoria_segura,
            habilidade="proatividade",
            contexto=self._contexto(),
        )
        return self._enfileirar({
            "tipo": "feedback", "conceitos": conceitos,
            "resultado": resultado_norm,
            "origem_evento": "feedback_proatividade",
            "proveniencia": "feedback_estruturado",
        })

    def _processar(self, evento: Mapping[str, Any]) -> None:
        if evento.get("tipo") == "feedback":
            ajuste = self.repositorio.registrar_feedback(
                evento.get("conceitos") or (),
                resultado=str(evento.get("resultado") or ""),
            )
            with self._lock:
                self._metricas["feedbacks"] += 1
                if ajuste.get("status") == "ajustado_sombra":
                    self._metricas["ajustes_plasticidade"] += 1
            return
        if evento.get("tipo") != "contexto":
            return
        conceitos = evento.get("conceitos") or ()
        self.repositorio.registrar_contexto(
            conceitos,
            origem_evento=str(evento.get("origem_evento") or "evento"),
            proveniencia=str(evento.get("proveniencia") or "observacao_estruturada"),
        )
        candidatos = self.repositorio.simular_memoria_trabalho(conceitos)
        conceitos_lista = [dict(item) for item in conceitos if isinstance(item, Mapping)]
        operacional = any(
            str(item.get("tipo") or "") == "intencao"
            and bool(_codigo(item.get("rotulo"), 48))
            for item in conceitos_lista
        )
        maduros = [
            dict(item) for item in candidatos
            if str(item.get("tipo") or "") in {"topico", "alvo"}
            and int(item.get("evidencias") or 0) >= 5
            and float(item.get("confianca") or 0.0) >= 0.65
            and float(item.get("score") or 0.0) >= 0.05
            and int(item.get("contradicoes") or 0) == 0
        ][:3]
        tipos: dict[str, int] = {}
        for item in candidatos:
            tipo = str(item.get("tipo") or "outro")
            tipos[tipo] = tipos.get(tipo, 0) + 1
        with self._lock:
            self._metricas["comparacoes_sombra"] += 1
            self._metricas["candidatos_sombra"] += len(candidatos)
            # Diagnóstico guarda apenas contagem e tipos, nunca rótulos.
            self._ultima_comparacao = {
                "quantidade": len(candidatos), "tipos": tipos,
                "maior_score": max(
                    (float(item.get("score") or 0.0) for item in candidatos),
                    default=0.0,
                ),
            }
            # Um comando sempre invalida a pista conversacional anterior.
            self._cache_continuidade = (
                {} if operacional or not maduros else {
                    "ts": time.time(),
                    "itens": maduros,
                    "origem": str(evento.get("origem_evento") or ""),
                }
            )

    def sinais_continuidade(self, *, validade_s: float = 180.0) -> list[dict[str, Any]]:
        """Retorna pistas maduras somente para desempatar contexto já existente."""
        if not self.influencia_habilitada:
            return []
        with self._lock:
            cache = dict(self._cache_continuidade)
        try:
            idade = max(0.0, time.time() - float(cache.get("ts") or 0.0))
        except (TypeError, ValueError):
            return []
        if not cache or idade > max(15.0, min(300.0, float(validade_s))):
            return []
        saida = []
        for item in list(cache.get("itens") or [])[:3]:
            if not isinstance(item, Mapping):
                continue
            rotulo = _texto_seguro(item.get("rotulo"), 96)
            if not rotulo:
                continue
            saida.append({
                "tipo": str(item.get("tipo") or ""),
                "rotulo": rotulo,
                "score": float(item.get("score") or 0.0),
                "evidencias": int(item.get("evidencias") or 0),
                "confianca": float(item.get("confianca") or 0.0),
            })
        if saida:
            with self._lock:
                self._metricas["sinais_continuidade"] += 1
        return saida

    def registrar_influencia_continuidade(self) -> None:
        if self.influencia_habilitada:
            with self._lock:
                self._metricas["influencias_continuidade"] += 1

    def processar_pendentes(self, limite: int = 100) -> int:
        processados = 0
        while processados < max(1, int(limite)):
            try:
                evento = self._fila.get_nowait()
            except queue.Empty:
                break
            try:
                self._processar(evento)
                with self._lock:
                    self._metricas["processados"] += 1
            except Exception as erro:
                with self._lock:
                    self._metricas["falhas"] += 1
                self.log(f"⚠️ [REDE ASSOCIATIVA] evento isolado após falha: {type(erro).__name__}")
            finally:
                self._fila.task_done()
            processados += 1
        return processados

    def _executar(self) -> None:
        desde_consolidacao = 0
        while not self._parar.is_set():
            try:
                evento = self._fila.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._processar(evento)
                desde_consolidacao += 1
                with self._lock:
                    self._metricas["processados"] += 1
                if desde_consolidacao >= 100:
                    self.repositorio.consolidar()
                    desde_consolidacao = 0
            except Exception as erro:
                with self._lock:
                    self._metricas["falhas"] += 1
                self.log(f"⚠️ [REDE ASSOCIATIVA] evento isolado após falha: {type(erro).__name__}")
            finally:
                self._fila.task_done()

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            metricas = dict(self._metricas)
        return {
            "modo": self.modo,
            "influencia_habilitada": self.influencia_habilitada,
            "fila": self._fila.qsize(),
            "metricas": metricas,
            "ultima_comparacao_sombra": dict(self._ultima_comparacao),
            **self.repositorio.diagnostico(),
        }


def criar_rede_associativa_runtime(**kwargs: Any) -> RedeAssociativaRuntime:
    return RedeAssociativaRuntime(**kwargs)
