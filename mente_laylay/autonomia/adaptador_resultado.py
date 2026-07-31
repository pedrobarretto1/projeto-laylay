"""Registro e verbalização coerente do resultado operacional de um turno."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, inferir_confirmacao
from mente_laylay.personalidade.falas_variadas import fala_por_estado_acao
from mente_laylay.personalidade.confirmacao_llm import (
    INTENTS_INFORMATIVOS,
    personalizar_confirmacao_llm,
    personalizar_informacao_llm,
)
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


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

    def contexto_fala(self) -> dict:
        return {
            "current_emotion": self.ctx.get("current_emotion", "calma"),
            "ultima_habilidade": self.ctx.get("ultima_habilidade", ""),
            "ultimo_alvo": self.ctx.get("ultimo_alvo", ""),
        }

    def marcar_resultado(
        self,
        status: str,
        executou: bool | None = None,
        *,
        confirmado: bool | None = None,
        detalhe: str = "",
    ) -> None:
        registrar = self.ctx.get("_registrar_resultado_execucao")
        if not callable(registrar):
            return
        try:
            status_norm = str(status or "").strip().lower()
            if executou is None:
                executou = status_norm not in STATUS_EXECUCAO_FALHOU
            contrato = ResultadoAcao(
                intent=self.intent,
                status=status,
                alvo=self.alvo_dos_params(),
                params=self.params,
                executou=bool(executou),
                confirmado=(
                    inferir_confirmacao(status, bool(executou))
                    if confirmado is None
                    else bool(confirmado)
                ),
                origem="executor",
                detalhe=detalhe,
                texto_usuario=self.texto_original,
            )
            registrar(
                contrato,
                self.texto_original,
                executou,
                origem="executor",
                status=status,
            )
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
        if executou is None:
            executou = not any(
                termo in status_norm
                for termo in (
                    "falha", "erro", "indisponivel", "nao_encontrado", "sem_suporte",
                )
            )
        fala_base = fala_por_estado_acao(
            status,
            fallback=fallback,
            alvo=alvo,
            contexto=self.contexto_fala(),
            texto_usuario=self.texto_original,
        )
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
            contexto={"destino": self.destino},
        )
        plano = planejar_resposta_acao(
            contrato,
            fala_base,
            emocao_preferida="calma" if status_calmo else "debochada",
            nivel_preferido=1 if status_calmo else 2,
        )
        if contrato.intent in INTENTS_INFORMATIVOS:
            # A frase factual inteira vira âncora literal. A LLM pode cercá-la
            # com a voz da Laylay, mas não resumir, trocar ou omitir os dados.
            confirmacao = personalizar_informacao_llm(
                fala_base,
                fatos_obrigatorios=[fala_base],
                enviar_mensagem=self.ctx.get("enviar_mensagem"),
                emocao="calma",
                nivel=1,
                contexto=self.contexto_fala(),
            )
        else:
            confirmacao = personalizar_confirmacao_llm(
                contrato,
                plano.fala,
                classe=getattr(plano, "classe", ""),
                emocao=plano.emocao,
                nivel=plano.nivel,
                enviar_mensagem=self.ctx.get("enviar_mensagem"),
                contexto=self.contexto_fala(),
            )
        falar_resultado = self.ctx.get("_falar_resultado_operacional")
        if callable(falar_resultado):
            falar_resultado(
                contrato,
                confirmacao.fala,
                confirmacao.emocao,
                confirmacao.nivel,
            )
        else:
            falar(confirmacao.fala, confirmacao.emocao, confirmacao.nivel)

    def falar_resultado_janela(self, nome: str, status: str) -> None:
        falas = {
            "ja_aberto_focado": f"{nome} já estava aberto e em foco.",
            "app_focado": f"{nome} já tava aberto, só puxei pra frente.",
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
            "falha_execucao": (
                f"Tentei mexer em {nome}, mas não rolou de verdade."
            ),
        }
        fallback = falas.get(
            status, f"Tentei mexer em {nome}, mas não rolou de verdade."
        )
        self.falar_por_status(status, fallback, alvo=nome)
