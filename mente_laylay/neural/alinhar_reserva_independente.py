"""Revisão manual da reserva congelada; jamais gera exemplos de treino."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.capacidades import intents_registradas
from .cobertura import carregar_manifesto_variantes
from .revisar_vinculos_segmentos import vincular_plano_manual

# Plano de anotação, NÃO regras para produção. Outros casos conservam origem
# única. Mudança de texto/segmentação aborta, não escolhe outra interpretação.
PLANOS_MULTIPLOS = {
    "res_ind_v1_mus_01": (", ", 1),
    "res_ind_v1_mus_08": (", ", 0),
    "res_ind_v1_app_03": ("; ", 0),
    "res_ind_v1_file_03": ("; ", 1),
    "res_ind_v1_iot_01": (", mas ", 0),
}


def alinhar_caso(caso: dict, variantes: set[tuple[str, str]]) -> dict:
    texto = caso["texto_entrada"]
    turno = classificar_modalidade_turno(texto, texto_tem_comando_explicito=texto_tem_comando_explicito,
                                        confirmacao_contextual_valida=False)
    dono, intervalos, lacunas = 0, {0: (0, len(texto))}, []
    if caso["id"] in PLANOS_MULTIPLOS:
        separador, dono = PLANOS_MULTIPLOS[caso["id"]]
        if texto.count(separador) != 1:
            raise ValueError("revisar fronteira manual: separador deixou de ser único")
        a = texto.index(separador)
        b = a + len(separador)
        intervalos = {0: (0, a), 1: (b, len(texto))}
        if separador == ", mas ":
            lacunas = [{"inicio": a, "fim": b, "texto": separador,
                        "justificativa": "Conector adversativo removido apenas dos segmentos; preservado na entrada integral e na relação de exclusão anotada."}]
    donos = {(a["intent"], a["action"]): dono for a in caso["segmentos"][0]["acoes"]}
    r = vincular_plano_manual(caso, turno, intervalos=intervalos, donos=donos,
                             variantes_permitidas=variantes, lacunas_revisadas=lacunas)
    return {**r, "dominio": caso["dominio"], "familia": caso["familia"],
            "papel_dataset": "reserva_independente", "revisao_semantica": "anotacao_assistida_por_ia_sem_scores",
            "rotulos_alterados": False}


def executar(*, reserva: Path, saida: Path) -> dict:
    if saida.exists():
        raise FileExistsError("preservar alinhamento anterior")
    protocolo = json.loads((reserva / "protocolo.json").read_text(encoding="utf-8"))
    fonte = reserva / "reserva_congelada.json"
    if hashlib.sha256(fonte.read_bytes()).hexdigest() != protocolo["sha256_reserva"]:
        raise ValueError("reserva congelada mudou")
    dados = json.loads(fonte.read_text(encoding="utf-8"))
    if any(dados.get(k) is not False for k in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")):
        raise ValueError("reserva não isolada")
    manifesto = Path(__file__).with_name("datasets") / "catalogo_variantes_v0.json"
    variantes = {(v["intent"], v["action"]) for v in carregar_manifesto_variantes(manifesto, intents_catalogadas=intents_registradas())["variants"]}
    casos = [alinhar_caso(c, variantes) for c in dados["casos"]]
    if len(casos) != 32 or len({c["id"] for c in casos}) != 32:
        raise ValueError("revisão manual não cobre exatamente a reserva congelada")
    r = {"total": len(casos), "casos": casos, "alinhamento_canonico_revisado": True,
         "modelo_avaliado": False, "treino_permitido": False, "autoriza_execucao": False,
         "autoriza_promocao": False, "rotulos_alterados": False,
         "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
             fonte, reserva / "protocolo.json", Path(__file__), manifesto,
             Path(__file__).with_name("revisar_vinculos_segmentos.py"),
             Path(__file__).with_name("anotacao_escopo.py"))}}
    saida.parent.mkdir(parents=True, exist_ok=True)
    with saida.open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reserva", type=Path, required=True)
    p.add_argument("--saida", type=Path, required=True)
    r = executar(**vars(p.parse_args()))
    print(json.dumps({"alinhados": r["total"], "treino": False, "modelo_avaliado": False}))
