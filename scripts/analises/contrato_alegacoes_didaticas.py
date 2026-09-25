"""Contrato offline para propostas de alegações de uma fala didática inteira.

O modelo pode propor papéis e citações, mas fontes registradas vêm do chamador.
Cobertura dos caracteres e cópia literal são recibos formais, não implicação.
Nenhum resultado desta sonda autoriza publicação, efeito ou veto de fala.
"""

from __future__ import annotations

from typing import Mapping, Sequence


_PAPEIS = frozenset({
    "premissa_usuario", "regra_hipotetica", "comparacao_numerica",
    "conclusao_derivada", "fato_externo", "nao_factual",
})
_ORIGENS_CITAVEIS = frozenset({"usuario", "pesquisa_verificada"})


def conferir_mapa_alegacoes(
    fala: str, *, fontes: Mapping[str, Mapping[str, str]],
    propostas: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Confere envelope textual e citações; deixa semântica para revisão.

    Não assume que os intervalos propostos são de fato alegações atômicas.
    ``pesquisa_verificada`` deve ser atribuída por outro serviço confiável,
    nunca pelo JSON proposto pelo modelo.
    """
    base: dict[str, object] = {
        "cobertura_textual": False,
        "atomizacao_verificada": False,
        "papeis_verificados": False,
        "condicoes_verificadas": False,
        "implicacao_verificada": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
        "alegacoes": [],
    }
    if (not isinstance(fala, str) or not fala or len(fala) > 4000
            or not isinstance(fontes, Mapping)
            or not isinstance(propostas, (list, tuple))
            or not propostas or len(propostas) > 128):
        return {**base, "estado": "entrada_invalida"}
    posicao = 0
    for proposta in propostas:
        if not isinstance(proposta, Mapping):
            return {**base, "estado": "proposta_invalida"}
        inicio, fim = proposta.get("inicio"), proposta.get("fim")
        if (type(inicio) is not int or type(fim) is not int
                or inicio != posicao or not inicio < fim <= len(fala)
                or not isinstance(proposta.get("papel"), str)
                or proposta.get("papel") not in _PAPEIS
                or not isinstance(proposta.get("evidencias"), list)
                or len(proposta["evidencias"]) > 16):
            return {**base, "estado": "cobertura_invalida"}
        posicao = fim
    if posicao != len(fala):
        return {**base, "estado": "cobertura_invalida"}

    alegacoes: list[dict[str, object]] = []
    for proposta in propostas:
        evidencias = proposta["evidencias"]
        estado = "revisao_semantica_pendente"
        if proposta["papel"] == "nao_factual":
            estado = "nao_factual_proposto_revisao_pendente"
        elif not evidencias:
            estado = "sem_fonte"
        else:
            for evidencia in evidencias:
                if not isinstance(evidencia, Mapping):
                    estado = "evidencia_invalida"
                    break
                identificador = evidencia.get("fonte_id")
                fonte = fontes.get(identificador) if isinstance(identificador, str) else None
                if not isinstance(fonte, Mapping):
                    estado = "fonte_desconhecida"
                    break
                origem = fonte.get("origem")
                if not isinstance(origem, str) or origem not in _ORIGENS_CITAVEIS:
                    estado = "fonte_sem_autoridade"
                    break
                citacao = evidencia.get("citacao")
                texto_fonte = fonte.get("texto")
                if (not isinstance(citacao, str) or not citacao.strip()
                        or not isinstance(texto_fonte, str)
                        or citacao not in texto_fonte):
                    estado = "citacao_invalida"
                    break
        alegacoes.append({
            "inicio": proposta["inicio"], "fim": proposta["fim"],
            "texto": fala[proposta["inicio"]:proposta["fim"]],
            "papel_proposto": proposta["papel"],
            "estado": estado,
            "fontes_literalmente_conferidas": estado == "revisao_semantica_pendente",
        })
    pendencias = {item["estado"] for item in alegacoes}
    return {
        **base,
        "estado": (
            "evidencia_invalida" if pendencias & {
            "evidencia_invalida", "fonte_desconhecida",
                "fonte_sem_autoridade", "citacao_invalida",
            } else "alegacoes_sem_fonte" if "sem_fonte" in pendencias
            else "papeis_semanticos_pendentes"
            if "nao_factual_proposto_revisao_pendente" in pendencias
            else "cobertura_formal_revisao_pendente"
        ),
        "cobertura_textual": True,
        "alegacoes": alegacoes,
    }
