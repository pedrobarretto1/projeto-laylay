"""Validadores de continuidade conversacional da Laylay."""

from __future__ import annotations

import random
import re
import time
from typing import Any, Callable, Dict, Iterable


def assunto_coerente_com_fala(
    assunto: str,
    *partes_fala: str,
    normalizar_texto: Callable[[str], str] | None = None,
) -> bool:
    """Exige ligação lexical mínima antes de rotular uma fala com um assunto."""
    normalizar = normalizar_texto if callable(normalizar_texto) else (lambda valor: str(valor or "").casefold())
    topico = re.sub(r"\s+", " ", str(normalizar(assunto) or "")).strip()
    fala = re.sub(r"\s+", " ", str(normalizar(" ".join(map(str, partes_fala))) or "")).strip()
    if not topico or not fala:
        return False
    if re.fullmatch(r"(?:nao|não)\s+\w+(?:\s+demais)?", topico):
        return False
    stop = {
        "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em",
        "um", "uma", "que", "eu", "voce", "você", "meu", "minha", "isso",
        "este", "esta", "era", "foi", "sobre", "mais", "nao", "não",
    }
    tokens_topico = {t for t in re.findall(r"[a-z0-9à-ÿ]+", topico) if len(t) >= 3 and t not in stop}
    tokens_fala = {t for t in re.findall(r"[a-z0-9à-ÿ]+", fala) if len(t) >= 3 and t not in stop}
    if not tokens_topico:
        return False
    return bool(tokens_topico & tokens_fala or topico in fala)


def _texto_e_resposta_sem_topico(texto_normalizado: str) -> bool:
    """Respostas pragmáticas curtas não representam um assunto de conversa."""
    tokens = str(texto_normalizado or "").split()
    if not tokens or len(tokens) > 5:
        return False
    conjunto = set(tokens)
    confirmacoes = {
        "sim", "quero", "pode", "claro", "aham", "uhum", "isso", "mesmo",
        "bora", "vai", "manda", "fechado", "ok", "certo", "beleza",
    }
    recusas = {
        "nao", "não", "quero", "mais", "deixa", "pra", "para", "la", "lá",
        "esquece", "cancela", "ele", "ela", "isso", "agora",
    }
    if re.fullmatch(
        r"(?:pode|podia|vamos|vou|quero)\s+(?:escolher|escolhe|colocar|tocar|ouvir|ver|fazer)(?:\s+(?:sim|entao|então|isso))?",
        str(texto_normalizado or "").strip(),
    ):
        return True
    return bool(conjunto and (conjunto <= confirmacoes or conjunto <= recusas))


def topico_memoria_valido(topico: str, normalizar_texto_curto: Callable[[str], str]) -> bool:
    t = normalizar_texto_curto(topico)
    if not t:
        return False
    if _texto_e_resposta_sem_topico(t):
        return False
    genericos = {
        "playlist", "musica", "música", "youtube", "netflix", "ia", "pc",
        "conversa", "chat", "hora", "hoje", "agora", "isso", "essa", "esse",
    }
    if t in genericos:
        return False
    if len(re.findall(r"[a-z0-9_-]{3,}", t)) <= 1 and t not in {
        "anime", "manga", "filme", "serie", "jogo", "trabalho", "praia", "rock", "metal",
    }:
        return False
    return True


