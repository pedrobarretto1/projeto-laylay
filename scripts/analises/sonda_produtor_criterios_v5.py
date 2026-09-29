"""A/B offline congelado: normalização original versus slots segmentados.

Painel local revisado antes da primeira consulta; não é revisão humana
independente nem evidência de ensino no runtime. Não publica ou treina.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.analises import sonda_produtor_criterios_v2 as produtor


DADOS = Path(__file__).parent / "dados"
ENTRADAS = DADOS / "sonda_criterios_entradas_v5.json"
REVISAO = DADOS / "sonda_criterios_revisao_v5.json"
HASH_ENTRADAS = "bab9fba73c34fdbfc964da688a140ee8bed217dfe280ce879763976296958786"
HASH_REVISAO = "a4e02626b34786634405e994d47ee1a84d710bf51b78c91106a204e989b3a6b1"
HASHES_V6 = (
    "1b9e8d4645e7423f178f09cfbf58bb5f20e636e0432ab20cbcd8c65aedf1147b",
    "f9243521064713ee1228d298bab5bcd0b16a598d875228e5876eea95752c7392",
)


def carregar_painel(versao: int = 5) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    if versao not in {5, 6}:
        raise ValueError("painel desconhecido")
    entradas = ENTRADAS if versao == 5 else DADOS / "sonda_criterios_entradas_v6.json"
    revisoes = REVISAO if versao == 5 else DADOS / "sonda_criterios_revisao_v6.json"
    hashes = (HASH_ENTRADAS, HASH_REVISAO) if versao == 5 else HASHES_V6
    entrada, revisao = entradas.read_bytes(), revisoes.read_bytes()
    if (hashlib.sha256(entrada).hexdigest() != hashes[0]
            or hashlib.sha256(revisao).hexdigest() != hashes[1]):
        raise ValueError(f"painel v{versao} alterado depois do congelamento")
    dados, gabarito = json.loads(entrada), json.loads(revisao)
    casos, respostas = dados["casos"], gabarito["casos"]
    ids = [caso["id"] for caso in casos]
    quantidade = 9 if versao == 5 else 12
    if (dados.get("versao") != versao or gabarito.get("versao") != versao
            or len(ids) != quantidade or len(set(ids)) != quantidade
            or set(ids) != set(respostas)):
        raise ValueError(f"painel v{versao} divergente")
    return casos, respostas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--painel", type=int, choices=(5, 6), default=5)
    args = parser.parse_args()
    casos, revisao = carregar_painel(args.painel)
    hashes = (HASH_ENTRADAS, HASH_REVISAO) if args.painel == 5 else HASHES_V6
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    # Exclusivo: repetição diagnóstica não sobrescreve a primeira coleta.
    with args.saida.open("x", encoding="utf-8") as arquivo:
        metadata = {"tipo": "metadata", "modelo": "qwen3:4b-instruct",
                    "temperatura": 0, "painel": args.painel,
                    "hash_entradas": hashes[0], "hash_revisao": hashes[1],
                    "hash_produtor": hashlib.sha256(
                        Path(produtor.__file__).read_bytes()).hexdigest(),
                    "aprovado_para_producao": False}
        arquivo.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        arquivo.flush()
        for indice, caso in enumerate(casos):
            # Alternar ordem dos braços; nenhuma resposta é histórico do outro.
            for segmentada in ((False, True) if indice % 2 == 0 else (True, False)):
                resultado = produtor.medir_caso(
                    caso, revisao[caso["id"]], exigir_condicao_unica=True,
                    normalizacao_segmentada=segmentada,
                )
                registro = {"modo": "segmentada" if segmentada else "original",
                            **resultado}
                arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
                arquivo.flush()
                print(json.dumps({campo: registro.get(campo) for campo in (
                    "id", "modo", "duracao_s", "erro", "afericao_final",
                )}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
