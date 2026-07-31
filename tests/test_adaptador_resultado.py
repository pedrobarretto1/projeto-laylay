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
    assert chamadas_llm[0][1]["timeout"] == 3
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


def test_falha_operacional_nao_e_entregue_para_llm(monkeypatch) -> None:
    chamadas_llm: list[bool] = []
    falas: list[tuple] = []
    monkeypatch.setattr(
        modulo,
        "fala_por_estado_acao",
        lambda _status, **_kwargs: "Não achei o Chrome.",
    )
    adaptador = _adaptador({
        "falar_com_lipsync": lambda *args: falas.append(args),
        "enviar_mensagem": lambda *_args, **_kwargs: chamadas_llm.append(True),
    })

    adaptador.falar_por_status("nao_encontrado", "Não achei o Chrome.", alvo="chrome")

    assert chamadas_llm == []
    assert "não" in falas[0][0].casefold()


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
