"""Regressões da execução real do roteiro difícil de 14/08/2026."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_consulta_aprendizados,
    extrair_intencao_abrir_app,
)
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import normalizar_pedido_natural
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.validacao_contrato_fala import (
    validar_aderencia_contrato_fala,
)
from mente_laylay.personalidade.leitura_social_conversa import (
    parece_elogio_ou_agradecimento_curto,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.confirmacao_llm import (
    _motivo_contrato_invalido,
    personalizar_confirmacao_llm,
)
from mente_laylay.percepcao.ambiente_sistema import naturalizar_clima_resumido


@pytest.mark.parametrize(
    ("texto", "esperado"),
    (
        ("eu queria que o opera estivesse aberto agora", "abre opera"),
        ("eu queria que opera estivesse aberto agora", "abre opera"),
        ("eu queria que a calculadora estivesse aberta agora", "abre calculadora"),
        ("eu queria que calculadora estivesse aberta agora", "abre calculadora"),
    ),
)
def test_desejo_de_abertura_nao_arranca_primeira_letra_do_alvo(
    texto: str,
    esperado: str,
) -> None:
    assert normalizar_pedido_natural(texto) == (esperado, "pedido")


def test_extrator_de_app_nao_trata_o_de_opera_como_artigo() -> None:
    comando = extrair_intencao_abrir_app(
        "abre opera",
        normalizar_texto=lambda valor: str(valor).casefold(),
        limpar_destino=lambda valor: valor,
        apps_map={"opera": "opera.exe"},
        sites_diretos={},
    )

    assert comando == {"intent": "APP_OPEN", "params": {"nome_app": "opera"}}


def test_pesquisa_web_explicita_vence_filtro_generico_de_conversa() -> None:
    comando = detectar_intencao_deterministica_mente(
        "Pesquisa por documentação do Python.",
        {
            "normalizar_texto": lambda valor: str(valor).casefold(),
            "texto_conversa_casual_sem_acao": lambda _texto: True,
            "mente_integrada_estado": {},
            "sites_diretos": {},
        },
    )

    assert comando == {
        "intent": "SEARCH",
        "params": {"query": "documentação do python", "engine": "google"},
    }


def _estado_arquivo(caminho: str) -> SimpleNamespace:
    return SimpleNamespace(mental={
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": "teste natural",
            "caminho": caminho,
        },
    })


@pytest.mark.parametrize(
    "texto",
    (
        "Onde ele está agora?",
        "Onde esse arquivo fica agora?",
        "Onde está ele agora?",
    ),
)
def test_localizacao_contextual_aceita_agora(
    texto: str,
    tmp_path,
) -> None:
    caminho = str(tmp_path / "documentos teste" / "teste natural")
    comando = detectar_intencao_arquivos(
        texto,
        params_cb=lambda **kwargs: kwargs,
        estado_mental=_estado_arquivo(caminho).mental,
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert comando == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "teste natural",
            "referencia_caminho": caminho,
            "alvo": "teste natural",
        },
    }


def test_porta_prioritaria_preserva_ponto_txt_e_abre_arquivo_recente(
    tmp_path,
) -> None:
    caminho = str(tmp_path / "teste completo")
    estado = SimpleNamespace(mental={
        "ultima_estrutura_arquivo_params": {
            "tipo": "arquivo",
            "arquivo_nome": "teste completo",
            "caminho": caminho,
        },
    })
    execucoes: list[dict] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            # Reproduz o normalizador geral que remove pontuação. O roteador
            # de arquivo deve receber a fala original mesmo assim.
            "_normalizar_texto_com_apelidos": (
                lambda valor: str(valor).casefold().replace(".", " ")
            ),
            "executar_intencao": lambda comando, _texto: (
                execucoes.append(comando) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "Abre o teste completo.txt e deixa em foco",
    ) is True
    assert execucoes == [{
        "intent": "FILE_OPEN_RESULT",
        "params": {
            "caminho": caminho,
            "alvo": "teste completo",
            "modo": "focus",
            "referencia_contextual": True,
        },
    }]


def test_arquivo_nomeado_vira_busca_exata_quando_contexto_aponta_para_pasta() -> None:
    comando = detectar_intencao_arquivos(
        "Abre o teste completo.txt e deixa em foco",
        params_cb=lambda **kwargs: kwargs,
        estado_mental={
            "ultima_estrutura_arquivo_params": {
                "tipo": "pasta",
                "caminho": r"C:\Downloads\pasta falha",
            },
        },
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert comando == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "teste completo.txt",
            "alvo": "teste completo.txt",
            "abrir_resultado_exato": True,
            "modo": "focus",
        },
    }


def test_delete_nomeado_reusa_caminho_movido_com_txt_opcional() -> None:
    caminho = r"C:\Downloads\documentos teste\teste natural"
    comando = detectar_intencao_arquivos(
        "Apaga o arquivo teste natural.txt.",
        params_cb=lambda **kwargs: kwargs,
        estado_mental={
            "ultima_estrutura_arquivo_params": {
                "tipo": "arquivo",
                "arquivo_nome": "teste natural",
                "caminho": caminho,
            },
        },
        normalizar_texto=lambda valor: str(valor).casefold(),
    )

    assert comando == {
        "intent": "DELETE_ITEM",
        "params": {"alvo": caminho, "tipo": "arquivo"},
    }


def test_fecha_ele_usa_referencia_tipificada_antes_da_conversa() -> None:
    estado = SimpleNamespace(mental={})
    execucoes: list[dict] = []
    registros: list[tuple] = []
    comando = {"intent": "CLOSE_TAB", "params": {"alvo": "youtube"}}
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_resolver_comando_contextual_forcado": lambda _texto: comando,
            "executar_intencao": lambda recebido, _texto: (
                execucoes.append(recebido) or True
            ),
            "_registrar_resultado_execucao": (
                lambda *args, **kwargs: registros.append((args, kwargs))
            ),
            "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
                AssertionError("a referência confirmada não pode cair na conversa")
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("Fecha ele.") is True
    assert execucoes == [comando]
    assert registros[0][1]["origem"] == "prioritario_referencia_tipificada"


def test_mencao_sem_ordem_nao_usa_barreira_de_referencia() -> None:
    estado = SimpleNamespace(mental={})
    chamadas: list[str] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_resolver_comando_contextual_forcado": (
                lambda texto: chamadas.append(texto)
            ),
            "resolver_comando_natural": lambda *_args: (None, ""),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("Eu estava falando dele.") is False
    assert chamadas == []


def test_retrato_pessoal_inclui_nome_cidade_e_gostos_sem_regras_operacionais() -> None:
    falas: list[str] = []
    registros = [
        {
            "tipo": "regra",
            "chave": "regra:fecha ele",
            "valor": "fecha a aba",
            "texto": "quando o usuário diz fecha ele, fecha a aba",
            "natureza": "confirmado",
            "confirmado_usuario": True,
        },
        {
            "tipo": "preferencia",
            "chave": "preferencia:quando o usuario diz bom dia",
            "valor": "perguntar pelo domingo",
            "texto": "quando o usuário diz bom dia, perguntar pelo domingo",
            "natureza": "confirmado",
            "confirmado_usuario": True,
        },
        {
            "tipo": "preferencia",
            "chave": "preferencia:afinidade:rock",
            "valor": "rock",
            "texto": "você gosta de rock",
            "natureza": "confirmado",
            "confirmado_usuario": True,
        },
        {
            "tipo": "identidade",
            "chave": "identidade:nome_usuario",
            "valor": "Pedro",
            "texto": "O nome confirmado do usuário é Pedro.",
            "natureza": "confirmado",
            "confirmado_usuario": True,
        },
        {
            "tipo": "fato_pessoal",
            "chave": "fato_pessoal:local onde mora",
            "valor": "Boituva",
            "texto": "você mora em Boituva",
            "natureza": "confirmado",
            "confirmado_usuario": True,
        },
    ]
    deps = DependenciasExecutorInformacoes(
        marcar_resultado=lambda *_args, **_kwargs: None,
        falar_por_status=lambda *_args, **_kwargs: None,
        registrar_mente=lambda *_args, **_kwargs: None,
    )

    resultado = executar_intencao_informacoes(
        "LEARNING_QUERY",
        {"limit": 10, "modo": "retrato"},
        "O que você lembra de mim?",
        {
            "_recuperar_aprendizados": lambda **_kwargs: registros,
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        deps,
    )

    assert resultado.tratado is True
    resposta = falas[0].casefold()
    assert "seu nome é pedro" in resposta
    assert "você mora em boituva" in resposta
    assert "rock" in resposta
    assert "fecha ele" not in resposta
    assert "domingo" not in resposta


def test_consulta_onde_moro_filtra_confiabilidade_operacional() -> None:
    comando = detectar_consulta_aprendizados(
        "Onde eu moro?",
        params_cb=lambda **kwargs: kwargs,
    )
    assert comando == {
        "intent": "LEARNING_QUERY",
        "params": {
            "limit": 3,
            "query": "mora local",
            "modo": "listar",
            "categoria": "fato_pessoal",
        },
    }

    falas: list[str] = []
    executar_intencao_informacoes(
        "LEARNING_QUERY",
        comando["params"],
        "Onde eu moro?",
        {
            "_recuperar_aprendizados": lambda **_kwargs: [
                {
                    "tipo": "fato_pessoal",
                    "chave": "fato_pessoal:local onde mora",
                    "texto": "você mora em Boituva",
                    "natureza": "confirmado",
                    "confirmado_usuario": True,
                },
                {
                    "tipo": "confiabilidade",
                    "chave": "confiabilidade:learning_query:mora local",
                    "texto": "a ação LEARNING_QUERY em listar: mora local costuma funcionar",
                    "natureza": "padrao_percebido",
                },
            ],
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
        },
        DependenciasExecutorInformacoes(
            marcar_resultado=lambda *_args, **_kwargs: None,
            falar_por_status=lambda *_args, **_kwargs: None,
            registrar_mente=lambda *_args, **_kwargs: None,
        ),
    )

    assert "Boituva" in falas[0]
    assert "LEARNING_QUERY" not in falas[0]
    assert "costuma funcionar" not in falas[0]


def test_saudacao_rejeita_vocativo_inventado_e_agradecimento_nao_retoma_rock() -> None:
    contrato_saudacao = construir_contrato_semantico_fala(
        "Oi Lay.",
        plano={"atos": [{"tipo": "saudacao"}]},
        funcao_comunicativa={"funcao": "saudacao"},
    )
    saudacao = validar_aderencia_contrato_fala(
        "Oi Lay.",
        "Oi, Nanda. Tudo bem?",
        contrato_fala=contrato_saudacao,
    )
    assert "saudacao_inventou_vocativo" in saudacao["problemas"]

    contrato_agradecimento = construir_contrato_semantico_fala(
        "Obrigado.",
        plano={"atos": [{"tipo": "reacao"}]},
        funcao_comunicativa={"funcao": "agradecimento"},
    )
    agradecimento = validar_aderencia_contrato_fala(
        "Obrigado.",
        "Foi um prazer conversar sobre rock — obrigado por compartilhar.",
        contrato_fala=contrato_agradecimento,
    )
    assert contrato_agradecimento["roteiro_concreto"]["estrategia"] == "encerramento_social"
    assert "agradecimento_retomou_assunto_antigo" in agradecimento["problemas"]
    assert parece_elogio_ou_agradecimento_curto(
        {}, "De nada, quer dizer, obrigado de novo."
    ) is True


def test_briefing_traduz_smoky_haze_antes_da_fala() -> None:
    fala = naturalizar_clima_resumido(
        "smoky haze +19°C umidade:63% vento:↙7km/h",
    )

    assert "névoa de fumaça" in fala
    assert "smoky" not in fala.casefold()
    assert "haze" not in fala.casefold()


def test_pesquisa_web_preserva_fala_factual_local() -> None:
    chamadas: list[str] = []
    resultado = ResultadoAcao(
        intent="SEARCH",
        status="pesquisa_realizada",
        alvo="documentação do Python",
        executou=True,
        confirmado=True,
    )
    fala = "Abri a pesquisa por documentação do Python."

    confirmacao = personalizar_confirmacao_llm(
        resultado,
        fala,
        classe="sucesso",
        emocao="calma",
        nivel=1,
        enviar_mensagem=lambda *_args, **_kwargs: chamadas.append("llm"),
        contexto={},
    )
    assert confirmacao.fala == fala
    assert confirmacao.usada_llm is False

    assert chamadas == []


@pytest.mark.parametrize(
    ("fala_ruim", "motivo"),
    (
        (
            "A lâmpada do quarto não respondeu. Eu já dei três tentativas.",
            "estado_operacional_nao_evidenciado",
        ),
        (
            "A lâmpada do quarto não respondeu. Não foi o estilo de ninguém.",
            "contexto_alheio_ao_resultado",
        ),
    ),
)
def test_indisponibilidade_iot_rejeita_contexto_e_tentativas_inventadas(
    fala_ruim: str,
    motivo: str,
) -> None:
    resultado = ResultadoAcao(
        intent="IOT_CONTROL",
        status="indisponivel",
        alvo="lampada_quarto",
        executou=False,
        confirmado=False,
    )
    assert _motivo_contrato_invalido(
        fala_ruim,
        resultado=resultado,
        classe="falha",
        status_declarado="indisponivel",
        alvo_declarado="lampada_quarto",
    ) == motivo


def test_falha_de_comando_explicito_nao_pode_virar_possibilidade() -> None:
    resultado = ResultadoAcao(
        intent="APP_OPEN",
        status="nao_encontrado",
        alvo="aplicativo que não existe",
        executou=False,
        confirmado=False,
    )

    assert _motivo_contrato_invalido(
        "Não executei. Ficou como uma possibilidade que não virou realidade.",
        resultado=resultado,
        classe="falha",
        status_declarado="nao_encontrado",
        alvo_declarado="aplicativo que não existe",
    ) == "falha_rebaixada_a_hipotese"
