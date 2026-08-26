"""Repara alvo e intenção imediata sem criar um segundo roteador."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict

from mente_laylay.arquivos.transacao_arquivos import caminho_criado_por_params


INTENTS_REPARAVEIS = {
    "APP_OPEN",
    "MAXIMIZE_WINDOW",
    "CLOSE_APP",
    "OPEN_URL",
    "CLOSE_TAB",
    "IOT_CONTROL",
    "IOT_STATUS",
    "PLAYLIST_PLAY",
    "PLAYLIST_ADD",
    "MUSIC_SEARCH",
    "SEARCH",
    "FILE_SEARCH",
    "MEDIA_CONTROL",
    "VOLUME",
    "AGENDAR_ACAO",
    "CREATE_FOLDER",
    "CREATE_FILE",
}


def _extrair_alvo_textual(texto: str) -> str:
    padroes = (
        r"\b(?:eu\s+)?(?:estava|tava|to|tô)\s+falando\s+(?:de|do|da|sobre)\s+(.+)$",
        r"\b(?:eu\s+)?(?:quis|quero)\s+dizer\s+(.+)$",
        r"\b(?:o alvo|o certo|era|e|é)\s+(?:o|a)?\s*(.+)$",
        r"^(?:(?:a|ah)\s+)?(?:nao|não)[,;:-]?\s+(?:lay\s*[,;:-]?\s*)?(?:o|a)?\s*(.+)$",
    )
    for padrao in padroes:
        achado = re.search(padrao, texto)
        if not achado:
            continue
        alvo = re.split(r"[,.!?]", achado.group(1), maxsplit=1)[0].strip(" -'")
        alvo = re.sub(
            r"\b(?:em\s+)?(?:tela\s+cheia|fullscreen|em\s+foco|pro\s+foco|para\s+frente)\b.*$",
            "",
            alvo,
        ).strip()
        alvo = re.sub(r"\b(?:abre|fecha|maximiza|minimiza|liga|desliga)\b.*$", "", alvo).strip()
        alvo = re.sub(r"\b(?:agora|na verdade)$", "", alvo).strip()
        if alvo and len(alvo.split()) <= 6:
            return alvo[:120]
    return ""


def _trecho_corretivo(texto: str) -> str:
    """Prioriza a última proposta da correção, descartando a ação rejeitada."""
    partes = re.split(
        r"\b(?:mas|era\s+para|queria|quis\s+dizer|na\s+verdade)\b|[,;]",
        str(texto or ""),
    )
    uteis = [parte.strip(" ,;:-") for parte in partes if parte.strip(" ,;:-")]
    return uteis[-1] if len(uteis) > 1 else str(texto or "").strip()


def _extrair_alvo_apos_acao(texto: str) -> str:
    padrao = (
        r"\b(?:abrir?|fecha(?:r)?|encerra(?:r)?|maximiza(?:r)?|"
        r"liga(?:r)?|desliga(?:r)?|pausa(?:r)?|despausa(?:r)?|retoma(?:r)?|"
        r"toca(?:r)?|repete|repetir|avanca(?:r)?|volta(?:r)?)\s+"
        r"(?:o|a|os|as)?\s*(.+)$"
    )
    achado = re.search(padrao, texto)
    if not achado:
        return ""
    alvo = re.split(r"[,.!?;]", achado.group(1), maxsplit=1)[0].strip(" -'")
    return alvo[:120] if alvo and len(alvo.split()) <= 6 else ""


def _intencao_corrigida(
    dominio: str,
    trecho: str,
    intent_anterior: str,
) -> tuple[str, str]:
    """Traduz apenas operações que já possuem executor confirmado."""
    if dominio == "app":
        if re.search(r"\b(?:fecha|fechar|encerra|encerrar|mata)\b", trecho):
            return "CLOSE_APP", "FECHAR"
        if re.search(r"\b(?:tela cheia|maximiza|maximizar|fullscreen)\b", trecho):
            return "MAXIMIZE_WINDOW", "MAXIMIZAR"
        if re.search(r"\b(?:abre|abrir|foco|frente)\b", trecho):
            return "APP_OPEN", "ABRIR"
    elif dominio == "site":
        if re.search(r"\b(?:fecha|fechar|encerra|encerrar)\b", trecho):
            return "CLOSE_TAB", "FECHAR"
        if re.search(r"\b(?:abre|abrir|entra|entrar|acessa|acessar)\b", trecho):
            return "OPEN_URL", "ABRIR"
    elif dominio == "iot":
        if re.search(r"\b(?:desliga|desligar)\b", trecho):
            return "IOT_CONTROL", "DESLIGAR"
        if re.search(r"\b(?:liga|ligar)\b", trecho):
            return "IOT_CONTROL", "LIGAR"
        if re.search(r"\b(?:estado|status)\b", trecho):
            return "IOT_STATUS", "STATUS"
    elif dominio == "musica":
        if re.search(r"\b(?:despausa|despausar|retoma|retomar|continua|continuar)\b", trecho):
            return "MEDIA_CONTROL", "RETOMAR"
        if re.search(r"\b(?:pausa|pausar)\b", trecho):
            return "MEDIA_CONTROL", "PAUSAR"
        if re.search(r"\b(?:proxima|próxima|avanca|avançar|pula)\b", trecho):
            return "MEDIA_CONTROL", "AVANCAR"
        if re.search(r"\b(?:anterior|volta|retrocede)\b", trecho):
            return "MEDIA_CONTROL", "RETROCEDER"
        if re.search(r"\b(?:repete|repetir|toca de novo)\b", trecho):
            return "MEDIA_CONTROL", "EXECUTAR"
    elif dominio == "volume" and re.search(r"\b(?:volume|coloca|define|ajusta)\b", trecho):
        return "VOLUME", "AJUSTAR"
    elif dominio == "agenda":
        return "AGENDAR_ACAO", "REAGENDAR"
    return intent_anterior, ""


def _dominio_da_intencao(intent: str) -> str:
    intent = str(intent or "").upper().strip()
    if intent in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        return "app"
    if intent in {"OPEN_URL", "CLOSE_TAB"}:
        return "site"
    if intent in {"IOT_CONTROL", "IOT_STATUS"}:
        return "iot"
    if intent in {"PLAYLIST_PLAY", "PLAYLIST_ADD", "MEDIA_CONTROL", "MUSIC_SEARCH"}:
        return "musica"
    if intent in {"SEARCH", "FILE_SEARCH"}:
        return "pesquisa"
    if intent == "VOLUME":
        return "volume"
    if intent == "AGENDAR_ACAO":
        return "agenda"
    if intent in {"CREATE_FOLDER", "CREATE_FILE"}:
        return "arquivo"
    return ""


def _consulta_corrigida(query_anterior: str, trecho: str, alvo_extraido: str) -> str:
    """Combina uma qualificação natural com a consulta anterior.

    ``não, é do Henrique Mendonça`` especifica a busca anterior; não pode
    substituir o título por apenas ``Henrique Mendonça``. O mesmo mecanismo é
    compartilhado por música, busca web e pesquisa de arquivos.
    """
    anterior = re.sub(r"\s+", " ", str(query_anterior or "")).strip(" .,!?:;-")
    bruto = re.sub(r"\s+", " ", str(trecho or "")).strip(" .,!?:;-")
    qualificacao = re.search(
        r"\b(?:[ée]\s+)?(?:do|da|de|com|vers[aã]o\s+do|vers[aã]o\s+da)\s+(.+)$",
        bruto,
        re.I,
    )
    if qualificacao and anterior:
        detalhe = qualificacao.group(1).strip(" .,!?:;-")
        if detalhe and detalhe.casefold() not in anterior.casefold():
            return f"{anterior} {detalhe}"[:220]
    novo = re.sub(r"^(?:[ée]\s+)?(?:do|da|de)\s+", "", str(alvo_extraido or bruto), flags=re.I)
    return re.sub(r"\s+", " ", novo).strip(" .,!?:;-")[:220]


def _extrair_nivel_volume(trecho: str) -> int | None:
    numeros = re.findall(r"\b(100|[1-9]?\d)\b", trecho)
    return int(numeros[-1]) if numeros else None


def _extrair_atraso_segundos(trecho: str) -> int | None:
    achados = re.findall(
        r"\b(\d{1,4})\s*(segundo|segundos|seg|minuto|minutos|min|hora|horas)\b",
        trecho,
    )
    if not achados:
        return None
    valor_bruto, unidade = achados[-1]
    valor = int(valor_bruto)
    if unidade.startswith("hora"):
        return valor * 3600
    if unidade.startswith("min"):
        return valor * 60
    return valor


def _montar_transacao_arquivo(
    intent_anterior: str,
    params_anteriores: Dict[str, Any],
    trecho: str,
) -> tuple[Dict[str, Any] | None, str]:
    origem = caminho_criado_por_params(intent_anterior, params_anteriores)
    if not origem:
        return None, ""
    destinos = re.findall(
        r"\b(?:em|no|na|para|pro|pra)\s+(?:o|a)?\s*"
        r"(downloads|desktop|area de trabalho|área de trabalho|documentos)\b",
        trecho,
    )
    if destinos:
        destino = destinos[-1]
        return {
            "intent": "FILE_TRANSACTION",
            "params": {"operacao": "mover", "origem": origem, "destino": destino},
        }, f"destino {destino}"

    nomes = re.findall(
        r"\b(?:chama|chamar|renomeia|renomear|nome(?:\s+certo)?\s+(?:e|é))\s+"
        r"(?:de\s+)?(?:o|a)?\s*([^,!?;]+)$",
        trecho,
    )
    if nomes:
        novo_nome = nomes[-1].strip(" '\"")
        return {
            "intent": "FILE_TRANSACTION",
            "params": {"operacao": "renomear", "origem": origem, "novo_nome": novo_nome},
        }, f"nome {novo_nome}"

    conteudos = re.findall(
        r"\b(?:escreve|escrever|conteudo|conteúdo)\s+(?:e|é)?\s*([^;]+)$",
        trecho,
    )
    if conteudos and str(intent_anterior).upper() == "CREATE_FILE":
        conteudo = conteudos[-1].strip(" '\"")
        return {
            "intent": "FILE_TRANSACTION",
            "params": {"operacao": "editar_conteudo", "origem": origem, "conteudo": conteudo},
        }, "conteúdo do arquivo"
    return None, ""


def registrar_correcao_alvo(
    estado_mental: Dict[str, Any] | None,
    reparacao: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Guarda o ensino de alvo sem torná-lo preferência permanente."""
    estado = dict(estado_mental or {})
    dados = dict(reparacao or {})
    if dados.get("tipo") != "operacional":
        return estado
    anterior = str(dados.get("alvo_anterior") or "").strip()
    novo = str(dados.get("alvo_novo") or "").strip()
    dominio = str(dados.get("dominio") or "").strip().lower()
    params_anteriores = dict(dados.get("parametros_anteriores") or {})
    intencao = dados.get("intencao") if isinstance(dados.get("intencao"), dict) else {}
    params_novos = dict(intencao.get("params") or {})
    mudou_alvo = bool(anterior and novo and anterior.casefold() != novo.casefold())
    mudou_parametros = bool(params_anteriores != params_novos)
    if not dominio or (not mudou_alvo and not mudou_parametros):
        return estado
    aprendizado = dict(estado.get("aprendizado_continuidade") or {})
    alvos = dict(aprendizado.get("correcoes_alvo") or {})
    if mudou_alvo:
        chave = f"{dominio}:{anterior.casefold()}>{novo.casefold()}"
        alvos[chave] = min(10, int(alvos.get(chave) or 0) + 1)
    parametros = dict(aprendizado.get("correcoes_parametros") or {})
    if mudou_parametros:
        chave_parametro = f"{dominio}:{str(intencao.get('intent') or '').upper()}"
        parametros[chave_parametro] = min(10, int(parametros.get(chave_parametro) or 0) + 1)
    historico = list(aprendizado.get("correcoes") or [])
    historico.append({
        "ts": time.time(),
        "tipo": "alvo_parametro" if mudou_alvo and mudou_parametros else ("alvo" if mudou_alvo else "parametro"),
        "dominio": dominio,
        "alvo_escolhido": anterior,
        "alvo_correto": novo,
        "intent_correto": str(intencao.get("intent") or ""),
    })
    aprendizado["correcoes_alvo"] = alvos
    aprendizado["correcoes_parametros"] = parametros
    aprendizado["correcoes"] = historico[-30:]
    aprendizado["ultima_correcao_ts"] = historico[-1]["ts"]
    estado["aprendizado_continuidade"] = aprendizado
    return estado


