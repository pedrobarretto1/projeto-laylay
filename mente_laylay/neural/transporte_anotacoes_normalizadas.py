"""Transporte offline por proveniência exata; não altera linguagem/autoridade.

Não faz diff aproximado. Metadados sem posição só são suficientes quando o
trecho de origem tem ocorrência literal única. Alterações dentro de menções
ou da âncora exigem revisão e são rejeitadas, mesmo quando preservam tamanho.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from mente_laylay.cognicao.normalizacao_linguagem import corrigir_erros_portugues_operacionais
from .anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from .preparar_lote_relacional_v3 import (
    VARIANTES, agrupar_sem_leakage, classificar_modalidade_turno, texto_tem_comando_explicito,
)
from .revisar_vinculos_segmentos import vincular_plano_manual


def construir_mapa(fonte: str, destino: str, eventos: list[dict]) -> dict:
    """Cada caractere não modificado conserva seu índice original."""
    if not isinstance(fonte, str) or not isinstance(destino, str) or not isinstance(eventos, list):
        raise ValueError("fontes e eventos inválidos")
    atual, origens, passos = fonte, list(range(len(fonte))), []
    for evento in eventos:
        if (not isinstance(evento, dict) or set(evento) != {"de", "para", "tipo"}
                or any(not isinstance(evento[k], str) or not evento[k] for k in evento)
                or evento["de"] == evento["para"]):
            raise ValueError("transformação sem registro válido")
        de, para = evento["de"], evento["para"]
        inicio = atual.find(de)
        if inicio < 0 or atual.find(de, inicio + 1) >= 0:
            raise ValueError("transformação ausente ou ambígua sem offsets")
        fim = inicio + len(de)
        indices = origens[inicio:fim]
        if any(i is None for i in indices) or indices != list(range(indices[0], indices[0] + len(indices))):
            raise ValueError("transformações sobrepostas sem proveniência direta")
        passos.append({**deepcopy(evento), "inicio_fonte": indices[0], "fim_fonte": indices[-1] + 1,
                       "inicio_etapa": inicio, "fim_etapa": fim})
        atual = atual[:inicio] + para + atual[fim:]
        origens[inicio:fim] = [None] * len(para)
    if atual != destino:
        raise ValueError("normalização contém transformação não registrada")
    return {"fonte": fonte, "destino": destino, "passos": passos,
            "posicoes": {origem: i for i, origem in enumerate(origens) if origem is not None}}


def transportar_intervalo(mapa: dict, inicio: int, fim: int) -> tuple[int, int]:
    if type(inicio) is not int or type(fim) is not int or not 0 <= inicio < fim <= len(mapa["fonte"]):
        raise ValueError("intervalo de origem inválido")
    posicoes = [mapa["posicoes"].get(i) for i in range(inicio, fim)]
    if any(i is None for i in posicoes):
        raise ValueError("transformação atingiu menção ou âncora protegida")
    if posicoes != list(range(posicoes[0], posicoes[0] + len(posicoes))):
        raise ValueError("intervalo deixou de ser contíguo")
    a, b = posicoes[0], posicoes[-1] + 1
    if mapa["fonte"][inicio:fim] != mapa["destino"][a:b]:
        raise ValueError("literal não foi preservado")
    return a, b


def alinhar_com_proveniencia(caso: dict) -> dict:
    original = caso["texto_entrada"]
    if len(caso["segmentos"]) != 1 or caso["segmentos"][0]["texto"] != original:
        raise ValueError("fonte manual precisa ser integral")
    ref = {"segmentos": [{"indice": caso["segmentos"][0]["indice"], "texto": original}]}
    validar_anotacao_escopo({"versao": 1, "origem": "anotacao_manual",
                            "referencia_sha256": referencia_canonica(ref)["sha256"],
                            "segmentos": caso["segmentos"]}, turno=ref, variantes_permitidas=VARIANTES)
    turno = classificar_modalidade_turno(original, texto_tem_comando_explicito=texto_tem_comando_explicito)
    normalizado, eventos = corrigir_erros_portugues_operacionais(original)
    # O classificador também pode casefold/compactar espaços. Não presumir
    # um mapa para transformações que o serviço ainda não registra.
    if turno["normalizado_estrutural"] != normalizado:
        raise ValueError("texto estrutural diverge do normalizador auditado")
    mapa = construir_mapa(original, normalizado, eventos)
    copia = deepcopy(caso)
    copia["texto_entrada"] = copia["segmentos"][0]["texto"] = normalizado
    for acao in copia["segmentos"][0]["acoes"]:
        for papel in ("alvos_solicitados", "alvos_excluidos", "alvos_mencionados"):
            for m in acao[papel]:
                m["inicio"], m["fim"] = transportar_intervalo(mapa, m["inicio"], m["fim"])
    ancora = caso["ancora_dono"]
    if type(ancora) is not int:
        raise ValueError("âncora inválida")
    ancora_nova, _ = transportar_intervalo(mapa, ancora, ancora + 1)
    intervalos, fim_anterior = {}, 0
    for s in turno["segmentos"]:
        if normalizado.count(s["texto"]) != 1:
            raise ValueError("segmento sem posição literal única no normalizado")
        a = normalizado.index(s["texto"])
        b = a + len(s["texto"])
        if a < fim_anterior:
            raise ValueError("segmentos sobrepostos ou fora de ordem")
        intervalos[s["indice"]] = (a, b)
        fim_anterior = b
    donos = [i for i, (a, b) in intervalos.items() if a <= ancora_nova < b]
    if len(donos) != 1:
        raise ValueError("âncora não chegou a segmento único")
    variantes = {(a["intent"], a["action"]) for a in copia["segmentos"][0]["acoes"]}
    if len(variantes) != 1:
        raise ValueError("fonte com múltiplas ações exige âncoras separadas")
    r = vincular_plano_manual(copia, turno, intervalos=intervalos,
                              donos={v: donos[0] for v in variantes}, variantes_permitidas=VARIANTES)
    r.update(texto_entrada=original, papel_dataset="desenvolvimento",
             proveniencia_normalizacao={"texto_normalizado": normalizado, "passos": mapa["passos"],
                 "sha256_fonte": hashlib.sha256(original.encode()).hexdigest(),
                 "ancora_fonte": ancora, "ancora_normalizada": ancora_nova},
             **{k: caso[k] for k in ("grupo_construcao", "grupo_entidades", "grupo_contraste")})
    return r


def executar(fonte_dir: Path, destino: Path) -> dict:
    protocolo = json.loads((fonte_dir / "protocolo.json").read_text(encoding="utf-8"))
    lote_path = fonte_dir / "lote_fonte.json"
    entradas_lote = [sha for caminho, sha in protocolo["fontes"].items()
                     if Path(caminho).resolve() == lote_path.resolve()]
    if len(entradas_lote) != 1:
        raise ValueError("lote selecionado não está vinculado ao protocolo")
    for caminho, sha in protocolo["fontes"].items():
        if hashlib.sha256(Path(caminho).read_bytes()).hexdigest() != sha:
            raise ValueError("fonte congelada divergiu; não atualizar hash automaticamente")
    dados = json.loads(lote_path.read_text(encoding="utf-8"))
    if any(dados.get(k) is not False for k in ("treino_permitido", "autoriza_execucao", "autoriza_promocao")):
        raise ValueError("fonte não isolada")
    casos = dados["casos"]
    if (not casos or len(casos) != protocolo["total"]
            or len(casos) != len({c["id"] for c in casos})
            or any(c.get("particao") != "desenvolvimento" for c in casos)):
        raise ValueError("lote inválido ou contém reserva")
    destino.mkdir(parents=True, exist_ok=False)
    grupos, _ = agrupar_sem_leakage(casos)
    alinhados = [alinhar_com_proveniencia(c) for c in casos]  # Qualquer falha impede publicação parcial.
    for c in alinhados:
        c["grupo_validacao"] = grupos[c["id"]]
    r = {"total": len(casos), "alinhados": len(alinhados), "casos": alinhados,
         "com_transformacao": sum(bool(c["proveniencia_normalizacao"]["passos"]) for c in alinhados),
         "treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False,
         "modelo_avaliado": False, "reserva_usada": False,
         "fontes": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
             fonte_dir / "lote_fonte.json", fonte_dir / "protocolo.json", Path(__file__),
             Path(__file__).parent.parent / "cognicao/normalizacao_linguagem.py")}}
    with (destino / "alinhamento.json").open("x", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    return r


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonte", type=Path, required=True)
    parser.add_argument("--destino", type=Path, required=True)
    args = parser.parse_args()
    r = executar(args.fonte, args.destino)
    print(json.dumps({k: r[k] for k in ("total", "alinhados", "com_transformacao", "treino_permitido")}))
