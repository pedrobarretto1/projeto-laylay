"""Continuidade canônica da mente, compartilhada por todos os domínios.

Este módulo não executa ações. Ele mantém um único contrato de continuidade
com trilhas por domínio para que música, IoT, arquivos, jogo e conversa não
disputem campos paralelos nem contaminem uns aos outros.
"""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Dict


VERSAO_CONTINUIDADE_GERAL = 1


def estado_continuidade_geral_inicial() -> Dict[str, Any]:
    return {
        "versao": VERSAO_CONTINUIDADE_GERAL,
        "modo": "oficial",
        "fonte_autoritativa": True,
        "dominio_ativo": "",
        "dominios": {},
        "historico": [],
        "ts": 0.0,
    }


_INTENTS_DOMINIO = {
    "APP_OPEN": "app", "CLOSE_APP": "app", "MAXIMIZE_WINDOW": "app",
    "ORGANIZAR_DESKTOP": "app",
    "OPEN_URL": "site", "CLOSE_TAB": "site", "SITE_ENTER": "site", "SEARCH": "site",
    "MUSIC_SEARCH": "musica", "MEDIA_CONTROL": "musica", "PLAYLIST_PLAY": "musica",
    "PLAYLIST_CREATE": "musica", "PLAYLIST_ADD": "musica", "PLAYLIST_LIST": "musica", "TOCAR_PLAYLIST": "musica",
    "PLAYLIST_MOVE": "musica",
    "TOCAR_PLAYLIST_SHUFFLE": "musica",
    "LAYLAY_PLAYLIST_LIST": "playlist_laylay",
    "LAYLAY_PLAYLIST_PLAY": "playlist_laylay",
    "LAYLAY_PLAYLIST_COPY": "playlist_laylay",
    "IOT_CONTROL": "iot", "IOT_STATUS": "iot", "IOT_LIST": "iot",
    "CREATE_FOLDER": "arquivos", "CREATE_FILE": "arquivos", "MOVE_ITEM": "arquivos",
    "DELETE_ITEM": "arquivos", "CONFIRM_DELETE_ITEM": "arquivos", "CANCEL_DELETE_ITEM": "arquivos",
    "FILE_SEARCH": "arquivos", "FILE_OPEN_RESULT": "arquivos", "FILE_TRANSACTION": "arquivos",
    "AGENDAR_LEMBRETE": "agenda", "AGENDAR_ACAO": "agenda", "LISTAR_AGENDAMENTOS": "agenda",
    "CANCELAR_AGENDAMENTO": "agenda",
    "LEARNING_QUERY": "memoria",
    "PEOPLE_REMEMBER": "pessoas", "PEOPLE_QUERY": "pessoas",
    "PEOPLE_LIST": "pessoas", "PEOPLE_FORGET": "pessoas",
    "GAME_VISION": "jogo", "GAME_VISION_CONTINUE": "jogo",
    "EMAIL_READ": "email", "EMAIL_SYNC": "email", "NOTIFICATIONS": "email",
    "VOLUME": "sistema", "WEATHER": "clima",
    "INBOX_ADD": "caixa_entrada", "INBOX_ADD_DISCUSSION": "caixa_entrada",
    "INBOX_LIST": "caixa_entrada",
    "INBOX_CONVERT_REMINDER": "caixa_entrada", "INBOX_DELETE": "caixa_entrada",
    "CONFIRM_INBOX_DELETE": "caixa_entrada",
    "CANCEL_INBOX_ACTION": "caixa_entrada",
    "COOPERATIVE_PLAN": "cooperacao",
}

_TIPOS_DOMINIO = {
    "janela": "app", "app": "app", "site": "site", "navegador": "site",
    "musica": "musica", "música": "musica", "playlist": "musica", "midia": "musica",
    "playlist_laylay": "playlist_laylay", "curadoria_laylay": "playlist_laylay",
    "iot": "iot", "arquivo": "arquivos", "arquivos": "arquivos",
    "agenda": "agenda", "jogo": "jogo", "visao_jogo": "jogo", "visão_jogo": "jogo",
    "email": "email", "clima": "clima", "conversa": "conversa",
    "caixa_entrada": "caixa_entrada", "nota": "caixa_entrada", "anotacao": "caixa_entrada",
    "conversacional": "conversa", "opiniao": "conversa", "opinião": "conversa",
    "cooperacao": "cooperacao", "cooperação": "cooperacao",
    "memoria": "memoria", "memória": "memoria", "aprendizado": "memoria",
    "pessoa": "pessoas", "pessoas": "pessoas", "memoria_pessoas": "pessoas",
}


