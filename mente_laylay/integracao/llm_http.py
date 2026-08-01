"""Cliente HTTP compatível para LLM remoto/local usado pela Laylay."""

from __future__ import annotations

import time
import threading
import re
from typing import Any, Callable

import requests

from mente_laylay.cognicao.conversa_sobre_capacidades import resposta_conversa_sobre_capacidade
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural
from mente_laylay.memoria_mental.observabilidade import relatar_falha_opcional


# Estados do transporte são dados internos. Eles não são frases da Laylay e
# nunca devem ser enviados à personalidade, ao terminal ou ao TTS como fala.
FALHA_LLM_TIMEOUT = "__LAYLAY_LLM_TIMEOUT__"
FALHA_LLM_INDISPONIVEL = "__LAYLAY_LLM_INDISPONIVEL__"
FALHA_LLM_OCUPADA = "__LAYLAY_LLM_OCUPADA__"


def eh_estado_tecnico_llm(valor: Any) -> bool:
    """Reconhece sentinelas mesmo depois de um limpador remover pontuação."""
    texto = str(valor or "").casefold().strip()
    compacto = re.sub(r"[^a-z0-9]+", "", texto)
    return compacto in {
        "laylayllmtimeout",
        "laylayllmindisponivel",
        "laylayllmocupada",
    }


class RespostaLLMFallback:
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        *,
        motivo: str = "",
        classe: str = "degradacao",
        impacto: str = "turno",
        fallback: str = "contingencia_conversacional",
    ):
        self.status_code = status_code
        self._content = str(content or "")
        self.text = self._content
        self.motivo = str(motivo or "")
        self.classe = str(classe or "degradacao")
        self.impacto = str(impacto or "turno")
        self.fallback = str(fallback or "contingencia_conversacional")

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": self._content,
                    }
                }
            ]
        }


def endpoint_eh_local(base_url: str) -> bool:
    base = str(base_url or "").lower()
    return "localhost" in base or "127.0.0.1" in base or "0.0.0.0" in base


def timeout_padrao(base_url: str, local_timeout: int, remote_timeout: int) -> int:
    return int(local_timeout if endpoint_eh_local(base_url) else remote_timeout)


def conteudo_fallback_llm_local(data: dict) -> str:
    mensagens = data.get("messages") if isinstance(data, dict) else []
    texto = " ".join(str((m or {}).get("content") or "")[:500] for m in mensagens if isinstance(m, dict))
    baixo = texto.lower()
    ultima_usuario = ""
    for mensagem in reversed(list(mensagens or [])):
        if isinstance(mensagem, dict) and str(mensagem.get("role") or "").lower() == "user":
            ultima_usuario = str(mensagem.get("content") or "").strip()
            break
    if "intent" in baixo and "json" in baixo:
        return '{"intent":"NONE","params":{}}'
    # O contrato principal de conversa merece uma fala válida mesmo quando o
    # transporte entra em contingência. Ela não confirma ações nem inventa o
    # conteúdo que o modelo deixou de produzir.
    if '"fala"' in baixo and "comandos" in baixo and "json" in baixo:
        fala = fala_contingencia_natural(ultima_usuario)
        import json
        return json.dumps({"fala": fala, "comandos": []}, ensure_ascii=False)
    if "responda apenas json" in baixo or "json válido" in baixo or "json valido" in baixo:
        return "{}"
    if int((data or {}).get("max_tokens") or 0) <= 5:
        return "NAO"
    resposta_capacidade = resposta_conversa_sobre_capacidade(ultima_usuario)
    if resposta_capacidade:
        return resposta_capacidade
    usuario_baixo = ultima_usuario.lower()
    if any(p in usuario_baixo for p in ("música", "musica", "playlist", "som", "faixa")):
        return "Peguei que o assunto é música, mas meu modelo travou nessa resposta. Me dá o estilo ou artista e eu continuo exatamente desse ponto."
    return FALHA_LLM_INDISPONIVEL


