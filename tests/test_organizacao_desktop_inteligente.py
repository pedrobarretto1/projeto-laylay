from __future__ import annotations

import pytest

from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.coordenador_intencao import (
    resolver_referencias_da_intencao,
)
from mente_laylay.autonomia.porteiro_acoes import (
    normalizar_texto,
    texto_tem_comando_explicito,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_organizacao_desktop,
    texto_expresso_melhor_no_deterministico,
)
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.memoria_mental.continuidade_geral import selecionar_continuidade
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_resultado_execucao
from mente_laylay.percepcao.janelas_sistema import (
    limpar_historico_atividade_janelas,
    organizar_janelas,
    planejar_organizacao_janelas,
    priorizar_janelas_visiveis,
    registrar_atividade_janela_ativa,
)


@pytest.fixture(autouse=True)
def _historico_de_janelas_isolado():
    limpar_historico_atividade_janelas()
    yield
    limpar_historico_atividade_janelas()


def _params(**kwargs):
    return kwargs


def _contexto_roteador() -> dict:
    return {
        "normalizar_texto": normalizar_texto,
        "texto_conversa_casual_sem_acao": lambda _texto: True,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: True,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda texto: (
            texto_expresso_melhor_no_deterministico(
                texto, normalizar_texto=normalizar_texto,
            )
        ),
        "texto_depende_de_contexto": lambda _texto: False,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "detectar_sugestao_indireta": lambda *_args: None,
        "resolver_consulta_recurso_local": lambda _texto: None,
        "modo_jogo_contexto": lambda: {},
        "visao_jogo_tem_analise_recente": lambda: False,
        "sites_diretos": {},
        "apps_map": {"steam": "steam", "discord": "discord"},
    }


def test_linguagem_natural_espacial_nao_cai_em_musica() -> None:
    assert texto_tem_comando_explicito("coloca a Steam na esquerda") is True
    assert detectar_intencao_deterministica_mente(
        "coloca a Steam na esquerda", _contexto_roteador(),
    ) == {
        "intent": "ORGANIZAR_DESKTOP",
        "params": {"left": "steam", "modo": "posicionar"},
    }
    assert detectar_intencao_deterministica_mente(
        "põe o Discord na direita", _contexto_roteador(),
    ) == {
        "intent": "ORGANIZAR_DESKTOP",
        "params": {"right": "discord", "modo": "posicionar"},
    }
    assert detectar_intencao_deterministica_mente(
        "joga o Chrome pro lado direito", _contexto_roteador(),
    ) == {
        "intent": "ORGANIZAR_DESKTOP",
        "params": {"right": "chrome", "modo": "posicionar"},
    }


def test_layout_duplo_e_organizacao_automatica_extraem_parametros_reais() -> None:
    assert detectar_organizacao_desktop(
        "coloca steam na esquerda e discord na direita", params_cb=_params,
    ) == {
        "intent": "ORGANIZAR_DESKTOP",
        "params": {
            "left": "steam", "right": "discord", "modo": "posicionar",
        },
    }
    assert detectar_organizacao_desktop(
        "organiza a area de trabalho", params_cb=_params,
    ) == {
        "intent": "ORGANIZAR_DESKTOP",
        "params": {"modo": "automatico"},
    }


def test_negacao_hipotese_e_pergunta_de_capacidade_nao_movem_janelas() -> None:
    contexto = _contexto_roteador()
    for frase in (
        "não coloca a Steam na esquerda",
        "talvez fosse legal colocar a Steam na esquerda",
        "como eu faria para colocar a Steam na esquerda?",
        "você sabe organizar as janelas?",
    ):
        assert detectar_intencao_deterministica_mente(frase, contexto) is None, frase


