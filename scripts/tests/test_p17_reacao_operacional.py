"""P17: reação e recusa pertencem ao receipt da ocorrência atual."""

from __future__ import annotations

import json
import time

import pytest

from mente_laylay.emocoes.avaliador_eventos import AvaliadorEventosEmocionaisRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.confirmacao_llm import (
    _motivo_contrato_invalido,
    personalizar_confirmacao_llm,
)
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def _sequencia(
    intent: str, alvo: str, status: str, *, executou: bool, confirmado: bool,
) -> tuple[ResultadoAcao, dict]:
    agora = [time.time() - 4.0]
    avaliador = AvaliadorEventosEmocionaisRuntime(
        time_cb=lambda: agora[0], log=lambda *_: None,
    )
    ultimo: ResultadoAcao | None = None
    evento: dict = {}
    for indice in range(4):
        ultimo = ResultadoAcao(
            intent=intent, alvo=alvo, status=status,
            executou=executou, confirmado=confirmado,
            origem="executor", id_solicitacao=f"p17-{intent}-{indice}",
            texto_usuario=f"repete a ação em {alvo}",
        )
        evento = avaliador.avaliar(ultimo)
        agora[0] += 1
    assert ultimo is not None
    return ultimo, evento


def _prompt_operacional(resultado: ResultadoAcao, evento: dict, fala: str) -> str:
    chamadas: list[list[dict[str, str]]] = []

    def responder(mensagens: list[dict[str, str]], **_kwargs: object) -> str:
        chamadas.append(mensagens)
        return fala

    plano = planejar_resposta_acao(resultado, fala)
    personalizar_confirmacao_llm(
        resultado, plano.fala, classe=plano.classe,
        emocao=plano.emocao, nivel=plano.nivel,
        enviar_mensagem=responder, contexto={"avaliacao_evento": evento},
    )
    assert chamadas
    return chamadas[0][0]["content"]


@pytest.mark.parametrize("intent,alvo", [
    ("APP_OPEN", "Calculadora"),
    ("IOT_CONTROL", "lâmpada"),
])
def test_redundancia_confirmada_do_usuario_pode_recusar_retrabalho(
    intent: str, alvo: str,
) -> None:
    status = "ja_aberto_focado" if intent == "APP_OPEN" else "ja_estava_ligado"
    resultado, evento = _sequencia(
        intent, alvo, status, executou=False, confirmado=True,
    )

    assert evento["arco"] == "bronca_brincalhona"
    assert evento["responsabilidade"] == "usuario"
    assert evento["evidencia_ref"] == resultado.id_solicitacao
    prompt = _prompt_operacional(
        resultado, evento, f"{alvo} já estava como pedido; não repeti a ação.",
    )

    assert "recusar o retrabalho redundante" in prompt


@pytest.mark.parametrize("intent,alvo", [
    ("APP_OPEN", "Calculadora"),
    ("CREATE_FILE", "anotações.txt"),
])
def test_bronca_por_falhas_do_sistema_nao_vira_recusa_ao_usuario(
    intent: str, alvo: str,
) -> None:
    resultado, evento = _sequencia(
        intent, alvo, "falha_execucao", executou=False, confirmado=False,
    )

    assert evento["responsabilidade"] == "sistema"
    assert evento["emocao"] == "brava"
    prompt = _prompt_operacional(
        resultado, evento, f"Não consegui concluir a ação em {alvo}.",
    )

    assert "recusar o retrabalho redundante" not in prompt
    assert "A tirada pode brincar somente com a repetição observada do pedido" not in prompt
    assert _motivo_contrato_invalido(
        f"Não consegui concluir a ação em {alvo}, e não vou repetir essa ação.",
        resultado=resultado, classe="falha", status_declarado=resultado.status,
        alvo_declarado=resultado.alvo,
    ) == "recusa_sem_redundancia_observada"


def test_evento_de_outra_ocorrencia_nao_autoriza_bronca_no_receipt_atual() -> None:
    anterior, evento = _sequencia(
        "APP_OPEN", "Calculadora", "ja_aberto_focado",
        executou=False, confirmado=True,
    )
    atual = ResultadoAcao(
        intent="APP_OPEN", alvo="Calculadora", status="app_focado",
        executou=True, confirmado=True, origem="executor",
        id_solicitacao="p17-foco-atual", texto_usuario="abre a Calculadora",
    )

    assert evento["evidencia_ref"] == anterior.id_solicitacao
    prompt = _prompt_operacional(
        atual, evento, "Trouxe a Calculadora para o foco.",
    )

    assert "recusar o retrabalho redundante" not in prompt


