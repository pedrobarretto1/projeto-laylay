from __future__ import annotations

import shutil
from pathlib import Path


def localizar_dashboard() -> tuple[Path, Path]:
    bases = [
        Path.cwd(),
        Path(__file__).resolve().parent,
    ]

    for base in bases:
        candidatos = [
            base / "cliente" / "terminal_2" / "dashboard.py"
        ]

        try:
            candidatos += list(
                base.glob("*/cliente/terminal_2/dashboard.py")
            )
        except OSError:
            pass

        for dashboard in candidatos:
            if not dashboard.is_file():
                continue

            dashboard = dashboard.resolve()
            raiz = dashboard.parents[2]
            terminal = (
                raiz
                / "cliente"
                / "terminal_laylay_2.py"
            )

            if terminal.is_file():
                return raiz, dashboard

    raise FileNotFoundError(
        "Não encontrei o dashboard da Laylay."
    )


def main() -> None:
    raiz, dashboard_path = localizar_dashboard()

    original = dashboard_path.read_text(
        encoding="utf-8"
    )

    if "    QBoxLayout,\n" in original:
        compile(
            original,
            str(dashboard_path),
            "exec",
        )
        print("QBoxLayout já está importado.")
        return

    ancora = """from PySide6.QtWidgets import (
    QFrame,
"""

    if ancora not in original:
        raise RuntimeError(
            "Não encontrei o bloco de imports do QtWidgets."
        )

    texto = original.replace(
        ancora,
        """from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
""",
        1,
    )

    compile(
        texto,
        str(dashboard_path),
        "exec",
    )

    backup = dashboard_path.with_name(
        "dashboard.py.reparo_qboxlayout.bak"
    )

    shutil.copy2(
        dashboard_path,
        backup,
    )

    dashboard_path.write_text(
        texto,
        encoding="utf-8",
    )

    print()
    print("REPARO QBOXLAYOUT APLICADO")
    print("--------------------------")
    print(f"Projeto: {raiz}")
    print(f"Arquivo: {dashboard_path}")
    print(f"Backup:  {backup}")
    print()
    print("Corrigido:")
    print("  ✓ QBoxLayout importado")
    print("  ✓ dashboard compilado antes de salvar")
    print()
    print("Pode abrir a Laylay novamente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
