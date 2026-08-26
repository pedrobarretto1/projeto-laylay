"""Ferramentas leves para interpretar comandos da autonomia da Laylay."""

from __future__ import annotations

import re
from typing import Callable, List, Optional

from mente_laylay.cognicao.gramatica_operacional import (
    texto_pede_avanco_midia_via_vai,
)


# P0_CADEIA_MULTIETAPAS_V1_20260815
LIMITE_ETAPAS_CADEIA = 5

_INICIO_ETAPA_OPERACIONAL = re.compile(
    r"^(?:"
    r"abr(?:e|a)|fech(?:a|e)|maximiz(?:a|e)|minimiz(?:a|e)|"
    r"cri(?:a|e)|colo(?:ca|que)|bot(?:a|e)|toc(?:a|que)|"
    r"deix(?:a|e)|pass(?:a|e)|pul(?:a|e)|avan[cç](?:a|e)|"
    r"troc(?:a|e)|volt(?:a|e)|confirm(?:a|e)|confir(?:a|e)|consult(?:a|e)|"
    r"adicion(?:a|e)|acrescent(?:a|e)|salv(?:a|e)|guard(?:a|e)|anot(?:a|e)|"
    r"apag(?:a|ue)|exclu(?:i|a)|delet(?:a|e)|remov(?:e|a)|"
    r"encontr(?:a|e)|procur(?:a|e)|pesquis(?:a|e)|busc(?:a|que)|"
    r"copi(?:a|e)|escrev(?:e|a)|grav(?:a|e)|mov(?:e|a)|renomei(?:a|e)|mud(?:a|e)|"
    r"lig(?:a|ue)|deslig(?:a|ue)|paus(?:a|e)|continu(?:a|e)|"
    r"retom(?:a|e)|organiz(?:a|e)|agend(?:a|e)|cancel(?:a|e)|"
    r"(?:me\s+)?lembr(?:a|e)|resum(?:e|a)|explic(?:a|que)|"
    r"list(?:a|e)|(?:me\s+)?(?:mostr(?:a|e)|diz|diga|fal(?:a|e))"
    r")\b",
    flags=re.IGNORECASE,
)

_SEPARADOR_ETAPA_OPERACIONAL = re.compile(
    r"\be\s+depois\b|\bem\s+seguida\b|\bdepois\b|"
    r"\bent[aã]o\b|[,;]|\be\b",
    flags=re.IGNORECASE,
)


def _parece_etapa_operacional(texto: str) -> bool:
    """Aceita um corte somente quando o trecho começa como ordem operacional."""
    t = str(texto or "").strip()
    return bool(
        _INICIO_ETAPA_OPERACIONAL.match(t)
        or texto_pede_avanco_midia_via_vai(t)
    )


