"""Resolve continuidades por significado, sem catalogar frases completas."""

from __future__ import annotations

import re
import time
import unicodedata
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict

from mente_laylay.arquivos.nome_natural import nome_com_nova_extensao_textual
from mente_laylay.memoria_mental.continuidade_geral import selecionar_referente_saliente


@dataclass(frozen=True)
class DecisaoContinuidade:
    operacao: str = ""
    dominio: str = ""
    acao: str = ""
    intent: str = ""
    alvo: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    confianca: float = 0.0
    motivo: str = ""

    def para_intencao(self) -> Dict[str, Any] | None:
        if not self.intent or self.confianca < 0.60:
            return None
        return {
            "intent": self.intent,
            "params": dict(self.params),
            "_semantica": {
                "operacao": self.operacao,
                "dominio": self.dominio,
                "acao": self.acao,
                "confianca": round(float(self.confianca), 3),
                "motivo": self.motivo,
            },
        }


def _normalizar(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    bruto = "".join(ch for ch in bruto if not unicodedata.combining(ch))
    bruto = re.sub(r"[^a-z0-9_\s.-]", " ", bruto)
    return re.sub(r"\s+", " ", bruto).strip()


def _tem_radical(tokens: list[str], *radicais: str) -> bool:
    return any(token.startswith(radical) for token in tokens for radical in radicais)


def _relacao_semantica(tokens: list[str]) -> str:
    conjunto = set(tokens)
    # Depois que uma mudanca de estado ja foi concluida, "não quero mais"
    # significa desfazer o efeito, não cancelar uma ação que já acabou.
    if {"quero", "mais", "nao"} <= conjunto:
        return "REVERTER"
    if _tem_radical(tokens, "desfaz", "restaur", "recuper") or (
        _tem_radical(tokens, "traz", "volt") and conjunto.intersection({"ela", "ele", "isso", "aquilo"})
    ):
        return "REVERTER"
    if conjunto.intersection({"novamente", "repete", "repetir"}) or (
        "novo" in conjunto and "de" in conjunto
    ) or ({"outra", "vez"} <= conjunto):
        return "REPETIR"
    if conjunto.intersection({"ela", "ele", "dela", "dele", "isso", "aquilo", "essa", "esse"}):
        return "REFERENCIAR"
    return ""


def _acao_semantica(tokens: list[str]) -> str:
    if _tem_radical(tokens, "cri", "refaz", "restaur", "recuper"):
        return "CRIAR"
    if _tem_radical(tokens, "apag", "delet", "remov", "exclu"):
        return "REMOVER"
    if _tem_radical(tokens, "abr", "entr", "acess"):
        return "ABRIR"
    if _tem_radical(tokens, "fech", "encerr"):
        return "FECHAR"
    if _tem_radical(tokens, "lig"):
        return "LIGAR"
    if _tem_radical(tokens, "deslig"):
        return "DESLIGAR"
    if _tem_radical(tokens, "paus"):
        return "PAUSAR"
    if _tem_radical(tokens, "despaus", "retom", "continu"):
        return "RETOMAR"
    if _tem_radical(tokens, "toc", "coloc"):
        return "EXECUTAR"
    if _tem_radical(tokens, "repet"):
        return "EXECUTAR"
    if _tem_radical(tokens, "proxim", "avanc", "pul"):
        return "AVANCAR"
    if _tem_radical(tokens, "anter", "retroced"):
        return "RETROCEDER"
    if _tem_radical(tokens, "mov", "transfer"):
        return "MOVER"
    if _tem_radical(tokens, "renome", "mud", "troc", "alter") and set(tokens).intersection(
        {"nome", "chama", "chamado", "tipo", "extensao", "formato"}
    ):
        return "RENOMEAR"
    if _tem_radical(tokens, "minimiz"):
        return "MINIMIZAR"
    return ""


def _acao_da_intencao(intent: str, params: Dict[str, Any] | None = None) -> str:
    intent = str(intent or "").upper()
    dados = dict(params or {})
    if intent in {"CREATE_FOLDER", "CREATE_FILE"}:
        return "CRIAR"
    if intent == "DELETE_ITEM":
        return "REMOVER"
    if intent == "MOVE_ITEM":
        return "MOVER"
    if intent == "FILE_TRANSACTION":
        operacao = str(dados.get("operacao") or "").casefold()
        return "RENOMEAR" if operacao == "renomear" else "MOVER" if operacao == "mover" else ""
    if intent in {"APP_OPEN", "OPEN_URL"}:
        return "ABRIR"
    if intent in {"CLOSE_APP", "CLOSE_TAB"}:
        return "FECHAR"
    if intent == "IOT_CONTROL":
        return {
            "ligar": "LIGAR",
            "desligar": "DESLIGAR",
        }.get(str(dados.get("acao") or "").lower(), "")
    if intent == "MEDIA_CONTROL":
        return {
            "pause": "PAUSAR", "play": "RETOMAR", "next": "AVANCAR",
            "prev": "RETROCEDER", "replay": "EXECUTAR",
        }.get(str(dados.get("acao") or "").lower(), "EXECUTAR")
    return ""


def _acao_aprendida_para_contexto(
    mente: Dict[str, Any],
    dominio: str,
    acao_anterior: str,
) -> str:
    """Recupera uma correcao anterior sem habilitar operacoes inexistentes."""
    aprendizado = mente.get("aprendizado_continuidade")
    if not isinstance(aprendizado, dict) or not dominio or not acao_anterior:
        return ""
    preferencias = aprendizado.get("preferencias_operacao")
    if not isinstance(preferencias, dict):
        return ""
    prefixo = f"{dominio}:{acao_anterior}>"
    candidatos: list[tuple[str, int]] = []
    for chave, peso in preferencias.items():
        if not str(chave).startswith(prefixo):
            continue
        try:
            candidatos.append((str(chave).split(">", 1)[1], int(peso)))
        except (IndexError, TypeError, ValueError):
            continue
    if not candidatos:
        return ""
    acao, _ = max(candidatos, key=lambda item: item[1])
    suportadas = {
        "CRIAR", "REMOVER", "ABRIR", "FECHAR", "LIGAR", "DESLIGAR",
        "PAUSAR", "RETOMAR", "EXECUTAR", "AVANCAR", "RETROCEDER",
        "RENOMEAR", "MOVER",
    }
    return acao if acao in suportadas else ""


def _dominio_explicito(tokens: list[str]) -> str:
    conjunto = set(tokens)
    if conjunto.intersection({
        "pasta", "arquivo", "documento", "txt", "md", "markdown", "extensao", "formato",
    }):
        return "arquivo"
    if conjunto.intersection({"ventilador", "tomada", "lampada", "luz", "dispositivo"}):
        return "iot"
    if conjunto.intersection({"musica", "faixa", "som", "playlist"}):
        return "musica"
    if conjunto.intersection({"site", "pagina", "aba", "guia", "web"}):
        return "site"
    if conjunto.intersection({"app", "aplicativo", "programa", "janela"}):
        return "app"
    return ""


def _dominio_contextual(mente: Dict[str, Any], estrutura: Dict[str, Any]) -> tuple[str, float]:
    continuidade = selecionar_referente_saliente(mente, ttl_s=900.0)
    dominio_canonico = str(continuidade.get("dominio") or "").strip().casefold()
    dominio_canonico = {"arquivos": "arquivo"}.get(dominio_canonico, dominio_canonico)
    if dominio_canonico in {"arquivo", "app", "site", "iot", "musica"}:
        return dominio_canonico, 0.96
    candidatos: list[tuple[str, float]] = []
    agora = time.time()
    focos: dict[str, Any] = (
        dict(mente.get("focos_por_dominio") or {})
        if isinstance(mente.get("focos_por_dominio"), dict) else {}
    )
    for dominio, foco in focos.items():
        if not isinstance(foco, dict):
            continue
        try:
            ts = float(foco.get("ts") or 0.0)
        except Exception:
            ts = 0.0
        if ts and agora - ts <= 600:
            candidatos.append((str(dominio), ts))
    if estrutura:
        try:
            ts_estrutura = float(mente.get("ultima_estrutura_arquivo_ts") or 0.0)
        except Exception:
            ts_estrutura = 0.0
        candidatos.append(("arquivo", ts_estrutura or agora - 1))
    if not candidatos:
        habilidade = str(mente.get("ultima_habilidade") or "").casefold()
        intent = str(mente.get("ultima_acao_intent") or mente.get("ultima_intencao") or "").upper()
        if habilidade in {"arquivo", "arquivos"} or intent in {
            "CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "MOVE_ITEM", "FILE_TRANSACTION",
        }:
            return "arquivo", 0.72
        if intent in {"IOT_CONTROL", "IOT_STATUS"}:
            return "iot", 0.70
        if intent in {"MEDIA_CONTROL", "PLAYLIST_PLAY", "MUSIC_SEARCH"}:
            return "musica", 0.68
        if intent in {"OPEN_URL", "CLOSE_TAB"}:
            return "site", 0.68
        if intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"}:
            return "app", 0.68
        return "", 0.0
    aprendizado: dict[str, Any] = (
        dict(mente.get("aprendizado_continuidade") or {})
        if isinstance(mente.get("aprendizado_continuidade"), dict) else {}
    )
    conflitos: dict[str, Any] = (
        dict(aprendizado.get("preferencias_conflito") or {})
        if isinstance(aprendizado.get("preferencias_conflito"), dict) else {}
    )
    origem_atual = max(candidatos, key=lambda item: item[1])[0]
    candidatos_ajustados = []
    for dominio, pontuacao in candidatos:
        try:
            reforco = int(conflitos.get(f"{origem_atual}>{dominio}") or 0)
        except Exception:
            reforco = 0
        candidatos_ajustados.append((dominio, pontuacao + min(60.0, reforco * 15.0)))
    dominio, _ = max(candidatos_ajustados, key=lambda item: item[1])
    return dominio, 0.82


def _recriar_estrutura(estrutura: Dict[str, Any]) -> tuple[str, Dict[str, Any], str]:
    dados = dict(estrutura or {})
    nome_pasta = str(dados.get("nome") or dados.get("pasta") or dados.get("alvo") or "").strip()
    arquivo = str(dados.get("arquivo_nome") or dados.get("nome_arquivo") or "").strip()
    if nome_pasta:
        params = {"nome": nome_pasta}
        for chave in ("pasta_pai", "pasta_interna", "mover_item", "arquivo_nome", "arquivo_conteudo", "target"):
            if str(dados.get(chave) or "").strip():
                params[chave] = dados[chave]
        return "CREATE_FOLDER", params, nome_pasta
    if arquivo:
        return "CREATE_FILE", {
            "arquivo_nome": arquivo,
            "arquivo_conteudo": str(dados.get("arquivo_conteudo") or ""),
            "target": str(dados.get("target") or "pc_a"),
        }, arquivo
    return "", {}, ""


def _alvo_contextual(mente: Dict[str, Any], dominio: str, params: Dict[str, Any]) -> str:
    chaves = {
        "app": ("nome_app", "app", "nome"),
        "site": ("alvo", "url", "site"),
        "iot": ("alvo", "dispositivo"),
        "musica": ("alvo", "musica", "nome"),
    }.get(dominio, ("alvo",))
    for chave in chaves:
        valor = str(params.get(chave) or "").strip()
        if valor:
            return valor
    ultima_musica = mente.get("ultima_musica_mencionada")
    titulo_mencionado = (
        str(ultima_musica.get("titulo") or "").strip()
        if isinstance(ultima_musica, dict) else ""
    )
    fallback = {
        "app": mente.get("ultimo_app_janela"),
        "site": mente.get("ultimo_site_aba"),
        "iot": mente.get("ultimo_dispositivo_iot"),
        "musica": titulo_mencionado or mente.get("musica_atual_titulo") or "musica",
    }
    return str(fallback.get(dominio) or mente.get("ultimo_alvo") or "").strip()


def _decisao_outro_dominio(
    *,
    dominio: str,
    acao: str,
    relacao: str,
    ultimo_intent: str,
    ultimo_params: Dict[str, Any],
    alvo: str,
    confianca: float,
) -> DecisaoContinuidade:
    mapas = {
        "app": {"ABRIR": "APP_OPEN", "FECHAR": "CLOSE_APP"},
        "site": {"ABRIR": "OPEN_URL", "FECHAR": "CLOSE_TAB"},
        "iot": {"LIGAR": "IOT_CONTROL", "DESLIGAR": "IOT_CONTROL"},
        "musica": {
            "PAUSAR": "MEDIA_CONTROL", "RETOMAR": "MEDIA_CONTROL",
            "EXECUTAR": "MEDIA_CONTROL", "AVANCAR": "MEDIA_CONTROL",
            "RETROCEDER": "MEDIA_CONTROL",
        },
    }
    intent = mapas.get(dominio, {}).get(acao, "")
    params: Dict[str, Any] = {}
    if dominio == "app" and intent:
        params = {"nome_app": alvo}
        if intent == "APP_OPEN":
            params["modo"] = "focus"
    elif dominio == "site" and intent:
        params = {"alvo": alvo}
    elif dominio == "iot" and intent:
        params = {"acao": "ligar" if acao == "LIGAR" else "desligar", "alvo": alvo}
    elif dominio == "musica" and intent:
        if acao == "EXECUTAR" and relacao == "REFERENCIAR" and alvo.casefold() != "musica":
            intent = "MUSIC_SEARCH"
            params = {"query": alvo, "origem": "referencia_fala_verificada"}
        else:
            comando = {
                "PAUSAR": "pause", "RETOMAR": "play", "EXECUTAR": "replay",
                "AVANCAR": "next", "RETROCEDER": "prev",
            }[acao]
            params = {"acao": comando, "platform": "music", "referencia_contextual": True}

    inversos = {
        "APP_OPEN": ("CLOSE_APP", {"nome_app": alvo}),
        "CLOSE_APP": ("APP_OPEN", {"nome_app": alvo, "modo": "focus"}),
        "OPEN_URL": ("CLOSE_TAB", {"alvo": alvo}),
        "CLOSE_TAB": ("OPEN_URL", {"alvo": alvo}),
    }
    if relacao == "REVERTER" and ultimo_intent in inversos:
        intent, params = inversos[ultimo_intent]
    elif relacao == "REVERTER" and dominio == "iot" and ultimo_intent in {"IOT_CONTROL", "IOT_STATUS"}:
        anterior = str(ultimo_params.get("acao") or "").lower()
        if anterior in {"ligar", "desligar"}:
            intent = "IOT_CONTROL"
            params = {"acao": "desligar" if anterior == "ligar" else "ligar", "alvo": alvo}
    elif relacao == "REVERTER" and dominio == "musica" and ultimo_intent == "MEDIA_CONTROL":
        anterior = str(ultimo_params.get("acao") or "").lower()
        if anterior in {"pause", "play"}:
            intent = "MEDIA_CONTROL"
            params = {"acao": "play" if anterior == "pause" else "pause", "platform": "music"}

    repetiveis = {
        "APP_OPEN", "CLOSE_APP", "OPEN_URL", "CLOSE_TAB", "IOT_CONTROL",
        "IOT_STATUS", "MEDIA_CONTROL", "PLAYLIST_PLAY", "MUSIC_SEARCH",
    }
    if relacao == "REPETIR" and not intent and ultimo_intent in repetiveis:
        intent = ultimo_intent
        params = dict(ultimo_params)

    if not intent or not params:
        return DecisaoContinuidade(
            operacao=relacao or acao,
            dominio=dominio,
            acao=acao,
            confianca=min(0.55, confianca),
            motivo="relacao reconhecida sem acao segura",
        )
    return DecisaoContinuidade(
        operacao=relacao or acao,
        dominio=dominio,
        acao=_acao_da_intencao(intent, params) or acao,
        intent=intent,
        alvo=alvo,
        params=params,
        confianca=min(0.96, confianca + 0.1),
        motivo="acao resolvida pela continuidade do dominio",
    )


def resolver_continuidade_semantica(
    texto: str,
    *,
    mente: Dict[str, Any] | None,
    estrutura_arquivo: Dict[str, Any] | None = None,
) -> DecisaoContinuidade:
    normalizado = _normalizar(texto)
    tokens = normalizado.split()
    if not tokens:
        return DecisaoContinuidade()
    if re.match(
        r"^(?:como\s+(?:eu\s+)?(?:faria|mudaria|trocaria|alteraria)|"
        r"se\s+(?:eu\s+)?(?:mudar|mudasse|trocar|trocasse)|"
        r"nao\s+(?:muda|mude|troca|troque|altera|altere|renomeia|renomeie))\b",
        normalizado,
    ):
        return DecisaoContinuidade(
            operacao="BLOQUEAR_SEM_AUTORIZACAO",
            confianca=0.99,
            motivo="hipotese ou negacao nao autoriza mutacao de arquivo",
        )
    if "playlist" in tokens:
        return DecisaoContinuidade()

    estado = dict(mente or {})
    estrutura = dict(estrutura_arquivo or {})
    retrato = estado.get("retrato_turno_atual")
    retrato = dict(retrato) if isinstance(retrato, dict) else {}
    referencia = retrato.get("referencia_resolvida")
    referencia = dict(referencia) if isinstance(referencia, dict) else {}
    tipo_referencia = str(referencia.get("tipo") or "").casefold()
    nome_referencia = str(referencia.get("nome") or "").strip()
    pedido_musica_do_referente = bool(
        _tem_radical(tokens, "toc", "coloc", "bot", "poe", "põe")
        and set(tokens).intersection({"musica", "som", "faixa", "cancao"})
        and set(tokens).intersection({"dele", "dela", "desse", "dessa"})
    )
    if pedido_musica_do_referente and tipo_referencia in {
        "artista", "cantor", "cantora", "banda", "referencia_nomeada",
    } and nome_referencia:
        return DecisaoContinuidade(
            operacao="BUSCAR_OBRA_DO_REFERENTE",
            dominio="musica",
            acao="BUSCAR",
            intent="MUSIC_SEARCH",
            alvo=nome_referencia,
            params={"query": nome_referencia, "referencia_contextual": True},
            confianca=0.99,
            motivo="pedido de musica resolvido pelo artista citado na conversa",
        )
    relacao = _relacao_semantica(tokens)
    acao = _acao_semantica(tokens)
    # Este resolvedor cuida de continuidade, nao substitui comandos completos.
    # Uma acao sem pronome, repeticao ou reversao continua no roteador normal.
    if not relacao:
        return DecisaoContinuidade()

    dominio = _dominio_explicito(tokens)
    confianca_dominio = 0.98 if dominio else 0.0
    if not dominio:
        dominio, confianca_dominio = _dominio_contextual(estado, estrutura)
    if not dominio:
        return DecisaoContinuidade(operacao=relacao or acao, confianca=0.25, motivo="dominio ambiguo")

    ultimo_intent = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").upper()
    ultimo_params: Dict[str, Any] = (
        dict(estado.get("ultima_acao_params") or {})
        if isinstance(estado.get("ultima_acao_params"), dict) else {}
    )
    # Reversão só é segura quando a ação anterior realmente terminou. Se ainda
    # está pendente ou falhou, o roteador deve preservar o cancelamento normal.
    rejeicao_de_efeito = {"quero", "mais", "nao"} <= set(tokens)
    if relacao == "REVERTER" and rejeicao_de_efeito and not (
        estado.get("ultima_acao_confirmada") is True
        or estado.get("ultima_acao_ok") is True
    ):
        return DecisaoContinuidade(
            operacao=relacao,
            dominio=dominio,
            confianca=0.45,
            motivo="acao anterior nao confirmada; reversao insegura",
        )
    if not acao:
        acao_anterior = _acao_da_intencao(ultimo_intent, ultimo_params)
        acao = _acao_aprendida_para_contexto(estado, dominio, acao_anterior)
    if dominio == "arquivo":
        if acao == "RENOMEAR":
            caminho_atual = str(estrutura.get("caminho") or "").strip()
            nome_atual = str(
                os.path.basename(caminho_atual) if caminho_atual else (
                    estrutura.get("arquivo_nome") or estrutura.get("nome_arquivo")
                    or estrutura.get("nome") or estrutura.get("pasta") or estrutura.get("alvo")
                    or estado.get("ultimo_arquivo") or estado.get("ultima_pasta") or ""
                )
            ).strip()
            troca_extensao = bool(set(tokens).intersection({"tipo", "extensao", "formato"}))
            novo_nome = ""
            if troca_extensao:
                nova_extensao = re.search(
                    r"\b(?:para|pra)\s+(?:(?:um|uma|o|a)\s+)?(\.?[a-z0-9]{1,12})\s*$",
                    normalizado,
                )
                if nova_extensao:
                    novo_nome = nome_com_nova_extensao_textual(
                        nome_atual,
                        nova_extensao.group(1),
                    )
            else:
                novo_nome_match = re.search(
                    r"\b(?:para|pra|como|de)\s+(?:(?:um|uma|o|a)\s+)?"
                    r"([a-z0-9_.-]+)\s*$",
                    normalizado,
                )
                novo_nome = str(
                    novo_nome_match.group(1) if novo_nome_match else ""
                ).strip()
            if nome_atual and novo_nome:
                if caminho_atual:
                    origem = caminho_atual
                else:
                    pasta_pai = str(estrutura.get("pasta_pai") or "Downloads").strip()
                    home_usuario = os.path.expanduser("~")
                    bases = {
                        "downloads": os.path.join(home_usuario, "Downloads"),
                        "desktop": os.path.join(home_usuario, "Desktop"),
                        "documentos": os.path.join(home_usuario, "Documents"),
                    }
                    base = bases.get(pasta_pai.casefold(), pasta_pai)
                    origem = os.path.join(base, nome_atual) if base else nome_atual
                return DecisaoContinuidade(
                    operacao="RENOMEAR_REFERENCIA",
                    dominio="arquivo",
                    acao="RENOMEAR",
                    intent="FILE_TRANSACTION",
                    alvo=nome_atual,
                    params={"operacao": "renomear", "origem": origem, "novo_nome": novo_nome},
                    confianca=min(0.97, confianca_dominio + 0.1),
                    motivo="renomeacao aplicada a estrutura recente",
                )
        if acao == "REMOVER":
            nome_exibicao = str(
                estrutura.get("nome") or estrutura.get("pasta") or estrutura.get("alvo")
                or estrutura.get("arquivo_nome") or estado.get("ultima_pasta") or estado.get("ultimo_arquivo") or ""
            ).strip()
            caminho_exato = str(estrutura.get("caminho") or "").strip()
            alvo_remocao = caminho_exato or nome_exibicao
            if alvo_remocao:
                tipo = "pasta" if str(estrutura.get("nome") or estrutura.get("pasta") or estado.get("ultima_pasta") or "").strip() else "arquivo"
                return DecisaoContinuidade(
                    operacao="REMOVER_REFERENCIA",
                    dominio="arquivo",
                    acao="REMOVER",
                    intent="DELETE_ITEM",
                    alvo=nome_exibicao or os.path.basename(alvo_remocao),
                    params={"alvo": alvo_remocao, "tipo": tipo},
                    confianca=min(0.97, confianca_dominio + 0.1),
                    motivo="acao de remocao aplicada a estrutura recente",
                )
        quer_recriar = acao == "CRIAR" and relacao in {"REPETIR", "REVERTER", "REFERENCIAR"}
        quer_reverter_exclusao = relacao == "REVERTER" and ultimo_intent == "DELETE_ITEM"
        if quer_recriar or quer_reverter_exclusao:
            intent, params, alvo = _recriar_estrutura(estrutura)
            if intent:
                return DecisaoContinuidade(
                    operacao="REVERTER_EXCLUSAO" if ultimo_intent == "DELETE_ITEM" else "REPETIR_CRIACAO",
                    dominio="arquivo",
                    acao="CRIAR",
                    intent=intent,
                    alvo=alvo,
                    params=params,
                    confianca=min(0.98, confianca_dominio + 0.12),
                    motivo="estrutura recente permite reconstruir o item",
                )

    if dominio in {"app", "site", "iot", "musica"}:
        alvo = _alvo_contextual(estado, dominio, ultimo_params)
        if alvo:
            return _decisao_outro_dominio(
                dominio=dominio,
                acao=acao,
                relacao=relacao,
                ultimo_intent=ultimo_intent,
                ultimo_params=ultimo_params,
                alvo=alvo,
                confianca=confianca_dominio,
            )

    return DecisaoContinuidade(
        operacao=relacao or acao,
        dominio=dominio,
        confianca=min(0.55, confianca_dominio),
        motivo="sem mapeamento seguro para execucao",
    )


def interpretar_continuidade_semantica_llm(
    texto: str,
    *,
    mente: Dict[str, Any] | None,
    estrutura_arquivo: Dict[str, Any] | None,
    enviar_mensagem: Any,
) -> DecisaoContinuidade:
    """Usa o modelo apenas para classificar papeis; parametros continuam locais."""
    if not callable(enviar_mensagem):
        return DecisaoContinuidade()
    estado = dict(mente or {})
    estrutura = dict(estrutura_arquivo or {})
    ultimo_params: Dict[str, Any] = (
        dict(estado.get("ultima_acao_params") or {})
        if isinstance(estado.get("ultima_acao_params"), dict) else {}
    )
    payload = {
        "fala": str(texto or "")[:180],
        "ultima_intencao": str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or ""),
        "ultimo_alvo": str(estado.get("ultima_acao_alvo") or estado.get("ultimo_alvo") or ""),
        "ultimos_params": ultimo_params,
        "estrutura_arquivo": estrutura,
        "focos": {
            dominio: str((foco or {}).get("alvo") or (foco or {}).get("topico") or "")
            for dominio, foco in dict(estado.get("focos_por_dominio") or {}).items()
            if isinstance(foco, dict)
        },
    }
    prompt = (
        "Classifique uma continuidade curta de comando em portugues. Nao execute e nao invente alvo. "
        "Responda somente JSON: "
        '{"dominio":"arquivo|app|site|iot|musica|indefinido",'
        '"operacao":"REPETIR|REVERTER|REFERENCIAR|NOVA_ACAO|INDEFINIDO",'
        '"acao":"CRIAR|REMOVER|ABRIR|FECHAR|LIGAR|DESLIGAR|PAUSAR|RETOMAR|EXECUTAR|INDEFINIDO",'
        '"confianca":0.0,"motivo":"curto"}.\n'
        f"Contexto: {json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        bruto = enviar_mensagem(
            [
                {"role": "system", "content": "Voce e um classificador semantico estrito."},
                {"role": "user", "content": prompt},
            ],
            _com_tools=False,
            max_tokens=100,
            modo_rapido=True,
            _tipo_chamada="interpretacao",
            _classe_timeout="rapida",
        )
        match = re.search(r"\{.*\}", str(bruto or ""), re.DOTALL)
        dados = json.loads(match.group(0)) if match else {}
    except Exception:
        return DecisaoContinuidade()

    dominios = {"arquivo", "app", "site", "iot", "musica"}
    operacoes = {"REPETIR", "REVERTER", "REFERENCIAR", "NOVA_ACAO"}
    acoes = {"CRIAR", "REMOVER", "ABRIR", "FECHAR", "LIGAR", "DESLIGAR", "PAUSAR", "RETOMAR", "EXECUTAR"}
    dominio = str(dados.get("dominio") or "").lower()
    operacao = str(dados.get("operacao") or "").upper()
    acao = str(dados.get("acao") or "").upper()
    try:
        confianca = float(dados.get("confianca") or 0.0)
    except Exception:
        confianca = 0.0
    if dominio not in dominios or operacao not in operacoes or acao not in acoes or confianca < 0.68:
        return DecisaoContinuidade()

    ultimo_intent = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").upper()
    if dominio == "arquivo":
        if acao == "REMOVER":
            nome = str(estrutura.get("nome") or estrutura.get("pasta") or estrutura.get("arquivo_nome") or "").strip()
            caminho = str(estrutura.get("caminho") or "").strip()
            alvo_remocao = caminho or nome
            if alvo_remocao:
                tipo = "pasta" if estrutura.get("nome") or estrutura.get("pasta") else "arquivo"
                return DecisaoContinuidade(
                    operacao=operacao, dominio=dominio, acao="REMOVER", intent="DELETE_ITEM", alvo=nome or os.path.basename(alvo_remocao),
                    params={"alvo": alvo_remocao, "tipo": tipo}, confianca=confianca,
                    motivo=str(dados.get("motivo") or "desambiguado pela IA"),
                )
        if acao == "CRIAR":
            intent, params, alvo = _recriar_estrutura(estrutura)
            if intent:
                return DecisaoContinuidade(
                    operacao=operacao, dominio=dominio, acao="CRIAR", intent=intent, alvo=alvo,
                    params=params, confianca=confianca,
                    motivo=str(dados.get("motivo") or "desambiguado pela IA"),
                )
        return DecisaoContinuidade()

    alvo = _alvo_contextual(estado, dominio, ultimo_params)
    if not alvo:
        return DecisaoContinuidade()
    decisao = _decisao_outro_dominio(
        dominio=dominio,
        acao=acao,
        relacao=operacao,
        ultimo_intent=ultimo_intent,
        ultimo_params=ultimo_params,
        alvo=alvo,
        confianca=confianca,
    )
    return decisao


