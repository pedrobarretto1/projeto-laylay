from __future__ import annotations

import json
import threading
import time

from mente_laylay.integracao.roteiro_teste_conversa import (
    ConfiguracaoRoteiro,
    RoteiroTesteConversaRuntime,
)


def test_guard_helper_existente_realmente_espera_worker() -> None:
    terminou = []

    def trabalhar() -> None:
        time.sleep(0.04)
        terminou.append(time.monotonic())

    worker = threading.Thread(target=trabalhar)
    worker.start()

    RoteiroTesteConversaRuntime._aguardar_processamento(
        worker,
        time.monotonic() + 1.0,
        time.monotonic,
    )

    assert terminou
    assert not worker.is_alive()


def test_red_proximo_turno_nao_pode_ser_enviado_com_worker_anterior_vivo(
    tmp_path,
) -> None:
    plano = {
        "id": 0,
        "texto_usuario": "anterior",
        "requer_execucao": False,
        "comandos": [],
    }

    holder = {}
    workers = []
    segundo_enviado_em = []
    primeiro_finalizado_em = []

    def enviar(texto: str):
        if texto == "primeiro":
            plano.clear()
            plano.update({
                "id": 1,
                "texto_usuario": texto,
                "requer_execucao": True,
                "autoriza_execucao": True,
                "fase": "tratado_prioritario",
                "comandos": [{
                    "intent": "CREATE_FILE",
                    "status": "arquivo_criado",
                    "executou": True,
                    "confirmado": True,
                }],
            })

            def executar_primeiro() -> None:
                holder["runtime"].observar_resposta(
                    "Primeira etapa confirmada."
                )

                # O worker ainda tem trabalho de cauda.
                time.sleep(0.10)
                primeiro_finalizado_em.append(time.monotonic())

            worker = threading.Thread(target=executar_primeiro)
            worker.start()
            workers.append(worker)
            return worker

        segundo_enviado_em.append(time.monotonic())

        plano.clear()
        plano.update({
            "id": 2,
            "texto_usuario": texto,
            "requer_execucao": False,
            "autoriza_execucao": False,
            "fase": "fala_verificada",
            "comandos": [],
        })

        holder["runtime"].observar_resposta(
            "Resposta correta do segundo."
        )
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("primeiro", "segundo"),
            timeout_resposta_s=1.0,
            silenciar_voz_durante_teste=True,
            aguardar_confirmacao_execucao=True,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: dict(plano),
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )

    holder["runtime"] = runtime

    assert runtime.executar() is True

    for worker in workers:
        worker.join(timeout=1.0)

    assert primeiro_finalizado_em
    assert segundo_enviado_em

    assert segundo_enviado_em[0] >= primeiro_finalizado_em[0], (
        "O roteiro liberou o turno N+1 enquanto o worker canônico "
        "do turno N ainda estava vivo."
    )


def test_red_fala_tardia_do_turno_anterior_nao_pode_virar_resposta_do_proximo(
    tmp_path,
) -> None:
    plano = {
        "id": 0,
        "texto_usuario": "anterior",
        "requer_execucao": False,
        "comandos": [],
    }

    holder = {}
    workers = []

    def enviar(texto: str):
        if texto == "primeiro":
            plano.clear()
            plano.update({
                "id": 1,
                "texto_usuario": texto,
                "requer_execucao": True,
                "autoriza_execucao": True,
                "fase": "tratado_prioritario",
                "comandos": [{
                    "intent": "CREATE_FILE",
                    "status": "arquivo_criado",
                    "executou": True,
                    "confirmado": True,
                }],
            })

            def executar_primeiro() -> None:
                holder["runtime"].observar_resposta(
                    "Resposta intermediária do primeiro."
                )

                time.sleep(0.08)

                # Reproduz exatamente a fala tardia do CREATE_FILE(B)
                # que apareceu depois de "Leia de novo." no RT1 real.
                holder["runtime"].observar_resposta(
                    "FALA_TARDIA_DO_PRIMEIRO"
                )

            worker = threading.Thread(target=executar_primeiro)
            worker.start()
            workers.append(worker)
            return worker

        plano.clear()
        plano.update({
            "id": 2,
            "texto_usuario": texto,
            "requer_execucao": False,
            "autoriza_execucao": False,
            "fase": "fala_verificada",
            "comandos": [],
        })

        def executar_segundo() -> None:
            # A resposta verdadeira chega depois da fala tardia do primeiro.
            time.sleep(0.16)
            holder["runtime"].observar_resposta(
                "RESPOSTA_CORRETA_DO_SEGUNDO"
            )

        worker = threading.Thread(target=executar_segundo)
        worker.start()
        workers.append(worker)
        return worker

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("primeiro", "segundo"),
            timeout_resposta_s=1.0,
            silenciar_voz_durante_teste=True,
            aguardar_confirmacao_execucao=True,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: dict(plano),
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )

    holder["runtime"] = runtime

    assert runtime.executar() is True

    for worker in workers:
        worker.join(timeout=1.0)

    checkpoint = json.loads(
        runtime.checkpoint_path.read_text(encoding="utf-8")
    )

    assert checkpoint["itens"][1]["resposta"] == (
        "RESPOSTA_CORRETA_DO_SEGUNDO"
    ), (
        "Uma fala tardia do turno anterior foi capturada como "
        "resposta do turno seguinte."
    )