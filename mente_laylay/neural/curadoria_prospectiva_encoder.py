"""Fila offline por evento: teste não é uso humano, contexto não é rótulo."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from .auditoria_shadow import ler_jsonl_tolerante
from .curadoria_encoder import _hash
from .supervisao_relacoes_v4 import FLAGS


def preparar_fila(coleta: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Preserva eventos e separa quarentena/testes de candidatos à revisão.

    Nenhuma categoria certifica autoria humana, completude do contexto ou
    prontidão de treino. Repetição textual não funde sessões nem turnos.
    """
    antes = _hash(coleta)
    if antes is None:
        raise FileNotFoundError(coleta)
    registros, invalidas = ler_jsonl_tolerante(coleta)
    ids = Counter(str(r.get("id") or "") for r in registros)
    turnos = Counter(str(r.get("turno_id")) for r in registros if r.get("turno_id") is not None)
    fila = []
    for indice, registro in enumerate(registros, 1):
        motivos = []
        entrada = registro.get("entrada")
        entrada = entrada if isinstance(entrada, dict) else {}
        texto = entrada.get("texto")
        identificador = str(registro.get("id") or "")
        if registro.get("tipo") != "entrada_prospectiva" or registro.get("versao") != 1:
            motivos.append("formato_nao_suportado")
        if not identificador or ids[identificador] != 1:
            motivos.append("identidade_registro_ausente_ou_duplicada")
        turno = registro.get("turno_id")
        if type(turno) is not int or turno <= 0 or turnos[str(turno)] != 1:
            motivos.append("identidade_turno_ausente_ou_duplicada")
        if not isinstance(texto, str) or not texto.strip():
            motivos.append("texto_ausente")
        elif entrada.get("truncado") is not False:
            motivos.append("texto_truncado_ou_fidelidade_desconhecida")
        elif (type(entrada.get("caracteres_originais")) is not int
              or entrada["caracteres_originais"] != len(texto)
              or entrada.get("sha256_original") != hashlib.sha256(texto.encode("utf-8")).hexdigest()):
            motivos.append("fidelidade_inconsistente")
        if (not registro.get("conversa_id") or not registro.get("sessao_conversa_ts")
                or registro.get("planejamento") != "concluido"):
            motivos.append("proveniencia_incompleta")
        if (any(registro.get(k) is not False for k in (*FLAGS, "apto_treino", "origem_humana_certificada"))
                or registro.get("anotacao") is not None or registro.get("particao") is not None
                or registro.get("origem_rotulo") != "pendente"):
            motivos.append("coleta_contem_autoridade_ou_supervisao")
        contexto = registro.get("contexto_anterior")
        if not isinstance(contexto, dict) or contexto.get("autoriza_execucao") is not False:
            motivos.append("contexto_fora_do_contrato")
        teste = registro.get("teste_declarado")
        origem = str(registro.get("origem_declarada") or "")
        if type(teste) is not bool or not origem or origem.casefold() == "presenca":
            motivos.append("origem_inconsistente")
        destino = ("quarentena" if motivos else "teste_declarado"
                   if teste or origem.casefold() == "roteiro_teste" else "revisao_pendente")
        fila.append({
            "id": f"prospectivo_{antes}_{indice}", "texto": texto,
            "destinacao": destino, "motivos": motivos,
            "origem_texto": "teste_declarado" if destino == "teste_declarado" else "desconhecida",
            "registro_origem": deepcopy(registro),
            "referencias": [{"arquivo": str(coleta.resolve()), "sha256": antes,
                             "indice_registro_valido": indice, "registro_id": identificador}],
            "ancestrais": None, "anotacao": None, "particao": None,
            "origem_rotulo": "pendente", "revisao_encoder": "pendente",
            "contexto_completo_certificado": False, **FLAGS,
        })
    if _hash(coleta) != antes:
        raise RuntimeError("coleta mudou durante leitura; exportação abortada")
    resumo = {
        "fonte": str(coleta.resolve()), "fonte_sha256": antes,
        "registros_validos_json": len(registros), "linhas_invalidas": invalidas,
        "destinacoes": dict(Counter(r["destinacao"] for r in fila)),
        "motivos_quarentena": dict(Counter(m for r in fila for m in r["motivos"])),
        "textos_distintos": len({r["texto"] for r in fila if isinstance(r["texto"], str)}),
        "revisoes_humanas_certificadas": 0, "particoes_formadas": False,
        "dados_prontos": False,
        "limites": ["sem_teste_declarado_nao_certifica_humano", "contexto_nao_e_rotulo",
                    "sem_anotacao_nao_vira_negativo", "indice_valido_nao_e_linha_fisica"], **FLAGS,
    }
    return fila, resumo


def executar(coleta: Path, destino: Path) -> dict[str, Any]:
    if destino.exists():
        raise FileExistsError("preservar revisão anterior")
    fila, resumo = preparar_fila(coleta)
    serializada = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in fila)
    resumo["codigo_sha256"] = _hash(Path(__file__))
    resumo["fila_sha256"] = hashlib.sha256(serializada.encode("utf-8")).hexdigest()
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "fila.jsonl").open("x", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(serializada)
    with (destino / "resumo.json").open("x", encoding="utf-8") as arquivo:
        json.dump(resumo, arquivo, ensure_ascii=False, indent=2)
    return resumo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coleta", type=Path, default=Path("memoria/neural/entradas_prospectivas.jsonl"))
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(executar(args.coleta, args.destino), ensure_ascii=False))
