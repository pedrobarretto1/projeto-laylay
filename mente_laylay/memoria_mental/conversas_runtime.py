"""Conversas persistentes com contexto isolado e memória global compartilhada."""

from __future__ import annotations

import threading
import re
from typing import Any, Callable, Dict, Mapping, Sequence

from mente_laylay.memoria_mental.estado_continuidades import (
    estado_continuidades_inicial,
)
from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao


_CAMPOS_MENTAIS_CONVERSA = frozenset({
    "ultima_entrada", "ultima_entrada_ts", "ultimas_entradas",
    "ultima_intencao", "ultimo_alvo", "ultimo_escopo", "ultima_habilidade",
    "ultimo_app_janela", "ultimo_site_aba", "ultimo_layout_janelas",
    "ultima_pasta", "ultimo_arquivo", "ultimo_caminho_arquivo",
    "ultimo_dispositivo_iot", "ultimo_ambiente_iot", "ultimo_estado_iot",
    "ultima_resposta", "direcao_fala_atual", "historico_direcao_fala",
    "ultima_afirmacao", "ultima_pergunta", "ultima_opiniao",
    "ultima_brincadeira", "resposta_esperada", "assunto_da_fala",
    "emocao_da_fala", "pendencia_atual", "ultima_pendencia_encerrada",
    "pendencia_acao_canonica", "oferta_pendente", "continuidade_geral",
    "ultimo_resumo_pagina", "capacidade_futura", "conteudo_atual",
    "focos_por_dominio", "assunto_estruturado_atual",
    "correcao_interpretacao_pendente", "alvo_corrigido", "alvo_corrigido_ts",
    "ultima_reparacao_alvo_anterior", "ultima_reparacao_alvo_novo",
    "ultima_reparacao_tipo", "ultima_reparacao_ts",
})

_PREFIXOS_MENTAIS_CONVERSA = (
    "pergunta_aberta_", "ultima_promessa_", "foco_vivo_",
    "foco_conversacional_", "foco_operacional_", "topico_explicito_",
    "ultima_acao_", "ultima_estrutura_arquivo_",
)

_CAMPOS_CONVERSACIONAIS_CONVERSA = frozenset({
    "current_emotion", "emotion_level", "emotion_cause",
    "emotion_started_at", "emotion_duration_s", "emotion_interactions_total",
    "emotion_interactions_left", "emotion_last_decay_at",
    "topicos_conversa_recente", "ultimo_topico_conversa", "ultimo_topico_ts",
})


def _pertence_ao_contexto_mental(chave: str) -> bool:
    return bool(
        chave in _CAMPOS_MENTAIS_CONVERSA
        or any(chave.startswith(prefixo) for prefixo in _PREFIXOS_MENTAIS_CONVERSA)
    )


def capturar_contexto_conversa(estado: Any) -> Dict[str, Any]:
    """Projeta só contexto do chat; identidade e aprendizado ficam globais."""
    snapshot = dict(estado.snapshot() or {})
    mental = dict(snapshot.get("mental") or {})
    conversacional = dict(snapshot.get("conversacional") or {})
    continuidades = dict(snapshot.get("continuidades") or {})
    return {
        "versao": 1,
        "mental": {
            chave: valor
            for chave, valor in mental.items()
            if _pertence_ao_contexto_mental(str(chave))
            and chave not in {
                "turno_atual", "plano_turno_atual", "contrato_fala_atual",
                "retrato_turno_atual", "especialistas_turno_atual",
            }
        },
        "conversacional": {
            chave: valor
            for chave, valor in conversacional.items()
            if chave in _CAMPOS_CONVERSACIONAIS_CONVERSA
        },
        "continuidades": {
            chave: valor
            for chave, valor in continuidades.items()
            if chave != "sugestoes_bloqueadas_ate"
        },
        "historico_long_term": str(
            dict(snapshot.get("memoria_conversa") or {}).get(
                "historico_long_term", "",
            ) or ""
        )[:32_000],
    }


