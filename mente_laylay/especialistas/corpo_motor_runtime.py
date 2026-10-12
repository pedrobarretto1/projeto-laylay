"""Porta do corpo com pulsos finitos no proprietário serial já instalado."""
from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol
from mente_laylay.autonomia.companhia_corporal import CompanhiaCorporalRuntime


class PortaTransporteCorpo(Protocol):
    def mover_corpo(self, pwm_esquerdo: int, pwm_direito: int, duracao_ms: int,
                    *, validar_inicio: Callable[[], bool] | None = None) -> dict[str, Any]: ...
    def parar_corpo(self) -> dict[str, Any]: ...
    def diagnostico(self) -> dict[str, Any]: ...


class CorpoMotorRuntime:
    def __init__(self, *, transporte: PortaTransporteCorpo, estado: Any = None,
                 registrar_falha_cb: Callable[..., Any] | None = None,
                 observar_resultado_cb: Callable[..., Any] | None = None,
                 companhia_bancada_ao_iniciar: bool = False,
                 passeio_bancada_ao_iniciar: bool = False,
                 perfil_corporal: str = "bancada",
                 prioridade_interacao_getter: Callable[[], bool] | None = None,
                 monotonic: Callable[[], float] | None = None) -> None:
        self.transporte = transporte
        self.estado = estado
        self.registrar_falha_cb = registrar_falha_cb
        self.observar_resultado_cb = observar_resultado_cb
        self.companhia = CompanhiaCorporalRuntime(corpo=self, estado=estado,
            companhia_bancada_ao_iniciar=companhia_bancada_ao_iniciar,
            passeio_bancada_ao_iniciar=passeio_bancada_ao_iniciar,
            perfil_corporal=perfil_corporal,
            prioridade_interacao_getter=prioridade_interacao_getter,
            **({"monotonic": monotonic} if monotonic is not None else {}))

    def diagnostico(self) -> dict[str, Any]:
        try:
            motor = dict(self.transporte.diagnostico().get("motor") or {})
        except Exception:
            motor = {"disponivel": False, "motivo": "diagnostico_serial_indisponivel"}
        return {**motor, "pulsos_limitados": True, "duracao_maxima_ms": motor.get("duracao_maxima_ms", 500),
                "autonomia_ativada": self.companhia.diagnostico()["ativa"],
                "companhia": self.companhia.diagnostico(), "possui_sensor_de_deslocamento": False}

    def _publicar(self, retorno: dict[str, Any]) -> None:
        if self.estado is None:
            return
        try:
            # Receipt transitório, não aprendizado durável nem autorização.
            self.estado.atualizar_campos("mental", corpo_motor={
                **retorno, "origem": "executor_corpo", "autoriza_execucao": False,
                "prova_rotacao": False, "prova_parada_fisica": False,
            })
        except Exception:
            pass

    def modelo_para_mente(self, turno_id: Any = None) -> dict[str, Any]:
        """Retrato vivo no owner do corpo; contexto nunca restaura uma concessão."""
        import time
        from mente_laylay.cognicao.decisao_turno import motivo_incoerencia_contratos_turno
        from mente_laylay.memoria_mental.atividade_operacional_runtime import projetar_execucao_operacional
        from mente_laylay.especialistas.rosto_oled_runtime import projetar_rosto, EMOCOES_ROSTO
        diag = self.transporte.diagnostico()
        with self.companhia._lock:
            c = dict(self.companhia._concessao or {})
            ativa = bool(c and not self.companhia._revogada.is_set() and c.get("sessao") == diag.get("sessao"))
        motor = diag.get("motor") or {}
        conectada = diag.get("aplicacao_confirmada") is True
        emocao, nivel, _ = projetar_rosto(self.companhia._conversa())
        modelo = {"origem": "owner_corpo_usb", "ts": time.time(), "turno_id": str(turno_id or ""),
            "sessao": diag.get("sessao", ""), "concessao_id": c.get("id", ""),
            "conectada": conectada, "companhia_ativa": ativa and conectada and motor.get("disponivel") is True,
            "passeio_ativo": ativa and conectada and c.get("passeio") is True,
            "perfil": self.companhia.perfil_corporal,
            "olhos": list(diag.get("confirmado") or ()), "motor_em_andamento": motor.get("em_andamento") is True,
            "emocao_causal": {"nome": EMOCOES_ROSTO[emocao], "nivel": nivel},
            "atencao_pc": self.companhia._atencao_prioritaria() or projetar_execucao_operacional(self.companhia._atividade()), "autoriza_execucao": False,
            "ultima_experiencia": self.estado.obter_copia("mental", "experiencia_corporal", {}) if self.estado is not None else {}}
        if self.estado is not None:
            def publicar(mental):
                novo = {**mental, "modelo_corporal": modelo}
                plano = dict(mental.get("plano_turno_atual") or {})
                if (turno_id is not None and str(plano.get("id")) == str(turno_id)
                        and not motivo_incoerencia_contratos_turno(mental.get("turno_atual"), plano, mental.get("retrato_turno_atual"))
                        and not plano.get("intencao_corporal")):
                    novo["plano_turno_atual"] = {**plano, "retrato_corporal": modelo}
                return novo
            self.estado.atualizar("mental", publicar)
        return modelo

    def confirmar_receipt(self, retorno: Any, intent: str) -> dict[str, Any]:
        retorno = dict(retorno) if isinstance(retorno, dict) else {"ok": False, "motivo": "receipt_serial_invalido"}
        retorno["ok"] = bool(
            retorno.get("ok") is True and retorno.get("parada_confirmada") is True
            and (intent == "CORPO_PARAR" or retorno.get("aplicacao_pwm_confirmada") is True)
        )
        self._publicar(retorno)
        return retorno

    def executar(self, intent: str, params: dict[str, Any], *, autorizacao: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if intent == "CORPO_COMPANHIA":
            return self.companhia.configurar(str(params.get("acao") or ""), autorizacao or {})
        if intent not in {"CORPO_MOVER", "CORPO_PARAR"}:
            return {"ok": False, "motivo": "intencao_corporal_invalida"}
        if intent == "CORPO_PARAR":
            self.companhia.revogar("parada_solicitada")
            retorno = self.transporte.parar_corpo()
        else:
            direcao = params.get("direcao")
            pwm, duracao = params.get("pwm", 255), params.get("duracao_ms", 250)
            if (direcao not in {"frente", "tras", "esquerda", "direita"}
                    or type(pwm) is not int or not 1 <= pwm <= 255
                    or type(duracao) is not int or not 50 <= duracao <= 500):
                return {"ok": False, "motivo": "parametros_corporais_invalidos"}
            esqu, dire = {
                "frente": (pwm, pwm), "tras": (-pwm, -pwm),
                "esquerda": (-pwm, pwm), "direita": (pwm, -pwm),
            }[direcao]
            estava_ativa = self.companhia.diagnostico()["ativa"]
            self.companhia.revogar("movimento_manual_prioritario")
            if estava_ativa and (self.transporte.diagnostico().get("motor") or {}).get("em_andamento"):
                self.transporte.parar_corpo()
            retorno = self.transporte.mover_corpo(esqu, dire, duracao)
        return self.confirmar_receipt(retorno, intent)


def criar_corpo_motor_runtime(**kwargs: Any) -> CorpoMotorRuntime:
    return CorpoMotorRuntime(**kwargs)
