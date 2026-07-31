"""Memoria visual da Laylay.

Este modulo guarda capturas e metadados em uma pasta própria, com limite diário,
para que a experiencia visual possa ser reutilizada depois sem virar captura contínua.
"""

from __future__ import annotations

import base64
import json
import os
import re
import threading
import unicodedata
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

MAX_MEMORIAS_VISUAIS_DIA = 5
RETENCAO_MEMORIA_VISUAL_DIAS = 7
_INDICE_LOCK = threading.RLock()
_MARCADORES_VISUAIS_SENSIVEIS = (
    "senha", "password", "login", "signin", "sign-in", "pagamento", "payment",
    "checkout", "internet banking", "internetbanking", "banco", "bank", "wallet",
    "carteira", "mensagem privada", "direct messages", "whatsapp", "web.telegram",
)


def contexto_visual_sensivel(contexto: dict | str | None) -> bool:
    if isinstance(contexto, dict):
        texto = " ".join(str(valor or "") for valor in contexto.values())
    else:
        texto = str(contexto or "")
    base = _normalizar_texto_visual(texto)
    return any(_normalizar_texto_visual(marcador) in base for marcador in _MARCADORES_VISUAIS_SENSIVEIS)


def executar_captura_tela(
    destino: str,
    *,
    enviar_pc_b: Callable[[dict], Any],
    capturar_tela: Callable[[], str],
    analisar_imagem: Callable[[str, str], str],
    falar: Callable[..., Any],
    estado_emocional: Callable[[], tuple[str, int]],
    registrar_memoria: Callable[..., Any] | None = None,
    obter_contexto: Callable[[], dict] | None = None,
    thread_factory: Callable[..., Any] = threading.Thread,
    log: Callable[[str], Any] = print,
) -> bool:
    """Executa a visão manual preservando destino, fala e processamento assíncrono."""
    pergunta = (
        "Você é a Laylay, assistente debochada, sarcástica e dona absoluta deste PC. "
        "Olhe para esta tela e descreva o que o usuário está fazendo ou o que está aberto. "
        "Seja curta (máximo 3 linhas), direta, irônica e julgue as escolhas dele se for o caso. "
        "Responda SEMPRE em português brasileiro, com seu jeitão de sempre."
    )
    contexto_atual = obter_contexto() if callable(obter_contexto) else {}
    if contexto_visual_sensivel(contexto_atual):
        falar("Não capturei a tela porque detectei uma página sensível, com possíveis senhas, conversa privada ou pagamento.", "calma", 1)
        log("[VISÃO] Captura bloqueada por contexto sensível.")
        return True
    if str(destino or "").strip().lower() == "pc_b":
        falar("Vou pedir ao PC B uma captura protegida; se for segura, a imagem será enviada ao serviço externo de análise.", "calma", 1)
        confirmado = bool(enviar_pc_b({
            "action": "capturar_tela",
            "pergunta": pergunta,
            "bloquearContextoSensivel": True,
        }))
        if not confirmado:
            falar("Pedi a captura ao PC B, mas ele não confirmou que verificou e analisou a tela.", "calma", 1)
            return True
        falar("Abrindo o olho no PC B, um segundo...", "calma", 1)
        return True

    def ver_tela_local() -> None:
        try:
            log("[VISÃO] Capturando tela local...")
            imagem = capturar_tela()
            if not imagem:
                falar("Não consegui capturar a tela.", "calma", 1)
                return
            falar("A imagem será enviada ao serviço externo de análise visual agora.", "calma", 1)
            descricao = analisar_imagem(imagem, pergunta)
            emocao, nivel = estado_emocional()
            if callable(registrar_memoria):
                try:
                    registrar_memoria(
                        imagem,
                        descricao,
                        motivo="captura visual manual",
                        contexto=contexto_atual,
                        emocao=emocao or "calma",
                        intensidade=int(nivel or 1),
                        tags=["visao", "captura", "manual"],
                        origem="pc_a",
                    )
                except Exception as erro_memoria:
                    log(f"[VISÃO] Falha ao registrar memória visual: {erro_memoria}")
            falar(str(descricao or "")[:300], emocao or "debochada", nivel or 2)
        except Exception as erro:
            log(f"[VISÃO] Erro: {erro}")
            falar("Tive um problema pra olhar a tela.", "irritada", 2)

    thread_factory(target=ver_tela_local, daemon=True).start()
    falar("Tô olhando pra tela agora, um segundo...", "calma", 1)
    return True


