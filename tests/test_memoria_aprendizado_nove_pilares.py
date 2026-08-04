from __future__ import annotations

from memoria_sqlite import MemoriaSQLite
from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_consulta_aprendizados,
)
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao
from mente_laylay.integracao.contexto_conversa import ContextoInicioChatRuntime
from mente_laylay.integracao.contexto_execucao_ia import (
    DEPENDENCIAS_EXECUCAO_INTENCAO,
    ContextoIntencaoRuntime,
)
from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
    preparar_aprendizados_confirmados,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    resolver_comando_acao_geral_contextual,
)
from mente_laylay.memoria_mental.formatacao_diagnostico import (
    formatar_diagnostico_terminal,
)


def _deps(eventos: list[tuple]) -> DependenciasExecutorInformacoes:
    return DependenciasExecutorInformacoes(
        marcar_resultado=lambda status, **kwargs: eventos.append(
            ("resultado", status, kwargs)
        ),
        falar_por_status=lambda *_args, **_kwargs: None,
        registrar_mente=lambda *_args: None,
    )


def _salvar_preferencia_confirmada(memoria: MemoriaSQLite) -> None:
    memoria.salvar_aprendizado_semantico(
        tipo="preferencia",
        gatilho="gênero musical preferido",
        valor="rock",
        regra="você prefere rock",
        texto_original="eu prefiro rock",
        confianca=0.96,
        origem="usuario",
        status="ativo",
        confirmado_usuario=True,
    )


