#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona APENAS o regressivo R1-C3 de EMAIL_READ(urgentes=True)
ao teste do candidato R1-V2. Não altera produção.

Uso:
    python .\\adicionar_regressivo_r1_v2_email_urgentes.py
    python .\\adicionar_regressivo_r1_v2_email_urgentes.py --reverter
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

ARQ = Path("tests/test_r1_v2_fail_closed_repeticao_tipificada.py")
MARCADOR_ARQUIVO = 'ROOT_R1_V2_FAIL_CLOSED_TIPADO_20260826'
MARCADOR_TESTE = 'ROOT_R1_V2_EMAIL_URGENTES_C3_20260826'
BLOCO = '\n\n# ROOT_R1_V2_EMAIL_URGENTES_C3_20260826\ndef test_c_email_read_urgentes_preserva_parametros_tipados_apos_iot() -> None:\n    estado = _registrar(\n        estado_mental_inicial(),\n        intent="EMAIL_READ",\n        params={"urgentes": True},\n        status="executado",\n        executou=True,\n        confirmado=True,\n        texto="Leia meus emails urgentes.",\n    )\n    estado = _registrar(\n        estado,\n        intent="IOT_CONTROL",\n        params={"acao": "ligar", "alvo": "lampada_quarto"},\n        status="ligado",\n        executou=True,\n        confirmado=True,\n        texto="Liga a lâmpada.",\n    )\n\n    turno, consulta = _aplicar(\n        estado,\n        "Leia de novo.",\n    )\n\n    assert consulta["classificacao"]["tipo"] == "tipada"\n    assert consulta["classificacao"]["acao_semantica"] == "LER"\n    assert consulta["repeticao"] == {\n        "intent": "EMAIL_READ",\n        "params": {"urgentes": True},\n    }\n    assert turno_tem_veto_execucao(turno) is False\n    assert autoriza_execucao_efetiva(turno) is True\n    assert turno["repeticao_operacional"] == {\n        "intent": "EMAIL_READ",\n        "params": {"urgentes": True},\n    }\n'


class Erro(RuntimeError):
    pass


def localizar_repo() -> Path:
    candidatos = [Path.cwd().resolve(), Path(__file__).resolve().parent]
    vistos = set()
    for origem in candidatos:
        for pasta in (origem, *origem.parents):
            if pasta in vistos:
                continue
            vistos.add(pasta)
            if (pasta / ".git").exists() and (pasta / "laylay.py").is_file():
                return pasta
    raise Erro("Não encontrei a raiz da Laylay.")


def validar(path: Path) -> None:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def aplicar(repo: Path) -> None:
    path = repo / ARQ
    if not path.is_file():
        raise Erro(f"teste R1-V2 ausente: {ARQ}")

    texto = path.read_text(encoding="utf-8")
    if MARCADOR_ARQUIVO not in texto:
        raise Erro(
            "o arquivo não parece ser o teste R1-V2 esperado; "
            "não vou modificar."
        )
    if MARCADOR_TESTE in texto:
        raise Erro("o regressivo EMAIL_READ(urgentes=True) já está presente.")

    novo = texto.rstrip() + BLOCO + "\n"
    ast.parse(novo, filename=str(path))
    path.write_text(novo, encoding="utf-8")
    validar(path)

    print("✅ REGRESSIVO R1-C3 ADICIONADO")
    print(f"arquivo: {ARQ}")
    print("produção alterada: NÃO")
    print()
    print("Rode:")
    print(
        r"python -m pytest .\tests\test_r1_v2_fail_closed_repeticao_tipificada.py -vv"
    )


def reverter(repo: Path) -> None:
    path = repo / ARQ
    if not path.is_file():
        raise Erro(f"teste R1-V2 ausente: {ARQ}")

    texto = path.read_text(encoding="utf-8")
    if MARCADOR_TESTE not in texto:
        raise Erro("o regressivo não está presente.")

    if BLOCO not in texto:
        raise Erro(
            "o bloco atual divergiu do bloco original; "
            "não vou remover automaticamente."
        )

    novo = texto.replace(BLOCO, "", 1).rstrip() + "\n"
    ast.parse(novo, filename=str(path))
    path.write_text(novo, encoding="utf-8")
    validar(path)

    print("✅ REGRESSIVO R1-C3 REMOVIDO")
    print(f"arquivo: {ARQ}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reverter", action="store_true")
    args = parser.parse_args()

    try:
        repo = localizar_repo()
        print("R1-V2 — REGRESSIVO EMAIL_READ(urgentes=True)")
        print("=" * 60)
        print(f"repo: {repo}")
        if args.reverter:
            reverter(repo)
        else:
            aplicar(repo)
        return 0
    except Erro as exc:
        print("\n🟠 NENHUMA ALTERAÇÃO FEITA")
        print(exc)
        return 1
    except Exception as exc:
        print("\n🔴 FALHA INESPERADA")
        print(f"{type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
