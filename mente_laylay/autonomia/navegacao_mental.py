"""Fluxos de navegacao, abas, imagem e midia da Laylay."""

from __future__ import annotations

import random
import re
from typing import Any, Dict, Optional

from mente_laylay.personalidade.falas_variadas import fala_de_confirmacao as _fala_de_confirmacao_variada


def handle_open_app_flow(contexto: Dict[str, Any], texto: str, lower_text: str) -> bool:
    extrair_intencao_abrir_app = contexto.get("extrair_intencao_abrir_app")
    executar_intencao = contexto.get("executar_intencao")
    if not callable(extrair_intencao_abrir_app) or not callable(executar_intencao):
        return False
    intent = extrair_intencao_abrir_app(texto)
    if not intent:
        return False
    return bool(executar_intencao(intent, texto))


def handle_youtube_volume_flow(contexto: Dict[str, Any], lower_text: str) -> bool:
    falar = contexto.get("falar_com_lipsync")
    ajustar_volume = contexto.get("ajustar_volume_sistema")
    ajustar_volume_rel = contexto.get("ajustar_volume_sistema_relativo")
    current_emotion = contexto.get("current_emotion", "calma")
    emotion_level = contexto.get("emotion_level", 1)
    ultima_habilidade = contexto.get("ultima_habilidade", "")
    ultimo_alvo = contexto.get("ultimo_alvo", "")
    t = re.sub(r"\s+", " ", (lower_text or "").strip().lower())
    if not t or not callable(falar) or not callable(ajustar_volume) or not callable(ajustar_volume_rel):
        return False

    def _ctx_fala() -> Dict[str, Any]:
        return {
            "current_emotion": current_emotion,
            "ultima_habilidade": ultima_habilidade,
            "ultimo_alvo": ultimo_alvo,
        }

    def _falar_confirmacao(chave: str, fallback: str, emocao: str = "calma", nivel: int = 1) -> None:
        falar(
            _fala_de_confirmacao_variada(
                chave,
                fallback=fallback,
                contexto=_ctx_fala(),
                texto_usuario=t,
            ),
            emocao,
            nivel,
        )

    mute_triggers = ["mudo", "mute", "silêncio", "silencio", "sem som", "silenciar"]
    up_triggers = ["aumenta", "aumentar", "sobe", "subir", "mais alto", "aumente", "aumenta o volume", "sobe o volume"]
    down_triggers = ["baixa", "abaixa", "baixar", "diminui", "diminuir", "reduz", "reduzir", "mais baixo", "baixin", "baixe o volume"]
    max_triggers = ["no talo", "no máximo", "no maximo", "máximo", "maximo", "100%", "volume máximo", "volume maximo"]
    low_triggers = ["baixinho", "bem baixo", "volume 2", "volume dois", "20%", "0.2", "volume baixo"]
    up_only = {"aumenta", "aumentar", "aumente", "sobe", "subir", "mais alto"}
    down_only = {"baixa", "abaixa", "baixar", "diminui", "diminuir", "reduz", "reduzir", "mais baixo"}

    if any(x in t for x in mute_triggers):
        ajustar_volume(0)
        _falar_confirmacao("volume_mute", "Mudo ligado.", "calma", 1)
        return True
    if any(x in t for x in max_triggers):
        ajustar_volume(100)
        falar(random.choice(["Volume no máximo. Agora você vai ouvir tudo.", "Dei o talo no som.", "Som no auge."]), "debochada", 2)
        return True
    if any(x in t for x in low_triggers):
        ajustar_volume(20)
        falar(random.choice(["Volume baixinho, com jeitinho.", "Deixei o som mais discreto.", "Baixei numa boa."]), "calma", 1)
        return True
    if t in up_only:
        ajustar_volume_rel(10)
        _falar_confirmacao("volume_up", "Aumentei o volume.", "debochada", 2)
        return True
    if t in down_only:
        ajustar_volume_rel(-10)
        _falar_confirmacao("volume_down", "Baixei o volume.", "calma", 1)
        return True

    m_pct = re.search(r"\bvolume\s*(\d{1,3})\s*(%?)\b", t)
    if m_pct:
        try:
            n = int(m_pct.group(1))
        except Exception:
            n = -1
        has_pct = str(m_pct.group(2) or "") == "%"
        if 0 <= n <= 100:
            v = n if has_pct or n > 10 else n * 10
            ajustar_volume(int(v))
            _falar_confirmacao("volume_set", "Volume ajustado.", "calma", 1)
            return True
    if any(x in t for x in up_triggers):
        ajustar_volume_rel(10)
        _falar_confirmacao("volume_up", "Aumentei o volume.", "calma", 1)
        return True
    if any(x in t for x in down_triggers):
        ajustar_volume_rel(-10)
        _falar_confirmacao("volume_down", "Baixei o volume.", "debochada", 2)
        return True
    return False


