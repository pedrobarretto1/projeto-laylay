"""Respostas locais curtas quando a LLM não conclui o turno."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping

from mente_laylay.emocoes.contrato_causal import evento_tem_causa_rastreavel
from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional
from mente_laylay.personalidade.variacao_fala import escolher_variacao


def _ultima_observacao_visual(contexto: Any) -> str:
    if not isinstance(contexto, Mapping):
        return ""
    jogo = contexto.get("contexto_jogo_atual")
    fontes = [contexto, jogo] if isinstance(jogo, Mapping) else [contexto]
    for fonte in fontes:
        for chave in ("ultima_observacao", "observacao_visual", "ultima_resposta_visual"):
            valor = re.sub(r"\s+", " ", str(fonte.get(chave) or "")).strip()
            if valor:
                return valor[:700]
    return ""


def _resposta_sobre_visual_recente(texto: str, observacao: str) -> str:
    """Responde a uma avaliação dêitica usando somente evidência já percebida."""
    if not observacao:
        return ""
    avaliacao = bool(re.search(
        r"\b(?:t[aá]|est[aá]|ficou|parece)\b.{0,35}"
        r"\b(?:legal|bonit[ao]|boa|bom|aconchegante|bacana|massa|da hora)\b",
        texto,
        flags=re.IGNORECASE,
    ))
    referencia = bool(re.search(
        r"\b(?:meu|minha|esse|essa|isto|isso|aqui|casinha|casa|constru[cç][aã]o|decora[cç][aã]o)\b",
        texto,
        flags=re.IGNORECASE,
    ))
    if not (avaliacao and referencia):
        return ""

    detalhe = re.search(
        r"\bcom\s+(.+?)(?:[.!?]|$)", observacao, flags=re.IGNORECASE,
    )
    if detalhe:
        evidencia = detalhe.group(1).strip(" ,.;:!?")
        if evidencia:
            return (
                "Tá sim. O que mais me chamou atenção foi "
                f"{evidencia} — ficou bem aconchegante."
            )

    observacao_limpa = re.sub(
        r"^(?:ol[aá](?:\s+s[oó])?|(?:ei|opa),?\s*[^,!]{0,30},?)\s*",
        "",
        observacao,
        flags=re.IGNORECASE,
    ).strip()
    if observacao_limpa:
        observacao_limpa = observacao_limpa[0].lower() + observacao_limpa[1:]
        return f"Tá sim. Pelo que acabei de ver, {observacao_limpa}"
    return ""


def _resposta_social_curta(texto: str) -> str:
    """Conclui atos sociais inequívocos sem depender do modelo generativo."""
    limpo = texto.strip(" .,!?")
    if re.fullmatch(
        r"(?:eu\s+)?(?:"
        r"n[aã]o\s+(?:to|t[oô]|estou)\s+(?:muito\s+)?bem"
        r"|(?:to|t[oô]|estou)\s+(?:muito\s+)?mal"
        r")(?:\s+(?:lay|laylay))?",
        limpo,
        flags=re.IGNORECASE,
    ):
        return escolher_variacao([
            "Poxa. Quer me contar o que aconteceu? Eu fico aqui com você.",
            "Eu ouvi que você não está bem. Não vou cobrir isso com frase bonita.",
            "Isso parece pesado agora. Pode falar no seu ritmo, sem cerimônia.",
        ])
    if re.fullmatch(
        r"(?:eu\s+)?(?:to|t[oô]|estou)\s+(?:muito\s+)?bem"
        r"(?:\s+sim)?(?:\s+(?:lay|laylay))?",
        limpo,
        flags=re.IGNORECASE,
    ):
        return escolher_variacao([
            "Bom saber. Pelo menos uma coisa decidiu colaborar hoje.",
            "Que bom. Seguimos sem precisar inventar drama por enquanto.",
            "Ótimo. Gosto quando o dia entrega uma notícia simples e boa.",
        ])
    if re.fullmatch(
        r"(?:obrigad[oa]|valeu)(?:\s+(?:lay|laylay))?",
        limpo,
        flags=re.IGNORECASE,
    ):
        return escolher_variacao([
            "Que nada. Fico feliz que tenha ajudado.",
            "De nada. Eu reclamo um pouco, mas entrego.",
            "Por nada. Minha pose agradece o reconhecimento.",
        ])
    if re.fullmatch(r"(?:k{2,}|h+a+h+a+)(?:\s+.*)?", limpo, flags=re.IGNORECASE):
        return escolher_variacao([
            "Kkkkk, essa me pegou. Ponto seu.",
            "Tá, essa foi boa. Minha pose sofreu um dano leve.",
            "Kkkkk, aproveita a vitória porque eu não distribuo assim toda hora.",
        ])
    return ""


def _resposta_leitura_emocional_causal(
    texto: str,
    contexto: Mapping[str, Any] | None,
) -> str:
    """Usa somente a leitura social válida publicada para o turno atual."""
    if not isinstance(contexto, Mapping):
        return ""
    plano = contexto.get("plano_turno_atual")
    if not isinstance(plano, Mapping):
        plano = contexto
    evento = plano.get("evento_emocional_causal")
    if not isinstance(evento, Mapping) or not evento_tem_causa_rastreavel(evento):
        return ""
    if (
        str(evento.get("origem") or "").casefold()
        not in {"contingencia_lexical_usuario", "leitura_semantica_principal"}
        or str(evento.get("natureza_evidencia") or "").casefold()
        != "leitura_social"
    ):
        return ""
    texto_turno = re.sub(
        r"\s+", " ", str(plano.get("texto_usuario") or "")
    ).strip().casefold()
    if texto_turno and texto_turno != re.sub(r"\s+", " ", texto).strip().casefold():
        return ""
    leitura = analisar_intencao_emocional(texto)
    emocao = str(leitura.get("emocao") or "").casefold()
    respostas = {
        "tristeza": (
            "Eu ouvi que você está triste. Não vou maquiar isso; fico aqui com você.",
            "Entendo que hoje bateu tristeza. Pode falar no seu ritmo, sem cerimônia.",
            "Você está triste, e eu não vou empilhar positividade vazia em cima disso.",
        ),
        "alegria": (
            "Aí sim — você terminou o projeto e está feliz. Parabéns por essa conquista.",
            "Que notícia boa: projeto terminado e você feliz. Isso merece comemoração.",
            "Parabéns por terminar o projeto. Dá para sentir o quanto você ficou feliz com isso.",
        ),
        "ansiedade": (
            "Eu ouvi que você está ansioso. Posso ficar com você nessa conversa sem apressar nada.",
            "Entendo que a ansiedade apertou. Fala comigo no seu ritmo.",
        ),
        "medo": (
            "Eu ouvi que você está com medo. Não vou diminuir o que você está sentindo.",
            "Entendo essa insegurança. Pode me contar o que aconteceu, sem pressa.",
        ),
        "culpa": (
            "Eu ouvi que você está se sentindo culpado. Vamos olhar para o que aconteceu sem te esmagar por isso.",
            "Entendo que a culpa está pesando. Pode me contar a parte concreta, no seu ritmo.",
        ),
        "cansaco": (
            "Eu ouvi que você está cansado. Não vou transformar isso em palestra.",
            "Entendo que o cansaço bateu. Posso só te acompanhar por aqui.",
        ),
        "esgotamento": (
            "Eu ouvi que você chegou no limite. Não vou jogar uma solução automática em cima disso.",
            "Entendo que você está esgotado. Pode falar sem precisar organizar tudo primeiro.",
        ),
        "irritacao": (
            "Eu ouvi que você está irritado. Me conta a causa concreta e eu acompanho sem aumentar o fogo.",
            "Entendo essa irritação. Pode dizer o que aconteceu sem enfeitar.",
        ),
        "tedio": (
            "Eu ouvi que o tédio bateu. Posso pensar em algo com você sem fingir urgência.",
            "Entendo: está tudo meio parado. A gente pode puxar uma ideia daqui.",
        ),
    }
    opcoes = respostas.get(emocao)
    return escolher_variacao(opcoes) if opcoes else ""


def _preferencia_local(texto: str) -> str:
    """Responde a uma escolha explícita mesmo quando o modelo expirou."""
    match = re.search(
        r"\bprefere\s+(.+?)\s+ou\s+(.+?)(?:[?!.]|$)",
        texto,
        re.IGNORECASE,
    )
    if not match:
        return ""
    opcoes = sorted(
        {
            parte.strip(" ,.!?;:\"'")
            for parte in match.groups()
            if parte.strip(" ,.!?;:\"'")
        },
        key=str.casefold,
    )
    if len(opcoes) < 2:
        return ""
    assinatura = "laylay|" + "|".join(opcao.casefold() for opcao in opcoes)
    escolhida = opcoes[
        hashlib.sha256(assinatura.encode("utf-8")).digest()[0] % len(opcoes)
    ]
    return (
        f"Eu prefiro {escolhida}, porque entre as opções combina mais com meu "
        "jeito direto e ainda dá espaço para variar."
    )


def fala_contingencia_natural(
    texto_usuario: Any,
    contexto: Mapping[str, Any] | None = None,
) -> str:
    """Mantém humanidade sem fingir que a resposta da IA foi concluída."""
    bruto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()
    texto = bruto.casefold()
    saudacao = bool(re.match(
        r"^(?:oi|ol[aá]|opa|e\s+a[ií]|bom\s+dia|boa\s+tarde|boa\s+noite)\b",
        texto,
        re.IGNORECASE,
    ))
    pergunta_bem_estar = bool(re.search(
        r"\b(?:tudo\s+bem\s+(?:com\s+)?voc[eê]|"
        r"como\s+(?:voc[eê]|a\s+laylay|lay|laylay)\s+(?:est[aá]|vai))\b",
        bruto,
        re.IGNORECASE,
    ))
    if pergunta_bem_estar:
        prefixo = "Oi! " if saudacao else ""
        resposta = escolher_variacao([
            "Tô bem por aqui. E você, como tá?",
            "Por aqui está tudo certo. Agora quero saber de você.",
            "Tô bem, com a cabeça no lugar por enquanto. E você?",
        ])
        return prefixo + resposta
    if re.fullmatch(
        r"(?:oi|ol[aá]|opa|e a[ií]|bom dia|boa tarde|boa noite)"
        r"(?:[, ]+(?:lay|laylay))?[!?. ]*",
        texto,
    ):
        return escolher_variacao([
            "Oi. Tô aqui.",
            "Opa. Pode falar.",
            "Oi, cheguei. Qual é a de hoje?",
        ])

    if re.fullmatch(
        r"(?:deixa|deixe|vamos deixar|pode deixar) (?:isso )?"
        r"(?:para|pra) depois[!?. ]*",
        texto,
    ):
        return escolher_variacao([
            "Combinado. A gente deixa isso para depois.",
            "Beleza, fica para outro momento.",
            "Fechado. Isso sai da mesa por enquanto.",
        ])

    resposta_emocional = _resposta_leitura_emocional_causal(bruto, contexto)
    if resposta_emocional:
        return resposta_emocional

    social = _resposta_social_curta(bruto)
    if social:
        return social

    preferencia = _preferencia_local(bruto)
    if preferencia:
        return preferencia

    visual = _resposta_sobre_visual_recente(
        bruto,
        _ultima_observacao_visual(contexto),
    )
    if visual:
        return visual

    progresso = re.search(
        r"\b(?:eu\s+)?(?:to|tô|estou)\s+(terminando|construindo|fazendo|montando)\s+(.+?)[.!?]*$",
        bruto,
        flags=re.IGNORECASE,
    )
    if progresso:
        acao = progresso.group(1).casefold()
        alvo = progresso.group(2).strip(" .!?\"")
        alvo = re.sub(r"\bminha\b", "sua", alvo, count=1, flags=re.IGNORECASE)
        alvo = re.sub(r"\bmeu\b", "seu", alvo, count=1, flags=re.IGNORECASE)
        if acao == "terminando":
            return f"Ahh, então era isso. Vai terminando {alvo} no seu ritmo — quero ver como fica."
        return f"Aí sim. Continua {acao} {alvo}; quero ver onde essa ideia vai dar."

    if "?" in bruto or re.match(
        r"^(?:como|qual|quais|por que|porque|onde|quando|quem|o que|e esse|e essa)\b",
        texto,
    ):
        return escolher_variacao([
            "Essa eu não consegui fechar sem chutar. Me dá um detalhe a mais?",
            "Faltou uma peça aí. Explica só um pouco mais para eu não inventar moda.",
            "Dá para responder, mas agora seria no chute. Completa só essa parte.",
        ])
    return escolher_variacao([
        "A ideia chegou, só não veio inteira. Continua daí.",
        "Peguei o começo. Desenvolve mais um pouco para eu acompanhar direito.",
        "Eu acompanhei até aqui; falta só uma peça para isso fechar.",
    ])
