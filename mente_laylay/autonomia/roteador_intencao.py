"""Roteador principal de intencoes da Laylay."""

from __future__ import annotations

from typing import Any, Dict
from mente_laylay.personalidade.falas_variadas import escolher as _escolher_fala_variada
from mente_laylay.autonomia.executor_janelas import (
    DependenciasExecutorJanelas,
    executar_intencao_janelas as _executar_intencao_janelas,
)
from mente_laylay.autonomia.executor_navegador import (
    DependenciasExecutorNavegador,
    executar_intencao_navegador as _executar_intencao_navegador,
)
from mente_laylay.autonomia.executor_audio import (
    DependenciasExecutorAudio,
    executar_intencao_audio as _executar_intencao_audio,
)
from mente_laylay.autonomia.executor_agenda import (
    DependenciasExecutorAgenda,
    executar_intencao_agenda as _executar_intencao_agenda,
)
from mente_laylay.autonomia.executor_informacoes import (
    DependenciasExecutorInformacoes,
    executar_intencao_informacoes as _executar_intencao_informacoes,
)
from mente_laylay.autonomia.executor_sistema import (
    DependenciasExecutorSistema,
    executar_intencao_sistema as _executar_intencao_sistema,
)
from mente_laylay.autonomia.executor_musical import (
    DependenciasExecutorMusical,
    executar_intencao_musical as _executar_intencao_musical,
)
from mente_laylay.autonomia.executor_playlists import (
    DependenciasExecutorPlaylists,
    executar_intencao_playlists as _executar_intencao_playlists,
)
from mente_laylay.autonomia.executor_cancelamentos import (
    DependenciasExecutorCancelamentos,
    executar_intencao_cancelamentos as _executar_intencao_cancelamentos,
)
from mente_laylay.autonomia.executor_integracoes import (
    DependenciasExecutorIntegracoes,
    executar_intencao_integracoes as _executar_intencao_integracoes,
)
from mente_laylay.autonomia.validacao_ambiente import ValidadorAmbiente
from mente_laylay.autonomia.adaptador_resultado import AdaptadorResultadoOperacional
from mente_laylay.autonomia.rota_musical import RotaMusical
from mente_laylay.autonomia.classificacao_habilidade import (
    classificar_habilidade_intent,
    extrair_alvo_mental,
)
from mente_laylay.percepcao.modo_jogo import pedido_foco_explicito


def _get(ctx: Dict[str, Any], nome: str, default=None):
    return ctx.get(nome, default)


def bloquear_por_emocao(intent: str, texto_original: str, ctx: Dict[str, Any]) -> bool:
    current_emotion = _get(ctx, "current_emotion", "")
    emotion_level = _get(ctx, "emotion_level", 1)
    falar = _get(ctx, "falar_com_lipsync")
    normalizar = _get(ctx, "_normalizar_texto_com_apelidos")
    try:
        nivel = int(emotion_level or 1)
    except Exception:
        nivel = 1
    if str(current_emotion or "").strip().lower() != "brava" or nivel < 3:
        return False
    intent = str(intent or "").upper().strip()
    if intent in {"MUSIC_SEARCH", "PLAYLIST_PLAY"} and callable(falar):
        fala = "Agora não. Tô brava e não tô a fim de mexer nisso."
        if callable(normalizar) and "por favor" in normalizar(texto_original):
            fala = "Nem assim. Depois eu vejo isso."
        falar(fala, "brava", max(3, nivel))
        return True
    return False


