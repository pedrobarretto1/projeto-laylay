"""Runtime de aprendizado de rotina e musica.

O runtime organiza a manipulacao dos dados aprendidos sem possuir um cerebro
separado. O estado continua sendo fornecido pelo integrador principal por
getters e setters.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
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
        estado_getter: Callable[[], Dict[str, Any]] | None = None,
        estado_setter: Callable[..., None] | None = None,
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
        if not callable(self._estado_getter):
            return {}
        try:
            estado = self._estado_getter()
            return estado if isinstance(estado, dict) else {}
        except Exception:
            return {}

    def _set(self, **campos: Any) -> None:
        if not callable(self._estado_setter):
            self._log("⚠️ [APRENDIZADO] estado compartilhado indisponível; atualização ignorada")
            return
        combinado = {**self._estado(), **campos}
        self._estado_setter(
            **campos,
            proveniencia=self._proveniencia(),
            confianca=self._confianca(combinado),
        )

    def _proveniencia(self) -> Dict[str, str]:
        return {
            "rotina": self.arquivo_rotina,
            "rotina_feedback": self.arquivo_feedback_rotina,
            "musica_historico": self.arquivo_musica_historico,
            "musica_feedback": self.arquivo_musica_feedback,
            "estado_vivo": "mente_compartilhada",
        }

    @staticmethod
    def _confianca(estado: Dict[str, Any]) -> Dict[str, float]:
        def _pontuar(pesos: Any, observacoes: Any) -> float:
            valores = [
                abs(float(valor))
                for valor in dict(pesos or {}).values()
                if isinstance(valor, (int, float))
            ]
            forca = max(valores, default=0.0)
            volume = len(dict(observacoes or {}))
            return round(min(1.0, max(forca / 3.0, volume / 7.0)), 3)

        return {
            "rotina": _pontuar(
                estado.get("rotina_feedback_pesos"),
                estado.get("rotina_dados_diarios"),
            ),
            "musica": _pontuar(
                estado.get("musica_feedback_pesos"),
                estado.get("musica_dados_diarios"),
            ),
        }

    def snapshot(self) -> Dict[str, Any]:
        estado = self._estado()
        snapshot = {
            chave: dict(valor) if isinstance(valor, dict) else valor
            for chave, valor in estado.items()
        }
        snapshot["proveniencia"] = self._proveniencia()
        snapshot["confianca"] = self._confianca(estado)
        return snapshot

    def atualizar(self, **campos: Any) -> None:
        self._set(**campos)

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
            registrar_observacao_cb=ctx.get("registrar_observacao_aprendizado"),
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

    def musica_registrar_historico(self, musica: str) -> Dict[str, Any] | None:
        musica_limpa = str(musica or "").replace("- YouTube", "").strip()
        if len(musica_limpa) < 3:
            return None
        estado = self._estado()
        dados = dict(estado.get("musica_dados_diarios") or {})
        hora_atual = datetime.now().strftime("%H:00")
        bloco_atual = dict(dados.get(hora_atual) or {})
        historico_atual = list(bloco_atual.get("musicas") or [])
        ultima = str(historico_atual[-1] if historico_atual else "").strip()
        registrar_historico_musica(
            dados,
            musica_limpa,
        )
        self._set(musica_dados_diarios=dados)
        self.salvar_musica_dados()

        # O websocket pode repetir metadados do mesmo video. A repeticao ainda
        # conta para o aprendizado, mas nao abre outra oportunidade cognitiva.
        if ultima.casefold() == musica_limpa.casefold():
            return None
        considerar_presenca = self._ctx().get("considerar_presenca")
        if not callable(considerar_presenca):
            return None
        evento = {
            "natureza": "evento",
            "origem": "aprendizado_musical",
            "dominio": "musica",
            "categoria": "musica",
            "confianca": 0.90,
            "fundamentada": True,
            "momento_seguro": True,
            "motivo": f"A reproducao musical mudou para {musica_limpa}.",
            "evidencias": [
                musica_limpa,
                "reproducao_confirmada_pelo_navegador",
            ],
            "chave": f"musica:reproducao:{musica_limpa}",
            "timestamp": time.time(),
            "validade_s": 120.0,
            "acao_proposta": None,
            "utilidade": 38,
            "executavel": False,
            "reversivel": False,
            "executar_automaticamente": False,
            "autoridade_usuario": False,
            "permissao_execucao": False,
        }
        try:
            return dict(considerar_presenca(evento) or {})
        except Exception as erro:
            self._log(f"[APRENDIZADO MUSICAL] evento ignorado: {erro}")
            return None

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
    ) -> Dict[str, Any] | None:
        ctx = self._ctx()
        estado = self._estado()
        continuidades_get = ctx.get("continuidades_get")
        continuidades_set = ctx.get("continuidades_set")
        pendente = continuidades_get("rotina_sugestao_pendente") if callable(continuidades_get) else None
        candidato = analisar_e_sugerir_rotina(
            estado.get("rotina_dados_diarios", {}),
            estado.get("rotina_feedback_pesos", {}),
            float(estado.get("rotina_ultima_sugestao") or 0.0),
            pendente,
            ctx.get("contexto_aponta_descanso", lambda: False),
            dias_para_aprender,
            limite_rejeicao,
        )
        if not candidato:
            return None
        considerar_presenca = ctx.get("considerar_presenca")
        if not callable(considerar_presenca):
            self._log("[APRENDIZADO ROTINA] diretor de presenca indisponivel")
            return None

        app = str(candidato.get("app") or "").strip()
        hora = str(candidato.get("hora") or "").strip()
        agora = float(candidato.get("ts") or time.time())
        total = max(1, int(candidato.get("total_registros") or 1))
        ocorrencias = max(0, int(candidato.get("ocorrencias") or 0))

        def concluir(entregue: bool, _motivo: str) -> None:
            if not entregue:
                return
            self._set(rotina_ultima_sugestao=agora)
            if callable(continuidades_set):
                continuidades_set(
                    "rotina_sugestao_pendente",
                    {"app": app, "hora": hora, "ts": agora},
                )

        evento = {
            "natureza": "evento",
            "origem": "aprendizado_rotina",
            "dominio": "rotina",
            "categoria": "dica",
            "confianca": round(min(1.0, ocorrencias / total), 3),
            "fundamentada": True,
            "momento_seguro": True,
            "motivo": (
                f"O uso de {candidato.get('nome_amigavel') or app} se repetiu "
                f"no horario {hora}; ha uma oportunidade de oferecer o app."
            ),
            "evidencias": [
                f"janela_recorrente:{app}",
                f"frequencia_horaria:{ocorrencias}/{total}",
            ],
            "chave": f"rotina:app:{hora}:{app}",
            "timestamp": agora,
            "validade_s": 300.0,
            "acao_proposta": {
                "intent": "OPEN_APP",
                "params": {"app": app},
            },
            # Rotina observada pode sugerir um alvo, nunca executa-lo sem a
            # confirmacao que so passa a existir depois da entrega da oferta.
            "utilidade": 52,
            "executavel": False,
            "reversivel": True,
            "autoridade_usuario": False,
            "permissao_execucao": False,
            "ao_concluir": concluir,
        }
        try:
            return dict(considerar_presenca(evento) or {})
        except Exception as erro:
            self._log(f"[APRENDIZADO ROTINA] evento ignorado: {erro}")
            return None

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

    def monitorar(
        self,
        *,
        dias_para_aprender: int,
        limite_rejeicao: int,
        analisar_musica_cb: Callable[[], Any] | None = None,
        intervalo_s: float = 60.0,
        sleep_fn: Callable[[float], Any] = time.sleep,
        deve_parar: Callable[[], bool] | None = None,
        aguardar_fn: Callable[[float], bool] | None = None,
    ) -> None:
        self._log("[ROTINA] Aprendizado de rotina iniciado - vai aprender em 7 dias")
        self.carregar_tudo()

        while not (callable(deve_parar) and deve_parar()):
            try:
                self.monitor_tick(
                    dias_para_aprender=dias_para_aprender,
                    limite_rejeicao=limite_rejeicao,
                    analisar_musica_cb=analisar_musica_cb,
                )
            except Exception as erro:
                self._log(f"[ROTINA] Erro no daemon: {erro}")
            espera = max(0.0, float(intervalo_s))
            if callable(aguardar_fn):
                if aguardar_fn(espera):
                    break
            else:
                sleep_fn(espera)


def criar_aprendizado_runtime(
    *,
    pasta_memoria: str,
    arquivo_rotina: str,
    arquivo_musica_historico: str,
    arquivo_musica_feedback: str,
    contexto_getter: Callable[[], Dict[str, Any]],
    estado_getter: Callable[[], Dict[str, Any]] | None = None,
    estado_setter: Callable[..., None] | None = None,
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
