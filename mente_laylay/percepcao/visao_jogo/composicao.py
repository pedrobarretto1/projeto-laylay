"""Composição da visão de jogo, suas sessões e observadores proativos."""

from __future__ import annotations

import os
from typing import Any, Callable, Mapping

from mente_laylay.memoria_mental.memoria_jogos import MemoriaJogos
from mente_laylay.pesquisa_jogos import criar_pesquisa_jogos_runtime
from mente_laylay.percepcao.visao_jogo.observador_inventario import (
    criar_observador_inventario_jogo_runtime,
)
from mente_laylay.percepcao.visao_jogo.observador_presenca import (
    criar_observador_presenca_jogo_runtime,
)
from mente_laylay.percepcao.visao_jogo.runtime import criar_visao_jogo_runtime
from mente_laylay.percepcao.visao_jogo.sessao_jogo import (
    ContextoSessoesJogo,
    identificar_jogo,
)


_DESLIGADO = {"0", "false", "nao", "não", "off", "desligado"}


class ComposicaoVisaoJogoRuntime:
    """Monta a percepção visual sem duplicar estado de jogo na aplicação."""

    def __init__(
        self,
        *,
        db_path: str,
        registrar_falha: Callable[..., Any] | None = None,
        env_getter: Callable[[str, str], str] = os.getenv,
        memoria_factory: Callable[..., Any] = MemoriaJogos,
        pesquisa_factory: Callable[..., Any] = criar_pesquisa_jogos_runtime,
        visao_factory: Callable[..., Any] = criar_visao_jogo_runtime,
        observador_inventario_factory: Callable[..., Any] = criar_observador_inventario_jogo_runtime,
        observador_presenca_factory: Callable[..., Any] = criar_observador_presenca_jogo_runtime,
        sessoes_factory: Callable[..., Any] = ContextoSessoesJogo,
        identificar_jogo_fn: Callable[[Mapping[str, Any]], Mapping[str, Any]] = identificar_jogo,
        log: Callable[..., Any] = print,
    ) -> None:
        self.registrar_falha = registrar_falha
        self.env_getter = env_getter
        self.log = log
        self._visao_factory = visao_factory
        self._observador_inventario_factory = observador_inventario_factory
        self._observador_presenca_factory = observador_presenca_factory
        self._sessoes_factory = sessoes_factory
        self._identificar_jogo = identificar_jogo_fn
        self._visao = None
        self._observador_inventario = None
        self._observador_presenca = None

        self.memoria = memoria_factory(str(db_path))
        self.pesquisa = pesquisa_factory(
            db_path=str(db_path),
            registrar_falha=registrar_falha,
            log=log,
        )

    def _relatar(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("composicao_visao_jogo", codigo, erro=erro)

    def _habilitado(self, nome: str, padrao: bool = True) -> bool:
        bruto = self.env_getter(nome, "1" if padrao else "0")
        return str(bruto or "").strip().casefold() not in _DESLIGADO

    def _numero(self, nome: str, padrao: float, conversor: Callable[[str], Any]) -> Any:
        bruto = self.env_getter(nome, str(padrao))
        try:
            return conversor(str(bruto or padrao).strip())
        except (TypeError, ValueError) as erro:
            self.log(f"⚠️ [VISÃO:CONFIG] {nome} inválida; usando {padrao:g}.")
            self._relatar(f"configuracao_{nome.casefold()}", erro)
            return conversor(str(padrao))

    def conectar_visao(
        self,
        *,
        contexto_jogo: Callable[[], Mapping[str, Any]],
        analisar_imagem: Callable[[str, str], str],
        falar: Callable[..., Any],
        sintetizar_texto: Callable[..., Any],
        ao_mapear_inventario: Callable[..., Any],
        processar_sugestao_proativa: Callable[..., Any],
        registrar_analise: Callable[..., Any],
        credencial_disponivel: bool,
        permitido_presenca: Callable[[], bool],
        interacao_iniciada: Callable[[], bool],
        stop_event: Any,
        progresso_cooperativo: Callable[[Mapping[str, Any]], Any] | None = None,
    ) -> Any:
        if self._visao is not None:
            return self._visao

        self._visao = self._visao_factory(
            contexto_jogo=contexto_jogo,
            analisar_imagem=analisar_imagem,
            falar=falar,
            sessoes=self._sessoes_factory(memoria=self.memoria),
            memoria_jogos=self.memoria,
            pesquisar_item=self.pesquisa.pesquisar_item,
            sintetizar_texto=sintetizar_texto,
            ao_mapear_inventario=ao_mapear_inventario,
            processar_sugestao_proativa=processar_sugestao_proativa,
            registrar_analise_cb=registrar_analise,
            progresso_cooperativo_cb=progresso_cooperativo,
            habilitado=self._habilitado("LAYLAY_VISAO_JOGO"),
            credencial_disponivel=bool(credencial_disponivel),
            log=self.log,
        )
        chave_jogo = lambda contexto: str(
            self._identificar_jogo(contexto).get("chave") or ""
        )
        self._observador_inventario = self._observador_inventario_factory(
            contexto_jogo=contexto_jogo,
            capturar=self._visao.capturar,
            executar_visao=self._visao.executar,
            jogo_chave_atual=chave_jogo,
            visao_ocupada=lambda: self._visao.em_andamento,
            habilitado=self._habilitado("LAYLAY_JOGO_PROATIVO"),
            intervalo_s=self._numero("LAYLAY_JOGO_PROATIVO_INTERVALO", 25.0, float),
            duracao_s=self._numero("LAYLAY_JOGO_PROATIVO_DURACAO", 600.0, float),
            max_analises=self._numero("LAYLAY_JOGO_PROATIVO_MAX_ANALISES", 12, int),
            log=self.log,
            stop_event=stop_event,
        )
        self._observador_presenca = self._observador_presenca_factory(
            contexto_jogo=contexto_jogo,
            capturar=self._visao.capturar,
            executar_visao=self._visao.executar,
            jogo_chave_atual=chave_jogo,
            visao_ocupada=lambda: self._visao.em_andamento,
            permitido=permitido_presenca,
            interacao_iniciada=interacao_iniciada,
            habilitado=bool(credencial_disponivel)
            and self._habilitado("LAYLAY_PRESENCA_VISUAL_JOGO"),
            intervalo_s=self._numero("LAYLAY_PRESENCA_VISUAL_INTERVALO", 35.0, float),
            max_analises_sessao=self._numero("LAYLAY_PRESENCA_VISUAL_MAX", 8, int),
            janela_analises_s=self._numero(
                "LAYLAY_PRESENCA_VISUAL_JANELA", 900.0, float,
            ),
            log=self.log,
            stop_event=stop_event,
        )
        return self._visao

    @property
    def visao(self) -> Any:
        if self._visao is None:
            raise RuntimeError("visão de jogo ainda não conectada à mente")
        return self._visao

    @property
    def observador_inventario(self) -> Any:
        if self._observador_inventario is None:
            raise RuntimeError("observador de inventário ainda não conectado")
        return self._observador_inventario

    @property
    def observador_presenca(self) -> Any:
        if self._observador_presenca is None:
            raise RuntimeError("observador de presença ainda não conectado")
        return self._observador_presenca


def criar_composicao_visao_jogo_runtime(**kwargs: Any) -> ComposicaoVisaoJogoRuntime:
    return ComposicaoVisaoJogoRuntime(**kwargs)
