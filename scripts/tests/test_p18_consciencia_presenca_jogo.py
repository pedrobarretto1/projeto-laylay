"""A consciência da presença no jogo preserva disponibilidade e autoridade."""

from __future__ import annotations

import re
import unicodedata

import pytest

from mente_laylay.autonomia.contexto_resposta_ia import criar_contexto_prompt_runtime
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime


def _normalizar(texto: str) -> str:
    return "".join(
        letra for letra in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(letra)
    )


def _conferir_contrato_presenca_jogo(texto: str) -> None:
    contrato = _normalizar(texto)
    assert "servico visual" in contrato and "credencial" in contrato
    assert "presenca" in contrato and "segur" in contrato
    assert "relevancia" in contrato
    assert re.search(r"reacao.{0,60}(?:composta|materializada) localmente", contrato)
    assert re.search(r"sem (?:uma )?segunda chamada.{0,20}llm", contrato)
    assert re.search(r"observar.{0,60}nao autoriza.{0,40}execut", contrato)


def test_catalogo_vivo_descreve_presenca_visual_e_reacao_local_no_jogo() -> None:
    mapa = MapaHabilidadesRuntime()
    snapshot = mapa.snapshot()

    _conferir_contrato_presenca_jogo(snapshot["dominios"]["visao"]["descricao"])
    assert set(snapshot["capacidades"]) == set(intents_registradas())
    assert mapa.diagnostico()["autoriza_execucao"] is False


@pytest.mark.parametrize("pergunta", (
    "Você consegue reagir ao jogo Just Cause 3?",
    "Você pode comentar o que acontece no jogo?",
    "Laylay consegue acompanhar o jogo sem outra chamada ao modelo?",
    "Você consegue reagir emocionalmente ao jogo?",
))
def test_pergunta_natural_descreve_reacao_local_sem_afirmar_efeito(
    pergunta: str,
) -> None:
    mapa = MapaHabilidadesRuntime()
    antes = mapa.snapshot()

    resposta = mapa.responder_pergunta_capacidade(pergunta)

    _conferir_contrato_presenca_jogo(resposta)
    assert mapa.snapshot() == antes


@pytest.mark.parametrize("pergunta", (
    "Você consegue reagir ao jogo Just Cause 3?",
    "Você pode acompanhar o jogo?",
))
def test_retrieval_contextual_transporta_limites_do_jogo_fora_da_personalidade(
    pergunta: str,
) -> None:
    mapa = MapaHabilidadesRuntime()
    contexto = mapa.contexto_para_prompt(pergunta)
    assert "visao" in mapa.dominios_relevantes(pergunta)
    assert "- visao [disponivel]" in contexto
    assert "- arquivos" not in contexto
    assert "- navegador" not in contexto
    _conferir_contrato_presenca_jogo(contexto)
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


def test_presenca_do_jogo_indisponivel_nao_e_prometida_por_visao_parcial() -> None:
    mapa = MapaHabilidadesRuntime(operacional_getter=lambda: {
        "capacidades": {
            "GAME_VISION": {
                "estado": "indisponivel", "motivo": "credencial_visual_ausente",
            },
        },
    })
    assert mapa.snapshot()["dominios"]["visao"]["estado"] == "parcial"

    resposta = mapa.responder_pergunta_capacidade(
        "Você consegue reagir emocionalmente ao jogo?",
    )

    assert "indispon" in resposta.casefold()
    assert "composta localmente" not in resposta.casefold()


def test_ausencia_do_servico_visual_nao_e_prometida_por_personalidade_disponivel() -> None:
    mapa = MapaHabilidadesRuntime(saude_getter=lambda: {
        "visao_jogo": {"status": "indisponivel"},
    })
    assert mapa.snapshot()["dominios"]["personalidade"]["estado"] == "disponivel"

    resposta = mapa.responder_pergunta_capacidade(
        "Você pode reagir emocionalmente ao jogo?",
    )

    assert "indispon" in resposta.casefold()
    assert "composta localmente" not in resposta.casefold()


@pytest.mark.parametrize("texto", (
    "comenta esse momento do jogo",
    "reaja ao jogo e ligue a lâmpada",
))
def test_comando_novo_nao_e_consumido_pelo_catalogo_de_presenca(texto: str) -> None:
    mapa = MapaHabilidadesRuntime()
    antes = mapa.snapshot()

    assert mapa.responder_pergunta_capacidade(texto) == ""
    assert mapa.snapshot() == antes


def test_turno_autorizado_permanece_no_roteador_de_execucao() -> None:
    mapa = MapaHabilidadesRuntime()

    assert mapa.responder_pergunta_capacidade(
        "Você pode reagir ao jogo e abrir a Calculadora?",
        turno={"autoriza_execucao": True},
    ) == ""
