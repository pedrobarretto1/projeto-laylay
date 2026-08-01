"""Interpretação semântica em modo observador para cada turno da Laylay."""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
from typing import Any, Callable, Dict

from mente_laylay.integracao.registro_conversa_llm import resolver_enviador_modelo

from mente_laylay.cognicao.leitura_semantica_turno import (
    comparar_com_legado,
    normalizar_leitura_semantica,
)


PROMPT_LEITURA_SEMANTICA = """Você interpreta a fala inteira dirigida à assistente Laylay.
Descreva significado, papéis e relação com o contexto; não responda ao usuário e não execute nada.
Retorne somente JSON válido neste formato:
{
  "atos":[{"tipo":"...","falante":"pedro","destinatario":"...","conteudo":"...","tema":"...","entidades":[],"confianca":0.0}],
  "modalidade_geral":"conversa|pergunta|comando|misto|correcao|confirmacao|recusa|reacao|deliberacao|ambiguo",
  "ato_principal":"...",
  "tema_principal":"...",
  "entidades":[],
  "relacao_contextual":{"tipo":"independente|responde_fala_anterior|continua_assunto|muda_assunto|corrige_interpretacao|confirma_pendencia|recusa_pendencia|ambiguo","responde_fala_anterior":false,"inicia_assunto_novo":false,"referencia_pendencia":false},
  "operacional":{"pedido_real":false,"hipotetico":false,"negado":false,"requer_esclarecimento":false,"intent_candidato":"","acao":"","alvo":"","parametros":{},"confianca":0.0},
  "ambiguidades":[],"evidencias":[],"confianca":0.0
}
Tipos de ato permitidos: saudacao, pergunta, pergunta_opiniao, pergunta_capacidade,
resposta_social, relato, opiniao, reacao, agradecimento, correcao, recusa,
confirmacao, contraproposta, pedido_acao, sugestao, deliberacao, encerramento, outro.
Analise todos os atos, inclusive quando uma resposta social é seguida por outra pergunta.
Diferencie falar sobre uma ação, perguntar capacidade e pedir que ela seja executada.
Uma confirmação só se refere à pendência quando o contexto realmente mostrar uma pergunta ativa e falada.
Não transforme gosto, comentário, hipótese, exemplo ou menção de música em pedido para tocar.
Não invente fatos, entidades, alvos ou intenções. Em dúvida, registre a ambiguidade.
O campo operacional nunca representa autorização; ele apenas descreve o pedido percebido."""


MODOS_VALIDOS = {"off", "shadow", "main", "conversation", "hybrid", "full"}


def _extrair_json(texto: Any) -> Dict[str, Any]:
    bruto = str(texto or "").strip()
    if bruto.startswith("```"):
        bruto = re.sub(r"^```(?:json)?\s*", "", bruto, flags=re.IGNORECASE)
        bruto = re.sub(r"\s*```$", "", bruto).strip()
    inicio, fim = bruto.find("{"), bruto.rfind("}")
    if inicio < 0 or fim <= inicio:
        return {}
    try:
        dados = json.loads(bruto[inicio : fim + 1])
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return dados if isinstance(dados, dict) else {}


