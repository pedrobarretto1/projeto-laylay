from __future__ import annotations

import threading

import pytest

from mente_laylay.personalidade.orquestrador_fala_runtime import (
    DEPENDENCIAS_ORQUESTRADOR_FALA,
    OrquestradorFalaRuntime,
)


def _servicos_completos() -> dict:
    return {nome: object() for nome in DEPENDENCIAS_ORQUESTRADOR_FALA}


class _EstadoFala:
    def __init__(self, mental: dict) -> None:
        self.mental = dict(mental)

    def substituir(self, dominio: str, valor: dict) -> None:
        assert dominio == "mental"
        self.mental = dict(valor)


class _VozFalsa:
    def __init__(self, retornos=None) -> None:
        self.falas = []
        self.retornos = list(retornos or [True])

    def falar(self, *args, **kwargs):
        self.falas.append((args, kwargs))
        return self.retornos.pop(0) if self.retornos else True


def _runtime_de_fala(*, voz=None, turno_id="turno-1"):
    estado = _EstadoFala({
        "turno_atual": {"id": turno_id},
        "plano_turno_atual": {
            "id": turno_id,
            "fase": "planejado",
            "requer_execucao": True,
            "texto_usuario": "liga a luz",
        },
    })
    voz = voz or _VozFalsa()
    logs = []
    runtime = OrquestradorFalaRuntime(servicos_iniciais={
        "_registrar_mente_curta": lambda *_args, **_kwargs: None,
        "_estado_compartilhado_runtime": estado,
        "_encerrar_topico_mente": lambda mental, conversa, **_kwargs: (mental, conversa),
        "salvar_memoria": lambda: None,
        "print": logs.append,
        "_dirigir_fala_mente": lambda fala, **kwargs: {
            "fala": fala,
            "emocao": kwargs.get("emocao") or "calma",
            "nivel": kwargs.get("nivel") or 1,
        },
        "_voz_runtime": voz,
        "_registrar_continuidade_da_fala_mente": lambda mental, *_args, **_kwargs: mental,
        "_threading": threading,
        "_agendar_fala_proativa": lambda *_args, **_kwargs: False,
    })
    return runtime, estado, voz, logs


def _resultado_luz(*, cor="roxo", confirmado=True):
    return {
        "intent": "IOT_CONTROL",
        "status": "cor_ajustada",
        "alvo": "lampada_quarto",
        "params": {"acao": "ajustar_cor", "cor": cor},
        "confirmado": confirmado,
    }


def test_orquestrador_consulta_namespace_legado_apenas_uma_vez() -> None:
    chamadas = []
    runtime = OrquestradorFalaRuntime(
        lambda: chamadas.append(True) or {"print": object(), "SEGREDO": object()}
    )

    runtime._ns()
    runtime._ns()
    assert chamadas == [True]
    assert runtime.servicos_registrados == ("print",)


def test_conexao_final_valida_filtra_e_congela_servicos() -> None:
    runtime = OrquestradorFalaRuntime(servicos_iniciais={})
    incompletos = _servicos_completos()
    incompletos.pop("_voz_runtime")
    with pytest.raises(RuntimeError, match="_voz_runtime"):
        runtime.conectar_servicos(incompletos)

    servicos = _servicos_completos()
    voz_final = servicos["_voz_runtime"]
    servicos["SEGREDO"] = object()
    runtime.conectar_servicos(servicos)
    servicos["_voz_runtime"] = object()
    servicos["novo"] = object()

    assert runtime._ns()["_voz_runtime"] is voz_final
    assert len(runtime.servicos_registrados) == len(DEPENDENCIAS_ORQUESTRADOR_FALA)
    assert "SEGREDO" not in runtime.servicos_registrados
    assert "novo" not in runtime.servicos_registrados


def test_mesmo_resultado_confirmado_fala_uma_unica_vez_no_turno() -> None:
    runtime, _estado, voz, logs = _runtime_de_fala()
    resultado = _resultado_luz()

    assert runtime.falar_resultado_operacional(
        resultado, "Pronto, deixei a luz roxa.", "debochada", 2,
    ) is True
    assert runtime.falar_resultado_operacional(
        resultado, "A lâmpada ficou roxa, bem bonitinha.", "feliz", 2,
    ) is True

    assert [chamada[0][0] for chamada in voz.falas] == ["Pronto, deixei a luz roxa."]
    assert any("duplicada suprimida" in linha for linha in logs)
    assert runtime.diagnostico()["duplicadas_suprimidas"] == 1


