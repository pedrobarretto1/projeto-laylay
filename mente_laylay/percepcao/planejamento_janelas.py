"""Observação de atividade e planejamento de layouts de janelas."""

from __future__ import annotations

import math
import re
import threading
import time
import unicodedata
from typing import Any, Callable, Iterable


MAPA_NOMES_JANELA = {
    "opera": "opera", "opera gx": "opera", "operagx": "opera",
    "opede": "opera", "opeditor": "opera", "chrome": "chrome",
    "google chrome": "chrome", "edge": "edge", "microsoft edge": "edge",
    "whatsapp.root": "whatsapp", "whatsapp": "whatsapp",
    "vscode": "visual studio code", "vs code": "visual studio code",
    "code": "visual studio code", "visual studio code": "visual studio code",
    "steam": "steam", "steamservice": "steam", "steamwebhelper": "steam",
}

TITULOS_AUXILIARES_JANELA = {"default ime", "msctfime ui", "program manager", "dwm"}

TITULOS_JANELA_LIXO = {
    "", "Program Manager", "Settings", "Configurações",
    "Microsoft Text Input Application", "Taskbar", "Cortana", "Search",
    "Widget", "LockApp.exe",
}

_ATIVIDADE_JANELAS_LOCK = threading.RLock()
_ATIVIDADE_JANELAS: dict[str, dict[str, Any]] = {}
_ULTIMA_ATIVIDADE_CHAVE = ""
_ULTIMA_ATIVIDADE_TS = 0.0

def _chave_atividade_janela(*, hwnd: Any = None, titulo: str = "") -> str:
    try:
        if hwnd is not None and int(hwnd):
            return f"hwnd:{int(hwnd)}"
    except (TypeError, ValueError):
        pass
    titulo_norm = normalizar_alvo_ambiente(titulo)
    return f"titulo:{titulo_norm}" if titulo_norm else ""

def registrar_atividade_janela_ativa(
    *,
    hwnd: Any = None,
    titulo: str = "",
    pid: int = 0,
    executavel: str = "",
    instante: float | None = None,
) -> None:
    """Acumula recência e tempo efetivo em foco a partir do monitor existente."""
    global _ULTIMA_ATIVIDADE_CHAVE, _ULTIMA_ATIVIDADE_TS
    chave = _chave_atividade_janela(hwnd=hwnd, titulo=titulo)
    if not chave:
        return
    agora = float(time.time() if instante is None else instante)
    with _ATIVIDADE_JANELAS_LOCK:
        item = dict(_ATIVIDADE_JANELAS.get(chave) or {})
        segundos_foco = float(item.get("segundos_foco") or 0.0)
        if _ULTIMA_ATIVIDADE_CHAVE == chave and _ULTIMA_ATIVIDADE_TS:
            # O monitor normalmente amostra a cada dois segundos. Um teto
            # impede somar horas depois de suspensão, travamento ou hibernação.
            segundos_foco += min(10.0, max(0.0, agora - _ULTIMA_ATIVIDADE_TS))
        mudou = _ULTIMA_ATIVIDADE_CHAVE != chave
        item.update({
            "chave": chave,
            "hwnd": hwnd,
            "titulo": str(titulo or "").strip(),
            "pid": int(pid or 0),
            "executavel": str(executavel or "").strip().casefold(),
            "primeiro_visto_ts": float(item.get("primeiro_visto_ts") or agora),
            "ultimo_foco_ts": agora,
            "segundos_foco": segundos_foco,
            "ativacoes": int(item.get("ativacoes") or 0) + (1 if mudou else 0),
        })
        _ATIVIDADE_JANELAS[chave] = item
        # O histórico é transitório e limitado; não vira memória pessoal.
        if len(_ATIVIDADE_JANELAS) > 80:
            antigas = sorted(
                _ATIVIDADE_JANELAS,
                key=lambda item_chave: float(
                    _ATIVIDADE_JANELAS[item_chave].get("ultimo_foco_ts") or 0.0
                ),
            )
            for antiga in antigas[:-60]:
                _ATIVIDADE_JANELAS.pop(antiga, None)
        _ULTIMA_ATIVIDADE_CHAVE = chave
        _ULTIMA_ATIVIDADE_TS = agora

def snapshot_atividade_janelas() -> dict[str, dict[str, Any]]:
    with _ATIVIDADE_JANELAS_LOCK:
        return {chave: dict(valor) for chave, valor in _ATIVIDADE_JANELAS.items()}

def limpar_historico_atividade_janelas() -> None:
    """Reinicia apenas o contexto efêmero; usado na inicialização e em testes."""
    global _ULTIMA_ATIVIDADE_CHAVE, _ULTIMA_ATIVIDADE_TS
    with _ATIVIDADE_JANELAS_LOCK:
        _ATIVIDADE_JANELAS.clear()
        _ULTIMA_ATIVIDADE_CHAVE = ""
        _ULTIMA_ATIVIDADE_TS = 0.0

