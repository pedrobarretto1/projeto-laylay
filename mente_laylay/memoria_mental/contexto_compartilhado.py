"""Funcoes de contexto compartilhado entre as habilidades da Laylay."""

from __future__ import annotations

import time
import re
from typing import Any, Dict

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, normalizar_resultado_acao
from mente_laylay.memoria_mental.pendencia import criar_pendencia, limpar_pendencia, registrar_pendencia
from mente_laylay.memoria_mental.continuidade_geral import (
    normalizar_dominio_continuidade,
    registrar_evento_continuidade,
)

from mente_laylay.memoria_mental.consciencia_temporal import (
    atualizar_consciencia_temporal,
)
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_interacao_semantica,
)
from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial


def estado_mental_inicial() -> Dict[str, Any]:
    """Compatibilidade pública para o estado criado pelo módulo dedicado."""
    return criar_estado_mental_inicial()


from mente_laylay.memoria_mental.continuidade_contexto import (
    classificar_pergunta_com_proposito,
    limpar_oferta_pendente,
    oferta_pendente_ativa,
    registrar_feedback_musical_conversacional,
    registrar_oferta_pendente,
    texto_parece_pergunta_aberta,
)

from mente_laylay.memoria_mental.continuidade_contexto import (
    alvo_corrigido_ativo,
    estrutura_arquivo_recente,
    limpar_pergunta_aberta,
    limpar_promessa_conversacional,
    pergunta_aberta_ativa,
    promessa_conversacional_ativa,
    registrar_alvo_corrigido,
    registrar_continuidade_da_fala,
    registrar_estrutura_arquivo_recente,
    registrar_pergunta_aberta,
    registrar_promessa_conversacional,
    texto_parece_resposta_curta_a_pergunta,
)


def intencao_reexecutavel(intent: str) -> bool:
    return str(intent or "").upper().strip() in {
        "APP_OPEN",
        "CLOSE_APP",
        "OPEN_URL",
        "CLOSE_TAB",
        "PLAYLIST_PLAY",
        "PLAYLIST_ADD",
        "MUSIC_SEARCH",
        "VOLUME",
        "MEDIA_CONTROL",
        "WEATHER",
        "EMAIL_READ",
        "EMAIL_SYNC",
        "NOTIFICATIONS",
        "BRIEFING_REPEAT",
        "SITE_ENTER",
        "LAYLAY_PLAYLIST_LIST",
        "LAYLAY_PLAYLIST_PLAY",
        "PLAYLIST_LIST",
        "IOT_CONTROL",
        "IOT_STATUS",
        "IOT_LIST",
        "INBOX_LIST",
        "ORGANIZAR_DESKTOP",
    }


_RESULTADOS_JA_SATISFEITOS_REFERENCIAVEIS = {
    ("APP_OPEN", "ja_aberto_focado"),
}


def resultado_ja_satisfeito_referenciavel(
    *,
    intent: str,
    status: str,
    confirmado: bool | None,
) -> bool:
    # Só no-ops confirmados que mantêm um alvo operacional vivo.
    chave = (
        str(intent or "").strip().upper(),
        str(status or "").strip().casefold(),
    )
    return bool(
        confirmado is True
        and chave in _RESULTADOS_JA_SATISFEITOS_REFERENCIAVEIS
    )


def contrato_confirma_referencia_operacional(
    *,
    intent: str,
    status: str,
    executou: bool | None,
    confirmado: bool | None,
) -> bool:
    # Referência confirma alvo; nunca concede autorização.
    return bool(
        confirmado is True
        and (
            executou is True
            or resultado_ja_satisfeito_referenciavel(
                intent=intent,
                status=status,
                confirmado=confirmado,
            )
        )
    )


def _resultado_pode_promover_referencia(
    contrato: ResultadoAcao, status: str,
) -> bool:
    """Separa a última tentativa do último referente operacional válido."""
    status_norm = str(status or "").strip().casefold()
    marcadores_falha = (
        "falha", "erro", "indispon", "nao_encontr", "não_encontr",
        "sem_resultado", "cancel", "recus", "expirad", "alvo_ausente",
        "referencia_ausente", "referência_ausente", "nao_confirmado",
        "não_confirmado", "sem_confirmacao", "sem_confirmação", "sem_pendencia",
        "sem_pendência",
    )
    if any(marcador in status_norm for marcador in marcadores_falha):
        return False
    pendente = (
        status_norm.startswith("aguardando")
        or status_norm.startswith("pendente")
        or status_norm.endswith("_pendente")
    )
    if pendente:
        return True
    return bool(
        contrato.executou is True
        or resultado_ja_satisfeito_referenciavel(
            intent=contrato.intent,
            status=status_norm,
            confirmado=contrato.confirmado,
        )
    )


