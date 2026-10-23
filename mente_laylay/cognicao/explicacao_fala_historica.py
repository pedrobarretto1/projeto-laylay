"""Realização limitada aos resultados vinculados a uma fala já entregue.

Não é um juiz universal de prosa. Ausência de cobertura não demonstra falsidade
do rascunho: exige uma realização verificável, sem completar causas ou etapas.
Os receipts históricos nunca entram na lista de comandos do pedido atual.
"""
from __future__ import annotations

import json
import math
import time
from typing import Any, Callable, Mapping, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from mente_laylay.memoria_mental.registro_semantico import RevisaoAlegacaoConsulta

from mente_laylay.memoria_mental.decisao_observada import (
    ExplicacaoOcorrencia, ExplicacaoHistoricaAto, ExplicacoesHistoricasPorAto, MedicaoObservada,
    avaliar_comparacoes_resultado, NaoQualificacaoMedicao, ExpectativaResultado, AvaliacaoComparacaoResultado, FontesComparacaoResultado,
)
from mente_laylay.cognicao.contratos_turno import ContratoExplicativoAto, SnapshotComandoIA


def _limite_agente(texto: str) -> tuple[str, ...] | None:
    from mente_laylay.cognicao.referencias_linguagem import agente_explicacao_causal
    agente, _ = agente_explicacao_causal(texto)
    if agente and agente != "destinatario":
        return ("Não tenho uma fonte histórica vinculada a quem realizou essa ação. "
                "Uma decisão da Laylay não prova o motivo de outra pessoa ou de um grupo.",)
    return None


def consulta_historica_multipla(turno: Mapping[str, Any], *, fonte_identificada: bool = False) -> bool:
    """Apenas elegibilidade; as fronteiras continuam sendo as do interpretador."""
    from mente_laylay.cognicao.referencias_linguagem import referencia_explicacao_historica
    segmentos = turno.get("segmentos")
    return isinstance(segmentos, list) and len(segmentos) > 1 and (fonte_identificada or any(
        referencia_explicacao_historica(str(s.get("texto_estrutural") or s.get("texto") or ""))
        for s in segmentos if isinstance(s, Mapping)))


def vincular_explicacoes_por_ato(
    texto: str, *, turno: Mapping[str, Any], mente: Mapping[str, Any],
    recuperar_ocorrencia: Callable[..., Any] | None = None,
) -> ExplicacoesHistoricasPorAto | None:
    """Consome a segmentação já decidida; não resegmenta nem concede autoridade.

    Toda consulta ao owner recebe somente a fonte textual daquele ato. Falha
    de vínculo não é reparada por recência nem pela fonte do texto inteiro.
    """
    from mente_laylay.cognicao.modalidade_turno import fontes_textuais_dos_segmentos
    from mente_laylay.cognicao.referencias_linguagem import referencia_explicacao_historica
    from mente_laylay.memoria_mental.registro_semantico import recuperar_evidencia_da_fala, vincular_revisoes_explicacao_ocorrencia

    segmentos = turno.get("segmentos")
    if (not turno.get("id") or turno.get("autoriza_execucao") is not False
            or not isinstance(segmentos, list) or not 2 <= len(segmentos) <= 8):
        return None
    fontes = fontes_textuais_dos_segmentos(texto, segmentos)
    if len(fontes) != len(segmentos):
        return None
    partes = []
    for segmento, fonte_textual in zip(segmentos, fontes):
        ato = ContratoExplicativoAto.do_segmento(segmento)
        if ato is None or ato.modalidade not in {"pergunta", "deliberacao"}:
            return None
        literal = fonte_textual.como_dict()["texto_original"]
        referencia = referencia_explicacao_historica(literal)
        ocorrencia, evidencia = None, {}
        falha_fonte = False
        if callable(recuperar_ocorrencia):
            # O owner pode reconhecer uma referência que esta leitura geral
            # não resolve. Não duplicar a gramática dele nesta composição.
            try:
                ocorrencia = recuperar_ocorrencia(literal, turno={**turno, "texto": literal, "segmentos": [segmento]})
            except Exception:
                falha_fonte = True
            if ocorrencia is not None and (type(ocorrencia) is not ExplicacaoOcorrencia
                    or ocorrencia.turno_consulta != str(turno["id"]) or ocorrencia.texto_consulta != literal):
                ocorrencia, falha_fonte = None, True
            elif ocorrencia is not None:
                ocorrencia = vincular_revisoes_explicacao_ocorrencia(mente.get("registro_semantico"),ocorrencia)
                falha_fonte = ocorrencia is None
        if referencia or ocorrencia is not None or falha_fonte:
            evidencia = recuperar_evidencia_da_fala(literal, mente) if not falha_fonte else {}
            normal = lambda s: " ".join(str(s).casefold().split())
            citacao = any(len(normal(f.get("fala", ""))) >= 8
                and normal(f.get("fala", "")) in normal(literal) for f in evidencia.get("falas", []))
            if evidencia and referencia != "outro_agente" and (citacao or (ocorrencia is None and referencia == "fala")):
                ocorrencia = None
            else:
                evidencia = {}
                if ocorrencia is None and not falha_fonte:
                    ocorrencia = ExplicacaoOcorrencia(str(turno["id"]), literal, (), "ausente")
        try:
            partes.append(ExplicacaoHistoricaAto(ato, fonte_textual, ocorrencia,
                SnapshotComandoIA(evidencia) if evidencia else None, falha_fonte))
        except (ValueError, TypeError):
            return None
    try:
        return ExplicacoesHistoricasPorAto(str(turno["id"]), texto, tuple(partes))
    except (ValueError, TypeError):
        return None


