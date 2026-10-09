"""Consciência do feedback de presença exige contrato e limites verificáveis."""

from __future__ import annotations

import re
import unicodedata

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import criar_contexto_prompt_runtime
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime


def _normalizar(texto: str) -> str:
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(caractere)
    )


def _conferir_contrato_feedback(texto: str) -> None:
    contrato = _normalizar(texto)
    assert "feedback de presenca" in contrato, "catálogo não descreve este feedback"
    assert re.search(r"entrega\w* confirmad\w*", contrato), "fila não comprova entrega"
    for sinal in ("aceitacao", "recusa", "correcao", "repeticao", "silencio"):
        assert sinal in contrato, f"feedback {sinal} não está descrito"
    assert re.search(r"(?:10|dez) minutos|600\s*(?:s\b|segundos)", contrato)
    assert "origem" in contrato and re.search(r"vincul\w*", contrato)
    assert "motor compartilhado de aprendizado" in contrato
    assert re.search(r"nao (?:concede |gera |cria |da )?autoriz\w*", contrato)
    assert re.search(r"nao.{0,100}preferencia duravel", contrato)


def test_catalogo_vivo_descreve_feedback_da_entrega_confirmada_e_seus_limites() -> None:
    mapa = MapaHabilidadesRuntime()
    snapshot = mapa.snapshot()

    assert snapshot["dominios"]["personalidade"]["estado"] == "disponivel"
    _conferir_contrato_feedback(snapshot["dominios"]["personalidade"]["descricao"])
    assert set(snapshot["capacidades"]) == set(intents_registradas())
    assert mapa.diagnostico()["autoriza_execucao"] is False


@pytest.mark.parametrize("pergunta", (
    "Você consegue aprender com feedback de presença?",
    "Você aprende quando aceito ou recuso seus comentários?",
    "Você consegue aprender quando fico em silêncio depois de uma dica?",
    "Laylay aprende com a correção dos seus comentários?",
    "Você pode aprender com minha reação às suas dicas?",
    "Você aprende quando peço para repetir seus comentários?",
    "Você consegue aprender com feedback de seus avisos?",
))
def test_resposta_natural_explica_feedback_sem_promover_preferencia(pergunta: str) -> None:
    mapa = MapaHabilidadesRuntime()
    antes = mapa.snapshot()

    resposta = mapa.responder_pergunta_capacidade(pergunta)

    assert resposta, "pergunta de capacidade ficou sem explicação"
    _conferir_contrato_feedback(resposta)
    assert mapa.snapshot() == antes, "explicar capacidade não registra feedback ou efeito"


@pytest.mark.parametrize("pergunta", (
    "Você consegue aprender com feedback de presença?",
    "Você consegue aprender quando fico em silêncio depois de uma dica?",
))
def test_recuperacao_contextual_transporta_contrato_fora_da_personalidade_permanente(
    pergunta: str,
) -> None:
    mapa = MapaHabilidadesRuntime()
    assert "personalidade" in mapa.dominios_relevantes(pergunta)
    contexto = mapa.contexto_para_prompt(pergunta)
    assert "- personalidade [disponivel]" in contexto
    _conferir_contrato_feedback(contexto)
    assert "- arquivos" not in contexto
    assert "- navegador" not in contexto
    runtime = criar_contexto_prompt_runtime(
        memoria_sqlite=None,
        resumo_mente_integrada=lambda _texto: "",
        formatar_playlists=lambda: "",
        get_status_humor_prompt=lambda: "calma",
        base_system_prompt="PERSONALIDADE BASE {status_humor}",
        estado_getter=lambda: {"messages": [], "turno_atual": {}},
        mapa_habilidades_prompt=mapa.contexto_para_prompt,
    )

    mensagens, _prompt = runtime.preparar(pergunta)

    assert mensagens[0]["content"].startswith("PERSONALIDADE BASE calma")
    assert contexto not in mensagens[0]["content"]
    assert mensagens[-1] == {"role": "system", "content": contexto}


@pytest.mark.parametrize("texto", (
    "boa dica, gostei dessa",
    "para de comentar",
    "essa dica está errada",
))
def test_feedback_direto_nao_vira_pergunta_de_capacidade(texto: str) -> None:
    mapa = MapaHabilidadesRuntime()
    antes = mapa.snapshot()

    assert mapa.responder_pergunta_capacidade(texto) == ""
    assert mapa.snapshot() == antes


def test_pergunta_com_execucao_autorizada_permanece_no_roteador() -> None:
    mapa = MapaHabilidadesRuntime()
    assert mapa.responder_pergunta_capacidade(
        "Você consegue aprender com feedback de presença?",
        turno={"autoriza_execucao": True},
    ) == ""


def test_feedback_indisponivel_nao_e_prometido_por_outro_dominio_disponivel() -> None:
    mapa = MapaHabilidadesRuntime(operacional_getter=lambda: {
        "dominios": {"personalidade": {"estado": "indisponivel"}},
    })

    resposta = mapa.responder_pergunta_capacidade(
        "Você consegue aprender com feedback de presença na memória?",
    )

    assert "indispon" in resposta.casefold()
    assert "motor compartilhado de aprendizado" not in resposta.casefold()


@pytest.mark.parametrize("pergunta", (
    "Você consegue aprender dicas de Python?",
    "Meu amigo aprende com seus comentários?",
))
def test_aprendizado_sem_feedback_da_assistente_nao_promete_o_contrato_de_presenca(
    pergunta: str,
) -> None:
    mapa = MapaHabilidadesRuntime()

    resposta = mapa.responder_pergunta_capacidade(pergunta)

    assert "feedback de presença" not in resposta.casefold()
    assert "motor compartilhado de aprendizado" not in resposta.casefold()


def test_catalogo_descreve_aviso_entregue_sem_prometer_captura_do_windows():
    texto = _normalizar(MapaHabilidadesRuntime().snapshot()["dominios"]["personalidade"]["descricao"])
    assert "avisos" in texto and "integracoes" in texto
    assert "captur" not in texto
