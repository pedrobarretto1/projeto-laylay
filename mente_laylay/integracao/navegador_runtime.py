"""Composicao do navegador atras de contratos tipados.

Este runtime nao classifica intencoes nem autoriza acoes. O porteiro e os
executores continuam decidindo se uma operacao pode ser realizada.
"""

from __future__ import annotations

from typing import Any, Callable


class NavegadorLeituraRuntime:
    def __init__(self, *, solicitacoes: Any, ambiente: Any) -> None:
        self.solicitacoes = solicitacoes
        self.ambiente = ambiente

    def conectado(self) -> bool:
        return bool(self.solicitacoes.conectado())

    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        return dict(self.solicitacoes.solicitar_aba_ativa(timeout_s=timeout_s) or {})

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return list(self.ambiente.listar_abas(timeout_s=timeout_s) or [])

    def diagnostico(self) -> dict[str, Any]:
        return {
            "conectado": self.conectado(),
            "leitura_aba_disponivel": callable(
                getattr(self.solicitacoes, "solicitar_aba_ativa", None)
            ),
            "listagem_disponivel": callable(getattr(self.ambiente, "listar_abas", None)),
        }


class NavegadorOperacoesRuntime:
    def __init__(
        self,
        *,
        comandos: Any,
        ambiente: Any,
        fechar_aba_nativa: Callable[[str], Any] | None = None,
    ) -> None:
        self.comandos = comandos
        self.ambiente = ambiente
        self._fechar_aba_nativa = fechar_aba_nativa

    def abrir_url(self, url: str, *, auto_click: bool = False, permitir_foco: bool = False) -> bool:
        return bool(self.ambiente.abrir_url(
            str(url or "").strip(),
            auto_click=bool(auto_click),
            permitir_foco=bool(permitir_foco),
        ))

    def pesquisar_youtube(self, consulta: str, *, permitir_foco: bool = False) -> bool:
        return bool(self.comandos.enviar(
            "youtube_search", {
                "query": str(consulta or "").strip(),
                "permitir_foco": bool(permitir_foco),
            },
        ))

    def tocar_youtube(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> bool:
        payload: dict[str, Any] = {
            "url": str(url or "").strip(),
            "permitir_foco": bool(permitir_foco),
        }
        if isinstance(tab_id, int):
            payload["target_tab_id"] = tab_id
        return bool(self.comandos.enviar("youtube_play", payload))

    def controlar_youtube(self, comando: str) -> bool:
        return bool(self.comandos.enviar(
            "youtube_control", {"command": str(comando or "").strip()},
        ))

    def fechar_aba(self, alvo: str) -> bool:
        alvo = str(alvo or "").strip()
        return bool(alvo and self.comandos.enviar(
            "close_specific_tab", {"target": alvo},
        ))

    def fechar_aba_atual(self) -> bool:
        return bool(self.comandos.enviar("close_current_tab", {}))

    def fechar_abas(self, ids: list[int]) -> bool:
        validos = [valor for valor in ids if isinstance(valor, int)]
        return bool(validos and self.comandos.enviar("close_tabs", {"ids": validos}))

    def recarregar_url(self, url: str) -> bool:
        return bool(self.comandos.enviar(
            "reload_url", {"url": str(url or "").strip()},
        ))

    def fechar_aba_nativa(self, alvo: str = "") -> bool:
        return bool(
            callable(self._fechar_aba_nativa)
            and self._fechar_aba_nativa(str(alvo or "").strip())
        )

    def fechar_abas_vazias(self) -> bool:
        return bool(self.ambiente.fechar_abas_vazias())

    def clicar(self, seletor: str) -> bool:
        return bool(self.comandos.enviar(
            "click", {"selector": str(seletor or "").strip()},
        ))

    def digitar(self, seletor: str, texto: str) -> bool:
        return bool(self.comandos.enviar(
            "type", {
                "selector": str(seletor or "").strip(),
                "text": str(texto or ""),
            },
        ))

    def pressionar(self, tecla: str) -> bool:
        return bool(self.comandos.enviar(
            "press", {"key": str(tecla or "").strip().casefold()},
        ))

    def diagnostico(self) -> dict[str, Any]:
        return {
            "comandos_disponiveis": callable(getattr(self.comandos, "enviar", None)),
            "navegacao_disponivel": callable(getattr(self.ambiente, "abrir_url", None)),
            "controle_pagina_disponivel": callable(getattr(self.comandos, "enviar", None)),
            "fechamento_nativo_disponivel": callable(self._fechar_aba_nativa),
        }


def criar_navegador_leitura_runtime(**kwargs: Any) -> NavegadorLeituraRuntime:
    return NavegadorLeituraRuntime(**kwargs)


def criar_navegador_operacoes_runtime(**kwargs: Any) -> NavegadorOperacoesRuntime:
    return NavegadorOperacoesRuntime(**kwargs)
