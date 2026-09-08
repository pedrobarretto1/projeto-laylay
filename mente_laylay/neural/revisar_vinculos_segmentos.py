"""Materializa planos MANUAIS de alinhamento, sem resolver linguagem."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Mapping

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.capacidades import intents_registradas
from .anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from .cobertura import carregar_manifesto_variantes


def vincular_plano_manual(caso: dict, turno: dict, *,
                         intervalos: Mapping[int, tuple[int, int]],
                         donos: Mapping[tuple[str, str], int],
                         variantes_permitidas: set[tuple[str, str]],
                         lacunas_revisadas: list[dict] | None = None) -> dict:
    """Converte somente offsets de um registro de fonte única já anotado.

    Intervalos da fonte e donos das ações são explícitos. Não escolhe dono,
    não busca menção por nome e não atribui papéis novos. Sem fuzzy matching.
    """
    fonte = caso["segmentos"]
    if len(fonte) != 1 or fonte[0]["texto"] != caso["texto_entrada"]:
        raise ValueError("migração exige fonte única integral")
    texto = caso["texto_entrada"]
    # Validar a anotação-fonte em seu próprio espaço de offsets, sem afirmar
    # que essa segmentação antiga é a composição real.
    referencia_fonte = {"segmentos": [{"indice": fonte[0]["indice"], "texto": texto}]}
    validar_anotacao_escopo({"versao": 1, "origem": "anotacao_manual", "segmentos": fonte,
                            "referencia_sha256": referencia_canonica(referencia_fonte)["sha256"]},
                           turno=referencia_fonte, variantes_permitidas=variantes_permitidas)
    ref = referencia_canonica(turno)
    segmentos = ref["leitura_observada"]["segmentos"]
    if set(intervalos) != {s["indice"] for s in segmentos}:
        raise ValueError("plano de intervalos incompleto")
    coberto = set()
    for s in segmentos:
        a, b = intervalos[s["indice"]]
        if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(texto)
                or texto[a:b] != s["texto"] or coberto.intersection(range(a, b))):
            raise ValueError("intervalo não corresponde ao segmento canônico")
        coberto.update(range(a, b))
    lacunas = deepcopy(lacunas_revisadas or [])
    for lacuna in lacunas:
        if set(lacuna) != {"inicio", "fim", "texto", "justificativa"}:
            raise ValueError("lacuna precisa de revisão explícita")
        a, b = lacuna["inicio"], lacuna["fim"]
        if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(texto)
                or texto[a:b] != lacuna["texto"] or coberto.intersection(range(a, b))
                or not isinstance(lacuna["justificativa"], str) or not lacuna["justificativa"].strip()):
            raise ValueError("lacuna revisada não corresponde à fonte")
        # A entrada original conserva este trecho; ele NÃO vira segmento ou
        # autoridade. Menções dentro de lacunas continuam proibidas abaixo.
        coberto.update(range(a, b))
    if any(letra not in " ,;.!?\t\r\n" for i, letra in enumerate(texto) if i not in coberto):
        raise ValueError("plano descartaria conteúdo da fonte")
    variantes = {(a["intent"], a["action"]) for a in fonte[0]["acoes"]}
    if set(donos) != variantes or any(type(i) is not int or i not in intervalos for i in donos.values()):
        raise ValueError("donos das ações precisam ser explícitos e válidos")
    novos = {s["indice"]: {"indice": s["indice"], "texto": s["texto"], "acoes": []} for s in segmentos}
    for original in fonte[0]["acoes"]:
        acao = deepcopy(original)
        for papel in ("alvos_solicitados", "alvos_excluidos", "alvos_mencionados"):
            for m in acao[papel]:
                candidatos = [(i, a) for i, (a, b) in intervalos.items() if a <= m["inicio"] < m["fim"] <= b]
                if len(candidatos) != 1:
                    raise ValueError("menção cruza fronteira ou não possui origem única")
                indice, inicio = candidatos[0]
                m.update(segmento=indice, inicio=m["inicio"] - inicio, fim=m["fim"] - inicio)
        novos[donos[(acao["intent"], acao["action"])]] ["acoes"].append(acao)
    anotacao = {"versao": 2, "origem": "anotacao_manual", "referencia_sha256": ref["sha256"],
                "segmentos": list(novos.values())}
    validado = validar_anotacao_escopo(anotacao, turno=turno, variantes_permitidas=variantes_permitidas)
    return {"id": caso["id"], "texto_entrada": texto, **validado,
            "plano_manual": {"intervalos": dict(intervalos),
                             "donos": [{"intent": k[0], "action": k[1], "segmento": v} for k, v in donos.items()],
                             **({"lacunas_revisadas": lacunas} if lacunas else {})}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grade", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        raise FileExistsError("preservar revisão anterior")
    protocolo = json.loads((args.grade / "protocolo.json").read_text(encoding="utf-8"))
    fonte = args.grade / "desenvolvimento.json"
    if hashlib.sha256(fonte.read_bytes()).hexdigest() != protocolo["sha256_particoes"][fonte.name]:
        raise ValueError("fonte congelada mudou")
    dados = json.loads(fonte.read_text(encoding="utf-8"))
    if dados.get("treino_permitido") is not False or dados.get("autoriza_execucao") is not False:
        raise ValueError("fonte não isolada")
    manifesto_path = Path(__file__).with_name("datasets") / "catalogo_variantes_v0.json"
    manifesto = carregar_manifesto_variantes(manifesto_path, intents_catalogadas=intents_registradas())
    variantes = {(v["intent"], v["action"]) for v in manifesto["variants"]}
    # Plano de revisão dos 12 exemplos conhecidos, NÃO regra de runtime.
    revisados = {f"rel_v2_e{e}_f1_{d}_pedido_q{q}" for e in (0, 1)
                 for d in ("apps", "musica", "arquivos") for q in (0, 1)}
    registros, encontrados = [], set()
    for caso in dados["casos"]:
        texto = caso["texto_entrada"]
        turno = classificar_modalidade_turno(texto, texto_tem_comando_explicito=texto_tem_comando_explicito)
        if caso["id"] in revisados:
            # A revisão manual estabelece: primeiro trecho exclui; segundo pede.
            if texto.count(", ") != 1:
                raise ValueError("molde revisado divergiu")
            limite = texto.index(", ")
            intervalos, dono = {0: (0, limite), 1: (limite + 2, len(texto))}, 1
            encontrados.add(caso["id"])
        else:
            intervalos, dono = {0: (0, len(texto))}, 0
        donos = {(a["intent"], a["action"]): dono for a in caso["segmentos"][0]["acoes"]}
        registros.append(vincular_plano_manual(caso, turno, intervalos=intervalos,
                                               donos=donos, variantes_permitidas=variantes))
    if encontrados != revisados or len(registros) != protocolo["particoes"]["desenvolvimento"]:
        raise ValueError("revisão incompleta")
    fontes = [Path(__file__), fonte, args.grade / "protocolo.json", manifesto_path,
              Path(__file__).with_name("anotacao_escopo.py"), Path(__file__).with_name("avaliacao_escopo.py")]
    r = {"total": len(registros), "vinculos_revisados": len(encontrados), "casos": registros,
         "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False,
         "modelo_avaliado": False, "reservas_alteradas": False,
         "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes}}
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    print(json.dumps({"alinhados": r["total"], "vinculos_revisados": r["vinculos_revisados"]}))


if __name__ == "__main__":
    main()
