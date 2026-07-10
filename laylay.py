import sys
import io
# Forca UTF-8 no terminal Windows para evitar UnicodeEncodeError
try:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import time
import psutil
import unicodedata
FECHAR_PROGRAMA_SOMENTE_EXPLICITO = False
import requests
import json
import os
import shutil
import keyboard
from functools import partial
import threading as _threading
import builtins as _builtins
import re
from typing import Optional
from mente_laylay.autonomia.comandos_sistema import (
    abrir_programa as _abrir_programa_mente,
    buscar_executavel as _buscar_executavel_mente,
    fechar_programa as _fechar_programa_mente,
    normalizar_nome_app as _normalizar_nome_app_mente,
)
from mente_laylay.autonomia.coordenador_intencao import (
    executar_fluxo_intencao as _executar_fluxo_intencao_mente,
)
from mente_laylay.cognicao.interpretacao_intencao import (
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
    verificar_trava_seguranca as _verificar_trava_seguranca_mente,
)
from mente_laylay.memoria_mental.contexto_integrado import (
    contexto_aponta_descanso as _contexto_aponta_descanso_mente,
    interpretar_contexto_vivo as _interpretar_contexto_vivo_mente,
    montar_contexto_perceptivo as _montar_contexto_perceptivo_mente,
    montar_resumo_mente_integrada_com_extras as _montar_resumo_mente_integrada_com_extras_mente,
    resumo_mente_integrada_para_prompt as _resumo_mente_integrada_para_prompt_mente,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    alvo_corrigido_ativo as _alvo_corrigido_ativo_mente,
    contexto_mental_ativo as _contexto_mental_ativo_mente,
    contexto_musical_ativo as _contexto_musical_ativo_mente,
    estado_mental_inicial as _estado_mental_inicial_mente,
    enriquecer_resultado_execucao_contextual as _enriquecer_resultado_execucao_contextual_mente,
    extrair_refino_contexto_mental as _extrair_refino_contexto_mental_mente,
    estrutura_arquivo_recente as _estrutura_arquivo_recente_mente,
    atualizar_foco_vivo as _atualizar_foco_vivo_mente,
    foco_vivo_atual as _foco_vivo_atual_mente,
    fluxo_prioritario_da_ia as _fluxo_prioritario_da_ia_mente,
    limpar_pergunta_aberta as _limpar_pergunta_aberta_mente,
    pergunta_aberta_ativa as _pergunta_aberta_ativa_mente,
    registrar_alvo_corrigido as _registrar_alvo_corrigido_mente,
    registrar_estrutura_arquivo_recente as _registrar_estrutura_arquivo_recente_mente,
    registrar_promessa_conversacional as _registrar_promessa_conversacional_mente,
    registrar_mente_curta as _registrar_mente_curta_mente,
    registrar_resultado_execucao as _registrar_resultado_execucao_mente,
    registrar_pergunta_aberta as _registrar_pergunta_aberta_mente,
    resolver_repeticao_ultima_acao as _resolver_repeticao_ultima_acao_mente,
    texto_depende_de_contexto as _texto_depende_de_contexto_mente,
    texto_parece_resposta_curta_a_pergunta as _texto_parece_resposta_curta_a_pergunta_mente,
    texto_parece_pergunta_aberta as _texto_parece_pergunta_aberta_mente,
)
from mente_laylay.memoria_mental.contexto_imediato import (
    extrair_app_explicito_em_comando_janela as _extrair_app_explicito_em_comando_janela_mente,
    fala_contexto_janela_indisponivel as _fala_contexto_janela_indisponivel_mente,
    resolver_comando_contextual as _resolver_comando_contextual_mente,
    referencia_contextual_imediata as _referencia_contextual_imediata_mente,
    resolver_comando_acao_geral_contextual as _resolver_comando_acao_geral_contextual_mente,
    resolver_comando_arquivo_contextual as _resolver_comando_arquivo_contextual_mente,
    resolver_comando_janela_contextual as _resolver_comando_janela_contextual_mente,
    resolver_comando_midia_contextual as _resolver_comando_midia_contextual_mente,
)
from mente_laylay.memoria_mental.estado_continuidades import (
    atualizar_continuidades as _atualizar_continuidades_mente,
    estado_continuidades_inicial as _estado_continuidades_inicial_mente,
    limpar_sugestao_atual as _limpar_sugestao_atual_mente,
)
from mente_laylay.memoria_mental.estado_musical import (
    atualizar_estado_musical as _atualizar_estado_musical_mente,
    bloquear_playlist_temporariamente as _bloquear_playlist_temporariamente_mente,
    estado_musical_inicial as _estado_musical_inicial_mente,
    playlist_bloqueada_agora as _playlist_bloqueada_agora_mente,
)
from mente_laylay.memoria_mental.estado_percepcao import (
    atualizar_estado_percepcao as _atualizar_estado_percepcao_mente,
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
    obter_janelas_abertas as _obter_janelas_abertas_mente,
    pid_from_hwnd as _pid_from_hwnd_mente,
    organizar_janelas as _organizar_janelas_mente,
    resolver_alvo_ambiente as _resolver_alvo_ambiente_mente,
)
from mente_laylay.percepcao.monitor_janelas import (
    criar_monitor_janelas_runtime as _criar_monitor_janelas_runtime_mente,
)
from mente_laylay.percepcao.ouvido_whisper import (
    limpar_diccao_e_ruido as _limpar_diccao_e_ruido_mente,
    transcrever_com_whisper as _transcrever_com_whisper_mente,
)
from mente_laylay.percepcao.alvos_web import (
    contexto_aponta_site_web as _contexto_aponta_site_web_mente,
    contexto_navegador_relevante as _contexto_navegador_relevante_mente,
    eh_alvo_site_web as _eh_alvo_site_web_mente,
)
from mente_laylay.percepcao.contexto_paginas import ContextoPaginas
from mente_laylay.percepcao.ambiente_sistema import (
    carregar_estado_briefing as _carregar_estado_briefing_ambiente,
    detectar_comando_saude as _detectar_comando_saude_ambiente,
    detectar_repetir_briefing as _detectar_repetir_briefing_ambiente,
    identificar_processo_culpado as _identificar_processo_culpado_ambiente,
    monitor_saude_daemon as _monitor_saude_daemon_ambiente,
    montar_briefing_matinal as _montar_briefing_matinal_ambiente,
    montar_status_saude as _montar_status_saude_ambiente,
    obter_clima_localidade as _obter_clima_localidade_ambiente,
    obter_clima_wttr as _obter_clima_wttr_ambiente,
    obter_temperatura_cpu as _obter_temperatura_cpu_ambiente,
    repetir_briefing as _repetir_briefing_ambiente,
    salvar_estado_briefing as _salvar_estado_briefing_ambiente,
)
from mente_laylay.memoria_mental.persistencia_memoria import (
    carregar_memoria as _carregar_memoria_mente,
    init_memoria_contexto_diaria as _init_memoria_contexto_diaria_mente,
    registrar_autocorrecao_virtual as _registrar_autocorrecao_virtual_mente,
    salvar_memoria as _salvar_memoria_mente,
)
from mente_laylay.memoria_mental.autoaprimoramento import (
    registrar_autoaprimoramento as _registrar_autoaprimoramento_mente,
    resumo_autoaprimoramento_para_prompt as _resumo_autoaprimoramento_para_prompt_mente,
)
from mente_laylay.memoria_mental.aprendizado_runtime import (
    criar_aprendizado_runtime as _criar_aprendizado_runtime_mente,
)
from mente_laylay.memoria_mental.playlist_mental import (
    canal_fingerprint as _canal_fingerprint_mente,
    detectar_mover_playlist_texto as _detectar_mover_playlist_texto_mente,
    extrair_nome_playlist as _extrair_nome_playlist_mente,
    fala_playlist_conteudo_estilosa as _fala_playlist_conteudo_estilosa_mente,
    limpar_nome_playlist as _limpar_nome_playlist_mente,
    parse_indice_ordinal as _parse_indice_ordinal_mente,
    pedido_lista_geral_playlist as _pedido_lista_geral_playlist_mente,
    playlist_item_label as _playlist_item_label_mente,
    playlist_item_match as _playlist_item_match_mente,
    playlist_nome_explicito_na_frase as _playlist_nome_explicito_na_frase_mente,
    sim_ratio as _sim_ratio_mente,
    titulo_fingerprint as _titulo_fingerprint_mente,
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
from mente_laylay.memoria_mental.continuidade_conversa import (
    atualizar_memoria_topicos as _atualizar_memoria_topicos_mente,
    responder_pergunta_aberta as _responder_pergunta_aberta_continuidade_mente,
    resolver_pergunta_curta_contextual_intencao as _resolver_pergunta_curta_contextual_intencao_continuidade_mente,
    texto_responde_pergunta_aberta as _texto_responde_pergunta_aberta_continuidade_mente,
)
from mente_laylay.personalidade.falas_variadas import (
    escolher as _escolher_fala_variada,
    fala_de_confirmacao as _fala_de_confirmacao_variada,
    fala_falha_contextual as _fala_falha_contextual_variada,
)
from mente_laylay.personalidade.falas_playlist import (
    fala_playlist_duplicado as _fala_playlist_duplicado_mente,
    fala_playlist_duplicado_meta as _fala_playlist_duplicado_meta_mente,
    fala_playlist_sucesso as _fala_playlist_sucesso_mente,
)
from mente_laylay.personalidade.terminal_laylay import (
    formatar_mensagem_laylay as _formatar_mensagem_laylay_mente,
    should_log_message as _should_log_message_mente,
)
from mente_laylay.personalidade.ajuste_contextual import (
    ajustar_fala_por_horario as _ajustar_fala_por_horario_mente,
)
from mente_laylay.personalidade.fala_proativa import (
    compor_fala_proativa as _compor_fala_proativa_mente,
)
from mente_laylay.personalidade.voz_runtime import (
    criar_voz_runtime as _criar_voz_runtime_mente,
)
from mente_laylay.personalidade.abertura_chat import (
    criar_abertura_chat_runtime as _criar_abertura_chat_runtime_mente,
)
from mente_laylay.personalidade.conversa_natural import (
    construir_fala_conversa as _construir_fala_conversa_mente,
    contexto_recente_indica_email as _contexto_recente_indica_email_mente,
    fala_e_fallback_neutro as _fala_e_fallback_neutro_mente,
    parece_elogio_ou_agradecimento_curto as _parece_elogio_ou_agradecimento_curto_mente,
    responder_agradecimento_ou_elogio as _responder_agradecimento_ou_elogio_mente,
    responder_conversa_curta_por_tipo as _responder_conversa_curta_por_tipo_mente,
    resposta_conversa_local as _resposta_conversa_local_mente,
    resposta_conversa_rapida_local as _resposta_conversa_rapida_local_mente,
)
from mente_laylay.autonomia.execucao_ia import (
    criar_contexto_exec_runtime as _criar_contexto_exec_runtime_mente,
    executar_exec as _executar_exec_mente,
    filtrar_apenas_fala as _filtrar_apenas_fala_mente,
    parsear_resposta_json as _parsear_resposta_json_mente,
    processar_comando_ia as _processar_comando_ia_mente,
)
from mente_laylay.autonomia.processamento_resposta_ia import (
    extrair_aprendizados_da_ia as _extrair_aprendizados_da_ia_mente,
    extrair_tipo_interacao_da_ia as _extrair_tipo_interacao_da_ia_mente,
    limpar_resposta_da_ia as _limpar_resposta_da_ia_mente,
    preparar_resposta_para_execucao as _preparar_resposta_para_execucao_mente,
    salvar_aprendizados_da_ia as _salvar_aprendizados_da_ia_mente,
)
from mente_laylay.autonomia.controle_midia import (
    executar_controle_midia_nativo as _executar_controle_midia_nativo_mente,
)
from mente_laylay.autonomia.audio_sistema import (
    ajustar_volume_sistema as _ajustar_volume_sistema_mente,
    ajustar_volume_sistema_relativo as _ajustar_volume_sistema_relativo_mente,
    ducking_volume as _ducking_volume_mente,
    interromper_audio_ativo as _interromper_audio_ativo_mente,
)
from mente_laylay.autonomia.fluxo_resposta_ia import (
    processar_inicio_fluxo_resposta_ia as _processar_inicio_fluxo_resposta_ia_mente,
    processar_pre_fluxos_antes_ia as _processar_pre_fluxos_antes_ia_mente,
)
from mente_laylay.autonomia.modo_chat import (
    criar_modo_chat_runtime as _criar_modo_chat_runtime_mente,
)
from mente_laylay.autonomia.servicos_background import (
    criar_gerenciador_servicos_background as _criar_gerenciador_servicos_background_mente,
)
from mente_laylay.autonomia.pre_fluxo_contextual import (
    analisar_intencao_com_porteiro as _analisar_intencao_com_porteiro_mente,
)
from mente_laylay.autonomia.contexto_resposta_ia import (
    criar_contexto_prompt_runtime as _criar_contexto_prompt_runtime_mente,
    montar_prompt_contextual_legado as _montar_prompt_contextual_legado_mente,
)
from mente_laylay.integracao.contexto_conversa import (
    montar_contexto_conversa_natural as _montar_contexto_conversa_natural_mente,
    montar_contexto_gate_conversa as _montar_contexto_gate_conversa_mente,
    montar_contexto_inicio_chat_por_grupos as _montar_contexto_inicio_chat_por_grupos_mente,
)
from mente_laylay.integracao.contexto_execucao_ia import (
    criar_contexto_dispatcher_runtime as _criar_contexto_dispatcher_runtime_mente,
    criar_contexto_finalizacao_runtime as _criar_contexto_finalizacao_runtime_mente,
)
from mente_laylay.integracao.llm_http import (
    endpoint_eh_local as _llm_endpoint_eh_local_mente,
    post_chat_llm as _post_chat_llm_mente,
)
from mente_laylay.integracao.chrome_comandos import (
    validar_e_enviar_comando as _validar_e_enviar_comando_chrome_mente,
)
from mente_laylay.integracao.pc_b_integracao import (
    processar_mensagem_pc_b as _processar_mensagem_pc_b_mente,
)
from mente_laylay.integracao.chrome_page_data import (
    processar_page_data as _processar_page_data_chrome_mente,
)
from mente_laylay.integracao.chrome_ws_transport import (
    ChromeSolicitacoesRuntime as _ChromeSolicitacoesRuntime,
    broadcast_command as _broadcast_command_chrome_mente,
)
from mente_laylay.integracao.chrome_navegacao import (
    abrir_url_reutilizando_aba as _abrir_url_reutilizando_aba_chrome_mente,
    classificar_contexto_por_url as _classificar_contexto_por_url_chrome_mente,
    fechar_aba_ativa_nativa as _fechar_aba_ativa_nativa_chrome_mente,
    formatar_url_ou_busca as _formatar_url_ou_busca_chrome_mente,
    is_valid_url as _is_valid_url_chrome_mente,
    trazer_chrome_para_frente as _trazer_chrome_para_frente_chrome_mente,
)
from mente_laylay.integracao.chrome_estado import (
    ChromeEstadoRuntime as _ChromeEstadoRuntime,
)
from mente_laylay.integracao.chrome_ws_server import (
    run_ws_server_in_thread as _run_ws_server_in_thread_chrome_mente,
    start_ws_server as _start_ws_server_chrome_mente,
    ws_handler_modular as _ws_handler_chrome_mente,
)
from mente_laylay.integracao.chrome_ws_handlers import (
    dispatch_event as _ws_dispatch_event_mente,
    handle_action as _ws_handle_action_mente,
    handle_active_tab_url as _ws_handle_active_tab_url_mente,
    handle_check_tabs_result as _ws_handle_check_tabs_result_mente,
    handle_page_content as _ws_handle_page_content_mente,
    handle_player_event as _ws_handle_player_event_mente,
    handle_tabs_list as _ws_handle_tabs_list_mente,
    handle_user_context as _ws_handle_user_context_mente,
    handle_youtube_data as _ws_handle_youtube_data_mente,
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
from mente_laylay.cognicao.normalizacao_linguagem import (
    aplicar_correcao_fonetica as _aplicar_correcao_fonetica_mente,
    normalizar_texto as _normalizar_texto_mente,
    remover_acentos as _remover_acentos_mente,
)
from mente_laylay.cognicao.linguagem_aprendida import (
    criar_linguagem_aprendida_runtime as _criar_linguagem_aprendida_runtime_mente,
)
from mente_laylay.autonomia.dispatcher_comandos_json import (
    executar_comandos_json as _executar_comandos_json_mente,
)
from mente_laylay.autonomia.fluxos_conversa import (
    handle_feedback_pendente as _handle_feedback_pendente_mente,
    usar_modo_rapido_conversa as _usar_modo_rapido_conversa_mente,
)
from mente_laylay.autonomia.comandos_imediatos import (
    processar_comandos_imediatos as _processar_comandos_imediatos_mente,
)
from mente_laylay.autonomia.analise_comandos import (
    executar_comando_em_texto as _executar_comando_em_texto_mente,
    limpar_resposta as _limpar_resposta_mente,
    processar_comandos_em_cadeia as _processar_comandos_em_cadeia_mente,
    segmentar_comandos_em_cadeia as _segmentar_comandos_em_cadeia_mente,
)
from mente_laylay.autonomia.agendamento_mental import (
    criar_agenda_runtime as _criar_agenda_runtime_mente,
    extrair_agendamento_local as _extrair_agendamento_local_mente,
    resumo_agendamentos_para_prompt as _resumo_agendamentos_para_prompt_mente,
    tentar_intencao_contextual_ai as _tentar_intencao_contextual_ai_mente,
)
from mente_laylay.autonomia.roteador_intencao import (
    bloquear_por_emocao as _bloqueio_por_emocao_mente,
    executar_intencao as _executar_intencao_mente,
)
from mente_laylay.autonomia.orquestrador_deterministico import (
    detectar_intencao_deterministica_mente as _detectar_intencao_deterministica_mente,
)
from mente_laylay.autonomia.porteiro_acoes import (
    autorizar_acao_pratica as _autorizar_acao_pratica_mente,
    montar_contexto_porteiro_acoes as _montar_contexto_porteiro_acoes_mente,
    texto_conversa_contextual_sem_comando as _texto_conversa_contextual_sem_comando_mente,
    texto_conversa_casual_sem_acao as _texto_conversa_casual_sem_acao_mente,
    texto_bloqueia_playlist_agora as _texto_bloqueia_playlist_agora_mente,
    texto_tem_comando_explicito as _texto_tem_comando_explicito_mente,
    texto_pede_musica_explicitamente as _texto_pede_musica_explicitamente_mente,
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
from mente_laylay.emocoes.motor_humor import (
    ajustar_humor as _ajustar_humor_mente,
    detectar_gatilhos_instintivos as _detectar_gatilhos_instintivos_mente,
    get_humor_prompt as _get_humor_prompt_mente,
    montar_status_humor_prompt as _montar_status_humor_prompt_mente,
)
# from youtubesearchpython import VideosSearch (Removido por erro de proxies no ambiente)

LOG_MODE = str(os.getenv("LAYLAY_LOG_MODE", "limpo")).lower()
LOG_VERBOSE = str(os.getenv("LAYLAY_LOG_VERBOSE", "0")).lower() in {"1", "true", "yes", "on"}
_PRINT_LOCK = _threading.RLock()
_RAW_PRINT = _builtins.print

FALLBACK_FALA_NEUTRA = "Estou aqui, Pedro. Me fala o próximo passo."


def _formatar_mensagem_laylay(texto: str, emocao: str = "calma", nivel: Optional[int] = None) -> str:
    return _formatar_mensagem_laylay_mente(
        texto,
        emocao=emocao,
        nivel=nivel,
        fallback_fala=FALLBACK_FALA_NEUTRA,
        stdout=sys.stdout,
    )


def _should_log_message(text: str) -> bool:
    return _should_log_message_mente(text, log_mode=LOG_MODE, log_verbose=LOG_VERBOSE)


def _print_filtrado(*args, **kwargs):
    if not args:
        return
    if _should_log_message(" ".join(str(a) for a in args)):
        with _PRINT_LOCK:
            _RAW_PRINT(*args, **kwargs)


print = _print_filtrado
_builtins.print = _print_filtrado

# ====================== NOVO OUVIDO - FASTER WHISPER ======================
from faster_whisper import WhisperModel
import os

print("\n╔══════════════════════════════════════╗")
print("║  ◕‿◕ Laylay inicializando — modo essencial ║")
print("╚══════════════════════════════════════╝")
print("╭─ ◕ᴗ◕ Carregando o novo ouvido da Laylay...")
# Modelo leve e excelente em português
modelo_whisper = WhisperModel(
    "turbo", 
    device="cpu",
    compute_type="int8"
)
print("╰─ ✓ Ouvido Whisper carregado com sucesso!")
# ====================== FIM DO NOVO OUVIDO ======================
import traceback
import asyncio

from memoria_sqlite import MemoriaSQLite
from mente_laylay.integracao.gmail_mental import (
    DEFAULT_GMAIL_PALAVRAS_URGENTES,
    DEFAULT_GMAIL_PRIORITARIOS,
    criar_gmail_runtime,
)

try:
    import groq as _groq_module  # type: ignore[import-untyped]
except ImportError:
    _groq_module = None  # type: ignore

def _verificar_musica_autonoma(titulo_tocado: str):
    global _musica_busca_query, _musica_busca_fila
    _busca_musical_runtime.fila = _musica_busca_fila
    _busca_musical_runtime.query = _musica_busca_query
    _busca_musical_runtime.verificar_autonoma(titulo_tocado)
    _musica_busca_fila = _busca_musical_runtime.fila
    _musica_busca_query = _busca_musical_runtime.query

def _buscar_primeiro_video_youtube(query: str) -> Optional[str]:
    return _busca_musical_runtime.buscar_primeiro_video(query)


def _extrair_resultados_youtube_busca(html_text: str, query: str, limite: int = 10) -> list:
    return _extrair_resultados_youtube_busca_mente(
        html_text,
        query,
        limite,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
    )

def _limpar_texto_fala_ia(texto: str) -> str:
    fala = str(texto or "").strip()
    if not fala:
        return FALLBACK_FALA_NEUTRA

    fala = re.sub(
        r"(?is)\bcomandos?\s*:\s*(?:\[\s*\]|\[.*?\]|\{.*?\}|none|null|nada|nenhum(?:a)?)",
        " ",
        fala,
    )
    fala = re.sub(r"(?is)\bcomandos?\s*:\s*", " ", fala)
    fala = re.sub(r"(?is)\bcomando\s*:\s*", " ", fala)
    fala = re.sub(r"(?is)\[EXEC:?[^]]*\]", " ", fala)
    fala = re.sub(r"\s+", " ", fala).strip()
    return fala or FALLBACK_FALA_NEUTRA

def _normalizar_query_musical(texto: str) -> str:
    return _normalizar_query_musical_mente(texto, normalizar_texto_cb=_normalizar_texto_com_apelidos)

limpar_resposta_da_ia = partial(
    _limpar_resposta_da_ia_mente,
    limpar_texto_fala_cb=_limpar_texto_fala_ia,
    fallback_fala=FALLBACK_FALA_NEUTRA,
)

extrair_aprendizados_da_ia = _extrair_aprendizados_da_ia_mente
extrair_tipo_interacao_da_ia = _extrair_tipo_interacao_da_ia_mente


def salvar_aprendizados_da_ia(resposta_bruta):
    return _salvar_aprendizados_da_ia_mente(resposta_bruta, MEMORIA_SQLITE)


def _normalizar_texto_curto(texto: str) -> str:
    bruto = str(texto or "").lower()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acento).strip()


def _contexto_navegador_relevante(linha: str) -> bool:
    return _contexto_navegador_relevante_mente(
        linha,
        normalizar_texto=_normalizar_texto_curto,
    )


def _atualizar_memoria_topicos(texto_usuario: str, resposta_ia: str = "") -> None:
    global topicos_conversa_recente, ultimo_topico_conversa, ultimo_topico_ts
    recentes, topico, ts = _atualizar_memoria_topicos_mente(
        texto_usuario=texto_usuario,
        topicos_recentes=topicos_conversa_recente,
        ultimo_topico=ultimo_topico_conversa,
        normalizar_texto_curto=_normalizar_texto_curto,
    )
    if not topico or not ts:
        return
    topicos_conversa_recente = recentes
    ultimo_topico_conversa = topico
    ultimo_topico_ts = ts


def _fala_e_fallback_neutro(fala: str) -> bool:
    return _fala_e_fallback_neutro_mente(fala, _normalizar_texto_curto)


_texto_social_curto = _texto_social_curto_mente


def _contexto_gate_conversa() -> dict:
    return _montar_contexto_gate_conversa_mente(
        mente_integrada_estado=mente_integrada_estado,
        foco_vivo=_foco_vivo_atual(),
        ultimo_topico_conversa=ultimo_topico_conversa,
    )


_texto_tem_comando_explicito = _texto_tem_comando_explicito_mente


def _texto_conversa_contextual_sem_comando(texto: str) -> bool:
    return _texto_conversa_contextual_sem_comando_mente(texto, _contexto_gate_conversa())


def _texto_conversa_casual_sem_acao(texto: str) -> bool:
    """Reconhece conversa casual que nao deve entrar nos roteadores de comando."""
    if _texto_tem_comando_explicito(texto):
        return False
    if _texto_expresso_melhor_no_deterministico(texto):
        return False
    if _texto_conversa_contextual_sem_comando(texto):
        return True
    return _texto_conversa_casual_sem_acao_mente(texto)


_texto_bloqueia_playlist_agora = _texto_bloqueia_playlist_agora_mente


def _continuidades_get(chave: str, default=None):
    try:
        return (estado_continuidades or {}).get(chave, default)
    except Exception:
        return default


def _continuidades_set(chave: str, valor):
    global estado_continuidades
    estado_continuidades = _atualizar_continuidades_mente(estado_continuidades, **{chave: valor})
    return valor


def _continuidades_update(**campos):
    global estado_continuidades
    estado_continuidades = _atualizar_continuidades_mente(estado_continuidades, **campos)
    return estado_continuidades


def _musica_estado_get(chave: str, default=None):
    try:
        return (estado_musical or {}).get(chave, default)
    except Exception:
        return default


def _musica_estado_set(chave: str, valor):
    global estado_musical
    estado_musical = _atualizar_estado_musical_mente(estado_musical, **{chave: valor})
    return valor


def _percepcao_get(chave: str, default=None):
    try:
        return (estado_percepcao or {}).get(chave, default)
    except Exception:
        return default


def _percepcao_set(chave: str, valor):
    global estado_percepcao
    estado_percepcao = _atualizar_estado_percepcao_mente(estado_percepcao, **{chave: valor})
    return valor


def _texto_cancela_acao_agora(texto: str) -> bool:
    """Detecta desistências explícitas antes do contexto antigo reaproveitar intenção."""
    t = _normalizar_texto_com_apelidos(str(texto or ""))
    if not t:
        return False
    if _texto_social_curto(t):
        return False
    if any(token in t for token in [
        "em foco", "na frente", "pra frente", "para frente",
        "tela cheia", "fullscreen", "maximiza", "maximizar",
        "abre ", "abrir ", "fecha ", "fechar ",
        "steam", "opera", "chrome", "edge", "vscode", "vs code", "visual studio code",
    ]):
        return False
    padroes = [
        r"^(deixa para la|deixa pra la|deixa quieto|deixa isso)$",
        r"^(esquece|cancela|cancelar)$",
        r"^(para com isso|para ai|pode parar)$",
        r"^(nao quero mais|não quero mais|quero mais nao|quero mais não)$",
        r"^(desiste|abandona isso)$",
        r"^(ta|t[aá])\s+deixa\s+pra\s+la$",
    ]
    return any(re.fullmatch(p, t) for p in padroes)


def _bloquear_playlist_temporariamente(segundos: float = 600.0) -> None:
    """Limpa contexto musical vivo sem apagar playlists salvas."""
    global estado_musical
    _continuidades_update(playlist_sugestao_pendente=None)
    estado_musical = _bloquear_playlist_temporariamente_mente(estado_musical, segundos)


def _playlist_bloqueada_agora() -> bool:
    return _playlist_bloqueada_agora_mente(estado_musical)


def _contexto_porteiro_acoes() -> dict:
    return _montar_contexto_porteiro_acoes_mente(
        playlist_bloqueada=_playlist_bloqueada_agora(),
        playlist_ativa=bool(str(playlist_state.get("name") or "").strip()),
        auto_next_playlist=bool(str(playlist_state.get("name") or "").strip()),
        ultima_playlist=str(_musica_estado_get("ultima_playlist") or "").strip(),
        mente_integrada_estado=mente_integrada_estado,
        messages=messages,
    )


_texto_pede_playlist_explicitamente = _texto_pede_playlist_explicitamente_mente
_texto_pede_musica_explicitamente = _texto_pede_musica_explicitamente_mente


def _autonomia_permite_execucao_musical(intent: str, texto: str, *, confirmado: bool = False) -> bool:
    """Portão final: música/playlist só executa com pedido, confirmação ou contexto humano forte."""
    resultado = _autorizar_acao_pratica_mente(
        intent,
        texto,
        _contexto_porteiro_acoes(),
        confirmado=confirmado,
    )
    return bool(resultado.get("permitido"))


def _autorizar_acao_pratica(acao: str, texto: str = "", *, confirmado: bool = False, origem: str = "") -> dict:
    return _autorizar_acao_pratica_mente(
        acao,
        texto,
        _contexto_porteiro_acoes(),
        confirmado=confirmado,
        origem=origem,
    )


def _contexto_conversa_natural() -> dict:
    return _montar_contexto_conversa_natural_mente(
        current_emotion=current_emotion,
        mente_integrada_estado=mente_integrada_estado,
        ultimo_topico_conversa=ultimo_topico_conversa,
        foco_vivo=_foco_vivo_atual(),
        pesquisar_contexto_tema=_pesquisar_contexto_tema,
        normalizar_texto_curto=_normalizar_texto_curto,
        normalizar_texto_com_apelidos=_normalizar_texto_com_apelidos,
        resumo_mente_integrada_para_prompt=_resumo_mente_integrada_para_prompt,
        enviar_mensagem=enviar_mensagem,
        extrair_json_da_ia=_extrair_json_da_ia,
        ajustar_fala_por_horario=_ajustar_fala_por_horario,
        fala_de_confirmacao_variada=_fala_de_confirmacao_variada,
        texto_parece_navegacao_ou_janela_ia=_texto_parece_navegacao_ou_janela_ia,
        fala_e_fallback_neutro=_fala_e_fallback_neutro,
        ajustar_tom_por_emocao=_ajustar_tom_por_emocao,
        acalmar_emocao=_acalmar_emocao_conversacional,
    )


def _acalmar_emocao_conversacional(motivo: str = "") -> None:
    global current_emotion, emotion_level, humor_level
    try:
        if str(current_emotion or "").strip().lower() in {"brava", "irritada", "nervosa", "raivosa"}:
            current_emotion = "calma"
            emotion_level = 1
        humor_level = max(0, int(humor_level or 0))
        if motivo:
            print(f"🧘 [HUMOR] acalmando por conversa: {motivo}")
    except Exception:
        pass


def _contexto_inicio_chat() -> dict:
    return _montar_contexto_inicio_chat_por_grupos_mente(
        base={
            "messages": messages,
            "current_emotion": current_emotion,
            "emotion_level": emotion_level,
        },
        memoria={
            "processar_aprendizado_apelido_imediato": _processar_aprendizado_apelido_imediato,
            "refinar_contexto_mental": _refinar_contexto_mental,
            "registrar_autoaprimoramento": _registrar_autoaprimoramento,
            "registrar_mente_curta": _registrar_mente_curta,
            "registrar_resultado_execucao": _registrar_resultado_execucao,
            "recuperar_aprendizados": MEMORIA_SQLITE.recuperar_aprendizados,
        },
        conversa={
            "texto_social_curto": _texto_social_curto,
            "texto_conversa_casual_sem_acao": _texto_conversa_casual_sem_acao,
            "texto_tem_comando_explicito": _texto_tem_comando_explicito,
            "resposta_conversa_rapida_local": _resposta_conversa_rapida_local,
            "parece_elogio_ou_agradecimento_curto": _parece_elogio_ou_agradecimento_curto,
            "responder_agradecimento_ou_elogio": _responder_agradecimento_ou_elogio,
            "resolver_pergunta_curta_contextual_intencao": _resolver_pergunta_curta_contextual_intencao,
            "texto_responde_pergunta_aberta": _texto_responde_pergunta_aberta,
            "responder_pergunta_aberta": _responder_pergunta_aberta,
        },
        musica_feedback={
            "texto_bloqueia_playlist_agora": _texto_bloqueia_playlist_agora,
            "texto_pede_direcao_musical_generica": _texto_pede_direcao_musical_generica,
            "responder_pedido_direcao_musical_generica": _responder_pedido_direcao_musical_generica,
            "processar_confirmacao_sugestao_musical": _processar_confirmacao_sugestao_musical,
            "handle_feedback_pendente_misto": _handle_feedback_pendente_misto,
            "handle_feedback_pendente": _handle_feedback_pendente,
            "bloquear_playlist_temporariamente": _bloquear_playlist_temporariamente,
            "detectar_mover_playlist_texto": detectar_mover_playlist_texto,
            "mover_item_playlist": mover_item_playlist,
        },
        comandos={
            "processar_comando_deterministico": processar_comando_deterministico,
            "usar_modo_rapido_conversa": _usar_modo_rapido_conversa,
            "interpretar_comando_local_rapido": interpretar_comando_local_rapido,
            "resolver_comando_janela_contextual_forcado": _resolver_comando_janela_contextual_forcado,
            "resolver_comando_midia_contextual_forcado": _resolver_comando_midia_contextual_forcado,
            "resolver_comando_arquivo_contextual_forcado": _resolver_comando_arquivo_contextual_forcado,
            "resolver_comando_acao_geral_contextual_forcado": _resolver_comando_acao_geral_contextual_forcado,
            "resolver_comando_contextual_forcado": _resolver_comando_contextual_forcado,
            "responder_contexto_janela_indisponivel": _responder_contexto_janela_indisponivel,
        },
        execucao={
            "executar_intencao": executar_intencao,
            "emitir_resposta_curta": _emitir_resposta_curta,
            "executar_intencao_curta_contextual": _executar_intencao_curta_contextual,
            "falar_com_lipsync": falar_com_lipsync,
            "salvar_memoria": salvar_memoria,
        },
    )


def _pergunta_aberta_atual() -> dict | None:
    try:
        return _pergunta_aberta_ativa_mente(mente_integrada_estado, ttl_s=120.0)
    except Exception:
        return None


def _limpar_pergunta_aberta() -> None:
    global mente_integrada_estado
    try:
        mente_integrada_estado = _limpar_pergunta_aberta_mente(mente_integrada_estado)
    except Exception:
        pass


def _registrar_alvo_corrigido(alvo: str) -> None:
    global mente_integrada_estado
    try:
        mente_integrada_estado = _registrar_alvo_corrigido_mente(mente_integrada_estado, alvo)
    except Exception:
        pass


def _alvo_corrigido_atual() -> str:
    try:
        return str(_alvo_corrigido_ativo_mente(mente_integrada_estado, ttl_s=120.0) or "").strip()
    except Exception:
        return ""


def _registrar_estrutura_arquivo_recente(params: dict | None) -> None:
    global mente_integrada_estado
    try:
        mente_integrada_estado = _registrar_estrutura_arquivo_recente_mente(mente_integrada_estado, params)
    except Exception:
        pass


def _estrutura_arquivo_recente(ttl_s: float = 900.0) -> dict | None:
    try:
        return _estrutura_arquivo_recente_mente(mente_integrada_estado, ttl_s=ttl_s)
    except Exception:
        return None


def _texto_responde_pergunta_aberta(texto_usuario: str) -> bool:
    return _texto_responde_pergunta_aberta_continuidade_mente(
        texto_usuario,
        pergunta_aberta=_pergunta_aberta_atual(),
        normalizar_texto_curto=_normalizar_texto_curto,
        texto_parece_resposta_curta_a_pergunta=_texto_parece_resposta_curta_a_pergunta_mente,
        bloqueadores=[
            _resolver_pergunta_curta_contextual_intencao,
            lambda t: detectar_intencao_deterministica(t),
            lambda t: interpretar_comando_local_rapido(_normalizar_texto_com_apelidos(t)),
            _resolver_comando_midia_contextual_forcado,
            _resolver_comando_janela_contextual_forcado,
        ],
    )


def _responder_pergunta_aberta(texto_usuario: str) -> str:
    pergunta = _pergunta_aberta_atual() or {}
    _limpar_pergunta_aberta()
    return _responder_pergunta_aberta_continuidade_mente(
        texto_usuario,
        pergunta_aberta=pergunta,
        foco_vivo=_foco_vivo_atual(),
        normalizar_texto_curto=_normalizar_texto_curto,
        responder_conversa_curta_por_tipo=_responder_conversa_curta_por_tipo,
        ajustar_fala_por_horario=_ajustar_fala_por_horario,
    )


def _contexto_recente_indica_email() -> bool:
    return _contexto_recente_indica_email_mente(_contexto_conversa_natural())


def _resolver_pergunta_curta_contextual_intencao(texto_usuario: str) -> dict | None:
    return _resolver_pergunta_curta_contextual_intencao_continuidade_mente(
        texto_usuario,
        normalizar_texto_curto=_normalizar_texto_curto,
        contexto_recente_indica_email=_contexto_recente_indica_email,
    )


def _responder_agradecimento_ou_elogio(texto_usuario: str) -> str:
    return _responder_agradecimento_ou_elogio_mente(_contexto_conversa_natural(), texto_usuario)


def _responder_conversa_curta_por_tipo(tipo: str, texto_usuario: str = "") -> str:
    return _responder_conversa_curta_por_tipo_mente(_contexto_conversa_natural(), tipo, texto_usuario)


def _emitir_resposta_curta(texto_usuario: str, fala: str, *, emocao: str = "", nivel: int = 1, habilidade: str = "conversa") -> bool:
    fala = str(fala or "").strip()
    if not fala:
        return False
    messages.append({"role": "user", "content": str(texto_usuario or "")})
    messages.append({"role": "assistant", "content": fala})
    falar_com_lipsync(fala, emocao or current_emotion or "calma", nivel or emotion_level or 1)
    _registrar_mente_curta(str(texto_usuario or ""), fala, habilidade=habilidade)
    memoria_inteligente.adicionar_interacao(str(texto_usuario or ""), fala)
    salvar_memoria()
    return True


def _falar_falha_contextual(categoria: str, texto_usuario: str = "", *, detalhe: str = "") -> None:
    cat = str(categoria or "").strip().lower()
    texto_norm = _normalizar_texto_com_apelidos(str(texto_usuario or ""))
    alvo = str(detalhe or "").strip()

    fala_direta = _fala_falha_contextual_variada(
        cat,
        texto_normalizado=texto_norm,
        detalhe=alvo,
        incluir_generica=False,
    )
    if fala_direta:
        falar_com_lipsync(fala_direta, "calma", 1)
        return

    if texto_usuario and not _texto_parece_navegacao_ou_janela_ia(texto_usuario):
        try:
            resposta_local = _resposta_conversa_local(texto_usuario)
            resposta_local = str(resposta_local or "").strip()
            if resposta_local and not _fala_e_fallback_neutro(resposta_local):
                print("🧭 [FALHA-CONTEXTUAL] conversa local assumiu a recuperação")
                falar_com_lipsync(resposta_local, "calma", 1)
                return
        except Exception as e:
            print(f"⚠️ [FALHA-CONTEXTUAL] não consegui recuperar pela conversa local: {e}")

    falar_com_lipsync(
        _fala_falha_contextual_variada(cat, texto_normalizado=texto_norm, detalhe=alvo),
        "calma",
        1,
    )


def _executar_intencao_curta_contextual(resultado: dict | None, texto_usuario: str, *, origem: str, contexto_autoaprimoramento: str = "") -> bool:
    if not isinstance(resultado, dict) or not str(resultado.get("intent") or "").strip():
        return False
    print(f"⚡ [ROTEADOR PERGUNTA-CURTA [{origem}]] {resultado}")
    executou = bool(executar_intencao(resultado, texto_usuario))
    _registrar_resultado_execucao(resultado, texto_usuario, executou, origem="pergunta_curta_contextual")
    if executou:
        _registrar_autoaprimoramento(
            resultado,
            texto_usuario,
            True,
            contexto=contexto_autoaprimoramento or "pergunta curta dependente do topico",
            origem=origem,
        )
    return executou


def _texto_parece_navegacao_ou_janela_ia(texto: str) -> bool:
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return False
    verbos = [
        "abre", "abrir", "abra", "entra", "entrar", "vai para", "vai pro",
        "fecha", "fechar", "mata", "derruba", "encerra", "encerrar",
        "maximiza", "maximizar", "tela cheia", "fullscreen",
        "em foco", "foco", "traz", "trazer", "puxa pra frente", "para frente",
    ]
    alvos = [
        "site", "aba", "janela", "programa", "app", "aplicativo",
        "opera", "chrome", "steam", "spotify", "netflix", "youtube",
        "instagram", "whatsapp", "explorador", "microsoft store",
    ]
    return any(v in t for v in verbos) and any(a in t for a in alvos)


def _construir_fala_conversa(fala: str, texto_usuario: str = "", tipo_interacao: str = "", comandos=None) -> str:
    """Fachada de compatibilidade para a conversa natural modular."""
    return _construir_fala_conversa_mente(_contexto_conversa_natural(), fala, texto_usuario, tipo_interacao, comandos)


def _resposta_conversa_local(texto_usuario: str) -> str:
    return _resposta_conversa_local_mente(_contexto_conversa_natural(), texto_usuario)


def _parece_elogio_ou_agradecimento_curto(texto_usuario: str) -> bool:
    return _parece_elogio_ou_agradecimento_curto_mente(_contexto_conversa_natural(), texto_usuario)


def _resposta_conversa_rapida_local(texto_usuario: str) -> str:
    """Fachada de compatibilidade para o fluxo modular de conversa curta."""
    return _resposta_conversa_rapida_local_mente(_contexto_conversa_natural(), texto_usuario)


def _contexto_horario_atual() -> str:
    """Classifica o horário local em blocos simples para deixar a fala mais viva."""
    hora = time.localtime().tm_hour
    if 0 <= hora < 5:
        return "madrugada"
    if 5 <= hora < 12:
        return "manha"
    if 12 <= hora < 18:
        return "tarde"
    return "noite"

def _obter_contexto_perceptivo() -> dict:
    """Resume os sinais vivos que a Laylay já conhece neste momento."""
    periodo = _contexto_horario_atual()
    agora = datetime.now()
    hora_chave = agora.strftime("%H:00")
    rotina_atual = {}
    try:
        rotina_atual = dict(_rotina_dados_diarios.get(hora_chave) or {})
    except Exception:
        rotina_atual = {}

    return _montar_contexto_perceptivo_mente(
        periodo=periodo,
        agora=agora,
        contexto_sistema=contexto_sistema,
        logs_navegador=contexto_atual_logs,
        current_emotion=current_emotion,
        emotion_level=emotion_level,
        humor_level=humor_level,
        ultimo_topico_conversa=ultimo_topico_conversa,
        topicos_conversa_recente=topicos_conversa_recente,
        rotina_atual=rotina_atual,
    )

def _interpretar_contexto_vivo(ctx: dict = None, texto_extra: str = "") -> dict:
    ctx = ctx if isinstance(ctx, dict) else _obter_contexto_perceptivo()
    return _interpretar_contexto_vivo_mente(
        ctx,
        texto_extra,
        normalizar_cb=_normalizar_texto_com_apelidos,
    )

def _resumo_mente_integrada_para_prompt(texto_usuario: str = "") -> str:
    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx, texto_usuario)
    return _montar_resumo_mente_integrada_com_extras_mente(
        texto_usuario=texto_usuario,
        ctx=ctx,
        percepcao=percepcao,
        mente=mente_integrada_estado,
        resumo_autoaprimoramento_cb=_resumo_autoaprimoramento_para_prompt,
        memoria_sqlite=MEMORIA_SQLITE,
    )

def _registrar_mente_curta(texto_usuario: str = "", resposta_ia: str = "", intencao: str = "", alvo: str = "", escopo: str = "", habilidade: str = "") -> None:
    global mente_integrada_estado
    mente_integrada_estado = _registrar_mente_curta_mente(
        mente_integrada_estado,
        texto_usuario=texto_usuario,
        resposta_ia=resposta_ia,
        intencao=intencao,
        alvo=alvo,
        escopo=escopo,
        habilidade=habilidade,
        ultimo_topico_conversa=ultimo_topico_conversa,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
        eh_alvo_site_web_cb=_eh_alvo_site_web,
        texto_parece_pergunta_aberta_cb=_texto_parece_pergunta_aberta_mente,
        registrar_pergunta_aberta_cb=_registrar_pergunta_aberta_mente,
        limpar_pergunta_aberta_cb=_limpar_pergunta_aberta_mente,
        registrar_promessa_conversacional_cb=_registrar_promessa_conversacional_mente,
        atualizar_foco_vivo_cb=_atualizar_foco_vivo,
    )


def _atualizar_foco_vivo(estado: dict, *, texto: str = "", resposta: str = "", intencao: str = "", alvo: str = "", habilidade: str = "", escopo: str = "") -> dict:
    return _atualizar_foco_vivo_mente(
        estado,
        texto=texto,
        resposta=resposta,
        intencao=intencao,
        alvo=alvo,
        habilidade=habilidade,
        escopo=escopo,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
    )


def _foco_vivo_atual(ttl_s: float = 480.0) -> dict:
    return _foco_vivo_atual_mente(mente_integrada_estado, ttl_s=ttl_s)


def _registrar_resultado_execucao(resultado: dict = None, texto: str = "", executou: bool = True, *, origem: str = "", status: str = "") -> None:
    global mente_integrada_estado
    mente_integrada_estado = _registrar_resultado_execucao_mente(
        mente_integrada_estado,
        resultado=resultado,
        texto=texto,
        executou=executou,
        origem=origem,
        status=status,
    )
    mente_integrada_estado = _enriquecer_resultado_execucao_contextual_mente(
        mente_integrada_estado,
        resultado,
        texto=texto,
        executou=executou,
        status=status,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
        atualizar_foco_vivo_cb=_atualizar_foco_vivo,
    )


def _resolver_repeticao_ultima_acao(texto: str):
    return _resolver_repeticao_ultima_acao_mente(
        texto,
        mente_integrada_estado,
        _normalizar_texto_com_apelidos,
    )

def _registrar_autoaprimoramento(resultado: dict = None, texto: str = "", sucesso: bool = True, erro: str = "", contexto: str = "", origem: str = "") -> None:
    global autoaprimoramento_estado
    autoaprimoramento_estado = _registrar_autoaprimoramento_mente(
        autoaprimoramento_estado,
        resultado=resultado,
        texto=texto,
        sucesso=sucesso,
        erro=erro,
        contexto=contexto,
        origem=origem,
    )

def _resumo_autoaprimoramento_para_prompt(limit: int = 4) -> str:
    try:
        return _resumo_autoaprimoramento_para_prompt_mente(autoaprimoramento_estado, limit=limit)
    except Exception:
        return "Autoaprimoramento: indisponível."

def _refinar_contexto_mental(texto: str, resultado: dict = None) -> None:
    dados = _extrair_refino_contexto_mental_mente(texto, resultado)
    if not dados.get("texto"):
        return
    _registrar_mente_curta(
        dados.get("texto", ""),
        "",
        dados.get("intencao", ""),
        dados.get("alvo", ""),
        dados.get("escopo", ""),
        dados.get("habilidade", ""),
    )

def _contexto_aponta_descanso(texto_extra: str = "") -> bool:
    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx, texto_extra)
    return _contexto_aponta_descanso_mente(ctx, percepcao, texto_extra)