def realizacoes_explicacoes_por_ato(fonte: ExplicacoesHistoricasPorAto, *, agora: float | None = None) -> tuple[str, ...]:
    """Uma resposta conjunta, preservando a cobertura e os limites de cada parte."""
    if type(fonte) is not ExplicacoesHistoricasPorAto:
        return ()
    respostas = []
    for parte in fonte.partes:
        literal = parte.fonte_textual.como_dict()["texto_original"]
        limite_agente = _limite_agente(literal)
        if limite_agente:
            opcoes = limite_agente
        elif parte.falha_fonte:
            opcoes = ("Não tenho evidência histórica válida para explicar esta parte.",)
        elif parte.ocorrencia is not None:
            opcoes = realizacoes_explicacao_ocorrencia(parte.ocorrencia, agora=agora)
        elif parte.fala is not None:
            opcoes = realizacoes_fala_historica(parte.fala.como_dict(), agora=agora)
        else:
            # Elipse não resolvida ou pergunta de outra natureza continua
            # visível, sem inventar a herança da causa ou declarar conclusão.
            opcoes = ("Esta parte ainda não foi respondida; preciso tratá-la separadamente.",)
        if not opcoes:
            opcoes = ("Não tenho evidência histórica válida para explicar esta parte.",)
        respostas.append(f"Sobre {json.dumps(literal, ensure_ascii=False)}: {opcoes[0]}")
    return (" ".join(respostas),)


def formatar_explicacoes_por_ato(contrato: Mapping[str, Any]) -> str:
    opcoes = realizacoes_explicacoes_por_ato(contrato.get("explicacoes_historicas_por_ato"))
    return ("EXPLICAÇÃO HISTÓRICA POR ATO: cada parte tem sua própria fonte e limite. "
            "Uma fonte não cobre as outras perguntas. Copie a realização conjunta integral no campo fala "
            "do JSON, comandos=[]. Não acrescente causas, efeitos ou novas ações. REALIZAÇÕES PERMITIDAS: "
            + json.dumps(list(opcoes), ensure_ascii=False))


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
    limite_agente = _limite_agente(fonte.texto_consulta)
    if limite_agente:
        return limite_agente
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
    if fonte.revisoes_proposicoes:
        partes = proposicoes_resultado_comparado(FontesComparacaoResultado(episodio.id,
            episodio.expectativas,episodio.medicoes,episodio.iniciada_em))
        revisoes = dict(fonte.revisoes_proposicoes)
        por_chave = {p["chave"]:p for p in partes}
        if any(k not in por_chave or r.texto_original!=por_chave[k]["texto"] for k,r in revisoes.items()):
            return ()
        resultado += " " + " ".join(realizacao_revisao_alegacao(revisoes[p["chave"]])
            if p["chave"] in revisoes else p["texto"] for p in partes if p["tipo"]!="comparacao")
        resultado += " " + realizar_comparacoes_resultado(avaliar_comparacoes_resultado(episodio),
            revisoes_proposicoes=revisoes)
    else:
        if episodio.expectativas:
            resultado += " " + realizar_expectativas_resultado(episodio.expectativas)
        if episodio.medicoes:
            resultado += " " + realizar_medicoes_observadas(episodio.medicoes)
        resultado += " " + realizar_comparacoes_resultado(avaliar_comparacoes_resultado(episodio))
    if episodio.nao_qualificacoes_medicao:
        resultado += " " + realizar_nao_qualificacoes_medicao(episodio.nao_qualificacoes_medicao)
    return (f"{identificacao}, {decisao} {resultado} {episodio.limite_observacao} O estado atual é uma informação separada.",)


