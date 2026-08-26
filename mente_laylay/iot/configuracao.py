"""Carregamento seguro de referências de configuração IoT."""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, Iterable


PREFIXO_TUYA_VENTILADOR = "IOT_TUYA_TOMADA_VENTILADOR"
PREFIXO_TUYA_LAMPADA = "IOT_TUYA_LAMPADA_QUARTO"

# P0_TUYA_CAMINHO_RAIZ_LAYLAY_V2_20260815
# configuracao.py fica em <raiz>/mente_laylay/iot/.
RAIZ_LAYLAY = Path(__file__).resolve().parents[2]


def resolver_caminho_laylay(caminho: str | Path) -> Path:
    """Resolve caminhos relativos de configuração a partir da raiz da Laylay."""
    path = Path(str(caminho or "").strip())
    if path.is_absolute():
        return path
    return RAIZ_LAYLAY / path


def ler_variavel_ambiente(nome: str, padrao: str = "") -> str:
    """Lê o processo e, no Windows, o perfil persistido pelo ``setx``."""
    nome = str(nome or "").strip()
    if not nome:
        return str(padrao or "")
    valor = os.getenv(nome)
    if valor is not None:
        return str(valor)
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as chave:
                valor, _ = winreg.QueryValueEx(chave, nome)
                return str(valor or "")
        except (FileNotFoundError, OSError):
            pass
    return str(padrao or "")


def nomes_variaveis_tuya(prefixo: str) -> Dict[str, str]:
    base = str(prefixo or "").strip().upper()
    return {
        "device_id": f"{base}_DEVICE_ID",
        "local_key": f"{base}_LOCAL_KEY",
        "ip": f"{base}_IP",
        "version": f"{base}_VERSION",
    }


def carregar_variaveis(
    referencias: Dict[str, str],
    *,
    obrigatorias: Iterable[str] = (),
) -> tuple[Dict[str, str], list[str]]:
    valores = {
        chave: ler_variavel_ambiente(nome_variavel).strip()
        for chave, nome_variavel in dict(referencias or {}).items()
    }
    faltando = [chave for chave in obrigatorias if not valores.get(str(chave))]
    return valores, faltando


def carregar_dispositivo_snapshot(caminho: str, *, nome: str = "", device_id: str = "") -> Dict[str, str]:
    """Lê somente os campos locais necessários de um snapshot TinyTuya."""
    path = resolver_caminho_laylay(caminho)
    try:
        dados = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    itens = dados.get("devices") if isinstance(dados, dict) else dados if isinstance(dados, list) else []
    nome_norm = str(nome or "").strip().casefold()
    id_norm = str(device_id or "").strip()
    for item in list(itens or []):
        if not isinstance(item, dict):
            continue
        corresponde = (
            bool(id_norm and str(item.get("id") or "").strip() == id_norm)
            or bool(nome_norm and str(item.get("name") or "").strip().casefold() == nome_norm)
        )
        if not corresponde:
            continue
        return {
            "device_id": str(item.get("id") or "").strip(),
            "local_key": str(item.get("key") or "").strip(),
            "ip": str(item.get("ip") or "").strip(),
            "version": str(item.get("ver") or "3.5").strip(),
        }
    return {}
