"""Fluxos de conversa e fallback da Laylay."""

from __future__ import annotations

import re
import time
from typing import Any, Dict
from mente_laylay.personalidade.falas_variadas import escolher as _escolher_fala_variada
from mente_laylay.personalidade.falas_variadas import fala_de_confirmacao as _fala_de_confirmacao_variada
from mente_laylay.personalidade.falas_variadas import fala_por_estado_acao as _fala_por_estado_acao


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def _parece_comando_novo(texto_norm: str) -> bool:
    """Nao deixa uma sugestao pendente engolir um comando novo completo."""
    t = re.sub(r"\s+", " ", str(texto_norm or "").strip().lower())
    if not t:
        return False

    palavras = t.split()
    if len(palavras) <= 4 and any(p in t for p in [
        "pode", "sim", "nao", "não", "ler", "le", "lê", "ver", "vai", "faz",
    ]):
        return False

    sinais_comando = [
        "playlist", "musica", "música", "youtube", "spotify", "volume",
        "abre", "abrir", "abra", "entra", "entrar", "fecha", "fechar",
        "pasta", "arquivo", "cria", "criar", "apaga", "apagar",
        "steam", "opera", "vscode", "chrome", "ifood", "instagram",
        "agenda", "compromisso", "lembrete",
    ]
    return any(s in t for s in sinais_comando)


def _foco_recente(contexto: Dict[str, Any], ttl_s: float = 150.0) -> Dict[str, Any]:
    foco = _get(contexto, "foco_vivo", {})
    if not isinstance(foco, dict):
        return {}
    try:
        idade = float(foco.get("idade_s") or 999999.0)
    except Exception:
        idade = 999999.0
    if idade > ttl_s:
        return {}
    return foco


def usar_modo_rapido_conversa(
    texto: str,
    *,
    normalizar_texto=None,
    interpretar_comando_local_rapido=None,
    resolver_comando_contextual=None,
) -> bool:
    """Decide quando a conversa pode usar um prompt leve sem perder comandos."""
    if callable(normalizar_texto):
        try:
            t = str(normalizar_texto(texto) or "").strip()
        except Exception:
            t = str(texto or "").strip().lower()
    else:
        t = str(texto or "").strip().lower()
    if not t:
        return True

    if callable(interpretar_comando_local_rapido):
        try:
            if interpretar_comando_local_rapido(t):
                return False
        except Exception:
            pass
    if callable(resolver_comando_contextual):
        try:
            if resolver_comando_contextual(t):
                return False
        except Exception:
            pass

    palavras_pesadas = [
        "playlist", "arquivo", "pasta", "download", "chrome", "opera", "vscode",
        "janela", "aba", "tela cheia", "fullscreen", "youtube", "netflix",
        "música", "musica", "memória", "memoria", "lembra", "aprendeu",
        "foco", "maximiza", "maximizar", "fecha", "abre", "abre o", "abre a",
        "pausa", "despausa", "retoma", "proxima", "próxima", "anterior",
    ]
    if any(p in t for p in palavras_pesadas):
        return False

    return len(t) <= 90


