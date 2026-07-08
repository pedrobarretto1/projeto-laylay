import sys
import io
import base64
# Forca UTF-8 no terminal Windows para evitar UnicodeEncodeError
try:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import tempfile
import time
import psutil
import unicodedata
FECHAR_PROGRAMA_SOMENTE_EXPLICITO = False
import requests
import json
import os
import shutil
import keyboard
import subprocess
from functools import partial
import threading as _threading
import builtins as _builtins
import re
from typing import Optional
from mente_laylay.autonomia.comandos_sistema import (
    abrir_programa as _abrir_programa_mente,
    buscar_executavel as _buscar_executavel_mente,
    fechar_programa as _fechar_programa_mente,
    extrair_comando_rapido as _extrair_comando_rapido_mente,
    normalizar_nome_app as _normalizar_nome_app_mente,
)
from mente_laylay.autonomia.coordenador_intencao import (
    INTENTS_EXECUTAVEIS as _INTENTS_EXECUTAVEIS_MENTE,
    executar_fluxo_intencao as _executar_fluxo_intencao_mente,
)
from mente_laylay.autonomia.analise_comandos import (
    separar_comandos_blindado as _separar_comandos_blindado_mente,
    extrair_nome_e_args as _extrair_nome_e_args_mente,
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
from mente_laylay.arquivos.roteador_arquivos import (
    executar_comando_arquivos as _executar_comando_arquivos_mente,
)
from mente_laylay.memoria_mental.contexto_integrado import (
    interpretar_contexto_vivo as _interpretar_contexto_vivo_mente,
    montar_contexto_perceptivo as _montar_contexto_perceptivo_mente,
    resumo_contexto_perceptivo_para_prompt as _resumo_contexto_perceptivo_para_prompt_mente,
    resumo_mente_integrada_para_prompt as _resumo_mente_integrada_para_prompt_mente,
)
from mente_laylay.memoria_mental.contexto_compartilhado import (
    alvo_corrigido_ativo as _alvo_corrigido_ativo_mente,
    contexto_mental_ativo as _contexto_mental_ativo_mente,
    contexto_musical_ativo as _contexto_musical_ativo_mente,
    estado_mental_inicial as _estado_mental_inicial_mente,
    estrutura_arquivo_recente as _estrutura_arquivo_recente_mente,
    fluxo_prioritario_da_ia as _fluxo_prioritario_da_ia_mente,
    intencao_reexecutavel as _intencao_reexecutavel_mente,
    limpar_promessa_conversacional as _limpar_promessa_conversacional_mente,
    limpar_pergunta_aberta as _limpar_pergunta_aberta_mente,
    pergunta_aberta_ativa as _pergunta_aberta_ativa_mente,
    promessa_conversacional_ativa as _promessa_conversacional_ativa_mente,
    registrar_alvo_corrigido as _registrar_alvo_corrigido_mente,
    registrar_estrutura_arquivo_recente as _registrar_estrutura_arquivo_recente_mente,
    registrar_promessa_conversacional as _registrar_promessa_conversacional_mente,
    registrar_resultado_execucao as _registrar_resultado_execucao_mente,
    registrar_pergunta_aberta as _registrar_pergunta_aberta_mente,
    resolver_repeticao_ultima_acao as _resolver_repeticao_ultima_acao_mente,
    texto_depende_de_contexto as _texto_depende_de_contexto_mente,
    texto_parece_resposta_curta_a_pergunta as _texto_parece_resposta_curta_a_pergunta_mente,
    texto_parece_pergunta_aberta as _texto_parece_pergunta_aberta_mente,
    texto_pede_repeticao_curta as _texto_pede_repeticao_curta_mente,
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
    focar_janela as _focar_janela_mente,
    janela_esta_em_foco as _janela_esta_em_foco_mente,
    listar_programas_abertos as _listar_programas_abertos_mente,
    maximizar_janela as _maximizar_janela_mente,
    normalizar_alvo_ambiente as _normalizar_alvo_ambiente_mente,
    organizar_janelas as _organizar_janelas_mente,
    resolver_alvo_ambiente as _resolver_alvo_ambiente_mente,
)
from mente_laylay.memoria_mental.persistencia_memoria import (
    carregar_memoria as _carregar_memoria_mente,
    init_memoria_contexto_diaria as _init_memoria_contexto_diaria_mente,
    registrar_autocorrecao_virtual as _registrar_autocorrecao_virtual_mente,
    salvar_memoria as _salvar_memoria_mente,
)
from mente_laylay.memoria_mental.autoaprimoramento import (
    inferir_habilidade_autoaprimoramento as _inferir_habilidade_autoaprimoramento_mente,
    normalizar_habilidade_autoaprimoramento as _normalizar_habilidade_autoaprimoramento_mente,
    registrar_autoaprimoramento as _registrar_autoaprimoramento_mente,
    resumo_autoaprimoramento_para_prompt as _resumo_autoaprimoramento_para_prompt_mente,
    resumir_autoaprimoramento_estado as _resumir_autoaprimoramento_estado_mente,
)
from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    analisar_e_sugerir_musica as _analisar_e_sugerir_musica_mente,
    analisar_e_sugerir_rotina as _analisar_e_sugerir_rotina_mente,
    carregar_feedback_pesos as _carregar_feedback_pesos_rotina_mente,
    carregar_musica_dados as _carregar_musica_dados_mente,
    carregar_musica_feedback_pesos as _carregar_musica_feedback_pesos_mente,
    carregar_rotinas_aprendidas as _carregar_rotinas_aprendidas_mente,
    classificar_confirmacao_contextual as _classificar_confirmacao_contextual_mente,
    classificar_confirmacao_local as _classificar_confirmacao_local_mente,
    logar_atividade_atual as _logar_atividade_atual_mente,
    musica_bloqueada as _musica_bloqueada_mente,
    musica_chave_feedback as _musica_chave_feedback_mente,
    normalizar_confirmacao_texto as _normalizar_confirmacao_texto_mente,
    registrar_feedback_musica as _registrar_feedback_musica_mente,
    registrar_feedback_rotina as _registrar_feedback_rotina_mente,
    registrar_historico_musica as _musica_registrar_historico_mente,
    rotina_app_bloqueado as _rotina_app_bloqueado_mente,
    rotina_chave_feedback as _rotina_chave_feedback_mente,
    salvar_feedback_pesos as _salvar_feedback_pesos_mente,
    salvar_musica_dados as _salvar_musica_dados_mente,
    salvar_musica_feedback_pesos as _salvar_musica_feedback_pesos_mente,
    salvar_rotinas_aprendidas as _salvar_rotinas_aprendidas_mente,
)
from mente_laylay.memoria_mental.playlist_mental import (
    add_to_playlist_url as _add_to_playlist_url_mente,
    detectar_mover_playlist_texto as _detectar_mover_playlist_texto_mente,
    ensure_playlists_file as _ensure_playlists_file_mente,
    fala_playlist_conteudo_estilosa as _fala_playlist_conteudo_estilosa_mente,
    list_playlist_urls as _list_playlist_urls_mente,
    limpar_nome_playlist as _limpar_nome_playlist_mente,
    yt_clean_title as _yt_clean_title_mente,
    playlist_item_at as _playlist_item_at_mente,
    playlist_len as _playlist_len_mente,
    playlist_primeira_url as _playlist_primeira_url_mente,
    playlists_load as _playlists_load_mente,
    playlists_save as _playlists_save_mente,
    resolver_nome_playlist_contextual as _resolver_nome_playlist_contextual_mente,
)
from mente_laylay.memoria_mental.curadoria_musical import (
    sincronizar_playlists_da_laylay as _sincronizar_playlists_da_laylay_mente,
    encontrar_faixa_playlist as _encontrar_faixa_playlist_laylay_mente,
)
from mente_laylay.personalidade.falas_variadas import (
    escolher as _escolher_fala_variada,
    fala_de_confirmacao as _fala_de_confirmacao_variada,
)
from mente_laylay.personalidade.conversa_natural import (
    analisar_conversa_curta_ia as _analisar_conversa_curta_ia_mente,
    classificar_conversa_curta_local as _classificar_conversa_curta_local_mente,
    construir_fala_conversa as _construir_fala_conversa_mente,
    contexto_recente_indica_email as _contexto_recente_indica_email_mente,
    parece_elogio_ou_agradecimento_curto as _parece_elogio_ou_agradecimento_curto_mente,
    responder_agradecimento_ou_elogio as _responder_agradecimento_ou_elogio_mente,
    responder_conversa_curta_por_tipo as _responder_conversa_curta_por_tipo_mente,
    resposta_conversa_local as _resposta_conversa_local_mente,
    resposta_curta_contextual as _resposta_curta_contextual_mente,
    resposta_pergunta_curta_dependente_topico as _resposta_pergunta_curta_dependente_topico_mente,
    resposta_conversa_rapida_local as _resposta_conversa_rapida_local_mente,
    retomar_topico_quando_fluido as _retomar_topico_quando_fluido_mente,
)
from mente_laylay.autonomia.navegacao_mental import (
    handle_close_tabs_flow as _handle_close_tabs_flow_mente,
    handle_image_flow as _handle_image_flow_mente,
    handle_open_app_flow as _handle_open_app_flow_mente,
    handle_pause_next_flow as _handle_pause_next_flow_mente,
    handle_site_flow as _handle_site_flow_mente,
    handle_youtube_music_intents as _handle_youtube_music_intents_mente,
    handle_youtube_volume_flow as _handle_youtube_volume_flow_mente,
)
from mente_laylay.autonomia.execucao_ia import (
    executar_exec as _executar_exec_mente,
    filtrar_apenas_fala as _filtrar_apenas_fala_mente,
    parsear_resposta_json as _parsear_resposta_json_mente,
    processar_comando_ia as _processar_comando_ia_mente,
)
from mente_laylay.autonomia.processamento_resposta_ia import (
    corrigir_saida_malformada_da_ia as _corrigir_saida_malformada_da_ia_mente,
    extrair_aprendizados_da_ia as _extrair_aprendizados_da_ia_mente,
    extrair_tipo_interacao_da_ia as _extrair_tipo_interacao_da_ia_mente,
    limpar_resposta_da_ia as _limpar_resposta_da_ia_mente,
    salvar_aprendizados_da_ia as _salvar_aprendizados_da_ia_mente,
)
from mente_laylay.autonomia.fluxo_resposta_ia import (
    processar_inicio_fluxo_resposta_ia as _processar_inicio_fluxo_resposta_ia_mente,
)
from mente_laylay.autonomia.contexto_resposta_ia import (
    preparar_contexto_resposta_ia as _preparar_contexto_resposta_ia_mente,
)
from mente_laylay.integracao.contexto_conversa import (
    montar_contexto_conversa_natural as _montar_contexto_conversa_natural_mente,
    montar_contexto_fallback_conversa as _montar_contexto_fallback_conversa_mente,
    montar_contexto_fala_curta as _montar_contexto_fala_curta_mente,
    montar_contexto_inicio_chat as _montar_contexto_inicio_chat_mente,
)
from mente_laylay.autonomia.finalizacao_execucao_ia import (
    finalizar_execucao_resposta_ia as _finalizar_execucao_resposta_ia_mente,
)
from mente_laylay.autonomia.anti_repeticao import (
    comando_repetido_recentemente as _comando_repetido_recentemente_mente,
    registrar_comando_executado as _registrar_comando_executado_mente,
)
from mente_laylay.cognicao.interpretador_continuidade import (
    interpretar_resposta_pendente as _interpretar_resposta_pendente_mente,
)
from mente_laylay.autonomia.dispatcher_comandos_json import (
    executar_comandos_json as _executar_comandos_json_mente,
)
from mente_laylay.autonomia.fluxos_conversa import (
    handle_comando_rapido_flow as _handle_comando_rapido_flow_mente,
    handle_feedback_pendente as _handle_feedback_pendente_mente,
    handle_fuzzy_intent_flow as _handle_fuzzy_intent_flow_mente,
    handle_llm_fallback_flow as _handle_llm_fallback_flow_mente,
)
from mente_laylay.autonomia.comandos_imediatos import (
    processar_comandos_imediatos as _processar_comandos_imediatos_mente,
)
from mente_laylay.autonomia.agendamento_mental import (
    extrair_agendamento_local as _extrair_agendamento_local_mente,
    resumo_agendamentos_para_prompt as _resumo_agendamentos_para_prompt_mente,
    tentar_intencao_contextual_ai as _tentar_intencao_contextual_ai_mente,
)
from mente_laylay.autonomia.roteador_intencao import (
    bloquear_por_emocao as _bloqueio_por_emocao_mente,
    executar_intencao as _executar_intencao_mente,
)
from mente_laylay.autonomia.porteiro_acoes import (
    autorizar_acao_pratica as _autorizar_acao_pratica_mente,
    pode_sugerir_musica as _pode_sugerir_musica_mente,
    texto_conversa_contextual_sem_comando as _texto_conversa_contextual_sem_comando_mente,
    texto_conversa_casual_sem_acao as _texto_conversa_casual_sem_acao_mente,
    texto_bloqueia_playlist_agora as _texto_bloqueia_playlist_agora_mente,
    texto_bem_estar_pede_musica as _texto_bem_estar_pede_musica_mente,
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
)
# from youtubesearchpython import VideosSearch (Removido por erro de proxies no ambiente)

LOG_MODE = str(os.getenv("LAYLAY_LOG_MODE", "limpo")).lower()
LOG_VERBOSE = str(os.getenv("LAYLAY_LOG_VERBOSE", "0")).lower() in {"1", "true", "yes", "on"}
_PRINT_LOCK = _threading.RLock()
_RAW_PRINT = _builtins.print

ANSI_RESET = "\033[0m"
ANSI_CYAN = "\033[96m"
ANSI_PINK = "\033[95m"
ANSI_YELLOW = "\033[93m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_BLUE = "\033[94m"
ANSI_DIM = "\033[2m"
FALLBACK_FALA_NEUTRA = "Estou aqui, Pedro. Me fala o próximo passo."
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _usar_cores() -> bool:
    try:
        return bool(getattr(sys.stdout, "isatty", lambda: False)())
    except Exception:
        return False


def _face_para_emocao(emocao: str, nivel: Optional[int] = None) -> str:
    emo = str(emocao or "calma").lower()
    face = "◕ᴗ◕"
    if emo in {"calma", "tranquila", "focada", "suave", "normal"}:
        face = "◕‿◕"
    elif emo in {"debochada", "alegre", "animada", "feliz", "divertida", "happy"}:
        face = "≧◡≦"
    elif emo in {"envergonhada", "encabulada", "timida", "tímida", "corada", "vergonhosa"}:
        face = "(｡>///<｡)"
    elif emo in {"irritada", "brava", "nervosa", "raivosa"}:
        face = "(╬ಠ益ಠ)"
    elif emo in {"triste", "decepcionada", "melancolica", "sad"}:
        face = "｡•́︿•̀｡"
    elif emo in {"surpresa", "surpreendida", "curiosa"}:
        face = "⊙o⊙"
    elif emo in {"sono", "cansada", "preguiçosa"}:
        face = "(´･_･`)"
    if nivel and nivel >= 3:
        face += "♡"
    elif nivel and nivel >= 2:
        face += "⋆"
    return face


def _cor_para_emocao(emocao: str) -> str:
    emo = str(emocao or "calma").lower()
    if emo in {"calma", "tranquila", "focada", "suave", "normal"}:
        return ANSI_CYAN
    if emo in {"debochada", "alegre", "animada", "feliz", "divertida", "happy"}:
        return ANSI_PINK
    if emo in {"envergonhada", "encabulada", "timida", "tímida", "corada", "vergonhosa"}:
        return ANSI_YELLOW
    if emo in {"irritada", "brava", "nervosa", "raivosa"}:
        return ANSI_RED
    if emo in {"triste", "decepcionada", "melancolica", "sad"}:
        return ANSI_BLUE
    if emo in {"surpresa", "surpreendida", "curiosa"}:
        return ANSI_YELLOW
    return ANSI_GREEN


def _formatar_mensagem_laylay(texto: str, emocao: str = "calma", nivel: Optional[int] = None) -> str:
    texto_limpo = str(texto or "").strip()
    if not texto_limpo:
        texto_limpo = FALLBACK_FALA_NEUTRA
    face = _face_para_emocao(emocao, nivel)
    color = _cor_para_emocao(emocao) if _usar_cores() else ""
    reset = ANSI_RESET if _usar_cores() else ""
    return f"{color}╭─ {face} Laylay: {texto_limpo}{reset}"


def _should_log_message(text: str) -> bool:
    mensagem = str(text or "")
    mensagem_sem_ansi = ANSI_RE.sub("", mensagem)
    if not mensagem.strip():
        return False
    lower = mensagem_sem_ansi.lower()

    if LOG_VERBOSE or LOG_MODE == "debug":
        return True

    if LOG_MODE in {"0", "false", "none", "quiet"}:
        return False

    if lower.startswith(("╭─", "💬 você:", "❌", "⚠️", "🛑", "╔", "║", "╚", "> ")):
        return True

    if "laylay pronta para conversar" in lower or "modo chat ativado" in lower or "chat ligado" in lower or "conversa aberta" in lower:
        return True

    if any(token in lower for token in [
        "[debug", "[ctx", "[ws]", "[chrome]", "[yt-", "[memória", "[visão", "[auto", "[rotina", "[feedback",
        "[pc b]", "[netflix]", "[video]", "[thread crash]", "[verificar_programas]", "[playlist]",
        "[disk]", "[gmail]", "[saúde]", "[agenda]", "[porteiro]", "debug:", "success_playback"
    ]):
        return False

    if any(token in lower for token in ["erro", "falha", "timeout", "não consegui", "nao consegui", "ação não autorizada", "ação nao autorizada"]):
        return True

    if LOG_MODE in {"limpo", "essencial"}:
        if any(token in lower for token in ["[ia] gerando resposta", "[roteador", "[janela:", "appopener carregado", "websocket server", "inicializando", "carregando o novo ouvido", "ouvido whisper carregado"]):
            return True
        return False

    return True


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
import re
import random
from typing import Optional
import difflib
import unicodedata
import ast
import re
import asyncio
import json
import email as _email_lib
import email.header as _email_header

from memoria_sqlite import MemoriaSQLite

try:
    import imaplib
except ImportError:
    imaplib = None  # type: ignore

try:
    import groq as _groq_module  # type: ignore[import-untyped]
except ImportError:
    _groq_module = None  # type: ignore

def _buscar_videos_youtube_fila(query: str, limite: int = 5) -> list:
    """Retorna uma fila de URLs para dar suporte a troca autonoma."""
    try:
        url_busca = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(str(query or ''))}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        import requests, re
        res = requests.get(url_busca, headers=headers, timeout=5)
        if res.status_code == 200:
            candidatos = _extrair_resultados_youtube_busca(res.text, query, limite=max(10, limite))
            links = []
            for item in candidatos:
                link = str(item.get("url") or "").strip()
                if link and link not in links:
                    links.append(link)
                if len(links) >= limite:
                    break
            return links
    except Exception as e:
        print(f"[YT-SCRAPER] Erro fila: {e}")
    return []

def _tentar_proxima_musica():
    global _musica_busca_fila, _musica_busca_query
    if _musica_busca_fila:
        prox_link = _musica_busca_fila.pop(0)
        print(f"[CORRETOR] Tentando proximo link para '{_musica_busca_query}': {prox_link}")
        validar_e_enviar_comando("open_url", {"url": prox_link})
    else:
        print("[CORRETOR] Fila esgotada.")
        falar_com_lipsync("Pedro, não consegui achar a música certa mesmo tentando os 5 primeiros resultados.", "triste", 1)
        _musica_busca_query = ""

def _verificar_musica_autonoma(titulo_tocado: str):
    global _musica_busca_query, _musica_busca_fila
    if not _musica_busca_query:
        return
        
    query = _musica_busca_query
    prompt = f"""
Você é um juiz de buscas de música. O usuário pediu a música: "{query}"
O vídeo que começou a tocar no YouTube se chama: "{titulo_tocado}"
Esta é a música correta (ou clipe oficial, lyric video etc)? Atenção a nomes de artistas/feats.
Responda APENAS "SIM" se for a música certa, ou "NAO" se for o vídeo errado.
"""
    mensagens = [{"role": "system", "content": prompt}]
    try:
        resp = enviar_mensagem(mensagens, _com_tools=False)
        if "NAO" in resp.upper() or "NÃO" in resp.upper():
            print(f"[IA-CORRETOR] '{titulo_tocado}' NÃO é a musica pedida ({query}).")
            falar_com_lipsync("Ihh, tocou o vídeo errado. Vou pular pro próximo da busca.", "irritada", 1)
            _tentar_proxima_musica()
        else:
            print(f"[IA-CORRETOR] Aprovado '{titulo_tocado}' para '{query}'.")
            _musica_busca_query = ""
            _musica_busca_fila.clear()
    except Exception as e:
        print(f"Erro no verificador: {e}")

def _buscar_primeiro_video_youtube(query: str) -> Optional[str]:
    """
    Scraper leve usando requests para encontrar o link do primeiro vídeo.
    Substitui a lib youtube-search-python que estava com erro de proxies.
    """
    try:
        print(f"🔍 [YT-SCRAPER] Procurando para: '{query}'")
        url_busca = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(str(query or ''))}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url_busca, headers=headers, timeout=5)
        if res.status_code == 200:
            candidatos = _extrair_resultados_youtube_busca(res.text, query, limite=8)
            if candidatos:
                link = str(candidatos[0].get("url") or "").strip()
                if link:
                    print(f"✅ [YT-SCRAPER] Encontrado: {link}")
                    return link
    except Exception as e:
        print(f"⚠️ [YT-SCRAPER] Erro: {e}")
    return None


def _pontuar_resultado_youtube(query: str, titulo: str, canal: str = "") -> int:
    q = _normalizar_query_musical(query or "")
    t = _normalizar_query_musical(titulo or "")
    c = _normalizar_query_musical(canal or "")
    if not q or not t:
        return 0

    q_tokens = [tok for tok in q.split() if len(tok) > 1]
    t_tokens = [tok for tok in t.split() if len(tok) > 1]
    c_tokens = [tok for tok in c.split() if len(tok) > 1]

    score = 0
    if q == t:
        score += 120
    if q in t or t in q:
        score += 70

    for tok in q_tokens:
        if tok in t:
            score += 10
        if tok in c:
            score += 4

    termos_combo = [
        "album", "álbum", "full album", "playlist", "mix", "compilation", "coletanea",
        "coletânea", "varias musicas", "várias músicas", "varias músicas", "top ",
        "best of", "as melhores", "melhores musicas", "melhores músicas", "setlist",
        "1 hora", "1h", "2 horas", "2h", "completo", "completa",
    ]
    if any(x in t for x in termos_combo):
        score -= 90

    # Penaliza resultados muito genéricos ou de compilação quando o usuário pediu algo mais específico.
    if any(x in t for x in ["ao vivo", "live", "lyrics", "lyric", "8d", "sped up", "slowed", "remix"]):
        score -= 4
    if any(x in q for x in ["ao vivo", "live"]) and any(x in t for x in ["ao vivo", "live"]):
        score += 12
    if any(x in q for x in ["lyrics", "letra", "lyric"]):
        if any(x in t for x in ["lyrics", "letra", "lyric"]):
            score += 14
    if any(x in q for x in ["official", "oficial", "video"]):
        if any(x in t for x in ["official", "oficial", "video"]):
            score += 10

    # Prefere canção principal quando o canal também bate
    if c_tokens and any(tok in q for tok in c_tokens[:3]):
        score += 6

    return score


def _resultado_youtube_parece_faixa_unica(titulo: str, canal: str = "") -> bool:
    t = _normalizar_query_musical(titulo or "")
    if not t:
        return False
    termos_combo = [
        "album", "álbum", "full album", "playlist", "mix", "compilation", "coletanea",
        "coletânea", "varias musicas", "várias músicas", "top ", "best of",
        "as melhores", "melhores musicas", "melhores músicas", "setlist",
        "1 hora", "1h", "2 horas", "2h", "completo", "completa",
    ]
    if any(x in t for x in termos_combo):
        return False
    # Uma faixa costuma ter separador artista-musica, titulo com parenteses de anime,
    # ou no minimo um titulo curto sem promessa de coletanea.
    titulo_bruto = str(titulo or "")
    if any(sep in titulo_bruto for sep in [" - ", "|", ":", "(", ")"]):
        return True
    return 3 <= len(t.split()) <= 8


def _extrair_resultados_youtube_busca(html_text: str, query: str, limite: int = 10) -> list:
    import html as _html

    html_text = str(html_text or "")
    if not html_text:
        return []

    vistos = set()
    candidatos = []
    padrao = re.compile(r'"videoId":"([a-zA-Z0-9_-]{11})"', re.DOTALL)
    for match in padrao.finditer(html_text):
        video_id = match.group(1)
        if not video_id or video_id in vistos:
            continue
        vistos.add(video_id)
        snippet = html_text[match.start(): match.start() + 3500]
        titulo = ""
        canal = ""
        m_titulo = re.search(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]\}', snippet, re.DOTALL)
        if m_titulo:
            titulo = _html.unescape(m_titulo.group(1))
        else:
            m_titulo = re.search(r'"title":\{"simpleText":"([^"]+)"\}', snippet, re.DOTALL)
            if m_titulo:
                titulo = _html.unescape(m_titulo.group(1))

        m_canal = re.search(r'"longBylineText":\{"runs":\[\{"text":"([^"]+)"\}\]\}', snippet, re.DOTALL)
        if not m_canal:
            m_canal = re.search(r'"ownerText":\{"runs":\[\{"text":"([^"]+)"\}\]\}', snippet, re.DOTALL)
        if m_canal:
            canal = _html.unescape(m_canal.group(1))

        if not titulo:
            continue

        if not _resultado_youtube_parece_faixa_unica(titulo, canal):
            continue
        score = _pontuar_resultado_youtube(query, titulo, canal)
        candidatos.append({
            "video_id": video_id,
            "title": titulo,
            "channel": canal,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "score": score,
        })
        if len(candidatos) >= max(limite * 3, 20):
            break

    if not candidatos:
        return []

    candidatos.sort(key=lambda x: (-int(x.get("score") or 0), len(str(x.get("title") or ""))))
    return candidatos[:limite]

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
    bruto = str(texto or "").strip()
    if not bruto:
        return ""
    bruto = re.sub(r"^\s*\(\s*\d+\s*\)\s*", "", bruto).strip()
    bruto = re.sub(r"^\s*\d+\s*[-–:]\s*", "", bruto).strip()

    t = _normalizar_texto_com_apelidos(bruto)
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""

    t = re.sub(
        r"^(?:quero\s+ouvir|quero\s+tocar|toca|toque|coloca|coloque|abre|abrir|pode\s+abrir|bota|poe|põe|me\s+mostra|me\s+deixa\s+ouvir)\s+",
        "",
        t,
    )
    t = re.sub(r"^(?:a|o|as|os|uma|um|essa|esse|essa\s+mesma)\s+", "", t)
    t = re.sub(r"\b(música|musica|song|faixa|track)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""

    m = re.search(r"^(.+?)\s+(?:da|do|de|dos|das|by)\s+(.+)$", t)
    if m:
        musica = m.group(1).strip()
        artista = m.group(2).strip()
        if musica and artista:
            return f"{musica} {artista}".strip()

    return t

limpar_resposta_da_ia = partial(
    _limpar_resposta_da_ia_mente,
    limpar_texto_fala_cb=_limpar_texto_fala_ia,
    fallback_fala=FALLBACK_FALA_NEUTRA,
)

def _saida_ia_parece_malformada(texto: str) -> bool:
    s = str(texto or "").strip()
    if not s:
        return False
    if re.search(r'(?i)\[EXEC:.*?\]', s):
        return True
    if re.search(r'(?i)\b(open_url|youtube_search|youtube_play|close_tab|close_specific_tab|open_app|close_app)\b', s):
        return True
    if ("{" in s or "}" in s) and not re.search(r'(?i)"?(fala|comandos|acao|alvo)"?\s*:', s):
        return True
    return False

def _corrigir_saida_malformada_da_ia(texto_usuario: str, resposta_bruta: str):
    return _corrigir_saida_malformada_da_ia_mente(texto_usuario, resposta_bruta, enviar_mensagem)


extrair_aprendizados_da_ia = _extrair_aprendizados_da_ia_mente
extrair_tipo_interacao_da_ia = _extrair_tipo_interacao_da_ia_mente


def salvar_aprendizados_da_ia(resposta_bruta):
    return _salvar_aprendizados_da_ia_mente(resposta_bruta, MEMORIA_SQLITE)


def _comando_repetido_recentemente(acao: str, alvo: str, janela_s: float = 18.0) -> bool:
    return _comando_repetido_recentemente_mente(_ULTIMOS_COMANDOS_EXECUTADOS, acao, alvo, janela_s=janela_s)


def _registrar_comando_executado(acao: str, alvo: str) -> None:
    _registrar_comando_executado_mente(_ULTIMOS_COMANDOS_EXECUTADOS, acao, alvo)


def _normalizar_texto_curto(texto: str) -> str:
    bruto = str(texto or "").lower()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acento).strip()


def _contexto_navegador_relevante(linha: str) -> bool:
    t = _normalizar_texto_curto(linha)
    if not t:
        return False
    bloqueios = [
        "localhost:1455",
        "sign into codex",
        "id_token=",
        "needs_setup=",
        "platform_url=",
        "auth.openai.com",
        "localhost",
        "127.0.0.1",
        "chrome-extension://",
        "moz-extension://",
        "edge-extension://",
        "about:blank",
    ]
    if any(b in t for b in bloqueios):
        return False
    return True


def _topico_memoria_valido(topico: str) -> bool:
    t = _normalizar_texto_curto(topico)
    if not t:
        return False
    genericos = {
        "playlist", "musica", "música", "youtube", "netflix", "ia", "pc",
        "conversa", "chat", "hora", "hoje", "agora", "isso", "essa", "esse",
    }
    if t in genericos:
        return False
    if len(re.findall(r"[a-z0-9_-]{3,}", t)) <= 1 and t not in {"anime", "manga", "filme", "serie", "jogo", "trabalho"}:
        return False
    return True


def _extrair_topico_conversa(texto: str, topico_anterior: str = "") -> str:
    """Extrai um tema curto para manter a memória de conversa viva."""
    t = _normalizar_texto_curto(texto)
    if not t:
        return str(topico_anterior or "").strip()

    if any(p in t for p in [
        "homem aranha", "spider man", "spiderman", "peter parker", "marvel", "dc",
        "anime", "manga", "filme", "serie", "série", "jogo", "games", "gaming",
        "trabalho", "pc", "ia", "inteligencia artificial", "inteligência artificial",
        "musica", "música", "playlist", "youtube", "netflix", "homem-aranha",
    ]):
        for tema in [
            "homem aranha", "peter parker", "marvel", "anime", "manga", "filme", "serie",
            "jogo", "trabalho", "pc", "ia", "música", "youtube", "netflix",
        ]:
            if tema in t:
                return tema

    if any(p in t for p in ["ele", "ela", "isso", "fato", "verdade", "kkk", "haha", "rs", "boa", "verdade"]):
        return str(topico_anterior or "").strip()

    if any(p in t for p in ["playlist", "musica", "música", "youtube", "netflix", "ia", "pc"]):
        if len(re.findall(r"[a-z0-9_-]{3,}", t)) <= 2:
            return str(topico_anterior or "").strip()

    stop = {
        "voce", "você", "gosta", "curte", "acha", "pensa", "prefere", "me", "disso",
        "daquilo", "sobre", "mais", "muito", "bem", "tipo", "qual", "como", "porque",
        "pq", "pra", "para", "que", "isso", "essa", "esse", "aquela", "aquele",
        "hoje", "ontem", "agora", "aqui", "ali", "pra", "pro", "vai", "ser", "tem",
        "tenho", "tá", "ta", "bom", "ok", "certo", "verdade", "fato",
    }
    tokens = [tok for tok in re.findall(r"[a-z0-9_-]{3,}", t) if tok not in stop]
    if not tokens:
        return str(topico_anterior or "").strip()
    topico = " ".join(tokens[:3]).strip()
    if len(topico) < 3:
        return str(topico_anterior or "").strip()
    return topico


def _atualizar_memoria_topicos(texto_usuario: str, resposta_ia: str = "") -> None:
    """Atualiza a memória curta de tópicos recentes."""
    global topicos_conversa_recente, ultimo_topico_conversa, ultimo_topico_ts

    texto_base = str(texto_usuario or "").strip()
    topico = _extrair_topico_conversa(texto_base, ultimo_topico_conversa)
    if not topico:
        return

    agora = time.time()
    ultimo_topico_conversa = topico
    ultimo_topico_ts = agora

    topicos_conversa_recente = [t for t in topicos_conversa_recente if str(t).strip().lower() != topico.lower()]
    topicos_conversa_recente.append(topico)
    if len(topicos_conversa_recente) > 8:
        topicos_conversa_recente = topicos_conversa_recente[-8:]


def _formatar_topicos_conversa_local() -> str:
    linhas = []
    if ultimo_topico_conversa:
        linhas.append(f"Tópico ativo: {ultimo_topico_conversa}")
    if topicos_conversa_recente:
        linhas.append("Tópicos recentes: " + "; ".join(topicos_conversa_recente[-5:]))
    return "\n".join(linhas)


def _fala_e_fallback_neutro(fala: str) -> bool:
    t = _normalizar_texto_curto(str(fala or ""))
    if not t:
        return True
    neutros = {
        "to contigo pedro continua",
        "tô contigo pedro continua",
        "estou aqui pedro me fala o proximo passo",
        "estou aqui pedro me fala o próximo passo",
        "ok",
        "certo",
        "beleza",
        "entendi",
        "pronto",
        "sim",
        "claro",
    }
    return t in neutros


_texto_social_curto = _texto_social_curto_mente


def _contexto_gate_conversa() -> dict:
    return {
        "mente": dict(mente_integrada_estado or {}),
        "foco_vivo": _foco_vivo_atual(),
        "ultimo_topico": ultimo_topico_conversa,
    }


_texto_tem_comando_explicito = _texto_tem_comando_explicito_mente


def _texto_conversa_contextual_sem_comando(texto: str) -> bool:
    return _texto_conversa_contextual_sem_comando_mente(texto, _contexto_gate_conversa())


def _texto_conversa_casual_sem_acao(texto: str) -> bool:
    """Reconhece conversa casual que nao deve entrar nos roteadores de comando."""
    if _texto_tem_comando_explicito(texto):
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


def _musica_estado_update(**campos):
    global estado_musical
    estado_musical = _atualizar_estado_musical_mente(estado_musical, **campos)
    return estado_musical


def _percepcao_get(chave: str, default=None):
    try:
        return (estado_percepcao or {}).get(chave, default)
    except Exception:
        return default


def _percepcao_set(chave: str, valor):
    global estado_percepcao
    estado_percepcao = _atualizar_estado_percepcao_mente(estado_percepcao, **{chave: valor})
    return valor


def _percepcao_update(**campos):
    global estado_percepcao
    estado_percepcao = _atualizar_estado_percepcao_mente(estado_percepcao, **campos)
    return estado_percepcao


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
    """Retrato minimo para o porteiro central decidir sem executar nada."""
    return {
        "playlist_bloqueada": _playlist_bloqueada_agora(),
        "playlist_ativa": bool(str(playlist_state.get("name") or "").strip()),
        "auto_next_playlist": bool(str(playlist_state.get("name") or "").strip()),
        "ultima_playlist": str(_musica_estado_get("ultima_playlist") or "").strip(),
        "mente": dict(mente_integrada_estado or {}),
        "messages": messages,
    }


_texto_pede_playlist_explicitamente = _texto_pede_playlist_explicitamente_mente
_texto_pede_musica_explicitamente = _texto_pede_musica_explicitamente_mente


def _texto_bem_estar_pede_musica(texto: str) -> bool:
    """Contexto humano onde uma sugestão musical pode fazer sentido, mas não executar sozinha."""
    return _texto_bem_estar_pede_musica_mente(texto)


def _autonomia_pode_sugerir_musica_agora() -> bool:
    """Sugestão musical precisa nascer do momento, não de rotina antiga solta."""
    return _pode_sugerir_musica_mente(_contexto_porteiro_acoes())


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
    )


def _analisar_conversa_curta_ia(texto_usuario: str) -> dict:
    return _analisar_conversa_curta_ia_mente(_contexto_conversa_natural(), texto_usuario)


def _contexto_fala_curta() -> dict:
    return _montar_contexto_fala_curta_mente(
        current_emotion=current_emotion,
        mente_integrada_estado=mente_integrada_estado,
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


def _promessa_conversacional_atual() -> dict | None:
    try:
        return _promessa_conversacional_ativa_mente(mente_integrada_estado, ttl_s=180.0)
    except Exception:
        return None


def _limpar_promessa_conversacional() -> None:
    global mente_integrada_estado
    try:
        mente_integrada_estado = _limpar_promessa_conversacional_mente(mente_integrada_estado)
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
    pergunta = _pergunta_aberta_atual()
    if not pergunta:
        return False
    t = str(texto_usuario or "").strip()
    if not t:
        return False
    try:
        if _resolver_pergunta_curta_contextual_intencao(t):
            return False
    except Exception:
        pass
    try:
        if interpretar_comando_local_rapido(_normalizar_texto_com_apelidos(t)):
            return False
    except Exception:
        pass
    try:
        if _resolver_comando_midia_contextual_forcado(t):
            return False
    except Exception:
        pass
    try:
        if _resolver_comando_janela_contextual_forcado(t):
            return False
    except Exception:
        pass
    try:
        return _texto_parece_resposta_curta_a_pergunta_mente(t, _normalizar_texto_curto)
    except Exception:
        return False


def _responder_pergunta_aberta(texto_usuario: str) -> str:
    pergunta = _pergunta_aberta_atual() or {}
    pergunta_txt = str(pergunta.get("pergunta") or "").strip()
    topico = str(pergunta.get("topico") or "").strip()
    t = _normalizar_texto_curto(texto_usuario)

    _limpar_pergunta_aberta()

    if any(p in t for p in ["sim", "pode", "quero", "bora", "vai", "manda", "claro", "aham", "uhum", "isso", "isso mesmo", "é sim", "e sim", "pode ser"]):
        foco = _foco_vivo_atual()
        foco_tipo = str(foco.get("tipo") or "").lower()
        foco_topico = str(foco.get("topico") or foco.get("alvo") or topico or "").strip()
        if foco_tipo in {"opiniao", "opinião", "conversa"} and foco_topico:
            return _responder_conversa_curta_por_tipo("OPINION", f"o que voce acha de {foco_topico}?")
        if topico:
            return _ajustar_fala_por_horario(random.choice([
                f"Fechado. Então seguimos por {topico}.",
                f"Beleza, peguei: é {topico}. Vou nessa linha.",
                f"Aí sim. Continuo por {topico}, sem largar o fio.",
            ]), texto_usuario)
        return _ajustar_fala_por_horario(random.choice([
            "Fechado. Peguei tua resposta e sigo nesse caminho.",
            "Beleza, então vamos por aí.",
            "Tá, entendi o sim. Vou continuar nessa linha.",
        ]), texto_usuario)

    if any(p in t for p in ["nao", "não", "agora nao", "agora não", "melhor nao", "melhor não"]):
        return _ajustar_fala_por_horario(random.choice([
            "Tranquilo, deixo isso de lado então.",
            "Beleza, sem forçar. Guardei a ideia no bolso.",
            "Tá, não mexo nisso agora.",
        ]), texto_usuario)

    if any(p in t for p in ["bem", "de boa", "tranquilo", "tranquila", "suave", "otimo", "ótimo", "legal"]):
        return _ajustar_fala_por_horario(random.choice([
            "Que bom. Aí meu circuito até respira mais leve.",
            "Aí sim, gosto de te ouvir assim.",
            "Bom saber. Então seguimos com a energia um pouco mais bonita.",
        ]), texto_usuario)

    if any(p in t for p in ["mal", "cansado", "cansada", "triste", "mais ou menos", "indo"]):
        return _ajustar_fala_por_horario(random.choice([
            "Entendi. Então eu baixo um pouco o ritmo e fico contigo sem apertar.",
            "Pego o clima. Se quiser, a gente vai mais devagar agora.",
            "Tá, senti esse peso aí. Posso ficar no modo companhia, sem te cobrar nada.",
        ]), texto_usuario)

    if pergunta_txt:
        return _ajustar_fala_por_horario(random.choice([
            f"Peguei tua resposta para o que eu perguntei. Vou considerar isso no assunto.",
            f"Entendi. Isso responde aquela minha pergunta, então não vou puxar outro caminho do nada.",
            f"Tá, conectei com minha pergunta anterior. Seguimos por esse fio.",
        ]), texto_usuario)

    return _ajustar_fala_por_horario("Entendi. Vou seguir por esse fio.", texto_usuario)


def _contexto_recente_indica_email() -> bool:
    return _contexto_recente_indica_email_mente(_contexto_conversa_natural())


def _resolver_pergunta_curta_contextual_intencao(texto_usuario: str) -> dict | None:
    t = _normalizar_texto_curto(texto_usuario)
    if not t or len(t.split()) > 10:
        return None

    pergunta_email = any(p in t for p in [
        "o que eles falam",
        "o que eles me falam",
        "o que os emails falam",
        "o que falam",
        "me fala deles",
        "fala deles",
        "pode ler",
        "pode ver",
        "le eles",
        "lê eles",
        "ler eles",
    ])
    if pergunta_email and _contexto_recente_indica_email():
        return {"intent": "EMAIL_READ", "params": {}}

    return None


def _resposta_pergunta_curta_dependente_topico(texto_usuario: str) -> str:
    return _resposta_pergunta_curta_dependente_topico_mente(_contexto_conversa_natural(), texto_usuario)


def _responder_agradecimento_ou_elogio(texto_usuario: str) -> str:
    return _responder_agradecimento_ou_elogio_mente(_contexto_conversa_natural(), texto_usuario)


def _classificar_conversa_curta_local(texto_usuario: str) -> dict:
    return _classificar_conversa_curta_local_mente(_contexto_conversa_natural(), texto_usuario)


def _resposta_curta_contextual(texto_usuario: str, tipo: str = "") -> str:
    return _resposta_curta_contextual_mente(_contexto_conversa_natural(), texto_usuario, tipo)


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

    if cat == "ia_timeout":
        falar_com_lipsync(random.choice([
            "Meu modelo demorou demais pra me responder agora. Tenta de novo em alguns segundos.",
            "Eu fiquei esperando a resposta e ela não voltou a tempo. Me chama de novo já já.",
            "A resposta travou no caminho. Daqui a pouco eu tento de novo contigo.",
        ]), "calma", 1)
        return

    if cat == "ia_api":
        falar_com_lipsync(random.choice([
            "Minha conexão com o cérebro local deu ruim agora. Tenta de novo daqui a pouquinho.",
            "O meu lado da IA tropeçou feio agora. Me chama de novo em instantes.",
            "Perdi o contato com a parte que pensa mais fundo. Se repetir já já, eu tento de novo.",
        ]), "calma", 1)
        return

    if cat == "execucao":
        if alvo:
            falar_com_lipsync(random.choice([
                f"Eu entendi o pedido, mas travou na hora de mexer em {alvo}.",
                f"Peguei a ideia, só que a execução de {alvo} não fechou direito.",
                f"Não foi falta de entender; foi {alvo} que não colaborou na prática.",
            ]), "calma", 1)
            return
        falar_com_lipsync(random.choice([
            "Eu entendi o que você quis, mas a execução tropeçou no caminho.",
            "Não foi tua fala que falhou; fui eu que não consegui fechar a ação agora.",
            "Peguei o pedido, só que a parte prática desandou no meio.",
        ]), "calma", 1)
        return

    if any(p in texto_norm for p in ["como voce", "como você", "tudo bem", "ta bem", "tá bem", "tudo na paz", "de boa"]):
        falar_com_lipsync(random.choice([
            "Eu ouvi teu tom, só não fechei a leitura direito. Me pergunta de novo sem pressa.",
            "Quase peguei, mas a curva ficou torta na minha cabeça. Pode repetir?",
            "Entendi que era papo, só não encaixei tua frase direito. Tenta mais uma vez pra mim.",
        ]), "calma", 1)
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

    falar_com_lipsync(random.choice([
        "Me perdi um pouco nessa curva. Fala de outro jeito pra mim.",
        "Não fechei tua frase direito aqui. Repete com outras palavras?",
        "Eu quase peguei, mas faltou encaixar a ideia. Tenta de novo pra mim.",
    ]), "calma", 1)


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


def _retomar_topico_quando_fluido(texto_usuario: str) -> str:
    """Retoma o tópico anterior quando a fala atual é curta e casual."""
    return _retomar_topico_quando_fluido_mente(_contexto_conversa_natural(), texto_usuario)

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

def _resumo_contexto_perceptivo_para_prompt() -> str:
    """Formato curto para injetar percepção contextual no prompt da IA."""
    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx)
    return _resumo_contexto_perceptivo_para_prompt_mente(ctx, percepcao)

def _resumo_mente_integrada_para_prompt(texto_usuario: str = "") -> str:
    """Agrupa memoria, percepcao, emocao, humor e rotina num unico retrato."""
    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx, texto_usuario)
    texto_base = str(texto_usuario or "").strip()
    mente = dict(mente_integrada_estado or {})
    auto_resumo = ""
    aprendizados = ""
    memoria_quente = ""
    topicos_prompt = ""
    try:
        auto_resumo = _resumo_autoaprimoramento_para_prompt(limit=4)
    except Exception:
        pass

    try:
        if texto_base:
            aprendizados = MEMORIA_SQLITE.formatar_aprendizados_relevantes_para_prompt(texto_base, limit=4)
    except Exception:
        pass

    try:
        memoria_quente = MEMORIA_SQLITE.formatar_memoria_quente_para_prompt(limit=4, max_chars=800)
    except Exception:
        pass

    try:
        topicos_prompt = MEMORIA_SQLITE.formatar_topicos_conversa_para_prompt(limit=4)
    except Exception:
        pass

    return _resumo_mente_integrada_para_prompt_mente(
        ctx=ctx,
        percepcao=percepcao,
        mente=mente,
        auto_resumo=auto_resumo,
        aprendizados=aprendizados,
        memoria_quente=memoria_quente,
        topicos_prompt=topicos_prompt,
    )

def _registrar_mente_curta(texto_usuario: str = "", resposta_ia: str = "", intencao: str = "", alvo: str = "", escopo: str = "", habilidade: str = "") -> None:
    global mente_integrada_estado
    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}

    texto_usuario = str(texto_usuario or "").strip()
    resposta_ia = str(resposta_ia or "").strip()
    intencao = str(intencao or "").strip()
    alvo = str(alvo or "").strip()
    escopo = str(escopo or "").strip()
    habilidade = str(habilidade or "").strip()

    if texto_usuario:
        estado["ultima_entrada"] = texto_usuario
        entradas = list(estado.get("ultimas_entradas") or [])
        entradas.append(texto_usuario[:160])
        estado["ultimas_entradas"] = entradas[-8:]
    if resposta_ia:
        estado["ultima_resposta"] = resposta_ia[:180]
        try:
            if _texto_parece_pergunta_aberta_mente(resposta_ia):
                estado = _registrar_pergunta_aberta_mente(
                    estado,
                    resposta_ia,
                    topico=alvo or habilidade or intencao or ultimo_topico_conversa,
                    origem=habilidade or intencao or "conversa",
                )
                print(f"🧠 [PERGUNTA ABERTA] registrada: {estado.get('pergunta_aberta_texto', '')[:90]}")
            else:
                estado = _limpar_pergunta_aberta_mente(estado)
        except Exception as e:
            print(f"⚠️ [PERGUNTA ABERTA] falha ao atualizar memória: {e}")
        try:
            estado = _registrar_promessa_conversacional_mente(
                estado,
                resposta_ia,
                alvo=alvo or estado.get("ultimo_alvo") or "",
            )
        except Exception as e:
            print(f"⚠️ [PROMESSA] falha ao registrar promessa conversacional: {e}")
    if intencao:
        estado["ultima_intencao"] = intencao
    if alvo:
        estado["ultimo_alvo"] = alvo
        alvo_norm = _normalizar_texto_com_apelidos(alvo)
        if any(x in alvo_norm for x in ["steam", "opera", "chrome", "edge", "vscode", "vs code", "visual studio code"]):
            estado["ultimo_app_janela"] = alvo
        if _eh_alvo_site_web(alvo_norm):
            estado["ultimo_site_aba"] = alvo
        if habilidade.lower() in {"arquivo", "arquivos", "sistema"} or intencao.upper() in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"}:
            alvo_limpo = str(alvo or "").strip()
            if alvo_limpo:
                if "." in os.path.basename(alvo_limpo):
                    estado["ultimo_arquivo"] = os.path.basename(alvo_limpo)
                    estado["ultimo_caminho_arquivo"] = alvo_limpo
                else:
                    estado["ultima_pasta"] = alvo_limpo
    if escopo:
        estado["ultimo_escopo"] = escopo
    if habilidade:
        estado["ultima_habilidade"] = habilidade
    estado = _atualizar_foco_vivo(
        estado,
        texto=texto_usuario,
        resposta=resposta_ia,
        intencao=intencao,
        alvo=alvo,
        habilidade=habilidade,
        escopo=escopo,
    )
    estado["ts"] = time.time()
    mente_integrada_estado = estado


def _inferir_tipo_foco_vivo(intencao: str = "", habilidade: str = "", alvo: str = "", texto: str = "", resposta: str = "") -> str:
    base = _normalizar_texto_com_apelidos(" ".join([
        str(intencao or ""),
        str(habilidade or ""),
        str(alvo or ""),
        str(texto or ""),
        str(resposta or ""),
    ]))
    intent = str(intencao or "").upper().strip()
    hab = str(habilidade or "").lower().strip()
    if intent in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"} or hab in {"arquivo", "arquivos"} or any(p in base for p in ["arquivo", "pasta", ".txt"]):
        return "arquivo"
    if intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"} or hab in {"janela", "app"}:
        return "janela"
    if intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"} or hab in {"site", "navegador"}:
        return "site"
    if intent in {"SEARCH"} or hab in {"pesquisa", "search"}:
        return "pesquisa"
    if intent in {"WEATHER"} or hab in {"clima", "tempo"}:
        return "clima"
    if intent in {"EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS"} or "email" in base:
        return "email"
    if intent in {"PLAYLIST_PLAY", "PLAYLIST_ADD", "PLAYLIST_LIST", "MUSIC_SEARCH", "MEDIA_CONTROL"} or hab in {"musica", "música", "playlist", "midia"}:
        return "musica"
    if intent in {"AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO"} or hab == "agenda":
        return "agenda"
    if hab == "conversa" or not intent:
        if any(p in base for p in ["opini", "acha", "presidente", "lula", "política", "politica"]):
            return "opiniao"
        return "conversa"
    return hab or "conversa"


def _extrair_topico_foco_vivo(texto: str = "", resposta: str = "", alvo: str = "", habilidade: str = "", intencao: str = "") -> str:
    alvo_limpo = str(alvo or "").strip()
    if alvo_limpo:
        return alvo_limpo[:120]
    t = _normalizar_texto_com_apelidos(texto)
    for padrao in [
        r"(?:o que voce acha|o que você acha|voce acha|você acha|qual sua opiniao|qual sua opinião)\s+(?:do|da|de|sobre)?\s*(?P<tema>.+)$",
        r"(?:quem\s+e|quem\s+é|o\s+que\s+e|o\s+que\s+é|como\s+funciona|como\s+que\s+funciona|me\s+explica|explica|me\s+fala\s+sobre|fala\s+sobre|me\s+fala\s+de|fala\s+de)\s+(?P<tema>.+)$",
        r"(?:como assim|por que|porque|pq)\s+(?P<tema>.+)$",
    ]:
        m = re.search(padrao, t, flags=re.IGNORECASE)
        if m:
            tema = str(m.group("tema") or "").strip(" ?!.:,;")
            if tema:
                return tema[:120]
    if "lula" in t:
        return "presidente Lula"
    if "presidente" in t:
        return "presidente"
    hab = str(habilidade or "").strip()
    intent = str(intencao or "").strip()
    if hab:
        return hab[:120]
    if intent:
        return intent[:120]
    resp = str(resposta or "").strip()
    return resp[:120]


def _atualizar_foco_vivo(estado: dict, *, texto: str = "", resposta: str = "", intencao: str = "", alvo: str = "", habilidade: str = "", escopo: str = "") -> dict:
    estado = dict(estado or {})
    tipo = _inferir_tipo_foco_vivo(intencao, habilidade, alvo, texto, resposta)
    topico = _extrair_topico_foco_vivo(texto, resposta, alvo, habilidade, intencao)
    estado["foco_vivo_tipo"] = tipo
    estado["foco_vivo_alvo"] = str(alvo or topico or "").strip()[:160]
    estado["foco_vivo_topico"] = str(topico or "").strip()[:160]
    estado["foco_vivo_habilidade"] = str(habilidade or tipo or "").strip()[:80]
    estado["foco_vivo_intencao"] = str(intencao or "").strip()[:80]
    estado["foco_vivo_texto"] = str(texto or "").strip()[:180]
    estado["foco_vivo_resposta"] = str(resposta or "").strip()[:180]
    estado["foco_vivo_escopo"] = str(escopo or "").strip()[:80]
    estado["foco_vivo_ts"] = time.time()
    return estado


def _foco_vivo_atual(ttl_s: float = 480.0) -> dict:
    try:
        estado = dict(mente_integrada_estado or {})
        ts = float(estado.get("foco_vivo_ts") or 0.0)
        if not ts or time.time() - ts > ttl_s:
            return {}
        return {
            "tipo": str(estado.get("foco_vivo_tipo") or "").strip(),
            "alvo": str(estado.get("foco_vivo_alvo") or "").strip(),
            "topico": str(estado.get("foco_vivo_topico") or "").strip(),
            "habilidade": str(estado.get("foco_vivo_habilidade") or "").strip(),
            "intencao": str(estado.get("foco_vivo_intencao") or "").strip(),
            "texto": str(estado.get("foco_vivo_texto") or "").strip(),
            "resposta": str(estado.get("foco_vivo_resposta") or "").strip(),
            "idade_s": max(0.0, time.time() - ts),
        }
    except Exception:
        return {}


def _intencao_reexecutavel(intent: str) -> bool:
    return _intencao_reexecutavel_mente(intent)


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
    try:
        if not executou or not isinstance(resultado, dict):
            return
        estado = dict(mente_integrada_estado or {})
        intent = str(resultado.get("intent") or resultado.get("acao") or "").strip().upper()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        apps_sem_janela_contextual = {
            "microsoft store",
            "store",
            "ms store",
            "loja microsoft",
            "loja",
        }
        if intent in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
            app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
            if app and _normalizar_texto_com_apelidos(app) not in apps_sem_janela_contextual:
                estado["ultimo_app_janela"] = app
                estado["ultimo_alvo"] = app
            elif app:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = app
                estado["ultimo_alvo"] = app
        elif intent in {"OPEN_URL", "CLOSE_TAB"}:
            alvo_web = str(params.get("alvo") or params.get("url") or params.get("nome_app") or "").strip()
            if alvo_web:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = alvo_web
        elif intent == "MEDIA_CONTROL":
            estado["ultima_habilidade"] = "midia"
            estado["ultimo_alvo"] = str(params.get("platform") or params.get("acao") or "musica").strip() or "musica"
            estado["ultimo_escopo"] = str(params.get("platform") or "music").strip()
        alvo_foco = str(
            params.get("alvo")
            or params.get("nome_app")
            or params.get("nome_playlist")
            or params.get("query")
            or params.get("nome")
            or params.get("arquivo_nome")
            or params.get("item")
            or estado.get("ultimo_alvo")
            or ""
        ).strip()
        habilidade_foco = {
            "APP_OPEN": "janela",
            "CLOSE_APP": "janela",
            "MAXIMIZE_WINDOW": "janela",
            "OPEN_URL": "site",
            "CLOSE_TAB": "site",
            "SITE_ENTER": "site",
            "SEARCH": "pesquisa",
            "WEATHER": "clima",
            "PLAYLIST_PLAY": "playlist",
            "PLAYLIST_ADD": "playlist",
            "PLAYLIST_LIST": "playlist",
            "MUSIC_SEARCH": "musica",
            "MEDIA_CONTROL": "midia",
            "CREATE_FOLDER": "arquivos",
            "DELETE_ITEM": "arquivos",
            "EMAIL_READ": "email",
            "EMAIL_SYNC": "email",
            "AGENDAR_LEMBRETE": "agenda",
            "LISTAR_AGENDAMENTOS": "agenda",
            "BRIEFING_REPEAT": "conversa",
        }.get(intent, str(estado.get("ultima_habilidade") or "").strip())
        estado = _atualizar_foco_vivo(
            estado,
            texto=texto,
            resposta=status or ("executado" if executou else "falhou"),
            intencao=intent,
            alvo=alvo_foco,
            habilidade=habilidade_foco,
        )
        mente_integrada_estado = estado
    except Exception:
        pass


def _texto_pede_repeticao_curta(texto: str) -> bool:
    return _texto_pede_repeticao_curta_mente(texto, _normalizar_texto_com_apelidos)


def _resolver_repeticao_ultima_acao(texto: str):
    return _resolver_repeticao_ultima_acao_mente(
        texto,
        mente_integrada_estado,
        _normalizar_texto_com_apelidos,
    )

def _normalizar_habilidade_autoaprimoramento(nome: str) -> str:
    return _normalizar_habilidade_autoaprimoramento_mente(nome)

def _inferir_habilidade_autoaprimoramento(resultado: dict = None, texto: str = "") -> str:
    return _inferir_habilidade_autoaprimoramento_mente(resultado, texto)

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

def _resumir_autoaprimoramento_estado(estado: dict = None, limit: int = 4) -> str:
    return _resumir_autoaprimoramento_estado_mente(estado, limit=limit)

def _resumo_autoaprimoramento_para_prompt(limit: int = 4) -> str:
    try:
        return _resumo_autoaprimoramento_para_prompt_mente(autoaprimoramento_estado, limit=limit)
    except Exception:
        return "Autoaprimoramento: indisponível."

def _refinar_contexto_mental(texto: str, resultado: dict = None) -> None:
    """Cria um retrato curto e compartilhado entre habilidades."""
    txt = str(texto or "").strip()
    if not txt:
        return
    intencao = ""
    alvo = ""
    escopo = ""
    habilidade = ""
    if isinstance(resultado, dict):
        intencao = str(resultado.get("intent") or resultado.get("acao") or "").strip()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        alvo = str(params.get("nome_playlist") or params.get("nome_app") or params.get("query") or params.get("url") or params.get("alvo") or "").strip()
        escopo = str(params.get("target") or params.get("modo") or params.get("platform") or "").strip()
        habilidade = str(resultado.get("habilidade") or resultado.get("skill") or "").strip()
    _registrar_mente_curta(txt, "", intencao, alvo, escopo, habilidade)

def _contexto_aponta_descanso(texto_extra: str = "") -> bool:
    """Decide se o contexto atual pede modo descanso em vez de iniciativa."""
    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx, texto_extra)
    texto_extra = str(texto_extra or "").strip().lower()
    amostra = " ".join([
        ctx["assunto"],
        ctx["title"],
        " ".join(ctx["logs_recentes"]),
        ctx["topico_ativo"],
        texto_extra,
    ]).lower()
    sinais_descanso = ["sono", "cansad", "dorm", "descans", "boa noite", "madrugada", "sleep", "apagar"]
    sinais_foco = ["codigo", "código", "program", "vs code", "vscode", "debug", "trabalho", "estudo", "foco"]

    if percepcao.get("conclusao") == "descanso" and int(percepcao.get("confianca") or 0) >= 1:
        return True
    if percepcao.get("conclusao") in {"foco", "musica", "pesquisa", "organizacao", "inicio_dia"}:
        return False
    if any(s in amostra for s in sinais_descanso):
        return True
    if ctx["periodo"] in {"madrugada", "noite"} and not any(s in amostra for s in sinais_foco):
        return True
    return False

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
    """Ajusta saudações e observações leves para combinar com o contexto atual."""
    fala = str(fala or "").strip()
    if not fala:
        return fala

    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx, texto_usuario)
    periodo = ctx["periodo"]
    texto_lower = str(texto_usuario or "").strip().lower()
    fala_lower = fala.lower()
    contexto_gatilho = " ".join(
        [
            ctx["assunto"],
            ctx["title"],
            " ".join(ctx["logs_recentes"]),
            ctx["topico_ativo"],
            " ".join(ctx["topicos_recentes"]),
        ]
    ).lower()
    contexto_descanso = any(k in contexto_gatilho for k in ["sono", "cansad", "dorm", "descans", "noite", "madrugada", "sleep"])
    contexto_foco = any(k in contexto_gatilho for k in ["codigo", "código", "program", "vs code", "vscode", "debug", "estudo", "trabalho", "foco"])
    contexto_musica = any(k in contexto_gatilho for k in ["musica", "música", "spotify", "youtube", "playlist", "som"])
    contexto_inicio_dia = any(k in contexto_gatilho for k in ["acord", "manh", "bom dia", "começando", "inicio do dia", "iniciando"])

    if "bom dia" in texto_lower:
        if contexto_descanso and periodo in {"madrugada", "noite"}:
            return _escolher_fala_variada([
                "Bom dia, Pedro. Mas esse corpo aí tá pedindo descanso, não cumprimento.",
                "Bom dia meio torto, Pedro. Parece que teu corpo ainda tá em modo descanso.",
                "Bom dia, mas teu contexto tá pedindo cama, não café.",
            ])
        if contexto_inicio_dia or periodo == "manha":
            return _escolher_fala_variada([
                "Bom dia, Pedro. Bora aproveitar a manhã.",
                "Bom dia, Pedro. Hora de fazer o dia acontecer.",
                "Bom dia. Vamos começar essa manhã direito.",
            ])
        if periodo == "madrugada":
            return _escolher_fala_variada([
                "Boa madrugada, Pedro. Ainda tá cedo demais até pra fingir que é dia.",
                "Boa madrugada. O relógio tá claramente fora de hora pra bom dia.",
                "Madrugada, Pedro. Isso aí ainda não virou manhã.",
            ])
        if periodo == "tarde":
            return _escolher_fala_variada([
                "Boa tarde, Pedro. Meio atrasado, mas valeu a intenção.",
                "Boa tarde. Chegou com um pequeno atraso, mas chegou.",
                "Boa tarde, Pedro. Essa saudação veio no timing caprichado demais.",
            ])
        return _escolher_fala_variada([
            "Boa noite, Pedro. Esse bom dia veio meio perdido, mas eu aceito.",
            "Boa noite, Pedro. Esse bom dia tropeçou no relógio.",
            "Boa noite. Esse cumprimento veio atravessado, mas tudo bem.",
        ])

    if "boa tarde" in texto_lower:
        if contexto_descanso and periodo == "madrugada":
            return _escolher_fala_variada([
                "Boa madrugada, Pedro. Essa tarde aí tá sonhando alto.",
                "Madrugada, Pedro. Essa tarde ainda não foi autorizada.",
                "Tá de madrugada, mas a saudação veio de tarde.",
            ])
        if periodo == "manha":
            return _escolher_fala_variada([
                "Bom dia ainda, Pedro. A tarde tá adiantada demais.",
                "Ainda é manhã, Pedro. Essa tarde chegou cedo demais.",
                "Bom dia, porque a tarde ainda nem acordou.",
            ])
        if contexto_inicio_dia:
            return _escolher_fala_variada([
                "Ainda tá com cara de começo de dia, Pedro. Tarde nenhuma decidiu chegar de verdade.",
                "O dia ainda tá começando, então essa tarde tá meio fictícia.",
                "Isso aí ainda tá com energia de manhã, não de tarde.",
            ])
        if periodo == "noite":
            return _escolher_fala_variada([
                "Boa noite, Pedro. Essa tarde já foi embora faz tempo.",
                "Boa noite. A tarde já encerrou o expediente.",
                "Noite, Pedro. A tarde já foi dormir.",
            ])
        return _escolher_fala_variada([
            "Boa tarde, Pedro.",
            "Boa tarde. Tô por aqui.",
            "Boa tarde, Pedro. Pode falar.",
        ])

    if "boa noite" in texto_lower:
        if contexto_descanso:
            return _escolher_fala_variada([
                "Boa noite, Pedro. Acho que o contexto já tá me dizendo pra baixar o ritmo.",
                "Boa noite. O contexto já pediu modo baixo.",
                "Noite, Pedro. Vou reduzir o volume do papo.",
            ])
        if periodo == "manha":
            return _escolher_fala_variada([
                "Bom dia, Pedro. Essa boa noite tá bem adiantada.",
                "Bom dia. A boa noite veio cedo demais.",
                "Pedro, isso ainda é manhã. A noite tá chutando a porta cedo.",
            ])
        if periodo == "tarde":
            return _escolher_fala_variada([
                "Ainda é tarde, Pedro. A noite tá chegando, mas não chegou.",
                "Tarde ainda, Pedro. A noite tá só ensaiando.",
                "A noite tá vindo, mas ainda não estacionou.",
            ])
        if periodo == "madrugada":
            return _escolher_fala_variada([
                "Boa madrugada, Pedro. Esse boa noite já virou plantão.",
                "Boa madrugada. O boa noite já entrou em turno extra.",
                "Madrugada, Pedro. Esse cumprimento já tá fazendo hora extra.",
            ])
        return _escolher_fala_variada([
            "Boa noite, Pedro.",
            "Boa noite. Tô por aqui.",
            "Boa noite, Pedro. Pode falar.",
        ])

    if periodo == "madrugada" and any(k in fala_lower for k in ["bom dia", "boa tarde", "horario de dia", "dia lindo"]):
        return "Pedro, isso aí tá com energia de madrugada. Melhor falar de café do que de bom dia."

    if periodo == "madrugada" and len(texto_lower.split()) <= 5 and any(k in texto_lower for k in ["vamos", "abrir", "começar", "fazer"]):
        return fala + " E no relógio? Já é madrugada, então vou ser objetiva."

    if contexto_descanso and "?" in fala and len(fala) < 90:
        return fala.rstrip(" .") + " E, sinceramente, esse contexto tá com cara de pausa."

    if contexto_foco and len(fala) < 90 and any(k in fala_lower for k in ["vamos", "começar", "seguir", "fazer", "continuar", "partir"]):
        return fala.rstrip(" .") + " Vamos no ritmo certo e sem meias distrações."

    fala_ou_texto_musical = any(
        k in (fala_lower + " " + texto_lower)
        for k in ["musica", "música", "playlist", "faixa", "som", "trilha", "youtube"]
    )
    if contexto_musica and fala_ou_texto_musical and len(fala) < 90 and any(k in fala_lower for k in ["tranquilo", "calma", "boa", "certo", "presente"]):
        return fala.rstrip(" .") + " Deixo isso no tom da trilha que você tá vivendo."

    if percepcao.get("conclusao") == "foco" and "?" not in fala and len(fala) < 100:
        if any(k in fala_lower for k in ["calma", "descansa", "devagar", "sem pressa"]):
            return fala.rstrip(" .") + " O contexto tá puxando mais pra foco do que pra pausa."
    if percepcao.get("conclusao") == "musica" and len(fala) < 100:
        if any(k in fala_lower for k in ["abrindo", "pronto", "beleza", "certo"]):
            return fala.rstrip(" .") + " Seu contexto musical tá bem claro pra mim agora."

    return fala


import pyttsx3
import sounddevice as sd
import soundfile as sf
import ctypes
import tempfile
import urllib.parse
import webbrowser
from datetime import datetime
import asyncio
import edge_tts
import threading    
from queue import Empty, Queue
from ctypes import wintypes
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import pyautogui
import pygetwindow as gw
from AppOpener import open as open_app

try:
    from pywinauto import Application
except Exception:
    Application = None
import speech_recognition as sr
import importlib
from importlib.util import find_spec
from urllib.parse import urlparse, parse_qs 
from typing import Optional

# Adicionado: Importação de websockets para resolver erro de 'websockets' not defined
import websockets
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
aba_anterior_id = None
aba_historico = []
playlist_pos = {"Carlos": 0}
interrupt_event = threading.Event()
is_speaking = False
playback_lock = threading.Lock()
_fala_fila = Queue()
_fala_worker_started = False
_fala_worker_lock = threading.Lock()
_fala_batch_window = 0.0
_fala_batch_max_items = 1
_fala_proativa_lock = threading.Lock()
_fala_proativa_buffer = []
_fala_proativa_timer = None
_fala_proativa_delay = 1.0
_fala_proativa_inicio_sistema = time.time()
_fala_proativa_janela_startup = 18.0
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
_assunto_change_ts = 0.0
_ultimo_proativo_ts = 0.0
_pending_tabs_requests = {}
_pending_active_url_requests = {}
_pending_check_tabs_requests = {}
_pending_page_content_requests = {}
_last_netflix_nav = {"url": "", "title": "", "ts": 0.0}
_pastas_contexto_cache = {"ts": 0.0, "texto": ""}
_dicionario_contexto_cache = {"versao": -1, "texto": ""}
_dicionario_paginas_versao = 0
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
# Setup (3 min): myaccount.google.com/security → Verificação em 2 etapas → Senhas de app
GMAIL_USER         = "pbarretto200@gmail.com"   # ← coloque seu Gmail aqui
GMAIL_APP_PASSWORD = "ngqrxmaphffnnbvu"  # ← App Password de 16 letras (sem espaços)
GMAIL_INTERVALO_S  = 300                     # verifica a cada 5 minutos
GMAIL_MAX_LIDOS    = 5                       # max emails lidos por voz

# Remetentes prioritários: qualquer email desses é anunciado imediatamente em voz alta
GMAIL_PRIORITARIOS = [
    "banco", "bradesco", "itau", "nubank", "inter", "santander",
    "correios", "receita", "fazenda", "prefeitura", "detran",
    "serpro", "nfe", "amazon", "mercadopago", "paypal", "ifood", "rappi",
]

# Palavras no assunto que tornam o email urgente
GMAIL_PALAVRAS_URGENTES = [
    "boleto", "fatura", "vencimento", "vence", "prazo",
    "senha", "bloqueado", "bloqueio", "suspens", "cancelamento",
    "urgente", "importante", "atenção", "atencao",
    "pix", "transação", "transferência", "cobrança", "débito",
    "último aviso", "pendente", "irregularidade", "verificação",
    "confirmação", "confirmacao", "erro", "falha", "alerta",
]

# Estado interno do daemon
_gmail_ids_vistos: set       = set()   # UIDs já anunciados nesta sessão
_gmail_ultimo_check: float   = 0.0
_gmail_nao_lidos_cache: list = []      # cache para consulta por voz
_pesquisa_tema_cache: dict = {}
_gmail_remetentes_silenciados: set = set()

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

# Fila para troca autonoma de musicas no YouTube
_musica_busca_fila = []
_musica_busca_query = ""
_musica_ultima_verificada = ""
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
_ULTIMO_TOGGLE_CHAT_TS = 0.0
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
dicionario_paginas = {}
EVENTO_PAGINA = asyncio.Event()
ULTIMO_CONTEUDO_PAGINA = ""

# ====================== PORTEIRO DO CHROME (rastreamento de abas) ======================
_tab_last_seen: dict = {}     # {url: {"title": str, "ts": float}}
_abas_sugeridas_fechar: list = []  # abas propostas no ultimo aviso
_porteiro_ultima_sugestao_ts: float = 0.0
RAM_THRESHOLD_PORTEIRO = 80   # % de RAM para disparar curadoria
ABA_IDLE_MINUTOS = 45         # minutos sem visitar para considerar "abandonada"
PORTEIRO_INTERVALO_MIN = 12   # checa a cada 12 minutos

# ====================== CONTEXTO ATUAL DO CHROME (para o novo prompt) ======================
aba_ativa_estado = _percepcao_get("aba_ativa", {"titulo": "Nenhuma aba aberta", "url": "Nenhuma URL"})
aba_titulo_atual = str(aba_ativa_estado.get("titulo") or "Nenhuma aba aberta")
aba_url_atual = str(aba_ativa_estado.get("url") or "Nenhuma URL")

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
    base = str(OPENROUTER_BASE_URL or "").lower()
    return "localhost" in base or "127.0.0.1" in base or "0.0.0.0" in base


def _llm_timeout_padrao() -> int:
    return LLM_LOCAL_TIMEOUT if _llm_endpoint_eh_local() else LLM_REMOTE_TIMEOUT


class _RespostaLLMFallback:
    def __init__(self, content: str, status_code: int = 200):
        self.status_code = status_code
        self._content = str(content or "")
        self.text = self._content

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": self._content,
                    }
                }
            ]
        }


def _conteudo_fallback_llm_local(data: dict) -> str:
    mensagens = data.get("messages") if isinstance(data, dict) else []
    texto = " ".join(str((m or {}).get("content") or "")[:500] for m in mensagens if isinstance(m, dict))
    baixo = texto.lower()
    if "intent" in baixo and "json" in baixo:
        return '{"intent":"NONE","params":{}}'
    if "responda apenas json" in baixo or "json válido" in baixo or "json valido" in baixo:
        return "{}"
    if int((data or {}).get("max_tokens") or 0) <= 5:
        return "NAO"
    return "Me perdi um pouco nessa resposta, Pedro. Segura um segundo e me fala de outro jeito."


def _compactar_payload_llm_local(data: dict) -> dict:
    novo = dict(data or {})
    novo.pop("response_format", None)
    novo.pop("tools", None)
    novo.pop("tool_choice", None)
    novo["stream"] = False
    mensagens = []
    for msg in list(novo.get("messages") or []):
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role") or "user").strip().lower()
        if role not in {"system", "user", "assistant"}:
            role = "user"
        content = str(msg.get("content") or "")
        if not content.strip():
            continue
        limite = 2500 if role == "system" else 1200
        mensagens.append({"role": role, "content": content[:limite]})
    if not mensagens:
        mensagens = [{"role": "user", "content": "Responda em português, curto e natural."}]
    if len(mensagens) > 6:
        sistemas = [m for m in mensagens if m["role"] == "system"][:1]
        mensagens = sistemas + [m for m in mensagens if m["role"] != "system"][-5:]
    novo["messages"] = mensagens
    try:
        novo["max_tokens"] = min(int(novo.get("max_tokens") or 512), 384)
    except Exception:
        novo["max_tokens"] = 384
    return novo


def _payload_precisa_compactar_llm_local(data: dict) -> bool:
    mensagens = data.get("messages") if isinstance(data, dict) else []
    if not isinstance(mensagens, list):
        return False
    total_chars = 0
    for msg in mensagens:
        if isinstance(msg, dict):
            total_chars += len(str(msg.get("content") or ""))
    try:
        max_tokens = int((data or {}).get("max_tokens") or 0)
    except Exception:
        max_tokens = 0
    # Qwen 7B local costuma estar em 4096 tokens; compactar antes evita 400.
    return total_chars > 9500 or max_tokens > 640


def _post_chat_llm(headers: dict, data: dict, timeout: Optional[int] = None):
    """Serializa chamadas ao Ollama/local LLM para evitar fila concorrente estourando timeout."""
    global _LLM_BAD_REQUEST_UNTIL
    url = f"{OPENROUTER_BASE_URL}/chat/completions"
    timeout = timeout or _llm_timeout_padrao()
    if _llm_endpoint_eh_local() and time.time() < _LLM_BAD_REQUEST_UNTIL:
        return _RespostaLLMFallback(_conteudo_fallback_llm_local(data))

    def _post(payload: dict):
        return requests.post(url, headers=headers, json=payload, timeout=timeout)

    if _llm_endpoint_eh_local():
        pegou_lock = _LLM_HTTP_LOCK.acquire(blocking=False)
        if not pegou_lock:
            print("[IA] Modelo local ocupado; aguardando a chamada anterior terminar...")
            _LLM_HTTP_LOCK.acquire()
        try:
            payload_envio = _compactar_payload_llm_local(data) if _payload_precisa_compactar_llm_local(data) else data
            resp = _post(payload_envio)
            if resp.status_code == 400:
                print(f"⚠️ [IA] 400 do modelo local. Corpo: {str(resp.text or '')[:500]}")
                retry_data = _compactar_payload_llm_local(payload_envio)
                resp_retry = _post(retry_data)
                if resp_retry.status_code != 400:
                    print("✓ [IA] Requisição local recuperada com payload compacto.")
                    return resp_retry
                print(f"⚠️ [IA] 400 persistiu no retry compacto. Corpo: {str(resp_retry.text or '')[:500]}")
                _LLM_BAD_REQUEST_UNTIL = time.time() + 20.0
                return _RespostaLLMFallback(_conteudo_fallback_llm_local(data))
            return resp
        finally:
            _LLM_HTTP_LOCK.release()
    return _post(data)

# ── GEMINI VISION API (Olho Que Tudo Vê) ─────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ====================== GROQ VISION (substitui Gemini) ======================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Modelo atual recomendado (2026) - Llama 4 Scout (melhor que o 3.2)
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
# Alternativa mais leve (se quiser economizar): "llama-3.2-11b-vision-preview"
current_tab_title = ""
SITES_DIRECTOS = {
    "youtube": "https://www.youtube.com",
    "spotify": "https://open.spotify.com",
    "wikipedia": "https://pt.wikipedia.org",
    "wikipédia": "https://pt.wikipedia.org",
    "google": "https://www.google.com",
    "netflix": "https://www.netflix.com",
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
    t = _normalizar_texto_com_apelidos(texto or "")
    if not t:
        return False
    if t in SITES_WEB_ALIAS:
        return True
    if t in SITES_DIRECTOS:
        return True
    if any(alias in t for alias in SITES_WEB_ALIAS):
        return True
    return any(dom in t for dom in ["instagram.com", "youtube.com", "netflix.com", "twitch.tv", "spotify.com", "web.whatsapp.com"])

def _contexto_aponta_site_web(texto: str = "") -> bool:
    """Usa a mente curta e o contexto vivo para decidir se algo deve ser tratado como site/aba."""
    amostra = []
    texto_norm = _normalizar_texto_com_apelidos(texto or "")
    if texto_norm:
        amostra.append(texto_norm)

    try:
        mente = dict(mente_integrada_estado or {})
    except Exception:
        mente = {}
    try:
        ctx = _obter_contexto_perceptivo()
    except Exception:
        ctx = {}

    for item in [
        mente.get("ultima_entrada"),
        mente.get("ultima_resposta"),
        mente.get("ultima_intencao"),
        mente.get("ultimo_alvo"),
        mente.get("ultima_habilidade"),
        ctx.get("exe"),
        ctx.get("title"),
        ctx.get("assunto"),
        ctx.get("topico_ativo"),
        " ".join(ctx.get("logs_recentes") or []),
        " ".join(ctx.get("topicos_recentes") or []),
    ]:
        if item:
            amostra.append(_normalizar_texto_com_apelidos(str(item)))

    txt = " | ".join([x for x in amostra if x]).strip()
    if not txt:
        return False

    gatilhos = [
        "instagram", "insta", "direct", "dm", "conversa do insta", "conversa do instagram",
        "youtube", "netflix", "twitch", "spotify", "whatsapp web", "web.whatsapp",
        "gmail", "google", "drive", "facebook", "twitter", "x.com"
    ]
    return any(g in txt for g in gatilhos)

def _normalizar_alvo_web_ou_app(alvo: str) -> str:
    """Quando o contexto aponta site, devolve o alvo normalizado para aba; caso contrário, mantém o original."""
    alvo_limpo = _normalizar_texto_com_apelidos(alvo or "")
    if not alvo_limpo:
        return ""
    if _eh_alvo_site_web(alvo_limpo) or _contexto_aponta_site_web(alvo_limpo):
        return alvo_limpo
    return alvo_limpo

def _descricao_emocao(emocao: str) -> str:
    return _descricao_emocao_mente(emocao)


def _perfil_comportamento_emocional(emocao: str) -> str:
    return _perfil_comportamento_emocional_mente(emocao)

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
- "netflix_search"    → busca na Netflix (alvo = nome do filme/série)

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
ALLOWED_ACTIONS = [
    "open_tab", "youtube_search", "open_url", "pause", "play", "next",
    "skip_forward", "skip_backward", "replay", "volume_up", "volume_down",
    "mute", "set_volume", "open_app", "netflix_search", "netflix_home",
    "switch_tab", "return_tab", "close_tab", "click_first_result",
    "youtube_control", "youtube_volume", "netflix_control", "start_netflix_navigation",
    "spinning_fish", "close_current_tab", "reload_url", "get_tabs_list", "close_tabs", 
    "update_tab", "close_specific_tab", "press", "search_universal",
    "playlist_create", "playlist_add", "playlist_list", "youtube_play",
    "search_in_page", "click", "type",   # Controle de DOM: pesquisa em paginas abertas
    "fechar_abas_paradas",               # Porteiro: fecha abas ociosas sugeridas
    "maximize_window",
    "ler_emails", "ler_emails_urgentes", "sincronizar_emails",
    "agendar_lembrete", "listar_agendamentos", "cancelar_agendamento"
]


# Escala de -10 (Fula da vida) a 10 (Extasiada de felicidade)
humor_laylay = 0 

def thread_exception_handler(args):
    """Captura qualquer erro em threads que mataria o processo"""
    print(f"❌ [THREAD CRASH] {args.exc_type.__name__} em {args.thread.name}: {args.exc_value}")
    traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
    # Não deixa o processo morrer
    print("🔄 Laylay continua rodando apesar do erro...")

threading.excepthook = thread_exception_handler

def atualizar_humor(variacao):
    global humor_laylay
    humor_laylay = max(-10, min(10, humor_laylay + variacao))

def is_valid_url(url: str) -> bool:
    """Valida se a URL é segura e bem formada (http/https)"""
    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urlparse(url)
    return all([parsed.scheme in ["http", "https"], parsed.netloc])

def ajustar_volume_sistema(nivel_percentual):
    try:
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        if devices is None: return
        
        # O segredo é pegar o EndpointVolume direto dos devices
        volume = devices.EndpointVolume 
        
        scalar_volume = max(0.0, min(1.0, float(nivel_percentual) / 100.0))
        volume.SetMasterVolumeLevelScalar(scalar_volume, None)
    except Exception as e:
        print(f"❌ Erro ao ajustar volume: {e}")

def ajustar_volume_sistema_relativo(delta_percentual):
    try:
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        if devices is None: return
        
        volume = devices.EndpointVolume
        current_vol = volume.GetMasterVolumeLevelScalar()
        new_vol = max(0.0, min(1.0, current_vol + (float(delta_percentual) / 100.0)))
        volume.SetMasterVolumeLevelScalar(new_vol, None)
    except Exception as e:
        print(f"❌ Erro ao ajustar volume relativo: {e}")

def _interromper_audio_ativo():
    """Corta a voz da Laylay na hora se o Pedro disser 'para' ou 'cala a boca'"""
    try:
        import sounddevice as sd
        # Se a Laylay estiver falando, corta a voz dela instantaneamente!
        stream = sd.get_stream()
        if stream and stream.active:
            sd.stop() 
            print("🛑 [BOCA COM FREIO] Laylay foi mandada calar a boca!")
    except Exception as e:
        pass  # Silencioso

# 🎧 Dicionário para lembrar qual era o volume antes da IA falar
volumes_originais_apps = {}

def ducking_volume(ativar=True):
    """
    Audio Ducking: Abaixa o volume dos navegadores/música quando a IA fala, 
    e restaura depois. Efeito tipo Jarvis do Iron Man!
    """
    global volumes_originais_apps
    try:
        from pycaw.pycaw import AudioUtilities
        sessions = AudioUtilities.GetAllSessions()
        
        # Lista dos apps que devem "calar a boca" para a Laylay falar
        apps_alvo = ["chrome.exe", "opera.exe", "spotify.exe", "msedge.exe", "brave.exe", "firefox.exe"]
        
        for session in sessions:
            process = session.Process
            if process and process.name().lower() in apps_alvo:
                try:
                    volume_control = session.SimpleAudioVolume
                    pid = process.pid
                    
                    if ativar:
                        # Salva o volume original (se a música tava no 100% ou 50%)
                        current_vol = volume_control.GetMasterVolume()
                        if pid not in volumes_originais_apps:
                            volumes_originais_apps[pid] = current_vol
                        
                        # Abaixa a música/vídeo para 15% (Laylay tem prioridade!)
                        volume_control.SetMasterVolume(0.15, None)
                    else:
                        try:
                            # A IA terminou de falar, restaura a música para como estava!
                            if pid in volumes_originais_apps:
                                volume_control.SetMasterVolume(volumes_originais_apps[pid], None)
                            else:
                                volume_control.SetMasterVolume(1.0, None)
                        finally:
                            # Forcado de volta a 100% ou original garantido, em caso de erro!
                            if pid in volumes_originais_apps:
                                del volumes_originais_apps[pid]
                            else:
                                try: volume_control.SetMasterVolume(1.0, None)
                                except: pass
                except:
                    pass  # Silencioso se falhar um app específico
    except Exception as e:
        pass  # Silencioso - audio ducking é opcional

def formatar_url_ou_busca(termo: str, prefer_com_br: bool = False) -> str:
    termo = termo.strip()
    termo_lower = termo.lower()
    
    # 🚀 CORREÇÃO 1: Se já for uma URL de busca ou tiver protocolo, não mexa!
    if "google.com/search" in termo_lower or termo.startswith("http"):
        return termo if termo.startswith("http") else f"https://{termo}"

    # 2. Checa sites diretos (Youtube, Netflix, etc)
    for site, url_base in SITES_DIRECTOS.items():
        if site == termo_lower: # Mudança: Usar '==' em vez de 'in' para evitar falsos positivos
            return url_base
            
    # 3. Se tem ".com" ou ".br" e não tem espaços, é um site direto
    if "." in termo and " " not in termo:
        url_tentativa = f"https://{termo}" if not termo.startswith("http") else termo
        if is_valid_url(url_tentativa):
            return url_tentativa
    
    # 4. Se falhou em tudo, busca no Google
    query = urllib.parse.quote(termo)
    if prefer_com_br:
        return f"https://www.google.com.br/search?q={query}"
    return f"https://www.google.com/search?q={query}"

def atualizar_contexto(site: Optional[str] = None, termo_busca: Optional[str] = None, aba_id: Optional[int] = None):
    global contexto_atual
    # Apenas atualiza se o valor não for None
    if site is not None: contexto_atual["site"] = site
    if termo_busca is not None: contexto_atual["termo_busca"] = termo_busca
    if aba_id is not None: contexto_atual["aba_id"] = aba_id
    _percepcao_set("contexto_web", dict(contexto_atual))

def atualizar_contexto_por_url(url: str):
    global contexto_atual
    parsed_url = urlparse(url)
    host = parsed_url.netloc
    if "youtube.com" in host:
        atualizar_contexto(site="youtube")
    elif "netflix.com" in host:
        atualizar_contexto(site="netflix")
    elif "google.com" in host:
        if "search?q=" in url:
            # Corrigido: Aspas triplas para aspas simples
            query = urllib.parse.unquote_plus(parsed_url.query.split('q=')[1].split('&')[0])
            atualizar_contexto(site="google_search", termo_busca=query)
        else:
            atualizar_contexto(site="google")
    else:
        atualizar_contexto(site="outro", termo_busca=None)

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

def _ws_log_invalid_message(message):
    print(f"🤔 [Chrome] Mensagem vazia ou inválida recebida: {message}")

def _ws_handle_tabs_list(data: dict):
    rid = str(data.get("requestId") or "")
    tabs = data.get("tabs")
    if rid and rid in _pending_tabs_requests:
        entry = _pending_tabs_requests.get(rid) or {}
        entry["tabs"] = tabs if isinstance(tabs, list) else []
        ev = entry.get("event")
        if ev:
            try:
                ev.set()
            except Exception:
                pass

def _ws_handle_active_tab_url(data: dict):
    rid = str(data.get("requestId") or "")
    url = str(data.get("url") or "")
    title = str(data.get("title") or "")
    if rid and rid in _pending_active_url_requests:
        entry = _pending_active_url_requests.get(rid)
        if isinstance(entry, asyncio.Future):
            if not entry.done():
                entry.set_result({"url": url, "title": title})
        elif isinstance(entry, dict):
            entry["url"] = url
            entry["title"] = title
            ev = entry.get("event")
            if ev:
                try:
                    ev.set()
                except Exception:
                    pass

def _ws_handle_youtube_data(data: dict):
    rid = str(data.get("requestId") or "")
    url = str(data.get("url") or "")
    title = str(data.get("title") or "")
    canal = str(data.get("canal") or data.get("channel") or "")
    if rid and rid in _pending_active_url_requests:
        entry = _pending_active_url_requests.get(rid)
        if isinstance(entry, asyncio.Future):
            if not entry.done():
                entry.set_result({"url": url, "title": title, "canal": canal})
        elif isinstance(entry, dict):
            entry["url"] = url
            entry["title"] = title
            entry["canal"] = canal
            ev = entry.get("event")
            if ev:
                try:
                    ev.set()
                except Exception:
                    pass

def _ws_handle_check_tabs_result(data: dict):
    try:
        rid = str(data.get("requestId") or "")
        tab_id = data.get("tabId", None)
        if rid and rid in _pending_check_tabs_requests:
            entry = _pending_check_tabs_requests.get(rid) or {}
            entry["tabId"] = int(tab_id) if isinstance(tab_id, int) else None
            ev = entry.get("event")
            if ev:
                try:
                    ev.set()
                except Exception:
                    pass
    except Exception:
        pass

def _ws_handle_player_event(data: dict):
    event = str(data.get("event") or "").strip().lower()
    url = str(data.get("url") or "")
    is_ad = bool(data.get("isAd"))
    duration = int(data.get("duration") or 0)
    if event == "user_click_detected":
        playlist_state["user_intervened"] = True
        print("🎧 USER_CLICK_DETECTED → playlists automáticas pausadas até o fim do vídeo atual")
        return
    if event != "video_ended":
        return
    if is_ad or duration < 60:
        return
    if not playlist_state.get("name"):
        return
    pl_nm = str(playlist_state.get("name") or "")
    if playlist_state["user_intervened"]:
        playlist_state["user_intervened"] = False
        print("🎧 Vídeo manual terminou — retomando playlist")
        print("[AUTO-NEXT] Música anterior finalizada. Carregando próxima...")
        ok_next = _playlist_avancar_proxima()
        if not ok_next:
            falar_com_lipsync(f"Acabou o show, Pedro. Essa foi a última da playlist {pl_nm}.", "debochada", 2)
        return
    if str(playlist_state.get("last_url") or "") and str(playlist_state.get("last_url") or "") != _yt_clean_url(url):
        return
    print("[AUTO-NEXT] Música anterior finalizada. Carregando próxima...")
    ok_next = _playlist_avancar_proxima()
    if not ok_next:
        falar_com_lipsync(f"Acabou o show, Pedro. Essa foi a última da playlist {pl_nm}.", "debochada", 2)
def _ws_handle_page_content(data):
    requestId = data.get("requestId")
    if requestId and requestId in _pending_page_content_requests:
        future = _pending_page_content_requests.pop(requestId)
        future.set_result(data)

def _ws_handle_user_context(data):
    global sugestao_bloqueada_ate, _ultimo_sugerido_ts, is_speaking, ultimo_open_site
    global contexto_sistema, _ultimo_proativo_ts, estado_percepcao
    kind = str(data.get("kind") or "").strip()
    detail = data.get("detail")
    url = str(data.get("url") or "").strip()
    title = str(data.get("title") or "").strip()
    if not kind and (detail is None or detail == "" or detail == {}):
        return
    linha = ""
    if kind == "nav":
        linha = f"Navegação: {title} | {url}".strip()
    elif kind == "click":
        if isinstance(detail, dict):
            label = str(detail.get("label") or "").strip()
            href = str(detail.get("href") or "").strip()
            linha = f"Clique: {label}" + (f" | {href}" if href else "")
        else:
            linha = f"Clique: {str(detail)}"
    elif kind == "console":
        if isinstance(detail, dict):
            level = str(detail.get("level") or "log").strip()
            msg = str(detail.get("message") or "").strip()
            linha = f"Console {level}: {msg}"
        else:
            linha = f"Console: {str(detail)}"
    else:
        linha = f"{kind}: {str(detail)}".strip()
    if linha and _contexto_navegador_relevante(linha):
        estado_percepcao = _registrar_log_navegador_mente(estado_percepcao, linha, limite=5)
        contexto_atual_logs[:] = list(_percepcao_get("logs_navegador", []))
        print(f"🧠 [CTX] {linha}")

    now = time.time()
    if kind == "nav" and "netflix.com" in url and "/watch" in url:
        print("✅ SUCCESS_PLAYBACK (Netflix)")
        _continuidades_update(
            comando_sugerido=None,
            comando_sugerido_payload=None,
            comando_sugerido_estado="NONE",
            comando_sugerido_ts=0.0,
        )
    if kind == "nav":
        if "spinning.fish" in url:
            globals()["fish_mode_active"] = True
            globals()["fish_mode_started_ts"] = time.time()
        else:
            if globals().get("fish_mode_active"):
                globals()["fish_mode_active"] = False
                globals()["fish_mode_started_ts"] = 0.0

    if kind == "nav":
        u = url.lower()
        if any(x in u for x in ["thingiverse.com", "printables.com", "cults3d.com", "myminifactory.com", "makerworld.com"]):
            exe = ""
            assunto = ""
            try:
                exe = str(contexto_sistema.get("exe") or "").lower()
                assunto = str(contexto_sistema.get("assunto") or "")
            except Exception:
                exe = ""
                assunto = ""
            if ("cura" in exe) or ("prusa" in exe) or (assunto == "Impressão 3D"):
                if not is_speaking and _continuidades_get("comando_sugerido_estado", "NONE") == "NONE":
                    if now - float(_ultimo_proativo_ts or 0.0) >= 1200:
                        _ultimo_proativo_ts = now
                        falar_com_lipsync("Preparando algo pra impressora 3D do seu irmão?", "calma", 1)

    if _continuidades_get("comando_sugerido_estado", "NONE") == "NONE" and now - float(_ultimo_sugerido_ts or 0.0) > 15:
        def _bloqueado(chave: str) -> bool:
            try:
                return now < float(sugestao_bloqueada_ate.get(chave, 0.0))
            except Exception:
                return False

        netflix_profile = False
        if "netflix.com" in url:
            t = title.lower()
            if ("perfil" in t) or ("profiles" in t) or ("assistindo" in t) or ("who" in t and "watch" in t) or ("/profiles" in url):
                netflix_profile = True

        if kind == "nav" and "netflix.com" in url and "/browse" in url:
            t = title.lower()
            if ("quem está assistindo" in t) or ("who" in t and "watch" in t):
                if _continuidades_get("comando_sugerido") is None and not _bloqueado("ENTRAR_PERFIL_PEDRO"):
                    _continuidades_update(
                        comando_sugerido="ENTRAR_PERFIL_PEDRO",
                        comando_sugerido_payload={"url": url, "title": title, "motivo": "browse_profile"},
                        comando_sugerido_estado="PENDING_CONFIRM",
                        comando_sugerido_ts=now,
                    )
                    _ultimo_sugerido_ts = now
                    if not is_speaking:
                        falar_com_lipsync("Pedro, quer que eu entre no perfil Pedro?", "calma", 1)

        if kind == "idle" and "netflix.com" in url and "/browse" in url and not _bloqueado("NETFLIX_PERFIL"):
            _continuidades_update(
                comando_sugerido="NETFLIX_PERFIL",
                comando_sugerido_payload={"url": url, "title": title, "motivo": "idle_browse"},
                comando_sugerido_estado="PENDING_CONFIRM",
                comando_sugerido_ts=now,
            )
            _ultimo_sugerido_ts = now
            if not is_speaking:
                falar_com_lipsync("Pedro, você ficou parado na Netflix. Quer que eu entre no teu perfil Pedro e deixe pronto?", "calma", 1)

        if netflix_profile and _continuidades_get("comando_sugerido") is None and not _bloqueado("NETFLIX_PERFIL"):
            _continuidades_update(
                comando_sugerido="NETFLIX_PERFIL",
                comando_sugerido_payload={"url": url, "title": title, "motivo": "perfil"},
                comando_sugerido_estado="PENDING_CONFIRM",
                comando_sugerido_ts=now,
            )
            _ultimo_sugerido_ts = now
            if not is_speaking:
                falar_com_lipsync("Pedro, você tá na tela de perfis da Netflix. Quer que eu entre no Pedro?", "calma", 1)

        erro_detectado = False
        erro_txt = ""
        if kind == "nav" and ("404" in (title.lower() + " " + url.lower())):
            erro_detectado = True
            erro_txt = f"{title} | {url}"
        if kind == "console" and isinstance(detail, dict):
            lvl = str(detail.get("level") or "").lower()
            msg = str(detail.get("message") or "")
            if "error" in lvl or "uncaught" in msg.lower() or "404" in msg:
                erro_detectado = True
                erro_txt = f"{linha} | {title} | {url}"

        if erro_detectado and _continuidades_get("comando_sugerido") is None:
            try:
                last_ts = float(ultimo_open_site.get("ts") or 0.0)
                last_topic = str(ultimo_open_site.get("topic") or "").lower()
                last_url = str(ultimo_open_site.get("url") or "").lower()
            except Exception:
                last_ts = 0.0
                last_topic = ""
                last_url = ""
            if now - last_ts < 25 and ("pet" in last_topic or "petz" in last_url) and not _bloqueado("OPEN_SITE_ALT"):
                _continuidades_update(
                    comando_sugerido="OPEN_SITE_ALT",
                    comando_sugerido_payload={"topic": "pet", "erro": erro_txt, "url": url, "title": title},
                    comando_sugerido_estado="PENDING_CONFIRM",
                    comando_sugerido_ts=now,
                )
                _ultimo_sugerido_ts = now
                if not is_speaking:
                    falar_com_lipsync("Ih, esse site de pet tá dando erro. Quer que eu tente outro?", "calma", 1)
                return
            lower_erro = (erro_txt or "").lower()
            if ("play" in lower_erro) or ("autoplay" in lower_erro) or ("failed" in lower_erro) or ("falhou" in lower_erro):
                if not _bloqueado("RELOAD_PAGE"):
                    _continuidades_update(
                        comando_sugerido="RELOAD_PAGE",
                        comando_sugerido_payload={"url": url, "title": title, "erro": erro_txt},
                    )
                    if not is_speaking:
                        falar_com_lipsync("Pedro, vi que o play falhou no Chrome. Queres que eu tente recarregar a página?", "calma", 1)
            else:
                if not _bloqueado("EXPLAIN_ERROR"):
                    _continuidades_update(
                        comando_sugerido="EXPLAIN_ERROR",
                        comando_sugerido_payload={"erro": erro_txt, "url": url, "title": title, "linha": linha},
                    )
        if _continuidades_get("comando_sugerido"):
            _continuidades_update(comando_sugerido_estado="PENDING_CONFIRM", comando_sugerido_ts=now)
            _ultimo_sugerido_ts = now
            if _continuidades_get("comando_sugerido") == "EXPLAIN_ERROR" and not is_speaking:
                falar_com_lipsync("Pedro, vi um erro aqui. Quer que eu explique o que aconteceu?", "calma", 1)

def armazenar_contexto_pagina(url: str, title: str, content: str):
    """Guarda a página no dicionário com limite inteligente"""
    global dicionario_paginas, _dicionario_contexto_cache, _dicionario_paginas_versao
    
    agora = time.time()
    # Limita o conteúdo (evita estourar tokens)
    conteudo_limpo = content[:6000].strip()
    
    dicionario_paginas[url] = {
        "title": title,
        "content": conteudo_limpo,
        "ts": agora,
        "resumo": ""
    }
    
    # Mantém só as 6 páginas mais recentes (evita memória infinita)
    if len(dicionario_paginas) > 6:
        mais_antiga = min(dicionario_paginas.items(), key=lambda x: x[1]["ts"])
        del dicionario_paginas[mais_antiga[0]]

    _dicionario_paginas_versao += 1
    _dicionario_contexto_cache["versao"] = -1
    _dicionario_contexto_cache["texto"] = ""
    
    print(f"📖 [VISÃO] Página salva no dicionário: {title[:60]}... ({len(conteudo_limpo)} chars)")


def get_dicionario_contexto() -> str:
    """Retorna o contexto formatado para injetar no prompt da Laylay com limite de 10.000 caracteres"""
    if not dicionario_paginas:
        return ""

    global _dicionario_contexto_cache
    versao_atual = int(globals().get("_dicionario_paginas_versao", 0) or 0)
    cache = _dicionario_contexto_cache
    if cache.get("texto") and int(cache.get("versao", -1)) == versao_atual:
        return str(cache.get("texto") or "")
    
    # Ordena por mais recente
    ordenado = sorted(
        dicionario_paginas.items(),
        key=lambda x: x[1]["ts"],
        reverse=True
    )
    
    texto = "\n\n📖 **DICIONÁRIO DE CONTEXTO ATUAL** (Páginas recentes abertas):\n"
    limite_chars = 10000
    chars_usados = 0
    
    for url, info in ordenado:
        if chars_usados >= limite_chars:
            break
            
        idade_min = int((time.time() - info["ts"]) / 60)
        resumo = info.get("resumo", "")
        conteudo = info.get("content", "")
        
        pode_usar = limite_chars - chars_usados
        conteudo_poda = conteudo[:pode_usar]
        
        texto += f"• {info['title']}\n  📍 {url}\n  ⏱️ há {idade_min}min\n"
        if resumo:
            texto += f"  📝 Resumo: {resumo}\n"
        texto += f"  📄 Conteúdo:\n{conteudo_poda}\n\n"
        
        chars_usados += len(conteudo_poda)

    texto = texto.strip()
    _dicionario_contexto_cache = {"versao": versao_atual, "texto": texto}
    return texto


def resumir_pagina_no_dicionario(url: str):
    """Chama a IA para fazer um resumo curto da página (chamado automaticamente)"""
    if url not in dicionario_paginas:
        return
    
    conteudo = dicionario_paginas[url]["content"]
    
    prompt_resumo = f"""
    Resuma em NO MÁXIMO 2 frases o conteúdo principal desta página.
    Foque apenas no que realmente importa para o Pedro.
    Página: {dicionario_paginas[url]['title']}
    
    CONTEÚDO:
    {conteudo[:4000]}
    """
    
    mensagens = [
        {"role": "system", "content": "Você é um resumidor extremamente conciso."},
        {"role": "user", "content": prompt_resumo}
    ]
    
    try:
        resumo = enviar_mensagem(mensagens, _com_tools=False)  # resumo de pagina: sem tools
        dicionario_paginas[url]["resumo"] = resumo.strip()
        print(f"📝 [VISÃO] Resumo gerado para {dicionario_paginas[url]['title'][:50]}...")
    except:
        pass

def _ws_handle_action(data: dict) -> bool:
    global current_tab_title, aba_historico, aba_anterior_id, aba_titulo_atual, aba_url_atual
    action = str(data.get("action") or "").strip()
    if action == "title_update":
        novo_titulo = str(data.get("title") or "").strip()
        if novo_titulo and novo_titulo != aba_titulo_atual:
            aba_titulo_atual = novo_titulo
            _percepcao_set("aba_ativa", {"titulo": aba_titulo_atual, "url": aba_url_atual})
            print(f"📥 [Chrome] Título atualizado → {aba_titulo_atual}")
        return True
    elif action in ("url_update", "active_tab_changed") or "url" in data:
        nova_url = str(data.get("url") or "").strip()
        novo_titulo = str(data.get("title") or "").strip()
        
        mudou = False
        if nova_url and nova_url != aba_url_atual:
            aba_url_atual = nova_url
            mudou = True
            
        if novo_titulo and novo_titulo != aba_titulo_atual:
            aba_titulo_atual = novo_titulo
            mudou = True
            
        if mudou:
            _percepcao_set("aba_ativa", {"titulo": aba_titulo_atual, "url": aba_url_atual})
            print(f"\U0001f9e0 [CTX] Aba Ativa -> [{aba_titulo_atual}] {aba_url_atual}")
            if action == "active_tab_changed":
                atualizar_contexto_por_url(aba_url_atual)
                # Porteiro: registra timestamp da ultima visita a esta URL
                if aba_url_atual and not aba_url_atual.startswith("chrome://"):
                    _tab_last_seen[aba_url_atual] = {
                        "title": aba_titulo_atual,
                        "ts": time.time()
                    }
                    
                # CORRETOR AUTONOMO VIA ABA ATIVA
                if "youtube.com/watch" in aba_url_atual and aba_titulo_atual and aba_titulo_atual != "YouTube" and not aba_titulo_atual.endswith(") YouTube"):
                    import re, threading
                    clean_title = re.sub(r'^\(\d+\)\s*', '', aba_titulo_atual).replace(" - YouTube", "").strip()
                    threading.Thread(target=_musica_registrar_historico, args=(clean_title,), daemon=True).start()
                    
                    if globals().get('_musica_busca_query') and globals().get('_musica_ultima_verificada') != aba_url_atual:
                        globals()['_musica_ultima_verificada'] = aba_url_atual
                        threading.Thread(target=_verificar_musica_autonoma, args=(clean_title,), daemon=True).start()
        return True
    if action == "netflix_status":
        status = data.get("status")
        movie = data.get("movie", "")
        if status == "id_extracted":
            video_id = data.get("id", "")
            print(f"✅ [Netflix] ID Extraído → {video_id} para {movie}")
            falar_com_lipsync(f"Achei o que você queria. Já dei o play.", "calma", 1)
        elif status == "searching_id":
            print(f"🔍 [Netflix] Escaneando links para → {movie}")
        elif status == "not_found":
            print(f"❌ [Netflix] Filme não encontrado → {movie}")
            falar_com_lipsync(f"Pedro, a Netflix tá fazendo jogo duro. Não achei o botão de play para {movie}, dá uma olhada aí.", "irritada", 2)
        return True
    if action == "manual_tab_change":
        frm = data.get("from")
        to = data.get("to")
        ft = data.get("fromTitle", "")
        tt = data.get("toTitle", "")
        if frm and to and frm != to:
            if aba_anterior_id and aba_anterior_id != to:
                aba_historico.append(aba_anterior_id)
            aba_anterior_id = to
            print(f"🔄 [Chrome] Troca de aba manual: {ft} ({frm}) → {tt} ({to})")
        return True
    if action == "tab_closed":
        closed_id = data.get("id")
        print(f"🗑️ [Chrome] Aba {closed_id} fechada.")
        aba_historico = [aid for aid in aba_historico if aid != closed_id]
        if aba_anterior_id == closed_id:
            aba_anterior_id = None
        return True
    if action == "youtube_video_started":
        video_title = data.get("title", "")
        # NOVO: Registra no aprendizado musical
        import threading
        threading.Thread(target=_musica_registrar_historico, args=(video_title,), daemon=True).start()
        
        # CORRETOR AUTONOMO:
        if globals().get('_musica_busca_query'):
            threading.Thread(target=_verificar_musica_autonoma, args=(video_title,), daemon=True).start()
        print(f"▶️ [YouTube] Vídeo iniciado: {video_title}")
        falar_com_lipsync(f"Iniciando o vídeo {video_title}. Prepare a pipoca, Pedro.", "calma", 1)
        return True
    if action == "youtube_video_paused":
        video_title = data.get("title", "")
        print(f"⏸️ [YouTube] Vídeo pausado: {video_title}")
        falar_com_lipsync(f"O vídeo {video_title} foi pausado. Precisa de algo, Pedro?", "calma", 1)
        return True
    if action == "youtube_video_resumed":
        video_title = data.get("title", "")
        print(f"▶️ [YouTube] Vídeo retomado: {video_title}")
        falar_com_lipsync(f"Retomando o vídeo {video_title}.", "calma", 1)
        return True
    if action == "youtube_video_ended":
        video_title = data.get("title", "")
        print(f"⏹️ [YouTube] Vídeo finalizado: {video_title}")
        falar_com_lipsync(f"O vídeo {video_title} terminou. O que faremos agora, Pedro?", "calma", 1)
        return True
    if action == "youtube_search_result_clicked":
        query = data.get("query", "")
        title = data.get("title", "")
        print(f"✅ [YouTube] Resultado de busca clicado para \'{query}\': {title}")
        falar_com_lipsync(f"Abrindo o vídeo \'{title}\' do YouTube.", "calma", 1)
        return True
    if action == "auto_click_status":
        status = str(data.get("status") or "").strip()
        motivo = str(data.get("motivo") or "").strip()
        if status == "erro_clique":
            print(f"❌ [AUTO-CLICK] Falhou: {motivo}")
            falar_com_lipsync("Pedro, não achei um link orgânico pra clicar.", "calma", 1)
        return True
    if action == "close_tab_status":
        status = str(data.get("status") or "").strip()
        if status == "blocked_form":
            falar_com_lipsync("Tá digitando em formulário, Pedro. Eu não vou fechar e apagar teu trabalho.", "calma", 1)
        return True
    if action == "netflix_search_opened":
        query = data.get("query", "")
        print(f"🔍 [Netflix] Busca aberta para \'{query}\'.")
        falar_com_lipsync(f"Abrindo a busca da Netflix para \'{query}\'.", "calma", 1)
        return True
    if action == "netflix_title_opened":
        title = data.get("title", "")
        print(f"✅ [Netflix] Título aberto: {title}")
        falar_com_lipsync(f"Abrindo o título \'{title}\' na Netflix. Preparando a experiência cinematográfica.", "calma", 1)
        return True
    if action == "netflix_play_started":
        title = data.get("title", "")
        print(f"▶️ [Netflix] Reprodução iniciada: {title}")
        falar_com_lipsync(f"Reprodução de \'{title}\' iniciada. Aproveite, Pedro.", "calma", 1)
        return True
    if action == "netflix_play_paused":
        title = data.get("title", "")
        print(f"⏸️ [Netflix] Reprodução pausada: {title}")
        falar_com_lipsync(f"Reprodução de \'{title}\' pausada. O que houve, Pedro?", "calma", 1)
        return True
    if action == "netflix_play_resumed":
        title = data.get("title", "")
        print(f"▶️ [Netflix] Reprodução retomada: {title}")
        falar_com_lipsync(f"Reprodução de \'{title}\' retomada.", "calma", 1)
        return True
    if action == "netflix_play_ended":
        title = data.get("title", "")
        print(f"⏹️ [Netflix] Reprodução finalizada: {title}")
        falar_com_lipsync(f"Reprodução de \'{title}\' finalizada. Próximo, Pedro?", "calma", 1)
        return True
    if action == "error":
        error_msg = data.get("message", "Erro desconhecido na extensão.")
        print(f"❌ [Chrome ERRO] {error_msg}")
        falar_com_lipsync(f"Houve um erro no Chrome: {error_msg}. Verifique, Pedro.", "irritada", 2)
        return True
    if action == "ping":
        return True
    if action:
        print(f"🤔 [Chrome] Mensagem desconhecida da extensão: {data}")
        return True
    return False

def _ws_dispatch_data(data: dict):
    t = str(data.get("type") or "").strip()
    if t == "ping":
        return
    if t == "TABS_LIST":
        _ws_handle_tabs_list(data)
        return
    if t == "CHECK_TABS_RESULT":
        _ws_handle_check_tabs_result(data)
        return
    if t == "ACTIVE_TAB_URL":
        _ws_handle_active_tab_url(data)
        return
    if t == "YOUTUBE_DATA":
        _ws_handle_youtube_data(data)
        return
    if t == "PLAYER_EVENT":
        _ws_handle_player_event(data)
        return
    if t == "USER_CONTEXT":
        _ws_handle_user_context(data)
        return
    if t == "PAGE_CONTENT":
        _ws_handle_page_content(data)
        return

    if data.get("type") != "ping":
        print(f"📥 [DEBUG Chrome] {data}")

    _ws_handle_action(data)

async def ws_handler(websocket):
    global connected_pc_b_clients

    # Identifica o tipo de cliente pela primeira mensagem
    is_pc_b = False
    try:
        first_msg_raw = await asyncio.wait_for(websocket.recv(), timeout=3.0)
        first_msg = json.loads(first_msg_raw) if first_msg_raw else {}
    except Exception:
        first_msg = {}

    if first_msg.get("type") == "pc_b_client":
        # ── AUTENTICAÇÃO PC B ──────────────────────────────────────────────
        token_recebido = first_msg.get("token")
        TOKEN_SECRETO = "Frankzane12"
        if token_recebido != TOKEN_SECRETO:
            print(f"🚫 [PC B] Conexão REJEITADA: Token inválido! ({websocket.remote_address})")
            await websocket.close()
            return
        # ───────────────────────────────────────────────────────────────────

        is_pc_b = True
        connected_pc_b_clients.add(websocket)
        print(f"[PC B] Cliente remoto conectado e AUTENTICADO! Total PC B: {len(connected_pc_b_clients)}")
    else:
        # E uma extensao Chrome — fecha as antigas
        await _ws_close_other_extensions(websocket)
        connected_extensions.add(websocket)
        print(f"[Chrome] Extensao conectada! Total: {len(connected_extensions)}")
        # Reprocessa a primeira mensagem como normal
        if isinstance(first_msg, dict):
            _ws_dispatch_data(first_msg)

    try:
        async for message in websocket:
            if not (isinstance(message, str) and message.strip()):
                continue
            try:
                data = json.loads(message)

                if is_pc_b:
                    if data.get("type") == "pc_b_screenshot":
                        # PC B mandou o print de volta → analisar com Gemini
                        img_b64 = data.get("imagem_b64", "")
                        pergunta = data.get("pergunta", "O que está acontecendo nessa tela?")
                        print(f"[VISÃO] Screenshot do PC B recebido ({len(img_b64)//1024}KB). Analisando...")
                        def _analisar_screenshot_pcb(b64, p):
                            descricao = _analisar_com_groq(b64, p)
                            print(f"[VISÃO] Groq sobre PC B: {descricao[:200]}")
                            try:
                                registrar_memoria_visual(
                                    b64,
                                    descricao,
                                    motivo="captura visual do PC B",
                                    contexto={"pc": "pc_b", "pergunta": p},
                                    emocao=current_emotion or "calma",
                                    intensidade=int(emotion_level or 1),
                                    tags=["pc_b", "visao", "captura"],
                                    origem="pc_b",
                                )
                            except Exception as e_mem:
                                print(f"⚠️ [VISÃO] Falha ao registrar memória visual do PC B: {e_mem}")
                            falar_com_lipsync(descricao[:300], current_emotion, emotion_level)
                        threading.Thread(target=_analisar_screenshot_pcb, args=(img_b64, pergunta), daemon=True).start()
                        continue

                    elif data.get("type") == "pc_b_status":
                        if data.get("status") == "error":
                            erro_msg = data.get("error", "Erro desconhecido")
                            app_err = data.get("app", "")
                            acao_err = data.get("action", "")
                            print(f"❌ [PC B] Falha remota: {erro_msg}")
                            def _notificar_erro():
                                global messages
                                informacao = (
                                    f"System: IMPORTANTE! O Computador B falhou ao tentar realizar a ação '{acao_err}' no alvo '{app_err}'. "
                                    f"O Windows lá retornou o erro: '{erro_msg}'. "
                                    "Isso é uma falha de sistema, VOCÊ DEVE avisar o usuário sobre isso AGORA mesmo para que ele saiba que não funcionou."
                                )
                                messages.append({"role": "system", "content": informacao})
                                try:
                                    bot_raw = enviar_mensagem(messages)
                                    fala, _ = limpar_resposta_da_ia(bot_raw)
                                    if fala:
                                        print(f"Laylay [Autocorreção PC B]: {fala}")
                                        messages.append({"role": "assistant", "content": fala})
                                        falar_com_lipsync(fala, "decepcionada", 2)
                                except Exception as e_ia:
                                    print(f"[PC B] Erro na autocorreção remota da IA: {e_ia}")
                            threading.Thread(target=_notificar_erro, daemon=True).start()
                        else:
                            print(f"✅ [PC B] Ação {data.get('action')} em {data.get('app', '')} concluída com sucesso!")
                    else:
                        print(f"[PC B] Mensagem recebida: {data.get('message', data.get('type', data))}")
                    continue

                # ====================== HANDLER DE VISAO ======================
                if data.get("type") == "PAGE_DATA":
                    payload = data.get("payload")
                    if payload and isinstance(payload, dict):
                        url = payload.get("url", "")
                        title = payload.get("title", "Sem titulo")
                        content = payload.get("content", "")
                        global ULTIMO_CONTEUDO_PAGINA
                        ULTIMO_CONTEUDO_PAGINA = f"SITIO: {title}\nCONTEUDO: {content}"
                        armazenar_contexto_pagina(url, title, content)
                        threading.Thread(target=resumir_pagina_no_dicionario, args=(url,), daemon=True).start()
                        EVENTO_PAGINA.set()
                        print(f"[VISAO] Pagina recebida: {title}")

                if isinstance(data, dict):
                    _ws_dispatch_data(data)

            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"Erro ao processar mensagem WS: {e}")
    except websockets.exceptions.ConnectionClosedOK:
        pass
    except websockets.exceptions.ConnectionClosedError:
        pass
    except Exception as e:
        print(f"Erro inesperado na conexao WebSocket: {e}")
    finally:
        connected_extensions.discard(websocket)
        connected_pc_b_clients.discard(websocket)
        if is_pc_b:
            print(f"[PC B] Cliente desconectado. Restantes: {len(connected_pc_b_clients)}")

async def start_ws_server():
    # Adicionado: Importação local de websockets para evitar erro de nome
    import websockets
    async with websockets.serve(ws_handler, "0.0.0.0", 8080):
        print("🚀 WebSocket Server Chrome rodando em http://localhost:8080")
        await asyncio.Future() # Mantém o servidor rodando indefinidamente

def run_ws_server_in_thread():
    global ws_loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ws_loop = loop
    print("🚀 WebSocket Server Chrome iniciado (thread-safe) — ws_loop definido")
    loop.run_until_complete(start_ws_server())

async def broadcast_command(msg: str):
    """Envio realmente assíncrono com erro visível"""
    print("DEBUG: Entrou em broadcast_command (async)")
    for client in list(connected_extensions):
        try:
            await client.send(msg)
            print("DEBUG: Mensagem enviada com sucesso para 1 cliente")
        except Exception as e:
            print(f"❌ ERRO AO ENVIAR PARA CLIENTE: {type(e).__name__} → {e}")
            connected_extensions.discard(client)

import uuid

async def solicitar_conteudo_pagina():
    """Solicita o conteúdo da página ativa da extensão do Chrome."""
    global ws_loop, connected_extensions, _pending_page_content_requests

    if not connected_extensions:
        print("❌ Nenhuma extensão conectada para solicitar conteúdo da página.")
        return {"success": False, "error": "Nenhuma extensão conectada"}

    if ws_loop is None:
        print("❌ ws_loop não inicializado.")
        return {"success": False, "error": "ws_loop não inicializado"}

    requestId = str(uuid.uuid4())
    future = ws_loop.create_future()
    _pending_page_content_requests[requestId] = future

    try:
        # Envia o comando para a extensão
        await broadcast_command(json.dumps({"action": "get_page_content", "requestId": requestId}))
        print(f"[WS] Solicitando conteúdo da página com requestId: {requestId}")

        # Aguarda a resposta da extensão
        response = await asyncio.wait_for(future, timeout=15) # Timeout de 15 segundos
        print(f"[WS] Resposta de conteúdo da página recebida para requestId: {requestId}")
        return response
    except asyncio.TimeoutError:
        print(f"❌ Timeout ao aguardar conteúdo da página para requestId: {requestId}")
        if requestId in _pending_page_content_requests:
            del _pending_page_content_requests[requestId]
        return {"success": False, "error": "Timeout ao obter conteúdo da página"}
    except Exception as e:
        print(f"❌ Erro ao solicitar conteúdo da página: {e}")
        if requestId in _pending_page_content_requests:
            del _pending_page_content_requests[requestId]
        return {"success": False, "error": str(e)}

def _netflix_tela_cheia_async():
    def worker():
        try:
            print("[NETFLIX] Aguardando carregamento para modo tela cheia....")
            time.sleep(5)
            info = solicitar_aba_ativa()
            url = str(info.get("url") or "").lower()
            if "netflix.com" not in url or "/watch" not in url:
                return
            try:
                aw = gw.getActiveWindow()
                active_title = str(getattr(aw, "title", "") or "").lower()
            except Exception:
                active_title = ""
            if not any(x in active_title for x in ["chrome", "edge", "opera"]):
                return
            pyautogui.press('tab', presses=11, interval=0.2)
            pyautogui.press('enter')
            try:
                if not is_speaking:
                    falar_com_lipsync("Cinema pronto, Pedro.", "calma", 1)
            except Exception:
                pass
        except Exception:
            pass
    threading.Thread(target=worker, daemon=True).start()

def executar_automacao_netflix(query: str):
    q = str(query or "").strip()
    print("🚀 Iniciando Automação Netflix via PyAutoGUI...")
    janela_salva = None
    titulo_ativo = ""
    try:
        janela_salva = gw.getActiveWindow()
        if janela_salva:
            try:
                print(f"✅ Janela anterior salva: {janela_salva.title}")
                titulo_ativo = str(janela_salva.title or "")
            except Exception:
                print("✅ Janela anterior salva.")
    except Exception:
        janela_salva = None

    if not garantir_aba_unica("https://www.netflix.com/"):
        return False
    time.sleep(1.2)

    try:
        active_title = ""
        try:
            aw = gw.getActiveWindow()
            active_title = str(getattr(aw, "title", "") or "")
        except Exception:
            active_title = ""
        if any(x in active_title.lower() for x in ["chrome", "edge", "opera"]):
            pass
        else:
            chrome = gw.getWindowsWithTitle('Chrome')
            if chrome:
                chrome[0].activate()
    except Exception:
        pass

    try:
        last_url = str((_last_netflix_nav.get("url") if isinstance(_last_netflix_nav, dict) else "") or "").lower()
        if "netflix.com/browse" in last_url:
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(5.0)
    except Exception:
        pass

    if not q:
        try:
            if janela_salva:
                janela_salva.activate()
        except Exception:
            pass
        return True

    if q:
        try:
            search_url = f"https://www.netflix.com/search?q={urllib.parse.quote(q)}"
            search_url = search_url.replace("searchq=", "search?q=")
            while search_url.endswith((".", ",", ")", "]")):
                search_url = search_url[:-1]
            garantir_aba_unica(search_url)
            print("🔎 Navegação direta para URL de busca")
        except Exception as e:
            print(f"❌ Falha ao navegar para busca Netflix: {e}")

    time.sleep(7)
    try:
        time.sleep(3)
        print("DEBUG: Executando sequência de 4 Tabs no card...")
        pyautogui.press('tab', presses=4, interval=0.25)
        print("Tabs enviados...")
        pyautogui.press('enter')
        print("Enter pressionado (card)...")
        time.sleep(5)
        pyautogui.press('tab', presses=2, interval=0.2)
        pyautogui.press('enter')
        print("Enter pressionado (play)...")
        _netflix_tela_cheia_async()
    except Exception as e:
        print(f"❌ Falha automação Netflix: {e}")

    if not q:
        try:
            if janela_salva:
                try:
                    print(f"🔄 Voltando para: {janela_salva.title}")
                except Exception:
                    print("🔄 Voltando para janela anterior.")
                janela_salva.activate()
        except Exception:
            pass
    return True

def executar_netflix_pedro():
    print("🚀 Entrando no perfil Pedro (Netflix)...")
    janela_salva = None
    try:
        janela_salva = gw.getActiveWindow()
    except Exception:
        janela_salva = None
    try:
        webbrowser.open("https://www.netflix.com/")
    except Exception as e:
        print(f"❌ Erro ao abrir Netflix: {e}")
        return False
    time.sleep(5)
    try:
        chrome = gw.getWindowsWithTitle('Chrome')[0]
        chrome.activate()
    except Exception:
        try:
            pyautogui.hotkey('alt', 'tab')
        except Exception:
            pass
    try:
        pyautogui.press('tab')
        pyautogui.press('enter')
    except Exception as e:
        print(f"❌ Falha ao selecionar perfil Netflix: {e}")
    try:
        if janela_salva:
            janela_salva.activate()
    except Exception:
        pass
    return True

def executar_netflix_perfil():
    try:
        win = gw.getActiveWindow()
        title = str(getattr(win, "title", "") or "")
    except Exception:
        title = ""
    try:
        wins_nf = gw.getWindowsWithTitle('Netflix')
        if wins_nf:
            try:
                wins_nf[0].activate()
            except Exception:
                pass
        else:
            wins_ch = gw.getWindowsWithTitle('Chrome')
            if wins_ch:
                try:
                    wins_ch[0].activate()
                except Exception:
                    pass
            elif "google chrome" not in title.lower():
                try:
                    pyautogui.hotkey('alt', 'tab')
                except Exception:
                    pass
    except Exception:
        pass
    time.sleep(0.4)
    try:
        pyautogui.press('tab')
        pyautogui.press('enter')
        return True
    except Exception:
        return False

def trazer_chrome_para_frente():
    try:
        wins = []
        try:
            wins = list(gw.getAllWindows() or [])
        except Exception:
            wins = []
        cand = []
        for w in wins:
            try:
                t = str(getattr(w, "title", "") or "")
            except Exception:
                t = ""
            if not t:
                continue
            tl = t.lower()
            if ("netflix" in tl) or ("google chrome" in tl) or ("chrome" in tl):
                cand.append(w)
        if cand:
            w = cand[0]
            try:
                w.activate()
            except Exception:
                pass
            try:
                w.maximize()
            except Exception:
                pass
            time.sleep(0.5)
            return True
    except Exception:
        pass
    return False

def validar_e_enviar_comando(action: str | None = None, payload: dict | None = None) -> bool:
    """ENVIO PARA O CHROME COM DEBUG TOTAL (rastreia exatamente onde para)"""
    print(f"DEBUG: Entrou em validar_e_enviar_comando → action={action} | payload={payload}")
    
    # ====================== PROTEÇÃO CONTRA None ======================
    action = str(action or "").strip()
    payload = payload if isinstance(payload, dict) else {}
    
    prefer_com_br = False
    
    if action == "entrar_no_site":
        action = "open_url"
        prefer_com_br = True

    # =====================================================================
    # 🚀 AQUI ESTÁ A MÁGICA: O PORTEIRO AGORA CONHECE OS SUPER PODERES!
    # =====================================================================
    if action not in ALLOWED_ACTIONS and action not in ["click", "type", "press", "execute_js"]:
        print(f"❌ [Chrome] Ação não autorizada: {action}")
        return False

    if action in ["open_tab", "open_url"]:
        raw = payload.get("url") or payload.get("query") or ""
        url = formatar_url_ou_busca(str(raw), prefer_com_br=prefer_com_br)
        url = str(url).strip().strip("`").strip()
        url = url.replace("searchq=", "search?q=")
        while url.endswith((".", ",", ")", "]")):
            url = url[:-1]
        payload["url"] = url
        if "query" in payload:
            payload.pop("query", None)
        if not is_valid_url(url):
            fallback = f"https://www.google.com/search?q={urllib.parse.quote(str(raw))}"
            print(f"[Navegação] 🔍 Termo '{raw}' não é URL. Convertendo para busca Google...")
            payload["url"] = fallback
            url = fallback
        atualizar_contexto_por_url(url)
        
        # Envia para a extensão para REUSO MAGICO da aba (evita poluição)
        if 'ws_loop' in globals() and ws_loop and connected_extensions:
            msg = {"action": "open_url", "url": url}
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
            print(f"📤 [Chrome] Enviando para extensão abrir/atualizar: {url}")
        else:
            # Fallback burro nativo (abre sempre nova aba)
            print(f"⚠️ [Fallback] Extensão não conectada, abrindo aba nativa.")
            webbrowser.open(url)
        return True

    # ====================== FECHAR ABA ESPECÍFICA ======================
    if action == "close_specific_tab":
        target = str(payload.get("target") or "").strip()
        if not target:
            print("❌ [Chrome] close_specific_tab sem target")
            return False
        print(f"📤 [Chrome] Enviando fechamento específico → '{target}'")
        msg = {"action": "close_specific_tab", "target": target}
        if 'ws_loop' in globals() and ws_loop and connected_extensions:
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
            print(f"📤 [Chrome] ✅ Comando ENVIADO → close_specific_tab | target={target}")
            return True
        else:
            print("❌ [Chrome] ws_loop ou extensão não conectada")
            return False

    if action == "youtube_search" and payload.get("query"):
        atualizar_contexto(site="youtube", termo_busca=str(payload.get("query")), aba_id=None)
        
    if action == "netflix_search" and payload.get("query"):
        atualizar_contexto(site="netflix", termo_busca=str(payload.get("query")), aba_id=None)
        query = str(payload.get("query") or "").strip()
        trazer_chrome_para_frente()
        enviar_comando_chrome("open_url", {"url": "https://www.netflix.com/."})
        
        def _later_nav():
            try:
                time.sleep(3)
                trazer_chrome_para_frente()
                enviar_comando_chrome("start_netflix_navigation", {"movie": query})
            except Exception:
                pass
        threading.Thread(target=_later_nav, daemon=True).start()
        
    if action == "reload_url":
        url = str(payload.get("url") or "").strip()
        if not is_valid_url(url):
            print(f"❌ [Chrome] reload_url inválida: {url}")
            return False
        payload = {"url": url}
        atualizar_contexto_por_url(url)

    if 'ws_loop' in globals() and ws_loop:
        if action == "youtube_search":
            query = str(payload.get("query") or "").strip()
            if not query:
                print("❌ [Chrome] youtube_search sem query.")
                return False
            url_escolhida = _buscar_primeiro_video_youtube(query)
            if url_escolhida:
                payload = {"url": url_escolhida}
                action = "open_url"
                print(f"🎯 [Chrome] youtube_search virou open_url com melhor match: {url_escolhida}")
            else:
                msg = {"action": "youtube_search", "query": query}
        else:
            if action == "open_url":
                try:
                    purl = str(payload.get("url") or "").strip()
                    dom = urlparse(purl).netloc or ""
                    tab_id = solicitar_tab_reciclagem(dom, timeout_s=3.0)
                    if tab_id is not None:
                        msg = {"action": "update_tab", "tabId": tab_id, "url": purl}
                        if payload.get("auto_click") is True:
                            msg["auto_click"] = True
                        asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
                        return True
                    try:
                        webbrowser.open(purl)
                    except Exception:
                        pass
                    return True
                except Exception:
                    pass
            msg = {"action": action, **payload}
        if action == "youtube_search":
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
        else:
            msg = {"action": action, **payload}
            asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)
    else:
        print("[WebSocket] Loop não inicializado; comando não foi enviado.")
        
    return True

def enviar_comando_chrome(action: str | None = None, payload: dict | None = None):
    """Função wrapper simples (mantém compatibilidade com o resto do código)"""
    return validar_e_enviar_comando(action, payload)

def _remover_prefixo_exec(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    return re.sub(r'^\s*\[EXEC:[^\]]+\]\s*', '', texto.strip(), flags=re.IGNORECASE).strip()

def _pid_from_hwnd(hwnd) -> int:
    try:
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(wintypes.HWND(int(hwnd)), ctypes.byref(pid))
        return int(pid.value or 0)
    except Exception:
        return 0

def _classificar_assunto(exe: str, title: str) -> str:
    e = (exe or "").lower()
    t = (title or "").lower()
    if "code.exe" in e or "visual studio code" in t:
        return "Programação"
    if "minecraft" in e or "minecraft" in t:
        return "Gaming"
    if "ultimaker-cura" in e or "cura" in e or "cura" in t or "prusa" in e or "slicer" in t:
        return "Impressão 3D"
    if "spotify" in e or "spotify" in t:
        return "Música"
    return ""

def _sugerir_assunto(assunto: str):
    global _ultimo_proativo_ts
    if is_speaking:
        return
    if _continuidades_get("comando_sugerido_estado", "NONE") != "NONE":
        return
    now = time.time()
    if now - float(_ultimo_proativo_ts or 0.0) < 1200:
        return
    _ultimo_proativo_ts = now
    if assunto == "Programação":
        falar_com_lipsync("Vejo que o código tá rendendo, Pedro. Quer uma música de foco?", "calma", 1)
    elif assunto == "Gaming":
        falar_com_lipsync("Tá no modo gamer, né, Pedro. Quer que eu deixe uma música de fundo?", "calma", 1)
    elif assunto == "Impressão 3D":
        falar_com_lipsync("Isso aí tá com cara de impressão 3D. Quer que eu te ajude a achar um modelo bom?", "calma", 1)

def monitorar_janela_ativa():
    global contexto_sistema, _assunto_change_ts, _ultimo_proativo_ts
    global sugestao_bloqueada_ate
    global conversa_ativa
    last_hwnd = None
    last_assunto = ""
    last_trigger_key = ""
    trigger_start_ts = 0.0
    while True:
        try:
            win = None
            try:
                win = gw.getActiveWindow()
            except Exception:
                win = None
            title = ""
            hwnd = None
            if win:
                try:
                    title = str(getattr(win, "title", "") or "").strip()
                except Exception:
                    title = ""
                try:
                    hwnd = getattr(win, "_hWnd", None) or getattr(win, "hWnd", None) or getattr(win, "handle", None)
                except Exception:
                    hwnd = None
            exe = ""
            if hwnd:
                pid = _pid_from_hwnd(hwnd)
                if pid:
                    try:
                        exe = (psutil.Process(pid).name() or "").strip()
                    except Exception:
                        exe = ""
            assunto = _classificar_assunto(exe, title)
            contexto_sistema["exe"] = exe
            contexto_sistema["title"] = title
            contexto_sistema["assunto"] = assunto
            _percepcao_set("contexto_sistema", dict(contexto_sistema))

            if hwnd and hwnd != last_hwnd:
                last_hwnd = hwnd
                _assunto_change_ts = time.time()
                last_assunto = assunto
                last_trigger_key = ""
                trigger_start_ts = 0.0
            else:
                if assunto and assunto == last_assunto and _assunto_change_ts and (time.time() - _assunto_change_ts) >= 180:
                    _sugerir_assunto(assunto)

            now = time.time()
            if _continuidades_get("comando_sugerido_estado", "NONE") != "NONE" or is_speaking or conversa_ativa:
                time.sleep(2)
                continue
                
            if now - float(_ultimo_proativo_ts or 0.0) < 1200:
                time.sleep(2)
                continue

            try:
                if win:
                    sw, sh = pyautogui.size()
                    ww = int(getattr(win, "width", 0) or 0)
                    wh = int(getattr(win, "height", 0) or 0)
                    fullscreen = (sw > 0 and sh > 0 and ww >= int(sw * 0.95) and wh >= int(sh * 0.95))
                else:
                    fullscreen = False
            except Exception:
                fullscreen = False

            exe_l = (exe or "").lower()
            title_l = (title or "").lower()
            jogo_pesado = fullscreen and assunto == "Gaming"
            if jogo_pesado:
                time.sleep(2)
                continue

            trigger_key = ""
            trigger_payload = None
            if "code.exe" in exe_l or "visual studio code" in title_l:
                trigger_key = "SYS_MODE_CODE"
                trigger_payload = {"action": "combo_python", "clean_tabs": True, "music_query": "lofi focus", "clean_empty_tabs": True}
            elif "steam.exe" in exe_l or (assunto == "Gaming" and not fullscreen):
                trigger_key = "SYS_MODE_GAMER"
                trigger_payload = {"action": "combo_gamer", "pause_music": True, "close_study_tabs": True}
            elif "explorer.exe" in exe_l:
                if "downloads" in title_l or "transfer" in title_l:
                    trigger_key = "SYS_ORGANIZE_DOWNLOADS"
                    trigger_payload = {"action": "combo_organize", "open_downloads": True}

            if not trigger_key:
                time.sleep(2)
                continue

            if now < float(sugestao_bloqueada_ate.get(trigger_key, 0.0) or 0.0):
                time.sleep(2)
                continue

            if trigger_key != last_trigger_key:
                last_trigger_key = trigger_key
                trigger_start_ts = now
                time.sleep(2)
                continue

            if trigger_start_ts and (now - trigger_start_ts) >= 12:
                _continuidades_update(
                    comando_sugerido=trigger_key,
                    comando_sugerido_payload=trigger_payload,
                    comando_sugerido_estado="PENDING_CONFIRM",
                    comando_sugerido_ts=now,
                    comando_pendente=trigger_key,
                    comando_pendente_payload=trigger_payload,
                )
                _ultimo_proativo_ts = now
                if trigger_key == "SYS_MODE_CODE":
                    falar_com_lipsync("Pedro, ativo Modo Code? Limpo abas vazias e coloco música de foco.", "calma", 1)
                elif trigger_key == "SYS_MODE_GAMER":
                    falar_com_lipsync("Pedro, Modo Gamer? Pauso a música e fecho abas de estudo.", "calma", 1)
                elif trigger_key == "SYS_ORGANIZE_DOWNLOADS":
                    falar_com_lipsync("Pedro, quer que eu organize teus downloads?", "calma", 1)
                last_trigger_key = ""
                trigger_start_ts = 0.0
        except Exception:
            pass
        time.sleep(2)


def obter_janelas_abertas():
    """Retorna lista limpa de janelas úteis abertas no Windows"""
    try:
        titulos = gw.getAllTitles()
        lixo = ["", "Program Manager", "Settings", "Configurações", "Microsoft Text Input Application", 
                "Taskbar", "Cortana", "Search", "Widget", "LockApp.exe"]
        uteis = [t.strip() for t in titulos if t.strip() and t not in lixo]
        return ", ".join(uteis) if uteis else "Nenhuma janela útil aberta"
    except:
        return "Não consegui ler as janelas abertas"

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

_COMANDO_RAPIDO_RE = re.compile(r"\b(toca|coloca|abre|abra)\b", flags=re.IGNORECASE)

extrair_comando_rapido = partial(_extrair_comando_rapido_mente, sites_directos=SITES_DIRECTOS)


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
    global _fala_worker_started
    with _fala_worker_lock:
        if _fala_worker_started:
            return
        threading.Thread(target=_worker_de_falas, daemon=True, name="Laylay-SpeechQueue").start()
        _fala_worker_started = True


def _combinar_falas_batch(itens: list) -> tuple[str, str, int]:
    falas = []
    emo = "calma"
    nivel = 1
    for idx, item in enumerate(itens):
        if not isinstance(item, dict):
            continue
        texto = limpar_para_voz(str(item.get("texto") or "")).strip()
        if not texto:
            continue
        texto = re.sub(r"\s+", " ", texto).strip()
        if not texto:
            continue
        if idx == 0:
            emo = str(item.get("emocao") or "calma")
            try:
                nivel = int(item.get("nivel") or 1)
            except Exception:
                nivel = 1
        if texto[-1] not in ".!?…":
            texto += "."
        falas.append(texto)

    if not falas:
        return FALLBACK_FALA_NEUTRA, emo, nivel

    texto_final = " ".join(falas)
    texto_final = re.sub(r"\s+", " ", texto_final).strip()
    return texto_final, emo, nivel


def _reproduzir_fala(texto: str, emocao: str, nivel: int):
    global is_speaking
    temp_file = None
    try:
        texto_voz = limpar_para_voz(texto)
        if not texto_voz:
            texto_voz = FALLBACK_FALA_NEUTRA

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_file = f.name

        communicate = edge_tts.Communicate(texto_voz, voice=VOICE)
        asyncio.run(communicate.save(temp_file))

        from typing import Any, cast
        data, samplerate = cast(Any, sf.read(temp_file))
        print("")
        print(_formatar_mensagem_laylay(texto_voz, emocao=emocao, nivel=nivel))

        ducking_volume(ativar=True)
        try:
            sd.play(data, samplerate)
            while sd.get_stream().active:
                if interrupt_event.is_set():
                    sd.stop()
                    print("🛑 [BARGE-IN] Fala interrompida pelo Pedro!")
                    break
                time.sleep(0.03)
        finally:
            ducking_volume(ativar=False)

    except Exception as e:
        print(f"❌ [FALA] Erro no áudio: {type(e).__name__} → {e}")
        try:
            _fallback_pyttsx(texto, emocao)
        except:
            pass
    finally:
        is_speaking = False
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass

def _worker_de_falas():
    while True:
        item = _fala_fila.get()
        if item is None:
            continue

        lote = [item]
        prazo = time.time() + _fala_batch_window
        while len(lote) < _fala_batch_max_items:
            restante = prazo - time.time()
            if restante <= 0:
                break
            try:
                prox = _fala_fila.get(timeout=restante)
            except Empty:
                break
            if prox is None:
                continue
            lote.append(prox)
            prazo = time.time() + _fala_batch_window

        texto_final, emocao, nivel = _combinar_falas_batch(lote)
        global current_emotion, emotion_level, is_speaking
        current_emotion = emocao
        emotion_level = nivel
        is_speaking = True
        try:
            _reproduzir_fala(texto_final, emocao, nivel)
        finally:
            for pedido in lote:
                if isinstance(pedido, dict):
                    ev = pedido.get("done_event")
                    if ev is not None:
                        try:
                            ev.set()
                        except Exception:
                            pass


def _normalizar_segmento_fala(texto: str) -> str:
    t = limpar_para_voz(str(texto or "")).strip()
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return ""
    if t[-1] not in ".!?…":
        t += "."
    return t


def _ajustar_tom_por_emocao(texto: str, emocao: str, texto_usuario: str = "") -> str:
    return _ajustar_tom_por_emocao_mente(texto, emocao, texto_usuario, normalizar_cb=_normalizar_texto_com_apelidos)


def _compor_fala_proativa(itens: list) -> tuple[str, str, int]:
    if not itens:
        return FALLBACK_FALA_NEUTRA, "calma", 1

    ctx = _obter_contexto_perceptivo()
    ordem = {"briefing": 0, "emails": 1, "rotina": 2, "musica": 3}
    itens_validos = sorted(
        [i for i in itens if isinstance(i, dict) and str(i.get("texto") or "").strip()],
        key=lambda i: (
            ordem.get(str(i.get("tipo") or "").lower(), 9),
            float(i.get("ts") or 0.0),
        ),
    )

    agrupados = {}
    for item in itens_validos:
        tipo_item = str(item.get("tipo") or "").lower().strip() or "geral"
        agrupados.setdefault(tipo_item, []).append(item)

    itens = []
    for tipo_item, grupo in sorted(agrupados.items(), key=lambda kv: ordem.get(kv[0], 9)):
        if tipo_item == "emails" and len(grupo) > 1:
            textos_email = []
            for item in grupo[:4]:
                texto_email = _normalizar_segmento_fala(item.get("texto") or "")
                texto_email = re.sub(r"^(Teus emails estão querendo atenção:\s*)", "", texto_email, flags=re.IGNORECASE).strip()
                if texto_email:
                    textos_email.append(texto_email)
            total = len(grupo)
            resumo = f"Tem {total} avisos de email no radar."
            if textos_email:
                resumo += " " + " ".join(textos_email)
            if total > len(textos_email):
                resumo += f" E ainda tem mais {total - len(textos_email)} sem eu tagarelar tudo agora."
            base = dict(grupo[0])
            base["texto"] = resumo
            base["ts"] = max(float(g.get("ts") or 0.0) for g in grupo)
            itens.append(base)
            continue

        if len(grupo) > 1:
            # Para rotina/música/briefing, evita eco repetido e fica com o sinal mais recente.
            itens.append(max(grupo, key=lambda g: float(g.get("ts") or 0.0)))
        else:
            itens.append(grupo[0])

    partes = []
    emocao = "calma"
    nivel = 1
    tipos = [str(i.get("tipo") or "").lower().strip() for i in itens]
    tem_briefing = "briefing" in tipos
    tem_emails = "emails" in tipos
    tem_rotina = "rotina" in tipos
    tem_musica = "musica" in tipos

    def _turbinhar(texto: str) -> str:
        texto = re.sub(r"\s+", " ", str(texto or "")).strip()
        if not texto:
            return ""
        if texto[-1] not in ".!?…":
            texto += "."
        return texto

    for idx, item in enumerate(itens):
        tipo = str(item.get("tipo") or "").lower().strip()
        texto = _normalizar_segmento_fala(item.get("texto") or "")
        if not texto:
            continue

        if idx == 0:
            emocao = str(item.get("emocao") or emocao)
            try:
                nivel = int(item.get("nivel") or nivel)
            except Exception:
                nivel = 1

        if tipo == "briefing":
            texto = _turbinhar(texto)
            texto = re.sub(r"^(Hoje|Agora|E aí|Bom dia)[, ]+", "", texto, flags=re.IGNORECASE)
            texto = texto[:1].upper() + texto[1:] if texto else texto
            texto = f"Olha só: {texto}"
        elif tipo == "emails":
            texto = _turbinhar(texto)
            texto = texto[:1].lower() + texto[1:] if texto else texto
            texto = f"Teus emails estão querendo atenção: {texto}"
        elif tipo == "rotina":
            texto = _turbinhar(texto)
            texto = f"Seu horário tá puxando isso aqui: {texto}"
        elif tipo == "musica":
            texto = _turbinhar(texto)
            texto = f"Tem um padrão musical querendo aparecer no contexto: {texto}"
        else:
            texto = _turbinhar(texto)

        texto_lower = _normalizar_texto_com_apelidos(texto)
        if ctx["periodo"] in {"madrugada", "noite"} and tipo in {"emails", "rotina", "musica"}:
            texto = texto.replace("querendo atenção", "pedindo um ritmo mais leve")
            if tipo == "musica" and "trilha sonora" not in texto_lower:
                texto += " Talvez hoje o melhor seja algo mais calmo."
        if ctx["topico_ativo"] and tipo in {"briefing", "rotina"} and len(texto) < 180:
            texto += f" Isso conversa com o que a gente vinha vendo sobre {ctx['topico_ativo']}."
        if ctx["humor"] <= -4 and tipo in {"emails", "rotina"}:
            texto = texto.replace("querendo atenção", "sem pressa para te encher")
        if ctx["emocao"] in {"triste", "decepcionada", "cansada"} and tipo == "briefing":
            texto += " Vou falar sem exagero pra não pesar mais o clima."

        texto = _ajustar_tom_por_emocao(texto, emocao, ctx.get("topico_ativo", ""))
        partes.append(texto)

    if not partes:
        return FALLBACK_FALA_NEUTRA, emocao, nivel

    if len(partes) == 1:
        texto_final = partes[0]
    elif len(partes) == 2:
        texto_final = f"{partes[0]} E {partes[1][0].lower() + partes[1][1:]}"
    else:
        texto_final = f"{partes[0]} Além disso, {partes[1][0].lower() + partes[1][1:]}"
        for parte in partes[2:]:
            texto_final += f" E {parte[0].lower() + parte[1:]}"

    if len(partes) > 1:
        texto_final = "Hmmm, " + texto_final[0].lower() + texto_final[1:]

    if tem_briefing and tem_musica:
        texto_final = texto_final.replace("E o padrão musical", "e o padrão musical", 1)
    if tem_emails and tem_musica and "padrão musical" not in texto_final.lower():
        texto_final += " E esse hábito musical também entra na conta."

    if ctx["periodo"] in {"madrugada", "noite"} and not tem_briefing:
        texto_final = texto_final.replace("Olha só:", "Olha só, baixando um pouco o ritmo:")
    if ctx["topico_ativo"] and ctx["topico_ativo"].lower() in texto_final.lower():
        texto_final = texto_final.replace("Seu horário tá puxando isso aqui:", "Seu cérebro tá puxando isso aqui junto com o contexto:")

    texto_final = re.sub(r"\s+", " ", texto_final).strip()

    return texto_final, emocao, nivel


def _flush_fala_proativa():
    global _fala_proativa_buffer, _fala_proativa_timer
    with _fala_proativa_lock:
        itens = list(_fala_proativa_buffer)
        _fala_proativa_buffer = []
        _fala_proativa_timer = None

    if not itens:
        return

    texto, emocao, nivel = _compor_fala_proativa(itens)
    falar_com_lipsync(texto, emocao, nivel)


def _agendar_fala_proativa(tipo: str, texto: str, emocao: str = "calma", nivel: int = 1):
    global _fala_proativa_timer
    tipo_norm = str(tipo or "").strip().lower()
    item = {
        "tipo": tipo_norm,
        "texto": str(texto or "").strip(),
        "emocao": emocao,
        "nivel": nivel,
        "ts": time.time(),
    }
    with _fala_proativa_lock:
        _fala_proativa_buffer.append(item)
        if _fala_proativa_timer and _fala_proativa_timer.is_alive():
            return
        atraso = _fala_proativa_delay
        idade_sistema = time.time() - _fala_proativa_inicio_sistema
        if tipo_norm in {"briefing", "emails", "rotina", "musica"} and idade_sistema < _fala_proativa_janela_startup:
            atraso = max(_fala_proativa_delay, _fala_proativa_janela_startup - idade_sistema)
            print(f"🧠 [FALA PROATIVA] aguardando {atraso:.1f}s para unificar falas iniciais")
        _fala_proativa_timer = threading.Timer(atraso, _flush_fala_proativa)
        _fala_proativa_timer.daemon = True
        _fala_proativa_timer.start()

async def _gerar_audio_edge(texto: str, arquivo: str):
    """Gera o áudio com edge_tts (mantém sua voz atual)"""
    communicate = edge_tts.Communicate(texto, voice=VOICE)
    await communicate.save(arquivo)

_fala_dinamica_cache = {}
_fala_dinamica_falhou_ate = 0.0


def _extrair_json_fala_dinamica(raw: str) -> str:
    bruto = str(raw or "").strip()
    if not bruto:
        return ""
    try:
        data = json.loads(bruto)
        return str(data.get("fala") or "").strip() if isinstance(data, dict) else ""
    except Exception:
        pass
    m = re.search(r"\{.*\}", bruto, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            return str(data.get("fala") or "").strip() if isinstance(data, dict) else ""
        except Exception:
            return ""
    return ""


def _fala_dinamica_deve_tentar(texto: str) -> bool:
    t = str(texto or "").strip()
    if not t or len(t) < 8 or len(t) > 220:
        return False
    baixo = t.lower()
    if "http://" in baixo or "https://" in baixo or "```" in baixo or "{" in t or "}" in t:
        return False
    if baixo.startswith(("erro na api", "traceback", "warning", "⚠️", "❌")):
        return False
    if any(x in baixo for x in [
        "cérebro desconectou", "cerebro desconectou",
        "circuitos de comunicacao", "circuitos de comunicação",
        "recomendação musical", "recomendacao musical",
    ]):
        return False
    gatilhos_template = [
        "abrindo", "fechando", "pronto", "colocando", "não vou", "nao vou",
        "quer ouvir", "quer que", "deixei", "fechado", "beleza", "tentei",
        "não consegui", "nao consegui", "achei", "minha aposta", "eu iria",
        "tô", "to",
    ]
    if any(x in baixo for x in ["chat ligado", "conversa aberta", "modo chat", "modo de urgência", "modo de urgencia"]):
        return False
    if any(g in baixo for g in gatilhos_template):
        return True
    # Falas muito curtas de comando costumam soar repetidas; deixa a IA temperar.
    return len(t.split()) <= 16 and not baixo.endswith("?")


def _fala_dinamica_preserva_sentido(original: str, nova: str) -> bool:
    o = _normalizar_texto_com_apelidos(original)
    n = _normalizar_texto_com_apelidos(nova)
    if not n or len(nova) > 240:
        return False
    if any(x in n for x in ["json", "comandos", "open_url", "youtube_search"]):
        return False
    negativos = ["nao consegui", "não consegui", "tentei", "falhou", "nao achei", "não achei"]
    positivos = ["consegui", "feito", "pronto", "abri", "fechei", "salvei", "toquei"]
    if any(x in o for x in negativos) and any(x in n for x in positivos) and not any(x in n for x in negativos):
        return False
    if "?" in original and "?" not in nova:
        return False
    if any(x in o for x in ["quer ouvir", "posso", "quer que"]) and not any(x in n for x in ["quer", "posso", "quer que"]):
        return False
    return True


def _temperar_fala_com_ia(texto: str, emocao: str = "calma", nivel: int = 1) -> str:
    global _fala_dinamica_falhou_ate
    base = str(texto or "").strip()
    if not _fala_dinamica_deve_tentar(base):
        return base
    if time.time() < _fala_dinamica_falhou_ate:
        return base
    cache_key = (base, str(emocao or ""), int(nivel or 1))
    if cache_key in _fala_dinamica_cache:
        return _fala_dinamica_cache[cache_key]

    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}
    contexto_curto = (
        f"emocao={emocao or 'calma'}({nivel or 1}); "
        f"ultima_habilidade={estado.get('ultima_habilidade') or ''}; "
        f"ultima_intencao={estado.get('ultima_intencao') or estado.get('ultima_acao_intent') or ''}; "
        f"ultimo_alvo={estado.get('ultimo_alvo') or ''}"
    )
    prompt = (
        "Você é a Laylay. Reescreva a fala base com mais naturalidade, liberdade e personalidade.\n"
        "Preserve exatamente o sentido prático: não invente ação, não mude sucesso para falha nem falha para sucesso.\n"
        "Se a fala base pergunta algo, mantenha como pergunta. Se confirma uma ação, confirme sem exagerar.\n"
        "Pode ser amiga, divertida, debochada leve, carinhosa ou estranhar o pedido, conforme o contexto.\n"
        "Evite formato repetido tipo sempre começar com Pronto/Beleza/Fechado.\n"
        "Nao alongue. Uma frase curta basta. Sem discurso, sem conselho extra.\n"
        "Responda APENAS JSON válido: {\"fala\":\"...\"}\n\n"
        f"Contexto: {contexto_curto}\n"
        f"Fala base: {base!r}\n"
    )
    try:
        raw = enviar_mensagem(
            [{"role": "system", "content": prompt}],
            _com_tools=False,
            max_tokens=90,
            modo_rapido=True,
        )
        if "Erro na API" in str(raw) or "circuitos de comunicacao" in str(raw) or "circuitos de comunicação" in str(raw):
            _fala_dinamica_falhou_ate = time.time() + 60.0
            return base
        nova = limpar_para_voz(_extrair_json_fala_dinamica(raw))
        if _fala_dinamica_preserva_sentido(base, nova):
            _fala_dinamica_cache[cache_key] = nova
            if len(_fala_dinamica_cache) > 80:
                _fala_dinamica_cache.clear()
            print(f"🗣️ [FALA DINAMICA] {base[:55]!r} -> {nova[:75]!r}")
            return nova
    except Exception as e:
        print(f"⚠️ [FALA DINAMICA] falha ao variar fala: {e}")
        _fala_dinamica_falhou_ate = time.time() + 30.0
    return base


def falar_com_lipsync(texto: str, emocao: str = "calma", nivel: Optional[int] = None, wait: bool = False):
    _iniciar_worker_de_falas()
    nivel_final = nivel if nivel is not None else 1
    texto_final = _temperar_fala_com_ia(texto, emocao, nivel_final)
    done_event = threading.Event()
    pedido = {
        "texto": texto_final,
        "emocao": emocao,
        "nivel": nivel_final,
        "done_event": done_event,
    }
    _fala_fila.put(pedido)
    if wait:
        done_event.wait()

def _fallback_pyttsx(texto, emocao_atual):
    try:
        texto_voz = limpar_para_voz(texto)
        if not texto_voz:
            texto_voz = FALLBACK_FALA_NEUTRA
        engine = pyttsx3.init()
        engine.setProperty("rate", 150 if "calma" in emocao_atual.lower() else 170)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        caminho = temp.name
        temp.close()
        engine.save_to_file(texto_voz, caminho)
        engine.runAndWait()
        data, sr_val = sf.read(caminho) # type: ignore
        
        # 🎧 AUDIO DUCKING também no fallback
        ducking_volume(ativar=True)
        try:
            sd.play(data, sr_val)
            sd.wait()
        finally:
            ducking_volume(ativar=False)
        
        os.unlink(caminho)
    except Exception as e:
        print(f"❌ Erro no fallback TTS: {e}")
        print(texto)

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
    """Carrega a data do último briefing executado."""
    if os.path.exists(BRIEFING_ARQUIVO):
        try:
            with open(BRIEFING_ARQUIVO, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("data_ultimo", "")
        except:
            pass
    return ""

def salvar_estado_briefing():
    """Salva que o briefing de hoje já foi feito (idempotente)."""
    try:
        data = {"data_ultimo": datetime.now().strftime("%Y-%m-%d")}
        with open(BRIEFING_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"💾 [BRIEFING] Estado salvo para {data['data_ultimo']}")
    except Exception as e:
        print(f"⚠️ [BRIEFING] Erro ao salvar estado: {e}")

def obter_clima_wttr():
    """Clima via wttr.in (gratuito, sem chave). Inclui aviso de chuva se umidade > 80%."""
    try:
        url = f"https://wttr.in/{BRIEFING_CIDADE}?format=%C+%t+umidade:%h+vento:%w&lang=pt"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            clima_raw = res.text.strip()
            # Detecção automática de chance de chuva
            umidade_match = re.search(r'umidade:(\d+)%', clima_raw)
            if umidade_match and int(umidade_match.group(1)) > 80:
                clima_raw += " — alta umidade, chance de chuva nas próximas horas!"
            return clima_raw
        return "Clima não disponível no momento."
    except Exception as e:
        print(f"⚠️ [BRIEFING] wttr.in falhou: {e}")
        return "Não consegui pegar o clima agora."


def obter_clima_localidade(localidade: str = "") -> dict:
    """Busca clima atual de uma localidade no wttr.in e devolve estrutura amigável."""
    cidade = str(localidade or BRIEFING_CIDADE or "").strip() or "Boituva"
    try:
        cidade_url = urllib.parse.quote(cidade)
        url = f"https://wttr.in/{cidade_url}?format=j1&lang=pt"
        res = requests.get(url, timeout=6)
        if res.status_code != 200:
            return {"ok": False, "localidade": cidade, "erro": "status"}
        data = res.json() if res.content else {}
        atual = ((data or {}).get("current_condition") or [{}])[0] or {}
        descricao = ""
        try:
            descricao = str((((atual.get("lang_pt") or atual.get("weatherDesc")) or [{}])[0] or {}).get("value") or "").strip()
        except Exception:
            descricao = ""
        if not descricao:
            try:
                descricao = str(((atual.get("weatherDesc") or [{}])[0] or {}).get("value") or "").strip()
            except Exception:
                descricao = ""
        return {
            "ok": True,
            "localidade": cidade,
            "temperatura_c": str(atual.get("temp_C") or "").strip(),
            "sensacao_c": str(atual.get("FeelsLikeC") or "").strip(),
            "umidade": str(atual.get("humidity") or "").strip(),
            "vento_kmph": str(atual.get("windspeedKmph") or "").strip(),
            "descricao": descricao,
        }
    except Exception as e:
        print(f"⚠️ [CLIMA] falha ao consultar clima de {cidade}: {e}")
        return {"ok": False, "localidade": cidade, "erro": str(e)}

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
    prompt_briefing = (
        f"System: É de manhã e você acabou de acordar o sistema do Pedro. "
        f"Faça o seu briefing matinal para ele do seu jeito debochado, inteligente, observador e um pouco sedutor na confiança. "
        f"Informe que em {BRIEFING_CIDADE} o clima hoje é: {clima}. "
        f"Pergunte o que ele vai fazer ou 'destruir' no PC hoje. "
        f"Se soar natural, conecte clima, humor e convite em uma única fala charmosa. "
        f"Use APENAS o JSON obrigatório com a chave 'fala' (sem comandos)."
    )
    try:
        mensagens = [
            {"role": "system", "content": prompt_briefing},
            {"role": "user", "content": "Gere o briefing agora."},
        ]
        bot_raw = enviar_mensagem(mensagens, _com_tools=False)
        bot = _remover_prefixo_exec(limpar_resposta(bot_raw)).strip()
        if not bot:
            bot = f"Hoje em {BRIEFING_CIDADE} o clima está {clima}. E aí, qual vai ser a bagunça de hoje, Pedro?"
        _agendar_fala_proativa("briefing", bot, "calma", 1)
    except Exception as e:
        print(f"⚠️ [BRIEFING] Falha ao montar fala: {e}")
        _agendar_fala_proativa("briefing", f"Hoje em {BRIEFING_CIDADE} o clima está {clima}. E aí, qual vai ser a bagunça de hoje, Pedro?", "calma", 1)
    salvar_estado_briefing()
    _briefing_executado = True
    print("✅ [BRIEFING MATINAL] Executado com sucesso!")

def repetir_briefing():
    """Repete o briefing quando o usuário pedir, delegando à IA."""
    clima = obter_clima_wttr()
    prompt_repetir = (
        f"System: O Pedro acabou de pedir para você repetir o briefing do clima. "
        f"Fale do seu jeito debochado (talvez zoando a memória dele). "
        f"A informação é: em {BRIEFING_CIDADE} o clima está {clima}. "
        f"Use APENAS o JSON obrigatório com a chave 'fala' (sem comandos)."
    )
    _gerar_resposta_exec_ia_sync(prompt_repetir)

def _detectar_repetir_briefing(texto: str) -> bool:
    """Detecta comandos como 'repete o briefing', 'repetir briefing', etc."""
    t = texto.lower().strip()
    triggers = ["repete o briefing", "repetir briefing", "briefing de novo",
                "fala o briefing de novo", "repete o clima"]
    return any(trig in t for trig in triggers)

def _injetar_comando_briefing_na_ia():
    """Helper futuro (caso queira injetar no histórico da IA)."""
    pass  # por enquanto não precisa

def obter_temperatura_cpu():
    """Temperatura com 2 métodos (Open Hardware Monitor → fallback ACPI)."""
    # Método 1: Open Hardware Monitor (mais preciso)
    try:
        import wmi
        c = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        sensors = c.Sensor()
        for sensor in sensors:
            if sensor.SensorType == 'Temperature' and ('CPU' in sensor.Name or 'Package' in sensor.Name):
                return round(float(sensor.Value), 1)
    except:
        pass

    # Método 2: ACPI nativo do Windows
    try:
        import wmi
        c = wmi.WMI(namespace="root\\wmi")
        temps = c.MSAcpi_ThermalZoneTemperature()
        for t in temps:
            return round((t.CurrentTemperature / 10.0) - 273.15, 1)
    except:
        pass

    return None  # sem sensor detectado


def identificar_processo_culpado():
    """Retorna o processo que mais está consumindo CPU no momento."""
    try:
        import psutil
        processos = []
        for p in psutil.process_iter(['name', 'cpu_percent']):
            try:
                if p.info['cpu_percent'] is not None:
                    processos.append((p.info['name'], p.info['cpu_percent']))
            except:
                pass
        if processos:
            culpado = max(processos, key=lambda x: x[1])
            return culpado[0] if culpado[1] > 15 else "nenhum em destaque"
    except:
        pass
    return "nenhum processo detectado"


def _falar_status_saude():
    """Fala o status completo com veredito (usado no daemon e por comando de voz)."""
    import psutil, time
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    temp = obter_temperatura_cpu()

    veredito = "tá tranquilo" if cpu < 60 and ram < 70 else \
               "tá esquentando" if cpu < 80 and ram < 85 else "tá pesado pra caralho"

    msg = f"CPU {cpu:.0f}%, RAM {ram:.0f}%"
    if temp is not None:
        msg += f", temperatura {temp}°C"
    msg += f". {veredito}, Pedro."

    culpado = identificar_processo_culpado()
    if culpado != "nenhum em destaque" and culpado != "nenhum processo detectado":
        msg += f" O culpado é {culpado}."

    falar_com_lipsync(msg, "calma", 1)
    print(f"🩺 [SAÚDE] {msg}")


def _monitor_saude_daemon():
    """Daemon principal — roda em background."""
    global _saude_cpu_alta_desde, _saude_ultimo_aviso
    print("🩺 [SAÚDE] Monitor de saúde iniciado (CPU/RAM/Temp + anti-falso-positivo)")

    while True:
        try:
            import psutil, time
            agora = time.time()

            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent

            # CPU sustentada (30 segundos)
            if cpu >= SAUDE_CPU_THRESHOLD:
                if _saude_cpu_alta_desde == 0.0:
                    _saude_cpu_alta_desde = agora
                elif (agora - _saude_cpu_alta_desde) >= SAUDE_CPU_SUSTENTADO_SEGUNDOS:
                    if (agora - _saude_ultimo_aviso) > 300:  # 5 minutos entre avisos
                        _saude_ultimo_aviso = agora
                        _falar_status_saude()
            else:
                _saude_cpu_alta_desde = 0.0

            # RAM crítica (aviso imediato)
            if ram >= SAUDE_RAM_THRESHOLD and (agora - _saude_ultimo_aviso) > 180:
                _saude_ultimo_aviso = agora
                _falar_status_saude()

        except Exception as e:
            print(f"⚠️ [SAÚDE] Erro no daemon: {e}")

        time.sleep(5)  # checa a cada 5 segundos


def detectar_comando_saude(texto: str) -> bool:
    """Comandos de voz sob demanda."""
    t = (texto or "").lower().strip()
    triggers = [
        "como tá o pc", "como ta o pc", "como está o pc",
        "tá pesado", "ta pesado", "status do pc",
        "saúde do pc", "como anda o pc", "tá quente o pc"
    ]
    return any(trig in t for trig in triggers)

def _carregar_rotinas_aprendidas():
    global _rotina_dados_diarios
    _rotina_dados_diarios = _carregar_rotinas_aprendidas_mente(ROTINA_ARQUIVO_APRENDIDO)
    print(f"📚 [ROTINA] {len(_rotina_dados_diarios)} horários já aprendidos")


def _salvar_rotinas_aprendidas():
    _salvar_rotinas_aprendidas_mente(ROTINA_ARQUIVO_APRENDIDO, _rotina_dados_diarios)
    print("💾 [ROTINA] Padrões salvos")


def _logar_atividade_atual():
    global _rotina_ultimo_log
    _rotina_ultimo_log = _logar_atividade_atual_mente(
        ROTINA_ARQUIVO_APRENDIDO,
        _rotina_dados_diarios,
        _rotina_ultimo_log,
        contexto_sistema,
        lambda: gw.getActiveWindow(),
        salvar_cb=_salvar_rotinas_aprendidas,
    )


def _rotina_chave_feedback(hora: str, app: str) -> str:
    return _rotina_chave_feedback_mente(hora, app)


def _rotina_app_bloqueado(hora: str, app: str) -> bool:
    return _rotina_app_bloqueado_mente(_rotina_feedback_pesos, hora, app, ROTINA_BLOQUEIO_REJEICAO_VEZES)


def _rotina_registrar_feedback(aceito: bool):
    global _rotina_feedback_pesos, _rotina_ultima_sugestao
    pendente_atual = _continuidades_get("rotina_sugestao_pendente")
    _rotina_feedback_pesos, pendente_novo, _rotina_ultima_sugestao = _registrar_feedback_rotina_mente(
        pendente_atual,
        _rotina_feedback_pesos,
        aceito,
        falar_cb=falar_com_lipsync,
        abrir_programa_cb=abrir_programa,
        salvar_cb=lambda pesos: _salvar_feedback_pesos_mente(os.path.join(PASTA_MEMORIA, "rotinas_feedback.json"), pesos),
        cooldown_min=ROTINA_BLOQUEIO_REJEICAO_MIN,
        limite_rejeicao=ROTINA_BLOQUEIO_REJEICAO_VEZES,
    )
    _continuidades_set("rotina_sugestao_pendente", pendente_novo)


def _carregar_feedback_pesos():
    global _rotina_feedback_pesos
    _rotina_feedback_pesos = _carregar_feedback_pesos_rotina_mente(os.path.join(PASTA_MEMORIA, "rotinas_feedback.json"))
    print(f"[FEEDBACK ROTINA] {len(_rotina_feedback_pesos)} peso(s) carregado(s)")


def _carregar_musica_dados():
    global _musica_dados_diarios
    _musica_dados_diarios = _carregar_musica_dados_mente(MUSICA_ARQUIVO_HISTORICO)


def _salvar_musica_dados():
    _salvar_musica_dados_mente(MUSICA_ARQUIVO_HISTORICO, _musica_dados_diarios)


def _carregar_musica_feedback_pesos():
    global _musica_feedback_pesos
    _musica_feedback_pesos = _carregar_musica_feedback_pesos_mente(MUSICA_ARQUIVO_FEEDBACK)


def _salvar_musica_feedback_pesos():
    _salvar_musica_feedback_pesos_mente(MUSICA_ARQUIVO_FEEDBACK, _musica_feedback_pesos)


def _musica_chave_feedback(hora: str, musica: str) -> str:
    return _musica_chave_feedback_mente(hora, musica)


def _musica_bloqueada(hora: str, musica: str) -> bool:
    return _musica_bloqueada_mente(_musica_feedback_pesos, hora, musica, ROTINA_BLOQUEIO_REJEICAO_VEZES)


def _musica_registrar_historico(musica: str):
    _musica_registrar_historico_mente(_musica_dados_diarios, musica, salvar_cb=_salvar_musica_dados)


def _normalizar_confirmacao_texto(texto: str) -> str:
    return _normalizar_confirmacao_texto_mente(texto)


def _classificar_confirmacao_local(texto: str):
    return _classificar_confirmacao_local_mente(texto)


def _classificar_confirmacao_contextual(texto: str, sugestao: str):
    local = _classificar_confirmacao_local(texto)
    if local is not None:
        return local
    return _classificar_confirmacao_contextual_mente(texto, sugestao, interpretar_confirmacao_llm=interpretar_confirmacao_llm)


def _interpretar_resposta_pendente(texto: str, pendencia: dict) -> dict:
    contexto_recente = ""
    try:
        contexto_recente = _resumo_mente_integrada_para_prompt_mente(mente_integrada_estado)
    except Exception:
        contexto_recente = ""

    def _llm(prompt: str) -> str:
        return enviar_mensagem(
            [{"role": "system", "content": prompt}],
            _com_tools=False,
            max_tokens=120,
            modo_rapido=True,
        )

    return _interpretar_resposta_pendente_mente(
        texto_usuario=texto,
        pendencia=pendencia,
        contexto=contexto_recente,
        interpretar_llm=_llm,
    )


def _handle_feedback_pendente(texto: str) -> bool:
    contexto = {
        "_rotina_sugestao_pendente": _continuidades_get("rotina_sugestao_pendente"),
        "_playlist_sugestao_pendente": _continuidades_get("playlist_sugestao_pendente"),
        "_email_sugestao_pendente": _continuidades_get("email_sugestao_pendente"),
        "_classificar_confirmacao_contextual": _classificar_confirmacao_contextual,
        "_classificar_confirmacao_local": _classificar_confirmacao_local,
        "_handle_sugestao_confirmacao": _handle_sugestao_confirmacao,
        "solicitar_aba_ativa": solicitar_aba_ativa,
        "add_to_playlist_url": add_to_playlist_url,
        "extrair_nome_playlist": extrair_nome_playlist,
        "_yt_clean_title": _yt_clean_title,
        "falar_com_lipsync": falar_com_lipsync,
        "_set_ultima_playlist": lambda valor: _musica_estado_set("ultima_playlist", valor),
        "_rotina_registrar_feedback": _rotina_registrar_feedback,
        "_interpretar_resposta_pendente": _interpretar_resposta_pendente,
        "_gmail_buscar_nao_lidos": _gmail_buscar_nao_lidos,
        "_gmail_falar_resumo_estiloso": _gmail_falar_resumo_estiloso,
    }
    resultado = _handle_feedback_pendente_mente(contexto, texto)
    _continuidades_update(
        rotina_sugestao_pendente=contexto.get("_rotina_sugestao_pendente"),
        playlist_sugestao_pendente=contexto.get("_playlist_sugestao_pendente"),
        email_sugestao_pendente=contexto.get("_email_sugestao_pendente"),
    )
    return resultado


def _separar_feedback_e_continuacao(texto: str):
    bruto = str(texto or "").strip()
    if not bruto:
        return None
    t = _normalizar_texto_com_apelidos(bruto)
    if not t:
        return None

    separadores = [
        " mas ",
        " mas, ",
        " e depois ",
        " depois ",
        " e ai ",
        " e aí ",
        " e ",
    ]
    for sep in separadores:
        if sep not in t:
            continue
        esquerda, direita = t.split(sep, 1)
        esquerda = esquerda.strip(" ,.!?;:")
        direita = direita.strip(" ,.!?;:")
        if not esquerda or not direita:
            continue
        if len(esquerda.split()) > 8:
            continue
        confirmado = _classificar_confirmacao_local(esquerda)
        if confirmado is None:
            continue
        return esquerda, direita, confirmado
    return None


def _handle_feedback_pendente_misto(texto: str) -> bool:
    """Trata frases como 'agora nao, mas coloca playlist anime' sem engolir o comando."""
    partes = _separar_feedback_e_continuacao(texto)
    if not partes:
        return False

    prefixo, resto, confirmado = partes
    if not _handle_feedback_pendente(prefixo):
        return False

    if resto:
        try:
            if processar_comandos_imediatos(resto):
                return True
        except Exception as e:
            print(f"⚠️ [FEEDBACK MISTO] falha ao executar continuacao: {e}")

    # Se a continuacao era conversa, deixa a frase completa seguir depois de limpar a pendencia.
    return bool(confirmado)


def _analisar_e_sugerir_musica():
    return


def _analisar_e_sugerir_rotina():
    global _rotina_ultima_sugestao
    pendente_atual = _continuidades_get("rotina_sugestao_pendente")
    _rotina_ultima_sugestao, pendente_novo = _analisar_e_sugerir_rotina_mente(
        _rotina_dados_diarios,
        _rotina_feedback_pesos,
        _rotina_ultima_sugestao,
        pendente_atual,
        _contexto_aponta_descanso,
        _agendar_fala_proativa,
        ROTINA_DIAS_PARA_APRENDER,
        ROTINA_BLOQUEIO_REJEICAO_VEZES,
    )
    _continuidades_set("rotina_sugestao_pendente", pendente_novo)


def monitor_rotina_daemon():
    """Daemon que registra atividades e sugere rotinas."""
    print("[ROTINA] Aprendizado de rotina iniciado - vai aprender em 7 dias")

    _carregar_rotinas_aprendidas()
    _carregar_feedback_pesos()
    _carregar_musica_dados()
    _carregar_musica_feedback_pesos()

    while True:
        try:
            _logar_atividade_atual()
            _analisar_e_sugerir_rotina()
            _analisar_e_sugerir_musica()
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


def executar_comando_interface(comando_linha):
    import re
    m = re.match(r"([A-Z_]+)(?:\((.*)\))?", comando_linha.strip())
    if m:
        cmd = m.group(1)
        arg = m.group(2)
        if arg:
            arg = arg.strip("\"'")
        _executar_exec(cmd, arg)
    else:
        print(f"⚠️ Formato de comando não reconhecido: {comando_linha}")

def processar_resposta_laylay(texto_bruto):
    texto = str(texto_bruto or "").strip()
    if not texto:
        return FALLBACK_FALA_NEUTRA, []
    texto = re.sub(r"```(?:python|json)?\s*", " ", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s*```", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip()
    try:
        # Tenta encontrar o JSON mesmo se a IA colocar texto em volta
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            dados = json.loads(match.group(0))
            fala = str(dados.get("fala", dados.get("texto", "Pronto.")) or "").strip()
            # Se comandos vier quebrado ou vazio, garante que seja uma lista
            cmds = dados.get("comandos", [])
            if not isinstance(cmds, list): cmds = []
            try:
                acao_set = {str(c.get("acao", "")).strip().lower() for c in cmds if isinstance(c, dict)}
                fala_norm = _normalizar_texto_com_apelidos(fala)
                if any(x in fala_norm for x in ["playlist", "toquei", "coloquei", "montei", "criei"]) and not acao_set.intersection({"playlist_add", "playlist_play", "tocar_playlist", "youtube_search", "open_url"}):
                    if "email" in fala_norm or "bloqueio" in fala_norm or "tela de bloqueio" in fala_norm:
                        fala = "Vou ficar no assunto certo, Pedro. Quer que eu leia os emails ou faça outra coisa?"
                    else:
                        fala = "Vou ficar no que foi realmente executado, Pedro."
            except Exception:
                pass
            fala = re.sub(r"(?is)\bjson\b", " ", fala)
            fala = re.sub(r"\s+", " ", fala).strip()
            return limpar_para_voz(fala), cmds
    except Exception as e:
        print(f"⚠️ Erro ao processar JSON da IA: {e}")
        # Se quebrar, tenta pegar apenas o texto antes do erro
        texto_limpo = re.sub(r"(?is)\bjson\b", " ", texto)
        texto_limpo = re.sub(r"\{.*?\}", " ", texto_limpo, flags=re.DOTALL)
        texto_limpo = re.sub(r"\s+", " ", texto_limpo).strip()
        return limpar_para_voz(texto_limpo), []
    texto_limpo = re.sub(r"(?is)\bjson\b", " ", texto)
    texto_limpo = re.sub(r"\{.*?\}", " ", texto_limpo, flags=re.DOTALL)
    texto_limpo = re.sub(r"\s+", " ", texto_limpo).strip()
    return limpar_para_voz(texto_limpo), []

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
    if not ('ws_loop' in globals() and ws_loop) or not connected_extensions:
        return []
    rid = str(int(time.time() * 1000))
    ev = threading.Event()
    _pending_tabs_requests[rid] = {"event": ev, "tabs": []}
    try:
        msg = {"action": "get_tabs_list", "requestId": rid}
        asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)  # type: ignore[arg-type]
    except Exception:
        _pending_tabs_requests.pop(rid, None)
        return []
    ok = ev.wait(timeout_s)
    entry = _pending_tabs_requests.pop(rid, None) or {}
    if not ok:
        return []
    tabs = entry.get("tabs")
    return tabs if isinstance(tabs, list) else []

def solicitar_tab_reciclagem(target_domain: str, timeout_s: float = 3.0):
    if not ('ws_loop' in globals() and ws_loop) or not connected_extensions:
        return None
    dom = str(target_domain or "").strip().lower()
    if not dom:
        return None
    dom = dom.split(":")[0]
    if dom.startswith("www."):
        dom = dom[4:]
    rid = str(int(time.time() * 1000))
    ev = threading.Event()
    _pending_check_tabs_requests[rid] = {"event": ev, "tabId": None}
    try:
        msg = {"action": "check_tabs", "requestId": rid, "target_domain": dom}
        asyncio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg)), ws_loop)  # type: ignore[arg-type]
    except Exception:
        _pending_check_tabs_requests.pop(rid, None)
        return None
    ok = ev.wait(timeout_s)
    entry = _pending_check_tabs_requests.pop(rid, None) or {}
    if not ok:
        return None
    tab_id = entry.get("tabId")
    return int(tab_id) if isinstance(tab_id, int) else None

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
    if not ('ws_loop' in globals() and ws_loop) or not connected_extensions:
        return {"url": "", "title": "", "canal": ""}
    async def _request():
        rid = str(int(time.time() * 1000))
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        _pending_active_url_requests[rid] = fut
        try:
            await broadcast_command(json.dumps({"action": "get_youtube_data", "requestId": rid}))
            res = await asyncio.wait_for(fut, timeout=timeout_s)
            if isinstance(res, dict):
                return {"url": str(res.get("url") or ""), "title": str(res.get("title") or ""), "canal": str(res.get("canal") or "")}
            return {"url": "", "title": "", "canal": ""}
        except Exception:
            return {"url": "", "title": "", "canal": ""}
        finally:
            try:
                _pending_active_url_requests.pop(rid, None)
            except Exception:
                pass

    try:
        f = asyncio.run_coroutine_threadsafe(_request(), ws_loop)  # type: ignore[arg-type]
        return f.result(timeout=timeout_s + 0.5)
    except Exception:
        return {"url": "", "title": "", "canal": ""}

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

def interpretar_intencao_fuzzy_llm(fala_usuario: str):
    api_key = os.environ.get("OPENROUTER_API_KEY") or API_KEY
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_HTTP_REFERER,
        "X-Title": OPENROUTER_APP_TITLE
    }
    fala = (fala_usuario or "").strip()
    if not fala:
        return None
    prompt = (
        'Você é um tradutor de intenções. O usuário pode ter cometido erros de fala ou o microfone falhou. '
        'Exemplos de correção fonética: "apas facias" -> "abas vazias", "netiflis" -> "netflix", "pauja" -> "pausa", "tin maia" -> "tim maia". '
        'Se ele disse algo parecido com "fechar abas vazias", "abrir netflix" ou "pausar", retorne o comando correto em formato JSON: '
        '{"intent": "CLOSE_EMPTY_TABS"}. Analise o som das palavras (fonética). '
        'Intents permitidos: CLOSE_EMPTY_TABS, CLOSE_TABS, OPEN_NETFLIX, PAUSE_MUSIC, NEXT_MUSIC, OPEN_SITE, RESUMIR_PAGINA. '
        'Para OPEN_SITE inclua {"intent":"OPEN_SITE","topic":"pet|noticias|tech|outro","raw":"..."} quando possível. Para RESUMIR_PAGINA, inclua {"intent":"RESUMIR_PAGINA"}. '
        'Responda APENAS com JSON válido.'
    )
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": fala}
        ],
        "max_tokens": 80,
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
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and isinstance(parsed.get("intent"), str):
            return parsed
        return None
    except Exception:
        return None

def _achar_tab_por_dominio(tabs_list, dominio: str):
    dom = (dominio or "").lower()
    if not dom:
        return None
    for t in (tabs_list if isinstance(tabs_list, list) else []):
        if not isinstance(t, dict):
            continue
        tid = t.get("id")
        url = str(t.get("url") or "").lower()
        if isinstance(tid, int) and dom in url:
            return tid
    return None

def abrir_url_com_reciclagem(url: str, auto_click: bool = False):
    if not isinstance(url, str) or not url.strip():
        return False
    if not ('ws_loop' in globals() and ws_loop) or not connected_extensions:
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False
    try:
        dominio = urlparse(url).netloc.lower()
    except Exception:
        dominio = ""
    tabs = solicitar_lista_abas()
    tab_id = _achar_tab_por_dominio(tabs, dominio) if dominio else None
    if tab_id is not None:
        enviar_comando_chrome("update_tab", {"tabId": tab_id, "url": url, "auto_click": bool(auto_click)})
        return True
    enviar_comando_chrome("open_url", {"url": url, "auto_click": bool(auto_click)})
    return True

def garantir_aba_unica(url_alvo: str, auto_click: bool = False):
    url = str(url_alvo or "").strip()
    if not url:
        return False
    url = url.replace("searchq=", "search?q=")
    if 'ws_loop' in globals() and ws_loop and connected_extensions:
        try:
            dominio = urlparse(url).netloc.lower()
        except Exception:
            dominio = ""
        tabs = solicitar_lista_abas()
        tab_id = _achar_tab_por_dominio(tabs, dominio) if dominio else None
        if tab_id is not None:
            enviar_comando_chrome("update_tab", {"tabId": tab_id, "url": url, "auto_click": bool(auto_click)})
            return True
        enviar_comando_chrome("open_url", {"url": url, "auto_click": bool(auto_click)})
        return True
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False

# Alias para compatibilidade com chamadas que usam o nome antigo
abrir_url_navegador = abrir_url_com_reciclagem

def buscar_imagem_url(assunto: str):
    termo = str(assunto or "").strip()
    if not termo:
        return None
    for lang in ["pt", "en"]:
        try:
            api = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "prop": "pageimages",
                "titles": termo,
                "pithumbsize": 1000,
                "redirects": 1
            }
            r = requests.get(api, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            pages = (data.get("query") or {}).get("pages") or {}
            for _, page in pages.items():
                thumb = page.get("thumbnail") if isinstance(page, dict) else None
                if isinstance(thumb, dict) and thumb.get("source"):
                    return str(thumb.get("source"))
        except Exception:
            continue
    return f"https://source.unsplash.com/featured/?{urllib.parse.quote(termo)}"


def _normalizar_tema_pesquisa(tema: str) -> str:
    t = str(tema or "").strip()
    if not t:
        return ""
    t = re.sub(
        r"^(?:o\s+que\s+voce\s+acha|o\s+que\s+você\s+acha|voce\s+acha|você\s+acha|qual\s+sua\s+opiniao|qual\s+sua\s+opinião|quem\s+e|quem\s+é|o\s+que\s+e|o\s+que\s+é|como\s+funciona|como\s+que\s+funciona|me\s+explica|explica|me\s+fala\s+sobre|fala\s+sobre|me\s+fala\s+de|fala\s+de)\s+",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"^(o|a|os|as|um|uma)\s+", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(que saiu|que lançou|que lancou|que lançou agora|novo|nova|recentemente)\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\b(daqui|disso|daquilo|nisso|nesse|nessa|dela|dele|ela|ele|isso)\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip(" -,.!?;:")
    return t


def _tema_pesquisa_bagunçado(tema: str) -> bool:
    t = _normalizar_tema_pesquisa(tema)
    if not t:
        return True
    if len(t) < 3:
        return True
    tokens = re.findall(r"[a-zA-Z0-9À-ÿ_-]+", t)
    if len(tokens) >= 10:
        return True
    lixo = {"que", "de", "do", "da", "pra", "para", "isso", "essa", "esse", "ela", "ele", "negocio", "negócio", "coisa"}
    uteis = [tok for tok in tokens if tok.lower() not in lixo and len(tok) >= 3]
    if len(uteis) == 0:
        return True
    return False


def _pontuar_hit_tema(consulta: str, titulo: str, snippet: str = "") -> int:
    c = _normalizar_texto_curto(consulta)
    t = _normalizar_texto_curto(titulo)
    s = _normalizar_texto_curto(snippet)
    score = 0
    if c == t:
        score += 120
    if c and c in t:
        score += 70
    for token in re.findall(r"[a-z0-9à-ÿ_-]{3,}", c):
        if token in t:
            score += 18
        if token in s:
            score += 7
    if "(" in titulo or ")" in titulo:
        score -= 4
    return score


def _pesquisar_contexto_tema(tema: str, ttl_s: float = 1800.0) -> dict:
    """Busca um contexto curto sobre um tema para opiniões mais informadas."""
    global _pesquisa_tema_cache
    bruto = str(tema or "").strip()
    consulta = _normalizar_tema_pesquisa(bruto)
    if not consulta:
        return {"ok": False, "tema": bruto}
    if _tema_pesquisa_bagunçado(consulta):
        return {"ok": False, "tema": bruto, "consulta": consulta, "motivo": "tema_baguncado"}

    chave = _normalizar_texto_curto(consulta)
    agora = time.time()
    try:
        cache = dict(_pesquisa_tema_cache.get(chave) or {})
    except Exception:
        cache = {}
    if cache and (agora - float(cache.get("ts") or 0.0)) < ttl_s:
        return dict(cache.get("data") or {})

    def _cachear(data: dict) -> dict:
        _pesquisa_tema_cache[chave] = {"ts": agora, "data": dict(data or {})}
        if len(_pesquisa_tema_cache) > 80:
            _pesquisa_tema_cache = dict(list(_pesquisa_tema_cache.items())[-50:])
        return data

    try:
        for lang in ("pt", "en"):
            try:
                api = f"https://{lang}.wikipedia.org/w/api.php"
                r = requests.get(
                    api,
                    params={
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": consulta,
                        "srlimit": 1,
                        "utf8": 1,
                    },
                    timeout=4,
                )
                r.raise_for_status()
                data = r.json()
                hits = ((data.get("query") or {}).get("search") or [])
                if not hits:
                    continue
                melhores = sorted(
                    hits[:4],
                    key=lambda h: _pontuar_hit_tema(
                        consulta,
                        str(h.get("title") or ""),
                        str(h.get("snippet") or ""),
                    ),
                    reverse=True,
                )
                hit = melhores[0] if melhores else {}
                titulo = str(hit.get("title") or consulta).strip()
                score_hit = _pontuar_hit_tema(consulta, titulo, str(hit.get("snippet") or ""))
                if score_hit < 18:
                    continue
                r2 = requests.get(
                    api,
                    params={
                        "action": "query",
                        "format": "json",
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                        "redirects": 1,
                        "titles": titulo,
                        "utf8": 1,
                    },
                    timeout=4,
                )
                r2.raise_for_status()
                data2 = r2.json()
                pages = ((data2.get("query") or {}).get("pages") or {})
                for _, page in pages.items():
                    resumo = str((page or {}).get("extract") or "").strip()
                    if resumo:
                        resumo = re.sub(r"\s+", " ", resumo).strip()
                        return _cachear({
                            "ok": True,
                            "tema": bruto,
                            "consulta": consulta,
                            "titulo": titulo,
                            "resumo": resumo[:420],
                            "fonte": f"wikipedia_{lang}",
                            "confianca": min(0.98, 0.45 + (score_hit / 140.0)),
                        })
            except Exception:
                continue

        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": consulta,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                    "kl": "br-pt",
                },
                timeout=4,
            )
            r.raise_for_status()
            data = r.json()
            resumo = str(data.get("AbstractText") or "").strip()
            titulo = str(data.get("Heading") or consulta).strip()
            if not resumo:
                for item in list(data.get("RelatedTopics") or []):
                    if isinstance(item, dict) and item.get("Text"):
                        resumo = str(item.get("Text") or "").strip()
                        break
            if resumo:
                resumo = re.sub(r"\s+", " ", resumo).strip()
                score_ddg = _pontuar_hit_tema(consulta, titulo, resumo)
                if score_ddg < 14:
                    return _cachear({"ok": False, "tema": bruto, "consulta": consulta, "motivo": "resultado_fraco"})
                return _cachear({
                    "ok": True,
                    "tema": bruto,
                    "consulta": consulta,
                    "titulo": titulo,
                    "resumo": resumo[:420],
                    "fonte": "duckduckgo",
                    "confianca": min(0.9, 0.4 + (score_ddg / 140.0)),
                })
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ [PESQUISA TEMA] falha geral em '{consulta}': {e}")

    return _cachear({"ok": False, "tema": bruto, "consulta": consulta})

def _nome_arquivo_imagem(assunto: str, ext: str):
    base = re.sub(r"[^a-zA-Z0-9]+", "_", (assunto or "").strip().lower()).strip("_")
    base = base or "imagem_laylay"
    ext = (ext or "jpg").lower().lstrip(".")
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    try:
        os.makedirs(downloads, exist_ok=True)
    except Exception:
        pass
    path = os.path.join(downloads, f"{base}.{ext}")
    if not os.path.exists(path):
        return path
    i = 2
    while True:
        cand = os.path.join(downloads, f"{base}_{i}.{ext}")
        if not os.path.exists(cand):
            return cand
        i += 1

def baixar_imagem_direto(assunto: str):
    termo = str(assunto or "").strip()
    if not termo:
        return None
    url_img = buscar_imagem_url(termo)
    if not url_img:
        return None
    try:
        r = requests.get(url_img, stream=True, timeout=30)
        r.raise_for_status()
        ctype = str(r.headers.get("content-type") or "").lower()
        ext = "jpg"
        if "png" in ctype:
            ext = "png"
        elif "webp" in ctype:
            ext = "webp"
        elif "gif" in ctype:
            ext = "gif"
        elif "jpeg" in ctype or "jpg" in ctype:
            ext = "jpg"
        else:
            try:
                p = urlparse(url_img).path
                e = os.path.splitext(p)[1].lower().lstrip(".")
                if e in {"jpg", "jpeg", "png", "webp", "gif"}:
                    ext = "jpg" if e == "jpeg" else e
            except Exception:
                pass
        destino = _nome_arquivo_imagem(termo, ext)
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
        return destino
    except Exception:
        return None

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
    """
    Busca a URL do primeiro video do YouTube para um nome de musica,
    usando apenas uma requisicao HTTP silenciosa (sem abrir browser).
    Retorna a URL ou string vazia se falhar.
    """
    import re as _re
    import urllib.parse as _up
    try:
        q = _up.quote(query)
        url = f"https://www.youtube.com/results?search_query={q}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            print(f"[YT-SILENT] HTTP {resp.status_code} para '{query}'")
            return ""
        candidatos = _extrair_resultados_youtube_busca(resp.text, query, limite=1)
        if candidatos:
            yt_url = str(candidatos[0].get("url") or "").strip()
            if yt_url:
                print(f"[YT-SILENT] URL encontrada: {yt_url}")
                return yt_url
        print(f"[YT-SILENT] Nenhum videoId encontrado para '{query}'")
        return ""
    except Exception as e:
        print(f"[YT-SILENT] Erro: {e}")
        return ""

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
            for aba in abas_abertas:
                url = str(aba.get("url") or "")
                titulo = str(aba.get("titulo") or aba.get("title") or "")[:50]
                if not url or url.startswith("chrome://") or url.startswith("chrome-extension://"):
                    continue
                if url == aba_url_atual:
                    continue  # aba atual nao toca
                last = _tab_last_seen.get(url)
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

def _agendamentos_load() -> list:
    try:
        if os.path.exists(_agendamentos_file):
            with open(_agendamentos_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        print(f"[AGENDA] Erro ao carregar: {e}")
    return []

def _agendamentos_save(lista: list):
    try:
        with open(_agendamentos_file, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AGENDA] Erro ao salvar: {e}")

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

def _disparar_agendamento(ag: dict):
    """Executa um agendamento: fala o texto e roda os comandos opcionais."""
    descricao = str(ag.get("descricao") or "Pedro, chegou a hora!").strip()
    comandos_disparo = ag.get("comandos_no_disparo") or []
    nome = str(ag.get("nome") or ag.get("id", ""))[:30]
    print(f"\n⏰ [AGENDA] Disparando: '{nome}' — {descricao}")
    try:
        falar_com_lipsync(descricao, "calma", 1)
    except Exception as e:
        print(f"[AGENDA] Erro ao falar: {e}")
    if isinstance(comandos_disparo, list) and comandos_disparo:
        import threading as _th
        def _exec_cmds():
            for cmd in comandos_disparo:
                if not isinstance(cmd, dict):
                    continue
                acao = str(cmd.get("acao", "")).strip()
                alvo = str(cmd.get("alvo", "")).strip()
                try:
                    destino = str(cmd.get("target", "pc_a")).lower().strip()
                    
                    if acao == "open_app":
                        if destino == "pc_b":
                            _enviar_pc_b({"action": "open_app", "app": alvo})
                        else:
                            abrir_programa(alvo)

                    elif acao in ("open_url", "youtube_search"):
                        if acao == "youtube_search":
                            msg_payload = {"action": "youtube_search", "query": alvo}
                            if destino == "pc_b":
                                url_yt = "https://www.youtube.com/results?search_query=" + alvo.replace(" ", "+")
                                _enviar_pc_b({"action": "open_url", "url": url_yt})
                            else:
                                if ws_loop:
                                    import asyncio as _aio
                                    _aio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg_payload)), ws_loop)
                        else: # open_url
                            msg_payload = {"action": "open_url", "url": alvo}
                            if destino == "pc_b":
                                _enviar_pc_b(msg_payload)
                            else:
                                if ws_loop:
                                    import asyncio as _aio
                                    _aio.run_coroutine_threadsafe(broadcast_command(json.dumps(msg_payload)), ws_loop)

                    elif acao == "notificar":
                        if destino == "pc_b":
                            _enviar_pc_b({"action": "notificar", "alvo": alvo})
                        else:
                            import ctypes as _ct
                            _ct.windll.user32.MessageBoxW(0, alvo, "Laylay", 64)

                    elif acao == "tocar_playlist":
                        # _executar_exec reaproveita o controle completo
                        if destino == "pc_b":
                            # Hack rápido para pc_b em string alvo
                            alvo = alvo + " no pc b"
                        _executar_exec("TOCAR_PLAYLIST", alvo)
                        
                except Exception as _e:
                    print(f"[AGENDA] Erro ao executar cmd '{acao}': {_e}")
        _th.Thread(target=_exec_cmds, daemon=True).start()

def _agenda_daemon():
    """Thread daemon que verifica agendamentos a cada 30 segundos."""
    import time as _t
    import datetime as _dt
    _dia_map = {"seg":0,"ter":1,"qua":2,"qui":3,"sex":4,"sab":5,"dom":6}
    _disparados_hoje: set = set()  # IDs/offsets já disparados nessa sessão
    print("⏰ [AGENDA] Thread de agendamentos iniciada.")
    while True:
        try:
            agora = _dt.datetime.now()
            hora_atual = agora.strftime("%H:%M")
            dia_semana = agora.weekday()  # 0=seg...6=dom
            lista = _agendamentos_load()
            modificado = False
            for ag in list(lista):
                if not ag.get("ativo", True):
                    continue
                tipo = str(ag.get("tipo", "once"))
                ag_id = str(ag.get("id", ""))
                if tipo == "once":
                    ts_exec = ag.get("ts_execucao", 0)
                    if ts_exec and _t.time() >= ts_exec and ag_id not in _disparados_hoje:
                        _disparados_hoje.add(ag_id)
                        _disparar_agendamento(ag)
                        ag["ativo"] = False  # one-shot: desativa após disparar
                        modificado = True
                elif tipo in ("daily", "weekly"):
                    hora_ag = str(ag.get("hora", "")).strip()
                    if hora_ag != hora_atual:
                        continue
                    chave = f"{ag_id}_{agora.strftime('%Y-%m-%d')}"
                    if chave in _disparados_hoje:
                        continue
                    dias = ag.get("dias", "todos")
                    if dias == "todos" or tipo == "daily":
                        disparar = True
                    elif isinstance(dias, list):
                        disparar = dia_semana in [_dia_map.get(str(d).lower(), -1) for d in dias]
                    else:
                        disparar = True
                    if disparar:
                        _disparados_hoje.add(chave)
                        _disparar_agendamento(ag)
            if modificado:
                _agendamentos_save(lista)
        except Exception as _e:
            print(f"[AGENDA] Erro no daemon: {_e}")
        _t.sleep(30)

def _playlists_load():
    data = _playlists_load_mente(playlists_state_file, playlists_legacy_file)
    try:
        if isinstance(data, dict):
            playlists_carregadas.clear()
            playlists_carregadas.update(data)
    except Exception:
        pass
    return data


def LIST_PLAYLIST_CONTENT(nome_playlist: str):
    nm = _resolver_nome_playlist_contextual(nome_playlist or "")
    if not nm:
        return {"ok": False, "error": "missing_name", "name": "", "total": 0, "last_titles": []}
    data = _playlists_load()
    lst = data.get(nm)
    if not isinstance(lst, list):
        lst = []
    titulos = []
    for it in lst:
        if isinstance(it, dict):
            t = str(it.get("titulo") or "").strip()
            if t:
                titulos.append(_yt_clean_title(t) or t)
    last_titles = [t for t in titulos[-3:] if t]
    return {"ok": True, "name": nm, "total": len(lst), "last_titles": last_titles}


def _fala_playlist_conteudo_estilosa(info: dict, fallback_nome: str = "") -> str:
    return _fala_playlist_conteudo_estilosa_mente(info, fallback_nome)


def list_playlist_urls(name: str):
    return _list_playlist_urls_mente(name, _playlists_load())


def _playlists_save(data: dict):
    return _playlists_save_mente(playlists_state_file, data)

def _yt_clean_url(url: str) -> str:
    try:
        u = urlparse(url)
        q = urllib.parse.parse_qs(u.query)
        vid = (q.get("v") or [""])[0]
        if vid:
            return f"https://www.youtube.com/watch?v={vid}"
        return url
    except Exception:
        return url

def _yt_clean_title(title: str) -> str:
    return _yt_clean_title_mente(title)

def _remover_acentos(s: str) -> str:
    try:
        n = unicodedata.normalize("NFKD", str(s or ""))
        return "".join(c for c in n if not unicodedata.combining(c))
    except Exception:
        return str(s or "")

_CORRECOES_FONETICAS = (
    (r"\bpaly\s*list\b", "playlist"),
    (r"\bplay\s*list\b", "playlist"),
    (r"\bpalylist\b", "playlist"),
    (r"\bplalyst\b", "playlist"),
    (r"\bplalist\b", "playlist"),
    (r"\bcamaitachi\b", "kamaitachi"),
    (r"\bkamaitaxi\b", "kamaitachi"),
    (r"\bkamaytachi\b", "kamaitachi"),
    (r"\bkamaitaxi\b", "kamaitachi"),
    (r"\byoutub\b", "youtube"),
    (r"\butube\b", "youtube"),
    (r"\bspotifi\b", "spotify"),
)

def _aplicar_correcao_fonetica(texto: str) -> str:
    t = str(texto or "").lower().strip()
    if not t:
        return ""
    t = re.sub(r"\s+", " ", t)
    for padrao, troca in _CORRECOES_FONETICAS:
        t = re.sub(padrao, troca, t, flags=re.IGNORECASE)
    return t

_APELIDOS_CACHE = {"ts": 0.0, "mapa": {}}
_APELIDOS_STOPWORDS = {
    "hoje", "amanha", "amanhã", "ontem", "agora", "depois", "antes",
    "segunda", "terca", "terça", "quarta", "quinta", "sexta", "sabado", "sábado", "domingo",
    "janeiro", "fevereiro", "marco", "março", "abril", "maio", "junho", "julho", "agosto",
    "setembro", "outubro", "novembro", "dezembro",
    "sim", "nao", "não", "talvez", "isso", "aquilo", "isto", "aqui", "ali", "lá",
    "eu", "voce", "você", "ele", "ela", "eles", "elas", "meu", "minha", "seu", "sua",
}

def _carregar_apelidos_memoria(force: bool = False) -> dict:
    """Carrega apelidos aprendidos do banco e mantém cache leve em memoria."""
    agora = time.time()
    cache = _APELIDOS_CACHE
    if not force and cache.get("mapa") and agora - float(cache.get("ts") or 0.0) < 180:
        return dict(cache.get("mapa") or {})

    mapa = {}
    try:
        itens = MEMORIA_SQLITE.listar_aprendizados_semanticos(limit=300)
        for item in itens:
            if str(item.get("tipo") or "").strip().lower() not in {"apelido", "alias"}:
                continue
            alias = _normalizar_texto(item.get("gatilho") or "")
            alvo = str(item.get("valor") or "").strip()
            if not alias or not alvo:
                continue
            alias_norm = _normalizar_texto(alias)
            alvo_norm = _normalizar_texto(alvo)
            if not alias_norm or not alvo_norm or alias_norm == alvo_norm:
                continue
            mapa[alias_norm] = alvo
    except Exception as e:
        print(f"⚠️ [APELIDOS] falha ao carregar cache: {e}")

    _APELIDOS_CACHE["ts"] = agora
    _APELIDOS_CACHE["mapa"] = mapa
    return dict(mapa)

def _aplicar_apelidos_learned(texto: str) -> str:
    t = str(texto or "").strip()
    if not t:
        return t
    mapa = _carregar_apelidos_memoria()
    if not mapa:
        return t

    t_norm = _normalizar_texto(t)
    for alias_norm, alvo in sorted(mapa.items(), key=lambda kv: len(kv[0]), reverse=True):
        alvo_norm = _normalizar_texto(alvo)
        if not alias_norm or not alvo_norm:
            continue
        padrao = rf"\b{re.escape(alias_norm)}\b"
        t_norm = re.sub(padrao, alvo_norm, t_norm, flags=re.IGNORECASE)
    return t_norm

def _normalizar_texto_com_apelidos(s: str) -> str:
    return _aplicar_apelidos_learned(_normalizar_texto(s))

def _extrair_apelido_ensinavel(texto: str):
    bruto = str(texto or "").strip()
    if not bruto or "?" in bruto:
        return None
    t = _normalizar_texto_com_apelidos(bruto)
    if not t or len(t.split()) > 9:
        return None

    marcadores_ensino = [
        "apelido", "alias", "quer dizer", "significa", "vira",
        "chama", "chamado de", "pra voce", "pra você",
        "quando eu falar", "quando eu disser", "quero te ensinar",
    ]
    if not any(m in t for m in marcadores_ensino):
        return None

    padroes = [
        r"^(?:meu|minha|o|a|um|uma|esse|essa|esse aqui|essa aqui)?\s*(?:apelido|alias)\s+(?P<alias>.+?)\s+(?:e|eh|é|quer dizer|significa|vira|chama|chamado de|apelido de)\s+(?P<alvo>.+)$",
        r"^(?P<alias>.+?)\s+(?:quer dizer|significa|vira|chama|é chamado de|eh chamado de|apelido de)\s+(?P<alvo>.+)$",
        r"^(?:quando eu falar|quando eu disser)\s+(?P<alias>.+?)\s+(?:e|eh|é)\s+(?P<alvo>.+)$",
    ]
    for padrao in padroes:
        m = re.match(padrao, t, flags=re.IGNORECASE)
        if not m:
            continue
        tem_marcador_explicito = any(
            marcador in padrao
            for marcador in ("apelido", "alias", "quer dizer", "significa", "vira", "chama", "chamado de")
        )
        alias = _normalizar_texto(m.group("alias") or "")
        alvo = _normalizar_texto(m.group("alvo") or "")
        if not alias or not alvo:
            continue
        alias_tokens = alias.split()
        alvo_tokens = alvo.split()
        if len(alias_tokens) > 4 or len(alvo_tokens) > 6:
            continue
        if alias in _APELIDOS_STOPWORDS or alvo in _APELIDOS_STOPWORDS:
            continue
        if alias.startswith("playlist ") or alvo.startswith("playlist "):
            continue
        if not any(ch.isalpha() for ch in alias) or not any(ch.isalpha() for ch in alvo):
            continue
        if not tem_marcador_explicito and max(len(alias), len(alvo)) < 6:
            continue
        if len(alias_tokens) == len(alvo_tokens) and len(alias_tokens) > 1:
            continue
        if alias == alvo:
            continue
        return {"apelido": alias, "alvo": alvo, "texto": bruto}
    return None

def _aprender_apelido(alias: str, alvo: str, contexto: str = "") -> bool:
    alias_limpo = _normalizar_texto(alias or "")
    alvo_limpo = _normalizar_texto(alvo or "")
    if not alias_limpo or not alvo_limpo or alias_limpo == alvo_limpo:
        return False
    try:
        salvo = MEMORIA_SQLITE.salvar_aprendizado_semantico(
            tipo="apelido",
            gatilho=alias_limpo,
            valor=alvo_limpo,
            regra=f'Apelido "{alias_limpo}" aponta para "{alvo_limpo}".',
            texto_original=str(contexto or f"{alias_limpo} é {alvo_limpo}"),
            confianca=0.96,
        )
        _carregar_apelidos_memoria(force=True)
        if salvo:
            print(f"🏷️ [APELIDO] '{alias_limpo}' aprendido como '{alvo_limpo}'")
            return True
    except Exception as e:
        print(f"⚠️ [APELIDO] falha ao salvar apelido: {e}")
    return False

def _processar_aprendizado_apelido_imediato(texto: str) -> bool:
    if _texto_social_curto(texto):
        return False
    info = _extrair_apelido_ensinavel(texto)
    if not info:
        return False
    alias = str(info.get("apelido") or "").strip()
    alvo = str(info.get("alvo") or "").strip()
    contexto = str(info.get("texto") or texto or "").strip()
    if not alias or not alvo:
        return False
    if _aprender_apelido(alias, alvo, contexto):
        fala = f"Beleza, vou lembrar que {alias} é {alvo}."
        print(f"🏷️ [APELIDO] {fala}")
        falar_com_lipsync(fala, "calma", 1)
        return True
    return False

def _normalizar_texto(s: str) -> str:
    t = _remover_acentos(str(s or "").lower())
    t = _aplicar_correcao_fonetica(t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _titulo_fingerprint(titulo: str) -> str:
    t = _normalizar_texto(_yt_clean_title(titulo))
    for w in ["oficial", "video", "lyrics", "clipe", "hd", "4k", "audio", "áudio", "official"]:
        t = re.sub(rf"\b{re.escape(_normalizar_texto(w))}\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _canal_fingerprint(canal: str) -> str:
    return _normalizar_texto(canal)

def _sim_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    try:
        return float(difflib.SequenceMatcher(None, a, b).ratio())
    except Exception:
        return 0.0

def _fala_playlist_sucesso(title: str, playlist_nome: str, created: bool) -> str:
    pl = _limpar_nome_playlist(playlist_nome)
    tit = _yt_clean_title(title) or "esse som"
    if created:
        return f"Beleza, Pedro. Criei a playlist {pl} e já guardei o link."
    return f"Pronto, {tit} tá lá na playlist {pl}. Só não me pede pra arrumar a bagunça desse arquivo."

def _fala_playlist_duplicado(title: str, playlist_nome: str) -> str:
    pl = _limpar_nome_playlist(playlist_nome)
    tit = _yt_clean_title(title) or "esse som"
    return f"Essa já tá lá, Pedro. Quer ouvir {tit} o dia inteiro ou tá com saudade do repeat?"

def _fala_playlist_duplicado_meta(title: str, playlist_nome: str, other_channel: bool) -> str:
    pl = _limpar_nome_playlist(playlist_nome)
    tit = _yt_clean_title(title) or "essa música"
    if other_channel:
        return f"Pedro, você já tem {tit} na playlist {pl}, só que de outro canal. Não vou salvar de novo pra não virar bagunça."
    return f"Essa música já tá guardada na playlist {pl}, só que o link é outro. Vou manter o que já tava lá pra poupar espaço."

def _limpar_nome_playlist(nome: str) -> str:
    return _limpar_nome_playlist_mente(nome)

def _resolver_nome_playlist_contextual(nome: str) -> str:
    try:
        data = playlists_carregadas if isinstance(playlists_carregadas, dict) and playlists_carregadas else _playlists_load()
    except Exception:
        data = {}
    return _resolver_nome_playlist_contextual_mente(nome, data, str(_musica_estado_get("ultima_playlist") or ""))

def _playlist_nome_explicito_na_frase(texto: str) -> bool:
    t = _normalizar_texto_com_apelidos(str(texto or "").strip())
    if not t or "playlist" not in t:
        return False
    m = re.search(r"\bplaylist\b\s+(.+)$", t, flags=re.IGNORECASE)
    if not m:
        return False
    resto = str(m.group(1) or "").strip()
    resto = re.sub(r"^(chamada|com nome|de nome)\s+", "", resto, flags=re.IGNORECASE)
    resto = re.sub(r"^(e\s+)?(coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add|toca|toque|abre|abra|cria|criar|crie|apaga|apagar|limpa|limpar|remove|remover|retira|retirar)\b.*$", "", resto, flags=re.IGNORECASE)
    resto = resto.strip(" .,!?:;")
    return bool(resto)


def _playlist_item_label(item) -> str:
    if isinstance(item, dict):
        return _yt_clean_title(str(item.get("titulo") or "")) or str(item.get("url") or "essa música")
    return str(item or "essa música")


def _playlist_item_match(item, musica: str) -> bool:
    alvo = _normalizar_texto(musica)
    if not alvo or alvo in {"ela", "essa", "isso", "musica", "música"}:
        return False
    if isinstance(item, dict):
        titulo = _normalizar_texto(item.get("titulo") or "")
        url = _normalizar_texto(item.get("url") or "")
        return alvo in titulo or alvo in url
    return alvo in _normalizar_texto(item)


def mover_item_playlist(origem: str, destino: str, musica: str = "") -> dict:
    data = _playlists_load()
    origem_nm = _limpar_nome_playlist(origem)
    destino_nm = _limpar_nome_playlist(destino)
    musica_txt = str(musica or "").strip()
    if not origem_nm or not destino_nm:
        return {"ok": False, "error": "missing_playlist", "titulo": ""}
    try:
        res = _detectar_mover_playlist_texto_mente(
            f"move {musica_txt} da playlist {origem_nm} para a playlist {destino_nm}"
        )
        if res:
            # Mantém a mesma interface, mas a regra real fica no módulo novo.
            pass
    except Exception:
        pass
    origem_lst = data.get(origem_nm)
    if not isinstance(origem_lst, list) or not origem_lst:
        return {"ok": False, "error": "source_empty", "titulo": "", "origem": origem_nm, "destino": destino_nm}
    idx = -1
    if musica_txt and _normalizar_texto(musica_txt) not in {"ela", "essa", "isso", "musica", "música"}:
        for i, item in enumerate(origem_lst):
            if _playlist_item_match(item, musica_txt):
                idx = i
                break
    if idx < 0:
        idx = len(origem_lst) - 1
    item = origem_lst.pop(idx)
    destino_lst = data.setdefault(destino_nm, [])
    if not isinstance(destino_lst, list):
        destino_lst = []
        data[destino_nm] = destino_lst
    item_url = _yt_clean_url(str(item.get("url") or "")) if isinstance(item, dict) else _yt_clean_url(str(item or ""))
    ja_existe = False
    if item_url:
        for existente in destino_lst:
            ex_url = _yt_clean_url(str(existente.get("url") or "")) if isinstance(existente, dict) else _yt_clean_url(str(existente or ""))
            if ex_url == item_url:
                ja_existe = True
                break
    if not ja_existe:
        destino_lst.append(item)
    if not origem_lst:
        data[origem_nm] = []
    _playlists_save(data)
    return {"ok": True, "duplicated": ja_existe, "titulo": _playlist_item_label(item), "origem": origem_nm, "destino": destino_nm}


def detectar_mover_playlist_texto(texto: str):
    return _detectar_mover_playlist_texto_mente(texto)


def extrair_nome_playlist(texto: str) -> str:
    t = _normalizar_texto_com_apelidos(str(texto or "").strip())
    padroes = [
        r"(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add).{0,80}?(?:na|nessa|nesta|para a|pra|em)\s+playlist\s+(?P<nome>.+)$",
        r"(?:na|para|a)\s+playlist\s+(?P<nome>.+?)(?:\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add|toca|toque|abre|abra|cria|criar|crie|apaga|apagar|limpa|limpar|remove|remover|retira|retirar)\b.*|$)",
        r"playlist\s+(?:chamada|com nome)?\s*(?P<nome>.+?)(?:\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add|toca|toque|abre|abra|cria|criar|crie|apaga|apagar|limpa|limpar|remove|remover|retira|retirar)\b.*|$)",
    ]
    nome = ""
    for padrao in padroes:
        m = re.search(padrao, t, flags=re.IGNORECASE)
        if m:
            nome = m.group("nome")
            break
    nome = _limpar_nome_playlist(nome)
    print(f"[DEBUG] Nome extraído da playlist: {nome}")
    return nome

def _formatar_playlists_para_prompt() -> str:
    if not playlists_carregadas:
        return "Nenhuma playlist salva ainda."
    nomes = sorted(list(playlists_carregadas.keys()))
    if not nomes:
        return "Nenhuma playlist salva ainda."
    return "Playlists salvas: " + ", ".join([f"'{n}'" for n in nomes]) + "."


def _pedido_lista_geral_playlist(texto_original: str, params: dict) -> bool:
    texto = _normalizar_texto_com_apelidos(str(texto_original or ""))
    if any(kw in texto for kw in [
        "quais sao minhas playlists",
        "quais são minhas playlists",
        "quais playlists eu tenho",
        "que playlists eu tenho",
        "listar minhas playlists",
        "lista minhas playlists",
        "mostra minhas playlists",
        "mostra as playlists",
        "quais sao as minhas playlists",
        "quais são as minhas playlists",
    ]):
        return True

    raw = str(
        params.get("nome_playlist")
        or params.get("playlist")
        or params.get("nome")
        or ""
    ).strip()
    if not raw:
        return False

    if any(sep in raw for sep in [",", ";", "|", "/"]):
        return True

    raw_norm = _limpar_nome_playlist(raw)
    if raw_norm in {"minhas playlists", "minha playlist", "playlist", "playlists"}:
        return True

    return False


def _listar_playlists_salvas() -> str:
    data = _playlists_load()
    if isinstance(data, dict):
        try:
            playlists_carregadas.clear()
            playlists_carregadas.update(data)
        except Exception:
            pass
    nomes = []
    for chave, itens in sorted((data or {}).items(), key=lambda kv: str(kv[0]).lower()):
        nome = str(chave or "").strip()
        if not nome:
            continue
        total = len(itens) if isinstance(itens, list) else 0
        nomes.append(f"{nome} ({total})")
    if not nomes:
        return "Você ainda não tem nenhuma playlist salva."
    if len(nomes) == 1:
        return f"Sua playlist salva é {nomes[0]}."
    return f"Suas playlists são: {', '.join(nomes)}."


def _playlists_laylay_load():
    global playlists_laylay_carregadas
    os.makedirs(PASTA_PLAYLISTS_LAYLAY, exist_ok=True)
    data = _playlists_load_mente(PLAYLISTS_LAYLAY_ARQUIVO, PLAYLISTS_LAYLAY_ARQUIVO)
    playlists_laylay_carregadas = data if isinstance(data, dict) else {}
    return playlists_laylay_carregadas


def _playlists_laylay_save(data: dict) -> bool:
    global playlists_laylay_carregadas
    os.makedirs(PASTA_PLAYLISTS_LAYLAY, exist_ok=True)
    ok = _playlists_save_mente(PLAYLISTS_LAYLAY_ARQUIVO, data or {})
    if ok:
        playlists_laylay_carregadas = dict(data or {})
    return ok


def _sincronizar_playlists_da_laylay():
    global playlists_laylay_carregadas
    atuais = _playlists_laylay_load()
    sincronizadas = _sincronizar_playlists_da_laylay_mente(
        _playlists_load(),
        _musica_dados_diarios,
        atuais,
    )
    _playlists_laylay_save(sincronizadas)
    return sincronizadas


def _listar_playlists_da_laylay(nome: str = "") -> str:
    data = _sincronizar_playlists_da_laylay()
    nome_limpo = _limpar_nome_playlist(nome or "")
    if nome_limpo:
        info = _fala_playlist_conteudo_estilosa_mente(
            {
                "name": nome_limpo,
                "total": len(data.get(nome_limpo) or []),
                "last_titles": [
                    _yt_clean_title(str((item or {}).get("titulo") or ""))
                    for item in (data.get(nome_limpo) or [])[:3]
                    if isinstance(item, dict)
                ],
            },
            nome_limpo,
        )
        return info
    nomes = []
    for chave, itens in sorted((data or {}).items(), key=lambda kv: str(kv[0]).lower()):
        total = len(itens) if isinstance(itens, list) else 0
        nomes.append(f"{chave} ({total})")
    if not nomes:
        return "Eu ainda não montei playlists minhas por aqui."
    return f"As minhas playlists são: {', '.join(nomes)}."


def _adicionar_descoberta_na_playlist_da_laylay(item: dict) -> None:
    if not isinstance(item, dict):
        return
    data = _playlists_laylay_load()
    lst = data.setdefault("descobertas_da_laylay", [])
    if not isinstance(lst, list):
        lst = []
        data["descobertas_da_laylay"] = lst
    url = _yt_clean_url(str(item.get("url") or "").strip())
    for existente in lst:
        if isinstance(existente, dict) and _yt_clean_url(str(existente.get("url") or "").strip()) == url:
            _playlists_laylay_save(data)
            return
    lst.append({
        "url": url,
        "titulo": str(item.get("titulo") or "").strip(),
        "canal": str(item.get("canal") or "").strip(),
        "data": str(item.get("data") or datetime.now().date().isoformat()),
        "motivo": str(item.get("motivo") or "descoberta_da_laylay").strip(),
    })
    _playlists_laylay_save(data)


def _copiar_faixa_da_playlist_laylay(nome_playlist_laylay: str, musica: str, destino_usuario: str) -> dict:
    data_laylay = _sincronizar_playlists_da_laylay()
    faixa = _encontrar_faixa_playlist_laylay_mente(data_laylay, nome_playlist_laylay, musica)
    if not faixa:
        return {"ok": False, "erro": "nao_encontrada"}
    res = add_to_playlist_url(
        destino_usuario,
        str(faixa.get("url") or ""),
        str(faixa.get("titulo") or ""),
        str(faixa.get("canal") or ""),
    )
    return {"ok": bool(isinstance(res, dict) and res.get("ok")), "faixa": faixa, "destino": destino_usuario}


def _resolver_query_musical_por_estilo(query: str, texto_original: str = "") -> dict:
    q = _normalizar_query_musical(query or texto_original)
    return {"query": q, "origem": "explicita"}


def _detectar_playlist_nome_direto(texto: str) -> str:
    t = _normalizar_texto_com_apelidos(str(texto or "").strip())
    if not t:
        return ""

    data = {}
    try:
        data = playlists_carregadas if isinstance(playlists_carregadas, dict) and playlists_carregadas else _playlists_load()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}

    gatilhos = [
        "coloca", "coloque", "toca", "toque", "abre", "abra",
        "sintoniza", "sintonize", "manda", "manda tocar"
    ]
    resto = t
    for gat in gatilhos:
        if resto.startswith(gat + " "):
            resto = resto[len(gat):].strip()
            break

    resto = re.sub(r"^(a|o|as|os|essa|esse|essa musica|essa música|essa playlist|esse som)\s+", "", resto).strip()
    resto = _limpar_nome_playlist(resto)
    if not resto:
        return ""

    if resto in data:
        return resto

    candidatos = []
    for chave in data.keys():
        chave_nm = _limpar_nome_playlist(str(chave or ""))
        if not chave_nm:
            continue
        if resto == chave_nm or resto.startswith(chave_nm) or chave_nm.startswith(resto):
            candidatos.append(chave_nm)
    candidatos = list(dict.fromkeys(candidatos))
    if len(candidatos) == 1:
        return candidatos[0]
    return ""

def _carregar_playlists_para_memoria():
    global playlists_carregadas
    playlists_carregadas = _playlists_load()
    _sincronizar_playlists_da_laylay()
    print(f"🎵 [PLAYLISTS] Playlists carregadas: {list(playlists_carregadas.keys())}")

def _ensure_playlists_file() -> bool:
    created = False
    try:
        base_dir = os.path.dirname(playlists_state_file)
        os.makedirs(base_dir, exist_ok=True)
        if not os.path.exists(playlists_state_file):
            if os.path.exists(playlists_legacy_file):
                try:
                    with open(playlists_legacy_file, "r", encoding="utf-8") as src:
                        legacy = src.read()
                    with open(playlists_state_file, "w", encoding="utf-8") as dst:
                        dst.write(legacy if legacy.strip() else "{}")
                except Exception:
                    with open(playlists_state_file, "w", encoding="utf-8") as f:
                        f.write("{}")
            else:
                with open(playlists_state_file, "w", encoding="utf-8") as f:
                    f.write("{}")
            created = True
    except Exception:
        pass
    return created

def add_to_playlist_url(playlist_name: str, url: str, title: str = "", canal: str = ""):
    data = _playlists_load()
    res = _add_to_playlist_url_mente(
        playlist_name,
        url,
        title,
        canal,
        state_file=playlists_state_file,
        legacy_file=playlists_legacy_file,
        data=data,
        ultima_playlist=str(_musica_estado_get("ultima_playlist") or ""),
    )
    try:
        name = _resolver_nome_playlist_contextual(playlist_name or "")
        link = _yt_clean_url(str(url or ""))
        if res.get("ok"):
            print(f"[PLAYLIST] Adicionando URL {link} na chave {name}")
            print(f"[PLAYLIST] Sucesso: {_yt_clean_title(title) or link} salvo em {name}")
            if isinstance(data, dict):
                playlists_carregadas.clear()
                playlists_carregadas.update(data)
    except Exception:
        pass
    return res

def add_to_playlist_from_active_tab(playlist_name: str):
    name = (playlist_name or "").strip().lower()
    if not name:
        return False
    info = solicitar_aba_ativa(timeout_s=2.0)
    url = str(info.get("url") or "")
    title = str(info.get("title") or "")
    canal = str(info.get("canal") or "")
    return add_to_playlist_url(name, url, title, canal)

def ADD_TO_PLAYLIST(nome_playlist: str, url: str, titulo: str, canal: str = "") -> bool:
    name = _limpar_nome_playlist(nome_playlist)
    if not name:
        return False
    link = str(url or "").strip()
    if not link:
        return False
    musica = _yt_clean_title(str(titulo or "")) or link
    print(f"[DISK] Escrevendo {musica} em {playlists_state_file}...")
    res = add_to_playlist_url(name, link, str(titulo or ""), str(canal or ""))
    ok = res.get("ok") if isinstance(res, dict) else bool(res)
    if not ok:
        return False
    try:
        data = _playlists_load()
        lst = data.get(name)
        if not isinstance(lst, list):
            return False
        target = _yt_clean_url(link)
        for it in reversed(lst[-10:]):
            if isinstance(it, dict):
                u = str(it.get("url") or "").strip()
            else:
                u = str(it or "").strip()
            if not u:
                continue
            if _yt_clean_url(u) == target:
                return True
        return False
    except Exception:
        return False

def _playlist_primeira_url(nome: str):
    return _playlist_primeira_url_mente(nome, _playlists_load())

def _playlist_item_at(nome: str, idx: int):
    return _playlist_item_at_mente(nome, idx, _playlists_load())

_ORDINAL_IDX = {
    "primeira": 0, "primeiro": 0, "1ª": 0, "1º": 0,
    "segunda": 1, "segundo": 1, "2ª": 1, "2º": 1,
    "terceira": 2, "terceiro": 2, "3ª": 2, "3º": 2,
    "quarta": 3, "quarto": 3, "4ª": 3, "4º": 3,
    "quinta": 4, "quinto": 4, "5ª": 4, "5º": 4,
    "última": -1, "ultimo": -1, "último": -1, "ultima": -1,
}

def _parse_indice_ordinal(token: str):
    t = str(token or "").strip().lower()
    t = re.sub(r"^\s*(toque|toca|coloca|abre)\b", " ", t).strip()
    t = re.sub(r"^(a|o|uma|um)\s+", "", t).strip()
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return None
    return _ORDINAL_IDX.get(t)

def playlist_len(nome: str) -> int:
    return _playlist_len_mente(nome, _playlists_load())

def _playlist_shuffle_start(nome: str):
    global indice_atual
    pl = _resolver_nome_playlist_contextual(nome)
    if not pl:
        return None
    data = _playlists_load()
    lst = data.get(pl)
    if not isinstance(lst, list) or not lst:
        return None
    queue = list(lst)
    random.shuffle(queue)
    _musica_estado_set("ultima_playlist", pl)
    playlist_state["name"] = pl
    playlist_state["user_intervened"] = False
    playlist_state["shuffle"] = True
    playlist_state["shuffle_queue"] = queue
    playlist_state["shuffle_index"] = 0
    indice_atual = 0
    first = queue[0]
    url = str(first.get("url") or "") if isinstance(first, dict) else str(first)
    titulo = _yt_clean_title(str(first.get("titulo") or "")) if isinstance(first, dict) else ""
    canal = str(first.get("canal") or "") if isinstance(first, dict) else ""
    return {"url": url, "titulo": titulo, "canal": canal, "len": len(queue)}

def delete_playlist(nome: str) -> bool:
    pl = _resolver_nome_playlist_contextual(nome)
    if not pl:
        return False
    data = _playlists_load()
    if pl not in data:
        return False
    try:
        data.pop(pl, None)
    except Exception:
        return False
    return bool(_playlists_save(data))

def _playlist_avancar_proxima():
    global indice_atual
    nm = playlist_state.get("name") or ""
    if not nm:
        return False
    if playlist_state.get("shuffle") and isinstance(playlist_state.get("shuffle_queue"), list):
        queue = playlist_state.get("shuffle_queue") or []
        idx = int(playlist_state.get("shuffle_index") or 0) + 1
        if idx >= len(queue):
            print(f"🎵 Playlist '{nm}' terminou")
            playlist_state["name"] = ""
            playlist_state["index"] = 0
            indice_atual = 0
            playlist_state.pop("shuffle", None)
            playlist_state.pop("shuffle_queue", None)
            playlist_state.pop("shuffle_index", None)
            return False
        playlist_state["shuffle_index"] = idx
        indice_atual = idx
        item = queue[idx]
        if isinstance(item, dict):
            url = str(item.get("url") or "")
            titulo = _yt_clean_title(str(item.get("titulo") or "")) or url
            canal = str(item.get("canal") or "")
        else:
            url = str(item)
            titulo = url
            canal = ""
        print(f"[PLAYLIST] Abrindo (Strong Reuse): {titulo} | Canal: {canal}")
        # ✅ NOVA CHAMADA FORTE (sempre mesma aba)
        validar_e_enviar_comando("youtube_play", {"url": url})
        playlist_state["last_url"] = url
        return True
    data = _playlists_load()
    lst = data.get(nm)
    if not isinstance(lst, list) or not lst:
        return False
    idx = int(playlist_state.get("index") or 0) + 1
    if idx >= len(lst):
        print(f"🎵 Playlist '{nm}' terminou")
        playlist_state["name"] = ""
        playlist_state["index"] = 0
        indice_atual = 0
        return False
    playlist_state["index"] = idx
    indice_atual = idx
    item = lst[idx]
    if isinstance(item, dict):
        url = str(item.get("url") or "")
        titulo = _yt_clean_title(str(item.get("titulo") or "")) or url
        canal = str(item.get("canal") or "")
    else:
        url = str(item)
        titulo = url
        canal = ""
    print(f"[PLAYLIST] Abrindo (Strong Reuse): {titulo} | Canal: {canal}")
    # ✅ NOVA CHAMADA FORTE (sempre mesma aba)
    validar_e_enviar_comando("youtube_play", {"url": url})
    playlist_state["last_url"] = url
    return True


def _playlist_voltar_anterior():
    global indice_atual
    nm = playlist_state.get("name") or ""
    if not nm:
        return False
    if playlist_state.get("shuffle") and isinstance(playlist_state.get("shuffle_queue"), list):
        queue = playlist_state.get("shuffle_queue") or []
        idx_atual = int(playlist_state.get("shuffle_index") or 0)
        if idx_atual <= 0 or idx_atual >= len(queue):
            return False
        idx = idx_atual - 1
        playlist_state["shuffle_index"] = idx
        indice_atual = idx
        item = queue[idx]
        if isinstance(item, dict):
            url = str(item.get("url") or "")
            titulo = _yt_clean_title(str(item.get("titulo") or "")) or url
            canal = str(item.get("canal") or "")
        else:
            url = str(item)
            titulo = url
            canal = ""
        print(f"[PLAYLIST] Voltando (Strong Reuse): {titulo} | Canal: {canal}")
        validar_e_enviar_comando("youtube_play", {"url": url})
        playlist_state["last_url"] = url
        return True

    data = _playlists_load()
    lst = data.get(nm)
    if not isinstance(lst, list) or not lst:
        return False
    idx_atual = int(playlist_state.get("index") or 0)
    if idx_atual <= 0 or idx_atual >= len(lst):
        return False
    idx = idx_atual - 1
    playlist_state["index"] = idx
    indice_atual = idx
    item = lst[idx]
    if isinstance(item, dict):
        url = str(item.get("url") or "")
        titulo = _yt_clean_title(str(item.get("titulo") or "")) or url
        canal = str(item.get("canal") or "")
    else:
        url = str(item)
        titulo = url
        canal = ""
    print(f"[PLAYLIST] Voltando (Strong Reuse): {titulo} | Canal: {canal}")
    validar_e_enviar_comando("youtube_play", {"url": url})
    playlist_state["last_url"] = url
    return True

def play_playlist(name: str):
    global indice_atual
    nm = _resolver_nome_playlist_contextual(name)
    if not nm:
        return False
    data = _playlists_load()
    lst = data.get(nm)
    if not isinstance(lst, list) or not lst:
        print(f"⚠️ Playlist vazia ou inexistente: {nm}")
        return False
    _musica_estado_set("ultima_playlist", nm)
    playlist_state["name"] = nm
    playlist_state["index"] = 0
    indice_atual = 0
    playlist_state["user_intervened"] = False
    playlist_state["last_url"] = ""
    playlist_state.pop("shuffle", None)
    playlist_state.pop("shuffle_queue", None)
    playlist_state.pop("shuffle_index", None)
    first = lst[0]
    if isinstance(first, dict):
        url = str(first.get("url") or "")
        titulo = _yt_clean_title(str(first.get("titulo") or "")) or url
        canal = str(first.get("canal") or "")
    else:
        url = str(first)
        titulo = url
        canal = ""
    print(f"[PLAYLIST] Abrindo (Strong Reuse): {titulo} | Canal: {canal}")
    # ✅ NOVA CHAMADA FORTE (sempre mesma aba)
    validar_e_enviar_comando("youtube_play", {"url": url})
    playlist_state["last_url"] = url
    return True

def _executar_combo_modo_code(payload: dict):
    if payload.get("clean_tabs") or payload.get("clean_empty_tabs"):
        fechar_abas_vazias()
    img_topic = str(payload.get("image_topic") or "").strip()
    img_action = str(payload.get("image_action") or "").strip().lower()
    nf = str(payload.get("netflix_query") or payload.get("movie") or "").strip()
    if nf:
        executar_automacao_netflix(nf)
        return True
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
        'Campos permitidos: action, clean_tabs, music_query, netflix_query, image_topic, image_action.'
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
    # Remove formatação Markdown e outros caracteres indesejados
    texto = re.sub(r'\*\*|__|\*|_', '', texto)  # Negrito, itálico
    texto = re.sub(r'\n+', ' ', texto) # Quebras de linha
    texto = re.sub(r'\s+', ' ', texto).strip() # Espaços múltiplos
    texto = texto.replace('"', '') # Aspas duplas
    return texto

def extrair_exec_da_resposta(texto_bruto):
    """Extrai a fala e a lista de comandos, não importa o formato que a IA mandou."""
    fala = ""
    comandos = []

    try:
        # Tenta tratar como JSON primeiro
        if "{" in texto_bruto:
            match = re.search(r'\{.*\}', texto_bruto, re.DOTALL)
            if match:
                dados = json.loads(match.group(0))
                fala = dados.get("fala", "")
                comandos = dados.get("comandos", [])
        
        # Se falhou ou não achou JSON, tenta tratar o formato de Tupla ("fala", [comandos])
        if not fala and "(" in texto_bruto:
            # Remove parênteses externos e tenta separar por vírgula, mas só a primeira
            conteudo = texto_bruto.strip().strip("()")
            # Regex para pegar a string da fala e a lista de comandos separadamente
            match_tupla = re.search(r'["\'](.*?)["\']\s*,\s*(\[.*\])', conteudo, re.DOTALL)
            if match_tupla:
                fala = match_tupla.group(1)
                # Converte a string da lista em uma lista real de Python
                comandos_str = match_tupla.group(2).replace("'", '"') # Garante aspas duplas pro JSON
                comandos = json.loads(comandos_str)

    except Exception as e:
        print(f"⚠️ Erro na extração: {e}")
        # Fallback: se tudo der errado, limpa o lixo e fala o que sobrou
        fala = re.sub(r'\[.*?\]|\{.*?\}|\(.*?\)', '', texto_bruto).strip()
    
    return fala, comandos

def executar_comando(cmd: str, arg):
    c = str(cmd or "").strip().upper()
    a = "" if arg is None else str(arg).strip()

    SITE_MAP = {
        "noticias": "https://g1.globo.com",
        "notícia": "https://g1.globo.com",
        "tech": "https://www.tabnews.com.br",
        "tecnologia": "https://www.tabnews.com.br"
    }

    YT_CTRL = {
        "YT_PAUSE": "pause_play",
        "YT_PLAY": "pause_play",
        "YT_NEXT": "next",
        "YT_REPLAY": "replay",
        "YT_MUTE": "mute"
    }

    if c in YT_CTRL:
        enviar_comando_chrome("youtube_control", {"command": YT_CTRL[c]})
        return True

    if c == "OPEN_APP":
        if not a or len(a) < 2:
            return False
        print(f"🚀 Abrindo: {a}")
        if APP_OPENER_AVAILABLE:
            try:
                open_app(a, match_closest=True)
                return True
            except Exception as e:
                print(f"❌ Falha ao abrir app: {e}")
        return False
    
    if c == "CLOSE_TAB":
        target = str(arg or "").strip()
        alvo_norm = _normalizar_texto_com_apelidos(target).lower().strip()
        for app in sorted(APPS_MAP.keys(), key=len, reverse=True):
            if alvo_norm and (alvo_norm == app or app in alvo_norm):
                print(f"🧠 [CLOSE_TAB] Alvo parece app, fechando como programa → '{app}'")
                fechar_programa(APPS_MAP.get(app, target))
                return True
        if target and len(target) > 2:   # tem nome específico (Google Drive, YouTube, etc)
            print(f"🌐 [CLOSE_TAB] Fechando aba específica → '{target}'")
            validar_e_enviar_comando("close_specific_tab", {"target": target})
        else:
            print("🌐 [CLOSE_TAB] Fechando aba atual (sem alvo especificado)")
            validar_e_enviar_comando("close_current_tab", {})
        return True
    
    if c == "LER_EMAILS":
        emails_c = _gmail_nao_lidos_cache or _gmail_buscar_nao_lidos()
        _gmail_falar_resumo_estiloso(emails_c, somente_prioritarios=False)
        return True

    if c == "LER_EMAILS_URGENTES":
        emails_c = _gmail_nao_lidos_cache or _gmail_buscar_nao_lidos()
        prios = [e for e in emails_c if e["prioritario"]]
        _gmail_falar_resumo_estiloso(prios, somente_prioritarios=True)
        return True

    if c == "SINCRONIZAR_EMAILS":
        global _gmail_ultimo_check
        _gmail_ultimo_check = 0.0
        return True
            

    if c == "FECHAR_PROGRAMA":
        if not a or len(a) < 2: return False
        # Chama a função matadora que criamos!
        fechar_programa(a) 
        return True

    if c == "YOUTUBE":
            if not a: return False
            query = str(a).lower()
            
            # 🚀 FILTRO: Só adiciona "música" se NÃO for algo de utilidade/culinária
            termos_gerais = ["receita", "como fazer", "tutorial", "aula", "curso", "documentário", "notícia", "review", "culinária"]
            
            # Se for uma busca curta e não tiver termos de tutorial, reforçamos que é música
            if not any(t in query for t in termos_gerais):
                if len(query.split()) <= 3 and "música" not in query and "clipe" not in query:
                    query += " música oficial"
            
            print(f"🚀 [SISTEMA] Busca refinada para: {query}")
            enviar_comando_chrome("youtube_search", {"query": query})
            return True

    elif c == "YT_VOLUME":
        try:
            # Extrai o número do argumento (ex: '80%' vira 80)
            match = re.search(r'\d+', str(a))
            if not match:
                print(f"❌ Erro ao processar YT_VOLUME: Nenhum número encontrado em '{a}'")
                return False
            valor_video = int(match.group())
            print(f"🚀 [SISTEMA] Redirecionando YT_VOLUME para volume do sistema: {valor_video}%")
            
            # Alterado: Agora chama a função local em vez de enviar ao Chrome
            ajustar_volume_sistema(valor_video)
            return True
        except Exception as e:
            print(f"❌ Erro ao processar YT_VOLUME: {e}")
            return False

    if c == "NETFLIX":
        return executar_automacao_netflix(a)

    # ====================== CORREÇÃO PRINCIPAL ======================
    if c == "OPEN_SITE":
        if not a:
            return False
        raw = str(a).strip()

        # Se a IA já mandou uma URL completa de busca Google, usa direto
        if "google.com/search" in raw.lower() or raw.startswith("http"):
            url = raw if raw.startswith("http") else f"https://{raw}"
        else:
            # Caso contrário, usa a lógica antiga
            url = formatar_url_ou_busca(raw, prefer_com_br=False)

        print(f"🚀 [OPEN_SITE] Abrindo: {url}")
        enviar_comando_chrome("open_url", {"url": url})
        # Atualiza contexto para futuro auto-click
        try:
            ultimo_open_site["ts"] = time.time()
            ultimo_open_site["topic"] = raw
            ultimo_open_site["url"] = url
            _percepcao_set("ultimo_open_site", dict(ultimo_open_site))
        except Exception:
            pass
        return True

    if c == "BROWSE_SITE" or c == "SEARCH_WEB" or c == "GOOGLE":
        if not a:
            return False
        url = f"https://www.google.com/search?q={urllib.parse.quote(a)}&laylay_auto=true"
        enviar_comando_chrome("open_url", {"url": url, "auto_click": True})
        return True

    return False

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

def detectar_bordao_natural(user_input, messages):
    # Lógica para detectar e aprender bordões (mantida)
    pass # Implementação original aqui

def atualizar_emocao(messages, current_emotion, emotion_level):
    ctx = _obter_contexto_perceptivo()
    emocao_atual = str(current_emotion or ctx["emocao"] or "calma").strip()
    try:
        nivel_atual = int(emotion_level or ctx["nivel_emocao"] or 1)
    except Exception:
        nivel_atual = 1

    if ctx["humor"] <= -6:
        emocao_atual = "irritada"
        nivel_atual = max(nivel_atual, 2)
    elif ctx["humor"] >= 6:
        emocao_atual = "alegre"
        nivel_atual = max(nivel_atual, 2)
    elif ctx["periodo"] in {"madrugada", "noite"} and ctx["emocao"] in {"cansada", "triste"}:
        emocao_atual = "calma"
        nivel_atual = max(1, nivel_atual - 1)

    ultimo_texto = ""
    try:
        for item in reversed(messages or []):
            if isinstance(item, dict) and item.get("role") == "user":
                ultimo_texto = str(item.get("content") or "")
                break
    except Exception:
        ultimo_texto = ""

    ultimo_lower = _normalizar_texto_com_apelidos(ultimo_texto)
    if any(word in ultimo_lower for word in ["obrigado", "obrigada", "valeu", "vlw", "amei", "gostei", "lindo", "linda", "perfeito", "maravilhoso", "maravilhosa", "fofa", "fofo", "bonita", "bonito", "você é incrível", "voce e incrivel"]):
        if emocao_atual not in {"irritada", "brava"}:
            emocao_atual = "envergonhada"
            nivel_atual = max(nivel_atual, 2)

    return emocao_atual, nivel_atual

def gerar_system_prompt_com_deboque(bordoes, resumo_conversa, memoria_fatos, memoria_eventos, historico_long_term, current_emotion, emotion_level):
    ctx = _obter_contexto_perceptivo()
    base = [BASE_SYSTEM_PROMPT]
    base.append(
        "ESTADO MENTAL COMPARTILHADO: "
        f"periodo={ctx['periodo']} | "
        f"emocao={ctx['emocao']}({ctx['nivel_emocao']}) | "
        f"humor={ctx['humor']} | "
        f"topico={ctx['topico_ativo'] or 'nenhum'}"
    )
    if ctx["exe"] or ctx["title"] or ctx["assunto"]:
        base.append(
            "CONTEXTO VIVO: "
            f"app={ctx['exe'] or 'desconhecido'} | "
            f"janela={ctx['title'] or 'indefinida'} | "
            f"assunto={ctx['assunto'] or 'indefinido'}"
        )
    if ctx["logs_recentes"]:
        base.append("SINAIS RECENTES: " + " | ".join(ctx["logs_recentes"][-3:]))
    if ctx["rotina_atual"]:
        janelas = ctx["rotina_atual"].get("janelas") or []
        assuntos = ctx["rotina_atual"].get("assuntos") or []
        partes = []
        if janelas:
            partes.append("janelas=" + ", ".join(map(str, janelas[-3:])))
        if assuntos:
            partes.append("assuntos=" + ", ".join(map(str, assuntos[-3:])))
        if partes:
            base.append("ROTINA DO HORARIO: " + " | ".join(partes))
    if resumo_conversa:
        base.append(f"RESUMO CURTO: {resumo_conversa}")
    if historico_long_term:
        base.append(f"HISTORICO LONGO: {historico_long_term}")
    return "\n".join(base)

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
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return ""

    aliases_apps = {
        "steam": {"steam"},
        "opera": {"opera", "ópera", "operagx", "opera gx"},
        "vscode": {"vscode", "vs code", "visual studio code", "code"},
        "chrome": {"chrome", "google chrome"},
        "edge": {"edge", "msedge", "microsoft edge"},
        "brave": {"brave", "brave browser"},
        "firefox": {"firefox", "mozilla firefox"},
        "microsoft store": {"microsoft store", "ms store", "store", "loja microsoft"},
    }

    for app, aliases in aliases_apps.items():
        if any(alias in t for alias in aliases):
            return app
    return ""


def _resolver_comando_janela_contextual_forcado(texto: str):
    """Força continuidade de janela/app antes do fluxo livre da IA."""
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None

    app_explicito = _extrair_app_explicito_em_comando_janela(t)
    if app_explicito:
        _registrar_alvo_corrigido(app_explicito)
        if any(x in t for x in ["tela cheia", "fullscreen", "maximiza", "maximizar"]):
            return {"intent": "MAXIMIZE_WINDOW", "params": {"nome_app": app_explicito}}
        return {"intent": "APP_OPEN", "params": {"nome_app": app_explicito, "modo": "focus"}}

    if not any(x in t for x in ["ele", "ela", "isso", "esse", "essa"]):
        return None

    if not any(x in t for x in ["foco", "na frente", "pra frente", "para frente", "tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return None

    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}

    apps_sem_janela_contextual = {
        "microsoft store",
        "store",
        "ms store",
        "loja microsoft",
        "loja",
    }

    ultima_intencao_ctx = str(
        estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or ""
    ).strip().upper()
    ultimo_app = _alvo_corrigido_atual() or str(estado.get("ultimo_app_janela") or "").strip()
    if not ultimo_app and ultima_intencao_ctx in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        candidato = str(
            (estado.get("ultima_acao_params") or {}).get("nome_app")
            or (estado.get("ultima_acao_params") or {}).get("app")
            or ""
        ).strip()
        if _normalizar_texto_com_apelidos(candidato) not in apps_sem_janela_contextual:
            ultimo_app = candidato

    if not ultimo_app:
        return None

    if any(x in t for x in ["tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return {"intent": "MAXIMIZE_WINDOW", "params": {"nome_app": ultimo_app}}
    return {"intent": "APP_OPEN", "params": {"nome_app": ultimo_app, "modo": "focus"}}


def _responder_contexto_janela_indisponivel(texto: str) -> bool:
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return False
    if not any(x in t for x in ["ele", "ela", "isso", "esse", "essa"]):
        return False
    if not any(x in t for x in ["foco", "na frente", "pra frente", "para frente", "tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return False
    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}

    ultimo_site = str(estado.get("ultimo_site_aba") or "").strip()
    ultimo_app = str(estado.get("ultimo_app_janela") or "").strip()
    if ultimo_app:
        return False

    ultima_intencao_ctx = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    if ultima_intencao_ctx not in {"APP_OPEN", "OPEN_URL", "MAXIMIZE_WINDOW"} and not ultimo_site:
        return False

    alvo = ultimo_site or str((estado.get("ultima_acao_params") or {}).get("nome_app") or "").strip() or "isso"
    if any(x in t for x in ["tela cheia", "fullscreen", "maximiza", "maximizar"]):
        falar_com_lipsync(
            _escolher_fala_variada([
                f"{alvo} não me virou uma janela normal pra maximizar. Se quiser, me pede um app ou janela de verdade.",
                f"Isso abriu por outro caminho, então eu não tenho uma janela comum de {alvo} pra deixar em destaque.",
                f"Eu entendi o alvo, mas {alvo} não apareceu como janela normal pra eu colocar em tela cheia.",
            ]),
            "calma",
            1,
        )
        return True
    falar_com_lipsync(
        _escolher_fala_variada([
            f"Eu peguei a referência, mas {alvo} não virou uma janela comum pra eu focar.",
            f"Isso aí não apareceu como janela normal, então não deu pra puxar {alvo} pro foco.",
            f"Entendi o 'ele', só que {alvo} não me deu uma janela real pra trazer pra frente.",
        ]),
        "calma",
        1,
    )
    return True


def _resolver_comando_midia_contextual_forcado(texto: str):
    """Resolve comandos curtos de midia usando o contexto musical antes da conversa curta."""
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None

    t_limpo = re.sub(r"\b(?:h+m+|hmm+|hum+|ahn+|ah+|tipo|entao|então|agora|lay|laylay|por favor|pfv)\b", " ", t)
    t_limpo = re.sub(r"\s+", " ", t_limpo).strip()
    if not t_limpo:
        t_limpo = t

    contexto_musical = _contexto_musical_ativo()
    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}
    ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultima_habilidade = str(estado.get("ultima_habilidade") or "").strip().lower()
    ts_mente = float(estado.get("ts") or 0.0)
    midia_recente = (
        ultima_intencao == "MEDIA_CONTROL"
        or ultima_habilidade in {"midia", "musica", "playlist"}
    ) and (time.time() - ts_mente <= 240)
    referencia_contextual = any(x in t_limpo for x in ["ela", "ele", "isso", "essa", "esse", "anterior", "antes"])
    menciona_midia = any(x in t_limpo for x in ["musica", "música", "som", "faixa", "trilha", "youtube", "playlist"])
    if not (contexto_musical or menciona_midia or (referencia_contextual and midia_recente)):
        return None

    def _params(acao: str):
        params = {"acao": acao, "platform": "music"}
        if referencia_contextual:
            params["referencia_contextual"] = True
        return {"intent": "MEDIA_CONTROL", "params": params}

    # Ordem importa: "despausa" contem "pausa", entao vem primeiro.
    if any(x in t_limpo for x in ["toca ela de novo", "toca ele de novo", "toca isso de novo", "toca essa de novo", "recomeca", "recomeça", "reinicia a musica", "reinicia a música", "repete essa", "repete ela"]):
        print(f"🎵 [MIDIA:CONTEXTO] replay detectado -> '{t_limpo}'")
        return _params("replay")
    if any(x in t_limpo for x in ["despausa", "despausar", "depausa", "depausar", "retoma", "retomar", "continua tocando", "continua ela", "continua ele", "volta a tocar"]):
        print(f"🎵 [MIDIA:CONTEXTO] play detectado -> '{t_limpo}'")
        return _params("play")
    if any(x in t_limpo for x in ["pausa", "pausar", "pause", "para ela", "para ele", "para isso", "para a musica", "para música"]):
        print(f"🎵 [MIDIA:CONTEXTO] pause detectado -> '{t_limpo}'")
        return _params("pause")
    if "playlist" not in t_limpo and any(x in t_limpo for x in ["proxima", "próxima", "proximo", "próximo", "pula", "passa ela", "passa essa"]):
        print(f"🎵 [MIDIA:CONTEXTO] next detectado -> '{t_limpo}'")
        return _params("next")
    if any(x in t_limpo for x in ["musica anterior", "música anterior", "anterior", "volta ela", "volta essa", "volta a musica", "volta a música", "volta para a de antes", "volta pra de antes", "volta para a anterior", "volta pra anterior", "vai para a anterior"]):
        print(f"🎵 [MIDIA:CONTEXTO] prev detectado -> '{t_limpo}'")
        return _params("prev")
    return None


def _resolver_comando_arquivo_contextual_forcado(texto: str):
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None

    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}

    ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultima_habilidade = str(estado.get("ultima_habilidade") or "").strip().lower()
    ts_mente = float(estado.get("ts") or 0.0)
    if not (
        (ultima_intencao in {"CREATE_FOLDER", "DELETE_ITEM", "CREATE_FILE", "MOVE_ITEM"} or ultima_habilidade in {"arquivo", "arquivos"})
        and (time.time() - ts_mente <= 300)
    ):
        return None

    estrutura = _estrutura_arquivo_recente(900.0) or {}
    if not isinstance(estrutura, dict) or not estrutura:
        return None

    if any(p in t for p in [
        "traz ela de volta",
        "traz ele de volta",
        "traz isso de volta",
        "restaura isso",
        "restaura ela",
        "restaura ele",
        "refaz isso",
        "faz isso de novo",
        "cria de novo",
        "cria isso de novo",
        "faz de novo",
    ]):
        nome = str(estrutura.get("nome") or estrutura.get("pasta") or estrutura.get("alvo") or "").strip()
        if not nome:
            return None
        params = {"nome": nome}
        for chave in ["pasta_pai", "pasta_interna", "mover_item", "arquivo_nome", "arquivo_conteudo", "target"]:
            valor = estrutura.get(chave)
            if str(valor or "").strip():
                params[chave] = valor
        print(f"📁 [ARQUIVO:CONTEXTO] recriando estrutura -> '{nome}'")
        return {"intent": "CREATE_FOLDER", "params": params}

    return None


def _resolver_comando_acao_geral_contextual_forcado(texto: str):
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return None

    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}

    ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultimo_params = estado.get("ultima_acao_params") if isinstance(estado.get("ultima_acao_params"), dict) else {}
    if not ultima_intencao or not ultimo_params:
        return None

    try:
        ts_mente = float(estado.get("ts") or 0.0)
    except Exception:
        ts_mente = 0.0
    if not ts_mente or (time.time() - ts_mente > 300):
        return None

    pedido_de_volta = any(p in t for p in [
        "traz de volta",
        "traz ela de volta",
        "traz ele de volta",
        "traz isso de volta",
        "restaura isso",
        "restaura ela",
        "restaura ele",
        "abre de novo",
        "abre isso de novo",
        "abre ela de novo",
        "abre ele de novo",
        "coloca de novo",
        "bota de novo",
        "toca de novo",
        "quero isso de novo",
    ])
    pedido_fechar_ref = any(p in t for p in [
        "fecha ela",
        "fecha ele",
        "fecha isso",
        "fecha essa",
        "fecha esse",
        "fecha de novo",
        "fecha isso de novo",
        "fecha ela de novo",
        "fecha ele de novo",
    ])

    pedido_retomar_musica = any(p in t for p in [
        "coloca de novo",
        "coloca ela de novo",
        "coloca isso de novo",
        "bota de novo",
        "bota ela de novo",
        "toca de novo",
        "toca ela de novo",
    ])

    if not (pedido_de_volta or pedido_fechar_ref or pedido_retomar_musica):
        return None

    if pedido_retomar_musica and ultima_intencao in {"PLAYLIST_PLAY", "PLAYLIST_LIST", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE", "MEDIA_CONTROL", "MUSIC_SEARCH"}:
        nome_playlist = str(
            ultimo_params.get("nome_playlist")
            or ultimo_params.get("playlist")
            or _musica_estado_get("ultima_playlist")
            or ""
        ).strip()
        if nome_playlist:
            print(f"🧠 [CONTEXTO-GERAL] retomando playlist por repeticao natural -> '{nome_playlist}'")
            return {"intent": "PLAYLIST_PLAY", "params": {"nome_playlist": nome_playlist}}
        return {"intent": "MEDIA_CONTROL", "params": {"acao": "play", "platform": "music", "referencia_contextual": True}}

    if ultima_intencao in {"CLOSE_APP", "APP_OPEN", "MAXIMIZE_WINDOW"}:
        nome_app = str(
            ultimo_params.get("nome_app")
            or ultimo_params.get("app")
            or estado.get("ultimo_app_janela")
            or ""
        ).strip()
        if nome_app:
            if pedido_fechar_ref:
                print(f"🧠 [CONTEXTO-GERAL] fechando app por referencia -> '{nome_app}'")
                return {"intent": "CLOSE_APP", "params": {"nome_app": nome_app}}
            print(f"🧠 [CONTEXTO-GERAL] retomando app -> '{nome_app}'")
            return {"intent": "APP_OPEN", "params": {"nome_app": nome_app, "modo": "focus"}}

    if ultima_intencao in {"CLOSE_TAB", "OPEN_URL", "SITE_ENTER"}:
        alvo = str(
            ultimo_params.get("alvo")
            or ultimo_params.get("url")
            or estado.get("ultimo_site_aba")
            or ""
        ).strip()
        if alvo:
            if pedido_fechar_ref:
                print(f"🧠 [CONTEXTO-GERAL] fechando site por referencia -> '{alvo}'")
                return {"intent": "CLOSE_TAB", "params": {"alvo": alvo}}
            print(f"🧠 [CONTEXTO-GERAL] retomando site -> '{alvo}'")
            return {"intent": "OPEN_URL", "params": {"alvo": alvo}}

    if ultima_intencao in {"PLAYLIST_PLAY", "PLAYLIST_LIST", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE"}:
        nome_playlist = str(
            ultimo_params.get("nome_playlist")
            or ultimo_params.get("playlist")
            or _musica_estado_get("ultima_playlist")
            or ""
        ).strip()
        if nome_playlist:
            if pedido_fechar_ref:
                return {"intent": "MEDIA_CONTROL", "params": {"acao": "pause", "platform": "music", "referencia_contextual": True}}
            print(f"🧠 [CONTEXTO-GERAL] retomando playlist -> '{nome_playlist}'")
            return {"intent": "PLAYLIST_PLAY", "params": {"nome_playlist": nome_playlist}}

    return None


def _resolver_comando_contextual_forcado(texto: str):
    candidatos = [
        ("JANELA", _resolver_comando_janela_contextual_forcado),
        ("MIDIA", _resolver_comando_midia_contextual_forcado),
        ("ARQUIVO", _resolver_comando_arquivo_contextual_forcado),
        ("GERAL", _resolver_comando_acao_geral_contextual_forcado),
    ]
    for rota, resolver in candidatos:
        try:
            resultado = resolver(texto)
        except Exception as e:
            print(f"⚠️ [CONTEXTO-{rota}] falha ao resolver: {e}")
            continue
        if isinstance(resultado, dict) and str(resultado.get("intent") or "").strip():
            saida = dict(resultado)
            saida["_rota_contextual"] = rota
            return saida
    return None


def _usar_modo_rapido_conversa(texto: str) -> bool:
    """Decide se a conversa pode responder com um contexto leve."""
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return True

    if interpretar_comando_local_rapido(t):
        return False
    if _resolver_comando_midia_contextual_forcado(t):
        return False

    palavras_pesadas = [
        "playlist", "arquivo", "pasta", "download", "chrome", "opera", "vscode",
        "janela", "aba", "tela cheia", "fullscreen", "youtube", "netflix",
        "música", "musica", "memória", "memoria", "lembra", "aprendeu",
        "foco", "maximiza", "maximizar", "fecha", "abre", "abre o", "abre a",
        "pausa", "despausa", "retoma", "proxima", "próxima", "anterior",
    ]
    if any(p in t for p in palavras_pesadas):
        return False

    if len(t) <= 90:
        return True

    return False


def _texto_pede_direcao_musical_generica(texto: str) -> bool:
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return False
    if any(p in t for p in [
        "nao tenho ouvido antes", "não tenho ouvido antes",
        "nao ouvi antes", "não ouvi antes",
        "uma que nao ouvi", "uma que não ouvi",
        "uma nova", "musica nova", "música nova",
    ]):
        try:
            estado = dict(mente_integrada_estado or {})
            if str(estado.get("ultima_habilidade") or "").lower() == "musica":
                return True
        except Exception:
            pass
    pede_escolha = any(p in t for p in [
        "recomenda", "recomendacao", "recomendação", "me indica", "indica uma",
        "sugere", "sugestao", "sugestão", "escolhe uma", "escolha uma",
        "me lista", "me liste", "lista musicas", "liste musicas",
        "me fale uma musica", "me fala uma musica", "me diga uma musica",
        "qual voce acha", "qual você acha", "voce acha que eu gostaria", "você acha que eu gostaria",
    ])
    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}
    continuacao_musical = (
        str(estado.get("ultima_intencao") or "").upper() == "MUSIC_OPINION_CHAT"
        and any(p in t for p in ["entao me fala", "então me fala", "me fala entao", "me fala então", "entao diz", "então diz", "me diz uma", "fala uma", "entao manda", "então manda"])
    )
    assunto_musical = any(p in t for p in [
        "musica", "música", "som", "faixa", "canção", "cancao", "ouvir", "tocar",
    ])
    return bool((pede_escolha and assunto_musical) or continuacao_musical)


def _sugestao_musical_nova_conversacional(texto: str = "") -> str:
    """Palpite conversacional: nao usa playlists do Pedro e nao executa nada."""
    t = _normalizar_texto_com_apelidos(texto)
    base = {
        "rock": [
            "Scalene - Surreal",
            "Supercombo - Piloto Automatico",
            "Far From Alaska - Thievery",
            "Vivendo do Ocio - Nostalgia",
        ],
        "pesado": [
            "Black Pantera - Fogo nos Racistas",
            "Project46 - Erro +55",
            "Sepultura - Roots Bloody Roots",
            "Surra - Bom Dia Senhor",
        ],
        "alternativo": [
            "Boogarins - Lucifernandis",
            "Terno Rei - Yoko",
            "Carne Doce - Artemisia",
            "Maglore - Mantra",
        ],
        "calmo": [
            "Tim Bernardes - Recomeçar",
            "Rubel - Quando Bate Aquela Saudade",
            "Cicero - Tempo de Pipa",
            "Ana Frango Eletrico - Electric Fish",
        ],
        "anime": [
            "Eve - Kaikai Kitan",
            "Aimer - Brave Shine",
            "TK from Ling tosite sigure - Unravel",
            "Asian Kung-Fu Generation - Rewrite",
        ],
        "madrugada": [
            "Boogarins - Infinu",
            "Terno Rei - Solidão de Volta",
            "Tagua Tagua - Inteiro Metade",
            "Glue Trip - Elbow Pain",
        ],
    }
    if any(p in t for p in ["pesad", "metal", "hard", "porrada"]):
        chave = "pesado"
    elif any(p in t for p in ["alternativ", "diferente", "estranh", "indie"]):
        chave = "alternativo"
    elif any(p in t for p in ["calm", "leve", "dormir", "relax"]):
        chave = "calmo"
    elif any(p in t for p in ["anime", "jap", "opening", "ost"]):
        chave = "anime"
    elif any(p in t for p in ["madrugada", "noite", "brisa"]):
        chave = "madrugada"
    elif "rock" in t:
        chave = "rock"
    else:
        chave = random.choice(list(base.keys()))
    return random.choice(base.get(chave) or base["alternativo"])


def _responder_pedido_direcao_musical_generica(texto: str = "") -> bool:
    t = _normalizar_texto_com_apelidos(texto)
    quer_nova = any(p in t for p in [
        "nao tenho ouvido antes", "não tenho ouvido antes",
        "nao ouvi antes", "não ouvi antes",
        "uma que nao ouvi", "uma que não ouvi",
        "uma nova", "musica nova", "música nova",
    ])
    sugestao = _sugestao_musical_nova_conversacional(t)
    if quer_nova:
        fala = random.choice([
            f"Então eu arrisco uma fora da tua prateleira: {sugestao}. Não toquei nada, só tô te dando um palpite novo.",
            f"Beleza, sem reciclar playlist. Meu chute com coragem é {sugestao}. Se quiser outro clima, eu viro a esquina.",
            f"Uma nova pra testar teu ouvido: {sugestao}. Pode ser que bata, pode ser que apanhe, mas é uma aposta honesta.",
        ])
    else:
        fala = random.choice([
            f"Eu iria de {sugestao}. Não veio da tua playlist; é um palpite meu pra você testar.",
            f"Minha aposta agora é {sugestao}. Se não bater, eu troco o tempero sem drama.",
            f"Vou te jogar uma nova na mesa: {sugestao}. Não executei nada, só recomendei mesmo.",
            f"Tá, eu arrisco: {sugestao}. Tem cara de música que pode te pegar de lado.",
        ])
    falar_com_lipsync(
        fala,
        "calma",
        1,
    )
    _registrar_mente_curta(
        texto,
        fala,
        intencao="MUSIC_OPINION_CHAT",
        alvo=sugestao,
        habilidade="musica",
    )
    return True


def _processar_confirmacao_sugestao_musical(texto: str = "") -> bool:
    """Continua uma recomendacao conversacional sem recriar a habilidade antiga."""
    t = _normalizar_texto_com_apelidos(texto)
    if not t:
        return False
    if any(p in t for p in ["nao", "não", "outra", "diferente", "nao gostei", "não gostei"]):
        return False

    confirma = any(p in t for p in [
        "quero ouvir", "quero escutar", "quero sim", "quero ver",
        "pode ser", "pode colocar", "pode tocar", "coloca", "toca",
        "manda", "bora", "vai nessa", "essa mesmo", "essa aí", "essa ai",
    ])
    pedir_entrega = any(p in t for p in [
        "entao me fala", "então me fala", "me fala entao", "me fala então",
        "me diga", "me diz", "fala uma", "me da outra", "me dá outra",
    ])
    if not (confirma or pedir_entrega):
        return False

    try:
        estado = dict(mente_integrada_estado or {})
    except Exception:
        estado = {}
    if str(estado.get("ultima_intencao") or "").upper() != "MUSIC_OPINION_CHAT":
        return False
    if str(estado.get("ultima_habilidade") or "").lower() != "musica":
        return False
    try:
        if time.time() - float(estado.get("ts") or 0.0) > 420:
            return False
    except Exception:
        return False

    sugestao = str(estado.get("ultimo_alvo") or "").strip()
    if not sugestao or _normalizar_texto_com_apelidos(sugestao) in {"musica_nova", "musica", "música"}:
        return False

    if pedir_entrega and not confirma:
        fala = random.choice([
            f"Então toma: {sugestao}. Essa foi a que eu escolhi pra você agora.",
            f"Tá, sem enrolar: {sugestao}. Essa é minha aposta do momento.",
            f"Fechado. A música que eu tô te indicando é {sugestao}.",
        ])
        _registrar_mente_curta(
            texto,
            fala,
            intencao="MUSIC_OPINION_CHAT",
            alvo=sugestao,
            habilidade="musica",
        )
        falar_com_lipsync(fala, "calma", 1)
        return True

    resultado = {"intent": "MUSIC_SEARCH", "params": {"query": sugestao, "origem": "sugestao_conversacional"}}
    print(f"⚡ [ROTEADOR SUGESTAO-MUSICAL [chat]] {resultado}")
    texto_execucao = f"toca {sugestao}"
    executou = bool(executar_intencao(resultado, texto_execucao))
    _registrar_resultado_execucao(resultado, texto, executou, origem="confirmacao_sugestao_musical")
    if executou:
        _registrar_mente_curta(
            texto,
            f"Colocando {sugestao} pra tocar.",
            intencao="MUSIC_SEARCH",
            alvo=sugestao,
            habilidade="musica",
        )
        try:
            _registrar_autoaprimoramento(resultado, texto, True, contexto="confirmacao de sugestao musical", origem="chat")
        except Exception as e_auto:
            print(f"⚠️ [AUTOAPRENDIZADO] falha ao registrar sugestao musical: {e_auto}")
    return executou


def processar_comandos_imediatos(texto: str) -> bool:
    contexto = {
        "_normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
        "_texto_social_curto": _texto_social_curto,
        "_texto_conversa_casual_sem_acao": _texto_conversa_casual_sem_acao,
        "_refinar_contexto_mental": _refinar_contexto_mental,
        "_resolver_comando_janela_contextual_forcado": _resolver_comando_janela_contextual_forcado,
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

def _confirmar_execucao_com_emocao(texto_usuario, system_msg, emotion, level):
    global messages
    messages.append({"role": "user", "content": texto_usuario})
    confirma = list(messages)
    confirma.append({"role": "system", "content": system_msg})
    bot_raw = enviar_mensagem(confirma, _com_tools=False)
    bot = _remover_prefixo_exec(limpar_resposta(bot_raw))
    if bot:
        print(f"Laylay [{emotion} lvl{level}]: {bot}")
        messages.append({"role": "assistant", "content": bot})
        falar_com_lipsync(bot, emotion, level)
        memoria_inteligente.adicionar_interacao(texto_usuario, bot)   # ← corrigido
        salvar_memoria()

def _extrair_json_da_ia(texto: str) -> str:
    s = str(texto or "").strip()
    if not s:
        return ""
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\s*```$", "", s)
        s = s.strip()
    i = s.find("{")
    j = s.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return ""
    return s[i : j + 1].strip()

def analisar_intencao(texto: str):
    global messages
    t = (texto or "").strip()
    if not t:
        return None
    if _texto_cancela_acao_agora(t):
        return {"intent": "CANCELAR_ACAO", "params": {}}
    if _texto_bloqueia_playlist_agora(t):
        return None
    if _texto_social_curto(t):
        return None
    t_corrigido = _normalizar_texto_com_apelidos(t)
    mente = dict(mente_integrada_estado or {})
    contexto_playlist = {}
    try:
        contexto_playlist = {
            "ultima_playlist": _musica_estado_get("ultima_playlist"),
            "playlist_ativa": str(playlist_state.get("name") or "").strip(),
            "ultima_url_playlist": str(playlist_state.get("last_url") or "").strip(),
        }
    except Exception:
        contexto_playlist = {"ultima_playlist": _musica_estado_get("ultima_playlist")}
    hist = []
    try:
        for m in (messages or [])[-12:]:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "")
            if role not in {"user", "assistant"}:
                continue
            content = str(m.get("content") or "").strip()
            if content:
                hist.append({"role": role, "content": content[:400]})
    except Exception:
        hist = []

    prompt = (
        "Você é o cérebro da assistente Laylay. Analise a frase do usuário e retorne apenas um JSON válido com:\n"
        "intent: (PLAYLIST_ADD, PLAYLIST_PLAY, PLAYLIST_LIST, LAYLAY_PLAYLIST_LIST, LAYLAY_PLAYLIST_COPY, MEDIA_CONTROL, CANCELAR_ACAO, CLOSE_TAB, CLOSE_APP, APP_OPEN, OPEN_URL, MAXIMIZE_WINDOW, VOLUME, NETFLIX, MUSIC_SEARCH, SITE_ENTER, SEARCH, WEATHER, CREATE_FOLDER, DELETE_ITEM, LISTAR_PLAYLISTS, TOCAR_PLAYLIST, TOCAR_PLAYLIST_SHUFFLE, AGENDAR_LEMBRETE, LISTAR_AGENDAMENTOS, CANCELAR_AGENDAMENTO)\n"
        "params: (dicionário com nome_playlist, nome_app, nivel_volume, query, acao, etc)\n"
        "Regras:\n"
        "- Retorne SOMENTE o JSON (sem markdown, sem texto extra).\n"
        "- Corrija mentalmente erros leves de pronuncia, transcricao e ortografia antes de decidir a intencao.\n"
        "- Trate apelidos ensinados como equivalentes do nome real quando fizer sentido.\n"
        "- Use a memória curta da mente inteira quando a frase estiver incompleta. Se houver um alvo recente, reutilize-o quando fizer sentido.\n"
        "- Saudações, agradecimentos, risadas e conversa social curta NUNCA viram playlist, música, site, arquivo ou comando por causa de contexto antigo.\n"
        "- Se a frase depender do contexto recente, do que foi dito agora pouco ou de um alvo implícito, interprete isso como continuidade do mesmo cérebro e não como um pedido fragmentado.\n"
        "- Use a memória de curto prazo da última playlist real quando o assunto atual for música e o usuário disser coisas como 'coloca essa também' e não citar playlist.\n"
        "- Se o assunto atual for email, agenda, notificação ou sistema, ignore pistas musicais antigas como ultima_playlist, playlist_ativa ou ultima_url_playlist.\n"
        "- Ao listar playlists, use as playlists que estão no contexto 'playlists_disponiveis'.\n"
        "- Música e playlist NUNCA devem ser executadas só por rotina antiga, ultima_playlist ou padrão aprendido. Para tocar algo, precisa haver pedido atual claro do usuário ou confirmação clara de uma sugestão recém-feita.\n"
        "- Em começo de conversa, saudações e perguntas sobre bem-estar, não ofereça nem execute playlist. Responda como conversa normal.\n"
        "- Se o bem-estar do Pedro sugerir música, no máximo pergunte antes; nunca toque sem confirmação.\n"
        "- Se o usuário pedir para colocar um app em foco, maximizar, tela cheia ou trazer para frente, trate como APP_OPEN/MAXIMIZE, nunca como SEARCH nem como OPEN_SITE.\n"
        "- Frases como 'coloca o Opera em foco', 'deixa o Opera em tela cheia', 'maximiza o Opera' devem virar foco da janela do Opera, não pesquisa no navegador.\n"
        "- Frases como 'deixa o Opera em foco' ou 'coloca ele em tela cheia' NÃO são cancelamento; são comando de janela.\n"
        "- Se o usuário pedir para fechar um programa real, como Steam, Opera, VS Code ou Spotify, prefira CLOSE_APP.\n"
        "- Se o usuário pedir para fechar aba, site ou janela do navegador, prefira CLOSE_TAB.\n"
        "- Se o usuário pedir para abrir um site conhecido, URL, domínio ou destino web explícito, use OPEN_URL.\n"
        "- Para playlist, site e foco de janela, interprete a frase inteira e o contexto recente antes de decidir; não use apenas um verbo ou um nome isolado como gatilho principal.\n"
        "- Se o usuário estiver pedindo para TOCAR/COLOCAR música ou pedindo um gênero/artista (ex: 'coloca um rock', 'coloque uma música de rock', 'coloca rock no youtube'), a intenção OBRIGATÓRIA é MUSIC_SEARCH com params.query.\n"
        "- Se o usuário pedir recomendação musical vaga, como 'me recomenda uma música' ou 'tem alguma música para me recomendar?', NÃO use MUSIC_SEARCH. Isso é conversa/pergunta vaga, não comando para tocar ou buscar.\n"
        "- Para MUSIC_SEARCH, NUNCA use Google; o destino é sempre YouTube.\n"
        "- Se a frase curta bater com o nome de uma playlist salva, só trate como PLAYLIST_PLAY se houver verbo atual de ação como tocar, colocar, abrir, ouvir ou se a Laylay acabou de perguntar qual playlist.\n"
        "- Se a frase mencionar 'playlist' e o usuário estiver perguntando 'quais', 'o que tem', 'mostra', 'lista', a intenção OBRIGATÓRIA é PLAYLIST_LIST com params.nome_playlist (ou use a última playlist real se não houver nome explícito).\n"
        "- Se a frase mencionar 'playlist', NUNCA retorne SEARCH (Google) para isso.\n"
        "- Se a frase for uma desistência explícita como 'deixa pra lá', 'esquece', 'cancela', 'não quero mais' ou 'para com isso', use CANCELAR_ACAO e limpe a intenção anterior.\n"
        "- Se a mensagem for curta e depender do que acabou de acontecer, use o contexto recente. Um 'essa aqui também' depois de um pedido de música deve virar PLAYLIST_ADD ou MUSIC_SEARCH, conforme o contexto.\n"
        "- Só use continuação musical quando a frase atual ainda apontar para música, playlist, tocar, salvar ou 'essa também'. Nunca use ultima_playlist para cumprimentos como 'oi lay' ou 'como você está?'.\n"
        "- Se o usuário disser algo como 'coloca a playlist anime', 'coloca a playlist kamai' ou 'toca a playlist brisa da madrugada', interprete como PLAYLIST_PLAY da playlist pedida ou do apelido conhecido, nunca como criação de pasta, arquivo ou resposta de conversa genérica.\n"
        "- Nunca invente pasta, pasta de músicas ou estrutura de arquivos quando o assunto for playlist, música, artista ou apelido musical.\n"
        "- Se o usuário pedir para lembrar algo em um horário ou daqui a alguns minutos, use AGENDAR_LEMBRETE com minutos ou hora_alvo e descreva o compromisso em descricao.\n"
        "- Se o usuário perguntar se tem compromisso, agenda, lembretes ou algo marcado, use LISTAR_AGENDAMENTOS.\n"
        "- Se o usuário pedir para cancelar um compromisso/lembrete, use CANCELAR_AGENDAMENTO com o alvo informado.\n"
        "- Se o usuário pedir para apagar, deletar, remover ou excluir uma pasta/arquivo, use DELETE_ITEM com params.alvo contendo só o nome real do item, não a frase inteira.\n"
        "- Em pedidos compostos como 'apaga a pasta roberto e dentro dela um arquivo...', DELETE_ITEM deve mirar a pasta 'roberto', porque apagar a pasta remove o conteúdo junto.\n"
        "- Se houver memória de autoaprimoramento indicando que uma habilidade já falhou ou teve correção recente, prefira o padrão que já funcionou melhor e evite repetir o caminho que errou.\n"
        "- Se a frase for do tipo 'entra em um site de X', 'entra no site de X', 'vai para um site de X', 'abre algo de X', a intenção OBRIGATÓRIA é SITE_ENTER com params.tema.\n"
        "- SITE_ENTER deve abrir uma busca no Google e clicar no primeiro resultado orgânico (sem anúncios).\n"
        "- Se o usuário pedir para fechar uma aba/site/janela (ex: 'fecha essa aba', 'mata essa janela', 'derruba o site'), a intenção OBRIGATÓRIA é CLOSE_TAB.\n"
        "- Se o usuário pedir para falar, ler, resumir, checar ou explicar emails, use EMAIL_READ ou EMAIL_SYNC conforme o caso; não transforme isso em conversa genérica.\n"
        "- Se o usuário reclamar de um remetente, notificação, email chato ou algo como 'manda X calar a boca', interprete o tom da brincadeira e converta em uma ação útil, como NOTIFICATIONS com silenciar_remetente ou EMAIL_READ/EMAIL_SYNC quando fizer sentido.\n"
        "- Se o usuário perguntar temperatura, clima, quantos graus está, se vai chover, ou como está o tempo em uma cidade, a intenção OBRIGATÓRIA é WEATHER com params.local.\n"
        "- Se o usuário pedir para ver suas playlists da Laylay, sua playlist, playlist dela ou playlists dela, use LAYLAY_PLAYLIST_LIST.\n"
        "- Se o usuário pedir para colocar uma música da playlist da Laylay em uma playlist dele, use LAYLAY_PLAYLIST_COPY com musica, origem e destino.\n"
        "- SEARCH é apenas para perguntas de fatos/explicações; se não tiver certeza, escolha SEARCH com params.query.\n"
        "- A decisão deve vir de uma única mente: use contexto, memória curta, rotina, humor, emoção, atividade atual e percepção viva como um retrato integrado, não como módulos separados.\n"
        "- Quando houver conflito entre sinais, priorize o sinal mais recente, o mais concreto e o que melhor encaixa no padrão aprendido da mesma mente.\n"
        "Exemplos:\n"
        "Usuário: 'coloca um rock' -> {\"intent\":\"MUSIC_SEARCH\",\"params\":{\"query\":\"rock\"}}\n"
        "Usuário: 'coloca rock no youtube' -> {\"intent\":\"MUSIC_SEARCH\",\"params\":{\"query\":\"rock\"}}\n"
        "Usuário: 'coloca essa também' (com música recente no contexto) -> {\"intent\":\"PLAYLIST_ADD\",\"params\":{\"nome_playlist\":\"playlist_recentemente_usada\"}}\n"
        "Usuário: 'coloca essa música na playlist kamai' (apelido já ensinado) -> {\"intent\":\"PLAYLIST_ADD\",\"params\":{\"nome_playlist\":\"kamaitachi\"}}\n"
        "Usuário: 'coloca a brisa da madrugada' (playlist salva com esse nome) -> {\"intent\":\"PLAYLIST_PLAY\",\"params\":{\"nome_playlist\":\"brisa da madrugada\"}}\n"
        "Usuário: 'coloca o Opera em foco' -> {\"intent\":\"APP_OPEN\",\"params\":{\"nome_app\":\"opera\"}}\n"
        "Usuário: 'deixa o Opera em tela cheia' -> {\"intent\":\"APP_OPEN\",\"params\":{\"nome_app\":\"opera\",\"modo\":\"fullscreen\"}}\n"
        "Usuário: 'abre o Opera' -> {\"intent\":\"APP_OPEN\",\"params\":{\"nome_app\":\"opera\"}}\n"
        "Usuário: 'fecha a Steam' -> {\"intent\":\"CLOSE_APP\",\"params\":{\"nome_app\":\"steam\"}}\n"
        "Usuário: 'fecha o site do ifood' -> {\"intent\":\"CLOSE_TAB\",\"params\":{\"alvo\":\"ifood\"}}\n"
        "Usuário: 'entra no instagram' -> {\"intent\":\"OPEN_URL\",\"params\":{\"alvo\":\"instagram\"}}\n"
        "Usuário: 'quais músicas tem na playlist rock?' -> {\"intent\":\"PLAYLIST_LIST\",\"params\":{\"nome_playlist\":\"rock\"}}\n"
        "Usuário: 'Laylay, assiste esse' (na Netflix) -> {\"intent\":\"MEDIA_CONTROL\",\"params\":{\"platform\":\"netflix\",\"acao\":\"enter\"}}\n"
        "Usuário: 'entra num site de comida' -> {\"intent\":\"SITE_ENTER\",\"params\":{\"tema\":\"comida\"}}\n"
        "Usuário: 'entra nesse site' (com site recente no contexto) -> {\"intent\":\"OPEN_URL\",\"params\":{\"alvo\":\"contexto_anterior\"}}\n"
        "Usuário: 'fecha essa aba' -> {\"intent\":\"CLOSE_TAB\",\"params\":{}}\n"
        "Usuário: 'me fale dos emails' -> {\"intent\":\"EMAIL_READ\",\"params\":{}}\n"
        "Usuário: 'o que eles me falam?' (sobre emails recentes no contexto) -> {\"intent\":\"EMAIL_READ\",\"params\":{}}\n"
        "Usuário: 'quantos graus tá em Boituva?' -> {\"intent\":\"WEATHER\",\"params\":{\"local\":\"Boituva\"}}\n"
        "Usuário: 'como está o clima em Sorocaba?' -> {\"intent\":\"WEATHER\",\"params\":{\"local\":\"Sorocaba\"}}\n"
        "Usuário: 'me mostra sua playlist' -> {\"intent\":\"LAYLAY_PLAYLIST_LIST\",\"params\":{}}\n"
        "Usuário: 'coloca a música x da sua playlist y na minha playlist z' -> {\"intent\":\"LAYLAY_PLAYLIST_COPY\",\"params\":{\"musica\":\"x\",\"origem\":\"y\",\"destino\":\"z\"}}\n"
        "Usuário: 'quem é o presidente?' -> {\"intent\":\"SEARCH\",\"params\":{\"query\":\"quem é o presidente\"}}\n"
        "Usuário: 'me lembra de 12:30 ir para o senai' -> {\"intent\":\"AGENDAR_LEMBRETE\",\"params\":{\"hora_alvo\":\"12:30\",\"descricao\":\"ir para o senai\"}}\n"
        "Usuário: 'tenho algum compromisso hoje?' -> {\"intent\":\"LISTAR_AGENDAMENTOS\",\"params\":{}}\n"
        "Usuário: 'apaga a pasta chamada roberto e dentro dela um arquivo de texto chamado antonio' -> {\"intent\":\"DELETE_ITEM\",\"params\":{\"alvo\":\"roberto\",\"tipo\":\"pasta\"}}\n"
        "Usuário: 'deixa pra lá' -> {\"intent\":\"CANCELAR_ACAO\",\"params\":{}}\n"
    )
    payload = {
        "texto_original": t,
        "texto_corrigido": t_corrigido,
        "retrato_mente_integrada": _resumo_mente_integrada_para_prompt(t),
        "contexto_conversas": {
            **contexto_playlist,
            "mente_curta": mente,
            "autoaprimoramento": _resumo_autoaprimoramento_para_prompt(limit=6),
            "agendamentos_ativos": _resumo_agendamentos_para_prompt(limit=6),
            "historico": hist,
            "playlists_disponiveis": list(playlists_carregadas.keys()),
        },
    }
    raw = enviar_mensagem([
        {"role": "system", "content": prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ], _com_tools=False, max_tokens=140, modo_rapido=True)
    js = _extrair_json_da_ia(raw)
    if not js:
        return None
    try:
        data = json.loads(js)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    intent_ia = str(data.get("intent") or "").upper().strip()
    if intent_ia == "CANCELAR_ACAO" and not _texto_cancela_acao_agora(t):
        return None
    if _playlist_bloqueada_agora() and intent_ia in {"PLAYLIST_ADD", "PLAYLIST_PLAY", "PLAYLIST_LIST", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE"}:
        if not _texto_pede_playlist_explicitamente(t):
            print("🎵 [PLAYLIST] Intenção musical bloqueada: contexto antigo tentou puxar playlist.")
            return None
    return data


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
        "ajustar_volume_sistema": ajustar_volume_sistema,
        "ajustar_volume_sistema_relativo": ajustar_volume_sistema_relativo,
        "solicitar_aba_ativa": solicitar_aba_ativa,
        "executar_netflix_perfil": executar_netflix_perfil,
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
    if not nome:
        return None

    nome_norm = nome.lower()
    if nome_norm in SITES_DIRECTOS or nome_norm.startswith("site ") or nome_norm in {"youtube", "google", "netflix", "spotify", "whatsapp", "chatgpt"}:
        site = nome_norm.replace("site ", "").strip()
        return {"intent": "OPEN_URL", "params": {"alvo": site}}

    candidatos = sorted(APPS_MAP.keys(), key=len, reverse=True)
    for app in candidatos:
        if nome_norm == app or nome_norm.startswith(app + " ") or app in nome_norm:
            return {"intent": "APP_OPEN", "params": {"nome_app": app}}

    return {"intent": "APP_OPEN", "params": {"nome_app": nome}}

def _segmentar_comandos_em_cadeia(texto: str) -> list:
    bruto = str(texto or "").strip()
    if not bruto:
        return []

    t = _normalizar_texto(bruto)
    t = re.sub(r"[,\.\!\?\:\;]+", " ", t)
    t = re.sub(r"\b(laylay|lay|por favor|pfv)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []

    for sep in (r"\be depois\b", r"\bem seguida\b", r"\bdepois\b", r"\bent[aã]o\b"):
        partes = re.split(sep, t, maxsplit=1)
        if len(partes) > 1:
            partes = [p.strip() for p in partes if p and p.strip()]
            if len(partes) > 1:
                return partes[:2]

    return [t]

def _executar_comando_em_texto(texto: str, origem: str = "") -> bool:
    t = (texto or "").strip()
    if not t:
        return False

    if _detectar_repetir_briefing(t):
        repetir_briefing()
        return True

    if processar_comando_deterministico(t, origem):
        return True

    comando_local = interpretar_comando_local_rapido(t)
    if comando_local:
        try:
            return bool(executar_intencao(comando_local, t))
        except Exception as e:
            print(f"⚠️ [COMANDO LOCAL] falha ao executar: {e}")
            return False

    return False

def processar_comandos_em_cadeia(texto: str, origem: str = "") -> bool:
    partes = _segmentar_comandos_em_cadeia(_normalizar_texto_com_apelidos(texto))
    if len(partes) < 2:
        return False

    executou_algum = False
    tag = origem or "cadeia"
    for idx, parte in enumerate(partes[:2], start=1):
        if _executar_comando_em_texto(parte, f"{tag}-{idx}"):
            executou_algum = True

    return executou_algum


def _extrair_criacao_pasta_arquivo(frase: str) -> dict:
    texto_local = re.sub(r"\s+", " ", str(frase or "").strip())
    if not texto_local:
        return {}

    combo_escreve = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?dentro(?:\s+dela|\s+da\s+pasta)?\s+"
        r"(?:um\s+|uma\s+)?arquivo(?:\s+de\s+texto)?\s+"
        r"(?:chamado|chamada|chamadda|com nome)?\s*(?P<arquivo>.+?)\s+"
        r"escreve\s+(?P<conteudo>.+)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if combo_escreve:
        pasta = str(combo_escreve.group("pasta") or "").strip(" .,!?:;\"'")
        arquivo = str(combo_escreve.group("arquivo") or "").strip(" .,!?:;\"'")
        conteudo = str(combo_escreve.group("conteudo") or "").strip(" .,!?:;\"'")
        if pasta and arquivo:
            return {"nome": pasta, "arquivo_nome": arquivo, "arquivo_conteudo": conteudo}

    mover_para_dentro = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?(?:dentro\s+dela\s+)?(?:coloca|mova|move|mover)\s+"
        r"(?:a|uma)?\s*pasta\s+(?P<mover>.+?)(?:\s+dentro(?:\s+dela|\s+da\s+pasta)?)?$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if mover_para_dentro:
        pasta = str(mover_para_dentro.group("pasta") or "").strip(" .,!?:;\"'")
        mover = str(mover_para_dentro.group("mover") or "").strip(" .,!?:;\"'")
        if pasta and mover:
            return {"nome": pasta, "mover_item": mover}

    nested_folder = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?dentro(?:\s+dela|\s+da\s+pasta)?\s*(?:coloca|cria|criar|crie)\s+"
        r"(?:a|uma)?\s*pasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<interna>.+?)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if nested_folder:
        pasta = str(nested_folder.group("pasta") or "").strip(" .,!?:;\"'")
        interna = str(nested_folder.group("interna") or "").strip(" .,!?:;\"'")
        if pasta and interna:
            return {"nome": pasta, "pasta_interna": interna}

    combo = re.search(
        r"\b(?:cria|criar|crie)\b.*?\bpasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(?P<pasta>.+?)\s+"
        r"(?:e\s+)?(?:dentro(?:\s+dela|\s+da\s+pasta)?\s*)?(?:coloca|cria|criar|crie)?\s*"
        r"(?:um\s+|uma\s+)?arquivo(?:\s+de\s+texto)?\s+"
        r"(?:chamado|chamada|chamadda|com nome)?\s*(?P<arquivo>.+?)"
        r"(?:\s+(?:escrito(?:\s+nele)?|com\s+o\s+texto|com\s+texto|contendo|que\s+diga)\s+(?P<conteudo>.+))?$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if combo:
        pasta = str(combo.group("pasta") or "").strip(" .,!?:;\"'")
        arquivo = str(combo.group("arquivo") or "").strip(" .,!?:;\"'")
        conteudo = str(combo.group("conteudo") or "").strip(" .,!?:;\"'")
        if pasta:
            return {"nome": pasta, "arquivo_nome": arquivo, "arquivo_conteudo": conteudo}

    m_folder = re.search(
        r"\b(?:cria|criar|crie)\s+(?:uma\s+)?pasta\s+(?:chamada|chamado|chamadda|com nome)?\s*(.+?)(?=\s+(?:e\s+dentro|dentro|e\s+coloca|e\s+cria|e\s+arquivo|arquivo|com\s+um\s+arquivo|com\s+arquivo|,|;|\.)|$)",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_folder:
        nome = str(m_folder.group(1) or "").strip(" .,!?:;\"'")
        if nome:
            return {"nome": nome}
    return {}


def _extrair_delete_pasta_arquivo(frase: str) -> dict:
    texto_local = re.sub(r"\s+", " ", str(frase or "").strip())
    if not texto_local:
        return {}

    if not re.search(r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\b", texto_local):
        return {}

    m_ref = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?P<ref>ela|ele|isso|essa|esse|essa\s+pasta|esse\s+arquivo)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_ref:
        ref = str(m_ref.group("ref") or "").strip()
        return {"alvo": ref}

    m_pasta = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:a|o|uma|um)?\s*pasta\s+(?:chamada|chamado|com\s+nome|de\s+nome)?\s*"
        r"(?P<nome>.+?)(?=\s+(?:e\s+dentro|dentro\s+dela|com\s+arquivo|arquivo|que\s+tem|contendo)|$)",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_pasta:
        nome = str(m_pasta.group("nome") or "").strip(" .,!?:;\"'")
        if nome:
            return {"alvo": nome, "tipo": "pasta"}

    m_arquivo = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:o|a|um|uma)?\s*(?:arquivo(?:\s+de\s+texto)?|txt)\s+"
        r"(?:chamado|chamada|com\s+nome|de\s+nome)?\s*(?P<nome>.+)$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_arquivo:
        nome = str(m_arquivo.group("nome") or "").strip(" .,!?:;\"'")
        if nome and not nome.lower().endswith(".txt"):
            nome = f"{nome}.txt"
        if nome:
            return {"alvo": nome, "tipo": "arquivo"}

    m_generico = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:o|a|os|as|um|uma)?\s*(?P<nome>[a-zA-Z0-9_\-.][a-zA-Z0-9_\-.\s]{0,40})$",
        texto_local,
        flags=re.IGNORECASE,
    )
    if m_generico:
        nome = str(m_generico.group("nome") or "").strip(" .,!?:;\"'")
        nome_norm = _normalizar_texto_com_apelidos(nome)
        if nome and nome_norm not in {
            "arquivo",
            "pasta",
            "item",
            "negocio",
            "negócio",
            "isso",
            "essa",
            "esse",
            "ela",
            "ele",
        }:
            return {"alvo": nome}

    return {}


def detectar_intencao_deterministica(texto: str):
    """Reconhece comandos claros sem depender da IA conversacional."""
    bruto = str(texto or "").strip()
    if not bruto:
        return None
    if _texto_conversa_casual_sem_acao(bruto):
        return None
    if _texto_bloqueia_playlist_agora(bruto):
        return {"intent": "STOP_PLAYLIST_CONTEXT", "params": {}}
    if _texto_social_curto(bruto):
        return None

    t = _normalizar_texto_com_apelidos(bruto)
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t or _ignorar_token_solto(t):
        return None
    if _fluxo_prioritario_da_ia(t) and not _texto_expresso_melhor_no_deterministico(t):
        return None
    if _texto_depende_de_contexto(t) and not any(x in t for x in ["fecha", "fechar", "mata", "derruba", "cancela", "cancelar", "volume", "tela cheia", "fullscreen", "em foco", "abrir", "abre", "apaga", "apagar", "deleta", "deletar", "remove", "remover", "exclui", "excluir"]):
        return None
    destino = _target_from_params({}, bruto)
    t_sem_destino = _limpar_destino_pc_b(t)

    def _params(**kwargs):
        if destino == "pc_b":
            kwargs["target"] = "pc_b"
        return kwargs

    if any(x in t for x in ["instagram.com/direct", "instagram.com", "www.instagram.com", "instagram direct", "direct/t/"]):
        return {"intent": "OPEN_URL", "params": _params(alvo="instagram")}
    if re.search(r"https?://\S+", bruto) and "instagram" in t:
        return {"intent": "OPEN_URL", "params": _params(alvo="instagram")}

    # Salvar a musica atual em playlist: precisa vencer fallback conversacional.
    m_add_musica_playlist = re.search(
        r"\b(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b"
        r".{0,60}?\b(?:essa|esta|a)?\s*(?:musica|música|faixa|canção|cancao)?\b"
        r".{0,30}?\b(?:na|nessa|nesta|para a|pra|em)\s+playlist\s+(?P<nome>.+)$",
        t_sem_destino,
        flags=re.IGNORECASE,
    )
    if m_add_musica_playlist:
        pl = _limpar_nome_playlist(m_add_musica_playlist.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_ADD", "params": _params(nome_playlist=pl)}

    if re.fullmatch(r"(essa|esta|isso|essa aqui|esta aqui)\s+(tambem|também)", t_sem_destino, flags=re.IGNORECASE):
        ultima_pl = str(_musica_estado_get("ultima_playlist") or "").strip()
        if ultima_pl:
            return {"intent": "PLAYLIST_ADD", "params": _params(nome_playlist=ultima_pl, referencia_contextual=True)}

    # Confirmacao do Porteiro: so intercepta se houver abas sugeridas.
    if _abas_sugeridas_fechar and re.fullmatch(
        r"(sim|pode|pode fechar|fecha|fecha as abas|limpa|limpa as abas|vai la|vai lá|faz o que sugeriu|manda ver)",
        t_sem_destino,
    ):
        return {"intent": "CLOSE_IDLE_TABS", "params": _params()}

    # Tela/visao.
    if any(p in t for p in [
        "o que voce ve na tela", "o que você vê na tela", "o que ta na tela", "o que tá na tela",
        "olha minha tela", "olha a tela", "ver minha tela", "captura a tela", "tira print",
        "screenshot", "print da tela",
        "guarda esse momento", "salva esse momento", "memoriza isso", "lembra dessa tela",
        "guarda essa tela", "salva essa tela", "faz memoria disso", "faz memória disso",
    ]):
        return {"intent": "SCREEN_CAPTURE", "params": _params()}

    # Emails e notificacoes.
    if "email" in t or "emails" in t or "e-mail" in t:
        if any(p in t for p in ["calar a boca", "silencia esse remetente", "silencia a shein", "manda a shein", "manda o remetente", "silenciar esse email", "ignorar esse email", "não me enche"]):
            alvo = ""
            m_alvo = re.search(r"manda a\s+(?P<alvo>[a-z0-9\s]+?)\s+calar a boca", t, flags=re.IGNORECASE)
            if m_alvo:
                alvo = str(m_alvo.group("alvo") or "").strip()
            return {"intent": "NOTIFICATIONS", "params": _params(acao="silenciar_remetente", alvo=alvo)}
        if any(p in t for p in ["sincroniza", "sincronizar", "atualiza", "atualizar"]):
            return {"intent": "EMAIL_SYNC", "params": _params()}
        if any(p in t for p in ["urgente", "urgentes", "importante", "importantes", "prioritario", "prioritários", "prioritarios"]):
            return {"intent": "EMAIL_READ", "params": _params(urgentes=True)}
        if any(p in t for p in ["le", "lê", "ler", "mostra", "ver", "verifica", "checa", "quantos", "fale", "falar", "resuma", "resumo", "me fala", "me fale", "o que eles me falam", "o que falam"]):
            return {"intent": "EMAIL_READ", "params": _params()}

    if "briefing" in t and any(p in t for p in ["fala", "fale", "mostra", "mostrar", "repete", "repetir", "diz", "diga", "conta", "contar"]):
        return {"intent": "BRIEFING_REPEAT", "params": _params()}

    if "notificacao" in t or "notificacoes" in t or "notificação" in t or "notificações" in t:
        if any(p in t for p in ["silencia", "silenciar", "desativa", "desativar", "mute"]):
            return {"intent": "NOTIFICATIONS", "params": _params(acao="silenciar")}
        if any(p in t for p in ["ativa", "ativar", "reativa", "reativar"]):
            return {"intent": "NOTIFICATIONS", "params": _params(acao="ativar")}
        if any(p in t for p in ["le", "lê", "ler", "mostra", "ver", "verifica"]):
            return {"intent": "NOTIFICATIONS", "params": _params(acao="ler")}

    # Volume.
    if "volume" in t or any(p in t for p in ["mudo", "mute", "sem som", "silencio", "silêncio", "mais alto", "mais baixo"]):
        m_vol = re.search(r"\b(?:volume|som)\s*(?:em|no|para|pra)?\s*(\d{1,3})\s*%?\b", t)
        if m_vol:
            return {"intent": "VOLUME", "params": _params(acao="set", nivel_volume=int(m_vol.group(1)))}
        if any(p in t for p in ["mudo", "mute", "sem som", "silencio", "silêncio", "silenciar"]):
            return {"intent": "VOLUME", "params": _params(acao="mute")}
        if any(p in t for p in ["aumenta", "aumentar", "sobe", "subir", "mais alto"]):
            return {"intent": "VOLUME", "params": _params(acao="up")}
        if any(p in t for p in ["abaixa", "baixa", "baixar", "diminui", "diminuir", "mais baixo"]):
            return {"intent": "VOLUME", "params": _params(acao="down")}

    # Controle de midia.
    if _contexto_musical_ativo() and any(x in t for x in ["pausa ela", "pausa ele", "pausa isso", "para ela", "para ele", "para isso"]):
        return {"intent": "MEDIA_CONTROL", "params": _params(acao="pause", platform="music")}
    if _contexto_musical_ativo() and any(x in t for x in ["despausa ela", "despausa ele", "retoma ela", "retoma ele", "continua ela", "continua ele"]):
        return {"intent": "MEDIA_CONTROL", "params": _params(acao="play", platform="music")}
    if any(x in t for x in ["despausa", "despausar", "retoma a musica", "retoma a música", "continua a musica", "continua a música", "volta a tocar", "continua tocando"]):
        return {"intent": "MEDIA_CONTROL", "params": _params(acao="play")}
    if any(x in t for x in ["pausa", "pause", "pausar", "para a musica", "para música", "para musica", "play pause"]):
        return {"intent": "MEDIA_CONTROL", "params": _params(acao="pause")}
    if ("playlist" not in t) and any(x in t for x in ["proxima musica", "próxima música", "proxima", "próxima", "pula", "proximo", "próximo"]):
        return {"intent": "MEDIA_CONTROL", "params": _params(acao="next")}
    if any(x in t for x in ["volta a musica", "música anterior", "musica anterior", "anterior"]):
        return {"intent": "MEDIA_CONTROL", "params": _params(acao="prev")}

    if any(x in t for x in ["sua playlist", "suas playlists", "playlist da laylay", "playlists da laylay", "playlist dela", "playlists dela"]):
        m_copy = re.search(
            r"(?:coloca|bota|adiciona|salva|guarda)\s+(?P<musica>.+?)\s+da\s+(?:sua|da\s+laylay|dela)\s+playlist\s+(?P<origem>.+?)\s+(?:na|minha|para a|pra)\s+playlist\s+(?P<destino>.+)$",
            t,
            flags=re.IGNORECASE,
        )
        if m_copy:
            return {
                "intent": "LAYLAY_PLAYLIST_COPY",
                "params": _params(
                    musica=str(m_copy.group("musica") or "").strip(),
                    origem=_limpar_nome_playlist(m_copy.group("origem") or ""),
                    destino=_limpar_nome_playlist(m_copy.group("destino") or ""),
                ),
            }
        m_nome = re.search(r"playlist\s+(?P<nome>[a-z0-9\s_]+)$", t, flags=re.IGNORECASE)
        return {"intent": "LAYLAY_PLAYLIST_LIST", "params": _params(nome_playlist=_limpar_nome_playlist(m_nome.group("nome") if m_nome else ""))}

    # Playlist: tocar/abrir uma playlist salva.
    if "playlist" in t:
        m_create_add = re.search(
            r"\b(?:cria|criar|crie)\s+(?:uma\s+)?playlist\s+(?:chamada|com nome|de nome)?\s*(?P<nome>.+?)\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b.*$",
            t,
            flags=re.IGNORECASE,
        )
        if m_create_add:
            pl = _limpar_nome_playlist(m_create_add.group("nome") or "")
            if pl:
                return {"intent": "PLAYLIST_ADD", "params": _params(nome_playlist=pl)}

        if re.search(r"\b(quais|lista|listar|mostra|mostrar|o que tem|oque tem)\b", t):
            pl = extrair_nome_playlist(bruto)
            if not pl:
                m = re.search(r"playlist\s+(.+)$", t)
                pl = _limpar_nome_playlist(m.group(1) if m else "")
            return {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}

        quer_salvar = (
            re.search(r"\b(coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b", t)
            and re.search(r"\b(na|nessa|nesta|para a|pra)\s+playlist\b", t)
        )
        if quer_salvar:
            pl = extrair_nome_playlist(bruto)
            return {"intent": "PLAYLIST_ADD", "params": _params(nome_playlist=pl)}

        quer_tocar = re.search(r"\b(toca|toque|coloca|coloque|abre|abra|ouvir|escuta|escute)\b", t)
        if quer_tocar:
            m = re.search(r"playlist\s+(.+)$", t)
            pl = _limpar_nome_playlist(m.group(1) if m else "")
            if pl:
                return {"intent": "PLAYLIST_PLAY", "params": _params(nome_playlist=pl)}

    # Organização de janelas/desktop.
    if any(v in t for v in ["organiza", "organizar", "arruma", "arrumar"]) and any(
        alvo in t for alvo in ["area de trabalho", "área de trabalho", "desktop", "tela", "janelas", "janela"]
    ):
        return {"intent": "ORGANIZAR_DESKTOP", "params": _params(left="vscode", right="opera")}

    # Continuidade contextual para janelas/apps.
    referencia_janela_contextual = (
        _texto_depende_de_contexto(t)
        or any(v in t for v in ["ele", "ela", "isso"])
    )
    if referencia_janela_contextual and any(v in t for v in ["foco", "na frente", "pra frente", "para frente", "tela cheia", "fullscreen", "maximiza", "maximizar"]):
        try:
            estado = dict(mente_integrada_estado or {})
        except Exception:
            estado = {}
        ultima_intencao_ctx = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
        ultimo_app = str(estado.get("ultimo_app_janela") or "").strip()
        if not ultimo_app and ultima_intencao_ctx in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
            ultimo_app = str(
                (estado.get("ultima_acao_params") or {}).get("nome_app")
                or (estado.get("ultima_acao_params") or {}).get("app")
                or estado.get("ultimo_alvo")
                or ""
            ).strip()
        if ultimo_app:
            if any(v in t for v in ["tela cheia", "fullscreen", "maximiza", "maximizar"]):
                return {"intent": "MAXIMIZE_WINDOW", "params": _params(nome_app=ultimo_app)}
            return {"intent": "APP_OPEN", "params": _params(nome_app=ultimo_app, modo="focus")}

    # Maximizar/foco/tela cheia de janela.
    m_max_posposto = re.search(
        r"\b(?:coloca|coloque|bota|deixa|poe|põe)\s+(?:o|a|os|as)?\s*(?P<app>.+?)\s+(?:em|no|na)\s+(?P<modo>tela cheia|fullscreen|full screen|foco|primeiro plano)$",
        t_sem_destino,
        flags=re.IGNORECASE,
    )
    if m_max_posposto:
        app = str(m_max_posposto.group("app") or "").strip()
        modo_txt = str(m_max_posposto.group("modo") or "").strip().lower()
        app = app.replace("pra frente", "").replace("para frente", "").strip()
        if app:
            if modo_txt in {"tela cheia", "fullscreen", "full screen"}:
                return {"intent": "MAXIMIZE_WINDOW", "params": _params(nome_app=app)}
            return {"intent": "APP_OPEN", "params": _params(nome_app=app, modo="focus")}

    m_max = re.search(r"\b(maximiza|maximizar|tela cheia|fullscreen|coloca em foco|bota em foco|deixa em foco|traz)\s+(?:o|a)?\s*(.+)$", t_sem_destino)
    if m_max:
        app = re.sub(r"^(o|a|os|as|um|uma)\s+", "", (m_max.group(2) or "").strip())
        app = app.replace("em foco", "").replace("pra frente", "").replace("para frente", "").strip()
        if app:
            modo = "fullscreen" if any(p in t for p in ["tela cheia", "fullscreen"]) else "focus"
            if modo == "fullscreen":
                return {"intent": "MAXIMIZE_WINDOW", "params": _params(nome_app=app)}
            return {"intent": "APP_OPEN", "params": _params(nome_app=app, modo="focus")}

    # Abrir aplicativos e sites mesmo quando o comando vem misturado com texto normal.
    intent_abrir = _extrair_intencao_abrir_app(bruto)
    if intent_abrir:
        if intent_abrir.get("intent") == "OPEN_URL":
            return {"intent": "OPEN_URL", "params": _params(**intent_abrir.get("params", {}))}
        nome_app = str(intent_abrir.get("params", {}).get("nome_app") or "").strip()
        if nome_app:
            return {"intent": "APP_OPEN", "params": _params(nome_app=nome_app)}

    # Desempate entre música e playlist quando o usuário fala só o nome.
    if re.match(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b", t):
        if any(x in t for x in ["música", "musica", "youtube", "no youtube", "no yt", "no you tube"]):
            q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b\s*", "", t).strip()
            q = re.sub(r"^(a|o|as|os|uma|um|essa|esse|essa música|essa musica|essa canção|essa cancao)\s+", "", q).strip()
            if q:
                return {"intent": "MUSIC_SEARCH", "params": _params(query=q)}

        pl_direta = _detectar_playlist_nome_direto(bruto)
        if pl_direta:
            if any(x in t for x in ["playlist", "lista", "listar", "quais", "mostra", "o que tem", "oque tem"]):
                return {"intent": "PLAYLIST_LIST", "params": _params(nome_playlist=pl_direta)}
            return {"intent": "PLAYLIST_PLAY", "params": _params(nome_playlist=pl_direta)}

        if not any(x in t for x in ["playlist", "música", "musica", "youtube", "yt", "netflix"]):
            q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b\s*", "", t).strip()
            q = re.sub(r"^(a|o|as|os|uma|um|essa|esse)\s+", "", q).strip()
            if q:
                return {"intent": "MUSIC_SEARCH", "params": _params(query=q)}

    # Fechar abas/sites/programas.
    m_close = re.search(r"\b(fecha|fechar|mata|derruba|encerra|encerrar)\s+(?:o|a|os|as|um|uma|essa|esse)?\s*(.+)$", t_sem_destino)
    if m_close:
        alvo = re.sub(r"^(aba|site|janela|programa|app|aplicativo)\s+(do|da|de)?\s*", "", (m_close.group(2) or "").strip()).strip()
        alvo = re.sub(r"^(o|a|os|as|um|uma)\s+", "", alvo).strip()
        if not alvo or alvo in {"aba", "essa aba", "site", "janela"}:
            return {"intent": "CLOSE_TAB", "params": _params()}
        alvo_norm = alvo.lower()
        if "aba" in t or "site" in t or alvo_norm in SITES_DIRECTOS or alvo_norm in {"youtube", "netflix", "google", "spotify", "whatsapp", "chatgpt"}:
            return {"intent": "CLOSE_TAB", "params": _params(alvo=alvo)}
        for app in sorted(APPS_MAP.keys(), key=len, reverse=True):
            if alvo_norm == app or app in alvo_norm:
                return {"intent": "CLOSE_APP", "params": _params(nome_app=app)}
        return {"intent": "CLOSE_APP", "params": _params(nome_app=alvo)}

    # Netflix.
    if "netflix" in t:
        if any(p in t for p in ["abre", "abrir", "entra", "entrar"]):
            return {"intent": "NETFLIX", "params": _params()}
        m_netflix = re.search(r"(?:procura|pesquisa|busca|coloca|toca)\s+(.*?)\s+(?:na|no)\s+netflix", t)
        if m_netflix:
            return {"intent": "NETFLIX", "params": _params(query=m_netflix.group(1).strip())}

    # Pesquisa web explicita.
    m_google = re.search(r"\b(pesquisa|pesquisar|busca|buscar|procura|procurar)\s+(?:no google\s+)?(?:sobre\s+)?(.+)$", t_sem_destino)
    if m_google and "youtube" not in t and "netflix" not in t:
        query = (m_google.group(2) or "").strip()
        if query:
            return {"intent": "SEARCH", "params": _params(query=query, engine="google")}

    # Abrir site/URL sem depender da IA.
    m_site = re.search(r"\b(entra|entrar|abre|abra|abrir|vai)\s+(?:no|na|em|para|pra)?\s*(?:site\s+)?(.+)$", t_sem_destino)
    if m_site:
        alvo = re.sub(r"^(o|a|os|as|um|uma)\s+", "", (m_site.group(2) or "").strip()).strip()
        alvo_norm = alvo.lower()
        if alvo_norm in SITES_DIRECTOS or "." in alvo_norm or alvo_norm.startswith(("http://", "https://")):
            return {"intent": "OPEN_URL", "params": _params(alvo=alvo)}

    # Controles de midia comuns quando chegam pelo chat.
    # YouTube/musica: depois de sites/apps para "abre youtube" nao virar busca musical.
    if "youtube" in t:
        m_yt = re.search(r"(?:procura|pesquisa|busca|buscar|coloca|toca|toque)\s+(.*?)\s+(?:no|na)\s+youtube", t)
        if m_yt and m_yt.group(1).strip():
            return {"intent": "MUSIC_SEARCH", "params": _params(query=m_yt.group(1).strip())}
        if any(p in t for p in ["abre", "abrir", "entra", "entrar"]):
            return {"intent": "OPEN_URL", "params": _params(alvo="youtube")}

    pl_direta = _detectar_playlist_nome_direto(bruto)
    if pl_direta and not any(x in t for x in ["música", "musica", "youtube", "yt"]):
        if any(x in t for x in ["playlist", "lista", "listar", "quais", "mostra", "o que tem", "oque tem"]):
            return {"intent": "PLAYLIST_LIST", "params": _params(nome_playlist=pl_direta)}
        return {"intent": "PLAYLIST_PLAY", "params": _params(nome_playlist=pl_direta)}

    if re.match(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute)\b", t) and "playlist" not in t and "netflix" not in t:
        q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute)\b", " ", t_sem_destino).strip()
        q = re.sub(r"^(a|o|uma|um)\s+", "", q).strip()
        q = q.replace("música", " ").replace("musica", " ").replace("no youtube", " ").replace("na youtube", " ")
        q = re.sub(r"\s+", " ", q).strip()
        q = _normalizar_query_musical(q)
        if q and q not in {"playlist", "netflix"}:
            return {"intent": "MUSIC_SEARCH", "params": _params(query=q)}

    # Pastas simples.
    m_pasta_contextual = re.search(
        r"\bdentro\s+dela\b.*?\b(?:coloca|cria|criar|crie)\b\s+(?:a|uma)?\s*pasta\s+(?:chamada|com nome)?\s*(?P<nome>.+)$",
        t_sem_destino,
        flags=re.IGNORECASE,
    )
    if m_pasta_contextual:
        try:
            estado = dict(mente_integrada_estado or {})
        except Exception:
            estado = {}
        ultima_intencao = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
        ultimo_params = estado.get("ultima_acao_params") if isinstance(estado.get("ultima_acao_params"), dict) else {}
        pasta_pai = str(ultimo_params.get("nome") or ultimo_params.get("pasta") or ultimo_params.get("alvo") or "").strip()
        nome_contextual = str(m_pasta_contextual.group("nome") or "").strip(" .,!?:;\"'")
        if ultima_intencao == "CREATE_FOLDER" and pasta_pai and nome_contextual:
            return {"intent": "CREATE_FOLDER", "params": _params(nome=nome_contextual, pasta_pai=pasta_pai)}

    delete_info = _extrair_delete_pasta_arquivo(t_sem_destino)
    if delete_info:
        return {"intent": "DELETE_ITEM", "params": _params(**delete_info)}

    pasta_info = _extrair_criacao_pasta_arquivo(t_sem_destino)
    if pasta_info:
        return {"intent": "CREATE_FOLDER", "params": _params(**pasta_info)}

    # Trava do PC: exige verbo explicito para nao disparar por conversa.
    if any(p in t for p in ["trava o pc", "travar o pc", "bloqueia o pc", "lock pc", "bloquear computador"]):
        return {"intent": "LOCK_PC", "params": _params()}

    return None


def _tentar_intencao_ai_primeiro(texto: str):
    bruto = str(texto or "").strip()
    if not bruto:
        return None
    if _texto_conversa_casual_sem_acao(bruto):
        return None
    if _texto_social_curto(bruto) or _texto_bloqueia_playlist_agora(bruto):
        return None

    t = _normalizar_texto_com_apelidos(bruto)
    if not t:
        return None
    if _texto_pede_direcao_musical_generica(t):
        return None
    if _texto_expresso_melhor_no_deterministico(t):
        return None

    deve_tentar = False
    if _contexto_mental_ativo():
        deve_tentar = True
    elif _texto_depende_de_contexto(t):
        deve_tentar = True
    elif _texto_parece_navegacao_ou_janela_ia(t):
        deve_tentar = True
    elif _fluxo_prioritario_da_ia(t):
        deve_tentar = True
    elif len(t.split()) <= 12 and not t.endswith("?"):
        deve_tentar = True

    if not deve_tentar:
        return None

    try:
        resultado = analisar_intencao(bruto)
    except Exception as e:
        print(f"⚠️ [IA-FIRST] falha ao analisar intenção: {e}")
        return None

    if not isinstance(resultado, dict):
        return None

    intent = str(resultado.get("intent") or "").upper().strip()
    if intent == "CANCELAR_ACAO" and not _texto_cancela_acao_agora(bruto):
        return None
    if intent == "MEDIA_CONTROL":
        acao = str((resultado.get("params") or {}).get("acao") or "").strip().lower()
        if acao and acao not in {"play", "pause", "next", "prev", "replay", "pause_play", "toggle", "resume", "retomar", "retoma", "continuar", "continua", "despausa", "despausar"}:
            return None
    if intent not in _INTENTS_EXECUTAVEIS_MENTE:
        return None
    return resultado


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

    if "playlist" in t and re.search(r"\b(coloca|coloque|toca|toque|abre|abra|ouvir|escuta|escute|salva|salve|guarda|guarde|adiciona|adicione|lista|listar|mostra|mostrar|quais)\b", t):
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

def _handle_open_app_flow(texto, lower_text):
    contexto = {
        "extrair_intencao_abrir_app": _extrair_intencao_abrir_app,
        "executar_intencao": executar_intencao,
    }
    return _handle_open_app_flow_mente(contexto, texto, lower_text)

def _handle_youtube_volume_flow(texto, lower_text):
    contexto = {
        "falar_com_lipsync": falar_com_lipsync,
        "ajustar_volume_sistema": ajustar_volume_sistema,
        "ajustar_volume_sistema_relativo": ajustar_volume_sistema_relativo,
    }
    return _handle_youtube_volume_flow_mente(contexto, lower_text)

def _handle_pause_next_flow(texto, lower_text):
    contexto = {
        "enviar_comando_chrome": enviar_comando_chrome,
        "_confirmar_execucao_debochada": _confirmar_execucao_debochada,
        "comando_sugerido": _continuidades_get("comando_sugerido"),
        "comando_sugerido_payload": _continuidades_get("comando_sugerido_payload"),
        "comando_sugerido_estado": _continuidades_get("comando_sugerido_estado", "NONE"),
        "comando_sugerido_ts": _continuidades_get("comando_sugerido_ts", 0.0),
    }
    resultado = _handle_pause_next_flow_mente(contexto, texto, lower_text)
    _continuidades_update(
        comando_sugerido=contexto["comando_sugerido"],
        comando_sugerido_payload=contexto["comando_sugerido_payload"],
        comando_sugerido_estado=contexto["comando_sugerido_estado"],
        comando_sugerido_ts=contexto["comando_sugerido_ts"],
    )
    return resultado

def _handle_youtube_music_intents(texto, lower_text):
    contexto = {
        "enviar_comando_chrome": enviar_comando_chrome,
        "falar_com_lipsync": falar_com_lipsync,
    }
    return _handle_youtube_music_intents_mente(contexto, texto, lower_text)

def _handle_close_tabs_flow(texto, lower_text):
    contexto = {
        "validar_e_enviar_comando": validar_e_enviar_comando,
        "_confirmar_execucao_debochada": _confirmar_execucao_debochada,
    }
    return _handle_close_tabs_flow_mente(contexto, texto, lower_text)

def _handle_site_flow(texto, lower_text):
    contexto = {
        "executar_comando": executar_comando,
        "_resetar_sugestao": _resetar_sugestao,
        "_confirmar_execucao_debochada": _confirmar_execucao_debochada,
    }
    return _handle_site_flow_mente(contexto, texto, lower_text)

def _handle_image_flow(texto, lower_text):
    contexto = {
        "buscar_imagem_url": buscar_imagem_url,
        "baixar_imagem_direto": baixar_imagem_direto,
        "falar_com_lipsync": falar_com_lipsync,
        "messages": messages,
        "webbrowser": webbrowser,
    }
    return _handle_image_flow_mente(contexto, texto, lower_text)

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
        "NETFLIX_PERFIL": "entrar no perfil Pedro da Netflix (Tab+Enter)",
        "ENTRAR_PERFIL_PEDRO": "entrar no perfil Pedro da Netflix (Tab+Enter)",
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

        if sugestao in {"NETFLIX_PERFIL", "ENTRAR_PERFIL_PEDRO"}:
            executar_netflix_perfil()
            _confirmar_execucao_debochada(texto, "O usuário confirmou a sugestão e o Python entrou no perfil Pedro da Netflix (apenas Tab+Enter). Responda curto, debochada, confirmando. Não use [EXEC].")
            return True

        if sugestao == "SYS_MODE_CODE":
            _executar_combo_modo_code(payload if isinstance(payload, dict) else {})
            oq = str(original_payload.get("music_query") or "lofi focus").strip().lower()
            nq = str((payload if isinstance(payload, dict) else {}).get("music_query") or oq).strip()
            nf = str((payload if isinstance(payload, dict) else {}).get("netflix_query") or "").strip()
            if nf:
                falar_com_lipsync(f"Beleza, ambiente pronto, mas troquei o Lo-fi por {nf}. Boa escolha, Pedro!", "debochada", 2)
            elif nq and nq.lower() != oq:
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
            executar_comando("OPEN_SITE", "https://www.cobasi.com.br")
            _confirmar_execucao_debochada(texto, "O usuário confirmou e o Python abriu um site alternativo de pet. Responda curto, debochada, confirmando. Não use [EXEC].")
            return True

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

def _handle_comando_rapido_flow(texto):
    contexto = {
        "extrair_comando_rapido": extrair_comando_rapido,
        "enviar_comando_chrome": enviar_comando_chrome,
        "executar_comando": executar_comando,
        "_confirmar_execucao_debochada": _confirmar_execucao_debochada,
    }
    return _handle_comando_rapido_flow_mente(contexto, texto)

def _handle_fuzzy_intent_flow(texto):
    contexto = {
        "interpretar_intencao_fuzzy_llm": interpretar_intencao_fuzzy_llm,
        "enviar_comando_chrome": enviar_comando_chrome,
        "falar_com_lipsync": falar_com_lipsync,
        "messages": messages,
        "abrir_url_com_reciclagem": abrir_url_com_reciclagem,
        "fechar_abas_vazias": fechar_abas_vazias,
        "solicitar_lista_abas": solicitar_lista_abas,
        "selecionar_abas_para_fechar_llm": selecionar_abas_para_fechar_llm,
        "add_to_playlist_url": add_to_playlist_url,
        "solicitar_aba_ativa": solicitar_aba_ativa,
        "extrair_nome_playlist": extrair_nome_playlist,
        "_playlist_primeira_url": _playlist_primeira_url,
        "playlist_len": playlist_len,
        "_playlist_item_at": _playlist_item_at,
        "_yt_clean_title": _yt_clean_title,
        "_fala_playlist_duplicado": _fala_playlist_duplicado,
        "_fala_playlist_duplicado_meta": _fala_playlist_duplicado_meta,
        "_fala_playlist_sucesso": _fala_playlist_sucesso,
        "executar_comando": executar_comando,
        "ultima_playlist": _musica_estado_get("ultima_playlist"),
    }
    resultado = _handle_fuzzy_intent_flow_mente(contexto, texto)
    _musica_estado_set("ultima_playlist", contexto.get("ultima_playlist", _musica_estado_get("ultima_playlist")))
    return resultado

def _handle_llm_fallback_flow(texto):
    contexto = _montar_contexto_fallback_conversa_mente(
        processar_aprendizado_apelido_imediato=_processar_aprendizado_apelido_imediato,
        refinar_contexto_mental=_refinar_contexto_mental,
        messages=messages,
        enviar_mensagem=enviar_mensagem,
        processar_resposta_laylay=processar_resposta_laylay,
        texto_indica_autocorrecao=_texto_indica_autocorrecao,
        registrar_autocorrecao_virtual=_registrar_autocorrecao_virtual,
        falar_com_lipsync=falar_com_lipsync,
        salvar_memoria=salvar_memoria,
        current_emotion=current_emotion,
        emotion_level=emotion_level,
        resposta_conversa_local=_resposta_conversa_local,
        resposta_conversa_rapida_local=_resposta_conversa_rapida_local,
        fala_e_fallback_neutro=_fala_e_fallback_neutro,
        registrar_mente_curta=_registrar_mente_curta,
    )
    return _handle_llm_fallback_flow_mente(contexto, texto)

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

def gerar_resposta_ia(texto: str):
    global messages, current_emotion, emotion_level, is_speaking
    t = str(texto or "").strip()
    if not t:
        return

    if _processar_aprendizado_apelido_imediato(t):
        return
    _refinar_contexto_mental(t)

    try:
        messages.append({"role": "user", "content": t})
        modo_rapido = _usar_modo_rapido_conversa(t)
        bot_raw = enviar_mensagem(messages, max_tokens=384 if modo_rapido else 640, modo_rapido=modo_rapido)
        bot_processado = processar_resposta_laylay(bot_raw)
        if isinstance(bot_processado, tuple):
            bot = str(bot_processado[0] or "").strip()
        else:
            bot = str(bot_processado or "").strip()
        bot = _construir_fala_conversa(bot, t, "conversa", [])
        if _texto_indica_autocorrecao(bot):
            try:
                _registrar_autocorrecao_virtual("conversa", t, bot, "autocorreção espontânea na resposta principal")
            except Exception as e:
                print(f"⚠️ [AUTOCORREÇÃO] falha ao registrar correção espontânea: {e}")

        _atualizar_memoria_topicos(t, bot)

        print(f"Laylay [{current_emotion} lvl{emotion_level}]: {bot}")
        messages.append({"role": "assistant", "content": bot})
        falar_com_lipsync(bot, current_emotion, emotion_level)
        _registrar_mente_curta(t, bot, habilidade="conversa")
        memoria_inteligente.adicionar_interacao(texto, bot)
        salvar_memoria()

    except Exception as e:
        erro_msg = "Pedro, estou sem conexão com a inteligência artificial agora. Tenta de novo em alguns segundos."
        print(f"Laylay [calma lvl1]: {erro_msg}")
        falar_com_lipsync(erro_msg, "calma", 1)
        
        is_speaking = False
        time.sleep(0.5)

def processar_comando_ia(resposta_texto: str):
    return _processar_comando_ia_mente(resposta_texto, FALLBACK_FALA_NEUTRA)


def _executar_controle_midia_nativo(command: str) -> bool:
    cmd = str(command or "").strip().lower()
    try:
        if cmd == "pause_play":
            print("🎵 [MIDIA:NATIVO] tecla play/pause")
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
            return True
        if cmd == "next":
            print("🎵 [MIDIA:NATIVO] tecla next")
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
            return True
        if cmd == "prev":
            print("🎵 [MIDIA:NATIVO] tecla previous x2")
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            time.sleep(0.18)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return True
        if cmd == "replay":
            print("🎵 [MIDIA:NATIVO] replay via previous")
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
            return True
    except Exception as e:
        print(f"⚠️ [MIDIA NATIVA] falha ao executar '{cmd}': {e}")
    return False


def _executar_exec(cmd: str, arg):
    comando = str(cmd or "").strip()
    c_args = "" if arg is None else str(arg).strip()
    contexto = {
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
        "arg": arg,
        "is_valid_url": is_valid_url,
        "formatar_url_ou_busca": formatar_url_ou_busca,
        "_listar_playlists_salvas": _listar_playlists_salvas,
        "_autorizar_acao_pratica": _autorizar_acao_pratica,
        "_normalizar_texto_com_apelidos": _normalizar_texto_com_apelidos,
        "ctypes": ctypes,
        "VK_MEDIA_PLAY_PAUSE": VK_MEDIA_PLAY_PAUSE,
        "VK_MEDIA_NEXT_TRACK": VK_MEDIA_NEXT_TRACK,
        "VK_MEDIA_PREV_TRACK": VK_MEDIA_PREV_TRACK,
    }
    if _executar_comando_conteudo_mente(comando, c_args, comando, comando.upper(), contexto):
        print(f"🧠 [EXEC] caminho modular de conteudo assumiu: {comando}")
        return True
    ok_legado = _executar_exec_mente(cmd, arg, contexto)
    if ok_legado:
        print(f"🧩 [EXEC] fallback legado assumiu: {comando}")
    return ok_legado
    

_normalizar_nome_app = _normalizar_nome_app_mente
_buscar_executavel = _buscar_executavel_mente
abrir_programa = _abrir_programa_mente
filtrar_apenas_fala = partial(_filtrar_apenas_fala_mente, historico=None, fallback_fala=FALLBACK_FALA_NEUTRA)

def limpar_diccao_e_ruido(texto_falado):
    """Filtro anti-ruído + corretor de dicção para eliminar alucinações do Whisper"""
    texto = texto_falado.lower().strip()
    
    # 1. MATA AS ALUCINAÇÕES DE RUÍDO DO WHISPER
    alucinacoes = [
        "obrigado por assistir", "inscreva-se", "legendas",
        "amém", "obrigado.", "com legendas", "obrigado",
        "editado por", "amara.org", "transmissão ao vivo"
    ]
    for alucinacao in alucinacoes:
        if texto == alucinacao or texto == alucinacao + ".":
            return ""  # Retorna vazio = ignora

    # 2. DICIONÁRIO DE CORREÇÃO (Seus erros de dicção)
    dicionario_correcao = {
        "canista minha terra": "organiza minha tela",
        "o canista minha terra": "organiza minha tela",
        "orcaniça": "organiza",
        "ocaniça": "organiza",
        "organisa": "organiza",
        "organaiza": "organiza",
        "mi yaya": "minha tela",
        "adiata": "tela",
        "opede": "opera",
        "opeditor": "opera",
        "whatsappi": "whatsapp",
        "whatsapi": "whatsapp",
        "what": "whatsapp",
        "pedu": "pelo",
        "teta cheia": "tela cheia",
        "teta": "tela",
        "coloco": "coloca",
        "troco": "troca",
        "coco": "código",
        "coigo": "código",
        "muica": "música",
        "muisca": "música",
        "próima": "próxima",
        "proxima": "próxima"
    }

    # Substitui palavras erradas pelas certas
    for errado, certo in dicionario_correcao.items():
        texto = texto.replace(errado, certo)
        
    return texto.strip()

def transcrever_com_whisper(audio):
    """Transcreve com Whisper + filtro anti-alucinação + initial_prompt"""
    try:
        temp_file = "temp_voz.wav"
        with open(temp_file, "wb") as f:
            f.write(audio.get_wav_data())

        # LISTA NEGRA de alucinações comuns
        lista_negra = [
            "legendas pela comunidade", "amara.org", "obrigado por assistir",
            "curta o vídeo", "inscreva-se no canal", "fiquem com deus",
            "transcrição", "legenda por", "edited by"
        ]

        # TRANSCRIÇÃO COM initial_prompt e VAD Filter otimizado
        segments, info = modelo_whisper.transcribe(
            temp_file,
            language="pt",
            initial_prompt="Organiza a tela, Laylay, YouTube, Spotify, VS Code, WhatsApp, Opera, Chrome, toca música, pausa, próxima, abre, fecha, clica, tela cheia, minha área, música",
            beam_size=5,
            best_of=5,
            no_speech_threshold=0.6,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        texto = " ".join([seg.text for seg in segments]).strip()

        # FILTRO DE SEGURANÇA
        texto_limpo = texto.lower()
        if any(frase in texto_limpo for frase in lista_negra) or len(texto) < 3:
            os.remove(temp_file) if os.path.exists(temp_file) else None
            return ""

        # DICIONÁRIO DE CORREÇÃO FONÉTICA (mata o "cloco", "dinh sa lõin", etc)
        correcoes = {
            "cloco": "coloca",
            "clo co": "coloca",
            "eda": "editor",
            "dinh sa lõin": "dance alone",
            "dinhsa loin": "dance alone",
            "dança alone": "dance alone",
            "fita": "VS Code",
            "fita editor": "VS Code",
        }
        for errado, certo in correcoes.items():
            texto = texto.replace(errado, certo)

        texto = re.sub(r'\s+', ' ', texto).strip()

        os.remove(temp_file) if os.path.exists(temp_file) else None
        return texto

    except Exception as e:
        print(f"❌ Erro no Whisper: {e}")
        return ""

def get_status_humor_prompt():
    """Retorna o texto que vai para o Grok/Gemini"""
    ctx = _obter_contexto_perceptivo()
    percepcao = _interpretar_contexto_vivo(ctx)
    humor = int(ctx["humor"] if ctx else humor_level)
    emocao = str(ctx["emocao"] if ctx else current_emotion).strip()
    periodo = str(ctx["periodo"] if ctx else _contexto_horario_atual()).strip()
    if humor <= -5:
        base = "está muito irritada, sarcástica e impaciente"
    elif humor <= -2:
        base = "está levemente irritada e debochada"
    elif humor >= 5:
        base = "está muito fofa, carinhosa e prestativa"
    elif humor >= 2:
        base = "está feliz, bem-humorada e debochada"
    else:
        base = "está neutra e calma"
    extras = []
    if periodo in {"madrugada", "noite"}:
        extras.append("o contexto pede baixo ritmo")
    if percepcao:
        extras.append(f"leitura contextual: {percepcao['conclusao']} (confianca={percepcao['confianca']})")
        extras.append(f"interpretacao: {percepcao['interpretacao']}")
    if emocao:
        extras.append(f"emoção percebida: {emocao}")
        extras.append(f"identidade emocional: {_descricao_emocao(emocao)}")
        extras.append(f"comportamento esperado: {_perfil_comportamento_emocional(emocao)}")
    if ctx.get("topico_ativo"):
        extras.append(f"tópico ativo: {ctx['topico_ativo']}")
    if extras:
        return base + "; " + "; ".join(extras)
    return base
    
def limpar_fala_final(texto_completo: str) -> str:
    """Tesoura inteligente: corta tudo que vem antes de 'Laylay:' """
    # Procura "Laylay:" (maiúsculo ou minúsculo)
    match = re.search(r"Laylay:\s*(.*)", texto_completo, re.IGNORECASE | re.DOTALL)
    
    if match:
        fala = match.group(1).strip()
    else:
        # Fallback seguro: remove [PENSAMENTO], [COMANDO] e qualquer coisa entre colchetes
        fala = re.sub(r"\[PENSAMENTO\]:.*?\[COMANDO\]:.*?\n", "", texto_completo, flags=re.DOTALL | re.IGNORECASE)
        fala = re.sub(r"\[.*?\]", "", fala, flags=re.IGNORECASE | re.DOTALL)
        fala = re.sub(r"^.*?:", "", fala, flags=re.IGNORECASE)  # remove tudo antes de dois-pontos
        fala = fala.strip()
    
    # Se sobrou algo vazio, devolve uma mensagem padrão
    if not fala or len(fala) < 3:
        fala = FALLBACK_FALA_NEUTRA
    
    return fala

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
    global messages, current_emotion, emotion_level, humor_level, MODO_CHAT, conversa_ativa

    t = str(texto or "").strip()
    if not t:
        return

    t_low = t.lower().strip()
    if t_low in {"modo chat", "ativar modo chat", "entrar no chat"}:
        MODO_CHAT = True
        conversa_ativa = True
        fala = "Modo chat ativado. Pode falar comigo sem eu sair distribuindo comando."
        messages.append({"role": "user", "content": t})
        messages.append({"role": "assistant", "content": fala})
        falar_com_lipsync(fala, "calma", 1)
        salvar_memoria()
        return

    if t_low in {"sair do chat", "desativar modo chat", "modo comandos"}:
        MODO_CHAT = False
        conversa_ativa = False
        fala = "Modo chat desativado. Voltei pro modo ação."
        messages.append({"role": "user", "content": t})
        messages.append({"role": "assistant", "content": fala})
        falar_com_lipsync(fala, "calma", 1)
        salvar_memoria()
        return

    contexto_inicio = _montar_contexto_inicio_chat_mente(
        messages=messages,
        current_emotion=current_emotion,
        emotion_level=emotion_level,
        processar_aprendizado_apelido_imediato=_processar_aprendizado_apelido_imediato,
        refinar_contexto_mental=_refinar_contexto_mental,
        processar_comando_deterministico=processar_comando_deterministico,
        usar_modo_rapido_conversa=_usar_modo_rapido_conversa,
        interpretar_comando_local_rapido=interpretar_comando_local_rapido,
        executar_intencao=executar_intencao,
        registrar_autoaprimoramento=_registrar_autoaprimoramento,
        texto_social_curto=_texto_social_curto,
        texto_conversa_casual_sem_acao=_texto_conversa_casual_sem_acao,
        texto_tem_comando_explicito=_texto_tem_comando_explicito,
        texto_bloqueia_playlist_agora=_texto_bloqueia_playlist_agora,
        resposta_conversa_rapida_local=_resposta_conversa_rapida_local,
        parece_elogio_ou_agradecimento_curto=_parece_elogio_ou_agradecimento_curto,
        responder_agradecimento_ou_elogio=_responder_agradecimento_ou_elogio,
        resolver_pergunta_curta_contextual_intencao=_resolver_pergunta_curta_contextual_intencao,
        texto_responde_pergunta_aberta=_texto_responde_pergunta_aberta,
        responder_pergunta_aberta=_responder_pergunta_aberta,
        texto_pede_direcao_musical_generica=_texto_pede_direcao_musical_generica,
        responder_pedido_direcao_musical_generica=_responder_pedido_direcao_musical_generica,
        processar_confirmacao_sugestao_musical=_processar_confirmacao_sugestao_musical,
        handle_feedback_pendente_misto=_handle_feedback_pendente_misto,
        handle_feedback_pendente=_handle_feedback_pendente,
        bloquear_playlist_temporariamente=_bloquear_playlist_temporariamente,
        resolver_comando_janela_contextual_forcado=_resolver_comando_janela_contextual_forcado,
        resolver_comando_midia_contextual_forcado=_resolver_comando_midia_contextual_forcado,
        resolver_comando_arquivo_contextual_forcado=_resolver_comando_arquivo_contextual_forcado,
        resolver_comando_acao_geral_contextual_forcado=_resolver_comando_acao_geral_contextual_forcado,
        resolver_comando_contextual_forcado=_resolver_comando_contextual_forcado,
        responder_contexto_janela_indisponivel=_responder_contexto_janela_indisponivel,
        emitir_resposta_curta=_emitir_resposta_curta,
        executar_intencao_curta_contextual=_executar_intencao_curta_contextual,
        registrar_mente_curta=_registrar_mente_curta,
        registrar_resultado_execucao=_registrar_resultado_execucao,
        falar_com_lipsync=falar_com_lipsync,
        salvar_memoria=salvar_memoria,
    )
    if _processar_inicio_fluxo_resposta_ia_mente(contexto_inicio, t):
        return

    if MODO_CHAT or conversa_ativa:
        print("🗨️ [CHAT] Modo chat ativo, mas seguindo o mesmo cérebro para comandos e conversa.")

    modo_rapido = _usar_modo_rapido_conversa(t)

    # Se a frase parece comando mas não foi resolvida ainda, tenta o roteador
    # de intenção antes de cair na conversa livre da IA.
    try:
        if processar_comandos_imediatos(t):
            return
    except Exception as e:
        print(f"⚠️ [IA] falha ao processar comandos imediatos: {e}")

    if not modo_rapido:
        try:
            mover_playlist = detectar_mover_playlist_texto(t)
            if mover_playlist:
                res = mover_item_playlist(
                    mover_playlist.get("origem", ""),
                    mover_playlist.get("destino", ""),
                    mover_playlist.get("musica", ""),
                )
                if res.get("ok"):
                    titulo = res.get("titulo") or "essa música"
                    origem = res.get("origem") or mover_playlist.get("origem", "")
                    destino = res.get("destino") or mover_playlist.get("destino", "")
                    fala = f"Movi {titulo} da playlist {origem} pra {destino}."
                    if res.get("duplicated"):
                        fala = f"Tirei {titulo} da playlist {origem}; ela já estava em {destino}."
                    print(f"🎵 [PLAYLIST] {fala}")
                    messages.append({"role": "user", "content": t})
                    messages.append({"role": "assistant", "content": fala})
                    falar_com_lipsync(fala, current_emotion or "calma", emotion_level or 1)
                    salvar_memoria()
                    return
                erro = res.get("error")
                if erro == "source_empty":
                    fala = f"Não achei nada na playlist {res.get('origem') or mover_playlist.get('origem')} pra mover."
                else:
                    fala = "Não consegui entender de qual playlist pra qual playlist é essa mudança."
                print(f"❌ [PLAYLIST] Falha ao mover por texto: {res}")
                falar_com_lipsync(fala, "calma", 1)
                return
        except Exception as e:
            print(f"⚠️ [PLAYLIST] Falha no atalho de mover playlist: {e}")

        try:
            entrada = str(texto or "")
            entrada_lower = entrada.lower()
            if any(s in entrada_lower for s in ["o que eu te ensinei", "o que eu te ensinei ontem", "o que você aprendeu", "o que aprendeu", "você lembra do que eu te falei", "você lembra do que eu te ensinei", "me lembra do que eu te ensinei"]):
                aprendizados = MEMORIA_SQLITE.recuperar_aprendizados(limit=3)
                if aprendizados:
                    ultimo = str(aprendizados[0]).strip()
                    if len(ultimo) > 120:
                        ultimo = ultimo[:117] + "..."
                    resposta_natural = f"Ah, lembrei. Você me ensinou isso: {ultimo}"
                    if "responde" in ultimo.lower() or "de agora" in ultimo.lower():
                        resposta_natural = f"Ah, claro. Você me passou isso aqui: {ultimo}"
                    if "de agora" in ultimo.lower():
                        resposta_natural = f"Ah, então é assim que você quer: {ultimo}"
                    print(f"🧠 [MEMÓRIA] Resposta natural de aprendizado pronta: {resposta_natural}")
                    falar_com_lipsync(resposta_natural, current_emotion or "calma", emotion_level or 1)
                    return
        except Exception as e:
            print(f"⚠️ [MEMÓRIA] Não consegui recuperar aprendizados: {e}")

        mensagens_contexto = {
            "memoria_sqlite": MEMORIA_SQLITE,
            "aba_titulo_atual": aba_titulo_atual,
            "aba_url_atual": aba_url_atual,
            "retrato_mente_integrada": _resumo_mente_integrada_para_prompt(t),
            "_resumo_mente_integrada_para_prompt": _resumo_mente_integrada_para_prompt,
            "_formatar_playlists_para_prompt": _formatar_playlists_para_prompt,
            "get_status_humor_prompt": get_status_humor_prompt,
        }
        messages, prompt_com_humor = _preparar_contexto_resposta_ia_mente(
            mensagens_contexto,
            t,
            messages,
            humor_level,
            BASE_SYSTEM_PROMPT,
        )

    messages.append({"role": "user", "content": texto})

    try:
        bot_raw = enviar_mensagem(messages, _com_tools=False, max_tokens=384 if modo_rapido else 640, modo_rapido=modo_rapido)
        print(f"🤖 [IA] Resposta bruta recebida (tamanho {len(str(bot_raw))} chars)")

        bot_raw_corrigido = _corrigir_saida_malformada_da_ia(t, bot_raw)
        if bot_raw_corrigido:
            try:
                _registrar_autocorrecao_virtual(
                    "ia",
                    "saida malformada",
                    "saida reformatada para json valido",
                    "segunda passada de autocorreção da resposta da IA",
                )
            except Exception as e_reg:
                print(f"⚠️ [AUTOCORREÇÃO] falha ao registrar correção da saída: {e_reg}")
            bot_raw = bot_raw_corrigido
            print("🍪 [AUTOCORREÇÃO] Saída da IA refeita em JSON válido antes de executar.")

        fala_limpa, comandos = limpar_resposta_da_ia(bot_raw)
        tipo_interacao = extrair_tipo_interacao_da_ia(bot_raw)
        fala_limpa = _construir_fala_conversa(fala_limpa, t, tipo_interacao, comandos)
        print(f"✨ [IA] Fala limpa: '{fala_limpa}' | Tipo: {tipo_interacao or 'legado'} | Comandos: {len(comandos)}")
        aprendizados_salvos = salvar_aprendizados_da_ia(bot_raw)

        if tipo_interacao in {"aprendizado", "conversa"} and comandos:
            _acoes_bloqueadas_tipo = [str(c.get("acao", "")) for c in comandos if isinstance(c, dict)]
            print(
                f"🧠 [INTENÇÃO] tipo={tipo_interacao}; bloqueando "
                f"{len(comandos)} comando(s): {_acoes_bloqueadas_tipo}"
            )
            comandos = []

        # ── INJETOR DE TARGET PC B ─────────────────────────────────────────────
        # Se o usuário mencionou 'PC B' na mensagem, força target:pc_b em todos
        # os comandos que suportam destino — independente do que a IA gerou.
        _MENCOES_PC_B = ["pc b", "pc_b", "computador b", "no b", "pro b", "pra b"]
        _usuario_pediu_pc_b = any(m in t.lower() for m in _MENCOES_PC_B)
        _ACOES_COM_TARGET = {
            "open_url", "youtube_search", "youtube_control", "open_app", "close_app",
            "organizar_desktop", "capturar_tela", "volume_up", "volume_down",
            "volume_set", "volume_mute", "parar_midia", "tocar_playlist",
            "close_tab", "close_specific_tab", "notificar", "criar_pasta",
        }
        if _usuario_pediu_pc_b and isinstance(comandos, list):
            for _cmd in comandos:
                if isinstance(_cmd, dict):
                    _acao_cmd = str(_cmd.get("acao", "")).strip()
                    # Só injeta se a ação suporta target E o target ainda não foi definido
                    if _acao_cmd in _ACOES_COM_TARGET and not _cmd.get("target"):
                        _cmd["target"] = "pc_b"
            print(f"🎯 [PC B] Target injetado em {len(comandos)} comando(s) — usuário pediu PC B.")
        # ── FIM INJETOR DE TARGET ──────────────────────────────────────────────

        # 1. Fala da Laylay (Aguardará o sucesso da execução para não mentir)
        fala_limpa_original = fala_limpa
        if not comandos and tipo_interacao in {"conversa", "", "confirmacao"}:
            _atualizar_memoria_topicos(t, fala_limpa_original)

        erros_execucao: list = []
        fala_emitida_por_acao = False
        fala_ja_emitida = False
        _fala_salva_no_inicio = False

        if not comandos and processar_comando_deterministico(t, "pos-ia-0-comandos"):
            return

        contexto_dispatch = {
            "messages": messages,
            "current_emotion": current_emotion,
            "emotion_level": emotion_level,
            "falar_com_lipsync": falar_com_lipsync,
            "salvar_memoria": salvar_memoria,
            "enviar_comando_chrome": enviar_comando_chrome,
            "validar_e_enviar_comando": validar_e_enviar_comando,
            "ajustar_volume_sistema": ajustar_volume_sistema,
            "ajustar_volume_sistema_relativo": ajustar_volume_sistema_relativo,
            "abrir_programa": abrir_programa,
            "fechar_programa": fechar_programa,
            "is_valid_url": is_valid_url,
            "formatar_url_ou_busca": formatar_url_ou_busca,
            "playlists_carregadas": playlists_carregadas,
            "_enviar_pc_b": _enviar_pc_b,
            "_detectar_foco_app_local": _detectar_foco_app_local,
            "_normalizar_query_musical": _normalizar_query_musical,
            "_limpar_nome_playlist": _limpar_nome_playlist,
            "_playlist_shuffle_start": _playlist_shuffle_start,
            "_buscar_primeiro_video_youtube": _buscar_primeiro_video_youtube,
            "_buscar_videos_youtube_fila": _buscar_videos_youtube_fila,
            "_playlist_item_at": _playlist_item_at,
            "add_to_playlist_url": add_to_playlist_url,
            "solicitar_aba_ativa": solicitar_aba_ativa,
            "_yt_clean_title": _yt_clean_title,
            "listar_abas_chrome": listar_abas_chrome,
            "listar_programas_abertos": listar_programas_abertos,
            "organizar_janelas_robusto": organizar_janelas_robusto,
            "ativar_tela_cheia_robusta": ativar_tela_cheia_robusta,
            "criar_pasta": criar_pasta,
            "criar_ou_editar_arquivo": criar_ou_editar_arquivo,
            "deletar_item": deletar_item,
            "registrar_memoria_visual": registrar_memoria_visual,
            "_capturar_tela_base64": _capturar_tela_base64,
            "_analisar_com_groq": _analisar_com_groq,
            "_obter_contexto_perceptivo": _obter_contexto_perceptivo,
            "_agendamentos_load": _agendamentos_load,
            "_agendamentos_save": _agendamentos_save,
            "_fala_agendamentos_estilosa": _fala_agendamentos_estilosa,
            "_gmail_nao_lidos_cache": _gmail_nao_lidos_cache,
            "_gmail_buscar_nao_lidos": _gmail_buscar_nao_lidos,
            "_gmail_falar_resumo_estiloso": _gmail_falar_resumo_estiloso,
            "ws_loop": ws_loop,
            "broadcast_command": broadcast_command,
            "_abas_sugeridas_fechar": _abas_sugeridas_fechar,
            "_executar_exec": _executar_exec,
            "processar_comando_deterministico": processar_comando_deterministico,
            "limpar_resposta_da_ia": limpar_resposta_da_ia,
            "_registrar_autoaprimoramento": _registrar_autoaprimoramento,
            "_registrar_autocorrecao_virtual": _registrar_autocorrecao_virtual,
            "_autorizar_acao_pratica": _autorizar_acao_pratica,
            "_autonomia_permite_execucao_musical": _autonomia_permite_execucao_musical,
            "_falhas_consecutivas": _falhas_consecutivas,
            "MAX_TENTATIVAS_AUTOCORRECAO": MAX_TENTATIVAS_AUTOCORRECAO,
            "_playlists_load": _playlists_load,
            "texto": texto,
        }
        resultado_dispatch = _executar_comandos_json_mente(
            contexto_dispatch,
            texto,
            comandos,
            fala_limpa_original,
            tipo_interacao,
            fala_ja_emitida,
            fala_emitida_por_acao,
            _fala_salva_no_inicio,
        )
        erros_execucao = list(resultado_dispatch.get("erros", erros_execucao) or [])
        fala_emitida_por_acao = bool(resultado_dispatch.get("fala_emitida_por_acao", fala_emitida_por_acao))
        fala_ja_emitida = bool(resultado_dispatch.get("fala_ja_emitida", fala_ja_emitida))
        _fala_salva_no_inicio = bool(resultado_dispatch.get("fala_salva_no_inicio", _fala_salva_no_inicio))

        contexto_finalizacao = {
            "messages": messages,
            "current_emotion": current_emotion,
            "emotion_level": emotion_level,
            "enviar_mensagem": enviar_mensagem,
            "limpar_resposta_da_ia": limpar_resposta_da_ia,
            "falar_com_lipsync": falar_com_lipsync,
            "salvar_memoria": salvar_memoria,
            "_registrar_autoaprimoramento": _registrar_autoaprimoramento,
            "_registrar_autocorrecao_virtual": _registrar_autocorrecao_virtual,
            "_falhas_consecutivas": _falhas_consecutivas,
            "MAX_TENTATIVAS_AUTOCORRECAO": MAX_TENTATIVAS_AUTOCORRECAO,
        }
        _finalizar_execucao_resposta_ia_mente(
            contexto_finalizacao,
            comandos or [],
            erros_execucao,
            fala_limpa_original,
            fala_ja_emitida,
            fala_emitida_por_acao,
            _fala_salva_no_inicio,
        )
        return

    except Exception as e:
        print(f"❌ Erro grave na geração da resposta IA: {e}")
        import traceback
        traceback.print_exc()


def _definir_modo_chat(ativo: bool, origem: str = "desconhecida") -> str:
    global MODO_CHAT, conversa_ativa, _ULTIMO_TOGGLE_CHAT_TS
    agora = time.time()
    if agora - float(_ULTIMO_TOGGLE_CHAT_TS or 0.0) < 0.8 and bool(ativo) == bool(MODO_CHAT):
        return "Modo chat já está no estado pedido."
    _ULTIMO_TOGGLE_CHAT_TS = agora
    MODO_CHAT = bool(ativo)
    conversa_ativa = bool(ativo)
    if MODO_CHAT:
        fala = _fala_de_confirmacao_variada("chat_on", fallback=_gerar_abertura_modo_chat())
    else:
        fala = _fala_de_confirmacao_variada("chat_off", fallback="Modo chat desativado. Voltei pro modo ação.")
    print(f"🗨️ [CHAT] {fala} | origem={origem}")
    return fala


def _gerar_abertura_modo_chat() -> str:
    """Gera uma abertura curta e variada para o modo chat."""
    global messages, current_emotion, emotion_level
    fallback = "Modo chat ativado. Agora eu fico no papo e largo os comandos por um instante."
    try:
        contexto_recente = []
        for msg in (messages or [])[-6:]:
            if isinstance(msg, dict) and str(msg.get("role") or "").lower() in {"user", "assistant"}:
                txt = str(msg.get("content") or "").strip()
                if txt:
                    contexto_recente.append({"role": str(msg.get("role") or "user"), "content": txt[:240]})
        prompt = [
            {
                "role": "system",
                "content": (
                    "Você é a Laylay. Crie uma única frase curta de abertura para quando o modo chat for ativado. "
                    "A frase deve soar natural, variar com o contexto recente e manter o jeitinho da Laylay. "
                    "Não diga que está em modo chat de forma mecânica. Não use listas. Não use markdown. "
                    "Nunca mencione empresas, nuvens, modelos, plataformas ou frases de assistente corporativa."
                ),
            }
        ]
        if contexto_recente:
            prompt.extend(contexto_recente)
        prompt.append(
            {
                "role": "user",
                "content": (
                    f"Crie a abertura do chat agora, em até 18 palavras, com emoção={current_emotion} e nível={emotion_level}."
                ),
            }
        )
        bruto = enviar_mensagem(prompt, _com_tools=False, max_tokens=80, modo_rapido=True)
        fala = _remover_prefixo_exec(limpar_resposta(bruto)).strip()
        fala = re.sub(r"\s+", " ", fala).strip(" \"'`")
        if len(fala) >= 4:
            return fala
    except Exception as e:
        print(f"⚠️ [CHAT] Falha ao gerar abertura dinâmica: {e}")
    return fallback


def _alternar_modo_chat_por_hotkey(ativo: bool) -> None:
    try:
        fala = _definir_modo_chat(ativo, origem="hotkey")
        falar_com_lipsync(fala, "calma", 1)
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


            # ====================== GMAIL IMAP — FUNÇÕES ======================

def _gmail_decodificar_header(valor: str) -> str:
    """Decodifica headers de email (Base64, quoted-printable, UTF-8 etc.)."""
    if not valor:
        return ""
    try:
        partes = _email_header.decode_header(valor)
        resultado = []
        for parte, charset in partes:
            if isinstance(parte, bytes):
                charset = charset or "utf-8"
                try:
                    resultado.append(parte.decode(charset, errors="replace"))
                except Exception:
                    resultado.append(parte.decode("utf-8", errors="replace"))
            else:
                resultado.append(str(parte))
        return " ".join(resultado).strip()
    except Exception:
        return str(valor)


def _gmail_extrair_remetente(from_raw: str) -> str:
    """Extrai nome ou email limpo do campo From."""
    decoded = _gmail_decodificar_header(from_raw)
    m = re.match(r'^"?([^"<]+)"?\s*<', decoded)
    if m:
        return m.group(1).strip()
    m2 = re.match(r'([^@<]+)[@<]', decoded)
    if m2:
        return m2.group(1).strip()
    return decoded[:40]


def _gmail_e_prioritario(remetente: str, assunto: str) -> bool:
    """Verifica se o email é de remetente prioritário ou tem assunto urgente."""
    rem_lower    = remetente.lower()
    if any(s in rem_lower for s in _gmail_remetentes_silenciados):
        return False
    assunto_lower = assunto.lower()
    for p in GMAIL_PRIORITARIOS:
        if p.lower() in rem_lower:
            return True
    for palavra in GMAIL_PALAVRAS_URGENTES:
        if palavra in assunto_lower:
            return True
    return False


def _gmail_carregar_ids_vistos():
    """Carrega UIDs já vistos do disco (persiste entre reinicializações)."""
    global _gmail_ids_vistos
    try:
        if os.path.exists(GMAIL_ARQUIVO):
            with open(GMAIL_ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            _gmail_ids_vistos = set(dados.get("ids_vistos", []))
    except Exception:
        pass


def _gmail_salvar_ids_vistos():
    """Salva UIDs vistos no disco."""
    try:
        ids_lista = list(_gmail_ids_vistos)[-500:]
        silenciados = sorted(list(_gmail_remetentes_silenciados))[:200]
        with open(GMAIL_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump({"ids_vistos": ids_lista, "remetentes_silenciados": silenciados}, f)
    except Exception:
        pass


def _gmail_carregar_remetentes_silenciados():
    global _gmail_remetentes_silenciados
    try:
        if os.path.exists(GMAIL_ARQUIVO):
            with open(GMAIL_ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            rems = dados.get("remetentes_silenciados", [])
            if isinstance(rems, list):
                _gmail_remetentes_silenciados = {str(x).strip().lower() for x in rems if str(x).strip()}
    except Exception:
        pass


def _gmail_silenciar_remetente(remetente: str) -> bool:
    rem = str(remetente or "").strip().lower()
    if not rem:
        return False
    _gmail_remetentes_silenciados.add(rem)
    _gmail_salvar_ids_vistos()
    return True


_gmail_carregar_remetentes_silenciados()


def _gmail_buscar_nao_lidos() -> list:
    """
    Conecta no Gmail via IMAP SSL e retorna lista de emails não lidos.
    Cada item: {"uid": str, "remetente": str, "assunto": str, "prioritario": bool}
    Retorna [] em caso de falha (offline, senha errada, timeout) — silêncio total.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or "xxxx" in GMAIL_APP_PASSWORD or "seu.email" in GMAIL_USER:
        return []

    if imaplib is None:
        print("⚠️ [Gmail] imaplib não disponível.")
        return []

    emails = []
    try:
        conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        conn.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        conn.select("INBOX", readonly=True)

        _, data = conn.search(None, "UNSEEN")
        ids_bytes = data[0].split() if data[0] else []
        ids_recentes = ids_bytes[-20:]  # busca até 20, filtra depois

        for uid_bytes in reversed(ids_recentes):
            uid = uid_bytes.decode()
            _, msg_data = conn.fetch(uid_bytes, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
            if not msg_data or not msg_data[0]:
                continue

            raw_header = bytes(msg_data[0][1])  # type: ignore  # IMAP retorna bytes | int; cast garante bytes
            msg = _email_lib.message_from_bytes(raw_header)

            remetente   = _gmail_extrair_remetente(msg.get("From", ""))
            assunto     = _gmail_decodificar_header(msg.get("Subject", "(sem assunto)"))
            prioritario = _gmail_e_prioritario(remetente, assunto)

            emails.append({
                "uid":         uid,
                "remetente":   remetente or "desconhecido",
                "assunto":     assunto or "(sem assunto)",
                "prioritario": prioritario,
                "silenciado":   any(s in (remetente or "").lower() for s in _gmail_remetentes_silenciados),
            })

        conn.logout()
    except imaplib.IMAP4.error as e:
        print(f"⚠️ [Gmail] Erro IMAP (credenciais?): {e}")
    except OSError:
        pass   # offline — silêncio total
    except Exception as e:
        print(f"⚠️ [Gmail] Erro inesperado: {e}")

    return emails


def _gmail_falar_email(email_dict: dict, prefixo: str = ""):
    """Monta e fala a notificação de um email."""
    rem      = email_dict["remetente"]
    ass      = email_dict["assunto"]
    if email_dict.get("silenciado"):
        return
    ass_curto = ass if len(ass) <= 60 else ass[:57] + "..."

    if email_dict["prioritario"]:
        texto = f"{prefixo}Email importante de {rem}: {ass_curto}."
        emocao = "debochada"
    else:
        texto = f"{prefixo}Email de {rem}: {ass_curto}."
        emocao = "calma"

    _continuidades_set("email_sugestao_pendente", {"remetente": str(rem or "").strip(), "ts": time.time()})
    _agendar_fala_proativa("emails", texto, emocao, 1)


def _gmail_falar_resumo_estiloso(emails: list, somente_prioritarios: bool = False):
    """Lê emails como um briefing curto da Laylay, não como lista numerada."""
    emails = [e for e in (emails or []) if not (isinstance(e, dict) and e.get("silenciado"))]
    if not emails:
        texto = "Nada novo no email, Pedro. A caixa postal tá quieta por enquanto."
        _continuidades_set("email_sugestao_pendente", None)
        _agendar_fala_proativa("emails", texto, "calma", 1)
        return texto

    selecionados = list(emails or [])[:GMAIL_MAX_LIDOS]
    prioritarios = [e for e in selecionados if e.get("prioritario")]
    normais = [e for e in selecionados if not e.get("prioritario")]

    def _limpar_assunto(s: str) -> str:
        s = re.sub(r"\s+", " ", str(s or "(sem assunto)").strip())
        s = s.replace("FW:", "").replace("Fwd:", "").strip()
        return s[:72] + "..." if len(s) > 75 else s

    def _resumo_email(e: dict) -> str:
        rem = str(e.get("remetente") or "alguém misterioso").strip()
        ass = _limpar_assunto(e.get("assunto") or "")
        if e.get("prioritario"):
            return f"{rem}: {ass}"
        return f"{rem}: {ass}"

    partes = []
    total = len(selecionados)
    if somente_prioritarios:
        abertura = f"Tem {total} email importante esperando tua atenção."
    elif prioritarios:
        abertura = f"Tem {total} email novo, sendo {len(prioritarios)} importante(s)."
    else:
        abertura = f"Tem {total} email novo."
    partes.append(abertura)

    destaques = prioritarios[:2] + normais[: max(0, 4 - len(prioritarios[:2]))]
    if destaques:
        partes.append("Resumo: " + "; ".join(_resumo_email(e) for e in destaques) + ".")

    restantes = total - len(destaques)
    if restantes > 0:
        partes.append(f"E ainda tem mais {restantes} aguardando na fila.")

    texto = " ".join(partes)
    _continuidades_set("email_sugestao_pendente", {"remetente": "", "ts": time.time()})
    _agendar_fala_proativa("emails", texto, "debochada" if prioritarios else "calma", 1)
    return texto


def gmail_daemon():
    """
    Thread daemon que verifica Gmail a cada GMAIL_INTERVALO_S segundos.
    Anuncia emails novos prioritários em voz alta.
    Emails não-prioritários ficam em cache para consulta por voz.
    Qualquer falha → silêncio total, tenta de novo no próximo ciclo.
    """
    global _gmail_ultimo_check, _gmail_nao_lidos_cache

    _gmail_carregar_ids_vistos()
    time.sleep(8)   # espera o startup terminar antes de fazer qualquer requisição
    print(f"📧 [Gmail] Daemon iniciado — verificando a cada {GMAIL_INTERVALO_S // 60}min")

    while True:
        try:
            agora = time.time()
            if agora - _gmail_ultimo_check < GMAIL_INTERVALO_S:
                time.sleep(30)
                continue

            _gmail_ultimo_check = agora
            print("📧 [Gmail] Verificando caixa de entrada...")

            emails = _gmail_buscar_nao_lidos()
            if not emails:
                time.sleep(30)
                continue

            _gmail_nao_lidos_cache = emails

            # Filtra emails que ainda não foram anunciados
            novos = [e for e in emails if e["uid"] not in _gmail_ids_vistos]
            if not novos:
                print(f"📧 [Gmail] {len(emails)} não lidos, nenhum novo para anunciar")
                time.sleep(30)
                continue

            # Não interrompe a fala atual
            if is_speaking:
                time.sleep(10)
                continue

            # Separa prioritários dos normais
            prioritarios = [e for e in novos if e["prioritario"]]
            normais      = [e for e in novos if not e["prioritario"]]

            # Anuncia SEMPRE os prioritários (um por um)
            for e in prioritarios[:GMAIL_MAX_LIDOS]:
                _gmail_falar_email(e)
                _gmail_ids_vistos.add(e["uid"])
                time.sleep(1.5)

            # Agrupa os normais em uma única frase para não virar spam de voz
            normais_novos = [e for e in normais if e["uid"] not in _gmail_ids_vistos]
            if normais_novos:
                n = len(normais_novos)
                if n == 1:
                    _gmail_falar_email(normais_novos[0])
                    _gmail_ids_vistos.add(normais_novos[0]["uid"])
                else:
                    _continuidades_set("email_sugestao_pendente", {"remetente": "", "ts": time.time()})
                    _agendar_fala_proativa(
                        "emails",
                        f"Você tem {n} emails novos. Fala 'lê os emails' pra ouvir.",
                        "calma", 1
                    )
                    for e in normais_novos:
                        _gmail_ids_vistos.add(e["uid"])

            _gmail_salvar_ids_vistos()

        except Exception as e:
            print(f"❌ [Gmail] Erro no daemon: {e}")

        time.sleep(30)

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
