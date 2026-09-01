"""P1-HC6 — Porteiro de produção recebe o owner canônico.

Contrato de composição descoberto pelo RT1-D:

    _prioridade_interacao_usuario_runtime
                  │
                  └── .ativa()
                         ↓
    contexto_getter do PorteiroProatividadeRuntime
                         ↓
    "interacao_usuario_ativa"

Este teste é estrutural de propósito. Ele não substitui o RT1-D:
- HC6 prova a aresta de composição no `laylay.py`;
- RT1-D prova o efeito temporal no root montado.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAYLAY = ROOT / "laylay.py"

OWNER = "_prioridade_interacao_usuario_runtime"
PORTEIRO = "_porteiro_proatividade_runtime"
FACTORY = "_criar_porteiro_proatividade_runtime_mente"


def _arvore() -> ast.Module:
    return ast.parse(
        LAYLAY.read_text(encoding="utf-8"),
        filename=str(LAYLAY),
    )


def _atribuicao_porteiro(arvore: ast.Module) -> ast.Call:
    encontrados: list[ast.Call] = []

    for no in ast.walk(arvore):
        if not isinstance(no, ast.Assign):
            continue
        if not any(
            isinstance(alvo, ast.Name) and alvo.id == PORTEIRO
            for alvo in no.targets
        ):
            continue
        if not isinstance(no.value, ast.Call):
            continue

        func = no.value.func
        nome_factory = func.id if isinstance(func, ast.Name) else ""
        if nome_factory == FACTORY:
            encontrados.append(no.value)

    assert len(encontrados) == 1, (
        f"esperava exatamente uma composição de {PORTEIRO} via {FACTORY}; "
        f"encontrei {len(encontrados)}"
    )
    return encontrados[0]


def _keyword(call: ast.Call, nome: str) -> ast.AST:
    for item in call.keywords:
        if item.arg == nome:
            return item.value
    raise AssertionError(
        f"{PORTEIRO} não recebeu keyword {nome!r}"
    )


def _dict_da_lambda_contexto(call: ast.Call) -> ast.Dict:
    contexto = _keyword(call, "contexto_getter")
    assert isinstance(contexto, ast.Lambda), (
        "contexto_getter do Porteiro precisa continuar sendo a projeção "
        "de contexto composta no root"
    )
    corpo = contexto.body
    assert isinstance(corpo, ast.Dict), (
        "contexto_getter do Porteiro deixou de retornar dict diretamente"
    )
    return corpo


def _valor_chave(dicionario: ast.Dict, chave: str) -> ast.AST:
    for chave_no, valor_no in zip(dicionario.keys, dicionario.values):
        if (
            isinstance(chave_no, ast.Constant)
            and chave_no.value == chave
        ):
            return valor_no
    raise AssertionError(
        f"contexto do Porteiro não publica {chave!r}"
    )


def _eh_owner_ativa(no: ast.AST) -> bool:
    # Aceita:
    #   _prioridade_interacao_usuario_runtime.ativa()
    # ou:
    #   bool(_prioridade_interacao_usuario_runtime.ativa())
    if isinstance(no, ast.Call):
        func = no.func

        if (
            isinstance(func, ast.Attribute)
            and func.attr == "ativa"
            and isinstance(func.value, ast.Name)
            and func.value.id == OWNER
            and not no.args
            and not no.keywords
        ):
            return True

        if (
            isinstance(func, ast.Name)
            and func.id == "bool"
            and len(no.args) == 1
            and not no.keywords
        ):
            return _eh_owner_ativa(no.args[0])

    return False


def test_red_p1hc6_porteiro_publica_interacao_usuario_ativa():
    arvore = _arvore()
    porteiro = _atribuicao_porteiro(arvore)
    contexto = _dict_da_lambda_contexto(porteiro)

    valor = _valor_chave(
        contexto,
        "interacao_usuario_ativa",
    )

    assert _eh_owner_ativa(valor), (
        "P1-HC6 RED: `interacao_usuario_ativa` existe, mas não deriva "
        "diretamente do owner canônico "
        f"{OWNER}.ativa()"
    )


def test_red_p1hc6_nao_usa_sinal_legado_como_substituto_do_owner():
    arvore = _arvore()
    porteiro = _atribuicao_porteiro(arvore)
    contexto = _dict_da_lambda_contexto(porteiro)

    valor = _valor_chave(
        contexto,
        "interacao_usuario_ativa",
    )

    dump = ast.dump(valor, include_attributes=False)

    assert OWNER in dump, (
        "P1-HC6 RED: composição tentou representar ownership com sinal "
        "derivado/legado em vez do owner canônico"
    )
