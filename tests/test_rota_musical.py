from __future__ import annotations

from mente_laylay.autonomia.rota_musical import RotaMusical
from tests.fakes_navegador import NavegadorOperacoesFake


def test_url_vazia_nao_dispara_nenhuma_rota() -> None:
    assert RotaMusical({}).abrir("   ") is False


def test_pc_b_recebe_url_sem_acionar_player_local() -> None:
    remotos: list[dict] = []
    rota = RotaMusical({
        "_enviar_pc_b": remotos.append,
        "_registro_navegador_operacoes_runtime": NavegadorOperacoesFake(
            abrir_cb=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("não deve abrir localmente")
            )
        ),
    }, "pc_b")

    assert rota.abrir("https://youtube.com/watch?v=1") is True
    assert remotos == [{
        "action": "open_url", "url": "https://youtube.com/watch?v=1"
    }]


def test_ambos_com_busca_envia_chrome_e_pc_b() -> None:
    navegador = NavegadorOperacoesFake()
    remotos: list[dict] = []
    rota = RotaMusical({
        "_registro_navegador_operacoes_runtime": navegador,
        "_enviar_pc_b": remotos.append,
    }, "ambos", "pesquisa Duality e traz para frente")

    assert rota.abrir("https://youtube.com/results", query="Duality") is True
    assert navegador.chamadas == [(
        "youtube_search", {"query": "Duality", "permitir_foco": True}
    )]
    assert remotos == [{
        "action": "open_url", "url": "https://youtube.com/results"
    }]


def test_ambos_mantem_envio_remoto_quando_abertura_local_falha() -> None:
    remotos: list[dict] = []
    rota = RotaMusical({
        "_registro_navegador_operacoes_runtime": NavegadorOperacoesFake(resultado=False),
        "_enviar_pc_b": remotos.append,
    }, "ambos")

    assert rota.abrir("https://youtube.com/watch?v=2") is False
    assert len(remotos) == 1


def test_busca_local_nao_toma_foco_sem_pedido_explicito() -> None:
    navegador = NavegadorOperacoesFake()
    rota = RotaMusical({
        "_registro_navegador_operacoes_runtime": navegador
    }, "pc_a", "coloca um rock pesado")

    assert rota.abrir("https://youtube.com/results", query="rock pesado") is True
    assert navegador.chamadas[0][1]["permitir_foco"] is False


def test_link_direto_exige_confirmacao_real_de_reproducao() -> None:
    navegador = NavegadorOperacoesFake()
    rota = RotaMusical({
        "_registro_navegador_operacoes_runtime": navegador,
    })

    assert rota.abrir("https://www.youtube.com/watch?v=abc") is True
    assert navegador.chamadas == [(
        "youtube_play",
        {"url": "https://www.youtube.com/watch?v=abc", "permitir_foco": False},
    )]


def test_link_direto_nao_declara_sucesso_se_player_nao_confirmar() -> None:
    rota = RotaMusical({
        "_registro_navegador_operacoes_runtime": NavegadorOperacoesFake(resultado=False),
    })

    assert rota.abrir("https://youtu.be/abc") is False


def test_abertura_local_respeita_confirmacao_tipado() -> None:
    rota_confirmada = RotaMusical({
        "_registro_navegador_operacoes_runtime": NavegadorOperacoesFake()
    })
    rota_falsa = RotaMusical({
        "_registro_navegador_operacoes_runtime": NavegadorOperacoesFake(resultado=False)
    })

    assert rota_confirmada.abrir("https://youtube.com/watch?v=3") is True
    assert rota_falsa.abrir("https://youtube.com/watch?v=3") is False


def test_falha_da_abertura_local_e_contida() -> None:
    rota = RotaMusical({
        "_registro_navegador_operacoes_runtime": NavegadorOperacoesFake(
            resultado=False
        )
    })

    assert rota.abrir("https://youtube.com/watch?v=4") is False


def test_pc_b_sem_transporte_disponivel_usa_fallback_local() -> None:
    navegador = NavegadorOperacoesFake()
    rota = RotaMusical({
        "_registro_navegador_operacoes_runtime": navegador
    }, "pc_b")

    assert rota.abrir("https://youtube.com/watch?v=5") is True
    assert navegador.chamadas[0][0] == "youtube_play"
