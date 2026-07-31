"""Leitura contextual de pedidos para a Laylay olhar o jogo atual.

O detector e deliberadamente condicionado ao modo jogo. Assim, perguntas
cotidianas como "o que e isso?" continuam sendo conversa fora de um jogo e
nao ganham permissao para capturar a tela por acidente.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Mapping


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


_PEDIDO_DE_OLHAR = re.compile(
    r"\b(?:olha|olhe|olhar|veja|ve|ver|analisa|analise|analisar|"
    r"observa|observe|observar|confere|conferir|checa|checar|da uma olhada|"
    r"me diz o que (?:voce )?ve)\b"
)
_PEDIDO_VISUAL_DIRETO = re.compile(
    r"\b(?:pode|consegue|da para|da pra)\s+"
    r"(?:ver|olhar|analisar|checar|conferir)\b.{0,90}"
    r"\b(?:isso|isto|esse|essa|este|esta|aqui|na tela|no jogo)\b"
)
_INSPECAO_INVENTARIO = re.compile(
    r"\b(?:olha|olhe|veja|ve|analisa|analise|confere|mapeia|escaneia)\b"
    r".{0,45}\b(?:meu|minha|o)\s+(?:inventario|equipamentos?|itens? equipados?)\b|"
    r"\b(?:analisa|mapeia|escaneia)\s+(?:meu|minha|o)\s+inventario\b"
)
_INSPECAO_PERSONAGEM = re.compile(
    r"\b(?:olha|olhe|veja|ve|analisa|analise|confere|mostra|le|leia)\b"
    r".{0,45}\b(?:meus|minhas|o|a)\s+"
    r"(?:atributos?|status|estatisticas?|ficha|build)\b"
)
_ANALISE_ARVORE_BUILD = re.compile(
    r"\b(?:olha|olhe|veja|analisa|analise|confere|da uma olhada)\b.{0,55}"
    r"\b(?:minha|a)\s+(?:arvore(?: de habilidades| de passivas)?|build)\b"
)
_HABILIDADE_VISUAL = re.compile(
    r"\b(?:habilidade|passiva|no da arvore|no passivo|talento|gema|skill|perk)\b"
)
_CONTINUACAO_VEREDITO_VISUAL = re.compile(
    r"^(?:mas\s+)?(?:ela|ele|isso|isto|esse no|essa habilidade)?\s*"
    r"(?:(?:e|eh)\s+(?:uma\s+)?boa\s+(?:pega(?:r)?|escolha)(?:\s+(?:ela|ele|isso))?|"
    r"vale\s+a\s+pena\s+(?:pegar|usar|ativar|escolher)(?:\s+(?:ela|ele|isso))?|"
    r"(?:e|eh)\s+bom\s+(?:pegar|usar|ativar)|"
    r"(?:devo|eu devo)\s+(?:pegar|usar|ativar)(?:\s+(?:ela|ele|isso))?)$"
)
_ITEM_EM_PEDIDO_VISUAL = re.compile(
    r"\b(?:item|arma|armadura|anel|amuleto|escudo|capacete|botas?|"
    r"sapatos?|cajado|martelo|luvas?|acessorio|equipamento|espada|arco)\b"
)
_ITEM_APONTADO_SEM_JULGAMENTO = re.compile(
    r"\b(?:e\s+)?(?:esse|essa|este|esta)\s+"
    r"(?:item|arma|armadura|anel|amuleto|escudo|capacete|botas?|sapatos?|"
    r"cajado|martelo|luvas?|acessorio|equipamento|espada|arco)"
    r"(?:\s+(?:aqui|ai|ali|na tela|sob o mouse))?\b"
)
_REPETIR_ANALISE_VISUAL = re.compile(
    r"^(?:(?:lay|laylay)\s*[,;:\-]?\s*)?"
    r"(?:(?:pode|tenta|tente|consegue)\s+)?"
    r"(?:olha|olhe|olhar|ve|veja|ver|analisa|analise|analisar|"
    r"observa|observe|observar|confere|confira|conferir|checa|cheque|checar)"
    r"(?:\s+(?:isso|isto|a tela|o item|esse item|essa coisa|ele|ela))?\s+"
    r"(?:de novo|novamente|outra vez|mais uma vez)"
    r"(?:\s+(?:isso|isto|a tela|o item|esse item|essa coisa|ele|ela))?$"
)
_REPETICAO_VISUAL_CURTA = re.compile(
    r"^(?:(?:lay|laylay)\s*[,;:\-]?\s*)?"
    r"(?:tenta(?:r)?\s+de novo|tenta(?:r)?\s+novamente|de novo|novamente|"
    r"outra vez|mais uma vez)$"
)
_NOVO_OBJETO_VISUAL_CURTO = re.compile(
    r"^(?:(?:lay|laylay)\s*[,;:\-]?\s*)?"
    r"(?:e\s+)?(?:esse|essa|este|esta|isso|isto)"
    r"(?:\s+(?:aqui|ai|ali|agora))?$"
)
_APRESENTACAO_COMPLEMENTO_VISUAL = re.compile(
    r"^(?:(?:lay|laylay)\s*[,;:\-]?\s*)?"
    r"(?:(?:aqui|agora)\s+(?:esta|estao|ta|tao)\s+|"
    r"(?:esse|essa|esses|essas)\s+(?:e|sao)\s+)"
    r"(?:o?s?\s+|a?s?\s+)?(?:meu|minha|meus|minhas)\s+"
    r"(?:atributos?|status|estatisticas?|build|equipamentos?|item\s+atual|"
    r"arma\s+atual|armadura\s+atual|bota\s+atual)$|"
    r"^(?:agora\s+)?(?:da|da)\s+(?:pra|para)\s+ver(?:\s+(?:direito|melhor))?$"
)
_ANCORA_VISUAL = re.compile(
    r"\b(?:isso|isto|esse|essa|esses|essas|aqui|ai|na tela|no jogo|"
    r"estou vendo|to vendo|estou segurando|to segurando|minha (?:casa|base|"
    r"construcao|armadura|arma|tela)|este lugar|essa area)\b"
)
_IDENTIFICACAO_VISUAL = re.compile(
    r"^(?:o que|que|qual|quem)\b.{0,90}\b(?:e|eh|seria|parece)\b.{0,50}"
    r"\b(?:isso|isto|esse|essa|aqui)\b|"
    r"^(?:o que|que|qual)\s+(?:item|bloco|minerio|inimigo|personagem|lugar|"
    r"objeto|arma|icone|bicho|coisa)\b.{0,70}\b(?:esse|essa|isto|isso|aqui)\b"
)
_IDENTIFICACAO_OBJETO_APONTADO = re.compile(
    r"^(?:qual|que|como)\b.{0,65}\b(?:desse|dessa|deste|desta)\s+"
    r"([a-z0-9][a-z0-9_-]*)\b"
)
_AJUDA_ESPACIAL = re.compile(
    r"\b(?:por onde (?:eu )?(?:saio|vou|passo)|onde (?:eu )?estou|"
    r"tem (?:algum )?perigo aqui|o que (?:eu )?faco agora|"
    r"como (?:eu )?(?:saio|passo|chego) (?:daqui|ai|ali)|"
    r"o que (?:posso|da para) melhorar aqui|como ficou)\b"
)
_AVALIACAO_ITEM = re.compile(
    r"\b(?:esse|essa|este|esta)\s+"
    r"(?:item|arma|armadura|anel|amuleto|escudo|capacete|bota|luva|acessorio|equipamento)"
    r"(?:\s+(?:aqui|ai|ali|na tela|sob o mouse))?"
    r"\s*(?:(?:e|eh|parece|seria)?\s*(?:bom|boa|forte|melhor|pior|util|ruim|fraco|fraca)|"
    r"(?:vale a pena|compensa)|serve\s+(?:pra|para)\s+(?:mim|minha build))\b|"
    r"\b(?:isso|isto)\s+(?:e|eh|parece|seria)\s+"
    r"(?:bom|boa|forte|melhor|pior|util|ruim|fraco|fraca)(?:\s+(?:pra|para)\s+mim)?\b|"
    r"\b(?:vale a pena|compensa)\s+(?:usar|equipar|pegar|comprar)\s+"
    r"(?:isso|isto|(?:esse|essa|este|esta)\s+(?:item|arma|armadura|equipamento))\b|"
    r"\b(?:troco|trocar|equipo|equipar|uso|usar)\s+"
    r"(?:isso|isto|(?:esse|essa|este|esta)\s+(?:item|arma|armadura|equipamento))\b|"
    r"\b(?:esse|essa|este|esta)\s+(?:item|arma|armadura|equipamento)\s+"
    r"(?:e|eh)\s+(?:melhor|pior)\s+que\s+(?:o|a)\s+(?:meu|minha|equipad[oa])\b"
)

_DEMONSTRATIVO_VISUAL = re.compile(
    r"\b(?:esse|essa|este|esta|esses|essas)\s+([a-z0-9][a-z0-9_-]*)\b"
)
_DEMONSTRATIVO_SEM_NOME = re.compile(
    r"\b(?:isso|isto)\b|\b(?:esse|essa|este|esta)\s*(?:[?!,.;:]|$)"
)
_JULGAMENTO_VISUAL = re.compile(
    r"\b(?:e|eh|parece|seria)\s+(?:muito\s+)?"
    r"(?:bom|boa|forte|util|ruim|fraco|fraca|melhor|pior)\b|"
    r"\b(?:vale\s+a\s+pena|compensa|presta)\b|"
    r"\bserve\s+(?:pra|para)\s+(?:mim|minha\s+build|meu\s+personagem)\b"
)

# Conceitos que podem ser avaliados durante uma conversa sobre o jogo, mas nao
# representam necessariamente algo sob o cursor. A lista e deliberadamente
# curta: nomes concretos desconhecidos (martelo, cajado, reliquia etc.) devem
# continuar funcionando sem exigir um dicionario de itens por jogo.
_ALVOS_CONVERSACIONAIS = frozenset(
    {
        "assunto",
        "build",
        "classe",
        "conversa",
        "dia",
        "estilo",
        "historia",
        "ideia",
        "jogo",
        "modo",
        "musica",
        "personagem",
    }
)

_NOMES_ITEM_VISUAL = (
    "item", "arma", "armadura", "anel", "amuleto", "escudo", "capacete",
    "bota", "botas", "sapato", "sapatos", "cajado", "martelo", "luva",
    "luvas", "acessorio", "equipamento", "espada", "arco",
)


def _corrigir_item_visual_provavel(original: str, normalizado: str) -> tuple[str, str]:
    """Recupera um substantivo curto deformado somente num pedido visual.

    A correção fica confinada à construção ``ver esse/essa X`` e exige alta
    semelhança com um equipamento conhecido. Assim nomes próprios e termos
    normais da conversa não são reescritos globalmente.
    """
    if not re.search(
        r"\b(?:olha|olhar|ve|ver|veja|analisa|analisar|observa|observar|"
        r"confere|conferir|checa|checar)\b",
        normalizado,
    ):
        return normalizado, original
    alvo = re.search(r"\b(?:esse|essa|este|esta)\s+([a-z0-9_-]{3,18})\b", normalizado)
    if not alvo:
        return normalizado, original
    ouvido = alvo.group(1)
    if ouvido in _NOMES_ITEM_VISUAL or ouvido in _ALVOS_CONVERSACIONAIS:
        return normalizado, original
    candidatos = sorted(
        (
            (SequenceMatcher(None, ouvido, nome).ratio(), nome)
            for nome in _NOMES_ITEM_VISUAL
            if abs(len(ouvido) - len(nome)) <= 2
        ),
        reverse=True,
    )
    if not candidatos or candidatos[0][0] < 0.74:
        return normalizado, original
    correto = candidatos[0][1]
    normalizado = re.sub(rf"\b{re.escape(ouvido)}\b", correto, normalizado, count=1)
    pergunta = re.sub(rf"\b{re.escape(ouvido)}\b", correto, original, count=1, flags=re.IGNORECASE)
    return normalizado, pergunta


def _e_avaliacao_visual_demonstrativa(texto: str) -> bool:
    """Reconhece um objeto apontado sem depender do nome conhecido do item."""
    if not _JULGAMENTO_VISUAL.search(texto):
        return False
    if _DEMONSTRATIVO_SEM_NOME.search(texto):
        return True
    alvo = _DEMONSTRATIVO_VISUAL.search(texto)
    if not alvo:
        return False
    return alvo.group(1) not in _ALVOS_CONVERSACIONAIS


def _e_identificacao_de_objeto_apontado(texto: str) -> bool:
    alvo = _IDENTIFICACAO_OBJETO_APONTADO.search(texto)
    return bool(alvo and alvo.group(1) not in _ALVOS_CONVERSACIONAIS)


def detectar_pedido_visao_jogo(
    texto: str,
    contexto_jogo: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Retorna uma intenção visual somente com jogo ativo e referência visível."""
    contexto = dict(contexto_jogo or {})
    if not bool(contexto.get("ativo")):
        return None
    original = str(texto or "").strip()
    normalizado = _normalizar(original)
    if not normalizado:
        return None
    normalizado, pergunta_visual = _corrigir_item_visual_provavel(original, normalizado)

    # "Que erro é esse?" normalmente retoma um erro que a própria Laylay
    # acabou de mencionar. Só vira visão quando Pedro ancora explicitamente a
    # pergunta na tela/jogo ou pede para olhar.
    pergunta_erro_contextual = bool(re.fullmatch(
        r"(?:que|qual) erro (?:e |eh )?(?:esse|isso)|"
        r"(?:que|qual) foi o erro|o que (?:aconteceu|deu errado)",
        normalizado.strip(" ?!.,"),
    ))
    ancora_erro_visual = bool(re.search(
        r"\b(?:na tela|no jogo|aqui na tela|olha|olhe|veja|analisa|observe)\b",
        normalizado,
    ))
    if pergunta_erro_contextual and not ancora_erro_visual:
        return None

    tipo = ""
    if (
        bool(contexto.get("analise_visual_recente"))
        and _CONTINUACAO_VEREDITO_VISUAL.fullmatch(normalizado.strip(" ?!.,"))
    ):
        tipo = "continuacao_visual"
    elif (
        bool(contexto.get("analise_visual_recente"))
        and _NOVO_OBJETO_VISUAL_CURTO.fullmatch(normalizado.strip(" ?!.,"))
    ):
        tipo = "identificacao"
    elif _APRESENTACAO_COMPLEMENTO_VISUAL.fullmatch(
        re.sub(r"\s+lay(?:lay)?$", "", normalizado.strip(" ?!.,"))
    ):
        # Pedro colocou na tela justamente a informação que faltava. É uma
        # nova evidência visual, não uma frase para a LLM de conversa. Mesmo
        # sem análise anterior, vale como pedido explícito para ler a ficha.
        tipo = "complemento_visual"
    elif _INSPECAO_INVENTARIO.search(normalizado):
        tipo = "inspecao_inventario"
    elif _INSPECAO_PERSONAGEM.search(normalizado):
        tipo = "inspecao_personagem"
    elif _ANALISE_ARVORE_BUILD.search(normalizado):
        tipo = "analise_build"
    elif _HABILIDADE_VISUAL.search(normalizado) and (
        _JULGAMENTO_VISUAL.search(normalizado) or _PEDIDO_DE_OLHAR.search(normalizado)
    ):
        tipo = "avaliacao_habilidade"
    elif (
        bool(contexto.get("analise_visual_recente"))
        and _REPETICAO_VISUAL_CURTA.fullmatch(normalizado.strip(" ?!.,"))
    ) or _REPETIR_ANALISE_VISUAL.fullmatch(normalizado.strip(" ?!.,")):
        # O runtime recupera pergunta e tipo anteriores desta mesma sessão,
        # mas captura um quadro novo em vez de reaproveitar a imagem antiga.
        tipo = "reanalise"
    elif _PEDIDO_VISUAL_DIRETO.search(normalizado) and _ITEM_EM_PEDIDO_VISUAL.search(normalizado):
        tipo = "avaliacao_item"
    elif _PEDIDO_VISUAL_DIRETO.search(normalizado):
        tipo = "observacao"
    elif _ITEM_APONTADO_SEM_JULGAMENTO.search(normalizado):
        tipo = "avaliacao_item"
    elif _AVALIACAO_ITEM.search(normalizado):
        tipo = "avaliacao_item"
    elif _e_avaliacao_visual_demonstrativa(normalizado):
        # Mantém a compatibilidade dos pedidos curtos de item. Habilidades e
        # passivas explícitas já foram separadas acima; continuações sem nome
        # são resolvidas pela entidade visual recente.
        tipo = "avaliacao_item"
    elif _PEDIDO_DE_OLHAR.search(normalizado) and _ITEM_EM_PEDIDO_VISUAL.search(normalizado):
        tipo = "avaliacao_item"
    elif _PEDIDO_DE_OLHAR.search(normalizado):
        tipo = "observacao"
    elif _IDENTIFICACAO_VISUAL.search(normalizado):
        tipo = "identificacao"
    elif _e_identificacao_de_objeto_apontado(normalizado):
        tipo = "identificacao"
    elif _AJUDA_ESPACIAL.search(normalizado):
        tipo = "orientacao"
    elif re.search(r"\b(?:o que|que|qual|como)\b", normalizado) and _ANCORA_VISUAL.search(normalizado):
        tipo = "pergunta_visual"
    if not tipo:
        return None

    return {
        "intent": "GAME_VISION",
        "params": {
            "pergunta": pergunta_visual,
            "tipo": tipo,
            "jogo": str(contexto.get("titulo") or contexto.get("processo") or "").strip(),
            "requer_cursor": tipo in {
                "avaliacao_item", "avaliacao_habilidade", "avaliacao_entidade",
            },
        },
    }


