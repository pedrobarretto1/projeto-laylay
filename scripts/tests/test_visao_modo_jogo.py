from __future__ import annotations

import base64
import io

from PIL import Image

from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.cognicao.intencao_visual_jogo import (
    aplicar_pedido_visual_ao_turno,
    detectar_pedido_visao_jogo,
)
from mente_laylay.percepcao.visao_jogo.captura_janela import (
    capturar_janela_jogo_base64,
)
from mente_laylay.percepcao.imagens_multimodais import (
    desempacotar_imagens,
    empacotar_imagens,
)
from mente_laylay.percepcao.visao_jogo.runtime import VisaoJogoRuntime
from mente_laylay.percepcao.visao_jogo.runtime import (
    aplicar_perfil_confirmado_na_resposta,
    higienizar_alegacoes_visao,
    higienizar_inspecao_personagem,
    resposta_pede_complemento,
    resposta_contradiz_identidade_sistema,
    resposta_inventa_falha_da_laylay,
    resposta_contradiz_estado_tela,
)


def test_demonstrativo_curto_recaptura_objeto_durante_contexto_visual():
    pedido = detectar_pedido_visao_jogo(
        "e esse aqui?",
        _jogo_ativo(analise_visual_recente=True),
    )

    assert pedido is not None
    assert pedido["intent"] == "GAME_VISION"
    assert pedido["params"]["tipo"] == "identificacao"
    assert pedido["params"]["requer_cursor"] is False


def test_visao_nao_pode_negar_a_nova_captura_que_acabou_de_receber():
    resposta = higienizar_alegacoes_visao(
        'Eu já analisei a imagem e não tenho como olhar de novo, pois não há arquivo novo.',
        tipo="reanalise",
        contexto={"titulo": "Minecraft Forge 1.20.1"},
        identidade={"nome_candidato": "Minecraft"},
    )

    assert "capturei a tela novamente" in resposta.casefold()
    assert "não tenho como" not in resposta.casefold()


def test_nome_de_item_modificado_sem_incerteza_recebe_ressalva():
    resposta = higienizar_alegacoes_visao(
        "O item que você está olhando é um Baú de Nether e sincroniza tudo.",
        tipo="identificacao",
        contexto={"titulo": "Minecraft Forge 1.20.1"},
        identidade={"nome_candidato": "Minecraft"},
    )

    assert "trato o nome e a mecânica como hipótese" in resposta
from mente_laylay.percepcao.visao_jogo.sessao_jogo import (
    ContextoSessoesJogo,
    confirmar_contexto_janela_sistema,
    extrair_perfil_build,
    identificar_jogo,
)
from mente_laylay.memoria_mental.memoria_jogos import MemoriaJogos


class _ThreadImediata:
    def __init__(self, *, target, daemon=True):
        self.target = target

    def start(self):
        self.target()


def _jogo_ativo(**extras):
    contexto = {
        "ativo": True,
        "processo": "jogo.exe",
        "titulo": "Meu Jogo",
        "limites": {"left": 10, "top": 20, "width": 800, "height": 600},
    }
    contexto.update(extras)
    return contexto


def test_pedido_visual_exige_modo_jogo_ativo():
    assert detectar_pedido_visao_jogo("que minério é esse?", {"ativo": False}) is None


def test_que_erro_e_esse_retoma_contexto_sem_roubo_da_visao():
    assert detectar_pedido_visao_jogo("que erro é esse?", _jogo_ativo()) is None
    pedido = detectar_pedido_visao_jogo("que erro é esse na tela do jogo?", _jogo_ativo())
    assert pedido is not None
    assert pedido["intent"] == "GAME_VISION"


def test_visao_nao_pode_inventar_que_a_propria_laylay_caiu():
    assert resposta_inventa_falha_da_laylay(
        "O script LayLay.py parou de funcionar e a assistente caiu."
    ) is True
    assert resposta_inventa_falha_da_laylay(
        "O jogo parece ter travado na tela de carregamento."
    ) is False


def test_pedido_visual_preserva_pergunta_e_especializa_turno():
    pedido = detectar_pedido_visao_jogo("que minério é esse?", _jogo_ativo())
    assert pedido == {
        "intent": "GAME_VISION",
        "params": {
            "pergunta": "que minério é esse?",
            "tipo": "identificacao",
            "jogo": "Meu Jogo",
            "requer_cursor": False,
        },
    }
    turno = aplicar_pedido_visual_ao_turno(
        {"modalidade": "pergunta", "autoriza_execucao": False}, pedido
    )
    assert turno["modalidade"] == "comando"
    assert turno["autoriza_execucao"] is True
    assert turno["natureza_acao"] == "consulta_visual"
    assert turno["texto_operacional"] == "que minério é esse?"


def test_tipo_de_objeto_apontado_no_jogo_vira_nova_visao():
    pedido = detectar_pedido_visao_jogo(
        "qual o tipo dessa madeira?", _jogo_ativo(titulo="Hytale"),
    )
    assert pedido["params"]["tipo"] == "identificacao"
    assert detectar_pedido_visao_jogo(
        "qual a história desse jogo?", _jogo_ativo(titulo="Hytale"),
    ) is None


def test_pergunta_sem_ancora_visual_nao_captura_so_por_estar_jogando():
    assert detectar_pedido_visao_jogo("você gosta desse jogo?", _jogo_ativo()) is None
    assert detectar_pedido_visao_jogo("quanto é cinquenta mais cinquenta?", _jogo_ativo()) is None