class MemoriaVisualRuntime:
    """Coordena captura manual usando o estado emocional e visual compartilhado."""

    def __init__(self, *, namespace_getter: Callable[[], dict], log: Callable[[str], Any] = print) -> None:
        self.namespace_getter = namespace_getter
        self.log = log

    def executar(self, destino: str, *, registrar_memoria: bool = False) -> bool:
        ns = self.namespace_getter() or {}
        return executar_captura_tela(
            destino,
            enviar_pc_b=ns["enviar_pc_b"],
            capturar_tela=ns["capturar_tela"],
            analisar_imagem=ns["analisar_imagem"],
            falar=ns["falar"],
            estado_emocional=ns["estado_emocional"],
            registrar_memoria=ns["registrar_memoria"] if registrar_memoria else None,
            obter_contexto=ns["obter_contexto"],
            log=self.log,
        )


def criar_memoria_visual_runtime(**kwargs: Any) -> MemoriaVisualRuntime:
    return MemoriaVisualRuntime(**kwargs)

_PASTA_MEMORIA = ""
_PASTA_MEMORIA_VISUAL = ""
_ARQUIVO_INDICE = ""


def configurar_memoria_visual(pasta_memoria: str, max_por_dia: int = 5) -> None:
    """Define onde a memoria visual sera salva."""
    global MAX_MEMORIAS_VISUAIS_DIA, RETENCAO_MEMORIA_VISUAL_DIAS, _PASTA_MEMORIA, _PASTA_MEMORIA_VISUAL, _ARQUIVO_INDICE
    _PASTA_MEMORIA = str(pasta_memoria or "").strip()
    _PASTA_MEMORIA_VISUAL = os.path.join(_PASTA_MEMORIA, "memoria_visual")
    _ARQUIVO_INDICE = os.path.join(_PASTA_MEMORIA, "memoria_visual_indice.json")
    MAX_MEMORIAS_VISUAIS_DIA = int(max_por_dia or 5)
    RETENCAO_MEMORIA_VISUAL_DIAS = max(1, int(os.getenv("LAYLAY_MEMORIA_VISUAL_RETENCAO_DIAS", "7") or 7))
    os.makedirs(_PASTA_MEMORIA_VISUAL, exist_ok=True)
    limpar_memorias_visuais_expiradas()