def conteudo_fallback_modo_jogo(data: dict) -> str:
    """Mantém contratos JSON válidos sem acordar o modelo durante uma partida."""
    mensagens = data.get("messages") if isinstance(data, dict) else []
    texto = " ".join(str((m or {}).get("content") or "")[:500] for m in mensagens if isinstance(m, dict))
    baixo = texto.casefold()
    if "intent" in baixo and "json" in baixo:
        return '{"intent":"NONE","params":{}}'
    if "responda apenas json" in baixo or "json válido" in baixo or "json valido" in baixo:
        return "{}"
    try:
        if int((data or {}).get("max_tokens") or 0) <= 5:
            return "NAO"
    except (TypeError, ValueError):
        pass
    return FALHA_LLM_OCUPADA


def compactar_payload_llm_local(data: dict) -> dict:
    novo = dict(data or {})
    novo.pop("response_format", None)
    novo.pop("tools", None)
    novo.pop("tool_choice", None)
    novo["stream"] = False
    mensagens = []
    for msg in list(novo.get("messages") or []):
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role") or "user").strip().lower()
        if role not in {"system", "user", "assistant"}:
            role = "user"
        content = str(msg.get("content") or "")
        if not content.strip():
            continue
        limite = 2500 if role == "system" else 1200
        mensagens.append({"role": role, "content": content[:limite]})
    if not mensagens:
        mensagens = [{"role": "user", "content": "Responda em português, curto e natural."}]
    if len(mensagens) > 6:
        sistemas = [m for m in mensagens if m["role"] == "system"][:1]
        mensagens = sistemas + [m for m in mensagens if m["role"] != "system"][-5:]
    novo["messages"] = mensagens
    try:
        novo["max_tokens"] = min(int(novo.get("max_tokens") or 512), 384)
    except (TypeError, ValueError):
        novo["max_tokens"] = 384
    return novo


def payload_precisa_compactar_llm_local(data: dict) -> bool:
    mensagens = data.get("messages") if isinstance(data, dict) else []
    if not isinstance(mensagens, list):
        return False
    total_chars = 0
    for msg in mensagens:
        if isinstance(msg, dict):
            total_chars += len(str(msg.get("content") or ""))
    try:
        max_tokens = int((data or {}).get("max_tokens") or 0)
    except (TypeError, ValueError):
        max_tokens = 0
    # Qwen 7B local costuma estar em 4096 tokens; compactar antes evita 400.
    return total_chars > 9500 or max_tokens > 640


