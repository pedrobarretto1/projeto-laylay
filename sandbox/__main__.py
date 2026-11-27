"""Bancada local do corpo da Laylay. Execute com `python -m sandbox`."""

import argparse
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
from socketserver import BaseRequestHandler, ThreadingTCPServer
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event, Lock, Thread
import time
from urllib.parse import parse_qs, urlsplit
import webbrowser

from .bancada import Cena
from .firmware_host import Firmware, compilar


PASTA = Path(__file__).resolve().parent


def ambiente_laylay_virtual(porta: int, token: bytes) -> dict[str, str]:
    return {**os.environ, "LAYLAY_CORPO_SIMULADOR_PORTA": str(porta),
            "LAYLAY_CORPO_SIMULADOR_SESSAO": token.hex(), "LAYLAY_ROSTO_PORTA": "CORPO_VIRTUAL",
            "LAYLAY_CORPO_COMPANHIA_BANCADA_AO_INICIAR": "1", "LAYLAY_CORPO_PASSEIO_BANCADA_AO_INICIAR": "1",
            "LAYLAY_CORPO_PWM_MINIMO": "170", "LAYLAY_CORPO_PWM_MAXIMO": "255"}


class Bancada:
    def __init__(self, sketch: Path, pasta: Path, *, preservar_edicao: bool = True) -> None:
        self.cena = Cena()
        self.lock = Lock()
        self.parar = Event()
        self.pasta = pasta
        self.sketch = pasta / "firmware_edicao/rosto_laylay"
        if not self.sketch.exists() or not preservar_edicao:
            if self.sketch.exists():
                raise ValueError("A cópia editável já existe.")
            self.sketch.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=self.sketch.parent) as temp:
                copia = Path(temp) / self.sketch.name
                shutil.copytree(sketch, copia, ignore=shutil.ignore_patterns("*.obj", "*.pdb", "*.exe"))
                for ajuste in ("firmware_posturas.patch", "firmware_busca.patch", "firmware_expressao.patch"):
                    resultado = subprocess.run(["git", "apply", "--no-index", "--ignore-space-change",
                                                str(PASTA / ajuste)], cwd=copia,
                                               capture_output=True, text=True, errors="replace", timeout=15)
                    if resultado.returncode:
                        raise RuntimeError(f"Não consegui aplicar {ajuste} ao firmware da bancada.\n{resultado.stderr}")
                copia.rename(self.sketch)
        self.arquivos = sorted(p.name for p in self.sketch.iterdir() if p.is_file() and p.suffix in {".h", ".ino"})
        self.token = secrets.token_bytes(32)
        self.cliente: socket.socket | None = None
        self.medidas = {"conectado": False, "frente_mm": None, "frente_estado": "AGUARDANDO", "imu": "AGUARDANDO", "protecao": "AGUARDANDO",
                        "manuseio_fase": "",
                        "pwm_esq": 0, "pwm_dir": 0, "oled": "", "ultima_linha": ""}
        self.estado_build, self.log_build = "compilando", ""
        self.firmware: Firmware | None = None
        self._compilar()
        self._thread = Thread(target=self._atualizar, daemon=True)
        self._thread.start()

    def _soltar_cliente(self) -> None:
        if self.cliente is not None:
            try:
                self.cliente.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.cliente = None

    def _compilar(self) -> None:
        destino = self.pasta / "build" / secrets.token_hex(6)
        try:
            exe, log = compilar(self.sketch, destino)
            novo = Firmware(exe)
        except (RuntimeError, OSError, subprocess.SubprocessError) as erro:
            with self.lock:
                self.estado_build, self.log_build = "erro", str(erro)[:20000]
            return
        with self.lock:
            if self.parar.is_set():
                novo.fechar()
                return
            self._soltar_cliente()
            if self.firmware:
                self.firmware.fechar()
            self.firmware = novo
            self.medidas.update(pwm_esq=0, pwm_dir=0, oled="", imu="AGUARDANDO", manuseio_fase="", ultima_linha="")
            self.estado_build, self.log_build = "aplicado", log[:20000]

    def recompilar(self) -> None:
        with self.lock:
            if self.estado_build == "compilando":
                raise ValueError("Já existe uma compilação em andamento.")
            self.estado_build, self.log_build = "compilando", ""
        Thread(target=self._compilar, daemon=True).start()

    def _serial(self, linhas: list[str]) -> None:
        for linha in linhas:
            modo, _, valor = linha.partition(" ")
            if modo == "R":
                if valor.startswith(("HAZARD", "PROTECT", "TURNEND", "ERROR", "MACK", "PWM")):
                    self.medidas["ultima_linha"] = valor
                if self.cliente is not None:
                    try:
                        self.cliente.sendall((valor + "\n").encode("ascii"))
                    except OSError:
                        self._soltar_cliente()
            elif modo == "E":
                esq, direita, frente, estado_frente, imu, protecao = valor.split()
                self.medidas.update(pwm_esq=int(esq), pwm_dir=int(direita), frente_mm=None if frente == "-1" else int(frente),
                                    frente_estado=estado_frente, imu=imu, protecao=protecao)
            elif modo == "I":
                self.medidas["manuseio_fase"] = valor
            elif modo == "O":
                self.medidas["oled"] = valor

    def _atualizar(self) -> None:
        ultimo = time.monotonic()
        quadros = 0
        while not self.parar.wait(.012):
            agora = time.monotonic()
            dt = min(.05, max(.001, agora - ultimo))
            ultimo = agora
            with self.lock:
                if not self.firmware:
                    continue
                amostras = self.cena.passo(dt, self.medidas["pwm_esq"], self.medidas["pwm_dir"])
                frente = self.cena.sensor_frontal()
                amostra = " ".join(f"{v:.5f}" for v in amostras)
                try:
                    self._serial(self.firmware.consultar(f"S {round(dt*1000)} {frente or -1} {int(self.cena.corpo.segurando)} {amostra}"))
                    quadros += 1
                    if quadros % 5 == 0:
                        self._serial(self.firmware.consultar("O"))
                except (RuntimeError, OSError, ValueError) as erro:
                    self._soltar_cliente()
                    self.firmware.fechar()
                    self.firmware = None
                    self.medidas.update(pwm_esq=0, pwm_dir=0, frente_mm=None, frente_estado="INDISPONIVEL",
                                        imu="INDISPONIVEL", protecao="INDISPONIVEL", manuseio_fase="")
                    self.estado_build, self.log_build = "erro", str(erro)

    def retrato(self) -> dict:
        return {**self.cena.retrato(), "firmware": {**self.medidas, "conectado": self.cliente is not None}}

    def fechar(self) -> None:
        self.parar.set()
        self._thread.join(timeout=2)
        with self.lock:
            self._soltar_cliente()
            if self.firmware:
                self.firmware.fechar()


