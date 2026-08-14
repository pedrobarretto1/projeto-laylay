"""Detectores determinísticos pequenos e reutilizáveis da Laylay."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Dict

from mente_laylay.cognicao.referencias_linguagem import (
    separar_alvo_e_complemento_foco,
    valor_e_referencia_contextual,
)
from mente_laylay.cognicao.modalidade_turno import analisar_protecao_operacional
from mente_laylay.cognicao.normalizacao_linguagem import (
    corrigir_erros_portugues_operacionais,
    texto_pede_opiniao,
)
from mente_laylay.autonomia.detectores_playlist import (
    detectar_confirmacao_porteiro,
    detectar_movimento_playlist,
    detectar_playlist_contextual_musica_atual,
    detectar_playlist_laylay,
    detectar_playlist_usuario,
)


def texto_pede_clima_atual(texto_normalizado: str) -> bool:
    """Reconhece consultas meteorológicas atuais e de horizonte próximo."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return False
    return (
        any(p in t for p in (
            "quantos graus", "temperatura", "previsao do tempo", "previsão do tempo",
        ))
        or bool(re.search(
            r"\b(?:qual|como\s+(?:esta|está|estara|estará|ta|tá|e|é))\s+"
            r"(?:o\s+)?(?:clima|tempo)\b",
            t,
        ))
        or bool(re.search(
            r"\b(?:clima|tempo)\s+(?:hoje|agora|em|de|no|na)\b",
            t,
        ))
        or bool(re.search(
            r"\b(?:vai\s+chover|chove(?:r)?\s+hoje|como\s+fica\s+(?:o\s+)?tempo|"
            r"tempo\s+por\s+(?:ai|aí|aqui))\b",
            t,
        ))
        or bool(re.search(
            r"\b(?:clima|tempo)\b.{0,24}\b(?:amanha|amanhã|"
            r"depois\s+de\s+amanha|depois\s+de\s+amanhã)\b",
            t,
        ))
    )


def normalizar_pedido_natural(texto_normalizado: str) -> tuple[str, str]:
    """Remove a moldura social do pedido sem apagar sua intenção prática.

    Retorna ``(texto_operacional, modalidade)``; falas deliberativas continuam
    intactas para não transformar pensamento em comando.
    """
    t = re.sub(r"\s+", " ", str(texto_normalizado or "")).strip()
    if not t:
        return "", ""
    protecao = analisar_protecao_operacional(t)
    if protecao.get("modalidade") == "deliberacao":
        return t, "deliberativo"

    original = t
    molduras = (
        r"^(?:ei\s+)?(?:laylay?\s+)?(?:sera que\s+)?(?:voce\s+)?"
        r"(?:pode|poderia|consegue|conseguiria)\s+",
        r"^(?:ei\s+)?(?:laylay?\s+)?(?:sera que\s+)?(?:da|tem)\s+(?:pra|para|como)\s+"
        r"(?:voce\s+)?",
        r"^(?:ei\s+)?(?:laylay?\s+)?(?:faz|faca)\s+(?:o\s+)?favor\s+de\s+",
        r"^(?:eu\s+)?queria\s+que\s+(?:voce\s+)?",
    )
    for padrao in molduras:
        novo = re.sub(padrao, "", t, count=1)
        if novo != t:
            t = novo.strip()
            break

    # Formas do subjuntivo comuns depois de "queria que você...".
    conjugacoes = {
        "abrisse": "abre", "fechasse": "fecha", "ligasse": "liga",
        "desligasse": "desliga", "colocasse": "coloca", "tocasse": "toca",
        "pausasse": "pausa", "aumentasse": "aumenta", "abaixasse": "abaixa",
        "diminuísse": "diminui", "diminuisse": "diminui",
    }
    primeira, *resto = t.split()
    if primeira in conjugacoes:
        t = " ".join([conjugacoes[primeira], *resto]).strip()
    # Desejo com estado imediato e alvo concreto e um pedido, mesmo quando o
    # portugues usa "estivesse aberto" em vez do verbo imperativo. Limitamos a
    # conversao a moldura "queria que" já removida acima e ao marcador agora;
    # hipóteses como "talvez fosse legal abrir" continuam deliberativas.
    if original != t:
        estado_aberto = re.fullmatch(
            r"(?:(?:o|a|os|as)\s+)?(?P<alvo>.+?)\s+estivesse(?:m)?\s+"
            r"abert[oa]s?\s+agora",
            t,
            flags=re.IGNORECASE,
        )
        if estado_aberto:
            alvo = str(estado_aberto.group("alvo") or "").strip()
            if alvo:
                t = f"abre {alvo}"
    return (t or original), ("pedido" if t != original else "direto")


def corrigir_verbo_operacional_digitado(texto_normalizado: str) -> str:
    """Compatibilidade: usa o corretor canônico, sem regra privada de IoT."""
    corrigido, _eventos = corrigir_erros_portugues_operacionais(
        texto_normalizado,
    )
    return corrigido


def extrair_intencao_abrir_app(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str],
    limpar_destino: Callable[[str], str],
    apps_map: Dict[str, Any],
    sites_diretos: Dict[str, Any],
) -> Dict[str, Any] | None:
    """Extrai abertura explícita distinguindo aplicativo instalado de destino web."""
    bruto = str(texto or "").strip()
    if not bruto:
        return None
    t = normalizar_texto(bruto) if callable(normalizar_texto) else bruto.lower()
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if not t or "playlist" in t:
        return None
    if any(x in t for x in ["instagram.com/direct", "instagram.com", "www.instagram.com", "instagram direct", "direct/t/"]):
        return {"intent": "OPEN_URL", "params": {"alvo": "instagram"}}
    if re.search(r"https?://\S+", bruto) and "instagram" in t:
        return {"intent": "OPEN_URL", "params": {"alvo": "instagram"}}

    encontrado = re.search(
        r"\b(?:pode\s+|da\s+pra\s+|dá\s+pra\s+|por favor\s+)?"
        r"(abre|abra|abrir|inicia|iniciar|executa|executar|roda|rodar)\s+"
        # O artigo precisa terminar em espaço. Sem isso, o ``o`` inicial de
        # ``Opera`` era consumido como artigo e o executor recebia ``pera``.
        r"(?:(?:o|a|os|as|um|uma)\s+)?(.+)$",
        t,
    )
    if not encontrado:
        return None
    nome = (encontrado.group(2) or "").strip()
    nome = limpar_destino(nome) if callable(limpar_destino) else nome
    nome = re.sub(r"\s+(agora|aqui|ai|aí|por favor|pfv)$", "", nome).strip()
    nome = re.sub(r"^(o|a|os|as|um|uma)\s+", "", nome).strip()
    nome = re.sub(r"^(?:programa|app|aplicativo)\s+(?:chamado|chamada|com\s+nome|de\s+nome)\s+", "", nome).strip()
    nome, complemento_foco = separar_alvo_e_complemento_foco(nome)
    if (
        not nome
        or nome.casefold() in {"que", "o que", "qual"}
        or (valor_e_referencia_contextual(nome) and not complemento_foco)
    ):
        return None

    nome_norm = nome.lower()
    sites = sites_diretos if isinstance(sites_diretos, dict) else {}
    if nome_norm in sites or nome_norm.startswith("site ") or nome_norm in {"youtube", "google", "spotify", "whatsapp", "chatgpt"}:
        return {"intent": "OPEN_URL", "params": {"alvo": nome_norm.replace("site ", "").strip()}}
    apps = apps_map if isinstance(apps_map, dict) else {}
    for app in sorted(apps.keys(), key=len, reverse=True):
        if nome_norm == app or nome_norm.startswith(app + " ") or app in nome_norm:
            params_app = {"nome_app": app}
            if complemento_foco:
                params_app["modo"] = "focus"
            return {"intent": "APP_OPEN", "params": params_app}
    params_app = {"nome_app": nome}
    if complemento_foco:
        params_app["modo"] = "focus"
    return {"intent": "APP_OPEN", "params": params_app}


