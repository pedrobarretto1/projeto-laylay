from __future__ import annotations

import json
from pathlib import Path
import threading
import time

import pytest

from mente_laylay.integracao.roteiro_teste_conversa import (
    ConfiguracaoRoteiro,
    EspelhoTerminalPersistente,
    RoteiroTesteConversaRuntime,
    carregar_configuracao_roteiro,
    preparar_diretorio_resultado,
)
from mente_laylay.personalidade.terminal_laylay import should_log_message


def test_noop_confirmado_nao_e_rotulado_como_falha_do_roteiro() -> None:
    plano = {
        "id": 2,
        "texto_usuario": "Essa também.",
        "fase": "tratado_prioritario",
        "comandos": [{
            "intent": "PLAYLIST_ADD",
            "status": "playlist_musica_ja_existia",
            "executou": False,
            "confirmado": True,
        }],
    }

    assert RoteiroTesteConversaRuntime._resultado_turno_terminal(
        plano,
        comando="Essa também.",
        plano_id_anterior=1,
    ) == (True, "execucao_confirmada")


def test_plano_composto_com_etapa_ja_satisfeita_conta_como_confirmado() -> None:
    plano = {
        "id": 4,
        "texto_usuario": "Abre o Visual Studio Code e coloca ele na direita.",
        "fase": "tratado_prioritario",
        "comandos": [
            {
                "intent": "APP_OPEN", "status": "ja_aberto_focado",
                "executou": False, "confirmado": True,
            },
            {
                "intent": "ORGANIZAR_DESKTOP", "status": "layout_confirmado",
                "executou": True, "confirmado": True,
            },
        ],
    }

    assert RoteiroTesteConversaRuntime._resultado_turno_terminal(
        plano,
        comando="Abre o Visual Studio Code e coloca ele na direita.",
        plano_id_anterior=3,
    ) == (True, "execucao_confirmada")


def test_contrato_final_sem_acao_nao_vira_execucao_nao_publicada() -> None:
    plano = {
        "id": 22,
        "texto_usuario": "continua",
        "fase": "fala_verificada",
        "requer_execucao": True,
        "autoriza_execucao": True,
        "comandos": [],
        "decisao_turno": {
            "proprietario": "conversa",
            "permite_acao": False,
            "requer_esclarecimento": True,
            "intencao": "",
            "status": "sem_acao",
        },
    }

    assert RoteiroTesteConversaRuntime._resultado_turno_terminal(
        plano,
        comando="continua",
        plano_id_anterior=21,
    ) == (True, "execucao_nao_autorizada")


def test_carrega_lista_e_opcoes_sem_executar_codigo_do_roteiro(tmp_path) -> None:
    roteiro = tmp_path / "roteiro.py"
    roteiro.write_text(
        "COMANDOS = ['oi lay', 'como você está?']\n"
        "TIMEOUT_RESPOSTA_S = 35\n"
        "INTERVALO_ENTRE_COMANDOS_S = 0.25\n"
        "PARAR_SEM_RESPOSTA = False\n"
        "ENCERRAR_AO_FINAL = True\n"
        "raise RuntimeError('não deve executar')\n",
        encoding="utf-8",
    )

    configuracao = carregar_configuracao_roteiro(roteiro)

    assert configuracao == ConfiguracaoRoteiro(
        comandos=("oi lay", "como você está?"),
        atraso_inicial_s=10.0,
        timeout_resposta_s=35.0,
        timeout_voz_s=240.0,
        intervalo_comandos_s=0.25,
        parar_sem_resposta=False,
        encerrar_ao_final=True,
        silenciar_voz_durante_teste=True,
        aguardar_confirmacao_execucao=True,
    )


def test_carrega_expectativas_semanticas_locais_sem_executar_roteiro(
    tmp_path,
) -> None:
    roteiro = tmp_path / "roteiro_personalidade.py"
    roteiro.write_text(
        "COMANDOS = ['isso me deixou triste']\n"
        "EXPECTATIVAS_SEMANTICAS = {\n"
        "    1: {\n"
        "        'sem_comando': True,\n"
        "        'nome': 'evento_emocional_causal',\n"
        "        'dominio': 'personalidade',\n"
        "    },\n"
        "}\n"
        "raise RuntimeError('não deve executar')\n",
        encoding="utf-8",
    )

    configuracao = carregar_configuracao_roteiro(roteiro)

    assert configuracao.expectativas_semanticas == {
        1: {
            "sem_comando": True,
            "nome": "evento_emocional_causal",
            "dominio": "personalidade",
        },
    }


