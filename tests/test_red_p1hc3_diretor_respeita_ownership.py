from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    PonteIniciativaAplicacaoRuntime,
)
from mente_laylay.integracao.prioridade_interacao_usuario import (
    criar_prioridade_interacao_usuario_runtime,
)


def _evento_valido() -> dict[str, Any]:
    return {
        "origem": "observador_jogo",
        "dominio": "jogo",
        "categoria": "celebracao",
        "confianca": 0.98,
        "momento_seguro": True,
        "motivo": "Pedro venceu a luta com pouca vida restante",
        "evidencias": [
            "vitória confirmada",
            "vida crítica visível",
        ],
        "chave": "p1hc3-evento",
        "validade_s": 8.0,
    }


def _turno_evento(evento: dict[str, Any]) -> dict[str, Any]:
    contrato = {
        "funcao": "reacao_evento",
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
    }

    return {
        "natureza_entrada": "evento",
        "entrada_cognitiva": dict(evento),
        "autoridade_usuario": False,
        "permissao_execucao": False,
        "autoriza_execucao": False,
        "contrato_fala": contrato,
    }


def _criar_diretor(
    contexto_getter,
    cognicoes: list[dict[str, Any]],
) -> DiretorPresencaRuntime:
    estado: dict[str, Any] = {}

    def processar_evento(evento: dict[str, Any]) -> dict[str, Any]:
        cognicoes.append(dict(evento))
        return _turno_evento(evento)

    return DiretorPresencaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: (
            estado.clear()
            or estado.update(novo)
        ),
        contexto_getter=contexto_getter,
        registrar_oportunidade=lambda _dados: {
            "decisao": "sugerir",
        },
        processar_evento_cognitivo=processar_evento,
        processar_proposta_comunicativa=lambda *_args, **_kwargs: {
            "status": "agendada",
            "agendada": True,
            "emissao_fisica": False,
            "autoriza_execucao": False,
        },
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )


def test_red_p1hc3_ponte_publica_ownership_canonico() -> None:
    prioridade = criar_prioridade_interacao_usuario_runtime()

    ponte = PonteIniciativaAplicacaoRuntime(
        estado_mental_getter=lambda: {},
        percepcao_getter=lambda _chave, padrao: padrao,
        conversa_getter=lambda _chave, padrao: padrao,
        modo_jogo=SimpleNamespace(
            ativo=True,
            contexto_atual=lambda: {},
        ),
        visao_leitura_getter=lambda: None,
        identificar_jogo=lambda _contexto: {},
        salvar_memoria=lambda: None,
        falar=lambda _texto, _emocao, _nivel: None,
        env_getter=lambda _nome, padrao: padrao,
        usuario_falando_getter=lambda: False,

        # Contrato novo: a Ponte recebe somente uma leitura do owner.
        prioridade_interacao_getter=prioridade.ativa,

        log=lambda _texto: None,
    )

    contexto_livre = ponte.contexto()

    assert contexto_livre["interacao_usuario_ativa"] is False

    claim = prioridade.adquirir("teste_hc3")

    try:
        contexto_ocupado = ponte.contexto()

        assert contexto_ocupado["usuario_falando"] is False
        assert contexto_ocupado["turno_ativo"] is False

        # Mesmo assim, ownership canônico está ativo.
        assert contexto_ocupado["interacao_usuario_ativa"] is True

    finally:
        prioridade.liberar(claim)


def test_red_p1hc3_diretor_bloqueia_antes_da_cognicao_quando_owner_ativo() -> None:
    cognicoes: list[dict[str, Any]] = []

    diretor = _criar_diretor(
        contexto_getter=lambda: {
            "modo_chat": False,
            "conversa_ativa": False,
            "turno_ativo": False,
            "modo_jogo_ativo": True,
            "modo_foco": False,
            "ultima_entrada_ts": 0.0,
            "is_speaking": False,
            "usuario_falando": False,

            # Único sinal que deve mandar nessa prova.
            "interacao_usuario_ativa": True,
        },
        cognicoes=cognicoes,
    )

    resultado = diretor.considerar(
        _evento_valido()
    )

    assert resultado["status"] == "bloqueada"
    assert cognicoes == []


def test_guard_p1hc3_owner_livre_nao_mata_presenca_valida() -> None:
    cognicoes: list[dict[str, Any]] = []

    diretor = _criar_diretor(
        contexto_getter=lambda: {
            "modo_chat": False,
            "conversa_ativa": False,
            "turno_ativo": False,
            "modo_jogo_ativo": True,
            "modo_foco": False,
            "ultima_entrada_ts": 0.0,
            "is_speaking": False,
            "usuario_falando": False,
            "interacao_usuario_ativa": False,
        },
        cognicoes=cognicoes,
    )

    resultado = diretor.considerar(
        _evento_valido()
    )

    assert resultado["status"] == "proposta_cognitiva"
    assert len(cognicoes) == 1