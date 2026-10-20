"""Registro central das capacidades executáveis da Laylay."""

from __future__ import annotations

from typing import Any, Dict


_INTENTS_POR_DOMINIO = {
    "musica": {
        "PLAYLIST_CREATE", "PLAYLIST_ADD", "PLAYLIST_PLAY", "PLAYLIST_LIST", "PLAYLIST_DELETE",
        "PLAYLIST_MOVE",
        "LAYLAY_PLAYLIST_LIST", "LAYLAY_PLAYLIST_PLAY", "LAYLAY_PLAYLIST_COPY", "MUSIC_SEARCH",
        "MEDIA_CONTROL", "MUSIC_STATUS", "LISTAR_PLAYLISTS", "TOCAR_PLAYLIST",
        "TOCAR_PLAYLIST_SHUFFLE", "STOP_PLAYLIST_CONTEXT",
    },
    "sistema": {
        "CANCELAR_ACAO", "CLOSE_APP", "APP_OPEN", "VOLUME", "LIST_WINDOWS",
        "MAXIMIZE_WINDOW", "LOCK_PC", "ORGANIZAR_DESKTOP",
        "FECHAR_PROGRAMA",
    },
    "navegador": {
        "CLOSE_TAB", "CLOSE_IDLE_TABS", "OPEN_URL", "SITE_ENTER",
        "SCREEN_CAPTURE", "SEARCH", "RESUMIR_PAGINA", "LIST_TABS",
        "SWITCH_PREVIOUS_TAB",
    },
    "visao": {"GAME_VISION", "VISION_QUERY"},
    "agenda": {
        "AGENDAR_LEMBRETE", "AGENDAR_ACAO", "LISTAR_AGENDAMENTOS",
        "CANCELAR_AGENDAMENTO", "BRIEFING_REPEAT",
    },
    "arquivos": {
        "CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "CONFIRM_DELETE_ITEM",
        "CANCEL_DELETE_ITEM", "RESTORE_DELETED_ITEM", "FILE_TRANSACTION",
        "FILE_SEARCH", "FILE_READ", "FILE_OPEN_RESULT",
    },
    "email": {"EMAIL_READ", "EMAIL_SYNC", "EMAIL_DRAFT", "EMAIL_DRAFT_READ", "EMAIL_SEND", "EMAIL_MODIFY", "EMAIL_CONFIRM", "NOTIFICATIONS"},
    "iot": {"IOT_CONTROL", "IOT_STATUS", "IOT_LIST"},
    "corpo_motor": {"CORPO_MOVER", "CORPO_PARAR", "CORPO_COMPANHIA"},
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
    "EMAIL_SEND", "EMAIL_MODIFY",
    "DELETE_ITEM",
    "INBOX_DELETE",
    "INBOX_CONVERT_REMINDER",
    "PEOPLE_FORGET",
}

