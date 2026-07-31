from __future__ import annotations

from datetime import datetime

from mente_laylay.autonomia.motor_iniciativa import MotorIniciativaRuntime
from mente_laylay.autonomia.governanca_iniciativa import (
    decisao_permite_emissao,
    detectar_comando_governanca_iniciativa,
)
from mente_laylay.autonomia.sugestoes_sistema import (
    detectar_sugestao_indireta,
    registrar_sugestao_indireta,
)
from mente_laylay.memoria_mental.diagnostico_mente import (
    construir_diagnostico_mente,
    formatar_diagnostico_terminal,
)
from mente_laylay.memoria_mental.persistencia_memoria import (
    POLITICA_PERSISTENCIA_MENTE,
    PersistenciaMemoriaRuntime,
)
from mente_laylay.percepcao.monitor_janelas import MonitorJanelasRuntime
from mente_laylay.percepcao.ritmo_circadiano import RitmoCircadianoRuntime


def _motor(
    *, contexto=None, estado_inicial=None, agora=1000.0, logs=None,
    executor=None, desfazer=None, capacidade_getter=None,
):
    estado = dict(estado_inicial or {})
    runtime = MotorIniciativaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: dict(contexto or {}),
        modo="sombra",
        executor_acao_cb=executor,
        desfazer_acao_cb=desfazer,
        capacidade_getter=capacidade_getter,
        clock=lambda: agora,
        log=(logs if logs is not None else []).append,
    )
    return runtime, estado


def test_vontade_segura_consulta_mapa_e_aguarda_recurso_indisponivel() -> None:
    executadas = []
    runtime, estado = _motor(
        executor=lambda acao: executadas.append(acao) or {
            "ok": True, "confirmado": True, "status": "ligado",
        },
        capacidade_getter=lambda intent: {
            "intent": intent, "disponivel": False,
            "estado": "indisponivel", "motivo": "resultado_recente",
        },
    )
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)

    decisao = runtime.registrar({
        "chave": "luz:indisponivel", "tipo": "rotina", "dominio": "iot",
        "origem": "teste", "acao_proposta": {"intent": "TIME_LIGHT_ON"},
        "utilidade": 100, "confianca": 0.98, "risco": "baixo",
        "executavel": True, "reversivel": True,
    })

    assert decisao["decisao"] == "aguardar"
    assert "capacidade_indisponivel" in decisao["motivos"]
    assert decisao["seguranca"]["capacidade_disponivel"] is False
    assert estado["seguranca"]["bloqueios_capacidade"] == 1
    assert executadas == []


def test_vontade_segura_nunca_executa_acao_que_exige_confirmacao_humana() -> None:
    executadas = []
    runtime, estado = _motor(
        executor=lambda acao: executadas.append(acao) or {
            "ok": True, "confirmado": True,
        },
        capacidade_getter=lambda intent: {"intent": intent, "disponivel": True},
    )
    runtime.configurar_dominio("arquivos", "acao_reversivel", confirmacao_explicita=True)

    decisao = runtime.registrar({
        "chave": "arquivo:apagar", "tipo": "rotina", "dominio": "arquivos",
        "origem": "teste", "acao_proposta": {
            "intent": "DELETE_ITEM", "params": {"alvo": "rascunho.txt"},
        },
        "utilidade": 100, "confianca": 0.99, "risco": "baixo",
        "executavel": True, "reversivel": True,
    })

    assert decisao["decisao"] == "sugerir"
    assert "confirmacao_humana_obrigatoria" in decisao["motivos"]
    assert decisao["seguranca"]["confirmacao_humana"] is True
    assert estado["seguranca"]["bloqueios_confirmacao"] == 1
    assert executadas == []


def test_orcamento_limita_sugestoes_reais_sem_afetar_modo_sombra() -> None:
    estado = {}
    relogio = [1000.0]
    runtime = MotorIniciativaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {},
        clock=lambda: relogio[0],
        log=lambda _mensagem: None,
    )
    runtime.configurar_dominio("jogo", "sugestao", confirmacao_explicita=True)

    decisoes = []
    for indice in range(4):
        relogio[0] += 1.0
        decisoes.append(runtime.registrar({
            "chave": f"jogo:dica:{indice}", "tipo": "observacao", "dominio": "jogo",
            "origem": "teste", "utilidade": 80, "confianca": 0.95,
            "risco": "baixo", "momento_seguro": True,
        }))

    assert [item["decisao"] for item in decisoes] == [
        "sugerir", "sugerir", "sugerir", "aguardar",
    ]
    assert "orcamento_de_iniciativas_esgotado" in decisoes[-1]["motivos"]
    assert estado["seguranca"]["bloqueios_orcamento"] == 1


