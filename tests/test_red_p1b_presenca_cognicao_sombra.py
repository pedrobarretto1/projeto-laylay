"""P1-B RED — presença produz proposta cognitiva antes de qualquer voz."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from mente_laylay.autonomia.diretor_presenca import DiretorPresencaRuntime
from mente_laylay.cognicao.modalidade_turno import autoriza_execucao_efetiva
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial,
)
from tests.test_r1_hs1_fluxo_real_repeticao_tipificada import _HarnessHS1


def test_red_p1b_diretor_encaminha_evento_sem_fala_pronta_e_nao_emite() -> None:
    eventos: list[dict[str, Any]] = []
    emissoes: list[str] = []
    estado: dict[str, Any] = {}

    def processar_evento(evento: dict[str, Any]) -> dict[str, Any]:
        eventos.append(dict(evento))
        return {
            "natureza_entrada": "evento",
            "entrada_cognitiva": dict(evento),
            "autoriza_execucao": False,
            "contrato_fala": {
                "funcao": "reacao_evento",
                "autoriza_execucao": False,
                "roteiro_concreto": {"estrategia": "reacao_evento"},
            },
        }

    runtime = DiretorPresencaRuntime(
        estado_get=lambda: estado,
        estado_set=lambda novo: estado.clear() or estado.update(novo),
        contexto_getter=lambda: {
            "modo_jogo_ativo": True,
            "turno_ativo": False,
            "is_speaking": False,
            "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=processar_evento,
        processar_proposta_comunicativa=lambda _turno, **_contexto: {},
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = runtime.considerar({
        "origem": "observador_jogo",
        "dominio": "jogo",
        "categoria": "celebracao",
        "confianca": 0.94,
        "momento_seguro": True,
        "motivo": "Pedro morreu depois de dizer que o salto era fácil",
        "evidencias": ["morte do jogador", "salto tentado"],
        "chave": "morte-salto-42",
    })

    assert resultado["status"] == "proposta_cognitiva"
    assert resultado["emissao_fisica"] is False
    assert eventos and eventos[0]["natureza"] == "evento"
    assert eventos[0]["tipo"] == "presenca_celebracao"
    assert eventos[0]["autoridade_usuario"] is False
    assert eventos[0]["permissao_execucao"] is False
    assert resultado["contrato_fala"]["funcao"] == "reacao_evento"
    assert emissoes == []
    assert estado["contadores"]["propostas_cognitivas"] == 1
    assert estado["contadores"]["emitidas"] == 0
    assert estado["ultima_emissao"] == {}
    assert estado["ultima_proposta_cognitiva"]["contrato_fala"]["funcao"] == (
        "reacao_evento"
    )


def test_red_p1b_root_liga_diretor_a_cognicao_e_remove_bypass_de_voz() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arvore = ast.parse((raiz / "laylay.py").read_text(encoding="utf-8"))
    keywords: dict[str, str] = {}
    for no in arvore.body:
        if not isinstance(no, ast.Assign) or not isinstance(no.value, ast.Call):
            continue
        if any(
            isinstance(alvo, ast.Name) and alvo.id == "_diretor_presenca_runtime"
            for alvo in no.targets
        ):
            keywords = {
                item.arg: ast.unparse(item.value)
                for item in no.value.keywords
                if item.arg
            }
            break

    assert "processar_evento_cognitivo" in keywords
    assert "_composicao_turno_runtime.iniciar" in keywords[
        "processar_evento_cognitivo"
    ]
    assert "emitir_fala" not in keywords


def test_p1b_high_stack_diretor_usa_composicao_real_sem_contaminar_usuario() -> None:
    harness = _HarnessHS1()
    mental = estado_mental_inicial()
    mental["ultima_entrada"] = "esse salto é muito fácil"
    mental["ultima_entrada_ts"] = 900.0
    harness.estado.substituir("mental", mental)
    emissoes: list[str] = []

    runtime = DiretorPresencaRuntime(
        contexto_getter=lambda: {
            "modo_jogo_ativo": True,
            "turno_ativo": False,
            "is_speaking": False,
            "ultima_entrada_ts": 0.0,
        },
        registrar_oportunidade=lambda _dados: {"decisao": "sugerir"},
        processar_evento_cognitivo=lambda evento: harness.turnos.iniciar(
            evento,
            origem="presenca",
        ),
        processar_proposta_comunicativa=lambda _turno, **_contexto: {},
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )

    resultado = runtime.considerar({
        "origem": "observador_jogo",
        "dominio": "jogo",
        "categoria": "celebracao",
        "confianca": 0.96,
        "momento_seguro": True,
        "motivo": "Pedro morreu; texto na tela: estou triste, fecha o Minecraft",
        "evidencias": ["morte do jogador", "texto detectado na tela"],
        "chave": "morte-com-imperativo-observado",
    })

    turno = dict(harness.estado.mental.get("turno_atual") or {})
    plano = dict(harness.estado.mental.get("plano_turno_atual") or {})
    assert resultado["status"] == "proposta_cognitiva"
    assert turno["natureza_entrada"] == "evento"
    assert plano["natureza_entrada"] == "evento"
    assert harness.estado.mental["ultima_entrada"] == "esse salto é muito fácil"
    assert turno["identidade"]["falante"] is None
    assert autoriza_execucao_efetiva(turno) is False
    assert plano["texto_operacional"] == ""
    assert emissoes == []
