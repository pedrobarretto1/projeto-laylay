"""Retrato imutável das entidades e limites contextuais de um turno."""

from __future__ import annotations

import re
import time
from typing import Any, Dict

from mente_laylay.memoria_mental.registro_semantico import resolver_referencia_pontuada
from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual


def _entidade(tipo: str, nome: str, *, origem: str, ts: float, dados: dict | None = None) -> dict:
    return {
        "tipo": str(tipo or "").strip(),
        "nome": str(nome or "").strip()[:180],
        "origem": str(origem or "").strip(),
        "ts": float(ts or 0.0),
        "dados": dict(dados or {}),
    }


def _nome_jogo(jogo: dict) -> str:
    titulo = str(jogo.get("titulo") or "").strip()
    if titulo:
        return re.split(r"\s+[—–|]\s+|\s+-\s+", titulo, maxsplit=1)[0].strip()[:100]
    processo = str(jogo.get("processo") or "").strip()
    processo = re.sub(r"(?:-win(?:32|64)-shipping|[._-]?x64)?\.exe$", "", processo, flags=re.I)
    return re.sub(r"[_-]+", " ", processo).strip()[:100]


def _nome_apresentacao(nome: str) -> str:
    """Mantém uma expressão nomeada inteira, inclusive palavras como ``Seu``."""
    limpo = re.sub(r"\s+", " ", str(nome or "")).strip(" .,!?:;\"'")
    if not limpo:
        return ""
    # A transcrição costuma vir toda em minúsculas. Capitalizar palavra a
    # palavra deixa o nome legível sem interpretar "seu" como posse.
    if limpo == limpo.casefold():
        limpo = " ".join(parte[:1].upper() + parte[1:] for parte in limpo.split())
    return limpo[:120]


def extrair_entidade_explicita(texto: str) -> dict:
    """Extrai a entidade que o usuário nomeou neste turno.

    A extração é deliberadamente conservadora: categorias explícitas sempre
    contam; em perguntas de gosto, somente expressões com ao menos duas
    palavras são tratadas como nome próprio provável.
    """
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if not bruto:
        return {}
    categorias = {
        "artista": r"artista|cantor|cantora|músico|musico|banda|grupo",
        "jogo": r"jogo|game",
        "filme": r"filme",
        "serie": r"série|serie",
        "livro": r"livro",
    }
    for tipo, rotulos in categorias.items():
        achado = re.search(
            rf"\b(?:{rotulos})\s+(?:chamad[oa]\s+)?([^,.!?;]{{2,100}})",
            bruto,
            flags=re.IGNORECASE,
        )
        if achado:
            nome = _nome_apresentacao(achado.group(1))
            if re.match(r"^(?:É|Está|Foi|Parece|Tem|Tá)\b", nome, flags=re.IGNORECASE):
                continue
            if nome:
                return {"tipo": tipo, "nome": nome, "origem": "nome_explicito"}

    achado = re.search(
        r"\b(?:gosta|curte|conhece|ouve|escuta)\s+(?:d[oa]|de)\s+([^,.!?;]{2,100})",
        bruto,
        flags=re.IGNORECASE,
    )
    if achado:
        nome = _nome_apresentacao(achado.group(1))
        if 2 <= len(nome.split()) <= 6:
            return {"tipo": "referencia_nomeada", "nome": nome, "origem": "nome_explicito"}
    achado = re.search(
        r"\b(?:o\s+que\s+(?:você|voce)\s+acha|(?:você|voce)\s+acha|"
        r"(?:você|voce)\s+pensa|qual\s+(?:a\s+)?sua\s+opinião|"
        r"qual\s+(?:a\s+)?sua\s+opiniao)\s+(?:d[oa]|de|sobre)\s+([^,.!?;]{2,100})",
        bruto,
        flags=re.IGNORECASE,
    )
    if achado:
        nome = _nome_apresentacao(achado.group(1))
        if 2 <= len(nome.split()) <= 6:
            return {"tipo": "referencia_nomeada", "nome": nome, "origem": "nome_explicito"}
    return {}