def registrar_resultado_execucao(
    estado_atual: Dict[str, Any] | None,
    resultado: ResultadoAcao | Dict[str, Any] | None = None,
    texto: str = "",
    executou: bool | None = None,
    *,
    origem: str = "",
    status: str = "",
) -> Dict[str, Any]:
    if not isinstance(resultado, (dict, ResultadoAcao)):
        return dict(estado_atual or {})

    estado = dict(estado_atual or {})
    contrato = normalizar_resultado_acao(
        resultado,
        texto=texto,
        executou=executou,
        origem=origem,
        status=status,
    )
    intent = contrato.intent
    params = dict(contrato.params)
    status_final = contrato.status
    registro_generico = not bool(status_final)
    texto_curto = str(texto or "").strip()[:200]
    mesmo_intent = str(estado.get("ultima_acao_intent") or "").strip().upper() == intent
    mesmo_texto = str(estado.get("ultima_acao_texto") or "").strip() == texto_curto
    mesmo_resultado = mesmo_intent and mesmo_texto

    # Uma pendência visual só pode sobreviver a dados que complementem aquela
    # análise. Quando uma ação de outro domínio foi realmente roteada, ela
    # substitui o assunto operacional anterior e impede respostas tardias sobre
    # inventário depois de "liga a luz", "abre o navegador" etc.
    pendencia = dict(estado.get("pendencia_atual") or {})
    if (
        pendencia.get("status") == "ativa"
        and str(pendencia.get("origem") or "") == "visao_jogo"
        and intent not in {"GAME_VISION", "GAME_VISION_CONTINUE"}
    ):
        estado = limpar_pendencia(estado, motivo="substituida_por_nova_acao")

    if not status_final:
        status_anterior = str(estado.get("ultima_acao_status") or "").strip().lower()
        if mesmo_resultado and status_anterior:
            status_final = status_anterior
        else:
            status_final = "executado" if contrato.executou is True else "falhou" if contrato.executou is False else "incerto"

    resultado_promovivel = _resultado_pode_promover_referencia(
        contrato, status_final,
    )
    estado["ultima_acao_promovivel"] = resultado_promovivel

    reexecucao_referencia_segura = bool(
        intent == "CREATE_FILE"
        and params.get("conteudo_ref")
        and contrato.confirmado is not True
        and status_final not in {"referencia_expirada", "referencia_divergente"}
    )
    estado["ultima_acao_status"] = status_final
    # Repeticao e referencia sao contratos diferentes. Uma tentativa falha nao
    # pode virar o referente de "ele/ela/isso", mas pode ser exatamente o que
    # o usuario quer refazer com "tenta de novo". O acoplamento anterior entre
    # os dois conceitos apagava falhas recuperaveis de IoT e playlists.
    tentativa_observada = bool(
        contrato.executou is not None or status_final not in {"", "incerto"}
    )
    reexecutavel = bool(
        (intencao_reexecutavel(intent) and tentativa_observada)
        or reexecucao_referencia_segura
    )
    estado["ultima_acao_reexecutavel"] = reexecutavel
    estado["ultima_acao_intent"] = intent
    estado["ultima_acao_params"] = dict(params)
    estado["ultima_acao_origem"] = contrato.origem
    estado["ultima_acao_texto"] = texto_curto
    estado["ultima_acao_confirmada"] = (
        estado.get("ultima_acao_confirmada")
        if mesmo_resultado and (registro_generico or contrato.confirmado is None)
        else contrato.confirmado
    )
    estado["ultima_acao_ok"] = (
        estado.get("ultima_acao_ok")
        if mesmo_resultado and (registro_generico or contrato.ok is None)
        else contrato.ok
    )
    estado["ultima_acao_alvo"] = (
        str(estado.get("ultima_acao_alvo") or "")
        if mesmo_resultado and (registro_generico or not contrato.alvo)
        else contrato.alvo
    )
    estado["ultima_acao_detalhe"] = (
        str(estado.get("ultima_acao_detalhe") or "")
        if mesmo_resultado and (registro_generico or not contrato.detalhe)
        else contrato.detalhe[:300]
    )
    estado["ultima_acao_ts"] = time.time()
    # Fonte canônica atômica: leitores não podem completar campos vazios com
    # pedaços de ações anteriores. Um alvo vazio continua sendo informação
    # válida deste evento, e não uma oportunidade para herdar outro domínio.
    contrato_anterior = (
        dict(estado.get("ultima_acao_contrato") or {})
        if mesmo_resultado else {}
    )
    estado["ultima_acao_contrato"] = {
        "id_solicitacao": (
            str(contrato_anterior.get("id_solicitacao") or "")
            if registro_generico and not contrato.id_solicitacao
            else contrato.id_solicitacao
        ),
        "intent": intent,
        "alvo": str(estado.get("ultima_acao_alvo") or ""),
        "status": status_final,
        "dominio": normalizar_dominio_continuidade(intent=intent),
        "executou": estado.get("ultima_acao_ok"),
        "confirmado": estado.get("ultima_acao_confirmada"),
        "origem": (
            str(contrato_anterior.get("origem") or "")
            if registro_generico and contrato_anterior.get("origem")
            else contrato.origem
        ),
        "evidencia_confirmacao": (
            str(contrato_anterior.get("evidencia_confirmacao") or "")
            if registro_generico and contrato_anterior.get("evidencia_confirmacao")
            else contrato.evidencia_confirmacao
        ),
    }

    # Exclusão e caixa de entrada usam ``pendencia_acao_canonica``. Esta
    # camada registra somente o resultado e limpa estados legados que possam
    # ter vindo de uma sessão anterior; não cria uma segunda pendência.
    if intent in {"CONFIRM_DELETE_ITEM", "CANCEL_DELETE_ITEM"}:
        estado = limpar_pendencia(
            estado,
            motivo=(
                "confirmada"
                if intent == "CONFIRM_DELETE_ITEM" and contrato.executou
                else "cancelada"
            ),
        )
    elif intent in {"CONFIRM_INBOX_DELETE", "CANCEL_INBOX_ACTION"}:
        pendencia_inbox = dict(estado.get("pendencia_atual") or {})
        if str(pendencia_inbox.get("origem") or "") == "caixa_entrada_pessoal":
            estado = limpar_pendencia(
                estado,
                motivo="cancelada" if intent == "CANCEL_INBOX_ACTION" else "confirmada",
            )

    # Ciclo de vida geral da pendência: se a ação aguardada realmente terminou
    # e teve confirmação, a resposta seguinte já pertence a um novo turno. Sem
    # isso, módulos de domínio podem conservar uma escolha antiga e interpretar
    # um agradecimento, uma saudação ou outro assunto como parâmetro da ação.
    pendencia_resolvida = dict(estado.get("pendencia_atual") or {})
    intencao_pendente = str(pendencia_resolvida.get("intencao") or "").strip().upper()
    if (
        pendencia_resolvida.get("status") == "ativa"
        and intencao_pendente
        and intencao_pendente == intent
        and contrato.executou is True
        and contrato.confirmado is True
    ):
        estado = limpar_pendencia(estado, motivo="resolvida_por_execucao")

    # A troca de dominio precisa acontecer no contrato-base, antes de qualquer
    # enriquecimento opcional. Assim uma ação web recente nunca deixa um app
    # anterior (por exemplo, Steam) vencer referências como "fecha isso".
    if resultado_promovivel and intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"}:
        alvo_site = str(params.get("alvo") or params.get("url") or params.get("site") or "").strip()
        if alvo_site:
            estado["ultimo_site_aba"] = alvo_site
            estado["ultimo_alvo"] = alvo_site
        estado["ultimo_app_janela"] = ""
    elif resultado_promovivel and intent in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        alvo_app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
        if alvo_app:
            estado["ultimo_app_janela"] = alvo_app
            estado["ultimo_alvo"] = alvo_app
    elif resultado_promovivel and intent == "ORGANIZAR_DESKTOP":
        esquerda = str(params.get("left") or params.get("esquerda") or "").strip()
        direita = str(params.get("right") or params.get("direita") or "").strip()
        estado["ultimo_layout_janelas"] = {
            "left": esquerda,
            "right": direita,
            "modo": str(params.get("modo") or "").strip(),
        }
        # Uma única janela continua sendo uma referência natural válida para
        # "agora coloca ela na direita". Com duas, o pronome seria ambíguo.
        if bool(esquerda) ^ bool(direita):
            alvo_app = esquerda or direita
            estado["ultimo_app_janela"] = alvo_app
            estado["ultimo_alvo"] = alvo_app
    elif intent in {"IOT_CONTROL", "IOT_STATUS"}:
        alvo_iot = str(params.get("alvo") or params.get("dispositivo") or "").strip()
        if alvo_iot:
            # Uma falha de rede/provedor invalida o resultado, não a entidade
            # explicitamente nomeada. Preservar somente o dispositivo permite
            # que ``deixa ela azul`` continue a mesma lâmpada sem promover a
            # falha inteira a sucesso ou a foco operacional confirmado.
            estado["ultimo_dispositivo_iot"] = alvo_iot
            if resultado_promovivel:
                estado["ultimo_alvo"] = alvo_iot
        ambiente_iot = str(params.get("ambiente") or "").strip()
        if ambiente_iot:
            estado["ultimo_ambiente_iot"] = ambiente_iot

    alvo_acao = str(
        params.get("alvo")
        or params.get("url")
        or params.get("site")
        or params.get("nome_app")
        or params.get("app")
        or ""
    ).strip()
    alvo_corrigido = str(estado.get("alvo_corrigido") or "").strip()
    if (
        resultado_promovivel
        and alvo_acao
        and alvo_corrigido
        and alvo_acao.casefold() != alvo_corrigido.casefold()
    ):
        estado["alvo_corrigido"] = ""
        estado["alvo_corrigido_ts"] = 0.0

    # Todo resultado observado entra na trilha oficial, inclusive falhas. Os
    # seletores de referencia continuam rejeitando status de falha, enquanto o
    # seletor exclusivo de repeticao pode recupera-los com seguranca.
    if intent and (tentativa_observada or resultado_promovivel):
        estado = registrar_evento_continuidade(
            estado,
            evento="acao",
            intent=intent,
            alvo=contrato.alvo,
            texto=texto_curto,
            params=params,
            status=status_final,
            origem=contrato.origem,
            ttl_s=900.0,
            reexecutavel=reexecutavel,
        )
    estado["ts"] = time.time()
    return estado


