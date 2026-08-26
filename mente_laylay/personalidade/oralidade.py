"""Conversão de texto estruturado em prosa adequada para síntese de voz."""

from __future__ import annotations

import re
from urllib.parse import urlparse


_CONECTORES_ETAPA = {
    1: "Primeiro",
    2: "Depois",
    3: "Em seguida",
    4: "Na sequência",
    5: "Por fim",
}


def _expandir_unidades(texto: str) -> str:
    s = str(texto or "")
    # Unidades compostas precisam vir antes das simples; caso contrário,
    # ``10 km/h`` viraria o híbrido oral ``10 quilômetros/h``.
    s = re.sub(r"(?<=\d)\s*km\s*/\s*h\b", " quilômetros por hora", s, flags=re.IGNORECASE)
    s = re.sub(r"(?<=\d)\s*m\s*/\s*s\b", " metros por segundo", s, flags=re.IGNORECASE)
    unidades = (
        (r"(?<=\d)\s*kg\b", " quilogramas"),
        (r"(?<=\d)\s*mg\b", " miligramas"),
        (r"(?<=\d)\s*g\b", " gramas"),
        (r"(?<=\d)\s*ml\b", " mililitros"),
        (r"(?<=\d)\s*l\b", " litros"),
        (r"(?<=\d)\s*cm\b", " centímetros"),
        (r"(?<=\d)\s*mm\b", " milímetros"),
        (r"(?<=\d)\s*km\b", " quilômetros"),
        (r"(?<=\d)\s*min\b", " minutos"),
        (r"(?<=\d)\s*h\b", " horas"),
    )
    for padrao, substituto in unidades:
        s = re.sub(padrao, substituto, s, flags=re.IGNORECASE)
    s = re.sub(r"(?<=\d)\s*°\s*C\b", " graus Celsius", s, flags=re.IGNORECASE)
    s = re.sub(r"\b1/2\s+(?=(?:colher|x[ií]cara|copo|litro))", "meia ", s, flags=re.IGNORECASE)
    s = re.sub(r"\b1/3\s+(?=(?:de\s+)?(?:colher|x[ií]cara|copo|litro))", "um terço de ", s, flags=re.IGNORECASE)
    s = re.sub(r"\b1/4\s+(?=(?:de\s+)?(?:colher|x[ií]cara|copo|litro))", "um quarto de ", s, flags=re.IGNORECASE)
    s = re.sub(r"\b3/4\s+(?=(?:de\s+)?(?:colher|x[ií]cara|copo|litro))", "três quartos de ", s, flags=re.IGNORECASE)
    s = re.sub(r"\b1\s+(?=x[ií]cara\b)", "uma ", s, flags=re.IGNORECASE)
    s = re.sub(r"\b1\s+(?=(?:ovo|dente|copo|litro|quilo|minuto|hora)\b)", "um ", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()


def _limpar_markdown_inline(texto: str) -> str:
    s = str(texto or "")
    s = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"(?<!\w)[*_~`]{1,3}", "", s)
    s = re.sub(r"[*_~`]{1,3}(?!\w)", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _item_rotulo_valor(item: str) -> str:
    limpo = _expandir_unidades(_limpar_markdown_inline(item)).strip(" .;:")
    if not limpo:
        return ""
    if ":" not in limpo:
        return limpo
    rotulo, valor = [parte.strip() for parte in limpo.split(":", 1)]
    if not rotulo or not valor:
        return limpo.replace(":", ",", 1)

    medida = bool(re.match(
        r"^(?:\d+(?:[.,]\d+)?|meia|um terço|um quarto|três quartos)\b",
        valor,
        flags=re.IGNORECASE,
    ))
    if not medida:
        return f"{rotulo}, {valor}"

    parenteses = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", valor)
    if parenteses:
        principal = parenteses.group(1).strip()
        alternativa = _expandir_unidades(parenteses.group(2).strip())
        return f"{principal} de {rotulo.casefold()}, ou {alternativa}"

    alternativa = re.match(r"^(.+?)\s+ou\s+(.+)$", valor, flags=re.IGNORECASE)
    if alternativa:
        principal = alternativa.group(1).strip()
        opcao = alternativa.group(2).strip()
        return f"{principal} de {rotulo.casefold()}, ou {opcao}"

    if re.fullmatch(r"\d+", valor) and rotulo.casefold().endswith("s"):
        return f"{valor} {rotulo.casefold()}"
    return f"{valor} de {rotulo.casefold()}"


def _separar_estrutura(texto: str) -> list[str]:
    s = str(texto or "").replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(
        r"\s+\*{1,2}(Ingredientes|Modo de preparo|Preparo|Materiais|Requisitos|Etapas)\s*:?\*{0,2}\s*",
        r"\n### \1\n",
        s,
        flags=re.IGNORECASE,
    )
    # Alguns modelos devolvem Markdown inteiro em uma linha. Preserva os
    # marcadores como limites antes que a limpeza de espaços os apague.
    s = re.sub(r"\s+(?=#{1,6}\s+)", "\n", s)
    # Hífen também separa artista e música. Só o convertemos em marcador
    # inline quando há uma seção estrutural clara; listas já quebradas por
    # linha continuam sendo reconhecidas normalmente no laço abaixo.
    if re.search(
        r"\b(?:ingredientes|materiais|requisitos|etapas|preparo|"
        r"modo\s+de\s+preparo)\b[^\n]{0,120}:?\s+-\s+",
        s,
        flags=re.IGNORECASE,
    ):
        s = re.sub(r"\s+(?=-\s+(?:\*{1,2})?[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", "\n", s)
    # Um número de equação seguido de ponto ("+ 9. Na segunda...") não é uma
    # etapa numerada. Só quebramos lista inline quando há pontuação estrutural
    # imediatamente antes do número.
    s = re.sub(
        r"(?<=[\.:!?])\s+(?=\d+[.)]\s+(?:\*{1,2})?[A-ZÁÉÍÓÚÂÊÔÃÕÇ])",
        "\n", s,
    )
    return [linha.strip() for linha in s.split("\n") if linha.strip()]


def naturalizar_texto_para_fala(texto: str) -> str:
    """Transforma Markdown, listas, medidas e etapas em frases pronunciáveis."""
    linhas = _separar_estrutura(texto)
    if not linhas:
        return ""

    saida: list[str] = []
    secao_ingredientes = False
    primeiro_ingrediente = True

    for linha in linhas:
        cabecalho = re.match(r"^#{1,6}\s+(.+)$", linha)
        if cabecalho:
            titulo = _limpar_markdown_inline(cabecalho.group(1)).strip(" .:")
            secao_ingredientes = "ingrediente" in titulo.casefold()
            primeiro_ingrediente = True
            if secao_ingredientes:
                saida.append("Agora, os ingredientes.")
            elif titulo:
                saida.append(f"{titulo}.")
            continue

        etapa = re.match(r"^(\d+)[.)]\s+(.+)$", linha)
        if etapa:
            numero = int(etapa.group(1))
            conteudo = _expandir_unidades(_limpar_markdown_inline(etapa.group(2))).strip(" .:")
            if conteudo:
                conteudo = conteudo[0].lower() + conteudo[1:]
            conector = _CONECTORES_ETAPA.get(numero, f"Na etapa {numero}")
            if conteudo:
                saida.append(f"{conector}, {conteudo}.")
            secao_ingredientes = False
            continue

        item = re.match(r"^[-*•]\s+(.+)$", linha)
        if item:
            conteudo = _item_rotulo_valor(item.group(1))
            if not conteudo:
                continue
            if secao_ingredientes:
                prefixo = "Você vai precisar de" if primeiro_ingrediente else "Também vai precisar de"
                saida.append(f"{prefixo} {conteudo}.")
                primeiro_ingrediente = False
            else:
                saida.append(f"{conteudo}.")
            continue

        limpo = _expandir_unidades(_limpar_markdown_inline(linha)).strip()
        if limpo:
            if limpo[-1] not in ".!?…":
                limpo += "."
            saida.append(limpo)

    fala = " ".join(saida)
    fala = re.sub(r"\bumidade\s*:\s*(?=\d)", "umidade em ", fala, flags=re.IGNORECASE)
    fala = re.sub(r"\bvento\s*:\s*(?=\d)", "vento de ", fala, flags=re.IGNORECASE)
    fala = re.sub(r"\b(?:temperatura|sensação|sensacao)\s*:\s*(?=\d)", lambda m: m.group(0).replace(":", " em"), fala, flags=re.IGNORECASE)
    fala = re.sub(r"\b(?:CPU|RAM|memória|memoria|volume)\s*:\s*(?=\d)", lambda m: m.group(0).replace(":", " em"), fala, flags=re.IGNORECASE)
    # Na síntese, ponto e vírgula costuma produzir uma pausa dura e artificial.
    fala = re.sub(r";\s*", ". ", fala)
    fala = re.sub(r"\s+([,.!?;:])", r"\1", fala)
    fala = re.sub(r"([!?])\s*\.", r"\1", fala)
    fala = re.sub(r"(?:\.\s*){2,}", ". ", fala)
    return re.sub(r"\s+", " ", fala).strip()


def _oralizar_matematica(texto: str) -> str:
    """Converte notação matemática em palavras somente na cópia para o TTS."""
    s = str(texto or "").replace("–", "-").replace("—", "-").replace("−", "-")
    urls: list[str] = []

    def proteger_url(match: re.Match) -> str:
        urls.append(match.group(0))
        return f"URLPROTEGIDA{len(urls) - 1}"

    # Sinais presentes em query strings não são operadores matemáticos.
    s = re.sub(r"https?://[^\s)]+", proteger_url, s, flags=re.IGNORECASE)
    s = re.sub(
        r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}",
        r"\1 dividido por \2",
        s,
        flags=re.IGNORECASE,
    )
    s = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"raiz quadrada de \1", s, flags=re.IGNORECASE)
    s = re.sub(r"\\(?:times|cdot)\b|×", " vezes ", s, flags=re.IGNORECASE)
    s = re.sub(r"\\div\b|÷", " dividido por ", s, flags=re.IGNORECASE)
    s = s.replace(r"\(", " ").replace(r"\)", " ")
    s = s.replace(r"\[", " ").replace(r"\]", " ").replace("$", " ")
    s = re.sub(r"\s*=\s*", " é igual a ", s)
    s = re.sub(r"\s*\+\s*", " mais ", s)
    s = re.sub(r"(?<=[\d)xyzXYZ])\s*-\s*(?=[\d(xyzXYZ])", " menos ", s)
    s = re.sub(r"(?<![\w)])-\s*(?=\d)", "menos ", s)
    s = re.sub(r"\s*\^\s*", " elevado a ", s)
    s = re.sub(r"(?<=\d)\s*(?=[xyzXYZ]\b)", " ", s)

    for indice, url in enumerate(urls):
        s = s.replace(f"URLPROTEGIDA{indice}", url)
    return re.sub(r"\s+", " ", s).strip()