def test_constante_legada_expectativas_do_caos_nao_e_ativada(tmp_path) -> None:
    roteiro = tmp_path / "roteiro_legado.py"
    roteiro.write_text(
        "COMANDOS = ['continua']\n"
        "EXPECTATIVAS = {'continua': {'sem_comando': True}}\n",
        encoding="utf-8",
    )

    configuracao = carregar_configuracao_roteiro(roteiro)

    assert configuracao.expectativas_semanticas == {}


@pytest.mark.parametrize(
    "expectativas",
    (
        [],
        {0: {"sem_comando": True}},
        {True: {"sem_comando": True}},
        {1: "não é um contrato"},
    ),
)
def test_rejeita_expectativas_semanticas_malformadas(expectativas) -> None:
    with pytest.raises(ValueError, match="EXPECTATIVAS_SEMANTICAS|expectativa"):
        ConfiguracaoRoteiro(
            comandos=("oi",),
            expectativas_semanticas=expectativas,
        )


def test_expectativa_local_do_roteiro_substitui_regra_global_so_na_execucao(
    tmp_path,
) -> None:
    comando = "continua"
    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=(comando,),
            expectativas_semanticas={
                1: {
                    "intents_any": ("MEDIA_CONTROL",),
                    "nome": "continuidade_musical_dedicada",
                    "dominio": "musica",
                },
            },
        ),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    runtime._atualizar_item(  # noqa: SLF001 - prova a fronteira do avaliador
        0,
        status="respondido",
        comando=comando,
        resposta="Pedi para a música continuar.",
        plano={
            "fase": "tratado_prioritario",
            "erros": [],
            "comandos": [{
                "intent": "MEDIA_CONTROL",
                "status": "midia_play",
                "executou": True,
                "confirmado": True,
            }],
        },
        avaliacao={"respondeu": True},
    )

    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    avaliacao = checkpoint["itens"][0]["avaliacao"]
    assert avaliacao["resultado_semantico"] == "passou"
    assert avaliacao["expectativa"] == "continuidade_musical_dedicada"
    assert avaliacao["origem_expectativa"] == "roteiro_dedicado"


def test_avaliador_recebe_plano_integral_sem_persisti_lo_no_checkpoint(
    tmp_path,
) -> None:
    comando = "Estou feliz porque terminei um projeto."
    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=(comando,),
            expectativas_semanticas={
                1: {
                    "campos_plano": {
                        "evento_emocional_causal.validade.valido": True,
                    },
                    "nome": "contrato_integral_efemero",
                    "dominio": "infraestrutura_teste",
                },
            },
        ),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    plano_integral = {
        "fase": "fala_verificada",
        "erros": [],
        "comandos": [],
        "evento_emocional_causal": {
            "validade": {"valido": True},
        },
    }

    runtime._atualizar_item(  # noqa: SLF001 - prova a fronteira do avaliador
        0,
        status="respondido",
        comando=comando,
        resposta="Que notícia boa.",
        plano=runtime._plano_compacto_checkpoint(plano_integral),  # noqa: SLF001
        _plano_avaliacao=plano_integral,
        avaliacao={"respondeu": True},
    )

    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    item = checkpoint["itens"][0]
    assert item["avaliacao"]["resultado_semantico"] == "passou"
    assert "evento_emocional_causal" not in item["plano"]
    assert "_plano_avaliacao" not in item


def test_espera_atraso_ativa_e_confirma_chat_antes_do_primeiro_comando(
    tmp_path,
) -> None:
    eventos: list[str] = []
    chat_ativo = {"valor": False}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def ativar_chat() -> None:
        eventos.append("chat")
        chat_ativo["valor"] = True

    def enviar(_texto: str) -> bool:
        eventos.append("envio")
        holder["runtime"].observar_resposta("resposta pronta")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("oi lay",),
            atraso_inicial_s=0.03,
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        ativar_modo_chat=ativar_chat,
        modo_chat_ativo_getter=lambda: chat_ativo["valor"],
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime
    iniciou = time.monotonic()

    assert runtime.executar() is True
    assert time.monotonic() - iniciou >= 0.03
    assert eventos == ["chat", "envio"]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["preparacao"] == {
        "status": "modo_chat_confirmado",
        "atraso_inicial_s": 0.03,
        "voz_silenciada": False,
    }


