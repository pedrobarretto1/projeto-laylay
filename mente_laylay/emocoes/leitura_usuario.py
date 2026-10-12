"""Leitura curta da intenção emocional expressa pelo usuário.

O módulo descreve o sinal emocional; ele não muda a emoção da Laylay e não
executa ações. Assim, acolhimento e comandos continuam responsabilidades
separadas dentro da mesma mente compartilhada.
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Callable, Dict

from mente_laylay.cognicao.normalizacao_linguagem import texto_e_metalinguistico
from mente_laylay.personalidade.leitura_social_conversa import analisar_avaliacao_social_direta


_CONCLUSAO_PROPRIA = re.compile(
    r"\b(?:entreguei|terminei|conclu[ií]|finalizei|acabei|resolvi|encerrei|"
    r"consegui\s+(?:terminar|concluir|finalizar|resolver|entregar))\b",
    re.IGNORECASE,
)
_DURACAO_CARGA = re.compile(r"\b(?:dias?|semanas?|meses?)\b", re.IGNORECASE)
_CARGA_ANTERIOR = re.compile(
    r"\b(?:pres[oa]|prendia|prendendo|consumia|tens[aã]o|atolad[oa]|"
    r"peso\s+(?:enorme\s+)?(?:d[ae]s?\s+costas))\b",
    re.IGNORECASE,
)
_LIBERACAO = re.compile(
    r"\b(?:tirei\s+(?:(?:um|esse|aquele)\s+)?peso(?:\s+enorme)?\s+d[ae]s?\s+costas|"
    r"(?:agora\s+)?(?:posso|pude)\s+respirar|"
    r"(?:estou|me\s+sinto)\s+livre\s+disso|"
    r"saiu\s+(?:(?:um|esse|aquele)\s+)?peso)\b",
    re.IGNORECASE,
)
_TRECHO_CITADO = re.compile(r'"[^"\n]*"|“[^”\n]*”|«[^»\n]*»|\x27[^\x27\n]*\x27|‘[^’\n]*’')
_ALVO_CONCLUIDO = re.compile(
    r"^\s+(?P<alvo>(?:o|a|os|as|um|uma)\s+[^,.!?;:]{2,80}?)"
    r"(?=\s+(?:depois|ap[oó]s|que|e|mas)\b|[,.!?;:]|$)",
    re.IGNORECASE,
)


def _inferir_alivio_com_causa(texto: str) -> Dict[str, Any]:
    """Propõe alívio só quando conclusão, carga anterior e liberação coexistem."""
    bruto = str(texto or "").strip()
    # Texto atribuído a outra pessoa não é experiência emocional do usuário.
    # Na dúvida, uma citação inteira não publica evento.
    texto_autoral = _TRECHO_CITADO.sub(" ", bruto)
    base = texto_autoral.casefold()
    if re.search(
        r"^(?:escreva|repita|invente|traduza|explique|cite|o que significa)\b|"
        r"\b(?:se eu|caso eu|se tivesse|talvez|imagina|imagine|suponha)\b|"
        r"\b(?:treino|academia|halter|anilha|levantamento de peso)\b",
        base,
    ):
        return {}
    conclusao = _CONCLUSAO_PROPRIA.search(texto_autoral)
    duracao = _DURACAO_CARGA.search(texto_autoral)
    carga = _CARGA_ANTERIOR.search(texto_autoral)
    liberacao = _LIBERACAO.search(texto_autoral)
    if not all((conclusao, duracao, carga, liberacao)):
        return {}
    if re.search(r"\b(?:n[aã]o|nunca)\s+" + re.escape(conclusao.group(0)), base):
        return {}
    if re.search(r"\b(?:n[aã]o|nunca|nem)\s*$", base[max(0, liberacao.start()-16):liberacao.start()]):
        return {}
    alvo = _ALVO_CONCLUIDO.match(texto_autoral[conclusao.end():])
    return {
        "emocao": "alivio",
        "intensidade": 2,
        "alvo": "estado_geral",
        "pedido_implicito": "acolhimento",
        "necessidade_acao": False,
        "natureza_evidencia": "inferencia",
        "causa": f"{conclusao.group(0)} após {duracao.group(0)} de carga relatada",
        "verbo_conclusao": conclusao.group(0),
        "alvo_conclusao": alvo.group("alvo").strip() if alvo else "",
        "periodo_carga": duracao.group(0),
        "trecho_evidencia": liberacao.group(0),
        "confianca": 0.82,
        "texto": bruto,
        "ts": time.time(),
    }


def _complemento_de_conquista_indica_sucesso(verbo: str, complemento: str) -> bool:
    if not complemento:
        return True
    if verbo in {"passei", "passar"}:
        return bool(re.match(
            r"(?:n[ao]s?\s+(?:prova|teste|exame|concurso|vestibular|"
            r"entrevista|sele[cç][aã]o)|de\s+(?:ano|fase))\b", complemento,
        ))
    if verbo in {"ganhei", "ganhar"}:
        return bool(re.match(
            r"(?:(?:o|a|um|uma|meu|minha)\s+)?(?:jogo|partida|corrida|"
            r"disputa|aposta|campeonato|competi[cç][aã]o|medalha|pr[eê]mio|"
            r"concurso|trof[eé]u|bolsa|vaga)\b", complemento,
        ))
    if verbo == "consegui":
        proximo = re.match(
            r"(?:terminar|concluir|finalizar|resolver|entregar|completar|"
            r"aprender|passar|vencer|ganhar)\b", complemento,
        )
        return bool(proximo and _complemento_de_conquista_indica_sucesso(
            proximo.group(0), complemento[proximo.end():].strip(" ,.!;:"),
        ))
    return True


def _tem_conquista_autoral_afirmada(texto: str, padrao: str) -> bool:
    """Aceita um resultado positivo relatado, sem promover menções a fatos.

    A frase independente e o contraste delimitam a negação. Complementos
    ambíguos sem sentido de sucesso ficam para a interpretação contextual.
    """
    autoral = _TRECHO_CITADO.sub(" ", str(texto or "")).casefold()
    for frase in re.findall(r"[^.!?;]+[.!?;]?", autoral):
        if frase.rstrip().endswith("?"):
            continue
        for trecho in re.split(r"\b(?:mas|por[eé]m|contudo)\b", frase):
            if texto_e_metalinguistico(trecho):
                continue
            for conquista in re.finditer(padrao, trecho):
                antes = trecho[:conquista.start()]
                if re.search(
                    r"\b(?:n[aã]o(?!\s+(?:s[oó]|apenas)\b)|nunca|jamais|nem|"
                    r"se|caso|talvez|ser[aá]\s+que|imagina|imagine|suponha|"
                    r"disse|falou|contou|escreveu|comentou|relatou|segundo|"
                    r"dele|dela|deles|delas|traduza|repita|cite|explique)\b",
                    antes,
                ):
                    continue
                verbo = conquista.group(0)
                depois = trecho[conquista.end():].strip(" ,.!;:")
                if not _complemento_de_conquista_indica_sucesso(verbo, depois):
                    continue
                return True
    return False


def analisar_pedido_expressao(texto: str) -> Dict[str, Any]:
    """Entidades de expressão na leitura canônica; menção não é pedido de pose."""
    bruto = str(texto or "").strip()
    if not bruto or "?" in bruto or _TRECHO_CITADO.search(bruto):
        return {}
    base = "".join(c for c in unicodedata.normalize("NFKD", bruto.casefold())
                   if not unicodedata.combining(c))
    base = re.sub(r"\s+", " ", base).strip(" .!,")
    base = re.sub(r"^(?:laylay|lay)[, ]+", "", base)
    base = re.sub(r"[, ]+(?:por favor|laylay|lay)$", "", base).strip(" ,")
    nomes = {"feliz": "alegre", "alegre": "alegre", "triste": "triste",
             "brava": "brava", "irritada": "irritada", "surpresa": "surpresa",
             "surpreendida": "surpresa", "envergonhada": "envergonhada",
             "timida": "envergonhada", "debochada": "debochada", "calma": "calma"}
    if base in {"volte ao normal", "volta ao normal", "se acalme", "acalme-se"}:
        emocao, nivel = "calma", 1
    else:
        pedido = re.fullmatch(
            r"(?:fica|fique|(?:mostra|mostre|faca) (?:uma )?(?:carinha|cara|expressao)) "
            r"(?:(um pouco|muito|bem|bastante|super) )?(" + "|".join(nomes) + r")", base)
        if not pedido:
            return {}
        emocao = nomes[pedido[2]]
        nivel = 1 if emocao == "calma" or pedido[1] == "um pouco" else 3 if pedido[1] else 2
    return {"emocao": emocao, "nivel": nivel, "alvo": "laylay", "confianca": 1.0,
            "trecho_evidencia": bruto, "autoriza_execucao": False,
            "memorizar_como_fato": False, "natureza": "expressao_solicitada"}


def analisar_funcao_comunicativa(texto: str) -> Dict[str, Any]:
    """Identifica o papel humano da fala sem decidir comandos."""
    bruto = str(texto or "").strip()
    base = re.sub(r"\s+", " ", bruto.casefold()).strip()
    if not base:
        return {}
    pedido = analisar_pedido_expressao(bruto)
    if pedido:
        return {"funcao": "pedido_expressao", "objetivo": "encenar a expressão pedida sem inventar sentimentos ou efeitos externos",
                "postura_esperada": "brincalhona", "permite_pergunta": False,
                "confianca": 1.0, "expressao_solicitada": pedido, "texto": bruto, "ts": time.time()}
    regras = (
        ("correcao", r"^(?:eu\s+)?(?:estou\s+(?:perguntando|falando)|perguntei|falei)\s+(?:sobre|d[aoe])\b[^.!?]{1,180}\bn[aã]o\s+(?:sobre|d[aoe])\b", "reconhecer a correcao de escopo sem confundir contexto com autorizacao"),
        ("encerramento", r"\b(?:era so isso|era só isso|por hoje e so|por hoje é só|ate mais|até mais|falou|depois a gente ve|depois a gente vê)\b", "encerrar o assunto sem retomar contexto antigo"),
        ("correcao", r"^(?:na verdade|nao lay|não lay|eu quis dizer|quis dizer|meu nome n[aã]o|voce (?:ainda )?nao (?:tem|consegue)|você (?:ainda )?não (?:tem|consegue)|ja falei|já falei)\b", "aceitar a correcao e atualizar o entendimento"),
        ("pedido_desculpas", r"^(?:(?:me\s+)?(?:desculpa|desculpe|perdoa|perdoe)|perd[aã]o|foi mal)\b[^.!?]{0,140}\b(?:repeti|pedi de novo|insisti|exagerei)\b", "reconhecer o pedido de desculpas pelo excesso confirmado sem apagar a causa"),
        ("conquista", r"\b(?:consegui|passei|ganhei|venci|tirei nota maxima|tirei nota máxima|deu certo|terminei|fui aprovado|fui aprovada)\b", "reconhecer a conquista antes de perguntar ou aconselhar"),
        ("agradecimento", r"\b(?:obrigad[oa]?|brigad[oa]?|valeu|vlw)\b", "reconhecer a ajuda concreta que motivou o agradecimento"),
        ("reacao_positiva", r"^(?:que bom|ainda bem|fico feliz)(?: lay| laylay)?[.!]*$", "receber a reação positiva sem inventar novo estado nem forçar pergunta"),
        ("elogio", r"\b(?:voce e incrivel|você é incrível|voce e maravilhosa|você é maravilhosa|gosto de voce|gosto de você|te adoro|te amo)\b", "receber o elogio como dirigido a Laylay"),
        ("desabafo", r"^(?:eu\s+)?(?:estou|to|tô)\s+(?:(?:um\s+pouco|meio|muito|bem|bastante)\s+)?triste\b|\b(?:nao aguento|não aguento|to triste|tô triste|to cansad|tô cansad|estou cansad|me sinto|dia horrivel|dia horrível)\b", "acolher antes de oferecer solucao"),
        ("frustracao", r"\b(?:nao foi|não foi|nao funcionou|não funcionou|de novo isso|voce errou|você errou|ja falei|já falei)\b", "reconhecer a frustracao e corrigir sem se defender"),
        ("decepcao", r"\b(?:fiquei decepcionad|esperava mais|que pena|achei que ia|poxa vida)\b", "reconhecer a decepcao antes de explicar"),
        ("inseguranca", r"\b(?:sera que eu consigo|será que eu consigo|nao sei se consigo|não sei se consigo|to com medo|tô com medo)\b", "acolher a inseguranca sem prometer resultado"),
        ("brincadeira", r"\b(?:kkk+|haha+|rsrs+|to brincando|tô brincando|zoeira)\b", "acompanhar a brincadeira sem tratar como fato"),
        ("relato", r"^(?:sabia que|hoje eu|ontem eu|sexta eu|eu fui|eu tive|aconteceu)\b", "reagir ao conteudo contado sem transformar em comando"),
    )
    perfis = {
        "encerramento": ("serenidade", "breve", False),
        "correcao": ("frustracao_possivel", "receptiva", False),
        "pedido_desculpas": ("reconciliacao", "receptiva", False),
        "alivio": ("alivio", "acolhedora", False),
        "conquista": ("alegria_ou_orgulho", "celebratoria", True),
        "agradecimento": ("gratidao", "calorosa", False),
        "reacao_positiva": ("alegria_leve", "breve", False),
        "elogio": ("afeto", "envergonhada", False),
        "critica_pessoal": ("avaliacao_negativa", "sensivel_sem_culpar", False),
        "rejeicao_pessoal": ("distanciamento", "respeitosa_sem_cobrar", False),
        "desabafo": ("sofrimento", "acolhedora", True),
        "frustracao": ("frustracao", "reparadora", False),
        "decepcao": ("decepcao", "cuidadosa", False),
        "inseguranca": ("inseguranca", "encorajadora", True),
        "brincadeira": ("diversao", "brincalhona", True),
        "relato": ("neutra", "interessada", True),
    }
    for funcao, padrao, objetivo in regras:
        if funcao == "elogio":
            avaliacao = analisar_avaliacao_social_direta(bruto)
            if not avaliacao:
                continue
            tipo = avaliacao["tipo"]
            funcao_social = "elogio" if tipo == "elogio_pessoal" else tipo
            emocao, postura, permite_pergunta = perfis[funcao_social]
            return {"funcao": funcao_social,
                    "objetivo": ("receber o elogio dirigido à Laylay" if tipo == "elogio_pessoal"
                                 else "reconhecer a avaliação pessoal sem culpar, cobrar afeto ou depreciar o usuário"),
                    "emocao_implicita": emocao, "postura_esperada": postura,
                    "permite_pergunta": permite_pergunta, "confianca": avaliacao["confianca"],
                    "avaliacao_social": avaliacao, "texto": bruto, "ts": time.time()}
        # Correções e encerramentos mantêm prioridade. Antes de classificar
        # conquista, a leitura causal já existente distingue alívio autoral
        # de mera conclusão, hipótese ou citação.
        if funcao == "conquista" and _inferir_alivio_com_causa(bruto):
            emocao, postura, permite_pergunta = perfis["alivio"]
            return {
                "funcao": "alivio",
                "objetivo": "reconhecer o alívio pela carga concluída sem forçar pergunta ou conselho",
                "emocao_implicita": emocao,
                "postura_esperada": postura,
                "permite_pergunta": permite_pergunta,
                "confianca": 0.82,
                "texto": bruto,
                "ts": time.time(),
            }
        if funcao == "conquista" and not _tem_conquista_autoral_afirmada(bruto, padrao):
            continue
        if re.search(padrao, base):
            emocao, postura, permite_pergunta = perfis.get(funcao, ("neutra", "natural", True))
            return {
                "funcao": funcao, "objetivo": objetivo, "emocao_implicita": emocao,
                "postura_esperada": postura, "permite_pergunta": permite_pergunta,
                "confianca": 0.94, "texto": bruto, "ts": time.time(),
            }
    return {
        "funcao": "informacao", "objetivo": "responder ao conteudo atual",
        "emocao_implicita": "neutra", "postura_esperada": "natural",
        "permite_pergunta": True, "confianca": 0.60, "texto": bruto, "ts": time.time(),
    }


def analisar_intencao_emocional(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any]:
    bruto = str(texto or "").strip()
    base = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.casefold()
    base = re.sub(r"\s+", " ", str(base or "")).strip()
    if not base:
        return {}

    marcadores_pessoais = (
        r"\b(?:eu\s+)?(?:estou|to|tô|ando|me sinto|fiquei|ando me sentindo)\b",
        r"\b(?:nao|não)\s+aguento\b",
        r"\b(?:dia|tarde|noite|madrugada)\s+(?:chata|chato|arrastada|arrastado)\b",
        r"\b(?:nao tem|não tem|tem nada|nao tenho|não tenho)\s+(?:nada\s+)?(?:pra|para)\s+fazer\b",
    )
    if not any(re.search(padrao, base) for padrao in marcadores_pessoais):
        return _inferir_alivio_com_causa(bruto)

    emocoes = (
        ("cansaco", r"\b(?:cansad[oa]|exaust[oa]|esgotad[oa]|sem energia)\b"),
        ("tristeza", r"\b(?:triste|desanimad[oa]|abatid[oa]|pra baixo|mal)\b"),
        ("ansiedade", r"\b(?:ansios[oa]|preocupad[oa]|apreensiv[oa]|nervos[oa])\b"),
        ("irritacao", r"\b(?:irritad[oa]|estressad[oa]|brav[oa]|com raiva|de saco cheio)\b"),
        ("alegria", r"\b(?:feliz|animad[oa]|empolgad[oa]|contente)\b"),
        ("medo", r"\b(?:com medo|assustad[oa]|insegur[oa])\b"),
        ("culpa", r"\b(?:culpad[oa]|com culpa|peso na consci[eê]ncia)\b"),
        ("tedio", r"\b(?:chata|chato|tedio|tédio|entediad[oa]|arrastad[oa])\b"),
        ("tedio", r"\b(?:nao tem|não tem|tem nada|nao tenho|não tenho)\s+(?:nada\s+)?(?:pra|para)\s+fazer\b"),
    )
    # O verbo pessoal e o sinal precisam compor o mesmo predicado. Um
    # "estou" posterior não prova que "triste" em outra oração é estado
    # atual do usuário. Formulações fora desta contingência conservadora
    # seguem para a leitura da principal, sem receber certeza lexical.
    prefixo_pessoal = (
        marcadores_pessoais[0]
        + r"\s+(?:(?:um pouco|meio que|muito|meio|levemente|realmente|"
        r"bastante|t[aã]o|bem|super|totalmente|emocionalmente)\s+)*"
    )
    predicado = None
    emocao = ""
    for nome, padrao in emocoes:
        predicado = re.search(prefixo_pessoal + padrao, base)
        if predicado:
            emocao = nome
            break
    if not emocao:
        predicado = re.search(marcadores_pessoais[2], base) or re.search(marcadores_pessoais[3], base)
        if predicado:
            emocao = "tedio"
    if not emocao:
        predicado = re.search(marcadores_pessoais[1], base)
        if predicado:
            emocao = "esgotamento"
    if not emocao:
        return _inferir_alivio_com_causa(bruto)

    sinal_pessoal = predicado.group(0)
    intensidade = 2
    if re.search(r"\b(?:um pouco|meio|meio que|levemente)\b", sinal_pessoal):
        intensidade = 1
    if (
        re.search(r"\b(?:muito|nao aguento|não aguento)\b", sinal_pessoal)
        or re.match(r"\s+(?:demais|pra caramba|para caramba|no limite)\b", base[predicado.end():])
    ):
        intensidade = 3

    alvo = "estado_geral"
    if re.search(r"\b(?:de|com)\s+(?:voce|você|tu|lay|laylay)\b", base):
        alvo = "laylay"
    elif re.search(r"\b(?:disso|disto|dessa|deste|dessa situacao|dessa situação)\b", base):
        alvo = "isso"
    else:
        trecho_alvo = re.search(
            r"\b(?:cansad[oa]|exaust[oa]|esgotad[oa]|irritad[oa]|estressad[oa]|brav[oa]|triste|preocupad[oa]|culpad[oa])\s+(?:de|com|por causa de)\s+(.+)$",
            base,
        )
        if trecho_alvo:
            alvo = re.split(r"[,.!?]", trecho_alvo.group(1), maxsplit=1)[0].strip()[:120] or alvo

    pedido_implicito = "acolhimento"
    necessidade_acao = False
    if re.search(r"\b(?:quero|preciso)\s+(?:desabafar|conversar|falar)\b", base):
        pedido_implicito = "escuta"
    elif re.search(r"\b(?:me ajuda|me ajude|preciso de ajuda|o que eu faco|o que faço|faz alguma coisa|pode fazer algo)\b", base):
        pedido_implicito = "ajuda"
        necessidade_acao = True

    return {
        "emocao": emocao,
        "intensidade": intensidade,
        "alvo": alvo,
        "pedido_implicito": pedido_implicito,
        "necessidade_acao": necessidade_acao,
        "texto": bruto,
        "ts": time.time(),
    }


def registrar_leitura_emocional(
    estado: Dict[str, Any] | None,
    leitura: Dict[str, Any] | None,
) -> Dict[str, Any]:
    novo = dict(estado or {})
    dados = dict(leitura or {})
    if not dados.get("emocao"):
        return novo
    novo.update(
        {
            "emocao_usuario": str(dados.get("emocao") or ""),
            "emocao_usuario_intensidade": int(dados.get("intensidade") or 1),
            "emocao_usuario_alvo": str(dados.get("alvo") or "estado_geral"),
            "emocao_usuario_pedido_implicito": str(dados.get("pedido_implicito") or "acolhimento"),
            "emocao_usuario_necessidade_acao": bool(dados.get("necessidade_acao")),
            "emocao_usuario_texto": str(dados.get("texto") or ""),
            "emocao_usuario_ts": float(dados.get("ts") or time.time()),
        }
    )
    return novo
