"""Prepara contrastes de supervisão; não treina, não abre reservas ou runtime."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

from .preparar_lote_relacional_v3 import PARES, VARIANTES, preencher, agrupar_sem_leakage
from .supervisao_relacoes_v4 import FLAGS, alinhar_relacoes, validar_fonte_relacional

FORMAS = {
    "direto": {"pedido": "{dono}{verbo} {a}", "recusa": "não {dono}{verbo} {a}",
               "relato": "ontem ela tentou {dono}{infinitivo} {a}"},
    "vontade": {"pedido": "quero que você {dono}{verbo} {a}", "recusa": "não quero que você {dono}{verbo} {a}",
                "relato": "ela contou que queria {dono}{infinitivo} {a}"},
    "necessidade": {"pedido": "preciso que você {dono}{verbo} {a}", "recusa": "não é para {dono}{infinitivo} {a}",
                   "relato": "o registro diz que ela foi {dono}{infinitivo} {a}"},
    "possibilidade": {"pedido": "pode {dono}{infinitivo} {a} agora", "recusa": "não vá {dono}{infinitivo} {a}",
                      "relato": "na sessão passada ela decidiu {dono}{infinitivo} {a}"},
}
COMPOSICOES = (("pedido",), ("recusa",), ("relato",),
              ("pedido", "recusa"), ("recusa", "pedido"),
              ("pedido", "relato"), ("relato", "pedido"))


def gerar_contrastes() -> list[dict]:
    """Moldes explícitos atribuem rótulos antes de consultar a linguagem real."""
    casos = []
    for familia, formas in FORMAS.items():
        for par, nomes in enumerate(PARES):
            for troca in (False, True):
                a, b = nomes[::-1] if troca else nomes
                dominios = (("apps", "APP_OPEN", "open", "abra", "abrir", "o aplicativo", a, b),
                    ("musica", "MUSIC_SEARCH", "search", "toque", "tocar", "a faixa", f"não volte {a}", f"não volte {b}"),
                    ("arquivos", "FILE_READ", "read", "leia", "ler", "o arquivo", f"não apagar {a}.txt", f"não apagar {b}.txt"))
                for dominio, intent, action, verbo, infinitivo, objeto, alvo_a, alvo_b in dominios:
                    for aspas in (False, True):
                        for atos in COMPOSICOES:
                            texto, nos = "", []
                            for i, ato in enumerate(atos):
                                alvo = alvo_a if len(atos) == 1 or ato == "pedido" else alvo_b
                                molde = formas[ato]
                                clausula, mencoes, ancora = preencher(molde,
                                    {"a": objeto + " " + (f'"{alvo}"' if aspas else alvo),
                                     "verbo": verbo, "infinitivo": infinitivo}, {"a": alvo})
                                if texto:
                                    texto += "; "
                                inicio = len(texto)
                                texto += clausula
                                v = verbo if "{verbo}" in molde else infinitivo
                                mencao = {**mencoes["a"], "inicio": mencoes["a"]["inicio"] + inicio,
                                          "fim": mencoes["a"]["fim"] + inicio}
                                nos.append({"id": f"n{i}", "intent": intent, "action": action, "ato": ato,
                                    "trecho": {"inicio": inicio, "fim": len(texto), "texto": clausula},
                                    "ancora": {"inicio": inicio + ancora, "fim": inicio + ancora + len(v), "texto": v},
                                    "alvos": [mencao]})
                            relacoes = []
                            if "pedido" in atos and "recusa" in atos:
                                relacoes = [{"tipo": "restringe", "origem": f"n{atos.index('recusa')}",
                                             "destino": f"n{atos.index('pedido')}"}]
                            fonte = {"versao": 4, "texto_entrada": texto, "nos": nos, "relacoes": relacoes, **FLAGS}
                            validar_fonte_relacional(fonte, variantes_permitidas=VARIANTES)
                            casos.append({"id": f"rel_v4_{familia}_{dominio}_e{par}_t{int(troca)}_q{int(aspas)}_" + "_".join(atos),
                                "grupo_construcao": familia, "grupo_entidades": f"par_{par}",
                                "grupo_contraste": f"{familia}_{dominio}_e{par}",
                                "particao": "desenvolvimento", "fonte": fonte})
    return casos


def agrupar_projecoes(casos: list[dict], grupos: dict[str, str]) -> tuple[dict, int]:
    """Une grupos com entradas locais iguais; rótulos não definem partições."""
    pais = {g: g for g in grupos.values()}

    def raiz(g):
        while pais[g] != g:
            g = pais[g]
        return g

    vistos, repeticoes = {}, 0
    for caso in casos:
        entrada = caso["alinhado"]["entrada"]
        for pos, segmento in enumerate(entrada["segmentos"]):
            chave = (segmento["texto"], pos, len(entrada["segmentos"]))
            grupo = grupos[caso["id"]]
            if chave in vistos:
                anterior = vistos[chave]
                if grupo != anterior:
                    repeticoes += 1
                ga, gb = sorted((raiz(grupo), raiz(anterior)))
                pais[gb] = ga
            else:
                vistos[chave] = grupo
    return {i: raiz(g) for i, g in grupos.items()}, repeticoes


def executar(destino: Path) -> dict:
    base = Path(__file__).resolve().parents[2]
    if destino.exists():
        raise FileExistsError("preservar artefatos anteriores")
    casos = gerar_contrastes()
    for caso in casos:
        caso["alinhado"] = alinhar_relacoes(caso["fonte"], variantes_permitidas=VARIANTES)
    # Não ajusta folds para obter pontuação: proximidade une famílias inteiras.
    grupos, auditoria = agrupar_sem_leakage([
        {"id": c["id"], "texto_entrada": c["fonte"]["texto_entrada"],
         "grupo_construcao": c["grupo_construcao"]} for c in casos])
    grupos, repeticoes = agrupar_projecoes(casos, grupos)
    for c in casos:
        c["grupo_validacao"] = grupos[c["id"]]
    totais = Counter(grupos.values())
    divisao = [{"treino": [c["id"] for c in casos if c["grupo_validacao"] != g],
                "teste": [c["id"] for c in casos if c["grupo_validacao"] == g]} for g in sorted(totais)] if len(totais) > 1 else []
    caminhos = [Path(__file__), Path(__file__).with_name("supervisao_relacoes_v4.py"),
        *[Path(__file__).with_name(n) for n in ("preparar_lote_relacional_v3.py", "qualidade.py",
            "anotacao_escopo.py", "revisar_vinculos_segmentos.py", "transporte_anotacoes_normalizadas.py")],
        base / "mente_laylay/cognicao/modalidade_turno.py", base / "mente_laylay/cognicao/normalizacao_linguagem.py",
        base / "mente_laylay/autonomia/porteiro_acoes.py"]
    protocolo = {"perfil": "supervisao_ocorrencias_v4", "git_head": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=base, text=True).strip(),
        "worktree": subprocess.check_output(["git", "status", "--short"], cwd=base, text=True).splitlines(),
        "codigo_sha256": {str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest() for p in caminhos},
        "moldes": FORMAS, "composicoes": COMPOSICOES, "casos": len(casos),
        "nos": sum(len(c["fonte"]["nos"]) for c in casos),
        "atos": dict(Counter(n["ato"] for c in casos for n in c["fonte"]["nos"])),
        "grupos": dict(totais), "dobras_candidatas": divisao,
        "projecoes_locais_repetidas_entre_grupos": repeticoes,
        "auditoria_lexical": auditoria, "modelo_consultado": False, "reservas_usadas": False,
        "apto_para_treino": False, "revisao": "moldes assistidos por IA; sem revisão humana independente",
        "pendencias": ["revisar semanticamente o lote", "auditar cobertura nas dobras e fixar protocolo pareado",
                       "medir atos, vínculos e plano completo separadamente"],
        "limites": "quatro paradigmas sintéticos; sem ganho de modelo demonstrado; agrupamento pode colapsar", **FLAGS}
    destino.mkdir(parents=True, exist_ok=False)
    lote = {"casos": casos, **FLAGS}
    bruto = json.dumps(lote, ensure_ascii=False, indent=2).encode("utf-8")
    protocolo["lote_sha256"] = hashlib.sha256(bruto).hexdigest()
    with (destino / "lote.json").open("xb") as f:
        f.write(bruto)
    with (destino / "protocolo.json").open("x", encoding="utf-8") as f:
        json.dump(protocolo, f, ensure_ascii=False, indent=2)
    return protocolo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, required=True)
    r = executar(parser.parse_args().destino)
    print(json.dumps({k: r[k] for k in ("casos", "nos", "atos", "grupos", "apto_para_treino")}, ensure_ascii=False))
