from __future__ import annotations

import shutil
from pathlib import Path


def localizar_terminal() -> tuple[Path, Path]:
    bases = [
        Path.cwd(),
        Path(__file__).resolve().parent,
    ]

    for base in bases:
        candidatos = [
            base / "cliente" / "terminal_laylay_2.py"
        ]

        try:
            candidatos += list(
                base.glob(
                    "*/cliente/terminal_laylay_2.py"
                )
            )
        except OSError:
            pass

        for terminal in candidatos:
            if not terminal.is_file():
                continue

            terminal = terminal.resolve()
            raiz = terminal.parents[1]

            dashboard = (
                raiz
                / "cliente"
                / "terminal_2"
                / "dashboard.py"
            )

            if dashboard.is_file():
                return raiz, terminal

    raise FileNotFoundError(
        "Não encontrei o projeto Laylay."
    )


def main() -> None:
    raiz, terminal_path = localizar_terminal()

    original = terminal_path.read_text(
        encoding="utf-8"
    )

    marcador = (
        "                /* =========================================\n"
        "                   P10.1 — SISTEMA FASE 3\n"
        "                   ========================================= */\n"
    )

    inicio = original.find(marcador)

    if inicio < 0:
        raise RuntimeError(
            "Não encontrei o CSS do P10.1."
        )

    fim = original.find(
        "                #pageTitle ",
        inicio,
    )

    if fim < 0:
        raise RuntimeError(
            "Não encontrei o final do CSS do P10.1."
        )

    bloco = original[inicio:fim]

    # Se já estiver escapado, não duplica de novo.
    if "#systemLowerRow {{" in bloco:
        compile(
            original,
            str(terminal_path),
            "exec",
        )
        print(
            "O CSS do P10.1 já está corrigido."
        )
        return

    # O stylesheet está dentro de f-string:
    # chaves literais de QSS precisam ser {{ e }}.
    bloco_corrigido = (
        bloco
        .replace("{", "{{")
        .replace("}", "}}")
    )

    texto = (
        original[:inicio]
        + bloco_corrigido
        + original[fim:]
    )

    # Validação real antes de tocar no arquivo.
    compile(
        texto,
        str(terminal_path),
        "exec",
    )

    backup = terminal_path.with_name(
        "terminal_laylay_2.py."
        "reparo_css_p101.bak"
    )

    shutil.copy2(
        terminal_path,
        backup,
    )

    terminal_path.write_text(
        texto,
        encoding="utf-8",
    )

    print()
    print("REPARO CSS P10.1 APLICADO")
    print("-------------------------")
    print(f"Projeto: {raiz}")
    print(f"Arquivo: {terminal_path}")
    print(f"Backup:  {backup}")
    print()
    print("Corrigido:")
    print("  ✓ {  -> {{")
    print("  ✓ }  -> }}")
    print("  ✓ somente dentro do bloco P10.1")
    print("  ✓ arquivo compilado antes de salvar")
    print()
    print(
        "Agora pode abrir a Laylay novamente."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