def _normalizar_texto_visual(texto: str) -> str:
    t = str(texto or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _carregar_indice_memoria_visual() -> dict:
    with _INDICE_LOCK:
        try:
            if _ARQUIVO_INDICE and os.path.exists(_ARQUIVO_INDICE):
                with open(_ARQUIVO_INDICE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        data.setdefault("dias", {})
                        return data
        except Exception:
            pass
    return {"dias": {}}


def _salvar_indice_memoria_visual(indice: dict) -> None:
    if not _ARQUIVO_INDICE:
        return
    os.makedirs(os.path.dirname(_ARQUIVO_INDICE), exist_ok=True)
    with _INDICE_LOCK:
        temporario = f"{_ARQUIVO_INDICE}.{uuid.uuid4().hex}.tmp"
        with open(temporario, "w", encoding="utf-8") as f:
            json.dump(indice, f, ensure_ascii=False, indent=2)
        os.replace(temporario, _ARQUIVO_INDICE)


def limpar_memorias_visuais_expiradas(agora: datetime | None = None) -> int:
    """Remove imagens/metadados fora do prazo e reconstrói o índice."""
    if not _PASTA_MEMORIA_VISUAL:
        return 0
    limite = (agora or datetime.now()).date() - timedelta(days=RETENCAO_MEMORIA_VISUAL_DIAS)
    removidos = 0
    with _INDICE_LOCK:
        indice = _carregar_indice_memoria_visual()
        dias = indice.get("dias") if isinstance(indice.get("dias"), dict) else {}
        for dia in list(dias):
            try:
                expirou = datetime.strptime(dia, "%Y-%m-%d").date() < limite
            except ValueError:
                expirou = True
            if not expirou:
                continue
            pasta = os.path.join(_PASTA_MEMORIA_VISUAL, dia)
            if os.path.isdir(pasta):
                import shutil
                shutil.rmtree(pasta, ignore_errors=True)
            removidos += len(dias.pop(dia, []) or [])
        indice["dias"] = dias
        _salvar_indice_memoria_visual(indice)
    return removidos


def _contar_memorias_visuais_no_dia(data_dia: str) -> int:
    indice = _carregar_indice_memoria_visual()
    dias = indice.get("dias") if isinstance(indice.get("dias"), dict) else {}
    registros = dias.get(data_dia) if isinstance(dias, dict) else []
    return len(registros) if isinstance(registros, list) else 0


def _classificar_importancia_memoria_visual(descricao: str, motivo: str, contexto: str) -> int:
    texto = _normalizar_texto_visual(" ".join([descricao or "", motivo or "", contexto or ""]))
    if any(k in texto for k in ["terminou", "concluiu", "finalizou", "ganhou", "vitoria", "vitória", "derrota", "novo jogo", "projeto", "render", "exportou", "salvou"]):
        return 9
    if any(k in texto for k in ["música", "musica", "show", "filme", "video", "vídeo", "assistiu", "playlist"]):
        return 8
    if any(k in texto for k in ["focado", "concentrado", "trabalho", "programando", "código", "codigo", "estudo"]):
        return 7
    if any(k in texto for k in ["curioso", "curiosidade", "pedido", "lembrar", "memória", "memoria"]):
        return 6
    return 5


def capturar_tela_base64(qualidade: int = 60) -> str:
    """Tira screenshot da tela atual e retorna Base64."""
    try:
        from PIL import Image, ImageFilter
        import io as _io
        import pyautogui

        img = pyautogui.screenshot()
        # Notificações do Windows normalmente aparecem no canto inferior direito.
        # O desfoque reduz vazamento acidental sem ocultar o centro da tarefa.
        largura, altura = img.size
        caixa = (int(largura * 0.72), int(altura * 0.68), largura, altura)
        canto = img.crop(caixa).filter(ImageFilter.GaussianBlur(radius=18))
        img.paste(canto, caixa)
        _resample = getattr(Image, "Resampling", Image).LANCZOS
        img.thumbnail((1280, 720), _resample)
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=qualidade)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return ""


def _resumir_erro_groq(erro: Exception) -> tuple[str, str]:
    bruto = str(erro or "").strip()
    seguro = re.sub(r"\bgsk_[A-Za-z0-9_-]+", "<chave_oculta>", bruto)
    seguro = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]+", "Bearer <oculto>", seguro)
    base = seguro.casefold()
    if "401" in base or "authentication" in base or "invalid api key" in base:
        return "autenticacao", seguro[:240]
    if "decommission" in base or "model_decommissioned" in base:
        return "modelo_desativado", seguro[:240]
    if "404" in base or "model_not_found" in base:
        return "modelo_indisponivel", seguro[:240]
    if "403" in base or "permission" in base:
        return "permissao_modelo", seguro[:240]
    if "413" in base or "too large" in base:
        return "imagem_grande", seguro[:240]
    if "429" in base or "rate limit" in base or "quota" in base:
        return "limite", seguro[:240]
    if re.search(r"\b(?:500|502|503|504)\b", base) or "timeout" in base:
        return "transitorio", seguro[:240]
    return "desconhecido", seguro[:240]


