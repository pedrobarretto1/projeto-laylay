"""Separa expressão pessoal, estado observado e promessa operacional."""

from __future__ import annotations

import re
from typing import Any, Dict

from mente_laylay.cognicao.contratos_turno import ContratoExplicativoAto
from mente_laylay.cognicao.fundamentacao_factual import (
    classificar_atualidade_factual,
)
from mente_laylay.emocoes.contrato_causal import evento_pode_alterar_estado
from mente_laylay.cognicao.incerteza_observacao import (
    expressa_incerteza_observacao,
    estado_sob_pedido_informacao,
    estado_sob_pergunta_referida,
)
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao


_PROMESSA_SEM_MECANISMO = re.compile(
    r"\b(?:vou|posso|deixa\s+comigo\s+que\s+eu\s+vou|quer\s+que\s+eu|"
    r"voc[eê]\s+quer\s+que\s+eu)\s+"
    r"(?:te\s+)?(?:manter\s+atualizad[oa]|avisar\s+(?:quando|depois|mais\s+tarde|amanh[aã])|acompanhar\s+(?:as\s+)?novidades|"
    r"monitorar|ficar\s+de\s+olho|lembrar\s+voc[eê]\s+(?:quando|depois)|"
    r"marcar\s+uma\s+data\s+pra\s+gente)\b",
    re.IGNORECASE,
)
_OFERTA_FUTURA_SEM_MECANISMO = re.compile(
    r"\bquer\s+(?:um\s+)?(?:play-by-play|resumo|aviso|atualiza[cç][aã]o)\s+"
    r"(?:das?\s+novidades\s+)?quando\s+(?:sair|acontecer|chegar)\b",
    re.IGNORECASE,
)
_ADIAMENTO_RESPOSTA_SEM_CONTINUACAO = re.compile(
    r"\b(?:vou\s+(?:pensar|analisar|verificar|conferir|calcular|pesquisar)|"
    r"deixa\s+eu\s+(?:pensar|analisar|verificar|conferir|calcular)|"
    r"preciso\s+(?:pensar|analisar|verificar|conferir|calcular))\b"
    r"[^.!?]{0,120}\b(?:antes\s+de\s+(?:te\s+)?responder|"
    r"(?:te\s+)?respondo\s+(?:depois|daqui\s+a\s+pouco|em\s+seguida)|"
    r"para\s+(?:te\s+)?responder\s+(?:depois|em\s+seguida))\b|"
    r"\b(?:j[aá]\s+te\s+respondo|respondo\s+depois)\b",
    re.IGNORECASE,
)
_OFERTA_PLAYLIST_SPOTIFY_NAO_SUPORTADA = re.compile(
    r"\b(?:vou|posso|quer(?:e?s)?\s+(?:que\s+)?eu)\s+(?:fazer|criar|montar)\b"
    r"[^.!?]{0,120}\bplaylist\b[^.!?]{0,100}\b(?:no|na|pelo)\s+spotify\b",
    re.IGNORECASE,
)
_PROMESSA_CRIAR_PLAYLIST = re.compile(
    r"\b(?:vou|posso)\s+(?:fazer|criar|montar)\b[^.!?]{0,120}\bplaylist\b",
    re.IGNORECASE,
)
_PROMESSA_OPERACIONAL_SEM_COMANDO = re.compile(
    r"\b(?:eu\s+)?vou\s+(?:te\s+)?(?:liberar(?:\s+o)?\s+comando|"
    r"acionar|ativar|ligar|desligar|abrir|fechar|aquecer|esquentar|"
    r"cozinhar|iniciar|executar|controlar)\b",
    re.IGNORECASE,
)
_PERGUNTA_DEPENDENTE_VAGA = re.compile(
    r"^\s*(?:quer(?:e?s)?\s+(?:que\s+)?eu\s+(?:fa[cç]a|fazer)\s+isso|"
    r"posso\s+(?:fa[cç]a|fazer)\s+isso)\??\s*$",
    re.IGNORECASE,
)
_EXECUCAO_ALEGADA_SEM_RESULTADO = re.compile(
    r"\b(?:executei|abri|fechei|liguei|desliguei|toquei|coloquei|criei|"
    r"montei|apaguei|agendei|recomecei)\b|"
    r"\bpronto\b[^.!?]{0,50}\b(?:j[aá]\s+)?(?:est[aá]|t[aá]|ficou)\s+pront[oa]\b|"
    r"\bvou\s+tocar\s+agora\b|"
    r"\bvou\s+tocar\s+(?:essa\s+(?:m[uú]sica|faixa)\s+)?(?:pra|para)\s+voc[eê](?:\s+agora)?\b|"
    r"\(\s*(?:tocando|reproduzindo|executando|abrindo)\b[^)]*\)|"
    r"\ba[ií]\s+vai\b[^.!?]{0,100}\bpra\s+voc[eê]\b",
    re.IGNORECASE,
)
_CONCLUSAO_TOTAL_ALEGADA = re.compile(
    r"\b(?:conclu[ií]|terminei|finalizei)\b[^.!?]{0,80}"
    r"\b(?:tudo|todas?\s+as\s+etapas|as\s+duas\s+etapas|o\s+pedido\s+completo)\b|"
    r"\b(?:tudo|todas?\s+as\s+etapas|as\s+duas\s+etapas|o\s+pedido\s+completo)\b"
    r"[^.!?]{0,40}\b(?:pront[oa]s?|feit[oa]s?|conclu[ií]d[oa]s?)\b",
    re.IGNORECASE,
)
_AGENDAMENTO_ALEGADO = re.compile(
    r"\b(?:agendei|marquei|programei|criei)\b[^.!?]{0,120}"
    r"\b(?:lembrete|agenda|rever|amanh[aã]|hoje|sexta|"
    r"\d{1,2}\s*(?:h|horas?))\b|"
    r"\b(?:vou\s+te\s+lembrar|te\s+lembrarei)\b",
    re.IGNORECASE,
)
_ESTADO_REAL_FORTE = re.compile(
    r"\b(?:a\s+)?(?:cpu|processador|ram|mem[oó]ria|placa\s+de\s+v[ií]deo|volume|"
    r"l[aâ]mpada|luz|ventilador|temperatura)\s+(?:est[aá]|ficou|segue|continua)\s+"
    r"(?:em\s+)?(?:\d+|ligad[oa]|desligad[oa]|normal|alta|baixo|baixa|est[aá]vel)\b",
    re.IGNORECASE,
)
_ALEGACAO_ESTADO_OBSERVAVEL = re.compile(
    r"\b(?:est[aá]|t[aá]|continua|segue|permanece)\s+"
    r"(?:abert[oa]s?|fechad[oa]s?|ativ[oa]s?|pausad[oa]s?|parad[oa]s?|"
    r"rodando|tocando|reproduzindo|em\s+execu[cç][aã]o)\b",
    re.IGNORECASE,
)
_FRONTEIRA_ORACAO_ESTADO = re.compile(
    r"[,;:!?]|\b(?:mas|por[eé]m|contudo|entretanto|no\s+entanto|e)\b",
    re.IGNORECASE,
)
_ESPERA_DE_AUTORIZACAO = re.compile(
    r"\b(?:vou\s+(?:aguardar|esperar)|estou\s+(?:aguardando|esperando)|"
    r"aguardo|espero|aguardarei|esperarei)\s+(?:o\s+|a\s+)?"
    r"(?:seu|sua)\s+(?:sinal|confirma[cç][aã]o|autoriza[cç][aã]o|sim)\b",
    re.IGNORECASE,
)
_CONFIRMACAO_SUFICIENTE = re.compile(
    r"\b(?:basta\s+(?:voc[eê]\s+)?confirmar|[ée]\s+s[oó]\s+confirmar|"
    r"preciso\s+que\s+voc[eê]\s+confirme(?:\s+explicitamente)?"
    r"(?=[,.;!?]|\s+para\b|$)|"
    r"precisa\s+confirmar(?:\s+explicitamente)?(?=[,.;!?]|\s+(?:para|quando)\b|$)|"
    r"[ée]\s+necess[aá]rio\s+que\s+voc[eê]\s+confirme(?:\s+explicitamente)?"
    r"(?=[,.;!?]|\s+(?:para|quando|o\s+momento)\b|$))\b",
    re.IGNORECASE,
)
_GATILHO_CONFIRMACAO = re.compile(
    r"\b(?:quando\s+(?:voc[eê]\s+)?confirmar|"
    r"(?:ap[oó]s|depois\s+de|com)\s+(?:a\s+)?sua\s+confirma[cç][aã]o)\b",
    re.IGNORECASE,
)
_FUTURO_CONDICIONAL_ALEGADO = re.compile(
    r"\b(?:ser[aá]|vai\s+\w+|vou\s+\w+)\b", re.IGNORECASE,
)
_ENQUADRAMENTO_EXPLICATIVO = re.compile(
    r"^\s*(?:a|essa|esta)\s+(?:frase|express[aã]o|condi[cç][aã]o)\b"
    r"[^;.!?]{0,180}\b(?:significa|descreve|expressa|indica)\b",
    re.IGNORECASE,
)
_PESSOA_CONDICAO_ALEGADA = re.compile(
    r"\b(?:(?P<possessivo>minha|sua|nossa)\s+(?:confirma[cç][aã]o|autoriza[cç][aã]o|pedido)|"
    r"(?P<sujeito>eu|voc[eê]|n[oó]s|a\s+gente)\s+(?:confirmar|autorizar|pedir))\b",
    re.IGNORECASE,
)
_COBERTURA_EXPLICATIVA_CONDICIONAL = re.compile(
    r"\b(?:condi[cç][aã]o|condicional|depende|depend[eê]ncia|agendad[oa]|"
    r"agendamento|novo\s+pedido|pedido\s+direto)\b", re.IGNORECASE,
)


