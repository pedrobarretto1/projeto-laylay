"""Runtime local das mutações de arquivos já protegidas pela Laylay."""

from __future__ import annotations

from typing import Any, Callable

from mente_laylay.arquivos.arquivos_sistema import (
    buscar_itens_com_nome,
    criar_ou_editar_arquivo,
    criar_pasta,
    escrever_arquivo_texto_seguro,
    mover_arquivo,
    resolver_caminho,
)
from mente_laylay.arquivos.lixeira_laylay import (
    cancelar_exclusao_pendente,
    confirmar_exclusao_pendente,
    existe_exclusao_pendente,
    mover_para_lixeira,
    restaurar_ultimo_item,
)
from mente_laylay.arquivos.transacao_arquivos import executar_transacao_arquivo


class ArquivosMutacaoRuntime:
    """Agrupa as mutações existentes sem alterar suas regras de segurança."""

    def __init__(
        self,
        *,
        resolver_caminho_cb: Callable[[str], str] = resolver_caminho,
        criar_pasta_cb: Callable[[str], bool] = criar_pasta,
        criar_arquivo_cb: Callable[[str, str, str], bool] = criar_ou_editar_arquivo,
        escrever_texto_seguro_cb: Callable[..., dict[str, Any]] = escrever_arquivo_texto_seguro,
        mover_item_cb: Callable[[str, str], bool] = mover_arquivo,
        transacionar_cb: Callable[[dict[str, Any]], Any] = executar_transacao_arquivo,
        buscar_itens_cb: Callable[[str], list[str]] = buscar_itens_com_nome,
        solicitar_exclusao_cb: Callable[..., Any] = mover_para_lixeira,
        confirmar_exclusao_cb: Callable[[], Any] = confirmar_exclusao_pendente,
        cancelar_exclusao_cb: Callable[[], Any] = cancelar_exclusao_pendente,
        restaurar_ultimo_cb: Callable[[], Any] = restaurar_ultimo_item,
        exclusao_pendente_cb: Callable[[], bool] = existe_exclusao_pendente,
    ) -> None:
        self._resolver_caminho = resolver_caminho_cb
        self._criar_pasta = criar_pasta_cb
        self._criar_arquivo = criar_arquivo_cb
        self._escrever_texto_seguro = escrever_texto_seguro_cb
        self._mover_item = mover_item_cb
        self._transacionar = transacionar_cb
        self._buscar_itens = buscar_itens_cb
        self._solicitar_exclusao = solicitar_exclusao_cb
        self._confirmar_exclusao = confirmar_exclusao_cb
        self._cancelar_exclusao = cancelar_exclusao_cb
        self._restaurar_ultimo = restaurar_ultimo_cb
        self._exclusao_pendente = exclusao_pendente_cb

    def resolver_caminho(self, valor: str) -> str:
        return str(self._resolver_caminho(valor) or "")

    def criar_pasta(self, caminho: str) -> bool:
        return bool(self._criar_pasta(caminho))

    def criar_arquivo(self, caminho: str, conteudo: str, modo: str = "w") -> bool:
        return bool(self._criar_arquivo(caminho, conteudo, modo))

    def escrever_texto_seguro(
        self, caminho: str, conteudo: str, *, sobrescrever: bool = False,
    ) -> dict[str, Any]:
        return dict(self._escrever_texto_seguro(
            caminho, conteudo, sobrescrever=sobrescrever,
        ) or {})

    def mover_item(self, origem: str, destino: str) -> bool:
        return bool(self._mover_item(origem, destino))

    def transacionar(self, params: dict[str, Any]) -> Any:
        return self._transacionar(dict(params or {}))

    def buscar_itens(self, alvo: str) -> list[str]:
        return [str(item) for item in (self._buscar_itens(alvo) or ())]

    def solicitar_exclusao(self, caminho: str) -> Any:
        return self._solicitar_exclusao(caminho)

    def confirmar_exclusao(self) -> Any:
        return self._confirmar_exclusao()

    def cancelar_exclusao(self) -> None:
        self._cancelar_exclusao()

    def restaurar_ultimo(self) -> Any:
        return self._restaurar_ultimo()

    def diagnostico(self) -> dict[str, Any]:
        return {
            "somente_raizes_autorizadas": True,
            "escrita_segura_disponivel": True,
            "lixeira_reversivel": True,
            "confirmacao_exclusao_pendente": bool(self._exclusao_pendente()),
        }


def criar_arquivos_mutacao_runtime(**kwargs: Any) -> ArquivosMutacaoRuntime:
    return ArquivosMutacaoRuntime(**kwargs)

