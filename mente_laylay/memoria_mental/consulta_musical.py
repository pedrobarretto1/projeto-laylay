"""Consultas musicais de somente leitura para a mente compartilhada."""

from __future__ import annotations

from typing import Any, Callable, Mapping


class ConsultaMusicalRuntime:
    """Reúne leituras musicais sem oferecer reprodução ou alteração."""

    def __init__(
        self,
        *,
        playlists_usuario: Any,
        playlists_laylay: Any,
        estado_getter: Callable[[], Mapping[str, Any]],
    ) -> None:
        self.playlists_usuario = playlists_usuario
        self.playlists_laylay = playlists_laylay
        self.estado_getter = estado_getter

    def listar_usuario(self) -> str:
        return str(self.playlists_usuario.listar_salvas() or "")

    def consultar_usuario(self, nome: str) -> dict[str, Any]:
        return dict(self.playlists_usuario.list_content(nome) or {})

    def contar_usuario(self, nome: str) -> int:
        return max(0, int(self.playlists_usuario.len(nome) or 0))

    def formatar_prompt(self) -> str:
        return str(self.playlists_usuario.formatar_para_prompt() or "")

    def retrato_usuario(self, texto: str = "") -> dict[str, Any]:
        return dict(self.playlists_usuario.retrato_para_mente(texto) or {})

    def indice_usuario(self) -> dict[str, int]:
        retrato = self.retrato_usuario()
        indice: dict[str, int] = {}
        for item in retrato.get("playlists") or ():
            if not isinstance(item, dict):
                continue
            nome = str(item.get("nome") or "").strip()
            if nome:
                indice[nome] = max(0, int(item.get("total") or 0))
        return indice

    def listar_laylay(self, nome: str = "") -> str:
        return str(self.playlists_laylay.listar(nome) or "")

    def retrato_laylay(self, texto: str = "") -> dict[str, Any]:
        return dict(self.playlists_laylay.retrato_para_mente(texto) or {})

    def estado(self) -> dict[str, Any]:
        bruto = dict(self.estado_getter() or {})
        reproducao = dict(bruto.get("playlist_state") or {})
        return {
            "ultima_playlist": str(bruto.get("ultima_playlist") or "").strip(),
            "playlist_ativa": str(reproducao.get("name") or "").strip(),
            "indice": max(0, int(reproducao.get("index") or 0)),
            "modo_aleatorio": bool(reproducao.get("shuffle", False)),
            "intervencao_usuario": bool(reproducao.get("user_intervened", False)),
            "status_avanco": str(reproducao.get("last_advance_status") or "").strip(),
            "musica_atual_titulo": str(
                bruto.get("musica_atual_titulo") or ""
            ).strip(),
            "musica_atual_status": str(
                bruto.get("musica_atual_status") or ""
            ).strip(),
        }

    def diagnostico(self) -> dict[str, Any]:
        estado = self.estado()
        try:
            curadoria = dict(self.playlists_laylay.diagnostico() or {})
        except Exception:
            curadoria = {"disponivel": False, "playlists": 0, "falhas": 1}
        return {
            "somente_leitura": True,
            "playlists_usuario": len(self.indice_usuario()),
            "playlists_laylay": max(0, int(curadoria.get("playlists") or 0)),
            "curadoria_disponivel": bool(curadoria.get("disponivel")),
            "curadoria_usa_historico": bool(curadoria.get("usa_historico")),
            "curadoria_cooperativa": bool(curadoria.get("cooperacao_habilitada")),
            "curadoria_falhas": max(0, int(curadoria.get("falhas") or 0)),
            "playlist_ativa": bool(estado.get("playlist_ativa")),
            "estado_disponivel": True,
            "expondo_urls": False,
        }


def criar_consulta_musical_runtime(**kwargs: Any) -> ConsultaMusicalRuntime:
    return ConsultaMusicalRuntime(**kwargs)