def aplicar_contexto_conversa(
    estado: Any,
    *,
    contexto: Mapping[str, Any] | None,
    mensagens: Sequence[Mapping[str, Any]] | None,
    resumo: str,
    base_system_prompt: str,
) -> None:
    """Troca o chat ativo preservando estado global e limpando referências."""
    dados = dict(contexto or {})
    atual = dict(estado.snapshot() or {})
    mental_atual = dict(atual.get("mental") or {})
    conversa_atual = dict(atual.get("conversacional") or {})
    memoria_atual = dict(atual.get("memoria_conversa") or {})
    mental_limpo, conversa_limpa, _ = renovar_contexto_sessao(
        mental_atual,
        conversa_atual,
        list(memoria_atual.get("messages") or []),
        motivo="troca_conversa",
        ativa=True,
    )

    iniciais = criar_estado_mental_inicial()
    chaves_para_limpar = {
        chave for chave in set(mental_limpo) | set(iniciais)
        if _pertence_ao_contexto_mental(str(chave))
    }
    for chave in chaves_para_limpar:
        if chave in iniciais:
            mental_limpo[chave] = iniciais[chave]
        else:
            valor = mental_limpo.get(chave)
            mental_limpo[chave] = (
                [] if isinstance(valor, list)
                else {} if isinstance(valor, dict)
                else False if isinstance(valor, bool)
                else 0.0 if chave.endswith(("_ts", "_at"))
                else ""
            )
    mental_salvo = dict(dados.get("mental") or {})
    mental_limpo.update({
        chave: valor for chave, valor in mental_salvo.items()
        if _pertence_ao_contexto_mental(str(chave))
    })

    conversa_salva = dict(dados.get("conversacional") or {})
    conversa_limpa.update({
        chave: valor for chave, valor in conversa_salva.items()
        if chave in _CAMPOS_CONVERSACIONAIS_CONVERSA
    })

    bloqueios_globais = dict(
        dict(atual.get("continuidades") or {}).get(
            "sugestoes_bloqueadas_ate", {},
        ) or {}
    )
    continuidades = estado_continuidades_inicial()
    continuidades.update(dict(dados.get("continuidades") or {}))
    continuidades["sugestoes_bloqueadas_ate"] = bloqueios_globais

    mensagens_validas = [
        dict(item) for item in (mensagens or []) if isinstance(item, Mapping)
    ]
    mensagens_validas = [
        item for item in mensagens_validas
        if str(item.get("role") or "").casefold() != "system"
    ]
    mensagens_validas.insert(0, {
        "role": "system", "content": str(base_system_prompt or ""),
    })
    memoria_atual.update({
        "messages": mensagens_validas,
        "resumo_conversa": str(resumo or "")[:16_000],
        "historico_long_term": str(
            dados.get("historico_long_term") or "",
        )[:32_000],
    })

    estado.substituir("mental", mental_limpo)
    estado.substituir("conversacional", conversa_limpa)
    estado.substituir("continuidades", continuidades)
    estado.substituir("memoria_conversa", memoria_atual)


