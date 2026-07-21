import io
import json
import re
import sys
import atexit

# Força UTF-8 no terminal Windows para evitar UnicodeEncodeError
try:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (OSError, ValueError):
    pass
import time
import psutil
import requests
import os
import keyboard
from functools import partial
import threading as _threading
import builtins as _builtins
from mente_laylay.autonomia.comandos_sistema import (
    abrir_programa as _abrir_programa_mente,
    fechar_programa as _fechar_programa_mente,
)
from mente_laylay.autonomia.coordenador_intencao import (
    criar_ciclo_comandos_runtime as _criar_ciclo_comandos_runtime_mente,
)
from mente_laylay.cognicao.interpretacao_intencao import (
    criar_adaptadores_conversacionais_runtime as _criar_adaptadores_conversacionais_runtime_mente,
    criar_interpretacao_intencao_runtime as _criar_interpretacao_intencao_runtime_mente,
    extrair_json_resposta as _extrair_json_resposta_mente,
)
from mente_laylay.autonomia.roteador_conteudo import (
    executar_comando_conteudo as _executar_comando_conteudo_mente,
)
from mente_laylay.arquivos.arquivos_sistema import (
    buscar_arquivo_no_pc as _buscar_arquivo_no_pc_mente,
    criar_ou_editar_arquivo as _criar_ou_editar_arquivo_mente,
    criar_pasta as _criar_pasta_mente,
    deletar_item as _deletar_item_mente,
    mapear_pastas_principais as _mapear_pastas_principais_mente,
    mover_arquivo as _mover_arquivo_mente,
    renomear_arquivo as _renomear_arquivo_mente,
    resolver_caminho as _resolver_caminho_mente,
)
from mente_laylay.memoria_mental.contexto_integrado import (
    resumo_mente_integrada_para_prompt as _resumo_mente_integrada_para_prompt_mente,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    estado_mental_inicial as _estado_mental_inicial_mente,
    fluxo_prioritario_da_ia as _fluxo_prioritario_da_ia_mente,
    limpar_pergunta_aberta as _limpar_pergunta_aberta_estado_mente,
    registrar_continuidade_da_fala as _registrar_continuidade_da_fala_mente,
    texto_depende_de_contexto as _texto_depende_de_contexto_mente,
    texto_parece_resposta_curta_a_pergunta as _texto_parece_resposta_curta_a_pergunta_mente,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    criar_contexto_imediato_runtime as _criar_contexto_imediato_runtime_mente,
)
from mente_laylay.memoria_mental.estado_continuidades import (
    estado_continuidades_inicial as _estado_continuidades_inicial_mente,
)
from mente_laylay.memoria_mental.estado_musical import (
    estado_musical_inicial as _estado_musical_inicial_mente,
)
from mente_laylay.memoria_mental.estado_percepcao import (
    estado_percepcao_inicial as _estado_percepcao_inicial_mente,
    registrar_log_navegador as _registrar_log_navegador_mente,
)
from mente_laylay.percepcao.janelas_sistema import (
    capturar_janela_ativa as _capturar_janela_ativa_mente,
    classificar_assunto as _classificar_assunto_mente,
    detectar_gatilho_proativo_sistema as _detectar_gatilho_proativo_sistema_mente,
    fala_gatilho_proativo_sistema as _fala_gatilho_proativo_sistema_mente,
    focar_janela as _focar_janela_mente,
    janela_esta_em_foco as _janela_esta_em_foco_mente,
    janela_em_tela_cheia as _janela_em_tela_cheia_mente,
    listar_programas_abertos as _listar_programas_abertos_mente,
    maximizar_janela as _maximizar_janela_mente,
    normalizar_alvo_ambiente as _normalizar_alvo_ambiente_mente,
    organizar_janelas as _organizar_janelas_mente,
    pid_from_hwnd as _pid_from_hwnd_mente,
    resolver_alvo_ambiente as _resolver_alvo_ambiente_mente,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    criar_estado_compartilhado_runtime as _criar_estado_compartilhado_runtime_mente,
)
from mente_laylay.memoria_mental.saude_mente import (
    criar_saude_mente_runtime as _criar_saude_mente_runtime,
)
from mente_laylay.memoria_mental.consciencia_temporal import (
    registrar_evento_visual_temporal as _registrar_evento_visual_temporal_mente,
)
from mente_laylay.memoria_mental.diagnostico_mente import (
    criar_diagnostico_mente_runtime as _criar_diagnostico_mente_runtime,
    detectar_pedido_diagnostico_mente as _detectar_pedido_diagnostico_mente,
)
from mente_laylay.memoria_mental.observabilidade import (
    criar_observabilidade_mente_runtime as _criar_observabilidade_mente_runtime,
)
from mente_laylay.percepcao.monitor_janelas import (
    criar_monitor_janelas_runtime as _criar_monitor_janelas_runtime_mente,
)
from mente_laylay.cognicao.interpretador_semantico_runtime import (
    criar_interpretador_semantico_runtime as _criar_interpretador_semantico_runtime_mente,
)
from mente_laylay.cognicao.orquestrador_turno_runtime import (
    iniciar_planejamento_turno as _iniciar_planejamento_turno_mente_runtime,
    registrar_leitura_semantica_principal as _registrar_leitura_semantica_principal_mente_runtime,
    atualizar_planejamento_turno as _atualizar_planejamento_turno_mente_runtime,
    verificar_fala_do_turno as _verificar_fala_do_turno_mente_runtime,
)
from mente_laylay.cognicao.decisao_turno import (
    filtrar_comandos_pelo_turno as _filtrar_comandos_pelo_turno_mente,
)
from mente_laylay.percepcao.ritmo_circadiano import (
    criar_ritmo_circadiano_runtime as _criar_ritmo_circadiano_runtime_mente,
)
from mente_laylay.memoria_mental.registro_semantico import (
    atualizar_registro_turno as _atualizar_registro_turno_mente,
)
from mente_laylay.percepcao.modo_jogo import (
    criar_modo_jogo_runtime as _criar_modo_jogo_runtime_mente,
    descarregar_modelo_ollama as _descarregar_modelo_ollama_mente,
)
from mente_laylay.percepcao.ouvido_whisper import (
    criar_ouvido_whisper_runtime as _criar_ouvido_whisper_runtime_mente,
    limpar_diccao_e_ruido as _limpar_diccao_e_ruido_mente,
)
from mente_laylay.percepcao.alvos_web import (
    contexto_aponta_site_web as _contexto_aponta_site_web_mente,
    contexto_navegador_relevante as _contexto_navegador_relevante_mente,
    eh_alvo_site_web as _eh_alvo_site_web_mente,
)
from mente_laylay.percepcao.contexto_paginas import (
    ContextoPaginas,
)
from mente_laylay.percepcao.ambiente_sistema import (
    carregar_estado_briefing as _carregar_estado_briefing_ambiente,
    criar_ambiente_sistema_runtime as _criar_ambiente_sistema_runtime_mente,
    detectar_comando_saude as _detectar_comando_saude_ambiente,
    detectar_repetir_briefing as _detectar_repetir_briefing_ambiente,
    montar_briefing_matinal as _montar_briefing_matinal_ambiente,
    obter_clima_localidade as _obter_clima_localidade_ambiente,
    obter_clima_wttr as _obter_clima_wttr_ambiente,
    salvar_estado_briefing as _salvar_estado_briefing_ambiente,
)
from mente_laylay.memoria_mental.persistencia_memoria import (
    criar_persistencia_memoria_runtime as _criar_persistencia_memoria_runtime_mente,
    init_memoria_contexto_diaria as _init_memoria_contexto_diaria_mente,
)
from mente_laylay.memoria_mental.aprendizado_runtime import (
    criar_aprendizado_runtime as _criar_aprendizado_runtime_mente,
)
from mente_laylay.memoria_mental.motor_aprendizado import (
    criar_motor_aprendizado_runtime as _criar_motor_aprendizado_runtime_mente,
)
from mente_laylay.memoria_mental.resumo_diario import (
    MemoriaLaylay as _MemoriaLaylayRuntime,
)
from mente_laylay.memoria_mental.playlist_mental import (
    detectar_mover_playlist_texto as _detectar_mover_playlist_texto_mente,
    fala_playlist_conteudo_estilosa as _fala_playlist_conteudo_estilosa_mente,
    limpar_nome_playlist as _limpar_nome_playlist_mente,
    yt_clean_title as _yt_clean_title_mente,
    yt_clean_url as _yt_clean_url_mente,
)
from mente_laylay.memoria_mental.busca_youtube import (
    extrair_resultados_youtube_busca as _extrair_resultados_youtube_busca_mente,
    normalizar_query_musical as _normalizar_query_musical_mente,
)
from mente_laylay.memoria_mental.busca_musical_runtime import (
    criar_busca_musical_runtime as _criar_busca_musical_runtime_mente,
)
from mente_laylay.memoria_mental.musica_conversacional_runtime import (
    criar_musica_conversacional_runtime as _criar_musica_conversacional_runtime_mente,
)
from mente_laylay.memoria_mental.playlist_runtime import (
    criar_playlist_runtime as _criar_playlist_runtime_mente,
)
from mente_laylay.memoria_mental.playlist_laylay_runtime import (
    criar_playlist_laylay_runtime as _criar_playlist_laylay_runtime_mente,
)
from mente_laylay.personalidade.falas_variadas import (
    escolher as _escolher_fala_variada,
    fala_de_confirmacao as _fala_de_confirmacao_variada,
)
from mente_laylay.personalidade.terminal_laylay import (
    criar_print_filtrado as _criar_print_filtrado_mente,
    escutar_texto_terminal as _escutar_texto_terminal_mente,
    formatar_mensagem_laylay as _formatar_mensagem_laylay_mente,
    should_log_message as _should_log_message_mente,
    tratar_excecao_thread as _tratar_excecao_thread_mente,
)
from mente_laylay.personalidade.voz_runtime import (
    criar_voz_runtime as _criar_voz_runtime_mente,
)
from mente_laylay.personalidade.avatar_runtime import (
    criar_avatar_runtime as _criar_avatar_runtime_mente,
)
from mente_laylay.personalidade.oralidade import (
    preparar_texto_para_tts as _preparar_texto_para_tts_mente,
)
from mente_laylay.personalidade.orquestrador_fala_runtime import (
    criar_orquestrador_fala_runtime as _criar_orquestrador_fala_runtime_mente,
)
from mente_laylay.personalidade.resposta_conversacional_runtime import (
    criar_resposta_conversacional_runtime as _criar_resposta_conversacional_runtime_mente,
)
from mente_laylay.personalidade.abertura_chat import (
    criar_abertura_chat_runtime as _criar_abertura_chat_runtime_mente,
)
from mente_laylay.personalidade.prompt_base import ALLOWED_ACTIONS, BASE_SYSTEM_PROMPT
from mente_laylay.personalidade.conversa_natural import (
    criar_conversa_natural_runtime as _criar_conversa_natural_runtime_mente,
    fala_e_fallback_neutro as _fala_e_fallback_neutro_mente,
)
from mente_laylay.autonomia.execucao_ia import (
    criar_coordenador_exec_runtime as _criar_coordenador_exec_runtime_mente,
    criar_contexto_exec_runtime as _criar_contexto_exec_runtime_mente,
    executar_exec as _executar_exec_mente,
    filtrar_apenas_fala as _filtrar_apenas_fala_mente,
    parsear_resposta_json as _parsear_resposta_json_mente,
    remover_prefixo_exec as _remover_prefixo_exec_mente,
)
from mente_laylay.autonomia.processamento_resposta_ia import (
    extrair_aprendizados_da_ia as _extrair_aprendizados_da_ia_mente,
    extrair_tipo_interacao_da_ia as _extrair_tipo_interacao_da_ia_mente,
    limpar_resposta_da_ia as _limpar_resposta_da_ia_mente,
    preparar_resposta_para_execucao as _preparar_resposta_para_execucao_mente,
)
from mente_laylay.autonomia.controle_midia import (
    executar_controle_midia_nativo as _executar_controle_midia_nativo_mente,
)
from mente_laylay.autonomia.audio_sistema import (
    ajustar_volume_sistema as _ajustar_volume_sistema_mente,
    ajustar_volume_sistema_relativo as _ajustar_volume_sistema_relativo_mente,
    definir_mudo_sistema as _definir_mudo_sistema_mente,
    ducking_volume as _ducking_volume_mente,
)
from mente_laylay.autonomia.fluxo_resposta_ia import (
    processar_inicio_fluxo_resposta_ia as _processar_inicio_fluxo_resposta_ia_mente,
    processar_pre_fluxos_antes_ia as _processar_pre_fluxos_antes_ia_mente,
)
from mente_laylay.autonomia.modo_chat import (
    criar_interacao_chat_runtime as _criar_interacao_chat_runtime_mente,
    criar_modo_chat_runtime as _criar_modo_chat_runtime_mente,
)
from mente_laylay.autonomia.barra_comando import (
    criar_barra_comando_runtime as _criar_barra_comando_runtime_mente,
)
from mente_laylay.autonomia.servicos_background import (
    criar_gerenciador_servicos_background as _criar_gerenciador_servicos_background_mente,
    criar_orquestrador_inicializacao as _criar_orquestrador_inicializacao_mente,
)
from mente_laylay.autonomia.porteiro_chrome import (
    criar_porteiro_chrome_runtime as _criar_porteiro_chrome_runtime_mente,
)
from mente_laylay.autonomia.contexto_resposta_ia import (
    criar_contexto_prompt_runtime as _criar_contexto_prompt_runtime_mente,
)
from mente_laylay.integracao.contexto_conversa import (
    criar_contexto_inicio_chat_runtime as _criar_contexto_inicio_chat_runtime_mente,
)
from mente_laylay.integracao.estado_contexto_runtime import (
    criar_estado_contexto_runtime as _criar_estado_contexto_runtime_mente,
)
from mente_laylay.autonomia.motor_temporal import (
    criar_motor_temporal_runtime as _criar_motor_temporal_runtime_mente,
)
from mente_laylay.integracao.adaptadores_aplicacao_runtime import (
    criar_adaptadores_aplicacao_runtime as _criar_adaptadores_aplicacao_runtime_mente,
)
from mente_laylay.integracao.contexto_execucao_ia import (
    criar_contexto_dispatcher_runtime as _criar_contexto_dispatcher_runtime_mente,
    criar_contexto_finalizacao_runtime as _criar_contexto_finalizacao_runtime_mente,
    criar_contexto_intencao_runtime as _criar_contexto_intencao_runtime_mente,
)
from mente_laylay.integracao.llm_http import (
    criar_llm_http_runtime as _criar_llm_http_runtime_mente,
)
from mente_laylay.integracao.cliente_llm_runtime import (
    criar_cliente_llm_runtime as _criar_cliente_llm_runtime_mente,
)
from mente_laylay.iot.resolucao_cores import resolver_cor_por_ia as _resolver_cor_por_ia_mente
from mente_laylay.integracao.chrome_comandos import (
    criar_chrome_comandos_runtime as _criar_chrome_comandos_runtime_mente,
)
from mente_laylay.integracao.pc_b_integracao import (
    criar_destino_pc_runtime as _criar_destino_pc_runtime_mente,
    criar_pc_b_runtime as _criar_pc_b_runtime_mente,
)
from mente_laylay.integracao.chrome_ws_transport import (
    ChromeSolicitacoesRuntime as _ChromeSolicitacoesRuntime,
    broadcast_command as _broadcast_command_chrome_mente,
)
from mente_laylay.integracao.chrome_navegacao import (
    abrir_url_reutilizando_aba as _abrir_url_reutilizando_aba_chrome_mente,
    classificar_contexto_por_url as _classificar_contexto_por_url_chrome_mente,
    fechar_aba_ativa_nativa as _fechar_aba_ativa_nativa_chrome_mente,
    fechar_abas_vazias as _fechar_abas_vazias_chrome_mente,
    formatar_url_ou_busca as _formatar_url_ou_busca_chrome_mente,
    is_valid_url as _is_valid_url_chrome_mente,
)
from mente_laylay.integracao.chrome_estado import (
    ChromeEstadoRuntime as _ChromeEstadoRuntime,
)
from mente_laylay.integracao.chrome_ws_server import (
    criar_chrome_ws_runtime as _criar_chrome_ws_runtime_mente,
    criar_websocket_transport_runtime as _criar_websocket_transport_runtime_mente,
    fechar_extensoes_anteriores as _fechar_extensoes_anteriores_chrome_mente,
    run_ws_server_in_thread as _run_ws_server_in_thread_chrome_mente,
)
from mente_laylay.integracao.chrome_ws_handlers import (
    criar_chrome_ws_eventos_runtime as _criar_chrome_ws_eventos_runtime_mente,
)
from mente_laylay.integracao.chrome_ws_contexto import (
    criar_chrome_ws_contexto_runtime as _criar_chrome_ws_contexto_runtime_mente,
)
from mente_laylay.integracao.ambiente_navegacao import (
    criar_ambiente_navegacao_runtime as _criar_ambiente_navegacao_runtime_mente,
)
from mente_laylay.autonomia.finalizacao_execucao_ia import (
    finalizar_execucao_resposta_ia as _finalizar_execucao_resposta_ia_mente,
)
from mente_laylay.autonomia.resposta_ia_runtime import (
    criar_resposta_ia_runtime as _criar_resposta_ia_runtime_mente,
)
from mente_laylay.autonomia.feedback_pendente_runtime import (
    criar_feedback_pendente_runtime as _criar_feedback_pendente_runtime_mente,
)
from mente_laylay.cognicao.interpretador_continuidade import (
    interpretar_resposta_pendente as _interpretar_resposta_pendente_mente,
)
from mente_laylay.cognicao.pesquisa_contextual import (
    criar_pesquisa_contextual_runtime as _criar_pesquisa_contextual_runtime_mente,
)
from mente_laylay.cognicao.fundamentacao_factual import (
    extrair_tema_fundamentacao as _extrair_tema_fundamentacao_mente,
    montar_fundamentacao as _montar_fundamentacao_mente,
)
from mente_laylay.cognicao.resumo_conteudo import (
    criar_resumo_conteudo_runtime as _criar_resumo_conteudo_runtime_mente,
)
from mente_laylay.cognicao.selecao_abas import (
    criar_selecao_abas_runtime as _criar_selecao_abas_runtime_mente,
)
from mente_laylay.cognicao.confirmacao_llm import (
    criar_confirmacao_llm_runtime as _criar_confirmacao_llm_runtime_mente,
)
from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto as _normalizar_texto_mente,
    normalizar_texto_curto as _normalizar_texto_curto_mente,
)
from mente_laylay.cognicao.linguagem_aprendida import (
    criar_linguagem_aprendida_runtime as _criar_linguagem_aprendida_runtime_mente,
)
from mente_laylay.autonomia.dispatcher_comandos_json import (
    executar_comandos_json as _executar_comandos_json_mente,
)
from mente_laylay.autonomia.fluxos_conversa import (
    handle_feedback_pendente as _handle_feedback_pendente_mente,
)
from mente_laylay.autonomia.comandos_imediatos import (
    criar_comandos_imediatos_runtime as _criar_comandos_imediatos_runtime_mente,
)
from mente_laylay.autonomia.sugestoes_sistema import (
    aplicar_preferencia_sugestao as _aplicar_preferencia_sugestao_mente,
    chave_preferencia_sugestao as _chave_preferencia_sugestao_mente,
    criar_sugestoes_sistema_runtime as _criar_sugestoes_sistema_runtime_mente,
)
from mente_laylay.autonomia.preferencias_sugestoes_runtime import (
    criar_preferencias_sugestoes_runtime as _criar_preferencias_sugestoes_runtime_mente,
)
from mente_laylay.autonomia.porteiro_proatividade import (
    criar_porteiro_proatividade_runtime as _criar_porteiro_proatividade_runtime_mente,
)
from mente_laylay.autonomia.analise_comandos import (
    limpar_resposta as _limpar_resposta_mente,
)
from mente_laylay.autonomia.agendamento_mental import (
    criar_agenda_runtime as _criar_agenda_runtime_mente,
    extrair_acao_agendada_local as _extrair_acao_agendada_local_mente,
    extrair_agendamento_local as _extrair_agendamento_local_mente,
    resumo_agendamentos_para_prompt as _resumo_agendamentos_para_prompt_mente,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    criar_deteccao_deterministica_runtime as _criar_deteccao_deterministica_runtime_mente,
)
from mente_laylay.autonomia.porteiro_acoes import (
    criar_porteiro_acoes_runtime as _criar_porteiro_acoes_runtime_mente,
    texto_bloqueia_playlist_agora as _texto_bloqueia_playlist_agora_mente,
    texto_tem_comando_explicito as _texto_tem_comando_explicito_mente,
    texto_pede_playlist_explicitamente as _texto_pede_playlist_explicitamente_mente,
    texto_social_curto as _texto_social_curto_mente,
)
from mente_laylay.emocoes.perfil_emocional import (
    ajustar_tom_por_emocao as _ajustar_tom_por_emocao_mente,
    descricao_emocao as _descricao_emocao_mente,
    limpar_para_voz as _limpar_para_voz_mente,
    modular_audio_params as _modular_audio_params_mente,
    perfil_comportamento_emocional as _perfil_comportamento_emocional_mente,
)
# from youtubesearchpython import VideosSearch (Removido por erro de proxies no ambiente)

