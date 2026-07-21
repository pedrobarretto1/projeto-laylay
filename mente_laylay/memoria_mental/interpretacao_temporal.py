"""Interpretação determinística de datas e recorrências em português brasileiro."""

from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Dict


_MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
_DIAS_SEMANA = {
    "segunda": 0, "terca": 1, "quarta": 2, "quinta": 3,
    "sexta": 4, "sabado": 5, "domingo": 6,
}
_NUMEROS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4,
    "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10,
    "quinze": 15, "vinte": 20, "trinta": 30,
}


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


def _numero(valor: str) -> int:
    bruto = str(valor or "").strip()
    return int(bruto) if bruto.isdigit() else int(_NUMEROS.get(bruto, 1))


def _com_horario(data: datetime, texto: str, *, padrao_hora: int = 9) -> tuple[datetime, bool]:
    match = re.search(r"\b(?:as|pelas?)\s+(\d{1,2})(?:[:h](\d{2}))?\b|\b(\d{1,2})h(?:([0-5]\d))?\b", texto)
    if not match:
        return data.replace(hour=padrao_hora, minute=0, second=0, microsecond=0), False
    hora = int(match.group(1) or match.group(3) or padrao_hora)
    minuto = int(match.group(2) or match.group(4) or 0)
    return data.replace(hour=min(max(hora, 0), 23), minute=minuto, second=0, microsecond=0), True


def proxima_ocorrencia(base_ts: float, recorrencia: Dict[str, Any], *, depois_de: float) -> float:
    """Calcula a próxima ocorrência sem depender de bibliotecas externas."""
    regra = dict(recorrencia or {})
    frequencia = str(regra.get("frequencia") or "")
    intervalo = max(1, int(regra.get("intervalo") or 1))
    atual = datetime.fromtimestamp(float(base_ts or depois_de))
    limite = datetime.fromtimestamp(float(depois_de))
    if frequencia == "diaria":
        while atual <= limite:
            atual += timedelta(days=intervalo)
    elif frequencia == "semanal":
        dia = regra.get("dia_semana")
        if dia is not None:
            delta = (int(dia) - limite.weekday()) % 7
            if delta == 0 and atual <= limite:
                delta = 7 * intervalo
            atual = limite.replace(hour=atual.hour, minute=atual.minute, second=0, microsecond=0) + timedelta(days=delta)
        else:
            while atual <= limite:
                atual += timedelta(weeks=intervalo)
    elif frequencia == "mensal":
        while atual <= limite:
            total = atual.year * 12 + atual.month - 1 + intervalo
            ano, mes_zero = divmod(total, 12)
            dia = min(atual.day, calendar.monthrange(ano, mes_zero + 1)[1])
            atual = atual.replace(year=ano, month=mes_zero + 1, day=dia)
    elif frequencia == "anual":
        while atual <= limite:
            try:
                atual = atual.replace(year=atual.year + intervalo)
            except ValueError:
                atual = atual.replace(year=atual.year + intervalo, day=28)
    return atual.timestamp() if frequencia else 0.0


