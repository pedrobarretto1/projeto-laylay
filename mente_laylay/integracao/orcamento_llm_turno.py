"""Orçamento único e seguro para chamadas de modelo no mesmo turno."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
import hashlib
import re
import threading
import time
from typing import Any, Callable


TIPOS_CHAMADA_LLM = frozenset({
    "principal",
    "interpretacao",
    "reparo_json",
    "reparo_factual",
    "continuacao",
    "reparo_comunicacao",
    "autoria_operacional",
})
TIPOS_REPARO_LLM = frozenset({
    "reparo_json",
    "reparo_factual",
    "continuacao",
    "reparo_comunicacao",
})
TIPOS_CHAMADA_SECUNDARIA_LLM = TIPOS_REPARO_LLM | {"autoria_operacional"}
LIMITES_CLASSE_S = {
    "rapida": 8.0,
    "normal": 20.0,
    "contextual": 30.0,
    "longa": 60.0,
}

# Uma chamada de reparo/autoria com menos tempo que isso tende apenas a gerar
# um timeout de 1–2 segundos e a degradar a telemetria. Nessas condições, a
# resposta determinística já pronta é mais correta e mais rápida.
FATIA_MINIMA_CHAMADA_SECUNDARIA_S = 3.0


def _codigo(valor: Any, padrao: str = "desconhecido", limite: int = 72) -> str:
    texto = str(valor or "").strip().casefold()
    permitido = "".join(
        caractere for caractere in texto
        if caractere.isalnum() or caractere in "_.:-"
    )
    return (permitido or padrao)[:limite]


def _tipo_chamada(valor: Any) -> str:
    tipo = _codigo(valor, "principal", 48)
    aliases = {
        "continuação": "continuacao",
        "reparo_comunicação": "reparo_comunicacao",
        "interpretação": "interpretacao",
    }
    tipo = aliases.get(tipo, tipo)
    return tipo if tipo in TIPOS_CHAMADA_LLM else "principal"


def _chave_turno(valor: Any) -> str:
    """Preserva traces técnicos e torna qualquer outro identificador opaco."""
    texto = str(valor or "").strip().casefold()
    if re.fullmatch(r"(?:turno|resposta-ia)-\d{1,12}", texto):
        return texto
    if not texto:
        return "turno-desconhecido"
    resumo = hashlib.blake2s(texto.encode("utf-8"), digest_size=8).hexdigest()
    return f"turno-opaco-{resumo}"


def _classe_timeout(valor: Any) -> str:
    classe = _codigo(valor, "normal", 16)
    aliases = {"rápida": "rapida", "rápido": "rapida", "longo": "longa"}
    classe = aliases.get(classe, classe)
    return classe if classe in LIMITES_CLASSE_S else "normal"


@dataclass(frozen=True)
class DecisaoOrcamentoLLM:
    permitida: bool
    motivo: str
    chamada_id: str = ""
    turno_id: str = ""
    geracao: int = 0
    tipo_chamada: str = "principal"
    timeout_s: float | None = None
    probe_circuito: bool = False


class OrcamentoLLMTurnoRuntime:
    """Limita chamadas sem conhecer prompts, respostas ou ações do usuário."""

    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        publicar_estado: Callable[[dict[str, Any]], Any] | None = None,
        registrar_decisao: Callable[..., Any] | None = None,
        log: Callable[[str], Any] | None = None,
        habilitado: bool = True,
        max_chamadas_turno: int = 2,
        falhas_para_abrir_circuito: int = 3,
        cooldown_circuito_s: float = 15.0,
        limite_turnos: int = 64,
    ) -> None:
        self.monotonic = monotonic
        self.publicar_estado = publicar_estado
        self.registrar_decisao = registrar_decisao
        self.log = log
        self.habilitado = bool(habilitado)
        self.max_chamadas_turno = max(1, min(int(max_chamadas_turno), 4))
        self.falhas_para_abrir_circuito = max(2, int(falhas_para_abrir_circuito))
        self.cooldown_circuito_s = max(1.0, float(cooldown_circuito_s))
        self.limite_turnos = max(8, int(limite_turnos))
        self._lock = threading.RLock()
        self._turno_contexto: ContextVar[str] = ContextVar(
            f"laylay_orcamento_llm_{id(self)}", default="",
        )
        self._turnos: dict[str, dict[str, Any]] = {}
        self._ordem_turnos: list[str] = []
        self._geracao = 0
        self._sequencia_chamadas = 0
        self._chamadas_autorizadas = 0
        self._chamadas_bloqueadas = 0
        self._bloqueios_por_motivo: dict[str, int] = {}
        self._chamadas_por_tipo: dict[str, int] = {}
        self._falhas_consecutivas = 0
        self._circuito_ate = 0.0
        self._probe_circuito_ativo = False

    def _publicar(self) -> None:
        if not callable(self.publicar_estado):
            return
        try:
            self.publicar_estado(self.diagnostico())
        except Exception:
            pass

    def _decisao(self, acao: str, motivo: str, *, tipo: str) -> None:
        if callable(self.registrar_decisao):
            try:
                self.registrar_decisao(
                    "orcamento_llm",
                    acao,
                    (motivo,),
                    categoria=tipo,
                )
            except Exception:
                pass

    def _registrar_bloqueio(self, motivo: str, tipo: str) -> DecisaoOrcamentoLLM:
        self._chamadas_bloqueadas += 1
        self._bloqueios_por_motivo[motivo] = (
            int(self._bloqueios_por_motivo.get(motivo) or 0) + 1
        )
        self._decisao("bloquear", motivo, tipo=tipo)
        if callable(self.log):
            try:
                self.log(
                    "⚡ [IA:ORÇAMENTO] chamada evitada | "
                    f"tipo={tipo} motivo={motivo}"
                )
            except Exception:
                pass
        self._publicar()
        return DecisaoOrcamentoLLM(False, motivo, tipo_chamada=tipo)

    def iniciar_turno(
        self,
        turno_id: Any,
        *,
        classe: str = "normal",
        ainda_atual_cb: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        if not self.habilitado:
            return {"modo": "desativado"}
        chave = _chave_turno(turno_id)
        classe_limpa = _classe_timeout(classe)
        agora = float(self.monotonic())
        with self._lock:
            self._geracao += 1
            estado = {
                "turno_id": chave,
                "geracao": self._geracao,
                "classe": classe_limpa,
                "inicio": agora,
                "prazo": agora + LIMITES_CLASSE_S[classe_limpa],
                "ativo": True,
                "finalizado": False,
                "ainda_atual_cb": ainda_atual_cb,
                "chamadas": [],
            }
            self._turnos[chave] = estado
            if chave in self._ordem_turnos:
                self._ordem_turnos.remove(chave)
            self._ordem_turnos.append(chave)
            while len(self._ordem_turnos) > self.limite_turnos:
                antigo = self._ordem_turnos.pop(0)
                self._turnos.pop(antigo, None)
            self._turno_contexto.set(chave)
        self._publicar()
        return self._retrato_turno(estado)

    def configurar_turno(self, *, classe: str) -> bool:
        if not self.habilitado:
            return False
        chave = self._turno_contexto.get()
        classe_limpa = _classe_timeout(classe)
        with self._lock:
            estado = self._turnos.get(chave)
            if not estado or not estado.get("ativo"):
                return False
            limite = LIMITES_CLASSE_S[classe_limpa]
            # Uma tarefa longa só pode ampliar o prazo antes da primeira
            # chamada. Uma classificação rápida sempre pode encurtá-lo.
            if classe_limpa == "longa" and estado.get("chamadas"):
                return False
            estado["classe"] = classe_limpa
            estado["prazo"] = float(estado.get("inicio") or self.monotonic()) + limite
        self._publicar()
        return True

    def _retrato_turno(self, estado: dict[str, Any] | None) -> dict[str, Any]:
        if not estado:
            return {}
        chamadas = list(estado.get("chamadas") or [])
        return {
            "turno_id": str(estado.get("turno_id") or ""),
            "geracao": int(estado.get("geracao") or 0),
            "classe": str(estado.get("classe") or "normal"),
            "ativo": bool(estado.get("ativo", False)),
            "finalizado": bool(estado.get("finalizado", False)),
            "chamadas": len(chamadas),
            "tipos": [str(item.get("tipo") or "") for item in chamadas],
        }

    @staticmethod
    def _callback_ainda_atual(estado: dict[str, Any] | None) -> bool:
        callback = (estado or {}).get("ainda_atual_cb")
        if not callable(callback):
            return True
        try:
            return bool(callback())
        except Exception:
            return True

    def autorizar_chamada(
        self,
        *,
        tipo_chamada: Any = "principal",
        classe_timeout: Any = "normal",
        timeout_solicitado: float | int | None = None,
    ) -> DecisaoOrcamentoLLM:
        tipo = _tipo_chamada(tipo_chamada)
        if not self.habilitado:
            return DecisaoOrcamentoLLM(
                True,
                "orcamento_desativado",
                tipo_chamada=tipo,
                timeout_s=None,
            )
        classe = _classe_timeout(classe_timeout)
        agora = float(self.monotonic())
        chave = self._turno_contexto.get()
        with self._lock:
            probe = False
            if self._circuito_ate > agora:
                return self._registrar_bloqueio("circuito_aberto", tipo)
            if self._circuito_ate and agora >= self._circuito_ate:
                if self._probe_circuito_ativo:
                    return self._registrar_bloqueio("probe_em_andamento", tipo)
                self._probe_circuito_ativo = True
                probe = True

            estado = self._turnos.get(chave) if chave else None
            if estado:
                if not estado.get("ativo") or estado.get("finalizado"):
                    return self._registrar_bloqueio("turno_finalizado", tipo)
                if not self._callback_ainda_atual(estado):
                    return self._registrar_bloqueio("turno_obsoleto", tipo)
                if classe == "longa" and not estado.get("chamadas"):
                    estado["classe"] = "longa"
                    estado["prazo"] = float(estado.get("inicio") or agora) + LIMITES_CLASSE_S["longa"]
                restante = float(estado.get("prazo") or agora) - agora
                if restante < 1.0:
                    return self._registrar_bloqueio("prazo_esgotado", tipo)
                if (
                    tipo in TIPOS_CHAMADA_SECUNDARIA_LLM
                    and restante < FATIA_MINIMA_CHAMADA_SECUNDARIA_S
                ):
                    if probe:
                        self._probe_circuito_ativo = False
                    return self._registrar_bloqueio(
                        "fatia_secundaria_insuficiente", tipo,
                    )
                chamadas = list(estado.get("chamadas") or [])
                if len(chamadas) >= self.max_chamadas_turno:
                    return self._registrar_bloqueio("limite_chamadas", tipo)
                tipos_anteriores = [str(item.get("tipo") or "") for item in chamadas]
                if chamadas:
                    if tipo == "principal" and "principal" in tipos_anteriores:
                        return self._registrar_bloqueio("principal_duplicada", tipo)
                    if tipo in TIPOS_REPARO_LLM and any(
                        item in TIPOS_REPARO_LLM for item in tipos_anteriores
                    ):
                        return self._registrar_bloqueio("reparo_duplicado", tipo)
                limite_timeout = restante
            else:
                limite_timeout = LIMITES_CLASSE_S[classe]

            if timeout_solicitado is not None:
                try:
                    limite_timeout = min(limite_timeout, max(1.0, float(timeout_solicitado)))
                except (TypeError, ValueError):
                    pass
            elif estado:
                limite_timeout = min(limite_timeout, LIMITES_CLASSE_S[classe])
            else:
                # Fora de um turno canônico, preserve a configuração histórica
                # do chamador. O circuito continua protegendo falhas repetidas.
                limite_timeout = None

            self._sequencia_chamadas += 1
            chamada_id = f"llm-{self._sequencia_chamadas:07d}"
            if estado is not None:
                estado.setdefault("chamadas", []).append({
                    "id": chamada_id,
                    "tipo": tipo,
                    "status": "em_andamento",
                    "probe": probe,
                })
            self._chamadas_autorizadas += 1
            self._chamadas_por_tipo[tipo] = int(self._chamadas_por_tipo.get(tipo) or 0) + 1
            decisao = DecisaoOrcamentoLLM(
                True,
                "autorizada",
                chamada_id=chamada_id,
                turno_id=str((estado or {}).get("turno_id") or ""),
                geracao=int((estado or {}).get("geracao") or 0),
                tipo_chamada=tipo,
                timeout_s=round(limite_timeout, 3) if limite_timeout is not None else None,
                probe_circuito=probe,
            )
        self._decisao("autorizar", "dentro_do_orcamento", tipo=tipo)
        self._publicar()
        return decisao

    def concluir_chamada(
        self,
        decisao: DecisaoOrcamentoLLM | None,
        *,
        sucesso: bool,
    ) -> dict[str, Any]:
        if not isinstance(decisao, DecisaoOrcamentoLLM) or not decisao.permitida:
            return {"atual": False, "motivo": "chamada_nao_autorizada"}
        if decisao.motivo == "orcamento_desativado":
            return {"atual": True, "motivo": "orcamento_desativado"}
        with self._lock:
            estado = self._turnos.get(decisao.turno_id) if decisao.turno_id else None
            if estado:
                for chamada in list(estado.get("chamadas") or []):
                    if str(chamada.get("id") or "") == decisao.chamada_id:
                        chamada["status"] = "concluida" if sucesso else "falha"
                        break
            atual = bool(
                not estado
                or (
                    estado.get("ativo")
                    and not estado.get("finalizado")
                    and int(estado.get("geracao") or 0) == decisao.geracao
                    and self._callback_ainda_atual(estado)
                )
            )
            if sucesso:
                self._falhas_consecutivas = 0
                self._circuito_ate = 0.0
                self._probe_circuito_ativo = False
            else:
                self._falhas_consecutivas += 1
                if self._falhas_consecutivas >= self.falhas_para_abrir_circuito:
                    self._circuito_ate = float(self.monotonic()) + self.cooldown_circuito_s
                    self._probe_circuito_ativo = False
                elif decisao.probe_circuito:
                    self._circuito_ate = float(self.monotonic()) + self.cooldown_circuito_s
                    self._probe_circuito_ativo = False
        self._publicar()
        return {
            "atual": atual,
            "motivo": "concluida" if atual else "resposta_obsoleta",
        }

    def finalizar_turno(self, turno_id: Any = None, *, sucesso: bool = True) -> bool:
        if not self.habilitado:
            return True
        contexto_atual = self._turno_contexto.get()
        chave = contexto_atual if turno_id is None else _chave_turno(turno_id)
        with self._lock:
            estado = self._turnos.get(chave)
            if not estado:
                return False
            estado["ativo"] = False
            estado["finalizado"] = True
            estado["sucesso"] = bool(sucesso)
            if self._turno_contexto.get() == chave:
                self._turno_contexto.set("")
        self._publicar()
        return True

    def diagnostico(self) -> dict[str, Any]:
        agora = float(self.monotonic())
        with self._lock:
            chave = self._turno_contexto.get()
            atual = self._retrato_turno(self._turnos.get(chave))
            return {
                "modo": "orcamento_unico" if self.habilitado else "desativado",
                "limite_chamadas_turno": self.max_chamadas_turno,
                "turnos": len(self._turnos),
                "turno_atual": atual,
                "chamadas_autorizadas": self._chamadas_autorizadas,
                "chamadas_bloqueadas": self._chamadas_bloqueadas,
                "chamadas_por_tipo": dict(self._chamadas_por_tipo),
                "bloqueios_por_motivo": dict(self._bloqueios_por_motivo),
                "falhas_consecutivas": self._falhas_consecutivas,
                "circuito_aberto": self._circuito_ate > agora,
                "circuito_restante_s": round(max(0.0, self._circuito_ate - agora), 2),
                "probe_em_andamento": self._probe_circuito_ativo,
                "conteudo_persistido": False,
                "autoriza_execucao": False,
            }


def criar_orcamento_llm_turno_runtime(**kwargs: Any) -> OrcamentoLLMTurnoRuntime:
    return OrcamentoLLMTurnoRuntime(**kwargs)