def texto_expresso_melhor_no_deterministico(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str],
) -> bool:
    """Indica comandos explícitos cuja rota local é mais segura que IA-first."""
    t = normalizar_texto(texto or "") if callable(normalizar_texto) else str(texto or "").lower().strip()
    if not t:
        return False
    t_layout = re.sub(r"^(?:agora|entao|então)\s+", "", t).strip()
    # O porteiro consulta os próprios detectores canônicos: ele só decide se a
    # rota local deve receber a frase, sem manter uma segunda lista de formas
    # linguísticas para visão ou briefing.
    visual = detectar_url_visual(
        t,
        str(texto or ""),
        params_cb=lambda **kwargs: kwargs,
    )
    if str((visual or {}).get("intent") or "").upper() in {
        "SCREEN_CAPTURE", "VISION_QUERY",
    }:
        return True
    informacao = detectar_email_notificacao_briefing(
        t,
        params_cb=lambda **kwargs: kwargs,
    )
    if str((informacao or {}).get("intent") or "").upper() == "BRIEFING_REPEAT":
        return True
    if texto_pede_clima_atual(t):
        return True
    if re.search(
        r"\b(?:qual|que)\s+(?:e|é\s+)?(?:a\s+)?(?:musica|música|faixa|som)\b"
        r".{0,24}\b(?:tocando|ouvindo)\b|"
        r"\bo\s+que\s+(?:esta|está|ta|tá)\s+tocando\b",
        t,
    ):
        return True
    if re.search(r"\b(?:email|emails|e-mail)\b", t) and re.search(
        r"\b(?:le|lê|leia|ler|mostra|verifica|checa|resuma|sincroniza|atualiza|"
        r"quais|quantos|lista|listar|fale|diga)\b", t
    ):
        return True
    if re.search(r"\b(?:volume|som)\b", t) and (
        re.search(r"\b\d{1,3}\s*%?\b", t)
        or re.search(r"\b(?:maximo|máximo|minimo|mínimo|mudo|mute|aumenta|abaixa|diminui)\b", t)
    ):
        return True
    if re.search(r"\b(?:como|qual)\s+(?:esta|está|ta|tá)\s+(?:o\s+)?(?:clima|tempo)\b", t):
        return True
    if any(p in t for p in ["playlist", "playlists"]) and re.search(
        r"\b(coloca|coloque|toca|toque|abre|abra|ouvir|escuta|escute|salva|salve|guarda|guarde|adiciona|adicione|lista|listar|mostra|mostrar|mostre|fale|fala|diga|diz|quais)\b",
        t,
    ):
        return True
    if re.fullmatch(r"(essa|esta|isso|essa aqui|esta aqui)\s+(tambem|também)", t):
        return True
    if re.search(
        r"\b(?:pula|pule|pular|passa)\s+(?:(?:esse|essa|o|a)\s+)?"
        r"(?:an(?:u|ú)ncio|propaganda)\b",
        t,
    ):
        return True
    if re.search(
        r"\b(?:pausa|pause|despausa|retoma|proxima|próxima|anterior)\b",
        t,
    ) and re.search(r"\b(?:musica|música|video|vídeo|som|ela|ele|isso)\b", t):
        return True
    if re.fullmatch(
        r"(?:a\s+)?(?:proxima|próxima|proximo|próximo)|"
        r"volta\s+(?:para|pra)\s+(?:a\s+)?anterior",
        t.strip(" .,!?:;"),
    ):
        # O detector ainda exige contexto musical real antes de executar.
        return True
    if any(v in t_layout for v in ["organiza", "organizar", "arruma", "arrumar"]) and any(
        alvo in t_layout for alvo in ["area de trabalho", "área de trabalho", "desktop", "tela", "janelas", "janela"]
    ):
        return True
    if re.search(r"^(?:coloca|coloque|bota|ponha|põe|poe|move|mova|posiciona|posicione|deixa|joga)\b", t_layout) and re.search(
        r"\b(?:(?:na|a|à|para a)\s+(?:esquerda|direita)|"
        r"(?:no|pro|para o|do)\s+lado\s+(?:esquerdo|direito))\b",
        t_layout,
    ):
        return True
    if re.search(r"\b(?:esquerda|direita)\b", t) and re.search(
        r"\b(?:e|,)\b.*\b(?:esquerda|direita)\b", t,
    ):
        return True
    if any(x in t for x in ["despausa", "despausar", "retoma a musica", "retoma a música", "continua a musica", "continua a música"]):
        return True
    if any(x in t for x in ["pausa a musica", "pausa a música", "proxima musica", "próxima música", "musica anterior", "música anterior", "volta a musica", "volta a música"]):
        return True
    if re.search(r"\b(liga|ligar|ligue|desliga|desligar|desligue|alterna|alternar)\b", t) and re.search(
        r"\b(dispositivo|aparelho|tomada|ventilador|luz|lampada|lâmpada|iot|ele|ela)\b", t
    ):
        return True
    if re.search(r"\b(dispositivo|aparelho|tomada|ventilador|iot)\b", t) and re.search(
        r"\b(status|estado|ligado|ligada|desligado|desligada|quais|lista|mostrar|mostra)\b", t
    ):
        return True
    if re.match(r"^\s*(abre|abra|abrir|fecha|fechar|maximiza|maximizar|traz|coloca|bota|deixa)\b", t):
        if any(x in t for x in ["steam", "opera", "chrome", "edge", "vscode", "vs code", "visual studio code", "janela", "foco", "tela cheia", "fullscreen"]):
            return True
    if re.match(r"^\s*(abre|abra|abrir|fecha|feche|fechar|maximiza|maximize|maximizar)\b", t):
        alvo = re.sub(
            r"^\s*(?:abre|abra|abrir|fecha|feche|fechar|maximiza|maximize|maximizar)\s+",
            "", t,
        ).strip()
        if alvo and alvo not in {"isso", "isto", "ele", "ela", "ai", "aí", "aqui", "o que", "que"}:
            return True
    if re.match(r"^\s*(coloca|bota|deixa|traz|maximiza|maximizar)\b", t):
        if any(x in t for x in ["ele", "ela", "isso"]) and any(x in t for x in ["foco", "tela cheia", "fullscreen", "na frente", "pra frente", "para frente"]):
            return True
    if re.match(r"^\s*(cria|criar|crie|apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\b", t):
        if any(x in t for x in ["pasta", "arquivo", "ela", "ele", "isso", "essa", "esse"]):
            return True
    if re.search(
        r"^(?:encontra|encontre|acha|ache|procura|procure|busca|buscar|pesquisa|localiza|localize)\b",
        t,
    ) and re.search(r"\b(?:arquivo|documento|codigo|código|imagem|foto|script|projeto)\b", t):
        return True
    if re.search(r"^onde\s+(?:esta|está|fica)\b", t) and re.search(
        r"\b(?:arquivo|documento|codigo|código|imagem|foto|script)\b", t,
    ):
        return True
    if re.search(r"^(?:quais?|mostra|mostre|lista|liste)\b", t) and re.search(
        r"\b(?:arquivos|documentos|imagens|fotos|scripts)\b", t,
    ):
        return True
    return "dentro dela" in t and "pasta" in t


