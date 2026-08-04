"""Ponte leve entre o estado interno da Laylay e seu avatar de tela."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import unicodedata
from typing import Any, Callable, Mapping


_ALIAS_EMOCOES_AVATAR = {
    "neutra": "neutra",
    "neutro": "neutra",
    "neutral": "neutra",
    "idle": "neutra",
    "calma": "calma",
    "tranquila": "calma",
    "tranquilo": "calma",
    "focada": "calma",
    "focado": "calma",
    "suave": "calma",
    "normal": "calma",
    "feliz": "feliz",
    "alegre": "feliz",
    "happy": "feliz",
    "divertida": "feliz",
    "divertido": "feliz",
    "satisfeita": "feliz",
    "animada": "animada",
    "animado": "animada",
    "empolgada": "animada",
    "empolgado": "animada",
    "entusiasmada": "animada",
    "agitada": "animada",
    "agitado": "animada",
    "debochada": "animada",
    "brava": "brava",
    "irritada": "brava",
    "nervosa": "brava",
    "raivosa": "brava",
    "envergonhada": "envergonhada",
    "encabulada": "envergonhada",
    "timida": "envergonhada",
    "corada": "envergonhada",
    "vergonhosa": "envergonhada",
    "triste": "triste",
    "decepcionada": "triste",
    "melancolica": "triste",
    "sad": "triste",
    "surpresa": "surpresa",
    "surpreendida": "surpresa",
    "curiosa": "surpresa",
}

_EMOCOES_CANONICAS_AVATAR = {
    "animada",
    "brava",
    "calma",
    "envergonhada",
    "feliz",
    "surpresa",
    "triste",
}

_ALIAS_ATIVIDADES_AVATAR = {
    "": "idle",
    "idle": "idle",
    "repouso": "idle",
    "quieta": "idle",
    "ouvindo": "listening",
    "escutando": "listening",
    "listening": "listening",
    "pensando": "thinking",
    "preparando": "thinking",
    "thinking": "thinking",
    "executando": "executing",
    "processando": "executing",
    "executing": "executing",
    "falando": "speaking",
    "speaking": "speaking",
    "sucesso": "success",
    "concluido": "success",
    "concluida": "success",
    "success": "success",
    "erro": "error",
    "falha": "error",
    "error": "error",
}


def normalizar_nome_asset(nome: str) -> str:
    texto = unicodedata.normalize("NFKD", str(nome or ""))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return "_".join(parte for parte in "".join(
        ch.casefold() if ch.isalnum() else " " for ch in texto
    ).split() if parte)


def normalizar_emocao_avatar(emocao: str) -> str:
    """Converte o vocabulário expressivo da mente nos quadros disponíveis."""
    chave = normalizar_nome_asset(emocao)
    return _ALIAS_EMOCOES_AVATAR.get(chave, chave or "calma")


def normalizar_atividade_avatar(atividade: str) -> str:
    """Reduz estados operacionais ao vocabulário visual compartilhado."""
    chave = normalizar_nome_asset(atividade)
    return _ALIAS_ATIVIDADES_AVATAR.get(chave, "idle")


def descobrir_assets_avatar(diretorio: str | os.PathLike[str]) -> dict[str, Path]:
    """Cataloga PNGs na raiz ou em uma pasta própria para cada emoção."""
    pasta = Path(diretorio)
    assets: dict[str, Path] = {}
    if not pasta.is_dir():
        return assets

    for caminho in sorted(pasta.rglob("*.png")):
        chave = normalizar_nome_asset(caminho.stem)
        resolvido = caminho.resolve()
        assets.setdefault(chave, resolvido)
        falando = "falando" in chave or "fala" in chave.split("_")

        # A pasta é a fonte mais explícita. Assim, por exemplo,
        # avatar/triste/*falando*.png vira "triste_falando" mesmo que um nome
        # futuro de arquivo seja mais curto. Pastas novas também são aceitas.
        relativa = caminho.relative_to(pasta)
        emocao_pasta = ""
        if len(relativa.parts) > 1:
            emocao_pasta = normalizar_emocao_avatar(relativa.parts[-2])

        emocao = emocao_pasta
        if not emocao:
            for candidata in _EMOCOES_CANONICAS_AVATAR:
                if candidata in chave:
                    emocao = candidata
                    break

        if emocao:
            alias = f"{emocao}_falando" if falando else emocao
            assets.setdefault(alias, resolvido)
        elif falando:
            # Só uma imagem sem emoção associada pode ser fallback de fala.
            # Uma boca de "animada", por exemplo, nunca vaza para "triste".
            assets.setdefault("falando", resolvido)

        if any(marca in chave for marca in ("neutra", "neutro", "neutral", "idle")):
            assets.setdefault("neutra", resolvido)

    return assets


def verificar_quadros_avatar(assets: Mapping[str, Path]) -> tuple[bool, bool]:
    """Informa se há ao menos um quadro parado e um quadro falando."""
    chaves = set(dict(assets or {}))
    tem_falando = "falando" in chaves or any(chave.endswith("_falando") for chave in chaves)
    tem_parado = any(
        chave in {"neutra", "calma"} or chave in _EMOCOES_CANONICAS_AVATAR
        for chave in chaves
        if not chave.endswith("_falando")
    )
    return tem_parado, tem_falando


def calcular_deslocamento_avatar(
    instante: float,
    *,
    falando: bool = False,
    movimento_ativo: bool = True,
) -> int:
    """Calcula um movimento vertical pequeno e barato para dar vida ao avatar."""
    if not movimento_ativo:
        return 0
    t = max(0.0, float(instante))
    if falando:
        # Movimento um pouco mais vivo, sem parecer que a imagem está tremendo.
        deslocamento = math.sin(t * math.tau / 0.56) * 1.15
        deslocamento += math.sin(t * math.tau / 1.70) * 0.55
    else:
        # Respiração lenta: no tamanho padrão, desloca apenas um ou dois pixels.
        deslocamento = math.sin(t * math.tau / 3.8) * 1.5
    return int(round(deslocamento))


def processo_pai_esta_ativo(
    pid: int,
    criado_em: float = 0.0,
    *,
    psutil_mod: Any = None,
) -> bool:
    """Confirma que o processo principal ainda é exatamente o que abriu o avatar."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        if psutil_mod is None:
            import psutil as psutil_importado

            psutil_mod = psutil_importado
        if not bool(psutil_mod.pid_exists(pid)):
            return False
        processo = psutil_mod.Process(pid)
        if not bool(processo.is_running()):
            return False
        status = str(processo.status() or "").casefold()
        if status == str(getattr(psutil_mod, "STATUS_ZOMBIE", "zombie")).casefold():
            return False
        referencia = float(criado_em or 0.0)
        if referencia and abs(float(processo.create_time()) - referencia) > 0.01:
            # O Windows pode reutilizar um PID depois que a Laylay fecha.
            return False
        return True
    except Exception as erro:
        nome_erro = type(erro).__name__
        if nome_erro in {"NoSuchProcess", "ZombieProcess"}:
            return False
        if nome_erro == "AccessDenied":
            # Falta de permissão não significa que o processo morreu.
            return True
        # Uma falha transitória de leitura não deve fechar o avatar por engano.
        return True