LOG_MODE = str(os.getenv("LAYLAY_LOG_MODE", "limpo")).lower()
LOG_VERBOSE = str(os.getenv("LAYLAY_LOG_VERBOSE", "0")).lower() in {"1", "true", "yes", "on"}
_PRINT_LOCK = _threading.RLock()
_RAW_PRINT = _builtins.print

FALLBACK_FALA_NEUTRA = "Não consegui encaixar isso direito. Me fala de outro jeito?"


_formatar_mensagem_laylay = partial(
    _formatar_mensagem_laylay_mente,
    fallback_fala=FALLBACK_FALA_NEUTRA,
    stdout=sys.stdout,
)
from mente_laylay.iot.runtime import criar_runtime_iot as _criar_runtime_iot_mente


_should_log_message = partial(
    _should_log_message_mente,
    log_mode=LOG_MODE,
    log_verbose=LOG_VERBOSE,
)


_print_filtrado = _criar_print_filtrado_mente(
    should_log=_should_log_message,
    raw_print=_RAW_PRINT,
    print_lock=_PRINT_LOCK,
)


# noinspection PyShadowingBuiltins
print = _print_filtrado
_builtins.print = _print_filtrado

print("\n╔══════════════════════════════════════╗")
print("║  ◕‿◕ Laylay inicializando — modo essencial ║")
print("╚══════════════════════════════════════╝")
import traceback
import asyncio

from memoria_sqlite import MemoriaSQLite
from mente_laylay.integracao.gmail_mental import (
    DEFAULT_GMAIL_PALAVRAS_URGENTES,
    DEFAULT_GMAIL_PRIORITARIOS,
    criar_gmail_runtime,
)

_resposta_conversacional_runtime = _criar_resposta_conversacional_runtime_mente(
    namespace_getter=lambda: globals(),
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
    fallback_fala=FALLBACK_FALA_NEUTRA,
    log=print,
)
_limpar_texto_fala_ia = _resposta_conversacional_runtime.limpar_texto_fala_ia
_atualizar_memoria_topicos = _resposta_conversacional_runtime.atualizar_memoria_topicos
_acalmar_emocao_conversacional = _resposta_conversacional_runtime.acalmar_emocao
_definir_emocao_conversacional = _resposta_conversacional_runtime.definir_emocao
_avancar_emocao_conversacional = _resposta_conversacional_runtime.avancar_emocao
_emitir_resposta_curta = _resposta_conversacional_runtime.emitir_resposta_curta
_falar_falha_contextual = _resposta_conversacional_runtime.falar_falha_contextual
_executar_intencao_curta_contextual = _resposta_conversacional_runtime.executar_intencao_curta

limpar_resposta_da_ia = partial(
    _limpar_resposta_da_ia_mente,
    limpar_texto_fala_cb=_limpar_texto_fala_ia,
    fallback_fala=FALLBACK_FALA_NEUTRA,
)

extrair_aprendizados_da_ia = _extrair_aprendizados_da_ia_mente
extrair_tipo_interacao_da_ia = _extrair_tipo_interacao_da_ia_mente


_normalizar_texto_curto = _normalizar_texto_curto_mente


_contexto_navegador_relevante = partial(
    _contexto_navegador_relevante_mente,
    normalizar_texto=_normalizar_texto_curto,
)


_fala_e_fallback_neutro = partial(
    _fala_e_fallback_neutro_mente,
    normalizar_texto_curto=_normalizar_texto_curto,
)


_texto_social_curto = _texto_social_curto_mente


_texto_tem_comando_explicito = _texto_tem_comando_explicito_mente


_texto_bloqueia_playlist_agora = _texto_bloqueia_playlist_agora_mente


_texto_pede_playlist_explicitamente = _texto_pede_playlist_explicitamente_mente


_porteiro_acoes_runtime = _criar_porteiro_acoes_runtime_mente(
    namespace_getter=lambda: globals(),
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
)
_texto_cancela_acao_agora = _porteiro_acoes_runtime.texto_cancela_acao_agora
_bloquear_playlist_temporariamente = _porteiro_acoes_runtime.bloquear_playlist_temporariamente
_playlist_bloqueada_agora = _porteiro_acoes_runtime.playlist_bloqueada_agora
_contexto_porteiro_acoes = _porteiro_acoes_runtime.contexto
_autonomia_permite_execucao_musical = _porteiro_acoes_runtime.autonomia_permite_execucao_musical
_autorizar_acao_pratica = _porteiro_acoes_runtime.autorizar_acao_pratica


_estado_contexto_runtime = _criar_estado_contexto_runtime_mente(
    namespace_getter=lambda: globals(),
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
)
_contexto_conversa_natural = _estado_contexto_runtime.contexto_conversa_natural
_obter_contexto_perceptivo = _estado_contexto_runtime.contexto_perceptivo
_registrar_mente_curta_base = _estado_contexto_runtime.registrar_mente_curta
_adaptadores_aplicacao_runtime = _criar_adaptadores_aplicacao_runtime_mente(
    namespace_getter=lambda: globals(),
)
_registrar_mente_curta = _adaptadores_aplicacao_runtime.registrar_mente_curta
_registrar_interacao_temporal = _estado_contexto_runtime.registrar_interacao_temporal
_registrar_resultado_execucao_base = _estado_contexto_runtime.registrar_resultado_execucao
_registrar_resultado_execucao = _adaptadores_aplicacao_runtime.registrar_resultado_execucao
_estado_contexto_intencao = _estado_contexto_runtime.estado_contexto_intencao
_atualizar_contexto_sistema_monitor = _estado_contexto_runtime.atualizar_contexto_sistema_monitor
_definir_ultimo_proativo_ts = _estado_contexto_runtime.definir_ultimo_proativo_ts
_compor_fala_proativa = _estado_contexto_runtime.compor_fala_proativa
_ajustar_estado_voz = _estado_contexto_runtime.ajustar_estado_voz
_contexto_gate_conversa = _estado_contexto_runtime.contexto_gate_conversa
_texto_conversa_contextual_sem_comando = _estado_contexto_runtime.texto_conversa_contextual_sem_comando
_texto_conversa_casual_sem_acao = _estado_contexto_runtime.texto_conversa_casual_sem_acao
_texto_parece_navegacao_ou_janela_ia = _estado_contexto_runtime.texto_parece_navegacao_ou_janela_ia
_texto_indica_autocorrecao = _estado_contexto_runtime.texto_indica_autocorrecao
_ajustar_fala_por_horario = _estado_contexto_runtime.ajustar_fala_por_horario
_renovar_sessao_conversa = _estado_contexto_runtime.renovar_sessao_conversa


_conversa_natural_runtime = _criar_conversa_natural_runtime_mente(_contexto_conversa_natural)


_pergunta_aberta_atual = _estado_contexto_runtime.pergunta_aberta_atual
_limpar_pergunta_aberta = _estado_contexto_runtime.limpar_pergunta_aberta
_registrar_alvo_corrigido = _estado_contexto_runtime.registrar_alvo_corrigido
_alvo_corrigido_atual = _estado_contexto_runtime.alvo_corrigido_atual
_registrar_estrutura_arquivo_recente = _estado_contexto_runtime.registrar_estrutura_arquivo_recente
_estrutura_arquivo_recente = _estado_contexto_runtime.estrutura_arquivo_recente
_texto_responde_pergunta_aberta = _estado_contexto_runtime.texto_responde_pergunta_aberta
_responder_pergunta_aberta = _estado_contexto_runtime.responder_pergunta_aberta


_contexto_recente_indica_email = _conversa_natural_runtime.contexto_recente_indica_email


_resolver_pergunta_curta_contextual_intencao = (
    _estado_contexto_runtime.resolver_pergunta_curta_contextual_intencao
)


_responder_agradecimento_ou_elogio = _conversa_natural_runtime.responder_agradecimento_ou_elogio
_responder_conversa_curta_por_tipo = _conversa_natural_runtime.responder_conversa_curta_por_tipo


_construir_fala_conversa = _conversa_natural_runtime.construir_fala
_resposta_conversa_local = _conversa_natural_runtime.resposta_local
_parece_elogio_ou_agradecimento_curto = _conversa_natural_runtime.parece_elogio_ou_agradecimento_curto
_resposta_conversa_rapida_local = _conversa_natural_runtime.resposta_rapida_local


_contexto_horario_atual = _estado_contexto_runtime.contexto_horario_atual
_interpretar_contexto_vivo = _estado_contexto_runtime.interpretar_contexto_vivo
_resumo_mente_integrada_para_prompt_base = _estado_contexto_runtime.resumo_mente_integrada_para_prompt
_resumo_mente_integrada_para_prompt = (
    _adaptadores_aplicacao_runtime.resumo_mente_integrada_para_prompt
)

_atualizar_foco_vivo = _estado_contexto_runtime.atualizar_foco_vivo
_foco_vivo_atual = _estado_contexto_runtime.foco_vivo_atual
_foco_conversacional_atual = _estado_contexto_runtime.foco_conversacional_atual
_foco_operacional_atual = _estado_contexto_runtime.foco_operacional_atual
_resolver_repeticao_ultima_acao = _estado_contexto_runtime.resolver_repeticao_ultima_acao

