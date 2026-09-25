"""Contrato offline para confrontar definição e exemplo por relação.

As relações são anotações propostas, NÃO são extraídas nem certificadas pela
fonte. Compatibilidade estrutural nunca equivale a suporte semântico.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from scripts.analises.sonda_composicao_extrativa_ensino import validar_unidade


@dataclass(frozen=True)
class RelacaoAnotada:
    fonte_id: str
    trecho: str
    papel: str
    relacao: str
    papeis: tuple[tuple[str, str], ...]
    condicoes: frozenset[str] = frozenset()


def avaliar_vinculo(
    definicao: RelacaoAnotada,
    exemplo: RelacaoAnotada,
    fontes: Mapping[str, Mapping[str, str]],
) -> dict[str, object]:
    """Localiza trechos, depois confronta relação, papéis e condições."""
    base: dict[str, object] = {
        "aprovado_para_compor": False,
        "anotacao_semantica_revisada": False,
    }
    if (definicao.papel != "definicao" or exemplo.papel != "exemplo"
            or not definicao.relacao or not exemplo.relacao
            or len(dict(definicao.papeis)) != len(definicao.papeis)
            or len(dict(exemplo.papeis)) != len(exemplo.papeis)):
        return {**base, "estado": "anotacao_invalida"}
    for registro in (definicao, exemplo):
        recibo = validar_unidade(
            {"tipo": "literal", "papel": registro.papel,
             "fonte_id": registro.fonte_id, "trecho": registro.trecho},
            fontes, "",
        )
        if recibo["estado"] != "literal_rastreavel":
            return {**base, "estado": "evidencia_literal_invalida",
                    "motivo": recibo["estado"]}
    if definicao.relacao != exemplo.relacao:
        return {**base, "estado": "relacao_diferente"}
    if dict(definicao.papeis) != dict(exemplo.papeis):
        return {**base, "estado": "direcao_ou_papeis_diferentes"}
    if not definicao.condicoes.issubset(exemplo.condicoes):
        return {**base, "estado": "condicao_omitida",
                "condicoes_ausentes": sorted(definicao.condicoes - exemplo.condicoes)}
    return {**base, "estado": "estrutura_compativel_revisao_pendente",
            "proveniencia_literal": True}
