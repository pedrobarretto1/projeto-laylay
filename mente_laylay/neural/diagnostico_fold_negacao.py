"""Reproduz um fold histórico para atribuição; não cria candidato promovível."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from sklearn.model_selection import GroupKFold

from mente_laylay.especialistas.capacidades import intents_registradas
from .avaliacao import head_aplicavel
from .dataset import carregar_jsonl
from .diagnostico_pistas_negacao import explicar_pistas, comparar_pistas
from .experimento_escopo_negacao import ajustar_cabeca, criar_prototipo_negacao, grupos_sem_duplicatas, medir_negacao
from .modelo import carregar_modelo
from .treino import _hash_dados


def diagnosticar_margem(itens: list[dict], scores: list[float]) -> dict:
    """Testa existência de limiar separador; não escolhe nem aplica limiar."""
    if len(itens) != len(scores) or not all(math.isfinite(s) for s in scores):
        raise ValueError("scores precisam ser finitos e alinhados")
    if {type(i.get("negated")) for i in itens} != {bool} or {i["negated"] for i in itens} != {False, True}:
        raise ValueError("margem exige ambas as classes booleanas")
    recusas = [(float(s), i["text"]) for i, s in zip(itens, scores) if i["negated"]]
    demais = [(float(s), i["text"]) for i, s in zip(itens, scores) if not i["negated"]]
    menor, maior = min(recusas), max(demais)
    return {"menor_score_recusa": menor, "maior_score_nao_recusa": maior,
            "existe_limiar_separador": maior[0] < menor[0],
            "margem": menor[0] - maior[0], "limiar_aplicado": False}


def selecionar_fold(itens: list[dict], cv: dict, grupo: str) -> tuple[list[int], list[int]]:
    """Reproduz IDs e grupos de TODOS os folds antes de selecionar um deles."""
    if cv.get("eixo") != "construcao":
        raise ValueError("diagnóstico exige CV por construção")
    grupos = grupos_sem_duplicatas(itens)
    encontrados = []
    for n, (treino, teste) in enumerate(GroupKFold(n_splits=len(cv["folds"])).split(itens, groups=grupos)):
        treino, teste = list(map(int, treino)), list(map(int, teste))
        ref = cv["folds"][n]
        grupos_teste = sorted({grupos[i] for i in teste})
        if ref["fold"] != n or ref["sha256_ids_teste"] != _hash_dados(teste) or ref["grupos_teste"] != grupos_teste:
            raise ValueError("fold não reproduz IDs/grupos históricos")
        if {grupos[i] for i in treino} & set(grupos_teste):
            raise ValueError("vazamento entre grupos")
        if grupo in grupos_teste:
            encontrados.append((treino, teste))
    if len(encontrados) != 1:
        raise ValueError("grupo precisa aparecer em exatamente um fold")
    return encontrados[0]


def diagnosticar(*, experimento: Path, anterior: Path, historico: Path, grupo: str, saida: Path) -> dict:
    if saida.exists():
        raise FileExistsError("preservar diagnóstico existente")
    ler = lambda p: json.loads(p.read_text(encoding="utf-8"))
    raiz = Path(__file__).resolve().parents[2]
    r, antigo = ler(experimento / "relatorio.json"), ler(anterior / "relatorio.json")
    if r["representacao_candidata"] != "sinais_atomicos" or antigo["representacao_candidata"] != "base":
        raise ValueError("comparação exige os candidatos atômico e lexical")
    if r["peso_novos"] != 1 or antigo["peso_novos"] != 1:
        raise ValueError("reprodução restrita ao peso original 1")
    # O runner anterior precede a adição da representação atômica. Não
    # atualizar seu hash: validar o código da rodada atual e registrar a
    # diferença antiga, além de reproduzir seus dados, folds e contagens.
    for nome, digest in r["proveniencia"]["sha256_componentes"].items():
        if hashlib.sha256((raiz / nome).read_bytes()).hexdigest() != digest:
            raise ValueError(f"componente do experimento mudou: {nome}")
    datasets = raiz / "mente_laylay/neural/datasets"
    catalogo = intents_registradas()
    manifesto = ler(historico / "validacao_cruzada_heads.json")
    hist = carregar_jsonl(datasets / "dev_v0.jsonl", intents_permitidas=catalogo)
    for nome in manifesto["dataset"]["lotes_candidatos"]:
        hist.extend(carregar_jsonl(datasets / "candidatos" / nome, intents_permitidas=catalogo))
    novos = carregar_jsonl(experimento / "lote_negacao.jsonl", intents_permitidas=catalogo)
    for rel in (r, antigo):
        if _hash_dados(hist) != rel["proveniencia"]["sha256_historicos"] or _hash_dados(novos) != rel["proveniencia"]["sha256_novos"]:
            raise ValueError("dados não reproduzem os experimentos")
    modelo_path = raiz / r["proveniencia"]["modelo"]
    modelo_hash = hashlib.sha256(modelo_path.read_bytes()).hexdigest()
    if modelo_hash != r["proveniencia"]["sha256_modelo"] or modelo_hash != antigo["proveniencia"]["sha256_modelo"]:
        raise ValueError("modelo configurado divergiu")
    hist = [i for i in hist if head_aplicavel(i, "negation")]
    novos = [i for i in novos if head_aplicavel(i, "negation")]
    itens = hist + novos
    treino, teste = selecionar_fold(itens, r["cv"], grupo)
    if (treino, teste) != selecionar_fold(itens, antigo["cv"], grupo):
        raise ValueError("experimentos não são pareados")
    fatia = [itens[i] for i in teste if i >= len(hist) and itens[i]["validation_group"] == grupo]
    if not fatia or any(itens[i].get("validation_group") == grupo for i in treino):
        raise ValueError("fatia ausente ou presente no treino")
    base = carregar_modelo(modelo_path).cabeca_negacao
    cabeças = {
        "controle": ajustar_cabeca(base, [itens[i] for i in treino if i < len(hist)]),
        "lexical": ajustar_cabeca(base, [itens[i] for i in treino]),
        "atomico": ajustar_cabeca(criar_prototipo_negacao(base, "sinais_atomicos"), [itens[i] for i in treino]),
    }
    medidas = {nome: medir_negacao(fatia, list(h.predict([i["text"] for i in fatia]))) for nome, h in cabeças.items()}
    margens = {nome: {f: diagnosticar_margem(lote, list(h.decision_function([i["text"] for i in lote])))
                      for f, lote in (("familia_nova", fatia), ("fold_completo", [itens[i] for i in teste]))}
               for nome, h in cabeças.items()}
    for nome, rel, chave in (("controle", r, "controle"), ("lexical", antigo, "candidato"), ("atomico", r, "candidato")):
        esperado = rel["cv"]["fatias"]["nova"][chave]["erros_por_grupo"].get(grupo, 0)
        if medidas[nome]["total"] - medidas[nome]["acertos"] != esperado:
            raise ValueError(f"erros não reproduzem o fold histórico: {nome}")
    casos = [{"esperado": i["negated"], "dominio": i["domain"],
              "explicacoes": {nome: explicar_pistas(h, i["text"]) for nome, h in cabeças.items()}} for i in fatia]
    # Controle diagnóstico: muda apenas a moldura da recusa, mantém o alvo.
    # Não entra em fit e não é uma nova métrica de generalização.
    pares = []
    prefixo = "não quero que você "
    for item in fatia:
        texto = item["text"]
        if item["negated"] and texto.startswith(prefixo):
            direto = "não " + texto[len(prefixo):]
            pares.append({"dominio": item["domain"], "comparacoes": {
                nome: comparar_pistas(h, texto, direto) for nome, h in cabeças.items()}})
    if hashlib.sha256(modelo_path.read_bytes()).hexdigest() != modelo_hash:
        raise ValueError("modelo mudou durante diagnóstico")
    resultado = {"somente_diagnostico": True, "autoriza_promocao": False, "autoriza_execucao": False,
                 "fit_apenas_reproducao_fold": True, "modelos_salvos": False, "grupo": grupo,
                 "treino": len(treino), "teste": len(teste), "sha256_ids_teste": _hash_dados(teste),
                 "sha256_modelo": modelo_hash, "medidas": medidas, "margens": margens, "casos": casos, "pares_diagnosticos": pares,
                 "componentes_anteriores_divergentes": [nome for nome, digest in antigo["proveniencia"]["sha256_componentes"].items()
                     if hashlib.sha256((raiz / nome).read_bytes()).hexdigest() != digest],
                 "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                            (experimento / "relatorio.json", anterior / "relatorio.json", Path(__file__),
                             raiz / "mente_laylay/neural/diagnostico_pistas_negacao.py")}}
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("x", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for nome in ("experimento", "anterior", "historico", "saida"):
        parser.add_argument("--" + nome, type=Path, required=True)
    parser.add_argument("--grupo", required=True)
    r = diagnosticar(**vars(parser.parse_args()))
    print(json.dumps(r["medidas"], ensure_ascii=False))


if __name__ == "__main__":
    main()
