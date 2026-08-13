"""Validação semântica da fala contra o roteiro concreto do turno.

O validador não escolhe ações nem reescreve a fala. Ele identifica violações
fortes do contrato produzido antes da geração, para que o reparador canônico
possa fazer uma única nova tentativa antes de voz e memória.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping


_POSICAO = re.compile(
    r"\b(?:eu\s+)?(?:gosto|curto|prefiro|acho|escolheria|escolho|iria\s+de|"
    r"fico\s+com|vou\s+de|meu\s+voto\s+vai\s+(?:para|pra)|"
    r"me\s+parece|me\s+interessa)\b",
    re.IGNORECASE,
)
_SAUDACAO = re.compile(
    r"\b(?:oi|ol[aá]|e\s+a[ií]|bom\s+dia|boa\s+tarde|boa\s+noite|fala|"
    r"t[oô]\s+aqui|estou\s+aqui|por\s+aqui|presente)\b",
    re.IGNORECASE,
)
_ESTADO_POSITIVO = re.compile(
    r"\b(?:que\s+bom|bom\s+saber|a[ií]\s+sim|legal|fico\s+feliz|"
    r"beleza|boa)\b",
    re.IGNORECASE,
)
_RECONHECIMENTO_ESTADO = re.compile(
    r"\b(?:cans|trist|preocup|ansios|feliz|animad|entendo|imagino|poxa|"
    r"que\s+bom|bom\s+saber|a[ií]\s+sim|pega\s+leve|descans)\w*\b",
    re.IGNORECASE,
)
_ESTADO_USUARIO = re.compile(
    r"\b(?:estou|t[oô]|t[aá]|ando)\s+(?:tudo\s+|um\s+pouco\s+|meio\s+)?"
    r"(?P<estado>bem|mal|cansad[oa]|triste|preocupad[oa]|ansios[oa]|"
    r"feliz|animad[oa]|tranquil[oa])\b",
    re.IGNORECASE,
)
_PRIMEIRA_PESSOA = re.compile(
    r"\b(?:eu\s+)?(?:t[oô]|estou|vou|fico)|\bpor\s+aqui\b|\baqui\b|"
    r"\btudo\s+bem\b|\bbem\s+por\s+aqui\b|\btranquil[ao]\b",
    re.IGNORECASE,
)
_EXPERIENCIA_FISICA = re.compile(
    r"\b(?:meu\s+corpo|estou|t[oô])\s+com\s+fome\b|"
    r"\b(?:comi|bebi|dormi|acordei|sa[ií]|fui\s+ao|meu\s+est[oô]mago)\b",
    re.IGNORECASE,
)
_INFERENCIA_OCULTA_SAUDACAO = re.compile(
    r"\b(?:voc[eê]|tu)\b[^.!?]{0,70}\b(?:parece|deve\s+estar|"
    r"me\s+deixou\s+com\s+a\s+sensa[cç][aã]o|n[aã]o\s+est[aá]\s+muito\s+bem|"
    r"est[aá]\s+escondendo)\b",
    re.IGNORECASE,
)
_FALLBACK_GENERICO = re.compile(
    r"\b(?:peguei\s+o\s+que\s+voc[eê]\s+disse|"
    r"minha\s+resposta\s+n[aã]o\s+fechou|"
    r"entendi\s+a\s+a[cç][aã]o\s+que\s+voc[eê]\s+pediu|"
    r"continua\s*[-—,]?\s*eu\s+t[oô]\s+acompanhando)\b",
    re.IGNORECASE,
)
_ABSTRACAO_ISOLADA = re.compile(
    r"\b(?:[ée]|eh|parece|vira|traz|d[aá])\s+(?:uma?\s+)?"
    r"(?:energia|vibe|sensa[cç][aã]o|alma|universo|ritmo|ess[eê]ncia)"
    r"\s*[.!?…]*$",
    re.IGNORECASE,
)
_COMPARACAO_METAFORICA = re.compile(
    r"\b(?:[ée]|parece|soa)\s+como\s+(?:um|uma|o|a)\b|"
    r"\btipo\s+(?:um|uma)\b",
    re.IGNORECASE,
)
_RECONHECE_AGRADECIMENTO = re.compile(
    r"\b(?:de nada|por nada|imagina|eu que agrade[cç]o|tamo junto|"
    r"disponha|foi um prazer)\b",
    re.IGNORECASE,
)
_RETOMADA_OPERACIONAL = re.compile(
    r"\b(?:continuar|tocar|m[uú]sica|playlist|arquivo|pasta|app|aplicativo|"
    r"janela|luz|l[aâ]mpada|comando|tarefa|resumo|pesquisa)\b",
    re.IGNORECASE,
)
_ACEITE_ADIAMENTO = re.compile(
    r"\b(?:t[aá](?:\s+bom)?|beleza|combinado|deixamos|fica|deixa)\b",
    re.IGNORECASE,
)
_CONECTOR_CRITERIO = re.compile(
    r"\b(?:porque|pois|por\s+causa|pela|pelo|com|tem|costuma|usa|"
    r"mistura|varia|oferece|permite|mant[eé]m|traz)\b",
    re.IGNORECASE,
)
_DEBOCHE_ACUSATORIO_CODIGO = re.compile(
    r"\b(?:o\s+que\s+vai\s+virar\s+um\s+bug|"
    r"voc[eê][^.!?]{0,70}(?:vai|pode)[^.!?]{0,40}\bbug|"
    r"c[oó]digo[^.!?]{0,60}(?:nem\s+eu|n[aã]o)\s+consigo\s+ler)\b",
    re.IGNORECASE,
)
_AUTORREDUCAO_TECNICA = re.compile(
    r"\b(?:sou|eu\s+sou)\s+s[oó]\s+(?:uma?|um)\s+(?:estrutura\s+de\s+texto|"
    r"conjunto\s+de\s+regras|chatbot|programa|sistema)|"
    r"\bn[aã]o\s+(?:sou\s+um\s+sistema\s+vivo|tenho\s+vida|tenho\s+emo[cç][oõ]es\s+reais)\b",
    re.IGNORECASE,
)
_RELATO_MEXENDO_CODIGO = re.compile(
    r"\b(?:mexendo|alterando|editando|arrumando|corrigindo)\b.{0,50}\bc[oó]digo\b",
    re.IGNORECASE,
)
_NEGACAO_IDENTIDADE_OPERACIONAL = re.compile(
    r"\b(?:sou|eu\s+sou)\s+(?:s[oó]|apenas)\s+(?:uma?\s+)?(?:chatbot|ia|"
    r"assistente\s+de\s+texto)|"
    r"\bs[oó]\s+(?:consigo\s+)?(?:conversar|converso|responder|respondo|falar|falo)\b|"
    r"\bn[aã]o\s+(?:estou|t[oô]|fico|rodo|funciono)\s+(?:no|dentro\s+do)\s+seu\s+"
    r"(?:pc|computador)|"
    r"\bn[aã]o\s+tenho\s+acesso\s+(?:ao|a)\s+seu\s+(?:pc|computador)\b",
    re.IGNORECASE,
)

_STOPWORDS = {
    "a", "as", "ao", "aos", "aquele", "aquela", "aquilo", "com", "como",
    "da", "das", "de", "do", "dos", "e", "ela", "ele", "em", "essa", "esse",
    "eu", "isso", "mais", "mas", "me", "meu", "minha", "na", "nas", "no",
    "nos", "o", "os", "ou", "para", "pela", "pelo", "porque", "por", "que",
    "se", "sem", "ser", "so", "sua", "te", "tem", "tu", "um", "uma", "voce",
}
_ABSTRACOES = {
    "energia", "vibe", "sensacao", "alma", "universo", "ritmo", "essencia",
    "vivo", "viva",
}
_MARCADORES_POSICAO = {
    "acho", "curto", "escolheria", "gosto", "interessa", "iria", "parece",
    "prefiro",
}


def _normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9\s.!?]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _frases(texto: str) -> list[str]:
    return [
        parte.strip()
        for parte in re.split(r"(?<=[.!?…])\s+", str(texto or "").strip())
        if parte.strip()
    ]


def _tokens_relevantes(texto: str, *, referente: str = "") -> set[str]:
    ignorar = set(_STOPWORDS) | set(_ABSTRACOES) | set(_MARCADORES_POSICAO)
    ignorar.update(re.findall(r"[a-z0-9]+", _normalizar(referente)))
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalizar(texto))
        if len(token) >= 3 and token not in ignorar
    }


def _tem_criterio_concreto(resposta: str, *, referente: str = "") -> bool:
    if not _CONECTOR_CRITERIO.search(resposta):
        return False
    return len(_tokens_relevantes(resposta, referente=referente)) >= 2


def _encontrar_posicao(resposta: str, referente: str) -> re.Match[str] | None:
    """Reconhece preferência explícita sem exigir sempre o verbo 'prefiro'."""
    posicao = _POSICAO.search(resposta)
    if posicao:
        return posicao
    opcoes = [
        parte.strip(" ,.!?;:\"'")
        for parte in re.split(r"\s+ou\s+", referente, flags=re.IGNORECASE)
        if parte.strip(" ,.!?;:\"'")
    ]
    primeira = _frases(resposta)[0] if _frases(resposta) else resposta
    for opcao in opcoes:
        direta = re.search(rf"^\s*{re.escape(opcao)}(?:\b|\s*[,;:!.-])", primeira, re.I)
        if direta:
            return direta
    return None


def _termos_ancora(texto: str) -> set[str]:
    return {
        token
        for token in _tokens_relevantes(texto)
        if len(token) >= 4
    }


def _indice_reconhecimento_estado(texto_usuario: str, resposta: str) -> int:
    estado = _ESTADO_USUARIO.search(texto_usuario)
    resposta_norm = _normalizar(resposta)
    if not estado:
        return -1
    valor = _normalizar(estado.group("estado"))
    raiz = valor[:5] if len(valor) > 5 else valor
    if valor == "bem":
        achado = _ESTADO_POSITIVO.search(resposta)
    else:
        achado = re.search(rf"\b{re.escape(raiz)}\w*\b", resposta_norm)
        if not achado:
            achado = _RECONHECIMENTO_ESTADO.search(resposta)
    return int(achado.start()) if achado else -1


def _resumo_reparo(
    contrato: Mapping[str, Any],
    roteiro: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "estrategia": str(roteiro.get("estrategia") or "")[:64],
        "atos_obrigatorios": [
            str(item)[:64] for item in list(contrato.get("atos") or [])[:8]
        ],
        "referente": str(contrato.get("referente") or "")[:180],
        "nucleo_primeira_frase": str(roteiro.get("nucleo_resposta") or "")[:320],
        "sequencia": [str(item)[:220] for item in list(roteiro.get("sequencia") or [])[:6]],
        "max_frases": max(1, min(8, int(contrato.get("max_frases") or 3))),
        "permite_metafora": bool(contrato.get("permite_metafora", False)),
        "autoriza_execucao": False,
    }


def validar_aderencia_contrato_fala(
    texto_usuario: str,
    fala: str,
    *,
    contrato_fala: Mapping[str, Any] | None,
    ultima_resposta: str = "",
) -> dict[str, Any]:
    """Verifica violações fortes do roteiro sem interpretar comandos."""
    contrato = dict(contrato_fala or {})
    roteiro = dict(contrato.get("roteiro_concreto") or {})
    if not roteiro:
        return {
            "avaliado": False,
            "aceita": True,
            "requer_reparo": False,
            "problemas": [],
            "estrategia": "",
            "contrato_reparo": {},
            "autoriza_execucao": False,
        }

    usuario = str(texto_usuario or "").strip()
    resposta = str(fala or "").strip()
    estrategia = str(roteiro.get("estrategia") or "resposta_direta")
    referente = str(contrato.get("referente") or "").strip()
    atos = {str(item or "").casefold() for item in contrato.get("atos") or []}
    partes = _frases(resposta)
    primeira = partes[0] if partes else ""
    problemas: list[str] = []

    if resposta and _FALLBACK_GENERICO.search(resposta):
        problemas.append("resposta_generica_sem_conteudo")

    if estrategia == "saudacao_simples":
        if not _SAUDACAO.search(primeira):
            problemas.append("saudacao_nao_respondida_no_inicio")
        primeira_sem_pergunta = primeira if "?" not in primeira else ""
        if primeira_sem_pergunta and _INFERENCIA_OCULTA_SAUDACAO.search(primeira_sem_pergunta):
            problemas.append("saudacao_inferiu_estado_oculto")

    if estrategia in {"opiniao_com_criterio", "resposta_multiacto"} and "opiniao" in atos:
        posicao = _encontrar_posicao(resposta, referente)
        if not posicao:
            problemas.append("ato_opiniao_nao_respondido")
        elif estrategia == "opiniao_com_criterio" and not _POSICAO.search(primeira):
            problemas.append("opiniao_nao_veio_na_primeira_frase")
        if posicao and not _tem_criterio_concreto(resposta, referente=referente):
            problemas.append("opiniao_sem_criterio_concreto")

    if estrategia == "esclarecimento_literal":
        anterior = str(contrato.get("fala_anterior_relevante") or ultima_resposta or "")
        ancora = _termos_ancora(anterior)
        resposta_ancoras = _termos_ancora(resposta)
        if not primeira or ("?" in primeira and len(partes) == 1):
            problemas.append("esclarecimento_sem_explicacao")
        if ancora and not (ancora & resposta_ancoras):
            problemas.append("esclarecimento_sem_ancora_anterior")
        # O usuário pediu uma reformulação literal. Começar por outra imagem
        # figurada ("rock é como...") preserva palavras do assunto, mas não
        # esclarece o que foi dito e costuma produzir comparações sem sentido.
        if primeira and _COMPARACAO_METAFORICA.search(primeira):
            problemas.append("esclarecimento_comecou_por_outra_metafora")

    if estrategia in {"acolhimento_literal", "resposta_multiacto"} and "estado_pessoal" in atos:
        indice_estado = _indice_reconhecimento_estado(usuario, resposta)
        if indice_estado < 0:
            problemas.append("ato_estado_pessoal_nao_reconhecido")
        elif estrategia == "acolhimento_literal" and indice_estado > len(primeira):
            problemas.append("estado_pessoal_nao_veio_na_primeira_frase")
        if estrategia == "resposta_multiacto" and "opiniao" in atos:
            posicao = _POSICAO.search(resposta)
            if posicao and indice_estado >= 0 and indice_estado > posicao.start():
                problemas.append("ordem_multiacto_invertida")

    if estrategia == "reciprocidade_social":
        if not _PRIMEIRA_PESSOA.search(primeira):
            problemas.append("bem_estar_nao_respondido_no_inicio")
        if _EXPERIENCIA_FISICA.search(resposta):
            problemas.append("bem_estar_com_experiencia_fisica")

    if estrategia == "encerramento_social":
        if not _RECONHECE_AGRADECIMENTO.search(primeira):
            problemas.append("agradecimento_nao_reconhecido")
        usuario_norm = _normalizar(usuario)
        retomada = _RETOMADA_OPERACIONAL.search(resposta)
        if retomada and retomada.group(0) not in usuario_norm:
            problemas.append("agradecimento_retomou_assunto_antigo")
        if "?" in resposta:
            problemas.append("agradecimento_abriu_nova_pergunta")

    if estrategia == "adiamento_literal":
        if not _ACEITE_ADIAMENTO.search(primeira):
            problemas.append("adiamento_nao_reconhecido")
        if len(re.findall(r"[\wÀ-ÿ]+", resposta)) > 16 or "?" in resposta:
            problemas.append("adiamento_nao_foi_curto")

    proibidas = " ".join(
        str(item or "") for item in contrato.get("inferencias_proibidas") or ()
    ).casefold()
    if "código ilegível" in proibidas and _DEBOCHE_ACUSATORIO_CODIGO.search(resposta):
        problemas.append("deboche_acusou_usuario_de_estragar_codigo")

    if estrategia == "conversa_codigo_laylay":
        if _AUTORREDUCAO_TECNICA.search(resposta):
            problemas.append("metacomentario_quebrou_personagem")
        if _RELATO_MEXENDO_CODIGO.search(usuario):
            tokens_usuario = _tokens_relevantes(usuario)
            tokens_resposta = _tokens_relevantes(resposta)
            reacoes_genericas = {
                "agora", "beleza", "boa", "certo", "entendi", "entao",
                "legal", "sabia",
            }
            if not (tokens_resposta - tokens_usuario - reacoes_genericas):
                problemas.append("reacao_codigo_apenas_ecoou_relato")

    capacidades_confirmadas = tuple(
        str(item or "").strip()
        for item in contrato.get("capacidades_confirmadas") or ()
        if str(item or "").strip()
    )
    if capacidades_confirmadas and _NEGACAO_IDENTIDADE_OPERACIONAL.search(resposta):
        problemas.append("identidade_negou_capacidades_confirmadas")

    if not bool(contrato.get("permite_metafora", False)):
        for parte in partes:
            if _ABSTRACAO_ISOLADA.search(parte):
                problemas.append("abstracao_sem_apoio_concreto")
                break

    problemas = list(dict.fromkeys(problemas))
    nucleares = {
        "saudacao_nao_respondida_no_inicio",
        "ato_opiniao_nao_respondido",
        "opiniao_nao_veio_na_primeira_frase",
        "esclarecimento_sem_explicacao",
        "esclarecimento_sem_ancora_anterior",
        "esclarecimento_comecou_por_outra_metafora",
        "ato_estado_pessoal_nao_reconhecido",
        "estado_pessoal_nao_veio_na_primeira_frase",
        "bem_estar_nao_respondido_no_inicio",
        "resposta_generica_sem_conteudo",
        "agradecimento_nao_reconhecido",
        "agradecimento_retomou_assunto_antigo",
        "agradecimento_abriu_nova_pergunta",
        "adiamento_nao_reconhecido",
        "adiamento_nao_foi_curto",
        "deboche_acusou_usuario_de_estragar_codigo",
        "metacomentario_quebrou_personagem",
        "reacao_codigo_apenas_ecoou_relato",
        "identidade_negou_capacidades_confirmadas",
    }
    contrato_reparo = _resumo_reparo(contrato, roteiro)
    if "identidade_negou_capacidades_confirmadas" in problemas:
        contrato_reparo.update(
            reparar_identidade_operacional=True,
            capacidades_confirmadas=list(capacidades_confirmadas[:8]),
        )
    return {
        "avaliado": True,
        "aceita": not problemas,
        "requer_reparo": bool(problemas),
        "problemas": problemas,
        "estrategia": estrategia,
        "nucleo_atendido": not bool(nucleares.intersection(problemas)),
        "contrato_reparo": contrato_reparo,
        "autoriza_execucao": False,
    }