# Uma continuação aditiva mantém a operação e o destino anteriores, mas usa o
# objeto implícito que está atual agora. Isso é diferente de "tenta de novo",
# que repete exatamente a ação anterior. A política fica centralizada para que
# novas habilidades possam aderir sem criar listas privadas de pronomes.
# Somente operações cujo novo objeto pode ser obtido com segurança entram aqui.
_POLITICAS_CONTINUACAO_ADITIVA = {
    "PLAYLIST_ADD": {
        "preservar_params": ("nome_playlist", "playlist"),
        "exige_um_dos_params": ("nome_playlist", "playlist"),
    },
}

_PADRAO_CONTINUACAO_ADITIVA = re.compile(
    r"^(?:e\s+)?(?:"
    r"(?:essa|esta|esse|este|isso|ela|ele)(?:\s+(?:aqui|ai))?\s+tambem"
    r"|tambem\s+(?:essa|esta|esse|este|isso|ela|ele)"
    r"|mais\s+(?:essa|esta|esse|este)"
    r")$",
    flags=re.IGNORECASE,
)


def _normalizar_fala_continuidade(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    sem_acentos = "".join(c for c in base if not unicodedata.combining(c))
    sem_pontuacao = re.sub(r"[^a-z0-9\s]", " ", sem_acentos)
    return re.sub(r"\s+", " ", sem_pontuacao).strip()


def texto_e_continuacao_aditiva(texto: str) -> bool:
    """Indica uma elipse curta como ``essa também`` ou ``mais essa``."""
    return bool(_PADRAO_CONTINUACAO_ADITIVA.fullmatch(
        _normalizar_fala_continuidade(texto)
    ))


def resolver_continuacao_aditiva(
    estado_atual: Dict[str, Any] | None,
    *,
    texto: str,
    ttl_s: float = 300.0,
) -> Dict[str, Any]:
    """Materializa uma continuação segura a partir da fonte oficial.

    O registro elegível mais recente vence, mesmo que uma percepção de outro
    domínio tenha virado o foco ativo depois. Falhas, ações aguardando
    confirmação e operações sem política explícita nunca são repetidas.
    """
    if not texto_e_continuacao_aditiva(texto):
        return {}

    continuidade = dict((estado_atual or {}).get("continuidade_geral") or {})
    dominios = dict(continuidade.get("dominios") or {})
    agora = time.time()
    candidatos: list[Dict[str, Any]] = []
    for dominio, bruto in dominios.items():
        item = dict(bruto or {})
        intent = str(item.get("intent") or "").upper().strip()
        # Uma elipse aditiva só pode herdar operações que declararam uma
        # política própria. Filtrar aqui é importante: uma percepção ou ação
        # mais nova de outro domínio não deve esconder o último PLAYLIST_ADD
        # válido e transformar "essa também" em conversa livre.
        if intent not in _POLITICAS_CONTINUACAO_ADITIVA or not item.get("ativa", True):
            continue
        try:
            idade = agora - float(item.get("ts") or 0.0)
            expira_em = float(item.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            continue
        if idade > ttl_s or (expira_em and agora >= expira_em):
            continue
        candidatos.append({**item, "dominio": dominio, "idade_s": max(0.0, idade)})

    if not candidatos:
        return {}
    selecionado = max(candidatos, key=lambda item: float(item.get("ts") or 0.0))
    intent = str(selecionado.get("intent") or "").upper().strip()
    politica = _POLITICAS_CONTINUACAO_ADITIVA[intent]
    status = str(selecionado.get("status") or "").casefold().strip()
    if not status or any(marcador in status for marcador in (
        "falha", "erro", "indispon", "nao_encontr", "não_encontr",
        "aguardando", "pendente", "cancel", "recus",
    )):
        return {}
    anteriores = dict(selecionado.get("params") or {})
    exigidos = tuple(politica.get("exige_um_dos_params") or ())
    if exigidos and not any(
        str(anteriores.get(chave) or "").strip() for chave in exigidos
    ):
        return {}
    params = {
        chave: anteriores[chave]
        for chave in tuple(politica.get("preservar_params") or ())
        if chave in anteriores and str(anteriores.get(chave) or "").strip()
    }
    params["referencia_contextual"] = True
    return {"intent": intent, "params": params}


def normalizar_dominio_continuidade(
    dominio: str = "", *, intent: str = "", habilidade: str = "", tipo: str = ""
) -> str:
    intent_norm = str(intent or "").strip().upper()
    if intent_norm in _INTENTS_DOMINIO:
        return _INTENTS_DOMINIO[intent_norm]
    for candidato in (dominio, habilidade, tipo):
        chave = str(candidato or "").strip().casefold()
        if chave in _TIPOS_DOMINIO:
            return _TIPOS_DOMINIO[chave]
        if chave:
            return chave[:40]
    return "conversa"


def _texto_seguro(valor: Any, limite: int = 240) -> str:
    texto = str(valor or "").replace("\x00", " ").strip()
    return re.sub(r"\s+", " ", texto)[:limite]


def _params_seguros(params: Dict[str, Any] | None) -> Dict[str, Any]:
    permitidos = {
        "acao", "alvo", "nome", "nome_app", "nome_playlist", "playlist", "query", "url",
        "dispositivo", "ambiente", "tipo", "tipo_arquivo", "pasta", "nome_arquivo",
        "item", "platform", "modo", "nivel_volume", "cor", "rgb", "temperatura", "brilho",
        "jogo", "pergunta", "nota_id", "tipo_nota", "filtro", "caminho", "indice",
        "forcar_indice", "somente_projeto", "referencia_caminho",
        "operacao", "origem", "destino", "novo_nome",
        "left", "right", "esquerda", "direita", "layout",
        # Referências opacas da cooperação podem ser repetidas enquanto vivem
        # em RAM. O conteúdo bruto nunca entra neste contrato.
        "conteudo_ref", "conteudo_hash", "sobrescrever_confirmado",
        "plano_cooperativo_id",
        "limit", "offset", "consulta",
    }
    seguro: Dict[str, Any] = {}
    for chave, valor in dict(params or {}).items():
        if chave not in permitidos or isinstance(valor, (dict, set)):
            continue
        if isinstance(valor, (list, tuple)):
            itens: list[Any] = []
            for item in list(valor)[:8]:
                if isinstance(item, (bool, int, float)):
                    itens.append(item)
                elif isinstance(item, str):
                    itens.append(_texto_seguro(item, 80))
            seguro[chave] = tuple(itens) if isinstance(valor, tuple) else itens
            continue
        limite_texto = 1000 if chave == "url" else 160
        seguro[chave] = (
            valor
            if isinstance(valor, (bool, int, float))
            else _texto_seguro(valor, limite_texto)
        )
    return seguro


def registrar_evento_continuidade(
    estado_atual: Dict[str, Any] | None,
    *,
    evento: str,
    dominio: str = "",
    intent: str = "",
    habilidade: str = "",
    tipo: str = "",
    alvo: str = "",
    topico: str = "",
    texto: str = "",
    resposta: str = "",
    params: Dict[str, Any] | None = None,
    status: str = "",
    origem: str = "",
    ttl_s: float = 900.0,
    ativa: bool = True,
    reexecutavel: bool | None = None,
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    continuidade = dict(estado.get("continuidade_geral") or estado_continuidade_geral_inicial())
    dominios = dict(continuidade.get("dominios") or {})
    dominio_norm = normalizar_dominio_continuidade(
        dominio, intent=intent, habilidade=habilidade, tipo=tipo
    )
    agora = time.time()
    registro = dict(dominios.get(dominio_norm) or {})
    try:
        registro_ainda_ativo = agora < float(registro.get("expira_em") or 0.0)
    except (TypeError, ValueError):
        registro_ainda_ativo = False
    if (
        registro_ainda_ativo
        and registro.get("ativa", True)
        and str(registro.get("evento") or "") == "pendencia"
        and str(registro.get("origem") or "") == "esclarecimento_operacional"
        and str(evento or "") == "foco"
    ):
        return estado
    item = {
        "evento": _texto_seguro(evento, 40),
        "dominio": dominio_norm,
        "intent": _texto_seguro(intent, 80).upper(),
        "habilidade": _texto_seguro(habilidade, 60),
        "tipo": _texto_seguro(tipo, 60),
        "alvo": _texto_seguro(alvo, 180),
        "topico": _texto_seguro(topico, 180),
        "texto": _texto_seguro(texto),
        "resposta": _texto_seguro(resposta),
        "params": _params_seguros(params),
        "status": _texto_seguro(status, 60),
        "origem": _texto_seguro(origem, 60),
        "ativa": bool(ativa),
        "reexecutavel": reexecutavel,
        "ts": agora,
        "expira_em": agora + max(1.0, float(ttl_s or 900.0)),
    }
    intent_mudou = bool(
        item.get("intent")
        and registro.get("intent")
        and item.get("intent") != registro.get("intent")
    )
    # Só o mesmo contrato pode completar seus próprios campos. Quando a
    # intenção muda, um vazio pertence ao evento novo e não herda entidade,
    # status ou parâmetros do evento anterior no mesmo domínio.
    if not intent_mudou:
        for chave in ("intent", "habilidade", "tipo", "alvo", "topico", "texto", "resposta", "status", "origem"):
            if not item[chave] and registro.get(chave):
                item[chave] = registro[chave]
        if not item["params"] and isinstance(registro.get("params"), dict):
            item["params"] = dict(registro["params"])
    if item["reexecutavel"] is None:
        item["reexecutavel"] = False if intent_mudou else bool(registro.get("reexecutavel", False))
    dominios[dominio_norm] = item
    historico = list(continuidade.get("historico") or [])
    historico.append({chave: item.get(chave) for chave in ("evento", "dominio", "intent", "alvo", "status", "ts")})
    continuidade.update({
        "versao": VERSAO_CONTINUIDADE_GERAL,
        "modo": "oficial",
        "fonte_autoritativa": True,
        "dominio_ativo": dominio_norm if ativa else str(continuidade.get("dominio_ativo") or ""),
        "dominios": dominios,
        "historico": historico[-24:],
        "ts": agora,
    })
    estado["continuidade_geral"] = continuidade
    estado["ts"] = agora
    return estado


def encerrar_continuidade(
    estado_atual: Dict[str, Any] | None, *, dominio: str = "", motivo: str = "resolvida"
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    continuidade = dict(estado.get("continuidade_geral") or {})
    dominios = dict(continuidade.get("dominios") or {})
    chave = normalizar_dominio_continuidade(dominio or continuidade.get("dominio_ativo") or "conversa")
    registro = dict(dominios.get(chave) or {})
    if registro:
        registro.update({"ativa": False, "status": _texto_seguro(motivo, 60), "ts": time.time()})
        dominios[chave] = registro
    continuidade["dominios"] = dominios
    if continuidade.get("dominio_ativo") == chave:
        continuidade["dominio_ativo"] = ""
    continuidade["ts"] = time.time()
    estado["continuidade_geral"] = continuidade
    return estado


def _dominio_pedido_no_texto(texto: str) -> str:
    base = str(texto or "").casefold()
    regras = (
        ("musica", r"\b(m[uú]sica|faixa|playlist|pausa|despausa|toca|replay)\b"),
        ("iot", r"\b(luz|l[aâ]mpada|tomada|ventilador|dispositivo)\b"),
        ("arquivos", r"\b(arquivo|pasta|diret[oó]rio|extens[aã]o|formato|markdown)\b|\.(?:txt|md)\b"),
        ("agenda", r"\b(agenda|lembrete|agendamento|compromisso)\b"),
        ("jogo", r"\b(jogo|item|invent[aá]rio|build|atributo|equipamento)\b"),
        ("email", r"\b(e-?mail|caixa de entrada)\b"),
        ("site", r"\b(site|p[aá]gina|aba|guia|navegador)\b"),
        ("app", r"\b(app|programa|janela|aplicativo)\b"),
        ("caixa_entrada", r"\b(nota|anotacao|anotação|caixa de entrada|ideia anotada)\b"),
    )
    for dominio, padrao in regras:
        if re.search(padrao, base):
            return dominio
    return ""


def selecionar_continuidade(
    estado_atual: Dict[str, Any] | None,
    *,
    texto: str = "",
    dominio: str = "",
    ttl_s: float = 900.0,
) -> Dict[str, Any]:
    continuidade = dict((estado_atual or {}).get("continuidade_geral") or {})
    dominios = dict(continuidade.get("dominios") or {})
    agora = time.time()
    dominio_norm = normalizar_dominio_continuidade(dominio) if dominio else _dominio_pedido_no_texto(texto)
    if not dominio_norm:
        dominio_norm = str(continuidade.get("dominio_ativo") or "").strip()
    registro = dict(dominios.get(dominio_norm) or {}) if dominio_norm else {}
    try:
        expira_em = float(registro.get("expira_em") or 0.0)
        idade = agora - float(registro.get("ts") or 0.0)
    except (TypeError, ValueError):
        return {}
    if not registro or not registro.get("ativa", True) or idade > ttl_s or (expira_em and agora >= expira_em):
        return {}
    registro["dominio"] = dominio_norm
    registro["idade_s"] = max(0.0, idade)
    return registro


def selecionar_referente_saliente(
    estado_atual: Dict[str, Any] | None,
    *,
    texto: str = "",
    dominio: str = "",
    ttl_s: float = 900.0,
) -> Dict[str, Any]:
    """Escolhe um referente por uma ordem única e auditável.

    A ordem evita o problema clássico de uma entidade antiga vencer uma ação
    recém-confirmada: pendência canônica ativa, contrato da ação atual,
    resultado oficial do mesmo domínio e, por último, o foco histórico.
    """
    estado = dict(estado_atual or {})
    agora = time.time()
    dominio_norm = normalizar_dominio_continuidade(dominio) if dominio else _dominio_pedido_no_texto(texto)

    pendencia = dict(estado.get("pendencia_acao_canonica") or {})
    if pendencia.get("status") in {"ativa", "em_processamento"}:
        try:
            ativa = float(pendencia.get("expira_em") or 0.0) > agora
        except (TypeError, ValueError):
            ativa = False
        if ativa:
            alvo = str(pendencia.get("referencia") or "").strip()
            dados = dict(pendencia.get("metadados") or {})
            dominio_pendente = normalizar_dominio_continuidade(
                habilidade=str(pendencia.get("origem") or ""),
                intent=str(dados.get("intent") or ""),
            )
            if not dominio_norm or dominio_pendente == dominio_norm:
                return {
                    "fonte_salienca": "pendencia_canonica",
                    "dominio": dominio_pendente,
                    "intent": str(dados.get("intent") or ""),
                    "alvo": alvo,
                    "params": dados,
                    "status": str(pendencia.get("status") or ""),
                }

    contrato = dict(estado.get("ultima_acao_contrato") or {})
    try:
        contrato_recente = agora - float(estado.get("ultima_acao_ts") or 0.0) <= ttl_s
    except (TypeError, ValueError):
        contrato_recente = False
    dominio_contrato = normalizar_dominio_continuidade(
        dominio=str(contrato.get("dominio") or ""), intent=str(contrato.get("intent") or ""),
    )
    if contrato_recente and contrato.get("intent") and (not dominio_norm or dominio_contrato == dominio_norm):
        return {
            "fonte_salienca": "acao_atual",
            "dominio": dominio_contrato,
            "intent": str(contrato.get("intent") or ""),
            "alvo": str(contrato.get("alvo") or ""),
            "status": str(contrato.get("status") or ""),
            "confirmado": contrato.get("confirmado"),
        }

    oficial = selecionar_continuidade(
        estado, texto=texto, dominio=dominio_norm, ttl_s=ttl_s,
    )
    if oficial:
        return {"fonte_salienca": "continuidade_dominio", **oficial}
    return {}


def selecionar_continuidade_por_classe(
    estado_atual: Dict[str, Any] | None,
    *,
    classe: str = "auto",
    ttl_s: float = 900.0,
) -> Dict[str, Any]:
    """Seleciona foco oficial sem recorrer aos campos legados."""
    continuidade = dict((estado_atual or {}).get("continuidade_geral") or {})
    dominios = dict(continuidade.get("dominios") or {})
    classe_norm = str(classe or "auto").strip().casefold()
    candidatos = []
    agora = time.time()
    for dominio, bruto in dominios.items():
        item = dict(bruto or {})
        try:
            idade = agora - float(item.get("ts") or 0.0)
            expira_em = float(item.get("expira_em") or 0.0)
        except (TypeError, ValueError):
            continue
        if not item or not item.get("ativa", True) or idade > ttl_s or (expira_em and agora >= expira_em):
            continue
        if classe_norm in {"conversa", "conversacional"} and dominio != "conversa":
            continue
        if classe_norm in {"operacao", "operação", "operacional"} and dominio == "conversa":
            continue
        item["dominio"] = dominio
        item["idade_s"] = max(0.0, idade)
        candidatos.append(item)
    if not candidatos:
        return {}
    ativo = str(continuidade.get("dominio_ativo") or "")
    return max(
        candidatos,
        key=lambda item: (item.get("dominio") == ativo, float(item.get("ts") or 0.0)),
    )


def resumo_continuidade_para_prompt(
    estado_atual: Dict[str, Any] | None, *, texto: str = "", ttl_s: float = 900.0
) -> str:
    item = selecionar_continuidade(estado_atual, texto=texto, ttl_s=ttl_s)
    if not item:
        return ""
    partes = [
        f"dominio={item.get('dominio')}",
        f"evento={item.get('evento') or '-'}",
        f"intent={item.get('intent') or '-'}",
        f"alvo={item.get('alvo') or item.get('topico') or '-'}",
        f"status={item.get('status') or '-'}",
    ]
    return (
        "CONTINUIDADE GERAL SELECIONADA: " + " | ".join(partes) + ". "
        "Use somente este fio quando a fala atual realmente fizer referência a ele; um pedido explícito "
        "de outro domínio sempre substitui esta referência."
    )