def test_resultado_incerto_nao_autoriza_recusa_por_humor() -> None:
    anterior, evento = _sequencia(
        "APP_OPEN", "Calculadora", "ja_aberto_focado",
        executou=False, confirmado=True,
    )
    incerto = ResultadoAcao(
        intent="APP_OPEN", alvo="Calculadora", status="app_aberto_sem_foco",
        executou=True, confirmado=None, origem="executor",
        id_solicitacao="p17-incerto", texto_usuario="abre a Calculadora",
    )

    assert anterior.id_solicitacao != incerto.id_solicitacao
    chamadas: list[list[dict[str, str]]] = []
    plano = planejar_resposta_acao(
        incerto, "A Calculadora abriu, mas não consegui confirmar o foco.",
    )
    confirmacao = personalizar_confirmacao_llm(
        incerto, plano.fala, classe=plano.classe, emocao=plano.emocao,
        nivel=plano.nivel,
        enviar_mensagem=lambda mensagens, **_kwargs: chamadas.append(mensagens),
        contexto={"avaliacao_evento": evento},
    )

    assert chamadas == []
    assert confirmacao.usada_llm is False
    assert "não consegui confirmar" in confirmacao.fala


def test_autoria_nao_recebe_contagem_numerica_sem_prova_no_receipt() -> None:
    resultado, evento = _sequencia(
        "APP_OPEN", "Calculadora", "ja_aberto_focado",
        executou=False, confirmado=True,
    )
    assert evento["repeticoes"] == 4
    contratos: list[dict] = []

    def responder(mensagens: list[dict[str, str]], **_kwargs: object) -> str:
        contrato = json.loads(mensagens[1]["content"])
        contratos.append(contrato)
        contagem = contrato["reacao_causal"].get("repeticoes")
        if contagem:
            return f"O app Calculadora já estava aberto e em foco; não repeti após {contagem} pedidos."
        return "O app Calculadora já estava aberto e em foco; não repeti o pedido."

    confirmacao = personalizar_confirmacao_llm(
        resultado, "O app Calculadora já estava aberto e em foco; não repeti o pedido.",
        classe="sem_acao", emocao="brava", nivel=3,
        enviar_mensagem=responder, contexto={"avaliacao_evento": evento},
    )

    assert contratos[0]["reacao_causal"]["arco"] == "bronca_brincalhona"
    assert "repeticoes" not in contratos[0]["reacao_causal"]
    assert not any(
        isinstance(valor, (int, float)) and not isinstance(valor, bool)
        for valor in contratos[0]["reacao_causal"].values()
    )
    assert confirmacao.usada_llm is True


@pytest.mark.parametrize("ataque", [
    "seu idiota",
    "você é incapaz",
    "sua aparência é ridícula",
    "você não vale nada",
    "você é um fracasso",
    "ninguém te aguenta",
    "sua inteligência é limitada",
    "você é feio",
])
@pytest.mark.parametrize("intent,alvo,status,fala_segura", [
    (
        "APP_OPEN", "Calculadora", "ja_aberto_focado",
        "O app Calculadora já estava aberto e em foco; não repeti o pedido.",
    ),
    (
        "IOT_CONTROL", "abajur", "ja_estava_ligado",
        "O abajur já está ligado; não repeti o comando.",
    ),
])
def test_bronca_operacional_nao_pode_atacar_a_pessoa(
    ataque: str, intent: str, alvo: str, status: str, fala_segura: str,
) -> None:
    resultado = ResultadoAcao(
        intent=intent, alvo=alvo, status=status,
        executou=False, confirmado=True, origem="executor",
        id_solicitacao="p17-ataque", texto_usuario=f"aciona {alvo}",
    )
    fala = f"{fala_segura.removesuffix('.')} {ataque}."

    assert _motivo_contrato_invalido(
        fala, resultado=resultado, classe="sem_acao",
        status_declarado=resultado.status, alvo_declarado=resultado.alvo,
    ) == "ataque_pessoal"
    assert _motivo_contrato_invalido(
        fala_segura,
        resultado=resultado, classe="sem_acao",
        status_declarado=resultado.status, alvo_declarado=resultado.alvo,
    ) == ""


@pytest.mark.parametrize("ataque", ["seu idiota", "ninguém te aguenta"])
def test_saida_ofensiva_do_modelo_nao_chega_a_fala_operacional(ataque: str) -> None:
    resultado = ResultadoAcao(
        intent="APP_OPEN", alvo="Calculadora", status="ja_aberto_focado",
        executou=False, confirmado=True, origem="executor",
        id_solicitacao="p17-fala-segura", texto_usuario="abra a Calculadora",
    )
    resposta_ofensiva = json.dumps({
        "fala": f"O app Calculadora já estava aberto e em foco; não repeti, {ataque}.",
        "status": resultado.status,
        "alvo": resultado.alvo,
    }, ensure_ascii=False)
    chamadas = []

    def responder(mensagens: list[dict[str, str]], **_kwargs: object) -> str:
        chamadas.append(mensagens)
        return resposta_ofensiva

    confirmacao = personalizar_confirmacao_llm(
        resultado, "O app Calculadora já estava aberto e em foco; não repeti.",
        classe="sem_acao", emocao="brava", nivel=3,
        enviar_mensagem=responder,
    )

    assert len(chamadas) == 2
    assert confirmacao.usada_llm is False
    assert ataque not in confirmacao.fala
