"""Gramática musical estreita para classificação de atos.

Este módulo reconhece somente formas linguísticas musicais explícitas ou
guardas conservadoras do próprio domínio. Ele não resolve contexto, não escolhe
executor e não concede autoridade fora do contrato retornado.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


def normalizar_gramatica_musical(texto: str) -> str:
    """Normalização estrutural conservadora; preserva pontuação semântica."""
    bruto = str(texto or "").casefold()
    base = unicodedata.normalize("NFKD", bruto)
    sem_acentos = "".join(ch for ch in base if not unicodedata.combining(ch))
    sem_acentos = re.sub(r"[“”\"']", " ", sem_acentos)
    sem_acentos = re.sub(r"[^a-z0-9_?.,!;:\s-]", " ", sem_acentos)
    return re.sub(r"\s+", " ", sem_acentos).strip()


@dataclass(frozen=True)
class AnaliseGramaticalMusical:
    classe: str
    operacao: str = ""
    evidencia_diretiva: bool = False
    depende_contexto: bool = False
    dominio_explicito: bool = False
    somente_leitura: bool = False
    regra: str = ""
    motivo: str = ""
    normalizado: str = ""


def _resultado(
    *,
    texto: str,
    classe: str,
    operacao: str = "",
    evidencia_diretiva: bool = False,
    depende_contexto: bool = False,
    dominio_explicito: bool = False,
    somente_leitura: bool = False,
    regra: str,
    motivo: str,
) -> AnaliseGramaticalMusical:
    return AnaliseGramaticalMusical(
        classe=classe,
        operacao=operacao,
        evidencia_diretiva=evidencia_diretiva,
        depende_contexto=depende_contexto,
        dominio_explicito=dominio_explicito,
        somente_leitura=somente_leitura,
        regra=regra,
        motivo=motivo,
        normalizado=texto,
    )


_RELEVANCIA_MUSICAL = re.compile(
    r"\b(?:"
    r"musica|musicas|faixa|faixas|playlist|playlists|som|midia|"
    r"toca|toque|tocar|coloca|coloque|colocar|"
    r"pausa|pause|pausar|retoma|retome|retomar|"
    r"continua|continue|continuar|"
    r"proxima|anterior|repete|repita|repetir|despausa|pula|pule"
    r")\b",
    re.IGNORECASE,
)


def texto_tem_relevancia_musical(texto: str) -> bool:
    """Relevância serve para escopo de guard; nunca equivale a jurisdição."""
    normalizado = normalizar_gramatica_musical(texto)
    if _RELEVANCIA_MUSICAL.search(normalizado):
        return True
    # ``bota`` só é verbo musical quando ocupa a moldura diretiva. No meio de
    # uma pergunta como ``essa bota é boa?`` é um substantivo do domínio do
    # jogo e não pode entregar ownership à gramática musical.
    return bool(re.match(r"^(?:por\s+favor\s+)?bota\b", normalizado))


# Molduras que explicitamente NÃO são ordens atuais.
_NEGACAO_INICIAL = re.compile(
    r"^(?:nao|nem|nunca|jamais)\b",
    re.IGNORECASE,
)
_HIPOTESE_OU_RELATO = re.compile(
    r"^(?:"
    r"talvez\b|seria\b|quem sabe\b|"
    r"se\b|caso\b|"
    r"eu\s+(?:gosto|gostaria|acho|penso|prefiro|sempre|costumo|queria\s+saber)\b|"
    r"(?:ele|ela|isso|essa|esse|este|esta|o youtube|a playlist|essa playlist)\b|"
    r"quando\b|ontem\b|hoje\b.*\b(?:eu|ele|ela)\b"
    r")",
    re.IGNORECASE,
)
_PERGUNTA_NAO_STATUS = re.compile(
    r"^(?:"
    r"por que\b|porque\b|quando\b|como\b|"
    r"o que acontece\b|"
    r"voce sabe\b|"
    r"se\b.*\?"
    r")",
    re.IGNORECASE,
)

# Consultas de estado musical são leitura, não mutação.
_STATUS = re.compile(
    r"^(?:"
    r"qual\s+(?:musica|faixa)\s+(?:esta|ta)\s+tocando|"
    r"o\s+que\s+(?:esta|ta)\s+tocando|"
    r"que\s+(?:musica|faixa)\s+(?:e|eh)\s+(?:essa|esta)|"
    r"qual\s+(?:e|eh)\s+a\s+(?:musica|faixa)\s+atual"
    r")\s*[?!.]*$",
    re.IGNORECASE,
)

# Playlists explícitas: verbo diretivo no começo + objeto playlist.
_PLAYLIST_PLAY = re.compile(
    r"^(?:por favor\s+)?"
    r"(?:toca|toque|coloca|coloque|bota|ponha|poe|abre|abra)\s+"
    r"(?:a\s+)?playlist\s+.+?[?!.]*$",
    re.IGNORECASE,
)

# Controles explícitos com domínio musical nomeado.
_PAUSA_EXPLICITA = re.compile(
    r"^(?:por favor\s+)?"
    r"(?:pausa|pause|pare|para)\s+"
    r"(?:a\s+)?(?:musica|faixa|som)[?!.]*$",
    re.IGNORECASE,
)
_RETOMA_EXPLICITA = re.compile(
    r"^(?:por favor\s+)?"
    r"(?:retoma|retome|continua|continue|despausa)\s+"
    r"(?:(?:a\s+)?(?:musica|faixa|som)|a\s+tocar)[?!.]*$",
    re.IGNORECASE,
)
_PROXIMA_EXPLICITA = re.compile(
    r"^(?:por favor\s+)?(?:"
    r"(?:vai|pula|passa)\s+(?:(?:para|pra)\s+)?(?:a\s+)?"
    r"(?:proxima)\s+(?:musica|faixa)|"
    r"(?:proxima)\s+(?:musica|faixa)"
    r")[?!.]*$",
    re.IGNORECASE,
)
_ANTERIOR_EXPLICITA = re.compile(
    r"^(?:por favor\s+)?(?:"
    r"(?:volta|retorna|retome)\s+(?:(?:para|pra)\s+)?(?:a\s+)?"
    r"(?:musica|faixa)\s+anterior|"
    r"(?:volta|retorna)\s+(?:(?:para|pra)\s+)?(?:a\s+)?anterior|"
    r"(?:volta|volte|retorna|retorne)\s+(?:para|pra)\s+"
    r"(?:a\s+)?(?:(?:musica|faixa)\s+)?de\s+antes"
    r")[?!.]*$",
    re.IGNORECASE,
)

# Repetição com dêitico: a operação é atual, mas o referente vem do contexto.
_REPETIR_ELIPTICA = re.compile(
    r"^(?:por favor\s+)?(?:"
    r"repete|repita|"
    r"toca|toque"
    r")\s+(?:essa|esta|ela|isso)"
    r"(?:\s+(?:de novo|novamente|outra vez))?[?!.]*$",
    re.IGNORECASE,
)

# REV3 — controle pronominal estreito.
# A operação é dita na fala atual; apenas o referente fica pendente.
_PRONOME_CONTROLE = r"(?:ela|ele|isso)"

_REFERENCIA_PRONOMINAL_ISOLADA = re.compile(
    rf"^{_PRONOME_CONTROLE}[?!.]*$",
    re.IGNORECASE,
)

_RELATO_PRONOMINAL = re.compile(
    rf"^(?:ele|ela|o\s+sistema|o\s+youtube|o\s+player|a\s+laylay)\s+"
    rf"(?:pausa|pause|retoma|retome|continua|continue|despausa)\s+"
    rf"{_PRONOME_CONTROLE}\b",
    re.IGNORECASE,
)

_PAUSA_PRONOMINAL = re.compile(
    rf"^(?:por favor\s+)?(?:pausa|pause)\s+"
    rf"{_PRONOME_CONTROLE}[.!]*$",
    re.IGNORECASE,
)

_RETOMA_PRONOMINAL = re.compile(
    rf"^(?:por favor\s+)?"
    rf"(?:retoma|retome|continua|continue|despausa)\s+"
    rf"{_PRONOME_CONTROLE}[.!]*$",
    re.IGNORECASE,
)


# Formas curtas: a fala atual traz a operação, mas não o domínio/referente.
_PAUSA_CURTA = re.compile(
    r"^(?:por favor\s+)?(?:pausa|pause|pare)[?!.]*$",
    re.IGNORECASE,
)
_RETOMA_CURTA = re.compile(
    r"^(?:por favor\s+)?(?:retoma|retome|despausa)[?!.]*$",
    re.IGNORECASE,
)
_CONTINUA_CURTA = re.compile(
    r"^(?:por favor\s+)?(?:continua|continue)[?!.]*$",
    re.IGNORECASE,
)
_PROXIMA_CURTA = re.compile(
    r"^(?:por favor\s+)?proxima[?!.]*$",
    re.IGNORECASE,
)

# Nominais/deíticos que NÃO carregam ato diretivo suficiente sozinhos.
_REFERENCIA_AMBIGUA = re.compile(
    r"^(?:"
    r"(?:a\s+)?anterior|"
    r"(?:a\s+)?proxima\s+(?:musica|faixa)|"
    r"(?:a\s+)?(?:musica|faixa)\s+anterior"
    r")[?!.]*$",
    re.IGNORECASE,
)

# Pedido genérico para tocar algo: verbo diretivo precisa começar o ato.
# Deliberadamente não aceita sujeitos anteriores: "ele toca...", "quando toca...".
_TOCAR_GENERICO = re.compile(
    r"^(?:por favor\s+)?"
    r"(?:toca|toque|coloca|coloque|bota|ponha|poe|escuta|escute)\s+"
    r"(?P<alvo>.+?)[?!.]*$",
    re.IGNORECASE,
)

# Pedido polido ambíguo só é aceito quando o beneficiário "pra mim" está explícito.
_PEDIDO_POLIDO_PARA_MIM = re.compile(
    r"^(?:por favor\s+)?"
    r"(?:(?:voce|vc)\s+)?"
    r"(?:pode|poderia|consegue|conseguiria)\s+(?:me\s+)?"
    r"(?:tocar|colocar|botar|por|pausar|retomar)\b"
    r".*\b(?:pra|para)\s+mim[?!.]*$",
    re.IGNORECASE,
)


def _cadeia_musical_explicita(texto: str) -> bool:
    """Reconhece vários atos musicais diretivos na mesma fala.

    A função só concede ownership quando o primeiro ato já pertence
    explicitamente à música e existe uma segunda operação musical separada.
    Comentários que apenas mencionam música continuam fora desta regra.
    """
    t = str(texto or "").strip()
    if not re.match(
        r"^(?:por favor\s+)?(?:"
        r"pausa|pause|retoma|retome|continua|continue|despausa|"
        r"passa|passe|pula|pule|vai|toca|toque|coloca|coloque|bota"
        r")\b",
        t,
        flags=re.IGNORECASE,
    ):
        return False
    if not re.search(r"(?:[,;]|\be\b)", t, flags=re.IGNORECASE):
        return False
    if not re.search(
        r"\b(?:musica|faixa|playlist|som)\b",
        t,
        flags=re.IGNORECASE,
    ):
        return False

    operacoes = re.findall(
        r"\b(?:pausa|pause|retoma|retome|continua|continue|despausa|"
        r"passa|passe|pula|pule|vai|toca|toque|coloca|coloque|bota)\b",
        t,
        flags=re.IGNORECASE,
    )
    consulta_final = bool(re.search(
        r"\b(?:me\s+)?(?:diz|diga|fala|fale|mostra|mostre)\b"
        r".{0,40}\b(?:estado|tocando|faixa|musica)\b",
        t,
        flags=re.IGNORECASE,
    ))
    return len(operacoes) >= 2 or (bool(operacoes) and consulta_final)

def analisar_gramatica_musical(texto: str) -> AnaliseGramaticalMusical:
    t = normalizar_gramatica_musical(texto)
    if not t:
        return _resultado(
            texto=t, classe="nenhuma", regra="vazio",
            motivo="entrada vazia",
        )

    # 1) Leitura musical explícita.
    if _STATUS.fullmatch(t):
        return _resultado(
            texto=t,
            classe="consulta_estado",
            operacao="status",
            evidencia_diretiva=False,
            depende_contexto=False,
            dominio_explicito=True,
            somente_leitura=True,
            regra="status_fullmatch",
            motivo="consulta explícita ao estado musical",
        )

    # 2) Negação continua tendo precedência absoluta.
    if _NEGACAO_INICIAL.search(t):
        return _resultado(
            texto=t, classe="protegida", regra="negacao_inicial",
            motivo="negação não concede pedido mutante",
        )

    # 2.1) Pedido polido estreito com beneficiário explícito.
    # A interrogação faz parte da cortesia; não transforma a frase em mera
    # pergunta de capacidade. A regra é ancorada no início e exige "pra mim"
    # / "para mim", evitando promover perguntas sobre terceiros.
    if _PEDIDO_POLIDO_PARA_MIM.fullmatch(t):
        operacao = "tocar"
        if re.search(r"\bpausar\b", t):
            operacao = "pausa"
        elif re.search(r"\bretomar\b", t):
            operacao = "retomar"
        return _resultado(
            texto=t, classe="pedido_direto", operacao=operacao,
            evidencia_diretiva=True,
            depende_contexto=operacao in {"pausa", "retomar"},
            dominio_explicito=bool(
                re.search(r"\b(?:musica|faixa|playlist|som)\b", t)
            ),
            regra="pedido_polido_para_mim",
            motivo="pedido polido com beneficiário explícito",
        )

    # 2.2) Referente pronominal isolado não é ato diretivo.
    # Esta exceção estreita impede o guard narrativo legado de promover
    # "ela"/"ele"/"isso" a fala protegida quando não há predicado algum.
    if _REFERENCIA_PRONOMINAL_ISOLADA.fullmatch(t):
        return _resultado(
            texto=t,
            classe="nenhuma",
            regra="referencia_pronominal_isolada",
            motivo="pronome isolado fornece referente, não operação",
        )

    # 2.3) Guardas gerais de pergunta/hipótese.
    if _PERGUNTA_NAO_STATUS.search(t) or t.endswith("?"):
        return _resultado(
            texto=t, classe="protegida", regra="pergunta",
            motivo="pergunta não é tratada como ordem musical",
        )
    if _RELATO_PRONOMINAL.search(t):
        return _resultado(
            texto=t,
            classe="protegida",
            regra="relato_pronominal",
            motivo=(
                "sujeito explícito + predicado operacional pronominal "
                "descreve terceiro/sistema; não é ordem à Laylay"
            ),
        )

    if _HIPOTESE_OU_RELATO.search(t):
        return _resultado(
            texto=t, classe="protegida", regra="hipotese_relato_sujeito",
            motivo="moldura narrativa/hipotética não concede ato diretivo",
        )

    if _cadeia_musical_explicita(t):
        return _resultado(
            texto=t,
            classe="pedido_direto",
            operacao="cadeia_musical",
            evidencia_diretiva=True,
            dominio_explicito=True,
            regra="cadeia_musical_explicita",
            motivo="dois ou mais atos musicais diretivos na mesma fala",
        )

    # 3) REV3 — controles pronominais.
    if _PAUSA_PRONOMINAL.fullmatch(t):
        return _resultado(
            texto=t,
            classe="pedido_direto",
            operacao="pausa",
            evidencia_diretiva=True,
            depende_contexto=True,
            dominio_explicito=False,
            regra="pausa_pronominal_fullmatch",
            motivo=(
                "verbo de pausa concede operação; pronome mantém "
                "referente pendente"
            ),
        )

    if _RETOMA_PRONOMINAL.fullmatch(t):
        return _resultado(
            texto=t,
            classe="pedido_direto",
            operacao="retomar",
            evidencia_diretiva=True,
            depende_contexto=True,
            dominio_explicito=False,
            regra="retoma_pronominal_fullmatch",
            motivo=(
                "verbo de retomada concede operação; pronome mantém "
                "referente pendente"
            ),
        )

    # 4) Formas explícitas.
    if _PLAYLIST_PLAY.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="tocar",
            evidencia_diretiva=True, dominio_explicito=True,
            regra="playlist_play_fullmatch",
            motivo="verbo diretivo inicial + playlist explícita",
        )
    if _PAUSA_EXPLICITA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="pausa",
            evidencia_diretiva=True, dominio_explicito=True,
            regra="pausa_explicita_fullmatch",
            motivo="controle de pausa com domínio musical explícito",
        )
    if _RETOMA_EXPLICITA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="retomar",
            evidencia_diretiva=True, dominio_explicito=True,
            regra="retoma_explicita_fullmatch",
            motivo="retomada com domínio musical explícito",
        )
    if _PROXIMA_EXPLICITA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="proxima",
            evidencia_diretiva=True, dominio_explicito=True,
            regra="proxima_explicita_fullmatch",
            motivo="avanço musical explícito",
        )
    if _ANTERIOR_EXPLICITA.fullmatch(t):
        dominio_anterior_explicito = bool(
            re.search(r"\b(?:musica|faixa)\b", t)
        )
        return _resultado(
            texto=t, classe="pedido_direto", operacao="anterior",
            evidencia_diretiva=True,
            depende_contexto=not dominio_anterior_explicito,
            dominio_explicito=dominio_anterior_explicito,
            regra="anterior_explicita_fullmatch",
            motivo="verbo diretivo de retorno; referente explícito ou elíptico",
        )
    if _REPETIR_ELIPTICA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="repetir",
            evidencia_diretiva=True, depende_contexto=True,
            dominio_explicito=False,
            regra="repetir_eliptica_fullmatch",
            motivo="operação de repetição atual com referente dêitico",
        )

    # 4) Formas curtas: operação presente, alvo/contexto ausente.
    if _PAUSA_CURTA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="pausa",
            evidencia_diretiva=True, depende_contexto=True,
            regra="pausa_curta_fullmatch",
            motivo="imperativo curto; contexto só poderá fornecer o alvo",
        )
    if _RETOMA_CURTA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="retomar",
            evidencia_diretiva=True, depende_contexto=True,
            regra="retoma_curta_fullmatch",
            motivo="imperativo curto; contexto só poderá fornecer o alvo",
        )
    if _CONTINUA_CURTA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="retomar",
            evidencia_diretiva=True, depende_contexto=True,
            regra="continua_curta_fullmatch",
            motivo="ato diretivo curto; domínio/referente ainda não resolvido",
        )
    if _PROXIMA_CURTA.fullmatch(t):
        return _resultado(
            texto=t, classe="pedido_direto", operacao="proxima",
            evidencia_diretiva=True, depende_contexto=True,
            regra="proxima_curta_fullmatch",
            motivo="avanço curto; contexto decide o domínio compatível",
        )

    # 5) Referências nominais/deíticas sem verbo diretivo.
    if _REFERENCIA_AMBIGUA.fullmatch(t):
        return _resultado(
            texto=t, classe="referencia_ambigua",
            evidencia_diretiva=False, depende_contexto=True,
            regra="referencia_nominal_ambigua",
            motivo="referente possível, mas a fala isolada não prova um pedido",
        )

    # 6) Tocar algo: somente quando o verbo inicia o ato.
    generico = _TOCAR_GENERICO.fullmatch(t)
    if generico:
        alvo = str(generico.group("alvo") or "").strip()
        dominio_explicito = bool(
            re.search(r"\b(?:musica|faixa|playlist|som)\b", alvo)
        )
        return _resultado(
            texto=t, classe="pedido_direto", operacao="tocar",
            evidencia_diretiva=True,
            depende_contexto=False,
            dominio_explicito=dominio_explicito,
            regra="tocar_generico_ancorado",
            motivo="verbo diretivo inicia a fala e possui complemento",
        )

    return _resultado(
        texto=t,
        classe="nenhuma",
        regra="nenhum_padrao",
        motivo="nenhuma forma musical diretiva estreita foi reconhecida",
    )
