from __future__ import annotations

from types import SimpleNamespace

import mente_laylay.autonomia.adaptador_resultado as modulo
from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional


def _adaptador(ctx: dict | None = None, **params) -> AdaptadorResultadoOperacional:
    return AdaptadorResultadoOperacional(
        {"intent": "APP_OPEN"},
        params or {"nome_app": "chrome"},
        "abre o chrome",
        "pc_a",
        ctx or {},
    )


def test_marcar_resultado_constroi_contrato_com_alvo_e_confirmacao() -> None:
    registros: list[tuple] = []
    adaptador = _adaptador({
        "_registrar_resultado_execucao": lambda *args, **kwargs: registros.append(
            (args, kwargs)
        )
    })

    adaptador.marcar_resultado("app_aberto", executou=True, detalhe="janela vista")

    args, kwargs = registros[0]
    contrato = args[0]
    assert contrato.intent == "APP_OPEN"
    assert contrato.alvo == "chrome"
    assert contrato.executou is True
    assert contrato.confirmado is True
    assert contrato.detalhe == "janela vista"
    assert args[1:3] == ("abre o chrome", True)
    assert kwargs == {"origem": "executor", "status": "app_aberto"}


def test_status_de_falha_sem_executou_nao_vira_sucesso() -> None:
    contratos = []
    adaptador = _adaptador({
        "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: (
            contratos.append(contrato)
        )
    })

    adaptador.marcar_resultado("falha_execucao")

    assert contratos[0].executou is False
    assert contratos[0].confirmado is False


def test_confirmacao_explicita_do_executor_tem_prioridade() -> None:
    contratos = []
    adaptador = _adaptador({
        "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: (
            contratos.append(contrato)
        )
    })

    adaptador.marcar_resultado("app_aberto", executou=True, confirmado=False)

    assert contratos[0].executou is True
    assert contratos[0].confirmado is False


def test_chamador_legado_nao_transforma_estado_ja_satisfeito_em_nova_execucao() -> None:
    contratos = []
    adaptador = _adaptador({
        "_registrar_resultado_execucao": lambda contrato, *_args, **_kwargs: (
            contratos.append(contrato)
        )
    })

    adaptador.marcar_resultado("ja_aberto_focado", executou=True)

    assert contratos[0].executou is False
    assert contratos[0].confirmado is True


def test_alvo_dos_params_preserva_prioridade_operacional() -> None:
    adaptador = _adaptador(
        None,
        alvo="luz",
        nome_app="chrome",
        url="https://example.com",
    )

    assert adaptador.alvo_dos_params() == "luz"


def test_contexto_de_fala_consulta_a_mesma_mente_do_turno() -> None:
    adaptador = _adaptador({
        "current_emotion": "feliz",
        "ultima_habilidade": "iot",
        "ultimo_alvo": "luz",
    })

    assert adaptador.contexto_fala() == {
        "current_emotion": "feliz",
        "ultima_habilidade": "iot",
        "ultimo_alvo": "luz",
        "ultima_resposta": "",
        "falas_recentes": [],
        "modo_jogo_ativo": False,
    }


def test_fala_por_status_repassa_resultado_ao_planejador(monkeypatch) -> None:
    falas: list[tuple] = []
    planejamentos: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Chrome aberto.",
    )

    def planejar(resultado, fala, **kwargs):
        planejamentos.append((resultado, fala, kwargs))
        return SimpleNamespace(fala="Chrome aberto.", emocao="feliz", nivel=2)

    monkeypatch.setattr(modulo, "planejar_resposta_acao", planejar)
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args)
    })

    adaptador.falar_por_status("app_aberto", "Abrindo Chrome.", alvo="chrome")

    resultado, fala_base, preferencias = planejamentos[0]
    assert resultado.status == "app_aberto"
    assert resultado.executou is True
    assert resultado.confirmado is True
    assert fala_base == "Chrome aberto."
    assert preferencias == {
        "emocao_preferida": "debochada",
        "nivel_preferido": 2,
    }
    assert falas == [("Chrome aberto.", "feliz", 2)]


def test_fala_por_status_entrega_contrato_ao_guardiao_operacional(monkeypatch) -> None:
    entregas: list[tuple] = []
    falas_diretas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Abri o Chrome sem drama.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas_diretas.append(args),
        "_falar_resultado_operacional": lambda *args: entregas.append(args),
    })

    adaptador.falar_por_status("app_aberto", "Abri o Chrome.", alvo="chrome")

    contrato, fala, emocao, nivel = entregas[0]
    assert contrato.intent == "APP_OPEN"
    assert contrato.status == "app_aberto"
    assert contrato.confirmado is True
    assert "chrome" in fala.casefold()
    assert len(fala.split()) >= 3
    assert (emocao, nivel) == ("debochada", 2)
    assert falas_diretas == []


