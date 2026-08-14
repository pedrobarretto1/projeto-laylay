"""Contrato unico do resultado real das habilidades da Laylay."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict

STATUS_RESULTADO_JA_SATISFEITO = {
    "ja_aberto_focado", "site_ja_aberto_focado",
    "ja_estava_ligado", "ja_estava_desligado",
    "playlist_ja_existia",
}

STATUS_RESULTADO_CANCELADO = {
    "cancelado", "cancelada", "acao_cancelada", "exclusao_cancelada",
    "cancelamento_confirmado",
}


STATUS_RESULTADO_CONFIRMADO = {
    "aba_fechada", "aba_fechada_em_vez_de_app", "app_fechado",
    "app_fechado_em_vez_de_aba", "app_focado", "app_iniciado_focado",
    "ja_aberto_focado",
    "janela_maximizada", "janela_arquivo_fechada",
    "pasta_criada", "subpasta_criada", "arquivo_criado",
    "conteudo_atualizado",
    "item_deletado", "item_movido_para_pasta", "emails_lidos",
    "emails_sincronizados", "notificacoes_lidas", "remetente_silenciado",
    "clima_consultado",
    "briefing_repetido", "dispositivos_listados",
    "playlists_listadas",
    "app_aberto", "url_aberta", "site_aberto",
    "url_aberta_via_app", "site_aberto_via_app",
    "musica_aberta", "musica_reproduzindo",
    "playlist_aberta", "playlist_aberta_pc_b",
    "playlist_criada",
    "playlist_deletada", "playlist_musica_adicionada", "acao_agendada",
    "lembrete_agendado", "agendamento_cancelado", "movido_para_lixeira",
    "nota_guardada", "notas_listadas", "discussao_guardada",
    "discussao_ja_guardada", "nota_excluida",
    # A pesquisa semântica relê dados locais e só publica caminhos que o
    # índice realmente devolveu. Esses estados possuem evidência de retorno,
    # portanto não podem ser rebaixados a "comando enviado sem confirmação".
    "arquivos_encontrados", "sem_resultados", "caminho_encontrado",
    "arquivo_aberto", "arquivo_aberto_focado", "resumo_concluido",
    "layout_confirmado",
} | STATUS_RESULTADO_JA_SATISFEITO


def inferir_confirmacao(status: str, executou: bool | None) -> bool | None:
    status_norm = str(status or "").strip().lower()
    # Em um no-op idempotente o executor não repete a ação, mas observou que o
    # estado desejado já era verdadeiro. Portanto ``executou=False`` e
    # ``confirmado=True`` são simultaneamente corretos.
    if status_norm in STATUS_RESULTADO_JA_SATISFEITO:
        return True
    if executou is False or any(
        termo in status_norm
        for termo in ("falha", "erro", "indisponivel", "nao_encontrado", "bloqueado")
    ):
        return False
    if executou is True and status_norm in STATUS_RESULTADO_CONFIRMADO:
        return True
    return None


@dataclass(frozen=True)
class ResultadoAcao:
    intent: str = ""
    acao: str = ""
    status: str = ""
    alvo: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    ok: bool | None = None
    executou: bool | None = None
    confirmado: bool | None = None
    origem: str = ""
    detalhe: str = ""
    texto_usuario: str = ""
    contexto: Dict[str, Any] = field(default_factory=dict)
    id_solicitacao: str = ""
    confirmacao_oferecida: str = ""
    evidencia_confirmacao: str = ""

    def __post_init__(self) -> None:
        intent = str(self.intent or self.acao or "").strip().upper()
        acao = str(self.acao or intent or "").strip()
        object.__setattr__(self, "intent", intent)
        object.__setattr__(self, "acao", acao)
        object.__setattr__(self, "status", str(self.status or "").strip().lower())
        object.__setattr__(self, "alvo", str(self.alvo or "").strip())
        object.__setattr__(self, "origem", str(self.origem or "").strip())
        object.__setattr__(self, "detalhe", str(self.detalhe or "").strip())
        object.__setattr__(self, "texto_usuario", str(self.texto_usuario or "").strip())
        object.__setattr__(self, "params", dict(self.params or {}))
        object.__setattr__(self, "contexto", dict(self.contexto or {}))
        object.__setattr__(self, "id_solicitacao", str(self.id_solicitacao or "").strip())
        # Importação tardia evita o ciclo especialistas -> operacional ->
        # resultado_acao durante a inicialização do pacote.
        from mente_laylay.especialistas.capacidades import consultar_capacidade

        capacidade = consultar_capacidade(intent)
        tipo_confirmacao = str(
            self.confirmacao_oferecida or capacidade.get("confirmacao_oferecida") or "indisponivel"
        ).strip().lower()
        object.__setattr__(self, "confirmacao_oferecida", tipo_confirmacao)
        object.__setattr__(self, "evidencia_confirmacao", str(
            self.evidencia_confirmacao or capacidade.get("evidencia_confirmacao") or ""
        ).strip())
        if (
            capacidade.get("dominio") != "desconhecido"
            and tipo_confirmacao == "indisponivel"
            and self.confirmado is True
        ):
            object.__setattr__(self, "confirmado", None)
        if self.ok is None and self.executou is not None:
            object.__setattr__(self, "ok", bool(self.executou))

    @property
    def estado_final(self) -> str:
        if self.status in STATUS_RESULTADO_CANCELADO:
            return "cancelado"
        if self.confirmado is True:
            return "confirmado"
        if self.executou is False or self.confirmado is False:
            return "falha"
        if self.executou is True:
            return "executado_sem_confirmacao"
        return "pendente"

    def como_dict(self) -> Dict[str, Any]:
        """Representa qualquer habilidade no mesmo protocolo de resultado."""
        return {
            "id_solicitacao": self.id_solicitacao,
            "intent": self.intent,
            "acao": self.acao,
            "alvo": self.alvo,
            "status": self.status,
            "executou": self.executou,
            "confirmado": self.confirmado,
            "ok": self.ok,
            "estado_final": self.estado_final,
            "origem": self.origem,
            "detalhe": self.detalhe,
            "params": dict(self.params),
            "contexto": dict(self.contexto),
            "confirmacao_oferecida": self.confirmacao_oferecida,
            "evidencia_confirmacao": self.evidencia_confirmacao,
            "estado_confirmacao": (
                "cancelado" if self.status in STATUS_RESULTADO_CANCELADO
                else "confirmado" if self.confirmado is True
                else "falhou" if self.executou is False or self.confirmado is False
                else "nao_confirmado"
            ),
        }

def normalizar_resultado_acao(
    resultado: ResultadoAcao | Dict[str, Any] | None,
    *,
    texto: str = "",
    executou: bool | None = None,
    origem: str = "",
    status: str = "",
) -> ResultadoAcao:
    """Converte retornos legados sem inventar confirmacao de execução."""
    if isinstance(resultado, ResultadoAcao):
        return replace(
            resultado,
            texto_usuario=str(texto or resultado.texto_usuario),
            executou=resultado.executou if executou is None else bool(executou),
            origem=str(origem or resultado.origem),
            status=str(status or resultado.status),
        )

    dados: Dict[str, Any] = dict(resultado) if isinstance(resultado, dict) else {}
    params_brutos = dados.get("params")
    params: Dict[str, Any] = (
        dict(params_brutos) if isinstance(params_brutos, dict) else {}
    )
    contexto_bruto = dados.get("contexto")
    contexto: Dict[str, Any] = (
        dict(contexto_bruto) if isinstance(contexto_bruto, dict) else {}
    )
    intent = str(dados.get("intent") or dados.get("acao") or "")
    alvo = str(
        dados.get("alvo")
        or params.get("alvo")
        or params.get("nome_app")
        or params.get("url")
        or params.get("site")
        or params.get("nome")
        or params.get("nome_playlist")
        or params.get("local")
        or params.get("query")
        or ""
    )
    executou_final = dados.get("executou") if executou is None else executou
    ok = dados.get("ok")
    confirmado = dados.get("confirmado")
    status_final = str(status or dados.get("status") or "")
    if confirmado is None:
        confirmado = inferir_confirmacao(status_final, executou_final)
    return ResultadoAcao(
        intent=intent,
        acao=str(dados.get("acao") or intent),
        status=status_final,
        alvo=alvo,
        params=params,
        ok=bool(ok) if ok is not None else None,
        executou=bool(executou_final) if executou_final is not None else None,
        confirmado=bool(confirmado) if confirmado is not None else None,
        origem=str(origem or dados.get("origem") or ""),
        detalhe=str(dados.get("detalhe") or dados.get("erro") or ""),
        texto_usuario=str(texto or dados.get("texto_usuario") or ""),
        contexto=contexto,
        id_solicitacao=str(dados.get("id_solicitacao") or dados.get("request_id") or ""),
        confirmacao_oferecida=str(dados.get("confirmacao_oferecida") or ""),
        evidencia_confirmacao=str(dados.get("evidencia_confirmacao") or ""),
    )