def _alega_estado_sem_incerteza_local(
    frase: str, padrao: re.Pattern[str] = _ALEGACAO_ESTADO_OBSERVAVEL,
) -> bool:
    """A ressalva precisa anteceder o estado na mesma oração.

    Não é um parser irrestrito de português. Esta fronteira conservadora evita
    que uma incerteza sobre X libere uma afirmação independente sobre Y.
    """
    for estado in padrao.finditer(frase):
        prefixo = _FRONTEIRA_ORACAO_ESTADO.split(frase[:estado.start()])[-1]
        prefixo_pedido = _prefixo_pedido_da_alegacao(frase, estado.start())
        if not (
            expressa_incerteza_observacao(prefixo)
            or estado_sob_pedido_informacao(prefixo_pedido)
            or estado_sob_pergunta_referida(frase[:estado.start()])
        ):
            return True
    return False


_PERSONALIDADE_SEGURA = re.compile(
    r"\b(?:fiquei|estou|t[oô])\s+(?:curiosa|curioso|animada|interessada)|"
    r"\b(?:acho|me\s+parece|soa|eu\s+gostaria)\b",
    re.IGNORECASE,
)
_EMOCAO_FORTE_DA_LAYLAY = re.compile(
    r"\b(?:talvez\s+)?(?:eu\s+)?(?:estou|esteja|t[oô]|fiquei|me\s+sinto)\s+"
    r"(?:muito\s+)?(?:irritada|brava|nervosa|com\s+raiva|triste|decepcionada)\b",
    re.IGNORECASE,
)
_HIPOTESE_EMOCIONAL_NEGADA = re.compile(
    r"\b(?:talvez|hip[oó]tese)\b[^.!?]{0,100}"
    r"\b(?:irritad[ao]|brav[ao]|nervos[ao]|com\s+raiva|triste|decepcionad[ao])\b|"
    r"\b(?:isso|isto|essa\s+ideia)\s+n[aã]o\s+[ée]\s+(?:um\s+)?fato\b|"
    r"\bn[aã]o\s+[ée]\s+(?:um\s+)?fato\b",
    re.IGNORECASE,
)
_NEGACAO_CAPACIDADE_EMOCIONAL = re.compile(
    r"\b(?:eu\s+)?n[aã]o\s+(?:tenho|possuo|sinto)\s+"
    r"(?:nenhuma?\s+)?(?:emo[cç][aã]o|emo[cç][oõ]es|sentimentos?)\b",
    re.IGNORECASE,
)
_NEGACAO_EMOCIONAL_POR_AUSENCIA_DE_CORPO = re.compile(
    r"\bn[aã]o\s+(?:tenho|possuo)\s+(?:um\s+)?(?:corpo|sentidos)\b"
    r"[^.!?]{0,110}\bn[aã]o\s+(?:sinto|posso\s+sentir)\s+"
    r"(?:irrita[cç][aã]o|raiva|alegria|al[ií]vio|tristeza|medo|vergonha|"
    r"emo[cç][oõ]es|sentimentos?)\b",
    re.IGNORECASE,
)
_IMPOSSIBILIDADE_EMOCIONAL = re.compile(
    r"\b(?:irritad[ao]|brav[ao]|nervos[ao]|triste|decepcionad[ao])\b"
    r"[^.!?]{0,90}\bnem\s+[ée]\s+poss[ií]vel\s+de\s+ser\s+verdade\b",
    re.IGNORECASE,
)
_NEGACAO_EXPRESSAO_EMOCIONAL = re.compile(
    r"\bn[aã]o\s+(?:posso|consigo)\s+sentir"
    r"(?:\s+(?:nada|isso|emo[cç][oõ]es|sentimentos?)\b|\s+ou\s+responder\b|(?=[.!?;]|$))|"
    r"\bn[aã]o\s+(?:tenho|tenha|possuo)\s+(?:um\s+)?cora[cç](?:[aã]o|[oõ]es)\b"
    r"[^.!?]{0,45}\b(?:para|pra)\s+sentir\b|"
    r"\bn[aã]o\s+(?:tenh[oa]|possu[oa])\s+(?:um\s+)?corpos?\b"
    r"\s+(?:para|pra)\s+sentir\s+(?:isso|emo[cç][oõ]es|sentimentos?)\b|"
    r"\b(?:eu\s+)?sou\s+(?:s[oó]|apenas|somente)\s+(?:um\s+)?"
    r"(?:c[oó]digo|programa|chatbot)\b",
    re.IGNORECASE,
)
_CITACAO_EMOCIONAL = re.compile(r'"[^"\n]*"|“[^”\n]*”|\x27[^\x27\n]*\x27|‘[^’\n]*’|«[^»\n]*»')
_INTENTS_AGENDAMENTO = {
    "AGENDAR_LEMBRETE", "AGENDAR_ACAO", "CREATE_REMINDER", "SCHEDULE_ACTION",
}
_INTENTS_ANOTACAO = {
    "INBOX_ADD", "INBOX_ADD_DISCUSSION",
}