def analisar_com_groq(
    imagem_b64: str,
    pergunta: str,
    api_key: str,
    model: str,
    *,
    client_factory: Callable[..., Any] | None = None,
    requests_post: Callable[..., Any] | None = None,
    forcar_http: bool = False,
    sleep_fn: Callable[[float], Any] | None = None,
    max_tentativas: int = 3,
    timeout_s: float = 35.0,
    retry_delay_s: float = 4.0,
    temperature: float = 0.7,
    log: Callable[[str], Any] = print,
) -> str:
    """Analisa uma imagem com Groq Vision."""
    max_tentativas = max(1, min(3, int(max_tentativas)))
    timeout_s = max(3.0, float(timeout_s))
    retry_delay_s = max(0.0, float(retry_delay_s))
    dormir = sleep_fn
    from mente_laylay.percepcao.imagens_multimodais import desempacotar_imagens

    imagens = desempacotar_imagens(imagem_b64)
    imagens_envio = imagens
    if len(imagens) >= 3:
        # O pacote de item guarda três quadros: contexto, tooltip amplo e
        # detalhe nativo. O detalhe fica reservado para a confirmação literal
        # que o runtime só solicita quando a primeira leitura é insegura. Isso
        # evita pagar pelos mesmos pixels duas vezes no limite TPM da Groq.
        imagens_envio = imagens[:2]
        log(
            "🎮 [VISÃO:GROQ] pacote otimizado | "
            f"enviadas={len(imagens_envio)} reservadas={len(imagens) - len(imagens_envio)}"
        )
    conteudo: list[dict[str, Any]] = [{"type": "text", "text": pergunta}]
    for indice, imagem in enumerate(imagens_envio, start=1):
        if len(imagens_envio) > 1:
            dimensoes = (
                f" ({imagem.get('width')}x{imagem.get('height')})"
                if imagem.get("width") and imagem.get("height") else ""
            )
            conteudo.append({
                "type": "text",
                "text": f"Imagem {indice}: {imagem.get('label')}{dimensoes}",
            })
        conteudo.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{imagem.get('mime') or 'image/jpeg'};base64,{imagem.get('data')}"
            },
        })
    payload = {
        "model": str(model or "").strip(),
        "messages": [
            {
                "role": "user",
                "content": conteudo,
            }
        ],
        "temperature": max(0.0, min(1.0, float(temperature))),
        "top_p": 0.8,
        "reasoning_effort": "none",
        "max_completion_tokens": 512,
    }
    for tentativa in range(max_tentativas):
        try:
            usar_http = bool(forcar_http)
            fabrica = client_factory
            if fabrica is None and not usar_http:
                try:
                    from groq import Groq  # type: ignore[import-untyped]

                    fabrica = Groq
                except ModuleNotFoundError:
                    usar_http = True
                    log("ℹ️ [VISÃO:GROQ] SDK ausente; usando API HTTP direta.")

            if usar_http:
                post = requests_post
                if post is None:
                    import requests

                    post = requests.post
                retorno = post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {str(api_key or '').strip()}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=timeout_s,
                )
                status = int(getattr(retorno, "status_code", 200) or 200)
                if status >= 400:
                    corpo = str(getattr(retorno, "text", "") or "")[:400]
                    raise RuntimeError(f"HTTP {status}: {corpo}")
                dados_resposta = retorno.json()
                texto = str(
                    (((dados_resposta.get("choices") or [{}])[0].get("message") or {}).get("content"))
                    or ""
                ).strip()
            else:
                client = fabrica(api_key=str(api_key or "").strip())
                resposta = client.chat.completions.create(**payload)
                texto = str(resposta.choices[0].message.content or "").strip()
            texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.IGNORECASE | re.DOTALL).strip()
            if texto.casefold().startswith("<think>"):
                log(f"⚠️ [VISÃO:GROQ] raciocínio interno sem resposta final | modelo={model}")
                return "Falha visual: o serviço não devolveu uma resposta final."
            if texto:
                return texto
            log(f"⚠️ [VISÃO:GROQ] resposta vazia | modelo={model}")
            return "Falha visual: o serviço devolveu uma resposta vazia."
        except Exception as e:
            categoria, detalhe = _resumir_erro_groq(e)
            log(
                f"⚠️ [VISÃO:GROQ] categoria={categoria} | modelo={model} "
                f"| tentativa={tentativa + 1}/{max_tentativas} | detalhe={detalhe}"
            )
            if categoria in {"limite", "transitorio"} and tentativa < max_tentativas - 1:
                if dormir is None:
                    import time

                    time.sleep(retry_delay_s * (tentativa + 1))
                else:
                    dormir(retry_delay_s * (tentativa + 1))
                continue
            falas = {
                "autenticacao": "Falha visual: a chave Groq foi recusada.",
                "modelo_desativado": "Falha visual: o modelo configurado foi desativado pela Groq.",
                "modelo_indisponivel": "Falha visual: o modelo configurado não está disponível.",
                "permissao_modelo": "Falha visual: sua conta não tem permissão para esse modelo.",
                "imagem_grande": "Falha visual: a imagem passou do limite do serviço.",
                "limite": "Falha visual: a Groq atingiu o limite temporário.",
                "transitorio": "Falha visual: o serviço Groq está temporariamente indisponível.",
            }
            return falas.get(categoria, "Falha visual: a chamada Groq não foi concluída.")
    return "Falha visual: a chamada Groq não foi concluída."