def _pendencia_combina_com_texto(contexto: Dict[str, Any], tipo: str, texto_norm: str, alvo: str = "") -> bool:
    t = re.sub(r"\s+", " ", str(texto_norm or "").strip().lower())
    if not t:
        return False

    pistas_email = any(p in t for p in ["email", "emails", "gmail", "remetente", "caixa", "ler", "lê", "le", "ver"])
    pistas_musica = any(p in t for p in ["playlist", "musica", "música", "som", "faixa", "trilha", "youtube", "toca", "coloca", "salva"])
    pistas_app = any(p in t for p in [
        "app", "programa", "janela", "site", "aba", "abrir", "abre", "foco", "tela cheia",
        "maximiza", "maximizar", "opera", "chrome", "steam", "vscode", "store", "ifood",
    ])
    alvo_norm = str(alvo or "").strip().lower()
    foco = _foco_recente(contexto)
    foco_tipo = str((foco or {}).get("tipo") or "").strip().lower()
    foco_texto = " ".join(
        str((foco or {}).get(ch) or "").strip().lower()
        for ch in ("tipo", "topico", "alvo", "habilidade", "intencao", "texto", "resposta")
    )
    confirmacao_generica = t in {
        "sim", "claro", "claro que sim", "aham", "uhum", "isso", "isso mesmo",
        "pode", "pode sim", "pode ser", "quero", "quero sim", "bora", "vai", "manda",
        "ok", "beleza", "fechou", "fechado",
    }

    if alvo_norm and alvo_norm in t:
        return True

    if tipo == "email":
        if pistas_musica or (pistas_app and not pistas_email):
            return False
        if pistas_email:
            return True
        if confirmacao_generica and foco and foco_tipo not in {"email", "conversa", "pesquisa"} and "email" not in foco_texto:
            return False
        return True

    if tipo == "playlist":
        if pistas_email or (pistas_app and not pistas_musica):
            return False
        if pistas_musica:
            return True
        if confirmacao_generica and foco and foco_tipo not in {"playlist", "musica", "música", "midia", "conversa"}:
            return False
        return True

    if tipo == "rotina":
        if pistas_email or pistas_musica:
            return False
        if pistas_app:
            return True
        if confirmacao_generica and foco and foco_tipo not in {"janela", "site", "conversa"}:
            return False
        return True

    return True


