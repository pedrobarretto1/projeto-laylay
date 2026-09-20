"""Prontidão e exportação de supervisão para o piloto de encoder, sem fit.

Reutiliza a anotação v4, a projeção de rótulos e o auditor de leakage.
Metadados não certificam revisão humana nem independência estatística.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
from itertools import combinations
import json
from pathlib import Path
from typing import Any

from .candidato_relacional import tokens
from .comparar_ocorrencias_v4 import carregar_perfil, rotular_ocorrencias, ROTULOS
from .preparar_lote_relacional_v3 import VARIANTES
from .qualidade import auditar_leakage_dataset
from .supervisao_relacoes_v4 import FLAGS, validar_fonte_relacional

PARTICOES = ("desenvolvimento", "treino", "selecao", "calibracao")
SEMENTES = (27, 53, 89)
CAMPOS = {"id", "texto", "grupo", "ancestrais", "particao", "origem_texto",
          "referencia_texto", "origem_rotulo", "referencia_rotulo", "conhecido_no_desenvolvimento",
          "enquadramento", "motivo_fora_perfil", "fonte_v4", *FLAGS}


def _rotulos_brutos(fonte: dict[str, Any]) -> list[str]:
    """Adapta offsets já anotados à projeção existente, sem chamar o parser.

Um único segmento aqui é sistema de coordenadas do TEXTO BRUTO, não uma
segmentação operacional. Não há inferência de verbo, ato, alvo ou permissão.
"""
    texto = fonte["texto_entrada"]
    nos = [{"intent": n["intent"], "action": n["action"], "ato": n["ato"],
            "ancora": {**n["ancora"], "segmento": 0}} for n in fonte["nos"]]
    return rotular_ocorrencias({"alinhado": {
        "entrada": {"texto_entrada": texto, "segmentos": [{"indice": 0, "texto": texto}]},
        "supervisao": {"nos": nos},
    }})


def validar_caso(caso: dict[str, Any]) -> None:
    """Valida declaração/offsets; NÃO interpreta a fala nem inventa rótulos."""
    if not isinstance(caso, dict) or set(caso) != CAMPOS:
        raise ValueError("campos do caso incompletos ou desconhecidos")
    for chave in ("id", "texto", "grupo", "referencia_texto", "referencia_rotulo"):
        if not isinstance(caso[chave], str) or not caso[chave].strip():
            raise ValueError(f"metadado vazio: {chave}")
    if any(caso[k] is not False for k in FLAGS):
        raise ValueError("corpus não autoriza treino, execução ou promoção")
    if type(caso["conhecido_no_desenvolvimento"]) is not bool:
        raise ValueError("exposição anterior precisa ser explícita")
    if caso["particao"] not in PARTICOES:
        raise ValueError("partição fora do piloto; reserva não entra neste leitor")
    if caso["origem_texto"] not in {"sintetico", "uso_real"}:
        raise ValueError("origem do texto desconhecida")
    if caso["origem_rotulo"] not in {"curadoria_ia", "revisao_humana", "pendente"}:
        raise ValueError("origem do rótulo desconhecida")
    pais = caso["ancestrais"]
    if pais is not None and (not isinstance(pais, list) or any(
            not isinstance(p, str) or not p.strip() for p in pais) or len(set(pais)) != len(pais)):
        raise ValueError("linhagem inválida; desconhecida deve ser null")
    if caso["enquadramento"] == "fora_perfil":
        if caso["fonte_v4"] is not None or not isinstance(caso["motivo_fora_perfil"], str) or not caso["motivo_fora_perfil"].strip():
            raise ValueError("fora do perfil exige motivo e não pode carregar rótulo operacional")
        return
    if caso["enquadramento"] != "supervisionado" or caso["motivo_fora_perfil"] is not None:
        raise ValueError("enquadramento inconsistente")
    fonte = caso["fonte_v4"]
    if not isinstance(fonte, dict) or fonte.get("texto_entrada") != caso["texto"]:
        raise ValueError("supervisão não corresponde ao texto bruto")
    validar_fonte_relacional(fonte, variantes_permitidas=VARIANTES)
    spans = {(a, b) for _, a, b in tokens(caso["texto"])}
    if any((n["ancora"]["inicio"], n["ancora"]["fim"]) not in spans for n in fonte["nos"]):
        raise ValueError("âncora mult token exige outro perfil; não reduzir à força")
    _rotulos_brutos(fonte)  # Provar a exportabilidade antes de anunciar prontidão.


def _parentescos(casos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Componentes transitivos por grupo, identidade e ancestral conhecido."""
    pais: dict[str, str] = {}

    def raiz(x: str) -> str:
        pais.setdefault(x, x)
        while pais[x] != x:
            pais[x] = pais[pais[x]]
            x = pais[x]
        return x

    for c in casos:
        no = "caso:" + c["id"]
        for parente in ["grupo:" + c["grupo"], *["caso:" + a for a in c["ancestrais"] or []]]:
            pais[raiz(parente)] = raiz(no)
    componentes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in casos:
        componentes[raiz("caso:" + c["id"])].append(c)
    return [{"ids": sorted(c["id"] for c in cs), "particoes": sorted({c["particao"] for c in cs})}
            for cs in componentes.values() if len({c["particao"] for c in cs}) > 1]