def test_modo_sombra_avalia_sem_conceder_execucao() -> None:
    runtime, estado = _motor(estado_inicial={"niveis": {"iot": 2}})

    decisao = runtime.registrar({
        "chave": "luz:noturna",
        "tipo": "rotina",
        "origem": "ritmo_circadiano",
        "dominio": "iot",
        "acao_proposta": "IOT_CONTROL",
        "utilidade": 100,
        "confianca": 0.95,
        "risco": "baixo",
        "executavel": True,
        "reversivel": True,
    })

    assert decisao["acao_simulada"] == "executar"
    assert decisao["decisao"] == "sombra_executar"
    assert estado["contadores"]["executariam"] == 1


def test_governanca_so_muda_permissao_com_confirmacao_explicita() -> None:
    runtime, _estado = _motor()
    negado = runtime.configurar_dominio("iluminação", "sugestao")
    assert negado == {"ok": False, "motivo": "confirmacao_explicita_necessaria"}
    assert runtime.permissoes_atuais()["dominios"] == {}

    aceito = runtime.configurar_dominio(
        "iluminação", "sugestao", confirmacao_explicita=True,
    )
    assert aceito["ok"] is True
    assert aceito["dominio"] == "iot"
    assert runtime.permissoes_atuais() == {
        "modo": "sugestao", "dominios": {"iot": "sugestao"},
    }


def test_governanca_detecta_apenas_ordem_clara() -> None:
    assert detectar_comando_governanca_iniciativa("mostra as permissões da autonomia") == {
        "acao": "status", "dominio": "", "permissao": "",
    }
    assert detectar_comando_governanca_iniciativa(
        "permita sugestões de iluminação"
    )["permissao"] == "sugestao"
    assert detectar_comando_governanca_iniciativa(
        "autorize ações reversíveis de iluminação"
    )["permissao"] == "acao_reversivel"
    assert detectar_comando_governanca_iniciativa(
        "bloqueie a autonomia de iluminação"
    )["permissao"] == "bloqueado"
    assert detectar_comando_governanca_iniciativa(
        "acho legal quando você sugere música"
    ) is None


def test_governanca_detecta_perfil_seguro_somente_com_autorizacao_clara() -> None:
    assert detectar_comando_governanca_iniciativa(
        "ative a autonomia segura"
    ) == {
        "acao": "configurar_perfil", "perfil": "seguro",
        "dominio": "", "permissao": "acao_reversivel",
    }
    assert detectar_comando_governanca_iniciativa(
        "pode executar ações reversíveis quando forem necessárias"
    )["acao"] == "configurar_perfil"
    assert detectar_comando_governanca_iniciativa(
        "desative a autonomia segura"
    )["permissao"] == "bloqueado"
    assert detectar_comando_governanca_iniciativa(
        "acho interessante ter autonomia segura"
    ) is None


def test_perfil_seguro_exige_confirmacao_e_libera_so_dominios_auditados() -> None:
    runtime, _estado = _motor()
    assert runtime.configurar_perfil_seguro()["ok"] is False

    resultado = runtime.configurar_perfil_seguro(confirmacao_explicita=True)

    assert resultado["ok"] is True
    assert resultado["dominios"] == ["iot", "musica", "conforto"]
    assert runtime.permissoes_atuais() == {
        "modo": "autorizado",
        "dominios": {
            "conforto": "acao_reversivel",
            "iot": "acao_reversivel",
            "musica": "acao_reversivel",
        },
    }
    assert "arquivos" not in runtime.permissoes_atuais()["dominios"]
    assert "navegador" not in runtime.permissoes_atuais()["dominios"]


def test_perfil_seguro_padrao_nao_reativa_dominio_bloqueado_pelo_usuario() -> None:
    runtime, _estado = _motor()
    runtime.configurar_dominio(
        "musica", "bloqueado", confirmacao_explicita=True,
    )

    resultado = runtime.ativar_perfil_seguro_padrao()

    assert resultado["ativados"] == ["iot", "conforto"]
    assert resultado["preservados"] == ["musica"]
    assert runtime.permissoes_atuais() == {
        "modo": "autorizado",
        "dominios": {
            "conforto": "acao_reversivel",
            "iot": "acao_reversivel",
            "musica": "bloqueado",
        },
    }
    estado = runtime.snapshot()
    assert estado["permissoes"]["iot"]["origem"] == "padrao_seguro"
    assert estado["permissoes"]["musica"]["origem"] == "usuario_explicito"


def test_perfil_seguro_executa_necessidade_clara_mas_nao_baixa_confianca() -> None:
    executadas = []
    runtime, _estado = _motor(
        estado_inicial={"niveis": {}},
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "volume_ajustado",
        },
    )
    runtime.configurar_perfil_seguro(confirmacao_explicita=True)

    clara = runtime.registrar({
        "chave": "som:alto", "tipo": "preferencia_contextual",
        "dominio": "conforto", "origem": "fala_indireta_confiavel",
        "acao_proposta": {"intent": "VOLUME_RELATIVE", "params": {"delta": -10}},
        "utilidade": 100, "confianca": 0.95, "risco": "baixo",
        "executavel": True, "reversivel": True,
    })
    incerta = runtime.registrar({
        "chave": "som:talvez", "tipo": "preferencia_contextual",
        "dominio": "conforto", "origem": "observacao",
        "acao_proposta": {"intent": "VOLUME_RELATIVE", "params": {"delta": 10}},
        "utilidade": 100, "confianca": 0.89, "risco": "baixo",
        "executavel": True, "reversivel": True,
    })

    assert clara["decisao"] == "executado"
    assert incerta["decisao"] != "executado"
    assert executadas == [{
        "intent": "VOLUME_RELATIVE",
        "params": {"delta": -10, "origem": "autonomia"},
    }]


