"""Registro central das capacidades executáveis da Laylay."""

from __future__ import annotations

from typing import Any, Dict


_INTENTS_POR_DOMINIO = {
    "musica": {
        "PLAYLIST_ADD", "PLAYLIST_PLAY", "PLAYLIST_LIST", "PLAYLIST_DELETE",
        "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_COPY", "MUSIC_SEARCH",
        "MEDIA_CONTROL", "LISTAR_PLAYLISTS", "TOCAR_PLAYLIST",
        "TOCAR_PLAYLIST_SHUFFLE", "STOP_PLAYLIST_CONTEXT",
    },
    "sistema": {
        "CANCELAR_ACAO", "CLOSE_APP", "APP_OPEN", "VOLUME",
        "MAXIMIZE_WINDOW", "LOCK_PC", "ORGANIZAR_DESKTOP",
        "FECHAR_PROGRAMA",
    },
    "navegador": {
        "CLOSE_TAB", "CLOSE_IDLE_TABS", "OPEN_URL", "SITE_ENTER",
        "SCREEN_CAPTURE", "SEARCH",
    },
    "agenda": {
        "AGENDAR_LEMBRETE", "AGENDAR_ACAO", "LISTAR_AGENDAMENTOS",
        "CANCELAR_AGENDAMENTO", "BRIEFING_REPEAT",
    },
    "arquivos": {
        "CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "CONFIRM_DELETE_ITEM",
        "CANCEL_DELETE_ITEM", "RESTORE_DELETED_ITEM", "FILE_TRANSACTION",
    },
    "email": {"EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS"},
    "iot": {"IOT_CONTROL", "IOT_STATUS", "IOT_LIST"},
    "conversa": {"WEATHER", "SUGGEST_ACTION"},
}

_CONFIRMACAO_OBRIGATORIA = {
    "DELETE_ITEM",
}

# A confirmação descreve a evidência que o executor realmente consegue obter.
# ``variavel`` significa que há rotas confirmáveis e rotas apenas enviadas; o
# ResultadoAcao decide por chamada, sem promover ``executou=True`` a sucesso.
_CONFIRMACAO_POR_INTENT = {
    # Música
    "PLAYLIST_ADD": ("persistencia_local", "a faixa reaparece no armazenamento da playlist"),
    "PLAYLIST_PLAY": ("variavel", "a aba pode ser observada; rotas remotas podem ficar sem retorno"),
    "PLAYLIST_LIST": ("retorno_dados", "a lista foi lida do armazenamento"),
    "PLAYLIST_DELETE": ("persistencia_local", "a ausência é conferida no armazenamento"),
    "LAYLAY_PLAYLIST_LIST": ("retorno_dados", "a lista interna foi consultada"),
    "LAYLAY_PLAYLIST_COPY": ("persistencia_local", "a cópia retorna sucesso do armazenamento"),
    "MUSIC_SEARCH": ("estado_observado", "a abertura da página musical é conferida"),
    "MEDIA_CONTROL": ("variavel", "Chrome pode responder; tecla global e PC remoto não informam o estado final"),
    "LISTAR_PLAYLISTS": ("retorno_dados", "a lista foi consultada"),
    "TOCAR_PLAYLIST": ("variavel", "depende da rota usada para reprodução"),
    "TOCAR_PLAYLIST_SHUFFLE": ("variavel", "depende da rota usada para reprodução"),
    "STOP_PLAYLIST_CONTEXT": ("estado_local", "o contexto local de playlist é limpo"),
    # Sistema
    "CANCELAR_ACAO": ("estado_local", "as pendências locais são removidas"),
    "CLOSE_APP": ("variavel", "o processo local é relido; envio remoto pode não responder"),
    "FECHAR_PROGRAMA": ("variavel", "alias de CLOSE_APP"),
    "APP_OPEN": ("variavel", "a janela local é relida; envio remoto pode não responder"),
    "VOLUME": ("variavel", "algumas APIs retornam aceite, mas o PC remoto não confirma o nível final"),
    "MAXIMIZE_WINDOW": ("variavel", "a janela local pode ser relida; envio remoto não confirma"),
    "LOCK_PC": ("indisponivel", "a chamada de bloqueio não permite releitura antes do encerramento"),
    "ORGANIZAR_DESKTOP": ("indisponivel", "o organizador não retorna o layout final observado"),
    # Navegador
    "CLOSE_TAB": ("variavel", "a aba local é relida; envio remoto pode não responder"),
    "CLOSE_IDLE_TABS": ("indisponivel", "o executor legado não devolve as abas finais"),
    "OPEN_URL": ("estado_observado", "a URL ou aba aberta é relida"),
    "SITE_ENTER": ("variavel", "a solicitação pode ser aceita sem observar o conteúdo final"),
    "SCREEN_CAPTURE": ("indisponivel", "o roteador ainda não recebe o caminho final da captura"),
    "SEARCH": ("variavel", "a confirmação depende da rota de pesquisa escolhida"),
    # Agenda
    "AGENDAR_LEMBRETE": ("persistencia_local", "o lembrete salvo é confirmado pelo armazenamento"),
    "AGENDAR_ACAO": ("persistencia_local", "a ação salva é confirmada pelo armazenamento"),
    "LISTAR_AGENDAMENTOS": ("retorno_dados", "os agendamentos são lidos do armazenamento"),
    "CANCELAR_AGENDAMENTO": ("persistencia_local", "o cancelamento retorna sucesso do armazenamento"),
    "BRIEFING_REPEAT": ("retorno_dados", "o briefing existente é recuperado"),
    # Arquivos
    "CREATE_FOLDER": ("variavel", "a existência local é relida; PC remoto depende de resposta"),
    "CREATE_FILE": ("estado_observado", "a existência local do arquivo é relida"),
    "DELETE_ITEM": ("variavel", "a ausência local é relida; PC remoto depende de resposta"),
    "CONFIRM_DELETE_ITEM": ("persistencia_local", "a lixeira retorna o resultado da movimentação"),
    "CANCEL_DELETE_ITEM": ("estado_local", "a pendência local é removida sem apagar o item"),
    "RESTORE_DELETED_ITEM": ("estado_observado", "a restauração retorna o caminho recuperado"),
    "FILE_TRANSACTION": ("estado_observado", "origem e destino são conferidos pela transação"),
    # Serviços e IoT
    "EMAIL_READ": ("retorno_dados", "as mensagens são recuperadas do serviço"),
    "EMAIL_SYNC": ("retorno_dados", "a sincronização retorna uma coleção válida"),
    "NOTIFICATIONS": ("variavel", "somente integrações específicas retornam sucesso"),
    "IOT_CONTROL": ("estado_observado", "o dispositivo é relido após o comando"),
    "IOT_STATUS": ("estado_observado", "o estado vem da leitura do dispositivo"),
    "IOT_LIST": ("retorno_dados", "a lista vem do runtime IoT"),
    "WEATHER": ("retorno_dados", "o provedor devolve dados meteorológicos válidos"),
    "SUGGEST_ACTION": ("indisponivel", "é apenas uma sugestão e não executa efeito"),
}

