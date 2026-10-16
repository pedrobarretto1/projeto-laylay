"""Porta do corpo com pulsos finitos no proprietário serial já instalado."""
from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol
from mente_laylay.autonomia.companhia_corporal import CompanhiaCorporalRuntime
from mente_laylay.memoria_mental.experiencia_corporal_runtime import criar_experiencia_corporal_runtime


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
        self.experiencias = criar_experiencia_corporal_runtime(estado=estado,
            diagnostico_getter=lambda: self.transporte.diagnostico(), relatar_falha=registrar_falha_cb)
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
                "companhia": self.companhia.diagnostico(), "experiencia": self.experiencias.retrato(), "possui_sensor_de_deslocamento": False}

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
        experiencia = self.experiencias.retrato()
        mental_atual = self.estado.retrato_dominio("mental") if self.estado is not None else {}
        turno_atual_id = str((mental_atual.get("turno_atual") or {}).get("id") or "")
        turno_leitura_id = str(turno_id) if turno_id is not None else turno_atual_id
        intencao = self.companhia.diagnostico().get("intencao") or {}
        campos_intencao = ("id", "objetivo_id", "nome", "motivo", "estado", "fase", "turno_id", "plano_id", "resultado")
        intencao_atual = {k: intencao[k] for k in campos_intencao if k in intencao}
        intencao_atual.update(autoriza_execucao=False,
            sessao_vigente=bool(conectada and ativa and intencao.get("sessao") == diag.get("sessao")),
            pertence_ao_turno_atual=bool(turno_atual_id and turno_leitura_id == turno_atual_id
                                       and intencao.get("turno_id") == turno_atual_id))
        ultima_experiencia = dict(mental_atual.get("experiencia_corporal") or {})
        if ultima_experiencia:
            ultima_experiencia["pertence_ao_turno_atual"] = bool(turno_atual_id and turno_leitura_id == turno_atual_id
                and ultima_experiencia.get("turno_id") == turno_atual_id)
        condicao = ("desconectada" if not conectada else "controle_motor_indisponivel" if motor.get("disponivel") is not True
                    else "acionamento_em_andamento" if motor.get("em_andamento") is True else "pronta")
        modelo = {"origem": "owner_corpo_usb", "ts": time.time(), "turno_id": turno_leitura_id,
            "sessao": diag.get("sessao", ""), "concessao_id": c.get("id", ""),
            "conectada": conectada, "companhia_ativa": ativa and conectada and motor.get("disponivel") is True,
            "passeio_ativo": ativa and conectada and c.get("passeio") is True,
            "perfil": self.companhia.perfil_corporal,
            "condicao": {"estado": condicao, "motivo_motor": str(motor.get("motivo") or ""), "origem": "diagnostico_firmware", "autoriza_execucao": False},
            "experiencia": experiencia,
            "intencao_em_curso": intencao_atual,
            "percepcao_fisica": {"deslocamento": "nao_medido", "contato": "nao_medido", "obstaculos": "nao_medido"},
            "olhos": list(diag.get("confirmado") or ()), "motor_em_andamento": motor.get("em_andamento") is True,
            "emocao_causal": {"nome": EMOCOES_ROSTO[emocao], "nivel": nivel},
            "atencao_pc": self.companhia._atencao_prioritaria() or projetar_execucao_operacional(self.companhia._atividade()), "autoriza_execucao": False,
            "ultima_experiencia": ultima_experiencia}
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

    def registrar_experiencia(self, ocorrencia: Mapping[str, Any], retorno: Mapping[str, Any],
                             receipts: list[dict[str, Any]], *, parada: bool = False) -> dict[str, Any]:
        try:
            return self.experiencias.registrar(ocorrencia, retorno, receipts, parada=parada)
        except Exception as erro:
            self.experiencias._falha("falha_publicacao_experiencia", erro)
            return {}

    def _executar_manual_observado(self, ocorrencia: Mapping[str, Any], intent: str, callback: Callable[[], Any]) -> dict[str, Any]:
        try:
            retorno = self.confirmar_receipt(callback(), intent)
        except Exception as erro:
            self.registrar_experiencia(ocorrencia, {"ok": False, "motivo": type(erro).__name__}, [])
            raise
        self.registrar_experiencia(ocorrencia, retorno, [retorno], parada=intent == "CORPO_PARAR")
        return retorno

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
            ocorrencia = self.experiencias.iniciar(nome="parar", origem_intencao="pedido_usuario", perfil=self.companhia.perfil_corporal)
            self.companhia.revogar("parada_solicitada")
            return self._executar_manual_observado(ocorrencia, intent, self.transporte.parar_corpo)
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
            ocorrencia = self.experiencias.iniciar(nome=f"mover_{direcao}", origem_intencao="pedido_usuario",
                perfil=self.companhia.perfil_corporal, movimentos=((esqu, dire, duracao),))
            estava_ativa = self.companhia.diagnostico()["ativa"]
            self.companhia.revogar("movimento_manual_prioritario")
            if estava_ativa and (self.transporte.diagnostico().get("motor") or {}).get("em_andamento"):
                self.transporte.parar_corpo()
            return self._executar_manual_observado(ocorrencia, intent, lambda: self.transporte.mover_corpo(esqu, dire, duracao))


def criar_corpo_motor_runtime(**kwargs: Any) -> CorpoMotorRuntime:
    return CorpoMotorRuntime(**kwargs)