def extrair_topico_conversa(texto: str, topico_anterior: str = "", *, normalizar_texto_curto: Callable[[str], str]) -> str:
    """Extrai um tema curto para manter a memória de conversa viva."""
    t = normalizar_texto_curto(texto)
    if not t:
        return str(topico_anterior or "").strip()
    if _texto_e_resposta_sem_topico(t):
        anterior = str(topico_anterior or "").strip()
        return anterior if topico_memoria_valido(anterior, normalizar_texto_curto) else ""

    if any(p in t for p in [
        "homem aranha", "spider man", "spiderman", "peter parker", "marvel", "dc",
        "anime", "manga", "filme", "serie", "série", "jogo", "games", "gaming",
        "trabalho", "pc", "ia", "inteligencia artificial", "inteligência artificial",
        "musica", "música", "playlist", "youtube", "netflix", "homem-aranha",
    ]):
        for tema in [
            "inteligencia artificial", "inteligência artificial", "homem aranha",
            "peter parker", "marvel", "anime", "manga", "filme", "serie",
            "jogo", "trabalho", "música", "youtube", "netflix", "pc", "ia",
        ]:
            if re.search(rf"(?<![a-z0-9à-ÿ]){re.escape(tema)}(?![a-z0-9à-ÿ])", t):
                return tema

    if any(p in t for p in ["ele", "ela", "isso", "fato", "verdade", "kkk", "haha", "rs", "boa", "verdade"]):
        return str(topico_anterior or "").strip()

    if any(p in t for p in ["playlist", "musica", "música", "youtube", "netflix", "ia", "pc"]):
        if len(re.findall(r"[a-z0-9_-]{3,}", t)) <= 2:
            return str(topico_anterior or "").strip()

    stop = {
        "voce", "você", "gosta", "curte", "acha", "pensa", "prefere", "me", "disso",
        "daquilo", "sobre", "mais", "muito", "bem", "tipo", "qual", "como", "porque",
        "pq", "pra", "para", "que", "isso", "essa", "esse", "aquela", "aquele",
        "hoje", "ontem", "agora", "aqui", "ali", "pra", "pro", "vai", "ser", "tem",
        "tenho", "tá", "ta", "bom", "ok", "certo", "verdade", "fato",
    }
    tokens = [tok for tok in re.findall(r"[a-z0-9_-]{3,}", t) if tok not in stop]
    if not tokens:
        return str(topico_anterior or "").strip()
    topico = " ".join(tokens[:3]).strip()
    if len(topico) < 3:
        return str(topico_anterior or "").strip()
    return topico


def mudanca_clara_de_topico(
    texto_usuario: str,
    topico_anterior: str,
    topico_novo: str,
    *,
    normalizar_texto_curto: Callable[[str], str],
) -> bool:
    """Distingue assunto novo de uma continuação curta ou pronominal."""
    anterior = str(topico_anterior or "").strip()
    novo = str(topico_novo or "").strip()
    if not anterior or not novo:
        return False
    if not topico_memoria_valido(anterior, normalizar_texto_curto):
        return True
    if anterior.casefold() == novo.casefold():
        return False
    t = normalizar_texto_curto(texto_usuario)
    if _texto_e_resposta_sem_topico(t):
        return False
    if re.match(r"^(?:e|mas|entao|então)?\s*(?:ele|ela|isso|esse|essa|aquilo|de novo)\b", t):
        return False
    return not assunto_coerente_com_fala(
        anterior,
        texto_usuario,
        normalizar_texto=normalizar_texto_curto,
    )


