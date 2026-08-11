from __future__ import annotations

from pathlib import Path

from mente_laylay.autonomia.central_notificacoes import CentralNotificacoesRuntime
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local,
)
from mente_laylay.memoria_mental.aprendizado_runtime import AprendizadoRuntime
from mente_laylay.memoria_mental.motor_aprendizado import MotorAprendizadoRuntime


def test_aprendizado_rotina_musica_publica_snapshot_compartilhado_com_fonte(
    tmp_path: Path,
) -> None:
    estado: dict = {}

    def atualizar(**campos) -> None:
        estado.update(campos)

    runtime = AprendizadoRuntime(
        pasta_memoria=str(tmp_path),
        arquivo_rotina=str(tmp_path / "rotina.json"),
        arquivo_musica_historico=str(tmp_path / "historico.json"),
        arquivo_musica_feedback=str(tmp_path / "feedback.json"),
        contexto_getter=lambda: {},
        estado_getter=lambda: estado,
        estado_setter=atualizar,
        log=lambda *_args: None,
    )

    runtime.atualizar(
        musica_feedback_pesos={"noite|nirvana": 2},
        musica_dados_diarios={"2026-08-10 22": {"musicas": ["Nirvana"]}},
    )

    snapshot = runtime.snapshot()
    assert not hasattr(runtime, "_estado_local")
    assert estado["musica_feedback_pesos"] == {"noite|nirvana": 2}
    assert snapshot["proveniencia"]["musica_feedback"] == str(tmp_path / "feedback.json")
    assert snapshot["confianca"]["musica"] > 0.0


def test_classificador_curto_e_unico_para_modalidade_e_pendencias() -> None:
    casos = {
        "sim": True,
        "confirmo": True,
        "isso": True,
        "pode ser": True,
        "precisa não": False,
        "deixa para depois": False,
        "deixa pra lá": False,
        "obrigado lay": None,
    }

    for texto, esperado in casos.items():
        assert classificar_confirmacao_local(texto) is esperado
        modalidade = classificar_modalidade_turno(
            texto,
            confirmacao_contextual_valida=True,
        )
        if esperado is True:
            assert modalidade["modalidade"] == "confirmacao"
            assert modalidade["autoriza_execucao"] is True
        elif esperado is False:
            assert modalidade["modalidade"] == "recusa"
            assert modalidade["autoriza_execucao"] is False
        else:
            assert modalidade["modalidade"] not in {"confirmacao", "recusa"}


class _MemoriaAprendizadoFake:
    def __init__(self) -> None:
        self.eventos: list[dict] = []

    def registrar_evidencia_aprendizado(self, **dados):
        self.eventos.append(dict(dados))
        return {
            "chave": dados["chave"],
            "confianca": abs(float(dados["sinal"])),
            "status": "candidata",
            "contradicoes": 0,
        }


def test_feedback_contextual_unico_preserva_origem_e_nao_promove_correcao_isolada() -> None:
    memoria = _MemoriaAprendizadoFake()
    motor = MotorAprendizadoRuntime(
        memoria_sqlite=memoria,
        contexto_getter=lambda: {},
        log=lambda *_args: None,
    )

    motor.registrar_feedback_contextual(
        tipo="correcao",
        aceito=False,
        resultado="corrigiu o alvo",
        origem="caixa_entrada",
        confianca=0.9,
        alvo="ideia espacial",
    )

    evento = memoria.eventos[-1]
    assert evento["origem"] == "feedback_contextual:caixa_entrada"
    assert evento["confirmado_usuario"] is False
    assert abs(evento["sinal"]) <= 0.4
    assert evento["contexto"]["confianca_evento"] == 0.9


def test_correcao_e_repeticao_entram_no_motor_com_sinal_fraco() -> None:
    memoria = _MemoriaAprendizadoFake()
    motor = MotorAprendizadoRuntime(
        memoria_sqlite=memoria,
        contexto_getter=lambda: {},
        log=lambda *_args: None,
    )

    motor.observar_interacao(
        "não Lay, eu quis dizer o outro arquivo",
        "Entendi.",
        habilidade="arquivos",
        alvo="nota.txt",
    )
    motor.observar_interacao(
        "tenta de novo",
        "Vou tentar.",
        habilidade="arquivos",
        alvo="nota.txt",
    )

    correcao, repeticao = memoria.eventos[-2:]
    assert correcao["valor"]["evento"] == "correcao"
    assert repeticao["valor"]["evento"] == "repeticao"
    assert correcao["origem"] == repeticao["origem"] == "feedback_contextual:arquivos"
    assert correcao["confirmado_usuario"] is False
    assert repeticao["confirmado_usuario"] is False
    assert abs(correcao["sinal"]) <= 0.4
    assert abs(repeticao["sinal"]) <= 0.4


def test_evento_de_pendencia_nao_agenda_alimenta_motor_compartilhado() -> None:
    memoria = _MemoriaAprendizadoFake()
    motor = MotorAprendizadoRuntime(
        memoria_sqlite=memoria,
        contexto_getter=lambda: {},
        log=lambda *_args: None,
    )

    motor.observar_evento_pendencia(
        "recusar",
        {"origem": "clipboard", "referencia": "resumir_texto"},
    )

    evento = memoria.eventos[-1]
    assert evento["valor"]["evento"] == "recusa"
    assert evento["valor"]["aceito"] is False
    assert evento["origem"] == "feedback_contextual:clipboard"


def test_preferencia_notificacao_persiste_e_publica_contexto_e_aprendizado(
    tmp_path: Path,
) -> None:
    contextos: list[dict] = []
    aprendizados: list[dict] = []
    central = CentralNotificacoesRuntime(
        str(tmp_path / "central.json"),
        contexto_atualizar_cb=lambda **campos: contextos.append(dict(campos)),
        registrar_aprendizado_cb=lambda **dados: aprendizados.append(dict(dados)),
        log=lambda *_args: None,
    )

    ok, _fala = central.definir_preferencia("compras", "silenciar")

    assert ok is True
    publicado = contextos[-1]["preferencias_notificacoes"]
    assert publicado["valores"]["compras"] == "silenciar"
    assert publicado["proveniencia"] == "preferencia_explicita_usuario"
    assert publicado["confianca"] == 1.0
    assert aprendizados[-1]["chave"] == "notificacoes:compras"
    assert aprendizados[-1]["confirmado_usuario"] is True