def limpar_resposta(texto: str) -> str:
    """Remove marcas visuais da resposta sem alterar o conteúdo semântico."""
    texto = str(texto or "")
    texto = re.sub(r"\*\*|__|\*|_", "", texto)
    texto = re.sub(r"\n+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.replace('"', "")


def segmentar_comandos_em_cadeia(
    texto: str,
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
) -> List[str]:
    """Separa uma cadeia curta de ordens sem transformar conjunções em ações."""
    bruto = str(texto or "").strip()
    if not bruto:
        return []

    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.lower()
    t = re.sub(r"[,\.!\?:;]+", " ", t)
    t = re.sub(r"\b(laylay|lay|por favor|pfv)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []

    # Os segmentos devolvidos continuam vindo da fala original: nomes,
    # resultado.md, URLs, aspas e pontuação interna não podem ser destruídos
    # pela cópia usada apenas para reconhecer o começo de cada ordem.
    bruto_operacional = re.sub(
        r"\b(laylay|lay|por favor|pfv)\b", " ", bruto,
        flags=re.IGNORECASE,
    )
    bruto_operacional = re.sub(
        r"^(?:eu\s+)?(?:quero|gostaria)\s+que\s+(?:voce|você)\s+",
        "",
        bruto_operacional,
        count=1,
        flags=re.IGNORECASE,
    )
    bruto_operacional = re.sub(r"\s+", " ", bruto_operacional).strip()
    normalizar = normalizar_texto if callable(normalizar_texto) else str.lower

    def normalizar_etapa(parte: str) -> str:
        return str(normalizar(parte) or "").strip(" .,!?;:")

    partes: List[str] = []
    inicio = 0

    # Um separador só vira fronteira quando o trecho acumulado à esquerda e o
    # restante à direita começam como ordens operacionais. Isso permite
    # "liga X, deixa azul e depois me diz..." sem cortar enumerações como
    # "liga a luz e o ventilador" ou "coloca vermelho, azul e verde".
    for encontrado in _SEPARADOR_ETAPA_OPERACIONAL.finditer(bruto_operacional):
        esquerda = bruto_operacional[inicio:encontrado.start()].strip(" .,!?;:")
        direita = bruto_operacional[encontrado.end():].strip(" .,!?;:")
        if not esquerda or not direita:
            continue
        # ``só então me diga o resultado`` conclui a verificação anterior;
        # não representa um quarto efeito operacional independente. Mantemos
        # a cláusula junto da consulta que precisa produzir esse resultado.
        if (
            re.fullmatch(r"ent[aã]o", encontrado.group(0), flags=re.IGNORECASE)
            and re.search(r"\bs[oó]\s*$", esquerda, flags=re.IGNORECASE)
            and re.match(
                r"(?:me\s+)?(?:diz|diga|fala|fale)\s+(?:o\s+)?resultado\b",
                direita,
                flags=re.IGNORECASE,
            )
        ):
            continue
        if not _parece_etapa_operacional(normalizar_etapa(esquerda)):
            continue
        if not _parece_etapa_operacional(normalizar_etapa(direita)):
            continue

        # Nunca executamos somente o começo de uma cadeia longa. Acima do
        # limite, o texto volta inteiro ao fluxo normal para não haver sucesso
        # parcial silencioso.
        if len(partes) + 2 > LIMITE_ETAPAS_CADEIA:
            return [t]

        partes.append(esquerda)
        inicio = encontrado.end()

    if partes:
        final = bruto_operacional[inicio:].strip(" ,!?;:")
        # Em uma etapa comum, o ponto final é apenas pontuação da ordem. Quando
        # há um nome com extensão, porém, a fala original precisa permanecer
        # intacta para não confundir ``resultado.md`` com texto sem extensão.
        if not re.search(r"\.[a-z0-9][a-z0-9_-]{0,15}\b", final, re.IGNORECASE):
            final = final.rstrip(".")
        if final and _parece_etapa_operacional(normalizar_etapa(final)):
            partes.append(final)
            if 2 <= len(partes) <= LIMITE_ETAPAS_CADEIA:
                return partes

    return [t]


def executar_comando_em_texto(
    texto: str,
    origem: str = "",
    *,
    detectar_repetir_briefing: Optional[Callable[[str], bool]] = None,
    repetir_briefing: Optional[Callable[[], object]] = None,
    processar_comando_deterministico: Optional[Callable[[str, str], bool]] = None,
    interpretar_comando_local_rapido: Optional[Callable[[str], object]] = None,
    executar_intencao: Optional[Callable[[object, str], object]] = None,
    log: Callable[[str], object] = print,
) -> bool:
    """Executa um trecho de comando textual usando callbacks do cérebro principal."""
    t = str(texto or "").strip()
    if not t:
        return False

    if callable(detectar_repetir_briefing) and detectar_repetir_briefing(t):
        if callable(repetir_briefing):
            repetir_briefing()
        return True

    if callable(processar_comando_deterministico) and processar_comando_deterministico(t, origem):
        return True

    comando_local = interpretar_comando_local_rapido(t) if callable(interpretar_comando_local_rapido) else None
    if comando_local:
        try:
            return bool(executar_intencao(comando_local, t)) if callable(executar_intencao) else False
        except Exception as e:
            log(f"⚠️ [COMANDO LOCAL] falha ao executar: {e}")
            return False

    return False


def processar_comandos_em_cadeia(
    texto: str,
    origem: str = "",
    *,
    normalizar_texto: Optional[Callable[[str], str]] = None,
    segmentar: Callable[..., List[str]] = segmentar_comandos_em_cadeia,
    executar_trecho: Optional[Callable[[str, str], bool]] = None,
    relatar_falha: Optional[Callable[[str, int, int], object]] = None,
) -> bool:
    """Executa uma cadeia curta em ordem e interrompe na primeira falha."""
    partes = segmentar(texto, normalizar_texto=normalizar_texto)
    if len(partes) < 2 or len(partes) > LIMITE_ETAPAS_CADEIA:
        return False

    tag = origem or "cadeia"
    for idx, parte in enumerate(partes, start=1):
        executou = bool(
            callable(executar_trecho)
            and executar_trecho(parte, f"{tag}-{idx}")
        )
        if not executou:
            if callable(relatar_falha):
                relatar_falha(parte, idx, idx - 1)
            # Etapas posteriores podem depender do resultado que faltou. Não
            # avançamos nem declaramos o composto concluído pela metade.
            break

    # A cadeia foi reconhecida e consumida, mesmo quando uma etapa falhou. A
    # falha já foi relatada acima; devolver False faria o fluxo reprocessar a
    # frase inteira e poderia duplicar as etapas que tiveram sucesso.
    return True
