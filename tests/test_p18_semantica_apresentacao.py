from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas
from mente_laylay.autonomia.pre_fluxo_contextual import processar_consulta_sistema_local
from mente_laylay.autonomia.sugestoes_sistema import detectar_sugestao_indireta
from mente_laylay.emocoes.avaliador_eventos import AvaliadorEventosEmocionaisRuntime
from mente_laylay.iot.runtime import RuntimeIoT
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.percepcao.janelas_sistema import observar_programas_abertos
from mente_laylay.personalidade.confirmacao_llm import _motivo_contrato_invalido


class _MemoriaIoT:
    def __init__(self) -> None:
        self.dispositivos: dict[str, dict] = {}

    def salvar_dispositivo_iot(self, dados):
        self.dispositivos[dados["nome"]] = dict(dados)
        return dict(dados)

    def listar_dispositivos_iot(self, ambiente="", *, somente_ativos=True):
        return [
            dict(item) for item in self.dispositivos.values()
            if (not ambiente or item.get("ambiente") == ambiente)
            and (not somente_ativos or item.get("ativo", True))
        ]

    def atualizar_estado_iot(self, nome, estado, **kwargs):
        self.dispositivos[nome]["estado"] = dict(estado)
        return dict(estado)

    def registrar_historico_iot(self, nome, **dados):
        return {"nome": nome, **dados}


def test_proposta_indireta_iot_preserva_deliberacao_sem_inventar_recusa() -> None:
    resultado = detectar_sugestao_indireta(
        "talvez fosse legal deixar a luz vermelha",
    )

    assert resultado is not None
    assert resultado["intent"] == "SUGGEST_ACTION"
    assert resultado["params"]["confianca"] == 0.88
    assert resultado["params"]["execucao_autonoma_elegivel"] is False
    assert resultado["params"]["acao_sugerida"] == {
        "intent": "IOT_CONTROL",
        "params": {
            "acao": "ajustar_cor",
            "alvo": "lampada_quarto",
            "cor": "vermelho",
            "rgb": (255, 0, 0),
            "origem": "usuario_indireto",
        },
    }
    assert "Quer que eu ajuste?" in resultado["params"]["fala"]


def test_pergunta_de_estado_iot_vence_cor_e_nao_chama_resolvedor_livre() -> None:
    pesquisas: list[str] = []
    runtime = RuntimeIoT(
        memoria_sqlite=_MemoriaIoT(),
        falar=lambda *_args: None,
        estado_mental_getter=lambda: {},
        resolver_cor=lambda nome: pesquisas.append(nome) or (1, 2, 3),
        emitir_fala=False,
        modo="simulado",
        log=lambda *_args: None,
    )

    resultado = runtime.detectar("como está a lâmpada do quarto?")

    assert resultado == {
        "intent": "IOT_STATUS",
        "params": {"acao": "status", "alvo": "lampada_quarto"},
    }
    assert pesquisas == []


class _Janela:
    def __init__(self, titulo: str) -> None:
        self.title = titulo


class _GW:
    @staticmethod
    def getAllWindows():
        return [
            _Janela("Projeto Laylay - Visual Studio Code"),
            _Janela("Steam"),
            _Janela("NVIDIA GeForce Overlay"),
            _Janela("Program Manager"),
        ]


class _Psutil:
    class NoSuchProcess(Exception):
        pass

    class AccessDenied(Exception):
        pass

    @staticmethod
    def process_iter(_campos):
        return [
            SimpleNamespace(info={"name": "steam.exe"}),
            SimpleNamespace(info={"name": "discord.exe"}),
            SimpleNamespace(info={"name": "SettingsSyncHost.exe"}),
        ]


def test_observacao_separa_janelas_processos_e_componentes_do_sistema() -> None:
    retrato = observar_programas_abertos(_GW(), _Psutil())

    assert retrato["janelas_visiveis"] == [
        "Projeto Laylay - Visual Studio Code",
        "Steam",
    ]
    assert retrato["processos_segundo_plano"] == ["Discord"]
    assert "NVIDIA GeForce Overlay" in retrato["componentes_filtrados"]
    assert "Program Manager" in retrato["componentes_filtrados"]


