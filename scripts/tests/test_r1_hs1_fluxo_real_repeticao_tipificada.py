"""R1-HS1 — RED high-stack da repetição tipada no fluxo real.

Objetivo
========
Atravessar duas fronteiras reais da Laylay sem executar efeitos físicos:

    estado canônico
        -> ComposicaoTurnoRuntime.iniciar()
        -> planejamento/retrato reais
        -> CicloComandosRuntime.resolver_comando_natural()
        -> resolver_intencao()
        -> arbitrar_turno()

Sequência causal
================

    IOT_CONTROL antigo
        -> FILE_READ(A)
        -> CREATE_FILE(B), não reexecutável
        -> "Leia de novo."

Contrato esperado
=================

A fala atual restringe a repetição semanticamente a LER. Portanto:

    planejamento_turno.repeticao_operacional == FILE_READ(A)
    decisão final do coordenador             == FILE_READ(A)

B pode ser o arquivo saliente atual, mas não pode substituir A.
O IoT antigo pode continuar reexecutável para "de novo" genérico, mas
não pode ganhar de "Leia de novo.".

Este teste NÃO executa FILE_READ, CREATE_FILE nem IOT_CONTROL.
Ele mede somente planejamento + resolução + arbitragem.
"""

from __future__ import annotations

import time
from typing import Any

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.cognicao.composicao_turno import ComposicaoTurnoRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
    texto_depende_de_contexto,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_contexto import (
    estrutura_arquivo_recente,
    registrar_estrutura_arquivo_recente,
)
from mente_laylay.memoria_mental.continuidade_semantica import (
    resolver_continuidade_semantica,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)


CAMINHO_A = r"C:\tmp\r1_hs1_a.txt"
CAMINHO_B = r"C:\tmp\r1_hs1_b.txt"
NOME_A = "r1_hs1_a.txt"
NOME_B = "r1_hs1_b.txt"


def _registrar_iot_antigo(estado: dict[str, Any]) -> dict[str, Any]:
    return registrar_resultado_execucao(
        estado,
        {
            "intent": "IOT_CONTROL",
            "params": {"acao": "desligar", "alvo": "lampada_quarto"},
            "alvo": "lampada_quarto",
            "status": "dispositivo_desligado",
            "executou": True,
            "confirmado": True,
            "origem": "iot",
        },
        "Desliga a lâmpada.",
        True,
        origem="iot",
        status="dispositivo_desligado",
    )


def _registrar_leitura_a(estado: dict[str, Any]) -> dict[str, Any]:
    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "FILE_READ",
            "params": {"caminho": CAMINHO_A, "alvo": NOME_A},
            "alvo": CAMINHO_A,
            "status": "arquivo_lido",
            "executou": True,
            "confirmado": True,
            "origem": "arquivos",
        },
        f"Leia o {NOME_A}.",
        True,
        origem="arquivos",
        status="arquivo_lido",
    )
    return registrar_estrutura_arquivo_recente(
        estado,
        {
            "tipo": "arquivo",
            "caminho": CAMINHO_A,
            "arquivo_nome": NOME_A,
            "nome_arquivo": NOME_A,
        },
    )


def _registrar_criacao_b(estado: dict[str, Any]) -> dict[str, Any]:
    estado = registrar_resultado_execucao(
        estado,
        {
            "intent": "CREATE_FILE",
            "params": {
                "caminho": CAMINHO_B,
                "alvo": NOME_B,
                "arquivo_nome": NOME_B,
            },
            "alvo": CAMINHO_B,
            "status": "arquivo_criado",
            "executou": True,
            "confirmado": True,
            "origem": "arquivos",
        },
        f"Crie o arquivo {NOME_B}.",
        True,
        origem="arquivos",
        status="arquivo_criado",
    )
    return registrar_estrutura_arquivo_recente(
        estado,
        {
            "tipo": "arquivo",
            "caminho": CAMINHO_B,
            "arquivo_nome": NOME_B,
            "nome_arquivo": NOME_B,
        },
    )