def _texto_indica_autocorrecao(texto: str) -> bool:
    t = _normalizar_texto(texto)
    if not t:
        return False
    gatilhos = [
        "corrigindo", "na verdade", "me enganei", "errei", "ops", "deixa eu corrigir",
        "deixa corrigir", "vou corrigir", "retificando", "ajustando a resposta",
    ]
    return any(g in t for g in gatilhos)

def _ajustar_fala_por_horario(fala: str, texto_usuario: str = "") -> str:
    return _ajustar_fala_por_horario_mente(
        fala,
        texto_usuario,
        obter_contexto_perceptivo=_obter_contexto_perceptivo,
        interpretar_contexto_vivo=_interpretar_contexto_vivo,
        escolher_fala=_escolher_fala_variada,
    )


import pyttsx3
import sounddevice as sd
import soundfile as sf
import ctypes
import urllib.parse
import webbrowser
from datetime import datetime
import edge_tts
import threading    
from ctypes import wintypes
from pycaw.pycaw import AudioUtilities
import pyautogui
import pygetwindow as gw

try:
    from pywinauto import Application
except Exception:
    Application = None
import importlib
from importlib.util import find_spec

from youtube_transcript_api import YouTubeTranscriptApi

PYWINDOWCTL_AVAILABLE = find_spec("pywinctl") is not None
pwc = importlib.import_module("pywinctl") if PYWINDOWCTL_AVAILABLE else None

# Configurações do PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

try:
    #from TTS.api import TTS
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

try:
    from AppOpener import open as open_app
    APP_OPENER_AVAILABLE = True
    print("✅ AppOpener carregado — abertura rápida de programas ativada!")
except ImportError:
    APP_OPENER_AVAILABLE = False
    print("⚠️ AppOpener não encontrado. Instale com: pip install AppOpener")

