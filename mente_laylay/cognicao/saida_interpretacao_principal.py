"""Envelope principal negociado, sem transformar formato em semântica ou ação."""
from __future__ import annotations

from typing import Any
import json

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.cognicao.leitura_semantica_turno import (
    TIPOS_ATO, ESTADOS_EMOCIONAIS_USUARIO, NATUREZAS_LEITURA_EMOCIONAL,
    normalizar_leitura_semantica,
)
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada


def _objeto(propriedades: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "properties": propriedades, "required": list(propriedades),
            "additionalProperties": False}


def criar_contrato_saida_interpretacao_principal(
    texto: str, *, fontes: tuple[SnapshotComandoIA, ...] = (),
) -> ContratoSaidaEstruturada:
    """O owner valida estrutura e literal; porteiro/executor seguem soberanos."""
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("fonte da interpretação principal ausente")
    if not isinstance(fontes, tuple) or len(fontes) > 8 or any(not isinstance(f, SnapshotComandoIA) for f in fontes):
        raise ValueError("fontes exigem snapshots textuais do host")
    fontes_dados = [f.como_dict() for f in fontes]
    ultimo_fim = 0
    for indice, fonte in enumerate(fontes_dados):
        intervalo = fonte.get("intervalo")
        if (set(fonte) != {"indice_segmento", "texto_original", "intervalo", "origem", "autoriza_execucao", "comprova_efeito"}
            or type(fonte["indice_segmento"]) is not int or fonte["indice_segmento"] != indice
            or not isinstance(intervalo, list) or len(intervalo) != 2 or any(type(i) is not int for i in intervalo)
            or not ultimo_fim <= intervalo[0] < intervalo[1] <= len(texto)
            or texto[slice(*intervalo)] != fonte["texto_original"]
            or fonte["origem"] != "segmentacao_canonica"
            or fonte["autoriza_execucao"] is not False or fonte["comprova_efeito"] is not False):
            raise ValueError("fonte textual não vinculada")
        ultimo_fim = intervalo[1]
    string = {"type": "string"}
    objeto_json = {"type": "object", "additionalProperties": True}
    interpretacao = _objeto({
        **{k: string for k in ("texto_original", "operacao", "tipo_recurso", "alvo", "destino", "condicao")},
        "parametros": objeto_json, "referencias": {"type": "array", "items": string},
        "dependencias": {"type": "array", "items": {"type": "integer", "minimum": 0}},
    })
    emocional = _objeto({
        "estado_usuario": {"type": "string", "enum": sorted(ESTADOS_EMOCIONAIS_USUARIO | {"nenhum"})},
        "intensidade": {"type": "integer", "minimum": 0, "maximum": 3},
        **{k: string for k in ("causa_expressa", "trecho_evidencia", "alvo")},
        "natureza_evidencia": {"type": "string", "enum": sorted(NATUREZAS_LEITURA_EMOCIONAL)},
        "hipotetica": {"type": "boolean"},
        "confianca": {"type": "number", "minimum": 0, "maximum": 1},
    })
    esquema = _objeto({
        "fala": string, "emocao": string,
        "nivel_emocao": {"type": "integer", "minimum": 1, "maximum": 3},
        "tipo_interacao": string,
        "leitura_turno": {"type": "array", "minItems": 1, "maxItems": 8, "items": _objeto({
            "tipo": {"type": "string", "enum": sorted(TIPOS_ATO)},
            "conteudo": string, "interpretacao": interpretacao,
        })},
        "leitura_emocional": emocional,
        "comandos": {"type": "array", "items": _objeto({
            "intent": {"type": "string", "enum": sorted(intents_registradas())}, "params": objeto_json,
        })},
        "aprendizados": {"type": "array", "items": {"anyOf": [string, objeto_json]}},
    })
    if fontes_dados:
        ramos = []
        for fonte in fontes_dados:
            # JSON quebra aliases internos do template: restringir o literal
            # não deve restringir fala, operação, alvo ou outros campos string.
            ramo = json.loads(json.dumps(esquema["properties"]["leitura_turno"]["items"]))
            ramo["properties"]["conteudo"]["const"] = fonte["texto_original"]
            props = ramo["properties"]["interpretacao"]["properties"]
            props["texto_original"]["const"] = fonte["texto_original"]
            props["intervalo"] = {"type": "array", "items": {"type": "integer"}, "const": fonte["intervalo"]}
            ramo["properties"]["interpretacao"]["required"].append("intervalo")
            ramos.append(ramo)
        esquema["properties"]["leitura_turno"].update(items={"anyOf": ramos},
            minItems=len(fontes_dados), maxItems=len(fontes_dados))

    def validar(dados: dict[str, Any]) -> None:
        # Snapshot valida a árvore JSON; codec também recusa duplicatas e NaN.
        SnapshotComandoIA(dados)
        if set(dados) != set(esquema["properties"]) or any(
            not isinstance(dados[k], str) for k in ("fala", "emocao", "tipo_interacao")
        ) or type(dados["nivel_emocao"]) is not int or not 1 <= dados["nivel_emocao"] <= 3:
            raise ValueError("envelope_principal_invalido")
        atos = dados["leitura_turno"]
        if not isinstance(atos, list) or not 1 <= len(atos) <= 8:
            raise ValueError("atos_tipados_ausentes")
        if fontes_dados and (len(atos) != len(fontes_dados) or any(
            not isinstance(ato, dict) or ato.get("conteudo") != fonte["texto_original"]
            or not isinstance(ato.get("interpretacao"), dict)
            or ato["interpretacao"].get("intervalo") != fonte["intervalo"]
            for ato, fonte in zip(atos, fontes_dados)
        )):
            raise ValueError("fontes_textuais_sem_cobertura_ordenada")
        for ato in atos:
            if (not isinstance(ato, dict) or set(ato) != {"tipo", "conteudo", "interpretacao"}
                or not isinstance(ato["tipo"], str) or ato["tipo"] not in TIPOS_ATO
                or not isinstance(ato["conteudo"], str) or not isinstance(ato["interpretacao"], dict)
                or set(ato["interpretacao"]) != set(interpretacao["properties"]) | ({"intervalo"} if fontes_dados else set())
                or ato["conteudo"] != ato["interpretacao"].get("texto_original")):
                raise ValueError("ato_tipado_invalido")
        leitura = normalizar_leitura_semantica({"atos": atos}, texto=texto, origem="llm_principal")
        if leitura.get("problemas_interpretacao") or len(leitura.get("atos", [])) != len(atos):
            raise ValueError("interpretacao_nao_vinculada_a_fonte")
        emocao = dados["leitura_emocional"]
        if (not isinstance(emocao, dict) or set(emocao) != set(emocional["properties"])
            or any(not isinstance(emocao[k], str) for k in (
                "estado_usuario", "causa_expressa", "trecho_evidencia", "alvo", "natureza_evidencia"))
            or emocao["estado_usuario"] not in ESTADOS_EMOCIONAIS_USUARIO | {"nenhum"}
            or emocao["natureza_evidencia"] not in NATUREZAS_LEITURA_EMOCIONAL
            or type(emocao["intensidade"]) is not int or not 0 <= emocao["intensidade"] <= 3
            or type(emocao["hipotetica"]) is not bool
            or type(emocao["confianca"]) not in (int, float) or not 0 <= emocao["confianca"] <= 1):
            raise ValueError("leitura_emocional_malformada")
        comandos = dados["comandos"]
        if not isinstance(comandos, list) or any(
            not isinstance(c, dict) or set(c) != {"intent", "params"}
            or not isinstance(c["intent"], str) or c["intent"] not in intents_registradas()
            or not isinstance(c["params"], dict) for c in comandos
        ):
            raise ValueError("proposta_de_comandos_malformada")
        if not isinstance(dados["aprendizados"], list) or any(
            not isinstance(a, (str, dict)) for a in dados["aprendizados"]
        ):
            raise ValueError("aprendizados_malformados")

    return ContratoSaidaEstruturada("interpretacao_principal_v1", "[INTERPRETACAO_PRINCIPAL]", esquema, validar)
