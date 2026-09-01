"""Fundamentação e validação factual geral para respostas conversacionais."""

from __future__ import annotations

import re
import time
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict

from mente_laylay.cognicao.proveniencia_informacao import (
    classificar_proveniencia_informacao,
    limitar_proveniencia_invalida,
)
from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
)


_TIPOS_OPERACIONAIS = {
    "app", "janela", "site", "iot", "dispositivo", "arquivo", "pasta",
    "playlist", "musica",
}

_ABERTURA_CONSULTA = re.compile(
    r"^(?:quem|qual|quais|quando|onde|como|quanto|o que|por que|porque|"
    r"me (?:fala|diz|conte)|(?:você|voce) (?:viu|soube|sabe))\b",
    re.IGNORECASE,
)
_SINAL_TEMPO_EXPLICITO = re.compile(
    r"\b(?:agora|hoje|neste momento|atualmente|recente(?:mente)?|últim[oa]s?|ultim[oa]s?|"
    r"esta semana|este mês|este mes|este ano|ainda|já saiu|ja saiu)\b",
    re.IGNORECASE,
)
_CONSULTA_PESSOAL_OU_INTERNA = re.compile(
    r"\b(?:como (?:você|voce|tu) (?:está|esta|tá|ta)|como (?:você|voce) se sente|"
    r"qual (?:é|e) meu nome|o que (?:você|voce) lembra de mim|"
    r"como (?:eu|meu|minha) (?:estou|sou|está|esta))\b",
    re.IGNORECASE,
)
_CONSULTA_MATEMATICA = re.compile(
    r"(?:\bquanto\s+(?:é|e|dá|da)\b.*\d|\d\s*(?:\+|-|x|×|\*|/|÷)\s*\d)",
    re.IGNORECASE,
)
_AFIRMACAO_ATUAL_MUTAVEL = re.compile(
    r"\b(?:n[aã]o vai ter|vai ter|vai sair|vai lan[cç]ar|nova gera[cç][aã]o|"
    r"exclusiv[oa]|compat[ií]vel|suporte oficial|ps\s*[3456]|playstation\s*[3456]|"
    r"xbox|switch|pc)\b",
    re.IGNORECASE,
)
_ANCORA_HISTORICA = re.compile(
    r"\b(?:em|no ano de|na década de|na decada de)\s+(?:18|19|20)\d{2}\b|"
    r"\b(?:quando nasceu|quando morreu|quem inventou|história de|historia de)\b",
    re.IGNORECASE,
)

