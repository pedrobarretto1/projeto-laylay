"""Contrato único que limita decisão, execução e resposta em cada turno."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, TYPE_CHECKING

from mente_laylay.cognicao.contratos_turno import (
    ContratoDecisaoTurno, ContratoOcorrenciaTurno, ContratoPropostaPrincipal, ExtracaoRespostaIA,
    ViolacaoPropostaPrincipal,
)
from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    turno_tem_veto_execucao,
)
from mente_laylay.especialistas.capacidades import intents_registradas

if TYPE_CHECKING:
    from mente_laylay.memoria_mental.estado_compartilhado_runtime import EstadoCompartilhadoRuntime


_PROPOSTA_NAO_INFORMADA = object()
_MOTIVO_SEM_AUTORIZACAO = "turno não autorizou execução"
_MOTIVO_INTENCAO_INCOMPATIVEL = "intenção incompatível com a operação explícita"


def criar_contrato_decisao(
    turno: Dict[str, Any] | None,
    plano: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Cria a autorização inicial sem inventar uma intenção operacional."""
    leitura = dict(turno or {})
    planejamento = dict(plano or {})
    modalidade = str(
        leitura.get("modalidade_geral")
        or leitura.get("modalidade")
        or planejamento.get("modalidade")
        or "conversa"
    ).strip().lower()
    autoriza_execucao = autoriza_execucao_efetiva(leitura)
    requer_execucao = bool(planejamento.get("requer_execucao"))
    misto = bool(planejamento.get("misto")) or modalidade == "misto"
    permite_acao = bool(autoriza_execucao and requer_execucao)
    if misto and permite_acao:
        proprietario = "coordenador"
    elif permite_acao:
        proprietario = "operacional"
    else:
        proprietario = "conversa"
    return ContratoDecisaoTurno(
        turno_id=planejamento.get("id") or leitura.get("id"),
        modalidade=modalidade,
        proprietario=proprietario,
        permite_acao=permite_acao,
        permite_resposta=True,
        requer_esclarecimento=bool(leitura.get("requer_esclarecimento")),
        intencao="",
        origem_decisao="classificador_turno",
        confianca=leitura.get("confianca") or 0.0,
        status="planejada",
    ).como_dict()


