"""Coordenação segura entre habilidades da mente única.

Habilidades publicam evidências e contribuições; somente este coordenador cria
um plano. Percepções não viram ordens, referências sensíveis ficam apenas em
RAM e a execução continua passando pelos porteiros e executores canônicos.
"""

from __future__ import annotations

import hashlib
import copy
import os
import re
import secrets
import threading
import time
import unicodedata
from collections import deque
from pathlib import Path
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


class GovernancaPlanoCooperativoRuntime:
    """Liga o plano aos porteiros e registros canônicos da mente única."""

    AUTORIZACOES_VALIDAS = frozenset({
        "explicita_no_pedido", "confirmacao_explicita",
        "autonomia_previamente_concedida", "somente_leitura", "teste_explicito",
    })
    RISCOS_COM_CONFIRMACAO = frozenset({"alto", "destrutivo", "irreversivel"})

    def __init__(
        self,
        *,
        quadro: QuadroCooperacaoRuntime,
        autorizar_acao: Callable[..., Mapping[str, Any]] | None = None,
        registrar_continuidade: Callable[[Mapping[str, Any], str], Any] | None = None,
        registrar_aprendizado: Callable[[Mapping[str, Any], str], Any] | None = None,
        registrar_decisao: Callable[..., Any] | None = None,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.quadro = quadro
        self.autorizar_acao = autorizar_acao
        self.registrar_continuidade = registrar_continuidade
        self.registrar_aprendizado = registrar_aprendizado
        self.registrar_decisao = registrar_decisao
        self.log = log
        self._lock = threading.RLock()
        self._finalizados: set[str] = set()

    def avaliar_autorizacao(
        self,
        plano: Mapping[str, Any],
        etapa: Mapping[str, Any],
        contexto: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        dados = dict(contexto or {})
        autorizacao = str(plano.get("autorizacao") or "").strip().casefold()
        risco = str(plano.get("risco") or "baixo").strip().casefold()
        confirmado = bool(dados.get("confirmado"))
        if autorizacao not in self.AUTORIZACOES_VALIDAS:
            return {"permitido": False, "motivo": "autorizacao_do_plano_invalida"}
        if risco in self.RISCOS_COM_CONFIRMACAO and not confirmado:
            return {"permitido": False, "motivo": "confirmacao_explicita_necessaria"}
        if not callable(self.autorizar_acao):
            return {"permitido": True, "motivo": autorizacao}
        acao = str(etapa.get("intent") or etapa.get("acao") or "")
        try:
            decisao = dict(self.autorizar_acao(
                acao,
                str(dados.get("texto") or ""),
                confirmado=confirmado,
                origem="orquestracao_cooperativa",
            ) or {})
        except Exception as erro:
            self.log(
                "⚠️ [COOPERAÇÃO] porteiro canônico indisponível | "
                f"erro={type(erro).__name__}"
            )
            return {"permitido": False, "motivo": "porteiro_indisponivel"}
        return {
            "permitido": bool(decisao.get("permitido")),
            "motivo": str(decisao.get("motivo") or "porteiro_negou"),
        }

    def registrar_ciclo(self, plano: Mapping[str, Any], evento: str) -> None:
        if not callable(self.registrar_continuidade):
            return
        try:
            self.registrar_continuidade(self.quadro.plano_publico(plano), str(evento or ""))
        except Exception as erro:
            self.log(
                "⚠️ [COOPERAÇÃO] continuidade não registrada | "
                f"erro={type(erro).__name__}"
            )

    def finalizar(
        self,
        plano: Mapping[str, Any],
        *,
        decisao: str,
        motivo: str,
    ) -> bool:
        plano_id = str(plano.get("id") or "")
        with self._lock:
            if not plano_id or plano_id in self._finalizados:
                return False
            self._finalizados.add(plano_id)
        publico = self.quadro.plano_publico(plano)
        if callable(self.registrar_aprendizado):
            try:
                self.registrar_aprendizado(publico, str(decisao or ""))
            except Exception:
                pass
        if callable(self.registrar_decisao):
            try:
                self.registrar_decisao(
                    "orquestracao_cooperativa", str(decisao or ""),
                    (str(motivo or "")[:160],),
                    categoria=str((publico.get("metadados") or {}).get("fluxo") or "plano"),
                )
            except Exception:
                pass
        self.registrar_ciclo(plano, "finalizado")
        self.quadro.registrar_finalizacao_governanca()
        return True


class ExecutorPlanoCooperativoRuntime:
    """Executa etapas autorizadas sem falar e sem contornar executores canônicos.

    O orçamento é cooperativo: ele impede o início de novas etapas depois do
    limite, mas não abandona uma chamada que já alterou estado. Cada adaptador
    continua responsável por seus próprios timeouts e pela evidência real.
    """

    def __init__(
        self,
        *,
        quadro: QuadroCooperacaoRuntime,
        governanca: GovernancaPlanoCooperativoRuntime | None = None,
        relogio: Callable[[], float] = time.monotonic,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.quadro = quadro
        self.governanca = governanca or GovernancaPlanoCooperativoRuntime(quadro=quadro, log=log)
        self.relogio = relogio
        self.log = log

    def _agora(self) -> float:
        return float(self.relogio())

    @staticmethod
    def _executor_da_etapa(
        etapa: Mapping[str, Any],
        executores: Mapping[str, Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]],
    ) -> Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]] | None:
        chaves = (
            str(etapa.get("id") or ""),
            str(etapa.get("acao") or ""),
            f"{etapa.get('habilidade') or ''}:{etapa.get('acao') or ''}",
        )
        return next((executores[chave] for chave in chaves if chave in executores), None)

    def executar(
        self,
        plano_id: str,
        executores: Mapping[
            str,
            Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
        ],
        *,
        contexto_execucao: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        plano = self.quadro.obter_plano(plano_id)
        if not plano:
            return {"ok": False, "estado": "expirado", "status": "plano_indisponivel"}
        if str(plano.get("estado") or "") in ESTADOS_FINAIS:
            estado_existente = str(plano.get("estado") or "")
            self.governanca.finalizar(
                plano,
                decisao=("aceito" if estado_existente == "confirmado" else estado_existente),
                motivo=str((plano.get("resultado") or {}).get("status") or "plano_finalizado"),
            )
            return {
                "ok": estado_existente == "confirmado",
                "estado": estado_existente,
                "status": str((plano.get("resultado") or {}).get("status") or "plano_finalizado"),
                "idempotente": True,
            }
        if plano.get("cancelamento_solicitado"):
            final = self.quadro.atualizar_plano(
                plano_id, "cancelado", resultado={"status": "cancelamento_solicitado"},
            ) or plano
            self.governanca.finalizar(
                final, decisao="cancelado", motivo="cancelamento_solicitado",
            )
            return {"ok": False, "estado": final.get("estado"), "status": "cancelamento_solicitado"}

        inicio = self._agora()
        limite_total = inicio + (int(plano.get("orcamento_total_ms") or 1) / 1000.0)
        self.quadro.atualizar_plano(plano_id, "executando")
        self.governanca.registrar_ciclo(self.quadro.obter_plano(plano_id) or plano, "iniciado")
        falhas: list[dict[str, Any]] = []
        interrompido = False
        expirou = False

        for etapa_original in list(plano.get("etapas") or []):
            etapa_id = str(etapa_original.get("id") or "")
            plano_atual = self.quadro.obter_plano(plano_id) or plano
            etapa = next((
                item for item in list(plano_atual.get("etapas") or [])
                if str(item.get("id") or "") == etapa_id
            ), dict(etapa_original))
            if str(etapa.get("estado") or "") == "confirmado":
                continue
            if plano_atual.get("cancelamento_solicitado"):
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "cancelado", resultado={"status": "cancelamento_solicitado"},
                )
                self.quadro.atualizar_plano(
                    plano_id, "cancelado", resultado={"status": "cancelamento_solicitado"},
                )
                final_cancelado = self.quadro.obter_plano(plano_id) or plano_atual
                self.governanca.finalizar(
                    final_cancelado, decisao="cancelado", motivo="cancelamento_solicitado",
                )
                return {"ok": False, "estado": "cancelado", "status": "cancelamento_solicitado"}
            if self._agora() >= limite_total:
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "expirado",
                    resultado={"status": "orcamento_total_excedido", "orcamento_excedido": True},
                )
                expirou = True
                break

            estados = {
                str(item.get("id") or ""): str(item.get("estado") or "")
                for item in list(plano_atual.get("etapas") or [])
            }
            pendentes = [
                dependencia for dependencia in list(etapa.get("depende_de") or [])
                if estados.get(str(dependencia)) != "confirmado"
            ]
            if pendentes:
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "bloqueado",
                    resultado={"status": "dependencia_nao_confirmada", "motivo": ",".join(pendentes)},
                )
                falhas.append({"etapa": etapa_id, "status": "dependencia_nao_confirmada"})
                interrompido = (
                    str(plano.get("politica_falha_parcial") or "interromper") == "interromper"
                    or str(etapa.get("politica_falha") or "interromper") == "interromper"
                )
                if interrompido:
                    break
                continue

            executor = self._executor_da_etapa(etapa, executores)
            autorizacao = self.governanca.avaliar_autorizacao(
                plano_atual, etapa, contexto_execucao,
            )
            if not autorizacao.get("permitido"):
                self.quadro.registrar_autorizacao_bloqueada()
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "bloqueado",
                    resultado={
                        "status": "autorizacao_negada",
                        "motivo": str(autorizacao.get("motivo") or "porteiro_negou"),
                    },
                )
                falhas.append({"etapa": etapa_id, "status": "autorizacao_negada"})
            elif not callable(executor):
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "falhou", resultado={"status": "executor_indisponivel"},
                )
                falhas.append({"etapa": etapa_id, "status": "executor_indisponivel"})
            else:
                inicio_etapa = self._agora()
                self.quadro.atualizar_etapa(plano_id, etapa_id, "executando")
                try:
                    retorno = dict(executor(etapa, plano_atual) or {})
                except Exception as erro:
                    self.log(
                        "⚠️ [COOPERAÇÃO] etapa falhou isoladamente | "
                        f"etapa={etapa_id} erro={type(erro).__name__}"
                    )
                    retorno = {"ok": False, "confirmado": False, "status": "falha_isolada"}
                duracao_ms = max(0, int((self._agora() - inicio_etapa) * 1000))
                confirmou = bool(retorno.get("ok") and retorno.get("confirmado") is True)
                excedeu = duracao_ms > int(etapa.get("orcamento_ms") or 1)
                resultado_etapa = {
                    "status": str(retorno.get("status") or ("confirmado" if confirmou else "nao_confirmado")),
                    "confirmado": confirmou,
                    "evidencia": str(retorno.get("evidencia") or "")[:160],
                    "orcamento_excedido": excedeu,
                }
                if confirmou:
                    self.quadro.atualizar_etapa(
                        plano_id, etapa_id, "confirmado",
                        resultado=resultado_etapa, duracao_ms=duracao_ms,
                    )
                else:
                    estado_falha = "expirado" if excedeu or retorno.get("estado_plano") == "expirado" else "falhou"
                    self.quadro.atualizar_etapa(
                        plano_id, etapa_id, estado_falha,
                        resultado=resultado_etapa, duracao_ms=duracao_ms,
                    )
                    falhas.append({"etapa": etapa_id, "status": resultado_etapa["status"]})
                    expirou = expirou or estado_falha == "expirado"

            if falhas and falhas[-1].get("etapa") == etapa_id:
                interrompido = (
                    str(plano.get("politica_falha_parcial") or "interromper") == "interromper"
                    or str(etapa.get("politica_falha") or "interromper") == "interromper"
                )
                if interrompido:
                    break

        plano_final = self.quadro.obter_plano(plano_id) or plano
        etapas_finais = list(plano_final.get("etapas") or [])
        obrigatorias_ok = all(
            str(item.get("estado") or "") == "confirmado"
            for item in etapas_finais if bool(item.get("obrigatoria", True))
        )
        if falhas and obrigatorias_ok:
            self.quadro.registrar_falha_parcial()
        if expirou and not obrigatorias_ok:
            estado_final = "expirado"
        elif obrigatorias_ok:
            estado_final = "confirmado"
        else:
            estado_final = "falhou"
        status_final = (
            "plano_confirmado_com_falha_parcial"
            if estado_final == "confirmado" and falhas
            else "plano_confirmado"
            if estado_final == "confirmado"
            else "orcamento_excedido"
            if estado_final == "expirado"
            else falhas[-1]["status"] if falhas else "etapas_nao_confirmadas"
        )
        self.quadro.atualizar_plano(
            plano_id,
            estado_final,
            resultado={
                "status": status_final,
                "confirmado": estado_final == "confirmado",
                "falhas_parciais": len(falhas) if obrigatorias_ok else 0,
                "interrompido": interrompido,
            },
        )
        final_atual = self.quadro.obter_plano(plano_id) or plano_final
        decisao = (
            "aceito" if estado_final == "confirmado"
            else "cancelado" if estado_final == "cancelado"
            else "expirado" if estado_final == "expirado"
            else "falhou"
        )
        self.governanca.finalizar(
            final_atual, decisao=decisao, motivo=status_final,
        )
        return {
            "ok": estado_final == "confirmado",
            "estado": estado_final,
            "status": status_final,
            "falhas": falhas,
        }


