from __future__ import annotations

from mente_laylay.autonomia.rota_musical import RotaMusical


def test_url_vazia_nao_dispara_nenhuma_rota() -> None:
    assert RotaMusical({}).abrir("   ") is False


def test_pc_b_recebe_url_sem_acionar_player_local() -> None:
    remotos: list[dict] = []
    rota = RotaMusical({
        "_enviar_pc_b": remotos.append,
        "abrir_url_com_reciclagem": lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("não deve abrir localmente")
        ),
    }, "pc_b")

    assert rota.abrir("https://youtube.com/watch?v=1") is True
    assert remotos == [{
        "action": "open_url", "url": "https://youtube.com/watch?v=1"
    }]


def test_ambos_com_busca_envia_chrome_e_pc_b() -> None:
    chrome: list[tuple] = []
    remotos: list[dict] = []
    rota = RotaMusical({
        "enviar_comando_chrome": lambda *args: chrome.append(args) or True,
        "_enviar_pc_b": remotos.append,
    }, "ambos", "pesquisa Duality e traz para frente")

    assert rota.abrir("https://youtube.com/results", query="Duality") is True
    assert chrome == [(
        "youtube_search", {"query": "Duality", "permitir_foco": True}
    )]
    assert remotos == [{
        "action": "open_url", "url": "https://youtube.com/results"
    }]


def test_ambos_mantem_envio_remoto_quando_abertura_local_falha() -> None:
    remotos: list[dict] = []
    rota = RotaMusical({
        "abrir_url_com_reciclagem": lambda *_args, **_kwargs: False,
        "_enviar_pc_b": remotos.append,
    }, "ambos")

    assert rota.abrir("https://youtube.com/watch?v=2") is False
    assert len(remotos) == 1


def test_busca_local_nao_toma_foco_sem_pedido_explicito() -> None:
    chrome: list[tuple] = []
    rota = RotaMusical({
        "enviar_comando_chrome": lambda *args: chrome.append(args) or True
    }, "pc_a", "coloca um rock pesado")

    assert rota.abrir("https://youtube.com/results", query="rock pesado") is True
    assert chrome[0][1]["permitir_foco"] is False


def test_link_direto_exige_confirmacao_real_de_reproducao() -> None:
    chrome: list[tuple] = []
    rota = RotaMusical({
        "enviar_comando_chrome": lambda *args: chrome.append(args) or True,
    })

    assert rota.abrir("https://www.youtube.com/watch?v=abc") is True
    assert chrome == [(
        "youtube_play",
        {"url": "https://www.youtube.com/watch?v=abc", "permitir_foco": False},
    )]


def test_link_direto_nao_declara_sucesso_se_player_nao_confirmar() -> None:
    rota = RotaMusical({
        "enviar_comando_chrome": lambda *_args, **_kwargs: False,
    })

    assert rota.abrir("https://youtu.be/abc") is False


def test_abertura_local_considera_apenas_false_como_falha() -> None:
    rota_sem_retorno = RotaMusical({
        "abrir_url_com_reciclagem": lambda *_args, **_kwargs: None
    })
    rota_falsa = RotaMusical({
        "abrir_url_com_reciclagem": lambda *_args, **_kwargs: False
    })

    assert rota_sem_retorno.abrir("https://youtube.com/watch?v=3") is True
    assert rota_falsa.abrir("https://youtube.com/watch?v=3") is False


def test_falha_da_abertura_local_e_contida() -> None:
    rota = RotaMusical({
        "abrir_url_com_reciclagem": lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("navegador indisponível")
        )
    })

    assert rota.abrir("https://youtube.com/watch?v=4") is False


def test_pc_b_sem_transporte_disponivel_usa_fallback_local() -> None:
    locais: list[str] = []
    rota = RotaMusical({
        "abrir_url_com_reciclagem": lambda url, **_kwargs: locais.append(url) or True
    }, "pc_b")

    assert rota.abrir("https://youtube.com/watch?v=5") is True
    assert locais == ["https://youtube.com/watch?v=5"]
