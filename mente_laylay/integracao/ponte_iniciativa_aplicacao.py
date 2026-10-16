"""Adaptação da iniciativa autônoma aos estados vivos da aplicação."""

from __future__ import annotations

import math
import time
from threading import RLock
from typing import Any, Callable, Mapping

from mente_laylay.autonomia.diretor_presenca import JANELA_FEEDBACK_PRESENCA_S
from mente_laylay.cognicao.interpretador_continuidade import qualificar_feedback_humor
from mente_laylay.emocoes.contrato_causal import criar_evento_feedback_comunicativo


class PonteIniciativaAplicacaoRuntime:
    """Concentra contexto, aprendizado e governança da iniciativa."""

    def __init__(
        self,
        *,
        estado_mental_getter: Callable[[], dict[str, Any]],
        percepcao_getter: Callable[[str, Any], Any],
        conversa_getter: Callable[[str, Any], Any],
        modo_jogo: Any,
        visao_leitura_getter: Callable[[], Any | None],
        identificar_jogo: Callable[[dict[str, Any]], dict[str, Any]],
        salvar_memoria: Callable[[], Any],
        falar: Callable[[str, str, int], Any],
        env_getter: Callable[[str, str], str],
        usuario_falando_getter: Callable[[], bool] | None = None,
        prioridade_interacao_getter: Callable[[], bool] | None = None,
        clock: Callable[[], float] = time.time,
        log: Callable[[str], Any] = print,
    ) -> None:
        self._estado_mental_getter = estado_mental_getter
        self._percepcao_getter = percepcao_getter
        self._conversa_getter = conversa_getter
        self._modo_jogo = modo_jogo
        self._visao_leitura_getter = visao_leitura_getter
        self._identificar_jogo = identificar_jogo
        self._salvar_memoria = salvar_memoria
        self._falar = falar
        self._env_getter = env_getter
        self._usuario_falando_getter = usuario_falando_getter or (lambda: False)
        self._prioridade_interacao_getter = (
            prioridade_interacao_getter or (lambda: False)
        )
        self._clock = clock
        self._log = log
        self._motor: Any | None = None
        self._porteiro: Any | None = None
        self._coordenador: Any | None = None
        self._rede: Any | None = None
        self._registrar_feedback_compartilhado: Callable[..., Any] | None = None
        self._publicar_evento_emocional_feedback: Callable[[dict[str, Any]], Any] | None = None
        self._lock_publicacao_feedback = RLock()

    def conectar(
        self, *, motor: Any, porteiro: Any, coordenador: Any, rede: Any,
    ) -> None:
        self._motor = motor
        self._porteiro = porteiro
        self._coordenador = coordenador
        self._rede = rede

    def conectar_usuario_falando(self, getter: Callable[[], bool]) -> None:
        if not callable(getter):
            raise ValueError("getter de fala do usuário deve ser callable")
        self._usuario_falando_getter = getter

    def conectar_aprendizado(
        self, *, registrar_feedback: Callable[..., Any],
        publicar_evento_emocional: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        """Recebe a porta compartilhada após a inicialização do motor."""
        if not callable(registrar_feedback):
            raise ValueError("registrar_feedback compartilhado deve ser callable")
        if publicar_evento_emocional is not None and not callable(publicar_evento_emocional):
            raise ValueError("publicar_evento_emocional compartilhado deve ser callable")
        self._registrar_feedback_compartilhado = registrar_feedback
        if publicar_evento_emocional is not None:
            self._publicar_evento_emocional_feedback = publicar_evento_emocional

    def _exigir_conexao(self) -> tuple[Any, Any, Any, Any]:
        if any(item is None for item in (
            self._motor, self._porteiro, self._coordenador, self._rede,
        )):
            raise RuntimeError("ponte de iniciativa ainda não foi conectada")
        return self._motor, self._porteiro, self._coordenador, self._rede

    def turno_em_andamento(self) -> bool:
        """Prioridade da conversa humana; evento não ocupa o próprio canal."""
        mental = self._estado_mental_getter()
        plano = mental.get("plano_turno_atual") or {}
        fase = (
            str(plano.get("fase") or "").strip().casefold()
            if isinstance(plano, dict) else ""
        )
        turno = mental.get("turno_atual") or {}
        evento_observado = bool(isinstance(plano, Mapping) and isinstance(turno, Mapping)
            and plano.get("id") and plano.get("id") == turno.get("id")
            and plano.get("natureza_entrada") == turno.get("natureza_entrada") == "evento"
            and plano.get("autoriza_execucao") is False and turno.get("autoriza_execucao") is False)
        return fase in {"planejado", "resposta_planejada"} and not evento_observado

    def contexto(self) -> dict[str, Any]:
        contexto_sistema = dict(self._percepcao_getter("contexto_sistema", {}) or {})
        atividade = " ".join((
            str(contexto_sistema.get("assunto") or ""),
            str(contexto_sistema.get("title") or ""),
        )).casefold()
        mental = self._estado_mental_getter()
        try:
            usuario_falando = bool(self._usuario_falando_getter())
        except Exception:
            usuario_falando = False
        try:
            interacao_usuario_ativa = bool(self._prioridade_interacao_getter())
        except Exception:
            interacao_usuario_ativa = False
        return {
            "modo_chat": bool(self._conversa_getter("modo_chat", False)),
            "conversa_ativa": bool(self._conversa_getter("conversa_ativa", False)),
            "turno_ativo": self.turno_em_andamento(),
            "modo_jogo_ativo": bool(self._modo_jogo.ativo),
            "modo_foco": any(item in atividade for item in (
                "programação", "programacao", "estudo", "trabalho focado",
            )),
            "ultima_entrada_ts": float(mental.get("ultima_entrada_ts") or 0.0),
            "ultima_fala_normal_ts": float(mental.get("ultima_fala_emitida_ts") or 0.0),
            "is_speaking": bool(self._conversa_getter("is_speaking", False)),
            "usuario_falando": usuario_falando,
            "interacao_usuario_ativa": interacao_usuario_ativa,
            "assunto": str(contexto_sistema.get("assunto") or ""),
            "titulo_janela": str(contexto_sistema.get("title") or ""),
            "musica_atual_status": str(mental.get("musica_atual_status") or ""),
        }

    def objetivos(self) -> list[dict[str, Any]]:
        if not bool(self._modo_jogo.ativo):
            return []
        leitura = self._visao_leitura_getter()
        if leitura is None:
            return []
        try:
            identidade = self._identificar_jogo(
                dict(self._modo_jogo.contexto_atual() or {})
            )
            perfil = dict(leitura.perfil_atual() or {})
        except Exception:
            return []
        tags = {"jogo", str(identidade.get("chave") or "")}
        for chave in ("classe", "build", "personagem"):
            if perfil.get(chave):
                tags.add(str(perfil[chave]))
        if len(tags) <= 2:
            return []
        return [{
            "nome": "melhorar_build_atual",
            "tags": sorted(tags),
            "prioridade": 7,
            "expira_em": self._clock() + 1800.0,
        }]

    def preparar_autonomia_segura_padrao(self) -> None:
        motor, _, _, _ = self._exigir_conexao()
        if self._env_getter("LAYLAY_AUTONOMIA_SEGURA", "1").casefold() in {
            "0", "false", "nao", "não", "off", "desligado",
        }:
            return
        resultado = motor.ativar_perfil_seguro_padrao()
        ativados = list(resultado.get("ativados") or [])
        if ativados:
            self._salvar_memoria()
            self._log(
                "🧭 [AUTONOMIA] perfil seguro ativo por padrão: "
                + ",".join(ativados)
            )

    def _publicar_feedback_emocional(self, tipo: str, proveniencia: Mapping[str, Any]) -> None:
        evento = criar_evento_feedback_comunicativo(tipo, proveniencia)
        if not evento or not callable(self._publicar_evento_emocional_feedback):
            return
        with self._lock_publicacao_feedback:
            quadro = dict(self._estado_mental_getter().get("eventos_emocionais_causais") or {})
            fontes = [quadro.get("atual"), *(quadro.get("historico") or [])]
            mesmas = [item for item in fontes if isinstance(item, Mapping)
                      and item.get("evidencia_ref") == evento["evidencia_ref"]]
            if mesmas:
                if not all(item == evento for item in mesmas):
                    self._log("⚠️ [FEEDBACK:PRESENÇA] ocorrência causal divergente")
                return
            # O publisher faz a guarda transacional entre produtores distintos;
            # este lock evita repetir o callback para a mesma ponte.
            try:
                if self._publicar_evento_emocional_feedback(evento) is False:
                    self._log("⚠️ [FEEDBACK:PRESENÇA] publicação causal rejeitada")
            except Exception as erro:
                self._log(f"⚠️ [FEEDBACK:PRESENÇA] porta causal falhou: {type(erro).__name__}")

    def _encaminhar_feedback_compartilhado(
        self, resultado: str, aceito: Any, dados: Mapping[str, Any],
    ) -> dict[str, Any]:
        evento = dados.get("evento_feedback")
        if not isinstance(evento, Mapping):
            return {"status": "sem_evento"}
        tipos = {"aceita": "aceitacao", "recusa": "recusa", "correcao": "correcao",
                 "repeticao": "repeticao", "silencio": "silencio"}
        if resultado not in tipos:
            return {"status": "rejeitado", "motivo": "tipo_feedback_invalido"}
        mental = self._estado_mental_getter()
        presenca = dict(mental.get("presenca_contextual") or {})
        emissao = dict(presenca.get("ultima_emissao") or {})
        id_entrega = str(evento.get("id_entrega") or "").strip()
        if id_entrega and str(emissao.get("id_entrega") or "").strip() != id_entrega:
            ocorrencias = [item for item in presenca.get("historico") or []
                           if str(item.get("id_entrega") or "").strip() == id_entrega]
            emissao = dict(ocorrencias[0]) if len(ocorrencias) == 1 else {}
        if (
            not id_entrega
            or id_entrega != str(evento.get("id_evento") or "").strip()
            or id_entrega != str(emissao.get("id_entrega") or "").strip()
            or evento.get("entregue") is not True
            or emissao.get("entregue") is not True
        ):
            return {"status": "rejeitado", "motivo": "entrega_nao_confirmada"}
        campos = {"dominio": "dominio", "origem_produtor": "origem", "categoria": "categoria", "alvo": "chave"}
        if any(
            str(evento.get(campo) or "").strip() != str(emissao.get(atributo) or "").strip()
            for campo, atributo in campos.items()
        ):
            return {"status": "rejeitado", "motivo": "proveniencia_divergente"}
        if emissao.get("feedback_registrado") is not True or emissao.get("feedback") != resultado:
            return {"status": "rejeitado", "motivo": "feedback_nao_observado"}
        esperado = True if resultado == "aceita" else False if resultado == "recusa" else None
        if aceito is not esperado:
            return {"status": "rejeitado", "motivo": "aceitacao_divergente"}
        try:
            entrega_ts = float(evento.get("entrega_ts") or 0.0)
            observado_ts = float(evento.get("observado_ts") or 0.0)
            ts_emissao = float(emissao.get("ts") or 0.0)
            ts_feedback = float(emissao.get("feedback_ts") or 0.0)
        except (TypeError, ValueError, OverflowError):
            return {"status": "rejeitado", "motivo": "tempo_feedback_invalido"}
        idade = observado_ts - entrega_ts
        if (
            not all(math.isfinite(valor) for valor in (entrega_ts, observado_ts, ts_emissao, ts_feedback))
            or entrega_ts <= 0.0 or entrega_ts != ts_emissao or idade < 0.0
            or observado_ts != ts_feedback
            or (resultado == "silencio" and idade < JANELA_FEEDBACK_PRESENCA_S)
            or (resultado != "silencio" and idade > JANELA_FEEDBACK_PRESENCA_S)
        ):
            return {"status": "rejeitado", "motivo": "janela_feedback_invalida"}
        proveniencia = {campo: evento.get(campo) for campo in (
            "id_entrega", "dominio", "origem_produtor", "categoria", "alvo",
            "entrega_ts", "observado_ts", "entregue",
        )}
        contexto_humor = str(emissao.get("contexto_humor") or "")
        if contexto_humor or evento.get("contexto_humor"):
            if (
                contexto_humor not in {"jogo", "conversa", "comandos"}
                or evento.get("contexto_humor") != contexto_humor
            ):
                return {"status": "rejeitado", "motivo": "contexto_entrega_divergente"}
            proveniencia["contexto_humor"] = contexto_humor
        humor = qualificar_feedback_humor(str(dados.get("texto_feedback") or ""))
        if humor and contexto_humor and humor["tipo"] == tipos[resultado]:
            proveniencia["feedback_humor"] = humor
            proveniencia["canal_entrega"] = str(emissao.get("canal_entrega") or "")
        elif (resultado == "silencio" and contexto_humor
              and emissao.get("solicitacao_feedback_humor") is True):
            proveniencia["solicitacao_feedback_humor"] = True
            proveniencia["texto_solicitacao_humor"] = str(emissao.get("fala") or "")
            proveniencia["feedback_humor"] = {
                "alvo_feedback": "humor", "tipo": "silencio", "direcao": "neutro",
                "evidencia_literal": "silencio",
            }
        self._publicar_feedback_emocional(tipos[resultado], proveniencia)
        if not callable(self._registrar_feedback_compartilhado):
            return {"status": "indisponivel", "id_evento": id_entrega}
        try:
            registro = self._registrar_feedback_compartilhado(
                tipo=tipos[resultado], aceito=esperado,
                resultado=str(dados.get("texto_feedback") or resultado),
                origem="presenca", alvo=str(evento.get("alvo") or ""),
                id_evento=id_entrega, proveniencia=proveniencia,
            )
        except Exception as erro:
            self._log(f"⚠️ [APRENDIZADO:PRESENÇA] porta falhou: {type(erro).__name__}")
            return {"status": "falha", "id_evento": id_entrega, "erro": type(erro).__name__}
        if not isinstance(registro, Mapping) or not str(registro.get("chave") or "").strip():
            return {"status": "sem_persistencia", "id_evento": id_entrega}
        return {"status": "registrado", "id_evento": id_entrega, "chave": str(registro["chave"])}

    def registrar_feedback(self, tipo: Any, aceito: Any = None, **dados: Any) -> dict[str, Any]:
        _, porteiro, coordenador, rede = self._exigir_conexao()
        resultado = str(dados.get("resultado") or "").strip().casefold()
        perfil_intervalo = {}
        if aceito is not None and resultado != "silencio":
            perfil_intervalo = porteiro.registrar_feedback(
                tipo, bool(aceito),
                comando=str(dados.get("comando") or ""),
                payload=dict(dados.get("payload") or {}),
            )
        perfil_contextual = coordenador.registrar_feedback(
            tipo, aceito,
            resultado=resultado,
            comando=str(dados.get("comando") or ""),
            payload=dict(dados.get("payload") or {}),
        )
        if perfil_contextual:
            resultado_rede = (
                resultado
                if resultado in {"aceita", "recusa", "silencio", "correcao"}
                else "aceita" if aceito is True
                else "recusa" if aceito is False
                else ""
            )
            if resultado_rede:
                try:
                    rede.observar_feedback(
                        categoria=str(tipo or ""), resultado=resultado_rede,
                    )
                except Exception as erro:
                    self._log(
                        "⚠️ [REDE ASSOCIATIVA] feedback isolado: "
                        f"{type(erro).__name__}"
                    )
            self._salvar_memoria()
        resultado_compartilhado = self._encaminhar_feedback_compartilhado(resultado, aceito, dados)
        return {
            "intervalo": perfil_intervalo, "contexto": perfil_contextual,
            "aprendizado_compartilhado": resultado_compartilhado,
        }

    def preparar_sugestoes_jogo(self) -> None:
        motor, _, _, _ = self._exigir_conexao()
        if self._env_getter("LAYLAY_JOGO_PROATIVO", "1").casefold() in {
            "0", "false", "nao", "não", "off", "desligado",
        }:
            return
        estado = motor.snapshot()
        if "jogo" in dict(estado.get("permissoes") or {}):
            return
        motor.configurar_dominio("jogo", "sugestao", confirmacao_explicita=True)
        self._salvar_memoria()

    def processar_governanca(self, pedido: dict[str, Any]) -> bool:
        motor, _, _, _ = self._exigir_conexao()
        dados = dict(pedido or {})
        if dados.get("acao") == "desfazer":
            resultado = motor.desfazer_ultima(confirmacao_explicita=True)
            if resultado.get("ok"):
                fala = "Desfiz minha última ação autônoma e confirmei a restauração."
            else:
                fala = {
                    "nenhuma_acao_autonoma_reversivel": "Não tenho uma ação autônoma recente para desfazer.",
                    "prazo_para_desfazer_expirou": "A janela segura para desfazer essa ação já passou.",
                }.get(
                    str(resultado.get("motivo") or ""),
                    "Não consegui desfazer essa ação com confirmação segura.",
                )
            self._falar(fala, "calma", 1)
            return True
        if dados.get("acao") == "status":
            dominios = dict(motor.permissoes_atuais().get("dominios") or {})
            if not dominios:
                fala = (
                    "Minha autonomia continua em observação, sem nenhum domínio "
                    "liberado. Você pode permitir sugestões de um domínio específico "
                    "quando quiser."
                )
            else:
                nomes = {
                    "bloqueado": "bloqueado",
                    "sugestao": "somente sugestões",
                    "acao_reversivel": "ações reversíveis autorizadas",
                }
                fala = "Minhas permissões atuais são: " + ", ".join(
                    f"{dominio}: {nomes.get(nivel, nivel)}"
                    for dominio, nivel in dominios.items()
                ) + "."
            self._falar(fala, "calma", 1)
            return True
        if dados.get("acao") == "configurar_perfil":
            resultado = motor.configurar_perfil_seguro(
                str(dados.get("permissao") or ""), confirmacao_explicita=True,
            )
            if not resultado.get("ok"):
                self._falar(
                    "Não consegui aplicar o perfil seguro sem enfraquecer as proteções.",
                    "calma", 1,
                )
                return True
            if resultado.get("permissao") == "bloqueado":
                fala = (
                    "Certo. Desativei a autonomia segura de luz, música e conforto. "
                    "Não vou agir sozinha nesses domínios."
                )
            else:
                fala = (
                    "Autonomia segura ativada. Posso cuidar de luz, música e conforto "
                    "quando a necessidade estiver clara e a confiança passar de noventa "
                    "por cento. Ações arriscadas continuam bloqueadas, e você pode pedir "
                    "para eu desfazer."
                )
            self._falar(fala, "calma", 1)
            self._salvar_memoria()
            return True
        resultado = motor.configurar_dominio(
            str(dados.get("dominio") or ""),
            str(dados.get("permissao") or ""),
            confirmacao_explicita=True,
        )
        if not resultado.get("ok"):
            self._falar(
                "Não consegui aplicar essa permissão com segurança. Me diga o domínio "
                "e o nível desejado.",
                "calma", 1,
            )
            return True
        dominio = str(resultado.get("dominio") or "esse domínio")
        permissao = str(resultado.get("permissao") or "bloqueado")
        falas = {
            "bloqueado": f"Certo. A autonomia de {dominio} ficou bloqueada.",
            "sugestao": f"Certo. Em {dominio}, posso sugerir, mas não agir sozinha.",
            "acao_reversivel": (
                f"Registrei sua autorização para ações reversíveis em {dominio}. "
                "Ações arriscadas continuam bloqueadas."
            ),
        }
        self._falar(falas[permissao], "calma", 1)
        self._salvar_memoria()
        return True


def criar_ponte_iniciativa_aplicacao_runtime(
    **kwargs: Any,
) -> PonteIniciativaAplicacaoRuntime:
    return PonteIniciativaAplicacaoRuntime(**kwargs)
