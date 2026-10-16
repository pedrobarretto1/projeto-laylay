"""Rascunhos pedidos pelo usuário; não são memória factual aprendida."""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping, Iterator


class RascunhosEmailRuntime:
    def __init__(self, arquivo: str) -> None:
        self.arquivo = arquivo

    @contextmanager
    def _conexao(self) -> Iterator[sqlite3.Connection]:
        Path(self.arquivo).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.arquivo, timeout=10)
        conn.execute("CREATE TABLE IF NOT EXISTS rascunhos (id TEXT PRIMARY KEY, conta TEXT NOT NULL, "
                     "versao INTEGER NOT NULL, estado TEXT NOT NULL, dados TEXT NOT NULL, ts REAL NOT NULL)")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def salvar(self, conta: str, dados: Mapping[str, Any], *, identificador: str = "", versao: int = 0) -> dict:
        identificador = identificador or uuid.uuid4().hex[:12]
        with self._conexao() as conn:
            if versao:
                cursor = conn.execute("UPDATE rascunhos SET dados=?, versao=versao+1, ts=? "
                    "WHERE id=? AND conta=? AND versao=? AND estado='rascunho'",
                    (json.dumps(dict(dados), ensure_ascii=False), time.time(), identificador, conta, versao))
                if cursor.rowcount != 1:
                    raise ValueError("rascunho_alterado_ou_indisponivel")
            else:
                conn.execute("INSERT INTO rascunhos VALUES (?, ?, 1, 'rascunho', ?, ?)",
                    (identificador, conta, json.dumps(dict(dados), ensure_ascii=False), time.time()))
        return self.obter(conta, identificador)

    def obter(self, conta: str, identificador: str) -> dict[str, Any]:
        with self._conexao() as conn:
            linha = conn.execute("SELECT id,versao,estado,dados FROM rascunhos WHERE conta=? AND id=?",
                                 (conta, identificador)).fetchone()
        if not linha:
            raise ValueError("rascunho_nao_encontrado")
        return {**json.loads(linha[3]), "id": linha[0], "versao": linha[1], "estado": linha[2],
                "identidade_conta": conta}

    def listar(self, conta: str) -> list[dict]:
        with self._conexao() as conn:
            linhas = conn.execute("SELECT id FROM rascunhos WHERE conta=? AND estado!='enviado' ORDER BY ts DESC LIMIT 50",
                                 (conta,)).fetchall()
        return [self.obter(conta, linha[0]) for linha in linhas]

    def transicionar(self, conta: str, identificador: str, versao: int, anterior: str, novo: str) -> bool:
        with self._conexao() as conn:
            cursor = conn.execute("UPDATE rascunhos SET estado=?,ts=? WHERE conta=? AND id=? AND versao=? AND estado=?",
                                 (novo, time.time(), conta, identificador, versao, anterior))
            return cursor.rowcount == 1

    def descartar(self, conta: str, identificador: str, versao: int) -> bool:
        with self._conexao() as conn:
            cursor = conn.execute("DELETE FROM rascunhos WHERE conta=? AND id=? AND versao=? AND estado='rascunho'",
                                 (conta, identificador, versao))
            return cursor.rowcount == 1