def test_status_calmo_nao_forca_personalidade_agitada(monkeypatch) -> None:
    preferencias: list[dict] = []
    monkeypatch.setattr(
        modulo, "fala_por_estado_acao", lambda _status, **_kwargs: "Volume ajustado."
    )

    def planejar(_resultado, _fala, **kwargs):
        preferencias.append(kwargs)
        return SimpleNamespace(fala="Volume ajustado.", emocao="calma", nivel=1)

    monkeypatch.setattr(modulo, "planejar_resposta_acao", planejar)
    _adaptador({"falar_com_lipsync": lambda *_args: None}).falar_por_status(
        "VOLUME_AJUSTADO", "Volume ajustado.", alvo="volume"
    )

    assert preferencias == [{
        "emocao_preferida": "calma",
        "nivel_preferido": 1,
    }]


def test_fala_de_janela_escolhe_fallback_especifico(monkeypatch) -> None:
    chamadas: list[tuple] = []

    def falar(self, status, fallback, *, alvo=""):
        chamadas.append((status, fallback, alvo))

    monkeypatch.setattr(AdaptadorResultadoOperacional, "falar_por_status", falar)
    _adaptador().falar_resultado_janela("chrome", "app_aberto_sem_foco")

    assert chamadas == [(
        "app_aberto_sem_foco",
        "chrome abriu, mas não consegui puxar ele pro foco agora.",
        "chrome",
    )]


def test_resultado_visivel_recebe_deboche_causal_sem_mudar_o_fato(monkeypatch) -> None:
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Opera já estava aberto e em foco.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "modo_jogo_ativo": lambda: True,
        "_avaliar_evento_emocional_operacional": lambda _resultado: {
            "emocao": "debochada",
            "nivel": 1,
            "responsabilidade": "usuario",
            "confianca": 0.94,
            "repeticoes": 1,
            "provocacao_usuario": 1,
            "permite_expressao": True,
            "arco": "provocacao_afetuosa",
            "ts": 100.0,
        },
    }, nome_app="Opera")

    adaptador.falar_por_status(
        "ja_aberto_focado", "Opera já estava aberto.", alvo="Opera",
    )

    assert "opera já estava" in falas[0][0].casefold()
    assert falas[0][0].casefold().count("opera") >= 2
    assert len(falas[0][0].split(". ")) <= 2
    assert falas[0][1:] == ("debochada", 1)


def test_falha_do_registrador_nao_interrompe_o_executor() -> None:
    adaptador = _adaptador({
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: (
            _ for _ in ()
        ).throw(RuntimeError("memória indisponível"))
    })

    adaptador.marcar_resultado("app_aberto", executou=True)


def test_confirmacao_confirmada_pode_receber_voz_da_llm(monkeypatch) -> None:
    falas: list[tuple] = []
    chamadas_llm: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Abri o Chrome.",
    )

    def enviar(mensagens, **kwargs):
        chamadas_llm.append((mensagens, kwargs))
        return (
            '{"fala":"Abri o Chrome. Ele já entrou em cena sem drama.",'
            '"emocao":"debochada","nivel":2,'
            '"status":"app_aberto","alvo":"chrome"}'
        )

    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "enviar_mensagem": enviar,
    })
    adaptador.falar_por_status("app_aberto", "Abrindo Chrome.", alvo="chrome")

    assert chamadas_llm
    assert chamadas_llm[0][1]["modo_rapido"] is True
    assert chamadas_llm[0][1]["timeout"] == 8.0
    assert chamadas_llm[0][1]["_prioridade_interativa"] is True
    assert chamadas_llm[0][1]["_permitir_durante_interacao"] is True
    assert falas == [("Abri o Chrome. Ele já entrou em cena sem drama.", "debochada", 2)]


def test_confirmacao_llm_contraditoria_volta_para_fala_segura(monkeypatch) -> None:
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Abri o Chrome.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "enviar_mensagem": lambda *_args, **_kwargs: (
            '{"fala":"Não consegui abrir o Chrome.","emocao":"triste",'
            '"nivel":3,"status":"app_aberto","alvo":"chrome"}'
        ),
    })

    adaptador.falar_por_status("app_aberto", "Abrindo Chrome.", alvo="chrome")

    assert "não consegui" not in falas[0][0].casefold()
    assert "chrome" in falas[0][0].casefold()


