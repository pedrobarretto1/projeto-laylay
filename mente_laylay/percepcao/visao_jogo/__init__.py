"""Visão temporária e sob demanda para o modo jogo."""

from .captura_janela import capturar_janela_jogo_base64
from .composicao import ComposicaoVisaoJogoRuntime, criar_composicao_visao_jogo_runtime
from .coordenador import CoordenadorVisaoJogoRuntime, criar_coordenador_visao_jogo_runtime
from .runtime import VisaoJogoRuntime, criar_visao_jogo_runtime
from .sessao_jogo import ContextoSessoesJogo, identificar_jogo

__all__ = [
    "ComposicaoVisaoJogoRuntime", "ContextoSessoesJogo",
    "CoordenadorVisaoJogoRuntime", "VisaoJogoRuntime",
    "capturar_janela_jogo_base64", "criar_composicao_visao_jogo_runtime",
    "criar_coordenador_visao_jogo_runtime", "criar_visao_jogo_runtime",
    "identificar_jogo",
]
