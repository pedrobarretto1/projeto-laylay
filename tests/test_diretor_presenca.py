from __future__ import annotations

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.percepcao.visao_jogo.presenca_visual import extrair_presenca_visual


def _turno_evento(evento):
    contrato = {
        "funcao": "reacao_evento",
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoriza_execucao": False,
        "roteiro_concreto": {
            "estrategia": "reacao_evento",
            "autoriza_execucao": False,
        },
    }
    return {
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
        "contrato_fala": contrato,
    }


def _materializador_entregue(falas, contextos=None):
    def processar(_turno, **contexto):
        fala = "Comentário gerado depois da cognição."
        contexto["ao_materializar_fala"](fala)
        falas.append((fala, contexto["emocao"], contexto["nivel"]))
        if contextos is not None:
            contextos.append(dict(contexto))
        contexto["ao_concluir"](True, "entregue")
        return {
            "status": "agendada",
            "fala": fala,
            "agendada": True,
            "emissao_fisica": False,
            "autoriza_execucao": False,
            "comandos_descartados": 0,
        }

    return processar


def _runtime(*, contexto=None):
    estado = {}
    falas = []
    oportunidades = []
    feedbacks = []
    agora = [1000.0]
    contexto_base = {
        "modo_jogo_ativo": True,
        "turno_ativo": False,
        "is_speaking": False,
        "ultima_entrada_ts": 0.0,
    }
    contexto_base.update(contexto or {})

    runtime = DiretorPresencaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: contexto_base,
        registrar_oportunidade=lambda dados: oportunidades.append(dict(dados)) or {"decisao": "sugerir"},
        processar_evento_cognitivo=_turno_evento,
        processar_proposta_comunicativa=_materializador_entregue(falas),
        registrar_feedback=lambda *args, **kwargs: feedbacks.append((args, kwargs)),
        clock=lambda: agora[0],
        log=lambda _texto: None,
    )
    return runtime, estado, falas, oportunidades, feedbacks, agora


def test_dica_de_jogo_exige_evidencia_e_momento_seguro() -> None:
    runtime, estado, falas, oportunidades, _feedbacks, _agora = _runtime()
    evento = {
        "dominio": "jogo", "categoria": "dica", "fala": "Esse bônus conversa com seu dano de gelo.",
        "confianca": 0.94, "fundamentada": True, "momento_seguro": True,
        "evidencias": ["bônus de frio visível", "build de gelo confirmada"], "chave": "frio:monge",
    }

    resultado = runtime.considerar(evento)

    assert resultado["status"] == "proposta_cognitiva"
    assert falas and oportunidades
    assert estado["contadores"]["emitidas"] == 1


