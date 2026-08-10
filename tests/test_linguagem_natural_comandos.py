from __future__ import annotations

from mente_laylay.autonomia.analise_comandos import segmentar_comandos_em_cadeia
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.coordenador_intencao import CicloComandosRuntime
from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
from mente_laylay.cognicao.interpretacao_intencao import (
    InterpretacaoIntencaoRuntime,
)
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.integracao.registro_conversa_llm import (
    RegistroModeloLLM,
    ResultadoModelo,
)
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade,
)


class _ContextoExecucao:
    def __init__(self, *, turno: dict, retrato: dict | None = None) -> None:
        self._turno = turno
        self._retrato = retrato or {}

    def montar(self) -> dict:
        return {
            "turno_atual": dict(self._turno),
            "retrato_turno_atual": dict(self._retrato),
            "registrar_arbitragem_turno": lambda *_args: None,
        }


def test_cadeia_natural_separa_duas_ordens_sem_cortar_conversa() -> None:
    assert segmentar_comandos_em_cadeia(
        "cria uma pasta chamada teste e coloca um arquivo dentro dela"
    ) == [
        "cria uma pasta chamada teste",
        "coloca um arquivo dentro dela",
    ]
    assert segmentar_comandos_em_cadeia(
        "encontra o código da lâmpada e abre o primeiro resultado"
    ) == [
        "encontra o código da lâmpada",
        "abre o primeiro resultado",
    ]
    assert segmentar_comandos_em_cadeia(
        "você prefere rock e metal?"
    ) == ["você prefere rock e metal"]


def test_cadeia_preserva_extensao_e_pontuacao_dos_argumentos() -> None:
    assert segmentar_comandos_em_cadeia(
        "Cria uma pasta chamada teste composto e coloca um arquivo chamado resultado.md dentro dela.",
        normalizar_texto=lambda texto: str(texto).casefold().replace(".", " "),
    ) == [
        "Cria uma pasta chamada teste composto",
        "coloca um arquivo chamado resultado.md dentro dela.",
    ]


def test_barreira_prioritaria_entrega_cadeia_ao_ciclo_canonico() -> None:
    chamadas: list[tuple[str, str]] = []
    estado = type("Estado", (), {"mental": {}})()
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "processar_comandos_em_cadeia": lambda texto, origem: (
            chamadas.append((texto, origem)) or True
        ),
        "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
            AssertionError("a cadeia tratada não deve cair na conversa")
        ),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    texto = "abre o Opera e depois maximiza a janela"
    assert runtime.processar_prioritarios(texto) is True
    assert chamadas == [(texto, "prioritario-cooperativo")]


def test_composto_caixa_agenda_exige_as_duas_etapas_confirmadas() -> None:
    chamadas: list[tuple[str, str]] = []
    comandos_executados: list[dict] = []

    class Caixa:
        def processar(self, texto: str) -> bool:
            chamadas.append(("caixa", texto))
            return True

        @staticmethod
        def ultimo_item_salvo() -> dict:
            return {
                "id": "nota-espacial",
                "titulo": "Aparência espacial para o avatar",
                "conteudo": "Criar uma aparência espacial para o avatar",
            }

    estado = type("Estado", (), {"mental": {}})()
    comando_agenda = {
        "intent": "AGENDAR_LEMBRETE",
        "params": {"descricao": "essa ideia", "dia": "amanhã", "hora": "11:00"},
    }
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_caixa_entrada_pessoal_runtime": Caixa(),
        "processar_comandos_em_cadeia": lambda *_args: (_ for _ in ()).throw(
            AssertionError("a cadeia especial não deve cair no executor genérico")
        ),
        "resolver_comando_natural": lambda texto, origem: (
            chamadas.append((origem, texto)) or (comando_agenda, "agenda")
        ),
        "executar_intencao": lambda comando, texto: (
            comandos_executados.append(comando)
            or chamadas.append((str(comando["intent"]), texto))
            or True
        ),
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    texto = (
        "Guarda essa ideia junto com suas sugestões e me lembra dela "
        "amanhã às 11 horas"
    )
    assert runtime.processar_prioritarios(texto) is True
    assert chamadas == [
        ("caixa", "Guarda essa ideia junto com suas sugestões"),
        (
            "prioritario-cooperativo-caixa-agenda",
            "me lembra dela amanhã às 11 horas",
        ),
        ("AGENDAR_LEMBRETE", "me lembra dela amanhã às 11 horas"),
    ]
    assert comandos_executados[0]["params"]["descricao"] == (
        "Aparência espacial para o avatar"
    )
    assert comandos_executados[0]["params"]["referencia_nota"] == "nota-espacial"


