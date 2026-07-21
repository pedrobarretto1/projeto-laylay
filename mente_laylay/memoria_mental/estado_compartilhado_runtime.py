"""Contêiner dos estados vivos compartilhados pela mente da Laylay."""

from __future__ import annotations

import copy
import threading
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.estado_continuidades import atualizar_continuidades
from mente_laylay.memoria_mental.estado_continuidades import limpar_sugestao_atual
from mente_laylay.memoria_mental.contexto_compartilhado import (
    contexto_mental_ativo,
    contexto_musical_ativo,
)
from mente_laylay.memoria_mental.estado_musical import atualizar_estado_musical
from mente_laylay.memoria_mental.estado_percepcao import atualizar_estado_percepcao


class DictEstadoSincronizado(dict):
    """Dicionario legado protegido pelo mesmo lock da mente compartilhada."""

    def __init__(self, dados: Dict[str, Any] | None, lock: threading.RLock) -> None:
        super().__init__(dados or {})
        self._estado_lock = lock

    def __setitem__(self, chave: Any, valor: Any) -> None:
        with self._estado_lock:
            super().__setitem__(chave, valor)

    def __delitem__(self, chave: Any) -> None:
        with self._estado_lock:
            super().__delitem__(chave)

    def clear(self) -> None:
        with self._estado_lock:
            super().clear()

    def pop(self, chave: Any, *args: Any) -> Any:
        with self._estado_lock:
            return super().pop(chave, *args)

    def popitem(self) -> tuple[Any, Any]:
        with self._estado_lock:
            return super().popitem()

    def setdefault(self, chave: Any, default: Any = None) -> Any:
        with self._estado_lock:
            return super().setdefault(chave, default)

    def update(self, *args: Any, **kwargs: Any) -> None:
        with self._estado_lock:
            super().update(*args, **kwargs)

    def copia(self) -> Dict[str, Any]:
        with self._estado_lock:
            return dict(super().items())


class ListaEstadoSincronizada(list):
    """Lista viva cujas mutações usam o lock central da mente."""

    def __init__(self, dados: list[Any] | None, lock: threading.RLock) -> None:
        super().__init__(dados or [])
        self._estado_lock = lock

    def append(self, item: Any) -> None:
        with self._estado_lock:
            super().append(item)

    def extend(self, itens: Any) -> None:
        with self._estado_lock:
            super().extend(itens)

    def insert(self, indice: int, item: Any) -> None:
        with self._estado_lock:
            super().insert(indice, item)

    def clear(self) -> None:
        with self._estado_lock:
            super().clear()

    def pop(self, indice: int = -1) -> Any:
        with self._estado_lock:
            return super().pop(indice)

    def remove(self, item: Any) -> None:
        with self._estado_lock:
            super().remove(item)

    def __setitem__(self, indice: Any, valor: Any) -> None:
        with self._estado_lock:
            super().__setitem__(indice, valor)

    def __delitem__(self, indice: Any) -> None:
        with self._estado_lock:
            super().__delitem__(indice)

    def __iadd__(self, itens: Any):
        with self._estado_lock:
            super().__iadd__(itens)
            return self

    def sort(self, *args: Any, **kwargs: Any) -> None:
        with self._estado_lock:
            super().sort(*args, **kwargs)

    def reverse(self) -> None:
        with self._estado_lock:
            super().reverse()

    def copia(self) -> list[Any]:
        with self._estado_lock:
            return list(super().__iter__())


