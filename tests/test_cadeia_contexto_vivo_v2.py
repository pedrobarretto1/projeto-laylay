from __future__ import annotations

import time

from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    _executar_listar_abas,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_consulta_abas
from mente_laylay.memoria_mental.contexto_imediato import (
    _dominio_restrito_referencia,
)


def _estado_confirmado(intent: str, dominio: str) -> dict:
    return {
        "ultima_acao_contrato": {
            "intent": intent,
            "dominio": dominio,
            "executou": True,
            "confirmado": True,
        },
        "ultima_acao_ts": time.time(),
    }


def test_ordinal_herda_dominio_da_ultima_acao_confirmada() -> None:
    assert _dominio_restrito_referencia(
        "abre o primeiro resultado",
        _estado_confirmado("SEARCH", "site"),
    ) == "site"

    assert _dominio_restrito_referencia(
        "abre o primeiro resultado",
        _estado_confirmado("FILE_SEARCH", "arquivo"),
    ) == "arquivo"


def test_consulta_singular_da_aba_ativa_reusa_list_tabs() -> None:
    resultado = detectar_consulta_abas(
        "me diz qual aba está aberta",
        params_cb=lambda **kwargs: kwargs,
    )
    assert resultado == {
        "intent": "LIST_TABS",
        "params": {"somente_ativa": True},
    }


def test_executor_lista_somente_a_aba_ativa_quando_solicitado() -> None:
    falas = []
    resultados = []

    class Navegador:
        def conectado(self):
            return True

        def aba_ativa(self, timeout_s=4.0):
            return {
                "tabId": 77,
                "windowId": 3,
                "active": True,
                "title": "Documentação Python",
                "url": "https://docs.python.org/3/",
            }

        def listar_abas(self, timeout_s=5.0):
            raise AssertionError(
                "consulta somente_ativa não deve listar todas as abas"
            )

    deps = DependenciasExecutorNavegador(
        marcar_resultado=lambda *args, **kwargs: resultados.append(
            (args, kwargs)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        abrir_url_com_validacao=lambda *_args, **_kwargs: False,
        alvo_preciso_para_aba=lambda valor: valor,
        esperar_aba_fechar=lambda *_args, **_kwargs: False,
        esperar_programa_fechar=lambda *_args, **_kwargs: False,
        executar_recursivo=lambda *_args, **_kwargs: False,
    )

    retorno = _executar_listar_abas(
        {
            "_registro_navegador_leitura_runtime": Navegador(),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        deps,
        params={"somente_ativa": True},
    )

    assert retorno.tratado is True
    assert resultados
    assert resultados[-1][0][0] == "aba_ativa_consultada"
    assert resultados[-1][1]["confirmado"] is True
    assert "Documentação Python" in falas[-1]


def test_cadeia_isola_especialista_e_retrato_da_frase_composta() -> None:
    executadas = []
    falas = []

    class Contexto:
        @staticmethod
        def montar():
            return {
                "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
                "turno_atual": {
                    "id": "turno-145",
                    "texto": (
                        "Volta para a aba anterior e depois "
                        "me diz qual aba está aberta."
                    ),
                    "modalidade": "conversa",
                    "modalidade_geral": "conversa",
                    "autoriza_execucao": False,
                    "especialistas": {
                        "operacional": {
                            "ativo": False,
                            "autoriza_execucao": False,
                            "requer_esclarecimento": False,
                            "confianca": 1.0,
                        }
                    },
                },
                "retrato_turno_atual": {
                    "id": "retrato-congelado",
                    "referencia_tipo": "arquivo",
                    "referencia_resolvida": {
                        "tipo": "arquivo",
                        "nome": "velho.txt",
                    },
                    "intents_permitidos": ["FILE_OPEN_RESULT"],
                    "operacao_explicita": "arquivo",
                },
                "continuidade_geral": {},
            }

    def detectar(texto: str):
        base = str(texto or "").casefold().strip(" .!?")
        if base == "volta para a aba anterior":
            return {"intent": "SWITCH_PREVIOUS_TAB", "params": {}}
        if base == "me diz qual aba está aberta":
            return {
                "intent": "LIST_TABS",
                "params": {"somente_ativa": True},
            }
        return None

    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
            "_texto_depende_de_contexto": lambda texto: "anterior" in str(texto).casefold(),
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "detectar_intencao_deterministica": detectar,
            "_resolver_comando_contextual_forcado": lambda _texto: None,
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )
    runtime.executar_intencao = (
        lambda resultado, _texto: executadas.append(resultado["intent"]) or True
    )

    assert runtime.processar_cadeia(
        "Volta para a aba anterior e depois me diz qual aba está aberta.",
        "regressao-145",
    ) is True
    assert executadas == ["SWITCH_PREVIOUS_TAB", "LIST_TABS"]
    assert falas == []


def test_falha_na_primeira_etapa_da_cadeia_sempre_pode_falar() -> None:
    falas = []

    class Contexto:
        @staticmethod
        def montar():
            return {
                "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
                "turno_atual": {
                    "id": "turno-falha",
                    "modalidade": "comando",
                    "modalidade_geral": "comando",
                    "autoriza_execucao": True,
                },
                "retrato_turno_atual": {},
                "continuidade_geral": {},
            }

    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
            "_texto_depende_de_contexto": lambda _texto: False,
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: None,
            "_resolver_comando_contextual_forcado": lambda _texto: None,
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )

    assert runtime.processar_cadeia(
        "abre a Calculadora e depois fecha ela",
        "regressao-fala",
    ) is True
    assert falas
    assert "etapa 1" in falas[-1].casefold()