class _InterpretadorNatural:
    def __init__(self, resultado: dict | None) -> None:
        self.resultado = resultado
        self.chamadas: list[str] = []

    def tentar_ai_primeiro(self, texto: str):
        self.chamadas.append(texto)
        return self.resultado


def _ciclo(
    resultado_ia: dict | None,
    *,
    turno: dict | None = None,
    retrato: dict | None = None,
) -> tuple[CicloComandosRuntime, _InterpretadorNatural]:
    interpretador = _InterpretadorNatural(resultado_ia)
    servicos = {
        "_interpretacao_intencao_runtime": interpretador,
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_depende_de_contexto": lambda _texto: False,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_cancela_acao_agora": lambda _texto: False,
        "_resolver_comando_midia_contextual_forcado": lambda _texto: None,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_resolver_comando_acao_geral_contextual_forcado": lambda _texto: None,
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "detectar_intencao_deterministica": lambda _texto: None,
        "_extrair_agendamento_local": lambda _texto: None,
        "_extrair_acao_agendada_local": lambda _texto: None,
        "_texto_parece_consulta_operacional": lambda _texto: False,
    }
    runtime = CicloComandosRuntime(
        namespace_getter=lambda: servicos,
        contexto_intencao_runtime=_ContextoExecucao(
            turno=turno or {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
            },
            retrato=retrato,
        ),
        log=lambda *_args: None,
    )
    return runtime, interpretador


def test_resolvedor_canonico_aceita_linguagem_natural_em_dominios_distintos() -> None:
    casos = (
        (
            "seria possível trazer o Opera para a minha frente agora",
            {"intent": "APP_OPEN", "params": {"nome_app": "opera"}},
        ),
        (
            "quero deixar o ventilador funcionando por aqui",
            {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "ventilador"}},
        ),
        (
            "guarda este pensamento na minha caixa pessoal",
            {"intent": "INBOX_ADD", "params": {"conteudo": "este pensamento"}},
        ),
        (
            "procura nos meus arquivos onde está o controlador da luz",
            {"intent": "FILE_SEARCH", "params": {"query": "controlador da luz"}},
        ),
        (
            "eu queria ouvir algo do C418 enquanto construo",
            {"intent": "MUSIC_SEARCH", "params": {"query": "C418"}},
        ),
    )

    for texto, esperado in casos:
        ciclo, interpretador = _ciclo(esperado)
        resultado, rota = ciclo.resolver_comando_natural(texto, "teste")

        assert resultado == esperado, texto
        assert rota == "ia-first-arbitrada", texto
        assert interpretador.chamadas == [texto], texto


def test_resolvedor_natural_respeita_pergunta_hipotetica_sem_executar() -> None:
    ciclo, _ = _ciclo(
        {"intent": "DELETE_ITEM", "params": {"alvo": "projeto"}},
        turno={
            "modalidade": "pergunta",
            "modalidade_geral": "pergunta",
            "autoriza_execucao": False,
        },
    )

    resultado, rota = ciclo.resolver_comando_natural(
        "se eu pedir para apagar a pasta projeto, você consegue?",
        "teste-seguranca",
    )

    assert resultado is None
    assert rota == ""


def test_detector_literal_tambem_obedece_autorizacao_geral_do_turno() -> None:
    resultado, rota = resolver_intencao(
        "se eu pedir para fechar o Chrome, você consegue?",
        "teste-seguranca",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: False,
            "detectar_intencao_deterministica": lambda _texto: {
                "intent": "CLOSE_APP", "params": {"nome_app": "chrome"},
            },
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "tentar_intencao_ai_primeiro": lambda _texto: None,
            "registrar_arbitragem_turno": lambda *_args: None,
            "turno_atual": {
                "modalidade": "pergunta",
                "modalidade_geral": "pergunta",
                "autoriza_execucao": False,
            },
            "retrato_turno_atual": {},
        },
    )

    assert resultado is None
    assert rota == ""


