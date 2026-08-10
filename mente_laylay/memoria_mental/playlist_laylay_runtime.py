"""Runtime das playlists proprias da Laylay.

Mantem persistencia e curadoria em um modulo separado, recebendo os dados da
mente musical compartilhada por callbacks para nao criar um estado paralelo.
"""

from __future__ import annotations

import os
import re
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

    def _resolver_chave(self, nome: str, data: Mapping[str, Any]) -> str:
        """Resolve nome falado, alias ou ordinal sem misturar posse."""
        nome_bruto = str(nome or "").strip()
        chaves = [
            str(chave) for chave, itens in sorted(
                data.items(), key=lambda kv: str(kv[0]).casefold()
            )
            if isinstance(itens, list)
        ]
        ordinal = re.fullmatch(r"#?\s*(\d+)", nome_bruto)
        if ordinal:
            indice = int(ordinal.group(1)) - 1
            return chaves[indice] if 0 <= indice < len(chaves) else ""

        nome_limpo = limpar_nome_playlist(nome_bruto)
        if not nome_limpo:
            return chaves[0] if chaves else ""
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
        if chave_real in data:
            return chave_real
        candidatos = [
            chave for chave in chaves
            if self._nome_falado(chave).casefold() == nome_norm
        ]
        return candidatos[0] if len(candidatos) == 1 else ""

    def detectar_nome_direto_contextual(self, texto: str) -> str:
        """Confirma um nome falado contra as curadorias realmente existentes.

        O detector não adivinha nem escolhe a primeira lista quando o texto
        está vazio. Isso permite usar uma resposta curta como ``climas que
        combinam com você`` sem transformar qualquer frase solta em playlist.
        """
        nome = re.sub(
            r"^\s*(?:a\s+)?playlist\s+",
            "",
            str(texto or "").strip(),
            count=1,
            flags=re.IGNORECASE,
        ).strip(" .,!?:;")
        if not nome:
            return ""
        data = self.load()
        chave = self._resolver_chave(nome, data)
        return self._nome_falado(chave) if chave else ""

    def selecionar(self, nome: str = "", indice_faixa: int = 0) -> dict[str, Any]:
        """Seleciona uma playlist/faixa própria com identidade explícita."""
        data = self.sincronizar()
        chave = self._resolver_chave(nome, data)
        itens = data.get(chave) if chave else None
        if not isinstance(itens, list) or not itens:
            return {
                "ok": False,
                "erro": "playlist_vazia_ou_nao_encontrada",
                "playlist": self._nome_falado(chave or nome),
            }
        indice = max(0, int(indice_faixa or 0))
        if indice >= len(itens):
            return {
                "ok": False,
                "erro": "faixa_nao_encontrada",
                "playlist": self._nome_falado(chave),
            }
        item = itens[indice]
        faixa = dict(item) if isinstance(item, dict) else {"url": str(item or "")}
        return {
            "ok": bool(str(faixa.get("url") or "").strip()),
            "playlist": self._nome_falado(chave),
            "chave": chave,
            "faixa": faixa,
        }

    def listar(self, nome: str = "") -> str:
        data = self.sincronizar()
        nome_bruto = str(nome or "").strip()
        if nome_bruto:
            chave_real = self._resolver_chave(nome_bruto, data)
            if not chave_real:
                return f"Não encontrei uma playlist minha chamada {nome_bruto}."
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
        chave = self._resolver_chave(nome_playlist_laylay, data)
        if str(musica or "").strip() in {"", "__primeira__"}:
            itens = data.get(chave) if chave else None
            faixa = (
                dict(itens[0]) if isinstance(itens, list) and itens
                and isinstance(itens[0], dict) else None
            )
        else:
            faixa = encontrar_faixa_playlist(data, chave or nome_playlist_laylay, musica)
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
            "origem": self._nome_falado(chave or nome_playlist_laylay),
        }


def criar_playlist_laylay_runtime(**kwargs: Any) -> PlaylistLaylayRuntime:
    return PlaylistLaylayRuntime(**kwargs)
