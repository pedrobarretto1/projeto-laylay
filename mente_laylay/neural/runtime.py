"""Runtime fail-closed do especialista neural de comandos."""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Iterable, Mapping

from .contratos import normalizar_previsao_neural
from .experiencias import BufferExperienciasNeurais
from .shadow import RelatorioShadowNeural


class EspecialistaNeuralComandosRuntime:
    """Observa a fala e publica divergências sem alterar o turno recebido."""

    MODOS = frozenset({"off", "shadow", "candidate"})

    def __init__(
        self,
        *,
        modelo: Any,
        buffer: BufferExperienciasNeurais,
        publicar: Callable[[dict[str, Any]], Any] | None,
        modo: str = "shadow",
        intents_permitidas: Iterable[str] = (),
        log: Callable[..., Any] = print,
    ) -> None:
        modo_normalizado = str(modo or "shadow").strip().casefold()
        self.modo = modo_normalizado if modo_normalizado in self.MODOS else "shadow"
        self.modelo = modelo
        self.buffer = buffer
        self.relatorio_shadow = RelatorioShadowNeural(buffer.caminho.parent)
        self.publicar = publicar
        self.intents_permitidas = frozenset(
            str(item).strip().upper() for item in intents_permitidas if str(item).strip()
        )
        self.log = log
        self._lock = threading.RLock()
        self._previsoes_por_texto: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _chave(texto: str) -> str:
        return " ".join(str(texto or "").casefold().split())

    def _prever_texto(self, texto: str) -> dict[str, Any]:
        inicio = time.perf_counter()
        bruto = self.modelo.prever(texto)
        previsao = normalizar_previsao_neural(
            bruto,
            texto=texto,
            modelo=str(getattr(self.modelo, "versao", "desconhecido")),
            intents_permitidas=self.intents_permitidas,
        )
        previsao["latency_ms"] = round(
            (time.perf_counter() - inicio) * 1000.0, 4
        )
        previsao["route"] = (
            "SHADOW" if self.modo == "shadow" else "CANDIDATE"
        )
        return previsao

    @staticmethod
    def _segmentos_canonicos(
        turno: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        segmentos = turno.get("segmentos")
        if not isinstance(segmentos, list):
            return []
        return [
            dict(item)
            for item in segmentos
            if isinstance(item, Mapping) and str(item.get("texto") or "").strip()
        ]

    @staticmethod
    def _comando_executavel(previsao: Mapping[str, Any]) -> bool:
        return bool(
            previsao.get("is_command")
            and not previsao.get("negated")
            and not (
                previsao.get("ood")
                and previsao.get("ood_calibrated", True)
            )
        )

    def observar(
        self,
        texto: str,
        *,
        turno_legado: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.modo == "off" or not str(texto or "").strip():
            return {}
        legado = dict(turno_legado or {})
        try:
            segmentos = self._segmentos_canonicos(legado)
            if len(segmentos) > 1:
                previsoes_segmentos = []
                for posicao, segmento in enumerate(segmentos):
                    previsao_segmento = self._prever_texto(
                        str(segmento.get("texto") or "").strip()
                    )
                    previsao_segmento["indice"] = int(
                        segmento.get("indice")
                        if segmento.get("indice") is not None
                        else posicao
                    )
                    previsoes_segmentos.append(previsao_segmento)
                executaveis = [
                    item
                    for item in previsoes_segmentos
                    if self._comando_executavel(item)
                ]
                primaria = executaveis[0] if executaveis else previsoes_segmentos[0]
                previsao = normalizar_previsao_neural(
                    primaria,
                    texto=texto,
                    modelo=str(getattr(self.modelo, "versao", "desconhecido")),
                    intents_permitidas=self.intents_permitidas,
                )
                previsao.update(
                    latency_ms=round(
                        sum(
                            float(item.get("latency_ms") or 0.0)
                            for item in previsoes_segmentos
                        ),
                        4,
                    ),
                    route=(
                        "SHADOW" if self.modo == "shadow" else "CANDIDATE"
                    ),
                    multi_segmento=True,
                    segmentos_origem="turno_canonico",
                    previsoes_segmentos=previsoes_segmentos,
                    is_command=bool(executaveis),
                    negated=(
                        False
                        if executaveis
                        else any(bool(item.get("negated")) for item in previsoes_segmentos)
                    ),
                    receipt_comparavel=len(executaveis) <= 1,
                )
            else:
                previsao = self._prever_texto(texto)
                previsao["multi_segmento"] = False
                previsao["receipt_comparavel"] = True
        except Exception as erro:
            self.log(f"⚠️ [NEURAL:COMANDOS] observação isolada: {type(erro).__name__}")
            return {}
        comando_legado = bool(legado.get("autoriza_execucao"))
        previsao["comparacao_legado"] = {
            "modalidade": str(
                legado.get("modalidade_geral") or legado.get("modalidade") or ""
            ),
            "autoriza_execucao": comando_legado,
            "veto_execucao_operacional": bool(legado.get("veto_execucao_operacional")),
            "divergiu_comando": bool(previsao.get("is_command")) != comando_legado,
        }
        with self._lock:
            self._previsoes_por_texto[self._chave(texto)] = dict(previsao)
            if len(self._previsoes_por_texto) > 128:
                primeira = next(iter(self._previsoes_por_texto))
                self._previsoes_por_texto.pop(primeira, None)
        if callable(self.publicar):
            self.publicar(dict(previsao))
        return previsao

    def finalizar_observacao_turno(
        self,
        texto: str,
        turno_final: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Compara a sombra com a decisão final sem alterar sua autoridade."""
        if self.modo == "off" or not str(texto or "").strip():
            return {}
        chave = self._chave(texto)
        with self._lock:
            previsao = dict(self._previsoes_por_texto.get(chave) or {})
        if not previsao:
            return {}
        try:
            comparacao = self.relatorio_shadow.registrar_turno(
                texto=texto,
                previsao=previsao,
                turno=dict(turno_final or {}),
            )
        except Exception as erro:
            self.log(f"⚠️ [NEURAL:SHADOW] relatório isolado: {type(erro).__name__}")
            return previsao
        previsao["comparacao_canonica"] = dict(comparacao)
        previsao["autoriza_execucao"] = False
        with self._lock:
            self._previsoes_por_texto[chave] = dict(previsao)
        if callable(self.publicar):
            self.publicar(dict(previsao))
        return previsao

    def preaquecer(self) -> bool:
        if self.modo == "off":
            return False
        carregar = getattr(self.modelo, "precarregar", None)
        if not callable(carregar):
            return True
        try:
            return bool(carregar())
        except Exception as erro:
            self.log(f"⚠️ [NEURAL:COMANDOS] pré-carga isolada: {type(erro).__name__}")
            return False

    def observar_resultado(
        self,
        resultado: Mapping[str, Any] | None,
        texto: str,
        executou: bool | None,
        *,
        origem: str = "",
        status: str = "",
    ) -> dict[str, Any]:
        observado = dict(resultado or {})
        if status and not observado.get("status"):
            observado["status"] = status
        confirmado = observado.get("confirmado")
        with self._lock:
            previsao = dict(self._previsoes_por_texto.get(self._chave(texto)) or {})
        experiencia = self.buffer.registrar_resultado(
            texto=texto,
            previsao=previsao,
            resultado=observado,
            executou=executou,
            confirmado=confirmado,
            origem=origem,
        )
        if previsao:
            try:
                self.relatorio_shadow.registrar_receipt(
                    texto=texto,
                    previsao=previsao,
                    resultado=observado,
                    executou=executou,
                    confirmado=confirmado,
                )
            except Exception as erro:
                self.log(f"⚠️ [NEURAL:SHADOW] receipt isolado: {type(erro).__name__}")
        return experiencia

    def observar_correcao(self, correcao: Mapping[str, Any] | None) -> dict[str, Any]:
        dados = dict(correcao or {})
        return self.buffer.registrar_correcao(
            texto_original=str(dados.get("texto_original") or dados.get("texto_execucao") or ""),
            intent_errada=str(dados.get("intent_errada") or ""),
            intent_correta=str(dados.get("intent_correta") or ""),
            params_corretos=(
                dados.get("params_corretos")
                if isinstance(dados.get("params_corretos"), Mapping)
                else {}
            ),
            texto_correcao=str(dados.get("texto_correcao") or ""),
            confirmada_por_execucao=(
                str(dados.get("status") or "") == "confirmada_por_execucao"
            ),
        )