def detectar_comentario_resultado_operacional(
    texto: str,
    estado_mental: Dict[str, Any] | None,
    *,
    agora: float | None = None,
    ttl_s: float = 240.0,
) -> Dict[str, Any] | None:
    """Liga uma reação natural ao resultado operacional mais recente.

    A função só reconhece comentários; pedidos explícitos continuam seguindo
    para os roteadores de comando e nunca são executados por esta camada.
    """
    bruto = re.sub(r"\s+", " ", str(texto or "")).strip()
    t = bruto.casefold()
    mente = dict(estado_mental or {})
    intent = str(mente.get("ultima_acao_intent") or "").strip().upper()
    if not bruto or not intent:
        return None
    ts = float(mente.get("ultima_acao_ts") or mente.get("foco_operacional_ts") or mente.get("ts") or 0.0)
    instante = float(agora if agora is not None else time.time())
    if ts <= 0.0 or instante - ts > float(ttl_s):
        return None
    if re.match(
        r"^(?:por favor\s+)?(?:liga|ligue|desliga|desligue|deixa|deixe|coloca|"
        r"coloque|muda|mude|ajusta|ajuste|abre|abra|fecha|feche|cria|crie|apaga|apague)\b",
        t,
    ):
        return None
    pergunta_autoria = bool(re.search(
        r"^(?:(?:mas|ent[aã]o)\s+)?(?:por\s+que|porque)\s+(?:voce|você)\s+"
        r"(?:colocou|abriu|fechou|mudou|ligou|desligou|criou|apagou|fez)\b",
        t,
    ))
    if pergunta_autoria:
        params = dict(mente.get("ultima_acao_params") or {})
        return {
            "intent": intent,
            "alvo": str(
                mente.get("ultima_acao_alvo")
                or params.get("alvo")
                or params.get("query")
                or "a ação"
            ).strip(),
            "params": params,
            "texto": bruto,
            "tipo": "questiona_autoria",
            "status": str(mente.get("ultima_acao_status") or "").strip(),
            "executou": mente.get("ultima_acao_ok"),
            "confirmado": mente.get("ultima_acao_confirmada"),
        }
    # Uma pergunta sobre a aba que sobreviveu exige percepção atual do
    # navegador. ``ficou`` também aparece em comentários subjetivos, mas aqui
    # o substantivo observável e a forma interrogativa provam que não se trata
    # de uma reação ao alvo recém-fechado. Deixar essa consulta cair no
    # comentário genérico reciclaria justamente a aba removida.
    if re.fullmatch(
        r"(?:(?:me\s+)?(?:diz|diga|fala|fale|mostra|mostre)\s+)?"
        r"(?:qual|que)\s+(?:(?:e|é)\s+)?(?:a\s+)?aba\s+"
        r"(?:(?:que\s+)?(?:esta|está|ta|tá)|ficou)\s+aberta[.!?]*",
        t,
    ):
        return None
    sinais = (
        "parece", "ficou", "saiu", "funcionou", "não funcionou", "nao funcionou",
        "deu certo", "não deu", "nao deu", "estranho", "errado", "melhor", "pior",
        "puxou", "isso aí", "isso ai", "resultado",
    )
    if not any(sinal in t for sinal in sinais):
        return None

    params = dict(mente.get("ultima_acao_params") or {})
    alvo = str(mente.get("ultima_acao_alvo") or params.get("alvo") or "o resultado").strip()
    comentario: Dict[str, Any] = {
        "intent": intent,
        "alvo": alvo,
        "params": params,
        "texto": bruto,
        "tipo": "comentario_resultado",
    }
    if intent == "IOT_CONTROL" and str(params.get("acao") or "").lower() == "ajustar_cor":
        cores = re.findall(
            r"\b(?:rosa|roxo|violeta|vermelho|vinho|bord[oô]|azul|verde|amarelo|laranja|branco)\b",
            t,
        )
        comentario.update({
            "tipo": "aparencia_cor",
            "cor_pedida": str(params.get("cor") or "").strip(),
            "cor_percebida": cores[-1] if cores else "",
        })
    return comentario


def atualizar_memoria_topicos(
    *,
    texto_usuario: str,
    topicos_recentes: list,
    ultimo_topico: str,
    normalizar_texto_curto: Callable[[str], str],
    limite: int = 8,
) -> tuple[list, str, float]:
    """Atualiza a memória curta de tópicos recentes."""
    texto_base = str(texto_usuario or "").strip()
    topico = extrair_topico_conversa(
        texto_base,
        ultimo_topico,
        normalizar_texto_curto=normalizar_texto_curto,
    )
    if not topico:
        return list(topicos_recentes or []), str(ultimo_topico or "").strip(), 0.0

    agora = time.time()
    recentes = [t for t in list(topicos_recentes or []) if str(t).strip().lower() != topico.lower()]
    recentes.append(topico)
    if len(recentes) > limite:
        recentes = recentes[-limite:]
    return recentes, topico, agora


def texto_responde_pergunta_aberta(
    texto_usuario: str,
    *,
    pergunta_aberta: dict | None,
    normalizar_texto_curto: Callable[[str], str],
    texto_parece_resposta_curta_a_pergunta: Callable[[str, Callable[[str], str]], bool],
    bloqueadores: Iterable[Callable[[str], object]] = (),
) -> bool:
    """Decide se a fala atual responde uma pergunta recente em vez de iniciar comando."""
    if not pergunta_aberta:
        return False

    t = str(texto_usuario or "").strip()
    if not t:
        return False

    for bloqueador in bloqueadores or ():
        if not callable(bloqueador):
            continue
        try:
            if bloqueador(t):
                return False
        except Exception:
            continue

    try:
        return bool(texto_parece_resposta_curta_a_pergunta(t, normalizar_texto_curto))
    except Exception:
        return False