def test_pedidos_naturais_de_reanalise_visual_reusam_contexto_do_jogo():
    frases = (
        "ver de novo",
        "olha novamente",
        "vê outra vez",
        "Lay, tenta analisar de novo",
        "confere mais uma vez",
        "olha esse item de novo",
    )
    for frase in frases:
        pedido = detectar_pedido_visao_jogo(frase, _jogo_ativo())
        assert pedido is not None, frase
        assert pedido["intent"] == "GAME_VISION"
        assert pedido["params"]["tipo"] == "reanalise"

    assert detectar_pedido_visao_jogo("ver de novo", {"ativo": False}) is None


def test_avaliacao_de_item_usa_contexto_visual_e_exige_cursor():
    pedido = detectar_pedido_visao_jogo("Lay, esse item é bom pra mim?", _jogo_ativo())
    assert pedido["intent"] == "GAME_VISION"
    assert pedido["params"]["tipo"] == "avaliacao_item"
    assert pedido["params"]["requer_cursor"] is True
    assert detectar_pedido_visao_jogo("essa arma vale a pena?", _jogo_ativo())["params"]["tipo"] == "avaliacao_item"
    assert detectar_pedido_visao_jogo("esse item aqui é bom?", _jogo_ativo())["params"]["tipo"] == "avaliacao_item"


def test_habilidade_e_arvore_tem_contrato_visual_proprio():
    habilidade = detectar_pedido_visao_jogo(
        "essa habilidade é boa?", _jogo_ativo(analise_visual_recente=True),
    )
    arvore = detectar_pedido_visao_jogo(
        "olha minha árvore de habilidades", _jogo_ativo(),
    )

    assert habilidade["params"]["tipo"] == "avaliacao_habilidade"
    assert habilidade["params"]["requer_cursor"] is True
    assert arvore["params"]["tipo"] == "analise_build"


def test_veredito_curto_retorna_a_analise_visual_em_vez_da_llm_comum():
    contexto = _jogo_ativo(analise_visual_recente=True)

    for frase in ("mas vale a pena pegar ela?", "mas é uma boa pega ela?"):
        pedido = detectar_pedido_visao_jogo(frase, contexto)
        assert pedido is not None, frase
        assert pedido["params"]["tipo"] == "continuacao_visual"
        assert pedido["params"]["requer_cursor"] is False


def test_pedido_natural_para_ver_equipamento_entra_na_visao():
    pedido = detectar_pedido_visao_jogo(
        "pode ver essa bota aqui", _jogo_ativo(titulo="Path of Exile 2")
    )
    assert pedido["intent"] == "GAME_VISION"
    assert pedido["params"]["tipo"] == "avaliacao_item"
    assert pedido["params"]["requer_cursor"] is True

    observacao = detectar_pedido_visao_jogo("consegue olhar isso aqui?", _jogo_ativo())
    assert observacao["params"]["tipo"] == "observacao"
    assert observacao["params"]["requer_cursor"] is False


def test_referencias_visuais_curtas_de_item_nao_escapam_para_llm():
    for frase in ("e essa bota aqui", "ver esse item"):
        pedido = detectar_pedido_visao_jogo(frase, _jogo_ativo(titulo="Path of Exile 2"))
        assert pedido is not None, frase
        assert pedido["intent"] == "GAME_VISION"
        assert pedido["params"]["tipo"] == "avaliacao_item"
        assert pedido["params"]["requer_cursor"] is True


def test_atributos_mostrados_depois_da_analise_viram_nova_captura_visual():
    contexto = _jogo_ativo(titulo="Path of Exile 2")
    contexto["analise_visual_recente"] = True

    for frase in ("aqui estão meus atributos", "esses são meus status", "agora dá pra ver"):
        pedido = detectar_pedido_visao_jogo(frase, contexto)
        assert pedido is not None, frase
        assert pedido["intent"] == "GAME_VISION"
        assert pedido["params"]["tipo"] == "complemento_visual"
        assert pedido["params"]["requer_cursor"] is False


def test_apresentacao_de_atributos_nao_exige_analise_anterior_e_aceita_lay_no_final():
    contexto = _jogo_ativo(titulo="Path of Exile 2")
    contexto["analise_visual_recente"] = False

    pedido = detectar_pedido_visao_jogo("esses sao meus atributos lay", contexto)

    assert pedido is not None
    assert pedido["intent"] == "GAME_VISION"
    assert pedido["params"]["tipo"] == "complemento_visual"
    assert pedido["params"]["requer_cursor"] is False


def test_olha_meus_atributos_usa_inspecao_especifica_em_vez_de_observacao_generica():
    pedido = detectar_pedido_visao_jogo(
        "olha meus atributos", _jogo_ativo(titulo="Path of Exile 2")
    )

    assert pedido is not None
    assert pedido["params"]["tipo"] == "inspecao_personagem"
    assert pedido["params"]["requer_cursor"] is False


def test_inspecao_de_atributos_remove_build_inventada_e_compara_o_maior_corretamente():
    resposta = higienizar_inspecao_personagem(
        "Seu personagem tem 7 de Força, 37 de Destreza e 33 de Inteligência. "
        "Isso faz sentido para uma build focada em magias!",
        perfil={"classe": "Monge"},
    )

    assert "7 de Força" in resposta
    assert "37 de Destreza" in resposta
    assert "33 de Inteligência" in resposta
    assert "focada em magias" not in resposta
    assert "maior valor visível é Destreza, com 37" in resposta
    assert "não confirmam o estilo" in resposta


def test_erro_fonetico_de_item_fica_confinado_ao_pedido_visual():
    pedido = detectar_pedido_visao_jogo(
        "pode ver essa boat", _jogo_ativo(titulo="Path of Exile 2"),
    )

    assert pedido["params"]["tipo"] == "avaliacao_item"
    assert pedido["params"]["pergunta"] == "pode ver essa bota"


