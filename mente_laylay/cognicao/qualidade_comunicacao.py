"""Qualidade semântica da fala sem substituir a personalidade da Laylay.

O módulo não escreve respostas normais nem decide ações. Ele detecta somente
falhas fortes de comunicação que justificam uma única nova tentativa da LLM:
frase interrompida, promessa sem entrega, fuga de uma pergunta direta e
conselho específico que não foi solicitado.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, Mapping


_FINAL_INCOMPLETO = re.compile(
    r"(?:\b(?:mas|porque|porém|porem|então|entao|e|ou|que|se|quando|como|"
    r"apesar\s+de|só\s+que|so\s+que)\b|[:;,—-])\s*[.!?…]*$",
    re.IGNORECASE,
)
_RESPOSTA_VAZIA_DISFARCADA = re.compile(
    r"^(?:claro|sim|posso|vamos|beleza|tá|ta|certo|ah|a+h+|entendi)"
    r"[.!?…\s-]*$",
    re.IGNORECASE,
)
_PEDIDO_DE_ENTREGA = re.compile(
    r"\b(?:me\s+(?:manda|mande|mandar|dá|da|dar|mostra|mostre|mostrar|"
    r"explica|explique|explicar|descreve|descreva|descrever|fala|falar|diz|dizer)|"
    r"liste|lista|quais|como\s+funciona|passo\s+a\s+passo|"
    r"resolve|resolva|calcule|faz\s+uma\s+descri[cç][aã]o)\b",
    re.IGNORECASE,
)
_PERGUNTA_DE_POSICAO = re.compile(
    r"\b(?:voc[eê]|tu)\s+(?:gosta|curte|prefere|acha|pensa)\b|"
    r"\b(?:qual|quais)\s+(?:m[uú]sica|filme|jogo|livro).*(?:gosta|prefere)\b|"
    r"\btem\s+algum(?:a)?\s+(?:m[uú]sica|filme|jogo|livro)\b",
    re.IGNORECASE,
)
_MARCADORES_POSICAO = re.compile(
    r"\b(?:sim|n[aã]o|gosto|curto|prefiro|acho|iria|escolheria|conhe[cç]o|"
    r"me\s+parece|me\s+interessa|fico\s+curiosa)\b",
    re.IGNORECASE,
)
_EVASAO_OPINIAO = re.compile(
    r"\b(?:n[aã]o\s+(?:tenho|encontrei|achei)\s+(?:informa[cç][aã]o|dados)|"
    r"n[aã]o\s+posso\s+(?:opinar|dizer)|como\s+uma\s+ia)\b",
    re.IGNORECASE,
)
_RELATO_SEM_PEDIDO = re.compile(
    r"\b(?:eu\s+)?(?:estou|t[oô])\s+(?:pensando|planejando|querendo)\s+em\b|"
    r"\bacho\s+que\s+(?:eu\s+)?vou\b",
    re.IGNORECASE,
)
_CONSELHO_LIMPEZA_ESPECIFICO = re.compile(
    r"\b(?:use|usa|coloque|coloca|adicione|adiciona|misture|mistura|jogue|joga)\b"
    r"[^.!?]{0,100}\b(?:sal|cloro|[aá]gua\s+sanit[aá]ria|vinagre|amon[ií]aco|"
    r"detergente|sab[aã]o|produto|marca)\b",
    re.IGNORECASE,
)
_MARCADORES_MUSICA = re.compile(
    r"\b(?:m[uú]sica|faixa|som|banda|artista|cantor|cantora|[aá]lbum|rock|"
    r"metal|grunge|guitarra|vocal|refr[aã]o|discografia)\b",
    re.IGNORECASE,
)
_DERIVA_FILOSOFICA = re.compile(
    r"\b(?:estado\s+de\s+paz|ilumina[cç][aã]o|liberta[cç][aã]o|sofrimento|"
    r"budismo|espiritual|consci[eê]ncia|equil[ií]brio\s+interior)\b",
    re.IGNORECASE,
)


def _normalizar(texto: Any) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def _foco_do_plano(plano: Mapping[str, Any] | None) -> Dict[str, Any]:
    contrato = dict(plano or {})
    referencia = dict(contrato.get("referencia_resolvida") or {})
    if referencia.get("nome"):
        return {
            "nome": str(referencia.get("nome") or "").strip(),
            "tipo": str(referencia.get("tipo") or "").strip().casefold(),
            "dominio": str(contrato.get("dominio") or "conversa").strip().casefold(),
            "origem": str(referencia.get("origem") or "referencia_resolvida"),
        }
    entidades = dict(contrato.get("entidades") or {})
    musica_tipos = ("artista", "banda", "cantor", "cantora", "musica")
    for chave in musica_tipos:
        item = entidades.get(chave)
        if isinstance(item, Mapping) and item.get("nome"):
            return {
                "nome": str(item.get("nome") or "").strip(),
                "tipo": str(item.get("tipo") or chave).strip().casefold(),
                "dominio": "musica",
                "origem": str(item.get("origem") or "entidades_turno"),
            }
    return {}


def avaliar_qualidade_comunicacao(
    texto_usuario: str,
    fala: str,
    *,
    plano: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Retorna problemas fortes; não corrige estilo nem conteúdo por conta própria."""
    usuario = _normalizar(texto_usuario)
    resposta = _normalizar(fala)
    problemas: list[str] = []
    foco = _foco_do_plano(plano)

    if not resposta:
        problemas.append("fala_vazia")
    else:
        palavras = re.findall(r"[\wÀ-ÿ]+", resposta, flags=re.UNICODE)
        if _FINAL_INCOMPLETO.search(resposta) or _RESPOSTA_VAZIA_DISFARCADA.fullmatch(resposta):
            problemas.append("resposta_incompleta")
        if _PEDIDO_DE_ENTREGA.search(usuario) and len(palavras) < 7:
            problemas.append("entrega_prometida_ausente")
        if (
            _PERGUNTA_DE_POSICAO.search(usuario)
            and not _MARCADORES_POSICAO.search(resposta)
        ):
            problemas.append("pergunta_direta_nao_respondida")
        if _PERGUNTA_DE_POSICAO.search(usuario) and _EVASAO_OPINIAO.search(resposta):
            problemas.append("opiniao_evitada_sem_necessidade")
        if (
            _RELATO_SEM_PEDIDO.search(usuario)
            and "?" not in usuario
            and _CONSELHO_LIMPEZA_ESPECIFICO.search(resposta)
        ):
            problemas.append("conselho_especifico_nao_solicitado")

        tipo_foco = str(foco.get("tipo") or "")
        dominio_foco = str(foco.get("dominio") or "")
        foco_musical = dominio_foco == "musica" or tipo_foco in {
            "artista", "banda", "cantor", "cantora", "musica",
            "referencia_nomeada",
        }
        if (
            foco_musical
            and _PERGUNTA_DE_POSICAO.search(usuario)
            and _DERIVA_FILOSOFICA.search(resposta)
            and not _MARCADORES_MUSICA.search(resposta)
        ):
            problemas.append("deriva_de_dominio")

    problemas = list(dict.fromkeys(problemas))
    return {
        "aceita": not problemas,
        "requer_reparo": bool(problemas),
        "problemas": problemas,
        "foco": foco,
        "pontuacao": max(0.0, 1.0 - (0.25 * len(problemas))),
    }


