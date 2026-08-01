"""Contrato único entre resultado real de ação e fala da Laylay."""

from __future__ import annotations

import re
from dataclasses import dataclass
from mente_laylay.memoria_mental.resultado_acao import (
    ResultadoAcao,
    STATUS_RESULTADO_JA_SATISFEITO,
)
from mente_laylay.personalidade.fala_operacional import estilizar_fala_operacional


@dataclass(frozen=True)
class PlanoResposta:
    fala: str
    classe: str
    emocao: str
    nivel: int
    grau_compromisso: str
    personalidade_permitida: bool


STATUS_FALHA = {
    "falha_execucao", "nao_encontrado", "indisponivel", "protocolo_indisponivel",
    "bloqueado_por_seguranca", "falha_validacao", "falha_consulta", "acao_invalida",
    "notificacoes_sem_suporte", "app_aberto_sem_foco",
}
STATUS_PENDENTE = {"confirmacao_necessaria", "aguardando_confirmacao", "pendente"}


def classificar_resultado(resultado: ResultadoAcao) -> str:
    status = str(resultado.status or "").strip().casefold()
    if status in STATUS_PENDENTE or "confirmacao" in status and "confirmado" not in status:
        return "pendente"
    if status in STATUS_RESULTADO_JA_SATISFEITO and resultado.confirmado is True:
        return "sem_acao"
    if resultado.executou is False or resultado.confirmado is False or status in STATUS_FALHA or any(
        termo in status for termo in ("falha", "erro", "indisponivel", "nao_encontrado", "bloqueado")
    ):
        return "falha"
    if resultado.executou is True and resultado.confirmado is None:
        return "incerto"
    if resultado.executou is True and resultado.confirmado is True:
        return "sucesso"
    # Um nome de status otimista não substitui a confirmação do executor.
    return "incerto"


def classificar_grau_compromisso(texto: str) -> str:
    t = re.sub(r"\s+", " ", str(texto or "")).strip().casefold()
    if re.search(r"\b(?:acho que (?:eu )?vou|talvez|estou pensando em|to pensando em|tô pensando em|seria bom)\b", t):
        return "deliberativo"
    if re.search(r"\b(?:por favor|pode|poderia|faz pra mim|faça pra mim)\b", t):
        return "pedido"
    if re.search(r"^(?:abre|fecha|liga|desliga|toca|pausa|cria|apaga|maximiza|coloca|aumenta|diminui)\b", t):
        return "ordem"
    return "neutro"


def _fala_compativel(fala: str, classe: str) -> bool:
    base = str(fala or "").casefold()
    sinais_falha = ("não consegui", "nao consegui", "falhou", "não respondeu", "nao respondeu", "não achei", "nao achei", "não executei", "nao executei")
    sinais_sucesso = ("consegui", "pronto", "feito", "abri", "fechei", "liguei", "desliguei", "criei", "apaguei", "confirmei")
    sinais_certeza_execucao = (*sinais_sucesso, "pausada", "pausei", "pulando", "troquei", "coloquei", "executei")
    if classe == "falha" and any(s in base for s in sinais_sucesso) and not any(s in base for s in sinais_falha):
        return False
    if classe == "sucesso" and any(s in base for s in sinais_falha):
        return False
    if classe == "sem_acao":
        sinais_sem_acao = (
            "já estava", "ja estava", "já está", "ja esta", "já tava", "ja tava", "não mexi",
            "nao mexi", "mantive", "nem precisei", "não vou", "nao vou",
        )
        if not any(s in base for s in sinais_sem_acao):
            return False
    if classe == "pendente":
        sinais_pendencia = ("confirma", "confirmação", "confirmacao", "preciso que", "quer que eu", "posso ")
        if not any(s in base for s in sinais_pendencia):
            return False
    if classe == "incerto" and any(s in base for s in sinais_certeza_execucao):
        return False
    return True


def _contextualizar_turno_misto(fala: str, texto_usuario: str) -> str:
    """Reconhece o comentário humano que acompanha um comando explícito."""
    texto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip().casefold()
    if not texto or not re.search(
        r"\b(?:abre|fecha|liga|desliga|toca|coloca|bota|cria|apaga|pausa|aumenta|abaixa)\b",
        texto,
    ):
        return fala
    reconhecimentos = (
        (r"\b(?:to|tô|estou)\s+cansad[oa]\b", "Peguei que você tá cansado."),
        (r"\b(?:ta|tá|esta|está)\s+(?:muito\s+)?quente\b", "Tá quente mesmo."),
        (r"\b(?:to|tô|estou)\s+com\s+frio\b", "Peguei que você tá com frio."),
        (r"\b(?:to|tô|estou)\s+triste\b", "Eu ouvi que você tá triste."),
        (r"\b(?:noite|dia)\s+chat[oa]\b", "O clima tá meio sem graça mesmo."),
    )
    for padrao, reconhecimento in reconhecimentos:
        if re.search(padrao, texto):
            base = str(fala or "").strip()
            if not base or reconhecimento.casefold() in base.casefold():
                return base
            return f"{reconhecimento} {base[0].lower() + base[1:] if len(base) > 1 else base.lower()}"
    return fala


