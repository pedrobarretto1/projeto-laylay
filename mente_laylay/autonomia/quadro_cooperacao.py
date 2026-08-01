"""Quadro efêmero e contratos de estado da cooperação entre habilidades."""

from __future__ import annotations

import copy
import hashlib
import re
import secrets
import threading
import time
import unicodedata
from collections import deque
from typing import Any, Callable, Iterable, Mapping


ESTADOS_PLANO = frozenset({
    "observado", "enriquecido", "proposto", "aguardando_autorizacao",
    "autorizado", "executando", "confirmado", "falhou", "cancelado", "expirado",
})
ESTADOS_FINAIS = frozenset({"confirmado", "falhou", "cancelado", "expirado"})
ESTADOS_ETAPA = frozenset({
    "proposto", "executando", "confirmado", "falhou", "bloqueado", "cancelado", "expirado",
})
POLITICAS_FALHA_ETAPA = frozenset({"interromper", "continuar"})
POLITICAS_FALHA_PLANO = frozenset({"interromper", "continuar_independentes"})


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


def _hash_texto(texto: str) -> str:
    return hashlib.sha256(str(texto or "").encode("utf-8", errors="replace")).hexdigest()


class QuadroCooperacaoRuntime:
    """Quadro efêmero de eventos, planos e referências privadas."""

    def __init__(
        self,
        *,
        modo: str = "sombra",
        relogio: Callable[[], float] = time.time,
        publicar_contexto: Callable[[Mapping[str, Any]], Any] | None = None,
        log: Callable[[str], Any] = print,
        limite_eventos: int = 80,
        limite_planos: int = 40,
    ) -> None:
        self.modo = "ativo" if str(modo).casefold() == "ativo" else "sombra"
        self.relogio = relogio
        self.publicar_contexto = publicar_contexto
        self.log = log
        self._lock = threading.RLock()
        self._eventos: deque[dict[str, Any]] = deque(maxlen=max(10, int(limite_eventos)))
        self._planos: dict[str, dict[str, Any]] = {}
        self._ordem_planos: deque[str] = deque(maxlen=max(10, int(limite_planos)))
        self._referencias: dict[str, dict[str, Any]] = {}
        self._diagnostico = {
            "eventos": 0, "planos": 0, "confirmados": 0, "falhas": 0,
            "cancelados": 0, "expirados": 0, "deduplicados": 0,
            "etapas_confirmadas": 0, "etapas_falhas": 0,
            "dependencias_bloqueadas": 0, "orcamentos_excedidos": 0,
            "falhas_parciais": 0, "cancelamentos_solicitados": 0,
            "autorizacoes_bloqueadas": 0, "finalizacoes_governanca": 0,
            "referencias_consumidas": 0,
            "ultimo_tipo": "", "ultimo_estado": "inicio",
        }

    def _agora(self) -> float:
        return float(self.relogio())

    def _limpar_expirados(self) -> None:
        agora = self._agora()
        for token, item in list(self._referencias.items()):
            if float(item.get("expira_em") or 0.0) <= agora:
                self._referencias.pop(token, None)
        for plano_id, plano in list(self._planos.items()):
            if (
                str(plano.get("estado") or "") not in ESTADOS_FINAIS
                and float(plano.get("expira_em") or 0.0) <= agora
            ):
                plano["estado"] = "expirado"
                plano["atualizado_em"] = agora
                self._diagnostico["expirados"] += 1

    def _publicar(self) -> None:
        if not callable(self.publicar_contexto):
            return
        try:
            self.publicar_contexto(self.snapshot())
        except Exception as erro:
            self.log(f"⚠️ [COOPERAÇÃO] contexto não publicado: {type(erro).__name__}")

    def guardar_referencia(
        self, valor: str, *, tipo: str, ttl_s: float = 600.0,
    ) -> dict[str, Any]:
        texto = str(valor or "")
        token = secrets.token_urlsafe(18)
        agora = self._agora()
        item = {
            "token": token,
            "tipo": str(tipo or "conteudo_temporario")[:80],
            "valor": texto,
            "hash": _hash_texto(texto),
            "tamanho": len(texto),
            "criada_em": agora,
            "expira_em": agora + max(1.0, float(ttl_s)),
            "leituras": 0,
        }
        with self._lock:
            self._limpar_expirados()
            self._referencias[token] = item
        return {chave: item[chave] for chave in ("token", "tipo", "hash", "tamanho", "expira_em")}

    def resolver_referencia(
        self, token: str, *, hash_esperado: str = "",
    ) -> dict[str, Any]:
        with self._lock:
            self._limpar_expirados()
            item = self._referencias.get(str(token or ""))
            if not item:
                return {"ok": False, "status": "referencia_expirada"}
            if hash_esperado and str(item.get("hash") or "") != str(hash_esperado):
                return {"ok": False, "status": "referencia_divergente"}
            item["leituras"] = int(item.get("leituras") or 0) + 1
            return {
                "ok": True,
                "status": "referencia_resolvida",
                "conteudo": str(item.get("valor") or ""),
                "hash": str(item.get("hash") or ""),
                "tamanho": int(item.get("tamanho") or 0),
            }

    def consumir_referencia(self, token: str) -> bool:
        """Descarta um dado privado depois de confirmação ou cancelamento final."""
        with self._lock:
            removida = self._referencias.pop(str(token or ""), None) is not None
            if removida:
                self._diagnostico["referencias_consumidas"] += 1
            return removida

    def publicar_evento(
        self,
        *,
        origem: str,
        tipo: str,
        resumo: str,
        confianca: float,
        relevancia: float,
        sensibilidade: str = "baixa",
        validade_s: float = 300.0,
        habilidades: Iterable[str] = (),
        evidencias: Iterable[str] = (),
        chave_deduplicacao: str = "",
        referencia: str = "",
    ) -> dict[str, Any]:
        agora = self._agora()
        chave = str(chave_deduplicacao or "").strip()[:160]
        with self._lock:
            self._limpar_expirados()
            if chave:
                repetido = next((
                    item for item in reversed(self._eventos)
                    if item.get("chave_deduplicacao") == chave
                    and float(item.get("expira_em") or 0.0) > agora
                ), None)
                if repetido:
                    self._diagnostico["deduplicados"] += 1
                    return dict(repetido)
            evento = {
                "id": secrets.token_hex(8),
                "origem": str(origem or "")[:80],
                "tipo": str(tipo or "")[:80],
                "resumo": re.sub(r"\s+", " ", str(resumo or "")).strip()[:240],
                "confianca": max(0.0, min(1.0, float(confianca))),
                "relevancia": max(0.0, min(1.0, float(relevancia))),
                "sensibilidade": str(sensibilidade or "baixa")[:40],
                "habilidades": [str(item)[:80] for item in habilidades if str(item).strip()][:8],
                "evidencias": [str(item)[:160] for item in evidencias if str(item).strip()][:8],
                "chave_deduplicacao": chave,
                "tem_referencia": bool(referencia),
                "referencia": str(referencia or ""),
                "criado_em": agora,
                "expira_em": agora + max(1.0, float(validade_s)),
                "estado": "observado",
            }
            self._eventos.append(evento)
            self._diagnostico["eventos"] += 1
            self._diagnostico["ultimo_tipo"] = evento["tipo"]
        self._publicar()
        return dict(evento)

    def criar_plano(
        self,
        *,
        objetivo: str,
        evento_ids: Iterable[str],
        etapas: Iterable[Mapping[str, Any]],
        confianca: float,
        risco: str,
        autorizacao: str,
        validade_s: float = 600.0,
        orcamento_total_ms: int = 8_000,
        politica_falha_parcial: str = "interromper",
        metadados: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        agora = self._agora()
        plano_id = secrets.token_hex(8)
        politica_plano = str(politica_falha_parcial or "interromper").strip().casefold()
        if politica_plano not in POLITICAS_FALHA_PLANO:
            raise ValueError("politica_falha_parcial inválida")
        etapas_normalizadas: list[dict[str, Any]] = []
        ids_vistos: set[str] = set()
        for indice, etapa_original in enumerate(list(etapas)[:12], start=1):
            etapa = dict(etapa_original or {})
            ordem = int(etapa.get("ordem") or indice)
            etapa_id = str(etapa.get("id") or ordem).strip()[:80]
            if not etapa_id or etapa_id in ids_vistos:
                raise ValueError("etapas do plano precisam de identificadores únicos")
            dependencias = [
                str(item).strip()[:80]
                for item in list(etapa.get("depende_de") or [])
                if str(item).strip()
            ]
            if any(item not in ids_vistos for item in dependencias):
                raise ValueError("dependência precisa apontar para uma etapa anterior")
            estado_etapa = str(etapa.get("estado") or "proposto").strip().casefold()
            if estado_etapa not in ESTADOS_ETAPA:
                raise ValueError("estado de etapa inválido")
            politica_etapa = str(etapa.get("politica_falha") or "interromper").strip().casefold()
            if politica_etapa not in POLITICAS_FALHA_ETAPA:
                raise ValueError("política de falha da etapa inválida")
            if etapa.get("idempotente", True) is not True:
                raise ValueError("etapas cooperativas precisam ser idempotentes")
            ids_vistos.add(etapa_id)
            etapas_normalizadas.append({
                "id": etapa_id,
                "ordem": ordem,
                "habilidade": str(etapa.get("habilidade") or "")[:80],
                "acao": str(etapa.get("acao") or "")[:100],
                "intent": str(etapa.get("intent") or "").strip().upper()[:100],
                "depende_de": dependencias,
                "estado": estado_etapa,
                "obrigatoria": bool(etapa.get("obrigatoria", True)),
                "idempotente": True,
                "orcamento_ms": max(1, min(120_000, int(etapa.get("orcamento_ms") or 2_000))),
                "politica_falha": politica_etapa,
                "evidencia_esperada": str(etapa.get("evidencia_esperada") or "")[:160],
                "resultado": {},
                "duracao_ms": 0,
            })
        plano = {
            "id": plano_id,
            "objetivo": str(objetivo or "")[:160],
            "eventos": [str(item)[:80] for item in evento_ids if str(item).strip()][:12],
            "etapas": etapas_normalizadas,
            "confianca": max(0.0, min(1.0, float(confianca))),
            "risco": str(risco or "baixo")[:40],
            "autorizacao": str(autorizacao or "necessaria")[:80],
            "estado": "proposto",
            "criado_em": agora,
            "atualizado_em": agora,
            "expira_em": agora + max(1.0, float(validade_s)),
            "orcamento_total_ms": max(1, min(300_000, int(orcamento_total_ms))),
            "politica_falha_parcial": politica_plano,
            "cancelamento_solicitado": False,
            "motivo_cancelamento": "",
            "iniciado_em": 0.0,
            "encerrado_em": 0.0,
            "versao_contrato": 2,
            "metadados": dict(metadados or {}),
            "resultado": {},
        }
        with self._lock:
            self._limpar_expirados()
            if len(self._ordem_planos) == self._ordem_planos.maxlen:
                antigo = self._ordem_planos[0]
                self._planos.pop(antigo, None)
            self._ordem_planos.append(plano_id)
            self._planos[plano_id] = plano
            self._diagnostico["planos"] += 1
            self._diagnostico["ultimo_estado"] = "proposto"
        self._publicar()
        return copy.deepcopy(plano)

    def obter_plano(self, plano_id: str) -> dict[str, Any] | None:
        with self._lock:
            self._limpar_expirados()
            plano = self._planos.get(str(plano_id or ""))
            return copy.deepcopy(plano) if plano else None

    def atualizar_plano(
        self, plano_id: str, estado: str, *, resultado: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        estado = str(estado or "").strip().casefold()
        if estado not in ESTADOS_PLANO:
            return None
        with self._lock:
            self._limpar_expirados()
            plano = self._planos.get(str(plano_id or ""))
            if not plano:
                return None
            estado_anterior = str(plano.get("estado") or "")
            if estado_anterior in ESTADOS_FINAIS and estado != estado_anterior:
                return copy.deepcopy(plano)
            plano["estado"] = estado
            plano["atualizado_em"] = self._agora()
            if estado == "executando" and not float(plano.get("iniciado_em") or 0.0):
                plano["iniciado_em"] = plano["atualizado_em"]
            if estado in ESTADOS_FINAIS:
                plano["encerrado_em"] = plano["atualizado_em"]
            if resultado is not None:
                plano["resultado"] = dict(resultado)
            self._diagnostico["ultimo_estado"] = estado
            if estado == "confirmado" and estado_anterior != estado:
                self._diagnostico["confirmados"] += 1
            elif estado == "falhou" and estado_anterior != estado:
                self._diagnostico["falhas"] += 1
            elif estado == "cancelado" and estado_anterior != estado:
                self._diagnostico["cancelados"] += 1
            elif estado == "expirado" and estado_anterior != estado:
                self._diagnostico["expirados"] += 1
            retorno = copy.deepcopy(plano)
        self._publicar()
        return retorno

    def atualizar_etapa(
        self,
        plano_id: str,
        etapa_id: str | int,
        estado: str,
        *,
        resultado: Mapping[str, Any] | None = None,
        duracao_ms: int = 0,
    ) -> dict[str, Any] | None:
        estado = str(estado or "").strip().casefold()
        if estado not in ESTADOS_ETAPA:
            return None
        with self._lock:
            self._limpar_expirados()
            plano = self._planos.get(str(plano_id or ""))
            if not plano:
                return None
            etapa = next((
                item for item in plano.get("etapas", [])
                if str(item.get("id") or "") == str(etapa_id)
            ), None)
            if not etapa:
                return None
            anterior = str(etapa.get("estado") or "")
            if anterior in {"confirmado", "cancelado", "expirado"} and estado != anterior:
                return copy.deepcopy(etapa)
            permitido = {"status", "confirmado", "evidencia", "motivo", "orcamento_excedido"}
            resultado_anterior = dict(etapa.get("resultado") or {})
            etapa["estado"] = estado
            etapa["duracao_ms"] = max(0, int(duracao_ms))
            etapa["resultado"] = {
                str(chave)[:80]: valor
                for chave, valor in dict(resultado or {}).items()
                if str(chave) in permitido and isinstance(valor, (str, int, float, bool, type(None)))
            }
            plano["atualizado_em"] = self._agora()
            if estado == "confirmado" and anterior != estado:
                self._diagnostico["etapas_confirmadas"] += 1
            elif estado == "falhou" and anterior != estado:
                self._diagnostico["etapas_falhas"] += 1
            elif estado == "bloqueado" and anterior != estado:
                self._diagnostico["dependencias_bloqueadas"] += 1
            if etapa["resultado"].get("orcamento_excedido") and not resultado_anterior.get("orcamento_excedido"):
                self._diagnostico["orcamentos_excedidos"] += 1
            retorno = copy.deepcopy(etapa)
        self._publicar()
        return retorno

    def solicitar_cancelamento(self, plano_id: str, motivo: str = "pedido_do_usuario") -> dict[str, Any] | None:
        with self._lock:
            self._limpar_expirados()
            plano = self._planos.get(str(plano_id or ""))
            if not plano:
                return None
            if str(plano.get("estado") or "") in ESTADOS_FINAIS:
                return copy.deepcopy(plano)
            plano["cancelamento_solicitado"] = True
            plano["motivo_cancelamento"] = str(motivo or "pedido_do_usuario")[:160]
            self._diagnostico["cancelamentos_solicitados"] += 1
            if str(plano.get("estado") or "") != "executando":
                plano["estado"] = "cancelado"
                plano["encerrado_em"] = self._agora()
                plano["atualizado_em"] = plano["encerrado_em"]
                self._diagnostico["cancelados"] += 1
                self._diagnostico["ultimo_estado"] = "cancelado"
            retorno = copy.deepcopy(plano)
        self._publicar()
        return retorno

    def registrar_falha_parcial(self) -> None:
        with self._lock:
            self._diagnostico["falhas_parciais"] += 1

    def registrar_autorizacao_bloqueada(self) -> None:
        with self._lock:
            self._diagnostico["autorizacoes_bloqueadas"] += 1

    def registrar_finalizacao_governanca(self) -> None:
        with self._lock:
            self._diagnostico["finalizacoes_governanca"] += 1

    @staticmethod
    def _plano_publico(plano: Mapping[str, Any]) -> dict[str, Any]:
        metadados = dict(plano.get("metadados") or {})
        metadados_publicos = {
            "fluxo": str(metadados.get("fluxo") or "")[:80],
            "nome": str(metadados.get("nome") or "")[:120],
            "tamanho_conteudo": int(metadados.get("tamanho_conteudo") or 0),
            "quantidade_janelas": int(metadados.get("quantidade_janelas") or 0),
        }
        return {
            "id": str(plano.get("id") or ""),
            "objetivo": str(plano.get("objetivo") or ""),
            "estado": str(plano.get("estado") or ""),
            "confianca": float(plano.get("confianca") or 0.0),
            "risco": str(plano.get("risco") or ""),
            "autorizacao": str(plano.get("autorizacao") or ""),
            "orcamento_total_ms": int(plano.get("orcamento_total_ms") or 0),
            "politica_falha_parcial": str(plano.get("politica_falha_parcial") or ""),
            "cancelamento_solicitado": bool(plano.get("cancelamento_solicitado")),
            "habilidades": [
                str(item.get("habilidade") or "")
                for item in list(plano.get("etapas") or [])
                if isinstance(item, Mapping)
            ],
            "etapas": [{
                "id": str(item.get("id") or ""),
                "habilidade": str(item.get("habilidade") or ""),
                "acao": str(item.get("acao") or ""),
                "intent": str(item.get("intent") or ""),
                "estado": str(item.get("estado") or ""),
                "depende_de": list(item.get("depende_de") or []),
                "orcamento_ms": int(item.get("orcamento_ms") or 0),
                "duracao_ms": int(item.get("duracao_ms") or 0),
                "evidencia_esperada": str(item.get("evidencia_esperada") or ""),
            } for item in list(plano.get("etapas") or []) if isinstance(item, Mapping)],
            "metadados": metadados_publicos,
        }

    def plano_publico(self, plano: Mapping[str, Any]) -> dict[str, Any]:
        return self._plano_publico(plano)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._limpar_expirados()
            eventos = [{
                "id": str(evento.get("id") or ""),
                "origem": str(evento.get("origem") or ""),
                "tipo": str(evento.get("tipo") or ""),
                "resumo": str(evento.get("resumo") or ""),
                "confianca": float(evento.get("confianca") or 0.0),
                "relevancia": float(evento.get("relevancia") or 0.0),
                "sensibilidade": str(evento.get("sensibilidade") or ""),
                "habilidades": list(evento.get("habilidades") or []),
                "tem_referencia": bool(evento.get("tem_referencia")),
                "estado": str(evento.get("estado") or ""),
            } for evento in list(self._eventos)[-8:]]
            planos = [
                self._plano_publico(self._planos[plano_id])
                for plano_id in list(self._ordem_planos)[-5:]
                if plano_id in self._planos
            ]
            return {"modo": self.modo, "eventos_recentes": eventos, "planos_recentes": planos}

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            self._limpar_expirados()
            return {
                "modo": self.modo,
                **dict(self._diagnostico),
                "referencias_ativas": len(self._referencias),
                "planos_ativos": sum(
                    1 for item in self._planos.values()
                    if str(item.get("estado") or "") not in ESTADOS_FINAIS
                ),
            }
