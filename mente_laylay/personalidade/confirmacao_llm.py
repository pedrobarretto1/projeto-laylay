"""Personalização segura e opcional das confirmações operacionais.

O executor continua sendo a única fonte da verdade. A LLM recebe um contrato
já concluído e pode somente reescrever sua confirmação. Uma primeira redação
inválida recebe uma correção autoral; só indisponibilidade ou duas violações do
contrato devolvem a fala determinística original.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from mente_laylay.cognicao.contratos_turno import ComplementoConversacionalTurno
from mente_laylay.emocoes.contrato_causal import evento_pode_alterar_estado
from mente_laylay.cognicao.preferencia_humor import humor_bloqueado_por_preferencia
from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto_basico as _normalizar,
)
from mente_laylay.integracao.llm_http import eh_estado_tecnico_llm
from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao,
    STATUS_RESULTADO_JA_SATISFEITO,
)
from mente_laylay.personalidade.prompt_voz_unica import IDENTIDADE_VOZ_LAYLAY
from mente_laylay.personalidade.antirrepeticao import repeticao_estrutural
from mente_laylay.personalidade.guarda_ataque_pessoal import contem_ataque_pessoal


EMOCOES_PERMITIDAS = frozenset({
    "calma", "alegre", "debochada", "envergonhada", "surpresa",
    "triste", "irritada", "brava", "acalmando-se",
})

_PARAMETROS_AUTORIA = frozenset({
    "acao", "alvo", "cor", "nome_app", "nome", "nome_arquivo",
    "nome_playlist", "query", "site", "url", "brilho", "temperatura", "volume",
})

# Consultas e listagens carregam dados que uma paráfrase poderia apagar.
INTENTS_INFORMATIVOS = frozenset({
    # Uma releitura de PWM não mede locomoção. Conservar literalmente o
    # alcance factual evita uma paráfrase "andei" sem sensor de deslocamento.
    "CORPO_MOVER", "CORPO_PARAR",
    "IOT_STATUS", "PLAYLIST_LIST", "LIST_PLAYLIST_CONTENT", "READ_EMAILS",
    "READ_URGENT_EMAILS", "LER_EMAILS", "LER_EMAILS_URGENTES",
    "WEATHER", "CLIMA", "LISTAR_AGENDAMENTOS", "LER_NOTIFICACOES",
    "NOTIFICATIONS",
    "LIST_TABS", "LIST_WINDOWS",
    "FILE_SEARCH", "FILE_READ", "SEARCH",
    # A confirmação não recebe o tipo original no novo turno. Reescrevê-la
    # fazia a LLM chamar uma pasta de "arquivo"; preserve a fala factual.
    "CONFIRM_DELETE_ITEM",
})

RAIZES_POR_STATUS: dict[str, tuple[str, ...]] = {
    "ligado": ("lig",),
    "desligado": ("deslig",),
    "cor_ajustada": ("rox", "azul", "verd", "amarel", "vermelh", "cor"),
    "branco_ajustado": ("branc", "luz"),
    "brilho_ajustado": ("brilh", "luz"),
    "volume_ajustado": ("volume", "som"),
    "volume_aumentado": ("aument", "subi", "volume", "som"),
    "volume_baixado": ("baix", "diminu", "volume", "som"),
    "volume_mudo": ("mudo", "silenci", "som"),
    "volume_desmutado": ("mudo", "som", "voz"),
    "midia_pause": ("paus",),
    "midia_play": ("retom", "play", "volt"),
    "midia_next": ("proxim", "troque", "passei"),
    "midia_prev": ("anterior", "voltei"),
    "midia_replay": ("recomec", "inicio", "começo"),
    "midia_skip_ad": ("anuncio", "pulei"),
    "pasta_criada": ("pasta", "criei", "criad"),
    "subpasta_criada": ("pasta", "criei", "criad"),
    "arquivo_criado": ("arquivo", "criei", "criad"),
    "conteudo_atualizado": ("escrevi", "atualiz", "texto"),
    "conteudo_acrescentado": ("acrescente", "adicione", "nova linha"),
    "item_deletado": ("apague", "remov", "lixeira"),
    "movido_para_lixeira": ("lixeira", "mov", "enviei"),
    "item_movido_para_pasta": ("mov", "mudei"),
    "app_aberto": ("abri", "aberto"),
    "app_iniciado_focado": ("iniciei", "abri", "nova", "foco", "frente"),
    "app_focado": ("foco", "frente", "trouxe", "puxei"),
    "ja_aberto_focado": ("aberto", "foco", "frente"),
    "site_ja_aberto_focado": ("aberto", "foco", "frente", "aba"),
    "ja_estava_ligado": ("ligad", "funcionando"),
    "ja_estava_desligado": ("desligad", "quiet"),
    "app_fechado": ("feche", "encerr"),
    "site_aberto": ("abri", "aberto", "navegador"),
    "url_aberta": ("abri", "aberto", "pagina"),
    "aba_fechada": ("aba", "feche"),
    "janela_maximizada": ("maximiz", "tela"),
    "musica_aberta": ("toc", "musica", "som"),
    "musica_reproduzindo": ("toc", "reprodu", "player", "som"),
    "musica_enviada_sem_confirmacao": ("abri", "enviei", "player", "confirm"),
    "playlist_aberta": ("playlist", "faixa", "toc"),
    "playlist_enviada_sem_confirmacao": ("playlist", "faixa", "fila", "confirm"),
    # O substantivo ``playlist`` sozinho não prova exclusão: uma listagem
    # antiga também o contém e já chegou a ser repetida depois de apagar.
    "playlist_deletada": ("apague", "remov", "exclu", "deletei"),
    "playlist_musica_adicionada": ("adicione", "salv", "guarde", "foi pra"),
    "acao_agendada": ("agend", "lembrete"),
    "lembrete_agendado": ("agend", "lembrete"),
    "lembrete_ja_agendado": ("ja", "agend", "marcad", "duplic", "mantive"),
    "agendamento_cancelado": ("cancel", "agenda"),
    "indisponivel": ("nao respondeu", "indisponivel", "offline"),
    "nao_encontrado": ("nao encontrei", "nao achei", "nao apareceu"),
    "falha_execucao": ("nao consegui", "falhou", "nao confirmou", "nao foi concluid", "nao foi realizad", "nao foi executad", "nao foi possivel"),
    "app_aberto_sem_foco": ("nao consegui", "foco", "frente"),
}


@dataclass(frozen=True)
class ConfirmacaoPersonalizada:
    fala: str
    emocao: str
    nivel: int
    usada_llm: bool = False
    motivo_fallback: str = ""


def _com_motivo_fallback(
    fallback: ConfirmacaoPersonalizada,
    motivo: str,
) -> ConfirmacaoPersonalizada:
    return ConfirmacaoPersonalizada(
        fallback.fala,
        fallback.emocao,
        fallback.nivel,
        usada_llm=False,
        motivo_fallback=str(motivo or "fallback_local"),
    )


def _extrair_json(resposta: Any) -> dict[str, Any]:
    texto = str(resposta or "").strip()
    if not texto or eh_estado_tecnico_llm(texto):
        return {}
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE)
    try:
        dados = json.loads(texto)
        return dados if isinstance(dados, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        inicio, fim = texto.find("{"), texto.rfind("}")
        if inicio < 0 or fim <= inicio:
            return {}
        try:
            dados = json.loads(texto[inicio : fim + 1])
            return dados if isinstance(dados, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}


def _extrair_dados_autoria(
    resposta: Any,
    *,
    resultado: ResultadoAcao,
    fallback: ConfirmacaoPersonalizada,
) -> dict[str, Any]:
    """Aceita JSON legado ou fala pura sem devolver autoridade ao modelo."""
    dados = _extrair_json(resposta)
    if dados:
        return dados
    texto = re.sub(r"\s+", " ", str(resposta or "")).strip()
    if not texto or eh_estado_tecnico_llm(texto):
        return {}
    texto = re.sub(r"^```(?:text|txt)?\s*|\s*```$", "", texto, flags=re.IGNORECASE).strip()
    # Estrutura quebrada não pode ser pronunciada como conversa. Fala pura é
    # segura porque status e alvo vêm do receipt, não de campos reescritos.
    if texto.startswith(("{", "[")) or re.search(
        r'(?i)["\']?(?:fala|status|alvo|emocao|nível|nivel)["\']?\s*:',
        texto,
    ):
        return {}
    return {
        "fala": texto,
        "status": resultado.status,
        "alvo": resultado.alvo,
        "emocao": fallback.emocao,
        "nivel": fallback.nivel,
    }


def _ativada() -> bool:
    valor = _normalizar(os.environ.get("LAYLAY_CONFIRMACOES_LLM", "1"))
    return valor not in {"0", "false", "nao", "off", "desativado"}


def _timeout_autoria_operacional() -> float:
    """Dá tempo para o primeiro carregamento local sem prender o turno indefinidamente."""
    try:
        valor = float(os.environ.get("LAYLAY_AUTORIA_OPERACIONAL_TIMEOUT", "8.0"))
    except (TypeError, ValueError):
        valor = 8.0
    return max(3.0, min(15.0, valor))


def _elegivel(resultado: ResultadoAcao, classe: str, fala: str) -> bool:
    if not _ativada() or classe not in {"sucesso", "sem_acao", "falha", "incerto"}:
        return False
    if classe in {"sucesso", "sem_acao"} and resultado.confirmado is not True:
        return False
    if classe == "falha" and not (
        resultado.executou is False or resultado.confirmado is False
    ):
        return False
    if classe == "incerto" and not (
        resultado.executou is True and resultado.confirmado is None
    ):
        return False
    if resultado.intent in INTENTS_INFORMATIVOS:
        return False
    # Respostas longas geralmente contêm listagens ou dados, não uma simples
    # confirmação; nelas a preservação literal vale mais que a variação.
    return 2 <= len(str(fala or "").split()) <= 42


def _tokens_concretos(resultado: ResultadoAcao) -> set[str]:
    valores = [resultado.alvo]
    for chave in (
        "cor", "nome_app", "nome", "nome_arquivo", "nome_playlist", "query",
        "site", "url", "brilho", "temperatura", "volume",
    ):
        valor = resultado.params.get(chave)
        if isinstance(valor, (str, int, float)):
            valores.append(str(valor))
    ignorar = {"isso", "acao", "pedido", "item", "uma", "para", "com", "que"}
    return {
        token for valor in valores for token in re.findall(r"[a-z0-9]+", _normalizar(valor))
        if len(token) >= 3 and token not in ignorar
    }


def _motivo_contrato_invalido(
    fala: str,
    *,
    resultado: ResultadoAcao,
    classe: str,
    status_declarado: str,
    alvo_declarado: str,
) -> str:
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    base = _normalizar(texto)
    if not 3 <= len(texto) <= 260:
        return "tamanho_invalido"
    if texto.count("?") > 0:
        return "pergunta_na_confirmacao"
    if contem_ataque_pessoal(texto):
        return "ataque_pessoal"
    # Confirmar um toggle prova a operação, sem fornecer a direção final.
    # Estado ligado/desligado exige um receipt que represente esse estado;
    # os parâmetros atuais de alternância não transportam essa observação.
    if _normalizar(resultado.status) == "midia_repeat_toggle" and re.search(
        r"\b(?:(?:des)?ativ(?:ad[oa]s?|ei|ou|o|a|ar)|"
        r"(?:des)?lig(?:ad[oa]s?|uei|ou|o|a|ar))\b", base,
    ):
        return "estado_final_do_toggle_nao_evidenciado"
    frases = [
        parte.strip()
        for parte in re.split(r"(?<=[.!?])\s+", texto)
        if parte.strip()
    ]
    if len(frases) > 2:
        return "fala_operacional_prolixa"
    # Identificadores diagnósticos não viram fatos só por terem sido enviados
    # ao reparo. Nomes legítimos continuam permitidos quando constam do alvo,
    # dos parâmetros factuais publicados ou do detalhe do executor.
    identificadores = lambda valor: {
        item.casefold() for item in re.findall(r"\b\w*_\w+\b", str(valor or ""))
    }
    fontes_factuais = [resultado.alvo, resultado.detalhe, *[
        str(valor) for chave, valor in resultado.params.items()
        if chave in _PARAMETROS_AUTORIA and isinstance(valor, (str, int, float, bool))
    ]]
    identificadores_permitidos = set().union(*[
        identificadores(fonte) for fonte in fontes_factuais
    ])
    if not identificadores(texto).issubset(identificadores_permitidos):
        return "diagnostico_sem_evidencia"
    if re.search(
        r"\bn[aã]o\s+(?:fale|chame|toque|olhe|volte|v[aá]\s+embora)\b",
        base,
    ):
        # Uma confirmação pode ter humor, mas não pode anexar ordens aleatórias
        # ao usuário. Esse padrão apareceu numa simples consulta de caminho.
        return "instrucao_alheia_ao_resultado"
    # Resultado operacional não é espaço para poesia desconectada. Além de
    # esconder a informação útil, construções desse tipo vinham acrescentando
    # celular, pão, frio e outros cenários que o executor nunca observou.
    if re.search(r"\bcomo se\b", base):
        return "metafora_operacional_nao_ancorada"
    # Alguns modelos devolvem no campo ``status`` a classe semântica que
    # acabaram de receber (``sem_acao``/``sucesso``/``falha``), em vez do
    # status específico do executor. Isso não é uma contradição: a segurança
    # real está na fala, validada logo abaixo pelas raízes do estado, pelo alvo
    # concreto e pela semântica da classe. Aceitar a classe evita jogar fora
    # uma confirmação correta por causa de metadado redundante.
    status_recebido = _normalizar(status_declarado)
    status_permitidos = {_normalizar(resultado.status), _normalizar(classe)}
    if status_recebido not in status_permitidos:
        return "status_divergente"
    if resultado.alvo and _normalizar(alvo_declarado) != _normalizar(resultado.alvo):
        return "alvo_divergente"
    sinais_falha = re.search(
        r"\b(?:nao consegui|nao fiz|nao executei|falhou|indisponivel|offline|"
        r"nao respondeu|nao encontrei|nao achei|nao apareceu|nao confirmou|"
        r"nao foi (?:concluid[oa]|realizad[oa]|executad[oa]|possivel))\b",
        base,
    )
    sinais_sem_acao = re.search(
        r"\b(?:ja estava|ja esta|nao mexi|nao rep[ei]ti|sem repetir|mantive|"
        r"deixei como|ficou como|nem precisei|nao precisei|nao precisa repetir|"
        r"pra que repetir|para que repetir|"
        r"nao (?:abri|liguei|desliguei|executei|fiz|toquei|mudei|alterei)|"
        r"nao vou (?:abrir|ligar|desligar|executar|fazer))\b",
        base,
    )
    recusa_retrabalho = re.search(
        r"\b(?:n[aã]o vou (?:repetir|refazer|fazer|executar|abrir|ligar|"
        r"desligar|tocar|mexer)|me recuso|recuso o retrabalho)\b",
        base,
    )
    if recusa_retrabalho and not (
        classe == "sem_acao"
        and resultado.executou is False
        and resultado.confirmado is True
        and _normalizar(resultado.status).replace(" ", "_")
        in STATUS_RESULTADO_JA_SATISFEITO
    ):
        return "recusa_sem_redundancia_observada"
    if classe == "sucesso" and sinais_falha:
        return "sucesso_negado"
    if classe == "sem_acao" and not sinais_sem_acao:
        return "nao_acao_ambigua"
    if classe == "falha" and not sinais_falha:
        return "falha_ocultada"
    if classe == "falha" and re.search(
        r"\b(?:ficou|era|seria)\s+(?:so\s+)?(?:como\s+)?uma\s+possibilidade\b|"
        r"\bnao\s+tive\s+coragem\s+de\s+imaginar\b",
        base,
    ):
        # Um comando explícito que falhou continua sendo um comando tentado.
        # Chamá-lo de hipótese apaga a modalidade real do turno.
        return "falha_rebaixada_a_hipotese"
    sinais_incerteza = re.search(
        r"\b(?:nao confirmou|sem confirmacao|nao consegui confirmar|"
        r"nao posso confirmar|reproducao nao confirmada|audio nao confirmado)\b",
        base,
    )
    if classe == "incerto" and not sinais_incerteza:
        return "incerteza_ocultada"
    if classe != "falha" and re.search(
        r"\b(?:talvez|acho que|vou tentar|posso tentar|quer que eu|ainda vou|"
        r"deixa eu (?:ver|tentar)|se voce quiser|se quiser)\b",
        base,
    ):
        return "promessa_ou_nova_oferta"
    if _normalizar(resultado.status) == "agendamento_cancelado" and re.search(
        r"\b(?:n[aã]o\s+esque[cç]a|a\s+gente\s+(?:est[aá]|t[aá])\s+no\s+aguardo|"
        r"vou\s+te\s+lembrar|ainda\s+(?:precisa|tem\s+que))\b",
        base,
    ):
        # Cancelar encerra a obrigação da Laylay. Uma tirada não pode anexar
        # outro lembrete, cobrança ou promessa à confirmação já concluída.
        return "cancelamento_reintroduziu_obrigacao"

    raizes = RAIZES_POR_STATUS.get(_normalizar(resultado.status), ())
    if raizes and not any(raiz in base for raiz in raizes):
        return "estado_observado_ausente"
    concretos = _tokens_concretos(resultado)
    if concretos and not any(token in base for token in concretos):
        return "alvo_concreto_ausente"
    # Identificadores alfanuméricos são fatos indivisíveis: aceitar apenas
    # outro token do mesmo alvo permitia à LLM trocar C418 por C410 enquanto
    # preservava palavras como "Sweden". Todo identificador com dígito precisa
    # sobreviver literalmente à personalização.
    identificadores = {token for token in concretos if any(ch.isdigit() for ch in token)}
    if identificadores and not all(token in base for token in identificadores):
        return "identificador_concreto_divergente"
    verdade_observada = _normalizar(" ".join((
        resultado.status,
        resultado.alvo,
        resultado.detalhe,
        json.dumps(resultado.params, ensure_ascii=False, default=str),
        json.dumps(resultado.contexto, ensure_ascii=False, default=str),
    )))
    intent_observada = _normalizar(resultado.intent)
    if intent_observada in {"close_app", "close_tab"} and re.search(
        r"\b(?:abrir|abriu|abrindo)\b",
        base,
    ):
        # Fechar algo inexistente não é uma falha de abertura. Essa troca de
        # verbo apareceu no roteiro e contradiz a ação que realmente falhou.
        return "verbo_operacional_divergente"
    anos_fala = set(re.findall(r"\b(?:19|20)\d{2}\b", base))
    if anos_fala and not anos_fala.issubset(
        set(re.findall(r"\b(?:19|20)\d{2}\b", verdade_observada))
    ):
        # Humor pode variar; data factual não observada, não. Evita anexar um
        # ano de filme inventado à simples confirmação de fechar uma aba.
        return "detalhe_temporal_nao_evidenciado"
    if (
        intent_observada
        in {"agendar_lembrete", "cancelar_agendamento", "listar_agendamentos"}
        or _normalizar(resultado.status).startswith(("agendamento_", "lembrete_"))
    ):
        marcadores_tempo_fala = set(re.findall(
            r"\b(?:hoje|amanha|amanhã|ontem)\b", base,
        ))
        marcadores_tempo_observados = set(re.findall(
            r"\b(?:hoje|amanha|amanhã|ontem)\b", verdade_observada,
        ))
        if not marcadores_tempo_fala.issubset(marcadores_tempo_observados):
            return "detalhe_temporal_nao_evidenciado"
    if (
        _normalizar(resultado.status) == "playlist_aberta"
        and re.search(
            r"\b(?:esta|está|ta|tá)\s+(?:sendo\s+)?ouvid[oa]\b|"
            r"\bmundo\s+inteiro\b.*\bouvir\b",
            base,
        )
    ):
        # Abrir a playlist confirma a navegação/entrega ao player. Não prova
        # que o áudio está audível para o usuário.
        return "audio_nao_observado"
    # "A playlist está vazia" é uma alegação verificável, não uma tirada. A
    # autoria só pode usá-la quando essa informação veio no contrato factual.
    if re.search(r"\bvazi[ao]s?\b", base) and "vazi" not in verdade_observada:
        return "estado_operacional_nao_evidenciado"
    if re.search(
        r"\b(?:dei|fiz|foram|houve)\s+(?:\w+\s+){0,2}(?:tentativas?|vezes?)\b",
        base,
    ) and not re.search(r"\b(?:tentativ|repet|vezes?)\b", verdade_observada):
        return "estado_operacional_nao_evidenciado"
    if re.search(r"\b(?:apetite|estilo)\b", base) and not re.search(
        r"\b(?:apetite|estilo)\b",
        verdade_observada,
    ):
        # Impede que contexto musical ou metáforas corporais sejam enxertados
        # numa confirmação de IoT/arquivo/janela sem qualquer evidência.
        return "contexto_alheio_ao_resultado"
    primeira_frase = re.split(r"(?<=[.!?])\s+", texto, maxsplit=1)[0]
    primeira_base = _normalizar(primeira_frase)
    if raizes and not any(raiz in primeira_base for raiz in raizes):
        return "verdade_operacional_nao_abre_fala"
    if concretos and not any(token in primeira_base for token in concretos):
        return "alvo_operacional_nao_abre_fala"
    return ""


def _fala_preserva_contrato(
    fala: str,
    *,
    resultado: ResultadoAcao,
    classe: str,
    status_declarado: str,
    alvo_declarado: str,
) -> bool:
    return not _motivo_contrato_invalido(
        fala,
        resultado=resultado,
        classe=classe,
        status_declarado=status_declarado,
        alvo_declarado=alvo_declarado,
    )


def _remover_pergunta_opcional(fala: str) -> str:
    """Conserva afirmações completas e remove só perguntas anexadas ao final."""
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    partes = [
        parte.strip()
        for parte in re.split(r"(?<=[.!?])\s+", texto)
        if parte.strip()
    ]
    afirmacoes = [parte for parte in partes if "?" not in parte]
    if afirmacoes:
        return " ".join(afirmacoes).strip()
    # Às vezes a pergunta vem grudada à confirmação por vírgula ou travessão.
    # Preserve apenas o trecho anterior ao último separador, desde que ele já
    # seja uma afirmação completa; a validação factual ainda roda em seguida.
    prefixos = [
        trecho.strip()
        for trecho in re.split(r"\s+(?:—|–|-)|[,;]\s+", texto)
        if trecho.strip()
    ]
    if len(prefixos) >= 2:
        candidato = " ".join(prefixos[:-1]).strip()
        return candidato.rstrip(" ,;—–-") + "."
    return ""


def _variar_abertura_repetida(fala: str, falas_anteriores: Any) -> str:
    """Inverte cláusulas independentes quando a LLM repete a mesma abertura."""
    atual = re.sub(r"\s+", " ", str(fala or "")).strip()
    anteriores = (
        list(falas_anteriores or [])
        if isinstance(falas_anteriores, (list, tuple))
        else [falas_anteriores]
    )
    anteriores = [
        re.sub(r"\s+", " ", str(item or "")).strip()
        for item in anteriores
        if str(item or "").strip()
    ]
    if not atual or not anteriores:
        return atual
    palavras_atual = re.findall(r"[a-z0-9]+", _normalizar(atual))[:5]
    aberturas_anteriores = {
        tuple(re.findall(r"[a-z0-9]+", _normalizar(item))[:5])
        for item in anteriores
    }
    if len(palavras_atual) < 4 or tuple(palavras_atual) not in aberturas_anteriores:
        return atual

    partes = [
        parte.strip(" ,;.!—–-")
        for parte in re.split(r"(?<=[.;!])\s+|[,;]\s+|\s+[—–-]\s+", atual)
        if parte.strip(" ,;.!—–-")
    ]
    indice_recusa = next(
        (
            indice for indice, parte in enumerate(partes[1:], start=1)
            if re.match(
                r"^(?:não|nao|nem|mantive|deixei|recusei)\b",
                parte,
                flags=re.IGNORECASE,
            )
        ),
        -1,
    )
    if len(partes) < 2 or indice_recusa < 1:
        return atual

    def montar(ordem: list[int]) -> str:
        trechos = []
        for indice in ordem:
            trecho = partes[indice].strip()
            if trecho:
                trechos.append(trecho[0].upper() + trecho[1:])
        return ". ".join(trechos).rstrip(" .") + "."

    restantes = [
        indice for indice in range(len(partes))
        if indice not in {0, indice_recusa}
    ]
    candidatos = [
        montar([indice_recusa, 0, *restantes]),
    ]
    # Se houver uma tirada independente escrita pela própria LLM, ela fornece
    # uma terceira estrutura possível sem introduzir uma frase local pronta.
    if restantes and not re.match(
        r"^(?:porque|pois|que|e|mas|só|so)\b",
        partes[restantes[0]],
        flags=re.IGNORECASE,
    ):
        candidatos.append(montar([restantes[0], indice_recusa, 0, *restantes[1:]]))

    for candidato in candidatos:
        abertura = tuple(re.findall(r"[a-z0-9]+", _normalizar(candidato))[:5])
        if abertura not in aberturas_anteriores:
            return candidato
    return atual


def _abertura_ja_usada(fala: str, falas_anteriores: Any) -> bool:
    atual = tuple(re.findall(r"[a-z0-9]+", _normalizar(fala))[:5])
    if len(atual) < 4:
        return False
    return any(
        atual == tuple(re.findall(r"[a-z0-9]+", _normalizar(item))[:5])
        for item in list(falas_anteriores or [])
        if str(item or "").strip()
    )


def _reaproveitou_contexto_antigo(
    fala: str,
    *,
    falas_anteriores: Any,
    fala_segura: str,
) -> bool:
    """Detecta enxerto literal de um turno antigo numa confirmação nova.

    A repetição de termos operacionais curtos é normal. O problema é copiar um
    trecho longo de uma fala anterior que não pertence à confirmação factual
    atual, como anexar uma consulta antiga de pessoas ao resultado da agenda.
    """
    atual = _normalizar(fala)
    segura = _normalizar(fala_segura)
    tokens_seguros = set(re.findall(r"[a-z0-9]+", segura))
    anteriores = (
        list(falas_anteriores or [])
        if isinstance(falas_anteriores, (list, tuple))
        else [falas_anteriores]
    )
    for anterior in anteriores:
        tokens = re.findall(r"[a-z0-9]+", _normalizar(anterior))
        if len(tokens) < 7:
            continue
        # Sete palavras reduzem falsos positivos de expressões inevitáveis
        # ("já está aberto e em foco") e ainda capturam contaminações inteiras.
        for indice in range(0, len(tokens) - 6):
            tokens_fragmento = tokens[indice : indice + 7]
            fragmento = " ".join(tokens_fragmento)
            # Artigos ou flexões pequenas podem fazer a confirmação nova
            # repetir o mesmo fato obrigatório com outra superfície. Se quase
            # todo o fragmento já pertence à fala segura, não é contaminação.
            if len(set(tokens_fragmento) & tokens_seguros) >= 5:
                continue
            if fragmento in atual and fragmento not in segura:
                return True
    return False


def personalizar_confirmacao_llm(
    resultado: ResultadoAcao,
    fala_segura: str,
    *,
    classe: str,
    emocao: str,
    nivel: int,
    enviar_mensagem: Callable[..., Any] | None,
    contexto: Mapping[str, Any] | None = None,
) -> ConfirmacaoPersonalizada:
    """Tenta uma paráfrase curta; em qualquer dúvida conserva a fala segura."""
    fallback = ConfirmacaoPersonalizada(
        fala=str(fala_segura or "").strip(),
        emocao=str(emocao or "calma"),
        nivel=max(1, min(3, int(nivel or 1))),
    )
    retrato = dict(contexto or {})
    if humor_bloqueado_por_preferencia(retrato):
        return fallback
    # Durante jogo, latência e uso de hardware vencem variedade: a fala local
    # curta continua sendo o caminho oficial.
    if bool(retrato.get("modo_jogo_ativo")):
        return _com_motivo_fallback(fallback, "modo_jogo_fala_local")
    if not callable(enviar_mensagem):
        return _com_motivo_fallback(fallback, "modelo_sem_callback")
    if not _elegivel(resultado, classe, fallback.fala):
        return _com_motivo_fallback(fallback, "resultado_nao_elegivel")

    evento = dict(retrato.get("avaliacao_evento") or {})
    evento_da_ocorrencia = bool(
        resultado.origem == "executor"
        and resultado.id_solicitacao
        and evento.get("origem") == "resultado_operacional"
        and str(evento.get("evidencia_ref") or "") == resultado.id_solicitacao
        and _normalizar(evento.get("alvo")) == _normalizar(resultado.alvo)
        and evento_pode_alterar_estado(evento)
    )
    recusa_retrabalho_confirmada = bool(
        evento_da_ocorrencia
        and classe == "sem_acao"
        and resultado.executou is False
        and resultado.confirmado is True
        and _normalizar(resultado.status).replace(" ", "_")
        in STATUS_RESULTADO_JA_SATISFEITO
        and evento.get("arco") == "bronca_brincalhona"
        and evento.get("responsabilidade") == "usuario"
        and float(evento.get("confianca") or 0.0) >= 0.90
    )
    reacao_causal = {
        chave: evento.get(chave)
        for chave in (
            "responsabilidade", "emocao", "arco", "permite_expressao",
        )
        if chave in evento
    }
    if "nivel" in evento:
        reacao_causal["intensidade"] = {
            1: "leve", 2: "moderada", 3: "alta",
        }.get(evento.get("nivel"), "indefinida")
    if not evento_da_ocorrencia:
        reacao_causal["permite_expressao"] = False
    contrato = {
        "intent": resultado.intent,
        "status": resultado.status,
        "alvo": resultado.alvo,
        "params": {
            chave: valor for chave, valor in resultado.params.items()
            if chave in _PARAMETROS_AUTORIA and isinstance(valor, (str, int, float, bool))
        },
        "executou": resultado.executou,
        "confirmado": resultado.confirmado,
        "classe_resultado": classe,
        "fala_segura": fallback.fala,
        # Histórico permanece apenas no verificador local de repetição.
        # Mesmo rotulado "não repetir", seu conteúdo factual contaminava a
        # autoria de outro receipt (clima enxertado em salvar playlist).
        "emocao_atual": str(retrato.get("current_emotion") or fallback.emocao),
        "reacao_causal": reacao_causal,
    }
    regra_reacao = (
        "A reação causal foi validada: inclua na mesma fala uma tirada curta coerente com "
        "responsabilidade e intensidade. No nível 1, seja espirituosa; no nível "
        "2, pode demonstrar deboche ou irritação clara; no nível 3, pode falar com firmeza "
        "e mostrar que está brava com a causa observada. "
        + (
            "Pode dar uma bronca curta no comportamento repetido e recusar o retrabalho redundante. "
            if recusa_retrabalho_confirmada else
            "Não atribua repetição ao usuário nem recuse uma ação que foi executada ou falhou. "
        )
        + "Não dilua a emoção com gentileza artificial. "
        if reacao_causal.get("permite_expressao") else
        "Não atribua culpa nem invente irritação, distração ou provocação. "
    )
    regra_classe = {
        "sucesso": "A ação foi executada e confirmada; não a negue. ",
        "sem_acao": (
            "O estado pedido já estava satisfeito e você conscientemente não repetiu a ação. "
            "A fala precisa declarar inequivocamente, com palavras próprias, que você observou "
            "o estado atual e não realizou uma nova execução redundante. Pode se recusar de "
            "modo carinhoso ou debochado ao retrabalho. Nunca ofereça tentar, repetir ou ver "
            "de novo. Não use frase-modelo: crie a construção e a tirada a partir do contexto. "
        ),
        "falha": (
            "A ação falhou ou não foi confirmada; admita isso com clareza e nunca finja sucesso. "
        ),
        "incerto": (
            "Parte da ação foi observada, mas o resultado final permanece sem confirmação. "
            "Diga exatamente o que ocorreu e o que não foi confirmado; não peça autorização, "
            "não trate como falha total e não afirme conclusão completa. "
        ),
    }.get(classe, "")
    regra_efeito = (
        "O receipt confirma somente a alternância da repetição; não confirma "
        "ativação, desativação ou estado ligado/desligado. Diga que a repetição "
        "foi alternada, sem inventar a direção do estado. "
        if _normalizar(resultado.status) == "midia_repeat_toggle" else ""
    )
    sistema = (
        f"{IDENTIDADE_VOZ_LAYLAY} "
        "Você está falando no cotidiano logo depois do resultado observado de um comando. "
        "Escreva uma única resposta completa na voz da Laylay; não cole uma confirmação técnica "
        "com outra frase pronta. Seja doce, jovem, natural e levemente debochada quando combinar. "
        "Use uma ou duas frases curtas. "
        f"{regra_classe}{regra_efeito}"
        "O contrato é verdade imutável: não altere ação, alvo, estado, números ou certeza; "
        "não prometa nem ofereça outra ação, não use 'se quiser', não faça pergunta e não "
        "acrescente fatos. A primeira frase deve começar pelo resultado e pelo alvo observados; "
        "só depois deles pode vir humor, emoção ou deboche. A personalidade deve continuar na "
        "mesma resposta, mas nunca esconder o status. "
        "Varie naturalmente começando pelo resultado, pela observação ou pela tirada, "
        "sem omitir os fatos obrigatórios. "
        + (
            "A tirada pode brincar somente com a repetição observada do pedido; "
            if recusa_retrabalho_confirmada else
            "A tirada deve mirar somente a causa observada do resultado; "
        )
        + "não invente celular, "
        "gestos, aparência ou ambiente do usuário. Não ataque a inteligência, "
        "aparência, identidade ou valor da pessoa. Não use palavrão nem linguagem ofensiva. "
        f"{regra_reacao}"
        "Responda somente com a fala final, sem JSON, rótulos ou explicações sobre o contrato."
    )
    try:
        resposta = enviar_mensagem(
            [
                {"role": "system", "content": sistema},
                {"role": "user", "content": json.dumps(contrato, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=120,
            modo_rapido=True,
            timeout=_timeout_autoria_operacional(),
            # Esta não é uma tarefa de fundo: é a fala final do comando que o
            # usuário acabou de pedir. Sem prioridade, o cliente local a
            # adiava por detectar a própria interação ainda ativa.
            _prioridade_interativa=True,
            _permitir_durante_interacao=True,
            _tipo_chamada="autoria_operacional",
            _classe_timeout="rapida",
            _contexto_fechado=True,
        )
    except Exception as erro:
        return _com_motivo_fallback(
            fallback, f"erro_chamada_{type(erro).__name__.lower()}",
        )

    def validar_dados(dados_candidatos: dict[str, Any]) -> tuple[str, str]:
        fala_candidata = str(dados_candidatos.get("fala") or "").strip()
        motivo = _motivo_contrato_invalido(
            fala_candidata,
            resultado=resultado,
            classe=classe,
            status_declarado=str(dados_candidatos.get("status") or ""),
            alvo_declarado=str(dados_candidatos.get("alvo") or ""),
        )
        # Números são fatos, não estilo. A fonte é o receipt atual e sua fala
        # factual, nunca o histórico, mesmo quando a redação antiga era válida.
        numeros = lambda texto: set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", texto))
        evidencia = " ".join((fallback.fala, resultado.alvo, resultado.detalhe,
            json.dumps(contrato["params"], ensure_ascii=False)))
        if not motivo and not numeros(fala_candidata).issubset(numeros(evidencia)):
            motivo = "detalhe_numerico_nao_evidenciado"
        historico_contextual = [
            *list(retrato.get("falas_recentes") or [])[-4:],
            str(retrato.get("ultima_resposta") or "").strip(),
        ]
        if not motivo and _reaproveitou_contexto_antigo(
            fala_candidata,
            falas_anteriores=historico_contextual,
            fala_segura=fallback.fala,
        ):
            motivo = "contexto_antigo_reaproveitado"
        if motivo == "pergunta_na_confirmacao":
            fala_sem_pergunta = _remover_pergunta_opcional(fala_candidata)
            if fala_sem_pergunta and "?" not in fala_sem_pergunta:
                # Limpeza textual não concede aprovação: a versão limpa
                # atravessa as mesmas verificações factuais e de histórico.
                return validar_dados({**dados_candidatos, "fala": fala_sem_pergunta})
        return fala_candidata, motivo

    dados = _extrair_dados_autoria(
        resposta,
        resultado=resultado,
        fallback=fallback,
    )
    if not dados and eh_estado_tecnico_llm(resposta):
        return _com_motivo_fallback(fallback, "resposta_tecnica_ou_json_invalido")
    fala, motivo_contrato = validar_dados(dados) if dados else ("", "json_invalido")
    if motivo_contrato:
        # O modelo está disponível, mas a primeira redação violou o contrato.
        # Dê à própria Laylay uma única chance de corrigir a fala antes de cair
        # no texto local. Segurança continua vencendo se a segunda vier errada.
        try:
            resposta_corrigida = enviar_mensagem(
                [
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": json.dumps(contrato, ensure_ascii=False)},
                    {
                        "role": "user",
                        "content": (
                            "Escreva outra fala curta usando somente os fatos do resultado "
                            "fornecido e respeitando todas as restrições de comunicação "
                            "acima. Retorne somente a fala final."
                        ),
                    },
                ],
                _com_tools=False,
                max_tokens=120,
                modo_rapido=True,
                timeout=_timeout_autoria_operacional(),
                _prioridade_interativa=True,
                _permitir_durante_interacao=True,
                _tipo_chamada=(
                    "reparo_json" if motivo_contrato == "json_invalido"
                    else "reparo_factual"
                ),
                _classe_timeout="rapida",
                _contexto_fechado=True,
            )
            dados_corrigidos = _extrair_dados_autoria(
                resposta_corrigida,
                resultado=resultado,
                fallback=fallback,
            )
            fala_corrigida, motivo_corrigido = (
                validar_dados(dados_corrigidos)
                if dados_corrigidos else ("", "json_invalido")
            )
            if not motivo_corrigido:
                dados = dados_corrigidos
                fala = fala_corrigida
                motivo_contrato = ""
        except Exception:
            pass
        if motivo_contrato:
            return _com_motivo_fallback(
                fallback, f"contrato_nao_preservado:{motivo_contrato}",
            )

    historico_variacao = list(retrato.get("falas_recentes") or [])[-4:]
    ultima_variacao = str(retrato.get("ultima_resposta") or "").strip()
    if ultima_variacao and ultima_variacao not in historico_variacao:
        historico_variacao.append(ultima_variacao)
    fala = _variar_abertura_repetida(fala, historico_variacao)
    if (
        _abertura_ja_usada(fala, historico_variacao)
        or repeticao_estrutural(fala, historico_variacao)
    ):
        # Uma única segunda amostra é mais natural que alternar dois moldes
        # mecanicamente. Só ocorre em pedidos realmente repetidos e conserva o
        # mesmo contrato imutável.
        try:
            resposta_variada = enviar_mensagem(
                [
                    {"role": "system", "content": sistema},
                    {"role": "user", "content": json.dumps(contrato, ensure_ascii=False)},
                    {
                        "role": "user",
                        "content": (
                            "A proposta anterior ainda repetiu uma abertura recente: "
                            f"{fala!r}. Gere outra opção realmente diferente, mantendo o "
                            "mesmo contrato e somente a fala final."
                        ),
                    },
                ],
                _com_tools=False,
                max_tokens=120,
                modo_rapido=True,
                timeout=_timeout_autoria_operacional(),
                _prioridade_interativa=True,
                _permitir_durante_interacao=True,
                _tipo_chamada="reparo_comunicacao",
                _classe_timeout="rapida",
            )
            dados_variados = _extrair_dados_autoria(
                resposta_variada,
                resultado=resultado,
                fallback=fallback,
            )
            fala_variada, motivo_variado = (
                validar_dados(dados_variados)
                if dados_variados else ("", "resposta_invalida")
            )
            fala_variada = _variar_abertura_repetida(
                fala_variada, historico_variacao,
            )
            if (
                not motivo_variado
                and not _abertura_ja_usada(fala_variada, historico_variacao)
                and not repeticao_estrutural(fala_variada, historico_variacao)
            ):
                dados = dados_variados
                fala = fala_variada
        except Exception:
            pass

    # A inversão de cláusulas também produz uma nova candidata. Só a versão
    # efetivamente entregue pode receber aprovação do contrato canônico.
    fala_final, motivo_final = validar_dados({**dados, "fala": fala})
    if motivo_final:
        return _com_motivo_fallback(
            fallback, f"contrato_nao_preservado:{motivo_final}",
        )
    fala = fala_final

    emocao_llm = _normalizar(dados.get("emocao"))
    if emocao_llm not in EMOCOES_PERMITIDAS:
        emocao_llm = fallback.emocao
    try:
        nivel_llm = max(1, min(3, int(dados.get("nivel") or fallback.nivel)))
    except (TypeError, ValueError):
        nivel_llm = fallback.nivel
    return ConfirmacaoPersonalizada(fala, emocao_llm, nivel_llm, usada_llm=True)


def personalizar_confirmacao_composta_llm(
    resultados: Sequence[ResultadoAcao],
    fala_segura: str,
    *,
    enviar_mensagem: Callable[..., Any] | None,
    contexto: Mapping[str, Any] | None = None,
    informacoes: Mapping[str, str] | None = None,
    texto_conversacional: str = "",
    avisos_obrigatorios: Sequence[str] = (),
    complemento_conversacional: ComplementoConversacionalTurno | None = None,
) -> ConfirmacaoPersonalizada:
    """Uma autoria para vários receipts; cada trecho mantém sua certeza própria.

    No modo operacional, trechos literais vinculam a fala inteira aos receipts.
    No modo misto, a autora escreve cada trecho uma única vez; o host vincula
    sua ordem aos receipts e acrescenta avisos imutáveis na publicação única.
    Condições cobertas usam escolhas de realização do owner, não prosa livre.
    """
    from mente_laylay.cognicao.guardiao_alegacoes import validar_alegacoes_da_fala
    from mente_laylay.cognicao.contrato_fala import (
        construir_realizacoes_nucleo_explicativo, realizar_nucleo_explicativo,
    )
    from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
    from mente_laylay.personalidade.planejador_resposta import (
        classificar_resultado, fala_factual_resultados_compostos, fala_resultado_por_aspectos,
    )

    itens = tuple(resultados)
    conversa = str(texto_conversacional or "").strip()
    avisos = tuple(str(a).strip() for a in avisos_obrigatorios if str(a).strip())
    segura = str(fala_segura or "").strip()
    if conversa:
        segura = " ".join([segura, "Não consegui responder à parte conversacional deste pedido."]).strip()
    fallback = ConfirmacaoPersonalizada(segura, "calma", 1)
    if complemento_conversacional is not None and (
        not isinstance(complemento_conversacional, ComplementoConversacionalTurno)
        or complemento_conversacional.texto != conversa
        or not complemento_conversacional.atos_explicativos
        or tuple(a.indice for a in complemento_conversacional.atos_explicativos)
           != complemento_conversacional.indices
    ):
        return _com_motivo_fallback(fallback, "contrato_explicativo_divergente")
    realizacoes = (construir_realizacoes_nucleo_explicativo(complemento_conversacional)
                  if complemento_conversacional is not None else ())
    if (complemento_conversacional is not None
        and all(a.relacao == "condicao_nao_verificada" for a in complemento_conversacional.atos_explicativos)
        and not realizacoes):
        return _com_motivo_fallback(fallback, "nucleo_sem_verificador")
    retrato = dict(contexto or {})
    informacoes = dict(informacoes or {})
    for item in itens:
        if item.tem_observacoes_do_executor:
            informacoes[item.id_solicitacao] = fala_resultado_por_aspectos(item)
    if humor_bloqueado_por_preferencia(retrato) and not conversa:
        return fallback
    if not callable(enviar_mensagem) or (not conversa and (not _ativada() or retrato.get("modo_jogo_ativo"))):
        return _com_motivo_fallback(fallback, "autoria_composta_indisponivel")
    if (not itens and not conversa) or any(not item.id_solicitacao or item.origem != "executor" for item in itens):
        return _com_motivo_fallback(fallback, "receipt_composto_invalido")
    classes = [classificar_resultado(item) for item in itens]
    if any(classe not in {"sucesso", "sem_acao", "falha", "incerto"} for classe in classes):
        return _com_motivo_fallback(fallback, "resultado_composto_nao_elegivel")
    contrato = {"resultados": [{
        "indice": indice,
        "id_solicitacao": item.id_solicitacao,
        "intent": item.intent, "status": item.status, "alvo": item.alvo,
        "executou": item.executou, "confirmado": item.confirmado,
        "classe_resultado": classe,
        "fato_verificado": fala_factual_resultados_compostos([item], informacoes=informacoes),
        "limite_evidencia": (
            "abertura confirmada; foco e reprodução não foram confirmados"
            if "abert" in item.status.casefold() and "focad" not in item.status.casefold()
            else "declare apenas o resultado e a certeza informados"
        ),
        "params": {chave: valor for chave, valor in item.params.items()
                   if chave in _PARAMETROS_AUTORIA and isinstance(valor, (str, int, float, bool))},
        "informacao_literal": informacoes.get(item.id_solicitacao, ""),
    } for indice, (item, classe) in enumerate(zip(itens, classes))]}
    sistema = (
        f"{IDENTIDADE_VOZ_LAYLAY} "
        "Você terminou as etapas de um único pedido composto. Escreva uma resposta nova, "
        "natural e curta que conte os resultados juntos, com o seu jeito. Não cole duas "
        "confirmações prontas. Cada resultado é verdade imutável: preserve alvo, ação, "
        "estado, números e certeza de cada etapa. Sucesso significa efeito confirmado; "
        "sem_acao significa estado já satisfeito sem nova execução; falha precisa ser "
        "admitida; incerto precisa dizer o que ainda não foi confirmado. A conclusão "
        "de uma etapa não prova a conclusão das outras. Não acrescente ações, fatos, "
        "promessas ou perguntas. Preserve informacao_literal integralmente quando houver. "
        "Abertura de app, arquivo ou playlist não prova foco nem que música está tocando. "
        "Use fato_verificado e limite_evidencia para preservar essa diferença. "
        "Use uma ou duas frases. Devolva JSON com fala e trechos: fala é a mensagem inteira; "
        "trechos é uma lista de strings, uma para cada resultado na MESMA ORDEM da lista de entrada. "
        "O primeiro trecho relata o primeiro resultado, o segundo trecho relata o segundo resultado, "
        "e assim por diante. Não troque os alvos. Escreva a fala nessa mesma ordem. "
        "Não copie identificadores internos na saída. Cada trecho "
        "deve ser uma cópia exata e não sobreposta da parte da fala que relata aquele "
        "resultado, incluindo sua certeza. Todo o conteúdo deve estar nesses trechos, "
        "exceto conectivos como e ou mas e pontuação. A cópia literal preserva maiúsculas. "
        'Formato obrigatório, exemplo com outros alvos: {"fala":"Abri a agenda e criei a pasta fotos.",'
        '"trechos":["Abri a agenda","criei a pasta fotos"]}. '
        "Não devolva comandos."
    )
    if conversa:
        contrato.update(texto_conversacional=conversa, avisos_obrigatorios=list(avisos))
        if complemento_conversacional is not None:
            contrato["atos_explicativos"] = [
                ato.como_dict() for ato in complemento_conversacional.atos_explicativos
            ]
        # Não acumular as instruções da paráfrase puramente operacional: elas
        # proibiam perguntas e exigiam que todo conteúdo tivesse receipt.
        sistema = (
            f"{IDENTIDADE_VOZ_LAYLAY} "
            "Responda ao pedido misto com JSON contendo somente trechos e conversa. "
            "trechos: lista de strings, uma para cada resultado na mesma ordem. "
            "Cada string relata somente seu fato_verificado, preservando alvo, ação, "
            "números e certeza. Sucesso confirmado, estado já satisfeito sem nova execução, "
            "falha e resultado incerto são diferentes; uma etapa não prova outra. "
            "Preserve informacao_literal quando houver. Abertura não prova foco ou reprodução. "
            "Se resultados estiver vazio, trechos deve ser []. "
            "conversa: sua resposta ao texto_conversacional, não uma cópia do pedido. "
            "Pode explicar o assunto ou pedir esclarecimento; não invente estado atual, "
            "efeitos, agendamento ou ações futuras. Uma condição futura não criou pendência: "
            "diga que a ação condicional não ficou agendada e será necessário um novo "
            "pedido explícito quando chegar a hora; não peça só 'sim' ou confirmação. "
            "Este complemento não executa ações; isso não significa que a Laylay seja "
            "incapaz de executá-las em outro pedido autorizado. Ausência de receipt não "
            "prova falta de acesso ou capacidade: não invente nenhuma dessas limitações. "
            "Os avisos_obrigatorios serão publicados pelo host; não os copie em nenhum campo. "
            "Seja natural e breve. Não devolva comandos, fala ou outros campos. "
            "Nos atos_explicativos, enunciador é quem escreveu o pedido (o usuário), "
            "destinatario é você, Laylay, e grupo não pode virar uma pessoa só. "
            "Preserve essa referência; não invente sujeito quando indeterminado. "
            'Formato: {"trechos":[],"conversa":"<resposta específica ao ato não operacional>"}.'
        )
        if humor_bloqueado_por_preferencia(retrato):
            sistema += " Responda sem humor, conforme a preferência vigente."
        if realizacoes:
            contrato["realizacoes_permitidas"] = realizacoes
            sistema = (
                f"{IDENTIDADE_VOZ_LAYLAY} "
                "Redija os resultados e escolha como explicar as condições deste pedido. "
                "Retorne somente JSON com trechos e realizacoes. trechos é uma lista de "
                "strings, uma por resultado, na mesma ordem. Preserve fato_verificado, "
                "alvo, números, informacao_literal e certeza de CADA resultado. "
                "Uma etapa não prova outra. Abertura não prova foco ou reprodução. "
                "Se resultados estiver vazio, trechos deve ser []. "
                "Para CADA item de realizacoes_permitidas, escolha uma opcao pelo id "
                "e preserve seu indice. Essa escolha é obrigatória e só escolhe redação, "
                "não execução. O host publica a fala escolhida e os avisos_obrigatorios; "
                "não os copie. Não escreva conversa, fala, comandos ou outros campos. "
                'Formato: {"trechos":[],"realizacoes":[{"indice":1,"opcao":"condicao_1"}]}.'
            )
    try:
        resposta = enviar_mensagem(
            [{"role": "system", "content": sistema},
             {"role": "user", "content": json.dumps(contrato, ensure_ascii=False)}],
            _com_tools=False, max_tokens=min(768, 128 + 96 * len(itens) + (320 if conversa else 0)),
            modo_rapido=False, timeout=15.0 if conversa else _timeout_autoria_operacional(),
            _prioridade_interativa=True, _permitir_durante_interacao=True,
            _tipo_chamada="autoria_operacional", _classe_timeout="normal" if conversa else "rapida",
            _contexto_fechado=True,
        )
    except Exception as erro:
        return _com_motivo_fallback(fallback, f"erro_chamada_{type(erro).__name__.lower()}")
    def validar_resposta(resposta_candidata: Any) -> ConfirmacaoPersonalizada:
        if realizacoes:
            # Nenhuma extração de JSON de prosa: conteúdo adicional não possui
            # cobertura. O modelo escolhe; o owner reconstrói e confere a fala.
            try:
                dados = (dict(resposta_candidata) if isinstance(resposta_candidata, Mapping)
                         else json.loads(str(resposta_candidata)))
            except (TypeError, ValueError):
                dados = {}
            if not isinstance(dados, dict) or set(dados) != {"trechos", "realizacoes"}:
                return _com_motivo_fallback(fallback, "estrutura_nuclear_invalida")
            proposta = {"realizacoes": dados["realizacoes"]}
            trecho_nuclear, motivo = realizar_nucleo_explicativo(complemento_conversacional, proposta)
            if motivo:
                return _com_motivo_fallback(fallback, motivo)
            aderencia = validar_aderencia_contrato_fala(
                conversa, trecho_nuclear, turno_id=complemento_conversacional.turno_id,
                contrato_fala={"exigir_nucleo_verificado": True,
                    "turno_id": complemento_conversacional.turno_id,
                    "complemento_nuclear": complemento_conversacional, "proposta_nuclear": proposta},
            )
            if not aderencia["aceita"]:
                return _com_motivo_fallback(fallback, "vinculo_nuclear_rejeitado")
            dados = {"trechos": dados["trechos"], "conversa": trecho_nuclear}
        else:
            dados = _extrair_json(resposta_candidata)
        if conversa:
            if (set(dados) != {"trechos", "conversa"}
                or not isinstance(dados.get("conversa"), str)
                or not isinstance(dados.get("trechos"), list)
                or len(dados["trechos"]) != len(itens)
                or any(not isinstance(t, str) or not t.strip() for t in dados["trechos"])):
                return _com_motivo_fallback(fallback, "estrutura_mista_invalida")
            # A relação posicional nasce da lista congelada do host. Os campos
            # abaixo são apenas a representação interna do verificador comum;
            # não são novas provas e não evitam a validação factual de cada trecho.
            trechos_mistos = [re.sub(r"\s+", " ", t).strip() for t in dados["trechos"]]
            trecho_conversa = (dados["conversa"] if realizacoes
                              else re.sub(r"\s+", " ", dados["conversa"]).strip())
            dados = {"fala": " ".join([*trechos_mistos, *avisos, trecho_conversa]),
                     "trechos": trechos_mistos, "trecho_conversacional": trecho_conversa,
                     "trechos_avisos": list(avisos)}
        fala = (str(dados.get("fala") or "").strip() if realizacoes
                else re.sub(r"\s+", " ", str(dados.get("fala") or "")).strip())
        trechos = dados.get("trechos")
        if (
            not 3 <= len(fala) <= 1000 or ("?" in fala and not conversa) or contem_ataque_pessoal(fala)
            or dados.get("comandos") not in (None, [], ())
            or not isinstance(trechos, list) or len(trechos) != len(itens)
        ):
            return _com_motivo_fallback(fallback, "estrutura_composta_invalida")
        por_id = {item.id_solicitacao: (item, classe) for item, classe in zip(itens, classes)}
        cobertos: set[str] = set()
        intervalos: list[tuple[int, int]] = []
        for posicao, campo in enumerate(trechos):
            if isinstance(campo, str):
                # O host associa a lista congelada de receipts à mesma lista de
                # trechos. A certeza, o alvo e a ação ainda precisam ser validados.
                campo = {"indice": posicao, "trecho": campo}
            if not isinstance(campo, dict):
                return _com_motivo_fallback(fallback, "trecho_composto_invalido")
            identidade = str(campo.get("id_solicitacao") or "").strip()
            indice = campo.get("indice")
            if indice is not None:
                if type(indice) is not int or not 0 <= indice < len(itens):
                    return _com_motivo_fallback(fallback, "indice_composto_invalido")
                identidade_host = itens[indice].id_solicitacao
                if identidade and identidade != identidade_host:
                    return _com_motivo_fallback(fallback, "identidade_composta_divergente")
                identidade = identidade_host
            trecho = re.sub(r"\s+", " ", str(campo.get("trecho") or "")).strip()
            # Receipt e ocorrência textual têm a mesma ordem congelada pelo
            # host. Texto igual em outro ato não reutiliza o primeiro intervalo.
            inicio = fala.find(trecho, intervalos[-1][1] if intervalos else 0) if trecho else -1
            fim = inicio + len(trecho)
            if (
                identidade not in por_id or identidade != itens[posicao].id_solicitacao
                or identidade in cobertos or inicio < 0
                or any(inicio < b and fim > a for a, b in intervalos)
            ):
                return _com_motivo_fallback(fallback, "vinculo_composto_invalido")
            item, classe = por_id[identidade]
            status = item.status.casefold()
            if "abert" in status and "focad" not in status:
                # A certeza pertence a este receipt, não às outras etapas.
                base_trecho = _normalizar(trecho)
                if (re.search(r"\b(?:foco|focad[oa]|frente)\b", base_trecho)
                    and item.params.get("foco_confirmado") is not True):
                    return _com_motivo_fallback(fallback, "foco_composto_nao_confirmado")
                if re.search(r"\b(?:tocando|reproduzindo|ouvindo|ouvid[oa])\b", base_trecho):
                    return _com_motivo_fallback(fallback, "reproducao_composta_nao_confirmada")
            literal = informacoes.get(identidade, "")
            if item.tem_observacoes_do_executor and trecho.rstrip(" .;") != fala_resultado_por_aspectos(item).rstrip(" .;"):
                return _com_motivo_fallback(fallback, "aspectos_compostos_alterados")
            motivo = (
                "" if item.tem_observacoes_do_executor else
                "informacao_composta_omitida" if literal and literal not in trecho else
                "" if literal else _motivo_contrato_invalido(
                    trecho, resultado=item, classe=classe,
                    status_declarado=item.status, alvo_declarado=item.alvo,
                )
            )
            if motivo:
                return _com_motivo_fallback(fallback, f"contrato_composto_nao_preservado:{motivo}")
            guardiao_trecho = validar_alegacoes_da_fala(
                trecho, plano={"requer_execucao": True, "comandos": [item.como_dict()]},
                origem="canal_voz",
            )
            if guardiao_trecho.get("problemas"):
                return _com_motivo_fallback(fallback, "alegacao_do_trecho_sem_receipt")
            cobertos.add(identidade)
            intervalos.append((inicio, fim))
        if conversa:
            trecho_conversa = (str(dados.get("trecho_conversacional") or "") if realizacoes
                              else re.sub(r"\s+", " ", str(dados.get("trecho_conversacional") or "")).strip())
            # Prosa livre mantém suas guardas. Na realização controlada, a
            # fonte citada é literal, não uma promessa assumida pela Laylay;
            # seu vínculo já foi conferido pelo verificador canônico acima.
            guardiao_conversa = {"problemas": []} if realizacoes else validar_alegacoes_da_fala(
                trecho_conversa, plano={"comandos": [], "texto_usuario": conversa,
                                        "atos_explicativos": (complemento_conversacional.atos_explicativos
                                                               if complemento_conversacional is not None else ()),
                                        "exigir_receipt_para_estado": True,
                                        "escopo_explicativo_sem_continuacao": bool(
                                            complemento_conversacional is not None
                                            and any(ato.relacao == "condicao_nao_verificada"
                                                    for ato in complemento_conversacional.atos_explicativos)
                                    ),
                                    "exigir_explicacao_condicional": bool(
                                        complemento_conversacional is not None
                                        and any(ato.relacao == "condicao_nao_verificada"
                                                for ato in complemento_conversacional.atos_explicativos)
                                    )},
                origem="canal_voz",
            )
            from mente_laylay.cognicao.guardiao_realidade_pessoal import detectar_experiencia_pessoal_inventada
            if (not trecho_conversa or guardiao_conversa.get("problemas")
                or (not realizacoes and detectar_experiencia_pessoal_inventada(trecho_conversa))):
                motivo = ":" + ",".join(guardiao_conversa["problemas"]) if guardiao_conversa.get("problemas") else ""
                return _com_motivo_fallback(fallback, "conversa_composta_invalida" + motivo)
            trechos_avisos = dados.get("trechos_avisos", [])
            if not isinstance(trechos_avisos, list) or trechos_avisos != list(avisos):
                return _com_motivo_fallback(fallback, "avisos_compostos_divergentes")
            for trecho in [trecho_conversa, *trechos_avisos]:
                inicio = fala.find(trecho)
                fim = inicio + len(trecho)
                if inicio < 0 or any(inicio < b and fim > a for a, b in intervalos):
                    return _com_motivo_fallback(fallback, "escopos_compostos_sobrepostos")
                intervalos.append((inicio, fim))
        sem_cobertura = fala
        for inicio, fim in sorted(intervalos, reverse=True):
            sem_cobertura = sem_cobertura[:inicio] + " " + sem_cobertura[fim:]
        if re.sub(r"\b(?:e|mas|enquanto|tambem|também)\b|[\W_]", "", sem_cobertura, flags=re.IGNORECASE):
            return _com_motivo_fallback(fallback, "alegacao_composta_sem_receipt")
        numeros = lambda texto: set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", texto))
        evidencia = " ".join((fallback.fala, json.dumps(contrato, ensure_ascii=False)))
        fala_operacional = " ".join(str(c.get("trecho") or "") if isinstance(c, dict) else str(c) for c in trechos)
        fala_conferida = fala_operacional if conversa else fala
        evidencia_numerica = json.dumps(contrato["resultados"], ensure_ascii=False) if conversa else evidencia
        if not numeros(fala_conferida).issubset(numeros(evidencia_numerica)):
            return _com_motivo_fallback(fallback, "detalhe_numerico_nao_evidenciado")
        guardiao = validar_alegacoes_da_fala(
            fala_conferida, plano={"requer_execucao": True, "comandos": [item.como_dict() for item in itens]},
            origem="canal_voz",
        )
        if guardiao.get("problemas"):
            return _com_motivo_fallback(fallback, "guardiao_composto_rejeitou")
        return ConfirmacaoPersonalizada(fala, fallback.emocao, fallback.nivel, usada_llm=True)

    validada = validar_resposta(resposta)
    if (validada.usada_llm or not conversa or complemento_conversacional is None
        or eh_estado_tecnico_llm(resposta)
        or not validada.motivo_fallback.startswith("conversa_composta_invalida")):
        return validada
    trechos_operacionais = tuple(_extrair_json(resposta)["trechos"])
    # Mesmo contrato, uma segunda redação, mesmas guardas. O diagnóstico é
    # sobre a proposta rejeitada; não vira fato/receipt nem inclui essa fala.
    diagnostico = {
        "origem": "validador_de_redacao",
        "motivo": validada.motivo_fallback,
        "nao_e_resultado_operacional": True,
        "instrucao": (
            "Corrija a redação, preservando resultados e atos_explicativos originais. "
            "Não crie pendência ou peça só confirmação: para executar depois, é "
            "necessário novo pedido direto. Enunciador é o usuário; destinatario "
            "é Laylay. Cite a fonte se precisar manter seus pronomes literais. "
            "Se o ato é condicao_nao_verificada, explique essa condição e que ela "
            "não deixou a ação agendada. Não responda sobre um pedido educado "
            "quando o ato é uma condição futura. "
            "Retorne somente o mesmo JSON com trechos e conversa."
            " Os trechos operacionais já foram validados: preserve-os literalmente; "
            "corrija somente conversa."
        ),
    }
    try:
        resposta_reparo = enviar_mensagem(
            [{"role": "system", "content": sistema},
             {"role": "user", "content": json.dumps(contrato, ensure_ascii=False)},
             {"role": "user", "content": json.dumps(diagnostico, ensure_ascii=False)}],
            _com_tools=False, max_tokens=min(768, 448 + 96 * len(itens)),
            modo_rapido=False, timeout=15.0,
            _prioridade_interativa=True, _permitir_durante_interacao=True,
            _tipo_chamada="reparo_factual", _classe_timeout="normal",
            _contexto_fechado=True,
        )
    except Exception as erro:
        return _com_motivo_fallback(fallback, f"erro_reparo_{type(erro).__name__.lower()}")
    dados_reparo = _extrair_json(resposta_reparo)
    if (not isinstance(dados_reparo.get("trechos"), list)
        or tuple(dados_reparo["trechos"]) != trechos_operacionais):
        return _com_motivo_fallback(fallback, "trecho_operacional_alterado_no_reparo")
    return validar_resposta(resposta_reparo)


def personalizar_informacao_llm(
    fala_segura: str,
    *,
    fatos_obrigatorios: list[str] | tuple[str, ...],
    enviar_mensagem: Callable[..., Any] | None,
    emocao: str = "calma",
    nivel: int = 1,
    contexto: Mapping[str, Any] | None = None,
) -> ConfirmacaoPersonalizada:
    """Dá voz a uma informação sem permitir que a LLM altere seu conteúdo.

    Diferentemente de uma confirmação operacional, uma listagem pode conter
    nomes e textos que precisam sobreviver integralmente à paráfrase. Por isso
    todos os fatos recebidos são âncoras literais: se um deles desaparecer, a
    resposta determinística original vence.
    """
    fallback = ConfirmacaoPersonalizada(
        fala=re.sub(r"\s+", " ", str(fala_segura or "")).strip(),
        emocao=str(emocao or "calma"),
        nivel=max(1, min(3, int(nivel or 1))),
    )
    retrato = dict(contexto or {})
    fatos = [re.sub(r"\s+", " ", str(fato or "")).strip() for fato in fatos_obrigatorios]
    if humor_bloqueado_por_preferencia(retrato):
        return fallback
    fatos = [fato for fato in fatos if fato]
    if (
        not _ativada()
        or not callable(enviar_mensagem)
        or not fallback.fala
        or not fatos
        or len(fallback.fala) > 900
        or bool(retrato.get("modo_jogo_ativo"))
    ):
        return fallback

    contrato = {
        "fala_segura": fallback.fala,
        "fatos_obrigatorios": fatos,
        "emocao_atual": str(retrato.get("current_emotion") or fallback.emocao),
    }
    sistema = (
        f"{IDENTIDADE_VOZ_LAYLAY} "
        "Reescreva a informação fornecida com a voz doce, jovem, natural e levemente "
        "debochada da Laylay quando combinar. Seja breve. Cada fato obrigatório deve "
        "aparecer literalmente e sem alteração na fala final. Você pode somente ligar "
        "os fatos com uma abertura ou comentário curto; não acrescente nomes, números, "
        "resultados, ações, promessas ou perguntas. Responda apenas JSON válido com "
        "fala, emocao e nivel. Emoções: calma, alegre, debochada, envergonhada, surpresa, "
        "triste, irritada, brava, acalmando-se."
    )
    try:
        resposta = enviar_mensagem(
            [
                {"role": "system", "content": sistema},
                {"role": "user", "content": json.dumps(contrato, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=180,
            modo_rapido=True,
            timeout=_timeout_autoria_operacional(),
            _prioridade_interativa=True,
            _permitir_durante_interacao=True,
            _tipo_chamada="autoria_operacional",
            _classe_timeout="rapida",
        )
    except Exception:
        return fallback

    dados = _extrair_json(resposta)
    fala = re.sub(r"\s+", " ", str(dados.get("fala") or "")).strip()
    fala_normalizada = _normalizar(fala)
    if (
        not 3 <= len(fala) <= 1000
        or fala.count("?")
        or any(_normalizar(fato) not in fala_normalizada for fato in fatos)
        or re.search(
            r"\b(?:vou fazer|vou abrir|vou apagar|vou excluir|executei|confirmei|"
            r"nao consegui|falhou)\b",
            fala_normalizada,
        )
        or re.search(
            r"\b(?:quando (?:a gente|voce|você)|antes de dormir|pra dormir|"
            r"foi dormir|ontem|na semana passada|eu lembrei|meu coracao|meu coração)\b",
            fala_normalizada,
        )
    ):
        return fallback

    emocao_llm = _normalizar(dados.get("emocao"))
    if emocao_llm not in EMOCOES_PERMITIDAS:
        emocao_llm = fallback.emocao
    try:
        nivel_llm = max(1, min(3, int(dados.get("nivel") or fallback.nivel)))
    except (TypeError, ValueError):
        nivel_llm = fallback.nivel
    return ConfirmacaoPersonalizada(fala, emocao_llm, nivel_llm, usada_llm=True)
