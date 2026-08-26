"""Contrato tipado para busca e abertura segura de arquivos locais."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PortaArquivosLeitura(Protocol):
    def pesquisar(
        self, consulta: str, *, limite: int = 5,
        forcar_indice: bool = False, somente_projeto: bool = False,
    ) -> dict[str, Any]: ...

    def abrir(self, caminho: str) -> bool: ...

    def diagnostico(self) -> dict[str, Any]: ...


_OPERACOES_OBRIGATORIAS = ("pesquisar", "abrir", "diagnostico")
_CAMPOS_DIAGNOSTICO = {
    "indexacoes", "pesquisas", "falhas", "arquivos_indexados", "cache_hits",
    "raizes", "cache_ativo", "indice_incompleto", "somente_leitura",
    "envia_conteudo_externo",
}
_CAMPOS_INTERNOS_RESULTADO = {
    "conteudo", "conteudo_norm", "raiz", "configuracao", "credenciais",
    "secret", "local_key",
}


@dataclass(frozen=True)
class RegistroArquivosLeitura:
    """Fronteira de leitura; não oferece criação, escrita ou exclusão."""

    servico: PortaArquivosLeitura = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroArquivosLeitura":
        ausentes = tuple(
            nome for nome in _OPERACOES_OBRIGATORIAS
            if not callable(getattr(servico, nome, None))
        )
        if ausentes:
            raise RuntimeError(
                "serviço de leitura de arquivos inválido na composição; "
                "operações ausentes: " + ", ".join(ausentes)
            )
        return cls(servico=servico)

    def pesquisar(
        self, consulta: str, *, limite: int = 5,
        forcar_indice: bool = False, somente_projeto: bool = False,
    ) -> dict[str, Any]:
        retorno = dict(self.servico.pesquisar(
            consulta,
            limite=limite,
            forcar_indice=forcar_indice,
            somente_projeto=somente_projeto,
        ) or {})
        resultados = []
        for item in retorno.get("resultados") or ():
            if not isinstance(item, dict):
                continue
            seguro = dict(item)
            for campo in _CAMPOS_INTERNOS_RESULTADO:
                seguro.pop(campo, None)
            if seguro.get("sensivel"):
                seguro["trecho"] = ""
            resultados.append(seguro)
        retorno["resultados"] = resultados
        return retorno

    def abrir(self, caminho: str) -> bool:
        return bool(self.servico.abrir(caminho))

    def ler_texto(self, caminho: str, *, limite: int = 4000) -> dict[str, Any]:
        """Lê texto local pela mesma fronteira segura usada pelo índice.

        A operação é opcional para serviços legados; sua ausência é relatada
        como indisponibilidade, sem tentar abrir ou interpretar o arquivo por
        outro caminho.
        """
        ler = getattr(self.servico, "ler_texto", None)
        if not callable(ler):
            return {"ok": False, "status": "indisponivel", "conteudo": ""}
        bruto = dict(ler(caminho, limite=limite) or {})
        return {
            "ok": bruto.get("ok") is True,
            "status": str(bruto.get("status") or "falha_execucao")[:80],
            "nome": str(bruto.get("nome") or "")[:240],
            "conteudo": str(bruto.get("conteudo") or "")[:max(1, min(8000, int(limite)))],
            "truncado": bruto.get("truncado") is True,
        }

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {chave: bruto[chave] for chave in _CAMPOS_DIAGNOSTICO if chave in bruto}


def registrar_arquivos_leitura(servico: Any) -> RegistroArquivosLeitura:
    if isinstance(servico, RegistroArquivosLeitura):
        return servico
    return RegistroArquivosLeitura.criar(servico)