_registrar_autoaprimoramento = _estado_contexto_runtime.registrar_autoaprimoramento
_resumo_autoaprimoramento_para_prompt = _estado_contexto_runtime.resumo_autoaprimoramento_para_prompt
_refinar_contexto_mental = _estado_contexto_runtime.refinar_contexto_mental
_contexto_aponta_descanso = _estado_contexto_runtime.contexto_aponta_descanso

import pyttsx3
import sounddevice as sd
import soundfile as sf
import ctypes
import webbrowser
import edge_tts
import threading    
from ctypes import wintypes
import pyautogui
import pygetwindow as gw

from youtube_transcript_api import YouTubeTranscriptApi

# Configurações do PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

try:
    from AppOpener import open as open_app
    APP_OPENER_AVAILABLE = True
    print("✅ AppOpener carregado — abertura rápida de programas ativada!")
except ImportError:
    APP_OPENER_AVAILABLE = False
    print("⚠️ AppOpener não encontrado. Instale com: pip install AppOpener")

_ws_transport_runtime = _criar_websocket_transport_runtime_mente()

# ====================== VARIÁVEIS GLOBAIS ======================
interrupt_event = threading.Event()
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
_estado_compartilhado_runtime = _criar_estado_compartilhado_runtime_mente(
    continuidades=_estado_continuidades_inicial_mente(),
    musical=_estado_musical_inicial_mente(),
    percepcao=_estado_percepcao_inicial_mente(),
    mental=_estado_mental_inicial_mente(),
    conversacional={
        "current_emotion": "calma",
        "is_speaking": False,
        "audio_playing": False,
        "emotion_level": 1,
        "humor_level": 0,
        "humor_last_update": 0.0,
        "humor_history": [],
        "emotion_cause": "estado inicial",
        "emotion_started_at": 0.0,
        "emotion_duration_s": 0.0,
        "emotion_interactions_total": 0,
        "emotion_interactions_left": 0,
        "emotion_last_decay_at": 0.0,
        "emotion_last_input_key": "",
        "emotion_last_input_at": 0.0,
        "topicos_conversa_recente": [],
        "ultimo_topico_conversa": "",
        "ultimo_topico_ts": 0.0,
    },
    memoria_conversa={
        "messages": [],
        "bordoes": [],
        "resumo_conversa": "",
        "memoria_fatos": [],
        "memoria_eventos": [],
        "historico_long_term": "",
    },
)
_saude_mente_runtime = _criar_saude_mente_runtime()
_observabilidade_mente_runtime = _criar_observabilidade_mente_runtime(
    estado_getter=lambda chave, padrao=None: _estado_compartilhado_runtime.obter_copia(
        "mental", chave, padrao,
    ),
    estado_setter=lambda **campos: _estado_compartilhado_runtime.atualizar_campos(
        "mental", **campos,
    ),
)
_validacao_mente_inicial = _estado_compartilhado_runtime.validar_estrutura()
if not _validacao_mente_inicial.get("ok"):
    print(
        "⚠️ [MENTE:CONEXOES] estrutura incompleta | "
        f"ausentes={_validacao_mente_inicial.get('ausentes') or []} | "
        f"invalidos={_validacao_mente_inicial.get('invalidos') or []}"
    )
else:
    print("🧠 [MENTE:CONEXOES] dominios compartilhados conectados")
_continuidades_get = _estado_compartilhado_runtime.continuidades_get
_continuidades_set = _estado_compartilhado_runtime.continuidades_set
_continuidades_update = _estado_compartilhado_runtime.continuidades_update
_musica_estado_get = _estado_compartilhado_runtime.musica_get
_musica_estado_set = _estado_compartilhado_runtime.musica_set
_percepcao_get = _estado_compartilhado_runtime.percepcao_get
_percepcao_set = _estado_compartilhado_runtime.percepcao_set
_conversa_estado_get = _estado_compartilhado_runtime.conversa_get
_memoria_conversa_get = _estado_compartilhado_runtime.memoria_conversa_get
sugestao_bloqueada_ate = _estado_compartilhado_runtime.vincular_dict(
    "continuidades", "sugestoes_bloqueadas_ate",
)
_contexto_paginas = ContextoPaginas()
_estado_compartilhado_runtime.atualizar_campos(
    "mental",
    autoaprimoramento_estado={
        "habilidades": {},
        "eventos": [],
        "ultimo_resumo": "",
        "cookie_reforco": 0,
    },
)
_estado_compartilhado_runtime.atualizar_campos("conversacional", is_speaking=False)
_base_dir = os.path.abspath(os.path.dirname(__file__)) if "__file__" in globals() else os.getcwd()
PASTA_MEMORIA = os.path.join(_base_dir, "memoria")
_avatar_runtime = _criar_avatar_runtime_mente(
    raiz_projeto=_base_dir,
    estado_getter=lambda: {
        "emotion": _conversa_estado_get("current_emotion", "calma"),
        "level": _conversa_estado_get("emotion_level", 1),
        "speaking": bool(_conversa_estado_get("audio_playing", False)),
    },
    log=print,
)
atexit.register(_avatar_runtime.parar)
# Agora as constantes que dependem de PASTA_MEMORIA
PLAYLISTS_ARQUIVO = "playlists.json"
PASTA_PLAYLISTS_LAYLAY = os.path.join(PASTA_MEMORIA, "playlists_laylay")
PLAYLISTS_LAYLAY_ARQUIVO = os.path.join(PASTA_PLAYLISTS_LAYLAY, "playlists_da_laylay.json")
AGENDAMENTOS_ARQUIVO = os.path.join(PASTA_MEMORIA, "agendamentos.json")

BRIEFING_ARQUIVO = os.path.join(PASTA_MEMORIA, "briefing_estado.json")
GMAIL_ARQUIVO = os.path.join(PASTA_MEMORIA, "gmail_estado.json")
ROTINA_ARQUIVO_APRENDIDO = os.path.join(PASTA_MEMORIA, "rotinas_aprendidas.json")
MUSICA_ARQUIVO_HISTORICO = os.path.join(PASTA_MEMORIA, "aprendizado_musical.json")
MUSICA_ARQUIVO_FEEDBACK = os.path.join(PASTA_MEMORIA, "musicas_feedback.json")

# ====================== BRIEFING MATINAL ======================
BRIEFING_CIDADE = "Boituva"                    # ← sua cidade (muda se viajar)
_ambiente_sistema_runtime = _criar_ambiente_sistema_runtime_mente()

# ====================== GMAIL VIA IMAP (App Password) ======================
# Configure fora do codigo:
#   setx GMAIL_USER "seu_email@gmail.com"
#   setx GMAIL_APP_PASSWORD "senha_de_app_nova"
GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_INTERVALO_S = int(os.getenv("GMAIL_INTERVALO_S", "300") or "300")
GMAIL_MAX_LIDOS = int(os.getenv("GMAIL_MAX_LIDOS", "5") or "5")
GMAIL_PRIORITARIOS = DEFAULT_GMAIL_PRIORITARIOS
GMAIL_PALAVRAS_URGENTES = DEFAULT_GMAIL_PALAVRAS_URGENTES

_pesquisa_contextual_runtime = _criar_pesquisa_contextual_runtime_mente(
    normalizar_texto_curto=_normalizar_texto_curto,
    requests_get=requests.get,
)

# ====================== MONITOR DE SAÚDE DO PC ======================
SAUDE_CPU_THRESHOLD = 85          # % CPU sustentada
SAUDE_RAM_THRESHOLD = 90          # % RAM
SAUDE_CPU_SUSTENTADO_SEGUNDOS = 30

# ====================== APRENDIZADO DE ROTINA ======================
ROTINA_DIAS_PARA_APRENDER = 7
# ====================== FEEDBACK DE ROTINA (Aprendizado por Resposta) ======================
# Pesos de feedback por app/hora: positivo = Pedro aceitou, negativo = rejeitou
# Formato: {"hora:app": int}  (ex: {"09:00:vscode": 3, "09:00:chrome": -2})
ROTINA_BLOQUEIO_REJEICAO_MIN = 60    # minutos de bloqueio apos "nao"
ROTINA_BLOQUEIO_REJEICAO_VEZES = 3   # apos 3 rejeicoes, nunca mais sugere aquele app/hora

# ====================== APRENDIZADO MUSICAL ======================
playlists_laylay_carregadas = {}
_contexto_dispatcher_runtime = None
_contexto_finalizacao_runtime = None
_contexto_prompt_runtime = None
_contexto_exec_runtime = None
_servicos_background_runtime = _criar_gerenciador_servicos_background_mente(
    log=print,
    reiniciar_apos_falha=True,
    atraso_reinicio_s=5.0,
)
_inicializacao_runtime = _criar_orquestrador_inicializacao_mente(
    servicos=_servicos_background_runtime,
    log=print,
    sleep=time.sleep,
)

# Fila para troca autonoma de musicas no YouTube
_musica_ultima_verificada = ""
_busca_musical_runtime = _criar_busca_musical_runtime_mente(
    extrair_resultados_youtube=lambda html, query, limite=10: _extrair_resultados_youtube_busca(html, query, limite),
    abrir_url=lambda url: validar_e_enviar_comando("open_url", {"url": url}),
    youtube_play=lambda url: validar_e_enviar_comando("youtube_play", {"url": url}),
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    enviar_mensagem=lambda mensagens, **kwargs: enviar_mensagem(mensagens, **kwargs),
    log=print,
)
try:
    os.makedirs(PASTA_MEMORIA, exist_ok=True)
    
    # Migração de Arquivos Antigos
    _migrables = ["laylay_memoria.json", "memoria_contexto.json"]
    import glob, shutil
    for _mtxt in glob.glob(os.path.join(_base_dir, "memoria_*.txt")):
        _migrables.append(os.path.basename(_mtxt))
    for _mfile in _migrables:
        _src = os.path.join(_base_dir, _mfile)
        _dst = os.path.join(PASTA_MEMORIA, _mfile)
        if os.path.exists(_src) and not os.path.exists(_dst):
            shutil.move(_src, _dst)
            print(f"📂 Arquivo migrado p/ memoria/: {_mfile}")
except OSError as e:
    print(f"⚠️ Aviso: Nao foi possivel criar ou migrar docs na pasta de memoria: {e}")

playlists_state_file = os.path.join(_base_dir, PLAYLISTS_ARQUIVO)
playlists_legacy_file = os.path.join(os.path.expanduser("~"), "playlists_laylay.json")
playlist_state = _estado_compartilhado_runtime.vincular_dict(
    "musical",
    "playlist_state",
    {"name": "", "index": 0, "user_intervened": False, "last_url": ""},
)
_playlist_runtime = _criar_playlist_runtime_mente(
    state_file=playlists_state_file,
    legacy_file=playlists_legacy_file,
    cache={},
    ultima_playlist_getter=lambda: str(_musica_estado_get("ultima_playlist") or ""),
    ultima_playlist_setter=lambda valor: _musica_estado_set("ultima_playlist", valor),
    playlist_state=playlist_state,
    youtube_play=lambda url, target_tab_id=None: validar_e_enviar_comando(
        "youtube_play",
        {"url": url, **({"target_tab_id": target_tab_id} if isinstance(target_tab_id, int) else {})},
    ),
    solicitar_aba_ativa=lambda **kwargs: solicitar_aba_ativa(**kwargs),
    normalizar_texto=lambda texto: _normalizar_texto(texto),
    normalizar_texto_com_apelidos=lambda texto: _normalizar_texto_com_apelidos(texto),
    sincronizar_playlists_laylay=lambda: _playlist_laylay_runtime.sincronizar(),
    log=print,
)
_playlist_laylay_runtime = _criar_playlist_laylay_runtime_mente(
    state_file=PLAYLISTS_LAYLAY_ARQUIVO,
    cache=playlists_laylay_carregadas,
    playlists_usuario_getter=lambda: _playlist_runtime.load(),
    historico_musical_getter=lambda: _estado_aprendizado_atual().get("musica_dados_diarios", {}),
    adicionar_playlist_usuario=lambda nome, url, titulo, canal: _playlist_runtime.add_url(
        nome,
        url,
        titulo,
        canal,
    ),
)
HOTKEY_MODO_CHAT_LIGA = "ctrl+shift+z"
HOTKEY_MODO_CHAT_DESLIGA = "ctrl+f9"
HOTKEY_BARRA_COMANDO = "ctrl+shift+space"
_modo_chat_runtime = None
_interpretacao_intencao_runtime = None
# Contador de falhas consecutivas por AçÃO+ALVO — anti-loop de desculpas
# Chave: "acao|alvo" | Valor: contagem de falhas seguidas
_falhas_consecutivas = _estado_compartilhado_runtime.vincular_dict(
    "mental", "falhas_consecutivas_execucao",
)
MAX_TENTATIVAS_AUTOCORRECAO = 3   # ← muda aqui se quiser mais ou menos paciencia
EVENTO_PAGINA = asyncio.Event()

# ====================== PORTEIRO DO CHROME (rastreamento de abas) ======================
_abas_sugeridas_fechar = _estado_compartilhado_runtime.vincular_lista(
    "percepcao", "abas_sugeridas_fechar",
)
RAM_THRESHOLD_PORTEIRO = 80   # % de RAM para disparar curadoria
ABA_IDLE_MINUTOS = 45         # minutos sem visitar para considerar "abandonada"
PORTEIRO_INTERVALO_MIN = 12   # checa a cada 12 minutos

# ====================== CONTEXTO ATUAL DO CHROME (para o novo prompt) ======================
aba_ativa_estado = _percepcao_get("aba_ativa", {"titulo": "Nenhuma aba aberta", "url": "Nenhuma URL"})
_chrome_estado = _ChromeEstadoRuntime(
    titulo_inicial=str(aba_ativa_estado.get("titulo") or "Nenhuma aba aberta"),
    url_inicial=str(aba_ativa_estado.get("url") or "Nenhuma URL"),
    aba_ativa_getter=lambda: _estado_compartilhado_runtime.obter_copia(
        "percepcao",
        "aba_ativa",
        {"titulo": "Nenhuma aba aberta", "url": "Nenhuma URL"},
    ),
    aba_ativa_setter=lambda aba: _percepcao_set("aba_ativa", aba),
)

# ====================== MEMÓRIA INTELIGENTE (Curto → Longo Prazo) ======================
memoria_inteligente = _MemoriaLaylayRuntime(
    pasta_memoria=PASTA_MEMORIA,
    enviar_mensagem=lambda mensagens: enviar_mensagem(mensagens, _com_tools=False),
    log=print,
)

# ====================== CONFIGURAÇÕES GLOBAIS ======================
API_KEY = "ollama"
MODEL = "Qwen2.5"
OPENROUTER_BASE_URL = "http://localhost:11434/v1"
MEMORIA_CONTEXTO_ARQUIVO = os.path.join(PASTA_MEMORIA, "memoria_contexto.json")
MEMORIA_SQLITE = MemoriaSQLite(os.path.join(PASTA_MEMORIA, "laylay_memoria.sqlite"))
OPENROUTER_HTTP_REFERER = os.environ.get("OPENROUTER_HTTP_REFERER", "http://localhost")
OPENROUTER_APP_TITLE = os.environ.get("OPENROUTER_APP_TITLE", "Laylay")
LLM_LOCAL_TIMEOUT = int(os.environ.get("LAYLAY_LLM_LOCAL_TIMEOUT", "120"))
LLM_REMOTE_TIMEOUT = int(os.environ.get("LAYLAY_LLM_REMOTE_TIMEOUT", "30"))
_llm_http_runtime = _criar_llm_http_runtime_mente(
        base_url=OPENROUTER_BASE_URL,
        local_timeout=LLM_LOCAL_TIMEOUT,
        remote_timeout=LLM_REMOTE_TIMEOUT,
        requests_post=requests.post,
        print_fn=print,
        ao_finalizar_conversa_modo_jogo=lambda: _descarregar_modelo_ollama_mente(MODEL),
)
_llm_endpoint_eh_local = _llm_http_runtime.endpoint_eh_local
_post_chat_llm = _llm_http_runtime.post

