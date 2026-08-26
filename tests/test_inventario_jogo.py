from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw

from mente_laylay.cognicao.intencao_visual_jogo import detectar_pedido_visao_jogo
from mente_laylay.memoria_mental.memoria_jogos import MemoriaJogos
from mente_laylay.percepcao.visao_jogo.inventario import extrair_dados_inventario
from mente_laylay.percepcao.visao_jogo.observador_inventario import (
    ObservadorInventarioJogoRuntime,
    assinatura_perceptual,
    distancia_assinaturas,
)
from mente_laylay.percepcao.visao_jogo.runtime import VisaoJogoRuntime
from mente_laylay.percepcao.visao_jogo.sessao_jogo import identificar_jogo


class _ThreadImediata:
    def __init__(self, *, target, daemon=True):
        self.target = target

    def start(self):
        self.target()


def _contexto():
    return {
        "ativo": True, "titulo": "Path of Exile 2",
        "processo": "PathOfExileSteam.exe", "pid": 42,
        "limites": {"left": 0, "top": 0, "width": 1280, "height": 720},
    }


def _imagem(inverter=False):
    imagem = Image.new("RGB", (160, 90), "black")
    desenho = ImageDraw.Draw(imagem)
    desenho.rectangle((0 if not inverter else 80, 0, 79 if not inverter else 159, 89), fill="white")
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_pedido_olha_meu_inventario_vira_inspecao_estrutural():
    pedido = detectar_pedido_visao_jogo("Lay, olha meu inventário", _contexto())

    assert pedido is not None
    assert pedido["params"]["tipo"] == "inspecao_inventario"
    assert pedido["params"]["requer_cursor"] is False


def test_contrato_normaliza_slots_multiplos_e_remove_marcadores():
    resposta = (
        "Encontrei seus equipamentos atuais.\n"
        'DADOS_INVENTARIO_JSON: {"tela_inventario_ativa":true,"personagem":"Monge",'
        '"slots":[{"slot":"anel","nome":"Anéis","quantidade":2,"confianca":0.9}],'
        '"equipados":[{"slot":"anel","nome":"Elo Solar","atributos":["+10 vida"],'
        '"confianca":0.88}],"confianca":0.91,"ambiguidades":[]}\n'
        'SUGESTAO_PROATIVA_JSON: {"relevante":false,"fala":"","confianca":0.9}'
    )

    fala, inventario, sugestao = extrair_dados_inventario(resposta)

    assert fala == "Encontrei seus equipamentos atuais."
    assert inventario["esquema"]["anel"]["quantidade"] == 2
    assert inventario["equipados"]["anel"][0]["nome"] == "Elo Solar"
    assert sugestao["relevante"] is False


def test_inspecao_visual_persiste_mapa_dinamico_e_arma_observador(tmp_path):
    memoria = MemoriaJogos(str(tmp_path / "mente.sqlite"))
    mapeamentos = []
    falas = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=_contexto,
        capturar=lambda _ctx: _imagem(),
        obter_cursor=lambda: (100, 100),
        analisar_imagem=lambda _img, _prompt: (
            "Mapeei o inventário e encontrei botas e dois anéis.\n"
            'DADOS_INVENTARIO_JSON: {"tela_inventario_ativa":true,"personagem":"Monge",'
            '"slots":[{"slot":"botas","quantidade":1,"confianca":0.95},'
            '{"slot":"anel","quantidade":2,"confianca":0.9}],'
            '"equipados":[{"slot":"botas","nome":"Passos","confianca":0.9}],'
            '"confianca":0.92,"ambiguidades":[]}'
        ),
        falar=lambda texto, *_: falas.append(texto),
        memoria_jogos=memoria,
        ao_mapear_inventario=lambda identidade, inv, imagem, proativo: mapeamentos.append(
            (dict(identidade), dict(inv), imagem, proativo)
        ),
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )

    assert runtime.executar({
        "pergunta": "olha meu inventário", "tipo": "inspecao_inventario",
    }) is True

    identidade = identificar_jogo(_contexto())
    salvo = memoria.carregar_inventario(identidade)
    assert salvo["esquema"]["anel"]["quantidade"] == 2
    assert salvo["equipados"]["botas"][0]["nome"] == "Passos"
    assert mapeamentos[0][3] is False
    assert falas == ["Mapeei o inventário e encontrei botas e dois anéis."]


def test_correcao_essa_e_minha_atual_atualiza_slot_sem_nova_visao(tmp_path):
    memoria = MemoriaJogos(str(tmp_path / "mente.sqlite"))
    chamadas = []
    falas = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=_contexto,
        capturar=lambda _ctx: _imagem(),
        obter_cursor=lambda: (100, 100),
        analisar_imagem=lambda *_: chamadas.append(True) or (
            "Essa bota tem evasão.\n"
            'DADOS_ITEM_JSON: {"nome":"Passos","categoria":"armadura",'
            '"slot":"botas","estado":"inventario","equipado":false,'
            '"atributos":["15 evasão"],"confianca":0.9}'
        ),
        falar=lambda texto, *_: falas.append(texto),
        memoria_jogos=memoria,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({"pergunta": "essa bota é boa?", "tipo": "avaliacao_item"})

    assert runtime.aplicar_referencia_item("essa é minha atual") is True

    identidade = identificar_jogo(_contexto())
    salvo = memoria.carregar_inventario(identidade)
    assert len(chamadas) == 1
    assert salvo["equipados"]["botas"][0]["nome"] == "Passos"
    assert "item atual" in falas[-1]


def test_observador_so_analisa_quando_quadro_muda():
    imagens = [_imagem(), _imagem(), _imagem(True)]
    chamadas = []
    relogio = [100.0]
    observador = ObservadorInventarioJogoRuntime(
        contexto_jogo=_contexto,
        capturar=lambda _ctx: imagens.pop(0),
        executar_visao=lambda params: chamadas.append(dict(params)) or True,
        jogo_chave_atual=lambda _ctx: "poe2",
        clock=lambda: relogio[0],
        intervalo_s=8,
        limiar_mudanca=10,
        log=lambda *_: None,
    )
    inicial = imagens[0]
    observador.armar(jogo_chave="poe2", imagem=inicial)

    assert observador.verificar_uma_vez() is False
    assert observador.verificar_uma_vez() is False
    assert observador.verificar_uma_vez() is True
    assert len(chamadas) == 1
    assert chamadas[0]["_proativo"] is True
    assert distancia_assinaturas(
        assinatura_perceptual(inicial), assinatura_perceptual(_imagem(True))
    ) >= 10