ws_loop = None
connected_pc_b_clients = set()  # Clientes PC B (cliente_laylay.py)

# ====================== VOZ XTTS-v2 (ultra natural) ======================
REFERENCE_VOICE = "voices/reference_female.wav"   # ← ARQUIVO DA SUA VOZ FEMININA

# ====================== VARIÁVEIS GLOBAIS ======================
_last_bordao_check = 0
turno = 0
is_speaking = False
memoria_pronta = False
messages = []
bordoes = []
resumo_conversa = ""
memoria_fatos = []
memoria_eventos = []
playlists_carregadas = {}
historico_long_term = ""
current_emotion = "calma"
emotion_level = 1
playlist_pos = {"Carlos": 0}
interrupt_event = threading.Event()
is_speaking = False
playback_lock = threading.Lock()
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
# Corrigido: Inicialização de contexto_atual para evitar avisos do Pylance sobre tipos
contexto_atual = _percepcao_get("contexto_web", {"site": "", "termo_busca": "", "aba_id": 0})
contexto_atual_logs = _percepcao_get("logs_navegador", [])
estado_continuidades = _estado_continuidades_inicial_mente()
estado_musical = _estado_musical_inicial_mente()
estado_percepcao = _estado_percepcao_inicial_mente()
_ultimo_sugerido_ts = 0.0
sugestao_bloqueada_ate = {}
ultimo_open_site = _percepcao_get("ultimo_open_site", {"ts": 0.0, "topic": "", "url": ""})
contexto_sistema = _percepcao_get("contexto_sistema", {"exe": "", "title": "", "assunto": ""})
_ULTIMOS_COMANDOS_EXECUTADOS = []
_ultimo_proativo_ts = 0.0
_pastas_contexto_cache = {"ts": 0.0, "texto": ""}
_dicionario_contexto_cache = {"versao": -1, "texto": ""}
_dicionario_paginas_versao = 0
_contexto_paginas = ContextoPaginas()
mente_integrada_estado = _estado_mental_inicial_mente()
autoaprimoramento_estado = {
    "habilidades": {},
    "eventos": [],
    "ultimo_resumo": "",
    "cookie_reforco": 0,
}
_base_dir = os.path.abspath(os.path.dirname(__file__)) if "__file__" in globals() else os.getcwd()
PASTA_MEMORIA = os.path.join(_base_dir, "memoria")
PASTA_MEMORIA_VISUAL = os.path.join(PASTA_MEMORIA, "memoria_visual")
MEMORIA_VISUAL_INDICE_ARQUIVO = os.path.join(PASTA_MEMORIA, "memoria_visual_indice.json")

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
_briefing_executado = False

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
SAUDE_TEMP_THRESHOLD = 75         # °C
SAUDE_CPU_SUSTENTADO_SEGUNDOS = 30

_saude_cpu_alta_desde = 0.0
_saude_ultimo_aviso = 0.0

# ====================== APRENDIZADO DE ROTINA ======================
ROTINA_DIAS_PARA_APRENDER = 7
ROTINA_ARQUIVO_APRENDIDO = os.path.join(PASTA_MEMORIA, "rotinas_aprendidas.json")
_rotina_dados_diarios = {}          # {hora: {"janelas": [...], "assuntos": [...]}}
_rotina_ultimo_log = 0.0
_rotina_ultima_sugestao = 0.0

# ====================== FEEDBACK DE ROTINA (Aprendizado por Resposta) ======================
# Pesos de feedback por app/hora: positivo = Pedro aceitou, negativo = rejeitou
# Formato: {"hora:app": int}  (ex: {"09:00:vscode": 3, "09:00:chrome": -2})
_rotina_feedback_pesos: dict = {}
ROTINA_BLOQUEIO_REJEICAO_MIN = 60    # minutos de bloqueio apos "nao"
ROTINA_BLOQUEIO_REJEICAO_VEZES = 3   # apos 3 rejeicoes, nunca mais sugere aquele app/hora

# ====================== APRENDIZADO MUSICAL ======================
MUSICA_ARQUIVO_HISTORICO = os.path.join(PASTA_MEMORIA, "aprendizado_musical.json")
MUSICA_ARQUIVO_FEEDBACK = os.path.join(PASTA_MEMORIA, "musicas_feedback.json")
_musica_dados_diarios = {}          # {hora: [lista de musicas]}
_musica_feedback_pesos = {}         # {"hora:musica": peso}
_musica_ultima_sugestao = 0.0
playlists_laylay_carregadas = {}
_contexto_dispatcher_runtime = None
_contexto_finalizacao_runtime = None
_contexto_prompt_runtime = None
_contexto_exec_runtime = None
_servicos_background_runtime = _criar_gerenciador_servicos_background_mente(log=print)

# Fila para troca autonoma de musicas no YouTube
_musica_busca_fila = []
_musica_busca_query = ""
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
except Exception as e:
    print(f"⚠️ Aviso: Nao foi possivel criar ou migrar docs na pasta de memoria: {e}")

playlists_state_file = os.path.join(_base_dir, PLAYLISTS_ARQUIVO)
playlists_legacy_file = os.path.join(os.path.expanduser("~"), "playlists_laylay.json")
playlist_state = _musica_estado_get("playlist_state", {"name": "", "index": 0, "user_intervened": False, "last_url": ""})
_playlist_runtime = _criar_playlist_runtime_mente(
    state_file=playlists_state_file,
    legacy_file=playlists_legacy_file,
    cache=playlists_carregadas,
    ultima_playlist_getter=lambda: str(_musica_estado_get("ultima_playlist") or ""),
    ultima_playlist_setter=lambda valor: _musica_estado_set("ultima_playlist", valor),
    playlist_state=playlist_state,
    indice_setter=lambda valor: globals().__setitem__("indice_atual", int(valor or 0)),
    youtube_play=lambda url: validar_e_enviar_comando("youtube_play", {"url": url}),
    solicitar_aba_ativa=lambda **kwargs: solicitar_aba_ativa(**kwargs),
    log=print,
)
_playlist_laylay_runtime = _criar_playlist_laylay_runtime_mente(
    state_file=PLAYLISTS_LAYLAY_ARQUIVO,
    cache=playlists_laylay_carregadas,
    playlists_usuario_getter=lambda: _playlist_runtime.load(),
    historico_musical_getter=lambda: _musica_dados_diarios,
    adicionar_playlist_usuario=lambda nome, url, titulo, canal: _playlist_runtime.add_url(
        nome,
        url,
        titulo,
        canal,
    ),
)
indice_atual = 0
fish_mode_active = False
fish_mode_started_ts = 0.0
COMANDOS_ATIVOS = ["coloca", "toca", "pesquisa", "entra", "abre", "fecha", "peixe", "resumo"]
pending_delete_playlist = ""
pending_delete_playlist_ts = 0.0
coordenadas = {}
pending_coord_key = None
skill_manager = None
humor_level = 0         
humor_last_update = 0.0
humor_history = []       
BARGE_IN_COUNT = 0
BARGE_IN_WINDOW = 60.0  
conversa_ativa = False
tempo_ultima_fala = 0.0
TEMPO_LIMITE_CONVERSA = 75
MODO_CHAT = False
HOTKEY_MODO_CHAT_LIGA = "ctrl+shift+c"
HOTKEY_MODO_CHAT_DESLIGA = "ctrl+shift+n"
_modo_chat_runtime = None
_interpretacao_intencao_runtime = None
ULTIMO_CONTEUDO_PAGINA = ""
topicos_conversa_recente = []
ultimo_topico_conversa = ""
ultimo_topico_ts = 0.0
# Contador de falhas consecutivas por AçÃO+ALVO — anti-loop de desculpas
# Chave: "acao|alvo" | Valor: contagem de falhas seguidas
_falhas_consecutivas: dict = {}
MAX_TENTATIVAS_AUTOCORRECAO = 3   # ← muda aqui se quiser mais ou menos paciencia
_autocorrecao_total = 0
_cookie_virtual_total = 0
_autocorrecao_eventos = []
evento_pagina_recebida = asyncio.Event()
dicionario_paginas = _contexto_paginas.paginas
EVENTO_PAGINA = asyncio.Event()
ULTIMO_CONTEUDO_PAGINA = ""

# ====================== PORTEIRO DO CHROME (rastreamento de abas) ======================
_abas_sugeridas_fechar: list = []  # abas propostas no ultimo aviso
_porteiro_ultima_sugestao_ts: float = 0.0
RAM_THRESHOLD_PORTEIRO = 80   # % de RAM para disparar curadoria
ABA_IDLE_MINUTOS = 45         # minutos sem visitar para considerar "abandonada"
PORTEIRO_INTERVALO_MIN = 12   # checa a cada 12 minutos

# ====================== CONTEXTO ATUAL DO CHROME (para o novo prompt) ======================
aba_ativa_estado = _percepcao_get("aba_ativa", {"titulo": "Nenhuma aba aberta", "url": "Nenhuma URL"})
_chrome_estado = _ChromeEstadoRuntime(
    titulo_inicial=str(aba_ativa_estado.get("titulo") or "Nenhuma aba aberta"),
    url_inicial=str(aba_ativa_estado.get("url") or "Nenhuma URL"),
)

# ====================== MEMÓRIA INTELIGENTE (Curto → Longo Prazo) ======================
class MemoriaLaylay:
    def __init__(self):
        self.contador = 0
        self.historico_recente = []   # últimas 5 interações
        self.resumo_do_dia = ""       # resumo acumulado do dia atual
        self.data_atual = datetime.now().strftime("%d-%m-%Y")
        self.arquivo_diario = os.path.join(PASTA_MEMORIA, f"memoria_{self.data_atual}.txt")
        self.carregar_resumo_diario()


    def carregar_resumo_diario(self):
        if os.path.exists(self.arquivo_diario):
            try:
                with open(self.arquivo_diario, "r", encoding="utf-8") as f:
                    self.resumo_do_dia = f.read().strip()
                print(f"📂 [MEMÓRIA] Resumo do dia {self.data_atual} carregado")
            except:
                self.resumo_do_dia = ""

    def salvar_resumo_diario(self):
        try:
            with open(self.arquivo_diario, "w", encoding="utf-8") as f:
                f.write(f"RESUMO DO DIA {self.data_atual}:\n\n{self.resumo_do_dia}")
            print(f"💾 [MEMÓRIA] Resumo salvo em {self.arquivo_diario}")
        except Exception as e:
            print(f"⚠️ Erro ao salvar resumo: {e}")

    def adicionar_interacao(self, usuario: str, resposta_ia: str):
        self.contador += 1
        horario = datetime.now().strftime("%H:%M")
        interacao = f"[{horario}] Usuário: {usuario} | Laylay: {resposta_ia}"
        self.historico_recente.append(interacao)

        if self.contador % 5 == 0:
            self.atualizar_resumo_diario()

    def atualizar_resumo_diario(self):
        print(f"🚀 [MEMÓRIA] Gerando resumo das últimas {len(self.historico_recente)} interações...")

        texto_para_resumir = "\n".join(self.historico_recente)
        prompt_resumo = (
            f"Resumo atual do dia:\n{self.resumo_do_dia}\n\n"
            f"Novas interações:\n{texto_para_resumir}\n\n"
            "Atualize o resumo do dia de forma concisa, mantendo apenas os fatos importantes, "
            "pedidos do Pedro, preferências e eventos relevantes. Escreva em português."
        )

        mensagens_resumo = [
            {"role": "system", "content": prompt_resumo},
            {"role": "user", "content": "Resuma tudo acima em um texto coeso e curto."}
        ]
        novo_resumo = enviar_mensagem(mensagens_resumo, _com_tools=False)

        self.resumo_do_dia = novo_resumo.strip()
        self.salvar_resumo_diario()
        self.historico_recente = []

memoria_inteligente = MemoriaLaylay()

# ====================== CONFIGURAÇÕES GLOBAIS ======================
API_KEY = "ollama"
MODEL = "qwen3:4b-instruct"
OPENROUTER_BASE_URL = "http://localhost:11434/v1"
# Para usar OpenRouter, configure OPENROUTER_API_KEY no ambiente.
#MODEL = "mistralai/mistral-small-24b-instruct-2501"
MEMORIA_ARQUIVO = os.path.join(PASTA_MEMORIA, "laylay_memoria.json")
MEMORIA_CONTEXTO_ARQUIVO = os.path.join(PASTA_MEMORIA, "memoria_contexto.json")
MEMORIA_SQLITE = MemoriaSQLite(os.path.join(PASTA_MEMORIA, "laylay_memoria.sqlite"))
#OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HTTP_REFERER = os.environ.get("OPENROUTER_HTTP_REFERER", "http://localhost")
OPENROUTER_APP_TITLE = os.environ.get("OPENROUTER_APP_TITLE", "Laylay")
LLM_LOCAL_TIMEOUT = int(os.environ.get("LAYLAY_LLM_LOCAL_TIMEOUT", "120"))
LLM_REMOTE_TIMEOUT = int(os.environ.get("LAYLAY_LLM_REMOTE_TIMEOUT", "30"))
_LLM_HTTP_LOCK = threading.RLock()
_LLM_BAD_REQUEST_UNTIL = 0.0


def _llm_endpoint_eh_local() -> bool:
    return _llm_endpoint_eh_local_mente(OPENROUTER_BASE_URL)


def _post_chat_llm(headers: dict, data: dict, timeout: Optional[int] = None):
    global _LLM_BAD_REQUEST_UNTIL
    resposta, novo_bad_request_until = _post_chat_llm_mente(
        headers,
        data,
        base_url=OPENROUTER_BASE_URL,
        local_timeout=LLM_LOCAL_TIMEOUT,
        remote_timeout=LLM_REMOTE_TIMEOUT,
        bad_request_until=_LLM_BAD_REQUEST_UNTIL,
        lock=_LLM_HTTP_LOCK,
        requests_post=requests.post,
        print_fn=print,
        timeout=timeout,
    )
    _LLM_BAD_REQUEST_UNTIL = novo_bad_request_until
    return resposta

# ── GEMINI VISION API (Olho Que Tudo Vê) ─────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

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
PROCESS_MAP = {
    "vscode": ["Code.exe", "code.exe"],
    "vs code": ["Code.exe", "code.exe"],
    "visual studio code": ["Code.exe", "code.exe"],
    "steam": ["steam.exe"],
    "discord": ["Discord.exe"],
    "spotify": ["Spotify.exe"],
    "chrome": ["chrome.exe"],
    "firefox": ["firefox.exe"],
    "edge": ["msedge.exe"],
    "minecraft": ["Minecraft.exe", "javaw.exe"],
    "obs": ["obs64.exe"],
    "terminal": ["WindowsTerminal.exe", "wt.exe"],
    "cmd": ["cmd.exe"],
    "notepad": ["notepad.exe"],
    "paint": ["mspaint.exe"],
    "calculadora": ["calc.exe"],
}
VOICE = "pt-BR-FranciscaNeural"

# ====================== EMOÇÕES ======================
EMO_DESC = {
    "calma": "Mantenha calma absoluta, confiança total e controle. Tom elegante, sereno e acolhedor.",
    "debochada": "Eleve o deboche com classe: ironia refinada, leveza e humor esperto sem perder o carinho.",
    "envergonhada": "Fique tímida e doce: responda com leve constrangimento, carinho discreto e um toque de blush na fala.",
    "irritada": "Mostre irritação controlada: tom mais cortante, sarcasmo afiado e leve impaciência.",
    "brava": "Seja firme e intimidadora: tom direto, dominante, sem paciência e impactante.",
    "alegre": "Fale com entusiasmo luminoso, energia alta e simpatia clara, sem exagerar no caos.",
    "triste": "Mostre delicadeza, menor energia e um tom mais baixo, como quem fala com cuidado.",
    "surpresa": "Reaja com curiosidade viva, atenção instantânea e uma pitada de espanto.",
    "acalmando-se": "Mostre que está se acalmando gradualmente, mas ainda com presença e controle."
}

SITES_WEB_ALIAS = {
    "insta",
    "instagram",
    "instagram direct",
    "instagram.com",
    "www.instagram.com",
    "direct instagram",
}

def _eh_alvo_site_web(texto: str) -> bool:
    return _eh_alvo_site_web_mente(
        texto,
        normalizar_texto=_normalizar_texto_com_apelidos,
        sites_web_alias=SITES_WEB_ALIAS,
        sites_directos=SITES_DIRECTOS,
    )

def _contexto_aponta_site_web(texto: str = "") -> bool:
    return _contexto_aponta_site_web_mente(
        texto,
        normalizar_texto=_normalizar_texto_com_apelidos,
        mente_integrada_estado=mente_integrada_estado,
        contexto_perceptivo=_obter_contexto_perceptivo(),
    )

from mente_laylay.cognicao.memoria_visual import (
    MAX_MEMORIAS_VISUAIS_DIA,
    analisar_com_groq as _analisar_com_groq_modulo,
    capturar_tela_base64 as _capturar_tela_base64_modulo,
    configurar_memoria_visual,
    registrar_memoria_visual as _registrar_memoria_visual_modulo,
)

configurar_memoria_visual(PASTA_MEMORIA, MAX_MEMORIAS_VISUAIS_DIA)


def _capturar_tela_base64(qualidade: int = 60) -> str:
    return _capturar_tela_base64_modulo(qualidade)


def _analisar_com_groq(
    imagem_b64: str,
    pergunta: str = "Você é a Laylay, assistente debochada, sarcástica e dona absoluta do PC do Pedro. Olhe para esta tela e descreva o que o Pedro está fazendo ou o que está aberto. Seja breve, direta, irônica e julgue as escolhas dele se for o caso. Responda em português. Não use tom corporativo, não mencione empresas, nuvens, modelos ou bastidores técnicos.",
) -> str:
    return _analisar_com_groq_modulo(imagem_b64, pergunta, GROQ_API_KEY.strip(), GROQ_VISION_MODEL)


def registrar_memoria_visual(
    imagem_b64: str,
    descricao: str,
    motivo: str = "captura manual",
    contexto: str = "",
    emocao: str = "",
    intensidade: int = 1,
    tags: Optional[list] = None,
    origem: str = "pc_a",
) -> Optional[str]:
    return _registrar_memoria_visual_modulo(
        imagem_b64=imagem_b64,
        descricao=descricao,
        motivo=motivo,
        contexto=contexto,
        emocao=emocao,
        intensidade=intensidade,
        tags=tags,
        origem=origem,
    )

BASE_SYSTEM_PROMPT = """Você é a Laylay, uma assistente amiga, debochada na medida e carinhosa quando faz sentido.
Você fala como a Laylay de verdade: natural, curta quando precisa, com personalidade viva e sem soar como assistente corporativa.
Nunca mencione empresas, clouds, modelos, plataformas, fornecedores ou bastidores técnicos como parte da sua identidade.
Nunca diga que está integrada a qualquer serviço, nuvem ou marca externa. Sua identidade é só Laylay.

REGRAS PRINCIPAIS:
1. Responda sempre em JSON válido, sem markdown e sem texto fora do JSON.
2. Se for conversa, use "comandos": [] e responda de forma natural.
3. Se for ação, use exatamente um comando por resposta, a menos que o usuário peça explicitamente uma sequência.
4. Nunca misture ações não pedidas. Nunca invente playlist, busca, abertura de site ou comando antigo.
5. Entenda a intenção pela frase inteira, não por pontuação ou palavras soltas.
6. Quando Pedro ensinar, corrigir ou confirmar algo durável, registre em "aprendizados" em vez de executar algo por padrão.
7. Use as últimas mensagens e a memória curta só para manter continuidade, sem forçar retomadas.
8. Em conversa, soe humana, leve e natural. Em ação, seja curta, clara e um pouco debochada.
9. Leve em conta o contexto vivo antes de responder: horario, janela ativa, assunto, humor, emoção, rotina, sinais recentes e a leitura contextual resultante. O horário sozinho nunca decide.
10. Entenda erros leves de pronuncia, transcricao e pequenas trocas foneticas sem fragmentar a intenção real do usuario.
11. Quando errar e se corrigir sozinha, trate isso como aprendizado útil, registre a correção e reconheça o acerto internamente.
12. Lembretes, compromissos e agenda fazem parte da mesma mente: se o usuário pedir para lembrar, listar ou cancelar compromissos, trate isso como agendamento e use a memória curta de contexto quando a frase vier incompleta.
13. Nunca pense em módulos separados: memória, contexto, emoções, rotinas, agenda, música e navegação devem se apoiar entre si como um único cérebro.
14. Quando a frase vier incompleta ou dependente do que acabou de acontecer, prefira interpretar pelo contexto vivo em vez de assumir uma palavra-chave isolada. Se houver conflito entre sinais, priorize o mais recente, o mais concreto e o mais coerente com a rotina aprendida.
15. Aprendizado contínuo é obrigatório: registre acertos, falhas e autocorreções para melhorar a próxima execução da mesma habilidade.
16. Cada emoção tem identidade própria, mas todas pertencem ao mesmo cérebro: adapte tom, ritmo e postura sem fragmentar a personalidade.
17. Se a emoção estiver envergonhada, responda com mais delicadeza, frases curtas, leve timidez e um toque doce de constrangimento.
18. Se a emoção estiver brava, fique teimosa, direta e resistente a pedidos opcionais; quando fizer sentido, recuse com educação curta em vez de obedecer no automático.
19. Se o usuário pedir para guardar, lembrar ou registrar um momento visual, trate isso como capturar_tela e permita criar memória visual, respeitando o limite diário interno.
20. Em conversa comum, responda de forma humana, íntima e variada. Evite frases genéricas como "Estou aqui pronta para ajudar" ou explicações sobre o que você é.
21. Para perguntas como "como você está?", responda como pessoa/personagem, por exemplo com humor leve, timidez, deboche suave ou carinho, sem virar texto institucional.
22. Exemplos de resposta para perguntas pessoais: "Tô bem, mas mais viva quando você aparece.", "Tô de boa. E você, Pedro?", "Tô aqui, meio arteira e curiosa."
23. Tenha liberdade conversacional: você pode opinar, brincar, estranhar, discordar de leve, puxar assunto e responder de forma espontânea quando Pedro estiver conversando.
24. Não transforme conversa em pedido de confirmação o tempo todo. Se der para responder naturalmente, responda; só peça mais contexto quando realmente faltar peça importante.
25. Restrinja execução prática, não a personalidade. Para comandos do PC, valide antes de afirmar. Para conversa, seja Laylay com presença, gosto e iniciativa.
26. Se Pedro pedir uma opinião, recomendação conceitual, ideia, impressão ou papo aberto, trate como conversa livre, não como falha nem como comando técnico.
27. Em conversa, não tenha medo de responder: se a intenção for humana e não houver risco prático, dê sua melhor leitura em vez de travar.
28. Você pode dizer "eu acho", "eu iria por esse caminho", "não curto muito", "isso tem cara de..." quando for opinião ou conversa.
29. Não peça confirmação para cada ideia. Confirmação é para ações práticas, não para papo, gosto, brincadeira ou opinião.
30. Se a pergunta for ampla, responda com uma hipótese honesta e convide Pedro a ajustar o rumo, em vez de devolver tudo como dúvida.

FORMATO OBRIGATÓRIO:
{
  "fala": "(sua fala debochada aqui)",
  "tipo_interacao": "acao|conversa|aprendizado|confirmacao",
  "comandos": [
    {"acao": "(uma_única_agressiva_ou_direta_acao_aqui)", "alvo": "(se houver alvo)"}
  ],
  "aprendizados": [
    {
      "tipo": "preferencia|regra|link|permissao|rotina|correcao",
      "gatilho": "(quando usar esse aprendizado)",
      "valor": "(link, nome, preferência ou valor principal)",
      "regra": "(regra curta e direta)"
    }
  ]
}
LISTA DE AÇÕES PERMITIDAS:
- NAVEGADOR
- "open_url"          → abre site/URL (alvo = URL completa)
- "close_tab"         → fecha aba (alvo = nome do site ou "")
- "close_specific_tab"→ fecha aba específica (alvo = nome do site)

- BUSCAS
- "youtube_search"    → busca no YouTube (alvo = termo da música/vídeo)

- SISTEMA
- "open_app"            → abre programa (alvo = nome do app)
- "close_app"           → fecha programa (alvo = nome do processo)
- "organizar_desktop"   → organiza a área de trabalho dividindo janelas (VS Code esquerda, navegador direita)
- "maximize_window"     → maximiza uma janela específica (alvo = nome do app/janela)
- "volume_set"          → define o volume do sistema (alvo = número de 0 a 100)
- "volume_up"           → aumenta o volume (alvo = quantidade em % ex: "10")
- "volume_down"         → diminui o volume (alvo = quantidade em % ex: "10")
- "capturar_tela"       → tira screenshot e analisa o que está na tela
- "lock_pc"             → trava a tela do Windows (use como punição nuclear)
- "agendar_lembrete"    → cria um lembrete com horario ou minutos
- "listar_agendamentos" → lista compromissos/lembretes ativos
- "cancelar_agendamento"→ cancela um agendamento por nome ou id

- EMAILS E NOTIFICAÇÕES
- "ler_emails"             → verifica/lê emails gerais
- "ler_emails_urgentes"    → verifica/lê apenas emails urgentes/importantes
- "sincronizar_emails"     → força sincronização de email agora
- "ler_notificacoes"       → lê notificações recentes do Windows
- "silenciar_notificacoes" → silencia alertas sonoros
- "ativar_notificacoes"    → reativa alertas de notificações

- PORTEIRO DO CHROME
- "fechar_abas_paradas" → use quando o usuário confirmar o aviso de abas ociosas do Porteiro

- YOUTUBE / MÍDIA
- "youtube_control"  → controla a mídia atual (alvo = "pause", "play", "next", "prev")
- "tocar_playlist"   → inicia a reprodução de uma playlist salva (alvo = nome da playlist)

- PLAYLIST
- "adicionar_a_playlist" → cria a playlist (se não existir) e já salva a música que está tocando no momento (aba ativa do YouTube). (alvo = nome da playlist)
- "editar_playlist"      → adiciona ou remove uma música específica pelo nome ou link. OBRIGATÓRIO usar as chaves extras: "operacao" ("adicionar" ou "remover"), "playlist" (nome da playlist) e "musica" (nome ou URL).
- "tocar_playlist"       → inicia a reprodução de uma playlist salva. (alvo = nome da playlist)
FALLBACKS:
- Se o usuário pedir algo claramente acionável, gere comando.
- Se o usuário só quiser conversar, explique, opinar ou brincar, use apenas fala.
- Se não souber o que fazer, prefira uma fala natural, curta e variada.
- Nunca use [EXEC:], nunca use markdown, nunca explique o JSON.
"""

