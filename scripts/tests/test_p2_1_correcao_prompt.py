from __future__ import annotations

import asyncio
from datetime import datetime

from mente_laylay.cognicao.resumo_conteudo import resumir_pagina_ou_video
from mente_laylay.integracao.preparacao_llm import preparar_payload_llm
from mente_laylay.memoria_mental.contexto_integrado import (
    compactar_contexto_integrado_para_prompt,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    EstadoCompartilhadoRuntime,
)
from mente_laylay.memoria_mental.resumo_diario import MemoriaLaylay
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT


def _chars(payload: dict) -> int:
    return sum(
        len(str(item.get("content") or ""))
        for item in payload.get("messages", [])
        if isinstance(item, dict)
    )


def test_retrato_mental_e_reduzido_por_relevancia_antes_do_transporte() -> None:
    linhas = ["--- MENTE INTEGRADA ---"]
    linhas.extend(f"Regra genérica repetida {indice}: " + "x" * 180 for indice in range(30))
    linhas.extend([
        "PLANO ÚNICO DESTE TURNO: dominio=conversa | requer_execucao=False",
        "RETRATO CONGELADO DESTE TURNO: referência=opera:Opera",
        "Turno atual: modalidade=pergunta | autoriza_execucao=False",
        "Contexto selecionado pelo filtro: usuário perguntou sobre Opera",
    ])

    reduzido = compactar_contexto_integrado_para_prompt(
        "\n".join(linhas), texto_usuario="o Opera está aberto?", limite_chars=1800,
    )

    assert len(reduzido) <= 1800
    assert "PLANO ÚNICO DESTE TURNO" in reduzido
    assert "referência=opera:Opera" in reduzido
    assert "autoriza_execucao=False" in reduzido
    assert "usuário perguntou sobre Opera" in reduzido


def test_historico_principal_preserva_turnos_recentes_inteiros_com_orcamento() -> None:
    mensagens = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]
    for indice in range(12):
        mensagens.extend([
            {"role": "user", "content": f"pergunta-{indice}-" + "u" * 250},
            {"role": "assistant", "content": f"resposta-{indice}-" + "a" * 250},
        ])

    payload = preparar_payload_llm(
        mensagens,
        model="teste",
        max_tokens=384,
        modo_rapido=False,
        otimizacao_prompt_ativa=True,
    )
    conteudos = [str(item["content"]) for item in payload["messages"]]

    assert "pergunta-0-" not in "\n".join(conteudos)
    assert mensagens[-1]["content"] in conteudos
    assert all(not texto.endswith("…") for texto in conteudos)
    assert _chars(payload) < len(BASE_SYSTEM_PROMPT) + 3000


def test_memoria_do_dia_recupera_interacoes_ainda_nao_consolidadas(tmp_path) -> None:
    memoria = MemoriaLaylay(
        pasta_memoria=str(tmp_path),
        enviar_mensagem=lambda _mensagens: "",
        agora=lambda: datetime(2026, 8, 10, 9, 30),
        log=lambda *_args: None,
    )
    memoria.adicionar_interacao("Hoje comecei a otimizar a Laylay.", "Vamos medir primeiro.")

    contexto = memoria.contexto_do_dia_para_prompt()

    assert "Interações recentes ainda não consolidadas" in contexto
    assert "Hoje comecei a otimizar a Laylay" in contexto
    assert "Vamos medir primeiro" in contexto


def test_resumo_de_pagina_usa_perfil_longo_e_proibe_fala_meta() -> None:
    chamadas: list[dict] = []
    falas: list[str] = []

    def enviar(mensagens, **opcoes):
        chamadas.append({"mensagens": mensagens, "opcoes": opcoes})
        return (
            "A página apresenta a história da China desde os registros da dinastia Shang. "
            "Também destaca o desenvolvimento no vale do rio Amarelo."
        )

    resultado = asyncio.run(resumir_pagina_ou_video(
        websocket_disponivel=lambda: True,
        solicitar_conteudo=lambda: asyncio.sleep(0, result={
            "success": True,
            "data": {
                "url": "https://pt.wikipedia.org/wiki/História_da_China",
                "title": "História da China",
                "content": (
                    "Os primeiros registros escritos pertencem à dinastia Shang. "
                    "A civilização se desenvolveu no vale do rio Amarelo."
                ),
            },
        }),
        falar=lambda fala, *_args: falas.append(fala),
        enviar_mensagem=enviar,
        limpar_resposta=lambda texto: texto,
        remover_prefixo_exec=lambda texto: texto,
        transcript_api=object(),
        log=lambda *_args: None,
    ))

    assert resultado is True
    assert chamadas[0]["opcoes"]["modo_rapido"] is False
    prompt = chamadas[0]["mensagens"][0]["content"]
    assert "Não use saudações" in prompt
    assert falas[-1].startswith("A página apresenta")


def test_pendencia_canonica_legada_invalida_e_normalizada_sem_apagar_valida() -> None:
    runtime = EstadoCompartilhadoRuntime(mental={"pendencia_acao_canonica": None})
    assert "mental.pendencia_acao_canonica" not in runtime.validar_estrutura()["invalidos"]
    assert runtime.mental["pendencia_acao_canonica"] == {}

    valida = {"id": "abc", "acao": "investigar_erro"}
    runtime.substituir("mental", {"pendencia_acao_canonica": valida})
    assert dict(runtime.mental["pendencia_acao_canonica"]) == valida