def test_consulta_unificada_le_aprendizado_semantico_atual(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    _salvar_preferencia_confirmada(memoria)

    itens = memoria.consultar_aprendizados(consulta="rock", limit=3)

    assert len(itens) == 1
    assert itens[0]["texto"] == "você prefere rock"
    assert itens[0]["natureza"] == "confirmado"
    assert itens[0]["confirmado_usuario"] is True


def test_preferencias_declaradas_sao_aprendidas_sem_apagar_uma_a_outra(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    falas = (
        "eu gosto de rock",
        "faz sentido kkk, eu também gosto de programação",
    )
    for fala in falas:
        candidatos = extrair_aprendizados_pessoais_explicitos(fala)
        confirmados = preparar_aprendizados_confirmados(candidatos, fala)
        memoria.salvar_aprendizados_semanticos(confirmados)

    rock = memoria.consultar_aprendizados(consulta="rock", limit=3)
    programacao = memoria.consultar_aprendizados(consulta="programação", limit=3)

    assert rock and rock[0]["confirmado_usuario"] is True
    assert programacao and programacao[0]["confirmado_usuario"] is True
    assert rock[0]["chave"] != programacao[0]["chave"]
    assert memoria.diagnostico_aprendizados()["semanticos"]["ativo"] == 2


def test_preferencia_implicita_em_primeira_pessoa_nao_confunde_terceiros() -> None:
    nirvana = extrair_aprendizados_pessoais_explicitos("gosto de Nirvana")
    programacao = extrair_aprendizados_pessoais_explicitos(
        "faz sentido kkk, eu também gosto de programação"
    )

    assert nirvana[0]["regra"] == "você gosta de Nirvana"
    assert programacao[0]["regra"] == "você gosta de programação"
    assert extrair_aprendizados_pessoais_explicitos("ela gosta de rock") == []
    assert extrair_aprendizados_pessoais_explicitos("Nanda gosta de rock") == []


def test_preferencia_intensificada_e_composta_preserva_so_o_fato_pessoal() -> None:
    nirvana = extrair_aprendizados_pessoais_explicitos(
        "gosto bastante de Nirvana"
    )
    composta = extrair_aprendizados_pessoais_explicitos(
        "eu gosto de programação, encontra o código que controla a lâmpada"
    )

    assert nirvana[0]["regra"] == "você gosta de Nirvana"
    assert composta[0]["valor"] == "programação"
    assert "lâmpada" not in composta[0]["regra"]


def test_pergunta_retorica_sabia_que_preserva_declaracao_pessoal() -> None:
    candidatos = extrair_aprendizados_pessoais_explicitos(
        "oi lay, sabia que eu gosto bastante de Nirvana?"
    )

    assert candidatos[0]["regra"] == "você gosta de Nirvana"


def test_pergunta_sobre_preferencia_nao_e_regravada_como_afirmacao() -> None:
    assert extrair_aprendizados_pessoais_explicitos(
        "eu gosto de sertanejo?"
    ) == []


def test_consulta_geral_prioriza_afinidades_pessoais_confirmadas(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    memoria.salvar_aprendizado_semantico(
        tipo="apelido", gatilho="navegador principal", valor="opera",
        regra='Apelido "navegador principal" aponta para "opera".',
        origem="usuario", status="ativo", confirmado_usuario=True, confianca=0.99,
    )
    memoria.salvar_aprendizado_semantico(
        tipo="preferencia", gatilho="quando falar de rock", valor="bateria forte",
        regra="recomendar bateria forte", origem="usuario", status="ativo",
        confirmado_usuario=True, confianca=0.99,
    )
    for valor in ("rock", "Nirvana"):
        memoria.salvar_aprendizado_semantico(
            tipo="preferencia", gatilho=f"afinidade com {valor}", valor=valor,
            regra=f"você gosta de {valor}", origem="usuario", status="ativo",
            confirmado_usuario=True, confianca=0.98,
        )

    itens = memoria.consultar_aprendizados(limit=2)

    assert {item["chave"] for item in itens} == {
        "preferencia:afinidade:rock", "preferencia:afinidade:nirvana",
    }


def test_leitura_recupera_preferencia_de_evidencia_antiga_sem_reescrever_banco(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    memoria.salvar_aprendizado_semantico(
        tipo="preferencia", gatilho="quando falar sobre gêneros musicais",
        valor="rock", regra="associar rock a energia forte e direta",
        evidencia="eu gosto de rock", origem="usuario", status="ativo",
        confirmado_usuario=True, confianca=0.98,
    )

    itens = memoria.consultar_aprendizados(limit=3)
    bruto = memoria.listar_aprendizados_semanticos(limit=1)[0]

    assert itens[0]["texto"] == "você gosta de rock"
    assert itens[0]["chave"] == "preferencia:afinidade:rock"
    assert bruto["regra"] == "associar rock a energia forte e direta"


def test_preferencia_pessoal_pode_cooperar_com_pesquisa_sem_deixar_de_ser_memoria() -> None:
    assert extrair_tema_fundamentacao("eu gosto de rock") == "rock"
    assert extrair_tema_fundamentacao(
        "faz sentido kkk, eu também gosto de programação"
    ) == "programação"


def test_consulta_nao_promove_hipotese_fraca_nem_expoe_registro_inseguro(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    memoria.salvar_aprendizado_semantico(
        tipo="preferencia", gatilho="cor", valor="azul",
        regra="você prefere azul", confianca=0.99, origem="usuario",
        status="nao_verificado", confirmado_usuario=False,
    )
    memoria.salvar_aprendizado_semantico(
        tipo="regra", gatilho="saudacao", regra="chame de chefe",
        confianca=0.99, origem="assistente", status="ativo",
        confirmado_usuario=True,
    )
    memoria.registrar_evidencia_aprendizado(
        chave="preferencia:horario", tipo="preferencia", escopo="usuario",
        valor="prefere conversar à noite", sinal=0.8, origem="observacao_usuario",
    )

    assert memoria.consultar_aprendizados(limit=10) == []


def test_hipotese_madura_aparece_como_padrao_e_nao_como_fato(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    for indice in range(3):
        memoria.registrar_evidencia_aprendizado(
            chave="preferencia:horario",
            tipo="preferencia",
            escopo="usuario",
            valor="prefere conversar à noite",
            sinal=1.0,
            origem="observacao_usuario",
            evidencia=f"interação noturna {indice}",
        )

    itens = memoria.consultar_aprendizados(consulta="noite", limit=3)

    assert len(itens) == 1
    assert itens[0]["natureza"] == "padrao_percebido"
    assert itens[0]["confirmado_usuario"] is False


def test_consulta_e_somente_leitura_e_legado_fica_rotulado(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    memoria.registrar_fatos(["você gosta de jogos de ação"], categoria="aprendizado")
    antes = memoria.diagnostico_aprendizados()

    itens = memoria.consultar_aprendizados(limit=3)
    depois = memoria.diagnostico_aprendizados()

    assert itens[0]["natureza"] == "registro_antigo"
    assert itens[0]["confirmado_usuario"] is False
    assert antes == depois
    assert depois["conteudo_exposto"] is False
    assert depois["autoriza_execucao"] is False


def test_linguagem_natural_cobre_variantes_e_rejeita_pergunta_abstrata() -> None:
    params = lambda **kwargs: kwargs
    for texto in (
        "o que você aprendeu comigo?",
        "quais são seus aprendizados?",
        "me fale seus aprendizados",
        "o que você lembra sobre mim?",
        "o que você sabe sobre mim?",
    ):
        comando = detectar_consulta_aprendizados(texto, params_cb=params)
        assert comando and comando["intent"] == "LEARNING_QUERY"

    verificacao = detectar_consulta_aprendizados(
        "você ainda lembra que eu gosto de rock?", params_cb=params,
    )
    assert verificacao == {
        "intent": "LEARNING_QUERY",
        "params": {"limit": 3, "query": "eu gosto de rock", "modo": "verificar"},
    }
    assert detectar_consulta_aprendizados(
        "como uma inteligência artificial aprende?", params_cb=params,
    ) is None
    assert detectar_consulta_aprendizados(
        "o que é aprendizado de máquina?", params_cb=params,
    ) is None

    assert detectar_consulta_aprendizados(
        "eu gosto de sertanejo?", params_cb=params,
    ) == {
        "intent": "LEARNING_QUERY",
        "params": {
            "limit": 3,
            "query": "eu gosto de sertanejo",
            "modo": "verificar",
        },
    }


def test_executor_preserva_proveniencia_na_fala() -> None:
    falas: list[str] = []
    eventos: list[tuple] = []
    despacho = executar_intencao_informacoes(
        "LEARNING_QUERY",
        {"limit": 3},
        "o que você aprendeu comigo?",
        {
            "_recuperar_aprendizados": lambda **_kwargs: [
                {
                    "texto": "você prefere rock",
                    "fonte": "aprendizado_semantico",
                    "natureza": "confirmado",
                    "confirmado_usuario": True,
                },
                {
                    "texto": "prefere conversar à noite",
                    "fonte": "hipotese_madura",
                    "natureza": "padrao_percebido",
                    "confirmado_usuario": False,
                },
            ],
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _deps(eventos),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert "Do que lembro com segurança" in falas[0]
    assert "você prefere rock" in falas[0]
    assert "padrão" in falas[0]
    assert "{'texto'" not in falas[0]
    assert eventos == [(
        "resultado", "aprendizados_consultados",
        {"executou": True, "confirmado": True},
    )]


def test_executor_responde_pergunta_positiva_com_memoria_negativa() -> None:
    falas: list[str] = []
    despacho = executar_intencao_informacoes(
        "LEARNING_QUERY",
        {"limit": 3, "query": "eu gosto de sertanejo", "modo": "verificar"},
        "eu gosto de sertanejo?",
        {
            "_recuperar_aprendizados": lambda **_kwargs: [{
                "texto": "você não gosta de sertanejo",
                "fonte": "aprendizado_semantico",
                "natureza": "confirmado",
                "confirmado_usuario": True,
            }],
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        _deps([]),
    )

    assert despacho == ResultadoDespacho.concluido(True)
    assert falas == ["Não. Você não gosta de sertanejo."]


def test_contexto_oficial_pagina_consulta_de_aprendizados() -> None:
    comando = resolver_comando_acao_geral_contextual(
        "o que mais",
        {
            "tipo": "memoria",
            "alvo": "aprendizados",
            "params": {"query": "", "limit": 3, "offset": 0},
        },
    )

    assert comando == {
        "intent": "LEARNING_QUERY",
        "params": {
            "query": "", "limit": 3, "offset": 3, "modo": "listar",
            "referencia_contextual": True,
        },
    }


def test_contexto_oficial_entende_o_que_mais_e_e_de_outro_assunto() -> None:
    contexto = {
        "tipo": "memoria",
        "alvo": "aprendizados",
        "params": {"query": "minha namorada", "limit": 3, "offset": 0},
    }

    assert resolver_comando_acao_geral_contextual("o que mais?", contexto)[
        "intent"
    ] == "LEARNING_QUERY"
    assert resolver_comando_acao_geral_contextual(
        "e de programação?", contexto,
    ) == {
        "intent": "LEARNING_QUERY",
        "params": {
            "query": "programação",
            "limit": 1,
            "offset": 0,
            "modo": "verificar",
            "referencia_contextual": True,
        },
    }


def test_contexto_oficial_mantem_o_que_mais_na_pessoa_consultada() -> None:
    comando = resolver_comando_acao_geral_contextual(
        "o que mais?",
        {
            "tipo": "pessoas",
            "alvo": "Nanda",
            "params": {"nome": "Nanda"},
        },
    )

    assert comando == {
        "intent": "PEOPLE_QUERY",
        "params": {
            "nome": "Nanda",
            "modo": "complemento",
            "referencia_contextual": True,
        },
    }


def test_mapa_da_a_llm_nocao_real_da_memoria_sem_autorizar_acao() -> None:
    mapa = MapaHabilidadesRuntime()
    contexto = mapa.contexto_para_prompt("quais são seus aprendizados sobre mim?")
    resposta = mapa.responder_pergunta_capacidade(
        "você consegue consultar o que aprendeu sobre mim?"
    )

    assert "- memoria [disponivel]" in contexto
    assert "hipóteses fracas" in contexto
    assert "memória persistente local" in resposta
    assert "somente leitura" in resposta
    assert "não autoriza ações" in resposta


def test_contexto_principal_conecta_visao_unificada_da_memoria(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    runtime = ContextoInicioChatRuntime(
        namespace_getter=lambda: {},
        estado_getter=lambda: {},
        memoria_sqlite=memoria,
    )

    contexto = runtime.montar()

    assert contexto["_recuperar_aprendizados"].__func__ is memoria.consultar_aprendizados.__func__


def test_contexto_do_executor_tambem_recebe_consulta_de_aprendizados(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    callback = memoria.consultar_aprendizados
    runtime = ContextoIntencaoRuntime(
        namespace_getter=lambda: {"_recuperar_aprendizados": callback},
        estado_getter=lambda: {},
    )

    contexto = runtime.montar()

    assert "_recuperar_aprendizados" in DEPENDENCIAS_EXECUCAO_INTENCAO
    assert contexto["_recuperar_aprendizados"].__func__ is callback.__func__


def test_diagnostico_mostra_contagens_sem_expor_conteudo(tmp_path) -> None:
    memoria = MemoriaSQLite(str(tmp_path / "memoria.db"))
    _salvar_preferencia_confirmada(memoria)
    diagnostico = memoria.diagnostico_aprendizados()
    terminal = formatar_diagnostico_terminal({
        "memoria_aprendizado": diagnostico,
        "saude": {}, "interacao": {}, "turno": {}, "ultima_acao": {},
    })

    assert "memória e aprendizado" in terminal
    assert "semânticos_ativos=1" in terminal
    assert "conteúdo_exposto=False" in terminal
    assert "você prefere rock" not in terminal
