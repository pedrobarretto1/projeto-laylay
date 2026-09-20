"""Aplica curadoria declarada à fila offline, sem inferir rótulos ou procedência.

Coincidência literal com roteiro prova exposição do texto, não origem do evento.
Nenhuma revisão aqui cria partição de treino ou certifica revisão humana.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from .curadoria_encoder import _hash
from .protocolo_ajuste_supervisionado import _rotulos_brutos
from .preparar_lote_relacional_v3 import VARIANTES
from .supervisao_relacoes_v4 import FLAGS, validar_fonte_relacional


def cruzar_exposicao(fila: list[dict], fontes: list[Path]) -> tuple[dict, dict]:
    """Lê apenas scripts explicitamente selecionados, sem importar/executar."""
    textos = {c["texto"] for c in fila}
    encontrados: dict[str, list[dict]] = {t: [] for t in textos}
    hashes = {}
    for caminho in fontes:
        dados = caminho.read_bytes()
        nome = str(caminho.resolve())
        hashes[nome] = hashlib.sha256(dados).hexdigest()
        for no in ast.walk(ast.parse(dados.decode("utf-8-sig"), filename=nome)):
            if not isinstance(no, ast.Constant) or not isinstance(no.value, str):
                continue
            if no.value in textos:
                encontrados[no.value].append({"arquivo": nome, "linha": no.lineno})
            elif "\n" in no.value or "\r" in no.value:
                # O caos usa uma string multilinha. A posição no valor decodificado
                # não é linha física do arquivo (pode haver escapes/concatenação).
                for indice, linha in enumerate(no.value.splitlines(), 1):
                    if linha in textos:
                        encontrados[linha].append({"arquivo": nome, "linha_constante": no.lineno,
                            "linha_no_valor": indice, "correspondencia": "linha_literal_do_valor"})
    return encontrados, hashes


def aplicar_revisao(fila: list[dict], revisao: dict, exposicoes: dict) -> tuple[list[dict], dict]:
    """Decisões explícitas cobrem a fila inteira; não há classificação por default."""
    if revisao.get("origem_rotulo") != "curadoria_ia":
        raise ValueError("este artefato declara somente curadoria IA")
    if len({c["id"] for c in fila}) != len(fila) or not fila:
        raise ValueError("fila vazia ou IDs repetidos")
    decisoes = {}
    for grupo in revisao["grupos"]:
        if not isinstance(grupo.get("motivo"), str) or not grupo["motivo"].strip():
            raise ValueError("decisão exige justificativa")
        if grupo.get("enquadramento") not in {"supervisionado", "fora_perfil"}:
            raise ValueError("enquadramento inválido")
        if any(grupo.get(k) is not False for k in FLAGS):
            raise ValueError("revisão não autoriza efeitos")
        for indice in grupo["indices_fila"]:
            if type(indice) is not int or not 1 <= indice <= len(fila) or indice in decisoes:
                raise ValueError("índice inválido ou decisão repetida")
            decisoes[indice] = grupo
    if set(decisoes) != set(range(1, len(fila) + 1)):
        raise ValueError("revisão incompleta; ausência não significa fora do perfil")
    saida = []
    for indice, item in enumerate(fila, 1):
        if any(item.get(k) is not False for k in FLAGS):
            raise ValueError("fila precisa permanecer sem autoridade")
        if any(item.get(k) is not None for k in ("particao", "ancestrais", "anotacao")):
            raise ValueError("não sobrescrever revisão ou partição anterior")
        grupo = decisoes[indice]
        fonte = grupo.get("fonte_v4")
        if grupo["enquadramento"] == "supervisionado":
            if not isinstance(fonte, dict) or fonte.get("texto_entrada") != item["texto"]:
                raise ValueError("anotação não corresponde ao texto bruto")
            validar_fonte_relacional(fonte, variantes_permitidas=VARIANTES)
            _rotulos_brutos(fonte)
        elif fonte is not None:
            raise ValueError("fora do perfil não pode receber rótulo operacional")
        r = deepcopy(item)
        r.update({"origem_rotulo": "curadoria_ia", "revisao_encoder": "aguarda_revisao_humana",
                  "enquadramento": grupo["enquadramento"], "motivo": grupo["motivo"],
                  "anotacao": deepcopy(fonte), "exposicoes_literais": exposicoes.get(item["texto"], []),
                  "conhecido_no_desenvolvimento": True, "origem_evento_verificada": False,
                  "grupo_proposto": grupo["grupo"], **FLAGS})
        saida.append(r)
    cobertura = Counter(f"{n['intent']}|{n['action']}|{n['ato']}"
                        for c in saida if c["anotacao"] for n in c["anotacao"]["nos"])
    resumo = {"textos": len(saida), "enquadramentos": dict(Counter(c["enquadramento"] for c in saida)),
              "cobertura_anotada_ia": dict(cobertura),
              "textos_com_exposicao_literal": sum(bool(c["exposicoes_literais"]) for c in saida),
              "registros_associados_a_textos_expostos": sum(len(c["referencias"]) for c in saida if c["exposicoes_literais"]),
              "origens_de_evento_certificadas": 0, "revisoes_humanas": 0,
              "particoes_formadas": False, "dados_prontos": False,
              "limites": ["coincidencia_nao_identifica_evento", "ausencia_nao_prova_ineditismo",
                          "curadoria_ia_nao_e_revisao_humana", "fila_inteira_agora_conhecida_no_desenvolvimento",
                          "fora_perfil_nao_vira_negativo_ausente"], **FLAGS}
    return saida, resumo


def executar(fila_path: Path, revisao_path: Path, fontes: list[Path], destino: Path) -> dict[str, Any]:
    if destino.exists():
        raise FileExistsError("preservar artefato anterior")
    fila_bytes = fila_path.read_bytes()
    revisao_bytes = revisao_path.read_bytes()
    revisao = json.loads(revisao_bytes)
    fila_hash = hashlib.sha256(fila_bytes).hexdigest()
    if revisao.get("fila_sha256") != fila_hash:
        raise ValueError("fila diverge do snapshot revisado")
    fila = [json.loads(linha) for linha in fila_bytes.decode("utf-8").splitlines() if linha.strip()]
    exposicoes, hashes = cruzar_exposicao(fila, fontes)
    saida, resumo = aplicar_revisao(fila, revisao, exposicoes)
    hashes.update({str(fila_path.resolve()): fila_hash,
                   str(revisao_path.resolve()): hashlib.sha256(revisao_bytes).hexdigest()})
    if any(_hash(Path(p)) != esperado for p, esperado in hashes.items()):
        raise RuntimeError("fonte mudou durante revisão")
    resumo.update({"fontes_sha256": hashes, "codigo_sha256": _hash(Path(__file__))})
    serializada = "".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n" for c in saida)
    resumo["fila_revisada_sha256"] = hashlib.sha256(serializada.encode()).hexdigest()
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "fila_revisada.jsonl").open("x", encoding="utf-8", newline="\n") as f:
        f.write(serializada)
    with (destino / "resumo.json").open("x", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fila", type=Path, required=True)
    p.add_argument("--revisao", type=Path, required=True)
    p.add_argument("--fonte-python", type=Path, action="append", default=[])
    p.add_argument("--destino", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(executar(a.fila, a.revisao, a.fonte_python, a.destino), ensure_ascii=False))