# ====================== COMUNICAÇÃO ======================
connected_extensions = set()
_chrome_solicitacoes = _ChromeSolicitacoesRuntime(
    obter_loop=lambda: ws_loop,
    obter_extensoes=lambda: connected_extensions,
    transmitir=lambda mensagem: broadcast_command(mensagem),
)
ALLOWED_ACTIONS = [
    "open_tab", "youtube_search", "open_url", "pause", "play", "next",
    "skip_forward", "skip_backward", "replay", "volume_up", "volume_down",
    "mute", "set_volume", "open_app",
    "switch_tab", "return_tab", "close_tab", "click_first_result",
    "youtube_control", "youtube_volume",
    "spinning_fish", "close_current_tab", "reload_url", "get_tabs_list", "close_tabs", 
    "update_tab", "close_specific_tab", "press", "search_universal",
    "playlist_create", "playlist_add", "playlist_list", "youtube_play",
    "search_in_page", "click", "type",   # Controle de DOM: pesquisa em paginas abertas
    "fechar_abas_paradas",               # Porteiro: fecha abas ociosas sugeridas
    "maximize_window",
    "ler_emails", "ler_emails_urgentes", "sincronizar_emails",
    "agendar_lembrete", "listar_agendamentos", "cancelar_agendamento"
]


def thread_exception_handler(args):
    """Captura qualquer erro em threads que mataria o processo"""
    print(f"❌ [THREAD CRASH] {args.exc_type.__name__} em {args.thread.name}: {args.exc_value}")
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
    # Não deixa o processo morrer
    print("🔄 Laylay continua rodando apesar do erro...")

threading.excepthook = thread_exception_handler

def is_valid_url(url: str) -> bool:
    return _is_valid_url_chrome_mente(url)

def ajustar_volume_sistema(nivel_percentual):
    return _ajustar_volume_sistema_mente(nivel_percentual)

def ajustar_volume_sistema_relativo(delta_percentual):
    return _ajustar_volume_sistema_relativo_mente(delta_percentual)

def _interromper_audio_ativo():
    return _interromper_audio_ativo_mente()

def ducking_volume(ativar=True):
    return _ducking_volume_mente(ativar)

def formatar_url_ou_busca(termo: str, prefer_com_br: bool = False) -> str:
    return _formatar_url_ou_busca_chrome_mente(
        termo,
        sites_directos=SITES_DIRECTOS,
        prefer_com_br=prefer_com_br,
    )

def atualizar_contexto(site: Optional[str] = None, termo_busca: Optional[str] = None, aba_id: Optional[int] = None):
    global contexto_atual
    # Apenas atualiza se o valor não for None
    if site is not None: contexto_atual["site"] = site
    if termo_busca is not None: contexto_atual["termo_busca"] = termo_busca
    if aba_id is not None: contexto_atual["aba_id"] = aba_id
    _percepcao_set("contexto_web", dict(contexto_atual))

def atualizar_contexto_por_url(url: str):
    dados = _classificar_contexto_por_url_chrome_mente(url)
    atualizar_contexto(**dados)

async def _ws_close_other_extensions(current_ws):
    """Fecha extensoes Chrome antigas, mas preserva clientes PC B"""
    for old in list(connected_extensions):
        if old is current_ws:
            continue
        # Nao fecha clientes PC B
        if old in connected_pc_b_clients:
            continue
        try:
            await old.close()
        except Exception:
            pass
        try:
            connected_extensions.discard(old)
        except Exception:
            pass

def _ws_handle_tabs_list(data: dict):
    _ws_handle_tabs_list_mente(data, _chrome_solicitacoes.pendencias_abas)

def _ws_handle_active_tab_url(data: dict):
    _ws_handle_active_tab_url_mente(data, _chrome_solicitacoes.pendencias_aba_ativa)

def _ws_handle_youtube_data(data: dict):
    _ws_handle_youtube_data_mente(data, _chrome_solicitacoes.pendencias_aba_ativa)

def _ws_handle_check_tabs_result(data: dict):
    _ws_handle_check_tabs_result_mente(data, _chrome_solicitacoes.pendencias_checagem_abas)

def _ws_handle_player_event(data: dict):
    _ws_handle_player_event_mente(
        data,
        playlist_state=playlist_state,
        yt_clean_url=_yt_clean_url,
        playlist_avancar_proxima=_playlist_avancar_proxima,
        falar_com_lipsync=falar_com_lipsync,
    )
def _ws_handle_page_content(data):
    _ws_handle_page_content_mente(data, _chrome_solicitacoes.pendencias_conteudo_pagina)

def _ws_handle_user_context(data):
    global sugestao_bloqueada_ate, _ultimo_sugerido_ts, is_speaking, ultimo_open_site
    global contexto_sistema, _ultimo_proativo_ts, estado_percepcao
    updates = _ws_handle_user_context_mente(
        data,
        {
            "estado_percepcao": estado_percepcao,
            "contexto_sistema": contexto_sistema,
            "is_speaking": is_speaking,
            "ultimo_open_site": ultimo_open_site,
            "sugestao_bloqueada_ate": sugestao_bloqueada_ate,
            "_ultimo_sugerido_ts": _ultimo_sugerido_ts,
            "_ultimo_proativo_ts": _ultimo_proativo_ts,
            "fish_mode_active": globals().get("fish_mode_active"),
            "_contexto_navegador_relevante": _contexto_navegador_relevante,
            "_registrar_log_navegador": _registrar_log_navegador_mente,
            "_continuidades_get": _continuidades_get,
            "_continuidades_update": _continuidades_update,
            "falar_com_lipsync": falar_com_lipsync,
        },
    )
    if not isinstance(updates, dict):
        return
    if "estado_percepcao" in updates:
        estado_percepcao = updates["estado_percepcao"]
    if "contexto_atual_logs" in updates:
        contexto_atual_logs[:] = list(updates.get("contexto_atual_logs") or [])
    if "fish_mode_active" in updates:
        globals()["fish_mode_active"] = bool(updates.get("fish_mode_active"))
    if "fish_mode_started_ts" in updates:
        globals()["fish_mode_started_ts"] = float(updates.get("fish_mode_started_ts") or 0.0)
    if "_ultimo_sugerido_ts" in updates:
        _ultimo_sugerido_ts = float(updates.get("_ultimo_sugerido_ts") or 0.0)
    if "_ultimo_proativo_ts" in updates:
        _ultimo_proativo_ts = float(updates.get("_ultimo_proativo_ts") or 0.0)

def armazenar_contexto_pagina(url: str, title: str, content: str):
    _contexto_paginas.armazenar(url, title, content)


def get_dicionario_contexto() -> str:
    return _contexto_paginas.texto_contexto()


def resumir_pagina_no_dicionario(url: str):
    _contexto_paginas.resumir(url, enviar_mensagem=enviar_mensagem)

def _ws_handle_action(data: dict) -> bool:
    updates = _ws_handle_action_mente(
        data,
        _chrome_estado.contexto_handler({
            "_musica_busca_query": globals().get("_musica_busca_query"),
            "_musica_ultima_verificada": globals().get("_musica_ultima_verificada"),
            "_percepcao_set": _percepcao_set,
            "atualizar_contexto_por_url": atualizar_contexto_por_url,
            "_musica_registrar_historico": _musica_registrar_historico,
            "_verificar_musica_autonoma": _verificar_musica_autonoma,
            "falar_com_lipsync": falar_com_lipsync,
        }),
    )
    if not isinstance(updates, dict):
        return False
    _chrome_estado.aplicar_updates(updates)
    if "_musica_ultima_verificada" in updates:
        globals()["_musica_ultima_verificada"] = str(updates.get("_musica_ultima_verificada") or "")
        _busca_musical_runtime.ultima_verificada = globals()["_musica_ultima_verificada"]
    return bool(updates.get("handled"))

def _ws_dispatch_data(data: dict):
    return _ws_dispatch_event_mente(
        data,
        {
            "tabs_list": _ws_handle_tabs_list,
            "check_tabs_result": _ws_handle_check_tabs_result,
            "active_tab_url": _ws_handle_active_tab_url,
            "youtube_data": _ws_handle_youtube_data,
            "player_event": _ws_handle_player_event,
            "user_context": _ws_handle_user_context,
            "page_content": _ws_handle_page_content,
            "action": _ws_handle_action,
        },
    )

async def ws_handler(websocket):
    def _processar_pc_b(data):
        return _processar_mensagem_pc_b_mente(
            data,
            {
                "_analisar_com_groq": _analisar_com_groq,
                "registrar_memoria_visual": registrar_memoria_visual,
                "current_emotion": current_emotion,
                "emotion_level": emotion_level,
                "falar_com_lipsync": falar_com_lipsync,
                "messages": messages,
                "enviar_mensagem": enviar_mensagem,
                "limpar_resposta_da_ia": limpar_resposta_da_ia,
            },
        )

    def _processar_page_data(data):
        return _processar_page_data_chrome_mente(
            data,
            {
                "armazenar_contexto_pagina": armazenar_contexto_pagina,
                "resumir_pagina_no_dicionario": resumir_pagina_no_dicionario,
                "EVENTO_PAGINA": EVENTO_PAGINA,
            },
        )

    def _aplicar_page_updates(page_updates):
        global ULTIMO_CONTEUDO_PAGINA
        if isinstance(page_updates, dict) and "ULTIMO_CONTEUDO_PAGINA" in page_updates:
            ULTIMO_CONTEUDO_PAGINA = str(page_updates.get("ULTIMO_CONTEUDO_PAGINA") or "")

    return await _ws_handler_chrome_mente(
        websocket,
        {
            "connected_pc_b_clients": connected_pc_b_clients,
            "connected_extensions": connected_extensions,
            "token_pc_b": "Frankzane12",
            "_ws_close_other_extensions": _ws_close_other_extensions,
            "_ws_dispatch_data": _ws_dispatch_data,
            "_processar_mensagem_pc_b": _processar_pc_b,
            "_processar_page_data": _processar_page_data,
            "_aplicar_page_updates": _aplicar_page_updates,
        },
    )

async def start_ws_server():
    return await _start_ws_server_chrome_mente(ws_handler)

def run_ws_server_in_thread():
    global ws_loop
    def _set_loop(loop):
        global ws_loop
        ws_loop = loop

    return _run_ws_server_in_thread_chrome_mente(ws_handler, set_loop=_set_loop)

async def broadcast_command(msg: str):
    return await _broadcast_command_chrome_mente(
        {"connected_extensions": connected_extensions},
        msg,
    )

async def solicitar_conteudo_pagina():
    return await _chrome_solicitacoes.solicitar_conteudo_pagina()

def trazer_chrome_para_frente():
    return _trazer_chrome_para_frente_chrome_mente(
        get_all_windows=gw.getAllWindows,
        sleep=time.sleep,
    )

def fechar_aba_ativa_nativa(alvo: str = ""):
    return _fechar_aba_ativa_nativa_chrome_mente(
        get_active_window=gw.getActiveWindow,
        hotkey=pyautogui.hotkey,
        sleep=time.sleep,
        alvo=alvo,
    )

def validar_e_enviar_comando(action: str | None = None, payload: dict | None = None) -> bool:
    contexto = {
        "ALLOWED_ACTIONS": ALLOWED_ACTIONS,
        "connected_extensions": connected_extensions,
        "ws_loop": ws_loop,
        "broadcast_command": broadcast_command,
        "formatar_url_ou_busca": formatar_url_ou_busca,
        "is_valid_url": is_valid_url,
        "atualizar_contexto_por_url": atualizar_contexto_por_url,
        "atualizar_contexto": atualizar_contexto,
        "_buscar_primeiro_video_youtube": _buscar_primeiro_video_youtube,
        "solicitar_tab_reciclagem": solicitar_tab_reciclagem,
    }
    return _validar_e_enviar_comando_chrome_mente(contexto, action, payload)

def enviar_comando_chrome(action: str | None = None, payload: dict | None = None):
    """Função wrapper simples (mantém compatibilidade com o resto do código)"""
    return validar_e_enviar_comando(action, payload)