def test_roteiro_silencioso_avanca_pela_resposta_sem_consultar_audio(
    tmp_path,
) -> None:
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        holder["runtime"].observar_resposta(f"resposta {texto}")
        return True

    def voz_nao_deveria_ser_consultada() -> bool:
        raise AssertionError("roteiro silencioso não deve consultar a fila de voz")

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("um", "dois"),
            timeout_resposta_s=1.0,
            timeout_voz_s=999.0,
            intervalo_comandos_s=0.0,
            silenciar_voz_durante_teste=True,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {"fase": "executado"},
        voz_ocupada_getter=voz_nao_deveria_ser_consultada,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    assert enviados == ["um", "dois"]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["criterio_conclusao"] == "transporte_resposta"
    assert checkpoint["preparacao"]["voz_silenciada"] is True
    assert all(item["voz_silenciada"] is True for item in checkpoint["itens"])
    assert all(item["voz_observada"] is False for item in checkpoint["itens"])


def test_proximo_comando_espera_resultado_final_do_turno_atual(tmp_path) -> None:
    enviados: list[tuple[str, float]] = []
    resultado_final_em: list[float] = []
    plano: dict = {
        "id": 1,
        "texto_usuario": "turno anterior",
        "requer_execucao": False,
        "comandos": [],
    }
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append((texto, time.monotonic()))
        if texto == "cria o arquivo":
            plano.clear()
            plano.update({
                "id": 2,
                "texto_usuario": texto,
                "requer_execucao": True,
                "autoriza_execucao": True,
                "comandos": [{
                    "intent": "CREATE_FILE",
                    "status": "processando",
                    "executou": None,
                    "confirmado": None,
                }],
            })
            holder["runtime"].observar_resposta("Estou terminando o arquivo.")

            def concluir() -> None:
                time.sleep(0.08)
                plano["comandos"] = [{
                    "intent": "CREATE_FILE",
                    "status": "arquivo_criado",
                    "executou": True,
                    "confirmado": True,
                }]
                resultado_final_em.append(time.monotonic())

            threading.Thread(target=concluir).start()
        else:
            plano.clear()
            plano.update({
                "id": 3,
                "texto_usuario": texto,
                "requer_execucao": False,
                "comandos": [],
            })
            holder["runtime"].observar_resposta("Conversa respondida.")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("cria o arquivo", "como você está?"),
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
    assert [texto for texto, _ts in enviados] == [
        "cria o arquivo", "como você está?",
    ]
    assert enviados[1][1] >= resultado_final_em[0]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["criterio_conclusao"] == (
        "transporte_resposta_e_resultado_turno"
    )
    assert checkpoint["itens"][0]["motivo_resultado"] == "execucao_confirmada"
    assert checkpoint["itens"][1]["motivo_resultado"] == "resposta_sem_execucao"


def test_pedido_de_confirmacao_libera_o_sim_seguinte(tmp_path) -> None:
    enviados: list[str] = []
    plano: dict = {}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        if texto == "apaga o arquivo":
            plano.clear()
            plano.update({
                "id": 10,
                "texto_usuario": texto,
                "requer_execucao": True,
                "autoriza_execucao": True,
                "comandos": [{
                    "intent": "DELETE_ITEM",
                    "status": "aguardando_confirmacao",
                    "executou": False,
                    "confirmado": False,
                }],
            })
            holder["runtime"].observar_resposta("Confirma a exclusão?")
        else:
            plano.clear()
            plano.update({
                "id": 11,
                "texto_usuario": texto,
                "requer_execucao": True,
                "autoriza_execucao": True,
                "comandos": [{
                    "intent": "CONFIRM_DELETE_ITEM",
                    "status": "movido_para_lixeira",
                    "executou": True,
                    "confirmado": True,
                }],
            })
            holder["runtime"].observar_resposta("Enviei para a lixeira.")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("apaga o arquivo", "Sim"),
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
    assert enviados == ["apaga o arquivo", "Sim"]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["motivo_resultado"] == (
        "aguardando_confirmacao_usuario"
    )
    assert checkpoint["itens"][1]["motivo_resultado"] == "execucao_confirmada"


def test_plano_antigo_nao_libera_proximo_comando(tmp_path) -> None:
    enviados: list[str] = []
    plano = {
        "id": 20,
        "texto_usuario": "turno anterior",
        "requer_execucao": False,
        "comandos": [],
    }
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        holder["runtime"].observar_resposta("Uma fala sem plano correspondente.")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("comando atual", "não deve sair"),
            timeout_resposta_s=0.06,
            silenciar_voz_durante_teste=True,
            aguardar_confirmacao_execucao=True,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: plano,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is False
    assert enviados == ["comando atual"]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["status"] == "resultado_nao_finalizado"
    assert checkpoint["itens"][0]["motivo_resultado"] == "plano_de_outro_turno"
    assert checkpoint["itens"][1]["status"] == "pendente"