def post_chat_llm(
    headers: dict,
    data: dict,
    *,
    base_url: str,
    local_timeout: int,
    remote_timeout: int,
    bad_request_until: float,
    lock: Any,
    requests_post: Callable[..., Any],
    print_fn: Callable[..., Any],
    timeout: int | None = None,
    prioridade_interativa: bool | None = None,
    espera_lock_interativa_s: float = 1.5,
) -> tuple[Any, float]:
    """Serializa chamadas locais e recupera 400 com payload compacto."""
    url = f"{base_url}/chat/completions"
    timeout = timeout_padrao(base_url, local_timeout, remote_timeout) if timeout is None else timeout
    local = endpoint_eh_local(base_url)

    if local and time.time() < float(bad_request_until or 0.0):
        return RespostaLLMFallback(
            conteudo_fallback_llm_local(data),
            motivo="circuito_temporario_ativo",
        ), float(bad_request_until or 0.0)

    def _post(payload: dict):
        return requests_post(url, headers=headers, json=payload, timeout=timeout)

    if not local:
        return _post(data), float(bad_request_until or 0.0)

    pegou_lock = lock.acquire(blocking=False)
    if not pegou_lock:
        if prioridade_interativa is False:
            print_fn("🧠 [IA] tarefa secundária adiada porque a conversa está usando o modelo.")
            return RespostaLLMFallback(
                conteudo_fallback_llm_local(data),
                motivo="tarefa_secundaria_adiada",
                classe="esperada",
                impacto="nenhum",
                fallback="adiamento_tarefa_secundaria",
            ), float(bad_request_until or 0.0)
        # Uma fala nova do Pedro não deve ficar vários segundos atrás de uma
        # requisição antiga. Ainda damos uma janela curta para reaproveitar o
        # modelo já carregado, mas depois liberamos o fluxo com fallback.
        espera_lock = min(
            max(0.1, float(espera_lock_interativa_s or 0.1)),
            max(0.1, float(timeout or 0.1)),
        )
        print_fn(f"[IA] Modelo local ocupado; aguardando no máximo {espera_lock:.1f}s...")
        pegou_lock = lock.acquire(timeout=espera_lock)
        if not pegou_lock:
            print_fn("⚠️ [IA] Modelo local continuou ocupado; chamada liberada sem bloquear o fluxo.")
            contingencia = conteudo_fallback_llm_local(data)
            if not (contingencia.startswith('{"fala":') and '"comandos":[]' in contingencia):
                contingencia = FALHA_LLM_OCUPADA
            return RespostaLLMFallback(
                contingencia,
                motivo="modelo_local_ocupado",
            ), float(bad_request_until or 0.0)
    try:
        payload_envio = compactar_payload_llm_local(data) if payload_precisa_compactar_llm_local(data) else data
        resp = _post(payload_envio)
        if resp.status_code == 400:
            print_fn(f"⚠️ [IA] 400 do modelo local. Corpo: {str(resp.text or '')[:500]}")
            retry_data = compactar_payload_llm_local(payload_envio)
            resp_retry = _post(retry_data)
            if resp_retry.status_code != 400:
                print_fn("✓ [IA] Requisição local recuperada com payload compacto.")
                return resp_retry, float(bad_request_until or 0.0)
            print_fn(f"⚠️ [IA] 400 persistiu no retry compacto. Corpo: {str(resp_retry.text or '')[:500]}")
            novo_bad_request_until = time.time() + 20.0
            return RespostaLLMFallback(
                conteudo_fallback_llm_local(data),
                motivo="requisicao_invalida_persistente",
                classe="defeito",
            ), novo_bad_request_until
        if resp.status_code >= 500:
            print_fn(f"⚠️ [IA] {resp.status_code} temporário do modelo local; usando resposta contextual.")
            novo_bad_request_until = time.time() + 10.0
            return RespostaLLMFallback(
                conteudo_fallback_llm_local(data),
                motivo="servidor_llm_temporariamente_indisponivel",
            ), novo_bad_request_until
        return resp, float(bad_request_until or 0.0)
    finally:
        if pegou_lock:
            lock.release()