def consolidar_arbitragem(
    contrato: Dict[str, Any] | None,
    arbitragem: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Anexa o vencedor real ao contrato; ausência de vencedor não autoriza ação."""
    novo = ContratoDecisaoTurno.de_mapping(contrato).como_dict()
    resultado = dict(arbitragem or {})
    decisao = resultado.get("decisao") if isinstance(resultado.get("decisao"), dict) else {}
    intent = str(decisao.get("intent") or decisao.get("acao") or "").strip().upper()
    referencia = (
        dict(resultado.get("referencia_resolvida") or {})
        if isinstance(resultado.get("referencia_resolvida"), dict)
        else {}
    )
    tem_referente = bool(str(
        referencia.get("nome")
        or referencia.get("alvo")
        or referencia.get("id")
        or ""
    ).strip())
    contexto_sem_referente = bool(
        resultado.get("depende_contexto")
        and not tem_referente
    )
    if intent:
        novo.update(
            proprietario="operacional",
            permite_acao=True,
            intencao=intent,
            origem_decisao=str(resultado.get("origem") or "arbitro"),
            confianca=round(float(resultado.get("confianca") or novo.get("confianca") or 0.0), 3),
            status="decidida",
        )
    elif contexto_sem_referente:
        # A fala pode autorizar uma operação elíptica ("continua", "maximiza"),
        # mas essa autoridade não cria o referente de que a operação depende.
        # Sem vencedor nem entidade resolvida, o único fechamento coerente é
        # pedir contexto; comandos autocontidos continuam aguardando a IA.
        novo.update(
            proprietario="conversa",
            permite_acao=False,
            requer_esclarecimento=True,
            intencao="",
            origem_decisao=str(
                resultado.get("origem") or "arbitro_contexto_sem_referente"
            ),
            status="sem_acao",
        )
    elif novo.get("permite_acao") and not list(resultado.get("rejeitados") or []):
        # Um detector que não encontrou candidato não revoga um pedido
        # explicitamente autorizado. Outro especialista ainda pode entendê-lo.
        novo.update(
            origem_decisao=str(resultado.get("origem") or "arbitro_sem_candidato"),
            status="aguardando_intencao",
        )
    else:
        novo.update(
            proprietario="conversa",
            permite_acao=False,
            intencao="",
            origem_decisao=str(resultado.get("origem") or "arbitro_sem_vencedor"),
            status="sem_acao",
        )
    return ContratoDecisaoTurno.de_mapping(novo).como_dict()


def motivo_incoerencia_contratos_turno(
    turno: Mapping[str, Any] | None,
    plano: Mapping[str, Any] | None,
    retrato: Mapping[str, Any] | None = None,
) -> str:
    """Valida correlação, sem reinterpretar a autorização ou a proposta da IA."""
    if any(valor is not None and not isinstance(valor, Mapping) for valor in (turno, plano, retrato)):
        return "contratos incoerentes: turno/plano/retrato malformado"
    leitura = dict(turno or {})
    planejamento = dict(plano or {})
    snapshot = dict(retrato or {})
    decisao = planejamento.get("decisao_turno")
    if decisao is not None and not isinstance(decisao, Mapping):
        return "contratos incoerentes: decisão do turno malformada"
    contrato = dict(decisao or {})
    valores_id = (
        leitura.get("id"), planejamento.get("id"), contrato.get("turno_id"),
        snapshot.get("id"), leitura.get("retrato_id"), planejamento.get("retrato_id"),
    )
    if any(
        valor is not None and (isinstance(valor, bool) or not isinstance(valor, (int, str)))
        for valor in valores_id
    ):
        return "contratos incoerentes: identidade de turno/plano/retrato malformada"
    ids = [
        str(valor).strip() if valor is not None else ""
        for valor in valores_id
    ]
    # Uma lista legada de intents sem identidade não representa um retrato
    # canônico. Referências/metadados modernos exigem o vínculo completo;
    # perder um campo nesse caminho não permite retornar ao contrato legado.
    moderno = bool(
        ids[4] or ids[5]
        or any(chave in snapshot for chave in ("id", "texto", "ts", "modalidade"))
    )
    if moderno and not all(ids):
        return "contratos incoerentes: identidade de turno/plano/retrato incompleta"
    if len({valor for valor in ids if valor}) > 1:
        return "contratos incoerentes: IDs de turno/plano/retrato divergentes"
    if moderno and any(
        valor is not None and not isinstance(valor, str)
        for valor in (
            leitura.get("texto"), leitura.get("texto_original"),
            planejamento.get("texto_usuario"), snapshot.get("texto"),
            leitura.get("texto_operacional_efetivo"),
            planejamento.get("texto_operacional_efetivo"),
        )
    ):
        return "contratos incoerentes: texto de turno/plano/retrato malformado"

    def texto_canonico(valor: Any) -> str:
        # Plano e retrato publicam somente os primeiros 500 caracteres.
        return str(valor or "").strip()[:500]

    original_turno = texto_canonico(leitura.get("texto_original") or leitura.get("texto"))
    original_plano = texto_canonico(planejamento.get("texto_usuario"))
    texto_retrato = texto_canonico(snapshot.get("texto"))
    if moderno and not all((original_turno, original_plano, texto_retrato)):
        return "contratos incoerentes: texto de turno/plano/retrato incompleto"
    originais = (
        original_turno, original_plano, texto_canonico(leitura.get("texto")),
    )
    if len({valor for valor in originais if valor}) > 1:
        return "contratos incoerentes: fala original de turno/plano divergente"
    if moderno:
        # A revisão mantém a fala original no plano e a proposta final no
        # retrato. Comparar a visão operacional evita reintroduzir o pedido
        # descartado ou bloquear uma revisão legítima.
        operacional_turno = (
            texto_canonico(leitura["texto_operacional_efetivo"])
            if "texto_operacional_efetivo" in leitura else original_turno
        )
        operacional_plano = (
            texto_canonico(planejamento["texto_operacional_efetivo"])
            if "texto_operacional_efetivo" in planejamento else original_plano
        )
        if not operacional_turno or not operacional_plano:
            return "contratos incoerentes: texto operacional incompleto"
        if len({operacional_turno, operacional_plano, texto_retrato}) > 1:
            return "contratos incoerentes: texto operacional de turno/plano/retrato divergente"
    return ""


def motivo_divergencia_ocorrencia_principal(
    proposta: ContratoPropostaPrincipal | None,
    *,
    turno: Mapping[str, Any] | None,
    plano: Mapping[str, Any] | None,
    retrato: Mapping[str, Any] | None,
) -> str:
    """Confere a ocorrência capturada, inclusive quando o modelo falhou."""
    incoerencia = motivo_incoerencia_contratos_turno(turno, plano, retrato)
    if incoerencia:
        return incoerencia
    if not isinstance(proposta, ContratoPropostaPrincipal):
        return "proposta principal ausente ou malformada"
    return _motivo_divergencia_identidade_ocorrencia(
        proposta.turno_id, proposta.texto_usuario,
        turno=turno, plano=plano, retrato=retrato, origem="proposta principal",
    )


def motivo_divergencia_ocorrencia_turno(
    ocorrencia: ContratoOcorrenciaTurno | None,
    *,
    turno: Mapping[str, Any] | None,
    plano: Mapping[str, Any] | None,
    retrato: Mapping[str, Any] | None,
) -> str:
    """Confere a origem de uma conclusão sem conferir autorização."""
    incoerencia = motivo_incoerencia_contratos_turno(turno, plano, retrato)
    if incoerencia:
        return incoerencia
    if not isinstance(ocorrencia, ContratoOcorrenciaTurno):
        return "ocorrência do turno ausente ou malformada"
    return _motivo_divergencia_identidade_ocorrencia(
        ocorrencia.turno_id, ocorrencia.texto_usuario,
        turno=turno, plano=plano, retrato=retrato, origem="conclusão do turno",
    )


def _motivo_divergencia_identidade_ocorrencia(
    turno_id: str,
    texto_usuario: str,
    *,
    turno: Mapping[str, Any] | None,
    plano: Mapping[str, Any] | None,
    retrato: Mapping[str, Any] | None,
    origem: str,
) -> str:
    leitura, planejamento, snapshot = dict(turno or {}), dict(plano or {}), dict(retrato or {})
    decisao = dict(planejamento.get("decisao_turno") or {})
    ids = (
        leitura.get("id"), planejamento.get("id"), decisao.get("turno_id"),
        snapshot.get("id"), leitura.get("retrato_id"), planejamento.get("retrato_id"),
    )
    if not all(valor is not None and str(valor).strip() for valor in ids):
        return f"{origem} sem frame identificado de turno/plano/retrato"
    if str(leitura.get("id")).strip() != turno_id:
        return f"{origem} pertence a outra ocorrência de turno"
    # A fonte conserva a fala original completa. Os produtores públicos
    # limitam seus textos a 500 caracteres; a revisão fica somente no retrato.
    # Esse vínculo não certifica sufixos nem parâmetros fora dessa projeção.
    def projecao(valor: Any) -> str:
        return str(valor or "").strip()[:500].rstrip()

    original = projecao(leitura.get("texto_original") or leitura.get("texto"))
    texto_plano = projecao(planejamento.get("texto_usuario"))
    if not original or not texto_plano or projecao(texto_usuario) != original or original != texto_plano:
        return f"texto da {origem} diverge da fala original do turno/plano"
    return ""


def motivo_incoerencia_proposta_principal(
    proposta: ContratoPropostaPrincipal | None,
    *,
    turno: Mapping[str, Any] | None,
    plano: Mapping[str, Any] | None,
    retrato: Mapping[str, Any] | None,
) -> str:
    """Vincula a emissão conhecida, sem provar culpa ou efeito."""
    motivo = motivo_divergencia_ocorrencia_principal(
        proposta, turno=turno, plano=plano, retrato=retrato,
    )
    if motivo:
        return motivo
    if not proposta.proveniencia_conhecida:
        return "proposta principal sem procedência suficiente"
    return ""


def filtrar_comandos_pelo_turno(
    comandos: Iterable[Dict[str, Any]] | None,
    *,
    turno: Dict[str, Any] | None,
    plano: Dict[str, Any] | None,
    retrato: Dict[str, Any] | None = None,
    proposta_principal: Any = _PROPOSTA_NAO_INFORMADA,
) -> Dict[str, Any]:
    """Impede que comandos inventados pela resposta da IA escapem do árbitro."""
    candidatos = [dict(item) for item in (comandos or ()) if isinstance(item, dict)]
    leitura = dict(turno or {})
    planejamento = dict(plano or {})
    snapshot = dict(retrato or {})
    decisao = planejamento.get("decisao_turno")
    contrato = dict(decisao) if isinstance(decisao, Mapping) else {}
    incoerencia = motivo_incoerencia_contratos_turno(leitura, planejamento, snapshot)
    com_procedencia = proposta_principal is not _PROPOSTA_NAO_INFORMADA
    if com_procedencia:
        divergencia_ocorrencia = incoerencia or motivo_divergencia_ocorrencia_principal(
            proposta_principal, turno=leitura, plano=planejamento, retrato=snapshot,
        )
        incoerencia = divergencia_ocorrencia or motivo_incoerencia_proposta_principal(
            proposta_principal, turno=leitura, plano=planejamento, retrato=snapshot,
        )
    autoriza = bool(
        not incoerencia
        and autoriza_execucao_efetiva(leitura)
        and planejamento.get("requer_execucao")
        and contrato.get("permite_acao", True)
    )
    veto_execucao = turno_tem_veto_execucao(leitura)
    permitidos = {str(item).strip().upper() for item in snapshot.get("intents_permitidos") or ()}
    aceitos: list[Dict[str, Any]] = []
    rejeitados: list[Dict[str, Any]] = []
    for comando in candidatos:
        intent = str(comando.get("intent") or comando.get("acao") or "").strip().upper()
        if incoerencia:
            motivo = incoerencia
        elif not autoriza:
            motivo = _MOTIVO_SEM_AUTORIZACAO
        elif not intent:
            motivo = "comando sem intenção"
        elif permitidos and intent not in permitidos:
            motivo = _MOTIVO_INTENCAO_INCOMPATIVEL
        else:
            aceitos.append(comando)
            continue
        rejeitados.append({"intent": intent, "motivo": motivo})
    resultado = {
        "comandos": aceitos,
        "rejeitados": rejeitados,
        "autoriza_execucao": autoriza,
        "proprietario": str(contrato.get("proprietario") or "conversa"),
        "veto_execucao_operacional": veto_execucao,
    }
    if com_procedencia:
        # Correlação não concede autorização e não transforma rejeição em culpa.
        resultado["proposta_vinculada"] = not bool(incoerencia)
        resultado["ocorrencia_vinculada"] = not bool(divergencia_ocorrencia)
    return resultado


def avaliar_violacoes_proposta_original(
    proposta: ContratoPropostaPrincipal | None,
    extracao: ExtracaoRespostaIA | None,
    *,
    turno: Mapping[str, Any],
    plano: Mapping[str, Any],
    retrato: Mapping[str, Any],
) -> tuple[ViolacaoPropostaPrincipal, ...]:
    """Compara a fonte preservada ao contrato atual usando o filtro canônico.

    Ausência de prova não afirma que o candidato está correto. As coerções
    compatíveis com extensões legadas não certificam esta evidência forte.
    """
    if (
        motivo_incoerencia_proposta_principal(proposta, turno=turno, plano=plano, retrato=retrato)
        or not isinstance(extracao, ExtracaoRespostaIA)
        or extracao.resposta_bruta != proposta.resposta_bruta
        or not extracao.proposta_operacional_explicita
        or not extracao.candidatos_preservados
        or not extracao.normalizacao_completa
    ):
        return ()
    decisao = plano.get("decisao_turno")
    if not isinstance(decisao, Mapping):
        return ()
    flags = (
        turno.get("autoriza_execucao"), turno.get("veto_execucao_operacional"),
        plano.get("requer_execucao"), decisao.get("permite_acao"),
    )
    if not all(isinstance(valor, bool) for valor in flags):
        return ()
    autoriza, veto, requer, permite = flags
    proprietario = decisao.get("proprietario")
    if not isinstance(proprietario, str) or decisao.get("origem_decisao") != "classificador_turno":
        return ()
    # Um veto inequívoco e um contrato positivo delimitado são duas provas
    # possíveis. Estados contraditórios ou simplesmente incompletos suspendem.
    veto_demonstrado = not autoriza and veto and not requer and not permite and proprietario == "conversa"
    positivo_demonstrado = autoriza and not veto and requer and permite and proprietario in {"operacional", "coordenador"}
    if not veto_demonstrado and not positivo_demonstrado:
        return ()
    operacao = retrato.get("operacao_explicita")
    permitidos = retrato.get("intents_permitidos")
    catalogo = intents_registradas()
    restricao_bem_formada = (
        isinstance(operacao, str) and isinstance(permitidos, (list, tuple))
        and all(isinstance(item, str) and item and item == item.strip().upper() for item in permitidos)
    )
    if not restricao_bem_formada:
        return ()
    restricao_delimitada = bool(operacao.strip() and permitidos and all(item in catalogo for item in permitidos))
    if positivo_demonstrado and not restricao_delimitada:
        return ()
    candidatos = [snapshot.como_dict() for snapshot in extracao.comandos_normalizados]
    if not all(
        isinstance(item.get("intent"), str) and item["intent"] in catalogo
        and isinstance(item.get("params"), dict) for item in candidatos
    ):
        return ()
    provas = []
    for indice, comando in enumerate(candidatos):
        # Mesmos dados e mesma decisão do filtro executável; não reclassificar
        # a fala nem usar a lista reparada para atribuir o erro original.
        resultado = filtrar_comandos_pelo_turno(
            [comando], turno=dict(turno), plano=dict(plano), retrato=dict(retrato),
            proposta_principal=proposta,
        )
        rejeitados = resultado["rejeitados"]
        motivo = rejeitados[0]["motivo"] if rejeitados else ""
        if not (
            (motivo == _MOTIVO_SEM_AUTORIZACAO and veto_demonstrado)
            or (motivo == _MOTIVO_INTENCAO_INCOMPATIVEL and positivo_demonstrado and restricao_delimitada)
        ):
            continue
        provas.append(ViolacaoPropostaPrincipal(
            turno_id=proposta.turno_id, indice_comando=indice,
            intent=comando["intent"], motivo=motivo, proprietario=proprietario,
            operacao_explicita=operacao if isinstance(operacao, str) else "",
        ))
    return tuple(provas)


class ValidadorComandosTurnoRuntime:
    """Lê um frame isolado do estado real e reutiliza o filtro canônico."""

    def __init__(self, *, estado_runtime: EstadoCompartilhadoRuntime) -> None:
        self._estado_runtime = estado_runtime

    def __call__(self, comandos: Iterable[Dict[str, Any]] | None) -> Dict[str, Any]:
        return self._validar(comandos)

    def validar_proposta(
        self, comandos: Iterable[Dict[str, Any]] | None,
        proposta_principal: ContratoPropostaPrincipal | None,
    ) -> Dict[str, Any]:
        return self._validar(comandos, proposta_principal=proposta_principal)

    def _validar(
        self, comandos: Iterable[Dict[str, Any]] | None,
        *, proposta_principal: Any = _PROPOSTA_NAO_INFORMADA,
        extracao_original: Any = _PROPOSTA_NAO_INFORMADA,
    ) -> Dict[str, Any]:
        mental = self._estado_runtime.snapshot()["mental"]
        turno = mental.get("turno_atual") or {}
        plano = mental.get("plano_turno_atual") or {}
        retrato = mental.get("retrato_turno_atual") or {}
        resultado = filtrar_comandos_pelo_turno(
            comandos, turno=turno, plano=plano,
            retrato=retrato, proposta_principal=proposta_principal,
        )
        if extracao_original is not _PROPOSTA_NAO_INFORMADA:
            resultado["violacoes_proposta_original"] = avaliar_violacoes_proposta_original(
                proposta_principal, extracao_original, turno=turno, plano=plano, retrato=retrato,
            )
        return resultado

    def validar_proposta_original(
        self, comandos: Iterable[Dict[str, Any]] | None,
        proposta_principal: ContratoPropostaPrincipal | None,
        extracao_original: ExtracaoRespostaIA | None,
    ) -> Dict[str, Any]:
        return self._validar(
            comandos, proposta_principal=proposta_principal,
            extracao_original=extracao_original,
        )


def criar_validador_comandos_turno_runtime(
    *, estado_runtime: EstadoCompartilhadoRuntime,
) -> ValidadorComandosTurnoRuntime:
    return ValidadorComandosTurnoRuntime(estado_runtime=estado_runtime)
