"""Fluxo principal de resposta da IA da Laylay."""

from __future__ import annotations

from typing import Any, Dict
from mente_laylay.autonomia.pre_fluxo_contextual import (
    executar_pipeline_pre_fluxo,
    processar_bloqueio_playlist_temporario,
    processar_comentario_resultado_operacional,
    processar_confirmacao_musical_pendente,
    processar_encerramento_conversa,
    processar_feedback_pendente,
    processar_opiniao_musica_atual,
    processar_pergunta_curta_contextual,
    processar_reparacao_conversacional,
    processar_resposta_pendencia_prioritaria,
    processar_continuacao_visao_jogo,
)


CATEGORIAS_PRE_FLUXO_PERMITIDAS = frozenset({
    "confirmacao",
    "continuidade",
    "pendencia",
    "protecao",
})

ETAPAS_PRE_FLUXO_AUDITADAS = (
    ("reparacao_conversacional", "continuidade"),
    ("comentario_resultado_operacional", "continuidade"),
    ("continuacao_visao_jogo", "continuidade"),
    ("opiniao_musica_atual", "continuidade"),
    ("resposta_pendencia_prioritaria", "pendencia"),
    ("feedback_pendente", "pendencia"),
    ("confirmacao_musical_pendente", "confirmacao"),
    ("bloqueio_playlist_temporario", "protecao"),
    ("pergunta_curta_contextual", "continuidade"),
)


def _get(ctx: Dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(ctx, dict) and key in ctx:
        return ctx.get(key, default)
    return default

def processar_inicio_fluxo_resposta_ia(ctx: Dict[str, Any], texto: str) -> bool:
    t = str(texto or "").strip()
    if not t:
        return True

    encerrado, etapa_encerramento = processar_encerramento_conversa(
        ctx, t, emitir_fala=False,
    )
    if etapa_encerramento:
        print(f"🧭 [PRE-FLUXO] {etapa_encerramento} | resposta reservada para a LLM")
    if encerrado:
        print(f"🧭 [PRE-FLUXO] {etapa_encerramento}")
        return True

    refinar_contexto_mental = _get(ctx, "_refinar_contexto_mental")
    evento_temporal = {}
    if callable(refinar_contexto_mental):
        evento_temporal = refinar_contexto_mental(t)
    # Adaptadores antigos ainda podem não devolver o evento. Nesse caso, o
    # registrador dedicado preserva o contrato sem duplicar a escrita quando
    # o refinamento moderno já atualizou a consciência temporal.
    if not isinstance(evento_temporal, dict):
        registrar_tempo = _get(ctx, "_registrar_interacao_temporal")
        evento_temporal = registrar_tempo(t) if callable(registrar_tempo) else {}

    recarregar_contexto = _get(ctx, "_recarregar_contexto_inicio")
    if callable(recarregar_contexto):
        try:
            contexto_atualizado = recarregar_contexto()
            if isinstance(contexto_atualizado, dict):
                ctx.clear()
                ctx.update(contexto_atualizado)
        except Exception as erro:
            print(f"⚠️ [MENTE:RETRATO] falha ao atualizar contexto do turno: {erro}")

    evento_temporal = evento_temporal if isinstance(evento_temporal, dict) else {}
    tipo_evento_temporal = str(evento_temporal.get("tipo") or "")
    if tipo_evento_temporal in {
        "confirmacao_conclusao_necessaria",
        "conclusao_confirmada",
        "conclusao_cancelada",
    }:
        print(
            "🧠 [TEMPO] estado atualizado sem fala local | "
            f"evento={tipo_evento_temporal}"
        )

    mente_turno = _get(ctx, "mente_integrada_estado", {})
    pendencia_turno = mente_turno.get("pendencia_atual") if isinstance(mente_turno, dict) else {}
    periodo_cb = _get(ctx, "_contexto_horario_atual")
    periodo = periodo_cb() if callable(periodo_cb) else "indefinido"
    print(
        "🧠 [CONTEXTO:TURNO] "
        f"periodo={periodo} | "
        f"pendencia={str((pendencia_turno or {}).get('origem') or '-')}:{str((pendencia_turno or {}).get('tipo') or '-')} | "
        f"ultima_habilidade={str((mente_turno or {}).get('ultima_habilidade') or '-')}"
    )

    def _log(etapa: str, detalhe: str = "") -> None:
        extra = f" | {detalhe}" if detalhe else ""
        print(f"🧭 [PRE-FLUXO] {etapa}{extra}")

    turno_atual = dict(mente_turno.get("turno_atual") or {}) if isinstance(mente_turno, dict) else {}
    modalidade_atual = str(
        turno_atual.get("modalidade_geral") or turno_atual.get("modalidade") or "conversa"
    ).lower()
    turno_sem_execucao = bool(
        not turno_atual.get("autoriza_execucao")
        and modalidade_atual != "comando"
    )
    usar_ia_principal_semantica = bool(
        turno_sem_execucao
        or (
            _get(ctx, "_semantica_na_resposta_principal", False)
            and modalidade_atual == "misto"
        )
    )

    # O pré-fluxo não classifica nem executa comandos novos. Sua única função
    # é preservar respostas vinculadas ao estado já criado neste mesmo turno:
    # continuidade, pendências, confirmações e proteções explícitas.
    etapas = [lambda: processar_continuacao_visao_jogo(ctx, t)]
    # Correções e perguntas sobre a autoria de uma ação pertencem ao contrato
    # operacional recente. Elas não podem cair na LLM como conversa solta.
    etapas.extend([
        lambda: processar_reparacao_conversacional(ctx, t),
        lambda: processar_comentario_resultado_operacional(ctx, t),
    ])
    if not usar_ia_principal_semantica:
        etapas.append(lambda: processar_opiniao_musica_atual(ctx, t))
    etapas.extend([
        lambda: processar_resposta_pendencia_prioritaria(ctx, t),
        # Uma contraproposta pode conter verbo operacional ("melhor diminuir
        # o brilho"). A sugestão pendente precisa interpretá-la antes que o
        # executor a trate como um comando novo sem contexto.
        lambda: processar_feedback_pendente(ctx, t),
        lambda: processar_confirmacao_musical_pendente(ctx, t),
        lambda: processar_bloqueio_playlist_temporario(ctx, t),
        lambda: processar_pergunta_curta_contextual(ctx, t),
    ])

    _log("voz_unica_llm", "conversa reservada para a LLM")

    if executar_pipeline_pre_fluxo(ctx, t, etapas, log_cb=_log):
        return True

    _log("sem_vencedor_precoce", "segue para ia principal")
    print(f"🧠 [IA] Gerando resposta para: '{texto}'")
    return False
