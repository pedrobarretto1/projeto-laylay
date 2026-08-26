from __future__ import annotations

from mente_laylay.integracao.politicas_composicao import (
    aprender_conteudo_area_transferencia,
    aprender_pesquisa_semantica_arquivos,
    construir_estado_visual,
    recomendar_playlist_real_para_presenca,
    registrar_feedback_agenda,
)


def test_estado_visual_prioriza_falha_recente_confirmada():
    estado = {
        "audio_playing": False,
        "is_speaking": False,
        "visual_activity": "idle",
        "visual_activity_until": 0.0,
        "current_emotion": "irritada",
        "emotion_level": 2,
    }
    visual = construir_estado_visual(
        conversa_get=lambda chave, padrao=None: estado.get(chave, padrao),
        plano_get=lambda: {
            "id": "turno-1",
            "atualizado_ts": 99.0,
            "fase": "executado",
            "comandos": [{"status": "indisponivel", "confirmado": False}],
        },
        time_fn=lambda: 100.0,
    )

    assert visual["activity"] == "error"
    assert visual["reaction_id"] == "erro:turno-1"
    assert visual["emotion"] == "irritada"


def test_recomendacao_de_presenca_usa_apenas_playlist_existente():
    fala = recomendar_playlist_real_para_presenca(
        "calmo",
        carregar_playlists=lambda: {"Brisa da madrugada": [], "Rock": []},
    )

    assert "Brisa da madrugada" in fala
    assert "Rock" not in fala


def test_aprendizado_de_busca_guarda_assunto_agregado_sem_resultado_bruto():
    chamadas = []
    ok = aprender_pesquisa_semantica_arquivos(
        "encontra arquivos sobre controlador lampada",
        [{"caminho": "segredo/controlador.py", "trecho": "token"}],
        normalizar=lambda texto: texto.casefold(),
        registrar_evidencia=lambda **dados: chamadas.append(dados) or dados,
    )

    assert ok is True
    assert chamadas[0]["valor"]["descricao_humana"] == (
        "costuma procurar arquivos sobre controlador lampada"
    )
    assert "segredo" not in str(chamadas[0])


def test_clipboard_explicito_e_feedback_agenda_preservam_seus_contratos():
    aprendizados = []
    evidencias = []

    assert aprender_conteudo_area_transferencia(
        "  prefiro luz roxa  ",
        "aprende isso",
        salvar_aprendizado=lambda **dados: aprendizados.append(dados) or True,
    ) is True
    registrar_feedback_agenda(
        "recusa",
        {"intent": "AGENDAR_LEMBRETE"},
        registrar_evidencia=lambda **dados: evidencias.append(dados),
    )

    assert aprendizados[0]["valor"] == "prefiro luz roxa"
    assert aprendizados[0]["confirmado_usuario"] is True
    assert evidencias[0]["sinal"] < 0
    assert evidencias[0]["confirmado_usuario"] is True