def handle_pause_next_flow(contexto: Dict[str, Any], texto: str, lower_text: str) -> bool:
    enviar_comando_chrome = contexto.get("enviar_comando_chrome")
    confirmar_execucao = contexto.get("_confirmar_execucao_debochada")
    comando_sugerido = contexto.get("comando_sugerido")
    if not callable(enviar_comando_chrome) or not callable(confirmar_execucao):
        return False

    if any(k in lower_text for k in ["pausa", "pause", "para "]):
        enviar_comando_chrome("youtube_control", {"command": "pause_play"})
        contexto["comando_sugerido"] = None
        contexto["comando_sugerido_payload"] = None
        contexto["comando_sugerido_estado"] = "NONE"
        contexto["comando_sugerido_ts"] = 0.0
        confirmar_execucao(texto, "O comando de pausa já foi executado pelo Python imediatamente. Responda com uma frase curta, natural e variada, no jeitinho da Laylay. Não use [EXEC].")
        return True

    if ("playlist" not in lower_text) and any(k in lower_text for k in ["próxima", "proxima", "pula", "próximo", "proximo"]):
        enviar_comando_chrome("youtube_control", {"command": "next"})
        contexto["comando_sugerido"] = None
        contexto["comando_sugerido_payload"] = None
        contexto["comando_sugerido_estado"] = "NONE"
        contexto["comando_sugerido_ts"] = 0.0
        confirmar_execucao(texto, "O comando de próxima já foi executado pelo Python imediatamente. Responda com uma frase curta, natural e variada, no jeitinho da Laylay. Não use [EXEC].")
        return True

    if ("playlist" not in lower_text) and any(k in lower_text for k in ["volta", "anterior", "música anterior", "musica anterior"]):
        enviar_comando_chrome("youtube_control", {"command": "prev"})
        contexto["comando_sugerido"] = None
        contexto["comando_sugerido_payload"] = None
        contexto["comando_sugerido_estado"] = "NONE"
        contexto["comando_sugerido_ts"] = 0.0
        confirmar_execucao(texto, "O comando de música anterior já foi executado pelo Python imediatamente. Responda com uma frase curta, natural e variada, no jeitinho da Laylay. Não use [EXEC].")
        return True

    return False


def handle_close_tabs_flow(contexto: Dict[str, Any], texto: str, lower_text: str) -> bool:
    validar_e_enviar_comando = contexto.get("validar_e_enviar_comando")
    confirmar_execucao = contexto.get("_confirmar_execucao_debochada")
    if not callable(validar_e_enviar_comando) or not callable(confirmar_execucao):
        return False
    if not any(k in lower_text for k in ["fecha", "fechar", "mata", "derruba", "fecha essa aba", "fecha a aba"]):
        return False
    target = ""
    m = re.search(r"(?:fecha|fechar|mata|derruba)\s+(?:a|essa|o|esse)?\s*aba\s*(?:do|da|de|do site|do google)?\s*(.+)", lower_text, flags=re.IGNORECASE)
    if m:
        target = m.group(1).strip().strip(".,!?").strip()
    else:
        m2 = re.search(r"fecha\s+(?:a|essa)?\s*aba\s*(.+)", lower_text, flags=re.IGNORECASE)
        if m2:
            target = m2.group(1).strip().strip(".,!?").strip()
    if target and len(target) > 2:
        validar_e_enviar_comando("close_specific_tab", {"target": target})
        confirmar_execucao(texto, f"Fechando a aba '{target}'. Já vai tarde.")
        return True
    validar_e_enviar_comando("close_current_tab", {})
    confirmar_execucao(texto, "Fechado. Já vai tarde.")
    return True


