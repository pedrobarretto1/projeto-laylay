"""Fachada de leitura e operações do ambiente local e navegador."""

from __future__ import annotations

import urllib.parse
from typing import Any, Callable, Dict, Mapping


DEPENDENCIAS_AMBIENTE_NAVEGACAO = (
    "_percepcao_get", "_percepcao_set", "_classificar_contexto_por_url_chrome_mente",
    "open_app", "APP_OPENER_AVAILABLE", "_organizar_janelas_mente", "gw",
    "pyautogui", "ctypes", "wintypes", "_listar_programas_abertos_mente",
    "psutil", "_normalizar_alvo_ambiente",
    "_resolver_alvo_ambiente_mente", "_janela_app_esta_em_foco",
    "_modo_jogo_runtime", "_abrir_url_reutilizando_aba_chrome_mente",
    "webbrowser",
    "_normalizar_texto_com_apelidos", "is_valid_url", "SITES_DIRECTOS",
    "formatar_url_ou_busca", "_fechar_abas_vazias_chrome_mente",
    "_eh_alvo_site_web_mente", "SITES_WEB_ALIAS",
    "_contexto_aponta_site_web_mente", "_estado_compartilhado_runtime",
    "_obter_contexto_perceptivo", "_listar_processos_audio_ativos_mente",
    "_planejar_organizacao_janelas_mente",
)


class AmbienteNavegacaoRuntime:
    def __init__(
        self, *, servicos_iniciais: Mapping[str, Any] | None = None,
        namespace_getter: Callable[[], Dict[str, Any]] | None = None, log=print,
    ) -> None:
        origem = dict(servicos_iniciais or {})
        if not origem and callable(namespace_getter):
            origem = dict(namespace_getter() or {})
        self._servicos = self._filtrar(origem)
        self._solicitacoes: Any = None
        self._comandos: Any = None
        self.log = log

    @staticmethod
    def _filtrar(servicos: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            nome: servicos[nome]
            for nome in DEPENDENCIAS_AMBIENTE_NAVEGACAO
            if nome in servicos
        }

    def _ns(self) -> Dict[str, Any]:
        return dict(self._servicos)

    def conectar_servicos(self, servicos: Mapping[str, Any]) -> None:
        self._servicos = self._filtrar(servicos)

    def conectar_navegador(self, *, solicitacoes: Any, comandos: Any) -> None:
        """Conecta transportes explícitos sem reabrir o namespace geral."""
        if not callable(getattr(solicitacoes, "solicitar_lista_abas", None)):
            raise RuntimeError("solicitações do navegador sem listagem de abas")
        if not callable(getattr(comandos, "enviar", None)):
            raise RuntimeError("executor do navegador sem envio validado")
        self._solicitacoes = solicitacoes
        self._comandos = comandos

    @property
    def servicos_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))

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
            psutil_mod=ns.get("psutil"),
            processos_audio_ativos_cb=ns.get("_listar_processos_audio_ativos_mente"),
        )

    def planejar_organizacao_janelas(self) -> dict:
        """Produz um plano local de layout sem mover nenhuma janela."""
        ns = self._ns()
        planejar = ns.get("_planejar_organizacao_janelas_mente")
        if not callable(planejar):
            return {
                "ok": False, "confirmado": False,
                "status": "planejador_indisponivel", "prioridades": [],
            }
        resultado = dict(planejar(
            ns.get("gw"),
            ctypes_mod=ns.get("ctypes"),
            wintypes_mod=ns.get("wintypes"),
            psutil_mod=ns.get("psutil"),
            processos_audio_ativos_cb=ns.get("_listar_processos_audio_ativos_mente"),
        ) or {})
        return {
            chave: valor for chave, valor in resultado.items()
            if not str(chave).startswith("_")
        }

    def listar_programas(self) -> list:
        ns = self._ns()
        return ns["_listar_programas_abertos_mente"](ns["gw"], ns["psutil"])

    def listar_abas(self, timeout_s: float = 5.0) -> list:
        if self._solicitacoes is None:
            return []
        abas_brutas = self._solicitacoes.solicitar_lista_abas(timeout_s=timeout_s)
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
        if self._solicitacoes is None or self._comandos is None:
            return False
        modo_jogo = ns.get("_modo_jogo_runtime")
        preservar_foco = bool(getattr(modo_jogo, "ativo", False)) and not bool(permitir_foco)
        return bool(ns["_abrir_url_reutilizando_aba_chrome_mente"](
            url,
            conectado=self._solicitacoes.conectado,
            solicitar_lista_abas=self._solicitacoes.solicitar_lista_abas,
            enviar_comando=self._comandos.enviar,
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
        if self._solicitacoes is None or self._comandos is None:
            return False
        return ns["_fechar_abas_vazias_chrome_mente"](
            solicitar_abas=self._solicitacoes.solicitar_lista_abas,
            enviar_comando=self._comandos.enviar,
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