class GerenciadorConversasRuntime:
    """Coordena CRUD, troca atômica e persistência do chat ativo."""

    def __init__(
        self,
        *,
        memoria_sqlite: Any,
        estado_compartilhado: Any,
        base_system_prompt: str,
        log: Callable[..., Any] = print,
    ) -> None:
        self.memoria_sqlite = memoria_sqlite
        self.estado = estado_compartilhado
        self.base_system_prompt = str(base_system_prompt or "")
        self.log = log
        self._lock = threading.RLock()
        self._ativa_id = ""
        # O catálogo pode existir, mas selecionar um chat é sempre uma ação da
        # sessão atual. A ponte sobe antes da carga completa da memória.
        self._sessao_sem_conversa = True

    def id_ativo(self) -> str:
        with self._lock:
            if self._sessao_sem_conversa:
                return ""
            return self._ativa_id or str(
                self.memoria_sqlite.conversa_ativa_id() or ""
            )

    def _mensagens_ativas(self) -> list[Dict[str, Any]]:
        return [
            dict(item)
            for item in list(self.estado.memoria_conversa_get("messages", []) or [])
            if isinstance(item, Mapping)
        ]

    def _resumo_ativo(self) -> str:
        return str(
            self.estado.memoria_conversa_get("resumo_conversa", "") or ""
        )

    def inicializar_legado(
        self,
        *,
        mensagens: Sequence[Mapping[str, Any]] | None,
        resumo: str = "",
        selecionar: bool = True,
    ) -> Dict[str, Any]:
        with self._lock:
            conversa = self.memoria_sqlite.garantir_conversa_inicial(
                mensagens_legadas=mensagens,
                resumo_legado=resumo,
                contexto_legado=capturar_contexto_conversa(self.estado),
            )
            if not conversa:
                raise RuntimeError("não foi possível inicializar conversa canônica")
            if selecionar:
                self._sessao_sem_conversa = False
                self._ativa_id = str(conversa["id"])
                aplicar_contexto_conversa(
                    self.estado,
                    contexto=conversa.get("contexto"),
                    mensagens=conversa.get("mensagens"),
                    resumo=str(conversa.get("resumo") or ""),
                    base_system_prompt=self.base_system_prompt,
                )
            return dict(conversa)

    def salvar_ativa(self) -> bool:
        with self._lock:
            conversa_id = self.id_ativo()
            if not conversa_id:
                # Uma sessão neutra não possui chat para persistir. Isso não é
                # falha: a memória global continua sendo salva normalmente.
                return True
            return bool(self.memoria_sqlite.salvar_conversa(
                conversa_id,
                mensagens=self._mensagens_ativas(),
                resumo=self._resumo_ativo(),
                contexto=capturar_contexto_conversa(self.estado),
            ))

    def reaplicar_ativa(self) -> bool:
        """Restaura contexto do chat depois de carregar a memória global."""
        with self._lock:
            if self._sessao_sem_conversa:
                return True
            conversa_id = self.id_ativo()
            conversa = self.memoria_sqlite.carregar_conversa(conversa_id)
            if not conversa:
                return False
            aplicar_contexto_conversa(
                self.estado,
                contexto=conversa.get("contexto"),
                mensagens=conversa.get("mensagens"),
                resumo=str(conversa.get("resumo") or ""),
                base_system_prompt=self.base_system_prompt,
            )
            return True

    def iniciar_sem_conversa(self) -> None:
        """Abre a sessão sem selecionar nem modificar chats persistidos."""
        with self._lock:
            self._sessao_sem_conversa = True
            self._ativa_id = ""
            aplicar_contexto_conversa(
                self.estado,
                contexto={},
                mensagens=[],
                resumo="",
                base_system_prompt=self.base_system_prompt,
            )

    def garantir_para_entrada(self, titulo: str = "Nova conversa") -> str:
        """Cria atomicamente o chat que receberá a primeira entrada da sessão."""
        with self._lock:
            conversa_id = self.id_ativo()
            if conversa_id:
                return conversa_id
            conversa = self.criar(titulo)
            return str(conversa.get("id") or "")

    def listar(self, *, incluir_arquivadas: bool = False) -> list[Dict[str, Any]]:
        return self.memoria_sqlite.listar_conversas(
            incluir_arquivadas=incluir_arquivadas,
        )

    def listar_para_terminal(self) -> list[Dict[str, Any]]:
        """Projeta chats ativos e arquivados; a ponte remove o conteúdo."""
        return self.listar(incluir_arquivadas=True)

    def criar(self, titulo: str = "Nova conversa") -> Dict[str, Any]:
        with self._lock:
            if self._ativa_id:
                self.salvar_ativa()
            conversa = self.memoria_sqlite.criar_conversa(
                titulo=titulo,
                mensagens=[{
                    "role": "system", "content": self.base_system_prompt,
                }],
                contexto={},
                ativar=True,
            )
            self._sessao_sem_conversa = False
            self._ativa_id = str(conversa["id"])
            aplicar_contexto_conversa(
                self.estado,
                contexto={},
                mensagens=conversa.get("mensagens"),
                resumo="",
                base_system_prompt=self.base_system_prompt,
            )
            return dict(conversa)

    def selecionar(self, conversa_id: str) -> Dict[str, Any] | None:
        identificador = str(conversa_id or "").strip()
        with self._lock:
            if not identificador:
                return None
            if identificador == self.id_ativo():
                return self.memoria_sqlite.carregar_conversa(identificador)
            if self._ativa_id and not self.salvar_ativa():
                return None
            conversa = self.memoria_sqlite.carregar_conversa(identificador)
            if not conversa or conversa.get("status") != "ativa":
                return None
            if not self.memoria_sqlite.selecionar_conversa(identificador):
                return None
            self._sessao_sem_conversa = False
            self._ativa_id = identificador
            aplicar_contexto_conversa(
                self.estado,
                contexto=conversa.get("contexto"),
                mensagens=conversa.get("mensagens"),
                resumo=str(conversa.get("resumo") or ""),
                base_system_prompt=self.base_system_prompt,
            )
            return dict(conversa)

    def mensagens(self, conversa_id: str | None = None) -> list[Dict[str, Any]]:
        identificador = str(conversa_id or self.id_ativo()).strip()
        with self._lock:
            if identificador and identificador == self.id_ativo():
                return self._mensagens_ativas()
            conversa = self.memoria_sqlite.carregar_conversa(identificador)
            return [
                dict(item) for item in list((conversa or {}).get("mensagens") or [])
                if isinstance(item, Mapping)
            ]

    def substituir_mensagens(
        self,
        mensagens: Sequence[Mapping[str, Any]],
        conversa_id: str | None = None,
    ) -> bool:
        identificador = str(conversa_id or self.id_ativo()).strip()
        with self._lock:
            if not identificador:
                return False
            conversa = self.memoria_sqlite.carregar_conversa(identificador)
            if not conversa:
                return False
            novas = [dict(item) for item in mensagens if isinstance(item, Mapping)]
            if identificador == self.id_ativo():
                self.estado.atualizar_campos("memoria_conversa", messages=novas)
                resumo = self._resumo_ativo()
                contexto = capturar_contexto_conversa(self.estado)
            else:
                resumo = str(conversa.get("resumo") or "")
                contexto = dict(conversa.get("contexto") or {})
            return bool(self.memoria_sqlite.salvar_conversa(
                identificador,
                mensagens=novas,
                resumo=resumo,
                contexto=contexto,
            ))

    def renomear(self, conversa_id: str, titulo: str) -> bool:
        return bool(self.memoria_sqlite.renomear_conversa(conversa_id, titulo))

    def fixar(self, conversa_id: str, fixada: bool) -> bool:
        """Ordena um chat importante sem alterar seu contexto ou conteúdo."""
        return bool(self.memoria_sqlite.fixar_conversa(conversa_id, fixada))

    def arquivar(self, conversa_id: str) -> bool:
        """Retira um chat dos recentes preservando seu contexto isolado."""
        identificador = str(conversa_id or "").strip()
        with self._lock:
            if not identificador:
                return False
            era_ativa = identificador == self.id_ativo()
            if era_ativa and not self.salvar_ativa():
                return False
            if not self.memoria_sqlite.arquivar_conversa(identificador):
                return False
            if not era_ativa:
                return True
            self._ativa_id = ""
            restantes = self.memoria_sqlite.listar_conversas(limite=1)
            if restantes:
                return self.selecionar(str(restantes[0]["id"])) is not None
            self.criar("Nova conversa")
            return True

    def desarquivar(self, conversa_id: str) -> bool:
        """Devolve o chat aos recentes sem ativá-lo silenciosamente."""
        return bool(self.memoria_sqlite.desarquivar_conversa(conversa_id))

    def nomear_automaticamente(self, conversa_id: str, texto: str) -> bool:
        """Nomeia apenas um chat novo; nunca sobrescreve título escolhido."""
        identificador = str(conversa_id or "").strip()
        entrada = re.sub(r"\s+", " ", str(texto or "")).strip()
        if not identificador or not entrada:
            return False
        with self._lock:
            conversa = self.memoria_sqlite.carregar_conversa(identificador)
            if not conversa or str(conversa.get("titulo") or "") != "Nova conversa":
                return False
            mensagens_usuario = [
                item for item in list(conversa.get("mensagens") or [])
                if isinstance(item, Mapping)
                and str(item.get("role") or "").casefold() == "user"
            ]
            if len(mensagens_usuario) > 1:
                return False
            titulo = entrada[:46].rstrip(" .,:;!?") or "Nova conversa"
            return bool(self.memoria_sqlite.renomear_conversa(
                identificador, titulo,
            ))

    def excluir(self, conversa_id: str) -> bool:
        identificador = str(conversa_id or "").strip()
        with self._lock:
            if not identificador:
                return False
            era_ativa = identificador == self.id_ativo()
            if not self.memoria_sqlite.excluir_conversa(identificador):
                return False
            if not era_ativa:
                return True
            self._ativa_id = ""
            restantes = self.memoria_sqlite.listar_conversas(limite=1)
            if restantes:
                return self.selecionar(str(restantes[0]["id"])) is not None
            self.criar("Nova conversa")
            return True

    def diagnostico(self) -> Dict[str, Any]:
        conversas = self.listar(incluir_arquivadas=True)
        return {
            "disponivel": True,
            "conversa_ativa_id": self.id_ativo(),
            "conversas": len(conversas),
            "conversas_arquivadas": sum(
                1 for item in conversas if item.get("status") == "arquivada"
            ),
            "conversas_fixadas": sum(
                1 for item in conversas if bool(item.get("fixada"))
            ),
            "isolamento_contexto": True,
            "memoria_global_compartilhada": True,
            "autoriza_execucao": False,
        }


def criar_gerenciador_conversas_runtime(**kwargs: Any) -> GerenciadorConversasRuntime:
    return GerenciadorConversasRuntime(**kwargs)
