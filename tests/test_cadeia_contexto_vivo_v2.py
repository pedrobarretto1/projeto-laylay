from __future__ import annotations

import time

from mente_laylay.autonomia.coordenador_intencao import (
    CicloComandosRuntime,
    resolver_intencao,
)
from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    _executar_listar_abas,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_consulta_abas
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.contexto_imediato import (
    ContextoImediatoRuntime,
    _dominio_restrito_referencia,
    referencia_contextual_imediata,
    resolver_comando_acao_geral_contextual,
    resolver_comando_contextual,
)
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    texto_depende_de_contexto,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.cognicao.referencias_linguagem import (
    texto_tem_referencia_contextual,
    valor_e_referencia_contextual,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
    registrar_resultado_execucao,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
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
    resultados_publicados = []
    falas = []

    class Contexto:
        @staticmethod
        def montar():
            texto_turno = (
                "Volta para a aba anterior e depois "
                "me diz qual aba está aberta."
            )
            return {
                "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
                "turno_atual": classificar_modalidade_turno(texto_turno),
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
            "_registrar_resultado_execucao": (
                lambda resultado, texto, executou, **kwargs: resultados_publicados.append(
                    (resultado["intent"], texto, executou, kwargs.get("origem"))
                )
            ),
            "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )
    runtime.executar_intencao = (
        lambda resultado, _texto: executadas.append(resultado["intent"]) or True
    )

    fala_completa = (
        "Volta para a aba anterior e depois me diz qual aba está aberta."
    )
    assert runtime.processar_cadeia(
        fala_completa,
        "regressao-145",
    ) is True
    assert executadas == ["SWITCH_PREVIOUS_TAB", "LIST_TABS"]
    assert [item[1] for item in resultados_publicados] == [
        fala_completa,
        fala_completa,
    ]
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


def test_etapa_eliptica_tipificada_consulta_owner_geral_da_playlist() -> None:
    """RED do caos: o owner existe, mas o coordenador não o consultava."""
    chamadas_geral = []
    resultado, rota = resolver_intencao(
        "me mostra o que tem nela",
        "turno-148-etapa-2",
        {
            "normalizar_texto": lambda texto: str(texto).casefold().strip(),
            "refinar_contexto_mental": lambda _texto: None,
            "turno_atual": {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
            },
            "retrato_turno_atual": {
                "referencia_tipo": "playlist",
                "referencia_resolvida": {
                    "tipo": "playlist",
                    "nome": "caos sonora",
                    "origem": "continuidade_operacional_viva_cadeia",
                },
            },
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: None,
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_comando_acao_geral_contextual_forcado": (
                lambda texto: chamadas_geral.append(texto) or {
                    "intent": "PLAYLIST_LIST",
                    "params": {
                        "nome_playlist": "caos sonora",
                        "referencia_contextual": True,
                    },
                }
            ),
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "tentar_intencao_ai_primeiro": lambda _texto: None,
            "texto_parece_consulta_operacional": lambda _texto: True,
            "continuidade_geral": {},
        },
    )

    assert chamadas_geral == ["me mostra o que tem nela"]
    assert resultado == {
        "intent": "PLAYLIST_LIST",
        "params": {
            "nome_playlist": "caos sonora",
            "referencia_contextual": True,
        },
    }
    assert rota == "contexto-geral"


def test_contracao_pronominal_nela_e_referencia_contextual_real() -> None:
    """RED do caos: ``nela`` precisa atravessar o contrato linguistico real."""
    assert texto_tem_referencia_contextual("me mostra o que tem nela") is True
    assert valor_e_referencia_contextual("nela") is True
    assert texto_depende_de_contexto(
        "me mostra o que tem nela",
        normalizar_texto_cb=normalizar_texto,
    ) is True
    # A contração deve ser uma palavra inteira; ``janela`` não é pronome.
    assert texto_tem_referencia_contextual("abre a janela") is False


def test_consulta_nela_restringe_owner_antes_da_arbitragem_contextual() -> None:
    """RED real: sem restrição, um especialista anterior sombreia a playlist."""
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "PLAYLIST_ADD",
            "alvo": "caos sonora",
            "status": "playlist_musica_adicionada",
            "executou": True,
            "confirmado": True,
            "params": {"nome_playlist": "caos sonora"},
        },
        "Adiciona essa música na playlist caos sonora",
        True,
        origem="executor",
    )
    trecho = "me mostra o que tem nela"
    dominio = _dominio_restrito_referencia(trecho, estado)
    referencia = referencia_contextual_imediata(
        mente_integrada_estado=estado,
        foco_vivo={},
        texto_atual=trecho,
        normalizar_texto=normalizar_texto,
    )

    resultado = resolver_comando_contextual(
        trecho,
        [
            (
                "IOT",
                lambda _texto: {
                    "intent": "IOT_STATUS",
                    "params": {"alvo": "lampada_antiga"},
                },
            ),
            (
                "GERAL",
                lambda texto: resolver_comando_acao_geral_contextual(
                    texto,
                    referencia,
                ),
            ),
        ],
        dominio_restrito=dominio,
    )

    assert dominio == "musica"
    assert _dominio_restrito_referencia("o que tem nela?", estado) == "musica"
    assert referencia["tipo"] == "playlist"
    assert referencia["alvo"] == "caos sonora"
    assert resultado is not None
    assert resultado["intent"] == "PLAYLIST_LIST"
    assert resultado["params"]["nome_playlist"] == "caos sonora"