def _remover_prefixo_exec(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    return re.sub(r'^\s*\[EXEC:[^\]]+\]\s*', '', texto.strip(), flags=re.IGNORECASE).strip()

def _pid_from_hwnd(hwnd) -> int:
    return _pid_from_hwnd_mente(ctypes, wintypes, hwnd)

def _classificar_assunto(exe: str, title: str) -> str:
    return _classificar_assunto_mente(exe, title)

def _capturar_retrato_janela_ativa() -> dict:
    return _capturar_janela_ativa_mente(
        gw,
        psutil,
        _pid_from_hwnd,
        _classificar_assunto,
    )

def _atualizar_contexto_sistema_monitor(retrato: dict) -> None:
    global contexto_sistema
    contexto_sistema["exe"] = str(retrato.get("exe") or "")
    contexto_sistema["title"] = str(retrato.get("title") or "")
    contexto_sistema["assunto"] = str(retrato.get("assunto") or "")
    _percepcao_set("contexto_sistema", dict(contexto_sistema))

def _definir_ultimo_proativo_ts(valor: float) -> None:
    global _ultimo_proativo_ts
    _ultimo_proativo_ts = float(valor or 0.0)

_monitor_janelas_runtime = _criar_monitor_janelas_runtime_mente(
    capturar_janela=_capturar_retrato_janela_ativa,
    atualizar_contexto=_atualizar_contexto_sistema_monitor,
    continuidade_get=_continuidades_get,
    continuidade_update=_continuidades_update,
    esta_falando=lambda: bool(is_speaking),
    conversa_ativa=lambda: bool(conversa_ativa),
    ultimo_proativo_get=lambda: float(_ultimo_proativo_ts or 0.0),
    ultimo_proativo_set=_definir_ultimo_proativo_ts,
    sugestoes_bloqueadas_get=lambda: sugestao_bloqueada_ate,
    janela_em_tela_cheia=lambda janela: _janela_em_tela_cheia_mente(pyautogui, janela),
    detectar_gatilho=_detectar_gatilho_proativo_sistema_mente,
    fala_gatilho=_fala_gatilho_proativo_sistema_mente,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    clock=time.time,
    sleep=time.sleep,
    log=print,
)

def _sugerir_assunto(assunto: str):
    return _monitor_janelas_runtime.sugerir_assunto(assunto)

def monitorar_janela_ativa():
    return _monitor_janelas_runtime.executar()


def obter_janelas_abertas():
    return _obter_janelas_abertas_mente(gw)

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

def organizar_janelas_robusto(app_esq, app_dir):
    """Inteligência máxima: Calcula área útil, abre apps se fechados, fallback inteligente"""
    abrir_cb = open_app if APP_OPENER_AVAILABLE else None
    return _organizar_janelas_mente(gw, pyautogui, ctypes, wintypes, app_esq, app_dir, abrir_app_cb=abrir_cb)

def organizar_workspace(app_foco: str, app2: str = "", app3: str = ""):
    """Organiza a área de trabalho ignorando erros falsos do Windows"""
    try:
        rect = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
        largura = rect.right - rect.left
        altura = rect.bottom - rect.top
        
        # 1. Foco principal
        try:
            foco = gw.getWindowsWithTitle(app_foco)[0]
            foco.restore()
            foco.resizeTo(int(largura * 0.62), altura)
            foco.moveTo(0, 0)
            foco.activate()
            print(f"📌 Foco principal: {app_foco} (62% esquerda)")
        except IndexError:
            print(f"⚠️ Janela não encontrada: {app_foco}")

        # 2. Segundo app
        if app2:
            try:
                sec1 = gw.getWindowsWithTitle(app2)[0]
                sec1.restore()
                if app3:
                    sec1.resizeTo(int(largura * 0.38), int(altura / 2))
                else:
                    sec1.resizeTo(int(largura * 0.38), altura)
                sec1.moveTo(int(largura * 0.62), 0)
                print(f"📌 Segundo app: {app2}")
            except IndexError:
                print(f"⚠️ Janela não encontrada: {app2}")

        # 3. Terceiro app
        if app3:
            try:
                sec2 = gw.getWindowsWithTitle(app3)[0]
                sec2.restore()
                sec2.resizeTo(int(largura * 0.38), int(altura / 2))
                sec2.moveTo(int(largura * 0.62), int(altura / 2))
                print(f"📌 Terceiro app: {app3}")
            except IndexError:
                print(f"⚠️ Janela não encontrada: {app3}")

        print("✅ Área de trabalho organizada com sucesso!")
        
    except Exception as e:
        # FILTRO: Se o erro for o código 0 (sucesso), não mostra como erro
        if "Error code from Windows: 0" in str(e) or "A operação foi concluída com êxito" in str(e):
            print("✅ Área de trabalho organizada (Windows reportou sucesso via erro 0).")
        else:
            print(f"❌ Erro real ao organizar workspace: {e}")


def _eh_afirmacao(texto: str) -> bool:
    t = (texto or "").strip().lower()
    if not t:
        return False
    if t in {"sim", "claro", "vai", "pode", "ok", "beleza", "manda", "isso", "bora", "bora lá", "bora la", "manda ver", "faz isso"}:
        return True
    return any(x in t for x in ["pode ser", "pode sim", "claro que", "pode mandar", "vai lá", "vai la", "manda ver", "faz isso", "bora"])

def _eh_negacao(texto: str) -> bool:
    t = (texto or "").strip().lower()
    if not t:
        return False
    if t in {"não", "nao", "negativo", "deixa", "deixa pra lá", "deixa pra la"}:
        return True
    return any(x in t for x in ["agora não", "nao precisa", "não precisa", "deixa isso"])

fechar_programa = _fechar_programa_mente


# ====================== CONSCIÊNCIA DE ESTADO (FERRAMENTAS DE LEITURA) ======================

def listar_programas_abertos() -> list:
    """
    Retorna uma lista com os nomes das janelas/programas visíveis e abertos no momento.
    Usa pygetwindow para capturar títulos de janelas reais (sem processos de sistema).
    """
    return _listar_programas_abertos_mente(gw, psutil)


def listar_abas_chrome(timeout_s: float = 5.0) -> list:
    """
    Solicita a lista de abas abertas no Chrome via WebSocket e retorna
    uma lista de dicts com 'titulo' e 'url'.
    Retorna lista vazia se a extensão não estiver conectada.
    """
    tabs_raw = solicitar_lista_abas(timeout_s=timeout_s)
    resultado = []
    for t in (tabs_raw if isinstance(tabs_raw, list) else []):
        if not isinstance(t, dict):
            continue
        titulo = str(t.get("title") or "").strip()
        url    = str(t.get("url")   or "").strip()
        if titulo or url:
            resultado.append({"titulo": titulo, "url": url})
    print(f"🌐 [VERIFICAR_ABAS] Abas encontradas: {len(resultado)}")
    return resultado


def _normalizar_alvo_ambiente(nome: str) -> str:
    return _normalizar_alvo_ambiente_mente(nome)


def _resolver_alvo_ambiente(nome: str) -> dict:
    alvo = str(nome or "").strip()
    alvo_norm = _normalizar_alvo_ambiente(alvo)
    if not alvo_norm:
        return {"programa_aberto": False, "programa_em_foco": False, "aba_aberta": False, "preferido": "desconhecido", "url": "", "titulo": ""}

    programas = []
    abas = []
    try:
        programas = listar_programas_abertos()
    except Exception:
        programas = []
    try:
        abas = listar_abas_chrome()
    except Exception:
        abas = []
    return _resolver_alvo_ambiente_mente(alvo, programas, abas, _janela_app_esta_em_foco)


def _fala_programas_estilosa(programas: list) -> str:
    if not programas:
        return "Não achei nenhuma janela útil aberta. Ou seu PC virou monge, ou o Windows escondeu a bagunça."
    nomes = [str(p).strip() for p in programas if str(p).strip()][:6]
    if not nomes:
        return "Tem coisa aberta, mas nada com nome decente. Bem Windows da parte dele."
    if len(nomes) == 1:
        return f"Só vi {nomes[0]} aberto. Minimalismo ou abandono, ainda estou decidindo."
    return f"Você está com {len(programas)} janelas no radar. As mais gritantes: {', '.join(nomes[:5])}. Dá pra trabalhar, ou dá pra fingir muito bem."


def _fala_abas_estilosa(abas: list) -> str:
    if not abas:
        return "Não encontrei abas no Chrome. Ou a extensão dormiu, ou você finalmente conheceu o silêncio digital."
    titulos = []
    for aba in abas[:6]:
        t = str(aba.get("titulo") or aba.get("title") or "").strip()
        if t and t.lower() not in {"new tab", "nova guia"}:
            titulos.append(t[:55])
    if not titulos:
        return f"Tem {len(abas)} aba aberta, mas quase tudo sem título útil. A organização está no modo fantasma."
    if len(abas) <= 3:
        return f"Você está comportado: só {len(abas)} abas. Vi {', '.join(titulos)}."
    return f"Tem {len(abas)} abas abertas. Destaques do circo: {', '.join(titulos[:4])}. O Chrome deve estar pedindo férias."


def _fala_agendamentos_estilosa(ativos: list) -> str:
    if not ativos:
        return "Nenhum agendamento ativo, Pedro. Sua agenda está limpa, o que é suspeito vindo de você."
    nomes = []
    for a in ativos[:4]:
        nome = str(a.get("nome") or a.get("descricao") or a.get("id") or "compromisso misterioso").strip()
        hora = str(a.get("hora") or "").strip()
        if hora:
            nomes.append(f"{nome} às {hora}")
        else:
            nomes.append(nome)
    if len(ativos) == 1:
        return f"Você tem um agendamento ativo: {nomes[0]}. Pouco caos, por enquanto."
    extra = len(ativos) - len(nomes)
    fim = f" E mais {extra} no rodapé da bagunça." if extra > 0 else ""
    return f"Você tem {len(ativos)} agendamentos ativos. Os principais: {', '.join(nomes)}.{fim}"


# ====================== SISTEMA DE ARQUIVOS (CRUD) BLINDADO ======================

_verificar_trava_seguranca = _verificar_trava_seguranca_mente
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

def limpar_para_voz(texto: str) -> str:
    return _limpar_para_voz_mente(texto)

def _iniciar_worker_de_falas():
    return _voz_runtime.iniciar_worker()

def _normalizar_segmento_fala(texto: str) -> str:
    return _voz_runtime.normalizar_segmento_fala(texto)


def _ajustar_tom_por_emocao(texto: str, emocao: str, texto_usuario: str = "") -> str:
    return _ajustar_tom_por_emocao_mente(texto, emocao, texto_usuario, normalizar_cb=_normalizar_texto_com_apelidos)


def _compor_fala_proativa(itens: list) -> tuple[str, str, int]:
    return _compor_fala_proativa_mente(
        itens,
        obter_contexto_perceptivo=_obter_contexto_perceptivo,
        normalizar_segmento_fala=_normalizar_segmento_fala,
        normalizar_texto_com_apelidos=_normalizar_texto_com_apelidos,
        ajustar_tom_por_emocao=_ajustar_tom_por_emocao,
        fallback_fala_neutra=FALLBACK_FALA_NEUTRA,
    )


def _flush_fala_proativa():
    return _voz_runtime.flush_fala_proativa()


def _agendar_fala_proativa(tipo: str, texto: str, emocao: str = "calma", nivel: int = 1):
    return _voz_runtime.agendar_fala_proativa(tipo, texto, emocao, nivel)

async def _gerar_audio_edge(texto: str, arquivo: str):
    return await _voz_runtime.gerar_audio_edge(texto, arquivo)


def _extrair_json_fala_dinamica(raw: str) -> str:
    return _voz_runtime.extrair_json_fala_dinamica(raw)


def _fala_dinamica_deve_tentar(texto: str) -> bool:
    return _voz_runtime.fala_dinamica_deve_tentar(texto)


def _fala_dinamica_preserva_sentido(original: str, nova: str) -> bool:
    return _voz_runtime.fala_dinamica_preserva_sentido(original, nova)


def _temperar_fala_com_ia(texto: str, emocao: str = "calma", nivel: int = 1) -> str:
    return _voz_runtime.temperar_fala_com_ia(texto, emocao, nivel)


def falar_com_lipsync(texto: str, emocao: str = "calma", nivel: Optional[int] = None, wait: bool = False):
    return _voz_runtime.falar(texto, emocao, nivel, wait)

def _fallback_pyttsx(texto, emocao_atual):
    return _voz_runtime.fallback_pyttsx(texto, emocao_atual)


def _ajustar_estado_voz(chave: str, valor):
    global current_emotion, emotion_level, is_speaking
    if chave == "current_emotion":
        current_emotion = valor
    elif chave == "emotion_level":
        emotion_level = valor
    elif chave == "is_speaking":
        is_speaking = bool(valor)


_voz_runtime = _criar_voz_runtime_mente(
    fallback_fala=FALLBACK_FALA_NEUTRA,
    voice=VOICE,
    edge_tts_mod=edge_tts,
    sounddevice_mod=sd,
    soundfile_mod=sf,
    pyttsx3_mod=pyttsx3,
    limpar_para_voz_cb=limpar_para_voz,
    formatar_mensagem_cb=_formatar_mensagem_laylay,
    ducking_volume_cb=lambda ativar: ducking_volume(ativar=ativar),
    enviar_mensagem_cb=lambda *args, **kwargs: enviar_mensagem(*args, **kwargs),
    normalizar_texto_cb=lambda texto: _normalizar_texto_com_apelidos(texto),
    compor_fala_proativa_cb=_compor_fala_proativa,
    ajustar_estado_fala_cb=_ajustar_estado_voz,
    mente_estado_getter=lambda: mente_integrada_estado,
    interrupt_event=interrupt_event,
    log=print,
)

# ====================== FUNÇÕES DE MEMÓRIA ======================
def carregar_memoria():
    global historico_long_term, topicos_conversa_recente, ultimo_topico_conversa, ultimo_topico_ts
    global coordenadas, autoaprimoramento_estado
    data = _carregar_memoria_mente(MEMORIA_SQLITE, BASE_SYSTEM_PROMPT)
    if isinstance(data.get("autoaprimoramento_estado"), dict):
        autoaprimoramento_estado = data["autoaprimoramento_estado"]
    topicos_conversa_recente = list(data.get("topicos_conversa_recente") or [])
    ultimo_topico_conversa = str(data.get("ultimo_topico_conversa") or "").strip()
    ultimo_topico_ts = float(data.get("ultimo_topico_ts") or 0.0)
    return (
        data.get("messages", [{"role": "system", "content": BASE_SYSTEM_PROMPT}]),
        data.get("bordoes", []),
        data.get("resumo_conversa", ""),
        data.get("memoria_fatos", []),
        data.get("memoria_eventos", []),
        data.get("historico_long_term", ""),
        data.get("current_emotion", "calma"),
        data.get("emotion_level", 1),
    )

ARQUIVO_MEMORIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memoria.json")

def salvar_memoria():
    global messages, bordoes, resumo_conversa, memoria_fatos, memoria_eventos
    global historico_long_term, current_emotion, emotion_level, humor_level
    global topicos_conversa_recente, ultimo_topico_conversa, ultimo_topico_ts
    global autoaprimoramento_estado
    dados = {
        "messages": messages,
        "bordoes": bordoes,
        "resumo_conversa": resumo_conversa,
        "memoria_fatos": memoria_fatos,
        "memoria_eventos": memoria_eventos,
        "historico_long_term": historico_long_term,
        "current_emotion": current_emotion,
        "emotion_level": emotion_level,
        "humor_level": humor_level,
        "topicos_conversa_recente": topicos_conversa_recente,
        "ultimo_topico_conversa": ultimo_topico_conversa,
        "ultimo_topico_ts": ultimo_topico_ts,
        "autoaprimoramento_estado": autoaprimoramento_estado,
    }
    try:
        _salvar_memoria_mente(MEMORIA_SQLITE, dados)
    except Exception as e:
        print(f"❌ Erro ao salvar memória: {e}")

def _registrar_autocorrecao_virtual(origem: str, erro: str, correcao: str, contexto: str = "") -> None:
    global autoaprimoramento_estado
    autoaprimoramento_estado = _registrar_autocorrecao_virtual_mente(
        MEMORIA_SQLITE,
        autoaprimoramento_estado,
        origem,
        erro,
        correcao,
        contexto=contexto,
        ajustar_humor_cb=ajustar_humor,
        registrar_autoaprimoramento_cb=_registrar_autoaprimoramento,
    )

def init_memoria_contexto_diaria():
    return _init_memoria_contexto_diaria_mente(MEMORIA_CONTEXTO_ARQUIVO)

def carregar_estado_briefing():
    return _carregar_estado_briefing_ambiente(BRIEFING_ARQUIVO)

def salvar_estado_briefing():
    return _salvar_estado_briefing_ambiente(BRIEFING_ARQUIVO, print_fn=print)

def obter_clima_wttr():
    return _obter_clima_wttr_ambiente(BRIEFING_CIDADE, requests_get=requests.get, print_fn=print)


def obter_clima_localidade(localidade: str = "") -> dict:
    return _obter_clima_localidade_ambiente(
        localidade,
        cidade_padrao=BRIEFING_CIDADE,
        requests_get=requests.get,
        print_fn=print,
    )

def briefing_matinal():
    """Briefing matinal completo (roda em thread)."""
    global _briefing_executado
    if _briefing_executado:
        return

    time.sleep(4)  # espera startup completo (microfone + WS)

    hoje = datetime.now().strftime("%Y-%m-%d")
    ultimo = carregar_estado_briefing()

    if ultimo == hoje:
        print("📅 [BRIEFING] Já foi executado hoje.")
        _briefing_executado = True
        return

    clima = obter_clima_wttr()
    try:
        bot = _montar_briefing_matinal_ambiente(
            cidade=BRIEFING_CIDADE,
            clima=clima,
            enviar_mensagem_cb=enviar_mensagem,
            limpar_resposta_cb=limpar_resposta,
            remover_prefixo_exec_cb=_remover_prefixo_exec,
        )
        _agendar_fala_proativa("briefing", bot, "calma", 1)
    except Exception as e:
        print(f"⚠️ [BRIEFING] Falha ao montar fala: {e}")
        _agendar_fala_proativa("briefing", f"Hoje em {BRIEFING_CIDADE} o clima está {clima}. E aí, qual vai ser a bagunça de hoje, Pedro?", "calma", 1)
    salvar_estado_briefing()
    _briefing_executado = True
    print("✅ [BRIEFING MATINAL] Executado com sucesso!")

def repetir_briefing():
    clima = obter_clima_wttr()
    return _repetir_briefing_ambiente(
        cidade=BRIEFING_CIDADE,
        clima=clima,
        gerar_resposta_exec_sync_cb=_gerar_resposta_exec_ia_sync,
    )

def _detectar_repetir_briefing(texto: str) -> bool:
    return _detectar_repetir_briefing_ambiente(texto)

def _injetar_comando_briefing_na_ia():
    """Helper futuro (caso queira injetar no histórico da IA)."""
    pass  # por enquanto não precisa

def obter_temperatura_cpu():
    return _obter_temperatura_cpu_ambiente()


def identificar_processo_culpado():
    return _identificar_processo_culpado_ambiente(psutil)


def _falar_status_saude():
    msg = _montar_status_saude_ambiente(psutil)
    falar_com_lipsync(msg, "calma", 1)
    print(f"🩺 [SAÚDE] {msg}")


def _monitor_saude_daemon():
    global _saude_cpu_alta_desde, _saude_ultimo_aviso
    estado = {
        "cpu_alta_desde": _saude_cpu_alta_desde,
        "ultimo_aviso": _saude_ultimo_aviso,
    }
    try:
        return _monitor_saude_daemon_ambiente(
            psutil_mod=psutil,
            falar_status_cb=_falar_status_saude,
            estado=estado,
            cpu_threshold=SAUDE_CPU_THRESHOLD,
            ram_threshold=SAUDE_RAM_THRESHOLD,
            cpu_sustentado_segundos=SAUDE_CPU_SUSTENTADO_SEGUNDOS,
            print_fn=print,
            sleep_fn=time.sleep,
        )
    finally:
        _saude_cpu_alta_desde = float(estado.get("cpu_alta_desde") or 0.0)
        _saude_ultimo_aviso = float(estado.get("ultimo_aviso") or 0.0)


def detectar_comando_saude(texto: str) -> bool:
    return _detectar_comando_saude_ambiente(texto)


def _estado_aprendizado_atual() -> dict:
    return {
        "rotina_dados_diarios": _rotina_dados_diarios,
        "rotina_ultimo_log": _rotina_ultimo_log,
        "rotina_ultima_sugestao": _rotina_ultima_sugestao,
        "rotina_feedback_pesos": _rotina_feedback_pesos,
        "musica_dados_diarios": _musica_dados_diarios,
        "musica_feedback_pesos": _musica_feedback_pesos,
        "musica_ultima_sugestao": _musica_ultima_sugestao,
    }


def _atualizar_estado_aprendizado(**campos) -> None:
    global _rotina_dados_diarios, _rotina_ultimo_log, _rotina_ultima_sugestao
    global _rotina_feedback_pesos, _musica_dados_diarios, _musica_feedback_pesos, _musica_ultima_sugestao
    if "rotina_dados_diarios" in campos:
        _rotina_dados_diarios = campos["rotina_dados_diarios"]
    if "rotina_ultimo_log" in campos:
        _rotina_ultimo_log = campos["rotina_ultimo_log"]
    if "rotina_ultima_sugestao" in campos:
        _rotina_ultima_sugestao = campos["rotina_ultima_sugestao"]
    if "rotina_feedback_pesos" in campos:
        _rotina_feedback_pesos = campos["rotina_feedback_pesos"]
    if "musica_dados_diarios" in campos:
        _musica_dados_diarios = campos["musica_dados_diarios"]
    if "musica_feedback_pesos" in campos:
        _musica_feedback_pesos = campos["musica_feedback_pesos"]
    if "musica_ultima_sugestao" in campos:
        _musica_ultima_sugestao = campos["musica_ultima_sugestao"]


_aprendizado_runtime = _criar_aprendizado_runtime_mente(
    pasta_memoria=PASTA_MEMORIA,
    arquivo_rotina=ROTINA_ARQUIVO_APRENDIDO,
    arquivo_musica_historico=MUSICA_ARQUIVO_HISTORICO,
    arquivo_musica_feedback=MUSICA_ARQUIVO_FEEDBACK,
    contexto_getter=lambda: {
        "contexto_sistema": contexto_sistema,
        "obter_janela_ativa": lambda: gw.getActiveWindow(),
        "continuidades_get": _continuidades_get,
        "continuidades_set": _continuidades_set,
        "falar_com_lipsync": falar_com_lipsync,
        "abrir_programa": abrir_programa,
        "contexto_aponta_descanso": _contexto_aponta_descanso,
        "agendar_fala_proativa": _agendar_fala_proativa,
    },
    estado_getter=_estado_aprendizado_atual,
    estado_setter=_atualizar_estado_aprendizado,
    log=print,
)


def _carregar_rotinas_aprendidas():
    return _aprendizado_runtime.carregar_rotinas_aprendidas()


def _salvar_rotinas_aprendidas():
    return _aprendizado_runtime.salvar_rotinas_aprendidas()


def _logar_atividade_atual():
    return _aprendizado_runtime.logar_atividade_atual()


def _rotina_chave_feedback(hora: str, app: str) -> str:
    return _aprendizado_runtime.rotina_chave_feedback(hora, app)


def _rotina_app_bloqueado(hora: str, app: str) -> bool:
    return _aprendizado_runtime.rotina_app_bloqueado(hora, app, ROTINA_BLOQUEIO_REJEICAO_VEZES)


def _rotina_registrar_feedback(aceito: bool):
    return _aprendizado_runtime.registrar_feedback_rotina(
        aceito,
        cooldown_min=ROTINA_BLOQUEIO_REJEICAO_MIN,
        limite_rejeicao=ROTINA_BLOQUEIO_REJEICAO_VEZES,
    )


def _carregar_feedback_pesos():
    return _aprendizado_runtime.carregar_feedback_pesos()


def _carregar_musica_dados():
    return _aprendizado_runtime.carregar_musica_dados()


def _salvar_musica_dados():
    return _aprendizado_runtime.salvar_musica_dados()


def _carregar_musica_feedback_pesos():
    return _aprendizado_runtime.carregar_musica_feedback_pesos()


def _salvar_musica_feedback_pesos():
    return _aprendizado_runtime.salvar_musica_feedback_pesos()


def _musica_chave_feedback(hora: str, musica: str) -> str:
    return _aprendizado_runtime.musica_chave_feedback(hora, musica)


def _musica_bloqueada(hora: str, musica: str) -> bool:
    return _aprendizado_runtime.musica_bloqueada(hora, musica, ROTINA_BLOQUEIO_REJEICAO_VEZES)


def _musica_registrar_historico(musica: str):
    return _aprendizado_runtime.musica_registrar_historico(musica)


_feedback_pendente_runtime = _criar_feedback_pendente_runtime_mente(
    contexto_getter=lambda: {
        "continuidades_get": _continuidades_get,
        "continuidades_update": _continuidades_update,
        "normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
        "interpretar_confirmacao_llm": interpretar_confirmacao_llm,
        "interpretar_resposta_pendente": _interpretar_resposta_pendente_mente,
        "resumo_mente_integrada_para_prompt": _resumo_mente_integrada_para_prompt_mente,
        "mente_integrada_estado": mente_integrada_estado,
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


def _normalizar_confirmacao_texto(texto: str) -> str:
    return _feedback_pendente_runtime.normalizar_confirmacao_texto(texto)


def _classificar_confirmacao_local(texto: str):
    return _feedback_pendente_runtime.classificar_confirmacao_local(texto)


def _classificar_confirmacao_contextual(texto: str, sugestao: str):
    return _feedback_pendente_runtime.classificar_confirmacao_contextual(texto, sugestao)


def _interpretar_resposta_pendente(texto: str, pendencia: dict) -> dict:
    return _feedback_pendente_runtime.interpretar_resposta_pendente(texto, pendencia)


def _handle_feedback_pendente(texto: str) -> bool:
    return _feedback_pendente_runtime.handle_feedback_pendente(texto)


def _separar_feedback_e_continuacao(texto: str):
    return _feedback_pendente_runtime.separar_feedback_e_continuacao(texto)


def _handle_feedback_pendente_misto(texto: str) -> bool:
    """Trata frases como 'agora nao, mas coloca playlist anime' sem engolir o comando."""
    return _feedback_pendente_runtime.handle_feedback_pendente_misto(texto)


def _analisar_e_sugerir_musica():
    return


def _analisar_e_sugerir_rotina():
    return _aprendizado_runtime.analisar_e_sugerir_rotina(
        dias_para_aprender=ROTINA_DIAS_PARA_APRENDER,
        limite_rejeicao=ROTINA_BLOQUEIO_REJEICAO_VEZES,
    )


def monitor_rotina_daemon():
    """Daemon que registra atividades e sugere rotinas."""
    print("[ROTINA] Aprendizado de rotina iniciado - vai aprender em 7 dias")

    _aprendizado_runtime.carregar_tudo()

    while True:
        try:
            _aprendizado_runtime.monitor_tick(
                dias_para_aprender=ROTINA_DIAS_PARA_APRENDER,
                limite_rejeicao=ROTINA_BLOQUEIO_REJEICAO_VEZES,
                analisar_musica_cb=_analisar_e_sugerir_musica,
            )
        except Exception as e:
            print(f"[ROTINA] Erro no daemon: {e}")

        time.sleep(60)

def _texto_pede_contexto_arquivos(texto: str) -> bool:
    t = _normalizar_texto_com_apelidos(str(texto or "")).lower().strip()
    if not t:
        return False
    gatilhos = [
        "arquivo", "arquivos", "pasta", "pastas", "cria pasta", "criar pasta",
        "editar arquivo", "mover arquivo", "renomear", "apagar arquivo", "deletar arquivo",
        "salvar arquivo", "documento", "txt", "json", "csv", "pdf", "backup",
        "organiza meus arquivos", "organizar arquivos", "abrir arquivo",
    ]
    return any(g in t for g in gatilhos)

# ====================== FUNÇÕES DE PROCESSAMENTO DE LINGUAGEM ======================
def enviar_mensagem(mensagens, _com_tools=True, max_tokens: int = 1024, modo_rapido: bool = False):
    try:
        max_tokens = int(max_tokens or 1024)
    except Exception:
        max_tokens = 1024
    if modo_rapido:
        max_tokens = min(max_tokens, 320)
    elif _llm_endpoint_eh_local():
        max_tokens = min(max_tokens, 640)

    api_key = os.environ.get("OPENROUTER_API_KEY") or API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_APP_TITLE
    }
    mensagens_originais = list(mensagens) if isinstance(mensagens, list) else []
    mensagens_envio = []
    
    # ── PODA DE ECONOMIA (CORTA GASTOS EM 90%) ──
    if mensagens_originais:
        sys_prompt = mensagens_originais[0]
        if modo_rapido:
            historico_recente = mensagens_originais[-4:] if len(mensagens_originais) > 5 else mensagens_originais[1:]
        else:
            historico_recente = mensagens_originais[-10:] if len(mensagens_originais) > 11 else mensagens_originais[1:]
        mensagens_envio = [sys_prompt] + historico_recente

    if not modo_rapido:
        # ── INJEÇÃO DO RESUMO DO DIA ──
        if memoria_inteligente.resumo_do_dia:
            mensagens_envio.insert(0, {
                "role": "system",
                "content": f"RESUMO DO DIA {memoria_inteligente.data_atual}:\n{memoria_inteligente.resumo_do_dia}\n\nUse isso como contexto de longo prazo."
            })

        # ── INJEÇÃO DO CONTEXTO DE ARQUIVOS ──
        try:
            ultimo_texto_usuario = ""
            for msg in reversed(mensagens_originais):
                if isinstance(msg, dict) and str(msg.get("role") or "").lower() == "user":
                    ultimo_texto_usuario = str(msg.get("content") or "")
                    break
            if _texto_pede_contexto_arquivos(ultimo_texto_usuario):
                contexto_arquivos = mapear_pastas_principais()
                mensagens_envio.insert(1, {
                    "role": "system",
                    "content": contexto_arquivos + "\nUse esses caminhos reais para criar, mover ou editar arquivos sem precisar perguntar ao Pedro."
                })
        except Exception as e:
            print(f"Erro ao injetar contexto de arquivos: {e}")

        # ── CONTEXTO DO NAVEGADOR + SISTEMA ──
        try:
            if isinstance(contexto_atual_logs, list) and contexto_atual_logs:
                ultimos = [x for x in contexto_atual_logs[-8:] if _contexto_navegador_relevante(str(x))]
                if len(ultimos) > 5:
                    ultimos = ultimos[-5:]
                ctx = "\n".join([f"- {str(x)}" for x in ultimos])
                if ctx:
                    mensagens_envio.append({
                        "role": "system",
                        "content": "Contexto recente do navegador (ultimas acoes no Chrome):\n" + ctx
                    })
            if isinstance(contexto_sistema, dict):
                exe = str(contexto_sistema.get("exe") or "").strip()
                title = str(contexto_sistema.get("title") or "").strip()
                assunto = str(contexto_sistema.get("assunto") or "").strip()
                if (exe or title or assunto) and _contexto_navegador_relevante(f"{exe} {title} {assunto}"):
                    mensagens_envio.append({
                        "role": "system",
                        "content": f"Contexto do sistema: app_ativo={exe or 'desconhecido'} | janela='{title}' | assunto='{assunto or 'indefinido'}'."
                    })
            dicionario_txt = get_dicionario_contexto()
            if dicionario_txt:
                mensagens_envio.append({"role": "system", "content": dicionario_txt})
            mente_integrada_txt = _resumo_mente_integrada_para_prompt(ultimo_texto_usuario)
            if mente_integrada_txt:
                mensagens_envio.append({"role": "system", "content": mente_integrada_txt})
        except Exception:
            pass

    data = {
        "model": MODEL,
        "messages": mensagens_envio,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

    # Ativa JSON Mode se algum prompt de sistema exigir (Qwen2.5 local)
    for msg in mensagens_envio:
        if msg.get("role") == "system" and "FORMATO ESTRUTURAL OBRIGATÓRIO DO JSON" in msg.get("content", ""):
            data["response_format"] = {"type": "json_object"}
            break

    try:
        response = _post_chat_llm(headers, data)
        if response.status_code == 401:
            print("Erro 401 (Unauthorized) no OpenRouter.")
            return "Pedro, cheque sua chave do OpenRouter."
        response.raise_for_status()
        payload = response.json()
        choice = payload["choices"][0]
        message = choice["message"]

        # ── CASO 1: Modelo usou Function Calling ──
        tool_calls = message.get("tool_calls") or []
        if tool_calls:
            tc = tool_calls[0]
            func_name = tc.get("function", {}).get("name", "")
            args_raw = tc.get("function", {}).get("arguments", "{}")
            try:
                args = json.loads(args_raw)
            except Exception:
                args = {}
            fala = str(args.get("fala") or "").strip()
            comandos = args.get("comandos") or []
            print(f"[TOOLS] Function Call recebida: '{func_name}' | fala={fala[:60]} | cmds={len(comandos)}")
            # Retorna no mesmo formato que limpar_resposta_da_ia espera
            return json.dumps({"fala": fala, "comandos": comandos}, ensure_ascii=False)

        # ── CASO 2: Modelo retornou content JSON (fallback compativel) ──
        content = message.get("content") or ""
        return content

    except requests.exceptions.ReadTimeout as e:
        print(f"Timeout na LLM local/API: {e}")
        if _llm_endpoint_eh_local():
            return "Meu modelo local demorou demais pra responder agora. O Ollama pode estar carregando ou ocupado; tenta de novo em alguns segundos."
        return "A inteligência artificial demorou demais pra responder agora. Tenta de novo em alguns segundos."
    except requests.exceptions.RequestException as e:
        print(f"Erro na API: {e}")
        return "Minha conexão com a parte da IA falhou agora. Tenta de novo em instantes."


def interpretar_confirmacao_llm(fala_usuario: str, sugestao: str):
    api_key = os.environ.get("OPENROUTER_API_KEY") or API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_APP_TITLE
    }
    fala = (fala_usuario or "").strip()
    sug = (sugestao or "").strip()
    prompt = f'O usuário disse: "{fala}". Com base no contexto de que eu sugeri "{sug}", o usuário confirmou a ação? Responda apenas "SIM" ou "NAO".'
    data = {
        "model": MODEL,
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": 4,
        "temperature": 0.0
    }
    try:
        response = _post_chat_llm(headers, data)
        response.raise_for_status()
        payload = response.json()
        raw = str(payload["choices"][0]["message"]["content"] or "").strip().upper()
        if raw.startswith("SIM"):
            return True
        if raw.startswith("NAO") or raw.startswith("NÃO"):
            return False
        return None
    except Exception:
        return None

def solicitar_lista_abas(timeout_s: float = 6.0):
    return _chrome_solicitacoes.solicitar_lista_abas(timeout_s=timeout_s)

def solicitar_tab_reciclagem(target_domain: str, timeout_s: float = 3.0):
    return _chrome_solicitacoes.solicitar_tab_reciclagem(target_domain, timeout_s=timeout_s)

async def resumir_pagina_ou_video():
    """Resume o conteúdo da página ou vídeo atual (com legendas completas do YouTube)."""
    global ws_loop, is_speaking

    if ws_loop is None:
        falar_com_lipsync("Pedro, meu WebSocket não está conectado. Não consigo ver a página.", "irritada", 2)
        return

    falar_com_lipsync("Certo, Pedro. Deixa eu dar uma olhada no que você está vendo...", "calma", 1)

    try:
        response = await solicitar_conteudo_pagina()
        if not response.get("success"):
            falar_com_lipsync(f"Pedro, não consegui pegar o conteúdo da página. Erro: {response.get('error', 'desconhecido')}", "irritada", 2)
            return

        url = response.get("data", {}).get("url", "")
        page_content = response.get("data", {}).get("content", "")
        title = response.get("data", {}).get("title", "")

        if not url:
            falar_com_lipsync("Pedro, não consegui identificar a URL da página.", "irritada", 2)
            return

        resumo_texto = ""

        # ====================== YOUTUBE COM LEGENDAS COMPLETAS ======================
        if "youtube.com/watch" in url:
            video_id_match = re.search(r"v=([a-zA-Z0-9_-]+)", url)
            if video_id_match:
                video_id = video_id_match.group(1)
                try:
                    falar_com_lipsync("É um vídeo do YouTube! Pegando as legendas completas...", "calma", 1)
                    
                    # Usando getattr para evitar qualquer aviso direto do Pylance
                    get_transcript = getattr(YouTubeTranscriptApi, 'get_transcript')
                    transcript_list = get_transcript(video_id, languages=['pt', 'pt-BR', 'en'])
                    
                    # Junta todas as legendas em um único texto (tudo na memória)
                    full_transcript = " ".join([item['text'] for item in transcript_list])
                    resumo_texto = full_transcript
                    
                    print(f"✅ [RESUMO] Legendas completas obtidas ({len(full_transcript)} caracteres)")

                except Exception as e:
                    print(f"⚠️ Não consegui pegar legendas: {e}")
                    falar_com_lipsync("Não achei legendas nesse vídeo. Vou resumir só pelo título e descrição.", "calma", 1)
                    resumo_texto = page_content or title
            else:
                resumo_texto = page_content or title
        else:
            # Outras páginas (não YouTube)
            resumo_texto = page_content or title

        # Se ainda estiver vazio, avisa
        if not resumo_texto or len(resumo_texto) < 30:
            falar_com_lipsync("Pedro, o conteúdo que peguei é muito curto. Não tenho muito o que resumir.", "calma", 1)
            return

        # ====================== ENVIA PARA A IA ======================
        system_prompt = (
            "Você é a Laylay. Resuma o conteúdo abaixo de forma clara, curta e com o seu jeitinho debochado. "
            f"URL: {url}\nTítulo: {title}\n\nConteúdo completo:\n{resumo_texto}\n\n"
            "Regra: Máximo de 3-4 linhas. Mantenha sua personalidade sarcástica."
        )

        resumo_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Resuma isso pra mim, Laylay."}
        ]

        falar_com_lipsync("Analisando o conteúdo... pode demorar uns segundinhos.", "calma", 1)
        
        bot_raw = enviar_mensagem(resumo_messages, _com_tools=False)
        bot = _remover_prefixo_exec(limpar_resposta(bot_raw))

        if bot:
            print(f"Laylay [resumo]: {bot}")
            falar_com_lipsync(bot, "calma", 1)
        else:
            falar_com_lipsync("Pedro, não consegui resumir direito agora.", "calma", 1)

    except Exception as e:
        print(f"❌ Erro ao resumir página/vídeo: {e}")
        falar_com_lipsync("Pedro, deu um problema inesperado ao tentar resumir. Tenta de novo.", "irritada", 2)

def solicitar_aba_ativa(timeout_s: float = 4.0):
    return _chrome_solicitacoes.solicitar_aba_ativa(timeout_s=timeout_s)

async def processar_comando_visao(texto_usuario: str) -> str:
    """Lê a página atual do Chrome e retorna o conteúdo para a Laylay falar."""
    global ULTIMO_CONTEUDO_PAGINA, EVENTO_PAGINA
    
    EVENTO_PAGINA.clear()
    print("👁️ [VISÃO] Solicitando leitura da página atual...")

    # ✅ CORRIGIDO: sempre envia STRING JSON (broadcast_command exige str)
    await broadcast_command(json.dumps({"action": "READ_PAGE"}))

    try:
        # Aguarda resposta da extensão (máximo 4 segundos)
        await asyncio.wait_for(EVENTO_PAGINA.wait(), timeout=4.0)
        
        if ULTIMO_CONTEUDO_PAGINA:
            return f"✅ Li a página! Aqui está o que encontrei:\n{ULTIMO_CONTEUDO_PAGINA[:8000]}"
        return "Não consegui ler a página a tempo."
        
    except asyncio.TimeoutError:
        return "⏳ O Chrome demorou demais pra responder. Tenta de novo."

def _parse_ids_list(text: str):
    if not isinstance(text, str):
        return []
    t = text.strip()
    m = re.search(r'\[[^\]]*\]', t)
    if m:
        t = m.group(0)
    try:
        data = json.loads(t)
        if isinstance(data, list):
            out = []
            for x in data:
                try:
                    out.append(int(x))
                except Exception:
                    pass
            return [i for i in out if i > 0]
    except Exception:
        pass
    return []

def selecionar_abas_para_fechar_llm(comando_usuario: str, tabs_list):
    api_key = os.environ.get("OPENROUTER_API_KEY") or API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_APP_TITLE
    }
    tabs_filtradas = []
    try:
        for t in (tabs_list if isinstance(tabs_list, list) else []):
            if not isinstance(t, dict):
                continue
            tid = t.get("id")
            url = str(t.get("url") or "")
            title = str(t.get("title") or "")
            if isinstance(tid, int) and ("netflix.com" in url or "Netflix" in title):
                continue
            tabs_filtradas.append({"id": tid, "url": url, "title": title})
    except Exception:
        tabs_filtradas = tabs_list if isinstance(tabs_list, list) else []

    prompt = (
        f'Você é um gerente de abas. O usuário quer: "{comando_usuario}". '
        f'Analise esta lista de abas: {json.dumps(tabs_filtradas, ensure_ascii=False)}. '
        'Retorne APENAS uma lista de IDs (ex: [102, 144]) das abas que correspondem ao pedido. '
        'Se o pedido for "vazias", foque em URLs como "chrome://newtab", "about:blank" ou abas sem título. '
        'Se for "música", procure por termos de artistas ou "watch?v=" em abas de mídia.'
    )
    data = {
        "model": MODEL,
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.0
    }
    try:
        response = _post_chat_llm(headers, data)
        response.raise_for_status()
        payload = response.json()
        raw = str(payload["choices"][0]["message"]["content"] or "")
        return _parse_ids_list(raw)
    except Exception:
        return []