def handle_feedback_pendente(contexto: Dict[str, Any], texto: str) -> bool:
    """Trata respostas a sugestões proativas antes de cair na conversa normal."""
    texto_norm = re.sub(r"\s+", " ", str(texto or "").strip().lower())
    if _parece_comando_novo(texto_norm):
        return False
    if any(p in texto_norm for p in [
        "deixa pra la", "deixa para la", "deixa quieto", "esquece", "cancela",
        "cancelar", "para com isso", "nao quero mais", "não quero mais",
        "quero mais nao", "quero mais não", "pode parar", "desiste",
    ]):
        for chave in (
            "_rotina_sugestao_pendente",
            "_playlist_sugestao_pendente",
        ):
            contexto[chave] = None
        if callable(_get(contexto, "_bloquear_playlist_temporariamente")):
            try:
                _get(contexto, "_bloquear_playlist_temporariamente")(0.0)
            except Exception:
                pass
        if callable(_get(contexto, "falar_com_lipsync")):
            _get(contexto, "falar_com_lipsync")(
                _escolher_fala_variada(["Certo, deixei isso pra lá.", "Beleza, cancelei.", "Tá, descartei a ideia."]),
                "calma",
                1,
            )
        return True
    rotina_sugestao_pendente = _get(contexto, "_rotina_sugestao_pendente")
    playlist_sugestao_pendente = _get(contexto, "_playlist_sugestao_pendente")
    email_sugestao_pendente = _get(contexto, "_email_sugestao_pendente")
    classificar_confirmacao_contextual = _get(contexto, "_classificar_confirmacao_contextual")
    classificar_confirmacao_local = _get(contexto, "_classificar_confirmacao_local")
    handle_sugestao_confirmacao = _get(contexto, "_handle_sugestao_confirmacao")
    solicitar_aba_ativa = _get(contexto, "solicitar_aba_ativa")
    add_to_playlist_url = _get(contexto, "add_to_playlist_url")
    extrair_nome_playlist = _get(contexto, "extrair_nome_playlist")
    yt_clean_title = _get(contexto, "_yt_clean_title")
    falar_com_lipsync = _get(contexto, "falar_com_lipsync")
    resolve_ultima_playlist = _get(contexto, "_set_ultima_playlist")
    registrar_feedback_rotina = _get(contexto, "_rotina_registrar_feedback")
    gmail_buscar = _get(contexto, "_gmail_buscar_nao_lidos")
    gmail_resumo = _get(contexto, "_gmail_falar_resumo_estiloso")

    agora = time.time()

    if email_sugestao_pendente is not None:
        if agora - float(email_sugestao_pendente.get("ts", 0.0)) > 120:
            print("[FEEDBACK EMAIL] Sugestao expirou sem resposta.")
            contexto["_email_sugestao_pendente"] = None
        else:
            alvo_email = str(email_sugestao_pendente.get("remetente") or "").strip()
            if not _pendencia_combina_com_texto(contexto, "email", texto_norm, alvo_email):
                alvo_email = alvo_email
            else:
                confirmado = None
                sugestao_txt = f"ver os emails de {alvo_email}" if alvo_email else "ver os emails"
                if callable(classificar_confirmacao_contextual):
                    confirmado = classificar_confirmacao_contextual(texto, sugestao_txt)
                elif callable(classificar_confirmacao_local):
                    confirmado = classificar_confirmacao_local(texto)
                if confirmado is not None:
                    status = "SIM" if confirmado else "NAO"
                    print(f"[FEEDBACK EMAIL] Resposta: {status} para '{alvo_email or 'emails'}'")
                    if confirmado:
                        emails_c = gmail_buscar() if callable(gmail_buscar) else []
                        if alvo_email:
                            alvo_norm = str(alvo_email).strip().lower()
                            filtrados = []
                            for e in emails_c if isinstance(emails_c, list) else []:
                                rem = str((e or {}).get("remetente") or "").strip().lower()
                                if alvo_norm and (alvo_norm == rem or alvo_norm in rem or rem in alvo_norm):
                                    filtrados.append(e)
                            emails_c = filtrados or emails_c
                        if callable(gmail_resumo):
                            gmail_resumo(emails_c, somente_prioritarios=False)
                    else:
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(
                                _escolher_fala_variada([
                                    "Tá, deixo os emails quietos por enquanto.",
                                    "Beleza, não vou abrir os emails agora.",
                                    "Certo, deixei essa caixa em paz.",
                                ]),
                                "calma",
                                1,
                            )
                    contexto["_email_sugestao_pendente"] = None
                    return True

    if playlist_sugestao_pendente is not None:
        if agora - float(playlist_sugestao_pendente.get("ts", 0.0)) > 90:
            print("[FEEDBACK PLAYLIST] Sugestao expirou sem resposta.")
            playlist_sugestao_pendente = None
        else:
            pl = str(playlist_sugestao_pendente.get("playlist") or "").strip()
            if _pendencia_combina_com_texto(contexto, "playlist", texto_norm, pl):
                confirmado = None
                if callable(classificar_confirmacao_contextual):
                    confirmado = classificar_confirmacao_contextual(texto, f"salvar a musica na playlist {pl}")
                elif callable(classificar_confirmacao_local):
                    confirmado = classificar_confirmacao_local(texto)
            else:
                confirmado = None
            if confirmado is not None:
                status = "SIM" if confirmado else "NAO"
                print(f"[FEEDBACK PLAYLIST] Resposta: {status} para '{pl}'")
                if confirmado:
                    info = solicitar_aba_ativa(timeout_s=2.0) if callable(solicitar_aba_ativa) else {}
                    url = str((info or {}).get("url") or "")
                    title = str((info or {}).get("title") or "")
                    canal = str((info or {}).get("canal") or "")
                    if not url or "youtube.com" not in url:
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_escolher_fala_variada(["Não achei a música aberta pra salvar agora.", "Não vi música aberta pra guardar.", "Faltou uma aba de música aberta."]), "calma", 1)
                    else:
                        res = add_to_playlist_url(pl, url, title, canal) if callable(add_to_playlist_url) else None
                        ok = res.get("ok") if isinstance(res, dict) else bool(res)
                    if ok:
                        if callable(resolve_ultima_playlist):
                            resolve_ultima_playlist(pl)
                        titulo = yt_clean_title(title) if callable(yt_clean_title) else title
                        titulo = titulo or "essa música"
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_escolher_fala_variada([
                                f"Beleza, criei e guardei {titulo} na playlist {pl}.",
                                f"Pronto, {titulo} foi pra playlist {pl}.",
                                f"Salvei {titulo} na playlist {pl}.",
                            ]), "debochada", 2)
                        else:
                            if callable(falar_com_lipsync):
                                falar_com_lipsync(_escolher_fala_variada(["Não consegui salvar essa música agora.", "O salvamento falhou por enquanto.", "Não deu pra guardar a música agora."]), "calma", 1)
                else:
                    if callable(falar_com_lipsync):
                        falar_com_lipsync(_escolher_fala_variada([
                            "Tá, deixei quieto.",
                            "Beleza, ignoro isso por enquanto.",
                            "Certo, vou deixar pra lá.",
                        ]), "calma", 1)
                contexto["_playlist_sugestao_pendente"] = None
                return True

    if rotina_sugestao_pendente is not None:
        if agora - float(rotina_sugestao_pendente.get("ts", 0.0)) > 90:
            print("[FEEDBACK ROTINA] Sugestao expirou sem resposta.")
            rotina_sugestao_pendente = None
        else:
            app = str(rotina_sugestao_pendente.get("app") or "")
            if _pendencia_combina_com_texto(contexto, "rotina", texto_norm, app):
                confirmado = None
                if callable(classificar_confirmacao_contextual):
                    confirmado = classificar_confirmacao_contextual(texto, f"abrir {app}")
                elif callable(classificar_confirmacao_local):
                    confirmado = classificar_confirmacao_local(texto)
            else:
                confirmado = None
            if confirmado is not None:
                status = "SIM" if confirmado else "NAO"
                print(f"[FEEDBACK ROTINA] Resposta: {status} para '{app}'")
                if callable(registrar_feedback_rotina):
                    registrar_feedback_rotina(aceito=bool(confirmado))
                contexto["_rotina_sugestao_pendente"] = None
                return True

    try:
        if callable(handle_sugestao_confirmacao) and handle_sugestao_confirmacao(texto):
            return True
    except Exception as e:
        print(f"⚠️ [SUGESTÃO] Falha ao tratar confirmação pendente: {e}")

    return False