def test_runtime_geral_recebe_dominio_restrito_apos_fala_de_confirmacao() -> None:
    """RED de produção: a fala pode ser foco, mas não sombrear o owner musical."""
    estado = registrar_resultado_execucao(
        estado_mental_inicial(),
        {
            "intent": "PLAYLIST_ADD",
            "alvo": "caos sonora",
            "status": "playlist_musica_adicionada",
            "executou": True,
            "confirmado": True,
            "params": {"nome_playlist": "caos sonora"},
        },
        "Adiciona essa música na playlist caos sonora",
        True,
        origem="executor",
    )
    estado = registrar_evento_continuidade(
        estado,
        evento="fala",
        dominio="conversa",
        tipo="conversa",
        topico="confirmacao",
        texto="Adiciona essa música na playlist caos sonora",
        resposta="Concluí o pedido em caos sonora e confirmei o resultado.",
        origem="fala_final",
    )
    estado_runtime = EstadoCompartilhadoRuntime(
        mental=estado,
        musical={"ultima_playlist": "caos sonora"},
    )
    runtime = ContextoImediatoRuntime(
        estado_runtime_getter=lambda: estado_runtime,
        servicos_iniciais={
            "_normalizar_texto_com_apelidos": normalizar_texto,
            "_alvo_corrigido_atual": lambda: "",
            "_registrar_alvo_corrigido": lambda _alvo: None,
            "_contexto_musical_ativo": lambda: True,
            "_estrutura_arquivo_recente": lambda _ttl: {},
            "_foco_vivo_atual": lambda **_kwargs: {},
        },
    )

    assert estado["continuidade_geral"]["dominio_ativo"] == "conversa"
    assert _dominio_restrito_referencia(
        "me mostra o que tem nela",
        estado,
    ) == "musica"
    assert runtime.resolver("me mostra o que tem nela") == {
        "intent": "PLAYLIST_LIST",
        "params": {
            "nome_playlist": "caos sonora",
            "referencia_contextual": True,
        },
        "_rota_contextual": "GERAL",
        "_dominio_contextual": "musica",
    }


