"""P12: falhas parciais, repetição e confirmação em mídia e navegador."""

from __future__ import annotations

from mente_laylay.autonomia.controle_midia import (
    VK_MEDIA_NEXT_TRACK,
    VK_MEDIA_PLAY_PAUSE,
    executar_controle_midia_nativo,
    executar_media_control,
)
from mente_laylay.autonomia.porteiro_chrome import (
    PorteiroChromeRuntime,
    fechar_abas_sugeridas,
)


class _User32:
    def __init__(self, *, falhar: bool = False) -> None:
        self.eventos: list[tuple[int, int]] = []
        self.falhar = falhar

    def keybd_event(self, tecla, _scan, flag, _extra) -> None:
        if self.falhar:
            raise OSError("driver indisponível")
        self.eventos.append((tecla, flag))


class _Ctypes:
    def __init__(self, *, falhar: bool = False) -> None:
        self.windll = type("Windll", (), {"user32": _User32(falhar=falhar)})()


class _MusicaOperacoes:
    def __init__(self, *, proxima: bool, anterior: bool) -> None:
        self.proxima = proxima
        self.anterior = anterior
        self.chamadas: list[str] = []

    def estado(self) -> dict:
        return {"playlist_ativa": "teste"}

    def avancar_proxima(self) -> bool:
        self.chamadas.append("next")
        return self.proxima

    def voltar_anterior(self) -> bool:
        self.chamadas.append("prev")
        return self.anterior


def _executar_midia(params: dict, ctx: dict):
    falas: list[str] = []
    resultados: list[tuple[str, bool | None]] = []
    contexto = {"falar_com_lipsync": lambda fala, *_args: falas.append(fala), **ctx}
    ok = executar_media_control(
        params,
        "comando de teste",
        "local",
        contexto,
        marcar_resultado=lambda status, executou=None, **_kw: resultados.append((status, executou)),
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )
    return ok, falas, resultados


def test_controle_nativo_confirma_eventos_e_isola_falha_de_driver() -> None:
    ctypes_ok = _Ctypes()
    assert executar_controle_midia_nativo("pause_play", ctypes_module=ctypes_ok) is True
    assert ctypes_ok.windll.user32.eventos == [
        (VK_MEDIA_PLAY_PAUSE, 0), (VK_MEDIA_PLAY_PAUSE, 2),
    ]

    ctypes_falha = _Ctypes(falhar=True)
    logs: list[str] = []
    assert executar_controle_midia_nativo(
        "next", ctypes_module=ctypes_falha, log=logs.append,
    ) is False
    assert any("falha" in item.casefold() for item in logs)
    assert executar_controle_midia_nativo("inexistente", ctypes_module=ctypes_ok) is False


def test_playlist_nao_confunde_falha_de_proxima_com_sucesso() -> None:
    musica = _MusicaOperacoes(proxima=False, anterior=True)
    ok, falas, resultados = _executar_midia(
        {"acao": "next"}, {"_registro_musica_operacoes_runtime": musica},
    )

    assert ok is False
    assert musica.chamadas == ["next"]
    assert resultados == [("falha_execucao", False)]
    assert falas and "não" in falas[-1].casefold()


def test_playlist_confirma_repeticao_anterior_quando_runtime_confirma() -> None:
    musica = _MusicaOperacoes(proxima=False, anterior=True)
    ok, _falas, resultados = _executar_midia(
        {"acao": "prev"}, {"_registro_musica_operacoes_runtime": musica},
    )

    assert ok is True
    assert musica.chamadas == ["prev"]
    assert resultados == [("midia_prev_playlist", True)]


def test_volume_sem_controlador_falha_sem_marcar_resultado_falso() -> None:
    ok, falas, resultados = _executar_midia({"nivel_volume": "70"}, {})
    assert ok is False
    assert resultados == []
    assert falas
    assert any(sinal in falas[-1].casefold() for sinal in ("não consegui", "não tive acesso", "escapou"))


def test_porteiro_vazio_e_idempotente() -> None:
    falas: list[str] = []
    assert fechar_abas_sugeridas([], enviar=lambda _url: True, falar=lambda fala, *_: falas.append(fala)) is True
    assert len(falas) == 1
    assert "não tem abas" in falas[0].casefold()


def test_porteiro_preserva_falha_parcial_e_nao_declara_sucesso() -> None:
    abas = ["https://um", "https://dois", "https://tres"]
    falas: list[str] = []
    enviados: list[str] = []

    def enviar(url: str) -> bool:
        enviados.append(url)
        return url != "https://dois"

    ok = fechar_abas_sugeridas(abas, enviar=enviar, falar=lambda fala, *_: falas.append(fala))

    assert ok is False
    assert enviados == ["https://um", "https://dois", "https://tres"]
    assert abas == ["https://dois"]
    assert "não respondeu" in falas[-1].casefold()


def test_porteiro_seleciona_apenas_abas_ociosas_e_respeita_cooldown() -> None:
    agora = 10_000.0
    sugeridas: list[str] = []
    falas: list[str] = []
    runtime = PorteiroChromeRuntime(
        abas_sugeridas=sugeridas,
        obter_ram_percent=lambda: 91.0,
        listar_abas=lambda **_kw: [
            {"url": "https://ativa", "title": "Ativa"},
            {"url": "chrome://settings", "title": "Interna"},
            {"url": "https://antiga-1", "title": "Antiga 1"},
            {"url": "https://antiga-2", "title": "Antiga 2"},
        ],
        obter_estado_chrome=lambda: {
            "aba_url_atual": "https://ativa",
            "_tab_last_seen": {
                "https://antiga-1": {"ts": agora - 4000},
                "https://antiga-2": {"ts": agora - 5000},
            },
        },
        falar=lambda fala, *_: falas.append(fala),
        clock=lambda: agora,
        cooldown_s=1800,
    )

    assert runtime.executar_ciclo() is True
    assert sugeridas == ["https://antiga-2", "https://antiga-1"]
    assert runtime.executar_ciclo() is False
    assert len(falas) == 1


def test_porteiro_nao_sugere_com_ram_baixa() -> None:
    runtime = PorteiroChromeRuntime(
        abas_sugeridas=[],
        obter_ram_percent=lambda: 20.0,
        listar_abas=lambda **_kw: (_ for _ in ()).throw(AssertionError("não deveria listar")),
        obter_estado_chrome=lambda: {},
        falar=lambda *_args: None,
    )
    assert runtime.executar_ciclo() is False
