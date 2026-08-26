"""Registro canônico de dispositivos, ambientes e aliases."""

from __future__ import annotations

from typing import Dict, Iterable, List

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.iot.configuracao import (
    PREFIXO_TUYA_LAMPADA,
    PREFIXO_TUYA_VENTILADOR,
    nomes_variaveis_tuya,
)
from mente_laylay.iot.contratos import DispositivoIoT


class RegistroDispositivos:
    def __init__(self, dispositivos: Iterable[DispositivoIoT] = ()) -> None:
        self._dispositivos: Dict[str, DispositivoIoT] = {}
        self._aliases: Dict[str, str] = {}
        for dispositivo in dispositivos:
            self.registrar(dispositivo)

    def registrar(self, dispositivo: DispositivoIoT) -> None:
        nome = normalizar_texto(dispositivo.nome)
        if not nome:
            raise ValueError("Nome canônico IoT inválido.")
        if nome in self._dispositivos:
            raise ValueError(f"Dispositivo IoT duplicado: {dispositivo.nome}")

        aliases = {
            dispositivo.nome,
            dispositivo.nome_amigavel,
            *dispositivo.aliases,
        }
        aliases_normalizados = {normalizar_texto(alias) for alias in aliases if normalizar_texto(alias)}
        conflitos = [alias for alias in aliases_normalizados if alias in self._aliases]
        if conflitos:
            raise ValueError(f"Alias IoT já cadastrado: {sorted(conflitos)}")

        self._dispositivos[nome] = dispositivo
        for alias in aliases_normalizados:
            self._aliases[alias] = nome

    def resolver(self, referencia: str, ambiente: str = "") -> DispositivoIoT | None:
        ref = normalizar_texto(referencia)
        ambiente_norm = normalizar_texto(ambiente)
        nome = self._aliases.get(ref) or (ref if ref in self._dispositivos else "")
        dispositivo = self._dispositivos.get(nome)
        if dispositivo and ambiente_norm and normalizar_texto(dispositivo.ambiente) != ambiente_norm:
            return None
        return dispositivo

    def listar(self, ambiente: str = "", *, somente_ativos: bool = True) -> List[DispositivoIoT]:
        ambiente_norm = normalizar_texto(ambiente)
        itens = []
        for dispositivo in self._dispositivos.values():
            if somente_ativos and not dispositivo.ativo:
                continue
            if ambiente_norm and normalizar_texto(dispositivo.ambiente) != ambiente_norm:
                continue
            itens.append(dispositivo)
        return sorted(itens, key=lambda item: (item.ambiente, item.nome_amigavel))


def criar_dispositivo_ventilador(*, protocolo: str = "simulado") -> DispositivoIoT:
    return DispositivoIoT(
        nome="tomada_ventilador",
        nome_amigavel="ventilador",
        tipo="tomada",
        ambiente="quarto",
        protocolo=protocolo,
        aliases=(
            "tomada do ventilador",
            "ventilador do quarto",
            "tomada ventilador",
        ),
        capacidades=frozenset({"ligar", "desligar", "alternar", "status"}),
        risco="moderado",
        configuracao={
            "dps_estado": "1",
            "variaveis": nomes_variaveis_tuya(PREFIXO_TUYA_VENTILADOR),
        },
    )


def criar_dispositivo_lampada(*, protocolo: str = "simulado") -> DispositivoIoT:
    return DispositivoIoT(
        nome="lampada_quarto",
        nome_amigavel="lâmpada do quarto",
        tipo="lampada_rgb",
        ambiente="quarto",
        protocolo=protocolo,
        aliases=(
            "lâmpada", "lampada", "luz", "luz do quarto", "lâmpada do quarto",
            "lampada do quarto", "led do quarto", "led bulb w5k",
        ),
        capacidades=frozenset({
            "ligar", "desligar", "alternar", "status",
            "ajustar_brilho", "ajustar_cor", "ajustar_branco",
        }),
        risco="baixo",
        configuracao={
            "classe_tuya": "bulb",
            "dps_estado": "20",
            "variaveis": nomes_variaveis_tuya(PREFIXO_TUYA_LAMPADA),
            # P0_TUYA_CAMINHO_RAIZ_LAYLAY_V2_20260815
            # Fonte local canônica (fora do Git): <raiz>/credencia_tuya/.
            "snapshot_path": "credencia_tuya/snapshot.json",
            # Compatibilidade com instalações/pareamentos antigos.
            # O protocolo continua escolhendo o snapshot válido mais recente.
            "snapshot_fallback_paths": (
                "credencia_tuya/devices.json",
                "dados/voz_pessoal/snapshot.json",
                "snapshot.json",
                "dados/voz_pessoal/devices.json",
                "devices.json",
            ),
            "snapshot_device_name": "LED BULB W5K",
        },
    )