# ====================== GROQ VISION (substitui Gemini) ======================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Modelo atual recomendado (2026) - Llama 4 Scout (melhor que o 3.2)
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
# Alternativa mais leve (se quiser economizar): "llama-3.2-11b-vision-preview"
SITES_DIRECTOS = {
    "youtube": "https://www.youtube.com",
    "spotify": "https://open.spotify.com",
    "wikipedia": "https://pt.wikipedia.org",
    "wikipédia": "https://pt.wikipedia.org",
    "google": "https://www.google.com",
    "twitch": "https://www.twitch.tv",
    "insta": "https://www.instagram.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "github": "https://github.com",
    "ifood": "https://www.ifood.com.br",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chat.openai.com",
    "gemini": "https://gemini.google.com",
    "claude": "https://claude.ai",
    "canva": "https://www.canva.com",
    "linkedin": "https://www.linkedin.com",
    "facebook": "https://www.facebook.com",
    "amazon": "https://www.amazon.com.br",
    "mercadolivre": "https://www.mercadolivre.com.br",
}
APPS_MAP = {
    "vscode": "code",
    "vs code": "code",
    "visual studio": "code",
    "visual studio code": "code",
    "mine": "minecraft",
    "minecraft": "minecraft",
    "discord": "discord",
    "spotify": "spotify",
    "chrome": "chrome",
    "firefox": "firefox",
    "edge": "msedge",
    "notepad": "notepad",
    "calculadora": "calc",
    "paint": "mspaint",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "steam": "steam",
    "epic": "epicgameslauncher",
    "obs": "obs64",
    "terminal": "wt",          # Windows Terminal
    "cmd": "cmd",
    "ifood": "https://www.ifood.com.br", # Redireciona para site se tentar abrir como app
    # === Microsoft Store ===
    "microsoft store": "ms-windows-store:",
    "store": "ms-windows-store:",
    "ms store": "ms-windows-store:",
    "loja microsoft": "ms-windows-store:",
    "loja": "ms-windows-store:",
}
VOICE = "pt-BR-FranciscaNeural"

SITES_WEB_ALIAS = {
    "insta",
    "instagram",
    "instagram direct",
    "instagram.com",
    "www.instagram.com",
    "direct instagram",
}

from mente_laylay.cognicao.memoria_visual import (
    MAX_MEMORIAS_VISUAIS_DIA,
    analisar_com_groq as _analisar_com_groq_modulo,
    capturar_tela_base64 as _capturar_tela_base64_modulo,
    configurar_memoria_visual,
    criar_memoria_visual_runtime as _criar_memoria_visual_runtime_mente,
    registrar_memoria_visual as _registrar_memoria_visual_modulo,
)

configurar_memoria_visual(PASTA_MEMORIA, MAX_MEMORIAS_VISUAIS_DIA)


_capturar_tela_base64 = _capturar_tela_base64_modulo
_analisar_com_groq = partial(
    _analisar_com_groq_modulo,
    api_key=GROQ_API_KEY.strip(),
    model=GROQ_VISION_MODEL,
)
def registrar_memoria_visual(
    imagem_b64,
    descricao,
    motivo="captura manual",
    contexto="",
    emocao="",
    intensidade=1,
    tags=None,
    origem="pc_a",
):
    caminho = _registrar_memoria_visual_modulo(
        imagem_b64,
        descricao,
        motivo=motivo,
        contexto=contexto,
        emocao=emocao,
        intensidade=intensidade,
        tags=tags,
        origem=origem,
    )
    if caminho:
        try:
            temporal = _registrar_evento_visual_temporal_mente(
                _estado_compartilhado_runtime.mental.get("consciencia_temporal"),
                str(descricao or ""),
                memoria_id=os.path.basename(str(caminho)),
                contexto=contexto if isinstance(contexto, dict) else {},
            )
            _estado_compartilhado_runtime.atualizar_campos(
                "mental", consciencia_temporal=temporal,
            )
        except Exception as erro:
            print(f"⚠️ [TEMPO:VISÃO] memória visual não entrou na linha do tempo: {erro}")
    return caminho


# ====================== COMUNICAÇÃO ======================
_chrome_solicitacoes = _ChromeSolicitacoesRuntime(
    obter_loop=_ws_transport_runtime.obter_loop,
    obter_extensoes=_ws_transport_runtime.obter_extensoes,
    transmitir=lambda mensagem: broadcast_command(mensagem),
)

_ambiente_navegacao_runtime = _criar_ambiente_navegacao_runtime_mente(
    namespace_getter=lambda: globals(),
    log=print,
)
atualizar_contexto = _ambiente_navegacao_runtime.atualizar_contexto
atualizar_contexto_por_url = _ambiente_navegacao_runtime.atualizar_contexto_por_url
organizar_janelas_robusto = _ambiente_navegacao_runtime.organizar_janelas
listar_programas_abertos = _ambiente_navegacao_runtime.listar_programas
listar_abas_chrome = _ambiente_navegacao_runtime.listar_abas
_resolver_alvo_ambiente = _ambiente_navegacao_runtime.resolver_alvo
abrir_url_com_reciclagem = _ambiente_navegacao_runtime.abrir_url
fechar_abas_vazias = _ambiente_navegacao_runtime.fechar_abas_vazias
_montar_url_site_ou_busca = _ambiente_navegacao_runtime.montar_url
_eh_alvo_site_web = _ambiente_navegacao_runtime.eh_alvo_site_web
_contexto_aponta_site_web = _ambiente_navegacao_runtime.contexto_aponta_site_web


def thread_exception_handler(args):
    nome_thread = str(getattr(getattr(args, "thread", None), "name", "thread") or "thread")
    erro = getattr(args, "exc_value", None)
    _saude_mente_runtime.registrar(
        f"thread:{nome_thread}",
        "degradado",
        detalhes=str(erro or "falha nao tratada"),
    )
    _tratar_excecao_thread_mente(
        args,
        log=print,
        traceback_mod=traceback,
    )

threading.excepthook = thread_exception_handler

is_valid_url = _is_valid_url_chrome_mente
ajustar_volume_sistema = _ajustar_volume_sistema_mente
ajustar_volume_sistema_relativo = _ajustar_volume_sistema_relativo_mente
definir_mudo_sistema = _definir_mudo_sistema_mente
ducking_volume = _ducking_volume_mente

formatar_url_ou_busca = partial(_formatar_url_ou_busca_chrome_mente, sites_directos=SITES_DIRECTOS)

_ws_close_other_extensions = partial(
    _fechar_extensoes_anteriores_chrome_mente,
    extensoes=_ws_transport_runtime.extensions,
    clientes_pc_b=_ws_transport_runtime.clientes_pc_b,
)

armazenar_contexto_pagina = _contexto_paginas.armazenar
get_dicionario_contexto = _contexto_paginas.texto_contexto


_chrome_ws_contexto_runtime = _criar_chrome_ws_contexto_runtime_mente(
    namespace_getter=lambda: globals(),
    monitor_saude=_saude_mente_runtime,
)
_contexto_user_ws = _chrome_ws_contexto_runtime.contexto_usuario
_aplicar_user_updates_ws = _chrome_ws_contexto_runtime.aplicar_updates_usuario
_contexto_action_ws = _chrome_ws_contexto_runtime.contexto_acao
_aplicar_action_updates_ws = _chrome_ws_contexto_runtime.aplicar_updates_acao


_chrome_ws_eventos_runtime = _criar_chrome_ws_eventos_runtime_mente(
    solicitacoes=_chrome_solicitacoes,
    playlist_state=playlist_state,
    yt_clean_url=lambda url: _yt_clean_url(url),
    playlist_avancar_proxima=lambda: _playlist_avancar_proxima(),
    falar_com_lipsync=lambda *args, **kwargs: falar_com_lipsync(*args, **kwargs),
    user_context_getter=_contexto_user_ws,
    aplicar_user_updates=_aplicar_user_updates_ws,
    action_context_getter=_contexto_action_ws,
    aplicar_action_updates=_aplicar_action_updates_ws,
)

_ws_dispatch_data = _chrome_ws_eventos_runtime.dispatch
_processar_pc_b_ws = _chrome_ws_contexto_runtime.processar_pc_b
_processar_page_data_ws = _chrome_ws_contexto_runtime.processar_pagina
_aplicar_page_updates_ws = _chrome_ws_contexto_runtime.aplicar_updates_pagina


_chrome_ws_runtime = _criar_chrome_ws_runtime_mente(
    contexto_getter=lambda: {
        **_ws_transport_runtime.contexto_conexoes(),
        "token_pc_b": os.environ.get("LAYLAY_PC_B_TOKEN", "").strip(),
        "_ws_close_other_extensions": _ws_close_other_extensions,
        "_ws_dispatch_data": _ws_dispatch_data,
        "_processar_mensagem_pc_b": _processar_pc_b_ws,
        "_processar_page_data": _processar_page_data_ws,
        "_aplicar_page_updates": _aplicar_page_updates_ws,
    },
)

ws_handler = _chrome_ws_runtime.handler

run_ws_server_in_thread = partial(
    _run_ws_server_in_thread_chrome_mente,
    ws_handler,
    set_loop=_ws_transport_runtime.definir_loop,
    host=os.environ.get("LAYLAY_WS_HOST", "0.0.0.0").strip() or "0.0.0.0",
)
broadcast_command = partial(
    _broadcast_command_chrome_mente,
    {"connected_extensions": _ws_transport_runtime.extensions},
)

solicitar_conteudo_pagina = _chrome_solicitacoes.solicitar_conteudo_pagina

fechar_aba_ativa_nativa = partial(
    _fechar_aba_ativa_nativa_chrome_mente,
    get_active_window=gw.getActiveWindow,
    hotkey=pyautogui.hotkey,
    sleep=time.sleep,
)

_chrome_comandos_runtime = _criar_chrome_comandos_runtime_mente(
    contexto_getter=lambda: {
        "ALLOWED_ACTIONS": ALLOWED_ACTIONS,
        "connected_extensions": _ws_transport_runtime.extensions,
        "ws_loop": _ws_transport_runtime.obter_loop(),
        "broadcast_command": broadcast_command,
        "enviar_chrome_confirmado": _chrome_solicitacoes.enviar_confirmado,
        "executar_chrome_confirmado": _chrome_solicitacoes.executar_confirmado,
        "solicitar_aba_ativa": _chrome_solicitacoes.solicitar_aba_ativa,
        "ultimo_resultado_chrome": lambda: dict(_chrome_solicitacoes.ultimo_resultado_comando),
        "formatar_url_ou_busca": formatar_url_ou_busca,
        "is_valid_url": is_valid_url,
        "atualizar_contexto_por_url": atualizar_contexto_por_url,
        "atualizar_contexto": atualizar_contexto,
        "_buscar_primeiro_video_youtube": _buscar_primeiro_video_youtube,
        "solicitar_tab_reciclagem": solicitar_tab_reciclagem,
        "modo_jogo_ativo": lambda: bool(_modo_jogo_runtime.ativo),
    }
)
validar_e_enviar_comando = _chrome_comandos_runtime.enviar
enviar_comando_chrome = _chrome_comandos_runtime.enviar

_remover_prefixo_exec = _remover_prefixo_exec_mente

_pid_from_hwnd = partial(_pid_from_hwnd_mente, ctypes, wintypes)

_classificar_assunto = _classificar_assunto_mente

_capturar_retrato_janela_ativa = partial(
    _capturar_janela_ativa_mente,
    gw,
    psutil,
    _pid_from_hwnd,
    _classificar_assunto,
)
from mente_laylay.percepcao.reconhecedor_voz_pessoal import (
    ReconhecedorVozPessoal as _ReconhecedorVozPessoal,
)

_modo_jogo_auto_habilitado = os.environ.get("LAYLAY_MODO_JOGO_AUTO", "1").casefold() not in {
    "0", "false", "nao", "não", "off", "desligado",
}
_modo_jogo_runtime = _criar_modo_jogo_runtime_mente(
    definir_bloqueio_llm=_llm_http_runtime.definir_modo_jogo,
    descarregar_modelo=lambda: _descarregar_modelo_ollama_mente(MODEL),
    habilitado=_modo_jogo_auto_habilitado,
    entrada_estavel_s=float(os.environ.get("LAYLAY_MODO_JOGO_ENTRADA_SEGUNDOS", "4")),
    tolerancia_saida_s=float(os.environ.get("LAYLAY_MODO_JOGO_SAIDA_SEGUNDOS", "45")),
    log=print,
)
modo_jogo_ativo = lambda: bool(_modo_jogo_runtime.ativo)

_monitor_janelas_runtime = _criar_monitor_janelas_runtime_mente(
    capturar_janela=_capturar_retrato_janela_ativa,
    atualizar_contexto=_atualizar_contexto_sistema_monitor,
    continuidade_get=_continuidades_get,
    continuidade_update=_continuidades_update,
    esta_falando=lambda: bool(_conversa_estado_get("is_speaking", False)),
    conversa_ativa=lambda: bool(_conversa_estado_get("conversa_ativa", False)),
    ultimo_proativo_get=lambda: float(_percepcao_get("ultimo_proativo_ts", 0.0) or 0.0),
    ultimo_proativo_set=_definir_ultimo_proativo_ts,
    sugestoes_bloqueadas_get=lambda: sugestao_bloqueada_ate,
    janela_em_tela_cheia=lambda janela: _janela_em_tela_cheia_mente(pyautogui, janela),
    detectar_gatilho=_detectar_gatilho_proativo_sistema_mente,
    fala_gatilho=_fala_gatilho_proativo_sistema_mente,
    # Observações do monitor pertencem à mesma mente. Se surgirem enquanto uma
    # resposta está sendo construída, entram nela em vez de disputar o áudio.
    falar=lambda texto, emocao="calma", nivel=1: _agendar_fala_proativa(
        "contexto_janela",
        texto,
        emocao,
        nivel,
        mesclar_turno=True,
    ),
    preparar_sugestao=lambda comando, payload, fala: _preparar_sugestao_aprendida(
        comando, payload, fala
    ),
    atualizar_modo_jogo=_modo_jogo_runtime.observar,
    interacao_iniciada=lambda: float(
        _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
    ) > 0.0,
    clock=time.time,
    sleep=time.sleep,
    log=print,
)

ativar_tela_cheia_robusta = partial(
    _maximizar_janela_mente,
    gw,
    pyautogui,
    psutil_mod=psutil,
)

focar_janela_app = partial(
    _focar_janela_mente,
    gw,
    pyautogui,
    psutil_mod=psutil,
)