def _entidade_curta_ja_conhecida(
    texto: str,
    *,
    entidades_recentes: Dict[str, Any] | None,
    registro_semantico: Dict[str, Any] | None,
) -> dict:
    """Recupera nomes de uma palavra quando o contexto já conhece a entidade.

    Uma palavra minúscula isolada pode ser conceito, lugar ou artista. Por isso
    ela só ganha tipo quando corresponde a uma entidade recente/registrada; a
    frase sozinha nunca força a classificação.
    """
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    achado = re.search(
        r"\b(?:gosta|curte|conhece|ouve|escuta|prefere)\s+(?:d[oa]|de)\s+"
        r"(?P<nome>[A-Za-zÀ-ÿ0-9_-]{2,60})[?!.]*$",
        bruto,
        flags=re.IGNORECASE,
    )
    if not achado:
        return {}
    candidato = str(achado.group("nome") or "").strip()
    candidato_norm = candidato.casefold()
    fontes = [
        dict(item)
        for item in dict(entidades_recentes or {}).values()
        if isinstance(item, dict)
    ]
    registro = dict(registro_semantico or {})
    fontes.extend(
        dict(item)
        for item in dict(registro.get("entidades") or {}).values()
        if isinstance(item, dict)
    )
    for item in fontes:
        nome = str(item.get("nome") or "").strip()
        if nome and nome.casefold() == candidato_norm:
            return {
                "tipo": str(item.get("tipo") or "referencia_nomeada"),
                "nome": nome,
                "origem": "nome_curto_contextual",
            }
    return {}


