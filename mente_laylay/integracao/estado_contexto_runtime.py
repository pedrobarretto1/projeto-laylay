"""Integra estado vivo, percepção e memória curta da Laylay."""

from __future__ import annotations

from datetime import datetime
import time
from typing import Any, Callable, Dict

from mente_laylay.integracao.contexto_conversa import (
    montar_contexto_conversa_natural,
    montar_contexto_gate_conversa,
)
from mente_laylay.autonomia.roteador_intencao import bloquear_por_emocao
from mente_laylay.autonomia.porteiro_acoes import (
    texto_conversa_casual_sem_acao,
    texto_conversa_contextual_sem_comando,
    texto_parece_pergunta_factual,
)
from mente_laylay.personalidade.ajuste_contextual import ajustar_fala_por_horario
from mente_laylay.cognicao.decisao_turno import consolidar_arbitragem
from mente_laylay.memoria_mental.contexto_compartilhado import (
    alvo_corrigido_ativo,
    atualizar_foco_vivo,
    enriquecer_resultado_execucao_contextual,
    extrair_refino_contexto_mental,
    foco_vivo_atual,
    estrutura_arquivo_recente,
    limpar_pergunta_aberta,
    limpar_oferta_pendente,
    limpar_promessa_conversacional,
    pergunta_aberta_ativa,
    oferta_pendente_ativa,
    promessa_conversacional_ativa,
    registrar_alvo_corrigido,
    registrar_estrutura_arquivo_recente,
    registrar_mente_curta,
    registrar_pergunta_aberta,
    registrar_promessa_conversacional,
    registrar_resultado_execucao,
    resolver_repeticao_ultima_acao,
    texto_parece_pergunta_aberta,
)
from mente_laylay.memoria_mental.continuidade_conversa import (
    resolver_pergunta_curta_contextual_intencao,
    responder_pergunta_aberta,
    texto_responde_pergunta_aberta,
)
from mente_laylay.memoria_mental.autoaprimoramento import (
    registrar_autoaprimoramento,
    resumo_autoaprimoramento_para_prompt,
)
from mente_laylay.memoria_mental.contexto_integrado import (
    contexto_aponta_descanso,
    interpretar_contexto_vivo,
    montar_contexto_perceptivo,
    montar_resumo_mente_integrada_com_extras,
)
from mente_laylay.personalidade.fala_proativa import compor_fala_proativa
from mente_laylay.percepcao.conteudo_atual import perceber_conteudo_atual
from mente_laylay.percepcao.ritmo_circadiano import construir_contexto_temporal
from mente_laylay.emocoes.motor_humor import (
    ajustar_humor as ajustar_humor_estado,
    montar_status_humor_prompt,
)
from mente_laylay.emocoes.leitura_usuario import registrar_leitura_emocional
from mente_laylay.memoria_mental.consciencia_temporal import atualizar_consciencia_temporal
from mente_laylay.memoria_mental.ciclo_vida_contexto import aplicar_ciclo_vida_contexto
from mente_laylay.memoria_mental.sessao_conversa import renovar_contexto_sessao
from mente_laylay.memoria_mental.pendencia import limpar_pendencia, pendencia_ativa