_INTENTS_CATALOGADAS = {intent for intents in _INTENTS_POR_DOMINIO.values() for intent in intents}
if _INTENTS_CATALOGADAS != set(_CONFIRMACAO_POR_INTENT):
    faltantes = sorted(_INTENTS_CATALOGADAS - set(_CONFIRMACAO_POR_INTENT))
    excedentes = sorted(set(_CONFIRMACAO_POR_INTENT) - _INTENTS_CATALOGADAS)
    raise RuntimeError(
        f"auditoria de confirmação incompleta: faltantes={faltantes}; excedentes={excedentes}"
    )

CAPACIDADES: Dict[str, Dict[str, Any]] = {
    intent: {
        "intent": intent,
        "dominio": dominio,
        "disponivel": True,
        "exige_confirmacao": intent in _CONFIRMACAO_OBRIGATORIA,
        "confirmacao_oferecida": _CONFIRMACAO_POR_INTENT[intent][0],
        "evidencia_confirmacao": _CONFIRMACAO_POR_INTENT[intent][1],
        "confirma_resultado": _CONFIRMACAO_POR_INTENT[intent][0] != "indisponivel",
        "confirmacao_variavel": _CONFIRMACAO_POR_INTENT[intent][0] == "variavel",
        "estado_sem_confirmacao": "nao_confirmado",
    }
    for dominio, intents in _INTENTS_POR_DOMINIO.items()
    for intent in intents
}


def intents_registradas() -> frozenset[str]:
    return frozenset(CAPACIDADES)


def consultar_capacidade(
    intent: str,
    *,
    saude: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    nome = str(intent or "").upper().strip()
    registro = dict(CAPACIDADES.get(nome) or {})
    if not registro:
        return {
            "intent": nome,
            "dominio": "desconhecido",
            "disponivel": False,
            "motivo": "capacidade_nao_registrada",
        }
    snapshot = dict(saude or {})
    dominio = str(registro.get("dominio") or "")
    estado_dominio = snapshot.get(dominio) if isinstance(snapshot.get(dominio), dict) else {}
    if str(estado_dominio.get("status") or "").lower() == "indisponivel":
        registro.update(disponivel=False, motivo="componente_indisponivel")
    return registro