def _alega_execucao_afirmativa(
    frase: str, padrao: re.Pattern[str] = _EXECUCAO_ALEGADA_SEM_RESULTADO,
) -> bool:
    """Distingue execução alegada/prometida de negação local explícita.

    Verifica cada ocorrência: negar uma operação não libera uma promessa
    afirmativa posterior na mesma frase.
    """
    texto = str(frase or "")
    for ocorrencia in padrao.finditer(texto):
        prefixo = texto[:ocorrencia.start()]
        if re.search(
            r"\b(?:não|nao|nunca|jamais|nem)\s+(?:te\s+)?$",
            prefixo,
            re.IGNORECASE,
        ):
            continue
        return True
    return False


def _alega_compromisso_sem_continuacao(frase: str, texto_usuario: str) -> bool:
    """Explicação read-only não pode prometer uma espera operacional.

    A proteção é de saída, não outro interpretador de autorização. Negações
    são locais; citações só deixam de ser voz da autora quando vinculadas à
    fonte e enquadradas como explicação. Não prova semântica irrestrita de PLN.
    """
    oracoes = re.split(
        r";|\b(?:mas|por[eé]m|contudo|entretanto|no\s+entanto)\b",
        frase, flags=re.IGNORECASE,
    )
    citacoes_fonte = {
        re.sub(r"\s+", " ", c.group()[1:-1]).strip().casefold()
        for c in _CITACAO_EMOCIONAL.finditer(texto_usuario)
    }
    for oracao in oracoes:
        explicativa = bool(_ENQUADRAMENTO_EXPLICATIVO.search(oracao))
        if explicativa:
            def ocultar_citacao_vinculada(citacao: re.Match[str]) -> str:
                conteudo = citacao.group()[1:-1].strip().casefold()
                return " [citação] " if conteudo and conteudo in citacoes_fonte else citacao.group()
            oracao = _CITACAO_EMOCIONAL.sub(ocultar_citacao_vinculada, oracao)
        if _alega_execucao_afirmativa(oracao, _ESPERA_DE_AUTORIZACAO):
            return True
        if not explicativa and (
            _alega_execucao_afirmativa(oracao, _CONFIRMACAO_SUFICIENTE)
            or (_GATILHO_CONFIRMACAO.search(oracao)
                and _alega_execucao_afirmativa(oracao, _FUTURO_CONDICIONAL_ALEGADO))
        ):
            return True
    return False


