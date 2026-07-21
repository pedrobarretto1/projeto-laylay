"""Métricas e eventos técnicos sanitizados para o diagnóstico da mente."""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Callable, Dict, Iterable


def _codigo(valor: Any, padrao: str = "sem_detalhe", limite: int = 96) -> str:
    texto = str(valor or "").strip().casefold()
    texto = re.sub(r"https?://\S+|[a-z]:\\\S+|[/\\][^\s]+", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[^a-z0-9áàâãéêíóôõúç_.: -]+", "", texto)
    texto = re.sub(r"\s+", "_", texto).strip("_.:-")
    return (texto or padrao)[:limite]


class ObservabilidadeMenteRuntime:
    """Atualiza somente telemetria técnica curta no domínio mental."""

    def __init__(
        self,
        *,
        estado_getter: Callable[[str, Any], Any],
        estado_setter: Callable[..., Any],
        clock: Callable[[], float] = time.time,
        limite_eventos: int = 20,
    ) -> None:
        self.estado_getter = estado_getter
        self.estado_setter = estado_setter
        self.clock = clock
        self.limite_eventos = max(5, int(limite_eventos))
        self._lock = threading.RLock()

    def _obter(self, chave: str, padrao: Any) -> Any:
        try:
            return self.estado_getter(chave, padrao)
        except Exception:
            return padrao

    def _atualizar(self, **campos: Any) -> None:
        try:
            self.estado_setter(**campos)
        except Exception:
            pass

    def registrar_metrica(self, componente: str, duracao_ms: float, sucesso: bool = True) -> Dict[str, Any]:
        nome = _codigo(componente, "desconhecido", 64)
        try:
            duracao = max(0.0, min(float(duracao_ms), 600000.0))
        except (TypeError, ValueError):
            duracao = 0.0
        with self._lock:
            metricas = dict(self._obter("diagnostico_metricas", {}) or {})
            atual = dict(metricas.get(nome) or {})
            amostras = int(atual.get("amostras") or 0) + 1
            media_anterior = float(atual.get("media_ms") or 0.0)
            atual.update(
                ultimo_ms=round(duracao, 2),
                media_ms=round(media_anterior + (duracao - media_anterior) / amostras, 2),
                max_ms=round(max(float(atual.get("max_ms") or 0.0), duracao), 2),
                amostras=amostras,
                falhas=int(atual.get("falhas") or 0) + (0 if sucesso else 1),
                ts=float(self.clock()),
            )
            metricas[nome] = atual
            self._atualizar(diagnostico_metricas=metricas)
            return dict(atual)

    def registrar_falha(
        self,
        componente: str,
        codigo: str,
        *,
        erro: BaseException | type[BaseException] | None = None,
    ) -> Dict[str, Any]:
        tipo = ""
        if isinstance(erro, BaseException):
            tipo = type(erro).__name__
        elif isinstance(erro, type) and issubclass(erro, BaseException):
            tipo = erro.__name__
        evento = {
            "componente": _codigo(componente, "desconhecido", 64),
            "codigo": _codigo(codigo, "falha", 80),
            "tipo": _codigo(tipo, "", 48) if tipo else "",
            "ts": float(self.clock()),
        }
        with self._lock:
            eventos = list(self._obter("diagnostico_falhas", []) or [])
            eventos.append(evento)
            self._atualizar(diagnostico_falhas=eventos[-self.limite_eventos:])
        return dict(evento)

    def registrar_decisao(
        self,
        componente: str,
        acao: str,
        motivos: Iterable[Any] = (),
        *,
        categoria: str = "",
    ) -> Dict[str, Any]:
        evento = {
            "componente": _codigo(componente, "desconhecido", 64),
            "acao": _codigo(acao, "indefinida", 48),
            "categoria": _codigo(categoria, "", 64) if categoria else "",
            "motivos": [_codigo(item, limite=96) for item in list(motivos or ())[:4]],
            "ts": float(self.clock()),
        }
        with self._lock:
            eventos = list(self._obter("diagnostico_decisoes", []) or [])
            eventos.append(evento)
            self._atualizar(diagnostico_decisoes=eventos[-self.limite_eventos:])
        return dict(evento)


def criar_observabilidade_mente_runtime(**kwargs: Any) -> ObservabilidadeMenteRuntime:
    return ObservabilidadeMenteRuntime(**kwargs)
