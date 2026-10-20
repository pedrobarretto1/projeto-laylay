"""Diretor único para presença espontânea da Laylay.

Sensores podem perceber muitas coisas; este runtime decide se vale interromper o
silêncio. Ele não executa comandos e não substitui o coordenador de
oportunidades. Seu papel é aplicar relevância, orçamento, variedade e segurança
antes de encaminhar uma observação ao restante da mente.
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.governanca_iniciativa import decisao_permite_emissao
from mente_laylay.cognicao.interpretador_continuidade import classificar_feedback_comunicativo
from mente_laylay.cognicao.interpretador_continuidade import solicitacao_feedback_humor
from mente_laylay.cognicao.interpretador_continuidade import resposta_indefinida_sobre_humor
from mente_laylay.cognicao.preferencia_humor import contexto_humor_turno


PERFIS_COMPANHIA = frozenset({"silencioso", "adaptativo", "presente"})
JANELA_FEEDBACK_PRESENCA_S = 600.0


def decisao_presenca_aceita_para_entrega(decisao: Mapping[str, Any] | None) -> bool:
    """Interpreta o recibo do Diretor sem confundir fila com efeito físico."""
    dados = dict(decisao or {})
    proposta = dados.get("proposta_comunicativa")
    return bool(
        str(dados.get("status") or "").casefold() == "proposta_cognitiva"
        and isinstance(proposta, Mapping)
        and proposta.get("agendada") is True
        and proposta.get("autoriza_execucao") is False
    )


def _codigo(valor: Any, limite: int = 96) -> str:
    texto = unicodedata.normalize("NFKD", str(valor or "").casefold())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-z0-9 _.:/-]+", "", texto)
    return re.sub(r"\s+", "_", texto).strip("_.:/-")[:limite]


def estado_presenca_inicial() -> dict[str, Any]:
    return {
        "versao": 2,
        "configuracao": {
            "ativo": True,
            "perfil": "adaptativo",
            "motivo_perfil": "inicio",
            "atualizado_ts": 0.0,
        },
        "aprendizado": {"categorias": {}},
        "historico": [],
        "ultima_emissao": {},
        "ultima_proposta_cognitiva": {},
        "atividade": {},
        "contadores": {
            "recebidas": 0,
            "emitidas": 0,
            "propostas_cognitivas": 0,
            "bloqueadas_contexto": 0,
            "bloqueadas_orcamento": 0,
            "bloqueadas_qualidade": 0,
            "bloqueadas_variedade": 0,
            "feedbacks": 0,
        },
    }


class DiretorPresencaRuntime:
    """Seleciona intervenções curtas sem transformar companhia em spam."""

    COOLDOWN_CATEGORIA = {
        "motivacao": 420.0,
        "celebracao": 300.0,
        "dica": 720.0,
        "musica": 1200.0,
        "companhia": 900.0,
        "curiosidade": 720.0,
    }
    COOLDOWN_JOGO = {
        "motivacao": 300.0,
        "celebracao": 180.0,
        "dica": 480.0,
        "musica": 900.0,
        "companhia": 420.0,
        "curiosidade": 300.0,
    }
    CONFIANCA_MINIMA = {
        "motivacao": 0.74,
        "celebracao": 0.76,
        "dica": 0.88,
        "musica": 0.78,
        "companhia": 0.72,
        "curiosidade": 0.72,
    }

    def __init__(
        self,
        *,
        estado_get: Callable[[], Mapping[str, Any]] = lambda: {},
        estado_set: Callable[[dict[str, Any]], Any] = lambda _estado: None,
        contexto_getter: Callable[[], Mapping[str, Any]] = lambda: {},
        registrar_oportunidade: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        processar_evento_cognitivo: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        processar_proposta_comunicativa: Callable[..., Mapping[str, Any]],
        concluir_evento_cognitivo: Callable[..., Mapping[str, Any]] | None = None,
        registrar_feedback: Callable[..., Any] | None = None,
        registrar_falha: Callable[..., Any] | None = None,
        recomendacao_musical: Callable[[str], str] | None = None,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Any] = time.sleep,
        log: Callable[[str], Any] = print,
        habilitado: bool = True,
        intervalo_ciclo_s: float = 15.0,
        stop_event: threading.Event | None = None,
        candidato_observado_getter: Callable[[], Mapping[str, Any]] | None = None,
        validar_observacao: Callable[[Mapping[str, Any]], bool] | None = None,
        notificacao_observada: threading.Event | None = None,
    ) -> None:
        self.estado_get = estado_get
        self.estado_set = estado_set
        self.contexto_getter = contexto_getter
        self.registrar_oportunidade = registrar_oportunidade
        if not callable(processar_evento_cognitivo):
            raise ValueError("processar_evento_cognitivo deve ser callable")
        if not callable(processar_proposta_comunicativa):
            raise ValueError("processar_proposta_comunicativa deve ser callable")
        self.processar_evento_cognitivo = processar_evento_cognitivo
        self.processar_proposta_comunicativa = processar_proposta_comunicativa
        self.concluir_evento_cognitivo = concluir_evento_cognitivo
        self.registrar_feedback = registrar_feedback
        self.registrar_falha = registrar_falha
        self.recomendacao_musical = recomendacao_musical
        self.clock = clock
        self.sleep = sleep
        self.log = log
        self.habilitado = bool(habilitado)
        self.intervalo_ciclo_s = max(2.0, float(intervalo_ciclo_s))
        self.stop_event = stop_event or threading.Event()
        self._lock = threading.RLock()
        self._running = False
        self.candidato_observado_getter = candidato_observado_getter
        self.validar_observacao = validar_observacao
        self.notificacao_observada = notificacao_observada

    def _falha(self, codigo: str, erro: BaseException) -> None:
        if callable(self.registrar_falha):
            self.registrar_falha("diretor_presenca", codigo, erro=erro)

    def _concluir_evento(self, turno: Mapping[str, Any], resultado: str) -> None:
        if not callable(self.concluir_evento_cognitivo):
            return
        try:
            self.concluir_evento_cognitivo(turno, resultado=resultado)
        except Exception as erro:
            self._falha("conclusao_evento_cognitivo", erro)

    def _estado(self) -> dict[str, Any]:
        try:
            recebido = dict(self.estado_get() or {})
        except Exception as erro:
            self._falha("estado_leitura", erro)
            recebido = {}
        base = estado_presenca_inicial()
        base.update(recebido)
        base["contadores"] = {
            **estado_presenca_inicial()["contadores"],
            **dict(base.get("contadores") or {}),
        }
        base["historico"] = [
            dict(item) for item in list(base.get("historico") or [])[-40:]
            if isinstance(item, Mapping)
        ]
        configuracao = {
            **estado_presenca_inicial()["configuracao"],
            **dict(base.get("configuracao") or {}),
        }
        perfil = str(configuracao.get("perfil") or "adaptativo").casefold()
        configuracao["perfil"] = perfil if perfil in PERFIS_COMPANHIA else "adaptativo"
        configuracao["ativo"] = bool(configuracao.get("ativo", True))
        base["configuracao"] = configuracao
        base["aprendizado"] = {
            "categorias": dict(
                dict(base.get("aprendizado") or {}).get("categorias") or {}
            ),
        }
        return base

    def configuracao_atual(self) -> dict[str, Any]:
        estado = self._estado()
        return dict(estado.get("configuracao") or {})

    def presenca_habilitada(self, _dominio: str = "") -> bool:
        return bool(self.habilitado and self.configuracao_atual().get("ativo", True))

    @staticmethod
    def _pontuacao_categoria(estado: Mapping[str, Any], categoria: str) -> int:
        categorias = dict(dict(estado.get("aprendizado") or {}).get("categorias") or {})
        return int(dict(categorias.get(categoria) or {}).get("pontuacao") or 0)

    def _escolher_perfil(
        self,
        estado: dict[str, Any],
        contexto: Mapping[str, Any],
        categoria: str = "companhia",
    ) -> str:
        """A própria Laylay calibra presença por atividade e feedback acumulado."""
        pontuacao = self._pontuacao_categoria(estado, categoria)
        if pontuacao <= -2:
            perfil, motivo = "silencioso", "feedback_negativo"
        elif contexto.get("modo_foco"):
            perfil, motivo = "silencioso", "concentracao_detectada"
        elif contexto.get("modo_jogo_ativo") and pontuacao >= 1:
            perfil, motivo = "presente", "jogo_com_feedback_positivo"
        else:
            perfil, motivo = "adaptativo", "contexto_neutro"
        config = dict(estado.get("configuracao") or {})
        if config.get("perfil") != perfil or config.get("motivo_perfil") != motivo:
            config.update(
                perfil=perfil,
                motivo_perfil=motivo,
                atualizado_ts=float(self.clock()),
            )
            estado["configuracao"] = config
        return perfil

    def _contexto(self) -> dict[str, Any]:
        try:
            valor = self.contexto_getter() or {}
            return dict(valor) if isinstance(valor, Mapping) else {}
        except Exception as erro:
            self._falha("contexto_leitura", erro)
            return {}

    @staticmethod
    def _evidencias(dados: Mapping[str, Any]) -> list[str]:
        valor = dados.get("evidencias")
        if isinstance(valor, str):
            valor = [valor]
        if not isinstance(valor, (list, tuple, set, frozenset)):
            return []
        # O transporte preserva a fonte; cortar aqui impediria o compositor
        # de distinguir uma oração inteira de um prefixo incompleto.
        return [str(item).strip() for item in valor if str(item).strip()][:5]

    @staticmethod
    def _incrementar(estado: dict[str, Any], campo: str) -> None:
        contadores = dict(estado.get("contadores") or {})
        contadores[campo] = int(contadores.get(campo) or 0) + 1
        estado["contadores"] = contadores

    def _bloqueio_contextual(self, dados: Mapping[str, Any], contexto: Mapping[str, Any], agora: float) -> str:
        if contexto.get("interacao_usuario_ativa"):
            return "interacao_usuario_ativa"
        if contexto.get("usuario_falando"):
            return "usuario_falando"
        if contexto.get("is_speaking") or contexto.get("turno_ativo"):
            return "fala_ou_turno_em_andamento"
        try:
            timestamp_evento = float(
                dados.get("timestamp") or dados.get("ts") or 0.0
            )
        except (TypeError, ValueError):
            timestamp_evento = 0.0
        try:
            validade_s = max(0.0, float(dados.get("validade_s") or 120.0))
        except (TypeError, ValueError):
            validade_s = 120.0
        if timestamp_evento > 0.0 and agora >= timestamp_evento + validade_s:
            return "evento_expirado"
        ultima_entrada = float(contexto.get("ultima_entrada_ts") or 0.0)
        if ultima_entrada and agora - ultima_entrada < 30.0:
            return "usuario_acabou_de_falar"
        dominio = _codigo(dados.get("dominio"), 24)
        categoria = _codigo(dados.get("categoria"), 24)
        if dominio == "jogo" and not contexto.get("modo_jogo_ativo"):
            return "jogo_nao_ativo"
        if dominio == "jogo" and categoria in {
            "dica", "musica", "motivacao", "celebracao", "companhia", "curiosidade",
        }:
            if not bool(dados.get("momento_seguro")):
                return "momento_de_jogo_inseguro"
        return ""

    def _bloqueio_qualidade(self, dados: Mapping[str, Any]) -> str:
        categoria = _codigo(dados.get("categoria"), 24) or "companhia"
        fala = str(dados.get("fala") or "").strip()
        try:
            confianca = float(dados.get("confianca") or 0.0)
        except (TypeError, ValueError):
            confianca = 0.0
        modo_cognitivo = callable(self.processar_evento_cognitivo)
        possui_evidencia = bool(
            self._evidencias(dados)
            or str(dados.get("motivo") or dados.get("conteudo") or "").strip()
        )
        if modo_cognitivo and not possui_evidencia:
            return "evento_sem_evidencia"
        if not modo_cognitivo and (not fala or len(fala) > 360):
            return "fala_ausente_ou_longa"
        if confianca < self.CONFIANCA_MINIMA.get(categoria, 0.80):
            return "confianca_insuficiente"
        evidencias = self._evidencias(dados)
        if categoria == "dica" and (not dados.get("fundamentada") or len(evidencias) < 2):
            return "dica_sem_duas_evidencias"
        if categoria == "musica" and bool(dados.get("executar_automaticamente")):
            return "musica_nao_pode_autotocar"
        return ""

    def _evento_cognitivo(
        self,
        dados: Mapping[str, Any],
        *,
        dominio: str,
        categoria: str,
        chave: str,
        agora: float,
    ) -> dict[str, Any]:
        evidencias = self._evidencias(dados)
        motivo = str(dados.get("motivo") or "").strip()[:500]
        descricao = str(
            dados.get("conteudo")
            or " | ".join(evidencias)
            or ("" if motivo else f"evento de presença {categoria} observado em {dominio}")
        ).strip()[:500]
        return {
            "natureza": "evento",
            "origem": str(dados.get("origem") or "diretor_presenca"),
            "tipo": f"presenca_{categoria}",
            "conteudo": descricao,
            "evidencia": {
                "descricao": descricao,
                "itens": evidencias,
                **({"foco_evidencia": dados["foco_evidencia"]}
                   if "foco_evidencia" in dados else {}),
                **({"proposta_reacao": dados["proposta_reacao"]}
                   if "proposta_reacao" in dados else {}),
                "motivo": motivo,
                "dominio": dominio,
                "categoria": categoria,
                **({"observacao_corporal":dict(dados["observacao_corporal"])}
                   if isinstance(dados.get("observacao_corporal"),Mapping) else {}),
                **({"ocorrencia_observada":dict(dados["ocorrencia_observada"])}
                   if dados.get("_reacao_observada_validada") else {}),
            },
            "confianca": float(dados.get("confianca") or 0.0),
            "timestamp": agora,
            "trace_id": f"presenca:{dominio}:{categoria}:{chave}",
            "autoridade_usuario": False,
            "permissao_execucao": False,
        }

    def _registrar_resultado_entrega(
        self,
        *,
        id_entrega: str,
        entregue: bool,
        motivo: str,
        fala: str,
        registro_proposta: Mapping[str, Any],
        ao_concluir_fonte: Callable[[bool, str], Any] | None,
    ) -> None:
        """Converte apenas entrega confirmada em emissão observável e feedbackável."""
        momento = float(self.clock())
        resultado = {
            "entregue": bool(entregue),
            "motivo": str(motivo or ""),
            "ts": momento,
        }
        with self._lock:
            estado = self._estado()
            ultima_proposta = dict(estado.get("ultima_proposta_cognitiva") or {})
            if ultima_proposta.get("id_entrega") == id_entrega:
                ultima_proposta["resultado_entrega"] = resultado
                estado["ultima_proposta_cognitiva"] = ultima_proposta

            if entregue:
                emissao = {
                    "id_entrega": id_entrega,
                    "entregue": True,
                    "ts": momento,
                    "proposta_ts": float(registro_proposta.get("ts") or 0.0),
                    "dominio": str(registro_proposta.get("dominio") or ""),
                    "categoria": str(registro_proposta.get("categoria") or ""),
                    "chave": str(registro_proposta.get("chave") or ""),
                    "origem": str(registro_proposta.get("origem") or ""),
                    "fala": str(fala or "").strip(),
                    "contexto_humor": str(registro_proposta.get("contexto_humor") or
                        contexto_humor_turno(modo_jogo_ativo=bool(self._contexto().get("modo_jogo_ativo")))),
                    "canal_entrega": str(registro_proposta.get("canal_entrega") or "audio_reproducao_confirmada"),
                    "autoriza_execucao": False,
                    "solicitacao_feedback_humor": solicitacao_feedback_humor(fala),
                }
                estado["historico"] = [
                    *list(estado.get("historico") or []),
                    emissao,
                ][-40:]
                estado["ultima_emissao"] = {
                    **emissao,
                    "feedback_registrado": False,
                }
                self._incrementar(estado, "emitidas")
            self.estado_set(estado)

        if callable(ao_concluir_fonte):
            try:
                ao_concluir_fonte(bool(entregue), str(motivo or ""))
            except Exception as erro:
                self._falha("callback_entrega_fonte", erro)

    def registrar_entrega_observada(
        self, *, id_entrega: str, entregue: bool, motivo: str, fala: str,
        dominio: str, categoria: str, chave: str, origem: str,
        contexto_humor: str = "", canal_entrega: str = "",
    ) -> None:
        """Recebe o receipt de outro produtor pela mesma porta de feedback.

        O produtor conserva decisão e fila; o Diretor só registra a ocorrência
        entregue, sem gerar outra fala, oportunidade ou autorização.
        """
        if entregue is not True or not all(str(v or "").strip() for v in (
            id_entrega, dominio, categoria, chave, origem,
        )):
            return
        with self._lock:
            if any(str(i.get("id_entrega") or "") == id_entrega
                   for i in self._estado().get("historico") or []):
                return
            self._registrar_resultado_entrega(
                id_entrega=id_entrega, entregue=True, motivo=motivo, fala=fala,
                registro_proposta={
                    "dominio": dominio, "categoria": categoria, "chave": chave,
                    "origem": origem, "autoriza_execucao": False,
                    "contexto_humor": contexto_humor, "canal_entrega": canal_entrega,
                }, ao_concluir_fonte=None,
            )

    def registrar_entrega_comunicativa(
        self, *, id_entrega: str, fala: str, entregue: bool,
        contexto_humor: str, canal_entrega: str,
    ) -> None:
        """Registra receipt textual ou de reprodução; não prova audição física."""
        if (entregue is not True or not str(fala or "").strip()
            or contexto_humor not in {"jogo", "conversa", "comandos"}
            or canal_entrega not in {"texto_publicado", "audio_reproducao_confirmada"}):
            return
        self.registrar_entrega_observada(
            id_entrega=id_entrega, entregue=True, motivo=canal_entrega, fala=fala,
            dominio=contexto_humor, categoria="resposta", chave=id_entrega,
            origem="orquestrador_fala", contexto_humor=contexto_humor,
            canal_entrega=canal_entrega,
        )

    def _processar_proposta_cognitiva(
        self,
        estado: dict[str, Any],
        dados: Mapping[str, Any],
        *,
        dominio: str,
        categoria: str,
        chave: str,
        agora: float,
        decisao_iniciativa: Mapping[str, Any],
    ) -> dict[str, Any]:
        evento = self._evento_cognitivo(
            dados,
            dominio=dominio,
            categoria=categoria,
            chave=chave,
            agora=agora,
        )
        try:
            turno = dict(self.processar_evento_cognitivo(evento) or {})
        except Exception as erro:
            self._falha("evento_cognitivo", erro)
            decisao = {
                "status": "nao_processada",
                "motivo": "falha_cognicao_evento",
                "categoria": categoria,
                "ts": agora,
            }
            estado["ultima_decisao"] = decisao
            self.estado_set(estado)
            return decisao

        contrato_fala = dict(turno.get("contrato_fala") or {})
        contrato_valido = bool(
            turno.get("natureza_entrada") == "evento"
            and turno.get("autoriza_execucao") is False
            and contrato_fala.get("funcao") == "reacao_evento"
            and contrato_fala.get("autoriza_execucao") is False
        )
        if not contrato_valido:
            decisao = {
                "status": "nao_processada",
                "motivo": "contrato_cognitivo_invalido",
                "categoria": categoria,
                "ts": agora,
            }
            estado["ultima_decisao"] = decisao
            self.estado_set(estado)
            self._concluir_evento(turno, "contrato_cognitivo_invalido")
            return decisao

        registro = {
            "ts": agora,
            "dominio": dominio,
            "categoria": categoria,
            "chave": chave,
            "origem": str(dados.get("origem") or "diretor_presenca").casefold(),
            "evento": evento,
            "contrato_fala": contrato_fala,
            "contexto_humor": contexto_humor_turno(
                modo_jogo_ativo=bool(self._contexto().get("modo_jogo_ativo"))),
            **({"ocorrencia_observada":dict(dados["ocorrencia_observada"])}
               if dados.get("_reacao_observada_validada") else {}),
        }
        id_entrega = f"{evento.get('trace_id') or 'presenca'}:{agora:.6f}"
        registro["id_entrega"] = id_entrega
        ao_concluir_fonte = (
            dados.get("ao_concluir")
            if callable(dados.get("ao_concluir"))
            else None
        )
        ao_iniciar_fonte = (
            dados.get("ao_iniciar")
            if callable(dados.get("ao_iniciar"))
            else None
        )
        ao_materializar_fonte = (
            dados.get("ao_materializar_fala")
            if callable(dados.get("ao_materializar_fala"))
            else None
        )
        ciclo_entrega: dict[str, Any] = {
            "fala": "",
            "concluido": False,
            "em_composicao": True,
            "pendente": None,
        }

        def ao_materializar_fala(fala: str) -> None:
            ciclo_entrega["fala"] = str(fala or "").strip()
            if callable(ao_materializar_fonte):
                ao_materializar_fonte(ciclo_entrega["fala"])

        def ao_concluir(entregue: bool, motivo: str) -> None:
            with self._lock:
                if ciclo_entrega["concluido"]:
                    return
                ciclo_entrega["concluido"] = True
                if ciclo_entrega["em_composicao"]:
                    ciclo_entrega["pendente"] = (bool(entregue), str(motivo or ""))
                    return
            self._registrar_resultado_entrega(
                id_entrega=id_entrega,
                entregue=bool(entregue),
                motivo=str(motivo or ""),
                fala=str(ciclo_entrega["fala"]),
                registro_proposta=registro,
                ao_concluir_fonte=ao_concluir_fonte,
            )

        proposta_comunicativa: dict[str, Any] = {}
        opcoes_admissao: dict[str, Any] = {}
        if dados.get("_reacao_observada_validada"):
            from mente_laylay.autonomia.ocorrencia_observada import AdmissaoReacaoObservada
            opcoes_admissao["admissao_observada"] = AdmissaoReacaoObservada(
                trace_id=str(evento["trace_id"]),
                validar_vigencia=lambda: bool(callable(self.validar_observacao) and self.validar_observacao(dados)))
        if callable(self.processar_proposta_comunicativa):
            emocao = str(
                dados.get("emocao")
                or ("animada" if categoria in {"motivacao", "celebracao"} else "calma")
            )
            try:
                proposta_comunicativa = dict(
                    self.processar_proposta_comunicativa(
                        turno,
                        evento=evento,
                        dominio=dominio,
                        categoria=categoria,
                        emocao=emocao,
                        nivel=int(dados.get("nivel") or 1),
                        origem=str(dados.get("origem") or ""),
                        decisao_iniciativa=dict(decisao_iniciativa),
                        ao_iniciar=ao_iniciar_fonte,
                        ao_concluir=ao_concluir,
                        ao_materializar_fala=ao_materializar_fala,
                        **opcoes_admissao,
                        **({"validar_vigencia":lambda: self.validar_observacao(dados)}
                           if callable(self.validar_observacao) and "observacao_corporal" in dados else {}),
                    )
                    or {}
                )
            except Exception as erro:
                self._falha("proposta_comunicativa", erro)
                proposta_comunicativa = {
                    "status": "falha_geracao",
                    "agendada": False,
                    "emissao_fisica": False,
                    "autoriza_execucao": False,
                }
            registro["proposta_comunicativa"] = proposta_comunicativa
        status_materializacao = (
            _codigo(proposta_comunicativa.get("status"), 48)
            if proposta_comunicativa
            else "nao_solicitada"
        ) or "sem_status"
        self._concluir_evento(turno, status_materializacao)
        estado["ultima_proposta_cognitiva"] = registro
        self._incrementar(estado, "propostas_cognitivas")
        decisao = {
            "status": "proposta_cognitiva",
            "categoria": categoria,
            "dominio": dominio,
            "contrato_fala": contrato_fala,
            "emissao_fisica": False,
            "ts": agora,
        }
        if proposta_comunicativa:
            decisao["proposta_comunicativa"] = proposta_comunicativa
        estado["ultima_decisao"] = decisao
        self.estado_set(estado)
        with self._lock:
            ciclo_entrega["em_composicao"] = False
            conclusao_pendente = ciclo_entrega["pendente"]
            ciclo_entrega["pendente"] = None
        if conclusao_pendente is not None:
            entregue, motivo = conclusao_pendente
            self._registrar_resultado_entrega(
                id_entrega=id_entrega,
                entregue=entregue,
                motivo=motivo,
                fala=str(ciclo_entrega["fala"]),
                registro_proposta=registro,
                ao_concluir_fonte=ao_concluir_fonte,
            )
        agendada = bool(proposta_comunicativa.get("agendada"))
        emissao_confirmada = bool(proposta_comunicativa.get("emissao_fisica"))
        self.log(
            f"🧠 [PRESENÇA:PROPOSTA] dominio={dominio} categoria={categoria} "
            f"status={status_materializacao} agendada={agendada} "
            f"emissao_confirmada={emissao_confirmada}"
        )
        return decisao

    def _bloqueio_orcamento(self, estado: Mapping[str, Any], dados: Mapping[str, Any], agora: float) -> str:
        historico = list(estado.get("historico") or [])
        if dados.get("_reacao_observada_validada"):
            from mente_laylay.autonomia.ocorrencia_observada import avaliar_relevancia_observada
            avaliacao = avaliar_relevancia_observada(dados,
                estado.get("admissoes_observadas") or [], agora=agora,
                perfil=str(estado["configuracao"].get("perfil") or "adaptativo"),
                pontuacao_feedback=self._pontuacao_categoria(estado,"companhia"))
            if isinstance(dados, dict):
                dados["_avaliacao_reacao_observada"] = avaliacao
            return "" if avaliacao["permitida"] else avaliacao["motivo"]
        origem = str(dados.get("origem") or "").strip().casefold()
        if origem == "observador_area_transferencia":
            # Copiar algo relevante é uma interação implícita do usuário, não
            # uma dica aleatória da rotina. Ela possui antispam próprio e não
            # disputa o orçamento de comentários espontâneos.
            if any(
                item.get("origem") == origem
                and agora - float(item.get("ts") or 0.0) < 60.0
                for item in historico
            ):
                return "cooldown_area_transferencia"
            return ""
        config = dict(estado.get("configuracao") or {})
        perfil = str(config.get("perfil") or "adaptativo")
        dominio = _codigo(dados.get("dominio"), 24) or "cotidiano"
        if dominio == "jogo" and perfil != "silencioso":
            janela_global = 1200.0
            limite_global = 7 if perfil == "presente" else 5
        else:
            janela_global = 2700.0 if perfil == "silencioso" else 1800.0
            limite_global = 1 if perfil == "silencioso" else 4 if perfil == "presente" else 3
        recentes = [item for item in historico if agora - float(item.get("ts") or 0.0) < janela_global]
        if len(recentes) >= limite_global:
            return "orcamento_global_30m"
        if perfil == "silencioso":
            janela, limite = (1500.0, 1) if dominio == "jogo" else (2700.0, 1)
        elif perfil == "presente":
            janela, limite = (600.0, 4) if dominio == "jogo" else (1200.0, 2)
        else:
            janela, limite = (600.0, 3) if dominio == "jogo" else (1200.0, 1)
        if sum(1 for item in historico if item.get("dominio") == dominio and agora - float(item.get("ts") or 0.0) < janela) >= limite:
            return "orcamento_dominio"
        categoria = _codigo(dados.get("categoria"), 24) or "companhia"
        cooldowns = self.COOLDOWN_JOGO if dominio == "jogo" else self.COOLDOWN_CATEGORIA
        cooldown = cooldowns.get(categoria, 900.0)
        fator = 1.65 if perfil == "silencioso" else 0.75 if perfil == "presente" else 1.0
        aprendido = dict(dict(estado.get("aprendizado") or {}).get("categorias") or {})
        pontuacao = int(dict(aprendido.get(categoria) or {}).get("pontuacao") or 0)
        if pontuacao < 0:
            fator += min(0.75, abs(pontuacao) * 0.15)
        elif pontuacao > 0:
            fator -= min(0.20, pontuacao * 0.05)
        cooldown *= max(0.65, fator)
        if any(item.get("categoria") == categoria and agora - float(item.get("ts") or 0.0) < cooldown for item in historico):
            return "cooldown_categoria"
        return ""

    def considerar(self, evento: Mapping[str, Any] | None) -> dict[str, Any]:
        dados = dict(evento or {})
        dados.pop("_reacao_observada_validada", None)
        dados.pop("_avaliacao_reacao_observada", None)
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            self._incrementar(estado, "recebidas")
            if not self.habilitado or not bool(dict(estado.get("configuracao") or {}).get("ativo", True)):
                estado["ultima_decisao"] = {"status": "desabilitado", "ts": agora}
                self.estado_set(estado)
                return dict(estado["ultima_decisao"])

            categoria = _codigo(dados.get("categoria"), 24) or "companhia"
            dominio = _codigo(dados.get("dominio"), 24) or "cotidiano"
            chave = _codigo(
                dados.get("chave")
                or dados.get("motivo")
                or " | ".join(self._evidencias(dados))
                or dados.get("fala"),
                96,
            )
            contexto = self._contexto()
            self._escolher_perfil(estado, contexto, categoria)
            motivo = self._bloqueio_contextual(dados, contexto, agora)
            contador = "bloqueadas_contexto"
            if not motivo and "ocorrencia_observada" in dados:
                from mente_laylay.autonomia.ocorrencia_observada import identidade_ocorrencia
                try:
                    vigente = bool(identidade_ocorrencia(dados) and callable(self.validar_observacao)
                        and self.validar_observacao(dados))
                except Exception as erro:
                    self._falha("validar_observacao", erro)
                    vigente = False
                if not vigente:
                    motivo = "observacao_expirada"
                elif dominio == "corpo":
                    dados["_reacao_observada_validada"] = True
            if not motivo:
                motivo = self._bloqueio_qualidade(dados)
                contador = "bloqueadas_qualidade"
            if not motivo:
                motivo = self._bloqueio_orcamento(estado, dados, agora)
                contador = "bloqueadas_orcamento"
            ultima = dict(estado.get("ultima_emissao") or {})
            if not motivo and chave and chave == ultima.get("chave"):
                motivo = "repeticao_semantica"
                contador = "bloqueadas_variedade"
            idade_ultima = agora - float(ultima.get("ts") or 0.0)
            cooldowns_variedade = self.COOLDOWN_JOGO if dominio == "jogo" else self.COOLDOWN_CATEGORIA
            limite_variedade = cooldowns_variedade.get(categoria, 900.0) * 1.10
            if (
                not motivo and ultima.get("categoria") == categoria
                and not dados.get("_reacao_observada_validada")
                and str(dados.get("origem") or "").casefold() != "observador_area_transferencia"
                and categoria not in {"celebracao"} and idade_ultima < limite_variedade
            ):
                motivo = "categoria_consecutiva"
                contador = "bloqueadas_variedade"
            if motivo:
                self._incrementar(estado, contador)
                decisao = {"status": "bloqueada", "motivo": motivo, "categoria": categoria, "ts": agora,
                    **({"relevancia_observada":dict(dados["_avaliacao_reacao_observada"])}
                       if dados.get("_avaliacao_reacao_observada") else {})}
                estado["ultima_decisao"] = decisao
                self.estado_set(estado)
                if dominio == "jogo":
                    self.log(
                        f"🌙 [PRESENÇA:JOGO] bloqueada | categoria={categoria} "
                        f"| motivo={motivo}"
                    )
                return decisao

            oportunidade = {
                "origem": str(dados.get("origem") or "diretor_presenca"),
                "tipo": f"presenca_{categoria}",
                "dominio": dominio,
                "chave": f"presenca:{dominio}:{categoria}:{chave}",
                "confianca": float(dados.get("confianca") or 0.0),
                "utilidade": int(dados.get("utilidade") or (84 if categoria == "dica" else 68)),
                "risco": "baixo",
                "momento_seguro": bool(dados.get("momento_seguro")),
                "validade_s": float(dados.get("validade_s") or 120.0),
                "tags": [dominio, categoria, *self._evidencias(dados)],
                "acao_proposta": dados.get("acao_proposta"),
                "executavel": bool(dados.get("executavel")),
                "reversivel": bool(dados.get("reversivel")),
                "assunto": str(dados.get("assunto") or ""),
                "autoriza_execucao": False,
                **({"ocorrencia_observada":dict(dados["ocorrencia_observada"])}
                   if dados.get("_reacao_observada_validada") else {}),
            }
            decisao_iniciativa: Mapping[str, Any] = {}
            if callable(self.registrar_oportunidade):
                try:
                    decisao_iniciativa = self.registrar_oportunidade(oportunidade) or {}
                except Exception as exc:
                    self.log(f"⚠️ [PRESENÇA] coordenador indisponível: {type(exc).__name__}: {exc}")
            if not decisao_permite_emissao(decisao_iniciativa):
                decisao = {
                    "status": "bloqueada",
                    "motivo": "governanca",
                    "categoria": categoria,
                    "decisao_iniciativa": dict(decisao_iniciativa),
                    "ts": agora,
                }
                estado["ultima_decisao"] = decisao
                self.estado_set(estado)
                return decisao

            if callable(self.processar_evento_cognitivo):
                if dados.get("_reacao_observada_validada"):
                    avaliacao = dict(dados["_avaliacao_reacao_observada"])
                    estado["admissoes_observadas"] = [*(estado.get("admissoes_observadas") or []),
                        {**avaliacao,"ts":agora}][-32:]
                    estado["ultima_reacao_observada"] = {
                        "ts":agora, "ocorrencia_observada":dict(dados["ocorrencia_observada"]),
                        "etapa":"admissao", "nao_prova_reproducao":True,
                        "avaliacao":avaliacao,
                    }
                return self._processar_proposta_cognitiva(
                    estado,
                    dados,
                    dominio=dominio,
                    categoria=categoria,
                    chave=chave,
                    agora=agora,
                    decisao_iniciativa=decisao_iniciativa,
                )

            decisao = {
                "status": "nao_processada",
                "motivo": "cognicao_evento_indisponivel",
                "categoria": categoria,
                "ts": agora,
            }
            estado["ultima_decisao"] = decisao
            self.estado_set(estado)
            return decisao

    @staticmethod
    def _evento_feedback_emissao(
        emissao: Mapping[str, Any], observado_ts: float,
    ) -> dict[str, Any]:
        """Transporta a identidade da entrega sem promover a fala a autoridade."""
        id_entrega = str(emissao.get("id_entrega") or "")
        return {
            "id_evento": id_entrega,
            "id_entrega": id_entrega,
            "dominio": str(emissao.get("dominio") or ""),
            "origem_produtor": str(emissao.get("origem") or ""),
            "categoria": str(emissao.get("categoria") or ""),
            "alvo": str(emissao.get("chave") or ""),
            "entrega_ts": float(emissao.get("ts") or 0.0),
            "observado_ts": observado_ts,
            "entregue": emissao.get("entregue") is True,
            "contexto_humor": str(emissao.get("contexto_humor") or ""),
        }

    def _registrar_resultado_feedback_compartilhado(
        self, id_entrega: str, retorno: Any,
    ) -> None:
        """Publica o diagnóstico somente na emissão que originou o feedback."""
        if not id_entrega:
            return
        resultado = retorno.get("aprendizado_compartilhado") if isinstance(retorno, Mapping) else None
        status = str(resultado.get("status") or "indisponivel") if isinstance(resultado, Mapping) else "indisponivel"
        with self._lock:
            estado = self._estado()
            emissao = dict(estado.get("ultima_emissao") or {})
            if str(emissao.get("id_entrega") or "") != id_entrega:
                ocorrencias = [item for item in estado.get("historico") or []
                               if str(item.get("id_entrega") or "") == id_entrega]
                if len(ocorrencias) != 1:
                    return
                emissao = dict(ocorrencias[0])
            if not emissao.get("feedback_registrado"):
                return
            anterior = dict(emissao.get("aprendizado_compartilhado") or {})
            emissao["aprendizado_compartilhado"] = {"status": status, "id_evento": id_entrega}
            self._atualizar_emissao_feedback(estado, emissao)
            if status == "registrado" and anterior.get("status") != "registrado":
                self._incrementar(estado, "feedbacks_compartilhados")
            self.estado_set(estado)

    @staticmethod
    def _atualizar_emissao_feedback(estado: dict[str, Any], emissao: Mapping[str, Any]) -> None:
        """Mantém o feedback na ocorrência entregue, mesmo após outra emissão."""
        id_entrega = str(emissao.get("id_entrega") or "")
        atual = estado.get("ultima_emissao") or {}
        if str(atual.get("id_entrega") or "") == id_entrega:
            estado["ultima_emissao"] = dict(emissao)
        if id_entrega:
            estado["historico"] = [
                dict(emissao) if str(item.get("id_entrega") or "") == id_entrega else item
                for item in estado.get("historico") or []
            ]

    def observar_resposta(self, texto: str) -> dict[str, Any]:
        """Aprende com resposta explícita sem consumir nem reinterpretar o turno."""
        resultado = classificar_feedback_comunicativo(texto)
        if not resultado:
            if resposta_indefinida_sobre_humor(texto):
                agora = float(self.clock())
                with self._lock:
                    estado = self._estado()
                    ultima = dict(estado.get("ultima_emissao") or {})
                    if (ultima.get("solicitacao_feedback_humor") is True
                        and not ultima.get("feedback_registrado")
                        and 0 <= agora - float(ultima.get("ts") or 0.0) <= JANELA_FEEDBACK_PRESENCA_S):
                        ultima["resposta_humor_relacionada_ts"] = agora
                        self._atualizar_emissao_feedback(estado, ultima)
                        self.estado_set(estado)
            return {}
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            ultima = dict(estado.get("ultima_emissao") or {})
            if (
                not ultima or ultima.get("feedback_registrado")
                or agora - float(ultima.get("ts") or 0.0) > JANELA_FEEDBACK_PRESENCA_S
            ):
                return {}
            ultima["feedback_registrado"] = True
            ultima["feedback"] = resultado
            ultima["feedback_ts"] = agora
            self._atualizar_emissao_feedback(estado, ultima)
            aprendizado = dict(estado.get("aprendizado") or {})
            categorias = dict(aprendizado.get("categorias") or {})
            categoria = str(ultima.get("categoria") or "companhia")
            registro = dict(categorias.get(categoria) or {})
            delta = 1 if resultado == "aceita" else -2 if resultado == "recusa" else -1
            registro["pontuacao"] = max(-4, min(4, int(registro.get("pontuacao") or 0) + delta))
            registro["ultimo_feedback"] = resultado
            registro["ts"] = agora
            categorias[categoria] = registro
            estado["aprendizado"] = {"categorias": categorias}
            self._incrementar(estado, "feedbacks")
            self.estado_set(estado)
        retorno_feedback = None
        if callable(self.registrar_feedback):
            try:
                retorno_feedback = self.registrar_feedback(
                    "jogo" if ultima.get("dominio") == "jogo" else ultima.get("categoria"),
                    True if resultado == "aceita" else False if resultado == "recusa" else None,
                    resultado=resultado,
                    texto_feedback=str(texto or "").strip(),
                    evento_feedback=self._evento_feedback_emissao(ultima, agora),
                )
            except Exception as erro:
                retorno_feedback = {"aprendizado_compartilhado": {"status": "falha"}}
                self._falha("feedback_resposta", erro)
        self._registrar_resultado_feedback_compartilhado(str(ultima.get("id_entrega") or ""), retorno_feedback)
        return {"resultado": resultado, "categoria": ultima.get("categoria")}

    def registrar_silencio_pendente(self) -> dict[str, Any]:
        """Registra silêncio como sinal fraco, uma única vez e sem punição imediata."""
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            ultima = dict(estado.get("ultima_emissao") or {})
            idade = agora - float(ultima.get("ts") or 0.0)
            if (
                not ultima or ultima.get("feedback_registrado")
                or ultima.get("resposta_humor_relacionada_ts")
                or idade < JANELA_FEEDBACK_PRESENCA_S
            ):
                return {}
            ultima["feedback_registrado"] = True
            ultima["feedback"] = "silencio"
            ultima["feedback_ts"] = agora
            self._atualizar_emissao_feedback(estado, ultima)
            self._incrementar(estado, "feedbacks")
            self.estado_set(estado)
        retorno_feedback = None
        if callable(self.registrar_feedback):
            try:
                retorno_feedback = self.registrar_feedback(
                    "jogo" if ultima.get("dominio") == "jogo" else ultima.get("categoria"),
                    None, resultado="silencio",
                    evento_feedback=self._evento_feedback_emissao(ultima, agora),
                )
            except Exception as erro:
                retorno_feedback = {"aprendizado_compartilhado": {"status": "falha"}}
                self._falha("feedback_silencio", erro)
        self._registrar_resultado_feedback_compartilhado(str(ultima.get("id_entrega") or ""), retorno_feedback)
        return {"resultado": "silencio", "categoria": ultima.get("categoria")}

    def _candidato_cotidiano(self, contexto: Mapping[str, Any], estado: dict[str, Any], agora: float) -> dict[str, Any]:
        if contexto.get("modo_jogo_ativo"):
            estado["atividade"] = {}
            return {}
        assunto = str(contexto.get("assunto") or "").strip()
        titulo = str(contexto.get("titulo_janela") or "").strip()
        chave = _codigo(f"{assunto}:{titulo}", 96)
        atividade = dict(estado.get("atividade") or {})
        if not chave or chave != atividade.get("chave"):
            estado["atividade"] = {"chave": chave, "assunto": assunto, "inicio_ts": agora}
            return {}
        duracao = agora - float(atividade.get("inicio_ts") or agora)
        perfil = self._escolher_perfil(estado, contexto, "companhia")
        limiar = 3600.0 if perfil == "silencioso" else 2100.0 if perfil == "presente" else 3000.0
        if duracao < limiar or assunto not in {"Programação", "Estudo", "Trabalho"}:
            return {}
        fala = "Você tá num foco bonito faz um tempo. Só não deixa o corpo pagar a conta: uma pausa curta agora pode salvar o ritmo depois."
        if callable(self.recomendacao_musical) and not contexto.get("musica_atual_status"):
            try:
                musical = str(self.recomendacao_musical("foco") or "").strip()
            except Exception as erro:
                self._falha("recomendacao_musical", erro)
                musical = ""
            if musical:
                fala = musical
                categoria = "musica"
            else:
                categoria = "companhia"
        else:
            categoria = "companhia"
        return {
            "origem": "presenca_cotidiana",
            "dominio": "musica" if categoria == "musica" else "rotina",
            "categoria": categoria,
            "fala": fala,
            "confianca": 0.86,
            "utilidade": 61,
            "evidencias": [assunto, "atividade contínua por cinquenta minutos"],
            "fundamentada": True,
            "momento_seguro": True,
            "chave": f"foco_longo:{chave}",
        }

    def executar_ciclo(self, *, incluir_cotidiano: bool = True) -> dict[str, Any]:
        if incluir_cotidiano:
            self.registrar_silencio_pendente()
        # O produtor só oferece fatos. Este mesmo diretor conserva orçamento,
        # prioridade, feedback e receipt de entrega; não roda na thread serial.
        if callable(self.candidato_observado_getter):
            candidato = dict(self.candidato_observado_getter() or {})
            if candidato:
                return self.considerar(candidato)
        if not incluir_cotidiano:
            return {"status": "observando"}
        agora = float(self.clock())
        with self._lock:
            estado = self._estado()
            contexto = self._contexto()
            candidato = self._candidato_cotidiano(contexto, estado, agora)
            self.estado_set(estado)
        return self.considerar(candidato) if candidato else {"status": "observando"}

    def executar(self) -> None:
        self._running = True
        proximo_cotidiano = 0.0
        try:
            while self._running and not self.stop_event.is_set():
                cotidiano = time.monotonic() >= proximo_cotidiano
                if cotidiano:
                    proximo_cotidiano = time.monotonic() + self.intervalo_ciclo_s
                # Limpa antes da leitura: publicação durante autoria permanece
                # sinalizada. Várias mudanças convergem no fato mais recente.
                if self.notificacao_observada is not None:
                    self.notificacao_observada.clear()
                try:
                    self.executar_ciclo(incluir_cotidiano=cotidiano)
                except Exception as exc:
                    self.log(f"⚠️ [PRESENÇA] ciclo ignorado: {type(exc).__name__}: {exc}")
                    self._falha("ciclo", exc)
                while self._running and not self.stop_event.is_set():
                    restante = proximo_cotidiano - time.monotonic()
                    if restante <= 0:
                        break
                    if self.notificacao_observada is None:
                        self.stop_event.wait(restante)
                    elif self.notificacao_observada.wait(min(.25, restante)):
                        break
        finally:
            self._running = False

    def encerrar(self) -> None:
        self._running = False
        self.stop_event.set()


def criar_diretor_presenca_runtime(**kwargs: Any) -> DiretorPresencaRuntime:
    return DiretorPresencaRuntime(**kwargs)
