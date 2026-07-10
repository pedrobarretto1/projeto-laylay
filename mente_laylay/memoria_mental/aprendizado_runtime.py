"""Runtime de aprendizado de rotina e musica.

O runtime organiza a manipulacao dos dados aprendidos sem possuir um cerebro
separado. O estado continua sendo fornecido pelo integrador principal por
getters e setters.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict

from mente_laylay.memoria_mental.aprendizado_rotina_musica import (
    analisar_e_sugerir_rotina,
    carregar_feedback_pesos,
    carregar_musica_dados,
    carregar_musica_feedback_pesos,
    carregar_rotinas_aprendidas,
    logar_atividade_atual,
    musica_bloqueada,
    musica_chave_feedback,
    registrar_feedback_rotina,
    registrar_historico_musica,
    rotina_app_bloqueado,
    rotina_chave_feedback,
    salvar_feedback_pesos,
    salvar_musica_dados,
    salvar_musica_feedback_pesos,
    salvar_rotinas_aprendidas,
)


class AprendizadoRuntime:
    def __init__(
        self,
        *,
        pasta_memoria: str,
        arquivo_rotina: str,
        arquivo_musica_historico: str,
        arquivo_musica_feedback: str,
        contexto_getter: Callable[[], Dict[str, Any]],
        estado_getter: Callable[[], Dict[str, Any]],
        estado_setter: Callable[..., None],
        log: Callable[..., Any] = print,
    ) -> None:
        self.pasta_memoria = pasta_memoria
        self.arquivo_rotina = arquivo_rotina
        self.arquivo_musica_historico = arquivo_musica_historico
        self.arquivo_musica_feedback = arquivo_musica_feedback
        self._contexto_getter = contexto_getter
        self._estado_getter = estado_getter
        self._estado_setter = estado_setter
        self._log = log

    def _ctx(self) -> Dict[str, Any]:
        try:
            ctx = self._contexto_getter() if callable(self._contexto_getter) else {}
            return ctx if isinstance(ctx, dict) else {}
        except Exception:
            return {}

    def _estado(self) -> Dict[str, Any]:
        try:
            estado = self._estado_getter() if callable(self._estado_getter) else {}
            return estado if isinstance(estado, dict) else {}
        except Exception:
            return {}

    def _set(self, **campos: Any) -> None:
        if callable(self._estado_setter):
            self._estado_setter(**campos)

    @property
    def arquivo_feedback_rotina(self) -> str:
        return os.path.join(self.pasta_memoria, "rotinas_feedback.json")

    def carregar_rotinas_aprendidas(self) -> Dict[str, Any]:
        dados = carregar_rotinas_aprendidas(self.arquivo_rotina)
        self._set(rotina_dados_diarios=dados)
        self._log(f"📚 [ROTINA] {len(dados)} horários já aprendidos")
        return dados

    def salvar_rotinas_aprendidas(self) -> None:
        salvar_rotinas_aprendidas(self.arquivo_rotina, self._estado().get("rotina_dados_diarios", {}))
        self._log("💾 [ROTINA] Padrões salvos")

    def logar_atividade_atual(self) -> None:
        ctx = self._ctx()
        estado = self._estado()
        novo_log = logar_atividade_atual(
            self.arquivo_rotina,
            estado.get("rotina_dados_diarios", {}),
            float(estado.get("rotina_ultimo_log") or 0.0),
            ctx.get("contexto_sistema", {}),
            ctx.get("obter_janela_ativa", lambda: None),
            salvar_cb=self.salvar_rotinas_aprendidas,
        )
        self._set(rotina_ultimo_log=novo_log)

    def rotina_chave_feedback(self, hora: str, app: str) -> str:
        return rotina_chave_feedback(hora, app)

    def rotina_app_bloqueado(self, hora: str, app: str, limite_rejeicao: int) -> bool:
        return rotina_app_bloqueado(
            self._estado().get("rotina_feedback_pesos", {}),
            hora,
            app,
            limite_rejeicao,
        )

    def registrar_feedback_rotina(self, aceito: bool, *, cooldown_min: int, limite_rejeicao: int) -> None:
        ctx = self._ctx()
        estado = self._estado()
        continuidades_get = ctx.get("continuidades_get")
        continuidades_set = ctx.get("continuidades_set")
        pendente = continuidades_get("rotina_sugestao_pendente") if callable(continuidades_get) else None
        pesos, pendente_novo, ultima = registrar_feedback_rotina(
            pendente,
            estado.get("rotina_feedback_pesos", {}),
            aceito,
            falar_cb=ctx.get("falar_com_lipsync"),
            abrir_programa_cb=ctx.get("abrir_programa"),
            salvar_cb=lambda novos_pesos: salvar_feedback_pesos(self.arquivo_feedback_rotina, novos_pesos),
            cooldown_min=cooldown_min,
            limite_rejeicao=limite_rejeicao,
        )
        self._set(rotina_feedback_pesos=pesos, rotina_ultima_sugestao=ultima)
        if callable(continuidades_set):
            continuidades_set("rotina_sugestao_pendente", pendente_novo)

    def carregar_feedback_pesos(self) -> Dict[str, int]:
        pesos = carregar_feedback_pesos(self.arquivo_feedback_rotina)
        self._set(rotina_feedback_pesos=pesos)
        self._log(f"[FEEDBACK ROTINA] {len(pesos)} peso(s) carregado(s)")
        return pesos

    def carregar_musica_dados(self) -> Dict[str, Any]:
        dados = carregar_musica_dados(self.arquivo_musica_historico)
        self._set(musica_dados_diarios=dados)
        return dados

    def salvar_musica_dados(self) -> None:
        salvar_musica_dados(self.arquivo_musica_historico, self._estado().get("musica_dados_diarios", {}))

    def carregar_musica_feedback_pesos(self) -> Dict[str, int]:
        pesos = carregar_musica_feedback_pesos(self.arquivo_musica_feedback)
        self._set(musica_feedback_pesos=pesos)
        return pesos

    def salvar_musica_feedback_pesos(self) -> None:
        salvar_musica_feedback_pesos(self.arquivo_musica_feedback, self._estado().get("musica_feedback_pesos", {}))

    def musica_chave_feedback(self, hora: str, musica: str) -> str:
        return musica_chave_feedback(hora, musica)

    def musica_bloqueada(self, hora: str, musica: str, limite_rejeicao: int) -> bool:
        return musica_bloqueada(
            self._estado().get("musica_feedback_pesos", {}),
            hora,
            musica,
            limite_rejeicao,
        )

    def musica_registrar_historico(self, musica: str) -> None:
        registrar_historico_musica(
            self._estado().get("musica_dados_diarios", {}),
            musica,
            salvar_cb=self.salvar_musica_dados,
        )

    def carregar_tudo(self) -> None:
        self.carregar_rotinas_aprendidas()
        self.carregar_feedback_pesos()
        self.carregar_musica_dados()
        self.carregar_musica_feedback_pesos()

    def analisar_e_sugerir_rotina(
        self,
        *,
        dias_para_aprender: int,
        limite_rejeicao: int,
    ) -> None:
        ctx = self._ctx()
        estado = self._estado()
        continuidades_get = ctx.get("continuidades_get")
        continuidades_set = ctx.get("continuidades_set")
        pendente = continuidades_get("rotina_sugestao_pendente") if callable(continuidades_get) else None
        ultima, pendente_novo = analisar_e_sugerir_rotina(
            estado.get("rotina_dados_diarios", {}),
            estado.get("rotina_feedback_pesos", {}),
            float(estado.get("rotina_ultima_sugestao") or 0.0),
            pendente,
            ctx.get("contexto_aponta_descanso", lambda: False),
            ctx.get("agendar_fala_proativa", lambda *args, **kwargs: None),
            dias_para_aprender,
            limite_rejeicao,
        )
        self._set(rotina_ultima_sugestao=ultima)
        if callable(continuidades_set):
            continuidades_set("rotina_sugestao_pendente", pendente_novo)

    def monitor_tick(
        self,
        *,
        dias_para_aprender: int,
        limite_rejeicao: int,
        analisar_musica_cb: Callable[[], Any] | None = None,
    ) -> None:
        self.logar_atividade_atual()
        self.analisar_e_sugerir_rotina(
            dias_para_aprender=dias_para_aprender,
            limite_rejeicao=limite_rejeicao,
        )
        if callable(analisar_musica_cb):
            analisar_musica_cb()


def criar_aprendizado_runtime(
    *,
    pasta_memoria: str,
    arquivo_rotina: str,
    arquivo_musica_historico: str,
    arquivo_musica_feedback: str,
    contexto_getter: Callable[[], Dict[str, Any]],
    estado_getter: Callable[[], Dict[str, Any]],
    estado_setter: Callable[..., None],
    log: Callable[..., Any] = print,
) -> AprendizadoRuntime:
    return AprendizadoRuntime(
        pasta_memoria=pasta_memoria,
        arquivo_rotina=arquivo_rotina,
        arquivo_musica_historico=arquivo_musica_historico,
        arquivo_musica_feedback=arquivo_musica_feedback,
        contexto_getter=contexto_getter,
        estado_getter=estado_getter,
        estado_setter=estado_setter,
        log=log,
    )
