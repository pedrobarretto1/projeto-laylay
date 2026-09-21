from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.autonomia.execucao_ia import CoordenadorExecRuntime
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    PonteIniciativaAplicacaoRuntime,
)


class _RespostaRegistrada:
    def __init__(self) -> None:
        self.chamadas: list[tuple[str, str]] = []

    def processar(
        self,
        texto: str,
        ainda_atual_cb=None,
        origem: str = "desconhecida",
    ) -> None:
        if callable(ainda_atual_cb):
            assert ainda_atual_cb() is True

        self.chamadas.append((texto, origem))


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


def test_red_p1h4_entrada_aceita_preempta_presenca_antes_do_turno() -> None:
    worker_entrou_no_handoff = threading.Event()
    liberar_handoff = threading.Event()

    resposta = _RespostaRegistrada()

    coordenador = CoordenadorExecRuntime(
        contexto_exec_getter=lambda: None,
        resposta_ia_getter=lambda: resposta,
        loop_getter=lambda: None,
        log=lambda *_args: None,
    )

    # Inserimos somente uma barreira determinística ENTRE:
    #
    # CoordenadorExecRuntime.agendar()
    #          ↓
    # assinatura já registrada como "em processamento"
    #          ↓
    # worker criado
    #          ↓
    # [BARREIRA H4]
    #          ↓
    # processar_entrada()
    #          ↓
    # RespostaIARuntime
    #
    # Não alteramos a lógica de agendamento nem o bookkeeping real.
    processar_agendado_real = coordenador._processar_agendado

    def processar_agendado_bloqueado(
        texto: str,
        geracao: int,
        origem: str = "desconhecida",
    ) -> Any:
        worker_entrou_no_handoff.set()

        liberar_handoff.wait(timeout=2.0)

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
        # A utterance foi reconhecida e aceita pela porta canônica.
        thread = coordenador.agendar(
            "essa pista continua fácil",
            origem="voz",
        )

        assert worker_entrou_no_handoff.wait(timeout=1.0)

        # -----------------------------------------------------
        # PROVA DE QUE A ENTRADA REALMENTE JÁ TEM OWNER
        # -----------------------------------------------------

        # RespostaIARuntime ainda não recebeu nada.
        assert resposta.chamadas == []

        # Mas o próprio Coordenador já considera a mesma utterance
        # como "em processamento": a duplicata é recusada.
        duplicata = coordenador.agendar(
            "essa pista continua fácil",
            origem="voz",
        )

        assert duplicata is None

        # -----------------------------------------------------
        # ESTADO PUBLICADO À PRESENÇA
        # -----------------------------------------------------

        contexto_handoff = ponte.contexto()

        assert contexto_handoff["usuario_falando"] is False
        assert contexto_handoff["turno_ativo"] is False

        # Exatamente nessa janela aparece um evento ambiental.
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
                "chave": "p1h4-evento-no-handoff",
                "validade_s": 8.0,
            }
        )

    finally:
        liberar_handoff.set()

        if isinstance(thread, threading.Thread):
            thread.join(timeout=1.0)

    # Depois da barreira, a utterance realmente segue pelo caminho aceito.
    assert resposta.chamadas == [
        ("essa pista continua fácil", "voz"),
    ]

    # ---------------------------------------------------------
    # PRIMEIRA FRONTEIRA RED P1-H4
    # ---------------------------------------------------------

    # A entrada já era propriedade do usuário antes de existir turno
    # canônico. Presença deveria perder a vez.
    assert resultado_presenca["status"] == "bloqueada"

    # Se a preempção for correta, o evento também não deve adquirir
    # cognição autônoma nessa lacuna.
    assert cognicoes_presenca == []