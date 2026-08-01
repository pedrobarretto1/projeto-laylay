"""Composição dos registros usados na entrada determinística e no chat.

Os runtimes legados ainda recebem um ``namespace_getter``, mas agora ele
enxerga somente um contrato congelado. Estados que mudam durante a execução
continuam chegando por getters explícitos ou por objetos runtime compartilhados.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from mente_laylay.autonomia.comandos_imediatos import criar_comandos_imediatos_runtime
from mente_laylay.autonomia.orquestrador_deterministico import (
    criar_deteccao_deterministica_runtime,
)
from mente_laylay.integracao.contexto_conversa import criar_contexto_inicio_chat_runtime
from mente_laylay.integracao.registro_memoria_pessoas import (
    registrar_memoria_pessoas,
)
from mente_laylay.integracao.registro_iot import registrar_iot
from mente_laylay.integracao.composicao_principal import RegistrosPrincipais


DEPENDENCIAS_DETECCAO = (
    "_extrair_acao_agendada_local", "_normalizar_texto_com_apelidos",
    "_texto_conversa_casual_sem_acao", "_texto_bloqueia_playlist_agora",
    "_texto_social_curto", "_ignorar_token_solto", "_fluxo_prioritario_da_ia",
    "_texto_expresso_melhor_no_deterministico", "_texto_depende_de_contexto",
    "_limpar_destino_pc_b", "_target_from_params", "_limpar_nome_playlist",
    "_musica_estado_get", "_contexto_musical_ativo", "extrair_nome_playlist",
    "_extrair_intencao_abrir_app", "_detectar_playlist_nome_direto",
    "_normalizar_query_musical",
    "_detectar_sugestao_indireta", "_abas_sugeridas_fechar",
    "_modo_jogo_runtime", "_registro_visao_jogo_leitura_runtime",
    "_resolver_consulta_recurso_local",
)

DEPENDENCIAS_COMANDOS_IMEDIATOS = (
    "_normalizar_texto_com_apelidos", "_texto_social_curto",
    "_texto_conversa_casual_sem_acao", "_refinar_contexto_mental",
    "_texto_tem_comando_explicito", "_texto_conversa_contextual_sem_comando",
    "_resolver_comando_janela_contextual_forcado",
    "_resolver_comando_midia_contextual_forcado",
    "_resolver_comando_arquivo_contextual_forcado",
    "_resolver_comando_acao_geral_contextual_forcado",
    "_resolver_comando_contextual_forcado",
    "_responder_contexto_janela_indisponivel", "_resolver_repeticao_ultima_acao",
    "_resolver_consulta_recurso_local", "_texto_parece_consulta_operacional",
    "_extrair_acao_agendada_local", "processar_comandos_em_cadeia",
    "processar_comando_deterministico", "interpretar_comando_local_rapido",
    "resolver_comando_natural", "decisao_comando_ja_avaliada",
    "analisar_intencao", "executar_intencao", "_registrar_resultado_execucao",
    "_registrar_autoaprimoramento", "_falar_falha_contextual",
    "resumir_pagina_ou_video", "falar_com_lipsync",
    "_estado_compartilhado_runtime", "_detectar_comando_governanca_iniciativa",
    "_processar_governanca_iniciativa", "_detectar_pedido_diagnostico_mente",
    "_mostrar_diagnostico_mente", "detectar_comando_saude", "_falar_status_saude",
    "detectar_intencao_deterministica",
    "_responder_pergunta_capacidade_local", "_area_transferencia_runtime",
    "_orquestrador_cooperativo_runtime",
    "_processar_oferta_area_transferencia_pendente",
    "_caixa_entrada_pessoal_runtime", "_central_notificacoes_runtime",
)

DEPENDENCIAS_CONTEXTO_CHAT = (
    "_interpretador_semantico_runtime", "_processar_aprendizado_apelido_imediato",
    "_refinar_contexto_mental", "_registrar_autoaprimoramento",
    "_registrar_mente_curta", "_registrar_interacao_temporal",
    "_registrar_resultado_execucao", "_texto_social_curto",
    "_texto_conversa_casual_sem_acao", "_texto_tem_comando_explicito",
    "_resposta_conversa_rapida_local", "_parece_elogio_ou_agradecimento_curto",
    "_responder_agradecimento_ou_elogio",
    "_resolver_pergunta_curta_contextual_intencao", "_texto_responde_pergunta_aberta",
    "_responder_pergunta_aberta", "_texto_bloqueia_playlist_agora",
    "_texto_pede_direcao_musical_generica",
    "_responder_pedido_direcao_musical_generica",
    "_processar_confirmacao_sugestao_musical", "_texto_pede_opiniao_musica_atual",
    "_responder_opiniao_musica_atual", "_handle_feedback_pendente_misto",
    "_handle_feedback_pendente", "_bloquear_playlist_temporariamente",
    "_registro_musica_operacoes_runtime",
    "processar_comando_deterministico", "_usar_modo_rapido_conversa",
    "interpretar_comando_local_rapido", "_resolver_comando_contextual_forcado",
    "_resolver_reparacao_conversacional", "_responder_contexto_janela_indisponivel",
    "_detectar_sugestao_indireta", "_registrar_sugestao_indireta",
    "_estado_compartilhado_runtime", "executar_intencao", "_emitir_resposta_curta",
    "_executar_intencao_curta_contextual", "falar_com_lipsync", "salvar_memoria",
    "_contexto_horario_atual", "_renovar_sessao_conversa",
    "_continuar_visao_jogo_pendente", "listar_programas_abertos",
    "_salvar_identidade_usuario",
)


def _filtrar(servicos: Mapping[str, Any], nomes: tuple[str, ...]) -> dict[str, Any]:
    return {nome: servicos[nome] for nome in nomes if nome in servicos}


class ComposicaoEntradaInteracaoRuntime:
    """Liga detecção, comandos imediatos e chat sem acesso global contínuo."""

    def __init__(
        self, *, servicos: Mapping[str, Any],
        estado_mental_getter: Callable[[], dict[str, Any]],
        sites_diretos: Mapping[str, Any], apps_map: Mapping[str, Any],
        registros_principais: RegistrosPrincipais | None = None,
        deteccao_factory: Callable[..., Any] = criar_deteccao_deterministica_runtime,
        comandos_factory: Callable[..., Any] = criar_comandos_imediatos_runtime,
        chat_factory: Callable[..., Any] = criar_contexto_inicio_chat_runtime,
    ) -> None:
        self._comandos_factory = comandos_factory
        self._chat_factory = chat_factory
        self._servicos_deteccao = _filtrar(servicos, DEPENDENCIAS_DETECCAO)
        self._servicos_interacao: dict[str, Any] = {}
        self._registros_principais = registros_principais
        self._comandos = None
        self._chat = None
        self.deteccao = deteccao_factory(
            namespace_getter=self._snapshot_deteccao,
            estado_getter=estado_mental_getter,
            sites_diretos=dict(sites_diretos or {}), apps_map=dict(apps_map or {}),
            iot=(registros_principais.iot if registros_principais is not None else (
                registrar_iot(servicos["_registro_iot_runtime"])
                if "_registro_iot_runtime" in servicos else None
            )),
        )

    def _snapshot_deteccao(self) -> dict[str, Any]:
        return dict(self._servicos_deteccao)

    def _snapshot_interacao(self) -> dict[str, Any]:
        return dict(self._servicos_interacao)

    def conectar(
        self, *, servicos: Mapping[str, Any], loop_getter: Callable[[], Any],
        estado_chat_getter: Callable[[], dict[str, Any]], memoria_sqlite: Any,
    ) -> tuple[Any, Any]:
        if self._comandos is not None:
            return self._comandos, self._chat
        if self._registros_principais is not None:
            registro_pessoas = self._registros_principais.memoria_pessoas
            registro_iot = self._registros_principais.iot
        elif "_registro_memoria_pessoas_runtime" not in servicos:
            raise RuntimeError(
                "dependência obrigatória ausente na composição: memória de pessoas"
            )
        else:
            registro_pessoas = registrar_memoria_pessoas(
                servicos["_registro_memoria_pessoas_runtime"]
            )
            if "_registro_iot_runtime" not in servicos:
                raise RuntimeError("dependência obrigatória ausente na composição: IoT")
            registro_iot = registrar_iot(servicos["_registro_iot_runtime"])
        if not callable(servicos.get("resolver_comando_natural")):
            raise RuntimeError(
                "dependência obrigatória ausente na composição: "
                "coordenador canônico de linguagem natural"
            )
        permitidos = set(DEPENDENCIAS_COMANDOS_IMEDIATOS).union(
            DEPENDENCIAS_CONTEXTO_CHAT
        )
        self._servicos_interacao = {
            nome: servicos[nome] for nome in permitidos if nome in servicos
        }
        self._comandos = self._comandos_factory(
            namespace_getter=self._snapshot_interacao, loop_getter=loop_getter,
            memoria_pessoas=registro_pessoas,
            iot=registro_iot,
        )
        self._chat = self._chat_factory(
            namespace_getter=self._snapshot_interacao,
            estado_getter=estado_chat_getter, memoria_sqlite=memoria_sqlite,
        )
        return self._comandos, self._chat

    @property
    def servicos_deteccao_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos_deteccao))

    @property
    def servicos_interacao_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos_interacao))

    @property
    def servicos_tipados_registrados(self) -> tuple[str, ...]:
        if self._comandos is None:
            return ()
        return ("iot", "memoria_pessoas")


def criar_composicao_entrada_interacao_runtime(
    **kwargs: Any,
) -> ComposicaoEntradaInteracaoRuntime:
    return ComposicaoEntradaInteracaoRuntime(**kwargs)
