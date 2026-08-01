"""Ponte da orquestração cooperativa para os serviços vivos da aplicação."""

from __future__ import annotations

from typing import Any, Callable


class PonteCooperacaoAplicacaoRuntime:
    """Adapta progresso, aprendizado e continuidade sem acessar a raiz."""

    def __init__(
        self,
        *,
        orquestrador_getter: Callable[[], Any | None],
        visao_analise_getter: Callable[[], Any],
        visao_leitura_getter: Callable[[], Any],
        pendencia_jogo_getter: Callable[[], dict[str, Any] | None],
        contexto_jogo_getter: Callable[[], dict[str, Any]],
        detectar_pedido_visao: Callable[[str, dict[str, Any]], dict[str, Any] | None],
        registrar_evidencia: Callable[..., Any],
        estado_mental_atualizar: Callable[[Callable[[dict[str, Any]], dict[str, Any]]], Any],
        registrar_evento_continuidade: Callable[..., dict[str, Any]],
        quadro_getter: Callable[[], Any],
    ) -> None:
        self._orquestrador_getter = orquestrador_getter
        self._visao_analise_getter = visao_analise_getter
        self._visao_leitura_getter = visao_leitura_getter
        self._pendencia_jogo_getter = pendencia_jogo_getter
        self._contexto_jogo_getter = contexto_jogo_getter
        self._detectar_pedido_visao = detectar_pedido_visao
        self._registrar_evidencia = registrar_evidencia
        self._estado_mental_atualizar = estado_mental_atualizar
        self._registrar_evento_continuidade = registrar_evento_continuidade
        self._quadro_getter = quadro_getter

    def registrar_progresso_visao(self, evento: dict[str, Any]) -> bool:
        runtime = self._orquestrador_getter()
        registrar = getattr(runtime, "registrar_progresso_visao_jogo", None)
        return bool(registrar(evento)) if callable(registrar) else False

    def continuar_visao_pendente(self, texto: str) -> bool:
        analise = self._visao_analise_getter()
        if analise.aplicar_referencia_item(texto):
            return True
        if analise.continuar_analise_recente(texto):
            return True
        if analise.continuar_pendencia(texto, self._pendencia_jogo_getter()):
            return True
        return bool(analise.processar_atualizacao_perfil(texto))

    def registrar_aprendizado(self, plano: dict[str, Any], decisao: str) -> bool:
        decisao_normalizada = str(decisao or "").strip().casefold()
        sinal = {
            "aceito": 0.7, "recusado": -0.6, "falhou": -0.35,
            "cancelado": -0.25, "expirado": -0.2,
        }.get(decisao_normalizada)
        if sinal is None:
            return False
        metadados = dict(plano.get("metadados") or {})
        fluxo = str(metadados.get("fluxo") or "plano_cooperativo").strip()[:80]
        habilidades = [
            str(item or "").strip()[:60]
            for item in list(plano.get("habilidades") or [])
            if str(item or "").strip()
        ]
        relacao = ":".join(dict.fromkeys(habilidades)) or fluxo
        descricao = (
            "costuma usar conteúdo copiado como entrada para criar arquivos de texto"
            if fluxo == "clipboard_para_arquivo"
            else f"considera útil a cooperação {relacao.replace(':', ' com ')}"
        )
        hipotese = self._registrar_evidencia(
            chave=f"cooperacao:{relacao}",
            tipo="relacao_habilidades",
            escopo="orquestracao_cooperativa",
            valor={"descricao_humana": descricao},
            sinal=sinal,
            origem="orquestracao_cooperativa",
            evidencia=(
                "composição confirmada e relida"
                if decisao_normalizada == "aceito"
                else f"composição encerrada como {decisao_normalizada}"
            ),
            confirmado_usuario=decisao_normalizada in {"aceito", "recusado"},
            contexto={"fluxo": fluxo},
        )
        return bool(hipotese)

    def registrar_continuidade(self, plano: dict[str, Any], evento: str) -> None:
        fluxo = str(
            (plano.get("metadados") or {}).get("fluxo") or "plano_cooperativo"
        ).strip()[:80]

        def atualizar(mental: dict[str, Any]) -> dict[str, Any]:
            return self._registrar_evento_continuidade(
                mental,
                evento=f"plano_{str(evento or 'atualizado')[:30]}",
                dominio="cooperacao",
                intent="COOPERATIVE_PLAN",
                habilidade="orquestracao_cooperativa",
                tipo=fluxo,
                alvo=str(plano.get("objetivo") or "")[:160],
                params={"modo": fluxo},
                status=str(plano.get("estado") or "")[:60],
                origem="orquestracao_cooperativa",
                ttl_s=900.0,
                ativa=False,
                reexecutavel=False,
            )

        self._estado_mental_atualizar(atualizar)

    def publicar_evento_agenda(
        self, operacao: str, *, alvo: str = "", confirmado: bool = False,
    ) -> dict[str, Any]:
        operacao_segura = str(operacao or "agenda_atualizada")[:64]
        confirmado_real = bool(confirmado)
        return self._quadro_getter().publicar_evento(
            origem="agenda",
            tipo=operacao_segura,
            resumo=(
                "agenda persistida e pronta para a central de notificações"
                if confirmado_real
                else "operação de agenda sem confirmação de persistência"
            ),
            confianca=1.0 if confirmado_real else 0.0,
            relevancia=0.75,
            sensibilidade="media",
            habilidades=("agenda", "central_notificacoes"),
            evidencias=(
                "persistencia_local_confirmada"
                if confirmado_real else "persistencia_local_nao_confirmada",
            ),
            chave_deduplicacao=(
                f"agenda:{operacao_segura}:{confirmado_real}:{str(alvo or '')[:48]}"
            ),
        )

    def detectar_visao_jogo(self, texto: str) -> dict[str, Any] | None:
        try:
            contexto = dict(self._contexto_jogo_getter() or {})
            contexto["analise_visual_recente"] = bool(
                self._visao_leitura_getter().tem_analise_recente()
            )
            return self._detectar_pedido_visao(texto, contexto)
        except Exception:
            return None


def criar_ponte_cooperacao_aplicacao_runtime(
    **kwargs: Any,
) -> PonteCooperacaoAplicacaoRuntime:
    return PonteCooperacaoAplicacaoRuntime(**kwargs)
