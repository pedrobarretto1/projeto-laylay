"""Treino isolado de negação: comparação pareada, sem promoção ou execução."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import copy
import hashlib
import json
import math
import re
from pathlib import Path
import subprocess

import joblib
from sklearn.base import clone
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline

from mente_laylay.especialistas.capacidades import intents_registradas
from .avaliacao import head_aplicavel
from .comparacao_linguistica import comparar_pedidos, criar_preditor_neural, prever_python_sem_contexto
from .dataset import carregar_jsonl, validar_exemplo
from .datasets.gerar_escopo_negacao_v1 import gerar_exemplos
from .datasets.gerar_escopo_negacao_v2 import gerar_grade
from .modelo import carregar_modelo
from .qualidade import _normalizar_texto, auditar_leakage_dataset
from .representacao_integral import criar_extrator_texto_integral_v1
from .representacao_sinais_atomicos import criar_extrator_sinais_atomicos
from .treino import _hash_dados


def grupos_sem_duplicatas(exemplos: list[dict]) -> list[str]:
    """Une grupos com textos normalizados idênticos antes de particionar."""
    pais: dict[str, str] = {}
    textos: dict[str, tuple[str, bool]] = {}
    grupos = []
    def raiz(g: str) -> str:
        while pais[g] != g:
            g = pais[g]
        return g
    for item in exemplos:
        grupo = str(item.get("validation_group") or item.get("family") or "").strip()
        if not grupo or type(item.get("negated")) is not bool:
            raise ValueError("grupo e rótulo explícitos são obrigatórios")
        pais.setdefault(grupo, grupo)
        texto = _normalizar_texto(item["text"])
        if not texto:
            raise ValueError("texto vazio")
        if texto in textos:
            anterior, rotulo = textos[texto]
            if rotulo != item["negated"]:
                raise ValueError("texto duplicado com negações contraditórias")
            pais[raiz(grupo)] = raiz(anterior)
        else:
            textos[texto] = grupo, item["negated"]
        grupos.append(grupo)
    return [raiz(g) for g in grupos]


def medir_negacao(exemplos: list[dict], previsoes: list[bool]) -> dict:
    pares = list(zip(exemplos, previsoes, strict=True))
    erros = [i for i, p in pares if i["negated"] != bool(p)]
    return {
        "total": len(pares), "acertos": len(pares) - len(erros),
        "negacoes_perdidas": sum(i["negated"] for i in erros),
        "negacoes_falsas": sum(not i["negated"] for i in erros),
        "erros_por_grupo": dict(Counter(i.get("validation_group", i["family"]) for i in erros)),
    }


def ajustar_cabeca(prototipo, exemplos: list[dict], *, pesos: list[float] | None = None):
    valores = [1.0] * len(exemplos) if pesos is None else list(pesos)
    if len(valores) != len(exemplos) or any(not math.isfinite(p) or p <= 0 for p in valores):
        raise ValueError("pesos devem ser positivos, finitos e alinhados aos exemplos")
    pares = [(i, p) for i, p in zip(exemplos, valores, strict=True) if head_aplicavel(i, "negation")]
    itens = [i for i, _ in pares]
    if {i["negated"] for i in itens} != {True, False}:
        raise ValueError("treino exige ambas as classes de negação")
    candidato = clone(prototipo)
    parametros = {} if all(p == 1 for _, p in pares) else {
        f"{candidato.steps[-1][0]}__sample_weight": [p for _, p in pares],
    }
    return candidato.fit([i["text"] for i in itens], [i["negated"] for i in itens], **parametros)


def criar_prototipo_negacao(cabeca, representacao: str):
    """Ablaciona canais sem alterar o extrator serializado em uso."""
    if representacao == "base":
        return clone(cabeca)
    if representacao not in {"integral", "combinada", "sinais_atomicos"}:
        raise ValueError("representação desconhecida")
    features = criar_extrator_sinais_atomicos(cabeca) if representacao == "sinais_atomicos" else criar_extrator_texto_integral_v1()
    if representacao == "combinada":
        features = FeatureUnion([
            ("legado", clone(cabeca.named_steps["features"])),
            ("integral", features),
        ])
    return Pipeline([
        ("features", features),
        ("classifier", clone(cabeca.named_steps["classifier"])),
    ])


def comparar_cv(prototipo, historicos: list[dict], novos: list[dict], splits: int = 4, *, prototipo_candidato=None, peso_novos: float = 1.0, eixo: str = "construcao") -> dict:
    if eixo not in {"construcao", "entidade"}:
        raise ValueError("eixo desconhecido")
    if not math.isfinite(peso_novos) or peso_novos <= 0:
        raise ValueError("peso_novos deve ser positivo e finito")
    historicos = [i for i in historicos if head_aplicavel(i, "negation")]
    novos = [i for i in novos if head_aplicavel(i, "negation")]
    itens = historicos + novos
    agrupados = [dict(i, validation_group=i.get("validation_entity_group") or i.get("validation_group") or i["family"]) for i in itens] if eixo == "entidade" else itens
    grupos = grupos_sem_duplicatas(agrupados)
    previsoes = {nome: [None] * len(itens) for nome in ("controle", "candidato")}
    folds = []
    for numero, (treino, teste) in enumerate(GroupKFold(n_splits=splits).split(itens, groups=grupos)):
        treino = list(map(int, treino))
        teste = list(map(int, teste))
        antigos = [i for i in treino if i < len(historicos)]
        assert not {grupos[i] for i in treino} & {grupos[i] for i in teste}
        for nome, indices in (("controle", antigos), ("candidato", treino)):
            escolhido = prototipo_candidato if nome == "candidato" and prototipo_candidato is not None else prototipo
            pesos = [peso_novos if nome == "candidato" and i >= len(historicos) else 1.0 for i in indices]
            cabeca = ajustar_cabeca(escolhido, [itens[i] for i in indices], pesos=pesos)
            for i, previsto in zip(teste, cabeca.predict([itens[i]["text"] for i in teste]), strict=True):
                previsoes[nome][i] = bool(previsto)
        folds.append({
            "fold": numero, "treino_historico": len(antigos),
            "treino_novo": len(treino) - len(antigos), "teste": len(teste),
            "grupos_teste": sorted({grupos[i] for i in teste}),
            "sha256_ids_teste": _hash_dados(teste),
        })
    fatias = {}
    for fatia, indices in (
        ("historica", list(range(len(historicos)))),
        ("nova", list(range(len(historicos), len(itens)))),
    ):
        fatias[fatia] = {
            nome: medir_negacao([itens[i] for i in indices], [valores[i] for i in indices])
            for nome, valores in previsoes.items()
        }
        fatias[fatia]["ganhos"] = sum(
            previsoes["controle"][i] != itens[i]["negated"] == previsoes["candidato"][i] for i in indices
        )
        fatias[fatia]["regressoes"] = sum(
            previsoes["controle"][i] == itens[i]["negated"] != previsoes["candidato"][i] for i in indices
        )
    return {"fatias": fatias, "folds": folds, "grupos_unicos": len(set(grupos)), "eixo": eixo}


def validar_reserva_entidades(treino: list[dict], reservas: list[dict]) -> dict:
    """Impede usar alvos reservados no histórico ou no novo treino."""
    treino_normal = [_normalizar_texto(i["text"]) for i in treino]
    reservadas = sorted({e for i in reservas if i["particao"] in {"entidade", "ambas"} for e in i["entidades"]})
    vistas = [e for e in reservadas if any(re.search(r"(?<!\w)" + re.escape(_normalizar_texto(e)) + r"(?!\w)", texto) for texto in treino_normal)]
    if vistas:
        raise ValueError(f"entidades reservadas presentes no treino: {vistas}")
    textos_treino = set(treino_normal)
    if any(_normalizar_texto(i["text"]) in textos_treino for i in reservas):
        raise ValueError("frase reservada duplicada no treino")
    return {"entidades_reservadas": reservadas, "entidades_vistas_no_treino": [], "frases_duplicadas": 0}


def executar_experimento(*, modelo_path: Path, historico_path: Path, bateria_path: Path, destino: Path, representacao: str = "base", peso_novos: float = 1.0, protocolo: str = "v1") -> dict:
    if protocolo not in {"v1", "entidades_v2"}:
        raise ValueError("protocolo desconhecido")
    if not math.isfinite(peso_novos) or peso_novos <= 0:
        raise ValueError("peso_novos deve ser positivo e finito")
    if representacao not in {"base", "integral", "combinada", "sinais_atomicos"}:
        raise ValueError("representação desconhecida")
    if destino.exists():
        raise FileExistsError("destino já existe; não sobrescrever experimento")
    raiz = Path(__file__).resolve().parents[2]
    datasets = raiz / "mente_laylay/neural/datasets"
    rel_treino = json.loads((historico_path / "ultimo_relatorio_treino.json").read_text(encoding="utf-8"))
    manifesto = json.loads((historico_path / "validacao_cruzada_heads.json").read_text(encoding="utf-8"))
    catalogo = intents_registradas()
    dev = carregar_jsonl(datasets / "dev_v0.jsonl", intents_permitidas=catalogo)
    lotes = [
        item for nome in manifesto["dataset"]["lotes_candidatos"]
        for item in carregar_jsonl(datasets / "candidatos" / nome, intents_permitidas=catalogo)
    ]
    if _hash_dados(lotes) != rel_treino["dataset"]["lotes_candidatos_sha256"]:
        raise ValueError("hash dos lotes históricos mudou")
    if hashlib.sha256((datasets / "dev_v0.jsonl").read_bytes()).hexdigest() != rel_treino["dataset"]["dev_sha256"]:
        raise ValueError("hash do DEV histórico mudou")
    historicos = dev + lotes
    grade = gerar_grade() if protocolo == "entidades_v2" else []
    reservas_v2 = [i for i in grade if i["particao"] != "treino"]
    novos = [validar_exemplo(i, intents_permitidas=catalogo) for i in (grade if grade else gerar_exemplos()) if i.get("particao", "treino") == "treino"]
    auditoria_reserva = validar_reserva_entidades(historicos + novos, reservas_v2) if grade else {}
    bateria = json.loads(bateria_path.read_text(encoding="utf-8"))
    frozen = carregar_jsonl(datasets / "frozen_v0.jsonl", intents_permitidas=catalogo)
    reservas = frozen + [{"text": c["text"], "family": c["id"]} for c in bateria["casos"]]
    auditorias = {
        "historico": auditar_leakage_dataset(novos, historicos),
        "diagnosticos": auditar_leakage_dataset(novos, reservas),
    }
    if not all(a["aprovado"] for a in auditorias.values()):
        raise ValueError("lote com sobreposição: " + json.dumps({k: a["totais"] for k, a in auditorias.items()}))
    modelo_hash = hashlib.sha256(modelo_path.read_bytes()).hexdigest()
    modelo = carregar_modelo(modelo_path)
    cabeca = modelo.cabeca_negacao
    controle = ajustar_cabeca(cabeca, historicos)
    textos = [i["text"] for i in historicos + novos]
    if list(controle.predict(textos)) != list(cabeca.predict(textos)):
        raise ValueError("reconstrução histórica não reproduziu a cabeça configurada")
    print("Base reconstruída; auditorias sem sobreposição. Iniciando CV pareada.", flush=True)
    # Congela a reserva e os parâmetros antes de treinar o candidato.
    destino.mkdir(parents=True, exist_ok=False)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as arquivo:
        json.dump({"protocolo": protocolo, "representacao": representacao, "peso_novos": peso_novos,
                   "sha256_treino": _hash_dados(historicos + novos), "reservas": reservas_v2,
                   "sha256_reserva": _hash_dados(reservas_v2), "autoriza_promocao": False}, arquivo, ensure_ascii=False, indent=2)
    prototipo = criar_prototipo_negacao(cabeca, representacao)
    cv = comparar_cv(cabeca, historicos, novos, prototipo_candidato=prototipo, peso_novos=peso_novos)
    cv_entidades = comparar_cv(cabeca, historicos, novos, prototipo_candidato=prototipo, peso_novos=peso_novos, eixo="entidade") if grade else {}
    cabeca_candidata = ajustar_cabeca(prototipo, historicos + novos, pesos=[1.0] * len(historicos) + [peso_novos] * len(novos))
    candidato = copy(modelo)
    candidato.cabeca_negacao = cabeca_candidata
    candidato.versao = modelo.versao + f"_escopo_negacao_v1_{representacao}_nao_promovido"
    diagnostico = comparar_pedidos(bateria, python=prever_python_sem_contexto, neural=criar_preditor_neural(candidato))
    # Prova pelo modelo completo de que a troca não alterou nenhum outro head.
    for caso in bateria["casos"]:
        antes, depois = modelo.prever(caso["text"]), candidato.prever(caso["text"])
        antes.pop("negated"); depois.pop("negated")
        antes["confidence"].pop("negation"); depois["confidence"].pop("negation")
        if antes != depois:
            raise AssertionError("outro head mudou")
    fatias = cv["fatias"]
    motivos = []
    for nome, valores in fatias.items():
        for metrica in ("negacoes_perdidas", "negacoes_falsas"):
            if valores["candidato"][metrica] > valores["controle"][metrica]:
                motivos.append(f"regressao_{nome}_{metrica}")
    if fatias["nova"]["candidato"]["acertos"] <= fatias["nova"]["controle"]["acertos"]:
        motivos.append("sem_ganho_novo")
    if hashlib.sha256(modelo_path.read_bytes()).hexdigest() != modelo_hash:
        raise AssertionError("artefato base mudou durante o experimento")
    relatorio = {
        "autoriza_promocao": False, "autoriza_execucao": False,
        "representacao_candidata": representacao,
        "peso_novos": peso_novos,
        "protocolo": protocolo,
        "cv_entidades": cv_entidades,
        "auditoria_reserva": auditoria_reserva,
        "reserva_v2": {
            particao: {
                nome: medir_negacao(fatia, list(c.predict([i["text"] for i in fatia])))
                for nome, c in (("base", cabeca), ("candidato", cabeca_candidata))
            }
            for particao in ("entidade", "construcao", "ambas")
            if (fatia := [i for i in reservas_v2 if i["particao"] == particao])
        },
        "ajuste_no_proprio_lote": medir_negacao(novos, list(cabeca_candidata.predict([i["text"] for i in novos]))),
        "gate_local": {"aprovado": not motivos, "motivos": motivos},
        "limites": ["CV só da cabeça de negação", "bateria e Frozen conhecidos, não reserva inédita", "sem validação no runtime completo"],
        "proveniencia": {
            "sha256_modelo": modelo_hash, "modelo": str(modelo_path),
            "sha256_novos": _hash_dados(novos), "sha256_historicos": _hash_dados(historicos),
            "sha256_bateria": hashlib.sha256(bateria_path.read_bytes()).hexdigest(),
            "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
            "worktree": subprocess.check_output(["git", "status", "--short"], cwd=raiz, text=True, encoding="utf-8"),
            "sha256_componentes": {
                str(p.relative_to(raiz)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (Path(__file__).resolve(), datasets / "gerar_escopo_negacao_v1.py", datasets / "gerar_escopo_negacao_v2.py", raiz / "mente_laylay/neural/representacao_integral.py", raiz / "mente_laylay/neural/representacao_sinais_atomicos.py")
            },
        },
        "auditorias": auditorias, "cv": cv, "comparacao_bateria": diagnostico,
        "frozen_negacao": {
            nome: medir_negacao(frozen, list(c.predict([i["text"] for i in frozen])))
            for nome, c in (("base", cabeca), ("candidato", cabeca_candidata))
        },
        "outros_heads_preservados_na_bateria": True,
    }
    with (destino / "lote_negacao.jsonl").open("x", encoding="utf-8") as arquivo:
        for item in novos:
            arquivo.write(json.dumps(item, ensure_ascii=False) + "\n")
    # Apenas a cabeça experimental, nunca gravar um modelo ativo substituto.
    joblib.dump(cabeca_candidata, destino / "cabeca_negacao_nao_promovida.joblib")
    with (destino / "relatorio.json").open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
    return relatorio


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--modelo", type=Path, required=True)
    p.add_argument("--historico", type=Path, required=True)
    p.add_argument("--bateria", type=Path, required=True)
    p.add_argument("--destino", type=Path, required=True)
    p.add_argument("--representacao", choices=("base", "integral", "combinada", "sinais_atomicos"), default="base")
    p.add_argument("--peso-novos", type=float, default=1.0)
    p.add_argument("--protocolo", choices=("v1", "entidades_v2"), default="v1")
    a = p.parse_args()
    r = executar_experimento(modelo_path=a.modelo, historico_path=a.historico, bateria_path=a.bateria, destino=a.destino, representacao=a.representacao, peso_novos=a.peso_novos, protocolo=a.protocolo)
    print(json.dumps({"gate": r["gate_local"], "cv": r["cv"]["fatias"], "bateria": r["comparacao_bateria"]["metricas"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
