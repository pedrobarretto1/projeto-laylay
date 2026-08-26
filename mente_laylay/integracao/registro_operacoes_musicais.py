"""Contrato tipado das mutações e da reprodução musical."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PortaMusicaOperacoes(Protocol):
    def criar_playlist(self, nome: str) -> dict[str, Any]: ...
    def apagar_playlist(self, nome: str) -> bool: ...
    def adicionar_faixa(self, nome: str, url: str, titulo: str, canal: str = "") -> bool: ...
    def mover_faixa(self, origem: str, destino: str, musica: str = "") -> dict[str, Any]: ...
    def detalhar_playlist(self, nome: str, **paginacao: Any) -> dict[str, Any]: ...
    def tocar_faixa_exata(self, nome: str, video_id: str, revisao: str) -> dict[str, Any]: ...
    def adicionar_url_playlist(self, nome: str, url: str) -> dict[str, Any]: ...
    def copiar_faixa_exata(self, origem: str, destino: str, video_id: str, revisao: str) -> dict[str, Any]: ...
    def mover_faixa_exata(self, origem: str, destino: str, video_id: str, revisao: str) -> dict[str, Any]: ...
    def remover_faixa_exata(self, nome: str, video_id: str, revisao: str) -> dict[str, Any]: ...
    def definir_capa_playlist(self, nome: str, caminho: str, revisao: str) -> dict[str, Any]: ...
    def restaurar_capa_playlist(self, nome: str, revisao: str) -> dict[str, Any]: ...
    def tocar_playlist(self, nome: str) -> bool: ...
    def preparar_shuffle(self, nome: str) -> dict[str, Any]: ...
    def primeira_url(self, nome: str) -> str: ...
    def avancar_proxima(self) -> bool: ...
    def voltar_anterior(self) -> bool: ...
    def definir_ultima_playlist(self, nome: str) -> None: ...
    def definir_ultima_url(self, url: str) -> None: ...
    def faixa_atual(self) -> dict[str, Any]: ...
    def copiar_curadoria(self, origem: str, musica: str, destino: str) -> dict[str, Any]: ...
    def selecionar_curadoria(self, nome: str = "", indice_faixa: int = 0) -> dict[str, Any]: ...
    def estado(self) -> dict[str, Any]: ...
    def diagnostico(self) -> dict[str, Any]: ...


_OPERACOES = (
    "criar_playlist", "apagar_playlist", "adicionar_faixa", "mover_faixa", "tocar_playlist",
    "preparar_shuffle", "primeira_url", "avancar_proxima", "voltar_anterior",
    "definir_ultima_playlist", "definir_ultima_url", "faixa_atual",
    "copiar_curadoria", "estado", "diagnostico",
)
_DIAGNOSTICO_PERMITIDO = {
    "mutacao_disponivel", "reproducao_disponivel", "auto_next_disponivel",
    "curadoria_disponivel", "playlist_ativa",
}
_ESTADO_PERMITIDO = {
    "playlist_ativa", "indice", "modo_aleatorio", "status_avanco", "tab_id",
}


@dataclass(frozen=True)
class RegistroOperacoesMusicais:
    """Publica operações nomeadas sem callbacks musicais no namespace geral."""

    servico: PortaMusicaOperacoes = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroOperacoesMusicais":
        ausentes = tuple(
            nome for nome in _OPERACOES if not callable(getattr(servico, nome, None))
        )
        if ausentes:
            raise RuntimeError(
                "serviço de operações musicais inválido na composição; "
                "operações ausentes: " + ", ".join(ausentes)
            )
        return cls(servico=servico)

    def apagar_playlist(self, nome: str) -> bool:
        return bool(self.servico.apagar_playlist(nome))

    def criar_playlist(self, nome: str) -> dict[str, Any]:
        return dict(self.servico.criar_playlist(nome) or {})

    def adicionar_faixa(self, nome: str, url: str, titulo: str, canal: str = "") -> bool:
        return bool(self.servico.adicionar_faixa(nome, url, titulo, canal))

    def adicionar_faixa_resultado(
        self, nome: str, url: str, titulo: str, canal: str = "",
    ) -> dict[str, Any]:
        detalhado = getattr(self.servico, "adicionar_faixa_resultado", None)
        if callable(detalhado):
            bruto = dict(detalhado(nome, url, titulo, canal) or {})
            return {
                "ok": bool(bruto.get("ok")),
                "added": bool(bruto.get("added")),
                "duplicated": bool(bruto.get("duplicated")),
                "status": str(bruto.get("status") or "").strip(),
            }
        ok = self.adicionar_faixa(nome, url, titulo, canal)
        return {
            "ok": ok,
            "added": ok,
            "duplicated": False,
            "status": "playlist_musica_adicionada" if ok else "falha_execucao",
        }

    def mover_faixa(self, origem: str, destino: str, musica: str = "") -> dict[str, Any]:
        return dict(self.servico.mover_faixa(origem, destino, musica) or {})

    def detalhar_playlist(self, nome: str, **paginacao: Any) -> dict[str, Any]:
        return dict(self.servico.detalhar_playlist(nome, **paginacao) or {})

    def tocar_faixa_exata(self, nome: str, video_id: str, revisao: str) -> dict[str, Any]:
        return dict(self.servico.tocar_faixa_exata(nome, video_id, revisao) or {})

    def adicionar_url_playlist(self, nome: str, url: str) -> dict[str, Any]:
        return dict(self.servico.adicionar_url_playlist(nome, url) or {})

    def copiar_faixa_exata(self, origem: str, destino: str, video_id: str, revisao: str) -> dict[str, Any]:
        return dict(self.servico.copiar_faixa_exata(origem, destino, video_id, revisao) or {})

    def mover_faixa_exata(self, origem: str, destino: str, video_id: str, revisao: str) -> dict[str, Any]:
        return dict(self.servico.mover_faixa_exata(origem, destino, video_id, revisao) or {})

    def remover_faixa_exata(self, nome: str, video_id: str, revisao: str) -> dict[str, Any]:
        return dict(self.servico.remover_faixa_exata(nome, video_id, revisao) or {})

    def definir_capa_playlist(self, nome: str, caminho: str, revisao: str) -> dict[str, Any]:
        return dict(self.servico.definir_capa_playlist(nome, caminho, revisao) or {})

    def restaurar_capa_playlist(self, nome: str, revisao: str) -> dict[str, Any]:
        return dict(self.servico.restaurar_capa_playlist(nome, revisao) or {})

    def tocar_playlist(self, nome: str) -> bool:
        return bool(self.servico.tocar_playlist(nome))

    def preparar_shuffle(self, nome: str) -> dict[str, Any]:
        return dict(self.servico.preparar_shuffle(nome) or {})

    def primeira_url(self, nome: str) -> str:
        return str(self.servico.primeira_url(nome) or "").strip()

    def avancar_proxima(self) -> bool:
        return bool(self.servico.avancar_proxima())

    def voltar_anterior(self) -> bool:
        return bool(self.servico.voltar_anterior())

    def definir_ultima_playlist(self, nome: str) -> None:
        self.servico.definir_ultima_playlist(nome)

    def definir_ultima_url(self, url: str) -> None:
        self.servico.definir_ultima_url(url)

    def faixa_atual(self) -> dict[str, Any]:
        retorno = dict(self.servico.faixa_atual() or {})
        return {
            "url": str(retorno.get("url") or "").strip(),
            "title": str(retorno.get("title") or "").strip(),
            "canal": str(retorno.get("canal") or "").strip(),
            "origem": str(retorno.get("origem") or "").strip(),
        }

    def copiar_curadoria(self, origem: str, musica: str, destino: str) -> dict[str, Any]:
        return dict(self.servico.copiar_curadoria(origem, musica, destino) or {})

    def selecionar_curadoria(
        self, nome: str = "", indice_faixa: int = 0,
    ) -> dict[str, Any]:
        selecionar = getattr(self.servico, "selecionar_curadoria", None)
        if not callable(selecionar):
            return {"ok": False, "erro": "curadoria_indisponivel"}
        retorno = dict(selecionar(nome, indice_faixa) or {})
        faixa_bruta = retorno.get("faixa")
        faixa = dict(faixa_bruta) if isinstance(faixa_bruta, dict) else {}
        # Esta porta executa reprodução, por isso a URL pode atravessar apenas
        # neste método mutável e não aparece no retrato de leitura/prompt.
        return {
            "ok": bool(retorno.get("ok")),
            "playlist": str(retorno.get("playlist") or "").strip(),
            "erro": str(retorno.get("erro") or "").strip(),
            "faixa": {
                "url": str(faixa.get("url") or "").strip(),
                "titulo": str(faixa.get("titulo") or "").strip(),
                "canal": str(faixa.get("canal") or "").strip(),
            },
        }

    def estado(self) -> dict[str, Any]:
        bruto = dict(self.servico.estado() or {})
        return {chave: bruto[chave] for chave in _ESTADO_PERMITIDO if chave in bruto}

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {chave: bruto[chave] for chave in _DIAGNOSTICO_PERMITIDO if chave in bruto}


def registrar_operacoes_musicais(servico: Any) -> RegistroOperacoesMusicais:
    if isinstance(servico, RegistroOperacoesMusicais):
        return servico
    return RegistroOperacoesMusicais.criar(servico)
