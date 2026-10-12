"""Executa pedidos corporais autorizados, sem afirmar locomoção observada."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from mente_laylay.autonomia.contrato_executor import ResultadoDespacho
from mente_laylay.cognicao.modalidade_turno import autoriza_execucao_efetiva
from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo


@dataclass(frozen=True, slots=True)
class DependenciasExecutorCorpo:
    marcar_resultado: Callable[..., Any]
    falar_por_status: Callable[..., Any]


def executar_intencao_corpo(intent: str, params: dict[str, Any], texto_original: str,
                            ctx: dict[str, Any], deps: DependenciasExecutorCorpo) -> ResultadoDespacho:
    if intent not in {"CORPO_MOVER", "CORPO_PARAR", "CORPO_COMPANHIA"}:
        return ResultadoDespacho.nao_tratado()

    def concluir(status: str, *, ok: bool, detalhe: str, fala: str, receipt: dict[str, Any] | None = None) -> ResultadoDespacho:
        executou = ok or (receipt or {}).get("aplicacao_pwm_confirmada") is True
        deps.marcar_resultado(status, executou=executou, confirmado=ok, detalhe=detalhe,
            alvo_resolvido="corpo", params_resolvidos=params,
            contexto_resultado={"receipt_corpo": dict(receipt or {}), "prova_deslocamento": False},
            evidencia_confirmacao=str((receipt or {}).get("evidencia") or ""))
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
        candidato = next((parte for parte in candidatos if intent == "CORPO_PARAR"
                          or (intent == "CORPO_COMPANHIA" and parte["params"].get("acao") == params.get("acao"))
                          or (intent == "CORPO_MOVER" and parte["params"].get("direcao") == params.get("direcao"))), None)
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
    # Um comando proposto não pode trocar a direção presente na fala atual.
    if candidato and intent == "CORPO_MOVER" and any(
        params.get(chave, candidato["params"][chave]) != candidato["params"][chave]
        for chave in ("direcao", "pwm", "duracao_ms")
    ):
        return concluir("bloqueado_alvo_divergente", ok=False, detalhe="direção difere da fala autorizadora",
                        fala="O movimento proposto não corresponde à direção que você pediu.")
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
    except Exception as erro:
        return concluir("falha_execucao", ok=False, detalhe=f"executor corporal: {type(erro).__name__}",
                        fala="O controle do corpo falhou. Não consegui confirmar a execução.")
    if receipt.get("ok") is not True:
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
        fala = f"Acionei um pulso para {params.get('direcao')}, limitado a até {params.get('duracao_ms', 250)} milissegundos. A ponte confirmou a parada."
    return concluir("corpo_parado" if intent == "CORPO_PARAR" else "pulso_corporal_confirmado", ok=True,
                    detalhe="estado do firmware confirmado; sem medida de giro ou deslocamento", fala=fala, receipt=receipt)