def auditar_corpus(casos: list[dict[str, Any]]) -> dict[str, Any]:
    """Um corpus válido pode continuar NÃO pronto para preparar o treino."""
    if not isinstance(casos, list) or not casos:
        raise ValueError("corpus vazio")
    for caso in casos:
        validar_caso(caso)
    if len({c["id"] for c in casos}) != len(casos):
        raise ValueError("identificadores repetidos")
    cruzamentos = _parentescos(casos)
    por_particao = {p: [c for c in casos if c["particao"] == p] for p in PARTICOES}
    vazamentos, familias = [], []
    for a, b in combinations(PARTICOES, 2):
        aa, bb = por_particao[a], por_particao[b]
        if not aa or not bb:
            continue
        r = auditar_leakage_dataset(
            [{"text": c["texto"], "family": c["grupo"]} for c in aa],
            [{"text": c["texto"], "family": c["grupo"]} for c in bb],
        )
        if r["familias_compartilhadas"]:
            familias.append({"particoes": [a, b], "familias": r["familias_compartilhadas"]})
        for par in r["duplicados_exatos"] + r["quase_duplicados"]:
            # Relatório não republica texto pessoal nem parâmetros do usuário.
            vazamentos.append({"a": aa[par["linha_dev"] - 1]["id"],
                               "b": bb[par["linha_frozen"] - 1]["id"],
                               "similaridade": par["similaridade"]})
    motivos = []
    textos: dict[str, list[str]] = defaultdict(list)
    for c in casos: textos[c["texto"]].append(c["id"])
    repetidos = [ids for ids in textos.values() if len(ids) > 1]
    if cruzamentos: motivos.append("parentesco_entre_particoes")
    if vazamentos: motivos.append("leakage_lexical_entre_particoes")
    if familias: motivos.append("familias_compartilhadas_entre_particoes")
    if repetidos: motivos.append("textos_repetidos")
    cobertura = {}
    for p in PARTICOES[1:]:
        cs = por_particao[p]
        supervisionados = [c for c in cs if c["enquadramento"] == "supervisionado"]
        classes = {f"{n['intent']}|{n['action']}|{n['ato']}" for c in supervisionados for n in c["fonte_v4"]["nos"]}
        faltam = sorted(ROTULOS - {"ausente"} - classes)
        cobertura[p] = {"casos": len(cs), "supervisionados": len(supervisionados), "classes_ausentes": faltam,
                       "fora_perfil": len(cs) - len(supervisionados)}
        if faltam: motivos.append(f"cobertura_incompleta:{p}")
        if p in {"selecao", "calibracao"} and any(c["conhecido_no_desenvolvimento"] for c in cs):
            motivos.append(f"exposicao_anterior:{p}")
        if any(c["ancestrais"] is None for c in cs): motivos.append(f"linhagem_desconhecida:{p}")
        if any(c["origem_rotulo"] == "pendente" for c in supervisionados): motivos.append(f"rotulos_pendentes:{p}")
        if not any(c["origem_texto"] == "uso_real" and c["origem_rotulo"] == "revisao_humana"
                   for c in supervisionados):
            motivos.append(f"sem_uso_real_revisado:{p}")
    if len({c["grupo"] for c in por_particao["treino"] if c["enquadramento"] == "supervisionado"}) < 2:
        motivos.append("treino_com_menos_de_dois_grupos")
    return {"manifesto_valido": True, "dados_prontos_para_preparacao": not motivos,
            "motivos": motivos, "particoes": dict(Counter(c["particao"] for c in casos)),
            "cobertura": cobertura, "parentescos_cruzados": cruzamentos, "vazamentos_lexicais": vazamentos,
            "familias_compartilhadas": familias, "textos_repetidos_ids": repetidos,
            "fora_perfil": [{"id": c["id"], "motivo": c["motivo_fora_perfil"]}
                            for c in casos if c["enquadramento"] == "fora_perfil"],
            "revisao_humana_certificada_por_codigo": False,
            "avaliacao_independente_disponivel": False,
            "viabilidade_de_fit_verificada": False, **FLAGS}


