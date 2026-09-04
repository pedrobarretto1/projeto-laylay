"""Buffer append-only de evidências para evolução controlada do especialista."""

from __future__ import annotations

import json
import re
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


DECISOES_REVISAO_CORRECAO = frozenset({"aprovada", "rejeitada"})


def _normalizar_texto(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9_ -]+", " ", base)).strip()


def _params(valor: Any) -> dict[str, Any]:
    return dict(valor or {}) if isinstance(valor, Mapping) else {}


class BufferExperienciasNeurais:
    """Registra sinais sem promover silêncio ou predição própria a ground truth."""

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self._lock = threading.RLock()

    def _gravar(self, experiencia: dict[str, Any]) -> dict[str, Any]:
        registro = dict(experiencia)
        registro.setdefault("id", uuid4().hex)
        registro.setdefault("ts", time.time())
        with self._lock:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            with self.caminho.open("a", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")
        return registro

    def registrar_resultado(
        self,
        *,
        texto: str,
        previsao: Mapping[str, Any] | None,
        resultado: Mapping[str, Any] | None,
        executou: bool | None,
        confirmado: bool | None,
        origem: str,
    ) -> dict[str, Any]:
        observado = dict(resultado or {})
        predicao = dict(previsao or {})
        receipt_verificado = bool(executou is True and confirmado is True)
        return self._gravar({
            "tipo": "resultado_comando",
            "text": str(texto or "").strip()[:500],
            "text_normalized": _normalizar_texto(texto),
            "intent_predita": str(predicao.get("intent") or "").upper(),
            "params_preditos": _params(predicao.get("params")),
            "intent_observada": str(observado.get("intent") or "").upper(),
            "params_observados": _params(observado.get("params")),
            "status": str(observado.get("status") or "")[:120],
            "executou": executou,
            "confirmado": confirmado,
            "origem": str(origem or "")[:100],
            "evidencia": (
                "EXPECTED_RECEIPT_VERIFIED" if receipt_verificado
                else "EXECUTION_RESULT_UNVERIFIED"
            ),
            "label_confidence": 0.45 if receipt_verificado else 0.15,
            "apto_treino": False,
            "requer_revisao": True,
            "predicao_propria_vira_label": False,
        })

    def registrar_correcao(
        self,
        *,
        texto_original: str,
        intent_errada: str,
        intent_correta: str,
        params_corretos: Mapping[str, Any] | None,
        texto_correcao: str,
        confirmada_por_execucao: bool,
    ) -> dict[str, Any]:
        forte = bool(confirmada_por_execucao and str(intent_correta or "").strip())
        return self._gravar({
            "tipo": "correcao_interpretacao",
            "text": str(texto_original or "").strip()[:500],
            "text_normalized": _normalizar_texto(texto_original),
            "texto_correcao": str(texto_correcao or "").strip()[:500],
            "intent_errada": str(intent_errada or "").strip().upper(),
            "intent_correta": str(intent_correta or "").strip().upper(),
            "params_corretos": _params(params_corretos),
            "evidencia": "EXPLICIT_CORRECTION",
            "label_confidence": 1.0 if forte else 0.8,
            "apto_treino": forte,
            "requer_revisao": not forte,
            "predicao_propria_vira_label": False,
        })

    def listar(self, *, apenas_aptas: bool = False) -> list[dict[str, Any]]:
        if not self.caminho.exists():
            return []
        registros: list[dict[str, Any]] = []
        with self._lock:
            for linha in self.caminho.read_text(encoding="utf-8").splitlines():
                try:
                    item = json.loads(linha)
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                if not isinstance(item, dict):
                    continue
                if apenas_aptas and not item.get("apto_treino"):
                    continue
                registros.append(item)
        return registros


class RegistroRevisoesCorrecoesNeurais:
    """Ledger append-only que separa evidência coletada de autorização para treino."""

    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho)
        self._lock = threading.RLock()

    def registrar_decisao(
        self,
        *,
        correcao_id: str,
        decisao: str,
        motivo: str = "",
        origem: str = "revisao_manual",
    ) -> dict[str, Any]:
        identificador = str(correcao_id or "").strip()
        decisao_normalizada = str(decisao or "").strip().casefold()
        if not identificador:
            raise ValueError("correcao_id obrigatório")
        if decisao_normalizada not in DECISOES_REVISAO_CORRECAO:
            raise ValueError(f"decisão de revisão inválida: {decisao_normalizada}")
        registro = {
            "id": uuid4().hex,
            "ts": time.time(),
            "correcao_id": identificador[:100],
            "decisao": decisao_normalizada,
            "motivo": str(motivo or "").strip()[:500],
            "origem": str(origem or "revisao_manual").strip()[:100],
        }
        with self._lock:
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            with self.caminho.open("a", encoding="utf-8", newline="\n") as arquivo:
                arquivo.write(
                    json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n"
                )
        return registro

    def decisoes_atuais(self) -> dict[str, str]:
        """Retorna a última decisão válida por correção; linha inválida não autoriza."""
        if not self.caminho.exists():
            return {}
        decisoes: dict[str, str] = {}
        with self._lock:
            linhas = self.caminho.read_text(encoding="utf-8").splitlines()
        for linha in linhas:
            try:
                item = json.loads(linha)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            if not isinstance(item, Mapping):
                continue
            identificador = str(item.get("correcao_id") or "").strip()
            decisao = str(item.get("decisao") or "").strip().casefold()
            if identificador and decisao in DECISOES_REVISAO_CORRECAO:
                decisoes[identificador] = decisao
        return decisoes

    def classificar(
        self,
        experiencias: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        decisoes = self.decisoes_atuais()
        resultado: dict[str, list[dict[str, Any]]] = {
            "aprovadas": [],
            "rejeitadas": [],
            "pendentes": [],
        }
        for experiencia in experiencias:
            identificador = str(experiencia.get("id") or "").strip()
            decisao = decisoes.get(identificador, "")
            if decisao == "aprovada":
                resultado["aprovadas"].append(experiencia)
            elif decisao == "rejeitada":
                resultado["rejeitadas"].append(experiencia)
            else:
                resultado["pendentes"].append(experiencia)
        return resultado