def handle_site_flow(contexto: Dict[str, Any], texto: str, lower_text: str) -> bool:
    executar_comando = contexto.get("executar_comando")
    resetar_sugestao = contexto.get("_resetar_sugestao")
    confirmar_execucao = contexto.get("_confirmar_execucao_debochada")
    if not callable(executar_comando) or not callable(resetar_sugestao) or not callable(confirmar_execucao):
        return False
    if "site" in lower_text and any(k in lower_text for k in ["pet", "petz", "noticias", "notícia", "noticia", "tech", "tecnologia"]):
        assunto = ""
        for k in ["pet", "petz", "noticias", "notícia", "noticia", "tech", "tecnologia"]:
            if k in lower_text:
                assunto = k
                break
        if not assunto:
            assunto = lower_text
        executar_comando("OPEN_SITE", assunto)
        resetar_sugestao()
        confirmar_execucao(texto, "O site já foi aberto pelo Python imediatamente. Responda curto, debochada, confirmando. Não use [EXEC].")
        return True
    return False


def handle_image_flow(contexto: Dict[str, Any], texto: str, lower_text: str) -> bool:
    buscar_imagem_url = contexto.get("buscar_imagem_url")
    baixar_imagem_direto = contexto.get("baixar_imagem_direto")
    falar = contexto.get("falar_com_lipsync")
    messages = contexto.get("messages")
    webbrowser = contexto.get("webbrowser")
    if not callable(falar) or not callable(buscar_imagem_url) or not callable(baixar_imagem_direto):
        return False
    if "imagem" in lower_text and ("aba" in lower_text or "abre" in lower_text or "abra" in lower_text):
        m = re.search(r"imagem\s+de\s+(.+)$", texto.strip(), flags=re.IGNORECASE)
        assunto_img = (m.group(1).strip() if m else "").strip()
        if assunto_img:
            url_img = buscar_imagem_url(assunto_img)
            if url_img:
                try:
                    if webbrowser is not None:
                        webbrowser.open(url_img)
                except Exception:
                    pass
                fala = f"Aqui está o {assunto_img} que você pediu, Pedro. Ficou bonito na tela?"
                if isinstance(messages, list):
                    messages.append({"role": "assistant", "content": fala})
                falar(fala, "debochada", 2)
                return True
    if "baixa" in lower_text and "imagem" in lower_text:
        m = re.search(r"imagem\s+de\s+(.+)$", texto.strip(), flags=re.IGNORECASE)
        assunto_img = (m.group(1).strip() if m else "").strip()
        if assunto_img:
            destino = baixar_imagem_direto(assunto_img)
            if destino:
                fala = f"Já baixei {assunto_img} nos seus Downloads, Pedro. Tá pronto pro seu próximo meme."
                if isinstance(messages, list):
                    messages.append({"role": "assistant", "content": fala})
                falar(fala, "debochada", 2)
                return True
    return False


def handle_youtube_music_intents(contexto: Dict[str, Any], texto: str, lower_text: str) -> bool:
    enviar_comando_chrome = contexto.get("enviar_comando_chrome")
    falar = contexto.get("falar_com_lipsync")
    if not callable(enviar_comando_chrome) or not callable(falar):
        return False
    if re.match(r"^\s*(coloque|coloca|toca|ouvir)\b", lower_text) and "playlist" not in lower_text and "netflix" not in lower_text:
        q = re.sub(r"^\s*(coloque|coloca|toca|ouvir)\b", " ", lower_text).strip()
        q = re.sub(r"^(a|o|uma|um)\s+", "", q).strip()
        q = q.replace("música", " ").replace("musica", " ")
        q = re.sub(r"\s+", " ", q).strip()
        if q:
            enviar_comando_chrome("youtube_search", {"query": q})
            falar(f"Colocando {q}.", "debochada", 2)
            return True
    if ("música" in lower_text or "musica" in lower_text or "tim maia" in lower_text) and "playlist" not in lower_text and "netflix" not in lower_text:
        q = lower_text
        for k in ["música", "musica", "coloca", "coloque", "toca", "ouvir", "pra", "para"]:
            q = q.replace(k, " ")
        q = re.sub(r"\s+", " ", q).strip()
        if q:
            enviar_comando_chrome("youtube_search", {"query": q})
            falar(f"Colocando {q}.", "debochada", 2)
            return True
    return False
