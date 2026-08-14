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
_SUFIXO_APLICATIVO = re.compile(
    r"\s*[-–—|]\s*(?:youtube(?:\s+music)?|opera(?:\s+gx)?|google\s+chrome|"
    r"chrome|mozilla\s+firefox|firefox|microsoft\s+edge|edge)\s*$",
    re.IGNORECASE,
)
_METADADO_MUSICAL = re.compile(
    r"\s*[\[(][^\])]*(?:official\s+(?:video|audio)|vídeo\s+oficial|video\s+oficial|"
    r"lyric(?:s)?(?:\s+video)?|letra|clipe|áudio\s+oficial|audio\s+oficial|"
    r"4k|hd)[^\])]*[\])]",
    re.IGNORECASE,
)


def _retirar_sufixos_de_aplicativo(texto: str) -> str:
    atual = str(texto or "").strip()
    anterior = None
    while atual and atual != anterior:
        anterior = atual
        atual = _SUFIXO_APLICATIVO.sub("", atual).strip(" -–—|")
    return atual


def limpar_titulo_musical_para_fala(titulo: str) -> str:
    """Transforma o título técnico do player em um nome curto para conversa.

    A URL e o título bruto continuam intactos no estado operacional. Esta
    função só prepara a apresentação, removendo contadores, nome do navegador
    e metadados editoriais inequívocos. Um único ``Radio Edit`` é preservado.
    """
    fala = _retirar_sufixos_de_aplicativo(titulo)
    fala = re.sub(r"^\s*\(\s*\d+\s*\)\s*", "", fala).strip()
    contador_separado = re.match(r"^\s*(\d+)\s*[-–:]\s*(.+)$", fala)
    if contador_separado:
        numero = contador_separado.group(1)
        parece_ano = len(numero) == 4 and 1900 <= int(numero) <= 2099
        if not parece_ano:
            fala = contador_separado.group(2).strip()
    # Contadores de fila/captura também chegam sem parênteses ou separador.
    # Só retiramos números longos diante de um título claramente descritivo,
    # preservando nomes musicais legítimos como ``1979``.
    if len(fala.split()) >= 6:
        fala = re.sub(r"^\s*\d{3,6}\s+(?=[A-Za-zÀ-ÿ])", "", fala).strip()
    fala = _METADADO_MUSICAL.sub(" ", fala)
    ocorrencias_edit = list(re.finditer(r"\bedit\b", fala, re.IGNORECASE))
    if len(ocorrencias_edit) >= 2:
        fala = fala[: ocorrencias_edit[0].start()].rstrip(" -–—|:,")
    fala = re.sub(r"\s*[-–—]\s*", " - ", fala)
    fala = re.sub(r"\s+", " ", fala).strip(" -–—|:,")
    if fala.casefold() in {
        "youtube", "youtube music", "opera", "chrome", "player",
    }:
        # Nome da plataforma não é título de faixa. Mantê-lo como se fosse
        # música fazia “Qual música está tocando?” responder “YouTube”.
        return ""
    return fala


def nome_janela_para_fala(nome: str) -> str:
    """Resume um título de janela sem alterar o alvo usado pelo executor."""
    bruto = re.sub(r"\s+", " ", str(nome or "")).strip()
    norm = bruto.casefold()
    nomes_conhecidos = (
        ("youtube", "YouTube"),
        ("visual studio code", "VS Code"),
        ("vscode", "VS Code"),
        ("spotify", "Spotify"),
        ("opera gx", "Opera GX"),
        ("opera", "Opera"),
        ("google chrome", "Chrome"),
        ("chrome", "Chrome"),
        ("mozilla firefox", "Firefox"),
        ("firefox", "Firefox"),
        ("microsoft edge", "Edge"),
        ("discord", "Discord"),
        ("steam", "Steam"),
    )
    for marcador, apresentacao in nomes_conhecidos:
        if marcador in norm:
            return apresentacao
    return _retirar_sufixos_de_aplicativo(bruto) or "a janela"


def limpar_fala_operacional(texto: str) -> str:
    """Aplica higiene conservadora a toda fala vinda de um executor.

    Não resume dados nem muda o resultado da ação. A limpeza compartilhada
    serve como última barreira contra resíduos internos e pontuação quebrada.
    Regras específicas de nomes ficam nas funções acima, antes da montagem.
    """
    fala = remover_residuos_operacionais(texto)
    # Horários também são indivisíveis nas falas dos executores. A autoria
    # operacional podia inserir um espaço em ``10:37`` depois do agendamento.
    fala = re.sub(r"\b([01]?\d|2[0-3]):\s+([0-5]\d)\b", r"\1:\2", fala)
    fala = re.sub(r"\s+([,.;:!?])", r"\1", fala)
    # Dois-pontos depois de algarismo pertencem ao horário já normalizado.
    fala = re.sub(r"([,;]|(?<!\d):)(?=\S)", r"\1 ", fala)
    return re.sub(r"\s+", " ", fala).strip()


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
