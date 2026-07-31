from datetime import datetime

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
        mapa_habilidades_getter=lambda: {
            "catalogadas": 43, "disponiveis": 42, "indisponiveis": 1,
            "observacoes_ativas": 1, "autoriza_execucao": False,
        },
        pesquisa_arquivos_getter=lambda: {
            "arquivos_indexados": 120, "pesquisas": 3, "cache_ativo": True,
            "indice_incompleto": False, "falhas": 0,
            "somente_leitura": True, "envia_conteudo_externo": False,
        },
        mutacoes_arquivos_getter=lambda: {
            "somente_raizes_autorizadas": True,
            "escrita_segura_disponivel": True,
            "lixeira_reversivel": True,
            "confirmacao_exclusao_pendente": False,
        },
        musica_leitura_getter=lambda: {
            "somente_leitura": True, "playlists_usuario": 12,
            "playlists_laylay": 3, "curadoria_usa_historico": True,
            "curadoria_cooperativa": True, "curadoria_falhas": 0,
            "playlist_ativa": True, "estado_disponivel": True,
            "expondo_urls": False,
        },
        fala_operacional_getter=lambda: {
            "tentativas": 3, "emitidas": 2,
            "duplicadas_suprimidas": 1, "reservadas": 0,
            "rejeitadas_voz": 0, "autoriza_execucao": False,
        },
        falar=lambda texto, emocao, nivel: falas.append((texto, emocao, nivel)),
        log=logs.append,
    )

    runtime.mostrar()

    assert "módulos auditados estão saudáveis" in falas[0][0]
    assert "DIAGNÓSTICO:MENTE" in logs[0]
    assert "mapa de habilidades: catalogadas=43" in logs[0]
    assert "pesquisa de arquivos: indexados=120 pesquisas=3" in logs[0]
    assert "somente_leitura=True envio_externo=False" in logs[0]
    assert "mutações de arquivos: raízes_autorizadas=True" in logs[0]
    assert "lixeira_reversível=True confirmação_pendente=False" in logs[0]
    assert "leitura musical: playlists=12" in logs[0]
    assert "curadorias_laylay=3 histórico_na_curadoria=True" in logs[0]
    assert "cooperação=True" in logs[0]
    assert "playlist_ativa=True" in logs[0]
    assert "somente_leitura=True expõe_urls=False" in logs[0]
    assert "voz operacional única: tentativas=3 emitidas=2" in logs[0]
    assert "duplicadas_suprimidas=1" in logs[0]


def test_diagnostico_expoe_so_metricas_seguras_da_rede_associativa():
    diagnostico = construir_diagnostico_mente(
        {"mental": {}, "conversacional": {}, "percepcao": {}, "continuidades": {}},
        {"memoria": {"status": "saudavel"}},
        {
            "modo": "sombra", "influencia_habilitada": False,
            "nos": 12, "conexoes": 18, "ativacoes": 5, "fila": 1,
            "mais_ativos": [{"rotulo": "informação privada"}],
            "metricas": {
                "processados": 9, "duplicados": 3, "falhas": 0,
                "descartados_fila": 2, "comparacoes_sombra": 8,
                "candidatos_sombra": 4,
            },
        },
    )

    assert diagnostico["rede_associativa"] == {
        "modo": "sombra", "influencia_habilitada": False,
        "nos": 12, "conexoes": 18, "ativacoes": 5, "fila": 1,
        "processados": 9, "duplicados": 3, "falhas": 0,
        "descartados_fila": 2, "comparacoes_sombra": 8,
        "candidatos_sombra": 4,
        "feedbacks": 0, "ajustes_plasticidade": 0,
        "sinais_continuidade": 0, "influencias_continuidade": 0,
        "plasticidade_perfis": 0, "plasticidade_amostras": 0,
    }
    texto = formatar_diagnostico_terminal(diagnostico)
    assert "rede associativa: modo=sombra" in texto
    assert "informação privada" not in texto


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


def test_consulta_de_horario_e_prioritaria_e_nao_passsa_pela_ia():
    falas = []
    namespace = {
        "_agora_temporal_cb": lambda: datetime(2026, 7, 22, 22, 47),
        "falar_com_lipsync": lambda *args: falas.append(args),
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )

    assert runtime.processar_prioritarios("que horas são?") is True
    assert falas == [("São 22h47 agora. Já é noite por aqui.", "calma", 1)]


def test_comando_de_governanca_e_prioritario_e_nao_passsa_pela_ia():
    chamadas = []
    namespace = {
        "_detectar_comando_governanca_iniciativa": lambda _texto: {
            "acao": "configurar", "dominio": "iot", "permissao": "sugestao",
        },
        "_processar_governanca_iniciativa": chamadas.append,
    }
    runtime = ComandosImediatosRuntime(
        namespace_getter=lambda: namespace,
        loop_getter=lambda: None,
    )
    assert runtime.processar_prioritarios("permita sugestões de iluminação") is True
    assert chamadas[0]["permissao"] == "sugestao"