class EstadoContextoRuntime:
    """Coordena retratos e registros usando uma única fonte de estado vivo."""

    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        estado_runtime_getter: Callable[[], Any],
    ) -> None:
        self.namespace_getter = namespace_getter
        self.estado_runtime_getter = estado_runtime_getter

    def _namespace(self) -> Dict[str, Any]:
        return self.namespace_getter() or {}

    def _estado(self) -> Any:
        return self.estado_runtime_getter()

    def renovar_sessao_conversa(self, motivo: str = "nova_sessao", ativa: bool = True) -> None:
        estado = self._estado()
        mental, conversa, mensagens = renovar_contexto_sessao(
            estado.mental,
            estado.conversacional,
            list(estado.memoria_conversa.get("messages", []) or []),
            motivo=motivo,
            ativa=ativa,
        )
        estado.substituir("mental", mental)
        estado.substituir("conversacional", conversa)
        memoria = dict(estado.memoria_conversa)
        memoria["messages"] = mensagens
        estado.substituir("memoria_conversa", memoria)
        print(f"🧹 [SESSÃO] contexto transitório renovado | motivo={motivo} | ativa={ativa}")

    def contexto_conversa_natural(self) -> Dict[str, Any]:
        ns = self._namespace()
        estado = self._estado()
        conversa_get = ns.get("_conversa_estado_get")

        def conversa(chave: str, padrao: Any) -> Any:
            return conversa_get(chave, padrao) if callable(conversa_get) else padrao

        contexto_perceptivo = self.contexto_perceptivo()
        modo_jogo_runtime = ns.get("_modo_jogo_runtime")
        if modo_jogo_runtime is not None and hasattr(modo_jogo_runtime, "contexto_atual"):
            try:
                contexto_perceptivo["jogo"] = dict(modo_jogo_runtime.contexto_atual() or {})
            except Exception:
                pass
        return montar_contexto_conversa_natural(
            current_emotion=conversa("current_emotion", "calma"),
            mente_integrada_estado=estado.mental,
            ultimo_topico_conversa=conversa("ultimo_topico_conversa", ""),
            # Conversa consulta seu próprio foco; ações antigas continuam
            # disponíveis no foco operacional sem contaminar este retrato.
            foco_vivo=self.foco_conversacional_atual(),
            obter_conteudo_atual=self.conteudo_atual,
            pesquisar_contexto_tema=ns["_pesquisa_contextual_runtime"].pesquisar_contexto_tema,
            normalizar_texto_curto=ns["_normalizar_texto_curto"],
            normalizar_texto_com_apelidos=ns["_normalizar_texto_com_apelidos"],
            resumo_mente_integrada_para_prompt=ns["_resumo_mente_integrada_para_prompt"],
            enviar_mensagem=ns["enviar_mensagem"],
            extrair_json_da_ia=ns["_extrair_json_da_ia"],
            ajustar_fala_por_horario=self.ajustar_fala_por_horario,
            fala_de_confirmacao_variada=ns["_fala_de_confirmacao_variada"],
            texto_parece_navegacao_ou_janela_ia=self.texto_parece_navegacao_ou_janela_ia,
            fala_e_fallback_neutro=ns["_fala_e_fallback_neutro"],
            ajustar_tom_por_emocao=ns["_ajustar_tom_por_emocao"],
            contexto_perceptivo=contexto_perceptivo,
            registrar_leitura_emocional_usuario=self.registrar_leitura_emocional_usuario,
            acalmar_emocao=ns["_acalmar_emocao_conversacional"],
            definir_emocao=ns["_definir_emocao_conversacional"],
            voz_unica_llm=True,
        )

    def conteudo_atual(self, texto_usuario: str = "") -> Dict[str, Any]:
        ns = self._namespace()
        paginas = ns.get("_contexto_paginas")
        pagina_lida = paginas.atual() if paginas is not None and hasattr(paginas, "atual") else {}
        percepcao_get = ns.get("_percepcao_get")
        aba = percepcao_get("aba_ativa", {}) if callable(percepcao_get) else {}
        snapshot_pagina = percepcao_get("pagina_ativa", {}) if callable(percepcao_get) else {}
        pagina = {}
        titulo_aba = str((aba or {}).get("titulo") or (aba or {}).get("title") or "").strip()
        url_aba = str((aba or {}).get("url") or "").strip()
        if titulo_aba:
            pagina = {"title": titulo_aba, "url": url_aba, "ts": datetime.now().timestamp()}
            mesmo_url = bool(url_aba and url_aba == str(pagina_lida.get("url") or "").strip())
            mesmo_titulo = bool(
                titulo_aba.casefold() == str(pagina_lida.get("title") or "").strip().casefold()
            )
            if mesmo_url or mesmo_titulo:
                pagina.update(pagina_lida)
                pagina["title"] = titulo_aba
                pagina["url"] = url_aba or str(pagina_lida.get("url") or "")
        elif pagina_lida:
            pagina = pagina_lida
        if isinstance(snapshot_pagina, dict) and snapshot_pagina:
            snapshot_url = str(snapshot_pagina.get("url") or "").strip()
            snapshot_titulo = str(snapshot_pagina.get("title") or "").strip()
            corresponde = bool(
                (snapshot_url and snapshot_url == str(pagina.get("url") or url_aba).strip())
                or (snapshot_titulo and snapshot_titulo.casefold() == str(pagina.get("title") or titulo_aba).strip().casefold())
            )
            if corresponde or not pagina:
                pagina["url"] = snapshot_url or str(pagina.get("url") or "")
                pagina["title"] = snapshot_titulo or str(pagina.get("title") or "")
                pagina["ts"] = float(snapshot_pagina.get("ts") or datetime.now().timestamp()) / (
                    1000.0 if float(snapshot_pagina.get("ts") or 0.0) > 10_000_000_000 else 1.0
                )
                if not str(pagina.get("content") or "").strip():
                    headings = [str(x).strip() for x in (snapshot_pagina.get("headings") or []) if str(x).strip()]
                    controles = []
                    for item in snapshot_pagina.get("elements") or []:
                        if not isinstance(item, dict):
                            continue
                        label = str(item.get("label") or "").strip()
                        if label:
                            controles.append(f"{item.get('id') or '?'}:{label}")
                    pagina["content"] = (
                        f"tipo={snapshot_pagina.get('kind') or 'geral'}; "
                        f"titulos={', '.join(headings[:8]) or '-'}; "
                        f"controles={', '.join(controles[:20]) or '-'}"
                    )
        retrato = perceber_conteudo_atual(
            texto_usuario=texto_usuario,
            mente=self._estado().mental,
            contexto_perceptivo=self.contexto_perceptivo(),
            pagina=pagina,
        )
        self._estado().atualizar_campos("mental", conteudo_atual=dict(retrato or {}))
        return retrato

    def registrar_leitura_emocional_usuario(self, leitura: Dict[str, Any]) -> None:
        try:
            estado = self._estado()
            estado.substituir(
                "mental",
                registrar_leitura_emocional(estado.mental, leitura),
            )
        except Exception:
            return

    def contexto_gate_conversa(self) -> Dict[str, Any]:
        ns = self._namespace()
        conversa_get = ns.get("_conversa_estado_get")
        ultimo_topico = conversa_get("ultimo_topico_conversa", "") if callable(conversa_get) else ""
        return montar_contexto_gate_conversa(
            mente_integrada_estado=self._estado().mental,
            foco_vivo=self.foco_vivo_atual(),
            obter_conteudo_atual=self.conteudo_atual,
            ultimo_topico_conversa=ultimo_topico,
        )

    def texto_conversa_contextual_sem_comando(self, texto: str) -> bool:
        return texto_conversa_contextual_sem_comando(texto, self.contexto_gate_conversa())

    def texto_conversa_casual_sem_acao(self, texto: str) -> bool:
        ns = self._namespace()
        if texto_parece_pergunta_factual(texto):
            return False
        if ns["_texto_tem_comando_explicito"](texto):
            return False
        if ns["_texto_expresso_melhor_no_deterministico"](texto):
            return False
        if self.texto_conversa_contextual_sem_comando(texto):
            return True
        return texto_conversa_casual_sem_acao(texto)

    def texto_parece_navegacao_ou_janela_ia(self, texto: str) -> bool:
        t = self._namespace()["_normalizar_texto_com_apelidos"](texto)
        if not t:
            return False
        verbos = (
            "abre", "abrir", "abra", "entra", "entrar", "vai para", "vai pro",
            "fecha", "fechar", "mata", "derruba", "encerra", "encerrar",
            "maximiza", "maximizar", "tela cheia", "fullscreen", "em foco", "foco",
            "traz", "trazer", "puxa pra frente", "para frente",
        )
        alvos = (
            "site", "aba", "janela", "programa", "app", "aplicativo", "opera",
            "chrome", "steam", "spotify", "netflix", "youtube", "instagram",
            "whatsapp", "explorador", "microsoft store",
        )
        return any(verbo in t for verbo in verbos) and any(alvo in t for alvo in alvos)

    def texto_indica_autocorrecao(self, texto: str) -> bool:
        t = self._namespace()["_normalizar_texto"](texto)
        if not t:
            return False
        gatilhos = (
            "corrigindo", "na verdade", "me enganei", "errei", "ops",
            "deixa eu corrigir", "deixa corrigir", "vou corrigir",
            "retificando", "ajustando a resposta",
        )
        return any(gatilho in t for gatilho in gatilhos)

    def ajustar_fala_por_horario(self, fala: str, texto_usuario: str = "") -> str:
        ns = self._namespace()
        return ajustar_fala_por_horario(
            fala,
            texto_usuario,
            obter_contexto_perceptivo=self.contexto_perceptivo,
            interpretar_contexto_vivo=self.interpretar_contexto_vivo,
            escolher_fala=ns["_escolher_fala_variada"],
        )

    def ajustar_humor(self, delta: int, motivo: str = "desconhecido") -> int:
        ns = self._namespace()
        conversa_get = ns["_conversa_estado_get"]
        contexto = {
            "humor_level": conversa_get("humor_level", 0),
            "humor_last_update": conversa_get("humor_last_update", 0.0),
            "humor_history": conversa_get("humor_history", []),
        }
        novo = ajustar_humor_estado(contexto, delta, motivo)
        self._estado().atualizar_campos(
            "conversacional",
            humor_level=contexto.get("humor_level", novo),
            humor_last_update=contexto.get("humor_last_update", 0.0),
            humor_history=contexto.get("humor_history", []),
        )
        return novo

    def status_humor_prompt(self) -> str:
        ns = self._namespace()
        conversa_get = ns["_conversa_estado_get"]
        ctx = self.contexto_perceptivo()
        percepcao = self.interpretar_contexto_vivo(ctx)
        return montar_status_humor_prompt(
            ctx,
            percepcao,
            humor_fallback=conversa_get("humor_level", 0),
            emocao_fallback=conversa_get("current_emotion", "calma"),
            periodo_fallback=ns["_contexto_horario_atual"](),
            descricao_emocao_cb=ns["_descricao_emocao_mente"],
            perfil_comportamento_cb=ns["_perfil_comportamento_emocional_mente"],
        )

    def contexto_perceptivo(self) -> Dict[str, Any]:
        ns = self._namespace()
        agora = datetime.now()
        ritmo_runtime = ns.get("_ritmo_circadiano_runtime")
        try:
            ritmo_temporal = dict(ritmo_runtime.contexto_atual()) if ritmo_runtime is not None else {}
        except Exception:
            ritmo_temporal = {}
        if not ritmo_temporal:
            ritmo_temporal = construir_contexto_temporal(agora)
        hora_chave = agora.strftime("%H:00")
        rotina_atual: Dict[str, Any] = {}
        try:
            rotina_atual = dict(
                ns["_estado_aprendizado_atual"]()
                .get("rotina_dados_diarios", {})
                .get(hora_chave)
                or {}
            )
        except Exception:
            rotina_atual = {}

        conversa_get = ns.get("_conversa_estado_get")
        percepcao_get = ns.get("_percepcao_get")

        def conversa(chave: str, padrao: Any) -> Any:
            return conversa_get(chave, padrao) if callable(conversa_get) else padrao

        contexto_sistema = (
            percepcao_get("contexto_sistema", {}) if callable(percepcao_get) else {}
        )
        contexto = montar_contexto_perceptivo(
            periodo=str(ritmo_temporal.get("periodo") or ns["_contexto_horario_atual"]()),
            agora=agora,
            contexto_sistema=contexto_sistema,
            logs_navegador=(
                ns["_estado_compartilhado_runtime"].obter_copia(
                    "percepcao", "logs_navegador", []
                )
                if ns.get("_estado_compartilhado_runtime") is not None
                else []
            ),
            current_emotion=conversa("current_emotion", "calma"),
            emotion_level=conversa("emotion_level", 1),
            humor_level=conversa("humor_level", 0),
            ultimo_topico_conversa=conversa("ultimo_topico_conversa", ""),
            topicos_conversa_recente=conversa("topicos_conversa_recente", []),
            rotina_atual=rotina_atual,
        )
        contexto["emocao_causa"] = conversa("emotion_cause", "")
        contexto["emocao_interacoes_restantes"] = conversa("emotion_interactions_left", 0)
        contexto["emocao_inicio"] = conversa("emotion_started_at", 0.0)
        contexto["emocao_duracao_s"] = conversa("emotion_duration_s", 0.0)
        contexto["ritmo_temporal"] = {
            chave: valor for chave, valor in ritmo_temporal.items() if chave != "agora"
        }
        return contexto

    @staticmethod
    def contexto_horario_atual() -> str:
        return str(construir_contexto_temporal(datetime.now()).get("periodo") or "")

    def interpretar_contexto_vivo(
        self,
        ctx: Dict[str, Any] | None = None,
        texto_extra: str = "",
    ) -> Dict[str, Any]:
        ns = self._namespace()
        contexto = ctx if isinstance(ctx, dict) else self.contexto_perceptivo()
        return interpretar_contexto_vivo(
            contexto,
            texto_extra,
            normalizar_cb=ns["_normalizar_texto_com_apelidos"],
        )

    def resumo_autoaprimoramento_para_prompt(self, limit: int = 4) -> str:
        try:
            estado = self._estado().obter("mental", "autoaprimoramento_estado", {})
            return resumo_autoaprimoramento_para_prompt(estado, limit=limit)
        except Exception:
            return "Autoaprimoramento: indisponível."

    def resumo_mente_integrada_para_prompt(self, texto_usuario: str = "") -> str:
        ns = self._namespace()
        ctx = self.contexto_perceptivo()
        rede = ns.get("_rede_associativa_runtime")
        if rede is not None:
            try:
                sinais = rede.sinais_continuidade()
                if sinais:
                    ctx["associacoes_continuidade"] = sinais
                    ctx["registrar_influencia_associativa"] = (
                        rede.registrar_influencia_continuidade
                    )
            except Exception as erro:
                ns["print"](
                    "⚠️ [REDE ASSOCIATIVA] pista de continuidade isolada: "
                    f"{type(erro).__name__}"
                )
        percepcao = self.interpretar_contexto_vivo(ctx, texto_usuario)
        ctx["conteudo_atual"] = self.conteudo_atual(texto_usuario)
        resumo = montar_resumo_mente_integrada_com_extras(
            texto_usuario=texto_usuario,
            ctx=ctx,
            percepcao=percepcao,
            mente=self._estado().mental,
            resumo_autoaprimoramento_cb=self.resumo_autoaprimoramento_para_prompt,
            memoria_sqlite=ns.get("MEMORIA_SQLITE"),
        )
        return resumo

    def registrar_autoaprimoramento(
        self,
        resultado: Dict[str, Any] | None = None,
        texto: str = "",
        sucesso: bool = True,
        erro: str = "",
        contexto: str = "",
        origem: str = "",
    ) -> None:
        estado = self._estado()
        estado_atualizado = registrar_autoaprimoramento(
            estado.obter("mental", "autoaprimoramento_estado", {}),
            resultado=resultado,
            texto=texto,
            sucesso=sucesso,
            erro=erro,
            contexto=contexto,
            origem=origem,
        )
        estado.atualizar_campos(
            "mental", autoaprimoramento_estado=estado_atualizado
        )

    def refinar_contexto_mental(
        self,
        texto: str,
        resultado: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Refina o turno e devolve o evento temporal produzido nessa atualização."""
        estado_runtime = self._estado()
        try:
            ultima_entrada_ts = float(estado_runtime.mental.get("ultima_entrada_ts") or 0.0)
        except (TypeError, ValueError):
            ultima_entrada_ts = 0.0
        if ultima_entrada_ts and time.time() - ultima_entrada_ts > 600.0:
            self.renovar_sessao_conversa("inatividade", ativa=True)
            estado_runtime = self._estado()
        contexto_vigente = aplicar_ciclo_vida_contexto(estado_runtime.mental)
        estado_runtime.substituir("mental", contexto_vigente)
        expirados = list(contexto_vigente.get("contextos_expirados_ultimo_ciclo") or [])
        if expirados:
            print(f"🧹 [CONTEXTO:EXPIRADO] {', '.join(expirados)}")
        avancar_emocao = self._namespace().get("_avancar_emocao_conversacional")
        if callable(avancar_emocao):
            avancar_emocao(consumir_interacao=True, interaction_key=texto)
        dados = extrair_refino_contexto_mental(texto, resultado)
        if not dados.get("texto"):
            return self.registrar_interacao_temporal(texto)
        self.registrar_mente_curta(
            dados.get("texto", ""),
            "",
            dados.get("intencao", ""),
            dados.get("alvo", ""),
            dados.get("escopo", ""),
            dados.get("habilidade", ""),
        )
        consciencia = estado_runtime.mental.get("consciencia_temporal") or {}
        return dict(consciencia.get("evento_turno") or {})

    def contexto_aponta_descanso(self, texto_extra: str = "") -> bool:
        ctx = self.contexto_perceptivo()
        percepcao = self.interpretar_contexto_vivo(ctx, texto_extra)
        return contexto_aponta_descanso(ctx, percepcao, texto_extra)

    def atualizar_foco_vivo(
        self,
        estado: Dict[str, Any],
        *,
        texto: str = "",
        resposta: str = "",
        intencao: str = "",
        alvo: str = "",
        habilidade: str = "",
        escopo: str = "",
    ) -> Dict[str, Any]:
        return atualizar_foco_vivo(
            estado,
            texto=texto,
            resposta=resposta,
            intencao=intencao,
            alvo=alvo,
            habilidade=habilidade,
            escopo=escopo,
            normalizar_texto_cb=self._namespace()[
                "_normalizar_texto_com_apelidos"
            ],
        )

    def foco_vivo_atual(self, ttl_s: float = 480.0) -> Dict[str, Any]:
        return foco_vivo_atual(self._estado().mental, ttl_s=ttl_s)

    def foco_conversacional_atual(self, ttl_s: float = 480.0) -> Dict[str, Any]:
        return foco_vivo_atual(
            self._estado().mental,
            ttl_s=ttl_s,
            dominio="conversacional",
        )

    def foco_operacional_atual(self, ttl_s: float = 480.0) -> Dict[str, Any]:
        return foco_vivo_atual(
            self._estado().mental,
            ttl_s=ttl_s,
            dominio="operacional",
        )

    def resolver_repeticao_ultima_acao(
        self,
        texto: str,
    ) -> Dict[str, Any] | None:
        return resolver_repeticao_ultima_acao(
            texto,
            self._estado().mental,
            self._namespace()["_normalizar_texto_com_apelidos"],
        )

    def pergunta_aberta_atual(self) -> Dict[str, Any] | None:
        try:
            mente = self._estado().mental
            pergunta = pergunta_aberta_ativa(mente, ttl_s=120.0)
            if pergunta:
                return pergunta
            pendencia = pendencia_ativa(mente, dominio="conversa")
            if not pendencia or pendencia.get("origem") != "pergunta_aberta":
                return None
            return {
                "pergunta": str(pendencia.get("conteudo") or ""),
                "tipo": str(pendencia.get("tipo") or "resposta_curta"),
                "proposito": str(pendencia.get("tipo") or ""),
                "resposta_esperada": str(pendencia.get("resposta_esperada") or ""),
                "topico": "",
            }
        except Exception:
            return None

    def limpar_pergunta_aberta(self) -> None:
        try:
            estado = self._estado()
            estado.substituir("mental", limpar_pergunta_aberta(estado.mental))
        except Exception:
            return

    def registrar_alvo_corrigido(self, alvo: str) -> None:
        try:
            estado = self._estado()
            estado.substituir("mental", registrar_alvo_corrigido(estado.mental, alvo))
        except Exception:
            return

    def alvo_corrigido_atual(self) -> str:
        try:
            return str(
                alvo_corrigido_ativo(self._estado().mental, ttl_s=120.0) or ""
            ).strip()
        except Exception:
            return ""

    def registrar_estrutura_arquivo_recente(
        self,
        params: Dict[str, Any] | None,
    ) -> None:
        try:
            estado = self._estado()
            estado.substituir(
                "mental",
                registrar_estrutura_arquivo_recente(estado.mental, params),
            )
        except Exception:
            return

    def estrutura_arquivo_recente(
        self,
        ttl_s: float = 900.0,
    ) -> Dict[str, Any] | None:
        try:
            return estrutura_arquivo_recente(self._estado().mental, ttl_s=ttl_s)
        except Exception:
            return None

    def texto_responde_pergunta_aberta(self, texto_usuario: str) -> bool:
        ns = self._namespace()
        return texto_responde_pergunta_aberta(
            texto_usuario,
            pergunta_aberta=self.pergunta_aberta_atual(),
            normalizar_texto_curto=ns["_normalizar_texto_curto"],
            texto_parece_resposta_curta_a_pergunta=ns[
                "_texto_parece_resposta_curta_a_pergunta_mente"
            ],
            bloqueadores=[
                ns["_resolver_pergunta_curta_contextual_intencao"],
                lambda texto: ns["detectar_intencao_deterministica"](texto),
                lambda texto: ns["interpretar_comando_local_rapido"](
                    ns["_normalizar_texto_com_apelidos"](texto)
                ),
                ns["_resolver_comando_midia_contextual_forcado"],
                ns["_resolver_comando_janela_contextual_forcado"],
            ],
        )

    def responder_pergunta_aberta(self, texto_usuario: str) -> str:
        ns = self._namespace()
        pergunta = self.pergunta_aberta_atual() or {}
        promessa = promessa_conversacional_ativa(self._estado().mental, ttl_s=180.0)
        self.limpar_pergunta_aberta()
        texto_norm = str(ns["_normalizar_texto_curto"](texto_usuario) or "").strip()
        confirmou = bool(
            promessa
            and (
                any(
                    sinal in texto_norm.split()
                    for sinal in ("sim", "pode", "quero", "claro", "bora", "manda", "vai")
                )
                or texto_norm in {"isso", "isso mesmo", "pode ser", "aham", "uhum", "fechado"}
            )
        )
        if confirmou:
            estado = self._estado()
            estado.substituir("mental", limpar_promessa_conversacional(estado.mental))
            tipo = str(promessa.get("tipo") or "").strip()
            alvo = str(promessa.get("alvo") or pergunta.get("topico") or "").strip()
            conteudo = str(promessa.get("conteudo") or "").strip()
            if tipo == "explicar_opiniao" and alvo:
                responder_tipo = ns.get("_responder_conversa_curta_por_tipo")
                if callable(responder_tipo):
                    fala = str(responder_tipo("OPINION", f"me explique melhor sua opinião sobre {alvo}") or "").strip()
                    if fala:
                        return fala
            if conteudo:
                return f"Claro. O ponto que eu queria abrir melhor é este: {conteudo}"
            if alvo:
                return f"Claro. Eu estava falando de {alvo}; vou explicar isso sem trocar de assunto."
        return responder_pergunta_aberta(
            texto_usuario,
            pergunta_aberta=pergunta,
            foco_vivo=ns["_foco_vivo_atual"](),
            normalizar_texto_curto=ns["_normalizar_texto_curto"],
            responder_conversa_curta_por_tipo=ns[
                "_responder_conversa_curta_por_tipo"
            ],
            ajustar_fala_por_horario=ns["_ajustar_fala_por_horario"],
        )

    def resolver_pergunta_curta_contextual_intencao(
        self,
        texto_usuario: str,
    ) -> Dict[str, Any] | None:
        ns = self._namespace()
        mente = self._estado().mental
        pendencia = pendencia_ativa(mente, dominio="musica")
        oferta = oferta_pendente_ativa(mente, ttl_s=300.0)
        texto_norm = str(ns["_normalizar_texto_curto"](texto_usuario) or "").strip()
        if (
            pendencia
            and str(pendencia.get("tipo") or "") == "esclarecimento"
            and str(pendencia.get("intencao") or "") == "MUSIC_SEARCH"
        ):
            cancelamentos = {
                "cancela", "cancelar", "deixa", "deixa pra la", "deixa para la",
                "nao quero", "não quero", "esquece",
            }
            if texto_norm in cancelamentos:
                estado = self._estado()
                estado.substituir(
                    "mental",
                    limpar_pendencia(estado.mental, motivo="cancelada"),
                )
                return None
            if texto_norm and len(texto_norm.split()) <= 16:
                estado = self._estado()
                estado.substituir(
                    "mental",
                    limpar_pendencia(estado.mental, motivo="respondida"),
                )
                return {
                    "intent": "MUSIC_SEARCH",
                    "params": {
                        "query": str(texto_usuario or "").strip(),
                        "origem": "continuacao_busca",
                    },
                }
        if pendencia and str(pendencia.get("intencao") or "") == "MUSIC_SEARCH":
            oferta_unificada = {
                "intent": "MUSIC_SEARCH",
                "opcoes": list(pendencia.get("opcoes") or []),
                "resposta_esperada": str(pendencia.get("resposta_esperada") or ""),
            }
            # A pendência unificada é a fonte mais nova; a estrutura legada
            # permanece apenas como compatibilidade durante a migração.
            oferta = oferta_unificada
        if oferta:
            opcoes = list(oferta.get("opcoes") or [])
            confirma = bool(
                set(texto_norm.split()).intersection({"sim", "quero", "pode", "bora", "manda", "vai"})
                or texto_norm in {"isso", "essa", "esse", "pode ser", "fechado"}
            )
            escolhida = None
            if len(opcoes) == 1 and confirma:
                escolhida = opcoes[0]
            elif opcoes:
                if any(p in texto_norm for p in ("primeira", "primeiro", "a primeira", "o primeiro")):
                    escolhida = opcoes[0]
                elif len(opcoes) > 1 and any(p in texto_norm for p in ("segunda", "segundo", "a segunda", "o segundo")):
                    escolhida = opcoes[1]
                else:
                    for opcao in opcoes:
                        rotulo = str(opcao.get("rotulo") or "").casefold()
                        if rotulo and rotulo in texto_norm.casefold():
                            escolhida = opcao
                            break
            if escolhida:
                estado = self._estado()
                estado.substituir("mental", limpar_oferta_pendente(estado.mental))
                return {
                    "intent": str(oferta.get("intent")),
                    "params": dict(escolhida.get("params") or {}),
                }
        return resolver_pergunta_curta_contextual_intencao(
            texto_usuario,
            normalizar_texto_curto=ns["_normalizar_texto_curto"],
            contexto_recente_indica_email=ns["_contexto_recente_indica_email"],
        )

    def atualizar_contexto_sistema_monitor(self, retrato: Dict[str, Any]) -> None:
        retrato = dict(retrato or {})
        self._namespace()["_percepcao_set"]("contexto_sistema", {
            "exe": str(retrato.get("exe") or ""),
            "title": str(retrato.get("title") or ""),
            "assunto": str(retrato.get("assunto") or ""),
        })

    def definir_ultimo_proativo_ts(self, valor: float) -> None:
        self._namespace()["_percepcao_set"]("ultimo_proativo_ts", float(valor or 0.0))

    def compor_fala_proativa(self, itens: list) -> tuple[str, str, int]:
        ns = self._namespace()
        return compor_fala_proativa(
            itens,
            obter_contexto_perceptivo=self.contexto_perceptivo,
            normalizar_segmento_fala=ns["_normalizar_segmento_fala"],
            normalizar_texto_com_apelidos=ns["_normalizar_texto_com_apelidos"],
            ajustar_tom_por_emocao=ns["_ajustar_tom_por_emocao"],
            fallback_fala_neutra=ns["FALLBACK_FALA_NEUTRA"],
        )

    def ajustar_estado_voz(self, chave: str, valor: Any) -> None:
        campos: Dict[str, Any] = {}
        if chave == "current_emotion":
            conversa_atual = self._estado().conversacional
            emocao_atual = str(conversa_atual.get("current_emotion") or "calma")
            emocao_nova = str(valor or "calma").strip().lower()
            if (
                emocao_nova == "calma"
                and emocao_atual.strip().lower() != "calma"
                and int(conversa_atual.get("emotion_interactions_left") or 0) > 0
            ):
                # "calma" pode ser apenas o tom técnico daquela fala. Não deve
                # apagar uma emoção temporal que ainda está viva.
                return
            if emocao_nova and emocao_nova != emocao_atual.strip().lower():
                definir_emocao = self._namespace().get("_definir_emocao_conversacional")
                if callable(definir_emocao):
                    definir_emocao(
                        emocao_nova,
                        int(self._estado().conversacional.get("emotion_level") or 1),
                        "tom usado na fala",
                    )
                    return
            campos["current_emotion"] = emocao_nova or "calma"
        elif chave == "emotion_level":
            conversa_atual = self._estado().conversacional
            nivel_atual = int(conversa_atual.get("emotion_level") or 1)
            nivel_novo = max(1, min(3, int(valor or 1)))
            if (
                str(conversa_atual.get("current_emotion") or "calma") != "calma"
                and int(conversa_atual.get("emotion_interactions_left") or 0) > 0
                and nivel_novo < nivel_atual
            ):
                return
            campos["emotion_level"] = nivel_novo
        elif chave == "is_speaking":
            campos["is_speaking"] = bool(valor)
        elif chave == "audio_playing":
            campos["audio_playing"] = bool(valor)
        if campos:
            self._estado().atualizar_campos("conversacional", **campos)

    def registrar_mente_curta(
        self,
        texto_usuario: str = "",
        resposta_ia: str = "",
        intencao: str = "",
        alvo: str = "",
        escopo: str = "",
        habilidade: str = "",
    ) -> None:
        ns = self._namespace()
        estado = self._estado()
        conversa_get = ns.get("_conversa_estado_get")
        ultimo_topico = (
            conversa_get("ultimo_topico_conversa", "") if callable(conversa_get) else ""
        )
        emocao_atual = (
            conversa_get("current_emotion", "calma") if callable(conversa_get) else "calma"
        )
        novo = registrar_mente_curta(
            estado.mental,
            texto_usuario=texto_usuario,
            resposta_ia=resposta_ia,
            intencao=intencao,
            alvo=alvo,
            escopo=escopo,
            habilidade=habilidade,
            ultimo_topico_conversa=ultimo_topico,
            emocao_atual=emocao_atual,
            normalizar_texto_cb=ns["_normalizar_texto_com_apelidos"],
            eh_alvo_site_web_cb=ns["_eh_alvo_site_web"],
            texto_parece_pergunta_aberta_cb=texto_parece_pergunta_aberta,
            registrar_pergunta_aberta_cb=registrar_pergunta_aberta,
            limpar_pergunta_aberta_cb=limpar_pergunta_aberta,
            registrar_promessa_conversacional_cb=registrar_promessa_conversacional,
            atualizar_foco_vivo_cb=ns["_atualizar_foco_vivo"],
        )
        estado.substituir("mental", novo)

    def registrar_interacao_temporal(self, texto_usuario: str) -> Dict[str, Any]:
        texto = str(texto_usuario or "").strip()
        if not texto:
            return {}
        estado = self._estado()
        consciencia = atualizar_consciencia_temporal(
            estado.mental.get("consciencia_temporal"),
            texto,
        )
        estado.atualizar_campos(
            "mental",
            consciencia_temporal=consciencia,
        )
        return dict(consciencia.get("evento_turno") or {})

    def registrar_resultado_execucao(
        self,
        resultado: Any = None,
        texto: str = "",
        executou: bool | None = None,
        *,
        origem: str = "",
        status: str = "",
    ) -> None:
        ns = self._namespace()
        estado = self._estado()
        novo = registrar_resultado_execucao(
            estado.mental,
            resultado=resultado,
            texto=texto,
            executou=executou,
            origem=origem,
            status=status,
        )
        estado.substituir("mental", novo)
        enriquecido = enriquecer_resultado_execucao_contextual(
            estado.mental,
            resultado,
            texto=texto,
            executou=executou,
            status=status,
            normalizar_texto_cb=ns["_normalizar_texto_com_apelidos"],
            atualizar_foco_vivo_cb=ns["_atualizar_foco_vivo"],
        )
        estado.substituir("mental", enriquecido)

    def estado_contexto_intencao(self) -> Dict[str, Any]:
        ns = self._namespace()
        estado = self._estado()
        mente = estado.mental
        musica_get = ns["_musica_estado_get"]
        conversa_get = ns["_conversa_estado_get"]
        memoria_get = ns["_memoria_conversa_get"]
        continuidades_get = ns["_continuidades_get"]
        playlist_state = ns["playlist_state"]

        def registrar_arbitragem(texto: str, arbitragem: Dict[str, Any]) -> None:
            atual = dict(estado.mental)
            historico = list(atual.get("historico_arbitragem") or [])[-39:]
            registro = {
                "texto": str(texto or "").strip()[:300],
                "decisao": dict(arbitragem.get("decisao") or {}),
                "origem": str(arbitragem.get("origem") or ""),
                "tipo": str(arbitragem.get("tipo") or ""),
                "modalidade": str(arbitragem.get("modalidade") or ""),
                "confianca": float(arbitragem.get("confianca") or 0.0),
                "rejeitados": list(arbitragem.get("rejeitados") or [])[:8],
                "retrato_id": arbitragem.get("retrato_id"),
                "referencia_resolvida": dict(arbitragem.get("referencia_resolvida") or {}),
                "ts": time.time(),
            }
            historico.append(registro)
            atual["historico_arbitragem"] = historico
            plano = dict(atual.get("plano_turno_atual") or {})
            if plano:
                plano["decisao_turno"] = consolidar_arbitragem(
                    plano.get("decisao_turno"),
                    arbitragem,
                )
                atual["plano_turno_atual"] = plano
                atual["decisao_turno_atual"] = dict(plano["decisao_turno"])
            if registro["rejeitados"]:
                candidatos = list(atual.get("casos_regressao_candidatos") or [])[-19:]
                candidatos.append(registro)
                atual["casos_regressao_candidatos"] = candidatos
            estado.substituir("mental", atual)

        return {
            "ultima_playlist": musica_get("ultima_playlist"),
            "current_emotion": conversa_get("current_emotion", "calma"),
            "emotion_level": conversa_get("emotion_level", 1),
            "messages": memoria_get("messages", []),
            "set_ultima_playlist": lambda valor: ns["_musica_estado_set"]("ultima_playlist", valor),
            "set_playlist_state_last_url": lambda valor: playlist_state.__setitem__("last_url", valor),
            "set_playlist_sugestao_pendente": lambda valor: ns["_continuidades_set"](
                "playlist_sugestao_pendente", valor
            ),
            "set_continuidade": ns.get("_continuidades_set"),
            "update_continuidades": ns.get("_continuidades_update"),
            "ultimo_alvo": str(mente.get("ultimo_alvo") or "").strip(),
            "ultima_intencao": str(mente.get("ultima_intencao") or "").strip(),
            "ultimo_escopo": str(mente.get("ultimo_escopo") or "").strip(),
            "ultima_habilidade": str(mente.get("ultima_habilidade") or "").strip(),
            "ultimas_entradas": list(mente.get("ultimas_entradas") or []),
            "foco_vivo": ns["_foco_vivo_atual"](),
            "_bloqueio_por_emocao": lambda intent, texto, _ctx: bloquear_por_emocao(
                intent,
                texto,
                {
                    "current_emotion": conversa_get("current_emotion", "calma"),
                    "emotion_level": conversa_get("emotion_level", 1),
                    "falar_com_lipsync": ns["falar_com_lipsync"],
                    "_normalizar_texto_com_apelidos": ns["_normalizar_texto_com_apelidos"],
                },
            ),
            "registrar_contexto_arquivo": lambda alvo, tipo="": self.registrar_mente_curta(
                "", "", intencao="ARQUIVOS", alvo=alvo, habilidade=tipo or "arquivos"
            ),
            "ultima_pasta_contextual": lambda: str(mente.get("ultima_pasta") or "").strip(),
            "ultimo_arquivo_contextual": lambda: str(
                mente.get("ultimo_caminho_arquivo") or mente.get("ultimo_arquivo") or ""
            ).strip(),
            "estrutura_arquivo_recente": lambda: ns["_estrutura_arquivo_recente"](ttl_s=900.0) or {},
            "_gmail_nao_lidos_cache": list(ns.get("_gmail_nao_lidos_cache") or []),
            "cidade_padrao_clima": ns["BRIEFING_CIDADE"],
            "_playlist_sugestao_pendente": continuidades_get("playlist_sugestao_pendente"),
            "turno_atual": dict(mente.get("turno_atual") or {}),
            "plano_turno_atual": dict(mente.get("plano_turno_atual") or {}),
            "retrato_turno_atual": dict(mente.get("retrato_turno_atual") or {}),
            "especialistas_turno_atual": dict(mente.get("especialistas_turno_atual") or {}),
            "registrar_arbitragem_turno": registrar_arbitragem,
        }


def criar_estado_contexto_runtime(**kwargs: Any) -> EstadoContextoRuntime:
    return EstadoContextoRuntime(**kwargs)
