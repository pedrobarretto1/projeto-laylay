from __future__ import annotations

from typing import Any, Callable


class NavegadorLeituraFake:
    def __init__(self, *, aba: dict | None = None, abas: list[dict] | None = None) -> None:
        self.aba = dict(aba or {})
        self.abas = list(abas or [])

    def conectado(self) -> bool:
        return True

    def aba_ativa(self, timeout_s: float = 4.0) -> dict[str, Any]:
        return dict(self.aba)

    def listar_abas(self, timeout_s: float = 5.0) -> list[dict[str, Any]]:
        return [dict(aba) for aba in self.abas]

    def diagnostico(self) -> dict[str, Any]:
        return {
            "conectado": True,
            "leitura_aba_disponivel": True,
            "listagem_disponivel": True,
        }


class NavegadorOperacoesFake:
    def __init__(
        self,
        *,
        resultado: bool = True,
        abrir_cb: Callable[..., Any] | None = None,
    ) -> None:
        self.resultado = bool(resultado)
        self.abrir_cb = abrir_cb
        self.chamadas: list[tuple[str, dict[str, Any]]] = []

    def _registrar(self, acao: str, payload: dict[str, Any]) -> bool:
        self.chamadas.append((acao, payload))
        return self.resultado

    def abrir_url(self, url: str, *, auto_click: bool = False, permitir_foco: bool = False) -> bool:
        if callable(self.abrir_cb):
            return bool(self.abrir_cb(
                url, auto_click=auto_click, permitir_foco=permitir_foco,
            ))
        return self._registrar("open_url", {
            "url": url, "auto_click": auto_click, "permitir_foco": permitir_foco,
        })

    def pesquisar_youtube(self, consulta: str, *, permitir_foco: bool = False) -> bool:
        return self._registrar("youtube_search", {
            "query": consulta, "permitir_foco": permitir_foco,
        })

    def tocar_youtube(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> bool:
        payload: dict[str, Any] = {"url": url, "permitir_foco": permitir_foco}
        if isinstance(tab_id, int):
            payload["target_tab_id"] = tab_id
        return self._registrar("youtube_play", payload)

    def tocar_youtube_detalhado(
        self, url: str, *, tab_id: int | None = None, permitir_foco: bool = False,
    ) -> dict[str, Any]:
        ok = self.tocar_youtube(
            url, tab_id=tab_id, permitir_foco=permitir_foco,
        )
        return {
            "ok": ok, "confirmado": ok,
            "status": "playing_confirmed" if ok else "falha_execucao",
        }

    def controlar_youtube(self, comando: str, *, tab_id: int | None = None) -> bool:
        payload: dict[str, Any] = {"command": comando}
        if isinstance(tab_id, int):
            payload["target_tab_id"] = tab_id
        return self._registrar("youtube_control", payload)

    def controlar_youtube_detalhado(
        self, comando: str, *, tab_id: int | None = None,
    ) -> dict[str, Any]:
        try:
            ok = self.controlar_youtube(comando, tab_id=tab_id)
        except TypeError:
            ok = self.controlar_youtube(comando)
        return {
            "ok": ok, "confirmado": ok,
            "status": "success" if ok else "falha_execucao",
        }

    def fechar_aba(self, alvo: str) -> bool:
        return self._registrar("close_specific_tab", {"target": alvo})

    def fechar_aba_atual(self) -> bool:
        return self._registrar("close_current_tab", {})

    def fechar_abas(self, ids: list[int]) -> bool:
        return self._registrar("close_tabs", {"ids": list(ids)})

    def focar_aba(self, tab_id: int) -> bool:
        return self._registrar("focus_tab", {"tabId": tab_id})

    def recarregar_url(self, url: str) -> bool:
        return self._registrar("reload_url", {"url": url})

    def fechar_aba_nativa(self, alvo: str = "") -> bool:
        return self._registrar("close_native", {"target": alvo})

    def fechar_abas_vazias(self) -> bool:
        return self._registrar("close_empty_tabs", {})

    def abrir_primeiro_resultado(self, consulta: str = "") -> bool:
        return self._registrar("click_first_result", {"query": consulta})

    def clicar(self, seletor: str) -> bool:
        return self._registrar("click", {"selector": seletor})

    def digitar(self, seletor: str, texto: str) -> bool:
        return self._registrar("type", {"selector": seletor, "text": texto})

    def pressionar(self, tecla: str) -> bool:
        return self._registrar("press", {"key": tecla})

    def diagnostico(self) -> dict[str, Any]:
        return {
            "comandos_disponiveis": True,
            "navegacao_disponivel": True,
            "controle_pagina_disponivel": True,
            "fechamento_nativo_disponivel": True,
        }
