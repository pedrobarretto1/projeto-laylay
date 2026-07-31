"""Personalidade curta para comandos, sempre ancorada no resultado real."""

from __future__ import annotations

import random
import re
from typing import Iterable

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao
from mente_laylay.personalidade.ritmo_natural import escolher_sem_repeticao


def _escolher(opcoes: Iterable[str], fallback: str) -> str:
    return escolher_sem_repeticao(
        opcoes,
        fallback=fallback,
        escolha_aleatoria=random.choice,
    )


def _alvo(resultado: ResultadoAcao) -> str:
    return re.sub(r"\s+", " ", str(resultado.alvo or "isso")).strip() or "isso"


def _fala_ja_tem_voz_propria(fala: str) -> bool:
    """Evita substituir uma reação autoral por uma frase pronta equivalente."""
    texto = re.sub(r"\s+", " ", str(fala or "")).strip()
    if len(texto.split()) < 7:
        return False
    return not bool(re.match(
        r"^(?:pronto|feito|ok|certo|beleza|conclui|concluí|executei|ação concluída|acao concluida|pedido concluído|pedido concluido)[,.:;!\s]",
        texto,
        re.IGNORECASE,
    ))


def _opcoes_iot(status: str, alvo: str) -> list[str]:
    ventilador = bool(re.search(r"\bventilador\b", alvo, re.IGNORECASE))
    if status == "ligado":
        if ventilador:
            return [
                f"Liguei {alvo}. Agora o calor tem concorrência.",
                f"Liguei {alvo}. Um pouco de vento nessa história.",
                f"Liguei {alvo}. Bem melhor com o ar circulando.",
            ]
        return [
            f"Liguei {alvo}. Já está funcionando.",
            f"Liguei {alvo}, e ele respondeu direitinho.",
            f"Liguei {alvo}. Ficou pronto por aí.",
        ]
    if status == "desligado":
        if ventilador:
            return [
                f"Desliguei {alvo}. Agora ficou mais quieto.",
                f"Desliguei {alvo}. O vento pode descansar.",
                f"Desliguei {alvo}. Ficou quietinho de novo.",
            ]
        return [
            f"Desliguei {alvo}. Tudo quieto por aí.",
            f"Desliguei {alvo}, e o estado foi confirmado.",
            f"Desliguei {alvo}. Tudo certo.",
        ]
    if status == "ja_estava_ligado":
        return [
            f"{alvo.capitalize()} já estava ligado. Dessa vez ele chegou antes de mim.",
            f"{alvo.capitalize()} já estava funcionando; não mexi no que já estava certo.",
        ]
    if status == "ja_estava_desligado":
        return [
            f"{alvo.capitalize()} já estava desligado. Nem precisei encostar.",
            f"{alvo.capitalize()} já estava quieto; mantive assim.",
        ]
    return []


