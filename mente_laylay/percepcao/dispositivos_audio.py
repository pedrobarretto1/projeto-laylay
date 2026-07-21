"""Seleção consistente dos dispositivos de entrada e saída de áudio."""

from __future__ import annotations

from typing import Any


def _indice_padrao(sounddevice_mod: Any, tipo: str) -> int | None:
    padrao = getattr(getattr(sounddevice_mod, "default", None), "device", None)
    posicao = 0 if tipo == "entrada" else 1
    try:
        valor = padrao[posicao]
    except (IndexError, KeyError, TypeError):
        valor = padrao if tipo == "entrada" else None
    try:
        indice = int(valor)
    except (TypeError, ValueError):
        return None
    return indice if indice >= 0 else None


def selecionar_dispositivo_audio(
    sounddevice_mod: Any,
    tipo: str,
    preferencia: str = "",
) -> tuple[int, dict[str, Any], str]:
    """Retorna índice, informações e origem da escolha (padrão/configurado/fallback)."""
    tipo = str(tipo or "").strip().casefold()
    if tipo not in {"entrada", "saida", "saída"}:
        raise ValueError(f"tipo de dispositivo de áudio inválido: {tipo}")
    tipo = "saida" if tipo in {"saida", "saída"} else "entrada"
    campo_canais = "max_input_channels" if tipo == "entrada" else "max_output_channels"
    dispositivos = list(sounddevice_mod.query_devices())
    candidatos = [
        (indice, dict(info))
        for indice, info in enumerate(dispositivos)
        if int(info.get(campo_canais) or 0) > 0
    ]
    if not candidatos:
        raise RuntimeError(f"nenhum dispositivo de {tipo} de áudio foi encontrado")

    pedido = str(preferencia or "").strip()
    if pedido:
        escolhido = None
        if pedido.isdigit():
            indice_pedido = int(pedido)
            escolhido = next((item for item in candidatos if item[0] == indice_pedido), None)
        else:
            pedido_norm = pedido.casefold()
            escolhido = next(
                (
                    item for item in candidatos
                    if pedido_norm in str(item[1].get("name") or "").casefold()
                ),
                None,
            )
        if escolhido is None:
            raise RuntimeError(f"dispositivo de {tipo} configurado não foi encontrado: {pedido}")
        return escolhido[0], escolhido[1], "configurado"

    indice_padrao = _indice_padrao(sounddevice_mod, tipo)
    escolhido = next((item for item in candidatos if item[0] == indice_padrao), None)
    if escolhido is not None:
        return escolhido[0], escolhido[1], "padrão do sistema"

    # Se o backend não informar um padrão, use o padrão da primeira API de host
    # que possua um candidato válido antes de recorrer à lista inteira.
    try:
        chave_host = "default_input_device" if tipo == "entrada" else "default_output_device"
        for host in list(sounddevice_mod.query_hostapis()):
            try:
                indice_host = int(host.get(chave_host, -1))
            except (AttributeError, TypeError, ValueError):
                continue
            escolhido = next((item for item in candidatos if item[0] == indice_host), None)
            if escolhido is not None:
                return escolhido[0], escolhido[1], "padrão do sistema"
    except Exception:
        pass

    escolhido = candidatos[0]
    return escolhido[0], escolhido[1], "fallback"

