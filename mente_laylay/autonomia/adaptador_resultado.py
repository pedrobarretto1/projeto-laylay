"""Registro e verbalização coerente do resultado operacional de um turno."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
from uuid import uuid4

from mente_laylay.memoria_mental.resultado_acao import (
    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO,
    ResultadoAcao,
    STATUS_RESULTADO_JA_SATISFEITO,
    inferir_confirmacao,
)
from mente_laylay.emocoes.avaliador_eventos import contextualizar_fala_evento
from mente_laylay.personalidade.falas_variadas import fala_por_estado_acao
from mente_laylay.personalidade.confirmacao_llm import (
    INTENTS_INFORMATIVOS,
    personalizar_confirmacao_llm,
    personalizar_informacao_llm,
)
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao
from mente_laylay.personalidade.higiene_fala import limpar_fala_operacional


STATUS_EXECUCAO_FALHOU = frozenset({
    "falha_execucao",
    "nao_encontrado",
    "app_aberto_sem_foco",
    "alvo_ausente",
    "notificacoes_sem_suporte",
})

STATUS_FALA_CALMA = frozenset({
    "emails_lidos",
    "emails_sincronizados",
    "notificacoes_lidas",
    "clima_consultado",
    "volume_ajustado",
    "volume_aumentado",
    "volume_baixado",
    "volume_mudo",
})


@dataclass(slots=True)
class AdaptadorResultadoOperacional:
    resultado: Dict[str, Any]
    params: Dict[str, Any]
    texto_original: str
    destino: str
    ctx: Dict[str, Any]
    # P0_BUG_B_OBSERVABILIDADE_EXECUCOES_V1_20260815
    # O ID identifica a ocorrência, não o tipo do intent.
    # P0_CONTRATO_EXECUCAO_NONE_V1_20260815
    # Quando o coordenador já criou a identidade, todos os publicadores da
    # mesma execução reutilizam esse ID. Chamadores legados ainda recebem UUID.
    id_solicitacao: str = ""

    def __post_init__(self) -> None:
        resultado = self.resultado if isinstance(self.resultado, dict) else {}
        # O marcador é uma prova apenas da invocação corrente. Se algum
        # resolvedor reutilizar o mesmo dict em outro turno, ele precisa voltar
        # a ser elegível ao fallback até publicar um novo ResultadoAcao.
        if isinstance(resultado, dict):
            resultado.pop(CHAVE_RESULTADO_OPERACIONAL_PUBLICADO, None)
        id_existente = str(
            self.id_solicitacao
            or resultado.get("id_solicitacao")
            or resultado.get("request_id")
            or ""
        ).strip()
        self.id_solicitacao = id_existente or uuid4().hex

    @property
    def intent(self) -> str:
        return str(
            self.resultado.get("intent") or self.resultado.get("acao") or ""
        )

    def alvo_dos_params(self) -> str:
        esquerda = str(self.params.get("left") or self.params.get("esquerda") or "").strip()
        direita = str(self.params.get("right") or self.params.get("direita") or "").strip()
        if esquerda or direita:
            partes = []
            if esquerda:
                partes.append(f"{esquerda} na esquerda")
            if direita:
                partes.append(f"{direita} na direita")
            return " e ".join(partes)
        return str(
            self.params.get("alvo")
            or self.params.get("nome_app")
            or self.params.get("url")
            or self.params.get("site")
            or self.params.get("nome")
            or self.params.get("nome_arquivo")
            or self.params.get("arquivo_nome")
            or self.params.get("nome_playlist")
            or self.params.get("local")
            or self.params.get("query")
            or ""
        )

    def contexto_fala(self, extra: Dict[str, Any] | None = None) -> dict:
        modo_jogo = self.ctx.get("modo_jogo_ativo", False)
        try:
            modo_jogo_ativo = bool(modo_jogo() if callable(modo_jogo) else modo_jogo)
        except Exception:
            modo_jogo_ativo = False
        contexto = {
            "current_emotion": self.ctx.get("current_emotion", "calma"),
            "ultima_habilidade": self.ctx.get("ultima_habilidade", ""),
            "ultimo_alvo": self.ctx.get("ultimo_alvo", ""),
            "ultima_resposta": self.ctx.get("ultima_resposta", ""),
            "falas_recentes": list(self.ctx.get("falas_recentes") or [])[-4:],
            "modo_jogo_ativo": modo_jogo_ativo,
        }
        if isinstance(extra, dict):
            contexto.update(extra)
        return contexto

    def marcar_resultado(
        self,
        status: str,
        executou: bool | None = None,
        *,
        confirmado: bool | None = None,
        detalhe: str = "",
        alvo_resolvido: str = "",
        params_resolvidos: Dict[str, Any] | None = None,
    ) -> None:
        """Publica também as resoluções descobertas durante a execução.

        ``self.params`` descreve o pedido recebido, mas alguns executores só
        descobrem o alvo real durante a ação. Devolver esse alvo no contrato
        canônico mantém referências como ``ele`` e ``essa também`` ligadas ao
        resultado efetivamente confirmado.
        """
        registrar = self.ctx.get("_registrar_resultado_execucao")
        if not callable(registrar):
            return
        try:
            status_norm = str(status or "").strip().lower()
            if status_norm in STATUS_RESULTADO_JA_SATISFEITO:
                # O executor confirmou o estado, mas não realizou uma nova
                # ação. Corrige também chamadores legados que usam ``ok``
                # como sinônimo de ``executou``.
                executou = False
            elif executou is None:
                executou = (
                    status_norm not in STATUS_EXECUCAO_FALHOU
                )
            params_finais = dict(self.params)
            if isinstance(params_resolvidos, dict):
                params_finais.update({
                    chave: valor
                    for chave, valor in params_resolvidos.items()
                    if valor is not None and str(valor).strip()
                })
            alvo_final = str(alvo_resolvido or "").strip() or self.alvo_dos_params()
            contrato = ResultadoAcao(
                intent=self.intent,
                status=status,
                alvo=alvo_final,
                params=params_finais,
                executou=bool(executou),
                confirmado=(
                    inferir_confirmacao(status, bool(executou))
                    if confirmado is None
                    else bool(confirmado)
                ),
                origem="executor",
                detalhe=detalhe,
                texto_usuario=self.texto_original,
                id_solicitacao=self.id_solicitacao,
            )
            registrar(
                contrato,
                self.texto_original,
                executou,
                origem="executor",
                status=status,
            )
            # Só marque depois que o registrador oficial retornou. Assim,
            # falhas de publicação continuam permitindo o fallback legado.
            if isinstance(self.resultado, dict):
                self.resultado[
                    CHAVE_RESULTADO_OPERACIONAL_PUBLICADO
                ] = self.id_solicitacao
        except Exception:
            pass

    def falar_por_status(
        self,
        status: str,
        fallback: str,
        *,
        alvo: str = "",
        executou: bool | None = None,
        confirmado: bool | None = None,
        detalhe: str = "",
    ) -> None:
        falar = self.ctx.get("falar_com_lipsync")
        if not callable(falar):
            return
        status_norm = str(status or "").strip().lower()
        if status_norm in STATUS_RESULTADO_JA_SATISFEITO:
            executou = False
        elif executou is None:
            executou = not any(
                termo in status_norm
                for termo in (
                    "falha", "erro", "indisponivel", "nao_encontrado", "sem_suporte",
                )
            )
        contexto_fala = self.contexto_fala()
        modo_jogo_ativo = bool(contexto_fala.get("modo_jogo_ativo"))
        if self.intent == "NOTIFICATIONS" and str(fallback or "").strip():
            # O resumo da central já é o dado observado. Passá-lo pelo gerador
            # de confirmação antes de montar o contrato acrescentava uma
            # âncora operacional artificial e podia rebaixá-lo a incerteza.
            fala_base = str(fallback).strip()
        else:
            fala_base = fala_por_estado_acao(
                status,
                fallback=fallback,
                alvo=alvo,
                contexto=contexto_fala,
                texto_usuario=self.texto_original,
            )
        if status_norm in STATUS_RESULTADO_JA_SATISFEITO and not modo_jogo_ativo:
            objeto = str(alvo or "isso").strip()
            if status_norm in {"ja_aberto_focado", "site_ja_aberto_focado"}:
                fala_base = f"{objeto} já está aberto e em foco; não repeti a abertura."
            elif status_norm == "app_ja_aberto_observado":
                fala_base = f"{objeto} já está aberto; não repeti a abertura."
            elif status_norm == "ja_estava_ligado":
                fala_base = f"{objeto} já está ligado; não repeti o comando."
            elif status_norm == "ja_estava_desligado":
                fala_base = f"{objeto} já está desligado; não repeti o comando."
            elif status_norm == "playlist_musica_ja_existia":
                fala_base = (
                    f"A faixa já estava na playlist {objeto}; mantive uma só cópia."
                )
            elif status_norm == "playlist_ja_existia":
                fala_base = f"A playlist {objeto} já existia; não criei outra."
            elif status_norm == "lembrete_ja_agendado":
                fala_base = (
                    f"O lembrete de {objeto} já estava agendado; "
                    "mantive uma só cópia."
                )
            else:
                fala_base = f"{objeto} já estava como você pediu; não repeti a ação."
        status_calmo = status_norm in STATUS_FALA_CALMA
        contrato = ResultadoAcao(
            intent=self.intent,
            status=status_norm,
            alvo=alvo,
            params=self.params,
            executou=executou,
            confirmado=(
                inferir_confirmacao(status_norm, executou)
                if confirmado is None
                else bool(confirmado)
            ),
            detalhe=detalhe,
            texto_usuario=self.texto_original,
            id_solicitacao=self.id_solicitacao,
            contexto={"destino": self.destino},
        )
        avaliacao_evento: dict[str, Any] = {}
        avaliar_evento = self.ctx.get("_avaliar_evento_emocional_operacional")
        if callable(avaliar_evento):
            try:
                avaliada = avaliar_evento(contrato)
                if isinstance(avaliada, dict):
                    avaliacao_evento = dict(avaliada)
            except Exception:
                avaliacao_evento = {}
        if avaliacao_evento:
            contrato.contexto["avaliacao_evento"] = dict(avaliacao_evento)
        emocao_evento = str(avaliacao_evento.get("emocao") or "").strip()
        expressao_evento = bool(avaliacao_evento.get("permite_expressao"))
        emocao_preferida = (
            emocao_evento
            if expressao_evento and emocao_evento
            else "calma" if status_calmo else "debochada"
        )
        nivel_preferido = (
            max(1, min(3, int(avaliacao_evento.get("nivel") or 1)))
            if expressao_evento
            else 1 if status_calmo else 2
        )
        plano = planejar_resposta_acao(
            contrato,
            fala_base,
            emocao_preferida=emocao_preferida,
            nivel_preferido=nivel_preferido,
        )
        if contrato.intent in INTENTS_INFORMATIVOS:
            # A frase factual inteira vira âncora literal. A LLM pode cercá-la
            # com a voz da Laylay, mas não resumir, trocar ou omitir os dados.
            # Listagens válidas não precisam ganhar um prefixo operacional.
            # Porém, se uma fala de sucesso contém incerteza ou falha, usamos a
            # versão saneada pelo contrato para nunca misturar duas verdades.
            fala_informativa = fala_base
            base_norm = str(fala_base or "").casefold()
            contradiz_sucesso = plano.classe == "sucesso" and any(
                sinal in base_norm
                for sinal in (
                    "não consegui", "nao consegui", "não confirmei",
                    "nao confirmei", "não respondeu", "nao respondeu",
                    "não executei", "nao executei", "falhou",
                )
            )
            if contradiz_sucesso or plano.classe in {
                "falha", "cancelado", "pendente", "sem_acao",
            }:
                fala_informativa = plano.fala
            confirmacao = personalizar_informacao_llm(
                fala_informativa,
                fatos_obrigatorios=[fala_informativa],
                enviar_mensagem=self.ctx.get("enviar_mensagem"),
                emocao="calma",
                nivel=1,
                contexto=self.contexto_fala({"avaliacao_evento": avaliacao_evento}),
            )
        else:
            confirmacao = personalizar_confirmacao_llm(
                contrato,
                plano.fala,
                classe=getattr(plano, "classe", ""),
                emocao=plano.emocao,
                nivel=plano.nivel,
                enviar_mensagem=self.ctx.get("enviar_mensagem"),
                contexto=self.contexto_fala({"avaliacao_evento": avaliacao_evento}),
            )
        if (
            not modo_jogo_ativo
            and not confirmacao.usada_llm
            and getattr(confirmacao, "motivo_fallback", "")
        ):
            log = self.ctx.get("print") or self.ctx.get("log") or print
            log(
                "⚠️ [FALA:AUTORIA] fallback local | "
                f"motivo={confirmacao.motivo_fallback} status={status_norm}"
            )
        # No cotidiano a confirmação e a reação emocional têm uma única
        # autora: a LLM. No jogo preservamos as frases locais, rápidas e sem
        # custo de inferência, inclusive a reação causal curta.
        fala_final = (
            contextualizar_fala_evento(
                confirmacao.fala,
                avaliacao_evento,
                alvo=contrato.alvo,
            )
            if modo_jogo_ativo
            else confirmacao.fala
        )
        fala_final = limpar_fala_operacional(fala_final)
        if not fala_final:
            fala_final = limpar_fala_operacional(plano.fala or fallback)
        emocao_final = emocao_evento if expressao_evento else confirmacao.emocao
        nivel_final = nivel_preferido if expressao_evento else confirmacao.nivel
        falar_resultado = self.ctx.get("_falar_resultado_operacional")
        if callable(falar_resultado):
            falar_resultado(
                contrato,
                fala_final,
                emocao_final,
                nivel_final,
            )
        else:
            falar(fala_final, emocao_final, nivel_final)

    def falar_resultado_janela(self, nome: str, status: str) -> None:
        falas = {
            "ja_aberto_focado": f"{nome} já estava aberto e em foco.",
            "app_focado": f"{nome} já tava aberto, só puxei pra frente.",
            "app_iniciado_focado": f"Iniciei {nome} e trouxe a nova janela para o foco.",
            "app_aberto": f"Abrindo {nome}.",
            "app_aberto_segundo_plano": (
                f"Abri {nome} em segundo plano, sem tirar você do jogo."
            ),
            "app_aberto_sem_foco": (
                f"{nome} abriu, mas não consegui puxar ele pro foco agora."
            ),
            "abertura_solicitada": (
                f"Pedi para abrir {nome}, mas ele ainda não apareceu para eu confirmar."
            ),
            "site_aberto": f"Abrindo {nome} no navegador.",
            "site_aberto_segundo_plano": (
                f"Deixei {nome} no navegador em segundo plano, sem trocar sua tela."
            ),
            "site_ja_aberto_focado": (
                f"{nome} já estava aberto; só trouxe a aba pra frente."
            ),
            "protocolo_aberto": f"Abrindo {nome} pelo protocolo do sistema.",
            "nao_encontrado": f"Não achei {nome}.",
            "janela_maximizada": f"{nome.title()} maximizado e em foco.",
            "maximizacao_nao_confirmada": (
                f"{nome} está aberto, mas eu não consegui confirmar que a janela foi maximizada."
            ),
            "falha_execucao": (
                f"Tentei mexer em {nome}, mas não rolou de verdade."
            ),
        }
        fallback = falas.get(
            status, f"Tentei mexer em {nome}, mas não rolou de verdade."
        )
        self.falar_por_status(status, fallback, alvo=nome)