def _operacao_explicita(texto: str) -> tuple[str, tuple[str, ...]]:
    t = str(texto or "").casefold()
    if (
        re.search(r"\b(?:coloca|coloque|bota|toque|toca|põe|poe)\b", t)
        and re.search(r"\b(?:música|musica|som|faixa|canção|cancao)\b", t)
        and re.search(r"\b(?:dele|dela|desse|dessa)\b", t)
    ):
        return "musica_do_referente", ("MUSIC_SEARCH",)
    if "playlist" in t:
        if re.search(r"\b(?:cria|criar|crie|faz|fazer)\b", t):
            return "playlist_criar", ("PLAYLIST_CREATE",)
        if re.search(r"\b(?:move|mova|transfere|transfira)\b", t) and re.search(
            r"\bda\s+playlist\b.*\b(?:pra|para)\s+(?:a\s+)?playlist\b", t
        ):
            return "playlist_mover", ("PLAYLIST_MOVE",)
        verbo_adicao = re.search(
            r"\b(?:coloca|coloque|bota|salva|salve|guarda|guarde|adiciona|adicione|add)\b",
            t,
        )
        destino_adicao = re.search(
            r"\b(?:na|nessa|nesta|para a|pra|em)\s+(?:minha\s+)?playlist\b",
            t,
        )
        # A forma oral sem crase só é adição quando há uma faixa explícita.
        # Isso preserva ``essa música a playlist`` sem confundir o artigo de
        # ``coloca a playlist rock``, que é um pedido para tocar a playlist.
        destino_adicao_oral = (
            re.search(r"\b(?:musica|música|faixa|canção|cancao)\b", t)
            and re.search(r"\ba\s+(?:minha\s+)?playlist\b", t)
        )
        if verbo_adicao and (destino_adicao or destino_adicao_oral):
            return "playlist_adicionar", ("PLAYLIST_ADD",)
        if re.search(r"\b(?:toca|toque|abre|abra|coloca|coloque|ouvir|escuta)\b", t):
            return "playlist_tocar", ("PLAYLIST_PLAY", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE")
    if re.search(r"\b(?:luz|lampada|lâmpada|ventilador|tomada|dispositivo)\b", t):
        return "iot", ("IOT_CONTROL", "IOT_STATUS", "IOT_LIST")
    if re.search(r"\b(?:arquivo|pasta|documento)\b", t):
        return "arquivo", (
            "FILE_SEARCH", "FILE_OPEN_RESULT", "CREATE_FOLDER", "CREATE_FILE",
            "DELETE_ITEM", "MOVE_ITEM", "FILE_TRANSACTION",
        )
    if re.search(r"\b(?:codigo|código|script)\b", t) and re.search(
        r"\b(?:encontra|encontre|acha|ache|procura|procure|localiza|localize)\b",
        t,
    ):
        return "arquivo", ("FILE_SEARCH",)
    return "", ()


def construir_retrato_turno(
    texto: str,
    *,
    turno: Dict[str, Any] | None,
    mente: Dict[str, Any] | None,
    contexto_perceptivo: Dict[str, Any] | None,
    playlist_state: Dict[str, Any] | None = None,
    jogo_contexto: Dict[str, Any] | None = None,
    agora: float | None = None,
) -> tuple[dict, dict]:
    """Congela o mundo percebido e atualiza a memória curta de entidades."""
    instante = float(agora if agora is not None else time.time())
    estado = dict(mente or {})
    percepcao = dict(contexto_perceptivo or {})
    playlist = dict(playlist_state or {})
    jogo = dict(jogo_contexto or percepcao.get("jogo") or {})
    recentes = {
        str(k): dict(v) for k, v in dict(estado.get("entidades_recentes") or {}).items()
        if isinstance(v, dict) and instante - float(v.get("ts") or 0.0) <= 900.0
    }

    nome_jogo = _nome_jogo(jogo)
    if nome_jogo:
        recentes["jogo"] = _entidade("jogo", nome_jogo, origem="modo_jogo", ts=instante, dados=jogo)
    nome_playlist = str(playlist.get("name") or "").strip()
    if nome_playlist:
        recentes["playlist"] = _entidade(
            "playlist", nome_playlist, origem="reprodutor", ts=instante,
            dados={"indice": playlist.get("index"), "url": playlist.get("last_url")},
        )
    estrutura = dict(estado.get("ultima_estrutura_arquivo_params") or {})
    caminho_estrutura = str(estrutura.get("caminho") or "").strip()
    tipo_estrutura = str(estrutura.get("tipo") or "").strip().casefold()
    if caminho_estrutura and tipo_estrutura in {"arquivo", "pasta"}:
        nome_estrutura = str(
            estrutura.get("arquivo_nome")
            or estrutura.get("nome")
            or estrutura.get("pasta")
            or caminho_estrutura
        ).strip()
        recentes[tipo_estrutura] = _entidade(
            tipo_estrutura,
            nome_estrutura,
            origem="estrutura_arquivo_confirmada",
            ts=instante,
            dados={**estrutura, "caminho": caminho_estrutura},
        )
    focos = dict(estado.get("focos_por_dominio") or {})
    for dominio, foco in focos.items():
        if not isinstance(foco, dict):
            continue
        nome = str(foco.get("alvo") or foco.get("topico") or "").strip()
        if nome:
            recentes[str(dominio)] = _entidade(
                str(dominio), nome, origem="foco_mental",
                ts=float(foco.get("ts") or instante), dados=foco,
            )
    exe = str(percepcao.get("exe") or "").strip()
    titulo = str(percepcao.get("title") or "").strip()
    if exe or titulo:
        recentes["janela"] = _entidade(
            "janela", titulo or exe, origem="janela_ativa", ts=instante,
            dados={"exe": exe, "titulo": titulo, "assunto": percepcao.get("assunto")},
        )

    explicita = extrair_entidade_explicita(texto)
    if not explicita:
        explicita = _entidade_curta_ja_conhecida(
            texto,
            entidades_recentes=recentes,
            registro_semantico=estado.get("registro_semantico"),
        )
    if explicita:
        tipo_explicito = str(explicita.get("tipo") or "referencia_nomeada")
        recentes[tipo_explicito] = _entidade(
            tipo_explicito,
            str(explicita.get("nome") or ""),
            origem="nome_explicito",
            ts=instante,
        )

    t = str(texto or "").casefold()
    operacao, intents_permitidos = _operacao_explicita(t)
    # Em ``coloca essa música na playlist X``, ``essa música`` não aponta para
    # uma entidade antiga da conversa: é a fonte operacional "faixa atual".
    # O executor de playlists ainda consulta e valida o player antes de gravar,
    # portanto o retrato pode resolver a referência sem inventar título nem
    # autorizar sucesso. Sem esta entidade, o especialista operacional marcava
    # o alvo como ambíguo e descartava um PLAYLIST_ADD já detectado corretamente.
    if operacao == "playlist_adicionar" and re.search(
        r"\b(?:essa|esta)\s+(?:musica|música|faixa|canção|cancao)\b",
        t,
    ):
        titulo_atual = str(estado.get("musica_atual_titulo") or "").strip()
        recentes["musica"] = _entidade(
            "musica",
            titulo_atual or "faixa atual",
            origem="reprodutor_atual",
            ts=instante,
            dados={
                "url": str(estado.get("musica_atual_url") or "").strip(),
                "status": str(estado.get("musica_atual_status") or "").strip(),
                "validacao_no_executor": True,
            },
        )
    referencia = ""
    referencia_resolvida = {}
    referencia_candidatos = []
    if re.search(r"\b(?:esse|este)\s+jogo\b|\bessa\s+partida\b", t):
        referencia = "jogo"
    elif re.search(r"\b(?:essa|esta)\s+(?:musica|música|faixa)\b", t):
        referencia = "musica" if "musica" in recentes else "playlist"
    elif re.search(r"\b(?:essa|esta)\s+playlist\b", t):
        referencia = "playlist"
    elif explicita:
        referencia = str(explicita.get("tipo") or "referencia_nomeada")
    elif re.search(r"\b(?:ela|ele|dele|dela|isso|essa|esse)\b", t):
        resolucao = resolver_referencia_pontuada(
            texto,
            entidades_recentes=recentes,
            registro=estado.get("registro_semantico"),
            operacao=operacao,
            agora=instante,
        )
        referencia = str(resolucao.get("chave") or "")
        referencia_resolvida = dict(resolucao.get("resolvida") or {})
        referencia_candidatos = list(resolucao.get("candidatos") or [])
    if not referencia_resolvida:
        referencia_resolvida = dict(recentes.get(referencia) or {})
    snapshot = {
        "id": int((turno or {}).get("id") or time.time_ns()),
        "texto": str(texto or "").strip()[:500],
        "modalidade": str((turno or {}).get("modalidade_geral") or (turno or {}).get("modalidade") or "conversa"),
        "entidades": {k: dict(v) for k, v in recentes.items()},
        "referencia_tipo": referencia,
        "referencia_resolvida": referencia_resolvida,
        "referencia_candidatos": referencia_candidatos,
        "entidade_explicita": dict(explicita),
        "operacao_explicita": operacao,
        "intents_permitidos": list(intents_permitidos),
        "atualidade_factual": classificar_atualidade_factual(texto, turno=turno),
        "ts": instante,
    }
    return snapshot, recentes


def dominio_intent(intent: str) -> str:
    nome = str(intent or "").upper().strip()
    if nome.startswith("IOT_"):
        return "iot"
    if "PLAYLIST" in nome or nome in {"MUSIC_SEARCH", "MEDIA_CONTROL"}:
        return "musica"
    if nome in {"CREATE_FOLDER", "CREATE_FILE", "DELETE_ITEM", "MOVE_ITEM", "FILE_TRANSACTION"}:
        return "arquivo"
    if nome in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"}:
        return "app"
    if nome in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER", "SEARCH"}:
        return "site"
    return ""