def test_turno_operacional_final_sem_comando_registra_falha_e_avanca(
    tmp_path,
) -> None:
    enviados: list[str] = []
    logs: list[str] = []
    plano: dict = {}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        plano.clear()
        if texto.startswith("Apaga"):
            plano.update({
                "id": 30,
                "texto_usuario": texto,
                "requer_execucao": True,
                "autoriza_execucao": True,
                "fase": "executado",
                "comandos": [],
                "erros": [],
            })
            resposta = "Entendi, mas não executei nem confirmei."
        else:
            plano.update({
                "id": 31,
                "texto_usuario": texto,
                "requer_execucao": False,
                "autoriza_execucao": False,
                "fase": "fala_verificada",
                "comandos": [],
                "erros": [],
            })
            resposta = "Continuando o roteiro."
        holder["runtime"].observar_resposta(resposta)
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("Apaga o arquivo roteiro correcao.txt.", "próximo teste"),
            timeout_resposta_s=1.0,
            silenciar_voz_durante_teste=True,
            aguardar_confirmacao_execucao=True,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: dict(plano),
        diretorio_resultado=tmp_path,
        log=logs.append,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    assert enviados == [
        "Apaga o arquivo roteiro correcao.txt.", "próximo teste",
    ]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["motivo_resultado"] == (
        "execucao_nao_publicada"
    )
    assert any("falha registrada; avançando" in linha for linha in logs)


def test_contrato_operacional_incompleto_registra_falha_e_avanca(
    tmp_path,
) -> None:
    enviados: list[str] = []
    logs: list[str] = []
    plano: dict = {}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        plano.clear()
        if texto.startswith("O que tem"):
            plano.update({
                "id": 40,
                "texto_usuario": texto,
                "requer_execucao": True,
                "autoriza_execucao": True,
                "fase": "tratado_prioritario",
                "comandos": [{
                    "intent": "PLAYLIST_LIST",
                    "alvo": "roteiro teste",
                    "status": "",
                    "executou": True,
                    "confirmado": None,
                }],
                "erros": [],
            })
            resposta = "A playlist Roteiro Teste tem uma música."
        else:
            plano.update({
                "id": 41,
                "texto_usuario": texto,
                "requer_execucao": False,
                "autoriza_execucao": False,
                "fase": "fala_verificada",
                "comandos": [],
                "erros": [],
            })
            resposta = "Continuando o roteiro."
        holder["runtime"].observar_resposta(resposta)
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=(
                "O que tem na playlist roteiro teste?",
                "próximo teste",
            ),
            timeout_resposta_s=1.0,
            silenciar_voz_durante_teste=True,
            aguardar_confirmacao_execucao=True,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: dict(plano),
        diretorio_resultado=tmp_path,
        log=logs.append,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    assert enviados == [
        "O que tem na playlist roteiro teste?", "próximo teste",
    ]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["motivo_resultado"] == (
        "contrato_operacional_incompleto"
    )
    assert any("falha registrada; avançando" in linha for linha in logs)


def test_nao_envia_comando_quando_modo_chat_nao_e_confirmado(tmp_path) -> None:
    enviados: list[str] = []
    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("não deve sair",),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=lambda texto: enviados.append(texto) or True,
        resultado_getter=lambda: {},
        ativar_modo_chat=lambda: None,
        modo_chat_ativo_getter=lambda: False,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )

    assert runtime.executar() is False
    assert enviados == []
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["preparacao"]["status"] == "modo_chat_nao_confirmado"
    assert checkpoint["itens"][0]["status"] == "pendente"


