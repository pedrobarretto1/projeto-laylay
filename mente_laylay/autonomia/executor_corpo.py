"""Executa pedidos corporais autorizados, sem afirmar locomoção observada."""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.cognicao.modalidade_turno import autoriza_execucao_efetiva
from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.memoria_mental.resultado_acao import AspectoResultado, ResultadoAcao
from mente_laylay.memoria_mental.decisao_observada import FontesComparacaoResultado, FalhaExecucaoComFontes
from mente_laylay.memoria_mental.experiencia_corporal_runtime import medicoes_rotacao_observadas, nao_qualificacoes_rotacao_observadas


@dataclass(frozen=True, slots=True)
class DependenciasExecutorCorpo:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]
    id_solicitacao: str = ""


def _movimento_corresponde(proposto: dict[str, Any], autorizado: dict[str, Any]) -> bool:
    return all(chave not in proposto or (type(proposto[chave]) is type(autorizado.get(chave))
                                        and proposto[chave] == autorizado.get(chave))
               for chave in ("direcao", "pwm", "duracao_ms", "angulo_graus"))


def fala_impedimento_movimento(resultado: ResultadoAcao) -> str:
    """Realiza somente impedimentos emitidos pelo executor para esta ação."""
    if (resultado.intent != "CORPO_MOVER" or resultado.origem != "executor"
            or resultado.status != "nao_executado_por_politica" or resultado.executou is not False):
        return ""
    receipt = resultado.contexto.get("receipt_corpo") or {}
    if receipt.get("motivo") == "lado_nao_informado":
        return "Quer que eu gire para a esquerda ou para a direita?"
    limite = receipt.get("duracao_maxima_ms")
    if receipt.get("motivo") == "duracao_corporal_fora_do_limite" and type(limite) is int:
        return f"Neste perfil, cada movimento precisa durar entre 50 e {limite} milissegundos. Não executei esse movimento."
    return ""


