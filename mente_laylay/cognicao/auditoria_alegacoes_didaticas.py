"""Observação de proveniência da fala didática, sem poder de publicação.

Esta auditoria só localiza pistas textuais e confere aritmética elementar.
Uma citação, mesmo literal, não demonstra implicação, escopo, causalidade ou
verdade externa. Os segmentos são candidatos textuais, não alegações já
interpretadas semanticamente.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Mapping, Sequence


_LIMITE_FONTES = 6
_DIVISORES = re.compile(
    r"[.!?;]+(?=\s|$)|,(?=\s)|\s+(?=(?:e|então|porque|pois|portanto)\b)",
    flags=re.IGNORECASE,
)
_MEDIDA = re.compile(r"(?<!\w)(\d+(?:[.,]\d+)?)\s*(%|°\s*[CF])(?!\w)", re.IGNORECASE)
_RELACAO_MENOR = re.compile(
    r"(?<!\w)(\d+(?:[.,]\d+)?)\s*(%|°\s*[CF])\s*"
    r"([^.!?;]{0,65}?)\b(?:abaixo\s+de|menor\s+(?:do\s+)?que)\s*"
    r"(?:[^.!?;]{0,25}?)?"
    r"(\d+(?:[.,]\d+)?)\s*(%|°\s*[CF])",
    flags=re.IGNORECASE,
)


def _normalizar(texto: str) -> str:
    sem_acentos = "".join(
        letra for letra in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(letra)
    )
    return " ".join(sem_acentos.split())


def _medidas(texto: str) -> set[tuple[float, str]]:
    return {
        (float(item.group(1).replace(",", ".")), item.group(2).replace(" ", "").casefold())
        for item in _MEDIDA.finditer(texto)
    }


def _comparacoes_aritmeticas(
    fala: str, medidas_fontes: set[tuple[float, str]],
) -> list[tuple[int, int]]:
    """Confere apenas números, unidades e ordem; nunca a entidade medida."""
    confirmadas: list[tuple[int, int]] = []
    for item in _RELACAO_MENOR.finditer(fala):
        entre = _normalizar(item.group(3))
        if re.search(r"\b(?:nao|nunca|nem)\b", entre):
            continue
        valor_a = float(item.group(1).replace(",", "."))
        valor_b = float(item.group(4).replace(",", "."))
        unidade_a = item.group(2).replace(" ", "").casefold()
        unidade_b = item.group(5).replace(" ", "").casefold()
        if (unidade_a == unidade_b and valor_a < valor_b
                and (valor_a, unidade_a) in medidas_fontes
                and (valor_b, unidade_b) in medidas_fontes):
            confirmadas.append(item.span())
    return confirmadas


def fontes_usuario_da_conversa(
    texto_atual: str, mensagens: Sequence[object],
) -> dict[str, str]:
    """Fontes candidatas somente de turnos do usuário na sessão corrente.

    O texto atual entra mesmo se ainda não tiver sido gravado no histórico.
    Fontes candidatas não são autorização de efeito nem prova factual externa.
    """
    fontes: dict[str, str] = {}
    atual = str(texto_atual or "").strip()[:500]
    if atual:
        fontes["turno_atual"] = atual
    anteriores = [
        str(item.get("content") or "").strip()[:500]
        for item in mensagens
        if isinstance(item, Mapping)
        and str(item.get("role") or "").casefold() == "user"
        and isinstance(item.get("content"), str)
        and str(item.get("content") or "").strip()
    ][-_LIMITE_FONTES:]
    for indice, texto in enumerate(reversed(anteriores), start=1):
        if texto != atual and texto not in fontes.values():
            fontes[f"usuario_recente_{indice}"] = texto
    return fontes


def auditar_fala_didatica_sombra(
    fala: str, *, fontes: Mapping[str, str], plano_id: object,
) -> dict[str, object]:
    """Registra lacunas para revisão sem vetar, reparar ou aprovar a fala."""
    fala_integral = str(fala or "")
    truncada = len(fala_integral) > 4000
    texto = fala_integral[:4000]
    fontes_validas = {
        str(identificador): conteudo[:1000]
        for identificador, conteudo in fontes.items()
        if isinstance(identificador, str) and identificador
        and isinstance(conteudo, str) and conteudo.strip()
    }
    medidas_fontes = set().union(*(_medidas(valor) for valor in fontes_validas.values()))
    comparacoes = _comparacoes_aritmeticas(texto, medidas_fontes)
    segmentos: list[dict[str, object]] = []
    inicio = 0
    limites = [achado.end() for achado in _DIVISORES.finditer(texto)] + [len(texto)]
    for fim in limites:
        if fim <= inicio:
            continue
        trecho = texto[inicio:fim]
        literal = _normalizar(trecho).strip(" ,.;:!?")
        candidatas = [
            identificador for identificador, fonte in fontes_validas.items()
            if literal and literal in _normalizar(fonte)
        ]
        comparacao = any(inicio <= primeiro < fim for primeiro, _ in comparacoes)
        estado = (
            "comparacao_aritmetica_revisao_pendente" if comparacao else
            "citacao_literal_revisao_pendente" if candidatas else
            "revisao_semantica_pendente"
        )
        segmentos.append({
            "inicio": inicio, "fim": fim, "texto": trecho,
            "estado": estado, "fontes_candidatas": candidatas,
            "comparacao_aritmetica_confirmada": comparacao,
            "implicacao_verificada": False,
        })
        inicio = fim
    return {
        "plano_id": str(plano_id or ""),
        "fase": "fala_pos_verificacao_candidata",
        "estado": "fala_truncada" if truncada else "observado" if segmentos else "fala_vazia",
        "fontes_disponiveis": list(fontes_validas),
        "segmentos": segmentos,
        "cobertura_textual": (
            not truncada and "".join(item["texto"] for item in segmentos) == texto
        ),
        "cobertura_semantica": False,
        "aprovado_para_compor": False,
        "autoriza_efeito": False,
    }
