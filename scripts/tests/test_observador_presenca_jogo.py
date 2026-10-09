from mente_laylay.percepcao.visao_jogo.observador_presenca import (
    ObservadorPresencaJogoRuntime,
)
from unittest.mock import patch
import base64
import io
import pytest
from PIL import Image
from mente_laylay.percepcao.imagens_multimodais import desempacotar_imagens


def _quadro_inicial_e_final():
    quadros = []
    for horizontal in (False, True):
        imagem = Image.new("RGB", (32, 18), "black")
        imagem.paste("white", (0, 0, 32 if horizontal else 16, 9 if horizontal else 18))
        arquivo = io.BytesIO()
        imagem.save(arquivo, format="JPEG")
        quadros.append(base64.b64encode(arquivo.getvalue()).decode())
    return quadros


def test_sequencia_visual_nao_dispara_duas_analises_por_minuto():
    observador = ObservadorPresencaJogoRuntime(
        contexto_jogo=lambda: {}, capturar=lambda _: "", executar_visao=lambda _: False,
        jogo_chave_atual=lambda _: "", intervalo_s=35,
    )
    assert observador.intervalo_s >= 60, "par temporal aumenta o custo da mesma chamada"


def test_presenca_recebe_sequencia_curta_do_mesmo_jogo_em_uma_analise():
    quadros = _quadro_inicial_e_final()
    capturas = iter(quadros)
    pedidos, esperas = [], []
    observador = ObservadorPresencaJogoRuntime(
        contexto_jogo=lambda: {"ativo": True, "hwnd": 7, "pid": 1},
        capturar=lambda _: next(capturas),
        executar_visao=lambda pedido: pedidos.append(pedido) or True,
        jogo_chave_atual=lambda _: "jogo:1", sleep=esperas.append, log=lambda _: None,
    )
    assert observador.verificar_uma_vez()
    imagens = desempacotar_imagens(pedidos[0]["_imagem_pre_capturada"])
    assert [i["data"] for i in imagens] == quadros, "acao exige ordem temporal, nao um objeto isolado"
    assert imagens[0]["label"].startswith("Quadro temporal 1")
    assert imagens[1]["label"].startswith("Quadro temporal 2")
    assert len(esperas) == len(pedidos) == observador._analises == 1
    assert pedidos[0]["_intervalo_quadros_s"] == esperas[0]
    assert "acontecimento" in pedidos[0]["pergunta"]


@pytest.mark.parametrize("falha", ["inativo", "outro_jogo", "outra_janela", "captura", "ocupado", "mudou_na_segunda"])
def test_sequencia_temporal_incompleta_ou_de_outro_alvo_nao_e_analisada(falha):
    quadros = _quadro_inicial_e_final()
    capturas, pedidos = [], []
    contexto = {"ativo": True, "hwnd": 7, "pid": 1, "chave": "jogo:1"}
    def capturar(_):
        capturas.append(True)
        if len(capturas) == 2 and falha == "mudou_na_segunda": contexto["hwnd"] = 8
        return quadros[0] if len(capturas) == 1 else "" if falha == "captura" else quadros[1]
    def intervalo(_):
        if falha == "inativo": contexto["ativo"] = False
        if falha == "outro_jogo": contexto["chave"] = "jogo:2"
        if falha == "outra_janela": contexto["hwnd"] = 8
    observador = ObservadorPresencaJogoRuntime(
        contexto_jogo=lambda: contexto, capturar=capturar,
        executar_visao=lambda p: pedidos.append(p) or True,
        jogo_chave_atual=lambda c: c["chave"],
        visao_ocupada=lambda: falha == "ocupado" and bool(capturas),
        sleep=intervalo, log=lambda _: None,
    )
    assert observador.verificar_uma_vez() is False
    assert pedidos == [] and observador._analises == 0


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
    assert "decida por conta própria" in pedidos[0]["pergunta"].casefold()


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