def test_envia_um_turno_por_vez_e_persiste_resposta_antes_do_proximo(tmp_path) -> None:
    enviados: list[str] = []
    checkpoint_antes_do_segundo: list[dict] = []
    runtime_holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append(texto)
        if len(enviados) == 2:
            checkpoint_antes_do_segundo.append(json.loads(
                (tmp_path / "checkpoint.json").read_text(encoding="utf-8")
            ))

        def responder() -> None:
            time.sleep(0.015)
            runtime_holder["runtime"].observar_resposta(f"resposta para {texto}")

        thread = threading.Thread(target=responder)
        thread.start()
        return thread

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("primeiro", "segundo"),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {"fase": "executado"},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    runtime_holder["runtime"] = runtime

    assert runtime.executar() is True
    assert enviados == ["primeiro", "segundo"]
    assert checkpoint_antes_do_segundo[0]["itens"][0]["status"] == "respondido"
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["concluido"] is True
    assert [item["status"] for item in checkpoint["itens"]] == [
        "respondido", "respondido",
    ]
    conversa = runtime.conversa_path.read_text(encoding="utf-8")
    assert conversa.index("primeiro") < conversa.index("resposta para primeiro")
    assert conversa.index("resposta para primeiro") < conversa.index("segundo")
    assert "**Plano observado:** executado; sem comando operacional." in conversa
    assert "```json" not in conversa
    planos = [
        json.loads(linha)
        for linha in runtime.planos_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [item["plano"] for item in planos] == [
        {"fase": "executado"}, {"fase": "executado"},
    ]
    for item in checkpoint["itens"]:
        esperado = {
            "respondeu": True,
            "plano_observado": True,
            "quantidade_comandos": 0,
            "execucao": "sem_comando_observado",
            "confirmacao": "sem_comando_observado",
            "intencao_correta": "nao_avaliado",
            "fala_coerente": "nao_avaliado",
        }
        assert {
            chave: item["avaliacao"][chave] for chave in esperado
        } == esperado
        assert item["avaliacao"]["versao_avaliador"] == 16
        assert item["avaliacao"]["erros_semanticos"] == []
        assert item["avaliacao"]["alertas_semanticos"] == []


def test_captura_plano_terminal_quando_worker_tem_tarefas_de_cauda(tmp_path) -> None:
    plano: dict = {}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        def processar() -> None:
            plano.update({
                "id": 501,
                "texto_usuario": texto,
                "requer_execucao": False,
                "fase": "fala_verificada",
                "comandos": [],
                "erros": [],
            })
            holder["runtime"].observar_resposta("Resposta já publicada.")
            time.sleep(0.03)
            plano.clear()
            time.sleep(0.12)

        thread = threading.Thread(target=processar)
        thread.start()
        return thread

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("turno com cauda lenta",),
            # O worker leva 150 ms. O prazo precisa permitir que a barreira
            # canônica termine; o contrato deste teste é preservar o snapshot
            # transitório depois da cauda, não liberar um worker ainda vivo.
            timeout_resposta_s=0.30,
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
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["status"] == "respondido"
    assert checkpoint["itens"][0]["motivo_resultado"] == "resposta_sem_execucao"


def test_captura_plano_no_mesmo_instante_em_que_resposta_e_publicada(tmp_path) -> None:
    plano: dict = {}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        def processar() -> None:
            plano.update({
                "id": 502,
                "texto_usuario": texto,
                "requer_execucao": False,
                "fase": "fala_verificada",
                "comandos": [],
                "erros": [],
            })
            holder["runtime"].observar_resposta("Resposta já publicada.")
            plano.clear()

        thread = threading.Thread(target=processar)
        thread.start()
        return thread

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("turno com plano transitório",),
            timeout_resposta_s=0.08,
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
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["status"] == "respondido"
    assert checkpoint["itens"][0]["motivo_resultado"] == "resposta_sem_execucao"


def test_cadeia_composta_persiste_fala_e_receipts_apos_worker_concluir(
    tmp_path,
) -> None:
    """A primeira fala de uma subetapa não encerra o turno composto."""
    plano: dict = {}
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        def processar() -> None:
            plano.update({
                "id": 503,
                "texto_usuario": texto,
                "requer_execucao": True,
                "fase": "tratado_prioritario",
                "comandos": [{
                    "intent": "PLAYLIST_ADD",
                    "status": "playlist_musica_adicionada",
                    "executou": True,
                    "confirmado": True,
                }],
                "erros": [],
            })
            holder["runtime"].observar_resposta("Faixa adicionada.")
            time.sleep(0.02)
            plano["comandos"].append({
                "intent": "PLAYLIST_LIST",
                "status": "playlists_listadas",
                "executou": True,
                "confirmado": True,
            })
            holder["runtime"].observar_resposta(
                "Faixa adicionada. A playlist tem uma música.",
            )

        thread = threading.Thread(target=processar)
        thread.start()
        return thread

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=(
                "Adiciona essa música na playlist teste e depois me mostra ela.",
            ),
            timeout_resposta_s=1.0,
            silenciar_voz_durante_teste=True,
            aguardar_confirmacao_execucao=True,
            expectativas_semanticas={
                1: {
                    "intents_all": ("PLAYLIST_ADD", "PLAYLIST_LIST"),
                    "statuses_all": (
                        "playlist_musica_adicionada",
                        "playlists_listadas",
                    ),
                    "confirmado": True,
                    "dominio": "musica",
                    "nome": "cadeia_composta_completa",
                },
            },
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: dict(plano),
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    item = checkpoint["itens"][0]
    assert item["resposta"] == "Faixa adicionada. A playlist tem uma música."
    assert [comando["intent"] for comando in item["plano"]["comandos"]] == [
        "PLAYLIST_ADD",
        "PLAYLIST_LIST",
    ]
    assert item["avaliacao"]["resultado_semantico"] == "passou"


def test_exibe_pergunta_no_terminal_antes_dos_logs_do_turno(tmp_path) -> None:
    logs: list[str] = []
    logs_visiveis: list[str] = []
    ordem: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def registrar(texto: str) -> None:
        logs.append(texto)
        if should_log_message(texto):
            logs_visiveis.append(texto)
        ordem.append("log")

    def enviar(texto: str) -> bool:
        ordem.append("envio")
        holder["runtime"].observar_resposta(f"resposta para {texto}")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("qual é o meu nome?",),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=registrar,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    saida = "\n".join(logs)
    saida_visivel = "\n".join(logs_visiveis)
    bloco = "💬 Você:\n> qual é o meu nome?"
    assert saida.count("💬 Você:") == 1
    assert bloco in saida
    assert bloco in saida_visivel
    assert saida.index(bloco) < saida.index(
        "🧪 [ROTEIRO:001] enviando: qual é o meu nome?"
    )
    assert ordem.index("envio") > ordem.index("log")


def test_sem_resposta_para_e_deixa_proximo_comando_pendente(tmp_path) -> None:
    enviados: list[str] = []
    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("sem resposta", "não deve sair"),
            timeout_resposta_s=0.03,
            intervalo_comandos_s=0.0,
            parar_sem_resposta=True,
        ),
        enviar_entrada=lambda texto: enviados.append(texto) or True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )

    assert runtime.executar() is False
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert enviados == ["sem resposta"]
    assert checkpoint["itens"][0]["status"] == "sem_resposta"
    assert checkpoint["itens"][1]["status"] == "pendente"
    assert "Nenhuma resposta foi observada" in runtime.conversa_path.read_text(
        encoding="utf-8"
    )


