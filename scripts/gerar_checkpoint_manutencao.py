"""Gera um retrato sanitizado e reproduzível da manutenção da Laylay.

O utilitário inspeciona estrutura, configuração pública e metadados do Git.
Ele não abre memória, credenciais, conversas, playlists nem dados da Tuya.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_CHECKPOINT = 1
DIRETORIOS_IGNORADOS = frozenset({
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".venv-1",
    ".venv-treino-voz",
    ".venv314",
    "__pycache__",
    "build",
    "build_portatil",
    "dist",
    "logs",
    "modelos",
    "runtime_llm",
})
NOMES_SENSIVEIS = frozenset({
    ".env",
    "devices.json",
    "playlists.json",
    "snapshot.json",
    "tinytuya.json",
    "tuya-raw.json",
})
PREFIXOS_SENSIVEIS = (
    "client_secret",
    "credentials",
    "secrets",
    "service-account",
    "token",
)
EXEMPLOS_PUBLICOS = frozenset({
    ".env.example",
    "devices.example.json",
    "snapshot.example.json",
    "tinytuya.example.json",
})

ExecutorGit = Callable[[Sequence[str]], str]


def normalizar_caminho(caminho: str | Path) -> str:
    return str(caminho).replace("\\", "/").strip("/")


def caminho_parece_sensivel(caminho: str | Path) -> bool:
    """Classifica pelo nome sem abrir o arquivo apontado."""

    normalizado = normalizar_caminho(caminho).casefold()
    partes = tuple(parte for parte in normalizado.split("/") if parte)
    if not partes:
        return False
    nome = partes[-1]
    if nome in EXEMPLOS_PUBLICOS:
        return False
    if partes[0] == "memoria":
        return True
    if len(partes) >= 2 and partes[:2] == ("dados", "voz_pessoal"):
        return True
    if nome in NOMES_SENSIVEIS:
        return True
    return nome.endswith(".json") and nome.startswith(PREFIXOS_SENSIVEIS)


def _arquivo_ignorado(caminho: Path, raiz: Path) -> bool:
    relativo = caminho.relative_to(raiz)
    return any(parte in DIRETORIOS_IGNORADOS for parte in relativo.parts[:-1])


def contar_linhas(caminho: Path) -> int:
    with caminho.open("r", encoding="utf-8", errors="replace") as arquivo:
        return sum(1 for _linha in arquivo)


def coletar_inventario_python(raiz: Path) -> dict[str, Any]:
    arquivos: list[tuple[str, int]] = []
    for caminho in raiz.rglob("*.py"):
        if not caminho.is_file() or _arquivo_ignorado(caminho, raiz):
            continue
        relativo = normalizar_caminho(caminho.relative_to(raiz))
        arquivos.append((relativo, contar_linhas(caminho)))

    testes = [(nome, linhas) for nome, linhas in arquivos if nome.startswith("tests/")]
    producao = [(nome, linhas) for nome, linhas in arquivos if not nome.startswith("tests/")]
    maiores = sorted(arquivos, key=lambda item: (-item[1], item[0]))[:10]
    return {
        "arquivos_python": len(arquivos),
        "linhas_python": sum(linhas for _nome, linhas in arquivos),
        "arquivos_producao": len(producao),
        "linhas_producao": sum(linhas for _nome, linhas in producao),
        "arquivos_testes": len(testes),
        "linhas_testes": sum(linhas for _nome, linhas in testes),
        "modulos_acima_1000_linhas": sum(linhas > 1_000 for _nome, linhas in producao),
        "maiores_modulos": [
            {"caminho": nome, "linhas": linhas} for nome, linhas in maiores
        ],
    }


def executar_git(raiz: Path, argumentos: Sequence[str]) -> str:
    processo = subprocess.run(
        ["git", *argumentos],
        cwd=raiz,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    return processo.stdout


def _separar_nulos(saida: str) -> list[str]:
    return [item for item in saida.split("\0") if item]


def coletar_estado_git(
    raiz: Path,
    *,
    executor: ExecutorGit | None = None,
) -> dict[str, Any]:
    chamar = executor or (lambda argumentos: executar_git(raiz, argumentos))
    commit = chamar(("rev-parse", "--short", "HEAD")).strip()
    ramo = chamar(("branch", "--show-current")).strip() or "detached"
    alterados = _separar_nulos(chamar(("status", "--porcelain=v1", "-z")))
    versionados = _separar_nulos(chamar(("ls-files", "-z")))
    sensiveis = sorted(
        normalizar_caminho(caminho)
        for caminho in versionados
        if caminho_parece_sensivel(caminho)
    )
    return {
        "commit": commit,
        "ramo": ramo,
        "entradas_alteradas": len(alterados),
        "arquivos_versionados": len(versionados),
        "arquivos_sensiveis_versionados": sensiveis,
    }


def criar_checkpoint(
    raiz: Path,
    *,
    executor_git: ExecutorGit | None = None,
    agora: datetime | None = None,
) -> dict[str, Any]:
    raiz = raiz.resolve()
    instante = agora or datetime.now(timezone.utc)
    return {
        "schema": SCHEMA_CHECKPOINT,
        "gerado_em_utc": instante.astimezone(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "plataforma": platform.platform(),
        "git": coletar_estado_git(raiz, executor=executor_git),
        "inventario": coletar_inventario_python(raiz),
        "configuracao_qualidade": {
            "pyproject": (raiz / "pyproject.toml").is_file(),
            "workflow_ci": (raiz / ".github" / "workflows" / "quality.yml").is_file(),
            "script_qualidade": (raiz / "scripts" / "verificar_qualidade.ps1").is_file(),
            "politica_finais_linha": (raiz / ".gitattributes").is_file(),
        },
        "privacidade": {
            "conteudo_pessoal_lido": False,
            "seguro_para_compartilhar": True,
        },
    }


def salvar_checkpoint(checkpoint: dict[str, Any], destino: Path | None) -> None:
    texto = json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True)
    if destino is None:
        print(texto)
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(f"{texto}\n", encoding="utf-8")


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raiz",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="raiz do repositório; por padrão, detectada pelo próprio script",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        help="arquivo JSON opcional; sem esta opção, escreve somente no terminal",
    )
    return parser


def main(argumentos: Sequence[str] | None = None) -> int:
    opcoes = construir_parser().parse_args(argumentos)
    checkpoint = criar_checkpoint(opcoes.raiz)
    salvar_checkpoint(checkpoint, opcoes.saida)
    if checkpoint["git"]["arquivos_sensiveis_versionados"]:
        print(
            "Checkpoint recusado: há arquivos potencialmente sensíveis versionados.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
