"""Supervisão offline por ocorrência; não interpreta nem autoriza comandos.

Cada nó tem ato e âncora próprios. Segmento canônico é uma referência de
localização, não uma restrição de um único ato por variante. Anotações v1/v2
continuam intactas e validam o escopo de CADA ocorrência separadamente.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Iterable

from mente_laylay.cognicao.normalizacao_linguagem import corrigir_erros_portugues_operacionais
from .anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from .preparar_lote_relacional_v3 import classificar_modalidade_turno, texto_tem_comando_explicito
from .revisar_vinculos_segmentos import vincular_plano_manual
from .transporte_anotacoes_normalizadas import construir_mapa, transportar_intervalo

PAPEIS = {"pedido": "alvos_solicitados", "recusa": "alvos_excluidos", "relato": "alvos_mencionados"}
FLAGS = {"treino_permitido": False, "autoriza_execucao": False, "autoriza_promocao": False}


def _campos(dados: dict, campos: set[str]) -> None:
    if not isinstance(dados, dict) or set(dados) != campos:
        raise ValueError("campos ausentes ou desconhecidos na supervisão v4")


def _intervalo(span: dict, texto: str) -> tuple[int, int]:
    _campos(span, {"inicio", "fim", "texto"})
    a, b = span["inicio"], span["fim"]
    if (type(a) is not int or type(b) is not int or not 0 <= a < b <= len(texto)
            or texto[a:b] != span["texto"] or not span["texto"].strip()):
        raise ValueError("intervalo não corresponde à fonte")
    return a, b


def _acao(no: dict) -> dict:
    return {"intent": no["intent"], "action": no["action"], "ato": no["ato"],
            "resolucao_alvo": "explicito" if no["ato"] == "pedido" else "nao_aplicavel",
            **{papel: deepcopy(no["alvos"]) if papel == PAPEIS[no["ato"]] else []
               for papel in PAPEIS.values()}}


def validar_fonte_relacional(fonte: dict, *, variantes_permitidas: Iterable[tuple[str, str]]) -> None:
    """Validação estrutural, não certificação semântica de rótulos sintéticos.

