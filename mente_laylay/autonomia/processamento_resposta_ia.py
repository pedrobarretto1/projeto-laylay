"""Pós-processamento da resposta da IA na Laylay."""

from __future__ import annotations

import ast
import json
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


def _normalizar_fala_cb(
    texto: str,
    limpar_texto_fala_cb: Optional[Callable[[str], str]] = None,
    fallback_fala: str = "Estou aqui, Pedro. Me fala o próximo passo.",
) -> str:
    if callable(limpar_texto_fala_cb):
        try:
            texto = limpar_texto_fala_cb(texto)
        except Exception:
            pass
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    return texto or fallback_fala


def _extrair_campo_textual_json_like(texto: str, campo: str) -> str:
    bruto = str(texto or "")
    if not bruto or not campo:
        return ""

    m = re.search(rf'["\']?{re.escape(campo)}["\']?\s*:\s*', bruto, re.IGNORECASE)
    if not m:
        return ""

    i = m.end()
    while i < len(bruto) and bruto[i].isspace():
        i += 1
    if i >= len(bruto):
        return ""

    quote = bruto[i]
    if quote not in {'"', "'"}:
        return ""
    i += 1

    resultado: List[str] = []
    escape = False
    while i < len(bruto):
        ch = bruto[i]
        if escape:
            resultado.append(ch)
            escape = False
        elif ch == "\\":
            escape = True
        elif ch == quote:
            break
        else:
            resultado.append(ch)
        i += 1

    return "".join(resultado).strip()