def realizar_expectativas_resultado(expectativas: Sequence[ExpectativaResultado]) -> str:
    """Meta prévia, sem inferir efeito nem reconstruir o pedido."""
    return " ".join(
        f"Valor solicitado de {json.dumps(e.grandeza, ensure_ascii=False)}: "
        f"{json.dumps(e.valor, allow_nan=False)} {json.dumps(e.unidade, ensure_ascii=False)}. "
        "A meta registrada não comprova que a operação foi concluída." for e in expectativas)


def proposicoes_resultado_comparado(fontes: FontesComparacaoResultado) -> tuple[dict[str, Any], ...]:
    """Proposições do owner e apoios exatos, sem analisar prosa da autora."""
    if type(fontes) is not FontesComparacaoResultado:
        return ()
    from dataclasses import asdict
    partes = []
    for i, meta in enumerate(fontes.expectativas):
        partes.append({"chave": f"meta:{i}", "tipo": "meta", "texto": realizar_expectativas_resultado((meta,)),
            "dados": asdict(meta), "apoios": ()})
    for i, medicao in enumerate(fontes.medicoes):
        partes.append({"chave": f"medicao:{i}", "tipo": "medicao", "texto": realizar_medicoes_observadas((medicao,)),
            "dados": asdict(medicao), "apoios": ()})
    for i, avaliacao in enumerate(avaliar_comparacoes_resultado(fontes)):
        comparacao = avaliacao.comparacao
        if comparacao is None:
            continue
        meta_i = next(n for n,m in enumerate(fontes.expectativas) if m is comparacao.expectativa)
        med_i = next(n for n,m in enumerate(fontes.medicoes) if m is comparacao.medicao)
        partes.append({"chave": f"comparacao:{i}", "tipo": "comparacao",
            "texto": realizar_comparacoes_resultado((avaliacao,)), "dados": asdict(comparacao),
            "apoios": (f"meta:{meta_i}", f"medicao:{med_i}")})
    return tuple(partes)


def realizar_comparacoes_resultado(
    avaliacoes: Sequence[AvaliacaoComparacaoResultado], *,
    revisoes_proposicoes: Mapping[str, RevisaoAlegacaoConsulta] | None = None,
) -> str:
    """Relata a mesma derivação e limites na história e no resultado imediato."""
    partes = []
    for i, avaliacao in enumerate(avaliacoes):
        if len(avaliacoes) > 1:
            partes.append(f"Comparação de {json.dumps(avaliacao.expectativa.grandeza, ensure_ascii=False)} "
                f"em {json.dumps(avaliacao.expectativa.unidade, ensure_ascii=False)}:")
        revisao = (revisoes_proposicoes or {}).get(f"comparacao:{i}")
        if revisao is not None:
            partes.append(realizacao_revisao_alegacao(revisao))
            continue
        comparacao = avaliacao.comparacao
        if comparacao is None:
            partes.append(_LIMITES_COMPARACAO_RESULTADO[avaliacao.estado])
            continue
        diferenca = comparacao.diferenca
        numero = format(diferenca, "f") if diferenca else "0"
        partes.append(f"Diferença aritmética (medido menos solicitado): {numero} "
            f"{json.dumps(comparacao.medicao.unidade, ensure_ascii=False)}. "
            "Esta diferença não comprova conclusão nem explica a causa do resultado.")
    return " ".join(partes)


