from __future__ import annotations

from pathlib import Path

from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.integracao.chrome_comandos import validar_e_enviar_comando


def test_extensao_pula_somente_sob_comando_explicito() -> None:
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "extençao_google" / "content_script.js").read_text(encoding="utf-8")

    assert "watchForSkippableYouTubeAds" not in codigo
    assert "_findYouTubeSkipButton" in codigo
    assert "_skipYouTubeAd" in codigo
    assert "ytp-ad-skip-button" in codigo
    assert 'status: "unsupported"' not in codigo


def test_pular_anuncio_nao_vira_proxima_musica() -> None:
    resultado = detectar_volume_ou_midia(
        "pula esse anuncio",
        params_cb=lambda **kwargs: kwargs,
        contexto_musical_ativo=True,
    )

    assert resultado == {
        "intent": "MEDIA_CONTROL",
        "params": {"acao": "skip_ad", "platform": "youtube"},
    }


def test_controle_youtube_aguarda_confirmacao_real_da_extensao() -> None:
    enviados: list[tuple[dict, float]] = []

    def executar_confirmado(payload: dict, timeout_s: float) -> bool:
        enviados.append((payload, timeout_s))
        return True

    contexto = {
        "ALLOWED_ACTIONS": {"youtube_control"},
        "connected_extensions": {object()},
        "ws_loop": object(),
        "executar_chrome_confirmado": executar_confirmado,
    }

    assert validar_e_enviar_comando(
        contexto,
        "youtube_control",
        {"command": "skip_ad"},
    ) is True
    assert enviados == [
        ({"action": "youtube_control", "command": "skip_ad"}, 3.0),
    ]


def test_executor_de_midia_envia_pulo_de_anuncio_ao_chrome() -> None:
    enviados: list[tuple[str, dict]] = []
    resultados: list[tuple[str, bool | None, bool | None]] = []

    ok = executar_media_control(
        {"acao": "skip_ad", "platform": "youtube"},
        "pula esse anúncio",
        "local",
        {
            "falar_com_lipsync": lambda *_args: None,
            "enviar_comando_chrome": lambda action, payload: enviados.append((action, payload)) or True,
            "playlist_state": {},
        },
        marcar_resultado=lambda status, executou=None, confirmado=None, **_kw: resultados.append(
            (status, executou, confirmado)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )

    assert ok is True
    assert enviados == [("youtube_control", {"command": "skip_ad"})]
    assert resultados == [("midia_skip_ad", True, True)]
