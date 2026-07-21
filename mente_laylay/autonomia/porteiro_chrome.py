"""Monitor de RAM e abas ociosas do Porteiro do Chrome."""

from __future__ import annotations

import time
import json
from typing import Any, Callable


def fechar_abas_sugeridas(
    abas_sugeridas: list[str],
    *,
    enviar: Callable[[str], Any],
    falar: Callable[..., Any],
    log: Callable[[str], Any] = print,
) -> bool:
    """Fecha somente as abas previamente propostas pelo Porteiro."""
    if not abas_sugeridas:
        falar("Não tem abas paradas registradas agora. Me acompanha mais de perto.", "calma", 1)
        return True
    quantidade = len(abas_sugeridas)
    log(f"🧹 [PORTEIRO] Fechando {quantidade} aba(s) sugeridas...")
    for url in list(abas_sugeridas):
        enviar(json.dumps({"action": "close_specific_tab", "target": str(url)[:60]}))
    abas_sugeridas.clear()
    plural = "s" if quantidade > 1 else ""
    falar(f"Pronto. Limpei {quantidade} aba{plural} parada{plural}. Agora sobra RAM de verdade.", "debochada", 2)
    return True


class PorteiroChromeRuntime:
    def __init__(
        self,
        *,
        abas_sugeridas: list[str],
        obter_ram_percent: Callable[[], float],
        listar_abas: Callable[..., Any],
        obter_estado_chrome: Callable[[], dict],
        falar: Callable[..., Any],
        enviar_fechamento: Callable[[str], Any] | None = None,
        ram_threshold: float = 80,
        idle_minutos: int = 45,
        intervalo_minutos: int = 12,
        cooldown_s: float = 1800.0,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Any] = time.sleep,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.abas_sugeridas = abas_sugeridas
        self.obter_ram_percent = obter_ram_percent
        self.listar_abas = listar_abas
        self.obter_estado_chrome = obter_estado_chrome
        self.falar = falar
        self.enviar_fechamento = enviar_fechamento
        self.ram_threshold = float(ram_threshold)
        self.idle_minutos = int(idle_minutos)
        self.intervalo_minutos = int(intervalo_minutos)
        self.cooldown_s = float(cooldown_s)
        self.clock = clock
        self.sleep = sleep
        self.log = log
        self.ultima_sugestao_ts = 0.0

    def fechar_sugeridas(self) -> bool:
        enviar = self.enviar_fechamento or (lambda _payload: None)
        return fechar_abas_sugeridas(
            self.abas_sugeridas,
            enviar=enviar,
            falar=self.falar,
            log=self.log,
        )

    def executar_ciclo(self) -> bool:
        ram_percent = float(self.obter_ram_percent())
        if ram_percent < self.ram_threshold:
            return False

        agora = self.clock()
        limite_idle = agora - (self.idle_minutos * 60)
        abas_abertas = self.listar_abas(timeout_s=5.0)
        if not isinstance(abas_abertas, list) or not abas_abertas:
            return False

        estado = self.obter_estado_chrome() or {}
        url_atual = str(estado.get("aba_url_atual") or "")
        ultimo_acesso = estado.get("_tab_last_seen") or {}
        ociosas: list[dict] = []
        for aba in abas_abertas:
            if not isinstance(aba, dict):
                continue
            url = str(aba.get("url") or "")
            titulo = str(aba.get("titulo") or aba.get("title") or "")[:50]
            if not url or url.startswith("chrome://") or url.startswith("chrome-extension://"):
                continue
            if url == url_atual:
                continue
            acesso = ultimo_acesso.get(url)
            ts_acesso = acesso.get("ts") if isinstance(acesso, dict) else None
            if ts_acesso is None:
                ts_acesso = agora - (self.idle_minutos * 60) - 1
            if float(ts_acesso) < limite_idle:
                ociosas.append({"url": url, "titulo": titulo, "minutos": int((agora - float(ts_acesso)) / 60)})

        if len(ociosas) < 2 or agora - self.ultima_sugestao_ts < self.cooldown_s:
            return False

        ociosas.sort(key=lambda item: item["minutos"], reverse=True)
        candidatas = ociosas[:3]
        self.ultima_sugestao_ts = agora
        self.abas_sugeridas[:] = [item["url"] for item in candidatas]

        nomes = ", ".join(item["titulo"] or item["url"][:30] for item in candidatas)
        horas, minutos = divmod(candidatas[0]["minutos"], 60)
        tempo = f"ha {horas}h{minutos:02d}" if horas else f"ha {candidatas[0]['minutos']} min"
        mensagem = (
            f"Pedro, a RAM ta em {int(ram_percent)}% e voce nao mexe em {len(candidatas)} abas {tempo}: "
            f"{nomes}. Manda um 'fecha as abas paradas' se quiser limpar."
        )
        self.log(f"[PORTEIRO] {mensagem}")
        try:
            self.falar(mensagem, "irritada", 1)
        except Exception as erro:
            self.log(f"[PORTEIRO] Erro ao falar: {erro}")
        return True

    def daemon(self) -> None:
        self.sleep(90)
        self.log("[PORTEIRO] Thread do Porteiro do Chrome iniciada.")
        while True:
            try:
                self.sleep(self.intervalo_minutos * 60)
                self.executar_ciclo()
            except Exception as erro:
                self.log(f"[PORTEIRO] Erro no daemon: {erro}")


def criar_porteiro_chrome_runtime(**kwargs) -> PorteiroChromeRuntime:
    return PorteiroChromeRuntime(**kwargs)