def test_preferencia_de_cor_no_horario_vira_acao_indireta_de_alta_confianca() -> None:
    resultado = detectar_sugestao_indireta(
        "eu gosto de luz roxa nesse horário",
    )

    assert resultado["params"]["confianca"] == 0.94
    assert resultado["params"]["execucao_autonoma_elegivel"] is True
    assert resultado["params"]["acao_sugerida"] == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ajustar_cor", "alvo": "lampada_quarto",
            "cor": "roxo", "rgb": (128, 0, 255),
            "origem": "usuario_indireto",
        },
    }
    assert detectar_sugestao_indireta(
        "minha irmã gosta de luz roxa nesse horário",
    ) is None


def test_necessidades_indiretas_seguras_recebem_dominio_e_confianca() -> None:
    calor = detectar_sugestao_indireta("estou com muito calor")
    escuro = detectar_sugestao_indireta("está muito escuro aqui")
    som = detectar_sugestao_indireta("o som está alto demais")

    assert calor["params"]["confianca"] == 0.96
    assert calor["params"]["acao_sugerida"]["params"]["alvo"] == "tomada_ventilador"
    assert escuro["params"]["acao_sugerida"]["params"]["acao"] == "ligar"
    assert som["params"]["dominio"] == "conforto"
    assert som["params"]["acao_sugerida"] == {
        "intent": "VOLUME_RELATIVE",
        "params": {"delta": -10, "origem": "usuario_indireto"},
    }


def test_frio_nao_herda_lampada_como_alvo_termico() -> None:
    resultado = detectar_sugestao_indireta(
        "estou com frio",
        {"ultimo_dispositivo_iot": "lampada_quarto", "ultimo_estado_iot": False},
    )

    assert resultado["params"]["acao_sugerida"]["params"] == {
        "acao": "desligar",
        "alvo": "tomada_ventilador",
        "origem": "usuario_indireto",
    }


def test_frases_ambiguas_nao_viram_comandos_indiretos() -> None:
    assert detectar_sugestao_indireta("esse prédio é muito alto") is None
    assert detectar_sugestao_indireta("minha irmã está com calor") is None
    assert detectar_sugestao_indireta("gosto de filmes escuros") is None
    assert detectar_sugestao_indireta("essa música é muito boa") is None


def test_desejo_musical_indireto_vira_busca_governada() -> None:
    resultado = detectar_sugestao_indireta("estou a fim de ouvir MF DOOM")

    assert resultado["params"]["dominio"] == "musica"
    assert resultado["params"]["confianca"] == 0.95
    assert resultado["params"]["acao_sugerida"] == {
        "intent": "MUSIC_SEARCH",
        "params": {"query": "mf doom", "origem": "usuario_indireto"},
    }


def test_incomodacao_musical_e_faixa_inadequada_viram_controles_distintos() -> None:
    pausa = detectar_sugestao_indireta("essa música está me distraindo")
    proxima = detectar_sugestao_indireta("não gostei dessa música")
    retomar = detectar_sugestao_indireta("a música parou")

    assert pausa["params"]["acao_sugerida"]["params"]["acao"] == "pause"
    assert proxima["params"]["acao_sugerida"]["params"]["acao"] == "next"
    assert proxima["params"]["confianca"] == 0.92
    assert retomar["params"]["acao_sugerida"]["params"]["acao"] == "play"


def test_fome_sem_comida_recomenda_ifood_sem_execucao_autonoma() -> None:
    resultado = detectar_sugestao_indireta("estou com fome mas não tem nada pronto")

    assert resultado["params"]["acao_sugerida"]["intent"] == "OPEN_URL"
    assert resultado["params"]["acao_sugerida"]["params"]["alvo"] == "https://www.ifood.com.br"
    assert resultado["params"]["execucao_autonoma_elegivel"] is False
    assert resultado["params"]["confianca"] == 0.96


