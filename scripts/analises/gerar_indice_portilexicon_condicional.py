"""Gera um índice offline mínimo de formas condicionais, sem tocar no runtime.

Fonte: PortiLexicon-UD (Lucelene Lopes et al.), VERB.tsv, licença MIT.
O commit e o hash da fonte são fixos; nunca atualizar silenciosamente.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import requests


COMMIT_FONTE = "315e063da1f89c89e2097c6e72428ebefb9ab1d1"
SHA256_FONTE = "3c3ccbf94e0c6e7a1673722f6adceb36e75fde7a70fd5a1dc0edc5b7bcc69342"
URL_FONTE = (
    "https://raw.githubusercontent.com/LuceleneL/PortiLexicon-UD/"
    f"{COMMIT_FONTE}/VERB.tsv"
)
DESTINO = (Path(__file__).resolve().parent / "dados" /
           "portilexicon_futuro_subjuntivo_3p.tsv")


def extrair_indice(conteudo: bytes) -> bytes:
    """Mantém só número da 3ª pessoa no futuro do subjuntivo, sem POS inferido."""
    if hashlib.sha256(conteudo).hexdigest() != SHA256_FONTE:
        raise ValueError("fonte PortiLexicon diferente do hash congelado")
    formas: dict[str, set[str]] = {}
    for linha in conteudo.decode("utf-8").splitlines():
        colunas = linha.split("\t")
        if len(colunas) != 3:
            raise ValueError("linha invalida na fonte PortiLexicon")
        forma, _lema, atributos = colunas
        if not forma.isalpha():
            continue
        pares = dict(campo.split("=", 1) for campo in atributos.split("|")
                     if "=" in campo)
        if (pares.get("Mood") == "Sub" and pares.get("Tense") == "Fut"
                and pares.get("Person") == "3"
                and pares.get("VerbForm") == "Fin"
                and pares.get("Number") in {"Sing", "Plur"}):
            numero = "S" if pares["Number"] == "Sing" else "P"
            formas.setdefault(forma.casefold(), set()).add(numero)
    if not 10000 <= len(formas) <= 100000:
        raise ValueError("cobertura inesperada no indice PortiLexicon")
    cabecalho = (
        "# PortiLexicon-UD, Lucelene Lopes et al.; ver PORTILEXICON_LICENSE.txt\n"
        f"# commit={COMMIT_FONTE}; fonte_sha256={SHA256_FONTE}\n"
        "# Mood=Sub|Tense=Fut|Person=3|VerbForm=Fin; numero S/P\n"
    )
    linhas = (f"{forma}\t{''.join(sorted(numeros))}\n"
              for forma, numeros in sorted(formas.items()))
    return (cabecalho + "".join(linhas)).encode("utf-8")


def main() -> None:
    resposta = requests.get(URL_FONTE, timeout=90)
    resposta.raise_for_status()
    indice = extrair_indice(resposta.content)
    if DESTINO.exists():
        if DESTINO.read_bytes() != indice:
            raise SystemExit("indice existente difere; abortando sem sobrescrever")
        print("indice existente confere")
        return
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("xb") as arquivo:
        arquivo.write(indice)
    if DESTINO.read_bytes() != indice:
        raise RuntimeError("indice gravado nao confere")
    print("indice criado", len(indice), hashlib.sha256(indice).hexdigest())


if __name__ == "__main__":
    main()