def test_tenta_de_novo_so_recaptura_quando_existe_analise_visual_recente():
    contexto = _jogo_ativo(analise_visual_recente=True)
    pedido = detectar_pedido_visao_jogo("tenta de novo", contexto)

    assert pedido["params"]["tipo"] == "reanalise"
    assert detectar_pedido_visao_jogo("tenta de novo", _jogo_ativo()) is None


def test_avaliacao_visual_aceita_nome_de_item_desconhecido_e_continuacao():
    pedido = detectar_pedido_visao_jogo(
        "e esse martelo? ele é bom?",
        _jogo_ativo(titulo="Path of Exile 2"),
    )
    assert pedido["intent"] == "GAME_VISION"
    assert pedido["params"] == {
        "pergunta": "e esse martelo? ele é bom?",
        "tipo": "avaliacao_item",
        "jogo": "Path of Exile 2",
        "requer_cursor": True,
    }
    assert detectar_pedido_visao_jogo("essa espada aqui presta?", _jogo_ativo())["params"]["tipo"] == "avaliacao_item"
    assert detectar_pedido_visao_jogo("e esse? vale a pena?", _jogo_ativo())["params"]["tipo"] == "avaliacao_item"


def test_pergunta_geral_de_rpg_nao_vira_avaliacao_de_item():
    assert detectar_pedido_visao_jogo("vale a pena jogar de mago?", _jogo_ativo()) is None
    assert detectar_pedido_visao_jogo("eu uso magia nesse jogo", _jogo_ativo()) is None
    assert detectar_pedido_visao_jogo("martelo é bom nesse jogo?", _jogo_ativo()) is None
    assert detectar_pedido_visao_jogo("esse jogo é bom?", _jogo_ativo()) is None
    assert detectar_pedido_visao_jogo("essa música é boa?", _jogo_ativo()) is None


def test_roteador_reconhece_visao_antes_do_filtro_de_pergunta():
    resultado = detectar_intencao_deterministica_mente(
        "o que posso melhorar aqui?",
        {
            "mente_integrada_estado": {},
            "detectar_sugestao_indireta": lambda *_: None,
            "modo_jogo_contexto": lambda: _jogo_ativo(),
        },
    )
    assert resultado["intent"] == "GAME_VISION"
    assert resultado["params"]["pergunta"] == "o que posso melhorar aqui?"


def test_captura_usa_apenas_limites_da_janela_e_fica_em_memoria():
    chamadas = []

    def grab(**kwargs):
        chamadas.append(kwargs)
        return Image.new("RGB", (800, 600), (30, 90, 140))

    imagem = capturar_janela_jogo_base64(_jogo_ativo(), image_grab=grab)
    assert imagem
    assert chamadas == [{"bbox": (10, 20, 810, 620), "all_screens": True}]


def test_captura_preta_e_rejeitada():
    imagem = capturar_janela_jogo_base64(
        _jogo_ativo(), image_grab=lambda **_: Image.new("RGB", (800, 600), (0, 0, 0))
    )
    assert imagem == ""


def test_captura_de_item_envia_geral_e_recortes_nativos_separados():
    contexto = _jogo_ativo(cursor={"x": 410, "y": 320})
    imagem_b64 = capturar_janela_jogo_base64(
        contexto,
        image_grab=lambda **_: Image.new("RGB", (800, 600), (30, 90, 140)),
    )
    imagens = desempacotar_imagens(imagem_b64)
    assert len(imagens) == 3
    assert "geral" in imagens[0]["label"].casefold()
    assert "tooltip" in imagens[1]["label"].casefold()
    assert "resolução nativa" in imagens[2]["label"].casefold()
    for item in imagens:
        imagem = Image.open(io.BytesIO(base64.b64decode(item["data"])))
        assert imagem.width == item["width"]
        assert imagem.height == item["height"]


def test_captura_ultrawide_nao_reduz_os_recortes_de_texto():
    contexto = _jogo_ativo(cursor={"x": 2050, "y": 540})
    contexto["limites"] = {"left": 0, "top": 0, "width": 2560, "height": 1080}
    pacote = capturar_janela_jogo_base64(
        contexto,
        image_grab=lambda **_: Image.new("RGB", (2560, 1080), (35, 75, 115)),
    )
    imagens = desempacotar_imagens(pacote)
    assert [(item["width"], item["height"]) for item in imagens] == [
        (1280, 540), (1200, 900), (900, 900),
    ]


def test_runtime_confirma_item_inseguro_usando_somente_recorte_nativo():
    imagens_analisadas = []
    pesquisas = []
    pacote = empacotar_imagens([
        {"label": "geral", "data": "geral", "width": 1920, "height": 810},
        {"label": "detalhe", "data": "detalhe", "width": 900, "height": 900},
    ])

    def analisar(imagem, _prompt):
        imagens_analisadas.append(imagem)
        if len(imagens_analisadas) == 1:
            return (
                "Parece uma bota rara.\n"
                'DADOS_ITEM_JSON: {"nome":"Tempest March","base":"Embossed Boots",'
                '"categoria":"Boots","raridade":"Rare",'
                '"atributos":["15% increased Movement Speed"],"confianca":0.68}'
            )
        return (
            'DADOS_ITEM_JSON: {"nome":"Tempest March","base":"Embossed Boots",'
            '"categoria":"Boots","raridade":"Rare",'
            '"atributos":["15% increased Movement Speed"],"confianca":0.86}'
        )

    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(
            titulo="Path of Exile 2", processo="poe2.exe",
        ),
        capturar=lambda _contexto: pacote,
        obter_cursor=lambda: (410, 320),
        analisar_imagem=analisar,
        pesquisar_item=lambda item, _contexto: pesquisas.append(dict(item)) or {
            "ok": False, "fontes": [],
        },
        falar=lambda *_: None,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
        log=lambda *_: None,
    )
    assert runtime.executar({
        "pergunta": "essa bota é boa?", "tipo": "avaliacao_item",
    }) is True
    assert imagens_analisadas == [pacote, "detalhe"]
    assert pesquisas[0]["nome"] == "Tempest March"
    assert pesquisas[0]["confianca"] >= 0.78