def test_musica_indireta_executa_somente_com_permissao_musical() -> None:
    executadas = []
    runtime, _estado = _motor(
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "musica_aberta",
        },
    )
    runtime.configurar_dominio("iot", "sugestao", confirmacao_explicita=True)
    detectada = detectar_sugestao_indireta("queria ouvir um rock pesado")

    primeira = runtime.registrar({
        "tipo": "preferencia_contextual", "origem": "fala_indireta_confiavel",
        "dominio": "musica", "confianca": 0.95, "utilidade": 100,
        "risco": "baixo", "executavel": True, "reversivel": True,
        "acao_proposta": detectada["params"]["acao_sugerida"],
    })
    runtime.configurar_dominio("musica", "acao_reversivel", confirmacao_explicita=True)
    segunda = runtime.registrar({
        "tipo": "preferencia_contextual", "origem": "fala_indireta_confiavel",
        "dominio": "musica", "confianca": 0.95, "utilidade": 100,
        "risco": "baixo", "executavel": True, "reversivel": True,
        "acao_proposta": detectada["params"]["acao_sugerida"],
    })

    assert primeira["decisao"] == "bloqueado_permissao"
    assert segunda["decisao"] == "executado"
    assert executadas[0]["intent"] == "MUSIC_SEARCH"


def test_fala_indireta_94_executa_com_permissao_mesmo_durante_conversa() -> None:
    executadas = []
    runtime, _estado = _motor(
        contexto={"turno_ativo": True, "conversa_ativa": True},
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "cor_ajustada",
        },
    )
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)
    detectada = detectar_sugestao_indireta("eu gosto de luz roxa nesse horario")

    tratado = registrar_sugestao_indireta(
        {"registrar_oportunidade": runtime.registrar}, detectada,
    )

    assert tratado is True
    assert executadas[0]["params"]["acao"] == "ajustar_cor"
    assert runtime.snapshot()["ultima_decisao"]["confianca"] == 0.94


def test_calor_executa_ventilador_com_permissao_iot() -> None:
    executadas = []
    runtime, _estado = _motor(
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "ligado",
        },
    )
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)

    tratado = registrar_sugestao_indireta(
        {"registrar_oportunidade": runtime.registrar},
        detectar_sugestao_indireta("estou com calor"),
    )

    assert tratado is True
    assert executadas[0] == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ligar", "alvo": "tomada_ventilador",
            "origem": "autonomia", "confirmado": True,
        },
    }


def test_volume_indireto_executa_so_com_permissao_de_conforto() -> None:
    executadas = []
    runtime, _estado = _motor(
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "volume_ajustado",
        },
    )
    runtime.configurar_dominio("conforto", "acao_reversivel", confirmacao_explicita=True)

    registrar_sugestao_indireta(
        {"registrar_oportunidade": runtime.registrar},
        detectar_sugestao_indireta("a música está muito baixa"),
    )

    assert executadas[0] == {
        "intent": "VOLUME_RELATIVE",
        "params": {"delta": 10, "origem": "autonomia"},
    }


def test_intent_consequente_nao_executa_mesmo_com_confianca_alta() -> None:
    executadas = []
    runtime, _estado = _motor(
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True,
        },
    )
    runtime.configurar_dominio("janelas", "acao_reversivel", confirmacao_explicita=True)
    decisao = runtime.registrar({
        "tipo": "preferencia_contextual", "origem": "fala_indireta_confiavel",
        "dominio": "janelas", "confianca": 0.99, "utilidade": 100,
        "risco": "baixo", "executavel": True, "reversivel": True,
        "acao_proposta": {"intent": "APP_OPEN", "params": {"nome_app": "chrome"}},
    })

    assert decisao["decisao"] != "executado"
    assert executadas == []


def test_confianca_89_nunca_executa_acao_autonoma() -> None:
    executadas = []
    runtime, _estado = _motor(
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True,
        },
    )
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)
    decisao = runtime.registrar({
        "chave": "luz:cor:incerta", "tipo": "preferencia_contextual",
        "origem": "fala_indireta_confiavel", "dominio": "iot",
        "confianca": 0.89, "utilidade": 100, "risco": "baixo",
        "executavel": True, "reversivel": True,
        "acao_proposta": {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": "ajustar_cor", "alvo": "lampada_quarto",
                "cor": "roxo", "rgb": (128, 0, 255),
            },
        },
    })

    assert decisao["decisao"] == "sugerir"
    assert executadas == []


def test_comando_indireto_pode_ser_repetido_depois_de_autorizar_dominio() -> None:
    executadas = []
    runtime, _estado = _motor(
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "cor_ajustada",
        },
    )
    runtime.configurar_dominio("jogo", "sugestao", confirmacao_explicita=True)
    oportunidade = {
        "chave": "preferencia:luz:roxa", "tipo": "preferencia_contextual",
        "origem": "fala_indireta_confiavel", "dominio": "iot",
        "confianca": 0.94, "utilidade": 100, "risco": "baixo",
        "executavel": True, "reversivel": True,
        "acao_proposta": {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": "ajustar_cor", "alvo": "lampada_quarto",
                "cor": "roxo", "rgb": (128, 0, 255),
            },
        },
    }

    primeira = runtime.registrar(oportunidade)
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)
    segunda = runtime.registrar(oportunidade)

    assert primeira["decisao"] == "bloqueado_permissao"
    assert segunda["decisao"] == "executado"
    assert len(executadas) == 1


