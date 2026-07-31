"""Execução confirmada e reversível das iniciativas já autorizadas."""

from __future__ import annotations

from typing import Any, Callable, Mapping


class ExecutorAcoesAutonomasRuntime:
    """Executa apenas integrações previamente filtradas pelo motor de iniciativa."""

    def __init__(
        self,
        *,
        executar_iot: Callable[[dict, str], Mapping[str, Any]],
        estado_mental_getter: Callable[[], Mapping[str, Any]],
        obter_volume: Callable[[], int | None],
        ajustar_volume: Callable[[int], bool],
        falar: Callable[[str, str, int], Any],
        executar_intencao: Callable[[dict[str, Any], str], bool] | None = None,
        controlar_midia: Callable[[str], bool] | None = None,
    ) -> None:
        self.executar_iot = executar_iot
        self.estado_mental_getter = estado_mental_getter
        self.obter_volume = obter_volume
        self.ajustar_volume = ajustar_volume
        self.falar = falar
        self.executar_intencao = executar_intencao
        self.controlar_midia = controlar_midia

    @staticmethod
    def _dados(acao: Any) -> tuple[str, dict[str, Any]]:
        if not isinstance(acao, Mapping):
            return "", {}
        intent = str(acao.get("intent") or "").strip().upper()
        params_brutos = acao.get("params")
        params = dict(params_brutos) if isinstance(params_brutos, Mapping) else {}
        return intent, params

    def executar(self, acao: Mapping[str, Any]) -> dict[str, Any]:
        intent, params = self._dados(acao)
        if intent == "IOT_CONTROL":
            return self._executar_iot(params)
        if intent == "VOLUME":
            return self._executar_volume(params)
        if intent == "VOLUME_RELATIVE":
            return self._executar_volume_relativo(params)
        if intent == "MEDIA_CONTROL":
            return self._executar_midia(params)
        if intent == "MUSIC_SEARCH":
            return self._executar_busca_musical(params)
        return {"ok": False, "confirmado": False, "status": "intent_nao_elegivel"}

    def _executar_iot(self, params: dict[str, Any]) -> dict[str, Any]:
        alvo = str(params.get("alvo") or "").strip()
        acao_iot = str(params.get("acao") or "").strip().lower()
        estado_mental = dict(self.estado_mental_getter() or {})
        por_dispositivo = dict(
            estado_mental.get("parametros_iot_por_dispositivo") or {}
        )
        parametros_anteriores = dict(por_dispositivo.get(alvo) or {})
        resultado = dict(self.executar_iot(
            {"intent": "IOT_CONTROL", "params": params},
            "ação autônoma autorizada pelo usuário",
        ) or {})
        ok = bool(resultado.get("ok")) and bool(resultado.get("confirmado"))
        desfazer: dict[str, Any] = {}
        if ok and acao_iot == "ligar" and resultado.get("estado_anterior") is False:
            desfazer = {
                "intent": "IOT_CONTROL",
                "params": {"acao": "desligar", "alvo": alvo},
            }
        elif ok and acao_iot == "desligar" and resultado.get("estado_anterior") is True:
            desfazer = {
                "intent": "IOT_CONTROL",
                "params": {"acao": "ligar", "alvo": alvo},
            }
        elif ok and acao_iot == "ajustar_brilho":
            brilho_anterior = parametros_anteriores.get("brilho")
            if isinstance(brilho_anterior, (int, float)):
                desfazer = {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_brilho",
                        "alvo": alvo,
                        "valor": int(brilho_anterior),
                    },
                }
        elif ok and acao_iot == "ajustar_cor":
            rgb_anterior = parametros_anteriores.get("rgb")
            cor_anterior = str(parametros_anteriores.get("cor") or "").strip()
            if isinstance(rgb_anterior, (tuple, list)) and len(rgb_anterior) == 3:
                desfazer = {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_cor", "alvo": alvo,
                        "cor": cor_anterior or "cor anterior",
                        "rgb": tuple(int(item) for item in rgb_anterior),
                    },
                }
            elif any(
                chave in parametros_anteriores for chave in ("temperatura", "brilho")
            ):
                desfazer = {
                    "intent": "IOT_CONTROL",
                    "params": {
                        "acao": "ajustar_branco", "alvo": alvo,
                        "temperatura": int(parametros_anteriores.get("temperatura", 50)),
                        "brilho": int(parametros_anteriores.get("brilho", 70)),
                    },
                }
        plano = dict(resultado.get("plano_resposta") or {})
        fala = str(plano.get("fala") or "").strip()
        if fala:
            self.falar(
                f"Tomei a iniciativa com a permissão que você me deu. {fala}",
                str(plano.get("emocao") or "calma"),
                int(plano.get("nivel") or 1),
            )
        return {
            "ok": ok,
            "confirmado": bool(resultado.get("confirmado")),
            "status": str(resultado.get("status") or ""),
            "desfazer": desfazer,
        }

    def _executar_volume(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            nivel_novo = int(params.get("nivel_volume"))
        except (TypeError, ValueError):
            return {
                "ok": False,
                "confirmado": False,
                "status": "volume_invalido",
                "desfazer": {},
            }
        nivel_anterior = self.obter_volume()
        executou = bool(self.ajustar_volume(nivel_novo))
        nivel_confirmado = self.obter_volume() if executou else None
        confirmado = (
            nivel_confirmado is not None
            and abs(nivel_confirmado - nivel_novo) <= 1
        )
        if confirmado:
            self.falar(
                "Tomei a iniciativa com a sua permissão e deixei o volume "
                f"em {nivel_novo} por cento.",
                "calma",
                1,
            )
        return {
            "ok": bool(executou and confirmado),
            "confirmado": confirmado,
            "status": "volume_ajustado" if confirmado else "falha_confirmacao_volume",
            "desfazer": (
                {"intent": "VOLUME", "params": {"nivel_volume": nivel_anterior}}
                if confirmado
                and nivel_anterior is not None
                and nivel_anterior != nivel_novo
                else {}
            ),
        }

    def _executar_volume_relativo(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            delta = int(params.get("delta"))
        except (TypeError, ValueError):
            return {
                "ok": False, "confirmado": False,
                "status": "volume_relativo_invalido", "desfazer": {},
            }
        nivel_anterior = self.obter_volume()
        if nivel_anterior is None:
            return {
                "ok": False, "confirmado": False,
                "status": "volume_atual_indisponivel", "desfazer": {},
            }
        # Evita tanto silêncio acidental quanto volume excessivo por inferência.
        nivel_novo = max(5, min(80, int(nivel_anterior) + delta))
        if nivel_novo == nivel_anterior:
            return {
                "ok": True, "confirmado": True,
                "status": "volume_ja_no_limite", "desfazer": {},
            }
        return self._executar_volume({"nivel_volume": nivel_novo})

    def _executar_midia(self, params: dict[str, Any]) -> dict[str, Any]:
        acao = str(params.get("acao") or "").strip().lower()
        inversa = {"pause": "play", "play": "pause", "next": "prev", "prev": "next"}.get(acao)
        if not inversa or not callable(self.controlar_midia):
            return {
                "ok": False, "confirmado": False,
                "status": "controle_midia_indisponivel", "desfazer": {},
            }
        confirmado = bool(self.controlar_midia(acao))
        if confirmado:
            falas = {
                "pause": "Percebi que ela estava atrapalhando e pausei pra você.",
                "play": "A música tinha parado, então coloquei de volta.",
                "next": "Essa não casou com o momento. Passei para a próxima.",
                "prev": "Voltei uma faixa pra você.",
            }
            self.falar(falas[acao], "calma", 1)
        return {
            "ok": confirmado,
            "confirmado": confirmado,
            "status": f"midia_{acao}" if confirmado else "falha_confirmacao_midia",
            "desfazer": (
                {"intent": "MEDIA_CONTROL", "params": {"acao": inversa}}
                if confirmado else {}
            ),
        }

    def _executar_busca_musical(self, params: dict[str, Any]) -> dict[str, Any]:
        query = str(params.get("query") or "").strip()
        if not query or not callable(self.executar_intencao):
            return {
                "ok": False, "confirmado": False,
                "status": "busca_musical_indisponivel", "desfazer": {},
            }
        comando = {
            "intent": "MUSIC_SEARCH",
            "params": {"query": query, "origem": "autonomia"},
        }
        executou = bool(self.executar_intencao(comando, f"toca {query}"))
        return {
            "ok": executou,
            "confirmado": executou,
            "status": "musica_aberta" if executou else "falha_busca_musical",
            "desfazer": (
                {"intent": "MEDIA_CONTROL", "params": {"acao": "pause"}}
                if executou else {}
            ),
        }

    def desfazer(self, acao: Mapping[str, Any]) -> dict[str, Any]:
        intent, params = self._dados(acao)
        if intent == "IOT_CONTROL":
            params.update(origem="autonomia", confirmado=True)
            resultado = dict(self.executar_iot(
                {"intent": intent, "params": params},
                "desfazer ação autônoma",
            ) or {})
            return {
                "ok": bool(resultado.get("ok")),
                "confirmado": bool(resultado.get("confirmado")),
                "status": str(resultado.get("status") or ""),
            }
        if intent == "VOLUME":
            try:
                nivel = int(params.get("nivel_volume"))
            except (TypeError, ValueError):
                return {"ok": False, "confirmado": False, "status": "token_invalido"}
            executou = bool(self.ajustar_volume(nivel))
            atual = self.obter_volume() if executou else None
            confirmado = atual is not None and abs(atual - nivel) <= 1
            return {
                "ok": bool(executou and confirmado),
                "confirmado": confirmado,
                "status": (
                    "volume_restaurado" if confirmado
                    else "falha_restauracao_volume"
                ),
            }
        if intent == "MEDIA_CONTROL":
            acao = str(params.get("acao") or "").strip().lower()
            if acao not in {"pause", "play", "next", "prev"} or not callable(self.controlar_midia):
                return {"ok": False, "confirmado": False, "status": "token_invalido"}
            confirmado = bool(self.controlar_midia(acao))
            return {
                "ok": confirmado,
                "confirmado": confirmado,
                "status": "midia_restaurada" if confirmado else "falha_restauracao_midia",
            }
        return {"ok": False, "confirmado": False, "status": "token_invalido"}


def criar_executor_acoes_autonomas_runtime(
    **kwargs: Any,
) -> ExecutorAcoesAutonomasRuntime:
    return ExecutorAcoesAutonomasRuntime(**kwargs)
