"""Higiene final para impedir que artefatos internos cheguem à fala."""

from __future__ import annotations

import re


_DIRETIVA_OPERACIONAL = re.compile(
    r"\[\s*\.?\s*(?:abre|abrir|toca|toque|tocar|coloca|coloque|botar|bota|"
    r"cria|criar|execute|executar|play|pause|fecha|fechar|liga|ligar|desliga|"
    r"desligar)\b[^\]]*\]",
    re.IGNORECASE,
)
_MARCADOR_MODELO = re.compile(r"(?<![\w])LYL(?![\w])", re.IGNORECASE)
_MARCADOR_ESQUEMA = re.compile(
    r"(?:\[\s*(?:fala|tipo_interacao|leitura_turno|comandos|aprendizados?|humor)\s*\]\s*:|"
    r"(?<!\w)(?:tipo_interacao|leitura_turno|comandos|aprendizados?|humor)\s*:)",
    re.IGNORECASE,
)
_TRECHO_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_MARCADOR_DADOS_VISUAIS = re.compile(
    r"DADOS_(?:ITEM|HABILIDADE|INVENTARIO|INVENTÁRIO)_JSON\s*:", re.IGNORECASE,
)
_CAUDA_JSON_VISUAL = re.compile(
    r",?\s*[\"'](?:slot|categoria|raridade|atributos|confianca|confiança)[\"']\s*:",
    re.IGNORECASE,
)
_PALAVRA_PENDURADA = re.compile(
    r"\b(?:e|mas|ou|porque|pois|que|de|do|da|dos|das|em|no|na|nos|nas|"
    r"com|sem|para|pra|por|pelo|pela|um|uma|uns|umas)\s*[.!?…]*$",
    re.IGNORECASE,
)


def remover_fragmento_final_incompleto(texto: str) -> str:
    """Descarta somente a última oração quando ela termina num conector solto.

    É uma defesa pequena para respostas interrompidas pelo provedor. Não tenta
    adivinhar gramática geral: atua apenas em finais inequivocamente pendurados,
    como ``"Vejo que você e."``. Se não houver uma frase completa anterior, a
    fala fica vazia para o chamador permanecer em silêncio ou tentar novamente.
    """
    fala = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not fala or not _PALAVRA_PENDURADA.search(fala):
        return fala
    anterior = list(re.finditer(r"[.!?…](?=\s+)", fala))
    if not anterior:
        return ""
    return fala[: anterior[-1].end()].strip()


def remover_residuos_operacionais(texto: str) -> str:
    """Remove pseudo-comandos e marcadores que nunca são texto para o usuário."""
    fala = str(texto or "")
    fala = _DIRETIVA_OPERACIONAL.sub(" ", fala)
    fala = _MARCADOR_MODELO.sub(" ", fala)
    marcador_visual = _MARCADOR_DADOS_VISUAIS.search(fala)
    if marcador_visual:
        fala = fala[:marcador_visual.start()]
    # Defesa final para respostas truncadas que perderam o início do marcador,
    # mas ainda carregam campos técnicos depois da frase natural.
    cauda_visual = _CAUDA_JSON_VISUAL.search(fala)
    if cauda_visual and len(fala[:cauda_visual.start()].split()) >= 3:
        fala = fala[:cauda_visual.start()].rstrip(" ,;:-{")
    # Modelos locais às vezes concluem a fala e continuam imprimindo o
    # contrato interno em formato pseudo-JSON: ``[fala]: ... [comandos]:``.
    # Tudo a partir do primeiro campo estrutural é metadado, nunca fala.
    marcador = _MARCADOR_ESQUEMA.search(fala)
    if marcador:
        fala = fala[:marcador.start()]
    # Remove uma cauda curta em outro sistema de escrita quando ela aparece
    # grudada em uma resposta predominantemente latina. Não altera nomes ou
    # respostas inteiras em outro idioma; atua somente na contaminação final.
    cjk = _TRECHO_CJK.search(fala)
    if cjk and len(re.findall(r"[A-Za-zÀ-ÿ]", fala[:cjk.start()])) >= 12:
        fala = fala[:cjk.start()].rstrip(" \t\r\n,;:-")
    fala = re.sub(r"\[\s*\]", " ", fala)
    fala = re.sub(r"\s+([,.;:!?])", r"\1", fala)
    fala = re.sub(r"([.!?])(?:\s*\1)+", r"\1", fala)
    # Uma geração interrompida pode deixar apenas o início da próxima
    # palavra como uma falsa frase final (por exemplo: ``... nostalgia. H.``).
    # Só removemos a letra isolada quando já existe uma resposta substancial,
    # preservando iniciais legítimas em respostas curtas.
    if len(fala.split()) >= 5:
        fala = re.sub(r"\s+[A-Za-zÀ-ÿ]\.\s*$", "", fala).rstrip()
    fala = re.sub(r"\s+", " ", fala).strip()
    return remover_fragmento_final_incompleto(fala)
