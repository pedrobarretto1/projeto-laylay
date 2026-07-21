"""Montadores de contexto do ciclo principal de resposta da Laylay.

Este modulo nao interpreta, nao executa comandos e nao fala com o usuario.
Ele apenas organiza os contratos que ligam `laylay.py` aos modulos da mente.
"""

from __future__ import annotations

from typing import Any, Callable, Dict


def _merge_grupos(*grupos: Dict[str, Any] | None) -> Dict[str, Any]:
    contexto: Dict[str, Any] = {}
    for grupo in grupos:
        if isinstance(grupo, dict):
            contexto.update(grupo)
    return contexto


def montar_contexto_dispatcher_comandos(
    *,
    base: Dict[str, Any] | None = None,
    navegacao: Dict[str, Any] | None = None,
    musica: Dict[str, Any] | None = None,
    arquivos: Dict[str, Any] | None = None,
    percepcao: Dict[str, Any] | None = None,
    agenda_email: Dict[str, Any] | None = None,
    execucao: Dict[str, Any] | None = None,
    autonomia: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Contexto usado pelo dispatcher de comandos JSON.

    A separacao por grupos deixa claro qual parte da mente fornece cada
    capacidade, sem transformar esses grupos em cerebros separados.
    """
    return _merge_grupos(
        base,
        navegacao,
        musica,
        arquivos,
        percepcao,
        agenda_email,
        execucao,
        autonomia,
    )


class ContextoDispatcherRuntime:
    """Monta o contrato do dispatcher com estado vivo da mesma mente."""

    def __init__(
        self,
        *,
        base: Dict[str, Any],
        navegacao: Dict[str, Any],
        musica: Dict[str, Any],
        arquivos: Dict[str, Any],
        percepcao: Dict[str, Any],
        agenda_email: Dict[str, Any],
        execucao: Dict[str, Any],
        autonomia: Dict[str, Any],
        estado_getter: Callable[[], Dict[str, Any]],
    ) -> None:
        self.base = dict(base or {})
        self.navegacao = dict(navegacao or {})
        self.musica = dict(musica or {})
        self.arquivos = dict(arquivos or {})
        self.percepcao = dict(percepcao or {})
        self.agenda_email = dict(agenda_email or {})
        self.execucao = dict(execucao or {})
        self.autonomia = dict(autonomia or {})
        self.estado_getter = estado_getter

    def montar(self) -> Dict[str, Any]:
        try:
            estado = self.estado_getter() or {}
        except Exception:
            estado = {}
        estado = estado if isinstance(estado, dict) else {}

        base = dict(self.base)
        base.update(
            {
                "messages": estado.get("messages"),
                "current_emotion": estado.get("current_emotion", "calma"),
                "emotion_level": estado.get("emotion_level", 1),
            }
        )
        navegacao = dict(self.navegacao)
        musica = dict(self.musica)
        musica["playlists_carregadas"] = estado.get("playlists_carregadas", {})
        agenda_email = dict(self.agenda_email)
        agenda_email["_gmail_nao_lidos_cache"] = estado.get("_gmail_nao_lidos_cache", [])
        execucao = dict(self.execucao)

        return montar_contexto_dispatcher_comandos(
            base=base,
            navegacao=navegacao,
            musica=musica,
            arquivos=self.arquivos,
            percepcao=self.percepcao,
            agenda_email=agenda_email,
            execucao=execucao,
            autonomia=self.autonomia,
        )


def criar_contexto_dispatcher_runtime(**kwargs: Any) -> ContextoDispatcherRuntime:
    return ContextoDispatcherRuntime(**kwargs)


DEPENDENCIAS_EXECUCAO_INTENCAO = (
    "_target_from_params", "_registrar_mente_curta", "_registrar_resultado_execucao",
    "falar_com_lipsync", "_enviar_pc_b", "APPS_MAP", "abrir_url_com_reciclagem",
    "abrir_programa", "fechar_programa", "enviar_comando_chrome", "criar_pasta",
    "criar_ou_editar_arquivo", "deletar_item", "resolver_caminho", "mover_arquivo",
    "ajustar_volume_sistema", "ajustar_volume_sistema_relativo", "definir_mudo_sistema", "solicitar_aba_ativa",
    "fechar_aba_ativa_nativa", "organizar_janelas_robusto", "ativar_tela_cheia_robusta",
    "focar_janela_app", "_gmail_falar_resumo_estiloso", "_gmail_buscar_nao_lidos",
    "_gmail_silenciar_remetente", "repetir_briefing", "obter_clima_localidade",
    "_agendamentos_load", "_agendamentos_save", "_agendamentos_transacionar", "_fala_agendamentos_estilosa",
    "_normalizar_query_musical", "_yt_clean_title", "_buscar_primeiro_video_youtube",
    "_playlist_nome_explicito_na_frase", "_playlist_shuffle_start",
    "_playlist_primeira_url", "_playlist_item_at", "delete_playlist", "playlist_len",
    "play_playlist", "_registrar_estrutura_arquivo_recente", "ADD_TO_PLAYLIST",
    "LIST_PLAYLIST_CONTENT", "_fala_playlist_conteudo_estilosa",
    "_pedido_lista_geral_playlist", "_listar_playlists_salvas",
    "_listar_playlists_da_laylay", "_copiar_faixa_da_playlist_laylay",
    "extrair_nome_playlist", "_resolver_query_musical_por_estilo",
    "_contexto_aponta_site_web", "_eh_alvo_site_web", "_resolver_alvo_ambiente",
    "_normalizar_texto_com_apelidos", "_montar_url_site_ou_busca",
    "_executar_fechar_abas_paradas", "_executar_captura_tela_intent",
    "_bloquear_playlist_temporariamente", "_autonomia_permite_execucao_musical",
    "_registrar_autoaprimoramento", "_resumo_agendamentos_para_prompt",
    "_extrair_agendamento_local", "_playlist_avancar_proxima",
    "_playlist_voltar_anterior", "playlist_state", "SITES_DIRECTOS",
    "APP_OPENER_AVAILABLE", "open_app", "_contexto_aponta_descanso",
    "_executar_controle_midia_nativo", "validar_e_enviar_comando",
    "_remover_prefixo_exec", "limpar_resposta", "enviar_mensagem",
    "_resumo_mente_integrada_para_prompt", "_texto_indica_autocorrecao",
    "_registrar_autocorrecao_virtual", "_atualizar_memoria_topicos",
    "_usar_modo_rapido_conversa", "interpretar_comando_local_rapido",
    "_detectar_repetir_briefing",
    "_executar_intencao_iot",
    "_registrar_sugestao_indireta",
    "modo_jogo_ativo",
)


class ContextoIntencaoRuntime:
    """Monta o contrato vivo entre o orquestrador e o roteador de intenção."""

    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        estado_getter: Callable[[], Dict[str, Any]],
        monitor_saude: Any = None,
        dependencias_tardias: tuple[str, ...] = (),
    ) -> None:
        self.namespace_getter = namespace_getter
        self.estado_getter = estado_getter
        self.monitor_saude = monitor_saude
        self.dependencias_tardias = frozenset(dependencias_tardias or ())
        namespace = self.namespace_getter() or {}
        self._servicos_estaticos = {
            nome: namespace[nome]
            for nome in DEPENDENCIAS_EXECUCAO_INTENCAO
            if nome not in self.dependencias_tardias and nome in namespace
        }

    def _servicos(self) -> Dict[str, Any]:
        servicos = dict(self._servicos_estaticos)
        if self.dependencias_tardias:
            namespace = self.namespace_getter() or {}
            for nome in self.dependencias_tardias:
                if nome in namespace:
                    servicos[nome] = namespace[nome]
        return servicos

    def validar_conexoes(self) -> Dict[str, Any]:
        servicos = self._servicos()
        if self.monitor_saude is not None:
            return self.monitor_saude.validar_dependencias(
                "execucao_intencao",
                servicos,
                DEPENDENCIAS_EXECUCAO_INTENCAO,
            )
        ausentes = [nome for nome in DEPENDENCIAS_EXECUCAO_INTENCAO if nome not in servicos]
        return {"status": "saudavel" if not ausentes else "degradado", "ausentes": ausentes}

    def montar(self) -> Dict[str, Any]:
        servicos = self._servicos()
        self.validar_conexoes()
        contexto = {
            nome: servicos[nome]
            for nome in DEPENDENCIAS_EXECUCAO_INTENCAO
            if nome in servicos
        }
        estado = self.estado_getter() or {}
        if isinstance(estado, dict):
            contexto.update(estado)
        return contexto


def criar_contexto_intencao_runtime(**kwargs: Any) -> ContextoIntencaoRuntime:
    return ContextoIntencaoRuntime(**kwargs)


def montar_contexto_finalizacao_ia(
    *,
    base: Dict[str, Any] | None = None,
    ia: Dict[str, Any] | None = None,
    voz_memoria: Dict[str, Any] | None = None,
    autoaprimoramento: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Contexto usado para finalizar a resposta apos execucao real."""
    return _merge_grupos(base, ia, voz_memoria, autoaprimoramento)


class ContextoFinalizacaoRuntime:
    """Monta o contrato final com o estado atual da mente compartilhada."""

    def __init__(
        self,
        *,
        ia: Dict[str, Any],
        voz_memoria: Dict[str, Any],
        autoaprimoramento: Dict[str, Any],
        estado_getter: Callable[[], Dict[str, Any]],
    ) -> None:
        self.ia = dict(ia or {})
        self.voz_memoria = dict(voz_memoria or {})
        self.autoaprimoramento = dict(autoaprimoramento or {})
        self.estado_getter = estado_getter

    def montar(self) -> Dict[str, Any]:
        try:
            estado = self.estado_getter() or {}
        except Exception:
            estado = {}
        estado = estado if isinstance(estado, dict) else {}

        base = {
            "messages": estado.get("messages"),
            "current_emotion": estado.get("current_emotion", "calma"),
            "emotion_level": estado.get("emotion_level", 1),
        }
        autoaprimoramento = dict(self.autoaprimoramento)
        autoaprimoramento["_falhas_consecutivas"] = estado.get(
            "_falhas_consecutivas",
            {},
        )
        return montar_contexto_finalizacao_ia(
            base=base,
            ia=self.ia,
            voz_memoria=self.voz_memoria,
            autoaprimoramento=autoaprimoramento,
        )


def criar_contexto_finalizacao_runtime(**kwargs: Any) -> ContextoFinalizacaoRuntime:
    return ContextoFinalizacaoRuntime(**kwargs)