def sintetizar_texto_com_groq(
    prompt: str,
    api_key: str,
    model: str,
    *,
    requests_post: Callable[..., Any] | None = None,
    timeout_s: float = 18.0,
    log: Callable[[str], Any] = print,
) -> str:
    """Síntese curta sem reenviar a imagem já interpretada."""
    if not str(prompt or "").strip() or not str(api_key or "").strip():
        return ""
    try:
        post = requests_post
        if post is None:
            import requests

            post = requests.post
        retorno = post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {str(api_key).strip()}",
                "Content-Type": "application/json",
            },
            json={
                "model": str(model or "").strip(),
                "messages": [{"role": "user", "content": str(prompt)[:12000]}],
                "temperature": 0.2,
                "top_p": 0.8,
                "reasoning_effort": "none",
                "max_completion_tokens": 380,
            },
            timeout=max(3.0, float(timeout_s)),
        )
        status = int(getattr(retorno, "status_code", 200) or 200)
        if status >= 400:
            raise RuntimeError(f"HTTP {status}")
        dados = retorno.json()
        texto = str(
            (((dados.get("choices") or [{}])[0].get("message") or {}).get("content"))
            or ""
        ).strip()
        return re.sub(
            r"<think>.*?</think>", "", texto,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
    except Exception as erro:
        categoria, _detalhe = _resumir_erro_groq(erro)
        log(f"⚠️ [PESQUISA JOGO:SÍNTESE] categoria={categoria}; usando leitura visual")
        return ""


def registrar_memoria_visual(
    imagem_b64: str,
    descricao: str,
    motivo: str = "captura manual",
    contexto: str | dict = "",
    emocao: str = "",
    intensidade: int = 1,
    tags: Optional[list] = None,
    origem: str = "pc_a",
) -> Optional[str]:
    """Salva uma memoria visual com limite diário e metadados."""
    if not imagem_b64:
        return None
    if not _PASTA_MEMORIA_VISUAL:
        return None

    hoje = datetime.now().strftime("%Y-%m-%d")
    agora = datetime.now()
    if _contar_memorias_visuais_no_dia(hoje) >= MAX_MEMORIAS_VISUAIS_DIA:
        print(f"🧠 [VISÃO] Limite diário de {MAX_MEMORIAS_VISUAIS_DIA} memórias visuais atingido em {hoje}.")
        return None

    try:
        pasta_dia = os.path.join(_PASTA_MEMORIA_VISUAL, hoje)
        os.makedirs(pasta_dia, exist_ok=True)

        uid = uuid.uuid4().hex[:12]
        nome_base = agora.strftime("%H%M%S") + f"_{uid}"
        img_path = os.path.join(pasta_dia, f"{nome_base}.jpg")
        meta_path = os.path.join(pasta_dia, f"{nome_base}.json")

        dados_img = base64.b64decode(str(imagem_b64).split(",")[-1])
        with open(img_path, "wb") as f_img:
            f_img.write(dados_img)

        indice = _carregar_indice_memoria_visual()
        if not isinstance(indice.get("dias"), dict):
            indice["dias"] = {}
        lista_dia = list(indice["dias"].get(hoje) or [])
        importancia = _classificar_importancia_memoria_visual(descricao, motivo, contexto)
        reg = {
            "id": uid,
            "data": hoje,
            "horario": agora.strftime("%H:%M:%S"),
            "imagem": img_path,
            "programa": str((contexto or {}).get("exe") if isinstance(contexto, dict) else "").strip(),
            "contexto": contexto if isinstance(contexto, dict) else {"texto": str(contexto or "")},
            "descricao": str(descricao or "").strip(),
            "emocao": str(emocao or "").strip(),
            "intensidade": int(intensidade or 1),
            "motivo": str(motivo or "").strip(),
            "tags": list(tags or []),
            "importancia": int(importancia),
            "origem": str(origem or "pc_a").strip(),
        }

        with open(meta_path, "w", encoding="utf-8") as f_meta:
            json.dump(reg, f_meta, ensure_ascii=False, indent=2)

        lista_dia.append(reg)
        indice["dias"][hoje] = lista_dia[-MAX_MEMORIAS_VISUAIS_DIA:]
        indice["ultimo_registro"] = reg
        indice["atualizado_em"] = agora.isoformat(" ")
        _salvar_indice_memoria_visual(indice)

        print(f"🖼️ [VISÃO] Memória visual salva: {img_path}")
        return img_path
    except Exception as e:
        print(f"⚠️ [VISÃO] Falha ao registrar memória visual: {e}")
        return None