def preparar_entrada_deterministica(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str],
    texto_conversa_casual_sem_acao: Callable[[str], bool],
    texto_bloqueia_playlist_agora: Callable[[str], bool],
    texto_social_curto: Callable[[str], bool],
    ignorar_token_solto: Callable[[str], bool],
    fluxo_prioritario_da_ia: Callable[[str], bool],
    texto_expresso_melhor_no_deterministico: Callable[[str], bool],
    texto_depende_de_contexto: Callable[[str], bool],
    limpar_destino_pc_b: Callable[[str], str],
) -> Dict[str, Any]:
    """Prepara e filtra a entrada antes da sequencia de detectores determinísticos."""
    bruto = str(texto or "").strip()
    if not bruto:
        return {"status": "ignorar"}

    normalizar = normalizar_texto if callable(normalizar_texto) else (lambda valor: str(valor or "").strip().lower())
    inicial = corrigir_verbo_operacional_digitado(normalizar(bruto))
    protecao_original = analisar_protecao_operacional(inicial)
    if (
        protecao_original.get("bloqueia_execucao")
        and re.search(
            r"\b(?:tela|print|screenshot|pagina|página|site|aba|video|vídeo|briefing)\b",
            inicial,
        )
    ):
        return {
            "status": "ignorar",
            "modalidade": str(protecao_original.get("modalidade") or "protegida"),
        }
    # Negação e pergunta sobre uma ação não autorizam essa ação. Exemplo:
    # "não abre o quê?" é pedido de esclarecimento, não APP_OPEN("que").
    if re.search(
        r"^(?:nao|não)\s+(?:abre|abrir|abriu|fecha|fechar|ligar|liga|desligar|desliga|toca|coloca)\b.*\b(?:que|qual|porque|por que)\b",
        inicial,
    ):
        return {"status": "ignorar", "modalidade": "pergunta_negativa"}
    natural, modalidade = normalizar_pedido_natural(inicial)
    if modalidade == "deliberativo":
        return {"status": "ignorar", "modalidade": modalidade}
    # Operações locais inequívocas recebem a primeira chance mesmo quando a
    # conversa, o modo jogo ou uma referência recente fariam a entrada parecer
    # contextual. Os detectores posteriores ainda precisam validar domínio,
    # alvo e parâmetros antes de qualquer execução.
    expresso_deterministico = bool(
        callable(texto_expresso_melhor_no_deterministico)
        and texto_expresso_melhor_no_deterministico(natural)
    )
    # O classificador de conversa recebe a parte operacional. Assim "será que
    # você pode abrir..." não parece apenas uma pergunta casual.
    if (
        not expresso_deterministico
        and callable(texto_conversa_casual_sem_acao)
        and texto_conversa_casual_sem_acao(natural)
    ):
        return {"status": "ignorar"}
    if callable(texto_bloqueia_playlist_agora) and texto_bloqueia_playlist_agora(bruto):
        return {"status": "intent", "resultado": {"intent": "STOP_PLAYLIST_CONTEXT", "params": {}}}
    if not expresso_deterministico and callable(texto_social_curto) and texto_social_curto(bruto):
        return {"status": "ignorar"}

    t = natural
    t = re.sub(r"\b(laylay|lay|por favor|pfv|pra mim|para mim)\b", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    if not t:
        return {"status": "ignorar"}
    if callable(ignorar_token_solto) and ignorar_token_solto(t):
        return {"status": "ignorar"}

    # A preferência histórica pela IA não pode esconder comandos diretos dos
    # especialistas locais. Ela existe para linguagem ambígua, não para uma
    # frase que já começa com um verbo operacional. O detector do domínio
    # ainda valida alvo e parâmetros, e o árbitro do turno continua sendo a
    # autoridade que permite ou bloqueia a execução.
    comando_operacional_direto = bool(re.match(
        r"^(?:abre|abra|abrir|fecha|feche|fechar|maximiza|maximize|maximizar|"
        r"coloca|coloque|bota|põe|poe|toca|toque|escuta|escute|ouvir|"
        r"pausa|pause|retoma|continua|pula|pule|"
        r"liga|ligue|ligar|desliga|desligue|desligar|"
        r"cria|crie|criar|apaga|apague|apagar|remove|remova|remover|"
        r"deleta|delete|deletar|exclui|exclua|excluir|"
        r"escreve|escreva|escrever|grava|grave|gravar|"
        r"pesquisa|pesquise|pesquisar|busca|busque|buscar|procura|procure|procurar|"
        r"organiza|organize|organizar|move|mova|mover|renomeia|renomeie|renomear|"
        r"salva|salve|salvar|guarda|guarde|guardar|adiciona|adicione|adicionar|"
        r"lista|liste|listar|mostra|mostre|mostrar|"
        r"aumenta|aumente|abaixa|abaixe|diminui|diminua|trava|trave|bloqueia|bloqueie)\b",
        t,
    ))
    if (
        callable(fluxo_prioritario_da_ia)
        and fluxo_prioritario_da_ia(t)
        and not expresso_deterministico
        and not comando_operacional_direto
    ):
        return {"status": "ignorar"}

    if (
        not expresso_deterministico
        and callable(texto_depende_de_contexto)
        and texto_depende_de_contexto(t)
    ):
        comandos_contextuais = [
            "fecha", "fechar", "mata", "derruba", "cancela", "cancelar",
            "volume", "tela cheia", "fullscreen", "em foco", "abrir", "abre",
            "coloca", "coloque", "salva", "salve", "guarda", "guarde",
            "adiciona", "adicione", "lista", "listar", "mostra", "mostrar",
            "toca", "toque", "liga", "ligar", "desliga", "desligar",
            "pesquisa", "pesquisar", "busca", "buscar", "procura", "procurar",
            "move", "mover", "renomeia", "renomear",
            "escreve", "escrever", "escreva", "grava", "gravar", "grave",
            "essa tambem", "essa também", "esse tambem", "esse também",
            "apaga", "apagar", "deleta", "deletar", "remove", "remover", "exclui", "excluir",
        ]
        if not any(x in t for x in comandos_contextuais):
            return {"status": "ignorar"}

    limpar_destino = limpar_destino_pc_b if callable(limpar_destino_pc_b) else (lambda valor: str(valor or ""))
    return {
        "status": "ok",
        "bruto": bruto,
        "modalidade": modalidade,
        "texto_normalizado": t,
        "texto_sem_destino": limpar_destino(t),
    }


def detectar_volume_ou_midia(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    contexto_musical_ativo: bool = False,
    contexto_volume_ativo: bool = False,
) -> Dict[str, Any] | None:
    """Reconhece volume e controles de mídia sem depender da IA."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    # Uma pergunta sobre o player é leitura. Ela precisa vencer qualquer
    # continuidade mutante para nunca virar ``replay`` por associação.
    if re.search(
        r"\b(?:qual|que)\s+(?:e|é\s+)?(?:a\s+)?(?:musica|música|faixa|som)\b"
        r".{0,24}\b(?:tocando|ouvindo)\b|"
        r"\bo\s+que\s+(?:esta|está|ta|tá)\s+tocando\b",
        t,
    ):
        return {
            "intent": "MUSIC_STATUS",
            "params": params(
                acao="status", platform="music", somente_leitura=True,
            ),
        }

    menciona_volume = "volume" in t or bool(re.search(r"\bsom\b", t))
    referencia_extremo = bool(re.search(
        r"\b(?:ao|no|para|pro|pra)?\s*(?:maximo|máximo|minimo|mínimo)\b|\bno\s+talo\b",
        t,
    ))
    if menciona_volume or (contexto_volume_ativo and referencia_extremo) or any(p in t for p in ["mudo", "mute", "muta", "mutar", "desmuta", "desmutar", "sem som", "silencio", "silêncio", "mais alto", "mais baixo"]):
        m_vol = re.search(r"\b(?:volume|som)\s*(?:em|no|para|pra)?\s*(\d{1,3})\s*%?\b", t)
        if m_vol:
            nivel = max(0, min(100, int(m_vol.group(1))))
            return {"intent": "VOLUME", "params": params(acao="set", nivel_volume=nivel)}
        if re.search(r"\b(?:maximo|máximo)\b|\bno\s+talo\b", t):
            return {"intent": "VOLUME", "params": params(acao="set", nivel_volume=100)}
        if re.search(r"\b(?:minimo|mínimo)\b", t):
            return {"intent": "VOLUME", "params": params(acao="set", nivel_volume=0)}
        if any(p in t for p in ["desmuta", "desmutar", "tira do mudo", "com som"]):
            return {"intent": "VOLUME", "params": params(acao="unmute")}
        if any(p in t for p in ["mudo", "mute", "muta", "mutar", "sem som", "silencio", "silêncio", "silenciar"]):
            return {"intent": "VOLUME", "params": params(acao="mute")}
        if any(p in t for p in ["aumenta", "aumentar", "sobe", "subir", "mais alto"]):
            return {"intent": "VOLUME", "params": params(acao="up")}
        if any(p in t for p in ["abaixa", "baixa", "baixar", "diminui", "diminuir", "mais baixo"]):
            return {"intent": "VOLUME", "params": params(acao="down")}

    if contexto_musical_ativo and any(x in t for x in ["despausa ela", "despausa ele", "despusa ela", "despusa ele", "depausa ela", "depausa ele", "retoma ela", "retoma ele", "continua ela", "continua ele"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="play", platform="music")}
    if contexto_musical_ativo and any(x in t for x in ["pausa ela", "pausa ele", "pausa isso", "para ela", "para ele", "para isso"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="pause", platform="music")}
    if re.search(
        r"\b(?:pula|pule|pular|passa|tira|remove)\s+(?:(?:esse|essa|o|a)\s+)?(?:anuncio|anúncio|propaganda)\b",
        t,
    ):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="skip_ad", platform="youtube")}
    if any(x in t for x in ["despausa", "despausar", "despusa", "despusar", "depausa", "depausar", "retoma a musica", "retoma a música", "continua a musica", "continua a música", "volta a tocar", "continua tocando"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="play")}
    if any(x in t for x in ["pausa", "pause", "pausar", "para a musica", "para música", "para musica", "play pause"]):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="pause")}
    if re.search(
        r"\b(?:reinicia|reiniciar|recomeca|recomeça|recomecar|recomeçar|"
        r"repete|repetir)\s+(?:(?:essa|esta|a)\s+)?(?:musica|música|faixa)\b",
        t,
    ):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="replay")}
    if re.search(
        r"\b(?:ativa|ative|desativa|desative|alterna|alterne)\s+"
        r"(?:(?:a|o)\s+)?(?:repeticao|repetição|loop)\b|"
        r"\b(?:repeticao|repetição|loop)\s+(?:da|dessa|nesta|na)\s+"
        r"(?:musica|música|faixa)\b",
        t,
    ):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="repeat_toggle")}
    proxima_por_fala_natural = bool(re.fullmatch(
        r"(?:passa|pasa|pula|pule)(?:\s+(?:para|pra|pro))?\s+(?:a\s+)?"
        r"(?:proxima|próxima|proxma)(?:\s+(?:musica|música|faixa))?",
        t,
    ))
    proxima_curta = bool(re.fullmatch(
        r"(?:a\s+)?(?:proxima|próxima|proximo|próximo|pula|pule)", t,
    ))
    proxima_nomeada = bool(re.search(
        r"\b(?:proxima|próxima)\s+(?:musica|música|faixa)\b", t,
    ))
    if "playlist" not in t and (
        proxima_por_fala_natural
        or proxima_nomeada
        or (proxima_curta and contexto_musical_ativo)
    ):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="next")}
    anterior_explicita = any(x in t for x in [
        "volta a musica", "volta a música", "música anterior", "musica anterior",
    ])
    anterior_contextual = bool(re.fullmatch(
        r"(?:a\s+)?anterior|volta\s+(?:para|pra)\s+(?:a\s+)?anterior",
        t.strip(" .,!?:;"),
    ))
    if anterior_explicita or (anterior_contextual and contexto_musical_ativo):
        return {"intent": "MEDIA_CONTROL", "params": params(acao="prev")}

    return None


def detectar_email_notificacao_briefing(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    contexto_email_ativo: bool = False,
) -> Dict[str, Any] | None:
    """Reconhece pedidos diretos de email, notificacao e briefing."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    if analisar_protecao_operacional(t).get("bloqueia_execucao"):
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    # Depois de uma leitura confirmada, pronomes como "deles" referem-se ao
    # lote observado pelo executor. Essa rota volta ao mesmo leitor/cache; não
    # pede à LLM que adivinhe a urgência das mensagens.
    if contexto_email_ativo and re.search(
        r"\b(?:(?:algum|alguns|quais|quantos|tem|tinha|e)\b.{0,28})?"
        r"(?:urgente|urgentes|importante|importantes|prioritario|prioritarios|prioritários)\b",
        t,
    ):
        return {
            "intent": "EMAIL_READ",
            "params": params(urgentes=True, referencia_contextual=True),
        }

    menciona_email = bool(re.search(r"\be(?:\s|-)?mails?\b", t))
    if menciona_email:
        if any(p in t for p in ["calar a boca", "silencia esse remetente", "silencia a shein", "manda a shein", "manda o remetente", "silenciar esse email", "ignorar esse email", "não me enche"]):
            alvo = ""
            m_alvo = re.search(r"manda a\s+(?P<alvo>[a-z0-9\s]+?)\s+calar a boca", t, flags=re.IGNORECASE)
            if m_alvo:
                alvo = str(m_alvo.group("alvo") or "").strip()
            return {"intent": "NOTIFICATIONS", "params": params(acao="silenciar_remetente", alvo=alvo)}
        if any(p in t for p in ["sincroniza", "sincronizar", "atualiza", "atualizar"]):
            return {"intent": "EMAIL_SYNC", "params": params()}
        if any(p in t for p in ["urgente", "urgentes", "importante", "importantes", "prioritario", "prioritários", "prioritarios"]):
            return {"intent": "EMAIL_READ", "params": params(urgentes=True)}
        if any(p in t for p in ["le", "lê", "ler", "mostra", "ver", "verifica", "checa", "quantos", "quais", "fale", "falar", "resuma", "resumo", "me fala", "me fale", "o que eles me falam", "o que falam"]):
            return {"intent": "EMAIL_READ", "params": params()}

    if "briefing" in t and (
        any(p in t for p in ["fala", "fale", "mostra", "mostrar", "repete", "repetir", "diz", "diga", "conta", "contar", "passa"])
        or bool(re.search(r"\bqual\s+(?:e|é\s+)?o?\s*briefing\b", t))
        or "briefing de hoje" in t
    ):
        return {"intent": "BRIEFING_REPEAT", "params": params()}

    if "notificacao" in t or "notificacoes" in t or "notificação" in t or "notificações" in t:
        if any(p in t for p in ["silencia", "silenciar", "desativa", "desativar", "mute"]):
            return {"intent": "NOTIFICATIONS", "params": params(acao="silenciar")}
        if any(p in t for p in ["ativa", "ativar", "reativa", "reativar"]):
            return {"intent": "NOTIFICATIONS", "params": params(acao="ativar")}
        if any(p in t for p in ["le", "lê", "ler", "mostra", "ver", "verifica"]):
            return {"intent": "NOTIFICATIONS", "params": params(acao="ler")}

    return None


def detectar_consulta_aprendizados(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece perguntas naturais sobre o que a Laylay aprendeu da pessoa."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    t = unicodedata.normalize("NFKD", t.casefold())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"\s+", " ", t).strip()
    # Explicações abstratas pertencem à conversa. Esta rota consulta apenas o
    # que a memória persistente aprendeu sobre a pessoa.
    if re.search(
        r"\b(?:como|o que e|explique|explica)\b.{0,35}\b"
        r"(?:ia|inteligencia artificial|machine learning|aprendizado de maquina)\b",
        t,
    ):
        return None
    consulta_identidade = bool(re.fullmatch(
        r"(?:qual (?:e )?(?:o )?meu nome|como (?:e que )?eu me chamo|"
        r"(?:voce )?(?:sabe|lembra) (?:qual (?:e )?)?(?:o )?meu nome|"
        r"(?:voce )?lembra do meu nome)[?.!]*",
        t,
    ))
    if consulta_identidade:
        params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
        return {
            "intent": "LEARNING_QUERY",
            "params": params(
                limit=1,
                query="nome do usuario",
                modo="identidade",
            ),
        }
    consulta_preferencias = bool(re.fullmatch(
        r"(?:(?:do que|o que) eu (?:gosto|prefiro|curto)|"
        r"quais (?:sao )?(?:as )?minhas preferencias|"
        r"(?:voce )?(?:sabe|lembra) (?:d[oa] que eu gosto|das minhas preferencias))"
        r"[?.!]*",
        t,
    ))
    if consulta_preferencias:
        params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
        return {
            "intent": "LEARNING_QUERY",
            "params": params(limit=5, query="preferencia", modo="listar"),
        }
    consulta_aversoes = bool(re.fullmatch(
        r"(?:(?:do que|o que) eu (?:nao gosto|detesto|odeio)|"
        r"quais (?:sao )?(?:as )?coisas que eu (?:nao gosto|detesto|odeio)|"
        r"(?:voce )?(?:sabe|lembra) (?:d[oa] que eu nao gosto|"
        r"do que eu detesto|do que eu odeio))"
        r"[?.!]*",
        t,
    ))
    if consulta_aversoes:
        params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
        return {
            "intent": "LEARNING_QUERY",
            "params": params(
                limit=5,
                query="preferencia",
                modo="listar",
                polaridade="negativa",
            ),
        }
    consultas_fato_pessoal = (
        (r"(?:onde eu moro|qual (?:e )?(?:a )?minha cidade)[?.!]*", "mora local"),
        (
            r"(?:com o que eu trabalho|qual (?:e )?(?:a )?minha profissao)"
            r"[?.!]*",
            "trabalho profissao",
        ),
        (r"(?:o que eu estudo|qual (?:e )?(?:a )?minha area de estudo)[?.!]*", "estudo"),
    )
    for padrao, consulta in consultas_fato_pessoal:
        if re.fullmatch(padrao, t):
            params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
            return {
                "intent": "LEARNING_QUERY",
                "params": params(
                    limit=3,
                    query=consulta,
                    modo="listar",
                    categoria="fato_pessoal",
                ),
            }
    verificacao = re.search(
        r"\b(?:voce\s+)?(?:ainda\s+)?lembra\s+que\s+(?P<consulta>.+?)[?.!]*$",
        t,
    )
    if verificacao:
        consulta = str(verificacao.group("consulta") or "").strip(" .?!")
        params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
        return {
            "intent": "LEARNING_QUERY",
            "params": params(limit=3, query=consulta, modo="verificar"),
        }
    consulta_pessoal = re.fullmatch(
        r"(?P<consulta>(?:eu\s+)?(?:nao\s+)?(?:gosto|curto|amo|adoro|odeio|prefiro)"
        r"(?:\s+(?:muito|bastante|demais))?\s+(?:de|do|da|dos|das)\s+.+?)\s*\?",
        t,
    )
    if consulta_pessoal:
        consulta = str(consulta_pessoal.group("consulta") or "").strip()
        params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
        return {
            "intent": "LEARNING_QUERY",
            "params": params(limit=3, query=consulta, modo="verificar"),
        }
    estruturas = (
        r"^(?:voce\s+)?lembra\s+de\s+mim[?.!]*$",
        r"\b(?:o\s+que|quais\s+coisas?)\b.{0,25}\b"
        r"(?:voce\s+)?sabe\b.{0,20}\bsobre\s+mim\b",
        r"\b(?:o\s+que|quais\s+coisas?|que\s+coisas?)\b.{0,45}\b"
        r"(?:voce\s+)?(?:aprendeu|guardou|lembra)\b(?:.{0,30}\b(?:sobre\s+mim|comigo))?",
        r"\b(?:o\s+que|quais\s+coisas?|que\s+coisas?)\b.{0,30}\b"
        r"eu\s+(?:te\s+)?(?:ensinei|falei|contei)\b",
        r"\b(?:voce\s+)?lembra\b.{0,35}\b(?:do\s+que|das\s+coisas\s+que)\b"
        r".{0,25}\beu\s+(?:te\s+)?(?:ensinei|falei|contei)\b",
        r"\b(?:me\s+)?(?:fala|fale|conta|conte|diz|diga|lembra|lembre)\b"
        r".{0,35}\b(?:o\s+que|do\s+que)\b.{0,35}\b"
        r"(?:aprendeu|eu\s+(?:te\s+)?(?:ensinei|falei|contei))\b",
        r"\b(?:quais|mostra|liste|lista|fala|fale|conte|diz|diga)\b"
        r".{0,30}\b(?:seus?|os|meus?)\s+aprendizados\b",
        r"\b(?:seus?|os)\s+aprendizados\b",
        r"\b(?:o\s+que|quais\s+coisas?)\b.{0,35}\b"
        r"(?:lembra|guardou)\b.{0,25}\bsobre\s+mim\b",
    )
    if not any(re.search(padrao, t, flags=re.IGNORECASE) for padrao in estruturas):
        return None
    params = params_cb if callable(params_cb) else lambda **kwargs: kwargs
    return {
        "intent": "LEARNING_QUERY",
        "params": params(limit=10, modo="retrato"),
    }


def detectar_clima(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece perguntas meteorologicas diretas e preserva a localidade citada."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    pede_clima = texto_pede_clima_atual(t)
    if not pede_clima:
        return None

    local = ""
    padroes_local = [
        r"\b(?:em|de)\s+([a-zà-ÿ][a-zà-ÿ\s-]*?)(?:\?|$)",
        r"\b(?:no|na)\s+([a-zà-ÿ][a-zà-ÿ\s-]*?)(?:\?|$)",
    ]
    for padrao in padroes_local:
        encontrado = re.search(padrao, t, flags=re.IGNORECASE)
        if encontrado:
            local = str(encontrado.group(1) or "").strip(" .,!?:;")
            break
    if local.casefold() in {
        "hoje", "agora", "aqui", "hoje aqui", "amanhã", "amanha",
        "depois de amanhã", "depois de amanha",
    }:
        local = ""
    dia_offset = 0
    if re.search(r"\bdepois\s+de\s+amanh[ãa]\b", t):
        dia_offset = 2
    elif re.search(r"\bamanh[ãa]\b", t):
        dia_offset = 1
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    dados: Dict[str, Any] = {}
    if local:
        dados["local"] = local
    if dia_offset:
        dados["day_offset"] = dia_offset
    return {"intent": "WEATHER", "params": params(**dados)}


def detectar_url_visual(
    texto_normalizado: str,
    texto_bruto: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece URLs diretas e pedidos de visão/captura."""
    t = str(texto_normalizado or "").strip()
    bruto = str(texto_bruto or "")
    if not t:
        return None
    if analisar_protecao_operacional(t).get("bloqueia_execucao"):
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if any(x in t for x in ["instagram.com/direct", "instagram.com", "www.instagram.com", "instagram direct", "direct/t/"]):
        return {"intent": "OPEN_URL", "params": params(alvo="instagram")}
    if re.search(r"https?://\S+", bruto) and "instagram" in t:
        return {"intent": "OPEN_URL", "params": params(alvo="instagram")}

    if any(p in t for p in [
        "o que voce ve na tela", "o que você vê na tela", "o que ta na tela", "o que tá na tela",
        "o que tem na minha tela", "o que ha na minha tela", "o que há na minha tela",
        "olha minha tela", "olha a tela", "ver minha tela", "captura a tela", "tira print",
        "screenshot", "print da tela",
        "guarda esse momento", "salva esse momento", "memoriza isso", "lembra dessa tela",
        "guarda essa tela", "salva essa tela", "faz memoria disso", "faz memória disso",
    ]):
        return {"intent": "SCREEN_CAPTURE", "params": params()}

    consulta_visual = t.strip(" .,!?:;")
    if re.fullmatch(
        r"(?:o\s+que\s+(?:voce|você)\s+consegue\s+identificar(?:\s+nela)?|"
        r"resume\s+(?:o\s+que\s+(?:voce|você)\s+(?:esta|está|ta|tá)\s+vendo|"
        r"o\s+que\s+(?:esta|está|ta|tá)\s+aparecendo\s+agora))",
        consulta_visual,
    ):
        modo = "resumir" if t.startswith("resume") else "identificar"
        return {
            "intent": "VISION_QUERY",
            "params": params(acao="consultar_contexto_visual", modo=modo),
        }

    return None


def detectar_organizacao_desktop(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece pedidos naturais e espaciais de organizacao de janelas.

    O detector devolve apenas os lados realmente pedidos. Isso evita abrir ou
    mover uma segunda janela por conta propria quando a pessoa diz somente
    ``coloca a Steam na esquerda``.
    """
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    t = re.sub(r"^(?:agora|entao|então)\s+", "", t).strip()
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if re.match(r"^(?:nao|não|nem)\b", t) or re.search(
        r"\b(?:talvez|seria legal|estou pensando|to pensando|como eu faria|como faz|"
        r"voc[eê] consegue|voc[eê] sabe)\b",
        t,
    ):
        return None

    def limpar_app(valor: str) -> str:
        nome = re.sub(r"\s+", " ", str(valor or "")).strip(" ,.;:!?")
        nome = re.sub(
            r"^(?:e\s+)?(?:coloca|coloque|bota|ponha|põe|poe|move|mova|"
            r"posiciona|posicione|deixa|deixe|joga)\s+",
            "",
            nome,
        ).strip()
        nome = re.sub(r"^(?:o|a|os|as|um|uma)\s+", "", nome).strip()
        return re.sub(r"\s+(?:por favor|pfv|agora)$", "", nome).strip()

    padrao_lado = re.compile(
        r"^(?P<app>.+?)\s+(?:(?:na|a|à|para a)\s+"
        r"(?P<lado>esquerda|direita)|(?:no|pro|para o|do)\s+lado\s+"
        r"(?P<lado_genero>esquerdo|direito))"
        r"(?:\s+(?:da|do)\s+(?:tela|desktop|monitor))?$"
    )
    lados: Dict[str, str] = {}
    # A conjuncao separa os dois alvos sem quebrar nomes compostos de apps.
    for trecho in re.split(r"\s+(?:e|,)\s+", t):
        trecho_limpo = re.sub(
            r"^(?:coloca|coloque|bota|ponha|põe|poe|move|mova|posiciona|"
            r"posicione|deixa|deixe|joga)\s+",
            "",
            trecho.strip(),
        )
        encontrado = padrao_lado.match(trecho_limpo)
        if not encontrado:
            continue
        app = limpar_app(encontrado.group("app"))
        lado = encontrado.group("lado") or encontrado.group("lado_genero")
        if app and app not in {"janela", "janelas", "programa", "app", "aplicativo"}:
            lados["left" if lado in {"esquerda", "esquerdo"} else "right"] = app

    if lados:
        return {
            "intent": "ORGANIZAR_DESKTOP",
            "params": params(**lados, modo="posicionar"),
        }

    if any(v in t for v in ["organiza", "organizar", "arruma", "arrumar"]) and any(
        alvo in t for alvo in ["area de trabalho", "área de trabalho", "desktop", "tela", "janelas", "janela"]
    ):
        return {"intent": "ORGANIZAR_DESKTOP", "params": params(modo="automatico")}

    return None


def detectar_janela_contextual(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    estado_mental: Dict[str, Any] | None = None,
    texto_depende_de_contexto: Callable[[str], bool] | None = None,
) -> Dict[str, Any] | None:
    """Resolve comandos de janela que dependem do ultimo app citado."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    depende_contexto = texto_depende_de_contexto if callable(texto_depende_de_contexto) else (lambda valor: False)

    referencia_janela_contextual = (
        bool(depende_contexto(t))
        or any(v in t for v in ["ele", "ela", "isso"])
    )
    if not referencia_janela_contextual:
        return None
    if not any(v in t for v in ["foco", "na frente", "pra frente", "para frente", "tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return None

    estado = dict(estado_mental or {})
    ultima_intencao_ctx = str(estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or "").strip().upper()
    ultimo_app = str(estado.get("ultimo_app_janela") or "").strip()
    if not ultimo_app and ultima_intencao_ctx in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        params_brutos = estado.get("ultima_acao_params")
        ultimos_params = params_brutos if isinstance(params_brutos, dict) else {}
        ultimo_app = str(
            ultimos_params.get("nome_app")
            or ultimos_params.get("app")
            or estado.get("ultimo_alvo")
            or ""
        ).strip()

    if not ultimo_app:
        return None
    if any(v in t for v in ["tela cheia", "fullscreen", "maximiza", "maximizar"]):
        return {"intent": "MAXIMIZE_WINDOW", "params": params(nome_app=ultimo_app)}
    return {"intent": "APP_OPEN", "params": params(nome_app=ultimo_app, modo="focus")}


def detectar_janela_explicita(
    texto_normalizado: str,
    texto_sem_destino: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece foco/maximizacao quando o app aparece explicitamente na frase."""
    t = str(texto_normalizado or "").strip()
    base = str(texto_sem_destino or t).strip()
    if not t or not base:
        return None
    if re.fullmatch(
        r"(?:abre|abra|abrir|mostra|mostre)\s+(?:o\s+)?primeiro\s+resultado"
        r"[ .,!?:;]*",
        base,
        flags=re.IGNORECASE,
    ):
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    m_max_posposto = re.search(
        r"\b(?:coloca|coloque|bota|deixa|poe|põe)\s+(?:o|a|os|as)?\s*(?P<app>.+?)\s+(?:em|no|na)\s+(?P<modo>tela cheia|fullscreen|full screen|foco|primeiro plano)$",
        base,
        flags=re.IGNORECASE,
    )
    if m_max_posposto:
        app = str(m_max_posposto.group("app") or "").strip()
        modo_txt = str(m_max_posposto.group("modo") or "").strip().lower()
        app = app.replace("pra frente", "").replace("para frente", "").strip()
        if app:
            if modo_txt in {"tela cheia", "fullscreen", "full screen"}:
                return {"intent": "MAXIMIZE_WINDOW", "params": params(nome_app=app)}
            return {"intent": "APP_OPEN", "params": params(nome_app=app, modo="focus")}

    m_max = re.search(r"\b(maximiza|maximize|maximizar|tela cheia|fullscreen|coloca em foco|bota em foco|deixa em foco|traz)\s+(?:o|a)?\s*(.+)$", base)
    if m_max:
        app = re.sub(r"^(o|a|os|as|um|uma)\s+", "", (m_max.group(2) or "").strip())
        app = app.replace("em foco", "").replace("pra frente", "").replace("para frente", "").strip()
        if app:
            verbo_modo = str(m_max.group(1) or "").casefold()
            if verbo_modo.startswith("maximiz") or any(
                p in t for p in ["tela cheia", "fullscreen"]
            ):
                return {"intent": "MAXIMIZE_WINDOW", "params": params(nome_app=app)}
            return {"intent": "APP_OPEN", "params": params(nome_app=app, modo="focus")}

    return None


def detectar_abrir_app_ou_site(
    texto_bruto: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    extrair_intencao_abrir_app: Callable[[str], Dict[str, Any] | None],
) -> Dict[str, Any] | None:
    """Adapta a extracao existente de abrir app/site para o roteador modular."""
    bruto = str(texto_bruto or "").strip()
    if not bruto:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    extrair = extrair_intencao_abrir_app if callable(extrair_intencao_abrir_app) else (lambda valor: None)

    intent_abrir = extrair(bruto)
    if not intent_abrir:
        return None
    if intent_abrir.get("intent") == "OPEN_URL":
        return {"intent": "OPEN_URL", "params": params(**intent_abrir.get("params", {}))}

    nome_app = str(intent_abrir.get("params", {}).get("nome_app") or "").strip()
    if nome_app:
        return {"intent": "APP_OPEN", "params": params(nome_app=nome_app)}

    return None


def detectar_fechar_alvo(
    texto_sem_destino: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
    sites_diretos: Any,
    apps_map: Any,
) -> Dict[str, Any] | None:
    """Reconhece pedidos de fechar aba, site, janela, programa ou app."""
    base = str(texto_sem_destino or "").strip()
    if not base:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    sites = sites_diretos if sites_diretos is not None else set()
    apps = apps_map if apps_map is not None else {}

    if re.fullmatch(
        r"(?:fecha|fechar|encerra|encerrar|limpa|limpar)\s+"
        r"(?:(?:as|essas)\s+)?abas\s+"
        r"(?:paradas|inativas|ociosas|sem\s+uso)[.!?]*",
        base,
        flags=re.IGNORECASE,
    ):
        return {"intent": "CLOSE_IDLE_TABS", "params": params()}

    # Artigos longos vêm primeiro e a fronteira impede ``a`` de consumir o
    # começo de ``as``. Antes, "fecha as abas" produzia o alvo ``s abas``.
    m_close = re.search(
        r"\b(fecha|fechar|mata|derruba|encerra|encerrar)\s+"
        r"(?:(?:essas|esses|essa|esse|estas|estes|esta|este|uma|um|as|os|a|o)\b\s*)?"
        r"(.+)$",
        base,
        flags=re.IGNORECASE,
    )
    if not m_close:
        return None

    alvo_bruto = str(m_close.group(2) or "").strip()
    alvo_tipado_app = bool(re.match(
        r"^(?:janela|programa|app|aplicativo)\b",
        alvo_bruto,
        flags=re.IGNORECASE,
    ))
    alvo = re.sub(
        r"^(aba|site|janela|programa|app|aplicativo)\s+(do|da|de)?\s*",
        "",
        alvo_bruto,
    ).strip()
    # ``chamado`` qualifica o nome; nunca faz parte dele. Sem esta limpeza,
    # "fecha um programa chamado X" procurava literalmente por "chamado X".
    alvo = re.sub(
        r"^(?:chamado|chamada|com\s+nome|de\s+nome)\s+",
        "",
        alvo,
        flags=re.IGNORECASE,
    ).strip()
    alvo = re.sub(r"^(?:uma|um|as|os|a|o)\s+", "", alvo).strip()
    if re.fullmatch(
        r"(?:(?:programa|app|aplicativo|janela)\s+)?"
        r"(?:que\s+(?:voce\s+)?(?:acabou\s+de\s+)?abrir|"
        r"(?:ultimo|ultima)\s+(?:programa|app|aplicativo|janela))",
        alvo,
    ):
        # É uma referência, não o nome literal de um executável. O resolvedor
        # contextual conhece a última janela e deve decidir o alvo.
        return None
    if not alvo or alvo in {"aba", "essa aba", "site", "janela"}:
        return {"intent": "CLOSE_TAB", "params": params()}

    alvo_norm = alvo.lower()
    if not alvo_tipado_app and (
        "aba" in base
        or "site" in base
        or alvo_norm in sites
        or alvo_norm in {
            "youtube", "netflix", "google", "spotify", "whatsapp", "chatgpt",
        }
    ):
        return {"intent": "CLOSE_TAB", "params": params(alvo=alvo)}

    for app in sorted(apps.keys(), key=len, reverse=True):
        if alvo_norm == app or app in alvo_norm:
            dados_mapeados: Dict[str, Any] = {"nome_app": app}
            if alvo_tipado_app:
                dados_mapeados["alvo_tipado"] = "app"
            return {"intent": "CLOSE_APP", "params": params(**dados_mapeados)}

    dados_app: Dict[str, Any] = {"nome_app": alvo}
    if alvo_tipado_app:
        # O executor usa esta evidência lexical para não reinterpretar um
        # programa inexistente como aba do navegador nem declarar falso êxito.
        dados_app["alvo_tipado"] = "app"
    return {"intent": "CLOSE_APP", "params": params(**dados_app)}


def detectar_web_e_youtube(
    texto_normalizado: str,
    texto_sem_destino: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
    sites_diretos: Any,
) -> Dict[str, Any] | None:
    """Reconhece pesquisa web, abertura de site e comandos diretos de YouTube."""
    t = str(texto_normalizado or "").strip()
    base = str(texto_sem_destino or t).strip()
    if not t or not base:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    sites = sites_diretos if sites_diretos is not None else set()

    # É uma continuação da busca canônica, não um endereço. O orquestrador a
    # resolve antes deste detector quando existe SEARCH confirmado; sem essa
    # evidência a frase deve pedir contexto, nunca abrir uma busca literal.
    if re.fullmatch(
        r"(?:abre|abra|abrir|mostra|mostre)\s+(?:o\s+)?primeiro\s+resultado"
        r"[ .,!?:;]*",
        base,
        flags=re.IGNORECASE,
    ):
        return None

    m_google = re.search(
        r"\b(pesquisa|pesquisar|busca|buscar|procura|procurar)\s+"
        r"(?:no google\s+)?(?:(?:sobre|por)\s+)?(.+)$",
        base,
    )
    if m_google and "youtube" not in t:
        query = (m_google.group(2) or "").strip(" .,!?:;")
        if query:
            return {"intent": "SEARCH", "params": params(query=query, engine="google")}

    m_site = re.search(r"\b(entra|entrar|abre|abra|abrir|vai)\s+(?:no|na|em|para|pra)?\s*(?:site\s+)?(.+)$", base)
    if m_site:
        alvo = re.sub(r"^(o|a|os|as|um|uma)\s+", "", (m_site.group(2) or "").strip()).strip()
        alvo_norm = alvo.lower()
        if alvo_norm in sites or "." in alvo_norm or alvo_norm.startswith(("http://", "https://")):
            return {"intent": "OPEN_URL", "params": params(alvo=alvo)}

    if "youtube" in t:
        m_yt = re.search(r"(?:procura|pesquisa|busca|buscar|coloca|toca|toque)\s+(.*?)\s+(?:no|na)\s+youtube", t)
        if m_yt and m_yt.group(1).strip():
            return {"intent": "MUSIC_SEARCH", "params": params(query=m_yt.group(1).strip())}
        if any(p in t for p in ["abre", "abrir", "entra", "entrar"]):
            return {"intent": "OPEN_URL", "params": params(alvo="youtube")}

    return None


def detectar_consulta_abas(
    texto: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece somente consultas explícitas sobre abas observáveis.

    A listagem não é uma pesquisa aberta nem uma pergunta para a LLM: ela
    depende da percepção atual da extensão. Manter um intent próprio impede
    que títulos e URLs sejam inventados quando o navegador não responder.
    """
    base = str(texto or "").strip().casefold().rstrip(" .,!?:;")
    if not base:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    if re.fullmatch(
        r"(?:quais|que|quantas)\s+abas\s+(?:estao|estão|tao|tão)\s+abertas|"
        r"(?:quais|que)\s+sao\s+as\s+abas\s+abertas|"
        r"(?:lista|liste|listar|mostra|mostre|mostrar)\s+(?:as\s+)?abas\s+abertas",
        base,
    ):
        return {"intent": "LIST_TABS", "params": params()}
    return None


def detectar_continuacao_resultado_web(
    texto: str,
    estado_mental: Dict[str, Any] | None,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Resolve ``abre o primeiro resultado`` só após uma busca confirmada."""
    base = str(texto or "").strip().casefold().rstrip(" .,!?:;")
    if not re.fullmatch(
        r"(?:abre|abra|abrir|mostra|mostre)\s+(?:o\s+)?primeiro\s+resultado",
        base,
    ):
        return None
    estado = estado_mental if isinstance(estado_mental, dict) else {}
    intent_anterior = str(
        estado.get("ultima_acao_intent") or estado.get("ultima_intencao") or ""
    ).strip().upper()
    status = str(estado.get("ultima_acao_status") or "").strip().casefold()
    confirmado = estado.get("ultima_acao_confirmada")
    params_anteriores = (
        dict(estado.get("ultima_acao_params") or {})
        if isinstance(estado.get("ultima_acao_params"), dict)
        else {}
    )
    consulta = str(
        params_anteriores.get("query")
        or estado.get("ultima_acao_alvo")
        or estado.get("ultimo_alvo")
        or ""
    ).strip()
    if (
        intent_anterior != "SEARCH"
        or confirmado is not True
        or status not in {"busca_aberta", "pesquisa_aberta", "resultados_observados"}
        or not consulta
    ):
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    return {
        "intent": "SEARCH",
        "params": params(
            query=consulta,
            abrir_resultado=1,
            origem="continuacao_resultado_web",
        ),
    }


def detectar_musica_ou_playlist_direta(
    texto_normalizado: str,
    texto_sem_destino: str = "",
    texto_bruto: str = "",
    *,
    params_cb: Callable[..., Dict[str, Any]],
    detectar_playlist_nome_direto: Callable[[str], str],
    normalizar_query_musical: Callable[[str], str],
) -> Dict[str, Any] | None:
    """Resolve comandos diretos de tocar música ou playlist pelo nome."""
    t = str(texto_normalizado or "").strip()
    base = str(texto_sem_destino or t).strip()
    bruto = str(texto_bruto or "").strip()
    if not t:
        return None
    # "Abre o primeiro resultado" e uma continuacao web, nunca o titulo de
    # uma musica. Sem SEARCH confirmado, deixamos a conversa pedir contexto em
    # vez de mandar "primeiro resultado" ao YouTube.
    if re.fullmatch(
        r"(?:abre|abra|abrir|mostra|mostre)\s+(?:o\s+)?primeiro\s+resultado"
        r"[ .,!?:;]*",
        t,
        flags=re.IGNORECASE,
    ):
        return None
    # Nomes de gêneros também podem ser nomes de playlists. A pergunta
    # ``o que você acha de rock?`` deve chegar à conversa, não tocar nem listar
    # a playlist homônima.
    if texto_pede_opiniao(bruto or t):
        return None
    if re.search(r"\b(?:volume|som)\b", t) and re.search(
        r"\b(?:maximo|máximo|minimo|mínimo|mudo|mute|aumenta|aumentar|abaixa|baixar|diminui|diminuir)\b",
        t,
    ):
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)
    detectar_playlist = detectar_playlist_nome_direto if callable(detectar_playlist_nome_direto) else (lambda valor: "")
    normalizar_musica = normalizar_query_musical if callable(normalizar_query_musical) else (lambda valor: str(valor or "").strip())

    convite_musical = re.match(
        r"^\s*(?:vamos\s+)?(?:ouvir|escutar)\s+(?:uma|um|algo)?\s*(.+)$",
        t,
    )
    if convite_musical and "playlist" not in t:
        q = str(convite_musical.group(1) or "").strip()
        q = re.sub(r"^(?:musica|música|som|faixa)\s+", "", q).strip()
        q = normalizar_musica(q)
        if q:
            return {"intent": "MUSIC_SEARCH", "params": params(query=q)}

    if re.match(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b", t):
        # Nomes já salvos vencem a interpretação genérica da palavra
        # "música": "coloca música brasileira" pode ser uma playlist.
        pl_direta = detectar_playlist(bruto)
        if pl_direta:
            if any(x in t for x in ["lista", "listar", "quais", "mostra", "o que tem", "oque tem"]):
                return {"intent": "PLAYLIST_LIST", "params": params(nome_playlist=pl_direta)}
            return {"intent": "PLAYLIST_PLAY", "params": params(nome_playlist=pl_direta)}

        if any(x in t for x in ["música", "musica", "youtube", "no youtube", "no yt", "no you tube"]):
            q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b\s*", "", t).strip()
            q = re.sub(r"^(a|o|as|os|uma|um|essa|esse|essa música|essa musica|essa canção|essa cancao)\s+", "", q).strip()
            if q:
                return {"intent": "MUSIC_SEARCH", "params": params(query=q)}

        if not any(x in t for x in ["playlist", "música", "musica", "youtube", "yt"]):
            q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute|abre|abra)\b\s*", "", t).strip()
            q = re.sub(r"^(a|o|as|os|uma|um|essa|esse)\s+", "", q).strip()
            if q:
                return {"intent": "MUSIC_SEARCH", "params": params(query=q)}

    pl_direta = detectar_playlist(bruto)
    if pl_direta and not any(x in t for x in ["música", "musica", "youtube", "yt"]):
        if any(x in t for x in ["playlist", "lista", "listar", "quais", "mostra", "o que tem", "oque tem"]):
            return {"intent": "PLAYLIST_LIST", "params": params(nome_playlist=pl_direta)}
        return {"intent": "PLAYLIST_PLAY", "params": params(nome_playlist=pl_direta)}

    if re.match(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute)\b", t) and "playlist" not in t:
        q = re.sub(r"^\s*(coloque|coloca|toca|toque|ouvir|escuta|escute)\b", " ", base).strip()
        q = re.sub(r"^(a|o|uma|um)\s+", "", q).strip()
        q = q.replace("música", " ").replace("musica", " ").replace("no youtube", " ").replace("na youtube", " ")
        q = re.sub(r"\s+", " ", q).strip()
        q = normalizar_musica(q)
        if q and q not in {"playlist"}:
            return {"intent": "MUSIC_SEARCH", "params": params(query=q)}

    return None


def detectar_trava_pc(
    texto_normalizado: str,
    *,
    params_cb: Callable[..., Dict[str, Any]],
) -> Dict[str, Any] | None:
    """Reconhece pedidos explicitos para bloquear/travar o computador."""
    t = str(texto_normalizado or "").strip()
    if not t:
        return None
    params = params_cb if callable(params_cb) else (lambda **kwargs: kwargs)

    if any(p in t for p in ["trava o pc", "travar o pc", "bloqueia o pc", "lock pc", "bloquear computador"]):
        return {"intent": "LOCK_PC", "params": params()}

    return None
