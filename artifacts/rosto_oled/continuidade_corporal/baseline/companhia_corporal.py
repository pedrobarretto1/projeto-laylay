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
from mente_laylay.cognicao.decisao_corporal import decidir_intencao_corporal
from mente_laylay.cognicao.modelo_corporal import proposta_corporal_vigente
from mente_laylay.cognicao.decisao_turno import motivo_incoerencia_contratos_turno
from mente_laylay.memoria_mental.atividade_operacional_runtime import (
    projetar_sucesso_operacional, projetar_atividade_operacional, projetar_falha_operacional, projetar_execucao_operacional,
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
                 perfil_corporal: str = "bancada",
                 prioridade_interacao_getter: Callable[[], bool] | None = None,
                 monotonic: Callable[[], float] = time.monotonic) -> None:
        self.corpo, self.estado, self.monotonic = corpo, estado, monotonic
        if perfil_corporal not in {"bancada", "rodas_suspensas"}:
            raise ValueError("perfil_corporal_invalido")
        self.perfil_corporal = perfil_corporal
        self.prioridade_interacao_getter = prioridade_interacao_getter or (lambda: False)
        self._variantes: dict[str, int] = {}
        self._intencao: dict[str, Any] = {}
        self._falha_observada = 0
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
            self.estado.atualizar_campos("mental", intencao_corporal={
                **self._intencao, "origem": "owner_companhia_corporal",
                "perfil": self.perfil_corporal, "autoriza_execucao": False,
                "prova_deslocamento": False,
            })

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            concessao = dict(self._concessao or {})
            ativa = bool(concessao and not self._revogada.is_set())
            return {"ativa": ativa, "motivo": self._motivo, "transporte_exigido": "serial",
                    "ttl_maximo_s": None, "gestos_maximos": None, "gestos_emitidos": concessao.get("gestos", 0),
                    "intervalo_minimo_s": INTERVALO_GESTOS_S, "pwm_gestos": 230 if self.perfil_corporal == "rodas_suspensas" else 100,
                    "duracao_maxima_gesto_ms": 5000 if self.perfil_corporal == "rodas_suspensas" else DURACAO_MOTOR_GESTO_MS,
                    "duracao_planejada_maxima_coreografia_ms": 16000 if self.perfil_corporal == "rodas_suspensas" else DURACAO_PLANEJADA_GESTO_MS,
                    "movimentos_maximos_por_gesto": 4,
                    "perfil_expressivo": "presenca_coordenada_v2" if self.perfil_corporal == "rodas_suspensas" else "ritmo_emocional_v2",
                    "perfil_corporal": self.perfil_corporal,
                    "intencao": dict(self._intencao),
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
        if self.perfil_corporal == "rodas_suspensas" and (diag.get("motor") or {}).get("duracao_maxima_ms", 500) < 5000:
            self._motivo = "rodas_suspensas_requer_firmware_longo"
            self._publicar()
            return {"ok": False, "motivo": self._motivo}
        retrato = self._retrato()
        with self._lock:
            # STOP pode chegar enquanto a consulta de transporte está em andamento.
            if automatica and not self._ativacao_pendente:
                return {"ok": False, "motivo": "ativacao_automatica_revogada"}
            self._concessao = {"id": secrets.token_hex(8), "sessao": diag["sessao"],
                              "origem": "configuracao_explicita_de_bancada" if automatica else "concessao_explicita_de_sessao",
                              "gestos": 0, "ultimo_gesto": self.monotonic() - INTERVALO_GESTOS_S,
                              "passeio": passeio,
                              "perfil": self.perfil_corporal,
                              "proximo_passeio": self.monotonic() + 8}
            self._ativacao_pendente = False
            self._observado = retrato  # Não reproduz a emoção anterior à concessão.
            self._sucesso_observado = (self._sucesso() or (0, 0))[0]
            self._falha_observada = (projetar_falha_operacional(self._atividade(), agora=self.monotonic()) or (0, 0))[0]
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
                        and 0 <= agora - float(meta.get("proposto_em", -100)) <= (20 if c.get("perfil") == "rodas_suspensas" else 5)
                        and meta.get("perfil", "bancada") == c.get("perfil", "bancada")
                        and diag.get("transporte") == "serial" and diag.get("aplicacao_confirmada") is True
                        and (diag.get("motor") or {}).get("disponivel") is True)

    def _aguardar_gesto(self, ms: int, validar: Callable[[], bool]) -> bool:
        # Nenhum lock de transporte durante a pausa; revogação acorda de imediato.
        return validar() and not self._revogada.wait(ms / 1000) and validar()

    def _conversa(self) -> dict[str, Any]:
        return self.estado.retrato_dominio("conversacional") if self.estado is not None else {}

    def _atencao_prioritaria(self) -> bool:
        try:
            return self.prioridade_interacao_getter() is True and self._conversa().get("audio_playing") is not True
        except Exception:
            return True  # Falha de leitura não concede iniciativa.

    def _assinatura_contexto(self) -> tuple[Any, ...]:
        a = self._atividade()
        plano = self._plano_pc()
        d = decidir_intencao_corporal(self._conversa(), a, permitir_passeio=True,
            agora=self.monotonic(), plano=plano, interacao_prioritaria=self._atencao_prioritaria())
        return self._retrato(), d.nome, a.get("falha_id", 0), a.get("sucesso_id", 0), plano.get("id", ""), (plano.get("intencao_corporal") or {}).get("id", "")

    def _plano_pc(self) -> dict[str, Any]:
        return self.estado.obter_copia("mental", "plano_turno_atual", {}) if self.estado is not None else {}

    def _proposta_mente(self, concessao: Mapping[str, Any]) -> dict[str, Any]:
        mental = self.estado.retrato_dominio("mental") if self.estado is not None else {}
        plano = mental.get("plano_turno_atual") or {}
        if motivo_incoerencia_contratos_turno(mental.get("turno_atual"), plano, mental.get("retrato_turno_atual")):
            return {}
        return proposta_corporal_vigente(plano, concessao, agora=self.monotonic())

    def _reservar_proposta(self, proposta: Mapping[str, Any], concessao: Mapping[str, Any]) -> bool:
        reservada = False
        def reservar(mental):
            nonlocal reservada
            plano = dict(mental.get("plano_turno_atual") or {})
            p = proposta_corporal_vigente(plano, concessao, agora=self.monotonic())
            if (p.get("id") != proposta.get("id") or p.get("estado") != "proposta"
                    or motivo_incoerencia_contratos_turno(mental.get("turno_atual"), plano, mental.get("retrato_turno_atual"))):
                return mental
            reservada = True
            return {**mental, "plano_turno_atual": {**plano, "intencao_corporal": {**p, "estado": "executando"}}}
        self.estado.atualizar("mental", reservar)
        return reservada

    def _devolver_experiencia(self, proposta: Mapping[str, Any], retorno: Mapping[str, Any], receipts: list[dict[str, Any]], *, ocorrencia: Mapping[str, Any] | None = None) -> None:
        ocorrencia = ocorrencia or self.corpo.experiencias.iniciar(nome=proposta["nome"], origem_intencao="llm_principal",
            perfil=self.perfil_corporal, turno_id=proposta["turno_id"], intencao_id=proposta["id"])
        experiencia = self.corpo.registrar_experiencia(ocorrencia, retorno, receipts)
        if not experiencia:
            return
        confirmado = experiencia["confirmado"]
        def concluir(mental):
            plano = dict(mental.get("plano_turno_atual") or {})
            p = dict(plano.get("intencao_corporal") or {})
            vigente = (str(plano.get("id")) == proposta["plano_id"] and p.get("id") == proposta["id"]
                and not motivo_incoerencia_contratos_turno(mental.get("turno_atual"), plano, mental.get("retrato_turno_atual")))
            # Experiência tem um writer; esta transação só conclui a proposta.
            novo = {**mental}
            if vigente:
                novo["plano_turno_atual"] = {**plano, "intencao_corporal": {**p,
                    "estado": "concluida" if confirmado else "interrompida", "resultado": experiencia}}
            return novo
        self.estado.atualizar("mental", concluir)

    def _registrar_intencao(self, decisao: Any) -> None:
        agora = self.monotonic()
        chave = (decisao.nome, decisao.emocao, decisao.nivel)
        if (tuple(self._intencao.get("chave", ())) != chave
                or agora >= self._intencao.get("ate_monotonic", 0)):
            self._intencao = {"id": secrets.token_hex(6), "nome": decisao.nome,
                "motivo": decisao.motivo, "prioridade": decisao.prioridade,
                "desde_monotonic": agora, "ate_monotonic": agora + 12,
                "chave": chave, "candidata_a_movimento": decisao.permite_movimento,
                "estado": "proposta"}
        self._publicar()

    def _gesto_suspenso(self, decisao: Any, retrato: tuple[int, int, int], *, variante: int = 0) -> GestoCorporal | None:
        base = self._gesto_suspenso_base(decisao, retrato, variante=variante)
        if base is None:
            return None
        # Variações finitas por estilo: mantém a assinatura, muda lado e ritmo.
        escala = (1.0, .88, 1.12)[variante % 3]
        espelhar = variante % 3 == 1
        movimentos = tuple((d if espelhar else e, e if espelhar else d,
                            max(50, min(5000, round(ms * escala)))) for e, d, ms in base.movimentos)
        return GestoCorporal(f"{base.nome}_v{variante % 3 + 1}",
                             round(base.antecipacao_ms * escala), movimentos, round(base.pausa_ms * escala))

    def _gesto_suspenso_base(self, decisao: Any, retrato: tuple[int, int, int], *, variante: int = 0) -> GestoCorporal | None:
        nivel, emo = retrato[1], retrato[0]
        forte = min(230, 110 + 35 * nivel)
        if variante % 3 == 2:
            # Uma frase distinta após as duas primeiras reações. A causa e a
            # concessão continuam sendo revalidadas pelo mesmo coordenador.
            frases = {
                "comemorar": ((forte, forte, 650), (-forte, forte, 900), (forte, -forte, 1800), (-forte, forte, 900)),
                "reagir_falha": ((-110, -110, 650), (-130, 130, 700), (130, -130, 1100)),
                "interagir": ((120, 120, 250), (-120, 120, 450)),
                "explorar": ((-150, 150, 1100), (160, 160, 3200), (150, -150, 1300)),
            }
            emocionais = {
                1: ((-120, -120, 450), (forte, -forte, 950), (-forte, forte, 1900), (forte, forte, 600)),
                2: ((-110, -110, 1200), (-110, 110, 550)),
                3: ((forte, -forte, 1100), (-forte, forte, 1100), (-130, -130, 650)),
                4: ((-120, -120, 450), (-forte, forte, 1200), (forte, -forte, 450)),
                5: ((-150, -150, 750), (120, -120, 500), (120, 120, 300)),
                6: ((-110, -110, 500), (-115, 115, 700), (115, -115, 1100)),
                7: ((140, -140, 1200), (-110, -110, 400), (-140, 140, 550)),
            }
            movimentos = emocionais.get(emo) if decisao.nome == "expressar" else frases.get(decisao.nome)
            if movimentos:
                return GestoCorporal(f"{decisao.nome}_frase", 180 if emo == 6 else 100,
                                    movimentos, 180 if emo in {2, 6} else 100)
        if decisao.nome == "comemorar":
            return GestoCorporal("comemoracao_suspensa", 120,
                ((forte, -forte, 2500), (-forte, forte, 1800), (forte, forte, 1500)), 140)
        if decisao.nome == "reagir_falha":
            return GestoCorporal("descontentamento_suspenso", 150,
                ((-130, 130, 900), (130, -130, 900), (-110, -110, 900)), 180)
        if decisao.nome == "interagir":
            return GestoCorporal("atencao_conversa", 80, ((-120, 120, 500), (120, -120, 350)), 160)
        if decisao.nome == "explorar":
            if self._passeios % 2:
                return GestoCorporal("exploracao_curva_suspensa", 100,
                    ((150, -150, 1800), (160, 160, 3500), (-140, -140, 1000)), 180)
            return GestoCorporal("exploracao_avanco_suspensa", 100,
                ((160, 160, 3500), (-150, 150, 1800), (150, 150, 2000)), 180)
        if decisao.nome != "expressar":
            return None
        if emo in {1, 7}:
            return GestoCorporal("alegria_suspensa", 100,
                ((forte, -forte, 1800), (-forte, forte, 2200), (forte, forte, 1200)), 160)
        if emo == 2:
            return GestoCorporal("recolhimento_suspenso", 280, ((-110, -110, 1800),))
        if emo in {3, 4}:
            return GestoCorporal("negacao_firme_suspensa", 100,
                ((forte, -forte, 1700), (-forte, forte, 1700), (forte, -forte, 1200)), 150)
        if emo == 6:
            return GestoCorporal("hesitacao_suspensa", 220,
                ((-115, 115, 900), (115, -115, 700), (-110, -110, 1000)), 300)
        if emo == 5:
            return GestoCorporal("surpresa_suspensa", 0, ((-150, -150, 1400),))
        return None

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
        atividade = self._atividade()
        ocupada = projetar_atividade_operacional(atividade, agora=self.monotonic())
        sucesso = self._sucesso()
        novo_sucesso = bool(sucesso and sucesso[0] != self._sucesso_observado)
        falha = projetar_falha_operacional(atividade, agora=self.monotonic())
        nova_falha = bool(falha and falha[0] != self._falha_observada)
        proposta = self._proposta_mente(c)
        decisao = decidir_intencao_corporal(self._conversa(), atividade,
            permitir_passeio=bool(c.get("passeio")), nova_emocao=retrato[:2] != anterior[:2],
            novo_sucesso=novo_sucesso, nova_falha=nova_falha, agora=self.monotonic(),
            interacao_prioritaria=self._atencao_prioritaria(),
            plano=self._plano_pc() if self.perfil_corporal == "rodas_suspensas" or proposta else None,
            proposta_corporal=proposta)
        self._registrar_intencao(decisao)
        if self._atencao_prioritaria() or projetar_execucao_operacional(atividade) or ((self.perfil_corporal == "rodas_suspensas" or proposta) and not decisao.permite_movimento):
            return {"ok": False, "motivo": "atividade_pc_prioritaria" if projetar_execucao_operacional(atividade) else decisao.motivo}
        self._observado = retrato
        contexto_inicial = self._assinatura_contexto()
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
        if self.perfil_corporal == "rodas_suspensas":
            origem_gesto = {"comemorar": "sucesso_operacional", "explorar": "passeio", "interagir": "fala",
                            "reagir_falha": "falha_operacional"}.get(decisao.nome, "emocao")
            if not decisao.proposta_id and (origem_gesto == "passeio" and self.monotonic() < c["proximo_passeio"]
                    or origem_gesto == "fala" and anterior[2] == retrato[2]):
                return {"ok": False, "motivo": "intencao_em_acomodacao"}
            chave_variante = f"{decisao.nome}:{retrato[0]}"
            variante = self._variantes.get(chave_variante, 0)
            variante = self.corpo.experiencias.selecionar_variante(chave_variante, self.perfil_corporal, variante)
            if variante is None:
                return {"ok": False, "motivo": "sem_variante_compativel_com_preferencia"}
            gesto = self._gesto_suspenso(decisao, retrato, variante=variante)
        elif decisao.proposta_id:
            origem_gesto = "mente"
            gesto = (selecionar_gesto(retrato[0], retrato[1]) if decisao.nome == "expressar" else
                COMEMORACOES[self._comemoracoes % len(COMEMORACOES)] if decisao.nome == "comemorar" else
                PASSEIOS[self._passeios % len(PASSEIOS)] if decisao.nome == "explorar" else
                GestoCorporal("interacao_mente", 60, ((100, -100, 150),)) if decisao.nome == "interagir" else
                GESTOS[4] if decisao.nome == "reagir_falha" else None)
        if gesto is None or self.monotonic() - c["ultimo_gesto"] < INTERVALO_GESTOS_S:
            return {"ok": False, "motivo": "sem_gesto_novo_ou_em_intervalo"}
        if decisao.proposta_id:
            if not self._reservar_proposta(proposta, c):
                return {"ok": False, "motivo": "proposta_corporal_substituida_ou_consumida"}
            origem_gesto = "mente"
        meta = {"concessao_id": c["id"], "proposto_em": self.monotonic(), "gesto": gesto.nome,
                "perfil": self.perfil_corporal, "intencao_id": decisao.proposta_id or self._intencao.get("id", ""),
                "turno_id": proposta.get("turno_id", ""), "origem_intencao": "llm_principal" if decisao.proposta_id else "mente_causal"}
        ocorrencia = self.corpo.experiencias.iniciar(nome=gesto.nome, origem_intencao=meta["origem_intencao"],
            perfil=self.perfil_corporal, intencao_id=meta["intencao_id"],
            turno_id=proposta.get("turno_id") if decisao.proposta_id else None,
            variante=variante if self.perfil_corporal == "rodas_suspensas" else 0,
            familia=chave_variante if self.perfil_corporal == "rodas_suspensas" else gesto.nome,
            movimentos=gesto.movimentos)
        meta["experiencia_id"] = ocorrencia["id"]
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
            elif origem_gesto == "falha_operacional":
                self._falha_observada = falha[0]
            self._intencao["estado"] = "executando"
            if self.perfil_corporal == "rodas_suspensas":
                self._variantes[chave_variante] = self._variantes.get(chave_variante, 0) + 1
        falha_inicial = atividade.get("falha_id", 0)
        def causa_vigente() -> bool:
            if self._atencao_prioritaria() or projetar_execucao_operacional(self._atividade()):
                return False
            if self.perfil_corporal == "rodas_suspensas" and self._assinatura_contexto() != contexto_inicial:
                return False
            if decisao.proposta_id and self._proposta_mente(c).get("id") != decisao.proposta_id:
                return False
            if origem_gesto == "sucesso_operacional":
                return self._sucesso() == sucesso and self._atividade().get("falha_id", 0) == falha_inicial
            if origem_gesto == "passeio":
                return (self._retrato() == retrato and not projetar_atividade_operacional(
                        self._atividade(), agora=self.monotonic()) and self._sucesso() == sucesso)
            return self._retrato() == retrato
        # Não enfileira/reenvia um gesto descartado; cada etapa revalida a concessão.
        interrompido_por_causa = False
        receipts_mente: list[dict[str, Any]] = []
        estilo = {"comemorar": 1, "reagir_falha": 4, "explorar": 10, "interagir": 0}.get(decisao.nome, retrato[0])
        coordenar = self.perfil_corporal == "rodas_suspensas" and diag.get("expressao", {}).get("suportado") is True
        def expressar(fase: int, e: int = 0, d: int = 0, duracao: int = 1800) -> dict[str, Any]:
            if not coordenar:
                return {"ok": True, "suportado": False}
            lado = 0 if e == d else 1 if e > d else -1
            return self.corpo.transporte.expressar_gesto(estilo, fase, lado, duracao,
                validar_inicio=lambda: self._vigente(meta) and causa_vigente(), tocar_som=fase == 1)
        def rosto_confirmado() -> dict[str, Any]:
            nonlocal interrompido_por_causa
            d = self.corpo.transporte.diagnostico()
            interrompido_por_causa = self._vigente(meta) and not causa_vigente()
            ok = self._vigente(meta) and causa_vigente() and self._olhos_confirmados(d)
            cue = expressar(0, *gesto.movimentos[0][:2], max(300, gesto.antecipacao_ms + 300)) if ok else {}
            ok = ok and cue.get("ok") is True
            return {"ok": ok, "confirmado": ok, "evidencia": "ack_do_mesmo_retrato_causal", "expressao": cue}

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
                cue = expressar(1, motores[0], motores[1], min(6000, motores[2] + 250))
                if not cue.get("ok"):
                    return {"ok": False, "confirmado": False, "motivo": "expressao_nao_confirmada", "expressao": cue}
                kwargs_movimento = {"suave": True} if coordenar and diag.get("motor", {}).get("rampa_suportada") is True else {}
                retorno = self.corpo.transporte.mover_corpo(*motores, validar_inicio=validar, **kwargs_movimento)
                retorno = self.corpo.confirmar_receipt(retorno, "CORPO_MOVER")
                receipts.append(retorno)
                receipts_mente.append(retorno)
                if not retorno["ok"]:
                    interrompido_por_causa = (retorno.get("motivo") == "concessao_expirada_antes_do_motor"
                                             and self._vigente(meta) and not causa_vigente())
                    return {**retorno, "confirmado": False, "gesto": gesto.nome,
                            "receipts_movimentos": receipts}
            acomodacao = expressar(2)
            return {"ok": acomodacao.get("ok") is True, "confirmado": acomodacao.get("ok") is True, "gesto": gesto.nome,
                    "acomodacao": acomodacao,
                    "receipts_movimentos": receipts, "prova_rotacao": False}

        falha_gesto = False
        try:
            retorno = self.coordenador.executar_gesto_corporal(meta, rosto_confirmado, movimento)
        except Exception as erro:
            retorno = {"ok": False, "status": "falha_coordenador_corporal", "motivo": type(erro).__name__}
        if not retorno.get("ok"):
            causa_substituida = interrompido_por_causa and self._vigente(meta)
            falha = not self._revogada.is_set() and not causa_substituida
            falha_gesto = falha
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
        self._intencao["estado"] = "concluida" if retorno.get("ok") else "interrompida"
        retorno_experiencia = {**retorno, **({"cancelado": True} if not retorno.get("ok") and not falha_gesto else {})}
        if decisao.proposta_id:
            self._devolver_experiencia(proposta, retorno_experiencia, receipts_mente, ocorrencia=ocorrencia)
        else:
            self.corpo.registrar_experiencia(ocorrencia, retorno_experiencia, receipts_mente)
        if self.perfil_corporal == "rodas_suspensas" and retorno.get("ok"):
            # A acomodação começa depois da coreografia longa, não durante ela.
            with self._lock:
                if self._concessao and self._concessao["id"] == c["id"]:
                    self._concessao["proximo_passeio"] = self.monotonic() + (8, 12, 10, 14)[self._passeios % 4]
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