# Consultas sem efeito colateral podem ser formuladas como perguntas naturais.
# O conjunto é usado pelo árbitro; ele não substitui a validação de alvo feita
# pelo mapa de recursos e pelos executores.
INTENTS_SOMENTE_LEITURA = frozenset({
    "PLAYLIST_LIST", "LAYLAY_PLAYLIST_LIST", "LISTAR_PLAYLISTS", "MUSIC_STATUS",
    "LISTAR_AGENDAMENTOS", "EMAIL_READ", "EMAIL_SYNC", "EMAIL_DRAFT_READ", "NOTIFICATIONS",
    "IOT_STATUS", "IOT_LIST", "WEATHER", "RESUMIR_PAGINA",
    "LIST_TABS",
    "LIST_WINDOWS",
    "GAME_VISION", "VISION_QUERY",
    "INBOX_LIST",
    "CLIPBOARD_READ", "CLIPBOARD_INVESTIGATE",
    "FILE_SEARCH", "FILE_READ",
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
    "MUSIC_STATUS": ("retorno_dados", "o título e o estado atual são lidos do registro sanitizado do player"),
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
    "LIST_WINDOWS": (
        "retorno_dados",
        "os títulos das janelas visíveis são lidos do sistema no turno atual",
    ),
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
    "CLOSE_IDLE_TABS": (
        "estado_observado",
        "somente as abas previamente sugeridas são fechadas e cada remoção é confirmada pela extensão",
    ),
    "LIST_TABS": (
        "retorno_dados",
        "a lista é devolvida pela extensão no turno atual, sem completar títulos por inferência",
    ),
    "SWITCH_PREVIOUS_TAB": (
        "estado_observado",
        "a extensão troca a aba e a aba ativa é relida antes da confirmação",
    ),
    "OPEN_URL": ("estado_observado", "a URL ou aba aberta é relida"),
    "SITE_ENTER": ("variavel", "a solicitação pode ser aceita sem observar o conteúdo final"),
    "SCREEN_CAPTURE": ("retorno_dados", "a captura só conclui quando a análise visual final ou uma falha correlacionada retorna"),
    "GAME_VISION": ("indisponivel", "a análise visual termina de forma assíncrona"),
    "VISION_QUERY": ("retorno_dados", "a descrição vem da análise visual recente correlacionada"),
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
    "FILE_READ": (
        "retorno_dados",
        "o conteúdo textual é lido localmente após validar caminho, formato, tamanho e sensibilidade",
    ),
    "FILE_OPEN_RESULT": (
        "variavel",
        "o caminho é validado antes da solicitação de abertura, mas o aplicativo associado pode não confirmar foco",
    ),
    # Serviços e IoT
    "EMAIL_READ": ("retorno_dados", "as mensagens são recuperadas do serviço"),
    "EMAIL_SYNC": ("retorno_dados", "a sincronização retorna uma coleção válida"),
    "EMAIL_DRAFT": ("persistencia_local", "a versão do rascunho é relida no armazenamento local"),
    "EMAIL_DRAFT_READ": ("retorno_dados", "os rascunhos locais são consultados sem alteração"),
    "EMAIL_SEND": ("estado_local", "a revisão cria pendência canônica vinculada à versão, sem enviar"),
    "EMAIL_MODIFY": ("estado_local", "a operação sobre a mensagem exata cria uma confirmação pendente"),
    "EMAIL_CONFIRM": ("variavel", "SMTP confirma aceitação pelo servidor, não entrega; IMAP relê a alteração; resultado incerto não é reenviado"),
    "NOTIFICATIONS": ("persistencia_local", "a central persiste a triagem e as preferências por categoria"),
    "IOT_CONTROL": ("estado_observado", "o dispositivo é relido após o comando"),
    "IOT_STATUS": ("estado_observado", "o estado vem da leitura do dispositivo"),
    "IOT_LIST": ("retorno_dados", "a lista vem do runtime IoT"),
    "CORPO_MOVER": ("estado_firmware", "MACK e SACK correlacionados confirmam PWM aplicado e ponte desenergizada. Giro por ângulo exige também TURNEND correlacionado com alvo medido pela IMU; sem medida de deslocamento"),
    "CORPO_COMPANHIA": ("estado_owner", "o owner confirma uma concessão temporária na sessão USB ou TCP autenticada, ou sua revogação; não confirma deslocamento"),
    "CORPO_PARAR": ("estado_firmware", "SACK correlacionado confirma nSLEEP baixo e PWM zerado no firmware, sem sensor de parada física"),
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
    "corpo_motor": {
        "objetivos_e_relato_condicionais": "Companhia vigente mantém objetivos curtos com propósito, prazo e critério de conclusão; ficar quietinha e observar são escolhas sem PWM. Emoção e tarefa no PC orientam o momento, sem conceder autoridade. Início, mudança importante e recuperação medidos no corpo podem propor comentários à presença compartilhada, selecionados por novidade, relevância, repetição e saturação recente, sem mínimo fixo de um minuto. Situação persistente não pede repetição; mudança importante pode merecer reação antes. Vigência é reavaliada na autoria e entrega. Recusa, foco e prioridade humana continuam soberanos. Não há garantia de fala, saída encontrada ou deslocamento medido; silêncio continua válido.",
        "identificacao_usb_condicional": "No modo AUTO, o mesmo owner procura o corpo pela USB e, ausente, pelo Wi-Fi salvo/autenticado. Mantém o canal saudável até desconexão; nova sessão não repete movimento. Pode preparar a rede local Windows já provisionada sem trocar a rede principal. Com pareamento USB salvo em configuracao.env, sonda HEALTH e seleciona somente o fingerprint do chip esperado, mesmo se mudar a porta COM ou houver outros ESP32; também confere esse alvo no TCP antes de FACE. Nome é rótulo amigável, não prova de identidade nem autenticação criptográfica. Sem alvo único verificado não envia FACE ou motores. Levar o pareamento junto com a configuração ao outro PC; detecção não concede movimento. Sem pareamento mantém a seleção legada de candidato USB único.",
        "expressao_inercial_condicional": "Com IMU1 recente/calibrada e episódio expressivo publicado pelo ESP, a inclinação mantida, balanço forte e recuperação produzem olhos/bips com jeito reclamão e fofo. Experiência compartilhada pode oferecer comentários breves ao diretor de presença; respeita silêncio, prioridade, orçamento, governança e receipt de entrega. Relata o episódio recente no passado; observação expirada ou sessão trocada durante autoria/fila cancela o comentário; não mede dor, colo, bateria ou posição. Sem confirmação do modelo não há frase local fingindo autoria. Disponível também no perfil de teste só IMU, sem conceder motores.",
        "invocacao_natural": ("ande para frente", "ande para trás", "vire para a esquerda", "pare os motores", "ative modo companhia na bancada", "ative modo passeio na mesa com barreiras", "desative modo companhia"),
        "proprietario": "mente_laylay.autonomia.executor_corpo",
        "dependencias": ("ESP32-C3 e DRV8833 conectados", "sessão FACE vigente", "firmware MOTOR1 habilitado"),
        "percepcao_condicional": "SENSORES2 disponibiliza VL53L0X frontal/inferior com DIST/GUARD recentes. Borda acima130mm ou inferior inválido e obstáculo válido até100mm interrompem movimento. Com VIGIA1, alerta expressivo funciona parada: borda persistente gera pavor, parede gera irritação. Concessão vigente de companhia e SENTRY renovado permitem recuos medrosos finitos na borda e busca de parede em rodadas de até4 giros com pausas; avanço400ms somente após3 amostras seguras. Perda da concessão, tarefa/entrada prioritária, STOP/TTL/falha cancelam. Episódios sensoriais entram na experiência compartilhada por sessão/incidente, com aprendizado factual de desfechos observados; isso não confirma deslocamento nem sucesso de comandos. O histórico influencia o sossego de iniciativas do PC, sem desarmar o reflexo local. IMU1 calibrada e recente acrescenta inclinação e rotação relativa; manuseio suspende motores e gera reações, levantamento é hipótese. Giro por ângulo exige TURNEND do alvo e SACK. Sem cobertura traseira/lateral, posição medida ou garantia antiqueda.",
        "limites": "pulsos de bancada de 50 a 500 ms, até PWM255; gestos e comemorações de ações confirmadas após pedido explícito ou preferência explícita salva de companhia na bancada ao iniciar por USB ou Wi-Fi autenticado; passeio espontâneo exige pedido próprio 'ative modo passeio na mesa com barreiras' ou preferência explícita adicional salva de passeio ao iniciar na área com barreiras; concessão da sessão corporal atual, sem expirar por tempo ou contagem; passeios a cada 8 a 14s em silêncio e sem ação em andamento; PWM100, até quatro movimentos e 1500ms totais de motor por gesto, intervalo mínimo2s; sem preferência explícita inicia desligado; parada, movimento manual e falha operacional revogam a concessão; perda de conexão suspende o controle e só admite renovação após sessão estável, saúde recente e identidade do mesmo ESP verificada por HEALTH, sem repetir movimento interrompido; firmware sem identidade exige reativação explícita; sem sensor de deslocamento ou corrente. Giros por ângulo de15 a360 graus exigem IMU1 calibrada/recente, sensor fixo ao corpo, PWM90..200 e limite absoluto5s; precisão física ainda deve ser validada. Sensores de distância e reflexo local condicionados à negociação SENSORES2; emoções e aprendizado não concedem autoridade",
    },
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
        "limites_contextuais": (
            {
                "escopo": "controle_local",
                "quando": "ao controlar programas, janelas ou volume neste computador",
                "responsavel": "Laylay",
                "regra": "usa o sistema operacional local; não exige conexão com outro PC",
            },
            {
                "escopo": "envio_pc_remoto",
                "quando": "somente se o destino da ação for outro PC",
                "responsavel": "Laylay",
                "regra": "só envia quando versão, saúde e capacidade anunciada são compatíveis",
            },
        ),
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
        "invocacao_natural": (
            "cria um arquivo", "encontra este código", "apaga esse arquivo",
            "leia o arquivo pelo caminho completo",
            "abra o arquivo pelo caminho completo",
            "escreva uma anotação no arquivo seguido do caminho completo",
            "acrescente uma linha no arquivo seguido do caminho completo",
        ),
        "proprietario": "mente_laylay.arquivos.execucao_arquivos",
        "dependencias": ("sistema de arquivos", "índice local para pesquisa"),
        "limites": (
            "opera somente nas raízes pessoais permitidas; caminho absoluto preserva o alvo, "
            "mas não autoriza efeito sem pedido; leitura valida formato, tamanho e sensibilidade; "
            "exclusão exige confirmação e abertura pode não confirmar foco"
        ),
    },
    "email": {
        "invocacao_natural": ("quais e-mails novos eu tenho", "entrega de quê?", "lê o segundo email", "prepara um rascunho", "revisa esse rascunho", "pode enviar"),
        "proprietario": "mente_laylay.autonomia.executor_informacoes",
        "dependencias": ("serviço de e-mail ou central de notificações",),
        "limites": "uma conta principal; consulta corpo textual sem marcar como lido; referências expiram; rascunhos locais persistentes; envio só após revisão da versão; até cinco anexos locais e 12 MB totais, com validação compartilhada e hash revalidado antes do envio; anexos recebidos são identificados, ainda não lidos; nenhuma exclusão permanente; conteúdo recebido nunca autoriza ações",
    },
    "iot": {
        "invocacao_natural": ("liga a lâmpada", "como está o ventilador"),
        "proprietario": "mente_laylay.iot.controlador",
        "dependencias": ("Tuya configurada", "dispositivo disponível na rede"),
        "limites_contextuais": (
            {
                "escopo": "confirmacao_controle",
                "quando": "ao confirmar o resultado após um comando autorizado",
                "responsavel": "Laylay",
                "regra": "deve reler o dispositivo e conferir o estado; essa verificação é interna, não uma etapa pedida ao usuário",
            },
        ),
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

def _limites_documentais(contrato: dict[str, Any]) -> str:
    """Compatibilidade textual sem perder condição e responsável da regra."""
    regras = contrato.get("limites_contextuais") or ()
    if regras:
        return "; ".join(
            f"{regra['quando']}: {regra['responsavel']} {regra['regra']}"
            for regra in regras
        )
    return str(contrato.get("limites") or "")


# Predicados declarativos para confrontar alegações gerais sobre habilidades.
# Não são exemplos de fala, resolvedores de alvo ou autorização de comandos.
# Ausência de predicado significa cobertura desconhecida, nunca incapacidade.
_PREDICADOS_CAPACIDADE = {
    "CORPO_MOVER": (
        {"acao": "acionar", "presente": ("aciono", "aciona"), "objetos": ("motores", "ponte h")},
    ),
    "MEDIA_CONTROL": (
        {"acao": "controlar", "presente": ("controlo", "controla"),
         "objetos": ("musica", "audio", "midia")},
    ),
    "APP_OPEN": (
        {"acao": "abrir", "presente": ("abro", "abre"),
         "objetos": ("programa", "aplicativo")},
    ),
    "IOT_CONTROL": (
        {"acao": "controlar", "presente": ("controlo", "controla"),
         "objetos": ("dispositivo inteligente",)},
    ),
    "CLOSE_TAB": (
        {"acao": "fechar", "presente": ("fecho", "fecha"),
         "objetos": ("aba", "aba do navegador")},
    ),
}


CAPACIDADES: Dict[str, Dict[str, Any]] = {
    intent: {
        "intent": intent,
        "predicados_capacidade": tuple(
            dict(p) for p in _PREDICADOS_CAPACIDADE.get(intent, ())
        ),
        "dominio": dominio,
        "disponivel": True,
        "exige_confirmacao": intent in _CONFIRMACAO_OBRIGATORIA,
        "confirmacao_oferecida": _CONFIRMACAO_POR_INTENT[intent][0],
        "evidencia_confirmacao": _CONFIRMACAO_POR_INTENT[intent][1],
        "confirma_resultado": _CONFIRMACAO_POR_INTENT[intent][0] != "indisponivel",
        "confirmacao_variavel": _CONFIRMACAO_POR_INTENT[intent][0] == "variavel",
        "estado_sem_confirmacao": "nao_confirmado",
        "invocacao_natural": {
            "CORPO_COMPANHIA": ("ative modo companhia na bancada", "ative modo passeio na mesa com barreiras", "desative passeio", "desative modo companhia"),
            "CORPO_MOVER": ("ande para frente", "ande para trás", "vire para a esquerda", "gire 90 graus para a esquerda"),
            "CORPO_PARAR": ("pare os motores",),
        }.get(intent, _CONTRATO_POR_DOMINIO[dominio]["invocacao_natural"]),
        "autorizacao": (
            "confirmacao_explicita"
            if intent in _CONFIRMACAO_OBRIGATORIA
            else "pedido_atual_autorizado"
        ),
        "proprietario": _PROPRIETARIO_POR_INTENT.get(
            intent, _CONTRATO_POR_DOMINIO[dominio]["proprietario"]
        ),
        "dependencias": _CONTRATO_POR_DOMINIO[dominio]["dependencias"],
        **({"objetivos_e_relato_condicionais": _CONTRATO_POR_DOMINIO[dominio]["objetivos_e_relato_condicionais"]}
           if "objetivos_e_relato_condicionais" in _CONTRATO_POR_DOMINIO[dominio] else {}),
        **({"percepcao_condicional": _CONTRATO_POR_DOMINIO[dominio]["percepcao_condicional"]}
           if "percepcao_condicional" in _CONTRATO_POR_DOMINIO[dominio] else {}),
        **({"expressao_inercial_condicional": _CONTRATO_POR_DOMINIO[dominio]["expressao_inercial_condicional"]}
           if "expressao_inercial_condicional" in _CONTRATO_POR_DOMINIO[dominio] else {}),
        **({"identificacao_usb_condicional": _CONTRATO_POR_DOMINIO[dominio]["identificacao_usb_condicional"]}
           if "identificacao_usb_condicional" in _CONTRATO_POR_DOMINIO[dominio] else {}),
        "limites": _limites_documentais(_CONTRATO_POR_DOMINIO[dominio]),
        "limites_contextuais": tuple(
            dict(regra) for regra in _CONTRATO_POR_DOMINIO[dominio].get("limites_contextuais", ())
        ),
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