def test_continuidade_canonica_preserva_layout_para_tenta_de_novo() -> None:
    estado = registrar_resultado_execucao(
        None,
        {
            "intent": "ORGANIZAR_DESKTOP",
            "alvo": "steam na esquerda",
            "params": {"left": "steam", "modo": "posicionar"},
            "status": "layout_confirmado",
            "executou": True,
            "confirmado": True,
        },
        "coloca a steam na esquerda",
    )

    continuidade = selecionar_continuidade(estado, texto="tenta de novo")

    assert continuidade["dominio"] == "app"
    assert continuidade["intent"] == "ORGANIZAR_DESKTOP"
    assert continuidade["params"]["left"] == "steam"
    assert continuidade["params"]["modo"] == "posicionar"


def test_pronome_de_janela_usa_referencia_canonica_em_vez_de_app_chamado_ela() -> None:
    intencao = detectar_organizacao_desktop(
        "agora coloca ela na direita", params_cb=_params,
    )
    resolvida = resolver_referencias_da_intencao(
        intencao,
        {"referencia_resolvida": {"tipo": "janela", "nome": "Steam"}},
    )

    assert resolvida is not None
    assert resolvida["params"]["right"] == "Steam"
    assert resolvida["params"]["right_original"] == "ela"
    assert resolver_referencias_da_intencao(intencao, {}) is None


def test_catalogo_vivo_explica_posicionamento_e_evidencia_real() -> None:
    mapa = MapaHabilidadesRuntime()
    contexto = mapa.contexto_para_prompt("coloca a Steam na esquerda")
    capacidade = mapa.consultar("ORGANIZAR_DESKTOP")

    assert "- sistema [disponivel]" in contexto
    assert "posicionar aplicativos específicos" in contexto
    assert capacidade["confirmacao_oferecida"] == "estado_observado"
    assert "geometria" in capacidade["evidencia_confirmacao"]
    resposta = mapa.responder_pergunta_capacidade(
        "Lay, você consegue colocar uma janela na esquerda?"
    )
    assert "movo somente os lados pedidos" in resposta
    assert "geometria final" in resposta


class _Janela:
    def __init__(
        self, title: str, left: int, top: int, width: int, height: int,
        *, hwnd: int | None = None,
    ):
        self.title = title
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.isMinimized = False
        self.isMaximized = False
        self.movimentos: list[tuple] = []
        if hwnd is not None:
            self._hWnd = hwnd

    def activate(self):
        return None

    def restore(self):
        self.isMinimized = False
        self.isMaximized = False

    def moveTo(self, left: int, top: int):
        self.left = left
        self.top = top
        self.movimentos.append(("move", left, top))

    def resizeTo(self, width: int, height: int):
        self.width = width
        self.height = height
        self.movimentos.append(("resize", width, height))


class _Gw:
    def __init__(self, janelas: list[_Janela], ativa: _Janela | None = None):
        self.janelas = janelas
        self.ativa = ativa

    def getAllWindows(self):
        return list(self.janelas)

    def getWindowsWithTitle(self, titulo: str):
        termo = str(titulo).casefold()
        return [janela for janela in self.janelas if termo in janela.title.casefold()]

    def getActiveWindow(self):
        return self.ativa


class _Rect:
    left = 0
    top = 0
    right = 0
    bottom = 0


class _User32:
    @staticmethod
    def SystemParametersInfoW(_acao, _param, rect, _flags):
        rect.left = 0
        rect.top = 0
        rect.right = 2560
        rect.bottom = 1040
        return True

    @staticmethod
    def GetWindowThreadProcessId(hwnd, pid):
        pid.value = int(hwnd)
        return 1


class _Ctypes:
    class _Windll:
        user32 = _User32()

    windll = _Windll()

    @staticmethod
    def byref(valor):
        return valor


class _Wintypes:
    RECT = _Rect

    class DWORD:
        def __init__(self):
            self.value = 0

    HWND = int


class _PyAutoGui:
    @staticmethod
    def press(_tecla):
        return None


