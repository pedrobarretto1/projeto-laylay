"""Memória persistente, estruturada e isolada por jogo.

Capturas nunca são gravadas. Somente identidade, perfil informado por Pedro e
resumos textuais das dúvidas/análises entram no SQLite da memória principal.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from typing import Any, Mapping


class MemoriaJogos:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(db_path)
        self._lock = threading.RLock()
        self._inicializar()

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.execute("PRAGMA busy_timeout = 15000")
        return conn

    def _inicializar(self) -> None:
        with self._lock, self._conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jogos_contexto (
                    chave TEXT PRIMARY KEY,
                    nome TEXT NOT NULL DEFAULT '',
                    titulo TEXT NOT NULL DEFAULT '',
                    processo TEXT NOT NULL DEFAULT '',
                    perfil_json TEXT NOT NULL DEFAULT '{}',
                    atualizado_em TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jogos_memorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jogo_chave TEXT NOT NULL,
                    tipo TEXT NOT NULL DEFAULT 'duvida',
                    pergunta TEXT NOT NULL DEFAULT '',
                    observacao TEXT NOT NULL DEFAULT '',
                    perfil_json TEXT NOT NULL DEFAULT '{}',
                    criado_em TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jogos_memorias_chave "
                "ON jogos_memorias(jogo_chave, id DESC)"
            )
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jogos_inventarios (
                    jogo_chave TEXT NOT NULL,
                    personagem TEXT NOT NULL DEFAULT 'padrao',
                    esquema_json TEXT NOT NULL DEFAULT '{}',
                    equipados_json TEXT NOT NULL DEFAULT '{}',
                    confianca REAL NOT NULL DEFAULT 0,
                    ambiguidades_json TEXT NOT NULL DEFAULT '[]',
                    atualizado_em TEXT NOT NULL,
                    PRIMARY KEY(jogo_chave, personagem)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jogos_itens_vistos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jogo_chave TEXT NOT NULL,
                    personagem TEXT NOT NULL DEFAULT 'padrao',
                    slot TEXT NOT NULL DEFAULT '',
                    estado TEXT NOT NULL DEFAULT 'desconhecido',
                    item_json TEXT NOT NULL DEFAULT '{}',
                    criado_em TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jogos_itens_slot "
                "ON jogos_itens_vistos(jogo_chave, personagem, slot, id DESC)"
            )

    @staticmethod
    def _chave(identidade: Mapping[str, Any]) -> str:
        return str(identidade.get("chave") or "").strip()

    def carregar_perfil(self, identidade: Mapping[str, Any]) -> dict[str, Any]:
        chave = self._chave(identidade)
        if not chave:
            return {}
        with self._lock, self._conectar() as conn:
            row = conn.execute(
                "SELECT perfil_json FROM jogos_contexto WHERE chave = ?", (chave,)
            ).fetchone()
        if not row:
            return {}
        try:
            valor = json.loads(row[0])
            return dict(valor) if isinstance(valor, dict) else {}
        except Exception:
            return {}

    def salvar_perfil(
        self, identidade: Mapping[str, Any], perfil: Mapping[str, Any]
    ) -> None:
        chave = self._chave(identidade)
        if not chave:
            return
        agora = datetime.now().isoformat(" ")
        payload = json.dumps(dict(perfil or {}), ensure_ascii=False)
        with self._lock, self._conectar() as conn:
            conn.execute("""
                INSERT INTO jogos_contexto(
                    chave, nome, titulo, processo, perfil_json, atualizado_em
                ) VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(chave) DO UPDATE SET
                    nome=excluded.nome, titulo=excluded.titulo,
                    processo=excluded.processo, perfil_json=excluded.perfil_json,
                    atualizado_em=excluded.atualizado_em
            """, (
                chave, str(identidade.get("nome_candidato") or ""),
                str(identidade.get("titulo") or ""),
                str(identidade.get("processo") or ""), payload, agora,
            ))

    def registrar_observacao(
        self,
        identidade: Mapping[str, Any],
        *,
        tipo: str,
        pergunta: str,
        observacao: str,
        perfil: Mapping[str, Any] | None = None,
    ) -> None:
        chave = self._chave(identidade)
        if not chave or not str(observacao or "").strip():
            return
        self.salvar_perfil(identidade, perfil or {})
        with self._lock, self._conectar() as conn:
            cursor = conn.execute("""
                INSERT INTO jogos_memorias(
                    jogo_chave, tipo, pergunta, observacao, perfil_json, criado_em
                ) VALUES(?, ?, ?, ?, ?, ?)
            """, (
                chave, str(tipo or "duvida")[:60], str(pergunta or "")[:500],
                str(observacao or "")[:1200],
                json.dumps(dict(perfil or {}), ensure_ascii=False),
                datetime.now().isoformat(" "),
            ))
            ultimo_id = int(cursor.lastrowid or 0)
            if ultimo_id:
                conn.execute("""
                    DELETE FROM jogos_memorias
                    WHERE jogo_chave = ? AND id NOT IN (
                        SELECT id FROM jogos_memorias WHERE jogo_chave = ?
                        ORDER BY id DESC LIMIT 200
                    )
                """, (chave, chave))

    def listar_recentes(
        self, identidade: Mapping[str, Any], limite: int = 6
    ) -> list[dict[str, Any]]:
        chave = self._chave(identidade)
        if not chave:
            return []
        with self._lock, self._conectar() as conn:
            rows = conn.execute("""
                SELECT tipo, pergunta, observacao, criado_em
                FROM jogos_memorias WHERE jogo_chave = ?
                ORDER BY id DESC LIMIT ?
            """, (chave, max(1, min(20, int(limite))))).fetchall()
        return [
            {"tipo": r[0], "pergunta": r[1], "observacao": r[2], "criado_em": r[3]}
            for r in rows
        ]

    def resumo_para_prompt(
        self,
        identidade: Mapping[str, Any],
        limite: int = 4,
        *,
        incluir_observacoes: bool = True,
    ) -> str:
        perfil = self.carregar_perfil(identidade)
        recentes = (
            self.listar_recentes(identidade, limite=limite)
            if incluir_observacoes else []
        )
        partes = []
        if perfil:
            partes.append("perfil informado pelo usuário: " + ", ".join(
                f"{chave}={valor}" for chave, valor in perfil.items()
            ))
        inventario = self.carregar_inventario(identidade)
        if inventario:
            equipados = dict(inventario.get("equipados") or {})
            resumo_equipados = []
            for slot, itens in list(equipados.items())[:20]:
                nomes = []
                for item in list(itens or [])[:4]:
                    if not isinstance(item, dict):
                        continue
                    nome = str(item.get("nome") or "item sem nome")
                    atributos = [str(valor) for valor in list(item.get("atributos") or [])[:8]]
                    nomes.append(
                        nome + (" [" + "; ".join(atributos) + "]" if atributos else "")
                    )
                if nomes:
                    resumo_equipados.append(f"{slot}=" + "/".join(nomes))
            partes.append(
                "mapa de equipamento observado: slots="
                + ",".join(list(dict(inventario.get("esquema") or {}))[:30])
                + ("; equipados=" + ", ".join(resumo_equipados) if resumo_equipados else "")
            )
        for item in reversed(recentes):
            partes.append(
                f"em {item['criado_em']}: pergunta={item['pergunta']}; "
                f"observação visual anterior={item['observacao']}"
            )
        if not partes:
            return ""
        return (
            "Memória deste jogo (pode estar desatualizada; use como contexto, "
            "não como prova do que está visível agora): " + " | ".join(partes)
        )[:3500]

    def salvar_inventario(
        self, identidade: Mapping[str, Any], inventario: Mapping[str, Any]
    ) -> None:
        chave = self._chave(identidade)
        dados = dict(inventario or {})
        personagem = str(dados.get("personagem") or "padrao").strip()[:100]
        if not chave:
            return
        with self._lock, self._conectar() as conn:
            conn.execute("""
                INSERT INTO jogos_inventarios(
                    jogo_chave, personagem, esquema_json, equipados_json,
                    confianca, ambiguidades_json, atualizado_em
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(jogo_chave, personagem) DO UPDATE SET
                    esquema_json=excluded.esquema_json,
                    equipados_json=excluded.equipados_json,
                    confianca=excluded.confianca,
                    ambiguidades_json=excluded.ambiguidades_json,
                    atualizado_em=excluded.atualizado_em
            """, (
                chave, personagem,
                json.dumps(dict(dados.get("esquema") or {}), ensure_ascii=False),
                json.dumps(dict(dados.get("equipados") or {}), ensure_ascii=False),
                float(dados.get("confianca") or 0.0),
                json.dumps(list(dados.get("ambiguidades") or []), ensure_ascii=False),
                datetime.now().isoformat(" "),
            ))

    def carregar_inventario(
        self, identidade: Mapping[str, Any], personagem: str = ""
    ) -> dict[str, Any]:
        chave = self._chave(identidade)
        if not chave:
            return {}
        query = (
            "SELECT personagem, esquema_json, equipados_json, confianca, "
            "ambiguidades_json, atualizado_em FROM jogos_inventarios "
            "WHERE jogo_chave = ?"
        )
        args: tuple[Any, ...] = (chave,)
        if personagem:
            query += " AND personagem = ?"
            args = (chave, str(personagem)[:100])
        query += " ORDER BY atualizado_em DESC LIMIT 1"
        with self._lock, self._conectar() as conn:
            row = conn.execute(query, args).fetchone()
        if not row:
            return {}
        try:
            return {
                "personagem": row[0], "esquema": json.loads(row[1]),
                "equipados": json.loads(row[2]), "confianca": float(row[3]),
                "ambiguidades": json.loads(row[4]), "atualizado_em": row[5],
            }
        except Exception:
            return {}

    def registrar_item_visual(
        self,
        identidade: Mapping[str, Any],
        item: Mapping[str, Any],
        *,
        personagem: str = "padrao",
    ) -> None:
        chave = self._chave(identidade)
        dados = dict(item or {})
        if not chave or not dados.get("nome"):
            return
        slot = str(dados.get("slot") or dados.get("categoria") or "").strip()[:60]
        estado = str(dados.get("estado") or "desconhecido").strip()[:40]
        with self._lock, self._conectar() as conn:
            cursor = conn.execute("""
                INSERT INTO jogos_itens_vistos(
                    jogo_chave, personagem, slot, estado, item_json, criado_em
                ) VALUES(?, ?, ?, ?, ?, ?)
            """, (
                chave, str(personagem or "padrao")[:100], slot, estado,
                json.dumps(dados, ensure_ascii=False), datetime.now().isoformat(" "),
            ))
            if cursor.lastrowid:
                conn.execute("""
                    DELETE FROM jogos_itens_vistos
                    WHERE jogo_chave = ? AND id NOT IN (
                        SELECT id FROM jogos_itens_vistos WHERE jogo_chave = ?
                        ORDER BY id DESC LIMIT 300
                    )
                """, (chave, chave))
        if dados.get("equipado") or estado.casefold() in {"equipado", "atual", "em_uso"}:
            self.definir_item_equipado(identidade, dados, personagem=personagem)

    def definir_item_equipado(
        self,
        identidade: Mapping[str, Any],
        item: Mapping[str, Any],
        *,
        personagem: str = "padrao",
    ) -> bool:
        dados = dict(item or {})
        slot = str(dados.get("slot") or dados.get("categoria") or "").strip()
        if not self._chave(identidade) or not slot or not dados.get("nome"):
            return False
        inventario = self.carregar_inventario(identidade, personagem) or {
            "personagem": personagem, "esquema": {}, "equipados": {},
            "confianca": float(dados.get("confianca") or 0.0), "ambiguidades": [],
        }
        equipados = dict(inventario.get("equipados") or {})
        item_equipado = {**dados, "estado": "equipado", "equipado": True}
        equipados[slot] = [item_equipado]
        inventario["equipados"] = equipados
        esquema = dict(inventario.get("esquema") or {})
        esquema.setdefault(slot, {
            "nome": slot.replace("_", " "), "categoria": str(dados.get("categoria") or ""),
            "quantidade": 1, "confianca": float(dados.get("confianca") or 0.0),
        })
        inventario["esquema"] = esquema
        self.salvar_inventario(identidade, inventario)
        return True

    def itens_recentes(
        self, identidade: Mapping[str, Any], *, slot: str = "", limite: int = 5
    ) -> list[dict[str, Any]]:
        chave = self._chave(identidade)
        if not chave:
            return []
        query = "SELECT item_json FROM jogos_itens_vistos WHERE jogo_chave = ?"
        args: list[Any] = [chave]
        if slot:
            query += " AND slot = ?"
            args.append(str(slot)[:60])
        query += " ORDER BY id DESC LIMIT ?"
        args.append(max(1, min(20, int(limite))))
        with self._lock, self._conectar() as conn:
            rows = conn.execute(query, tuple(args)).fetchall()
        saida = []
        for row in rows:
            try:
                item = json.loads(row[0])
            except Exception:
                continue
            if isinstance(item, dict):
                saida.append(item)
        return saida
