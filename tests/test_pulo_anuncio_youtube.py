from __future__ import annotations

from pathlib import Path

from mente_laylay.autonomia.controle_midia import executar_media_control
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.integracao.chrome_comandos import validar_e_enviar_comando
from tests.fakes_navegador import NavegadorOperacoesFake


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


def test_play_e_pause_recebem_prazo_para_confirmacao_observavel() -> None:
    enviados: list[tuple[dict, float]] = []
    contexto = {
        "ALLOWED_ACTIONS": {"youtube_control"},
        "connected_extensions": {object()},
        "ws_loop": object(),
        "executar_chrome_confirmado": lambda payload, timeout_s: (
            enviados.append((payload, timeout_s)) or True
        ),
    }

    assert validar_e_enviar_comando(
        contexto, "youtube_control", {"command": "pause"},
    )
    assert validar_e_enviar_comando(
        contexto, "youtube_control", {"command": "play"},
    )
    assert enviados == [
        ({"action": "youtube_control", "command": "pause"}, 5.0),
        ({"action": "youtube_control", "command": "play"}, 12.0),
    ]


def test_content_script_tem_um_unico_executor_de_controle_youtube() -> None:
    raiz = Path(__file__).resolve().parents[1]
    codigo = (raiz / "extençao_google" / "content_script.js").read_text(
        encoding="utf-8",
    )

    assert codigo.count('else if (request.action === "youtube_control")') == 1
    assert "controlYouTube(String(request.command))" not in codigo
    assert "pausedConfirmed" in codigo


def test_executor_de_midia_envia_pulo_de_anuncio_ao_chrome() -> None:
    enviados: list[tuple[str, dict]] = []
    resultados: list[tuple[str, bool | None, bool | None]] = []
    navegador = NavegadorOperacoesFake()

    ok = executar_media_control(
        {"acao": "skip_ad", "platform": "youtube"},
        "pula esse anúncio",
        "local",
        {
            "falar_com_lipsync": lambda *_args: None,
            "_registro_navegador_operacoes_runtime": navegador,
            "playlist_state": {},
        },
        marcar_resultado=lambda status, executou=None, confirmado=None, **_kw: resultados.append(
            (status, executou, confirmado)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        ctx_fala=lambda: {},
    )

    assert ok is True
    enviados.extend(navegador.chamadas)
    assert enviados == [("youtube_control", {"command": "skip_ad"})]
    assert resultados == [("midia_skip_ad", True, True)]
