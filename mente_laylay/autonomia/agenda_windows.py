"""Integra a agenda da Laylay aos despertadores do Agendador do Windows."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable


def _nome_tarefa(identificador: str) -> str:
    seguro = "".join(ch for ch in str(identificador or "") if ch.isalnum() or ch in "_-")[:48]
    return f"Laylay_Despertar_{seguro or 'agenda'}"


def _xml_tarefa(instante: dt.datetime, *, voltar_a_dormir: bool) -> str:
    inicio = instante.replace(microsecond=0).isoformat()
    comando = "Start-Sleep -Seconds 2"
    if voltar_a_dormir:
        comando += "; Start-Sleep -Seconds 90; rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
    argumento = html.escape(f'-NoProfile -NonInteractive -WindowStyle Hidden -Command "{comando}"')
    return f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers><TimeTrigger><StartBoundary>{inicio}</StartBoundary><Enabled>true</Enabled></TimeTrigger></Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><WakeToRun>true</WakeToRun><ExecutionTimeLimit>PT5M</ExecutionTimeLimit></Settings>
  <Actions Context="Author"><Exec><Command>powershell.exe</Command><Arguments>{argumento}</Arguments></Exec></Actions>
</Task>'''


def sincronizar_despertares_windows(
    agendamentos: list[dict[str, Any]],
    *,
    estado_path: str,
    agora: dt.datetime | None = None,
    executar: Callable[..., Any] = subprocess.run,
    log: Callable[[str], Any] = print,
) -> bool:
    if os.name != "nt" or os.getenv("LAYLAY_AGENDA_DESPERTAR_WINDOWS", "1").strip() == "0":
        return False
    momento = agora or dt.datetime.now()
    ativos: dict[str, dt.datetime] = {}
    for item in agendamentos if isinstance(agendamentos, list) else []:
        if not isinstance(item, dict) or not item.get("ativo", True) or str(item.get("tipo") or "once") != "once":
            continue
        try:
            instante = dt.datetime.fromtimestamp(float(item.get("ts_execucao") or 0))
        except (TypeError, ValueError, OSError):
            continue
        if instante > momento:
            ativos[str(item.get("id") or int(instante.timestamp()))] = instante

    estado = Path(estado_path)
    try:
        anteriores = set(json.loads(estado.read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
        anteriores = set()

    sucesso = True
    for identificador in anteriores - set(ativos):
        resultado = executar(
            ["schtasks.exe", "/Delete", "/TN", _nome_tarefa(identificador), "/F"],
            capture_output=True, text=True, timeout=8, check=False,
        )
        sucesso = sucesso and int(getattr(resultado, "returncode", 1)) == 0

    voltar = os.getenv("LAYLAY_AGENDA_VOLTAR_SUSPENSAO", "0").strip() == "1"
    for identificador, instante in ativos.items():
        caminho_xml = ""
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-16", suffix=".xml", delete=False) as arquivo:
                arquivo.write(_xml_tarefa(instante, voltar_a_dormir=voltar))
                caminho_xml = arquivo.name
            resultado = executar(
                ["schtasks.exe", "/Create", "/TN", _nome_tarefa(identificador), "/XML", caminho_xml, "/F"],
                capture_output=True, text=True, timeout=10, check=False,
            )
            if int(getattr(resultado, "returncode", 1)) != 0:
                sucesso = False
                log(f"[AGENDA:WINDOWS] Não consegui registrar o despertar de {identificador}.")
        except Exception as erro:
            sucesso = False
            log(f"[AGENDA:WINDOWS] Falha ao integrar despertar: {erro}")
        finally:
            if caminho_xml:
                try:
                    os.remove(caminho_xml)
                except OSError:
                    pass

    estado.parent.mkdir(parents=True, exist_ok=True)
    temporario = estado.with_suffix(".tmp")
    temporario.write_text(json.dumps(sorted(ativos)), encoding="utf-8")
    os.replace(temporario, estado)
    return sucesso
