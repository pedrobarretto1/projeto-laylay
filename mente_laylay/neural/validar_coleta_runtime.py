"""Confere evidência persistida da sonda, não certifica qualidade da conversa."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from mente_laylay.integracao.roteiro_teste_conversa import carregar_configuracao_roteiro
from .auditoria_shadow import ler_jsonl_tolerante
from .curadoria_encoder import _hash


def validar(comandos: tuple[str, ...], planos: list[dict], registros: list[dict], resumo: dict) -> dict:
    n = len(comandos)
    if not n or resumo.get("concluido_transporte") is not True or resumo.get("respondidos") != n:
        raise ValueError("transporte incompleto")
    if len(planos) != n or [p.get("indice") for p in planos] != list(range(n)):
        raise ValueError("planos incompletos ou fora de ordem")
    ids = [p.get("plano", {}).get("id") for p in planos]
    if any(type(i) is not int or i <= 0 for i in ids) or len(set(ids)) != n:
        raise ValueError("identidades canônicas inválidas")
    selecionados = [r for r in registros if r.get("turno_id") in ids]
    if Counter(r["turno_id"] for r in selecionados) != Counter(ids):
        raise ValueError("coleta ausente ou duplicada por turno")
    por_id = {r["turno_id"]: r for r in selecionados}
    conversa, sessao = None, None
    tamanhos_contexto = []
    for i, (texto, p) in enumerate(zip(comandos, planos)):
        plano = p["plano"]
        if p.get("comando") != texto or plano.get("texto_usuario") != texto:
            raise ValueError("plano não corresponde à entrada enviada")
        if plano.get("comandos") != []:
            raise ValueError("sonda sem efeitos registrou comando operacional")
        r = por_id[ids[i]]
        entrada = r.get("entrada", {})
        if (r.get("tipo") != "entrada_prospectiva" or r.get("planejamento") != "concluido"
                or entrada.get("texto") != texto or entrada.get("truncado") is not False
                or entrada.get("caracteres_originais") != len(texto)
                or entrada.get("sha256_original") != hashlib.sha256(texto.encode()).hexdigest()):
            raise ValueError("fidelidade da entrada não comprovada")
        if r.get("origem_declarada") != "roteiro_teste" or r.get("teste_declarado") is not True:
            raise ValueError("origem de teste não preservada")
        if any(r.get(k) is not False for k in (
                "origem_humana_certificada", "apto_treino", "treino_permitido", "autoriza_execucao", "autoriza_promocao")):
            raise ValueError("coleta não pode certificar humano ou autorizar ações")
        if r.get("anotacao") is not None or r.get("particao") is not None or r.get("origem_rotulo") != "pendente":
            raise ValueError("rótulo ou partição indevidos")
        if not isinstance(r.get("conversa_id"), str) or not r["conversa_id"]:
            raise ValueError("conversa não identificada")
        if type(r.get("sessao_conversa_ts")) not in (float, int) or r["sessao_conversa_ts"] <= 0:
            raise ValueError("sessão não identificada")
        atual = (r["conversa_id"], r["sessao_conversa_ts"])
        if i == 0: conversa, sessao = atual
        if atual != (conversa, sessao):
            raise ValueError("sessão/conversa mudou na sonda")
        contexto = r.get("contexto_anterior", {})
        if contexto.get("turno_id") != (ids[i - 1] if i else None):
            raise ValueError("encadeamento de turnos incorreto")
        if contexto.get("autoriza_execucao") is not False:
            raise ValueError("contexto virou autoridade")
        mensagens = contexto.get("mensagens")
        if not isinstance(mensagens, list) or len(mensagens) > 4 or any(
                m.get("papel") not in {"user", "assistant"} for m in mensagens):
            raise ValueError("contexto inclui mensagem fora do contrato")
        tamanhos_contexto.append(len(mensagens))
    return {"coleta_runtime_green": True, "turnos_conferidos": n, "ids_canonicos": ids,
            "conversa_id": conversa, "sessao_conversa_ts": sessao,
            "mensagens_contexto_por_turno": tamanhos_contexto,
            "comandos_operacionais_nos_planos": 0, "origem_teste_preservada": True,
            "qualidade_conversa_certificada": False, "contexto_completo_certificado": False,
            "amostras_humanas": 0, "autoriza_treino": False, "autoriza_promocao": False}


def executar(roteiro: Path, pasta: Path, coleta: Path, destino: Path) -> dict:
    if destino.exists():
        raise FileExistsError("preservar validação anterior")
    caminhos = [roteiro, pasta / "planos.jsonl", pasta / "resumo.json", coleta]
    hashes = {str(p.resolve()): _hash(p) for p in caminhos}
    if any(h is None for h in hashes.values()): raise FileNotFoundError("evidência ausente")
    comandos = carregar_configuracao_roteiro(str(roteiro)).comandos
    planos, erros_planos = ler_jsonl_tolerante(caminhos[1])
    registros, erros_coleta = ler_jsonl_tolerante(coleta)
    if erros_planos or erros_coleta: raise ValueError("evidência corrompida")
    r = validar(comandos, planos, registros, json.loads(caminhos[2].read_text(encoding="utf-8")))
    if any(_hash(Path(p)) != h for p, h in hashes.items()): raise RuntimeError("evidência mudou durante leitura")
    r.update(fontes_sha256=hashes, validador_sha256=_hash(Path(__file__)))
    with destino.open("x", encoding="utf-8") as f: json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for nome in ("roteiro", "pasta", "coleta", "destino"): p.add_argument("--" + nome, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(executar(a.roteiro, a.pasta, a.coleta, a.destino), ensure_ascii=False))
