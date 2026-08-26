"""Modo jogo conservador para preservar GPU sem desligar a mente da Laylay."""

from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from typing import Any, Callable


PROCESSOS_NAO_JOGO = {
    "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe", "brave.exe",
    "vivaldi.exe", "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe",
    "epicwebhelper.exe", "goggalaxy.exe", "battle.net.exe", "riotclientservices.exe",
    "lunar client.exe", "discord.exe", "spotify.exe", "vlc.exe", "obs64.exe",
    "code.exe", "pycharm64.exe", "devenv.exe", "explorer.exe", "applicationframehost.exe",
    "photoshop.exe", "illustrator.exe", "afterfx.exe", "premiere pro.exe", "blender.exe",
    "resolve.exe", "fusion360.exe", "freecad.exe", "cura.exe", "acrobat.exe",
    "winword.exe", "excel.exe", "powerpnt.exe", "notepad.exe", "notepad++.exe",
}

EXECUTAVEIS_JOGO_CONHECIDOS = {
    "minecraft.exe", "minecraft.windows.exe", "javaw.exe",
    "gta5.exe", "rdr2.exe", "cs2.exe", "valorant-win64-shipping.exe",
    "fortniteclient-win64-shipping.exe", "rocketleague.exe", "eldenring.exe",
    "overwatch.exe", "league of legends.exe", "dota2.exe", "hl2.exe",
    "terraria.exe", "stardew valley.exe", "cyberpunk2077.exe",
}

MARCADORES_TITULO_JOGO = {
    "minecraft", "valorant", "fortnite", "rocket league", "counter-strike",
    "grand theft auto", "gta v", "red dead redemption", "elden ring",
    "league of legends", "overwatch", "terraria", "stardew valley",
}

PASTAS_INSTALACAO_JOGO = (
    "\\steamapps\\common\\",
    "\\epic games\\",
    "\\riot games\\",
    "\\xboxgames\\",
    "\\gog galaxy\\games\\",
    "\\jogos\\",
    "\\games\\",
)


def pedido_foco_explicito(texto: str) -> bool:
    """Distingue abrir em segundo plano de um pedido real para trocar a tela."""
    t = str(texto or "").casefold().strip()
    return bool(re.search(
        r"(?:\bem foco\b|\bdar foco\b|\bpra frente\b|\bpara frente\b|"
        r"\btroca(?:r)? (?:pra|para) (?:a )?(?:aba|janela)\b|"
        r"\bvai (?:pra|para) (?:a )?(?:aba|janela)\b|\bmostra(?:r)? (?:a )?(?:aba|janela)\b|"
        r"\bmaximiza(?:r)?\b|\btela cheia\b|\bfullscreen\b)",
        t,
    ))


def processo_parece_jogo(
    executavel: str,
    titulo: str = "",
    caminho: str = "",
    *,
    memoria_mb: float = 0.0,
    linha_comando: str = "",
) -> bool:
    """Classifica apenas com evidência forte; navegador e launcher sempre perdem."""
    exe = os.path.basename(str(executavel or caminho or "")).casefold().strip()
    titulo_norm = str(titulo or "").casefold().strip()
    caminho_norm = str(caminho or "").replace("/", "\\").casefold()
    if not exe or exe in PROCESSOS_NAO_JOGO:
        return False

    if exe in EXECUTAVEIS_JOGO_CONHECIDOS:
        # javaw é genérico e só conta como jogo quando a janela confirma.
        return exe != "javaw.exe" or any(marcador in titulo_norm for marcador in MARCADORES_TITULO_JOGO)
    if any(pasta in caminho_norm for pasta in PASTAS_INSTALACAO_JOGO):
        return True
    if exe.endswith("-win64-shipping.exe") or exe.endswith("-win32-shipping.exe"):
        return True
    if any(marcador in titulo_norm for marcador in MARCADORES_TITULO_JOGO):
        return True

    # Jogos independentes nem sempre vivem em uma loja conhecida. Para eles,
    # combinamos sinais em vez de confiar apenas em tela cheia. Isso reconhece
    # executáveis como Soulframe.x64.exe sem transformar qualquer aplicativo
    # pesado em jogo.
    pontos = 0
    try:
        if float(memoria_mb or 0.0) >= 768.0:
            pontos += 1
    except (TypeError, ValueError):
        pass
    nome_base = exe.removesuffix(".exe").replace(".x64", "").replace("_x64", "").strip()
    if len(nome_base) >= 4 and nome_base in titulo_norm:
        pontos += 1
    comando = str(linha_comando or "").casefold()
    sinais_graficos = (
        "graphicsdriver", "gpupreference", "-dx11", "-dx12", "-d3d11", "-d3d12",
        "vulkan", "windowmode", "shadercache", "fullscreen",
    )
    if any(sinal in comando for sinal in sinais_graficos):
        pontos += 2
    if exe.endswith((".x64.exe", "_x64.exe", "64-shipping.exe")):
        pontos += 1
    return pontos >= 3


def descarregar_modelo_ollama(
    modelo: str,
    *,
    executar: Callable[..., Any] = subprocess.run,
) -> bool:
    modelo = str(modelo or "").strip()
    if not modelo:
        return False
    kwargs: dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": 12,
        "check": False,
    }
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        resultado = executar(["ollama", "stop", modelo], **kwargs)
        return int(getattr(resultado, "returncode", 1) or 0) == 0
    except (OSError, subprocess.SubprocessError):
        return False