class ServidorCorpo(ThreadingTCPServer):
    daemon_threads = True


class ClienteCorpo(BaseRequestHandler):
    def handle(self) -> None:
        bancada = self.server.bancada
        conexao = self.request
        conexao.settimeout(.5)
        try:
            # Lê só o tamanho da autenticação. O protocolo segue no mesmo fluxo.
            token = bytearray()
            while len(token) < 32:
                parte = conexao.recv(32 - len(token))
                if not parte:
                    return
                token.extend(parte)
            with bancada.lock:
                if not hmac.compare_digest(token, bancada.token) or bancada.cliente or not bancada.firmware:
                    return
                conexao.sendall(b"+")
                bancada.cliente = conexao
            buffer = bytearray()
            while not bancada.parar.is_set():
                try:
                    parte = conexao.recv(1024)
                except TimeoutError:
                    continue
                if not parte:
                    break
                buffer.extend(parte)
                while b"\n" in buffer:
                    linha, _, buffer = buffer.partition(b"\n")
                    if not 1 <= len(linha) <= 384:
                        return
                    comando = linha.decode("ascii").rstrip("\r")
                    with bancada.lock:
                        if bancada.cliente is not conexao or not bancada.firmware:
                            return
                        bancada._serial(bancada.firmware.consultar(f"P {comando}"))
                if len(buffer) > 384:
                    return
        except (OSError, RuntimeError, UnicodeError):
            pass
        finally:
            with bancada.lock:
                if bancada.cliente is conexao:
                    bancada.cliente = None
                    if bancada.firmware:
                        try:
                            bancada._serial(bancada.firmware.consultar("P STOP"))
                        except (OSError, RuntimeError):
                            pass


