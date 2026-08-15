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
from typing import Any, Mapping

from mente_laylay.integracao.instancia_unica import adquirir_instancia_unica


_instancia_unica_runtime = adquirir_instancia_unica(
    sys.executable if getattr(sys, "frozen", False) else __file__
)
if not _instancia_unica_runtime.adquirida:
    print("⚠️ [INICIALIZAÇÃO] A Laylay já está aberta. Não iniciei uma segunda instância.")
    raise SystemExit(0)
atexit.register(_instancia_unica_runtime.liberar)


def _carregar_configuracao_portatil() -> None:
    """Carrega configurações ao lado do executável sem sobrescrever o Windows."""
    raiz = (
        os.path.abspath(os.path.dirname(sys.executable))
        if getattr(sys, "frozen", False)
        else os.path.abspath(os.path.dirname(__file__))
    )
    caminho = os.path.join(raiz, "configuracao.env")
    try:
        with open(caminho, "r", encoding="utf-8-sig") as arquivo:
            for linha in arquivo:
                texto = linha.strip()
                if not texto or texto.startswith("#") or "=" not in texto:
                    continue
                chave, valor = texto.split("=", 1)
                chave = chave.strip()
                valor = valor.strip().strip('"').strip("'")
                if chave and chave.replace("_", "").isalnum():
                    os.environ.setdefault(chave, valor)
    except FileNotFoundError:
        pass
    except OSError as erro:
        print(f"⚠️ [CONFIGURAÇÃO] não consegui ler configuracao.env: {erro}")
    # A chave configurada pela interface vive fora do projeto e é protegida
    # pelo DPAPI. Variáveis externas continuam tendo precedência.
    try:
        from mente_laylay.integracao.configuracao_aplicacao import (
            carregar_segredo_no_ambiente,
        )

        carregar_segredo_no_ambiente()
    except Exception as erro:
        print(
            "⚠️ [CONFIGURAÇÃO] credencial protegida indisponível: "
            f"{type(erro).__name__}."
        )


_carregar_configuracao_portatil()
if os.environ.get("LAYLAY_SMOKE_DISTRIBUICAO", "").casefold() in {"1", "true", "sim"}:
    from mente_laylay.integracao.smoke_distribuicao import main as _smoke_distribuicao_main

    raise SystemExit(_smoke_distribuicao_main(os.path.dirname(sys.executable)))
