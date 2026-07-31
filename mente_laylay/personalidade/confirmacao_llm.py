"""Personalização segura e opcional das confirmações operacionais.

O executor continua sendo a única fonte da verdade. A LLM recebe um contrato
já concluído e pode somente reescrever sua confirmação; qualquer saída lenta,
inválida ou contraditória devolve a fala determinística original.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from mente_laylay.integracao.llm_http import eh_estado_tecnico_llm
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.prompt_voz_unica import IDENTIDADE_VOZ_LAYLAY


EMOCOES_PERMITIDAS = frozenset({
    "calma", "alegre", "debochada", "envergonhada", "surpresa",
    "triste", "irritada", "brava", "acalmando-se",
})

# Consultas e listagens carregam dados que uma paráfrase poderia apagar.
INTENTS_INFORMATIVOS = frozenset({
    "IOT_STATUS", "PLAYLIST_LIST", "LIST_PLAYLIST_CONTENT", "READ_EMAILS",
    "READ_URGENT_EMAILS", "LER_EMAILS", "LER_EMAILS_URGENTES",
    "WEATHER", "CLIMA", "LISTAR_AGENDAMENTOS", "LER_NOTIFICACOES",
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
    "item_deletado": ("apague", "remov", "lixeira"),
    "movido_para_lixeira": ("lixeira", "mov", "enviei"),
    "item_movido_para_pasta": ("mov", "mudei"),
    "app_aberto": ("abri", "aberto"),
    "app_focado": ("foco", "frente", "trouxe", "puxei"),
    "ja_aberto_focado": ("aberto", "foco", "frente"),
    "app_fechado": ("feche", "encerr"),
    "site_aberto": ("abri", "aberto", "navegador"),
    "url_aberta": ("abri", "aberto", "pagina"),
    "aba_fechada": ("aba", "feche"),
    "janela_maximizada": ("maximiz", "tela"),
    "musica_aberta": ("toc", "musica", "som"),
    "playlist_aberta": ("playlist", "faixa", "toc"),
    "playlist_deletada": ("playlist", "apague", "remov"),
    "playlist_musica_adicionada": ("playlist", "adicione", "salv", "guarde"),
    "acao_agendada": ("agend", "lembrete"),
    "lembrete_agendado": ("agend", "lembrete"),
    "agendamento_cancelado": ("cancel", "agenda"),
}


@dataclass(frozen=True)
class ConfirmacaoPersonalizada:
    fala: str
    emocao: str
    nivel: int
    usada_llm: bool = False


def _normalizar(texto: Any) -> str:
    valor = unicodedata.normalize("NFKD", str(texto or ""))
    valor = "".join(ch for ch in valor if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", valor).strip().casefold()


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


def _elegivel(resultado: ResultadoAcao, classe: str, fala: str) -> bool:
    if not _ativada() or classe != "sucesso" or resultado.confirmado is not True:
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


def _fala_preserva_contrato(
    fala: str,
    *,
    resultado: ResultadoAcao,
    status_declarado: str,
    alvo_declarado: str,
) -> bool:
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    base = _normalizar(texto)
    if not 3 <= len(texto) <= 260 or texto.count("?") > 0:
        return False
    if _normalizar(status_declarado) != _normalizar(resultado.status):
        return False
    if resultado.alvo and _normalizar(alvo_declarado) != _normalizar(resultado.alvo):
        return False
    if re.search(
        r"\b(?:nao consegui|nao fiz|nao executei|falhou|talvez|acho que|vou tentar|"
        r"posso tentar|quer que eu|ainda vou|nao respondeu)\b",
        base,
    ):
        return False

    raizes = RAIZES_POR_STATUS.get(_normalizar(resultado.status), ())
    if raizes and not any(raiz in base for raiz in raizes):
        return False
    concretos = _tokens_concretos(resultado)
    if concretos and not any(token in base for token in concretos):
        return False
    return True


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
    if not callable(enviar_mensagem) or not _elegivel(resultado, classe, fallback.fala):
        return fallback

    retrato = dict(contexto or {})
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
        "fala_segura": fallback.fala,
        "emocao_atual": str(retrato.get("current_emotion") or fallback.emocao),
    }
    sistema = (
        f"{IDENTIDADE_VOZ_LAYLAY} "
        "Você está falando logo depois de um comando já executado. "
        "Reescreva somente a confirmação fornecida com personalidade doce, jovem, natural, "
        "levemente divertida ou debochada quando combinar. Use uma ou duas frases curtas. "
        "O contrato é verdade imutável: não altere ação, alvo, estado, números ou certeza; "
        "não prometa outra ação, não faça pergunta e não acrescente fatos. "
        "Responda apenas JSON válido com fala, emocao, nivel, status e alvo. "
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
            timeout=3,
            _prioridade_interativa=False,
        )
    except Exception:
        return fallback

    dados = _extrair_json(resposta)
    fala = str(dados.get("fala") or "").strip()
    if not _fala_preserva_contrato(
        fala,
        resultado=resultado,
        status_declarado=str(dados.get("status") or ""),
        alvo_declarado=str(dados.get("alvo") or ""),
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
    fatos = [re.sub(r"\s+", " ", str(fato or "")).strip() for fato in fatos_obrigatorios]
    fatos = [fato for fato in fatos if fato]
    if (
        not _ativada()
        or not callable(enviar_mensagem)
        or not fallback.fala
        or not fatos
        or len(fallback.fala) > 900
    ):
        return fallback

    retrato = dict(contexto or {})
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
            timeout=3,
            _prioridade_interativa=False,
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
