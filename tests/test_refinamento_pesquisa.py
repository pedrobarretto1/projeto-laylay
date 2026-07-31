from mente_laylay.cognicao.refinamento_pesquisa import (
    refinar_consulta_musical,
    refinar_consulta_web,
)


def test_pedido_contextual_minecraft_escolhe_faixa_concreta() -> None:
    perfil = refinar_consulta_musical(
        "musica boa para jogar minecraft",
        "coloca uma musica boa para jogar minecraft",
        {"genre": "ambient", "mood": "calmo", "context": "jogando minecraft"},
        cursores={},
    )

    assert perfil["query"] == "C418 - Sweden Minecraft Volume Alpha"
    assert perfil["origem"] == "contexto_curado"
    assert perfil["tipo_resultado"] == "faixa"


def test_curadoria_contextual_varia_sem_perder_o_contexto() -> None:
    cursores: dict[str, int] = {}

    primeira = refinar_consulta_musical(
        "musica para jogar minecraft", "coloca musica para jogar minecraft", cursores=cursores
    )
    segunda = refinar_consulta_musical(
        "musica para jogar minecraft", "coloca musica para jogar minecraft", cursores=cursores
    )

    assert primeira["query"] != segunda["query"]
    assert "C418" in primeira["query"]
    assert "C418" in segunda["query"]


def test_pedido_de_uma_hora_escolhe_selecao_longa() -> None:
    perfil = refinar_consulta_musical(
        "musicas para jogar minecraft por uma hora",
        "coloca musicas para jogar minecraft por uma hora",
        cursores={},
    )

    assert perfil["query"] == "C418 Minecraft relaxing music mix 1 hour"
    assert perfil["tipo_resultado"] == "selecao_longa"


def test_titulo_explicito_nao_e_substituido() -> None:
    perfil = refinar_consulta_musical(
        "Remember The Time", "coloca Remember The Time", cursores={}
    )

    assert perfil["query"] == "Remember The Time"
    assert perfil["origem"] == "explicita"


def test_pesquisa_web_remove_moldura_do_comando() -> None:
    perfil = refinar_consulta_web(
        "pesquisa na internet como corrigir erro 0x80070005",
        "pesquisa na internet como corrigir erro 0x80070005",
    )

    assert perfil["query"] == "como corrigir erro 0x80070005"
