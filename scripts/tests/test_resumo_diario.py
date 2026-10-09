from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from mente_laylay.autonomia.finalizacao_execucao_ia import (
    finalizar_execucao_resposta_ia,
)
from mente_laylay.cognicao.estado_tecnico_llm import (
    eh_estado_tecnico_llm,
    estado_bloqueio_orcamento_llm,
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


def test_lote_pendente_recarregado_tenta_novamente_na_proxima_interacao(tmp_path) -> None:
    instantes = [
        datetime(2026, 7, 29, 22, 50),
        datetime(2026, 7, 29, 22, 51),
    ]
    pasta = str(tmp_path)
    memoria_com_falha = MemoriaLaylay(
        pasta_memoria=pasta,
        enviar_mensagem=lambda _mensagens: "LAYLAY_LLM_INDISPONIVEL",
        agora=lambda: instantes[0],
        log=lambda *_: None,
    )
    for indice in range(5):
        memoria_com_falha.adicionar_interacao(f"fala {indice}", f"resposta {indice}")

    memoria_recuperada = MemoriaLaylay(
        pasta_memoria=pasta,
        enviar_mensagem=lambda _mensagens: "Resumo recuperado sem perder o lote.",
        agora=lambda: instantes[1],
        log=lambda *_: None,
    )
    memoria_recuperada.adicionar_interacao("nova fala", "nova resposta")

    conteudo = (tmp_path / "memoria_29-07-2026.txt").read_text(encoding="utf-8")
    assert "Resumo recuperado sem perder o lote." in conteudo
    assert "INTERAÇÕES PENDENTES" not in conteudo
    assert memoria_recuperada.historico_recente == []
    assert memoria_recuperada.contador == 0


@pytest.mark.parametrize(
    "estado_tecnico",
    [
        pytest.param("__LAYLAY_LLM_TIMEOUT__", id="timeout"),
        pytest.param("__LAYLAY_LLM_OCUPADA__", id="ocupada"),
        pytest.param("__LAYLAY_LLM_INDISPONIVEL__", id="indisponivel"),
    ]
    + [
        pytest.param(
            estado_bloqueio_orcamento_llm(motivo),
            id=f"orcamento_{motivo}",
        )
        for motivo in (
            "limite_chamadas",
            "principal_duplicada",
            "reparo_duplicado",
            "prazo_esgotado",
            "turno_obsoleto",
            "turno_finalizado",
            "fatia_secundaria_insuficiente",
            "circuito_aberto",
            "probe_em_andamento",
        )
    ],
)
def test_estado_tecnico_preserva_resumo_lote_arquivo_e_retentativa(
    tmp_path, estado_tecnico: str,
) -> None:
    instante = [datetime(2026, 7, 29, 22, 50)]
    arquivo = tmp_path / "memoria_29-07-2026.txt"
    resumo_anterior = "O usuário conversou com a Laylay sobre música."
    resumo_recuperado = "O usuário conversou sobre música e organizou suas anotações."
    chamadas = []
    antes_da_falha = {}

    def resumir(mensagens):
        chamadas.append(mensagens)
        if len(chamadas) == 1:
            return resumo_anterior
        if len(chamadas) == 2:
            antes_da_falha.update(
                resumo=memoria.resumo_do_dia,
                lote=tuple(memoria.historico_recente),
                contador=memoria.contador,
                conteudo=arquivo.read_bytes(),
            )
            return estado_tecnico
        return resumo_recuperado

    memoria = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=resumir,
        agora=lambda: instante[0],
        log=lambda *_: None,
    )
    for indice in range(5):
        memoria.adicionar_interacao(f"conversa inicial {indice}", f"resposta inicial {indice}")
    assert len(chamadas) == 1
    assert memoria.resumo_do_dia == resumo_anterior

    instante[0] += timedelta(seconds=31)
    for indice in range(5):
        memoria.adicionar_interacao(f"anotação pendente {indice}", f"resposta pendente {indice}")

    assert len(chamadas) == 2
    assert eh_estado_tecnico_llm(estado_tecnico)
    assert antes_da_falha["contador"] == 5
    assert memoria.resumo_do_dia == antes_da_falha["resumo"]
    assert tuple(memoria.historico_recente) == antes_da_falha["lote"]
    assert memoria.contador == antes_da_falha["contador"]
    assert arquivo.read_bytes() == antes_da_falha["conteudo"]

    recarregada = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=resumir,
        agora=lambda: instante[0],
        log=lambda *_: None,
    )
    assert recarregada.resumo_do_dia == antes_da_falha["resumo"]
    assert tuple(recarregada.historico_recente) == antes_da_falha["lote"]
    assert recarregada.contador == antes_da_falha["contador"]

    instante[0] += timedelta(seconds=29)
    memoria.atualizar_resumo_diario()
    assert len(chamadas) == 2
    assert arquivo.read_bytes() == antes_da_falha["conteudo"]

    instante[0] += timedelta(seconds=1)
    memoria.atualizar_resumo_diario()
    assert len(chamadas) == 3
    assert resumo_anterior in chamadas[-1][0]["content"]
    assert all(linha in chamadas[-1][0]["content"] for linha in antes_da_falha["lote"])
    assert memoria.resumo_do_dia == resumo_recuperado
    assert memoria.historico_recente == []
    assert memoria.contador == 0
    assert resumo_recuperado in arquivo.read_text(encoding="utf-8")
    assert "INTERAÇÕES PENDENTES" not in arquivo.read_text(encoding="utf-8")


def test_resumo_legitimo_que_menciona_timeout_e_consolidado(tmp_path) -> None:
    resumo = "O usuário relatou um timeout ao pesquisar e depois organizou suas anotações."
    assert not eh_estado_tecnico_llm(resumo)
    memoria = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=lambda _mensagens: resumo,
        agora=lambda: datetime(2026, 7, 29, 22, 50),
        log=lambda *_: None,
    )
    for indice in range(5):
        memoria.adicionar_interacao(f"anotação {indice}", f"resposta {indice}")

    assert memoria.resumo_do_dia == resumo
    assert memoria.historico_recente == []
    assert memoria.contador == 0
    conteudo = (tmp_path / "memoria_29-07-2026.txt").read_text(encoding="utf-8")
    assert resumo in conteudo
    assert "INTERAÇÕES PENDENTES" not in conteudo


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


def test_finalizacao_limpa_nao_imprime_a_mesma_fala_crua(capsys) -> None:
    falas = []
    finalizar_execucao_resposta_ia(
        {
            "messages": [{"role": "user", "content": "oi"}],
            "current_emotion": "calma",
            "emotion_level": 1,
            "enviar_mensagem": lambda *_args, **_kwargs: "",
            "limpar_resposta_da_ia": lambda texto: (texto, []),
            "falar_com_lipsync": lambda fala, *_args: falas.append(fala) or True,
            "verificar_fala_turno": lambda fala, **_kwargs: {
                "aceita": True, "fala": fala,
            },
            "_falhas_consecutivas": {},
            "log_verbose": False,
        },
        [], [], "Oi, tô aqui.", False, False, False,
    )

    assert falas == ["Oi, tô aqui."]
    assert "Laylay: Oi, tô aqui." not in capsys.readouterr().out