def _estado_causal() -> dict[str, Any]:
    estado = estado_mental_inicial()
    estado = _registrar_iot_antigo(estado)
    estado = _registrar_leitura_a(estado)
    estado = _registrar_criacao_b(estado)
    return estado


class _ModoJogoVazio:
    @staticmethod
    def contexto_atual() -> dict[str, Any]:
        return {}


class _SaudeVazia:
    @staticmethod
    def snapshot() -> dict[str, Any]:
        return {}


class _PesquisaVazia:
    @staticmethod
    def pesquisar_contexto_tema(_tema: str) -> dict[str, Any]:
        return {}

    @staticmethod
    def obter_contexto_cache(_tema: str) -> dict[str, Any]:
        return {}

    @staticmethod
    def precarregar_contexto_tema(_tema: str) -> None:
        return None


def _classificar_turno_real(texto: str, **_kwargs: Any) -> dict[str, Any]:
    return classificar_modalidade_turno(texto)


def _registro_semantico_neutro(
    registro: Any,
    _texto: str,
    **_kwargs: Any,
) -> dict[str, Any]:
    return dict(registro or {}) if isinstance(registro, dict) else {}


class _HarnessHS1:
    def __init__(self) -> None:
        self.logs: list[str] = []
        self.arbitragens: list[tuple[str, dict[str, Any]]] = []
        self.estado = EstadoCompartilhadoRuntime(
            mental=_estado_causal(),
            memoria_conversa={"messages": []},
        )

        def log(*args: Any, **_kwargs: Any) -> None:
            self.logs.append(" ".join(str(item) for item in args))

        def resolver_retry(texto: str) -> dict[str, Any] | None:
            return resolver_repeticao_ultima_acao(
                texto,
                dict(self.estado.mental),
                normalizar_texto_basico,
            )

        def resolver_semantico(texto: str) -> dict[str, Any] | None:
            estrutura = dict(
                estrutura_arquivo_recente(
                    dict(self.estado.mental),
                    ttl_s=900.0,
                )
                or {}
            )
            decisao = resolver_continuidade_semantica(
                texto,
                mente=dict(self.estado.mental),
                estrutura_arquivo=estrutura,
            )
            return decisao.para_intencao()

        self._resolver_retry = resolver_retry
        self._resolver_semantico = resolver_semantico

        servicos_turno = {
            "APPS_MAP": {},
            "_abrir_correcao_interpretacao_mente": lambda *_a, **_k: {},
            "_analisar_funcao_comunicativa_mente": (
                lambda *_a, **_k: {"funcao": "pedido"}
            ),
            "_analisar_identidade_turno_mente": lambda *_a, **_k: {},
            "_atualizar_assunto_estruturado_mente": lambda *_a, **_k: {},
            "_atualizar_plano_turno_mente": (
                lambda plano, **_k: dict(plano or {})
            ),
            "_atualizar_registro_turno_mente": _registro_semantico_neutro,
            "_classificar_encerramento_assunto_mente": lambda *_a, **_k: "",
            "_classificar_modalidade_turno_mente": _classificar_turno_real,
            "_construir_parecer_especialistas_mente": lambda *_a, **_k: {},
            "_construir_retrato_turno_mente": construir_retrato_turno,
            "_contexto_horario_atual": lambda: "dia",
            "_estado_compartilhado_runtime": self.estado,
            "_evidencia_habilidades_turno_mente": lambda *_a, **_k: {},
            "_extrair_correcao_duravel_mente": lambda *_a, **_k: {},
            "_extrair_tema_fundamentacao_mente": lambda *_a, **_k: "",
            "_interpretador_semantico_runtime": None,
            "_limpar_pergunta_aberta_estado_mente": (
                lambda estado: dict(estado or {})
            ),
            "_modo_jogo_runtime": _ModoJogoVazio(),
            "_montar_fundamentacao_mente": lambda *_a, **_k: {},
            "_normalizar_texto_com_apelidos": normalizar_texto_basico,
            "_obter_contexto_perceptivo": lambda: {},
            "_observabilidade_mente_runtime": None,
            "_orquestrador_cooperativo_runtime": None,
            "_pendencia_ativa_turno_mente": lambda *_a, **_k: None,
            "_persistir_correcao_duravel_mente": lambda *_a, **_k: False,
            "_pesquisa_contextual_runtime": _PesquisaVazia(),
            "_planejar_turno_mente": planejar_turno,
            "_registrar_etapa_turno_mente": (
                lambda trilha, *_a, **_k: list(trilha or [])
            ),
            "_resolver_repeticao_ultima_acao": resolver_retry,
            "_resumo_identidade_turno_mente": lambda *_a, **_k: "",
            "_saude_mente_runtime": _SaudeVazia(),
            "_texto_tem_comando_explicito": lambda *_a, **_k: False,
            "_verificar_fala_turno_mente": (
                lambda fala, **_k: {
                    "fala": fala,
                    "aceita": True,
                    "problemas": [],
                }
            ),
            "_registro_visao_jogo_leitura_runtime": None,
            "MEMORIA_SQLITE": None,
            "playlist_state": {},
            "print": log,
            "time": time,
        }

        self.turnos = ComposicaoTurnoRuntime(servicos=servicos_turno)
        harness = self

        class _ContextoIntencao:
            @staticmethod
            def montar() -> dict[str, Any]:
                mental = dict(harness.estado.mental)
                return {
                    "mente_integrada_estado": mental,
                    "turno_atual": dict(mental.get("turno_atual") or {}),
                    "retrato_turno_atual": dict(
                        mental.get("retrato_turno_atual") or {}
                    ),
                    "continuidade_geral": dict(
                        mental.get("continuidade_geral") or {}
                    ),
                    "ultima_intencao": mental.get("ultima_intencao", ""),
                    "ultima_habilidade": mental.get("ultima_habilidade", ""),
                    "_musica_estado_get": (
                        lambda _chave, default=None: default
                    ),
                    "_pendencia_acao_runtime": None,
                    "registrar_arbitragem_turno": (
                        lambda texto, resultado: harness.arbitragens.append(
                            (str(texto), dict(resultado or {}))
                        )
                    ),
                }

        def detector_arquivo(texto: str) -> dict[str, Any] | None:
            return detectar_intencao_arquivos(
                texto,
                params_cb=lambda **kwargs: kwargs,
                estado_mental=dict(self.estado.mental),
                normalizar_texto=normalizar_texto_basico,
            )

        servicos_ciclo = {
            "_normalizar_texto_com_apelidos": normalizar_texto_basico,
            "_texto_depende_de_contexto": (
                lambda texto: texto_depende_de_contexto(
                    texto,
                    normalizar_texto_basico,
                )
            ),
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "_refinar_contexto_mental": lambda *_a, **_k: None,
            "_texto_cancela_acao_agora": lambda _texto: False,
            "_resolver_comando_midia_contextual_forcado": lambda _texto: None,
            "_resolver_comando_contextual_forcado": resolver_semantico,
            "_resolver_comando_acao_geral_contextual_forcado": (
                lambda _texto: None
            ),
            "_resolver_repeticao_ultima_acao": resolver_retry,
            "detectar_intencao_deterministica": detector_arquivo,
            "_limpar_nome_playlist": lambda valor: str(valor or "").strip(),
            "_extrair_agendamento_local": lambda _texto: None,
            "_extrair_acao_agendada_local": lambda _texto: None,
            "_registrar_resultado_execucao": lambda *_a, **_k: None,
            "_registrar_autoaprimoramento": lambda *_a, **_k: None,
            "_detectar_repetir_briefing": lambda _texto: False,
            "repetir_briefing": lambda: False,
            "interpretar_comando_local_rapido": lambda _texto: None,
        }

        self.ciclo = CicloComandosRuntime(
            namespace_getter=lambda: servicos_ciclo,
            contexto_intencao_runtime=_ContextoIntencao(),
            log=log,
        )

    def iniciar_turno(self, texto: str = "Leia de novo.") -> dict[str, Any]:
        return self.turnos.iniciar(texto, origem="terminal")

    def resolver(self, texto: str = "Leia de novo."):
        return self.ciclo.resolver_comando_natural(
            texto,
            origem="r1-hs1",
        )