def selecionar_contexto_imediato(
    mensagens: Iterable[Mapping[str, Any]] | None,
    *,
    limite: int = 4,
) -> list[dict[str, str]]:
    """Seleciona só a troca recente; memória longa não entra no reparo."""
    uteis: list[dict[str, str]] = []
    for item in list(mensagens or []):
        if not isinstance(item, Mapping):
            continue
        papel = str(item.get("role") or "").strip().casefold()
        conteudo = _normalizar(item.get("content"))
        if papel not in {"user", "assistant"} or not conteudo:
            continue
        uteis.append({"role": papel, "content": conteudo[:700]})
    return uteis[-max(1, int(limite or 4)):]


def montar_mensagens_reparo_comunicacao(
    texto_usuario: str,
    fala_rejeitada: str,
    avaliacao: Mapping[str, Any],
    *,
    mensagens: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Cria uma única tentativa de reparo, pequena e sem autorização prática."""
    payload = {
        "mensagem_atual": _normalizar(texto_usuario)[:900],
        "rascunho_rejeitado": _normalizar(fala_rejeitada)[:1200],
        "problemas": list(avaliacao.get("problemas") or []),
        "foco_confirmado": dict(avaliacao.get("foco") or {}),
        "troca_recente": selecionar_contexto_imediato(mensagens),
    }
    instrucao = (
        "Você está reparando uma resposta da Laylay, não iniciando outro assunto. "
        "Responda à mensagem atual de forma natural, completa e proporcional. Preserve "
        "o foco confirmado e use a troca recente apenas quando ela for relevante. Não "
        "invente lembranças, experiências físicas, títulos, artistas, produtos, marcas ou "
        "conselhos específicos. Não prometa responder depois e não termine só com uma "
        "introdução. Não execute nem sugira comandos. Mantenha a personalidade carismática, "
        "atenta e debochada com carinho quando combinar; uma tirada basta e nunca substitui "
        "a resposta. Retorne somente JSON válido no "
        'formato {"fala":"resposta completa","comandos":[]}.'
    )
    return [
        {"role": "system", "content": instrucao},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def contingencia_comunicacao(texto_usuario: str, *, foco: Mapping[str, Any] | None = None) -> str:
    """Último recurso contextual quando a única tentativa de reparo também falha."""
    texto = _normalizar(texto_usuario)
    nome = str(dict(foco or {}).get("nome") or "").strip()
    if re.search(r"\b(?:tudo\s+bem|como\s+(?:voc[eê]|vai\s+voc[eê]))\b", texto, re.I):
        return "Tô bem por aqui. E você, como tá?"
    if re.search(r"\b(?:eu\s+)?(?:estou|t[oô])\s+bem\b", texto, re.I):
        return "Que bom. Fico feliz de saber."
    if _PERGUNTA_DE_POSICAO.search(texto) and nome:
        return f"{nome} me interessa, mas não vou inventar um detalhe só para deixar a resposta bonita."
    if _PEDIDO_DE_ENTREGA.search(texto):
        return "Eu não consegui fechar essa resposta com a qualidade que você pediu. Prefiro não te entregar só metade."
    return "Peguei o que você disse. Minha resposta não fechou direito, mas eu mantive o assunto daqui."
