"""Monitor proativo da janela ativa conectado ao estado mental compartilhado."""

from __future__ import annotations

import time
from typing import Any, Callable


FALAS_ASSUNTO = {
    "Programação": "Vejo que o código tá rendendo, Pedro. Quer uma música de foco?",
    "Gaming": "Tá no modo gamer, né, Pedro. Quer que eu deixe uma música de fundo?",
    "Impressão 3D": "Isso aí tá com cara de impressão 3D. Quer que eu te ajude a achar um modelo bom?",
}


class MonitorJanelasRuntime:
    """Observa janelas sem possuir uma mente separada da Laylay."""

    def __init__(
        self,
        *,
        capturar_janela: Callable[[], dict[str, Any]],
        atualizar_contexto: Callable[[dict[str, Any]], Any],
        continuidade_get: Callable[[str, Any], Any],
        continuidade_update: Callable[..., Any],
        esta_falando: Callable[[], bool],
        conversa_ativa: Callable[[], bool],
        ultimo_proativo_get: Callable[[], float],
        ultimo_proativo_set: Callable[[float], Any],
        sugestoes_bloqueadas_get: Callable[[], dict[str, float]],
        janela_em_tela_cheia: Callable[[Any], bool],
        detectar_gatilho: Callable[[str, str, str, bool], tuple[str, dict | None]],
        fala_gatilho: Callable[[str], str],
        falar: Callable[[str, str, int], Any],
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Any] = time.sleep,
        log: Callable[[str], Any] = print,
        intervalo_s: float = 2.0,
        estabilidade_assunto_s: float = 180.0,
        permanencia_gatilho_s: float = 12.0,
        cooldown_proativo_s: float = 1200.0,
    ) -> None:
        self.capturar_janela = capturar_janela
        self.atualizar_contexto = atualizar_contexto
        self.continuidade_get = continuidade_get
        self.continuidade_update = continuidade_update
        self.esta_falando = esta_falando
        self.conversa_ativa = conversa_ativa
        self.ultimo_proativo_get = ultimo_proativo_get
        self.ultimo_proativo_set = ultimo_proativo_set
        self.sugestoes_bloqueadas_get = sugestoes_bloqueadas_get
        self.janela_em_tela_cheia = janela_em_tela_cheia
        self.detectar_gatilho = detectar_gatilho
        self.fala_gatilho = fala_gatilho
        self.falar = falar
        self.clock = clock
        self.sleep = sleep
        self.log = log
        self.intervalo_s = float(intervalo_s)
        self.estabilidade_assunto_s = float(estabilidade_assunto_s)
        self.permanencia_gatilho_s = float(permanencia_gatilho_s)
        self.cooldown_proativo_s = float(cooldown_proativo_s)

        self.ultimo_hwnd: Any = None
        self.ultimo_assunto = ""
        self.assunto_change_ts = 0.0
        self.ultimo_gatilho = ""
        self.gatilho_inicio_ts = 0.0

    def _ha_pendencia_ou_interacao(self) -> bool:
        return bool(
            self.continuidade_get("comando_sugerido_estado", "NONE") != "NONE"
            or self.esta_falando()
            or self.conversa_ativa()
        )

    def _cooldown_ativo(self, agora: float) -> bool:
        return agora - float(self.ultimo_proativo_get() or 0.0) < self.cooldown_proativo_s

    def sugerir_assunto(self, assunto: str, agora: float | None = None) -> bool:
        assunto = str(assunto or "").strip()
        fala = FALAS_ASSUNTO.get(assunto, "")
        if not fala or self.esta_falando():
            return False
        if self.continuidade_get("comando_sugerido_estado", "NONE") != "NONE":
            return False
        agora = float(self.clock() if agora is None else agora)
        if self._cooldown_ativo(agora):
            return False
        self.ultimo_proativo_set(agora)
        self.falar(fala, "calma", 1)
        return True

    def executar_ciclo(self) -> dict[str, Any]:
        retrato = dict(self.capturar_janela() or {})
        self.atualizar_contexto(retrato)

        janela = retrato.get("win")
        titulo = str(retrato.get("title") or "")
        hwnd = retrato.get("hwnd")
        executavel = str(retrato.get("exe") or "")
        assunto = str(retrato.get("assunto") or "")
        agora = float(self.clock())

        if hwnd and hwnd != self.ultimo_hwnd:
            self.ultimo_hwnd = hwnd
            self.assunto_change_ts = agora
            self.ultimo_assunto = assunto
            self.ultimo_gatilho = ""
            self.gatilho_inicio_ts = 0.0
        elif (
            assunto
            and assunto == self.ultimo_assunto
            and self.assunto_change_ts
            and agora - self.assunto_change_ts >= self.estabilidade_assunto_s
        ):
            self.sugerir_assunto(assunto, agora)

        if self._ha_pendencia_ou_interacao() or self._cooldown_ativo(agora):
            return {"status": "bloqueado", "retrato": retrato}

        fullscreen = bool(self.janela_em_tela_cheia(janela))
        if fullscreen and assunto == "Gaming":
            return {"status": "jogo_fullscreen", "retrato": retrato}

        gatilho, payload = self.detectar_gatilho(executavel, titulo, assunto, fullscreen)
        gatilho = str(gatilho or "")
        if not gatilho:
            return {"status": "sem_gatilho", "retrato": retrato}

        bloqueios = dict(self.sugestoes_bloqueadas_get() or {})
        if agora < float(bloqueios.get(gatilho, 0.0) or 0.0):
            return {"status": "gatilho_bloqueado", "gatilho": gatilho, "retrato": retrato}

        if gatilho != self.ultimo_gatilho:
            self.ultimo_gatilho = gatilho
            self.gatilho_inicio_ts = agora
            return {"status": "observando_gatilho", "gatilho": gatilho, "retrato": retrato}

        if self.gatilho_inicio_ts and agora - self.gatilho_inicio_ts >= self.permanencia_gatilho_s:
            self.continuidade_update(
                comando_sugerido=gatilho,
                comando_sugerido_payload=payload,
                comando_sugerido_estado="PENDING_CONFIRM",
                comando_sugerido_ts=agora,
                comando_pendente=gatilho,
                comando_pendente_payload=payload,
            )
            self.ultimo_proativo_set(agora)
            fala = str(self.fala_gatilho(gatilho) or "")
            if fala:
                self.falar(fala, "calma", 1)
            self.ultimo_gatilho = ""
            self.gatilho_inicio_ts = 0.0
            return {"status": "sugestao_emitida", "gatilho": gatilho, "retrato": retrato}

        return {"status": "aguardando_gatilho", "gatilho": gatilho, "retrato": retrato}

    def executar(self, deve_parar: Callable[[], bool] | None = None) -> None:
        while not (callable(deve_parar) and deve_parar()):
            try:
                self.executar_ciclo()
            except Exception as exc:
                self.log(f"⚠️ [MONITOR JANELAS] ciclo ignorado: {type(exc).__name__}: {exc}")
            self.sleep(self.intervalo_s)


def criar_monitor_janelas_runtime(**kwargs: Any) -> MonitorJanelasRuntime:
    return MonitorJanelasRuntime(**kwargs)
