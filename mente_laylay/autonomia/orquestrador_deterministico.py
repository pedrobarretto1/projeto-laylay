"""Orquestracao do roteador deterministico da Laylay.

Este modulo nao guarda estado proprio. Ele recebe callbacks e estado do
`laylay.py`, preservando a regra de uma mente unica.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Mapping

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.cognicao.evidencia_operacional import autoriza_candidato_iot_direto
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_abrir_app_ou_site,
    detectar_confirmacao_porteiro,
    detectar_clima,
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
    normalizar_pedido_natural,
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
    mente_previa = _get(ctx, "mente_integrada_estado", {})
    ultimo_intent_previo = str(
        (mente_previa or {}).get("ultima_acao_intent")
        or (mente_previa or {}).get("ultima_intencao")
        or ""
    ).upper() if isinstance(mente_previa, Mapping) else ""
    texto_previo = str(texto or "").casefold()
    if ultimo_intent_previo == "VOLUME" and re.search(
        r"\b(?:aumenta|sobe|coloca|deixa|abaixa|diminui)?\b.*\b(?:maximo|máximo|minimo|mínimo)\b|\bno\s+talo\b",
        texto_previo,
    ):
        nivel = 0 if re.search(r"\b(?:minimo|mínimo)\b", texto_previo) else 100
        return {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": nivel, "referencia_contextual": True}}

    sugestao_indireta = _call(
        ctx,
        "detectar_sugestao_indireta",
        texto,
        _get(ctx, "mente_integrada_estado", {}),
    )
    if isinstance(sugestao_indireta, dict):
        return sugestao_indireta

    # O detector IoT conhece aliases, capacidades e parâmetros reais. Ele deve
    # poder apresentar um candidato antes do filtro genérico de conversa curta;
    # a guarda semântica impede que hipótese, negação ou comentário virem ação.
    normalizar = _get(ctx, "normalizar_texto")
    texto_normalizado_previo = (
        normalizar(texto) if callable(normalizar) else str(texto or "").casefold().strip()
    )
    texto_operacional_iot, modalidade_iot = normalizar_pedido_natural(texto_normalizado_previo)
    if autoriza_candidato_iot_direto(texto_operacional_iot, modalidade=modalidade_iot):
        candidato_iot = _call(
            ctx,
            "detectar_intencao_iot",
            texto_operacional_iot,
            _get(ctx, "mente_integrada_estado", {}),
        )
        if isinstance(candidato_iot, dict):
            return candidato_iot

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
    mente_atual = _get(ctx, "mente_integrada_estado", {})
    ultimo_intent = str((mente_atual or {}).get("ultima_acao_intent") or (mente_atual or {}).get("ultima_intencao") or "").upper() if isinstance(mente_atual, Mapping) else ""

    def params(**kwargs: Any) -> Dict[str, Any]:
        if destino == "pc_b":
            kwargs["target"] = "pc_b"
        return kwargs

    detectores: list[Callable[[], Dict[str, Any] | None]] = [
        lambda: _call(
            ctx,
            "detectar_intencao_iot",
            t,
            _get(ctx, "mente_integrada_estado", {}),
        ),
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
        lambda: detectar_clima(t, params_cb=params),
        lambda: detectar_volume_ou_midia(
            t,
            params_cb=params,
            contexto_musical_ativo=bool(_call(ctx, "contexto_musical_ativo", default=False)),
            contexto_volume_ativo=ultimo_intent == "VOLUME",
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


class DeteccaoDeterministicaRuntime:
    def __init__(
        self,
        *,
        namespace_getter: Callable[[], Dict[str, Any]],
        estado_getter: Callable[[], Dict[str, Any]],
        sites_diretos: Dict[str, Any],
        apps_map: Dict[str, Any],
    ) -> None:
        self.namespace_getter = namespace_getter
        self.estado_getter = estado_getter
        self.sites_diretos = sites_diretos
        self.apps_map = apps_map

    def detectar(self, texto: str) -> Dict[str, Any] | None:
        ns = self.namespace_getter() or {}

        # A agenda tem precedência sobre a execução imediata. Se houver uma
        # ação com prazo, resolvemos apenas o trecho operacional e envolvemos o
        # resultado em AGENDAR_ACAO. Assim nenhum detector usa os números do
        # horário como volume, brilho ou outro parâmetro.
        extrair_agendamento = ns.get("_extrair_acao_agendada_local")
        if callable(extrair_agendamento):
            agendamento = extrair_agendamento(texto)
            if isinstance(agendamento, dict) and agendamento.get("texto_acao"):
                acao_base = self.detectar(str(agendamento.get("texto_acao") or ""))
                intent_base = str((acao_base or {}).get("intent") or "").upper().strip()
                bloqueados = {
                    "", "AGENDAR_ACAO", "AGENDAR_LEMBRETE", "LISTAR_AGENDAMENTOS",
                    "CANCELAR_AGENDAMENTO", "SUGGEST_ACTION", "CANCELAR_ACAO",
                }
                if isinstance(acao_base, dict) and intent_base not in bloqueados:
                    params = dict(agendamento)
                    params["acao_agendada"] = acao_base
                    params["rota_original"] = "deterministico"
                    return {"intent": "AGENDAR_ACAO", "params": params}

        nomes = (
            "_normalizar_texto_com_apelidos", "_texto_conversa_casual_sem_acao",
            "_texto_bloqueia_playlist_agora", "_texto_social_curto", "_ignorar_token_solto",
            "_fluxo_prioritario_da_ia", "_texto_expresso_melhor_no_deterministico",
            "_texto_depende_de_contexto", "_limpar_destino_pc_b", "_target_from_params",
            "_limpar_nome_playlist", "_musica_estado_get", "_contexto_musical_ativo",
            "extrair_nome_playlist", "_extrair_intencao_abrir_app",
            "_detectar_playlist_nome_direto", "_normalizar_query_musical",
            "_detectar_intencao_iot", "_detectar_sugestao_indireta",
        )
        contexto = {nome.lstrip("_"): ns.get(nome) for nome in nomes}
        contexto.update({
            "normalizar_texto": ns.get("_normalizar_texto_com_apelidos"),
            "abas_sugeridas_fechar": ns.get("_abas_sugeridas_fechar", []),
            "mente_integrada_estado": self.estado_getter() or {},
            "sites_diretos": self.sites_diretos,
            "apps_map": self.apps_map,
            "detectar_intencao_iot": ns.get("_detectar_intencao_iot"),
            "detectar_sugestao_indireta": ns.get("_detectar_sugestao_indireta"),
        })
        return detectar_intencao_deterministica_mente(texto, contexto)


def criar_deteccao_deterministica_runtime(**kwargs: Any) -> DeteccaoDeterministicaRuntime:
    return DeteccaoDeterministicaRuntime(**kwargs)
