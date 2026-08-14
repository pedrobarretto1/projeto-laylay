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
from typing import Any, Callable, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto_basico as _normalizar,
)
from mente_laylay.integracao.llm_http import eh_estado_tecnico_llm
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.prompt_voz_unica import IDENTIDADE_VOZ_LAYLAY
from mente_laylay.personalidade.antirrepeticao import repeticao_estrutural


EMOCOES_PERMITIDAS = frozenset({
    "calma", "alegre", "debochada", "envergonhada", "surpresa",
    "triste", "irritada", "brava", "acalmando-se",
})

# Consultas e listagens carregam dados que uma paráfrase poderia apagar.
INTENTS_INFORMATIVOS = frozenset({
    "IOT_STATUS", "PLAYLIST_LIST", "LIST_PLAYLIST_CONTENT", "READ_EMAILS",
    "READ_URGENT_EMAILS", "LER_EMAILS", "LER_EMAILS_URGENTES",
    "WEATHER", "CLIMA", "LISTAR_AGENDAMENTOS", "LER_NOTIFICACOES",
    "NOTIFICATIONS",
    "LIST_TABS", "LIST_WINDOWS",
    "FILE_SEARCH", "SEARCH",
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
    "ja_estava_ligado": ("ligado", "funcionando"),
    "ja_estava_desligado": ("desligado", "quieto"),
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
    "agendamento_cancelado": ("cancel", "agenda"),
    "indisponivel": ("nao respondeu", "indisponivel", "offline"),
    "nao_encontrado": ("nao encontrei", "nao achei", "nao apareceu"),
    "falha_execucao": ("nao consegui", "falhou", "nao confirmou"),
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
    frases = [
        parte.strip()
        for parte in re.split(r"(?<=[.!?])\s+", texto)
        if parte.strip()
    ]
    if len(frases) > 2:
        return "fala_operacional_prolixa"
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
        r"nao respondeu|nao encontrei|nao achei|nao apareceu|nao confirmou)\b",
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
    # Durante jogo, latência e uso de hardware vencem variedade: a fala local
    # curta continua sendo o caminho oficial.
    if bool(retrato.get("modo_jogo_ativo")):
        return _com_motivo_fallback(fallback, "modo_jogo_fala_local")
    if not callable(enviar_mensagem):
        return _com_motivo_fallback(fallback, "modelo_sem_callback")
    if not _elegivel(resultado, classe, fallback.fala):
        return _com_motivo_fallback(fallback, "resultado_nao_elegivel")

    evento = dict(retrato.get("avaliacao_evento") or {})
    reacao_causal = {
        chave: evento.get(chave)
        for chave in (
            "responsabilidade", "confianca", "emocao", "nivel", "arco",
            "permite_expressao", "repeticoes", "provocacao_usuario",
        )
        if chave in evento
    }
    contrato = {
        "intent": resultado.intent,
        "status": resultado.status,
        "alvo": resultado.alvo,
        "params": {
            chave: valor for chave, valor in resultado.params.items()
            if chave in {
                "acao", "alvo", "cor", "nome_app", "nome", "nome_arquivo",
                "nome_playlist", "query", "site", "url", "brilho",
                "temperatura", "volume",
            } and isinstance(valor, (str, int, float, bool))
        },
        "executou": resultado.executou,
        "confirmado": resultado.confirmado,
        "classe_resultado": classe,
        "fala_segura": fallback.fala,
        "ultima_fala_operacional": str(retrato.get("ultima_resposta") or "").strip()[:300],
        "falas_recentes_a_nao_repetir": [
            str(item or "").strip()[:220]
            for item in list(retrato.get("falas_recentes") or [])[-4:]
            if str(item or "").strip()
        ],
        "emocao_atual": str(retrato.get("current_emotion") or fallback.emocao),
        "reacao_causal": reacao_causal,
    }
    regra_reacao = (
        "A reação causal foi validada: inclua na mesma fala uma tirada curta coerente com "
        "responsabilidade, confiança e intensidade. No nível 1, seja espirituosa; no nível "
        "2, pode demonstrar deboche ou irritação clara; no nível 3, pode ficar genuinamente "
        "brava, dar uma bronca curta e recusar o retrabalho redundante. Quando a responsabilidade "
        "for do usuário, confronte diretamente o comportamento repetido, sem atacar o valor, a "
        "inteligência ou a identidade da pessoa. Não dilua a emoção com gentileza artificial. "
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
    sistema = (
        f"{IDENTIDADE_VOZ_LAYLAY} "
        "Você está falando no cotidiano logo depois do resultado observado de um comando. "
        "Escreva uma única resposta completa na voz da Laylay; não cole uma confirmação técnica "
        "com outra frase pronta. Seja doce, jovem, natural e levemente debochada quando combinar. "
        "Use uma ou duas frases curtas. "
        f"{regra_classe}"
        "O contrato é verdade imutável: não altere ação, alvo, estado, números ou certeza; "
        "não prometa nem ofereça outra ação, não use 'se quiser', não faça pergunta e não "
        "acrescente fatos. A primeira frase deve começar pelo resultado e pelo alvo observados; "
        "só depois deles pode vir humor, emoção ou deboche. A personalidade deve continuar na "
        "mesma resposta, mas nunca esconder o status. "
        "Se ultima_fala_operacional ou falas_recentes_a_nao_repetir estiverem preenchidas, "
        "não reutilize nenhuma abertura, ordem de ideias ou tirada dessa lista. Varie "
        "naturalmente começando pela recusa, pelo resultado, pela observação ou pela tirada, "
        "sem omitir os fatos obrigatórios. "
        "A tirada pode brincar somente com a repetição observada do pedido; não invente celular, "
        "gestos, aparência ou ambiente do usuário. Não use palavrão nem linguagem ofensiva. "
        f"{regra_reacao}"
        "Responda apenas JSON válido com fala, emocao, nivel, status e alvo. "
        "Nos campos status e alvo, prefira copiar exatamente os valores recebidos no contrato. "
        "Emoções: calma, alegre, debochada, envergonhada, surpresa, triste, irritada, brava, acalmando-se."
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
            motivo_sem_pergunta = _motivo_contrato_invalido(
                fala_sem_pergunta,
                resultado=resultado,
                classe=classe,
                status_declarado=str(dados_candidatos.get("status") or ""),
                alvo_declarado=str(dados_candidatos.get("alvo") or ""),
            )
            if not motivo_sem_pergunta:
                return fala_sem_pergunta, ""
        return fala_candidata, motivo

    dados = _extrair_json(resposta)
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
                            "Sua proposta anterior foi rejeitada por "
                            f"{motivo_contrato}. Escreva outra fala realmente nova, "
                            "corrigindo exatamente esse ponto e preservando todos os "
                            "fatos do contrato. Retorne somente o JSON solicitado."
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
            )
            dados_corrigidos = _extrair_json(resposta_corrigida)
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
                            "mesmo contrato e o mesmo formato JSON."
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
            dados_variados = _extrair_json(resposta_variada)
            fala_variada, motivo_variado = validar_dados(dados_variados)
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

    emocao_llm = _normalizar(dados.get("emocao"))
    if emocao_llm not in EMOCOES_PERMITIDAS:
        emocao_llm = fallback.emocao
    try:
        nivel_llm = max(1, min(3, int(dados.get("nivel") or fallback.nivel)))
    except (TypeError, ValueError):
        nivel_llm = fallback.nivel
    return ConfirmacaoPersonalizada(fala, emocao_llm, nivel_llm, usada_llm=True)


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
