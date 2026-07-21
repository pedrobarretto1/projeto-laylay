"""Persistência, interpretação e execução de preferências de sugestões."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Callable, Mapping


class PreferenciasSugestoesRuntime:
    def __init__(self, namespace_getter: Callable[[], Mapping[str, Any]]) -> None:
        self._namespace_getter = namespace_getter

    def _ns(self) -> Mapping[str, Any]:
        return self._namespace_getter()

    def obter(self, comando: str, payload: dict | None = None):
        ns = self._ns()
        chave = ns["_chave_preferencia_sugestao_mente"](comando, payload)
        try:
            motor = ns.get("_motor_aprendizado_runtime")
            if motor is not None:
                selecionada = motor.selecionar_preferencia_sugestao(chave)
                if isinstance(selecionada, dict):
                    return selecionada
            bruto = ns["MEMORIA_SQLITE"].carregar_preferencias().get(f"sugestao_contextual:{chave}")
            dados = json.loads(bruto) if bruto else None
            if not isinstance(dados, dict):
                return None
            aprendizado = dados.get("_aprendizado") if isinstance(dados.get("_aprendizado"), dict) else {}
            hipotese_chave = str(aprendizado.get("hipotese_chave") or "").strip()
            # Registros anteriores à maturidade continuam válidos para não
            # apagar preferências que Pedro já ensinou.
            if not hipotese_chave:
                return dados
            if motor is None:
                return dados
            avaliacao = motor.avaliar_hipotese(hipotese_chave)
            if avaliacao.get("aplicavel"):
                dados["_maturidade_atual"] = avaliacao
                return dados
            ns["print"](
                "🧠 [PREFERÊNCIA] não aplicada neste contexto | "
                f"chave={chave} | nivel={avaliacao.get('nivel')} | "
                f"motivos={avaliacao.get('motivos') or []}"
            )
            return None
        except Exception as erro:
            ns["print"](f"⚠️ [PREFERÊNCIA] não consegui recuperar sugestão {chave}: {erro}")
            return None

    def registrar(self, chave: str, registro: dict):
        ns = self._ns()
        dados = dict(registro or {})
        chave = str(chave or "").strip()
        if not chave or not isinstance(dados.get("alternativa"), dict):
            return False
        try:
            memoria = ns["MEMORIA_SQLITE"]
            motor = ns.get("_motor_aprendizado_runtime")
            hipotese_chave = f"preferencia_sugestao:{chave}"
            hipotese = motor.registrar_contraproposta(chave, dados) if motor is not None else None
            if isinstance(hipotese, dict) and hipotese.get("conflito"):
                ns["print"](
                    "🧠 [PREFERÊNCIA] conflito confiável aguardando confirmação | "
                    f"contexto={chave} | existente={hipotese.get('chave_existente')}"
                )
                return hipotese
            hipotese_chave = str((hipotese or {}).get("chave") or hipotese_chave)
            avaliacao = (
                motor.avaliar_hipotese(hipotese_chave)
                if motor is not None else {
                    "nivel": "legado_confirmado", "aplicavel": True,
                    "confianca_efetiva": 0.9,
                }
            )
            dados["_aprendizado"] = {
                "hipotese_chave": hipotese_chave,
                "nivel_inicial": str(avaliacao.get("nivel") or "hipotese"),
                "confianca_inicial": float(avaliacao.get("confianca_efetiva") or 0.0),
                "aplicavel_inicialmente": bool(avaliacao.get("aplicavel")),
                "contexto": dict(avaliacao.get("contexto_evidencia") or {}),
                "status_hipotese": str((hipotese or {}).get("status") or ""),
                "registrado_em": time.time(),
            }
            memoria.salvar_preferencia(
                f"sugestao_contextual:{chave}", json.dumps(dados, ensure_ascii=False),
            )
            descricao = str(dados.get("descricao") or "alternativa escolhida").strip()
            evidencia = str(dados.get("evidencia") or "").strip()
            preferencia_global = bool(avaliacao.get("global"))
            contexto_preferencia = dict(avaliacao.get("contexto_evidencia") or {})
            escopo_humano = "global" if preferencia_global else ", ".join(
                f"{campo}={contexto_preferencia.get(campo)}"
                for campo in ("periodo", "atividade", "aplicativo")
                if contexto_preferencia.get(campo)
            ) or "contexto em que foi ensinada"
            memoria.salvar_aprendizado_semantico(
                tipo="preferencia", gatilho=f"sugestão contextual {chave}",
                valor=descricao,
                regra=(
                    f"No escopo {escopo_humano}, Pedro prefere {descricao} em vez da proposta anterior."
                ),
                texto_original=evidencia,
                confianca=max(0.5, float(avaliacao.get("confianca_efetiva") or 0.0)),
                origem="contraproposta_usuario", evidencia=evidencia,
                # Preferências condicionais vivem no motor contextual. Só uma
                # declaração realmente global pode entrar no prompt genérico.
                status="ativo" if preferencia_global and avaliacao.get("aplicavel") else "nao_verificado",
                confirmado_usuario=bool(
                    preferencia_global and str(avaliacao.get("nivel") or "") == "confirmada"
                ),
            )
            ns["salvar_memoria"]()
            ns["print"](
                "🧠 [PREFERÊNCIA] contraproposta registrada | "
                f"contexto={chave} | alternativa={descricao} | "
                f"nivel={avaliacao.get('nivel')}"
            )
            return {
                "salvo": True,
                "hipotese_chave": hipotese_chave,
                "avaliacao": avaliacao,
            }
        except Exception as erro:
            ns["print"](f"⚠️ [PREFERÊNCIA] não consegui salvar contraproposta: {erro}")
            return False

    def preparar(self, comando: str, payload: dict, fala: str):
        return self._ns()["_aplicar_preferencia_sugestao_mente"](
            comando, payload, fala, self.obter,
        )

    def interpretar_contraproposta(self, texto: str, comando: str, payload: dict):
        ns = self._ns()
        dados = dict(payload or {})
        interna = dados.get("intent") if isinstance(dados.get("intent"), dict) else {}
        params = interna.get("params") if isinstance(interna.get("params"), dict) else dados
        alvo = str(params.get("alvo") or dados.get("alvo") or "").strip()
        texto_operacional = str(texto or "").strip()
        alvo_fala = {
            "lampada_quarto": "lâmpada do quarto",
            "tomada_ventilador": "ventilador",
        }.get(alvo, alvo.replace("_", " "))
        if alvo_fala and any(palavra in texto_operacional.casefold() for palavra in (
            "brilho", "luz", "cor", "liga", "desliga", "acende", "apaga",
        )):
            texto_operacional = re.sub(
                r"\b(?:dela|dele|nela|nele)\b", f"da {alvo_fala}",
                texto_operacional, flags=re.IGNORECASE,
            )
            if alvo_fala.casefold() not in texto_operacional.casefold():
                texto_operacional += f" na {alvo_fala}"
        detectores = [
            ns[nome] for nome in
            ("_detectar_intencao_iot", "detectar_intencao_deterministica", "analisar_intencao")
            if nome in ns
        ]
        for detectar in detectores:
            try:
                resultado = detectar(texto_operacional)
            except Exception:
                continue
            if not isinstance(resultado, dict):
                continue
            if str(resultado.get("intent") or "").upper() == "SUGGEST_ACTION":
                params_resultado = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
                resultado = (
                    params_resultado.get("acao_sugerida")
                    if isinstance(params_resultado.get("acao_sugerida"), dict) else {}
                )
            intent = str(resultado.get("intent") or "").strip().upper()
            if intent and intent not in {"SUGGEST_ACTION", "CANCELAR_ACAO"}:
                return resultado
        return None

    def executar_temporal(
        self, comando: str, payload: dict, texto_confirmacao: str = "",
    ) -> bool:
        ns = self._ns()
        comando = str(comando or "").strip().upper()
        dados = dict(payload or {})
        alvo = str(dados.get("alvo") or "lampada_quarto")
        acao_luz = "ligar" if comando == "TIME_LIGHT_ON" else "desligar"
        resultado_luz = ns["_executar_intencao_iot"](
            {"intent": "IOT_CONTROL", "params": {
                "acao": acao_luz, "alvo": alvo,
                "origem": "usuario", "confirmado": True,
            }},
            texto_confirmacao,
        )
        luz_ok = bool(resultado_luz.get("ok")) if isinstance(resultado_luz, dict) else False
        if comando == "TIME_LIGHT_ON":
            plano = resultado_luz.get("plano_resposta") if isinstance(resultado_luz, dict) else None
            fala = str((plano or {}).get("fala") or "") if isinstance(plano, dict) else ""
            ns["falar_com_lipsync"](
                fala or (
                    "Liguei a luz do quarto. A noite ficou menos cavernosa."
                    if luz_ok else
                    "Tentei ligar a luz do quarto, mas ela não confirmou a mudança."
                ), "calma", 1,
            )
            return luz_ok
        if comando != "TIME_WIND_DOWN":
            return False
        volume = max(0, min(100, int(dados.get("volume") or 25)))
        volume_ok = bool(ns["ajustar_volume_sistema"](volume))
        if luz_ok and volume_ok:
            fala = f"Pronto. Apaguei a luz e deixei o volume em {volume} por cento. Agora o PC entrou no ritmo da madrugada."
        elif luz_ok:
            fala = "Apaguei a luz, mas o volume não confirmou o ajuste. A parte silenciosa se rebelou um pouco."
        elif volume_ok:
            fala = f"Deixei o volume em {volume} por cento, mas a luz não respondeu agora."
        else:
            fala = "Tentei deixar tudo mais quieto, mas nem a luz nem o volume confirmaram a mudança."
        ns["falar_com_lipsync"](fala, "carinhosa" if luz_ok or volume_ok else "calma", 1)
        return bool(luz_ok or volume_ok)


def criar_preferencias_sugestoes_runtime(
    namespace_getter: Callable[[], Mapping[str, Any]],
) -> PreferenciasSugestoesRuntime:
    return PreferenciasSugestoesRuntime(namespace_getter)
