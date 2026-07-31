from mente_laylay.personalidade.terminal_laylay import should_log_message


def test_modo_essencial_exibe_diagnostico_e_transcricao_de_voz():
    assert should_log_message("🗣️ [VOCÊ DISSE] Lay, liga a luz", log_mode="essencial")
    assert should_log_message(
        "🎙️ [OUVIDO:LEITURA] original='Lay, liga a luz'",
        log_mode="limpo",
    )
    assert should_log_message(
        "🎙️ [OUVIDO:NÍVEL] calibrado ruído=0.0020",
        log_mode="essencial",
    )
    assert should_log_message(
        "🧠 [REDE ASSOCIATIVA] modo=sombra | influência=desativada",
        log_mode="limpo",
    )
    assert should_log_message(
        "📋 [CLIPBOARD:INÍCIO] serviço=ativo modo=sugestao",
        log_mode="limpo",
    )
