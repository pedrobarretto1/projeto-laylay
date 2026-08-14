"""Registro central das capacidades executáveis da Laylay."""

from __future__ import annotations

from typing import Any, Dict


_INTENTS_POR_DOMINIO = {
    "musica": {
        "PLAYLIST_CREATE", "PLAYLIST_ADD", "PLAYLIST_PLAY", "PLAYLIST_LIST", "PLAYLIST_DELETE",
        "PLAYLIST_MOVE",
        "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY", "MUSIC_SEARCH",
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
        "SCREEN_CAPTURE", "SEARCH", "RESUMIR_PAGINA",
    },
    "visao": {"GAME_VISION"},
    "agenda": {
        "AGENDAR_LEMBRETE", "AGENDAR_ACAO", "LISTAR_AGENDAMENTOS",
        "CANCELAR_AGENDAMENTO", "BRIEFING_REPEAT",
    },
    "arquivos": {
        "CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "CONFIRM_DELETE_ITEM",
        "CANCEL_DELETE_ITEM", "RESTORE_DELETED_ITEM", "FILE_TRANSACTION",
        "FILE_SEARCH", "FILE_OPEN_RESULT",
    },
    "email": {"EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS"},
    "iot": {"IOT_CONTROL", "IOT_STATUS", "IOT_LIST"},
    "area_transferencia": {
        "CLIPBOARD_READ", "CLIPBOARD_TRANSFORM", "CLIPBOARD_SEARCH",
        "CLIPBOARD_INVESTIGATE", "CLIPBOARD_WRITE", "CLIPBOARD_UNDO",
        "CLIPBOARD_LEARN",
    },
    "caixa_entrada": {
        "INBOX_ADD", "INBOX_ADD_DISCUSSION", "INBOX_LIST", "INBOX_CONVERT_REMINDER",
        "INBOX_DELETE", "CONFIRM_INBOX_DELETE",
        "CANCEL_INBOX_ACTION",
    },
    "pessoas": {
        "PEOPLE_REMEMBER", "PEOPLE_QUERY", "PEOPLE_LIST", "PEOPLE_FORGET",
    },
    "memoria": {"LEARNING_QUERY"},
    "cooperacao": {"COOPERATIVE_PLAN"},
    "conversa": {"WEATHER", "SUGGEST_ACTION"},
}

_CONFIRMACAO_OBRIGATORIA = {
    "DELETE_ITEM",
    "INBOX_DELETE",
    "INBOX_CONVERT_REMINDER",
    "PEOPLE_FORGET",
}

# Consultas sem efeito colateral podem ser formuladas como perguntas naturais.
# O conjunto é usado pelo árbitro; ele não substitui a validação de alvo feita
# pelo mapa de recursos e pelos executores.
INTENTS_SOMENTE_LEITURA = frozenset({
    "PLAYLIST_LIST", "LAYLAY_PLAYLIST_LIST", "LISTAR_PLAYLISTS",
    "LISTAR_AGENDAMENTOS", "EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS",
    "IOT_STATUS", "IOT_LIST", "WEATHER", "RESUMIR_PAGINA",
    "GAME_VISION",
    "INBOX_LIST",
    "CLIPBOARD_READ", "CLIPBOARD_INVESTIGATE",
    "FILE_SEARCH",
    "PEOPLE_QUERY", "PEOPLE_LIST",
    "LEARNING_QUERY",
})