def resolver_pergunta_curta_contextual_intencao(
    texto_usuario: str,
    *,
    normalizar_texto_curto: Callable[[str], str],
    contexto_recente_indica_email: Callable[[], bool] | None = None,
) -> dict | None:
    """Converte respostas curtas dependentes do contexto em intencoes seguras."""
    try:
        t = str(normalizar_texto_curto(texto_usuario) or "").strip()
    except Exception:
        t = str(texto_usuario or "").strip().lower()
    if not t or len(t.split()) > 10:
        return None

    pergunta_email = any(p in t for p in [
        "o que eles falam",
        "o que eles me falam",
        "o que os emails falam",
        "o que falam",
        "me fala deles",
        "fala deles",
        "pode ler",
        "pode ver",
        "le eles",
        "lê eles",
        "ler eles",
    ])
    if pergunta_email and callable(contexto_recente_indica_email):
        try:
            if contexto_recente_indica_email():
                return {"intent": "EMAIL_READ", "params": {}}
        except Exception:
            return None

    return None


def responder_pergunta_aberta(
    texto_usuario: str,
    *,
    pergunta_aberta: dict | None,
    foco_vivo: dict | None = None,
    normalizar_texto_curto: Callable[[str], str],
    responder_conversa_curta_por_tipo: Callable[[str, str], str] | None = None,
    ajustar_fala_por_horario: Callable[[str, str], str] | None = None,
) -> str:
    """Gera uma resposta coerente para a pendencia de pergunta aberta."""
    pergunta = dict(pergunta_aberta or {})
    pergunta_txt = str(pergunta.get("pergunta") or "").strip()
    topico = str(pergunta.get("topico") or "").strip()
    tipo_pergunta = str(pergunta.get("tipo") or "").strip().lower()
    try:
        t = str(normalizar_texto_curto(texto_usuario) or "").strip()
    except Exception:
        t = str(texto_usuario or "").strip().lower()

    def _ajustar(fala: str) -> str:
        if callable(ajustar_fala_por_horario):
            try:
                return str(ajustar_fala_por_horario(fala, texto_usuario) or fala)
            except Exception:
                pass
        return fala

    proposito = str(pergunta.get("proposito") or "").strip().lower()
    if any(p in t for p in ["trocar de assunto", "outro assunto", "mudar de assunto", "vamos trocar"]):
        return _ajustar("Beleza. Fechamos esse fio e você pode puxar o próximo assunto.")
    if any(p in t for p in ["aprofundar", "continuar nesse", "seguir nesse", "vamos continuar"]):
        assunto = topico or "esse assunto"
        return _ajustar(f"Fechado. Continuamos em {assunto}, sem trocar o fio.")
    negou_curto = bool(re.search(
        r"\b(?:nao|não)\b|\b(?:quero|pode|melhor)\s+(?:nao|não)\b",
        t,
    ))
    confirmou_curto = not negou_curto and bool(
        set(t.split()).intersection({"sim", "quero", "pode", "claro", "bora", "manda", "vai"})
        or t in {"isso", "isso mesmo", "pode ser", "aham", "uhum", "fechado"}
    )
    if proposito == "escolha" and confirmou_curto:
        return _ajustar("Quero, mas você precisa escolher qual dos dois. Me diz o nome e eu sigo nele.")
    if proposito == "confirmacao_musical" and confirmou_curto:
        return _ajustar("Fechado. Me diz o nome da música para eu não tocar a faixa errada.")
    if proposito == "dia_usuario":
        dia_quieto = bool(
            re.search(r"\b(?:nao|não)\s+(?:tem|teve)\s+(?:nada|anda)\s+(?:demais|de\s+mais)\b", t)
            or any(p in t for p in ["nada demais", "nada de mais", "nada especial", "foi normal", "dia normal"])
        )
        if dia_quieto:
            return _ajustar(random.choice([
                "Então foi um dia quieto, sem grande acontecimento. Às vezes isso é até bom; quer deixar o momento mais interessante comigo?",
                "Nada muito fora da curva hoje, então. Quer que a gente invente alguma coisa leve agora?",
                "Dia comum, peguei. Não vou forçar uma história onde não teve; mas ainda dá pra melhorar o resto do dia.",
            ]))
        return _ajustar(random.choice([
            "Entendi. E qual pedacinho do dia ficou mais na cabeça, mesmo que tenha sido pequeno?",
            "Peguei. Teve alguma coisinha boa ou foi tudo bem no automático?",
            "Tá. Se quiser me contar uma parte só, eu acompanho sem transformar isso num interrogatório.",
        ]))

    # Respostas de bem-estar devem ser resolvidas antes de confirmacoes. Assim
    # "estou bem sim" nao vira um aceite generico por conter a palavra "sim".
    if tipo_pergunta == "bem_estar" and any(p in t for p in ["bem", "de boa", "tranquilo", "tranquila", "suave", "otimo", "ótimo", "legal", "feliz"]):
        return _ajustar(random.choice([
            "Que bom. Aí meu circuito até respira mais leve.",
            "Aí sim, gosto de te ouvir assim.",
            "Bom saber. Então seguimos com a energia um pouco mais bonita.",
        ]))

    if tipo_pergunta == "bem_estar" and any(p in t for p in ["mal", "cansado", "cansada", "triste", "mais ou menos", "indo"]):
        return _ajustar(random.choice([
            "Entendi. Então eu baixo um pouco o ritmo e fico contigo sem apertar.",
            "Pego o clima. Se quiser, a gente vai mais devagar agora.",
            "Tá, senti esse peso aí. Posso ficar no modo companhia, sem te cobrar nada.",
        ]))

    if not negou_curto and any(p in t for p in ["sim", "pode", "quero", "bora", "vai", "manda", "claro", "aham", "uhum", "isso", "isso mesmo", "é sim", "e sim", "pode ser"]):
        foco = dict(foco_vivo or {})
        foco_tipo = str(foco.get("tipo") or "").lower()
        foco_topico = str(foco.get("topico") or foco.get("alvo") or topico or "").strip()
        if foco_topico.lower() in {"", "conversa", "chat", "ia", "opinion", "opiniao", "opinião"} and topico:
            foco_topico = topico
        if foco_tipo in {"opiniao", "opinião", "conversa"} and foco_topico and callable(responder_conversa_curta_por_tipo):
            try:
                return str(responder_conversa_curta_por_tipo("OPINION", f"o que voce acha de {foco_topico}?") or "").strip()
            except Exception:
                pass
        if topico:
            return _ajustar(random.choice([
                f"Fechado. Então seguimos por {topico}.",
                f"Beleza, peguei: é {topico}. Vou nessa linha.",
                f"Aí sim. Continuo por {topico}, sem largar o fio.",
            ]))
        return _ajustar(random.choice([
            "Fechado. Peguei tua resposta e sigo nesse caminho.",
            "Beleza, então vamos por aí.",
            "Tá, entendi o sim. Vou continuar nessa linha.",
        ]))

    if negou_curto:
        pergunta_norm = pergunta_txt.casefold()
        if re.search(r"\b(?:abra|abrir|abro|abre)\b", pergunta_norm):
            return _ajustar(random.choice([
                "Beleza, não abro.",
                "Tranquilo, deixo fechado.",
                "Tá, não mexo nisso.",
            ]))
        return _ajustar(random.choice([
            "Tranquilo, deixo isso de lado então.",
            "Beleza, sem forçar. Guardei a ideia no bolso.",
            "Tá, não mexo nisso agora.",
        ]))

    if any(p in t for p in ["bem", "de boa", "tranquilo", "tranquila", "suave", "otimo", "ótimo", "legal"]):
        return _ajustar(random.choice([
            "Que bom. Aí meu circuito até respira mais leve.",
            "Aí sim, gosto de te ouvir assim.",
            "Bom saber. Então seguimos com a energia um pouco mais bonita.",
        ]))

    if any(p in t for p in ["mal", "cansado", "cansada", "triste", "mais ou menos", "indo"]):
        return _ajustar(random.choice([
            "Entendi. Então eu baixo um pouco o ritmo e fico contigo sem apertar.",
            "Pego o clima. Se quiser, a gente vai mais devagar agora.",
            "Tá, senti esse peso aí. Posso ficar no modo companhia, sem te cobrar nada.",
        ]))

    if pergunta_txt:
        return _ajustar("Entendi o que você quis dizer e vou manter isso neste assunto.")

    return _ajustar("Entendi. Vou seguir por esse fio.")