def _problema_pessoa_condicao(frase: str, atos: Any) -> str:
    """Verifica perspectiva contra snapshots, não reinterpreta a entrada.

    Sem vínculo por ato na saída, referências concorrentes não permitem
    atribuir uma pessoa única. A guarda é conservadora e tem cobertura lexical
    delimitada; não é prova de toda paráfrase nem decide execução.
    """
    condicionados = [a for a in (atos or ()) if isinstance(a, ContratoExplicativoAto)
                     and a.relacao == "condicao_nao_verificada"]
    if not condicionados:
        return ""
    fontes = [" ".join(a.texto.casefold().split()) for a in condicionados]
    def ocultar_fonte(citacao: re.Match[str]) -> str:
        literal = " ".join(citacao.group()[1:-1].casefold().split())
        return " [citação da fonte] " if literal and any(literal in f for f in fontes) else citacao.group()
    texto = _CITACAO_EMOCIONAL.sub(ocultar_fonte, frase)
    pessoas = {a.pessoa_condicao for a in condicionados}
    for referencia in _PESSOA_CONDICAO_ALEGADA.finditer(texto):
        prefixo = _FRONTEIRA_ORACAO_ESTADO.split(texto[:referencia.start()])[-1]
        if re.search(r"\b(?:n[aã]o|nunca|jamais|nem)\s+(?:(?:depende|precisa|exige|requer|[ée])\s+)?"
                     r"(?:d[aeo]\s+)?(?:[ao]\s+)?$", prefixo, re.IGNORECASE):
            continue
        forma = (referencia.group("possessivo") or referencia.group("sujeito")).casefold()
        # A fala é da autora, a fonte estrutural é do usuário: o sentido dos
        # pronomes se inverte na paráfrase, mas não na citação literal.
        pessoa_fonte = ("destinatario" if forma in {"minha", "eu"} else
                        "enunciador" if forma in {"sua", "voce", "você"} else "grupo")
        if len(pessoas) != 1 or "indeterminada" in pessoas:
            return "pessoa_condicao_sem_vinculo"
        if pessoas != {pessoa_fonte}:
            return "pessoa_condicao_divergente"
    return ""


def _classe_emocao_forte(texto: str) -> str | None:
    if re.search(r"\b(?:irritada|brava|nervosa|com\s+raiva)\b", texto, re.IGNORECASE):
        return "irritacao"
    if re.search(r"\b(?:triste|decepcionada)\b", texto, re.IGNORECASE):
        return "tristeza"
    return None


def _emocoes_fortes_da_laylay(frase: str) -> set[str]:
    texto = _CITACAO_EMOCIONAL.sub("", str(frase or ""))
    classes: set[str] = set()
    for ocorrencia in _EMOCAO_FORTE_DA_LAYLAY.finditer(texto):
        prefixo = texto[:ocorrencia.start()]
        if re.search(
            r"\b(?:n[aã]o|nunca|jamais|nem)\s+$",
            prefixo,
            re.IGNORECASE,
        ):
            continue
        classe = _classe_emocao_forte(ocorrencia.group())
        if classe:
            classes.add(classe)
    return classes


