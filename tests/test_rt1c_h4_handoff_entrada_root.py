"""RT1-C — handoff H4 através da entrada e do Coordenador montados pelo root.

Esta prova NÃO cria um Coordenador novo e NÃO chama agendar() como uma API
isolada de componente.

Ela:
1. importa `laylay.py`;
2. usa `_processar_entrada_voz`, o callback que o Ouvido do root realmente usa;
3. intercepta apenas a entrada de `_processar_agendado` com uma barreira
   determinística;
4. observa o contexto pelo Diretor montado pelo root antes do turno começar.

Janela procurada:

    entrada de voz aceita
        ↓
    Coordenador já possui a utterance
        ↓
    [BARREIRA antes de processar_entrada]
        ↓
    usuario_falando == False
    turno_ativo == False
    interacao_usuario_ativa == True
        ↓
    presença deve perder prioridade

USER INTERACTION OWNERSHIP > AUTONOMOUS PRESENCE
"""

from __future__ import annotations

import importlib
import threading
import time
from typing import Any


class _RespostaControlada:
    """Evita LLM/voz depois de liberarmos a barreira."""

    def __init__(self) -> None:
        self.chamadas: list[tuple[str, str]] = []

    def processar(
        self,
        texto: str,
        *,
        origem: str = "desconhecida",
        **_kwargs: Any,
    ) -> bool:
        self.chamadas.append((str(texto), str(origem)))
        return True


def test_rt1c_entrada_aceita_mantem_owner_no_root_antes_do_turno():
    root = importlib.import_module("laylay")

    entrada_voz = root._processar_entrada_voz
    coordenador = root._coordenador_exec_runtime
    diretor = root._diretor_presenca_runtime

    # Prova de identidade mínima: o Ouvido do root aponta exatamente para
    # esta entrada. Se isso mudar, RT1-C deixaria de representar o handoff
    # acústico/canônico que produção usa.
    assert root._ouvido_whisper_runtime.processar_texto is entrada_voz

    worker_entrou = threading.Event()
    liberar_worker = threading.Event()
    worker_terminou = threading.Event()

    processar_agendado_real = coordenador._processar_agendado
    resposta_getter_real = coordenador._resposta_ia_getter
    resposta_controlada = _RespostaControlada()

    def processar_agendado_com_barreira(
        texto: str,
        geracao: int,
        origem: str = "desconhecida",
    ) -> Any:
        worker_entrou.set()
        try:
            if not liberar_worker.wait(timeout=3.0):
                raise RuntimeError("timeout esperando liberação da barreira RT1-C")
            return processar_agendado_real(
                texto,
                geracao,
                origem,
            )
        finally:
            worker_terminou.set()

    coordenador._processar_agendado = processar_agendado_com_barreira
    # Esta troca ocorre somente para o trecho APÓS a barreira. O que RT1-C
    # mede — admissão, claim e contexto — já aconteceu antes dela.
    coordenador._resposta_ia_getter = lambda: resposta_controlada

    texto = "essa pista continua fácil"
    retorno = None

    try:
        # Entra pela callback REAL usada pelo Ouvido do root.
        retorno = entrada_voz(texto)

        assert worker_entrou.wait(timeout=2.0), (
            "a entrada de voz do root não alcançou o worker do Coordenador"
        )

        # Nenhum turno/resposta foi iniciado ainda.
        assert resposta_controlada.chamadas == []

        # A própria estrutura real do Coordenador deve considerar a utterance
        # em processamento: a mesma entrada é recusada enquanto a barreira está
        # aberta. Fazemos isso diretamente no Coordenador apenas como
        # observação do bookkeeping; não é o estímulo principal do teste.
        duplicata = coordenador.agendar(
            texto,
            origem="voz",
        )
        assert duplicata is None, (
            "a entrada chegou ao worker, mas o Coordenador não a considera "
            "em processamento"
        )

        contexto = diretor._contexto()

        assert not bool(contexto.get("usuario_falando")), (
            "pré-condição H4 inválida: usuario_falando ainda está True"
        )
        assert not bool(contexto.get("turno_ativo")), (
            "pré-condição H4 inválida: um turno começou antes da barreira"
        )

        assert contexto.get("interacao_usuario_ativa") is True, (
            "RT1-C RED: a entrada de voz já foi aceita pelo Coordenador do root, "
            "mas o contexto real do Diretor perdeu ownership antes de o turno "
            "começar. "
            f"contexto={{'usuario_falando': {contexto.get('usuario_falando')!r}, "
            f"'turno_ativo': {contexto.get('turno_ativo')!r}, "
            f"'interacao_usuario_ativa': "
            f"{contexto.get('interacao_usuario_ativa')!r}}}"
        )

        evento = {
            "dominio": "cotidiano",
            "categoria": "companhia",
            "motivo": "evento controlado RT1-C durante handoff de entrada",
            "confianca": 0.95,
            "timestamp": time.time(),
            "validade_s": 120.0,
        }

        motivo = diretor._bloqueio_contextual(
            evento,
            contexto,
            float(diretor.clock()),
        )

        assert motivo == "interacao_usuario_ativa", (
            "o owner está no contexto, mas o Diretor do root não o trata como "
            f"prioridade durante o handoff; motivo={motivo!r}"
        )

    finally:
        liberar_worker.set()
        worker_terminou.wait(timeout=2.0)

        # Se a rota devolveu uma Thread, aguarda explicitamente; em outras
        # configurações ela pode devolver Future ou None.
        if isinstance(retorno, threading.Thread):
            retorno.join(timeout=1.0)

        coordenador._processar_agendado = processar_agendado_real
        coordenador._resposta_ia_getter = resposta_getter_real

    assert resposta_controlada.chamadas == [
        (texto, "voz"),
    ], (
        "depois da barreira, a utterance não seguiu pelo processar_entrada "
        "do Coordenador real"
    )

    # Depois de processar a entrada, o claim canônico deve ter sido liberado.
    contexto_final = diretor._contexto()
    assert contexto_final.get("interacao_usuario_ativa") is False, (
        "claim de entrada ficou órfão depois do worker concluir"
    )
