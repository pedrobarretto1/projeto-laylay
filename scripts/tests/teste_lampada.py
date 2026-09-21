import json
import time

import tinytuya


# ==========================================
# PREENCHA MANUALMENTE
# ==========================================

DEVICE_ID = "ebfe0c0f05f20b9b6b0wch"
IP_LAMPADA = "192.168.100.57"
LOCAL_KEY = "bX#a8*KIJaMEjoK("
VERSAO = 3.5


# ==========================================
# CONEXÃO
# ==========================================

lampada = tinytuya.BulbDevice(
    dev_id=DEVICE_ID,
    address=IP_LAMPADA,
    local_key=LOCAL_KEY,
    version=VERSAO,
)

lampada.set_socketPersistent(True)
lampada.set_socketTimeout(5)


def mostrar_resposta(resposta):
    print(json.dumps(resposta, indent=2, ensure_ascii=False))


def ligar():
    mostrar_resposta(lampada.turn_on())


def desligar():
    mostrar_resposta(lampada.turn_off())


def vermelho():
    lampada.turn_on()
    time.sleep(0.3)
    mostrar_resposta(lampada.set_colour(255, 0, 0))


def verde():
    lampada.turn_on()
    time.sleep(0.3)
    mostrar_resposta(lampada.set_colour(0, 255, 0))


def azul():
    lampada.turn_on()
    time.sleep(0.3)
    mostrar_resposta(lampada.set_colour(0, 0, 255))


def branco_quente():
    lampada.turn_on()
    time.sleep(0.3)
    mostrar_resposta(
        lampada.set_white_percentage(
            brightness=70,
            colourtemp=10,
        )
    )


def branco_frio():
    lampada.turn_on()
    time.sleep(0.3)
    mostrar_resposta(
        lampada.set_white_percentage(
            brightness=70,
            colourtemp=100,
        )
    )


def brilho():
    valor = int(input("Brilho de 1 a 100: "))

    if not 1 <= valor <= 100:
        print("O brilho deve estar entre 1 e 100.")
        return

    lampada.turn_on()
    time.sleep(0.3)
    mostrar_resposta(
        lampada.set_brightness_percentage(valor)
    )


def status():
    mostrar_resposta(lampada.status())


while True:
    print(
        """
=== TESTE DA LÂMPADA TUYA ===

1 - Ver status
2 - Ligar
3 - Desligar
4 - Vermelho
5 - Verde
6 - Azul
7 - Branco quente
8 - Branco frio
9 - Alterar brilho
0 - Sair
"""
    )

    opcao = input("Escolha: ").strip()

    try:
        if opcao == "1":
            status()

        elif opcao == "2":
            ligar()

        elif opcao == "3":
            desligar()

        elif opcao == "4":
            vermelho()

        elif opcao == "5":
            verde()

        elif opcao == "6":
            azul()

        elif opcao == "7":
            branco_quente()

        elif opcao == "8":
            branco_frio()

        elif opcao == "9":
            brilho()

        elif opcao == "0":
            print("Teste encerrado.")
            break

        else:
            print("Opção inválida.")

    except Exception as erro:
        print(f"Erro ao controlar a lâmpada: {erro}")