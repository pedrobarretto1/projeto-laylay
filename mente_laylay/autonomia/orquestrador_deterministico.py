"""Orquestracao do roteador deterministico da Laylay.

Este modulo nao guarda estado proprio. Ele recebe callbacks e estado do
`laylay.py`, preservando a regra de uma mente unica.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Mapping

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_abrir_app_ou_site,
    detectar_confirmacao_porteiro,
    detectar_email_notificacao_briefing,
    detectar_fechar_alvo,
    detectar_janela_contextual,
    detectar_janela_explicita,
    detectar_musica_ou_playlist_direta,
    detectar_organizacao_desktop,
    detectar_playlist_contextual_musica_atual,
    detectar_playlist_laylay,
    detectar_playlist_usuario,
    detectar_trava_pc,
    detectar_url_visual,
    detectar_volume_ou_midia,
    detectar_web_e_youtube,
    preparar_entrada_deterministica,
)


def _get(ctx: Mapping[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default) if isinstance(ctx, Mapping) else default


def _call(ctx: Mapping[str, Any], nome: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    fn = _get(ctx, nome)
    if callable(fn):
        return fn(*args, **kwargs)
    return default


def detectar_intencao_deterministica_mente(texto: str, ctx: Mapping[str, Any]) -> Dict[str, Any] | None:
    """Executa a cadeia deterministica em ordem, usando dependencias injetadas."""
    preparo = preparar_entrada_deterministica(
        texto,
        normalizar_texto=_get(ctx, "normalizar_texto"),
        texto_conversa_casual_sem_acao=_get(ctx, "texto_conversa_casual_sem_acao"),
        texto_bloqueia_playlist_agora=_get(ctx, "texto_bloqueia_playlist_agora"),
        texto_social_curto=_get(ctx, "texto_social_curto"),
        ignorar_token_solto=_get(ctx, "ignorar_token_solto"),
        fluxo_prioritario_da_ia=_get(ctx, "fluxo_prioritario_da_ia"),
        texto_expresso_melhor_no_deterministico=_get(ctx, "texto_expresso_melhor_no_deterministico"),
        texto_depende_de_contexto=_get(ctx, "texto_depende_de_contexto"),
        limpar_destino_pc_b=_get(ctx, "limpar_destino_pc_b"),
    )
    if preparo.get("status") == "intent":
        return preparo.get("resultado")
    if preparo.get("status") != "ok":
        return None

    bruto = str(preparo.get("bruto") or "").strip()
    t = str(preparo.get("texto_normalizado") or "").strip()
    t_sem_destino = str(preparo.get("texto_sem_destino") or "").strip()
    bruto_sem_destino = str(_call(ctx, "limpar_destino_pc_b", bruto, default=bruto) or bruto).strip()
    destino = _call(ctx, "target_from_params", {}, bruto, default="pc_a")

    def params(**kwargs: Any) -> Dict[str, Any]:
        if destino == "pc_b":
            kwargs["target"] = "pc_b"
        return kwargs

    detectores: list[Callable[[], Dict[str, Any] | None]] = [
        lambda: detectar_url_visual(t, bruto, params_cb=params),
        lambda: detectar_playlist_contextual_musica_atual(
            t_sem_destino,
            params_cb=params,
            limpar_nome_playlist=_get(ctx, "limpar_nome_playlist"),
            ultima_playlist=_call(ctx, "musica_estado_get", "ultima_playlist", default=""),
        ),
        lambda: detectar_confirmacao_porteiro(
            t_sem_destino,
            params_cb=params,
            ha_abas_sugeridas=bool(_get(ctx, "abas_sugeridas_fechar")),
        ),
        lambda: detectar_email_notificacao_briefing(t, params_cb=params),
        lambda: detectar_volume_ou_midia(
            t,
            params_cb=params,
            contexto_musical_ativo=bool(_call(ctx, "contexto_musical_ativo", default=False)),
        ),
        lambda: detectar_playlist_laylay(
            t,
            params_cb=params,
            limpar_nome_playlist=_get(ctx, "limpar_nome_playlist"),
        ),
        lambda: detectar_playlist_usuario(
            t,
            bruto,
            params_cb=params,
            limpar_nome_playlist=_get(ctx, "limpar_nome_playlist"),
            extrair_nome_playlist=_get(ctx, "extrair_nome_playlist"),
        ),
        lambda: detectar_organizacao_desktop(t, params_cb=params),
        lambda: detectar_janela_contextual(
            t,
            params_cb=params,
            estado_mental=_get(ctx, "mente_integrada_estado", {}),
            texto_depende_de_contexto=_get(ctx, "texto_depende_de_contexto"),
        ),
        lambda: detectar_janela_explicita(t, t_sem_destino, params_cb=params),
        lambda: detectar_abrir_app_ou_site(
            bruto,
            params_cb=params,
            extrair_intencao_abrir_app=_get(ctx, "extrair_intencao_abrir_app"),
        ),
        lambda: detectar_musica_ou_playlist_direta(
            t,
            t_sem_destino,
            bruto,
            params_cb=params,
            detectar_playlist_nome_direto=_get(ctx, "detectar_playlist_nome_direto"),
            normalizar_query_musical=_get(ctx, "normalizar_query_musical"),
        ),
        lambda: detectar_fechar_alvo(
            t_sem_destino,
            params_cb=params,
            sites_diretos=_get(ctx, "sites_diretos"),
            apps_map=_get(ctx, "apps_map"),
        ),
        lambda: detectar_web_e_youtube(
            t,
            t_sem_destino,
            params_cb=params,
            sites_diretos=_get(ctx, "sites_diretos"),
        ),
        lambda: detectar_intencao_arquivos(
            bruto_sem_destino,
            params_cb=params,
            estado_mental=_get(ctx, "mente_integrada_estado", {}),
            normalizar_texto=_get(ctx, "normalizar_texto"),
        ),
        lambda: detectar_trava_pc(t, params_cb=params),
    ]

    for detector in detectores:
        resultado = detector()
        if resultado:
            return resultado
    return None