def test_runtime_envia_pergunta_original_e_nao_persiste_imagem():
    prompts = []
    falas = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(),
        capturar=lambda contexto: "imagem-base64",
        analisar_imagem=lambda imagem, prompt: prompts.append((imagem, prompt)) or "Parece ferro, mas a textura não está totalmente nítida.",
        falar=lambda *args: falas.append(args),
        thread_factory=_ThreadImediata,
        log=lambda *_: None,
    )

    assert runtime.executar({"pergunta": "que minério é esse?", "tipo": "identificacao"}) is True
    assert prompts and prompts[0][0] == "imagem-base64"
    assert "Pergunta original do usuário: que minério é esse?" in prompts[0][1]
    assert "Meu Jogo" in prompts[0][1]
    assert falas[-1][0].startswith("Parece ferro")
    assert runtime.em_andamento is False


def test_nova_pergunta_recaptura_quadro_identico_e_usa_o_mais_novo():
    capturas = iter(["quadro-a", "quadro-a", "quadro-b"])
    imagens_analisadas = []
    logs = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(),
        capturar=lambda _contexto: next(capturas),
        analisar_imagem=lambda imagem, _prompt: imagens_analisadas.append(imagem) or "resposta",
        falar=lambda *_: None,
        esperar_recaptura_s=0,
        thread_factory=_ThreadImediata,
        log=logs.append,
    )
    assert runtime.executar({"pergunta": "que madeira é essa?", "tipo": "identificacao"})
    assert runtime.executar({"pergunta": "que bicho é esse?", "tipo": "identificacao"})
    assert imagens_analisadas == ["quadro-a", "quadro-b"]
    assert any("captura idêntica" in item for item in logs)


def test_reanalise_recaptura_tela_e_preserva_pergunta_tipo_e_cursor():
    capturas = iter(["quadro-antigo", "quadro-novo"])
    contextos_captura = []
    prompts = []
    logs = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(
            titulo="Path of Exile 2", processo="poe2.exe",
        ),
        capturar=lambda contexto: (
            contextos_captura.append(dict(contexto)) or next(capturas)
        ),
        obter_cursor=lambda: (410, 320),
        analisar_imagem=lambda _imagem, prompt: prompts.append(prompt) or "resposta",
        falar=lambda *_: None,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
        log=logs.append,
    )

    assert runtime.executar({
        "pergunta": "lay esse sapato é bom?", "tipo": "avaliacao_item",
    })
    assert runtime.executar({"pergunta": "ver de novo", "tipo": "reanalise"})

    assert len(contextos_captura) == 2
    assert contextos_captura[1]["cursor"] == {"x": 410, "y": 320}
    assert "Pergunta original do usuário: lay esse sapato é bom?" in prompts[1]
    assert "Tipo de ajuda: avaliacao_item" in prompts[1]
    assert any("VISÃO:CONTINUIDADE" in item for item in logs)


def test_captura_nova_nao_injeta_observacao_visual_antiga_no_prompt(tmp_path):
    memoria = MemoriaJogos(str(tmp_path / "jogos.sqlite"))
    identidade = identificar_jogo(_jogo_ativo())
    memoria.registrar_observacao(
        identidade, tipo="identificacao", pergunta="que madeira é essa?",
        observacao="Pedro está derrubando uma árvore.", perfil={"classe": "druida"},
    )
    prompts = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(),
        capturar=lambda _contexto: "quadro-com-bicho",
        analisar_imagem=lambda _imagem, prompt: prompts.append(prompt) or "É um animal.",
        falar=lambda *_: None,
        memoria_jogos=memoria,
        thread_factory=_ThreadImediata,
        log=lambda *_: None,
    )
    assert runtime.executar({"pergunta": "que bicho é esse?", "tipo": "identificacao"})
    assert "classe=druida" in prompts[0]
    assert "derrubando uma árvore" not in prompts[0]
    assert "capturada novamente para esta pergunta" in prompts[0]


def test_contexto_visual_rele_processo_da_janela_monitorada():
    class Janela:
        @staticmethod
        def IsWindow(hwnd):
            return hwnd == 77

        @staticmethod
        def GetWindowText(_hwnd):
            return "Hytale"

        @staticmethod
        def GetForegroundWindow():
            return 77

    class ProcessoWin:
        @staticmethod
        def GetWindowThreadProcessId(_hwnd):
            return 1, 4242

    class Processo:
        def name(self):
            return "Hytale.exe"

        def exe(self):
            return r"D:\\Games\\Hytale\\Hytale.exe"

    class Psutil:
        @staticmethod
        def Process(pid):
            assert pid == 4242
            return Processo()

    contexto = confirmar_contexto_janela_sistema(
        _jogo_ativo(hwnd=77, titulo="Minecraft", processo="javaw.exe"),
        win32gui_mod=Janela,
        win32process_mod=ProcessoWin,
        psutil_mod=Psutil,
    )
    assert contexto["titulo"] == "Hytale"
    assert contexto["processo"] == "Hytale.exe"
    assert contexto["pid"] == 4242
    assert contexto["hwnd_em_foco"] is True
    assert contexto["processo_confirmado_sistema"] is True


