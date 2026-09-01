"""P1-H4-R — entrada aceita mantém ownership antes do turno.

Sucessor causal do H4 histórico.

Mantém a mesma barreira determinística depois de agendar() e antes de
processar_entrada(), mas compõe Coordenador e Ponte com a MESMA instância
do owner canônico.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    PonteIniciativaAplicacaoRuntime,
)
from mente_laylay.integracao.prioridade_interacao_usuario import (
    criar_prioridade_interacao_usuario_runtime,
)


def _turno_evento_valido(evento: dict[str, Any]) -> dict[str, Any]:
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


class _RespostaRegistrada:
    def __init__(self) -> None:
        self.chamadas: list[tuple[str, str]] = []

    def processar(
        self,
        texto: str,
        origem: str = "desconhecida",
        **_kwargs: Any,
    ) -> bool:
        self.chamadas.append(
            (
                str(texto),
                str(origem),
            )
        )
        return True


def test_p1h4r_entrada_aceita_mantem_owner_antes_do_turno() -> None:
    worker_entrou_no_handoff = threading.Event()
    liberar_handoff = threading.Event()

    prioridade = criar_prioridade_interacao_usuario_runtime()
    resposta = _RespostaRegistrada()

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: resposta,
        loop_getter=lambda: None,
        prioridade_interacao=prioridade,
        log=lambda *_args: None,
    )

    # Mesma barreira causal do H4 histórico:
    #
    # agendar()
    #   ↓
    # assinatura registrada
    #   ↓
    # claim entrada_canonica REAL
    #   ↓
    # worker criado
    #   ↓
    # [BARREIRA]
    #   ↓
    # processar_entrada()
    processar_agendado_real = coordenador._processar_agendado

    def processar_agendado_bloqueado(
        texto: str,
        geracao: int,
        origem: str = "desconhecida",
    ) -> Any:
        worker_entrou_no_handoff.set()
        liberar_handoff.wait(timeout=3.0)
        return processar_agendado_real(
            texto,
            geracao,
            origem,
        )

    coordenador._processar_agendado = (  # type: ignore[method-assign]
        processar_agendado_bloqueado
    )

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
        prioridade_interacao_getter=prioridade.ativa,
        log=lambda _texto: None,
    )

    estado_diretor: dict[str, Any] = {}
    cognicoes_presenca: list[dict[str, Any]] = []

    def processar_evento(evento: dict[str, Any]) -> dict[str, Any]:
        cognicoes_presenca.append(dict(evento))
        return _turno_evento_valido(evento)

    diretor = DiretorPresencaRuntime(
        estado_get=lambda: estado_diretor,
        estado_set=lambda novo: (
            estado_diretor.clear()
            or estado_diretor.update(novo)
        ),
        contexto_getter=ponte.contexto,
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

    thread = None
    resultado_presenca: dict[str, Any] = {}
    contexto_handoff: dict[str, Any] = {}

    try:
        thread = coordenador.agendar(
            "essa pista continua fácil",
            origem="voz",
        )

        assert worker_entrou_no_handoff.wait(timeout=2.0)

        # Ainda não existe resposta/turno.
        assert resposta.chamadas == []

        # Bookkeeping real continua recusando duplicata.
        duplicata = coordenador.agendar(
            "essa pista continua fácil",
            origem="voz",
        )
        assert duplicata is None

        contexto_handoff = ponte.contexto()

        # Sinais históricos continuam falsos nesta janela.
        assert contexto_handoff["usuario_falando"] is False
        assert contexto_handoff["turno_ativo"] is False

        # Mas ownership canônico já existe.
        assert prioridade.ativa() is True
        assert contexto_handoff["interacao_usuario_ativa"] is True

        resultado_presenca = diretor.considerar(
            {
                "origem": "observador_jogo",
                "dominio": "jogo",
                "categoria": "celebracao",
                "confianca": 0.98,
                "momento_seguro": True,
                "motivo": (
                    "Pedro passou a curva logo depois de comentar "
                    "sobre a dificuldade da pista"
                ),
                "evidencias": [
                    "curva concluída",
                    "jogo ainda ativo",
                ],
                "chave": "p1h4r-evento-no-handoff",
                "validade_s": 8.0,
            }
        )

        # Primeira fronteira causal do H4-R.
        assert resultado_presenca["status"] == "bloqueada"
        assert cognicoes_presenca == []

    finally:
        liberar_handoff.set()

        if isinstance(thread, threading.Thread):
            thread.join(timeout=2.0)

    # Depois da barreira, a mesma utterance segue pela rota real.
    assert resposta.chamadas == [
        (
            "essa pista continua fácil",
            "voz",
        ),
    ]

    # Claim da entrada foi liberado pelo finally canônico do Coordenador.
    assert prioridade.ativa() is False