def aplicar_pedido_visual_ao_turno(turno: Mapping[str, Any], pedido: Mapping[str, Any]) -> dict[str, Any]:
    """Autoriza apenas a consulta visual explicitamente reconhecida."""
    novo = dict(turno or {})
    params = dict(pedido.get("params") or {})
    pergunta = str(params.get("pergunta") or "").strip()
    segmento = {
        "indice": 0,
        "texto": pergunta[:300],
        "modalidade": "comando",
        "confianca": 0.97,
        "motivo": "pedido visual explícito durante modo jogo",
        "autoriza_execucao": True,
        "acao_explicita": True,
        "requer_esclarecimento": False,
        "natureza_acao": "consulta_visual",
    }
    novo.update(
        modalidade="comando",
        modalidade_geral="comando",
        ato_principal="comando",
        atos=["comando"],
        segmentos=[segmento],
        texto_operacional=pergunta[:500],
        texto_conversacional="",
        autoriza_execucao=True,
        acao_explicita=True,
        requer_esclarecimento=False,
        depende_contexto=True,
        natureza_acao="consulta_visual",
        motivo="pedido visual explícito durante modo jogo",
        motivo_decisao="pedido visual explícito durante modo jogo",
        pedido_visao_jogo=params,
        confianca=max(float(novo.get("confianca") or 0.0), 0.97),
    )
    return novo
