"""Geracao contextual da fala de abertura do modo chat."""

from __future__ import annotations

import re
import random
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict
from mente_laylay.memoria_mental.identidade_usuario import contexto_identidade_usuario
from mente_laylay.percepcao.ritmo_circadiano import construir_contexto_temporal


def abertura_soa_natural(texto: str) -> bool:
    """Rejeita construções traduzidas ou com tom de atendente virtual."""
    fala = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
    padroes_artificiais = (
        r"\bcomo\b.{0,45}\bsendo\s+(?:pra|para)\s+(?:voce|você)\b",
        r"\bcomo\s+(?:esta|está)\b.{0,35}\bsendo\b",
        r"\bcomo\s+posso\s+(?:te\s+)?ajudar\b",
        r"\bem\s+que\s+posso\s+(?:te\s+)?ajudar\b",
        r"\bpront[ao]\s+para\s+(?:te\s+)?ajudar\b",
    )
    return bool(fala) and not any(re.search(padrao, fala) for padrao in padroes_artificiais)


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
        self._aberturas_recentes: deque[str] = deque(maxlen=8)

    def _fallback_variado(self, tipo: str) -> str:
        temporal = construir_contexto_temporal(datetime.now())
        periodo = str(temporal.get("periodo") or "").replace("manha", "manhã")
        bases = {
            "inicio": [
                "Oi. Acordei por aqui; o que temos para hoje?",
                "Ei. Tudo ligado e a cabeça no lugar.",
                "Oi. Tô por aqui, curiosa pra saber qual é a de hoje.",
                "Olá. Pode trazer ideia, pergunta ou bagunça.",
                {
                    "madrugada": "Oi. A madrugada está quieta e eu já estou por aqui.",
                    "manhã": "Bom dia. Já estou por aqui.",
                    "tarde": "Boa tarde. Já estou por aqui.",
                    "noite": "Boa noite. Já estou por aqui.",
                }[periodo],
                "Ei, cheguei quietinha, mas já estou prestando atenção.",
                "Oi. Sistema em pé e conversa à vontade.",
                "Olá. Hoje eu prometo pensar antes de puxar contexto antigo.",
            ],
            "chat": [
                "Agora sim, pode falar comigo sem pressa.",
                "Tô te ouvindo. Manda do seu jeito.",
                "Conversa aberta. O que está passando pela sua cabeça?",
                "Chega mais, eu tô aqui.",
                "Pode falar. Hoje eu sigo o seu fio.",
                "Pronto, atenção toda sua agora.",
            ],
        }
        opcoes = [
            fala for fala in bases.get(tipo, bases["chat"])
            if fala.casefold() not in self._aberturas_recentes
        ]
        fala = random.choice(opcoes or bases.get(tipo, bases["chat"]))
        self._aberturas_recentes.append(fala.casefold())
        return fala

    def gerar_local(self, tipo: str = "chat") -> str:
        """Cria uma abertura imediata sem disputar a LLM com o usuário."""
        tipo = "inicio" if str(tipo).lower() == "inicio" else "chat"
        return self._fallback_variado(tipo)

    def gerar(self, tipo: str = "chat") -> str:
        tipo = "inicio" if str(tipo).lower() == "inicio" else "chat"
        fallback = self._fallback_variado(tipo)
        try:
            temporal = construir_contexto_temporal(datetime.now())
            estado = self.estado_getter() or {}
            mensagens = estado.get("messages") or []
            # A abertura inicia um encontro novo; não deve dramatizar uma
            # emoção tímida ou irritada que sobrou da conversa anterior.
            emocao = "calma" if tipo == "inicio" else str(estado.get("current_emotion") or "calma")
            nivel = 1 if tipo == "inicio" else estado.get("emotion_level", 1)
            contexto_recente = []
            # O início do programa é uma sessão nova. Histórico persistido
            # continua disponível como memória, mas não como turno em aberto.
            if tipo != "inicio":
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
                    f"Você é a Laylay. Crie uma única frase curta de abertura para o {tipo} da interação. "
                    "A frase deve soar natural, variar com o contexto recente e manter o jeitinho da Laylay. "
                    "Escreva em português brasileiro espontâneo, como uma amiga falando. "
                    "Evite construções traduzidas como 'como está a noite sendo para você'; "
                    "prefira formas diretas como 'como tá sua noite?' ou 'como foi seu dia?'. "
                    "Não diga que está em modo chat de forma mecânica. Não use listas nem markdown. "
                    "Nunca mencione empresas, nuvens, modelos, plataformas ou frases de assistente corporativa. "
                    "Não diga que o usuário pediu sua presença ou ativação; apenas chegue naturalmente. "
                    "Não continue receita, tutorial, resumo, tarefa, pergunta ou assunto anterior. "
                    "A abertura deve funcionar mesmo sem nenhum contexto de conversa. "
                    f"{contexto_identidade_usuario(estado.get('nome_usuario', ''))} "
                    f"Agora são {temporal.get('hora')}, período={temporal.get('periodo')}, "
                    f"fase={temporal.get('fase')}; use um tom {temporal.get('tom_comunicacao')}. "
                    "Comece com um cumprimento simples. Não invente que viu o usuário, que ele olhou para você, "
                    "que chamou você ou que seu corpo ficou vermelho, quente ou tímido. "
                    f"Não repita nenhuma destas aberturas recentes: {list(self._aberturas_recentes)}"
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
            implicacoes_falsas = (
                "ja que voce pediu", "já que você pediu", "como voce pediu", "como você pediu",
                "porque voce pediu", "porque você pediu",
            )
            reacoes_fisicas_inventadas = (
                "me olhou", "você me olhou", "voce me olhou", "me viu", "você me viu", "voce me viu",
                "me chamou assim", "nariz quente", "tô vermelha", "to vermelha", "fiquei vermelha",
                "tô corada", "to corada", "fiquei tímida", "fiquei timida",
            )
            continuacoes_de_tarefa = (
                "vou te passar", "vou continuar", "vamos continuar", "retomar",
                "receita", "ingredientes", "medidas", "resumo", "tutorial",
                "primeiro passo", "você vai precisar", "voce vai precisar",
            )
            cumprimentos = ("oi", "olá", "ola", "ei", "opa", "bom dia", "boa tarde", "boa noite", "boa madrugada")
            fala_norm = fala.casefold()
            if (
                len(fala) >= 4
                and fala_norm not in self._aberturas_recentes
                and fala_norm.startswith(cumprimentos)
                and abertura_soa_natural(fala)
                and not any(trecho in fala_norm for trecho in implicacoes_falsas)
                and not any(trecho in fala_norm for trecho in reacoes_fisicas_inventadas)
                and not any(trecho in fala_norm for trecho in continuacoes_de_tarefa)
            ):
                self._aberturas_recentes.append(fala.casefold())
                return fala
            return fallback
        except Exception as erro:
            self.log(f"⚠️ [CHAT] Falha ao gerar abertura dinâmica: {erro}")
            return fallback


def criar_abertura_chat_runtime(**kwargs: Any) -> AberturaChatRuntime:
    return AberturaChatRuntime(**kwargs)