class Painel(BaseHTTPRequestHandler):
    def log_message(self, *_args) -> None:
        pass

    def _responder(self, dados, codigo: int = 200, tipo: str = "application/json; charset=utf-8") -> None:
        saida = dados if isinstance(dados, bytes) else json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(saida)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(saida)

    def _pedido(self) -> dict:
        if self.headers.get("Origin") != f"http://{self.headers.get('Host')}" or self.headers.get_content_type() != "application/json":
            raise ValueError("A edição deve vir da própria bancada local.")
        tamanho = int(self.headers.get("Content-Length", "0"))
        if not 0 < tamanho <= 1_000_000:
            raise ValueError("Tamanho inválido.")
        dado = json.loads(self.rfile.read(tamanho))
        if not isinstance(dado, dict):
            raise ValueError("Envie um objeto JSON.")
        return dado

    def _tratar(self, metodo: str) -> None:
        try:
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                return self._responder({"erro": "Use o endereço local da bancada."}, 403)
            rota = urlsplit(self.path)
            bancada = self.server.bancada
            pagina = {"/": ("index.html", "text/html"), "/estilo.css": ("estilo.css", "text/css"),
                      "/bancada.js": ("bancada.js", "text/javascript")}.get(rota.path)
            if pagina and metodo == "GET":
                nome, tipo = pagina
                return self._responder((PASTA / "web" / nome).read_bytes(), tipo=tipo + "; charset=utf-8")
            dados = self._pedido() if metodo in {"POST", "PUT"} else {}
            if rota.path == "/api/compilar" and metodo == "POST":
                bancada.recompilar()
                return self._responder({"estado": "compilando"}, 202)
            with bancada.lock:
                if rota.path == "/api/estado" and metodo == "GET":
                    return self._responder(bancada.retrato())
                if rota.path == "/api/cena" and metodo == "POST":
                    bancada.cena.atualizar(dados)
                    return self._responder(bancada.retrato())
                if rota.path == "/api/firmware":
                    arquivo = parse_qs(rota.query).get("arquivo", [""])[0]
                    if not arquivo and metodo == "GET":
                        return self._responder({"arquivos": bancada.arquivos, "estado": bancada.estado_build, "log": bancada.log_build})
                    if arquivo not in bancada.arquivos:
                        raise ValueError("Arquivo fora da cópia da bancada.")
                    caminho = bancada.sketch / arquivo
                    if not caminho.resolve().is_relative_to(bancada.sketch.resolve()):
                        raise ValueError("Arquivo fora da cópia da bancada.")
                    if metodo == "GET":
                        return self._responder({"arquivo": arquivo, "conteudo": caminho.read_text(encoding="utf-8")})
                    if bancada.estado_build == "compilando":
                        raise ValueError("Aguarde a compilação antes de editar de novo.")
                    conteudo = dados.get("conteudo")
                    if not isinstance(conteudo, str):
                        raise ValueError("Conteúdo inválido.")
                    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
                    temporario.write_text(conteudo, encoding="utf-8")
                    temporario.replace(caminho)
                    return self._responder({"arquivo": arquivo})
            self._responder({"erro": "Página inexistente."}, 404)
        except (OSError, ValueError) as erro:
            self._responder({"erro": str(erro)}, 400)

    def do_GET(self) -> None:
        self._tratar("GET")

    def do_POST(self) -> None:
        self._tratar("POST")

    def do_PUT(self) -> None:
        self._tratar("PUT")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--porta", type=int, default=8766)
    parser.add_argument("--laylay", action="store_true", help="Inicia a Laylay com conexão exclusiva à bancada")
    parser.add_argument("--sem-abrir", action="store_true", help="Não abrir o navegador automaticamente")
    args = parser.parse_args()
    raiz = PASTA.parent
    with ThreadingHTTPServer(("127.0.0.1", args.porta), Painel) as painel, ServidorCorpo(("127.0.0.1", 0), ClienteCorpo) as corpo:
        bancada = painel.bancada = corpo.bancada = Bancada(raiz / "firmware/rosto_laylay", PASTA)
        Thread(target=corpo.serve_forever, daemon=True).start()
        laylay = None
        url = f"http://127.0.0.1:{painel.server_port}/"
        try:
            if args.laylay:
                ambiente = ambiente_laylay_virtual(corpo.server_address[1], bancada.token)
                laylay = subprocess.Popen([sys.executable, "-m", "sandbox.laylay_virtual"], cwd=raiz, env=ambiente)
            print(f"Bancada virtual em {url}", flush=True)
            if not args.sem_abrir:
                webbrowser.open(url)
            painel.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            bancada.fechar()
            corpo.shutdown()
            if laylay is not None and laylay.poll() is None:
                print("A Laylay ficou sem conexão com o corpo virtual. Encerre a janela dela normalmente.")


if __name__ == "__main__":
    main()