def executar_intencao(resultado: dict, texto_original: str, ctx: Dict[str, Any]) -> bool:
    if not isinstance(resultado, dict):
        return False

    destino = _get(ctx, "_target_from_params", lambda p, t="": "pc_a")
    registrar_mente_curta = _get(ctx, "_registrar_mente_curta")
    bloqueio = _get(ctx, "_bloqueio_por_emocao")
    falar = _get(ctx, "falar_com_lipsync")

    def _reg(*args, **kwargs):
        if callable(registrar_mente_curta):
            return registrar_mente_curta(*args, **kwargs)
        return None

    intent = str(resultado.get("intent") or "").upper().strip()
    raw_params = resultado.get("params")
    params = dict(raw_params) if isinstance(raw_params, dict) else {}
    if pedido_foco_explicito(texto_original):
        params["permitir_foco"] = True
    destino_val = destino(params, texto_original) if callable(destino) else "pc_a"
    validacao_ambiente = ValidadorAmbiente(ctx, destino_val, texto_original)
    rota_musical = RotaMusical(ctx, destino_val, texto_original)
    adaptador_resultado = AdaptadorResultadoOperacional(
        resultado, params, texto_original, destino_val, ctx
    )
    alvo_mental = extrair_alvo_mental(params)
    habilidade = classificar_habilidade_intent(intent)
    _reg(texto_original, "", intent, alvo_mental, destino_val, habilidade)

    if callable(bloqueio) and bloqueio(intent, texto_original, ctx):
        return True

    despacho_janelas = _executar_intencao_janelas(
        intent,
        params,
        destino_val,
        ctx,
        DependenciasExecutorJanelas(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            falar_resultado_janela=adaptador_resultado.falar_resultado_janela,
            alvo_preciso_para_aba=validacao_ambiente.alvo_preciso_para_aba,
            esperar_aba_fechar=validacao_ambiente.esperar_aba_fechar,
            esperar_programa_fechar=validacao_ambiente.esperar_programa_fechar,
            executar_recursivo=executar_intencao,
        ),
        texto_original=texto_original,
    )
    if despacho_janelas.tratado:
        return despacho_janelas.retorno

    despacho_navegador = _executar_intencao_navegador(
        intent,
        params,
        texto_original,
        destino_val,
        ctx,
        DependenciasExecutorNavegador(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            abrir_url_com_validacao=validacao_ambiente.abrir_url_com_validacao,
            alvo_preciso_para_aba=validacao_ambiente.alvo_preciso_para_aba,
            esperar_aba_fechar=validacao_ambiente.esperar_aba_fechar,
            esperar_programa_fechar=validacao_ambiente.esperar_programa_fechar,
            executar_recursivo=executar_intencao,
        ),
    )
    if despacho_navegador.tratado:
        return despacho_navegador.retorno

    despacho_audio = _executar_intencao_audio(
        intent,
        params,
        destino_val,
        ctx,
        DependenciasExecutorAudio(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
        ),
    )
    if despacho_audio.tratado:
        return despacho_audio.retorno

    despacho_agenda = _executar_intencao_agenda(
        intent,
        params,
        texto_original,
        ctx,
        DependenciasExecutorAgenda(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
        ),
    )
    if despacho_agenda.tratado:
        return despacho_agenda.retorno

    despacho_informacoes = _executar_intencao_informacoes(
        intent,
        params,
        texto_original,
        ctx,
        DependenciasExecutorInformacoes(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            registrar_mente=_reg,
        ),
    )
    if despacho_informacoes.tratado:
        return despacho_informacoes.retorno

    despacho_sistema = _executar_intencao_sistema(
        intent,
        params,
        destino_val,
        ctx,
        DependenciasExecutorSistema(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
        ),
    )
    if despacho_sistema.tratado:
        return despacho_sistema.retorno

    despacho_musical = _executar_intencao_musical(
        intent,
        params,
        texto_original,
        ctx,
        DependenciasExecutorMusical(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            abrir_url_musical=rota_musical.abrir_detalhado,
            registrar_mente=_reg,
            falar_por_status=adaptador_resultado.falar_por_status,
            musica_leitura=ctx.get("_registro_musica_leitura_runtime"),
            musica_operacoes=ctx.get("_registro_musica_operacoes_runtime"),
        ),
    )
    if despacho_musical.tratado:
        return despacho_musical.retorno

    despacho_playlists = _executar_intencao_playlists(
        intent,
        params,
        texto_original,
        destino_val,
        ctx,
        DependenciasExecutorPlaylists(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            abrir_url_musical=rota_musical.abrir,
            contexto_fala=adaptador_resultado.contexto_fala,
            musica_leitura=ctx.get("_registro_musica_leitura_runtime"),
            musica_operacoes=ctx.get("_registro_musica_operacoes_runtime"),
        ),
    )
    if despacho_playlists.tratado:
        return despacho_playlists.retorno

    despacho_cancelamentos = _executar_intencao_cancelamentos(
        intent,
        ctx,
        DependenciasExecutorCancelamentos(
            marcar_resultado=adaptador_resultado.marcar_resultado
        ),
    )
    if despacho_cancelamentos.tratado:
        return despacho_cancelamentos.retorno

    despacho_integracoes = _executar_intencao_integracoes(
        intent,
        resultado,
        params,
        texto_original,
        destino_val,
        ctx,
        DependenciasExecutorIntegracoes(
            marcar_resultado=adaptador_resultado.marcar_resultado,
            falar_por_status=adaptador_resultado.falar_por_status,
            contexto_fala=adaptador_resultado.contexto_fala,
            iot=ctx.get("_registro_iot_runtime"),
            arquivos_leitura=ctx.get("_registro_arquivos_leitura_runtime"),
            arquivos_mutacao=ctx.get("_registro_arquivos_mutacao_runtime"),
        ),
    )
    if despacho_integracoes.tratado:
        return despacho_integracoes.retorno

    if callable(falar):
        falar(_escolher_fala_variada([
            "Eu não fechei tua intenção direito agora. Tenta falar de outro jeito pra mim.",
            "Me perdi um pouco aqui. Tenta falar de outro jeito.",
            "Não entendi direito. Repete pra mim com outras palavras.",
            "Quase peguei o fio, mas ele escapou. Me fala de novo sem pressa.",
        ]), "calma", 1)
    return True
