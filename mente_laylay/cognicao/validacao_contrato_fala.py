"""Validação semântica da fala contra o roteiro concreto do turno.

O validador não escolhe ações nem reescreve a fala. Ele identifica violações
fortes do contrato produzido antes da geração, para que o reparador canônico
possa fazer uma única nova tentativa antes de voz e memória.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping
from mente_laylay.cognicao.incerteza_observacao import (
    expressa_incerteza_observacao,
    estado_sob_pergunta_referida,
)
from mente_laylay.cognicao.normalizacao_linguagem import TIPOS_REFERENCIA_TEXTUAL


def solicita_fonte_sem_afirmar_conteudo(fala: str) -> bool:
    """Gramática limitada do ato de pedir uma fonte ainda não resolvida.

    Não é um detector universal de verdade. Aceita apenas um pedido completo,
    com objeto textual e finalidade de análise; nenhum trecho livre pode
    acrescentar fatos antes/depois ou dentro de uma oração subordinada.
    Não é usada para conversa livre nem para fontes já identificadas.
    """
    texto = unicodedata.normalize("NFKD", str(fala or "").casefold())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto).strip()
    nome = "(?:" + "|".join(sorted(TIPOS_REFERENCIA_TEXTUAL | {"trecho", "conteudo"})) + ")"
    objeto = rf"(?:(?:o|esse|este|seu|um)\s+)?{nome}(?:\s+(?:do|desse|deste|de)\s+{nome})?(?:\s+(?:completo|integral))?"
    fonte = rf"{objeto}(?:\s+ou\s+{objeto})?"
    analisar = r"(?:analisar|analise|analisasse|avaliar|avalie|avaliasse|examinar|entender|dar\s+uma\s+olhada)"
    finalidade = rf"para\s+(?:eu\s+)?{analisar}(?:\s+o\s+que\s+(?:ele|o\s+relato)\s+(?:comprova|diz|informa))?"
    contexto = rf"(?:que\s+(?:voce\s+)?(?:quer|deseja|gostaria)\s+(?:que\s+eu\s+)?{analisar}|que\s+(?:voce\s+)?(?:mencionou|citou)|{finalidade})"
    verbo = (
        r"(?:(?:voce\s+)?(?:pode|poderia|consegue|conseguiria)\s+(?:me\s+)?"
        r"(?:mostrar|enviar|mandar|compartilhar|passar|colar)|"
        r"(?:me\s+)?(?:mostre|mostra|envie|envia|mande|manda|compartilhe|compartilha|passe|passa)|cole|cola)"
    )
    pedido = rf"{verbo}\s+(?:aqui\s+)?{fonte}(?:\s+(?:comigo|aqui))?(?:\s+{contexto})?"
    identificar = rf"(?:qual|que)\s+{fonte}\s+(?:que\s+)?(?:voce\s+)?(?:quer|deseja|gostaria)\s+(?:que\s+eu\s+)?{analisar}"
    identificar += rf"|a\s+qual\s+{nome}\s+voce\s+se\s+refere"
    necessidade = rf"preciso\s+(?:do|desse|deste|de)\s+{fonte}(?:\s+{finalidade})?"
    return bool(re.fullmatch(
        rf"(?:(?:por\s+favor|entendi|certo)[, ]+)?(?:{pedido}|{identificar}|{necessidade})(?:,?\s+por\s+favor)?[.?!]?",
        texto,
    ))


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
    r"\b(?:estou|t[oô]|t[aá]|ando)\s+"
    r"(?:tudo\s+|um\s+pouco\s+|meio\s+|muito\s+)?"
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
_MARCADORES_RESPOSTA_METALINGUISTICA = re.compile(
    r"\b(?:frases?|palavras?|express(?:[aã]o|[oõ]es)|formula[cç](?:[aã]o|[oõ]es)|"
    r"exemplos?|cita[cç](?:[aã]o|[oõ]es)|voc[eê]\s+citou|"
    r"voc[eê]\s+(?:pode|poderia)\s+(?:perguntar|dizer|escrever)|"
    r"(?:perguntar|dizer|escrever)\s+(?:exatamente\s+)?assim|"
    r"essa\s+pergunta\s+(?:j[aá]\s+)?funciona)\b",
    re.IGNORECASE,
)
_NEGACAO_CAPACIDADE_ESTADO_OBSERVAVEL = re.compile(
    r"\b(?:n[aã]o\s+(?:tenho|possuo)\s+acesso(?:\s+direto)?|"
    r"n[aã]o\s+consigo\s+(?:ver|consultar|verificar|observar|acompanhar))\b",
    re.IGNORECASE,
)
_RECONHECIMENTO_NEGACAO_OPERACIONAL = re.compile(
    r"\b(?:entendi|certo|beleza|pode\s+deixar|tem\s+raz[aã]o|"
    r"voc[eê]\s+n[aã]o\s+(?:pediu|perguntou|solicitou)|"
    # A abstenção é um ato de primeira pessoa, não uma lista de habilidades.
    # Negar capacidade (não vou conseguir/poder/saber) não reconhece a decisão.
    r"(?:n[aã]o|nunca|jamais)\s+(?:(?:vou|irei)\s+"
    r"(?!(?:conseguir|poder|saber)\b)[^\W\d_]+[aei]r|farei))\b",
    re.IGNORECASE,
)
_ALEGACAO_ESTADO_EM_NEGACAO_OPERACIONAL = re.compile(
    r"\b(?:n[aã]o\s+)?(?:est[aá]|continua|ficou|permanece)\s+"
    r"(?:abert[oa]s?|fechad[oa]s?|rodando|em\s+execu[cç][aã]o)\b|"
    r"\bn[aã]o\s+tem\s+como\s+estar\s+(?:abert[oa]|fechad[oa])\b",
    re.IGNORECASE,
)
_CLASSIFICACAO_METALINGUISTICA_EXPLICITA = re.compile(
    r"\bisso\s+[ée]\s+(?:uma?\s+)?(?P<tipo>consulta|pergunta|frase|comando)\b",
    re.IGNORECASE,
)
_NEGACAO_CLASSIFICACAO_METALINGUISTICA = re.compile(
    r"\bn[aã]o\s+(?:[ée]|se\s+trata\s+de)\s+(?:uma?\s+)?"
    r"(?P<tipo>consulta|pergunta|frase|comando)\b(?!\s+atual)",
    re.IGNORECASE,
)
_PEDIDO_NAO_CONSULTAR = re.compile(
    r"\bn[aã]o\s+(?:consulte|verifique|pesquise)\b",
    re.IGNORECASE,
)
_NEGACAO_GERAL_DE_CONSULTA = re.compile(
    r"\bn[aã]o\s+(?:fa[cç]o|realizo|consigo\s+(?:fazer|realizar))\s+"
    r"(?:consultas?|verifica[cç][oõ]es|pesquisas?)\b",
    re.IGNORECASE,
)
_LEITURA_ALTERNATIVA_METALINGUISTICA = re.compile(
    r"\b(?:tamb[eé]m\s+)?pode\s+ser\s+(?:interpretad[ao]|entendid[ao])\s+como\b|"
    r"\bpode\s+(?:tamb[eé]m\s+)?significar\b|\bcomo\s+se\s+(?:estiv[eé]ssemos|fosse)\b",
    re.IGNORECASE,
)
_PEDIDO_LEITURA_ALTERNATIVA = re.compile(
    r"\b(?:outr[oa]\s+(?:sentido|significado|interpreta[cç][aã]o)|"
    r"mais\s+de\s+um\s+(?:sentido|significado)|amb[ií]gu[ao]|"
    r"pode\s+(?:ser\s+interpretad[ao]|significar))\b",
    re.IGNORECASE,
)
_PEDIDO_FORMULACAO_DIRETA = re.compile(
    r"\b(?:como\s+eu\s+perguntaria|como\s+(?:posso|devo)\s+perguntar|"
    r"qual\s+(?:[ée]\s+)?a\s+forma\s+de\s+perguntar)\b",
    re.IGNORECASE,
)
_ENTREGA_FORMULACAO_DIRETA = re.compile(
    r"\b(?:voc[eê]\s+(?:pode|poderia)\s+perguntar|"
    r"pergunte\s+(?:exatamente\s+)?assim|a\s+forma\s+direta\s+[ée])\b",
    re.IGNORECASE,
)
_EXTRAPOLACAO_DECLARACAO_ESTADO = re.compile(
    r"\bn[aã]o\s+(?:tenho|temos|consigo|conseguimos)\s+acesso\b|"
    r"\bse\s+quiser\b|\bposso\s+ajudar\b|\bcomo\s+sempre\b|"
    r"\bj[aá]\s+sabia\b",
    re.IGNORECASE,
)
_TRECHO_CITADO = re.compile(r'["“«](?P<conteudo>.+?)["”»]')
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
_RETOMADA_ASSUNTO_AGRADECIMENTO = re.compile(
    r"\b(?:conversar|conversamos|falamos|assunto)\s+(?:sobre|de)\b",
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
    r"\bn[aã]o\s+tenho\s+acesso\s+(?:ao|a)\s+seu\s+(?:pc|computador)\b"
    r"|\bn[aã]o\s+tenho\s+acesso\s+direto\s+(?:ao|a|à)\s+"
    r"(?:spotify|youtube|opera|chrome|visual\s+studio\s+code|vs\s*code|"
    r"bloco\s+de\s+notas|plataforma)\b"
    r"|\b(?:spotify|youtube|opera|chrome|visual\s+studio\s+code|vs\s*code|"
    r"bloco\s+de\s+notas)\s+n[aã]o\s+(?:est[aá]|fica|existe)\s+"
    r"(?:no|em)\s+meu\s+sistema\b"
    r"|\bn[aã]o\s+(?:posso|consigo|vou|costumo)\s+abrir\s+"
    r"(?:o\s+|a\s+)?(?:spotify|youtube|opera|chrome|visual\s+studio\s+code|"
    r"vs\s*code|bloco\s+de\s+notas)\b"
    r"|\bn[aã]o\s+abro\s+nada\s+que\s+n[aã]o\s+esteja\s+no\s+meu\s+sistema\b",
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
_CAPITALIZADAS_GENERICAS = {
    "agora", "ah", "ainda", "assim", "beleza", "bom", "certo", "entendi",
    "entao", "fico", "laylay", "nao", "nesse", "neste", "olha", "sim", "talvez",
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


def _termos_nomeados(texto: str) -> set[str]:
    """Extrai âncoras nomeadas sem tentar fazer reconhecimento de entidades."""
    termos: set[str] = set()
    padrao = re.compile(
        r"\b[A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ]"
        r"[A-Za-zÁÀÂÃÉÊÍÓÔÕÚÜÇáàâãéêíóôõúüç0-9+.-]{2,}\b"
    )
    for achado in padrao.finditer(str(texto or "")):
        termo = _normalizar(achado.group(0))
        if termo and termo not in _CAPITALIZADAS_GENERICAS:
            termos.add(termo)
    return termos


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


def _opcao_escolhida(resposta: str, referente: str) -> str:
    """Lê somente uma escolha explícita entre as opções do referente."""
    base = _normalizar(resposta)
    opcoes = [
        parte.strip(" ,.!?;:\"'")
        for parte in re.split(r"\s+ou\s+", referente, flags=re.IGNORECASE)
        if parte.strip(" ,.!?;:\"'")
    ]
    for opcao in opcoes:
        opcao_norm = _normalizar(opcao)
        if re.search(
            rf"\b(?:prefiro|escolho|vou\s+de|fico\s+com|iria\s+de)\s+"
            rf"{re.escape(opcao_norm)}\b",
            base,
        ) or re.match(rf"^{re.escape(opcao_norm)}(?:\b|\s*[,;:!.-])", base):
            return opcao_norm
    return ""


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
        if not achado:
            # Uma atribuição explícita ao usuário não depende de um bordão.
            # Não aceitar uma oração que negue ou questione esse estado.
            for frase in _frases(resposta):
                if "?" in frase or re.search(r"\b(?:n[aã]o|nem)\b", frase, re.IGNORECASE):
                    continue
                explicito = re.search(r"\bvoc[eê]\s+est[aá]\s+bem\b", frase, re.IGNORECASE)
                if explicito:
                    return resposta.find(frase) + explicito.start()
    else:
        achado = re.search(rf"\b{re.escape(raiz)}\w*\b", resposta_norm)
        if not achado:
            achado = _RECONHECIMENTO_ESTADO.search(resposta)
    return int(achado.start()) if achado else -1


def reconhecimento_estado_pessoal_valido(fala: str, estado: str) -> bool:
    """Valida só o fragmento de acolhimento, nunca o conteúdo temático restante."""
    texto = str(fala or "").strip()
    if not texto or len(texto) > 140 or "?" in texto or len(_frases(texto)) != 1:
        return False
    # Não permitir que o reparador inverta o falante do estado informado.
    if re.search(r"\b(?:eu|estou|t[oô]|ando)\b", texto, re.IGNORECASE):
        return False
    return _indice_reconhecimento_estado("estou " + str(estado), texto) >= 0


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
        "estado_referencia_textual": str(contrato.get("estado_referencia_textual") or ""),
        "texto_usuario_corrigido": str(contrato.get("texto_usuario_corrigido") or "")[:500],
        "nucleo_primeira_frase": str(roteiro.get("nucleo_resposta") or "")[:320],
        "sequencia": [str(item)[:220] for item in list(roteiro.get("sequencia") or [])[:6]],
        "max_frases": max(1, min(8, int(contrato.get("max_frases") or 3))),
        "permite_metafora": bool(contrato.get("permite_metafora", False)),
        "autoriza_execucao": False,
        # A fonte já foi selecionada pelo contrato do turno. Reparar uma
        # explicação não pode obrigar o modelo a reconstruí-la pelo rascunho.
        **({"documentacao_capacidades": contrato["documentacao_capacidades"]}
           if roteiro.get("estrategia") == "explicacao_capacidades"
           and contrato.get("documentacao_capacidades") else {}),
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

    if estrategia == "analise_evidencia_textual" and contrato.get("estado_referencia_textual") == "nao_resolvida":
        if not solicita_fonte_sem_afirmar_conteudo(resposta):
            problemas.append("referencia_textual_ausente_sem_esclarecimento")

    if resposta and _FALLBACK_GENERICO.search(resposta):
        problemas.append("resposta_generica_sem_conteudo")

    if (
        estrategia == "resposta_metalinguistica"
        and not _MARCADORES_RESPOSTA_METALINGUISTICA.search(resposta)
    ):
        problemas.append("metalinguagem_tratada_como_conteudo")

    if estrategia == "resposta_metalinguistica":
        classificacao = _CLASSIFICACAO_METALINGUISTICA_EXPLICITA.search(usuario)
        contradicao = _NEGACAO_CLASSIFICACAO_METALINGUISTICA.search(resposta)
        if (
            classificacao
            and contradicao
            and classificacao.group("tipo").casefold()
            == contradicao.group("tipo").casefold()
        ):
            problemas.append("metalinguagem_contradisse_classificacao")

        if (
            _LEITURA_ALTERNATIVA_METALINGUISTICA.search(resposta)
            and not _PEDIDO_LEITURA_ALTERNATIVA.search(usuario)
        ):
            problemas.append("metalinguagem_inventou_leitura_alternativa")
        if (
            _PEDIDO_FORMULACAO_DIRETA.search(usuario)
            and not _ENTREGA_FORMULACAO_DIRETA.search(resposta)
        ):
            problemas.append("metalinguagem_nao_entregou_formulacao_direta")

        if _PEDIDO_NAO_CONSULTAR.search(usuario):
            tokens_usuario = _tokens_relevantes(usuario)
            for citacao in _TRECHO_CITADO.finditer(resposta):
                tokens_citados = _tokens_relevantes(citacao.group("conteudo"))
                if tokens_citados and not tokens_citados.issubset(tokens_usuario):
                    problemas.append("metalinguagem_citou_conteudo_ausente")
                    break
            if _termos_nomeados(resposta) - tokens_usuario:
                problemas.append("metalinguagem_introduziu_entidade_ausente")
            if _NEGACAO_GERAL_DE_CONSULTA.search(resposta):
                problemas.append("metalinguagem_negou_capacidade")

    if estrategia == "estado_observavel_sem_evidencia":
        if not expressa_incerteza_observacao(resposta):
            problemas.append("estado_observavel_sem_incerteza")
        if _NEGACAO_CAPACIDADE_ESTADO_OBSERVAVEL.search(resposta):
            problemas.append("estado_observavel_negou_habilidade")
        recentes = contrato.get("respostas_recentes_evitar") or ()
        nomes_recentes = {
            termo
            for fala_recente in recentes
            for termo in _termos_nomeados(str(fala_recente or ""))
        }
        tokens_usuario = _tokens_relevantes(usuario)
        tokens_resposta = _tokens_relevantes(resposta)
        # Só contexto explicitamente vinculado à correção pelo contrato; não
        # transformar o histórico inteiro de respostas em fonte de entidades.
        tokens_correcao = (
            _tokens_relevantes(str(contrato.get("texto_usuario_corrigido") or ""))
            if contrato.get("funcao") == "correcao" else set()
        )
        if (nomes_recentes & tokens_resposta) - tokens_usuario - tokens_correcao:
            problemas.append("estado_observavel_herdou_entidade_antiga")

    if estrategia == "negacao_operacional_sem_efeito":
        if not _RECONHECIMENTO_NEGACAO_OPERACIONAL.search(resposta):
            problemas.append("negacao_operacional_sem_reconhecimento")
        if any(
            not estado_sob_pergunta_referida(resposta[:ocorrencia.start()])
            for ocorrencia in _ALEGACAO_ESTADO_EM_NEGACAO_OPERACIONAL.finditer(resposta)
        ):
            problemas.append("negacao_operacional_alegou_estado")
        if len(partes) > 1:
            problemas.append("negacao_operacional_extrapolou")

    if estrategia == "reconhecimento_relato_explicito" and "?" in resposta:
        problemas.append("relato_explicito_abriu_pergunta")

    if estrategia == "reconhecimento_estado_declarado":
        termos_usuario = _tokens_relevantes(usuario)
        if _termos_nomeados(resposta) - termos_usuario:
            problemas.append("declaracao_introduziu_entidade_ausente")
        if _EXTRAPOLACAO_DECLARACAO_ESTADO.search(resposta):
            problemas.append("declaracao_extrapolou_estado_informado")

    if estrategia == "saudacao_simples":
        if not _SAUDACAO.search(primeira):
            problemas.append("saudacao_nao_respondida_no_inicio")
        primeira_sem_pergunta = primeira if "?" not in primeira else ""
        if primeira_sem_pergunta and _INFERENCIA_OCULTA_SAUDACAO.search(primeira_sem_pergunta):
            problemas.append("saudacao_inferiu_estado_oculto")
        vocativo = re.match(
            r"^\s*(?:oi|ol[aá])\s*,\s*([^,.!?]{1,40})[.!?]",
            primeira,
            flags=re.IGNORECASE,
        )
        if vocativo:
            valor = _normalizar(vocativo.group(1))
            genericos = {
                "tudo bem", "to aqui", "estou aqui", "por aqui", "cheguei",
                "bom te ver", "que bom",
            }
            if valor not in genericos:
                problemas.append("saudacao_inventou_vocativo")

    if estrategia in {"opiniao_com_criterio", "resposta_multiacto"} and "opiniao" in atos:
        posicao = _encontrar_posicao(resposta, referente)
        if not posicao:
            problemas.append("ato_opiniao_nao_respondido")
        elif estrategia == "opiniao_com_criterio" and not _POSICAO.search(primeira):
            problemas.append("opiniao_nao_veio_na_primeira_frase")
        if posicao and not _tem_criterio_concreto(resposta, referente=referente):
            problemas.append("opiniao_sem_criterio_concreto")
        anterior_opiniao = str(
            contrato.get("fala_anterior_relevante") or ultima_resposta or ""
        )
        escolha_anterior = _opcao_escolhida(anterior_opiniao, referente)
        escolha_atual = _opcao_escolhida(resposta, referente)
        if (
            escolha_anterior
            and escolha_atual
            and escolha_anterior != escolha_atual
        ):
            problemas.append("opiniao_contradisse_posicao_recente")

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
        if (
            (retomada and retomada.group(0) not in usuario_norm)
            or _RETOMADA_ASSUNTO_AGRADECIMENTO.search(resposta)
        ):
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
        "referencia_textual_ausente_sem_esclarecimento",
        "relato_explicito_abriu_pergunta",
        "saudacao_nao_respondida_no_inicio",
        "saudacao_inventou_vocativo",
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
        "metalinguagem_tratada_como_conteudo",
        "metalinguagem_contradisse_classificacao",
        "metalinguagem_citou_conteudo_ausente",
        "metalinguagem_introduziu_entidade_ausente",
        "metalinguagem_negou_capacidade",
        "metalinguagem_inventou_leitura_alternativa",
        "metalinguagem_nao_entregou_formulacao_direta",
        "estado_observavel_sem_incerteza",
        "estado_observavel_negou_habilidade",
        "estado_observavel_herdou_entidade_antiga",
        "negacao_operacional_sem_reconhecimento",
        "negacao_operacional_alegou_estado",
        "negacao_operacional_extrapolou",
        "declaracao_introduziu_entidade_ausente",
        "declaracao_extrapolou_estado_informado",
    }
    contrato_reparo = _resumo_reparo(contrato, roteiro)
    estado_informado = _ESTADO_USUARIO.search(usuario) if "estado_pessoal" in atos else None
    if estado_informado:
        contrato_reparo["estado_pessoal_informado"] = {
            "falante": "usuario", "estado": estado_informado.group("estado"),
        }
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