def realizar_nao_qualificacoes_medicao(observacoes: Sequence[NaoQualificacaoMedicao]) -> str:
    """Mesmo relato de fonte e limite na história, publicação imediata e composto."""
    partes = []
    for observacao in observacoes:
        criterio = {
            "fonte_nao_correlacionada": "Não há encerramento correlacionado admitido para qualificar esta leitura.",
            "contexto_alterado": "O contexto da execução mudou; esta leitura não foi admitida para a ocorrência.",
            "valor_nao_admitido": "O valor recebido não foi admitido como número finito para a medição.",
            "criterio_da_fonte_nao_atendido": "O critério de qualificação da fonte não foi atendido.",
        }[observacao.criterio]
        relato = (f"Critério registrado de não qualificação de {json.dumps(observacao.grandeza, ensure_ascii=False)}: "
            f"{criterio}")
        if observacao.codigo:
            relato += f" O encerramento foi registrado com código {json.dumps(observacao.codigo, ensure_ascii=False)}."
        partes.append(relato + " Isso relata o critério registrado; não identifica uma causa física.")
    return " ".join(partes)


_LIMITES_COMPARACAO_RESULTADO = {
    "fontes_ausentes": "Não há valor solicitado nem medição qualificada nesta fonte para comparação.",
    "meta_ausente": "Não há valor solicitado registrado nesta fonte para comparação.",
    "medicao_ausente": "Não há medição qualificada nesta fonte para comparar com o valor solicitado.",
    "owner_distinto": "Não há medição do mesmo owner da meta para comparação.",
    "grandeza_sem_correspondencia": "Não há medição da mesma grandeza da meta para comparação.",
    "unidade_distinta": "Não há medição na mesma unidade da meta; não vou converter as unidades para comparar.",
    "referencial_meta_ausente": "A meta não tem referencial registrado para comparação.",
    "referencial_medicao_ausente": "Não há medição com o referencial da meta; há medição sem referencial registrado.",
    "referencial_distinto": "Meta e medições não têm um referencial comum registrado para comparação.",
    "medicao_ambigua": "Há mais de uma medição compatível; esta fonte não define qual usar na comparação.",
}


def realizar_medicoes_observadas(medicoes: Sequence[MedicaoObservada]) -> str:
    """Preserva valor, sinal, unidade e limite, sem certificar a fonte."""
    return " ".join(
        f"Medição registrada de {json.dumps(m.grandeza, ensure_ascii=False)}: "
        f"{json.dumps(m.valor, allow_nan=False)} {json.dumps(m.unidade, ensure_ascii=False)}. "
        f"{m.limite_observacao}" for m in medicoes
    )


def formatar_explicacao_ocorrencia(contrato: Mapping[str, Any]) -> str:
    opcoes = realizacoes_explicacao_ocorrencia(contrato.get("explicacao_ocorrencia"))
    return ("EXPLICAÇÃO HISTÓRICA VINCULADA AO OWNER: motivo, tentativa, confirmação e estado atual são distintos. "
            "Copie uma realização integral no campo fala do JSON, com comandos=[]. "
            "Sem justificativas extras, percepção inventada, novas ações ou permissão. REALIZAÇÕES PERMITIDAS: "
            + json.dumps(list(opcoes), ensure_ascii=False))


