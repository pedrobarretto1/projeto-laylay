from __future__ import annotations

from mente_laylay.autonomia.controle_midia import executar_media_control
from tests.fakes_navegador import NavegadorLeituraFake, NavegadorOperacoesFake


def _ctx_base(*, enviar_chrome, aba_youtube: bool = True, nativo=None, falas=None):
    falas = falas if falas is not None else []
    navegador = NavegadorOperacoesFake(resultado=True)
    if callable(enviar_chrome):
        navegador.controlar_youtube = lambda comando: bool(
            enviar_chrome("youtube_control", {"command": comando})
        )
    return {
        "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        "_registro_navegador_operacoes_runtime": navegador if callable(enviar_chrome) else None,
        "_registro_navegador_leitura_runtime": NavegadorLeituraFake(aba={
            "url": "https://www.youtube.com/watch?v=teste" if aba_youtube else "",
            "title": "YouTube" if aba_youtube else "",
        }),
        "_executar_controle_midia_nativo": nativo,
        "playlist_state": {},
    }


def test_confirmacao_do_chrome_chega_ao_resultado_e_a_fala() -> None:
    falas: list[str] = []
    resultados: list[tuple[str, bool | None, bool | None]] = []
    enviados: list[tuple[str, dict]] = []

    def enviar(action: str, payload: dict) -> bool:
        enviados.append((action, payload))
        return True

    ok = executar_media_control(
        {"acao": "next", "platform": "music"},
        "próxima música",
        "local",
        _ctx_base(enviar_chrome=enviar, falas=falas),
        marcar_resultado=lambda status, executou=None, confirmado=None, **_kw: resultados.append(
            (status, executou, confirmado)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )

    assert ok is True
    assert enviados == [("youtube_control", {"command": "next"})]
    assert resultados == [("midia_next", True, True)]
    assert falas
    assert "não consegui confirmar" not in falas[-1].casefold()


def test_tecla_nativa_fala_do_envio_sem_fingir_confirmacao() -> None:
    falas: list[str] = []
    resultados: list[tuple[str, bool | None, bool | None]] = []
    comandos_nativos: list[str] = []

    ok = executar_media_control(
        {"acao": "pause", "platform": "music"},
        "pausa ela",
        "local",
        _ctx_base(
            enviar_chrome=None,
            aba_youtube=False,
            nativo=lambda comando: comandos_nativos.append(comando) or True,
            falas=falas,
        ),
        marcar_resultado=lambda status, executou=None, confirmado=None, **_kw: resultados.append(
            (status, executou, confirmado)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )

    assert ok is True
    assert comandos_nativos == ["pause_play"]
    assert resultados == [("midia_pause", True, None)]
    assert falas
    assert any(sinal in falas[-1].casefold() for sinal in ("mandei", "pedi"))
    assert "não consegui confirmar" not in falas[-1].casefold()


def test_retomada_confirmada_tem_fala_propria_em_vez_de_feito_generico() -> None:
    falas: list[str] = []

    ok = executar_media_control(
        {"acao": "play", "platform": "music"},
        "despausa ela",
        "local",
        _ctx_base(enviar_chrome=lambda *_args: True, falas=falas),
        marcar_resultado=lambda *_args, **_kwargs: None,
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )

    assert ok is True
    assert falas
    assert falas[-1] != "Feito."
    assert any(sinal in falas[-1].casefold() for sinal in ("retomei", "play", "voltou"))