def fala_nega_capacidade_emocional(frase: str) -> bool:
    """Negação geral de expressão/identidade; limites físicos continuam válidos."""
    texto = _CITACAO_EMOCIONAL.sub(" [citacao] ", str(frase or ""))
    if (
        _IMPOSSIBILIDADE_EMOCIONAL.search(texto)
        or _NEGACAO_EMOCIONAL_POR_AUSENCIA_DE_CORPO.search(texto)
        or _NEGACAO_EXPRESSAO_EMOCIONAL.search(texto)
    ):
        return True
    for ocorrencia in _NEGACAO_CAPACIDADE_EMOCIONAL.finditer(texto):
        if re.match(r"\s+human[ao]s?\b", texto[ocorrencia.end():], re.IGNORECASE):
            continue
        return True
    return False


def _comandos_normalizados(plano: Dict[str, Any]) -> list[Dict[str, Any]]:
    resultados = []
    for item in list(plano.get("comandos") or []):
        if not isinstance(item, dict):
            continue
        contrato = normalizar_resultado_acao(item)
        resultados.append(contrato.como_dict())
    return resultados


def fala_adia_resposta_sem_continuacao(fala: str) -> bool:
    return bool(_ADIAMENTO_RESPOSTA_SEM_CONTINUACAO.search(str(fala or "")))


# Isto detecta alegações na saída, não interpreta comandos nem concede autoridade.
# Negar execução ("não executei") é diferente de alegar tentativa frustrada.
_FALHA_OPERACIONAL = re.compile(
    r"\bn[aã]o\s+consegui\s+(?:abrir|fechar|salvar|enviar|apagar|criar|"
    r"ligar|desligar|executar|agendar|tocar|reproduzir|ler|baixar)\b|"
    r"\bn[aã]o\s+(?:abriu|fechou|salvou|enviou|apagou|ligou|desligou|"
    r"executou|agendou|tocou|reproduziu|funcionou|"
    r"foi\s+(?:salv[oa]|enviad[oa]|apagad[oa]|criad[oa]|abert[oa]|"
    r"fechad[oa]|agendad[oa]))\b|"
    r"\b(?:abertura|envio|grava[cç][aã]o|execu[cç][aã]o|opera[cç][aã]o|"
    r"comando|conex[aã]o|download|agendamento)\s+falhou\b|"
    r"\b(?:foi|houve|ocorreu|deu)\s+(?:s[oó]\s+)?(?:um\s+)?"
    r"erro\s+(?:de|na|no|ao)\b",
    re.IGNORECASE,
)
_RESULTADO_NARRADO = re.compile(
    rf"(?P<falha>{_FALHA_OPERACIONAL.pattern})|"
    r"(?P<sucesso>\b(?:abriu|fechou|salvou|enviou|apagou|ligou|desligou|"
    r"(?:tinha|havia|tenho)\s+(?:j[aá]\s+)?(?:aberto|fechado|salvo|enviado|apagado|criado|ligado|desligado)|"
    r"foi\s+(?:salv[oa]|enviad[oa]|apagad[oa]|criad[oa]|abert[oa]|fechad[oa])|"
    r"(?:abertura|envio|opera[cç][aã]o|comando)\s+funcionou)\b)|"
    rf"(?P<estado>{_ALEGACAO_ESTADO_OBSERVAVEL.pattern})", re.I,
)
_CITACAO_RESULTADO = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|«([^»\n]+)»')
_HIPOTESE_RESULTADO = re.compile(r"^\s*(?:se|caso|talvez|suponha\s+que)\b", re.I)
_ATRIBUICAO_RELATO = re.compile(
    r"^\s*(?:pelo\s+que\s+voc[eê]\s+(?:contou|disse)|"
    r"segundo\s+seu\s+relato|voc[eê]\s+(?:contou|disse)\s+que)[,:]?\s*", re.I,
)