def registrar_decisao_semantica(
    mente: Dict[str, Any] | None,
    decisao: DecisaoContinuidade,
    texto: str,
) -> Dict[str, Any]:
    estado = dict(mente or {})
    if not decisao.intent or decisao.confianca < 0.60:
        return estado
    estado["ultima_decisao_semantica"] = {
        "texto": str(texto or "")[:180],
        "operacao": decisao.operacao,
        "dominio": decisao.dominio,
        "acao": decisao.acao or _acao_da_intencao(decisao.intent, decisao.params),
        "intent": decisao.intent,
        "alvo": decisao.alvo,
        "confianca": round(float(decisao.confianca), 3),
        "ts": time.time(),
    }
    return estado


def _trecho_corrigido(normalizado: str) -> str:
    """Isola a parte corretiva da fala usando sua estrutura, nao frases inteiras."""
    partes = re.split(
        r"\b(?:mas|era\s+para|queria|quis\s+dizer|estou\s+falando|to\s+falando|me\s+refiro)\b",
        normalizado,
    )
    uteis = [parte.strip() for parte in partes if parte.strip()]
    return uteis[-1] if len(uteis) > 1 else normalizado


def aprender_correcao_semantica(
    mente: Dict[str, Any] | None,
    texto: str,
    *,
    ttl_s: float = 180.0,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Aprende correcoes explicitas de dominio ou operacao sem decorar frases."""
    estado = dict(mente or {})
    anterior = estado.get("ultima_decisao_semantica") if isinstance(estado.get("ultima_decisao_semantica"), dict) else {}
    if not anterior:
        return estado, {}
    try:
        idade = time.time() - float(anterior.get("ts") or 0.0)
    except Exception:
        idade = ttl_s + 1
    if idade < 0 or idade > ttl_s:
        return estado, {}

    normalizado = _normalizar(texto)
    tokens = normalizado.split()
    trecho_correto = _trecho_corrigido(normalizado)
    tokens_corretos = trecho_correto.split()
    dominio_correto = _dominio_explicito(tokens_corretos) or _dominio_explicito(tokens)
    acao_correta = _acao_semantica(tokens_corretos)
    sinal_correcao = bool(
        _tem_radical(tokens, "corrig", "refer", "fal", "diz", "quer")
        or set(tokens).intersection({"nao", "errado", "outra", "outro"})
    )
    dominio_anterior = str(anterior.get("dominio") or "").strip().lower()
    acao_anterior = str(anterior.get("acao") or "").strip().upper()
    if not sinal_correcao or not dominio_anterior:
        return estado, {}

    correcao_dominio = bool(dominio_correto and dominio_correto != dominio_anterior)
    dominio_operacao = dominio_correto or dominio_anterior
    correcao_operacao = bool(acao_correta and acao_anterior and acao_correta != acao_anterior)
    if not correcao_dominio and not correcao_operacao:
        return estado, {}

    aprendizado = dict(estado.get("aprendizado_continuidade") or {})
    conflitos = dict(aprendizado.get("preferencias_conflito") or {})
    preferencias_operacao = dict(aprendizado.get("preferencias_operacao") or {})
    if correcao_dominio:
        chave = f"{dominio_anterior}>{dominio_correto}"
        conflitos[chave] = min(10, int(conflitos.get(chave) or 0) + 1)
    if correcao_operacao:
        chave_operacao = f"{dominio_operacao}:{acao_anterior}>{acao_correta}"
        preferencias_operacao[chave_operacao] = min(
            10, int(preferencias_operacao.get(chave_operacao) or 0) + 1
        )
    correcoes = list(aprendizado.get("correcoes") or [])
    evento = {
        "ts": time.time(),
        "texto": normalizado[:180],
        "dominio_escolhido": dominio_anterior,
        "dominio_correto": dominio_correto or dominio_anterior,
        "acao_escolhida": acao_anterior,
        "acao_correta": acao_correta,
        "intent_anterior": str(anterior.get("intent") or ""),
        "alvo_anterior": str(anterior.get("alvo") or ""),
    }
    correcoes.append(evento)
    aprendizado["preferencias_conflito"] = conflitos
    aprendizado["preferencias_operacao"] = preferencias_operacao
    aprendizado["correcoes"] = correcoes[-30:]
    aprendizado["ultima_correcao_ts"] = evento["ts"]
    estado["aprendizado_continuidade"] = aprendizado
    estado["ultima_decisao_semantica"] = {}
    return estado, evento
