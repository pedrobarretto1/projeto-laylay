"""Teste manual e deliberado do primeiro dispositivo Tuya da Laylay."""

from __future__ import annotations

import argparse
import sys

from mente_laylay.iot.configuracao import ler_variavel_ambiente
from mente_laylay.iot.controlador import ControladorIoT
from mente_laylay.iot.protocolos.tuya import ProtocoloTuya
from mente_laylay.iot.registro import RegistroDispositivos, criar_dispositivo_ventilador


CONFIRMACAO_ACAO = "EU_ESTOU_PRESENTE"


def _configuracao_presente() -> list[str]:
    nomes = {
        "device_id": "IOT_TUYA_TOMADA_VENTILADOR_DEVICE_ID",
        "local_key": "IOT_TUYA_TOMADA_VENTILADOR_LOCAL_KEY",
        "ip": "IOT_TUYA_TOMADA_VENTILADOR_IP",
        "version": "IOT_TUYA_TOMADA_VENTILADOR_VERSION",
    }
    return [campo for campo, variavel in nomes.items() if not ler_variavel_ambiente(variavel).strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Teste físico controlado da tomada do ventilador")
    parser.add_argument("acao", choices=("status", "ligar", "desligar"))
    parser.add_argument("--confirmar", default="", help="Confirmação adicional para ligar ou desligar")
    args = parser.parse_args(argv)

    if ler_variavel_ambiente("IOT_TESTE_FISICO_AUTORIZADO").strip().upper() != "SIM":
        print("BLOQUEADO: defina IOT_TESTE_FISICO_AUTORIZADO=SIM para autorizar este teste manual.")
        return 2
    faltando = _configuracao_presente()
    if faltando:
        print("BLOQUEADO: configuração Tuya ausente: " + ", ".join(faltando))
        return 2
    if args.acao != "status" and args.confirmar != CONFIRMACAO_ACAO:
        print(f"BLOQUEADO: {args.acao} exige --confirmar {CONFIRMACAO_ACAO}.")
        return 2

    dispositivo = criar_dispositivo_ventilador(protocolo="tuya")
    controlador = ControladorIoT(
        RegistroDispositivos([dispositivo]),
        [ProtocoloTuya(timeout=3.0, tentativas=2)],
    )
    resultado = controlador.executar(
        args.acao,
        "ventilador",
        origem="usuario",
        confirmado=args.acao != "status",
    )
    print(
        "RESULTADO "
        f"acao={resultado.acao} status={resultado.status} ok={resultado.ok} "
        f"confirmado={resultado.confirmado} estado={resultado.estado_atual}"
    )
    return 0 if resultado.ok else 1


if __name__ == "__main__":
    sys.exit(main())
