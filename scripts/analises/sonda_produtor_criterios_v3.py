"""Painel cego v3 do produtor de criterios; nenhuma ligacao com o runtime.

O par de arquivos e verificado por hash antes de qualquer consulta. O
gabarito so participa da afericao posterior, nunca da passagem de etapas.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.analises.sonda_produtor_criterios_v2 import medir_caso


DADOS = Path(__file__).parent / "dados"
ENTRADAS = DADOS / "sonda_criterios_entradas_v3.json"
REVISAO = DADOS / "sonda_criterios_revisao_v3.json"
HASH_ENTRADAS = "d4eafb9dee41e8eed47760a22dc69df231f334558c66647d0445d654f2daab23"
HASH_REVISAO = "efe5d80656f76932c354543e0f59ff23de230dd586fd45e50949503293dbb61c"


def carregar_painel() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    """Recusa alteracao silenciosa de entradas ou revisao congeladas."""
    entradas_bytes = ENTRADAS.read_bytes()
    revisao_bytes = REVISAO.read_bytes()
    if (hashlib.sha256(entradas_bytes).hexdigest() != HASH_ENTRADAS
            or hashlib.sha256(revisao_bytes).hexdigest() != HASH_REVISAO):
        raise ValueError("painel v3 alterado depois do congelamento")
    entradas = json.loads(entradas_bytes.decode("utf-8"))
    revisao = json.loads(revisao_bytes.decode("utf-8"))
    casos, gabarito = entradas["casos"], revisao["casos"]
    ids = [caso["id"] for caso in casos]
    if (entradas.get("versao") != 3 or revisao.get("versao") != 3
            or len(ids) != 10 or len(ids) != len(set(ids))
            or set(ids) != set(gabarito)):
        raise ValueError("painel v3 divergente da revisao")
    return casos, gabarito


def main() -> None:
    casos, revisao = carregar_painel()
    for caso in casos:
        print(json.dumps(
            medir_caso(caso, revisao[caso["id"]]), ensure_ascii=False,
        ), flush=True)


if __name__ == "__main__":
    main()
