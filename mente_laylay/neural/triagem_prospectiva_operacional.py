"""Governed triage for prospectively collected operational review candidates.

This module never upgrades AI curation into human review, training data, model
promotion, or execution authority. It only binds explicit triage decisions to
an immutable prospective queue and keeps repeated texts grouped.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .supervisao_operacional_v1 import VARIANTES


STATUS_PERMITIDOS = frozenset({
    "candidato_literal",
    "contextual",
    "agendado",
    "fora_perfil",
})


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _texto_normalizado(texto: object) -> str:
    return " ".join(str(texto or "").strip().casefold().split())


def _grupo_texto(texto: object) -> str:
    normalizado = _texto_normalizado(texto)
    if not normalizado:
        raise ValueError("texto pendente vazio")
    return "texto_" + hashlib.sha256(normalizado.encode("utf-8")).hexdigest()


def _carregar_fila(caminho: str | Path) -> tuple[list[dict[str, Any]], bytes]:
    path = Path(caminho)
    bruto = path.read_bytes()
    itens: list[dict[str, Any]] = []
    for numero, linha in enumerate(bruto.decode("utf-8").splitlines(), 1):
        if not linha.strip():
            continue
        valor = json.loads(linha)
        if not isinstance(valor, dict):
            raise ValueError(f"fila linha {numero} nao e objeto")
        itens.append(dict(valor))
    return itens, bruto


def _carregar_resumo(caminho: str | Path) -> dict[str, Any]:
    valor = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if not isinstance(valor, dict):
        raise ValueError("resumo da fila invalido")
    return dict(valor)


def preparar_triagem(
    fila_path: str | Path,
    resumo_path: str | Path,
    manifesto: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate an exhaustive AI-curation manifest against a frozen queue."""
    if not isinstance(manifesto, Mapping):
        raise TypeError("manifesto deve ser mapeamento")
    if int(manifesto.get("versao") or 0) != 1:
        raise ValueError("versao de manifesto desconhecida")
    if str(manifesto.get("origem_decisao") or "").strip().casefold() != "curadoria_ia":
        raise ValueError("triagem exige origem curadoria_ia")
    if manifesto.get("revisao_humana") is not False:
        raise ValueError("curadoria IA nao pode declarar revisao humana")
    if any(
        manifesto.get(chave) is not False
        for chave in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")
    ):
        raise ValueError("manifesto nao pode conceder autoridade")

    fila, bruto = _carregar_fila(fila_path)
    resumo_fonte = _carregar_resumo(resumo_path)
    sha_fila = _sha256_bytes(bruto)
    if resumo_fonte.get("fila_sha256") != sha_fila:
        raise ValueError("SHA da fila diverge do resumo congelado")
    if manifesto.get("fonte_fila_sha256") != sha_fila:
        raise ValueError("manifesto deve declarar o SHA exato da fila de origem")
    if any(
        resumo_fonte.get(chave) is not False
        for chave in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")
    ):
        raise ValueError("fonte da triagem contem autoridade")
    if resumo_fonte.get("dados_prontos") is not False:
        raise ValueError("fonte nao pode estar marcada como dados prontos")

    pendentes = {
        indice: item
        for indice, item in enumerate(fila, 1)
        if item.get("destinacao") == "revisao_pendente"
    }
    decisoes = manifesto.get("decisoes")
    if not isinstance(decisoes, list):
        raise ValueError("manifesto precisa listar decisoes")

    por_indice: dict[int, dict[str, Any]] = {}
    for decisao in decisoes:
        if not isinstance(decisao, Mapping):
            raise ValueError("decisao invalida")
        indice = decisao.get("indice_fila")
        if type(indice) is not int or indice <= 0 or indice in por_indice:
            raise ValueError("manifesto deve cobrir pendentes sem duplicacao")
        por_indice[indice] = dict(decisao)

    if set(por_indice) != set(pendentes):
        raise ValueError(
            "manifesto deve cobrir todos os revisao_pendente exatamente uma vez"
        )

    saida: list[dict[str, Any]] = []
    for indice in sorted(pendentes):
        origem = pendentes[indice]
        decisao = por_indice[indice]
        status = str(decisao.get("status") or "").strip().casefold()
        motivo = str(decisao.get("motivo") or "").strip()
        if status not in STATUS_PERMITIDOS or not motivo:
            raise ValueError(f"decisao {indice} sem status/motivo valido")

        intent = str(decisao.get("intent_proposta") or "").strip().upper()
        action = str(decisao.get("action_proposta") or "").strip().casefold()
        if status == "candidato_literal":
            if (intent, action) not in VARIANTES:
                raise ValueError(
                    f"decisao {indice}: variante proposta fora do perfil"
                )
        elif intent or action:
            raise ValueError(
                f"decisao {indice}: somente candidato_literal recebe variante"
            )

        texto = origem.get("texto")
        item = {
            "indice_fila": indice,
            "id_fonte": str(origem.get("id") or ""),
            "texto": texto,
            "sha256_texto": hashlib.sha256(
                str(texto or "").encode("utf-8")
            ).hexdigest(),
            "grupo_texto": _grupo_texto(texto),
            "status": status,
            "motivo": motivo,
            "origem_decisao": "curadoria_ia",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
            "referencias": deepcopy(origem.get("referencias") or []),
        }
        if status == "candidato_literal":
            item["intent_proposta"] = intent
            item["action_proposta"] = action
        saida.append(item)

    grupos = Counter(item["grupo_texto"] for item in saida)
    candidatos_literais = [
        item for item in saida if item["status"] == "candidato_literal"
    ]
    grupos_candidatos_literais = Counter(
        item["grupo_texto"] for item in candidatos_literais
    )
    status_contagem = Counter(item["status"] for item in saida)
    return {
        "versao": 1,
        "fonte_fila_sha256": sha_fila,
        "contrato": {
            "uso": "fila_revisao_operacional",
            "revisao_humana": False,
            "dados_prontos_para_treino": False,
            "treino_permitido": False,
            "autoriza_execucao": False,
            "autoriza_promocao": False,
        },
        "resumo": {
            "total_pendentes": len(saida),
            "status": dict(sorted(status_contagem.items())),
            "textos_distintos_pendentes": len(grupos),
            "eventos_repetidos": sum(valor - 1 for valor in grupos.values()),
            "grupos_texto_repetidos": sum(
                1 for valor in grupos.values() if valor > 1
            ),
            "candidatos_literais_eventos": len(candidatos_literais),
            "candidatos_literais_textos_distintos": len(
                grupos_candidatos_literais
            ),
            "candidatos_literais_eventos_repetidos": sum(
                valor - 1 for valor in grupos_candidatos_literais.values()
            ),
        },
        "itens": saida,
    }


def escrever_triagem(
    fila_path: str | Path,
    resumo_path: str | Path,
    manifesto_path: str | Path,
    destino: str | Path,
) -> dict[str, Any]:
    """Write a new immutable triage directory after full validation."""
    destino_path = Path(destino)
    if destino_path.exists():
        raise FileExistsError("preservar triagem anterior")
    manifesto_bytes = Path(manifesto_path).read_bytes()
    manifesto = json.loads(manifesto_bytes.decode("utf-8"))
    resultado = preparar_triagem(fila_path, resumo_path, manifesto)
    resultado["manifesto_sha256"] = _sha256_bytes(manifesto_bytes)

    destino_path.mkdir(parents=True, exist_ok=False)
    itens = resultado.pop("itens")
    with (destino_path / "fila_revisao.jsonl").open(
        "x", encoding="utf-8", newline="\n"
    ) as arquivo:
        for item in itens:
            arquivo.write(
                json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n"
            )
    (destino_path / "resumo.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return resultado
