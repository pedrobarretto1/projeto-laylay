"""Intenção corporal derivada da mente; não concede movimento ou escreve estado."""
from __future__ import annotations
from dataclasses import dataclass
import time
import math
from typing import Any, Mapping
from mente_laylay.especialistas.rosto_oled_runtime import projetar_rosto
from mente_laylay.integracao.politicas_composicao import construir_estado_visual
from mente_laylay.cognicao.modelo_corporal import resultado_operacional_do_plano
from mente_laylay.memoria_mental.atividade_operacional_runtime import (
    projetar_execucao_operacional, projetar_sucesso_operacional, projetar_falha_operacional,
)


@dataclass(frozen=True)
class IntencaoCorporal:
    nome: str
    motivo: str
    prioridade: int
    emocao: int
    nivel: int
    permite_movimento: bool = False  # Candidata; concessão ainda é obrigatória.
    proposta_id: str = ""
    pontuacoes: tuple[tuple[str, int], ...] = ()
    duracao_momento_s: int = 0


def _decidir_ritmo(ritmo: Mapping[str, Any], emocao: int, nivel: int, agora: float) -> IntencaoCorporal:
    carga = max(0, int(ritmo.get("motor_ms_60s", 0)))
    repeticoes = max(0, int(ritmo.get("exploracoes_180s", 0)))
    gestos = max(0, int(ritmo.get("gestos_120s", 0)))
    livre = max(0, float(ritmo.get("tempo_sem_gesto_s", 0)))
    pontos = {"atenta": 55, "descansar": 44 + min(30, gestos * 4 + carga // 1500),
              "explorar": 30 + min(40, int(livre / 2)) - min(40, repeticoes * 10) - min(30, carga // 1500)}
    if ritmo.get("primeira_iniciativa") is True:
        pontos["explorar"] += 30
    if emocao == 1 and nivel >= 2:
        pontos["explorar"] += 10
    if carga >= 20000:
        escolhido, motivo = "descansar", "orcamento_de_movimento_recente"
    elif (ritmo.get("momento_nome") in {"atenta", "descansar"}
          and float(ritmo.get("momento_ate", 0)) > agora):
        escolhido = ritmo["momento_nome"]
        motivo = "equilibrio_observar" if escolhido == "atenta" else "equilibrio_descansar"
    else:
        escolhido = max(pontos, key=pontos.get)
        motivo = "equilibrio_observar" if escolhido == "atenta" else "equilibrio_" + escolhido
    duracao = 30 + min(30, gestos * 5 + carga // 1000) if escolhido == "atenta" else 45 + min(45, gestos * 6 + carga // 1000)
    return IntencaoCorporal(escolhido, motivo, 30, emocao, nivel, escolhido == "explorar",
        pontuacoes=tuple(pontos.items()), duracao_momento_s=duracao)


def decidir_intencao_corporal(conversa: Mapping[str, Any], atividade: Mapping[str, Any], *,
                             permitir_passeio: bool, nova_emocao: bool = False,
                             novo_sucesso: bool = False, nova_falha: bool = False,
                             interacao_prioritaria: bool = False,
                             passeio_em_repouso: bool = False,
                             ritmo_corporal: Mapping[str, Any] | None = None,
                             plano: Mapping[str, Any] | None = None,
                             proposta_corporal: Mapping[str, Any] | None = None,
                             agora: float | None = None, wall_time: float | None = None) -> IntencaoCorporal:
    """Atividade PC → oportunidade, emoção causal → estilo, receipt → reação."""
    agora = time.monotonic() if agora is None else agora
    emocao, nivel, _ = projetar_rosto(conversa)
    def resultado(nome: str, motivo: str, prioridade: int, mover: bool = False, proposta_id: str = "") -> IntencaoCorporal:
        if mover and ritmo_corporal and ritmo_corporal.get("origem") == "ritmo_corporal_observado" and ritmo_corporal.get("motor_ms_60s", 0) >= 20000:
            return _decidir_ritmo(ritmo_corporal, emocao, nivel, agora)
        return IntencaoCorporal(nome, motivo, prioridade, emocao, nivel, mover, proposta_id)
    try:
        visual = construir_estado_visual(conversa_get=lambda c, p=None: conversa.get(c, p),
            plano_get=lambda: plano or {}, time_fn=lambda: time.time() if wall_time is None else wall_time)
    except (ValueError, TypeError, OverflowError):
        return resultado("atenta", "contexto_pc_invalido", 100)
    ocupada = projetar_execucao_operacional(atividade)
    if ocupada or (interacao_prioritaria and not visual["speaking"]) or visual["activity"] in {"thinking", "executing", "listening", "preparando", "processando"}:
        return resultado("atenta", "atividade_pc_em_andamento", 100)
    if ritmo_corporal is not None:
        inteiros = ("motor_ms_60s", "gestos_120s", "exploracoes_180s")
        tempos = ("tempo_sem_gesto_s", "momento_ate")
        if (ritmo_corporal.get("origem") != "ritmo_corporal_observado"
            or any(type(ritmo_corporal.get(k, 0)) is not int or ritmo_corporal.get(k, 0) < 0 for k in inteiros)
            or any(type(ritmo_corporal.get(k, 0)) not in {int, float}
                   or not math.isfinite(ritmo_corporal.get(k, 0)) or ritmo_corporal.get(k, 0) < 0 for k in tempos)):
            return resultado("atenta", "ritmo_corporal_sem_fonte_ou_invalido", 35)
    if proposta_corporal:
        # O owner já conferiu ocorrência, sessão, concessão e prazo. Aqui só
        # escolhemos o momento, usando fatos do mesmo plano e emoção causal.
        nome = proposta_corporal["nome"]
        pid = str(proposta_corporal["id"])
        if nome in {"descansar", "atenta"}:
            return resultado(nome, "intencao_da_mente", 95, proposta_id=pid)
        if nome == "interagir" and not (visual["speaking"] or conversa.get("is_speaking") is True):
            return resultado("atenta", "aguardando_fala_do_turno", 95)
        if nome in {"comemorar", "reagir_falha"} and not resultado_operacional_do_plano(plano or {}, sucesso=nome == "comemorar"):
            return resultado("atenta", "aguardando_resultado_do_mesmo_plano", 95)
        if nome == "expressar" and (not emocao or nivel < 2):
            return resultado("atenta", "aguardando_emocao_causal", 95)
        if nome == "explorar" and (not permitir_passeio or visual["speaking"]):
            return resultado("atenta", "passeio_sem_oportunidade_ou_concessao", 95)
        return resultado(nome, "intencao_da_mente", 95, True, pid)
    if visual["speaking"] or conversa.get("is_speaking") is True:
        return resultado("interagir", "conversa_em_andamento", 90, True)
    if nova_falha and projetar_falha_operacional(atividade, agora=agora):
        return resultado("reagir_falha", "falha_operacional_observada", 85, True)
    if novo_sucesso and projetar_sucesso_operacional(atividade, agora=agora):
        return resultado("comemorar", "sucesso_operacional_confirmado", 80, True)
    if nova_emocao and emocao and nivel >= 2:
        return resultado("expressar", "mudanca_emocional_causal", 70, True)
    if emocao in {2, 8}:
        return resultado("descansar", "acomodacao_emocional", 40)
    if permitir_passeio and passeio_em_repouso:
        return resultado("descansar", "repouso_espontaneo", 35)
    if permitir_passeio and ritmo_corporal is not None:
        return _decidir_ritmo(ritmo_corporal, emocao, nivel, agora)
    if permitir_passeio:
        return resultado("explorar", "disponivel_para_passeio_concedido", 30, True)
    return resultado("descansar", "sem_intencao_de_movimento", 10)
