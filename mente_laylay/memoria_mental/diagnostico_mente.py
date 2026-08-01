"""Retrato seguro e legível do funcionamento atual da mente única."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Mapping

from mente_laylay.memoria_mental.continuidade_geral import selecionar_continuidade_por_classe


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or ""))
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", base.casefold()).strip()


def _codigo_seguro(valor: Any, limite: int = 96) -> str:
    texto = _normalizar(str(valor or ""))
    texto = re.sub(r"https?://\S+|[a-z]:\\\S+|[/\\][^\s]+", "", texto)
    texto = re.sub(r"[^a-z0-9_.: -]+", "", texto)
    return re.sub(r"\s+", "_", texto).strip("_.:-")[:limite]


def detectar_pedido_diagnostico_mente(texto: str) -> bool:
    """Aceita pedidos explícitos sem confundir conversa emocional com diagnóstico."""
    t = _normalizar(texto)
    comandos_barra = {
        "/diagnostico", "/diagnostico mente", "/diagnostico mete",
        "/diagostico", "/diagostico mente", "/diagostico mete",
        "/dignostico", "/dignostico mente", "/dignostico mete",
        "/status interno", "/status mente",
    }
    if t in comandos_barra:
        return True
    expressoes = (
        "diagnostico da mente",
        "diagnostico interno",
        "status interno da laylay",
        "status dos modulos",
        "verifique seus modulos",
        "verifica seus modulos",
        "mostre seus modulos",
        "mostra seus modulos",
    )
    return any(expressao in t for expressao in expressoes)


def construir_diagnostico_mente(
    estado: Mapping[str, Any] | None,
    saude: Mapping[str, Any] | None,
    rede_associativa: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    dominios = dict(estado or {})
    mental = dict(dominios.get("mental") or {})
    conversa = dict(dominios.get("conversacional") or {})
    percepcao = dict(dominios.get("percepcao") or {})
    continuidades = dict(dominios.get("continuidades") or {})
    turno = dict(mental.get("turno_atual") or {})
    plano = dict(mental.get("plano_turno_atual") or {})
    modulos = {str(nome): dict(registro or {}) for nome, registro in dict(saude or {}).items()}
    totais = {"saudavel": 0, "degradado": 0, "indisponivel": 0}
    problemas = []
    for nome, registro in sorted(modulos.items()):
        status = str(registro.get("status") or "indisponivel")
        if status not in totais:
            status = "indisponivel"
        totais[status] += 1
        if status != "saudavel":
            problemas.append({
                "modulo": nome,
                "status": status,
                "ausentes": list(registro.get("ausentes") or []),
            })

    continuidade_oficial = dict(mental.get("continuidade_geral") or {})
    acao_oficial = selecionar_continuidade_por_classe(mental, classe="operacional")
    ultima_acao = {
        "intent": acao_oficial.get("intent") or mental.get("ultima_acao_intent") or mental.get("ultima_intencao") or "",
        "alvo": acao_oficial.get("alvo") or mental.get("ultima_acao_alvo") or mental.get("ultimo_alvo") or "",
        "status": acao_oficial.get("status") or mental.get("ultima_acao_status") or "",
        "confirmado": mental.get("ultima_acao_confirmada"),
    }

    pendencias = sum(
        1
        for valor in continuidades.values()
        if bool(valor) and valor not in ({}, [], "", "NONE", "none")
    )
    pendencia_acao = dict(mental.get("pendencia_acao_canonica") or {})
    if pendencia_acao.get("status") in {"ativa", "em_processamento"}:
        pendencias += 1
    contexto_sistema = dict(percepcao.get("contexto_sistema") or {})
    aba_ativa = dict(percepcao.get("aba_ativa") or {})
    metricas_brutas = dict(mental.get("diagnostico_metricas") or {})
    prompts_brutos = dict(mental.get("diagnostico_prompts") or {})
    latencias = {}
    for nome, registro in metricas_brutas.items():
        if not isinstance(registro, Mapping):
            continue
        chave = _codigo_seguro(nome, 64)
        if not chave:
            continue
        latencias[chave] = {
            "ultimo_ms": round(float(registro.get("ultimo_ms") or 0.0), 2),
            "media_ms": round(float(registro.get("media_ms") or 0.0), 2),
            "max_ms": round(float(registro.get("max_ms") or 0.0), 2),
            "amostras": int(registro.get("amostras") or 0),
            "falhas": int(registro.get("falhas") or 0),
            "orcamento_ms": round(float(registro.get("orcamento_ms") or 0.0), 2),
            "excedeu_orcamento": bool(registro.get("excedeu_orcamento", False)),
            "excessos": int(registro.get("excessos") or 0),
        }
    tamanhos_prompt = {}
    for nome, registro in prompts_brutos.items():
        if not isinstance(registro, Mapping):
            continue
        chave = _codigo_seguro(nome, 64)
        if chave:
            tamanhos_prompt[chave] = {
                "ultimo_chars": int(registro.get("ultimo_chars") or 0),
                "media_chars": round(float(registro.get("media_chars") or 0.0), 2),
                "max_chars": int(registro.get("max_chars") or 0),
                "amostras": int(registro.get("amostras") or 0),
            }
    falhas = []
    for item in list(mental.get("diagnostico_falhas") or [])[-8:]:
        if not isinstance(item, Mapping):
            continue
        falhas.append({
            "componente": _codigo_seguro(item.get("componente"), 64),
            "codigo": _codigo_seguro(item.get("codigo"), 80),
            "tipo": _codigo_seguro(item.get("tipo"), 48),
            "classe": _codigo_seguro(item.get("classe"), 24) or "nao_classificada",
            "impacto": _codigo_seguro(item.get("impacto"), 24) or "servico",
            "fallback": _codigo_seguro(item.get("fallback"), 64) or "nenhum",
            "ts": float(item.get("ts") or 0.0),
        })
    servicos_background = []
    for nome, item in dict(mental.get("diagnostico_servicos") or {}).items():
        if not isinstance(item, Mapping):
            continue
        servicos_background.append({
            "nome": _codigo_seguro(nome, 64),
            "estado": _codigo_seguro(item.get("estado"), 32) or "desconhecido",
            "tentativa": int(item.get("tentativa") or 0),
            "atraso_s": round(float(item.get("atraso_s") or 0.0), 2),
            "fallback": _codigo_seguro(item.get("fallback"), 64) or "nenhum",
            "quedas": int(item.get("quedas") or 0),
            "reinicios": int(item.get("reinicios") or 0),
            "falhas_inicializacao": int(item.get("falhas_inicializacao") or 0),
            "orfaos": int(item.get("orfaos") or 0),
            "ts": float(item.get("ts") or 0.0),
        })
    servicos_background.sort(key=lambda item: str(item.get("nome") or ""))
    # Uma queda já seguida por um evento saudável continua visível nos
    # contadores de quedas/reinícios, mas não deve aparecer como falha atual.
    # Isso evita que o diagnóstico assuste o usuário depois da recuperação.
    servicos_por_nome = {
        str(item.get("nome") or ""): item for item in servicos_background
    }
    falhas_ativas = []
    falhas_recuperadas = 0
    for falha in falhas:
        componente = str(falha.get("componente") or "")
        servico = (
            servicos_por_nome.get(componente.removeprefix("servico_"))
            if componente.startswith("servico_") else None
        )
        recuperada = bool(
            falha.get("codigo") == "queda_background"
            and servico
            and servico.get("estado") in {"ativo", "finalizado", "encerrado"}
            and float(servico.get("ts") or 0.0) > 0.0
            and float(servico.get("ts") or 0.0) >= float(falha.get("ts") or 0.0) > 0.0
        )
        if recuperada:
            falhas_recuperadas += 1
        else:
            falhas_ativas.append(falha)
    falhas = falhas_ativas
    falhas_por_classe = {
        classe: sum(1 for item in falhas if item.get("classe") == classe)
        for classe in ("esperada", "degradacao", "defeito", "nao_classificada")
    }
    decisoes = []
    for item in list(mental.get("diagnostico_decisoes") or [])[-8:]:
        if not isinstance(item, Mapping):
            continue
        decisoes.append({
            "componente": _codigo_seguro(item.get("componente"), 64),
            "acao": _codigo_seguro(item.get("acao"), 48),
            "categoria": _codigo_seguro(item.get("categoria"), 64),
            "motivos": [
                _codigo_seguro(motivo, 96)
                for motivo in list(item.get("motivos") or [])[:4]
                if _codigo_seguro(motivo, 96)
            ],
        })
    iniciativa_bruta = dict(mental.get("iniciativa_autonoma") or {})
    contadores_iniciativa = dict(iniciativa_bruta.get("contadores") or {})
    ultima_iniciativa = dict(iniciativa_bruta.get("ultima_decisao") or {})
    auditoria_bruta = dict(iniciativa_bruta.get("auditoria") or {})
    permissoes_brutas = dict(iniciativa_bruta.get("permissoes") or {})
    seguranca_bruta = dict(iniciativa_bruta.get("seguranca") or {})
    coordenacao_bruta = dict(mental.get("coordenador_oportunidades") or {})
    contadores_coordenacao = dict(coordenacao_bruta.get("contadores") or {})
    ultima_coordenacao = dict(coordenacao_bruta.get("ultima") or {})
    aprendizado_coordenacao = dict(coordenacao_bruta.get("aprendizado") or {})
    presenca_bruta = dict(mental.get("presenca_contextual") or {})
    contadores_presenca = dict(presenca_bruta.get("contadores") or {})
    ultima_presenca = dict(presenca_bruta.get("ultima_decisao") or {})
    configuracao_presenca = dict(presenca_bruta.get("configuracao") or {})
    permissoes = {}
    for dominio, registro in permissoes_brutas.items():
        dominio_seguro = _codigo_seguro(dominio, 40)
        if not dominio_seguro:
            continue
        nivel = (
            str(registro.get("nivel") or "bloqueado")
            if isinstance(registro, Mapping) else str(registro or "bloqueado")
        )
        permissoes[dominio_seguro] = _codigo_seguro(nivel, 32) or "bloqueado"
    iniciativa = {
        "modo": _codigo_seguro(iniciativa_bruta.get("modo") or "sombra", 24),
        "avaliadas": int(contadores_iniciativa.get("avaliadas") or 0),
        "duplicadas": int(contadores_iniciativa.get("duplicadas") or 0),
        "ultima": {
            "tipo": _codigo_seguro(ultima_iniciativa.get("tipo"), 48),
            "decisao": _codigo_seguro(ultima_iniciativa.get("decisao"), 48),
            "pontuacao": int(ultima_iniciativa.get("pontuacao") or 0),
            "confianca": round(float(ultima_iniciativa.get("confianca") or 0.0), 3),
            "risco": _codigo_seguro(ultima_iniciativa.get("risco"), 24),
        } if ultima_iniciativa else {},
        "auditoria": {
            "status": _codigo_seguro(auditoria_bruta.get("status") or "sem_amostras", 32),
            "amostras": int(auditoria_bruta.get("amostras") or 0),
            "dominios_candidatos": int(auditoria_bruta.get("dominios_candidatos") or 0),
            "taxa_duplicacao": round(float(auditoria_bruta.get("taxa_duplicacao") or 0.0), 3),
            "autoriza_execucao": False,
        },
        "permissoes": permissoes,
        "vontade_segura": {
            "modo": _codigo_seguro(seguranca_bruta.get("modo") or "vontade_segura", 32),
            "autoriza_execucao": False,
            "bloqueios_capacidade": int(seguranca_bruta.get("bloqueios_capacidade") or 0),
            "bloqueios_confirmacao": int(seguranca_bruta.get("bloqueios_confirmacao") or 0),
            "bloqueios_orcamento": int(seguranca_bruta.get("bloqueios_orcamento") or 0),
            "simulacoes_orcamento": int(seguranca_bruta.get("simulacoes_orcamento") or 0),
        },
        "coordenacao": {
            "recebidas": int(contadores_coordenacao.get("recebidas") or 0),
            "encaminhadas": int(contadores_coordenacao.get("encaminhadas") or 0),
            "duplicadas": int(contadores_coordenacao.get("duplicadas_semanticas") or 0),
            "baixa_confianca": int(contadores_coordenacao.get("baixa_confianca") or 0),
            "alinhadas_objetivo": int(contadores_coordenacao.get("alinhadas_objetivo") or 0),
            "feedbacks": int(contadores_coordenacao.get("feedbacks") or 0),
            "aceitas": int(contadores_coordenacao.get("aceitas") or 0),
            "recusadas": int(contadores_coordenacao.get("recusadas") or 0),
            "silencios": int(contadores_coordenacao.get("silencios") or 0),
            "correcoes": int(contadores_coordenacao.get("correcoes") or 0),
            "perfis_maduros": sum(
                1 for valor in aprendizado_coordenacao.values()
                if isinstance(valor, Mapping) and int(valor.get("ajuste_utilidade") or 0) != 0
            ),
            "objetivos_ativos": len(list(coordenacao_bruta.get("objetivos") or [])),
            "ultima_decisao": _codigo_seguro(ultima_coordenacao.get("decisao"), 48),
        },
        "presenca": {
            "ativa": bool(configuracao_presenca.get("ativo", True)),
            "perfil": _codigo_seguro(configuracao_presenca.get("perfil") or "adaptativo", 24),
            "motivo_perfil": _codigo_seguro(
                configuracao_presenca.get("motivo_perfil") or "inicio", 48,
            ),
            "recebidas": int(contadores_presenca.get("recebidas") or 0),
            "emitidas": int(contadores_presenca.get("emitidas") or 0),
            "bloqueadas_contexto": int(contadores_presenca.get("bloqueadas_contexto") or 0),
            "bloqueadas_orcamento": int(contadores_presenca.get("bloqueadas_orcamento") or 0),
            "bloqueadas_qualidade": int(contadores_presenca.get("bloqueadas_qualidade") or 0),
            "bloqueadas_variedade": int(contadores_presenca.get("bloqueadas_variedade") or 0),
            "feedbacks": int(contadores_presenca.get("feedbacks") or 0),
            "ultima": {
                "status": _codigo_seguro(ultima_presenca.get("status"), 32),
                "motivo": _codigo_seguro(ultima_presenca.get("motivo"), 64),
                "categoria": _codigo_seguro(ultima_presenca.get("categoria"), 32),
            } if ultima_presenca else {},
        },
    }
    rede_bruta = dict(rede_associativa or {})
    metricas_rede = dict(rede_bruta.get("metricas") or {})
    plasticidade_rede = dict(rede_bruta.get("plasticidade") or {})
    rede_segura = {
        "modo": _codigo_seguro(rede_bruta.get("modo") or "desligado", 24),
        "influencia_habilitada": bool(rede_bruta.get("influencia_habilitada", False)),
        "nos": int(rede_bruta.get("nos") or 0),
        "conexoes": int(rede_bruta.get("conexoes") or 0),
        "ativacoes": int(rede_bruta.get("ativacoes") or 0),
        "fila": int(rede_bruta.get("fila") or 0),
        "processados": int(metricas_rede.get("processados") or 0),
        "duplicados": int(metricas_rede.get("duplicados") or 0),
        "falhas": int(metricas_rede.get("falhas") or 0),
        "descartados_fila": int(metricas_rede.get("descartados_fila") or 0),
        "comparacoes_sombra": int(metricas_rede.get("comparacoes_sombra") or 0),
        "candidatos_sombra": int(metricas_rede.get("candidatos_sombra") or 0),
        "feedbacks": int(metricas_rede.get("feedbacks") or 0),
        "ajustes_plasticidade": int(metricas_rede.get("ajustes_plasticidade") or 0),
        "sinais_continuidade": int(metricas_rede.get("sinais_continuidade") or 0),
        "influencias_continuidade": int(metricas_rede.get("influencias_continuidade") or 0),
        "plasticidade_perfis": int(plasticidade_rede.get("perfis") or 0),
        "plasticidade_amostras": int(plasticidade_rede.get("amostras") or 0),
    }
    return {
        "saude": {**totais, "problemas": problemas},
        "interacao": {
            "emocao": conversa.get("current_emotion") or "calma",
            "nivel": int(conversa.get("emotion_level") or 1),
            "fala_reservada": bool(conversa.get("is_speaking", False)),
            "audio_reproduzindo": bool(conversa.get("audio_playing", False)),
            "modo_chat": bool(conversa.get("modo_chat", False)),
        },
        "turno": {
            "fase": plano.get("fase") or turno.get("fase") or "ocioso",
            "modalidade": turno.get("modalidade_geral") or turno.get("modalidade") or "",
            "origem": _codigo_seguro(
                plano.get("origem_entrada") or turno.get("origem_entrada"), 24,
            ),
            "autoriza_execucao": bool(turno.get("autoriza_execucao", False)),
            "erros": [_codigo_seguro(item) for item in list(plano.get("erros") or [])[:5]],
        },
        "ultima_acao": ultima_acao,
        "continuidade_geral": {
            "modo": _codigo_seguro(continuidade_oficial.get("modo") or "oficial", 24),
            "fonte_autoritativa": bool(continuidade_oficial.get("fonte_autoritativa", True)),
            "dominio_ativo": _codigo_seguro(continuidade_oficial.get("dominio_ativo"), 40),
            "dominios": len(dict(continuidade_oficial.get("dominios") or {})),
        },
        "percepcao": {
            "janela": contexto_sistema.get("title") or contexto_sistema.get("exe") or "",
            "site": aba_ativa.get("url") or "",
        },
        "pendencias": pendencias,
        "pendencia_acao": {
            "ativa": pendencia_acao.get("status") in {"ativa", "em_processamento"},
            "origem": _codigo_seguro(pendencia_acao.get("origem"), 48),
            "acao": _codigo_seguro(pendencia_acao.get("acao"), 48),
            "status": _codigo_seguro(pendencia_acao.get("status"), 32),
        },
        "latencias": latencias,
        "tamanhos_prompt": tamanhos_prompt,
        "falhas_recentes": falhas,
        "falhas_recuperadas": falhas_recuperadas,
        "falhas_por_classe": falhas_por_classe,
        "servicos_background": servicos_background,
        "decisoes_recentes": decisoes,
        "iniciativa": iniciativa,
        "rede_associativa": rede_segura,
    }


def formatar_diagnostico_terminal(diagnostico: Mapping[str, Any]) -> str:
    saude = dict(diagnostico.get("saude") or {})
    interacao = dict(diagnostico.get("interacao") or {})
    turno = dict(diagnostico.get("turno") or {})
    acao = dict(diagnostico.get("ultima_acao") or {})
    continuidade = dict(diagnostico.get("continuidade_geral") or {})
    problemas = list(saude.get("problemas") or [])
    latencias = dict(diagnostico.get("latencias") or {})
    tamanhos_prompt = dict(diagnostico.get("tamanhos_prompt") or {})
    falhas = list(diagnostico.get("falhas_recentes") or [])
    falhas_recuperadas = int(diagnostico.get("falhas_recuperadas") or 0)
    falhas_por_classe = dict(diagnostico.get("falhas_por_classe") or {})
    servicos_background = list(diagnostico.get("servicos_background") or [])
    decisoes = list(diagnostico.get("decisoes_recentes") or [])
    iniciativa = dict(diagnostico.get("iniciativa") or {})
    rede = dict(diagnostico.get("rede_associativa") or {})
    habilidades = dict(diagnostico.get("habilidades") or {})
    pesquisa_arquivos = dict(diagnostico.get("pesquisa_arquivos") or {})
    mutacoes_arquivos = dict(diagnostico.get("mutacoes_arquivos") or {})
    musica_leitura = dict(diagnostico.get("musica_leitura") or {})
    musica_operacoes = dict(diagnostico.get("musica_operacoes") or {})
    navegador_leitura = dict(diagnostico.get("navegador_leitura") or {})
    navegador_operacoes = dict(diagnostico.get("navegador_operacoes") or {})
    visao_jogo_leitura = dict(diagnostico.get("visao_jogo_leitura") or {})
    visao_jogo_analise = dict(diagnostico.get("visao_jogo_analise") or {})
    conversa_llm = dict(diagnostico.get("conversa_llm") or {})
    composicao_principal = dict(diagnostico.get("composicao_principal") or {})
    cooperacao = dict(diagnostico.get("orquestracao_cooperativa") or {})
    agenda = dict(diagnostico.get("agenda") or {})
    pessoas = dict(diagnostico.get("memoria_pessoas") or {})
    linguagem_natural = dict(diagnostico.get("linguagem_natural") or {})
    fala_operacional = dict(diagnostico.get("fala_operacional") or {})
    pendencia_acao = dict(diagnostico.get("pendencia_acao") or {})
    protecoes_ciclo = dict(diagnostico.get("protecoes_ciclo") or {})
    linhas = [
        "🩺 [DIAGNÓSTICO:MENTE]",
        (
            f"  módulos: saudáveis={saude.get('saudavel', 0)} "
            f"degradados={saude.get('degradado', 0)} indisponíveis={saude.get('indisponivel', 0)}"
        ),
        (
            f"  interação: emoção={interacao.get('emocao')} nível={interacao.get('nivel')} "
            f"fala_reservada={interacao.get('fala_reservada')} áudio={interacao.get('audio_reproduzindo')}"
        ),
        (
            f"  turno: fase={turno.get('fase')} modalidade={turno.get('modalidade') or '-'} "
            f"origem={turno.get('origem') or '-'} "
            f"execução_autorizada={turno.get('autoriza_execucao')}"
        ),
        (
            f"  última ação: intent={acao.get('intent') or '-'} alvo={acao.get('alvo') or '-'} "
            f"status={acao.get('status') or '-'} confirmada={acao.get('confirmado')}"
        ),
        (
            f"  continuidade geral: modo={continuidade.get('modo') or 'oficial'} "
            f"oficial={bool(continuidade.get('fonte_autoritativa', True))} "
            f"domínio_ativo={continuidade.get('dominio_ativo') or '-'} "
            f"domínios={int(continuidade.get('dominios') or 0)}"
        ),
        f"  pendências contextuais: {diagnostico.get('pendencias', 0)}",
        (
            f"  iniciativa: modo={iniciativa.get('modo') or 'sombra'} "
            f"avaliadas={int(iniciativa.get('avaliadas') or 0)} "
            f"duplicadas={int(iniciativa.get('duplicadas') or 0)}"
        ),
        (
            f"  rede associativa: modo={rede.get('modo') or 'desligado'} "
            f"influência={bool(rede.get('influencia_habilitada', False))} "
            f"nós={int(rede.get('nos') or 0)} conexões={int(rede.get('conexoes') or 0)} "
            f"ativações={int(rede.get('ativacoes') or 0)} fila={int(rede.get('fila') or 0)} "
            f"duplicados={int(rede.get('duplicados') or 0)} "
            f"comparações={int(rede.get('comparacoes_sombra') or 0)} "
            f"candidatos={int(rede.get('candidatos_sombra') or 0)} "
            f"feedbacks={int(rede.get('feedbacks') or 0)} "
            f"plasticidade={int(rede.get('ajustes_plasticidade') or 0)}/"
            f"{int(rede.get('plasticidade_amostras') or 0)} "
            f"continuidade={int(rede.get('influencias_continuidade') or 0)}/"
            f"{int(rede.get('sinais_continuidade') or 0)} "
            f"falhas={int(rede.get('falhas') or 0)}"
        ),
    ]
    if pendencia_acao.get("ativa"):
        linhas.insert(
            6,
            "  pendência de ação: "
            f"origem={pendencia_acao.get('origem') or '-'} "
            f"ação={pendencia_acao.get('acao') or '-'} "
            f"status={pendencia_acao.get('status') or '-'}",
        )
    if habilidades:
        linhas.append(
            "  mapa de habilidades: "
            f"catalogadas={int(habilidades.get('catalogadas') or 0)} "
            f"disponíveis={int(habilidades.get('disponiveis') or 0)} "
            f"indisponíveis={int(habilidades.get('indisponiveis') or 0)} "
            f"observações={int(habilidades.get('observacoes_ativas') or 0)} "
            "autoriza_execução=False"
        )
    if linguagem_natural:
        linhas.append(
            "  linguagem natural: "
            f"modo={linguagem_natural.get('modo') or 'coordenador_canonico'} "
            f"tentativas={int(linguagem_natural.get('tentativas') or 0)} "
            f"resolvidas={int(linguagem_natural.get('resolvidas') or 0)} "
            f"sem_intenção={int(linguagem_natural.get('sem_intencao') or 0)} "
            f"reusos_turno={int(linguagem_natural.get('reutilizadas_no_turno') or 0)} "
            f"última={linguagem_natural.get('ultima_intent') or '-'} "
            f"rota={linguagem_natural.get('ultima_rota') or '-'} "
            "autoriza_execução=False"
        )
        tolerancia = dict(linguagem_natural.get("tolerancia_portugues") or {})
        if tolerancia:
            linhas.append(
                "  tolerância de português: "
                f"modo={tolerancia.get('modo') or 'operacional_conservador'} "
                f"normalizações={int(tolerancia.get('normalizacoes') or 0)} "
                f"entradas_corrigidas={int(tolerancia.get('entradas_corrigidas') or 0)} "
                f"substituições={int(tolerancia.get('substituicoes') or 0)} "
                "aproxima_argumentos=False autoriza_execução=False"
            )
        execucao_turno = dict(linguagem_natural.get("execucao_turno") or {})
        if execucao_turno:
            linhas.append(
                "  idempotência do turno: "
                f"iniciadas={int(execucao_turno.get('iniciadas') or 0)} "
                f"reutilizadas={int(execucao_turno.get('reutilizadas') or 0)} "
                f"aguardadas={int(execucao_turno.get('aguardadas') or 0)} "
                f"ativas={int(execucao_turno.get('ativas') or 0)} "
                f"timeouts={int(execucao_turno.get('timeouts') or 0)} "
                f"falhas={int(execucao_turno.get('falhas') or 0)}"
            )
    if fala_operacional:
        linhas.append(
            "  voz operacional única: "
            f"tentativas={int(fala_operacional.get('tentativas') or 0)} "
            f"emitidas={int(fala_operacional.get('emitidas') or 0)} "
            f"duplicadas_suprimidas={int(fala_operacional.get('duplicadas_suprimidas') or 0)} "
            f"reservadas={int(fala_operacional.get('reservadas') or 0)} "
            f"rejeitadas={int(fala_operacional.get('rejeitadas_voz') or 0)} "
            "autoriza_execução=False"
        )
        emocao_causal = dict(fala_operacional.get("emocao_causal") or {})
        if emocao_causal:
            ultima_causa = dict(emocao_causal.get("ultima") or {})
            linhas.append(
                "  emoção causal operacional: "
                f"avaliados={int(emocao_causal.get('avaliados') or 0)} "
                f"expressões={int(emocao_causal.get('expressoes') or 0)} "
                f"responsabilidade={_codigo_seguro(ultima_causa.get('responsabilidade'), 16)} "
                f"confiança={round(float(ultima_causa.get('confianca') or 0.0) * 100):.0f}% "
                f"emoção={_codigo_seguro(ultima_causa.get('emocao'), 16)} "
                "autoriza_execução=False persistência_pessoal=False"
            )
    if protecoes_ciclo:
        linhas.append(
            "  proteções do ciclo: "
            f"reentradas_evitadas={int(protecoes_ciclo.get('reentradas_evitadas') or 0)} "
            "execuções_duplicadas_convergidas="
            f"{int(protecoes_ciclo.get('execucoes_duplicadas_convergidas') or 0)} "
            "falas_duplicadas_suprimidas="
            f"{int(protecoes_ciclo.get('falas_duplicadas_suprimidas') or 0)} "
            f"órfãos_atuais={int(protecoes_ciclo.get('servicos_orfaos_atuais') or 0)} "
            f"órfãos_detectados={int(protecoes_ciclo.get('servicos_orfaos_detectados') or 0)}"
        )
    if pesquisa_arquivos:
        linhas.append(
            "  pesquisa de arquivos: "
            f"indexados={int(pesquisa_arquivos.get('arquivos_indexados') or 0)} "
            f"pesquisas={int(pesquisa_arquivos.get('pesquisas') or 0)} "
            f"cache={bool(pesquisa_arquivos.get('cache_ativo'))} "
            f"índice_incompleto={bool(pesquisa_arquivos.get('indice_incompleto'))} "
            f"falhas={int(pesquisa_arquivos.get('falhas') or 0)} "
            "somente_leitura=True envio_externo=False"
        )
    if mutacoes_arquivos:
        linhas.append(
            "  mutações de arquivos: "
            f"raízes_autorizadas={bool(mutacoes_arquivos.get('somente_raizes_autorizadas'))} "
            f"escrita_segura={bool(mutacoes_arquivos.get('escrita_segura_disponivel'))} "
            f"lixeira_reversível={bool(mutacoes_arquivos.get('lixeira_reversivel'))} "
            "confirmação_pendente="
            f"{bool(mutacoes_arquivos.get('confirmacao_exclusao_pendente'))}"
        )
    if musica_leitura:
        linhas.append(
            "  leitura musical: "
            f"playlists={int(musica_leitura.get('playlists_usuario') or 0)} "
            f"curadorias_laylay={int(musica_leitura.get('playlists_laylay') or 0)} "
            f"histórico_na_curadoria={bool(musica_leitura.get('curadoria_usa_historico'))} "
            f"cooperação={bool(musica_leitura.get('curadoria_cooperativa'))} "
            f"falhas_curadoria={int(musica_leitura.get('curadoria_falhas') or 0)} "
            f"playlist_ativa={bool(musica_leitura.get('playlist_ativa'))} "
            f"estado_disponível={bool(musica_leitura.get('estado_disponivel'))} "
            "somente_leitura=True expõe_urls=False"
        )
    if musica_operacoes:
        linhas.append(
            "  operações musicais: "
            f"mutação={bool(musica_operacoes.get('mutacao_disponivel'))} "
            f"reprodução={bool(musica_operacoes.get('reproducao_disponivel'))} "
            f"auto_next={bool(musica_operacoes.get('auto_next_disponivel'))} "
            f"curadoria={bool(musica_operacoes.get('curadoria_disponivel'))} "
            f"playlist_ativa={bool(musica_operacoes.get('playlist_ativa'))}"
        )
    if navegador_leitura or navegador_operacoes:
        linhas.append(
            "  navegador tipado: "
            f"conectado={bool(navegador_leitura.get('conectado'))} "
            f"leitura_aba={bool(navegador_leitura.get('leitura_aba_disponivel'))} "
            f"listagem={bool(navegador_leitura.get('listagem_disponivel'))} "
            f"navegação={bool(navegador_operacoes.get('navegacao_disponivel'))} "
            f"comandos={bool(navegador_operacoes.get('comandos_disponiveis'))} "
            "expõe_urls=False autoriza_execução=False"
        )
    if visao_jogo_leitura or visao_jogo_analise:
        linhas.append(
            "  visão de jogo tipada: "
            f"habilitada={bool(visao_jogo_leitura.get('habilitado'))} "
            f"credencial={bool(visao_jogo_leitura.get('credencial_disponivel'))} "
            f"em_andamento={bool(visao_jogo_leitura.get('em_andamento'))} "
            f"recente={bool(visao_jogo_leitura.get('analise_recente'))} "
            f"análise={bool(visao_jogo_analise.get('analise_disponivel'))} "
            f"continuidade={bool(visao_jogo_analise.get('continuidade_disponivel'))} "
            f"falhas={int(visao_jogo_analise.get('falhas') or 0)} "
            "captura_persistida=False imagem_exposta=False "
            "autoriza_execução=False"
        )
    if conversa_llm:
        linhas.append(
            "  conversa e LLM tipadas: "
            f"prompt={bool(conversa_llm.get('prompt_disponivel'))} "
            f"modelo={bool(conversa_llm.get('modelo_disponivel'))} "
            f"estado={bool(conversa_llm.get('estado_disponivel'))} "
            f"requisições={int(conversa_llm.get('requisicoes') or 0)} "
            f"falhas={int(conversa_llm.get('falhas') or 0)} "
            "memória_exposta=False credencial_exposta=False "
            "autoriza_execução=False"
        )
    if composicao_principal:
        linhas.append(
            "  composição principal: "
            f"disponível={bool(composicao_principal.get('disponivel'))} "
            f"registros={int(composicao_principal.get('quantidade') or 0)} "
            f"namespace_global={bool(composicao_principal.get('namespace_global'))} "
            "credencial_exposta=False autoriza_execução=False"
        )
    if cooperacao:
        linhas.append(
            "  orquestração cooperativa: "
            f"modo={cooperacao.get('modo') or 'sombra'} "
            f"eventos={int(cooperacao.get('eventos') or 0)} "
            f"planos={int(cooperacao.get('planos') or 0)} "
            f"confirmados={int(cooperacao.get('confirmados') or 0)} "
            f"falhas={int(cooperacao.get('falhas') or 0)} "
            f"parciais={int(cooperacao.get('falhas_parciais') or 0)} "
            f"dependências_bloqueadas={int(cooperacao.get('dependencias_bloqueadas') or 0)} "
            f"orçamentos_excedidos={int(cooperacao.get('orcamentos_excedidos') or 0)} "
            f"cancelamentos={int(cooperacao.get('cancelamentos_solicitados') or 0)} "
            f"autorizações_bloqueadas={int(cooperacao.get('autorizacoes_bloqueadas') or 0)} "
            f"ciclos_finalizados={int(cooperacao.get('finalizacoes_governanca') or 0)} "
            f"ativos={int(cooperacao.get('planos_ativos') or 0)} "
            f"referências_ativas={int(cooperacao.get('referencias_ativas') or 0)}"
        )
    if agenda:
        linhas.append(
            "  agenda: "
            f"disponível={bool(agenda.get('disponivel'))} "
            f"daemon={bool(agenda.get('daemon_ativo'))} "
            f"ativos={int(agenda.get('agendamentos_ativos') or 0)} "
            f"gravações={int(agenda.get('gravacoes') or 0)} "
            f"falhas_persistência={int(agenda.get('falhas_persistencia') or 0)} "
            f"disparos={int(agenda.get('disparos_confirmados') or 0)} "
            f"retries={int(agenda.get('retries') or 0)} "
            "conteúdo_exposto=False autoriza_execução=False"
        )
    if pessoas:
        linhas.append(
            "  memória de pessoas: "
            f"ativas={int(pessoas.get('ativas') or 0)} "
            f"relações={int(pessoas.get('relacoes_ativas') or 0)} "
            f"fatos={int(pessoas.get('fatos_ativos') or 0)} "
            f"correções={int(pessoas.get('correcoes') or 0)} "
            f"esquecimentos={int(pessoas.get('esquecimentos') or 0)} "
            f"ambiguidades={int(pessoas.get('ambiguidades') or 0)} "
            f"falhas={int(pessoas.get('falhas') or 0)} "
            "persistência_local=True envio_externo=False"
        )
    ultima_iniciativa = dict(iniciativa.get("ultima") or {})
    if ultima_iniciativa:
        linhas.append(
            f"  última iniciativa: {ultima_iniciativa.get('tipo') or '-'} "
            f"decisão={ultima_iniciativa.get('decisao') or '-'} "
            f"pontuação={int(ultima_iniciativa.get('pontuacao') or 0)} "
            f"confiança={float(ultima_iniciativa.get('confianca') or 0.0):.0%} "
            f"risco={ultima_iniciativa.get('risco') or '-'}"
        )
    coordenacao = dict(iniciativa.get("coordenacao") or {})
    if coordenacao.get("recebidas"):
        linhas.append(
            "  coordenação de oportunidades: "
            f"recebidas={int(coordenacao.get('recebidas') or 0)} "
            f"encaminhadas={int(coordenacao.get('encaminhadas') or 0)} "
            f"agrupadas={int(coordenacao.get('duplicadas') or 0)} "
            f"baixa_confiança={int(coordenacao.get('baixa_confianca') or 0)} "
            f"alinhadas_objetivo={int(coordenacao.get('alinhadas_objetivo') or 0)} "
            f"feedbacks={int(coordenacao.get('feedbacks') or 0)} "
            f"perfis_maduros={int(coordenacao.get('perfis_maduros') or 0)}"
        )
    presenca = dict(iniciativa.get("presenca") or {})
    linhas.append(
            "  presença autônoma: "
            f"perfil={presenca.get('perfil') or 'adaptativo'} "
            f"motivo={presenca.get('motivo_perfil') or 'inicio'} "
            f"recebidas={int(presenca.get('recebidas') or 0)} "
            f"emitidas={int(presenca.get('emitidas') or 0)} "
            f"bloqueadas_contexto={int(presenca.get('bloqueadas_contexto') or 0)} "
            f"bloqueadas_orçamento={int(presenca.get('bloqueadas_orcamento') or 0)} "
            f"bloqueadas_qualidade={int(presenca.get('bloqueadas_qualidade') or 0)}"
        )
    auditoria = dict(iniciativa.get("auditoria") or {})
    linhas.append(
        f"  auditoria da iniciativa: status={auditoria.get('status') or 'sem_amostras'} "
        f"amostras={int(auditoria.get('amostras') or 0)} "
        f"domínios_candidatos={int(auditoria.get('dominios_candidatos') or 0)} "
        f"duplicação={float(auditoria.get('taxa_duplicacao') or 0.0):.1%} "
        "execução_autorizada=False"
    )
    permissoes = dict(iniciativa.get("permissoes") or {})
    if permissoes:
        linhas.append(
            "  permissões da autonomia: "
            + ", ".join(f"{dominio}={nivel}" for dominio, nivel in sorted(permissoes.items()))
        )
    vontade = dict(iniciativa.get("vontade_segura") or {})
    if vontade:
        linhas.append(
            "  vontade segura: "
            f"modo={vontade.get('modo') or 'vontade_segura'} "
            f"capacidade_bloqueada={int(vontade.get('bloqueios_capacidade') or 0)} "
            f"confirmação_exigida={int(vontade.get('bloqueios_confirmacao') or 0)} "
            f"orçamento_bloqueado={int(vontade.get('bloqueios_orcamento') or 0)} "
            f"simulações={int(vontade.get('simulacoes_orcamento') or 0)} "
            "execução_autorizada=False"
        )
    if latencias:
        resumo_latencias = []
        for nome, metrica in sorted(latencias.items()):
            alerta = " ⚠" if metrica.get("excedeu_orcamento") else ""
            resumo_latencias.append(
                f"{nome}={float(metrica.get('ultimo_ms') or 0.0):.0f}ms"
                f" (média {float(metrica.get('media_ms') or 0.0):.0f}ms/{int(metrica.get('amostras') or 0)})"
                f"{alerta}"
            )
        linhas.append("  latências: " + " | ".join(resumo_latencias))
    if tamanhos_prompt:
        resumo_prompts = [
            f"{nome}={int(metrica.get('ultimo_chars') or 0)} chars"
            for nome, metrica in sorted(tamanhos_prompt.items())
        ]
        linhas.append("  prompts: " + " | ".join(resumo_prompts))
    if decisoes:
        ultima = decisoes[-1]
        motivos = ",".join(ultima.get("motivos") or []) or "sem_motivo"
        linhas.append(
            f"  decisão recente: {ultima.get('componente') or '-'}={ultima.get('acao') or '-'} "
            f"categoria={ultima.get('categoria') or '-'} motivo={motivos}"
        )
    if servicos_background:
        estados_saudaveis = {"ativo", "finalizado", "encerrado"}
        ativos = sum(1 for item in servicos_background if item.get("estado") == "ativo")
        degradados = sum(
            1 for item in servicos_background
            if item.get("estado") not in estados_saudaveis
        )
        quedas = sum(int(item.get("quedas") or 0) for item in servicos_background)
        reinicios = sum(int(item.get("reinicios") or 0) for item in servicos_background)
        orfaos = sum(int(item.get("orfaos") or 0) for item in servicos_background)
        linhas.append(
            "  serviços de fundo: "
            f"total={len(servicos_background)} ativos={ativos} degradados={degradados} "
            f"quedas={quedas} reinícios={reinicios} órfãos={orfaos}"
        )
        for servico in servicos_background:
            if servico.get("estado") in estados_saudaveis:
                continue
            linhas.append(
                f"  serviço: {servico.get('nome') or '-'}={servico.get('estado') or '-'} "
                f"tentativa={int(servico.get('tentativa') or 0)} "
                f"fallback={servico.get('fallback') or 'nenhum'}"
            )
    linhas.append(
        f"  falhas técnicas recentes: {len(falhas)} "
        f"(esperadas={int(falhas_por_classe.get('esperada') or 0)} "
        f"degradações={int(falhas_por_classe.get('degradacao') or 0)} "
        f"defeitos={int(falhas_por_classe.get('defeito') or 0)} "
        f"não_classificadas={int(falhas_por_classe.get('nao_classificada') or 0)} "
        f"recuperadas={falhas_recuperadas})"
    )
    for falha in falhas[-5:]:
        linhas.append(
            f"  falha: {falha.get('componente') or '-'}={falha.get('codigo') or '-'} "
            f"classe={falha.get('classe') or '-'} impacto={falha.get('impacto') or '-'} "
            f"fallback={falha.get('fallback') or 'nenhum'} tipo={falha.get('tipo') or '-'}"
        )
    for problema in problemas:
        ausentes = ",".join(problema.get("ausentes") or []) or "sem detalhe"
        linhas.append(f"  atenção: {problema.get('modulo')}={problema.get('status')} ({ausentes})")
    return "\n".join(linhas)


class DiagnosticoMenteRuntime:
    def __init__(
        self,
        *,
        estado_getter: Callable[[], Mapping[str, Any]],
        saude_getter: Callable[[], Mapping[str, Any]],
        rede_associativa_getter: Callable[[], Mapping[str, Any]] | None = None,
        mapa_habilidades_getter: Callable[[], Mapping[str, Any]] | None = None,
        pesquisa_arquivos_getter: Callable[[], Mapping[str, Any]] | None = None,
        mutacoes_arquivos_getter: Callable[[], Mapping[str, Any]] | None = None,
        musica_leitura_getter: Callable[[], Mapping[str, Any]] | None = None,
        musica_operacoes_getter: Callable[[], Mapping[str, Any]] | None = None,
        navegador_leitura_getter: Callable[[], Mapping[str, Any]] | None = None,
        navegador_operacoes_getter: Callable[[], Mapping[str, Any]] | None = None,
        visao_jogo_leitura_getter: Callable[[], Mapping[str, Any]] | None = None,
        visao_jogo_analise_getter: Callable[[], Mapping[str, Any]] | None = None,
        conversa_llm_getter: Callable[[], Mapping[str, Any]] | None = None,
        composicao_principal_getter: Callable[[], Mapping[str, Any]] | None = None,
        orquestracao_cooperativa_getter: Callable[[], Mapping[str, Any]] | None = None,
        agenda_getter: Callable[[], Mapping[str, Any]] | None = None,
        memoria_pessoas_getter: Callable[[], Mapping[str, Any]] | None = None,
        linguagem_natural_getter: Callable[[], Mapping[str, Any]] | None = None,
        fala_operacional_getter: Callable[[], Mapping[str, Any]] | None = None,
        falar: Callable[[str, str, int], Any],
        log: Callable[[str], Any] = print,
    ) -> None:
        self.estado_getter = estado_getter
        self.saude_getter = saude_getter
        self.rede_associativa_getter = rede_associativa_getter
        self.mapa_habilidades_getter = mapa_habilidades_getter
        self.pesquisa_arquivos_getter = pesquisa_arquivos_getter
        self.mutacoes_arquivos_getter = mutacoes_arquivos_getter
        self.musica_leitura_getter = musica_leitura_getter
        self.musica_operacoes_getter = musica_operacoes_getter
        self.navegador_leitura_getter = navegador_leitura_getter
        self.navegador_operacoes_getter = navegador_operacoes_getter
        self.visao_jogo_leitura_getter = visao_jogo_leitura_getter
        self.visao_jogo_analise_getter = visao_jogo_analise_getter
        self.conversa_llm_getter = conversa_llm_getter
        self.composicao_principal_getter = composicao_principal_getter
        self.orquestracao_cooperativa_getter = orquestracao_cooperativa_getter
        self.agenda_getter = agenda_getter
        self.memoria_pessoas_getter = memoria_pessoas_getter
        self.linguagem_natural_getter = linguagem_natural_getter
        self.fala_operacional_getter = fala_operacional_getter
        self.falar = falar
        self.log = log

    def snapshot(self) -> dict[str, Any]:
        rede = {}
        if callable(self.rede_associativa_getter):
            try:
                rede = dict(self.rede_associativa_getter() or {})
            except Exception:
                rede = {"modo": "indisponivel", "metricas": {"falhas": 1}}
        diagnostico = construir_diagnostico_mente(
            self.estado_getter(), self.saude_getter(), rede,
        )
        if callable(self.mapa_habilidades_getter):
            try:
                diagnostico["habilidades"] = dict(self.mapa_habilidades_getter() or {})
            except Exception:
                diagnostico["habilidades"] = {
                    "catalogadas": 0, "disponiveis": 0, "indisponiveis": 0,
                    "observacoes_ativas": 0, "autoriza_execucao": False,
                }
        if callable(self.pesquisa_arquivos_getter):
            try:
                diagnostico["pesquisa_arquivos"] = dict(self.pesquisa_arquivos_getter() or {})
            except Exception:
                diagnostico["pesquisa_arquivos"] = {
                    "arquivos_indexados": 0, "pesquisas": 0, "falhas": 1,
                    "cache_ativo": False, "indice_incompleto": True,
                    "somente_leitura": True, "envia_conteudo_externo": False,
                }
        if callable(self.mutacoes_arquivos_getter):
            try:
                diagnostico["mutacoes_arquivos"] = dict(
                    self.mutacoes_arquivos_getter() or {}
                )
            except Exception:
                diagnostico["mutacoes_arquivos"] = {
                    "somente_raizes_autorizadas": True,
                    "escrita_segura_disponivel": False,
                    "lixeira_reversivel": False,
                    "confirmacao_exclusao_pendente": False,
                }
        if callable(self.musica_leitura_getter):
            try:
                diagnostico["musica_leitura"] = dict(
                    self.musica_leitura_getter() or {}
                )
            except Exception:
                diagnostico["musica_leitura"] = {
                    "somente_leitura": True, "playlists_usuario": 0,
                    "playlist_ativa": False, "estado_disponivel": False,
                    "expondo_urls": False,
                }
        if callable(self.musica_operacoes_getter):
            try:
                diagnostico["musica_operacoes"] = dict(
                    self.musica_operacoes_getter() or {}
                )
            except Exception:
                diagnostico["musica_operacoes"] = {
                    "mutacao_disponivel": False,
                    "reproducao_disponivel": False,
                    "auto_next_disponivel": False,
                    "curadoria_disponivel": False,
                    "playlist_ativa": False,
                }
        if callable(self.navegador_leitura_getter):
            try:
                diagnostico["navegador_leitura"] = dict(
                    self.navegador_leitura_getter() or {}
                )
            except Exception:
                diagnostico["navegador_leitura"] = {
                    "conectado": False,
                    "leitura_aba_disponivel": False,
                    "listagem_disponivel": False,
                }
        if callable(self.navegador_operacoes_getter):
            try:
                diagnostico["navegador_operacoes"] = dict(
                    self.navegador_operacoes_getter() or {}
                )
            except Exception:
                diagnostico["navegador_operacoes"] = {
                    "comandos_disponiveis": False,
                    "navegacao_disponivel": False,
                    "controle_pagina_disponivel": False,
                    "fechamento_nativo_disponivel": False,
                }
        if callable(self.visao_jogo_leitura_getter):
            try:
                diagnostico["visao_jogo_leitura"] = dict(
                    self.visao_jogo_leitura_getter() or {}
                )
            except Exception:
                diagnostico["visao_jogo_leitura"] = {
                    "habilitado": False, "credencial_disponivel": False,
                    "em_andamento": False, "analise_recente": False,
                    "contexto_jogo_ativo": False, "captura_persistida": False,
                    "imagem_exposta": False, "autoriza_execucao": False,
                }
        if callable(self.visao_jogo_analise_getter):
            try:
                diagnostico["visao_jogo_analise"] = dict(
                    self.visao_jogo_analise_getter() or {}
                )
            except Exception:
                diagnostico["visao_jogo_analise"] = {
                    "analise_disponivel": False,
                    "continuidade_disponivel": False,
                    "solicitacoes": 0, "aceitas": 0, "recusadas": 0,
                    "falhas": 1, "captura_exposta": False,
                    "prompt_exposto": False, "autoriza_execucao": False,
                }
        if callable(self.conversa_llm_getter):
            try:
                diagnostico["conversa_llm"] = dict(self.conversa_llm_getter() or {})
            except Exception:
                diagnostico["conversa_llm"] = {
                    "prompt_disponivel": False, "modelo_disponivel": False,
                    "estado_disponivel": False, "requisicoes": 0, "falhas": 1,
                    "memoria_exposta": False, "credencial_exposta": False,
                    "autoriza_execucao": False,
                }
        if callable(self.composicao_principal_getter):
            try:
                bruto = dict(self.composicao_principal_getter() or {})
                diagnostico["composicao_principal"] = {
                    "disponivel": bool(bruto.get("disponivel")),
                    "quantidade": int(bruto.get("quantidade") or 0),
                    "namespace_global": bool(bruto.get("namespace_global")),
                    "credencial_exposta": bool(bruto.get("credencial_exposta")),
                    "autoriza_execucao": bool(bruto.get("autoriza_execucao")),
                }
            except Exception:
                diagnostico["composicao_principal"] = {
                    "disponivel": False, "quantidade": 0,
                    "namespace_global": True, "credencial_exposta": False,
                    "autoriza_execucao": False,
                }
        if callable(self.orquestracao_cooperativa_getter):
            try:
                diagnostico["orquestracao_cooperativa"] = dict(
                    self.orquestracao_cooperativa_getter() or {}
                )
            except Exception:
                diagnostico["orquestracao_cooperativa"] = {
                    "modo": "sombra", "eventos": 0, "planos": 0,
                    "confirmados": 0, "falhas": 1, "planos_ativos": 0,
                    "referencias_ativas": 0,
                }
        if callable(self.agenda_getter):
            try:
                diagnostico["agenda"] = dict(self.agenda_getter() or {})
            except Exception:
                diagnostico["agenda"] = {
                    "disponivel": False,
                    "daemon_ativo": False,
                    "agendamentos_ativos": 0,
                    "gravacoes": 0,
                    "falhas_persistencia": 1,
                    "disparos_confirmados": 0,
                    "retries": 0,
                    "conteudo_exposto": False,
                    "autoriza_execucao": False,
                }
        # O retrato tipado da agenda é coletado depois da auditoria geral e é
        # mais recente. Se ele confirma persistência disponível, remova um
        # alerta antigo do mesmo módulo em vez de publicar dois estados
        # contraditórios no mesmo diagnóstico.
        agenda_atual = dict(diagnostico.get("agenda") or {})
        if agenda_atual.get("disponivel") is True:
            saude = dict(diagnostico.get("saude") or {})
            problemas = list(saude.get("problemas") or [])
            problema_agenda = next(
                (
                    item for item in problemas
                    if str(item.get("modulo") or "").strip().casefold() == "agenda"
                ),
                None,
            )
            if problema_agenda is not None:
                status_anterior = str(
                    problema_agenda.get("status") or "degradado"
                ).strip().casefold()
                if status_anterior in {"degradado", "indisponivel"}:
                    saude[status_anterior] = max(
                        0, int(saude.get(status_anterior) or 0) - 1,
                    )
                    saude["saudavel"] = int(saude.get("saudavel") or 0) + 1
                saude["problemas"] = [
                    item for item in problemas if item is not problema_agenda
                ]
                diagnostico["saude"] = saude
        if callable(self.memoria_pessoas_getter):
            try:
                diagnostico["memoria_pessoas"] = dict(self.memoria_pessoas_getter() or {})
            except Exception:
                diagnostico["memoria_pessoas"] = {
                    "ativas": 0, "relacoes_ativas": 0, "fatos_ativos": 0,
                    "correcoes": 0, "esquecimentos": 0, "ambiguidades": 0,
                    "falhas": 1, "persistencia_local": True, "envio_externo": False,
                }
        if callable(self.linguagem_natural_getter):
            try:
                diagnostico["linguagem_natural"] = dict(
                    self.linguagem_natural_getter() or {}
                )
            except Exception:
                diagnostico["linguagem_natural"] = {
                    "modo": "indisponivel", "tentativas": 0,
                    "resolvidas": 0, "sem_intencao": 0,
                    "ultima_rota": "", "ultima_intent": "",
                    "autoriza_execucao": False,
                }
        if callable(self.fala_operacional_getter):
            try:
                diagnostico["fala_operacional"] = dict(
                    self.fala_operacional_getter() or {}
                )
            except Exception:
                diagnostico["fala_operacional"] = {
                    "tentativas": 0, "emitidas": 0,
                    "duplicadas_suprimidas": 0, "reservadas": 0,
                    "rejeitadas_voz": 0, "autoriza_execucao": False,
                }
        linguagem = dict(diagnostico.get("linguagem_natural") or {})
        execucao = dict(linguagem.get("execucao_turno") or {})
        fala = dict(diagnostico.get("fala_operacional") or {})
        servicos = list(diagnostico.get("servicos_background") or [])
        diagnostico["protecoes_ciclo"] = {
            "reentradas_evitadas": int(linguagem.get("reutilizadas_no_turno") or 0),
            "execucoes_duplicadas_convergidas": (
                int(execucao.get("reutilizadas") or 0)
                + int(execucao.get("aguardadas") or 0)
            ),
            "falas_duplicadas_suprimidas": int(
                fala.get("duplicadas_suprimidas") or 0
            ),
            "servicos_orfaos_atuais": sum(
                1 for item in servicos if str(item.get("estado") or "") == "orfao"
            ),
            "servicos_orfaos_detectados": sum(
                int(item.get("orfaos") or 0) for item in servicos
            ),
        }
        return diagnostico

    def mostrar(self) -> dict[str, Any]:
        diagnostico = self.snapshot()
        self.log(formatar_diagnostico_terminal(diagnostico))
        saude = dict(diagnostico.get("saude") or {})
        problemas = int(saude.get("degradado") or 0) + int(saude.get("indisponivel") or 0)
        falhas = len(diagnostico.get("falhas_recentes") or [])
        if problemas or falhas:
            partes = []
            if problemas:
                partes.append(f"{problemas} módulo{'s' if problemas != 1 else ''} pedindo atenção")
            if falhas:
                partes.append(f"{falhas} falha{'s' if falhas != 1 else ''} técnica{'s' if falhas != 1 else ''} recente{'s' if falhas != 1 else ''}")
            fala = f"Encontrei {' e '.join(partes)}. Deixei o diagnóstico seguro no terminal."
            emocao, nivel = "focada", 2
        else:
            fala = "Minha mente está conectada e os módulos auditados estão saudáveis. Deixei o retrato no terminal."
            emocao, nivel = "calma", 1
        self.falar(fala, emocao, nivel)
        return diagnostico


def criar_diagnostico_mente_runtime(**kwargs: Any) -> DiagnosticoMenteRuntime:
    return DiagnosticoMenteRuntime(**kwargs)
