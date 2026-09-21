from __future__ import annotations

from mente_laylay.integracao.ambiente_navegacao import AmbienteNavegacaoRuntime


def test_ambiente_filtra_e_congela_servicos_apos_conexao() -> None:
    get_inicial = object()
    runtime = AmbienteNavegacaoRuntime(
        servicos_iniciais={
            "_percepcao_get": get_inicial,
            "SEGREDO": "não reter",
        },
        log=lambda *_args: None,
    )
    assert runtime._ns() == {"_percepcao_get": get_inicial}

    get_final = object()
    servicos = {
        "_percepcao_get": get_final,
        "SITES_DIRECTOS": {"youtube": "https://youtube.com"},
        "SEGREDO": "não reter",
    }
    runtime.conectar_servicos(servicos)
    servicos["_percepcao_get"] = object()
    servicos["novo"] = object()

    assert runtime._ns()["_percepcao_get"] is get_final
    assert "SITES_DIRECTOS" in runtime.servicos_registrados
    assert "SEGREDO" not in runtime.servicos_registrados
    assert "novo" not in runtime.servicos_registrados


def test_namespace_legado_e_consultado_somente_na_criacao() -> None:
    chamadas = []
    runtime = AmbienteNavegacaoRuntime(
        namespace_getter=lambda: chamadas.append(True) or {"psutil": object()},
    )

    runtime._ns()
    runtime._ns()
    assert chamadas == [True]


def test_organizador_recebe_audio_e_tempo_de_processos_do_ambiente() -> None:
    chamadas = []
    audio_cb = lambda: {"chrome.exe"}
    psutil_falso = object()
    runtime = AmbienteNavegacaoRuntime(servicos_iniciais={
        "_organizar_janelas_mente": lambda *args, **kwargs: (
            chamadas.append((args, kwargs)) or {"status": "ok"}
        ),
        "gw": object(),
        "pyautogui": object(),
        "ctypes": object(),
        "wintypes": object(),
        "psutil": psutil_falso,
        "_listar_processos_audio_ativos_mente": audio_cb,
        "APP_OPENER_AVAILABLE": False,
    })

    runtime.organizar_janelas("", "")

    _, kwargs = chamadas[0]
    assert kwargs["psutil_mod"] is psutil_falso
    assert kwargs["processos_audio_ativos_cb"] is audio_cb


def test_planejador_de_layout_e_somente_leitura_e_remove_objetos_privados() -> None:
    janela = object()
    chamadas = []
    runtime = AmbienteNavegacaoRuntime(servicos_iniciais={
        "_planejar_organizacao_janelas_mente": lambda *args, **kwargs: (
            chamadas.append((args, kwargs)) or {
                "ok": True,
                "confirmado": True,
                "status": "layout_planejado",
                "nome_esquerda": "Editor",
                "prioridades": [{"titulo": "Editor", "motivos": ["janela em foco"]}],
                "_janela_esquerda": janela,
            }
        ),
        "gw": object(),
        "ctypes": object(),
        "wintypes": object(),
        "psutil": object(),
        "_listar_processos_audio_ativos_mente": lambda: set(),
    })

    resultado = runtime.planejar_organizacao_janelas()

    assert chamadas
    assert resultado["status"] == "layout_planejado"
    assert "_janela_esquerda" not in resultado
