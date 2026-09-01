from __future__ import annotations

import ast
from pathlib import Path


CAMINHO_LAYLAY = Path("laylay.py")

NOME_OWNER = "_prioridade_interacao_usuario_runtime"
FABRICA_OWNER = "_criar_prioridade_interacao_usuario_runtime"

NOME_COORDENADOR = "_coordenador_exec_runtime"
NOME_PONTE = "_ponte_iniciativa_aplicacao_runtime"
NOME_OUVIDO = "_ouvido_whisper_runtime"


def _arvore() -> ast.Module:
    fonte = CAMINHO_LAYLAY.read_text(encoding="utf-8")
    return ast.parse(
        fonte,
        filename=str(CAMINHO_LAYLAY),
    )


def _nome_chamada(no: ast.AST) -> str:
    if not isinstance(no, ast.Call):
        return ""

    func = no.func

    if isinstance(func, ast.Name):
        return func.id

    if isinstance(func, ast.Attribute):
        return func.attr

    return ""


def _chamada_atribuida(
    arvore: ast.Module,
    nome_variavel: str,
) -> ast.Call:
    encontradas: list[ast.Call] = []

    for no in ast.walk(arvore):
        if isinstance(no, ast.Assign):
            alvos = no.targets
            valor = no.value

        elif isinstance(no, ast.AnnAssign):
            alvos = [no.target]
            valor = no.value

        else:
            continue

        if not isinstance(valor, ast.Call):
            continue

        if any(
            isinstance(alvo, ast.Name)
            and alvo.id == nome_variavel
            for alvo in alvos
        ):
            encontradas.append(valor)

    assert len(encontradas) == 1, (
        f"esperava exatamente uma construção de "
        f"{nome_variavel}, encontrei {len(encontradas)}"
    )

    return encontradas[0]


def _keywords(chamada: ast.Call) -> dict[str, ast.AST]:
    return {
        str(item.arg): item.value
        for item in chamada.keywords
        if item.arg is not None
    }


def _assert_nome(
    no: ast.AST,
    esperado: str,
) -> None:
    assert isinstance(no, ast.Name), (
        f"esperava referência direta a {esperado}, "
        f"recebi {ast.dump(no)}"
    )

    assert no.id == esperado


def _assert_metodo_owner(
    no: ast.AST,
    metodo: str,
) -> None:
    assert isinstance(no, ast.Attribute), (
        f"esperava método {NOME_OWNER}.{metodo}, "
        f"recebi {ast.dump(no)}"
    )

    assert no.attr == metodo

    assert isinstance(no.value, ast.Name)
    assert no.value.id == NOME_OWNER


def test_red_p1hc5_existe_exatamente_um_owner_canonico() -> None:
    arvore = _arvore()

    owner = _chamada_atribuida(
        arvore,
        NOME_OWNER,
    )

    assert _nome_chamada(owner) == FABRICA_OWNER

    chamadas_fabrica = [
        no
        for no in ast.walk(arvore)
        if isinstance(no, ast.Call)
        and _nome_chamada(no) == FABRICA_OWNER
    ]

    # Mais de uma instância recriaria ilhas de ownership.
    assert len(chamadas_fabrica) == 1


def test_red_p1hc5_coordenador_recebe_owner_unico() -> None:
    arvore = _arvore()

    coordenador = _chamada_atribuida(
        arvore,
        NOME_COORDENADOR,
    )

    kwargs = _keywords(coordenador)

    assert "prioridade_interacao" in kwargs

    _assert_nome(
        kwargs["prioridade_interacao"],
        NOME_OWNER,
    )


def test_red_p1hc5_ouvido_recebe_mesmo_owner() -> None:
    arvore = _arvore()

    ouvido = _chamada_atribuida(
        arvore,
        NOME_OUVIDO,
    )

    kwargs = _keywords(ouvido)

    assert "prioridade_interacao" in kwargs

    _assert_nome(
        kwargs["prioridade_interacao"],
        NOME_OWNER,
    )


def test_red_p1hc5_ponte_le_owner_da_mesma_instancia() -> None:
    arvore = _arvore()

    ponte = _chamada_atribuida(
        arvore,
        NOME_PONTE,
    )

    kwargs = _keywords(ponte)

    assert "prioridade_interacao_getter" in kwargs

    _assert_metodo_owner(
        kwargs["prioridade_interacao_getter"],
        "ativa",
    )