"""Gestos da mente sob concessão efêmera: percepção nunca concede movimento."""
from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.gramatica_corpo import detectar_intencao_corpo
from mente_laylay.cognicao.modalidade_turno import autoriza_execucao_efetiva
from mente_laylay.especialistas.rosto_oled_runtime import projetar_rosto
from mente_laylay.memoria_mental.atividade_operacional_runtime import (
    projetar_sucesso_operacional, projetar_atividade_operacional,
)


@dataclass(frozen=True)
class GestoCorporal:
    """Partitura finita; duração é PWM aplicado, nunca distância observada."""
    nome: str
    antecipacao_ms: int
    movimentos: tuple[tuple[int, int, int], ...]
    pausa_ms: int = 0


# Autoria própria inspirada na composição expressiva do Cozmo: rosto, reação,
# pausa e acomodação. Sem copiar animações, ângulos ou velocidades de outro robô.
# PWM100 preservado; comandos individuais respeitam os 500 ms do firmware.
# A concessão pertence à sessão, sem expirar por contagem ou tempo de conversa.
INTERVALO_GESTOS_S = 2
DURACAO_MOTOR_GESTO_MS = 1500
DURACAO_PLANEJADA_GESTO_MS = 2400
GESTOS = {
    1: GestoCorporal("alegria_balanco", 100, ((100, 100, 220), (-100, -100, 220)), 100),
    2: GestoCorporal("tristeza_recolhimento", 300, ((-100, -100, 180),)),
    3: GestoCorporal("braveza_negacao", 70,
                    ((100, -100, 180), (-100, 100, 220), (100, -100, 140), (-100, 100, 100)), 60),
    4: GestoCorporal("irritacao_desviar", 180, ((-100, 100, 220), (100, -100, 100)), 200),
    5: GestoCorporal("surpresa_recuo", 0, ((-100, -100, 150),)),
    6: GestoCorporal("vergonha_hesitacao", 220, ((-100, 100, 130), (100, -100, 90)), 250),
    7: GestoCorporal("deboche_olhar_lateral", 120, ((100, -100, 300), (-100, 100, 140)), 160),
}
COMEMORACOES = (
    # Tempos práticos das rotinas comemorar/wiggle de control_display; PWM100.
    GestoCorporal("comemoracao_balanco", 120, ((-100, 100, 240), (100, -100, 480), (-100, 100, 240)), 80),
    GestoCorporal("comemoracao_dancinha", 100,
                  ((-100, 100, 170), (100, -100, 330), (-100, 100, 330), (100, -100, 170)), 100),
    GestoCorporal("comemoracao_giro", 100, ((100, -100, 400),) * 3),
)
PASSEIOS = (
    GestoCorporal("passeio_avanco", 80, ((100, 100, 300), (-100, 100, 180)), 120),
    GestoCorporal("passeio_recuo", 80, ((-100, -100, 220), (100, -100, 180)), 120),
    GestoCorporal("passeio_curva", 80, ((100, 100, 250), (100, -100, 220)), 120),
    GestoCorporal("passeio_olhar", 80, ((-100, 100, 220), (100, -100, 120)), 120),
)


