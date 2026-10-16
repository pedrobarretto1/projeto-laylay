from __future__ import annotations

import threading
import math
from typing import Any, Mapping


def conversa_em_andamento(contexto: Mapping[str, Any], *, agora: float,
                         ultima_fala_ts: float = 0.0) -> bool:
    """Prioridade vem da atividade vigente; canal aberto sozinho não a retém."""
    if any(contexto.get(c) for c in ('interacao_usuario_ativa',
            'interacao_em_andamento', 'usuario_falando', 'is_speaking')):
        return True
    if not (contexto.get('modo_chat') or contexto.get('conversa_ativa')):
        return False
    if contexto.get('turno_ativo'):
        return True
    try:
        referencias = (float(contexto.get('ultima_entrada_ts') or 0),
                       float(ultima_fala_ts or contexto.get('ultima_fala_normal_ts') or 0))
        if not math.isfinite(agora) or any(not math.isfinite(t) for t in referencias):
            return True
        return any(t > 0 and agora-t < 30 for t in referencias)
    except (TypeError, ValueError, OverflowError):
        return True


class PrioridadeInteracaoUsuarioRuntime:
    """Owner canônico e concorrente da prioridade da interação do usuário."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sequencia = 0
        self._claims: dict[str, str] = {}

    @staticmethod
    def _normalizar_fonte(fonte: Any) -> str:
        valor = str(fonte or "").strip().casefold()

        if not valor:
            raise ValueError(
                "fonte do claim de interação não pode ser vazia"
            )

        return valor

    def adquirir(self, fonte: str) -> str:
        """Adquire um claim independente e devolve seu token exclusivo."""

        fonte_norm = self._normalizar_fonte(fonte)

        with self._lock:
            self._sequencia += 1

            token = (
                f"interacao-usuario-{self._sequencia:08d}"
            )

            self._claims[token] = fonte_norm

            return token

    def liberar(self, claim: str) -> bool:
        """Libera somente o claim identificado pelo token recebido.

        Tokens desconhecidos, já liberados ou vazios são stale releases e
        nunca podem afetar outros owners.
        """

        token = str(claim or "").strip()

        if not token:
            return False

        with self._lock:
            if token not in self._claims:
                return False

            del self._claims[token]
            return True

    def ativa(self) -> bool:
        """Indica se qualquer fase ainda possui a interação do usuário."""

        with self._lock:
            return bool(self._claims)

    def snapshot(self) -> dict[str, Any]:
        """Retorna observabilidade isolada sem expor estado mutável interno."""

        with self._lock:
            claims = dict(self._claims)

        fontes = sorted(set(claims.values()))

        contagem_por_fonte: dict[str, int] = {}

        for fonte in claims.values():
            contagem_por_fonte[fonte] = (
                contagem_por_fonte.get(fonte, 0) + 1
            )

        return {
            "ativa": bool(claims),
            "total_claims": len(claims),
            "fontes_ativas": fontes,
            "claims_por_fonte": contagem_por_fonte,
        }


def criar_prioridade_interacao_usuario_runtime(
    **_kwargs: Any,
) -> PrioridadeInteracaoUsuarioRuntime:
    return PrioridadeInteracaoUsuarioRuntime()
