"""Fluxo principal de resposta da IA da Laylay."""

from __future__ import annotations

from typing import Any, Dict
from mente_laylay.autonomia.pre_fluxo_contextual import (
    executar_pipeline_pre_fluxo,
    processar_aprendizado_apelido,
    processar_bloqueio_playlist_temporario,
    processar_consulta_sistema_local,
    processar_encerramento_conversa,
    processar_execucao_pratica_precoce,
    processar_feedback_pendente,
    processar_fluxo_musical_generico,
    processar_opiniao_musica_atual,
    processar_identidade_usuario,
    processar_pergunta_curta_contextual,
    processar_resposta_pendencia_prioritaria,
    processar_continuacao_visao_jogo,
    processar_sugestao_indireta,
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

    etapas = [
        # Identidade explícita precisa vencer conversa e interpretação por IA;
        # só assim o nome confirmado se torna a fonte única da sessão.
        lambda: processar_identidade_usuario(ctx, t),
        # Reações como "ficou rosa" pertencem ao resultado da ação recém
        # executada, não ao tópico de conversa que existia antes do comando.
        lambda: processar_consulta_sistema_local(ctx, t),
        # Uma análise visual pode ter pedido classe, build ou qualquer outro
        # detalhe livre. Essa continuação pertence ao mesmo fio antes dos
        # atalhos sociais e da IA genérica.
        lambda: processar_continuacao_visao_jogo(ctx, t),
    ]
    if not usar_ia_principal_semantica:
        etapas.append(lambda: processar_opiniao_musica_atual(ctx, t))
    etapas.extend([
        lambda: processar_resposta_pendencia_prioritaria(ctx, t),
        # Uma contraproposta pode conter verbo operacional ("melhor diminuir
        # o brilho"). A sugestão pendente precisa interpretá-la antes que o
        # executor a trate como um comando novo sem contexto.
        lambda: processar_feedback_pendente(ctx, t),
        lambda: processar_execucao_pratica_precoce(ctx, t),
    ])
    etapas.extend([
        lambda: processar_bloqueio_playlist_temporario(ctx, t),
        lambda: processar_fluxo_musical_generico(ctx, t),
        lambda: processar_sugestao_indireta(ctx, t),
        lambda: processar_pergunta_curta_contextual(ctx, t),
    ])

    _log("voz_unica_llm", "conversa reservada para a LLM")
    etapas.append(lambda: processar_aprendizado_apelido(ctx, t))

    if executar_pipeline_pre_fluxo(ctx, t, etapas, log_cb=_log):
        return True

    _log("sem_vencedor_precoce", "segue para ia principal")
    print(f"🧠 [IA] Gerando resposta para: '{texto}'")
    return False


def processar_movimento_playlist_pre_ia(ctx: Dict[str, Any], texto: str) -> bool:
    detectar_movimento = _get(ctx, "_detectar_mover_playlist_texto")
    mover_item = _get(ctx, "_mover_item_playlist")
    falar = _get(ctx, "falar_com_lipsync")
    salvar_memoria = _get(ctx, "salvar_memoria")
    messages = _get(ctx, "messages")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    if not callable(detectar_movimento) or not callable(mover_item):
        return False

    try:
        movimento = detectar_movimento(texto)
        if not movimento:
            return False
        resultado = mover_item(
            movimento.get("origem", ""),
            movimento.get("destino", ""),
            movimento.get("musica", ""),
        )
        resultado = resultado if isinstance(resultado, dict) else {}
        if resultado.get("ok"):
            titulo = resultado.get("titulo") or "essa música"
            origem = resultado.get("origem") or movimento.get("origem", "")
            destino = resultado.get("destino") or movimento.get("destino", "")
            fala = f"Movi {titulo} da playlist {origem} pra {destino}."
            if resultado.get("duplicated"):
                fala = f"Tirei {titulo} da playlist {origem}; ela já estava em {destino}."
            print(f"🎵 [PLAYLIST] {fala}")
            if isinstance(messages, list):
                messages.append({"role": "user", "content": str(texto or "").strip()})
                messages.append({"role": "assistant", "content": fala})
            if callable(falar):
                falar(fala, current_emotion or "calma", emotion_level or 1)
            if callable(salvar_memoria):
                salvar_memoria()
            return True

        if resultado.get("error") == "source_empty":
            fala = (
                f"Não achei nada na playlist "
                f"{resultado.get('origem') or movimento.get('origem')} pra mover."
            )
        else:
            fala = "Não consegui entender de qual playlist pra qual playlist é essa mudança."
        print(f"❌ [PLAYLIST] Falha ao mover por texto: {resultado}")
        if callable(falar):
            falar(fala, "calma", 1)
        return True
    except Exception as erro:
        print(f"⚠️ [PLAYLIST] Falha no atalho de mover playlist: {erro}")
        return False


def processar_consulta_aprendizados_pre_ia(ctx: Dict[str, Any], texto: str) -> bool:
    recuperar_aprendizados = _get(ctx, "_recuperar_aprendizados")
    falar = _get(ctx, "falar_com_lipsync")
    current_emotion = _get(ctx, "current_emotion", "calma")
    emotion_level = _get(ctx, "emotion_level", 1)
    entrada = str(texto or "")
    entrada_lower = entrada.lower()
    consultas = [
        "o que eu te ensinei",
        "o que eu te ensinei ontem",
        "o que você aprendeu",
        "o que aprendeu",
        "você lembra do que eu te falei",
        "você lembra do que eu te ensinei",
        "me lembra do que eu te ensinei",
    ]
    if not any(consulta in entrada_lower for consulta in consultas):
        return False
    if not callable(recuperar_aprendizados):
        return False

    try:
        aprendizados = recuperar_aprendizados(limit=3)
        if not aprendizados:
            return False
        ultimo = str(aprendizados[0]).strip()
        if len(ultimo) > 120:
            ultimo = ultimo[:117] + "..."
        resposta = f"Ah, lembrei. Você me ensinou isso: {ultimo}"
        if "responde" in ultimo.lower() or "de agora" in ultimo.lower():
            resposta = f"Ah, claro. Você me passou isso aqui: {ultimo}"
        if "de agora" in ultimo.lower():
            resposta = f"Ah, então é assim que você quer: {ultimo}"
        print(f"🧠 [MEMÓRIA] Resposta natural de aprendizado pronta: {resposta}")
        if callable(falar):
            falar(resposta, current_emotion or "calma", emotion_level or 1)
        return True
    except Exception as erro:
        print(f"⚠️ [MEMÓRIA] Não consegui recuperar aprendizados: {erro}")
        return False


def processar_pre_fluxos_antes_ia(ctx: Dict[str, Any], texto: str) -> bool:
    """Executa atalhos especializados que devem vencer antes da chamada ao LLM."""
    if processar_movimento_playlist_pre_ia(ctx, texto):
        return True
    return processar_consulta_aprendizados_pre_ia(ctx, texto)