# A confirmação descreve a evidência que o executor realmente consegue obter.
# ``variavel`` significa que há rotas confirmáveis e rotas apenas enviadas; o
# ResultadoAcao decide por chamada, sem promover ``executou=True`` a sucesso.
_CONFIRMACAO_POR_INTENT = {
    # Música
    "PLAYLIST_CREATE": ("persistencia_local", "a playlist vazia reaparece no armazenamento local"),
    "PLAYLIST_ADD": ("persistencia_local", "a faixa reaparece no armazenamento da playlist"),
    "PLAYLIST_PLAY": ("variavel", "a aba pode ser observada; o cliente remoto informa entrega, mas nem sempre confirma áudio"),
    "PLAYLIST_LIST": ("retorno_dados", "a lista foi lida do armazenamento"),
    "PLAYLIST_DELETE": ("persistencia_local", "a ausência é conferida no armazenamento"),
    "PLAYLIST_MOVE": ("persistencia_local", "a origem e o destino são persistidos no armazenamento"),
    "LAYLAY_PLAYLIST_LIST": ("retorno_dados", "a lista interna foi consultada"),
    "LAYLAY_PLAYLIST_PLAY": ("estado_observado", "a curadoria foi entregue ao player"),
    "LAYLAY_PLAYLIST_COPY": ("persistencia_local", "a cópia retorna sucesso do armazenamento"),
    "MUSIC_SEARCH": ("estado_observado", "a abertura da página musical é conferida"),
    "MEDIA_CONTROL": ("variavel", "Chrome pode observar o player; teclas globais locais ou remotas confirmam envio, não o estado final da mídia"),
    "LISTAR_PLAYLISTS": ("retorno_dados", "a lista foi consultada"),
    "TOCAR_PLAYLIST": ("variavel", "depende da rota usada para reprodução"),
    "TOCAR_PLAYLIST_SHUFFLE": ("variavel", "depende da rota usada para reprodução"),
    "STOP_PLAYLIST_CONTEXT": ("estado_local", "o contexto local de playlist é limpo"),
    "LEARNING_QUERY": ("retorno_dados", "os aprendizados foram lidos da memória persistente"),
    # Sistema
    "CANCELAR_ACAO": ("estado_local", "as pendências locais são removidas"),
    "CLOSE_APP": ("estado_observado", "a janela é relida localmente ou pelo cliente remoto compatível"),
    "FECHAR_PROGRAMA": ("variavel", "alias de CLOSE_APP"),
    "APP_OPEN": ("estado_observado", "a janela é relida localmente ou pelo cliente remoto compatível"),
    "VOLUME": ("estado_observado", "o nível é relido pela API de áudio local ou remota"),
    "MAXIMIZE_WINDOW": ("estado_observado", "a janela local ou remota é relida após a maximização"),
    "LOCK_PC": ("indisponivel", "a chamada de bloqueio não permite releitura antes do encerramento"),
    "ORGANIZAR_DESKTOP": (
        "estado_observado",
        "a seleção automática combina foco, áudio, recência e tempo aberto; a geometria "
        "das janelas movidas é relida e comparada com o lado solicitado",
    ),
    # Navegador
    "CLOSE_TAB": ("variavel", "a aba local pode ser relida; no cliente remoto o atalho confirma apenas o envio"),
    "CLOSE_IDLE_TABS": ("indisponivel", "o executor legado não devolve as abas finais"),
    "OPEN_URL": ("estado_observado", "a URL ou aba aberta é relida"),
    "SITE_ENTER": ("variavel", "a solicitação pode ser aceita sem observar o conteúdo final"),
    "SCREEN_CAPTURE": ("indisponivel", "o roteador ainda não recebe o caminho final da captura"),
    "GAME_VISION": ("indisponivel", "a análise visual termina de forma assíncrona"),
    "SEARCH": ("variavel", "a confirmação depende da rota de pesquisa escolhida"),
    "RESUMIR_PAGINA": (
        "retorno_dados",
        "o conteúdo da aba é lido e o resumo final é entregue no próprio turno",
    ),
    # Agenda
    "AGENDAR_LEMBRETE": ("persistencia_local", "o lembrete salvo é confirmado pelo armazenamento"),
    "AGENDAR_ACAO": ("persistencia_local", "a ação salva é confirmada pelo armazenamento"),
    "LISTAR_AGENDAMENTOS": ("retorno_dados", "os agendamentos são lidos do armazenamento"),
    "CANCELAR_AGENDAMENTO": ("persistencia_local", "o cancelamento retorna sucesso do armazenamento"),
    "BRIEFING_REPEAT": ("retorno_dados", "o briefing existente é recuperado"),
    # Arquivos
    "CREATE_FOLDER": ("estado_observado", "a existência é relida localmente ou pelo cliente remoto"),
    "CREATE_FILE": ("estado_observado", "a existência local do arquivo é relida"),
    "DELETE_ITEM": ("estado_observado", "a movimentação para a lixeira é relida localmente ou pelo cliente remoto"),
    "CONFIRM_DELETE_ITEM": ("persistencia_local", "a lixeira retorna o resultado da movimentação"),
    "CANCEL_DELETE_ITEM": ("estado_local", "a pendência local é removida sem apagar o item"),
    "RESTORE_DELETED_ITEM": ("estado_observado", "a restauração retorna o caminho recuperado"),
    "FILE_TRANSACTION": ("estado_observado", "origem e destino são conferidos pela transação"),
    "FILE_SEARCH": (
        "retorno_dados",
        "os resultados são lidos de um índice local efêmero por nome, caminho, conteúdo, tipo e data",
    ),
    "FILE_OPEN_RESULT": (
        "variavel",
        "o caminho é validado antes da solicitação de abertura, mas o aplicativo associado pode não confirmar foco",
    ),
    # Serviços e IoT
    "EMAIL_READ": ("retorno_dados", "as mensagens são recuperadas do serviço"),
    "EMAIL_SYNC": ("retorno_dados", "a sincronização retorna uma coleção válida"),
    "NOTIFICATIONS": ("persistencia_local", "a central persiste a triagem e as preferências por categoria"),
    "IOT_CONTROL": ("estado_observado", "o dispositivo é relido após o comando"),
    "IOT_STATUS": ("estado_observado", "o estado vem da leitura do dispositivo"),
    "IOT_LIST": ("retorno_dados", "a lista vem do runtime IoT"),
    "CLIPBOARD_READ": ("retorno_dados", "o texto é lido diretamente da área de transferência"),
    "CLIPBOARD_TRANSFORM": ("retorno_dados", "o resultado temporário é devolvido sem substituir o original"),
    "CLIPBOARD_SEARCH": ("variavel", "a pesquisa é encaminhada ao navegador sem persistir o conteúdo"),
    "CLIPBOARD_INVESTIGATE": (
        "retorno_dados",
        "o erro copiado é pesquisado internamente e uma síntese fundamentada é devolvida",
    ),
    "CLIPBOARD_WRITE": ("estado_observado", "o conteúdo escrito é relido e comparado ao resultado"),
    "CLIPBOARD_UNDO": ("estado_observado", "o texto anterior é restaurado e relido"),
    "CLIPBOARD_LEARN": ("persistencia_local", "o aprendizado explicitamente autorizado é salvo na memória"),
    "INBOX_ADD": ("persistencia_local", "a nota reaparece no arquivo da caixa de entrada"),
    "INBOX_ADD_DISCUSSION": (
        "persistencia_local",
        "o resumo estruturado da discussão reaparece no arquivo da caixa de entrada",
    ),
    "INBOX_LIST": ("retorno_dados", "as notas são lidas do armazenamento local"),
    "INBOX_CONVERT_REMINDER": ("variavel", "a conversão é encaminhada e confirmada pela agenda"),
    "INBOX_DELETE": ("persistencia_local", "a nota deixa de aparecer entre os itens ativos"),
    "CONFIRM_INBOX_DELETE": ("persistencia_local", "a exclusão pendente é aplicada ao armazenamento"),
    "CANCEL_INBOX_ACTION": ("estado_local", "a alteração pendente é descartada"),
    "PEOPLE_REMEMBER": (
        "persistencia_local",
        "a pessoa, a relação e a proveniência reaparecem no armazenamento local estruturado",
    ),
    "PEOPLE_QUERY": ("retorno_dados", "o perfil é lido da memória local de pessoas"),
    "PEOPLE_LIST": ("retorno_dados", "os perfis ativos são lidos da memória local"),
    "PEOPLE_FORGET": (
        "persistencia_local",
        "após confirmação, o perfil deixa de aparecer entre as memórias ativas",
    ),
    "COOPERATIVE_PLAN": (
        "estado_observado",
        "o coordenador acompanha as etapas e só confirma após o executor reler o resultado",
    ),
    "WEATHER": ("retorno_dados", "o provedor devolve dados meteorológicos válidos"),
    "SUGGEST_ACTION": ("indisponivel", "é apenas uma sugestão e não executa efeito"),
}