class LLMHttpRuntime:
    """Mantém configuração e estado transitório do transporte HTTP da LLM."""

    def __init__(
        self,
        *,
        base_url: str,
        local_timeout: int,
        remote_timeout: int,
        requests_post: Callable[..., Any],
        print_fn: Callable[..., Any] = print,
        ao_finalizar_conversa_modo_jogo: Callable[[], Any] | None = None,
        game_timeout: int = 15,
        game_idle_unload_s: float = 60.0,
        espera_lock_interativa_s: float = 1.5,
        timer_factory: Callable[..., Any] = threading.Timer,
        registrar_falha: Callable[..., Any] | None = None,
    ) -> None:
        self.base_url = str(base_url or "").rstrip("/")
        self.local_timeout = int(local_timeout)
        self.remote_timeout = int(remote_timeout)
        self.game_timeout = max(1, int(game_timeout))
        self.game_idle_unload_s = max(5.0, float(game_idle_unload_s))
        self.espera_lock_interativa_s = max(0.1, float(espera_lock_interativa_s))
        self.timer_factory = timer_factory
        self.requests_post = requests_post
        self.print_fn = print_fn
        self.ao_finalizar_conversa_modo_jogo = ao_finalizar_conversa_modo_jogo
        self.registrar_falha = registrar_falha
        # Estado e transporte não podem compartilhar o mesmo lock: uma chamada
        # local pode durar minutos, enquanto o monitor de jogos precisa ativar
        # o bloqueio imediatamente para mandar o Ollama liberar a GPU.
        self._state_lock = threading.RLock()
        self._request_lock = threading.RLock()
        self._bad_request_until = 0.0
        self._modo_jogo_ativo = False
        self._requisicoes_ativas = 0
        self._game_unload_timer: Any = None
        self._game_session_generation = 0
        self._game_session_state = "fria"

    def _relatar(
        self,
        codigo: str,
        erro: BaseException,
        *,
        classe: str = "degradacao",
        impacto: str = "servico",
        fallback: str = "sessao_jogo_sem_descarga_automatica",
        fase: str = "ciclo_sessao_jogo",
    ) -> bool:
        return relatar_falha_opcional(
            self.registrar_falha,
            "llm_http",
            codigo,
            erro=erro,
            classe=classe,
            impacto=impacto,
            fallback=fallback,
            dominio="llm",
            fase=fase,
        )

    @property
    def bad_request_until(self) -> float:
        with self._state_lock:
            return self._bad_request_until

    def endpoint_eh_local(self) -> bool:
        return endpoint_eh_local(self.base_url)

    @property
    def modo_jogo_ativo(self) -> bool:
        with self._state_lock:
            return self._modo_jogo_ativo

    @property
    def requisicao_local_em_andamento(self) -> bool:
        with self._state_lock:
            return bool(self.endpoint_eh_local() and self._requisicoes_ativas > 0)

    def definir_modo_jogo(self, ativo: bool) -> None:
        with self._state_lock:
            self._modo_jogo_ativo = bool(ativo)
            if not ativo:
                self._game_session_state = "encerrada"
                self._game_session_generation += 1
                timer = self._game_unload_timer
                self._game_unload_timer = None
            else:
                self._game_session_state = "fria"
                timer = None
        if timer is not None:
            try:
                timer.cancel()
            except Exception as erro:
                # Timer é uma fronteira substituível; falhar ao cancelar não
                # invalida a resposta já entregue, mas precisa aparecer no diagnóstico.
                self._relatar("falha_cancelar_timer_jogo", erro)

    @property
    def estado_sessao_jogo(self) -> str:
        with self._state_lock:
            return self._game_session_state

    def _agendar_descarregamento_jogo(self) -> None:
        """Renova a sessão; o modelo só sai após silêncio conversacional."""
        with self._state_lock:
            if not self._modo_jogo_ativo:
                return
            anterior = self._game_unload_timer
            self._game_session_generation += 1
            geracao = self._game_session_generation
            self._game_session_state = "resfriando"
            timer = self.timer_factory(
                self.game_idle_unload_s,
                lambda: self._descarregar_sessao_jogo(geracao),
            )
            try:
                timer.daemon = True
            except Exception as erro:
                self._relatar(
                    "falha_configurar_timer_jogo",
                    erro,
                    fallback="timer_sem_daemon",
                )
            self._game_unload_timer = timer
        if anterior is not None:
            try:
                anterior.cancel()
            except Exception as erro:
                self._relatar("falha_cancelar_timer_anterior", erro)
        try:
            timer.start()
        except Exception as erro:
            with self._state_lock:
                if self._game_unload_timer is timer:
                    self._game_unload_timer = None
                    self._game_session_state = "fria"
            self._relatar("falha_iniciar_timer_jogo", erro)
            return
        self.print_fn(
            f"🎮 [CONVERSA:JOGO] sessão local mantida por até "
            f"{self.game_idle_unload_s:.0f}s de silêncio."
        )

    def _descarregar_sessao_jogo(self, geracao: int) -> None:
        with self._state_lock:
            if (
                geracao != self._game_session_generation
                or not self._modo_jogo_ativo
            ):
                return
            if self._requisicoes_ativas > 0:
                reagendar = True
            else:
                reagendar = False
                self._game_unload_timer = None
                self._game_session_state = "encerrada"
        if reagendar:
            self._agendar_descarregamento_jogo()
            return
        if callable(self.ao_finalizar_conversa_modo_jogo):
            try:
                self.ao_finalizar_conversa_modo_jogo()
                self.print_fn("🎮 [CONVERSA:JOGO] sessão ociosa encerrada; VRAM liberada.")
            except Exception as erro:
                self.print_fn(f"⚠️ [MODO JOGO] não consegui descarregar a IA local: {erro}")
                self._relatar(
                    "falha_descarregar_modelo_jogo",
                    erro,
                    fallback="modelo_mantido_carregado",
                )

    def post(self, headers: dict, data: dict, timeout: int | None = None):
        dados_envio = dict(data or {})
        permitir_conversa_jogo = bool(dados_envio.pop("_laylay_conversa_modo_jogo", False))
        prioridade_interativa = dados_envio.pop("_laylay_prioridade_interativa", None)
        local_em_jogo = self.endpoint_eh_local() and self.modo_jogo_ativo
        if local_em_jogo and not permitir_conversa_jogo:
            return RespostaLLMFallback(
                conteudo_fallback_modo_jogo(dados_envio),
                motivo="economia_modo_jogo",
                classe="esperada",
                impacto="nenhum",
                fallback="bloqueio_modelo_local_em_jogo",
            )

        if local_em_jogo:
            # A resposta principal pode acordar o modelo uma única vez, usando
            # menos contexto e menos tokens para reduzir o impacto na partida.
            dados_envio = compactar_payload_llm_local(dados_envio)
            try:
                dados_envio["max_tokens"] = min(int(dados_envio.get("max_tokens") or 256), 256)
            except (TypeError, ValueError):
                dados_envio["max_tokens"] = 256
            self.print_fn("🎮 [MODO JOGO] conversa solicitada; IA local acordada só para esta resposta.")
            with self._state_lock:
                self._game_session_state = "respondendo"

        timeout_efetivo = timeout
        if timeout_efetivo is None and local_em_jogo:
            timeout_efetivo = self.game_timeout

        with self._state_lock:
            self._requisicoes_ativas += 1
            bad_request_until = self._bad_request_until
        try:
            resposta, novo_limite = post_chat_llm(
                headers,
                dados_envio,
                base_url=self.base_url,
                local_timeout=self.local_timeout,
                remote_timeout=self.remote_timeout,
                bad_request_until=bad_request_until,
                lock=self._request_lock,
                requests_post=self.requests_post,
                print_fn=self.print_fn,
                timeout=timeout_efetivo,
                prioridade_interativa=prioridade_interativa,
                espera_lock_interativa_s=self.espera_lock_interativa_s,
            )
            with self._state_lock:
                self._bad_request_until = novo_limite
            return resposta
        finally:
            with self._state_lock:
                self._requisicoes_ativas = max(0, self._requisicoes_ativas - 1)
            if local_em_jogo:
                self._agendar_descarregamento_jogo()


