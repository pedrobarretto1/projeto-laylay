"""Adaptadores estreitos do runtime visual para os registros tipados."""

from __future__ import annotations

from threading import RLock
from typing import Any, Mapping

from .sessao_jogo import identificar_jogo


class VisaoJogoLeituraRuntime:
    def __init__(self, *, visao: Any) -> None:
        self.visao = visao

    def em_andamento(self) -> bool:
        return bool(self.visao.em_andamento)

    def tem_analise_recente(self, max_idade_s: float = 900.0) -> bool:
        return bool(self.visao.tem_analise_recente(max_idade_s=max_idade_s))

    def observar_texto_usuario(self, texto: str) -> dict[str, Any]:
        return dict(self.visao.observar_texto_usuario(texto) or {})

    def perfil_atual(self) -> dict[str, Any]:
        contexto = dict(self.visao.contexto_jogo() or {})
        if not bool(contexto.get("ativo")):
            return {}
        identidade = identificar_jogo(contexto)
        return dict(self.visao.sessoes.perfil(identidade) or {})

    def diagnostico(self) -> dict[str, Any]:
        try:
            contexto_ativo = bool(dict(self.visao.contexto_jogo() or {}).get("ativo"))
        except Exception:
            contexto_ativo = False
        return {
            "habilitado": bool(self.visao.habilitado),
            "credencial_disponivel": bool(self.visao.credencial_disponivel),
            "em_andamento": self.em_andamento(),
            "analise_recente": self.tem_analise_recente(),
            "contexto_jogo_ativo": contexto_ativo,
            "captura_persistida": False,
            "imagem_exposta": False,
            "autoriza_execucao": False,
        }


class VisaoJogoAnaliseRuntime:
    def __init__(self, *, visao: Any) -> None:
        self.visao = visao
        self._lock = RLock()
        self._metricas = {
            "solicitacoes": 0, "aceitas": 0, "recusadas": 0, "falhas": 0,
        }

    def _chamar(self, nome: str, *args: Any) -> bool:
        with self._lock:
            self._metricas["solicitacoes"] += 1
        try:
            ok = bool(getattr(self.visao, nome)(*args))
        except Exception:
            with self._lock:
                self._metricas["falhas"] += 1
            raise
        with self._lock:
            self._metricas["aceitas" if ok else "recusadas"] += 1
        return ok

    def executar(self, params: Mapping[str, Any] | None) -> bool:
        return self._chamar("executar", dict(params or {}))

    def aplicar_referencia_item(self, texto: str) -> bool:
        return self._chamar("aplicar_referencia_item", texto)

    def continuar_analise_recente(self, texto: str) -> bool:
        return self._chamar("continuar_analise_recente", texto)

    def continuar_pendencia(
        self, texto: str, pendencia: Mapping[str, Any] | None,
    ) -> bool:
        return self._chamar("continuar_pendencia", texto, dict(pendencia or {}))

    def processar_atualizacao_perfil(self, texto: str) -> bool:
        return self._chamar("processar_atualizacao_perfil", texto)

    def diagnostico(self) -> dict[str, Any]:
        with self._lock:
            metricas = dict(self._metricas)
        return {
            "analise_disponivel": bool(
                self.visao.habilitado and self.visao.credencial_disponivel
            ),
            "continuidade_disponivel": True,
            **metricas,
            "captura_exposta": False,
            "prompt_exposto": False,
            "autoriza_execucao": False,
        }


def criar_visao_jogo_leitura_runtime(**kwargs: Any) -> VisaoJogoLeituraRuntime:
    return VisaoJogoLeituraRuntime(**kwargs)


def criar_visao_jogo_analise_runtime(**kwargs: Any) -> VisaoJogoAnaliseRuntime:
    return VisaoJogoAnaliseRuntime(**kwargs)