def _relatar_falha_janela(
    registrar_falha: Callable[..., Any] | None,
    codigo: str,
    erro: BaseException,
) -> None:
    if callable(registrar_falha):
        registrar_falha("janelas_sistema", codigo, erro=erro)

def pid_from_hwnd(ctypes_mod: Any, wintypes_mod: Any, hwnd: Any) -> int:
    """Obtém o PID de uma janela Windows a partir do HWND."""
    try:
        pid = wintypes_mod.DWORD()
        ctypes_mod.windll.user32.GetWindowThreadProcessId(
            wintypes_mod.HWND(int(hwnd)),
            ctypes_mod.byref(pid),
        )
        return int(pid.value or 0)
    except Exception:
        return 0

def normalizar_alvo_ambiente(nome: str) -> str:
    bruto = str(nome or "").strip().lower()
    bruto = unicodedata.normalize("NFKD", bruto)
    bruto = "".join(c for c in bruto if not unicodedata.combining(c))
    bruto = bruto.replace(".exe", "")
    bruto = re.sub(r"[^\w\s\.-]", " ", bruto)
    bruto = re.sub(r"\s+", " ", bruto).strip()
    return MAPA_NOMES_JANELA.get(bruto, bruto)

def _titulo_janela(janela: Any) -> str:
    try:
        return str(getattr(janela, "title", "") or "").strip()
    except Exception:
        return ""

def _hwnd_da_janela(janela: Any) -> Any:
    for atributo in ("_hWnd", "hWnd", "handle"):
        try:
            valor = getattr(janela, atributo, None)
            if valor is not None:
                return valor
        except Exception:
            continue
    return None

def priorizar_janelas_visiveis(
    janelas: Iterable[Any],
    *,
    janela_ativa: Any = None,
    ctypes_mod: Any = None,
    wintypes_mod: Any = None,
    psutil_mod: Any = None,
    processos_audio: Iterable[str] | None = None,
    instante: float | None = None,
) -> list[dict[str, Any]]:
    """Classifica janelas por foco, áudio, recência e tempo de uso.

    A pontuação usa apenas sinais locais observáveis. O foco sempre vence;
    áudio e uso recente decidem principalmente a janela secundária. Tempo de
    processo tem peso pequeno para um app antigo não dominar para sempre.
    """
    agora = float(time.time() if instante is None else instante)
    historico = snapshot_atividade_janelas()
    audio = {
        str(nome or "").strip().casefold()
        for nome in (processos_audio or ())
        if str(nome or "").strip()
    }
    audio_sem_extensao = {nome.removesuffix(".exe") for nome in audio}
    hwnd_ativo = _hwnd_da_janela(janela_ativa)
    ranking: list[dict[str, Any]] = []

    for janela in list(janelas or []):
        titulo = _titulo_janela(janela)
        hwnd = _hwnd_da_janela(janela)
        chave = _chave_atividade_janela(hwnd=hwnd, titulo=titulo)
        item_historico = dict(historico.get(chave) or {})
        if not item_historico:
            item_historico = dict(historico.get(
                _chave_atividade_janela(titulo=titulo),
            ) or {})

        pid = 0
        executavel = str(item_historico.get("executavel") or "").strip().casefold()
        criado_em = 0.0
        if hwnd is not None and ctypes_mod is not None and wintypes_mod is not None:
            try:
                pid = int(pid_from_hwnd(ctypes_mod, wintypes_mod, hwnd) or 0)
            except Exception:
                pid = 0
        if pid and psutil_mod is not None:
            try:
                processo = psutil_mod.Process(pid)
                executavel = str(processo.name() or executavel).strip().casefold()
                criado_em = float(processo.create_time() or 0.0)
            except Exception:
                pass

        pontuacao = 0.0
        motivos: list[str] = []
        ativa = bool(
            janela is janela_ativa
            or (hwnd is not None and hwnd_ativo is not None and str(hwnd) == str(hwnd_ativo))
        )
        if ativa:
            pontuacao += 1000.0
            motivos.append("janela em foco")

        exe_sem_extensao = executavel.removesuffix(".exe")
        titulo_norm = normalizar_alvo_ambiente(titulo)
        tem_audio = bool(
            executavel in audio
            or exe_sem_extensao in audio_sem_extensao
            or any(nome and nome in titulo_norm for nome in audio_sem_extensao)
        )
        if tem_audio:
            pontuacao += 340.0
            motivos.append("reproduzindo áudio")

        ultimo_foco = float(item_historico.get("ultimo_foco_ts") or 0.0)
        if ultimo_foco:
            idade_foco = max(0.0, agora - ultimo_foco)
            bonus_recencia = max(0.0, 220.0 * (1.0 - idade_foco / 1800.0))
            pontuacao += bonus_recencia
            if bonus_recencia >= 30.0 and not ativa:
                motivos.append("uso recente")

        segundos_foco = max(0.0, float(item_historico.get("segundos_foco") or 0.0))
        ativacoes = max(0, int(item_historico.get("ativacoes") or 0))
        bonus_uso = min(90.0, math.log1p(segundos_foco) * 16.0) + min(40.0, ativacoes * 8.0)
        pontuacao += bonus_uso
        if bonus_uso >= 35.0 and not ativa:
            motivos.append("uso recorrente")

        if criado_em > 0.0:
            tempo_aberto = max(0.0, agora - criado_em)
            bonus_abertura_recente = max(0.0, 80.0 * (1.0 - tempo_aberto / 3600.0))
            bonus_estabilidade = min(25.0, math.log1p(tempo_aberto / 3600.0) * 8.0)
            pontuacao += bonus_abertura_recente + bonus_estabilidade
            if bonus_abertura_recente >= 25.0 and not ativa:
                motivos.append("aberto recentemente")

        largura = max(0, int(getattr(janela, "width", 0) or 0))
        altura = max(0, int(getattr(janela, "height", 0) or 0))
        pontuacao += min(20.0, (largura * altura) / 150000.0)
        ranking.append({
            "janela": janela,
            "titulo": titulo,
            "hwnd": hwnd,
            "pid": pid,
            "executavel": executavel,
            "pontuacao": round(pontuacao, 2),
            "motivos": motivos or ["janela visível"],
            "audio_ativo": tem_audio,
            "ultimo_foco_ts": ultimo_foco,
            "segundos_foco": round(segundos_foco, 2),
            "criado_em": criado_em,
        })

    ranking.sort(
        key=lambda item: (
            float(item.get("pontuacao") or 0.0),
            float(item.get("ultimo_foco_ts") or 0.0),
        ),
        reverse=True,
    )
    return ranking