def test_proximo_comando_espera_a_voz_terminar(tmp_path) -> None:
    enviados: list[tuple[str, float]] = []
    voz_ocupada = threading.Event()
    voz_terminou_em: list[float] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append((texto, time.monotonic()))

        def processar() -> None:
            holder["runtime"].observar_resposta(f"resposta {texto}")
            voz_ocupada.set()

            def reproduzir() -> None:
                time.sleep(0.08)
                voz_terminou_em.append(time.monotonic())
                voz_ocupada.clear()

            threading.Thread(target=reproduzir).start()

        thread = threading.Thread(target=processar)
        thread.start()
        return thread

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("um", "dois"),
            timeout_resposta_s=1.0,
            timeout_voz_s=1.5,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        voz_ocupada_getter=voz_ocupada.is_set,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    assert [texto for texto, _ts in enviados] == ["um", "dois"]
    assert enviados[1][1] >= voz_terminou_em[0]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["voz_observada"] is True
    assert checkpoint["itens"][0]["voz_concluida"] is True


def test_voz_que_nao_termina_interrompe_roteiro(tmp_path) -> None:
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append(texto)
        holder["runtime"].observar_resposta("resposta pronta")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("um", "dois"),
            timeout_resposta_s=1.0,
            timeout_voz_s=0.05,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        voz_ocupada_getter=lambda: bool(enviados),
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is False
    assert enviados == ["um"]
    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["itens"][0]["status"] == "voz_nao_finalizada"
    assert checkpoint["itens"][1]["status"] == "pendente"


def test_primeiro_comando_tambem_espera_fala_inicial(tmp_path) -> None:
    voz_ocupada = threading.Event()
    voz_ocupada.set()
    fala_inicial_terminou = {"valor": 0.0}
    enviado_em: list[float] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def liberar_fala_inicial() -> None:
        time.sleep(0.06)
        fala_inicial_terminou["valor"] = time.monotonic()
        voz_ocupada.clear()

    threading.Thread(target=liberar_fala_inicial).start()

    def enviar(_texto: str):
        enviado_em.append(time.monotonic())
        holder["runtime"].observar_resposta("pronto")
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("primeiro",),
            timeout_resposta_s=1.0,
            timeout_voz_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        voz_ocupada_getter=voz_ocupada.is_set,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True
    assert enviado_em[0] >= fala_inicial_terminou["valor"]