def resolver_asset_avatar(
    assets: Mapping[str, Path],
    emocao: str,
    *,
    falando: bool = False,
) -> Path:
    """Escolhe um quadro com fallback determinístico e preparado para novas bocas."""
    catalogo = dict(assets or {})
    if not catalogo:
        raise LookupError("catálogo do avatar vazio")
    emocao_canonica = normalizar_emocao_avatar(emocao)
    if falando:
        for chave in (
            f"{emocao_canonica}_falando",
            f"falando_{emocao_canonica}",
            "falando",
        ):
            if chave in catalogo:
                return catalogo[chave]
    for chave in (emocao_canonica, "calma", "neutra"):
        if chave in catalogo:
            return catalogo[chave]
    return next(iter(catalogo.values()))


def normalizar_estado_avatar(estado: Mapping[str, Any] | None) -> dict[str, Any]:
    dados = dict(estado or {})
    emocao = normalizar_emocao_avatar(str(dados.get("emotion") or dados.get("emocao") or "calma"))
    try:
        nivel = max(0, min(3, int(dados.get("level", dados.get("nivel", 1)))))
    except (TypeError, ValueError):
        nivel = 1
    falando = bool(dados.get("speaking", dados.get("falando", False)))
    atividade = normalizar_atividade_avatar(
        str(dados.get("activity") or dados.get("atividade") or "")
    )
    if falando:
        atividade = "speaking"
    try:
        intensidade = max(0.0, min(1.0, float(
            dados.get("intensity", dados.get("intensidade", nivel / 3.0))
        )))
    except (TypeError, ValueError):
        intensidade = max(0.0, min(1.0, nivel / 3.0))
    return {
        "type": "state",
        "emotion": emocao or "calma",
        "level": nivel,
        "speaking": falando,
        "activity": atividade,
        "intensity": round(intensidade, 3),
        "reaction_id": str(dados.get("reaction_id") or dados.get("reacao_id") or "")[:80],
    }