def _ancora_resultado(resultado: ResultadoAcao, classe: str) -> str:
    alvo = str(resultado.alvo or "").strip()
    objeto = alvo or "o que você pediu"
    status = str(resultado.status or "").strip().casefold()
    if classe == "falha":
        return f"Não consegui concluir o pedido em {objeto}." if alvo else "Não consegui fazer o que você pediu."
    if classe == "pendente":
        return f"Ainda não mexi em {objeto}; falta sua confirmação."
    if classe == "incerto":
        return f"Enviei o comando para {objeto}, mas não consegui confirmar o resultado."
    if classe == "sem_acao":
        if status in {"ja_aberto_focado", "site_ja_aberto_focado"}:
            return f"{objeto.capitalize()} já está aberto e em foco; não repeti a abertura."
        if status == "ja_estava_ligado":
            return f"{objeto.capitalize()} já está ligado; não repeti o comando."
        if status == "ja_estava_desligado":
            return f"{objeto.capitalize()} já está desligado; não repeti o comando."
        return f"{objeto.capitalize()} já estava como você pediu; não repeti a ação."

    if status in {"ligado", "ja_estava_ligado"}:
        return f"{objeto.capitalize()} está ligado; confirmei o estado."
    if status in {"desligado", "ja_estava_desligado"}:
        return f"{objeto.capitalize()} está desligado; confirmei o estado."
    if "volume" in status:
        return f"Ajustei {objeto} e o comando respondeu."
    if "fechad" in status or "deletad" in status or "cancelad" in status:
        return f"Concluí o fechamento de {objeto}."
    if "abert" in status or "focad" in status:
        return f"Deixei {objeto} aberto e em foco."
    if "criad" in status:
        return f"Criei {objeto} e confirmei que ficou pronto."
    if "agendad" in status:
        return f"Agendei {objeto} e confirmei o registro."
    return f"Concluí o pedido em {objeto} e confirmei o resultado."


def _garantir_resultado_explicito(fala: str, resultado: ResultadoAcao, classe: str) -> str:
    """Preserva expressão livre, mas nunca deixa o resultado operacional implícito."""
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    base = texto.casefold()
    sinais = {
        "sucesso": (
            "consegui", "concluí", "conclui", "confirm", "abri", "fechei", "liguei",
            "desliguei", "criei", "apaguei", "ajustei", "aumentei", "baixei", "silenciei",
            "agendei", "cancelei", "está ligado", "esta ligado", "está desligado", "esta desligado",
            "já estava", "ja estava", "já está", "ja esta", "já ficou", "pronto",
            "aberto", "em foco", "trouxe", "puxei pra frente", "encontrei",
            "procurei", "listei",
        ),
        "falha": (
            "não consegui", "nao consegui", "não foi", "nao foi", "falhou", "não respondeu",
            "nao respondeu", "não confirmou", "nao confirmou", "não achei", "nao achei",
            "não executei", "nao executei", "não rolou", "nao rolou", "não colaborou", "nao colaborou",
        ),
        "pendente": ("ainda não", "ainda nao", "confirma", "falta sua", "antes de mexer"),
        "incerto": (
            "não consegui confirmar", "nao consegui confirmar", "sem confirmação", "sem confirmacao",
            "não sei se", "nao sei se", "ainda não apareceu", "ainda nao apareceu",
            "ainda está inicializando", "ainda esta inicializando", "ainda não tenho", "ainda nao tenho",
            "mandei ", "pedi ", "comando de ", "comando enviado", "enviei o comando",
        ),
        "sem_acao": (
            "já estava", "ja estava", "já está", "ja esta", "já tava", "ja tava", "não mexi", "nao mexi",
            "não repeti", "nao repeti", "mantive", "nem precisei", "não vou", "nao vou",
        ),
    }
    if any(sinal in base for sinal in sinais.get(classe, ())):
        return texto
    ancora = _ancora_resultado(resultado, classe)
    if not texto:
        return ancora
    return f"{ancora} {texto[0].upper() + texto[1:] if len(texto) > 1 else texto.upper()}"


def planejar_resposta_acao(
    resultado: ResultadoAcao,
    fala_base: str = "",
    *,
    emocao_preferida: str = "",
    nivel_preferido: int = 1,
) -> PlanoResposta:
    classe = classificar_resultado(resultado)
    alvo = str(resultado.alvo or "isso").strip()
    fala = re.sub(r"\s+", " ", str(fala_base or "")).strip()
    if not fala or not _fala_compativel(fala, classe):
        if classe == "sucesso":
            fala = f"Concluí a ação em {alvo} e confirmei o resultado."
        elif classe == "sem_acao":
            fala = _ancora_resultado(resultado, classe)
        elif classe == "falha":
            fala = f"Não consegui concluir a ação em {alvo}."
        elif classe == "pendente":
            fala = f"Preciso da sua confirmação antes de mexer em {alvo}."
        else:
            fala = f"Enviei o comando para {alvo}, mas não consegui confirmar a resposta."
    fala = _contextualizar_turno_misto(fala, resultado.texto_usuario)
    fala = _garantir_resultado_explicito(fala, resultado, classe)

    emocao = str(emocao_preferida or "").strip().lower()
    nivel = max(1, min(3, int(nivel_preferido or 1)))
    if classe == "falha":
        # Uma falha técnica pede clareza, não raiva automática. A emoção pode
        # vir do contexto real da conversa, mas o erro sozinho não a fabrica.
        emocao, nivel = (emocao or "calma"), 1
    elif classe in {"pendente", "incerto"}:
        emocao, nivel = "calma", 1
    elif not emocao:
        emocao, nivel = "calma", 1

    fala = estilizar_fala_operacional(
        resultado,
        fala,
        classe=classe,
        emocao=emocao,
    )
    fala = _contextualizar_turno_misto(fala, resultado.texto_usuario)

    return PlanoResposta(
        fala=fala,
        classe=classe,
        emocao=emocao,
        nivel=nivel,
        grau_compromisso=classificar_grau_compromisso(resultado.texto_usuario),
        personalidade_permitida=True,
    )