def test_retomada_pula_turno_ja_respondido(tmp_path) -> None:
    comandos = ("já foi", "continua daqui")
    diretorio = preparar_diretorio_resultado(
        tmp_path / "roteiro.py", raiz=tmp_path / "resultados",
    )
    runtime_inicial = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=diretorio,
        log=lambda *_args: None,
    )
    runtime_inicial._atualizar_item(  # noqa: SLF001 - prepara checkpoint real
        0, status="respondido", resposta="pronto",
    )
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str):
        enviados.append(texto)
        holder["runtime"].observar_resposta("resposta retomada")
        return True

    retomado = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=comandos,
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        diretorio_resultado=diretorio,
        retomar=True,
        log=lambda *_args: None,
    )
    holder["runtime"] = retomado

    assert retomado.executar() is True
    assert enviados == ["continua daqui"]


def test_retomada_reconstroi_referencia_com_consultas_seguras(tmp_path) -> None:
    comandos = (
        "Encontra o código e abre o primeiro resultado",
        "Onde esse arquivo fica?",
        "Fecha ele.",
        "O que eu copiei?",
    )
    inicial = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    inicial._atualizar_item(0, status="respondido", resposta="aberto")  # noqa: SLF001
    inicial._atualizar_item(1, status="respondido", resposta="caminho")  # noqa: SLF001
    inicial._atualizar_item(2, status="enviado")  # noqa: SLF001
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        holder["runtime"].observar_resposta(f"resposta: {texto}")
        return True

    retomado = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=comandos,
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        retomar=True,
        log=lambda *_args: None,
    )
    holder["runtime"] = retomado

    assert retomado.executar() is True
    assert enviados == list(comandos)
    checkpoint = json.loads(retomado.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["retomada_contexto"] == {
        "status": "reconstrucao_programada",
        "inicio": 0,
        "fim": 2,
    }


def test_retomada_reenvia_composto_autocontido_com_referencia_interna(
    tmp_path,
) -> None:
    comando = (
        "Coloca a playlist VMZ, pausa a música e me diz o estado dela."
    )
    inicial = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=(comando,)),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    inicial._atualizar_item(0, status="enviado")  # noqa: SLF001
    enviados: list[str] = []
    holder: dict[str, RoteiroTesteConversaRuntime] = {}

    def enviar(texto: str) -> bool:
        enviados.append(texto)
        holder["runtime"].observar_resposta("playlist pausada")
        return True

    retomado = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=(comando,),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        retomar=True,
        log=lambda *_args: None,
    )
    holder["runtime"] = retomado

    assert retomado.executar() is True
    assert enviados == [comando]


@pytest.mark.parametrize(
    ("comando", "depende"),
    (
        ("Abre o Opera e coloca ele na esquerda.", False),
        (
            "Coloca a playlist VMZ, pausa a música e me diz o estado dela.",
            False,
        ),
        ("Fecha ela.", True),
        ("Coloca ela na playlist VMZ.", True),
        (
            "Adiciona essa música na playlist caos sonora e depois me mostra "
            "o que tem nela.",
            True,
        ),
    ),
)
def test_retomada_distingue_referencia_interna_de_contexto_anterior(
    comando,
    depende,
) -> None:
    assert (
        RoteiroTesteConversaRuntime._comando_depende_de_contexto(comando)
        is depende
    )