def selecionar_gesto(emocao: int, nivel: int, *, espelhar: bool = False) -> GestoCorporal | None:
    """Intensidade altera o tempo, preservando o piso PWM e o orçamento total."""
    base = GESTOS.get(emocao)
    if base is None:
        return None
    delta = (max(1, min(3, nivel)) - 2) * 30
    teto = min(500, DURACAO_MOTOR_GESTO_MS // len(base.movimentos))
    movimentos = tuple((d if espelhar else e, e if espelhar else d, max(50, min(teto, ms + delta)))
                       for e, d, ms in base.movimentos)
    return GestoCorporal(base.nome, base.antecipacao_ms, movimentos, base.pausa_ms)


class CompanhiaCorporalRuntime:
    def __init__(self, *, corpo: Any, estado: Any,
                 companhia_bancada_ao_iniciar: bool = False,
                 passeio_bancada_ao_iniciar: bool = False,
                 monotonic: Callable[[], float] = time.monotonic) -> None:
        self.corpo, self.estado, self.monotonic = corpo, estado, monotonic
        self._lock = threading.RLock()
        self._revogada = threading.Event()
        self._revogada.set()
        self._concessao: dict[str, Any] | None = None
        self._automatica_ao_iniciar = companhia_bancada_ao_iniciar is True
        self._passeio_ao_iniciar = self._automatica_ao_iniciar and passeio_bancada_ao_iniciar is True
        self._ativacao_pendente = self._automatica_ao_iniciar
        self._motivo = "aguardando_ativacao_explicita"
        self._observado = (0, 1, 0)
        self._alternar = False
        self._sucesso_observado = 0
        self._comemoracoes = 0
        self._passeios = 0
        self.coordenador: Any = None
        self._publicar()

    def _retrato(self) -> tuple[int, int, int]:
        if self.estado is None:
            return (0, 1, 0)
        estado = self.estado.retrato_dominio("conversacional")
        olhos = projetar_rosto(estado)
        # Gesto lê a causa na mente; não depende de enviar voz ao OLED.
        return olhos[0], olhos[1], int(estado.get("is_speaking") is True)

    def _olhos_confirmados(self, diagnostico: Mapping[str, Any]) -> bool:
        retrato = self._retrato()
        return tuple(diagnostico.get("confirmado") or ()) == (retrato[0], retrato[1], 0)

    def _atividade(self) -> dict[str, Any]:
        return self.estado.obter_copia("mental", "atividade_operacional", {}) if self.estado is not None else {}

    def _sucesso(self) -> tuple[int, float] | None:
        return projetar_sucesso_operacional(self._atividade(), agora=self.monotonic())

    def revogar(self, motivo: str) -> None:
        # Publicado antes de aguardar o transporte: STOP pode interromper MACK.
        self._revogada.set()
        with self._lock:
            self._concessao = None
            self._ativacao_pendente = False
            self._motivo = motivo
        self._publicar()

    def _publicar(self) -> None:
        if self.estado is not None:
            self.estado.atualizar_campos("mental", companhia_corporal=self.diagnostico())

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            concessao = dict(self._concessao or {})
            ativa = bool(concessao and not self._revogada.is_set())
            return {"ativa": ativa, "motivo": self._motivo, "transporte_exigido": "serial",
                    "ttl_maximo_s": None, "gestos_maximos": None, "gestos_emitidos": concessao.get("gestos", 0),
                    "intervalo_minimo_s": INTERVALO_GESTOS_S, "pwm_gestos": 100,
                    "duracao_maxima_gesto_ms": DURACAO_MOTOR_GESTO_MS,
                    "duracao_planejada_maxima_coreografia_ms": DURACAO_PLANEJADA_GESTO_MS,
                    "movimentos_maximos_por_gesto": 4,
                    "perfil_expressivo": "ritmo_emocional_v2",
                    "passeio_ativado": ativa and concessao.get("passeio") is True,
                    "comemoracoes_emitidas": self._comemoracoes, "passeios_emitidos": self._passeios,
                    "giro_360_calibrado": False,
                    "restantes_s": None, "vigencia": "sessao_usb_atual_ate_revogacao",
                    "origem": concessao.get("origem", "concessao_explicita_de_sessao"),
                    "ativacao_automatica_ao_iniciar": self._automatica_ao_iniciar,
                    "passeio_automatico_ao_iniciar": self._passeio_ao_iniciar,
                    "autoriza_execucao": False,
                    "persistente": False, "possui_sensores": False}

    def configurar(self, acao: str, autorizacao: Mapping[str, Any]) -> dict[str, Any]:
        pedido = detectar_intencao_corpo(str(autorizacao.get("texto") or ""))
        if (not autoriza_execucao_efetiva(autorizacao) or not pedido
            or pedido["intent"] != "CORPO_COMPANHIA" or pedido["params"]["acao"] != acao):
            return {"ok": False, "motivo": "concessao_sem_pedido_atual"}
        if acao == "desativar":
            self.revogar("desativada_pelo_usuario")
            retorno = self.corpo.transporte.parar_corpo()
            return {**retorno, "ok": retorno.get("ok") is True and retorno.get("parada_confirmada") is True}
        return self._ativar_sessao(passeio=pedido["params"].get("passeio") is True)

    def _ativar_sessao(self, *, passeio: bool = False, automatica: bool = False) -> dict[str, Any]:
        """Mesmo owner e contrato USB para pedido atual ou preferência explícita."""
        diag = self.corpo.transporte.diagnostico()
        if (diag.get("transporte") != "serial" or not diag.get("sessao")
            or diag.get("aplicacao_confirmada") is not True
            or (diag.get("motor") or {}).get("disponivel") is not True
            or (diag.get("motor") or {}).get("em_andamento")
            or self.coordenador is None):
            return {"ok": False, "motivo": "companhia_requer_sessao_usb_pronta"}
        retrato = self._retrato()
        with self._lock:
            # STOP pode chegar enquanto a consulta de transporte está em andamento.
            if automatica and not self._ativacao_pendente:
                return {"ok": False, "motivo": "ativacao_automatica_revogada"}
            self._concessao = {"id": secrets.token_hex(8), "sessao": diag["sessao"],
                              "origem": "configuracao_explicita_de_bancada" if automatica else "concessao_explicita_de_sessao",
                              "gestos": 0, "ultimo_gesto": self.monotonic() - INTERVALO_GESTOS_S,
                              "passeio": passeio,
                              "proximo_passeio": self.monotonic() + 8}
            self._ativacao_pendente = False
            self._observado = retrato  # Não reproduz a emoção anterior à concessão.
            self._sucesso_observado = (self._sucesso() or (0, 0))[0]
            self._motivo = "concessao_usb_vigente"
            self._revogada.clear()
        self._publicar()
        return {"ok": True, "modo_ativado": True, "passeio_ativado": passeio,
                "evidencia": "concessao_temporaria_no_owner_corporal"}

    def autorizar_escopo(self, plano: Mapping[str, Any], etapa: Mapping[str, Any]) -> dict[str, Any]:
        meta = plano.get("metadados") or {}
        if (meta.get("fluxo") != "companhia_corporal"
            or etapa.get("intent") not in {"ROSTO_VERIFICAR", "CORPO_GESTO"}):
            return {"permitido": False, "motivo": "operacao_fora_do_escopo"}
        return {"permitido": self._vigente(meta), "motivo": "concessao_corporal_revalidada"}

    def _vigente(self, meta: Mapping[str, Any]) -> bool:
        diag = self.corpo.transporte.diagnostico()
        with self._lock:
            c = self._concessao
            agora = self.monotonic()
            return bool(c and not self._revogada.is_set() and c["id"] == meta.get("concessao_id")
                        and c["sessao"] == diag.get("sessao")
                        and 0 <= agora - float(meta.get("proposto_em", -100)) <= 5
                        and diag.get("transporte") == "serial" and diag.get("aplicacao_confirmada") is True
                        and (diag.get("motor") or {}).get("disponivel") is True)

    def _aguardar_gesto(self, ms: int, validar: Callable[[], bool]) -> bool:
        # Nenhum lock de transporte durante a pausa; revogação acorda de imediato.
        return validar() and not self._revogada.wait(ms / 1000) and validar()

    def processar(self) -> dict[str, Any]:
        retrato = self._retrato()
        diag = self.corpo.transporte.diagnostico()
        with self._lock:
            anterior = self._observado
            c = dict(self._concessao or {})
            ativar_automaticamente = self._ativacao_pendente
        if not c:
            self._observado = retrato
            if ativar_automaticamente:
                return self._ativar_sessao(automatica=True, passeio=self._passeio_ao_iniciar)
            return {"ok": False, "motivo": "companhia_inativa"}
        if (diag.get("sessao") != c["sessao"] or diag.get("aplicacao_confirmada") is not True
            or diag.get("transporte") != "serial" or (diag.get("motor") or {}).get("disponivel") is not True):
            self.revogar("concessao_expirada_ou_conexao_perdida")
            return {"ok": False, "motivo": self._motivo}
        if not self._olhos_confirmados(diag):
            return {"ok": False, "motivo": "aguardando_retrato_no_oled"}
        self._observado = retrato
        atividade = self._atividade()
        ocupada = projetar_atividade_operacional(atividade, agora=self.monotonic())
        sucesso = self._sucesso()
        novo_sucesso = bool(sucesso and sucesso[0] != self._sucesso_observado)
        origem_gesto = "emocao"
        if novo_sucesso and not ocupada:
            gesto = COMEMORACOES[self._comemoracoes % len(COMEMORACOES)]
            origem_gesto = "sucesso_operacional"
        else:
            gesto = selecionar_gesto(retrato[0], retrato[1], espelhar=bool(c["gestos"] % 2)) if retrato[:2] != anterior[:2] else None
        if gesto is None and retrato[2] and not anterior[2]:
            self._alternar = not self._alternar
            motores_fala = (100, -100, 150) if self._alternar else (-100, 100, 150)
            gesto = GestoCorporal("fala_enfase", 60, (motores_fala,))
            origem_gesto = "fala"
        if (gesto is None and c.get("passeio") and not ocupada and not retrato[2]
                and self.monotonic() >= c["proximo_passeio"]):
            gesto = PASSEIOS[self._passeios % len(PASSEIOS)]
            origem_gesto = "passeio"
        if gesto is None or self.monotonic() - c["ultimo_gesto"] < INTERVALO_GESTOS_S:
            return {"ok": False, "motivo": "sem_gesto_novo_ou_em_intervalo"}
        meta = {"concessao_id": c["id"], "proposto_em": self.monotonic(), "gesto": gesto.nome}
        with self._lock:
            if not self._concessao or self._concessao["id"] != c["id"] or self._revogada.is_set():
                return {"ok": False, "motivo": "concessao_revogada"}
            self._concessao["gestos"] += 1
            self._concessao["ultimo_gesto"] = self.monotonic()
            self._concessao["proximo_passeio"] = self.monotonic() + (8, 12, 10, 14)[self._passeios % 4]
            if origem_gesto == "sucesso_operacional":
                self._sucesso_observado = sucesso[0]
                self._comemoracoes += 1
            elif origem_gesto == "passeio":
                self._passeios += 1
        falha_inicial = atividade.get("falha_id", 0)
        def causa_vigente() -> bool:
            if origem_gesto == "sucesso_operacional":
                return self._sucesso() == sucesso and self._atividade().get("falha_id", 0) == falha_inicial
            if origem_gesto == "passeio":
                return (self._retrato() == retrato and not projetar_atividade_operacional(
                        self._atividade(), agora=self.monotonic()) and self._sucesso() == sucesso)
            return self._retrato() == retrato
        # Não enfileira/reenvia um gesto descartado; cada etapa revalida a concessão.
        interrompido_por_causa = False
        def rosto_confirmado() -> dict[str, Any]:
            nonlocal interrompido_por_causa
            d = self.corpo.transporte.diagnostico()
            interrompido_por_causa = self._vigente(meta) and not causa_vigente()
            ok = self._vigente(meta) and causa_vigente() and self._olhos_confirmados(d)
            return {"ok": ok, "confirmado": ok, "evidencia": "ack_do_mesmo_retrato_causal"}

        def movimento() -> dict[str, Any]:
            nonlocal interrompido_por_causa
            validar = lambda: self._vigente(meta) and causa_vigente()
            receipts: list[dict[str, Any]] = []
            for indice, motores in enumerate(gesto.movimentos):
                espera = gesto.antecipacao_ms if indice == 0 else gesto.pausa_ms
                if not self._aguardar_gesto(espera, validar):
                    interrompido_por_causa = self._vigente(meta) and not causa_vigente()
                    return {"ok": False, "confirmado": False, "motivo": "gesto_interrompido",
                            "gesto": gesto.nome, "receipts_movimentos": receipts}
                retorno = self.corpo.transporte.mover_corpo(*motores, validar_inicio=validar)
                retorno = self.corpo.confirmar_receipt(retorno, "CORPO_MOVER")
                receipts.append(retorno)
                if not retorno["ok"]:
                    interrompido_por_causa = (retorno.get("motivo") == "concessao_expirada_antes_do_motor"
                                             and self._vigente(meta) and not causa_vigente())
                    return {**retorno, "confirmado": False, "gesto": gesto.nome,
                            "receipts_movimentos": receipts}
            return {"ok": True, "confirmado": True, "gesto": gesto.nome,
                    "receipts_movimentos": receipts, "prova_rotacao": False}

        try:
            retorno = self.coordenador.executar_gesto_corporal(meta, rosto_confirmado, movimento)
        except Exception as erro:
            retorno = {"ok": False, "status": "falha_coordenador_corporal", "motivo": type(erro).__name__}
        if not retorno.get("ok"):
            causa_substituida = interrompido_por_causa and self._vigente(meta)
            falha = not self._revogada.is_set() and not causa_substituida
            if not causa_substituida:
                self.revogar("gesto_nao_confirmado")
            else:
                with self._lock:
                    self._motivo = "gesto_interrompido_por_nova_expressao"
            self.corpo.transporte.parar_corpo()
            if falha and callable(self.corpo.observar_resultado_cb):
                self.corpo.observar_resultado_cb({**retorno, "status": "falha_gesto_corporal", "origem": "executor"})
            if falha and callable(self.corpo.registrar_falha_cb):
                self.corpo.registrar_falha_cb("corpo_motor", "gesto_nao_confirmado")
        self._publicar()
        return retorno

    def executar(self, *, deve_parar: Callable[[], bool], aguardar_fn: Callable[[float], Any]) -> None:
        try:
            while not deve_parar():
                try:
                    self.processar()
                except Exception:
                    self.revogar("falha_presenca_corporal")
                    self.corpo.transporte.parar_corpo()
                if aguardar_fn(.2):
                    break
        finally:
            self.revogar("aplicacao_encerrada")
