"""Separa expressão pessoal, estado observado e promessa operacional."""

from __future__ import annotations

import re
from typing import Any, Dict

from mente_laylay.cognicao.fundamentacao_factual import (
    classificar_atualidade_factual,
)
from mente_laylay.emocoes.contrato_causal import evento_tem_causa_rastreavel
from mente_laylay.cognicao.incerteza_observacao import (
    expressa_incerteza_observacao,
    estado_sob_pedido_informacao,
    estado_sob_pergunta_referida,
)
from mente_laylay.memoria_mental.resultado_acao import normalizar_resultado_acao


_PROMESSA_SEM_MECANISMO = re.compile(
    r"\b(?:vou|posso|deixa\s+comigo\s+que\s+eu\s+vou|quer\s+que\s+eu|"
    r"voc[eê]\s+quer\s+que\s+eu)\s+"
    r"(?:te\s+)?(?:manter\s+atualizad[oa]|avisar\s+quando|acompanhar\s+(?:as\s+)?novidades|"
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
    r"(?:abert[oa]s?|fechad[oa]s?|ativ[oa]s?|rodando|em\s+execu[cç][aã]o)\b",
    re.IGNORECASE,
)
_FRONTEIRA_ORACAO_ESTADO = re.compile(
    r"[,;:!?]|\b(?:mas|por[eé]m|contudo|entretanto|no\s+entanto|e)\b",
    re.IGNORECASE,
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


def _alega_emocao_forte_da_laylay(frase: str) -> bool:
    texto = str(frase or "")
    for ocorrencia in _EMOCAO_FORTE_DA_LAYLAY.finditer(texto):
        prefixo = texto[:ocorrencia.start()]
        if re.search(
            r"\b(?:n[aã]o|nunca|jamais|nem)\s+$",
            prefixo,
            re.IGNORECASE,
        ):
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
    mantidas: list[str] = []
    removidas: list[str] = []
    oferta_dependente_removida = False
    conclusao_total_rejeitada = False
    agendamento_rejeitado = False
    emocao_sem_causa_rejeitada = False
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
    evento_causal_valido = evento_tem_causa_rastreavel(
        contrato.get("evento_emocional_causal")
        if isinstance(contrato.get("evento_emocional_causal"), dict)
        else None
    )
    hipotese_emocional_negada = bool(
        _HIPOTESE_EMOCIONAL_NEGADA.search(texto_usuario)
    )
    estado_atual_rejeitado = False
    for frase in frases:
        if (
            origem_ia
            and consulta_estado_observavel
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
            and hipotese_emocional_negada
            and not evento_causal_valido
            and _alega_emocao_forte_da_laylay(frase)
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
    elif emocao_sem_causa_rejeitada:
        ajustada = (
            "Você tem razão: isso não é um fato. Não vou tratar essa emoção "
            "como real sem uma causa observável."
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