class ModoJogoRuntime:
    """Confirma entrada/saída do jogo e controla apenas o consumidor de GPU."""

    def __init__(
        self,
        *,
        definir_bloqueio_llm: Callable[[bool], Any],
        descarregar_modelo: Callable[[], bool],
        llm_em_andamento: Callable[[], bool] | None = None,
        preparar_overlays: Callable[[dict[str, Any]], Any] | None = None,
        habilitado: bool = True,
        clock: Callable[[], float] = time.monotonic,
        entrada_estavel_s: float = 4.0,
        tolerancia_saida_s: float = 45.0,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.definir_bloqueio_llm = definir_bloqueio_llm
        self.descarregar_modelo = descarregar_modelo
        self.llm_em_andamento = llm_em_andamento or (lambda: False)
        self.preparar_overlays = preparar_overlays
        self.habilitado = bool(habilitado)
        self.clock = clock
        self.entrada_estavel_s = max(0.0, float(entrada_estavel_s))
        self.tolerancia_saida_s = max(0.0, float(tolerancia_saida_s))
        self.log = log
        self._lock = threading.RLock()
        self._ativo = False
        self._candidato_desde: float | None = None
        self._ultimo_jogo_visto = 0.0
        self._processo_jogo = ""
        self._titulo_jogo = ""
        self._hwnd_jogo = 0
        self._pid_jogo = 0
        self._caminho_jogo = ""
        self._limites_jogo: dict[str, int] = {}

    @property
    def ativo(self) -> bool:
        with self._lock:
            return self._ativo

    def contexto_atual(self) -> dict[str, Any]:
        """Expõe o jogo recente mesmo quando uma barra/terminal toma o foco."""
        with self._lock:
            return {
                "ativo": self._ativo,
                "processo": self._processo_jogo,
                "titulo": self._titulo_jogo,
                "visto_em": self._ultimo_jogo_visto,
                "hwnd": self._hwnd_jogo,
                "pid": self._pid_jogo,
                "process_path": self._caminho_jogo,
                "limites": dict(self._limites_jogo),
            }

    def observar(self, retrato: dict[str, Any] | None, fullscreen: bool) -> dict[str, Any]:
        retrato = dict(retrato or {})
        agora = float(self.clock())
        exe = str(retrato.get("exe") or "")
        jogo_confirmado = bool(
            self.habilitado
            and fullscreen
            and processo_parece_jogo(
                exe,
                retrato.get("title", ""),
                retrato.get("process_path", ""),
                memoria_mb=retrato.get("process_memory_mb", 0.0),
                linha_comando=retrato.get("process_cmdline", ""),
            )
        )
        with self._lock:
            if jogo_confirmado:
                self._ultimo_jogo_visto = agora
                self._processo_jogo = exe
                self._titulo_jogo = str(retrato.get("title") or "").strip()
                self._hwnd_jogo = int(retrato.get("hwnd") or 0)
                self._pid_jogo = int(retrato.get("pid") or 0)
                self._caminho_jogo = str(retrato.get("process_path") or "").strip()
                janela = retrato.get("win")
                limites = {
                    "left": int(retrato.get("left") or getattr(janela, "left", 0) or 0),
                    "top": int(retrato.get("top") or getattr(janela, "top", 0) or 0),
                    "width": int(retrato.get("width") or getattr(janela, "width", 0) or 0),
                    "height": int(retrato.get("height") or getattr(janela, "height", 0) or 0),
                }
                if limites["width"] > 0 and limites["height"] > 0:
                    self._limites_jogo = limites
                if self._candidato_desde is None:
                    self._candidato_desde = agora
                try:
                    entrada_urgente = bool(self.llm_em_andamento())
                except Exception:
                    entrada_urgente = False
                if not self._ativo and (
                    entrada_urgente
                    or agora - self._candidato_desde >= self.entrada_estavel_s
                ):
                    self._ativo = True
                    self.definir_bloqueio_llm(True)
                    liberou = bool(self.descarregar_modelo())
                    self.log(
                        f"🎮 [MODO JOGO] ativo para {exe}"
                        f"{' com entrada urgente' if entrada_urgente else ''}; IA local pausada e "
                        f"VRAM {'liberada' if liberou else 'solicitada para liberação'}."
                    )
                # A adaptação pode falhar se o jogo trocar de HWND ou estiver
                # recriando o swapchain naquele instante. O runtime possui
                # backoff e deduplicação, então observar novamente é seguro.
                if self._ativo and callable(self.preparar_overlays):
                    try:
                        self.preparar_overlays(retrato)
                    except Exception as erro:
                        self.log(
                            "⚠️ [OVERLAY JOGO] compatibilidade ignorada: "
                            f"{type(erro).__name__}"
                        )
            else:
                self._candidato_desde = None
                if self._ativo and agora - self._ultimo_jogo_visto >= self.tolerancia_saida_s:
                    anterior = self._processo_jogo
                    self._ativo = False
                    self._processo_jogo = ""
                    self._titulo_jogo = ""
                    self._hwnd_jogo = 0
                    self._pid_jogo = 0
                    self._caminho_jogo = ""
                    self._limites_jogo = {}
                    self.definir_bloqueio_llm(False)
                    self.log(
                        f"🎮 [MODO JOGO] encerrado após sair de {anterior}; IA local disponível sob demanda."
                    )
            return {
                "ativo": self._ativo,
                "jogo_confirmado": jogo_confirmado,
                "processo": self._processo_jogo,
            }


def criar_modo_jogo_runtime(**kwargs: Any) -> ModoJogoRuntime:
    return ModoJogoRuntime(**kwargs)
