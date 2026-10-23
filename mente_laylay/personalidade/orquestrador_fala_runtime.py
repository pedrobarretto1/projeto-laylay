"""Orquestra a fala final e sua continuidade na mente única."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.estado_tecnico_llm import eh_estado_tecnico_llm
from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
from mente_laylay.cognicao.preferencia_humor import contexto_humor_turno
from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
from mente_laylay.personalidade.contingencia_natural import fala_contingencia_natural
from mente_laylay.personalidade.retrato_entrega import (
    RetratoEntregaFala,
    criar_retrato_entrega_fala,
)
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.progresso_fala import ProgressoFala
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_fala_observada, registrar_esclarecimento_proposicao_entregue,
)
from mente_laylay.personalidade.confirmacao_llm import (
    INTENTS_INFORMATIVOS, personalizar_confirmacao_composta_llm,
)
from mente_laylay.personalidade.planejador_resposta import (
    classificar_resultado, fala_factual_resultados_compostos, fala_resultado_por_aspectos,
)


DEPENDENCIAS_ORQUESTRADOR_FALA = (
    "_registrar_mente_curta", "_estado_compartilhado_runtime",
    "_encerrar_topico_mente", "salvar_memoria", "print",
    "_dirigir_fala_mente", "_voz_runtime",
    "_registrar_continuidade_da_fala_mente", "_threading",
    "_agendar_fala_proativa",
)

DEPENDENCIAS_OPCIONAIS_ORQUESTRADOR_FALA = (
    "_registrar_metrica_diagnostico",
    "_registrar_entrega_comunicativa",
)


@dataclass(slots=True)
class _LoteResultadosOperacionais:
    turno_id: str
    texto_usuario: str
    enviar_mensagem: Callable[..., Any] | None
    resultados: list[ResultadoAcao] = field(default_factory=list)
    informacoes: dict[str, str] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    contexto: dict[str, Any] = field(default_factory=dict)
    falha_cadeia: tuple[str, int, int] | None = None
    resposta_publicada: bool = False
    fala_publicada: str = ""
    complemento: ComplementoConversacionalTurno | None = None
    complemento_aceito: bool = False

    def registrar_falha(self, trecho: str, indice: int, concluidas: int) -> None:
        self.falha_cadeia = (str(trecho or ""), int(indice), int(concluidas))


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
            "rejeitadas_entrega": 0,
        }
        self._observadores_fala_final: list[Callable[..., Any]] = []
        self._observadores_texto_final: list[Callable[..., Any]] = []
        self._observadores_entrega_resultados: list[Callable[..., Any]] = []
        self._textos_publicados_turno: dict[str, list[str]] = {}
        self._progressos: dict[str, ProgressoFala] = {}
        self._lote_resultados: ContextVar[_LoteResultadosOperacionais | None] = ContextVar(
            "lote_resultados_operacionais", default=None,
        )

    def _turno_fala_atual(self) -> str:
        mental = self._ns()["_estado_compartilhado_runtime"].mental
        return str(dict(mental.get("turno_atual") or {}).get("id") or "").strip()

    @contextmanager
    def agrupar_resultados_operacionais(
        self, *, texto_usuario: str, enviar_mensagem: Callable[..., Any] | None = None,
    ):
        """Adia somente apresentação; cada executor continua publicando seu receipt."""
        anterior = self._lote_resultados.get()
        if anterior is not None:
            yield anterior
            return
        lote = _LoteResultadosOperacionais(self._turno_fala_atual(), str(texto_usuario or ""), enviar_mensagem)
        token = self._lote_resultados.set(lote)
        try:
            yield lote
        except Exception:
            lote.avisos.append("Não consegui concluir o restante do pedido.")
            raise
        finally:
            self._lote_resultados.reset(token)
            self._entregar_resultados_compostos(lote)

    def acumular_resultado_operacional(
        self, resultado: Any, texto: str, emocao: str = "calma", nivel: int = 1,
        *, contexto: Mapping[str, Any] | None = None,
    ) -> bool:
        """Consome a apresentação de um resultado quando há pedido composto ativo."""
        lote = self._lote_resultados.get()
        if lote is None:
            return False
        if not isinstance(resultado, ResultadoAcao) or not resultado.id_solicitacao or resultado.origem != "executor":
            lote.avisos.append("Não consegui validar o resultado de uma das ações com segurança.")
            return True
        receipt = deepcopy(resultado)
        indice = next((i for i, item in enumerate(lote.resultados)
                       if item.id_solicitacao == receipt.id_solicitacao), None)
        if indice is None:
            lote.resultados.append(receipt)
        else:
            # Republicação pode rebaixar a certeza da mesma ocorrência. A
            # apresentação segue o snapshot mais recente do publicador.
            lote.resultados[indice] = receipt
        lote.contexto.update(dict(contexto or {}))
        if receipt.intent in INTENTS_INFORMATIVOS or receipt.tem_observacoes_do_executor:
            lote.informacoes[receipt.id_solicitacao] = (fala_resultado_por_aspectos(receipt)
                if receipt.tem_observacoes_do_executor else str(texto or "").strip())
        else:
            lote.informacoes.pop(receipt.id_solicitacao, None)
        return True

    def _entregar_resultados_compostos(self, lote: _LoteResultadosOperacionais) -> bool:
        ns = self._ns()
        if not lote.resultados and not lote.avisos and lote.falha_cadeia is None and lote.complemento is None:
            return False
        def complemento_vigente() -> bool:
            if lote.complemento is None:
                return True
            turno = dict(ns["_estado_compartilhado_runtime"].mental.get("turno_atual") or {})
            return (lote.complemento.turno_id == turno.get("id")
                    and ComplementoConversacionalTurno.da_prioridade(turno, lote.texto_usuario) == lote.complemento)

        if not complemento_vigente():
            ns["print"]("🛡️ [FALA:COMPOSTA] complemento retido: cobertura não está vigente")
            return False
        if not lote.turno_id or lote.turno_id != self._turno_fala_atual():
            ns["print"]("🛡️ [FALA:COMPOSTA] resultado retido: turno mudou antes da entrega")
            return False
        avisos = list(dict.fromkeys(lote.avisos))
        if lote.falha_cadeia is not None:
            _trecho, indice, concluidas = lote.falha_cadeia
            if not lote.resultados or classificar_resultado(lote.resultados[-1]) in {"sucesso", "sem_acao"}:
                avisos.append(
                    f"Não consegui executar a etapa {indice}; parei nesse ponto."
                    if indice > 0 else "Uma das etapas não foi confirmada."
                )
        fala_segura = fala_factual_resultados_compostos(lote.resultados, informacoes=lote.informacoes)
        complemento = lote.complemento
        if complemento is not None and not lote.resultados and not avisos:
            avisos.append("Ainda não tenho confirmação do resultado da parte operacional.")
        if complemento is not None:
            fala_segura = " ".join([p for p in (fala_segura, *avisos) if p])
        if lote.resultados or complemento is not None:
            confirmacao = personalizar_confirmacao_composta_llm(
                lote.resultados, fala_segura,
                enviar_mensagem=lote.enviar_mensagem, contexto=lote.contexto,
                informacoes=lote.informacoes,
                **({"texto_conversacional": complemento.texto,
                    "avisos_obrigatorios": avisos,
                    "complemento_conversacional": complemento} if complemento is not None else {}),
            )
            fala = confirmacao.fala
            emocao, nivel = confirmacao.emocao, confirmacao.nivel
            lote.complemento_aceito = complemento is not None and confirmacao.usada_llm
            if confirmacao.motivo_fallback:
                ns["print"]("⚠️ [FALA:COMPOSTA] fallback factual | " + confirmacao.motivo_fallback)
        else:
            fala = ""
            emocao, nivel = "calma", 1
        fala = " ".join([parte for parte in (fala, *(avisos if complemento is None else [])) if parte]).strip()
        # Uma chamada demorada pode terminar depois de a conversa mudar.
        # Os receipts continuam publicados; sua fala não pertence ao turno novo.
        if lote.turno_id != self._turno_fala_atual() or not complemento_vigente():
            ns["print"]("🛡️ [FALA:COMPOSTA] resultado retido: turno mudou durante autoria")
            return False
        if not fala:
            return False
        aceita = self.falar(fala, emocao, nivel, _resultados_entrega=tuple(lote.resultados))
        lote.resposta_publicada = bool(aceita or fala in self.textos_publicados_turno(lote.turno_id))
        lote.fala_publicada = fala if lote.resposta_publicada else ""
        return aceita

    def textos_publicados_turno(self, turno_id: Any) -> tuple[str, ...]:
        """Texto aceito por canal textual; não é receipt de áudio ou de ação."""
        with self._lock_confirmacoes:
            return tuple(self._textos_publicados_turno.get(str(turno_id or ""), ()))

    def registrar_observador_texto_final(
        self, observador: Callable[..., Any],
    ) -> None:
        """Publica o texto consolidado sem depender da fila de áudio.

        A interface desktop é um canal textual. Uma indisponibilidade ou uma
        deduplicação da voz não pode esconder uma resposta que já atravessou
        os guardiões conversacionais.
        """
        if not callable(observador):
            raise TypeError("observador de texto final deve ser chamável")
        if observador not in self._observadores_texto_final:
            self._observadores_texto_final.append(observador)

    def registrar_observador_fala_final(self, observador: Callable[..., Any]) -> None:
        """Observa somente falas que atravessaram a fronteira final da voz."""
        if not callable(observador):
            raise TypeError("observador de fala final deve ser chamável")
        if observador not in self._observadores_fala_final:
            self._observadores_fala_final.append(observador)

    def registrar_observador_entrega_resultados(self, observador: Callable[..., Any]) -> None:
        """Receipts da invocação acompanham entrega textual ou áudio confirmado."""
        if not callable(observador):
            raise TypeError("observador de entrega deve ser chamável")
        if observador not in self._observadores_entrega_resultados:
            self._observadores_entrega_resultados.append(observador)

    def publicar_texto_proativo(
        self,
        texto: str,
        emocao: str = "calma",
        nivel: int = 1,
        *,
        _retrato_entrega: RetratoEntregaFala | None = None,
    ) -> bool:
        """Entrega uma fala autônoma aos canais textuais antes do TTS.

        Falas de turno já atravessam :meth:`falar`. O lote proativo nasce na
        fila de voz, por isso precisa desta fronteira específica para não
        desaparecer do Terminal nem ser associado a uma entrada do usuário.
        """
        fala = str(texto or "").strip()
        if not fala:
            return False
        retrato = _retrato_entrega or criar_retrato_entrega_fala(
            getattr(self._ns()["_estado_compartilhado_runtime"], "conversacional", {}),
            mensagem_id=f"proativa:{time.time_ns()}",
        )
        mensagem_id = retrato.mensagem_id
        emocao, nivel = retrato.emocao, retrato.nivel
        publicado = False
        for observador in tuple(self._observadores_texto_final):
            try:
                resultado = observador(
                    fala,
                    str(emocao or "calma"),
                    max(1, min(3, int(nivel or 1))),
                    proativa=True,
                    mensagem_id=mensagem_id,
                )
                publicado = resultado is not False or publicado
            except Exception as erro:
                self._ns()["print"](
                    "⚠️ [TEXTO PROATIVO:OBSERVADOR] consumidor isolado falhou: "
                    f"{type(erro).__name__}"
                )
        return publicado

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
        if isinstance(resultado, ResultadoAcao) and resultado.tem_observacoes_do_executor:
            texto = fala_resultado_por_aspectos(resultado)
        if self.acumular_resultado_operacional(resultado, texto, emocao, nivel):
            return True
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        mental = dict(estado.mental)
        # Um único retrato do receipt alimenta validação e deduplicação.
        # Falha de leitura não pode virar licença para a fala original nem
        # reservar uma confirmação usando atributos de um objeto corrompido.
        dados_resultado: dict[str, Any] = {}
        resultado_entrega = None
        try:
            resultado_entrega = deepcopy(resultado) if isinstance(resultado, ResultadoAcao) else None
            retrato = resultado_entrega if resultado_entrega is not None else resultado
            como_dict = getattr(retrato, "como_dict", None)
            bruto = como_dict() if callable(como_dict) else retrato
            if isinstance(bruto, Mapping):
                dados_resultado = dict(bruto)
        except Exception:
            dados_resultado = {}
        chave = self._chave_confirmacao_operacional(dados_resultado, mental)
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
            contexto_resultado = dados_resultado.get("contexto", {})
            avaliacao_evento = (
                dict(contexto_resultado.get("avaliacao_evento") or {})
                if isinstance(contexto_resultado, Mapping)
                else {}
            )

            # Última fronteira factual antes do TTS: mesmo que um executor
            # antigo ou um bug monte uma frase otimista demais, o receipt
            # recebido aqui decide o que pode ser afirmado. Resultados
            # confirmados atravessam sem alteração.
            texto_seguro = str(texto or "").strip()
            if dados_resultado:
                guardiao_resultado = validar_alegacoes_da_fala(
                    texto_seguro,
                    plano={
                        "requer_execucao": True,
                        "comandos": [dados_resultado],
                    },
                    origem="canal_voz",
                )
                texto_seguro = str(
                    guardiao_resultado.get("fala") or texto_seguro
                ).strip()
                if guardiao_resultado.get("problemas"):
                    ns["print"](
                        "🛡️ [GUARDIÃO:RESULTADO] "
                        f"problemas={guardiao_resultado.get('problemas') or []}"
                    )
            else:
                texto_seguro = "Não consegui validar o resultado dessa ação com segurança."
                ns["print"](
                    "🛡️ [GUARDIÃO:RESULTADO] problemas=['recibo_indisponivel_ou_invalido']"
                )

            aceita = self.falar(
                texto_seguro,
                emocao,
                nivel,
                _avaliacao_evento=avaliacao_evento,
                _resultados_entrega=(resultado_entrega,) if resultado_entrega is not None else (),
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
                self._metricas_confirmacoes["rejeitadas_entrega"] += 1
                if chave is not None:
                    self._confirmacoes_operacionais.pop(chave, None)
        return bool(aceita)

    def diagnostico(self) -> dict[str, Any]:
        with self._lock_confirmacoes:
            return {
                **dict(self._metricas_confirmacoes),
                # Alias histórico: conta rejeição comunicativa, não é
                # telemetria de rejeições do canal de áudio.
                "rejeitadas_voz": self._metricas_confirmacoes["rejeitadas_entrega"],
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

    def anunciar_etapa(
        self, plano: Mapping[str, Any], etapa: Mapping[str, Any], *,
        vigente: Callable[[], bool],
    ) -> None:
        """Anuncia uma etapa admitida e espera só o início do áudio.

        O executor mantém autoridade, cancelamento e receipt. Falha de voz
        não impede o trabalho; espera vencida invalida o anúncio enfileirado.
        """
        texto = str(etapa.get("descricao_progresso") or "").strip()
        if not texto:
            return
        chave = f"{plano['id']}:{etapa['id']}"
        with self._lock_confirmacoes:
            if chave in self._progressos:
                return
            progresso = ProgressoFala(chave, vigente)
            self._progressos[chave] = progresso
            while len(self._progressos) > 80:
                self._progressos.pop(next(iter(self._progressos)))
        if not self.falar(texto, _progresso=progresso):
            progresso.concluir()
            return
        voz = self._ns()["_voz_runtime"]
        progresso.aguardar_inicio(float(getattr(voz, "tts_timeout_s", 8.0)) + 1.0)

    def falar(
        self,
        texto: str,
        emocao: str = "calma",
        nivel=None,
        wait: bool = False,
        _proativa: bool = False,
        _avaliacao_evento: Mapping[str, Any] | None = None,
        _resultados_entrega: tuple[ResultadoAcao, ...] = (),
        _progresso: ProgressoFala | None = None,
    ) -> bool:
        """Aceita comunicação por texto publicado ou pela porta de voz.

        O bool permite concluir o tratamento do pedido. Aceitação na fila não
        comprova reprodução; callbacks de áudio e receipts mantêm esse papel.
        ``wait`` espera a tentativa de voz, sem invalidar texto já publicado.
        """
        lote = self._lote_resultados.get()
        if lote is not None and not _proativa and _progresso is None:
            fala_pendente = str(texto or "").strip()
            if fala_pendente:
                # A chamada direta não trouxe um receipt próprio. Receipts
                # de outras etapas não autorizam alegações deste aviso.
                guardiao_aviso = validar_alegacoes_da_fala(
                    fala_pendente,
                    plano={"requer_execucao": False, "comandos": [],
                           "exigir_receipt_para_estado": True,
                           "texto_usuario": lote.texto_usuario},
                    origem="canal_voz",
                )
                if guardiao_aviso.get("problemas"):
                    fala_pendente = "Não consegui validar uma das confirmações com segurança."
                    self._ns()["print"](
                        "🛡️ [FALA:COMPOSTA] aviso sem receipt | "
                        f"problemas={guardiao_aviso.get('problemas') or []}"
                    )
                lote.avisos.append(fala_pendente)
            return bool(fala_pendente)
        ns = self._ns()
        estado = ns["_estado_compartilhado_runtime"]
        mental_antes = dict(estado.mental)
        plano_antes = dict(mental_antes.get("plano_turno_atual") or {})
        # A fala já foi escrita pela LLM ou pelo executor operacional. Esta
        # fronteira não corrige estilo, autorreferência nem injeta memória.
        fala = str(texto or "").strip()
        if _progresso is not None:
            if not _progresso.pode_emitir():
                return False
            verificacao = validar_alegacoes_da_fala(
                fala, plano={"requer_execucao": False, "comandos": [],
                             "exigir_receipt_para_estado": True}, origem="canal_voz",
            )
            if verificacao.get("problemas"):
                return False
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
        turno_id = str(
            dict(mental_antes.get("turno_atual") or {}).get("id")
            or plano_antes.get("id") or ""
        ).strip()
        retrato_entrega = criar_retrato_entrega_fala(
            getattr(estado, "conversacional", {}),
            mensagem_id=(
                f"progresso:{_progresso.id}" if _progresso is not None
                else f"proativa:{time.time_ns()}" if _proativa
                else (f"turno:{turno_id}" if turno_id else "")
            ),
        )
        emocao, nivel = retrato_entrega.emocao, retrato_entrega.nivel
        direcao = ns["_dirigir_fala_mente"](
            fala, texto_usuario=str(plano_antes.get("texto_usuario") or ""),
            estado_mental=mente_direcao, emocao=emocao, nivel=nivel,
            proativa=_proativa, preservar_texto=True,
        )
        fala = str(direcao.get("fala") or fala)
        # O diretor sugere estilo, mas só o episódio da mente compartilhada
        # possui autoridade para emoção e intensidade publicadas em voz/texto.
        direcao = dict(direcao)
        emocao_proposta = str(direcao.get("emocao") or "").strip().casefold()
        if str(direcao.get("tom") or "").strip().casefold() == emocao_proposta:
            direcao["tom"] = emocao
        direcao["emocao"] = emocao
        direcao["nivel"] = nivel
        mensagem_id = retrato_entrega.mensagem_id
        resultados_entrega = deepcopy(tuple(_resultados_entrega))
        contexto_humor = contexto_humor_turno(
            operacional=bool(plano_antes.get("requer_execucao")),
            modo_jogo_ativo=bool(mental_antes.get("modo_jogo_ativo")),
        )
        inicio_publicacao_texto = time.perf_counter()
        texto_publicado = False
        for observador in tuple(self._observadores_texto_final):
            try:
                resultado_observador = observador(
                    fala, emocao, nivel,
                    proativa=bool(_proativa),
                    mensagem_id=mensagem_id,
                )
                texto_publicado = (
                    resultado_observador is not False or texto_publicado
                )
            except Exception as erro:
                ns["print"](
                    "⚠️ [TEXTO:OBSERVADOR] consumidor isolado falhou: "
                    f"{type(erro).__name__}"
                )
        if texto_publicado and not _proativa and turno_id and fala:
            with self._lock_confirmacoes:
                textos = self._textos_publicados_turno.setdefault(turno_id, [])
                if fala not in textos:
                    textos.append(fala)
                while len(self._textos_publicados_turno) > 64:
                    self._textos_publicados_turno.pop(next(iter(self._textos_publicados_turno)))
        registrar_entrega = ns.get("_registrar_entrega_comunicativa")
        ocorrencia_fala_id = f"{mensagem_id}:{time.time_ns()}"
        sessao_fala = mental_antes.get("sessao_conversa_ts")
        def concluir_entrega(entregue: bool, texto_entregue: str, canal: str) -> None:
            if _proativa or not mensagem_id:
                return
            if entregue is True and texto_entregue != fala:
                ns["print"]("⚠️ [FALA:EVIDÊNCIA] conteúdo entregue difere da ocorrência capturada")
            if (entregue is True and texto_entregue == fala
                    and callable(getattr(estado, "atualizar", None))):
                try:
                    def registrar_vinculo(mental):
                        # Entrega atrasada mantém o turno original, mas nunca
                        # contamina uma sessão/chat aberto depois da emissão.
                        if mental.get("sessao_conversa_ts") != sessao_fala:
                            return mental
                        registro = registrar_fala_observada(
                            mental.get("registro_semantico"),
                            ocorrencia_id=ocorrencia_fala_id, turno_id=turno_id,
                            fala=texto_entregue, resultados=resultados_entrega,
                            canal=canal,
                        )
                        return registrar_esclarecimento_proposicao_entregue(
                            {**mental, "registro_semantico": registro},
                            dict(plano_antes.get("contrato_fala") or {}).get("revisao_alegacao"),
                            entrega_id=ocorrencia_fala_id,turno_id=turno_id,
                        )
                    estado.atualizar("mental", registrar_vinculo)
                except (ValueError, TypeError) as erro:
                    ns["print"](f"⚠️ [FALA:EVIDÊNCIA] vínculo recusado: {type(erro).__name__}")
            if callable(registrar_entrega):
                try:
                    registrar_entrega(id_entrega=mensagem_id, fala=texto_entregue,
                        entregue=entregue, contexto_humor=contexto_humor, canal_entrega=canal)
                except Exception as erro:
                    ns["print"](f"⚠️ [ENTREGA:FEEDBACK] registro indisponível: {type(erro).__name__}")
            if entregue is True and resultados_entrega:
                for observador in tuple(self._observadores_entrega_resultados):
                    try:
                        observador(resultados=deepcopy(resultados_entrega), fala=texto_entregue,
                            id_entrega=mensagem_id, canal_entrega=canal)
                    except Exception as erro:
                        ns["print"](f"⚠️ [ENTREGA:RESULTADOS] observador isolado: {type(erro).__name__}")
        if texto_publicado:
            concluir_entrega(True, fala, "texto_publicado")
        parametros_entrega = {}
        if _progresso is not None:
            parametros_entrega["_progresso"] = _progresso
        if not texto_publicado and not _proativa and (callable(registrar_entrega) or resultados_entrega):
            parametros_entrega["_ao_concluir_entrega"] = lambda entregue, texto: concluir_entrega(
                entregue, texto, "audio_reproducao_confirmada")
        aceita = ns["_voz_runtime"].falar(
            fala, emocao, nivel, wait=wait, _proativa=_proativa,
            _texto_publicado_antecipado=bool(
                self._observadores_texto_final
                or self._observadores_fala_final
            ),
            _retrato_entrega=retrato_entrega,
            **parametros_entrega,
        )
        if aceita is not False:
            inicio_publicacao_fala = time.perf_counter()
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
                duracao_ms = (
                    time.perf_counter() - inicio_publicacao_fala
                ) * 1000.0
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
        registrar_metrica = ns.get("_registrar_metrica_diagnostico")
        if callable(registrar_metrica) and self._observadores_texto_final:
            duracao_ms = (
                time.perf_counter() - inicio_publicacao_texto
            ) * 1000.0
            try:
                registrar_metrica(
                    "tts_texto_visivel", duracao_ms, texto_publicado,
                    turno_id=turno_id,
                    rota="publicacao_visual_independente",
                    fase="texto_final",
                )
            except TypeError:
                registrar_metrica(
                    "tts_texto_visivel", duracao_ms, texto_publicado,
                )
        if (texto_publicado or aceita is not False) and not _proativa:
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
        return texto_publicado or bool(aceita)

    def entregar_fala_inicial_confirmada(
        self, tipo, texto, emocao="calma", nivel=1, *,
        adiar_se_interacao: bool = False,
        ao_entrega_adiada: Callable[[], Any] | None = None,
        detalhar: bool = False,
    ) -> bool | dict[str, Any]:
        ns = self._ns()
        conclusao = ns["_threading"].Event()
        resultado = {"entregue": False, "motivo": "sem_retorno"}
        entrega_lock = RLock()
        espera = {"encerrada": False, "concluida": False}

        def ao_concluir(entregue, motivo):
            with entrega_lock:
                if espera["concluida"]:
                    return
                espera["concluida"] = True
                resultado["entregue"] = bool(entregue)
                resultado["motivo"] = str(motivo or "")
                tardia = espera["encerrada"]
                conclusao.set()
            if tardia:
                if entregue:
                    ns["print"](f"✅ [FALA INICIAL] {tipo} pendente foi entregue.")
                    if callable(ao_entrega_adiada):
                        ao_entrega_adiada()
                else:
                    ns["print"](f"⚠️ [FALA INICIAL] entrega pendente de {tipo} falhou: {motivo}")

        agendada = ns["_agendar_fala_proativa"](
            tipo, texto, emocao, nivel, ao_concluir=ao_concluir, forcar_inicio=True,
        )
        if not agendada:
            return {"entregue": False, "pendente": False} if detalhar else False
        if not conclusao.wait(45.0):
            with entrega_lock:
                pendente = not espera["concluida"]
                espera["encerrada"] = pendente
            if pendente:
                ns["print"](f"🧠 [FALA INICIAL] {tipo} continua pendente após 45s; aguardando recibo de entrega.")
                return {"entregue": False, "pendente": True} if detalhar else False
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
