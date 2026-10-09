"""Observabilidade passiva para encerramentos inesperados da Laylay."""
from __future__ import annotations

import atexit
import faulthandler
import json
import os
from pathlib import Path
import threading
import time
from typing import Any

# P0_DIAGNOSTICO_ENCERRAMENTO_V1_20260815
NOME_LOG_ENCERRAMENTO = "diagnostico_encerramento.log"
NOME_LOG_FALHAS_NATIVAS = "falhas_nativas.log"


def registrar_evento_encerramento(
    diretorio: str | os.PathLike[str],
    evento: str,
    *,
    componente: str = "laylay",
    **campos: Any,
) -> bool:
    """Persiste um evento JSONL com fsync sem afetar a disponibilidade."""
    try:
        pasta = Path(diretorio).expanduser().resolve()
        pasta.mkdir(parents=True, exist_ok=True)
        registro = {
            "ts": time.time(),
            "monotonic": time.monotonic(),
            "pid": os.getpid(),
            "thread": threading.current_thread().name,
            "componente": str(componente or "laylay")[:64],
            "evento": str(evento or "evento")[:96],
        }
        for chave, valor in campos.items():
            nome = str(chave or "")[:64]
            if not nome:
                continue
            registro[nome] = (
                valor
                if isinstance(valor, (str, int, float, bool)) or valor is None
                else str(valor)[:240]
            )
        caminho = pasta / NOME_LOG_ENCERRAMENTO
        with open(caminho, "a", encoding="utf-8", newline="\n") as arquivo:
            arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())
        return True
    except Exception:
        return False


class SentinelaEncerramento:
    """Mantém a caixa-preta nativa viva e marca saídas Python normais."""
    def __init__(
        self,
        diretorio: str | os.PathLike[str],
        *,
        componente: str = "laylay",
        habilitar_faulthandler: bool = True,
    ) -> None:
        self.diretorio = Path(diretorio).expanduser().resolve()
        self.componente = str(componente or "laylay")[:64]
        # Um fd não depende da destruição de um objeto TextIO. A captura fica
        # disponível nos demais callbacks; o SO fecha o fd ao sair do processo.
        self._fault_fd: int | None = None
        self._faulthandler_ativo = False
        self._atexit_registrado = False
        self.marcar("processo_observado", python=_versao_python())
        if habilitar_faulthandler:
            self._habilitar_faulthandler()
        try:
            atexit.register(self._ao_sair_normalmente)
            self._atexit_registrado = True
        except Exception:
            self.marcar("atexit_registro_falhou")

    def marcar(self, evento: str, **campos: Any) -> bool:
        return registrar_evento_encerramento(
            self.diretorio, evento, componente=self.componente, **campos,
        )

    def _habilitar_faulthandler(self) -> None:
        try:
            self.diretorio.mkdir(parents=True, exist_ok=True)
            self._fault_fd = os.open(
                self.diretorio / NOME_LOG_FALHAS_NATIVAS,
                os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0),
                0o600,
            )
            faulthandler.enable(file=self._fault_fd, all_threads=True)
            self._faulthandler_ativo = True
            self.marcar("faulthandler_ativo")
        except Exception as erro:
            self._faulthandler_ativo = False
            self.marcar("faulthandler_indisponivel", erro_tipo=type(erro).__name__)
            try:
                if self._fault_fd is not None:
                    os.close(self._fault_fd)
            except Exception:
                pass
            self._fault_fd = None

    def _ao_sair_normalmente(self) -> None:
        self.marcar("atexit_iniciado")
        # atexit usa ordem inversa. Esta marca conclui somente a sentinela;
        # callbacks anteriores ainda podem falhar, portanto não desativar aqui.
        self.marcar("atexit_concluido", alcance="callback_sentinela")
        try:
            if self._fault_fd is not None:
                os.fsync(self._fault_fd)
        except Exception:
            pass

    def desregistrar_para_teste(self) -> None:
        if self._atexit_registrado:
            try:
                atexit.unregister(self._ao_sair_normalmente)
            except Exception:
                pass
            self._atexit_registrado = False
        if self._faulthandler_ativo:
            try:
                faulthandler.disable()
            except Exception:
                pass
            self._faulthandler_ativo = False
        try:
            if self._fault_fd is not None:
                os.close(self._fault_fd)
        except Exception:
            pass
        self._fault_fd = None


def _versao_python() -> str:
    try:
        import sys
        return ".".join(str(item) for item in sys.version_info[:3])
    except Exception:
        return ""


def criar_sentinela_encerramento(
    diretorio: str | os.PathLike[str], *, componente: str = "laylay",
) -> SentinelaEncerramento:
    return SentinelaEncerramento(diretorio, componente=componente)
