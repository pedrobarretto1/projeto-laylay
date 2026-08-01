"""Classificação única da natureza de cada turno da Laylay."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict


def analisar_protecao_operacional(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
) -> Dict[str, Any]:
    """Lê negação, hipótese e pergunta antes de qualquer intenção prática."""
    normalizar = normalizar_texto if callable(normalizar_texto) else (
        lambda valor: str(valor or "").casefold().strip()
    )
    t = re.sub(r"\s+", " ", str(normalizar(texto) or "")).strip()
    neutra = {
        "bloqueia_execucao": False,
        "modalidade": "",
        "natureza_acao": "nenhuma",
        "motivo": "",
    }
    if not t:
        return neutra
    if re.search(r"^(?:nao|não)\s+\w+.*\b(?:qu[eê]|qual|porque|por que)\b", t):
        return {
            "bloqueia_execucao": True,
            "modalidade": "pergunta",
            "natureza_acao": "instrucao_ou_explicacao",
            "motivo": "pergunta negativa sobre ação",
        }
    if re.search(
        r"\b(?:acho que (?:eu )?vou|talvez|estou pensando em|to pensando em|"
        r"seria bom|seria legal|quem sabe|tenho vontade de|estou com vontade de|"
        r"to com vontade de|queria saber|se eu (?:pedir|quiser|mandar)|"
        r"quando (?:voce|você|eu|a gente)|caso (?:eu|voce|você|a gente))\b",
        t,
    ):
        return {
            "bloqueia_execucao": True,
            "modalidade": "deliberacao",
            "natureza_acao": "hipotetica",
            "motivo": "intenção hipotética ou reflexão",
        }
    if re.search(
        r"^(?:nao|não|nunca|jamais)\s+(?:(?:pode|deve|vai)\s+)?"
        r"(?:abre|abra|fecha|feche|liga|ligue|acende|desliga|desligue|toca|"
        r"toque|coloca|apaga|remove|muda|ajusta|deixa)\b",
        t,
    ):
        return {
            "bloqueia_execucao": True,
            "modalidade": "recusa",
            "natureza_acao": "cancelamento",
            "motivo": "negação operacional",
        }
    if re.search(
        r"^(?:como(?:\s+(?:eu\s+)?)?(?:faria|fa[cç]o|posso|poderia)?|"
        r"onde|quando|por\s+que|porque|qual\s+(?:a\s+)?forma\s+de|"
        r"o\s+que\s+(?:eu\s+)?(?:faria|fa[cç]o)|o\s+que\s+acontece\s+se)\b"
        r".*\b(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|"
        r"remover|usar|fazer)\b",
        t,
    ) or re.search(r"\b(?:queria|gostaria)\s+de\s+saber\s+como\b", t):
        return {
            "bloqueia_execucao": True,
            "modalidade": "pergunta",
            "natureza_acao": "instrucao_ou_explicacao",
            "motivo": "pergunta informativa sobre uma ação",
        }
    return neutra


def _classificar_modalidade_base(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> Dict[str, Any]:
    bruto = str(texto or "").strip()
    normalizar = normalizar_texto if callable(normalizar_texto) else (lambda valor: str(valor or "").casefold().strip())
    t = re.sub(r"\s+", " ", str(normalizar(bruto) or "")).strip()
    resultado = {
        "id": time.time_ns(), "texto": bruto[:500], "normalizado": t[:500],
        "modalidade": "conversa", "confianca": 0.60,
        "motivo": "fala sem marcador operacional dominante", "ts": time.time(),
        "acao_explicita": False,
        "autoriza_execucao": False,
        "requer_esclarecimento": False,
        "depende_contexto": False,
        "natureza_acao": "nenhuma",
        "confirmacao_contextual_valida": bool(confirmacao_contextual_valida),
    }
    if not t:
        resultado.update(modalidade="vazio", confianca=1.0, motivo="entrada vazia")
        return resultado
    protecao = analisar_protecao_operacional(
        t,
        normalizar_texto=lambda valor: str(valor or "").strip(),
    )
    if protecao["bloqueia_execucao"] and protecao["motivo"] == "pergunta negativa sobre ação":
        resultado.update(
            modalidade=protecao["modalidade"], confianca=0.99,
            motivo=protecao["motivo"], natureza_acao=protecao["natureza_acao"],
        )
        return resultado
    if re.search(
        r"^(?:na verdade|eu quis dizer|quis dizer|nao lay|não lay|to falando de|estou falando de|"
        r"eu (?:nao|não) pedi|(?:nao|não) te pedi|eu te perguntei|eu perguntei|como assim.+eu .*perguntei)\b",
        t,
    ):
        resultado.update(modalidade="correcao", confianca=0.99, motivo="reparação explícita", natureza_acao="correcao")
        return resultado
    if protecao["bloqueia_execucao"]:
        resultado.update(
            modalidade=protecao["modalidade"],
            confianca=0.98 if protecao["modalidade"] != "deliberacao" else 0.97,
            motivo=protecao["motivo"],
            natureza_acao=protecao["natureza_acao"],
            depende_contexto=protecao["modalidade"] == "recusa",
        )
        return resultado

    if re.match(
        r"^(?:eu\s+)?(?:achei|pensei|entendi)\s+que\s+(?:voc[eê]|tu)\s+ia\s+"
        r"(?:colocar|tocar|abrir|fechar|ligar|desligar|fazer|executar)\b",
        t,
    ):
        resultado.update(
            modalidade="reacao", confianca=0.99,
            motivo="expectativa sobre ação passada; não autoriza execução",
            natureza_acao="decepcao",
        )
        return resultado

    confirmacoes = {"sim", "sim pode", "pode", "pode sim", "quero", "quero sim", "eu quero", "claro", "aham", "uhum", "isso", "isso mesmo", "bora", "vai", "manda", "pode ser", "fechado", "beleza", "ok"}
    recusas = {
        "nao", "não", "agora nao", "agora não", "nao precisa", "não precisa",
        "deixa", "deixa quieto", "deixa pra la", "deixa pra lá",
        "deixa para la", "deixa para lá", "esquece", "melhor nao",
        "melhor não", "pode nao", "pode não",
    }
    if t in confirmacoes:
        resultado.update(
            modalidade="confirmacao", confianca=0.98,
            motivo=("confirmação ligada a pendência ativa" if confirmacao_contextual_valida else "confirmação social sem pendência acionável"),
            natureza_acao="confirmacao_contextual",
            depende_contexto=True,
            autoriza_execucao=bool(confirmacao_contextual_valida),
        )
        return resultado
    if t in recusas:
        resultado.update(modalidade="recusa", confianca=0.98, motivo="recusa curta explícita")
        return resultado
    if re.fullmatch(
        r"(?:h+m+|hum+|entendi|tendi|ta bom|tá bom|ah ta|ah tá|ata|nossa|"
        r"caramba|pois e|pois é|e ne|e né|ne|né)(?: entao| então)?",
        t,
    ):
        resultado.update(modalidade="reacao", confianca=0.92, motivo="reação curta à fala anterior")
        return resultado
    # O usuário pode mencionar o nome da playlist sem repetir a palavra
    # "playlist": "quais músicas eu tenho em Kamaitachi" ainda é uma
    # consulta ao catálogo local, não uma pergunta factual para a conversa.
    if re.search(r"\b(?:quais|quantas|lista|listar|liste|mostra|mostrar|mostre)\b", t) and re.search(
        r"\b(?:musicas|músicas|faixas)\b", t
    ) and re.search(
        r"\b(?:eu\s+tenho|tenho|tem|salvas?|guardadas?|em|na|no|da|do)\b", t
    ):
        resultado.update(
            modalidade="comando", confianca=0.98,
            motivo="consulta explícita às faixas de uma playlist local",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado

    # Inventários locais são consultas operacionais, mesmo quando formulados
    # como pergunta. Sem esta distinção, "quais minhas playlists" cai na
    # conversa generativa e a LLM pode inventar nomes em vez de ler o arquivo.
    if re.search(r"\bplaylists?\b", t) and re.search(
        r"\b(?:que|quais|quantas|lista|listar|liste|mostra|mostrar|mostre|"
        r"fale|fala|diga|diz)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta explícita ao inventário local de playlists",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if re.search(r"\b(?:e-?mail|emails?)\b", t) and re.search(
        r"\b(?:que|quais|quantos|lista|listar|mostra|mostrar|mostre|fale|fala|"
        r"diga|diz|leia|ler|resuma|resumo)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta explícita à caixa de e-mail",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    # Consultas a estado local são operações de leitura. Elas precisam chegar
    # ao especialista determinístico em vez de cair na conversa generativa.
    if (
        re.search(
            r"\b(?:como\s+(?:esta|está|ta|tá|ficou|se\s+encontra)|"
            r"qual\s+(?:e|é)\s+(?:o\s+)?(?:status|estado)|"
            r"mostra|mostrar|consulta|consultar|status|estado)\b",
            t,
        )
        and re.search(r"\b(?:lampada|lâmpada|luz|tomada|ventilador|dispositivo|aparelho|iot)\b", t)
    ) or re.search(
        r"\b(?:quais|que|lista|listar|mostra|mostrar)\b.*\b(?:programas|aplicativos|apps|janelas)\b.*\b(?:abert[oa]s?|rodando|execucao|execução)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="consulta explícita a estado local",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if re.fullmatch(
        r"(?:para|pare|pausa|pause)\s+(?:a\s+)?m[uú]sica|"
        r"(?:volta|retoma|continua)\s+(?:a\s+)?(?:tocar|m[uú]sica)",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.99,
            motivo="controle explícito da mídia atual",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="pedido_direto",
        )
        return resultado
    if re.search(r"\b(?:me\s+lembra|lembra\s+(?:de|pra)|me\s+avisa|cria\s+(?:um\s+)?lembrete|agende|agendar)\b", t):
        resultado.update(
            modalidade="comando", confianca=0.99, motivo="pedido explícito de agendamento",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="pedido_direto",
        )
        return resultado
    if re.search(
        r"^(?:o\s+que\s+(?:essa|esta)\s+(?:pagina|página|site|video|vídeo)\b|"
        r"(?:resume|resuma|resumir|leia|ler|verifique)\b.*\b(?:pagina|página|site|video|vídeo))",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.97,
            motivo="consulta explícita de conteúdo atual",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="consulta",
        )
        return resultado
    if re.search(
        r"^(?:pesquisa|pesquisar|busca|buscar|procura|procurar)\b\s+.+|"
        r"^(?:pula|pule|passa|tira|remove)\b.*\b(?:anuncio|anúncio|propaganda)\b|"
        r"^(?:proxima|próxima)\s+(?:musica|música|faixa)|^(?:musica|música)\s+anterior|"
        r"^(?:olha|veja|ver|captura|capture)\b.*\b(?:minha\s+)?tela\b|^tira\s+(?:um\s+)?print\b|"
        r"^(?:trava|bloqueia)\b.*\b(?:pc|computador|tela)\b|"
        r"^(?:volume\s+(?:maximo|máximo|minimo|mínimo|mudo|\d{1,3})|mute|mudo|desmuta)\b",
        t,
    ):
        resultado.update(
            modalidade="comando", confianca=0.98,
            motivo="comando determinístico explícito",
            acao_explicita=True, autoriza_execucao=True, natureza_acao="pedido_direto",
        )
        return resultado

    # Perguntas de conhecimento ou capacidade são respondidas; não executadas.
    if re.search(
        r"\b(?:voce|você)\s+(?:viu|conhece|soube|sabe\s+(?:o\s+que|quem|como)|"
        r"tem\s+capacidade|e\s+capaz|é\s+capaz)|\b(?:ja|já)\s+ouviu\s+falar\b",
        t,
    ):
        resultado.update(modalidade="pergunta", confianca=0.98, motivo="pergunta sobre conhecimento ou capacidade", natureza_acao="capacidade")
        return resultado
    pedido_polido = bool(re.search(
        r"^(?:por favor\s+)?(?:pode|poderia|consegue|conseguiria)\s+"
        r"(?:abrir|abre|fechar|fecha|ligar|liga|desligar|desliga|tocar|toca|colocar|"
        r"coloca|criar|apagar|ler|leia|verificar|verifique|resumir|resuma|resume)\b",
        t,
    ))
    pedido_para_mim = bool(re.search(
        r"^(?:voce|você)\s+(?:pode|poderia|consegue|conseguiria)\s+.*\b(?:pra|para)\s+mim\b",
        t,
    ))
    imperativo_direto = bool(re.search(
        r"^(?:por favor\s+)?(?:abre|abra|fecha|feche|liga|ligue|desliga|desligue|"
        r"toca|toque|coloca|coloque|deixa|deixe|bota|põe|poe|cria|crie|apaga|remove|deleta|"
        r"maximiza|organiza|pausa|retoma|aumenta|abaixa|diminui|resume|resuma|"
        r"leia|verifique)\b",
        t,
    ))
    comando_detectado = False
    if callable(texto_tem_comando_explicito):
        try:
            comando_detectado = bool(texto_tem_comando_explicito(t))
        except Exception:
            comando_detectado = False
    capacidade_ambigua = bool(re.search(
        r"^(?:voce|você)\s+(?:pode|poderia|consegue|conseguiria)\s+"
        r"(?:abrir|fechar|ligar|desligar|tocar|colocar|criar|apagar|ler|verificar|resumir)\b",
        t,
    )) and not pedido_para_mim
    if capacidade_ambigua:
        resultado.update(
            modalidade="pergunta", confianca=0.88,
            motivo="pedido de capacidade ambíguo; execução não presumida",
            natureza_acao="capacidade", requer_esclarecimento=True,
        )
        return resultado
    if imperativo_direto or pedido_polido or pedido_para_mim or comando_detectado:
        palavras = t.split()
        alvo_pronominal = bool(re.search(r"\b(?:ele|ela|isso|essa|esse|aquela|aquele)\b", t))
        alvo_ausente = len(palavras) <= 1
        resultado.update(
            modalidade="comando",
            confianca=0.98 if (imperativo_direto or pedido_para_mim) and not alvo_ausente else 0.82,
            motivo="pedido prático explícito" if not alvo_ausente else "verbo operacional sem alvo",
            acao_explicita=True,
            autoriza_execucao=not alvo_ausente,
            requer_esclarecimento=alvo_ausente,
            depende_contexto=alvo_pronominal or alvo_ausente,
            natureza_acao="pedido_direto",
        )
        return resultado

    # "Você consegue abrir X?" sem "para mim" é ambíguo: pode ser teste de
    # capacidade. A Laylay responde ou esclarece, mas não age por suposição.
    interrogativos = r"(?:como|qual|quais|quem|quando|onde|porque|por que|o que|que tal|vamos fazer o que)"
    if "?" in bruto or re.search(rf"^(?:e\s+|mas\s+|entao\s+)?{interrogativos}\b", t):
        resultado.update(modalidade="pergunta", confianca=0.94, motivo="pergunta nova")
        return resultado
    if re.search(r"\b(?:obrigado|obrigada|valeu|gostei|adorei|odeio|nao gosto|não gosto)\b", t):
        resultado.update(modalidade="reacao", confianca=0.88, motivo="reação ou preferência")
    return resultado


_VERBOS_COMANDO = re.compile(
    r"\b(?:abre|abrir|abra|fecha|fechar|feche|liga|ligar|ligue|desliga|desligar|"
    r"desligue|toca|tocar|toque|coloca|colocar|coloque|deixa|deixar|deixe|bota|põe|poe|cria|criar|"
    r"crie|apaga|apagar|remove|remover|deleta|deletar|maximiza|maximizar|pausa|"
    r"pausar|retoma|aumenta|abaixa|diminui|organiza|agende|agendar|me lembra|me avisa|"
    r"leia|ler|lê|le|pesquisa|pesquisar|busca|buscar|procura|procurar|"
    r"encontra|encontre|achar|acha|ache|localiza|localize|pula|pule|"
    r"captura|capture|trava|bloqueia)\b",
    re.IGNORECASE,
)


_PERGUNTA_RECIPROCA_FINAL = re.compile(
    r"(?:[,;]\s*|\s+)"
    r"(?P<sufixo>(?:(?:mas\s+)?e\s+)?(?:"
    r"(?:o|a)\s+(?:seu|sua|teu|tua)|"
    r"(?:voc[eê]|tu)|"
    r"(?:do|da)\s+(?:seu|teu)\s+lado|"
    r"por\s+a[ií]|"
    r"como\s+(?:foi|est[aá]|t[aá])\s+(?:(?:o|a)\s+)?(?:seu|sua|teu|tua)"
    r"))\?\s*$",
    flags=re.IGNORECASE,
)


def texto_tem_pergunta_reciproca_apos_resposta(texto: str) -> bool:
    """Reconhece respostas seguidas de pergunta elíptica: ``estou bem, e o seu?``."""
    t = re.sub(r"\s+", " ", str(texto or "").strip().casefold())
    if not t.endswith("?"):
        return False
    reciproca = _PERGUNTA_RECIPROCA_FINAL.search(t)
    if not reciproca:
        return False
    prefixo = t[:reciproca.start()].strip(" ,;")
    return len(prefixo.split()) >= 2


def _segmentar_turno_misto(texto_normalizado: str) -> list[str]:
    """Separa atos claros sem fragmentar complementos do mesmo comando."""
    t = re.sub(r"\s+", " ", str(texto_normalizado or "")).strip()
    if not t:
        return []
    partes = [p.strip(" ,;") for p in re.split(r"[,;]+", t) if p.strip(" ,;")]
    if len(partes) == 1:
        # Duas frases também podem conter dois atos: "estou bem. Você gosta
        # de Slipknot?". O legado só separava vírgula e escondia a pergunta.
        frases = [
            p.strip(" .!,;")
            for p in re.split(
                r"[.!]\s+(?=(?:voc[eê]|tu|qual|quais|quem|o\s+que|como|quando|onde|por\s+que)\b)",
                t,
                flags=re.IGNORECASE,
            )
            if p.strip(" .!,;")
        ]
        if len(frases) > 1:
            partes = frases
    if len(partes) == 1:
        reciproca = _PERGUNTA_RECIPROCA_FINAL.search(t)
        if reciproca and texto_tem_pergunta_reciproca_apos_resposta(t):
            prefixo = t[:reciproca.start()].strip(" ,;")
            pergunta = t[reciproca.start():].strip(" ,;")
            partes = [prefixo, pergunta]
        m = _VERBOS_COMANDO.search(t)
        if len(partes) == 1 and m and m.start() > 0:
            prefixo = t[:m.start()].strip(" ,;")
            comando = t[m.start():].strip(" ,;")
            # Molduras educadas pertencem ao comando, não são conversa.
            if prefixo and not re.fullmatch(
                r"(?:voce|você)?\s*(?:pode|poderia|consegue|conseguiria|por favor|faz favor)|"
                r"(?:volta|retoma|continua)\s+a",
                prefixo,
            ):
                partes = [prefixo, comando]
    expandidas: list[str] = []
    for parte in partes:
        pedacos = re.split(r"\s+(?:e|mas|entao|então)\s+(?=" + _VERBOS_COMANDO.pattern[2:] + r")", parte)
        expandidas.extend(p.strip() for p in pedacos if p.strip())
    return expandidas or [t]


def classificar_modalidade_turno(
    texto: str,
    *,
    normalizar_texto: Callable[[str], str] | None = None,
    texto_tem_comando_explicito: Callable[[str], bool] | None = None,
    confirmacao_contextual_valida: bool = False,
) -> Dict[str, Any]:
    """Classifica o turno e preserva atos secundários em falas compostas."""
    bruto = str(texto or "").strip()
    normalizar = normalizar_texto if callable(normalizar_texto) else (lambda valor: str(valor or "").casefold().strip())
    normalizado = re.sub(r"\s+", " ", str(normalizar(bruto) or "")).strip()
    principal = _classificar_modalidade_base(
        bruto,
        normalizar_texto=normalizar,
        texto_tem_comando_explicito=texto_tem_comando_explicito,
        confirmacao_contextual_valida=confirmacao_contextual_valida,
    )
    pergunta_negativa = bool(re.search(
        r"^(?:nao|não)\s+\w+.*\b(?:qu[eê]|qual|porque|por que)\b",
        normalizado,
    )) or bool(
        str(principal.get("modalidade") or "") == "pergunta"
        and "?" in bruto
        and re.search(r"^(?:nao|não)\s+", bruto.casefold())
    )
    deliberativo = str(principal.get("modalidade") or "") == "deliberacao"
    modalidade_principal = str(principal.get("modalidade") or "")
    pergunta_composta_social = texto_tem_pergunta_reciproca_apos_resposta(
        normalizado
    ) or bool(
        modalidade_principal == "pergunta"
        and re.search(
            r"\b(?:estou|to|t[oô]|t[aá]|tudo)\b[^,;]{0,80}\b(?:bem|de boa|tranquil[oa]|suave)\b"
            r"[^,;]*[,;]\s*(?:lay(?:lay)?\s*[,;]?\s*)?"
            r"(?:voc[eê]|tu)\b[^?]{0,160}\?\s*$",
            normalizado,
            flags=re.IGNORECASE,
        )
    ) or bool(
        modalidade_principal == "pergunta"
        and re.search(
            r"\b(?:estou|to|t[oô]|t[aá]|tudo)\b.{0,80}\b(?:bem|de boa|"
            r"tranquil[oa]|suave)\b[^.!;,]{0,40}[.!;,]\s*(?:voc[eê]|tu)\b[^?]{0,160}\?\s*$",
            normalizado,
            flags=re.IGNORECASE,
        )
    )
    comando_separado = bool(re.search(
        r"[,;]\s*(?:abre|abra|fecha|feche|liga|ligue|desliga|desligue|toca|toque|"
        r"coloca|coloque|bota|põe|poe|cria|crie|apaga|remove|deleta|maximiza|"
        r"organiza|pausa|retoma|aumenta|abaixa|diminui|resume|resuma|leia|verifique)\b",
        normalizado,
    ))
    turno_protegido = (
        (
            modalidade_principal in {"pergunta", "deliberacao", "correcao"}
            or str(principal.get("natureza_acao") or "") == "decepcao"
        )
        and not comando_separado
        and not pergunta_composta_social
    )
    segmentos_texto = [normalizado] if pergunta_negativa or deliberativo or turno_protegido else _segmentar_turno_misto(normalizado)
    segmentos: list[Dict[str, Any]] = []
    for indice, trecho in enumerate(segmentos_texto):
        analise = _classificar_modalidade_base(
            trecho,
            normalizar_texto=lambda valor: str(valor or "").strip(),
            texto_tem_comando_explicito=texto_tem_comando_explicito,
            confirmacao_contextual_valida=confirmacao_contextual_valida,
        )
        modalidade = str(analise.get("modalidade") or "conversa")
        segmentos.append({
            "indice": indice,
            "texto": trecho[:300],
            "modalidade": modalidade,
            "confianca": float(analise.get("confianca") or 0.0),
            "motivo": str(analise.get("motivo") or ""),
            "autoriza_execucao": bool(analise.get("autoriza_execucao")),
            "acao_explicita": bool(analise.get("acao_explicita")),
            "requer_esclarecimento": bool(analise.get("requer_esclarecimento")),
            "natureza_acao": str(analise.get("natureza_acao") or "nenhuma"),
        })

    modalidades = {s["modalidade"] for s in segmentos if s["modalidade"] != "vazio"}
    tem_comando = not pergunta_negativa and not deliberativo and "comando" in modalidades
    prioridade = ("correcao", "comando", "pergunta", "confirmacao", "recusa", "deliberacao", "reacao", "conversa")
    ato_principal = next((m for m in prioridade if m in modalidades), str(principal.get("modalidade") or "conversa"))
    if tem_comando:
        ato_principal = "comando"
    modalidade_geral = "misto" if len(modalidades) > 1 and len(segmentos) > 1 else ato_principal
    texto_operacional = " ".join(s["texto"] for s in segmentos if s["modalidade"] == "comando").strip()
    texto_conversacional = " ".join(s["texto"] for s in segmentos if s["modalidade"] not in {"comando", "vazio"}).strip()
    autoriza_execucao = any(bool(s.get("autoriza_execucao")) for s in segmentos if s.get("modalidade") == "comando")
    if ato_principal == "confirmacao":
        autoriza_execucao = bool(confirmacao_contextual_valida)
    requer_esclarecimento = any(bool(s.get("requer_esclarecimento")) for s in segmentos)
    acao_explicita = any(bool(s.get("acao_explicita")) for s in segmentos)
    principal.update({
        "modalidade": ato_principal,
        "modalidade_geral": modalidade_geral,
        "ato_principal": ato_principal,
        "atos": [s["modalidade"] for s in segmentos],
        "segmentos": segmentos,
        "texto_operacional": texto_operacional[:500],
        "texto_conversacional": texto_conversacional[:500],
        "acao_explicita": acao_explicita,
        "autoriza_execucao": autoriza_execucao,
        "requer_esclarecimento": requer_esclarecimento,
        "depende_contexto": bool(principal.get("depende_contexto")) or ato_principal in {"confirmacao", "recusa"},
        "confirmacao_contextual_valida": bool(confirmacao_contextual_valida),
        "natureza_acao": str(principal.get("natureza_acao") or "nenhuma"),
        "motivo_decisao": str(principal.get("motivo") or ""),
    })
    if modalidade_geral == "misto":
        principal.update(confianca=max(float(principal.get("confianca") or 0.0), 0.94), motivo="turno com múltiplos atos compatíveis")
    return principal