def test_consulta_sistema_explica_janela_aba_e_processo_sem_misturar() -> None:
    emitidas: list[str] = []
    tratada, rota = processar_consulta_sistema_local(
        {
            "observar_programas_abertos": lambda: {
                "janelas_visiveis": ["Visual Studio Code", "Opera"],
                "processos_segundo_plano": ["Discord"],
            },
            "_emitir_resposta_curta": (
                lambda _texto, fala, **_kwargs: emitidas.append(fala)
            ),
        },
        "quais programas estão abertos?",
    )

    assert tratada is True
    assert rota == "consulta_programas_abertos"
    assert emitidas and emitidas[0].startswith("Janelas visíveis:")
    assert "Em segundo plano, sem janela visível: Discord." in emitidas[0]
    assert "abas continuam dentro da janela do navegador" in emitidas[0]


def test_abertura_distingue_iniciar_de_focalizar_e_de_nao_agir() -> None:
    estados = iter([
        {"programa_aberto": False, "programa_em_foco": False},
        {"programa_aberto": True, "programa_em_foco": True},
        {"programa_aberto": True, "programa_em_foco": True},
    ])
    with patch("mente_laylay.autonomia.habilidade_janelas.time.sleep", lambda _s: None):
        iniciado = executar_habilidade_janelas(
            "APP_OPEN",
            {"nome_app": "opera"},
            {
                "APPS_MAP": {"opera": "opera"},
                "_resolver_alvo_ambiente": lambda _nome: next(estados),
                "abrir_programa": lambda _nome: True,
                "focar_janela_app": lambda _nome: True,
            },
        )

    assert iniciado["status"] == "app_iniciado_focado"
    assert iniciado["estado_anterior"]["programa_aberto"] is False
    assert iniciado["estado_posterior"]["programa_em_foco"] is True

    focado = executar_habilidade_janelas(
        "APP_OPEN",
        {"nome_app": "opera"},
        {
            "APPS_MAP": {"opera": "opera"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                "programa_em_foco": False,
            },
            "abrir_programa": lambda _nome: True,
            "focar_janela_app": lambda _nome: True,
        },
    )
    assert focado["status"] == "app_focado"

    ja_estava = executar_habilidade_janelas(
        "APP_OPEN",
        {"nome_app": "opera"},
        {
            "APPS_MAP": {"opera": "opera"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                "programa_em_foco": True,
            },
        },
    )
    assert ja_estava["status"] == "ja_aberto_focado"


def test_personalidade_nao_pode_vir_antes_da_verdade_operacional() -> None:
    resultado = ResultadoAcao(
        intent="APP_OPEN",
        status="app_iniciado_focado",
        alvo="Opera",
        executou=True,
        confirmado=True,
    )

    motivo = _motivo_contrato_invalido(
        "Olha quem resolveu aparecer. Iniciei o Opera e trouxe a janela ao foco.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="app_iniciado_focado",
        alvo_declarado="Opera",
    )
    assert motivo == "verdade_operacional_nao_abre_fala"

    assert _motivo_contrato_invalido(
        "Iniciei o Opera e trouxe a janela ao foco. Agora ele resolveu aparecer.",
        resultado=resultado,
        classe="sucesso",
        status_declarado="app_iniciado_focado",
        alvo_declarado="Opera",
    ) == ""


def test_diagnostico_emocional_explica_contencao_em_vez_de_perda_silenciosa() -> None:
    runtime = AvaliadorEventosEmocionaisRuntime(time_cb=lambda: 100.0)
    avaliacao = runtime.avaliar(ResultadoAcao(
        intent="IOT_CONTROL",
        status="indisponivel",
        alvo="lâmpada",
        executou=False,
        confirmado=False,
        texto_usuario="liga a luz",
    ))
    diagnostico = runtime.diagnostico()

    assert avaliacao["permite_expressao"] is False
    assert avaliacao["motivo_expressao"] == "falha_sistema_isolada"
    assert diagnostico["contencoes"] == 1
    assert diagnostico["expressoes"] == 0
    assert diagnostico["ultima_decisao_expressao"] == "conter"
    assert diagnostico["contencoes_por_motivo"] == {
        "falha_sistema_isolada": 1,
    }
