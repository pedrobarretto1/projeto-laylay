"""Execução governada das etapas de um plano cooperativo."""

from __future__ import annotations

import time
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.governanca_cooperacao import GovernancaPlanoCooperativoRuntime
from mente_laylay.autonomia.quadro_cooperacao import ESTADOS_FINAIS, QuadroCooperacaoRuntime


class ExecutorPlanoCooperativoRuntime:
    """Executa etapas autorizadas sem falar e sem contornar executores canônicos.

    O orçamento é cooperativo: ele impede o início de novas etapas depois do
    limite, mas não abandona uma chamada que já alterou estado. Cada adaptador
    continua responsável por seus próprios timeouts e pela evidência real.
    """

    def __init__(
        self,
        *,
        quadro: QuadroCooperacaoRuntime,
        governanca: GovernancaPlanoCooperativoRuntime | None = None,
        relogio: Callable[[], float] = time.monotonic,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.quadro = quadro
        self.governanca = governanca or GovernancaPlanoCooperativoRuntime(quadro=quadro, log=log)
        self.relogio = relogio
        self.log = log

    def _agora(self) -> float:
        return float(self.relogio())

    @staticmethod
    def _executor_da_etapa(
        etapa: Mapping[str, Any],
        executores: Mapping[str, Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]],
    ) -> Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]] | None:
        chaves = (
            str(etapa.get("id") or ""),
            str(etapa.get("acao") or ""),
            f"{etapa.get('habilidade') or ''}:{etapa.get('acao') or ''}",
        )
        return next((executores[chave] for chave in chaves if chave in executores), None)

    def executar(
        self,
        plano_id: str,
        executores: Mapping[
            str,
            Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]],
        ],
        *,
        contexto_execucao: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        plano = self.quadro.obter_plano(plano_id)
        if not plano:
            return {"ok": False, "estado": "expirado", "status": "plano_indisponivel"}
        if str(plano.get("estado") or "") in ESTADOS_FINAIS:
            estado_existente = str(plano.get("estado") or "")
            self.governanca.finalizar(
                plano,
                decisao=("aceito" if estado_existente == "confirmado" else estado_existente),
                motivo=str((plano.get("resultado") or {}).get("status") or "plano_finalizado"),
            )
            return {
                "ok": estado_existente == "confirmado",
                "estado": estado_existente,
                "status": str((plano.get("resultado") or {}).get("status") or "plano_finalizado"),
                "idempotente": True,
            }
        if plano.get("cancelamento_solicitado"):
            final = self.quadro.atualizar_plano(
                plano_id, "cancelado", resultado={"status": "cancelamento_solicitado"},
            ) or plano
            self.governanca.finalizar(
                final, decisao="cancelado", motivo="cancelamento_solicitado",
            )
            return {"ok": False, "estado": final.get("estado"), "status": "cancelamento_solicitado"}

        inicio = self._agora()
        limite_total = inicio + (int(plano.get("orcamento_total_ms") or 1) / 1000.0)
        self.quadro.atualizar_plano(plano_id, "executando")
        self.governanca.registrar_ciclo(self.quadro.obter_plano(plano_id) or plano, "iniciado")
        falhas: list[dict[str, Any]] = []
        interrompido = False
        expirou = False

        for etapa_original in list(plano.get("etapas") or []):
            etapa_id = str(etapa_original.get("id") or "")
            plano_atual = self.quadro.obter_plano(plano_id) or plano
            etapa = next((
                item for item in list(plano_atual.get("etapas") or [])
                if str(item.get("id") or "") == etapa_id
            ), dict(etapa_original))
            if str(etapa.get("estado") or "") == "confirmado":
                continue
            if plano_atual.get("cancelamento_solicitado"):
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "cancelado", resultado={"status": "cancelamento_solicitado"},
                )
                self.quadro.atualizar_plano(
                    plano_id, "cancelado", resultado={"status": "cancelamento_solicitado"},
                )
                final_cancelado = self.quadro.obter_plano(plano_id) or plano_atual
                self.governanca.finalizar(
                    final_cancelado, decisao="cancelado", motivo="cancelamento_solicitado",
                )
                return {"ok": False, "estado": "cancelado", "status": "cancelamento_solicitado"}
            if self._agora() >= limite_total:
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "expirado",
                    resultado={"status": "orcamento_total_excedido", "orcamento_excedido": True},
                )
                expirou = True
                break

            estados = {
                str(item.get("id") or ""): str(item.get("estado") or "")
                for item in list(plano_atual.get("etapas") or [])
            }
            pendentes = [
                dependencia for dependencia in list(etapa.get("depende_de") or [])
                if estados.get(str(dependencia)) != "confirmado"
            ]
            if pendentes:
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "bloqueado",
                    resultado={"status": "dependencia_nao_confirmada", "motivo": ",".join(pendentes)},
                )
                falhas.append({"etapa": etapa_id, "status": "dependencia_nao_confirmada"})
                interrompido = (
                    str(plano.get("politica_falha_parcial") or "interromper") == "interromper"
                    or str(etapa.get("politica_falha") or "interromper") == "interromper"
                )
                if interrompido:
                    break
                continue

            executor = self._executor_da_etapa(etapa, executores)
            autorizacao = self.governanca.avaliar_autorizacao(
                plano_atual, etapa, contexto_execucao,
            )
            if not autorizacao.get("permitido"):
                self.quadro.registrar_autorizacao_bloqueada()
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "bloqueado",
                    resultado={
                        "status": "autorizacao_negada",
                        "motivo": str(autorizacao.get("motivo") or "porteiro_negou"),
                    },
                )
                falhas.append({"etapa": etapa_id, "status": "autorizacao_negada"})
            elif not callable(executor):
                self.quadro.atualizar_etapa(
                    plano_id, etapa_id, "falhou", resultado={"status": "executor_indisponivel"},
                )
                falhas.append({"etapa": etapa_id, "status": "executor_indisponivel"})
            else:
                inicio_etapa = self._agora()
                self.quadro.atualizar_etapa(plano_id, etapa_id, "executando")
                try:
                    retorno = dict(executor(etapa, plano_atual) or {})
                except Exception as erro:
                    self.log(
                        "⚠️ [COOPERAÇÃO] etapa falhou isoladamente | "
                        f"etapa={etapa_id} erro={type(erro).__name__}"
                    )
                    retorno = {"ok": False, "confirmado": False, "status": "falha_isolada"}
                duracao_ms = max(0, int((self._agora() - inicio_etapa) * 1000))
                confirmou = bool(retorno.get("ok") and retorno.get("confirmado") is True)
                excedeu = duracao_ms > int(etapa.get("orcamento_ms") or 1)
                resultado_etapa = {
                    "status": str(retorno.get("status") or ("confirmado" if confirmou else "nao_confirmado")),
                    "confirmado": confirmou,
                    "evidencia": str(retorno.get("evidencia") or "")[:160],
                    "orcamento_excedido": excedeu,
                }
                if confirmou:
                    self.quadro.atualizar_etapa(
                        plano_id, etapa_id, "confirmado",
                        resultado=resultado_etapa, duracao_ms=duracao_ms,
                    )
                else:
                    estado_falha = "expirado" if excedeu or retorno.get("estado_plano") == "expirado" else "falhou"
                    self.quadro.atualizar_etapa(
                        plano_id, etapa_id, estado_falha,
                        resultado=resultado_etapa, duracao_ms=duracao_ms,
                    )
                    falhas.append({"etapa": etapa_id, "status": resultado_etapa["status"]})
                    expirou = expirou or estado_falha == "expirado"

            if falhas and falhas[-1].get("etapa") == etapa_id:
                interrompido = (
                    str(plano.get("politica_falha_parcial") or "interromper") == "interromper"
                    or str(etapa.get("politica_falha") or "interromper") == "interromper"
                )
                if interrompido:
                    break

        plano_final = self.quadro.obter_plano(plano_id) or plano
        etapas_finais = list(plano_final.get("etapas") or [])
        obrigatorias_ok = all(
            str(item.get("estado") or "") == "confirmado"
            for item in etapas_finais if bool(item.get("obrigatoria", True))
        )
        if falhas and obrigatorias_ok:
            self.quadro.registrar_falha_parcial()
        if expirou and not obrigatorias_ok:
            estado_final = "expirado"
        elif obrigatorias_ok:
            estado_final = "confirmado"
        else:
            estado_final = "falhou"
        status_final = (
            "plano_confirmado_com_falha_parcial"
            if estado_final == "confirmado" and falhas
            else "plano_confirmado"
            if estado_final == "confirmado"
            else "orcamento_excedido"
            if estado_final == "expirado"
            else falhas[-1]["status"] if falhas else "etapas_nao_confirmadas"
        )
        self.quadro.atualizar_plano(
            plano_id,
            estado_final,
            resultado={
                "status": status_final,
                "confirmado": estado_final == "confirmado",
                "falhas_parciais": len(falhas) if obrigatorias_ok else 0,
                "interrompido": interrompido,
            },
        )
        final_atual = self.quadro.obter_plano(plano_id) or plano_final
        decisao = (
            "aceito" if estado_final == "confirmado"
            else "cancelado" if estado_final == "cancelado"
            else "expirado" if estado_final == "expirado"
            else "falhou"
        )
        self.governanca.finalizar(
            final_atual, decisao=decisao, motivo=status_final,
        )
        return {
            "ok": estado_final == "confirmado",
            "estado": estado_final,
            "status": status_final,
            "falhas": falhas,
        }