def preparar_particao(casos: list[dict[str, Any]], particao: str) -> dict[str, Any]:
    """Consumidor fail-closed: gera entradas/rótulos, não autoriza um fit.

Não é válido chamar um treinador diretamente com o corpus anotado.
Metadados, ato e fronteiras gold nunca pertencem à entrada de inferência.
"""
    if particao not in PARTICOES[1:]:
        raise ValueError("somente treino/selecao/calibracao; nunca reserva")
    auditoria = auditar_corpus(casos)
    if not auditoria["dados_prontos_para_preparacao"]:
        raise ValueError("corpus não pronto: " + ", ".join(auditoria["motivos"]))
    saida, excluidos = [], []
    for c in casos:
        if c["particao"] != particao:
            continue
        if c["enquadramento"] == "fora_perfil":
            excluidos.append({"id": c["id"], "motivo": c["motivo_fora_perfil"]})
            continue
        saida.append({"id": c["id"], "entrada": {"texto": c["texto"]},
                      "rotulos": _rotulos_brutos(c["fonte_v4"])})
    return {"particao": particao, "exemplos": saida, "fora_perfil": excluidos,
            "rotulos_catalogo": sorted(ROTULOS), **FLAGS}


def importar_desenvolvimento_v4(casos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserva uso anterior, origem sintética e grupos; não cria reserva."""
    return [{"id": c["id"], "texto": c["fonte"]["texto_entrada"],
             "grupo": c["grupo_validacao"], "ancestrais": ["gerador_v4:" + c["grupo_construcao"]],
             "particao": "desenvolvimento", "origem_texto": "sintetico",
             "referencia_texto": "expansao_relacoes_v4_20260908/" + c["id"],
             "origem_rotulo": "curadoria_ia", "referencia_rotulo": "supervisao_relacoes_v4/" + c["id"],
             "conhecido_no_desenvolvimento": True, "enquadramento": "supervisionado",
             "motivo_fora_perfil": None, "fonte_v4": deepcopy(c["fonte"]), **FLAGS} for c in casos]


def executar_auditoria(destino: Path) -> dict[str, Any]:
    """Audita a base conhecida; nenhuma previsão, treino ou leitura de reserva."""
    if destino.exists():
        raise FileExistsError("preservar auditoria anterior")
    casos_v4, _ = carregar_perfil()
    casos = importar_desenvolvimento_v4(casos_v4)
    r = auditar_corpus(casos)
    protocolo = {"versao": 1, "sementes": SEMENTES, "origem": "desenvolvimento_v4_conhecido",
                 "condicoes": [{"nome": "congelado", "treinar_encoder": False},
                               {"nome": "ajustado", "treinar_encoder": True}],
                 "codigo_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 "corpus_sha256": hashlib.sha256(json.dumps(casos, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
                 "checkpoint_treinavel_fixado": False, "reserva": {"disponivel": False},
                 "comparacao_viavel": False,
                 "pendencias": ["checkpoint_tokenizer_e_cabeca_pareados", "ambiente_isolado_e_smoke_forward_backward",
                                "dados_naturais_revisados_e_particoes", "orcamento_e_selecao_fixados_antes_do_fit"],
                 **FLAGS}
    destino.mkdir(parents=True, exist_ok=False)
    for nome, dados in (("protocolo.json", protocolo), ("prontidao.json", r)):
        with (destino / nome).open("x", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    print(json.dumps(executar_auditoria(parser.parse_args().destino), ensure_ascii=False))