def _opcoes_status(status: str, alvo: str) -> list[str]:
    if status in {"ligado", "desligado", "ja_estava_ligado", "ja_estava_desligado"}:
        return _opcoes_iot(status, alvo)

    grupos = {
        "pasta_criada": [
            f"Criei a pasta {alvo}. Espaço novo, ainda sem bagunça.",
            f"A pasta {alvo} já está pronta. Novinha em folha.",
            f"Criei {alvo}. Agora ela existe de verdade por aqui.",
        ],
        "subpasta_criada": [
            f"Criei {alvo} lá dentro. Tudo no lugar certo.",
            f"{alvo} já ganhou seu cantinho dentro da pasta.",
        ],
        "arquivo_criado": [
            f"Criei {alvo}. Saiu do pensamento e virou arquivo.",
            f"{alvo} já está criado e no lugar.",
            f"Arquivo {alvo} pronto. Pequeno, porém oficialmente existente.",
        ],
        "item_deletado": [
            f"Removi {alvo}. Foi embora sem deixar discurso de despedida.",
            f"{alvo} removido. Limpeza feita.",
            f"Apaguei {alvo}. Menos uma coisa ocupando espaço.",
        ],
        "item_movido_para_pasta": [
            f"Mudei {alvo} de lugar. Agora está na pasta certa.",
            f"{alvo} foi para o destino certo. Organização venceu hoje.",
        ],
        "janela_maximizada": [
            f"Maximizei {alvo}. Agora ele é o protagonista da tela.",
            f"{alvo} em destaque. Sem disputar espaço com ninguém.",
            f"Deixei {alvo} grandão na tela, como solicitado.",
        ],
        "app_aberto": [
            f"Abri {alvo}. Já está pronto pra entrar em cena.",
            f"{alvo} aberto. Pode assumir daqui.",
            f"Puxei {alvo} pra tela. Ele já respondeu.",
        ],
        "app_aberto_pc_b": [
            f"Abri {alvo} no PC B. A ordem atravessou direitinho.",
            f"{alvo} já está aberto no PC B.",
        ],
        "site_aberto": [
            f"Abri {alvo} no navegador. Caminho livre.",
            f"{alvo} já está na tela. Pode entrar.",
            f"Puxei {alvo} pela web. Chegou direitinho.",
        ],
        "site_ja_aberto_focado": [
            f"{alvo} já estava por ali; só puxei a aba pra frente.",
            f"Nem precisei abrir outra: achei {alvo} e trouxe pro foco.",
            f"{alvo} já estava aberto. Deixei a aba na sua frente.",
        ],
        "url_aberta": [
            f"Abri {alvo}. A página já está na tela.",
            f"{alvo} aberto no navegador. Rota confirmada.",
        ],
        "app_fechado": [
            f"Fechei {alvo}. Ele saiu de cena sem reclamar.",
            f"{alvo} encerrado. Menos uma janela pedindo atenção.",
            f"Fechei {alvo}. Pode riscar da tela.",
        ],
        "aba_fechada": [
            f"Fechei a aba de {alvo}. Uma a menos no desfile.",
            f"A aba de {alvo} saiu de cena.",
            f"Fechei {alvo} no navegador. Ficou mais respirável por lá.",
        ],
        "app_focado": [
            f"Trouxe {alvo} pra frente. Agora não tem como ele se esconder.",
            f"{alvo} já estava aberto; puxei pro foco.",
            f"Coloquei {alvo} na frente. É todo seu.",
        ],
        "ja_aberto_focado": [
            f"{alvo} já estava aberto e na frente. Pela primeira vez, nenhum drama.",
            f"{alvo} já estava exatamente onde você queria.",
        ],
        "volume_ajustado": (
            [
                f"Deixei o {alvo}. Agora ficou no ponto.",
                f"{alvo.capitalize()}. Nem sussurro, nem ataque sonoro.",
                f"Ajustei o {alvo}. Pedido cumprido sem estourar os ouvidos.",
            ]
            if re.search(r"\d", alvo)
            else [
                "Ajustei o volume. Agora ficou no ponto.",
                "Volume regulado. Nem sussurro, nem ataque sonoro.",
                "Deixei o volume como você pediu. Civilizado de novo.",
            ]
        ),
        "volume_aumentado": [
            "Aumentei o volume. Agora dá pra música se defender.",
            "Subi o som. Um pouco mais de presença, sem virar guerra.",
            "Volume aumentado. A trilha ganhou voz.",
        ],
        "volume_baixado": [
            "Baixei o volume. Seus ouvidos agradecem em silêncio.",
            "Diminuí o som. Agora ele conversa em vez de gritar.",
            "Volume reduzido. Ficou bem mais comportado.",
        ],
        "volume_mudo": [
            "Silenciei tudo. Paz sonora instaurada.",
            "Deixei no mudo. Agora até o PC fala baixo.",
            "Som cortado. Silêncio confirmado.",
        ],
        "volume_desmutado": [
            "Tirei do mudo. O som voltou do exílio.",
            "Devolvi a voz ao PC. Áudio liberado.",
            "Som de volta. O silêncio perdeu o cargo.",
        ],
        "midia_pause": [
            "Pausei. A música fica quieta até você chamar.",
            "Dei pausa. A trilha segura a respiração um pouquinho.",
            "Música pausada. Silêncio estratégico ativado.",
        ],
        "midia_play": [
            "Retomei. A trilha voltou pro lugar dela.",
            "Dei play. A música voltou a ocupar o ambiente.",
            "Retomei a música. O silêncio já tinha trabalhado o bastante.",
        ],
        "midia_pause_play": [
            "Alternei a reprodução. O player entendeu o recado.",
            "Troquei o estado da música. Comando confirmado.",
        ],
        "midia_next": [
            "Passei pra próxima. Essa fila não cria raiz.",
            "Próxima faixa na vez. A anterior já cumpriu o turno.",
            "Troquei a música. Vida nova pra trilha.",
        ],
        "midia_prev": [
            "Voltei pra anterior. Às vezes recuar é só bom gosto.",
            "Faixa anterior de volta. Essa ganhou mais uma chance.",
        ],
        "midia_replay": [
            "Recomecei a faixa. Do início, como manda o capricho.",
            "Voltei pro começo. Essa merece outra volta.",
        ],
        "midia_skip_ad": [
            "Pulei o anúncio. A programação normal agradece.",
            "Anúncio fora do caminho. Agora volta ao que interessa.",
            "Pronto, pulei. O anúncio perdeu a vez.",
        ],
        "musica_aberta": [
            f"Coloquei {alvo} pra tocar. Agora deixa a música fazer a parte dela.",
            f"{alvo} já está no caminho do som.",
            f"Puxei {alvo}. A trilha está por conta dela agora.",
        ],
        "playlist_aberta": [
            f"Abri {alvo} e enviei a primeira faixa.",
            f"{alvo} já está aberta; deixei a primeira faixa no navegador.",
            f"Puxei a playlist {alvo}. O navegador ficou com a primeira faixa.",
        ],
        "playlist_deletada": [
            f"Apaguei a playlist {alvo}. Ela saiu do palco.",
            f"A playlist {alvo} foi removida. Fim dessa seleção.",
        ],
        "agendamento_cancelado": [
            f"Cancelei {alvo}. Esse compromisso perdeu a vez.",
            f"{alvo} saiu da agenda. Espaço recuperado.",
        ],
    }
    return grupos.get(status, [])


