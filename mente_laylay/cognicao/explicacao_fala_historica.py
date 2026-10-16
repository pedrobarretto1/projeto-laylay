"""Realização limitada aos resultados vinculados a uma fala já entregue.

Não é um juiz universal de prosa. Ausência de cobertura não demonstra falsidade
do rascunho: exige uma realização verificável, sem completar causas ou etapas.
Os receipts históricos nunca entram na lista de comandos do pedido atual.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, Mapping

from mente_laylay.memoria_mental.decisao_observada import ExplicacaoOcorrencia


def realizacoes_explicacao_ocorrencia(fonte: ExplicacaoOcorrencia, *, agora: float | None = None) -> tuple[str, ...]:
    """Mesma admissão compartilhada para decisões de qualquer owner.

    Não tenta certificar prosa livre por palavras presentes ou ausentes. O motivo
    é relato da regra registrada; não comprova causa externa nem experiência.
    """
    if type(fonte) is not ExplicacaoOcorrencia:
        return ()
    instante = time.time() if agora is None else agora
    if (type(instante) not in (int, float) or not math.isfinite(instante)
            or any(not 0 <= instante - e.encerrada_em <= 900 for e in fonte.episodios)):
        return ()
    if fonte.referencia == "ausente":
        return ("Não tenho uma ocorrência histórica identificada para explicar esse motivo; isso não prova que a ação não aconteceu. Qual fala ou ação você quer que eu explique?",)
    if fonte.referencia == "ambigua":
        return ("Há mais de uma ocorrência possível; de qual delas você está falando?",)
    episodio = fonte.episodios[0]
    identificacao = f"Na ocorrência {json.dumps(episodio.nome.replace('_', ' '), ensure_ascii=False)}"
    d = episodio.decisao
    if d is not None and episodio.justificativa_registrada:
        motivo = json.dumps(d.motivo.replace("_", " "), ensure_ascii=False)
        decisao = f"a decisão anterior registrou o motivo {motivo}. Isso relata a regra usada, sem comprovar uma causa externa."
    else:
        decisao = "o motivo da escolha não foi registrado nesta fonte; não vou reconstruí-lo pelo resultado ou pelo estado atual."
    confirmacao = {True: "confirmação registrada", False: "sem confirmação", None: "confirmação desconhecida"}[episodio.confirmado]
    resultado = f"Há tentativa registrada, {confirmacao} no escopo {json.dumps(episodio.escopo_confirmacao, ensure_ascii=False)}."
    return (f"{identificacao}, {decisao} {resultado} {episodio.limite_observacao} O estado atual é uma informação separada.",)


def formatar_explicacao_ocorrencia(contrato: Mapping[str, Any]) -> str:
    opcoes = realizacoes_explicacao_ocorrencia(contrato.get("explicacao_ocorrencia"))
    return ("EXPLICAÇÃO HISTÓRICA VINCULADA AO OWNER: motivo, tentativa, confirmação e estado atual são distintos. "
            "Copie uma realização integral no campo fala do JSON, com comandos=[]. "
            "Sem justificativas extras, percepção inventada, novas ações ou permissão. REALIZAÇÕES PERMITIDAS: "
            + json.dumps(list(opcoes), ensure_ascii=False))


def realizacoes_fala_historica(
    evidencia: Mapping[str, Any], *, agora: float | None = None,
) -> tuple[str, ...]:
    """Projeta apenas os três valores de execução/confirmação de cada receipt.

    Status, texto, critério de confirmação e IDs opacos não provam causa,
    processamento ou observação física. Não reinterpretar esses campos.
    """
    instante = time.time() if agora is None else agora
    if (type(instante) not in (int, float) or not math.isfinite(instante)
        or evidencia.get("autoriza_execucao") is not False):
        return ()
    falas = evidencia.get("falas")
    if not isinstance(falas, list) or not 1 <= len(falas) <= 2:
        return ()
    for fala in falas:
        if not isinstance(fala, Mapping):
            return ()
        ts = fala.get("ts")
        if (type(ts) not in (int, float) or not math.isfinite(ts)
            or not 0 <= instante - ts <= 900 or not fala.get("id")
            or not fala.get("turno_id") or not fala.get("fala")
            or fala.get("autoriza_execucao") is not False
            or not isinstance(fala.get("canais"), list) or not fala["canais"]
            or any(c not in {"texto_publicado", "audio_reproducao_confirmada"} for c in fala["canais"])):
            return ()
    if evidencia.get("referencia_ambigua") is True and len(falas) > 1:
        return ("Essa fala está ligada a mais de uma ocorrência; de qual delas você está falando?",)
    if evidencia.get("referencia_ambigua") is not False or len(falas) != 1:
        return ()
    resultados = falas[0].get("resultados")
    if not isinstance(resultados, list) or len(resultados) > 16:
        return ()
    if not resultados:
        return ("Essa fala foi entregue, mas não tem resultado operacional vinculado nesta fonte; "
                "isso não prova que uma ação aconteceu nem que deixou de acontecer.",)
    etapas = []
    identidades = set()
    for indice, resultado in enumerate(resultados, 1):
        if not isinstance(resultado, Mapping):
            return ()
        identidade = resultado.get("id_solicitacao")
        alvo = resultado.get("alvo")
        executou, confirmado = resultado.get("executou"), resultado.get("confirmado")
        if (not isinstance(identidade, str) or not identidade or identidade in identidades
            or resultado.get("origem") != "executor" or not resultado.get("intent")
            or not isinstance(alvo, str) or len(alvo) > 180
            or any(v is not None and type(v) is not bool for v in (executou, confirmado))):
            return ()
        identidades.add(identidade)
        execucao = {True: "execução registrada", False: "execução não concluída", None: "execução desconhecida"}[executou]
        if executou is False and confirmado is True:
            execucao = "sem nova execução registrada"
        confirmacao = {True: "efeito confirmado", False: "efeito não confirmado", None: "confirmação desconhecida"}[confirmado]
        etapas.append(f"etapa {indice}, alvo {json.dumps(alvo or 'não identificado', ensure_ascii=False)}: {execucao}, {confirmacao}")
    fatos = "; ".join(etapas)
    limite = "Esta fonte não informa a causa nem a etapa de processamento; também não comprova o estado atual."
    return (f"O registro daquela fala mostra: {fatos}. {limite}",
            f"Naquela ocasião: {fatos}. {limite}")


def avaliar_fala_historica(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    """Valida escopo e cobertura pelo owner, nunca por autoaprovação da LLM."""
    contrato = plano.get("contrato_fala")
    if not isinstance(contrato, Mapping) or not {"evidencia_fala_historica", "explicacao_ocorrencia"}.intersection(contrato):
        return None
    decisional = "explicacao_ocorrencia" in contrato
    evidencia = contrato.get("explicacao_ocorrencia") if decisional else contrato.get("evidencia_fala_historica")
    vinculo_valido = bool(
        contrato.get("origem") == "mente_unica"
        and contrato.get("autoriza_execucao") is False
        and contrato.get("turno_id") == plano.get("id") and plano.get("id")
        and (evidencia.texto_consulta if decisional and type(evidencia) is ExplicacaoOcorrencia
             else contrato.get("texto_consulta_historica")) == plano.get("texto_usuario")
        and plano.get("autoriza_execucao") is False
        and not plano.get("requer_execucao") and not plano.get("comandos")
    )
    if decisional:
        vinculo_valido = bool(vinculo_valido and type(evidencia) is ExplicacaoOcorrencia
                             and evidencia.turno_consulta == str(plano.get("id")))
        opcoes = realizacoes_explicacao_ocorrencia(evidencia) if vinculo_valido else ()
    else:
        opcoes = realizacoes_fala_historica(evidencia) if vinculo_valido and isinstance(evidencia, Mapping) else ()
    fonte_valida = bool(opcoes)
    if not opcoes:
        opcoes = ("Não tenho evidência histórica válida para explicar essa ocorrência." if decisional
                  else "Não tenho evidência histórica válida para explicar essa fala.",)
    texto = " ".join(str(fala or "").split())
    coberta = texto in opcoes
    return {
        "fala": texto if coberta else opcoes[0],
        "problemas": [] if coberta else ["explicacao_historica_sem_cobertura" if fonte_valida else "evidencia_historica_invalida"],
        "acao": "aceita" if coberta else "ajustada",
        "cobertura": "realizacao_controlada_resultados_historicos" if coberta else "ausente",
        "fonte_valida": fonte_valida,
        "prova_semantica_livre": False, "autoriza_execucao": False,
    }


def formatar_realizacoes_historicas(contrato: Mapping[str, Any]) -> str:
    evidencia = contrato.get("evidencia_fala_historica")
    opcoes = realizacoes_fala_historica(evidencia) if isinstance(evidencia, Mapping) else ()
    return (
        "EXPLICAÇÃO HISTÓRICA COM COBERTURA LIMITADA: os dados são do turno original. "
        "Não há prova semântica de prosa livre nem causa ou processamento registrados. "
        "Selecione uma realização abaixo e copie seu texto integral no campo fala do JSON, "
        "com comandos=[]. Não acrescente explicações, observações físicas ou novos fatos. "
        "Isto não autoriza ações. REALIZAÇÕES PERMITIDAS: "
        + json.dumps(list(opcoes), ensure_ascii=False)
    )
