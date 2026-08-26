"""Governança dos planos cooperativos e integração com os porteiros."""

from __future__ import annotations

import threading
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.quadro_cooperacao import QuadroCooperacaoRuntime


class GovernancaPlanoCooperativoRuntime:
    """Liga o plano aos porteiros e registros canônicos da mente única."""

    AUTORIZACOES_VALIDAS = frozenset({
        "explicita_no_pedido", "confirmacao_explicita",
        "autonomia_previamente_concedida", "somente_leitura", "teste_explicito",
    })
    RISCOS_COM_CONFIRMACAO = frozenset({"alto", "destrutivo", "irreversivel"})

    def __init__(
        self,
        *,
        quadro: QuadroCooperacaoRuntime,
        autorizar_acao: Callable[..., Mapping[str, Any]] | None = None,
        registrar_continuidade: Callable[[Mapping[str, Any], str], Any] | None = None,
        registrar_aprendizado: Callable[[Mapping[str, Any], str], Any] | None = None,
        registrar_decisao: Callable[..., Any] | None = None,
        log: Callable[[str], Any] = print,
    ) -> None:
        self.quadro = quadro
        self.autorizar_acao = autorizar_acao
        self.registrar_continuidade = registrar_continuidade
        self.registrar_aprendizado = registrar_aprendizado
        self.registrar_decisao = registrar_decisao
        self.log = log
        self._lock = threading.RLock()
        self._finalizados: set[str] = set()

    def avaliar_autorizacao(
        self,
        plano: Mapping[str, Any],
        etapa: Mapping[str, Any],
        contexto: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        dados = dict(contexto or {})
        autorizacao = str(plano.get("autorizacao") or "").strip().casefold()
        risco = str(plano.get("risco") or "baixo").strip().casefold()
        confirmado = bool(dados.get("confirmado"))
        if autorizacao not in self.AUTORIZACOES_VALIDAS:
            return {"permitido": False, "motivo": "autorizacao_do_plano_invalida"}
        if risco in self.RISCOS_COM_CONFIRMACAO and not confirmado:
            return {"permitido": False, "motivo": "confirmacao_explicita_necessaria"}
        if not callable(self.autorizar_acao):
            self.log(
                "⚠️ [COOPERAÇÃO] porteiro canônico ausente; execução bloqueada"
            )
            return {"permitido": False, "motivo": "porteiro_indisponivel"}
        acao = str(etapa.get("intent") or etapa.get("acao") or "")
        try:
            decisao = dict(self.autorizar_acao(
                acao,
                str(dados.get("texto") or ""),
                confirmado=confirmado,
                origem="orquestracao_cooperativa",
            ) or {})
        except Exception as erro:
            self.log(
                "⚠️ [COOPERAÇÃO] porteiro canônico indisponível | "
                f"erro={type(erro).__name__}"
            )
            return {"permitido": False, "motivo": "porteiro_indisponivel"}
        return {
            "permitido": bool(decisao.get("permitido")),
            "motivo": str(decisao.get("motivo") or "porteiro_negou"),
        }

    def registrar_ciclo(self, plano: Mapping[str, Any], evento: str) -> None:
        if not callable(self.registrar_continuidade):
            return
        try:
            self.registrar_continuidade(self.quadro.plano_publico(plano), str(evento or ""))
        except Exception as erro:
            self.log(
                "⚠️ [COOPERAÇÃO] continuidade não registrada | "
                f"erro={type(erro).__name__}"
            )

    def finalizar(
        self,
        plano: Mapping[str, Any],
        *,
        decisao: str,
        motivo: str,
    ) -> bool:
        plano_id = str(plano.get("id") or "")
        with self._lock:
            if not plano_id or plano_id in self._finalizados:
                return False
            self._finalizados.add(plano_id)
        publico = self.quadro.plano_publico(plano)
        if callable(self.registrar_aprendizado):
            try:
                self.registrar_aprendizado(publico, str(decisao or ""))
            except Exception:
                pass
        if callable(self.registrar_decisao):
            try:
                self.registrar_decisao(
                    "orquestracao_cooperativa", str(decisao or ""),
                    (str(motivo or "")[:160],),
                    categoria=str((publico.get("metadados") or {}).get("fluxo") or "plano"),
                )
            except Exception:
                pass
        self.registrar_ciclo(plano, "finalizado")
        self.quadro.registrar_finalizacao_governanca()
        return True