_janela_app_esta_em_foco = partial(_janela_esta_em_foco_mente, gw)

fechar_programa = _fechar_programa_mente


# ====================== CONSCIÊNCIA DE ESTADO (FERRAMENTAS DE LEITURA) ======================

_normalizar_alvo_ambiente = _normalizar_alvo_ambiente_mente


# ====================== SISTEMA DE ARQUIVOS (CRUD) BLINDADO ======================

resolver_caminho = _resolver_caminho_mente
criar_pasta = _criar_pasta_mente
criar_ou_editar_arquivo = _criar_ou_editar_arquivo_mente
mover_arquivo = _mover_arquivo_mente
renomear_arquivo = _renomear_arquivo_mente
deletar_item = _deletar_item_mente

# ====================== CONSCIÊNCIA DE ARQUIVOS (FILE CONTEXT) ======================

mapear_pastas_principais = _mapear_pastas_principais_mente
buscar_arquivo_no_pc = _buscar_arquivo_no_pc_mente


# ====================== FUNÇÕES DE VOZ ======================
modular_audio_params = _modular_audio_params_mente

limpar_para_voz = _limpar_para_voz_mente


_orquestrador_fala_runtime = _criar_orquestrador_fala_runtime_mente(
    namespace_getter=lambda: globals(),
)
_registrar_fala_proativa_emitida = (
    _orquestrador_fala_runtime.registrar_fala_proativa_emitida
)


_porteiro_proatividade_runtime = _criar_porteiro_proatividade_runtime_mente(
    contexto_getter=lambda: {
        "modo_chat": bool(_conversa_estado_get("modo_chat", False)),
        "conversa_ativa": bool(_conversa_estado_get("conversa_ativa", False)),
        "funcao_comunicativa": str(
            (_estado_compartilhado_runtime.mental.get("funcao_comunicativa_atual") or {}).get("funcao")
            if isinstance(_estado_compartilhado_runtime.mental.get("funcao_comunicativa_atual"), dict)
            else ""
        ),
        "ultima_entrada_ts": float(
            _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
        ),
        "modo_jogo_ativo": bool(_modo_jogo_runtime.ativo),
        "assunto": str(
            (_estado_compartilhado_runtime.percepcao.get("contexto_sistema") or {}).get("assunto")
            if isinstance(_estado_compartilhado_runtime.percepcao.get("contexto_sistema"), dict)
            else ""
        ),
        "titulo_janela": str(
            (_estado_compartilhado_runtime.percepcao.get("contexto_sistema") or {}).get("title")
            if isinstance(_estado_compartilhado_runtime.percepcao.get("contexto_sistema"), dict)
            else ""
        ),
    },
    perfil_getter=lambda: _estado_compartilhado_runtime.obter_copia(
        "mental", "perfil_proatividade", {},
    ),
    perfil_setter=lambda perfil: _estado_compartilhado_runtime.atualizar_campos(
        "mental", perfil_proatividade=perfil,
    ),
    registrar_decisao_cb=_observabilidade_mente_runtime.registrar_decisao,
)


_voz_runtime = _criar_voz_runtime_mente(
    fallback_fala=FALLBACK_FALA_NEUTRA,
    voice=VOICE,
    edge_tts_mod=edge_tts,
    sounddevice_mod=sd,
    soundfile_mod=sf,
    pyttsx3_mod=pyttsx3,
    limpar_para_voz_cb=limpar_para_voz,
    preparar_tts_cb=_preparar_texto_para_tts_mente,
    formatar_mensagem_cb=_formatar_mensagem_laylay,
    ducking_volume_cb=lambda ativar: ducking_volume(ativar=ativar),
    modular_audio_params_cb=modular_audio_params,
    compor_fala_proativa_cb=_compor_fala_proativa,
    ajustar_estado_fala_cb=_ajustar_estado_voz,
    proativa_permitida_cb=lambda: (
        not bool(_conversa_estado_get("modo_chat", False))
        and not bool(_conversa_estado_get("conversa_ativa", False))
        and time.time() - float(_estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0) >= 30.0
    ),
    avaliar_proatividade_cb=_porteiro_proatividade_runtime.avaliar,
    chave_turno_cb=lambda: float(
        _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
    ),
    interrupt_event=interrupt_event,
    registrar_fala_emitida_cb=_registrar_fala_proativa_emitida,
    registrar_metrica_cb=_observabilidade_mente_runtime.registrar_metrica,
    registrar_falha_cb=_observabilidade_mente_runtime.registrar_falha,
    log=print,
    # Respostas disparadas pelo mesmo turno entram numa única fala/linha.
    batch_window=0.20,
    batch_max_items=4,
)
from mente_laylay.cognicao.modalidade_turno import (
    classificar_modalidade_turno as _classificar_modalidade_turno_mente,
)
from mente_laylay.memoria_mental.pendencia import pendencia_ativa as _pendencia_ativa_turno_mente
from mente_laylay.cognicao.identidade_conversacional import (
    analisar_identidade_turno as _analisar_identidade_turno_mente,
    ajustar_autorreferencia_assistente as _ajustar_autorreferencia_assistente_mente,
    resumo_identidade_turno as _resumo_identidade_turno_mente,
)
from mente_laylay.emocoes.leitura_usuario import analisar_funcao_comunicativa as _analisar_funcao_comunicativa_mente
from mente_laylay.memoria_mental.correcoes_usuario import (
    extrair_correcao_duravel as _extrair_correcao_duravel_mente,
    persistir_correcao_duravel as _persistir_correcao_duravel_mente,
)
from mente_laylay.memoria_mental.correcoes_interpretacao import (
    abrir_correcao_interpretacao as _abrir_correcao_interpretacao_mente,
    concluir_correcao_interpretacao as _concluir_correcao_interpretacao_mente,
)
from mente_laylay.memoria_mental.encerramento_assunto import (
    classificar_encerramento_assunto as _classificar_encerramento_assunto_mente,
    encerrar_topico as _encerrar_topico_mente,
)
from mente_laylay.memoria_mental.assunto_estruturado import (
    atualizar_assunto_estruturado as _atualizar_assunto_estruturado_mente,
)
from mente_laylay.memoria_mental.trilha_turno import (
    registrar_etapa_turno as _registrar_etapa_turno_mente,
)
from mente_laylay.personalidade.memoria_sutil import sutilizar_referencia_memoria as _sutilizar_referencia_memoria_mente
from mente_laylay.personalidade.diretor_fala import dirigir_fala as _dirigir_fala_mente
from mente_laylay.cognicao.plano_turno import (
    atualizar_plano_turno as _atualizar_plano_turno_mente,
    planejar_turno as _planejar_turno_mente,
    verificar_fala_turno as _verificar_fala_turno_mente,
)

# ====================== FUNÇÕES DE MEMÓRIA ======================
_persistencia_memoria_runtime = _criar_persistencia_memoria_runtime_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    base_system_prompt=BASE_SYSTEM_PROMPT,
    estado_obter=_estado_compartilhado_runtime.obter,
    estado_atualizar=_estado_compartilhado_runtime.atualizar_campos,
    ajustar_humor_cb=lambda delta, motivo: ajustar_humor(delta, motivo),
    registrar_autoaprimoramento_cb=_registrar_autoaprimoramento,
    log=print,
)
carregar_memoria = _persistencia_memoria_runtime.carregar
salvar_memoria = _persistencia_memoria_runtime.salvar
_registrar_autocorrecao_virtual = _persistencia_memoria_runtime.registrar_autocorrecao

init_memoria_contexto_diaria = partial(_init_memoria_contexto_diaria_mente, MEMORIA_CONTEXTO_ARQUIVO)
carregar_estado_briefing = partial(_carregar_estado_briefing_ambiente, BRIEFING_ARQUIVO)
salvar_estado_briefing = partial(_salvar_estado_briefing_ambiente, BRIEFING_ARQUIVO, print_fn=print)
obter_clima_wttr = partial(
    _obter_clima_wttr_ambiente,
    BRIEFING_CIDADE,
    requests_get=requests.get,
    print_fn=print,
    timeout_s=2.5,
)


obter_clima_localidade = partial(
    _obter_clima_localidade_ambiente,
    cidade_padrao=BRIEFING_CIDADE,
    requests_get=requests.get,
    print_fn=print,
)

repetir_briefing = partial(
    _ambiente_sistema_runtime.repetir_briefing_atual,
    cidade=BRIEFING_CIDADE,
    obter_clima=obter_clima_wttr,
    enviar_mensagem=lambda *args, **kwargs: enviar_mensagem(*args, **kwargs),
    limpar_resposta=lambda texto: limpar_resposta(texto),
    remover_prefixo_exec=lambda texto: _remover_prefixo_exec(texto),
    falar=lambda texto, emocao, nivel: falar_com_lipsync(texto, emocao, nivel),
    print_fn=print,
    )

_detectar_repetir_briefing = _detectar_repetir_briefing_ambiente

detectar_comando_saude = _detectar_comando_saude_ambiente


_aprendizado_runtime = _criar_aprendizado_runtime_mente(
    pasta_memoria=PASTA_MEMORIA,
    arquivo_rotina=ROTINA_ARQUIVO_APRENDIDO,
    arquivo_musica_historico=MUSICA_ARQUIVO_HISTORICO,
    arquivo_musica_feedback=MUSICA_ARQUIVO_FEEDBACK,
    contexto_getter=lambda: {
        "contexto_sistema": _percepcao_get("contexto_sistema", {}),
        "obter_janela_ativa": lambda: gw.getActiveWindow(),
        "continuidades_get": _continuidades_get,
        "continuidades_set": _continuidades_set,
        "falar_com_lipsync": falar_com_lipsync,
        "abrir_programa": abrir_programa,
        "contexto_aponta_descanso": _contexto_aponta_descanso,
        "registrar_observacao_aprendizado": lambda janela, assunto, hora: (
            _motor_aprendizado_runtime.registrar_observacao_rotina(janela, assunto, hora)
        ),
        # No modo chat, a fala do usuário tem prioridade absoluta. Sugestões de
        # rotina podem esperar em vez de atravessar um desabafo ou comando.
        "agendar_fala_proativa": lambda *args, **kwargs: (
            False
            if _conversa_estado_get("modo_chat", False)
            or _conversa_estado_get("conversa_ativa", False)
            or float(_estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0) <= 0.0
            else _agendar_fala_proativa(*args, **kwargs)
        ),
    },
    log=print,
)
_verificar_musica_autonoma = _busca_musical_runtime.verificar_autonoma
_buscar_primeiro_video_youtube = _busca_musical_runtime.buscar_primeiro_video
_iniciar_worker_de_falas = _voz_runtime.iniciar_worker
_normalizar_segmento_fala = _voz_runtime.normalizar_segmento_fala
_agendar_fala_proativa = _voz_runtime.agendar_fala_proativa


_preferencias_sugestoes_runtime = _criar_preferencias_sugestoes_runtime_mente(
    namespace_getter=lambda: globals(),
)
_preferencia_sugestao_get = _preferencias_sugestoes_runtime.obter
_registrar_preferencia_sugestao = _preferencias_sugestoes_runtime.registrar
_preparar_sugestao_aprendida = _preferencias_sugestoes_runtime.preparar
_interpretar_contraproposta_sugestao = (
    _preferencias_sugestoes_runtime.interpretar_contraproposta
)

_ritmo_circadiano_runtime = _criar_ritmo_circadiano_runtime_mente(
    estado_get=lambda: dict(_percepcao_get("ritmo_circadiano", {}) or {}),
    estado_set=lambda estado: _percepcao_set("ritmo_circadiano", dict(estado or {})),
    continuidades_get=_continuidades_get,
    continuidades_update=_continuidades_update,
    agendar_fala=_agendar_fala_proativa,
    interacao_iniciada=lambda: float(
        _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
    ) > 0.0,
    conversa_ativa=lambda: bool(
        _conversa_estado_get("modo_chat", False)
        or _conversa_estado_get("conversa_ativa", False)
    ),
    preparar_sugestao=_preparar_sugestao_aprendida,
    fuso=os.environ.get("LAYLAY_FUSO_HORARIO", "America/Sao_Paulo"),
    log=print,
)

_motor_temporal_runtime = _criar_motor_temporal_runtime_mente(
    estado_get=lambda: dict(
        _estado_compartilhado_runtime.mental.get("consciencia_temporal") or {}
    ),
    estado_set=lambda estado: _estado_compartilhado_runtime.atualizar_campos(
        "mental", consciencia_temporal=dict(estado or {}),
    ),
    contexto_getter=lambda: {
        **dict(_obter_contexto_perceptivo() or {}),
        "emocao_usuario": str(
            _estado_compartilhado_runtime.mental.get("emocao_usuario") or ""
        ),
        "perfil_proatividade": dict(
            _estado_compartilhado_runtime.mental.get("perfil_proatividade") or {}
        ),
        "titulo_janela": str(
            (_percepcao_get("contexto_sistema", {}) or {}).get("title") or ""
        ),
    },
    agendar_fala=_agendar_fala_proativa,
    interacao_iniciada=lambda: float(
        _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
    ) > 0.0,
    conversa_ativa=lambda: bool(
        _conversa_estado_get("modo_chat", False)
        or _conversa_estado_get("conversa_ativa", False)
    ),
    log=print,
)

_motor_aprendizado_runtime = _criar_motor_aprendizado_runtime_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    contexto_getter=_obter_contexto_perceptivo,
    agendar_fala=_agendar_fala_proativa,
    continuidades_get=_continuidades_get,
    continuidades_update=_continuidades_update,
    interacao_iniciada=lambda: float(
        _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
    ) > 0.0,
    conversa_ativa=lambda: bool(
        _conversa_estado_get("modo_chat", False)
        or _conversa_estado_get("conversa_ativa", False)
    ),
    pesquisar_conhecimento=_pesquisa_contextual_runtime.pesquisar_contexto_tema,
    log=print,
)


_finalizar_encerramento_assunto_apos_fala = (
    _orquestrador_fala_runtime.finalizar_encerramento_assunto
)
falar_com_lipsync = _orquestrador_fala_runtime.falar

_iot_runtime = _criar_runtime_iot_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    definir_emocao=_definir_emocao_conversacional,
    emitir_fala=False,
    resolver_cor=lambda nome: _resolver_cor_por_ia_mente(
        nome,
        enviar_mensagem=lambda *args, **kwargs: enviar_mensagem(*args, **kwargs),
        log=print,
    ),
    log=print,
)
_detectar_intencao_iot = _iot_runtime.detectar
_executar_intencao_iot = _iot_runtime.executar
_falar_status_saude = partial(
    _ambiente_sistema_runtime.falar_status_saude,
    psutil_mod=psutil,
    falar=lambda texto, emocao="calma", nivel=1: _agendar_fala_proativa(
        "saude",
        texto,
        emocao,
        nivel,
    ),
    print_fn=print,
)
from mente_laylay.especialistas.coordenador import (
    construir_parecer_especialistas as _construir_parecer_especialistas_mente,
)
from mente_laylay.cognicao.retrato_turno import (
    construir_retrato_turno as _construir_retrato_turno_mente,
)
_monitor_saude_daemon = partial(
    _ambiente_sistema_runtime.monitorar_saude,
    psutil_mod=psutil,
    falar_status_cb=_falar_status_saude,
    cpu_threshold=SAUDE_CPU_THRESHOLD,
    ram_threshold=SAUDE_RAM_THRESHOLD,
    cpu_sustentado_segundos=SAUDE_CPU_SUSTENTADO_SEGUNDOS,
    print_fn=print,
    sleep_fn=time.sleep,
)


