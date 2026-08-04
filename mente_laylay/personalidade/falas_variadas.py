"""Variações curtas de fala para a personalidade da Laylay."""

from __future__ import annotations

import random
from typing import Any, Callable, Iterable, Sequence

from mente_laylay.personalidade.ritmo_natural import escolher_sem_repeticao
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, inferir_confirmacao
from mente_laylay.personalidade.planejador_resposta import planejar_resposta_acao


def escolher(items: Sequence[str] | Iterable[str], fallback: str = "") -> str:
    return escolher_sem_repeticao(
        items,
        fallback=fallback,
        escolha_aleatoria=random.choice,
    )


def escolher_contextual(
    items: Sequence[str] | Iterable[str],
    *,
    contexto=None,
    texto_usuario: str = "",
    fallback: str = "",
) -> str:
    """Filtra as variações pelo momento antes de escolher uma delas."""
    opcoes = [str(item).strip() for item in items if str(item).strip()]
    if not opcoes:
        return fallback
    ctx = _extrair_contexto(contexto)
    emocao = str(ctx.get("current_emotion") or ctx.get("emocao") or "").casefold()
    funcao = str(ctx.get("funcao_comunicativa") or ctx.get("funcao") or "").casefold()
    modo_jogo = bool(ctx.get("modo_jogo") or ctx.get("game_mode"))
    usuario = str(texto_usuario or "").casefold()

    def pontuar(fala: str) -> float:
        base = fala.casefold()
        pontos = 0.0
        if modo_jogo:
            pontos += max(0.0, 5.0 - len(fala) / 18.0)
        if emocao in {"brava", "irritada"} or funcao in {"frustracao", "correcao"}:
            pontos += max(0.0, 3.0 - len(fala) / 35.0)
            if any(x in base for x in ("drama", "civilizado", "confissão", "foi de base")):
                pontos -= 4.0
        if funcao in {"frustracao", "correcao"} and any(
            x in base for x in ("entendi", "corrig", "não consegui", "tentei")
        ):
            pontos += 2.0
        if emocao == "envergonhada" and any(x in base for x in ("obrigada", "gostei", "feliz")):
            pontos += 1.5
        if usuario and any(palavra in base for palavra in usuario.split() if len(palavra) > 4):
            pontos += 0.5
        return pontos

    notas = [(pontuar(opcao), opcao) for opcao in opcoes]
    melhor = max(nota for nota, _ in notas)
    candidatas = [opcao for nota, opcao in notas if nota >= melhor - 0.15]
    return escolher(candidatas, fallback=fallback)


def _extrair_contexto(contexto=None) -> dict:
    return dict(contexto or {}) if isinstance(contexto, dict) else {}


def _alvo_bonito(alvo: str) -> str:
    return str(alvo or "").strip() or "isso"


