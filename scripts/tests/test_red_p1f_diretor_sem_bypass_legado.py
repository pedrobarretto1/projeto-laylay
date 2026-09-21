"""P1-F RED — o Diretor não possui modo alternativo de fala sem cognição."""

from __future__ import annotations

import inspect
from typing import Any

from mente_laylay.autonomia.diretor_presenca import (
    DiretorPresencaRuntime,
    decisao_presenca_aceita_para_entrega,
)


def test_red_p1f_diretor_sem_cognicao_falha_fechado_e_nao_emite() -> None:
    estado: dict[str, Any] = {}
    falas: list[str] = []
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
        processar_evento_cognitivo=lambda evento: dict(evento),
        processar_proposta_comunicativa=lambda _turno, **_contexto: {},
        clock=lambda: 1000.0,
        log=lambda _texto: None,
    )
    # Falsificação explícita: mesmo uma porta legada injetada depois da
    # construção não pode criar um segundo caminho de emissão.
    runtime.emitir_fala = lambda texto, *_args, **_kwargs: falas.append(texto) or True
    runtime.processar_evento_cognitivo = None

    resultado = runtime.considerar({
        "origem": "observador_jogo",
        "dominio": "jogo",
        "categoria": "celebracao",
        "fala": "Essa fala pré-escrita não pode contornar a cognição.",
        "confianca": 0.96,
        "momento_seguro": True,
        "motivo": "vitória observada",
        "evidencias": ["tela de vitória"],
        "chave": "sem-cognicao-sem-bypass",
    })

    assert resultado == {
        "status": "nao_processada",
        "motivo": "cognicao_evento_indisponivel",
        "categoria": "celebracao",
        "ts": 1000.0,
    }
    assert falas == []
    assert estado["contadores"]["emitidas"] == 0
    assert estado["ultima_emissao"] == {}


def test_red_p1f_contrato_publico_nao_oferece_injecao_direta_de_voz() -> None:
    parametros = inspect.signature(DiretorPresencaRuntime).parameters

    assert "processar_evento_cognitivo" in parametros
    assert "emitir_fala" not in parametros


def test_red_p1f_recibo_legado_emitida_nao_e_aceito_como_entrega_canonica() -> None:
    assert decisao_presenca_aceita_para_entrega({"status": "emitida"}) is False
