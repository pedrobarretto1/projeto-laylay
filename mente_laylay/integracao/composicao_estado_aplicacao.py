"""Composição filtrada do estado contextual e dos adaptadores da aplicação."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from mente_laylay.integracao.adaptadores_aplicacao_runtime import (
    criar_adaptadores_aplicacao_runtime,
)
from mente_laylay.integracao.estado_contexto_runtime import criar_estado_contexto_runtime


DEPENDENCIAS_ESTADO_CONTEXTO = (
    "_conversa_estado_get", "_modo_jogo_runtime", "_pesquisa_contextual_runtime",
    "_normalizar_texto_curto", "_normalizar_texto_com_apelidos",
    "_resumo_mente_integrada_para_prompt", "enviar_mensagem", "_extrair_json_da_ia",
    "_fala_de_confirmacao_variada", "_fala_e_fallback_neutro",
    "_ajustar_tom_por_emocao", "_acalmar_emocao_conversacional",
    "_definir_emocao_conversacional", "_contexto_paginas", "_percepcao_get",
    "_texto_tem_comando_explicito", "_texto_expresso_melhor_no_deterministico",
    "_normalizar_texto", "_escolher_fala_variada", "_contexto_horario_atual",
    "_descricao_emocao_mente", "_perfil_comportamento_emocional_mente",
    "_ritmo_circadiano_runtime", "_estado_aprendizado_atual",
    "_estado_compartilhado_runtime", "MEMORIA_SQLITE",
    "_avancar_emocao_conversacional", "_texto_parece_resposta_curta_a_pergunta_mente",
    "_resolver_pergunta_curta_contextual_intencao", "detectar_intencao_deterministica",
    "interpretar_comando_local_rapido", "_resolver_comando_midia_contextual_forcado",
    "_resolver_comando_janela_contextual_forcado", "_responder_conversa_curta_por_tipo",
    "_foco_vivo_atual", "_ajustar_fala_por_horario", "_contexto_recente_indica_email",
    "_percepcao_set", "_normalizar_segmento_fala", "FALLBACK_FALA_NEUTRA",
    "_eh_alvo_site_web", "_atualizar_foco_vivo", "_musica_estado_get",
    "_memoria_conversa_get", "_continuidades_get", "playlist_state",
    "_musica_estado_set", "_continuidades_set", "_continuidades_update",
    "falar_com_lipsync", "_estrutura_arquivo_recente", "_gmail_nao_lidos_cache",
    "BRIEFING_CIDADE", "_observabilidade_mente_runtime",
)

DEPENDENCIAS_ADAPTADORES_APLICACAO = (
    "_registrar_mente_curta_base", "_motor_aprendizado_runtime",
    "_rede_associativa_runtime", "print",
    "_registrar_resultado_execucao_base", "_estado_compartilhado_runtime",
    "_especialista_neural_comandos_runtime",
    "_atualizar_plano_turno_mente", "_concluir_correcao_interpretacao_mente",
    "_resumo_mente_integrada_para_prompt_base", "_continuidades_get",
    "_aprendizado_runtime", "ROTINA_BLOQUEIO_REJEICAO_MIN",
    "ROTINA_BLOQUEIO_REJEICAO_VEZES", "_registrar_mente_curta",
    "salvar_memoria", "MEMORIA_SQLITE", "APPS_MAP", "_playlist_runtime",
    "_saude_mente_runtime", "_chrome_ws_contexto_runtime",
    "_contexto_intencao_runtime", "_ciclo_comandos_runtime",
    "falar_com_lipsync", "enviar_mensagem", "carregar_memoria",
    "_gmail_buscar_nao_lidos", "gmail_daemon",
    "run_ws_server_in_thread", "_registro_navegador_operacoes_runtime",
    "_pendencia_acao_runtime", "_classificar_confirmacao_local",
    "_registro_navegador_leitura_runtime", "_registro_iot_runtime",
    "_area_transferencia_runtime", "_caixa_entrada_pessoal_runtime",
    "_central_notificacoes_runtime", "_avatar_runtime",
    "_registro_visao_jogo_leitura_runtime",
    "_registro_visao_jogo_analise_runtime",
    "_registro_modelo_llm_runtime", "_agenda_runtime",
)


def _filtrar(servicos: Mapping[str, Any], nomes: tuple[str, ...]) -> dict[str, Any]:
    return {nome: servicos[nome] for nome in nomes if nome in servicos}


class ComposicaoEstadoAplicacaoRuntime:
    """Permite montagem precoce e congela os registros na conexão final."""

    def __init__(
        self,
        *,
        servicos_iniciais: Mapping[str, Any],
        estado_runtime_getter: Callable[[], Any],
        registrar_falha: Callable[..., Any] | None = None,
        estado_factory: Callable[..., Any] = criar_estado_contexto_runtime,
        adaptadores_factory: Callable[..., Any] = criar_adaptadores_aplicacao_runtime,
    ) -> None:
        self._servicos_estado = _filtrar(
            servicos_iniciais, DEPENDENCIAS_ESTADO_CONTEXTO,
        )
        self._servicos_adaptadores = _filtrar(
            servicos_iniciais, DEPENDENCIAS_ADAPTADORES_APLICACAO,
        )
        self._conectado = False
        self.estado = estado_factory(
            namespace_getter=self._snapshot_estado,
            estado_runtime_getter=estado_runtime_getter,
            registrar_falha=registrar_falha,
        )
        self.adaptadores = adaptadores_factory(
            namespace_getter=self._snapshot_adaptadores,
        )

    def _snapshot_estado(self) -> dict[str, Any]:
        return dict(self._servicos_estado)

    def _snapshot_adaptadores(self) -> dict[str, Any]:
        return dict(self._servicos_adaptadores)

    def conectar(self, *, servicos: Mapping[str, Any]) -> tuple[Any, Any]:
        if self._conectado:
            return self.estado, self.adaptadores
        self._servicos_estado = _filtrar(servicos, DEPENDENCIAS_ESTADO_CONTEXTO)
        self._servicos_adaptadores = _filtrar(
            servicos, DEPENDENCIAS_ADAPTADORES_APLICACAO,
        )
        self._conectado = True
        return self.estado, self.adaptadores

    @property
    def conectado(self) -> bool:
        return self._conectado

    @property
    def servicos_estado_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos_estado))

    @property
    def servicos_adaptadores_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos_adaptadores))


def criar_composicao_estado_aplicacao_runtime(
    **kwargs: Any,
) -> ComposicaoEstadoAplicacaoRuntime:
    return ComposicaoEstadoAplicacaoRuntime(**kwargs)