class InterpretadorSemanticoRuntime:
    """Produz leitura validada; em ``shadow`` apenas registra divergências."""

    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        enviar_mensagem: Callable[..., Any] | None = None,
        modelo_llm: Any = None,
        modo: str | None = None,
        timeout_s: float = 2.0,
        log: Callable[..., Any] = print,
    ) -> None:
        configurado = str(modo or os.getenv("LAYLAY_INTERPRETACAO_SEMANTICA", "main")).strip().lower()
        self.modo = configurado if configurado in MODOS_VALIDOS else "shadow"
        self.contexto_getter = contexto_getter
        self.enviar_mensagem = resolver_enviador_modelo(
            modelo_llm=modelo_llm,
            enviar_mensagem=enviar_mensagem,
        )
        self.timeout_s = max(0.2, min(10.0, float(timeout_s)))
        self.log = log
        self._cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
        self._falhas_consecutivas = 0
        self._circuito_ate = 0.0
        self._observacao_lock = threading.Lock()
        self._observacao_em_andamento = False

    def _contexto(self) -> Dict[str, Any]:
        try:
            valor = self.contexto_getter()
            return dict(valor or {}) if isinstance(valor, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _resumo_contexto(ctx: Dict[str, Any]) -> Dict[str, Any]:
        mente = dict(ctx.get("mente") or {}) if isinstance(ctx.get("mente"), dict) else {}
        pendencia = dict(mente.get("pendencia_atual") or {}) if isinstance(mente.get("pendencia_atual"), dict) else {}
        mensagens = [m for m in list(ctx.get("mensagens") or []) if isinstance(m, dict)]
        ultima_assistente = next(
            (str(m.get("content") or "").strip()[:400] for m in reversed(mensagens) if m.get("role") == "assistant"),
            str(mente.get("ultima_resposta") or "").strip()[:400],
        )
        assunto = dict(mente.get("assunto_estruturado_atual") or {}) if isinstance(mente.get("assunto_estruturado_atual"), dict) else {}
        return {
            "ultima_fala_laylay": ultima_assistente,
            "assunto_atual": str(assunto.get("titulo") or mente.get("ultimo_topico") or "")[:180],
            "pendencia": {
                "ativa": pendencia.get("status") == "ativa",
                "foi_falada": bool(pendencia.get("foi_falada")),
                "tipo": str(pendencia.get("tipo") or "")[:60],
                "resposta_esperada": str(pendencia.get("resposta_esperada") or "")[:80],
                "descricao": str(pendencia.get("descricao") or pendencia.get("pergunta") or "")[:240],
            },
            "ultima_acao": {
                "intent": str(mente.get("ultima_acao_intent") or "")[:80],
                "alvo": str(mente.get("ultima_acao_alvo") or "")[:160],
            },
        }

    @staticmethod
    def _chave_cache(texto: str, contexto: Dict[str, Any]) -> str:
        material = json.dumps({"texto": texto, "contexto": contexto}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(material.encode("utf-8", errors="replace")).hexdigest()

    def analisar(self, texto: str, *, turno_legado: Dict[str, Any] | None = None) -> Dict[str, Any]:
        fala = " ".join(str(texto or "").strip().split())
        if self.modo == "off" or not fala or not callable(self.enviar_mensagem):
            return {}
        agora = time.monotonic()
        if agora < self._circuito_ate:
            return {}
        contexto = self._resumo_contexto(self._contexto())
        chave = self._chave_cache(fala, contexto)
        cache = self._cache.get(chave)
        if cache and agora - cache[0] <= 20.0:
            return dict(cache[1])
        payload = {"fala_atual": fala[:500], "contexto": contexto}
        try:
            bruto = self.enviar_mensagem(
                [
                    {"role": "system", "content": PROMPT_LEITURA_SEMANTICA},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                _com_tools=False,
                max_tokens=420,
                modo_rapido=True,
                timeout=max(1, int(round(self.timeout_s))),
            )
            dados = _extrair_json(bruto)
            leitura = normalizar_leitura_semantica(dados, texto=fala, origem="llm")
            if not leitura.get("valida"):
                raise ValueError("leitura sem atos válidos")
        except Exception as exc:
            self._falhas_consecutivas += 1
            if self._falhas_consecutivas >= 3:
                self._circuito_ate = agora + 60.0
                self._falhas_consecutivas = 0
                self.log("⚠️ [SEMÂNTICA] circuito pausado por 60s após falhas consecutivas.")
            else:
                self.log(f"⚠️ [SEMÂNTICA] observador indisponível: {type(exc).__name__}")
            return {}
        self._falhas_consecutivas = 0
        comparacao = comparar_com_legado(leitura, turno_legado)
        leitura["comparacao_legado"] = comparacao
        leitura["modo"] = self.modo
        self._cache[chave] = (agora, dict(leitura))
        if len(self._cache) > 128:
            antigos = sorted(self._cache.items(), key=lambda item: item[1][0])[:32]
            for chave_antiga, _ in antigos:
                self._cache.pop(chave_antiga, None)
        atos = ",".join(str(item.get("tipo") or "") for item in leitura.get("atos") or [])
        self.log(
            "🧠 [SEMÂNTICA:TURNO] "
            f"modo={self.modo} | atos={atos or '-'} | modalidade={leitura.get('modalidade_geral')} "
            f"| confiança={float(leitura.get('confianca') or 0.0):.2f} "
            f"| divergências={comparacao.get('divergencias') or []}"
        )
        return dict(leitura)

    def observar(self, texto: str, *, turno_legado: Dict[str, Any] | None = None) -> bool:
        """Agenda uma leitura ``shadow`` sem acrescentar latência ao turno."""
        if self.modo != "shadow" or not str(texto or "").strip():
            return False
        with self._observacao_lock:
            if self._observacao_em_andamento:
                self.log("🧠 [SEMÂNTICA] observação anterior ainda em andamento; turno não bloqueado.")
                return False
            self._observacao_em_andamento = True

        def executar() -> None:
            try:
                self.analisar(texto, turno_legado=turno_legado)
            finally:
                with self._observacao_lock:
                    self._observacao_em_andamento = False

        threading.Thread(
            target=executar,
            name="laylay-semantica-shadow",
            daemon=True,
        ).start()
        return True

def criar_interpretador_semantico_runtime(**kwargs: Any) -> InterpretadorSemanticoRuntime:
    return InterpretadorSemanticoRuntime(**kwargs)
