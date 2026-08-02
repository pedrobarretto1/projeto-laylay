"""Retrato seguro e legível do funcionamento atual da mente única."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Mapping

from mente_laylay.memoria_mental.continuidade_geral import selecionar_continuidade_por_classe
from mente_laylay.memoria_mental.formatacao_diagnostico import (
    _codigo_seguro,
    _normalizar,
    formatar_diagnostico_terminal,
)


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
