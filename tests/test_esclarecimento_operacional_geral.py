"""Regressões da camada única de pedidos operacionais incompletos."""

from __future__ import annotations

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.autonomia.pre_fluxo_contextual import (
    processar_esclarecimento_operacional,
)
from mente_laylay.cognicao.esclarecimento_operacional import (
    detectar_esclarecimento_operacional,
    registrar_esclarecimento_operacional,
    resolver_esclarecimento_operacional,
)
from mente_laylay.integracao.estado_contexto_runtime import EstadoContextoRuntime


class _Estado:
    def __init__(self) -> None:
        self.mental: dict = {}

    def substituir(self, dominio: str, estado: dict) -> dict:
        assert dominio == "mental"
        self.mental = dict(estado or {})
        return self.mental


def test_registro_central_reconhece_intencoes_sem_alvo_sem_inventar_dados() -> None:
    casos = {
        "eu queria ouvir uma música na verdade": ("MUSIC_SEARCH", "query"),
        "abre um programa": ("APP_OPEN", "nome_app"),
        "cria uma pasta": ("CREATE_FOLDER", "nome"),
        "cria um arquivo de texto": ("CREATE_FILE", "alvo"),
        "procura um arquivo": ("FILE_SEARCH", "query"),
        "pesquisa alguma coisa": ("SEARCH", "query"),
    }
    for texto, esperado in casos.items():
        contrato = detectar_esclarecimento_operacional(texto)
        assert contrato is not None
        assert (contrato["intent"], contrato["campo"]) == esperado

    # Um alvo escrito pelo usuário vence o esclarecimento genérico.
    assert detectar_esclarecimento_operacional("abre o Opera") is None
    assert detectar_esclarecimento_operacional("cria uma pasta chamada testes") is None


def test_resposta_curta_retorna_para_o_intent_canonico_certo() -> None:
    contrato = detectar_esclarecimento_operacional("cria uma pasta")
    estado = registrar_esclarecimento_operacional({}, contrato)

    resolucao = resolver_esclarecimento_operacional("projetos", estado)
    assert resolucao == {
        "tipo": "executar",
        "intencao": {
            "intent": "CREATE_FOLDER",
            "params": {
                "nome": "projetos",
                "origem": "esclarecimento_operacional",
            },
        },
    }


def test_comando_novo_substitui_esclarecimento_antigo_sem_hijackar_contexto() -> None:
    contrato = detectar_esclarecimento_operacional("abre um programa")
    estado = registrar_esclarecimento_operacional({}, contrato)

    resolucao = resolver_esclarecimento_operacional(
        "liga a luz",
        estado,
        texto_tem_comando_explicito=lambda _texto: True,
    )
    assert resolucao == {"tipo": "substituir"}


def test_pre_fluxo_pergunta_o_dado_faltante_e_grava_pendencia_na_mente_unica() -> None:
    estado = _Estado()
    falas: list[str] = []
    contexto = {
        "_estado_compartilhado_runtime": estado,
        "mente_integrada_estado": estado.mental,
        "_emitir_resposta_curta": lambda _entrada, fala, **_kwargs: falas.append(fala) or True,
    }

    assert processar_esclarecimento_operacional(contexto, "abre um programa") == (
        True,
        "esclarecimento_operacional",
    )
    assert falas == ["Qual programa você quer abrir?"]
    assert estado.mental["pendencia_atual"]["intencao"] == "APP_OPEN"


def test_resposta_da_pendencia_e_executavel_sem_pedir_ajuda_da_llm() -> None:
    estado = _Estado()
    contrato = detectar_esclarecimento_operacional("procura um arquivo")
    estado.mental = registrar_esclarecimento_operacional(estado.mental, contrato)
    runtime = EstadoContextoRuntime(
        namespace_getter=lambda: {
            "_texto_tem_comando_explicito": lambda _texto: False,
        },
        estado_runtime_getter=lambda: estado,
    )

    assert runtime.resolver_pergunta_curta_contextual_intencao("tuya") == {
        "intent": "FILE_SEARCH",
        "params": {
            "query": "tuya",
            "origem": "esclarecimento_operacional",
        },
    }
    assert not estado.mental.get("esclarecimento_operacional_ativo")


def test_prioridade_intercepta_pedido_incompleto_antes_da_llm() -> None:
    estado = _Estado()
    falas: list[str] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_emitir_resposta_curta": lambda _entrada, fala, **_kwargs: falas.append(fala) or True,
            "resolver_comando_natural": lambda *_args: (_ for _ in ()).throw(
                AssertionError("não deve chegar ao resolvedor/LLM")
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("cria uma pasta") is True
    assert falas == ["Qual nome você quer dar à pasta?"]


def test_pedido_novo_limpa_esclarecimento_antigo_antes_de_trocar_de_dominio() -> None:
    estado = _Estado()
    estado.mental = registrar_esclarecimento_operacional(
        estado.mental,
        detectar_esclarecimento_operacional("abre um programa"),
    )
    pedidos: list[str] = []
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_texto_tem_comando_explicito": lambda texto: "musica" in texto.casefold(),
            "_texto_pede_direcao_musical_generica": lambda _texto: True,
            "_responder_pedido_direcao_musical_generica": lambda texto: pedidos.append(texto) or True,
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("coloca uma música") is True
    assert pedidos == ["coloca uma música"]
    assert not estado.mental.get("esclarecimento_operacional_ativo")
