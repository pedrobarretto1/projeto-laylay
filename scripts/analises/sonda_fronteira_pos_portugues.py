"""Sonda POS portuguesa offline; modelo externo só é carregado pelo CLI.

VERB/AUX são indícios locais, não validação semântica, fala ou autorização.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Callable, Iterable, Mapping

from scripts.analises.sonda_fronteira_predicados_v1 import reconstruir_condicoes
from scripts.analises.sonda_produtor_candidatos_v1 import gerar_candidatos
from scripts.analises.sonda_produtor_condicoes_v2 import (
    carregar_painel, confrontar_trechos,
)
from scripts.analises.veto_superficie_sujeito_composto import (
    verificar_sujeito_composto_superficial,
)


def _em_oracao_relativa(token: object) -> bool:
    return (getattr(token, "dep_", "") == "acl:relcl"
            or (getattr(token, "pos_", "") == "AUX"
                and getattr(getattr(token, "head", None), "dep_", "")
                == "acl:relcl"))


def _pos_verbal_contraditorio(token: object) -> bool:
    """Etiqueta verbal e papel nominal simultâneos exigem abstenção."""
    if getattr(token, "pos_", "") != "VERB":
        return False
    if (getattr(token, "dep_", "") == "conj"
            and getattr(getattr(token, "head", None), "dep_", "") == "obj"
            and not any(getattr(filho, "dep_", "") in {"nsubj", "csubj"}
                        for filho in getattr(token, "children", ()))):
        return True
    return any(getattr(filho, "pos_", "") == "DET"
               and getattr(filho, "dep_", "") == "det"
               for filho in getattr(token, "children", ()))


def _vinculos_objeto_candidatos(
    fonte: str,
    trechos: list[Mapping[str, object]], segmentos: list[Mapping[str, object]],
    tokens: list[object],
) -> list[dict[str, object]]:
    """Registra arco direto, offsets e conflito POS; não decide a partição."""
    candidatos = []
    for indice in range(1, len(trechos) - 1):
        if (segmentos[indice]["tem_predicado"]
                or not segmentos[indice - 1]["tem_predicado"]
                or not any(item["tem_predicado"]
                           for item in segmentos[indice + 1:])):
            continue
        atual = trechos[indice]
        anterior = trechos[indice - 1]
        conteudo = [token for token in tokens
                    if (atual["inicio"] <= token.idx
                        and token.idx + len(token.text) <= atual["fim"]
                        and token.text.isalpha()
                        and token.dep_ not in {"cc", "det", "case", "mark"})]
        if len(conteudo) != 1:
            continue
        token = conteudo[0]
        antecedente = getattr(token, "head", None)
        verbo = getattr(antecedente, "head", None)
        if antecedente is None or verbo is None:
            continue
        if (token.dep_ != "conj"
                or getattr(antecedente, "dep_", "") != "obj"
                or not anterior["inicio"] <= antecedente.idx
                or antecedente.idx + len(antecedente.text) > anterior["fim"]
                or not anterior["inicio"] <= verbo.idx
                or verbo.idx + len(verbo.text) > anterior["fim"]
                or verbo.text != segmentos[indice - 1]["ancora"]
                or fonte[token.idx:token.idx + len(token.text)] != token.text
                or fonte[antecedente.idx:antecedente.idx + len(antecedente.text)]
                != antecedente.text
                or fonte[verbo.idx:verbo.idx + len(verbo.text)] != verbo.text):
            continue
        candidatos.append({
            "id": atual["id"], "token": token.text, "inicio": token.idx,
            "fim": token.idx + len(token.text),
            "antecedente": antecedente.text,
            "inicio_antecedente": antecedente.idx,
            "fim_antecedente": antecedente.idx + len(antecedente.text),
            "ancora_anterior": verbo.text, "inicio_ancora": verbo.idx,
            "fim_ancora": verbo.idx + len(verbo.text),
            "relacao": "conj_de_objeto_direto",
            "pos_conflitante": (
                token.pos_ not in {"NOUN", "PROPN"}
                or antecedente.pos_ not in {"NOUN", "PROPN"}
                or verbo.pos_ not in {"VERB", "AUX"}),
        })
    return candidatos


def _particao_objeto_em_sombra(
    fonte: str, trechos: list[Mapping[str, object]],
    segmentos: list[Mapping[str, object]],
    vinculos: list[Mapping[str, object]],
    tokens: list[object],
) -> tuple[dict[str, object] | None, dict[str, object]]:
    """Prévia literal e causa de abstenção; não altera decisão canônica."""
    internos = [
        indice for indice, segmento in enumerate(segmentos)
        if (not segmento["tem_predicado"]
            and any(item["tem_predicado"] for item in segmentos[:indice])
            and any(item["tem_predicado"] for item in segmentos[indice + 1:]))
    ]
    ids_internos = [trechos[indice]["id"] for indice in internos]

    def auditoria(estado: str, **detalhes: object) -> dict[str, object]:
        return {"estado": estado, "ids_internos": ids_internos,
                **detalhes, "aprovado_para_producao": False,
                "autoriza_efeito": False}

    if not internos:
        return None, auditoria("sem_fronteira_interna")
    if (len(vinculos) != len(internos)
            or [item["id"] for item in vinculos] != ids_internos):
        return None, auditoria("vinculo_interno_ausente_ou_extra")
    if any(item["pos_conflitante"] for item in vinculos):
        return None, auditoria("vinculo_pos_conflitante")
    for indice in internos:
        superficie = verificar_sujeito_composto_superficial(
            fonte, trechos[indice - 1], trechos[indice], trechos[indice + 1],
        )
        if superficie["estado"] != "sem_veto_superficial":
            return None, auditoria(
                "veto_superficie_sujeito_composto",
                id_vetado=trechos[indice]["id"],
                estado_superficie=superficie["estado"],
            )
    # Uma expressão determinada seguida de predicado plural pode iniciar
    # sujeito composto da condição seguinte. O parser já confundiu esse
    # desenho com conjunção de objetos; não promover a prévia nesse conflito.
    for indice in internos:
        if (re.match(r"(?i)^(?:o|a|os|as|um|uma|uns|umas)\s+",
                     trechos[indice]["citacao"])
                and any(
                    token.pos_ in {"VERB", "AUX"}
                    and trechos[indice + 1]["inicio"] <= token.idx
                    and token.idx + len(token.text)
                    <= trechos[indice + 1]["fim"]
                    and "Plur" in getattr(token, "morph", {}).get("Number", [])
                    for token in tokens
                )):
            return None, auditoria(
                "veto_morfologia_predicado_plural",
                id_vetado=trechos[indice]["id"],
            )
    trechos_compostos: list[str] = []
    inicios: list[int] = []
    inicio_grupo = 0
    for indice, segmento in enumerate(segmentos):
        if segmento["tem_predicado"]:
            inicio = trechos[inicio_grupo]["inicio"]
            inicios.append(inicio)
            trechos_compostos.append(fonte[inicio:trechos[indice]["fim"]])
            inicio_grupo = indice + 1
        elif indice in internos:
            if not trechos_compostos or inicio_grupo != indice:
                return None, auditoria("composicao_literal_invalida")
            trechos_compostos[-1] = fonte[
                inicios[-1]:trechos[indice]["fim"]
            ]
            inicio_grupo = indice + 1
    if inicio_grupo != len(trechos):
        return None, auditoria("composicao_literal_invalida")
    return {
        "estado": "particao_objeto_experimental_revisao_pendente",
        "trechos_condicoes": trechos_compostos,
        "vinculos_ids": ids_internos,
        "aprovado_para_producao": False,
        "autoriza_efeito": False,
    }, auditoria("previsao_em_sombra")


def confrontar_ancoras(
    resultado: Mapping[str, object], esperadas: Mapping[str, str],
) -> dict[str, object]:
    """Audita a âncora separadamente da coincidência de trechos literais.

    A revisão entra somente depois da proposta; nunca orienta o analisador.
    """
    base = {"estado": "referencia_invalida", "aprovado_para_producao": False,
            "autoriza_efeito": False}
    candidatos = resultado.get("candidatos")
    itens = candidatos.get("candidatos") if isinstance(candidatos, Mapping) else None
    if (not isinstance(itens, list) or not itens
            or any(not isinstance(item, Mapping)
                   or not isinstance(item.get("id"), str) for item in itens)
            or not isinstance(esperadas, Mapping)):
        return base
    ids = [item["id"] for item in itens]
    if (len(ids) != len(set(ids)) or set(esperadas) != set(ids)
            or any(not isinstance(valor, str) or len(valor) > 40
                   for valor in esperadas.values())):
        return base
    reconstrucao = resultado.get("reconstrucao")
    if (resultado.get("escolha")
            or not isinstance(reconstrucao, Mapping)
            or reconstrucao.get("estado")
            != "segmentos_ancorados_revisao_pendente"):
        return {**base, "estado": "abstencao_sem_afericao_de_ancora"}
    proposta = resultado.get("proposta")
    segmentos = proposta.get("segmentos") if isinstance(proposta, Mapping) else None
    if (not isinstance(segmentos, list) or len(segmentos) != len(ids)
            or any(not isinstance(item, Mapping)
                   or not isinstance(item.get("id"), str)
                   or not isinstance(item.get("ancora"), str)
                   or type(item.get("tem_predicado")) is not bool
                   for item in segmentos)):
        return {**base, "estado": "proposta_invalida"}
    observadas = {item["id"]: item["ancora"] for item in segmentos}
    if set(observadas) != set(ids) or len(observadas) != len(segmentos):
        return {**base, "estado": "proposta_invalida"}
    divergencias = [
        {"id": item, "observada": observadas[item], "esperada": esperadas[item]}
        for item in ids if observadas[item] != esperadas[item]
    ]
    if divergencias:
        return {**base, "estado": "ancoras_divergentes",
                "divergencias": divergencias}
    return {**base, "estado": "ancoras_alinhadas_revisao_pendente"}


def auditar_previa_em_sombra(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    resultado: Mapping[str, object],
) -> dict[str, object]:
    """Compara somente trechos literais após a proposta, nunca a aprova.

    O confronto reutiliza o validador de citações, mas não avalia conectivo
    nem direção: a prévia experimental não propõe esses dois campos.
    """
    base = {"aprovado_para_producao": False, "autoriza_efeito": False}
    previa = resultado.get("particao_objeto_em_sombra")
    if previa is None:
        return {**base, "estado": "sem_previa"}
    if not isinstance(previa, Mapping):
        return {**base, "estado": "previa_invalida"}
    trechos = previa.get("trechos_condicoes")
    if not isinstance(trechos, list):
        return {**base, "estado": "previa_invalida"}
    confronto = confrontar_trechos(caso, gabarito, {
        "representavel": True,
        "trechos_condicoes": trechos,
        "conectivo_condicoes": "indeterminado",
        "direcao_implicacao": "indeterminado",
    })
    if confronto.get("trechos_alinhados_revisao") is True:
        return {**base, "estado": "trechos_alinhados_revisao_local"}
    if confronto.get("estado") == "trechos_divergentes":
        return {**base, "estado": "trechos_divergentes_revisao_local"}
    return {**base, "estado": "previa_ou_referencia_invalida",
            "detalhe": confronto["estado"]}


def resumir_resultados(
    resultados: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Conta somente estados retrospectivos locais; não mede acurácia real."""
    base = {"aprovado_para_producao": False, "autoriza_efeito": False}
    itens = list(resultados)
    estados = {
        "trechos_alinhados_revisao_local": "trechos_alinhados",
        "trechos_divergentes_revisao_local": "trechos_divergentes",
        "sem_previa": "sem_previa",
        "previa_ou_referencia_invalida": "afericao_invalida",
        "previa_invalida": "afericao_invalida",
    }
    if (not itens or any(not isinstance(item, Mapping)
                         or not isinstance(item.get("id"), str)
                         or item.get("aprovado_para_producao") is not False
                         or item.get("autoriza_efeito") is not False
                         or not isinstance(item.get("afericao_previa"), Mapping)
                         for item in itens)):
        return {**base, "estado": "entrada_invalida"}
    ids = [item["id"] for item in itens]
    if len(ids) != len(set(ids)):
        return {**base, "estado": "entrada_invalida"}
    contagens = {"trechos_alinhados": 0, "trechos_divergentes": 0,
                 "sem_previa": 0, "afericao_invalida": 0}
    previas = 0
    for item in itens:
        afericao = item["afericao_previa"]
        estado = afericao.get("estado")
        tem_previa = "particao_objeto_em_sombra" in item
        previa = item.get("particao_objeto_em_sombra")
        if (not isinstance(estado, str) or estado not in estados
                or afericao.get("aprovado_para_producao") is not False
                or afericao.get("autoriza_efeito") is not False
                or (tem_previa and (
                    not isinstance(previa, Mapping)
                    or previa.get("aprovado_para_producao") is not False
                    or previa.get("autoriza_efeito") is not False))
                or (estado == "sem_previa") == tem_previa):
            return {**base, "estado": "entrada_invalida"}
        previas += int(tem_previa)
        contagens[estados[estado]] += 1
    return {"estado": "resumo_offline_revisao_local", "casos": len(itens),
            "previas": previas, **contagens, **base}


