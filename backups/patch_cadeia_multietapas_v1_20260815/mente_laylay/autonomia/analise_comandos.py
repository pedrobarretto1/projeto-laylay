"""Ferramentas leves para interpretar comandos da autonomia da Laylay."""

from __future__ import annotations

import re
from typing import Callable, List, Optional


_INICIO_ETAPA_OPERACIONAL = re.compile(
    r"^(?:"
    r"abr(?:e|a)|fech(?:a|e)|maximiz(?:a|e)|minimiz(?:a|e)|"
    r"cri(?:a|e)|coloc(?:a|que)|bot(?:a|e)|toc(?:a|que)|"
    r"adicion(?:a|e)|salv(?:a|e)|guard(?:a|e)|anot(?:a|e)|"
    r"apag(?:a|ue)|exclu(?:i|a)|delet(?:a|e)|remov(?:e|a)|"
    r"encontr(?:a|e)|procur(?:a|e)|pesquis(?:a|e)|busc(?:a|que)|"
    r"copi(?:a|e)|escrev(?:e|a)|grav(?:a|e)|mov(?:e|a)|renomei(?:a|e)|mud(?:a|e)|"
    r"lig(?:a|ue)|deslig(?:a|ue)|paus(?:a|e)|continu(?:a|e)|"
    r"retom(?:a|e)|organiz(?:a|e)|agend(?:a|e)|cancel(?:a|e)|"
    r"(?:me\s+)?lembr(?:a|e)|resum(?:e|a)|explic(?:a|que)|"
    r"mostr(?:a|e)|list(?:a|e)|diz|diga|fal(?:a|e)"
    r")\b",
    flags=re.IGNORECASE,
)


def _parece_etapa_operacional(texto: str) -> bool:
    """Limita o ``e`` simples a duas ordens, sem cortar conversa comum."""
    return bool(_INICIO_ETAPA_OPERACIONAL.match(str(texto or "").strip()))


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
    """Separa comandos naturais em até duas etapas encadeadas."""
    bruto = str(texto or "").strip()
    if not bruto:
        return []

    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.lower()
    t = re.sub(r"[,\.!\?:;]+", " ", t)
    t = re.sub(r"\b(laylay|lay|por favor|pfv)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return []

    # Localizamos o conector na fala original. A cópia normalizada serve só
    # para reconhecer verbos; devolver seus segmentos destruiria argumentos
    # como ``resultado.md``, URLs, aspas e nomes com pontuação.
    bruto_operacional = re.sub(
        r"\b(laylay|lay|por favor|pfv)\b", " ", bruto,
        flags=re.IGNORECASE,
    )
    bruto_operacional = re.sub(r"\s+", " ", bruto_operacional).strip()
    for sep in (r"\be depois\b", r"\bem seguida\b", r"\bdepois\b", r"\bent[aã]o\b"):
        encontrado = re.search(sep, bruto_operacional, flags=re.IGNORECASE)
        if encontrado:
            partes_brutas = [
                bruto_operacional[:encontrado.start()].strip(" .,!?;:"),
                bruto_operacional[encontrado.end():].strip(" .,!?;:"),
            ]
            normalizar = normalizar_texto if callable(normalizar_texto) else str.lower
            partes_operacionais = [
                str(normalizar(parte) or "").strip(" .,!?;:")
                for parte in partes_brutas
            ]
            # ``depois`` também é marcador temporal em hipóteses e adiamentos.
            # Só existe cadeia quando os dois lados são ordens completas. Isso
            # impede que ``Talvez eu apague X depois.`` seja consumido como
            # uma execução e que o ponto final vire uma etapa fantasma.
            if (
                all(partes_brutas)
                and all(_parece_etapa_operacional(parte) for parte in partes_operacionais)
            ):
                return partes_brutas[:2]

    # O conectivo simples também forma uma cadeia quando ambos os lados são
    # ordens reconhecíveis ("cria a pasta e coloca um arquivo nela"). A
    # validação dos dois verbos impede falsos cortes em frases como
    # "você prefere rock e metal?" ou "liga a luz e o ventilador".
    for encontrado in re.finditer(r"\be\b", bruto_operacional, flags=re.IGNORECASE):
        esquerda_bruta = bruto_operacional[:encontrado.start()].strip(" ,!?;:")
        direita_bruta = bruto_operacional[encontrado.end():].strip(" ,!?;:")
        normalizar = normalizar_texto if callable(normalizar_texto) else str.lower
        esquerda = str(normalizar(esquerda_bruta) or "").strip()
        direita = str(normalizar(direita_bruta) or "").strip()
        if _parece_etapa_operacional(esquerda) and _parece_etapa_operacional(direita):
            return [esquerda_bruta, direita_bruta]

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
    """Executa comandos naturais encadeados, mantendo compatibilidade com o fluxo antigo."""
    partes = segmentar(texto, normalizar_texto=normalizar_texto)
    if len(partes) < 2:
        return False

    tag = origem or "cadeia"
    for idx, parte in enumerate(partes[:2], start=1):
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