_entregar_fala_inicial_confirmada = (
    _orquestrador_fala_runtime.entregar_fala_inicial_confirmada
)


briefing_matinal = partial(
    _ambiente_sistema_runtime.executar_briefing,
    cidade=BRIEFING_CIDADE,
    carregar_estado=carregar_estado_briefing,
    salvar_estado=salvar_estado_briefing,
    obter_clima=obter_clima_wttr,
    montar_fala=lambda clima: _montar_briefing_matinal_ambiente(
        cidade=BRIEFING_CIDADE,
        clima=clima,
        enviar_mensagem_cb=enviar_mensagem,
        limpar_resposta_cb=limpar_resposta,
        remover_prefixo_exec_cb=_remover_prefixo_exec,
    ),
    agendar_fala=_entregar_fala_inicial_confirmada,
    print_fn=print,
)
_estado_aprendizado_atual = _aprendizado_runtime.snapshot


_rotina_registrar_feedback = _adaptadores_aplicacao_runtime.registrar_feedback_rotina


_musica_registrar_historico = _aprendizado_runtime.musica_registrar_historico


_feedback_pendente_runtime = _criar_feedback_pendente_runtime_mente(
    contexto_getter=lambda: {
        "continuidades_get": _continuidades_get,
        "continuidades_update": _continuidades_update,
        "normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
        "interpretar_confirmacao_llm": interpretar_confirmacao_llm,
        "interpretar_resposta_pendente": _interpretar_resposta_pendente_mente,
        "resumo_mente_integrada_para_prompt": _resumo_mente_integrada_para_prompt_mente,
        "mente_integrada_estado": _estado_compartilhado_runtime.mental,
        "enviar_mensagem": enviar_mensagem,
        "handle_feedback_pendente": _handle_feedback_pendente_mente,
        "handle_sugestao_confirmacao": _handle_sugestao_confirmacao,
        "solicitar_aba_ativa": solicitar_aba_ativa,
        "add_to_playlist_url": add_to_playlist_url,
        "extrair_nome_playlist": extrair_nome_playlist,
        "yt_clean_title": _yt_clean_title,
        "falar_com_lipsync": falar_com_lipsync,
        "set_ultima_playlist": lambda valor: _musica_estado_set("ultima_playlist", valor),
        "rotina_registrar_feedback": _rotina_registrar_feedback,
        "gmail_buscar_nao_lidos": _gmail_buscar_nao_lidos,
        "gmail_falar_resumo_estiloso": _gmail_falar_resumo_estiloso,
        "processar_comandos_imediatos": processar_comandos_imediatos,
    },
    log=print,
)


_classificar_confirmacao_local = _feedback_pendente_runtime.classificar_confirmacao_local
_handle_feedback_pendente = _feedback_pendente_runtime.handle_feedback_pendente
_handle_feedback_pendente_misto = _feedback_pendente_runtime.handle_feedback_pendente_misto


monitor_rotina_daemon = partial(
    _aprendizado_runtime.monitorar,
    dias_para_aprender=ROTINA_DIAS_PARA_APRENDER,
    limite_rejeicao=ROTINA_BLOQUEIO_REJEICAO_VEZES,
    analisar_musica_cb=None,
    intervalo_s=60,
    sleep_fn=time.sleep,
)

# ====================== FUNÇÕES DE PROCESSAMENTO DE LINGUAGEM ======================
_cliente_llm_runtime = _criar_cliente_llm_runtime_mente(
    namespace_getter=lambda: {
        "llm_endpoint_eh_local": _llm_endpoint_eh_local,
        "memoria_inteligente": memoria_inteligente,
        "model": MODEL,
        "normalizar_texto": _normalizar_texto_com_apelidos,
        "texto_tem_comando_explicito": _texto_tem_comando_explicito,
        "extrair_json": _extrair_json_resposta_mente,
        "mapear_pastas": mapear_pastas_principais,
        "contexto_logs": _estado_compartilhado_runtime.obter_copia(
            "percepcao", "logs_navegador", []
        ),
        "contexto_navegador_relevante": _contexto_navegador_relevante,
        "contexto_sistema": lambda: _percepcao_get("contexto_sistema", {}),
        "obter_contexto_paginas": get_dicionario_contexto,
        "resumo_mente_integrada": _resumo_mente_integrada_para_prompt,
        "post_chat": _post_chat_llm,
        "api_key": API_KEY,
        "http_referer": OPENROUTER_HTTP_REFERER,
        "app_title": OPENROUTER_APP_TITLE,
    },
    log=print,
)
enviar_mensagem = _cliente_llm_runtime.enviar
_interpretador_semantico_runtime = _criar_interpretador_semantico_runtime_mente(
    contexto_getter=lambda: {
        "mente": _estado_compartilhado_runtime.mental,
        "mensagens": _memoria_conversa_get("messages", []),
    },
    enviar_mensagem=enviar_mensagem,
    log=print,
)
resumir_pagina_no_dicionario = partial(
    _contexto_paginas.resumir,
    enviar_mensagem=enviar_mensagem,
)


_confirmacao_llm_runtime = _criar_confirmacao_llm_runtime_mente(
    namespace_getter=lambda: {
        "post_chat": _post_chat_llm,
        "api_key": API_KEY,
        "model": MODEL,
        "http_referer": OPENROUTER_HTTP_REFERER,
        "app_title": OPENROUTER_APP_TITLE,
    }
)
interpretar_confirmacao_llm = _confirmacao_llm_runtime.interpretar
_merge_intent_llm = _confirmacao_llm_runtime.mesclar

solicitar_lista_abas = _chrome_solicitacoes.solicitar_lista_abas
solicitar_tab_reciclagem = _chrome_solicitacoes.solicitar_tab_reciclagem


_registrar_contexto_resumo_pagina = (
    _adaptadores_aplicacao_runtime.registrar_contexto_resumo_pagina
)


_resumo_conteudo_runtime = _criar_resumo_conteudo_runtime_mente(
    namespace_getter=lambda: {
        "websocket_disponivel": lambda: _ws_transport_runtime.obter_loop() is not None,
        "solicitar_conteudo": solicitar_conteudo_pagina,
        "falar": falar_com_lipsync,
        "enviar_mensagem": enviar_mensagem,
        "limpar_resposta": limpar_resposta,
        "remover_prefixo_exec": _remover_prefixo_exec,
        "transcript_api": YouTubeTranscriptApi,
        "registrar_contexto_resumo": _registrar_contexto_resumo_pagina,
    },
    log=print,
)
resumir_pagina_ou_video = _resumo_conteudo_runtime.resumir

solicitar_aba_ativa = _chrome_solicitacoes.solicitar_aba_ativa

_selecao_abas_runtime = _criar_selecao_abas_runtime_mente(
    namespace_getter=lambda: {
        "post_chat": _post_chat_llm,
        "api_key": API_KEY,
        "model": MODEL,
        "http_referer": OPENROUTER_HTTP_REFERER,
        "app_title": OPENROUTER_APP_TITLE,
    }
)
selecionar_abas_para_fechar_llm = _selecao_abas_runtime.selecionar

_porteiro_runtime = _criar_porteiro_chrome_runtime_mente(
    abas_sugeridas=_abas_sugeridas_fechar,
    obter_ram_percent=lambda: psutil.virtual_memory().percent,
    listar_abas=listar_abas_chrome,
    obter_estado_chrome=_chrome_estado.snapshot,
    falar=lambda texto, emocao="irritada", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    enviar_fechamento=lambda payload: (
        asyncio.run_coroutine_threadsafe(broadcast_command(payload), loop)
        if (loop := _ws_transport_runtime.obter_loop()) else None
    ),
    ram_threshold=RAM_THRESHOLD_PORTEIRO,
    idle_minutos=ABA_IDLE_MINUTOS,
    intervalo_minutos=PORTEIRO_INTERVALO_MIN,
    log=print,
)

_porteiro_daemon = _porteiro_runtime.daemon
_executar_fechar_abas_paradas = _porteiro_runtime.fechar_sugeridas

# ====================== SISTEMA DE AGENDAMENTOS ======================
_agendamentos_file = os.path.join(_base_dir, AGENDAMENTOS_ARQUIVO)

_pc_b_runtime = _criar_pc_b_runtime_mente(
    clientes_getter=lambda: _ws_transport_runtime.clientes_pc_b,
    loop_getter=_ws_transport_runtime.obter_loop,
    log=print,
)
_enviar_pc_b = _pc_b_runtime.enviar
_agenda_enviar_chrome_local = _chrome_comandos_runtime.enviar_payload_bruto

from mente_laylay.autonomia.agenda_windows import sincronizar_despertares_windows as _sincronizar_despertares_windows


_agenda_runtime = _criar_agenda_runtime_mente(
    _agendamentos_file,
    falar_cb=falar_com_lipsync,
    abrir_programa_cb=lambda alvo: abrir_programa(alvo),
    enviar_pc_b_cb=_enviar_pc_b,
    sincronizar_despertares_cb=lambda itens: _sincronizar_despertares_windows(
        itens,
        estado_path=os.path.join(_base_dir, "memoria", "agenda_windows_tarefas.json"),
        log=print,
    ),
    enviar_chrome_local_cb=_agenda_enviar_chrome_local,
    executar_exec_cb=lambda cmd, arg: _executar_exec(cmd, arg),
    executar_intencao_cb=lambda resultado, texto: executar_intencao(resultado, texto),
    log=print,
)


_agendamentos_load = _agenda_runtime.load
_agendamentos_save = _agenda_runtime.save
_agendamentos_transacionar = _agenda_runtime.transacionar
_agenda_daemon = _agenda_runtime.daemon
_fala_agendamentos_estilosa = _agenda_runtime.fala_estilosa

_playlists_load = _playlist_runtime.load
LIST_PLAYLIST_CONTENT = _playlist_runtime.list_content


_fala_playlist_conteudo_estilosa = _fala_playlist_conteudo_estilosa_mente


_yt_clean_url = _yt_clean_url_mente
_yt_clean_title = _yt_clean_title_mente

_normalizar_texto = _normalizar_texto_mente

_linguagem_aprendida_runtime = _criar_linguagem_aprendida_runtime_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    normalizar_texto=_normalizar_texto,
    texto_social_curto=lambda texto: _texto_social_curto(texto),
    falar=lambda fala, emocao, nivel: falar_com_lipsync(fala, emocao, nivel),
    log=print,
)
_normalizar_texto_com_apelidos = _linguagem_aprendida_runtime.normalizar_com_apelidos
_ajustar_tom_por_emocao = partial(
    _ajustar_tom_por_emocao_mente,
    normalizar_cb=_normalizar_texto_com_apelidos,
)
_processar_aprendizado_apelido_imediato = _linguagem_aprendida_runtime.processar_aprendizado_imediato
_extrair_resultados_youtube_busca = partial(
    _extrair_resultados_youtube_busca_mente,
    normalizar_texto_cb=_normalizar_texto_com_apelidos,
)
_normalizar_query_musical = partial(
    _normalizar_query_musical_mente,
    normalizar_texto_cb=_normalizar_texto_com_apelidos,
)

_limpar_nome_playlist = _limpar_nome_playlist_mente

_playlist_nome_explicito_na_frase = _playlist_runtime.nome_explicito_na_frase
mover_item_playlist = _playlist_runtime.mover_item_contextual


detectar_mover_playlist_texto = _detectar_mover_playlist_texto_mente


extrair_nome_playlist = _playlist_runtime.extrair_nome

_formatar_playlists_para_prompt = _playlist_runtime.formatar_para_prompt


_pedido_lista_geral_playlist = _playlist_runtime.pedido_lista_geral


_listar_playlists_salvas = _playlist_runtime.listar_salvas
_sincronizar_playlists_da_laylay = _playlist_laylay_runtime.sincronizar
_listar_playlists_da_laylay = _playlist_laylay_runtime.listar
_copiar_faixa_da_playlist_laylay = _playlist_laylay_runtime.copiar_faixa


_detectar_playlist_nome_direto = _playlist_runtime.detectar_nome_direto_contextual
_carregar_playlists_para_memoria = _playlist_runtime.carregar_para_memoria

add_to_playlist_url = _playlist_runtime.add_url
ADD_TO_PLAYLIST = _playlist_runtime.add_and_verify
_playlist_primeira_url = _playlist_runtime.primeira_url
_playlist_item_at = _playlist_runtime.item_at
playlist_len = _playlist_runtime.len
_playlist_shuffle_start = _playlist_runtime.shuffle_start
delete_playlist = _playlist_runtime.delete
_playlist_avancar_proxima = _playlist_runtime.avancar_proxima
_playlist_voltar_anterior = _playlist_runtime.voltar_anterior
play_playlist = _playlist_runtime.play


_executar_sugestao_temporal = _preferencias_sugestoes_runtime.executar_temporal

_sugestoes_sistema_runtime = _criar_sugestoes_sistema_runtime_mente(
    contexto_getter=lambda: {
        "fechar_abas_vazias": fechar_abas_vazias,
        "pesquisa_contextual_runtime": _pesquisa_contextual_runtime,
        "abrir_url_externo": webbrowser.open,
        "enviar_comando_chrome": enviar_comando_chrome,
        "solicitar_lista_abas": solicitar_lista_abas,
        "selecionar_abas_para_fechar_llm": selecionar_abas_para_fechar_llm,
        "abrir_caminho": os.startfile,
        "continuidades_get": _continuidades_get,
        "continuidades_update": _continuidades_update,
        "resetar_sugestao": _resetar_sugestao,
        "normalizar_texto": _normalizar_texto_com_apelidos,
        "classificar_confirmacao_local": _classificar_confirmacao_local,
        "interpretar_confirmacao_llm": interpretar_confirmacao_llm,
        "merge_intent_llm": _merge_intent_llm,
        "falar": falar_com_lipsync,
        "messages": _memoria_conversa_get("messages", []),
        "enviar_mensagem": enviar_mensagem,
        "limpar_resposta": limpar_resposta,
        "remover_prefixo_exec": _remover_prefixo_exec,
        "current_emotion": _conversa_estado_get("current_emotion", "calma"),
        "emotion_level": _conversa_estado_get("emotion_level", 1),
        "memoria_inteligente": memoria_inteligente,
        "salvar_memoria": salvar_memoria,
        "log": print,
        "executar_intencao": executar_intencao,
        "sugestao_bloqueada_ate": sugestao_bloqueada_ate,
        "resposta_conversa_local": _resposta_conversa_local,
        "executar_sugestao_temporal": _executar_sugestao_temporal,
        "preferencia_sugestao_get": _preferencia_sugestao_get,
        "interpretar_contraproposta": _interpretar_contraproposta_sugestao,
        "registrar_preferencia_sugestao": _registrar_preferencia_sugestao,
        "confirmar_hipotese_aprendizado": _motor_aprendizado_runtime.confirmar_hipotese,
        "registrar_excecao_preferencia": _motor_aprendizado_runtime.registrar_excecao_preferencia,
        "resolver_conflito_preferencia": _motor_aprendizado_runtime.resolver_conflito_preferencia,
        "registrar_feedback_proatividade": _porteiro_proatividade_runtime.registrar_feedback,
    }
)
_executar_combo_modo_code = _sugestoes_sistema_runtime.executar_modo_code
_executar_combo_modo_gamer = _sugestoes_sistema_runtime.executar_modo_gamer
_executar_combo_organizacao = _sugestoes_sistema_runtime.executar_organizacao
_handle_sugestao_confirmacao = _sugestoes_sistema_runtime.processar_confirmacao
_detectar_sugestao_indireta = _sugestoes_sistema_runtime.detectar_indireta
_registrar_sugestao_indireta = _sugestoes_sistema_runtime.registrar_indireta