def test_owner_geral_nao_e_consultado_sem_referencia_tipificada() -> None:
    chamadas_geral = []
    resultado, _rota = resolver_intencao(
        "me mostra o que tem nela",
        "sem-referencia-tipificada",
        {
            "normalizar_texto": lambda texto: str(texto).casefold().strip(),
            "refinar_contexto_mental": lambda _texto: None,
            "turno_atual": {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
            },
            "retrato_turno_atual": {},
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: None,
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_comando_acao_geral_contextual_forcado": (
                lambda _texto: chamadas_geral.append(True) or {
                    "intent": "PLAYLIST_LIST",
                    "params": {"nome_playlist": "antiga"},
                }
            ),
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "tentar_intencao_ai_primeiro": lambda _texto: None,
            "texto_parece_consulta_operacional": lambda _texto: True,
            "continuidade_geral": {},
        },
    )

    assert chamadas_geral == []
    assert resultado is None


def test_cadeia_real_adiciona_e_consulta_a_mesma_playlist() -> None:
    fala = (
        "Adiciona essa música na playlist caos sonora e depois me mostra "
        "o que tem nela."
    )
    estado = estado_mental_inicial()
    executadas = []
    falas = []

    class Contexto:
        @staticmethod
        def montar():
            return {
                "mente_integrada_estado": estado,
                "turno_atual": classificar_modalidade_turno(fala),
                "retrato_turno_atual": {},
                "continuidade_geral": dict(
                    estado.get("continuidade_geral") or {}
                ),
                "falar_com_lipsync": lambda texto, *_args: falas.append(texto),
            }

    def detectar(trecho: str):
        if str(trecho).casefold().startswith("adiciona essa música"):
            return {
                "intent": "PLAYLIST_ADD",
                "params": {"nome_playlist": "caos sonora"},
            }
        return None

    def resolver_owner_geral(trecho: str):
        if (
            estado.get("ultima_playlist") == "caos sonora"
            and "o que tem nela" in str(trecho).casefold()
        ):
            return {
                "intent": "PLAYLIST_LIST",
                "params": {
                    "nome_playlist": "caos sonora",
                    "referencia_contextual": True,
                },
            }
        return None

    runtime = CicloComandosRuntime(
        namespace_getter=lambda: {
            "_normalizar_texto_com_apelidos": (
                lambda texto: str(texto).casefold().strip()
            ),
            "_texto_depende_de_contexto": lambda texto: texto_depende_de_contexto(
                texto,
                normalizar_texto_cb=normalizar_texto,
            ),
            "_texto_parece_consulta_operacional": lambda _texto: True,
            "detectar_intencao_deterministica": detectar,
            "_resolver_comando_contextual_forcado": lambda _texto: None,
            "_resolver_comando_acao_geral_contextual_forcado": (
                resolver_owner_geral
            ),
            "_resolver_repeticao_ultima_acao": lambda _texto: None,
            "musica_estado_get": lambda chave, default="": (
                estado.get(chave, default)
            ),
            "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
            "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        },
        contexto_intencao_runtime=Contexto(),
        log=lambda *_args: None,
    )

    def executar(comando, _texto):
        executadas.append(dict(comando))
        if comando["intent"] == "PLAYLIST_ADD":
            atualizado = registrar_evento_continuidade(
                estado,
                evento="acao",
                dominio="musica",
                intent="PLAYLIST_ADD",
                habilidade="playlist",
                tipo="playlist",
                alvo="caos sonora",
                params={"nome_playlist": "caos sonora"},
                status="playlist_musica_adicionada",
            )
            estado.clear()
            estado.update(atualizado)
            estado.update({
                "ultima_playlist": "caos sonora",
                "ultima_acao_intent": "PLAYLIST_ADD",
                "ultima_intencao": "PLAYLIST_ADD",
                "ultima_habilidade": "playlist",
                "ultima_acao_params": {"nome_playlist": "caos sonora"},
                "ultima_acao_status": "playlist_musica_adicionada",
                "ultima_acao_executou": True,
                "ultima_acao_confirmado": True,
                "ts": time.time(),
            })
        return True

    runtime.executar_intencao = executar

    assert runtime.processar_cadeia(fala, "turno-148") is True
    assert [item["intent"] for item in executadas] == [
        "PLAYLIST_ADD",
        "PLAYLIST_LIST",
    ]
    assert falas == []
