"""Coordena conversa e operação mantendo uma memória, executor e voz."""

from __future__ import annotations

from typing import Any, Dict, Iterable

from mente_laylay.especialistas.conversa import construir_parecer_conversa
from mente_laylay.especialistas.deliberacao import (
    criar_parecer_habilidade,
    deliberar_habilidades,
)
from mente_laylay.especialistas.operacional import (
    anexar_resultados_operacionais,
    construir_parecer_operacional,
)


def construir_parecer_especialistas(
    texto: str,
    *,
    turno: Dict[str, Any] | None,
    funcao_comunicativa: Dict[str, Any] | None,
    retrato: Dict[str, Any] | None,
    saude: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    leitura = dict(turno or {})
    funcao = dict(funcao_comunicativa or {})
    snapshot = dict(retrato or {})
    operacional = construir_parecer_operacional(texto, turno=leitura, retrato=snapshot)
    operacional["saude_componentes"] = dict(saude or {})
    social = construir_parecer_conversa(
        texto,
        turno=leitura,
        funcao_comunicativa=funcao,
        operacional_ativo=bool(operacional.get("ativo")),
    )

    aprendizados_explicitos = [
        dict(item) for item in list(leitura.get("aprendizados_explicitos") or [])
        if isinstance(item, dict)
    ]
    tema_factual = str(leitura.get("tema_factual") or "").strip()
    referencia = dict(snapshot.get("referencia_resolvida") or {})
    candidatos_referencia = [
        dict(item) for item in list(snapshot.get("referencia_candidatos") or [])
        if isinstance(item, dict)
    ]
    contexto_ativo = bool(referencia or candidatos_referencia)
    confianca_contexto = float(
        referencia.get("confianca")
        or (candidatos_referencia[0].get("pontuacao") if candidatos_referencia else 0.0)
        or (0.95 if referencia else 0.0)
    )

    pareceres_habilidades = [
        criar_parecer_habilidade(
            "conversa",
            ativo=bool(social.get("ativo")),
            proposta=(
                "acolher e responder ao significado humano da fala atual"
                if social.get("ativo") else ""
            ),
            confianca=0.94 if social.get("ativo") else 0.0,
            relevancia=1.0,
            evidencias=(
                f"funcao_comunicativa:{social.get('funcao') or 'informacao'}",
                f"postura:{social.get('postura') or 'natural'}",
            ),
            politica_falha="interromper_resposta",
        ),
        criar_parecer_habilidade(
            "operacao",
            ativo=bool(operacional.get("ativo")),
            proposta=(
                "executar somente a ação consensual autorizada e devolver o resultado real"
                if operacional.get("autoriza_execucao")
                else "interpretar a possível ação sem produzir efeito não autorizado"
            ),
            confianca=float(operacional.get("confianca") or 0.0),
            relevancia=1.0 if operacional.get("ativo") else 0.0,
            evidencias=(
                f"operacao:{operacional.get('operacao') or '-'}",
                f"autorizada:{bool(operacional.get('autoriza_execucao'))}",
            ),
            autoriza_execucao=bool(operacional.get("autoriza_execucao")),
            politica_falha="continuar_com_resultado_real",
        ),
        criar_parecer_habilidade(
            "contexto_geral",
            ativo=contexto_ativo,
            proposta="resolver referências e manter o assunto correto para as demais habilidades",
            confianca=confianca_contexto,
            relevancia=0.92 if contexto_ativo else 0.0,
            evidencias=(
                f"referencia:{referencia.get('nome') or '-'}",
                f"candidatos:{len(candidatos_referencia)}",
            ),
            silenciosa=True,
        ),
        criar_parecer_habilidade(
            "memoria_aprendizado",
            ativo=bool(aprendizados_explicitos),
            proposta="registrar silenciosamente somente o que o usuário declarou de forma explícita",
            confianca=max(
                (float(item.get("confianca") or 0.0) for item in aprendizados_explicitos),
                default=0.0,
            ),
            relevancia=0.98 if aprendizados_explicitos else 0.0,
            evidencias=(
                f"declaracoes_explicitas:{len(aprendizados_explicitos)}",
                "origem:usuario",
            ),
            silenciosa=True,
        ),
        criar_parecer_habilidade(
            "pesquisa_factual",
            ativo=bool(tema_factual),
            proposta="enriquecer a conversa com fatos verificáveis quando houver evidência suficiente",
            confianca=0.78 if tema_factual else 0.0,
            relevancia=0.76 if tema_factual else 0.0,
            evidencias=(f"tema:{tema_factual or '-'}",),
            silenciosa=True,
        ),
        criar_parecer_habilidade(
            "personalidade",
            ativo=True,
            proposta="fundir as contribuições aceitas em uma resposta natural com a voz da Laylay",
            confianca=0.96,
            relevancia=0.96,
            evidencias=("uma_mente", "uma_voz"),
            dependencias=("conversa",) if social.get("ativo") else (),
            politica_falha="usar_fala_segura_sem_apagar_o_contexto",
        ),
    ]
    deliberacao = deliberar_habilidades(
        pareceres_habilidades,
        objetivo_turno=str(
            funcao.get("objetivo")
            or "combinar as habilidades adequadas para responder à fala atual"
        ),
    )

    if social.get("ativo") and operacional.get("ativo"):
        modo = "integrado"
        ordem = ["reconhecer_parte_humana", "executar_parte_operacional", "unificar_resultado"]
        consultas = [
            "operacional_consulta_limites_sociais_antes_de_agir",
            "social_consulta_resultado_operacional_antes_de_falar",
        ]
    elif operacional.get("ativo"):
        modo = "operacional"
        ordem = ["executar_parte_operacional", "informar_resultado_real"]
        consultas = []
    else:
        modo = "social"
        ordem = ["responder_parte_humana"]
        consultas = []

    return {
        "social": social,
        "operacional": operacional,
        "coordenacao": {
            "modo": modo,
            "ordem": ordem,
            "consultas": consultas,
            "memoria_compartilhada": True,
            "voz_unica": True,
            "executor_unico": True,
            "consulta_concluida": False,
            "arquitetura": "consenso_distribuido",
            "sem_vencedor_isolado": True,
        },
        "pareceres_habilidades": pareceres_habilidades,
        "deliberacao": deliberacao,
    }


def registrar_resultado_operacional(
    especialistas: Dict[str, Any] | None,
    comandos: Iterable[Dict[str, Any]] = (),
) -> Dict[str, Any]:
    painel = dict(especialistas or {})
    social = dict(painel.get("social") or {})
    coordenacao = dict(painel.get("coordenacao") or {})
    operacional, possui_resultado = anexar_resultados_operacionais(
        dict(painel.get("operacional") or {}),
        comandos,
    )
    if possui_resultado:
        social["resultado_operacional_consultado"] = bool(social.get("ativo"))
        coordenacao["consulta_concluida"] = True
    painel.update(social=social, operacional=operacional, coordenacao=coordenacao)
    return painel
