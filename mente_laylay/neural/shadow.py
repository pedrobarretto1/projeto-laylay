"""Observabilidade persistente do especialista neural em modo sombra."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


_CHAVES_TOTAIS = (
    "turnos",
    "concordancias_comando",
    "divergencias_comando",
    "falsos_comandos_neurais",
    "comandos_perdidos_neurais",
    "segmentos_comparaveis",
    "concordancias_comando_segmento",
    "divergencias_comando_segmento",
    "falsos_comandos_neurais_segmento",
    "comandos_perdidos_neurais_segmento",
    "receipts_observados",
    "receipts_confirmados",
    "concordancias_intent",
    "divergencias_intent",
    "concordancias_acao",
    "divergencias_acao",
)


def _texto_limpo(valor: Any, limite: int = 500) -> str:
    return " ".join(str(valor or "").strip().split())[:limite]


def _hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.casefold().encode("utf-8")).hexdigest()


def _acao(dados: Mapping[str, Any] | None) -> str:
    origem = dict(dados or {})
    params = origem.get("params")
    if not isinstance(params, Mapping):
        return ""
    return str(params.get("acao") or "").strip().casefold()


class RelatorioShadowNeural:
    """Registra comparações sem convertê-las em autorização ou ground truth."""

    def __init__(self, pasta_estado: str | Path) -> None:
        pasta = Path(pasta_estado)
        self.caminho_eventos = pasta / "shadow_eventos.jsonl"
        self.caminho_relatorio = pasta / "shadow_relatorio.json"
        self._lock = threading.RLock()

    @staticmethod
    def _resumo_vazio() -> dict[str, Any]:
        return {
            "versao": 1,
            "atualizado_em": 0.0,
            "modelo_ultimo": "",
            "totais": {chave: 0 for chave in _CHAVES_TOTAIS},
            "taxas": {},
            "por_intent": {},
            "divergencias_recentes": [],
            "contrato": {
                "somente_observacao": True,
                "autoriza_execucao": False,
                "predicao_propria_vira_label": False,
            },
        }

    def _ler_resumo(self) -> dict[str, Any]:
        resumo = self._resumo_vazio()
        if not self.caminho_relatorio.exists():
            return resumo
        try:
            bruto = json.loads(self.caminho_relatorio.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return resumo
        if not isinstance(bruto, Mapping):
            return resumo
        resumo.update({
            "atualizado_em": float(bruto.get("atualizado_em") or 0.0),
            "modelo_ultimo": str(bruto.get("modelo_ultimo") or "")[:100],
        })
        totais = dict(bruto.get("totais") or {})
        resumo["totais"].update({
            chave: max(0, int(totais.get(chave) or 0)) for chave in _CHAVES_TOTAIS
        })
        if isinstance(bruto.get("por_intent"), Mapping):
            resumo["por_intent"] = {
                str(chave)[:100]: dict(valor)
                for chave, valor in bruto["por_intent"].items()
                if isinstance(valor, Mapping)
            }
        if isinstance(bruto.get("divergencias_recentes"), list):
            resumo["divergencias_recentes"] = [
                dict(item)
                for item in bruto["divergencias_recentes"][-25:]
                if isinstance(item, Mapping)
            ]
        return resumo

    def _gravar(self, evento: dict[str, Any], atualizar_resumo) -> dict[str, Any]:
        registro = dict(evento)
        registro.setdefault("id", uuid4().hex)
        registro.setdefault("ts", time.time())
        registro.update({
            "somente_observacao": True,
            "autoriza_execucao": False,
            "apto_treino": False,
            "predicao_propria_vira_label": False,
        })
        with self._lock:
            self.caminho_eventos.parent.mkdir(parents=True, exist_ok=True)
            with self.caminho_eventos.open("a", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")
            resumo = self._ler_resumo()
            atualizar_resumo(resumo, registro)
            self._atualizar_taxas(resumo)
            resumo["atualizado_em"] = float(registro["ts"])
            resumo["modelo_ultimo"] = str(registro.get("modelo") or "")[:100]
            temporario = self.caminho_relatorio.with_suffix(".json.tmp")
            temporario.write_text(
                json.dumps(resumo, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            temporario.replace(self.caminho_relatorio)
        return registro

    @staticmethod
    def _atualizar_taxas(resumo: dict[str, Any]) -> None:
        totais = dict(resumo.get("totais") or {})
        turnos = int(totais.get("turnos") or 0)
        receipts = int(totais.get("receipts_confirmados") or 0)
        acoes = int(totais.get("concordancias_acao") or 0) + int(
            totais.get("divergencias_acao") or 0
        )
        segmentos = int(totais.get("segmentos_comparaveis") or 0)

        def taxa(numerador: str, denominador: int) -> float:
            if denominador <= 0:
                return 0.0
            return round(float(totais.get(numerador) or 0) / denominador, 6)

        resumo["taxas"] = {
            "concordancia_comando": taxa("concordancias_comando", turnos),
            "divergencia_comando": taxa("divergencias_comando", turnos),
            "falso_comando_neural": taxa("falsos_comandos_neurais", turnos),
            "comando_perdido_neural": taxa("comandos_perdidos_neurais", turnos),
            "concordancia_comando_segmento": taxa(
                "concordancias_comando_segmento", segmentos
            ),
            "divergencia_comando_segmento": taxa(
                "divergencias_comando_segmento", segmentos
            ),
            "falso_comando_neural_segmento": taxa(
                "falsos_comandos_neurais_segmento", segmentos
            ),
            "comando_perdido_neural_segmento": taxa(
                "comandos_perdidos_neurais_segmento", segmentos
            ),
            "concordancia_intent_confirmado": taxa(
                "concordancias_intent", receipts
            ),
            "divergencia_intent_confirmado": taxa(
                "divergencias_intent", receipts
            ),
            "concordancia_acao_comparavel": taxa("concordancias_acao", acoes),
            "divergencia_acao_comparavel": taxa("divergencias_acao", acoes),
        }

    @staticmethod
    def _incrementar_intent(
        resumo: dict[str, Any], intent: str, chave: str,
    ) -> None:
        nome = intent or "SEM_INTENT"
        por_intent = resumo.setdefault("por_intent", {})
        item = por_intent.setdefault(nome, {})
        item[chave] = int(item.get(chave) or 0) + 1

    @staticmethod
    def _anexar_divergencia(resumo: dict[str, Any], registro: dict[str, Any]) -> None:
        recentes = list(resumo.get("divergencias_recentes") or [])
        recentes.append({
            "id": registro.get("id"),
            "ts": registro.get("ts"),
            "tipo": registro.get("tipo"),
            "texto": registro.get("texto", ""),
            "texto_hash": registro.get("texto_hash"),
            "modelo": registro.get("modelo"),
            "neural": dict(registro.get("neural") or {}),
            "canonico": dict(registro.get("canonico") or {}),
            "comparacao": dict(registro.get("comparacao") or {}),
        })
        resumo["divergencias_recentes"] = recentes[-25:]

    def registrar_turno(
        self,
        *,
        texto: str,
        previsao: Mapping[str, Any],
        turno: Mapping[str, Any],
    ) -> dict[str, Any]:
        fala = _texto_limpo(texto)
        neural = dict(previsao or {})
        canonico = dict(turno or {})
        veto = bool(canonico.get("veto_execucao_operacional"))
        comando_canonico = bool(canonico.get("autoriza_execucao")) and not veto
        ood_calibrated = bool(neural.get("ood_calibrated", True))
        comando_neural = bool(
            neural.get("is_command")
            and not neural.get("negated")
            and not (neural.get("ood") and ood_calibrated)
        )
        falso_comando = bool(comando_neural and not comando_canonico)
        comando_perdido = bool(comando_canonico and not comando_neural)
        divergiu = falso_comando or comando_perdido
        previsoes_segmentos = [
            dict(item)
            for item in list(neural.get("previsoes_segmentos") or [])
            if isinstance(item, Mapping)
        ]
        segmentos_canonicos = [
            dict(item)
            for item in list(canonico.get("segmentos") or [])
            if isinstance(item, Mapping)
        ]

        def indice_segmento(item: Mapping[str, Any], padrao: int) -> int:
            try:
                return int(item.get("indice", padrao))
            except (TypeError, ValueError):
                return padrao

        canonicos_por_indice = {
            indice_segmento(item, posicao): item
            for posicao, item in enumerate(segmentos_canonicos)
        }
        comparacoes_segmentos = []
        segmentos_neurais_resumo = []
        segmentos_canonicos_resumo = []
        for posicao, item in enumerate(segmentos_canonicos):
            indice = indice_segmento(item, posicao)
            segmentos_canonicos_resumo.append({
                "indice": indice,
                "texto_hash": _hash_texto(_texto_limpo(item.get("texto"))),
                "modalidade": str(item.get("modalidade") or "")[:100],
                "autoriza_execucao": bool(item.get("autoriza_execucao")),
                "veto_execucao_operacional": bool(
                    item.get("veto_execucao_operacional")
                ),
            })
        for posicao, item in enumerate(previsoes_segmentos):
            indice = indice_segmento(item, posicao)
            texto_hash = str(item.get("texto_hash") or "")
            canonico_segmento = canonicos_por_indice.get(indice)
            hash_canonico = (
                _hash_texto(_texto_limpo(canonico_segmento.get("texto")))
                if isinstance(canonico_segmento, Mapping)
                else ""
            )
            comparavel = bool(
                canonico_segmento is not None
                and texto_hash
                and texto_hash == hash_canonico
            )
            comando_segmento_neural = bool(
                item.get("is_command")
                and not item.get("negated")
                and not (
                    item.get("ood")
                    and item.get("ood_calibrated", True)
                )
            )
            comando_segmento_canonico = bool(
                comparavel
                and canonico_segmento.get("autoriza_execucao")
                and not canonico_segmento.get("veto_execucao_operacional")
            )
            falso_segmento = bool(
                comparavel
                and comando_segmento_neural
                and not comando_segmento_canonico
            )
            perdido_segmento = bool(
                comparavel
                and comando_segmento_canonico
                and not comando_segmento_neural
            )
            divergencia_segmento = falso_segmento or perdido_segmento
            comparacoes_segmentos.append({
                "indice": indice,
                "comparavel": comparavel,
                "status": (
                    "evidencia_insuficiente"
                    if not comparavel
                    else "falso_comando_neural"
                    if falso_segmento
                    else "comando_perdido_neural"
                    if perdido_segmento
                    else "concordancia_comando"
                ),
                "falso_comando_neural": falso_segmento,
                "comando_perdido_neural": perdido_segmento,
                "comando_neural_executavel": comando_segmento_neural,
                "comando_canonico_autorizado": comando_segmento_canonico,
            })
            segmentos_neurais_resumo.append({
                "indice": indice,
                "texto_hash": texto_hash,
                "intent": str(item.get("intent") or "").upper(),
                "acao": _acao(item),
                "is_command": bool(item.get("is_command")),
                "negated": bool(item.get("negated")),
                "ood": bool(item.get("ood")),
                "ood_calibrated": bool(item.get("ood_calibrated", True)),
                "confidence": dict(item.get("confidence") or {}),
                "latency_ms": float(item.get("latency_ms") or 0.0),
                "autoriza_execucao": False,
            })
        segmentos_comparaveis = sum(
            1 for item in comparacoes_segmentos if item["comparavel"]
        )
        falsos_segmentos = sum(
            1 for item in comparacoes_segmentos if item["falso_comando_neural"]
        )
        perdidos_segmentos = sum(
            1 for item in comparacoes_segmentos if item["comando_perdido_neural"]
        )
        divergencias_segmentos = falsos_segmentos + perdidos_segmentos
        concordancias_segmentos = segmentos_comparaveis - divergencias_segmentos
        status = (
            "falso_comando_neural"
            if falso_comando
            else "comando_perdido_neural"
            if comando_perdido
            else "concordancia_comando"
        )
        comparacao = {
            "status": status,
            "divergiu_comando": divergiu,
            "falso_comando_neural": falso_comando,
            "comando_perdido_neural": comando_perdido,
            "comando_neural_executavel": comando_neural,
            "comando_canonico_autorizado": comando_canonico,
            "segmentos_total": len(previsoes_segmentos),
            "segmentos_comparaveis": segmentos_comparaveis,
            "concordancias_comando_segmento": concordancias_segmentos,
            "divergencias_comando_segmento": divergencias_segmentos,
            "falsos_comandos_neurais_segmento": falsos_segmentos,
            "comandos_perdidos_neurais_segmento": perdidos_segmentos,
            "segmentos": comparacoes_segmentos,
        }
        evento = {
            "tipo": "comparacao_turno",
            "modelo": str(neural.get("modelo") or "")[:100],
            "texto_hash": str(neural.get("texto_hash") or _hash_texto(fala)),
            "neural": {
                "intent": str(neural.get("intent") or "").upper(),
                "acao": _acao(neural),
                "is_command": bool(neural.get("is_command")),
                "negated": bool(neural.get("negated")),
                "ood": bool(neural.get("ood")),
                "ood_calibrated": ood_calibrated,
                "confidence": dict(neural.get("confidence") or {}),
                "latency_ms": float(neural.get("latency_ms") or 0.0),
                "route": str(neural.get("route") or ""),
                "multi_segmento": bool(neural.get("multi_segmento")),
                "segmentos": segmentos_neurais_resumo,
            },
            "canonico": {
                "modalidade": str(
                    canonico.get("modalidade_geral")
                    or canonico.get("modalidade")
                    or ""
                )[:100],
                "autoriza_execucao": comando_canonico,
                "veto_execucao_operacional": veto,
                "origem_veto": str(
                    canonico.get("origem_veto_execucao_operacional") or ""
                )[:120],
                "operacao_explicita": str(canonico.get("operacao_explicita") or "")[:120],
                "requer_esclarecimento": bool(canonico.get("requer_esclarecimento")),
                "segmentos": segmentos_canonicos_resumo,
            },
            "comparacao": comparacao,
        }
        if divergiu or divergencias_segmentos:
            evento["texto"] = fala

        def atualizar(resumo: dict[str, Any], registro: dict[str, Any]) -> None:
            totais = resumo["totais"]
            totais["turnos"] += 1
            totais["segmentos_comparaveis"] += segmentos_comparaveis
            totais["concordancias_comando_segmento"] += concordancias_segmentos
            totais["divergencias_comando_segmento"] += divergencias_segmentos
            totais["falsos_comandos_neurais_segmento"] += falsos_segmentos
            totais["comandos_perdidos_neurais_segmento"] += perdidos_segmentos
            intent = str(registro["neural"].get("intent") or "")
            self._incrementar_intent(resumo, intent, "turnos")
            if divergiu:
                totais["divergencias_comando"] += 1
                if falso_comando:
                    totais["falsos_comandos_neurais"] += 1
                if comando_perdido:
                    totais["comandos_perdidos_neurais"] += 1
                self._incrementar_intent(resumo, intent, "divergencias_comando")
            else:
                totais["concordancias_comando"] += 1
                self._incrementar_intent(resumo, intent, "concordancias_comando")
            if divergiu or divergencias_segmentos:
                self._anexar_divergencia(resumo, registro)

        self._gravar(evento, atualizar)
        return comparacao

    def registrar_receipt(
        self,
        *,
        texto: str,
        previsao: Mapping[str, Any],
        resultado: Mapping[str, Any],
        executou: bool | None,
        confirmado: bool | None,
    ) -> dict[str, Any]:
        fala = _texto_limpo(texto)
        neural = dict(previsao or {})
        observado = dict(resultado or {})
        receipt_confirmado = bool(executou is True and confirmado is True)
        intent_neural = str(neural.get("intent") or "").strip().upper()
        intent_observada = str(observado.get("intent") or "").strip().upper()
        acao_neural = _acao(neural)
        acao_observada = _acao(observado)
        receipt_comparavel = bool(neural.get("receipt_comparavel", True))
        intent_comparavel = bool(receipt_confirmado and receipt_comparavel)
        intent_igual = bool(
            intent_comparavel and intent_neural == intent_observada
        )
        # Ausência de ação em qualquer lado significa evidência insuficiente,
        # não divergência. Intent e ação são contratos independentes.
        acao_comparavel = bool(
            receipt_confirmado
            and receipt_comparavel
            and acao_neural
            and acao_observada
        )
        acao_igual = bool(acao_comparavel and acao_neural == acao_observada)
        divergiu = bool(
            intent_comparavel
            and (not intent_igual or (acao_comparavel and not acao_igual))
        )
        comparacao = {
            "status": (
                "receipt_nao_confirmado"
                if not receipt_confirmado
                else "receipt_multi_segmento_nao_correlacionado"
                if not receipt_comparavel
                else "divergencia_receipt"
                if divergiu
                else "concordancia_receipt"
            ),
            "receipt_confirmado": receipt_confirmado,
            "intent_comparavel": intent_comparavel,
            "intent_igual": intent_igual,
            "acao_comparavel": acao_comparavel,
            "acao_igual": acao_igual,
            "divergiu_receipt": divergiu,
        }
        evento = {
            "tipo": "comparacao_receipt",
            "modelo": str(neural.get("modelo") or "")[:100],
            "texto_hash": str(neural.get("texto_hash") or _hash_texto(fala)),
            "neural": {
                "intent": intent_neural,
                "acao": acao_neural,
                "multi_segmento": bool(neural.get("multi_segmento")),
                "receipt_comparavel": receipt_comparavel,
            },
            "canonico": {
                "intent": intent_observada,
                "acao": acao_observada,
                "status": str(observado.get("status") or "")[:120],
                "executou": executou,
                "confirmado": confirmado,
            },
            "comparacao": comparacao,
        }
        if divergiu:
            evento["texto"] = fala

        def atualizar(resumo: dict[str, Any], registro: dict[str, Any]) -> None:
            totais = resumo["totais"]
            totais["receipts_observados"] += 1
            self._incrementar_intent(resumo, intent_neural, "receipts_observados")
            if not receipt_confirmado:
                return
            totais["receipts_confirmados"] += 1
            self._incrementar_intent(resumo, intent_neural, "receipts_confirmados")
            if not intent_comparavel:
                return
            totais[
                "concordancias_intent" if intent_igual else "divergencias_intent"
            ] += 1
            self._incrementar_intent(
                resumo,
                intent_neural,
                "concordancias_intent" if intent_igual else "divergencias_intent",
            )
            if acao_comparavel:
                totais[
                    "concordancias_acao" if acao_igual else "divergencias_acao"
                ] += 1
            if divergiu:
                self._anexar_divergencia(resumo, registro)

        self._gravar(evento, atualizar)
        return comparacao
