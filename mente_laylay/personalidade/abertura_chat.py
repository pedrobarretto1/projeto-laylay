"""Geracao contextual da fala de abertura do modo chat."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict


class AberturaChatRuntime:
    def __init__(
        self,
        *,
        estado_getter: Callable[[], Dict[str, Any]],
        enviar_mensagem: Callable[..., Any],
        limpar_resposta: Callable[[Any], str],
        remover_prefixo_exec: Callable[[str], str],
        log: Callable[..., Any] = print,
    ) -> None:
        self.estado_getter = estado_getter
        self.enviar_mensagem = enviar_mensagem
        self.limpar_resposta = limpar_resposta
        self.remover_prefixo_exec = remover_prefixo_exec
        self.log = log

    def gerar(self) -> str:
        fallback = "Modo chat ativado. Agora eu fico no papo e largo os comandos por um instante."
        try:
            estado = self.estado_getter() or {}
            mensagens = estado.get("messages") or []
            emocao = str(estado.get("current_emotion") or "calma")
            nivel = estado.get("emotion_level", 1)
            contexto_recente = []
            for mensagem in list(mensagens)[-6:]:
                if not isinstance(mensagem, dict):
                    continue
                if str(mensagem.get("role") or "").lower() not in {"user", "assistant"}:
                    continue
                texto = str(mensagem.get("content") or "").strip()
                if texto:
                    contexto_recente.append({
                        "role": str(mensagem.get("role") or "user"),
                        "content": texto[:240],
                    })

            prompt = [{
                "role": "system",
                "content": (
                    "Você é a Laylay. Crie uma única frase curta de abertura para quando o modo chat for ativado. "
                    "A frase deve soar natural, variar com o contexto recente e manter o jeitinho da Laylay. "
                    "Não diga que está em modo chat de forma mecânica. Não use listas nem markdown. "
                    "Nunca mencione empresas, nuvens, modelos, plataformas ou frases de assistente corporativa."
                ),
            }]
            prompt.extend(contexto_recente)
            prompt.append({
                "role": "user",
                "content": f"Crie a abertura do chat agora, em até 18 palavras, com emoção={emocao} e nível={nivel}.",
            })
            bruto = self.enviar_mensagem(prompt, _com_tools=False, max_tokens=80, modo_rapido=True)
            fala = self.remover_prefixo_exec(self.limpar_resposta(bruto)).strip()
            fala = re.sub(r"\s+", " ", fala).strip(" \"'`")
            return fala if len(fala) >= 4 else fallback
        except Exception as erro:
            self.log(f"⚠️ [CHAT] Falha ao gerar abertura dinâmica: {erro}")
            return fallback


def criar_abertura_chat_runtime(**kwargs: Any) -> AberturaChatRuntime:
    return AberturaChatRuntime(**kwargs)
