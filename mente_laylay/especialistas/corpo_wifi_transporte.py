"""Configuração local e fluxo TCP autenticado; decisões e receipts pertencem ao corpo."""
from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import IPv4Address
import json
from pathlib import Path
import re
import socket
import time


CAMINHO_CONFIGURACAO_WIFI = Path(__file__).resolve().parents[2] / "memoria" / "corpo_wifi.json"


class ConfiguracaoCorpoWifiInvalida(ValueError):
    """Não inclui o conteúdo do arquivo nem a credencial na mensagem."""


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
        conexao.connect((configuracao.host, configuracao.porta))
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