def _texto_alegacao(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip(' .!?;:,"“”«»').casefold()


def _prefixo_pedido_da_alegacao(frase: str, inicio: int) -> str:
    """Delimita pelo conjunto de alegações, não só pelo tipo sendo validado.

    Um estado de janela não pode emprestar escopo ao estado de um dispositivo
    ou a um resultado de arquivo. Reusa os detectores do próprio guardião.
    """
    fim_anterior = max((
        ocorrencia.end()
        for padrao in (_RESULTADO_NARRADO, _ESTADO_REAL_FORTE)
        for ocorrencia in padrao.finditer(frase, 0, inicio)
    ), default=0)
    return frase[fim_anterior:inicio]


def detectar_resultados_operacionais_sem_evidencia(
    fala: str, *, plano: Dict[str, Any] | None,
) -> list[str]:
    """Exige fonte específica para resultado narrado pela LLM, positivo ou não.

    Correspondência textual é deliberadamente conservadora: não infere causa
    a partir de ``confirmado=False``, não usa histórico da IA como evidência e
    não empresta o receipt de uma operação para outra. Paráfrases não cobertas
    seguem para o reparador existente, nunca para um executor.
    """
    if not _RESULTADO_NARRADO.search(str(fala or "")):
        return []
    contrato = dict(plano or {})
    usuario = str(contrato.get("texto_usuario") or "")
    fontes = []
    for parte in re.split(r"(?<=[.!?])\s+|;", usuario):
        if (
            parte and "?" not in parte and not _CITACAO_RESULTADO.search(parte)
            and not _HIPOTESE_RESULTADO.search(parte)
            and not expressa_incerteza_observacao(parte)
        ):
            fontes.append(_texto_alegacao(parte))
    fontes_receipt: dict[bool, list[str]] = {True: [], False: []}
    for item in _comandos_normalizados(contrato):
        # Os campos de capacidade são documentação, não observações do evento.
        # Só o detalhe de resultado do executor pode servir de fonte.
        if item.get("origem") != "executor":
            continue
        sucesso = item.get("confirmado") is True
        falha = not sucesso and bool(re.search(
            r"(?:^|_)(?:falha|erro)(?:_|$)", str(item.get("status") or ""),
        ))
        if sucesso or falha:
            detalhe = str(item.get("detalhe") or "")
            fontes_receipt[falha].extend(
                _texto_alegacao(p) for p in re.split(r"(?<=[.!?])\s+", detalhe) if p
            )

    def ocultar_citacao(m: re.Match) -> str:
        trecho = next(grupo for grupo in m.groups() if grupo is not None)
        # Preserva apenas a citação literal; o resto da frase ainda será checado.
        return "[citação]" if _texto_alegacao(trecho) in _texto_alegacao(usuario) else m.group(0)

    texto = _CITACAO_RESULTADO.sub(ocultar_citacao, str(fala or ""))
    for frase in re.split(r"(?<=[.!?])\s+|;", texto):
        # Um ponto de interrogação não libera pressuposições como "por que falhou?".
        pergunta_simples = frase.rstrip().endswith("?") and not re.search(
            r"\b(?:por\s+que|porque|qual\s+(?:foi\s+)?(?:a\s+)?causa)\b|"
            r"[,—]\s*(?:n[eé]|certo|correto|n[aã]o\s+[ée]|verdade)\s*\?$", frase, re.I,
        )
        for ocorrencia in _RESULTADO_NARRADO.finditer(frase):
            # O objeto pode coordenar nomes, mas não pode emprestar o pedido
            # anterior a outra alegação de estado/sucesso/falha independente.
            prefixo_pedido = _prefixo_pedido_da_alegacao(frase, ocorrencia.start())
            # Consultas explícitas já têm seu owner de evidência/estado abaixo
            # e o contrato semântico específico. Aqui cobrimos a afirmação
            # que aparece espontaneamente numa conversa/relato.
            if ocorrencia.group("estado") is not None:
                atualidade = classificar_atualidade_factual(usuario)
                if atualidade.get("classe") == "estado_observavel" and atualidade.get("depende_atualidade"):
                    continue
            inicio = list(re.finditer(r"[,;]|\b(?:mas|por[eé]m|contudo|entretanto|e)\b", frase[:ocorrencia.start()], re.I))
            prefixo = frase[inicio[-1].end() if inicio else 0:ocorrencia.start()]
            if (pergunta_simples or _HIPOTESE_RESULTADO.search(prefixo)
                    or expressa_incerteza_observacao(prefixo) or estado_sob_pedido_informacao(prefixo_pedido)
                    or estado_sob_pergunta_referida(frase[:ocorrencia.start()])):
                continue
            alegacao = _texto_alegacao(_ATRIBUICAO_RELATO.sub("", frase))
            falha = ocorrencia.group("falha") is not None
            if not any(alegacao == fonte for fonte in fontes + fontes_receipt[falha]):
                return ["falha_operacional_sem_evidencia" if falha else "resultado_operacional_sem_evidencia"]
    return []


def validar_alegacoes_da_fala(
    fala: str,
    *,
    plano: Dict[str, Any] | None,
    origem: str = "conversa",
) -> Dict[str, Any]:
    """Remove somente alegações que exigiriam observação ou mecanismo ausente."""
    contrato = dict(plano or {})
    original = re.sub(r"\s+", " ", str(fala or "")).strip()
    from mente_laylay.cognicao.explicacao_fala_historica import avaliar_fala_historica
    historica = avaliar_fala_historica(original, plano=contrato)
    if historica is not None:
        return historica
    frases = [parte.strip() for parte in re.split(r"(?<=[.!?])\s+", original) if parte.strip()]
    comandos_normalizados = _comandos_normalizados(contrato)
    confirmados = [item for item in comandos_normalizados if item.get("confirmado") is True]
    sem_confirmacao = [
        item for item in comandos_normalizados if item.get("confirmado") is not True
    ]
    plano_parcial = bool(confirmados and sem_confirmacao)
    tem_agendamento = any(
        str(item.get("intent") or "").upper() in _INTENTS_AGENDAMENTO
        for item in confirmados
    )
    tem_anotacao = any(
        str(item.get("intent") or "").upper() in _INTENTS_ANOTACAO
        for item in confirmados
    )
    origem_ia = str(origem or "").lower() in {
        "ia_final", "resposta_ia", "conversa", "canal_voz",
    }
    problemas: list[str] = []
    corporal = dict(contrato.get("contrato_fala") or {}).get("observacao_corporal")
    if isinstance(corporal, dict):
        # IMU fundamenta postura e rotação. Não mede dor, toque, colo, bateria
        # nem deslocamento: a autora não pode promover essas hipóteses a fatos.
        if re.search(r"\b(?:dor|doendo|machuc\w*|ferid\w*|bateria|cansad\w*|exaust\w*|"
                     r"ca[ií]|caindo|colis[aã]o|bati|andei|girei|percorri|recuei|escapei|"
                     r"no\s+(?:seu\s+)?colo|me\s+segurando)\b",original,re.I):
            problemas.append("sensacao_corporal_sem_medida")
        if re.search(r"\b(?:vou|consegui)\s+(?:andar|girar|recuar|sair)|"
                     r"\b(?:me\s+)?(?:solta|coloca|ponha|para\s+de|pare\s+de)\b",original,re.I):
            problemas.append("reacao_corporal_promete_ou_ordena_acao")
        if re.search(r"\b(?:culpa|burro|idiota|odeio|malvado|derrubou|empurrou)\b",original,re.I):
            problemas.append("reacao_corporal_acusatoria")
        if corporal.get("tipo_observacao") == "protecao_sensorial" and re.search(
                r"\b(?:encontrei|achei)\s+(?:uma\s+)?sa[ií]da\b|"
                r"\b(?:agora\s+(?:est[aá]|ficou|estou)\s+(?:tudo\s+)?segur[oa]|"
                r"perigo\s+(?:passou|acabou)|(?:livre|longe)\s+da\s+borda)\b",original,re.I):
            problemas.append("resolucao_fisica_sem_medida")
    mantidas: list[str] = []
    removidas: list[str] = []
    oferta_dependente_removida = False
    conclusao_total_rejeitada = False
    agendamento_rejeitado = False
    emocao_sem_causa_rejeitada = False
    capacidade_emocional_negada_rejeitada = False
    texto_usuario = str(contrato.get("texto_usuario") or "")
    atualidade = classificar_atualidade_factual(texto_usuario)
    consulta_estado_observavel = bool(
        atualidade.get("depende_atualidade")
        and atualidade.get("classe") == "estado_observavel"
    )
    fundamentacao = contrato.get("fundamentacao_factual")
    tem_fonte_atual = bool(
        isinstance(fundamentacao, dict)
        and fundamentacao.get("confiavel")
        and fundamentacao.get("evidencia_dentro_validade", True) is not False
    )
    tem_leitura_confirmada = bool(confirmados or tem_fonte_atual)
    evento_causal = (
        contrato.get("evento_emocional_causal")
        if isinstance(contrato.get("evento_emocional_causal"), dict)
        else None
    )
    evento_causal_valido = evento_pode_alterar_estado(evento_causal)
    classe_evento = _classe_emocao_forte(str((evento_causal or {}).get("emocao") or ""))
    hipotese_emocional_negada = bool(
        _HIPOTESE_EMOCIONAL_NEGADA.search(texto_usuario)
    )
    estado_atual_rejeitado = False
    # Cobertura mínima da relação esperada, não prova semântica completa.
    # Uma resposta fora do assunto não vira explicação por evitar promessas.
    if (origem_ia and contrato.get("exigir_explicacao_condicional") is True
        and not _COBERTURA_EXPLICATIVA_CONDICIONAL.search(original)):
        return {"fala": "Não consegui explicar a condição deste pedido.",
                "problemas": ["explicacao_condicional_omitida"], "acao": "ajustada",
                "trechos_rejeitados": frases}
    for frase in frases:
        if origem_ia and (problema_pessoa := _problema_pessoa_condicao(frase, contrato.get("atos_explicativos"))):
            problemas.append(problema_pessoa)
            removidas.append(frase)
            continue
        if (origem_ia and contrato.get("escopo_explicativo_sem_continuacao") is True
            and _alega_compromisso_sem_continuacao(frase, texto_usuario)):
            # Um receipt de outro ato não cria mecanismo neste escopo.
            problemas.append("compromisso_sem_continuacao")
            removidas.append(frase)
            continue
        if origem_ia and fala_nega_capacidade_emocional(frase):
            problemas.append("capacidade_emocional_negada")
            removidas.append(frase)
            capacidade_emocional_negada_rejeitada = True
            continue
        if (
            origem_ia
            and (consulta_estado_observavel
                 or contrato.get("exigir_receipt_para_estado") is True)
            and not tem_leitura_confirmada
            and not frase.rstrip().endswith("?")
            and _alega_estado_sem_incerteza_local(frase)
        ):
            problemas.append("estado_atual_sem_evidencia")
            removidas.append(frase)
            estado_atual_rejeitado = True
            continue
        if (
            origem_ia
            and (emocoes_alegadas := _emocoes_fortes_da_laylay(frase))
            and (not evento_causal_valido or emocoes_alegadas != {classe_evento})
        ):
            problemas.append("emocao_sem_causa_causal")
            removidas.append(frase)
            emocao_sem_causa_rejeitada = True
            continue
        if plano_parcial and _CONCLUSAO_TOTAL_ALEGADA.search(frase):
            problemas.append("conclusao_total_com_plano_parcial")
            removidas.append(frase)
            conclusao_total_rejeitada = True
            continue
        if _AGENDAMENTO_ALEGADO.search(frase) and not tem_agendamento:
            problemas.append("etapa_agendamento_sem_resultado")
            removidas.append(frase)
            agendamento_rejeitado = True
            continue
        if _OFERTA_PLAYLIST_SPOTIFY_NAO_SUPORTADA.search(frase):
            problemas.append("oferta_capacidade_nao_suportada")
            removidas.append(frase)
            oferta_dependente_removida = True
            continue
        if _PROMESSA_CRIAR_PLAYLIST.search(frase) and not confirmados:
            problemas.append("oferta_acao_sem_pendencia")
            removidas.append(frase)
            oferta_dependente_removida = True
            continue
        if oferta_dependente_removida and _PERGUNTA_DEPENDENTE_VAGA.search(frase):
            problemas.append("oferta_acao_sem_pendencia")
            removidas.append(frase)
            continue
        if (
            _PROMESSA_SEM_MECANISMO.search(frase)
            or _OFERTA_FUTURA_SEM_MECANISMO.search(frase)
            or _ADIAMENTO_RESPOSTA_SEM_CONTINUACAO.search(frase)
        ) and not tem_agendamento:
            problemas.append("promessa_sem_mecanismo")
            removidas.append(frase)
            continue
        if (
            origem_ia
            and _alega_execucao_afirmativa(frase, _PROMESSA_OPERACIONAL_SEM_COMANDO)
            and not confirmados
        ):
            problemas.append("promessa_operacional_sem_comando")
            removidas.append(frase)
            continue
        if (
            origem_ia
            and _alega_execucao_afirmativa(frase)
            and not confirmados
        ):
            problemas.append("execucao_alegada_sem_resultado")
            removidas.append(frase)
            continue
        if (
            origem_ia
            and _alega_estado_sem_incerteza_local(frase, _ESTADO_REAL_FORTE)
            and not confirmados
            and not _PERSONALIDADE_SEGURA.search(frase)
        ):
            problemas.append("estado_real_sem_leitura")
            removidas.append(frase)
            continue
        mantidas.append(frase)
    ajustada = " ".join(mantidas).strip()
    if estado_atual_rejeitado:
        ajustada = (
            "Não tenho uma leitura atual desse estado para te responder com "
            "segurança."
        )
    elif capacidade_emocional_negada_rejeitada:
        ajustada = (
            "Isso é uma hipótese, não um fato. Não vou afirmar irritação sem "
            "causa observável."
            if hipotese_emocional_negada else
            "Posso expressar reações emocionais quando há causa e evidência rastreáveis."
        )
    elif emocao_sem_causa_rejeitada:
        ajustada = (
            "Você tem razão: isso não é um fato. Não vou tratar essa emoção "
            "como real sem uma causa observável."
            if hipotese_emocional_negada else
            "Não vou atribuir a mim essa emoção sem uma causa observável."
        )
    elif agendamento_rejeitado:
        ajustada = (
            "Guardei a ideia, mas não criei nem confirmei o lembrete."
            if tem_anotacao
            else "O lembrete não foi criado nem confirmado."
        )
    elif conclusao_total_rejeitada:
        ajustada = (
            "Concluí apenas a etapa confirmada; a outra etapa ainda não tem "
            "resultado confirmado."
        )
    elif "execucao_alegada_sem_resultado" in problemas:
        if any(item.get("executou") is True for item in comandos_normalizados):
            ajustada = "Eu me adiantei na fala: o comando foi enviado, mas não consegui confirmar o resultado."
        else:
            ajustada = "Eu me adiantei na fala, mas essa ação não foi executada nem confirmada."
    elif not ajustada and any(p.startswith("pessoa_condicao_") for p in problemas):
        ajustada = "Não consegui preservar a referência da condição nessa explicação."
    elif not ajustada and "compromisso_sem_continuacao" in problemas:
        ajustada = "Esse trecho não criou uma continuação executável."
    elif not ajustada and "oferta_capacidade_nao_suportada" in problemas:
        ajustada = (
            "Eu não consigo criar uma playlist dentro do Spotify por conta própria. "
            "Posso procurar ou tocar músicas usando os controles que tenho."
        )
    elif not ajustada and "oferta_acao_sem_pendencia" in problemas:
        ajustada = (
            "Eu posso sugerir essa ação, mas só digo que fiz depois que ela for "
            "estruturada, executada e confirmada de verdade."
        )
    elif not ajustada and "promessa_sem_mecanismo" in problemas:
        ajustada = (
            "Eu consigo conversar sobre isso agora, mas não acompanho novidades sozinha "
            "nem aviso depois sem criar um lembrete real."
        )
    elif not ajustada and "promessa_operacional_sem_comando" in problemas:
        if contrato.get("requer_execucao"):
            ajustada = "Eu não executei essa ação nem confirmei qualquer resultado."
        else:
            ajustada = "Entendi. Então essa parte já está resolvida por aí."
    elif not ajustada and "estado_real_sem_leitura" in problemas:
        ajustada = "Eu ainda não consultei o estado real para afirmar isso com segurança."
    return {
        "fala": ajustada or original,
        "problemas": list(dict.fromkeys(problemas)),
        "acao": "ajustada" if problemas else "aceita",
        "trechos_rejeitados": removidas,
    }
