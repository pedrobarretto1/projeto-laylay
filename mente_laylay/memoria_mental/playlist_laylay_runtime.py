"""Runtime das playlists proprias da Laylay.

Mantem persistencia e curadoria em um modulo separado, recebendo os dados da
mente musical compartilhada por callbacks para nao criar um estado paralelo.
"""

from __future__ import annotations

import os
import unicodedata
from typing import Any, Callable, Dict, Mapping

from mente_laylay.memoria_mental.curadoria_musical import (
    encontrar_faixa_playlist,
    sincronizar_playlists_da_laylay,
)
from mente_laylay.memoria_mental.playlist_mental import (
    fala_playlist_conteudo_estilosa,
    limpar_nome_playlist,
    playlists_load,
    playlists_save,
    yt_clean_title,
)


class PlaylistLaylayRuntime:
    def __init__(
        self,
        *,
        state_file: str,
        cache: Dict[str, Any],
        playlists_usuario_getter: Callable[[], Dict[str, Any]],
        historico_musical_getter: Callable[[], Dict[str, Any]],
        adicionar_playlist_usuario: Callable[[str, str, str, str], Any],
        publicar_cooperacao: Callable[[Mapping[str, Any]], Any] | None = None,
    ) -> None:
        self.state_file = state_file
        self.cache = cache
        self.playlists_usuario_getter = playlists_usuario_getter
        self.historico_musical_getter = historico_musical_getter
        self.adicionar_playlist_usuario = adicionar_playlist_usuario
        self.publicar_cooperacao = publicar_cooperacao
        self._sincronizacoes = 0
        self._gravacoes = 0
        self._falhas = 0
        self._ultima_sincronizacao_alterou = False

    def _sync_cache(self, data: Dict[str, Any] | None) -> Dict[str, Any]:
        data = data if isinstance(data, dict) else {}
        self.cache.clear()
        self.cache.update(data)
        return self.cache

    def load(self) -> Dict[str, Any]:
        pasta = os.path.dirname(self.state_file)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        data = playlists_load(self.state_file, self.state_file)
        return self._sync_cache(data)

    def save(self, data: Dict[str, Any]) -> bool:
        pasta = os.path.dirname(self.state_file)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        ok = playlists_save(self.state_file, data or {})
        if ok:
            self._sync_cache(data or {})
        return bool(ok)

    def sincronizar(self) -> Dict[str, Any]:
        self._sincronizacoes += 1
        atuais = self.load()
        try:
            playlists_usuario = self.playlists_usuario_getter() or {}
        except Exception:
            self._falhas += 1
            playlists_usuario = {}
        try:
            historico = self.historico_musical_getter() or {}
        except Exception:
            self._falhas += 1
            historico = {}
        sincronizadas = sincronizar_playlists_da_laylay(
            playlists_usuario if isinstance(playlists_usuario, dict) else {},
            historico if isinstance(historico, dict) else {},
            atuais,
        )
        self._ultima_sincronizacao_alterou = sincronizadas != atuais
        if self._ultima_sincronizacao_alterou:
            if self.save(sincronizadas):
                self._gravacoes += 1
                if callable(self.publicar_cooperacao):
                    try:
                        self.publicar_cooperacao({
                            "playlists_usuario": sum(
                                isinstance(itens, list)
                                for itens in playlists_usuario.values()
                            ),
                            "registros_historico": sum(
                                len(bloco.get("musicas") or ())
                                for bloco in historico.values()
                                if isinstance(bloco, dict)
                            ),
                            "curadorias": sum(
                                isinstance(itens, list)
                                for itens in sincronizadas.values()
                            ),
                        })
                    except Exception:
                        self._falhas += 1
            else:
                self._falhas += 1
        else:
            self._sync_cache(atuais)
        return sincronizadas

    @staticmethod
    def _nome_falado(nome: str) -> str:
        chave = str(nome or "").strip().casefold()
        aliases = {
            "xodos_que_eu_seperei": "xodós que eu separei",
            "climas_que_combinam_com_voce": "climas que combinam com você",
            "descobertas_da_laylay": "descobertas da Laylay",
        }
        return aliases.get(chave, chave.replace("_", " ").strip())

    def listar(self, nome: str = "") -> str:
        data = self.sincronizar()
        nome_limpo = limpar_nome_playlist(nome or "")
        if nome_limpo:
            nome_norm = self._nome_falado(nome_limpo).casefold()
            aliases = {
                "xodós que eu separei": "xodos_que_eu_seperei",
                "xodos que eu separei": "xodos_que_eu_seperei",
                "xodos que eu seperei": "xodos_que_eu_seperei",
                "climas que combinam comigo": "climas_que_combinam_com_voce",
                "climas que combinam com você": "climas_que_combinam_com_voce",
                "climas que combinam com voce": "climas_que_combinam_com_voce",
            }
            chave_real = aliases.get(nome_norm, nome_limpo)
            if chave_real not in data:
                candidatos = [
                    chave for chave in data
                    if self._nome_falado(chave).casefold() == nome_norm
                ]
                chave_real = candidatos[0] if len(candidatos) == 1 else chave_real
            itens = data.get(chave_real)
            itens = itens if isinstance(itens, list) else []
            return fala_playlist_conteudo_estilosa(
                {
                    "name": self._nome_falado(chave_real),
                    "total": len(itens),
                    "last_titles": [
                        yt_clean_title(str(item.get("titulo") or ""))
                        for item in itens[:3]
                        if isinstance(item, dict)
                    ],
                },
                self._nome_falado(chave_real),
                proprietario="laylay",
            )

        nomes = []
        for chave, itens in sorted(data.items(), key=lambda kv: str(kv[0]).lower()):
            total = len(itens) if isinstance(itens, list) else 0
            nomes.append(f"{self._nome_falado(chave)} ({total})")
        if not nomes:
            return "Eu ainda não montei playlists minhas por aqui."
        return f"As minhas playlists são: {', '.join(nomes)}."

    def diagnostico(self) -> dict[str, Any]:
        data = self.load()
        return {
            "disponivel": True,
            "playlists": sum(isinstance(itens, list) for itens in data.values()),
            "sincronizacoes": self._sincronizacoes,
            "gravacoes": self._gravacoes,
            "ultima_sincronizacao_alterou": self._ultima_sincronizacao_alterou,
            "falhas": self._falhas,
            "usa_historico": True,
            "cooperacao_habilitada": callable(self.publicar_cooperacao),
        }

    def retrato_para_mente(self, texto: str = "") -> dict[str, Any]:
        """Resume a curadoria própria sem entregar URLs ao prompt."""
        data = self.load()
        playlists = [
            {"nome": str(nome), "total": len(itens) if isinstance(itens, list) else 0}
            for nome, itens in sorted(data.items(), key=lambda item: str(item[0]).casefold())
            if str(nome or "").strip()
        ]
        consulta = unicodedata.normalize("NFKD", str(texto or "").casefold())
        consulta = "".join(ch for ch in consulta if not unicodedata.combining(ch))
        detalhe: dict[str, Any] = {}
        for nome, itens in data.items():
            nome_norm = unicodedata.normalize("NFKD", str(nome).casefold())
            nome_norm = "".join(ch for ch in nome_norm if not unicodedata.combining(ch))
            nome_falado = nome_norm.replace("_", " ")
            aliases = {nome_falado}
            if nome_norm == "xodos_que_eu_seperei":
                # A chave histórica nasceu com "seperei"; a conversa usa a
                # grafia natural sem exigir migração destrutiva do arquivo.
                aliases.add("xodos que eu separei")
            elif nome_norm == "climas_que_combinam_com_voce":
                aliases.add("climas que combinam comigo")
            consulta_falada = consulta.replace("_", " ")
            if not nome_falado or not any(alias in consulta_falada for alias in aliases):
                continue
            titulos = [
                yt_clean_title(str(item.get("titulo") or ""))
                for item in itens if isinstance(item, dict) and item.get("titulo")
            ] if isinstance(itens, list) else []
            detalhe = {"nome": str(nome), "titulos": [item for item in titulos if item][:8]}
            break
        return {"playlists": playlists[:30], "detalhe": detalhe}

    def copiar_faixa(
        self,
        nome_playlist_laylay: str,
        musica: str,
        destino_usuario: str,
    ) -> dict:
        data = self.sincronizar()
        faixa = encontrar_faixa_playlist(data, nome_playlist_laylay, musica)
        if not faixa:
            return {"ok": False, "erro": "nao_encontrada"}
        resultado = self.adicionar_playlist_usuario(
            destino_usuario,
            str(faixa.get("url") or ""),
            str(faixa.get("titulo") or ""),
            str(faixa.get("canal") or ""),
        )
        return {
            "ok": bool(isinstance(resultado, dict) and resultado.get("ok")),
            "faixa": faixa,
            "destino": destino_usuario,
        }


def criar_playlist_laylay_runtime(**kwargs: Any) -> PlaylistLaylayRuntime:
    return PlaylistLaylayRuntime(**kwargs)
