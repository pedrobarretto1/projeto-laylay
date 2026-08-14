"""Regressões da execução real do roteiro difícil de 14/08/2026."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.roteador_deterministico import normalizar_pedido_natural
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


def test_briefing_traduz_smoky_haze_antes_da_fala() -> None:
    fala = naturalizar_clima_resumido(
        "smoky haze +19°C umidade:63% vento:↙7km/h",
    )

    assert "névoa de fumaça" in fala
    assert "smoky" not in fala.casefold()
    assert "haze" not in fala.casefold()