def test_executor_visual_move_so_a_steam_e_confere_geometria() -> None:
    steam = _Janela("Steam", 300, 80, 900, 700)
    discord = _Janela("Discord", 1400, 100, 900, 700)

    resultado = organizar_janelas(
        _Gw([steam, discord], steam), _PyAutoGui(), _Ctypes(), _Wintypes(),
        "steam", "",
    )

    assert resultado["status"] == "layout_confirmado"
    assert resultado["confirmado"] is True
    assert (steam.left, steam.top, steam.width, steam.height) == (0, 0, 1280, 1040)
    assert discord.movimentos == []


def test_organizacao_automatica_usa_janelas_visiveis_sem_apps_fixos() -> None:
    steam = _Janela("Steam", 300, 80, 900, 700)
    discord = _Janela("Discord", 1400, 100, 800, 650)

    resultado = organizar_janelas(
        _Gw([steam, discord], steam), _PyAutoGui(), _Ctypes(), _Wintypes(),
        "", "",
    )

    assert resultado["status"] == "layout_confirmado"
    assert resultado["nome_esquerda"] == "Steam"
    assert resultado["nome_direita"] == "Discord"
    assert (steam.left, steam.width) == (0, 1280)
    assert (discord.left, discord.width) == (1280, 1280)
    assert resultado["prioridades"][0]["motivos"] == ["janela em foco"]


def test_planejamento_observa_e_prioriza_sem_mover_janelas() -> None:
    steam = _Janela("Steam", 300, 80, 900, 700)
    chrome = _Janela("Google Chrome", 1400, 100, 900, 700)

    resultado = planejar_organizacao_janelas(
        _Gw([steam, chrome], steam),
        ctypes_mod=_Ctypes(),
        wintypes_mod=_Wintypes(),
        processos_audio_ativos_cb=lambda: {"chrome.exe"},
    )

    assert resultado["status"] == "layout_planejado"
    assert resultado["confirmado"] is True
    assert resultado["quantidade"] == 2
    assert resultado["nome_esquerda"] == "Steam"
    assert resultado["nome_direita"] == "Google Chrome"
    assert steam.movimentos == []
    assert chrome.movimentos == []


def test_prioridade_combina_foco_audio_e_uso_recente() -> None:
    editor = _Janela("Visual Studio Code", 0, 0, 900, 700)
    chrome = _Janela("Google Chrome", 0, 0, 900, 700)
    discord = _Janela("Discord", 0, 0, 900, 700)
    agora = 10_000.0
    registrar_atividade_janela_ativa(
        titulo="Google Chrome", executavel="chrome.exe", instante=agora - 300,
    )
    registrar_atividade_janela_ativa(
        titulo="Discord", executavel="discord.exe", instante=agora - 5,
    )

    ranking = priorizar_janelas_visiveis(
        [chrome, discord, editor],
        janela_ativa=editor,
        processos_audio={"chrome.exe"},
        instante=agora,
    )

    assert [item["titulo"] for item in ranking] == [
        "Visual Studio Code", "Google Chrome", "Discord",
    ]
    assert "janela em foco" in ranking[0]["motivos"]
    assert "reproduzindo áudio" in ranking[1]["motivos"]
    assert "uso recente" in ranking[2]["motivos"]


def test_programa_aberto_recentemente_desempata_janelas_sem_historico() -> None:
    recente = _Janela("Aplicativo recente", 0, 0, 800, 600, hwnd=101)
    antigo = _Janela("Aplicativo antigo", 0, 0, 800, 600, hwnd=202)
    agora = 20_000.0

    class _Processo:
        def __init__(self, pid: int):
            self.pid = pid

        def name(self):
            return f"app{self.pid}.exe"

        def create_time(self):
            return agora - (120 if self.pid == 101 else 86_400)

    class _Psutil:
        Process = _Processo

    ranking = priorizar_janelas_visiveis(
        [antigo, recente],
        ctypes_mod=_Ctypes(),
        wintypes_mod=_Wintypes(),
        psutil_mod=_Psutil(),
        instante=agora,
    )

    assert [item["titulo"] for item in ranking] == [
        "Aplicativo recente", "Aplicativo antigo",
    ]
    assert "aberto recentemente" in ranking[0]["motivos"]