def estilizar_fala_operacional(
    resultado: ResultadoAcao,
    fala_base: str,
    *,
    classe: str,
    emocao: str = "calma",
) -> str:
    """Varia só sucessos confirmados; falha e incerteza conservam a precisão original."""
    fala = re.sub(r"\s+", " ", str(fala_base or "")).strip()
    if classe != "sucesso" or resultado.confirmado is not True:
        return fala

    status = str(resultado.status or "").strip().casefold()
    alvo_txt = _alvo(resultado)
    if resultado.intent == "IOT_STATUS" and status in {"ligado", "desligado"}:
        estado = "ligado" if status == "ligado" else "desligado"
        opcoes_estado = [
            f"{alvo_txt.capitalize()} está {estado}. Estado conferido.",
            f"Conferi aqui: {alvo_txt} está {estado}.",
            f"{alvo_txt.capitalize()} está {estado}. Pelo menos ele não está fazendo mistério.",
        ]
        escolhida = _escolher(opcoes_estado, fala)
        if str(resultado.contexto.get("modo") or "").casefold() == "simulado":
            escolhida = f"No simulador, {escolhida[0].lower() + escolhida[1:]}"
        return escolhida
    if status in {"arquivo_criado", "pasta_criada", "subpasta_criada"}:
        # Criações compostas podem citar pasta, arquivo e conteúdo na mesma
        # confirmação. Uma variação curta não pode apagar esses detalhes.
        artefatos_fala = set(re.findall(r"\b[\wÀ-ÿ_-]+\.[a-z0-9]{1,8}\b", fala, re.IGNORECASE))
        artefatos_alvo = set(re.findall(r"\b[\wÀ-ÿ_-]+\.[a-z0-9]{1,8}\b", alvo_txt, re.IGNORECASE))
        if artefatos_fala - artefatos_alvo or re.search(r"\b(?:lá|la) dentro\b", fala, re.IGNORECASE):
            return fala
    if _fala_ja_tem_voz_propria(fala):
        return fala
    opcoes = _opcoes_status(status, alvo_txt)
    if not opcoes:
        return fala

    emocao_norm = str(emocao or "calma").strip().casefold()
    if emocao_norm in {"brava", "irritada", "nervosa", "triste"}:
        # Nessas emoções, a Laylay continua sendo ela, mas sem fabricar animação.
        opcoes = [opcao for opcao in opcoes if opcao.count(".") <= 1] or opcoes

    escolhida = _escolher(opcoes, fala)
    if str(resultado.contexto.get("modo") or "").casefold() == "simulado":
        escolhida = f"No simulador, {escolhida[0].lower() + escolhida[1:]}"
    return escolhida
