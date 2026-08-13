from __future__ import annotations

import shutil
from pathlib import Path


def encontrar_dashboard() -> Path:
    candidatos = [
        Path.cwd() / "cliente" / "terminal_2" / "dashboard.py",
        Path(__file__).resolve().parent / "cliente" / "terminal_2" / "dashboard.py",
        Path(__file__).resolve().parent / "dashboard.py",
    ]

    for caminho in candidatos:
        if caminho.is_file():
            return caminho

    raise FileNotFoundError(
        "Não encontrei cliente/terminal_2/dashboard.py.\n"
        "Coloque este arquivo na raiz do projeto Laylay e execute novamente."
    )


def main() -> None:
    caminho = encontrar_dashboard()
    texto = caminho.read_text(encoding="utf-8")

    # Se já estiver correto, não mexe.
    if (
        "\n    def _aplicar_memoria_recente(" in texto
        and "\n    def aplicar_dashboard(" in texto
        and "\ndef _aplicar_memoria_recente(" not in texto
        and "\ndef aplicar_dashboard(" not in texto
    ):
        print("O dashboard.py já parece estar com a indentação corrigida.")
        return

    linhas = texto.splitlines(keepends=True)

    try:
        inicio_memoria = next(
            i for i, linha in enumerate(linhas)
            if linha.startswith("def _aplicar_memoria_recente(")
        )
        inicio_dashboard = next(
            i for i, linha in enumerate(linhas)
            if i > inicio_memoria and linha.startswith("def aplicar_dashboard(")
        )
        inicio_invalidar = next(
            i for i, linha in enumerate(linhas)
            if i > inicio_dashboard and linha.startswith("    def invalidar_dashboard(")
        )
        inicio_lateral = next(
            i for i, linha in enumerate(linhas)
            if i > inicio_invalidar and linha.startswith("class PainelLateralDashboard")
        )
    except StopIteration as exc:
        raise RuntimeError(
            "A estrutura esperada não foi encontrada. "
            "Nenhuma alteração foi feita."
        ) from exc

    # Os dois métodos ficaram fora da classe. Indentamos somente eles.
    # invalidar_dashboard já tem 4 espaços e deve continuar assim,
    # virando irmão dos outros métodos dentro da classe.
    for i in range(inicio_memoria, inicio_invalidar):
        if linhas[i].strip():
            linhas[i] = "    " + linhas[i]

    corrigido = "".join(linhas)

    # Verificação de segurança: o arquivo inteiro precisa continuar sintaticamente válido.
    compile(corrigido, str(caminho), "exec")

    backup = caminho.with_suffix(".py.bak")
    shutil.copy2(caminho, backup)
    caminho.write_text(corrigido, encoding="utf-8")

    print("Pronto!")
    print(f"Corrigido: {caminho}")
    print(f"Backup:    {backup}")
    print()
    print("Agora você pode iniciar a Laylay normalmente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:
        print(f"ERRO: {erro}")
        raise