def planejar_organizacao_janelas(
    gw_mod: Any,
    *,
    ctypes_mod: Any = None,
    wintypes_mod: Any = None,
    psutil_mod: Any = None,
    processos_audio_ativos_cb: Callable[[], Iterable[str]] | None = None,
    registrar_falha: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Observa e prioriza janelas sem mover, focar ou abrir aplicativos."""
    try:
        todas = list(gw_mod.getAllWindows() if gw_mod is not None else [])
    except Exception as erro:
        _relatar_falha_janela(registrar_falha, "enumeracao_layout", erro)
        return {
            "ok": False, "confirmado": False, "status": "falha_enumeracao",
            "quantidade": 0, "nome_esquerda": "", "nome_direita": "",
            "prioridades": [],
        }

    lixo = {normalizar_alvo_ambiente(item) for item in TITULOS_JANELA_LIXO}
    candidatas = []
    for janela in todas:
        titulo = _titulo_janela(janela)
        titulo_norm = normalizar_alvo_ambiente(titulo)
        if (
            not titulo
            or titulo_norm in lixo
            or titulo_norm in TITULOS_AUXILIARES_JANELA
            or titulo_norm == "laylay"
            or titulo_norm.startswith("laylay ")
        ):
            continue
        if getattr(janela, "isMinimized", False):
            continue
        largura = int(getattr(janela, "width", 0) or 0)
        altura = int(getattr(janela, "height", 0) or 0)
        if largura < 180 or altura < 120:
            continue
        candidatas.append(janela)

    try:
        ativa = gw_mod.getActiveWindow() if gw_mod is not None else None
    except Exception:
        ativa = None
    processos_audio: set[str] = set()
    if callable(processos_audio_ativos_cb):
        try:
            processos_audio = set(processos_audio_ativos_cb() or ())
        except Exception as erro:
            _relatar_falha_janela(registrar_falha, "leitura_audio_layout", erro)

    ranking = priorizar_janelas_visiveis(
        candidatas,
        janela_ativa=ativa,
        ctypes_mod=ctypes_mod,
        wintypes_mod=wintypes_mod,
        psutil_mod=psutil_mod,
        processos_audio=processos_audio,
    )
    prioridades = [{
        "titulo": str(item.get("titulo") or ""),
        "pontuacao": float(item.get("pontuacao") or 0.0),
        "motivos": list(item.get("motivos") or []),
    } for item in ranking[:5]]
    if prioridades:
        print(f"🧠 [ORGANIZE:PRIORIDADE] {prioridades}")
    return {
        "ok": bool(ranking),
        "confirmado": True,
        "status": "layout_planejado" if ranking else "sem_janelas_organizaveis",
        "quantidade": len(ranking),
        "nome_esquerda": str(ranking[0].get("titulo") or "") if ranking else "",
        "nome_direita": str(ranking[1].get("titulo") or "") if len(ranking) > 1 else "",
        "prioridades": prioridades,
        # Objetos de janela ficam restritos ao processo e nunca entram no
        # quadro cooperativo, diagnóstico ou memória compartilhada.
        "_janela_esquerda": ranking[0].get("janela") if ranking else None,
        "_janela_direita": ranking[1].get("janela") if len(ranking) > 1 else None,
    }