def test_fallback_de_autoria_expoe_motivo_sem_quebrar_o_comando(monkeypatch) -> None:
    logs: list[str] = []
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Abri o Chrome.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "print": logs.append,
        "enviar_mensagem": lambda *_args, **_kwargs: "LAYLAY_LLM_INDISPONIVEL",
    })

    adaptador.falar_por_status("app_aberto", "Abrindo Chrome.", alvo="chrome")

    assert falas
    assert any("resposta_tecnica_ou_json_invalido" in item for item in logs)


def test_falha_operacional_cotidiana_recebe_uma_fala_autoral_da_llm(monkeypatch) -> None:
    chamadas_llm: list[bool] = []
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Não achei o Chrome.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "enviar_mensagem": lambda *_args, **_kwargs: (
            chamadas_llm.append(True)
            or '{"fala":"Não achei o Chrome por aqui; hoje ele resolveu brincar de invisível.",'
               '"emocao":"debochada","nivel":1,'
               '"status":"nao_encontrado","alvo":"chrome"}'
        ),
    })

    adaptador.falar_por_status("nao_encontrado", "Não achei o Chrome.", alvo="chrome")

    assert chamadas_llm == [True]
    assert falas == [(
        "Não achei o Chrome por aqui; hoje ele resolveu brincar de invisível.",
        "debochada",
        1,
    )]


def test_estado_ja_satisfeito_vira_nao_acao_consciente_autoral(monkeypatch) -> None:
    entregas: list[tuple] = []
    chamadas: list[object] = []

    def enviar(mensagens, **_kwargs):
        chamadas.append(mensagens)
        return (
            '{"fala":"O Opera já está aberto e em foco; não vou abrir de novo o que já está na sua cara.",'
            '"emocao":"debochada","nivel":1,'
            '"status":"ja_aberto_focado","alvo":"Opera"}'
        )

    adaptador = _adaptador({
        "falar_com_lipsync": lambda *_args: None,
        "enviar_mensagem": enviar,
        "_falar_resultado_operacional": lambda *args: entregas.append(args),
    }, nome_app="Opera")

    adaptador.falar_por_status(
        "ja_aberto_focado", "Opera já estava aberto e em foco.", alvo="Opera",
    )

    contrato, fala, emocao, nivel = entregas[0]
    assert chamadas
    assert contrato.executou is False
    assert contrato.confirmado is True
    assert "não vou abrir de novo" in fala.casefold()
    assert (emocao, nivel) == ("debochada", 1)


def test_app_ja_aberto_observado_preserva_estado_explicito_no_fallback() -> None:
    entregas: list[tuple] = []
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *_args: None,
        "enviar_mensagem": lambda *_args, **_kwargs: "json inválido",
        "_falar_resultado_operacional": lambda *args: entregas.append(args),
    }, nome_app="microsoft store")

    adaptador.falar_por_status(
        "app_ja_aberto_observado",
        "Microsoft Store já está aberto; só te avisei e não mexi nele.",
        alvo="microsoft store",
        executou=False,
        confirmado=True,
    )

    contrato, fala, _emocao, _nivel = entregas[0]
    assert contrato.executou is False
    assert contrato.confirmado is True
    assert "aberto" in fala.casefold()
    assert "não repeti" in fala.casefold()


def test_estado_ja_satisfeito_aceita_classe_semantica_no_status_da_llm() -> None:
    entregas: list[tuple] = []
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *_args: None,
        "enviar_mensagem": lambda *_args, **_kwargs: (
            '{"fala":"O Opera já está aberto e em foco; não vou abrir de novo só porque seus olhos tiraram férias.",'
            '"emocao":"debochada","nivel":2,'
            '"status":"sem_acao","alvo":"Opera"}'
        ),
        "_falar_resultado_operacional": lambda *args: entregas.append(args),
    }, nome_app="Opera")

    adaptador.falar_por_status(
        "ja_aberto_focado", "Opera já estava aberto e em foco.", alvo="Opera",
    )

    assert entregas[0][1].endswith("seus olhos tiraram férias.")
    assert entregas[0][2:] == ("debochada", 2)


def test_autoria_varia_abertura_que_acabou_de_usar() -> None:
    entregas: list[tuple] = []
    abertura = "O Opera já está aberto e em foco."
    adaptador = _adaptador({
        "ultima_resposta": f"{abertura} Não vou abrir de novo.",
        "falar_com_lipsync": lambda *_args: None,
        "enviar_mensagem": lambda *_args, **_kwargs: (
            '{"fala":"O Opera já está aberto e em foco. Não vou abrir de novo só porque seus olhos tiraram férias.",'
            '"emocao":"debochada","nivel":2,'
            '"status":"sem_acao","alvo":"Opera"}'
        ),
        "_falar_resultado_operacional": lambda *args: entregas.append(args),
    }, nome_app="Opera")

    adaptador.falar_por_status(
        "ja_aberto_focado", "Opera já estava aberto e em foco.", alvo="Opera",
    )

    fala = entregas[0][1]
    assert fala.startswith("Não vou abrir de novo")
    assert "O Opera já está aberto e em foco." in fala


