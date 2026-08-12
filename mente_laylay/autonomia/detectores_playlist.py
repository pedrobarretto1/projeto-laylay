"""Detectores determinísticos do domínio de playlists."""

from __future__ import annotations

import re
from typing import Any, Callable, Dict

def detectar_playlist_contextual_musica_atual(
    texto_sem_destino: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    limpar_nome_playlist: Callable[[str], str],
    ultima_playlist: Any = "",
) -> Dict[str, Any] | None:
    """Reconhece salvar a musica atual em playlist e continuacoes como 'essa tambem'."""
    t = str(texto_sem_destino or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    limpar_nome = limpar_nome_playlist if callable(limpar_nome_playlist) else (lambda valor: str(valor or "").strip())

    m_add_musica_playlist = re.search(
        r"\b(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b"
        r".{0,60}?\b(?:essa|esta|a)?\s*(?:musica|música|faixa|canção|cancao)?\b"
        # A preposição isolada ``a`` não pertence a esta etapa: em
        # ``coloca a playlist rock`` ela é o artigo do objeto que deve tocar.
        # A tolerância para ``coloca essa música a playlist`` é feita antes,
        # pela normalização gramatical estreita, que a transforma em ``na``.
        r".{0,30}?\b(?:na|nessa|nesta|para a|pra|em)\s+playlist\s+(?P<nome>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_add_musica_playlist:
        pl = limpar_nome(m_add_musica_playlist.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_ADD", "params": params(nome_playlist=pl)}

    if re.fullmatch(r"(essa|esta|isso|essa aqui|esta aqui)\s+(tambem|também)", t, flags=re.IGNORECASE):
        ultima_pl = str(ultima_playlist or "").strip()
        if ultima_pl:
            return {
                "intent": "PLAYLIST_ADD",
                "params": params(nome_playlist=ultima_pl, referencia_contextual=True),
            }

    if re.fullmatch(
        r"(?:e\s+)?(?:o\s+que|oque)\s+(?:eu\s+)?(?:tenho|tem|ha|há)\s+"
        r"(?:dentro\s+)?(?:nela|nessa|nesta)(?:\s+playlist)?\??",
        t,
        flags=re.IGNORECASE,
    ):
        ultima_pl = str(ultima_playlist or "").strip()
        if ultima_pl:
            return {
                "intent": "PLAYLIST_LIST",
                "params": params(nome_playlist=ultima_pl, referencia_contextual=True),
            }

    return None

def detectar_movimento_playlist(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    limpar_nome_playlist: Callable[[str], str],
) -> Dict[str, Any] | None:
    """Reconhece a transferência explícita de uma faixa entre playlists."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    limpar_nome = (
        limpar_nome_playlist
        if callable(limpar_nome_playlist)
        else lambda valor: str(valor or "").strip()
    )
    padroes = (
        r"(?:tira|remove|retira)\s+(?P<musica>.+?)\s+da\s+playlist\s+"
        r"(?P<origem>.+?)\s+e\s+(?:coloca|bota|adiciona|joga)\s+"
        r"(?:na|pra|para\s+a|para)\s+playlist\s+(?P<destino>.+)",
        r"(?:move|mova|transfere|transfira)\s+(?P<musica>.+?)\s+da\s+"
        r"playlist\s+(?P<origem>.+?)\s+(?:pra|para\s+a|para)\s+playlist\s+"
        r"(?P<destino>.+)",
    )
    for padrao in padroes:
        encontrado = re.search(padrao, t, flags=re.IGNORECASE)
        if not encontrado:
            continue
        musica = str(encontrado.group("musica") or "").strip(" .,!?:;")
        origem = limpar_nome(encontrado.group("origem") or "")
        destino = limpar_nome(encontrado.group("destino") or "")
        if musica and origem and destino:
            params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
            return {
                "intent": "PLAYLIST_MOVE",
                "params": params(musica=musica, origem=origem, destino=destino),
            }
    return None

def detectar_confirmacao_porteiro(
    texto_sem_destino: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    ha_abas_sugeridas: bool = False,
) -> Dict[str, Any] | None:
    """Confirma a limpeza de abas sugeridas pelo Porteiro do navegador."""
    if not ha_abas_sugeridas:
        return None
    t = str(texto_sem_destino or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if re.fullmatch(
        r"(sim|pode|pode fechar|fecha|fecha as abas|limpa|limpa as abas|vai la|vai lá|faz o que sugeriu|manda ver)",
        t,
        flags=re.IGNORECASE,
    ):
        return {"intent": "CLOSE_IDLE_TABS", "params": params()}

    return None

def detectar_playlist_laylay(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    limpar_nome_playlist: Callable[[str], str],
    playlist_laylay_recente: str = "",
    detectar_nome_direto: Callable[[str], str] | None = None,
) -> Dict[str, Any] | None:
    """Reconhece comandos sobre as playlists próprias da Laylay."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    limpar_nome = limpar_nome_playlist if callable(limpar_nome_playlist) else (lambda valor: str(valor or "").strip())

    # Depois que uma curadoria foi listada ou tocada, "dessa playlist" é uma
    # referência válida. A faixa omitida significa a primeira apresentada;
    # não se inventa título nem se confunde a lista própria com a do usuário.
    m_copy_contextual = re.search(
        r"(?:copia|copie|coloca|coloque|adiciona|adicione)\s+"
        r"(?:uma\s+)?(?:musica|música|faixa)\s+(?:dessa|desta|daquela)\s+playlist\s+"
        r"(?:na|para(?:\s+a)?|pra)\s+(?:minha\s+)?playlist\s+(?P<destino>.+?)\??$",
        t,
        flags=re.IGNORECASE,
    )
    origem_recente = str(playlist_laylay_recente or "").strip()

    # A resposta curta com o nome de uma curadoria só é operacional quando o
    # próprio catálogo confirma o nome e existe um fio recente da Laylay. A
    # forma explícita ``playlist <nome>`` também é inequívoca. Assim o nome
    # manual continua natural sem sequestrar uma conversa que apenas mencione
    # as mesmas palavras.
    nome_direto = ""
    if callable(detectar_nome_direto):
        try:
            nome_direto = str(detectar_nome_direto(t) or "").strip()
        except Exception:
            nome_direto = ""
    if nome_direto and (
        origem_recente
        or re.match(r"^(?:a\s+)?playlist\s+", t, flags=re.IGNORECASE)
    ):
        return {
            "intent": "LAYLAY_PLAYLIST_LIST",
            "params": params(
                nome_playlist=nome_direto,
                referencia_contextual=bool(origem_recente),
            ),
        }

    if m_copy_contextual and origem_recente:
        return {
            "intent": "LAYLAY_PLAYLIST_COPY",
            "params": params(
                musica="__primeira__",
                origem=origem_recente,
                destino=limpar_nome(m_copy_contextual.group("destino") or ""),
                referencia_contextual=True,
            ),
        }

    # Autoria expressa posse mesmo sem o pronome "sua":
    # "quais playlists você criou?" pertence à curadoria da Laylay, não ao
    # inventário do usuário nem à última playlist consultada.
    referencia_autoria = bool(re.search(
        r"\b(?:playlist|playlists)\s+(?:que\s+)?"
        r"(?:voce|você|laylay|a\s+laylay|ela)\s+"
        r"(?:criou|fez|montou|separou|organizou|preparou)\b",
        t,
        flags=re.IGNORECASE,
    ))
    referencia_posse = bool(re.search(
        r"\b(?:qual|quais|que)\s+(?:playlist|playlists)\s+"
        r"(?:e|é|sao|são)\s+(?:sua|suas|da\s+laylay|dela)\b",
        t,
        flags=re.IGNORECASE,
    ))
    referencia_curadoria = bool(re.search(
        r"\b(?:sua|suas|da\s+laylay|dela)\s+"
        r"(?:(?:primeira|segunda|terceira|quarta|quinta|\d+[ªa]?)\s+)?playlists?\b",
        t,
        flags=re.IGNORECASE,
    ))

    if not any(x in t for x in [
        "sua playlist",
        "suas playlists",
        "playlist da laylay",
        "playlists da laylay",
        "playlist dela",
        "playlists dela",
    ]) and not referencia_autoria and not referencia_posse and not referencia_curadoria:
        return None

    ordinal = ""
    m_ordinal = re.search(
        r"\b(?P<ordem>primeira|segunda|terceira|quarta|quinta|\d+)[ªa]?\s+playlist\b",
        t,
        flags=re.IGNORECASE,
    )
    if m_ordinal:
        mapa_ordem = {
            "primeira": 1, "segunda": 2, "terceira": 3,
            "quarta": 4, "quinta": 5,
        }
        token = str(m_ordinal.group("ordem") or "").casefold()
        ordinal = f"#{mapa_ordem.get(token, int(token) if token.isdigit() else 1)}"

    m_copy = re.search(
        r"(?:coloca|bota|adiciona|salva|guarda)\s+(?P<musica>.+?)\s+da\s+(?:sua|da\s+laylay|dela)\s+playlist\s+(?P<origem>.+?)\s+(?:na|minha|para a|pra)\s+playlist\s+(?P<destino>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_copy:
        return {
            "intent": "LAYLAY_PLAYLIST_COPY",
            "params": params(
                musica=str(m_copy.group("musica") or "").strip(),
                origem=limpar_nome(m_copy.group("origem") or ""),
                destino=limpar_nome(m_copy.group("destino") or ""),
            ),
        }

    if re.search(r"\b(?:toca|toque|coloca|coloque|abre|abra|bota|escuta|ouvir)\b", t):
        return {
            "intent": "LAYLAY_PLAYLIST_PLAY",
            "params": params(nome_playlist=ordinal),
        }

    if ordinal and re.search(
        r"\b(?:quais|quantas|lista|mostra|o\s+que|oque|tem|conteudo|conteúdo)\b",
        t,
        flags=re.IGNORECASE,
    ):
        return {
            "intent": "LAYLAY_PLAYLIST_LIST",
            "params": params(nome_playlist=ordinal),
        }

    if referencia_autoria or referencia_posse:
        return {
            "intent": "LAYLAY_PLAYLIST_LIST",
            "params": params(nome_playlist=""),
        }

    m_nome = re.search(r"playlist\s+(?P<nome>[a-z0-9\s_]+)$", t, flags=re.IGNORECASE)
    return {
        "intent": "LAYLAY_PLAYLIST_LIST",
        "params": params(nome_playlist=limpar_nome(m_nome.group("nome") if m_nome else "")),
    }

def detectar_playlist_usuario(
    texto_normalizado: str,
    texto_bruto: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
    limpar_nome_playlist: Callable[[str], str],
    extrair_nome_playlist: Callable[[str], str],
    detectar_playlist_nome_direto: Callable[[str], str] | None = None,
) -> Dict[str, Any] | None:
    """Reconhece comandos diretos sobre playlists realmente salvas."""
    t = str(texto_normalizado or "").strip()
    bruto = str(texto_bruto or "")
    # Quantidade/conteúdo com a palavra playlist depois do verbo:
    # "quantas músicas tem a playlist sendo sendo". A forma anterior só
    # aceitava "quantas músicas tem em sendo sendo" e deixava esta consulta
    # objetiva escapar para a conversa generativa.
    # Primeiro a forma em que o verbo vem no fim; caso contrário o padrão
    # flexível abaixo poderia incorporar "tem" ao nome da playlist.
    m_playlist_tem_quantidade = re.search(
        r"\b(?:quantas|quais)\s+(?:as\s+)?(?:musicas|músicas|faixas)\s+"
        r"(?:a|o|na|no|da|do)\s+playlist\s+(?P<nome>.+?)\s+"
        r"(?:tem|possui|guarda|contem|contém)\??$",
        t,
        flags=re.IGNORECASE,
    )
    if m_playlist_tem_quantidade:
        pl = limpar_nome_playlist(m_playlist_tem_quantidade.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}

    m_quantidade_playlist = re.search(
        r"\b(?:quantas|quais)\s+(?:as\s+)?(?:musicas|músicas|faixas)\s+"
        r"(?:(?:que\s+)?(?:eu\s+)?(?:tenho|tem|existem|estao|estão|ficam)\s+)?"
        r"(?:n[ao]|da|do|a|o)?\s*playlist\s+(?P<nome>.+?)\??$",
        t,
        flags=re.IGNORECASE,
    )
    if m_quantidade_playlist:
        pl = limpar_nome_playlist(m_quantidade_playlist.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}

    # Forma natural sem a palavra "playlist": a preposição liga a lista de
    # faixas ao nome do catálogo que deve ser consultado.
    m_conteudo = re.search(
        r"\b(?:quais|quantas|lista(?:r)?|liste|mostra(?:r)?|mostre)\s+"
        r"(?:as\s+)?(?:musicas|músicas|faixas)\s+"
        r"(?:(?:que\s+)?(?:eu\s+)?(?:tenho|tem|estao|estão|ficam)\s+)?"
        r"(?:em|na|no|da|do)\s+(?P<nome>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_conteudo:
        pl = limpar_nome_playlist(m_conteudo.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}

    # "O que tem em Kamaitachi?" só vira consulta operacional quando o alvo
    # corresponde a uma playlist real. Sem essa validação, nomes próprios
    # desconhecidos continuam sendo perguntas normais para a conversa.
    m_conteudo_natural = re.fullmatch(
        r"(?:e\s+)?(?:o\s+que|oque)\s+(?:eu\s+)?(?:tenho|tem|ha|há)\s+"
        r"(?:(?:dentro|salvo|guardado)\s+)?(?:em|na|no|da|do)\s+(?P<nome>.+?)\??",
        t,
        flags=re.IGNORECASE,
    )
    if m_conteudo_natural and callable(detectar_playlist_nome_direto):
        nome_citado = limpar_nome_playlist(m_conteudo_natural.group("nome") or "")
        pl = detectar_playlist_nome_direto(nome_citado) if nome_citado else ""
        if pl:
            return {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}
    if "playlist" not in t:
        return None

    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    limpar_nome = limpar_nome_playlist if callable(limpar_nome_playlist) else (lambda valor: str(valor or "").strip())
    extrair_nome = extrair_nome_playlist if callable(extrair_nome_playlist) else (lambda valor: "")

    m_delete_ref = re.fullmatch(
        r"(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir|tira|tirar)\s+"
        r"(?P<ref>(?:essa|esta|aquela)\s+playlist)",
        t,
        flags=re.IGNORECASE,
    )
    if m_delete_ref:
        return {
            "intent": "PLAYLIST_DELETE",
            "params": params(nome_playlist=str(m_delete_ref.group("ref") or "").strip()),
        }

    m_delete = re.search(
        r"\b(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir|tira|tirar)\s+"
        r"(?:a|o|uma|um)?\s*playlist\s+(?:chamada|com nome|de nome)?\s*(?P<nome>.+)$",
        t,
        flags=re.IGNORECASE,
    )
    if m_delete:
        pl = limpar_nome(m_delete.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_DELETE", "params": params(nome_playlist=pl)}

    m_create_add = re.search(
        r"\b(?:cria|criar|crie)\s+(?:uma\s+)?playlist\s+(?:chamada|com nome|de nome)?\s*(?P<nome>.+?)\s+(?:e\s+)?(?:coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b.*$",
        t,
        flags=re.IGNORECASE,
    )
    if m_create_add:
        pl = limpar_nome(m_create_add.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_ADD", "params": params(nome_playlist=pl)}

    m_create = re.fullmatch(
        r"(?:por\s+favor\s+)?(?:cria|criar|crie|faz|fazer)\s+"
        r"(?:uma\s+)?playlist\s+(?:chamada|com\s+o?\s*nome|de\s+nome)?\s*"
        r"(?P<nome>.+?)\??",
        t,
        flags=re.IGNORECASE,
    )
    if m_create:
        pl = limpar_nome(m_create.group("nome") or "")
        if pl:
            return {"intent": "PLAYLIST_CREATE", "params": params(nome_playlist=pl)}

    if re.search(r"\b(quais|quantas|lista|listar|mostra|mostrar|mostre|fale|falar|diga|dizer|o que tem|oque tem)\b", t):
        pl = extrair_nome(bruto)
        if not pl:
            m = re.search(r"playlist\s+(.+)$", t)
            pl = limpar_nome(m.group(1) if m else "")
        return {"intent": "PLAYLIST_LIST", "params": {"nome_playlist": pl}}

    quer_salvar = (
        re.search(r"\b(coloca|coloque|salva|salve|guarda|guarde|adiciona|adicione|add)\b", t)
        and re.search(r"\b(na|nessa|nesta|para a|pra)\s+playlist\b", t)
    )
    if quer_salvar:
        pl = extrair_nome(bruto)
        return {"intent": "PLAYLIST_ADD", "params": params(nome_playlist=pl)}

    quer_tocar = re.search(
        r"\b(toca|toque|coloca|coloque|abre|abra|ouvir|escuta|escute|"
        r"embaralha|embaralhe|mistura|misture)\b",
        t,
    )
    if quer_tocar:
        m = re.search(r"playlist\s+(.+)$", t)
        nome_bruto = m.group(1) if m else ""
        modo_aleatorio = bool(re.search(
            r"\b(?:aleatorio|aleatório|aleatoria|aleatória|shuffle|"
            r"embaralha(?:da|do)?|mistura(?:da|do)?)\b",
            t,
        ))
        if modo_aleatorio:
            nome_bruto = re.sub(
                r"\s+(?:(?:em\s+)?modo\s+|de\s+forma\s+)?"
                r"(?:aleatorio|aleatório|aleatoria|aleatória|shuffle|"
                r"embaralha(?:da|do)?|mistura(?:da|do)?)\s*$",
                "",
                nome_bruto,
                flags=re.IGNORECASE,
            )
        pl = limpar_nome(nome_bruto)
        if pl:
            return {
                "intent": "PLAYLIST_PLAY",
                "params": params(
                    nome_playlist=pl,
                    **({"modo": "shuffle"} if modo_aleatorio else {}),
                ),
            }

    return None

