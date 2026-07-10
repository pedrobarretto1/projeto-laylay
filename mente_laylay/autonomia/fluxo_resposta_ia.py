"""Fluxo principal de resposta da IA da Laylay."""

from __future__ import annotations

from typing import Any, Dict
from mente_laylay.autonomia.pre_fluxo_contextual import (
    executar_pipeline_pre_fluxo,
    processar_aprendizado_apelido,
    processar_bloqueio_playlist_temporario,
    processar_elogio_ou_agradecimento,
    processar_execucao_pratica_precoce,
    processar_feedback_pendente,
    processar_fluxo_musical_generico,
    processar_pergunta_aberta,
    processar_pergunta_curta_contextual,
    responder_conversa_social_curta,
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default

def processar_inicio_fluxo_resposta_ia(ctx: Dict[str, Any], texto: str) -> bool:
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    t = str(texto or "").strip()
    if not t:
        return True

    refinar_contexto_mental = _get(ctx, "_refinar_contexto_mental")
    if callable(refinar_contexto_mental):
        refinar_contexto_mental(t)

    def _log(etapa: str, detalhe: str = "") -> None:
        extra = f" | {detalhe}" if detalhe else ""
        print(f"🧭 [PRE-FLUXO] {etapa}{extra}")

    etapas = [
        lambda: processar_execucao_pratica_precoce(ctx, t),
        lambda: processar_elogio_ou_agradecimento(
            ctx, t, emocao=current_emotion or "calma", nivel=emotion_level or 1
        ),
        lambda: processar_bloqueio_playlist_temporario(ctx, t),
        lambda: processar_feedback_pendente(ctx, t),
        lambda: processar_fluxo_musical_generico(ctx, t),
        lambda: processar_pergunta_curta_contextual(ctx, t),
        lambda: processar_pergunta_aberta(
            ctx, t, emocao=current_emotion or "calma", nivel=emotion_level or 1
        ),
        lambda: responder_conversa_social_curta(
            ctx, t, emocao=current_emotion or "calma", nivel=emotion_level or 1
        ),
        lambda: processar_aprendizado_apelido(ctx, t),
    ]

    if executar_pipeline_pre_fluxo(ctx, t, etapas, log_cb=_log):
        return True

    _log("sem_vencedor_precoce", "segue para ia principal")
    print(f"🧠 [IA] Gerando resposta para: '{texto}'")
    return False


def processar_movimento_playlist_pre_ia(ctx: Dict[str, Any], texto: str) -> bool:
    detectar_movimento = _get(ctx, "_detectar_mover_playlist_texto")
    mover_item = _get(ctx, "_mover_item_playlist")
    falar = _get(ctx, "falar_com_lipsync")
    salvar_memoria = _get(ctx, "salvar_memoria")
    messages = _get(ctx, "messages")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    if not callable(detectar_movimento) or not callable(mover_item):
        return False

    try:
        movimento = detectar_movimento(texto)
        if not movimento:
            return False
        resultado = mover_item(
            movimento.get("origem", ""),
            movimento.get("destino", ""),
            movimento.get("musica", ""),
        )
        resultado = resultado if isinstance(resultado, dict) else {}
        if resultado.get("ok"):
            titulo = resultado.get("titulo") or "essa música"
            origem = resultado.get("origem") or movimento.get("origem", "")
            destino = resultado.get("destino") or movimento.get("destino", "")
            fala = f"Movi {titulo} da playlist {origem} pra {destino}."
            if resultado.get("duplicated"):
                fala = f"Tirei {titulo} da playlist {origem}; ela já estava em {destino}."
            print(f"🎵 [PLAYLIST] {fala}")
            if isinstance(messages, list):
                messages.append({"role": "user", "content": str(texto or "").strip()})
                messages.append({"role": "assistant", "content": fala})
            if callable(falar):
                falar(fala, current_emotion or "calma", emotion_level or 1)
            if callable(salvar_memoria):
                salvar_memoria()
            return True

        if resultado.get("error") == "source_empty":
            fala = (
                f"Não achei nada na playlist "
                f"{resultado.get('origem') or movimento.get('origem')} pra mover."
            )
        else:
            fala = "Não consegui entender de qual playlist pra qual playlist é essa mudança."
        print(f"❌ [PLAYLIST] Falha ao mover por texto: {resultado}")
        if callable(falar):
            falar(fala, "calma", 1)
        return True
    except Exception as erro:
        print(f"⚠️ [PLAYLIST] Falha no atalho de mover playlist: {erro}")
        return False


def processar_consulta_aprendizados_pre_ia(ctx: Dict[str, Any], texto: str) -> bool:
    recuperar_aprendizados = _get(ctx, "_recuperar_aprendizados")
    falar = _get(ctx, "falar_com_lipsync")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    entrada = str(texto or "")
    entrada_lower = entrada.lower()
    consultas = [
        "o que eu te ensinei",
        "o que eu te ensinei ontem",
        "o que você aprendeu",
        "o que aprendeu",
        "você lembra do que eu te falei",
        "você lembra do que eu te ensinei",
        "me lembra do que eu te ensinei",
    ]
    if not any(consulta in entrada_lower for consulta in consultas):
        return False
    if not callable(recuperar_aprendizados):
        return False

    try:
        aprendizados = recuperar_aprendizados(limit=3)
        if not aprendizados:
            return False
        ultimo = str(aprendizados[0]).strip()
        if len(ultimo) > 120:
            ultimo = ultimo[:117] + "..."
        resposta = f"Ah, lembrei. Você me ensinou isso: {ultimo}"
        if "responde" in ultimo.lower() or "de agora" in ultimo.lower():
            resposta = f"Ah, claro. Você me passou isso aqui: {ultimo}"
        if "de agora" in ultimo.lower():
            resposta = f"Ah, então é assim que você quer: {ultimo}"
        print(f"🧠 [MEMÓRIA] Resposta natural de aprendizado pronta: {resposta}")
        if callable(falar):
            falar(resposta, current_emotion or "calma", emotion_level or 1)
        return True
    except Exception as erro:
        print(f"⚠️ [MEMÓRIA] Não consegui recuperar aprendizados: {erro}")
        return False


def processar_pre_fluxos_antes_ia(ctx: Dict[str, Any], texto: str) -> bool:
    """Executa atalhos especializados que devem vencer antes da chamada ao LLM."""
    if processar_movimento_playlist_pre_ia(ctx, texto):
        return True
    return processar_consulta_aprendizados_pre_ia(ctx, texto)
