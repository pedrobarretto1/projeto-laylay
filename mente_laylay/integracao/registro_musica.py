"""Contrato tipado e sanitizado para consultas de música e playlists."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class PortaMusicaLeitura(Protocol):
    def listar_usuario(self) -> str: ...
    def consultar_usuario(self, nome: str) -> dict[str, Any]: ...
    def contar_usuario(self, nome: str) -> int: ...
    def formatar_prompt(self) -> str: ...
    def retrato_usuario(self, texto: str = "") -> dict[str, Any]: ...
    def indice_usuario(self) -> dict[str, int]: ...
    def listar_laylay(self, nome: str = "") -> str: ...
    def retrato_laylay(self, texto: str = "") -> dict[str, Any]: ...
    def estado(self) -> dict[str, Any]: ...
    def diagnostico(self) -> dict[str, Any]: ...


_OPERACOES = (
    "listar_usuario", "consultar_usuario", "contar_usuario", "formatar_prompt",
    "retrato_usuario", "indice_usuario", "listar_laylay", "retrato_laylay",
    "estado", "diagnostico",
)
_ESTADO_PERMITIDO = {
    "ultima_playlist", "playlist_ativa", "indice", "modo_aleatorio",
    "intervencao_usuario", "status_avanco", "musica_atual_titulo",
    "musica_atual_status",
}
_DIAGNOSTICO_PERMITIDO = {
    "somente_leitura", "playlists_usuario", "playlist_ativa",
    "estado_disponivel", "expondo_urls", "playlists_laylay",
    "curadoria_disponivel", "curadoria_usa_historico", "curadoria_falhas",
    "curadoria_cooperativa",
}


def _texto_sem_url(valor: Any) -> str:
    texto = str(valor or "").strip()
    return re.sub(r"https?://\S+", "[link omitido]", texto, flags=re.IGNORECASE)


def _retrato_seguro(bruto: dict[str, Any]) -> dict[str, Any]:
    playlists = []
    for item in bruto.get("playlists") or ():
        if not isinstance(item, dict):
            continue
        nome = _texto_sem_url(item.get("nome"))
        if nome:
            playlists.append({"nome": nome, "total": max(0, int(item.get("total") or 0))})
    detalhe_bruto = bruto.get("detalhe") or {}
    detalhe: dict[str, Any] = {}
    if isinstance(detalhe_bruto, dict) and detalhe_bruto:
        detalhe = {
            "nome": _texto_sem_url(detalhe_bruto.get("nome")),
            "titulos": [
                _texto_sem_url(titulo) for titulo in detalhe_bruto.get("titulos") or ()
                if str(titulo or "").strip()
            ][:8],
        }
    return {"playlists": playlists[:30], "detalhe": detalhe}


@dataclass(frozen=True)
class RegistroMusicaLeitura:
    """Fronteira sem comandos de play, adição, remoção ou URLs."""

    servico: PortaMusicaLeitura = field(repr=False)

    @classmethod
    def criar(cls, servico: Any) -> "RegistroMusicaLeitura":
        ausentes = tuple(
            nome for nome in _OPERACOES if not callable(getattr(servico, nome, None))
        )
        if ausentes:
            raise RuntimeError(
                "serviço de leitura musical inválido na composição; operações ausentes: "
                + ", ".join(ausentes)
            )
        return cls(servico=servico)

    def listar_usuario(self) -> str:
        return str(self.servico.listar_usuario() or "")

    def consultar_usuario(self, nome: str) -> dict[str, Any]:
        bruto = dict(self.servico.consultar_usuario(nome) or {})
        return {
            "ok": bool(bruto.get("ok")),
            "name": _texto_sem_url(bruto.get("name")),
            "total": max(0, int(bruto.get("total") or 0)),
            "last_titles": [
                _texto_sem_url(titulo) for titulo in bruto.get("last_titles") or ()
                if str(titulo or "").strip()
            ][:3],
            **({"error": str(bruto.get("error"))} if bruto.get("error") else {}),
        }

    def contar_usuario(self, nome: str) -> int:
        return max(0, int(self.servico.contar_usuario(nome) or 0))

    def formatar_prompt(self) -> str:
        return str(self.servico.formatar_prompt() or "")

    def retrato_usuario(self, texto: str = "") -> dict[str, Any]:
        return _retrato_seguro(dict(self.servico.retrato_usuario(texto) or {}))

    def indice_usuario(self) -> dict[str, int]:
        bruto = dict(self.servico.indice_usuario() or {})
        return {
            _texto_sem_url(nome): max(0, int(total or 0))
            for nome, total in bruto.items() if str(nome or "").strip()
        }

    def listar_laylay(self, nome: str = "") -> str:
        return str(self.servico.listar_laylay(nome) or "")

    def retrato_laylay(self, texto: str = "") -> dict[str, Any]:
        return _retrato_seguro(dict(self.servico.retrato_laylay(texto) or {}))

    def estado(self) -> dict[str, Any]:
        bruto = dict(self.servico.estado() or {})
        retorno = {
            chave: bruto[chave] for chave in _ESTADO_PERMITIDO if chave in bruto
        }
        for chave in (
            "ultima_playlist", "playlist_ativa", "status_avanco",
            "musica_atual_titulo", "musica_atual_status",
        ):
            if chave in retorno:
                retorno[chave] = _texto_sem_url(retorno[chave])
        return retorno

    def diagnostico(self) -> dict[str, Any]:
        bruto = dict(self.servico.diagnostico() or {})
        return {
            chave: bruto[chave] for chave in _DIAGNOSTICO_PERMITIDO if chave in bruto
        }


def registrar_musica_leitura(servico: Any) -> RegistroMusicaLeitura:
    if isinstance(servico, RegistroMusicaLeitura):
        return servico
    return RegistroMusicaLeitura.criar(servico)