def test_coordenador_recupera_essa_tambem_da_continuidade_oficial() -> None:
    estado = registrar_evento_continuidade(
        estado_mental_inicial(),
        evento="acao",
        intent="PLAYLIST_ADD",
        alvo="rei do pop",
        params={"nome_playlist": "rei do pop"},
        status="playlist_musica_adicionada",
    )

    resultado, rota = resolver_intencao(
        "essa também",
        "teste-continuacao",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            # Simula justamente a falha observada: o especialista não devolve
            # candidato, mas a fonte canônica continua válida.
            "detectar_intencao_deterministica": lambda _texto: None,
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
                AssertionError("a continuação não deveria chegar à IA")
            ),
            "registrar_arbitragem_turno": lambda *_args: None,
            "continuidade_geral": estado["continuidade_geral"],
            "turno_atual": {
                "modalidade": "comando",
                "modalidade_geral": "comando",
                "autoriza_execucao": True,
            },
            "retrato_turno_atual": {},
        },
    )

    assert resultado == {
        "intent": "PLAYLIST_ADD",
        "params": {
            "nome_playlist": "rei do pop",
            "referencia_contextual": True,
        },
    }
    assert rota == "continuidade-aditiva"


def test_coordenador_preserva_playlist_add_quando_detector_principal_falha() -> None:
    resultado, rota = resolver_intencao(
        "coloca essa musica na playlist rei do pop",
        "chat",
        {
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "refinar_contexto_mental": lambda _texto: None,
            "extrair_agendamento": lambda _texto: None,
            "extrair_acao_agendada": lambda _texto: None,
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_depende_de_contexto": lambda _texto: True,
            "detectar_intencao_deterministica": lambda _texto: None,
            "resolver_comando_contextual_forcado": lambda _texto: None,
            "resolver_repeticao_ultima_acao": lambda _texto: None,
            "tentar_intencao_ai_primeiro": lambda _texto: (_ for _ in ()).throw(
                AssertionError("pedido explícito de playlist não pode chegar à LLM")
            ),
            "turno_atual": {"modalidade": "comando", "autoriza_execucao": True},
            "retrato_turno_atual": {
                "operacao_explicita": "playlist_adicionar",
                "intents_permitidos": ["PLAYLIST_ADD"],
            },
            "registrar_arbitragem_turno": lambda *_args: None,
        },
    )

    assert resultado == {
        "intent": "PLAYLIST_ADD",
        "params": {"nome_playlist": "rei do pop"},
    }
    assert rota == "deterministico-explicito"


def test_barreira_prioritaria_executa_resolucao_canonica_uma_vez() -> None:
    resolucoes: list[tuple[str, str]] = []
    execucoes: list[tuple[dict, str]] = []
    registros: list[tuple] = []
    estado = type("Estado", (), {"mental": {}})()
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "resolver_comando_natural": lambda texto, origem: (
            resolucoes.append((texto, origem))
            or ({"intent": "APP_OPEN", "params": {"nome_app": "opera"}}, "ia-first-arbitrada")
        ),
        "executar_intencao": lambda intent, texto: execucoes.append((intent, texto)) or True,
        "_registrar_resultado_execucao": lambda *args, **kwargs: registros.append((args, kwargs)),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    texto = "seria possível trazer o Opera para a minha frente agora"
    assert runtime.processar_prioritarios(texto) is True
    assert resolucoes == [(texto, "prioritario-linguagem-natural")]
    assert execucoes == [
        ({"intent": "APP_OPEN", "params": {"nome_app": "opera"}}, texto),
    ]
    assert len(registros) == 1


def test_barreira_prioritaria_entrega_busca_de_codigo_ao_executor_local() -> None:
    execucoes: list[tuple[dict, str]] = []
    registros: list[tuple] = []
    estado = type("Estado", (), {"mental": {}})()
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_normalizar_texto_com_apelidos": lambda valor: str(valor).casefold(),
        "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
            AssertionError("a busca explícita não deve depender da LLM")
        ),
        "executar_intencao": lambda intent, texto: execucoes.append((intent, texto)) or True,
        "_registrar_resultado_execucao": lambda *args, **kwargs: registros.append((args, kwargs)),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    texto = "Encontra o código que controla a lâmpada."
    assert runtime.processar_prioritarios(texto) is True
    assert execucoes == [(
        {
            "intent": "FILE_SEARCH",
            "params": {
                "query": "código que controla a lâmpada",
                "somente_projeto": False,
            },
        },
        texto,
    )]
    assert len(registros) == 1
    assert registros[0][1]["origem"] == "prioritario_busca_arquivos"


