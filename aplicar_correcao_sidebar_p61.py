from __future__ import annotations

import shutil
from pathlib import Path


NOVO_SETTINGS_SVG = '''<svg xmlns="http://www.w3.org/2000/svg"
     width="24"
     height="24"
     viewBox="0 0 24 24"
     fill="none"
     stroke="#C7C3C8"
     stroke-width="1.8"
     stroke-linecap="round"
     stroke-linejoin="round">
  <circle cx="12" cy="12" r="3"/>
  <path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06-2.12 2.12-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V20.3h-3v-.09a1.7 1.7 0 0 0-1.03-1.56 1.7 1.7 0 0 0-1.87.34l-.06.06-2.12-2.12.06-.06A1.7 1.7 0 0 0 7.04 15a1.7 1.7 0 0 0-1.56-1.03H5.4v-3h.08A1.7 1.7 0 0 0 7.04 9.94a1.7 1.7 0 0 0-.34-1.87l-.06-.06 2.12-2.12.06.06a1.7 1.7 0 0 0 1.87.34 1.7 1.7 0 0 0 1.03-1.56V4.65h3v.08a1.7 1.7 0 0 0 1.03 1.56 1.7 1.7 0 0 0 1.87-.34l.06-.06 2.12 2.12-.06.06a1.7 1.7 0 0 0-.34 1.87 1.7 1.7 0 0 0 1.56 1.03H21v3h-.08A1.7 1.7 0 0 0 19.4 15Z"/>
</svg>
'''


def localizar_projeto() -> tuple[Path, Path, Path]:
    bases = [Path.cwd(), Path(__file__).resolve().parent]
    candidatos: list[Path] = []

    for base in bases:
        direto = base / "cliente" / "terminal_laylay_2.py"
        if direto.is_file():
            candidatos.append(direto)

        for encontrado in base.glob("*/cliente/terminal_laylay_2.py"):
            if encontrado.is_file():
                candidatos.append(encontrado)

    vistos: set[Path] = set()

    for terminal in candidatos:
        terminal = terminal.resolve()

        if terminal in vistos:
            continue

        vistos.add(terminal)

        raiz = terminal.parents[1]
        settings_svg = (
            raiz
            / "cliente"
            / "terminal_2"
            / "assets"
            / "icons"
            / "settings.svg"
        )

        if settings_svg.is_file():
            return raiz, terminal, settings_svg

    raise FileNotFoundError(
        "Não encontrei o projeto Laylay. "
        "Execute este arquivo dentro da pasta do projeto."
    )


def trocar_unico(
    texto: str,
    antigo: str,
    novo: str,
    descricao: str,
) -> str:
    if antigo not in texto:
        raise RuntimeError(
            f"Não encontrei {descricao}. Nenhum arquivo foi salvo."
        )

    return texto.replace(antigo, novo, 1)


def main() -> None:
    raiz, terminal_path, settings_path = localizar_projeto()

    terminal_original = terminal_path.read_text(encoding="utf-8")
    settings_original = settings_path.read_text(encoding="utf-8")

    terminal = terminal_original

    # 1. Garante o nome correto.
    if 'self.marca = QLabel("Laylay ✦")' not in terminal:
        if 'self.marca = QLabel("Layla ✦")' in terminal:
            terminal = terminal.replace(
                'self.marca = QLabel("Layla ✦")',
                'self.marca = QLabel("Laylay ✦")',
                1,
            )
        elif 'self.marca = QLabel("Layla")' in terminal:
            terminal = terminal.replace(
                'self.marca = QLabel("Layla")',
                'self.marca = QLabel("Laylay ✦")',
                1,
            )
        else:
            raise RuntimeError(
                "Não encontrei o nome da Laylay no topo."
            )

    # 2. Mantém o botão de nova conversa só para compatibilidade,
    #    mas escondido e fora do layout visual.
    terminal = trocar_unico(
        terminal,
        '        self.nova = QPushButton()\n',
        '        self.nova = QPushButton(self.sidebar_topo)\n',
        "a criação do botão de nova conversa",
    )

    antigo_tooltip = (
        '        self.nova.setToolTip(\n'
        '            "Nova conversa"\n'
        '        )\n'
        '        self.nova.clicked.connect(\n'
    )

    novo_tooltip = (
        '        self.nova.setToolTip(\n'
        '            "Nova conversa"\n'
        '        )\n'
        '        self.nova.hide()\n'
        '        self.nova.clicked.connect(\n'
    )

    terminal = trocar_unico(
        terminal,
        antigo_tooltip,
        novo_tooltip,
        "o estado visual do botão de nova conversa",
    )

    antigo_layout = (
        '        topo.addWidget(self.avatar_side)\n'
        '        topo.addLayout(marca_box, 1)\n'
        '        topo.addWidget(self.nova)\n'
        '        topo.addWidget(self.recolher)\n'
    )

    novo_layout = (
        '        topo.addWidget(self.avatar_side)\n'
        '        topo.addLayout(marca_box, 1)\n'
        '        topo.addWidget(self.recolher)\n'
    )

    terminal = trocar_unico(
        terminal,
        antigo_layout,
        novo_layout,
        "o botão + no layout superior",
    )

    # 3. Valida tudo antes de salvar.
    compile(terminal, str(terminal_path), "exec")

    if (
        "<svg" not in NOVO_SETTINGS_SVG
        or "</svg>" not in NOVO_SETTINGS_SVG
        or 'viewBox="0 0 24 24"' not in NOVO_SETTINGS_SVG
    ):
        raise RuntimeError("O novo SVG não passou pela validação.")

    # 4. Backups.
    terminal_backup = terminal_path.with_name(
        "terminal_laylay_2.py.p61.bak"
    )
    settings_backup = settings_path.with_name(
        "settings.svg.p61.bak"
    )

    shutil.copy2(terminal_path, terminal_backup)
    shutil.copy2(settings_path, settings_backup)

    terminal_path.write_text(terminal, encoding="utf-8")
    settings_path.write_text(NOVO_SETTINGS_SVG, encoding="utf-8")

    print()
    print("P6.1 APLICADO COM SUCESSO")
    print("-------------------------")
    print(f"Projeto: {raiz}")
    print()
    print("Corrigido:")
    print("  ✓ Laylay preservado corretamente")
    print("  ✓ Botão + removido do topo")
    print("  ✓ Ícone de Configurações redesenhado")
    print()
    print("Backups:")
    print(f"  {terminal_backup}")
    print(f"  {settings_backup}")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print()
        print("ERRO:")
        print(erro)
        raise
