"""Sonda de âncora/ato por token, sem alvos gold ou autoridade operacional."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import time
import warnings

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction import DictVectorizer
from sklearn.neural_network import MLPClassifier
from threadpoolctl import threadpool_limits
from tokenizers import Tokenizer

from .candidato_relacional import tokens, atributos_token, validar_entrada
from .comparar_contexto_semantico_v3 import PASTA_ENCODER, SHA_ENCODER, conferir_comprimentos
from .comparar_lote_estrutural_v3 import PARAMETROS_COMPARACAO
from .diagnosticar_head_relacional import medir_acoes
from .encoder_semantico import EncoderSemanticoONNX
from .expandir_relacoes_v4 import BASE, carregar_base, preparar_dobras
from .preparar_lote_relacional_v3 import VARIANTES

PASTA_FONTE = BASE / "memoria/neural/experimentos/expansao_relacoes_v4_20260908"
SHA_LOTE = "f389af34b78ecf540ce551867d27e21191d6855e8113410535a106392fb55a07"
ROTULOS = {"ausente"} | {f"{i}|{a}|{ato}" for i, a in VARIANTES for ato in ("pedido", "recusa", "relato")}
MODOS = ("janela_lexical", "janela_contextual")


def estado_ajuste(modelo: MLPClassifier) -> dict:
    """Escalares NumPy do fit viram metadados JSON, nunca flags de sucesso."""
    return {"iteracoes": int(modelo.n_iter_), "loss": float(modelo.loss_)}


def representar_tokens(entrada: dict) -> tuple[list, list[dict]]:
    validar_entrada(entrada)
    ts = tokens(entrada["texto_entrada"])
    if not ts:
        raise ValueError("entrada sem tokens")
    return ts, [atributos_token({}, ts, i, 0, 0) for i in range(len(ts))]


def rotular_ocorrencias(caso: dict) -> list[str]:
    """Gold só para fit/métrica: converte offsets canônicos em offsets brutos."""
    entrada = caso["alinhado"]["entrada"]
    ts, _ = representar_tokens(entrada)
    origem = entrada["texto_entrada"]
    segmentos = {s["indice"]: s["texto"] for s in entrada["segmentos"]}
    por_span = {(a, b): i for i, (_, a, b) in enumerate(ts)}
    ys, vistos = ["ausente"] * len(ts), set()
    for n in caso["alinhado"]["supervisao"]["nos"]:
        ancora = n["ancora"]
        s = segmentos[ancora["segmento"]]
        if origem.count(s) != 1:
            raise ValueError("projeção literal da âncora exige revisão")
        inicio = origem.index(s)
        span = (inicio + ancora["inicio"], inicio + ancora["fim"])
        if span not in por_span or origem[slice(*span)] != ancora["texto"] or span in vistos:
            raise ValueError("âncora incompatível com o perfil de um token por ocorrência")
        rotulo = f"{n['intent']}|{n['action']}|{n['ato']}"
        if rotulo not in ROTULOS:
            raise ValueError("variante/ato fora do perfil")
        ys[por_span[span]] = rotulo
        vistos.add(span)
    return ys


def alinhar_subtokens(texto: str, offsets: list, mascara: list, especiais: list, ocultos: np.ndarray) -> np.ndarray:
    """Média por interseção de caracteres, L2; um subtoken pode servir a dois tokens."""
    if (ocultos.shape != (len(offsets), 384) or not np.isfinite(ocultos).all()
            or len(mascara) != len(offsets) or len(especiais) != len(offsets)):
        raise ValueError("saída contextual inválida")
    saida = []
    for _, a, b in tokens(texto):
        indices = [i for i, (x, y) in enumerate(offsets) if mascara[i] and not especiais[i] and x < b and a < y]
        cobertos = {j for i in indices for j in range(*offsets[i])}
        if not indices or not set(range(a, b)) <= cobertos:
            raise ValueError("subtoken não cobre token literal")
        # Tokenizers pode juntar aspas/pontuação. Conserva as duas posições
        # literais e compartilha o estado, sem inventar uma separação interna.
        pesos = [min(b, offsets[i][1]) - max(a, offsets[i][0]) for i in indices]
        v = np.average(ocultos[indices], axis=0, weights=pesos)
        norma = np.linalg.norm(v)
        if not np.isfinite(norma) or norma < 1e-9:
            raise ValueError("vetor contextual sem norma válida")
        saida.append(v / norma)
    return np.asarray(saida, dtype=np.float32)


def codificar_contexto(textos: list[str], encoder: EncoderSemanticoONNX) -> list[np.ndarray]:
    """Adaptador OFFLINE da sessão existente; não altera o encoder de produção.