def test_resultados_operacionais_diferentes_preservam_duas_falas() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala()

    runtime.falar_resultado_operacional(_resultado_luz(cor="roxo"), "Ficou roxa.")
    runtime.falar_resultado_operacional(_resultado_luz(cor="azul"), "Agora ficou azul.")

    assert [chamada[0][0] for chamada in voz.falas] == [
        "Ficou roxa.", "Agora ficou azul.",
    ]


def test_novo_turno_pode_confirmar_novamente_o_mesmo_resultado() -> None:
    runtime, estado, voz, _logs = _runtime_de_fala()
    resultado = _resultado_luz()

    runtime.falar_resultado_operacional(resultado, "Ficou roxa.")
    estado.mental["turno_atual"] = {"id": "turno-2"}
    estado.mental["plano_turno_atual"] = {
        "id": "turno-2", "fase": "planejado", "requer_execucao": True,
    }
    runtime.falar_resultado_operacional(resultado, "Ficou roxa de novo.")

    assert [chamada[0][0] for chamada in voz.falas] == [
        "Ficou roxa.", "Ficou roxa de novo.",
    ]


def test_conversa_e_resultado_nao_confirmado_nao_sao_silenciados() -> None:
    runtime, estado, voz, _logs = _runtime_de_fala()
    estado.mental["plano_turno_atual"]["requer_execucao"] = False

    runtime.falar("Eu tô aqui.")
    runtime.falar("Eu tô aqui.")
    runtime.falar_resultado_operacional(
        _resultado_luz(confirmado=False), "A lâmpada não respondeu.",
    )
    runtime.falar_resultado_operacional(
        _resultado_luz(confirmado=False), "Ainda não respondeu.",
    )

    assert len(voz.falas) == 4


def test_rejeicao_da_voz_libera_nova_tentativa_do_resultado() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala(
        voz=_VozFalsa([False, True]),
    )
    resultado = _resultado_luz()

    assert runtime.falar_resultado_operacional(resultado, "Ficou roxa.") is False
    assert runtime.falar_resultado_operacional(resultado, "Ficou roxa.") is True

    assert len(voz.falas) == 2
    diagnostico = runtime.diagnostico()
    assert diagnostico["rejeitadas_voz"] == 1
    assert diagnostico["emitidas"] == 1


def test_observador_recebe_apenas_fala_aceita_pela_fronteira_final() -> None:
    runtime, _estado, _voz, _logs = _runtime_de_fala(
        voz=_VozFalsa([False, True]),
    )
    publicadas = []
    runtime.registrar_observador_fala_final(
        lambda texto, emocao, nivel, **dados: publicadas.append(
            (texto, emocao, nivel, dados),
        )
    )

    assert runtime.falar("candidato recusado") is False
    assert runtime.falar("resposta consolidada", "feliz", 2) is True

    assert publicadas == [
        (
            "resposta consolidada", "feliz", 2,
            {"proativa": False, "mensagem_id": "turno:turno-1"},
        ),
    ]
    assert _voz.falas[-1][1]["_texto_publicado_antecipado"] is True


def test_publicacao_visual_imediata_registra_latencia_sem_esperar_audio() -> None:
    runtime, _estado, voz, _logs = _runtime_de_fala()
    metricas = []
    runtime.conectar_servicos({
        **runtime._servicos,
        "_registrar_metrica_diagnostico": (
            lambda *args, **kwargs: metricas.append((args, kwargs))
        ),
    })
    publicadas = []
    runtime.registrar_observador_fala_final(
        lambda texto, *_args, **_kwargs: publicadas.append(texto) or True
    )

    assert runtime.falar("Resposta pronta.") is True

    assert publicadas == ["Resposta pronta."]
    assert voz.falas[-1][1]["wait"] is False
    assert any(
        args[0] == "tts_texto_visivel" and kwargs["fase"] == "texto_final"
        for args, kwargs in metricas
    )