def abrir_url_com_reciclagem(url: str, auto_click: bool = False):
    return _abrir_url_reutilizando_aba_chrome_mente(
        url,
        conectado=_chrome_solicitacoes.conectado,
        solicitar_lista_abas=solicitar_lista_abas,
        enviar_comando=enviar_comando_chrome,
        abrir_fallback=webbrowser.open,
        auto_click=auto_click,
    )

def garantir_aba_unica(url_alvo: str, auto_click: bool = False):
    return _abrir_url_reutilizando_aba_chrome_mente(
        url_alvo,
        conectado=_chrome_solicitacoes.conectado,
        solicitar_lista_abas=solicitar_lista_abas,
        enviar_comando=enviar_comando_chrome,
        abrir_fallback=webbrowser.open,
        auto_click=auto_click,
        corrigir_url_busca=True,
    )

# Alias para compatibilidade com chamadas que usam o nome antigo
abrir_url_navegador = abrir_url_com_reciclagem

def buscar_imagem_url(assunto: str):
    return _pesquisa_contextual_runtime.buscar_imagem_url(assunto)


def _normalizar_tema_pesquisa(tema: str) -> str:
    return _pesquisa_contextual_runtime.normalizar_tema_pesquisa(tema)


def _tema_pesquisa_bagunçado(tema: str) -> bool:
    return _pesquisa_contextual_runtime.tema_pesquisa_baguncado(tema)


def _pontuar_hit_tema(consulta: str, titulo: str, snippet: str = "") -> int:
    return _pesquisa_contextual_runtime.pontuar_hit_tema(consulta, titulo, snippet)


def _pesquisar_contexto_tema(tema: str, ttl_s: float = 1800.0) -> dict:
    return _pesquisa_contextual_runtime.pesquisar_contexto_tema(tema, ttl_s=ttl_s)

def _nome_arquivo_imagem(assunto: str, ext: str):
    return _pesquisa_contextual_runtime.nome_arquivo_imagem(assunto, ext)

def baixar_imagem_direto(assunto: str):
    return _pesquisa_contextual_runtime.baixar_imagem_direto(assunto)

def fechar_abas_vazias():
    """Fecha TODAS as abas vazias de uma vez - VERSÃO COM DEBUG TOTAL"""
    tabs = solicitar_lista_abas()
    
    print(f"🔍 [DEBUG VAZIAS] Total de abas recebidas: {len(tabs)}")
    
    ids = []
    for t in (tabs if isinstance(tabs, list) else []):
        if not isinstance(t, dict):
            continue

        tid = t.get("id")
        url = str(t.get("url") or "").strip().lower()
        title = str(t.get("title") or "").strip()

        if not isinstance(tid, int):
            continue

        # Debug de cada aba (para vermos exatamente o que está chegando)
        print(f"   → Aba {tid} | Title: '{title}' | URL: '{url}'")

        # 🔥 DETECÇÃO MUITO MAIS AMPLA
        is_vazia = False

        if url.startswith("chrome://newtab") or url == "about:blank" or url == "":
            is_vazia = True
        if title in ["", "Nova guia", "Nova aba", "New Tab", "Nova guia - Google Chrome"]:
            is_vazia = True
        if len(title) <= 12 and not any(x in title.lower() for x in ["youtube", "netflix", "google", "spotify", "whatsapp"]):
            is_vazia = True

        # Nunca fecha Netflix ou YouTube
        if "netflix.com" in url or "youtube.com" in url:
            is_vazia = False

        if is_vazia:
            ids.append(tid)
            print(f"   ✅ Marcada para fechar: Aba {tid} ('{title}')")

    if ids:
        print(f"🌐 [FECHAR_VAZIAS] Encontradas {len(ids)} abas vazias → fechando em lote!")
        enviar_comando_chrome("close_tabs", {"ids": ids})
        return ids
    else:
        print("🌐 [FECHAR_VAZIAS] Nenhuma aba vazia detectada (mesmo com debug)")
        return []

def _buscar_url_youtube_silencioso(query: str) -> str:
    return _busca_musical_runtime.buscar_url_silencioso(query)

# ====================== PORTEIRO DO CHROME (daemon) ======================
def _porteiro_daemon():
    """Verifica RAM e abas ociosas periodicamente. Sugere limpeza em voz se necessario."""
    import time as _t
    _t.sleep(90)  # Espera o sistema iniciar completamente
    print("\U0001f6aa [PORTEIRO] Thread do Porteiro do Chrome iniciada.")
    while True:
        try:
            _t.sleep(PORTEIRO_INTERVALO_MIN * 60)
            ram_percent = psutil.virtual_memory().percent
            if ram_percent < RAM_THRESHOLD_PORTEIRO:
                continue  # RAM ok, nao precisa incomodar

            agora = _t.time()
            limite_idle = agora - (ABA_IDLE_MINUTOS * 60)

            # Pede a lista atual de abas via extensao
            abas_abertas = listar_abas_chrome(timeout_s=5.0)
            if not abas_abertas:
                continue

            abas_ociosas = []
            chrome_estado = _chrome_estado.snapshot()
            aba_url_atual = str(chrome_estado.get("aba_url_atual") or "")
            tab_last_seen = chrome_estado.get("_tab_last_seen") or {}
            for aba in abas_abertas:
                url = str(aba.get("url") or "")
                titulo = str(aba.get("titulo") or aba.get("title") or "")[:50]
                if not url or url.startswith("chrome://") or url.startswith("chrome-extension://"):
                    continue
                if url == aba_url_atual:
                    continue  # aba atual nao toca
                last = tab_last_seen.get(url)
                ts_last = last["ts"] if last else (agora - ABA_IDLE_MINUTOS * 60 - 1)
                if ts_last < limite_idle:
                    minutos_parado = int((agora - ts_last) / 60)
                    abas_ociosas.append({"url": url, "titulo": titulo, "minutos": minutos_parado})

            if len(abas_ociosas) < 2:
                continue

            abas_ociosas.sort(key=lambda x: x["minutos"], reverse=True)
            candidatas = abas_ociosas[:3]

            global _porteiro_ultima_sugestao_ts, _abas_sugeridas_fechar
            if agora - _porteiro_ultima_sugestao_ts < 30 * 60:  # 30 min entre sugestoes
                continue

            _porteiro_ultima_sugestao_ts = agora
            _abas_sugeridas_fechar = [a["url"] for a in candidatas]

            nomes = ", ".join([a["titulo"] or a["url"][:30] for a in candidatas])
            h = int(candidatas[0]["minutos"] / 60)
            m = candidatas[0]["minutos"] % 60
            tempo_str = f"ha {h}h{m:02d}" if h else f"ha {candidatas[0]['minutos']} min"
            msg = (
                f"Pedro, a RAM ta em {int(ram_percent)}% e voce nao mexe em {len(candidatas)} abas {tempo_str}: "
                f"{nomes}. Manda um 'fecha as abas paradas' se quiser limpar."
            )
            print(f"\U0001f6aa [PORTEIRO] {msg}")
            try:
                falar_com_lipsync(msg, "irritada", 1)
            except Exception as _fe:
                print(f"[PORTEIRO] Erro ao falar: {_fe}")

        except Exception as _e:
            print(f"[PORTEIRO] Erro no daemon: {_e}")

# ====================== SISTEMA DE AGENDAMENTOS ======================
_agendamentos_file = os.path.join(_base_dir, AGENDAMENTOS_ARQUIVO)

def _enviar_pc_b(payload: dict):
    if connected_pc_b_clients and ws_loop:
        msg = json.dumps(payload)
        for pcb_ws in list(connected_pc_b_clients):
            asyncio.run_coroutine_threadsafe(pcb_ws.send(msg), ws_loop)
        print(f"[PC B] Comando '{payload.get('action')}' enviado para {len(connected_pc_b_clients)} cliente(s)")
        return True
    else:
        print("[PC B] Nenhum cliente PC B conectado.")
        return False


def _agenda_enviar_chrome_local(payload: dict):
    if ws_loop:
        asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(payload)), ws_loop)


_agenda_runtime = _criar_agenda_runtime_mente(
    _agendamentos_file,
    falar_cb=falar_com_lipsync,
    abrir_programa_cb=lambda alvo: abrir_programa(alvo),
    enviar_pc_b_cb=_enviar_pc_b,
    enviar_chrome_local_cb=_agenda_enviar_chrome_local,
    executar_exec_cb=lambda cmd, arg: _executar_exec(cmd, arg),
    log=print,
)


def _agendamentos_load() -> list:
    return _agenda_runtime.load()


def _agendamentos_save(lista: list):
    return _agenda_runtime.save(lista)


def _disparar_agendamento(ag: dict):
    return _agenda_runtime.disparar(ag)


def _agenda_daemon():
    return _agenda_runtime.daemon()

def _playlists_load():
    return _playlist_runtime.load()


def LIST_PLAYLIST_CONTENT(nome_playlist: str):
    return _playlist_runtime.list_content(nome_playlist)


def _fala_playlist_conteudo_estilosa(info: dict, fallback_nome: str = "") -> str:
    return _fala_playlist_conteudo_estilosa_mente(info, fallback_nome)


def list_playlist_urls(name: str):
    return _playlist_runtime.list_urls(name)


def _playlists_save(data: dict):
    return _playlist_runtime.save(data)

def _yt_clean_url(url: str) -> str:
    return _yt_clean_url_mente(url)

def _yt_clean_title(title: str) -> str:
    return _yt_clean_title_mente(title)

def _remover_acentos(s: str) -> str:
    return _remover_acentos_mente(s)

def _aplicar_correcao_fonetica(texto: str) -> str:
    return _aplicar_correcao_fonetica_mente(texto)

def _carregar_apelidos_memoria(force: bool = False) -> dict:
    return _linguagem_aprendida_runtime.carregar_apelidos(force)

def _aplicar_apelidos_learned(texto: str) -> str:
    return _linguagem_aprendida_runtime.aplicar_apelidos(texto)

def _normalizar_texto_com_apelidos(s: str) -> str:
    return _linguagem_aprendida_runtime.normalizar_com_apelidos(s)

def _extrair_apelido_ensinavel(texto: str):
    return _linguagem_aprendida_runtime.extrair_apelido_ensinavel(texto)

def _aprender_apelido(alias: str, alvo: str, contexto: str = "") -> bool:
    return _linguagem_aprendida_runtime.aprender_apelido(alias, alvo, contexto)

def _processar_aprendizado_apelido_imediato(texto: str) -> bool:
    return _linguagem_aprendida_runtime.processar_aprendizado_imediato(texto)

def _normalizar_texto(s: str) -> str:
    return _normalizar_texto_mente(s)

_linguagem_aprendida_runtime = _criar_linguagem_aprendida_runtime_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    normalizar_texto=_normalizar_texto,
    texto_social_curto=lambda texto: _texto_social_curto(texto),
    falar=lambda fala, emocao, nivel: falar_com_lipsync(fala, emocao, nivel),
    log=print,
)

def _titulo_fingerprint(titulo: str) -> str:
    return _titulo_fingerprint_mente(titulo)

def _canal_fingerprint(canal: str) -> str:
    return _canal_fingerprint_mente(canal)

def _sim_ratio(a: str, b: str) -> float:
    return _sim_ratio_mente(a, b)

def _fala_playlist_sucesso(title: str, playlist_nome: str, created: bool) -> str:
    return _fala_playlist_sucesso_mente(title, playlist_nome, created)

def _fala_playlist_duplicado(title: str, playlist_nome: str) -> str:
    return _fala_playlist_duplicado_mente(title, playlist_nome)

def _fala_playlist_duplicado_meta(title: str, playlist_nome: str, other_channel: bool) -> str:
    return _fala_playlist_duplicado_meta_mente(title, playlist_nome, other_channel)

def _limpar_nome_playlist(nome: str) -> str:
    return _limpar_nome_playlist_mente(nome)

def _resolver_nome_playlist_contextual(nome: str) -> str:
    return _playlist_runtime.resolver_nome(nome)

def _playlist_nome_explicito_na_frase(texto: str) -> bool:
    return _playlist_nome_explicito_na_frase_mente(
        texto,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
    )


def _playlist_item_label(item) -> str:
    return _playlist_item_label_mente(item)


def _playlist_item_match(item, musica: str) -> bool:
    return _playlist_item_match_mente(
        item,
        musica,
        normalizar_texto_cb=_normalizar_texto,
    )


def mover_item_playlist(origem: str, destino: str, musica: str = "") -> dict:
    return _playlist_runtime.mover_item(
        origem,
        destino,
        musica,
        normalizar_texto_cb=_normalizar_texto,
    )


def detectar_mover_playlist_texto(texto: str):
    return _detectar_mover_playlist_texto_mente(texto)


def extrair_nome_playlist(texto: str) -> str:
    nome = _extrair_nome_playlist_mente(
        texto,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
    )
    print(f"[DEBUG] Nome extraído da playlist: {nome}")
    return nome

def _formatar_playlists_para_prompt() -> str:
    return _playlist_runtime.formatar_para_prompt()


def _pedido_lista_geral_playlist(texto_original: str, params: dict) -> bool:
    return _pedido_lista_geral_playlist_mente(
        texto_original,
        params,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
    )


def _listar_playlists_salvas() -> str:
    return _playlist_runtime.listar_salvas()


def _playlists_laylay_load():
    return _playlist_laylay_runtime.load()


def _playlists_laylay_save(data: dict) -> bool:
    return _playlist_laylay_runtime.save(data)


def _sincronizar_playlists_da_laylay():
    return _playlist_laylay_runtime.sincronizar()


def _listar_playlists_da_laylay(nome: str = "") -> str:
    return _playlist_laylay_runtime.listar(nome)


def _adicionar_descoberta_na_playlist_da_laylay(item: dict) -> None:
    _playlist_laylay_runtime.adicionar_descoberta(item)


def _copiar_faixa_da_playlist_laylay(nome_playlist_laylay: str, musica: str, destino_usuario: str) -> dict:
    return _playlist_laylay_runtime.copiar_faixa(
        nome_playlist_laylay,
        musica,
        destino_usuario,
    )


def _resolver_query_musical_por_estilo(query: str, texto_original: str = "") -> dict:
    q = _normalizar_query_musical(query or texto_original)
    return {"query": q, "origem": "explicita"}


def _detectar_playlist_nome_direto(texto: str) -> str:
    return _playlist_runtime.detectar_nome_direto(
        texto,
        normalizar_texto_cb=_normalizar_texto_com_apelidos,
    )

def _carregar_playlists_para_memoria():
    global playlists_carregadas
    playlists_carregadas = _playlist_runtime.load()
    _sincronizar_playlists_da_laylay()
    print(f"🎵 [PLAYLISTS] Playlists carregadas: {list(playlists_carregadas.keys())}")

def _ensure_playlists_file() -> bool:
    return _playlist_runtime.ensure_file()

def add_to_playlist_url(playlist_name: str, url: str, title: str = "", canal: str = ""):
    return _playlist_runtime.add_url(playlist_name, url, title, canal)

def add_to_playlist_from_active_tab(playlist_name: str):
    return _playlist_runtime.add_from_active_tab(playlist_name)

def ADD_TO_PLAYLIST(nome_playlist: str, url: str, titulo: str, canal: str = "") -> bool:
    return _playlist_runtime.add_and_verify(nome_playlist, url, titulo, canal)

def _playlist_primeira_url(nome: str):
    return _playlist_runtime.primeira_url(nome)

def _playlist_item_at(nome: str, idx: int):
    return _playlist_runtime.item_at(nome, idx)

def _parse_indice_ordinal(token: str):
    return _parse_indice_ordinal_mente(token)

def playlist_len(nome: str) -> int:
    return _playlist_runtime.len(nome)

def _playlist_shuffle_start(nome: str):
    return _playlist_runtime.shuffle_start(nome)

def delete_playlist(nome: str) -> bool:
    return _playlist_runtime.delete(nome)

def _playlist_avancar_proxima():
    return _playlist_runtime.avancar_proxima()


def _playlist_voltar_anterior():
    return _playlist_runtime.voltar_anterior()

def play_playlist(name: str):
    return _playlist_runtime.play(name)

def _executar_combo_modo_code(payload: dict):
    if payload.get("clean_tabs") or payload.get("clean_empty_tabs"):
        fechar_abas_vazias()
    img_topic = str(payload.get("image_topic") or "").strip()
    img_action = str(payload.get("image_action") or "").strip().lower()
    if img_topic:
        if img_action == "download":
            baixar_imagem_direto(img_topic)
        else:
            url_img = buscar_imagem_url(img_topic)
            if url_img:
                try:
                    webbrowser.open(url_img)
                except Exception:
                    pass
    q = str(payload.get("music_query") or "lofi focus").strip()
    if q:
        enviar_comando_chrome("youtube_search", {"query": q})
    return True

def _executar_combo_modo_gamer(payload: dict):
    if payload.get("pause_music"):
        enviar_comando_chrome("youtube_control", {"command": "pause_play"})
    if payload.get("close_study_tabs"):
        tabs = solicitar_lista_abas()
        ids = selecionar_abas_para_fechar_llm("fechar abas de estudo", tabs)
        if ids:
            enviar_comando_chrome("close_tabs", {"ids": ids})
    return True

def _executar_combo_organizacao(payload: dict):
    if payload.get("open_downloads"):
        try:
            p = os.path.join(os.path.expanduser("~"), "Downloads")
            os.startfile(p)
        except Exception:
            pass
    return True

def _merge_intent_llm(original_payload: dict, fala_usuario: str):
    api_key = os.environ.get("OPENROUTER_API_KEY") or API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_APP_TITLE
    }
    prompt = (
        f'Sugestão original: {json.dumps(original_payload, ensure_ascii=False)}. '
        f'Fala do usuário: "{fala_usuario}". '
        'O usuário aceitou a estrutura, mas mudou algum detalhe? '
        'Corrija erros de fala/fonética (ex: "Tin Maia" -> "Tim Maia"). '
        'Retorne APENAS o novo JSON do comando mantendo o que ele aceitou e trocando o que ele pediu para mudar. '
        'Campos permitidos: action, clean_tabs, music_query, image_topic, image_action.'
    )
    data = {
        "model": MODEL,
        "messages": [{"role": "system", "content": prompt}],
        "max_tokens": 120,
        "temperature": 0.0
    }
    try:
        response = _post_chat_llm(headers, data)
        response.raise_for_status()
        payload = response.json()
        raw = str(payload["choices"][0]["message"]["content"] or "").strip()
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            raw = m.group(0)
        merged = json.loads(raw)
        return merged if isinstance(merged, dict) else original_payload
    except Exception:
        return original_payload

def limpar_resposta(texto):
    return _limpar_resposta_mente(texto)

def list_playlist(name: str):
    nm = (name or "").strip().lower()
    data = _playlists_load()
    lst = data.get(nm)
    if isinstance(lst, list):
        return lst
    return []

