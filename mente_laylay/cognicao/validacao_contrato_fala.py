"""Validação semântica da fala contra o roteiro concreto do turno.

O validador não escolhe ações nem reescreve a fala. Ele identifica violações
fortes do contrato produzido antes da geração, para que o reparador canônico
possa fazer uma única nova tentativa antes de voz e memória.
"""

from __future__ import annotations

import json
import re
import unicodedata
from typing import Any, Mapping
from mente_laylay.cognicao.incerteza_observacao import (
    expressa_incerteza_observacao,
    estado_sob_pergunta_referida,
)
from mente_laylay.cognicao.normalizacao_linguagem import TIPOS_REFERENCIA_TEXTUAL


def _contradicoes_capacidade(
    texto_usuario: str, fala: str, contrato: Mapping[str, Any], turno_id: Any,
) -> list[dict[str, str]]:
    """Confronta negativas gerais explícitas com fonte do mesmo turno.

    Gramática limitada de alegação, não classificador de comandos. Alvo
    específico, condição, citação ou predicado não cadastrado ficam fora.
    A lista de domínios confirmados não basta para atestar qualquer ação.
    """
    roteiro = dict(contrato.get("roteiro_concreto") or {})
    if not (
        turno_id and str(contrato.get("turno_id")) == str(turno_id)
        and contrato.get("origem") == "mente_unica"
        and contrato.get("autoriza_execucao") is False
        and roteiro.get("estrategia") == "explicacao_capacidades"
        and roteiro.get("ancora_literal") == texto_usuario
    ):
        return []
    try:
        documentos = json.loads(contrato.get("documentacao_capacidades") or "")
    except (TypeError, ValueError):
        return []
    if not isinstance(documentos, list):
        return []
    dominios = {
        d.get("dominio") for d in documentos if isinstance(d, dict)
        and isinstance(d.get("dominio"), str) and d.get("estado") == "disponivel"
    }
    if not dominios:
        return []
    # Não promover fala citada a alegação própria. O marcador mantém a
    # fronteira, impedindo que retirar uma citação junte pedaços de frases.
    sem_citacoes = re.sub(r'"[^"\n]*"|“[^”\n]*”|\x27[^\x27\n]*\x27|‘[^’\n]*’',
                          " [citacao] ", fala)
    contradicoes = []
    for frase in re.split(r"(?<=[.!?;])\s+", sem_citacoes):
        if "?" in frase:
            continue
        # A conclusão causal pode seguir uma alegação completa, mas não
        # condicionais como 'sem autorização' ou 'se o serviço cair'.
        trecho = re.split(r",\s*(?:ent[aã]o|por isso)\b", frase, maxsplit=1, flags=re.I)[0]
        normal = unicodedata.normalize("NFKD", trecho.casefold())
        normal = "".join(c for c in normal if not unicodedata.combining(c))
        normal = re.sub(r"\s+", " ", normal).strip().rstrip(".!;")
        for predicado in contrato.get("predicados_capacidade") or ():
            if not isinstance(predicado, Mapping) or predicado.get("dominio") not in dominios:
                continue
            if (predicado.get("capacidade") and predicado.get("acao")
                    and predicado.get("presente") and predicado.get("objetos")):
                intent = str(predicado["capacidade"])
                acao = re.escape(predicado["acao"])
                presentes = "|".join(re.escape(v) for v in predicado["presente"])
                sujeito = rf"(?:(?:eu )?nao (?:consigo|posso) {acao}|(?:eu |a laylay |laylay )nao (?:{presentes}))"
                objetos = []
                for objeto in predicado["objetos"]:
                    objetos.append(" ".join(
                        re.escape(palavra) + ("s?" if palavra not in {"do", "da", "de"} else "")
                        for palavra in objeto.split()
                    ))
                alvo = "(?:" + "|".join(objetos) + ")"
                # Só objeto genérico. 'Este programa', alvo nomeado e
                # outro computador não herdam capacidade geral do catálogo.
                padrao = (rf"{sujeito} (?:diretamente )?(?:(?:o|a|os|as) )?{alvo}"
                          r"(?: diretamente)?(?: no seu (?:computador|pc))?")
                if re.fullmatch(padrao, normal):
                    contradicoes.append({"capacidade": intent, "acao": predicado["acao"],
                                          "trecho": trecho.strip(), "fonte": "catalogo_vivo"})
    return contradicoes


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
_EMOCAO_PROPRIA_NA_FALA = re.compile(
    r"\b(?:eu\s+)?(?:estou|t[oô]|fiquei)\s+"
    r"(?:(?:muito|um\s+pouco|meio)\s+)?"
    r"(?:feliz|triste|ansios[ao]|preocupad[ao]|irritad[ao]|brav[ao]|"
    r"animad[ao]|cansad[ao])\b",
    re.IGNORECASE,
)
_APARENCIA_USUARIO_AFIRMADA = re.compile(
    r"\b(?:voc[eê]|tu|pedro)\s+(?:est[aá]|t[aá])\s+com\s+"
    r"(?:(?:um|uma)\s+)?(?:olhar|cara|rosto|express[aã]o|gesto)\b",
    re.IGNORECASE,
)
_APARENCIA_USUARIO_DECLARADA = re.compile(
    r"\b(?:eu\s+)?(?:estou|t[oô])\s+com\s+(?:(?:um|uma)\s+)?"
    r"(?:olhar|cara|rosto|express[aã]o|gesto)\b|"
    r"\b(?:meu|minha)\s+(?:olhar|cara|rosto|express[aã]o|gesto)\b",
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


_MARCADORES_DISCURSIVOS_RELATO = {
    "agora", "ainda", "assim", "enorme", "finalmente", "hoje", "muito",
    "pouco", "tanto", "voce",
}


def _relato_informativo_sem_ancora(
    usuario: str, resposta: str, contrato: Mapping[str, Any], roteiro: Mapping[str, Any],
) -> bool:
    """Detecta perda literal do assunto em uma reação a relato conversacional.

    É uma prova limitada: falta de termos em comum pede reparo, mas presença
    deles não atesta que a resposta compreendeu o relato.
    """
    if not (
        contrato.get("funcao") == "informacao"
        and set(contrato.get("atos") or ()) == {"conversa"}
        and roteiro.get("estrategia") == "resposta_direta"
        and roteiro.get("ancora_literal") == usuario
        and "?" not in usuario
    ):
        return False
    ancora = _termos_ancora(usuario) - _MARCADORES_DISCURSIVOS_RELATO
    if len(ancora) < 2:
        return False
    return not bool(ancora & (_termos_ancora(resposta) - _MARCADORES_DISCURSIVOS_RELATO))


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


def conferir_ato_social(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    """Confere um ato discursivo integral contra sua fonte atual.

    Consome segmentos já decididos e seu vínculo textual compartilhado, sem
    resegmentar. Saudação/recepção de agradecimento não certificam serviço
    prestado; acolhimento de relato não certifica o estado real da pessoa.
    Tom e declaração da IA não substituem a conferência da unidade inteira.
    """
    import hashlib
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos

    contrato = plano.get("contrato_fala")
    usuario, turno = plano.get("texto_usuario"), plano.get("id")
    if (not isinstance(contrato, Mapping) or not turno or type(usuario) is not str
        or contrato.get("origem") != "mente_unica"
        or str(contrato.get("turno_id")) != str(turno)
        or contrato.get("autoriza_execucao") is not False
        or plano.get("natureza_entrada") == "evento"
        or plano.get("requer_execucao") or plano.get("comandos")
        or dict(contrato.get("roteiro_concreto") or {}).get("ancora_literal") != usuario):
        return None
    atos = plano.get("atos")
    if (not isinstance(atos, list) or not atos
        or any(not isinstance(a, Mapping) or a.get("requer_execucao") is not False for a in atos)
        or any(type(a.get("ordem")) is not int or a["ordem"] != i for i, a in enumerate(atos))
        or any(a.get("tipo") != "pergunta" for a in atos[1:])):
        return None
    fontes = fontes_textuais_dos_segmentos(usuario, atos)
    if len(fontes) != len(atos):
        return None
    origem = fontes[0].como_dict()
    inicio, fim = origem["intervalo"]
    # Só o ato social é certificado. Conectores entre perguntas pertencem à
    # segmentação canônica; não são condição para provar a saudação inicial.
    # À esquerda não pode haver aspas, condição ou negação omitida; à direita
    # o trecho precisa terminar antes de um delimitador ou do fim da entrada.
    if (usuario[:inicio].strip()
        or (fim < len(usuario) and usuario[fim] not in ",;.!?")):
        return None
    trecho = origem["texto_original"]

    def dobrar(texto: str) -> str:
        # Preservar pontuação e aspas: removê-las poderia converter uma
        # citação, uma pergunta ou uma segunda oração em reconhecimento.
        texto = unicodedata.normalize("NFKD", texto.casefold())
        return re.sub(r"\s+", " ", "".join(c for c in texto if not unicodedata.combining(c))).strip()

    if type(fala) is not str or not fala or len(fala) > 140:
        return None
    texto, fonte = dobrar(fala), dobrar(trecho)

    def certificado(tipo: str, forma: str, papeis: dict[str, str]) -> dict[str, Any]:
        return {
            "regra": "ato_discursivo_fonte_atual_v2", "owner": "validacao_contrato_fala",
            "tipo_ato": tipo, "forma": forma, "escopo": "ato_discursivo_sobre_utterance_atual",
            "fonte": {"tipo": "utterance_atual", "turno_id": str(turno), "texto": trecho,
                      "intervalo": origem["intervalo"], "origem": origem["origem"],
                      "sha256": hashlib.sha256(usuario.encode("utf-8")).hexdigest()},
            "papeis": papeis,
            "realizacao": {"texto": fala, "intervalo": [0, len(fala)],
                           "sha256": hashlib.sha256(fala.encode("utf-8")).hexdigest()},
            "ato_conferido": True, "estado_real_verificado": False,
            "prova_semantica_livre": False, "pode_confirmar_fato_externo": False, "autoriza_execucao": False,
        }

    tipos = contrato.get("atos") or ()
    vocativo = r"(?:[, ]+(?:lay|laylay))?"
    if "saudacao" in tipos and atos[0].get("tipo") == "conversa":
        saudacao = re.fullmatch(rf"(?P<nucleo>oi|ola|e ai|bom dia|boa tarde|boa noite){vocativo}[.!]?", fonte)
        resposta = re.fullmatch(r"(?:oi|ola|e ai|bom dia|boa tarde|boa noite)[.!]?", texto)
        if saudacao and resposta:
            periodo = re.sub(r"[.!]$", "", texto)
            if periodo not in {"bom dia", "boa tarde", "boa noite"} or periodo == saudacao.group("nucleo"):
                return certificado("saudacao", "reciprocidade_de_saudacao", {
                    "emissor_original": "usuario", "destinatario": "usuario"})
    if ("agradecimento" in tipos and len(atos) == 1 and atos[0].get("tipo") in {"reacao", "conversa"}
        and re.fullmatch(rf"(?:obrigad[oa]|valeu|vlw){vocativo}[.!]?", fonte)
        and re.fullmatch(r"(?:de nada|por nada|disponha|imagina)[.!]?", texto)):
        return certificado("agradecimento", "recepcao_de_agradecimento", {
            "agradecedor": "usuario", "destinatario": "usuario"})
    if "estado_pessoal" not in tipos or atos[0].get("tipo") != "conversa":
        return None
    relato = _ESTADO_USUARIO.search(trecho)
    if (relato is None or trecho[:relato.start()].strip().casefold() not in {"", "eu"}
        or re.fullmatch(r"[.!]?", trecho[relato.end():]) is None
        or relato.group(0).split()[0].casefold() not in {"estou", "to", "tô", "ando"}):
        return None
    estado = dobrar(relato.group("estado"))
    positivo = estado in {"bem", "feliz", "animado", "animada", "tranquilo", "tranquila"}
    predicado = r"(?:que )?(?:bom|otimo|legal)"
    referencia = rf"que voce esta {re.escape(estado)}"
    formas = [("retomada_explicita", rf"entendo {referencia}")]
    if positivo:
        formas.extend([
            ("acolhimento_eliptico", rf"{predicado}(?: saber(?: disso)?)?"),
            ("acolhimento_explicito", rf"{predicado} (?:saber )?{referencia}"),
        ])
    forma = next((nome for nome, padrao in formas
                  if re.fullmatch(rf"(?:ah,? )?{padrao}[.!]?", texto)), None)
    if forma is None or not reconhecimento_estado_pessoal_valido(fala, relato.group("estado")):
        return None
    return certificado("estado_pessoal", forma, {
        "relator": "usuario", "destinatario": "usuario", "estado_declarado": estado})


def realizacoes_ato_social(plano: Mapping[str, Any]) -> tuple[str, ...]:
    """Projeta a gramática conferível do owner para negociação, sem prova da IA."""
    relato = _ESTADO_USUARIO.search(str(plano.get("texto_usuario") or ""))
    candidatas = ("Oi!", "Olá!", "Bom dia!", "Boa tarde!", "Boa noite!", "Por nada.", "De nada!")
    if relato is not None:
        estado = relato.group("estado").casefold()
        candidatas += ("Que bom saber!", f"Que bom que você está {estado}!",
                       f"Entendo que você está {estado}.")
    return tuple(fala for fala in candidatas if conferir_ato_social(fala, plano=plano) is not None)


def inventariar_atos_autoria(plano: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Alvos da emissão, não prova de que uma proposição responda à pergunta.

    Primeira adoção: saudação conferível seguida de perguntas não operacionais.
    Reusa o plano e o vínculo textual atuais; não interpreta a saída da IA.
    """
    import hashlib
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
    opcoes = tuple(f for f in realizacoes_ato_social(plano)
                   if conferir_ato_social(f, plano=plano).get("tipo_ato") == "saudacao")
    atos = plano.get("atos")
    if not opcoes or not isinstance(atos, list) or not 2 <= len(atos) <= 8:
        return ()
    texto = plano["texto_usuario"]
    fontes = fontes_textuais_dos_segmentos(texto, atos)
    if len(fontes) != len(atos):
        return ()
    itens = []
    for i, fonte in enumerate(fontes):
        dados = fonte.como_dict()
        identidade = json.dumps([str(plano["id"]), texto, i, dados["intervalo"]], ensure_ascii=False)
        itens.append({"id": "ato:" + hashlib.sha256(identidade.encode("utf-8")).hexdigest()[:24],
            "tipo": "saudacao" if i == 0 else "pergunta", "ordem": i,
            "texto_original": dados["texto_original"], "intervalo": dados["intervalo"],
            "turno_id": str(plano["id"]), "realizacoes": list(opcoes) if i == 0 else [],
            "autoriza_execucao": False, "prova_implicacao": False})
    return tuple(itens)


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


def _avaliar_realizacao_nuclear(
    texto_usuario: str, fala: str, contrato: Mapping[str, Any], turno_id: Any,
) -> dict[str, Any]:
    """Vínculo verificável de realização controlada, não inferência livre.

    As opções são regeneradas pelo owner, não confiadas ao JSON do modelo.
    Divergência do texto/seleção é contradição de vínculo; sem representação
    coberta não é possível decidir a verdade semântica da prosa livre.
    """
    from mente_laylay.cognicao.contrato_fala import realizar_nucleo_explicativo
    from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno

    resultado = {
        "avaliado": False, "aceita": False, "requer_reparo": False,
        "problemas": ["nucleo_sem_verificador"], "categoria": "cobertura_ausente",
        "nucleo_atendido": False, "contrato_reparo": {},
        "estrategia": str(dict(contrato.get("roteiro_concreto") or {}).get("estrategia") or ""),
        "autoriza_execucao": False, "prova_semantica_livre": False,
    }
    complemento = contrato.get("complemento_nuclear")
    proposta = contrato.get("proposta_nuclear")
    if not isinstance(complemento, ComplementoConversacionalTurno) or not isinstance(proposta, (Mapping, list)):
        return resultado
    if (not turno_id or turno_id != contrato.get("turno_id")
        or turno_id != complemento.turno_id or texto_usuario != complemento.texto):
        return {**resultado, "problemas": ["vinculo_nuclear_nao_vigente"]}
    def contradicao(motivo: str) -> dict[str, Any]:
        return {**resultado, "avaliado": True, "requer_reparo": True,
                "categoria": "contradicao_vinculo", "problemas": [motivo],
                "contrato_reparo": {"motivo": motivo, "autoriza_execucao": False,
                                    "limite": "mesma fonte e realizações do owner, sem conteúdo adicional"}}
    realizada, motivo = realizar_nucleo_explicativo(complemento, proposta)
    if motivo in {"nucleo_sem_verificador", "realizacao_sem_cobertura"}:
        return {**resultado, "problemas": [motivo]}
    if motivo:
        return contradicao(motivo)
    if fala.strip() != realizada:
        return contradicao("texto_diverge_da_realizacao")
    return {**resultado, "avaliado": True, "aceita": True,
            "categoria": "aderencia", "nucleo_atendido": True, "problemas": [],
            "cobertura": "realizacao_controlada_condicional", "indices_cobertos": list(complemento.indices)}


def validar_aderencia_contrato_fala(
    texto_usuario: str,
    fala: str,
    *,
    contrato_fala: Mapping[str, Any] | None,
    ultima_resposta: str = "",
    turno_id: Any = None,
) -> dict[str, Any]:
    """Verifica violações fortes do roteiro sem interpretar comandos."""
    contrato = dict(contrato_fala or {})
    if {"evidencia_fala_historica", "explicacao_ocorrencia", "explicacoes_historicas_por_ato", "revisao_alegacao"}.intersection(contrato):
        from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
        # Esta API verifica comunicação, sem poder validar execução. O guardião
        # também confere o plano concreto antes da publicação.
        historica = avaliar_fala_historica(fala, plano={
            "id": turno_id, "texto_usuario": texto_usuario, "contrato_fala": contrato,
            "autoriza_execucao": False, "requer_execucao": False, "comandos": [],
        })
        return {**historica, "avaliado": True, "aceita": not historica["problemas"],
                "requer_reparo": bool(historica["problemas"]),
                "estrategia": "explicacao_resultados_historicos", "contrato_reparo": {}}
    if contrato.get("exigir_nucleo_verificado") is True:
        return _avaliar_realizacao_nuclear(texto_usuario, fala, contrato, turno_id)
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
    contradicoes_capacidade = _contradicoes_capacidade(usuario, resposta, contrato, turno_id)
    if contradicoes_capacidade:
        problemas.append("capacidade_documentada_negada")

    if estrategia == "reconhecimento_social_direto":
        # A entrada já foi interpretada pelo owner social. Conferir recepção e
        # foco na fala não reinterpreta a utterance nem escolhe outra emoção.
        autoral = _TRECHO_CITADO.sub(" [citacao] ", resposta)
        atributo = str(dict(contrato.get("avaliacao_social") or {}).get("atributo") or "")
        if atributo:
            resposta_normal = unicodedata.normalize("NFKD", autoral.casefold())
            resposta_normal = "".join(c for c in resposta_normal if not unicodedata.combining(c))
            if contrato.get("funcao") == "elogio" and re.search(
                rf"\b(?:eu\s+)?nao\s+sou\s+(?:(?:nem\s+um\s+pouco|muito|nada)\s+)?{re.escape(atributo)}\b",
                resposta_normal,
            ):
                problemas.append("avaliacao_social_anulada")
            if contrato.get("funcao") == "critica_pessoal" and re.search(
                rf"\b(?:voce|tu|vc)\s+(?:e|eh|es)\s+(?:(?:muito|mo|bem)\s+)?{re.escape(atributo)}\b",
                resposta_normal,
            ):
                problemas.append("avaliacao_social_alvo_invertido")
        if contrato.get("funcao") == "elogio":
            if not re.search(
                r"\b(?:obrigad[ao]|agrade[cç]o|carinho|elogio|gostei|"
                r"gosto\s+de\s+voc[eê]|sem\s+jeito|fico\s+(?:feliz|contente))\b",
                primeira, re.I,
            ):
                problemas.append("avaliacao_social_nao_reconhecida")
            if re.search(
                r"\bn[aã]o\s+[ée]\s+(?:nada\s+especial|um\s+elogio)\b|"
                r"\b[ée]\s+s[oó]\s+(?:uma?\s+)?(?:brincadeira|conversa)\b|"
                r"\bn[aã]o\s+tenho\s+(?:um\s+)?(?:corpo|cora[cç][aã]o|sentidos)\b",
                autoral, re.I,
            ):
                problemas.append("avaliacao_social_anulada")
        elif not re.search(
            r"\b(?:entend\w*|receb\w*|ouvi|poxa|essa\s+doeu|"
            r"n[aã]o\s+era\s+(?:minha|a\s+minha)\s+inten[cç][aã]o)\b", primeira, re.I,
        ):
            problemas.append("avaliacao_social_nao_reconhecida")
        if contrato.get("funcao") in {"critica_pessoal", "rejeicao_pessoal"} and re.search(
            r"\bn[aã]o\s+[ée]\s+(?:uma?\s+)?(?:cr[ií]tica|rejei[cç][aã]o)\b",
            autoral, re.I,
        ):
            problemas.append("avaliacao_social_anulada")

    if estrategia == "analise_evidencia_textual" and contrato.get("estado_referencia_textual") == "nao_resolvida":
        if not solicita_fonte_sem_afirmar_conteudo(resposta):
            problemas.append("referencia_textual_ausente_sem_esclarecimento")

    if resposta and _FALLBACK_GENERICO.search(resposta):
        problemas.append("resposta_generica_sem_conteudo")
    if _relato_informativo_sem_ancora(usuario, resposta, contrato, roteiro):
        problemas.append("relato_atual_sem_ancora")
    resposta_autoral = _TRECHO_CITADO.sub(" ", resposta)
    if (
        "estado_pessoal" in atos
        and _ESTADO_USUARIO.search(usuario)
        and _EMOCAO_PROPRIA_NA_FALA.search(resposta_autoral)
    ):
        problemas.append("estado_pessoal_falante_invertido")
    if (
        _APARENCIA_USUARIO_AFIRMADA.search(resposta_autoral)
        and not _APARENCIA_USUARIO_DECLARADA.search(usuario)
    ):
        problemas.append("aparencia_do_usuario_sem_evidencia")

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
        if estrategia == "acolhimento_literal":
            causa_relato = re.search(r"\bporque\s+([^.!?]+)", usuario, re.IGNORECASE)
            if causa_relato:
                termos_causa = (
                    _termos_ancora(causa_relato.group(1))
                    - _MARCADORES_DISCURSIVOS_RELATO
                    - {"certo", "deu", "fiquei", "senti"}
                )
                if len(termos_causa) >= 2 and not termos_causa.intersection(
                    _termos_ancora(resposta)
                ):
                    problemas.append("estado_pessoal_causa_omitida")

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
        "avaliacao_social_alvo_invertido",
        "avaliacao_social_nao_reconhecida",
        "avaliacao_social_anulada",
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
        "estado_pessoal_causa_omitida",
        "estado_pessoal_falante_invertido",
        "aparencia_do_usuario_sem_evidencia",
        "estado_pessoal_nao_veio_na_primeira_frase",
        "bem_estar_nao_respondido_no_inicio",
        "resposta_generica_sem_conteudo",
        "relato_atual_sem_ancora",
        "agradecimento_nao_reconhecido",
        "agradecimento_retomou_assunto_antigo",
        "agradecimento_abriu_nova_pergunta",
        "adiamento_nao_reconhecido",
        "adiamento_nao_foi_curto",
        "deboche_acusou_usuario_de_estragar_codigo",
        "metacomentario_quebrou_personagem",
        "reacao_codigo_apenas_ecoou_relato",
        "identidade_negou_capacidades_confirmadas",
        "capacidade_documentada_negada",
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
    if estrategia == "expressao_solicitada":
        if "?" in fala:
            problemas.append("expressao_solicitada_abriu_pergunta")
        if len(fala.split()) > 32:
            problemas.append("expressao_solicitada_nao_foi_breve")
        if re.search(r"\b(?:se quiser|se voc[eê] quiser|posso inventar|imagens mentais|"
                     r"hip[oó]tese|suposi[cç][aã]o|n[aã]o sinto|n[aã]o tenho corpo|"
                     r"n[aã]o (?:posso|consigo)|n[aã]o vou (?:ficar|encenar|mostrar|fazer|mudar)|"
                     r"n[aã]o, eu n[aã]o recebi)\b", fala, re.I):
            problemas.append("expressao_solicitada_virou_recusa")
    contrato_reparo = _resumo_reparo(contrato, roteiro)
    if estrategia == "expressao_solicitada":
        contrato_reparo.update(
            preservar_identidade_emocional=True,
            evento_emocional_causal=dict(contrato.get("evento_emocional_causal") or {}),
        )
    if estrategia == "reconhecimento_social_direto":
        contrato_reparo.update(
            preservar_identidade_emocional=True,
            evento_emocional_causal=dict(contrato.get("evento_emocional_causal") or {}),
        )
    if contradicoes_capacidade:
        contrato_reparo["contradicoes_capacidade"] = contradicoes_capacidade
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
