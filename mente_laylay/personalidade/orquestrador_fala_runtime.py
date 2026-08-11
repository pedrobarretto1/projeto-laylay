"""Orquestra a fala final e sua continuidade na mente única."""

from __future__ import annotations

import json
import time
from threading import RLock
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.estado_tecnico_llm import eh_estado_tecnico_llm
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural


DEPENDENCIAS_ORQUESTRADOR_FALA = (
    "_registrar_mente_curta", "_estado_compartilhado_runtime",
    "_encerrar_topico_mente", "salvar_memoria", "print",
    "_dirigir_fala_mente", "_voz_runtime",
    "_registrar_continuidade_da_fala_mente", "_threading",
    "_agendar_fala_proativa",
)

DEPENDENCIAS_OPCIONAIS_ORQUESTRADOR_FALA = (
    "_registrar_metrica_diagnostico",
)


class OrquestradorFalaRuntime:
    def __init__(
        self,
        namespace_getter: Callable[[], Mapping[str, Any]] | None = None,
        *,
        servicos_iniciais: Mapping[str, Any] | None = None,
    ) -> None:
        origem = dict(servicos_iniciais or {})
        if not origem and callable(namespace_getter):
            origem = dict(namespace_getter() or {})
        self._servicos = self._filtrar(origem)
        self._lock_confirmacoes = RLock()
        self._confirmacoes_operacionais: dict[tuple[str, str], dict[str, Any]] = {}
        self._metricas_confirmacoes = {
            "tentativas": 0,
            "emitidas": 0,
            "duplicadas_suprimidas": 0,
            "rejeitadas_voz": 0,
        }
        self._observadores_fala_final: list[Callable[..., Any]] = []

    def registrar_observador_fala_final(self, observador: Callable[..., Any]) -> None:
        """Observa somente falas que atravessaram a fronteira final da voz."""
        if not callable(observador):
            raise TypeError("observador de fala final deve ser chamável")
        if observador not in self._observadores_fala_final:
            self._observadores_fala_final.append(observador)

    def remover_observador_fala_final(self, observador: Callable[..., Any]) -> bool:
        """Reverte publicação antecipada sem afetar o fallback no início da voz."""
        if observador not in self._observadores_fala_final:
            return False
        self._observadores_fala_final.remove(observador)
        return True

    @staticmethod
    def _filtrar(servicos: Mapping[str, Any]) -> dict[str, Any]:
        return {
            nome: servicos[nome]
            for nome in (
                *DEPENDENCIAS_ORQUESTRADOR_FALA,
                *DEPENDENCIAS_OPCIONAIS_ORQUESTRADOR_FALA,
            )
            if nome in servicos
        }

    def _ns(self) -> Mapping[str, Any]:
        return dict(self._servicos)

    def conectar_servicos(self, servicos: Mapping[str, Any]) -> None:
        ausentes = [
            nome for nome in DEPENDENCIAS_ORQUESTRADOR_FALA
            if nome not in servicos
        ]
        if ausentes:
            raise RuntimeError(
                "serviços ausentes no orquestrador de fala: "
                + ", ".join(ausentes)
            )
        self._servicos = self._filtrar(servicos)

    @property
    def servicos_registrados(self) -> tuple[str, ...]:
        return tuple(sorted(self._servicos))

    @staticmethod
    def _normalizar_assinatura(valor: Any) -> Any:
        if isinstance(valor, Mapping):
            metadados = {
                "confidence", "confianca", "referencia_contextual",
                "_semantica", "_rota_contextual",
            }
            return {
                str(chave): OrquestradorFalaRuntime._normalizar_assinatura(item)
                for chave, item in sorted(valor.items(), key=lambda par: str(par[0]))
                if str(chave) not in metadados
                and not str(chave).endswith("_original")
            }
        if isinstance(valor, (list, tuple, set, frozenset)):
            itens = [
                OrquestradorFalaRuntime._normalizar_assinatura(item)
                for item in valor
            ]
            if isinstance(valor, (set, frozenset)):
                return sorted(itens, key=repr)
            return itens
        if valor is None or isinstance(valor, (str, int, float, bool)):
            return valor
        return str(valor)

    def _chave_confirmacao_operacional(
        self, resultado: Any, mental: Mapping[str, Any],
    ) -> tuple[str, str] | None:
        plano = dict(mental.get("plano_turno_atual") or {})
        turno = dict(mental.get("turno_atual") or {})
        turno_id = str(turno.get("id") or plano.get("id") or "").strip()
        plano_id = str(plano.get("id") or "").strip()
        fase = str(plano.get("fase") or "").strip().casefold()
        if (
            not turno_id
            or plano_id != turno_id
            or fase not in {"planejado", "resposta_planejada"}
        ):
            return None
        if isinstance(resultado, Mapping):
            dados = dict(resultado)
        else:
            dados = {
                "intent": getattr(resultado, "intent", ""),
                "status": getattr(resultado, "status", ""),
                "alvo": getattr(resultado, "alvo", ""),
                "params": getattr(resultado, "params", {}),
                "confirmado": getattr(resultado, "confirmado", None),
            }
        if dados.get("confirmado") is not True:
            return None
        intent = str(dados.get("intent") or dados.get("acao") or "").strip().upper()
        status = str(dados.get("status") or "").strip().casefold()
        if not intent or not status:
            return None
        assinatura = json.dumps(
            {
                "intent": intent,
                "status": status,
                "alvo": str(dados.get("alvo") or "").strip(),
                "params": self._normalizar_assinatura(
                    dados.get("params") if isinstance(dados.get("params"), Mapping) else {}
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return turno_id, assinatura

    def _podar_confirmacoes_operacionais(self) -> None:
        if len(self._confirmacoes_operacionais) <= 256:
            return
        antigas = sorted(
            self._confirmacoes_operacionais.items(),
            key=lambda item: float(item[1].get("ts") or 0.0),
        )
        for chave, _registro in antigas[: len(antigas) - 192]:
            self._confirmacoes_operacionais.pop(chave, None)

    def falar_resultado_operacional(
        self,
        resultado: Any,
        texto: str,
        emocao: str = "calma",
        nivel: int = 1,
    ) -> bool:
        """Entrega no máximo uma confirmação para o mesmo resultado do turno."""
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        mental = dict(estado.mental)
        chave = self._chave_confirmacao_operacional(resultado, mental)
        with self._lock_confirmacoes:
            self._metricas_confirmacoes["tentativas"] += 1
            if chave is not None and chave in self._confirmacoes_operacionais:
                self._metricas_confirmacoes["duplicadas_suprimidas"] += 1
                ns["print"](
                    "🔇 [VOZ:RESULTADO] confirmação operacional duplicada suprimida"
                )
                return True
            if chave is not None:
                self._confirmacoes_operacionais[chave] = {
                    "status": "reservada", "ts": time.monotonic(),
                }
                self._podar_confirmacoes_operacionais()

        try:
            contexto_resultado = getattr(resultado, "contexto", {})
            avaliacao_evento = (
                dict(contexto_resultado.get("avaliacao_evento") or {})
                if isinstance(contexto_resultado, Mapping)
                else {}
            )
            aceita = self.falar(
                texto,
                emocao,
                nivel,
                _avaliacao_evento=avaliacao_evento,
            )
        except Exception:
            if chave is not None:
                with self._lock_confirmacoes:
                    self._confirmacoes_operacionais.pop(chave, None)
            raise

        with self._lock_confirmacoes:
            if aceita:
                self._metricas_confirmacoes["emitidas"] += 1
                if chave is not None:
                    self._confirmacoes_operacionais[chave] = {
                        "status": "emitida", "ts": time.monotonic(),
                    }
            else:
                self._metricas_confirmacoes["rejeitadas_voz"] += 1
                if chave is not None:
                    self._confirmacoes_operacionais.pop(chave, None)
        return bool(aceita)

    def diagnostico(self) -> dict[str, Any]:
        with self._lock_confirmacoes:
            return {
                **dict(self._metricas_confirmacoes),
                "reservadas": sum(
                    1 for registro in self._confirmacoes_operacionais.values()
                    if str(registro.get("status") or "") == "reservada"
                ),
                "resultados_retidos": len(self._confirmacoes_operacionais),
                "autoriza_execucao": False,
            }

    def registrar_fala_proativa_emitida(self, texto, itens) -> None:
        ns = self._ns()
        tipos = [
            str(item.get("tipo") or "").strip().lower()
            for item in list(itens or []) if isinstance(item, dict)
        ]
        habilidade = "+".join(dict.fromkeys(tipo for tipo in tipos if tipo)) or "proativa"
        ns["_registrar_mente_curta"](
            "", str(texto or ""), intencao="FALA_PROATIVA",
            alvo="inicialização" if "briefing" in tipos or "abertura" in tipos else habilidade,
            escopo="conversa", habilidade=f"proativa:{habilidade}",
        )

    def finalizar_encerramento_assunto(self) -> None:
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        mental = dict(estado.mental)
        if mental.get("encerramento_assunto_pendente") != "topico":
            return
        motivo = str(mental.get("encerramento_assunto_motivo") or "encerrado pelo usuário")
        nova_mente, nova_conversa = ns["_encerrar_topico_mente"](
            mental, dict(estado.conversacional), motivo=motivo,
        )
        estado.substituir("mental", nova_mente)
        estado.substituir("conversacional", nova_conversa)
        ns["salvar_memoria"]()
        ns["print"]("🧠 [CONTEXTO] assunto encerrado; fatos duráveis preservados")

    def falar(
        self,
        texto: str,
        emocao: str = "calma",
        nivel=None,
        wait: bool = False,
        _proativa: bool = False,
        _avaliacao_evento: Mapping[str, Any] | None = None,
    ) -> bool:
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        mental_antes = dict(estado.mental)
        plano_antes = dict(mental_antes.get("plano_turno_atual") or {})
        # A fala já foi escrita pela LLM ou pelo executor operacional. Esta
        # fronteira não corrige estilo, autorreferência nem injeta memória.
        fala = str(texto or "").strip()
        if eh_estado_tecnico_llm(fala):
            ns["print"]("⚠️ [FALA] estado técnico da LLM absorvido antes da voz")
            if plano_antes.get("requer_execucao"):
                fala = (
                    "Minha resposta não ficou pronta agora, mas não vou "
                    "confirmar uma ação sem evidência."
                )
            else:
                fala = fala_contingencia_natural(
                    str(plano_antes.get("texto_usuario") or ""),
                    contexto=mental_antes,
                )
        # Resultados operacionais são validados pelo executor. Nas conversas,
        # toda rota de fala passa por este guardião, inclusive atalhos locais.
        if not plano_antes.get("requer_execucao"):
            guardiao = validar_alegacoes_da_fala(
                fala, plano=plano_antes, origem="canal_voz",
            )
            fala = str(guardiao.get("fala") or fala)
            if guardiao.get("problemas"):
                ns["print"](
                    "🛡️ [GUARDIÃO:FALA] "
                    f"problemas={guardiao.get('problemas') or []}"
                )
        mente_direcao = dict(mental_antes)
        if isinstance(_avaliacao_evento, Mapping) and _avaliacao_evento:
            mente_direcao["avaliacao_emocional_operacional_atual"] = dict(
                _avaliacao_evento
            )
        direcao = ns["_dirigir_fala_mente"](
            fala, texto_usuario=str(plano_antes.get("texto_usuario") or ""),
            estado_mental=mente_direcao, emocao=emocao, nivel=nivel,
            proativa=_proativa, preservar_texto=True,
        )
        fala = str(direcao.get("fala") or fala)
        emocao = str(direcao.get("emocao") or emocao or "calma")
        nivel = int(direcao.get("nivel") or nivel or 1)
        turno_id = str(
            dict(mental_antes.get("turno_atual") or {}).get("id")
            or plano_antes.get("id")
            or ""
        ).strip()
        mensagem_id = (
            f"proativa:{time.time_ns()}"
            if _proativa
            else (f"turno:{turno_id}" if turno_id else "")
        )
        aceita = ns["_voz_runtime"].falar(
            fala, emocao, nivel, wait=wait, _proativa=_proativa,
            _texto_publicado_antecipado=bool(self._observadores_fala_final),
        )
        if aceita is not False:
            inicio_publicacao = time.perf_counter()
            publicada = False
            for observador in tuple(self._observadores_fala_final):
                try:
                    resultado_observador = observador(
                        fala, emocao, nivel,
                        proativa=bool(_proativa),
                        mensagem_id=mensagem_id,
                    )
                    publicada = resultado_observador is not False or publicada
                except Exception as erro:
                    ns["print"](
                        "⚠️ [FALA:OBSERVADOR] consumidor isolado falhou: "
                        f"{type(erro).__name__}"
                    )
            registrar_metrica = ns.get("_registrar_metrica_diagnostico")
            if callable(registrar_metrica) and self._observadores_fala_final:
                duracao_ms = (time.perf_counter() - inicio_publicacao) * 1000.0
                try:
                    registrar_metrica(
                        "tts_texto_visivel", duracao_ms, publicada,
                        turno_id=turno_id,
                        rota="publicacao_visual",
                        fase="texto_final",
                    )
                except TypeError:
                    registrar_metrica(
                        "tts_texto_visivel", duracao_ms, publicada,
                    )
        if aceita is not False and not _proativa:
            mental = dict(estado.mental)
            plano = dict(mental.get("plano_turno_atual") or {})
            assunto = str(
                plano.get("dominio") or mental.get("ultimo_alvo")
                or mental.get("foco_conversacional_topico") or ""
            )
            mental["ultima_resposta"] = fala[:500]
            mental["ultima_fala_emitida_ts"] = time.time()
            mental["direcao_fala_atual"] = dict(direcao)
            historico = list(mental.get("historico_direcao_fala") or [])[-39:]
            historico.append(dict(direcao))
            mental["historico_direcao_fala"] = historico
            mental = ns["_registrar_continuidade_da_fala_mente"](
                mental, fala,
                texto_usuario=str(plano.get("texto_usuario") or mental.get("ultima_entrada") or ""),
                assunto=assunto, origem=str(plano.get("dominio") or "fala"),
                emocao=emocao,
            )
            estado.substituir("mental", mental)
            self.finalizar_encerramento_assunto()
        return bool(aceita)

    def entregar_fala_inicial_confirmada(
        self, tipo, texto, emocao="calma", nivel=1, *,
        adiar_se_interacao: bool = False,
        ao_entrega_adiada: Callable[[], Any] | None = None,
        detalhar: bool = False,
    ) -> bool | dict[str, Any]:
        ns = self._ns()
        conclusao = ns["_threading"].Event()
        resultado = {"entregue": False, "motivo": "sem_retorno"}

        def ao_concluir(entregue, motivo):
            resultado["entregue"] = bool(entregue)
            resultado["motivo"] = str(motivo or "")
            conclusao.set()

        agendada = ns["_agendar_fala_proativa"](
            tipo, texto, emocao, nivel, ao_concluir=ao_concluir, forcar_inicio=True,
        )
        if not agendada:
            return {"entregue": False, "pendente": False} if detalhar else False
        if not conclusao.wait(45.0):
            ns["print"](f"⚠️ [FALA INICIAL] entrega de {tipo} não foi confirmada em 45s")
            return {"entregue": False, "pendente": False} if detalhar else False
        if not resultado["entregue"]:
            ns["print"](f"⚠️ [FALA INICIAL] {tipo} não entregue: {resultado['motivo']}")
            pendente = False
            if adiar_se_interacao and resultado["motivo"] == "interacao_iniciada":
                def ao_concluir_adiado(entregue, motivo):
                    if entregue:
                        ns["print"](f"✅ [FALA INICIAL] {tipo} pendente foi entregue.")
                        if callable(ao_entrega_adiada):
                            ao_entrega_adiada()
                    else:
                        ns["print"](
                            f"⚠️ [FALA INICIAL] entrega pendente de {tipo} falhou: {motivo}"
                        )

                pendente = bool(ns["_agendar_fala_proativa"](
                    tipo, texto, emocao, nivel,
                    ao_concluir=ao_concluir_adiado,
                    forcar_inicio=False,
                    preservar_ate_entrega=True,
                ))
                if pendente:
                    ns["print"](
                        f"🧠 [FALA INICIAL] {tipo} preservado; será entregue após o turno atual."
                    )
            if detalhar:
                return {"entregue": False, "pendente": pendente}
        else:
            estado = ns["_estado_compartilhado_runtime"]
            mental = dict(estado.mental)
            mental["ultima_fala_emitida_ts"] = time.time()
            mental["ultima_resposta"] = str(texto or "").strip()[:500]
            estado.substituir("mental", mental)
        if detalhar:
            return {"entregue": bool(resultado["entregue"]), "pendente": False}
        return bool(resultado["entregue"])


def criar_orquestrador_fala_runtime(
    namespace_getter: Callable[[], Mapping[str, Any]] | None = None,
    *,
    servicos_iniciais: Mapping[str, Any] | None = None,
) -> OrquestradorFalaRuntime:
    return OrquestradorFalaRuntime(
        namespace_getter, servicos_iniciais=servicos_iniciais,
    )
