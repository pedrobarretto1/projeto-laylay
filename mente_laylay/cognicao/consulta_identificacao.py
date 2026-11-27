"""Identificação por fonte pública, vinculada à pergunta do turno."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlsplit

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos


_IDENTIFICACAO = re.compile(
    r"(?:(?P<pessoa>quem)\s+(?:[eéèê]|foi|era)|o\s+que\s+(?:[eéèê]|foi|era))\s+"
    r"(?P<tema>[^?!.;:,«»\"“”]+)[?!.]*", re.IGNORECASE,
)
_CARGO_ATUAL = re.compile(
    r"(?:(?:o|a)\s+)?(?:atual\s+)?(?P<cargo>presidente|governador[ae]?|prefeit[oa])"
    r"\s+(?:atual\s+)?(?P<lugar>d(?:e|o|a|os|as)\s+.+)", re.IGNORECASE,
)
_MEMORIA_USUARIO = re.compile(
    r"(?:o que (?:eu (?:te )?(?:contei|disse|falei|mencionei)|"
    r"voc[eê] (?:lembra|recorda) d[eo] que eu (?:te )?(?:contei|disse|falei|mencionei)))"
    r"\s+sobre\s+(?P<tema>[^?!.;:,]+)[?!.]*", re.IGNORECASE,
)
_CONTEXTO_FICCIONAL = re.compile(
    r"\b(?:na (?:nossa|minha) (?:hist[oó]ria|fic[cç][aã]o|cena)|na fic[cç][aã]o|"
    r"no (?:nosso|meu) (?:conto|roteiro|universo fict[ií]cio))\b", re.IGNORECASE,
)


def _pergunta_simples(turno: Mapping[str, Any]) -> bool:
    return (turno.get("modalidade_geral", turno.get("modalidade")) == "pergunta"
            and turno.get("autoriza_execucao") is False
            and len(turno.get("segmentos") or ()) == 1)


def tema_identificacao(texto: str) -> str:
    achado = _IDENTIFICACAO.fullmatch(str(texto or "").strip())
    if not achado:
        return ""
    tema = achado["tema"].strip()
    return tema if 1 <= len(tema.split()) <= 8 and len(tema) <= 160 else ""


def cargo_identificacao_atual(texto: str) -> str:
    tema = tema_identificacao(texto)
    if not re.match(r"^quem\s+[eéèê]\s", texto.strip(), re.IGNORECASE):
        return ""
    achado = _CARGO_ATUAL.fullmatch(tema)
    if not achado:
        return ""
    return f"{achado['cargo']} {achado['lugar']}"


def qualificacao_identificacao_publica(texto: str, *, turno: Mapping[str, Any]) -> str:
    """A identificação aberta é só uma pergunta e não herda referência privada."""
    if not _pergunta_simples(turno):
        return ""
    tema = tema_identificacao(texto)
    if not tema_com_escopo_publico(tema):
        return ""
    return tema if "atual" not in normalizar_texto_basico(tema).split() else cargo_identificacao_atual(texto)


def tema_com_escopo_publico(tema: str) -> bool:
    base = normalizar_texto_basico(tema)
    return bool(re.fullmatch(r"[\w' -]+", base) and any(c.isalpha() for c in base) and not re.search(
        r"\b(?:meu|minha|meus|minhas|nosso|nossa|voce|tu|ele|ela|isso|esse|essa|"
        r"historia|ficcao|nos falamos|que eu|que voce|hoje|agora|melhor|pior)\b", base,
    ))


def delimitar_fonte_identificacao(texto: str, *, turno: Mapping[str, Any]) -> tuple[str, str]:
    """Extrai fonte pedida e referente, sem escolher uma evidência."""
    if not _pergunta_simples(turno):
        return "", ""
    if pedido := _MEMORIA_USUARIO.fullmatch(texto.strip()):
        return "historico", pedido["tema"].strip()
    tema = tema_identificacao(texto)
    if contexto := _CONTEXTO_FICCIONAL.search(tema):
        referente = (tema[:contexto.start()] + tema[contexto.end():]).strip()
        if referente:
            return "ficcao", referente
    tema = qualificacao_identificacao_publica(texto, turno=turno)
    return ("publica", tema) if tema else ("", "")


@dataclass(frozen=True, slots=True)
class RespostaIdentificacaoPublica:
    turno_id: str
    texto_usuario: str
    fala: str
    motivo: str
    url: str = ""
    expira_em: float = 0.0


@dataclass(frozen=True, slots=True)
class RespostaDocumentalPublicada:
    entrega_id: str
    tema: str
    documento: RespostaIdentificacaoPublica

    @classmethod
    def vincular(cls, *, entrega_id: str, turno_id: str, texto_usuario: str,
                fala: str, tema: str, documento: object) -> RespostaDocumentalPublicada | None:
        if (not entrega_id or not tema or type(documento) is not RespostaIdentificacaoPublica
                or documento.fala != fala
                or not fonte_documental_vigente(documento, turno_id=turno_id, texto=texto_usuario)):
            return None
        return cls(entrega_id, tema, documento)


def fonte_documental_vigente(
    fonte: RespostaIdentificacaoPublica | None, *, turno_id: str, texto: str,
    publicacao: RespostaDocumentalPublicada | None = None,
) -> bool:
    """Vincula o documento conferido à ocorrência que pode consumir o conteúdo."""
    if not turno_id or not texto or type(fonte) is not RespostaIdentificacaoPublica:
        return False
    if publicacao is not None:
        if (type(publicacao) is not RespostaDocumentalPublicada
                or publicacao.documento != fonte or not publicacao.entrega_id):
            return False
        turno_id, texto = publicacao.documento.turno_id, publicacao.documento.texto_usuario
    if (fonte.motivo != "identificacao_documental"
            or not turno_id or fonte.turno_id != turno_id or fonte.texto_usuario != texto
            or not fonte.fala or not time.time() < fonte.expira_em):
        return False
    url = urlsplit(fonte.url)
    return url.scheme == "https" and url.netloc == "pt.wikipedia.org" and url.path.startswith("/wiki/")


@dataclass(frozen=True, slots=True)
class RespostaIdentificacaoLocal:
    turno_id: str
    texto_usuario: str
    fala: str
    motivo: str
    trechos: tuple[str, ...]


def recuperar_identificacao_local(
    texto: str, *, turno_id: Any, escopo: str, tema: str, historico: list[Mapping[str, Any]],
) -> RespostaIdentificacaoLocal:
    """Cita o histórico literal do interlocutor, dentro da moldura pedida."""
    escolhido = normalizar_texto_basico(tema)
    trechos = []
    for mensagem in reversed(historico):
        if mensagem.get("role") != "user":
            continue
        for trecho in enunciados_discursivos(str(mensagem.get("content") or "")):
            if trecho == texto or trecho.endswith("?") or not 1 <= len(trecho) <= 360:
                continue
            ficcional = bool(_CONTEXTO_FICCIONAL.search(trecho))
            if escopo == "ficcao" and not ficcional:
                continue
            if escolhido and re.search(r"(?<!\w)" + re.escape(escolhido) + r"(?!\w)", normalizar_texto_basico(trecho)):
                if trecho not in trechos:
                    trechos.append(trecho)
        if len(trechos) >= 3:
            break
    trechos = tuple(reversed(trechos[:3]))
    if trechos:
        introducao = "Na história, você disse" if escopo == "ficcao" else "Você me contou"
        fala = f"{introducao} " + " ".join(f"«{trecho}»" for trecho in trechos)
    else:
        meio = "na nossa história" if escopo == "ficcao" else "no que você me contou"
        fala = f"Não encontrei {tema} {meio} até aqui."
    return RespostaIdentificacaoLocal(str(turno_id), texto, fala,
        "historico_encontrado" if trechos else "historico_sem_trecho", trechos)


def construir_resposta_identificacao_publica(
    texto: str, *, turno_id: Any, pesquisa: Mapping[str, Any],
    fundamentacao: Mapping[str, Any], cargo: str, tema: str = "",
) -> RespostaIdentificacaoPublica | None:
    """Realiza o ocupante do quadro lido ou uma frase integral da introdução."""
    if not turno_id:
        return None
    fontes = list(fundamentacao.get("fontes") or ())
    apoiada = fundamentacao.get("confiavel") and fontes and pesquisa.get("fonte") == "wikipedia_pt"
    if apoiada and cargo and pesquisa.get("ocupante"):
        fonte = fontes[0]
        fala = f"Segundo a Wikipédia, o cargo de {pesquisa['titulo']} é ocupado por {pesquisa['ocupante']}."
    elif apoiada and not cargo and pesquisa.get("identificacao_por_titulo") is True:
        fonte = fontes[0]
        fala = next(iter(enunciados_discursivos(fonte["trecho"], separar_ponto_e_virgula=False)), "")
        if not 20 <= len(fala) <= 450 or not fala.endswith("."):
            return None
    elif cargo and pesquisa.get("motivo") == "cargo_sem_fonte_pertinente":
        return RespostaIdentificacaoPublica(str(turno_id), texto,
            f"Não consegui confirmar quem ocupa o cargo de {cargo} agora.",
            "ocupante_nao_confirmado")
    elif tema and pesquisa.get("identificacao_ambigua") is True:
        return RespostaIdentificacaoPublica(str(turno_id), texto,
            f"Qual {tema} você quer dizer?", "referencia_ambigua")
    elif tema and not cargo:
        motivo = "pesquisa_pendente" if pesquisa.get("pesquisa_pendente") else "fonte_insuficiente"
        return RespostaIdentificacaoPublica(str(turno_id), texto,
            f"Ainda não consegui confirmar uma resposta sobre {tema}.", motivo)
    else:
        return None
    return RespostaIdentificacaoPublica(str(turno_id), texto, fala, "identificacao_documental",
        fonte["url"], float(fundamentacao.get("evidencia_expira_em") or 0.0))


def resposta_identificacao_publica_vigente(texto: str, plano: Mapping[str, Any]) -> str:
    resposta = plano.get("identificacao_publica")
    if (type(resposta) not in {RespostaIdentificacaoPublica, RespostaIdentificacaoLocal} or not plano.get("id")
            or resposta.turno_id != str(plano["id"]) or resposta.texto_usuario != texto
            or plano.get("texto_usuario") != texto or plano.get("autoriza_execucao") is not False
            or plano.get("requer_execucao") or plano.get("comandos")
            or (type(resposta) is RespostaIdentificacaoPublica and resposta.url and time.time() >= resposta.expira_em)):
        return ""
    return resposta.fala
