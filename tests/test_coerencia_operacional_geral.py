"""Regressões do contrato compartilhado entre conversa e execução."""

from __future__ import annotations

import time

from mente_laylay.autonomia.fluxo_resposta_ia import processar_inicio_fluxo_resposta_ia
from mente_laylay.autonomia.sugestoes_sistema import detectar_sugestao_indireta
from mente_laylay.memoria_mental.continuidade_conversa import (
    detectar_comentario_resultado_operacional,
)
from mente_laylay.memoria_mental.reparacao_conversacional import (
    detectar_reparacao_conversacional,
)


def test_desejo_vago_nao_virou_busca_com_titulo_inventado() -> None:
    assert detectar_sugestao_indireta("queria ouvir uma música na verdade") is None

    concreta = detectar_sugestao_indireta("queria ouvir MF DOOM")
    assert concreta["params"]["acao_sugerida"]["params"]["query"] == "mf doom"


def test_correcao_natural_refaz_consultas_sem_perder_o_alvo_anterior() -> None:
    for intent in ("MUSIC_SEARCH", "SEARCH", "FILE_SEARCH"):
        estado = {
            "ts": time.time(),
            "ultima_acao_intent": intent,
            "ultima_acao_params": {"query": "aposta brutal"},
        }
        reparacao = detectar_reparacao_conversacional(
            "não Lay, é do Henrique Mendonça",
            estado,
            normalizar_texto=lambda texto: texto.casefold(),
        )
        assert reparacao["tipo"] == "operacional"
        assert reparacao["intencao"]["intent"] == intent
        assert reparacao["intencao"]["params"]["query"] == (
            "aposta brutal henrique mendonça"
        )


def test_pergunta_de_autoria_recupera_resultado_operacional_real() -> None:
    comentario = detectar_comentario_resultado_operacional(
        "por que você colocou música?",
        {
            "ultima_acao_intent": "MUSIC_SEARCH",
            "ultima_acao_params": {"query": "aposta brutal"},
            "ultima_acao_status": "falha_execucao",
            "ultima_acao_confirmada": False,
            "ultima_acao_ok": False,
            "ultima_acao_ts": time.time(),
        },
    )
    assert comentario["tipo"] == "questiona_autoria"
    assert comentario["alvo"] == "aposta brutal"
    assert comentario["confirmado"] is False


def test_fluxo_pre_llm_executa_correcao_de_consulta_ja_contextualizada() -> None:
    executadas: list[dict] = []
    falas: list[str] = []
    estado = {
        "ts": time.time(),
        "ultima_acao_intent": "MUSIC_SEARCH",
        "ultima_acao_params": {"query": "aposta brutal"},
        "ultima_acao_alvo": "aposta brutal",
        "turno_atual": {"modalidade_geral": "correcao", "autoriza_execucao": False},
        "pendencia_atual": {},
    }

    def resolver(texto: str):
        return detectar_reparacao_conversacional(
            texto,
            estado,
            normalizar_texto=lambda valor: valor.casefold(),
        )

    contexto = {
        "mente_integrada_estado": estado,
        "_refinar_contexto_mental": lambda _texto: {},
        "_resolver_reparacao_conversacional": resolver,
        "executar_intencao": lambda dados, _texto: executadas.append(dados) or True,
        "_registrar_resultado_execucao": lambda *_args, **_kwargs: None,
        "_registrar_autoaprimoramento": lambda *_args, **_kwargs: None,
        "falar_com_lipsync": lambda fala, *_args: falas.append(fala),
    }
    contexto["_recarregar_contexto_inicio"] = lambda: dict(contexto)

    assert processar_inicio_fluxo_resposta_ia(
        contexto, "não Lay, é do Henrique Mendonça"
    ) is True
    assert executadas == [{
        "intent": "MUSIC_SEARCH",
        "params": {"query": "aposta brutal henrique mendonça"},
    }]
    assert falas == []