class AvatarRuntime:
    """Inicia o overlay isolado e publica somente mudanças visuais via UDP local."""

    def __init__(
        self,
        *,
        raiz_projeto: str | os.PathLike[str],
        estado_getter: Callable[[], Mapping[str, Any]],
        log: Callable[[str], Any] = print,
        env_getter: Callable[[str, str], str] = os.getenv,
        popen: Callable[..., Any] = subprocess.Popen,
        intervalo: float = 0.10,
        heartbeat: float = 1.0,
        visual_externo_disponivel: Callable[[], bool] | None = None,
        registrar_falha: Callable[..., Any] | None = None,
    ) -> None:
        self.raiz_projeto = Path(raiz_projeto).resolve()
        self.estado_getter = estado_getter
        self.log = log
        self.env_getter = env_getter
        self.popen = popen
        self.intervalo = max(0.05, float(intervalo))
        self.heartbeat = max(0.5, float(heartbeat))
        self.visual_externo_disponivel = visual_externo_disponivel
        self.registrar_falha = registrar_falha
        self._processo: Any = None
        self._socket: socket.socket | None = None
        self._porta: int | None = None
        self._thread: threading.Thread | None = None
        self._monitor_thread: threading.Thread | None = None
        self._controle_lock = threading.RLock()
        self._oculto_por_externo = False
        self._parar = threading.Event()

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("avatar", codigo, erro=erro)

    def ativo(self) -> bool:
        # A interface desktop é a fonte explícita desta preferência. Ausência
        # significa desligado: iniciar a Laylay nunca deve abrir um mascote por
        # surpresa. A chave antiga continua funcionando como bloqueio mestre.
        mascote = str(
            self.env_getter("LAYLAY_MASCOT_ENABLED", "0") or ""
        ).strip().casefold()
        legado = str(
            self.env_getter("LAYLAY_AVATAR_ATIVO", "1") or ""
        ).strip().casefold()
        falsos = {"0", "false", "nao", "não", "off", "desligado", ""}
        return mascote not in falsos and legado not in falsos

    def iniciar(self) -> bool:
        if not self.ativo():
            return False
        if (
            self._processo is not None and self._processo.poll() is None
        ) or (
            self._monitor_thread is not None and self._monitor_thread.is_alive()
        ):
            return True

        pasta_assets = self.raiz_projeto / "avatar"
        assets = descobrir_assets_avatar(pasta_assets)
        tem_parado, tem_falando = verificar_quadros_avatar(assets)
        faltando = []
        if not tem_parado:
            faltando.append("imagem parada")
        if not tem_falando:
            faltando.append("imagem falando")
        script = self.raiz_projeto / "cliente" / "avatar_laylay.py"
        executavel_avatar = self.raiz_projeto / "AvatarLaylay.exe"
        recurso_avatar = executavel_avatar if getattr(sys, "frozen", False) else script
        if faltando or not recurso_avatar.is_file():
            detalhe = ", ".join(faltando) if faltando else str(recurso_avatar)
            self.log(f"⚠️ [AVATAR] Não iniciado; recurso ausente: {detalhe}")
            return False

        self._parar.clear()
        externo = self._visual_externo_ativo()
        self._oculto_por_externo = externo
        if externo:
            self.log("✨ [AVATAR] Widget fixado ativo; avatar Python mantido oculto.")
            iniciado = True
        else:
            iniciado = self._iniciar_janela(pasta_assets, script)
        if self.visual_externo_disponivel is not None:
            self._monitor_thread = threading.Thread(
                target=self._monitorar_preferencia_visual,
                args=(pasta_assets, script),
                name="Laylay-Avatar-Preferencia",
                daemon=True,
            )
            self._monitor_thread.start()
        return iniciado

    def _iniciar_janela(self, pasta_assets: Path, script: Path) -> bool:
        with self._controle_lock:
            if self._parar.is_set():
                return False
            if self._processo is not None and self._processo.poll() is None:
                return True
            self._porta = self._reservar_porta_local()
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tamanho = str(self.env_getter("LAYLAY_AVATAR_TAMANHO", "230") or "230")
        pid_pai = os.getpid()
        criado_em_pai = 0.0
        try:
            import psutil

            criado_em_pai = float(psutil.Process(pid_pai).create_time())
        except Exception:
            pass
        comando = [
            *(
                [str(self.raiz_projeto / "AvatarLaylay.exe")]
                if getattr(sys, "frozen", False)
                else [sys.executable, str(script)]
            ),
            "--port",
            str(self._porta),
            "--assets",
            str(pasta_assets),
            "--state-file",
            str(self.raiz_projeto / "memoria" / "avatar_estado.json"),
            "--size",
            tamanho,
            "--parent-pid",
            str(pid_pai),
            "--parent-started",
            str(criado_em_pai),
        ]
        kwargs: dict[str, Any] = {"cwd": str(self.raiz_projeto)}
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self._processo = self.popen(comando, **kwargs)
        except Exception as erro:
            self.log(f"⚠️ [AVATAR] Não foi possível abrir a janela: {erro}")
            self._relatar("abertura_janela", erro)
            self._fechar_socket()
            return False

        self._oculto_por_externo = False
        self._thread = threading.Thread(
            target=self._publicar_estado,
            name="Laylay-Avatar-Estado",
            daemon=True,
        )
        self._thread.start()
        self.log("✨ [AVATAR] Laylay apareceu no canto da tela.")
        return True

    def parar(self, timeout_s: float = 1.5) -> None:
        prazo = time.monotonic() + max(0.0, float(timeout_s))
        self._parar.set()
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=max(0.0, prazo - time.monotonic()))
        self._fechar_janela(timeout_s=max(0.0, prazo - time.monotonic()))
        self._monitor_thread = None

    def _fechar_janela(self, timeout_s: float = 1.5) -> None:
        prazo = time.monotonic() + max(0.0, float(timeout_s))
        with self._controle_lock:
            self._enviar({"type": "shutdown"})
            processo = self._processo
            if processo is not None and processo.poll() is None:
                try:
                    processo.wait(timeout=max(0.0, prazo - time.monotonic()))
                except subprocess.TimeoutExpired:
                    try:
                        processo.terminate()
                    except OSError as erro:
                        self._relatar("encerramento_processo", erro)
            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=max(0.0, prazo - time.monotonic()))
            self._fechar_socket()
            self._processo = None
            self._thread = None

    def _visual_externo_ativo(self) -> bool:
        if self.visual_externo_disponivel is None:
            return False
        try:
            return bool(self.visual_externo_disponivel())
        except Exception as erro:
            self._relatar("visual_externo", erro)
            return False

    def _monitorar_preferencia_visual(self, pasta_assets: Path, script: Path) -> None:
        while not self._parar.wait(0.20):
            externo = self._visual_externo_ativo()
            processo_ativo = bool(
                self._processo is not None and self._processo.poll() is None
            )
            if externo and processo_ativo:
                self._oculto_por_externo = True
                self._fechar_janela()
                self.log("✨ [AVATAR] Widget fixado assumiu a tela; avatar Python ocultado.")
            elif not externo and self._oculto_por_externo and not processo_ativo:
                # Se o widget for fechado ou desafixado, o avatar comum volta
                # automaticamente. Fechar o Tk manualmente não causa relançamento.
                self._iniciar_janela(pasta_assets, script)

    @staticmethod
    def _reservar_porta_local() -> int:
        temporario = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            temporario.bind(("127.0.0.1", 0))
            return int(temporario.getsockname()[1])
        finally:
            temporario.close()

    def _publicar_estado(self) -> None:
        ultimo: dict[str, Any] | None = None
        ultimo_envio = 0.0
        while not self._parar.wait(self.intervalo):
            if self._processo is not None and self._processo.poll() is not None:
                if not self._parar.is_set():
                    self.log("⚠️ [AVATAR] A janela foi fechada; a Laylay continua funcionando.")
                return
            try:
                atual = normalizar_estado_avatar(self.estado_getter())
            except Exception as erro:
                self.log(f"⚠️ [AVATAR] Estado visual indisponível: {erro}")
                self._relatar("estado_visual", erro)
                continue
            agora = time.monotonic()
            if atual != ultimo or agora - ultimo_envio >= self.heartbeat:
                if self._enviar(atual):
                    ultimo = atual
                    ultimo_envio = agora

    def _enviar(self, mensagem: Mapping[str, Any]) -> bool:
        if self._socket is None or self._porta is None:
            return False
        try:
            dados = json.dumps(dict(mensagem), ensure_ascii=False).encode("utf-8")
            self._socket.sendto(dados, ("127.0.0.1", self._porta))
            return True
        except OSError as erro:
            self._relatar("envio_udp", erro)
            return False

    def _fechar_socket(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
        self._socket = None


def criar_avatar_runtime(**kwargs: Any) -> AvatarRuntime:
    return AvatarRuntime(**kwargs)