def test_permissao_de_sugestao_nunca_vira_execucao() -> None:
    runtime, _estado = _motor(estado_inicial={"niveis": {"iot": 2}})
    runtime.configurar_dominio("iot", "sugestao", confirmacao_explicita=True)
    decisao = runtime.registrar({
        "chave": "luz:noturna", "tipo": "rotina", "dominio": "iot",
        "origem": "teste", "acao_proposta": "IOT_CONTROL", "utilidade": 100,
        "risco": "baixo", "executavel": True, "reversivel": True,
    })
    assert decisao["decisao"] == "sugerir"
    assert decisao["permissao"] == "sugestao"


def test_acao_autonoma_exige_permissao_reversibilidade_e_baixo_risco() -> None:
    runtime, _estado = _motor(
        estado_inicial={"niveis": {"iot": 2}},
        executor=lambda _acao: {
            "ok": True, "confirmado": True, "status": "ligado",
            "desfazer": {
                "intent": "IOT_CONTROL",
                "params": {"acao": "desligar", "alvo": "lampada_quarto"},
            },
        },
    )
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)
    decisao = runtime.registrar({
        "chave": "luz:noturna", "tipo": "rotina", "dominio": "iot",
        "origem": "teste", "acao_proposta": {"intent": "TIME_LIGHT_ON"}, "utilidade": 100,
        "confianca": 0.95,
        "risco": "baixo", "executavel": True, "reversivel": True,
    })
    assert decisao["decisao"] == "executado"
    assert decisao["execucao"]["confirmado"] is True
    assert decisao_permite_emissao(decisao) is False

    bloqueada = runtime.registrar({
        "chave": "luz:irreversivel", "tipo": "rotina", "dominio": "iot",
        "origem": "teste", "acao_proposta": "IOT_CONTROL", "utilidade": 100,
        "risco": "baixo", "executavel": True, "reversivel": False,
    })
    assert bloqueada["decisao"] == "sugerir"


def test_modo_jogo_rebaixa_rotina_para_espera() -> None:
    runtime, _estado = _motor(contexto={"modo_jogo_ativo": True})

    decisao = runtime.registrar({
        "chave": "rotina:jogo",
        "tipo": "rotina",
        "origem": "monitor_janelas",
        "utilidade": 62,
        "risco": "baixo",
        "reversivel": True,
    })

    assert decisao["acao_simulada"] == "aguardar"
    assert "modo_jogo" in decisao["motivos"]


def test_inventario_em_momento_seguro_pode_sugerir_durante_jogo() -> None:
    runtime, _estado = _motor(contexto={
        "modo_jogo_ativo": True, "conversa_ativa": True,
    })
    runtime.configurar_dominio("jogo", "sugestao", confirmacao_explicita=True)

    decisao = runtime.registrar({
        "chave": "inventario:botas:upgrade", "tipo": "observacao",
        "dominio": "jogo", "origem": "visao_inventario_jogo",
        "utilidade": 76, "risco": "baixo", "momento_seguro": True,
    })

    assert decisao["decisao"] == "sugerir"
    assert "momento_seguro_jogo" in decisao["motivos"]
    assert "modo_jogo" not in decisao["motivos"]
    assert "conversa_ativa" not in decisao["motivos"]


def test_governanca_reconhece_dominio_de_jogo() -> None:
    pedido = detectar_comando_governanca_iniciativa(
        "permita sugestões de inventário no jogo"
    )

    assert pedido == {
        "acao": "configurar", "dominio": "jogo", "permissao": "sugestao",
    }


def test_risco_alto_impede_sugestao_mesmo_com_utilidade_alta() -> None:
    runtime, _estado = _motor()

    decisao = runtime.registrar({
        "chave": "arquivo:perigoso",
        "tipo": "rotina",
        "origem": "sistema",
        "utilidade": 100,
        "risco": "alto",
        "executavel": True,
    })

    assert decisao["acao_simulada"] == "ignorar"


def test_oportunidade_repetida_nao_polui_historico() -> None:
    runtime, estado = _motor()
    oportunidade = {
        "chave": "mesma:oportunidade", "tipo": "observacao",
        "origem": "teste", "utilidade": 60, "risco": "baixo",
    }

    primeira = runtime.registrar(oportunidade)
    segunda = runtime.registrar(oportunidade)

    assert not primeira.get("duplicada")
    assert segunda["duplicada"] is True
    assert len(estado["historico"]) == 1
    assert estado["contadores"]["duplicadas"] == 1


def test_historico_tecnico_permanece_limitado() -> None:
    estado = {}
    relogio = [1000.0]
    runtime = MotorIniciativaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {},
        clock=lambda: relogio[0],
        limite_historico=5,
        log=lambda _mensagem: None,
    )
    for indice in range(8):
        relogio[0] += 1.0
        runtime.registrar({
            "chave": f"evento:{indice}", "tipo": "observacao",
            "origem": "teste", "utilidade": 45, "risco": "baixo",
        })

    assert len(estado["historico"]) == 5
    assert estado["historico"][0]["assinatura"] == "evento:3"


