from mente_laylay.autonomia.comandos_imediatos import ComandosImediatosRuntime
from mente_laylay.memoria_mental.diagnostico_mente import (
    DiagnosticoMenteRuntime,
    construir_diagnostico_mente,
    detectar_pedido_diagnostico_mente,
    formatar_diagnostico_terminal,
)


def test_detector_exige_pedido_interno_explicito():
    assert detectar_pedido_diagnostico_mente("mostra o diagnóstico da mente")
    assert detectar_pedido_diagnostico_mente("/diagnostico")
    assert detectar_pedido_diagnostico_mente("qual o status interno da Laylay?")
    assert not detectar_pedido_diagnostico_mente("como você se sente dentro do PC?")
    assert not detectar_pedido_diagnostico_mente("recebi um diagnóstico médico")


def test_snapshot_resume_estado_sem_expor_historico_ou_segredos():
    estado = {
        "mental": {
            "ultima_acao_intent": "IOT_CONTROL",
            "ultima_acao_alvo": "lampada_quarto",
            "ultima_acao_status": "sucesso",
            "ultima_acao_confirmada": True,
            "segredo": "não pode sair",
        },
        "conversacional": {
            "current_emotion": "calma",
            "emotion_level": 1,
            "is_speaking": False,
            "audio_playing": False,
        },
        "percepcao": {
            "contexto_sistema": {"title": "Visual Studio Code", "exe": "Code.exe"},
            "aba_ativa": {"url": "https://example.test"},
        },
        "continuidades": {"comando_sugerido_estado": "NONE", "comando_pendente": None},
        "memoria_conversa": {"messages": [{"content": "privado"}]},
    }
    diagnostico = construir_diagnostico_mente(
        estado,
        {"voz": {"status": "saudavel"}, "iot": {"status": "degradado", "ausentes": ["chave"]}},
    )

    assert diagnostico["ultima_acao"]["confirmado"] is True
    assert diagnostico["percepcao"]["janela"] == "Visual Studio Code"
    assert diagnostico["saude"]["degradado"] == 1
    texto = formatar_diagnostico_terminal(diagnostico)
    assert "iot=degradado" in texto
    assert "privado" not in texto
    assert "não pode sair" not in texto


def test_runtime_fala_resumo_e_imprime_detalhes():
    falas, logs = [], []
    runtime = DiagnosticoMenteRuntime(
        estado_getter=lambda: {"mental": {}, "conversacional": {}, "percepcao": {}, "continuidades": {}},
        saude_getter=lambda: {"voz": {"status": "saudavel"}},
        falar=lambda texto, emocao, nivel: falas.append((texto, emocao, nivel)),
        log=logs.append,
    )

    runtime.mostrar()

    assert "módulos auditados estão saudáveis" in falas[0][0]
    assert "DIAGNÓSTICO:MENTE" in logs[0]


def test_comando_prioritario_nao_passsa_pela_ia():
    chamadas = []
    namespace = {
        "_detectar_pedido_diagnostico_mente": detectar_pedido_diagnostico_mente,
        "_mostrar_diagnostico_mente": lambda: chamadas.append("diagnostico"),
        "detectar_comando_saude": lambda _texto: False,
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("mostra o diagnóstico da mente") is True
    assert chamadas == ["diagnostico"]
