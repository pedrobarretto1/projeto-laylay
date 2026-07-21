"""Ponte entre os handlers WebSocket e o estado vivo da Laylay."""

from __future__ import annotations

from typing import Any, Callable, Dict
import time

from mente_laylay.integracao.chrome_page_data import processar_page_data
from mente_laylay.integracao.pc_b_integracao import processar_mensagem_pc_b


class ChromeWsContextoRuntime:
    DEPENDENCIAS_BASE = (
        "_estado_compartilhado_runtime", "_percepcao_get", "_percepcao_set",
        "_conversa_estado_get", "_continuidades_get", "_continuidades_update",
        "_chrome_estado", "_contexto_paginas", "falar_com_lipsync",
    )

    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        monitor_saude: Any = None,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.monitor_saude = monitor_saude

    def _ns(self) -> Dict[str, Any]:
        return self.namespace_getter() or {}

    def validar_conexoes(self) -> Dict[str, Any]:
        ns = self._ns()
        if self.monitor_saude is not None:
            return self.monitor_saude.validar_dependencias(
                "chrome_contexto",
                ns,
                self.DEPENDENCIAS_BASE,
                callables=(
                    "_percepcao_get", "_percepcao_set", "_conversa_estado_get",
                    "_continuidades_get", "_continuidades_update", "falar_com_lipsync",
                ),
            )
        ausentes = [nome for nome in self.DEPENDENCIAS_BASE if nome not in ns]
        return {"status": "saudavel" if not ausentes else "degradado", "ausentes": ausentes}

    def contexto_usuario(self) -> Dict[str, Any]:
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        return {
            "estado_percepcao": estado.snapshot()["percepcao"],
            "contexto_sistema": ns["_percepcao_get"]("contexto_sistema", {}),
            "is_speaking": bool(ns["_conversa_estado_get"]("is_speaking", False)),
            "ultimo_open_site": estado.obter_copia(
                "percepcao", "ultimo_open_site", {"ts": 0.0, "topic": "", "url": ""}
            ),
            "sugestao_bloqueada_ate": ns["_continuidades_get"](
                "sugestoes_bloqueadas_ate", {}
            ),
            "_ultimo_sugerido_ts": ns["_percepcao_get"]("ultimo_sugerido_ts", 0.0),
            "_ultimo_proativo_ts": ns["_percepcao_get"]("ultimo_proativo_ts", 0.0),
            "fish_mode_active": bool(ns["_percepcao_get"]("fish_mode_active", False)),
            "_contexto_navegador_relevante": ns["_contexto_navegador_relevante"],
            "_registrar_log_navegador": ns["_registrar_log_navegador_mente"],
            "_continuidades_get": ns["_continuidades_get"],
            "_continuidades_update": ns["_continuidades_update"],
            "falar_com_lipsync": ns["falar_com_lipsync"],
        }

    def aplicar_updates_usuario(self, updates: Dict[str, Any]) -> None:
        ns = self._ns()
        if "estado_percepcao" in updates:
            retrato = updates.get("estado_percepcao")
            if isinstance(retrato, dict):
                ns["_estado_compartilhado_runtime"].mesclar_campos(
                    "percepcao", **retrato,
                )
        if "fish_mode_active" in updates:
            ns["_percepcao_set"](
                "fish_mode_active", bool(updates.get("fish_mode_active"))
            )
        if "fish_mode_started_ts" in updates:
            ns["_percepcao_set"](
                "fish_mode_started_ts",
                float(updates.get("fish_mode_started_ts") or 0.0),
            )
        if "_ultimo_sugerido_ts" in updates:
            ns["_percepcao_set"]("ultimo_sugerido_ts", float(updates.get("_ultimo_sugerido_ts") or 0.0))
        if "_ultimo_proativo_ts" in updates:
            ns["_percepcao_set"]("ultimo_proativo_ts", float(updates.get("_ultimo_proativo_ts") or 0.0))

    def contexto_acao(self) -> Dict[str, Any]:
        ns = self._ns()
        return ns["_chrome_estado"].contexto_handler({
            "_musica_busca_query": ns["_busca_musical_runtime"].query,
            "_musica_ultima_verificada": ns.get("_musica_ultima_verificada"),
            "_percepcao_set": ns["_percepcao_set"],
            "atualizar_contexto_por_url": ns["atualizar_contexto_por_url"],
            "_musica_registrar_historico": ns["_musica_registrar_historico"],
            "_verificar_musica_autonoma": ns["_verificar_musica_autonoma"],
            "falar_com_lipsync": ns["falar_com_lipsync"],
            "_registrar_musica_atual": self.registrar_musica_atual,
        })

    def registrar_musica_atual(self, titulo: str, status: str = "tocando", url: str = "") -> None:
        titulo_limpo = str(titulo or "").strip()
        if not titulo_limpo:
            return
        estado = self._ns()["_estado_compartilhado_runtime"]
        estado.atualizar_campos(
            "mental",
            musica_atual_titulo=titulo_limpo,
            musica_atual_url=str(url or "").strip(),
            musica_atual_status=str(status or "tocando").strip(),
            musica_atual_ts=time.time(),
        )

    def aplicar_updates_acao(self, updates: Dict[str, Any]) -> None:
        ns = self._ns()
        ns["_chrome_estado"].aplicar_updates(updates)
        if "_musica_ultima_verificada" in updates:
            valor = str(updates.get("_musica_ultima_verificada") or "")
            ns["_musica_ultima_verificada"] = valor
            ns["_busca_musical_runtime"].ultima_verificada = valor

    def processar_pc_b(self, data: Dict[str, Any]) -> bool:
        ns = self._ns()
        return processar_mensagem_pc_b(data, {
            "registrar_status_pc_b": getattr(ns.get("_pc_b_runtime"), "registrar_status", None),
            "_analisar_com_groq": ns["_analisar_com_groq"],
            "registrar_memoria_visual": ns["registrar_memoria_visual"],
            "current_emotion": ns["_conversa_estado_get"]("current_emotion", "calma"),
            "emotion_level": ns["_conversa_estado_get"]("emotion_level", 1),
            "falar_com_lipsync": ns["falar_com_lipsync"],
            "messages": ns["_memoria_conversa_get"]("messages", []),
            "enviar_mensagem": ns["enviar_mensagem"],
            "limpar_resposta_da_ia": ns["limpar_resposta_da_ia"],
        })

    def processar_pagina(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ns = self._ns()
        return processar_page_data(data, {
            "armazenar_contexto_pagina": ns["armazenar_contexto_pagina"],
            "resumir_pagina_no_dicionario": ns["resumir_pagina_no_dicionario"],
            "EVENTO_PAGINA": ns["EVENTO_PAGINA"],
        })

    def aplicar_updates_pagina(self, updates: Dict[str, Any]) -> None:
        if isinstance(updates, dict) and "ULTIMO_CONTEUDO_PAGINA" in updates:
            ns = self._ns()
            paginas = ns["_contexto_paginas"]
            paginas.definir_ultimo_conteudo(updates.get("ULTIMO_CONTEUDO_PAGINA") or "")
            pagina = paginas.atual()
            if pagina:
                ns["_estado_compartilhado_runtime"].atualizar_campos(
                    "mental",
                    conteudo_atual={
                        "tipo": "pagina",
                        "titulo": str(pagina.get("title") or ""),
                        "descricao": str(pagina.get("content") or "")[:1200],
                        "url": str(pagina.get("url") or ""),
                        "status": "visivel",
                        "fonte": "extensao_chrome",
                        "ts": float(pagina.get("ts") or time.time()),
                        "confianca": 0.96,
                    },
                )


def criar_chrome_ws_contexto_runtime(**kwargs: Any) -> ChromeWsContextoRuntime:
    return ChromeWsContextoRuntime(**kwargs)