def test_auditoria_exige_amostra_antes_de_liberar_teste_de_sugestao() -> None:
    runtime, estado = _motor()

    for indice in range(5):
        runtime.registrar({
            "chave": f"iot:{indice}", "tipo": "rotina", "dominio": "iot",
            "origem": "teste", "utilidade": 70, "risco": "baixo",
        })

    auditoria = runtime.avaliar_prontidao()
    assert auditoria["status"] == "observando"
    assert auditoria["dominios"]["iot"]["motivos"] == ["amostra_insuficiente"]
    assert auditoria["autoriza_execucao"] is False
    assert estado["auditoria"] == auditoria


def test_auditoria_marca_dominio_consistente_apenas_como_candidato() -> None:
    runtime, _estado = _motor()

    for indice in range(6):
        runtime.registrar({
            "chave": f"iot:{indice}", "tipo": "rotina", "dominio": "iot",
            "origem": "teste", "utilidade": 70, "risco": "baixo",
        })

    auditoria = runtime.avaliar_prontidao()
    dominio = auditoria["dominios"]["iot"]
    assert auditoria["status"] == "candidato_sugestao"
    assert dominio["status"] == "candidato_sugestao"
    assert dominio["amostras"] == 6
    assert dominio["acionaveis"] == 6
    assert auditoria["autoriza_execucao"] is False


def test_auditoria_bloqueia_fonte_que_repete_oportunidades_demais() -> None:
    runtime, _estado = _motor()
    for indice in range(6):
        oportunidade = {
            "chave": f"janela:{indice}", "tipo": "contexto_janela",
            "dominio": "janelas", "origem": "teste", "utilidade": 70,
            "risco": "baixo",
        }
        runtime.registrar(oportunidade)
        runtime.registrar(oportunidade)
        runtime.registrar(oportunidade)

    auditoria = runtime.avaliar_prontidao()
    assert auditoria["taxa_duplicacao"] > 0.5
    assert auditoria["dominios"]["janelas"]["status"] == "observando"
    assert "fonte_muito_repetitiva" in auditoria["dominios"]["janelas"]["motivos"]


def test_persistencia_inclui_apenas_estado_sanitizado_da_iniciativa() -> None:
    dominios = {
        "mental": {"iniciativa_autonoma": {
            "modo": "sombra", "historico": [{"tipo": "rotina"}],
            "contadores": {"avaliadas": 1},
        }, "coordenador_oportunidades": {
            "aprendizado": {
                "jogo:observacao:jogo:livre": {
                    "aceitas": 0, "recusadas": 3, "amostras": 3,
                    "ajuste_utilidade": -8, "status": "preferencia_emergente",
                    "descricao": "texto que não deve persistir",
                },
            },
            "contadores": {"feedbacks": 3, "recusadas": 3},
            "ultima": {"descricao": "decisão temporária"},
            "recentes": [{"descricao": "evento temporário"}],
            "objetivos": [{"nome": "objetivo da sessão"}],
        }},
        "conversacional": {},
        "memoria_conversa": {},
    }
    runtime = PersistenciaMemoriaRuntime(
        memoria_sqlite=object(),
        base_system_prompt="",
        estado_obter=lambda dominio, chave, padrao=None: dominios.get(dominio, {}).get(chave, padrao),
        estado_atualizar=lambda _dominio, **_campos: None,
    )

    snapshot = runtime.snapshot()

    assert snapshot["iniciativa_autonoma"]["modo"] == "sombra"
    assert "iniciativa_autonoma" in POLITICA_PERSISTENCIA_MENTE["duravel"]
    assert "ultima_entrada" not in snapshot["iniciativa_autonoma"]
    aprendizado = snapshot["coordenador_oportunidades"]
    assert "coordenador_oportunidades" in POLITICA_PERSISTENCIA_MENTE["duravel"]
    assert aprendizado["aprendizado"]["jogo:observacao:jogo:livre"]["ajuste_utilidade"] == -8
    assert "descricao" not in aprendizado["aprendizado"]["jogo:observacao:jogo:livre"]
    assert "ultima" not in aprendizado
    assert "recentes" not in aprendizado
    assert "objetivos" not in aprendizado


def test_ritmo_circadiano_publica_oportunidade_sem_mudar_confirmacao() -> None:
    estado = {}
    continuidades = {"comando_sugerido_estado": "NONE"}
    oportunidades = []
    falas = []
    runtime = RitmoCircadianoRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.update(novo),
        continuidades_get=lambda chave, padrao=None: continuidades.get(chave, padrao),
        continuidades_update=lambda **campos: continuidades.update(campos),
        agendar_fala=lambda *args, **kwargs: falas.append((args, kwargs)) or True,
        interacao_iniciada=lambda: True,
        conversa_ativa=lambda: False,
        registrar_oportunidade=oportunidades.append,
        agora_cb=lambda: datetime(2026, 7, 16, 19, 10),
    )

    resultado = runtime.executar_ciclo()

    assert resultado["status"] == "sugestao_agendada"
    assert oportunidades[0]["acao_proposta"]["intent"] == "TIME_LIGHT_ON"
    assert oportunidades[0]["acao_proposta"]["params"]["alvo"] == "lampada_quarto"
    assert continuidades["comando_sugerido_estado"] == "NONE"


