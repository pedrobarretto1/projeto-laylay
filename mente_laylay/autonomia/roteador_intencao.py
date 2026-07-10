"""Roteador principal de intencoes da Laylay."""

from __future__ import annotations

import random
import re
import os
import time
import urllib.parse
from typing import Any, Dict
from mente_laylay.personalidade.falas_variadas import escolher as _escolher_fala_variada
from mente_laylay.personalidade.falas_variadas import fala_de_confirmacao as _fala_de_confirmacao_variada
from mente_laylay.personalidade.falas_variadas import fala_por_estado_acao as _fala_por_estado_acao
from mente_laylay.autonomia.habilidade_janelas import executar_habilidade_janelas as _executar_habilidade_janelas
from mente_laylay.autonomia.controle_midia import executar_media_control as _executar_media_control
from mente_laylay.arquivos.execucao_arquivos import executar_intencao_arquivos as _executar_intencao_arquivos


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


def bloquear_por_emocao(intent: str, texto_original: str, ctx: Dict[str, Any]) -> bool:
    current_emotion = _get(ctx, "current_emotion", "")
    emotion_level = _get(ctx, "emotion_level", 1)
    falar = _get(ctx, "falar_com_lipsync")
    normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
    try:
        nivel = int(emotion_level or 1)
    except Exception:
        nivel = 1
    if str(current_emotion or "").strip().lower() != "brava" or nivel < 3:
        return False
    intent = str(intent or "").upper().strip()
    if intent in {"MUSIC_SEARCH", "PLAYLIST_PLAY"} and callable(falar):
        fala = "Agora não. Tô brava e não tô a fim de mexer nisso."
        if callable(normalizar) and "por favor" in normalizar(texto_original):
            fala = "Nem assim. Depois eu vejo isso."
        falar(fala, "brava", max(3, nivel))
        return True
    return False