def test_retomada_nao_refaz_exclusao_para_reconstruir_sim(tmp_path) -> None:
    comandos = ("Apaga o arquivo teste.txt", "Sim")
    inicial = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    inicial._atualizar_item(0, status="respondido", resposta="confirma?")  # noqa: SLF001
    inicial._atualizar_item(1, status="enviado")  # noqa: SLF001
    enviados: list[str] = []
    retomado = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=comandos, intervalo_comandos_s=0.0),
        enviar_entrada=lambda texto: enviados.append(texto) or True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        retomar=True,
        log=lambda *_args: None,
    )

    assert retomado.executar() is False
    assert enviados == []
    checkpoint = json.loads(retomado.checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint["retomada_contexto"]["status"] == (
        "contexto_nao_reconstruivel_com_seguranca"
    )


def test_espelho_terminal_confirma_conteudo_no_disco(tmp_path) -> None:
    class Saida:
        encoding = "utf-8"

        def __init__(self) -> None:
            self.texto = ""

        def write(self, texto: str) -> int:
            self.texto += texto
            return len(texto)

        def flush(self) -> None:
            return None

        def isatty(self) -> bool:
            return False

    original = Saida()
    caminho = tmp_path / "terminal.log"
    espelho = EspelhoTerminalPersistente(original, caminho)
    espelho.write("mensagem enviada\n")
    espelho.write("resposta recebida\n")

    assert original.texto == "mensagem enviada\nresposta recebida\n"
    assert caminho.read_text(encoding="utf-8") == original.texto
    espelho.fechar()


def test_retomada_recusa_checkpoint_de_outro_roteiro(tmp_path) -> None:
    primeiro = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(comandos=("um",)),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    assert primeiro.checkpoint_path.is_file()

    with pytest.raises(ValueError, match="roteiro mudou"):
        RoteiroTesteConversaRuntime(
            ConfiguracaoRoteiro(comandos=("outro",)),
            enviar_entrada=lambda _texto: True,
            resultado_getter=lambda: {},
            diretorio_resultado=tmp_path,
            retomar=True,
            log=lambda *_args: None,
        )


def test_retomada_recusa_criterio_semantico_alterado_com_mesmos_comandos(
    tmp_path,
) -> None:
    comando = "continua"
    RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=(comando,),
            expectativas_semanticas={
                1: {"sem_comando": True, "nome": "sem_contexto"},
                comando: {"sem_comando": True},
            },
        ),
        enviar_entrada=lambda _texto: True,
        resultado_getter=lambda: {},
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )

    with pytest.raises(ValueError, match="roteiro mudou"):
        RoteiroTesteConversaRuntime(
            ConfiguracaoRoteiro(
                comandos=(comando,),
                expectativas_semanticas={
                    1: {
                        "intents_any": ("MEDIA_CONTROL",),
                        "nome": "com_contexto_musical",
                    },
                    comando: {"sem_comando": True},
                },
            ),
            enviar_entrada=lambda _texto: True,
            resultado_getter=lambda: {},
            diretorio_resultado=tmp_path,
            retomar=True,
            log=lambda *_args: None,
        )


def test_checkpoint_separa_resposta_de_execucao_e_avaliacao_semantica(
    tmp_path,
) -> None:
    holder: dict[str, RoteiroTesteConversaRuntime] = {}
    plano = {
        "fase": "tratado_prioritario",
        "comandos": [{
            "intent": "OPEN_URL",
            "status": "falha_execucao",
            "executou": False,
            "confirmado": False,
        }],
    }

    def enviar(_texto: str) -> bool:
        holder["runtime"].observar_resposta(
            "Não consegui confirmar a abertura.",
        )
        return True

    runtime = RoteiroTesteConversaRuntime(
        ConfiguracaoRoteiro(
            comandos=("abre o primeiro resultado",),
            timeout_resposta_s=1.0,
            intervalo_comandos_s=0.0,
        ),
        enviar_entrada=enviar,
        resultado_getter=lambda: plano,
        diretorio_resultado=tmp_path,
        log=lambda *_args: None,
    )
    holder["runtime"] = runtime

    assert runtime.executar() is True

    checkpoint = json.loads(runtime.checkpoint_path.read_text(encoding="utf-8"))
    avaliacao = checkpoint["itens"][0]["avaliacao"]
    assert checkpoint["criterio_conclusao"] == "transporte_resposta_e_voz"
    esperado = {
        "respondeu": True,
        "plano_observado": True,
        "quantidade_comandos": 1,
        "execucao": "nenhuma_etapa_executada",
        "confirmacao": "nenhuma_etapa_confirmada",
        "intencao_correta": "nao_avaliado",
        "fala_coerente": "sim",
    }
    assert {chave: avaliacao[chave] for chave in esperado} == esperado
    assert avaliacao["versao_avaliador"] == 16
    assert avaliacao["dominio"] == "browser"
    assert avaliacao["intents_observadas"] == ["OPEN_URL"]
    assert avaliacao["statuses_observados"] == ["falha_execucao"]
    assert avaliacao["erros_semanticos"] == []
    assert avaliacao["alertas_semanticos"] == [
        "dependencia_externa_nao_confirmada",
    ]
    conversa = runtime.conversa_path.read_text(encoding="utf-8")
    assert "`OPEN_URL` → `falha_execucao`" in conversa
    bruto = json.loads(runtime.planos_path.read_text(encoding="utf-8"))
    assert bruto["plano"] == plano