def test_ritmo_circadiano_respeita_dominio_bloqueado_pela_governanca() -> None:
    estado = {}
    falas = []
    runtime = RitmoCircadianoRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.update(novo),
        continuidades_get=lambda _chave, padrao=None: padrao,
        continuidades_update=lambda **_campos: None,
        agendar_fala=lambda *args, **kwargs: falas.append((args, kwargs)) or True,
        interacao_iniciada=lambda: True,
        conversa_ativa=lambda: False,
        registrar_oportunidade=lambda _dados: {"decisao": "bloqueado_permissao"},
        agora_cb=lambda: datetime(2026, 7, 16, 19, 10),
    )

    resultado = runtime.executar_ciclo()
    assert resultado["status"] == "bloqueado_permissao"
    assert falas == []


def test_ritmo_executa_luz_sem_emitir_sugestao_apos_autorizacao_explicita() -> None:
    executadas = []
    motor, _estado_motor = _motor(
        executor=lambda acao: executadas.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "ligado",
        },
    )
    motor.configurar_dominio("iluminação", "acao_reversivel", confirmacao_explicita=True)
    estado_ritmo = {}
    falas = []
    runtime = RitmoCircadianoRuntime(
        estado_get=lambda: estado_ritmo,
        estado_set=lambda novo: estado_ritmo.update(novo),
        continuidades_get=lambda _chave, padrao=None: padrao,
        continuidades_update=lambda **_campos: None,
        agendar_fala=lambda *args, **kwargs: falas.append((args, kwargs)) or True,
        interacao_iniciada=lambda: True,
        conversa_ativa=lambda: False,
        registrar_oportunidade=motor.registrar,
        agora_cb=lambda: datetime(2026, 7, 16, 19, 10),
    )

    resultado = runtime.executar_ciclo()

    assert resultado["status"] == "executado_autonomamente"
    assert falas == []
    assert estado_ritmo["sugestoes_emitidas"]["luz_anoitecer"] == "2026-07-16"
    assert executadas == [{
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ligar", "alvo": "lampada_quarto",
            "origem": "autonomia", "confirmado": True,
        },
    }]


def test_monitor_de_janelas_publica_oportunidade_de_rotina() -> None:
    oportunidades = []
    falas = []
    runtime = MonitorJanelasRuntime(
        capturar_janela=lambda: {},
        atualizar_contexto=lambda _retrato: None,
        continuidade_get=lambda _chave, padrao=None: padrao,
        continuidade_update=lambda **_campos: None,
        esta_falando=lambda: False,
        conversa_ativa=lambda: False,
        ultimo_proativo_get=lambda: 0.0,
        ultimo_proativo_set=lambda _valor: None,
        sugestoes_bloqueadas_get=lambda: {},
        janela_em_tela_cheia=lambda _janela: False,
        detectar_gatilho=lambda *_args: ("", None),
        fala_gatilho=lambda _gatilho: "",
        falar=lambda *args: falas.append(args),
        registrar_oportunidade=oportunidades.append,
        clock=lambda: 2000.0,
    )

    assert runtime.sugerir_assunto("Programação", agora=2000.0) is True
    assert oportunidades[0]["acao_proposta"]["intent"] == "SYS_MODE_CODE"
    assert falas


def test_allowlist_rebaixa_acao_nao_auditada_para_sugestao() -> None:
    runtime, _estado = _motor(
        estado_inicial={"niveis": {"rotina": 2}},
        executor=lambda _acao: {"ok": True, "confirmado": True},
    )
    runtime.configurar_dominio("rotina", "acao_reversivel", confirmacao_explicita=True)

    decisao = runtime.registrar({
        "chave": "codigo:automatico", "tipo": "rotina", "dominio": "rotina",
        "origem": "teste", "acao_proposta": {"intent": "SYS_MODE_CODE"},
        "utilidade": 100, "confianca": 0.95,
        "risco": "baixo", "executavel": True, "reversivel": True,
    })

    assert decisao["decisao"] == "sugerir"
    assert "intent_nao_elegivel" in decisao["motivos"]


def test_falhas_repetidas_abrem_circuito_do_dominio() -> None:
    runtime, estado = _motor(
        estado_inicial={"niveis": {"iot": 2}},
        executor=lambda _acao: {"ok": False, "confirmado": False, "status": "indisponivel"},
    )
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)
    for indice in range(3):
        resultado = runtime.registrar({
            "chave": f"luz:falha:{indice}", "tipo": "rotina", "dominio": "iot",
                "origem": "teste", "acao_proposta": {"intent": "TIME_LIGHT_ON"},
                "utilidade": 100, "confianca": 0.95,
                "risco": "baixo", "executavel": True, "reversivel": True,
        })
        assert resultado["decisao"] == "execucao_falhou"

    bloqueada = runtime.registrar({
        "chave": "luz:quarta", "tipo": "rotina", "dominio": "iot",
        "origem": "teste", "acao_proposta": {"intent": "TIME_LIGHT_ON"},
        "utilidade": 100, "confianca": 0.95,
        "risco": "baixo", "executavel": True, "reversivel": True,
    })
    assert bloqueada["decisao"] == "bloqueado_circuito"
    assert estado["execucao"]["circuitos_ate"]["iot"] > 1000.0


