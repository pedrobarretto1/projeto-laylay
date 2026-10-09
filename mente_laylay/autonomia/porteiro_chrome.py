"""Monitor de RAM e abas ociosas do Porteiro do Chrome."""

from __future__ import annotations

import time
import threading
import hashlib
import json
import re
from typing import Any, Callable

from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    classificar_confirmacao_local, normalizar_confirmacao_texto,
)
from mente_laylay.memoria_mental.pendencia_acao import PendenciaAcaoRuntime
from mente_laylay.memoria_mental.resultado_acao import ResultadoTratamentoOperacional


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
    falhas: list[str] = []
    fechadas = 0
    for url in list(abas_sugeridas):
        try:
            resultado = enviar(str(url))
            if resultado is False:
                falhas.append(str(url))
            else:
                fechadas += 1
        except Exception as erro:
            falhas.append(str(url))
            log(f"⚠️ [PORTEIRO] falha ao fechar aba: {type(erro).__name__}")
    abas_sugeridas[:] = falhas
    if falhas:
        falar(
            f"Fechei {fechadas} aba(s), mas {len(falhas)} não respondeu. "
            "Mantive essas na lista para não fingir que a limpeza terminou.",
            "irritada",
            1,
        )
        return False
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
        stop_event: threading.Event | None = None,
        pendencias: PendenciaAcaoRuntime | None = None,
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
        self.stop_event = stop_event or threading.Event()
        self.pendencias = pendencias
        self._lock = threading.RLock()

    def _referencia_abas(self) -> str:
        material = json.dumps(list(self.abas_sugeridas), ensure_ascii=False)
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def processar_confirmacao(
        self, texto: str, *,
        executar: Callable[[dict[str, Any], str], ResultadoTratamentoOperacional],
        permitir_execucao: bool = True,
    ) -> bool:
        """Consome somente a oferta identificada; executor publica o receipt."""
        with self._lock:
            if self.pendencias is None:
                return False
            item = self.pendencias.obter()
            if not item or item.get("origem") != "porteiro_chrome":
                return False
            decisao = classificar_confirmacao_local(texto, somente_aceite_generico=True)
            # O domínio acrescenta apenas o verbo elíptico. Sim/não pertencem
            # ao interpretador compartilhado de todas as habilidades.
            fechamento = re.fullmatch(
                r"(?:pode\s+)?(?:fechar|fecha|feche|limpa|limpe)"
                r"(?:\s+as\s+abas(?:\s+(?:paradas|ociosas))?)?",
                normalizar_confirmacao_texto(texto),
            )
            if decisao is None and fechamento:
                decisao = True
            if decisao is None or (decisao is True and not permitir_execucao):
                return False
            resultado = self.pendencias.resolver(
                texto, id_esperado=item["id"],
                classificar_dominio=lambda *_: "aceitar" if decisao else "recusar",
                somente_aceite_generico=True,
            )
            status = resultado.get("status")
            if status in {"concorrente", "em_processamento"}:
                self.falar("O pedido está mudando ou já está em andamento. Aguarde um instante.", "calma", 1)
                return True
            if not resultado.get("tratado"):
                return False
            if status == "recusar":
                self.pendencias.concluir(item["id"], "recusada")
                self.abas_sugeridas.clear()
                self.falar("Certo, mantive as abas abertas.", "calma", 1)
                return True
            if (
                status != "aceitar"
                or item.get("acao") != "fechar_abas_paradas"
                or item.get("referencia") != self._referencia_abas()
                or not self.abas_sugeridas
            ):
                self.pendencias.concluir(item["id"], "alvos_alterados")
                self.falar("As abas sugeridas mudaram. Preciso confirmar a nova lista antes de fechar.", "calma", 1)
                return True
            try:
                tratamento = executar({"intent": "CLOSE_IDLE_TABS", "params": {}}, texto)
                final = "executada" if tratamento.confirmado is True else "falha_execucao"
                if not tratamento.tratado:
                    self.falar("Não consegui executar o fechamento das abas.", "calma", 1)
            except Exception as erro:
                self.log(f"[PORTEIRO] Falha na confirmação: {type(erro).__name__}")
                final = "falha_execucao"
                self.falar("Não consegui confirmar o fechamento das abas.", "calma", 1)
            self.pendencias.concluir(item["id"], final)
            return True

    def fechar_sugeridas(self) -> bool:
        with self._lock:
            enviar = self.enviar_fechamento or (lambda _payload: False)
            return fechar_abas_sugeridas(
                self.abas_sugeridas, enviar=enviar, falar=self.falar, log=self.log,
            )

    def executar_ciclo(self) -> bool:
        with self._lock:
            return self._executar_ciclo()

    def _executar_ciclo(self) -> bool:
        if self.pendencias is not None and self.pendencias.obter():
            return False
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
        self.abas_sugeridas[:] = [item["url"] for item in candidatas]

        nomes = ", ".join(item["titulo"] or item["url"][:30] for item in candidatas)
        horas, minutos = divmod(candidatas[0]["minutos"], 60)
        tempo = f"ha {horas}h{minutos:02d}" if horas else f"ha {candidatas[0]['minutos']} min"
        mensagem = (
            f"Sua memória está em {int(ram_percent)} por cento e encontrei "
            f"{len(candidatas)} abas paradas {tempo}: {nomes}. "
            "Se quiser aliviar um pouco, eu fecho só as que estão paradas."
        )
        self.log(f"[PORTEIRO] {mensagem}")
        pendencia = None
        if self.pendencias is not None:
            pendencia = self.pendencias.registrar(
                origem="porteiro_chrome", acao="fechar_abas_paradas",
                dominio="navegador", pergunta=mensagem,
                referencia=self._referencia_abas(),
                metadados={
                    "intent": "CLOSE_IDLE_TABS", "quantidade": len(candidatas),
                    "sobrevive_comando_independente": True,
                },
                ttl_s=300.0,
            )
            if not pendencia:
                self.abas_sugeridas.clear()
                return False
        try:
            entregue = self.falar(mensagem, "calma", 1) is not False
        except Exception as erro:
            self.log(f"[PORTEIRO] Erro ao falar: {erro}")
            entregue = False
        if not entregue:
            if pendencia:
                self.pendencias.concluir(pendencia["id"], "falha_publicacao")
            self.abas_sugeridas.clear()
            return False
        self.ultima_sugestao_ts = agora
        return True

    def daemon(self) -> None:
        if self.stop_event.wait(90):
            return
        self.log("[PORTEIRO] Thread do Porteiro do Chrome iniciada.")
        while not self.stop_event.is_set():
            try:
                if self.stop_event.wait(self.intervalo_minutos * 60):
                    break
                self.executar_ciclo()
            except Exception as erro:
                self.log(f"[PORTEIRO] Erro no daemon: {erro}")

    def encerrar(self) -> None:
        self.stop_event.set()


def criar_porteiro_chrome_runtime(**kwargs) -> PorteiroChromeRuntime:
    return PorteiroChromeRuntime(**kwargs)
