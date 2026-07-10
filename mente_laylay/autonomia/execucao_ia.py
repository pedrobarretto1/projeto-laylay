"""Parsing e execucao legada de respostas da IA na Laylay.

Este modulo continua existindo como fallback de compatibilidade enquanto
o roteador modular de conteudo assume o caminho principal.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any, Callable, Dict, Optional, Tuple


def processar_comando_ia(resposta_texto: str, fallback_fala: str) -> Dict[str, Any]:
    raw = str(resposta_texto or "")
    m = re.search(r"\[EXEC:\s*(.*?)\]", raw, flags=re.IGNORECASE | re.DOTALL)
    exec_raw = (m.group(1).strip() if m else "")
    fala = re.sub(r"\[EXEC:.*?\]", " ", raw, flags=re.IGNORECASE | re.DOTALL)
    fala = re.sub(r"\s+", " ", fala).strip() or fallback_fala
    if not exec_raw:
        return {"has_exec": False, "cmd": "", "arg": None, "fala": fala}
    mm = re.match(r"^\s*([A-Z0-9_]+)\s*(?:\((.*)\))?\s*$", exec_raw)
    if not mm:
        return {"has_exec": True, "cmd": exec_raw.upper(), "arg": None, "fala": fala}
    cmd = str(mm.group(1) or "").strip().upper()
    arg_raw = (mm.group(2) or "").strip()
    arg = None
    if arg_raw:
        a = arg_raw
        if a.endswith(","):
            a = a[:-1].strip()
        try:
            if (a.startswith('"') and a.endswith('"')) or (a.startswith("'") and a.endswith("'")):
                arg = ast.literal_eval(a)
            else:
                arg = a
        except Exception:
            arg = a.strip('"').strip("'")
    return {"has_exec": True, "cmd": cmd, "arg": arg, "fala": fala}


def executar_exec(
    cmd: str,
    arg: Any,
    contexto: Dict[str, Any],
) -> bool:
    c = str(cmd or "").strip().upper()
    a = "" if arg is None else str(arg).strip()

    enviar_comando_chrome = contexto.get("enviar_comando_chrome")
    ajustar_volume_sistema = contexto.get("ajustar_volume_sistema")
    abrir_programa = contexto.get("abrir_programa")
    fechar_programa = contexto.get("fechar_programa")
    validar_e_enviar_comando = contexto.get("validar_e_enviar_comando")
    _eh_alvo_site_web = contexto.get("_eh_alvo_site_web")
    _contexto_aponta_site_web = contexto.get("_contexto_aponta_site_web")
    APPS_MAP = contexto.get("APPS_MAP")
    is_valid_url = contexto.get("is_valid_url")
    formatar_url_ou_busca = contexto.get("formatar_url_ou_busca")
    _normalizar_texto_com_apelidos = contexto.get("_normalizar_texto_com_apelidos")
    ctypes = contexto.get("ctypes")
    VK_MEDIA_PLAY_PAUSE = contexto.get("VK_MEDIA_PLAY_PAUSE")
    VK_MEDIA_NEXT_TRACK = contexto.get("VK_MEDIA_NEXT_TRACK")
    VK_MEDIA_PREV_TRACK = contexto.get("VK_MEDIA_PREV_TRACK")

    if c == "YOUTUBE":
        if a and callable(enviar_comando_chrome):
            enviar_comando_chrome("youtube_search", {"query": a})
            return True
        return False

    if c in {"YT_VOLUME", "SET_VOLUME"}:
        try:
            m_vol = re.search(r"\d+", a)
            nivel = int(m_vol.group()) if m_vol else 50
            if callable(ajustar_volume_sistema):
                ajustar_volume_sistema(nivel)
            return True
        except Exception:
            return False

    if c == "OPEN_SITE":
        if not a or not callable(enviar_comando_chrome):
            return False
        url = a
        if callable(is_valid_url) and not is_valid_url(url):
            url = formatar_url_ou_busca(url, prefer_com_br=False) if callable(formatar_url_ou_busca) else url
        enviar_comando_chrome("open_url", {"url": url})
        return True

    if c == "OPEN_APP":
        if not a or len(a) < 2 or not callable(abrir_programa):
            return False
        return bool(abrir_programa(a))

    if c == "FECHAR_PROGRAMA":
        if not a:
            return False
        if callable(_eh_alvo_site_web) and callable(_contexto_aponta_site_web) and (_eh_alvo_site_web(a) or _contexto_aponta_site_web(a)):
            if callable(enviar_comando_chrome):
                enviar_comando_chrome("close_specific_tab", {"target": a})
                return True
        if callable(fechar_programa):
            fechar_programa(a)
            return True
        return False

    if c in ["YT_PAUSE", "YT_PLAY"]:
        if ctypes is None or VK_MEDIA_PLAY_PAUSE is None:
            return False
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 2, 0)
        return True

    if c == "YT_NEXT":
        if ctypes is None or VK_MEDIA_NEXT_TRACK is None:
            return False
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 2, 0)
        return True

    if c == "YT_REPLAY":
        if ctypes is None or VK_MEDIA_PREV_TRACK is None:
            return False
        ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MEDIA_PREV_TRACK, 0, 2, 0)
        return True

    if c == "CLOSE_TAB":
        target = str(arg or "").strip()
        if isinstance(APPS_MAP, dict) and target:
            alvo_norm = target.lower().strip()
            for app in sorted(APPS_MAP.keys(), key=len, reverse=True):
                if alvo_norm == app or app in alvo_norm:
                    if callable(fechar_programa):
                        fechar_programa(APPS_MAP.get(app, target))
                        return True
                    break
        if callable(validar_e_enviar_comando):
            if target and len(target) > 2:
                validar_e_enviar_comando("close_specific_tab", {"target": target})
            else:
                validar_e_enviar_comando("close_current_tab", {})
            return True
        return False

    return False


class ContextoExecRuntime:
    """Coordena o caminho modular e o fallback EXEC com contexto atualizado."""

    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        executar_conteudo_cb: Callable[..., bool],
        executar_legado_cb: Callable[[str, Any, Dict[str, Any]], bool] = executar_exec,
        log: Callable[[str], None] = print,
    ) -> None:
        self.contexto_getter = contexto_getter
        self.executar_conteudo_cb = executar_conteudo_cb
        self.executar_legado_cb = executar_legado_cb
        self.log = log

    def montar_contexto(self, arg: Any) -> Dict[str, Any]:
        contexto = dict(self.contexto_getter() or {})
        contexto["arg"] = arg
        return contexto

    def executar(self, cmd: str, arg: Any) -> bool:
        comando = str(cmd or "").strip()
        c_args = "" if arg is None else str(arg).strip()
        contexto = self.montar_contexto(arg)

        if self.executar_conteudo_cb(
            comando,
            c_args,
            comando,
            comando.upper(),
            contexto,
        ):
            self.log(f"🧠 [EXEC] caminho modular de conteudo assumiu: {comando}")
            return True

        ok_legado = bool(self.executar_legado_cb(cmd, arg, contexto))
        if ok_legado:
            self.log(f"🧩 [EXEC] fallback legado assumiu: {comando}")
        return ok_legado


def criar_contexto_exec_runtime(**kwargs: Any) -> ContextoExecRuntime:
    return ContextoExecRuntime(**kwargs)


def filtrar_apenas_fala(
    texto_bruto: str,
    executar_comando_autonomo_cb: Optional[Callable[[str], Any]] = None,
    fallback_fala: str = "Tô por aqui, Pedro. Me dá só mais um pedaço disso.",
) -> str:
    if not texto_bruto:
        return fallback_fala

    match_cmd = re.search(r"\[COMANDO\]:\s*(.*?)(?:\n|Laylay:|$)", texto_bruto, re.IGNORECASE | re.DOTALL)
    if match_cmd:
        cmd_str = match_cmd.group(1).strip()
        cmd_final = ""
        try:
            lista = ast.literal_eval(cmd_str)
            if isinstance(lista, list):
                cmd_final = " | ".join([str(x).strip() for x in lista])
        except Exception:
            cmd_final = re.sub(r'[\[\]\'"]', '', cmd_str).strip()
        if cmd_final and "NENHUM" not in cmd_final.upper() and callable(executar_comando_autonomo_cb):
            executar_comando_autonomo_cb(cmd_final)

    match_fala = re.search(r"Laylay:\s*(.*)", texto_bruto, re.IGNORECASE | re.DOTALL)
    if match_fala:
        fala = match_fala.group(1).strip()
        return fala or fallback_fala

    fala_limpa = re.sub(r"\[.*?\]:?.*?\n", "", texto_bruto, flags=re.IGNORECASE | re.DOTALL)
    fala_limpa = re.sub(r"\[.*?\]", "", fala_limpa, flags=re.IGNORECASE | re.DOTALL)
    return fala_limpa.strip() or fallback_fala


def parsear_resposta_json(resposta_bruta: str, fallback_fala: str) -> Tuple[str, str]:
    if not resposta_bruta or not isinstance(resposta_bruta, str):
        return fallback_fala, ""
    texto = re.sub(r"```(?:python|json)?", "", resposta_bruta.strip(), flags=re.IGNORECASE).strip()

    fala = ""
    comandos_str = ""

    try:
        dados = ast.literal_eval(texto)
        if isinstance(dados, tuple) and len(dados) >= 2:
            fala = str(dados[0]).strip()
            comandos_raw = dados[1] if isinstance(dados[1], list) else []
            for cmd in comandos_raw:
                if isinstance(cmd, dict):
                    acao = str(cmd.get("acao", "")).strip().upper()
                    alvo = str(cmd.get("alvo", "")).strip()
                    if acao and acao != "NENHUM":
                        comandos_str += f"{acao}('{alvo}')" if alvo else f"{acao}()"
                        comandos_str += " | "
            comandos_str = comandos_str.strip(" | ")
    except Exception:
        pass

    if not fala:
        try:
            data = json.loads(texto)
            fala = str(data.get("fala", fallback_fala)).strip()
            cmds = data.get("comandos", [])
            if isinstance(cmds, list):
                for cmd in cmds:
                    acao = str(cmd.get("acao", "")).strip().upper()
                    alvo = str(cmd.get("alvo", "")).strip()
                    if acao and acao != "NENHUM":
                        comandos_str += f"{acao}('{alvo}')" if alvo else f"{acao}()"
                        comandos_str += " | "
                comandos_str = comandos_str.strip(" | ")
        except Exception:
            pass

    if not fala:
        fala = re.sub(r"\[.*?\]", "", texto, flags=re.DOTALL).strip() or fallback_fala

    return fala, comandos_str