from mente_laylay.autonomia.comandos_sistema import (
    abrir_programa as _abrir_programa_mente,
    fechar_programa as _fechar_programa_mente,
)
from mente_laylay.autonomia.composicao_ciclo_comandos import (
    criar_composicao_ciclo_comandos_runtime as _criar_composicao_ciclo_comandos_runtime,
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
    escrever_arquivo_texto_seguro as _escrever_arquivo_texto_seguro_mente,
    mapear_pastas_principais as _mapear_pastas_principais_mente,
    mover_arquivo as _mover_arquivo_mente,
    renomear_arquivo as _renomear_arquivo_mente,
    resolver_caminho as _resolver_caminho_mente,
)
from mente_laylay.arquivos.pesquisa_semantica import (
    criar_pesquisa_semantica_arquivos_runtime as _criar_pesquisa_semantica_arquivos_runtime,
)
from mente_laylay.arquivos.mutacoes import (
    criar_arquivos_mutacao_runtime as _criar_arquivos_mutacao_runtime,
)
from mente_laylay.arquivos.lixeira_laylay import (
    configurar_pendencia_exclusao as _configurar_pendencia_exclusao,
)
from mente_laylay.integracao.registro_arquivos import (
    registrar_arquivos_leitura as _registrar_arquivos_leitura,
)
from mente_laylay.integracao.registro_mutacoes_arquivos import (
    registrar_arquivos_mutacao as _registrar_arquivos_mutacao,
)
from mente_laylay.integracao.reinicio_processo import construir_argumentos_reinicio
from mente_laylay.integracao.registro_musica import (
    registrar_musica_leitura as _registrar_musica_leitura,
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
    fechar_janela_por_titulo as _fechar_janela_por_titulo_mente,
    focar_janela as _focar_janela_mente,
    janela_esta_em_foco as _janela_esta_em_foco_mente,
    janela_em_tela_cheia as _janela_em_tela_cheia_mente,
    listar_programas_abertos as _listar_programas_abertos_mente,
    observar_programas_abertos as _observar_programas_abertos_mente,
    maximizar_janela as _maximizar_janela_mente,
    normalizar_alvo_ambiente as _normalizar_alvo_ambiente_mente,
    organizar_janelas as _organizar_janelas_mente,
    planejar_organizacao_janelas as _planejar_organizacao_janelas_mente,
    pid_from_hwnd as _pid_from_hwnd_mente,
    resolver_alvo_ambiente as _resolver_alvo_ambiente_mente,
)
from mente_laylay.memoria_mental.estado_compartilhado_runtime import (
    criar_estado_compartilhado_runtime as _criar_estado_compartilhado_runtime_mente,
)
from mente_laylay.memoria_mental.saude_mente import (
    criar_saude_mente_runtime as _criar_saude_mente_runtime,
)
from mente_laylay.memoria_mental.continuidade_geral import (
    registrar_evento_continuidade as _registrar_evento_continuidade_geral,
)
from mente_laylay.especialistas.mapa_habilidades import (
    criar_mapa_habilidades_runtime as _criar_mapa_habilidades_runtime,
)
from mente_laylay.especialistas.area_transferencia import (
    criar_area_transferencia_runtime as _criar_area_transferencia_runtime,
)
from mente_laylay.autonomia.orquestracao_cooperativa import (
    criar_orquestrador_cooperativo_runtime as _criar_orquestrador_cooperativo_runtime,
    criar_quadro_cooperacao_runtime as _criar_quadro_cooperacao_runtime,
)
from mente_laylay.percepcao.observador_area_transferencia import (
    classificar_resposta_oferta as _classificar_resposta_oferta_clipboard,
    criar_observador_area_transferencia_runtime as _criar_observador_area_transferencia_runtime,
    oferta_deve_ceder_a_novo_comando as _oferta_clipboard_deve_ceder,
)
from mente_laylay.memoria_mental.pendencia_acao import (
    criar_pendencia_acao_runtime as _criar_pendencia_acao_runtime,
)
from mente_laylay.memoria_mental.memoria_pessoas import (
    criar_memoria_pessoas_runtime as _criar_memoria_pessoas_runtime,
)
from mente_laylay.integracao.registro_memoria_pessoas import (
    registrar_memoria_pessoas as _registrar_memoria_pessoas,
)
from mente_laylay.especialistas.caixa_entrada_pessoal import (
    criar_caixa_entrada_pessoal_runtime as _criar_caixa_entrada_pessoal_runtime,
)
from mente_laylay.autonomia.governanca_iniciativa import (
    detectar_comando_governanca_iniciativa as _detectar_comando_governanca_iniciativa,
)
from mente_laylay.autonomia.diretor_presenca import (
    criar_diretor_presenca_runtime as _criar_diretor_presenca_runtime_mente,
)
from mente_laylay.memoria_mental.consciencia_temporal import (
    registrar_evento_visual_temporal as _registrar_evento_visual_temporal_mente,
)
from mente_laylay.memoria_mental.diagnostico_mente import (
    criar_diagnostico_mente_runtime as _criar_diagnostico_mente_runtime,
    detectar_pedido_diagnostico_mente as _detectar_pedido_diagnostico_mente,
)
from mente_laylay.memoria_mental.disponibilidade_operacional import (
    criar_disponibilidade_operacional_runtime as _criar_disponibilidade_operacional_runtime,
)
from mente_laylay.memoria_mental.observabilidade import (
    criar_observabilidade_mente_runtime as _criar_observabilidade_mente_runtime,
)
from mente_laylay.memoria_mental.implantacao_desempenho import (
    FLAGS_OTIMIZACAO as _FLAGS_OTIMIZACAO_DESEMPENHO,
    GuardiaoImplantacaoDesempenho as _GuardiaoImplantacaoDesempenho,
    flag_desempenho_ativa as _flag_desempenho_ativa,
    snapshot_flags_desempenho as _snapshot_flags_desempenho,
)
from mente_laylay.percepcao.monitor_janelas import (
    criar_monitor_janelas_runtime as _criar_monitor_janelas_runtime_mente,
)
from mente_laylay.cognicao.interpretador_semantico_runtime import (
    criar_interpretador_semantico_runtime as _criar_interpretador_semantico_runtime_mente,
)
from mente_laylay.cognicao.composicao_turno import (
    criar_composicao_turno_runtime as _criar_composicao_turno_runtime,
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
from mente_laylay.percepcao.compatibilidade_overlay_jogo import (
    criar_compatibilidade_overlay_jogo_runtime as _criar_compatibilidade_overlay_jogo_runtime_mente,
)
from mente_laylay.percepcao.visao_jogo.composicao import (
    criar_composicao_visao_jogo_runtime as _criar_composicao_visao_jogo_runtime,
)
from mente_laylay.percepcao.visao_jogo.coordenador import (
    criar_coordenador_visao_jogo_runtime as _criar_coordenador_visao_jogo_runtime,
)
from mente_laylay.percepcao.visao_jogo.portas_runtime import (
    criar_visao_jogo_analise_runtime as _criar_visao_jogo_analise_runtime,
    criar_visao_jogo_leitura_runtime as _criar_visao_jogo_leitura_runtime,
)
from mente_laylay.integracao.registro_visao_jogo import (
    registrar_visao_jogo_analise as _registrar_visao_jogo_analise,
    registrar_visao_jogo_leitura as _registrar_visao_jogo_leitura,
)
from mente_laylay.integracao.registro_conversa_llm import (
    criar_modelo_llm_diferido_runtime as _criar_modelo_llm_diferido_runtime,
    criar_estado_conversa_runtime as _criar_estado_conversa_runtime,
    registrar_modelo_llm as _registrar_modelo_llm,
)
from mente_laylay.integracao.desktop_bridge import (
    criar_desktop_bridge_runtime as _criar_desktop_bridge_runtime,
)
from mente_laylay.integracao.roteiro_teste_conversa import (
    RoteiroTesteConversaRuntime as _RoteiroTesteConversaRuntime,
    carregar_configuracao_roteiro as _carregar_configuracao_roteiro,
    instalar_espelho_terminal as _instalar_espelho_terminal_roteiro,
    preparar_diretorio_resultado as _preparar_diretorio_resultado_roteiro,
)
from mente_laylay.integracao.dashboard_terminal import (
    criar_dashboard_terminal_runtime as _criar_dashboard_terminal_runtime,
)
from mente_laylay.integracao.letras_lrclib import (
    criar_letras_lrclib_runtime as _criar_letras_lrclib_runtime,
)
from mente_laylay.percepcao.telemetria_gpu import (
    criar_telemetria_gpu_runtime as _criar_telemetria_gpu_runtime,
)
from mente_laylay.percepcao.telemetria_rede import (
    criar_telemetria_rede_runtime as _criar_telemetria_rede_runtime,
)
from mente_laylay.integracao.acoes_painel_runtime import (
    executar_acao_painel_tipado as _executar_acao_painel_tipado,
)
from mente_laylay.integracao.configuracao_aplicacao import (
    criar_configuracao_aplicacao_runtime as _criar_configuracao_aplicacao_runtime,
)
from mente_laylay.integracao.composicao_principal import (
    criar_registros_principais as _criar_registros_principais,
)
from mente_laylay.integracao.ponte_clipboard_aplicacao import (
    criar_ponte_clipboard_aplicacao_runtime as _criar_ponte_clipboard_aplicacao_runtime,
)
from mente_laylay.integracao.ponte_iniciativa_aplicacao import (
    criar_ponte_iniciativa_aplicacao_runtime as _criar_ponte_iniciativa_aplicacao_runtime,
)
from mente_laylay.integracao.ponte_cooperacao_aplicacao import (
    criar_ponte_cooperacao_aplicacao_runtime as _criar_ponte_cooperacao_aplicacao_runtime,
)
from mente_laylay.integracao.registro_servicos_aplicacao import (
    criar_registro_servicos_aplicacao_runtime as _criar_registro_servicos_aplicacao_runtime,
)
from mente_laylay.integracao.adaptadores_composicao import (
    agendar_entrada_canonica as _agendar_entrada_canonica_mente,
    avaliar_evento_emocional_operacional as _avaliar_evento_emocional_operacional_mente,
    definir_atividade_visual as _definir_atividade_visual_mente,
    descarregar_modelo_local as _descarregar_modelo_local_integracao,
    entregar_briefing_inicial as _entregar_briefing_inicial_mente,
    observar_evento_pendencia_agenda as _observar_evento_pendencia_agenda_mente,
    publicar_curadoria_musical_cooperativa as _publicar_curadoria_musical_cooperativa_mente,
    registrar_memoria_visual_integrada as _registrar_memoria_visual_integrada_mente,
    salvar_identidade_usuario as _salvar_identidade_usuario_mente,
)
from mente_laylay.cognicao.intencao_visual_jogo import (
    detectar_pedido_visao_jogo as _detectar_pedido_visao_jogo_cooperativo,
)
from mente_laylay.autonomia.governanca_iniciativa import (
    decisao_permite_emissao as _decisao_permite_emissao_iniciativa,
)
from mente_laylay.percepcao.visao_jogo.sessao_jogo import identificar_jogo
from mente_laylay.percepcao.ouvido_whisper import (
    criar_ouvido_whisper_runtime as _criar_ouvido_whisper_runtime_mente,
    limpar_diccao_e_ruido as _limpar_diccao_e_ruido_mente,
)
from mente_laylay.percepcao.saidas_audio_windows import GerenciadorSaidasAudioWindows
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
    selecionar_fala_inicial as _selecionar_fala_inicial_ambiente,
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
from mente_laylay.memoria_mental.identidade_usuario import (
    salvar_nome_usuario_confirmado as _salvar_nome_usuario_confirmado_mente,
)
from mente_laylay.memoria_mental.mapa_recursos import (
    criar_mapa_recursos_runtime as _criar_mapa_recursos_runtime,
)
from mente_laylay.memoria_mental.rede_associativa import (
    criar_rede_associativa_runtime as _criar_rede_associativa_runtime_mente,
)
from mente_laylay.memoria_mental.resumo_diario import (
    MemoriaLaylay as _MemoriaLaylayRuntime,
)
from mente_laylay.memoria_mental.playlist_mental import (
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
from mente_laylay.memoria_mental.operacoes_musicais_runtime import (
    criar_operacoes_musicais_runtime as _criar_operacoes_musicais_runtime_mente,
)
from mente_laylay.memoria_mental.consulta_musical import (
    criar_consulta_musical_runtime as _criar_consulta_musical_runtime_mente,
)
from mente_laylay.integracao.registro_operacoes_musicais import (
    registrar_operacoes_musicais as _registrar_operacoes_musicais,
)
from mente_laylay.integracao.navegador_runtime import (
    criar_navegador_leitura_runtime as _criar_navegador_leitura_runtime,
    criar_navegador_operacoes_runtime as _criar_navegador_operacoes_runtime,
)
from mente_laylay.integracao.registro_navegador import (
    registrar_navegador_leitura as _registrar_navegador_leitura,
    registrar_navegador_operacoes as _registrar_navegador_operacoes,
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
    resolver_vozes_tts as _resolver_vozes_tts_mente,
)
from mente_laylay.personalidade.oralidade import (
    preparar_texto_para_tts as _preparar_texto_para_tts_mente,
)
from mente_laylay.personalidade.orquestrador_fala_runtime import (
    criar_orquestrador_fala_runtime as _criar_orquestrador_fala_runtime_mente,
)
from mente_laylay.personalidade.composicao_resposta_conversacional import (
    criar_composicao_resposta_conversacional_runtime as _criar_composicao_resposta_conversacional_runtime,
)
from mente_laylay.personalidade.abertura_chat import (
    criar_abertura_chat_runtime as _criar_abertura_chat_runtime_mente,
)
from mente_laylay.personalidade.prompt_base import ALLOWED_ACTIONS
from mente_laylay.personalidade.prompt_voz_unica import BASE_SYSTEM_PROMPT
from mente_laylay.personalidade.politica_voz_unica import voz_unica_llm_ativa
from mente_laylay.personalidade.conversa_natural import (
    criar_conversa_natural_runtime as _criar_conversa_natural_runtime_mente,
    fala_e_fallback_neutro as _fala_e_fallback_neutro_mente,
)
from mente_laylay.autonomia.execucao_ia import (
    criar_coordenador_exec_runtime as _criar_coordenador_exec_runtime_mente,
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
    obter_volume_sistema as _obter_volume_sistema_mente,
    definir_mudo_sistema as _definir_mudo_sistema_mente,
    ducking_volume as _ducking_volume_mente,
    listar_processos_com_audio_ativo as _listar_processos_audio_ativos_mente,
)
from mente_laylay.autonomia.fluxo_resposta_ia import (
    processar_inicio_fluxo_resposta_ia as _processar_inicio_fluxo_resposta_ia_mente,
)
from mente_laylay.autonomia.modo_chat import (
    criar_interacao_chat_runtime as _criar_interacao_chat_runtime_mente,
    criar_modo_chat_runtime as _criar_modo_chat_runtime_mente,
)
from mente_laylay.autonomia.servicos_background import (
    criar_gerenciador_servicos_background as _criar_gerenciador_servicos_background_mente,
    criar_orquestrador_inicializacao as _criar_orquestrador_inicializacao_mente,
)
from mente_laylay.autonomia.porteiro_chrome import (
    criar_porteiro_chrome_runtime as _criar_porteiro_chrome_runtime_mente,
)
from mente_laylay.integracao.composicao_entrada_interacao import (
    criar_composicao_entrada_interacao_runtime as _criar_composicao_entrada_interacao_runtime,
)
from mente_laylay.integracao.composicao_estado_aplicacao import (
    criar_composicao_estado_aplicacao_runtime as _criar_composicao_estado_aplicacao_runtime,
)
from mente_laylay.autonomia.motor_temporal import (
    criar_motor_temporal_runtime as _criar_motor_temporal_runtime_mente,
)
from mente_laylay.autonomia.motor_iniciativa import (
    criar_motor_iniciativa_runtime as _criar_motor_iniciativa_runtime_mente,
)
from mente_laylay.autonomia.executor_acoes_autonomas import (
    criar_executor_acoes_autonomas_runtime as _criar_executor_acoes_autonomas_runtime,
)
from mente_laylay.autonomia.composicao_servicos import (
    criar_composicao_servicos_padrao as _criar_composicao_servicos_padrao,
)
from mente_laylay.autonomia.coordenador_oportunidades import (
    criar_coordenador_oportunidades_runtime as _criar_coordenador_oportunidades_runtime_mente,
)
from mente_laylay.integracao.composicao_contextos_ia import (
    criar_composicao_contextos_ia_runtime as _criar_composicao_contextos_ia_runtime,
)
from mente_laylay.integracao.composicao_inteligencia_externa import (
    criar_composicao_inteligencia_externa_runtime as _criar_composicao_inteligencia_externa_runtime,
)
from mente_laylay.integracao.runtime_llm_portatil import (
    criar_runtime_llm_portatil as _criar_runtime_llm_portatil,
)
from mente_laylay.integracao.orcamento_llm_turno import (
    criar_orcamento_llm_turno_runtime as _criar_orcamento_llm_turno_runtime,
)
from mente_laylay.iot.composicao import (
    criar_composicao_iot_laylay_runtime as _criar_composicao_iot_laylay_runtime,
)
from mente_laylay.integracao.registro_iot import registrar_iot as _registrar_iot
from mente_laylay.integracao.pc_b_integracao import (
    criar_destino_pc_runtime as _criar_destino_pc_runtime_mente,
    criar_pc_b_runtime as _criar_pc_b_runtime_mente,
)
from mente_laylay.integracao.composicao_chrome_comandos import (
    criar_composicao_chrome_comandos_laylay_runtime as _criar_composicao_chrome_comandos_laylay_runtime,
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
    criar_websocket_transport_runtime as _criar_websocket_transport_runtime_mente,
    fechar_extensoes_anteriores as _fechar_extensoes_anteriores_chrome_mente,
)
from mente_laylay.integracao.composicao_chrome_ws import (
    criar_composicao_chrome_ws_laylay_runtime as _criar_composicao_chrome_ws_laylay_runtime,
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
from mente_laylay.integracao.composicao_visual import (
    criar_composicao_visual_laylay_runtime as _criar_composicao_visual_laylay_runtime,
)
from mente_laylay.integracao.composicao_gmail import (
    criar_composicao_gmail_laylay_runtime as _criar_composicao_gmail_laylay_runtime,
)
from mente_laylay.integracao.politicas_composicao import (
    aprender_conteudo_area_transferencia as _aprender_conteudo_area_transferencia_mente,
    aprender_pesquisa_semantica_arquivos as _aprender_pesquisa_semantica_arquivos_mente,
    construir_estado_visual as _construir_estado_visual_mente,
    observar_conteudo_area_transferencia as _observar_conteudo_area_transferencia_mente,
    observar_item_caixa_entrada as _observar_item_caixa_entrada_mente,
    recomendar_playlist_real_para_presenca as _recomendar_playlist_real_para_presenca_mente,
    registrar_feedback_agenda as _registrar_feedback_agenda_mente,
)
from mente_laylay.cognicao.fundamentacao_factual import (
    extrair_tema_fundamentacao as _extrair_tema_fundamentacao_mente,
    montar_fundamentacao as _montar_fundamentacao_mente,
)
from mente_laylay.cognicao.resumo_conteudo import (
    criar_resumo_conteudo_runtime as _criar_resumo_conteudo_runtime_mente,
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
from mente_laylay.cognicao.investigacao_erro import InvestigadorErroRuntime
from mente_laylay.autonomia.central_notificacoes import (
    criar_central_notificacoes_runtime as _criar_central_notificacoes_runtime_mente,
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
from mente_laylay.emocoes.avaliador_eventos import (
    criar_avaliador_eventos_emocionais_runtime as _criar_avaliador_eventos_emocionais_runtime_mente,
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
print(
    "🧠 [BUILD:MENTE] continuidade=pendencia-canonica-v1 "
    f"arquivo={os.path.abspath(__file__)}"
)
print(
    "🧠 [VOZ ÚNICA] LLM autora da conversa | "
    f"ativa={voz_unica_llm_ativa()}"
)
import traceback
import asyncio

from memoria_sqlite import MemoriaSQLite
_composicao_resposta_conversacional_runtime = (
    _criar_composicao_resposta_conversacional_runtime(
        estado_runtime_getter=lambda: _estado_compartilhado_runtime,
        fallback_fala=FALLBACK_FALA_NEUTRA,
        log=print,
    )
)
_resposta_conversacional_runtime = _composicao_resposta_conversacional_runtime.runtime
_limpar_texto_fala_ia = _resposta_conversacional_runtime.limpar_texto_fala_ia
_atualizar_memoria_topicos = _resposta_conversacional_runtime.atualizar_memoria_topicos
_suspender_topico_conversacional = _resposta_conversacional_runtime.suspender_topico_conversacional
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
    playlist_state_getter=lambda: playlist_state,
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
)
_texto_cancela_acao_agora = _porteiro_acoes_runtime.texto_cancela_acao_agora
_bloquear_playlist_temporariamente = _porteiro_acoes_runtime.bloquear_playlist_temporariamente
_playlist_bloqueada_agora = _porteiro_acoes_runtime.playlist_bloqueada_agora
_contexto_porteiro_acoes = _porteiro_acoes_runtime.contexto
_autonomia_permite_execucao_musical = _porteiro_acoes_runtime.autonomia_permite_execucao_musical
_autorizar_acao_pratica = _porteiro_acoes_runtime.autorizar_acao_pratica


_composicao_estado_aplicacao_runtime = _criar_composicao_estado_aplicacao_runtime(
    servicos_iniciais={},
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
)
_estado_contexto_runtime = _composicao_estado_aplicacao_runtime.estado
_contexto_conversa_natural = _estado_contexto_runtime.contexto_conversa_natural
_obter_contexto_perceptivo = _estado_contexto_runtime.contexto_perceptivo
_registrar_mente_curta_base = _estado_contexto_runtime.registrar_mente_curta
_adaptadores_aplicacao_runtime = _composicao_estado_aplicacao_runtime.adaptadores
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
        "visual_activity": "idle",
        "visual_activity_until": 0.0,
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
_mapa_habilidades_runtime = _criar_mapa_habilidades_runtime(
    saude_getter=_saude_mente_runtime.snapshot,
)
_texto_parece_consulta_operacional = _mapa_habilidades_runtime.parece_consulta_operacional


def _evidencia_habilidades_turno_mente(
    texto: str,
    *,
    turno: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Entrega ao contrato apenas a projeção conversacional do catálogo vivo."""
    return _mapa_habilidades_runtime.evidencia_conversacional(
        texto,
        turno=turno,
    )


def _responder_pergunta_capacidade_local(texto: str) -> str:
    """Cruza pergunta, decisão do turno e conversa recente no catálogo vivo."""
    mente = _estado_compartilhado_runtime.mental
    memoria_conversa = _estado_compartilhado_runtime.memoria_conversa
    turno = dict(mente.get("turno_atual") or {})
    mensagens = list(memoria_conversa.get("messages") or [])
    return _mapa_habilidades_runtime.responder_pergunta_capacidade(
        texto,
        turno=turno,
        contexto={
            "mensagens": mensagens,
            "ultima_fala_usuario": str(mente.get("ultima_fala_usuario") or ""),
            "ultima_acao_intent": str(mente.get("ultima_acao_intent") or ""),
            "ultima_acao_status": str(mente.get("ultima_acao_status") or ""),
            "ultima_acao_ok": mente.get("ultima_acao_ok"),
            "ultima_acao_alvo": str(mente.get("ultima_acao_alvo") or ""),
            "ultima_acao_params": dict(mente.get("ultima_acao_params") or {}),
            "ultima_acao_ts": float(mente.get("ultima_acao_ts") or 0.0),
            "assunto": str(
                dict(mente.get("assunto_estruturado_atual") or {}).get("titulo") or ""
            ),
            "foco": str(dict(mente.get("foco_vivo") or {}).get("topico") or ""),
        },
    )
_otimizacoes_desempenho_refs: dict[str, Any] = {}


def _desativar_otimizacoes_desempenho_sessao(motivo: str) -> None:
    """Retorna ao caminho conservador sem interromper o turno atual."""
    os.environ["LAYLAY_OTIMIZACOES_DESEMPENHO"] = "0"
    for flag in _FLAGS_OTIMIZACAO_DESEMPENHO.values():
        os.environ[flag] = "0"
    orcamento = _otimizacoes_desempenho_refs.get("orcamento_llm")
    if orcamento is not None:
        orcamento.habilitado = False
    composicao_llm = _otimizacoes_desempenho_refs.get("composicao_llm")
    desativar_prompt = getattr(composicao_llm, "desativar_otimizacao_prompt", None)
    if callable(desativar_prompt):
        desativar_prompt()
    resumo = _otimizacoes_desempenho_refs.get("resumo")
    desativar_cache = getattr(resumo, "desativar_cache", None)
    if callable(desativar_cache):
        desativar_cache()
    orquestrador_fala = _otimizacoes_desempenho_refs.get("orquestrador_fala")
    bridge = _otimizacoes_desempenho_refs.get("desktop_bridge")
    remover_observador = getattr(
        orquestrador_fala, "remover_observador_fala_final", None,
    )
    publicar = getattr(bridge, "publicar_fala_final", None)
    if callable(remover_observador) and callable(publicar):
        remover_observador(publicar)
    print(
        "⚠️ [DESEMPENHO] otimizações revertidas nesta sessão | "
        f"motivo={motivo}"
    )


def _publicar_implantacao_desempenho(estado: Mapping[str, Any]) -> None:
    _estado_compartilhado_runtime.atualizar_campos(
        "mental",
        diagnostico_implantacao_desempenho={
            **_snapshot_flags_desempenho(),
            **dict(estado or {}),
        },
    )


_guardiao_implantacao_desempenho = _GuardiaoImplantacaoDesempenho(
    desativar=_desativar_otimizacoes_desempenho_sessao,
    publicar_estado=_publicar_implantacao_desempenho,
)
_observabilidade_mente_runtime = _criar_observabilidade_mente_runtime(
    estado_getter=lambda chave, padrao=None: _estado_compartilhado_runtime.obter_copia(
        "mental", chave, padrao,
    ),
    estado_setter=lambda **campos: _estado_compartilhado_runtime.atualizar_campos(
        "mental", **campos,
    ),
    log=print,
    observar_implantacao=_guardiao_implantacao_desempenho.observar,
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
_avaliador_eventos_emocionais_runtime = (
    _criar_avaliador_eventos_emocionais_runtime_mente(log=print)
)
_avaliar_evento_emocional_operacional = partial(
    _avaliar_evento_emocional_operacional_mente,
    avaliador=_avaliador_eventos_emocionais_runtime,
    definir_emocao=lambda emocao, nivel, causa: _definir_emocao_conversacional(
        emocao, nivel, causa,
    ),
    log=print,
)


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
_base_dir = (
    os.path.abspath(os.path.dirname(sys.executable))
    if getattr(sys, "frozen", False)
    else os.path.abspath(os.path.dirname(__file__))
)
_configuracao_aplicacao_runtime = _criar_configuracao_aplicacao_runtime(
    raiz=_base_dir,
)
PASTA_MEMORIA = os.path.join(_base_dir, "memoria")
_definir_atividade_visual = partial(
    _definir_atividade_visual_mente,
    atualizar_estado=lambda **campos: _estado_compartilhado_runtime.atualizar_campos(
        "conversacional", **campos,
    ),
)


_estado_visual_laylay = partial(
    _construir_estado_visual_mente,
    conversa_get=_conversa_estado_get,
    plano_get=lambda: dict(
        _estado_compartilhado_runtime.mental.get("plano_turno_atual") or {}
    ),
)


_composicao_visual_runtime = _criar_composicao_visual_laylay_runtime(
    raiz_projeto=_base_dir,
    estado_getter=_estado_visual_laylay,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    log=print,
)
_gamebar_bridge_runtime = _composicao_visual_runtime.gamebar
_avatar_runtime = _composicao_visual_runtime.avatar
atexit.register(_composicao_visual_runtime.parar)
# Agora as constantes que dependem de PASTA_MEMORIA
PLAYLISTS_ARQUIVO = "playlists.json"
PASTA_PLAYLISTS_LAYLAY = os.path.join(PASTA_MEMORIA, "playlists_laylay")
PLAYLISTS_LAYLAY_ARQUIVO = os.path.join(PASTA_PLAYLISTS_LAYLAY, "playlists_da_laylay.json")
AGENDAMENTOS_ARQUIVO = os.path.join(PASTA_MEMORIA, "agendamentos.json")

BRIEFING_ARQUIVO = os.path.join(PASTA_MEMORIA, "briefing_estado.json")
GMAIL_ARQUIVO = os.path.join(PASTA_MEMORIA, "gmail_estado.json")
CENTRAL_NOTIFICACOES_ARQUIVO = os.path.join(PASTA_MEMORIA, "central_notificacoes.json")
ROTINA_ARQUIVO_APRENDIDO = os.path.join(PASTA_MEMORIA, "rotinas_aprendidas.json")
MUSICA_ARQUIVO_HISTORICO = os.path.join(PASTA_MEMORIA, "aprendizado_musical.json")
MUSICA_ARQUIVO_FEEDBACK = os.path.join(PASTA_MEMORIA, "musicas_feedback.json")

# ====================== BRIEFING MATINAL ======================
BRIEFING_CIDADE = "Boituva"                    # ← sua cidade (muda se viajar)
_ambiente_sistema_runtime = _criar_ambiente_sistema_runtime_mente()

# ====================== GMAIL VIA IMAP (App Password) ======================
# Configure fora do código: GMAIL_USER e GMAIL_APP_PASSWORD.

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
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    registrar_evento=_observabilidade_mente_runtime.registrar_evento_servico,
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
_orcamento_llm_turno_runtime = _criar_orcamento_llm_turno_runtime(
    habilitado=_flag_desempenho_ativa("LAYLAY_ORCAMENTO_LLM_ATIVO"),
    publicar_estado=lambda estado: _estado_compartilhado_runtime.atualizar_campos(
        "mental", diagnostico_orcamento_llm=estado,
    ),
    registrar_decisao=_observabilidade_mente_runtime.registrar_decisao,
    log=print,
)
_otimizacoes_desempenho_refs["orcamento_llm"] = _orcamento_llm_turno_runtime
_modelo_llm_diferido_runtime = _criar_modelo_llm_diferido_runtime()
_registro_modelo_llm_runtime = _registrar_modelo_llm(
    _modelo_llm_diferido_runtime
)
_busca_musical_runtime = _criar_busca_musical_runtime_mente(
    extrair_resultados_youtube=(
        lambda html, query, limite=10, **kwargs:
        _extrair_resultados_youtube_busca(html, query, limite, **kwargs)
    ),
    abrir_url=lambda url: _registro_navegador_operacoes_runtime.abrir_url(url),
    youtube_play=lambda url: _registro_navegador_operacoes_runtime.tocar_youtube(url),
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    enviar_mensagem=_registro_modelo_llm_runtime.enviar,
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
# A playlist pode continuar entre reinícios, mas o player é uma observação
# efêmera da extensão. Restaurá-lo faria a faixa da sessão anterior parecer
# atual até o navegador responder novamente.
playlist_state.pop("player", None)
playlist_state.pop("tab_id", None)
_playlist_runtime = _criar_playlist_runtime_mente(
    state_file=playlists_state_file,
    legacy_file=playlists_legacy_file,
    cache={},
    ultima_playlist_getter=lambda: str(_musica_estado_get("ultima_playlist") or ""),
    ultima_playlist_setter=lambda valor: _musica_estado_set("ultima_playlist", valor),
    playlist_state=playlist_state,
    youtube_play=lambda url, target_tab_id=None: (
        _registro_navegador_operacoes_runtime.tocar_youtube_detalhado(
            url,
            tab_id=target_tab_id if isinstance(target_tab_id, int) else None,
        )
    ),
    solicitar_aba_ativa=lambda **kwargs: (
        _registro_navegador_leitura_runtime.aba_ativa(**kwargs)
    ),
    normalizar_texto=lambda texto: _normalizar_texto(texto),
    normalizar_texto_com_apelidos=lambda texto: _normalizar_texto_com_apelidos(texto),
    sincronizar_playlists_laylay=lambda: _playlist_laylay_runtime.sincronizar(),
    log=print,
)


_ponte_curadoria_cooperativa = {"publicar": None}
_publicar_curadoria_musical_cooperativa = partial(
    _publicar_curadoria_musical_cooperativa_mente,
    publicar_getter=lambda: _ponte_curadoria_cooperativa.get("publicar"),
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
    publicar_cooperacao=_publicar_curadoria_musical_cooperativa,
)
_operacoes_musicais_runtime = _criar_operacoes_musicais_runtime_mente(
    playlists_usuario=_playlist_runtime,
    playlists_laylay=_playlist_laylay_runtime,
    musica_estado_getter=_musica_estado_get,
    musica_estado_setter=_musica_estado_set,
    solicitar_aba_ativa=lambda **kwargs: (
        _registro_navegador_leitura_runtime.aba_ativa(**kwargs)
    ),
    playlist_state=playlist_state,
    log=print,
)
_registro_musica_operacoes_runtime = _registrar_operacoes_musicais(
    _operacoes_musicais_runtime
)
_consulta_musical_runtime = _criar_consulta_musical_runtime_mente(
    playlists_usuario=_playlist_runtime,
    playlists_laylay=_playlist_laylay_runtime,
    estado_getter=lambda: {
        "ultima_playlist": _musica_estado_get("ultima_playlist", ""),
        "musica_atual_titulo": _musica_estado_get("musica_atual_titulo", ""),
        "musica_atual_status": _musica_estado_get("musica_atual_status", ""),
        "playlist_state": playlist_state,
    },
)
_registro_musica_leitura_runtime = _registrar_musica_leitura(
    _consulta_musical_runtime
)
_mapa_recursos_runtime = _criar_mapa_recursos_runtime()
_mapa_recursos_runtime.registrar(
    "playlists_usuario",
    arquivo=PLAYLISTS_ARQUIVO,
    descricao="playlists reais salvas pelo usuário, com nomes, quantidades e títulos conhecidos",
    termos=(
        "playlist", "playlists", "faixas salvas", "musicas salvas",
        "músicas salvas", "arquivo playlists",
    ),
    leitor=_registro_musica_leitura_runtime.retrato_usuario,
    escrita_via="comandos de playlist",
    intent_consulta="PLAYLIST_LIST",
    parametro_detalhe="nome_playlist",
)
_mapa_recursos_runtime.registrar(
    "playlists_laylay",
    arquivo="memoria/playlists_laylay/playlists_da_laylay.json",
    descricao="curadorias musicais montadas pela própria Laylay a partir do histórico confirmado",
    termos=(
        "suas playlists", "playlist da laylay", "playlists da laylay",
        "playlist que voce criou", "playlist que você criou",
        "playlists que voce criou", "playlists que você criou",
        "playlists voce criou", "playlists você criou",
        "playlists criadas por voce", "playlists criadas por você",
        "playlists que voce montou", "playlists que você montou",
        "xodos que eu separei", "climas que combinam comigo",
    ),
    leitor=_registro_musica_leitura_runtime.retrato_laylay,
    escrita_via="curadoria musical da Laylay",
    intent_consulta="LAYLAY_PLAYLIST_LIST",
    parametro_detalhe="nome_playlist",
)
HOTKEY_MODO_CHAT_LIGA = "ctrl+shift+z"
HOTKEY_MODO_CHAT_DESLIGA = "ctrl+f9"
# Uma tecla única evita que jogos em tela cheia conservem Ctrl/Shift como
# pressionados ao alternar entre Raw Input, Game Bar e o hook de texto.
HOTKEY_BARRA_COMANDO = os.environ.get("LAYLAY_HOTKEY_BARRA", "f10").strip() or "f10"
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
    enviar_mensagem=lambda mensagens: _registro_modelo_llm_runtime.enviar(
        mensagens,
        _com_tools=False,
        max_tokens=512,
        modo_rapido=True,
        timeout=30,
        _permitir_durante_interacao=True,
    ),
    log=print,
)

# ====================== CONFIGURAÇÕES GLOBAIS ======================
_runtime_llm_portatil = _criar_runtime_llm_portatil(
    raiz=_base_dir,
    requests_get=requests.get,
    requests_post=requests.post,
    log=print,
)
API_KEY = _runtime_llm_portatil.api_key
MODEL = _runtime_llm_portatil.modelo
OPENROUTER_BASE_URL = _runtime_llm_portatil.base_url
atexit.register(_runtime_llm_portatil.encerrar)


_descarregar_modelo_local = partial(
    _descarregar_modelo_local_integracao,
    runtime_portatil=_runtime_llm_portatil,
    modelo=MODEL,
    descarregar_ollama=_descarregar_modelo_ollama_mente,
)
MEMORIA_CONTEXTO_ARQUIVO = os.path.join(PASTA_MEMORIA, "memoria_contexto.json")
MEMORIA_SQLITE = MemoriaSQLite(os.path.join(PASTA_MEMORIA, "laylay_memoria.sqlite"))
_recuperar_aprendizados = MEMORIA_SQLITE.consultar_aprendizados
_rede_associativa_runtime = _criar_rede_associativa_runtime_mente(
    db_path=MEMORIA_SQLITE.db_path,
    modo=os.getenv("LAYLAY_REDE_ASSOCIATIVA_MODO", "continuidade"),
    contexto_getter=lambda: {
        **dict(_obter_contexto_perceptivo() or {}),
        "modo_jogo_ativo": bool(_modo_jogo_runtime.ativo),
        "emocao_usuario": str(
            _estado_compartilhado_runtime.mental.get("emocao_usuario") or ""
        ),
    },
    log=print,
)
OPENROUTER_HTTP_REFERER = os.environ.get("OPENROUTER_HTTP_REFERER", "http://localhost")
OPENROUTER_APP_TITLE = os.environ.get("OPENROUTER_APP_TITLE", "Laylay")
_composicao_inteligencia_externa_runtime = (
    _criar_composicao_inteligencia_externa_runtime(
        base_url=OPENROUTER_BASE_URL,
        model=MODEL,
        api_key=API_KEY,
        http_referer=OPENROUTER_HTTP_REFERER,
        app_title=OPENROUTER_APP_TITLE,
        normalizar_texto_curto=_normalizar_texto_curto,
        requests_get=requests.get,
        requests_post=_runtime_llm_portatil.post,
        ao_finalizar_conversa_modo_jogo=_descarregar_modelo_local,
        registrar_falha=_observabilidade_mente_runtime.relatar_falha,
        registrar_orcamento_prompt=(
            _observabilidade_mente_runtime.registrar_orcamento_prompt
        ),
        log=print,
    )
)
_otimizacoes_desempenho_refs["composicao_llm"] = (
    _composicao_inteligencia_externa_runtime
)
_pesquisa_contextual_runtime = _composicao_inteligencia_externa_runtime.pesquisa
_llm_http_runtime = _composicao_inteligencia_externa_runtime.http
LLM_LOCAL_TIMEOUT = _composicao_inteligencia_externa_runtime.local_timeout
LLM_GAME_TIMEOUT = _composicao_inteligencia_externa_runtime.game_timeout
LLM_REMOTE_TIMEOUT = _composicao_inteligencia_externa_runtime.remote_timeout
_llm_endpoint_eh_local = _llm_http_runtime.endpoint_eh_local
_post_chat_llm = _llm_http_runtime.post

# ====================== GROQ VISION (substitui Gemini) ======================
GROQ_API_KEY = _composicao_inteligencia_externa_runtime.groq_api_key
GROQ_VISION_MODEL = _composicao_inteligencia_externa_runtime.groq_model
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
    "prime video": "https://www.primevideo.com/",
    "amazon prime video": "https://www.primevideo.com/",
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
VOICE, VOICE_FALLBACK = _resolver_vozes_tts_mente()

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
    capturar_tela_base64 as _capturar_tela_base64_modulo,
    configurar_memoria_visual,
    criar_memoria_visual_runtime as _criar_memoria_visual_runtime_mente,
    registrar_memoria_visual as _registrar_memoria_visual_modulo,
)

configurar_memoria_visual(PASTA_MEMORIA, MAX_MEMORIAS_VISUAIS_DIA)


_capturar_tela_base64 = _capturar_tela_base64_modulo
_analisar_com_groq = _composicao_inteligencia_externa_runtime.analisar_imagem
registrar_memoria_visual = partial(
    _registrar_memoria_visual_integrada_mente,
    registrar_memoria=_registrar_memoria_visual_modulo,
    registrar_evento_temporal=_registrar_evento_visual_temporal_mente,
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    atualizar_estado=lambda **campos: _estado_compartilhado_runtime.atualizar_campos(
        "mental", **campos,
    ),
    log=print,
)


# ====================== COMUNICAÇÃO ======================
_composicao_chrome_comandos_runtime = _criar_composicao_chrome_comandos_laylay_runtime(
    ws_transport=_ws_transport_runtime,
    log=print,
    registrar_falha=_observabilidade_mente_runtime.registrar_falha,
)
_chrome_solicitacoes = _composicao_chrome_comandos_runtime.solicitacoes

_ambiente_navegacao_runtime = _criar_ambiente_navegacao_runtime_mente(
    servicos_iniciais={},
    log=print,
)
atualizar_contexto = _ambiente_navegacao_runtime.atualizar_contexto
atualizar_contexto_por_url = _ambiente_navegacao_runtime.atualizar_contexto_por_url
organizar_janelas_robusto = _ambiente_navegacao_runtime.organizar_janelas
planejar_organizacao_desktop = _ambiente_navegacao_runtime.planejar_organizacao_janelas
listar_programas_abertos = _ambiente_navegacao_runtime.listar_programas
observar_programas_abertos = _ambiente_navegacao_runtime.observar_programas
_resolver_alvo_ambiente = _ambiente_navegacao_runtime.resolver_alvo
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
obter_volume_sistema = _obter_volume_sistema_mente
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


_composicao_chrome_ws_runtime = _criar_composicao_chrome_ws_laylay_runtime(
    servicos_iniciais={},
    monitor_saude=_saude_mente_runtime,
    solicitacoes=_chrome_solicitacoes,
    playlist_state=playlist_state,
    yt_clean_url=lambda url: _yt_clean_url(url),
    playlist_avancar_proxima=(
        _registro_musica_operacoes_runtime.avancar_proxima
    ),
    falar_com_lipsync=lambda *args, **kwargs: falar_com_lipsync(*args, **kwargs),
    ws_transport=_ws_transport_runtime,
    fechar_extensoes_anteriores=_ws_close_other_extensions,
    stop_event=_servicos_background_runtime.evento_parada,
)
_chrome_ws_contexto_runtime = _composicao_chrome_ws_runtime.contexto
_chrome_ws_eventos_runtime = _composicao_chrome_ws_runtime.eventos
_chrome_ws_runtime = _composicao_chrome_ws_runtime.ws
ws_handler = _composicao_chrome_ws_runtime.handler
run_ws_server_in_thread = _composicao_chrome_ws_runtime.executar_servidor
_analisar_com_groq_jogo = (
    _composicao_inteligencia_externa_runtime.analisar_imagem_jogo
)
_sintetizar_pesquisa_jogo = (
    _composicao_inteligencia_externa_runtime.sintetizar_pesquisa_jogo
)
broadcast_command = _composicao_chrome_comandos_runtime.broadcast_command

solicitar_conteudo_pagina = _chrome_solicitacoes.solicitar_conteudo_pagina

fechar_aba_ativa_nativa = partial(
    _fechar_aba_ativa_nativa_chrome_mente,
    get_active_window=gw.getActiveWindow,
    hotkey=pyautogui.hotkey,
    sleep=time.sleep,
)

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
_overlay_jogo_runtime = _criar_compatibilidade_overlay_jogo_runtime_mente(
    habilitado=os.environ.get(
        "LAYLAY_OVERLAY_JOGO_BORDERLESS", "0"
    ).casefold() not in {"0", "false", "nao", "não", "off", "desligado"},
    log=print,
)
_modo_jogo_runtime = _criar_modo_jogo_runtime_mente(
    definir_bloqueio_llm=_llm_http_runtime.definir_modo_jogo,
    descarregar_modelo=_descarregar_modelo_local,
    llm_em_andamento=lambda: _llm_http_runtime.requisicao_local_em_andamento,
    preparar_overlays=_overlay_jogo_runtime.preparar,
    habilitado=_modo_jogo_auto_habilitado,
    entrada_estavel_s=float(os.environ.get("LAYLAY_MODO_JOGO_ENTRADA_SEGUNDOS", "4")),
    tolerancia_saida_s=float(os.environ.get("LAYLAY_MODO_JOGO_SAIDA_SEGUNDOS", "45")),
    log=print,
)
modo_jogo_ativo = lambda: bool(_modo_jogo_runtime.ativo)


# A visão é conectada mais tarde, depois de captura, pesquisa e fala.
_registro_visao_jogo_leitura_runtime = None
_ponte_iniciativa_aplicacao_runtime = _criar_ponte_iniciativa_aplicacao_runtime(
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    percepcao_getter=_percepcao_get,
    conversa_getter=_conversa_estado_get,
    modo_jogo=_modo_jogo_runtime,
    visao_leitura_getter=lambda: _registro_visao_jogo_leitura_runtime,
    identificar_jogo=identificar_jogo,
    salvar_memoria=lambda: salvar_memoria(),
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(
        texto, emocao, nivel,
    ),
    env_getter=os.environ.get,
    log=print,
)
_turno_mental_em_andamento = _ponte_iniciativa_aplicacao_runtime.turno_em_andamento
_contexto_motor_iniciativa = _ponte_iniciativa_aplicacao_runtime.contexto


_motor_iniciativa_runtime = _criar_motor_iniciativa_runtime_mente(
    estado_get=lambda: dict(
        _estado_compartilhado_runtime.mental.get("iniciativa_autonoma") or {}
    ),
    estado_set=lambda estado: _estado_compartilhado_runtime.atualizar_campos(
        "mental", iniciativa_autonoma=dict(estado or {}),
    ),
    contexto_getter=_contexto_motor_iniciativa,
    modo=os.environ.get("LAYLAY_INICIATIVA_MODO", "sombra").strip().casefold(),
    registrar_decisao_cb=_observabilidade_mente_runtime.registrar_decisao,
    capacidade_getter=_mapa_habilidades_runtime.consultar,
    log=print,
)


_objetivos_iniciativa_atuais = _ponte_iniciativa_aplicacao_runtime.objetivos


_coordenador_oportunidades_runtime = _criar_coordenador_oportunidades_runtime_mente(
    encaminhar=_motor_iniciativa_runtime.registrar,
    estado_get=lambda: dict(
        _estado_compartilhado_runtime.mental.get("coordenador_oportunidades") or {}
    ),
    estado_set=lambda estado: _estado_compartilhado_runtime.atualizar_campos(
        "mental", coordenador_oportunidades=dict(estado or {}),
    ),
    contexto_getter=_contexto_motor_iniciativa,
    objetivos_getter=_objetivos_iniciativa_atuais,
    log=print,
)
_registrar_oportunidade_iniciativa = _coordenador_oportunidades_runtime.registrar

_preparar_autonomia_segura_padrao = (
    _ponte_iniciativa_aplicacao_runtime.preparar_autonomia_segura_padrao
)
_registrar_feedback_proatividade = (
    _ponte_iniciativa_aplicacao_runtime.registrar_feedback
)
_preparar_sugestoes_proativas_jogo = (
    _ponte_iniciativa_aplicacao_runtime.preparar_sugestoes_jogo
)
_processar_governanca_iniciativa = (
    _ponte_iniciativa_aplicacao_runtime.processar_governanca
)

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
    registrar_oportunidade=_registrar_oportunidade_iniciativa,
    atualizar_modo_jogo=_modo_jogo_runtime.observar,
    interacao_iniciada=lambda: float(
        _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
    ) > 0.0,
    clock=time.time,
    sleep=_servicos_background_runtime.aguardar,
    log=print,
)

ativar_tela_cheia_robusta = partial(
    _maximizar_janela_mente,
    gw,
    pyautogui,
    psutil_mod=psutil,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
)

focar_janela_app = partial(
    _focar_janela_mente,
    gw,
    pyautogui,
    psutil_mod=psutil,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
)

fechar_janela_por_titulo = partial(
    _fechar_janela_por_titulo_mente,
    gw,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    pyautogui_mod=pyautogui,
)

_janela_app_esta_em_foco = partial(_janela_esta_em_foco_mente, gw)

fechar_programa = _fechar_programa_mente


# ====================== CONSCIÊNCIA DE ESTADO (FERRAMENTAS DE LEITURA) ======================

_normalizar_alvo_ambiente = _normalizar_alvo_ambiente_mente


# ====================== SISTEMA DE ARQUIVOS (CRUD) BLINDADO ======================

resolver_caminho = _resolver_caminho_mente
criar_pasta = _criar_pasta_mente
criar_ou_editar_arquivo = _criar_ou_editar_arquivo_mente
escrever_arquivo_texto_seguro = _escrever_arquivo_texto_seguro_mente
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
    servicos_iniciais={},
)
_otimizacoes_desempenho_refs["orquestrador_fala"] = _orquestrador_fala_runtime
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
_ponte_iniciativa_aplicacao_runtime.conectar(
    motor=_motor_iniciativa_runtime,
    porteiro=_porteiro_proatividade_runtime,
    coordenador=_coordenador_oportunidades_runtime,
    rede=_rede_associativa_runtime,
)


_voz_runtime = _criar_voz_runtime_mente(
    fallback_fala=FALLBACK_FALA_NEUTRA,
    voice=VOICE,
    fallback_voice=VOICE_FALLBACK,
    iniciar_servico_cb=_servicos_background_runtime.iniciar,
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
    nome_usuario_cb=lambda: str(
        _estado_compartilhado_runtime.mental.get("nome_usuario") or ""
    ),
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
    publicar_texto_proativo_cb=_orquestrador_fala_runtime.publicar_texto_proativo,
    registrar_metrica_cb=_observabilidade_mente_runtime.registrar_metrica,
    trace_context_getter=_observabilidade_mente_runtime.obter_trace_corrente,
    registrar_falha_cb=_observabilidade_mente_runtime.registrar_falha,
    log=print,
    # A mente já consolida candidatos do mesmo turno antes desta fila. Aqui
    # cada item precisa permanecer isolado para nunca costurar dois comandos.
    batch_window=0.0,
    batch_max_items=1,
    tts_timeout_s=float(os.environ.get("LAYLAY_TTS_TIMEOUT", "8.0")),
    stop_event=_servicos_background_runtime.evento_parada,
)
from mente_laylay.cognicao.modalidade_turno import (
    classificar_modalidade_turno as _classificar_modalidade_turno_mente,
)
from mente_laylay.memoria_mental.pendencia import (
    criar_pendencia as _criar_pendencia_mente,
    limpar_pendencia as _limpar_pendencia_mente,
    pendencia_ativa as _pendencia_ativa_turno_mente,
    registrar_pendencia as _registrar_pendencia_mente,
)
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


_salvar_identidade_usuario = partial(
    _salvar_identidade_usuario_mente,
    persistir_nome=partial(_salvar_nome_usuario_confirmado_mente, MEMORIA_SQLITE),
    atualizar_estado=lambda **campos: _estado_compartilhado_runtime.atualizar_campos(
        "mental", **campos,
    ),
    salvar_memoria=salvar_memoria,
)

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
    enviar_mensagem=_registro_modelo_llm_runtime.enviar,
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
    estado_getter=lambda: dict(
        _estado_compartilhado_runtime.mental.get("aprendizado_rotina_musica") or {}
    ),
    estado_setter=lambda **campos: _estado_compartilhado_runtime.atualizar(
        "mental",
        lambda estado: {
            **dict(estado),
            "aprendizado_rotina_musica": {
                **dict(estado.get("aprendizado_rotina_musica") or {}),
                **campos,
            },
        },
    ),
    log=print,
)
_verificar_musica_autonoma = _busca_musical_runtime.verificar_autonoma
_buscar_primeiro_video_youtube = _busca_musical_runtime.buscar_primeiro_video
_resolver_primeiro_video_youtube = _busca_musical_runtime.resolver_primeiro_video
_chrome_comandos_runtime = _composicao_chrome_comandos_runtime.conectar_executor(
    allowed_actions=ALLOWED_ACTIONS,
    formatar_url_ou_busca=formatar_url_ou_busca,
    is_valid_url=is_valid_url,
    atualizar_contexto_por_url=atualizar_contexto_por_url,
    atualizar_contexto=atualizar_contexto,
    buscar_primeiro_video_youtube=_buscar_primeiro_video_youtube,
    modo_jogo_ativo=lambda: bool(_modo_jogo_runtime.ativo),
)
_ambiente_navegacao_runtime.conectar_navegador(
    solicitacoes=_chrome_solicitacoes,
    comandos=_chrome_comandos_runtime,
)
_navegador_leitura_runtime = _criar_navegador_leitura_runtime(
    solicitacoes=_chrome_solicitacoes,
    ambiente=_ambiente_navegacao_runtime,
    # P0_NAVEGADOR_COMPOSICAO_ANTERIOR_V4_1_20260815
    estado=_chrome_estado,
)
_registro_navegador_leitura_runtime = _registrar_navegador_leitura(
    _navegador_leitura_runtime
)
_navegador_operacoes_runtime = _criar_navegador_operacoes_runtime(
    comandos=_chrome_comandos_runtime,
    ambiente=_ambiente_navegacao_runtime,
    fechar_aba_nativa=fechar_aba_ativa_nativa,
)
_registro_navegador_operacoes_runtime = _registrar_navegador_operacoes(
    _navegador_operacoes_runtime
)
_iniciar_worker_de_falas = _voz_runtime.iniciar_worker
_normalizar_segmento_fala = _voz_runtime.normalizar_segmento_fala
_agendar_fala_proativa = _voz_runtime.agendar_fala_proativa


_recomendar_playlist_real_para_presenca = partial(
    _recomendar_playlist_real_para_presenca_mente,
    carregar_playlists=_playlist_runtime.load,
    registrar_falha=_observabilidade_mente_runtime.registrar_falha,
    log=print,
)


_diretor_presenca_runtime = _criar_diretor_presenca_runtime_mente(
    estado_get=lambda: dict(
        _estado_compartilhado_runtime.mental.get("presenca_contextual") or {}
    ),
    estado_set=lambda estado: _estado_compartilhado_runtime.atualizar_campos(
        "mental", presenca_contextual=dict(estado or {}),
    ),
    contexto_getter=_contexto_motor_iniciativa,
    registrar_oportunidade=_registrar_oportunidade_iniciativa,
    emitir_fala=lambda texto, emocao="calma", nivel=1, **dados: _agendar_fala_proativa(
        "assistencia_clipboard"
        if dados.get("origem") == "observador_area_transferencia"
        else "presenca_jogo" if dados.get("dominio") == "jogo" else "diretor_presenca",
        texto,
        emocao,
        nivel,
        mesclar_turno=False,
        ao_concluir=dados.get("ao_concluir"),
        preservar_ate_entrega=bool(
            dados.get("origem") == "observador_area_transferencia"
        ),
    ),
    registrar_feedback=_registrar_feedback_proatividade,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    recomendacao_musical=_recomendar_playlist_real_para_presenca,
    habilitado=os.environ.get("LAYLAY_PRESENCA", "1").casefold()
    not in {"0", "false", "nao", "não", "off", "desligado"},
    intervalo_ciclo_s=float(os.environ.get("LAYLAY_PRESENCA_INTERVALO", "15")),
    stop_event=_servicos_background_runtime.evento_parada,
    log=print,
)


_preferencias_sugestoes_runtime = _criar_preferencias_sugestoes_runtime_mente(
    servicos_iniciais={},
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
    registrar_oportunidade=_registrar_oportunidade_iniciativa,
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
    registrar_oportunidade=_registrar_oportunidade_iniciativa,
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


_aprender_pesquisa_semantica_arquivos = partial(
    _aprender_pesquisa_semantica_arquivos_mente,
    normalizar=lambda texto: _normalizar_texto(texto),
    registrar_evidencia=_motor_aprendizado_runtime.registrar_evidencia,
)


_pesquisa_semantica_arquivos_runtime = _criar_pesquisa_semantica_arquivos_runtime(
    projeto_raiz=os.path.abspath(os.path.dirname(__file__)),
    log=print,
)
_registro_arquivos_leitura_runtime = _registrar_arquivos_leitura(
    _pesquisa_semantica_arquivos_runtime
)
_arquivos_mutacao_runtime = _criar_arquivos_mutacao_runtime()
_registro_arquivos_mutacao_runtime = _registrar_arquivos_mutacao(
    _arquivos_mutacao_runtime
)
_orquestrador_fala_runtime.conectar_servicos({
    "_registrar_mente_curta": _registrar_mente_curta,
    "_estado_compartilhado_runtime": _estado_compartilhado_runtime,
    "_encerrar_topico_mente": _encerrar_topico_mente,
    "salvar_memoria": salvar_memoria,
    "print": print,
    "_dirigir_fala_mente": _dirigir_fala_mente,
    "_voz_runtime": _voz_runtime,
    "_registrar_continuidade_da_fala_mente": _registrar_continuidade_da_fala_mente,
    "_threading": _threading,
    "_agendar_fala_proativa": _agendar_fala_proativa,
    "_registrar_metrica_diagnostico": (
        _observabilidade_mente_runtime.registrar_metrica
    ),
})
falar_com_lipsync = _orquestrador_fala_runtime.falar
_falar_resultado_operacional = _orquestrador_fala_runtime.falar_resultado_operacional

_composicao_iot_runtime = _criar_composicao_iot_laylay_runtime(
    memoria_sqlite=MEMORIA_SQLITE,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    definir_emocao=_definir_emocao_conversacional,
    emitir_fala=False,
    enviar_mensagem=_registro_modelo_llm_runtime.enviar,
    log=print,
)
_iot_runtime = _composicao_iot_runtime.runtime
_registro_iot_runtime = _registrar_iot(_iot_runtime)
_preferencias_sugestoes_runtime.conectar_iot(_registro_iot_runtime)
_adaptadores_aplicacao_runtime.conectar_iot(_registro_iot_runtime)
_mapa_recursos_runtime.registrar(
    "dispositivos_iot",
    arquivo="memória SQLite (catálogo IoT sanitizado)",
    descricao=(
        "dispositivos inteligentes reais configurados, seus ambientes e "
        "as ações que a Laylay pode executar"
    ),
    termos=(
        "dispositivo", "dispositivos", "aparelho", "aparelhos",
        "casa inteligente", "iot", "o que tem no quarto",
    ),
    leitor=_registro_iot_runtime.retrato_para_mente,
    escrita_via="comandos IoT",
    intent_consulta="IOT_LIST",
)
_falar_status_saude = partial(
    _ambiente_sistema_runtime.falar_status_saude,
    psutil_mod=psutil,
    falar=lambda texto, emocao="calma", nivel=1: _central_notificacoes_ingerir_sistema(
        texto,
        aplicativo="monitor de saúde",
        prioridade="alta",
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
    deve_parar=_servicos_background_runtime.deve_parar,
    aguardar_fn=_servicos_background_runtime.aguardar,
)


_entregar_fala_inicial_confirmada = (
    _orquestrador_fala_runtime.entregar_fala_inicial_confirmada
)


_entregar_briefing_inicial = partial(
    _entregar_briefing_inicial_mente,
    entregar=_entregar_fala_inicial_confirmada,
    salvar_estado=salvar_estado_briefing,
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
        enviar_mensagem_cb=_registro_modelo_llm_runtime.enviar,
        limpar_resposta_cb=limpar_resposta,
        remover_prefixo_exec_cb=_remover_prefixo_exec,
    ),
    agendar_fala=_entregar_briefing_inicial,
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
        "enviar_mensagem": _registro_modelo_llm_runtime.enviar,
        "handle_feedback_pendente": _handle_feedback_pendente_mente,
        "handle_sugestao_confirmacao": _handle_sugestao_confirmacao,
        "musica_operacoes": _registro_musica_operacoes_runtime,
        "extrair_nome_playlist": extrair_nome_playlist,
        "yt_clean_title": _yt_clean_title,
        "falar_com_lipsync": falar_com_lipsync,
        "rotina_registrar_feedback": _rotina_registrar_feedback,
        "gmail_buscar_nao_lidos": _gmail_buscar_nao_lidos,
        "gmail_falar_resumo_estiloso": _gmail_falar_resumo_estiloso,
        "registrar_feedback_proatividade": _registrar_feedback_proatividade,
        "registrar_feedback_aprendizado": (
            _adaptadores_aplicacao_runtime.registrar_feedback_contextual
        ),
        "resolver_comando_natural": resolver_comando_natural,
        "executar_intencao": executar_intencao,
        "registrar_resultado_execucao": _registrar_resultado_execucao,
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
    deve_parar=_servicos_background_runtime.deve_parar,
    aguardar_fn=_servicos_background_runtime.aguardar,
)

# ====================== FUNÇÕES DE PROCESSAMENTO DE LINGUAGEM ======================
_cliente_llm_runtime = _composicao_inteligencia_externa_runtime.conectar_cliente(
    memoria_inteligente=memoria_inteligente,
    normalizar_texto=lambda texto: _normalizar_texto_com_apelidos(texto),
    mapear_pastas=mapear_pastas_principais,
    contexto_logs_getter=lambda: _estado_compartilhado_runtime.obter_copia(
        "percepcao", "logs_navegador", []
    ),
    contexto_navegador_relevante=_contexto_navegador_relevante,
    contexto_sistema_getter=lambda: _percepcao_get("contexto_sistema", {}),
    obter_contexto_paginas=get_dicionario_contexto,
    resumo_mente_integrada=_resumo_mente_integrada_para_prompt,
    registrar_metrica=_observabilidade_mente_runtime.registrar_metrica,
    orcamento_turno=_orcamento_llm_turno_runtime,
    interacao_ativa=lambda: bool(
        _conversa_estado_get("modo_chat", False)
        or _conversa_estado_get("conversa_ativa", False)
        or _estado_compartilhado_runtime.mental.get("interacao_em_andamento")
    ),
)
_modelo_llm_diferido_runtime.conectar(_cliente_llm_runtime)


_aprender_conteudo_area_transferencia = partial(
    _aprender_conteudo_area_transferencia_mente,
    salvar_aprendizado=MEMORIA_SQLITE.salvar_aprendizado_semantico,
)


_observar_conteudo_area_transferencia = partial(
    _observar_conteudo_area_transferencia_mente,
    registrar_evidencia=_motor_aprendizado_runtime.registrar_evidencia,
)


_observar_item_caixa_entrada = partial(
    _observar_item_caixa_entrada_mente,
    registrar_evidencia=_motor_aprendizado_runtime.registrar_evidencia,
)


_investigador_erro_clipboard_runtime = InvestigadorErroRuntime(
    modelo_llm=_registro_modelo_llm_runtime,
    limpar_resposta=_limpar_texto_fala_ia,
    log=print,
)
_cooperacao_refs = {"orquestrador": None, "quadro": None}


def _investigar_erro_clipboard_cooperativo(conteudo):
    orquestrador = _cooperacao_refs["orquestrador"]
    processar = getattr(orquestrador, "processar_investigacao_clipboard", None)
    if not callable(processar):
        return {
            "ok": False,
            "fala": "A cooperação da investigação não está disponível agora.",
        }
    return processar(
        conteudo,
        investigador=_investigador_erro_clipboard_runtime,
    )


_registrar_feedback_agenda = partial(
    _registrar_feedback_agenda_mente,
    registrar_evidencia=_motor_aprendizado_runtime.registrar_evidencia,
)


_observar_evento_pendencia_agenda = partial(
    _observar_evento_pendencia_agenda_mente,
    registrar_feedback=_registrar_feedback_agenda,
)


def _observar_evento_pendencia(evento, pendencia):
    _observar_evento_pendencia_agenda(evento, pendencia)
    _motor_aprendizado_runtime.observar_evento_pendencia(evento, pendencia)


_pendencia_acao_runtime = _criar_pendencia_acao_runtime(
    estado_getter=lambda: _estado_compartilhado_runtime.mental,
    estado_atualizar=lambda atualizador: _estado_compartilhado_runtime.atualizar(
        "mental", atualizador,
    ),
    log=print,
    evento_cb=_observar_evento_pendencia,
)
_configurar_pendencia_exclusao(_pendencia_acao_runtime)


_memoria_pessoas_runtime = _criar_memoria_pessoas_runtime(
    caminho=os.path.join(PASTA_MEMORIA, "pessoas_relacoes.json"),
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    pendencia_runtime=_pendencia_acao_runtime,
    classificar_confirmacao_contextual=(
        _feedback_pendente_runtime.classificar_confirmacao_contextual
    ),
    registrar_resultado=_registrar_resultado_execucao,
    registrar_mente_curta=_registrar_mente_curta,
    registrar_aprendizado=_motor_aprendizado_runtime.registrar_evidencia,
    esquecer_aprendizado=_motor_aprendizado_runtime.esquecer_por_prefixo,
    estado_getter=lambda: _estado_compartilhado_runtime.mental,
    estado_atualizar=lambda atualizador: _estado_compartilhado_runtime.atualizar(
        "mental", atualizador,
    ),
    log=print,
)
_registro_memoria_pessoas_runtime = _registrar_memoria_pessoas(
    _memoria_pessoas_runtime
)
_adaptadores_aplicacao_runtime.conectar_memoria_pessoas(
    _registro_memoria_pessoas_runtime
)
_saude_mente_runtime.registrar(
    "memoria_pessoas",
    "saudavel",
    detalhes=(
        "memória local estruturada conectada a contexto, aprendizado, continuidade, "
        "segurança, diagnóstico e mapa de habilidades"
    ),
)


_area_transferencia_runtime = _criar_area_transferencia_runtime(
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    modelo_llm=_registro_modelo_llm_runtime,
    executar_intencao=lambda resultado, texto: executar_intencao(resultado, texto),
    registrar_operacao=_registrar_mente_curta,
    registrar_resultado=_registrar_resultado_execucao,
    aprender_conteudo=_aprender_conteudo_area_transferencia,
    observar_conteudo=_observar_conteudo_area_transferencia,
    investigar_erro=_investigar_erro_clipboard_cooperativo,
    pendencia_runtime=_pendencia_acao_runtime,
    log=print,
)


_ponte_clipboard_aplicacao_runtime = _criar_ponte_clipboard_aplicacao_runtime(
    pendencias=_pendencia_acao_runtime,
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    estado_mental_atualizar=lambda **campos: _estado_compartilhado_runtime.atualizar_campos(
        "mental", **campos,
    ),
    memoria_conversa_getter=lambda: list(_memoria_conversa_get("messages", []) or []),
    memoria_conversa_setter=lambda mensagens: _estado_compartilhado_runtime.atualizar_campos(
        "memoria_conversa", messages=mensagens,
    ),
    pendencia_protegida_getter=_pendencia_ativa_turno_mente,
    oferta_deve_ceder=_oferta_clipboard_deve_ceder,
    texto_tem_comando_explicito=_texto_tem_comando_explicito,
    classificar_resposta=_classificar_resposta_oferta_clipboard,
    classificar_confirmacao=_feedback_pendente_runtime.classificar_confirmacao_contextual,
    area_transferencia=_area_transferencia_runtime,
    caixa_entrada_getter=lambda: _caixa_entrada_pessoal_runtime,
    falar=falar_com_lipsync,
    agendar_fala=_agendar_fala_proativa,
    log=print,
)
_registrar_oferta_area_transferencia_entregue = (
    _ponte_clipboard_aplicacao_runtime.registrar_oferta_entregue
)
_processar_oferta_area_transferencia_pendente = (
    _ponte_clipboard_aplicacao_runtime.processar_oferta_pendente
)
_encaminhar_oferta_area_transferencia = (
    _ponte_clipboard_aplicacao_runtime.encaminhar_oferta
)


_observador_area_transferencia_runtime = _criar_observador_area_transferencia_runtime(
    snapshot_getter=_area_transferencia_runtime.snapshot_passivo,
    considerar_presenca=_encaminhar_oferta_area_transferencia,
    contexto_getter=lambda: {
        **_contexto_motor_iniciativa(),
        "clipboard_ofertas_silenciadas": dict(
            _estado_compartilhado_runtime.mental.get(
                "clipboard_ofertas_silenciadas", {}
            ) or {}
        ),
    },
    oferta_entregue=_registrar_oferta_area_transferencia_entregue,
    modo=os.environ.get("LAYLAY_CLIPBOARD_OBSERVADOR_MODO", "sugestao"),
    intervalo_s=float(os.environ.get("LAYLAY_CLIPBOARD_OBSERVADOR_INTERVALO", "1")),
    estabilidade_s=float(os.environ.get("LAYLAY_CLIPBOARD_OBSERVADOR_ESTABILIDADE", "3")),
    stop_event=_servicos_background_runtime.evento_parada,
    log=print,
)
_area_transferencia_runtime.conectar_observador_passivo(
    _observador_area_transferencia_runtime.marcar_conteudo_consumido
)
_observador_area_transferencia_runtime.preparar_baseline()
_saude_mente_runtime.registrar(
    "observador_area_transferencia",
    "saudavel",
    detalhes=(
        "percepção local sanitizada conectada ao modo companhia; "
        f"modo={_observador_area_transferencia_runtime.modo}"
    ),
)
_caixa_entrada_pessoal_runtime = _criar_caixa_entrada_pessoal_runtime(
    caminho=os.path.join(PASTA_MEMORIA, "caixa_entrada_pessoal.json"),
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    registrar_resultado=_registrar_resultado_execucao,
    executar_intencao=lambda resultado, texto: executar_intencao(resultado, texto),
    contexto_getter=lambda: {
        "messages": _memoria_conversa_get("messages", []),
    },
    clipboard_getter=_area_transferencia_runtime.obter_texto_seguro,
    observar_item=_observar_item_caixa_entrada,
    modelo_llm=_registro_modelo_llm_runtime,
    pendencia_runtime=_pendencia_acao_runtime,
    log=print,
)
_confirmacao_llm_runtime = _composicao_inteligencia_externa_runtime.confirmacao
interpretar_confirmacao_llm = _confirmacao_llm_runtime.interpretar
_merge_intent_llm = _confirmacao_llm_runtime.mesclar
_selecao_abas_runtime = _composicao_inteligencia_externa_runtime.selecao_abas
selecionar_abas_para_fechar_llm = _selecao_abas_runtime.selecionar
_interpretador_semantico_runtime = _criar_interpretador_semantico_runtime_mente(
    contexto_getter=lambda: {
        "mente": _estado_compartilhado_runtime.mental,
        "mensagens": _memoria_conversa_get("messages", []),
    },
    modelo_llm=_registro_modelo_llm_runtime,
    log=print,
)
resumir_pagina_no_dicionario = partial(
    _contexto_paginas.resumir,
    modelo_llm=_registro_modelo_llm_runtime,
)


_registrar_contexto_resumo_pagina = (
    _adaptadores_aplicacao_runtime.registrar_contexto_resumo_pagina
)


_resumo_conteudo_runtime = _criar_resumo_conteudo_runtime_mente(
    namespace_getter=lambda: {
        "websocket_disponivel": lambda: _ws_transport_runtime.obter_loop() is not None,
        "solicitar_conteudo": solicitar_conteudo_pagina,
        "falar": falar_com_lipsync,
        "limpar_resposta": limpar_resposta,
        "remover_prefixo_exec": _remover_prefixo_exec,
        "transcript_api": YouTubeTranscriptApi,
        "registrar_contexto_resumo": _registrar_contexto_resumo_pagina,
    },
    modelo_llm=_registro_modelo_llm_runtime,
    cache_habilitado=lambda: _flag_desempenho_ativa(
        "LAYLAY_CACHE_RESUMOS_ATIVO"
    ),
    log=print,
)
_otimizacoes_desempenho_refs["resumo"] = _resumo_conteudo_runtime
resumir_pagina_ou_video = _resumo_conteudo_runtime.resumir

_porteiro_runtime = _criar_porteiro_chrome_runtime_mente(
    abas_sugeridas=_abas_sugeridas_fechar,
    obter_ram_percent=lambda: psutil.virtual_memory().percent,
    listar_abas=_registro_navegador_leitura_runtime.listar_abas,
    obter_estado_chrome=_chrome_estado.snapshot,
    falar=lambda texto, emocao="irritada", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    enviar_fechamento=_registro_navegador_operacoes_runtime.fechar_aba,
    ram_threshold=RAM_THRESHOLD_PORTEIRO,
    idle_minutos=ABA_IDLE_MINUTOS,
    intervalo_minutos=PORTEIRO_INTERVALO_MIN,
    log=print,
    stop_event=_servicos_background_runtime.evento_parada,
)

_porteiro_daemon = _porteiro_runtime.daemon
_executar_fechar_abas_paradas = _porteiro_runtime.fechar_sugeridas

# ====================== SISTEMA DE AGENDAMENTOS ======================
_agendamentos_file = os.path.join(_base_dir, AGENDAMENTOS_ARQUIVO)

_pc_b_runtime = _criar_pc_b_runtime_mente(
    clientes_getter=lambda: _ws_transport_runtime.clientes_pc_b,
    loop_getter=_ws_transport_runtime.obter_loop,
    clientes_compativeis_getter=(
        _ws_transport_runtime.clientes_pc_b_compativeis
    ),
    estado_clientes_getter=_ws_transport_runtime.retrato_clientes_pc_b,
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
    executar_comando_conteudo_cb=lambda cmd, arg: _executar_comando_conteudo(cmd, arg),
    executar_intencao_cb=lambda resultado, texto: executar_intencao(resultado, texto),
    log=print,
    stop_event=_servicos_background_runtime.evento_parada,
)


_agendamentos_load = _agenda_runtime.load
_agendamentos_save = _agenda_runtime.save
_agendamentos_transacionar = _agenda_runtime.transacionar
_agenda_daemon = _agenda_runtime.daemon
_fala_agendamentos_estilosa = _agenda_runtime.fala_estilosa
_saude_mente_runtime.registrar(
    "agenda",
    "saudavel" if _agenda_runtime.diagnostico().get("disponivel") else "degradado",
    detalhes="agenda local conectada a pendência canônica, aprendizado, diagnóstico e cooperação",
)
_mapa_recursos_runtime.registrar(
    "agenda",
    arquivo="memoria/agendamentos.json",
    descricao="lembretes e ações agendadas reais, incluindo recorrência e horário",
    termos=(
        "agenda", "agendamento", "agendamentos", "lembrete", "lembretes",
        "compromissos", "o que tenho marcado", "arquivo da agenda",
    ),
    leitor=_agenda_runtime.retrato_para_mente,
    escrita_via="comandos de agenda",
    intent_consulta="LISTAR_AGENDAMENTOS",
)
_mapa_recursos_runtime.registrar(
    "caixa_entrada_pessoal",
    arquivo="memoria/caixa_entrada_pessoal.json",
    descricao="ideias, notas, tarefas, links e pensamentos que foram realmente guardados",
    termos=(
        "caixa de entrada", "minhas ideias", "ideias salvas", "ideias guardadas",
        "ideias anotadas", "minhas notas", "notas salvas", "notas guardadas",
        "o que guardei", "o que anotei",
    ),
    leitor=_caixa_entrada_pessoal_runtime.retrato_para_mente,
    escrita_via="comandos da caixa de entrada pessoal",
    intent_consulta="INBOX_LIST",
    executor_consulta=_caixa_entrada_pessoal_runtime.reexecutar,
)
_mapa_recursos_runtime.registrar(
    "memoria_pessoas",
    arquivo="memoria/pessoas_relacoes.json",
    descricao="pessoas, relações e fatos pessoais explicitamente confirmados pelo usuário",
    termos=(
        "pessoas que eu te falei", "pessoas que voce lembra", "quem eu te apresentei",
        "memoria de pessoas", "relações pessoais", "relacoes pessoais",
    ),
    leitor=_registro_memoria_pessoas_runtime.retrato_para_mente,
    escrita_via="memória de pessoas e relações",
    intent_consulta="PEOPLE_QUERY",
    parametro_detalhe="nome",
    executor_consulta=_registro_memoria_pessoas_runtime.reexecutar,
)
_resolver_consulta_recurso_local = _mapa_recursos_runtime.resolver_consulta
_executar_consulta_recurso_local = _mapa_recursos_runtime.executar_consulta

_fala_playlist_conteudo_estilosa = _fala_playlist_conteudo_estilosa_mente


_yt_clean_url = _yt_clean_url_mente
_yt_clean_title = _yt_clean_title_mente

_normalizar_texto = _normalizar_texto_mente

_linguagem_aprendida_runtime = _criar_linguagem_aprendida_runtime_mente(
    memoria_sqlite=MEMORIA_SQLITE,
    normalizar_texto=_normalizar_texto,
    texto_social_curto=lambda texto: _texto_social_curto(texto),
    falar=lambda fala, emocao, nivel: falar_com_lipsync(fala, emocao, nivel),
    turno_id_getter=lambda: (
        dict(_estado_compartilhado_runtime.mental.get("turno_atual") or {}).get("id")
        or _estado_compartilhado_runtime.mental.get("ultima_entrada_ts")
    ),
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


extrair_nome_playlist = _playlist_runtime.extrair_nome



_pedido_lista_geral_playlist = _playlist_runtime.pedido_lista_geral


_sincronizar_playlists_da_laylay = _playlist_laylay_runtime.sincronizar
_detectar_playlist_nome_direto = _playlist_runtime.detectar_nome_direto_contextual
_detectar_playlist_laylay_nome_direto = (
    _playlist_laylay_runtime.detectar_nome_direto_contextual
)
_carregar_playlists_para_memoria = _playlist_runtime.carregar_para_memoria


_executar_sugestao_temporal = _preferencias_sugestoes_runtime.executar_temporal

_sugestoes_sistema_runtime = _criar_sugestoes_sistema_runtime_mente(
    contexto_getter=lambda: {
        "pesquisa_contextual_runtime": _pesquisa_contextual_runtime,
        "abrir_url_externo": webbrowser.open,
        "_registro_navegador_leitura_runtime": _registro_navegador_leitura_runtime,
        "_registro_navegador_operacoes_runtime": _registro_navegador_operacoes_runtime,
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
        "limpar_resposta": limpar_resposta,
        "remover_prefixo_exec": _remover_prefixo_exec,
        "current_emotion": _conversa_estado_get("current_emotion", "calma"),
        "emotion_level": _conversa_estado_get("emotion_level", 1),
        "memoria_inteligente": memoria_inteligente,
        "salvar_memoria": salvar_memoria,
        "log": print,
        "executar_intencao": executar_intencao,
        "sugestao_bloqueada_ate": sugestao_bloqueada_ate,
        "executar_sugestao_temporal": _executar_sugestao_temporal,
        "preferencia_sugestao_get": _preferencia_sugestao_get,
        "interpretar_contraproposta": _interpretar_contraproposta_sugestao,
        "registrar_preferencia_sugestao": _registrar_preferencia_sugestao,
        "confirmar_hipotese_aprendizado": _motor_aprendizado_runtime.confirmar_hipotese,
        "registrar_excecao_preferencia": _motor_aprendizado_runtime.registrar_excecao_preferencia,
        "resolver_conflito_preferencia": _motor_aprendizado_runtime.resolver_conflito_preferencia,
        "registrar_feedback_proatividade": _registrar_feedback_proatividade,
        "registrar_oportunidade": _registrar_oportunidade_iniciativa,
    },
    modelo_llm=_registro_modelo_llm_runtime,
)
_executar_combo_modo_code = _sugestoes_sistema_runtime.executar_modo_code
_executar_combo_modo_gamer = _sugestoes_sistema_runtime.executar_modo_gamer
_executar_combo_organizacao = _sugestoes_sistema_runtime.executar_organizacao
_handle_sugestao_confirmacao = _sugestoes_sistema_runtime.processar_confirmacao
_detectar_sugestao_indireta = _sugestoes_sistema_runtime.detectar_indireta
_registrar_sugestao_indireta = _sugestoes_sistema_runtime.registrar_indireta

limpar_resposta = _limpar_resposta_mente

_contexto_imediato_runtime = _criar_contexto_imediato_runtime_mente(
    servicos_iniciais={},
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
    iot=_registro_iot_runtime,
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

_composicao_visao_jogo_runtime = _criar_composicao_visao_jogo_runtime(
    db_path=MEMORIA_SQLITE.db_path,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    log=print,
)
_memoria_jogos_runtime = _composicao_visao_jogo_runtime.memoria
_pesquisa_jogos_runtime = _composicao_visao_jogo_runtime.pesquisa

_coordenador_visao_jogo_runtime = _criar_coordenador_visao_jogo_runtime(
    memoria_jogos=_memoria_jogos_runtime,
    observador_inventario_getter=lambda: (
        _composicao_visao_jogo_runtime.observador_inventario
    ),
    diretor_presenca_getter=lambda: _diretor_presenca_runtime,
    recomendar_playlist=_recomendar_playlist_real_para_presenca,
    registrar_oportunidade=_registrar_oportunidade_iniciativa,
    decisao_permite_emissao=_decisao_permite_emissao_iniciativa,
    agendar_fala=_agendar_fala_proativa,
    registrar_mente_curta=_registrar_mente_curta,
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    estado_mental_substituir=lambda estado: (
        _estado_compartilhado_runtime.substituir("mental", estado)
    ),
    criar_pendencia=_criar_pendencia_mente,
    registrar_pendencia=_registrar_pendencia_mente,
    pendencia_ativa=_pendencia_ativa_turno_mente,
    limpar_pendencia=_limpar_pendencia_mente,
    salvar_memoria=salvar_memoria,
)
_processar_sugestao_visual_proativa = (
    _coordenador_visao_jogo_runtime.processar_sugestao_proativa
)
_ao_mapear_inventario_jogo = _coordenador_visao_jogo_runtime.ao_mapear_inventario
_registrar_analise_visual_jogo = _coordenador_visao_jogo_runtime.registrar_analise


_ponte_cooperacao_aplicacao_runtime = _criar_ponte_cooperacao_aplicacao_runtime(
    orquestrador_getter=lambda: _cooperacao_refs["orquestrador"],
    visao_analise_getter=lambda: _registro_visao_jogo_analise_runtime,
    visao_leitura_getter=lambda: _registro_visao_jogo_leitura_runtime,
    pendencia_jogo_getter=lambda: _pendencia_ativa_turno_mente(
        _estado_compartilhado_runtime.mental, dominio="jogo",
    ),
    contexto_jogo_getter=_modo_jogo_runtime.contexto_atual,
    detectar_pedido_visao=_detectar_pedido_visao_jogo_cooperativo,
    registrar_evidencia=_motor_aprendizado_runtime.registrar_evidencia,
    estado_mental_atualizar=lambda atualizador: _estado_compartilhado_runtime.atualizar(
        "mental", atualizador,
    ),
    registrar_evento_continuidade=_registrar_evento_continuidade_geral,
    quadro_getter=lambda: _cooperacao_refs["quadro"],
)
_registrar_progresso_visao_cooperativa = (
    _ponte_cooperacao_aplicacao_runtime.registrar_progresso_visao
)


_visao_jogo_servico = _composicao_visao_jogo_runtime.conectar_visao(
    contexto_jogo=_modo_jogo_runtime.contexto_atual,
    analisar_imagem=_analisar_com_groq_jogo,
    falar=falar_com_lipsync,
    sintetizar_texto=_sintetizar_pesquisa_jogo,
    ao_mapear_inventario=_ao_mapear_inventario_jogo,
    processar_sugestao_proativa=_processar_sugestao_visual_proativa,
    registrar_analise=_registrar_analise_visual_jogo,
    credencial_disponivel=(
        _composicao_inteligencia_externa_runtime.credencial_visual_disponivel
    ),
    permitido_presenca=lambda: not bool(
        not _diretor_presenca_runtime.presenca_habilitada("jogo")
        or _conversa_estado_get("is_speaking", False)
        or _turno_mental_em_andamento()
    ),
    interacao_iniciada=lambda: float(
        _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
    ) > 0.0,
    stop_event=_servicos_background_runtime.evento_parada,
    progresso_cooperativo=_registrar_progresso_visao_cooperativa,
)
_registro_visao_jogo_leitura_runtime = _registrar_visao_jogo_leitura(
    _criar_visao_jogo_leitura_runtime(visao=_visao_jogo_servico)
)
_registro_visao_jogo_analise_runtime = _registrar_visao_jogo_analise(
    _criar_visao_jogo_analise_runtime(visao=_visao_jogo_servico)
)
_observador_inventario_jogo_runtime = (
    _composicao_visao_jogo_runtime.observador_inventario
)
_observador_presenca_jogo_runtime = (
    _composicao_visao_jogo_runtime.observador_presenca
)


_continuar_visao_jogo_pendente = (
    _ponte_cooperacao_aplicacao_runtime.continuar_visao_pendente
)


_composicao_ciclo_comandos_runtime = _criar_composicao_ciclo_comandos_runtime(
    log=print,
    monitor_saude=_saude_mente_runtime,
    registrar_metrica=_observabilidade_mente_runtime.registrar_metrica,
    registrar_falha=_observabilidade_mente_runtime.registrar_falha,
    registrar_decisao=_observabilidade_mente_runtime.registrar_decisao,
)
executar_intencao = _composicao_ciclo_comandos_runtime.executar_intencao
_executar_comando_em_texto = _composicao_ciclo_comandos_runtime.executar_texto
processar_comandos_em_cadeia = _composicao_ciclo_comandos_runtime.processar_cadeia
processar_comando_deterministico = (
    _composicao_ciclo_comandos_runtime.processar_deterministico
)
resolver_comando_natural = (
    _composicao_ciclo_comandos_runtime.resolver_comando_natural
)
decisao_comando_ja_avaliada = (
    _composicao_ciclo_comandos_runtime.decisao_comando_ja_avaliada
)
_tentar_intencao_ai_primeiro = (
    _composicao_ciclo_comandos_runtime.tentar_intencao_ai_primeiro
)


_registrar_aprendizado_cooperativo = (
    _ponte_cooperacao_aplicacao_runtime.registrar_aprendizado
)
_registrar_continuidade_cooperativa = (
    _ponte_cooperacao_aplicacao_runtime.registrar_continuidade
)


_quadro_cooperacao_runtime = _criar_quadro_cooperacao_runtime(
    modo="ativo",
    publicar_contexto=lambda snapshot: _estado_compartilhado_runtime.atualizar_campos(
        "mental", cooperacao_habilidades=dict(snapshot or {}),
    ),
    log=print,
)
_cooperacao_refs["quadro"] = _quadro_cooperacao_runtime


_publicar_evento_agenda_cooperativo = (
    _ponte_cooperacao_aplicacao_runtime.publicar_evento_agenda
)
_detectar_visao_jogo_cooperativa = (
    _ponte_cooperacao_aplicacao_runtime.detectar_visao_jogo
)


_orquestrador_cooperativo_runtime = _criar_orquestrador_cooperativo_runtime(
    quadro=_quadro_cooperacao_runtime,
    clipboard_snapshot=_area_transferencia_runtime.snapshot_passivo,
    clipboard_getter=_area_transferencia_runtime.obter_texto_seguro,
    marcar_clipboard_consumido=(
        _observador_area_transferencia_runtime.marcar_conteudo_consumido
    ),
    executar_intencao=lambda resultado, texto: executar_intencao(resultado, texto),
    resolver_caminho=resolver_caminho,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    planejar_layout=lambda: planejar_organizacao_desktop(),
    detectar_visao_jogo=_detectar_visao_jogo_cooperativa,
    estado_getter=lambda: _estado_compartilhado_runtime.mental,
    pendencia_runtime=_pendencia_acao_runtime,
    classificar_confirmacao_contextual=(
        _feedback_pendente_runtime.classificar_confirmacao_contextual
    ),
    registrar_aprendizado=_registrar_aprendizado_cooperativo,
    registrar_decisao=_observabilidade_mente_runtime.registrar_decisao,
    registrar_continuidade=_registrar_continuidade_cooperativa,
    autorizar_acao=_autorizar_acao_pratica,
    log=print,
)
_cooperacao_refs["orquestrador"] = _orquestrador_cooperativo_runtime
_ponte_curadoria_cooperativa["publicar"] = (
    _orquestrador_cooperativo_runtime.registrar_curadoria_musical
)
_resolver_referencia_cooperativa = _orquestrador_cooperativo_runtime.resolver_referencia
_saude_mente_runtime.registrar(
    "orquestracao_cooperativa", "saudavel",
    detalhes=(
        "modo=ativo; fluxos governados=clipboard_para_arquivo,"
        "clipboard_pesquisa_llm,caixa_para_agenda,organizacao_desktop_inteligente,"
        "analise_item_jogo,curadoria_musical"
    ),
)


_executor_acoes_autonomas_runtime = _criar_executor_acoes_autonomas_runtime(
    executar_iot=_registro_iot_runtime.executar,
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    obter_volume=lambda: obter_volume_sistema(log=print),
    ajustar_volume=lambda nivel: ajustar_volume_sistema(nivel, log=print),
    falar=falar_com_lipsync,
    executar_intencao=executar_intencao,
    controlar_midia=lambda acao: bool(
        _registro_navegador_operacoes_runtime.controlar_youtube(acao)
    ),
)
_executar_acao_autonoma_segura = _executor_acoes_autonomas_runtime.executar
_desfazer_acao_autonoma_segura = _executor_acoes_autonomas_runtime.desfazer


_motor_iniciativa_runtime.definir_executor(
    _executar_acao_autonoma_segura,
    desfazer=_desfazer_acao_autonoma_segura,
)

_musica_conversacional_runtime = _criar_musica_conversacional_runtime_mente(
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    normalizar_texto=_normalizar_texto_com_apelidos,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    registrar_mente_curta=_registrar_mente_curta,
    executar_intencao=executar_intencao,
    registrar_resultado_execucao=_registrar_resultado_execucao,
    registrar_autoaprimoramento=_registrar_autoaprimoramento,
    modelo_llm=_registro_modelo_llm_runtime,
    buscar_resultados_musicais=_busca_musical_runtime.buscar_resultados,
    pendencia_runtime=_pendencia_acao_runtime,
    log=print,
)
_texto_pede_direcao_musical_generica = _musica_conversacional_runtime.texto_pede_direcao
_responder_pedido_direcao_musical_generica = _musica_conversacional_runtime.responder_pedido_direcao
_processar_confirmacao_sugestao_musical = _musica_conversacional_runtime.processar_confirmacao
_texto_pede_opiniao_musica_atual = _musica_conversacional_runtime.texto_pede_opiniao_atual
_responder_opiniao_musica_atual = _musica_conversacional_runtime.responder_opiniao_atual
_recomendar_musica_verificada = _musica_conversacional_runtime.recomendar_artista_verificado

ajustar_humor = _estado_contexto_runtime.ajustar_humor

_executar_controle_midia_nativo = _executar_controle_midia_nativo_mente

_coordenador_exec_runtime = _criar_coordenador_exec_runtime_mente(
    contexto_exec_getter=lambda: _contexto_exec_runtime,
    resposta_ia_getter=lambda: _resposta_ia_runtime,
    loop_getter=_ws_transport_runtime.obter_loop,
    log=print,
)
_executar_comando_conteudo = _coordenador_exec_runtime.executar


abrir_programa = _abrir_programa_mente
filtrar_apenas_fala = partial(_filtrar_apenas_fala_mente, historico=None, fallback_fala=FALLBACK_FALA_NEUTRA)

limpar_diccao_e_ruido = _limpar_diccao_e_ruido_mente


get_status_humor_prompt = _estado_contexto_runtime.status_humor_prompt

parsear_resposta_json = partial(_parsear_resposta_json_mente, fallback_fala=FALLBACK_FALA_NEUTRA)


_agendar_entrada_canonica = partial(
    _agendar_entrada_canonica_mente,
    modo_jogo_ativo=lambda: bool(_modo_jogo_runtime.ativo),
    agendar=_coordenador_exec_runtime.agendar,
)


_processar_entrada_barra = partial(_agendar_entrada_canonica, canal="barra")
_processar_entrada_voz = partial(_agendar_entrada_canonica, canal="voz")
_processar_entrada_terminal = partial(_agendar_entrada_canonica, canal="terminal")

_barra_comando_runtime = _composicao_visual_runtime.conectar_barra(
    processar_texto=_processar_entrada_barra,
    keyboard_mod=keyboard,
    hotkey=HOTKEY_BARRA_COMANDO,
    modo_jogo_ativo=lambda: bool(_modo_jogo_runtime.ativo),
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
    processar_texto=_processar_entrada_voz,
    esta_falando=lambda: bool(_conversa_estado_get("is_speaking", False)),
    modo_chat_ativo=lambda: bool(_conversa_estado_get("modo_chat", False)),
    escuta_permitida=lambda: not bool(
        _conversa_estado_get("modo_chat", False)
        or _conversa_estado_get("conversa_ativa", False)
    ),
    modo_jogo_ativo=lambda: bool(_modo_jogo_runtime.ativo),
    atividade_visual=_definir_atividade_visual,
    ultima_fala_laylay=lambda: str(_estado_compartilhado_runtime.mental.get("ultima_resposta") or ""),
    vocabulario_dinamico=_vocabulario_dinamico_voz,
    pronuncias_aprendidas=_pronuncias_aprendidas_voz,
    salvar_pronuncia=_salvar_pronuncia_voz,
    reconhecer_comando_pessoal=_reconhecedor_voz_pessoal.reconhecer,
    solicitar_confirmacao=falar_com_lipsync,
    sounddevice_mod=sd,
    limpar_texto=limpar_diccao_e_ruido,
    deve_continuar=lambda: not _servicos_background_runtime.deve_parar(),
    log=print,
)

_interacao_chat_runtime = _criar_interacao_chat_runtime_mente(
    estado_runtime_getter=lambda: _estado_compartilhado_runtime,
    modo_chat_runtime_getter=lambda: _modo_chat_runtime,
    abertura_runtime_getter=lambda: _abertura_chat_runtime,
    processar_texto=_processar_entrada_terminal,
    escutar_terminal=_escutar_texto_terminal_mente,
    keyboard_mod=keyboard,
    hotkey_liga=HOTKEY_MODO_CHAT_LIGA,
    hotkey_desliga=HOTKEY_MODO_CHAT_DESLIGA,
    # No roteiro automatizado, o próprio executor publica cada bloco
    # ``💬 Você:``. Manter o leitor interativo concorrente desenhava um segundo
    # prompt (`> 💬 Você:`) e ainda poderia consumir teclas acidentalmente.
    stdin_getter=lambda: (
        None
        if "--roteiro" in set(sys.argv[1:])
        else getattr(sys, "stdin", None)
    ),
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
_estado_conversa_runtime = _criar_estado_conversa_runtime(
    getter=lambda: _memoria_conversa_get("messages", []),
    setter=_definir_messages_resposta_ia,
)


def _estado_terminal_2() -> dict:
    conversa = _estado_compartilhado_runtime.snapshot().get("conversacional", {})
    modo_chat = bool(conversa.get("modo_chat") or conversa.get("conversa_ativa"))
    ouvido_ativo = bool(_ouvido_whisper_runtime.ativo()) and (
        "Laylay-Ouvido" in set(_servicos_background_runtime.ativos())
    )
    return {
        "visual_activity": conversa.get("visual_activity", "idle"),
        "current_emotion": conversa.get("current_emotion", "calma"),
        "emotion_level": conversa.get("emotion_level", 1),
        "is_speaking": conversa.get("is_speaking", False),
        "voice_available": ouvido_ativo,
        "microphone_level": (
            _ouvido_whisper_runtime.nivel_microfone()
            if ouvido_ativo else 0.0
        ),
        "interaction_mode": "chat" if modo_chat else "voice",
    }


_reinicio_aplicacao_solicitado = _threading.Event()


def _solicitar_reinicio_aplicacao() -> bool:
    if _reinicio_aplicacao_solicitado.is_set():
        return False
    _reinicio_aplicacao_solicitado.set()
    return True


_configuracao_llm_ativa_dashboard = _configuracao_aplicacao_runtime.estado()
_letras_lrclib_runtime = _criar_letras_lrclib_runtime(log=print)
_telemetria_gpu_runtime = _criar_telemetria_gpu_runtime()
_telemetria_rede_runtime = _criar_telemetria_rede_runtime(psutil_mod=psutil)
_saidas_audio_runtime = GerenciadorSaidasAudioWindows(log=print)
_dashboard_terminal_runtime = _criar_dashboard_terminal_runtime(
    # Configurações salvas exigem reinício; o painel deve continuar mostrando
    # o provedor/modelo realmente carregado neste processo, não o próximo.
    configuracao_getter=lambda: dict(_configuracao_llm_ativa_dashboard),
    llm_getter=lambda: _diagnostico_conversa_llm_tipadas(),
    interacao_getter=_estado_terminal_2,
    memoria_saude_getter=MEMORIA_SQLITE.diagnostico_aprendizados,
    agenda_getter=_agenda_runtime.load,
    aprendizados_getter=MEMORIA_SQLITE.consultar_aprendizados,
    estado_mental_getter=lambda: _estado_compartilhado_runtime.snapshot().get(
        "mental", {}
    ),
    contexto_jogo_getter=_modo_jogo_runtime.contexto_atual,
    capacidade_getter=_mapa_habilidades_runtime.consultar,
    musica_getter=lambda: {
        **dict(_registro_musica_leitura_runtime.estado() or {}),
        "player": dict(playlist_state.get("player") or {}),
        "playlist": str(playlist_state.get("name") or ""),
    },
    playlists_getter=_playlist_runtime.catalogo_publico,
    playlist_queue_getter=_playlist_runtime.fila_publica,
    audio_output_getter=_saidas_audio_runtime.snapshot,
    volume_getter=lambda: obter_volume_sistema(log=lambda _mensagem: None),
    iot_getter=_registro_iot_runtime.retrato_para_mente,
    letras_getter=_letras_lrclib_runtime.snapshot,
    gpu_getter=_telemetria_gpu_runtime.snapshot,
    network_getter=_telemetria_rede_runtime.snapshot,
    psutil_mod=psutil,
    projeto="Laylay",
    cidade=BRIEFING_CIDADE,
    log=print,
)


_desktop_bridge_runtime = _criar_desktop_bridge_runtime(
    enviar_entrada=lambda texto: _agendar_entrada_canonica(texto, canal="desktop"),
    historico_getter=_estado_conversa_runtime.mensagens,
    estado_getter=_estado_terminal_2,
    dashboard_getter=_dashboard_terminal_runtime.snapshot,
    resultado_acao_getter=lambda: dict(
        _estado_compartilhado_runtime.mental.get("plano_turno_atual") or {}
    ),
    executar_acao_painel=lambda acao_id, payload: _executar_acao_painel_tipado(
        acao_id,
        payload,
        executar_intencao=executar_intencao,
        selecionar_saida_audio=_saidas_audio_runtime.selecionar,
    ),
    modo_setter=lambda ativo: _definir_modo_chat(ativo, origem="terminal_2"),
    configuracao_getter=_configuracao_aplicacao_runtime.estado,
    configuracao_setter=_configuracao_aplicacao_runtime.atualizar,
    reiniciar_aplicacao=_solicitar_reinicio_aplicacao,
    port=int(os.environ.get("LAYLAY_TERMINAL_2_PORTA", "0") or 0),
    log=print,
)
_otimizacoes_desempenho_refs["desktop_bridge"] = _desktop_bridge_runtime
_publicacao_visual_antecipada_ativa = _flag_desempenho_ativa(
    "LAYLAY_PUBLICACAO_VISUAL_ANTECIPADA"
)
# O Terminal é um canal textual: sua resposta não pode depender de síntese,
# reprodução ou aceitação da fila de voz. A flag permanece no diagnóstico da
# implantação, mas a entrega correta do texto é uma garantia funcional.
_orquestrador_fala_runtime.registrar_observador_texto_final(
    _desktop_bridge_runtime.publicar_fala_final,
)


_interpretacao_intencao_runtime = _criar_interpretacao_intencao_runtime_mente(
    contexto_getter=lambda: {
        "estado": {
            "messages": _memoria_conversa_get("messages", []),
            "mente_integrada_estado": _estado_compartilhado_runtime.mental,
            "playlist_state": {
                "name": _registro_musica_leitura_runtime.estado().get(
                    "playlist_ativa", ""
                ),
                "index": _registro_musica_leitura_runtime.estado().get("indice", 0),
            },
            "playlists_carregadas": _registro_musica_leitura_runtime.indice_usuario(),
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
        "extrair_json_da_ia": _extrair_json_da_ia,
        "playlist_bloqueada_agora": _playlist_bloqueada_agora,
        "texto_pede_playlist_explicitamente": _texto_pede_playlist_explicitamente,
        "texto_parece_consulta_operacional": _texto_parece_consulta_operacional,
        "mapa_habilidades_prompt": _mapa_habilidades_runtime.contexto_para_prompt,
        "mapa_recursos_prompt": _mapa_recursos_runtime.contexto_para_prompt,
    },
    modelo_llm=_registro_modelo_llm_runtime,
    log=print,
)


_abertura_chat_runtime = _criar_abertura_chat_runtime_mente(
    estado_getter=lambda: {
        "messages": _memoria_conversa_get("messages", []),
        "current_emotion": _conversa_estado_get("current_emotion", "calma"),
        "emotion_level": _conversa_estado_get("emotion_level", 1),
    },
    modelo_llm=_registro_modelo_llm_runtime,
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
    ),
    log=print,
)
analisar_intencao = _interpretacao_intencao_runtime.analisar


            # ====================== GMAIL IMAP — RUNTIME ======================

_central_notificacoes_runtime = _criar_central_notificacoes_runtime_mente(
    os.path.join(_base_dir, CENTRAL_NOTIFICACOES_ARQUIVO),
    falar_cb=falar_com_lipsync,
    agendar_fala_cb=_agendar_fala_proativa,
    agenda_getter=_agendamentos_load,
    modo_jogo_getter=lambda: bool(_modo_jogo_runtime.ativo),
    conversa_ativa_getter=lambda: bool(_conversa_estado_get("conversa_ativa", False)),
    is_speaking_getter=lambda: bool(_conversa_estado_get("is_speaking", False)),
    contexto_atualizar_cb=lambda **campos: (
        _estado_compartilhado_runtime.atualizar_campos("mental", **campos)
    ),
    registrar_aprendizado_cb=_motor_aprendizado_runtime.registrar_evidencia,
    log=print,
)
_central_notificacoes_executar = _central_notificacoes_runtime.executar
_central_notificacoes_ingerir_sistema = _central_notificacoes_runtime.ingerir_alerta_sistema
_agenda_runtime.notificar_evento_cb = _central_notificacoes_runtime.ingerir_agendamento
_mapa_recursos_runtime.registrar(
    "central_notificacoes",
    arquivo="memoria/central_notificacoes.json",
    descricao=(
        "avisos priorizados de email, agenda, lembretes e alertas internos; "
        "agrupa repetidos e respeita categorias silenciosas"
    ),
    termos=(
        "notificacao", "notificacoes", "avisos", "alertas", "avisos importantes",
        "o que precisa da minha atencao", "central de notificacoes",
    ),
    leitor=lambda _texto="": _central_notificacoes_runtime.diagnostico(),
    escrita_via="preferências explícitas da central de notificações",
    intent_consulta="NOTIFICATIONS",
)

_gmail_runtime = _criar_composicao_gmail_laylay_runtime(
    arquivo_estado=GMAIL_ARQUIVO,
    continuidades_set=_continuidades_set,
    agendar_fala_proativa=_agendar_fala_proativa,
    is_speaking_getter=lambda: bool(_conversa_estado_get("is_speaking", False)),
    modo_jogo_getter=lambda: bool(_modo_jogo_runtime.ativo),
    centralizar_notificacoes_cb=_central_notificacoes_runtime.ingerir_emails,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    log=print,
    stop_event=_servicos_background_runtime.evento_parada,
)
_gmail_nao_lidos_cache = _gmail_runtime.nao_lidos_cache
_gmail_configurado = _gmail_runtime.configurado
_gmail_silenciar_remetente = _gmail_runtime.silenciar_remetente
_gmail_buscar_nao_lidos = _gmail_runtime.buscar_nao_lidos
_gmail_falar_resumo_estiloso = _gmail_runtime.falar_resumo_estiloso
gmail_daemon = _gmail_runtime.daemon

_registros_principais_runtime = _criar_registros_principais(
    memoria_pessoas=_registro_memoria_pessoas_runtime,
    iot=_registro_iot_runtime,
    arquivos_leitura=_registro_arquivos_leitura_runtime,
    arquivos_mutacao=_registro_arquivos_mutacao_runtime,
    musica_leitura=_registro_musica_leitura_runtime,
    musica_operacoes=_registro_musica_operacoes_runtime,
    navegador_leitura=_registro_navegador_leitura_runtime,
    navegador_operacoes=_registro_navegador_operacoes_runtime,
    visao_jogo_leitura=_registro_visao_jogo_leitura_runtime,
    visao_jogo_analise=_registro_visao_jogo_analise_runtime,
    modelo_llm=_registro_modelo_llm_runtime,
    estado_conversa=_estado_conversa_runtime,
)

# Uma única captura allowlist substitui o compartilhamento irrestrito do
# namespace. Serviços criados abaixo são publicados explicitamente.
_registro_servicos_aplicacao_runtime = _criar_registro_servicos_aplicacao_runtime(
    globals(),
)

_composicao_contextos_ia_runtime = _criar_composicao_contextos_ia_runtime(
    memoria_sqlite=MEMORIA_SQLITE,
    base_system_prompt=BASE_SYSTEM_PROMPT,
    servicos=_registro_servicos_aplicacao_runtime.snapshot(),
    messages_getter=_estado_conversa_runtime.mensagens,
    conversa_getter=_conversa_estado_get,
    mente_getter=lambda: _estado_compartilhado_runtime.mental,
    aba_getter=lambda: (
        _chrome_estado.aba_titulo_atual, _chrome_estado.aba_url_atual,
    ),
    musica_leitura=_registros_principais_runtime.musica_leitura,
    musica_operacoes=_registros_principais_runtime.musica_operacoes,
    navegador_leitura=_registros_principais_runtime.navegador_leitura,
    navegador_operacoes=_registros_principais_runtime.navegador_operacoes,
    visao_jogo_leitura=_registros_principais_runtime.visao_jogo_leitura,
    visao_jogo_analise=_registros_principais_runtime.visao_jogo_analise,
    modelo_llm=_registro_modelo_llm_runtime,
    gmail_cache_getter=lambda: _gmail_nao_lidos_cache,
    falhas_getter=lambda: _falhas_consecutivas,
    verificar_fala_turno=lambda fala, origem="ia_final": (
        _verificar_fala_do_turno(fala, origem=origem)
    ),
    executar_conteudo_cb=_executar_comando_conteudo_mente,
    mapa_habilidades_prompt=_mapa_habilidades_runtime.contexto_para_prompt,
    mapa_recursos_prompt=_mapa_recursos_runtime.contexto_para_prompt,
    registrar_tamanho_prompt=_observabilidade_mente_runtime.registrar_tamanho_prompt,
    otimizacao_prompt_ativa=os.environ.get(
        "LAYLAY_OTIMIZACAO_PROMPT_ATIVA", "1",
    ).casefold() not in {"0", "false", "nao", "não", "off"},
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    log=print,
)
_contexto_prompt_runtime = _composicao_contextos_ia_runtime.prompt
_contexto_exec_runtime = _composicao_contextos_ia_runtime.execucao
_contexto_dispatcher_runtime = _composicao_contextos_ia_runtime.dispatcher
_contexto_finalizacao_runtime = _composicao_contextos_ia_runtime.finalizacao


def _diagnostico_conversa_llm_tipadas() -> dict:
    prompt = _contexto_prompt_runtime.diagnostico()
    modelo = _registro_modelo_llm_runtime.diagnostico()
    estado = _estado_conversa_runtime.diagnostico()
    return {
        "prompt_disponivel": bool(prompt.get("disponivel")),
        "modelo_disponivel": bool(modelo.get("disponivel")),
        "estado_disponivel": bool(estado.get("disponivel")),
        "requisicoes": int(modelo.get("requisicoes") or 0),
        "sucessos": int(modelo.get("sucessos") or 0),
        "prompts_rapidos": int(prompt.get("preparacoes_rapidas") or 0),
        "otimizacao_prompt_ativa": bool(prompt.get("otimizacao_prompt_ativa")),
        "fontes_prompt_consultadas": dict(prompt.get("fontes_consultadas") or {}),
        "fontes_prompt_poupadas": dict(prompt.get("fontes_poupadas") or {}),
        "falhas": int(modelo.get("falhas") or 0) + int(prompt.get("falhas") or 0),
        "falhas_consecutivas": int(modelo.get("falhas_consecutivas") or 0),
        "estado": str(modelo.get("estado") or "saudavel"),
        "ultima_falha_codigo": str(modelo.get("ultima_falha_codigo") or ""),
        "memoria_exposta": False,
        "credencial_exposta": False,
        "autoriza_execucao": False,
    }


_composicao_entrada_interacao_runtime = _criar_composicao_entrada_interacao_runtime(
    servicos=_registro_servicos_aplicacao_runtime.snapshot(),
    registros_principais=_registros_principais_runtime,
    estado_mental_getter=lambda: _estado_compartilhado_runtime.mental,
    sites_diretos=SITES_DIRECTOS,
    apps_map=APPS_MAP,
)
_deteccao_deterministica_runtime = _composicao_entrada_interacao_runtime.deteccao
detectar_intencao_deterministica = _deteccao_deterministica_runtime.detectar
_registro_servicos_aplicacao_runtime.publicar(
    detectar_intencao_deterministica=detectar_intencao_deterministica,
)
_contexto_intencao_runtime, _ciclo_comandos_runtime = (
    _composicao_ciclo_comandos_runtime.conectar(
        servicos=_registro_servicos_aplicacao_runtime.snapshot(),
        estado_getter=_estado_contexto_intencao,
        registros_principais=_registros_principais_runtime,
    )
)
_registro_servicos_aplicacao_runtime.publicar(
    _contexto_intencao_runtime=_contexto_intencao_runtime,
    _ciclo_comandos_runtime=_ciclo_comandos_runtime,
)

_disponibilidade_operacional_runtime = _criar_disponibilidade_operacional_runtime(
    navegador_leitura_getter=_registro_navegador_leitura_runtime.diagnostico,
    navegador_operacoes_getter=_registro_navegador_operacoes_runtime.diagnostico,
    conversa_llm_getter=_diagnostico_conversa_llm_tipadas,
    visao_leitura_getter=_registro_visao_jogo_leitura_runtime.diagnostico,
    visao_analise_getter=_registro_visao_jogo_analise_runtime.diagnostico,
    area_transferencia_getter=_area_transferencia_runtime.diagnostico,
    caixa_entrada_getter=_caixa_entrada_pessoal_runtime.diagnostico,
    notificacoes_getter=_central_notificacoes_runtime.diagnostico,
    iot_getter=_registro_iot_runtime.diagnostico,
    avatar_getter=_avatar_runtime.diagnostico,
)
_mapa_habilidades_runtime.conectar_disponibilidade_operacional(
    _disponibilidade_operacional_runtime.snapshot,
)


_diagnostico_mente_runtime = _criar_diagnostico_mente_runtime(
    estado_getter=_estado_compartilhado_runtime.snapshot,
    saude_getter=lambda: (
        _auditar_saude_mente(),
        _saude_mente_runtime.snapshot(),
    )[1],
    rede_associativa_getter=_rede_associativa_runtime.diagnostico,
    mapa_habilidades_getter=_mapa_habilidades_runtime.diagnostico,
    pesquisa_arquivos_getter=_registro_arquivos_leitura_runtime.diagnostico,
    mutacoes_arquivos_getter=_registro_arquivos_mutacao_runtime.diagnostico,
    musica_leitura_getter=_registro_musica_leitura_runtime.diagnostico,
    musica_operacoes_getter=_registro_musica_operacoes_runtime.diagnostico,
    navegador_leitura_getter=_registro_navegador_leitura_runtime.diagnostico,
    navegador_operacoes_getter=_registro_navegador_operacoes_runtime.diagnostico,
    visao_jogo_leitura_getter=_registro_visao_jogo_leitura_runtime.diagnostico,
    visao_jogo_analise_getter=_registro_visao_jogo_analise_runtime.diagnostico,
    conversa_llm_getter=_diagnostico_conversa_llm_tipadas,
    composicao_principal_getter=_registros_principais_runtime.diagnostico,
    orquestracao_cooperativa_getter=_orquestrador_cooperativo_runtime.diagnostico,
    agenda_getter=_agenda_runtime.diagnostico,
    memoria_pessoas_getter=_registro_memoria_pessoas_runtime.diagnostico,
    aprendizado_getter=MEMORIA_SQLITE.diagnostico_aprendizados,
    linguagem_natural_getter=lambda: {
        **_composicao_ciclo_comandos_runtime.diagnostico_linguagem_natural(),
        "tolerancia_portugues": (
            _linguagem_aprendida_runtime.diagnostico_tolerancia_portugues()
        ),
    },
    fala_operacional_getter=lambda: {
        **_orquestrador_fala_runtime.diagnostico(),
        "emocao_causal": _avaliador_eventos_emocionais_runtime.diagnostico(),
    },
    estrutura_getter=lambda: _estado_compartilhado_runtime.validar_estrutura(
        conexoes={
            "estado_compartilhado": _estado_compartilhado_runtime,
            "pendencia_runtime": _pendencia_acao_runtime,
            "classificador_confirmacao": _classificar_confirmacao_local,
            "motor_aprendizado": _motor_aprendizado_runtime,
            "aprendizado_runtime": _aprendizado_runtime,
        },
    ),
    disponibilidade_operacional_getter=(
        _disponibilidade_operacional_runtime.snapshot
    ),
    area_transferencia_getter=_area_transferencia_runtime.diagnostico,
    caixa_entrada_getter=_caixa_entrada_pessoal_runtime.diagnostico,
    notificacoes_getter=_central_notificacoes_runtime.diagnostico,
    iot_getter=_registro_iot_runtime.diagnostico,
    avatar_getter=_avatar_runtime.diagnostico,
    dashboard_getter=_dashboard_terminal_runtime.diagnostico,
    pc_b_getter=_pc_b_runtime.diagnostico,
    falar=lambda texto, emocao="calma", nivel=1: falar_com_lipsync(texto, emocao, nivel),
    log=print,
)
_mostrar_diagnostico_mente = _diagnostico_mente_runtime.mostrar
_registro_servicos_aplicacao_runtime.publicar(
    _mostrar_diagnostico_mente=_mostrar_diagnostico_mente,
)

_comandos_imediatos_runtime, _contexto_inicio_chat_runtime = (
    _composicao_entrada_interacao_runtime.conectar(
        servicos=_registro_servicos_aplicacao_runtime.snapshot(),
        loop_getter=_ws_transport_runtime.obter_loop,
        estado_chat_getter=lambda: {
            "messages": _memoria_conversa_get("messages", []),
            "current_emotion": _conversa_estado_get("current_emotion", "calma"),
            "emotion_level": _conversa_estado_get("emotion_level", 1),
        },
        memoria_sqlite=MEMORIA_SQLITE,
    )
)
_processar_comandos_prioritarios = _comandos_imediatos_runtime.processar_prioritarios

_contexto_inicio_chat = _contexto_inicio_chat_runtime.montar


_composicao_turno_runtime = _criar_composicao_turno_runtime(
    servicos=_registro_servicos_aplicacao_runtime.snapshot(),
)
_iniciar_planejamento_turno = _composicao_turno_runtime.iniciar
_atualizar_planejamento_turno = _composicao_turno_runtime.atualizar
_verificar_fala_do_turno = _composicao_turno_runtime.verificar_fala
_registrar_leitura_semantica_principal = (
    _composicao_turno_runtime.registrar_leitura_semantica
)
_registro_servicos_aplicacao_runtime.publicar(
    _verificar_fala_do_turno=_verificar_fala_do_turno,
)
_servicos_aplicacao_finais = _registro_servicos_aplicacao_runtime.snapshot()
_preferencias_sugestoes_runtime.conectar_servicos(_servicos_aplicacao_finais)
_contexto_imediato_runtime.conectar_servicos(_servicos_aplicacao_finais)
_ambiente_navegacao_runtime.conectar_servicos(_servicos_aplicacao_finais)
_composicao_chrome_ws_runtime.conectar_servicos(_servicos_aplicacao_finais)
_composicao_estado_aplicacao_runtime.conectar(
    servicos=_servicos_aplicacao_finais,
)
_composicao_resposta_conversacional_runtime.conectar(
    servicos=_servicos_aplicacao_finais,
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
        "modo_jogo_ativo": lambda: bool(_modo_jogo_runtime.ativo),
        "contexto_inicio": _contexto_inicio_chat,
        "processar_inicio_fluxo": _processar_inicio_fluxo_resposta_ia_mente,
        "usar_modo_rapido": _usar_modo_rapido_conversa,
        "texto_depende_de_contexto": _texto_depende_de_contexto,
        "preparacao_conversa": _contexto_prompt_runtime,
        "estado_conversa": _registros_principais_runtime.estado_conversa,
        "modelo_llm": _registro_modelo_llm_runtime,
        "fallback_fala": FALLBACK_FALA_NEUTRA,
        "preparar_resposta": lambda texto, resposta_bruta: _preparar_resposta_para_execucao_mente(
            texto,
            resposta_bruta,
            modelo_llm=_registro_modelo_llm_runtime,
            limpar_texto_fala_cb=_limpar_texto_fala_ia,
            fallback_fala=FALLBACK_FALA_NEUTRA,
            memoria_sqlite=MEMORIA_SQLITE,
            registrar_autocorrecao_cb=_registrar_autocorrecao_virtual,
            registrar_falha_cb=_observabilidade_mente_runtime.registrar_falha,
            contexto_contingencia=dict(_estado_compartilhado_runtime.mental),
            contexto_comunicacao={
                "plano_turno": dict(
                    _estado_compartilhado_runtime.mental.get("plano_turno_atual") or {}
                ),
                "mensagens": list(_memoria_conversa_get("messages", []) or []),
            },
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
        "registrar_mente_curta": _registrar_mente_curta,
        "salvar_memoria": salvar_memoria,
        "definir_emocao_resposta": _definir_emocao_conversacional,
        "registrar_metrica_diagnostico": _observabilidade_mente_runtime.registrar_metrica,
        "iniciar_trace_diagnostico": _observabilidade_mente_runtime.iniciar_trace_turno,
        "atualizar_trace_diagnostico": _observabilidade_mente_runtime.atualizar_trace_turno,
        "finalizar_trace_diagnostico": _observabilidade_mente_runtime.finalizar_trace_turno,
        "iniciar_orcamento_llm_turno": _orcamento_llm_turno_runtime.iniciar_turno,
        "configurar_orcamento_llm_turno": _orcamento_llm_turno_runtime.configurar_turno,
        "finalizar_orcamento_llm_turno": _orcamento_llm_turno_runtime.finalizar_turno,
        "registrar_falha_diagnostico": _observabilidade_mente_runtime.registrar_falha,
        "registrar_decisao_diagnostico": _observabilidade_mente_runtime.registrar_decisao,
        "observar_feedback_presenca": _diretor_presenca_runtime.observar_resposta,
                            },
    log=print,
)


# ====================== FIM DAS FUNÇÕES GMAIL ======================

_auditar_saude_mente = _adaptadores_aplicacao_runtime.auditar_saude_mente


_composicao_servicos_runtime = _criar_composicao_servicos_padrao(
    _registro_servicos_aplicacao_runtime.snapshot(),
    gerenciador=_servicos_background_runtime,
    registrar_falha=_observabilidade_mente_runtime.relatar_falha,
    registrar_metrica=_observabilidade_mente_runtime.registrar_metrica,
    inicializacao_diferida=_flag_desempenho_ativa(
        "LAYLAY_INICIALIZACAO_DUAS_FASES"
    ),
    log=print,
)


def _encerrar_laylay() -> None:
    try:
        _letras_lrclib_runtime.parar()
        _dashboard_terminal_runtime.parar()
        _desktop_bridge_runtime.parar()
        _composicao_servicos_runtime.encerrar()
    finally:
        _runtime_llm_portatil.encerrar()


def _argumentos_roteiro_teste(argumentos: list[str]) -> dict[str, Any]:
    resultado: dict[str, Any] = {
        "caminho": "",
        "retomar": False,
        "resultado_raiz": os.path.join(_base_dir, "resultados_testes"),
    }
    indice = 0
    while indice < len(argumentos):
        atual = str(argumentos[indice] or "")
        if atual == "--roteiro" and indice + 1 < len(argumentos):
            resultado["caminho"] = argumentos[indice + 1]
            indice += 2
            continue
        if atual == "--resultado-raiz" and indice + 1 < len(argumentos):
            resultado["resultado_raiz"] = argumentos[indice + 1]
            indice += 2
            continue
        if atual == "--retomar":
            resultado["retomar"] = True
        indice += 1
    return resultado


def main():
    """Ponto de entrada principal da Laylay."""
    inicio_programa_ts = time.time()
    argumentos_roteiro = _argumentos_roteiro_teste(list(sys.argv[1:]))
    caminho_roteiro = str(argumentos_roteiro.get("caminho") or "").strip()
    configuracao_roteiro = None
    diretorio_resultado_roteiro = None
    espelhos_terminal: tuple[Any, Any] = ()
    if caminho_roteiro:
        try:
            configuracao_roteiro = _carregar_configuracao_roteiro(caminho_roteiro)
            diretorio_resultado_roteiro = _preparar_diretorio_resultado_roteiro(
                caminho_roteiro,
                raiz=str(argumentos_roteiro["resultado_raiz"]),
                retomar=bool(argumentos_roteiro["retomar"]),
            )
            espelhos_terminal = _instalar_espelho_terminal_roteiro(
                diretorio_resultado_roteiro,
            )
            print(
                "🧪 [ROTEIRO] persistência ativada antes dos testes | "
                f"pasta={diretorio_resultado_roteiro}"
            )
            if configuracao_roteiro.silenciar_voz_durante_teste:
                _voz_runtime.definir_modo_silencioso(
                    True, origem="roteiro_teste",
                )
        except Exception as erro:
            print(
                "❌ [ROTEIRO] não foi possível carregar o teste | "
                f"tipo={type(erro).__name__} detalhe={erro}"
            )
            return

    def usuario_ja_iniciou_conversa() -> bool:
        ultima_entrada = float(
            _estado_compartilhado_runtime.mental.get("ultima_entrada_ts") or 0.0
        )
        return bool(
            ultima_entrada >= inicio_programa_ts
            or _conversa_estado_get("modo_chat", False)
            or _conversa_estado_get("conversa_ativa", False)
        )

    if _flag_desempenho_ativa("LAYLAY_PREAQUECER_LLM"):
        _servicos_background_runtime.iniciar(
            "Laylay-Preaquecimento-LLM",
            partial(
                _runtime_llm_portatil.preaquecer,
                interacao_ativa=usuario_ja_iniciou_conversa,
            ),
        )

    if os.environ.get("LAYLAY_TERMINAL_2", "1").casefold() not in {
        "0", "false", "nao", "não", "off", "desligado",
    }:
        _desktop_bridge_runtime.iniciar()
        _desktop_bridge_runtime.iniciar_cliente(
            os.path.join(_base_dir, "cliente", "terminal_laylay_2.py")
        )
    _auditar_saude_mente()
    resultado_inicializacao = _composicao_servicos_runtime.iniciar(_inicializacao_runtime)
    nome_observador_clipboard = "Laylay-Observador-Área-Transferência"
    ativos_background = set(_servicos_background_runtime.ativos())
    if nome_observador_clipboard not in ativos_background:
        _servicos_background_runtime.iniciar(
            nome_observador_clipboard,
            _observador_area_transferencia_runtime.executar,
        )
        ativos_background = set(_servicos_background_runtime.ativos())
    observador_clipboard_ativo = nome_observador_clipboard in ativos_background
    print(
        "📋 [CLIPBOARD:INÍCIO] "
        f"serviço={'ativo' if observador_clipboard_ativo else 'inativo'} "
        f"modo={_observador_area_transferencia_runtime.modo}"
    )
    if not observador_clipboard_ativo:
        _observabilidade_mente_runtime.relatar_falha(
            "observador_area_transferencia",
            "servico_nao_iniciado",
            erro=RuntimeError("thread do observador não ficou ativa"),
        )
    falas_iniciais_ativas = str(
        os.environ.get("LAYLAY_FALAS_INICIAIS", "0") or "0"
    ).strip().casefold() in {"1", "true", "sim", "on", "ligado"}
    briefing_inicial_ativo = str(
        os.environ.get("LAYLAY_BRIEFING_INICIAL", "1") or "1"
    ).strip().casefold() not in {"0", "false", "nao", "não", "off", "desligado"}
    tipo_fala_inicial = _selecionar_fala_inicial_ambiente(
        usuario_iniciou=usuario_ja_iniciou_conversa(),
        briefing_pendente=(
            carregar_estado_briefing() != time.strftime("%Y-%m-%d")
        ),
        briefing_ativo=briefing_inicial_ativo,
        abertura_ativa=falas_iniciais_ativas,
    )
    if tipo_fala_inicial == "briefing":
        briefing_matinal()
    elif tipo_fala_inicial == "abertura":
        abertura_inicial = _abertura_chat_runtime.gerar_local("inicio")
        if not _entregar_fala_inicial_confirmada(
            "abertura", abertura_inicial, "calma", 1,
        ):
            abertura_fallback = _abertura_chat_runtime.gerar_local("inicio")
            print(f"╭─ ◕‿◕ Laylay: {abertura_fallback}")
    roteiro_finalizado = _threading.Event()
    roteiro_runtime = None
    if configuracao_roteiro is not None and diretorio_resultado_roteiro is not None:
        def finalizar_roteiro(_sucesso: bool) -> None:
            if configuracao_roteiro.silenciar_voz_durante_teste:
                _voz_runtime.definir_modo_silencioso(
                    False, origem="roteiro_teste_finalizado",
                )
            roteiro_finalizado.set()

        roteiro_runtime = _RoteiroTesteConversaRuntime(
            configuracao_roteiro,
            enviar_entrada=lambda texto: _agendar_entrada_canonica(
                texto, canal="roteiro_teste",
            ),
            resultado_getter=lambda: dict(
                _estado_compartilhado_runtime.mental.get("plano_turno_atual") or {}
            ),
            voz_ocupada_getter=lambda: bool(
                _conversa_estado_get("is_speaking", False)
                or _conversa_estado_get("audio_playing", False)
                or not _voz_runtime.fila.empty()
            ),
            ativar_modo_chat=lambda: _definir_modo_chat(
                True, origem="roteiro_teste",
            ),
            modo_chat_ativo_getter=lambda: bool(
                _conversa_estado_get("modo_chat", False)
                or _conversa_estado_get("conversa_ativa", False)
            ),
            diretorio_resultado=diretorio_resultado_roteiro,
            retomar=bool(argumentos_roteiro["retomar"]),
            ao_finalizar=finalizar_roteiro,
            log=print,
        )
        _orquestrador_fala_runtime.registrar_observador_texto_final(
            roteiro_runtime.observar_resposta,
        )
        roteiro_runtime.iniciar()

    _inicializacao_runtime.manter_ativo(
        fala_pronta="",
        ao_encerrar=_encerrar_laylay,
        deve_encerrar=lambda: bool(
            _reinicio_aplicacao_solicitado.is_set()
            or (
                configuracao_roteiro is not None
                and configuracao_roteiro.encerrar_ao_final
                and roteiro_finalizado.is_set()
            )
        ),
    )
    if _reinicio_aplicacao_solicitado.is_set():
        argumentos = construir_argumentos_reinicio(
            sys.executable,
            script=__file__,
            argumentos=sys.argv[1:],
            empacotado=bool(getattr(sys, "frozen", False)),
        )
        print("♻️ [LAYLAY] serviços encerrados; iniciando uma sessão limpa.")
        try:
            _instancia_unica_runtime.liberar()
            os.execv(sys.executable, argumentos)
        except OSError as erro:
            print(f"⚠️ [LAYLAY] não consegui reiniciar o processo: {erro}")
    if espelhos_terminal:
        sys.stdout = espelhos_terminal[0].original
        sys.stderr = espelhos_terminal[1].original
    for espelho in espelhos_terminal:
        fechar = getattr(espelho, "fechar", None)
        if callable(fechar):
            fechar()
if __name__ == "__main__":
    main()
