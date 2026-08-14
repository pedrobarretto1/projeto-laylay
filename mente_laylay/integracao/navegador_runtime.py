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
        return bool(self.tocar_youtube_detalhado(
            url, tab_id=tab_id, permitir_foco=permitir_foco,
        ).get("ok"))

    def tocar_youtube_detalhado(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "url": str(url or "").strip(),
            "permitir_foco": bool(permitir_foco),
        }
        if isinstance(tab_id, int):
            payload["target_tab_id"] = tab_id
        enviar_detalhado = getattr(self.comandos, "enviar_detalhado", None)
        if callable(enviar_detalhado):
            resultado = dict(enviar_detalhado("youtube_play", payload) or {})
            status = str(resultado.get("status") or "").strip().casefold()
            if status == "autoplay_blocked":
                aba = resultado.get("tab")
                aba = aba if isinstance(aba, dict) else {}
                aba_id = aba.get("id")
                if not isinstance(aba_id, int):
                    aba_id = aba.get("tabId")
                if not isinstance(aba_id, int):
                    aba_id = tab_id
                if isinstance(aba_id, int):
                    segunda_tentativa = self.controlar_youtube_detalhado(
                        "play", tab_id=aba_id,
                    )
                    evidencia = segunda_tentativa.get("evidence")
                    evidencia = evidencia if isinstance(evidencia, dict) else {}
                    confirmou_play = bool(
                        segunda_tentativa.get("ok") is True
                        and segunda_tentativa.get("confirmado") is True
                        and evidencia.get("playing") is True
                        and evidencia.get("audible") is True
                    )
                    if confirmou_play:
                        return {
                            **resultado,
                            **segunda_tentativa,
                            "ok": True,
                            "confirmado": True,
                            "status": "playing_confirmed",
                            "message": "",
                            "tab": segunda_tentativa.get("tab") or aba,
                            "evidence": evidencia,
                            "retry_status": str(
                                segunda_tentativa.get("status") or ""
                            ).strip(),
                        }
                    return {
                        **resultado,
                        "retry_status": str(
                            segunda_tentativa.get("status") or ""
                        ).strip(),
                        "retry_evidence": segunda_tentativa.get("evidence"),
                    }
            return resultado
        ok = bool(self.comandos.enviar("youtube_play", payload))
        return {
            "ok": ok, "confirmado": True if ok else False,
            "status": "confirmacao_legada" if ok else "falha_execucao",
        }

    def controlar_youtube(
        self, comando: str, *, tab_id: int | None = None,
    ) -> bool:
        return bool(self.controlar_youtube_detalhado(
            comando, tab_id=tab_id,
        ).get("ok"))

    def controlar_youtube_detalhado(
        self,
        comando: str,
        *,
        tab_id: int | None = None,
        queue_item_id: str = "",
        queue_index: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "command": str(comando or "").strip(),
        }
        if isinstance(tab_id, int):
            payload["target_tab_id"] = tab_id
        if queue_item_id:
            payload["queue_item_id"] = str(queue_item_id).strip()
        if isinstance(queue_index, int) and not isinstance(queue_index, bool):
            payload["queue_index"] = queue_index
        enviar_detalhado = getattr(self.comandos, "enviar_detalhado", None)
        if callable(enviar_detalhado):
            return dict(enviar_detalhado("youtube_control", payload) or {})
        ok = bool(self.comandos.enviar("youtube_control", payload))
        return {
            "ok": ok, "confirmado": True if ok else False,
            "status": "confirmacao_legada" if ok else "falha_execucao",
        }

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

    def abrir_primeiro_resultado(self, consulta: str = "") -> bool:
        return bool(self.comandos.enviar(
            "click_first_result",
            {"query": str(consulta or "").strip()},
        ))

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
