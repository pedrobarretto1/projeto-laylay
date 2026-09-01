from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    PonteIniciativaAplicacaoRuntime,
)
from mente_laylay.percepcao.ouvido_whisper import OuvidoWhisperRuntime


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


def test_red_p1h3_stt_pendente_ainda_preempta_presenca_autonoma() -> None:
    entrou_no_stt = threading.Event()
    liberar_stt = threading.Event()
    entrada_entregue = threading.Event()

    continuar = [True]
    textos_entregues: list[str] = []
    cognicoes_presenca: list[dict[str, Any]] = []

    def processar_texto(texto: str) -> None:
        textos_entregues.append(texto)
        entrada_entregue.set()

    ouvido = OuvidoWhisperRuntime(
        processar_texto=processar_texto,
        esta_falando=lambda: False,
        escuta_permitida=lambda: True,
        modo_chat_ativo=lambda: False,
        modo_jogo_ativo=lambda: True,
        deve_continuar=lambda: continuar[0],
        entrega_assincrona=True,
        log=lambda _texto: None,
    )

    def transcrever_bloqueado(_audio: Any) -> tuple[str, float]:
        entrou_no_stt.set()

        # Mantém a utterance presa exatamente entre:
        #
        # captura concluída
        #       ↓
        # STT em processamento
        #       ↓
        # processar_texto ainda NÃO chamado
        #
        liberar_stt.wait(timeout=2.0)

        return "laylay, teste de prioridade", 0.99

    ouvido.transcrever_com_confianca = transcrever_bloqueado  # type: ignore[method-assign]

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
        usuario_falando_getter=ouvido.usuario_falando,
        log=lambda _texto: None,
    )

    estado_diretor: dict[str, Any] = {}

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

    resultado_presenca: dict[str, Any] = {}
    contexto_durante_stt: dict[str, Any] = {}

    try:
        # Simula exatamente a transição já existente em executar():
        #
        # voz detectada
        #     ↓
        # _usuario_falando = True
        #     ↓
        # fim acústico
        #     ↓
        # _usuario_falando = False
        #     ↓
        # _agendar_entrega(audio)
        ouvido._usuario_falando = True

        assert ouvido.usuario_falando() is True

        ouvido._usuario_falando = False
        ouvido._agendar_entrega(object())

        # Garante que não estamos simplesmente com um áudio parado na fila:
        # o worker REAL já retirou o áudio e está dentro do STT.
        assert entrou_no_stt.wait(timeout=1.0)

        # A utterance ainda NÃO chegou à mente.
        assert textos_entregues == []

        contexto_durante_stt = ponte.contexto()

        # Enquanto o STT está bloqueado, um evento ambiental aparece.
        resultado_presenca = diretor.considerar(
            {
                "origem": "observador_jogo",
                "dominio": "jogo",
                "categoria": "celebracao",
                "confianca": 0.98,
                "momento_seguro": True,
                "motivo": (
                    "Pedro venceu a luta com pouca vida restante"
                ),
                "evidencias": [
                    "vitória confirmada",
                    "vida crítica visível",
                ],
                "chave": "p1h3-evento-durante-stt",
                "validade_s": 8.0,
            }
        )

    finally:
        # Nenhuma thread do teste fica viva depois da prova.
        liberar_stt.set()

        entrada_entregue.wait(timeout=1.0)

        continuar[0] = False

        worker = ouvido._worker_audio
        if worker is not None:
            worker.join(timeout=1.0)

    # ---------------------------------------------------------
    # OBSERVAÇÃO DA RAIZ ATUAL
    # ---------------------------------------------------------

    # Enquanto o STT estava realmente em andamento, o único sinal
    # publicado hoje para prioridade do usuário já havia caído.
    assert contexto_durante_stt["usuario_falando"] is False

    # E confirmamos que era uma utterance real, não ruído de harness:
    # depois que liberamos o STT ela foi entregue à mente.
    assert textos_entregues == ["teste de prioridade"]

    # ---------------------------------------------------------
    # PRIMEIRA FRONTEIRA RED DO P1-H3
    # ---------------------------------------------------------

    # Mesmo com o VAD já em False, a interação de Pedro ainda não terminou
    # semanticamente. Presença autônoma deve perder prioridade.
    assert resultado_presenca["status"] == "bloqueada"

    # Se a preempção estiver correta, evento ambiental nem deve adquirir
    # cognição autônoma enquanto a utterance anterior está pendente.
    assert cognicoes_presenca == []