def realizacoes_fala_historica(
    evidencia: Mapping[str, Any], *, agora: float | None = None,
) -> tuple[str, ...]:
    """Projeta execução, confirmação e o escopo capturado de cada receipt.

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
        escopo = resultado.get("confirmacao_oferecida")
        if (not isinstance(identidade, str) or not identidade or identidade in identidades
            or resultado.get("origem") != "executor" or not resultado.get("intent")
            or not isinstance(alvo, str) or len(alvo) > 180
            or ("confirmacao_oferecida" in resultado and (
                type(escopo) is not str or not 0 < len(escopo) <= 80
                or escopo != escopo.strip() or not escopo.isprintable()))
            or any(v is not None and type(v) is not bool for v in (executou, confirmado))):
            return ()
        identidades.add(identidade)
        execucao = {True: "execução registrada", False: "execução não concluída", None: "execução desconhecida"}[executou]
        if executou is False and confirmado is True:
            execucao = "sem nova execução registrada"
        confirmacao = {True: "efeito confirmado", False: "efeito não confirmado", None: "confirmação desconhecida"}[confirmado]
        if escopo is not None:
            if confirmado is True and escopo == "indisponivel":
                confirmacao = "confirmação registrada"
            confirmacao += f" no escopo registrado {json.dumps(escopo, ensure_ascii=False)}"
        else:
            # Fonte legada não possui esta premissa. Catálogo/status/descrição
            # atuais não podem preencher retroativamente seu alcance.
            if confirmado is True:
                confirmacao = "confirmação registrada"
            confirmacao += ", escopo não registrado"
        etapas.append(f"etapa {indice}, alvo {json.dumps(alvo or 'não identificado', ensure_ascii=False)}: {execucao}, {confirmacao}")
    fatos = "; ".join(etapas)
    limite = "Esta fonte não informa a causa nem a etapa de processamento; também não comprova o estado atual."
    return (f"O registro daquela fala mostra: {fatos}. {limite}",
            f"Naquela ocasião: {fatos}. {limite}")


def avaliar_fala_historica(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any] | None:
    """Valida escopo e cobertura pelo owner, nunca por autoaprovação da LLM."""
    contrato = plano.get("contrato_fala")
    if isinstance(contrato, Mapping) and "revisao_alegacao" in contrato:
        return _avaliar_revisao_alegacao(fala, plano=plano)
    if not isinstance(contrato, Mapping) or not {"evidencia_fala_historica", "explicacao_ocorrencia", "explicacoes_historicas_por_ato"}.intersection(contrato):
        return None
    composta = "explicacoes_historicas_por_ato" in contrato
    decisional = "explicacao_ocorrencia" in contrato
    evidencia = (contrato.get("explicacoes_historicas_por_ato") if composta else
                 contrato.get("explicacao_ocorrencia") if decisional else contrato.get("evidencia_fala_historica"))
    vinculo_valido = bool(
        contrato.get("origem") == "mente_unica"
        and contrato.get("autoriza_execucao") is False
        and contrato.get("turno_id") == plano.get("id") and plano.get("id")
        and (evidencia.texto_consulta if (composta and type(evidencia) is ExplicacoesHistoricasPorAto)
             or (decisional and type(evidencia) is ExplicacaoOcorrencia)
             else contrato.get("texto_consulta_historica")) == plano.get("texto_usuario")
        and plano.get("autoriza_execucao") is False
        and not plano.get("requer_execucao") and not plano.get("comandos")
    )
    if composta:
        vinculo_valido = bool(vinculo_valido and type(evidencia) is ExplicacoesHistoricasPorAto
                             and evidencia.turno_consulta == str(plano.get("id")))
        opcoes = realizacoes_explicacoes_por_ato(evidencia) if vinculo_valido else ()
    elif decisional:
        vinculo_valido = bool(vinculo_valido and type(evidencia) is ExplicacaoOcorrencia
                             and evidencia.turno_consulta == str(plano.get("id")))
        opcoes = realizacoes_explicacao_ocorrencia(evidencia) if vinculo_valido else ()
    else:
        opcoes = realizacoes_fala_historica(evidencia) if vinculo_valido and isinstance(evidencia, Mapping) else ()
        if opcoes:
            opcoes = _limite_agente(str(plano.get("texto_usuario") or "")) or opcoes
    fonte_valida = bool(opcoes)
    if not opcoes:
        opcoes = ("Não tenho evidência histórica válida para explicar essas partes da pergunta." if composta else
                  "Não tenho evidência histórica válida para explicar essa ocorrência." if decisional
                  else "Não tenho evidência histórica válida para explicar essa fala.",)
    texto = " ".join(str(fala or "").split())
    # Mesma projeção de espaços para candidato e opções. O literal original
    # continua na fonte; publicação devolve a realização canônica, de forma
    # estável mesmo quando o usuário escreveu dois espaços dentro da pergunta.
    indice = next((i for i, opcao in enumerate(opcoes) if texto == " ".join(opcao.split())), None)
    coberta = indice is not None
    return {
        "fala": opcoes[indice] if coberta else opcoes[0],
        "problemas": [] if coberta else ["explicacao_historica_sem_cobertura" if fonte_valida else "evidencia_historica_invalida"],
        "acao": "aceita" if coberta else "ajustada",
        "cobertura": "realizacao_controlada_resultados_historicos" if coberta else "ausente",
        "fonte_valida": fonte_valida,
        "prova_semantica_livre": False, "autoriza_execucao": False,
    }


def montar_pacote_explicacao_historica(plano: Mapping[str, Any]) -> PacotePrompt | None:
    """Projeta a realização conferida pelo mesmo owner, sem inferência nova.

    A realização deve caber integralmente nas unidades do contrato existente.
    Fontes inválidas ou texto não representável conservam a revisão normal;
    nunca cortar a fonte, elevar limites ou usar a redação do modelo como prova.
    """
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    from mente_laylay.cognicao.suporte_autoria import segmentar_realizacao_autoral
    avaliacao = avaliar_fala_historica("", plano=plano)
    if not avaliacao or not avaliacao["fonte_valida"]:
        return None
    fala = avaliacao["fala"]
    if not segmentar_realizacao_autoral(fala):
        return None

    def validar(dados: dict[str, Any]) -> None:
        if (set(dados) != {"fala", "comandos"} or dados.get("fala") != fala
            or dados.get("comandos") != []):
            raise ValueError("realizacao_fora_da_explicacao_historica")

    codec = ContratoSaidaEstruturada("realizacao_historica_v1", "[REALIZACAO_HISTORICA]", {
        "type": "object", "additionalProperties": False, "required": ["fala", "comandos"],
        "properties": {"fala": {"type": "string", "enum": [fala]},
                       "comandos": {"type": "array", "maxItems": 0, "items": {"type": "object"}}},
    }, validar)
    return PacotePrompt(({
        "role": "system", "content": (
            "Realize somente a explicação histórica conferida pelo owner no schema. "
            "Copie a realização integral, sem completar causas, fatos ou estado atual. "
            "O campo textual será transportado na representação autoral negociada. "
            "A referência histórica não autoriza comandos nem confirma efeitos novos. "
            "A revisão do host continua obrigatória; não há prova semântica de prosa livre."),
    }, {"role": "user", "content": str(plano["texto_usuario"])}),
        contexto_fechado=True, contrato_saida=codec)


def realizacao_opcoes_proposicao(
    qualificadores: tuple[tuple[str,str,str], ...], *, sem_correspondencia: bool = False,
) -> str:
    """Opções integrais no orçamento da pendência; excesso não vira opção truncada."""
    from mente_laylay.memoria_mental.pendencia import LIMITE_CONTEUDO_PENDENCIA
    if not qualificadores:return ""
    opcoes=[]
    for _ident,metodo,referencial in qualificadores:
        campos=[]
        if metodo:campos.append('pelo método '+json.dumps(metodo,ensure_ascii=False))
        if referencial:campos.append('no referencial '+json.dumps(referencial,ensure_ascii=False))
        opcoes.append(' e '.join(campos))
    limite=('Não identifiquei uma afirmação entregue para essa referência.' if sem_correspondencia else
        'Há mais de uma afirmação possível nessa referência.')
    texto=(limite+' Qual afirmação você quer revisar? '
        +'Opções de medição: '+'; '.join(opcoes)+'. '
        +'Cite a afirmação ou seu ID se essas opções não distinguirem. '
        +'A referência não comprova fatos nem autoriza ações.')
    return texto if len(texto)<=LIMITE_CONTEUDO_PENDENCIA else ""


def realizacao_revisao_alegacao(fonte: Any) -> str:
    from mente_laylay.memoria_mental.registro_semantico import RevisaoAlegacaoConsulta, ReferenciaProposicaoPendente
    if type(fonte) is ReferenciaProposicaoPendente:
        if opcoes:=realizacao_opcoes_proposicao(fonte.qualificadores,
                sem_correspondencia=fonte.referencia=='ausente'):return opcoes
        limite = ("Há mais de uma afirmação possível nessa referência." if fonte.referencia=="ambigua" else
                  "Não identifiquei uma afirmação entregue para essa referência.")
        return (limite + " Qual afirmação você quer revisar? Cite a afirmação ou seu ID. "
                "Preciso identificar a afirmação antes de revisá-la; essa referência não comprova fatos nem autoriza ações.")
    if type(fonte) is not RevisaoAlegacaoConsulta:
        return ""
    if fonte.status in {"suporte_em_revisao", "suporte_interno_invalido"}:
        limite = ("Uma alegação declarada como fonte foi contestada ou corrigida; o suporte desta conclusão está em revisão. "
                  if fonte.status == "suporte_em_revisao" else
                  "Não consigo verificar a cadeia de fontes internas desta conclusão. ")
        return (f'A afirmação {json.dumps(fonte.texto_original, ensure_ascii=False)} precisa ser reavaliada. '
                + limite + "Não a mantenho como fato confirmado. Isso não prova que ela seja falsa nem "
                "confirma uma alternativa. A referência à fonte também não prova a inferência. "
                "A revisão não altera confirmações de ações anteriores nem autoriza repeti-las ou desfazê-las.")
    estado = "está contestada" if fonte.status == "contestado" else "foi marcada como corrigida"
    return (f'A afirmação {json.dumps(fonte.texto_original, ensure_ascii=False)} {estado} no registro. '
            "Não a mantenho como fato confirmado. Essa revisão não prova que ela seja falsa nem "
            "confirma uma alternativa; preciso de uma fonte válida para reavaliá-la. "
            "Isso não apaga os receipts de ações nem autoriza repeti-las ou desfazê-las.")


def _avaliar_revisao_alegacao(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any]:
    from mente_laylay.memoria_mental.registro_semantico import RevisaoAlegacaoConsulta, ReferenciaProposicaoPendente
    contrato = plano["contrato_fala"]
    fonte = contrato["revisao_alegacao"]
    valida = bool(type(fonte) in (RevisaoAlegacaoConsulta,ReferenciaProposicaoPendente)
        and contrato.get("origem") == "mente_unica" and contrato.get("autoriza_execucao") is False
        and str(contrato.get("turno_id")) == str(plano.get("id")) == fonte.turno_consulta
        and plano.get("id") and fonte.texto_consulta == plano.get("texto_usuario")
        and plano.get("autoriza_execucao") is False
        and not plano.get("requer_execucao") and not plano.get("comandos"))
    realizacao = realizacao_revisao_alegacao(fonte) if valida else "Não tenho uma revisão válida vinculada a esta consulta."
    # O limite de fonte inválida também precisa de conclusão estável. Aceitar
    # esse texto não valida a fonte, a proposição nem os comandos do plano.
    coberta = " ".join(str(fala or "").split()) == " ".join(realizacao.split())
    return {"fala": realizacao, "problemas": [] if coberta else [
        "revisao_alegacao_sem_cobertura" if valida else "revisao_alegacao_invalida"],
        "acao": "aceita" if coberta else "ajustada", "fonte_valida": valida,
        "cobertura": "realizacao_controlada_revisao" if coberta else "ausente",
        "prova_semantica_livre": False, "autoriza_execucao": False}


def formatar_revisao_alegacao(contrato: Mapping[str, Any]) -> str:
    realizacao = realizacao_revisao_alegacao(contrato.get("revisao_alegacao"))
    return ("REVISÃO DA ALEGAÇÃO VINCULADA À CONSULTA: fonte do registro, não prova de falsidade. "
            "Copie integralmente a realização no campo fala, com comandos=[]. Não acrescente fatos "
            "nem use uma paráfrase como prova de cobertura. REALIZAÇÃO PERMITIDA: "
            + json.dumps(realizacao, ensure_ascii=False))


def formatar_realizacoes_historicas(contrato: Mapping[str, Any]) -> str:
    evidencia = contrato.get("evidencia_fala_historica")
    opcoes = realizacoes_fala_historica(evidencia) if isinstance(evidencia, Mapping) else ()
    if opcoes:
        opcoes = _limite_agente(str(contrato.get("texto_consulta_historica") or "")) or opcoes
    return (
        "EXPLICAÇÃO HISTÓRICA COM COBERTURA LIMITADA: os dados são do turno original. "
        "Não há prova semântica de prosa livre nem causa ou processamento registrados. "
        "Selecione uma realização abaixo e copie seu texto integral no campo fala do JSON, "
        "com comandos=[]. Não acrescente explicações, observações físicas ou novos fatos. "
        "Isto não autoriza ações. REALIZAÇÕES PERMITIDAS: "
        + json.dumps(list(opcoes), ensure_ascii=False)
    )
