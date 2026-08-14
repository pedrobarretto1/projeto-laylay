"""Regressões extraídas do roteiro completo de 166 turnos."""

from __future__ import annotations

import pytest

from mente_laylay.autonomia.agendamento_mental import (
    texto_pede_lembrete_explicito,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_consulta_aprendizados,
    normalizar_pedido_natural,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.porteiro_acoes import (
    texto_pede_repeticao_curta as porteiro_pede_repeticao,
)
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.guardiao_realidade_pessoal import (
    detectar_experiencia_pessoal_inventada,
    remover_trechos_de_realidade_inventada,
)
from mente_laylay.memoria_mental.compatibilidade_contexto import (
    resolver_repeticao_ultima_acao,
    texto_pede_repeticao_curta,
)


def _normalizar(texto: str) -> str:
    return str(texto or "").casefold().strip()


@pytest.mark.parametrize(
    "texto",
    (
        "Não crie nenhum arquivo.",
        "Não abre o Opera.",
        "Não abre o Spotify.",
    ),
)
def test_negacao_operacional_nao_e_quebrada_em_recusa_mais_comando(
    texto: str,
) -> None:
    turno = classificar_modalidade_turno(texto)

    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""
    assert "comando" not in turno["atos"]


@pytest.mark.parametrize(
    "texto",
    (
        "Como eu abriria o Spotify?",
        "Como eu fecharia o Opera?",
        "Como eu criaria um arquivo?",
    ),
)
def test_pergunta_instrucional_no_condicional_nao_autoriza_execucao(
    texto: str,
) -> None:
    turno = classificar_modalidade_turno(texto)

    assert turno["modalidade"] == "pergunta"
    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""


@pytest.mark.parametrize("texto", ("Próxima.", "Volta para a anterior."))
def test_controle_musical_eliptico_continua_sendo_pedido_explicito(
    texto: str,
) -> None:
    turno = classificar_modalidade_turno(texto)

    assert turno["modalidade"] == "comando"
    assert turno["autoriza_execucao"] is True


@pytest.mark.parametrize(
    "texto",
    (
        "De nada, quer dizer, obrigado de novo.",
        "Obrigado de novo.",
        "Eu falei de novo.",
    ),
)
def test_de_novo_dentro_de_fala_social_nao_repete_ultima_acao(texto: str) -> None:
    estado = {
        "ultima_acao_reexecutavel": True,
        "ultima_acao_intent": "CLOSE_APP",
        "ultima_acao_params": {"nome_app": "opera"},
    }

    assert texto_pede_repeticao_curta(texto, _normalizar) is False
    assert porteiro_pede_repeticao(texto) is False
    assert resolver_repeticao_ultima_acao(texto, estado, _normalizar) is None


@pytest.mark.parametrize(
    "texto",
    ("Tenta de novo.", "Faz de novo.", "Outra vez.", "Mais uma vez."),
)
def test_retry_curto_e_isolado_continua_reconhecido(texto: str) -> None:
    assert texto_pede_repeticao_curta(texto, _normalizar) is True
    assert porteiro_pede_repeticao(texto) is True


def test_consulta_de_memoria_nao_vira_pedido_de_lembrete() -> None:
    texto = "O que você lembra de mim?"
    turno = classificar_modalidade_turno(texto)

    assert texto_pede_lembrete_explicito(texto) is False
    assert turno["modalidade"] == "pergunta"
    assert turno["autoriza_execucao"] is False
    assert detectar_consulta_aprendizados(
        texto,
        params_cb=lambda **kwargs: kwargs,
    ) == {"intent": "LEARNING_QUERY", "params": {"limit": 3}}


def test_voce_lembra_de_mim_consulta_memoria_sem_agendar() -> None:
    texto = "Você lembra de mim?"
    turno = classificar_modalidade_turno(texto)

    assert texto_pede_lembrete_explicito(texto) is False
    assert turno["autoriza_execucao"] is False
    assert detectar_consulta_aprendizados(
        texto,
        params_cb=lambda **kwargs: kwargs,
    ) == {"intent": "LEARNING_QUERY", "params": {"limit": 3}}

    contexto = {
        "normalizar_texto": lambda valor: str(valor).casefold(),
        "texto_conversa_casual_sem_acao": lambda _valor: False,
        "texto_bloqueia_playlist_agora": lambda _valor: False,
        "texto_social_curto": lambda _valor: False,
        "ignorar_token_solto": lambda _valor: False,
        "fluxo_prioritario_da_ia": lambda _valor: False,
        "limpar_destino_pc_b": lambda valor: valor,
        "mente_integrada_estado": {},
    }
    assert detectar_intencao_deterministica_mente(texto, contexto) == {
        "intent": "LEARNING_QUERY",
        "params": {"limit": 3},
    }


@pytest.mark.parametrize(
    "texto",
    (
        "Me lembra de beber água amanhã.",
        "Lembra de me avisar amanhã.",
        "Cria um lembrete para amanhã.",
    ),
)
def test_pedido_real_de_lembrete_continua_reconhecido(texto: str) -> None:
    assert texto_pede_lembrete_explicito(texto) is True
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is True


@pytest.mark.parametrize(
    "fala",
    (
        "Metal me deixa cansada depois de um tempo.",
        "Eu fico exausta com esse som.",
        "Preciso de um espaço para respirar.",
        "Isso sobrecarrega o meu corpo.",
    ),
)
def test_personalidade_nao_inventa_fadiga_ou_respiracao_fisica(fala: str) -> None:
    assert "fadiga_ou_respiracao_inventada" in (
        detectar_experiencia_pessoal_inventada(fala)
    )
    assert remover_trechos_de_realidade_inventada(fala) == ""


def test_personalidade_pode_descrever_caracteristica_da_musica_sem_corpo() -> None:
    fala = "Prefiro rock porque as guitarras deixam a faixa mais dinâmica."

    assert detectar_experiencia_pessoal_inventada(fala) == []


def test_desejo_com_estado_imediato_e_pedido_de_abertura() -> None:
    turno = classificar_modalidade_turno(
        "Eu queria que o Opera estivesse aberto agora.",
    )

    assert turno["modalidade"] == "comando"
    assert turno["autoriza_execucao"] is True
    assert normalizar_pedido_natural(
        "eu queria que o opera estivesse aberto agora",
    ) == ("abre opera", "pedido")


def test_possibilidade_sem_pedido_imediato_nao_autoriza_abertura() -> None:
    turno = classificar_modalidade_turno("Talvez fosse legal abrir o Opera.")

    assert turno["autoriza_execucao"] is False
    assert normalizar_pedido_natural(
        "talvez fosse legal abrir o opera",
    ) == ("talvez fosse legal abrir o opera", "deliberativo")