def test_desfazer_exige_ordem_explicita_e_usa_token_sanitizado() -> None:
    reversoes = []
    runtime, estado = _motor(
        estado_inicial={"niveis": {"iot": 2}},
        executor=lambda _acao: {
            "ok": True, "confirmado": True, "status": "ligado",
            "desfazer": {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "desligar", "alvo": "lampada_quarto",
                    "segredo": "nao persistir",
                },
            },
        },
        desfazer=lambda acao: reversoes.append(dict(acao)) or {
            "ok": True, "confirmado": True, "status": "desligado",
        },
    )
    runtime.configurar_dominio("iot", "acao_reversivel", confirmacao_explicita=True)
    runtime.registrar({
        "chave": "luz:reversivel", "tipo": "rotina", "dominio": "iot",
        "origem": "teste", "acao_proposta": {"intent": "TIME_LIGHT_ON"},
        "utilidade": 100, "confianca": 0.95,
        "risco": "baixo", "executavel": True, "reversivel": True,
    })

    assert runtime.desfazer_ultima()["motivo"] == "confirmacao_explicita_necessaria"
    resultado = runtime.desfazer_ultima(confirmacao_explicita=True)
    assert resultado["ok"] is True
    assert "segredo" not in reversoes[0]["params"]
    assert estado["execucao"]["ultimo_desfazer"] == {}
    assert detectar_comando_governanca_iniciativa(
        "desfaça sua última ação autônoma"
    )["acao"] == "desfazer"


def test_diagnostico_expoe_apenas_resumo_da_iniciativa() -> None:
    estado = {
        "mental": {"iniciativa_autonoma": {
            "modo": "sombra",
            "seguranca": {
                "modo": "vontade_segura", "bloqueios_capacidade": 2,
                "bloqueios_confirmacao": 1, "bloqueios_orcamento": 1,
                "simulacoes_orcamento": 4, "segredo": "não expor",
            },
            "contadores": {"avaliadas": 4, "duplicadas": 1},
            "ultima_decisao": {
                "tipo": "ritmo_temporal", "decisao": "sombra_sugerir",
                "pontuacao": 63, "confianca": 0.94,
                "risco": "baixo", "descricao": "segredo privado",
            },
            "auditoria": {
                "status": "candidato_sugestao", "amostras": 12,
                "dominios_candidatos": 1, "taxa_duplicacao": 0.125,
                "autoriza_execucao": True,
                "dominios": {"iot": {"segredo": "não expor"}},
            },
        }, "coordenador_oportunidades": {
            "contadores": {
                "recebidas": 8, "encaminhadas": 5,
                "duplicadas_semanticas": 2, "baixa_confianca": 1,
                "alinhadas_objetivo": 3, "feedbacks": 7,
                "aceitas": 2, "recusadas": 3, "silencios": 1, "correcoes": 1,
            },
            "aprendizado": {
                "jogo:observacao:jogo:livre": {"ajuste_utilidade": -6},
            },
            "objetivos": [{"nome": "segredo", "tags": ["privado"]}],
            "ultima": {"decisao": "sugerir", "descricao": "não expor"},
        }},
        "conversacional": {}, "percepcao": {}, "continuidades": {},
    }

    diagnostico = construir_diagnostico_mente(estado, {})
    texto = formatar_diagnostico_terminal(diagnostico)

    assert diagnostico["iniciativa"]["avaliadas"] == 4
    assert "modo=sombra" in texto
    assert "sombra_sugerir" in texto
    assert "confiança=94%" in texto
    assert diagnostico["iniciativa"]["auditoria"]["status"] == "candidato_sugestao"
    assert diagnostico["iniciativa"]["auditoria"]["autoriza_execucao"] is False
    assert "duplicação=12.5%" in texto
    assert "vontade segura: modo=vontade_segura" in texto
    assert "capacidade_bloqueada=2" in texto
    assert diagnostico["iniciativa"]["vontade_segura"]["autoriza_execucao"] is False
    assert diagnostico["iniciativa"]["coordenacao"] == {
        "recebidas": 8, "encaminhadas": 5, "duplicadas": 2,
        "baixa_confianca": 1, "alinhadas_objetivo": 3,
        "feedbacks": 7, "aceitas": 2, "recusadas": 3,
        "silencios": 1, "correcoes": 1, "perfis_maduros": 1,
        "objetivos_ativos": 1, "ultima_decisao": "sugerir",
    }
    assert "coordenação de oportunidades" in texto
    assert "segredo privado" not in texto
    assert "não expor" not in texto