# O contrato abaixo é consumido pela consciência e pelo diagnóstico. Ele não
# substitui detector nem executor: descreve como cada domínio pode ser pedido,
# quem é responsável pela execução e quais condições limitam o resultado.
_CONTRATO_POR_DOMINIO = {
    "musica": {
        "invocacao_natural": ("toca uma música", "abre minha playlist", "pausa a música"),
        "proprietario": "mente_laylay.autonomia.executor_musical",
        "dependencias": ("catálogo local quando aplicável", "player ou navegador"),
        "limites": "o cliente remoto confirma entrega, mas controles globais não provam que o áudio mudou",
    },
    "sistema": {
        "invocacao_natural": ("abre o Opera", "maximiza a janela", "organiza a área de trabalho"),
        "proprietario": "mente_laylay.autonomia.executor_sistema",
        "dependencias": ("sistema operacional", "resolvedor de janelas"),
        "limites": "só envia ao PC remoto quando versão, saúde e capacidade anunciada são compatíveis",
    },
    "navegador": {
        "invocacao_natural": ("abre este site", "fecha esta aba", "resume a página atual"),
        "proprietario": "mente_laylay.autonomia.executor_navegador",
        "dependencias": ("WebSocket do navegador", "extensão Laylay carregada"),
        "limites": "só interage com ações reconhecidas e conteúdo acessível da aba",
    },
    "visao": {
        "invocacao_natural": ("olha minha tela", "analisa este item"),
        "proprietario": "mente_laylay.autonomia.executor_sistema",
        "dependencias": ("captura de tela", "provedor visual configurado"),
        "limites": "não afirma detalhes ilegíveis ou ausentes da imagem",
    },
    "agenda": {
        "invocacao_natural": ("me lembra amanhã", "lista meus lembretes"),
        "proprietario": "mente_laylay.autonomia.agendamento_mental",
        "dependencias": ("relógio local", "armazenamento da agenda"),
        "limites": "data ou horário ambíguo exige esclarecimento",
    },
    "arquivos": {
        "invocacao_natural": ("cria um arquivo", "encontra este código", "apaga esse arquivo"),
        "proprietario": "mente_laylay.arquivos.execucao_arquivos",
        "dependencias": ("sistema de arquivos", "índice local para pesquisa"),
        "limites": "opera somente em caminhos resolvidos e exclusão exige confirmação",
    },
    "email": {
        "invocacao_natural": ("quais e-mails novos eu tenho", "mostra minhas notificações"),
        "proprietario": "mente_laylay.autonomia.executor_informacoes",
        "dependencias": ("serviço de e-mail ou central de notificações",),
        "limites": "retorna apenas integrações configuradas e dados realmente lidos",
    },
    "iot": {
        "invocacao_natural": ("liga a lâmpada", "como está o ventilador"),
        "proprietario": "mente_laylay.iot.controlador",
        "dependencias": ("Tuya configurada", "dispositivo disponível na rede"),
        "limites": "confirma controle somente após reler o dispositivo",
    },
    "area_transferencia": {
        "invocacao_natural": ("o que eu copiei", "coloca isso em maiúsculas"),
        "proprietario": "mente_laylay.especialistas.area_transferencia",
        "dependencias": ("área de transferência local",),
        "limites": "conteúdo sensível não é persistido sem pedido explícito",
    },
    "caixa_entrada": {
        "invocacao_natural": ("anota esta ideia", "me fale minhas ideias"),
        "proprietario": "mente_laylay.especialistas.caixa_entrada_pessoal",
        "dependencias": ("armazenamento local da caixa de entrada",),
        "limites": "exclusão e conversão em lembrete exigem confirmação",
    },
    "pessoas": {
        "invocacao_natural": ("minha namorada se chama Nanda", "o que sabe sobre Nanda"),
        "proprietario": "mente_laylay.memoria_mental.memoria_pessoas",
        "dependencias": ("memória local de pessoas e relações",),
        "limites": "só guarda relações afirmadas e esquecer exige confirmação",
    },
    "memoria": {
        "invocacao_natural": ("o que você aprendeu comigo",),
        "proprietario": "mente_laylay.memoria_mental.aprendizado_runtime",
        "dependencias": ("memória de aprendizado com proveniência",),
        "limites": "não promove inferência isolada a fato confirmado",
    },
    "cooperacao": {
        "invocacao_natural": ("faz estas etapas juntas",),
        "proprietario": "mente_laylay.autonomia.orquestracao_cooperativa",
        "dependencias": ("porteiro", "executores participantes"),
        "limites": "cada etapa mantém autorização e evidência próprias",
    },
    "conversa": {
        "invocacao_natural": ("vai chover hoje", "o que você sugere"),
        "proprietario": "mente_laylay.autonomia.fluxos_conversa",
        "dependencias": ("provedor da habilidade quando necessário",),
        "limites": "sugestões não autorizam execução por conta própria",
    },
}