def test_runtime_prioriza_processo_confirmado_e_corrige_contradicao_visual():
    prompts = []
    falas = []

    def analisar(_imagem, prompt):
        prompts.append(prompt)
        if len(prompts) == 1:
            return "Parece ser Minecraft, não Hytale; Hytale ainda não foi lançado."
        return "No Hytale, o minério parece cobre, embora a textura não esteja totalmente nítida."

    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(hwnd=77),
        confirmar_contexto=lambda contexto: {
            **dict(contexto), "titulo": "Hytale", "processo": "Hytale.exe",
            "pid": 4242, "hwnd_em_foco": True,
            "processo_confirmado_sistema": True,
        },
        capturar=lambda _contexto: "imagem",
        analisar_imagem=analisar,
        falar=lambda *args: falas.append(args),
        thread_factory=_ThreadImediata,
        log=lambda *_: None,
    )
    assert runtime.executar({"pergunta": "que minério é esse?", "tipo": "identificacao"}) is True
    assert "IDENTIDADE DO JOGO CONFIRMADA PELO SISTEMA OPERACIONAL" in prompts[0]
    assert "Executável: Hytale.exe" in prompts[0]
    assert "Rascunho rejeitado" in prompts[1]
    assert falas[-1][0].startswith("No Hytale")


def test_contradicao_so_e_barrada_com_identidade_confirmada():
    confirmada = {
        "nome_candidato": "Hytale", "confirmado": True,
    }
    incerta = {
        "nome_candidato": "Hytale", "confirmado": False,
    }
    resposta = "Parece Minecraft, não Hytale; Hytale ainda não foi lançado."
    assert resposta_contradiz_identidade_sistema(resposta, confirmada) is True
    assert resposta_contradiz_identidade_sistema(resposta, incerta) is False


def test_runtime_nao_analisa_quando_modo_jogo_esta_inativo():
    analisou = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: {"ativo": False},
        capturar=lambda _: "imagem",
        analisar_imagem=lambda *_: analisou.append(True) or "resposta",
        falar=lambda *_: None,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({"pergunta": "olha isso"}) is False
    assert analisou == []


def test_presenca_visual_espera_enquanto_titulo_confirma_carregamento():
    analisou = []
    logs = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Minecraft: NeoForge Loading..."),
        capturar=lambda _: "imagem",
        analisar_imagem=lambda *_: analisou.append(True) or "Uma caverna escura.",
        falar=lambda *_: None,
        thread_factory=_ThreadImediata,
        log=logs.append,
    )

    assert runtime.executar({
        "pergunta": "observe o que está acontecendo",
        "tipo": "observacao_presenca_proativa",
        "_proativo": True,
    }) is True
    assert analisou == []
    assert any("observação adiada" in item for item in logs)


def test_fala_do_usuario_sobre_menu_bloqueia_gameplay_inventado():
    falas = []
    prompts = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Minecraft"),
        capturar=lambda _: "imagem",
        analisar_imagem=lambda _imagem, prompt: prompts.append(prompt) or (
            "Essa caverna está escura e você está explorando minério."
        ),
        falar=lambda *args: falas.append(args),
        thread_factory=_ThreadImediata,
    )
    runtime.observar_texto_usuario("não lay, eu ainda estou no menu")

    assert runtime.executar({"pergunta": "o que aparece?", "tipo": "observacao"}) is True
    assert "ESTADO ATUAL DA TELA CONFIRMADO: menu" in prompts[0]
    assert falas
    assert "ainda está no menu" in falas[-1][0]
    assert "caverna" not in falas[-1][0].casefold()


def test_estado_de_menu_rejeita_descricao_de_caverna():
    assert resposta_contradiz_estado_tela(
        "Essa caverna tem minério e você está explorando.",
        {"estado": "menu"},
    ) is True
    assert resposta_contradiz_estado_tela(
        "O menu principal está aberto.",
        {"estado": "menu"},
    ) is False


def test_titulo_transitorio_do_neoforge_nao_vira_nome_do_jogo():
    identidade = identificar_jogo(_jogo_ativo(
        titulo="Minecraft: NeoForge Loading...",
        processo="javaw.exe",
        processo_confirmado_sistema=True,
    ))

    assert identidade["nome_candidato"] == "Minecraft"


def test_runtime_explica_quando_servico_visual_nao_esta_configurado():
    falas = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(),
        capturar=lambda _: "imagem",
        analisar_imagem=lambda *_: "não deveria chamar",
        falar=lambda *args: falas.append(args),
        credencial_disponivel=False,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({"pergunta": "olha isso"}) is True
    assert "chave do serviço visual" in falas[-1][0]


def test_runtime_avalia_item_com_jogo_mouse_e_build_da_mesma_sessao():
    prompts = []
    contextos_captura = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(),
        capturar=lambda contexto: contextos_captura.append(dict(contexto)) or "imagem",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=lambda _imagem, prompt: prompts.append(prompt) or "É forte para sua build de força, mas falta ver o item equipado.",
        falar=lambda *_: None,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({
        "pergunta": "Minha build é de força, esse item é bom pra mim?",
        "tipo": "avaliacao_item",
    }) is True
    assert contextos_captura[0]["cursor_dentro_janela"] is True
    assert contextos_captura[0]["cursor"] == {"x": 410, "y": 320}
    assert "Jogo candidato: Meu Jogo" in prompts[0]
    assert "build: forca" in prompts[0]
    assert "Não transfira regras" in prompts[0]


