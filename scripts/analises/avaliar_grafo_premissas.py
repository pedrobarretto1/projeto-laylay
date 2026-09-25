"""Mede pistas do grafo contra gabarito externo ao auditor, sem aprovar fala."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Mapping

from scripts.analises.grafo_premissas_didaticas import (
    FonteDidatica, ReferenteAncorado, RegraDidatica, conferir_grafo_premissas,
)


def confrontar_condicoes_revisadas(
    fontes: tuple[FonteDidatica, ...],
    referentes: tuple[ReferenteAncorado, ...],
    propostas: tuple[RegraDidatica, ...],
    referencias_revisadas: tuple[RegraDidatica, ...],
    *, escopo: str,
) -> dict[str, object]:
    """Confronta uma proposta com referência separada, sem certificar a fonte.

    Igualdade de slots não prova implicação, conjunção, disjunção nem que as
    condições ocorreram. A referência precisa vir de revisão independente do
    proponente; essa função não autentica o revisor.
    """
    base: dict[str, object] = {
        "estado": "entrada_invalida", "ausentes": [], "extras": [],
        "slots_condicoes_alinhados": False,
        "conectivo_verificado": False,
        "conectivo_alinhado_revisao": False,
        "implicacao_alinhada_revisao": False,
        "revisao_independente_autenticada": False,
        "condicoes_satisfeitas": False,
        "consequencias_observadas": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
    }
    proposta = conferir_grafo_premissas(
        fontes, referentes, (), propostas, escopo=escopo,
    )
    if proposta["estado"] != "estrutura_ancorada_revisao_pendente":
        return {**base, "estado": "proposta_invalida", "motivo": proposta["estado"]}
    referencia = conferir_grafo_premissas(
        fontes, referentes, (), referencias_revisadas, escopo=escopo,
    )
    if referencia["estado"] != "estrutura_ancorada_revisao_pendente":
        return {**base, "estado": "referencia_invalida", "motivo": referencia["estado"]}

    por_id = {regra.identificador: regra for regra in propostas}
    revisadas = {regra.identificador: regra for regra in referencias_revisadas}
    if set(por_id) != set(revisadas):
        return {**base, "estado": "regras_divergentes",
                "regras_ausentes": sorted(set(revisadas) - set(por_id)),
                "regras_extras": sorted(set(por_id) - set(revisadas))}

    ausentes = []
    extras = []
    for identificador, regra_revisada in revisadas.items():
        regra_proposta = por_id[identificador]
        if (regra_proposta.fonte_id != regra_revisada.fonte_id
                or (regra_proposta.efeito_referente_id,
                    regra_proposta.efeito_atributo,
                    regra_proposta.efeito_valor)
                != (regra_revisada.efeito_referente_id,
                    regra_revisada.efeito_atributo,
                    regra_revisada.efeito_valor)):
            return {**base, "estado": "efeito_ou_fonte_divergente",
                    "regra_id": identificador}
        contador_proposto = Counter(regra_proposta.condicoes)
        for condicao in regra_revisada.condicoes:
            if contador_proposto[condicao]:
                contador_proposto[condicao] -= 1
            else:
                ausentes.append({"regra_id": identificador, **asdict(condicao)})
        contador_revisado = Counter(regra_revisada.condicoes)
        for condicao in regra_proposta.condicoes:
            if contador_revisado[condicao]:
                contador_revisado[condicao] -= 1
            else:
                extras.append({"regra_id": identificador, **asdict(condicao)})

    if ausentes and extras:
        estado = "condicoes_divergentes"
    elif ausentes:
        estado = "condicao_omitida"
    elif extras:
        estado = "condicao_extra"
    else:
        estado = "slots_condicoes_alinhados_revisao_pendente"
    if estado != "slots_condicoes_alinhados_revisao_pendente":
        return {**base, "estado": estado, "ausentes": ausentes,
                "extras": extras}

    base_alinhada = {**base, "slots_condicoes_alinhados": True}
    conectivos_alinhados = []
    implicacoes_alinhadas = []
    for identificador, regra_revisada in revisadas.items():
        regra_proposta = por_id[identificador]
        if regra_revisada.conectivo_condicoes != "indeterminado":
            if regra_proposta.conectivo_condicoes == "indeterminado":
                return {**base_alinhada, "estado": "conectivo_pendente",
                        "regra_id": identificador}
            if regra_proposta.conectivo_condicoes != regra_revisada.conectivo_condicoes:
                return {**base_alinhada, "estado": "conectivo_divergente",
                        "regra_id": identificador}
            conectivos_alinhados.append(True)
        if regra_revisada.direcao_implicacao != "indeterminado":
            if regra_proposta.direcao_implicacao == "indeterminado":
                return {**base_alinhada, "estado": "implicacao_pendente",
                        "regra_id": identificador}
            if regra_proposta.direcao_implicacao != regra_revisada.direcao_implicacao:
                return {**base_alinhada, "estado": "implicacao_divergente",
                        "regra_id": identificador}
            implicacoes_alinhadas.append(True)
    relacoes_completas = (len(conectivos_alinhados) == len(revisadas)
                         and len(implicacoes_alinhadas) == len(revisadas))
    return {
        **base_alinhada,
        "estado": ("slots_e_relacao_alinhados_revisao_pendente"
                   if relacoes_completas else estado),
        "conectivo_alinhado_revisao": bool(conectivos_alinhados),
        "implicacao_alinhada_revisao": bool(implicacoes_alinhadas),
    }


def confrontar_gabarito(
    auditoria: Mapping[str, object], gabarito: Mapping[str, object],
    *, cobertura: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Retorna falhas/abstenções por slot; não autentica o revisor do gabarito."""
    base = {"estado": "avaliacao_invalida", "motivo": "entrada_invalida",
            "slots": {}, "contagens": {},
            "cobertura_condicoes": "nao_medida",
            "relacao_condicional": "nao_medida",
            "aprovado_para_compor": False, "autoriza_efeito": False}
    if not isinstance(auditoria, Mapping) or not isinstance(gabarito, Mapping):
        return base
    if (auditoria.get("estado") != "pistas_literais_revisao_pendente"
            or not isinstance(auditoria.get("premissas"), Mapping)
            or not isinstance(auditoria.get("condicoes"), Mapping)
            or not isinstance(auditoria.get("efeitos"), Mapping)
            or not isinstance(gabarito.get("slots"), Mapping)
            or type(gabarito.get("condicoes_completas")) is not bool):
        return {**base, "motivo": str(auditoria.get("estado"))}

    observados: dict[str, str] = {}
    for identificador, estado in auditoria["premissas"].items():
        observados[f"premissa:{identificador}"] = estado
    for identificador, condicoes in auditoria["condicoes"].items():
        if not isinstance(condicoes, list) or any(
            not isinstance(item, Mapping)
            or not isinstance(item.get("referente"), str)
            or not isinstance(item.get("direcao"), str)
            for item in condicoes
        ):
            return base
        for indice, item in enumerate(condicoes):
            observados[f"condicao:{identificador}:{indice}:referente"] = item["referente"]
            observados[f"condicao:{identificador}:{indice}:direcao"] = item["direcao"]
    for identificador, estado in auditoria["efeitos"].items():
        observados[f"efeito:{identificador}"] = estado

    rotulos = gabarito["slots"]
    if (not rotulos or set(rotulos) != set(observados)
            or any(type(valor) is not bool for valor in rotulos.values())):
        return {**base, "motivo": "cobertura_divergente",
                "slots_faltantes": sorted(set(observados) - set(rotulos)),
                "slots_extras": sorted(set(rotulos) - set(observados))}

    estado_cobertura = "nao_medida"
    estado_relacao = "nao_medida"
    if cobertura is not None:
        if not isinstance(cobertura, Mapping):
            return base
        estado_comparador = str(cobertura.get("estado"))
        alinhada = cobertura.get("slots_condicoes_alinhados")
        if (type(alinhada) is not bool or estado_comparador not in {
                "slots_condicoes_alinhados_revisao_pendente", "condicao_omitida",
                "condicao_extra", "condicoes_divergentes",
                "conectivo_pendente", "conectivo_divergente",
                "implicacao_pendente", "implicacao_divergente",
                "slots_e_relacao_alinhados_revisao_pendente",
            } or alinhada != gabarito["condicoes_completas"]):
            return {**base, "motivo": "gabarito_ou_cobertura_divergente"}
        estado_cobertura = (
            "slots_alinhados_revisao_pendente" if alinhada else estado_comparador
        )
        if alinhada:
            estado_relacao = (
                "relacao_pendente" if estado_comparador
                == "slots_condicoes_alinhados_revisao_pendente"
                else estado_comparador
            )
        else:
            estado_relacao = "nao_avaliada_por_condicoes"

    estados: dict[str, str] = {}
    contagens = {nome: 0 for nome in (
        "pista_compatível", "pista_falso_positivo", "rejeicao_compatível",
        "rejeicao_incorreta", "abstencao_em_correto", "abstencao_em_incorreto",
    )}
    for identificador, esperado in rotulos.items():
        pista = observados[identificador]
        if pista in {"referente_literal_localizado", "direcao_literal_coerente"}:
            estado = "pista_compatível" if esperado else "pista_falso_positivo"
        elif pista == "direcao_literal_divergente":
            estado = "rejeicao_incorreta" if esperado else "rejeicao_compatível"
        elif pista in {"referente_sem_ancora_literal", "direcao_indeterminada"}:
            estado = "abstencao_em_correto" if esperado else "abstencao_em_incorreto"
        else:
            return {**base, "motivo": "pista_desconhecida"}
        estados[identificador] = estado
        contagens[estado] += 1
    return {**base, "estado": "confronto_diagnostico", "slots": estados,
            "contagens": contagens, "cobertura_condicoes": estado_cobertura,
            "relacao_condicional": estado_relacao}
