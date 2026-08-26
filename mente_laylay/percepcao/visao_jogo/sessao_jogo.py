"""Identidade e contexto efêmero da sessão visual de um jogo."""

from __future__ import annotations

import os
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto_basico as _normalizar,
)


_TITULOS_GENERICOS = {
    "", "game", "jogo", "unity", "unreal engine", "directx", "vulkan",
}


def _nome_estavel_por_titulo(titulo: str) -> str:
    """Remove estados transitórios do título sem adivinhar outro jogo."""
    normalizado = _normalizar(titulo)
    if "minecraft" in normalizado:
        return "Minecraft"
    return str(titulo or "").strip()


def confirmar_contexto_janela_sistema(
    contexto: Mapping[str, Any] | None,
    *,
    win32gui_mod: Any = None,
    win32process_mod: Any = None,
    psutil_mod: Any = None,
) -> dict[str, Any]:
    """Relê título e processo do HWND do jogo sem depender da imagem."""
    dados = dict(contexto or {})
    try:
        hwnd = int(dados.get("hwnd") or 0)
    except (TypeError, ValueError):
        hwnd = 0
    if not hwnd:
        return dados
    try:
        if win32gui_mod is None:
            import win32gui as win32gui_mod
        if win32process_mod is None:
            import win32process as win32process_mod
        if psutil_mod is None:
            import psutil as psutil_mod
        if not bool(win32gui_mod.IsWindow(hwnd)):
            return dados
        titulo = str(win32gui_mod.GetWindowText(hwnd) or "").strip()
        _, pid = win32process_mod.GetWindowThreadProcessId(hwnd)
        pid = int(pid or 0)
        if not pid:
            return dados
        processo = psutil_mod.Process(pid)
        executavel = str(processo.name() or "").strip()
        if not executavel:
            return dados
        try:
            caminho = str(processo.exe() or "").strip()
        except Exception:
            caminho = ""
        try:
            hwnd_frente = int(win32gui_mod.GetForegroundWindow() or 0)
            _, pid_frente = win32process_mod.GetWindowThreadProcessId(hwnd_frente)
            em_foco = hwnd_frente == hwnd or int(pid_frente or 0) == pid
        except Exception:
            em_foco = False
        dados.update(
            processo=executavel,
            pid=pid,
            processo_confirmado_sistema=True,
            hwnd_em_foco=bool(em_foco),
        )
        if titulo:
            dados["titulo"] = titulo
        if caminho:
            dados["process_path"] = caminho
    except Exception:
        # A visão continua disponível mesmo se o Windows negar a releitura.
        return dados
    return dados


def identificar_jogo(contexto: Mapping[str, Any] | None) -> dict[str, Any]:
    """Cria uma identidade conservadora usando os sinais já confirmados pelo modo jogo."""
    dados = dict(contexto or {})
    titulo = str(dados.get("titulo") or "").strip()
    processo = str(dados.get("processo") or "").strip()
    processo_nome = os.path.splitext(os.path.basename(processo))[0].strip()
    titulo_norm = _normalizar(titulo)
    processo_norm = _normalizar(processo_nome)
    titulo_util = bool(titulo_norm and titulo_norm not in _TITULOS_GENERICOS)
    processo_util = bool(processo_norm and processo_norm not in _TITULOS_GENERICOS)

    confirmado_sistema = bool(dados.get("processo_confirmado_sistema"))
    if confirmado_sistema and processo_util:
        nome = _nome_estavel_por_titulo(titulo) if titulo_util else processo_nome
        confianca = 0.99
        fonte = "janela_e_processo_sistema"
    elif titulo_util and processo_util:
        nome = titulo
        confianca = 0.86
        fonte = "titulo_e_processo"
    elif titulo_util:
        nome = titulo
        confianca = 0.72
        fonte = "titulo"
    elif processo_util:
        nome = processo_nome
        confianca = 0.64
        fonte = "processo"
    else:
        nome = "jogo não identificado"
        confianca = 0.20
        fonte = "insuficiente"

    # O título da janela pode mudar entre menu, mapa e personagem. O processo
    # é a identidade estável quando é informativo; títulos ficam como fallback
    # para executáveis genéricos como game.exe.
    chave = (
        f"exe:{processo_norm}"
        if processo_util
        else f"titulo:{titulo_norm or '-'}"
    )
    return {
        "chave": chave,
        "nome_candidato": nome,
        "titulo": titulo,
        "processo": processo,
        "process_path": str(dados.get("process_path") or "").strip(),
        "pid": int(dados.get("pid") or 0),
        "hwnd_em_foco": bool(dados.get("hwnd_em_foco")),
        "processo_confirmado_sistema": confirmado_sistema,
        "confianca": confianca,
        "fonte": fonte,
        "confirmado": confirmado_sistema or confianca >= 0.80,
    }


def extrair_perfil_build(texto: str) -> dict[str, Any]:
    """Extrai apenas informações de personagem ditas explicitamente por Pedro."""
    original = str(texto or "").strip()
    normalizado = _normalizar(original)
    perfil: dict[str, Any] = {}
    fim_valor = r"(?=\s+(?:nivel|level|lvl|esse|essa|este|esta)\b|[,;.!?]|$)"
    padroes_build = (
        rf"\bminha build (?:(?:e|eh)\s+(?:de\s+)?|de\s+|focada em\s+)([\w -]{{2,40}}?){fim_valor}",
        rf"\b(?:estou|to) (?:usando|com) (?:uma )?build (?:de )?([\w -]{{2,40}}?){fim_valor}",
    )
    for padrao in padroes_build:
        match = re.search(padrao, normalizado)
        if match:
            perfil["build"] = match.group(1).strip(" -,.!?")
            break
    match_classe = None if re.search(r"\b(?:nao|nunca)\s+sou\b", normalizado) else re.search(
        r"\b(?:minha classe (?:e|eh)|sou (?:um|uma)?|jogo de|"
        r"(?:estou|to) jogando de|(?:estou|to) de)\s*([\w -]{2,35})",
        normalizado,
    )
    if match_classe:
        perfil["classe"] = match_classe.group(1).strip(" -,.!?")
    match_nivel = re.search(r"\b(?:nivel|level|lvl)\s*(\d{1,4})\b", normalizado)
    if match_nivel:
        perfil["nivel"] = int(match_nivel.group(1))
    return perfil


class ContextoSessoesJogo:
    """Mantém build apenas em RAM e isolada pela identidade de cada jogo."""

    def __init__(self, memoria: Any = None) -> None:
        self._perfis: dict[str, dict[str, Any]] = {}
        self._memoria = memoria

    def observar(self, identidade: Mapping[str, Any], texto: str) -> dict[str, Any]:
        chave = str(identidade.get("chave") or "").strip()
        if not chave:
            return {}
        atual = dict(self._perfis.get(chave) or {})
        if not atual and self._memoria is not None:
            try:
                atual.update(self._memoria.carregar_perfil(identidade))
            except Exception:
                pass
        atual.update(extrair_perfil_build(texto))
        if atual:
            self._perfis[chave] = atual
            if self._memoria is not None:
                try:
                    self._memoria.salvar_perfil(identidade, atual)
                except Exception:
                    pass
        return atual

    def perfil(self, identidade: Mapping[str, Any]) -> dict[str, Any]:
        chave = str(identidade.get("chave") or "")
        atual = dict(self._perfis.get(chave) or {})
        if not atual and self._memoria is not None:
            try:
                atual = dict(self._memoria.carregar_perfil(identidade) or {})
                if atual:
                    self._perfis[chave] = atual
            except Exception:
                pass
        return atual
