"""Confronta alinhamento manual com segmentos reais, sem inferência neural."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.capacidades import intents_registradas
from .anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from .cobertura import carregar_manifesto_variantes


def auditar_piloto(piloto: Path) -> dict:
    """Mantém rótulos manuais intactos; alinhamento divergente aborta."""
    dados = json.loads(piloto.read_text(encoding="utf-8"))
    if (dados.get("tipo") != "piloto_anotacao_escopo_manual"
            or dados.get("treino_permitido") is not False
            or dados.get("autoriza_execucao") is not False):
        raise ValueError("piloto deve proibir treino e execução")
    casos = dados.get("casos")
    if not isinstance(casos, list) or not casos:
        raise ValueError("piloto sem casos")
    ids = [c.get("id") for c in casos]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("ids inválidos ou duplicados")
    manifesto_path = Path(__file__).with_name("datasets") / "catalogo_variantes_v0.json"
    manifesto = carregar_manifesto_variantes(manifesto_path, intents_catalogadas=intents_registradas())
    variantes = {(i["intent"], i["action"]) for i in manifesto["variants"]}
    registros = []
    for caso in casos:
        entrada = caso["texto_entrada"]
        if not isinstance(entrada, str) or not entrada.strip():
            raise ValueError("entrada inválida")
        turno = classificar_modalidade_turno(
            entrada, texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=False,
        )
        # Hash referencia a observação desta rodada; segmentos e spans manuais
        # continuam fixos no piloto e não são corrigidos pelo classificador.
        anotacao = {"versao": 1, "origem": "anotacao_manual",
                    "referencia_sha256": referencia_canonica(turno)["sha256"],
                    "segmentos": caso["segmentos"]}
        registro = validar_anotacao_escopo(anotacao, turno=turno, variantes_permitidas=variantes)
        registros.append({"id": caso["id"], "texto_entrada": entrada, **registro})
    raiz = Path(__file__).resolve().parents[2]
    fontes = [piloto, manifesto_path, Path(__file__),
              Path(__file__).with_name("anotacao_escopo.py"),
              raiz / "mente_laylay/cognicao/modalidade_turno.py",
              raiz / "mente_laylay/autonomia/porteiro_acoes.py"]
    return {"tipo": "auditoria_alinhamento_manual", "treino_permitido": False,
            "autoriza_execucao": False, "autoriza_promocao": False,
            "runtime_completo": False, "modelo_avaliado": False,
            "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes},
            "total": len(registros), "casos": registros}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--piloto", type=Path, default=Path(__file__).with_name("datasets") / "escopo_relacional_piloto_v1.json")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        raise FileExistsError("preservar auditoria anterior")
    relatorio = auditar_piloto(args.piloto)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        json.dump(relatorio, arquivo, ensure_ascii=False, indent=2)
    print(json.dumps({"casos_alinhados": relatorio["total"], "treino": False, "execucao": False}))


if __name__ == "__main__":
    main()