def fala_de_confirmacao(
    chave: str,
    fallback: str = "Feito.",
    *,
    alvo: str = "",
    contexto=None,
    texto_usuario: str = "",
) -> str:
    chave = str(chave or "").strip().lower()
    alvo_txt = _alvo_bonito(alvo)
    ctx = _extrair_contexto(contexto)
    ultima_habilidade = str(ctx.get("ultima_habilidade") or "").strip().lower()
    ultimo_alvo = str(ctx.get("ultimo_alvo") or "").strip()
    emocao = str(ctx.get("current_emotion") or ctx.get("emocao") or "").strip().lower()
    texto_usuario = str(texto_usuario or "").strip()
    opcoes = {
        "pause": [
            "Pausada. Respira um pouco aí.",
            "Dei pause. Silêncio estratégico.",
            "Parei a música. Agora a trilha escuta você.",
        ],
        "play": [
            "Retomei a música.",
            "Dei play de novo.",
            "A música voltou.",
        ],
        "next": [
            "Próxima faixa. Bora.",
            "Trocando a música agora.",
            "Pulando pra seguinte.",
        ],
        "prev": [
            "Voltei pra anterior.",
        "Retornando uma faixa.",
        "Dei um passo atrás na música.",
    ],
        "replay": [
            "Recomeçando essa aí.",
            "Voltei pro começo da música.",
            "Repetindo ela sem trocar de faixa.",
        ],
        "skip_ad": [
            "Anúncio pulado.",
            "Pulei o anúncio.",
            "Pronto, tirei o anúncio da frente.",
        ],
    "open_app": [
            "Abrindo agora.",
            "Já vou abrir.",
            "Pronto, abrindo isso.",
            f"Deixa comigo. Já vou puxar {alvo_txt}.",
            f"{alvo_txt} tá vindo.",
        ],
        "close_app": [
            "Fechado.",
            "Tá encerrado.",
            "Pronto, fechei.",
            f"{alvo_txt} foi de base.",
            f"Já encerrei {alvo_txt}.",
        ],
        "open_site": [
            "Abrindo pra você.",
            "Já tô abrindo.",
            "Pronto, deixei aberto.",
            f"Já abri {alvo_txt}. Vai lá ver.",
            f"{alvo_txt} na tela. Sem cerimônia.",
        ],
        "playlist_add": [
            "Guardado.",
            "Anotado na playlist.",
            "Salvei certinho.",
            f"Guardei isso em {alvo_txt}.",
        ],
        "playlist_play": [
            "Abrindo a playlist.",
            "Tô colocando pra tocar.",
            "Já abri a playlist.",
            f"{alvo_txt} vindo pro som.",
            f"Já puxei {alvo_txt} pra tocar.",
        ],
        "volume_up": [
            "Aumentei o volume.",
            "Subi um pouco o som.",
            "Dei uma levantada no áudio.",
        ],
        "volume_down": [
            "Baixei o volume.",
            "Diminuí o som.",
            "Reduzi um pouquinho.",
        ],
        "volume_mute": [
            "Mudo ligado.",
            "Silenciei tudo.",
            "Pronto. Tudo em silêncio.",
        ],
        "volume_set": [
            "Volume ajustado.",
            "Pronto, regulado.",
            "Deixei no ponto.",
        ],
        "greeting": [
            "Oi.",
            "Oi, tô aqui.",
            "Fala comigo.",
            "Tô por aqui.",
            "Oi. Tô com você.",
            "Tô acordada. O que você aprontou agora?",
        ],
        "bem_estar": [
            "Tô bem, presente e prestando atenção em você. E você, como tá?",
            "Tô bem. Cabeça no lugar e curiosa pelo que vem. Mas e você, tá tudo bem por aí?",
            "Tô bem sim. Agora fiquei curiosa com o teu lado: como você tá?",
            "Por aqui tá tudo certo. E do teu lado, como você tá de verdade?",
        ],
        "chat_on": [
            "Modo chat ativado. Tô aqui com você.",
            "Chat ligado. Pode mandar.",
            "Agora sim, conversa aberta.",
            "Pronto, larguei a pressa. Pode falar comigo no teu ritmo.",
        ],
        "chat_off": [
            "Modo chat desativado. Voltei pro modo ação.",
            "Chat fechado. Tô pronta pra agir.",
            "Saí do papo e voltei pra execução.",
        ],
    }
    base = escolher_contextual(
        opcoes.get(chave, []), contexto=ctx, texto_usuario=texto_usuario, fallback=fallback,
    )

    if chave == "greeting":
        if ultima_habilidade == "playlist":
            extras = [
                " Ainda tô com eco de música na cabeça, inclusive.",
                f" Ainda lembrando de {ultimo_alvo} por aqui.",
            ]
            if ultimo_alvo:
                return base + random.choice(extras)
        if emocao in {"alegre", "debochada"}:
            return base + random.choice([" Bora ver no que isso vai dar.", " Manda tua próxima ideia."])

    if chave in {"open_app", "open_site", "close_app", "playlist_play"} and texto_usuario:
        if emocao == "brava":
            return base

    return base


