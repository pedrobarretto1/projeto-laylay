"""Codec de saída explicitamente negociada, com validação pelo owner."""

from __future__ import annotations

import json
import re
from dataclasses import InitVar, dataclass, field
from typing import Any, Callable, Mapping


def _objeto_sem_duplicatas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    objeto: dict[str, Any] = {}
    for chave, valor in pares:
        if chave in objeto:
            raise ValueError("chave JSON duplicada")
        objeto[chave] = valor
    return objeto


def _recusar_constante(_valor: str) -> None:
    raise ValueError("constante JSON não finita")


@dataclass(frozen=True)
class ContratoSaidaEstruturada:
    """O schema transporta o formato; o validator do domínio confere os dados.

    Validar a estrutura não transforma proposta em fato ou autorização. O
    marcador só é publicado depois da validação integral da resposta tipada.
    """

    nome: str
    marcador: str
    esquema: InitVar[Mapping[str, Any]]
    validar: Callable[[dict[str, Any]], None] = field(repr=False)
    _esquema_json: str = field(init=False, repr=False)

    def __post_init__(self, esquema: Mapping[str, Any]) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.nome):
            raise ValueError("nome de contrato inválido")
        if not self.marcador or self.marcador.strip() != self.marcador:
            raise ValueError("marcador de contrato inválido")
        if not callable(self.validar) or not isinstance(esquema, Mapping):
            raise TypeError("contrato exige schema e validator do owner")
        object.__setattr__(self, "_esquema_json", json.dumps(
            dict(esquema), ensure_ascii=False, allow_nan=False,
        ))

    @property
    def response_format(self) -> dict[str, Any]:
        return {"type": "json_schema", "json_schema": {
            "name": self.nome, "strict": True,
            "schema": json.loads(self._esquema_json),
        }}

    @property
    def instrucao_formato(self) -> str:
        return (
            f"CONTRATO DE SAÍDA NEGOCIADO: {self.nome}. Responda somente com "
            "um objeto JSON que obedeça ao schema informado no transporte. "
            f"O marcador {self.marcador} será inserido pelo host após a validação; "
            "não escreva esse marcador, prosa externa ou blocos Markdown. Nesta "
            "consulta tipada, esta regra de formato prevalece sobre pedidos de "
            "prefixo textual na pergunta. Preserve todas as demais restrições "
            "de evidência, incerteza e ausência de autoridade."
        )

    def canonizar_json(self, resposta: str) -> str:
        """Decodifica somente o documento completo; não procura JSON na prosa."""
        if not isinstance(resposta, str):
            raise TypeError("resposta estruturada deve ser textual")
        dados = json.loads(
            resposta, object_pairs_hook=_objeto_sem_duplicatas,
            parse_constant=_recusar_constante,
        )
        if not isinstance(dados, dict):
            raise ValueError("resposta estruturada deve ser um objeto")
        self.validar(dados)
        return self.marcador + " " + json.dumps(
            dados, ensure_ascii=False, allow_nan=False, separators=(",", ":"),
        )

    def validar_framing(self, resposta: str) -> str:
        """Compatibilidade de provedor que já produz o framing contratado."""
        texto = str(resposta or "").strip()
        if not texto.startswith(self.marcador):
            raise ValueError("resposta sem o marcador contratado")
        return self.canonizar_json(texto[len(self.marcador):].strip())


class AnaliseVisualComContrato:
    """Publica explicitamente a capacidade opcional da porta instalada."""

    suporta_contrato_saida = True

    def __init__(self, analisar: Callable[..., str]) -> None:
        self._analisar = analisar

    def __call__(
        self, imagem: str, pergunta: str, *,
        contrato_saida: ContratoSaidaEstruturada | None = None,
    ) -> str:
        if contrato_saida is None:
            return self._analisar(imagem, pergunta)
        return self._analisar(imagem, pergunta, contrato_saida=contrato_saida)
