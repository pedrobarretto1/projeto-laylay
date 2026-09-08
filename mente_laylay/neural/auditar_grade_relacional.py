"""Audita a grade congelada; RED de alinhamento não vira subconjunto verde."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.capacidades import intents_registradas
from .anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from .cobertura import carregar_manifesto_variantes
from .qualidade import auditar_leakage_dataset


def auditar_grade(diretorio: Path) -> dict:
    ler = lambda p: json.loads(p.read_text(encoding="utf-8"))
    protocolo = ler(diretorio / "protocolo.json")
    if any(protocolo.get(k) is not False for k in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")):
        raise ValueError("protocolo não isolado")
    particoes = {}
    for nome, digest in protocolo["sha256_particoes"].items():
        if Path(nome).name != nome:
            raise ValueError("nome de partição inválido")
        caminho = diretorio / nome
        if hashlib.sha256(caminho.read_bytes()).hexdigest() != digest:
            raise ValueError("partição mudou após congelamento")
        particoes[caminho.stem] = ler(caminho)["casos"]
    if {k: len(v) for k, v in particoes.items()} != protocolo["particoes"]:
        raise ValueError("contagens divergiram")
    dev = particoes["desenvolvimento"]
    reservas = [c for k, v in particoes.items() if k != "desenvolvimento" for c in v]
    lexical = lambda cs: [{"text": c["texto_entrada"], "family": c["grupo_contraste"]} for c in cs]
    leakage = auditar_leakage_dataset(lexical(dev), lexical(reservas))
    manifesto_path = Path(__file__).with_name("datasets") / "catalogo_variantes_v0.json"
    manifesto = carregar_manifesto_variantes(manifesto_path, intents_catalogadas=intents_registradas())
    variantes = {(v["intent"], v["action"]) for v in manifesto["variants"]}
    alinhados, falhas = [], []
    for caso in dev:
        turno = classificar_modalidade_turno(caso["texto_entrada"],
                    texto_tem_comando_explicito=texto_tem_comando_explicito,
                    confirmacao_contextual_valida=False)
        referencia = referencia_canonica(turno)
        anotacao = {"versao": 1, "origem": "anotacao_manual", "segmentos": caso["segmentos"],
                    "referencia_sha256": referencia["sha256"]}
        try:
            validar_anotacao_escopo(anotacao, turno=turno, variantes_permitidas=variantes)
        except ValueError as erro:
            falhas.append({"id": caso["id"], "dominio": caso["dominio"],
                           "grupo_construcao": caso["grupo_construcao"], "com_aspas": caso["com_aspas"],
                           "texto_entrada": caso["texto_entrada"], "esperado": caso["segmentos"],
                           "observado": referencia, "erro": str(erro)})
        else:
            alinhados.append(caso["id"])
    raiz = Path(__file__).resolve().parents[2]
    fontes = [Path(__file__), manifesto_path, diretorio / "protocolo.json",
              Path(__file__).with_name("anotacao_escopo.py"),
              Path(__file__).with_name("avaliacao_escopo.py"),
              raiz / "mente_laylay/cognicao/modalidade_turno.py",
              raiz / "mente_laylay/autonomia/porteiro_acoes.py"]
    return {"total_dev": len(dev), "alinhados": alinhados, "falhas_alinhamento": falhas,
            "falhas_por_dominio": dict(Counter(c["dominio"] for c in falhas)),
            "falhas_por_construcao": dict(Counter(c["grupo_construcao"] for c in falhas)),
            "falhas_por_aspas": dict(Counter(str(c["com_aspas"]) for c in falhas)),
            "leakage_dev_reservas": leakage,
            "classificador_aplicado_as_reservas": False, "modelo_avaliado": False,
            "apto_alinhamento_integral": not falhas,
            "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False,
            "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diretorio", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        raise FileExistsError("preservar auditoria anterior")
    resultado = auditar_grade(args.diretorio)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(json.dumps({"total": resultado["total_dev"], "alinhados": len(resultado["alinhados"]),
                      "falhas": len(resultado["falhas_alinhamento"]), "dominios": resultado["falhas_por_dominio"]}))


if __name__ == "__main__":
    main()
