"""Estado compartilhado da percepção viva de sistema e navegador."""

from __future__ import annotations

from typing import Any, Dict, List


def estado_percepcao_inicial() -> Dict[str, Any]:
    return {
        "contexto_web": {
            "site": "",
            "termo_busca": "",
            "aba_id": 0,
        },
        "logs_navegador": [],
        "ultimo_open_site": {
            "ts": 0.0,
            "topic": "",
            "url": "",
        },
        "contexto_sistema": {
            "exe": "",
            "title": "",
            "assunto": "",
        },
        "aba_ativa": {
            "titulo": "Nenhuma aba aberta",
            "url": "Nenhuma URL",
        },
    }


def atualizar_estado_percepcao(estado_atual: Dict[str, Any] | None, **campos: Any) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    for chave, valor in campos.items():
        estado[chave] = valor
    if not isinstance(estado.get("contexto_web"), dict):
        estado["contexto_web"] = {"site": "", "termo_busca": "", "aba_id": 0}
    if not isinstance(estado.get("logs_navegador"), list):
        estado["logs_navegador"] = []
    if not isinstance(estado.get("ultimo_open_site"), dict):
        estado["ultimo_open_site"] = {"ts": 0.0, "topic": "", "url": ""}
    if not isinstance(estado.get("contexto_sistema"), dict):
        estado["contexto_sistema"] = {"exe": "", "title": "", "assunto": ""}
    if not isinstance(estado.get("aba_ativa"), dict):
        estado["aba_ativa"] = {"titulo": "Nenhuma aba aberta", "url": "Nenhuma URL"}
    return estado


def registrar_log_navegador(
    estado_atual: Dict[str, Any] | None,
    linha: str,
    *,
    limite: int = 5,
) -> Dict[str, Any]:
    estado = atualizar_estado_percepcao(estado_atual)
    logs: List[str] = list(estado.get("logs_navegador") or [])
    texto = str(linha or "").strip()
    if texto:
        logs.append(texto)
    if limite > 0 and len(logs) > limite:
        logs = logs[-limite:]
    estado["logs_navegador"] = logs
    return estado