def test_barreira_prioritaria_abre_resultado_por_ordinal_curto() -> None:
    caminho = r"C:\projeto\controlador.py"
    estado = type("Estado", (), {
        "mental": {
            "ultima_estrutura_arquivo_params": {
                "tipo": "pesquisa_semantica",
                "consulta": "código que controla a lâmpada",
                "resultados": [caminho],
                "nomes": ["controlador.py"],
            },
        },
    })()
    execucoes: list[tuple[dict, str]] = []
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_normalizar_texto_com_apelidos": lambda valor: str(valor).casefold(),
        "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
            AssertionError("a seleção ordinal deve usar a continuidade de arquivos")
        ),
        "executar_intencao": lambda intent, texto: execucoes.append((intent, texto)) or True,
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("o primeiro") is True
    assert execucoes == [(
        {
            "intent": "FILE_OPEN_RESULT",
            "params": {"caminho": caminho, "alvo": "controlador.py", "indice": 1},
        },
        "o primeiro",
    )]


def test_barreira_prioritaria_restaura_ultimo_item_sem_cair_na_llm() -> None:
    estado = type("Estado", (), {"mental": {}})()
    execucoes: list[tuple[dict, str]] = []
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "_normalizar_texto_com_apelidos": lambda valor: str(valor).casefold(),
        "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
            AssertionError("a restauração contextual não deve cair na conversa")
        ),
        "executar_intencao": lambda intent, texto: execucoes.append((intent, texto)) or True,
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("quero ele de volta") is True
    assert execucoes == [(
        {"intent": "RESTORE_DELETED_ITEM", "params": {}},
        "quero ele de volta",
    )]


def test_comando_reconhecido_com_falha_nao_cai_na_conversa_generica() -> None:
    estado = type("Estado", (), {"mental": {}})()
    namespace = {
        "_estado_compartilhado_runtime": estado,
        "resolver_comando_natural": lambda *_args: (
            {"intent": "IOT_CONTROL", "params": {"acao": "ligar", "alvo": "ventilador"}},
            "ia-first-arbitrada",
        ),
        "executar_intencao": lambda *_args: False,
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "quero deixar o ventilador funcionando por aqui"
    ) is True


def test_prompt_do_interpretador_recebe_catalogo_vivo_de_habilidades() -> None:
    chamadas: list[list[dict]] = []
    runtime = InterpretacaoIntencaoRuntime(
        contexto_getter=lambda: {
            "estado": {},
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_bloqueia_playlist_agora": lambda _texto: False,
            "texto_social_curto": lambda _texto: False,
            "texto_parece_consulta_operacional": lambda _texto: False,
            "enviar_mensagem": lambda mensagens, **_kwargs: (
                chamadas.append(mensagens) or '{"intent":"NONE","params":{}}'
            ),
            "extrair_json_da_ia": lambda texto: texto,
        },
        log=lambda *_args: None,
    )

    runtime.analisar("cuida desse conteúdo do jeito certo")
    prompt = chamadas[0][0]["content"]

    assert "Catálogo executável canônico" in prompt
    for intent in ("FILE_SEARCH", "INBOX_LIST", "IOT_LIST", "PEOPLE_QUERY"):
        assert intent in intents_registradas()
        assert intent in prompt


def test_interpretador_aceita_modelo_tipado_sem_callback_no_contexto() -> None:
    pedidos = []

    class Modelo:
        def executar(self, pedido):
            pedidos.append(pedido)
            return ResultadoModelo('{"intent":"NONE","params":{}}', True)

        def diagnostico(self):
            return {"disponivel": True}

    runtime = InterpretacaoIntencaoRuntime(
        contexto_getter=lambda: {
            "estado": {},
            "normalizar_texto": lambda texto: str(texto).casefold(),
            "texto_cancela_acao_agora": lambda _texto: False,
            "texto_bloqueia_playlist_agora": lambda _texto: False,
            "texto_social_curto": lambda _texto: False,
            "texto_parece_consulta_operacional": lambda _texto: False,
            "extrair_json_da_ia": lambda texto: texto,
        },
        modelo_llm=RegistroModeloLLM.criar(Modelo()),
        log=lambda *_args: None,
    )

    runtime.analisar("cuida desse conteúdo")

    assert len(pedidos) == 1
    assert pedidos[0].com_tools is False


