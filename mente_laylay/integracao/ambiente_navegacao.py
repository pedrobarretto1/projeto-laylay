"""Fachada de leitura e operações do ambiente local e navegador."""

from __future__ import annotations

import urllib.parse
from typing import Any, Callable, Dict


class AmbienteNavegacaoRuntime:
    def __init__(self, *, namespace_getter: Callable[[], Dict[str, Any]], log=print) -> None:
        self.namespace_getter = namespace_getter
        self.log = log

    def _ns(self) -> Dict[str, Any]:
        return self.namespace_getter() or {}

    def atualizar_contexto(self, site=None, termo_busca=None, aba_id=None) -> None:
        ns = self._ns()
        contexto = dict(ns["_percepcao_get"]("contexto_web", {}))
        if site is not None:
            contexto["site"] = site
        if termo_busca is not None:
            contexto["termo_busca"] = termo_busca
        if aba_id is not None:
            contexto["aba_id"] = aba_id
        ns["_percepcao_set"]("contexto_web", contexto)

    def atualizar_contexto_por_url(self, url: str) -> None:
        ns = self._ns()
        dados = ns["_classificar_contexto_por_url_chrome_mente"](url)
        self.atualizar_contexto(**dados)

    def organizar_janelas(self, app_esq: str, app_dir: str):
        ns = self._ns()
        abrir_cb = ns.get("open_app") if ns.get("APP_OPENER_AVAILABLE") else None
        return ns["_organizar_janelas_mente"](
            ns["gw"], ns["pyautogui"], ns["ctypes"], ns["wintypes"],
            app_esq, app_dir, abrir_app_cb=abrir_cb,
        )

    def listar_programas(self) -> list:
        ns = self._ns()
        return ns["_listar_programas_abertos_mente"](ns["gw"], ns["psutil"])

    def listar_abas(self, timeout_s: float = 5.0) -> list:
        abas_brutas = self._ns()["solicitar_lista_abas"](timeout_s=timeout_s)
        resultado = []
        for aba in abas_brutas if isinstance(abas_brutas, list) else []:
            if not isinstance(aba, dict):
                continue
            titulo = str(aba.get("title") or "").strip()
            url = str(aba.get("url") or "").strip()
            if titulo or url:
                resultado.append({"titulo": titulo, "url": url})
        self.log(f"🌐 [VERIFICAR_ABAS] Abas encontradas: {len(resultado)}")
        return resultado

    def resolver_alvo(self, nome: str) -> Dict[str, Any]:
        ns = self._ns()
        alvo = str(nome or "").strip()
        normalizado = ns["_normalizar_alvo_ambiente"](alvo)
        if not normalizado:
            return {
                "programa_aberto": False, "programa_em_foco": False,
                "aba_aberta": False, "preferido": "desconhecido", "url": "", "titulo": "",
            }
        try:
            programas = self.listar_programas()
        except Exception:
            programas = []
        try:
            abas = self.listar_abas()
        except Exception:
            abas = []
        return ns["_resolver_alvo_ambiente_mente"](
            alvo, programas, abas, ns["_janela_app_esta_em_foco"]
        )

    def abrir_url(self, url: str, auto_click: bool = False, permitir_foco: bool = False) -> bool:
        ns = self._ns()
        modo_jogo = ns.get("_modo_jogo_runtime")
        preservar_foco = bool(getattr(modo_jogo, "ativo", False)) and not bool(permitir_foco)
        return bool(ns["_abrir_url_reutilizando_aba_chrome_mente"](
            url,
            conectado=ns["_chrome_solicitacoes"].conectado,
            solicitar_lista_abas=ns["solicitar_lista_abas"],
            enviar_comando=ns["enviar_comando_chrome"],
            abrir_fallback=lambda alvo: (
                False if preservar_foco else ns["webbrowser"].open(alvo, new=2)
            ),
            auto_click=auto_click,
            preservar_foco=preservar_foco,
        ))

    def montar_url(self, alvo: str) -> str:
        ns = self._ns()
        texto = str(alvo or "").strip()
        if not texto:
            return ""
        normalizado = ns["_normalizar_texto_com_apelidos"](texto)
        if ns["is_valid_url"](texto):
            return texto
        sites = ns.get("SITES_DIRECTOS", {})
        if normalizado in sites:
            return str(sites[normalizado])
        if "." in normalizado and " " not in normalizado:
            return str(ns["formatar_url_ou_busca"](normalizado) or "")
        return f"https://www.google.com/search?q={urllib.parse.quote(texto)}"

    def fechar_abas_vazias(self):
        ns = self._ns()
        return ns["_fechar_abas_vazias_chrome_mente"](
            solicitar_abas=ns["solicitar_lista_abas"],
            enviar_comando=ns["enviar_comando_chrome"],
        )

    def eh_alvo_site_web(self, texto: str) -> bool:
        ns = self._ns()
        return bool(ns["_eh_alvo_site_web_mente"](
            texto,
            normalizar_texto=ns["_normalizar_texto_com_apelidos"],
            sites_web_alias=ns["SITES_WEB_ALIAS"],
            sites_directos=ns["SITES_DIRECTOS"],
        ))

    def contexto_aponta_site_web(self, texto: str = "") -> bool:
        ns = self._ns()
        return bool(ns["_contexto_aponta_site_web_mente"](
            texto,
            normalizar_texto=ns["_normalizar_texto_com_apelidos"],
            mente_integrada_estado=ns["_estado_compartilhado_runtime"].mental,
            contexto_perceptivo=ns["_obter_contexto_perceptivo"](),
        ))


def criar_ambiente_navegacao_runtime(**kwargs: Any) -> AmbienteNavegacaoRuntime:
    return AmbienteNavegacaoRuntime(**kwargs)