def executar_intencao_corpo(intent: str, params: dict[str, Any], texto_original: str,
                            ctx: dict[str, Any], deps: DependenciasExecutorCorpo) -> ResultadoDespacho:
    if intent not in {"CORPO_MOVER", "CORPO_PARAR", "CORPO_COMPANHIA"}:
        return ResultadoDespacho.nao_tratado()
    fontes = None

    def concluir(status: str, *, ok: bool, detalhe: str, fala: str, receipt: dict[str, Any] | None = None) -> ResultadoDespacho:
        executou = ok or (receipt or {}).get("aplicacao_pwm_confirmada") is True
        aspectos = ()
        if status == "falha_execucao" and receipt is not None and deps.id_solicitacao:
            # O executor adapta campos observados; o verbalizador compartilhado
            # não conhece protocolo corporal nem infere aspectos pelo texto.
            aspectos = tuple(AspectoResultado(deps.id_solicitacao, escopo, receipt[chave],
                f"receipt_corpo.{chave}") for chave, escopo in (
                    ("aplicacao_pwm_confirmada", "comando elétrico dos motores"),
                    ("parada_confirmada", "parada elétrica")) if type(receipt.get(chave)) is bool)
        deps.marcar_resultado(status, executou=executou, confirmado=ok, detalhe=detalhe,
            alvo_resolvido="corpo", params_resolvidos=params,
            contexto_resultado={"receipt_corpo": dict(receipt or {}), "prova_deslocamento": False},
            evidencia_confirmacao=str((receipt or {}).get("evidencia") or ""), aspectos=aspectos,
            medicoes=medicoes_rotacao_observadas(receipt or {}, ocorrencia_id=deps.id_solicitacao),
            nao_qualificacoes_medicao=nao_qualificacoes_rotacao_observadas(receipt or {}, ocorrencia_id=deps.id_solicitacao),
            expectativas=tuple(replace(e, ocorrencia_id=deps.id_solicitacao) for e in fontes.expectativas)
                if fontes is not None and deps.id_solicitacao else (),
            inicio_execucao=fontes.iniciada_em if fontes is not None else None,
            fontes_ocorrencia=fontes if fontes is not None and deps.id_solicitacao else None)
        deps.falar_por_status(status, fala, alvo="corpo", executou=executou, confirmado=ok, detalhe=detalhe)
        return ResultadoDespacho.concluido(ok)

    turno = ctx.get("turno_atual") or {}
    candidato = detectar_intencao_corpo(texto_original)
    # O ciclo conserva a fala composta inteira na autoria do resultado. As
    # ordens corporais podem vir dos átomos já autorizados pelo mesmo turno;
    # não dividimos a linguagem outra vez nem promovemos o auth agregado.
    if not candidato:
        candidatos = []
        for segmento in turno.get("segmentos") or ():
            if not isinstance(segmento, dict) or not autoriza_execucao_efetiva(segmento):
                continue
            parte = detectar_intencao_corpo(str(segmento.get("texto") or ""))
            if parte and parte["intent"] == intent:
                candidatos.append(parte)
        correspondentes = [parte for parte in candidatos if intent == "CORPO_PARAR"
                           or (intent == "CORPO_COMPANHIA" and parte["params"].get("acao") == params.get("acao"))
                           or (intent == "CORPO_MOVER" and _movimento_corresponde(params, parte["params"]))]
        if correspondentes and all(parte == correspondentes[0] for parte in correspondentes):
            candidato = correspondentes[0]
    resolver_repeticao = ctx.get("_resolver_repeticao_ultima_acao")
    repeticao = resolver_repeticao(texto_original) if callable(resolver_repeticao) and not candidato else None
    repeticao_valida = bool(isinstance(repeticao, dict) and repeticao.get("intent") == intent
                            and repeticao.get("params") == params)
    if (not autoriza_execucao_efetiva(turno)
            or str(turno.get("texto") or "").strip().casefold() != texto_original.strip().casefold()
            or (not candidato and not repeticao_valida)
            or (candidato and candidato["intent"] != intent)):
        return concluir("bloqueado_sem_autorizacao", ok=False, detalhe="o turno não autorizou este pedido corporal",
                        fala="Preciso de um pedido atual de movimento ou parada para acionar o corpo.")
    if candidato and intent == "CORPO_MOVER":
        if not _movimento_corresponde(params, candidato["params"]):
            return concluir("bloqueado_alvo_divergente", ok=False, detalhe="parâmetros diferem da fala autorizadora",
                            fala="O movimento proposto não corresponde ao que você pediu.")
        # Campos omitidos por uma proposta não descartam parâmetros da fala.
        params = candidato["params"]
        if not params["direcao"]:
            return concluir("nao_executado_por_politica", ok=False, detalhe="lado do giro não especificado",
                            fala="Quer que eu gire para a esquerda ou para a direita?",
                            receipt={"motivo": "lado_nao_informado"})
    if intent == "CORPO_COMPANHIA" and (not candidato or params != candidato["params"]):
        return concluir("bloqueado_sem_autorizacao", ok=False, detalhe="concessão difere do pedido atual",
                        fala="Ative o modo companhia na bancada ou na área delimitada para permitir os gestos.")
    corpo = ctx.get("_corpo_motor_runtime")
    if not callable(getattr(corpo, "executar", None)):
        return concluir("indisponivel", ok=False, detalhe="runtime corporal ausente",
                        fala="O controle dos motores está indisponível agora.")
    try:
        concessao_turno = turno
        if intent == "CORPO_COMPANHIA" and not detectar_intencao_corpo(str(turno.get("texto") or "")):
            concessao_turno = next((s for s in turno.get("segmentos") or ()
                if isinstance(s, dict) and autoriza_execucao_efetiva(s)
                and detectar_intencao_corpo(str(s.get("texto") or "")) == candidato), {})
        receipt = corpo.executar(intent, params, autorizacao=concessao_turno) if intent == "CORPO_COMPANHIA" else corpo.executar(intent, params)
        receipt = dict(receipt)
        captura = receipt.pop("_fontes_resultado", None)
        fontes = captura if type(captura) is FontesComparacaoResultado else None
    except Exception as erro:
        if type(erro) is FalhaExecucaoComFontes:
            fontes = erro.fontes
            erro = erro.__cause__ if isinstance(erro.__cause__, Exception) else erro
        return concluir("falha_execucao", ok=False, detalhe=f"executor corporal: {type(erro).__name__}",
                        fala="O controle do corpo falhou. Não consegui confirmar a execução.")
    if receipt.get("ok") is not True:
        if receipt.get("motivo") == "duracao_corporal_fora_do_limite":
            limite = receipt["duracao_maxima_ms"]
            return concluir("nao_executado_por_politica", ok=False,
                            detalhe=f"duração solicitada: {params['duracao_ms']} ms; limite neste perfil: {limite} ms",
                            fala=f"Neste perfil, cada movimento precisa durar entre 50 e {limite} milissegundos. Não executei esse movimento.",
                            receipt=receipt)
        if intent == "CORPO_COMPANHIA":
            return concluir("falha_execucao", ok=False, detalhe=str(receipt.get("motivo") or "modo indisponível"),
                            fala="Não consegui confirmar o modo companhia. Preciso do corpo conectado pela USB e pronto.", receipt=receipt)
        if receipt.get("cancelado") is True or receipt.get("status") == "cancelado":
            fala = "Interrompi o pulso. A ponte confirmou a parada." if receipt.get("parada_confirmada") is True else "Interrompi o pedido de movimento, mas a ponte não confirmou a parada."
            return concluir("cancelado", ok=False, detalhe="pulso interrompido por parada solicitada", fala=fala, receipt=receipt)
        return concluir("falha_execucao", ok=False, detalhe=str(receipt.get("motivo") or "receipt incompleto"),
                        fala="Não consegui confirmar o comando dos motores e a parada da ponte.", receipt=receipt)
    fala = "A ponte confirmou os motores desenergizados."
    if intent == "CORPO_COMPANHIA":
        fala = ("Ativei o modo companhia nesta sessão USB, sem encerrar por tempo ou contagem de gestos. "
                "Vou reagir com o corpo na bancada; parar os motores ou dar um movimento manual desativa esse modo."
                if params.get("acao") == "ativar" else "Desativei os gestos por iniciativa e a ponte confirmou a parada.")
        if receipt.get("passeio_ativado") is True:
            fala = ("Ativei o passeio nesta sessão USB. Vou intercalar avanços, recuos e giros na área com barreiras, "
                    "reagir às emoções e comemorar ações confirmadas. Diga 'pare os motores' para interromper.")
        return concluir("companhia_ativada" if params.get("acao") == "ativar" else "companhia_desativada",
                        ok=True, detalhe="concessão temporária confirmada pelo owner corporal", fala=fala, receipt=receipt)
    if intent == "CORPO_MOVER":
        if params.get("angulo_graus") is not None:
            if receipt.get("prova_rotacao") is not True:
                return concluir("falha_execucao", ok=False, detalhe="ângulo não confirmado pelo MPU",
                                fala="Não consegui confirmar o giro medido.", receipt=receipt)
            return concluir("giro_medido_confirmado", ok=True, detalhe="rotação relativa estimada pela IMU e parada elétrica",
                fala=f"O sensor mediu aproximadamente {abs(receipt['rotacao_medida_graus']):.0f} graus de giro para {params['direcao']}; a ponte confirmou a parada.", receipt=receipt)
        fala = f"Acionei um pulso para {params.get('direcao')}, limitado a até {params.get('duracao_ms', 250)} milissegundos. A ponte confirmou a parada."
    return concluir("corpo_parado" if intent == "CORPO_PARAR" else "pulso_corporal_confirmado", ok=True,
                    detalhe="estado do firmware confirmado; sem medida de giro ou deslocamento", fala=fala, receipt=receipt)