def test_consulta_operacional_reconhece_quantidade_no_feminino() -> None:
    mapa = MapaHabilidadesRuntime()

    assert mapa.parece_consulta_operacional(
        "quantas músicas tem a playlist sendo sendo"
    ) is True


def test_diagnostico_da_linguagem_natural_explica_rota_sem_autorizar() -> None:
    ciclo, _ = _ciclo(
        {"intent": "APP_OPEN", "params": {"nome_app": "opera"}},
    )
    ciclo.resolver_comando_natural("traz o Opera pra frente", "teste")

    diagnostico = ciclo.diagnostico_linguagem_natural()

    assert diagnostico["tentativas"] == 1
    assert diagnostico["resolvidas"] == 1
    assert diagnostico["ultima_intent"] == "APP_OPEN"
    assert diagnostico["ultima_rota"] == "ia-first-arbitrada"
    assert diagnostico["usa_contexto"] is True
    assert diagnostico["usa_memoria"] is True
    assert diagnostico["usa_catalogo_habilidades"] is True
    assert diagnostico["autoriza_execucao"] is False


def test_mesmo_turno_reutiliza_decisao_sem_chamar_interpretador_duas_vezes() -> None:
    turno = {
        "id": 701,
        "modalidade": "conversa",
        "modalidade_geral": "conversa",
        "autoriza_execucao": False,
    }
    ciclo, interpretador = _ciclo(None, turno=turno)
    texto = "seria possível fazer isso mais tarde?"

    assert ciclo.resolver_comando_natural(texto, "prioritario") == (None, "")
    assert ciclo.processar_deterministico(texto, "pre-ia", texto) is False

    assert interpretador.chamadas == [texto]
    diagnostico = ciclo.diagnostico_linguagem_natural()
    assert diagnostico["tentativas"] == 1
    assert diagnostico["reutilizadas_no_turno"] == 1


def test_mesma_frase_e_reavaliada_quando_o_turno_muda() -> None:
    turno = {
        "id": 801,
        "modalidade": "conversa",
        "modalidade_geral": "conversa",
        "autoriza_execucao": False,
    }
    contexto = _ContextoExecucao(turno=turno)
    interpretador = _InterpretadorNatural(None)
    servicos = {
        "_interpretacao_intencao_runtime": interpretador,
        "_normalizar_texto_com_apelidos": lambda texto: str(texto).casefold(),
        "_texto_depende_de_contexto": lambda _texto: False,
        "_refinar_contexto_mental": lambda _texto: None,
        "_texto_cancela_acao_agora": lambda _texto: False,
        "_resolver_comando_contextual_forcado": lambda _texto: None,
        "_resolver_repeticao_ultima_acao": lambda _texto: None,
        "detectar_intencao_deterministica": lambda _texto: None,
        "_extrair_agendamento_local": lambda _texto: None,
        "_extrair_acao_agendada_local": lambda _texto: None,
        "_texto_parece_consulta_operacional": lambda _texto: False,
    }
    ciclo = CicloComandosRuntime(
        namespace_getter=lambda: servicos,
        contexto_intencao_runtime=contexto,
        log=lambda *_args: None,
    )
    texto = "talvez eu organize isso depois"

    assert ciclo.resolver_comando_natural(texto, "turno-1") == (None, "")
    turno["id"] = 802
    assert ciclo.resolver_comando_natural(texto, "turno-2") == (None, "")

    assert interpretador.chamadas == [texto, texto]
    assert ciclo.diagnostico_linguagem_natural()["tentativas"] == 2


def test_runtime_nao_expoe_segundo_passe_de_classificacao() -> None:
    chamadas = []
    namespace = {
        "resolver_comando_natural": (
            lambda texto, origem: chamadas.append((texto, origem)) or (None, "")
        ),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert not hasattr(runtime, "processar")
    assert runtime.processar_prioritarios(
        "coloca uma música para jogar minecraft"
    ) is False
    assert chamadas == [(
        "coloca uma música para jogar minecraft",
        "prioritario-linguagem-natural",
    )]
