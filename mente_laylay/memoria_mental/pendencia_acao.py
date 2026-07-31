"""Pendência operacional canônica da mente única.

O runtime não guarda uma segunda cópia do estado: toda leitura e mutação passa
pelo EstadoCompartilhadoRuntime. O conteúdo sensível da ação nunca entra aqui;
somente identificadores, metadados sanitizados e a pergunta já falada.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Callable, Mapping

from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)


CHAVE_PENDENCIA_ACAO = "pendencia_acao_canonica"


class PendenciaAcaoRuntime:
    def __init__(
        self,
        *,
        estado_getter: Callable[[], Mapping[str, Any]],
        estado_atualizar: Callable[[Callable[[dict], dict]], Mapping[str, Any]],
        agora: Callable[[], float] = time.time,
        log: Callable[[str], Any] = print,
    ) -> None:
        self._estado_getter = estado_getter
        self._estado_atualizar = estado_atualizar
        self._agora = agora
        self._log = log

    def _id(self, origem: str, acao: str, referencia: str) -> str:
        material = f"{origem}|{acao}|{referencia}|{self._agora():.6f}"
        return hashlib.sha256(material.encode("utf-8", errors="ignore")).hexdigest()[:12]

    def obter(self, *, incluir_processando: bool = True) -> dict[str, Any] | None:
        item = dict((self._estado_getter() or {}).get(CHAVE_PENDENCIA_ACAO) or {})
        permitidos = {"ativa", "em_processamento"} if incluir_processando else {"ativa"}
        if item.get("status") not in permitidos:
            return None
        if float(item.get("expira_em") or 0.0) <= float(self._agora()):
            self.concluir(str(item.get("id") or ""), "expirada")
            return None
        return item

    def registrar(
        self,
        *,
        origem: str,
        acao: str,
        pergunta: str,
        referencia: str = "",
        metadados: Mapping[str, Any] | None = None,
        ttl_s: float = 300.0,
    ) -> dict[str, Any] | None:
        origem, acao = str(origem or "").strip(), str(acao or "").strip()
        if not origem or not acao:
            return None
        instante = float(self._agora())
        novo = {
            "id": self._id(origem, acao, referencia),
            "origem": origem,
            "acao": acao,
            "pergunta": str(pergunta or "").strip()[:300],
            "referencia": str(referencia or "").strip()[:160],
            "metadados": dict(metadados or {}),
            "status": "ativa",
            "criada_em": instante,
            "expira_em": instante + max(1.0, float(ttl_s or 300.0)),
        }
        resultado = {"registrada": False}

        def _atualizar(estado: dict) -> dict:
            atual = dict(estado.get(CHAVE_PENDENCIA_ACAO) or {})
            if atual.get("status") == "em_processamento":
                return estado
            estado[CHAVE_PENDENCIA_ACAO] = novo
            resultado["registrada"] = True
            return estado

        self._estado_atualizar(_atualizar)
        if not resultado["registrada"]:
            return None
        self._log(
            f"🧠 [PENDÊNCIA:AÇÃO] criada | id={novo['id']} "
            f"origem={origem} ação={acao}"
        )
        return dict(novo)

    def resolver(
        self,
        texto: str,
        *,
        classificar_dominio: Callable[[str, str], str] | None = None,
        classificar_contextual: Callable[[str, str], Any] | None = None,
    ) -> dict[str, Any]:
        item = self.obter(incluir_processando=True)
        if not item:
            return {"tratado": False, "status": "sem_pendencia"}
        if item.get("status") == "em_processamento":
            return {"tratado": True, "status": "em_processamento", "pendencia": item}

        local = classificar_confirmacao_local(texto)
        if local is True:
            decisao = "aceitar"
        elif local is False:
            decisao = "recusar"
        else:
            decisao = "ignorar"
            if callable(classificar_dominio):
                decisao = str(classificar_dominio(texto, str(item.get("acao") or "")) or "ignorar")
            if decisao == "ignorar" and callable(classificar_contextual):
                natural = classificar_contextual(texto, str(item.get("pergunta") or ""))
                if natural is True:
                    decisao = "aceitar"
                elif natural is False:
                    decisao = "recusar"
        if decisao not in {"aceitar", "recusar"}:
            return {"tratado": False, "status": "nao_relacionada", "pendencia": item}

        id_esperado = str(item.get("id") or "")
        resultado = {"alterada": False}

        def _atualizar(estado: dict) -> dict:
            atual = dict(estado.get(CHAVE_PENDENCIA_ACAO) or {})
            if str(atual.get("id") or "") != id_esperado or atual.get("status") != "ativa":
                return estado
            atual["status"] = "em_processamento" if decisao == "aceitar" else "recusada"
            atual["respondida_em"] = float(self._agora())
            estado[CHAVE_PENDENCIA_ACAO] = atual
            resultado["alterada"] = True
            return estado

        self._estado_atualizar(_atualizar)
        if not resultado["alterada"]:
            return {"tratado": True, "status": "concorrente", "pendencia": item}
        self._log(
            f"🧠 [PENDÊNCIA:AÇÃO] resposta | id={id_esperado} decisão={decisao}"
        )
        return {"tratado": True, "status": decisao, "pendencia": {**item, "status": decisao}}

    def concluir(self, pendencia_id: str, status: str) -> bool:
        concluida = {"valor": False}

        def _atualizar(estado: dict) -> dict:
            atual = dict(estado.get(CHAVE_PENDENCIA_ACAO) or {})
            if not atual or (pendencia_id and str(atual.get("id") or "") != pendencia_id):
                return estado
            atual["status"] = str(status or "concluida")
            atual["encerrada_em"] = float(self._agora())
            estado["ultima_pendencia_acao"] = atual
            estado[CHAVE_PENDENCIA_ACAO] = {}
            concluida["valor"] = True
            return estado

        self._estado_atualizar(_atualizar)
        if concluida["valor"]:
            self._log(f"🧠 [PENDÊNCIA:AÇÃO] encerrada | id={pendencia_id} status={status}")
        return bool(concluida["valor"])

    def diagnostico(self) -> dict[str, Any]:
        item = self.obter(incluir_processando=True)
        return {
            "ativa": bool(item),
            "id": str((item or {}).get("id") or ""),
            "origem": str((item or {}).get("origem") or ""),
            "acao": str((item or {}).get("acao") or ""),
            "status": str((item or {}).get("status") or "sem_pendencia"),
        }


def criar_pendencia_acao_runtime(**kwargs: Any) -> PendenciaAcaoRuntime:
    return PendenciaAcaoRuntime(**kwargs)
