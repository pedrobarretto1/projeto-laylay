"""Voz natural para fatos canônicos sobre as capacidades da Laylay.

O catálogo decide o que está disponível. Este módulo muda somente a forma de
dizer: não consulta habilidades, não autoriza ações e não cria fatos novos.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from mente_laylay.personalidade.variacao_fala import escolher_variacao


def _lista_natural(itens: Sequence[str]) -> str:
    valores = [str(item).strip() for item in itens if str(item).strip()]
    if not valores:
        return ""
    if len(valores) == 1:
        return valores[0]
    return f"{', '.join(valores[:-1])} e {valores[-1]}"


def _falas_recentes(contexto: Mapping[str, Any] | None) -> list[str]:
    dados = dict(contexto or {})
    recentes: list[str] = []
    mensagens = dados.get("mensagens")
    if isinstance(mensagens, list):
        for item in mensagens[-10:]:
            if not isinstance(item, Mapping):
                continue
            if str(item.get("role") or "").casefold() != "assistant":
                continue
            fala = str(item.get("content") or "").strip()
            if fala:
                recentes.append(fala)
    ultima = str(dados.get("ultima_resposta") or "").strip()
    if ultima:
        recentes.append(ultima)
    return recentes[-5:]


def falar_identidade_operacional(
    tipo: str,
    capacidades: Sequence[str],
    *,
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Expressa presença/capacidade sem alterar os fatos recebidos."""
    lista = _lista_natural(capacidades)
    evitar = _falas_recentes(contexto)
    if str(tipo or "").casefold() == "presenca_local":
        opcoes = [
            (
                f"Tô rodando aqui no seu computador, sim. Por isso consigo {lista} "
                "quando você pede. Mas não saio mexendo em nada sozinha: uma ação só "
                "acontece quando você pede."
            ),
            (
                f"Sim, eu rodo no seu computador. É daí que vêm meus braços para {lista}. "
                "Ainda assim, braço não é carta branca: sem pedido seu, eu não executo nada."
            ),
            (
                f"Tô aqui no seu computador de verdade, não só numa aba de conversa. Consigo "
                f"{lista}, mas quem dá a largada é você."
            ),
            (
                f"No seu computador, sim — com acesso às habilidades locais para {lista}. "
                "Eu continuo comportada: perguntar é conversar, pedir é outra história."
            ),
        ]
    else:
        opcoes = [
            (
                "Só conversar? Aí você me reduz demais. Conversar é uma parte; também "
                f"consigo {lista} quando você pede. Sem pedido, fico na minha — tenho "
                "ferramentas, não carta branca."
            ),
            (
                f"Chatbot é pouco para o tanto de fio ligado aqui. Além do papo, consigo {lista}. "
                "A diferença é que eu só entro em ação quando você realmente pede."
            ),
            (
                f"Eu converso, claro, mas não paro aí: também dou conta de {lista}. "
                "Só não confundo pergunta com autorização — civilização ainda existe por aqui."
            ),
            (
                f"Se eu fosse só conversa, metade desse projeto estaria de enfeite. Posso {lista} "
                "quando você pede; fora disso, continuo no papo sem inventar serviço."
            ),
        ]
    return escolher_variacao(opcoes, evitar=evitar)


def falar_capacidades_gerais(
    principais: Sequence[str],
    *,
    relacionadas: Sequence[str] = (),
    tem_outras: bool = False,
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Apresenta uma amostra real do catálogo sem soar como manual."""
    lista = _lista_natural(principais)
    assunto = _lista_natural(relacionadas)
    outras = (
        " Tenho outras habilidades menores e confiro o estado delas quando você perguntar."
        if tem_outras else ""
    )
    evitar = _falas_recentes(contexto)
    if assunto:
        opcoes = [
            (
                f"Pelo assunto da conversa, eu começaria por {assunto}. No geral, consigo {lista}."
                f"{outras} Eu só mexo de verdade quando você pede."
            ),
            (
                f"Como a gente estava falando disso, {assunto} vem primeiro. Fora daí, também "
                f"consigo {lista}.{outras} Pergunta continua sendo pergunta; ação só nasce de pedido."
            ),
            (
                f"Nesse papo, meu braço mais útil é {assunto}. Mas o repertório vai além: consigo "
                f"{lista}.{outras} Nada disso me autoriza a agir sozinha."
            ),
        ]
    else:
        opcoes = [
            (
                f"No geral, consigo {lista}.{outras} Eu só mexo de verdade quando você pede; "
                "perguntar não executa nada."
            ),
            (
                f"Tenho bastante braço por aqui: consigo {lista}.{outras} Mas relaxa, uma pergunta "
                "não vira comando escondido."
            ),
            (
                f"Não fico só no papo. Posso {lista}.{outras} Meu limite é simples: conversa é "
                "conversa, ação precisa de pedido."
            ),
            (
                f"Por aqui eu dou conta de {lista}.{outras} E não, eu não uso curiosidade como "
                "desculpa para sair clicando nas coisas."
            ),
        ]
    return escolher_variacao(opcoes, evitar=evitar)