def enriquecer_resultado_execucao_contextual(
    estado_atual: Dict[str, Any] | None,
    resultado: ResultadoAcao | Dict[str, Any] | None,
    texto: str = "",
    executou: bool | None = None,
    *,
    status: str = "",
    normalizar_texto_cb=None,
    atualizar_foco_vivo_cb=None,
) -> Dict[str, Any]:
    """Atualiza alvos recentes e foco vivo depois de uma ação prática."""
    estado = dict(estado_atual or {})
    if not isinstance(resultado, (dict, ResultadoAcao)):
        return estado

    try:
        contrato = normalizar_resultado_acao(
            resultado,
            texto=texto,
            executou=executou,
            status=status,
        )
        if not _resultado_pode_promover_referencia(contrato, contrato.status):
            return estado
        intent = contrato.intent
        params = dict(contrato.params)
        apps_sem_janela_contextual = {
            "microsoft store",
            "store",
            "ms store",
            "loja microsoft",
            "loja",
        }

        def normalizar(valor: str) -> str:
            if callable(normalizar_texto_cb):
                return normalizar_texto_cb(valor)
            return str(valor or "").strip().lower()

        if intent in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
            app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
            if app and normalizar(app) not in apps_sem_janela_contextual:
                estado["ultimo_app_janela"] = app
                estado["ultimo_alvo"] = app
            elif app:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = app
                estado["ultimo_alvo"] = app
        elif intent in {"OPEN_URL", "CLOSE_TAB"}:
            alvo_web = str(params.get("alvo") or params.get("url") or params.get("nome_app") or "").strip()
            if alvo_web:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = alvo_web
        elif intent == "MEDIA_CONTROL":
            estado["ultima_habilidade"] = "midia"
            estado["ultimo_alvo"] = str(params.get("platform") or params.get("acao") or "musica").strip() or "musica"
            estado["ultimo_escopo"] = str(params.get("platform") or "music").strip()
        elif intent in {"PLAYLIST_CREATE", "PLAYLIST_ADD", "PLAYLIST_MOVE"}:
            playlist = str(
                params.get("destino") or params.get("playlist_destino")
                or params.get("nome_playlist") or params.get("playlist")
                or params.get("nome") or ""
            ).strip()
            if playlist:
                estado["ultimo_alvo"] = playlist
                estado["ultima_habilidade"] = "playlist"
                estado["ultimo_escopo"] = "playlist"
        elif intent in {"IOT_CONTROL", "IOT_STATUS"}:
            dispositivo = str(params.get("alvo") or params.get("dispositivo") or "").strip()
            if dispositivo:
                estado["ultimo_dispositivo_iot"] = dispositivo
                estado["ultimo_alvo"] = dispositivo
            estado["ultimo_ambiente_iot"] = str(params.get("ambiente") or estado.get("ultimo_ambiente_iot") or "").strip()
            estado["ultima_habilidade"] = "iot"
            estado["ultimo_escopo"] = "casa"

        alvo_foco = str(
            params.get("alvo")
            or params.get("nome_app")
            or params.get("nome_playlist")
            or params.get("destino")
            or params.get("query")
            or params.get("nome")
            or params.get("nome_arquivo")
            or params.get("arquivo_nome")
            or params.get("item")
            or estado.get("ultimo_alvo")
            or ""
        ).strip()
        habilidade_foco = {
            "APP_OPEN": "janela",
            "CLOSE_APP": "janela",
            "MAXIMIZE_WINDOW": "janela",
            "OPEN_URL": "site",
            "CLOSE_TAB": "site",
            "SITE_ENTER": "site",
            "SEARCH": "pesquisa",
            "WEATHER": "clima",
            "PLAYLIST_CREATE": "playlist",
            "PLAYLIST_PLAY": "playlist",
            "PLAYLIST_ADD": "playlist",
            "PLAYLIST_LIST": "playlist",
            "PLAYLIST_MOVE": "playlist",
            "LAYLAY_PLAYLIST_LIST": "playlist_laylay",
            "LAYLAY_PLAYLIST_PLAY": "playlist_laylay",
            "LAYLAY_PLAYLIST_COPY": "playlist_laylay",
            "MUSIC_SEARCH": "musica",
            "MEDIA_CONTROL": "midia",
            "CREATE_FOLDER": "arquivos",
            "CREATE_FILE": "arquivos",
            "DELETE_ITEM": "arquivos",
            "EMAIL_READ": "email",
            "EMAIL_SYNC": "email",
            "AGENDAR_LEMBRETE": "agenda",
            "AGENDAR_ACAO": "agenda",
            "LISTAR_AGENDAMENTOS": "agenda",
            "BRIEFING_REPEAT": "conversa",
            "LEARNING_QUERY": "memoria",
            "IOT_CONTROL": "iot",
            "IOT_STATUS": "iot",
            "IOT_LIST": "iot",
        }.get(intent, str(estado.get("ultima_habilidade") or "").strip())

        if callable(atualizar_foco_vivo_cb):
            estado = atualizar_foco_vivo_cb(
                estado,
                texto=texto,
                resposta=status or ("executado" if executou else "falhou"),
                intencao=intent,
                alvo=alvo_foco,
                habilidade=habilidade_foco,
            )
    except Exception:
        return estado

    return estado


