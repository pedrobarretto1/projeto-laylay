"""Dispatcher dos comandos JSON executados pela resposta da IA."""

from __future__ import annotations

import json
import re
import subprocess
import threading
from typing import Any, Dict, List

from mente_laylay.personalidade.falas_variadas import fala_por_estado_acao as _fala_por_estado_acao


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def executar_comandos_json(
    ctx: Dict[str, Any],
    texto: str,
    comandos: List[Dict[str, Any]],
    fala_limpa_original: str,
    tipo_interacao: str,
    fala_ja_emitida: bool,
    fala_emitida_por_acao: bool,
    fala_salva_no_inicio: bool,
) -> Dict[str, Any]:
    """Executa ações JSON usando o contexto compartilhado da Laylay."""
    mensagens = _get(ctx, "messages")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")
    salvar_memoria = _get(ctx, "salvar_memoria")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    enviar_comando_chrome = _get(ctx, "enviar_comando_chrome")
    abrir_programa = _get(ctx, "abrir_programa")
    fechar_programa = _get(ctx, "fechar_programa")
    _enviar_pc_b = _get(ctx, "_enviar_pc_b")
    _detectar_foco_app_local = _get(ctx, "_detectar_foco_app_local")
    _normalizar_query_musical = _get(ctx, "_normalizar_query_musical")
    _limpar_nome_playlist = _get(ctx, "_limpar_nome_playlist")
    _playlist_shuffle_start = _get(ctx, "_playlist_shuffle_start")
    _buscar_primeiro_video_youtube = _get(ctx, "_buscar_primeiro_video_youtube")
    add_to_playlist_url = _get(ctx, "add_to_playlist_url")
    solicitar_aba_ativa = _get(ctx, "solicitar_aba_ativa")
    playlists_carregadas = _get(ctx, "playlists_carregadas", {})
    _playlists_load = _get(ctx, "_playlists_load")
    listar_abas_chrome = _get(ctx, "listar_abas_chrome")
    listar_programas_abertos = _get(ctx, "listar_programas_abertos")
    organizar_janelas_robusto = _get(ctx, "organizar_janelas_robusto")
    ativar_tela_cheia_robusta = _get(ctx, "ativar_tela_cheia_robusta")
    criar_pasta = _get(ctx, "criar_pasta")
    criar_ou_editar_arquivo = _get(ctx, "criar_ou_editar_arquivo")
    deletar_item = _get(ctx, "deletar_item")
    registrar_memoria_visual = _get(ctx, "registrar_memoria_visual")
    _capturar_tela_base64 = _get(ctx, "_capturar_tela_base64")
    _analisar_com_groq = _get(ctx, "_analisar_com_groq")
    _obter_contexto_perceptivo = _get(ctx, "_obter_contexto_perceptivo")
    _agendamentos_load = _get(ctx, "_agendamentos_load")
    _agendamentos_save = _get(ctx, "_agendamentos_save")
    _gmail_nao_lidos_cache = _get(ctx, "_gmail_nao_lidos_cache")
    _gmail_buscar_nao_lidos = _get(ctx, "_gmail_buscar_nao_lidos")
    _gmail_falar_resumo_estiloso = _get(ctx, "_gmail_falar_resumo_estiloso")
    ws_loop = _get(ctx, "ws_loop")
    broadcast_command = _get(ctx, "broadcast_command")
    _abas_sugeridas_fechar = _get(ctx, "_abas_sugeridas_fechar")
    _executar_exec = _get(ctx, "_executar_exec")
    processar_comando_deterministico = _get(ctx, "processar_comando_deterministico")
    _autorizar_acao_pratica = _get(ctx, "_autorizar_acao_pratica")
    _autonomia_permite_execucao_musical = _get(ctx, "_autonomia_permite_execucao_musical")

    erros_execucao: List[str] = []
    if not isinstance(comandos, list):
        comandos = []

    def _extrair_alvo(cmd: dict) -> str:
        for k in ("alvo", "url", "app", "query", "nome"):
            v = cmd.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        return ""

    def _destino_cmd(cmd: dict, padrao: str = "pc_a") -> str:
        return str(cmd.get("target", padrao)).lower().strip()

    def _playlists_atuais() -> Dict[str, Any]:
        if isinstance(playlists_carregadas, dict) and playlists_carregadas:
            return playlists_carregadas
        if callable(_playlists_load):
            try:
                data = _playlists_load() or {}
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def _ctx_fala() -> Dict[str, Any]:
        return {
            "current_emotion": current_emotion,
            "ultima_habilidade": "",
            "ultimo_alvo": "",
        }

    def _falar_status(status: str, fallback: str, *, alvo: str = "", emocao: str = "debochada", nivel: int = 2) -> None:
        nonlocal fala_emitida_por_acao
        if not callable(falar_com_lipsync):
            return
        falar_com_lipsync(
            _fala_por_estado_acao(
                status,
                fallback=fallback,
                alvo=alvo,
                contexto=_ctx_fala(),
                texto_usuario=texto,
            ),
            emocao,
            nivel,
        )
        fala_emitida_por_acao = True

    def _abrir_url(destino: str, url: str) -> None:
        if destino == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "open_url", "url": url})
        elif destino == "ambos" and callable(_enviar_pc_b):
            enviar_comando_chrome("open_url", {"url": url})
            _enviar_pc_b({"action": "open_url", "url": url})
        else:
            enviar_comando_chrome("open_url", {"url": url})

    def _enviar_youtube_control(destino: str, command: str) -> None:
        if destino == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "youtube_control", "command": command})
        elif destino == "ambos" and callable(_enviar_pc_b):
            enviar_comando_chrome("youtube_control", {"command": command})
            _enviar_pc_b({"action": "youtube_control", "command": command})
        else:
            enviar_comando_chrome("youtube_control", {"command": command})

    def _abrir_app(destino: str, nome_app: str, quantidade: int = 1) -> None:
        if destino == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "open_app", "app": nome_app, "quantidade": quantidade})
        elif destino == "ambos" and callable(_enviar_pc_b):
            abrir_programa(nome_app)
            _enviar_pc_b({"action": "open_app", "app": nome_app, "quantidade": quantidade})
        else:
            abrir_programa(nome_app)

    def _fechar_app(destino: str, nome_app: str) -> None:
        if destino == "pc_b" and callable(_enviar_pc_b):
            _enviar_pc_b({"action": "close_app", "app": nome_app})
        elif destino == "ambos" and callable(_enviar_pc_b):
            fechar_programa(nome_app)
            _enviar_pc_b({"action": "close_app", "app": nome_app})
        else:
            fechar_programa(nome_app)

    _MENCOES_PC_B = ["pc b", "pc_b", "computador b", "no b", "pro b", "pra b"]
    _usuario_pediu_pc_b = any(m in texto.lower() for m in _MENCOES_PC_B)

    if _usuario_pediu_pc_b:
        for _cmd in comandos:
            if isinstance(_cmd, dict) and not _cmd.get("target"):
                if str(_cmd.get("acao", "")).strip() in {"open_url", "youtube_search", "youtube_control", "open_app", "close_app", "organizar_desktop", "capturar_tela", "volume_up", "volume_down", "volume_set", "volume_mute", "parar_midia", "tocar_playlist", "close_tab", "close_specific_tab", "notificar", "criar_pasta"}:
                    _cmd["target"] = "pc_b"
        print(f"🎯 [PC B] Target injetado em {len(comandos)} comando(s) — usuário pediu PC B.")

    if not comandos and processar_comando_deterministico and processar_comando_deterministico(texto, "pos-ia-0-comandos"):
        return {"erros": [], "fala_emitida_por_acao": False, "fala_ja_emitida": fala_ja_emitida, "fala_salva_no_inicio": fala_salva_no_inicio}

    for cmd in comandos:
        if not isinstance(cmd, dict):
            continue
        acao = str(cmd.get("acao", "")).strip()
        if not acao or acao.upper() in {"", "NENHUM", "NONE"}:
            continue
        alvo_raw = _extrair_alvo(cmd)
        alvo = re.sub(r'\[.*?\]\((.*?)\)', r'\1', str(alvo_raw or "")).replace("[", "").replace("]", "").strip('"\' ')

        if acao == "open_url" and callable(enviar_comando_chrome):
            destino = _destino_cmd(cmd)
            url_bruta = alvo.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
            if not url_bruta.startswith(("http://", "https://")):
                foco_local = _detectar_foco_app_local(texto or "") if callable(_detectar_foco_app_local) else None
                if foco_local and callable(organizar_janelas_robusto):
                    try:
                        organizar_janelas_robusto("vscode", foco_local["app"])
                    except Exception:
                        pass
                    if callable(ativar_tela_cheia_robusta):
                        try:
                            ativar_tela_cheia_robusta(foco_local["app"])
                        except Exception:
                            pass
                _falar_status(
                    "app_focado",
                    "Pronto. Dei foco no Opera em vez de te mandar pra uma busca torta.",
                    alvo=foco_local["app"] if isinstance(foco_local, dict) else "opera",
                )
                continue
            _abrir_url(destino, url_bruta)

        elif acao == "youtube_search" and callable(enviar_comando_chrome):
            if callable(_autorizar_acao_pratica):
                decisao = _autorizar_acao_pratica("MUSIC_SEARCH", texto, origem="json")
                if not bool(decisao.get("permitido")):
                    print(f"🎵 [AUTONOMIA] youtube_search JSON bloqueado: {decisao.get('motivo')}.")
                    continue
            elif callable(_autonomia_permite_execucao_musical) and not _autonomia_permite_execucao_musical("MUSIC_SEARCH", texto):
                print("🎵 [AUTONOMIA] youtube_search JSON bloqueado: sem pedido musical explícito.")
                continue
            destino = _destino_cmd(cmd)
            alvo = _normalizar_query_musical(alvo or texto) if callable(_normalizar_query_musical) else alvo
            pl_nome = _limpar_nome_playlist(alvo) if callable(_limpar_nome_playlist) else ""
            if pl_nome:
                try:
                    if pl_nome in _playlists_atuais():
                        info = _playlist_shuffle_start(pl_nome) if callable(_playlist_shuffle_start) else None
                        if info and info.get("url"):
                            url = str(info.get("url") or "")
                            if destino == "pc_b" and callable(_enviar_pc_b):
                                _enviar_pc_b({"action": "open_url", "url": url})
                            elif destino == "ambos" and callable(_enviar_pc_b):
                                enviar_comando_chrome("youtube_play", {"url": url})
                                _enviar_pc_b({"action": "open_url", "url": url})
                            else:
                                enviar_comando_chrome("youtube_play", {"url": url})
                            continue
                except Exception:
                    pass
            if destino == "pc_b" and callable(_buscar_primeiro_video_youtube) and callable(_enviar_pc_b):
                link_direto = _buscar_primeiro_video_youtube(alvo)
                _enviar_pc_b({"action": "open_url", "url": link_direto or ("https://www.youtube.com/results?search_query=" + alvo.replace(" ", "+"))})
            elif destino == "ambos" and callable(_buscar_primeiro_video_youtube) and callable(_enviar_pc_b):
                link_direto = _buscar_primeiro_video_youtube(alvo)
                url_final = link_direto or ("https://www.youtube.com/results?search_query=" + alvo.replace(" ", "+"))
                enviar_comando_chrome("youtube_search", {"query": alvo})
                _enviar_pc_b({"action": "open_url", "url": url_final})
            else:
                enviar_comando_chrome("youtube_search", {"query": alvo})

        elif acao == "youtube_control" and callable(enviar_comando_chrome):
            destino = _destino_cmd(cmd)
            _enviar_youtube_control(destino, alvo)

        elif acao == "open_app" and callable(abrir_programa):
            destino = _destino_cmd(cmd)
            _abrir_app(destino, alvo)

        elif acao == "close_app" and callable(fechar_programa):
            destino = _destino_cmd(cmd)
            _fechar_app(destino, alvo)

        elif acao in {"adicionar_playlist", "adicionar_a_playlist"} and callable(add_to_playlist_url):
            playlist_nome = str(cmd.get("alvo") or cmd.get("playlist") or "").strip()
            if not playlist_nome:
                continue
            info = solicitar_aba_ativa(timeout_s=3.0) if callable(solicitar_aba_ativa) else {}
            url = str((info or {}).get("url") or "").strip()
            title = str((info or {}).get("title") or "").strip()
            canal = str((info or {}).get("canal") or "").strip()
            if url and "youtube.com" in url:
                add_to_playlist_url(playlist_nome, url, title, canal)

        elif acao == "capturar_tela" and callable(_capturar_tela_base64) and callable(_analisar_com_groq):
            destino = str(cmd.get("target", "pc_a")).lower().strip()
            pergunta_visao = "Você é a Laylay, assistente debochada, sarcástica e dona absoluta do PC do Pedro. Olhe para esta tela e descreva o que o Pedro está fazendo ou o que está aberto. Seja curta (máximo 3 linhas), direta, irônica e julgue as escolhas dele se for o caso. Responda SEMPRE em português brasileiro, com seu jeitão de sempre."
            if destino == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "capturar_tela", "pergunta": pergunta_visao})
                _falar_status("__captura_pc_b__", "Abrindo o olho no PC B, um segundo...", alvo="pc b", emocao="calma", nivel=1)
            else:
                def _ver_tela_local():
                    try:
                        img_b64 = _capturar_tela_base64()
                        if not img_b64:
                            return
                        descricao = _analisar_com_groq(img_b64, pergunta_visao)
                        if callable(registrar_memoria_visual):
                            try:
                                registrar_memoria_visual(img_b64, descricao, motivo="captura visual manual", contexto=_obter_contexto_perceptivo() if callable(_obter_contexto_perceptivo) else {}, emocao=current_emotion or "calma", intensidade=int(emotion_level or 1), tags=["visao", "captura", "manual"], origem="pc_a")
                            except Exception:
                                pass
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(descricao[:300], current_emotion or "debochada", emotion_level or 2)
                    except Exception:
                        if callable(falar_com_lipsync):
                            falar_com_lipsync("Tive um problema pra olhar a tela, Pedro.", "irritada", 2)
                threading.Thread(target=_ver_tela_local, daemon=True).start()

        elif acao == "organizar_desktop" and callable(organizar_janelas_robusto):
            app_esquerda = str(cmd.get("left") or cmd.get("esquerda") or cmd.get("vscode") or "vscode").strip()
            app_direita = str(cmd.get("right") or cmd.get("direita") or cmd.get("opera") or cmd.get("chrome") or "opera").strip()
            destino = str(cmd.get("target", "pc_a")).lower().strip()
            if destino == "pc_b" and callable(_enviar_pc_b):
                _enviar_pc_b({"action": "organizar_desktop", "left": app_esquerda, "right": app_direita})
            else:
                organizar_janelas_robusto(app_esquerda, app_direita)

        elif acao == "maximize_window":
            continue

        elif acao == "criar_pasta" and callable(criar_pasta):
            criar_pasta(alvo)
            _falar_status("__pasta_criada__", f"Pasta {alvo} criada.", alvo=alvo or "pasta", emocao="calma", nivel=1)

        elif acao == "criar_arquivo" and callable(criar_ou_editar_arquivo):
            criar_ou_editar_arquivo(alvo or "novo_arquivo.txt", "")

        elif acao == "deletar_item" and callable(deletar_item):
            deletar_item(alvo)

        elif acao == "verificar_programas" and callable(listar_programas_abertos):
            lista = listar_programas_abertos()
            info_txt = "System: Programas/janelas abertas no momento: " + ", ".join(lista[:25]) if lista else "System: Nenhum programa com janela visível encontrado no momento."
            if isinstance(mensagens, list):
                mensagens.append({"role": "user", "content": info_txt + "\n\n[RESPOSTA OBRIGATÓRIA EM JSON: {\"fala\": \"...\", \"comandos\": [...]}]"})

        elif acao == "verificar_abas" and callable(listar_abas_chrome):
            abas = listar_abas_chrome(timeout_s=5.0)
            info_txt = "System: Abas abertas no Chrome:\n" + "\n".join([f"{i}. {str(a.get('titulo') or '')[:60]} | {str(a.get('url') or '')[:80]}" for i, a in enumerate(abas[:20], 1)]) if abas else "System: Nenhuma aba encontrada no Chrome (extensão pode estar desconectada)."
            if isinstance(mensagens, list):
                mensagens.append({"role": "user", "content": info_txt + "\n\n[RESPOSTA OBRIGATÓRIA EM JSON: {\"fala\": \"...\", \"comandos\": [...]}]"})

        elif acao == "agendar_lembrete" and callable(_agendamentos_load) and callable(_agendamentos_save):
            import datetime as _dt, uuid as _uuid, time as _ti
            minutos = cmd.get("minutos")
            hora_alvo = str(cmd.get("hora_alvo") or "").strip()
            descricao = str(cmd.get("descricao") or alvo or "Lembrete!").strip()
            comandos_disparo = cmd.get("comandos_no_disparo") or []
            ag_id = str(_uuid.uuid4())[:8]
            ts_exec = _ti.time() + int(minutos) * 60 if minutos is not None else _dt.datetime.strptime(f"{_dt.date.today()} {hora_alvo}", "%Y-%m-%d %H:%M").timestamp()
            novo_ag = {"id": ag_id, "tipo": "once", "ts_execucao": ts_exec, "descricao": descricao, "comandos_no_disparo": comandos_disparo, "nome": descricao[:30], "ativo": True, "criado_em": _dt.datetime.now().isoformat()}
            lista_ag = _agendamentos_load()
            lista_ag.append(novo_ag)
            _agendamentos_save(lista_ag)

        elif acao == "ler_emails" and callable(_gmail_falar_resumo_estiloso):
            emails_c = _gmail_nao_lidos_cache or (_gmail_buscar_nao_lidos() if callable(_gmail_buscar_nao_lidos) else [])
            _gmail_falar_resumo_estiloso(emails_c, somente_prioritarios=False)

        elif acao == "sincronizar_emails":
            pass

        elif acao == "fechar_abas_paradas" and _abas_sugeridas_fechar:
            if callable(broadcast_command) and ws_loop:
                for url_fechar in list(_abas_sugeridas_fechar):
                    payload = json.dumps({"action": "close_specific_tab", "target": url_fechar[:60]})
                    try:
                        import asyncio as _aio
                        _aio.run_coroutine_threadsafe(broadcast_command(payload), ws_loop)
                    except Exception:
                        pass
            _abas_sugeridas_fechar.clear()

        else:
            try:
                if callable(_executar_exec):
                    if acao.lower() in {"youtube", "youtube_search", "tocar_playlist", "youtube_play"} and callable(_autorizar_acao_pratica):
                        decisao = _autorizar_acao_pratica(acao, texto, origem="json_legacy")
                        if not bool(decisao.get("permitido")):
                            print(f"🎵 [AUTONOMIA] ação legada bloqueada: {acao} ({decisao.get('motivo')}).")
                            continue
                    _executar_exec(acao.upper(), alvo)
            except Exception as ef:
                erros_execucao.append(f"ação '{acao}' (alvo='{alvo}'): {type(ef).__name__} — {ef}")

    if callable(salvar_memoria):
        salvar_memoria()

    return {
        "erros": erros_execucao,
        "fala_emitida_por_acao": fala_emitida_por_acao,
        "fala_ja_emitida": fala_ja_emitida,
        "fala_salva_no_inicio": fala_salva_no_inicio,
    }
