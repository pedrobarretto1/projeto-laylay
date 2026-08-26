"""Auditoria reproduzível da distribuição portátil da Laylay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Iterable


ARQUIVOS_OBRIGATORIOS = (
    "Laylay.exe",
    "AvatarLaylay.exe",
    "Iniciar Laylay.exe",
    "configuracao.env",
    "README_PORTATIL.md",
    "LICENCAS_TERCEIROS.md",
)
ARQUIVOS_PRIVADOS = {
    "devices.json",
    "snapshot.json",
    "tinytuya.json",
    "tuya-raw.json",
}
SUFIXOS_TEXTO = {".env", ".ini", ".json", ".md", ".txt", ".yaml", ".yml"}
PADRAO_CHAVE_PRIVADA = re.compile(
    r"(?:api[_-]?key|password|passwd|secret|token|gmail_user|email)",
    re.IGNORECASE,
)
PADROES_CAMINHO_PESSOAL = (
    re.compile(r"[A-Za-z]:[\\/]Users[\\/](?!Public(?:[\\/]|$)|Default(?:[\\/]|$))", re.IGNORECASE),
    re.compile(r"/(?:home|Users)/[^/$%{][^/]+/", re.IGNORECASE),
)


def _arquivos_texto_do_pacote(pacote: Path) -> Iterable[Path]:
    for caminho in pacote.rglob("*"):
        if not caminho.is_file() or caminho.suffix.casefold() not in SUFIXOS_TEXTO:
            continue
        if "_internal" in caminho.relative_to(pacote).parts:
            continue
        if caminho.stat().st_size <= 2 * 1024 * 1024:
            yield caminho


def _ler_configuracao(caminho: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if not caminho.is_file():
        return valores
    for linha in caminho.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        chave, valor = texto.split("=", 1)
        valores[chave.strip()] = valor.strip().strip('"\'')
    return valores


def auditar_pacote(
    pasta: str | Path,
    *,
    exigir_modelo: bool = True,
    permitir_memoria: bool = False,
    permitir_privados: bool = False,
) -> dict[str, object]:
    pacote = Path(pasta).expanduser().resolve()
    problemas: list[str] = []
    avisos: list[str] = []

    if not pacote.is_dir():
        return {"status": "falha", "pacote": str(pacote), "problemas": ["pasta do pacote não existe"], "avisos": []}

    for nome in ARQUIVOS_OBRIGATORIOS:
        if not (pacote / nome).is_file():
            problemas.append(f"arquivo obrigatório ausente: {nome}")
    for pasta_obrigatoria in ("avatar", "memoria", "runtime_llm", "extensao_chrome"):
        if not (pacote / pasta_obrigatoria).is_dir():
            problemas.append(f"pasta obrigatória ausente: {pasta_obrigatoria}")

    servidores = list((pacote / "runtime_llm").rglob("llama-server.exe"))
    if not servidores:
        problemas.append("llama-server.exe não foi incluído")
    modelos = list((pacote / "modelos").glob("*.gguf")) if (pacote / "modelos").is_dir() else []
    if exigir_modelo and not modelos:
        problemas.append("modelo GGUF não foi incluído")
    elif not modelos:
        avisos.append("modelo GGUF ausente; conversa local ficará degradada")

    arquivos_memoria = [item for item in (pacote / "memoria").rglob("*") if item.is_file()]
    if arquivos_memoria and not permitir_memoria:
        problemas.append("o pacote limpo contém memória pessoal")

    encontrados_privados = sorted(
        str(item.relative_to(pacote))
        for item in pacote.rglob("*")
        if item.is_file() and item.name.casefold() in ARQUIVOS_PRIVADOS
    )
    pasta_voz = pacote / "dados" / "voz_pessoal"
    if (encontrados_privados or pasta_voz.exists()) and not permitir_privados:
        problemas.append("o pacote limpo contém arquivos privados de integração")

    configuracao = _ler_configuracao(pacote / "configuracao.env")
    if not permitir_privados:
        preenchidas = sorted(
            chave for chave, valor in configuracao.items()
            if valor and PADRAO_CHAVE_PRIVADA.search(chave)
        )
        if preenchidas:
            problemas.append("configuração contém credenciais preenchidas: " + ", ".join(preenchidas))
        if configuracao.get("IOT_CONTROLE_FISICO_AUTORIZADO", "NAO").casefold() not in {"nao", "não", "0", "false"}:
            problemas.append("controle IoT físico veio autorizado no pacote limpo")

    caminhos_pessoais: list[str] = []
    for caminho in _arquivos_texto_do_pacote(pacote):
        texto = caminho.read_text(encoding="utf-8-sig", errors="replace")
        if any(padrao.search(texto) for padrao in PADROES_CAMINHO_PESSOAL):
            caminhos_pessoais.append(str(caminho.relative_to(pacote)))
    if caminhos_pessoais:
        problemas.append("caminhos pessoais encontrados em: " + ", ".join(sorted(caminhos_pessoais)))

    return {
        "status": "ok" if not problemas else "falha",
        "pacote": str(pacote),
        "problemas": problemas,
        "avisos": avisos,
        "modelo_incluido": bool(modelos),
        "motores_llm": len(servidores),
        "memorias": len(arquivos_memoria),
        "arquivos_privados": encontrados_privados,
    }


def auditar_versionamento(raiz: str | Path) -> dict[str, object]:
    projeto = Path(raiz).expanduser().resolve()
    resultado = subprocess.run(
        ["git", "ls-files"], cwd=projeto, check=True, capture_output=True, text=True,
    )
    rastreados = [Path(linha.strip()) for linha in resultado.stdout.splitlines() if linha.strip()]
    proibidos: list[str] = []
    for relativo in rastreados:
        partes = tuple(parte.casefold() for parte in relativo.parts)
        nome = relativo.name.casefold()
        if partes and partes[0] == "memoria":
            proibidos.append(str(relativo))
        elif len(partes) >= 2 and partes[:2] == ("dados", "voz_pessoal"):
            proibidos.append(str(relativo))
        elif nome in ARQUIVOS_PRIVADOS or nome in {"playlists.json", "configuracao.env", ".env"}:
            proibidos.append(str(relativo))
    return {
        "status": "ok" if not proibidos else "falha",
        "proibidos": sorted(proibidos),
        "arquivos_rastreados": len(rastreados),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pacote", nargs="?", help="pasta Laylay gerada pelo PyInstaller")
    parser.add_argument("--raiz-projeto", default=".")
    parser.add_argument("--sem-modelo", action="store_true")
    parser.add_argument("--permitir-memoria", action="store_true")
    parser.add_argument("--permitir-privados", action="store_true")
    parser.add_argument("--somente-versionamento", action="store_true")
    args = parser.parse_args(argv)

    relatorio: dict[str, object] = {"versionamento": auditar_versionamento(args.raiz_projeto)}
    if not args.somente_versionamento:
        if not args.pacote:
            parser.error("informe a pasta do pacote ou use --somente-versionamento")
        relatorio["pacote"] = auditar_pacote(
            args.pacote,
            exigir_modelo=not args.sem_modelo,
            permitir_memoria=args.permitir_memoria,
            permitir_privados=args.permitir_privados,
        )
    print(json.dumps(relatorio, ensure_ascii=False, indent=2))
    falhou = any(
        isinstance(item, dict) and item.get("status") != "ok"
        for item in relatorio.values()
    )
    return 1 if falhou else 0


if __name__ == "__main__":
    raise SystemExit(main())