def limpar_resposta_da_ia(
    resposta_bruta: Any,
    limpar_texto_fala_cb: Optional[Callable[[str], str]] = None,
    fallback_fala: str = "Estou aqui, Pedro. Me fala o próximo passo.",
) -> Tuple[str, List[Dict[str, Any]]]:
    """Separa fala e comandos, mesmo quando a saída da IA vem malformada."""
    if isinstance(resposta_bruta, tuple) and len(resposta_bruta) == 2:
        fala, comandos = resposta_bruta
        return _normalizar_fala_cb(str(fala or ""), limpar_texto_fala_cb, fallback_fala), list(comandos or [])

    original = str(resposta_bruta or "").strip()
    fala_final = ""
    comandos_finais: List[Dict[str, Any]] = []

    texto_pre = re.sub(r"^```(?:json)?\s*", "", original, flags=re.IGNORECASE)
    texto_pre = re.sub(r"\s*```$", "", texto_pre, flags=re.IGNORECASE).strip()

    try:
        dados = json.loads(texto_pre)
        if isinstance(dados, dict):
            fala_final = str(dados.get("fala", "")).strip()
            comandos = dados.get("comandos", [])
            if isinstance(comandos, list):
                comandos_finais = [c for c in comandos if isinstance(c, dict)]
                if comandos_finais:
                    return _normalizar_fala_cb(fala_final, limpar_texto_fala_cb, fallback_fala), comandos_finais
    except Exception:
        pass

    try:
        match_cmds = re.search(r'["\']?comandos["\']?\s*:\s*(\[.*?\])', texto_pre, re.IGNORECASE | re.DOTALL)
        if match_cmds:
            cmd_txt = match_cmds.group(1).strip()
            try:
                parsed = json.loads(cmd_txt)
            except Exception:
                parsed = ast.literal_eval(cmd_txt)
            if isinstance(parsed, list):
                comandos_finais = [c for c in parsed if isinstance(c, dict)]
    except Exception:
        pass

    try:
        fala_final = _extrair_campo_textual_json_like(texto_pre, "fala") or fala_final
    except Exception:
        pass

    if not comandos_finais:
        def _limpar_alvo_bruto(valor: str) -> str:
            v = str(valor or "").strip()
            v = v.strip(" '\"\t\r\n")
            v = v.rstrip(".,;:!?)]}>'\"")
            return v.strip()

        texto_busca = texto_pre
        padroes_soltos = [
            ("open_url", r'(?i)\bopen_url\b\s*["\':=]*\s*(?P<alvo>(?:https?://|www\.)[^\s"\']+|[^\s"\']+\.[^\s"\']+)(?:\b|$)'),
            ("youtube_search", r'(?i)\byoutube_search\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("youtube_play", r'(?i)\byoutube_play\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("close_tab", r'(?i)\bclose_tab\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("close_specific_tab", r'(?i)\bclose_specific_tab\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("open_app", r'(?i)\bopen_app\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
            ("close_app", r'(?i)\bclose_app\b\s*["\':=]*\s*(?P<alvo>.+?)(?:$|\n)'),
        ]
        for acao_solta, padrao_solto in padroes_soltos:
            m_solto = re.search(padrao_solto, texto_busca, flags=re.IGNORECASE | re.DOTALL)
            if not m_solto:
                continue
            alvo_solto = _limpar_alvo_bruto(m_solto.group("alvo") or "")
            if not alvo_solto:
                continue
            if acao_solta == "open_url":
                if not re.match(r"^(?:https?://|www\.)", alvo_solto, flags=re.IGNORECASE):
                    continue
            elif acao_solta in {"youtube_search", "youtube_play"}:
                alvo_solto = alvo_solto.strip(" '\"")
            comando = {"acao": acao_solta, "alvo": alvo_solto}
            if acao_solta == "open_url":
                comando["url"] = alvo_solto
            elif acao_solta in {"youtube_search", "youtube_play"}:
                comando["query"] = alvo_solto
            elif acao_solta in {"close_tab", "close_specific_tab"}:
                comando["target"] = alvo_solto
            elif acao_solta in {"open_app", "close_app"}:
                comando["app"] = alvo_solto
            comandos_finais = [comando]
            break

    if comandos_finais and not fala_final:
        txt_limpo_de_json = re.sub(r"\{.*\}", "", texto_pre, flags=re.DOTALL).strip()
        if txt_limpo_de_json and len(txt_limpo_de_json) > 1:
            fala_final = txt_limpo_de_json

    if not comandos_finais:
        if fala_final:
            if "{" in original or "comandos" in original.lower() or "intencao" in original.lower():
                print(f"⚠️ [IA] Resposta malformada tratada como fala: {fala_final[:60]}...")
            return _normalizar_fala_cb(fala_final, limpar_texto_fala_cb, fallback_fala), []
        texto_fala_pura = re.sub(r"\{.*\}", "", texto_pre, flags=re.DOTALL).strip()
        if not texto_fala_pura:
            texto_fala_pura = texto_pre
        texto_fala_pura = re.sub(r"\[EXEC:.*?\]", "", texto_fala_pura, flags=re.IGNORECASE | re.DOTALL)
        texto_fala_pura = texto_fala_pura.strip()
        if len(texto_fala_pura) < 2:
            texto_fala_pura = fallback_fala
        if "{" in original or "comandos" in original.lower():
            print(f"⚠️ [IA] Resposta malformada tratada como fala: {texto_fala_pura[:60]}...")
        return _normalizar_fala_cb(texto_fala_pura, limpar_texto_fala_cb, fallback_fala), []

    return _normalizar_fala_cb(fala_final, limpar_texto_fala_cb, fallback_fala), comandos_finais


def _saida_ia_parece_malformada(texto: str) -> bool:
    s = str(texto or "").strip()
    if not s:
        return False
    if re.search(r"(?i)\[EXEC:.*?\]", s):
        return True
    if re.search(r"(?i)\b(open_url|youtube_search|youtube_play|close_tab|close_specific_tab|open_app|close_app)\b", s):
        return True
    if ("{" in s or "}" in s) and not re.search(r'(?i)"?(fala|comandos|acao|alvo)"?\s*:', s):
        return True
    return False


def corrigir_saida_malformada_da_ia(
    texto_usuario: str,
    resposta_bruta: Any,
    enviar_mensagem_cb: Optional[Callable[..., Any]] = None,
) -> Optional[Any]:
    bruto = str(resposta_bruta or "").strip()
    if not bruto or not _saida_ia_parece_malformada(bruto):
        return None
    if not callable(enviar_mensagem_cb):
        return None

    prompt = (
        "Você é um corretor de saída. Reescreva a resposta abaixo em JSON válido e APENAS JSON.\n"
        "Formato obrigatório:\n"
        "{\"fala\":\"...\",\"comandos\":[{\"acao\":\"...\",\"alvo\":\"...\"}]}\n"
        "Regras:\n"
        "- Não use markdown.\n"
        "- Não use aspas soltas fora do JSON.\n"
        "- Se houver comando de abrir URL, use acao=open_url e coloque a URL em alvo.\n"
        "- Se a resposta anterior já tinha um comando implícito, preserve a intenção.\n"
        "- Se não houver comando, retorne comandos vazios.\n"
    )
    payload = {
        "texto_usuario": str(texto_usuario or "")[:1200],
        "resposta_bruta": bruto[:1800],
    }
    try:
        corrigida = enviar_mensagem_cb(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=240,
            modo_rapido=True,
        )
        if corrigida and str(corrigida).strip():
            return corrigida
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao pedir correção da saída: {e}")
    return None


def extrair_aprendizados_da_ia(resposta_bruta: Any) -> List[Any]:
    original = str(resposta_bruta or "").strip()
    if not original:
        return []

    texto_pre = re.sub(r"^```(?:json)?\s*", "", original, flags=re.IGNORECASE)
    texto_pre = re.sub(r"\s*```$", "", texto_pre, flags=re.IGNORECASE).strip()

    candidatos: Any = []
    try:
        dados = json.loads(texto_pre)
        if isinstance(dados, dict):
            candidatos = dados.get("aprendizados") or dados.get("aprendizado") or []
    except Exception:
        try:
            match = re.search(r'["\']?aprendizados?["\']?\s*:\s*(\[[\s\S]*?\]|["\'][\s\S]*?["\'])', texto_pre, re.IGNORECASE)
            if match:
                raw = match.group(1).strip()
                try:
                    candidatos = json.loads(raw)
                except Exception:
                    candidatos = ast.literal_eval(raw)
        except Exception:
            candidatos = []

    if isinstance(candidatos, str):
        candidatos = [candidatos]
    if not isinstance(candidatos, list):
        return []

    aprendizados: List[Any] = []
    for item in candidatos:
        if isinstance(item, dict):
            if any(str(item.get(k) or "").strip() for k in ("gatilho", "valor", "regra", "texto")):
                aprendizados.append(item)
            continue
        txt = str(item or "").strip()
        if len(txt) >= 8 and txt.lower() not in {"none", "nenhum", "n/a", "null"}:
            aprendizados.append(txt)
    return aprendizados


def salvar_aprendizados_da_ia(resposta_bruta: Any, memoria_sqlite: Any) -> List[Any]:
    aprendizados = extrair_aprendizados_da_ia(resposta_bruta)
    if not aprendizados:
        return []
    try:
        salvos_semanticos = memoria_sqlite.salvar_aprendizados_semanticos(aprendizados)
        fatos: List[str] = []
        for item in aprendizados:
            if isinstance(item, dict):
                gatilho = str(item.get("gatilho") or "").strip()
                valor = str(item.get("valor") or item.get("url") or item.get("link") or "").strip()
                regra = str(item.get("regra") or item.get("texto") or "").strip()
                resumo = " | ".join(p for p in [gatilho, valor, regra] if p)
                if resumo:
                    fatos.append(resumo)
            else:
                fatos.append(str(item).strip())
        if fatos:
            memoria_sqlite.registrar_fatos(fatos, categoria="aprendizado")
        print(f"🧠 [MEMÓRIA] {len(salvos_semanticos) or len(aprendizados)} aprendizado(s) salvo(s): {aprendizados[:2]}")
    except Exception as e:
        print(f"⚠️ [MEMÓRIA] Falha ao salvar aprendizados da IA: {e}")
        return []
    return aprendizados


def extrair_tipo_interacao_da_ia(resposta_bruta: Any) -> str:
    original = str(resposta_bruta or "").strip()
    if not original:
        return ""
    texto_pre = re.sub(r"^```(?:json)?\s*", "", original, flags=re.IGNORECASE)
    texto_pre = re.sub(r"\s*```$", "", texto_pre, flags=re.IGNORECASE).strip()
    try:
        dados = json.loads(texto_pre)
        if isinstance(dados, dict):
            tipo = str(dados.get("tipo_interacao") or dados.get("tipo") or "").strip().lower()
            if tipo in {"acao", "conversa", "aprendizado", "confirmacao"}:
                return tipo
    except Exception:
        pass
    try:
        match = re.search(r'["\']?tipo_interacao["\']?\s*:\s*["\']([^"\']+)["\']', texto_pre, re.IGNORECASE)
        if match:
            tipo = match.group(1).strip().lower()
            if tipo in {"acao", "conversa", "aprendizado", "confirmacao"}:
                return tipo
    except Exception:
        pass
    return ""