def fala_por_estado_acao(
    status: str,
    fallback: str = "Feito.",
    *,
    alvo: str = "",
    contexto=None,
    texto_usuario: str = "",
) -> str:
    status = str(status or "").strip().lower()
    alvo_txt = _alvo_bonito(alvo)
    ctx = _extrair_contexto(contexto)
    emocao = str(ctx.get("current_emotion") or ctx.get("emocao") or "").strip().lower()
    texto_usuario = str(texto_usuario or "").strip()

    opcoes = {
        "app_aberto": [
            f"Abrindo {alvo_txt}.",
            f"{alvo_txt} entrando agora.",
            f"Já vou abrir {alvo_txt}.",
        ],
        "app_aberto_sem_foco": [
            f"{alvo_txt} já estava aberto, mas não consegui trazer pra frente agora.",
            f"{alvo_txt} já tá aberto, só não respondeu ao foco dessa vez.",
            f"Eu achei {alvo_txt} aberto, mas a janela não colaborou pra vir pro foco.",
        ],
        "abertura_solicitada": [
            f"Pedi para abrir {alvo_txt}, mas ele ainda não apareceu para eu confirmar.",
            f"O comando de abertura de {alvo_txt} foi aceito; ele ainda está inicializando.",
            f"Disparei {alvo_txt}, mas ainda não tenho uma janela ou processo para confirmar.",
        ],
        "app_aberto_pc_b": [
            f"Abrindo {alvo_txt} no PC B.",
            f"Mandei {alvo_txt} acordar no PC B.",
            f"{alvo_txt} já tá indo pro PC B.",
        ],
        "app_focado": [
            f"{alvo_txt} já tava aberto, só puxei pra frente.",
            f"{alvo_txt} já existia aí, só trouxe pro foco.",
            f"{alvo_txt} tava se escondendo. Joguei ele pra frente.",
        ],
        "app_iniciado_focado": [
            f"Iniciei {alvo_txt} e trouxe a nova janela pra frente.",
            f"Abri {alvo_txt}; ele acabou de chegar e já está em foco.",
        ],
        "ja_aberto_focado": [
            f"{alvo_txt} já tava na tua cara.",
            f"{alvo_txt} já estava aberto e em foco. Nem precisei encostar.",
            f"{alvo_txt} já tava ali, mais exposto que confissão.",
        ],
        "app_fechado": [
            f"Pronto, fechei {alvo_txt}.",
            f"{alvo_txt} foi encerrado.",
            f"{alvo_txt} saiu de cena agora.",
        ],
        "app_fechado_pc_b": [
            f"Fechei {alvo_txt} no PC B.",
            f"{alvo_txt} saiu de cena no PC B.",
            f"Despachei {alvo_txt} no PC B.",
        ],
        "aba_fechada": [
            f"Fechei a aba de {alvo_txt}.",
            f"Aba de {alvo_txt} encerrada.",
            f"{alvo_txt} saiu do navegador agora.",
        ],
        "aba_fechada_em_vez_de_app": [
            f"O {alvo_txt} estava aberto numa aba. Fechei e conferi.",
            f"Achei o {alvo_txt} no navegador e fechei a aba certinha.",
            f"Era uma aba do {alvo_txt}, não um programa separado. Já fechei.",
        ],
        "app_fechado_em_vez_de_aba": [
            f"{alvo_txt} tava aberto como programa, não como aba. Fechei ele.",
            f"{alvo_txt} era app de verdade, então encerrei o programa.",
            f"Isso aí não era aba, era app. Já cortei pela raiz.",
        ],
        "url_aberta": [
            f"Abrindo {alvo_txt}.",
            f"Já deixei {alvo_txt} na tela.",
            f"{alvo_txt} abrindo agora.",
        ],
        "site_aberto": [
            f"Abri {alvo_txt} no navegador.",
            f"{alvo_txt} veio pela rota web certinho.",
            f"Joguei {alvo_txt} no navegador pra você.",
        ],
        "url_aberta_via_app": [
            f"{alvo_txt} abriu pelo caminho web.",
            f"Abri {alvo_txt} no navegador.",
            f"{alvo_txt} veio pela rota de site, mas veio.",
        ],
        "site_aberto_via_app": [
            f"Abrindo {alvo_txt}.",
            f"{alvo_txt} já tá entrando pela web.",
            f"Joguei {alvo_txt} no navegador pra você.",
        ],
        "protocolo_aberto": [
            f"Abrindo {alvo_txt}.",
            f"{alvo_txt} respondeu pelo protocolo certo.",
            f"Disparei {alvo_txt} do jeito que ele gosta.",
        ],
        "janela_maximizada": [
            f"Deixei {alvo_txt} em destaque.",
            f"{alvo_txt} ficou em tela cheia normal agora.",
            f"Maximizei {alvo_txt}. Tá em destaque de verdade agora.",
        ],
        "janela_maximizada_pc_b": [
            f"Maximizei {alvo_txt} no PC B.",
            f"{alvo_txt} ficou em destaque no PC B.",
            f"Joguei {alvo_txt} pro foco no PC B.",
        ],
        "busca_site_iniciada": [
            f"Tô procurando o melhor caminho pra {alvo_txt}.",
            f"Abri a busca de {alvo_txt} pra entrar no site certo.",
            f"Comecei a caçada por {alvo_txt}.",
        ],
        "volume_ajustado": [
            "Pronto, volume ajustado.",
            "Deixei o som no ponto.",
            "Agora o volume tá civilizado.",
        ],
        "volume_aumentado": [
            "Aumentei o volume.",
            "Subi o som.",
            "Dei uma levantada no áudio.",
        ],
        "volume_baixado": [
            "Baixei o volume.",
            "Diminuí o som.",
            "Reduzi o barulho um pouco.",
        ],
        "volume_mudo": [
            "Mudo ligado.",
            "Silenciei tudo.",
            "Agora ficou em silêncio.",
        ],
        "remetente_silenciado": [
            f"Pronto, silenciei {alvo_txt}. Agora ele só fala se você deixar.",
            f"{alvo_txt} entrou no modo mudo.",
            f"Botei {alvo_txt} pra falar baixo daqui pra frente.",
        ],
        "emails_lidos": [
            "Te contei os emails que estavam no radar.",
            "Já olhei tua caixa e te passei o resumo.",
            "Emails lidos. Sem romantizar a caixa de entrada.",
        ],
        "emails_sincronizados": [
            "Caixa atualizada.",
            "Puxei os emails mais recentes.",
            "Sincronizei teus emails agora.",
        ],
        "clima_consultado": [
            "Clima consultado direitinho.",
            "Já dei uma espiada no tempo real pra você.",
            "Tempo na mesa. Informação sem chute.",
        ],
        "cancelado": [
            "Beleza, cancelei isso.",
            "Certo, deixei pra lá.",
            "Tá, descartei essa ação.",
        ],
        "playlist_contexto_bloqueado": [
            "Fechado, sem playlist agora.",
            "Cortei o embalo musical por enquanto.",
            "Tranquilo. Deixei a playlist quietinha.",
        ],
        "falha_execucao": [
            f"Tentei mexer em {alvo_txt}, mas a ação não confirmou direito.",
            f"Tentei executar isso em {alvo_txt}, mas ele não respondeu como devia.",
            f"Eu tentei, mas {alvo_txt} não colaborou. Não vou fingir que deu certo.",
        ],
        "nao_encontrado": [
            f"Não achei {alvo_txt} por aqui.",
            f"{alvo_txt} não apareceu no radar.",
            f"Procurei {alvo_txt}, mas ele não deu as caras.",
        ],
        "notificacoes_sem_suporte": [
            "Ainda não tenho o painel completo das notificações.",
            "Essa parte das notificações ainda não responde na minha mão.",
            "Entendi o pedido, mas esse pedaço ainda não tá plugado inteiro em mim.",
        ],
    }

    base = escolher_contextual(
        opcoes.get(status, []), contexto=ctx, texto_usuario=texto_usuario, fallback=fallback,
    )
    confirmado = inferir_confirmacao(status, True)
    return planejar_resposta_acao(
        ResultadoAcao(
            status=status,
            alvo=alvo_txt,
            texto_usuario=texto_usuario,
            contexto=ctx,
            executou=True if confirmado is True else None,
            confirmado=confirmado,
        ),
        base,
        emocao_preferida=emocao or "calma",
    ).fala


