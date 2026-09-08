"""Experimento offline: duas MLPs propõem relações, nunca efeitos/permissão.

Não é importado pelo runtime. A entrada de inferência contém somente texto e
segmentos. Não recebe spans, variantes esperadas ou decisões do porteiro.
"""
from __future__ import annotations

from collections import Counter
import re

from sklearn.feature_extraction import DictVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline

from .avaliacao_escopo import PAPEIS

PARAMETROS = dict(hidden_layer_sizes=(32,), solver="adam", alpha=0.001,
                  max_iter=180, random_state=27, early_stopping=False)


def tokens(texto: str) -> list[tuple[str, int, int]]:
    """Tokenização genérica; offsets literais, sem vocabulário de comandos."""
    return [(m.group(), m.start(), m.end()) for m in re.finditer(r"\w+|[^\w\s]", texto)]


def validar_entrada(entrada: dict) -> None:
    if set(entrada) != {"texto_entrada", "segmentos"}:
        raise ValueError("inferência aceita somente texto e segmentos")
    if not isinstance(entrada["texto_entrada"], str) or not entrada["texto_entrada"].strip():
        raise ValueError("entrada vazia")
    segmentos = entrada["segmentos"]
    if not isinstance(segmentos, list) or not segmentos:
        raise ValueError("segmentos vazios")
    vistos = set()
    for s in segmentos:
        if (set(s) != {"indice", "texto"} or type(s["indice"]) is not int
                or s["indice"] < 0 or s["indice"] in vistos
                or not isinstance(s["texto"], str) or not s["texto"].strip()):
            raise ValueError("segmento inválido ou com metadados proibidos")
        vistos.add(s["indice"])


def _lexico(texto: str, prefixo: str) -> dict:
    palavras = [t[0].casefold() for t in tokens(texto)]
    contagem = Counter(palavras)
    contagem.update(" ".join(par) for par in zip(palavras, palavras[1:]))
    return {prefixo + k: v for k, v in contagem.items()}


def atributos_acao(entrada: dict, posicao: int, variante: tuple[str, str]) -> dict:
    return {**_lexico(entrada["texto_entrada"], "entrada:"),
            **_lexico(entrada["segmentos"][posicao]["texto"], "dono:"),
            "variante": "/".join(variante), "posicao_dono": float(posicao),
            "total_segmentos": float(len(entrada["segmentos"]))}


def atributos_token(base: dict, ts: list, i: int, origem: int, dono: int) -> dict:
    palavra = ts[i][0]
    f = {**base, "distancia_segmentos": float(origem - dono),
         "posicao_token": i / max(1, len(ts) - 1), "capital": palavra[:1].isupper(),
         "sufixo2": palavra[-2:].casefold(), "sufixo3": palavra[-3:].casefold()}
    for deslocamento in range(-2, 3):
        j = i + deslocamento
        f[f"janela{deslocamento}"] = ts[j][0].casefold() if 0 <= j < len(ts) else "<BORDA>"
    return f


def rotulos_bio(texto: str, indice: int, acao: dict) -> list[str]:
    ts = tokens(texto)
    rotulos = ["O"] * len(ts)
    for papel in PAPEIS:
        for m in acao[papel]:
            if m["segmento"] != indice:
                continue
            indices = [i for i, (_, a, b) in enumerate(ts) if m["inicio"] <= a and b <= m["fim"]]
            if (not indices or ts[indices[0]][1] != m["inicio"]
                    or ts[indices[-1]][2] != m["fim"]):
                raise ValueError("menção não representável sem perder offsets")
            for n, i in enumerate(indices):
                if rotulos[i] != "O":
                    raise ValueError("papéis sobrepostos")
                rotulos[i] = ("B:" if n == 0 else "I:") + papel
    return rotulos