def registrar_mente_curta(
    estado_atual: Dict[str, Any] | None,
    *,
    texto_usuario: str = "",
    resposta_ia: str = "",
    intencao: str = "",
    alvo: str = "",
    escopo: str = "",
    habilidade: str = "",
    ultimo_topico_conversa: str = "",
    emocao_atual: str = "",
    normalizar_texto_cb=None,
    eh_alvo_site_web_cb=None,
    texto_parece_pergunta_aberta_cb=None,
    registrar_pergunta_aberta_cb=None,
    limpar_pergunta_aberta_cb=None,
    registrar_promessa_conversacional_cb=None,
    atualizar_foco_vivo_cb=None,
    log: Any = print,
) -> Dict[str, Any]:
    """Registra entrada/resposta recentes sem isolar a mente dos callbacks centrais."""
    try:
        estado = dict(estado_atual or {})
    except Exception:
        estado = {}

    texto_usuario = str(texto_usuario or "").strip()
    resposta_ia = str(resposta_ia or "").strip()
    intencao = str(intencao or "").strip()
    alvo = str(alvo or "").strip()
    escopo = str(escopo or "").strip()
    habilidade = str(habilidade or "").strip()

    # Uma contestação explícita reduz a confiança da fala anterior. Ela não
    # pode continuar circulando no prompt como se fosse um fato confirmado.
    texto_contestacao = str(texto_usuario or "").casefold()
    if texto_usuario and re.search(
        r"\b(?:que\s+papo\s+(?:e|é)\s+esse|de\s+onde\s+(?:voce|você)\s+tirou|"
        r"isso\s+(?:e|é)\s+verdade|viajou|nada\s+a\s+ver|tem\s+certeza\s+disso)\b",
        texto_contestacao,
    ):
        anterior_contestada = str(estado.get("ultima_resposta") or "").strip()
        if anterior_contestada:
            estado["alegacao_contestada"] = {
                "texto": anterior_contestada[:500],
                "contestacao": texto_usuario[:300],
                "topico": str(estado.get("assunto_da_fala") or ultimo_topico_conversa or "")[:160],
                "status": "nao_confiavel_ate_verificacao",
                "ts": time.time(),
            }

    assunto_semantico = str(
        ((estado.get("assunto_estruturado_atual") or {}).get("titulo")
         if isinstance(estado.get("assunto_estruturado_atual"), dict) else "")
        or estado.get("assunto_da_fala")
        or ultimo_topico_conversa
        or alvo
        or ""
    ).strip()
    fundamentacao_atual = (
        dict(estado.get("fundamentacao_factual_turno") or {})
        if isinstance(estado.get("fundamentacao_factual_turno"), dict)
        else {}
    )
    fonte_factual = str(fundamentacao_atual.get("fonte") or "").strip() if fundamentacao_atual.get("confiavel") else ""
    estado["registro_semantico"] = registrar_interacao_semantica(
        estado.get("registro_semantico"),
        texto_usuario=texto_usuario,
        resposta_laylay=resposta_ia,
        assunto=assunto_semantico,
        # A rota não é fonte. Somente a fundamentação fechada do turno é.
        fonte_resposta=fonte_factual,
    )

    if texto_usuario:
        try:
            from mente_laylay.cognicao.conversa_sobre_capacidades import (
                extrair_registro_capacidade_futura,
            )

            registro_capacidade = extrair_registro_capacidade_futura(texto_usuario)
            if registro_capacidade:
                registro_capacidade["ts"] = time.time()
                estado["capacidade_futura"] = registro_capacidade
        except Exception:
            pass

    if texto_usuario:
        estado = registrar_feedback_musical_conversacional(estado, texto_usuario)
        estado["ultima_entrada_ts"] = time.time()
        estado["consciencia_temporal"] = atualizar_consciencia_temporal(
            estado.get("consciencia_temporal"),
            texto_usuario,
            resposta_ia=resposta_ia,
        )
        estado["ultima_entrada"] = texto_usuario
        entradas = list(estado.get("ultimas_entradas") or [])
        entradas.append(texto_usuario[:160])
        estado["ultimas_entradas"] = entradas[-8:]
    if resposta_ia:
        conteudo_anterior_promessa = str(
            estado.get("ultima_opiniao") or estado.get("ultima_afirmacao") or ""
        ).strip()
        estado["ultima_resposta"] = resposta_ia[:180]
        estado = registrar_continuidade_da_fala(
            estado,
            resposta_ia,
            texto_usuario=texto_usuario,
            assunto=alvo or ultimo_topico_conversa,
            origem=habilidade or intencao,
            emocao=emocao_atual,
        )
        estado = registrar_oferta_pendente(
            estado,
            resposta_ia,
            alvo_contexto=alvo or ultimo_topico_conversa or assunto_semantico,
        )
        # Esclarecimentos operacionais também pertencem à continuidade geral.
        # Sem esta pendência, uma resposta curta como "Love Me" seria entregue
        # à conversa comum em vez de completar o MUSIC_SEARCH iniciado antes.
        if (
            intencao.upper() == "MUSIC_SEARCH"
            and not alvo
            and re.search(
                r"\b(?:me\s+diz|fala|qual)\b[^.!?]{0,50}\b(?:m[uú]sica|faixa|som)\b|"
                r"\btocar\s+o\s+qu[eê]\b",
                resposta_ia.casefold(),
            )
        ):
            estado = registrar_pendencia(
                estado,
                criar_pendencia(
                    origem="esclarecimento_operacional",
                    tipo="esclarecimento",
                    dominio="musica",
                    conteudo=resposta_ia,
                    resposta_esperada="nome da música, artista ou estilo",
                    intencao="MUSIC_SEARCH",
                    ttl_s=180.0,
                    foi_falada=True,
                ),
            )
        try:
            if callable(texto_parece_pergunta_aberta_cb) and texto_parece_pergunta_aberta_cb(resposta_ia):
                if callable(registrar_pergunta_aberta_cb):
                    estado = registrar_pergunta_aberta_cb(
                        estado,
                        resposta_ia,
                        # O assunto explicito da conversa vence rotulos genericos
                        # como "conversa" e alvos operacionais mais antigos.
                        topico=alvo or ultimo_topico_conversa or habilidade or intencao,
                        origem=habilidade or intencao or "conversa",
                    )
                    log(f"🧠 [PERGUNTA ABERTA] registrada: {estado.get('pergunta_aberta_texto', '')[:90]}")
            elif callable(limpar_pergunta_aberta_cb):
                estado = limpar_pergunta_aberta_cb(estado)
        except Exception as e:
            log(f"⚠️ [PERGUNTA ABERTA] falha ao atualizar memória: {e}")
        try:
            if callable(registrar_promessa_conversacional_cb):
                estado = registrar_promessa_conversacional_cb(
                    estado,
                    resposta_ia,
                    alvo=alvo or estado.get("ultimo_alvo") or "",
                    conteudo=(
                        estado.get("ultima_opiniao")
                        or estado.get("ultima_afirmacao")
                        or conteudo_anterior_promessa
                        or ""
                    ),
                )
        except Exception as e:
            log(f"⚠️ [PROMESSA] falha ao registrar promessa conversacional: {e}")
    if intencao:
        estado["ultima_intencao"] = intencao
    if alvo:
        estado["ultimo_alvo"] = alvo
        alvo_norm = normalizar_texto_cb(alvo) if callable(normalizar_texto_cb) else alvo.lower()
        if any(x in alvo_norm for x in ["steam", "opera", "chrome", "edge", "vscode", "vs code", "visual studio code"]):
            estado["ultimo_app_janela"] = alvo
        if callable(eh_alvo_site_web_cb) and eh_alvo_site_web_cb(alvo_norm):
            estado["ultimo_site_aba"] = alvo
        if habilidade.lower() in {"arquivo", "arquivos", "pasta", "sistema"} or intencao.upper() in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"}:
            alvo_limpo = str(alvo or "").strip()
            if alvo_limpo:
                import os
                if habilidade.lower() == "arquivo":
                    estado["ultimo_arquivo"] = os.path.basename(alvo_limpo)
                    estado["ultimo_caminho_arquivo"] = alvo_limpo
                elif habilidade.lower() == "pasta":
                    estado["ultima_pasta"] = alvo_limpo
                elif "." in os.path.basename(alvo_limpo):
                    estado["ultimo_arquivo"] = os.path.basename(alvo_limpo)
                    estado["ultimo_caminho_arquivo"] = alvo_limpo
                else:
                    estado["ultima_pasta"] = alvo_limpo
    if escopo:
        estado["ultimo_escopo"] = escopo
    if habilidade:
        estado["ultima_habilidade"] = habilidade
    if callable(atualizar_foco_vivo_cb):
        estado = atualizar_foco_vivo_cb(
            estado,
            texto=texto_usuario,
            resposta=resposta_ia,
            intencao=intencao,
            alvo=alvo,
            habilidade=habilidade,
            escopo=escopo,
        )
    estado["ts"] = time.time()
    return estado


from mente_laylay.memoria_mental.foco_contexto import (
    atualizar_foco_vivo,
    extrair_refino_contexto_mental,
    extrair_topico_foco_vivo,
    foco_por_dominio,
    foco_vivo_atual,
    inferir_tipo_foco_vivo,
)

from mente_laylay.memoria_mental.compatibilidade_contexto import (
    contexto_mental_ativo,
    contexto_musical_ativo,
    fluxo_prioritario_da_ia,
    resolver_repeticao_ultima_acao,
    texto_depende_de_contexto,
    texto_pede_repeticao_curta,
)
