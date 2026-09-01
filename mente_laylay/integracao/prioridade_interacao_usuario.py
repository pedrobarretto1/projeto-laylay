from __future__ import annotations

import threading
from typing import Any


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