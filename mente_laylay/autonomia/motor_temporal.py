"""Proatividade da linha do tempo, calibrada pelo contexto da mente."""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.interpretacao_temporal import proxima_ocorrencia


def _normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base).strip()


def _tokens(texto: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", _normalizar(texto)))


class MotorTemporalRuntime:
    def __init__(
        self,
        *,
        estado_get: Callable[[], Dict[str, Any]],
        estado_set: Callable[[Dict[str, Any]], Any],
        contexto_getter: Callable[[], Dict[str, Any]],
        agendar_fala: Callable[..., Any],
        interacao_iniciada: Callable[[], bool],
        conversa_ativa: Callable[[], bool],
        clock: Callable[[], float] = time.time,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.estado_get = estado_get
        self.estado_set = estado_set
        self.contexto_getter = contexto_getter
        self.agendar_fala = agendar_fala
        self.interacao_iniciada = interacao_iniciada
        self.conversa_ativa = conversa_ativa
        self.clock = clock
        self.log = log
        self._lock = threading.Lock()
        self._agendando = False

    def _contexto(self) -> Dict[str, Any]:
        try:
            contexto = self.contexto_getter() or {}
            return contexto if isinstance(contexto, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _fala_prazo(item: Dict[str, Any], delta_s: float) -> str:
        assunto = str(item.get("assunto") or "seu compromisso").strip()
        if delta_s < 0:
            return f"Aquele prazo de {assunto} já chegou. Continua valendo ou você quer me atualizar?"
        if delta_s <= 3 * 3600:
            return f"Passando baixinho pra lembrar: {assunto} está chegando nas próximas horas."
        return f"Lembrete de convivência: {assunto} está marcado para amanhã."

    @staticmethod
    def _limiar_acompanhamento(item: Dict[str, Any], estatisticas: Dict[str, Any]) -> float:
        tipo = str(item.get("tipo") or "evento")
        metrica = dict(estatisticas.get(tipo) or {})
        if int(metrica.get("amostras") or 0) >= 2:
            return max(3 * 86400.0, min(30 * 86400.0, float(metrica.get("media_s") or 0.0) * 0.75))
        return {
            "projeto": 7, "planta": 7, "jogo": 5, "estudo": 3, "evento": 2,
        }.get(tipo, 7) * 86400.0

    def _candidato(self, estado: Dict[str, Any], contexto: Dict[str, Any], agora: float) -> Dict[str, Any] | None:
        marcadores = dict(estado.get("proatividade_temporal") or {})
        abertas = [item for item in estado.get("pendencias_vivas") or [] if item.get("status", "aberta") == "aberta"]
        for item in abertas:
            alvo = float(item.get("data_alvo_ts") or 0.0)
            if not alvo:
                continue
            delta = alvo - agora
            chave = f"prazo:{item.get('id')}:{int(alvo)}"
            if -6 * 3600 <= delta <= 24 * 3600 and chave not in marcadores:
                return {
                    "chave": chave, "tipo": "lembrete",
                    "fala": self._fala_prazo(item, delta), "emocao": "carinhosa",
                }

        emocao_usuario = _normalizar(contexto.get("emocao_usuario"))
        if emocao_usuario in {"frustracao", "tristeza", "raiva", "ansiedade"}:
            return None
        atividade = " ".join(str(contexto.get(chave) or "") for chave in ("atividade", "assunto", "titulo_janela"))
        tokens_atividade = _tokens(atividade)
        estatisticas = dict(estado.get("estatisticas_duracao") or {})
        perfil = dict(contexto.get("perfil_proatividade") or {})
        perfil_acompanhamento = dict(perfil.get("observacao") or {})
        recuo_aprendido = min(
            4.0,
            float(2 ** max(0, int(perfil_acompanhamento.get("recusas_consecutivas") or 0))),
        )
        for item in abertas:
            if float(item.get("data_alvo_ts") or 0.0):
                continue
            ultima = float(item.get("ultima_mencao_ts") or item.get("iniciado_em") or agora)
            idade = max(0.0, agora - ultima)
            limiar = self._limiar_acompanhamento(item, estatisticas) * recuo_aprendido
            relacionada = bool(tokens_atividade & _tokens(item.get("assunto") or ""))
            if idade < limiar or (not relacionada and idade < limiar * 2.0):
                continue
            janela = int(agora // (3 * 86400))
            chave = f"acompanhamento:{item.get('id')}:{janela}"
            if chave in marcadores:
                continue
            assunto = str(item.get("assunto") or f"aquele {item.get('tipo') or 'assunto'}").strip()
            return {
                "chave": chave, "tipo": "observacao",
                "fala": f"Me bateu curiosidade sobre {assunto}. Como isso está indo?",
                "emocao": "curiosa",
            }
        return None

    def executar_ciclo(self) -> Dict[str, Any]:
        if not self.interacao_iniciada() or self.conversa_ativa():
            return {"status": "contexto_ocupado"}
        with self._lock:
            if self._agendando:
                return {"status": "agendamento_em_andamento"}
            estado = dict(self.estado_get() or {})
            agora = float(self.clock())
            pendencias = list(estado.get("pendencias_vivas") or [])
            atualizou_recorrencia = False
            for indice, item_original in enumerate(pendencias):
                item = dict(item_original or {})
                recorrencia = dict(item.get("recorrencia") or {})
                alvo = float(item.get("data_alvo_ts") or 0.0)
                if not recorrencia or not alvo or alvo >= agora - 2 * 86400.0:
                    continue
                proxima = proxima_ocorrencia(alvo, recorrencia, depois_de=agora)
                pendencias[indice] = {
                    **item, "data_alvo_ts": proxima,
                    "ocorrencias_nao_confirmadas": int(item.get("ocorrencias_nao_confirmadas") or 0) + 1,
                }
                atualizou_recorrencia = True
            if atualizou_recorrencia:
                estado["pendencias_vivas"] = pendencias
                self.estado_set(estado)
            candidato = self._candidato(estado, self._contexto(), agora)
            if not candidato:
                return {"status": "sem_candidato"}
            self._agendando = True

        def concluir(entregue: bool, motivo: str) -> None:
            with self._lock:
                self._agendando = False
            if not entregue:
                self.log(f"⏳ [TEMPO] acompanhamento adiado: {motivo}")
                return
            atual = dict(self.estado_get() or {})
            marcadores = dict(atual.get("proatividade_temporal") or {})
            marcadores[candidato["chave"]] = float(self.clock())
            # Mantém apenas marcadores recentes; recorrências antigas não precisam viver para sempre.
            limite = float(self.clock()) - 90 * 86400.0
            atual["proatividade_temporal"] = {
                chave: ts for chave, ts in marcadores.items() if float(ts or 0.0) >= limite
            }
            self.estado_set(atual)

        aceito = self.agendar_fala(
            candidato["tipo"], candidato["fala"], candidato["emocao"], 1,
            ao_concluir=concluir,
        )
        if aceito is False:
            with self._lock:
                self._agendando = False
            return {"status": "adiado_pelo_porteiro"}
        return {"status": "agendado", "tipo": candidato["tipo"]}

    def executar(self, deve_parar: Callable[[], bool] | None = None, intervalo_s: float = 120.0) -> None:
        while not (callable(deve_parar) and deve_parar()):
            try:
                self.executar_ciclo()
            except Exception as erro:
                self.log(f"⚠️ [TEMPO] ciclo de acompanhamento ignorado: {type(erro).__name__}: {erro}")
            time.sleep(intervalo_s)


def criar_motor_temporal_runtime(**kwargs: Any) -> MotorTemporalRuntime:
    return MotorTemporalRuntime(**kwargs)