def handle_comando_rapido_flow(contexto: Dict[str, Any], texto: str) -> bool:
    extrair_comando_rapido = _get(contexto, "extrair_comando_rapido")
    enviar_comando_chrome = _get(contexto, "enviar_comando_chrome")
    executar_intencao = _get(contexto, "executar_intencao")
    confirmar_execucao_debochada = _get(contexto, "_confirmar_execucao_debochada")
    if not callable(extrair_comando_rapido):
        return False

    cmd_rapido = extrair_comando_rapido(texto)
    if not cmd_rapido:
        return False

    tipo, arg = cmd_rapido
    if tipo == "OPEN_URL":
        if not callable(executar_intencao):
            return False
        return bool(executar_intencao({"intent": "OPEN_URL", "params": {"alvo": arg}}, texto))
    if tipo == "OPEN_APP":
        if not callable(executar_intencao):
            return False
        return bool(executar_intencao({"intent": "APP_OPEN", "params": {"nome_app": arg}}, texto))
    if tipo == "YOUTUBE" and callable(enviar_comando_chrome):
        enviar_comando_chrome("youtube_search", {"query": arg})
        if callable(confirmar_execucao_debochada):
            confirmar_execucao_debochada(
                texto,
                "O comando já foi executado pelo Python. Responda só com uma fala curta debochada confirmando. Não use [EXEC].",
            )
        return True
    return False


