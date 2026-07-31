from __future__ import annotations

from datetime import datetime

from mente_laylay.autonomia.finalizacao_execucao_ia import (
    finalizar_execucao_resposta_ia,
)
from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay


def test_primeira_conversa_cria_arquivo_e_sobrevive_ao_reinicio(tmp_path) -> None:
    agora = lambda: datetime(2026, 7, 29, 22, 40)
    memoria = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=lambda _mensagens: "não deveria resumir ainda",
        agora=agora,
        log=lambda *_: None,
    )

    memoria.adicionar_interacao("oi lay", "Oi! Tudo bem?")

    arquivo = tmp_path / "memoria_29-07-2026.txt"
    assert arquivo.exists()
    assert "INTERAÇÕES PENDENTES DE CONSOLIDAÇÃO" in arquivo.read_text(encoding="utf-8")

    recarregada = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=lambda _mensagens: "resumo restaurado",
        agora=agora,
        log=lambda *_: None,
    )
    assert recarregada.contador == 1
    assert "Usuário: oi lay" in recarregada.historico_recente[0]


def test_quinto_turno_consolida_resumo_sem_manter_transcricao(tmp_path) -> None:
    memoria = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=lambda _mensagens: "O usuário conversou com a Laylay sobre música.",
        agora=lambda: datetime(2026, 7, 29, 22, 45),
        log=lambda *_: None,
    )

    for indice in range(5):
        memoria.adicionar_interacao(f"fala {indice}", f"resposta {indice}")

    conteudo = (tmp_path / "memoria_29-07-2026.txt").read_text(encoding="utf-8")
    assert "O usuário conversou com a Laylay sobre música." in conteudo
    assert "INTERAÇÕES PENDENTES" not in conteudo
    assert memoria.historico_recente == []


def test_falha_da_llm_preserva_lote_para_tentar_depois(tmp_path) -> None:
    def falhar(_mensagens):
        raise TimeoutError("modelo ocupado")

    memoria = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=falhar,
        agora=lambda: datetime(2026, 7, 29, 22, 50),
        log=lambda *_: None,
    )

    for indice in range(5):
        memoria.adicionar_interacao(f"fala {indice}", f"resposta {indice}")

    conteudo = (tmp_path / "memoria_29-07-2026.txt").read_text(encoding="utf-8")
    assert "INTERAÇÕES PENDENTES DE CONSOLIDAÇÃO" in conteudo
    assert len(memoria.historico_recente) == 5


def test_conversa_normal_finalizada_entra_na_memoria_diaria() -> None:
    registros = []
    mensagens = [{"role": "user", "content": "como foi seu dia?"}]

    class MemoriaFalsa:
        def adicionar_interacao(self, usuario, fala):
            registros.append((usuario, fala))

    finalizar_execucao_resposta_ia(
        {
            "messages": mensagens,
            "current_emotion": "calma",
            "emotion_level": 1,
            "enviar_mensagem": lambda *_args, **_kwargs: "",
            "limpar_resposta_da_ia": lambda texto: (texto, []),
            "falar_com_lipsync": lambda *_args, **_kwargs: True,
            "verificar_fala_turno": lambda fala, **_kwargs: {
                "aceita": True,
                "fala": fala,
            },
            "memoria_inteligente": MemoriaFalsa(),
            "_falhas_consecutivas": {},
        },
        [],
        [],
        "Foi tranquilo. E o seu?",
        False,
        False,
        False,
    )

    assert registros == [("como foi seu dia?", "Foi tranquilo. E o seu?")]
