"""Lixeira reversivel e confirmacao de exclusoes da Laylay.

O estado deste modulo e operacional, nao uma segunda memoria conversacional.
Ele mantem somente o item fisico movido, um indice duravel e uma confirmacao
curta para qualquer exclusao solicitada.
"""

from __future__ import annotations

import json
import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResultadoLixeira:
    status: str
    sucesso: bool
    caminho: str = ""
    destino: str = ""
    requer_confirmacao: bool = False


class LixeiraLaylay:
    def __init__(self, raiz: str | None = None) -> None:
        base = Path(raiz or os.getenv("LAYLAY_LIXEIRA_DIR") or (Path.home() / ".laylay" / "lixeira"))
        self.raiz = base.resolve()
        self.itens = self.raiz / "itens"
        self.indice = self.raiz / "indice.json"
        self._lock = threading.RLock()
        self._pendente: dict[str, Any] = {}

    def _carregar(self) -> list[dict[str, Any]]:
        try:
            dados = json.loads(self.indice.read_text(encoding="utf-8"))
            return [dict(item) for item in dados if isinstance(item, dict)] if isinstance(dados, list) else []
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return []

    def _salvar(self, itens: list[dict[str, Any]]) -> None:
        self.raiz.mkdir(parents=True, exist_ok=True)
        temporario = self.indice.with_suffix(f".{uuid.uuid4().hex}.tmp")
        temporario.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporario, self.indice)

    def tem_confirmacao_pendente(self) -> bool:
        with self._lock:
            return bool(self._pendente and time.time() < float(self._pendente.get("expira_em") or 0))

    def cancelar_pendente(self) -> None:
        with self._lock:
            self._pendente = {}

    def mover(self, caminho: str, *, confirmado: bool = False) -> ResultadoLixeira:
        origem = Path(caminho).expanduser().resolve()
        if not origem.exists():
            return ResultadoLixeira("nao_encontrado", False, str(origem))

        with self._lock:
            if not confirmado:
                self._pendente = {"caminho": str(origem), "expira_em": time.time() + 90.0}
                return ResultadoLixeira(
                    "aguardando_confirmacao", False, str(origem), requer_confirmacao=True
                )

            identificador = f"{int(time.time())}_{uuid.uuid4().hex}"
            destino = self.itens / identificador / origem.name
            destino.parent.mkdir(parents=True, exist_ok=False)
            try:
                shutil.move(str(origem), str(destino))
            except OSError:
                shutil.rmtree(destino.parent, ignore_errors=True)
                return ResultadoLixeira("falha_mover", False, str(origem))

            registros = self._carregar()
            registros.append({
                "id": identificador,
                "origem": str(origem),
                "destino": str(destino),
                "nome": origem.name,
                "apagado_em": time.time(),
                "restaurado_em": None,
            })
            self._salvar(registros)
            self._pendente = {}
            return ResultadoLixeira("movido_para_lixeira", True, str(origem), str(destino))

    def confirmar_pendente(self) -> ResultadoLixeira:
        with self._lock:
            if not self.tem_confirmacao_pendente():
                self._pendente = {}
                return ResultadoLixeira("sem_confirmacao_pendente", False)
            caminho = str(self._pendente.get("caminho") or "")
        return self.mover(caminho, confirmado=True)

    def restaurar_ultimo(self) -> ResultadoLixeira:
        with self._lock:
            registros = self._carregar()
            item = next(
                (registro for registro in reversed(registros) if not registro.get("restaurado_em")),
                None,
            )
            if not item:
                return ResultadoLixeira("lixeira_vazia", False)
            origem = Path(str(item.get("origem") or "")).expanduser()
            atual = Path(str(item.get("destino") or "")).expanduser()
            if not atual.exists():
                return ResultadoLixeira("item_da_lixeira_ausente", False, str(origem), str(atual))
            if origem.exists():
                return ResultadoLixeira("destino_ja_existe", False, str(origem), str(atual))
            origem.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(atual), str(origem))
            except OSError:
                return ResultadoLixeira("falha_restaurar", False, str(origem), str(atual))
            item["restaurado_em"] = time.time()
            self._salvar(registros)
            shutil.rmtree(atual.parent, ignore_errors=True)
            return ResultadoLixeira("restaurado", True, str(origem), str(atual))


_RUNTIME = LixeiraLaylay()


def mover_para_lixeira(caminho: str, *, confirmado: bool = False) -> ResultadoLixeira:
    return _RUNTIME.mover(caminho, confirmado=confirmado)


def confirmar_exclusao_pendente() -> ResultadoLixeira:
    return _RUNTIME.confirmar_pendente()


def cancelar_exclusao_pendente() -> None:
    _RUNTIME.cancelar_pendente()


def existe_exclusao_pendente() -> bool:
    return _RUNTIME.tem_confirmacao_pendente()


def restaurar_ultimo_item() -> ResultadoLixeira:
    return _RUNTIME.restaurar_ultimo()