def test_guard_hs1_estado_causal_contem_iot_leitura_a_e_criacao_b() -> None:
    harness = _HarnessHS1()
    mental = dict(harness.estado.mental)
    continuidade = dict(mental.get("continuidade_geral") or {})
    historico = [
        dict(item)
        for item in list(continuidade.get("historico") or [])
        if isinstance(item, dict)
    ]
    intents = [
        str(item.get("intent") or "").strip().upper()
        for item in historico
    ]

    assert "IOT_CONTROL" in intents
    assert "FILE_READ" in intents
    assert "CREATE_FILE" in intents
    assert mental["ultima_acao_intent"] == "CREATE_FILE"

    estrutura = estrutura_arquivo_recente(mental, ttl_s=900.0)
    assert estrutura
    assert estrutura["caminho"] == CAMINHO_B


def test_guard_hs1_detector_de_arquivo_nao_inventa_b_para_leia_de_novo() -> None:
    harness = _HarnessHS1()
    resultado = detectar_intencao_arquivos(
        "Leia de novo.",
        params_cb=lambda **kwargs: kwargs,
        estado_mental=dict(harness.estado.mental),
        normalizar_texto=normalizar_texto_basico,
    )
    assert resultado is None


def test_guard_hs1_continuidade_semantica_continua_cedendo() -> None:
    harness = _HarnessHS1()
    candidato = harness._resolver_semantico("Leia de novo.")
    assert candidato is None


