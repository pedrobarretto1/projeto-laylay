"""Perfil offline literal/imediato: ação, ato, alvo e valor são supervisões distintas.

Não interpreta frases nem certifica sua anotação. Não é consumidor de treino:
contexto, agendamento e operações implícitas exigem outro perfil explícito.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from mente_laylay.especialistas.capacidades import intents_registradas
from .candidato_relacional import tokens
from .cobertura import carregar_catalogo_variantes, validar_catalogo_variantes
from .comparar_ocorrencias_v4 import rotular_ocorrencias
from .preparar_lote_relacional_v3 import VARIANTES as VARIANTES_HISTORICAS
from .supervisao_relacoes_v4 import FLAGS, PAPEIS, _campos, _intervalo, validar_fonte_relacional

PERFIL = "operacional_literal_v1"
VARIANTES = frozenset(VARIANTES_HISTORICAS) | frozenset({
    ("IOT_CONTROL", "on"), ("IOT_CONTROL", "off"),
    ("MEDIA_CONTROL", "pause"), ("MEDIA_CONTROL", "play"), ("MEDIA_CONTROL", "next"),
    ("VOLUME", "set"),
})
ROTULOS = frozenset({"ausente"} | {
    f"{intent}|{action}|{ato}" for intent, action in VARIANTES for ato in PAPEIS
})


def conferir_catalogo() -> None:
    """Reutiliza catálogo/validador; extensão absoluta de volume é só experimental."""
    intents = intents_registradas()
    catalogo = carregar_catalogo_variantes(
        Path(__file__).with_name("datasets") / "catalogo_variantes_v0.json",
        intents_catalogadas=intents,
    )
    # Dispatcher canônico mapeia volume_set/set_volume para VOLUME + acao=set.
    # O manifesto histórico só tem up/down; não o reescrever para este piloto.
    extensao = validar_catalogo_variantes([{
        "intent": "VOLUME", "action": "set", "domain": "audio",
        "risk": "LOW_RISK", "operational_influence_enabled": False,
    }], intents_catalogadas=intents)
    disponiveis = {(v["intent"], v["action"]) for v in catalogo + extensao}
    if not VARIANTES <= disponiveis:
        raise ValueError("perfil operacional divergiu do catálogo")


def preparar_exemplo_operacional(anotacao: dict[str, Any]) -> dict[str, Any]:
    """Valida declaração revisável e projeta supervisão; entrada é somente texto.

Escopo/origem são declarações do anotador, não certificados pelo código.
Alvos permanecem menções literais; nenhum ID físico ou efeito é inferido.
"""
    _campos(anotacao, {
        "versao", "perfil", "escopo", "origem_rotulo", "referencia_rotulo",
        "fonte_v4", "parametros", *FLAGS,
    })
    if type(anotacao["versao"]) is not int or anotacao["versao"] != 1 or anotacao["perfil"] != PERFIL:
        raise ValueError("versão/perfil operacional inválido")
    if anotacao["escopo"] != "literal_imediato":
        raise ValueError("escopo contextual, temporal ou implícito exige outro perfil")
    if any(anotacao[k] is not False for k in FLAGS):
        raise ValueError("anotação não pode conceder autoridade")
    if (anotacao["origem_rotulo"] not in {"curadoria_ia", "revisao_humana"}
            or not isinstance(anotacao["referencia_rotulo"], str)
            or not anotacao["referencia_rotulo"].strip()):
        raise ValueError("revisão deve declarar origem e referência")
    conferir_catalogo()
    fonte = anotacao["fonte_v4"]
    validar_fonte_relacional(fonte, variantes_permitidas=VARIANTES)
    texto = fonte["texto_entrada"]
    nos = {no["id"]: no for no in fonte["nos"]}
    esperados = {no["id"] for no in nos.values() if (no["intent"], no["action"]) == ("VOLUME", "set")}
    if not isinstance(anotacao["parametros"], list):
        raise ValueError("parâmetros devem ser lista")
    vistos = set()
    spans_tokens = {(a, b) for _, a, b in tokens(texto)}
    for parametro in anotacao["parametros"]:
        _campos(parametro, {"ocorrencia", "nome", "valor", "unidade", "evidencia"})
        dono = parametro["ocorrencia"]
        if not isinstance(dono, str) or dono not in esperados or dono in vistos:
            raise ValueError("parâmetro sem dono válido ou duplicado")
        vistos.add(dono)
        if (parametro["nome"] != "nivel_volume" or parametro["unidade"] != "percentual"
                or type(parametro["valor"]) is not int or not 0 <= parametro["valor"] <= 100):
            raise ValueError("volume exige inteiro percentual de 0 a 100")
        a, b = _intervalo(parametro["evidencia"], texto)
        no = nos[dono]
        trecho = no["trecho"]
        if not trecho["inicio"] <= a < b <= trecho["fim"] or (a, b) not in spans_tokens:
            raise ValueError("evidência numérica fora da ocorrência ou token incompleto")
        if (not re.fullmatch(r"[0-9]{1,3}", texto[a:b]) or int(texto[a:b]) != parametro["valor"]):
            raise ValueError("valor não corresponde à evidência literal")
        for span in [no["ancora"], *no["alvos"]]:
            if a < span["fim"] and span["inicio"] < b:
                raise ValueError("valor não pode substituir ação ou alvo")
    if vistos != esperados:
        raise ValueError("volume absoluto sem parâmetro anotado")
    projecao = {"alinhado": {
        "entrada": {"texto_entrada": texto, "segmentos": [{"indice": 0, "texto": texto}]},
        "supervisao": {"nos": [{**no, "ancora": {**no["ancora"], "segmento": 0}} for no in nos.values()]},
    }}
    rotulos = rotular_ocorrencias(projecao, rotulos_permitidos=ROTULOS)
    return {
        "perfil": PERFIL, "uso": "diagnostico", "entrada": {"texto": texto},
        "supervisao": {"rotulos": rotulos, "fonte_v4": deepcopy(fonte),
                       "parametros": deepcopy(anotacao["parametros"])},
        "origem_rotulo": anotacao["origem_rotulo"], "referencia_rotulo": anotacao["referencia_rotulo"],
        "rotulos_catalogo": sorted(ROTULOS), "revisao_semantica_certificada": False,
        "dados_prontos_para_treino": False, **FLAGS,
    }
