"""Porteiro central para autorizar acoes praticas da Laylay.

Este modulo nao executa nada. Ele apenas decide se uma acao pratica
parece autorizada pelo pedido atual, por confirmacao recente ou por
contexto forte. A ideia e manter as habilidades existentes, mas evitar
que memoria antiga ou rotina solta virem execucao automatica.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, Dict, Iterable

from mente_laylay.cognicao.evidencia_operacional import texto_tem_evidencia_iot_parametro
from mente_laylay.memoria_mental.estado_continuidades import atualizar_continuidades
from mente_laylay.memoria_mental.estado_musical import (
    bloquear_playlist_temporariamente,
    playlist_bloqueada_agora,
)


ACOES_MUSICA = {
    "music_search",
    "musica",
    "youtube_search",
    "youtube_play",
    "playlist_play",
    "tocar_playlist",
    "tocar_playlist_shuffle",
    "playlist_shuffle",
}


def montar_contexto_porteiro_acoes(
    *,
    playlist_bloqueada: bool,
    playlist_ativa: bool,
    auto_next_playlist: bool,
    ultima_playlist: str,
    mente_integrada_estado: Dict[str, Any] | None,
    messages: Any,
) -> Dict[str, Any]:
    """Retrato minimo para o porteiro central decidir sem executar nada."""
    return {
        "playlist_bloqueada": bool(playlist_bloqueada),
        "playlist_ativa": bool(playlist_ativa),
        "auto_next_playlist": bool(auto_next_playlist),
        "ultima_playlist": str(ultima_playlist or "").strip(),
        "mente": dict(mente_integrada_estado or {}),
        "messages": messages,
    }


def normalizar_texto(texto: str) -> str:
    bruto = str(texto or "").lower()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    sem_acento = re.sub(r"[^\w\s?]", " ", sem_acento)
    return re.sub(r"\s+", " ", sem_acento).strip()


def _parece_agradecimento_ou_elogio_curto(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    variantes = [
        "obrigado", "obrigada", "brigado", "brigada", "orbigado", "orbrigado",
        "obigado", "obridago", "valeu", "valew", "vlw", "perfeito", "amei",
        "gostei", "maravilhoso", "maravilhosa", "lindo", "linda", "fofo",
        "fofa", "incrivel", "estou te elogiando", "to te elogiando",
        "apenas um elogio", "so um elogio",
        "voce e legal", "voce e bem legal", "voce e muito legal",
        "vc e legal", "vc e bem legal", "te acho legal",
    ]
    return any(v in t for v in variantes)


def _parece_meta_conversa_curta(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    padroes = [
        r"^(ta de boa|tudo de boa|ta suave|tudo suave)(\s+lay|\s+laylay)?\??$",
        r"^(voce ta de boa|voce esta de boa|c voce ta de boa)(\s+lay|\s+laylay)?\??$",
        r"^(nao|não)\s+lay,?\s+(eu\s+)?to\s+te\s+perguntando\s+se\s+voce\s+esta\s+bem\??$",
        r"^(nao|não)\s+lay,?\s+(eu\s+)?to\s+te\s+falando\s+o\s+que\??$",
        r"^apenas\s+estou\s+te\s+perguntando\s+se\s+voce\s+esta\s+bem\??$",
        r"^o\s+que\s+eu\s+estou\s+te\s+perguntando\??$",
    ]
    return any(re.fullmatch(p, t) for p in padroes) or (
        ("estou te perguntando" in t or "to te perguntando" in t)
        and any(p in t for p in ["voce esta bem", "ta tudo bem", "tudo bem", "ta de boa", "de boa"])
    )


def texto_social_curto(texto: str) -> bool:
    """Reconhece conversa curta que nao deve herdar comando antigo."""
    t = normalizar_texto(texto)
    if not t:
        return False

    if _parece_meta_conversa_curta(t):
        return True

    palavras = t.split()
    if len(palavras) > 8:
        return False

    comandos = {
        "playlist", "musica", "toca", "toque", "coloca", "coloque",
        "abre", "abrir", "entra", "fecha", "fechar", "apaga", "apagar",
        "cria", "criar", "arquivo", "pasta", "volume", "pausa", "proxima",
        "anterior", "youtube", "google", "email", "emails",
    }
    if any(p in t for p in comandos):
        return False

    if _parece_agradecimento_ou_elogio_curto(t):
        if len(palavras) <= 8:
            return True

    padroes = [
        r"^(oi|ola|e ai|salve|bom dia|boa tarde|boa noite)(\s+lay|\s+laylay)?$",
        r"^(como voce esta|como voce ta|como ta|voce esta bem|voce ta bem|esta bem|ta bem|tudo bem|tudo numa boa|tudo na boa|de boa|ta de boa|tudo de boa|tudo na paz)(\s+lay|\s+laylay)?\??$",
        r"^(lay|laylay)\??$",
        r"^(obrigado|obrigada|valeu|vlw|brigado|brigada)(\s+lay|\s+laylay)?$",
        r"^(perfeito|amei|gostei|maravilhoso|maravilhosa|fofo|fofa|lindo|linda|incrivel|incrível)(\s+lay|\s+laylay)?$",
        r"^(perfeito\s+obrigado|perfeito\s+obrigada|valeu\s+lay|obrigado\s+lay|obrigada\s+lay|valeu\s+laylay)$",
        r"^(estou te elogiando|to te elogiando|tava te elogiando)(\s+lay|\s+laylay)?$",
        r"^(nao|não)\s+lay\s+(e|é)\s+(so|s[oó])\s+um\s+elogio$",
        r"^(nao|não)\s+lay\s+(e|é)\s+apenas\s+um\s+elogio$",
        r"^(era so|era só)\s+um\s+elogio$",
        r"^(kk+|haha+|rs+|kkkk+|relaxa|de boa|tranquilo|beleza|blz|ok|certo)$",
        r"^(nao|não)\s+lay,?\s+to\s+perguntando\s+se\s+ta\s+tudo\s+bem",
    ]
    return any(re.fullmatch(p, t) for p in padroes)


def texto_conversa_casual_sem_acao(texto: str) -> bool:
    """Reconhece falas de conversa que nao devem disparar roteadores de comando."""
    t = normalizar_texto(texto)
    if not t:
        return False
    if texto_parece_pergunta_factual(t):
        return False
    if texto_tem_comando_explicito(t):
        return False
    if any(p in t for p in ["em foco", "foco", "tela cheia", "fullscreen", "maximiza", "maximizar", "pra frente", "para frente", "primeiro plano"]):
        return False
    if texto_social_curto(t):
        return True

    # Perguntar se a Laylay conhece, viu ou ouviu falar de um assunto é
    # conversa, mesmo quando o nome contém números. Não é ordem para pesquisar,
    # abrir site ou executar qualquer ação relacionada ao tema.
    if re.search(
        r"\b(?:voce|você)\s+(?:viu|soube|conhece)|"
        r"\b(?:ja\s+|já\s+)?ouviu\s+falar\b|"
        r"\bficou\s+sabendo\b",
        t,
    ):
        return True

    # Horários e números também aparecem em relatos pessoais. A presença de
    # ``17:30`` ou de uma modalidade esportiva não transforma a fala em ação.
    relato_pessoal = bool(re.search(
        r"\b(?:eu\s+)?(?:vou|fui|viajo|viajar|jogar|competir|participar|passar|fico|ficar)\b|"
        r"\b(?:minha\s+semana|jogos?\s+regionais|campeonato|arremessamento\s+de\s+peso)\b",
        t,
    ))
    if relato_pessoal and not texto_tem_comando_explicito(t):
        return True

    comandos = {
        "playlist", "musica", "toca", "toque", "coloca", "coloque", "abre", "abrir",
        "fecha", "fechar", "apaga", "apagar", "cria", "criar", "volume", "youtube",
        "google", "site", "aba", "janela", "programa", "app", "arquivo", "pasta",
        "email", "emails", "notificacao", "notificacoes", "agenda", "lembrete",
        "agendamento", "netflix", "spotify", "pesquisa", "buscar", "procura",
        "foco", "fullscreen", "maximiza", "maximizar",
    }
    if any(p in t for p in comandos):
        return False

    padroes = [
        r"^(ta de boa|tudo na paz|tudo de boa|tudo suave|ta suave)\??$",
        r"^(essa|esse)\s+.+\s+(e|eh)\s+.+$",
        r"^(eu to|eu estou)\s+te\s+perguntando\s+.+\??$",
        r"^o que eu estou te perguntando\??$",
        r"^(nao|não)\s+lay,?\s+.+$",
        r"^(?:nao tem|não tem|tem nada|nao tenho|não tenho)\s+(?:nada\s+)?(?:pra|para)\s+fazer(?:\s+.+)?$",
        r"^(?:que\s+)?(?:dia|tarde|noite|madrugada)\s+(?:chata|chato|arrastada|arrastado)$",
    ]
    if any(re.fullmatch(p, t) for p in padroes):
        return True

    palavras = t.split()
    if (
        len(palavras) <= 8
        and "http" not in t
        and not any(ch.isdigit() for ch in t)
    ):
        return True

    if re.fullmatch(r"^(eu to|eu estou)\s+.+$", t):
        return True
    if re.fullmatch(r"^(entao|então)\s+.+$", t):
        return True
    if re.fullmatch(r"^(como assim|ue|u[eé]|oxi|ata|ah ta|ah tá)\??$", t):
        return True

    if "?" in str(texto or "") and len(t.split()) <= 10:
        return True
    return False


def texto_parece_pergunta_factual(texto: str) -> bool:
    """Separa perguntas de conhecimento de continuidades sociais curtas."""
    t = normalizar_texto(texto)
    if not t:
        return False
    if any(p in t for p in ["como voce", "como você", "voce esta", "você está", "voce ta", "você tá"]):
        return False
    return bool(re.match(
        r"^(?:quem\s+(?:e|é)|qual\s+(?:e|é)|o\s+que\s+(?:e|é)|quando\b|onde\b|por\s+que\b|porque\b|como\s+funciona\b)",
        t,
    ))


def texto_tem_comando_explicito(texto: str) -> bool:
    """Detecta quando ha pedido pratico claro o bastante para nao ser tratado como papo."""
    t = normalizar_texto(texto)
    if not t:
        return False
    t_operacional = re.sub(r"^(?:agora|entao|então)\s+", "", t).strip()

    if re.match(r"^(?:nao|não|nem)\b", t_operacional):
        return False

    # É uma forma elíptica de comando: a operação concreta só será recuperada
    # se existir continuidade oficial compatível. Sem esse sinal, o árbitro
    # encerrava "essa também" como conversa antes do roteador canônico.
    if re.fullmatch(
        r"(?:e\s+)?(?:(?:essa|esta|esse|este|isso|ela|ele)(?:\s+(?:aqui|ai|aí))?\s+"
        r"(?:tambem|também)|(?:tambem|também)\s+(?:essa|esta|esse|este|isso|ela|ele)|"
        r"mais\s+(?:essa|esta|esse|este))",
        t_operacional,
    ):
        return True

    # Edição elíptica ainda é um pedido explícito pelo ato de fala. O alvo não
    # nasce aqui: o roteador só a executa quando existe arquivo recente tipado.
    if re.match(
        r"^(?:escreve|escreva|grava|grave|adiciona|adicione|"
        r"acrescenta|acrescente)\b\s+\S+",
        t_operacional,
    ):
        return True

    if re.search(r"^(?:coloca|coloque|bota|ponha|põe|poe|move|mova|posiciona|posicione|deixa|joga)\b", t_operacional) and re.search(
        r"\b(?:(?:na|a|à|para a)\s+(?:esquerda|direita)|"
        r"(?:no|pro|para o|do)\s+lado\s+(?:esquerdo|direito))\b",
        t_operacional,
    ):
        return True

    # Pesquisas locais são comandos práticos de somente leitura. Verbos como
    # "encontra" e "localiza" não faziam parte do vocabulário operacional e
    # o árbitro encerrava o turno como conversa antes de o especialista de
    # arquivos receber a frase. A guarda exige verbo inicial + objeto de
    # arquivo/código, preservando perguntas de capacidade e comentários.
    if re.search(
        r"^(?:encontra|encontre|acha|ache|procura|procure|busca|busque|"
        r"pesquisa|pesquise|localiza|localize)\b",
        t,
    ) and re.search(
        r"\b(?:arquivo|arquivos|documento|documentos|codigo|código|script|"
        r"scripts|imagem|imagens|foto|fotos|projeto)\b",
        t,
    ):
        return True

    if texto_pede_playlist_explicitamente(t) or texto_pede_musica_explicitamente(t):
        return True

    if texto_tem_evidencia_iot_parametro(t):
        return True

    if re.search(r"\b(?:me\s+lembra|lembra\s+(?:de|pra)|me\s+avisa|cria\s+(?:um\s+)?lembrete|agende|agendar)\b", t):
        return True

    if "http" in t or "www " in t:
        return True

    if any(p in t for p in ["email", "emails", "e mail"]):
        if any(p in t for p in [
            "quantos", "tem algum", "tem novo", "tem novos", "chegou",
            "chegaram", "pode ler", "le os", "ler os", "o que falam",
            "o que chegou", "me fala dos", "me fale dos",
        ]):
            return True

    verbos = [
        "abre", "abrir", "abra", "entra", "entrar", "entre", "acessa", "acessar",
        "acesse", "vai no", "vai na", "ir no", "ir na",
        "fecha", "fechar", "feche", "coloca", "coloque",
        "bota", "poe", "põe", "toca", "toque", "cria", "criar", "crie",
        "escreve", "escrever", "escreva", "grava", "gravar", "grave",
        "adiciona", "adicionar", "adicione", "acrescenta", "acrescentar",
        "acrescente",
        "apaga", "apagar", "deleta", "deletar", "remove", "remover", "exclui", "excluir",
        "maximiza", "maximizar", "organiza", "organizar", "silencia", "silenciar",
        "sincroniza", "sincronizar", "aumenta", "aumentar", "abaixa", "baixar",
        "diminui", "diminuir", "pausa", "pausar", "despausa", "retoma", "continua",
        "liga", "ligar", "ligue", "desliga", "desligar", "desligue", "acende",
    ]
    alvos = [
        "playlist", "musica", "música", "som", "volume", "email", "emails",
        "notificacao", "notificacoes", "site", "aba", "janela", "programa", "app",
        "arquivo", "pasta", "desktop", "area de trabalho", "área de trabalho",
        "steam", "opera", "chrome", "edge", "vscode", "visual studio code",
        "youtube", "netflix", "spotify", "instagram", "whatsapp", "ifood",
        "microsoft store", "google",
        "ventilador", "tomada", "lampada", "lâmpada", "luz", "dispositivo", "iot",
    ]
    if any(v in t for v in verbos) and any(a in t for a in alvos):
        return True

    if any(x in t for x in ["tela cheia", "fullscreen", "em foco", "pra frente", "para frente", "primeiro plano"]):
        return True

    if any(x in t for x in [
        "pausa ela",
        "pausa ele",
        "pausa isso",
        "despausa ela",
        "despausa ele",
        "retoma ela",
        "retoma ele",
        "continua ela",
        "continua ele",
        "proxima musica",
        "próxima música",
        "musica anterior",
        "música anterior",
        "volta a musica",
        "volta a música",
        "volta para a de antes",
        "volta pra de antes",
        "volta pra anterior",
        "toca ela de novo",
        "repete ela",
        "repete essa",
    ]):
        return True

    if re.search(
        r"\b(?:traz|trazer|abre|abrir|coloca|colocar|bota|botar|toca|tocar|restaura|restaurar|refaz|refazer)\b.*\b(?:de volta|de novo|novamente)\b",
        t,
    ):
        return True

    if re.search(r"\b(?:pode\s+ler|pode\s+ver|le\s+eles|l[eê]\s+eles|ler\s+eles)\b", t):
        return True

    if re.search(
        r"\b(?:traz|trazer|cria|criar|faz|refaz|restaura|restaurar)\b.*\b(?:de volta|de novo|novamente)\b",
        t,
    ):
        return True

    if re.search(
        r"^\s*(?:apaga|apagar|delete|deleta|deletar|remove|remover|exclui|excluir)\s+"
        r"(?:o|a|os|as|um|uma)?\s*[a-z0-9_\-.][a-z0-9_\-.\s]{0,40}$",
        t,
    ):
        return True

    return False


def texto_conversa_contextual_sem_comando(texto: str, contexto: Dict[str, Any] | None = None) -> bool:
    """Protege continuidades de conversa para nao virarem comando por heranca torta."""
    t = normalizar_texto(texto)
    if not t:
        return False
    if texto_parece_pergunta_factual(t):
        return False

    if texto_tem_comando_explicito(t):
        return False

    if texto_social_curto(t) or texto_conversa_casual_sem_acao(t):
        return True

    contexto = contexto if isinstance(contexto, dict) else {}
    mente = contexto.get("mente") or {}
    foco = contexto.get("foco_vivo") or {}
    ultima_habilidade = str((mente.get("ultima_habilidade") if isinstance(mente, dict) else "") or "").strip().lower()
    ultima_intencao = str((mente.get("ultima_intencao") if isinstance(mente, dict) else "") or "").strip().upper()
    ultimo_topico = normalizar_texto(str(contexto.get("ultimo_topico") or foco.get("topico") or foco.get("alvo") or "").strip())
    foco_tipo = normalizar_texto(str(foco.get("tipo") or "").strip())

    contexto_conversa = (
        foco_tipo in {"conversa", "opiniao", "opinião"}
        or ultima_habilidade in {"conversa", "opiniao", "opinião", "pesquisa"}
        or ultima_intencao in {"OPINION", "QUESTION", "CONTINUE", "WELLBEING", "PRAISE", "SEARCH"}
    )

    if any(p in t for p in [
        "faz o l", "como assim", "e porque", "e por que", "o que voce acha",
        "o que voce sacha", "qual sua opiniao", "qual sua opinião", "o que voce pensa",
    ]):
        return True

    if any(p in t for p in ["nao lay", "não lay", "a nao lay", "ah nao lay", "eu to falando", "eu estou falando"]):
        return True

    if any(p in t for p in ["lula", "presidente", "politica", "política"]) and not texto_tem_comando_explicito(t):
        return True

    respostas_humanas = [
        "sim", "claro", "claro que sim", "aham", "uhum", "isso", "isso mesmo",
        "foi sim", "veio sim", "veiuo sim", "é sim", "e sim", "nao gostei", "não gostei",
        "quero outra", "mas eu to falando", "mas eu estou falando",
    ]
    if any(t == r or t.startswith(f"{r} ") for r in respostas_humanas):
        return True if (contexto_conversa or ultimo_topico) else False

    if contexto_conversa and len(t.split()) <= 10:
        return True

    if ultimo_topico and len(t.split()) <= 10 and any(p in t for p in ["ele", "ela", "isso", "dele", "dela", "desse", "dessa"]):
        return True

    return False


def texto_bloqueia_playlist_agora(texto: str) -> bool:
    t = normalizar_texto(texto)
    if "playlist" not in t:
        return False
    negativos = [
        "sem playlist",
        "nao playlist",
        "nao quero playlist",
        "nao toca playlist",
        "nao coloca playlist",
        "chega de playlist",
        "para de playlist",
        "para com playlist",
        "corta playlist",
        "deixa playlist quieta",
        "sem musica agora",
    ]
    return any(p in t for p in negativos) or ("nao" in t and "playlist" in t)


def texto_cancela_acao_agora(texto: str) -> bool:
    """Reconhece desistência explícita sem capturar conversa social ou janela."""
    t = normalizar_texto(texto)
    if not t or texto_social_curto(t):
        return False
    if any(token in t for token in [
        "em foco", "na frente", "pra frente", "para frente",
        "tela cheia", "fullscreen", "maximiza", "maximizar",
        "abre ", "abrir ", "fecha ", "fechar ",
        "steam", "opera", "chrome", "edge", "vscode", "vs code",
        "visual studio code",
    ]):
        return False
    padroes = [
        r"^(deixa para la|deixa pra la|deixa quieto|deixa isso)$",
        r"^(esquece|cancela|cancelar)$",
        r"^(para com isso|para ai|pode parar)$",
        r"^(nao quero mais|quero mais nao)$",
        r"^(desiste|abandona isso)$",
        r"^ta\s+deixa\s+pra\s+la$",
    ]
    return any(re.fullmatch(padrao, t) for padrao in padroes)


class PorteiroAcoesRuntime:
    """Liga o porteiro puro ao estado compartilhado sem executar habilidades."""

    def __init__(
        self,
        *,
        playlist_state_getter: Callable[[], Dict[str, Any]],
        estado_runtime_getter: Callable[[], Any],
    ) -> None:
        self.playlist_state_getter = playlist_state_getter
        self.estado_runtime_getter = estado_runtime_getter

    def _estado(self) -> Any:
        return self.estado_runtime_getter()

    def texto_cancela_acao_agora(self, texto: str) -> bool:
        return texto_cancela_acao_agora(texto)

    def bloquear_playlist_temporariamente(self, segundos: float = 600.0) -> None:
        estado = self._estado()
        estado.atualizar(
            "continuidades",
            atualizar_continuidades,
            playlist_sugestao_pendente=None,
        )
        estado.substituir(
            "musical",
            bloquear_playlist_temporariamente(estado.musical, segundos),
        )

    def playlist_bloqueada_agora(self) -> bool:
        return playlist_bloqueada_agora(self._estado().musical)

    def contexto(self) -> Dict[str, Any]:
        estado = self._estado()
        playlist_state = self.playlist_state_getter() or {}
        return montar_contexto_porteiro_acoes(
            playlist_bloqueada=self.playlist_bloqueada_agora(),
            playlist_ativa=bool(str(playlist_state.get("name") or "").strip()),
            auto_next_playlist=bool(str(playlist_state.get("name") or "").strip()),
            ultima_playlist=str(
                estado.obter("musical", "ultima_playlist", "") or ""
            ).strip(),
            mente_integrada_estado=estado.mental,
            messages=estado.obter("memoria_conversa", "messages", []),
        )

    def autorizar_acao_pratica(
        self,
        acao: str,
        texto: str = "",
        *,
        confirmado: bool = False,
        origem: str = "",
    ) -> Dict[str, Any]:
        return autorizar_acao_pratica(
            acao,
            texto,
            self.contexto(),
            confirmado=confirmado,
            origem=origem,
        )

    def autonomia_permite_execucao_musical(
        self,
        intent: str,
        texto: str,
        *,
        confirmado: bool = False,
    ) -> bool:
        return bool(
            self.autorizar_acao_pratica(
                intent,
                texto,
                confirmado=confirmado,
            ).get("permitido")
        )


def criar_porteiro_acoes_runtime(**kwargs: Any) -> PorteiroAcoesRuntime:
    return PorteiroAcoesRuntime(**kwargs)


def texto_pede_playlist_explicitamente(texto: str) -> bool:
    t = normalizar_texto(texto)
    verbos = [
        "toca", "toque", "tocar", "coloca", "coloque", "colocar",
        "abre", "abra", "abrir", "ouvir", "escuta", "escute", "escutar",
        "pode playlist", "volta playlist",
    ]
    if "playlist" in t:
        return any(v in t for v in verbos)
    return bool(re.match(
        r"^\s*(?:(?:pode|poderia|consegue|conseguiria)\s+)?"
        r"(?:toca|toque|tocar|coloca|coloque|colocar|abre|abra|abrir|"
        r"ouvir|escuta|escute|escutar)\b\s+.+",
        t,
    ))


def texto_pede_musica_explicitamente(texto: str) -> bool:
    t = normalizar_texto(texto)
    if not t:
        return False
    verbos = [
        "toca", "toque", "tocar", "coloca", "coloque", "colocar",
        "bota", "botar", "poe", "abre", "abra", "abrir", "ouvir",
        "escuta", "escute", "escutar", "da play",
        "procura", "pesquisa", "busca",
    ]
    termos = ["musica", "som", "playlist", "youtube", "faixa", "cancao"]
    if any(v in t for v in verbos) and any(m in t for m in termos):
        return True
    if texto_pede_playlist_explicitamente(t):
        return True
    return bool(re.match(
        r"^\s*(?:(?:pode|poderia|consegue|conseguiria)\s+)?"
        r"(?:toca|toque|tocar|coloca|coloque|colocar|bota|botar|poe|"
        r"escuta|escute|escutar)\b\s+.+",
        t,
    ))


def texto_pede_repeticao_curta(texto: str) -> bool:
    t = normalizar_texto(texto).strip(" .,!?:;")
    if not t:
        return False
    if len(t.split()) > 6:
        return False
    return bool(re.fullmatch(
        r"(?:(?:tenta|tente|faz|faca|vai)\s+)?(?:de\s+novo|novamente|"
        r"outra\s+vez|mais\s+uma\s+vez)|tenta\s+outra\s+vez",
        t,
    ))


def _ultimas_mensagens_usuario(mensagens: Iterable[Any], limite: int = 4) -> list[str]:
    users: list[str] = []
    try:
        for msg in list(mensagens or [])[-12:]:
            if isinstance(msg, dict) and msg.get("role") == "user":
                conteudo = str(msg.get("content") or "").strip()
                if conteudo:
                    users.append(conteudo)
    except Exception:
        return []
    return users[-limite:]


def _ultima_intencao_contextual(contexto: Dict[str, Any]) -> str:
    mente = contexto.get("mente") or {}
    if isinstance(mente, dict):
        return str(mente.get("ultima_intencao") or "").strip().upper()
    return ""


def _ultima_habilidade_contextual(contexto: Dict[str, Any]) -> str:
    mente = contexto.get("mente") or {}
    if isinstance(mente, dict):
        return str(mente.get("ultima_habilidade") or "").strip().lower()
    return ""


def _continua_pedido_musical_recente(texto: str, contexto: Dict[str, Any]) -> bool:
    if not texto_pede_repeticao_curta(texto):
        return False
    ultima_intencao = _ultima_intencao_contextual(contexto)
    ultima_habilidade = _ultima_habilidade_contextual(contexto)
    if ultima_intencao in {"PLAYLIST_PLAY", "TOCAR_PLAYLIST", "TOCAR_PLAYLIST_SHUFFLE", "MUSIC_SEARCH"}:
        return True
    if ultima_habilidade in {"playlist", "midia"}:
        return True
    users = _ultimas_mensagens_usuario(contexto.get("messages") or [])
    if not users:
        return False
    ultimo_pedido = users[-1]
    return texto_pede_playlist_explicitamente(ultimo_pedido) or texto_pede_musica_explicitamente(ultimo_pedido)


def autorizar_acao_pratica(
    acao: str,
    texto: str = "",
    contexto: Dict[str, Any] | None = None,
    *,
    confirmado: bool = False,
    origem: str = "",
) -> Dict[str, Any]:
    """Autoriza ou bloqueia uma acao sem executar nada."""
    contexto = contexto if isinstance(contexto, dict) else {}
    acao_norm = str(acao or "").strip().lower()
    texto_atual = str(texto or "").strip()

    if confirmado:
        return {"permitido": True, "motivo": "confirmacao explicita", "categoria": "confirmado"}

    if contexto.get("playlist_bloqueada") and acao_norm in ACOES_MUSICA:
        return {"permitido": False, "motivo": "playlist bloqueada pelo usuario", "categoria": "musica"}

    if acao_norm in {"playlist_play", "tocar_playlist", "tocar_playlist_shuffle", "playlist_shuffle"}:
        permitido = texto_pede_playlist_explicitamente(texto_atual) or _continua_pedido_musical_recente(texto_atual, contexto)
        return {
            "permitido": permitido,
            "motivo": "pedido explicito de playlist" if permitido else "sem pedido explicito de playlist ou continuidade recente",
            "categoria": "playlist",
        }

    if acao_norm in {"music_search", "musica", "youtube_search"}:
        permitido = texto_pede_musica_explicitamente(texto_atual) or _continua_pedido_musical_recente(texto_atual, contexto)
        return {
            "permitido": permitido,
            "motivo": "pedido explicito de musica" if permitido else "sem pedido explicito de musica ou continuidade recente",
            "categoria": "musica",
        }

    if acao_norm == "youtube_play":
        if contexto.get("playlist_ativa") or contexto.get("auto_next_playlist"):
            return {"permitido": True, "motivo": "continuidade de playlist ativa", "categoria": "playlist"}
        permitido = (
            texto_pede_musica_explicitamente(texto_atual)
            or texto_pede_playlist_explicitamente(texto_atual)
            or _continua_pedido_musical_recente(texto_atual, contexto)
        )
        return {
            "permitido": permitido,
            "motivo": "pedido explicito de reproducao" if permitido else "sem pedido explicito de reproducao ou continuidade recente",
            "categoria": "musica",
        }

    return {"permitido": True, "motivo": "acao fora do escopo sensivel atual", "categoria": "geral"}
