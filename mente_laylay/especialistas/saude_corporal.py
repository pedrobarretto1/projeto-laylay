"""Diagnóstico correlacionado do dispositivo; não concede movimento."""
from __future__ import annotations
import hashlib
import re
from collections.abc import Mapping


def validar_identidade_corpo_usb(dados: Mapping | None) -> dict[str, str]:
    """Preferência local: nome é rótulo; fingerprint HEALTH é o alvo esperado."""
    if dados is None or dados == {}:
        return {}
    if not isinstance(dados, Mapping) or set(dados) != {"dispositivo", "nome"}:
        raise ValueError("pareamento_usb_invalido")
    dispositivo, nome = dados["dispositivo"], dados["nome"]
    if (not isinstance(dispositivo, str) or not re.fullmatch(r"[a-f0-9]{16}", dispositivo)
            or not isinstance(nome, str) or not 1 <= len(nome) <= 64 or nome != nome.strip()
            or any(not (c.isalnum() or c in " ._-()") for c in nome)):
        raise ValueError("pareamento_usb_invalido")
    return {"dispositivo": dispositivo, "nome": nome}

MOTIVOS_RESET = ("desconhecido","ligacao_energia","pino_externo","software","panic",
    "watchdog_interrupcao","watchdog_tarefa","watchdog","sono_profundo","brownout",
    "sdio","usb","jtag","efuse","instabilidade_energia","cpu_travada")

def interpretar_saude(linha: str, sequencia: int) -> dict:
    p=linha.split()
    if (len(p)!=12 or p[:3]!=["HEALTH","1",str(sequencia)]
        or len(p[3])!=12 or len(p[4])!=8
        or any(c not in "0123456789abcdef" for c in p[3]+p[4])
        or p[10] not in {"NENHUMA","TRANSPORTE","OLED","TTL","I2C","TIMEOUT_OLED","NACK_OLED"}
        or any(not p[i].isdecimal() or int(p[i])>4294967295 for i in (5,6,7,8,9,11))):
        raise ValueError("receipt_saude_invalido")
    motivo=int(p[5])
    return {"dispositivo":hashlib.sha256(p[3].encode()).hexdigest()[:16],"boot":p[4],
        "motivo_boot":MOTIVOS_RESET[motivo] if motivo<len(MOTIVOS_RESET) else "desconhecido",
        "motivo_boot_codigo":motivo,"uptime_ms":int(p[6]),"heap_livre":int(p[7]),
        "heap_minimo":int(p[8]),"perdas_sessao":int(p[9]),"motivo_perda_sessao":p[10],
        "perda_sessao_em_ms":int(p[11]),"origem":"executor_esp","autoriza_execucao":False}