class EstadoCompartilhadoRuntime:
    """Centraliza estados simples sem esconder os dicionários dos módulos legados."""

    def __init__(
        self,
        *,
        continuidades: Dict[str, Any] | None = None,
        musical: Dict[str, Any] | None = None,
        percepcao: Dict[str, Any] | None = None,
        mental: Dict[str, Any] | None = None,
        conversacional: Dict[str, Any] | None = None,
        memoria_conversa: Dict[str, Any] | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self.continuidades = self._preparar_dominio(continuidades)
        self.musical = self._preparar_dominio(musical)
        self.percepcao = self._preparar_dominio(percepcao)
        self.mental = self._preparar_dominio(mental)
        self.conversacional = self._preparar_dominio(conversacional)
        self.memoria_conversa = self._preparar_dominio(memoria_conversa)

    def obter(self, dominio: str, chave: str, default: Any = None) -> Any:
        with self._lock:
            return self._estado(dominio).get(chave, default)

    def obter_copia(self, dominio: str, chave: str, default: Any = None) -> Any:
        """Entrega uma leitura isolada para consumidores que nao devem mutar a mente."""
        with self._lock:
            valor = self._estado(dominio).get(chave, default)
            return self._copiar_valor(valor)

    def atualizar(
        self,
        dominio: str,
        atualizador: Callable[..., Dict[str, Any]],
        **campos: Any,
    ) -> Dict[str, Any]:
        with self._lock:
            atual = self._estado(dominio)
            novo = atualizador(atual, **campos) if callable(atualizador) else atual
            return self.substituir(dominio, novo)

    def substituir(self, dominio: str, estado: Dict[str, Any] | None) -> Dict[str, Any]:
        with self._lock:
            novo = self._preparar_dominio(estado)
            nome = self._nome_atributo(dominio)
            setattr(self, nome, novo)
            return novo

    def atualizar_campos(self, dominio: str, **campos: Any) -> Dict[str, Any]:
        with self._lock:
            novo = dict(self._estado(dominio))
            novo.update(campos)
            return self.substituir(dominio, novo)

    def mesclar_campos(self, dominio: str, **campos: Any) -> Dict[str, Any]:
        """Mescla um retrato externo preservando coleções já vinculadas."""
        with self._lock:
            estado = self._estado(dominio)
            novo = dict(estado)
            for chave, valor in campos.items():
                atual = estado.get(chave)
                if isinstance(atual, DictEstadoSincronizado) and isinstance(valor, dict):
                    atual.clear()
                    atual.update({
                        item_chave: self._preparar_valor(item_valor)
                        for item_chave, item_valor in valor.items()
                    })
                    novo[chave] = atual
                elif isinstance(atual, ListaEstadoSincronizada) and isinstance(valor, list):
                    atual[:] = [self._preparar_valor(item) for item in valor]
                    novo[chave] = atual
                else:
                    novo[chave] = self._preparar_valor(valor)
            setattr(self, self._nome_atributo(dominio), novo)
            return novo

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {
                "continuidades": self._copiar_dominio(self.continuidades),
                "musical": self._copiar_dominio(self.musical),
                "percepcao": self._copiar_dominio(self.percepcao),
                "mental": self._copiar_dominio(self.mental),
                "conversacional": self._copiar_dominio(self.conversacional),
                "memoria_conversa": self._copiar_dominio(self.memoria_conversa),
            }

    def vincular_dict(
        self,
        dominio: str,
        chave: str,
        default: Dict[str, Any] | None = None,
    ) -> DictEstadoSincronizado:
        """Mantem compatibilidade com dicts legados sem escapar do lock central."""
        with self._lock:
            estado = self._estado(dominio)
            atual = estado.get(chave)
            if isinstance(atual, DictEstadoSincronizado):
                return atual
            dados = atual if isinstance(atual, dict) else (default or {})
            vinculado = DictEstadoSincronizado(dados, self._lock)
            novo = dict(estado)
            novo[chave] = vinculado
            setattr(self, self._nome_atributo(dominio), novo)
            return vinculado

    def vincular_lista(
        self,
        dominio: str,
        chave: str,
        default: list[Any] | None = None,
    ) -> ListaEstadoSincronizada:
        """Vincula listas legadas ao mesmo estado e lock usados pela mente."""
        with self._lock:
            estado = self._estado(dominio)
            atual = estado.get(chave)
            if isinstance(atual, ListaEstadoSincronizada):
                return atual
            dados = atual if isinstance(atual, list) else (default or [])
            vinculada = ListaEstadoSincronizada(dados, self._lock)
            novo = dict(estado)
            novo[chave] = vinculada
            setattr(self, self._nome_atributo(dominio), novo)
            return vinculada

    def validar_estrutura(self) -> Dict[str, Any]:
        """Valida os contratos minimos que mantem os modulos na mesma mente."""
        obrigatorios = {
            "continuidades": ("comando_sugerido_estado", "sugestoes_bloqueadas_ate"),
            "musical": ("playlist_state", "ultima_playlist"),
            "percepcao": (
                "aba_ativa", "logs_navegador", "ultimo_open_site",
                "abas_sugeridas_fechar", "fish_mode_active", "fish_mode_started_ts",
            ),
            "mental": (
                "ultima_intencao", "ultima_acao_status", "consciencia_temporal",
                "falhas_consecutivas_execucao",
            ),
            "conversacional": ("current_emotion", "is_speaking"),
            "memoria_conversa": ("messages", "memoria_fatos", "memoria_eventos"),
        }
        ausentes: list[str] = []
        invalidos: list[str] = []
        with self._lock:
            for dominio, chaves in obrigatorios.items():
                estado = self._estado(dominio)
                if not isinstance(estado, dict):
                    invalidos.append(dominio)
                    continue
                for chave in chaves:
                    if chave not in estado:
                        ausentes.append(f"{dominio}.{chave}")
            playlist = self.musical.get("playlist_state")
            if not isinstance(playlist, dict):
                invalidos.append("musical.playlist_state")
            aba = self.percepcao.get("aba_ativa")
            if not isinstance(aba, dict):
                invalidos.append("percepcao.aba_ativa")
            if not isinstance(self.continuidades.get("sugestoes_bloqueadas_ate"), dict):
                invalidos.append("continuidades.sugestoes_bloqueadas_ate")
            if not isinstance(self.percepcao.get("abas_sugeridas_fechar"), list):
                invalidos.append("percepcao.abas_sugeridas_fechar")
            if not isinstance(self.mental.get("falhas_consecutivas_execucao"), dict):
                invalidos.append("mental.falhas_consecutivas_execucao")
        return {
            "ok": not ausentes and not invalidos,
            "ausentes": ausentes,
            "invalidos": invalidos,
        }

    def continuidades_get(self, chave: str, default: Any = None) -> Any:
        return self.obter("continuidades", chave, default)

    def continuidades_set(self, chave: str, valor: Any) -> Any:
        self.atualizar(
            "continuidades",
            atualizar_continuidades,
            **{chave: valor},
        )
        return valor

    def continuidades_update(self, **campos: Any) -> Dict[str, Any]:
        return self.atualizar(
            "continuidades",
            atualizar_continuidades,
            **campos,
        )

    def limpar_sugestao(self) -> Dict[str, Any]:
        return self.substituir(
            "continuidades",
            limpar_sugestao_atual(self.continuidades),
        )

    def contexto_musical_ativo(self, playlist_state: Dict[str, Any] | None = None) -> bool:
        return contexto_musical_ativo(
            self.musica_get("ultima_playlist"),
            playlist_state or {},
        )

    def contexto_mental_ativo(self, playlist_state: Dict[str, Any] | None = None) -> bool:
        return contexto_mental_ativo(
            self.mental,
            self.musica_get("ultima_playlist"),
            playlist_state or {},
        )

    def musica_get(self, chave: str, default: Any = None) -> Any:
        return self.obter("musical", chave, default)

    def musica_set(self, chave: str, valor: Any) -> Any:
        self.atualizar("musical", atualizar_estado_musical, **{chave: valor})
        return valor

    def percepcao_get(self, chave: str, default: Any = None) -> Any:
        return self.obter("percepcao", chave, default)

    def percepcao_set(self, chave: str, valor: Any) -> Any:
        self.atualizar("percepcao", atualizar_estado_percepcao, **{chave: valor})
        return valor

    def conversa_get(self, chave: str, default: Any = None) -> Any:
        return self.obter("conversacional", chave, default)

    def memoria_conversa_get(self, chave: str, default: Any = None) -> Any:
        return self.obter("memoria_conversa", chave, default)

    def _estado(self, dominio: str) -> Dict[str, Any]:
        return getattr(self, self._nome_atributo(dominio))

    @staticmethod
    def _copiar_valor(valor: Any) -> Any:
        if isinstance(valor, DictEstadoSincronizado):
            valor = valor.copia()
        if isinstance(valor, ListaEstadoSincronizada):
            valor = valor.copia()
        if isinstance(valor, dict):
            return {chave: EstadoCompartilhadoRuntime._copiar_valor(item) for chave, item in valor.items()}
        if isinstance(valor, list):
            return [EstadoCompartilhadoRuntime._copiar_valor(item) for item in valor]
        if isinstance(valor, tuple):
            return tuple(EstadoCompartilhadoRuntime._copiar_valor(item) for item in valor)
        try:
            return copy.deepcopy(valor)
        except Exception:
            if isinstance(valor, dict):
                return dict(valor)
            if isinstance(valor, list):
                return list(valor)
            return valor

    def _preparar_dominio(self, estado: Dict[str, Any] | None) -> Dict[str, Any]:
        return {
            chave: self._preparar_valor(valor)
            for chave, valor in dict(estado or {}).items()
        }

    def _preparar_valor(self, valor: Any) -> Any:
        if isinstance(valor, (DictEstadoSincronizado, ListaEstadoSincronizada)):
            return valor
        if isinstance(valor, dict):
            return DictEstadoSincronizado(
                {chave: self._preparar_valor(item) for chave, item in valor.items()},
                self._lock,
            )
        if isinstance(valor, list):
            return ListaEstadoSincronizada(
                [self._preparar_valor(item) for item in valor],
                self._lock,
            )
        return valor

    @classmethod
    def _copiar_dominio(cls, estado: Dict[str, Any]) -> Dict[str, Any]:
        return {chave: cls._copiar_valor(valor) for chave, valor in estado.items()}

    @staticmethod
    def _nome_atributo(dominio: str) -> str:
        nome = str(dominio or "").strip().lower()
        aliases = {
            "continuidade": "continuidades",
            "continuidades": "continuidades",
            "musica": "musical",
            "música": "musical",
            "musical": "musical",
            "percepcao": "percepcao",
            "percepção": "percepcao",
            "mente": "mental",
            "mental": "mental",
            "conversa": "conversacional",
            "conversacional": "conversacional",
            "memoria": "memoria_conversa",
            "memoria_conversa": "memoria_conversa",
        }
        if nome not in aliases:
            raise KeyError(f"Domínio de estado desconhecido: {dominio}")
        return aliases[nome]


def criar_estado_compartilhado_runtime(**kwargs: Any) -> EstadoCompartilhadoRuntime:
    return EstadoCompartilhadoRuntime(**kwargs)