def detectar_reparacao_conversacional(
    texto: str,
    estado_mental: Dict[str, Any] | None,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    extrair_app_explicito: Callable[[str], str] | None = None,
    ttl_s: float = 180.0,
) -> Dict[str, Any] | None:
    bruto = str(texto or "").strip()
    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.casefold()
    t = re.sub(r"\s+", " ", str(t or "")).strip()
    if not t:
        return None
    sinais = (
        r"^(?:nao|não)\s+lay\b",
        r"^(?:nao|não)[,;:-]\s+",
        r"^(?:nao|não)\s+era\s+para\b",
        r"^(?:nao|não)\b.+[,;]\s*.+$",
        r"^(?:a|ah)\s+(?:nao|não)\s+lay\b",
        r"\b(?:eu\s+)?(?:quis|quero)\s+dizer\b",
        r"\b(?:eu\s+)?(?:estava|tava|to|tô)\s+falando\s+(?:de|do|da|sobre)\b",
        r"\bna verdade\b",
    )
    if not any(re.search(padrao, t) for padrao in sinais):
        return None

    estado = dict(estado_mental or {})
    try:
        recente = time.time() - float(estado.get("ts") or 0.0) <= ttl_s
    except Exception:
        recente = False

    trecho_correto = _trecho_corretivo(t)
    intent_anterior = str(
        estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or ""
    ).upper().strip()
    dominio = _dominio_da_intencao(intent_anterior)
    params_anteriores = dict(estado.get("ultima_acao_params") or {})
    alvo_app = ""
    if callable(extrair_app_explicito):
        try:
            alvo_app = str(extrair_app_explicito(trecho_correto) or "").strip()
        except Exception:
            alvo_app = ""
    alvo_novo = (
        alvo_app
        or _extrair_alvo_apos_acao(trecho_correto)
        or _extrair_alvo_textual(trecho_correto)
        or _extrair_alvo_textual(t)
    )
    correcao_so_parametro = bool(
        (dominio == "volume" and _extrair_nivel_volume(trecho_correto) is not None)
        or (dominio == "agenda" and _extrair_atraso_segundos(trecho_correto) is not None)
        or (
            dominio == "arquivo"
            and re.search(
                r"\b(?:downloads|desktop|area de trabalho|área de trabalho|"
                r"chama|chamar|renomeia|renomear|nome|escreve|escrever|conteudo|conteúdo)\b",
                trecho_correto,
            )
        )
    )
    if not alvo_novo and not correcao_so_parametro:
        correcao_direta = bool(
            re.search(r"^(?:(?:a|ah)\s+)?(?:nao|não)\s+lay\b", t)
            or re.search(r"\b(?:quis|quero)\s+dizer\b", t)
            or re.search(r"\b(?:estava|tava|to|tô)\s+falando\b", t)
        )
        if not correcao_direta:
            return None
        return {"tipo": "conversacional", "alvo_novo": "", "texto": bruto}

    alvo_anterior = str(
        params_anteriores.get("nome_app")
        or params_anteriores.get("alvo")
        or params_anteriores.get("nome_playlist")
        or estado.get("ultimo_alvo")
        or ""
    ).strip()

    if not recente or intent_anterior not in INTENTS_REPARAVEIS:
        return {
            "tipo": "conversacional",
            "alvo_anterior": alvo_anterior,
            "alvo_novo": alvo_novo,
            "texto": bruto,
        }

    if dominio == "arquivo":
        transacao, resumo = _montar_transacao_arquivo(
            intent_anterior,
            params_anteriores,
            trecho_correto,
        )
        if transacao:
            return {
                "tipo": "operacional",
                "alvo_anterior": alvo_anterior or str(transacao["params"].get("origem") or ""),
                "alvo_novo": resumo,
                "dominio": "arquivo",
                "operacao_corrigida": str(transacao["params"].get("operacao") or "").upper(),
                "parametros_anteriores": params_anteriores,
                "resumo_correcao": resumo,
                "intencao": transacao,
                "texto": bruto,
            }

    # Assuntos livres nunca viram apps apenas porque a última ação mexeu numa
    # janela. Para esse domínio exigimos um aplicativo reconhecido pelo extrator.
    comando_janela_explicito = bool(re.search(
        r"\b(?:abre|abrir|fecha|fechar|foco|frente|tela cheia|maximiza|maximizar|minimiza|minimizar|fullscreen)\b",
        t,
    ))
    if (
        intent_anterior in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}
        and not alvo_app
        and not comando_janela_explicito
    ):
        return {
            "tipo": "conversacional",
            "alvo_anterior": alvo_anterior,
            "alvo_novo": alvo_novo,
            "texto": bruto,
        }

    params = dict(params_anteriores)
    intent_corrigido, operacao_corrigida = _intencao_corrigida(
        dominio,
        trecho_correto,
        intent_anterior,
    )
    operacao_nao_suportada = bool(
        not operacao_corrigida
        and re.search(r"\b(?:minimiza|minimizar|move|mover|renomeia|renomear)\b", trecho_correto)
    )
    if dominio == "arquivo" and correcao_so_parametro:
        operacao_nao_suportada = True
    if operacao_nao_suportada:
        return {
            "tipo": "nao_suportada",
            "alvo_anterior": alvo_anterior,
            "alvo_novo": alvo_novo,
            "dominio": dominio,
            "operacao_solicitada": trecho_correto,
            "texto": bruto,
        }
    intent_anterior = intent_corrigido
    if intent_anterior in {"MUSIC_SEARCH", "SEARCH", "FILE_SEARCH"}:
        consulta_anterior = str(params.get("query") or params.get("alvo") or "").strip()
        consulta_corrigida = _consulta_corrigida(consulta_anterior, trecho_correto, alvo_novo)
        if not consulta_corrigida:
            return None
        params["query"] = consulta_corrigida
        params.pop("alvo", None)
        alvo_novo = consulta_corrigida
        resumo_correcao = consulta_corrigida
    elif intent_anterior in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        params["nome_app"] = alvo_novo
        params.pop("app", None)
    elif intent_anterior in {"OPEN_URL", "CLOSE_TAB"}:
        params["alvo"] = alvo_novo
        params.pop("url", None)
        params.pop("site", None)
    elif intent_anterior in {"PLAYLIST_PLAY", "PLAYLIST_ADD"}:
        params["nome_playlist"] = alvo_novo
    elif intent_anterior in {"IOT_CONTROL", "IOT_STATUS"}:
        params["alvo"] = alvo_novo
        if operacao_corrigida in {"LIGAR", "DESLIGAR"}:
            params["acao"] = operacao_corrigida.casefold()
    elif intent_anterior == "MEDIA_CONTROL":
        comandos_midia = {
            "PAUSAR": "pause", "RETOMAR": "play", "AVANCAR": "next",
            "RETROCEDER": "prev", "EXECUTAR": "replay",
        }
        if operacao_corrigida in comandos_midia:
            params["acao"] = comandos_midia[operacao_corrigida]
            params["platform"] = "music"
        params["alvo"] = alvo_novo
    elif intent_anterior == "VOLUME":
        nivel = _extrair_nivel_volume(trecho_correto)
        if nivel is None:
            return None
        params = {"acao": "set", "nivel_volume": nivel, "referencia_contextual": True}
        resumo_correcao = f"volume {nivel}"
    elif intent_anterior == "AGENDAR_ACAO":
        atraso = _extrair_atraso_segundos(trecho_correto)
        if atraso is None or not isinstance(params.get("acao_agendada"), dict):
            return None
        for chave_tempo in ("segundos", "minutos", "horas", "hora_alvo"):
            params.pop(chave_tempo, None)
        params["atraso_segundos"] = atraso
        params["substituir_agendamento_anterior"] = True
        resumo_correcao = f"prazo de {atraso // 60} minuto(s)" if atraso % 60 == 0 else f"prazo de {atraso} segundo(s)"
    else:
        resumo_correcao = alvo_novo

    return {
        "tipo": "operacional",
        "alvo_anterior": alvo_anterior,
        "alvo_novo": alvo_novo,
        "dominio": dominio,
        "operacao_corrigida": operacao_corrigida,
        "parametros_anteriores": params_anteriores,
        "resumo_correcao": locals().get("resumo_correcao", alvo_novo),
        "intencao": {"intent": intent_anterior, "params": params},
        "texto": bruto,
    }
