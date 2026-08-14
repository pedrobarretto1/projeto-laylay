"""Processamento de mensagens vindas do PC B."""

from __future__ import annotations

import asyncio
import json
import re
import threading
import time
import uuid
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default


class DestinoPCRuntime:
    """Interpreta destino local/remoto sem guardar estado próprio."""

    def __init__(self, *, normalizar_texto: Callable[[str], str]) -> None:
        self.normalizar_texto = normalizar_texto

    def resolver(self, params: dict, texto_original: str = "") -> str:
        params = params if isinstance(params, dict) else {}
        alvo = str(params.get("target") or "").strip().lower()
        texto = self.normalizar_texto(str(texto_original or ""))
        if alvo in {"pc_b", "pc b", "b", "computador_b", "computador b"}:
            return "pc_b"
        if any(x in texto for x in ["pc b", "pc_b", "computador b", "no b", "pro b", "pra b", "para o b"]):
            return "pc_b"
        if alvo in {"ambos", "both", "todos"}:
            return "ambos"
        return "pc_a"

    def limpar_mencao(self, texto: str) -> str:
        resultado = str(texto or "").strip()
        resultado = re.sub(r"\b(no|pro|pra|para o|para)\s+pc\s*b\b", " ", resultado, flags=re.IGNORECASE)
        resultado = re.sub(r"\b(no|pro|pra|para o|para)\s+b\b", " ", resultado, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", resultado).strip(" .,!?:;")


def criar_destino_pc_runtime(**kwargs: Any) -> DestinoPCRuntime:
    return DestinoPCRuntime(**kwargs)


class PCBRuntime:
    def __init__(
        self,
        *,
        clientes_getter: Callable[[], Any],
        loop_getter: Callable[[], Any],
        clientes_compativeis_getter: Callable[[str], Any] | None = None,
        estado_clientes_getter: Callable[[], Any] | None = None,
        log=print,
    ) -> None:
        self.clientes_getter = clientes_getter
        self.loop_getter = loop_getter
        self.clientes_compativeis_getter = clientes_compativeis_getter
        self.estado_clientes_getter = estado_clientes_getter
        self.log = log
        self._lock = threading.RLock()
        self._pendentes: Dict[str, Dict[str, Any]] = {}

    def enviar(self, payload: Dict[str, Any], timeout_s: float = 5.0) -> bool:
        """Envia e somente retorna sucesso depois do estado final do PC B."""
        clientes = set(self.clientes_getter() or ())
        loop = self.loop_getter()
        if not clientes or loop is None:
            self.log("[PC B] Nenhum cliente PC B conectado.")
            return False
        acao = str(payload.get("action") or "").strip()
        if callable(self.clientes_compativeis_getter):
            compativeis = set(self.clientes_compativeis_getter(acao) or ())
            clientes.intersection_update(compativeis)
            if not clientes:
                self.log(
                    f"[PC B] Nenhum cliente saudável anunciou suporte para {acao or 'a ação'}."
                )
                return False
        request_id = str(payload.get("requestId") or uuid.uuid4().hex)
        evento = threading.Event()
        entrada: Dict[str, Any] = {"event": evento, "result": None, "criado_em": time.time()}
        with self._lock:
            self._pendentes[request_id] = entrada
        mensagem = dict(payload)
        mensagem["requestId"] = request_id
        mensagem["expectsFinalStatus"] = True
        try:
            texto = json.dumps(mensagem)
            enviados = 0
            for cliente in list(clientes):
                futuro = asyncio.run_coroutine_threadsafe(cliente.send(texto), loop)
                futuro.result(timeout=min(2.0, max(0.2, float(timeout_s))))
                enviados += 1
            if not enviados:
                return False
            self.log(f"[PC B] Solicitação {request_id} enviada; aguardando confirmação final.")
            respondeu = evento.wait(max(0.2, float(timeout_s)))
            with self._lock:
                final = self._pendentes.pop(request_id, None) or entrada
            resultado = final.get("result")
            if not respondeu or not isinstance(resultado, dict):
                self.log(f"[PC B] Solicitação {request_id} enviada, mas não confirmada.")
                return False
            status = str(resultado.get("status") or "").strip().lower()
            return status in {"ok", "success", "completed", "concluido", "concluído"} and bool(
                resultado.get("final", True)
            )
        except Exception as erro:
            self.log(f"[PC B] Falha na solicitação {request_id}: {erro}")
            return False
        finally:
            with self._lock:
                self._pendentes.pop(request_id, None)

    def registrar_status(self, data: Dict[str, Any]) -> bool:
        request_id = str(data.get("requestId") or "")
        if not request_id:
            self.log("[PC B] Status sem requestId ignorado para confirmação de execução.")
            return False
        with self._lock:
            entrada = self._pendentes.get(request_id)
            if not entrada:
                return False
            entrada["result"] = dict(data)
            evento = entrada.get("event")
        if evento is not None:
            evento.set()
        return True

    def diagnostico(self) -> dict[str, Any]:
        clientes = []
        if callable(self.estado_clientes_getter):
            try:
                clientes = list(self.estado_clientes_getter() or [])
            except Exception:
                clientes = []
        capacidades = sorted({
            str(capacidade)
            for cliente in clientes if isinstance(cliente, dict) and cliente.get("fresh")
            for capacidade in cliente.get("capabilities", ())
        })
        saudaveis = sum(
            1 for cliente in clientes
            if isinstance(cliente, dict)
            and cliente.get("fresh")
            and cliente.get("health") == "ready"
        )
        with self._lock:
            pendentes = len(self._pendentes)
        return {
            "disponivel": bool(saudaveis),
            "clientes_conectados": len(clientes),
            "clientes_saudaveis": saudaveis,
            "capacidades": capacidades,
            "solicitacoes_pendentes": pendentes,
            "somente_estado_sanitizado": True,
            "autoriza_execucao": False,
        }


def criar_pc_b_runtime(**kwargs: Any) -> PCBRuntime:
    return PCBRuntime(**kwargs)


def processar_mensagem_pc_b(data: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    tipo = data.get("type")
    falar_com_lipsync = _get(ctx, "falar_com_lipsync")

    if tipo == "pc_b_screenshot":
        analisar_com_groq = _get(ctx, "_analisar_com_groq")
        registrar_memoria_visual = _get(ctx, "registrar_memoria_visual")
        current_emotion = _get(ctx, "current_emotion", "calma")
        emotion_level = int(_get(ctx, "emotion_level", 1) or 1)

        img_b64 = data.get("imagem_b64", "")
        if data.get("contextoSensivel") is True or data.get("sensitiveContext") is True:
            print("🛑 [VISÃO] PC B bloqueou captura em contexto sensível.")
            if callable(falar_com_lipsync):
                falar_com_lipsync("Não analisei a tela do PC B porque ela estava em um contexto sensível.", "calma", 1)
            return True
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
        registrar_status = _get(ctx, "registrar_status_pc_b")
        if callable(registrar_status):
            registrar_status(data)
        if data.get("status") == "error":
            erro_msg = data.get("error", "Erro desconhecido")
            app_err = data.get("app", "")
            acao_err = data.get("action", "")
            print(f"❌ [PC B] Falha remota: {erro_msg}")
            if data.get("sensitiveContext") is True:
                if callable(falar_com_lipsync):
                    falar_com_lipsync("O PC B bloqueou a captura porque detectou um contexto sensível.", "calma", 1)
                return True
            alvo = str(app_err or "PC B").strip()
            plano = planejar_resposta_acao(
                ResultadoAcao(
                    intent=str(acao_err or "ACAO_PC_B"),
                    status="falha_execucao",
                    alvo=alvo,
                    executou=False,
                    confirmado=False,
                    detalhe=str(erro_msg or ""),
                ),
                f"O PC B não conseguiu concluir a ação em {alvo}. Motivo: {erro_msg}.",
                emocao_preferida="decepcionada",
                nivel_preferido=2,
            )
            if callable(falar_com_lipsync):
                falar_com_lipsync(plano.fala, plano.emocao, plano.nivel)
        else:
            print(f"✅ [PC B] Ação {data.get('action')} em {data.get('app', '')} concluída com sucesso!")
        return True

    print(f"[PC B] Mensagem recebida: {data.get('message', data.get('type', data))}")
    return True