Este perfil explícito cobre ocorrências não sobrepostas, com alvos literais.
Escopo implícito, aninhado ou sem alvo exige outro perfil; não é adivinhado.
"""
    _campos(fonte, {"versao", "texto_entrada", "nos", "relacoes", *FLAGS})
    if type(fonte["versao"]) is not int or fonte["versao"] != 4:
        raise ValueError("versão relacional inválida")
    if any(fonte[k] is not False for k in FLAGS):
        raise ValueError("supervisão precisa permanecer isolada")
    texto = fonte["texto_entrada"]
    if not isinstance(texto, str) or not texto.strip() or not isinstance(fonte["nos"], list) or not fonte["nos"]:
        raise ValueError("fonte sem texto ou ocorrências")
    variantes = set(variantes_permitidas)
    ref = {"segmentos": [{"indice": 0, "texto": texto}]}
    por_id, intervalos = {}, []
    for no in fonte["nos"]:
        _campos(no, {"id", "intent", "action", "ato", "trecho", "ancora", "alvos"})
        if not isinstance(no["id"], str) or not no["id"].strip() or no["id"] in por_id:
            raise ValueError("ocorrência sem identificador único")
        if no["ato"] not in PAPEIS or not isinstance(no["alvos"], list) or not no["alvos"]:
            raise ValueError("ato ou alvos fora do perfil explícito")
        a, b = _intervalo(no["trecho"], texto)
        c, d = _intervalo(no["ancora"], texto)
        if not a <= c < d <= b:
            raise ValueError("âncora fora da ocorrência")
        if any(a < y and x < b for x, y in intervalos):
            raise ValueError("ocorrências sobrepostas exigem revisão de escopo")
        intervalos.append((a, b))
        for alvo in no["alvos"]:
            x, y = _intervalo(alvo, texto)
            if not a <= x < y <= b or (x < d and c < y):
                raise ValueError("alvo fora da ocorrência ou sobreposto à âncora")
        # Reutiliza catálogo, regras de ato/papel e validade de spans existentes.
        validar_anotacao_escopo({"versao": 1, "origem": "anotacao_manual",
            "referencia_sha256": referencia_canonica(ref)["sha256"],
            "segmentos": [{"indice": 0, "texto": texto, "acoes": [_acao(no)]}]},
            turno=ref, variantes_permitidas=variantes)
        por_id[no["id"]] = no
    coberto = {i for a, b in intervalos for i in range(a, b)}
    if any(i not in coberto and c not in " ,;.!?\n\r\t" for i, c in enumerate(texto)):
        raise ValueError("fonte contém trecho sem supervisão explícita")
    if not isinstance(fonte["relacoes"], list):
        raise ValueError("relações devem ser lista")
    vistas = set()
    for relacao in fonte["relacoes"]:
        _campos(relacao, {"tipo", "origem", "destino"})
        origem, destino = relacao["origem"], relacao["destino"]
        if (not isinstance(origem, str) or not isinstance(destino, str)
                or origem not in por_id or destino not in por_id or origem == destino):
            raise ValueError("relação sem ocorrências válidas")
        recusa, pedido = por_id[origem], por_id[destino]
        if (relacao["tipo"] != "restringe" or recusa["ato"] != "recusa" or pedido["ato"] != "pedido"
                or (recusa["intent"], recusa["action"]) != (pedido["intent"], pedido["action"])):
            raise ValueError("relação não pode converter relato ou outra ação em restrição")
        chave = (origem, destino)
        if chave in vistas:
            raise ValueError("relação duplicada")
        vistas.add(chave)
        if {a["texto"].casefold() for a in recusa["alvos"]} & {a["texto"].casefold() for a in pedido["alvos"]}:
            raise ValueError("pedido e restrição conflitantes exigem revisão temporal")


def alinhar_relacoes(fonte: dict, *, variantes_permitidas: Iterable[tuple[str, str]]) -> dict:
    """Usa composição canônica de linguagem, sem aproveitar seu veto como gold."""
    variantes = set(variantes_permitidas)
    validar_fonte_relacional(fonte, variantes_permitidas=variantes)
    original = fonte["texto_entrada"]
    turno = classificar_modalidade_turno(original, texto_tem_comando_explicito=texto_tem_comando_explicito)
    normalizado, eventos = corrigir_erros_portugues_operacionais(original)
    if turno["normalizado_estrutural"] != normalizado:
        raise ValueError("normalização canônica sem proveniência completa")
    mapa = construir_mapa(original, normalizado, eventos)
    intervalos, anterior = {}, 0
    for s in turno["segmentos"]:
        if normalizado.count(s["texto"]) != 1:
            raise ValueError("segmento sem localização literal única")
        a = normalizado.index(s["texto"])
        b = a + len(s["texto"])
        if a < anterior:
            raise ValueError("segmentos sobrepostos ou fora de ordem")
        intervalos[s["indice"]] = (a, b)
        anterior = b
    nos = []
    for no in fonte["nos"]:
        a, b = transportar_intervalo(mapa, no["ancora"]["inicio"], no["ancora"]["fim"])
        donos = [(i, x) for i, (x, y) in intervalos.items() if x <= a < b <= y]
        if len(donos) != 1:
            raise ValueError("âncora não chegou a um segmento único")
        dono, inicio = donos[0]
        acao = _acao(no)
        for ms in (acao[p] for p in PAPEIS.values()):
            for m in ms:
                m["inicio"], m["fim"] = transportar_intervalo(mapa, m["inicio"], m["fim"])
        caso = {"id": no["id"], "texto_entrada": normalizado,
                "segmentos": [{"indice": 0, "texto": normalizado, "acoes": [acao]}]}
        alinhado = vincular_plano_manual(caso, turno, intervalos=intervalos,
            donos={(no["intent"], no["action"]): dono}, variantes_permitidas=variantes)
        acao_alinhada = next(a for s in alinhado["anotacao"]["segmentos"] for a in s["acoes"])
        nos.append({"id": no["id"], "ancora": {"segmento": dono, "inicio": a - inicio,
                    "fim": b - inicio, "texto": no["ancora"]["texto"]},
                    "trecho_fonte": deepcopy(no["trecho"]), **acao_alinhada})
    return {"versao": 4, "entrada": {"texto_entrada": original,
            "segmentos": [{k: s[k] for k in ("indice", "texto")} for s in turno["segmentos"]]},
            "supervisao": {"nos": nos, "relacoes": deepcopy(fonte["relacoes"])},
            "referencia": referencia_canonica(turno), "proveniencia": mapa["passos"], **FLAGS}