class OrquestradorCooperativoRuntime:
    """Planeja relações entre habilidades e ativa somente fluxos permitidos."""

    ORIGEM_PENDENCIA = "orquestracao_cooperativa"
    ACAO_SOBRESCREVER = "sobrescrever_arquivo_com_clipboard"

    def __init__(
        self,
        *,
        quadro: QuadroCooperacaoRuntime,
        clipboard_snapshot: Callable[[], Mapping[str, Any]],
        clipboard_getter: Callable[[], str],
        executar_intencao: Callable[[dict[str, Any], str], bool],
        resolver_caminho: Callable[[str], str],
        falar: Callable[[str, str, int], Any],
        planejar_layout: Callable[[], Mapping[str, Any]] | None = None,
        detectar_visao_jogo: Callable[[str], Mapping[str, Any] | None] | None = None,
        estado_getter: Callable[[], Mapping[str, Any]] = lambda: {},
        pendencia_runtime: Any = None,
        classificar_confirmacao_contextual: Callable[[str, str], Any] | None = None,
        registrar_aprendizado: Callable[[Mapping[str, Any], str], Any] | None = None,
        registrar_decisao: Callable[..., Any] | None = None,
        registrar_continuidade: Callable[[Mapping[str, Any], str], Any] | None = None,
        autorizar_acao: Callable[..., Mapping[str, Any]] | None = None,
        executor_plano: ExecutorPlanoCooperativoRuntime | None = None,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.quadro = quadro
        self.clipboard_snapshot = clipboard_snapshot
        self.clipboard_getter = clipboard_getter
        self.executar_intencao = executar_intencao
        self.resolver_caminho = resolver_caminho
        self.falar = falar
        self.planejar_layout = planejar_layout
        self.detectar_visao_jogo = detectar_visao_jogo
        self.estado_getter = estado_getter
        self.pendencia_runtime = pendencia_runtime
        self.classificar_confirmacao_contextual = classificar_confirmacao_contextual
        self.registrar_aprendizado = registrar_aprendizado
        self.registrar_decisao = registrar_decisao
        self.log = log
        self.governanca = GovernancaPlanoCooperativoRuntime(
            quadro=quadro,
            autorizar_acao=autorizar_acao,
            registrar_continuidade=registrar_continuidade,
            registrar_aprendizado=registrar_aprendizado,
            registrar_decisao=registrar_decisao,
            log=log,
        )
        self.executor_plano = executor_plano or ExecutorPlanoCooperativoRuntime(
            quadro=quadro, governanca=self.governanca, log=log,
        )

    def _processar_analise_item_jogo(
        self, pedido: Mapping[str, Any], texto: str,
    ) -> bool:
        params = dict(pedido.get("params") or {})
        jogo = str(params.get("jogo") or "jogo em execução").strip()
        evento = self.quadro.publicar_evento(
            origem="linguagem_natural_jogo",
            tipo="avaliacao_item_solicitada",
            resumo=f"avaliação de item solicitada em {jogo}",
            confianca=0.99,
            relevancia=0.99,
            sensibilidade="local_temporaria",
            validade_s=180.0,
            habilidades=("visao_jogo", "pesquisa_jogos", "memoria_jogos"),
            evidencias=("pedido explícito", "modo jogo ativo"),
            chave_deduplicacao="",
        )
        plano = self.quadro.criar_plano(
            objetivo="identificar e avaliar um item no jogo atual",
            evento_ids=(str(evento.get("id") or ""),),
            etapas=(
                {
                    "id": "ler_item", "ordem": 1,
                    "habilidade": "visao_jogo", "acao": "capturar_e_ler_item",
                    "intent": "GAME_VISION", "estado": "proposto",
                    "orcamento_ms": 60_000, "idempotente": True,
                    "evidencia_esperada": "quadro_atual_lido_sem_inventar_item",
                },
                {
                    "id": "pesquisar_item", "ordem": 2,
                    "habilidade": "pesquisa_jogos", "acao": "enriquecer_item",
                    "depende_de": ["ler_item"], "estado": "proposto",
                    "orcamento_ms": 30_000, "idempotente": True,
                    "politica_falha": "continuar",
                    "evidencia_esperada": "pesquisa_tentada_com_fontes_ou_limite_explicito",
                },
                {
                    "id": "avaliar_build", "ordem": 3,
                    "habilidade": "memoria_jogos", "acao": "cruzar_item_com_perfil",
                    "depende_de": ["pesquisar_item"], "estado": "proposto",
                    "orcamento_ms": 30_000, "idempotente": True,
                    "evidencia_esperada": "parecer_final_contextualizado",
                },
            ),
            confianca=0.99,
            risco="baixo",
            autorizacao="explicita_no_pedido",
            validade_s=180.0,
            orcamento_total_ms=120_000,
            politica_falha_parcial="continuar_independentes",
            metadados={"fluxo": "analise_item_jogo", "jogo": jogo},
        )
        plano_id = str(plano.get("id") or "")
        etapa = next(iter(plano.get("etapas") or []), {})
        autorizacao = self.governanca.avaliar_autorizacao(
            plano, etapa, {"texto": texto, "confirmado": True},
        )
        if not autorizacao.get("permitido"):
            final = self.quadro.atualizar_plano(
                plano_id, "falhou",
                resultado={"status": "autorizacao_negada", "confirmado": False},
            ) or plano
            self.governanca.finalizar(
                final, decisao="falhou", motivo=str(autorizacao.get("motivo") or "autorizacao_negada"),
            )
            self.falar("Não consegui autorizar a leitura do jogo agora.", "calma", 1)
            return True

        self.quadro.atualizar_plano(plano_id, "executando")
        self.quadro.atualizar_etapa(
            plano_id, "ler_item", "executando",
            resultado={"status": "analise_visual_solicitada"},
        )
        self.governanca.registrar_ciclo(plano, "iniciado")
        params["_plano_cooperativo_id"] = plano_id
        tratado = bool(self.executar_intencao({"intent": "GAME_VISION", "params": params}, texto))
        if tratado:
            self.log(
                "🤝 [COOPERAÇÃO] análise de item iniciada | "
                f"id={plano_id} jogo={jogo}"
            )
            return True
        self.registrar_progresso_visao_jogo({
            "plano_id": plano_id, "fase": "falha", "status": "visao_nao_iniciada",
        })
        self.falar("Não consegui iniciar a análise desse item agora.", "calma", 1)
        return True

    def registrar_progresso_visao_jogo(self, evento: Mapping[str, Any]) -> bool:
        """Fecha o plano assíncrono usando apenas evidências sanitizadas da visão."""
        dados = dict(evento or {})
        plano_id = str(dados.get("plano_id") or "")
        fase = str(dados.get("fase") or "").strip().casefold()
        plano = self.quadro.obter_plano(plano_id)
        if not plano or str((plano.get("metadados") or {}).get("fluxo") or "") != "analise_item_jogo":
            return False
        if str(plano.get("estado") or "") in ESTADOS_FINAIS:
            return True
        duracao_ms = max(0, int(dados.get("duracao_ms") or 0))
        status = str(dados.get("status") or fase or "progresso")[:120]
        if fase == "leitura_visual":
            self.quadro.atualizar_etapa(
                plano_id, "ler_item", "confirmado", duracao_ms=duracao_ms,
                resultado={
                    "status": status, "confirmado": True,
                    "evidencia": "quadro_atual_lido_sem_inventar_item",
                },
            )
            self.quadro.atualizar_etapa(
                plano_id, "pesquisar_item", "executando",
                resultado={"status": "enriquecimento_iniciado"},
            )
            return True
        if fase == "pesquisa":
            leitura = next((
                item for item in plano.get("etapas") or []
                if str(item.get("id") or "") == "ler_item"
            ), {})
            if str(leitura.get("estado") or "") != "confirmado":
                return False
            self.quadro.atualizar_etapa(
                plano_id, "pesquisar_item", "confirmado", duracao_ms=duracao_ms,
                resultado={
                    "status": status, "confirmado": True,
                    "evidencia": "pesquisa_tentada_com_fontes_ou_limite_explicito",
                },
            )
            self.quadro.atualizar_etapa(
                plano_id, "avaliar_build", "executando",
                resultado={"status": "contextualizacao_iniciada"},
            )
            return True
        if fase == "parecer_final":
            atual = self.quadro.obter_plano(plano_id) or plano
            pesquisa = next((
                item for item in atual.get("etapas") or []
                if str(item.get("id") or "") == "pesquisar_item"
            ), {})
            if str(pesquisa.get("estado") or "") != "confirmado":
                return False
            self.quadro.atualizar_etapa(
                plano_id, "avaliar_build", "confirmado", duracao_ms=duracao_ms,
                resultado={
                    "status": status, "confirmado": True,
                    "evidencia": "parecer_final_contextualizado",
                },
            )
            final = self.quadro.atualizar_plano(
                plano_id, "confirmado",
                resultado={"status": "parecer_pronto", "confirmado": True},
            ) or atual
            self.governanca.finalizar(final, decisao="aceito", motivo="parecer_pronto")
            self.log(f"🤝 [COOPERAÇÃO] análise de item confirmada | id={plano_id}")
            return True
        if fase == "falha":
            atual = self.quadro.obter_plano(plano_id) or plano
            etapa_atual = next((
                item for item in atual.get("etapas") or []
                if str(item.get("estado") or "") in {"executando", "proposto"}
            ), {})
            if etapa_atual:
                self.quadro.atualizar_etapa(
                    plano_id, str(etapa_atual.get("id") or ""), "falhou",
                    duracao_ms=duracao_ms,
                    resultado={"status": status, "confirmado": False, "motivo": status},
                )
            final = self.quadro.atualizar_plano(
                plano_id, "falhou",
                resultado={"status": status, "confirmado": False},
            ) or atual
            self.governanca.finalizar(final, decisao="falhou", motivo=status)
            return True
        return False

    @staticmethod
    def detectar(texto: str) -> dict[str, Any] | None:
        original = re.sub(r"\s+", " ", str(texto or "")).strip()
        t = _normalizar(original)
        if not t:
            return None
        if re.search(r"^(?:nao|não)\b|\b(?:nao|não)\s+(?:coloca|salva|grava|cria)\b", t):
            return None
        if re.search(
            r"\b(?:como eu faria|talvez|seria legal|seria possivel|se eu pedir|"
            r"voce (?:consegue|pode|sabe))\b",
            t,
        ):
            return None
        organiza_desktop = bool(re.search(
            r"\b(?:organiza|organize|organizar|arruma|arrume|ajeita|ajeite)\b"
            r"[^.!?]{0,60}\b(?:area de trabalho|desktop|janelas|tela)\b",
            t,
        ))
        posicionamento_explicito = bool(re.search(
            r"\b(?:esquerda|direita|lado esquerdo|lado direito)\b",
            t,
        ))
        if organiza_desktop and not posicionamento_explicito:
            return {
                "tipo": "organizacao_desktop_inteligente",
                "confianca": 0.99,
            }
        tem_clipboard = bool(re.search(
            r"\b(?:o que (?:eu )?copiei|texto copiado|conteudo copiado|"
            r"area de transferencia|clipboard)\b",
            t,
        ))
        tem_arquivo = bool(re.search(r"\b(?:arquivo(?: de texto)?|txt|documento de texto)\b", t))
        tem_acao = bool(re.search(
            r"\b(?:coloca|coloque|colocar|salva|salve|salvar|grava|grave|gravar|"
            r"cria|crie|criar|transforma|transforme|transformar)\b",
            t,
        ))
        if not (tem_clipboard and tem_arquivo and tem_acao):
            return None

        pasta = ""
        trecho_nome = ""
        encontrado = re.search(
            r"\b(?:chamado|chamada|com (?:o )?nome|de nome)\s+"
            r"(?P<nome>.+?)(?:\s+dentro\s+(?:da pasta\s+|do diretorio\s+|de\s+)?(?P<pasta>.+))?$",
            original,
            flags=re.IGNORECASE,
        )
        if encontrado:
            trecho_nome = str(encontrado.group("nome") or "")
            pasta = str(encontrado.group("pasta") or "")
        else:
            encontrado = re.search(
                r"\b(?:arquivo(?: de texto)?|txt)\s+(?P<nome>[\w .-]+?)"
                r"(?:\s+(?:com|usando|contendo)\s+(?:o )?(?:texto |conteudo )?(?:que )?(?:eu )?copiei)\b",
                original,
                flags=re.IGNORECASE,
            )
            if encontrado:
                trecho_nome = str(encontrado.group("nome") or "")
        nome = trecho_nome.strip(" .,!?:;\"'")
        pasta = pasta.strip(" .,!?:;\"'")
        if not nome or nome.casefold() in {"arquivo", "texto", "txt", "documento"}:
            return None
        if any(separador in nome for separador in ("/", "\\", ":")) or len(nome) > 120:
            return None
        if not nome.casefold().endswith(".txt"):
            nome = f"{nome}.txt"
        return {
            "tipo": "clipboard_para_arquivo",
            "nome": nome,
            "pasta": pasta,
            "confianca": 0.98,
        }

    def _processar_organizacao_desktop(
        self, intencao: Mapping[str, Any], texto: str,
    ) -> bool:
        if not callable(self.planejar_layout):
            self.falar(
                "Não consegui observar as janelas abertas para montar um layout seguro agora.",
                "calma", 1,
            )
            return True
        try:
            analise = dict(self.planejar_layout() or {})
        except Exception as erro:
            self.log(
                "⚠️ [COOPERAÇÃO:JANELAS] percepção falhou | "
                f"erro={type(erro).__name__}"
            )
            analise = {"ok": False, "status": "falha_percepcao", "prioridades": []}

        prioridades = [
            {
                "titulo": str(item.get("titulo") or "")[:180],
                "pontuacao": float(item.get("pontuacao") or 0.0),
                "motivos": [str(motivo)[:80] for motivo in list(item.get("motivos") or [])[:5]],
            }
            for item in list(analise.get("prioridades") or [])[:5]
            if isinstance(item, Mapping) and str(item.get("titulo") or "").strip()
        ]
        quantidade = max(0, int(analise.get("quantidade") or len(prioridades)))
        assinatura = _hash_texto("|".join(
            str(item.get("titulo") or "") for item in prioridades
        ))
        evento = self.quadro.publicar_evento(
            origem="percepcao_janelas",
            tipo="ambiente_de_trabalho_observado",
            resumo=f"{quantidade} janela(s) organizável(is) observada(s)",
            confianca=float(intencao.get("confianca") or 0.0),
            relevancia=0.97,
            sensibilidade="local_temporaria",
            validade_s=60.0,
            habilidades=("percepcao_janelas", "priorizacao_janelas", "sistema_janelas"),
            evidencias=("janelas visíveis", "foco local", "áudio ativo", "uso recente"),
            chave_deduplicacao=f"layout_janelas:{assinatura}",
        )
        if not analise.get("ok") or not prioridades:
            self._registrar_decisao(
                "falhou", str(analise.get("status") or "sem_janelas_organizaveis"),
                categoria="organizacao_desktop_inteligente",
            )
            self.falar(
                "Não encontrei janelas visíveis suficientes para organizar sem adivinhar.",
                "calma", 1,
            )
            return True

        esquerda = str(analise.get("nome_esquerda") or prioridades[0]["titulo"]).strip()
        direita = str(
            analise.get("nome_direita")
            or (prioridades[1]["titulo"] if len(prioridades) > 1 else "")
        ).strip()
        plano = self.quadro.criar_plano(
            objetivo="organizar a área de trabalho pelas janelas prioritárias",
            evento_ids=(str(evento.get("id") or ""),),
            etapas=(
                {
                    "id": "perceber_janelas", "ordem": 1,
                    "habilidade": "percepcao_janelas", "acao": "observar_janelas_visiveis",
                    "estado": "confirmado", "orcamento_ms": 1_000,
                    "idempotente": True,
                    "evidencia_esperada": "inventario_local_de_janelas_visiveis",
                },
                {
                    "id": "priorizar_janelas", "ordem": 2,
                    "habilidade": "priorizacao_janelas", "acao": "classificar_prioridade",
                    "depende_de": ["perceber_janelas"], "estado": "confirmado",
                    "orcamento_ms": 1_000, "idempotente": True,
                    "evidencia_esperada": "ranking_por_foco_audio_recencia_e_tempo",
                },
                {
                    "id": "aplicar_layout", "ordem": 3,
                    "habilidade": "sistema_janelas", "acao": "aplicar_layout",
                    "intent": "ORGANIZAR_DESKTOP", "depende_de": ["priorizar_janelas"],
                    "estado": "proposto", "orcamento_ms": 5_000,
                    "idempotente": True, "politica_falha": "interromper",
                    "evidencia_esperada": "geometria_final_confirmada",
                },
            ),
            confianca=float(intencao.get("confianca") or 0.0),
            risco="baixo",
            autorizacao="explicita_no_pedido",
            validade_s=60.0,
            orcamento_total_ms=8_000,
            politica_falha_parcial="interromper",
            metadados={
                "fluxo": "organizacao_desktop_inteligente",
                "quantidade_janelas": quantidade,
            },
        )
        plano_id = str(plano.get("id") or "")
        self.log(
            "🤝 [COOPERAÇÃO] plano criado | "
            f"fluxo=organizacao_desktop_inteligente id={plano_id} janelas={quantidade}"
        )

        def aplicar_layout(
            _etapa: Mapping[str, Any], _plano_atual: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            resultado = {
                "intent": "ORGANIZAR_DESKTOP",
                "params": {
                    "left": esquerda,
                    "right": direita,
                    "modo": "automatico_cooperativo",
                    "prioridades_planejadas": prioridades[:2],
                    "plano_cooperativo_id": plano_id,
                },
            }
            tratado = bool(self.executar_intencao(resultado, texto))
            estado = dict(self.estado_getter() or {})
            status = str(estado.get("ultima_acao_status") or "").strip().casefold()
            confirmou = bool(
                tratado
                and str(estado.get("ultima_acao_intent") or "").upper()
                == "ORGANIZAR_DESKTOP"
                and estado.get("ultima_acao_confirmada") is True
                and status == "layout_confirmado"
            )
            return {
                "ok": confirmou,
                "confirmado": confirmou,
                "status": status or "layout_nao_confirmado",
                "evidencia": "geometria_final_confirmada" if confirmou else "",
            }

        self.quadro.atualizar_plano(plano_id, "autorizado")
        resumo = self.executor_plano.executar(
            plano_id,
            {"aplicar_layout": aplicar_layout},
            contexto_execucao={"texto": texto, "confirmado": True},
        )
        if not resumo.get("ok") and str(resumo.get("status") or "") in {
            "autorizacao_negada", "executor_indisponivel", "plano_indisponivel",
        }:
            self.falar(
                "Eu montei o layout, mas a execução segura não foi autorizada.",
                "calma", 1,
            )
        return True

    def _caminho(self, nome: str, pasta: str) -> str:
        if pasta:
            return os.path.join(self.resolver_caminho(pasta), nome)
        return self.resolver_caminho(nome)

    @staticmethod
    def _hash_arquivo(caminho: str) -> str:
        try:
            texto = Path(caminho).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return ""
        return _hash_texto(texto)

    def _aprender(self, plano: Mapping[str, Any], decisao: str) -> None:
        if callable(self.registrar_aprendizado):
            try:
                self.registrar_aprendizado(self.quadro.plano_publico(plano), decisao)
            except Exception:
                pass

    def _registrar_decisao(
        self, decisao: str, motivo: str, *, categoria: str = "clipboard_para_arquivo",
    ) -> None:
        if callable(self.registrar_decisao):
            try:
                self.registrar_decisao(
                    "orquestracao_cooperativa", decisao, (motivo,),
                    categoria=str(categoria or "plano_cooperativo")[:80],
                )
            except Exception:
                pass

    def _consumir_referencia_plano(self, plano: Mapping[str, Any]) -> None:
        metadados = dict(plano.get("metadados") or {})
        self.quadro.consumir_referencia(str(metadados.get("referencia_conteudo") or ""))

    def _executar_plano(self, plano: Mapping[str, Any], texto: str, *, sobrescrever: bool) -> bool:
        plano_id = str(plano.get("id") or "")
        metadados = dict(plano.get("metadados") or {})
        referencia = str(metadados.get("referencia_conteudo") or "")
        hash_conteudo = str(metadados.get("hash_conteudo") or "")
        nome = str(metadados.get("nome") or "")
        pasta = str(metadados.get("pasta") or "")
        def executar_arquivo(
            _etapa: Mapping[str, Any], _plano_atual: Mapping[str, Any],
        ) -> Mapping[str, Any]:
            resolvida = self.quadro.resolver_referencia(
                referencia, hash_esperado=hash_conteudo,
            )
            if not resolvida.get("ok"):
                return {
                    "ok": False,
                    "confirmado": False,
                    "status": str(resolvida.get("status") or "referencia_expirada"),
                    "estado_plano": "expirado",
                }
            resultado = {
                "intent": "CREATE_FILE",
                "params": {
                    "alvo": nome,
                    "pasta": pasta,
                    "tipo_arquivo": "texto",
                    "conteudo_ref": referencia,
                    "conteudo_hash": hash_conteudo,
                    "sobrescrever_confirmado": bool(sobrescrever),
                    "plano_cooperativo_id": plano_id,
                },
            }
            tratado = bool(self.executar_intencao(resultado, texto))
            estado = dict(self.estado_getter() or {})
            status = str(estado.get("ultima_acao_status") or "").strip().casefold()
            confirmou = bool(
                tratado
                and str(estado.get("ultima_acao_intent") or "").upper() == "CREATE_FILE"
                and estado.get("ultima_acao_confirmada") is True
                and status == "arquivo_criado"
            )
            return {
                "ok": confirmou,
                "confirmado": confirmou,
                "status": status or "nao_confirmado",
                "evidencia": "arquivo_existente_e_hash_confirmado" if confirmou else "",
            }

        resumo = self.executor_plano.executar(
            plano_id,
            {"criar_arquivo": executar_arquivo},
            contexto_execucao={"texto": texto, "confirmado": bool(sobrescrever)},
        )
        plano_final = self.quadro.obter_plano(plano_id) or plano
        if resumo.get("ok"):
            self._consumir_referencia_plano(plano_final)
        else:
            status = str(resumo.get("status") or "nao_confirmado")
            if resumo.get("estado") == "expirado":
                self._consumir_referencia_plano(plano_final)
                self.falar(
                    "A referência temporária ao texto expirou. Copie novamente antes de eu criar o arquivo.",
                    "calma", 1,
                )
        return True

    def _processar_pendencia(self, texto: str) -> bool:
        runtime = self.pendencia_runtime
        obter = getattr(runtime, "obter", None)
        resolver = getattr(runtime, "resolver", None)
        concluir = getattr(runtime, "concluir", None)
        pendencia = dict(obter() or {}) if callable(obter) else {}
        if str(pendencia.get("origem") or "") != self.ORIGEM_PENDENCIA:
            return False
        resolucao = dict(resolver(
            texto,
            classificar_contextual=self.classificar_confirmacao_contextual,
        ) or {}) if callable(resolver) else {}
        if not resolucao.get("tratado"):
            return False
        status = str(resolucao.get("status") or "")
        if status in {"em_processamento", "concorrente"}:
            return True
        pendencia = dict(resolucao.get("pendencia") or pendencia)
        pendencia_id = str(pendencia.get("id") or "")
        plano_id = str((pendencia.get("metadados") or {}).get("plano_id") or "")
        plano = self.quadro.obter_plano(plano_id)
        if status == "recusar":
            if callable(concluir):
                concluir(pendencia_id, "recusada")
            if plano:
                plano = self.quadro.solicitar_cancelamento(
                    plano_id, "sobrescrita_recusada",
                ) or plano
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    plano, decisao="recusado", motivo="sobrescrita_recusada",
                )
            self.falar("Tudo bem. Mantive o arquivo existente exatamente como estava.", "calma", 1)
            return True
        if not plano:
            if callable(concluir):
                concluir(pendencia_id, "plano_expirado")
            self.falar("Esse plano expirou. Faça o pedido novamente para eu usar o conteúdo atual.", "calma", 1)
            return True
        metadados = dict(plano.get("metadados") or {})
        snapshot = dict(self.clipboard_snapshot() or {})
        if str(snapshot.get("assinatura") or "") != str(metadados.get("hash_conteudo") or ""):
            if callable(concluir):
                concluir(pendencia_id, "conteudo_alterado")
            plano_cancelado = self.quadro.atualizar_plano(
                plano_id, "cancelado", resultado={"status": "conteudo_alterado"},
            ) or plano
            self._consumir_referencia_plano(plano)
            self.governanca.finalizar(
                plano_cancelado, decisao="cancelado", motivo="conteudo_alterado",
            )
            self.falar("Você copiou outra coisa depois da confirmação. Não sobrescrevi o arquivo.", "calma", 1)
            return True
        if callable(concluir):
            concluir(pendencia_id, "autorizada")
        self.quadro.atualizar_plano(plano_id, "autorizado")
        return self._executar_plano(plano, texto, sobrescrever=True)

    def processar(self, texto: str) -> bool:
        if self._processar_pendencia(texto):
            return True
        if callable(self.detectar_visao_jogo):
            try:
                pedido_visual = self.detectar_visao_jogo(texto)
            except Exception:
                pedido_visual = None
            if (
                isinstance(pedido_visual, Mapping)
                and str(pedido_visual.get("intent") or "").upper() == "GAME_VISION"
                and str((pedido_visual.get("params") or {}).get("tipo") or "") == "avaliacao_item"
            ):
                return self._processar_analise_item_jogo(pedido_visual, texto)
        intencao = self.detectar(texto)
        if not intencao:
            return False
        if str(intencao.get("tipo") or "") == "organizacao_desktop_inteligente":
            return self._processar_organizacao_desktop(intencao, texto)

        snapshot = dict(self.clipboard_snapshot() or {})
        if snapshot.get("status") != "ok":
            self.falar("Não encontrei um texto disponível na área de transferência.", "calma", 1)
            return True
        if snapshot.get("bloqueado") or str(snapshot.get("tipo") or "") == "sensivel":
            self.falar("O conteúdo copiado parece sensível. Não vou colocá-lo em um arquivo.", "preocupada", 2)
            self._registrar_decisao("bloqueado", "conteúdo sensível")
            return True
        conteudo = str(self.clipboard_getter() or "")
        assinatura = str(snapshot.get("assinatura") or "")
        if not conteudo or not assinatura or _hash_texto(conteudo) != assinatura:
            self.falar("O conteúdo copiado mudou enquanto eu montava o plano. Copie novamente e repita o pedido.", "calma", 1)
            return True

        referencia = self.quadro.guardar_referencia(
            conteudo, tipo="texto_clipboard", ttl_s=600.0,
        )
        evento = self.quadro.publicar_evento(
            origem="area_transferencia",
            tipo="conteudo_copiado_solicitado",
            resumo="texto copiado destinado a um arquivo local",
            confianca=float(intencao.get("confianca") or 0.0),
            relevancia=0.96,
            sensibilidade="temporaria",
            habilidades=("area_transferencia", "arquivos"),
            evidencias=("referência explícita ao conteúdo copiado", "pedido explícito para criar arquivo"),
            chave_deduplicacao=f"clipboard_arquivo:{assinatura}:{intencao['nome']}",
            referencia=str(referencia.get("token") or ""),
        )
        caminho = self._caminho(str(intencao["nome"]), str(intencao.get("pasta") or ""))
        plano = self.quadro.criar_plano(
            objetivo="salvar conteúdo copiado em arquivo de texto",
            evento_ids=(str(evento.get("id") or ""),),
            etapas=(
                {
                    "ordem": 1, "habilidade": "area_transferencia",
                    "acao": "fornecer_referencia", "estado": "confirmado",
                    "orcamento_ms": 500, "idempotente": True,
                    "evidencia_esperada": "hash_e_tamanho_da_referencia_validos",
                },
                {
                    "ordem": 2, "habilidade": "arquivos", "acao": "criar_arquivo",
                    "intent": "CREATE_FILE",
                    "depende_de": [1], "estado": "proposto", "orcamento_ms": 5_000,
                    "idempotente": True, "politica_falha": "interromper",
                    "evidencia_esperada": "arquivo_existente_e_hash_confirmado",
                },
            ),
            confianca=float(intencao.get("confianca") or 0.0),
            risco="baixo",
            autorizacao="explicita_no_pedido",
            orcamento_total_ms=8_000,
            politica_falha_parcial="interromper",
            metadados={
                "fluxo": "clipboard_para_arquivo",
                "referencia_conteudo": str(referencia.get("token") or ""),
                "hash_conteudo": assinatura,
                "tamanho_conteudo": len(conteudo),
                "nome": str(intencao["nome"]),
                "pasta": str(intencao.get("pasta") or ""),
                "caminho": caminho,
            },
        )
        self.log(
            "🤝 [COOPERAÇÃO] plano criado | fluxo=clipboard_para_arquivo "
            f"id={plano.get('id')} tamanho={len(conteudo)}"
        )

        if os.path.exists(caminho):
            if self._hash_arquivo(caminho) == assinatura:
                plano = self.quadro.atualizar_plano(
                    str(plano.get("id") or ""), "confirmado",
                    resultado={"status": "arquivo_ja_contem_conteudo", "confirmado": True},
                ) or plano
                self.quadro.atualizar_etapa(
                    str(plano.get("id") or ""), "2", "confirmado",
                    resultado={
                        "status": "arquivo_ja_contem_conteudo", "confirmado": True,
                        "evidencia": "arquivo_existente_e_hash_confirmado",
                    },
                )
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    self.quadro.obter_plano(str(plano.get("id") or "")) or plano,
                    decisao="aceito", motivo="arquivo_ja_contem_conteudo",
                )
                self.falar(f"{intencao['nome']} já contém exatamente o texto copiado. Não precisei alterar nada.", "calma", 1)
                return True
            atual = getattr(self.pendencia_runtime, "obter", lambda: None)()
            if atual:
                plano = self.quadro.atualizar_plano(
                    str(plano.get("id") or ""), "cancelado",
                    resultado={"status": "outra_confirmacao_ativa"},
                ) or plano
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    plano, decisao="cancelado", motivo="outra_confirmacao_ativa",
                )
                self.falar("Esse arquivo já existe, mas há outra confirmação esperando. Não alterei nada.", "calma", 1)
                return True
            pergunta = f"{intencao['nome']} já existe. Quer substituir pelo texto que está copiado?"
            pendencia = self.pendencia_runtime.registrar(
                origem=self.ORIGEM_PENDENCIA,
                acao=self.ACAO_SOBRESCREVER,
                pergunta=pergunta,
                referencia=str(plano.get("id") or ""),
                metadados={"plano_id": str(plano.get("id") or ""), "arquivo": str(intencao["nome"])},
                ttl_s=300.0,
            ) if self.pendencia_runtime is not None else None
            if pendencia:
                self.quadro.atualizar_plano(str(plano.get("id") or ""), "aguardando_autorizacao")
                self.falar(pergunta, "calma", 1)
            else:
                plano = self.quadro.atualizar_plano(
                    str(plano.get("id") or ""), "cancelado",
                    resultado={"status": "confirmacao_indisponivel"},
                ) or plano
                self._consumir_referencia_plano(plano)
                self.governanca.finalizar(
                    plano, decisao="cancelado", motivo="confirmacao_indisponivel",
                )
                self.falar("O arquivo já existe e eu não consegui abrir uma confirmação segura. Não alterei nada.", "calma", 1)
            return True

        self.quadro.atualizar_plano(str(plano.get("id") or ""), "autorizado")
        return self._executar_plano(plano, texto, sobrescrever=False)

    def resolver_referencia(self, token: str, *, hash_esperado: str = "") -> dict[str, Any]:
        return self.quadro.resolver_referencia(token, hash_esperado=hash_esperado)

    def diagnostico(self) -> dict[str, Any]:
        return self.quadro.diagnostico()


def criar_quadro_cooperacao_runtime(**kwargs: Any) -> QuadroCooperacaoRuntime:
    return QuadroCooperacaoRuntime(**kwargs)


def criar_executor_plano_cooperativo_runtime(**kwargs: Any) -> ExecutorPlanoCooperativoRuntime:
    return ExecutorPlanoCooperativoRuntime(**kwargs)


def criar_orquestrador_cooperativo_runtime(**kwargs: Any) -> OrquestradorCooperativoRuntime:
    return OrquestradorCooperativoRuntime(**kwargs)