def preparar_texto_para_tts(texto: str) -> str:
    """Cria uma versão oral sem modificar o texto exibido ou memorizado."""
    texto_oral = str(texto or "")

    inventario = re.fullmatch(
        r"\s*Suas playlists são:\s*(?P<itens>.+?)\.\s*",
        texto_oral,
        flags=re.IGNORECASE,
    )
    if inventario:
        itens = re.findall(
            r"(?:^|,\s*)([^,()]+?)\s*\(\s*\d+\s*\)",
            str(inventario.group("itens") or ""),
        )
        nomes = [re.sub(r"\s+", " ", nome).strip() for nome in itens if nome.strip()]
        if nomes:
            if len(nomes) == 1:
                enumeracao = nomes[0]
            elif len(nomes) == 2:
                enumeracao = f"{nomes[0]} e {nomes[1]}"
            else:
                enumeracao = f"{', '.join(nomes[:-1])} e {nomes[-1]}"
            texto_oral = f"Você tem {len(nomes)} playlists: {enumeracao}."

    if re.search(r"\bplaylist\b", texto_oral, flags=re.IGNORECASE):
        # Rótulos editoriais do YouTube ajudam na tela, mas soam como lixo
        # quando a assistente lê os títulos em voz alta.
        texto_oral = re.sub(
            r"\s*\((?:official|oficial|music\s+video|vídeo|video|audio|áudio|"
            r"lyrics?|lyric\s+video|clipe|hd|4k)[^)]*\)",
            "",
            texto_oral,
            flags=re.IGNORECASE,
        )
        texto_oral = re.sub(
            r"\b(?:official|oficial)\s+(?:music\s+)?(?:video|vídeo|audio|áudio)\b|"
            r"\b(?:HD|4K|lyrics?|lyric\s+video)\b",
            "",
            texto_oral,
            flags=re.IGNORECASE,
        )
        # Para o TTS, “artista, com música” cria uma pausa natural. O texto
        # visual continua exibindo o título original com hífen.
        texto_oral = re.sub(r"\s+[-–—]\s+", ", com ", texto_oral)
        texto_oral = re.sub(r"\s+([,.;:])", r"\1", texto_oral)
        texto_oral = re.sub(r"\s+", " ", texto_oral).strip()

    texto_oral = _oralizar_matematica(texto_oral)
    fala = naturalizar_texto_para_fala(texto_oral)
    if not fala:
        return ""
    fala = re.sub(r"(?<=\d)\s*%", " por cento", fala)
    fala = re.sub(
        r"\b(ensolarado|nublado|chuvoso|chovendo|limpo|encoberto)\s*,?\s*"
        r"(\d+(?:[.,]\d+)?\s+graus(?:\s+Celsius)?)",
        r"\1, com \2",
        fala,
        flags=re.IGNORECASE,
    )
    fala = re.sub(
        r",?\s+(umidade\s+em\s+\d+(?:[.,]\d+)?\s+por\s+cento)",
        r", com \1",
        fala,
        flags=re.IGNORECASE,
    )
    fala = re.sub(
        r"\bCPU\s+em\s+", "o processador em ", fala, flags=re.IGNORECASE,
    )
    fala = re.sub(
        r"\bRAM\s+em\s+", "a memória RAM em ", fala, flags=re.IGNORECASE,
    )
    fala = re.sub(
        r"\b(\d{1,2}):00\b", r"\1 horas", fala,
    )
    fala = re.sub(
        r"\b(\d{1,2}):(\d{2})\b", r"\1 horas e \2 minutos", fala,
    )

    def oralizar_url(match: re.Match) -> str:
        bruto = match.group(0).rstrip(".,;!?")
        try:
            host = urlparse(bruto).netloc or bruto
        except Exception:
            host = bruto
        host = re.sub(r"^www\.", "", host, flags=re.IGNORECASE)
        return host.replace(".", " ponto ").replace("-", " hífen ")

    fala = re.sub(r"https?://[^\s)]+", oralizar_url, fala, flags=re.IGNORECASE)
    fala = re.sub(r"\s*\(([^()]{1,100})\)", r", \1,", fala)
    # Duas perguntas consecutivas soam como interrogatório. Mantém a última
    # entonação e transforma as anteriores em pausas conclusivas.
    if fala.count("?") > 1:
        ultima = fala.rfind("?")
        fala = fala[:ultima].replace("?", ".") + fala[ultima:]
    fala = re.sub(r",\s*,+", ",", fala)
    fala = re.sub(r"\s+([,.!?])", r"\1", fala)
    fala = re.sub(r"\s+", " ", fala).strip()
    return fala
