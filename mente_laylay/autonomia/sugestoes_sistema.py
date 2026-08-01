"""Confirmação e execução de sugestões práticas da mente da Laylay."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Callable, Dict

from mente_laylay.integracao.registro_conversa_llm import resolver_enviador_modelo

from mente_laylay.autonomia.porteiro_proatividade import categoria_sugestao
from mente_laylay.cognicao.erros_navegador import resumir_erro_navegador
from mente_laylay.memoria_mental.estado_continuidades import (
    SUGESTAO_SEM_RESPOSTA_TIMEOUT_S,
)


def _get(ctx: Dict[str, Any], chave: str, padrao: Any = None) -> Any:
    return ctx.get(chave, padrao) if isinstance(ctx, dict) else padrao


_INTENTS_CONTRAPROPOSTA_SEGURAS = {
    "IOT_CONTROL", "APP_OPEN", "OPEN_URL", "MUSIC_SEARCH", "PLAYLIST_PLAY",
    "WEATHER", "EMAIL_READ", "VOLUME", "MEDIA_CONTROL", "ORGANIZAR_DESKTOP",
    "RESUMIR_PAGINA",
}


def chave_preferencia_sugestao(comando: str, payload: Dict[str, Any] | None = None) -> str:
    dados = dict(payload or {})
    origem = str(dados.get("preferencia_origem_chave") or "").strip()
    if origem:
        return origem
    comando_norm = str(comando or "").strip().upper() or "SUGESTAO"
    if comando_norm == "EXECUTE_INTENT":
        interna = dados.get("intent") if isinstance(dados.get("intent"), dict) else {}
        intent = str(interna.get("intent") or "").strip().upper()
        params = interna.get("params") if isinstance(interna.get("params"), dict) else {}
        acao = str(params.get("acao") or params.get("modo") or "").strip().lower()
        alvo = str(params.get("alvo") or params.get("nome_app") or params.get("query") or "").strip().lower()
        return ":".join(parte for parte in (comando_norm, intent, acao, alvo) if parte)
    return comando_norm


def parece_contraproposta(texto: str) -> bool:
    t = re.sub(r"\s+", " ", str(texto or "").strip().casefold())
    if not t:
        return False
    return bool(
        re.search(r"\b(?:melhor|prefiro|preferia|em vez|ao inves|ao invés|apenas|somente|só|so)\b", t)
        or re.match(r"^(?:não|nao)[, ]+.{3,}", t)
        or re.search(
            r"\bmas\b.+\b(?:faz|faça|deixa|coloca|abre|liga|desliga|diminui|aumenta|baixa|ajusta)\b",
            t,
        )
        or re.search(r"\b(?:não|nao) (?:faz|faça|quero) .+\b(?:faz|faça|deixa|coloca|abre|liga|desliga|diminui|aumenta)\b", t)
    )


def descrever_intencao_alternativa(intencao: Dict[str, Any]) -> str:
    intent = str(intencao.get("intent") or "").strip().upper()
    params = intencao.get("params") if isinstance(intencao.get("params"), dict) else {}
    acao = str(params.get("acao") or params.get("modo") or "").strip().lower()
    alvo = str(params.get("alvo") or params.get("nome_app") or params.get("query") or "").strip()
    if intent == "IOT_CONTROL" and acao == "ajustar_brilho":
        valor = params.get("valor")
        return f"diminuir o brilho da luz para {valor} por cento" if valor is not None else "diminuir o brilho da luz"
    if intent == "IOT_CONTROL":
        verbo = {"ligar": "ligar", "desligar": "apagar", "ajustar_cor": "mudar a cor de"}.get(acao, acao or "ajustar")
        return f"{verbo} {alvo or 'o dispositivo'}".strip()
    if intent == "VOLUME":
        nivel = params.get("nivel_volume", params.get("value"))
        return f"deixar o volume em {nivel} por cento" if nivel is not None else "ajustar o volume"
    if intent == "APP_OPEN":
        return f"abrir {alvo or params.get('nome') or 'o aplicativo'}"
    if intent == "MUSIC_SEARCH":
        return f"procurar {alvo or 'outra música'}"
    return str(params.get("descricao") or alvo or intent.replace("_", " ").lower()).strip()


def verbalizar_pergunta_alternativa(intencao: Dict[str, Any]) -> str:
    intent = str(intencao.get("intent") or "").strip().upper()
    params = intencao.get("params") if isinstance(intencao.get("params"), dict) else {}
    acao = str(params.get("acao") or params.get("modo") or "").strip().lower()
    alvo = str(params.get("alvo") or params.get("nome_app") or params.get("query") or "").strip()
    if intent == "IOT_CONTROL" and acao == "ajustar_brilho":
        valor = params.get("valor")
        return f"diminua o brilho da luz para {valor} por cento" if valor is not None else "diminua o brilho da luz"
    if intent == "IOT_CONTROL" and acao == "ligar":
        return f"ligue {alvo or 'o dispositivo'}"
    if intent == "IOT_CONTROL" and acao == "desligar":
        return f"apague {alvo or 'o dispositivo'}"
    if intent == "VOLUME":
        nivel = params.get("nivel_volume", params.get("value"))
        return f"deixe o volume em {nivel} por cento" if nivel is not None else "ajuste o volume"
    if intent == "APP_OPEN":
        return f"abra {alvo or params.get('nome') or 'o aplicativo'}"
    if intent == "MUSIC_SEARCH":
        return f"procure {alvo or 'outra música'}"
    return f"faça a alternativa que você escolheu ({descrever_intencao_alternativa(intencao)})"


def aplicar_preferencia_sugestao(
    comando: str,
    payload: Dict[str, Any] | None,
    fala: str,
    preferencia_get: Callable[[str, Dict[str, Any]], Any] | None,
) -> tuple[str, Dict[str, Any], str]:
    dados = dict(payload or {})
    if not callable(preferencia_get):
        return comando, dados, fala
    try:
        preferencia = preferencia_get(str(comando or ""), dados)
    except Exception:
        preferencia = None
    if not isinstance(preferencia, dict):
        return comando, dados, fala
    alternativa = preferencia.get("alternativa")
    if not isinstance(alternativa, dict):
        return comando, dados, fala
    intent = str(alternativa.get("intent") or "").strip().upper()
    if intent not in _INTENTS_CONTRAPROPOSTA_SEGURAS:
        return comando, dados, fala
    chave = chave_preferencia_sugestao(comando, dados)
    descricao = str(preferencia.get("descricao") or descrever_intencao_alternativa(alternativa)).strip()
    novo_payload = {
        "intent": alternativa,
        "descricao": descricao,
        "origem": "preferencia_aprendida",
        "preferencia_origem_chave": chave,
        "preferencia_hipotese_chave": str(
            ((preferencia.get("_aprendizado") or {}).get("hipotese_chave") or "")
            if isinstance(preferencia.get("_aprendizado"), dict) else ""
        ),
    }
    fala_futura = str(
        preferencia.get("fala_futura")
        or f"Quer que eu {verbalizar_pergunta_alternativa(alternativa)}?"
    ).strip()
    return "EXECUTE_INTENT", novo_payload, fala_futura


def detectar_sugestao_indireta(
    texto: str,
    estado_mental: Dict[str, Any] | None = None,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any] | None:
    """Converte uma necessidade implícita em proposta, nunca em execução direta."""
    bruto = str(texto or "").strip()
    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.lower()
    t = re.sub(r"\s+", " ", str(t or "")).strip()
    if not t or "?" in bruto:
        return None
    mente = estado_mental if isinstance(estado_mental, dict) else {}

    def _acao_confiavel(
        acao_sugerida: Dict[str, Any],
        *,
        descricao: str,
        fala: str,
        dominio: str,
        confianca: float,
    ) -> Dict[str, Any]:
        """Padroniza necessidades inequívocas sem contornar a governança central."""
        return {
            "intent": "SUGGEST_ACTION",
            "params": {
                "acao_sugerida": acao_sugerida,
                "descricao": descricao,
                "fala": fala,
                "origem": "fala_indireta_confiavel",
                "dominio": dominio,
                "confianca": confianca,
                "risco": "baixo",
                "reversivel": True,
                "execucao_autonoma_elegivel": True,
            },
        }

    cores_contextuais = {
        "roxa": ("roxo", (128, 0, 255)),
        "roxo": ("roxo", (128, 0, 255)),
        "azul": ("azul", (0, 0, 255)),
        "vermelha": ("vermelho", (255, 0, 0)),
        "vermelho": ("vermelho", (255, 0, 0)),
        "verde": ("verde", (0, 255, 0)),
        "rosa": ("rosa", (255, 105, 180)),
        "amarela": ("amarelo", (255, 255, 0)),
        "amarelo": ("amarelo", (255, 255, 0)),
        "laranja": ("laranja", (255, 128, 0)),
    }
    preferencia_luz = re.search(
        r"^(?:eu\s+)?(?:gosto|prefiro)\s+(?:d[aeo]\s+)?(?:usar\s+)?(?:a\s+)?"
        r"(?:luz|lampada|iluminacao)\s+"
        r"(roxa|roxo|azul|vermelha|vermelho|verde|rosa|amarela|amarelo|laranja)\s+"
        r"(?:nesse|neste|a\s+esse|a\s+este)\s+hor[aá]rio\b",
        t,
    )
    if preferencia_luz:
        cor, rgb = cores_contextuais[preferencia_luz.group(1)]
        return _acao_confiavel(
            {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ajustar_cor", "alvo": "lampada_quarto",
                    "cor": cor, "rgb": rgb, "origem": "usuario_indireto",
                },
            },
            descricao=f"deixar a luz {preferencia_luz.group(1)}",
            fala=f"Quer que eu deixe a luz {preferencia_luz.group(1)}?",
            dominio="iot",
            confianca=0.94,
        )

    escuro = bool(re.search(
        r"^(?:aqui|o quarto|meu quarto|esse lugar|este lugar)?\s*"
        r"(?:esta|está|ta|tá|ficou)\s+(?:muito\s+)?(?:escuro|escura)(?:\s+(?:aqui|demais))?[.!]*$",
        t,
    ))
    if escuro:
        return _acao_confiavel(
            {
                "intent": "IOT_CONTROL",
                "params": {
                    "acao": "ligar", "alvo": "lampada_quarto",
                    "origem": "usuario_indireto",
                },
            },
            descricao="ligar a luz",
            fala="Ficou escuro por aí. Quer que eu ligue a luz?",
            dominio="iot",
            confianca=0.95,
        )

    volume_alto = bool(re.search(
        r"^(?:(?:o|a)\s+)?(?:som|audio|áudio|volume|musica|música)\s+"
        r"(?:esta|está|ta|tá|ficou)\s+(?:muito\s+alt[oa]|alt[oa]\s+demais)(?:\s+aqui)?[.!]*$",
        t,
    ))
    volume_baixo = bool(re.search(
        r"^(?:(?:o|a)\s+)?(?:som|audio|áudio|volume|musica|música)\s+"
        r"(?:esta|está|ta|tá|ficou)\s+(?:muito\s+baix[oa]|baix[oa]\s+demais)(?:\s+aqui)?[.!]*$",
        t,
    ))
    if volume_alto or volume_baixo:
        delta = -10 if volume_alto else 10
        direcao = "abaixar" if volume_alto else "aumentar"
        return _acao_confiavel(
            {
                "intent": "VOLUME_RELATIVE",
                "params": {"delta": delta, "origem": "usuario_indireto"},
            },
            descricao=f"{direcao} um pouco o volume",
            fala=f"O som está {'alto' if volume_alto else 'baixo'}. Quer que eu {direcao} um pouco?",
            dominio="conforto",
            confianca=0.95,
        )

    desejo_musical = re.search(
        r"^(?:eu\s+)?(?:queria|gostaria\s+de|estou\s+a\s+fim\s+de|"
        r"to\s+a\s+fim\s+de|tô\s+a\s+fim\s+de|estou\s+com\s+vontade\s+de|"
        r"to\s+com\s+vontade\s+de|tô\s+com\s+vontade\s+de)\s+"
        r"(?:ouvir|escutar|colocar)\s+(.+?)[.!]*$",
        t,
    )
    if desejo_musical:
        query = re.sub(r"^(?:uma|um|alguma)\s+(?:musica|música|som)\s+(?:de\s+)?", "", desejo_musical.group(1)).strip()
        query = re.sub(r"^(?:uma|um)\s+", "", query).strip()
        if query and query not in {"musica", "música", "alguma coisa", "qualquer coisa"}:
            return _acao_confiavel(
                {
                    "intent": "MUSIC_SEARCH",
                    "params": {"query": query, "origem": "usuario_indireto"},
                },
                descricao=f"colocar {query}",
                fala=f"Você está no clima de {query}. Quer que eu coloque?",
                dominio="musica",
                confianca=0.95,
            )

    precisa_pausa = bool(
        re.search(
            r"^(?:essa|a)\s+(?:musica|música|faixa)\s+"
            r"(?:esta|está|ta|tá)\s+me\s+(?:distraindo|atrapalhando|incomodando)[.!]*$",
            t,
        )
        or re.search(r"^(?:eu\s+)?preciso\s+de\s+silencio\s+(?:agora|um\s+pouco)[.!]*$", t)
    )
    musica_parou = bool(re.search(
        r"^(?:a|essa)\s+(?:musica|música|faixa)\s+(?:parou|ficou\s+pausada)[.!]*$",
        t,
    ))
    musica_nao_combinou = bool(
        re.search(
            r"^(?:essa|a)\s+(?:musica|música|faixa)\s+"
            r"(?:nao|não)\s+(?:combinou|encaixou)(?:\s+com\s+(?:o\s+)?clima)?[.!]*$",
            t,
        )
        or re.search(r"^(?:eu\s+)?(?:nao|não)\s+gostei\s+dessa\s+(?:musica|música|faixa)[.!]*$", t)
    )
    if precisa_pausa or musica_parou or musica_nao_combinou:
        acao_midia = "pause" if precisa_pausa else ("play" if musica_parou else "next")
        descricao_midia = {
            "pause": "pausar a música",
            "play": "retomar a música",
            "next": "passar para a próxima música",
        }[acao_midia]
        fala_midia = {
            "pause": "Ela está atrapalhando seu foco. Quer que eu pause?",
            "play": "A música parou. Quer que eu retome?",
            "next": "Essa não combinou muito. Quer que eu passe para a próxima?",
        }[acao_midia]
        return _acao_confiavel(
            {
                "intent": "MEDIA_CONTROL",
                "params": {"acao": acao_midia, "platform": "music", "origem": "usuario_indireto"},
            },
            descricao=descricao_midia,
            fala=fala_midia,
            dominio="musica",
            confianca=0.95 if acao_midia != "next" else 0.92,
        )

    fome_sem_comida = bool(
        re.search(
            r"^(?:eu\s+)?(?:estou|to|tô)\s+(?:com\s+)?(?:muita\s+)?fome\s+"
            r"(?:e|mas)\s+(?:nao|não)\s+(?:tem|tenho)\s+(?:nada|comida)(?:\s+pront[oa])?.*$",
            t,
        )
        or re.search(r"^(?:eu\s+)?(?:queria|quero)\s+pedir\s+(?:alguma\s+)?comida[.!]*$", t)
    )
    if fome_sem_comida:
        return {
            "intent": "SUGGEST_ACTION",
            "params": {
                "acao_sugerida": {
                    "intent": "OPEN_URL",
                    "params": {"alvo": "https://www.ifood.com.br", "origem": "usuario_indireto"},
                },
                "descricao": "abrir o iFood",
                "fala": "Tá com cara de noite sem panela. Quer que eu abra o iFood pra você escolher algo?",
                "origem": "recomendacao_contextual",
                "dominio": "navegador",
                "confianca": 0.96,
                "risco": "baixo",
                "reversivel": False,
                "execucao_autonoma_elegivel": False,
            },
        }

    calor = bool(
        re.search(r"\b(?:estou|to|tô|ta|tá|ficou)\s+(?:com\s+)?(?:muito\s+)?calor\b", t)
        or re.search(r"\b(?:esta|está|ta|tá|ficou)\s+(?:muito\s+)?quente\s+(?:aqui|hoje|demais)\b", t)
    )
    frio = bool(
        re.search(r"\b(?:estou|to|tô|ta|tá|ficou)\s+(?:com\s+)?(?:muito\s+)?frio\b", t)
        or re.search(r"\b(?:esta|está|ta|tá|ficou)\s+(?:muito\s+)?frio\s+(?:aqui|hoje|demais)\b", t)
    )
    if not calor and not frio:
        return None

    # O último dispositivo pode ser uma lâmpada; uma necessidade térmica nunca
    # deve herdar esse alvo apenas por recência.
    alvo = "tomada_ventilador"
    estado_iot = mente.get("ultimo_estado_iot")
    ultimo_alvo = str(mente.get("ultimo_dispositivo_iot") or "").strip()
    if ultimo_alvo == alvo and calor and estado_iot is True:
        return None
    if ultimo_alvo == alvo and frio and estado_iot is False:
        return None
    acao = "ligar" if calor else "desligar"
    descricao = f"{acao} o ventilador"
    fala = (
        "Tá quente mesmo. Quer que eu ligue o ventilador?"
        if calor
        else "Esfriou por aí. Quer que eu desligue o ventilador?"
    )
    return _acao_confiavel(
        {
            "intent": "IOT_CONTROL",
            "params": {
                "acao": acao, "alvo": alvo, "origem": "usuario_indireto",
            },
        },
        descricao=descricao,
        fala=fala,
        dominio="iot",
        confianca=0.96,
    )


def registrar_sugestao_indireta(ctx: Dict[str, Any], resultado: Dict[str, Any] | None) -> bool:
    """Guarda uma sugestão genérica para confirmação posterior."""
    if not isinstance(resultado, dict):
        return False
    params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
    acao_sugerida = params.get("acao_sugerida")
    if not isinstance(acao_sugerida, dict):
        return False
    intent_sugerido = str(acao_sugerida.get("intent") or "").upper().strip()
    if not intent_sugerido or intent_sugerido in {"SUGGEST_ACTION", "CANCELAR_ACAO"}:
        return False
    try:
        confianca = float(params.get("confianca") or 0.0)
    except (TypeError, ValueError):
        confianca = 0.0
    registrar_oportunidade = _get(ctx, "registrar_oportunidade")
    if (
        bool(params.get("execucao_autonoma_elegivel"))
        and confianca >= 0.90
        and callable(registrar_oportunidade)
    ):
        decisao = dict(registrar_oportunidade({
            "tipo": "preferencia_contextual",
            "origem": str(params.get("origem") or "fala_indireta_confiavel"),
            "dominio": str(params.get("dominio") or ""),
            "risco": str(params.get("risco") or "baixo"),
            "confianca": confianca,
            "utilidade": 100,
            "executavel": True,
            "reversivel": bool(params.get("reversivel")),
            "acao_proposta": acao_sugerida,
            "validade_s": 30.0,
        }) or {})
        if str(decisao.get("decisao") or "") in {
            "executado", "execucao_falhou", "bloqueado_circuito",
        }:
            return True
    atualizar = _get(ctx, "continuidades_update")
    falar = _get(ctx, "falar")
    if not callable(atualizar) or not callable(falar):
        return False
    payload = {
        "intent": {
            "intent": intent_sugerido,
            "params": dict(acao_sugerida.get("params") or {}),
        },
        "descricao": str(params.get("descricao") or "executar a ação sugerida").strip(),
        "origem": str(params.get("origem") or "conversa_indireta").strip(),
    }
    comando, payload, fala_preferida = aplicar_preferencia_sugestao(
        "EXECUTE_INTENT",
        payload,
        str(params.get("fala") or "Eu consigo agir nisso. Quer que eu faça?"),
        _get(ctx, "preferencia_sugestao_get"),
    )
    atualizar(
        comando_sugerido=comando,
        comando_sugerido_payload=payload,
        comando_sugerido_estado="PENDING_CONFIRM",
        comando_sugerido_ts=time.time(),
        comando_pendente=comando,
        comando_pendente_payload=payload,
    )
    falar(fala_preferida, "calma", 1)
    return True


def processar_confirmacao_sugestao(ctx: Dict[str, Any], texto: str) -> bool:
    continuidades_get = _get(ctx, "continuidades_get")
    resetar_sugestao = _get(ctx, "resetar_sugestao")
    classificar_local = _get(ctx, "classificar_confirmacao_local")
    interpretar_llm = _get(ctx, "interpretar_confirmacao_llm")
    comando = continuidades_get("comando_sugerido") if callable(continuidades_get) else None
    payload = continuidades_get("comando_sugerido_payload") if callable(continuidades_get) else None
    estado = continuidades_get("comando_sugerido_estado", "NONE") if callable(continuidades_get) else "NONE"
    ts = continuidades_get("comando_sugerido_ts", 0.0) if callable(continuidades_get) else 0.0
    payload = payload if isinstance(payload, dict) else {}
    registrar_feedback = _get(ctx, "registrar_feedback_proatividade")

    if estado != "PENDING_CONFIRM" or not comando:
        return False
    if time.time() - float(ts or 0.0) >= SUGESTAO_SEM_RESPOSTA_TIMEOUT_S:
        if callable(registrar_feedback):
            try:
                registrar_feedback(
                    categoria_sugestao(comando, payload), None,
                    comando=comando, payload=payload, resultado="silencio",
                )
            except Exception:
                pass
        if callable(resetar_sugestao):
            resetar_sugestao()
        return False

    descricao = {
        "SYS_MODE_CODE": "ativar Modo Code (limpar abas vazias e tocar música de foco)",
        "SYS_MODE_GAMER": "ativar Modo Gamer (pausar música e fechar abas de estudo)",
        "SYS_ORGANIZE_DOWNLOADS": "organizar Downloads",
        "EXPLAIN_ERROR": "explicar o erro do navegador",
        "RELOAD_PAGE": "recarregar a página para tentar corrigir",
        "OPEN_SITE_ALT": "abrir um site alternativo",
        "EXECUTE_INTENT": str((payload or {}).get("descricao") or "executar a ação sugerida"),
        "TIME_LIGHT_ON": "ligar a luz do quarto porque anoiteceu",
        "TIME_WIND_DOWN": "baixar o volume e apagar a luz para a noite tardia",
        "LEARN_CONFIRM": str((payload or {}).get("descricao") or "confirmar um padrão percebido"),
        "LEARN_CONFLICT": "substituir a preferência anterior pela nova neste mesmo contexto",
    }.get(comando, comando)

    original_payload = payload

    def _feedback(aceito: bool | None, *, resultado: str = "") -> None:
        if callable(registrar_feedback):
            try:
                registrar_feedback(
                    categoria_sugestao(comando, original_payload),
                    aceito,
                    comando=comando,
                    payload=original_payload,
                    resultado=resultado,
                )
            except Exception:
                pass
    if comando == "EXPLAIN_ERROR" and re.search(
        r"\b(?:qual|que)\s+erro\b|\bo\s+que\s+(?:aconteceu|deu\s+errado)\b",
        str(texto or ""),
        flags=re.IGNORECASE,
    ):
        falar = _get(ctx, "falar")
        if callable(falar):
            falar(resumir_erro_navegador(original_payload, detalhado=True), "curiosa", 1)
            return True

    interpretar_contraproposta = _get(ctx, "interpretar_contraproposta")
    if parece_contraproposta(texto) and callable(interpretar_contraproposta):
        try:
            alternativa = interpretar_contraproposta(texto, comando, original_payload)
        except Exception:
            alternativa = None
        if isinstance(alternativa, dict):
            intent_alt = str(alternativa.get("intent") or "").strip().upper()
            if intent_alt in _INTENTS_CONTRAPROPOSTA_SEGURAS:
                _feedback(False, resultado="correcao")
                chave = chave_preferencia_sugestao(comando, original_payload)
                descricao_alt = descrever_intencao_alternativa(alternativa)
                pergunta_alt = verbalizar_pergunta_alternativa(alternativa)
                registro = {
                    "alternativa": alternativa,
                    "descricao": descricao_alt,
                    "fala_futura": f"Já que você prefere assim, quer que eu {pergunta_alt}?",
                    "evidencia": str(texto or "").strip(),
                }
                registrar_preferencia = _get(ctx, "registrar_preferencia_sugestao")
                resultado_aprendizado = None
                if callable(registrar_preferencia):
                    resultado_aprendizado = registrar_preferencia(chave, registro)
                if callable(resetar_sugestao):
                    resetar_sugestao()
                atualizar = _get(ctx, "continuidades_update")
                if isinstance(resultado_aprendizado, dict) and resultado_aprendizado.get("conflito"):
                    if callable(atualizar):
                        atualizar(
                            comando_sugerido="LEARN_CONFLICT",
                            comando_sugerido_payload=resultado_aprendizado,
                            comando_sugerido_estado="PENDING_CONFIRM",
                            comando_sugerido_ts=time.time(),
                            comando_pendente="LEARN_CONFLICT",
                            comando_pendente_payload=resultado_aprendizado,
                        )
                    falar = _get(ctx, "falar")
                    if callable(falar):
                        falar(
                            str(resultado_aprendizado.get("pergunta") or "Encontrei duas preferências diferentes. Quer substituir a anterior?"),
                            "curiosa", 1,
                        )
                    return True
                novo_payload = {
                    "intent": alternativa,
                    "descricao": descricao_alt,
                    "origem": "contraproposta_usuario",
                    "preferencia_origem_chave": chave,
                    "preferencia_hipotese_chave": str(
                        resultado_aprendizado.get("hipotese_chave") or ""
                    ) if isinstance(resultado_aprendizado, dict) else "",
                }
                if callable(atualizar):
                    atualizar(
                        comando_sugerido="EXECUTE_INTENT",
                        comando_sugerido_payload=novo_payload,
                        comando_sugerido_estado="PENDING_CONFIRM",
                        comando_sugerido_ts=time.time(),
                        comando_pendente="EXECUTE_INTENT",
                        comando_pendente_payload=novo_payload,
                    )
                falar = _get(ctx, "falar")
                if callable(falar):
                    falar(
                        f"Boa, essa alternativa faz mais sentido pra você. Vou lembrar disso. Quer que eu {pergunta_alt} agora?",
                        # A intenção continua estruturada; só esta camada cuida
                        # da conjugação natural da pergunta.
                        "carinhosa",
                        1,
                    )
                return True

    confirmado = classificar_local(texto) if callable(classificar_local) else None
    if confirmado is None and callable(interpretar_llm):
        confirmado = interpretar_llm(texto, descricao)
    if confirmado is None and "mas" in str(texto or "").lower():
        confirmado = True

    falar = _get(ctx, "falar")
    if confirmado is True:
        _feedback(True)
        sugestao = comando
        original_payload = payload if isinstance(payload, dict) else {}
        if callable(resetar_sugestao):
            resetar_sugestao()
        if "mas" in str(texto or "").lower() and isinstance(payload, dict):
            merge_intent = _get(ctx, "merge_intent_llm")
            if callable(merge_intent):
                payload = merge_intent(payload, texto)

        if sugestao == "SYS_MODE_CODE":
            executar = _get(ctx, "executar_modo_code")
            if callable(executar):
                executar(payload if isinstance(payload, dict) else {})
            oq = str(original_payload.get("music_query") or "lofi focus").strip().lower()
            nq = str((payload if isinstance(payload, dict) else {}).get("music_query") or oq).strip()
            fala = f"Beleza, ambiente pronto, mas troquei o Lo-fi pelo mestre {nq}. Boa escolha!" if nq and nq.lower() != oq else "Beleza, modo Code ligado. Eu limpei a bagunça e botei música pra tua cabeça funcionar."
            if callable(falar):
                falar(fala, "debochada", 2)
            return True

        if sugestao == "LEARN_CONFIRM":
            confirmar_hipotese = _get(ctx, "confirmar_hipotese_aprendizado")
            chave = str(original_payload.get("chave") or "").strip()
            if callable(confirmar_hipotese) and chave:
                confirmar_hipotese(chave, True)
            if callable(falar):
                falar("Fechado. Agora isso é uma preferência confirmada, não só um palpite meu.", "carinhosa", 1)
            return True

        if sugestao == "LEARN_CONFLICT":
            resolver_conflito = _get(ctx, "resolver_conflito_preferencia")
            resolvida = resolver_conflito(original_payload, True) if callable(resolver_conflito) else None
            if callable(falar):
                falar(
                    "Entendi. A nova preferência substitui a anterior somente nesse contexto."
                    if resolvida else "Entendi a troca, mas não consegui salvar a nova preferência agora.",
                    "carinhosa" if resolvida else "calma", 1,
                )
            return True

        if sugestao in {"TIME_LIGHT_ON", "TIME_WIND_DOWN"}:
            executar_temporal = _get(ctx, "executar_sugestao_temporal")
            if callable(executar_temporal):
                executar_temporal(sugestao, original_payload, texto)
            return True

        if sugestao in {"SYS_MODE_GAMER", "SYS_ORGANIZE_DOWNLOADS"}:
            executar = _get(ctx, "executar_modo_gamer" if sugestao == "SYS_MODE_GAMER" else "executar_organizacao")
            if callable(executar):
                executar(payload if isinstance(payload, dict) else {})
            fala = "Modo Gamer ativado. Agora fica mais fácil focar." if sugestao == "SYS_MODE_GAMER" else "Downloads na mira. Eu organizei o caos pra você não se perder."
            if callable(falar):
                falar(fala, "calma" if sugestao == "SYS_MODE_GAMER" else "debochada", 1 if sugestao == "SYS_MODE_GAMER" else 2)
            return True

        if sugestao == "EXPLAIN_ERROR":
            erro = str(original_payload.get("erro") or original_payload.get("linha") or "")
            messages = _get(ctx, "messages")
            if isinstance(messages, list):
                messages.append({"role": "user", "content": texto})
                mensagens_ia = list(messages)
            else:
                mensagens_ia = []
            mensagens_ia.extend([
                {"role": "user", "content": "Explique este erro/alerta do navegador de forma clara e curta, com um passo a passo do que fazer agora:\n" + erro},
                {"role": "system", "content": "Não use [EXEC]."},
            ])
            enviar = _get(ctx, "enviar_mensagem")
            limpar = _get(ctx, "limpar_resposta")
            remover = _get(ctx, "remover_prefixo_exec")
            bruto = enviar(mensagens_ia, _com_tools=False) if callable(enviar) else ""
            resposta = limpar(bruto) if callable(limpar) else str(bruto or "")
            resposta = remover(resposta) if callable(remover) else resposta
            if resposta:
                if isinstance(messages, list):
                    messages.append({"role": "assistant", "content": resposta})
                if callable(falar):
                    falar(resposta, _get(ctx, "current_emotion", "calma"), _get(ctx, "emotion_level", 1))
            return True

        if sugestao == "RELOAD_PAGE":
            alvo = str(original_payload.get("url") or "").strip()
            navegador = _get(ctx, "_registro_navegador_operacoes_runtime")
            if alvo and navegador is not None:
                navegador.recarregar_url(alvo)
            confirmar = _get(ctx, "confirmar_execucao_debochada")
            if callable(confirmar):
                confirmar(texto, "O usuário confirmou e o Python recarregou a página no Chrome. Responda curto, debochada, confirmando. Não use [EXEC].")
            return True

        if sugestao == "OPEN_SITE_ALT":
            executar_intencao = _get(ctx, "executar_intencao")
            return bool(executar_intencao({"intent": "OPEN_URL", "params": {"alvo": "https://www.cobasi.com.br"}}, texto)) if callable(executar_intencao) else False
        if sugestao == "EXECUTE_INTENT":
            executar_intencao = _get(ctx, "executar_intencao")
            intent_payload = original_payload.get("intent") if isinstance(original_payload, dict) else None
            if callable(executar_intencao) and isinstance(intent_payload, dict):
                return bool(executar_intencao(intent_payload, texto))
            return False
        return False

    if confirmado is False:
        _feedback(False)
        if comando == "LEARN_CONFLICT":
            resolver_conflito = _get(ctx, "resolver_conflito_preferencia")
            if callable(resolver_conflito):
                resolver_conflito(original_payload, False)
            if callable(resetar_sugestao):
                resetar_sugestao()
            if callable(falar):
                falar("Certo. Mantive a preferência anterior para esse contexto.", "calma", 1)
            return True
        if comando == "LEARN_CONFIRM":
            confirmar_hipotese = _get(ctx, "confirmar_hipotese_aprendizado")
            chave = str((payload or {}).get("chave") or "") if isinstance(payload, dict) else ""
            if callable(confirmar_hipotese) and chave:
                confirmar_hipotese(chave, False)
        chave_preferencia = str(
            original_payload.get("preferencia_hipotese_chave")
            or original_payload.get("preferencia_origem_chave") or ""
        ).strip()
        registrar_excecao = _get(ctx, "registrar_excecao_preferencia")
        if chave_preferencia and callable(registrar_excecao):
            registrar_excecao(chave_preferencia, texto)
        bloqueios = _get(ctx, "sugestao_bloqueada_ate")
        if isinstance(bloqueios, dict):
            bloqueios[comando] = time.time() + 600
        if callable(resetar_sugestao):
            resetar_sugestao()
        if callable(falar):
            falar("Tudo bem, deixei essa sugestão quieta.", "calma", 1)
        return True
    return False


class SugestoesSistemaRuntime:
    """Executa e confirma sugestões usando as integrações vivas da Laylay."""

    def __init__(
        self,
        *,
        contexto_getter: Callable[[], Dict[str, Any]],
        modelo_llm: Any = None,
    ) -> None:
        self.contexto_getter = contexto_getter
        self.enviar_mensagem = resolver_enviador_modelo(modelo_llm=modelo_llm)

    def _ctx(self) -> Dict[str, Any]:
        try:
            contexto = self.contexto_getter() if callable(self.contexto_getter) else {}
            contexto = contexto if isinstance(contexto, dict) else {}
            if self.enviar_mensagem is not None:
                contexto = dict(contexto)
                contexto["enviar_mensagem"] = self.enviar_mensagem
            return contexto
        except Exception:
            return {}

    def executar_modo_code(self, payload: Dict[str, Any]) -> bool:
        ctx = self._ctx()
        payload = dict(payload or {})
        if payload.get("clean_tabs") or payload.get("clean_empty_tabs"):
            navegador = _get(ctx, "_registro_navegador_operacoes_runtime")
            if navegador is not None:
                navegador.fechar_abas_vazias()

        topico = str(payload.get("image_topic") or "").strip()
        acao_imagem = str(payload.get("image_action") or "").strip().lower()
        pesquisa = _get(ctx, "pesquisa_contextual_runtime")
        if topico and pesquisa is not None:
            if acao_imagem == "download":
                pesquisa.baixar_imagem_direto(topico)
            else:
                url = pesquisa.buscar_imagem_url(topico)
                abrir_url = _get(ctx, "abrir_url_externo")
                if url and callable(abrir_url):
                    try:
                        abrir_url(url)
                    except Exception:
                        pass

        query = str(payload.get("music_query") or "lofi focus").strip()
        navegador = _get(ctx, "_registro_navegador_operacoes_runtime")
        if query and navegador is not None:
            navegador.pesquisar_youtube(query)
        return True

    def detectar_indireta(self, texto: str, estado_mental: Dict[str, Any] | None = None):
        local = detectar_sugestao_indireta(
            texto,
            estado_mental,
            normalizar_texto=_get(self._ctx(), "normalizar_texto"),
        )
        if local:
            return local
        return self._inferir_indireta_ia(texto, estado_mental)

    def _inferir_indireta_ia(self, texto: str, estado_mental: Dict[str, Any] | None = None):
        ctx = self._ctx()
        bruto = str(texto or "").strip()
        normalizar = _get(ctx, "normalizar_texto")
        t = normalizar(bruto) if callable(normalizar) else bruto.lower()
        if not t or "?" in bruto or len(t) > 180:
            return None
        tem_comando = _get(ctx, "texto_tem_comando_explicito")
        if callable(tem_comando) and tem_comando(t):
            return None
        if not re.search(
            r"\b(estou|to|tô|preciso|queria|gostaria|nao consigo|não consigo|ta dificil|tá difícil|me incomoda|me atrapalha)\b",
            t,
        ):
            return None
        if re.search(r"\b(estou|to|tô)\s+(bem|otimo|ótimo|feliz|de boa|tranquilo)\b", t):
            return None

        enviar = _get(ctx, "enviar_mensagem")
        extrair = _get(ctx, "extrair_json")
        if not callable(enviar):
            return None
        prompt = (
            "Você detecta necessidades indiretas para a Laylay. Não execute nada. "
            "Retorne NONE se não houver uma ação prática, clara e útil. Caso haja, retorne SOMENTE JSON: "
            '{"intent":"SUGGEST_ACTION","params":{"acao_sugerida":{"intent":"INTENT","params":{}},'
            '"descricao":"ação curta","fala":"pergunta natural?","origem":"inferencia_ia"}}. '
            "Intents permitidos: IOT_CONTROL, IOT_STATUS, IOT_LIST, APP_OPEN, OPEN_URL, MUSIC_SEARCH, "
            "PLAYLIST_PLAY, WEATHER, EMAIL_READ, VOLUME, MEDIA_CONTROL, ORGANIZAR_DESKTOP, RESUMIR_PAGINA. "
            "Não use DELETE_ITEM, CLOSE_APP, CLOSE_TAB, LOCK_PC ou ações destrutivas. "
            "Não force sugestão em elogio, opinião, bem-estar ou desabafo. "
            f"Contexto curto: {dict(estado_mental or {})}. Frase: {bruto}"
        )
        try:
            resposta = str(
                enviar(
                    [{"role": "system", "content": prompt}],
                    _com_tools=False,
                    max_tokens=180,
                    modo_rapido=True,
                )
                or ""
            ).strip()
            if not resposta or resposta.upper() == "NONE":
                return None
            json_texto = extrair(resposta) if callable(extrair) else resposta
            dados = json.loads(json_texto)
        except Exception:
            return None
        if str(dados.get("intent") or "").upper() != "SUGGEST_ACTION":
            return None
        params = dados.get("params") if isinstance(dados.get("params"), dict) else {}
        acao = params.get("acao_sugerida") if isinstance(params.get("acao_sugerida"), dict) else {}
        permitido = {
            "IOT_CONTROL", "IOT_STATUS", "IOT_LIST", "APP_OPEN", "OPEN_URL",
            "MUSIC_SEARCH", "PLAYLIST_PLAY", "WEATHER", "EMAIL_READ", "VOLUME",
            "MEDIA_CONTROL", "ORGANIZAR_DESKTOP", "RESUMIR_PAGINA",
        }
        if str(acao.get("intent") or "").upper() not in permitido:
            return None
        fala = str(params.get("fala") or "").strip()
        if not fala:
            return None
        params["fala"] = fala if fala.endswith("?") else fala + "?"
        params["origem"] = "inferencia_ia"
        dados["params"] = params
        return dados

    def registrar_indireta(self, resultado: Dict[str, Any], texto: str = "") -> bool:
        ctx = self._ctx()
        return registrar_sugestao_indireta(
            {
                "continuidades_update": _get(ctx, "continuidades_update"),
                "falar": _get(ctx, "falar"),
                "preferencia_sugestao_get": _get(ctx, "preferencia_sugestao_get"),
                "registrar_oportunidade": _get(ctx, "registrar_oportunidade"),
            },
            resultado,
        )

    def executar_modo_gamer(self, payload: Dict[str, Any]) -> bool:
        ctx = self._ctx()
        payload = dict(payload or {})
        navegador_operacoes = _get(ctx, "_registro_navegador_operacoes_runtime")
        navegador_leitura = _get(ctx, "_registro_navegador_leitura_runtime")
        if payload.get("pause_music") and navegador_operacoes is not None:
            navegador_operacoes.controlar_youtube("pause_play")
        if payload.get("close_study_tabs"):
            selecionar = _get(ctx, "selecionar_abas_para_fechar_llm")
            abas = navegador_leitura.listar_abas() if navegador_leitura is not None else []
            ids = selecionar("fechar abas de estudo", abas) if callable(selecionar) else []
            if ids and navegador_operacoes is not None:
                navegador_operacoes.fechar_abas(ids)
        return True

    def executar_organizacao(self, payload: Dict[str, Any]) -> bool:
        payload = dict(payload or {})
        if payload.get("open_downloads"):
            abrir_caminho = _get(self._ctx(), "abrir_caminho")
            if callable(abrir_caminho):
                try:
                    abrir_caminho(os.path.join(os.path.expanduser("~"), "Downloads"))
                except Exception:
                    pass
        return True

    def confirmar_execucao(self, texto_usuario: str, system_msg: str) -> bool:
        ctx = self._ctx()
        mensagens = _get(ctx, "messages", [])
        if not isinstance(mensagens, list):
            mensagens = []
        mensagens.append({"role": "user", "content": texto_usuario})
        confirma = list(mensagens)
        confirma.append({"role": "system", "content": system_msg})
        enviar = _get(ctx, "enviar_mensagem")
        limpar = _get(ctx, "limpar_resposta")
        remover = _get(ctx, "remover_prefixo_exec")
        bot_raw = enviar(confirma, _com_tools=False) if callable(enviar) else ""
        bot = limpar(bot_raw) if callable(limpar) else str(bot_raw or "")
        bot = remover(bot) if callable(remover) else bot
        if not bot:
            return False
        log = _get(ctx, "log", print)
        log(f"Laylay [debochada lvl2]: {bot}")
        mensagens.append({"role": "assistant", "content": bot})
        falar = _get(ctx, "falar")
        if callable(falar):
            falar(bot, "debochada", 2)
        memoria = _get(ctx, "memoria_inteligente")
        if memoria is not None and hasattr(memoria, "adicionar_interacao"):
            memoria.adicionar_interacao(texto_usuario, bot)
        salvar = _get(ctx, "salvar_memoria")
        if callable(salvar):
            salvar()
        return True

    def processar_confirmacao(self, texto: str) -> bool:
        ctx = self._ctx()
        contexto = {
            "continuidades_get": _get(ctx, "continuidades_get"),
            "resetar_sugestao": _get(ctx, "resetar_sugestao"),
            "classificar_confirmacao_local": _get(ctx, "classificar_confirmacao_local"),
            "interpretar_confirmacao_llm": _get(ctx, "interpretar_confirmacao_llm"),
            "merge_intent_llm": _get(ctx, "merge_intent_llm"),
            "executar_modo_code": self.executar_modo_code,
            "executar_modo_gamer": self.executar_modo_gamer,
            "executar_organizacao": self.executar_organizacao,
            "falar": _get(ctx, "falar"),
            "messages": _get(ctx, "messages", []),
            "enviar_mensagem": _get(ctx, "enviar_mensagem"),
            "limpar_resposta": _get(ctx, "limpar_resposta"),
            "remover_prefixo_exec": _get(ctx, "remover_prefixo_exec"),
            "current_emotion": _get(ctx, "current_emotion", "calma"),
            "emotion_level": _get(ctx, "emotion_level", 1),
            "_registro_navegador_leitura_runtime": _get(
                ctx, "_registro_navegador_leitura_runtime"
            ),
            "_registro_navegador_operacoes_runtime": _get(
                ctx, "_registro_navegador_operacoes_runtime"
            ),
            "confirmar_execucao_debochada": self.confirmar_execucao,
            "executar_intencao": _get(ctx, "executar_intencao"),
            "sugestao_bloqueada_ate": _get(ctx, "sugestao_bloqueada_ate"),
            "executar_sugestao_temporal": _get(ctx, "executar_sugestao_temporal"),
            "continuidades_update": _get(ctx, "continuidades_update"),
            "interpretar_contraproposta": _get(ctx, "interpretar_contraproposta"),
            "registrar_preferencia_sugestao": _get(ctx, "registrar_preferencia_sugestao"),
            "confirmar_hipotese_aprendizado": _get(ctx, "confirmar_hipotese_aprendizado"),
            "registrar_excecao_preferencia": _get(ctx, "registrar_excecao_preferencia"),
            "resolver_conflito_preferencia": _get(ctx, "resolver_conflito_preferencia"),
            "registrar_feedback_proatividade": _get(ctx, "registrar_feedback_proatividade"),
        }
        return processar_confirmacao_sugestao(contexto, texto)


def criar_sugestoes_sistema_runtime(**kwargs: Any) -> SugestoesSistemaRuntime:
    return SugestoesSistemaRuntime(**kwargs)
