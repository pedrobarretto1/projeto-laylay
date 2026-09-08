"""Percepção temporal e iniciativas circadianas da Laylay.

O relógio é uma fonte de contexto, não uma autorização para executar ações.
Luz e volume só podem sair da sugestão quando o motor central encontra uma
permissão explícita, uma ação reversível elegível e confirmação do executor.
"""

from __future__ import annotations

import threading
import time
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Any, Callable

from mente_laylay.autonomia.diretor_presenca import (
    decisao_presenca_aceita_para_entrega,
)
from mente_laylay.memoria_mental.estado_continuidades import sugestao_pendente_ativa

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python antigo
    ZoneInfo = None  # type: ignore[assignment]


def agora_no_fuso(fuso: str = "America/Sao_Paulo") -> datetime:
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(str(fuso or "America/Sao_Paulo")))
        except Exception:
            pass
    return datetime.now().astimezone()


def detectar_consulta_horario(texto: str) -> bool:
    """Reconhece somente pedidos pelo horário atual, não horários de eventos."""
    normalizado = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", str(texto or "").casefold())
        if unicodedata.category(caractere) != "Mn"
    )
    normalizado = re.sub(r"[^a-z0-9\s]", " ", normalizado)
    normalizado = re.sub(r"\s+", " ", normalizado).strip()
    normalizado = re.sub(r"^(?:oi\s+)?(?:lay|laylay)\s+", "", normalizado)
    normalizado = re.sub(r"\s+(?:lay|laylay)$", "", normalizado).strip()
    padroes = (
        r"que horas (?:sao|e)(?: agora)?",
        r"qual (?:e )?a hora(?: agora)?",
        r"qual (?:e )?o horario(?: atual)?",
        r"me (?:diz|fala) (?:a hora|as horas|que horas (?:sao|e))(?: agora)?",
        r"hora atual",
    )
    return any(re.fullmatch(padrao, normalizado) for padrao in padroes)


def responder_consulta_horario(
    agora: datetime | None = None,
    *,
    fuso: str = "America/Sao_Paulo",
) -> str:
    """Produz uma resposta curta a partir do relógio real da Laylay."""
    contexto = construir_contexto_temporal(
        agora or agora_no_fuso(fuso),
        fuso=fuso,
    )
    atual = contexto["agora"]
    verbo = "É" if atual.hour == 1 else "São"
    complementos = {
        "madrugada": "Já é madrugada por aqui.",
        "manha": "Ainda é manhã por aqui.",
        "tarde": "Ainda é tarde por aqui.",
        "noite": "Já é noite por aqui.",
    }
    return (
        f"{verbo} {atual.strftime('%Hh%M')} agora. "
        f"{complementos[str(contexto['periodo'])]}"
    )


def construir_contexto_temporal(
    agora: datetime | None = None,
    *,
    fuso: str = "America/Sao_Paulo",
) -> dict[str, Any]:
    atual = agora or agora_no_fuso(fuso)
    hora = atual.hour
    if hora < 5:
        periodo = "madrugada"
    elif hora < 12:
        periodo = "manha"
    elif hora < 18:
        periodo = "tarde"
    else:
        periodo = "noite"

    if 5 <= hora < 8:
        fase = "amanhecer"
        ritmo = "despertando"
        tom = "leve e acolhedor, com energia baixa a moderada"
    elif 8 <= hora < 12:
        fase = "manha_ativa"
        ritmo = "produtivo"
        tom = "vivo, curioso e objetivo"
    elif 12 <= hora < 18:
        fase = "tarde"
        ritmo = "estavel"
        tom = "natural, atento e disposto"
    elif 18 <= hora < 21:
        fase = "anoitecer"
        ritmo = "desacelerando"
        tom = "calmo e companheiro"
    elif 21 <= hora < 23:
        fase = "noite"
        ritmo = "calmo"
        tom = "mais tranquilo, sem perder o carisma"
    else:
        fase = "noite_tardia"
        ritmo = "descanso"
        tom = "baixo, curto e acolhedor; evite euforia"

    escuro_esperado = hora >= 18 or hora < 6
    if fase == "noite_tardia":
        recomendacoes = ["reduzir_volume", "desligar_luz", "reduzir_estimulos"]
    elif fase == "anoitecer":
        recomendacoes = ["oferecer_luz_ambiente"]
    elif fase in {"amanhecer", "manha_ativa"}:
        recomendacoes = ["favorecer_inicio_do_dia"]
    else:
        recomendacoes = []

    return {
        "agora": atual,
        "iso": atual.isoformat(),
        "data": atual.date().isoformat(),
        "hora": atual.strftime("%H:%M"),
        "hora_inteira": hora,
        "fuso": getattr(atual.tzinfo, "key", None) or str(atual.tzinfo or fuso),
        "periodo": periodo,
        "fase": fase,
        "ritmo": ritmo,
        "tom_comunicacao": tom,
        "escuro_esperado": escuro_esperado,
        "recomendacoes": recomendacoes,
    }