def medir_caso(
    caso: Mapping[str, object], gabarito: Mapping[str, object],
    nlp: Callable[[str], Iterable[object]],
) -> dict[str, object]:
    """Usa POS do texto inteiro e reconstrói com a mesma guarda literal."""
    gerados = gerar_candidatos(caso)
    resultado = {"id": caso["id"], "candidatos": gerados,
                 "aprovado_para_producao": False, "autoriza_efeito": False}
    if gerados["estado"] != "candidatos_gerados_revisao_pendente":
        return {**resultado, "escolha": "nao_executada_sem_candidatos"}
    if gerados["estrutura_plana_possivel"] is False:
        return {**resultado, "escolha": "recusa_estrutura_plana"}
    fonte = caso["fonte"]
    tokens = list(nlp(fonte))
    segmentos = []
    evidencias = []
    relativa_pendente = False
    escopo_relativo_ambiguo = False
    predicado_pos_ambiguo = False
    for trecho in gerados["candidatos"]:
        verbos = [token for token in tokens
                  if (token.pos_ in {"VERB", "AUX"}
                      and trecho["inicio"] <= token.idx
                      and token.idx + len(token.text) <= trecho["fim"]
                      and fonte[token.idx:token.idx + len(token.text)]
                      == token.text)]
        contraditorios = [token for token in verbos
                          if _pos_verbal_contraditorio(token)]
        if contraditorios:
            predicado_pos_ambiguo = True
            ids_contraditorios = {id(token) for token in contraditorios}
            verbos = [token for token in verbos
                      if id(token) not in ids_contraditorios]
        # POS não verbal com papel oracional pode ser erro de etiquetagem.
        # Não o converta em verbo nem use sua ausência para unir premissas.
        suspeitos_pos = [
            token for token in tokens
            if (token.pos_ not in {"VERB", "AUX"}
                and ((token.pos_ == "ADJ"
                      and (token.dep_ in {"advcl", "acl"}
                           or (token.dep_ == "conj"
                               and any(getattr(filho, "dep_", "")
                                       in {"nsubj", "csubj"}
                                       and trecho["inicio"] <= filho.idx
                                       < trecho["fim"]
                                       for filho in getattr(token, "children", ())))))
                     or (token.dep_ == "ROOT"
                         and any(getattr(outro, "dep_", "") == "nsubj"
                                 and getattr(outro, "head", None) == token
                                 and trecho["inicio"] <= outro.idx < trecho["fim"]
                                 for outro in tokens)))
                and trecho["inicio"] <= token.idx
                and token.idx + len(token.text) <= trecho["fim"])
        ]
        # Uma oração relativa descreve um referente; seu verbo não fecha
        # sozinho a premissa condicional da qual esse referente participa.
        relativos = [token for token in verbos
                     if _em_oracao_relativa(token)]
        verbos = [token for token in verbos if token not in relativos]
        if suspeitos_pos and not verbos:
            predicado_pos_ambiguo = True
        # Após um fragmento composto só de relativa, um verbo logo depois
        # do conectivo pode continuar a relativa ou iniciar a condição.
        # O POS/dependency sozinho não resolve essa fronteira com segurança.
        if (relativa_pendente
                and any(token.idx == trecho["inicio"] for token in verbos)):
            escopo_relativo_ambiguo = True
        relativa_pendente = (relativa_pendente or bool(relativos)) and not verbos
        segmentos.append({"id": trecho["id"],
                          "tem_predicado": bool(verbos),
                          "ancora": verbos[0].text if verbos else ""})
        evidencias.append({"id": trecho["id"],
                           "tokens": [{"texto": token.text, "pos": token.pos_}
                                      for token in verbos],
                           "relativos_excluidos": [token.text
                                                  for token in relativos],
                           "pos_contraditorio": [token.text
                                                  for token in contraditorios],
                           "pos_suspeitos": [token.text
                                             for token in suspeitos_pos]})
    proposta = {"segmentos": segmentos}
    vinculos = _vinculos_objeto_candidatos(
        fonte, gerados["candidatos"], segmentos, tokens,
    )
    resultado = {
        **resultado, "proposta": proposta, "evidencias_pos": evidencias,
        "vinculos_objeto_candidatos": vinculos,
        "continuidades_nominais_candidatas": [
            {chave: item[chave] for chave in
             ("id", "token", "antecedente", "ancora_anterior")}
            for item in vinculos if not item["pos_conflitante"]
        ],
    }
    if escopo_relativo_ambiguo:
        return {**resultado, "escolha": "abstencao_escopo_relativo_ambiguo"}
    if predicado_pos_ambiguo:
        return {**resultado, "escolha": "abstencao_predicado_pos_ambiguo"}
    conversao = reconstruir_condicoes(caso, proposta)
    resultado = {**resultado, "reconstrucao": conversao}
    if conversao["estado"] == "fronteira_interna_sem_predicado_ambigua":
        particao, auditoria = _particao_objeto_em_sombra(
            fonte, gerados["candidatos"], segmentos, vinculos, tokens,
        )
        resultado["auditoria_particao_objeto_em_sombra"] = auditoria
        if particao is not None:
            resultado["particao_objeto_em_sombra"] = particao
    if conversao["estado"] != "segmentos_ancorados_revisao_pendente":
        return resultado
    return {**resultado, "afericao": confrontar_trechos(
        caso, gabarito, conversao["trechos"],
    )}


def main() -> None:
    import spacy

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--painel", type=int,
                        choices=(7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21),
                        default=7)
    parser.add_argument("--modelo-pos", default="pt_core_news_sm")
    parser.add_argument("--resumo", action="store_true",
                        help="conta apenas estados retrospectivos locais")
    args = parser.parse_args()
    nlp = spacy.load(args.modelo_pos)
    casos, gabarito = carregar_painel(args.painel)
    resultados = []
    for caso in casos:
        referencia = gabarito[caso["id"]]
        resultado = medir_caso(caso, referencia, nlp)
        resultado["afericao_previa"] = auditar_previa_em_sombra(
            caso, referencia, resultado,
        )
        if "ancoras_segmentos" in referencia:
            resultado["afericao_ancoras"] = confrontar_ancoras(
                resultado, referencia["ancoras_segmentos"],
            )
        if args.resumo:
            resultados.append(resultado)
        else:
            print(json.dumps(resultado, ensure_ascii=False), flush=True)
    if args.resumo:
        print(json.dumps({"painel": args.painel,
                          **resumir_resultados(resultados)},
                         ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