limpar_resposta = _limpar_resposta_mente

_contexto_imediato_runtime = _criar_contexto_imediato_runtime_mente(
    namespace_getter=lambda: globals(),
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
)
_extrair_app_explicito_em_comando_janela = _contexto_imediato_runtime.extrair_app_explicito
_resolver_comando_janela_contextual_forcado = _contexto_imediato_runtime.resolver_janela
_responder_contexto_janela_indisponivel = _contexto_imediato_runtime.responder_janela_indisponivel
_resolver_comando_midia_contextual_forcado = _contexto_imediato_runtime.resolver_midia
_resolver_comando_arquivo_contextual_forcado = _contexto_imediato_runtime.resolver_arquivo
_referencia_contextual_imediata = _contexto_imediato_runtime.referencia
_resolver_comando_acao_geral_contextual_forcado = _contexto_imediato_runtime.resolver_acao_geral
_resolver_comando_contextual_forcado = _contexto_imediato_runtime.resolver
_resolver_reparacao_conversacional = _contexto_imediato_runtime.resolver_reparacao

_adaptadores_conversacionais_runtime = _criar_adaptadores_conversacionais_runtime_mente(
    normalizar_texto=_normalizar_texto_com_apelidos,
    texto_depende_de_contexto=lambda texto: _texto_depende_de_contexto(texto),
    resolver_comando_contextual=_resolver_comando_contextual_forcado,
    limpar_destino=lambda texto: _limpar_destino_pc_b(texto),
    normalizar_query_musical=_normalizar_query_musical,
    apps_map=APPS_MAP,
    sites_diretos=SITES_DIRECTOS,
)
interpretar_comando_local_rapido = _adaptadores_conversacionais_runtime.interpretar_comando_local
_usar_modo_rapido_conversa = _adaptadores_conversacionais_runtime.usar_modo_rapido
_ignorar_token_solto = _adaptadores_conversacionais_runtime.ignorar_token_solto
_texto_expresso_melhor_no_deterministico = (
    _adaptadores_conversacionais_runtime.texto_expresso_melhor_no_deterministico
)
_extrair_intencao_abrir_app = _adaptadores_conversacionais_runtime.extrair_intencao_abrir_app
_resolver_query_musical_por_estilo = _adaptadores_conversacionais_runtime.resolver_query_musical_por_estilo


# ====================== MICROFONE EM TEMPO REAL ======================
_resetar_sugestao = _estado_compartilhado_runtime.limpar_sugestao

_extrair_json_da_ia = _extrair_json_resposta_mente

_contexto_musical_ativo = partial(
    _estado_compartilhado_runtime.contexto_musical_ativo,
    playlist_state,
)
_contexto_mental_ativo = partial(
    _estado_compartilhado_runtime.contexto_mental_ativo,
    playlist_state,
)

_texto_depende_de_contexto = partial(
    _texto_depende_de_contexto_mente,
    normalizar_texto_cb=_normalizar_texto_com_apelidos,
)

_fluxo_prioritario_da_ia = partial(
    _fluxo_prioritario_da_ia_mente,
    normalizar_texto_cb=_normalizar_texto_com_apelidos,
    texto_depende_de_contexto_cb=_texto_depende_de_contexto,
)

_resumo_agendamentos_para_prompt = partial(_resumo_agendamentos_para_prompt_mente, _agendamentos_load)
_extrair_agendamento_local = partial(
    _extrair_agendamento_local_mente,
    normalizar_texto_cb=_normalizar_texto_com_apelidos,
)
_extrair_acao_agendada_local = partial(
    _extrair_acao_agendada_local_mente,
    normalizar_texto_cb=_normalizar_texto_com_apelidos,
)

_destino_pc_runtime = _criar_destino_pc_runtime_mente(
    normalizar_texto=_normalizar_texto_com_apelidos,
)
_target_from_params = _destino_pc_runtime.resolver
_limpar_destino_pc_b = _destino_pc_runtime.limpar_mencao

_memoria_visual_runtime = _criar_memoria_visual_runtime_mente(
    namespace_getter=lambda: {
        "enviar_pc_b": _enviar_pc_b,
        "capturar_tela": _capturar_tela_base64,
        "analisar_imagem": _analisar_com_groq,
        "falar": falar_com_lipsync,
        "estado_emocional": lambda: (
            _conversa_estado_get("current_emotion", "calma"),
            _conversa_estado_get("emotion_level", 1),
        ),
        "registrar_memoria": registrar_memoria_visual,
        "obter_contexto": _obter_contexto_perceptivo,
    },
    log=print,
)
_executar_captura_tela_intent = _memoria_visual_runtime.executar


_contexto_intencao_runtime = _criar_contexto_intencao_runtime_mente(
    namespace_getter=lambda: globals(),
    estado_getter=_estado_contexto_intencao,
    monitor_saude=_saude_mente_runtime,
    dependencias_tardias=(
        "abrir_programa",
        "_gmail_falar_resumo_estiloso",
        "_gmail_buscar_nao_lidos",
        "_gmail_silenciar_remetente",
        "_executar_controle_midia_nativo",
    ),
)

_ciclo_comandos_runtime = _criar_ciclo_comandos_runtime_mente(
    namespace_getter=lambda: globals(),
    contexto_intencao_runtime=_contexto_intencao_runtime,
    log=print,
    monitor_saude=_saude_mente_runtime,
    registrar_metrica_cb=_observabilidade_mente_runtime.registrar_metrica,
    registrar_falha_cb=_observabilidade_mente_runtime.registrar_falha,
    registrar_decisao_cb=_observabilidade_mente_runtime.registrar_decisao,
    dependencias_tardias=(
        "_interpretacao_intencao_runtime",
        "detectar_intencao_deterministica",
    ),
)
executar_intencao = _ciclo_comandos_runtime.executar_intencao
_executar_comando_em_texto = _ciclo_comandos_runtime.executar_texto
processar_comandos_em_cadeia = _ciclo_comandos_runtime.processar_cadeia
processar_comando_deterministico = _ciclo_comandos_runtime.processar_deterministico
_tentar_intencao_ai_primeiro = _ciclo_comandos_runtime.tentar_intencao_ai_primeiro

_musica_conversacional_runtime = _criar_musica_conversacional_runtime_mente(
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    normalizar_texto=_normalizar_texto_com_apelidos,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    registrar_mente_curta=_registrar_mente_curta,
    executar_intencao=executar_intencao,
    registrar_resultado_execucao=_registrar_resultado_execucao,
    registrar_autoaprimoramento=_registrar_autoaprimoramento,
    enviar_mensagem=enviar_mensagem,
    log=print,
)
_texto_pede_direcao_musical_generica = _musica_conversacional_runtime.texto_pede_direcao
_responder_pedido_direcao_musical_generica = _musica_conversacional_runtime.responder_pedido_direcao
_processar_confirmacao_sugestao_musical = _musica_conversacional_runtime.processar_confirmacao
_texto_pede_opiniao_musica_atual = _musica_conversacional_runtime.texto_pede_opiniao_atual
_responder_opiniao_musica_atual = _musica_conversacional_runtime.responder_opiniao_atual

ajustar_humor = _estado_contexto_runtime.ajustar_humor

_executar_controle_midia_nativo = _executar_controle_midia_nativo_mente

_coordenador_exec_runtime = _criar_coordenador_exec_runtime_mente(
    contexto_exec_getter=lambda: _contexto_exec_runtime,
    resposta_ia_getter=lambda: _resposta_ia_runtime,
    loop_getter=_ws_transport_runtime.obter_loop,
    log=print,
)
_executar_exec = _coordenador_exec_runtime.executar


abrir_programa = _abrir_programa_mente
filtrar_apenas_fala = partial(_filtrar_apenas_fala_mente, historico=None, fallback_fala=FALLBACK_FALA_NEUTRA)

limpar_diccao_e_ruido = _limpar_diccao_e_ruido_mente


get_status_humor_prompt = _estado_contexto_runtime.status_humor_prompt

parsear_resposta_json = partial(_parsear_resposta_json_mente, fallback_fala=FALLBACK_FALA_NEUTRA)
gerar_resposta_exec_ia = _coordenador_exec_runtime.agendar

_barra_comando_runtime = _criar_barra_comando_runtime_mente(
    processar_texto=gerar_resposta_exec_ia,
    keyboard_mod=keyboard,
    hotkey=HOTKEY_BARRA_COMANDO,
    log=print,
)
registrar_hotkey_barra_comando = _barra_comando_runtime.registrar_hotkey


_pronuncias_aprendidas_voz = _adaptadores_aplicacao_runtime.pronuncias_aprendidas_voz
_salvar_pronuncia_voz = _adaptadores_aplicacao_runtime.salvar_pronuncia_voz
_vocabulario_dinamico_voz = _adaptadores_aplicacao_runtime.vocabulario_dinamico_voz


_reconhecedor_voz_pessoal = _ReconhecedorVozPessoal(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados", "voz_pessoal"),
    log=print,
)

_ouvido_whisper_runtime = _criar_ouvido_whisper_runtime_mente(
    processar_texto=gerar_resposta_exec_ia,
    esta_falando=lambda: bool(_conversa_estado_get("is_speaking", False)),
    escuta_permitida=lambda: not bool(
        _conversa_estado_get("modo_chat", False)
        or _conversa_estado_get("conversa_ativa", False)
    ),
    modo_jogo_ativo=lambda: bool(_modo_jogo_runtime.ativo),
    ultima_fala_laylay=lambda: str(_estado_compartilhado_runtime.mental.get("ultima_resposta") or ""),
    vocabulario_dinamico=_vocabulario_dinamico_voz,
    pronuncias_aprendidas=_pronuncias_aprendidas_voz,
    salvar_pronuncia=_salvar_pronuncia_voz,
    reconhecer_comando_pessoal=_reconhecedor_voz_pessoal.reconhecer,
    solicitar_confirmacao=falar_com_lipsync,
    sounddevice_mod=sd,
    limpar_texto=limpar_diccao_e_ruido,
    log=print,
)

_interacao_chat_runtime = _criar_interacao_chat_runtime_mente(
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
    modo_chat_runtime_getter=lambda: _modo_chat_runtime,
    abertura_runtime_getter=lambda: _abertura_chat_runtime,
    processar_texto=gerar_resposta_exec_ia,
    escutar_terminal=_escutar_texto_terminal_mente,
    keyboard_mod=keyboard,
    hotkey_liga=HOTKEY_MODO_CHAT_LIGA,
    hotkey_desliga=HOTKEY_MODO_CHAT_DESLIGA,
    stdin_getter=lambda: getattr(sys, "stdin", None),
    raw_print=_RAW_PRINT,
    print_lock=_PRINT_LOCK,
    log=print,
)
_atualizar_estado_modo_chat = _interacao_chat_runtime.atualizar_estado
_definir_modo_chat = _interacao_chat_runtime.definir
_gerar_abertura_modo_chat = _interacao_chat_runtime.gerar_abertura
_alternar_modo_chat_por_hotkey = _interacao_chat_runtime.alternar_por_hotkey
registrar_hotkeys_modo_chat = _interacao_chat_runtime.registrar_hotkeys
_escutar_texto_do_chat_terminal = _interacao_chat_runtime.escutar_terminal
_definir_messages_resposta_ia = _interacao_chat_runtime.definir_messages


_interpretacao_intencao_runtime = _criar_interpretacao_intencao_runtime_mente(
    contexto_getter=lambda: {
        "estado": {
            "messages": _memoria_conversa_get("messages", []),
            "mente_integrada_estado": _estado_compartilhado_runtime.mental,
            "playlist_state": playlist_state,
            "playlists_carregadas": _playlist_runtime.cache,
        },
        "normalizar_texto": _normalizar_texto_com_apelidos,
        "texto_cancela_acao_agora": _texto_cancela_acao_agora,
        "texto_bloqueia_playlist_agora": _texto_bloqueia_playlist_agora,
        "texto_social_curto": _texto_social_curto,
        "texto_conversa_casual_sem_acao": _texto_conversa_casual_sem_acao,
        "texto_conversa_contextual_sem_comando": _texto_conversa_contextual_sem_comando,
        "texto_tem_comando_explicito": _texto_tem_comando_explicito,
        "texto_pede_direcao_musical_generica": _texto_pede_direcao_musical_generica,
        "texto_expresso_melhor_no_deterministico": _texto_expresso_melhor_no_deterministico,
        "texto_depende_de_contexto": _texto_depende_de_contexto,
        "texto_parece_navegacao_ou_janela_ia": _texto_parece_navegacao_ou_janela_ia,
        "fluxo_prioritario_da_ia": _fluxo_prioritario_da_ia,
        "contexto_mental_ativo": _contexto_mental_ativo,
        "musica_estado_get": _musica_estado_get,
        "resumo_mente_integrada_para_prompt": _resumo_mente_integrada_para_prompt,
        "resumo_autoaprimoramento_para_prompt": _resumo_autoaprimoramento_para_prompt,
        "resumo_agendamentos_para_prompt": _resumo_agendamentos_para_prompt,
        "enviar_mensagem": enviar_mensagem,
        "extrair_json_da_ia": _extrair_json_da_ia,
        "playlist_bloqueada_agora": _playlist_bloqueada_agora,
        "texto_pede_playlist_explicitamente": _texto_pede_playlist_explicitamente,
    },
    log=print,
)


_abertura_chat_runtime = _criar_abertura_chat_runtime_mente(
    estado_getter=lambda: {
        "messages": _memoria_conversa_get("messages", []),
        "current_emotion": _conversa_estado_get("current_emotion", "calma"),
        "emotion_level": _conversa_estado_get("emotion_level", 1),
    },
    enviar_mensagem=enviar_mensagem,
    limpar_resposta=limpar_resposta,
    remover_prefixo_exec=_remover_prefixo_exec,
    log=print,
)


_modo_chat_runtime = _criar_modo_chat_runtime_mente(
    estado_getter=lambda: {
        "modo_chat": _conversa_estado_get("modo_chat", False),
        "conversa_ativa": _conversa_estado_get("conversa_ativa", False),
    },
    estado_setter=_atualizar_estado_modo_chat,
    messages_getter=lambda: _memoria_conversa_get("messages", []),
    fala_confirmacao=_fala_de_confirmacao_variada,
    gerar_abertura=_gerar_abertura_modo_chat,
    falar=falar_com_lipsync,
    salvar_memoria=salvar_memoria,
    iniciar_sessao=_renovar_sessao_conversa,
    encerrar_sessao=_renovar_sessao_conversa,
    deve_emitir_fala=lambda ativo: (
        not ativo
        or time.time() - float(_estado_compartilhado_runtime.mental.get("ultima_fala_emitida_ts") or 0.0) >= 15.0
    ),
    log=print,
)
analisar_intencao = _interpretacao_intencao_runtime.analisar


            # ====================== GMAIL IMAP — RUNTIME ======================

