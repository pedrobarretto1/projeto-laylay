"""Experiência factual do executor, no estado e aprendizado compartilhados."""
from __future__ import annotations

from copy import deepcopy
import math
import threading
import time
from typing import Any, Callable, Mapping
from uuid import uuid4


class ExperienciaCorporalRuntime:
    def __init__(self, *, estado: Any, diagnostico_getter: Callable[[], Mapping[str, Any]],
                 relatar_falha: Callable[..., Any] | None = None,
                 clock: Callable[[], float] = time.time) -> None:
        self.estado, self.diagnostico_getter = estado, diagnostico_getter
        self.relatar_falha, self.clock = relatar_falha, clock
        self.aprendizado: Any = None
        self._ultimo_erro = ""
        self._lock = threading.RLock()

    def _falha(self, codigo: str, erro: Exception) -> None:
        self._ultimo_erro = codigo
        try:
            if callable(self.relatar_falha):
                self.relatar_falha("corpo_motor", codigo, erro=erro)
        except Exception:
            pass

    def conectar_aprendizado(self, aprendizado: Any) -> None:
        self.aprendizado = aprendizado
        # Recupera observações, nunca sessão ou concessão. Não substitui o vivo.
        try:
            if self.estado is None or self.estado.obter_copia("mental", "historico_corporal", []):
                return
            historico = []
            for h in aprendizado.memoria.listar_hipoteses_aprendizado(limit=500):
                if h.get("tipo") != "execucao_corporal":
                    continue
                for evento in aprendizado.memoria.listar_eventos_aprendizado(h["chave"], limit=3):
                    e = (evento.get("contexto") or {}).get("experiencia")
                    if isinstance(e, dict) and e.get("origem") == "executor_corpo":
                        historico.append({**e, "recuperada_da_memoria": True, "pertence_ao_turno_atual": False})
            historico = sorted({e["id"]: e for e in historico if e.get("id")}.values(), key=lambda e: e["ts"])[-12:]
            if historico:
                self.estado.atualizar_campos("mental", historico_corporal=historico, experiencia_corporal=historico[-1])
        except Exception as erro:
            self._falha("falha_recuperacao_experiencia", erro)

    def iniciar(self, *, nome: str, origem_intencao: str, perfil: str,
                intencao_id: str = "", turno_id: str | None = None,
                variante: int = 0, movimentos: tuple = (), familia: str = "") -> dict[str, Any]:
        mental = self.estado.retrato_dominio("mental") if self.estado is not None else {}
        diag = self.diagnostico_getter()
        return {"id": uuid4().hex, "origem": "executor_corpo", "nome": nome, "familia": familia or nome,
                "origem_intencao": origem_intencao, "perfil": perfil,
                "intencao_id": intencao_id, "turno_id": str(turno_id if turno_id is not None else (mental.get("turno_atual") or {}).get("id", "")),
                "sessao": str(diag.get("sessao") or ""), "iniciada_em": self.clock(),
                "variante": variante % 3, "movimentos": [list(m) for m in movimentos]}

    def registrar(self, ocorrencia: Mapping[str, Any], retorno: Mapping[str, Any],
                  receipts: list[dict[str, Any]], *, parada: bool = False) -> dict[str, Any]:
        if ocorrencia.get("origem") != "executor_corpo" or not ocorrencia.get("id"):
            raise ValueError("experiência exige ocorrência criada pelo executor")
        confirmado = bool(retorno.get("ok") is True and receipts and all(
            r.get("ok") is True and r.get("parada_confirmada") is True
            and (parada or r.get("aplicacao_pwm_confirmada") is True) for r in receipts))
        cancelado = retorno.get("cancelado") is True or retorno.get("status") == "cancelado"
        e = {**dict(ocorrencia), "ts": self.clock(), "confirmado": confirmado,
             "duracao_comandada_confirmada_ms": sum(r.get("duracao_ms", 0) for r in receipts
                 if r.get("aplicacao_pwm_confirmada") is True and type(r.get("duracao_ms")) is int
                 and 0 <= r["duracao_ms"] <= 5000),
             "resultado": "parada_eletrica_confirmada" if confirmado and parada else "pwm_e_parada_confirmados" if confirmado else "interrompida" if cancelado else "gesto_nao_confirmado",
             "motivo": str(retorno.get("motivo") or retorno.get("status") or "")[:120],
             "movimentos_confirmados": sum(r.get("aplicacao_pwm_confirmada") is True for r in receipts),
             "parada_confirmada": bool(receipts and receipts[-1].get("parada_confirmada") is True),
             "prova_deslocamento": False, "autoriza_execucao": False}
        novo = False
        with self._lock:
            if self.estado is not None:
                def publicar(mental):
                    nonlocal novo, e
                    historico = list(mental.get("historico_corporal") or [])
                    if any(item.get("id") == e["id"] for item in historico):
                        return mental
                    novo = True
                    e = {**e, "pertence_ao_turno_atual": bool(e["turno_id"] and str((mental.get("turno_atual") or {}).get("id", "")) == e["turno_id"])}
                    return {**mental, "historico_corporal": (historico + [e])[-12:], "experiencia_corporal": e}
                self.estado.atualizar("mental", publicar)
            else:
                novo = True
            if novo and self.aprendizado is not None:
                try:
                    aprendido = self.aprendizado.registrar_evidencia(
                        chave=f"corpo_execucao:{e['perfil']}:{e['nome']}:{e['variante']}", tipo="execucao_corporal", escopo="corpo_motor",
                        valor={"nome": e["nome"], "perfil": e["perfil"], "variante": e["variante"], "descricao_humana": "confirmação elétrica de gesto, sem observação de deslocamento"},
                        sinal=0 if cancelado else .7 if confirmado else -.8, origem="executor_corpo", evidencia=e["resultado"],
                        contexto={"perfil": e["perfil"], "experiencia": e}, id_evento=f"corpo_execucao:{e['id']}")
                    if aprendido is None:
                        self._ultimo_erro = "falha_persistencia_experiencia"
                    elif self.estado is not None:
                        self._ultimo_erro = ""
                        self.estado.atualizar_campos("mental", aprendizado_corporal={
                            "origem": "aprendizado_compartilhado", "chave": aprendido["chave"],
                            "estado_hipotese": aprendido["status"], "confianca": aprendido["confianca"],
                            "limite_evidencia": "confirmacao_eletrica_sem_deslocamento", "autoriza_execucao": False})
                except Exception as erro:
                    self._falha("falha_aprendizado_experiencia", erro)
        return deepcopy(e)

    def observar_feedback(self, texto: str, *, turno_id: str, referencia_id: str) -> bool:
        from mente_laylay.cognicao.interpretador_continuidade import qualificar_feedback_corporal
        qualificacao = qualificar_feedback_corporal(texto)
        if not qualificacao or not self.aprendizado or self.estado is None or not turno_id or not referencia_id:
            return False
        historico = self.estado.obter_copia("mental", "historico_corporal", [])
        e = next((e for e in reversed(historico) if e.get("id") == referencia_id), {})
        diag = self.diagnostico_getter()
        idade = self.clock() - float(e.get("ts", 0))
        if not e or not math.isfinite(idade) or not 0 <= idade <= 60 or e.get("recuperada_da_memoria") or e.get("sessao") != diag.get("sessao"):
            return False
        if diag.get("aplicacao_confirmada") is not True:
            return False
        fonte = {"dominio": "corpo_motor", "experiencia_id": e["id"], "turno_id": turno_id,
                 "perfil": e["perfil"], "nome": e["nome"], "variante": e["variante"], "autoriza_execucao": False}
        identidade = f"corpo:{turno_id}:{e['id']}"
        tipo, aceito = qualificacao["tipo"], qualificacao["aceito"]
        registro = self.aprendizado.registrar_feedback_contextual(tipo=tipo, aceito=aceito,
            resultado=texto, origem="corpo_motor", alvo=e["nome"], id_evento=identidade, proveniencia=fonte)
        if registro is None:
            return False
        if tipo in {"aceitacao", "recusa"}:
            self.aprendizado.registrar_evidencia(
                chave=f"{'corpo_preferencia' if aceito else 'corpo_evitacao'}:{e['perfil']}:{e.get('familia', e['nome'])}:{e['variante']}", tipo="preferencia_corporal", escopo="corpo_motor",
                valor={"nome": e["nome"], "perfil": e["perfil"], "variante": e["variante"], "direcao": "favorecer" if aceito else "evitar", "descricao_humana": "avaliação do usuário sobre este gesto corporal"},
                # Recusa é evidência a favor de evitar a variante; não falha
                # da hipótese de preferência. O feedback genérico mantém sinal.
                sinal=.45, origem="feedback_usuario", evidencia=texto,
                contexto=fonte, id_evento=f"corpo_preferencia:{identidade}")
        self.estado.atualizar_campos("mental", feedback_corporal={**fonte, "tipo": tipo, "aceito": aceito})
        return True

    def selecionar_variante(self, nome: str, perfil: str, padrao: int) -> int | None:
        historico = self.estado.obter_copia("mental", "historico_corporal", []) if self.estado is not None else []
        sessao = str(self.diagnostico_getter().get("sessao") or "")
        recentes = [e for e in historico[-6:] if e.get("familia") == nome and e.get("perfil") == perfil
                    and e.get("sessao") == sessao and not e.get("recuperada_da_memoria")
                    and (e.get("confirmado") is True or e.get("movimentos_confirmados", 0) > 0)]
        ordem = [(padrao + i) % 3 for i in range(3)]
        # Escolha sobre experiência factual da mesma sessão, sem estimar distância.
        # Não muda a assinatura, os parâmetros ou a autoridade do executor.
        contagens = {v: sum(e.get("variante") == v for e in recentes) for v in ordem}
        ultima = recentes[-1].get("variante") if recentes else None
        ordem.sort(key=lambda v: (v == ultima, contagens[v]))
        if self.aprendizado is None:
            return ordem[0]
        candidatas = []
        evitadas = set()
        try:
            for variante in range(3):
                evitar = f"corpo_evitacao:{perfil}:{nome}:{variante}"
                if self.aprendizado.avaliar_hipotese(evitar).get("aplicavel"):
                    evitadas.add(variante)
                    continue
                chave = f"corpo_preferencia:{perfil}:{nome}:{variante}"
                h = self.aprendizado.memoria.obter_hipotese_aprendizado(chave)
                if not h or h.get("evidencias_positivas", 0) <= h.get("evidencias_negativas", 0):
                    continue
                avaliacao = self.aprendizado.avaliar_hipotese(chave)
                if avaliacao.get("aplicavel"):
                    candidatas.append((h.get("confianca", 0), -ordem.index(variante), variante))
            if candidatas:
                return max(candidatas)[2]
            return next((v for v in ordem if v not in evitadas), None)
        except Exception as erro:
            self._falha("falha_selecao_variante", erro)
            return ordem[0]

    def ritmo_recente(self, *, sessao: str, perfil: str, agora: float | None = None) -> dict[str, Any]:
        """Resumo amostral de comandos confirmados; não estima fadiga ou bateria."""
        agora = self.clock() if agora is None else agora
        historico = self.estado.obter_copia("mental", "historico_corporal", []) if self.estado is not None else []
        motor_ms = gestos = exploracoes = 0
        vistos = set()
        for e in historico[-12:]:
            if (not isinstance(e, Mapping) or not isinstance(e.get("id"), str) or not e["id"]
                or e["id"] in vistos or e.get("origem") != "executor_corpo"
                or e.get("sessao") != sessao or e.get("perfil") != perfil or e.get("recuperada_da_memoria")):
                continue
            try:
                idade = agora - float(e.get("ts", 0))
            except (ValueError, TypeError):
                continue
            if not math.isfinite(idade) or not 0 <= idade <= 180:
                continue
            duracao = e.get("duracao_comandada_confirmada_ms")
            if duracao is None and e.get("confirmado") is True:
                # Compatibilidade com receipts antigos, de coreografia completa.
                duracao = sum(m[2] for m in e.get("movimentos", [])
                    if isinstance(m, (list, tuple)) and len(m) == 3
                    and type(m[2]) is int and 0 <= m[2] <= 5000)
            if type(duracao) is not int or not 0 < duracao <= 20000:
                continue
            vistos.add(e["id"])
            if idade <= 60:
                motor_ms += duracao
            if e.get("confirmado") is True:
                if idade <= 120:
                    gestos += 1
                familia = str(e.get("familia") or e.get("nome") or "")
                if familia.split(":", 1)[0] == "explorar" or familia.startswith("passeio_"):
                    exploracoes += 1
        return {"origem": "ritmo_corporal_observado", "motor_ms_60s": motor_ms,
                "gestos_120s": gestos, "exploracoes_180s": exploracoes,
                "amostra_maxima": 12, "autoriza_execucao": False, "prova_deslocamento": False}

    def retrato(self) -> dict[str, Any]:
        historico = self.estado.obter_copia("mental", "historico_corporal", []) if self.estado is not None else []
        campos = ("id", "nome", "turno_id", "origem_intencao", "perfil", "variante", "resultado", "confirmado", "ts", "prova_deslocamento", "recuperada_da_memoria")
        return {"origem": "experiencia_corporal_observada", "historico_recente": [{k: e[k] for k in campos if k in e} for e in historico[-3:]],
                "aprendizado": self.estado.obter_copia("mental", "aprendizado_corporal", {}) if self.estado is not None else {},
                "feedback": self.estado.obter_copia("mental", "feedback_corporal", {}) if self.estado is not None else {},
                "aprendizado_conectado": self.aprendizado is not None, "autoriza_execucao": False,
                "sensores_fisicos": False, "ultimo_erro": self._ultimo_erro}


def criar_experiencia_corporal_runtime(**kwargs: Any) -> ExperienciaCorporalRuntime:
    return ExperienciaCorporalRuntime(**kwargs)