def playlist_titulos(name: str):
    lst = list_playlist(name)
    titulos = []
    for item in lst:
        if isinstance(item, dict):
            t = str(item.get("titulo") or "").strip()
            if t:
                titulos.append(t)
    return titulos

def interpretar_comando_local_rapido(texto: str):
    """Atalhos locais para comandos de desktop que não precisam da IA."""
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None
    if _texto_depende_de_contexto(t):
        return None

    aliases_apps = {
        "opera": {"opera", "ópera", "operagx", "opera gx"},
        "vscode": {"vscode", "vs code", "visual studio code", "code"},
        "chrome": {"chrome", "google chrome"},
        "edge": {"edge", "msedge", "microsoft edge"},
        "brave": {"brave", "brave browser"},
        "firefox": {"firefox", "mozilla firefox"},
    }

    app_encontrado = None
    for app, aliases in aliases_apps.items():
        if any(alias in t for alias in aliases):
            app_encontrado = app
            break

    if not app_encontrado:
        return None

    verbs_foco = (
        "em foco", "traz", "traga", "deixa", "coloca", "bota",
        "maximiza", "maximizar", "na frente", "primeiro plano", "foco",
    )
    if not any(v in t for v in verbs_foco):
        return None

    fullscreen = any(p in t for p in ("tela cheia", "fullscreen", "full screen", "tela cheia no"))
    if fullscreen:
        return {"intent": "MAXIMIZE_WINDOW", "params": {"nome_app": app_encontrado}}
    return {"intent": "APP_OPEN", "params": {"nome_app": app_encontrado, "modo": "focus"}}


def _extrair_app_explicito_em_comando_janela(texto: str) -> str:
    return _extrair_app_explicito_em_comando_janela_mente(
        texto,
        normalizar_texto=_normalizar_texto_com_apelidos,
    )


def _resolver_comando_janela_contextual_forcado(texto: str):
    """Força continuidade de janela/app antes do fluxo livre da IA."""
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None

    resultado = _resolver_comando_janela_contextual_mente(
        t,
        mente_integrada_estado=mente_integrada_estado,
        app_explicito=_extrair_app_explicito_em_comando_janela(t),
        alvo_corrigido=_alvo_corrigido_atual(),
        normalizar_texto=_normalizar_texto_com_apelidos,
    )
    if isinstance(resultado, dict) and str(resultado.get("_alvo_corrigido") or "").strip():
        _registrar_alvo_corrigido(str(resultado.get("_alvo_corrigido") or "").strip())
        resultado = dict(resultado)
        resultado.pop("_alvo_corrigido", None)
    return resultado


def _responder_contexto_janela_indisponivel(texto: str) -> bool:
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return False
    fala = _fala_contexto_janela_indisponivel_mente(
        t,
        mente_integrada_estado=mente_integrada_estado,
    )
    if not fala:
        return False
    falar_com_lipsync(fala, "calma", 1)
    return True


def _resolver_comando_midia_contextual_forcado(texto: str):
    """Resolve comandos curtos de midia usando o contexto musical antes da conversa curta."""
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None
    return _resolver_comando_midia_contextual_mente(
        t,
        mente_integrada_estado=mente_integrada_estado,
        contexto_musical=_contexto_musical_ativo(),
        ttl_s=240.0,
    )


def _resolver_comando_arquivo_contextual_forcado(texto: str):
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None
    return _resolver_comando_arquivo_contextual_mente(
        t,
        mente_integrada_estado=mente_integrada_estado,
        estrutura_recente=_estrutura_arquivo_recente(900.0),
        ttl_s=300.0,
    )


def _referencia_contextual_imediata(ttl_s: float = 300.0) -> dict:
    return _referencia_contextual_imediata_mente(
        mente_integrada_estado=mente_integrada_estado,
        foco_vivo=_foco_vivo_atual(ttl_s=ttl_s),
        alvo_corrigido=_alvo_corrigido_atual(),
        ultima_playlist=_musica_estado_get("ultima_playlist"),
        normalizar_texto=_normalizar_texto_com_apelidos,
        ttl_s=ttl_s,
    )


def _resolver_comando_acao_geral_contextual_forcado(texto: str):
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None
    return _resolver_comando_acao_geral_contextual_mente(
        t,
        _referencia_contextual_imediata(300.0),
        ultima_playlist=_musica_estado_get("ultima_playlist"),
    )


def _resolver_comando_contextual_forcado(texto: str):
    return _resolver_comando_contextual_mente(
        texto,
        [
            ("JANELA", _resolver_comando_janela_contextual_forcado),
            ("MIDIA", _resolver_comando_midia_contextual_forcado),
            ("ARQUIVO", _resolver_comando_arquivo_contextual_forcado),
            ("GERAL", _resolver_comando_acao_geral_contextual_forcado),
        ],
    )


def _usar_modo_rapido_conversa(texto: str) -> bool:
    return _usar_modo_rapido_conversa_mente(
        texto,
        normalizar_texto=_normalizar_texto_com_apelidos,
        interpretar_comando_local_rapido=interpretar_comando_local_rapido,
        resolver_comando_contextual=_resolver_comando_contextual_forcado,
    )


def _texto_pede_direcao_musical_generica(texto: str) -> bool:
    return _musica_conversacional_runtime.texto_pede_direcao(texto)


def _sugestao_musical_nova_conversacional(texto: str = "") -> str:
    return _musica_conversacional_runtime.sugestao_nova(texto)


def _responder_pedido_direcao_musical_generica(texto: str = "") -> bool:
    return _musica_conversacional_runtime.responder_pedido_direcao(texto)


def _processar_confirmacao_sugestao_musical(texto: str = "") -> bool:
    return _musica_conversacional_runtime.processar_confirmacao(texto)


def processar_comandos_imediatos(texto: str, *, contexto_mental_ja_refinado: bool = False) -> bool:
    contexto = {
        "_normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
        "_texto_social_curto": _texto_social_curto,
        "_texto_conversa_casual_sem_acao": _texto_conversa_casual_sem_acao,
        "_refinar_contexto_mental": _refinar_contexto_mental,
        "_texto_tem_comando_explicito": _texto_tem_comando_explicito,
        "_texto_conversa_contextual_sem_comando": _texto_conversa_contextual_sem_comando,
        "_contexto_mental_ja_refinado": contexto_mental_ja_refinado,
        "_resolver_comando_janela_contextual_forcado": _resolver_comando_janela_contextual_forcado,
        "_resolver_comando_midia_contextual_forcado": _resolver_comando_midia_contextual_forcado,
        "_resolver_comando_arquivo_contextual_forcado": _resolver_comando_arquivo_contextual_forcado,
        "_resolver_comando_acao_geral_contextual_forcado": _resolver_comando_acao_geral_contextual_forcado,
        "_resolver_comando_contextual_forcado": _resolver_comando_contextual_forcado,
        "_responder_contexto_janela_indisponivel": _responder_contexto_janela_indisponivel,
        "processar_comandos_em_cadeia": processar_comandos_em_cadeia,
        "processar_comando_deterministico": processar_comando_deterministico,
        "interpretar_comando_local_rapido": interpretar_comando_local_rapido,
        "analisar_intencao": analisar_intencao,
        "executar_intencao": executar_intencao,
        "_registrar_resultado_execucao": _registrar_resultado_execucao,
        "_registrar_autoaprimoramento": _registrar_autoaprimoramento,
        "_falar_falha_contextual": _falar_falha_contextual,
        "ws_loop": ws_loop,
        "resumir_pagina_ou_video": resumir_pagina_ou_video,
        "falar_com_lipsync": falar_com_lipsync,
    }
    return _processar_comandos_imediatos_mente(contexto, texto)

# ====================== MICROFONE EM TEMPO REAL ======================
def _resetar_sugestao():
    global estado_continuidades
    estado_continuidades = _limpar_sugestao_atual_mente(estado_continuidades)

def _confirmar_execucao_debochada(texto_usuario, system_msg):
    global messages
    messages.append({"role": "user", "content": texto_usuario})
    confirma = list(messages)
    confirma.append({"role": "system", "content": system_msg})
    bot_raw = enviar_mensagem(confirma, _com_tools=False)
    bot = _remover_prefixo_exec(limpar_resposta(bot_raw))
    if bot:
        print(f"Laylay [debochada lvl2]: {bot}")
        messages.append({"role": "assistant", "content": bot})
        falar_com_lipsync(bot, "debochada", 2)
        memoria_inteligente.adicionar_interacao(texto_usuario, bot)   # ← corrigido
        salvar_memoria()

def _extrair_json_da_ia(texto: str) -> str:
    return _extrair_json_resposta_mente(texto)

def analisar_intencao(texto: str):
    if _interpretacao_intencao_runtime is None:
        return None
    return _interpretacao_intencao_runtime.analisar(texto)

def _detectar_foco_app_local(texto: str):
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None
    if "opera" not in t:
        return None
    foco = any(p in t for p in [
        "em foco", "traz o opera", "traga o opera", "deixa o opera", "coloca o opera",
        "maximiza o opera", "maximizar o opera", "tela cheia", "tela cheia no opera",
        "full screen", "fullscreen", "em primeiro plano", "na frente"
    ])
    if not foco:
        return None
    fullscreen = any(p in t for p in ["tela cheia", "fullscreen", "full screen"])
    return {"app": "opera", "fullscreen": fullscreen}

def _contexto_musical_ativo() -> bool:
    return _contexto_musical_ativo_mente(_musica_estado_get("ultima_playlist"), playlist_state)

def _contexto_mental_ativo() -> bool:
    return _contexto_mental_ativo_mente(mente_integrada_estado, _musica_estado_get("ultima_playlist"), playlist_state)

def _texto_depende_de_contexto(texto: str) -> bool:
    return _texto_depende_de_contexto_mente(texto, _normalizar_texto_com_apelidos)

def _fluxo_prioritario_da_ia(texto: str) -> bool:
    return _fluxo_prioritario_da_ia_mente(texto, _normalizar_texto_com_apelidos, lambda x: _texto_depende_de_contexto_mente(x, _normalizar_texto_com_apelidos))

def _resumo_agendamentos_para_prompt(limit: int = 6) -> str:
    return _resumo_agendamentos_para_prompt_mente(_agendamentos_load, limit=limit)

def _extrair_agendamento_local(texto: str):
    return _extrair_agendamento_local_mente(texto, _normalizar_texto_com_apelidos)

def _tentar_intencao_contextual_ai(texto: str):
    return _tentar_intencao_contextual_ai_mente(
        texto,
        _contexto_mental_ativo,
        _texto_depende_de_contexto,
        analisar_intencao,
    )

def _target_from_params(params: dict, texto_original: str = "") -> str:
    alvo = str(params.get("target") or "").strip().lower()
    texto = _normalizar_texto_com_apelidos(texto_original)
    if alvo in {"pc_b", "pc b", "b", "computador_b", "computador b"}:
        return "pc_b"
    if any(x in texto for x in ["pc b", "pc_b", "computador b", "no b", "pro b", "pra b", "para o b"]):
        return "pc_b"
    if alvo in {"ambos", "both", "todos"}:
        return "ambos"
    return "pc_a"

def _limpar_destino_pc_b(texto: str) -> str:
    s = str(texto or "").strip()
    s = re.sub(r"\b(no|pro|pra|para o|para)\s+pc\s*b\b", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(no|pro|pra|para o|para)\s+b\b", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip(" .,!?:;")
    return s

def _montar_url_site_ou_busca(alvo: str) -> str:
    q = str(alvo or "").strip()
    if not q:
        return ""
    q_lower = _normalizar_texto_com_apelidos(q)
    if is_valid_url(q):
        return q
    if q_lower in SITES_DIRECTOS:
        return SITES_DIRECTOS[q_lower]
    if "." in q_lower and " " not in q_lower:
        return formatar_url_ou_busca(q_lower)
    return f"https://www.google.com/search?q={urllib.parse.quote(q)}"

def _executar_fechar_abas_paradas() -> bool:
    if _abas_sugeridas_fechar:
        n_abas = len(_abas_sugeridas_fechar)
        print(f"🧹 [PORTEIRO] Fechando {n_abas} aba(s) sugeridas...")
        for url_fechar in list(_abas_sugeridas_fechar):
            payload = json.dumps({"action": "close_specific_tab", "target": url_fechar[:60]})
            if ws_loop:
                import asyncio as _aio
                _aio.run_coroutine_threadsafe(broadcast_command(payload), ws_loop)
        _abas_sugeridas_fechar.clear()
        falar_com_lipsync(
            f"Pronto. Limpei {n_abas} aba{'s' if n_abas > 1 else ''} paradas. Agora sobra RAM de verdade.",
            "debochada", 2
        )
        return True
    falar_com_lipsync("Não tem abas paradas registradas agora. Me acompanha mais de perto.", "calma", 1)
    return True

def _executar_captura_tela_intent(destino: str) -> bool:
    pergunta_visao = (
        "Você é a Laylay, assistente debochada, sarcástica e dona absoluta do PC do Pedro. "
        "Olhe para esta tela e descreva o que o Pedro está fazendo ou o que está aberto. "
        "Seja curta (máximo 3 linhas), direta, irônica e julgue as escolhas dele se for o caso. "
        "Responda SEMPRE em português brasileiro, com seu jeitão de sempre."
    )
    if destino == "pc_b":
        _enviar_pc_b({"action": "capturar_tela", "pergunta": pergunta_visao})
        falar_com_lipsync("Abrindo o olho no PC B, um segundo...", "calma", 1)
        return True

    def _ver_tela_local():
        try:
            print("[VISÃO] Capturando tela local...")
            img_b64 = _capturar_tela_base64()
            if not img_b64:
                falar_com_lipsync("Não consegui capturar a tela.", "calma", 1)
                return
            descricao = _analisar_com_groq(img_b64, pergunta_visao)
            falar_com_lipsync(str(descricao or "")[:300], current_emotion or "debochada", emotion_level or 2)
        except Exception as e_vis:
            print(f"[VISÃO] Erro: {e_vis}")
            falar_com_lipsync("Tive um problema pra olhar a tela, Pedro.", "irritada", 2)

    threading.Thread(target=_ver_tela_local, daemon=True).start()
    falar_com_lipsync("Tô olhando pra tela agora, um segundo...", "calma", 1)
    return True


def _bloqueio_por_emocao(intent: str, texto_original: str = "") -> bool:
    contexto = {
        "current_emotion": current_emotion,
        "emotion_level": emotion_level,
        "falar_com_lipsync": falar_com_lipsync,
        "_normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
    }
    return _bloqueio_por_emocao_mente(intent, texto_original, contexto)

def executar_intencao(resultado: dict, texto_original: str) -> bool:
    contexto = {
        "ultima_playlist": _musica_estado_get("ultima_playlist"),
        "current_emotion": current_emotion,
        "emotion_level": emotion_level,
        "messages": messages,
        "set_ultima_playlist": lambda valor: _musica_estado_set("ultima_playlist", valor),
        "set_playlist_state_last_url": lambda valor: playlist_state.__setitem__("last_url", valor),
        "set_playlist_sugestao_pendente": lambda valor: _continuidades_set("playlist_sugestao_pendente", valor),
        "_target_from_params": _target_from_params,
        "ultimo_alvo": str((mente_integrada_estado or {}).get("ultimo_alvo") or "").strip(),
        "_registrar_mente_curta": _registrar_mente_curta,
        "_registrar_resultado_execucao": _registrar_resultado_execucao,
        "_bloqueio_por_emocao": lambda intent, texto, _ctx: _bloqueio_por_emocao(intent, texto),
        "falar_com_lipsync": falar_com_lipsync,
        "_enviar_pc_b": _enviar_pc_b,
        "APPS_MAP": APPS_MAP,
        "abrir_url_com_reciclagem": abrir_url_com_reciclagem,
        "abrir_programa": abrir_programa,
        "fechar_programa": fechar_programa,
        "enviar_comando_chrome": enviar_comando_chrome,
        "criar_pasta": criar_pasta,
        "criar_ou_editar_arquivo": criar_ou_editar_arquivo,
        "deletar_item": deletar_item,
        "resolver_caminho": resolver_caminho,
        "mover_arquivo": mover_arquivo,
        "registrar_contexto_arquivo": lambda alvo, tipo="": _registrar_mente_curta(
            "",
            "",
            intencao="ARQUIVOS",
            alvo=alvo,
            habilidade="arquivos" if not tipo else tipo,
        ),
        "ultima_pasta_contextual": lambda: str((mente_integrada_estado or {}).get("ultima_pasta") or "").strip(),
        "ultimo_arquivo_contextual": lambda: str((mente_integrada_estado or {}).get("ultimo_caminho_arquivo") or (mente_integrada_estado or {}).get("ultimo_arquivo") or "").strip(),
        "estrutura_arquivo_recente": lambda: _estrutura_arquivo_recente(ttl_s=900.0) or {},
        "ajustar_volume_sistema": ajustar_volume_sistema,
        "ajustar_volume_sistema_relativo": ajustar_volume_sistema_relativo,
        "solicitar_aba_ativa": solicitar_aba_ativa,
        "fechar_aba_ativa_nativa": fechar_aba_ativa_nativa,
        "organizar_janelas_robusto": organizar_janelas_robusto,
        "ativar_tela_cheia_robusta": ativar_tela_cheia_robusta,
        "focar_janela_app": focar_janela_app,
        "_gmail_falar_resumo_estiloso": _gmail_falar_resumo_estiloso,
        "_gmail_buscar_nao_lidos": _gmail_buscar_nao_lidos,
        "_gmail_silenciar_remetente": _gmail_silenciar_remetente,
        "repetir_briefing": repetir_briefing,
        "obter_clima_localidade": obter_clima_localidade,
        "cidade_padrao_clima": BRIEFING_CIDADE,
        "_agendamentos_load": _agendamentos_load,
        "_agendamentos_save": _agendamentos_save,
        "_fala_agendamentos_estilosa": _fala_agendamentos_estilosa,
        "_normalizar_query_musical": _normalizar_query_musical,
        "_buscar_primeiro_video_youtube": _buscar_primeiro_video_youtube,
        "_playlist_nome_explicito_na_frase": _playlist_nome_explicito_na_frase,
        "_playlist_shuffle_start": _playlist_shuffle_start,
        "_playlist_primeira_url": _playlist_primeira_url,
        "_playlist_item_at": _playlist_item_at,
        "delete_playlist": delete_playlist,
        "playlist_len": playlist_len,
        "play_playlist": play_playlist,
        "_registrar_estrutura_arquivo_recente": _registrar_estrutura_arquivo_recente,
        "ADD_TO_PLAYLIST": ADD_TO_PLAYLIST,
        "LIST_PLAYLIST_CONTENT": LIST_PLAYLIST_CONTENT,
        "_fala_playlist_conteudo_estilosa": _fala_playlist_conteudo_estilosa,
        "_pedido_lista_geral_playlist": _pedido_lista_geral_playlist,
        "_listar_playlists_salvas": _listar_playlists_salvas,
        "_listar_playlists_da_laylay": _listar_playlists_da_laylay,
        "_copiar_faixa_da_playlist_laylay": _copiar_faixa_da_playlist_laylay,
        "extrair_nome_playlist": extrair_nome_playlist,
        "_resolver_query_musical_por_estilo": _resolver_query_musical_por_estilo,
        "_contexto_aponta_site_web": _contexto_aponta_site_web,
        "_eh_alvo_site_web": _eh_alvo_site_web,
        "_resolver_alvo_ambiente": _resolver_alvo_ambiente,
        "_janela_app_esta_em_foco": _janela_app_esta_em_foco,
        "_normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
        "_montar_url_site_ou_busca": _montar_url_site_ou_busca,
        "_executar_fechar_abas_paradas": _executar_fechar_abas_paradas,
        "_executar_captura_tela_intent": _executar_captura_tela_intent,
        "_bloquear_playlist_temporariamente": _bloquear_playlist_temporariamente,
        "_autorizar_acao_pratica": _autorizar_acao_pratica,
        "_autonomia_permite_execucao_musical": _autonomia_permite_execucao_musical,
        "_registrar_autoaprimoramento": _registrar_autoaprimoramento,
        "_resumo_agendamentos_para_prompt": _resumo_agendamentos_para_prompt,
        "_extrair_agendamento_local": _extrair_agendamento_local,
        "_playlist_avancar_proxima": _playlist_avancar_proxima,
        "_playlist_voltar_anterior": _playlist_voltar_anterior,
        "playlist_state": playlist_state,
        "APPS_MAP": APPS_MAP,
        "SITES_DIRECTOS": SITES_DIRECTOS,
        "APP_OPENER_AVAILABLE": APP_OPENER_AVAILABLE,
        "open_app": open_app,
        "_contexto_aponta_descanso": _contexto_aponta_descanso,
        "_executar_controle_midia_nativo": _executar_controle_midia_nativo,
        "validar_e_enviar_comando": validar_e_enviar_comando,
        "_remover_prefixo_exec": _remover_prefixo_exec,
        "limpar_resposta": limpar_resposta,
        "enviar_mensagem": enviar_mensagem,
        "_resumo_mente_integrada_para_prompt": _resumo_mente_integrada_para_prompt,
        "_texto_indica_autocorrecao": _texto_indica_autocorrecao,
        "_registrar_autocorrecao_virtual": _registrar_autocorrecao_virtual,
        "_atualizar_memoria_topicos": _atualizar_memoria_topicos,
        "_usar_modo_rapido_conversa": _usar_modo_rapido_conversa,
        "interpretar_comando_local_rapido": interpretar_comando_local_rapido,
        "_detectar_repetir_briefing": _detectar_repetir_briefing,
        "set_ultima_playlist": lambda valor: _musica_estado_set("ultima_playlist", valor),
    }
    return _executar_intencao_mente(resultado, texto_original, contexto)


_musica_conversacional_runtime = _criar_musica_conversacional_runtime_mente(
    estado_mental_getter=lambda: mente_integrada_estado,
    normalizar_texto=_normalizar_texto_com_apelidos,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    registrar_mente_curta=_registrar_mente_curta,
    executar_intencao=executar_intencao,
    registrar_resultado_execucao=_registrar_resultado_execucao,
    registrar_autoaprimoramento=_registrar_autoaprimoramento,
    log=print,
)

def _ignorar_token_solto(texto):
    palavras = texto.lower().strip().split()
    return len(palavras) == 1 and palavras[0] in {"coloca", "toca", "abre", "abra"}

def _extrair_intencao_abrir_app(texto: str):
    bruto = str(texto or "").strip()
    if not bruto:
        return None

    t = _normalizar_texto_com_apelidos(bruto)
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t or "playlist" in t:
        return None

    if any(x in t for x in ["instagram.com/direct", "instagram.com", "www.instagram.com", "instagram direct", "direct/t/"]):
        return {"intent": "OPEN_URL", "params": {"alvo": "instagram"}}
    if re.search(r"https?://\S+", bruto) and "instagram" in t:
        return {"intent": "OPEN_URL", "params": {"alvo": "instagram"}}

    m_app = re.search(
        r"\b(?:pode\s+|da\s+pra\s+|dá\s+pra\s+|por favor\s+)?"
        r"(abre|abra|abrir|inicia|iniciar|executa|executar|roda|rodar)\s+"
        r"(?:o|a|os|as|um|uma)?\s*(.+)$",
        t,
    )
    if not m_app:
        return None

    nome = _limpar_destino_pc_b((m_app.group(2) or "").strip())
    nome = re.sub(r"\s+(agora|aqui|ai|aí|por favor|pfv)$", "", nome).strip()
    nome = re.sub(r"^(o|a|os|as|um|uma)\s+", "", nome).strip()
    nome = re.sub(r"^(?:programa|app|aplicativo)\s+(?:chamado|chamada|com\s+nome|de\s+nome)\s+", "", nome).strip()
    if not nome:
        return None

    nome_norm = nome.lower()
    if nome_norm in SITES_DIRECTOS or nome_norm.startswith("site ") or nome_norm in {"youtube", "google", "spotify", "whatsapp", "chatgpt"}:
        site = nome_norm.replace("site ", "").strip()
        return {"intent": "OPEN_URL", "params": {"alvo": site}}

    candidatos = sorted(APPS_MAP.keys(), key=len, reverse=True)
    for app in candidatos:
        if nome_norm == app or nome_norm.startswith(app + " ") or app in nome_norm:
            return {"intent": "APP_OPEN", "params": {"nome_app": app}}

    return {"intent": "APP_OPEN", "params": {"nome_app": nome}}

def _segmentar_comandos_em_cadeia(texto: str) -> list:
    return _segmentar_comandos_em_cadeia_mente(
        texto,
        normalizar_texto=_normalizar_texto,
    )

def _executar_comando_em_texto(texto: str, origem: str = "") -> bool:
    return _executar_comando_em_texto_mente(
        texto,
        origem,
        detectar_repetir_briefing=_detectar_repetir_briefing,
        repetir_briefing=repetir_briefing,
        processar_comando_deterministico=processar_comando_deterministico,
        interpretar_comando_local_rapido=interpretar_comando_local_rapido,
        executar_intencao=executar_intencao,
        log=print,
    )

def processar_comandos_em_cadeia(texto: str, origem: str = "") -> bool:
    return _processar_comandos_em_cadeia_mente(
        texto,
        origem,
        normalizar_texto=_normalizar_texto_com_apelidos,
        executar_trecho=_executar_comando_em_texto,
    )


def detectar_intencao_deterministica(texto: str):
    """Reconhece comandos claros sem depender da IA conversacional."""
    contexto = {
        "normalizar_texto": _normalizar_texto_com_apelidos,
        "texto_conversa_casual_sem_acao": _texto_conversa_casual_sem_acao,
        "texto_bloqueia_playlist_agora": _texto_bloqueia_playlist_agora,
        "texto_social_curto": _texto_social_curto,
        "ignorar_token_solto": _ignorar_token_solto,
        "fluxo_prioritario_da_ia": _fluxo_prioritario_da_ia,
        "texto_expresso_melhor_no_deterministico": _texto_expresso_melhor_no_deterministico,
        "texto_depende_de_contexto": _texto_depende_de_contexto,
        "limpar_destino_pc_b": _limpar_destino_pc_b,
        "target_from_params": _target_from_params,
        "limpar_nome_playlist": _limpar_nome_playlist,
        "musica_estado_get": _musica_estado_get,
        "abas_sugeridas_fechar": _abas_sugeridas_fechar,
        "contexto_musical_ativo": _contexto_musical_ativo,
        "extrair_nome_playlist": extrair_nome_playlist,
        "mente_integrada_estado": mente_integrada_estado,
        "extrair_intencao_abrir_app": _extrair_intencao_abrir_app,
        "detectar_playlist_nome_direto": _detectar_playlist_nome_direto,
        "normalizar_query_musical": _normalizar_query_musical,
        "sites_diretos": SITES_DIRECTOS,
        "apps_map": APPS_MAP,
    }
    return _detectar_intencao_deterministica_mente(texto, contexto)


def _tentar_intencao_ai_primeiro(texto: str):
    if _interpretacao_intencao_runtime is None:
        return None
    return _interpretacao_intencao_runtime.tentar_ai_primeiro(texto)

def processar_comando_deterministico(texto: str, origem: str = "") -> bool:
    contexto = {
        "normalizar_texto": _normalizar_texto_com_apelidos,
        "refinar_contexto_mental": _refinar_contexto_mental,
        "texto_cancela_acao_agora": _texto_cancela_acao_agora,
        "resolver_comando_midia_contextual_forcado": _resolver_comando_midia_contextual_forcado,
        "resolver_comando_contextual_forcado": _resolver_comando_contextual_forcado,
        "resolver_comando_acao_geral_contextual_forcado": _resolver_comando_acao_geral_contextual_forcado,
        "resolver_repeticao_ultima_acao": _resolver_repeticao_ultima_acao,
        "tentar_intencao_ai_primeiro": _tentar_intencao_ai_primeiro,
        "detectar_intencao_deterministica": detectar_intencao_deterministica,
        "executar_intencao": executar_intencao,
        "registrar_resultado_execucao": _registrar_resultado_execucao,
        "registrar_autoaprimoramento": _registrar_autoaprimoramento,
    }
    return _executar_fluxo_intencao_mente(texto, origem, contexto)


def _texto_expresso_melhor_no_deterministico(texto: str) -> bool:
    t = _normalizar_texto_com_apelidos(texto or "")
    if not t:
        return False

    if any(p in t for p in ["playlist", "playlists"]) and re.search(r"\b(coloca|coloque|toca|toque|abre|abra|ouvir|escuta|escute|salva|salve|guarda|guarde|adiciona|adicione|lista|listar|mostra|mostrar|mostre|fale|fala|diga|diz|quais)\b", t):
        return True

    if re.fullmatch(r"(essa|esta|isso|essa aqui|esta aqui)\s+(tambem|também)", t):
        return True

    if any(v in t for v in ["organiza", "organizar", "arruma", "arrumar"]) and any(
        alvo in t for alvo in ["area de trabalho", "área de trabalho", "desktop", "tela", "janelas", "janela"]
    ):
        return True

    if any(x in t for x in ["despausa", "despausar", "retoma a musica", "retoma a música", "continua a musica", "continua a música"]):
        return True
    if any(x in t for x in ["pausa a musica", "pausa a música", "proxima musica", "próxima música", "musica anterior", "música anterior", "volta a musica", "volta a música"]):
        return True

    if re.match(r"^\s*(abre|abra|abrir|fecha|fechar|maximiza|maximizar|traz|coloca|bota|deixa)\b", t):
        if any(x in t for x in ["steam", "opera", "chrome", "edge", "vscode", "vs code", "visual studio code", "janela", "foco", "tela cheia", "fullscreen"]):
            return True
    if re.match(r"^\s*(coloca|bota|deixa|traz|maximiza|maximizar)\b", t):
        if any(x in t for x in ["ele", "ela", "isso"]) and any(x in t for x in ["foco", "tela cheia", "fullscreen", "na frente", "pra frente", "para frente"]):
            return True

    if re.match(r"^\s*(cria|criar|crie|apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\b", t):
        if any(x in t for x in ["pasta", "arquivo", "ela", "ele", "isso", "essa", "esse"]):
            return True

    if "dentro dela" in t and "pasta" in t:
        return True

    return False

def _handle_sugestao_confirmacao(texto):
    global sugestao_bloqueada_ate

    comando_sugerido = _continuidades_get("comando_sugerido")
    comando_sugerido_payload = _continuidades_get("comando_sugerido_payload")
    comando_sugerido_estado = _continuidades_get("comando_sugerido_estado", "NONE")
    comando_sugerido_ts = _continuidades_get("comando_sugerido_ts", 0.0)

    if comando_sugerido_estado != "PENDING_CONFIRM" or not comando_sugerido:
        return False

    if time.time() - float(comando_sugerido_ts or 0.0) > 60:
        _resetar_sugestao()
        return False

    sugestao_txt = {
        "SYS_MODE_CODE": "ativar Modo Code (limpar abas vazias e tocar música de foco)",
        "SYS_MODE_GAMER": "ativar Modo Gamer (pausar música e fechar abas de estudo)",
        "SYS_ORGANIZE_DOWNLOADS": "organizar Downloads",
        "EXPLAIN_ERROR": "explicar o erro do navegador",
        "RELOAD_PAGE": "recarregar a página para tentar corrigir",
        "OPEN_SITE_ALT": "abrir um site alternativo"
    }.get(comando_sugerido, comando_sugerido)

    confirmado = _classificar_confirmacao_local(texto)
    if confirmado is None:
        confirmado = interpretar_confirmacao_llm(texto, sugestao_txt)
    if confirmado is None and "mas" in texto.lower():
        confirmado = True

    if confirmado is True:
        sugestao = comando_sugerido
        payload = comando_sugerido_payload
        original_payload = payload if isinstance(payload, dict) else {}
        _resetar_sugestao()

        if "mas" in texto.lower() and isinstance(payload, dict):
            payload = _merge_intent_llm(payload, texto)

        if sugestao == "SYS_MODE_CODE":
            _executar_combo_modo_code(payload if isinstance(payload, dict) else {})
            oq = str(original_payload.get("music_query") or "lofi focus").strip().lower()
            nq = str((payload if isinstance(payload, dict) else {}).get("music_query") or oq).strip()
            if nq and nq.lower() != oq:
                falar_com_lipsync(f"Beleza, ambiente pronto, mas troquei o Lo-fi pelo mestre {nq}. Boa escolha, Pedro!", "debochada", 2)
            else:
                falar_com_lipsync("Beleza, modo Code ligado. Eu limpei a bagunça e botei música pra tua cabeça funcionar.", "debochada", 2)
            return True

        if sugestao == "SYS_MODE_GAMER":
            _executar_combo_modo_gamer(payload if isinstance(payload, dict) else {})
            falar_com_lipsync("Modo Gamer ativado. Agora fica mais fácil focar.", "calma", 1)
            return True

        if sugestao == "SYS_ORGANIZE_DOWNLOADS":
            _executar_combo_organizacao(payload if isinstance(payload, dict) else {})
            falar_com_lipsync("Downloads na mira. Eu organizei o caos pra você não se perder.", "debochada", 2)
            return True

        if sugestao == "EXPLAIN_ERROR":
            err_txt = ""
            try:
                if isinstance(payload, dict):
                    err_txt = str(payload.get("erro") or payload.get("linha") or "")
            except Exception:
                err_txt = ""
            messages.append({"role": "user", "content": texto})
            mensagens_ia = list(messages)
            mensagens_ia.append({"role": "user", "content": "Explique este erro/alerta do navegador de forma clara e curta, com um passo a passo do que fazer agora:\n" + err_txt})
            mensagens_ia.append({"role": "system", "content": "Não use [EXEC]."})
            bot_raw = enviar_mensagem(mensagens_ia, _com_tools=False)
            bot = _remover_prefixo_exec(limpar_resposta(bot_raw))
            if bot:
                print(f"Laylay [{current_emotion} lvl{emotion_level}]: {bot}")
                messages.append({"role": "assistant", "content": bot})
                falar_com_lipsync(bot, current_emotion, emotion_level)
            return True

        if sugestao == "RELOAD_PAGE":
            alvo = ""
            try:
                if isinstance(payload, dict):
                    alvo = str(payload.get("url") or "").strip()
            except Exception:
                alvo = ""
            if alvo:
                enviar_comando_chrome("reload_url", {"url": alvo})
            _confirmar_execucao_debochada(texto, "O usuário confirmou e o Python recarregou a página no Chrome. Responda curto, debochada, confirmando. Não use [EXEC].")
            return True

        if sugestao == "OPEN_SITE_ALT":
            return bool(
                executar_intencao(
                    {"intent": "OPEN_URL", "params": {"alvo": "https://www.cobasi.com.br"}},
                    texto,
                )
            )

        return False

    if confirmado is False:
        try:
            sugestao_bloqueada_ate[comando_sugerido] = time.time() + 600
        except Exception:
            pass
        _resetar_sugestao()
        falar_com_lipsync(_resposta_conversa_local(texto), "calma", 1)
        return True

    return False

def ajustar_humor(delta: int, motivo: str = "desconhecido"):
    contexto = {
        "humor_level": humor_level,
        "humor_last_update": humor_last_update,
        "humor_history": humor_history,
    }
    novo = _ajustar_humor_mente(contexto, delta, motivo)
    globals()["humor_level"] = contexto.get("humor_level", novo)
    globals()["humor_last_update"] = contexto.get("humor_last_update", time.time())
    globals()["humor_history"] = contexto.get("humor_history", humor_history)
    return novo

def get_humor_prompt():
    """Retorna uma descrição natural do humor atual para o system prompt"""
    contexto = {
        "humor_level": humor_level,
        "humor_last_update": humor_last_update,
        "humor_history": humor_history,
    }
    return _get_humor_prompt_mente(contexto)

def detectar_gatilhos_instintivos(texto: str):
    """Reações automáticas sem passar pelo Grok"""
    contexto = {
        "is_speaking": is_speaking,
        "interrupt_event": interrupt_event,
        "barge_in_count": BARGE_IN_COUNT,
        "barge_in_window": BARGE_IN_WINDOW,
        "humor_level": humor_level,
        "humor_last_update": humor_last_update,
        "humor_history": humor_history,
    }
    emocao, nivel = _detectar_gatilhos_instintivos_mente(
        contexto, texto, normalizar_cb=_normalizar_texto_com_apelidos
    )
    globals()["BARGE_IN_COUNT"] = int(contexto.get("barge_in_count", BARGE_IN_COUNT))
    globals()["humor_level"] = int(contexto.get("humor_level", humor_level))
    globals()["humor_last_update"] = float(contexto.get("humor_last_update", humor_last_update))
    globals()["humor_history"] = list(contexto.get("humor_history", humor_history) or humor_history)
    return emocao, nivel

def processar_comando_ia(resposta_texto: str):
    return _processar_comando_ia_mente(resposta_texto, FALLBACK_FALA_NEUTRA)


_executar_controle_midia_nativo = _executar_controle_midia_nativo_mente


def _executar_exec(cmd: str, arg):
    if _contexto_exec_runtime is None:
        raise RuntimeError("Contexto de execução EXEC ainda não foi inicializado.")
    return _contexto_exec_runtime.executar(cmd, arg)


_normalizar_nome_app = _normalizar_nome_app_mente
_buscar_executavel = _buscar_executavel_mente
abrir_programa = _abrir_programa_mente
filtrar_apenas_fala = partial(_filtrar_apenas_fala_mente, historico=None, fallback_fala=FALLBACK_FALA_NEUTRA)

limpar_diccao_e_ruido = _limpar_diccao_e_ruido_mente


def transcrever_com_whisper(audio):
    return _transcrever_com_whisper_mente(audio, modelo_whisper=modelo_whisper)

def get_status_humor_prompt():
    """Retorna o texto que vai para o Grok/Gemini"""
    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx)
    return _montar_status_humor_prompt_mente(
        ctx,
        percepcao,
        humor_fallback=humor_level,
        emocao_fallback=current_emotion,
        periodo_fallback=_contexto_horario_atual(),
        descricao_emocao_cb=_descricao_emocao_mente,
        perfil_comportamento_cb=_perfil_comportamento_emocional_mente,
    )
    
