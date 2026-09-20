"""Composição filtrada das operações que acompanham um turno da conversa."""

from __future__ import annotations

from typing import Any, Mapping

from mente_laylay.cognicao.orquestrador_turno_runtime import (
    atualizar_planejamento_turno,
    concluir_planejamento_evento,
    iniciar_planejamento_turno,
    registrar_leitura_semantica_principal,
    registrar_falha_opcional,
    verificar_fala_do_turno,
)


DEPENDENCIAS_ORQUESTRACAO_TURNO = (
    "APPS_MAP",
    "_abrir_correcao_interpretacao_mente",
    "_analisar_funcao_comunicativa_mente",
    "_analisar_identidade_turno_mente",
    "_atualizar_assunto_estruturado_mente",
    "_atualizar_plano_turno_mente",
    "_atualizar_registro_turno_mente",
    "_classificar_encerramento_assunto_mente",
    "_classificar_modalidade_turno_mente",
    "_coleta_entradas_neurais",
    "_construir_parecer_especialistas_mente",
    "_construir_retrato_turno_mente",
    "_contexto_horario_atual",
    "_estado_compartilhado_runtime",
    "_especialista_neural_comandos_runtime",
    "_evidencia_habilidades_turno_mente",
    "_extrair_correcao_duravel_mente",
    "_extrair_tema_fundamentacao_mente",
    "_interpretador_semantico_runtime",
    "_limpar_pergunta_aberta_estado_mente",
    "_modo_jogo_runtime",
    "_montar_fundamentacao_mente",
    "_normalizar_texto_com_apelidos",
    "_obter_contexto_perceptivo",
    "_observabilidade_mente_runtime",
    "_orquestrador_cooperativo_runtime",
    "_pendencia_ativa_turno_mente",
    "_persistir_correcao_duravel_mente",
    "_pesquisa_contextual_runtime",
    "_planejar_turno_mente",
    "_registrar_etapa_turno_mente",
    "_resolver_repeticao_ultima_acao",
    "_resumo_identidade_turno_mente",
    "_saude_mente_runtime",
    "_texto_tem_comando_explicito",
    "_verificar_fala_turno_mente",
    "_registro_visao_jogo_leitura_runtime",
    "MEMORIA_SQLITE",
    "playlist_state",
    "print",
    "time",
)


class ComposicaoTurnoRuntime:
    """Expõe o ciclo do turno sobre um registro estável e auditável."""

    def __init__(self, *, servicos: Mapping[str, Any]) -> None:
        self._servicos = {
            nome: servicos[nome]
            for nome in DEPENDENCIAS_ORQUESTRACAO_TURNO
            if nome in servicos
        }

    def _snapshot(self) -> dict[str, Any]:
        return dict(self._servicos)

    def iniciar(
        self,
        entrada: str | Mapping[str, Any],
        *,
        origem: str = "desconhecida",
    ) -> dict:
        coletor = self._servicos.get("_coleta_entradas_neurais")
        captura = None
        if coletor is not None:
            try:
                captura = coletor.preparar(entrada, origem)
            except Exception as erro:
                self._falha_coleta(erro)
        turno, falha = None, None
        try:
            turno = iniciar_planejamento_turno(self._snapshot, entrada, origem=origem)
            return turno
        except Exception as erro:
            falha = type(erro).__name__
            raise
        finally:
            if coletor is not None and captura is not None:
                try:
                    coletor.registrar(captura, turno, erro=falha)
                except Exception as erro:
                    self._falha_coleta(erro)

    def _falha_coleta(self, erro: Exception) -> None:
        registrar_falha_opcional(self._snapshot(), "neural_coleta", "falha_coleta_entrada", erro,
            classe="observabilidade", impacto="amostra_nao_persistida", fallback="preservar_turno")
        if self._servicos.get("_observabilidade_mente_runtime") is None:
            try:
                logger = self._servicos.get("print")
                if callable(logger):
                    logger(f"⚠️ [NEURAL:COLETA] amostra não persistida | tipo={type(erro).__name__}")
            except Exception:
                pass

    def atualizar(
        self, fase: str, *, comandos=(), erros=(), fala: str = "",
    ) -> dict:
        return atualizar_planejamento_turno(
            self._snapshot, fase, comandos=comandos, erros=erros, fala=fala,
        )

    def concluir_evento(
        self,
        turno: Mapping[str, Any],
        *,
        resultado: str,
    ) -> dict:
        return concluir_planejamento_evento(
            self._snapshot,
            turno,
            resultado=resultado,
        )

    def verificar_fala(self, fala: str, *, origem: str = "conversa") -> dict:
        return verificar_fala_do_turno(self._snapshot, fala, origem=origem)

    def registrar_leitura_semantica(
        self, texto: str, leitura: dict | None,
    ) -> dict:
        return registrar_leitura_semantica_principal(
            self._snapshot, texto, leitura,
        )

    @property
    def servicos_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))


def criar_composicao_turno_runtime(**kwargs: Any) -> ComposicaoTurnoRuntime:
    return ComposicaoTurnoRuntime(**kwargs)