_DOMINIOS_ATUALIDADE = (
    (
        "tempo_real",
        900.0,
        re.compile(
            r"\b(?:clima|tempo agora|temperatura|previsão do tempo|previsao do tempo|"
            r"cotação|cotacao|câmbio|cambio|placar|resultado do jogo|trânsito|transito)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "acontecimento_recente",
        3600.0,
        re.compile(
            r"\b(?:notícia|noticia|novidade|aconteceu|acontecendo|eleição|eleicao|"
            r"foi anunciado|acabou de|últimas notícias|ultimas noticias)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "agenda_ou_disponibilidade",
        21600.0,
        re.compile(
            r"\b(?:quando (?:sai|lança|lanca|começa|comeca)|data de lançamento|data de lancamento|"
            r"vai sair|vai lançar|vai lancar|estreia|agenda|horário do jogo|horario do jogo|"
            r"disponível|disponivel|em estoque|preço|preco|quanto custa)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "estado_mutavel",
        86400.0,
        re.compile(
            r"\b(?:versão|versao|atualização|atualizacao|presidente|governador|prefeito|"
            r"ceo|diretor executivo|lei vigente|regra atual|requisito|especificação atual|"
            r"especificacao atual|compatível|compativel|suporte oficial)\b",
            re.IGNORECASE,
        ),
    ),
)


def _normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "").casefold())
    base = "".join(ch for ch in base if not unicodedata.combining(ch))
    base = re.sub(r"[^a-z0-9\s.-]", " ", base)
    return re.sub(r"\s+", " ", base).strip()


def classificar_atualidade_factual(
    texto: str,
    *,
    turno: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Classifica consultas cujo valor factual pode mudar com o tempo.

    A decisão combina forma da fala, referência temporal e domínio mutável. Um
    termo isolado não basta: comandos, matemática e perguntas pessoais ficam
    fora mesmo quando contêm palavras como ``agora``.
    """
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    normalizado = _normalizar(bruto)
    leitura = dict(turno or {})
    modalidade = str(
        leitura.get("modalidade_geral") or leitura.get("modalidade") or ""
    ).casefold()
    eh_consulta = bool(
        "?" in bruto
        or modalidade in {"pergunta", "misto"}
        or _ABERTURA_CONSULTA.search(bruto)
    )
    base = {
        "depende_atualidade": False,
        "classe": "estavel",
        "validade_sugerida_s": 0.0,
        "confianca": 0.0,
        "motivos": [],
    }
    afirmacao_mutavel = bool(_AFIRMACAO_ATUAL_MUTAVEL.search(bruto))
    if not normalizado or (not eh_consulta and not afirmacao_mutavel):
        return {**base, "classe": "nao_consulta", "motivos": ["fala_nao_consultiva"]}
    if _CONSULTA_PESSOAL_OU_INTERNA.search(bruto):
        return {**base, "classe": "contexto_pessoal", "motivos": ["resposta_vem_da_mente_local"]}
    if _CONSULTA_MATEMATICA.search(bruto):
        return {**base, "motivos": ["resultado_deterministico"]}

    sinal_temporal = bool(_SINAL_TEMPO_EXPLICITO.search(bruto))
    if _ANCORA_HISTORICA.search(bruto) and not sinal_temporal:
        return {**base, "classe": "historica", "motivos": ["ancora_historica_explicita"]}

    for classe, validade, padrao in _DOMINIOS_ATUALIDADE:
        if padrao.search(bruto):
            motivos = [f"dominio:{classe}"]
            if sinal_temporal:
                motivos.append("marcador_temporal_explicito")
            return {
                "depende_atualidade": True,
                "classe": classe,
                "validade_sugerida_s": validade,
                "confianca": 0.96 if sinal_temporal else 0.88,
                "motivos": motivos,
            }

    if afirmacao_mutavel:
        return {
            "depende_atualidade": True,
            "classe": "agenda_ou_disponibilidade",
            "validade_sugerida_s": 21600.0,
            "confianca": 0.9,
            "motivos": ["afirmacao_sobre_plataforma_ou_disponibilidade"],
        }

    if sinal_temporal:
        return {
            "depende_atualidade": True,
            "classe": "recente_generica",
            "validade_sugerida_s": 21600.0,
            "confianca": 0.82,
            "motivos": ["marcador_temporal_explicito"],
        }
    return {**base, "confianca": 0.85, "motivos": ["sem_sinal_de_mutabilidade"]}


def avaliar_validade_fundamentacao(
    fundamentacao: Dict[str, Any] | None,
    *,
    agora: float | None = None,
) -> Dict[str, Any]:
    """Invalida evidência temporal vencida sem apagar fatos estáveis."""
    base = dict(fundamentacao or {})
    atualidade = dict(base.get("atualidade") or {})
    if not bool(
        base.get("requer_evidencia_recente")
        or atualidade.get("depende_atualidade")
    ):
        return base

    instante = float(agora if agora is not None else time.time())
    try:
        expira_em = float(base.get("evidencia_expira_em"))
    except (TypeError, ValueError):
        expira_em = 0.0
    validade_conhecida = expira_em > 0.0
    dentro_validade = bool(validade_conhecida and instante < expira_em)
    base["evidencia_dentro_validade"] = dentro_validade
    try:
        obtida_em = float(base.get("evidencia_obtida_em") or instante)
    except (TypeError, ValueError):
        obtida_em = instante
    base["evidencia_idade_s"] = max(0.0, instante - obtida_em)
    base["evidencia_expirada"] = not dentro_validade
    if dentro_validade or not base.get("confiavel"):
        return base

    # Preserva apenas metadados para diagnóstico. O conteúdo vencido não pode
    # continuar no prompt nem servir ao verificador como limite factual.
    base.update({
        "confiavel": False,
        "confianca": 0.0,
        "resumo": "",
        "fonte": "",
        "motivo": (
            "validade_evidencia_desconhecida"
            if not validade_conhecida
            else "evidencia_temporal_expirada"
        ),
    })
    base["proveniencia"] = limitar_proveniencia_invalida(base.get("proveniencia"))
    return base


def _tema_numerado_plausivel(valor: str, *, posicao_no_texto: int = 0) -> bool:
    candidato = str(valor or "").strip()
    achado = re.fullmatch(
        r"(?P<nome>[A-Za-zÀ-ÿ]{2,16})(?P<separador>\s*)(?P<numero>\d{1,3})",
        candidato,
    )
    if not achado:
        return True
    nome = achado.group("nome")
    if nome.casefold() in {"ps", "xbox"}:
        return False
    return bool(
        not achado.group("separador")
        or len(re.findall(r"[A-Z]", nome)) >= 2
        or (nome[:1].isupper() and posicao_no_texto > 0)
    )


def extrair_tema_fundamentacao(
    texto: str,
    *,
    retrato: Dict[str, Any] | None = None,
    registro_semantico: Dict[str, Any] | None = None,
) -> str:
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    # Perguntas sobre a preferência da própria Laylay e instruções de estilo
    # continuam conversacionais. Já uma preferência declarada pelo usuário
    # pode cooperar com memória e pesquisa: a declaração é a evidência pessoal
    # e a pesquisa serve apenas como enriquecimento auxiliar.
    if re.search(
        r"\b(?:voc[eê]|tu)\s+(?:gosta|curte|prefere)\b", bruto,
        flags=re.IGNORECASE,
    ):
        return ""
    referencia_previa = re.search(
        r"\b(?:dele|dela|deles|delas|desse|dessa|disso)\b",
        bruto,
        flags=re.IGNORECASE,
    )
    preferencias_declaradas = extrair_aprendizados_pessoais_explicitos(bruto)
    if preferencias_declaradas and not referencia_previa:
        return str(preferencias_declaradas[0].get("valor") or "").strip()[:160]
    if re.search(
        r"\b(?:explique|explica|responda|fale|diga)\b.*\b(?:como\s+(?:uma\s+)?"
        r"crian[cç]a|de\s+(?:um\s+)?jeito|de\s+forma|simples|resumid[oa]|"
        r"detalhad[oa]|curt[oa])\b",
        bruto, flags=re.IGNORECASE,
    ):
        return ""

    recomendacao = re.search(
        r"\b(?:recomenda|recomende|recomendar|indica|indique|sugere|sugira)\b"
        r"[^?!.]{0,100}\b(?P<categoria>filme|s[eé]rie|livro|jogo)\b"
        r"(?:\s+(?:de|do\s+g[eê]nero)\s+(?P<genero>[a-zA-ZÀ-ÿ -]{2,40}))?",
        bruto,
        flags=re.IGNORECASE,
    )
    if recomendacao:
        categoria = recomendacao.group("categoria").casefold()
        genero = str(recomendacao.group("genero") or "").strip(" ,.!?;:\"'")
        return f"{categoria} de {genero}"[:160] if genero else categoria[:160]
    snapshot = dict(retrato or {})
    referencia = dict(snapshot.get("referencia_resolvida") or {})
    tipo = str(referencia.get("tipo") or "").casefold()
    nome = str(referencia.get("nome") or "").strip()
    if (
        nome
        and tipo not in _TIPOS_OPERACIONAIS
        and _tema_numerado_plausivel(nome)
    ):
        return nome[:160]

    # Títulos sequenciais costumam aparecer como GTA 6, GTA6, FIFA 27 etc.
    # Capturar o primeiro evita que a plataforma citada depois (PS4/PS5) vire
    # o tema principal da pesquisa.
    titulo_numerado = re.search(
        r"\b(?P<nome>(?!PS\s*$|Xbox\s*$)[A-Za-zÀ-ÿ]{2,16})(?P<separador>\s*)(?P<numero>\d{1,3})\b",
        bruto,
    )
    if titulo_numerado:
        nome = titulo_numerado.group("nome")
        separador = titulo_numerado.group("separador")
        # Sem espaço, a combinação costuma ser um identificador real (GTA6,
        # iPhone15). Com espaço, exigimos aparência de sigla/título; assim
        # verbos comuns como "contou 20" não viram assunto pesquisável.
        parece_titulo = _tema_numerado_plausivel(
            f"{nome}{separador}{titulo_numerado.group('numero')}",
            posicao_no_texto=titulo_numerado.start(),
        )
        if parece_titulo:
            tema = f"{nome} {titulo_numerado.group('numero')}".strip()
            return tema[:160]
    padroes = (
        r"^(?:voc[eê]\s+)?(?:j[aá]\s+)?(?:ouviu(?:\s+falar)?|conhece)\s+(?:d[oa]|de\s+)?(.+?)[?!.]*$",
        r"^(?:quem\s+(?:e|é)|o\s+que\s+(?:e|é))\s+(.+?)[?!.]*$",
        r"^(?:o\s+que\s+(?:voce|você)\s+acha|qual\s+(?:a\s+)?sua\s+opini[aã]o)\s+(?:d[oa]|de|sobre)\s+(.+?)[?!.]*$",
        r"^(?:fala|fale|me\s+fala|explique|me\s+explica)\s+(?:de|do|da|sobre)\s+(.+?)[?!.]*$",
        r"^(?:que|qual)\s+(?:outra\s+)?m[uú]sica\s+(?:d[oa]|de)\s+(.+?)(?:\s+voc[eê]\s+(?:gosta|curte))?[?!.]*$",
        r"^(?:voc[eê]\s+)?(?:gosta|curte)\s+(?:d[oa]|de)\s+(.+?)[?!.]*$",
        r"^(?:eu\s+)?(?:ou[cç]o|escuto|curto|gosto\s+d[ea])\s+(?:bastante\s+)?(.+?)[?!.]*$",
    )
    for padrao in padroes:
        achado = re.search(padrao, bruto, flags=re.IGNORECASE)
        if achado:
            tema = achado.group(1).strip(" ,.!?;:\"'")
            if 1 <= len(tema.split()) <= 8:
                return tema[:160]

    registro = dict(registro_semantico or {})
    entidades = dict(registro.get("entidades") or {})
    ativa = dict(entidades.get(str(registro.get("entidade_ativa_id") or "")) or {})
    nome_ativo = str(ativa.get("nome") or "").strip()
    if nome_ativo.casefold() in {"filme", "serie", "série", "livro", "jogo"}:
        preferencia = re.search(
            r"\b(?:quero|prefiro|pode\s+ser)\b[^.!?]{0,50}\bde\s+"
            r"(?P<genero>[a-zA-ZÀ-ÿ -]{2,40})[.!?]*$",
            bruto,
            flags=re.IGNORECASE,
        )
        if preferencia:
            genero = str(preferencia.group("genero") or "").strip(" ,.!?;:\"'")
            if genero:
                return f"{nome_ativo} de {genero}"[:160]
    if re.search(r"\b(?:ele|ela|dele|dela|desse|dessa|isso|esse|essa)\b", bruto, flags=re.IGNORECASE):
        return nome_ativo[:160]
    return ""


def montar_fundamentacao(
    tema: str,
    pesquisa: Dict[str, Any] | None,
    *,
    agora: float | None = None,
    atualidade: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    dados = dict(pesquisa or {})
    instante = float(agora if agora is not None else time.time())
    resumo = re.sub(r"\s+", " ", str(dados.get("resumo") or "")).strip()
    try:
        confianca = float(dados.get("confianca") or 0.0)
    except (TypeError, ValueError):
        confianca = 0.0
    confiavel = bool(dados.get("ok") and resumo and confianca >= 0.60)
    candidatos = [
        re.sub(r"\s+", " ", str(item or "")).strip()[:100]
        for item in list(dados.get("candidatos") or [])[:12]
        if re.sub(r"\s+", " ", str(item or "")).strip()
    ]
    classificacao_atualidade = dict(atualidade or {})
    try:
        obtida_em = float(dados.get("evidencia_obtida_em") or instante)
    except (TypeError, ValueError):
        obtida_em = instante
    try:
        validade_fonte = max(0.0, float(dados.get("evidencia_validade_s") or 1800.0))
    except (TypeError, ValueError):
        validade_fonte = 1800.0
    try:
        validade_atualidade = max(
            0.0, float(classificacao_atualidade.get("validade_sugerida_s") or 0.0)
        )
    except (TypeError, ValueError):
        validade_atualidade = 0.0
    validade_efetiva = (
        min(validade_fonte, validade_atualidade)
        if classificacao_atualidade.get("depende_atualidade") and validade_atualidade
        else validade_fonte
    )
    expira_em = obtida_em + validade_efetiva
    idade_s = max(0.0, instante - obtida_em)
    dentro_validade = bool(validade_efetiva > 0.0 and instante < expira_em)
    fundamentacao = {
        "tema": str(tema or "").strip()[:160],
        "titulo": str(dados.get("titulo") or tema or "").strip()[:160],
        "resumo": resumo[:1200] if confiavel else "",
        "candidatos": candidatos if confiavel else [],
        "fonte": str(dados.get("fonte") or "").strip()[:120] if confiavel else "",
        "confianca": round(confianca, 3) if confiavel else 0.0,
        "confiavel": confiavel,
        "motivo": "fonte_contextual_suficiente" if confiavel else str(dados.get("motivo") or "sem_fonte_suficiente"),
        "ts": instante,
        "atualidade": classificacao_atualidade,
        "requer_evidencia_recente": bool(classificacao_atualidade.get("depende_atualidade")),
        "evidencia_disponivel": bool(dados.get("ok") and resumo),
        "evidencia_obtida_em": obtida_em,
        "evidencia_obtida_em_iso": datetime.fromtimestamp(obtida_em, timezone.utc).isoformat(),
        "evidencia_validade_s": validade_efetiva,
        "evidencia_expira_em": expira_em,
        "evidencia_expira_em_iso": datetime.fromtimestamp(expira_em, timezone.utc).isoformat(),
        "evidencia_idade_s": idade_s,
        "evidencia_dentro_validade": dentro_validade,
        "evidencia_cache": bool(dados.get("evidencia_cache", False)),
    }
    fundamentacao["proveniencia"] = classificar_proveniencia_informacao(
        fundamentacao,
        contexto="fundamentacao_factual",
    )
    return avaliar_validade_fundamentacao(fundamentacao, agora=instante)


_GRUPOS_ESPECIFICOS = (
    {"politica", "politico", "deputado", "senador", "presidente", "partido", "mandato", "eleito"},
    {"crime", "preso", "condenado", "fraude", "assassinato", "processo"},
    {"doenca", "diagnostico", "cancer", "internado", "sindrome", "tratamento"},
    {"premio", "premiado", "campeao", "venceu", "vencedor", "indicacao"},
    {"mpb", "jazz", "pop", "rock", "rap", "trap", "samba", "soul", "funk", "reggae", "metal", "blues", "axe"},
    {"fundador", "diretor", "autor", "criador", "inventor", "desenvolvedor", "produtor"},
    {"nascimento", "nasceu", "morreu", "falecido", "casado", "filho", "filha"},
    {"mora", "vive", "cidade", "pais", "brasileiro", "brasileira", "paulista", "carioca", "nacionalidade"},
    {"processador", "ram", "vram", "resolucao", "chipset", "nucleos", "threads"},
    {"ps4", "ps5", "playstation", "xbox", "switch", "plataforma", "compatibilidade"},
)

_FAMILIARIDADE_INVENTADA = re.compile(
    r"\b(?:j[aá]\s+ouvi|(?:eu\s+)?ouvi\s+(?:(?:alg|um)as?|muitas?)\s+m[uú]sicas?|"
    r"ouvi\s+(?:tudo|o\s+cat[aá]logo)|acompanho\s+(?:ele|ela|o\s+trabalho)|"
    r"conhe[cç]o\s+(?:bem|todo|toda)|experimentei\s+(?:todo|toda)|assisti\s+todos?|li\s+todos?)\b",
    re.IGNORECASE,
)

_MEDIDA_ESPECIFICA = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:kb|mb|gb|tb|hz|khz|mhz|ghz|fps|mp|megapixels?|"
    r"km|kg|gramas?|metros?|milimetros?|polegadas?|watts?|w)\b",
    re.IGNORECASE,
)


def _plataformas_citadas(texto: str) -> set[str]:
    normalizado = _normalizar(texto)
    plataformas: set[str] = set()
    for numero in (4, 5, 6):
        if re.search(rf"\b(?:ps\s*{numero}|playstation\s*{numero})\b", normalizado):
            plataformas.add(f"ps{numero}")
    if re.search(r"\bxbox\s+series\s+x\b", normalizado):
        plataformas.add("xbox_series_x")
    if re.search(r"\bxbox\s+series\s+s\b", normalizado):
        plataformas.add("xbox_series_s")
    if re.search(r"\bnintendo\s+switch\s*2\b", normalizado):
        plataformas.add("switch_2")
    if re.search(r"\b(?:pc|windows)\b", normalizado):
        plataformas.add("pc")
    return plataformas


def extrair_titulos_citados(texto: str) -> list[str]:
    """Extrai obras destacadas por aspas ou ênfase Markdown da fala."""
    bruto = str(texto or "")
    encontrados = [
        str(a or b).strip()
        for a, b in re.findall(
            r'["“]([^"”]{2,100})["”]|\'([^\']{2,100})\'', bruto,
        )
        if str(a or b).strip()
    ]
    encontrados.extend(
        str(item or "").strip()
        for item in re.findall(r'(?<!\*)\*{1,2}([^*\n]{2,100})\*{1,2}(?!\*)', bruto)
        if str(item or "").strip()
    )
    return list(dict.fromkeys(encontrados))


def _titulos_citados(texto: str) -> list[str]:
    return extrair_titulos_citados(texto)


def _frase_especifica_sem_base(frase: str, tema: str = "") -> bool:
    t = _normalizar(frase)
    if len(t.split()) < 4:
        return False
    if _titulos_citados(frase) or re.search(r"\b(?:18|19|20)\d{2}\b", t):
        return True
    if any(_grupo_presente(set(t.split()), grupo) for grupo in _GRUPOS_ESPECIFICOS):
        return True
    tema_norm = _normalizar(tema)
    subjetiva = bool(re.search(
        r"\b(?:acho|parece|soa|interessante|legal|curioso|curiosa|gosto|na minha opiniao)\b",
        t,
    ))
    if tema_norm and tema_norm in t and not subjetiva and re.search(
        r"\b(?:e|foi|era|tem|teve|possui|produz|fabrica|criou|fundou|desenvolveu|"
        r"publicou|lancou|participou|trabalhou|pertence|fica|funciona)\b",
        t,
    ):
        return True
    return bool(re.search(
        r"\b(?:e conhecido|é conhecido|foi conhecido|uma das|um dos|lancou|lançou|"
        r"criou|fundou|ganhou|mistura|combina elementos|participou|nasceu|morreu|"
        r"se passa em|foi desenvolvido|foi publicado)\b",
        str(frase or ""),
        flags=re.IGNORECASE,
    ))


def _grupo_presente(tokens: set[str], grupo: set[str]) -> bool:
    return any(
        token.strip(".-") == termo
        or (len(termo) >= 4 and token.strip(".-").startswith(termo))
        for token in tokens
        for termo in grupo
    )


def _fala_social_sem_alegacao_externa(frase: str) -> bool:
    """Distingue reação conversacional de uma afirmação factual pesquisável."""
    texto = _normalizar(frase)
    if not texto:
        return False
    if _titulos_citados(frase) or _MEDIDA_ESPECIFICA.search(frase):
        return False
    if re.search(r"\b(?:18|19|20)\d{2}\b", texto):
        return False
    if re.search(
        r"\b(?:nasceu|morreu|lancou|criou|fundou|ganhou|foi desenvolvido|"
        r"foi publicado|se passa em|e conhecido|pertence|possui|produz|"
        r"mistura|combina elementos)\b",
        texto,
    ):
        return False
    return bool(re.search(
        r"\b(?:entendi|legal|boa|interessante|curioso|curiosa|gosto|prefiro|"
        r"combina com voce|te pega|voce curte|me conta|qual|o que)\b",
        texto,
    ))


def _fallback_sem_inventar(tema: str, texto_usuario: str) -> str:
    nome = str(tema or "esse tema").strip()
    usuario = _normalizar(texto_usuario)
    if extrair_aprendizados_pessoais_explicitos(texto_usuario):
        return (
            f"{nome.capitalize()}, então. Boa, isso já me dá uma pista melhor do seu gosto. "
            "O que mais te pega nisso?"
        )
    if re.search(r"\b(?:gosto|curto|adoro|sou fa|tambem gosto)\b", usuario):
        return (
            f"Entendi o que você quis dizer sobre {nome}. Posso seguir por esse fio "
            "sem inventar detalhes que eu ainda não confirmei."
        )
    if re.search(r"\b(?:voce gosta|você gosta|voce curte|você curte|o que acha|qual sua opiniao)\b", str(texto_usuario or ""), flags=re.IGNORECASE):
        return (
            f"Eu ainda não conheço {nome} com segurança suficiente para dizer que gosto ou citar detalhes. "
            "Posso formar uma impressão pelo que eu encontrar de forma confiável, sem fingir repertório."
        )
    if "?" in str(texto_usuario or ""):
        return (
            f"Sobre {nome}, eu não encontrei uma base confiável o bastante para afirmar detalhes específicos. "
            "Prefiro assumir essa limitação a completar a resposta no chute."
        )
    return (
        f"Esse assunto sobre {nome} parece interessante, mas eu ainda não tenho informação verificada "
        "o bastante para acrescentar detalhes sem inventar."
    )


def reparar_recomendacao_com_evidencia(
    fundamentacao: Dict[str, Any] | None,
    fala_candidata: str = "",
) -> str:
    """Materializa uma recomendação mínima somente de candidatos observados.

    Quando o modelo escolheu um item válido, a escolha é preservada. O renderer
    apenas remove alegações que a lista pesquisada não comprovou.
    """
    base = dict(fundamentacao or {})
    candidatos = [
        re.sub(r"\s+", " ", str(item or "")).strip()
        for item in list(base.get("candidatos") or [])
        if re.sub(r"\s+", " ", str(item or "")).strip()
    ]
    if not candidatos:
        return ""
    fala_normalizada = _normalizar(fala_candidata)
    candidato_escolhido = next((
        candidato
        for candidato in candidatos
        if _normalizar(candidato) in fala_normalizada
    ), candidatos[0])
    tema = str(base.get("tema") or "esse tema").strip()
    return (
        f"Eu iria de {candidato_escolhido}. Esse aparece na lista que encontrei "
        f"para {tema}."
    )


_NEGACAO_CAPACIDADE_COM_PESQUISA = re.compile(
    r"\b(?:n[aã]o\s+(?:posso|consigo)\s+(?:te\s+)?"
    r"(?:recomendar|sugerir|indicar)|"
    r"n[aã]o\s+tenho\s+acesso\s+(?:a|à)\s+(?:uma\s+)?"
    r"(?:base\s+de\s+dados|dados|informa[cç][oõ]es|cat[aá]logo))\b",
    re.IGNORECASE,
)

_DESCRICAO_OBRA_FORA_DA_LISTA = re.compile(
    r"\b(?:basead[oa]s?\s+em|hist[oó]ria\s+real|sinopse|enredo|trama|"
    r"protagonist[as]?|personage(?:m|ns)|se\s+passa|dirigid[oa]\s+por|"
    r"estrelad[oa]\s+por|conta\s+(?:a\s+)?hist[oó]ria|acompanha\s+|"
    r"jogador(?:a)?\s+de|se\s+apaixona|final|cl[aá]ssic[oa]s?|roteiro|"
    r"mistura|ritmo|clima|cenas?|explora|mostra|traz|porque|pois|tem)\b",
    re.IGNORECASE,
)


def validar_fala_com_fundamentacao(
    fala: str,
    *,
    fundamentacao: Dict[str, Any] | None,
    texto_usuario: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    original = re.sub(r"\s+", " ", str(fala or "")).strip()
    base = avaliar_validade_fundamentacao(fundamentacao, agora=agora)
    reparo_recomendacao = reparar_recomendacao_com_evidencia(base, original)
    if (
        reparo_recomendacao
        and base.get("confiavel")
        and base.get("evidencia_dentro_validade", True) is not False
        and _NEGACAO_CAPACIDADE_COM_PESQUISA.search(original)
    ):
        return {
            "fala": reparo_recomendacao,
            "problemas": ["negacao_capacidade_contradiz_pesquisa"],
            "acao": "recomendacao_reparada_por_evidencia",
            "trechos_rejeitados": [original],
        }
    tema = str(base.get("titulo") or base.get("tema") or "esse tema").strip()
    evidencia = " ".join((
        str(base.get("resumo") or ""),
        str(texto_usuario or ""),
    ))
    evidencia_norm = _normalizar(evidencia)
    preferencia_declarada = bool(
        base.get("declaracao_pessoal_explicita")
        or extrair_aprendizados_pessoais_explicitos(texto_usuario)
    )
    problemas: list[str] = []
    frases = [parte.strip() for parte in re.split(r"(?<=[.!?])\s+", original) if parte.strip()]
    rejeitadas: list[str] = []
    evidencia_lista_candidatos = bool(
        base.get("confiavel")
        and base.get("candidatos")
        and str(base.get("titulo") or "").casefold().startswith("candidatos de ")
    )
    candidatos_normalizados = {
        _normalizar(item)
        for item in list(base.get("candidatos") or [])
        if _normalizar(item)
    }

    for frase in frases:
        titulos = _titulos_citados(frase)
        titulo_sem_evidencia = any(_normalizar(titulo) not in evidencia_norm for titulo in titulos)
        anos = set(re.findall(r"\b(?:18|19|20)\d{2}\b", _normalizar(frase)))
        ano_sem_evidencia = any(ano not in evidencia_norm for ano in anos)
        tokens = set(_normalizar(frase).split())
        tokens_evidencia = set(evidencia_norm.split())
        categoria_sem_evidencia = any(
            _grupo_presente(tokens, grupo) and not _grupo_presente(tokens_evidencia, grupo)
            for grupo in _GRUPOS_ESPECIFICOS
        )
        medida_sem_evidencia = bool(
            _MEDIDA_ESPECIFICA.search(frase)
            and _normalizar(_MEDIDA_ESPECIFICA.search(frase).group(0)) not in evidencia_norm
        )
        plataformas_frase = _plataformas_citadas(frase)
        plataformas_evidencia = _plataformas_citadas(evidencia)
        plataforma_sem_evidencia = bool(plataformas_frase - plataformas_evidencia)
        familiaridade_inventada = bool(_FAMILIARIDADE_INVENTADA.search(frase))
        reacao_social_preferencia = bool(
            preferencia_declarada and _fala_social_sem_alegacao_externa(frase)
        )
        sem_base = bool(
            not base.get("confiavel")
            and _frase_especifica_sem_base(frase, tema)
            and not reacao_social_preferencia
        )
        frase_normalizada = _normalizar(frase)
        frase_nomeia_candidato = any(
            candidato in frase_normalizada
            for candidato in candidatos_normalizados
        )
        declaracao_adicional_nao_comprovada = bool(
            not frase_nomeia_candidato
            and "?" not in frase
            and len(frase_normalizada.split()) >= 4
        )
        descricao_encontrada = _DESCRICAO_OBRA_FORA_DA_LISTA.search(frase)
        descricao_obra_sem_evidencia = bool(
            evidencia_lista_candidatos
            and (
                declaracao_adicional_nao_comprovada
                or (
                    descricao_encontrada
                    and _normalizar(descricao_encontrada.group(0)) not in evidencia_norm
                )
            )
        )
        if (
            titulo_sem_evidencia or ano_sem_evidencia or categoria_sem_evidencia
            or medida_sem_evidencia or plataforma_sem_evidencia
            or familiaridade_inventada or sem_base or descricao_obra_sem_evidencia
        ):
            rejeitadas.append(frase)
            if titulo_sem_evidencia:
                problemas.append("obra_sem_evidencia")
            if ano_sem_evidencia:
                problemas.append("data_sem_evidencia")
            if categoria_sem_evidencia:
                problemas.append("caracteristica_sem_evidencia")
            if medida_sem_evidencia:
                problemas.append("medida_sem_evidencia")
            if plataforma_sem_evidencia:
                problemas.append("plataforma_sem_evidencia")
            if familiaridade_inventada:
                problemas.append("familiaridade_inventada")
            if sem_base:
                problemas.append("alegacao_especifica_sem_fonte")
            if descricao_obra_sem_evidencia:
                problemas.append("descricao_obra_sem_evidencia")

    if not rejeitadas:
        return {"fala": original, "problemas": [], "acao": "aceita"}

    if reparo_recomendacao and {
        "obra_sem_evidencia", "descricao_obra_sem_evidencia",
    }.intersection(problemas):
        # A pesquisa já materializou opções verificáveis. Se a LLM sair dessa
        # lista, não preservamos descrições anexadas ao título inventado: a
        # fala inteira volta para um candidato observado na mesma evidência.
        return {
            "fala": reparo_recomendacao,
            "problemas": list(dict.fromkeys(problemas)),
            "acao": "recomendacao_reparada_por_evidencia",
            "trechos_rejeitados": rejeitadas,
        }

    restantes = [frase for frase in frases if frase not in rejeitadas]
    fala_segura = " ".join(restantes).strip()
    # Saudações soltas como "isso é ótimo" não sustentam a resposta depois
    # que os detalhes inventados são removidos.
    if len(_normalizar(fala_segura).split()) < 7:
        fala_segura = _fallback_sem_inventar(tema, texto_usuario)
    return {
        "fala": fala_segura,
        "problemas": list(dict.fromkeys(problemas)),
        "acao": "ajustada",
        "trechos_rejeitados": rejeitadas,
    }