_gmail_runtime = criar_gmail_runtime(
    arquivo_estado=GMAIL_ARQUIVO,
    usuario=GMAIL_USER,
    app_password=GMAIL_APP_PASSWORD,
    intervalo_s=GMAIL_INTERVALO_S,
    max_lidos=GMAIL_MAX_LIDOS,
    prioritarios=GMAIL_PRIORITARIOS,
    palavras_urgentes=GMAIL_PALAVRAS_URGENTES,
    continuidades_set=_continuidades_set,
    agendar_fala_proativa=_agendar_fala_proativa,
    is_speaking_getter=lambda: bool(_conversa_estado_get("is_speaking", False)),
    modo_jogo_getter=lambda: bool(_modo_jogo_runtime.ativo),
)
_gmail_nao_lidos_cache = _gmail_runtime.nao_lidos_cache
_gmail_silenciar_remetente = _gmail_runtime.silenciar_remetente
_gmail_buscar_nao_lidos = _gmail_runtime.buscar_nao_lidos
_gmail_falar_resumo_estiloso = _gmail_runtime.falar_resumo_estiloso
gmail_daemon = _gmail_runtime.daemon

_contexto_prompt_runtime = _criar_contexto_prompt_runtime_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    resumo_mente_integrada=_resumo_mente_integrada_para_prompt,
    formatar_playlists=_formatar_playlists_para_prompt,
    get_status_humor_prompt=get_status_humor_prompt,
    base_system_prompt=BASE_SYSTEM_PROMPT,
    estado_getter=lambda: {
        "messages": _memoria_conversa_get("messages", []),
        "humor_level": _conversa_estado_get("humor_level", 0),
        "aba_titulo_atual": _chrome_estado.aba_titulo_atual,
        "aba_url_atual": _chrome_estado.aba_url_atual,
        "turno_atual": dict(_estado_compartilhado_runtime.mental.get("turno_atual") or {}),
    },
)

_contexto_exec_runtime = _criar_contexto_exec_runtime_mente(
    contexto_getter=lambda: {
        "enviar_comando_chrome": enviar_comando_chrome,
        "validar_e_enviar_comando": validar_e_enviar_comando,
        "ajustar_volume_sistema": ajustar_volume_sistema,
        "falar_com_lipsync": falar_com_lipsync,
        "play_playlist": play_playlist,
        "_playlist_shuffle_start": _playlist_shuffle_start,
        "solicitar_aba_ativa": solicitar_aba_ativa,
        "abrir_programa": abrir_programa,
        "fechar_programa": fechar_programa,
        "APPS_MAP": APPS_MAP,
        "ADD_TO_PLAYLIST": ADD_TO_PLAYLIST,
        "set_ultima_playlist": lambda valor: _musica_estado_set("ultima_playlist", valor),
        "ativar_tela_cheia_robusta": ativar_tela_cheia_robusta,
        "_eh_alvo_site_web": _eh_alvo_site_web,
        "_contexto_aponta_site_web": _contexto_aponta_site_web,
        "is_valid_url": is_valid_url,
        "formatar_url_ou_busca": formatar_url_ou_busca,
        "_listar_playlists_salvas": _listar_playlists_salvas,
        "_autorizar_acao_pratica": _autorizar_acao_pratica,
    },
    executar_conteudo_cb=_executar_comando_conteudo_mente,
    executar_legado_cb=_executar_exec_mente,
    log=print,
)

_contexto_dispatcher_runtime = _criar_contexto_dispatcher_runtime_mente(
    base={
        "falar_com_lipsync": falar_com_lipsync,
        "salvar_memoria": salvar_memoria,
    },
    navegacao={
        "enviar_comando_chrome": enviar_comando_chrome,
        "_enviar_pc_b": _enviar_pc_b,
        "interpretar_comando_local_rapido": interpretar_comando_local_rapido,
        "solicitar_aba_ativa": solicitar_aba_ativa,
        "listar_abas_chrome": listar_abas_chrome,
        "listar_programas_abertos": listar_programas_abertos,
        "organizar_janelas_robusto": organizar_janelas_robusto,
        "ativar_tela_cheia_robusta": ativar_tela_cheia_robusta,
    },
    musica={
        "_normalizar_query_musical": _normalizar_query_musical,
        "_limpar_nome_playlist": _limpar_nome_playlist,
        "_playlist_shuffle_start": _playlist_shuffle_start,
        "_buscar_primeiro_video_youtube": _buscar_primeiro_video_youtube,
        "add_to_playlist_url": add_to_playlist_url,
        "_playlists_load": _playlists_load,
    },
    arquivos={
        "executar_intencao": executar_intencao,
    },
    percepcao={
        "_executar_captura_tela_intent": lambda destino: _executar_captura_tela_intent(
            destino, registrar_memoria=True
        ),
    },
    agenda_email={
        "_agendamentos_load": _agendamentos_load,
        "_agendamentos_save": _agendamentos_save,
        "_agendamentos_transacionar": _agendamentos_transacionar,
        "_gmail_buscar_nao_lidos": _gmail_buscar_nao_lidos,
        "_gmail_falar_resumo_estiloso": _gmail_falar_resumo_estiloso,
    },
    execucao={
        "_executar_fechar_abas_paradas": _executar_fechar_abas_paradas,
        "_executar_exec": _executar_exec,
        "processar_comando_deterministico": processar_comando_deterministico,
    },
    autonomia={
        "_autorizar_acao_pratica": _autorizar_acao_pratica,
        "_autonomia_permite_execucao_musical": _autonomia_permite_execucao_musical,
    },
    estado_getter=lambda: {
        "messages": _memoria_conversa_get("messages", []),
        "current_emotion": _conversa_estado_get("current_emotion", "calma"),
        "emotion_level": _conversa_estado_get("emotion_level", 1),
        "playlists_carregadas": _playlist_runtime.cache,
        "_gmail_nao_lidos_cache": _gmail_nao_lidos_cache,
    },
)

_contexto_finalizacao_runtime = _criar_contexto_finalizacao_runtime_mente(
    ia={
        "enviar_mensagem": enviar_mensagem,
        "limpar_resposta_da_ia": limpar_resposta_da_ia,
    },
    voz_memoria={
        "falar_com_lipsync": falar_com_lipsync,
        "salvar_memoria": salvar_memoria,
        "verificar_fala_turno": lambda fala, origem="ia_final": _verificar_fala_do_turno(
            fala, origem=origem
        ),
    },
    autoaprimoramento={
        "_registrar_autoaprimoramento": _registrar_autoaprimoramento,
        "_registrar_autocorrecao_virtual": _registrar_autocorrecao_virtual,
        "MAX_TENTATIVAS_AUTOCORRECAO": MAX_TENTATIVAS_AUTOCORRECAO,
    },
    estado_getter=lambda: {
        "messages": _memoria_conversa_get("messages", []),
        "current_emotion": _conversa_estado_get("current_emotion", "calma"),
        "emotion_level": _conversa_estado_get("emotion_level", 1),
        "_falhas_consecutivas": _falhas_consecutivas,
    },
)


_deteccao_deterministica_runtime = _criar_deteccao_deterministica_runtime_mente(
    namespace_getter=lambda: globals(),
    estado_getter=lambda: _estado_compartilhado_runtime.mental,
    sites_diretos=SITES_DIRECTOS,
    apps_map=APPS_MAP,
)
detectar_intencao_deterministica = _deteccao_deterministica_runtime.detectar

_diagnostico_mente_runtime = _criar_diagnostico_mente_runtime(
    estado_getter=_estado_compartilhado_runtime.snapshot,
    saude_getter=lambda: (
        _auditar_saude_mente(),
        _saude_mente_runtime.snapshot(),
    )[1],
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    log=print,
)
_mostrar_diagnostico_mente = _diagnostico_mente_runtime.mostrar

_comandos_imediatos_runtime = _criar_comandos_imediatos_runtime_mente(
    namespace_getter=lambda: globals(),
    loop_getter=_ws_transport_runtime.obter_loop,
)
processar_comandos_imediatos = _comandos_imediatos_runtime.processar
_processar_comandos_prioritarios = _comandos_imediatos_runtime.processar_prioritarios

_contexto_inicio_chat_runtime = _criar_contexto_inicio_chat_runtime_mente(
    namespace_getter=lambda: globals(),
    estado_getter=lambda: {
        "messages": _memoria_conversa_get("messages", []),
        "current_emotion": _conversa_estado_get("current_emotion", "calma"),
        "emotion_level": _conversa_estado_get("emotion_level", 1),
    },
    memoria_sqlite=MEMORIA_SQLITE,
)
_contexto_inicio_chat = _contexto_inicio_chat_runtime.montar


_iniciar_planejamento_turno = partial(
    _iniciar_planejamento_turno_mente_runtime, lambda: globals(),
)


_atualizar_planejamento_turno = partial(
    _atualizar_planejamento_turno_mente_runtime, lambda: globals(),
)


_verificar_fala_do_turno = partial(
    _verificar_fala_do_turno_mente_runtime, lambda: globals(),
)


_registrar_leitura_semantica_principal = partial(
    _registrar_leitura_semantica_principal_mente_runtime, lambda: globals(),
)


_resposta_ia_runtime = _criar_resposta_ia_runtime_mente(
    contexto_getter=lambda: {
        "iniciar_turno_voz": _voz_runtime.iniciar_turno_resposta,
        "finalizar_turno_voz": _voz_runtime.finalizar_turno_resposta,
        "sincronizar_turno_voz": _voz_runtime.sincronizar_chave_turno_resposta,
        "marcar_inicio_turno": _iniciar_planejamento_turno,
        "obter_turno_atual": lambda: dict(
            _estado_compartilhado_runtime.mental.get("turno_atual") or {}
        ),
        "modo_chat_runtime": _modo_chat_runtime,
        "processar_comandos_prioritarios": _processar_comandos_prioritarios,
        "modo_chat": _conversa_estado_get("modo_chat", False),
        "conversa_ativa": _conversa_estado_get("conversa_ativa", False),
        "contexto_inicio": _contexto_inicio_chat,
        "processar_inicio_fluxo": _processar_inicio_fluxo_resposta_ia_mente,
        "usar_modo_rapido": _usar_modo_rapido_conversa,
        "processar_comandos_imediatos": processar_comandos_imediatos,
        "processar_pre_fluxos": _processar_pre_fluxos_antes_ia_mente,
        "contexto_prompt_runtime": _contexto_prompt_runtime,
        "get_messages": lambda: _memoria_conversa_get("messages", []),
        "set_messages": _definir_messages_resposta_ia,
        "enviar_mensagem": enviar_mensagem,
        "fallback_fala": FALLBACK_FALA_NEUTRA,
        "preparar_resposta": lambda texto, resposta_bruta: _preparar_resposta_para_execucao_mente(
            texto,
            resposta_bruta,
            enviar_mensagem_cb=enviar_mensagem,
            limpar_texto_fala_cb=_limpar_texto_fala_ia,
            fallback_fala=FALLBACK_FALA_NEUTRA,
            construir_fala_cb=_construir_fala_conversa,
            memoria_sqlite=MEMORIA_SQLITE,
            registrar_autocorrecao_cb=_registrar_autocorrecao_virtual,
            log=print,
        ),
        "registrar_leitura_semantica_principal": _registrar_leitura_semantica_principal,
        "validar_comandos_planejados": lambda comandos: _filtrar_comandos_pelo_turno_mente(
            comandos,
            turno=dict(_estado_compartilhado_runtime.mental.get("turno_atual") or {}),
            plano=dict(_estado_compartilhado_runtime.mental.get("plano_turno_atual") or {}),
            retrato=dict(_estado_compartilhado_runtime.mental.get("retrato_turno_atual") or {}),
        ),
        "atualizar_plano_turno": _atualizar_planejamento_turno,
        "atualizar_memoria_topicos": _atualizar_memoria_topicos,
        "processar_comando_deterministico": processar_comando_deterministico,
        "contexto_dispatch_runtime": _contexto_dispatcher_runtime,
        "executar_comandos_json": _executar_comandos_json_mente,
        "contexto_finalizacao_runtime": _contexto_finalizacao_runtime,
        "finalizar_execucao": _finalizar_execucao_resposta_ia_mente,
        "registrar_metrica_diagnostico": _observabilidade_mente_runtime.registrar_metrica,
        "registrar_falha_diagnostico": _observabilidade_mente_runtime.registrar_falha,
        "registrar_decisao_diagnostico": _observabilidade_mente_runtime.registrar_decisao,
    },
    log=print,
)


# ====================== FIM DAS FUNÇÕES GMAIL ======================

_auditar_saude_mente = _adaptadores_aplicacao_runtime.auditar_saude_mente


def _encerrar_laylay() -> None:
    try:
        salvar_memoria()
    finally:
        _avatar_runtime.parar()

def main():
    """Ponto de entrada principal da Laylay."""
    _auditar_saude_mente()
    _inicializacao_runtime.iniciar(
        etapas={
            "carregar memória": carregar_memoria,
            "iniciar nova sessão conversacional": lambda: _renovar_sessao_conversa("inicio_programa", True),
            "iniciar memória de contexto diária": init_memoria_contexto_diaria,
            "carregar playlists": _carregar_playlists_para_memoria,
            "iniciar worker de falas": _iniciar_worker_de_falas,
            "iniciar avatar": _avatar_runtime.iniciar,
        },
        threads={
            "Laylay-WS": run_ws_server_in_thread,
            "Laylay-Gmail": gmail_daemon,
            "Laylay-Agenda": _agenda_daemon,
            "Laylay-Rotina": monitor_rotina_daemon,
            "Laylay-Porteiro": _porteiro_daemon,
            "Laylay-Saude": _monitor_saude_daemon,
            "Laylay-Monitor-Janelas": _monitor_janelas_runtime.executar,
            "Laylay-Ritmo-Circadiano": _ritmo_circadiano_runtime.executar,
            "Laylay-Consciência-Temporal": _motor_temporal_runtime.executar,
            "Laylay-Aprendizado": _motor_aprendizado_runtime.executar,
            "Laylay-Ouvido": _ouvido_whisper_runtime.executar,
        },
        hotkeys=None,
    )
    briefing_pendente = carregar_estado_briefing() != time.strftime("%Y-%m-%d")
    if briefing_pendente:
        fala_inicial_entregue = briefing_matinal()
    else:
        abertura_inicial = _abertura_chat_runtime.gerar("inicio")
        fala_inicial_entregue = _entregar_fala_inicial_confirmada(
            "abertura", abertura_inicial, "calma", 1
        )
    if not fala_inicial_entregue:
        abertura_fallback = _abertura_chat_runtime.gerar("inicio")
        print(f"╭─ ◕‿◕ Laylay: {abertura_fallback}")
    registrar_hotkeys_modo_chat()
    registrar_hotkey_barra_comando()
    _servicos_background_runtime.iniciar(
        "Laylay-Chat-Terminal",
        _escutar_texto_do_chat_terminal,
    )
    _inicializacao_runtime.manter_ativo(
        fala_pronta="",
        ao_encerrar=_encerrar_laylay,
    )
if __name__ == "__main__":
    main()