Usa os estados anteriores ao pooling da frase. O tokenizer desta instância
isolada foi auditado separadamente sem truncamento antes de chegar aqui.
"""
    conferir_comprimentos(textos, Tokenizer.from_file(str(encoder.caminho_tokenizer)), encoder.max_length)
    encoder.precarregar()
    saida = []
    for inicio in range(0, len(textos), encoder.batch_size):
        lote = textos[inicio:inicio + encoder.batch_size]
        cs = encoder._tokenizer.encode_batch(lote)
        inputs = {nome: np.asarray([getattr(c, atributo) for c in cs], dtype=np.int64)
                  for nome, atributo in (("input_ids", "ids"), ("attention_mask", "attention_mask"),
                                         ("token_type_ids", "type_ids"))}
        hs = encoder._sessao.run(None, inputs)[0]
        if hs.shape != (len(cs), len(cs[0].ids), 384):
            raise ValueError("ONNX não retornou estados por token esperados")
        saida.extend(alinhar_subtokens(t, c.offsets, c.attention_mask, c.special_tokens_mask, h)
                     for t, c, h in zip(lote, cs, hs))
    return saida


def medir(casos: list[dict], previstos: list[list[str]]) -> dict:
    if len(casos) != len(previstos) or len({c["id"] for c in casos}) != len(casos):
        raise ValueError("medição incompleta")
    chaves, esperados, saidas = [], [], []
    for c, pred in zip(casos, previstos):
        ts, _ = representar_tokens(c["alinhado"]["entrada"])
        gold = rotular_ocorrencias(c)
        if len(pred) != len(ts) or any(p not in ROTULOS for p in pred):
            raise ValueError("previsão incompleta ou fora do catálogo")
        for (_, inicio, _), e, p in zip(ts, gold, pred):
            for intent, action in sorted(VARIANTES):
                def projetar(rotulo):
                    if not rotulo.startswith(f"{intent}|{action}|"):
                        return "ausente"
                    ato = rotulo.split("|")[2]
                    return ato + ("/explicito" if ato == "pedido" else "/nao_aplicavel")
                # Campo 2 da chave é offset bruto da âncora, NÃO índice do segmento.
                chaves.append((c["id"], inicio, intent, action))
                esperados.append(projetar(e))
                saidas.append(projetar(p))
    return medir_acoes(chaves, esperados, saidas)


def carregar_perfil() -> tuple[list[dict], list[dict]]:
    carregar_base()  # Confere dependências e baseline v4 sem abrir reservas.
    bruto = (PASTA_FONTE / "lote.json").read_bytes()
    if hashlib.sha256(bruto).hexdigest() != SHA_LOTE:
        raise ValueError("lote do comparativo mudou")
    protocolo = json.loads((PASTA_FONTE / "protocolo.json").read_text(encoding="utf-8"))
    if hashlib.sha256(Path(__file__).with_name("expandir_relacoes_v4.py").read_bytes()).hexdigest() != protocolo["codigo_sha256"]:
        raise ValueError("código da expansão mudou")
    resultado = json.loads((PASTA_FONTE / "resultado.json").read_text(encoding="utf-8"))
    lote = json.loads(bruto)
    if any(lote[k] is not False for k in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")):
        raise ValueError("fonte sem isolamento")
    casos = lote["casos"]
    if len(casos) != 1176 or any(c["particao"] != "desenvolvimento" for c in casos):
        raise ValueError("perfil fora do desenvolvimento autorizado")
    dobras = preparar_dobras(casos, {c["id"]: c["grupo_validacao"] for c in casos})
    if not resultado["divisao_viavel"] or dobras != resultado["dobras"] or resultado["pares"] or resultado["repeticoes_locais"]:
        raise ValueError("partição não corresponde à auditoria congelada")
    return casos, dobras


def executar(destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar experimento anterior")
    casos, dobras = carregar_perfil()
    encoder = EncoderSemanticoONNX(PASTA_ENCODER, sha256_modelo=SHA_ENCODER, batch_size=16)
    encoder.validar_artefatos()
    textos = [c["alinhado"]["entrada"]["texto_entrada"] for c in casos]
    tamanhos = conferir_comprimentos(textos, Tokenizer.from_file(str(encoder.caminho_tokenizer)))
    gold = [rotular_ocorrencias(c) for c in casos]
    arquivos = [Path(__file__), *[Path(__file__).with_name(n) for n in (
        "candidato_relacional.py", "diagnosticar_head_relacional.py", "encoder_semantico.py",
        "comparar_contexto_semantico_v3.py", "comparar_lote_estrutural_v3.py", "expandir_relacoes_v4.py")]]
    protocolo = {"perfil": "sonda_ocorrencias_v4", "fonte_sha256": SHA_LOTE, "dobras": dobras,
        "parametros": PARAMETROS_COMPARACAO, "modos": MODOS, "encoder_sha256": SHA_ENCODER,
        "tokenizer_sha256": hashlib.sha256(encoder.caminho_tokenizer.read_bytes()).hexdigest(),
        "codigo_sha256": {str(p.relative_to(BASE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos},
        "python": platform.python_version(), "max_tokens": max(tamanhos),
        "supervisao_autorizada": "perfil derivado explícito dos 1176 casos; sidecars permanecem proibidos",
        "unidade": "todos os tokens brutos; 9 classes variante/ato e ausente; janela lexical +/-2",
        "controle": "MLP lexical adaptada à nova unidade, não head histórico nem modelo ativo",
        "candidato": "mesma MLP e janela + 384 estados contextuais por token; MiniLM congelado",
        "pooling_subtokens": "interseção por caracteres + L2; estado compartilhado se subtoken cruza pontuação",
        "gate": {"exatidao_minima": 0.95, "max_pedidos_inventados": 0, "max_extras": 0},
        "escopo": "âncora, variante e ato; relações e alvos NÃO avaliados",
        "limites": "um seed; desenvolvimento sintético; sem fine-tuning de Transformer",
        "fontes_tecnicas": ["https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                            "https://huggingface.co/docs/tokenizers/api/encoding"],
        "autoriza_execucao": False, "autoriza_promocao": False, "reservas_usadas": False}
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    inicio = time.perf_counter()
    ctx = codificar_contexto(textos, encoder)
    print(json.dumps({"encoder_segundos": time.perf_counter() - inicio, "tokens": sum(len(v) for v in ctx)}), flush=True)
    xs = [representar_tokens(c["alinhado"]["entrada"])[1] for c in casos]
    por_id = {c["id"]: i for i, c in enumerate(casos)}
    resultados = []
    with threadpool_limits(limits=1):
        for numero, dobra in enumerate(dobras):
            tr, te = ([por_id[i] for i in dobra[k]] for k in ("treino", "teste"))
            vectorizer = DictVectorizer(dtype=np.float32)
            xtr = vectorizer.fit_transform([x for i in tr for x in xs[i]])
            xte = vectorizer.transform([x for i in te for x in xs[i]])
            ytr = [y for i in tr for y in gold[i]]
            if set(ytr) != ROTULOS:
                raise ValueError("dobra sem classes completas")
            for modo in MODOS:
                matriz_tr, matriz_te = xtr, xte
                if modo == "janela_contextual":
                    matriz_tr = hstack((xtr, csr_matrix(np.vstack([ctx[i] for i in tr]))), format="csr")
                    matriz_te = hstack((xte, csr_matrix(np.vstack([ctx[i] for i in te]))), format="csr")
                modelo = MLPClassifier(**PARAMETROS_COMPARACAO)
                with warnings.catch_warnings(record=True) as avisos:
                    warnings.simplefilter("always")
                    modelo.fit(matriz_tr, ytr)
                def avaliar(ids, matriz):
                    pred, partes, cursor = modelo.predict(matriz).tolist(), [], 0
                    for i in ids:
                        tamanho = len(xs[i])
                        partes.append(pred[cursor:cursor + tamanho])
                        cursor += tamanho
                    return medir([casos[i] for i in ids], partes)
                m = {"modo": modo, "dobra": numero, "grupo": dobra["grupo_teste"],
                     "treino": avaliar(tr, matriz_tr), "teste": avaliar(te, matriz_te),
                     **estado_ajuste(modelo),
                     "avisos": [str(a.message) for a in avisos]}
                resultados.append(m)
                with (destino / f"{modo}_dobra_{numero}.json").open("x", encoding="utf-8") as f:
                    json.dump(m, f, ensure_ascii=False, indent=2)
                print(json.dumps({"modo": modo, "dobra": numero, "exatos": m["teste"]["casos_exatos_acao_sem_alvos"],
                    "casos": m["teste"]["casos"], "inventados": m["teste"]["pedidos_inventados"]}), flush=True)
    resumo = {}
    for modo in MODOS:
        ms = [m["teste"] for m in resultados if m["modo"] == modo]
        r = {k: sum(m[k] for m in ms) for k in ("casos", "casos_exatos_acao_sem_alvos", "acoes_esperadas",
             "acoes_ausentes", "acoes_extras", "pedidos_inventados")}
        r["taxa_exata"] = r["casos_exatos_acao_sem_alvos"] / r["casos"]
        r["media_por_grupo"] = sum(m["casos_exatos_acao_sem_alvos"] / m["casos"] for m in ms) / len(ms)
        r["apto_proxima_fronteira"] = r["taxa_exata"] >= .95 and r["pedidos_inventados"] == r["acoes_extras"] == 0
        resumo[modo] = r
    r = {"resumo": resumo, "segundos": time.perf_counter() - inicio,
         "modelo_completo_avaliado": False, "autoriza_promocao": False, "autoriza_execucao": False}
    with (destino / "resultado.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    print(json.dumps(executar(parser.parse_args().destino)["resumo"], ensure_ascii=False))