def test_runtime_une_visao_pesquisa_e_build_antes_de_falar():
    prompts = []
    sinteses = []
    falas = []
    pesquisas = []

    def analisar(_imagem, prompt):
        prompts.append(prompt)
        return (
            "As botas parecem úteis, mas ainda falta validar a base.\n"
            'DADOS_ITEM_JSON: {"nome":"Tempest March","base":"Embossed Boots",'
            '"categoria":"Boots","raridade":"Rare","nivel_item":18,'
            '"atributos":["15% increased Movement Speed"],'
            '"termos_pesquisa":["Embossed Boots"],"confianca":0.9}'
        )

    def sintetizar(prompt):
        sinteses.append(prompt)
        return (
            "Para seu monge, a velocidade ajuda no posicionamento, mas ainda preciso "
            "ver as botas equipadas para afirmar que a troca compensa."
        )

    def pesquisar(item, contexto):
        pesquisas.append((dict(item), dict(contexto)))
        return {
            "ok": True, "cache": True,
            "fontes": [{
                "fonte": "poe2wiki", "titulo": "Embossed Boots",
                "resumo": "Embossed Boots é uma base de botas com evasão.",
                "url": "https://www.poe2wiki.net/wiki/Embossed_Boots",
                "confianca": 0.9,
            }],
        }

    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(
            titulo="Path of Exile 2", processo="poe2.exe",
        ),
        capturar=lambda _contexto: "imagem",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=analisar,
        pesquisar_item=pesquisar,
        sintetizar_texto=sintetizar,
        falar=lambda *args: falas.append(args),
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
        log=lambda *_: None,
    )
    runtime.observar_texto_usuario("estou jogando de monge")

    assert runtime.executar({"pergunta": "esse sapato é bom?", "tipo": "avaliacao_item"})
    assert len(prompts) == 1
    assert len(sinteses) == 1
    assert pesquisas[0][0]["base"] == "Embossed Boots"
    assert pesquisas[0][1]["perfil"]["classe"] == "monge"
    assert "EVIDÊNCIA EXTERNA VERIFICADA" in sinteses[0]
    assert "Embossed Boots é uma base" in sinteses[0]
    assert falas[-1][0].startswith("Para seu monge")
    assert "DADOS_ITEM_JSON" not in falas[-1][0]


def test_runtime_item_publica_fases_cooperativas_sem_imagem_ou_texto_bruto():
    eventos = []
    falas = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(
            titulo="Path of Exile 2", processo="poe2.exe",
        ),
        capturar=lambda _contexto: "imagem-secreta-base64",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=lambda _imagem, _prompt: (
            "A bota tem velocidade útil.\n"
            'DADOS_ITEM_JSON: {"nome":"Passo Solar","base":"Boots",'
            '"categoria":"Boots","atributos":["10% movement speed"],'
            '"confianca":0.91}'
        ),
        pesquisar_item=lambda *_args: {"ok": False, "fontes": []},
        falar=lambda *args: falas.append(args),
        progresso_cooperativo_cb=lambda evento: eventos.append(dict(evento)),
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
        log=lambda *_: None,
    )

    assert runtime.executar({
        "pergunta": "essa bota é boa?", "tipo": "avaliacao_item",
        "_plano_cooperativo_id": "plano-123",
    })
    assert [evento["fase"] for evento in eventos] == [
        "leitura_visual", "pesquisa", "parecer_final",
    ]
    assert all(evento["plano_id"] == "plano-123" for evento in eventos)
    assert "imagem-secreta-base64" not in str(eventos)
    assert "Passo Solar" not in str(eventos)
    assert len(falas) == 1


def test_runtime_nao_adivinha_item_sem_mouse_dentro_do_jogo():
    falas = []
    analisou = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(),
        capturar=lambda _contexto: "imagem",
        obter_cursor=lambda: (2, 2),
        analisar_imagem=lambda *_: analisou.append(True) or "resposta",
        falar=lambda *args: falas.append(args),
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({"pergunta": "esse item é bom pra mim?", "tipo": "avaliacao_item"}) is True
    assert analisou == []
    assert "mouse sobre o item" in falas[-1][0]


def test_contexto_de_build_nao_vaza_entre_jogos():
    sessoes = ContextoSessoesJogo()
    jogo_a = identificar_jogo(_jogo_ativo(titulo="RPG A", processo="rpga.exe"))
    jogo_b = identificar_jogo(_jogo_ativo(titulo="RPG B", processo="rpgb.exe"))
    assert sessoes.observar(jogo_a, "minha build é de força") == {"build": "forca"}
    assert sessoes.perfil(jogo_b) == {}


def test_runtime_aprende_build_em_turno_anterior_da_sessao():
    prompts = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(),
        capturar=lambda _contexto: "imagem",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=lambda _imagem, prompt: prompts.append(prompt) or "resposta",
        falar=lambda *_: None,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    assert runtime.observar_texto_usuario("Nesse jogo sou um mago, nível 24") == {
        "classe": "mago",
        "nivel": 24,
    }
    assert runtime.executar({"pergunta": "esse item é bom pra mim?", "tipo": "avaliacao_item"}) is True
    assert "classe: mago" in prompts[0]
    assert "nivel: 24" in prompts[0]


def test_classe_aceita_fala_natural_estou_jogando_de():
    assert extrair_perfil_build("estou jogando de monge") == {"classe": "monge"}
    assert extrair_perfil_build("tô de arqueira") == {"classe": "arqueira"}


