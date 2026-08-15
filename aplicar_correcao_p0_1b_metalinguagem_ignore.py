#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MARCADOR = "P0_METALINGUAGEM_IGNORE_20260814"
MODALIDADE_REL = Path("mente_laylay/cognicao/modalidade_turno.py")
TESTE_REL = Path("tests/test_p0_autorizacao_modalidade.py")


def achar_raiz(inicio: Path) -> Path:
    inicio = inicio.resolve()
    for pasta in (inicio, *inicio.parents):
        if (
            (pasta / "laylay.py").is_file()
            and (pasta / MODALIDADE_REL).is_file()
            and (pasta / TESTE_REL).is_file()
        ):
            return pasta
    raise FileNotFoundError(
        "Não encontrei a raiz da Laylay. Coloque este script dentro do projeto "
        "ou use --root."
    )


def raiz_padrao() -> Path:
    for inicio in (Path(__file__).resolve().parent, Path.cwd().resolve()):
        try:
            return achar_raiz(inicio)
        except FileNotFoundError:
            pass
    raise FileNotFoundError("Não encontrei a raiz do projeto.")


def patch_modalidade(fonte: str) -> str:
    if MARCADOR in fonte:
        return fonte

    ancora = '''        or re.search(r"^(?:a\\s+)?(?:palavra|frase|expressao|texto|termo)\\b", t)
        or re.search(r"\\bnao\\s+(?:e|eh)\\s+(?:um\\s+)?(?:pedido|comando|ordem)\\b", t)
'''

    substituto = '''        or re.search(r"^(?:a\\s+)?(?:palavra|frase|expressao|texto|termo)\\b", t)
        # P0_METALINGUAGEM_IGNORE_20260814
        # "ignore/desconsidere a palavra X" fala SOBRE o token X; o verbo
        # citado depois não ganha autorização operacional.
        or re.search(
            r"^(?:por\\s+favor\\s+)?"
            r"(?:ignore|ignora|ignorar|desconsidere|desconsidera|desconsiderar)\\s+"
            r"(?:a\\s+|o\\s+)?(?:palavra|frase|expressao|texto|termo)\\b",
            t,
        )
        or re.search(r"\\bnao\\s+(?:e|eh)\\s+(?:um\\s+)?(?:pedido|comando|ordem)\\b", t)
'''

    if ancora not in fonte:
        raise RuntimeError(
            "Âncora da proteção de metalinguagem não encontrada. "
            "O arquivo mudou; não apliquei patch por aproximação."
        )

    fonte = fonte.replace(ancora, substituto, 1)
    ast.parse(fonte)
    return fonte


def patch_testes(fonte: str) -> str:
    if "Ignore a palavra abre nesta frase." not in fonte:
        ancora = '''    "A palavra fecha não é um pedido para fechar nada.",
'''
        substituto = '''    "A palavra fecha não é um pedido para fechar nada.",
    "Ignore a palavra abre nesta frase.",
    "Desconsidere a frase fecha a Calculadora.",
'''
        if ancora not in fonte:
            raise RuntimeError("Âncora da matriz NAO_EXECUTAR não encontrada.")
        fonte = fonte.replace(ancora, substituto, 1)

    if "test_runtime_imediato_bloqueia_ignore_palavra_com_detector_agressivo" not in fonte:
        bloco = r'''

def test_runtime_imediato_bloqueia_ignore_palavra_com_detector_agressivo():
    texto = "Ignore a palavra abre nesta frase."
    runtime, executados, _registros, _falas = _runtime_para(
        texto,
        detector=lambda _texto: {
            "intent": "APP_OPEN",
            "params": {"nome_app": "nesta frase"},
        },
    )
    assert runtime.processar_prioritarios(texto) is False
    assert executados == []


def test_ignore_palavra_e_metalinguagem_no_turno_inteiro():
    turno = classificar_modalidade_turno(
        "Ignore a palavra abre nesta frase."
    )
    assert turno["autoriza_execucao"] is False
    assert turno["texto_operacional"] == ""
    assert turno["atos"] == ["conversa"]
    assert turno["natureza_acao"] == "mencao_operacional"
'''
        fonte = fonte.rstrip() + bloco + "\n"

    ast.parse(fonte)
    return fonte


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplica P0.1b: metalinguagem 'ignore a palavra...'."
    )
    parser.add_argument("--root", type=Path)
    parser.add_argument("--sem-testes", action="store_true")
    args = parser.parse_args()

    raiz = achar_raiz(args.root.expanduser()) if args.root else raiz_padrao()
    modalidade = raiz / MODALIDADE_REL
    testes = raiz / TESTE_REL

    fonte_modalidade = modalidade.read_text(encoding="utf-8")
    fonte_testes = testes.read_text(encoding="utf-8")

    novo_modalidade = patch_modalidade(fonte_modalidade)
    novo_testes = patch_testes(fonte_testes)

    backup = (
        raiz
        / "_backup_correcao_p0_metalinguagem"
        / datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(modalidade, backup / MODALIDADE_REL.name)
    shutil.copy2(testes, backup / TESTE_REL.name)

    try:
        modalidade.write_text(novo_modalidade, encoding="utf-8")
        testes.write_text(novo_testes, encoding="utf-8")

        ast.parse(modalidade.read_text(encoding="utf-8"))
        ast.parse(testes.read_text(encoding="utf-8"))

        subprocess.run(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(MODALIDADE_REL),
                str(TESTE_REL),
            ],
            cwd=raiz,
            check=True,
        )

        if not args.sem_testes:
            suites = [str(TESTE_REL)]
            for rel in (
                Path("tests/test_p0_autopreservacao_executor.py"),
                Path("tests/test_p0_isolamento_contexto.py"),
                Path("tests/test_regressoes_roteiro_118.py"),
            ):
                if (raiz / rel).is_file():
                    suites.append(str(rel))

            subprocess.run(
                [sys.executable, "-m", "pytest", "-q", *suites],
                cwd=raiz,
                check=True,
            )

    except Exception as erro:
        print(f"\nERRO: {type(erro).__name__}: {erro}")
        print("Restaurando estado anterior...")
        shutil.copy2(backup / MODALIDADE_REL.name, modalidade)
        shutil.copy2(backup / TESTE_REL.name, testes)
        print("✓ Restauração concluída.")
        return 1

    print("\n✓ P0.1b aplicada com sucesso.")
    print(f"Backup: {backup}")
    print("Contraexemplo coberto: Ignore a palavra abre nesta frase.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
