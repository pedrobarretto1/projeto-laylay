from __future__ import annotations

import time

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    resolver_comando_midia_contextual,
)
from mente_laylay.percepcao.janelas_sistema import maximizar_janela
from tests.fakes_navegador import NavegadorOperacoesFake


class _Estado:
    def __init__(self, mental: dict | None = None) -> None:
        self.mental = dict(mental or {})


def _contexto_deterministico(mente: dict) -> dict:
    return {
        "normalizar_texto": lambda texto: str(texto).casefold().strip(),
        "texto_conversa_casual_sem_acao": lambda _texto: False,
        "texto_bloqueia_playlist_agora": lambda _texto: False,
        "texto_social_curto": lambda _texto: False,
        "ignorar_token_solto": lambda _texto: False,
        "fluxo_prioritario_da_ia": lambda _texto: True,
        "texto_expresso_melhor_no_deterministico": lambda _texto: False,
        "texto_depende_de_contexto": lambda _texto: True,
        "limpar_destino_pc_b": lambda texto: texto,
        "target_from_params": lambda _params, _texto: "pc_a",
        "detectar_intencao_iot": lambda *_args: None,
        "detectar_sugestao_indireta": lambda *_args: None,
        "resolver_consulta_recurso_local": lambda _texto: None,
        "mente_integrada_estado": mente,
        "sites_diretos": {},
        "apps_map": {},
    }


def test_escrita_contextual_atravessa_a_porta_deterministica() -> None:
    caminho = r"C:\Users\pedro\Downloads\teste manutenção.txt"
    mente = {
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": "teste manutenção.txt",
            "caminho": caminho,
        },
    }

    for fala, conteudo in (
        ('Escreve "teste concluído" nele.', "teste concluído"),
        ("escreve cralos nele", "cralos"),
        ("grava azul e verde nele", "azul e verde"),
    ):
        resultado = detectar_intencao_deterministica_mente(
            fala,
            _contexto_deterministico(mente),
        )
        assert resultado == {
            "intent": "CREATE_FILE",
            "params": {
                "alvo": caminho,
                "conteudo": conteudo,
                "editar_existente": True,
            },
        }


def test_resumo_de_pagina_sem_executor_nunca_some_em_silencio() -> None:
    falas: list[str] = []
    resultados: list[tuple[bool, str]] = []
    estado = _Estado()
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "_registrar_resultado_execucao": (
                lambda _intent, _texto, executou, **kwargs:
                resultados.append((executou, kwargs.get("status", "")))
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("Resume a página atual") is True
    assert resultados == [(False, "executor_indisponivel")]
    assert "não está conectado" in falas[-1]


def test_busca_de_codigo_abre_primeiro_resultado_no_mesmo_turno() -> None:
    caminho = r"C:\projeto\mente_laylay\iot\controlador.py"
    estado = _Estado()
    execucoes: list[dict] = []
    registros: list[tuple[str, bool, str]] = []
    cadeia_generica: list[str] = []

    def executar(intencao: dict, _texto: str) -> bool:
        execucoes.append(intencao)
        if intencao["intent"] == "FILE_SEARCH":
            estado.mental["ultima_estrutura_arquivo_params"] = {
                "tipo": "pesquisa_semantica",
                "consulta": "código que controla a lâmpada",
                "resultados": [caminho],
                "nomes": ["controlador.py"],
            }
        return True

    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
            "executar_intencao": executar,
            "processar_comandos_em_cadeia": (
                lambda texto, *_args: cadeia_generica.append(texto) or True
            ),
            "_registrar_resultado_execucao": (
                lambda intencao, _texto, executou, *, origem, **_kwargs:
                registros.append((intencao["intent"], executou, origem))
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "Encontra o código que controla a lâmpada e abre o primeiro resultado"
    ) is True
    assert [item["intent"] for item in execucoes] == [
        "FILE_SEARCH", "FILE_OPEN_RESULT",
    ]
    assert execucoes[1]["params"]["caminho"] == caminho
    assert cadeia_generica == []
    assert [item[2] for item in registros] == [
        "prioritario_cooperativo_busca_arquivo:1",
        "prioritario_cooperativo_busca_arquivo:2",
    ]


def test_controles_curtos_exigem_midia_recente_e_preservam_continuidade() -> None:
    recente = {
        "ultima_acao_intent": "MEDIA_CONTROL",
        "ultima_habilidade": "midia",
        "ts": time.time(),
    }

    assert resolver_comando_midia_contextual(
        "pausa",
        mente_integrada_estado=recente,
        contexto_musical=False,
    )["params"]["acao"] == "pause"
    assert resolver_comando_midia_contextual(
        "continua",
        mente_integrada_estado=recente,
        contexto_musical=False,
    )["params"]["acao"] == "play"
    assert resolver_comando_midia_contextual(
        "continua",
        mente_integrada_estado={},
        contexto_musical=False,
    ) is None


def test_prime_video_mapeado_abre_site_sem_tentar_app_local() -> None:
    navegador = NavegadorOperacoesFake()
    apps: list[str] = []
    resultado = executar_habilidade_janelas(
        "APP_OPEN",
        {"nome_app": "Prime Video"},
        {
            "SITES_DIRECTOS": {
                "prime video": "https://www.primevideo.com/",
            },
            "APPS_MAP": {},
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
            "_resolver_alvo_ambiente": lambda _nome: {"aba_aberta": False},
            "_registro_navegador_operacoes_runtime": navegador,
            "abrir_programa": lambda nome: apps.append(nome) or True,
        },
    )

    assert resultado["status"] == "site_aberto"
    assert navegador.chamadas[0][0] == "open_url"
    assert apps == []


def test_foco_sozinho_nao_e_confirmacao_de_maximizacao() -> None:
    resultado = executar_habilidade_janelas(
        "MAXIMIZE_WINDOW",
        {"nome_app": "Opera"},
        {
            "APPS_MAP": {"opera": "opera"},
            "_resolver_alvo_ambiente": lambda _nome: {
                "programa_aberto": True,
                "programa_em_foco": True,
            },
            "ativar_tela_cheia_robusta": lambda _nome: False,
        },
    )

    assert resultado["ok"] is False
    assert resultado["status"] == "maximizacao_nao_confirmada"
    assert resultado["foco_confirmado"] is True


def test_maximizacao_so_confirma_quando_a_janela_observa_o_estado() -> None:
    class Janela:
        title = "Opera"
        isMinimized = False
        isMaximized = False

        def activate(self) -> None:
            return None

        def maximize(self) -> None:
            self.isMaximized = True

    janela = Janela()

    class Gw:
        @staticmethod
        def getAllWindows():
            return [janela]

    assert maximizar_janela(Gw(), None, "Opera") is True
