"""Processamento de mensagens vindas do PC B."""

from __future__ import annotations

import threading
from typing import Any, Dict


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


def processar_mensagem_pc_b(data: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    tipo = data.get("type")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")

    if tipo == "pc_b_screenshot":
        analisar_com_groq = _get(ctx, "_analisar_com_groq")
        registrar_memoria_visual = _get(ctx, "registrar_memoria_visual")
        current_emotion = _get(ctx, "current_emotion", "calma")
        emotion_level = int(_get(ctx, "emotion_level", 1) or 1)

        img_b64 = data.get("imagem_b64", "")
        pergunta = data.get("pergunta", "O que está acontecendo nessa tela?")
        print(f"[VISÃO] Screenshot do PC B recebido ({len(img_b64)//1024}KB). Analisando...")

        def _analisar_screenshot_pcb(b64: str, p: str) -> None:
            descricao = analisar_com_groq(b64, p) if callable(analisar_com_groq) else ""
            print(f"[VISÃO] Groq sobre PC B: {str(descricao)[:200]}")
            try:
                if callable(registrar_memoria_visual):
                    registrar_memoria_visual(
                        b64,
                        descricao,
                        motivo="captura visual do PC B",
                        contexto={"pc": "pc_b", "pergunta": p},
                        emocao=current_emotion or "calma",
                        intensidade=emotion_level,
                        tags=["pc_b", "visao", "captura"],
                        origem="pc_b",
                    )
            except Exception as e_mem:
                print(f"⚠️ [VISÃO] Falha ao registrar memória visual do PC B: {e_mem}")
            if callable(falar_com_lipsync) and descricao:
                falar_com_lipsync(str(descricao)[:300], current_emotion, emotion_level)

        threading.Thread(target=_analisar_screenshot_pcb, args=(img_b64, pergunta), daemon=True).start()
        return True

    if tipo == "pc_b_status":
        if data.get("status") == "error":
            erro_msg = data.get("error", "Erro desconhecido")
            app_err = data.get("app", "")
            acao_err = data.get("action", "")
            print(f"❌ [PC B] Falha remota: {erro_msg}")

            messages = _get(ctx, "messages")
            enviar_mensagem = _get(ctx, "enviar_mensagem")
            limpar_resposta_da_ia = _get(ctx, "limpar_resposta_da_ia")

            def _notificar_erro() -> None:
                informacao = (
                    f"System: IMPORTANTE! O Computador B falhou ao tentar realizar a ação '{acao_err}' no alvo '{app_err}'. "
                    f"O Windows lá retornou o erro: '{erro_msg}'. "
                    "Isso é uma falha de sistema, VOCÊ DEVE avisar o usuário sobre isso AGORA mesmo para que ele saiba que não funcionou."
                )
                if isinstance(messages, list):
                    messages.append({"role": "system", "content": informacao})
                try:
                    bot_raw = enviar_mensagem(messages) if callable(enviar_mensagem) else ""
                    fala, _ = limpar_resposta_da_ia(bot_raw) if callable(limpar_resposta_da_ia) else (str(bot_raw or ""), [])
                    if fala:
                        print(f"Laylay [Autocorreção PC B]: {fala}")
                        if isinstance(messages, list):
                            messages.append({"role": "assistant", "content": fala})
                        if callable(falar_com_lipsync):
                            falar_com_lipsync(fala, "decepcionada", 2)
                except Exception as e_ia:
                    print(f"[PC B] Erro na autocorreção remota da IA: {e_ia}")

            threading.Thread(target=_notificar_erro, daemon=True).start()
        else:
            print(f"✅ [PC B] Ação {data.get('action')} em {data.get('app', '')} concluída com sucesso!")
        return True

    print(f"[PC B] Mensagem recebida: {data.get('message', data.get('type', data))}")
    return True
