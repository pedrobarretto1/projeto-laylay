"""Trava de instância única para a aplicação desktop da Laylay.

No Windows, iniciar duas cópias no mesmo console faz ambas disputarem stdin e
a porta da extensão Chrome. O mutex é limitado à sessão do usuário e ao caminho
do projeto, permitindo instalações diferentes sem conflito entre si.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from typing import Any, Callable


ERRO_MUTEX_JA_EXISTE = 183
CODIGO_ROTEIRO_NAO_EXECUTADO = 73


def codigo_saida_instancia_ocupada(argumentos: list[str] | tuple[str, ...]) -> int:
    """Distingue abertura normal ignorada de roteiro que não chegou a rodar."""
    return (
        CODIGO_ROTEIRO_NAO_EXECUTADO
        if "--roteiro" in {str(item or "") for item in argumentos}
        else 0
    )


def nome_mutex_instancia(identificador: str | os.PathLike[str]) -> str:
    caminho = str(Path(identificador).resolve()).casefold().encode("utf-8")
    resumo = hashlib.sha256(caminho).hexdigest()[:20]
    return rf"Local\Laylay_{resumo}"


@dataclass
class InstanciaUnicaRuntime:
    adquirida: bool
    nome: str = ""
    handle: Any = None
    fechar_handle: Callable[[Any], Any] | None = None

    def liberar(self) -> None:
        handle, self.handle = self.handle, None
        if handle is not None and callable(self.fechar_handle):
            try:
                self.fechar_handle(handle)
            except Exception:
                pass


def _portas_mutex_windows() -> tuple[
    Callable[[str], Any], Callable[[Any], Any], Callable[[], int]
]:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    criar = kernel32.CreateMutexW
    criar.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    criar.restype = wintypes.HANDLE
    fechar = kernel32.CloseHandle
    fechar.argtypes = (wintypes.HANDLE,)
    fechar.restype = wintypes.BOOL
    return (
        lambda nome: criar(None, False, nome),
        fechar,
        ctypes.get_last_error,
    )


def adquirir_instancia_unica(
    identificador: str | os.PathLike[str],
    *,
    sistema: str | None = None,
    criar_mutex: Callable[[str], Any] | None = None,
    fechar_mutex: Callable[[Any], Any] | None = None,
    obter_ultimo_erro: Callable[[], int] | None = None,
) -> InstanciaUnicaRuntime:
    plataforma = str(sistema or os.name).casefold()
    nome = nome_mutex_instancia(identificador)
    if plataforma != "nt":
        return InstanciaUnicaRuntime(adquirida=True, nome=nome)

    try:
        if not all((criar_mutex, fechar_mutex, obter_ultimo_erro)):
            criar_mutex, fechar_mutex, obter_ultimo_erro = _portas_mutex_windows()
        handle = criar_mutex(nome)  # type: ignore[misc]
        erro = int(obter_ultimo_erro() or 0)  # type: ignore[misc]
        if not handle:
            # Falhar aberta é mais seguro do que impedir a inicialização por
            # uma indisponibilidade isolada da API de sincronização.
            return InstanciaUnicaRuntime(adquirida=True, nome=nome)
        if erro == ERRO_MUTEX_JA_EXISTE:
            fechar_mutex(handle)  # type: ignore[misc]
            return InstanciaUnicaRuntime(adquirida=False, nome=nome)
        return InstanciaUnicaRuntime(
            adquirida=True,
            nome=nome,
            handle=handle,
            fechar_handle=fechar_mutex,
        )
    except Exception:
        return InstanciaUnicaRuntime(adquirida=True, nome=nome)
