"""Implantação gradual e reversível das otimizações de desempenho."""

from __future__ import annotations

from collections import deque
import os
import threading
import time
from typing import Any, Callable, Mapping


VALORES_DESATIVADOS = frozenset({"0", "false", "nao", "não", "off", "desligado"})
SINAIS_REGRESSAO = frozenset({
    "fallback",
    "contradicao",
    "duplicacao",
    "perda_contexto",
    "falso_sucesso",
})
FLAGS_OTIMIZACAO = {
    "orcamento_llm": "LAYLAY_ORCAMENTO_LLM_ATIVO",
    "prompt_proporcional": "LAYLAY_OTIMIZACAO_PROMPT_ATIVA",
    "publicacao_visual": "LAYLAY_PUBLICACAO_VISUAL_ANTECIPADA",
    "tts_primeira_frase": "LAYLAY_TTS_ANTECIPAR_PRIMEIRA_FRASE",
    "startup_duas_fases": "LAYLAY_INICIALIZACAO_DUAS_FASES",
    "cache_resumos": "LAYLAY_CACHE_RESUMOS_ATIVO",
    "cache_tuya": "LAYLAY_CACHE_TUYA_ATIVO",
}


def flag_desempenho_ativa(
    nome: str,
    *,
    padrao: str = "1",
    env_getter: Callable[[str, str], str | None] = os.getenv,
) -> bool:
    """Combina a chave mestre com uma flag específica, sem efeitos colaterais."""
    mestre = str(
        env_getter("LAYLAY_OTIMIZACOES_DESEMPENHO", "1") or "1"
    ).strip().casefold()
    especifica = str(env_getter(nome, padrao) or padrao).strip().casefold()
    return mestre not in VALORES_DESATIVADOS and especifica not in VALORES_DESATIVADOS


def snapshot_flags_desempenho(
    *,
    env_getter: Callable[[str, str], str | None] = os.getenv,
) -> dict[str, Any]:
    mestre = flag_desempenho_ativa(
        "LAYLAY_OTIMIZACOES_DESEMPENHO", env_getter=env_getter,
    )
    return {
        "modo": "gradual" if mestre else "revertido",
        "mestre_ativa": mestre,
        "flags": {
            nome: flag_desempenho_ativa(flag, env_getter=env_getter)
            for nome, flag in FLAGS_OTIMIZACAO.items()
        },
        "conteudo_exposto": False,
        "autoriza_execucao": False,
    }


class GuardiaoImplantacaoDesempenho:
    """Reverte a sessão após regressões repetidas, nunca por um caso isolado."""

    def __init__(
        self,
        *,
        desativar: Callable[[str], Any],
        publicar_estado: Callable[[Mapping[str, Any]], Any] | None = None,
        clock: Callable[[], float] = time.monotonic,
        janela_s: float = 300.0,
        limite_consecutivo: int = 3,
        limite_janela: int = 4,
    ) -> None:
        self.desativar = desativar
        self.publicar_estado = publicar_estado
        self.clock = clock
        self.janela_s = max(10.0, float(janela_s))
        self.limite_consecutivo = max(2, int(limite_consecutivo))
        self.limite_janela = max(self.limite_consecutivo, int(limite_janela))
        self._eventos: deque[tuple[float, str]] = deque(maxlen=32)
        self._ultimo_sinal = ""
        self._consecutivos = 0
        self._revertido = False
        self._motivo = ""
        self._lock = threading.RLock()
        self._publicar()

    def observar(self, sinal: str) -> bool:
        sinal = str(sinal or "").strip().casefold()
        if sinal not in SINAIS_REGRESSAO:
            return False
        agora = float(self.clock())
        with self._lock:
            if self._revertido:
                return False
            while self._eventos and agora - self._eventos[0][0] > self.janela_s:
                self._eventos.popleft()
            self._eventos.append((agora, sinal))
            if sinal == self._ultimo_sinal:
                self._consecutivos += 1
            else:
                self._ultimo_sinal = sinal
                self._consecutivos = 1
            deve_reverter = (
                self._consecutivos >= self.limite_consecutivo
                or len(self._eventos) >= self.limite_janela
            )
            if not deve_reverter:
                self._publicar()
                return False
            self._revertido = True
            self._motivo = sinal
        try:
            self.desativar(sinal)
        finally:
            self._publicar()
        return True

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "modo": "revertido" if self._revertido else "gradual",
                "revertido": self._revertido,
                "motivo": self._motivo,
                "eventos_janela": len(self._eventos),
                "consecutivos": self._consecutivos,
                "conteudo_exposto": False,
                "autoriza_execucao": False,
            }

    def _publicar(self) -> None:
        if callable(self.publicar_estado):
            try:
                self.publicar_estado(self.snapshot())
            except Exception:
                pass


def sinal_regressao_por_falha(codigo: Any, fallback: Any = "") -> str:
    assinatura = f"{codigo} {fallback}".strip().casefold()
    if "falso_sucesso" in assinatura or "sucesso_sem_evidencia" in assinatura:
        return "falso_sucesso"
    if "contradi" in assinatura:
        return "contradicao"
    if "duplic" in assinatura:
        return "duplicacao"
    if "perda_contexto" in assinatura or "contexto_perdido" in assinatura:
        return "perda_contexto"
    if "fallback" in assinatura and "nenhum" not in assinatura:
        return "fallback"
    return ""