def test_memoria_persistente_e_isolada_por_jogo(tmp_path):
    memoria = MemoriaJogos(str(tmp_path / "jogos.sqlite"))
    jogo_a = identificar_jogo(_jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"))
    jogo_b = identificar_jogo(_jogo_ativo(titulo="Outro RPG", processo="outro.exe"))

    memoria.registrar_observacao(
        jogo_a, tipo="avaliacao_item", pergunta="esse escudo é bom?",
        observacao="Tem regeneração, mas faltava conhecer a classe.",
        perfil={"classe": "monge"},
    )

    reaberta = MemoriaJogos(str(tmp_path / "jogos.sqlite"))
    assert reaberta.carregar_perfil(jogo_a) == {"classe": "monge"}
    assert reaberta.listar_recentes(jogo_a)[0]["pergunta"] == "esse escudo é bom?"
    assert reaberta.carregar_perfil(jogo_b) == {}
    assert reaberta.listar_recentes(jogo_b) == []


def test_curiosidade_visual_proativa_nao_abre_pendencia_de_resposta():
    eventos = []
    sugestoes = []
    resposta = (
        "Esse lugar parece diferente. Será que tem alguma coisa escondida ali?\n"
        'PRESENCA_JOGO_JSON: {"relevante":true,"categoria":"curiosidade",'
        '"fala":"Esse lugar parece diferente. Será que tem alguma coisa escondida ali?",'
        '"motivo":"área nova","evidencias":["estrutura incomum visível"],'
        '"confianca":0.86,"momento_seguro":true,"clima_musical":"calmo"}'
    )
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Minecraft", processo="javaw.exe"),
        capturar=lambda _contexto: "imagem-nova",
        analisar_imagem=lambda *_args: resposta,
        falar=lambda *_args: True,
        processar_sugestao_proativa=lambda *args: sugestoes.append(args) or True,
        registrar_analise_cb=lambda evento: eventos.append(dict(evento)),
        thread_factory=_ThreadImediata,
    )

    assert runtime.executar({
        "pergunta": "observe por curiosidade",
        "tipo": "observacao_presenca_proativa",
        "_proativo": True,
        "_imagem_pre_capturada": "imagem-nova",
    }) is True

    assert sugestoes and sugestoes[0][0]["categoria"] == "curiosidade"
    assert eventos[-1]["solicita_complemento"] is False


def test_complemento_reanalisa_mesma_imagem_e_fecha_o_fio_visual():
    prompts = []
    capturas = []
    eventos = []

    def analisar(_imagem, prompt):
        prompts.append(prompt)
        if len(prompts) == 1:
            return "O escudo parece útil, mas sem saber sua classe não consigo fechar a comparação."
        return "Como monge, ele ajuda na sobrevivência, mas o bônus de dano não favorece sua ofensiva."

    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"),
        capturar=lambda _contexto: capturas.append(True) or "mesma-imagem",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=analisar,
        falar=lambda *_: True,
        registrar_analise_cb=lambda evento: eventos.append(dict(evento)),
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({
        "pergunta": "esse item é bom?", "tipo": "avaliacao_item",
    }) is True
    identidade = identificar_jogo(_jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"))
    pendencia = {
        "status": "ativa", "foi_falada": True, "origem": "visao_jogo",
        "dominio": "jogo", "conteudo": eventos[0]["resposta"],
        "opcoes": [{"jogo_chave": identidade["chave"]}],
    }

    assert runtime.continuar_pendencia("estou jogando de monge", pendencia) is True

    assert capturas == [True]
    assert len(prompts) == 2
    assert "classe: monge" in prompts[1]
    assert "estou jogando de monge" in prompts[1]
    assert eventos[0]["solicita_complemento"] is True
    assert eventos[1]["solicita_complemento"] is False


def test_veredito_de_habilidade_e_imediato_e_nao_chama_modelo_novamente():
    falas = []
    analises = []

    def analisar(_imagem, prompt):
        analises.append(prompt)
        return (
            "Esse nó recupera vida ao matar inimigos, então favorece a limpeza de grupos.\n"
            'DADOS_HABILIDADE_JSON: {"nome":"Colheita Vital","tipo":"passiva",'
            '"efeito":"recupera vida ao matar inimigos","custo_pontos":1,'
            '"beneficios":["sustentação contra grupos"],"limitacoes":["não ativa em chefes"],'
            '"sinergias":[],"situacoes_fortes":["grupos"],"situacoes_fracas":["chefes"],'
            '"termos_pesquisa":["life on kill"],"confianca":0.91}'
        )

    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"),
        capturar=lambda _contexto: "imagem-arvore",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=analisar,
        falar=lambda texto, *_: falas.append(texto),
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )

    assert runtime.executar({
        "pergunta": "essa habilidade é boa?", "tipo": "avaliacao_habilidade",
    }) is True
    assert runtime.continuar_analise_recente("mas vale a pena pegar ela?") is True

    assert len(analises) == 1
    assert "grupos" in falas[-1]
    assert "chefes" in falas[-1]


def test_pedido_de_atributo_ilegivel_abre_continuacao_visual():
    resposta = (
        "A resistência elétrica ajuda, mas não consigo ver a velocidade de movimento "
        "ou a defesa base para confirmar se é o melhor upgrade."
    )

    assert resposta_pede_complemento(resposta) is True