def chave_noite(contexto: dict[str, Any]) -> str:
    atual = contexto.get("agora")
    if not isinstance(atual, datetime):
        return str(contexto.get("data") or "")
    # Depois da meia-noite ainda estamos tratando a noite iniciada no dia anterior.
    data_base = atual - timedelta(days=1) if atual.hour < 5 else atual
    return data_base.date().isoformat()


def adaptar_fala_ao_ritmo(fala: str, contexto: dict[str, Any] | None) -> str:
    """Suaviza a oralidade tarde da noite sem inserir comentários artificiais."""
    texto = str(fala or "").strip()
    fase = str((contexto or {}).get("fase") or "")
    if not texto or fase != "noite_tardia":
        return texto
    texto = re.sub(r"!{2,}", "!", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


class RitmoCircadianoRuntime:
    def __init__(
        self,
        *,
        estado_get: Callable[[], dict[str, Any]],
        estado_set: Callable[[dict[str, Any]], Any],
        continuidades_get: Callable[[str, Any], Any],
        continuidades_update: Callable[..., Any],
        considerar_presenca: Callable[[dict[str, Any]], Any],
        interacao_iniciada: Callable[[], bool],
        conversa_ativa: Callable[[], bool],
        preparar_sugestao: Callable[[str, dict[str, Any], str], tuple[str, dict[str, Any], str]] | None = None,
        agora_cb: Callable[[], datetime] | None = None,
        fuso: str = "America/Sao_Paulo",
        log: Callable[[str], Any] = print,
    ) -> None:
        self.estado_get = estado_get
        self.estado_set = estado_set
        self.continuidades_get = continuidades_get
        self.continuidades_update = continuidades_update
        self.considerar_presenca = considerar_presenca
        self.interacao_iniciada = interacao_iniciada
        self.conversa_ativa = conversa_ativa
        self.preparar_sugestao = preparar_sugestao
        self.agora_cb = agora_cb or (lambda: agora_no_fuso(fuso))
        self.fuso = fuso
        self.log = log
        self._lock = threading.Lock()
        self._em_agendamento = False

    def contexto_atual(self) -> dict[str, Any]:
        return construir_contexto_temporal(self.agora_cb(), fuso=self.fuso)

    def _candidato(self, contexto: dict[str, Any]) -> dict[str, Any] | None:
        fase = contexto.get("fase")
        noite = chave_noite(contexto)
        estado = dict(self.estado_get() or {})
        emitidas = dict(estado.get("sugestoes_emitidas") or {})
        candidato = None
        if fase in {"anoitecer", "noite"} and emitidas.get("luz_anoitecer") != noite:
            candidato = {
                "chave": "luz_anoitecer",
                "marcador": noite,
                "comando": "TIME_LIGHT_ON",
                "payload": {"alvo": "lampada_quarto"},
                "fala": "Já escureceu por este horário. Quer que eu ligue a luz do quarto?",
                "emocao": "calma",
            }
        elif fase == "noite_tardia" and emitidas.get("modo_noite") != noite:
            candidato = {
                "chave": "modo_noite",
                "marcador": noite,
                "comando": "TIME_WIND_DOWN",
                "payload": {"alvo": "lampada_quarto", "volume": 25},
                "fala": (
                    "Já ficou bem tarde. Quer que eu deixe tudo mais quieto, "
                    "baixando o volume e apagando a luz se ela estiver acesa?"
                ),
                "emocao": "carinhosa",
            }
        if candidato and callable(self.preparar_sugestao):
            try:
                comando, payload, fala = self.preparar_sugestao(
                    candidato["comando"],
                    dict(candidato["payload"]),
                    candidato["fala"],
                )
                candidato["comando"] = comando
                candidato["payload"] = dict(payload or {})
                candidato["fala"] = fala
            except Exception as erro:
                self.log(f"⚠️ [RITMO] preferência temporal ignorada: {erro}")
        return candidato

    def executar_ciclo(self) -> dict[str, Any]:
        contexto = self.contexto_atual()
        estado = dict(self.estado_get() or {})
        estado["contexto_atual"] = {
            chave: valor for chave, valor in contexto.items() if chave != "agora"
        }
        self.estado_set(estado)

        if not self.interacao_iniciada() or self.conversa_ativa():
            return {"status": "somente_percepcao", "contexto": contexto}
        if sugestao_pendente_ativa(self.continuidades_get):
            return {"status": "outra_sugestao_pendente", "contexto": contexto}
        with self._lock:
            if self._em_agendamento:
                return {"status": "agendamento_em_andamento", "contexto": contexto}
            candidato = self._candidato(contexto)
            if not candidato:
                return {"status": "sem_sugestao", "contexto": contexto}
            self._em_agendamento = True

        def concluir(entregue: bool, motivo: str) -> None:
            with self._lock:
                self._em_agendamento = False
            if not entregue:
                self.log(f"🕰️ [RITMO] sugestão temporal adiada: {motivo}")
                return
            atual = dict(self.estado_get() or {})
            emitidas = dict(atual.get("sugestoes_emitidas") or {})
            emitidas[candidato["chave"]] = candidato["marcador"]
            atual["sugestoes_emitidas"] = emitidas
            self.estado_set(atual)
            self.continuidades_update(
                comando_sugerido=candidato["comando"],
                comando_sugerido_payload=dict(candidato["payload"]),
                comando_sugerido_estado="PENDING_CONFIRM",
                comando_sugerido_ts=time.time(),
                comando_pendente=candidato["comando"],
                comando_pendente_payload=dict(candidato["payload"]),
            )

        dominio = "conforto"
        if candidato["comando"] == "TIME_LIGHT_ON":
            dominio = "iot"
        elif candidato["comando"] == "EXECUTE_INTENT":
            interna = (
                candidato["payload"].get("intent")
                if isinstance(candidato["payload"].get("intent"), dict)
                else {}
            )
            if str(interna.get("intent") or "").upper() == "IOT_CONTROL":
                dominio = "iot"
        instante = contexto.get("agora")
        timestamp = instante.timestamp() if isinstance(instante, datetime) else time.time()
        evento = {
            "natureza": "evento",
            "origem": "ritmo_circadiano",
            "dominio": dominio,
            "categoria": "dica",
            "confianca": 0.96,
            "fundamentada": True,
            "momento_seguro": True,
            "motivo": (
                f"O ritmo temporal entrou na fase {contexto.get('fase')}; "
                "há uma oportunidade de oferecer conforto reversível."
            ),
            "evidencias": [
                f"fase_temporal:{contexto.get('fase')}",
                f"recomendacao:{candidato['chave']}",
            ],
            "chave": f"ritmo:{candidato['chave']}:{candidato['marcador']}",
            "timestamp": timestamp,
            "validade_s": 900.0,
            "acao_proposta": {
                "intent": candidato["comando"],
                "params": dict(candidato["payload"]),
            },
            "utilidade": 62 if candidato["chave"] == "modo_noite" else 56,
            "executavel": True,
            "reversivel": True,
            "autoridade_usuario": False,
            "permissao_execucao": False,
            "ao_concluir": concluir,
        }
        try:
            resultado = dict(self.considerar_presenca(evento) or {})
        except Exception as erro:
            self.log(f"⚠️ [PRESENÇA] evento circadiano ignorado: {erro}")
            resultado = {}
        if not decisao_presenca_aceita_para_entrega(resultado):
            with self._lock:
                self._em_agendamento = False
            decisao_iniciativa = dict(resultado.get("decisao_iniciativa") or {})
            decisao = str(decisao_iniciativa.get("decisao") or "")
            status = {
                "executado": "executado_autonomamente",
                "execucao_falhou": "execucao_autonoma_falhou",
            }.get(decisao, "bloqueado_permissao")
            if status == "executado_autonomamente":
                atual = dict(self.estado_get() or {})
                emitidas = dict(atual.get("sugestoes_emitidas") or {})
                emitidas[candidato["chave"]] = candidato["marcador"]
                atual["sugestoes_emitidas"] = emitidas
                self.estado_set(atual)
            return {"status": status, "contexto": contexto}
        return {"status": "sugestao_agendada", "contexto": contexto}

    def executar(
        self, deve_parar: Callable[[], bool] | None = None,
        intervalo_s: float = 60.0,
        aguardar_fn: Callable[[float], bool] | None = None,
    ) -> None:
        while not (callable(deve_parar) and deve_parar()):
            try:
                self.executar_ciclo()
            except Exception as erro:
                self.log(f"⚠️ [RITMO] ciclo temporal ignorado: {type(erro).__name__}: {erro}")
            if callable(aguardar_fn):
                if aguardar_fn(intervalo_s):
                    break
            else:
                time.sleep(intervalo_s)


def criar_ritmo_circadiano_runtime(**kwargs: Any) -> RitmoCircadianoRuntime:
    return RitmoCircadianoRuntime(**kwargs)
