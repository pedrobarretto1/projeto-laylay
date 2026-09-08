from mente_laylay.percepcao.visao_jogo.observador_presenca import (
    ObservadorPresencaJogoRuntime,
)
from unittest.mock import patch


def test_orcamento_visual_e_renovado_a_cada_janela_curta() -> None:
    agora = [1001.0]
    observador = ObservadorPresencaJogoRuntime(
        contexto_jogo=lambda: {"ativo": True},
        capturar=lambda _contexto: "",
        executar_visao=lambda _pedido: True,
        jogo_chave_atual=lambda _contexto: "jogo",
        interacao_iniciada=lambda: True,
        max_analises_sessao=6,
        janela_analises_s=900.0,
        clock=lambda: agora[0],
        log=lambda _texto: None,
    )
    observador._jogo = "jogo"
    observador._inicio_sessao = 100.0
    observador._analises = 6

    assert observador.verificar_uma_vez() is False
    assert observador._analises == 0
    assert observador._inicio_sessao == 1001.0


def test_curiosidade_captura_quadro_novo_e_decide_sem_exigir_resposta() -> None:
    pedidos = []
    observador = ObservadorPresencaJogoRuntime(
        contexto_jogo=lambda: {"ativo": True, "titulo": "Minecraft"},
        capturar=lambda _contexto: "aW1hZ2VtLW5vdmEtZG8tam9nbw==",
        executar_visao=lambda pedido: pedidos.append(dict(pedido)) or True,
        jogo_chave_atual=lambda _contexto: "minecraft",
        interacao_iniciada=lambda: True,
        permitido=lambda: True,
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    with patch(
        "mente_laylay.percepcao.visao_jogo.observador_presenca.assinatura_perceptual",
        return_value="f" * 36,
    ):
        assert observador.verificar_uma_vez() is True
    assert pedidos[0]["tipo"] == "observacao_presenca_proativa"
    assert pedidos[0]["_proativo"] is True
    assert pedidos[0]["_origem_presenca"] == "curiosidade_visual"
    assert "não cobre resposta" not in pedidos[0]["pergunta"].casefold()
    assert "decida por conta própria" in pedidos[0]["pergunta"]


def test_jogo_confirmado_pode_despertar_curiosidade_sem_fala_anterior() -> None:
    pedidos = []
    observador = ObservadorPresencaJogoRuntime(
        contexto_jogo=lambda: {"ativo": True, "titulo": "Forza Horizon 6"},
        capturar=lambda _contexto: "aW1hZ2VtLWZvcnph",
        executar_visao=lambda pedido: pedidos.append(dict(pedido)) or True,
        jogo_chave_atual=lambda _contexto: "forza-horizon-6",
        interacao_iniciada=lambda: False,
        permitido=lambda: True,
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    with patch(
        "mente_laylay.percepcao.visao_jogo.observador_presenca.assinatura_perceptual",
        return_value="a" * 36,
    ):
        assert observador.verificar_uma_vez() is True
    assert len(pedidos) == 1
    assert pedidos[0]["_origem_presenca"] == "curiosidade_visual"