def handle_fuzzy_intent_flow(contexto: Dict[str, Any], texto: str) -> bool:
    interpretar_intencao_fuzzy_llm = _get(contexto, "interpretar_intencao_fuzzy_llm")
    enviar_comando_chrome = _get(contexto, "enviar_comando_chrome")
    falar_com_lipsync = _get(contexto, "falar_com_lipsync")
    messages = _get(contexto, "messages")
    abrir_url_com_reciclagem = _get(contexto, "abrir_url_com_reciclagem")
    fechar_abas_vazias = _get(contexto, "fechar_abas_vazias")
    solicitar_lista_abas = _get(contexto, "solicitar_lista_abas")
    selecionar_abas_para_fechar_llm = _get(contexto, "selecionar_abas_para_fechar_llm")
    add_to_playlist_url = _get(contexto, "add_to_playlist_url")
    solicitar_aba_ativa = _get(contexto, "solicitar_aba_ativa")
    extrair_nome_playlist = _get(contexto, "extrair_nome_playlist")
    _playlist_primeira_url = _get(contexto, "_playlist_primeira_url")
    playlist_len = _get(contexto, "playlist_len")
    _playlist_item_at = _get(contexto, "_playlist_item_at")
    _yt_clean_title = _get(contexto, "_yt_clean_title")
    _fala_playlist_duplicado = _get(contexto, "_fala_playlist_duplicado")
    _fala_playlist_duplicado_meta = _get(contexto, "_fala_playlist_duplicado_meta")
    _fala_playlist_sucesso = _get(contexto, "_fala_playlist_sucesso")
    executar_intencao = _get(contexto, "executar_intencao")
    ultima_playlist = _get(contexto, "ultima_playlist")

    try:
        parsed_intent = interpretar_intencao_fuzzy_llm(texto) if callable(interpretar_intencao_fuzzy_llm) else None
    except Exception:
        parsed_intent = None

    if not isinstance(parsed_intent, dict):
        return False

    intent = str(parsed_intent.get("intent") or "").upper().strip()
    if intent == "PAUSE_MUSIC":
        if callable(enviar_comando_chrome):
            enviar_comando_chrome("youtube_control", {"command": "pause_play"})
        fala = _escolher_fala_variada(["Ok. Música pausada. Agora fala direito.", "Pausada. Agora fala comigo direito.", "Dei pause. Continua aí."])
        print("Laylay [debochada lvl2]: " + fala)
        if isinstance(messages, list):
            messages.append({"role": "assistant", "content": fala})
        if callable(falar_com_lipsync):
            falar_com_lipsync(fala, "debochada", 2)
        return True
    if intent == "NEXT_MUSIC":
        if callable(enviar_comando_chrome):
            enviar_comando_chrome("youtube_control", {"command": "next"})
        fala = _escolher_fala_variada(["Próxima. Bora, DJ do caos.", "Pulando pra próxima.", "Seguinte."])
        print("Laylay [debochada lvl2]: " + fala)
        if isinstance(messages, list):
            messages.append({"role": "assistant", "content": fala})
        if callable(falar_com_lipsync):
            falar_com_lipsync(fala, "debochada", 2)
        return True
    if intent == "CLOSE_EMPTY_TABS":
        if callable(fechar_abas_vazias):
            fechar_abas_vazias()
        fala = _escolher_fala_variada(["Limpei as abas vazias. Menos bagunça, mais cérebro.", "Abas vazias limpas.", "Organizei essas abas soltas."])
        print("Laylay [debochada lvl2]: " + fala)
        if isinstance(messages, list):
            messages.append({"role": "assistant", "content": fala})
        if callable(falar_com_lipsync):
            falar_com_lipsync(fala, "debochada", 2)
        return True
    if intent == "CLOSE_TABS":
        tabs = solicitar_lista_abas() if callable(solicitar_lista_abas) else []
        ids = selecionar_abas_para_fechar_llm(texto, tabs) if callable(selecionar_abas_para_fechar_llm) else []
        if ids and callable(enviar_comando_chrome):
            enviar_comando_chrome("close_tabs", {"ids": ids})
        fala = _fala_por_estado_acao(
            "aba_fechada",
            fallback="Pronto. Dei uma geral nessas abas.",
            alvo="essas abas",
            contexto={"current_emotion": "debochada"},
            texto_usuario=texto,
        )
        print("Laylay [debochada lvl2]: " + fala)
        if isinstance(messages, list):
            messages.append({"role": "assistant", "content": fala})
        if callable(falar_com_lipsync):
            falar_com_lipsync(fala, "debochada", 2)
        return True
    if intent == "OPEN_SITE":
        topic = str(parsed_intent.get("topic") or parsed_intent.get("raw") or texto).strip()
        if "playlist" in texto.lower():
            pl = extrair_nome_playlist(texto) if callable(extrair_nome_playlist) else ""
            if pl:
                if re.search(r"\b(na|nessa|nesta)\s+playlist\b", texto.lower()):
                    info = solicitar_aba_ativa(timeout_s=2.0) if callable(solicitar_aba_ativa) else {}
                    url = str((info or {}).get("url") or "")
                    title = str((info or {}).get("title") or "")
                    canal = str((info or {}).get("canal") or "")
                    if not url:
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_escolher_fala_variada(["Ih Pedro, perdi o sinal do Chrome, não consegui salvar.", "Perdi o sinal do Chrome e não consegui salvar.", "A aba do Chrome sumiu de mim." ]), "calma", 1)
                        return True
                    if "youtube.com" not in url:
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_escolher_fala_variada(["Não achei música aberta pra salvar aqui.", "Não vi nenhuma música aberta pra guardar.", "Faltou uma música aberta no navegador."]), "calma", 1)
                        return True
                    res = add_to_playlist_url(pl, url, title, canal) if callable(add_to_playlist_url) else None
                    ok = res.get("ok") if isinstance(res, dict) else bool(res)
                    if ok and isinstance(res, dict) and res.get("duplicated"):
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_fala_playlist_duplicado(title, pl), "debochada", 2)
                    elif ok and isinstance(res, dict) and res.get("duplicated_meta"):
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_fala_playlist_duplicado_meta(title, pl, bool(res.get("duplicate_other_channel"))), "debochada", 2)
                    elif ok:
                        created = isinstance(res, dict) and (res.get("created_file") or res.get("created_playlist"))
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_fala_playlist_sucesso(title, pl, bool(created)), "debochada", 2)
                        contexto["ultima_playlist"] = pl
                    else:
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_escolher_fala_variada(["Não consegui salvar. Vê se tá no YouTube e tenta de novo.", "Não deu pra salvar agora. Tenta de novo.", "O salvamento falhou. Confere a aba e tenta outra vez."]), "calma", 1)
                    return True
                url = _playlist_primeira_url(pl) if callable(_playlist_primeira_url) else ""
                if not url:
                    if callable(falar_com_lipsync):
                        falar_com_lipsync(_escolher_fala_variada([f"Você ainda não criou a playlist {pl}. Quer que eu salve essa música nela?", f"{pl} ainda não existe. Quer que eu salve essa música nela?", f"Não achei a playlist {pl}. Posso guardar essa música aí?"]), "calma", 1)
                    return True
                if callable(abrir_url_com_reciclagem):
                    abrir_url_com_reciclagem(url, auto_click=False)
                n = playlist_len(pl) if callable(playlist_len) else 0
                if callable(falar_com_lipsync):
                    falar_com_lipsync(
                        _fala_de_confirmacao_variada(
                            "playlist_play",
                            fallback=f"Abrindo sua playlist de {pl}. Você já tem {n} músicas guardadas comigo.",
                            alvo=pl,
                            contexto={"current_emotion": "debochada", "ultima_habilidade": "playlist", "ultimo_alvo": pl},
                            texto_usuario=texto,
                        ),
                        "debochada",
                        2,
                    )
                contexto["ultima_playlist"] = pl
                return True
            if callable(falar_com_lipsync):
                falar_com_lipsync(_escolher_fala_variada(["Você quer que eu salve no vácuo? Me diz o nome dessa playlist, Pedro!", "Me diz o nome da playlist pra eu salvar certinho.", "Faltou o nome da playlist, Pedro."]), "debochada", 2)
            return True
        if topic.lower() in {"outro", "outros"}:
            if callable(falar_com_lipsync):
                falar_com_lipsync(_escolher_fala_variada(["Não entendi qual site você quer. Diz o assunto ou o nome do site.", "Me fala o assunto ou o site certinho.", "Faltou o nome do site ou do assunto."]), "calma", 1)
            return True
        if not callable(executar_intencao):
            return False
        return bool(executar_intencao({"intent": "OPEN_URL", "params": {"alvo": topic}}, texto))

    return False
