"""Smoke test sem hardware para a distribuição congelada."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any

from mente_laylay.integracao.runtime_llm_portatil import RuntimeLLMPortatil


MODULOS_CRITICOS = {
    "chat_terminal": "mente_laylay.autonomia.modo_chat",
    "atalhos": "keyboard",
    "voz": "mente_laylay.percepcao.ouvido_whisper",
    "avatar": "mente_laylay.personalidade.avatar_runtime",
    "navegador": "mente_laylay.integracao.chrome_ws_server",
    "modo_jogo": "mente_laylay.percepcao.modo_jogo",
}


def executar_smoke_distribuicao(
    raiz: str | os.PathLike[str],
    *,
    ambiente: dict[str, str] | None = None,
) -> dict[str, Any]:
    pasta = Path(raiz).expanduser().resolve()
    env = dict(os.environ if ambiente is None else ambiente)
    capacidades: dict[str, str] = {}
    falhas: list[str] = []
    for nome, modulo in MODULOS_CRITICOS.items():
        try:
            importlib.import_module(modulo)
            capacidades[nome] = "disponivel"
        except Exception as erro:
            capacidades[nome] = "indisponivel"
            falhas.append(f"{nome}: {type(erro).__name__}")

    artefatos = {
        "laylay": (pasta / "Laylay.exe").is_file(),
        "launcher": (pasta / "Iniciar Laylay.exe").is_file(),
        "avatar": (pasta / "AvatarLaylay.exe").is_file(),
        "extensao_chrome": (pasta / "extensao_chrome" / "manifest.json").is_file(),
    }
    for nome, presente in artefatos.items():
        if not presente:
            falhas.append(f"artefato ausente: {nome}")

    memoria = pasta / "memoria"
    try:
        memoria.mkdir(parents=True, exist_ok=True)
        sentinela = memoria / ".smoke-escrita"
        sentinela.write_text("ok", encoding="utf-8")
        sentinela.unlink()
        memoria_gravavel = True
    except OSError as erro:
        memoria_gravavel = False
        falhas.append(f"memória sem escrita: {type(erro).__name__}")

    runtime = RuntimeLLMPortatil(raiz=pasta, ambiente=env)
    modelo_presente = runtime.modelo_disponivel
    motor_presente = runtime.motor_disponivel
    exigir_modelo = str(env.get("LAYLAY_SMOKE_EXIGIR_MODELO", "1")).casefold() not in {"0", "false", "nao", "não"}
    if not motor_presente:
        falhas.append("motor LLM portátil ausente")
    if exigir_modelo and not modelo_presente:
        falhas.append("modelo GGUF ausente")

    return {
        "status": "ok" if not falhas else "falha",
        "capacidades": capacidades,
        "artefatos": artefatos,
        "memoria_gravavel": memoria_gravavel,
        "llm": {
            "backend": runtime.backend,
            "motor_presente": motor_presente,
            "modelo_presente": modelo_presente,
            "degradacao_sem_ollama": runtime.backend == "portatil",
        },
        "falhas": falhas,
    }


def main(raiz: str | os.PathLike[str]) -> int:
    resultado = executar_smoke_distribuicao(raiz)
    print("LAYLAY_SMOKE_JSON=" + json.dumps(resultado, ensure_ascii=False, sort_keys=True))
    return 0 if resultado["status"] == "ok" else 1