def test_red_hs1_planejamento_real_preserva_file_read_a() -> None:
    harness = _HarnessHS1()
    turno = harness.iniciar_turno("Leia de novo.")
    repeticao = dict(turno.get("repeticao_operacional") or {})

    assert repeticao, (
        "O planejamento real perdeu completamente a repetição. "
        f"turno={turno!r} logs={harness.logs!r}"
    )
    assert repeticao.get("intent") == "FILE_READ", (
        "Primeira fronteira RED: o próprio planejamento do turno "
        "materializou uma operação incompatível com LER. "
        f"repeticao_operacional={repeticao!r} "
        f"modalidade={turno.get('modalidade_geral')!r}"
    )

    params = dict(repeticao.get("params") or {})
    assert params.get("caminho") == CAMINHO_A
    assert params.get("caminho") != CAMINHO_B


def test_red_hs1_coordenador_real_termina_em_file_read_a() -> None:
    harness = _HarnessHS1()
    harness.iniciar_turno("Leia de novo.")
    decisao, rota = harness.resolver("Leia de novo.")

    assert isinstance(decisao, dict), (
        "O coordenador não materializou nenhuma intenção. "
        f"rota={rota!r} arbitragens={harness.arbitragens!r} "
        f"logs={harness.logs!r}"
    )
    assert decisao.get("intent") == "FILE_READ", (
        "A decisão final do coordenador atravessou a semântica LER. "
        f"decisao={decisao!r} rota={rota!r} "
        f"arbitragens={harness.arbitragens!r}"
    )

    params = dict(decisao.get("params") or {})
    assert params.get("caminho") == CAMINHO_A
    assert params.get("caminho") != CAMINHO_B


def test_guard_hs1_nao_executa_efeitos_fisicos() -> None:
    harness = _HarnessHS1()
    harness.iniciar_turno("Leia de novo.")
    harness.resolver("Leia de novo.")

    diagnostico = harness.ciclo.diagnostico_linguagem_natural()
    execucao = dict(diagnostico.get("execucao_turno") or {})
    assert int(execucao.get("iniciadas") or 0) == 0
