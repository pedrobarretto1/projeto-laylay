"""Variações curtas de fala para a personalidade da Laylay."""

from __future__ import annotations

import random
from typing import Iterable, Sequence


def escolher(items: Sequence[str] | Iterable[str], fallback: str = "") -> str:
    opcoes = [str(x).strip() for x in items if str(x or "").strip()]
    if not opcoes:
        return fallback
    return random.choice(opcoes)


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
        "next": [
            "Próxima faixa. Bora.",
            "Trocando a música. Sem drama.",
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
            "Oi, Pedro.",
            "Oi, tô aqui.",
            "Fala comigo.",
            "Tô por aqui.",
            "Cheguei. Pode jogar o caos na mesa.",
            "Tô acordada. O que você aprontou agora?",
        ],
        "bem_estar": [
            "Tô bem, presente e prestando atenção em você. E aí, como você tá de verdade?",
            "Tô firme. Um pouco feita de cabo e contexto, mas firme. E você?",
            "Tô bem sim. Qual foi a boa de hoje?",
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
    base = escolher(opcoes.get(chave, []), fallback=fallback)

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

    if chave == "bem_estar" and emocao == "envergonhada":
        return base + " Não repara se eu ficar meio boba."

    if chave in {"open_app", "open_site", "close_app", "playlist_play"} and texto_usuario:
        if "por favor" in texto_usuario.lower():
            return base + random.choice([" Você pediu bonitinho, então até coopero.", " Hoje eu deixo passar porque você foi educado."])
        if emocao == "brava":
            return base + random.choice([" Mas sem inventar moda depois.", " Resolve isso logo e me poupa."])

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
            f"{alvo_txt} não tava aberto como programa. Fechei a aba.",
            f"{alvo_txt} era aba, não app. Já fechei.",
            f"Peguei {alvo_txt} no navegador e encerrei por lá.",
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

    base = escolher(opcoes.get(status, []), fallback=fallback)
    if emocao == "brava" and status in {"app_aberto", "app_focado", "ja_aberto_focado", "url_aberta", "site_aberto_via_app"}:
        return base + " Agora resolve isso logo."
    if "por favor" in texto_usuario.lower() and status in {"app_aberto", "app_fechado", "ja_aberto_focado", "url_aberta"}:
        return base + " Você pediu bonitinho, então eu cooperei."
    return base


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
