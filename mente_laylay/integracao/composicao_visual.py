"""Monta Game Bar, avatar e barra de comando sobre o mesmo estado visual."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.barra_comando import criar_barra_comando_runtime
from mente_laylay.integracao.gamebar_bridge import criar_gamebar_bridge_runtime
from mente_laylay.personalidade.avatar_runtime import criar_avatar_runtime


_FALSOS = {"0", "false", "nao", "não", "off", "desligado"}


class ComposicaoVisualLaylayRuntime:
    """Preserva a criação em duas fases exigida pelo processador de comandos."""

    def __init__(
        self,
        *,
        raiz_projeto: str | os.PathLike[str],
        estado_getter: Callable[[], Mapping[str, Any]],
        registrar_falha: Callable[..., Any] | None = None,
        env_getter: Callable[[str, str], str] = os.getenv,
        log: Callable[[str], Any] = print,
        gamebar_factory: Callable[..., Any] = criar_gamebar_bridge_runtime,
        avatar_factory: Callable[..., Any] = criar_avatar_runtime,
        barra_factory: Callable[..., Any] = criar_barra_comando_runtime,
    ) -> None:
        self.raiz_projeto = Path(raiz_projeto).resolve()
        self.estado_getter = estado_getter
        self.registrar_falha = registrar_falha
        self.env_getter = env_getter
        self.log = log
        self.barra_factory = barra_factory
        self._barra: Any = None
        porta = self._inteiro_env("LAYLAY_GAMEBAR_PORTA", 18766, minimo=1024, maximo=65535)
        self.gamebar = gamebar_factory(
            estado_getter=estado_getter,
            porta=porta,
            env_getter=env_getter,
            registrar_falha=registrar_falha,
            log=log,
        )
        self.avatar = avatar_factory(
            raiz_projeto=self.raiz_projeto,
            estado_getter=estado_getter,
            visual_externo_disponivel=self.gamebar.conectado,
            registrar_falha=registrar_falha,
            env_getter=env_getter,
            log=log,
        )

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("composicao_visual", codigo, erro=erro)

    def _inteiro_env(self, nome: str, padrao: int, *, minimo: int, maximo: int) -> int:
        bruto = self.env_getter(nome, str(padrao))
        try:
            valor = int(str(bruto or padrao).strip())
            if not minimo <= valor <= maximo:
                raise ValueError("fora do intervalo")
            return valor
        except (TypeError, ValueError) as erro:
            self.log(f"⚠️ [VISUAL] {nome} inválida; usando {padrao}.")
            self._relatar(f"configuracao_{nome.casefold()}", erro)
            return int(padrao)

    def _booleano_env(self, nome: str, padrao: bool = True) -> bool:
        bruto = self.env_getter(nome, "1" if padrao else "0")
        return str(bruto or "").strip().casefold() not in _FALSOS

    def conectar_barra(
        self,
        *,
        processar_texto: Callable[[str], Any],
        keyboard_mod: Any,
        hotkey: str,
        modo_jogo_ativo: Callable[[], bool],
    ) -> Any:
        if self._barra is not None:
            return self._barra
        self._barra = self.barra_factory(
            processar_texto=processar_texto,
            keyboard_mod=keyboard_mod,
            hotkey=hotkey,
            modo_jogo_ativo=modo_jogo_ativo,
            sobreposicao_sem_foco_jogo=self._booleano_env(
                "LAYLAY_BARRA_SEM_FOCO_JOGO", True,
            ),
            estado_visual_cb=self.gamebar.publicar_barra,
            visual_externo_disponivel=self.gamebar.conectado,
            registrar_falha=self.registrar_falha,
            log=self.log,
        )
        return self._barra

    @property
    def barra(self) -> Any:
        if self._barra is None:
            raise RuntimeError("barra de comando ainda não conectada ao processador de texto")
        return self._barra

    def parar(self) -> None:
        """Finalizador de emergência para a saída normal do interpretador."""
        if self._barra is not None:
            try:
                self._barra.encerrar()
            except Exception as erro:
                self.log(
                    "⚠️ [VISUAL] barra não encerrou corretamente: "
                    f"{type(erro).__name__}"
                )
                self._relatar("encerramento_barra", erro)
        self.avatar.parar()
        self.gamebar.parar()


def criar_composicao_visual_laylay_runtime(**kwargs: Any) -> ComposicaoVisualLaylayRuntime:
    return ComposicaoVisualLaylayRuntime(**kwargs)