def fala_falha_contextual(
    categoria: str,
    *,
    texto_normalizado: str = "",
    detalhe: str = "",
    incluir_generica: bool = True,
) -> str:
    """Falas claras para falhas de entendimento/execucao sem prometer acao falsa."""
    cat = str(categoria or "").strip().lower()
    texto_norm = str(texto_normalizado or "").strip().lower()
    alvo = str(detalhe or "").strip()

    if cat == "ia_timeout":
        return escolher([
            "Meu modelo demorou demais pra me responder agora. Tenta de novo em alguns segundos.",
            "Eu fiquei esperando a resposta e ela não voltou a tempo. Me chama de novo já já.",
            "A resposta travou no caminho. Daqui a pouco eu tento de novo contigo.",
        ])

    if cat == "ia_api":
        return escolher([
            "Minha conexão com o cérebro local deu ruim agora. Tenta de novo daqui a pouquinho.",
            "O meu lado da IA tropeçou feio agora. Me chama de novo em instantes.",
            "Perdi o contato com a parte que pensa mais fundo. Se repetir já já, eu tento de novo.",
        ])

    if cat == "execucao":
        if alvo:
            return escolher([
                f"Eu entendi o pedido, mas travou na hora de mexer em {alvo}.",
                f"Peguei a ideia, só que a execução de {alvo} não fechou direito.",
                f"Não foi falta de entender; foi {alvo} que não colaborou na prática.",
            ])
        return escolher([
            "Eu entendi o que você quis, mas a execução tropeçou no caminho.",
            "Não foi tua fala que falhou; fui eu que não consegui fechar a ação agora.",
            "Peguei o pedido, só que a parte prática desandou no meio.",
        ])

    if any(p in texto_norm for p in ["como voce", "como você", "tudo bem", "ta bem", "tá bem", "tudo na paz", "de boa"]):
        return escolher([
            "Eu ouvi teu tom, só não fechei a leitura direito. Me pergunta de novo sem pressa.",
            "Quase peguei, mas a curva ficou torta na minha cabeça. Pode repetir?",
            "Entendi que era papo, só não encaixei tua frase direito. Tenta mais uma vez pra mim.",
        ])

    if not incluir_generica:
        return ""

    return escolher([
        "Me perdi um pouco nessa curva. Fala de outro jeito pra mim.",
        "Não fechei tua frase direito aqui. Repete com outras palavras?",
        "Eu quase peguei, mas faltou encaixar a ideia. Tenta de novo pra mim.",
    ])


def emitir_falha_contextual(
    categoria: str,
    texto_usuario: str = "",
    *,
    detalhe: str = "",
    normalizar_texto: Callable[[str], str],
    falar: Callable[..., Any],
    log: Callable[[str], Any] = print,
) -> None:
    """Emite somente a falha operacional; nunca improvisa conversa local."""
    cat = str(categoria or "").strip().lower()
    texto_norm = normalizar_texto(str(texto_usuario or "")) if callable(normalizar_texto) else str(texto_usuario or "").lower()
    alvo = str(detalhe or "").strip()
    direta = fala_falha_contextual(cat, texto_normalizado=texto_norm, detalhe=alvo, incluir_generica=False)
    if direta:
        falar(direta, "calma", 1)
        return
    falar(fala_falha_contextual(cat, texto_normalizado=texto_norm, detalhe=alvo), "calma", 1)
