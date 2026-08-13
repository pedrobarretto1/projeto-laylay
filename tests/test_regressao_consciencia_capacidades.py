from __future__ import annotations

from types import SimpleNamespace

import pytest

from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.cognicao.identidade_conversacional import (
    ajustar_autorreferencia_assistente,
    analisar_identidade_turno,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.especialistas.mapa_habilidades import MapaHabilidadesRuntime


@pytest.mark.parametrize(
    "texto",
    (
        "quais suas habilidades?",
        "então quais são suas habilidades?",
        "o que dá para você fazer?",
    ),
)
def test_pergunta_geral_le_catalogo_vivo_sem_executar(texto: str) -> None:
    mapa = MapaHabilidadesRuntime()
    turno = classificar_modalidade_turno(texto)

    resposta = mapa.responder_pergunta_capacidade(texto, turno=turno)

    assert "arquivos" in resposta.casefold()
    assert "programas" in resposta.casefold()
    assert "perguntar não executa nada" in resposta.casefold()
    assert "cliente de rede" not in resposta.casefold()
    assert "executor" not in resposta.casefold()
    assert turno["autoriza_execucao"] is False


def test_hipotese_de_criar_arquivo_preserva_conversa_e_nao_executa() -> None:
    texto = "e se eu falar para você criar um arquivo? você vai criar?"
    mapa = MapaHabilidadesRuntime()
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno)

    resposta = mapa.responder_pergunta_capacidade(texto, turno=turno)

    assert turno["natureza_acao"] == "hipotetica"
    assert turno["autoriza_execucao"] is False
    assert plano["requer_execucao"] is False
    assert plano["turno_sem_autorizacao"] is True
    assert "se você me pedir de verdade" in resposta.casefold()
    assert "não fiz nada" in resposta.casefold()


def test_pedido_real_nao_e_consumido_pela_resposta_de_capacidade() -> None:
    texto = "cria um arquivo chamado teste.txt"
    mapa = MapaHabilidadesRuntime()
    turno = classificar_modalidade_turno(texto)

    assert turno["autoriza_execucao"] is True
    assert mapa.responder_pergunta_capacidade(texto, turno=turno) == ""
    assert planejar_turno(texto, turno=turno)["requer_execucao"] is True


def test_contexto_recente_prioriza_capacidade_ligada_ao_assunto() -> None:
    mapa = MapaHabilidadesRuntime()
    texto = "então quais são suas habilidades?"
    resposta = mapa.responder_pergunta_capacidade(
        texto,
        turno=classificar_modalidade_turno(texto),
        contexto={
            "mensagens": [
                {"role": "user", "content": "estou mexendo no seu código"},
                {"role": "assistant", "content": "Eita, sobrou para o meu código."},
            ],
        },
    )

    assert resposta.startswith("Pelo assunto que a gente estava falando")
    assert "criar, procurar e organizar arquivos" in resposta.casefold()
    assert resposta.casefold().count("criar, procurar e organizar arquivos") == 1
    assert len(resposta) < 600
    assert ";" not in resposta


def test_porta_prioritaria_responde_sem_chamar_executor_ou_llm() -> None:
    mapa = MapaHabilidadesRuntime()
    falas: list[str] = []
    execucoes: list[dict] = []
    estado = SimpleNamespace(
        mental={
            "turno_atual": classificar_modalidade_turno(
                "se eu falar para você criar um arquivo, você vai criar?"
            ),
        },
    )
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: {
            "_estado_compartilhado_runtime": estado,
            "_responder_pergunta_capacidade_local": (
                lambda texto: mapa.responder_pergunta_capacidade(
                    texto,
                    turno=estado.mental["turno_atual"],
                )
            ),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
            "executar_intencao": lambda comando, _texto: (
                execucoes.append(comando) or True
            ),
        },
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios(
        "se eu falar para você criar um arquivo, você vai criar?"
    ) is True
    assert falas and "não fiz nada" in falas[-1].casefold()
    assert execucoes == []


def test_fallback_de_comando_nao_substitui_resposta_de_hipotese() -> None:
    texto = "se eu falar para você criar um arquivo, você vai criar?"
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno)

    resultado = verificar_fala_turno(
        "Consigo criar quando você pedir de verdade; agora só conversamos sobre isso.",
        plano=plano,
        origem="ia_final",
    )

    assert "comando_sem_execucao_confirmada" not in resultado["problemas"]
    assert "não executei nem confirmei" not in resultado["fala"].casefold()


def test_seu_codigo_aponta_para_a_propria_laylay() -> None:
    identidade = analisar_identidade_turno("estou mexendo no seu código")

    assert identidade["referencia_laylay"] is True
    assert identidade["relacao_com_laylay"] == "codigo"
    assert ajustar_autorreferencia_assistente(
        "O código do Laylay está complicado."
    ) == "meu código está complicado."


def test_catalogo_projeta_evidencia_de_identidade_sem_autorizar_acao() -> None:
    mapa = MapaHabilidadesRuntime(
        operacional_getter=lambda: {
            "dominios": {
                "arquivos": {"estado": "disponivel", "motivo": "operacional"},
                "sistema": {"estado": "disponivel", "motivo": "operacional"},
            },
        },
    )

    evidencia = mapa.evidencia_conversacional(
        "o que você faz por aqui?",
        turno=classificar_modalidade_turno("o que você faz por aqui?"),
    )

    assert evidencia["fonte"] == "catalogo_vivo"
    assert evidencia["possui_capacidades_locais"] is True
    assert "arquivos" in evidencia["dominios_confirmados"]
    assert "sistema" in evidencia["dominios_confirmados"]
    assert evidencia["autoriza_execucao"] is False
    assert "intent" not in str(evidencia).casefold()