def executar_intencao(resultado: dict, texto_original: str, ctx: Dict[str, Any]) -> bool:
    if not isinstance(resultado, dict):
        return False

    ultima_playlist = _get(ctx, "ultima_playlist")
    destino = _get(ctx, "_target_from_params", lambda p, t="": "pc_a")
    registrar_mente_curta = _get(ctx, "_registrar_mente_curta")
    registrar_resultado_execucao = _get(ctx, "_registrar_resultado_execucao")
    bloqueio = _get(ctx, "_bloqueio_por_emocao")
    falar = _get(ctx, "falar_com_lipsync")
    enviar_pc_b = _get(ctx, "_enviar_pc_b")
    abrir_url = _get(ctx, "abrir_url_com_reciclagem")
    abrir_programa = _get(ctx, "abrir_programa")
    fechar_programa = _get(ctx, "fechar_programa")
    enviar_chrome = _get(ctx, "enviar_comando_chrome")
    resolver_caminho = _get(ctx, "resolver_caminho")
    registrar_contexto_arquivo = _get(ctx, "registrar_contexto_arquivo")
    ultima_pasta_contextual = _get(ctx, "ultima_pasta_contextual")
    ultimo_arquivo_contextual = _get(ctx, "ultimo_arquivo_contextual")
    estrutura_arquivo_recente = _get(ctx, "estrutura_arquivo_recente")
    ajustar_volume = _get(ctx, "ajustar_volume_sistema")
    ajustar_volume_rel = _get(ctx, "ajustar_volume_sistema_relativo")
    solicitar_aba = _get(ctx, "solicitar_aba_ativa")
    fechar_aba_nativa = _get(ctx, "fechar_aba_ativa_nativa")
    organizar = _get(ctx, "organizar_janelas_robusto")
    ativar_full = _get(ctx, "ativar_tela_cheia_robusta")
    focar_app = _get(ctx, "focar_janela_app")
    gmail_resumo = _get(ctx, "_gmail_falar_resumo_estiloso")
    gmail_buscar = _get(ctx, "_gmail_buscar_nao_lidos")
    repetir_briefing = _get(ctx, "repetir_briefing")
    obter_clima_localidade = _get(ctx, "obter_clima_localidade")
    cidade_padrao_clima = _get(ctx, "cidade_padrao_clima", "Boituva")
    _agendamentos_load = _get(ctx, "_agendamentos_load")
    _agendamentos_save = _get(ctx, "_agendamentos_save")
    _fala_agendamentos_estilosa = _get(ctx, "_fala_agendamentos_estilosa")
    _normalizar_query_musical = _get(ctx, "_normalizar_query_musical")
    _buscar_primeiro_video_youtube = _get(ctx, "_buscar_primeiro_video_youtube")
    _playlist_nome_explicito_na_frase = _get(ctx, "_playlist_nome_explicito_na_frase")
    _playlist_shuffle_start = _get(ctx, "_playlist_shuffle_start")
    _playlist_primeira_url = _get(ctx, "_playlist_primeira_url")
    _playlist_item_at = _get(ctx, "_playlist_item_at")
    _playlist_len = _get(ctx, "playlist_len")
    _playlist_sugestao_pendente = _get(ctx, "_playlist_sugestao_pendente")
    play_playlist = _get(ctx, "play_playlist")
    add_to_playlist = _get(ctx, "ADD_TO_PLAYLIST")
    list_playlist_content = _get(ctx, "LIST_PLAYLIST_CONTENT")
    fala_playlist_conteudo_estilosa = _get(ctx, "_fala_playlist_conteudo_estilosa")
    pedido_lista_geral = _get(ctx, "_pedido_lista_geral_playlist")
    listar_playlists_salvas = _get(ctx, "_listar_playlists_salvas")
    listar_playlists_da_laylay = _get(ctx, "_listar_playlists_da_laylay")
    copiar_faixa_da_playlist_laylay = _get(ctx, "_copiar_faixa_da_playlist_laylay")
    extrair_nome_playlist = _get(ctx, "extrair_nome_playlist")
    resolver_query_musical_por_estilo = _get(ctx, "_resolver_query_musical_por_estilo")
    _contexto_aponta_site_web = _get(ctx, "_contexto_aponta_site_web")
    _eh_alvo_site_web = _get(ctx, "_eh_alvo_site_web")
    _normalizar_texto_com_apelidos = _get(ctx, "_normalizar_texto_com_apelidos")
    _montar_url_site_ou_busca = _get(ctx, "_montar_url_site_ou_busca")
    _executar_fechar_abas_paradas = _get(ctx, "_executar_fechar_abas_paradas")
    _executar_captura_tela_intent = _get(ctx, "_executar_captura_tela_intent")
    _bloquear_playlist_temporariamente = _get(ctx, "_bloquear_playlist_temporariamente")
    _autonomia_permite_execucao_musical = _get(ctx, "_autonomia_permite_execucao_musical")
    _playlist_nome_explicito_na_frase = _get(ctx, "_playlist_nome_explicito_na_frase")
    resolver_alvo_ambiente = _get(ctx, "_resolver_alvo_ambiente")
    __registrar_autoaprimoramento = _get(ctx, "_registrar_autoaprimoramento")
    _resumo_agendamentos_para_prompt = _get(ctx, "_resumo_agendamentos_para_prompt")
    _extrair_agendamento_local = _get(ctx, "_extrair_agendamento_local")
    messages = _get(ctx, "messages")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    _enviar_pc_b = _get(ctx, "_enviar_pc_b")
    open_app = _get(ctx, "open_app")
    APPS_MAP = _get(ctx, "APPS_MAP", {})
    SITES_DIRECTOS = _get(ctx, "SITES_DIRECTOS", {})
    APP_OPENER_AVAILABLE = _get(ctx, "APP_OPENER_AVAILABLE", False)
    _contexto_aponta_descanso = _get(ctx, "_contexto_aponta_descanso")
    executar_controle_midia_nativo = _get(ctx, "_executar_controle_midia_nativo")
    validar_e_enviar_comando = _get(ctx, "validar_e_enviar_comando")
    _remover_prefixo_exec = _get(ctx, "_remover_prefixo_exec")
    limpar_resposta = _get(ctx, "limpar_resposta")
    enviar_mensagem = _get(ctx, "enviar_mensagem")
    _resumo_mente_integrada_para_prompt = _get(ctx, "_resumo_mente_integrada_para_prompt")
    _texto_indica_autocorrecao = _get(ctx, "_texto_indica_autocorrecao")
    _registrar_autocorrecao_virtual = _get(ctx, "_registrar_autocorrecao_virtual")
    _atualizar_memoria_topicos = _get(ctx, "_atualizar_memoria_topicos")
    _usar_modo_rapido_conversa = _get(ctx, "_usar_modo_rapido_conversa")
    interpretar_comando_local_rapido = _get(ctx, "interpretar_comando_local_rapido")
    _detectar_repetir_briefing = _get(ctx, "_detectar_repetir_briefing")

    def _reg(*args, **kwargs):
        if callable(registrar_mente_curta):
            return registrar_mente_curta(*args, **kwargs)
        return None

    def _marcar_resultado(status: str, executou: bool | None = None):
        if callable(registrar_resultado_execucao):
            try:
                status_norm = str(status or "").strip().lower()
                if executou is None:
                    executou = status_norm not in {
                        "falha_execucao",
                        "nao_encontrado",
                        "app_aberto_sem_foco",
                        "alvo_ausente",
                        "notificacoes_sem_suporte",
                    }
                registrar_resultado_execucao(
                    resultado,
                    texto_original,
                    bool(executou),
                    origem="executor",
                    status=status,
                )
            except Exception:
                pass

    def _registrar_arquivo(alvo: str, tipo: str = "arquivos") -> None:
        if callable(registrar_contexto_arquivo):
            try:
                registrar_contexto_arquivo(alvo, tipo)
            except Exception:
                pass

    def _falar_por_status(status: str, fallback: str, *, alvo: str = ""):
        if callable(falar):
            status_calmo = {
                "emails_lidos",
                "emails_sincronizados",
                "clima_consultado",
                "volume_ajustado",
                "volume_aumentado",
                "volume_baixado",
                "volume_mudo",
            }
            falar(
                _fala_por_estado_acao(
                    status,
                    fallback=fallback,
                    alvo=alvo,
                    contexto=_ctx_fala(),
                    texto_usuario=texto_original,
                ),
                "debochada" if status not in status_calmo else "calma",
                2 if status not in status_calmo else 1,
            )

    def _resolver_estado_alvo(nome: str) -> dict:
        if not nome or not callable(resolver_alvo_ambiente):
            return {}
        try:
            return resolver_alvo_ambiente(nome) or {}
        except Exception:
            return {}

    def _esperar_programa_fechar(nome: str, tentativas: int = 5, intervalo: float = 0.2) -> bool:
        if not nome:
            return False
        for _ in range(max(1, tentativas)):
            leitura = _resolver_estado_alvo(nome)
            if not bool((leitura or {}).get("programa_aberto")):
                return True
            try:
                time.sleep(intervalo)
            except Exception:
                pass
        leitura_final = _resolver_estado_alvo(nome)
        return not bool((leitura_final or {}).get("programa_aberto"))

    def _esperar_aba_fechar(alvo: str, aba_antes: dict | None = None, tentativas: int = 5, intervalo: float = 0.2) -> bool:
        alvo_limpo = str(alvo or "").strip()
        aba_antes = aba_antes if isinstance(aba_antes, dict) else {}
        for _ in range(max(1, tentativas)):
            if alvo_limpo:
                leitura = _resolver_estado_alvo(alvo_limpo)
                if not bool((leitura or {}).get("aba_aberta")):
                    return True
            elif callable(solicitar_aba):
                try:
                    aba_depois = solicitar_aba() or {}
                except Exception:
                    aba_depois = {}
                url_antes = str(aba_antes.get("url") or "").strip().lower()
                titulo_antes = str(aba_antes.get("title") or "").strip().lower()
                url_depois = str(aba_depois.get("url") or "").strip().lower()
                titulo_depois = str(aba_depois.get("title") or "").strip().lower()
                if (url_antes and url_antes != url_depois) or (titulo_antes and titulo_antes != titulo_depois):
                    return True
            try:
                time.sleep(intervalo)
            except Exception:
                pass
        if alvo_limpo:
            leitura_final = _resolver_estado_alvo(alvo_limpo)
            return not bool((leitura_final or {}).get("aba_aberta"))
        return False

    def _host_para_alvo_web(valor: str) -> str:
        try:
            bruto = str(valor or "").strip()
            if not bruto:
                return ""
            parsed = urllib.parse.urlparse(bruto)
            host = str(parsed.netloc or "").strip().lower()
            if host.startswith("www."):
                host = host[4:]
            return host
        except Exception:
            return ""

    def _alvo_preciso_para_aba(alvo: str) -> str:
        alvo_limpo = str(alvo or "").strip()
        if not alvo_limpo:
            return ""
        url_ref = _montar_url_site_ou_busca(alvo_limpo) if callable(_montar_url_site_ou_busca) else alvo_limpo
        host_ref = _host_para_alvo_web(url_ref)
        if host_ref:
            return host_ref
        return alvo_limpo

    def _aba_corresponde_url(alvo: str, url_esperada: str, aba: dict | None) -> bool:
        aba = aba if isinstance(aba, dict) else {}
        url_atual = str(aba.get("url") or "").strip().lower()
        titulo_atual = str(aba.get("title") or aba.get("titulo") or "").strip().lower()
        alvo_ref = str(alvo or "").strip().lower()
        url_ref = str(url_esperada or "").strip().lower()
        host_ref = _host_para_alvo_web(url_ref) or _host_para_alvo_web(alvo_ref)
        if url_ref and url_atual.startswith(url_ref):
            return True
        if host_ref and (host_ref in url_atual or host_ref in titulo_atual):
            return True
        if alvo_ref and (alvo_ref in url_atual or alvo_ref in titulo_atual):
            return True
        return False

    def _esperar_url_abrir(url: str, *, alvo: str = "", tentativas: int = 8, intervalo: float = 0.25) -> bool:
        url_limpa = str(url or "").strip()
        alvo_ref = _alvo_preciso_para_aba(alvo or url_limpa)
        for _ in range(max(1, tentativas)):
            if alvo_ref:
                leitura = _resolver_estado_alvo(alvo_ref)
                if bool((leitura or {}).get("aba_aberta")):
                    return True
            if callable(solicitar_aba):
                try:
                    aba_atual = solicitar_aba() or {}
                except Exception:
                    aba_atual = {}
                if _aba_corresponde_url(alvo_ref, url_limpa, aba_atual):
                    return True
            try:
                time.sleep(intervalo)
            except Exception:
                pass
        return False

    def _resolver_caminho_local(valor: str) -> str:
        bruto = str(valor or "").strip()
        if not bruto:
            return ""
        if callable(resolver_caminho):
            try:
                return str(resolver_caminho(bruto) or "").strip()
            except Exception:
                return bruto
        return bruto

    def _item_local_existe(valor: str, tipo: str = "") -> bool:
        caminho = _resolver_caminho_local(valor)
        if not caminho:
            return False
        try:
            if "arquivo" in str(tipo or "").lower():
                return os.path.isfile(caminho)
            if "pasta" in str(tipo or "").lower():
                return os.path.isdir(caminho)
            return os.path.exists(caminho)
        except Exception:
            return False

    def _resolver_referencia_arquivo_contextual(alvo_ref: str, tipo_ref: str = "") -> str:
        ref = str(alvo_ref or "").strip()
        ref_norm = ref.lower()
        tipo_norm = str(tipo_ref or "").strip().lower()
        if ref_norm not in {"ela", "ele", "isso", "essa", "esse", "essa pasta", "esse arquivo"}:
            return ref
        ultima_pasta = str(ultima_pasta_contextual() or "").strip() if callable(ultima_pasta_contextual) else ""
        ultimo_arquivo = str(ultimo_arquivo_contextual() or "").strip() if callable(ultimo_arquivo_contextual) else ""
        estrutura = {}
        if callable(estrutura_arquivo_recente):
            try:
                estrutura = estrutura_arquivo_recente() or {}
            except Exception:
                estrutura = {}
        if not isinstance(estrutura, dict):
            estrutura = {}
        estrutura_pasta = str(
            estrutura.get("nome")
            or estrutura.get("pasta")
            or estrutura.get("alvo")
            or ""
        ).strip()
        estrutura_arquivo = str(
            estrutura.get("arquivo_nome")
            or estrutura.get("nome_arquivo")
            or estrutura.get("arquivo")
            or ""
        ).strip()
        if estrutura_arquivo and "." not in estrutura_arquivo:
            estrutura_arquivo = f"{estrutura_arquivo}.txt"
        ultimo_alvo_mental = str(_get(ctx, "ultimo_alvo", "") or "").strip()
        alvo_mental_existe = bool(ultimo_alvo_mental and _item_local_existe(ultimo_alvo_mental))
        if "pasta" in tipo_norm or ref_norm in {"ela", "essa", "essa pasta", "isso"}:
            return ultima_pasta or estrutura_pasta or (ultimo_alvo_mental if alvo_mental_existe else "") or ultimo_arquivo or estrutura_arquivo or ref
        if "arquivo" in tipo_norm or ref_norm in {"ele", "esse", "esse arquivo"}:
            return ultimo_arquivo or estrutura_arquivo or (ultimo_alvo_mental if alvo_mental_existe else "") or ultima_pasta or estrutura_pasta or ref
        if ultimo_alvo_mental and _item_local_existe(ultimo_alvo_mental):
            return ultimo_alvo_mental
        foco_vivo = _get(ctx, "foco_vivo", {}) or {}
        alvo_foco = str((foco_vivo or {}).get("alvo") or "").strip()
        if alvo_foco and _item_local_existe(alvo_foco):
            return alvo_foco
        if ultimo_arquivo and _item_local_existe(ultimo_arquivo, "arquivo"):
            return ultimo_arquivo
        if ultima_pasta and _item_local_existe(ultima_pasta, "pasta"):
            return ultima_pasta
        return ultima_pasta or estrutura_pasta or ultimo_arquivo or estrutura_arquivo or ref

    def _abrir_url_com_validacao(url: str, *, alvo: str = "", auto_click: bool = False) -> bool:
        url_limpa = str(url or "").strip()
        if not url_limpa:
            return False
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "open_url", "url": url_limpa})
            return True
        if callable(abrir_url):
            try:
                retorno = abrir_url(url_limpa, auto_click=auto_click)
                if retorno is False:
                    return False
                return _esperar_url_abrir(url_limpa, alvo=alvo or url_limpa)
            except Exception:
                return False
        return False

    def _falar_resultado_janela(nome: str, status_janela: str) -> None:
        fallback_map = {
            "ja_aberto_focado": f"{nome} já estava aberto e em foco.",
            "app_focado": f"{nome} já tava aberto, só puxei pra frente.",
            "app_aberto": f"Abrindo {nome}.",
            "app_aberto_sem_foco": f"{nome} abriu, mas não consegui puxar ele pro foco agora.",
            "site_aberto": f"Abrindo {nome} no navegador.",
            "protocolo_aberto": f"Abrindo {nome} pelo protocolo do sistema.",
            "nao_encontrado": f"Não achei {nome}.",
            "janela_maximizada": f"{nome.title()} maximizado e em foco.",
            "falha_execucao": f"Tentei mexer em {nome}, mas não rolou de verdade.",
        }
        _falar_por_status(status_janela, fallback_map.get(status_janela, f"Tentei mexer em {nome}, mas não rolou de verdade."), alvo=nome)

    def _abrir_url_musical(url: str, *, query: str = "") -> bool:
        url_limpa = str(url or "").strip()
        if not url_limpa:
            return False
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "open_url", "url": url_limpa})
            return True
        if destino_val == "ambos":
            ok_local = False
            if query and callable(enviar_chrome):
                enviar_chrome("youtube_search", {"query": query})
                ok_local = True
            elif callable(abrir_url):
                try:
                    retorno = abrir_url(url_limpa, auto_click=False)
                    ok_local = False if retorno is False else True
                except Exception:
                    ok_local = False
            if callable(_enviar_pc_b):
                _enviar_pc_b({"action": "open_url", "url": url_limpa})
            return ok_local
        if query and callable(enviar_chrome):
            enviar_chrome("youtube_search", {"query": query})
            return True
        if callable(abrir_url):
            try:
                retorno = abrir_url(url_limpa, auto_click=False)
                return False if retorno is False else True
            except Exception:
                return False
        return False

    def _sugerir_criacao_playlist(pl: str) -> None:
        if callable(ctx.get("set_playlist_sugestao_pendente")):
            ctx["set_playlist_sugestao_pendente"]({"playlist": pl, "ts": time.time()})
        if callable(falar):
            falar(_escolher_fala_variada([
                f"Você ainda não criou a playlist {pl}. Quer que eu salve essa música nela?",
                f"{pl} ainda não existe. Quer que eu salve essa música lá?",
                f"Não achei a playlist {pl}. Posso guardar essa música nela?",
            ]), "calma", 1)

    def _ctx_fala() -> dict:
        return {
            "current_emotion": current_emotion,
            "ultima_habilidade": _get(ctx, "ultima_habilidade", ""),
            "ultimo_alvo": _get(ctx, "ultimo_alvo", ""),
        }

    intent = str(resultado.get("intent") or "").upper().strip()
    raw_params = resultado.get("params")
    params = raw_params if isinstance(raw_params, dict) else {}
    destino_val = destino(params, texto_original) if callable(destino) else "pc_a"
    alvo_mental = str(
        params.get("nome_playlist")
        or params.get("nome_app")
        or params.get("query")
        or params.get("url")
        or params.get("alvo")
        or params.get("tema")
        or ""
    ).strip()
    habilidade = ""
    if intent in {"PLAYLIST_ADD", "PLAYLIST_PLAY", "PLAYLIST_LIST", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE"}:
        habilidade = "playlist"
    elif intent in {"LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_COPY"}:
        habilidade = "playlist_laylay"
    elif intent in {"APP_OPEN", "OPEN_URL"}:
        habilidade = "navegacao"
    elif intent in {"MUSIC_SEARCH", "MEDIA_CONTROL"}:
        habilidade = "midia"
    elif intent in {"VOLUME"}:
        habilidade = "audio"
    elif intent in {"CLOSE_TAB", "CLOSE_IDLE_TABS"}:
        habilidade = "navegador"
    elif intent in {"SEARCH", "SITE_ENTER"}:
        habilidade = "pesquisa"
    elif intent in {"WEATHER"}:
        habilidade = "clima"
    _reg(texto_original, "", intent, alvo_mental, destino_val, habilidade)

    if callable(bloqueio) and bloqueio(intent, texto_original, ctx):
        return True

    if intent == "STOP_PLAYLIST_CONTEXT":
        if callable(_bloquear_playlist_temporariamente):
            _bloquear_playlist_temporariamente()
        _marcar_resultado("playlist_contexto_bloqueado")
        if callable(falar):
            falar(_escolher_fala_variada([
                "Fechado, sem playlist agora. Guardei a caixinha de som.",
                "Tá, corto playlist por enquanto. Ela fica quietinha no canto.",
                "Entendi. Nada de playlist agora, pode falar comigo normal.",
            ]), "calma", 1)
        return True

    if intent == "CANCELAR_ACAO":
        if callable(_bloquear_playlist_temporariamente):
            _bloquear_playlist_temporariamente(0.0)
        try:
            if isinstance(ctx, dict):
                ctx["_playlist_sugestao_pendente"] = None
                ctx["_rotina_sugestao_pendente"] = None
                ctx["comando_sugerido"] = None
                ctx["comando_sugerido_payload"] = None
                ctx["comando_sugerido_estado"] = "NONE"
                ctx["comando_sugerido_ts"] = 0.0
                ctx["comando_pendente"] = None
                ctx["comando_pendente_payload"] = None
        except Exception:
            pass
        if callable(falar):
            falar(_escolher_fala_variada([
                "Beleza, cancelei isso.",
                "Certo, deixei pra lá.",
                "Tá, descartei a ação anterior.",
            ]), "calma", 1)
        _marcar_resultado("cancelado")
        return True

    if intent == "ORGANIZAR_DESKTOP":
        app_esquerda = str(params.get("left") or params.get("esquerda") or "vscode").strip()
        app_direita = str(params.get("right") or params.get("direita") or "opera").strip()
        try:
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "organizar_desktop", "left": app_esquerda, "right": app_direita})
                if callable(falar):
                    falar(_escolher_fala_variada([
                        "Organizando a bagunça no PC B...",
                        "PC B em ordem. Vou ajeitar isso.",
                        "Deixando o PC B mais limpo agora.",
                    ]), "debochada", 2)
                return True
            if callable(organizar):
                organizar(app_esquerda, app_direita)
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Área de trabalho organizada, Pedro. VS Code à esquerda, navegador à direita. Tá limpo agora.",
                    "Pronto. Arrumei a área e deixei tudo no lugar.",
                    "Organizei a mesa do sistema. Ficou respirável agora.",
                ]), "debochada", 2)
        except Exception:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Tentei organizar a área, mas o Windows resolveu fazer drama.",
                    "A organização emperrou no humor do Windows.",
                    "Quase arrumei tudo, mas o sistema fez cena.",
                ]), "irritada", 2)
        return True

    if intent == "OPEN_URL":
        alvo = str(params.get("url") or params.get("alvo") or params.get("site") or params.get("query") or "").strip()
        if callable(_contexto_aponta_site_web) and _contexto_aponta_site_web(alvo):
            alvo = _normalizar_texto_com_apelidos(alvo) if callable(_normalizar_texto_com_apelidos) else alvo
        url = _montar_url_site_ou_busca(alvo) if callable(_montar_url_site_ou_busca) else alvo
        if not url:
            if callable(falar):
                falar(_escolher_fala_variada(["Abrir o quê, Pedro? Me dá um site ou assunto.", "Me diz o que você quer abrir.", "Faltou o site ou o assunto."]), "debochada", 2)
            return True
        ok_abertura = _abrir_url_com_validacao(url, alvo=alvo or url, auto_click=False)
        _marcar_resultado("url_aberta" if ok_abertura else "falha_execucao", executou=ok_abertura)
        _falar_por_status(
            "url_aberta" if ok_abertura else "falha_execucao",
            f"Abrindo {alvo or url}." if ok_abertura else f"Tentei abrir {alvo or url}, mas não consegui confirmar a rota.",
            alvo=alvo or url,
        )
        return True

    if intent == "CLOSE_IDLE_TABS":
        return bool(_executar_fechar_abas_paradas()) if callable(_executar_fechar_abas_paradas) else False

    if intent == "SCREEN_CAPTURE":
        return bool(_executar_captura_tela_intent(destino_val)) if callable(_executar_captura_tela_intent) else False

    if intent == "MAXIMIZE_WINDOW":
        app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "maximize_window", "app": app})
            _marcar_resultado("janela_maximizada_pc_b", executou=True)
            _falar_por_status("janela_maximizada_pc_b", f"Maximizando {app or 'a janela'} no PC B.", alvo=app or "a janela")
            return True
        resultado_janela = _executar_habilidade_janelas(intent, params, ctx)
        if isinstance(resultado_janela, dict) and resultado_janela.get("handled"):
            app = str(resultado_janela.get("nome_app") or params.get("nome_app") or "").strip()
            status_janela = str(resultado_janela.get("status") or "falha_execucao").strip().lower()
            if status_janela == "alvo_ausente":
                if callable(falar):
                    falar(_escolher_fala_variada(["Qual janela você quer maximizar, Pedro?", "Me fala qual janela eu devo trazer pra frente.", "Faltou dizer a janela."]), "calma", 1)
                return True
            _marcar_resultado(status_janela, executou=bool(resultado_janela.get("ok")))
            _falar_resultado_janela(app, status_janela)
            return True
        if not app:
            if callable(falar):
                falar(_escolher_fala_variada(["Qual janela você quer maximizar, Pedro?", "Me fala qual janela eu devo trazer pra frente.", "Faltou dizer a janela."]), "calma", 1)
            return True
        _marcar_resultado("falha_execucao", executou=False)
        _falar_por_status("falha_execucao", f"Tentei maximizar {app}, mas não rolou de verdade.", alvo=app)
        return True

    if intent == "CLOSE_APP":
        nome_app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
        if not nome_app:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Fechar o quê, Pedro? Me fala o nome do programa direito.",
                    "Qual programa eu fecho?",
                    "Faltou o nome do app.",
                ]), "debochada", 2)
            return True
        leitura_alvo = resolver_alvo_ambiente(nome_app) if callable(resolver_alvo_ambiente) else {}
        programa_aberto = bool((leitura_alvo or {}).get("programa_aberto"))
        if bool((leitura_alvo or {}).get("aba_aberta")) and not bool((leitura_alvo or {}).get("programa_aberto")):
            alvo_tab = _alvo_preciso_para_aba(nome_app)
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "close_specific_tab", "target": alvo_tab})
                ok_aba = True
            elif callable(enviar_chrome):
                enviar_chrome("close_specific_tab", {"target": alvo_tab})
                ok_aba = _esperar_aba_fechar(alvo_tab)
            else:
                ok_aba = False
            _marcar_resultado("aba_fechada_em_vez_de_app" if ok_aba else "falha_execucao", executou=ok_aba)
            _falar_por_status(
                "aba_fechada_em_vez_de_app" if ok_aba else "falha_execucao",
                f"{nome_app} não estava aberto como programa. Fechei a aba." if ok_aba else f"Tentei fechar a aba de {nome_app}, mas ela resistiu.",
                alvo=nome_app,
            )
            return True
        if (not programa_aberto) and callable(_eh_alvo_site_web) and callable(_contexto_aponta_site_web) and (_eh_alvo_site_web(nome_app) or _contexto_aponta_site_web(nome_app)):
            alvo_tab = _alvo_preciso_para_aba(nome_app)
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "close_specific_tab", "target": alvo_tab})
                ok_aba = True
            elif callable(enviar_chrome):
                enviar_chrome("close_specific_tab", {"target": alvo_tab})
                ok_aba = _esperar_aba_fechar(alvo_tab)
            else:
                ok_aba = False
            _marcar_resultado("aba_fechada" if ok_aba else "falha_execucao", executou=ok_aba)
            _falar_por_status(
                "aba_fechada" if ok_aba else "falha_execucao",
                f"Fechei a aba do {nome_app}." if ok_aba else f"Tentei fechar a aba do {nome_app}, mas não consegui confirmar.",
                alvo=nome_app,
            )
            return True
        mapped = APPS_MAP.get(nome_app.lower(), nome_app)
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "close_app", "app": mapped})
            _marcar_resultado("app_fechado_pc_b", executou=True)
            _falar_por_status("app_fechado_pc_b", f"Fechando {nome_app} no PC B.", alvo=nome_app)
        elif callable(fechar_programa):
            try:
                fechar_programa(mapped)
            except Exception:
                pass
            ok_fechamento = _esperar_programa_fechar(nome_app)
            _marcar_resultado("app_fechado" if ok_fechamento else "falha_execucao", executou=ok_fechamento)
            _falar_por_status(
                "app_fechado" if ok_fechamento else "falha_execucao",
                f"Pronto, {nome_app} foi fechado." if ok_fechamento else f"Tentei fechar {nome_app}, mas ele continuou por aí.",
                alvo=nome_app,
            )
        return True

    if intent == "EMAIL_READ":
        somente = bool(params.get("urgentes") or params.get("prioritarios"))
        remetente_filtro = str(
            params.get("remetente")
            or params.get("alvo")
            or params.get("query")
            or ""
        ).strip().lower()
        emails_c = _get(ctx, "_gmail_nao_lidos_cache", []) or (gmail_buscar() if callable(gmail_buscar) else [])
        if somente:
            emails_c = [e for e in emails_c if e.get("prioritario")]
        if remetente_filtro:
            filtrados = []
            for e in emails_c if isinstance(emails_c, list) else []:
                rem = str((e or {}).get("remetente") or "").strip().lower()
                if rem and (remetente_filtro == rem or remetente_filtro in rem or rem in remetente_filtro):
                    filtrados.append(e)
            emails_c = filtrados or emails_c
        if callable(gmail_resumo):
            gmail_resumo(emails_c, somente_prioritarios=somente)
        _marcar_resultado("emails_lidos")
        return True

    if intent == "EMAIL_SYNC":
        ok_sync = False
        if callable(gmail_buscar):
            try:
                emails_sync = gmail_buscar()
                ok_sync = isinstance(emails_sync, list)
            except Exception:
                ok_sync = False
        _marcar_resultado("emails_sincronizados" if ok_sync else "falha_execucao", executou=ok_sync)
        _falar_por_status(
            "emails_sincronizados" if ok_sync else "falha_execucao",
            "Atualizando a caixa de entrada." if ok_sync else "Tentei atualizar teus emails, mas a caixa não respondeu direito.",
            alvo="emails",
        )
        return True

    if intent == "BRIEFING_REPEAT":
        if callable(repetir_briefing):
            repetir_briefing()
        _marcar_resultado("briefing_repetido")
        return True

    if intent == "WEATHER":
        local = str(
            params.get("local")
            or params.get("cidade")
            or params.get("bairro")
            or params.get("query")
            or cidade_padrao_clima
        ).strip()
        info = obter_clima_localidade(local) if callable(obter_clima_localidade) else {"ok": False, "localidade": local}
        if not info.get("ok"):
            if callable(falar):
                falar(
                    _escolher_fala_variada([
                        f"Tentei sentir o clima de {local}, mas minha antena do tempo falhou agora.",
                        f"Fui olhar o tempo em {local}, mas não consegui puxar essa informação agora.",
                        f"O clima de {local} escapou de mim por enquanto. Se quiser, tenta de novo em instantes.",
                    ]),
                    "calma",
                    1,
                )
            return True
        cidade = str(info.get("localidade") or local).strip()
        temp = str(info.get("temperatura_c") or "").strip()
        sens = str(info.get("sensacao_c") or "").strip()
        desc = str(info.get("descricao") or "").strip()
        umidade = str(info.get("umidade") or "").strip()
        base = f"Agora em {cidade} está {temp} graus"
        if desc:
            base += f", com {desc}"
        if sens:
            base += f". Sensação de {sens} graus"
        if umidade:
            base += f" e umidade em {umidade}%"
        base += "."
        if callable(falar):
            falar(
                _escolher_fala_variada([
                    base,
                    f"Dei uma espiada no tempo: {base}",
                    f"Clima na mesa. {base}",
                ]),
                "calma",
                1,
            )
        _marcar_resultado("clima_consultado")
        return True

    if intent == "NOTIFICATIONS":
        acao_not = str(params.get("acao") or "ler").strip().lower()
        alvo_not = str(params.get("alvo") or params.get("remetente") or params.get("query") or "").strip()
        if callable(falar):
            if acao_not in {"silenciar_remetente", "silenciar_email", "silenciar_remetente_email"}:
                silenciar_fn = _get(ctx, "_gmail_silenciar_remetente")
                if alvo_not and callable(silenciar_fn):
                    try:
                        silenciar_fn(alvo_not)
                    except Exception:
                        pass
                _marcar_resultado("remetente_silenciado")
                _falar_por_status("remetente_silenciado", f"Pronto, silenciei {alvo_not or 'esse remetente'}.", alvo=alvo_not or "esse remetente")
            elif acao_not in {"silenciar", "mute", "desativar"}:
                _marcar_resultado("notificacoes_sem_suporte")
                _falar_por_status("notificacoes_sem_suporte", "Ainda não tenho a alavanca do silêncio total.", alvo="notificacoes")
            elif acao_not in {"ativar", "reativar"}:
                _marcar_resultado("notificacoes_sem_suporte")
                _falar_por_status("notificacoes_sem_suporte", "Notificações ainda são com o Windows, por enquanto.", alvo="notificacoes")
            else:
                _marcar_resultado("notificacoes_sem_suporte")
                _falar_por_status("notificacoes_sem_suporte", "Leitura de notificações ainda depende do Windows.", alvo="notificacoes")
        return True

    if intent == "LOCK_PC":
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "lock_pc"})
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Travando o PC B agora.",
                    "PC B bloqueado.",
                    "Tranquei o PC B.",
                ]), "calma", 1)
            return True
        try:
            import ctypes
            ctypes.windll.user32.LockWorkStation()
        except Exception:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Não consegui travar o Windows agora.",
                    "Ainda não deu pra bloquear o Windows.",
                    "O bloqueio do Windows não quis colaborar.",
                ]), "calma", 1)
            return True
        if callable(falar):
            falar(_escolher_fala_variada(["PC bloqueado.", "Pronto, bloqueado.", "Tela travada."]), "calma", 1)
        return True

    if intent in {"CREATE_FOLDER", "DELETE_ITEM"}:
        return _executar_intencao_arquivos(
            intent,
            params,
            destino_val,
            ctx,
            marcar_resultado=_marcar_resultado,
            registrar_arquivo=_registrar_arquivo,
            item_local_existe=_item_local_existe,
            resolver_caminho_local=_resolver_caminho_local,
            resolver_referencia_arquivo_contextual=_resolver_referencia_arquivo_contextual,
        )

    if intent == "CLOSE_TAB":
        info = solicitar_aba() if callable(solicitar_aba) else {}
        url = str(info.get("url") or "").lower() if isinstance(info, dict) else ""
        alvo_tab = str(params.get("alvo") or params.get("site") or params.get("nome") or "").strip()
        alvo_tab_preciso = _alvo_preciso_para_aba(alvo_tab) if alvo_tab else ""
        leitura_alvo = resolver_alvo_ambiente(alvo_tab) if alvo_tab and callable(resolver_alvo_ambiente) else {}
        alvo_web = bool(callable(_eh_alvo_site_web) and _eh_alvo_site_web(alvo_tab))
        if alvo_tab and not alvo_web and bool((leitura_alvo or {}).get("programa_aberto")) and callable(fechar_programa):
            mapped = APPS_MAP.get(alvo_tab.lower(), alvo_tab)
            try:
                fechar_programa(mapped)
            except Exception:
                pass
            ok_fechamento = _esperar_programa_fechar(alvo_tab)
            _marcar_resultado("app_fechado_em_vez_de_aba" if ok_fechamento else "falha_execucao", executou=ok_fechamento)
            _falar_por_status(
                "app_fechado_em_vez_de_aba" if ok_fechamento else "falha_execucao",
                f"{alvo_tab} estava aberto como programa. Fechei ele, não a aba." if ok_fechamento else f"Tentei fechar {alvo_tab} como programa, mas ele resistiu.",
                alvo=alvo_tab,
            )
            return True
        if not alvo_tab and callable(_contexto_aponta_site_web) and _contexto_aponta_site_web(texto_original):
            alvo_tab = str(params.get("nome_app") or params.get("query") or params.get("alvo") or "site").strip()
        ok_aba = False
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            payload = {"action": "close_specific_tab", "target": alvo_tab_preciso or alvo_tab} if alvo_tab else {"action": "close_current_tab"}
            _enviar_pc_b(payload)
            ok_aba = True
        elif alvo_tab and callable(enviar_chrome):
            enviado = bool(enviar_chrome("close_specific_tab", {"target": alvo_tab_preciso or alvo_tab}))
            if enviado:
                ok_aba = _esperar_aba_fechar(alvo_tab_preciso or alvo_tab, info)
            elif callable(fechar_aba_nativa):
                ok_aba = bool(fechar_aba_nativa(alvo_tab_preciso or alvo_tab))
        elif callable(enviar_chrome):
            enviado = bool(enviar_chrome("close_current_tab", {}))
            if enviado:
                ok_aba = _esperar_aba_fechar("", info)
            elif callable(fechar_aba_nativa):
                ok_aba = bool(fechar_aba_nativa(""))
        _marcar_resultado("aba_fechada" if ok_aba else "falha_execucao", executou=ok_aba)
        _falar_por_status(
            "aba_fechada" if ok_aba else "falha_execucao",
            "Fechado. Já vai tarde." if ok_aba else f"Tentei fechar {alvo_tab or 'essa aba'}, mas não consegui confirmar se ela saiu de cena.",
            alvo=alvo_tab or "essa aba",
        )
        return True

    if intent == "SITE_ENTER":
        tema = str(params.get("tema") or params.get("topic") or params.get("assunto") or params.get("query") or "").strip() or str(texto_original or "").strip()
        if not tema:
            if callable(falar):
                falar(_escolher_fala_variada(["Entrar onde, Pedro? Fala o tema do site.", "Qual site você quer?", "Me fala o assunto do site."]), "debochada", 2)
            return True
        url = f"https://www.google.com/search?q={urllib.parse.quote(tema)}&laylay_auto=true"
        ok_busca = _abrir_url_com_validacao(url, alvo=tema, auto_click=True)
        _marcar_resultado("busca_site_iniciada" if ok_busca else "falha_execucao", executou=ok_busca)
        _falar_por_status(
            "busca_site_iniciada" if ok_busca else "falha_execucao",
            f"Vou entrar no melhor site de {tema}." if ok_busca else f"Tentei abrir uma busca de {tema}, mas a rota web falhou.",
            alvo=tema,
        )
        return True

    if intent == "APP_OPEN":
        nome = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
        if not nome:
            if callable(falar):
                falar(_escolher_fala_variada(["Tá, mas abrir o quê? Fala o nome do app direito.", "Me diz qual app eu devo abrir.", "Faltou o nome do aplicativo."]), "debochada", 2)
            return True
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            key = nome.lower().strip()
            mapped = APPS_MAP.get(key, nome)
            url_site = ""
            if isinstance(mapped, str) and mapped.startswith(("http://", "https://")):
                url_site = mapped
            elif isinstance(mapped, str) and re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:$", mapped.strip()):
                url_site = mapped
            elif callable(_eh_alvo_site_web) and callable(_contexto_aponta_site_web) and (_eh_alvo_site_web(nome) or _contexto_aponta_site_web(nome)):
                url_site = SITES_DIRECTOS.get(key) or SITES_DIRECTOS.get(_normalizar_texto_com_apelidos(nome)) or ""
                if not url_site and "instagram" in key:
                    url_site = "https://www.instagram.com"
            if url_site:
                _enviar_pc_b({"action": "open_url", "url": url_site})
                _marcar_resultado("site_aberto", executou=True)
                _falar_por_status("site_aberto", f"Abrindo {nome} no PC B.", alvo=nome)
                return True
            _enviar_pc_b({"action": "open_app", "app": mapped, "quantidade": 1})
            _marcar_resultado("app_aberto_pc_b", executou=True)
            _falar_por_status("app_aberto_pc_b", f"Abrindo {nome} no PC B.", alvo=nome)
            return True
        resultado_janela = _executar_habilidade_janelas(intent, params, ctx)
        if isinstance(resultado_janela, dict) and resultado_janela.get("handled"):
            nome = str(resultado_janela.get("nome_app") or params.get("nome_app") or "").strip()
            status_janela = str(resultado_janela.get("status") or "falha_execucao").strip().lower()
            if status_janela == "alvo_ausente":
                if callable(falar):
                    falar(_escolher_fala_variada(["Tá, mas abrir o quê? Fala o nome do app direito.", "Me diz qual app eu devo abrir.", "Faltou o nome do aplicativo."]), "debochada", 2)
                return True
            _marcar_resultado(status_janela, executou=bool(resultado_janela.get("ok")))
            _falar_resultado_janela(nome, status_janela)
            return True
        _marcar_resultado("falha_execucao", executou=False)
        _falar_por_status("falha_execucao", f"Tentei abrir {nome}, mas não consegui validar a abertura.", alvo=nome)
        return True

    if intent == "MEDIA_CONTROL":
        return _executar_media_control(
            params,
            texto_original,
            destino_val,
            ctx,
            marcar_resultado=_marcar_resultado,
            falar_por_status=_falar_por_status,
            ctx_fala=_ctx_fala,
        )

    if intent == "MUSIC_SEARCH":
        if callable(_autonomia_permite_execucao_musical) and not _autonomia_permite_execucao_musical(intent, texto_original):
            print("🎵 [AUTONOMIA] MUSIC_SEARCH bloqueado: sem pedido musical explícito.")
            return False
        query = str(params.get("query") or params.get("musica") or params.get("nome") or texto_original).strip()
        query = _normalizar_query_musical(query or texto_original) if callable(_normalizar_query_musical) else query
        if callable(resolver_query_musical_por_estilo):
            try:
                perfil_query = resolver_query_musical_por_estilo(query, texto_original)
                if isinstance(perfil_query, dict) and str(perfil_query.get("query") or "").strip():
                    query = str(perfil_query.get("query") or query).strip()
            except Exception:
                pass
        if not query:
            if callable(falar):
                falar(_escolher_fala_variada(["Tá, mas tocar o quê? Fala a música direito.", "Me diz a música.", "Qual faixa você quer?"]), "debochada", 2)
            return True
        link_direto = _buscar_primeiro_video_youtube(query) if callable(_buscar_primeiro_video_youtube) else ""
        url_final = link_direto if link_direto else ("https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query))
        ok_busca = _abrir_url_musical(url_final, query=query if not link_direto else "")
        _marcar_resultado("musica_aberta" if ok_busca else "falha_execucao", executou=ok_busca)
        if callable(falar):
            falar(
                _escolher_fala_variada([
                    f"Sintonizando o melhor do {query} no YouTube agora, Pedro.",
                    f"Botando {query} pra tocar agora.",
                    f"Já achei {query}.",
                ]) if ok_busca else _escolher_fala_variada([
                    f"Tentei puxar {query}, mas a rota musical falhou agora.",
                    f"Fui atrás de {query}, mas não consegui abrir esse som direito.",
                    f"Quase puxei {query}, mas a trilha não respondeu do jeito certo.",
                ]),
                "calma" if ok_busca else "irritada",
                1 if ok_busca else 2,
            )
        return bool(ok_busca)

    if intent == "LAYLAY_PLAYLIST_LIST":
        nome = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
        if callable(falar):
            falar(
                listar_playlists_da_laylay(nome) if callable(listar_playlists_da_laylay) else "Ainda não montei playlists minhas por aqui.",
                "calma",
                1,
            )
        return True

    if intent == "LAYLAY_PLAYLIST_COPY":
        musica = str(params.get("musica") or params.get("nome") or "").strip()
        origem = str(params.get("origem") or params.get("playlist_origem") or "").strip()
        destino = str(params.get("destino") or params.get("playlist_destino") or "").strip()
        if not musica or not origem or not destino:
            if callable(falar):
                falar(
                    _escolher_fala_variada([
                        "Me fala qual música da minha playlist vai para qual playlist tua.",
                        "Faltou dizer a música, a minha playlist e a tua playlist de destino.",
                        "Preciso da faixa, da minha playlist e da tua playlist pra copiar certinho.",
                    ]),
                    "calma",
                    1,
                )
            return True
        res = copiar_faixa_da_playlist_laylay(origem, musica, destino) if callable(copiar_faixa_da_playlist_laylay) else {"ok": False}
        if bool(res.get("ok")):
            faixa = res.get("faixa") or {}
            titulo = str(faixa.get("titulo") or musica).strip() or musica
            if callable(ctx.get("set_ultima_playlist")):
                ctx["set_ultima_playlist"](destino)
            if callable(falar):
                falar(
                    _escolher_fala_variada([
                        f"Pronto, puxei {titulo} da minha playlist {origem} pra tua playlist {destino}.",
                        f"Beleza, {titulo} saiu da minha curadoria e foi pra {destino}.",
                        f"Já coloquei {titulo} da minha playlist {origem} em {destino}.",
                    ]),
                    "debochada",
                    2,
                )
        else:
            if callable(falar):
                falar(
                    _escolher_fala_variada([
                        f"Não achei essa faixa na minha playlist {origem}.",
                        f"A minha playlist {origem} não me entregou essa música agora.",
                        f"Procurei na minha playlist {origem}, mas essa faixa não apareceu.",
                    ]),
                    "calma",
                    1,
                )
        return True

    if intent == "VOLUME":
        acao = str(params.get("acao") or params.get("modo") or "").strip().lower()
        nivel = params.get("nivel_volume") if "nivel_volume" in params else params.get("value")
        if acao in {"up", "aumentar", "aumenta"}:
            ok_volume = False
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "volume_up", "delta": 10})
                ok_volume = True
            elif callable(ajustar_volume_rel):
                ajustar_volume_rel(10)
                ok_volume = True
            _marcar_resultado("volume_aumentado" if ok_volume else "falha_execucao", executou=ok_volume)
            _falar_por_status(
                "volume_aumentado" if ok_volume else "falha_execucao",
                "Aumentei o volume." if ok_volume else "Tentei aumentar o volume, mas o controle não respondeu.",
                alvo="volume",
            )
            return True
        if acao in {"down", "baixar", "baixa"}:
            ok_volume = False
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "volume_down", "delta": 10})
                ok_volume = True
            elif callable(ajustar_volume_rel):
                ajustar_volume_rel(-10)
                ok_volume = True
            _marcar_resultado("volume_baixado" if ok_volume else "falha_execucao", executou=ok_volume)
            _falar_por_status(
                "volume_baixado" if ok_volume else "falha_execucao",
                "Baixei o volume." if ok_volume else "Tentei baixar o volume, mas o controle não respondeu.",
                alvo="volume",
            )
            return True
        if acao in {"mute", "mudo"}:
            ok_volume = False
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "set_volume", "nivel": 0})
                ok_volume = True
            elif callable(ajustar_volume):
                ajustar_volume(0)
                ok_volume = True
            _marcar_resultado("volume_mudo" if ok_volume else "falha_execucao", executou=ok_volume)
            _falar_por_status(
                "volume_mudo" if ok_volume else "falha_execucao",
                "Mudo ligado." if ok_volume else "Tentei mutar o som, mas o controle não respondeu.",
                alvo="volume",
            )
            return True
        if isinstance(nivel, (int, float, str)):
            try:
                v = float(nivel)
            except Exception:
                v = -1.0
            if v <= 1.0 and v >= 0:
                v = v * 100.0
            if 0.0 <= v <= 100.0:
                ok_volume = False
                if destino_val == "pc_b" and callable(_enviar_pc_b):
                    _enviar_pc_b({"action": "set_volume", "nivel": int(v)})
                    ok_volume = True
                elif callable(ajustar_volume):
                    ajustar_volume(int(v))
                    ok_volume = True
                _marcar_resultado("volume_ajustado" if ok_volume else "falha_execucao", executou=ok_volume)
                _falar_por_status(
                    "volume_ajustado" if ok_volume else "falha_execucao",
                    "Volume ajustado." if ok_volume else "Tentei ajustar o volume, mas o controle não respondeu.",
                    alvo="volume",
                )
                return True
        if callable(falar):
            falar(_escolher_fala_variada(["Volume como, Pedro? No talo, baixinho, mudo...", "Como você quer o volume, Pedro?", "Me diz o nível do som."]), "debochada", 2)
        return True

    if intent == "FECHAR_PROGRAMA":
        nome_app = str(params.get("nome") or params.get("app") or params.get("programa") or params.get("nome_busca") or "").strip()
        if not nome_app:
            if callable(falar):
                falar(_escolher_fala_variada(["Fechar o quê, Pedro? Me fala o nome do programa direito.", "Qual programa eu fecho?", "Faltou o nome do app."]), "debochada", 2)
            return True
        return executar_intencao(
            {"intent": "CLOSE_APP", "params": {"nome_app": nome_app}},
            texto_original,
            ctx,
        )

    if intent == "SEARCH":
        clima_like = any(
            trecho in str(texto_original or "").lower()
            for trecho in ["quantos graus", "temperatura", "clima", "como está o tempo", "como esta o tempo", "vai chover", "tempo em"]
        )
        if clima_like:
            local_clima = str(
                params.get("local")
                or params.get("cidade")
                or params.get("query")
                or texto_original
            ).strip()
            return executar_intencao({"intent": "WEATHER", "params": {"local": local_clima}}, texto_original, ctx)
        if "playlist" in str(texto_original or "").lower():
            pl = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
            if not pl and callable(extrair_nome_playlist):
                try:
                    pl = str(extrair_nome_playlist(texto_original) or "").strip()
                except Exception:
                    pl = ""
            if not pl:
                pl = str(ultima_playlist or "").strip()
            if pl:
                return executar_intencao({"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}, texto_original, ctx)
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Isso é playlist, Pedro. Eu leio arquivo local, não o Google. Me diz qual playlist.",
                    "Me diz qual playlist você quer ver.",
                    "Playlist é comigo, mas preciso do nome certo.",
                ]), "debochada", 2)
            return True
        query = str(params.get("query") or params.get("termo") or params.get("q") or texto_original).strip()
        lower_text = str(texto_original or "").strip().lower()
        allow_google = ("pesquisa" in lower_text) or lower_text.startswith("o que é") or lower_text.startswith("o que eh")
        engine = str(params.get("engine") or params.get("site") or ("google" if allow_google else "")).strip().lower()
        if engine == "youtube":
            if destino_val == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "open_url", "url": "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)})
            elif callable(enviar_chrome):
                enviar_chrome("youtube_search", {"query": query})
            fala_search = _escolher_fala_variada([
                f"Sintonizando o melhor do {query} no YouTube agora, Pedro.",
                f"Botando {query} pra tocar agora.",
                f"Já achei {query}.",
            ])
            if callable(falar):
                falar(fala_search, "calma", 1)
            if callable(registrar_mente_curta):
                registrar_mente_curta(texto_original, fala_search, "SEARCH", query, "", "pesquisa")
            return True
        if not allow_google:
            try:
                if isinstance(messages, list):
                    messages.append({"role": "user", "content": texto_original})
                bot_raw = enviar_mensagem(messages) if callable(enviar_mensagem) else ""
                bot = _remover_prefixo_exec(limpar_resposta(bot_raw)) if callable(_remover_prefixo_exec) and callable(limpar_resposta) else str(bot_raw)
                if bot and isinstance(messages, list):
                    messages.append({"role": "assistant", "content": bot})
                if callable(falar):
                    falar(bot or _escolher_fala_variada(["Oi, Pedro.", "Fala comigo, Pedro.", "Tô por aqui."]), current_emotion, emotion_level)
                if bot and callable(registrar_mente_curta):
                    registrar_mente_curta(texto_original, bot, "SEARCH", query, "", "pesquisa")
            except Exception:
                if callable(falar):
                    falar(_escolher_fala_variada(["Oi, Pedro.", "Fala comigo, Pedro.", "Tô por aqui."]), "calma", 1)
            return True
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        if destino_val == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "open_url", "url": url + "&laylay_auto=true", "auto_click": True})
        elif callable(enviar_chrome):
            enviar_chrome("open_url", {"url": url + "&laylay_auto=true", "auto_click": True})
        fala_search = _escolher_fala_variada([f"Abrindo a busca para {query}.", f"Já procurei {query}.", f"Abri a busca de {query}."])
        if callable(falar):
            falar(fala_search, "calma", 1)
        if callable(registrar_mente_curta):
            registrar_mente_curta(texto_original, fala_search, "SEARCH", query, "", "pesquisa")
        return True

    if intent == "AGENDAR_LEMBRETE":
        import uuid as _uuid, datetime as _dt
        descricao = str(params.get("descricao") or params.get("alvo") or params.get("texto") or "").strip() or "Lembrete"
        minutos = params.get("minutos")
        hora_alvo = str(params.get("hora_alvo") or params.get("hora") or "").strip()
        ag_id = str(_uuid.uuid4())[:8]
        try:
            if minutos is not None:
                ts_exec = _dt.datetime.now().timestamp() + int(minutos) * 60
                tempo_txt = f"em {int(minutos)} minutos"
            elif hora_alvo:
                hoje = _dt.date.today()
                ts_exec = _dt.datetime.strptime(f"{hoje} {hora_alvo}", "%Y-%m-%d %H:%M").timestamp()
                tempo_txt = f"às {hora_alvo}"
            else:
                if callable(falar):
                    falar(_escolher_fala_variada([
                        "Me diz o horário ou em quantos minutos eu te lembro disso.",
                        "Fala o horário ou os minutos do lembrete.",
                        "Preciso do tempo pra guardar esse lembrete.",
                    ]), "calma", 1)
                return True
        except Exception:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Não consegui entender o horário do lembrete. Fala no formato 12:30 ou em 15 minutos.",
                    "Esse horário não bateu. Tenta 12:30 ou 15 minutos.",
                    "Me passa a hora num formato mais certinho.",
                ]), "calma", 1)
            return True
        novo_ag = {"id": ag_id, "tipo": "once", "ts_execucao": ts_exec, "descricao": descricao, "comandos_no_disparo": [], "nome": descricao[:30], "ativo": True, "criado_em": _dt.datetime.now().isoformat()}
        lista_ag = _agendamentos_load() if callable(_agendamentos_load) else []
        lista_ag.append(novo_ag)
        if callable(_agendamentos_save):
            _agendamentos_save(lista_ag)
        if callable(falar):
            falar(_escolher_fala_variada([
                f"Feito. Vou te lembrar {tempo_txt} de {descricao}.",
                f"Pronto, lembrete salvo para {tempo_txt}.",
                f"Anotado. Vou te lembrar de {descricao} {tempo_txt}.",
            ]), "debochada", 2)
        if callable(_get(ctx, "_registrar_mente_curta")):
            _get(ctx, "_registrar_mente_curta")(texto_original, descricao, "AGENDAR_LEMBRETE", descricao, hora_alvo or str(minutos or ""), "agenda")
        return True

    if intent == "LISTAR_AGENDAMENTOS":
        lista_ag = _agendamentos_load() if callable(_agendamentos_load) else []
        ativos = [a for a in lista_ag if a.get("ativo", True)]
        resumo = _fala_agendamentos_estilosa(ativos) if callable(_fala_agendamentos_estilosa) else "Agendamentos."
        if callable(falar):
            falar(resumo, "debochada", 1)
        return True

    if intent == "CANCELAR_AGENDAMENTO":
        alvo = str(params.get("alvo") or params.get("nome") or params.get("query") or "").strip().lower()
        if not alvo:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Cancelo o quê, Pedro? Me fala qual lembrete ou compromisso você quer apagar.",
                    "Qual compromisso eu corto?",
                    "Faltou dizer qual agendamento eu devo apagar.",
                ]), "debochada", 2)
            return True
        lista_ag = _agendamentos_load() if callable(_agendamentos_load) else []
        cancelados = 0
        for ag in lista_ag:
            nome = str(ag.get("nome") or ag.get("descricao") or ag.get("id") or "").lower()
            ag_id = str(ag.get("id") or "").lower()
            if alvo in nome or alvo == ag_id:
                ag["ativo"] = False
                cancelados += 1
        if callable(_agendamentos_save):
            _agendamentos_save(lista_ag)
        msg = _escolher_fala_variada([
            f"{cancelados} agendamento(s) cancelado(s)." if cancelados else "Nao achei nenhum agendamento com esse nome.",
            f"Apaguei {cancelados} agendamento(s)." if cancelados else "Não encontrei nenhum agendamento com esse nome.",
            f"Feito, {cancelados} compromisso(s) saíram da lista." if cancelados else "Nada pra cancelar com esse nome.",
        ])
        if callable(falar):
            falar(msg, "calma", 1)
        return True

    if intent == "PLAYLIST_DELETE":
        pl = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or params.get("alvo") or "").strip()
        if not pl:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Qual playlist eu apago, Pedro?",
                    "Me fala o nome da playlist antes de eu sair cortando coisa.",
                    "Faltou o nome da playlist.",
                ]), "calma", 1)
            return True
        delete_playlist = _get(ctx, "delete_playlist")
        ok_delete = bool(delete_playlist(pl)) if callable(delete_playlist) else False
        _marcar_resultado("playlist_deletada" if ok_delete else "falha_execucao", executou=ok_delete)
        if ok_delete and callable(ctx.get("set_ultima_playlist")):
            ctx["set_ultima_playlist"]("")
        if callable(falar):
            falar(_escolher_fala_variada([
                f"Apaguei a playlist {pl}. Ela saiu do palco.",
                f"Playlist {pl} deletada.",
                f"Pronto, removi {pl} das suas playlists.",
            ] if ok_delete else [
                f"Tentei apagar a playlist {pl}, mas não encontrei ela.",
                f"{pl} não apareceu nas playlists pra eu apagar.",
                f"Procurei a playlist {pl}, mas ela não deu as caras.",
            ]), "calma" if ok_delete else "irritada", 1 if ok_delete else 2)
        return True

    if intent == "PLAYLIST_ADD":
        pl = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
        if not pl:
            if callable(_playlist_nome_explicito_na_frase) and _playlist_nome_explicito_na_frase(texto_original):
                if callable(falar):
                    falar(_escolher_fala_variada([
                        "Qual playlist é essa? Me diz o nome certo ou me ensina o apelido.",
                        "Essa playlist veio meio torta. Me passa o nome certo.",
                        "Preciso do nome da playlist ou do apelido que eu já conheço.",
                    ]), "calma", 1)
                return True
            pl = str(ultima_playlist or "").strip()
        if not pl:
            if callable(falar):
                falar(_escolher_fala_variada(["Me diz o nome da playlist.", "Qual playlist você quer?", "Faltou o nome da playlist."]), "calma", 1)
            return True
        info = solicitar_aba() if callable(solicitar_aba) else {}
        url = str(info.get("url") or "") if isinstance(info, dict) else ""
        title = str(info.get("title") or "") if isinstance(info, dict) else ""
        canal = str(info.get("canal") or "") if isinstance(info, dict) else ""
        if not url:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Ih Pedro, perdi o sinal do Chrome, não consegui salvar.",
                    "Perdi a janela do Chrome e não consegui salvar.",
                    "Não achei a aba certa para salvar isso.",
                ]), "calma", 1)
            return True
        if "youtube.com" not in url:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Não achei música aberta pra salvar aqui.",
                    "Não vi nenhuma música aberta para guardar.",
                    "Faltou uma música aberta no navegador.",
                ]), "calma", 1)
            return True
        ok = add_to_playlist(pl, url, title, canal) if callable(add_to_playlist) else False
        if ok:
            if callable(ctx.get("set_ultima_playlist")):
                ctx["set_ultima_playlist"](pl)
            if callable(falar):
                falar(_escolher_fala_variada([
                    f"Beleza, guardando {(_get(ctx,'_yt_clean_title', lambda x: x)(title) or 'essa música')} na playlist {pl}.",
                    f"Pronto, {(_get(ctx,'_yt_clean_title', lambda x: x)(title) or 'essa música')} foi pra playlist {pl}.",
                    f"Salvei {(_get(ctx,'_yt_clean_title', lambda x: x)(title) or 'essa música')} em {pl}.",
                ]), "debochada", 2)
        else:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Ih Pedro, deu erro no meu caderninho aqui. Não consegui salvar essa porcaria não.",
                    "Meu caderninho travou e não salvou agora.",
                    "Deu ruim no registro da playlist. Tenta de novo.",
                ]), "debochada", 2)
        return True

    if intent == "PLAYLIST_LIST":
        pl = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
        if callable(pedido_lista_geral) and pedido_lista_geral(texto_original, params):
            if callable(falar):
                falar(
                    listar_playlists_salvas() if callable(listar_playlists_salvas) else "Sem playlists.",
                    "calma",
                    1,
                )
            return True
        if not pl and callable(extrair_nome_playlist):
            try:
                pl = str(extrair_nome_playlist(texto_original) or "").strip()
            except Exception:
                pl = ""
        if not pl:
            if callable(_playlist_nome_explicito_na_frase) and _playlist_nome_explicito_na_frase(texto_original):
                if callable(falar):
                    falar(_escolher_fala_variada([
                        "Qual playlist você quer ver? Esse nome veio pela metade.",
                        "Me fala o nome completo da playlist.",
                        "Esse nome ficou incompleto. Me dá a playlist certa.",
                    ]), "calma", 1)
                return True
            pl = str(ultima_playlist or "").strip()
        if not pl:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Tá, mas qual playlist? Eu não leio pensamento. Ainda.",
                    "Me diz qual playlist você quer ver.",
                    "Faltou o nome da playlist.",
                ]), "debochada", 2)
            return True
        info = list_playlist_content(pl) if callable(list_playlist_content) else {"ok": False, "name": pl, "total": 0}
        nm = str(info.get("name") or pl).strip()
        if info.get("ok") and int(info.get("total", 0) or 0) > 0 and callable(fala_playlist_conteudo_estilosa):
            if callable(falar):
                falar(fala_playlist_conteudo_estilosa(info, pl), "calma", 1)
        else:
            if callable(falar):
                falar(_escolher_fala_variada([
                    f"Não achei a playlist {pl}. Se quiser, eu listo as que estão salvas.",
                    f"{pl} não apareceu. Posso listar as que estão salvas.",
                    f"Não encontrei {pl}. Quer que eu mostre as playlists salvas?",
                ]), "calma", 1)
        if callable(ctx.get("set_ultima_playlist")):
            ctx["set_ultima_playlist"](nm or pl)
        return True

    if intent == "PLAYLIST_PLAY":
        if callable(_autonomia_permite_execucao_musical) and not _autonomia_permite_execucao_musical(intent, texto_original):
            print("🎵 [AUTONOMIA] PLAYLIST_PLAY bloqueado: sem pedido explícito de playlist.")
            return False
        texto_base = _normalizar_texto_com_apelidos(texto_original) if callable(_normalizar_texto_com_apelidos) else texto_original
        if "playlist" not in str(texto_base).lower():
            pass
        pl = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
        if not pl:
            if callable(_playlist_nome_explicito_na_frase) and _playlist_nome_explicito_na_frase(texto_original):
                if callable(falar):
                    falar(_escolher_fala_variada([
                        "Qual playlist é essa? Fala o nome completo ou o apelido que eu já conheço.",
                        "Essa playlist veio pela metade. Me fala o nome certo.",
                        "Preciso do nome completo ou do apelido conhecido.",
                    ]), "calma", 1)
                return True
            pl = str(ultima_playlist or "").strip()
        if not pl:
            if callable(falar):
                falar(_escolher_fala_variada([
                    "Tá, mas qual playlist? Eu não leio pensamento. Ainda.",
                    "Me diz qual playlist você quer tocar.",
                    "Faltou o nome da playlist.",
                ]), "debochada", 2)
            return True
        modo = str(params.get("modo") or "").strip().lower()
        if modo == "shuffle":
            info = _playlist_shuffle_start(pl) if callable(_playlist_shuffle_start) else None
            if not info or not str(info.get("url") or ""):
                if callable(falar):
                    falar(_escolher_fala_variada([
                        f"Essa playlist {pl} tá vazia. Quer que eu invente música também?",
                        f"{pl} tá vazia por enquanto.",
                        f"Não tem música em {pl} ainda.",
                    ]), "debochada", 2)
                return True
            url = str(info.get("url") or "")
            ok_playlist = _abrir_url_musical(url)
            if callable(ctx.get("set_playlist_state_last_url")):
                ctx["set_playlist_state_last_url"](url)
            if callable(ctx.get("set_ultima_playlist")):
                ctx["set_ultima_playlist"](pl)
            _marcar_resultado("playlist_aberta" if ok_playlist else "falha_execucao", executou=ok_playlist)
            if callable(falar):
                falar(
                    _fala_de_confirmacao_variada(
                        "playlist_play",
                        fallback=f"Abrindo sua playlist de {pl}." if ok_playlist else f"Tentei abrir a playlist {pl}, mas a rota musical falhou.",
                        alvo=pl,
                        contexto=_ctx_fala(),
                        texto_usuario=texto_original,
                    ),
                    "debochada",
                    2,
                )
            return bool(ok_playlist)
        if destino_val == "pc_b":
            url = _playlist_primeira_url(pl) if callable(_playlist_primeira_url) else None
            if not url:
                _sugerir_criacao_playlist(pl)
                return True
            ok_playlist = _abrir_url_musical(str(url or ""))
            if callable(ctx.get("set_ultima_playlist")):
                ctx["set_ultima_playlist"](pl)
            _marcar_resultado("playlist_aberta_pc_b" if ok_playlist else "falha_execucao", executou=ok_playlist)
            if callable(falar):
                falar(
                    _fala_de_confirmacao_variada(
                        "playlist_play",
                        fallback=f"Abrindo sua playlist de {pl} no PC B." if ok_playlist else f"Tentei abrir {pl} no PC B, mas a rota falhou.",
                        alvo=pl,
                        contexto=_ctx_fala(),
                        texto_usuario=texto_original,
                    ),
                    "debochada",
                    2,
                )
            return bool(ok_playlist)
        ok = play_playlist(pl) if callable(play_playlist) else False
        if not ok:
            _marcar_resultado("falha_execucao", executou=False)
            _sugerir_criacao_playlist(pl)
            return True
        if callable(ctx.get("set_ultima_playlist")):
            ctx["set_ultima_playlist"](pl)
        n = _playlist_len(pl) if callable(_playlist_len) else 0
        _marcar_resultado("playlist_aberta", executou=True)
        if callable(falar):
            falar(
                _fala_de_confirmacao_variada(
                    "playlist_play",
                    fallback=f"Abrindo sua playlist de {pl}. Você já tem {n} músicas guardadas comigo.",
                    alvo=pl,
                    contexto=_ctx_fala(),
                    texto_usuario=texto_original,
                ),
                "debochada",
                2,
            )
        return True

    if callable(falar):
        falar(_escolher_fala_variada([
            "Eu não fechei tua intenção direito agora. Tenta falar de outro jeito pra mim.",
            "Me perdi um pouco aqui. Tenta falar de outro jeito.",
            "Não entendi direito. Repete pra mim com outras palavras.",
            "Quase peguei o fio, mas ele escapou. Me fala de novo sem pressa.",
        ]), "calma", 1)
    return True
