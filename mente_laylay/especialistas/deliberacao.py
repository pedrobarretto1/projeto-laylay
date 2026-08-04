"""Deliberação distribuída entre habilidades da mente única.

Cada habilidade publica um parecer pequeno e verificável. O deliberador não
escolhe um vencedor: ele forma uma coalizão com os pareceres compatíveis e
registra por que cada contribuição entrou ou ficou de fora. A execução segue
separada e continua sujeita aos porteiros de segurança.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


LIMIAR_ATIVACAO = 0.35


def criar_parecer_habilidade(
    nome: str,
    *,
    ativo: bool,
    proposta: str,
    confianca: float,
    relevancia: float,
    evidencias: Iterable[str] = (),
    dependencias: Iterable[str] = (),
    conflitos: Iterable[str] = (),
    silenciosa: bool = False,
    autoriza_execucao: bool = False,
    politica_falha: str = "continuar_sem_substituir_resposta",
    saude: float = 1.0,
) -> dict[str, Any]:
    """Normaliza a hipótese de uma habilidade antes da deliberação."""
    confianca_segura = max(0.0, min(1.0, float(confianca or 0.0)))
    relevancia_segura = max(0.0, min(1.0, float(relevancia or 0.0)))
    saude_segura = max(0.0, min(1.0, float(saude or 0.0)))
    ativacao = confianca_segura * relevancia_segura * saude_segura if ativo else 0.0
    return {
        "habilidade": str(nome or "").strip()[:80],
        "ativo": bool(ativo),
        "proposta": str(proposta or "").strip()[:240],
        "confianca": round(confianca_segura, 3),
        "relevancia": round(relevancia_segura, 3),
        "saude": round(saude_segura, 3),
        "ativacao": round(ativacao, 3),
        "evidencias": [str(item)[:160] for item in evidencias if str(item).strip()][:8],
        "dependencias": [str(item)[:80] for item in dependencias if str(item).strip()][:8],
        "conflitos": [str(item)[:80] for item in conflitos if str(item).strip()][:8],
        "silenciosa": bool(silenciosa),
        "autoriza_execucao": bool(autoriza_execucao),
        "politica_falha": str(politica_falha or "continuar_sem_substituir_resposta")[:80],
    }


def deliberar_habilidades(
    pareceres: Iterable[Mapping[str, Any]],
    *,
    objetivo_turno: str,
) -> dict[str, Any]:
    """Forma uma coalizão compatível sem eleger uma habilidade vencedora."""
    candidatos = [dict(item) for item in pareceres if isinstance(item, Mapping)]
    ativos = [item for item in candidatos if bool(item.get("ativo"))]
    nomes_ativos = {str(item.get("habilidade") or "") for item in ativos}
    selecionados: list[dict[str, Any]] = []
    rejeitados: list[dict[str, Any]] = []

    for parecer in ativos:
        nome = str(parecer.get("habilidade") or "")
        ativacao = float(parecer.get("ativacao") or 0.0)
        conflitos_presentes = sorted(
            item for item in set(parecer.get("conflitos") or ()) if item in nomes_ativos
        )
        dependencias_ausentes = sorted(
            item for item in set(parecer.get("dependencias") or ()) if item not in nomes_ativos
        )
        if ativacao < LIMIAR_ATIVACAO:
            rejeitados.append({
                "habilidade": nome,
                "motivo": "ativacao_insuficiente",
                "ativacao": round(ativacao, 3),
            })
            continue
        if conflitos_presentes:
            rejeitados.append({
                "habilidade": nome,
                "motivo": "conflito_nao_resolvido",
                "com": conflitos_presentes,
                "ativacao": round(ativacao, 3),
            })
            continue
        # Dependência ausente não inventa um bloqueio global: a contribuição
        # entra como parcial quando sua política permite seguir sem ela.
        parcial = bool(dependencias_ausentes)
        if parcial and str(parecer.get("politica_falha") or "").startswith("interromper"):
            rejeitados.append({
                "habilidade": nome,
                "motivo": "dependencia_ausente",
                "dependencias": dependencias_ausentes,
                "ativacao": round(ativacao, 3),
            })
            continue
        parecer["contribuicao_parcial"] = parcial
        parecer["dependencias_ausentes"] = dependencias_ausentes
        selecionados.append(parecer)

    selecionados.sort(key=lambda item: float(item.get("ativacao") or 0.0), reverse=True)
    participantes = [str(item.get("habilidade") or "") for item in selecionados]
    silenciosas = [
        str(item.get("habilidade") or "")
        for item in selecionados if bool(item.get("silenciosa"))
    ]
    executoras = [
        str(item.get("habilidade") or "")
        for item in selecionados if bool(item.get("autoriza_execucao"))
    ]
    evidencias = list(dict.fromkeys(
        str(evidencia)
        for parecer in selecionados
        for evidencia in list(parecer.get("evidencias") or ())
        if str(evidencia).strip()
    ))[:12]
    propostas = [
        str(item.get("proposta") or "")
        for item in selecionados if str(item.get("proposta") or "").strip()
    ]
    return {
        "arquitetura": "consenso_distribuido",
        "objetivo": str(objetivo_turno or "responder ao turno atual")[:240],
        "estado": "consenso_formado" if selecionados else "sem_coalizao",
        "participantes": participantes,
        "silenciosas": silenciosas,
        "executoras_autorizadas": executoras,
        "pareceres": selecionados,
        "rejeitados": rejeitados,
        "evidencias_compartilhadas": evidencias,
        "conclusao_conjunta": propostas,
        "rodadas": (
            {"fase": "hipoteses", "participantes": [str(item.get("habilidade") or "") for item in ativos]},
            {"fase": "compatibilidade", "aceitos": participantes, "rejeitados": len(rejeitados)},
            {"fase": "consenso", "contribuicoes": len(propostas)},
        ),
        "regras": {
            "sem_vencedor_isolado": True,
            "voz_final_unica": True,
            "falha_auxiliar_nao_substitui_resposta": True,
            "execucao_somente_por_porteiro_canonico": True,
            "memoria_e_aprendizado_silenciosos": True,
        },
    }
