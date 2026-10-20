"""Configuração local e fluxo TCP autenticado; decisões e receipts pertencem ao corpo."""
from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import IPv4Address
import json
from pathlib import Path
import re
import socket
import time
import os
import subprocess
from typing import Any


CAMINHO_CONFIGURACAO_WIFI = Path(__file__).resolve().parents[2] / "memoria" / "corpo_wifi.json"


class RedeLocalCorpoWindows:
    """Reutiliza o gerente de rede já provisionado; não altera a rede principal."""

    def __init__(self, raiz: Path | None = None) -> None:
        self.raiz = raiz or CAMINHO_CONFIGURACAO_WIFI.parents[1]
        self._processo: Any = None
        self._nova_tentativa_em = 0.0

    def preparar(self, configuracao: ConfiguracaoCorpoWifi) -> None:
        arquivo = self.raiz / 'memoria' / 'corpo_hotspot_windows.json'
        script = self.raiz / 'scripts' / 'hotspot_corpo_windows.ps1'
        if (os.name != 'nt' or not configuracao.host.startswith('192.168.137.')
                or not arquivo.is_file() or not script.is_file()):
            return
        perfil = json.loads(arquivo.read_text(encoding='utf-8-sig'))
        if perfil.get('modo') != 'hosted_network_temporario' or perfil.get('ssid') != 'Laylay-Corpo-PC':
            return
        recibo = self.raiz / 'artifacts' / 'rosto_oled' / 'wifi' / 'hotspot_windows.json'
        import psutil

        def pronto(pid: int | None = None) -> bool:
            try:
                r = json.loads(recibo.read_text(encoding='utf-8-sig'))
                if r.get('estado') != 'ativo' or r.get('conexao_original_preservada') is not True:
                    return False
                if pid is not None and r.get('pid') != pid:
                    return False
                processo = psutil.Process(int(r['pid']))
                return processo.name().casefold() == 'powershell.exe' and any(
                    Path(a).resolve() == script.resolve() for a in processo.cmdline() if a.casefold().endswith('.ps1'))
            except (OSError, ValueError, KeyError, psutil.Error):
                return False

        if pronto():
            return
        if time.monotonic() < self._nova_tentativa_em:
            raise ConnectionError('aguardando_rede_local_corpo')
        self._nova_tentativa_em = time.monotonic() + 30
        self._processo = subprocess.Popen(['powershell.exe', '-NoProfile', '-ExecutionPolicy',
            'Bypass', '-File', str(script)], cwd=str(self.raiz),
            creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        prazo = time.monotonic() + 8
        while time.monotonic() < prazo and self._processo.poll() is None:
            if pronto(self._processo.pid):
                return
            time.sleep(.1)
        raise ConnectionError('rede_local_corpo_nao_confirmada')

    def encerrar(self) -> None:
        if self._processo is not None and self._processo.poll() is None:
            (self.raiz / 'memoria' / 'corpo_hotspot_windows.parar').write_text('parar', encoding='ascii')
            try:
                self._processo.wait(timeout=3)
            except subprocess.TimeoutExpired:
                pass


class ConfiguracaoCorpoWifiInvalida(ValueError):
    """Não inclui o conteúdo do arquivo nem a credencial na mensagem."""


class ConexaoCorpoIndisponivel(ConnectionError):
    """Falha antes da autenticação; permite preparar a rede local existente."""


@dataclass(frozen=True)
class ConfiguracaoCorpoWifi:
    host: str
    porta: int
    token: str = field(repr=False)
    hostname: str = "laylay-corpo.local"

    def __post_init__(self) -> None:
        try:
            valido = (
                type(self.host) is str and str(IPv4Address(self.host)) == self.host
                and type(self.porta) is int and 1 <= self.porta <= 65535
                and type(self.token) is str and re.fullmatch(r"[a-fA-F0-9]{64}", self.token) is not None
                and self.hostname == "laylay-corpo.local"
            )
        except (ValueError, TypeError):
            valido = False
        if not valido:
            raise ConfiguracaoCorpoWifiInvalida("configuracao_wifi_invalida")

    @property
    def endpoint(self) -> str:
        return f"{self.host}:{self.porta}"


def carregar_configuracao_corpo_wifi(caminho: Path | str) -> ConfiguracaoCorpoWifi | None:
    """Ausente/desativada preserva USB; qualquer arquivo inválido falha fechado."""
    caminho = Path(caminho)
    try:
        if not caminho.exists():
            return None
        # Um arquivo de provisionamento é pequeno. Não ler conteúdo arbitrário.
        if caminho.stat().st_size > 4096:
            raise ConfiguracaoCorpoWifiInvalida("configuracao_wifi_invalida")
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if (type(dados) is not dict or type(dados.get("version")) is not int
                or dados["version"] != 1 or type(dados.get("ativo")) is not bool):
            raise ConfiguracaoCorpoWifiInvalida("configuracao_wifi_invalida")
        if not dados["ativo"]:
            return None
        return ConfiguracaoCorpoWifi(host=dados.get("host"), porta=dados.get("porta"),
                                    token=dados.get("token"), hostname=dados.get("hostname"))
    except (OSError, ValueError, TypeError, UnicodeError):
        raise ConfiguracaoCorpoWifiInvalida("configuracao_wifi_invalida") from None


class FluxoCorpoTcp:
    """A mesma interface read/write/close da USB; EOF nunca significa timeout."""
    def __init__(self, conexao: socket.socket) -> None:
        self._conexao = conexao
        self._conexao.settimeout(.1)

    def read(self, quantidade: int) -> bytes:
        try:
            dados = self._conexao.recv(quantidade)
        except socket.timeout:
            return b""
        except OSError:
            raise ConnectionError("conexao_corpo_encerrada") from None
        if not dados:
            raise ConnectionError("conexao_corpo_encerrada")
        return dados

    def write(self, dados: bytes) -> int:
        try:
            self._conexao.sendall(dados)
        except socket.timeout:
            raise TimeoutError("escrita_corpo_expirada") from None
        except OSError:
            raise ConnectionError("escrita_corpo_falhou") from None
        return len(dados)

    def close(self) -> None:
        self._conexao.close()


def abrir_corpo_tcp(configuracao: ConfiguracaoCorpoWifi) -> FluxoCorpoTcp:
    """Abre IPv4 sem DNS e autentica antes de entregar o fluxo ao owner do protocolo."""
    conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        conexao.settimeout(.8)
        try:
            conexao.connect((configuracao.host, configuracao.porta))
        except OSError:
            raise ConexaoCorpoIndisponivel('conexao_corpo_indisponivel') from None
        conexao.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        fluxo = FluxoCorpoTcp(conexao)
        fluxo.write(f"AUTH 1 {configuracao.token}\n".encode("ascii"))
        prazo = time.monotonic() + .8
        recebido = bytearray()
        while time.monotonic() < prazo:
            recebido.extend(fluxo.read(128))
            if len(recebido) > 128:
                raise ConnectionError("autenticacao_corpo_rejeitada")
            if b"\n" in recebido:
                linha, _, restante = recebido.partition(b"\n")
                if linha.rstrip(b"\r") != b"AUTH_OK 1" or restante:
                    raise ConnectionError("autenticacao_corpo_rejeitada")
                return fluxo
        raise TimeoutError("autenticacao_corpo_expirada")
    except Exception as erro:
        conexao.close()
        if isinstance(erro, (ConnectionError, TimeoutError)):
            raise
        raise ConnectionError("conexao_corpo_falhou") from None