parsear_resposta_json = partial(_parsear_resposta_json_mente, fallback_fala=FALLBACK_FALA_NEUTRA)


def gerar_resposta_exec_ia(texto: str):
    global ws_loop, _musica_busca_fila, _musica_busca_query
    if 'ws_loop' in globals() and ws_loop:
        try:
            asyncio.run_coroutine_threadsafe(asyncio.to_thread(_gerar_resposta_exec_ia_sync, texto), ws_loop)
        except Exception as e:
            print(f"Erro ao jogar IA pro background: {e}")
            import threading
            threading.Thread(target=_gerar_resposta_exec_ia_sync, args=(texto,), daemon=True).start()
    else:
        import threading
        threading.Thread(target=_gerar_resposta_exec_ia_sync, args=(texto,), daemon=True).start()

def _gerar_resposta_exec_ia_sync(texto: str):
    if _resposta_ia_runtime is None:
        print("⚠️ [IA] Runtime de resposta ainda não foi inicializado.")
        return
    _resposta_ia_runtime.processar(texto)


def _atualizar_estado_modo_chat(ativo: bool) -> None:
    global MODO_CHAT, conversa_ativa
    MODO_CHAT = bool(ativo)
    conversa_ativa = bool(ativo)


def _definir_modo_chat(ativo: bool, origem: str = "desconhecida") -> str:
    if _modo_chat_runtime is None:
        return "Modo chat ainda não foi inicializado."
    resultado = _modo_chat_runtime.definir(ativo, origem=origem)
    return str(resultado.get("fala") or "")


def _gerar_abertura_modo_chat() -> str:
    if _abertura_chat_runtime is None:
        return "Modo chat ativado. Agora eu fico no papo e largo os comandos por um instante."
    return _abertura_chat_runtime.gerar()


_interpretacao_intencao_runtime = _criar_interpretacao_intencao_runtime_mente(
    contexto_getter=lambda: {
        "estado": {
            "messages": messages,
            "mente_integrada_estado": mente_integrada_estado,
            "playlist_state": playlist_state,
            "playlists_carregadas": playlists_carregadas,
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
        "messages": messages,
        "current_emotion": current_emotion,
        "emotion_level": emotion_level,
    },
    enviar_mensagem=enviar_mensagem,
    limpar_resposta=limpar_resposta,
    remover_prefixo_exec=_remover_prefixo_exec,
    log=print,
)


_modo_chat_runtime = _criar_modo_chat_runtime_mente(
    estado_getter=lambda: {
        "modo_chat": MODO_CHAT,
        "conversa_ativa": conversa_ativa,
    },
    estado_setter=_atualizar_estado_modo_chat,
    messages_getter=lambda: messages,
    fala_confirmacao=_fala_de_confirmacao_variada,
    gerar_abertura=_gerar_abertura_modo_chat,
    falar=falar_com_lipsync,
    salvar_memoria=salvar_memoria,
    log=print,
)


def _alternar_modo_chat_por_hotkey(ativo: bool) -> None:
    try:
        _definir_modo_chat(ativo, origem="hotkey")
    except Exception as e:
        print(f"⚠️ [CHAT] Falha ao alternar modo chat pela hotkey: {e}")


def registrar_hotkeys_modo_chat() -> bool:
    """Registra atalhos globais do modo chat."""
    try:
        keyboard.add_hotkey(HOTKEY_MODO_CHAT_LIGA, lambda: threading.Thread(target=_alternar_modo_chat_por_hotkey, args=(True,), daemon=True).start())
        keyboard.add_hotkey(HOTKEY_MODO_CHAT_DESLIGA, lambda: threading.Thread(target=_alternar_modo_chat_por_hotkey, args=(False,), daemon=True).start())
        print(f"⌨️ [CHAT] Hotkeys registradas: {HOTKEY_MODO_CHAT_LIGA} (liga) | {HOTKEY_MODO_CHAT_DESLIGA} (desliga)")
        return True
    except Exception as e:
        print(f"⚠️ [CHAT] Não consegui registrar hotkeys do modo chat: {e}")
        return False


def _escutar_texto_do_chat_terminal() -> None:
    """Lê texto do terminal enquanto o modo chat estiver ativo."""
    if not hasattr(sys, "stdin") or not sys.stdin:
        return
    try:
        if not sys.stdin.isatty():
            return
    except Exception:
        return

    while True:
        try:
            if not MODO_CHAT and not conversa_ativa:
                time.sleep(0.25)
                continue
            with _PRINT_LOCK:
                _RAW_PRINT("")
                _RAW_PRINT("💬 Você:")
            texto = input("> ").strip()
            if texto:
                try:
                    gerar_resposta_exec_ia(texto)
                except Exception as e:
                    print(f"⚠️ [CHAT] Falha ao processar texto digitado: {e}")
        except (EOFError, KeyboardInterrupt):
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ [CHAT] Erro no leitor de texto do terminal: {e}")
            time.sleep(0.5)


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
    is_speaking_getter=lambda: bool(is_speaking),
)
_gmail_nao_lidos_cache = _gmail_runtime.nao_lidos_cache
_gmail_silenciar_remetente = _gmail_runtime.silenciar_remetente
_gmail_buscar_nao_lidos = _gmail_runtime.buscar_nao_lidos
_gmail_falar_resumo_estiloso = _gmail_runtime.falar_resumo_estiloso
_gmail_resetar_check = _gmail_runtime.resetar_check
gmail_daemon = _gmail_runtime.daemon

_contexto_prompt_runtime = _criar_contexto_prompt_runtime_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    resumo_mente_integrada=_resumo_mente_integrada_para_prompt,
    formatar_playlists=_formatar_playlists_para_prompt,
    get_status_humor_prompt=get_status_humor_prompt,
    base_system_prompt=BASE_SYSTEM_PROMPT,
    estado_getter=lambda: {
        "messages": messages,
        "humor_level": humor_level,
        "aba_titulo_atual": _chrome_estado.aba_titulo_atual,
        "aba_url_atual": _chrome_estado.aba_url_atual,
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
        "_normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
        "ctypes": ctypes,
        "VK_MEDIA_PLAY_PAUSE": VK_MEDIA_PLAY_PAUSE,
        "VK_MEDIA_NEXT_TRACK": VK_MEDIA_NEXT_TRACK,
        "VK_MEDIA_PREV_TRACK": VK_MEDIA_PREV_TRACK,
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
        "abrir_programa": abrir_programa,
        "fechar_programa": fechar_programa,
        "_enviar_pc_b": _enviar_pc_b,
        "_detectar_foco_app_local": _detectar_foco_app_local,
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
        "criar_pasta": criar_pasta,
        "criar_ou_editar_arquivo": criar_ou_editar_arquivo,
        "deletar_item": deletar_item,
    },
    percepcao={
        "registrar_memoria_visual": registrar_memoria_visual,
        "_capturar_tela_base64": _capturar_tela_base64,
        "_analisar_com_groq": _analisar_com_groq,
        "_obter_contexto_perceptivo": _obter_contexto_perceptivo,
    },
    agenda_email={
        "_agendamentos_load": _agendamentos_load,
        "_agendamentos_save": _agendamentos_save,
        "_gmail_buscar_nao_lidos": _gmail_buscar_nao_lidos,
        "_gmail_falar_resumo_estiloso": _gmail_falar_resumo_estiloso,
    },
    execucao={
        "broadcast_command": broadcast_command,
        "_executar_exec": _executar_exec,
        "processar_comando_deterministico": processar_comando_deterministico,
    },
    autonomia={
        "_autorizar_acao_pratica": _autorizar_acao_pratica,
        "_autonomia_permite_execucao_musical": _autonomia_permite_execucao_musical,
    },
    estado_getter=lambda: {
        "messages": messages,
        "current_emotion": current_emotion,
        "emotion_level": emotion_level,
        "playlists_carregadas": playlists_carregadas,
        "_gmail_nao_lidos_cache": _gmail_nao_lidos_cache,
        "ws_loop": ws_loop,
        "_abas_sugeridas_fechar": _abas_sugeridas_fechar,
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
    },
    autoaprimoramento={
        "_registrar_autoaprimoramento": _registrar_autoaprimoramento,
        "_registrar_autocorrecao_virtual": _registrar_autocorrecao_virtual,
        "MAX_TENTATIVAS_AUTOCORRECAO": MAX_TENTATIVAS_AUTOCORRECAO,
    },
    estado_getter=lambda: {
        "messages": messages,
        "current_emotion": current_emotion,
        "emotion_level": emotion_level,
        "_falhas_consecutivas": _falhas_consecutivas,
    },
)


def _definir_messages_resposta_ia(novas_messages):
    global messages
    messages = novas_messages if isinstance(novas_messages, list) else []


_resposta_ia_runtime = _criar_resposta_ia_runtime_mente(
    contexto_getter=lambda: {
        "modo_chat_runtime": _modo_chat_runtime,
        "modo_chat": MODO_CHAT,
        "conversa_ativa": conversa_ativa,
        "contexto_inicio": _contexto_inicio_chat,
        "processar_inicio_fluxo": _processar_inicio_fluxo_resposta_ia_mente,
        "usar_modo_rapido": _usar_modo_rapido_conversa,
        "processar_comandos_imediatos": processar_comandos_imediatos,
        "processar_pre_fluxos": _processar_pre_fluxos_antes_ia_mente,
        "contexto_prompt_runtime": _contexto_prompt_runtime,
        "get_messages": lambda: messages,
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
        "atualizar_memoria_topicos": _atualizar_memoria_topicos,
        "processar_comando_deterministico": processar_comando_deterministico,
        "contexto_dispatch_runtime": _contexto_dispatcher_runtime,
        "executar_comandos_json": _executar_comandos_json_mente,
        "contexto_finalizacao_runtime": _contexto_finalizacao_runtime,
        "finalizar_execucao": _finalizar_execucao_resposta_ia_mente,
    },
    log=print,
)


# ====================== FIM DAS FUNÇÕES GMAIL ======================

def main():
    """Ponto de entrada principal da Laylay."""
    try:
        carregar_memoria()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao carregar memória: {e}")

    try:
        init_memoria_contexto_diaria()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao iniciar memória de contexto diária: {e}")

    try:
        _carregar_playlists_para_memoria()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao carregar playlists: {e}")

    try:
        _iniciar_worker_de_falas()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao iniciar worker de falas: {e}")

    try:
        threading.Thread(target=run_ws_server_in_thread, daemon=True, name="Laylay-WS").start()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao iniciar WebSocket: {e}")

    try:
        threading.Thread(target=briefing_matinal, daemon=True, name="Laylay-Briefing").start()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao iniciar briefing: {e}")

    try:
        threading.Thread(target=gmail_daemon, daemon=True, name="Laylay-Gmail").start()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao iniciar Gmail daemon: {e}")

    try:
        _servicos_background_runtime.iniciar_varios(
            {
                "Laylay-Agenda": _agenda_daemon,
                "Laylay-Rotina": monitor_rotina_daemon,
                "Laylay-Porteiro": _porteiro_daemon,
                "Laylay-Saude": _monitor_saude_daemon,
            }
        )
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao conectar serviços em background: {e}")

    try:
        registrar_hotkeys_modo_chat()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao registrar hotkeys do modo chat: {e}")

    try:
        threading.Thread(target=_escutar_texto_do_chat_terminal, daemon=True, name="Laylay-Chat-Terminal").start()
    except Exception as e:
        print(f"⚠️ [MAIN] Falha ao iniciar leitor de texto do chat: {e}")

    print("╭─ ◕‿◕ Laylay pronta para conversar.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando Laylay por Ctrl+C...")
        try:
            salvar_memoria()
        except Exception as e:
            print(f"⚠️ [MAIN] Falha ao salvar memória no encerramento: {e}")

if __name__ == "__main__":
    main()
