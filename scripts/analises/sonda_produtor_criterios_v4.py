"""Painel cego v4 para testar o veto estrutural de criterio unico offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.analises.sonda_produtor_criterios_v2 import medir_caso


DADOS = Path(__file__).parent / "dados"
ENTRADAS = DADOS / "sonda_criterios_entradas_v4.json"
REVISAO = DADOS / "sonda_criterios_revisao_v4.json"
HASH_ENTRADAS = "0217a119efd0457b17585eaddcaaca5b33a8ad4bb11eb7f6aa8ee776a1855b35"
HASH_REVISAO = "e5b5dcc945ae2db289a7cf00ef65bc687169412fe417e083b2e76041516d7691"


def carregar_painel() -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    entradas_bytes = ENTRADAS.read_bytes()
    revisao_bytes = REVISAO.read_bytes()
    if (hashlib.sha256(entradas_bytes).hexdigest() != HASH_ENTRADAS
            or hashlib.sha256(revisao_bytes).hexdigest() != HASH_REVISAO):
        raise ValueError("painel v4 alterado depois do congelamento")
    entradas = json.loads(entradas_bytes.decode("utf-8"))
    revisao = json.loads(revisao_bytes.decode("utf-8"))
    casos, gabarito = entradas["casos"], revisao["casos"]
    ids = [caso["id"] for caso in casos]
    if (entradas.get("versao") != 4 or revisao.get("versao") != 4
            or len(ids) != 10 or len(ids) != len(set(ids))
            or set(ids) != set(gabarito)):
        raise ValueError("painel v4 divergente da revisao")
    return casos, gabarito


def main() -> None:
    casos, revisao = carregar_painel()
    for caso in casos:
        print(json.dumps(medir_caso(
            caso, revisao[caso["id"]], exigir_condicao_unica=True,
        ), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