def test_diretor_identifica_fala_como_presenca_de_jogo() -> None:
    recebidos = []
    falas = []
    runtime = DiretorPresencaRuntime(
        contexto_getter=lambda: {
            "modo_jogo_ativo": True, "turno_ativo": False,
            "is_speaking": False, "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=_turno_evento,
        processar_proposta_comunicativa=_materializador_entregue(falas, recebidos),
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = runtime.considerar({
        "dominio": "jogo", "categoria": "companhia",
        "fala": "Esse lugar ficou bonito, hein.", "confianca": 0.9,
        "momento_seguro": True, "evidencias": ["nova área visível"],
        "chave": "area-nova",
    })

    assert resultado["status"] == "proposta_cognitiva"
    assert recebidos[0]["dominio"] == "jogo"
    assert recebidos[0]["categoria"] == "companhia"


def test_diretor_encaminha_callback_de_entrega_da_oferta() -> None:
    recebidos = []
    falas = []
    callback = lambda *args: recebidos.append(args)
    runtime = DiretorPresencaRuntime(
        contexto_getter=lambda: {
            "modo_jogo_ativo": False, "turno_ativo": False,
            "is_speaking": False, "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=_turno_evento,
        processar_proposta_comunicativa=_materializador_entregue(falas),
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = runtime.considerar({
        "dominio": "rotina", "categoria": "dica", "fala": "Quer que eu veja?",
        "confianca": 0.95, "fundamentada": True, "momento_seguro": True,
        "evidencias": ["erro copiado", "janela atual"], "chave": "clipboard-erro",
        "ao_concluir": callback,
    })

    assert resultado["status"] == "proposta_cognitiva"
    assert recebidos == [(True, "entregue")]


def test_diretor_identifica_origem_da_assistencia_clipboard() -> None:
    recebidos = []
    falas = []
    runtime = DiretorPresencaRuntime(
        contexto_getter=lambda: {
            "modo_jogo_ativo": False, "turno_ativo": False,
            "is_speaking": False, "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=_turno_evento,
        processar_proposta_comunicativa=_materializador_entregue(falas, recebidos),
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = runtime.considerar({
        "origem": "observador_area_transferencia",
        "dominio": "rotina", "categoria": "dica", "fala": "Quer que eu veja?",
        "confianca": 0.95, "fundamentada": True, "momento_seguro": True,
        "evidencias": ["erro copiado", "janela atual"], "chave": "clipboard-origem",
    })

    assert resultado["status"] == "proposta_cognitiva"
    assert recebidos[0]["origem"] == "observador_area_transferencia"


def test_erro_copiado_nao_disputa_orcamento_com_dica_anterior() -> None:
    estado = {
        "historico": [{
            "ts": 990.0, "dominio": "rotina", "categoria": "dica",
            "chave": "outra-dica", "origem": "rotina",
        }],
    }
    falas = []
    runtime = DiretorPresencaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {
            "modo_jogo_ativo": False, "turno_ativo": False,
            "is_speaking": False, "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=_turno_evento,
        processar_proposta_comunicativa=_materializador_entregue(falas),
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = runtime.considerar({
        "origem": "observador_area_transferencia",
        "dominio": "rotina", "categoria": "dica",
        "fala": "Vi um erro copiado. Quer que eu investigue?",
        "confianca": 0.95, "fundamentada": True, "momento_seguro": True,
        "evidencias": ["erro copiado", "janela atual"], "chave": "clipboard-novo",
    })

    assert resultado["status"] == "proposta_cognitiva"
    assert falas


def test_dica_obvia_sem_duas_evidencias_e_bloqueada() -> None:
    runtime, _estado, falas, oportunidades, _feedbacks, _agora = _runtime()

    resultado = runtime.considerar({
        "dominio": "jogo", "categoria": "dica", "fala": "Use uma poção.",
        "confianca": 0.99, "fundamentada": True, "momento_seguro": True,
        "evidencias": ["vida baixa"], "chave": "pocao",
    })

    assert resultado == {"status": "bloqueada", "motivo": "dica_sem_duas_evidencias", "categoria": "dica", "ts": 1000.0}
    assert not falas and not oportunidades


def test_presenca_nao_interrompe_combate_ou_turno() -> None:
    runtime, _estado, falas, _oportunidades, _feedbacks, _agora = _runtime()

    insegura = runtime.considerar({
        "dominio": "jogo", "categoria": "motivacao", "fala": "Vai que é sua.",
        "confianca": 0.9, "momento_seguro": False, "evidencias": ["chefe visível"],
    })

    assert insegura["motivo"] == "momento_de_jogo_inseguro"
    assert not falas


def test_recomendacao_musical_nunca_autotoca() -> None:
    runtime, _estado, falas, _oportunidades, _feedbacks, _agora = _runtime()

    resultado = runtime.considerar({
        "dominio": "jogo", "categoria": "musica", "fala": "Rock combina aqui.",
        "confianca": 0.9, "momento_seguro": True, "executar_automaticamente": True,
        "evidencias": ["combate intenso observado"],
    })

    assert resultado["motivo"] == "musica_nao_pode_autotocar"
    assert not falas


def test_feedback_explicito_aprende_sem_consumir_turno() -> None:
    runtime, _estado, _falas, _oportunidades, feedbacks, agora = _runtime()
    runtime.considerar({
        "dominio": "jogo", "categoria": "celebracao", "fala": "Essa foi bonita!",
        "confianca": 0.9, "momento_seguro": True, "evidencias": ["tela de vitória"],
    })
    agora[0] += 10

    resultado = runtime.observar_resposta("boa, gostei dessa")

    assert resultado["resultado"] == "aceita"
    assert feedbacks


def test_silencio_so_vira_feedback_depois_de_dez_minutos() -> None:
    runtime, estado, _falas, _oportunidades, feedbacks, agora = _runtime()
    runtime.considerar({
        "dominio": "jogo", "categoria": "musica",
        "fala": "Sua playlist combina com esse ritmo.",
        "confianca": 0.9, "momento_seguro": True,
        "evidencias": ["jogo calmo"], "chave": "musica-foco",
    })

    agora[0] += 599
    assert runtime.registrar_silencio_pendente() == {}
    assert estado["ultima_emissao"]["feedback_registrado"] is False

    agora[0] += 1
    resultado = runtime.registrar_silencio_pendente()

    assert resultado == {"resultado": "silencio", "categoria": "musica"}
    assert estado["ultima_emissao"]["feedback_registrado"] is True
    assert feedbacks[-1][1]["resultado"] == "silencio"


def test_falha_auxiliar_do_diretor_e_encaminhada_sem_quebrar_o_ciclo() -> None:
    falhas = []

    runtime = DiretorPresencaRuntime(
        estado_get=lambda: (_ for _ in ()).throw(RuntimeError("estado indisponível")),
        contexto_getter=lambda: {},
        processar_evento_cognitivo=_turno_evento,
        processar_proposta_comunicativa=_materializador_entregue([]),
        registrar_falha=lambda *args, **kwargs: falhas.append((args, kwargs)),
        clock=lambda: 1000.0,
        log=lambda *_: None,
    )

    resultado = runtime.executar_ciclo()

    assert resultado == {"status": "observando"}
    assert falhas[0][0] == ("diretor_presenca", "estado_leitura")


def test_parser_de_presenca_remove_contrato_da_fala() -> None:
    resposta, evento = extrair_presenca_visual(
        'Boa luta!\nPRESENCA_JOGO_JSON: {"relevante": true, "categoria": "celebracao", '
        '"fala": "Essa luta foi bonita!", "motivo": "vitória", '
        '"evidencias": ["tela de vitória"], "confianca": 0.91, '
        '"momento_seguro": true, "clima_musical": "intenso"}'
    )

    assert resposta == "Boa luta!"
    assert evento["categoria"] == "celebracao"
    assert evento["momento_seguro"] is True
    assert "PRESENCA_JOGO_JSON" not in evento["fala"]


def test_parser_preserva_companhia_e_curiosidade_visual() -> None:
    for categoria in ("companhia", "curiosidade"):
        _resposta, evento = extrair_presenca_visual(
            'PRESENCA_JOGO_JSON: {"relevante": true, '
            f'"categoria": "{categoria}", "fala": "Que lugar estranho é esse?", '
            '"motivo": "área nova", "evidencias": ["estrutura incomum"], '
            '"confianca": 0.84, "momento_seguro": true, "clima_musical": ""}'
        )

        assert evento["relevante"] is True
        assert evento["categoria"] == categoria


def test_parser_rejeita_comentario_visual_generico_de_pausa() -> None:
    _resposta, evento = extrair_presenca_visual(
        'PRESENCA_JOGO_JSON: {"relevante": true, "categoria": "companhia", '
        '"fala": "Parece que você está num momento de pausa. É um bom momento para respirar.", '
        '"motivo": "menu aberto", "evidencias": ["menu aberto"], '
        '"confianca": 0.9, "momento_seguro": true, "clima_musical": "calmo"}'
    )

    assert evento["relevante"] is False
    assert evento["categoria"] == "nenhuma"
    assert evento["fala"] == ""


def test_presenca_visual_remove_artista_nao_sustentado_pelas_evidencias() -> None:
    _resposta, evento = extrair_presenca_visual(
        'PRESENCA_JOGO_JSON: {"relevante": true, "categoria": "companhia", '
        '"fala": "Você trocou o cajado por uma playlist bem pesada do Anitta e One Punch Man. Essa mistura ficou cósmica.", '
        '"motivo": "música durante o jogo", '
        '"evidencias": ["cajado visível", "playlist aberta", "personagem nível 12"], '
        '"confianca": 0.86, "momento_seguro": true, "clima_musical": "intenso"}'
    )

    assert evento["relevante"] is True
    assert "Anitta" not in evento["fala"]
    assert "One Punch Man" not in evento["fala"]
    assert "playlist bem pesada" in evento["fala"]
    assert "Essa mistura ficou cósmica" in evento["fala"]


def test_presenca_visual_preserva_artista_literal_confirmado_na_evidencia() -> None:
    _resposta, evento = extrair_presenca_visual(
        'PRESENCA_JOGO_JSON: {"relevante": true, "categoria": "companhia", '
        '"fala": "Essa playlist do AniRap combinou com a luta.", '
        '"motivo": "música durante o jogo", '
        '"evidencias": ["texto exato visível: AniRap"], '
        '"confianca": 0.9, "momento_seguro": true, "clima_musical": "intenso"}'
    )

    assert "AniRap" in evento["fala"]


def test_curiosidade_de_jogo_pode_voltar_sem_cooldown_de_cotidiano() -> None:
    runtime, _estado, falas, _oportunidades, _feedbacks, agora = _runtime()
    primeiro = {
        "dominio": "jogo", "categoria": "curiosidade",
        "fala": "Essa estrutura parece diferente. O que será que tem ali?",
        "confianca": 0.86, "momento_seguro": True,
        "evidencias": ["estrutura visível"], "chave": "estrutura-1",
    }
    assert runtime.considerar(primeiro)["status"] == "proposta_cognitiva"

    agora[0] += 350
    segundo = dict(primeiro, fala="Esse bicho eu ainda não tinha visto por aqui.", chave="criatura-2")
    assert runtime.considerar(segundo)["status"] == "proposta_cognitiva"
    assert len(falas) == 2


def test_laylay_fica_silenciosa_quando_detecta_concentracao() -> None:
    runtime, estado, falas, _oportunidades, _feedbacks, agora = _runtime(contexto={
        "modo_jogo_ativo": False,
        "modo_foco": True,
        "assunto": "Programação",
        "titulo_janela": "laylay.py - Visual Studio Code",
    })

    assert runtime.executar_ciclo()["status"] == "observando"
    agora[0] += 3500
    assert runtime.executar_ciclo()["status"] == "observando"
    assert estado["configuracao"]["perfil"] == "silencioso"
    assert estado["configuracao"]["motivo_perfil"] == "concentracao_detectada"
    assert falas == []


def test_feedback_positivo_de_jogo_deixa_presenca_mais_proxima() -> None:
    runtime, estado, _falas, _oportunidades, _feedbacks, agora = _runtime()
    runtime.considerar({
        "dominio": "jogo", "categoria": "celebracao", "fala": "Essa foi bonita!",
        "confianca": 0.9, "momento_seguro": True, "evidencias": ["vitória"],
        "chave": "vitoria-1",
    })
    agora[0] += 10
    runtime.observar_resposta("boa, gostei dessa")
    agora[0] += 500

    runtime.considerar({
        "dominio": "jogo", "categoria": "celebracao", "fala": "Outra vitória limpa!",
        "confianca": 0.9, "momento_seguro": True, "evidencias": ["nova vitória"],
        "chave": "vitoria-2",
    })

    assert estado["configuracao"]["perfil"] == "presente"
    assert estado["configuracao"]["motivo_perfil"] == "jogo_com_feedback_positivo"


def test_feedback_negativo_faz_laylay_reduzir_presenca_sozinha() -> None:
    runtime, estado, _falas, _oportunidades, _feedbacks, agora = _runtime()
    runtime.considerar({
        "dominio": "jogo", "categoria": "motivacao", "fala": "Você consegue.",
        "confianca": 0.9, "momento_seguro": True, "evidencias": ["tentativa difícil"],
        "chave": "tentativa-1",
    })
    agora[0] += 10
    runtime.observar_resposta("não precisa comentar, fica quieta")
    agora[0] += 1000

    runtime.considerar({
        "dominio": "jogo", "categoria": "motivacao", "fala": "Respira e tenta de novo.",
        "confianca": 0.9, "momento_seguro": True, "evidencias": ["nova tentativa"],
        "chave": "tentativa-2",
    })

    assert estado["configuracao"]["perfil"] == "silencioso"
    assert estado["configuracao"]["motivo_perfil"] == "feedback_negativo"