_PROPRIETARIO_POR_INTENT = {
    "RESUMIR_PAGINA": "mente_laylay.autonomia.comandos_imediatos",
    "NOTIFICATIONS": "mente_laylay.autonomia.central_notificacoes",
    "WEATHER": "mente_laylay.autonomia.executor_informacoes",
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
        "invocacao_natural": _CONTRATO_POR_DOMINIO[dominio]["invocacao_natural"],
        "autorizacao": (
            "confirmacao_explicita"
            if intent in _CONFIRMACAO_OBRIGATORIA
            else "pedido_atual_autorizado"
        ),
        "proprietario": _PROPRIETARIO_POR_INTENT.get(
            intent, _CONTRATO_POR_DOMINIO[dominio]["proprietario"]
        ),
        "dependencias": _CONTRATO_POR_DOMINIO[dominio]["dependencias"],
        "limites": _CONTRATO_POR_DOMINIO[dominio]["limites"],
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
    estado_bruto = snapshot.get(dominio)
    estado_dominio: Dict[str, Any] = (
        dict(estado_bruto) if isinstance(estado_bruto, dict) else {}
    )
    if str(estado_dominio.get("status") or "").lower() == "indisponivel":
        registro.update(disponivel=False, motivo="componente_indisponivel")
    return registro