def criar_llm_http_runtime(**kwargs: Any) -> LLMHttpRuntime:
    return LLMHttpRuntime(**kwargs)


def executar_chat_llm(
    data: dict,
    *,
    post_chat: Callable[[dict, dict], Any],
    interpretar_payload: Callable[[dict], str],
    api_key: str,
    http_referer: str,
    app_title: str,
    endpoint_local: bool,
    timeout: int | None = None,
    log: Callable[[str], Any] = print,
    registrar_falha: Callable[..., Any] | None = None,
) -> str:
    """Executa uma chamada preparada e converte rede/payload em fala."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": http_referer,
        "X-Title": app_title,
    }
    try:
        response = post_chat(headers, data, timeout=timeout) if timeout is not None else post_chat(headers, data)
        if isinstance(response, RespostaLLMFallback) and response.motivo:
            # Transportes externos podem devolver o mesmo contrato sem passar
            # pelo runtime local. O relator suprime duplicatas por janela.
            if callable(registrar_falha):
                registrar_falha(
                    "llm_http",
                    response.motivo,
                    classe=response.classe,
                    impacto=response.impacto,
                    fallback=response.fallback,
                )
        if response.status_code == 401:
            log("Erro 401 (Unauthorized) no OpenRouter.")
            if callable(registrar_falha):
                registrar_falha(
                    "llm_http", "credencial_recusada",
                    classe="defeito", impacto="turno",
                    fallback="aviso_credencial",
                )
            return "Cheque sua chave do OpenRouter."
        response.raise_for_status()
        payload = response.json()
        return interpretar_payload(payload)
    except requests.exceptions.ReadTimeout as erro:
        log(f"Timeout na LLM local/API: {erro}")
        if callable(registrar_falha):
            registrar_falha(
                "llm_http", "timeout_resposta", erro=erro,
                classe="degradacao", impacto="turno",
                fallback="contingencia_conversacional",
            )
        return FALHA_LLM_TIMEOUT
    except requests.exceptions.RequestException as erro:
        log(f"Erro na API: {erro}")
        if callable(registrar_falha):
            registrar_falha(
                "llm_http", "transporte_indisponivel", erro=erro,
                classe="degradacao", impacto="turno",
                fallback="contingencia_conversacional",
            )
        return FALHA_LLM_INDISPONIVEL
