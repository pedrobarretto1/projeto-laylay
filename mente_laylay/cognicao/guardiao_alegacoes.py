"""Separa expressão pessoal, estado observado e promessa operacional."""

from __future__ import annotations

import re
from typing import Any, Dict

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
_PERSONALIDADE_SEGURA = re.compile(
    r"\b(?:fiquei|estou|t[oô])\s+(?:curiosa|curioso|animada|interessada)|"
    r"\b(?:acho|me\s+parece|soa|eu\s+gostaria)\b",
    re.IGNORECASE,
)
_INTENTS_AGENDAMENTO = {
    "AGENDAR_LEMBRETE", "AGENDAR_ACAO", "CREATE_REMINDER", "SCHEDULE_ACTION",
}
_INTENTS_ANOTACAO = {
    "INBOX_ADD", "INBOX_ADD_DISCUSSION",
}


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
    for frase in frases:
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
            and _PROMESSA_OPERACIONAL_SEM_COMANDO.search(frase)
            and not confirmados
        ):
            problemas.append("promessa_operacional_sem_comando")
            removidas.append(frase)
            continue
        if (
            origem_ia
            and _EXECUCAO_ALEGADA_SEM_RESULTADO.search(frase)
            and not confirmados
        ):
            problemas.append("execucao_alegada_sem_resultado")
            removidas.append(frase)
            continue
        if (
            origem_ia
            and _ESTADO_REAL_FORTE.search(frase)
            and not confirmados
            and not _PERSONALIDADE_SEGURA.search(frase)
        ):
            problemas.append("estado_real_sem_leitura")
            removidas.append(frase)
            continue
        mantidas.append(frase)
    ajustada = " ".join(mantidas).strip()
    if agendamento_rejeitado:
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
