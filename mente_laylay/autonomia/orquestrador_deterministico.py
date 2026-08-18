"""Orquestracao do roteador deterministico da Laylay.

Este modulo nao guarda estado proprio. Ele recebe callbacks e estado do
`laylay.py`, preservando a regra de uma mente unica.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Mapping

from mente_laylay.integracao.registro_iot import PortaIoT

from mente_laylay.arquivos.roteador_arquivos import detectar_intencao_arquivos
from mente_laylay.cognicao.evidencia_operacional import (
    autoriza_candidato_iot_direto,
    bloqueia_controle_iot_por_modalidade,
    detectar_consulta_lista_iot,
)
from mente_laylay.autonomia.roteador_deterministico import (
    detectar_abrir_app_ou_site,
    detectar_confirmacao_porteiro,
    detectar_clima,
    detectar_consulta_abas,
    detectar_consulta_aprendizados,
    detectar_continuacao_resultado_web,
    detectar_email_notificacao_briefing,
    detectar_fechar_alvo,
    detectar_janela_contextual,
    detectar_janela_explicita,
    detectar_musica_ou_playlist_direta,
    detectar_movimento_playlist,
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
from mente_laylay.cognicao.intencao_visual_jogo import detectar_pedido_visao_jogo
from mente_laylay.cognicao.referencias_linguagem import (
    extrair_indice_referencia_ordinal,
    separar_alvo_e_complemento_foco,
    valor_e_referencia_contextual,
)
from mente_laylay.cognicao.modalidade_turno import analisar_protecao_operacional
from mente_laylay.memoria_mental.continuidade_geral import (
    resolver_continuacao_aditiva,
    selecionar_referente_saliente,
)


def _get(ctx: Mapping[str, Any], nome: str, default: Any = None) -> Any:
    return ctx.get(nome, default) if isinstance(ctx, Mapping) else default


def _call(ctx: Mapping[str, Any], nome: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    fn = _get(ctx, nome)
    if callable(fn):
        return fn(*args, **kwargs)
    return default


def _detectar_elipse_espacial_confirmada(
    texto: str,
    mente: Mapping[str, Any] | None,
) -> Dict[str, Any] | None:
    """Materializa somente a elipse que o planejamento atual já autorizou."""
    if str(texto or "").casefold().strip() != "esquerda":
        return None
    estado = dict(mente or {}) if isinstance(mente, Mapping) else {}
    turno = dict(estado.get("turno_atual") or {})
    if str(turno.get("texto") or "").casefold().strip() != "esquerda":
        return None
    if not bool(turno.get("autoriza_execucao")):
        return None
    if bool(turno.get("requer_esclarecimento")):
        return None

    elipse = dict(turno.get("elipse_operacional") or {})
    if (
        str(elipse.get("tipo") or "") != "posicionamento_janela"
        or str(elipse.get("direcao") or "") != "left"
        or str(elipse.get("alvo_requerido") or "") != "app"
    ):
        return None

    referencia = dict(turno.get("referencia_resolvida") or {})
    tipo = str(referencia.get("tipo") or "").casefold()
    nome = str(referencia.get("nome") or "").strip()
    if tipo != "app" or not nome:
        return None

    return {
        "intent": "ORGANIZAR_DESKTOP",
        "params": {
            "left": nome,
            "modo": "posicionar",
            "referencia_contextual": True,
            "referencia_contextual_fonte": "turno_atual.referencia_resolvida",
            "direcao_original": "esquerda",
        },
    }


def detectar_intencao_deterministica_mente(texto: str, ctx: Mapping[str, Any]) -> Dict[str, Any] | None:
    """Executa a cadeia deterministica em ordem, usando dependencias injetadas."""
    # Esta decisão usa obrigatoriamente a fala original. Normalizações feitas
    # mais abaixo podem remover justamente o ``não`` ou a moldura ``como eu
    # faria``; uma ação física jamais deve ser autorizada a partir desse texto
    # já reescrito.
    bloqueio_iot_original = bloqueia_controle_iot_por_modalidade(texto)

    def _candidato_iot_seguro(texto_detector: str) -> Dict[str, Any] | None:
        candidato = _call(
            ctx,
            "detectar_intencao_iot",
            texto_detector,
            _get(ctx, "mente_integrada_estado", {}),
        )
        if not isinstance(candidato, dict):
            return None
        intent = str(candidato.get("intent") or "").upper().strip()
        if intent == "IOT_CONTROL" and bloqueio_iot_original:
            return None
        return candidato

    # Consulta objetiva e sem efeito colateral. Ela não depende do runtime IoT
    # já ter sido injetado e vence os filtros genéricos de pergunta/conversa.
    consulta_lista_iot = detectar_consulta_lista_iot(texto)
    if consulta_lista_iot:
        return consulta_lista_iot

    mente_previa = _get(ctx, "mente_integrada_estado", {})
    elipse_espacial = _detectar_elipse_espacial_confirmada(texto, mente_previa)
    if elipse_espacial:
        return elipse_espacial

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

    contexto_jogo = dict(_call(ctx, "modo_jogo_contexto", default={}) or {})
    contexto_jogo["analise_visual_recente"] = bool(
        _call(ctx, "visao_jogo_tem_analise_recente", default=False)
    )
    pedido_visao_jogo = detectar_pedido_visao_jogo(texto, contexto_jogo)
    if pedido_visao_jogo:
        return pedido_visao_jogo

    # O detector IoT conhece aliases, capacidades e parâmetros reais. Ele deve
    # poder apresentar um candidato antes do filtro genérico de conversa curta;
    # a guarda semântica impede que hipótese, negação ou comentário virem ação.
    normalizar = _get(ctx, "normalizar_texto")
    texto_normalizado_previo = (
        normalizar(texto) if callable(normalizar) else str(texto or "").casefold().strip()
    )
    texto_operacional_iot, modalidade_iot = normalizar_pedido_natural(texto_normalizado_previo)
    # Listagem e estado são consultas sem efeito colateral. Elas costumam ter
    # forma de pergunta e, por isso, o filtro casual abaixo pode encerrar a
    # detecção antes da cadeia de especialistas. Controle físico continua
    # dependendo das guardas de modalidade logo abaixo.
    candidato_iot_leitura = _candidato_iot_seguro(texto_operacional_iot)
    if (
        isinstance(candidato_iot_leitura, dict)
        and str(candidato_iot_leitura.get("intent") or "").upper().strip()
        in {"IOT_LIST", "IOT_STATUS"}
    ):
        return candidato_iot_leitura
    if autoriza_candidato_iot_direto(texto_operacional_iot, modalidade=modalidade_iot):
        candidato_iot = candidato_iot_leitura or _candidato_iot_seguro(texto_operacional_iot)
        if isinstance(candidato_iot, dict):
            return candidato_iot

    # A posse/ordem de uma curadoria precisa ser resolvida antes do recurso
    # genérico ``playlist``. Caso contrário, ``sua primeira playlist`` é
    # capturada como uma lista do usuário e perde justamente a identidade e o
    # ordinal. Só promovemos aqui uma lista com alvo concreto ou uma ação
    # própria inequívoca; negação, hipótese e pergunta de instrução continuam
    # bloqueando qualquer execução.
    playlist_laylay_previa = ""
    if isinstance(mente_previa, Mapping) and ultimo_intent_previo in {
        "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY",
    }:
        playlist_laylay_previa = str(
            mente_previa.get("ultima_acao_alvo")
            or mente_previa.get("ultimo_alvo")
            or ""
        ).strip()
    candidato_playlist_laylay = detectar_playlist_laylay(
        texto_operacional_iot,
        params_cb=lambda **kwargs: kwargs,
        limpar_nome_playlist=(
            _get(ctx, "limpar_nome_playlist")
            if callable(_get(ctx, "limpar_nome_playlist"))
            else lambda valor: str(valor or "").strip()
        ),
        playlist_laylay_recente=playlist_laylay_previa,
        detectar_nome_direto=_get(ctx, "detectar_playlist_laylay_nome_direto"),
    )
    if isinstance(candidato_playlist_laylay, dict):
        intent_laylay = str(candidato_playlist_laylay.get("intent") or "").upper()
        params_laylay = dict(candidato_playlist_laylay.get("params") or {})
        alvo_laylay = str(
            params_laylay.get("nome_playlist")
            or params_laylay.get("origem")
            or ""
        ).strip()
        nome_catalogado = ""
        detectar_nome_laylay = _get(ctx, "detectar_playlist_laylay_nome_direto")
        if callable(detectar_nome_laylay) and alvo_laylay:
            try:
                nome_catalogado = str(detectar_nome_laylay(alvo_laylay) or "").strip()
            except Exception:
                nome_catalogado = ""
        leitura_especifica = (
            intent_laylay == "LAYLAY_PLAYLIST_LIST"
            and bool(alvo_laylay)
            and (alvo_laylay.startswith("#") or bool(nome_catalogado))
        )
        protecao_laylay = analisar_protecao_operacional(
            texto,
            normalizar_texto=normalizar if callable(normalizar) else None,
        )
        acao_segura = (
            intent_laylay in {"LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY"}
            and not protecao_laylay.get("bloqueia_execucao")
        )
        if leitura_especifica or acao_segura:
            return candidato_playlist_laylay

    # O catálogo de recursos conhece seus dados reais e o intent de leitura.
    # Perguntas naturais de consulta precisam chegar aqui antes dos filtros
    # genéricos de conversa, sem conceder nenhuma operação de escrita.
    consulta_recurso = _call(ctx, "resolver_consulta_recurso_local", texto)
    if isinstance(consulta_recurso, dict):
        return consulta_recurso

    # Consultas objetivas de leitura não precisam de autorização operacional e
    # não podem ser descartadas por um classificador genérico de conversa. A
    # cadeia completa continua abaixo para continuações e ações com efeito.
    consulta_email = detectar_email_notificacao_briefing(
        texto_normalizado_previo,
        params_cb=lambda **kwargs: kwargs,
        contexto_email_ativo=False,
    )
    if (
        isinstance(consulta_email, dict)
        and str(consulta_email.get("intent") or "").upper() == "EMAIL_READ"
        and modalidade_iot != "deliberativo"
    ):
        return consulta_email

    consulta_clima = detectar_clima(
        texto_normalizado_previo,
        params_cb=lambda **kwargs: kwargs,
    )
    if consulta_clima and modalidade_iot != "deliberativo":
        return consulta_clima

    # Consultas e controles explícitos do player precisam vencer o filtro
    # conversacional genérico aplicado por ``preparar_entrada_deterministica``.
    # Sem esta precedência, frases como "vai para a próxima faixa" podiam ser
    # entregues à LLM quando a aba visível não era a do player. A modalidade
    # continua sendo a autoridade para mutações: hipótese, negação e pergunta
    # instrucional não ganham execução aqui.
    candidato_midia_previo = detectar_volume_ou_midia(
        texto_normalizado_previo,
        params_cb=lambda **kwargs: kwargs,
        contexto_musical_ativo=bool(
            _call(ctx, "contexto_musical_ativo", default=False)
        ),
        contexto_volume_ativo=ultimo_intent_previo == "VOLUME",
    )
    if isinstance(candidato_midia_previo, dict):
        intent_midia_previo = str(
            candidato_midia_previo.get("intent") or ""
        ).upper().strip()
        protecao_midia = analisar_protecao_operacional(
            texto,
            normalizar_texto=normalizar if callable(normalizar) else None,
        )
        if intent_midia_previo == "MUSIC_STATUS":
            return candidato_midia_previo
        if (
            intent_midia_previo in {"MEDIA_CONTROL", "VOLUME"}
            and modalidade_iot != "deliberativo"
            and not protecao_midia.get("bloqueia_execucao")
        ):
            return candidato_midia_previo

    consulta_abas = detectar_consulta_abas(
        texto_normalizado_previo,
        params_cb=lambda **kwargs: kwargs,
    )
    if consulta_abas and modalidade_iot != "deliberativo":
        return consulta_abas

    # Uma referência ordinal pertence à busca web confirmada mais recente.
    # Ela precisa ser resolvida antes da busca local: caso contrário, um
    # resultado antigo de arquivos podia sequestrar ``abre o primeiro
    # resultado`` logo após uma pesquisa na internet.
    continuacao_resultado_web = detectar_continuacao_resultado_web(
        texto_normalizado_previo,
        dict(mente_previa or {}) if isinstance(mente_previa, Mapping) else {},
        params_cb=lambda **kwargs: kwargs,
    )
    if continuacao_resultado_web:
        return continuacao_resultado_web

    # O roteador de arquivos possui marcadores locais mais específicos. Ele
    # precisa ter a primeira palavra em frases como ``pesquisa o arquivo X``;
    # se não houver marcador local, ele cede e a pesquisa web logo abaixo
    # continua responsável por ``pesquisa por documentação do Python``.
    consulta_arquivo = detectar_intencao_arquivos(
        texto,
        params_cb=lambda **kwargs: kwargs,
        estado_mental=mente_previa if isinstance(mente_previa, Mapping) else {},
        normalizar_texto=normalizar if callable(normalizar) else None,
    )
    if (
        isinstance(consulta_arquivo, dict)
        and str(consulta_arquivo.get("intent") or "").upper()
        in {"FILE_SEARCH", "FILE_OPEN_RESULT"}
    ):
        return consulta_arquivo

    # Pesquisas explícitas são consultas operacionais e precisam vencer o
    # filtro genérico de conversa. Antes desta barreira, a forma natural
    # ``Pesquisa por documentação do Python`` podia ser classificada como
    # conversa e nunca chegar ao mesmo detector web usado mais abaixo.
    consulta_web = detectar_web_e_youtube(
        texto_normalizado_previo,
        texto_normalizado_previo,
        params_cb=lambda **kwargs: kwargs,
        sites_diretos=_get(ctx, "sites_diretos"),
    )
    if (
        isinstance(consulta_web, dict)
        and str(consulta_web.get("intent") or "").upper() == "SEARCH"
        and modalidade_iot != "deliberativo"
    ):
        return consulta_web

    consulta_aprendizados = detectar_consulta_aprendizados(
        texto_normalizado_previo,
        params_cb=lambda **kwargs: kwargs,
    )
    if consulta_aprendizados:
        return consulta_aprendizados

    referente_atual = selecionar_referente_saliente(
        dict(mente_previa or {}) if isinstance(mente_previa, Mapping) else {},
        ttl_s=600.0,
    )
    contexto_email_ativo = bool(
        str(referente_atual.get("dominio") or "") == "email"
        and str(referente_atual.get("intent") or "").upper() == "EMAIL_READ"
        and str(referente_atual.get("status") or "") == "emails_lidos"
        and referente_atual.get("confirmado") is not False
    )
    if contexto_email_ativo:
        seguimento_email = detectar_email_notificacao_briefing(
            texto_normalizado_previo,
            params_cb=lambda **kwargs: kwargs,
            contexto_email_ativo=True,
        )
        if seguimento_email:
            return seguimento_email

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
    playlist_laylay_recente = ""
    if isinstance(mente_atual, Mapping) and ultimo_intent in {
        "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY",
    }:
        playlist_laylay_recente = str(
            mente_atual.get("ultima_acao_alvo")
            or mente_atual.get("ultimo_alvo")
            or ""
        ).strip()

    def params(**kwargs: Any) -> Dict[str, Any]:
        if destino == "pc_b":
            kwargs["target"] = "pc_b"
        return kwargs

    # Elipses curtas não devem disputar entidades soltas na memória semântica.
    # A continuidade oficial já sabe qual foi a ação operacional confirmada e
    # cada intent declara quais parâmetros podem ser herdados com segurança.
    continuacao_aditiva = resolver_continuacao_aditiva(
        dict(mente_atual or {}) if isinstance(mente_atual, Mapping) else {},
        texto=t_sem_destino,
    )
    if continuacao_aditiva:
        params_continuacao = dict(continuacao_aditiva.get("params") or {})
        return {
            "intent": str(continuacao_aditiva.get("intent") or ""),
            "params": params(**params_continuacao),
        }

    estrutura_arquivo = (
        dict(mente_atual.get("ultima_estrutura_arquivo_params") or {})
        if isinstance(mente_atual, Mapping)
        and isinstance(mente_atual.get("ultima_estrutura_arquivo_params"), Mapping)
        else {}
    )
    selecao_resultado_arquivo = bool(
        str(estrutura_arquivo.get("tipo") or "") == "pesquisa_semantica"
        and extrair_indice_referencia_ordinal(t_sem_destino) is not None
    )
    ultima_intencao_arquivo = str(
        mente_atual.get("ultima_acao_intent")
        or mente_atual.get("ultima_intencao")
        or ""
    ).upper() if isinstance(mente_atual, Mapping) else ""
    abertura_arquivo_contextual = False
    abertura_candidata = re.fullmatch(
        r"(?:abre|abra|abrir|mostra|mostre)\s+(?P<referencia>.+)",
        t_sem_destino.rstrip(" .,!?:;"),
        flags=re.IGNORECASE,
    )
    if abertura_candidata and str(estrutura_arquivo.get("tipo") or "").casefold() == "arquivo":
        referencia_limpa, _pediu_foco = separar_alvo_e_complemento_foco(
            abertura_candidata.group("referencia") or ""
        )
        abertura_arquivo_contextual = bool(
            valor_e_referencia_contextual(referencia_limpa)
            and ultima_intencao_arquivo in {
                "CREATE_FILE", "FILE_OPEN_RESULT", "FILE_SEARCH", "FILE_TRANSACTION",
            }
        )

    detectores: list[Callable[[], Dict[str, Any] | None]] = [
        lambda: _candidato_iot_seguro(t),
        lambda: detectar_url_visual(t, bruto, params_cb=params),
        # Posicionamento espacial e organizacao da area de trabalho precisam
        # vencer musica e abertura generica. "Steam na esquerda" descreve uma
        # janela e nunca uma faixa chamada "steam na esquerda".
        lambda: detectar_organizacao_desktop(t, params_cb=params),
        # Vocabulário estrutural explícito precisa vencer o detector musical:
        # "coloca um arquivo de texto..." não é uma busca por uma música
        # chamada "arquivo de texto". A guarda estreita preserva playlists.
        lambda: detectar_intencao_arquivos(
            bruto_sem_destino,
            params_cb=params,
            estado_mental=_get(ctx, "mente_integrada_estado", {}),
            normalizar_texto=_get(ctx, "normalizar_texto"),
        ) if abertura_arquivo_contextual or re.search(
            r"\b(?:arquivo|pasta|documento|diretorio|diretório|txt|"
            r"escreve|escreva|escrever|grava|grave|gravar)\b",
            t,
        ) else None,
        # Uma seleção ordinal pertence primeiro à habilidade que publicou a
        # lista recente. Sem esta precedência, "abra o primeiro" virava a
        # tentativa de abrir um aplicativo literalmente chamado "primeiro".
        lambda: detectar_intencao_arquivos(
            t_sem_destino,
            params_cb=params,
            estado_mental=mente_atual,
            normalizar_texto=_get(ctx, "normalizar_texto"),
        ) if selecao_resultado_arquivo else None,
        lambda: detectar_movimento_playlist(
            t_sem_destino,
            params_cb=params,
            limpar_nome_playlist=_get(ctx, "limpar_nome_playlist"),
        ),
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
        lambda: detectar_email_notificacao_briefing(
            t,
            params_cb=params,
            contexto_email_ativo=contexto_email_ativo,
        ),
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
            playlist_laylay_recente=playlist_laylay_recente,
            detectar_nome_direto=_get(ctx, "detectar_playlist_laylay_nome_direto"),
        ),
        lambda: detectar_playlist_usuario(
            t,
            bruto,
            params_cb=params,
            limpar_nome_playlist=_get(ctx, "limpar_nome_playlist"),
            extrair_nome_playlist=_get(ctx, "extrair_nome_playlist"),
            detectar_playlist_nome_direto=_get(ctx, "detectar_playlist_nome_direto"),
        ),
        lambda: detectar_janela_contextual(
            t,
            params_cb=params,
            estado_mental=_get(ctx, "mente_integrada_estado", {}),
            texto_depende_de_contexto=_get(ctx, "texto_depende_de_contexto"),
        ),
        lambda: detectar_janela_explicita(t, t_sem_destino, params_cb=params),
        lambda: detectar_abrir_app_ou_site(
            t_sem_destino,
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
            # Invariante final: nenhum detector atual ou futuro consegue
            # contornar a modalidade original de um controle físico.
            if (
                str(resultado.get("intent") or "").upper().strip() == "IOT_CONTROL"
                and bloqueio_iot_original
            ):
                continue
            if str(resultado.get("intent") or "").upper().strip() == "ORGANIZAR_DESKTOP":
                params_layout = dict(resultado.get("params") or {})
                chaves_layout = ("left", "right", "esquerda", "direita")
                precisa_referente = any(
                    bool(str(params_layout.get(chave) or "").strip())
                    and valor_e_referencia_contextual(
                        str(params_layout.get(chave) or "")
                    )
                    for chave in chaves_layout
                )
                if precisa_referente:
                    referente_app = selecionar_referente_saliente(
                        dict(mente_atual or {}) if isinstance(mente_atual, Mapping) else {},
                        dominio="app",
                        ttl_s=300.0,
                    )
                    alvo_app = str(referente_app.get("alvo") or "").strip()
                    if alvo_app:
                        for chave in chaves_layout:
                            valor = str(params_layout.get(chave) or "").strip()
                            if valor and valor_e_referencia_contextual(valor):
                                params_layout[f"{chave}_original"] = valor
                                params_layout[chave] = alvo_app
                                params_layout["referencia_contextual"] = True
                        resultado = {**resultado, "params": params_layout}
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
        iot: PortaIoT | None = None,
    ) -> None:
        self.namespace_getter = namespace_getter
        self.estado_getter = estado_getter
        self.sites_diretos = sites_diretos
        self.apps_map = apps_map
        self.iot = iot

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
            "_detectar_playlist_laylay_nome_direto",
            "_detectar_sugestao_indireta",
            "_resolver_consulta_recurso_local",
        )
        contexto = {nome.lstrip("_"): ns.get(nome) for nome in nomes}
        contexto.update({
            "normalizar_texto": ns.get("_normalizar_texto_com_apelidos"),
            "abas_sugeridas_fechar": ns.get("_abas_sugeridas_fechar", []),
            "mente_integrada_estado": self.estado_getter() or {},
            "sites_diretos": self.sites_diretos,
            "apps_map": self.apps_map,
            "detectar_intencao_iot": getattr(self.iot, "detectar", None),
            "detectar_sugestao_indireta": ns.get("_detectar_sugestao_indireta"),
            "modo_jogo_contexto": getattr(ns.get("_modo_jogo_runtime"), "contexto_atual", None),
            "visao_jogo_tem_analise_recente": getattr(
                ns.get("_registro_visao_jogo_leitura_runtime"),
                "tem_analise_recente", None,
            ),
        })
        return detectar_intencao_deterministica_mente(texto, contexto)


def criar_deteccao_deterministica_runtime(**kwargs: Any) -> DeteccaoDeterministicaRuntime:
    return DeteccaoDeterministicaRuntime(**kwargs)