def decodificar_bio(texto: str, indice: int, rotulos: list[str]) -> dict:
    ts = tokens(texto)
    if len(ts) != len(rotulos):
        raise ValueError("quantidade de rótulos divergiu")
    saida = {p: [] for p in PAPEIS}
    atual = None
    for (palavra, a, b), rotulo in zip(ts, rotulos):
        if rotulo == "O":
            atual = None
            continue
        tipo, papel = rotulo.split(":", 1)
        if tipo not in {"B", "I"} or papel not in saida:
            raise ValueError("rótulo BIO inválido")
        if tipo == "B":
            atual = (papel, {"segmento": indice, "inicio": a, "fim": b, "texto": palavra})
            saida[papel].append(atual[1])
        elif atual is None or atual[0] != papel:
            # I órfão não vira início inventado. Falha fica visível na avaliação.
            raise ValueError("continuação BIO sem início compatível")
        else:
            atual[1].update(fim=b, texto=texto[atual[1]["inicio"]:b])
    return saida


class CandidatoRelacional:
    """Proponente experimental. Nenhum método executa nem autoriza comandos."""

    def ajustar(self, exemplos: list[dict]) -> "CandidatoRelacional":
        if not exemplos or any(e.get("perfil_treino") != "desenvolvimento_relacional_v1"
                               or e.get("papel_dataset") != "desenvolvimento"
                               for e in exemplos):
            raise ValueError("treino exige exportação explícita de desenvolvimento")
        self.variantes = sorted({(a["intent"], a["action"]) for e in exemplos
                                for s in e["segmentos_anotados"] for a in s["acoes"]})
        xs, ys, xt, yt = [], [], [], []
        for e in exemplos:
            entrada = e["entrada"]
            validar_entrada(entrada)
            acoes = {(s["indice"], a["intent"], a["action"]): a
                     for s in e["segmentos_anotados"] for a in s["acoes"]}
            for pos, s in enumerate(entrada["segmentos"]):
                for variante in self.variantes:
                    base = atributos_acao(entrada, pos, variante)
                    acao = acoes.get((s["indice"], *variante))
                    xs.append(base)
                    ys.append(acao["ato"] + "/" + acao["resolucao_alvo"] if acao else "ausente")
                    if acao is None:
                        continue
                    for origem, seg in enumerate(entrada["segmentos"]):
                        ts = tokens(seg["texto"])
                        xt.extend(atributos_token(base, ts, i, origem, pos) for i in range(len(ts)))
                        yt.extend(rotulos_bio(seg["texto"], seg["indice"], acao))
        if len(set(ys)) < 2 or len(set(yt)) < 2:
            raise ValueError("supervisão insuficiente para as duas cabeças")
        self.acoes = make_pipeline(DictVectorizer(), MLPClassifier(**PARAMETROS)).fit(xs, ys)
        self.papeis = make_pipeline(DictVectorizer(), MLPClassifier(**PARAMETROS)).fit(xt, yt)
        return self

    def prever(self, entrada: dict) -> list[dict]:
        validar_entrada(entrada)
        candidatos = [(pos, v, atributos_acao(entrada, pos, v))
                      for pos in range(len(entrada["segmentos"])) for v in self.variantes]
        rotulos = self.acoes.predict([c[2] for c in candidatos])
        saida = [{"indice": s["indice"], "acoes": []} for s in entrada["segmentos"]]
        for (pos, variante, base), rotulo in zip(candidatos, rotulos):
            if rotulo == "ausente":
                continue
            ato, resolucao = rotulo.split("/", 1)
            acao = {"intent": variante[0], "action": variante[1], "ato": ato,
                    "resolucao_alvo": resolucao, **{p: [] for p in PAPEIS}}
            for origem, s in enumerate(entrada["segmentos"]):
                ts = tokens(s["texto"])
                atributos = [atributos_token(base, ts, i, origem, pos) for i in range(len(ts))]
                mencoes = decodificar_bio(s["texto"], s["indice"], self.papeis.predict(atributos).tolist())
                for papel in PAPEIS:
                    acao[papel].extend(mencoes[papel])
            saida[pos]["acoes"].append(acao)
        return saida