def interpretar_referencia_temporal(texto: str, *, agora: float) -> Dict[str, Any]:
    normalizado = _normalizar(texto)
    atual = datetime.fromtimestamp(float(agora))
    alvo: datetime | None = None
    origem = ""
    confianca = 0.0

    if "depois de amanha" in normalizado:
        alvo, origem, confianca = atual + timedelta(days=2), "depois_de_amanha", 0.99
    elif re.search(r"\bamanha\b", normalizado):
        alvo, origem, confianca = atual + timedelta(days=1), "amanha", 0.99
    elif re.search(r"\bhoje\b", normalizado):
        alvo, origem, confianca = atual, "hoje", 0.99
    elif "semana que vem" in normalizado or "proxima semana" in normalizado:
        alvo, origem, confianca = atual + timedelta(days=7), "semana_que_vem", 0.94

    relativo = re.search(
        r"\bdaqui (?:a )?(\d{1,3}|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|quinze|vinte|trinta) "
        r"(minutos?|horas?|dias?|semanas?|mes(?:es)?|anos?)\b",
        normalizado,
    )
    if relativo:
        quantidade = _numero(relativo.group(1))
        unidade = relativo.group(2)
        if unidade.startswith("minuto"):
            alvo = atual + timedelta(minutes=quantidade)
        elif unidade.startswith("hora"):
            alvo = atual + timedelta(hours=quantidade)
        elif unidade.startswith("dia"):
            alvo = atual + timedelta(days=quantidade)
        elif unidade.startswith("semana"):
            alvo = atual + timedelta(weeks=quantidade)
        elif unidade.startswith("mes"):
            total = atual.year * 12 + atual.month - 1 + quantidade
            ano, mes_zero = divmod(total, 12)
            alvo = atual.replace(
                year=ano, month=mes_zero + 1,
                day=min(atual.day, calendar.monthrange(ano, mes_zero + 1)[1]),
            )
        else:
            try:
                alvo = atual.replace(year=atual.year + quantidade)
            except ValueError:
                alvo = atual.replace(year=atual.year + quantidade, day=28)
        origem, confianca = "intervalo_relativo", 0.98

    numerica = re.search(r"\b(?:dia\s+)?([0-3]?\d)[/-]([01]?\d)(?:[/-](\d{2,4}))?\b", normalizado)
    if numerica:
        dia, mes = int(numerica.group(1)), int(numerica.group(2))
        ano = int(numerica.group(3) or atual.year)
        ano += 2000 if ano < 100 else 0
        try:
            alvo = atual.replace(year=ano, month=mes, day=dia)
            if not numerica.group(3) and alvo.date() < atual.date():
                alvo = alvo.replace(year=ano + 1)
            origem, confianca = "data_numerica", 0.99
        except ValueError:
            pass

    por_extenso = re.search(
        r"\b(?:dia\s+)?([0-3]?\d)\s+de\s+(" + "|".join(_MESES) + r")(?:\s+de\s+(\d{4}))?\b",
        normalizado,
    )
    if por_extenso:
        dia, mes = int(por_extenso.group(1)), _MESES[por_extenso.group(2)]
        ano = int(por_extenso.group(3) or atual.year)
        try:
            alvo = atual.replace(year=ano, month=mes, day=dia)
            if not por_extenso.group(3) and alvo.date() < atual.date():
                alvo = alvo.replace(year=ano + 1)
            origem, confianca = "data_extenso", 0.99
        except ValueError:
            pass

    dia_isolado = re.search(r"\bdia\s+([0-3]?\d)\b", normalizado)
    if dia_isolado and alvo is None:
        dia = int(dia_isolado.group(1))
        try:
            alvo = atual.replace(day=dia)
            if alvo.date() < atual.date():
                total = atual.year * 12 + atual.month
                ano, mes_zero = divmod(total, 12)
                alvo = alvo.replace(
                    year=ano, month=mes_zero + 1,
                    day=min(dia, calendar.monthrange(ano, mes_zero + 1)[1]),
                )
            origem, confianca = "dia_do_mes", 0.90
        except ValueError:
            pass

    mes_isolado = next((numero for nome, numero in _MESES.items() if re.search(rf"\b(?:em|no mes de) {nome}\b", normalizado)), None)
    if mes_isolado is not None and alvo is None:
        ano = atual.year + (1 if mes_isolado < atual.month else 0)
        alvo = atual.replace(year=ano, month=mes_isolado, day=1)
        origem, confianca = "mes_nomeado", 0.88

    if alvo is None and re.search(r"\b(?:proximo mes|mes que vem)\b", normalizado):
        total = atual.year * 12 + atual.month
        ano, mes_zero = divmod(total, 12)
        alvo = atual.replace(year=ano, month=mes_zero + 1, day=1)
        origem, confianca = "proximo_mes", 0.90

    dia_semana = next((numero for nome, numero in _DIAS_SEMANA.items() if re.search(rf"\b{nome}(?:-feira)?\b", normalizado)), None)
    if dia_semana is not None and alvo is None:
        delta = (dia_semana - atual.weekday()) % 7
        if delta == 0 or "proxima" in normalizado:
            delta += 7
        alvo, origem, confianca = atual + timedelta(days=delta), "dia_semana", 0.92

    recorrencia: Dict[str, Any] = {}
    intervalo_rec = re.search(r"\ba cada (\d{1,2}|um|uma|dois|duas|tres|quatro) (dias?|semanas?|mes(?:es)?|anos?)\b", normalizado)
    if intervalo_rec:
        unidade = intervalo_rec.group(2)
        frequencia = "diaria" if unidade.startswith("dia") else "semanal" if unidade.startswith("semana") else "mensal" if unidade.startswith("mes") else "anual"
        recorrencia = {"frequencia": frequencia, "intervalo": _numero(intervalo_rec.group(1))}
    elif re.search(r"\b(?:todo dia|todos os dias|diariamente)\b", normalizado):
        recorrencia = {"frequencia": "diaria", "intervalo": 1}
    elif re.search(r"\b(?:toda semana|semanalmente)\b", normalizado):
        recorrencia = {"frequencia": "semanal", "intervalo": 1}
    elif re.search(r"\b(?:todo mes|mensalmente)\b", normalizado):
        recorrencia = {"frequencia": "mensal", "intervalo": 1}
    elif re.search(r"\b(?:todo ano|anualmente)\b", normalizado):
        recorrencia = {"frequencia": "anual", "intervalo": 1}
    elif dia_semana is not None and re.search(r"\b(?:toda|todo)\b", normalizado):
        recorrencia = {"frequencia": "semanal", "intervalo": 1, "dia_semana": dia_semana}

    if recorrencia and alvo is None:
        base = atual
        if recorrencia.get("frequencia") == "semanal" and recorrencia.get("dia_semana") is not None:
            delta = (int(recorrencia["dia_semana"]) - atual.weekday()) % 7
            alvo = atual + timedelta(days=delta or 7)
        elif recorrencia.get("frequencia") == "diaria":
            alvo = atual
        else:
            alvo = datetime.fromtimestamp(
                proxima_ocorrencia(atual.timestamp(), recorrencia, depois_de=atual.timestamp())
            )
        origem, confianca = "recorrencia", 0.96

    horario_explicito = False
    if alvo is not None:
        alvo, horario_explicito = _com_horario(alvo, normalizado)
        if alvo <= atual and origem in {"hoje", "recorrencia"}:
            if recorrencia:
                alvo = datetime.fromtimestamp(
                    proxima_ocorrencia(alvo.timestamp(), recorrencia, depois_de=atual.timestamp())
                )
            else:
                alvo += timedelta(days=1)

    return {
        "data_alvo_ts": float(alvo.timestamp()) if alvo is not None else 0.0,
        "recorrencia": recorrencia,
        "origem": origem,
        "confianca": confianca,
        "horario_explicito": horario_explicito,
        "texto_temporal": bool(alvo is not None or recorrencia),
    }