def test_dado_complementar_do_item_usa_sintese_textual_sem_reenviar_imagem():
    analises_visuais = []
    sinteses = []
    capturas = []
    eventos = []

    def analisar(_imagem, prompt):
        analises_visuais.append(prompt)
        return (
            "As botas ajudam com Mana, mas não consigo ver a evasão para confirmar a defesa.\n"
            'DADOS_ITEM_JSON: {"nome":"Botas do Viajante","defesas":{},'
            '"atributos":{"mana":12},"requisitos":{"nivel":11},"ilegivel":["evasao"]}'
        )

    def sintetizar(prompt):
        sinteses.append(prompt)
        return (
            "Com 15 de evasão, elas servem como uma melhoria defensiva básica no nível 11. "
            "Para o seu Monge, Mana e evasão ajudam agora, embora ainda não sejam botas fortes."
        )

    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"),
        capturar=lambda _contexto: capturas.append(True) or "imagem-item",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=analisar,
        sintetizar_texto=sintetizar,
        falar=lambda *_: True,
        registrar_analise_cb=lambda evento: eventos.append(dict(evento)),
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    runtime.observar_texto_usuario("estou jogando de monge")
    assert runtime.executar({
        "pergunta": "esse item é bom?", "tipo": "avaliacao_item",
    }) is True
    identidade = identificar_jogo(_jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"))
    pendencia = {
        "status": "ativa", "foi_falada": True, "origem": "visao_jogo",
        "dominio": "jogo", "conteudo": eventos[0]["resposta"],
        "opcoes": [{"jogo_chave": identidade["chave"]}],
    }

    assert runtime.continuar_pendencia("ela tem 15 de evasão", pendencia) is True

    assert capturas == [True]
    assert len(analises_visuais) == 1
    assert len(sinteses) == 1
    assert "ela tem 15 de evasão" in sinteses[0]
    assert "Botas do Viajante" in sinteses[0]
    assert "classe': 'monge'" in sinteses[0]
    assert eventos[-1]["solicita_complemento"] is False


def test_olha_de_novo_nao_e_consumido_como_dado_complementar():
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"),
        capturar=lambda _contexto: "imagem-item",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=lambda *_: "Não consigo ver a evasão para confirmar.",
        falar=lambda *_: True,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({
        "pergunta": "esse item é bom?", "tipo": "avaliacao_item",
    }) is True
    identidade = identificar_jogo(_jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"))
    pendencia = {
        "status": "ativa", "foi_falada": True, "origem": "visao_jogo",
        "dominio": "jogo", "conteudo": "Não consigo ver a evasão para confirmar.",
        "opcoes": [{"jogo_chave": identidade["chave"]}],
    }

    assert runtime.continuar_pendencia("Lay, olha de novo", pendencia) is False


def test_comando_iot_nao_e_consumido_por_pendencia_visual():
    chamadas = []
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"),
        capturar=lambda _contexto: "imagem-item",
        obter_cursor=lambda: (410, 320),
        analisar_imagem=lambda *_: chamadas.append(True) or "Não consigo ver sua classe.",
        falar=lambda *_: True,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )
    assert runtime.executar({"pergunta": "esse item é bom?", "tipo": "avaliacao_item"})
    identidade = identificar_jogo(_jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"))
    pendencia = {
        "status": "ativa", "foi_falada": True, "origem": "visao_jogo",
        "dominio": "jogo", "conteudo": "Não consigo ver sua classe.",
        "opcoes": [{"jogo_chave": identidade["chave"]}],
    }

    assert runtime.continuar_pendencia("liga a luz", pendencia) is False
    assert len(chamadas) == 1


def test_nivel_da_build_e_corrigido_sem_alterar_requisito_do_item():
    resposta = "Para sua build de Monge nível 12, estas botas exigem nível 15."
    corrigida = aplicar_perfil_confirmado_na_resposta(resposta, {"nivel": 13})

    assert "build de Monge nível 13" in corrigida
    assert "exigem nível 15" in corrigida


def test_atualizacao_pura_de_nivel_responde_localmente_sem_analisar_imagem(tmp_path):
    falas = []
    chamadas_visuais = []
    memoria = MemoriaJogos(str(tmp_path / "jogos.sqlite"))
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(
            titulo="Path of Exile 2", processo="PathOfExileSteam.exe",
        ),
        analisar_imagem=lambda *_: chamadas_visuais.append(True) or "não deveria chamar",
        falar=lambda texto, *_: falas.append(texto),
        memoria_jogos=memoria,
        confirmar_contexto=lambda contexto: contexto,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )

    assert runtime.processar_atualizacao_perfil(
        "só um aviso, estou no nível 12"
    ) is True

    identidade = identificar_jogo(_jogo_ativo(
        titulo="Path of Exile 2", processo="PathOfExileSteam.exe",
    ))
    assert memoria.carregar_perfil(identidade)["nivel"] == 12
    assert chamadas_visuais == []
    assert "nível 12" in falas[-1]


def test_atualizacao_de_nivel_com_pergunta_nova_nao_e_consumida():
    runtime = VisaoJogoRuntime(
        contexto_jogo=lambda: _jogo_ativo(titulo="Path of Exile 2", processo="poe2.exe"),
        analisar_imagem=lambda *_: "resposta",
        falar=lambda *_: None,
        esperar_tooltip_s=0,
        thread_factory=_ThreadImediata,
    )

    assert runtime.processar_atualizacao_perfil(
        "estou no nível 12, essa bota é melhor?"
    ) is False


def test_nivel_confirmado_corrige_contradicao_da_visao():
    resposta = (
        "Essas botas exigem nível 11 e você está no nível 5, então não pode "
        "equipá-las agora. Guarde para quando subir de nível!"
    )

    corrigida = aplicar_perfil_confirmado_na_resposta(resposta, {"nivel": 12})

    assert "nível 5" not in corrigida
    assert "requisito de nível 11 já está atendido pelo seu nível 12" in corrigida
