"""Persistência principal da memória da Laylay."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple


def carregar_memoria(memoria_sqlite, base_system_prompt: str):
    data = memoria_sqlite.carregar_estado()
    if not isinstance(data, dict):
        data = {}

    estado_auto = data.get("autoaprimoramento_estado")
    topicos_conversa_recente = [
        str(t).strip()
        for t in (data.get("topicos_conversa_recente") or [])
        if str(t).strip()
    ]
    ultimo_topico_conversa = str(data.get("ultimo_topico_conversa") or "").strip()
    try:
        ultimo_topico_ts = float(data.get("ultimo_topico_ts") or 0.0)
    except Exception:
        ultimo_topico_ts = 0.0
    mensagens = data.get("messages", [{"role": "system", "content": base_system_prompt}])
    if not isinstance(mensagens, list) or not mensagens:
        mensagens = [{"role": "system", "content": base_system_prompt}]
    mensagens = [m for m in mensagens if isinstance(m, dict) and m.get("role")]
    if not mensagens:
        mensagens = [{"role": "system", "content": base_system_prompt}]

    return {
        "messages": mensagens,
        "bordoes": data.get("bordoes", []),
        "resumo_conversa": data.get("resumo_conversa", ""),
        "memoria_fatos": data.get("memoria_fatos", []),
        "memoria_eventos": data.get("memoria_eventos", []),
        "historico_long_term": data.get("historico_long_term", ""),
        "current_emotion": data.get("current_emotion", data.get("emocao_atual", "calma")),
        "emotion_level": data.get("emotion_level", data.get("nivel_emocao", 1)),
        "autoaprimoramento_estado": estado_auto if isinstance(estado_auto, dict) else None,
        "topicos_conversa_recente": topicos_conversa_recente,
        "ultimo_topico_conversa": ultimo_topico_conversa,
        "ultimo_topico_ts": ultimo_topico_ts,
    }


def salvar_memoria(memoria_sqlite, dados: Dict[str, Any]) -> None:
    memoria_sqlite.salvar_estado(**dict(dados))


def registrar_autocorrecao_virtual(
    memoria_sqlite,
    estado: Dict[str, Any],
    origem: str,
    erro: str,
    correcao: str,
    contexto: str = "",
    ajustar_humor_cb: Optional[Callable[[int, str], None]] = None,
    registrar_autoaprimoramento_cb: Optional[Callable[..., None]] = None,
) -> Dict[str, Any]:
    origem_limpa = str(origem or "desconhecido").strip()
    erro_limpo = str(erro or "").strip()
    correcao_limpa = str(correcao or "").strip()
    contexto_limpo = str(contexto or "").strip()

    if not erro_limpo and not correcao_limpa:
        return estado

    estado = dict(estado or {})
    estado["_autocorrecao_total"] = int(estado.get("_autocorrecao_total") or 0) + 1
    estado["_cookie_virtual_total"] = int(estado.get("_cookie_virtual_total") or 0) + 1
    eventos = list(estado.get("_autocorrecao_eventos") or [])
    evento = {
        "ts": datetime.now().isoformat(" "),
        "origem": origem_limpa,
        "erro": erro_limpo[:180],
        "correcao": correcao_limpa[:220],
        "contexto": contexto_limpo[:220],
        "cookie": estado["_cookie_virtual_total"],
    }
    eventos.append(evento)
    if len(eventos) > 20:
        eventos = eventos[-20:]
    estado["_autocorrecao_eventos"] = eventos

    resumo = (
        f"Autocorrecao #{estado['_autocorrecao_total']} em {origem_limpa}: "
        f"erro='{erro_limpo[:120]}' -> correcao='{correcao_limpo[:160]}'"
    )
    if contexto_limpo:
        resumo += f" | contexto={contexto_limpo[:120]}"

    try:
        memoria_sqlite.salvar_eventos([resumo])
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao registrar evento: {e}")

    try:
        memoria_sqlite.salvar_resumo(f"{resumo} | cookie_virtual={estado['_cookie_virtual_total']}", tipo="autocorrecao")
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao salvar resumo: {e}")

    try:
        memoria_sqlite.salvar_aprendizado_semantico(
            tipo="autocorrecao",
            gatilho=erro_limpo[:140] or origem_limpa,
            valor=correcao_limpa[:180],
            regra="Quando perceber um erro próprio, corrigir a resposta e tornar a correção visível.",
            texto_original=f"{origem_limpa}: {erro_limpo} => {correcao_limpa}",
            confianca=0.92,
        )
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao salvar aprendizado: {e}")

    try:
        memoria_sqlite.salvar_aprendizado_semantico(
            tipo="correcao",
            gatilho=origem_limpa or erro_limpo[:120],
            valor=correcao_limpa[:180],
            regra="A correção ensinada pelo Pedro deve ser reaproveitada em próximas respostas semelhantes.",
            texto_original=f"{origem_limpa}: {erro_limpo} => {correcao_limpa}",
            confianca=0.95,
        )
    except Exception as e:
        print(f"⚠️ [AUTOCORREÇÃO] falha ao salvar correção aprendida: {e}")

    try:
        memoria_sqlite.salvar_preferencia("laylay_cookie_virtual_total", str(estado["_cookie_virtual_total"]))
    except Exception:
        pass

    if callable(ajustar_humor_cb):
        try:
            ajustar_humor_cb(+1, "cookie virtual por autocorreção")
        except Exception:
            pass

    if callable(registrar_autoaprimoramento_cb):
        try:
            registrar_autoaprimoramento_cb(
                {},
                f"{origem_limpa} {erro_limpo} {correcao_limpo}",
                True,
                erro=erro_limpo,
                contexto=contexto_limpo,
                origem=origem_limpa,
            )
        except Exception as e:
            print(f"⚠️ [AUTOCORREÇÃO] falha ao registrar autoaprimoramento: {e}")

    print(f"🍪 [AUTOCORREÇÃO] cookie virtual #{estado['_cookie_virtual_total']} concedido para a Laylay.")
    return estado


def init_memoria_contexto_diaria(arquivo: str) -> Optional[str]:
    if not os.path.exists(arquivo):
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump({"data": str(datetime.now().date()), "bom_dia_dito": False}, f, ensure_ascii=False, indent=2)
        return "Bom dia, Pedro. Pronta para mais um dia de dominação digital."

    with open(arquivo, "r", encoding="utf-8") as f:
        try:
            contexto = json.load(f)
        except Exception:
            contexto = {}

    hoje = str(datetime.now().date())
    if not isinstance(contexto, dict):
        contexto = {}
    if contexto.get("data") != hoje:
        contexto = {"data": hoje, "bom_dia_dito": False}
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(contexto, f, ensure_ascii=False, indent=2)
        return "Bom dia, Pedro. Pronta para mais um dia de dominação digital."

    if not bool(contexto.get("bom_dia_dito", False)):
        contexto["bom_dia_dito"] = True
        with open(arquivo, "w", encoding="utf-8") as f:
            json.dump(contexto, f, ensure_ascii=False, indent=2)
        return "Bom dia, Pedro. Pronta para mais um dia de dominação digital."
    return None
