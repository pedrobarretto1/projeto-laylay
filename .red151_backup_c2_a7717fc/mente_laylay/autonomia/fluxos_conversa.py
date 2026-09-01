"""Fluxos de conversa e fallback da Laylay."""

from __future__ import annotations

import re
import time
from typing import Any, Dict
from mente_laylay.personalidade.falas_variadas import escolher as _escolher_fala_variada
from mente_laylay.personalidade.proporcao_resposta import (
    parece_pedido_reexplicacao,
    parece_problema_matematico,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def _parece_comando_novo(texto_norm: str) -> bool:
    """Nao deixa uma sugestao pendente engolir um comando novo completo."""
    t = re.sub(r"\s+", " ", str(texto_norm or "").strip().lower())
    if not t:
        return False
    if re.search(r"\b(?:melhor|prefiro|preferia|em vez|ao inves|ao invés|apenas|somente|só|so)\b", t):
        # Com uma sugestão pendente, esses marcadores indicam refino da ideia,
        # não um comando solto que deva ignorar o contexto.
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
    texto_depende_de_contexto=None,
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

    # Fórmulas são visualmente curtas, mas precisam do prompt completo e de
    # mais espaço de geração para desenvolver a conta até a conclusão.
    if parece_problema_matematico(texto):
        return False
    if parece_pedido_reexplicacao(texto):
        return False
    # A decisão semântica central também cobre pronomes, reparos e perguntas
    # elípticas. Nenhuma continuação dependente do turno anterior deve perder
    # o histórico só por possuir poucas palavras.
    if callable(texto_depende_de_contexto):
        try:
            if texto_depende_de_contexto(texto):
                return False
        except Exception:
            pass

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
        "código", "codigo", "habilidade", "computador", "pc", "sistema",
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
    negacao_generica = t in {
        "nao", "não", "agora nao", "agora não", "nao precisa", "não precisa",
        "deixa", "deixa quieto", "esquece", "melhor nao", "melhor não",
    }
    resposta_explicita = confirmacao_generica or negacao_generica

    if alvo_norm and alvo_norm in t:
        return True

    if tipo == "email":
        if pistas_musica or (pistas_app and not pistas_email):
            return False
        if pistas_email:
            return True
        if confirmacao_generica and foco and foco_tipo not in {"email", "conversa", "pesquisa"} and "email" not in foco_texto:
            return False
        return resposta_explicita

    if tipo == "playlist":
        if pistas_email or (pistas_app and not pistas_musica):
            return False
        if pistas_musica:
            return True
        if confirmacao_generica and foco and foco_tipo not in {"playlist", "musica", "música", "midia", "conversa"}:
            return False
        return resposta_explicita

    if tipo == "rotina":
        if pistas_email or pistas_musica:
            return False
        if pistas_app:
            return True
        if confirmacao_generica and foco and foco_tipo not in {"janela", "site", "conversa"}:
            return False
        return resposta_explicita

    return False


def handle_feedback_pendente(contexto: Dict[str, Any], texto: str) -> bool:
    """Trata respostas a sugestões proativas antes de cair na conversa normal."""
    texto_norm = re.sub(r"\s+", " ", str(texto or "").strip().lower())
    registrar_feedback_proatividade = _get(contexto, "_registrar_feedback_proatividade")
    registrar_feedback_aprendizado = _get(contexto, "_registrar_feedback_aprendizado")
    classificar_confirmacao_contextual = _get(contexto, "_classificar_confirmacao_contextual")
    classificar_confirmacao_local = _get(contexto, "_classificar_confirmacao_local")

    def _feedback_contextual(tipo: str, aceito=None, resultado: str = "") -> None:
        if callable(registrar_feedback_proatividade):
            try:
                registrar_feedback_proatividade(tipo, aceito, resultado=resultado)
            except Exception:
                pass
        if callable(registrar_feedback_aprendizado):
            try:
                registrar_feedback_aprendizado(
                    tipo=resultado or "feedback",
                    aceito=aceito,
                    resultado=resultado,
                    origem=tipo,
                    confianca=1.0 if aceito is not None else 0.6,
                )
            except Exception:
                pass

    agora = time.time()
    timeout_s = 600.0

    # Um novo comando nunca vira uma resposta forçada à sugestão anterior.
    # Antes de liberá-lo, porém, consolidamos como silêncio somente as ofertas
    # que ficaram dez minutos completos sem retorno.
    for chave, categoria, rotulo in (
        ("_email_sugestao_pendente", "emails", "EMAIL"),
        ("_playlist_sugestao_pendente", "musica", "PLAYLIST"),
        ("_rotina_sugestao_pendente", "rotina", "ROTINA"),
    ):
        pendencia = _get(contexto, chave)
        if not isinstance(pendencia, dict):
            continue
        try:
            idade = agora - float(pendencia.get("ts", 0.0) or 0.0)
        except (TypeError, ValueError):
            idade = timeout_s
        if idade >= timeout_s:
            print(f"[FEEDBACK {rotulo}] Sugestao expirou sem resposta apos 10 minutos.")
            _feedback_contextual(categoria, None, "silencio")
            contexto[chave] = None

    if _parece_comando_novo(texto_norm):
        return False
    if callable(classificar_confirmacao_local) and classificar_confirmacao_local(texto) is False:
        categorias_canceladas = []
        for chave, categoria in (
            ("_rotina_sugestao_pendente", "rotina"),
            ("_playlist_sugestao_pendente", "musica"),
            ("_email_sugestao_pendente", "emails"),
        ):
            if _get(contexto, chave) is not None:
                categorias_canceladas.append(categoria)
            contexto[chave] = None
        for categoria in categorias_canceladas:
            _feedback_contextual(categoria, False, "recusa")
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
    handle_sugestao_confirmacao = _get(contexto, "_handle_sugestao_confirmacao")
    musica_operacoes = _get(contexto, "_registro_musica_operacoes_runtime")
    extrair_nome_playlist = _get(contexto, "extrair_nome_playlist")
    yt_clean_title = _get(contexto, "_yt_clean_title")
    falar_com_lipsync = _get(contexto, "falar_com_lipsync")
    registrar_feedback_rotina = _get(contexto, "_rotina_registrar_feedback")
    gmail_buscar = _get(contexto, "_gmail_buscar_nao_lidos")
    gmail_resumo = _get(contexto, "_gmail_falar_resumo_estiloso")

    if email_sugestao_pendente is not None:
        if agora - float(email_sugestao_pendente.get("ts", 0.0)) >= timeout_s:
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
                    _feedback_contextual(
                        "emails", bool(confirmado), "aceita" if confirmado else "recusa",
                    )
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
        if agora - float(playlist_sugestao_pendente.get("ts", 0.0)) >= timeout_s:
            contexto["_playlist_sugestao_pendente"] = None
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
                _feedback_contextual(
                    "musica", bool(confirmado), "aceita" if confirmado else "recusa",
                )
                status = "SIM" if confirmado else "NAO"
                print(f"[FEEDBACK PLAYLIST] Resposta: {status} para '{pl}'")
                if confirmado:
                    ok = False
                    info = musica_operacoes.faixa_atual() if musica_operacoes is not None else {}
                    url = str((info or {}).get("url") or "")
                    title = str((info or {}).get("title") or "")
                    canal = str((info or {}).get("canal") or "")
                    if not url or "youtube.com" not in url:
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(_escolher_fala_variada(["Não achei a música aberta pra salvar agora.", "Não vi música aberta pra guardar.", "Faltou uma aba de música aberta."]), "calma", 1)
                    else:
                        ok = bool(
                            musica_operacoes.adicionar_faixa(pl, url, title, canal)
                        ) if musica_operacoes is not None else False
                    if ok:
                        musica_operacoes.definir_ultima_playlist(pl)
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
                            falar_com_lipsync(_escolher_fala_variada([
                                "Não consegui salvar essa música agora.",
                                "O salvamento falhou por enquanto.",
                                "Não deu pra guardar a música agora.",
                            ]), "calma", 1)
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
        if agora - float(rotina_sugestao_pendente.get("ts", 0.0)) >= timeout_s:
            contexto["_rotina_sugestao_pendente"] = None
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
                _feedback_contextual(
                    "rotina", bool(confirmado), "aceita" if confirmado else "recusa",
                )
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
