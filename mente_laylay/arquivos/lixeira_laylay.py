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
from typing import Any, Callable


@dataclass(frozen=True)
class ResultadoLixeira:
    status: str
    sucesso: bool
    caminho: str = ""
    destino: str = ""
    requer_confirmacao: bool = False


class LixeiraLaylay:
    def __init__(
        self,
        raiz: str | None = None,
        *,
        pendencia_runtime: Any = None,
        agora: Callable[[], float] = time.time,
    ) -> None:
        base = Path(raiz or os.getenv("LAYLAY_LIXEIRA_DIR") or (Path.home() / ".laylay" / "lixeira"))
        self.raiz = base.resolve()
        self.itens = self.raiz / "itens"
        self.indice = self.raiz / "indice.json"
        self._lock = threading.RLock()
        self._pendencia_runtime = pendencia_runtime
        self._agora = agora

    def configurar_pendencia_runtime(self, pendencia_runtime: Any) -> None:
        self._pendencia_runtime = pendencia_runtime

    def _pendencia(self) -> dict[str, Any]:
        obter = getattr(self._pendencia_runtime, "obter", None)
        if not callable(obter):
            return {}
        atual = obter()
        if not isinstance(atual, dict):
            return {}
        if str(atual.get("origem") or "") != "lixeira_laylay":
            return {}
        if str(atual.get("acao") or "") != "confirmar_exclusao":
            return {}
        return dict(atual)

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
            return bool(self._pendencia())

    def cancelar_pendente(self) -> None:
        with self._lock:
            pendencia = self._pendencia()
            concluir = getattr(self._pendencia_runtime, "concluir", None)
            if pendencia and callable(concluir):
                concluir(str(pendencia.get("id") or ""), "cancelada")

    def mover(self, caminho: str, *, confirmado: bool = False) -> ResultadoLixeira:
        origem = Path(caminho).expanduser().resolve()
        if not origem.exists():
            return ResultadoLixeira("nao_encontrado", False, str(origem))

        with self._lock:
            if not confirmado:
                registrar = getattr(self._pendencia_runtime, "registrar", None)
                nova = registrar(
                    origem="lixeira_laylay",
                    acao="confirmar_exclusao",
                    pergunta=f"Enviar {origem.name} para a lixeira?",
                    referencia=str(origem)[:160],
                    metadados={"caminho": str(origem)[:500], "intent": "CONFIRM_DELETE_ITEM"},
                    ttl_s=90.0,
                ) if callable(registrar) else None
                if not nova:
                    return ResultadoLixeira("confirmacao_indisponivel", False, str(origem))
                return ResultadoLixeira(
                    "aguardando_confirmacao", False, str(origem), requer_confirmacao=True
                )

            identificador = f"{int(self._agora())}_{uuid.uuid4().hex}"
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
                "apagado_em": self._agora(),
                "restaurado_em": None,
            })
            self._salvar(registros)
            return ResultadoLixeira("movido_para_lixeira", True, str(origem), str(destino))

    def confirmar_pendente(self) -> ResultadoLixeira:
        with self._lock:
            pendencia = self._pendencia()
            if not pendencia:
                return ResultadoLixeira("sem_confirmacao_pendente", False)
            resolver = getattr(self._pendencia_runtime, "resolver", None)
            concluir = getattr(self._pendencia_runtime, "concluir", None)
            if not (callable(resolver) and callable(concluir)):
                return ResultadoLixeira("confirmacao_indisponivel", False)
            resolucao = resolver("sim")
            if resolucao.get("status") not in {"aceitar", "em_processamento"}:
                return ResultadoLixeira("confirmacao_concorrente", False)
            metadados = dict(pendencia.get("metadados") or {})
            caminho = str(metadados.get("caminho") or pendencia.get("referencia") or "")
        resultado = self.mover(caminho, confirmado=True)
        concluir(
            str(pendencia.get("id") or ""),
            "concluida" if resultado.sucesso else "falha_execucao",
        )
        return resultado

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
            item["restaurado_em"] = self._agora()
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


def configurar_pendencia_exclusao(pendencia_runtime: Any) -> None:
    _RUNTIME.configurar_pendencia_runtime(pendencia_runtime)