def test_pergunta_opcional_no_fim_nao_descarta_confirmacao_autoral() -> None:
    logs: list[str] = []
    falas: list[tuple] = []
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "print": logs.append,
        "enviar_mensagem": lambda *_args, **_kwargs: (
            '{"fala":"A lâmpada do quarto não respondeu; hoje ela resolveu testar minha paciência. Quer que eu tente de novo?",'
            '"emocao":"irritada","nivel":1,'
            '"status":"indisponivel","alvo":"lampada_quarto"}'
        ),
    }, alvo="lampada_quarto")

    adaptador.falar_por_status(
        "indisponivel", "A lâmpada do quarto não respondeu.", alvo="lampada_quarto",
        executou=False,
    )

    assert falas[0][0].endswith("hoje ela resolveu testar minha paciência.")
    assert "?" not in falas[0][0]
    assert not any("FALA:AUTORIA" in item for item in logs)


def test_autoria_rejeitada_expoe_regra_exata_que_foi_violada(monkeypatch) -> None:
    logs: list[str] = []
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "O Opera já está aberto e em foco; não repeti a abertura.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "print": logs.append,
        "enviar_mensagem": lambda *_args, **_kwargs: (
            '{"fala":"O Opera já está aberto e em foco; não repeti, mas posso tentar de novo.",'
            '"emocao":"debochada","nivel":2,'
            '"status":"ja_aberto_focado","alvo":"Opera"}'
        ),
    }, nome_app="Opera")

    adaptador.falar_por_status(
        "ja_aberto_focado", "Opera já estava aberto e em foco.", alvo="Opera",
    )

    assert falas[0][0].endswith("já está aberto e em foco; não repeti a abertura.")
    assert any(
        "contrato_nao_preservado:promessa_ou_nova_oferta" in item
        for item in logs
    )


def test_modo_jogo_mantem_fala_local_e_nao_chama_llm(monkeypatch) -> None:
    falas: list[tuple] = []
    chamadas: list[bool] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Opera já tava na tua cara.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "enviar_mensagem": lambda *_args, **_kwargs: chamadas.append(True),
        "modo_jogo_ativo": lambda: True,
    }, nome_app="Opera")

    adaptador.falar_por_status(
        "ja_aberto_focado", "Opera já estava aberto.", alvo="Opera",
    )

    assert chamadas == []
    assert falas[0][0] == "Opera já tava na tua cara."


def test_consulta_informativa_pode_ganhar_estilo_sem_perder_texto(monkeypatch) -> None:
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Suas playlists são rock (3) e trap (5).",
    )
    adaptador = AdaptadorResultadoOperacional(
        {"intent": "PLAYLIST_LIST"},
        {},
        "quais são minhas playlists?",
        "pc_a",
        {
            "falar_com_lipsync": lambda *args: falas.append(args),
            "enviar_mensagem": lambda *_args, **_kwargs: (
                '{"fala":"Olha o seu pequeno império musical: Suas playlists são rock (3) e trap (5).",'
                '"emocao":"debochada","nivel":2}'
            ),
        },
    )

    adaptador.falar_por_status("playlists_listadas", "Playlists listadas.")

    assert falas == [(
        "Olha o seu pequeno império musical: Suas playlists são rock (3) e trap (5).",
        "debochada",
        2,
    )]


def test_status_iot_confirmado_remove_ancora_de_incerteza_contraditoria(monkeypatch) -> None:
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: (
            "Enviei o comando, mas ainda não consegui confirmar. "
            "A lâmpada do quarto está desligada. Estado conferido."
        ),
    )
    adaptador = AdaptadorResultadoOperacional(
        {"intent": "IOT_STATUS"},
        {"alvo": "lampada_quarto"},
        "como está a lâmpada do quarto?",
        "pc_a",
        {"falar_com_lipsync": lambda *args: falas.append(args)},
    )

    adaptador.falar_por_status(
        "desligado",
        "A lâmpada do quarto está desligada.",
        alvo="lâmpada do quarto",
        executou=True,
        confirmado=True,
    )

    assert falas
    fala = falas[0][0].casefold()
    assert "está desligada" in fala or "está desligado" in fala
    assert "não consegui" not in fala
    assert "nao consegui" not in fala
