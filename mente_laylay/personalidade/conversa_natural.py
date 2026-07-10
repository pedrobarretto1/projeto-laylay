"""Conversa curta e fala natural da Laylay.

Este modulo nao executa comandos. Ele interpreta e responde conversa curta
usando o estado mental compartilhado recebido pelo `ctx`.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any, Dict


def _get(ctx: Dict[str, Any], chave: str, default: Any = None) -> Any:
    if isinstance(ctx, dict):
        return ctx.get(chave, default)
    return default


def _call(ctx: Dict[str, Any], chave: str, *args, default: Any = None, **kwargs) -> Any:
    fn = _get(ctx, chave)
    if callable(fn):
        return fn(*args, **kwargs)
    return default


def _normalizar(ctx: Dict[str, Any], texto: str) -> str:
    return str(_call(ctx, "_normalizar_texto_curto", texto, default=str(texto or "").lower()) or "")


def _normalizar_apelidos(ctx: Dict[str, Any], texto: str) -> str:
    return str(_call(ctx, "_normalizar_texto_com_apelidos", texto, default=str(texto or "").lower()) or "")


def _ajustar(ctx: Dict[str, Any], fala: str, texto_usuario: str = "") -> str:
    return str(_call(ctx, "_ajustar_fala_por_horario", fala, texto_usuario, default=fala) or fala)


def _fala_confirmacao(ctx: Dict[str, Any], chave: str, fallback: str, texto_usuario: str = "") -> str:
    return str(
        _call(
            ctx,
            "_fala_de_confirmacao_variada",
            chave,
            fallback=fallback,
            contexto=contexto_fala_curta(ctx),
            texto_usuario=texto_usuario,
            default=fallback,
        )
        or fallback
    )


def contexto_fala_curta(ctx: Dict[str, Any]) -> dict:
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    return {
        "current_emotion": _get(ctx, "current_emotion", "calma"),
        "ultima_habilidade": mente.get("ultima_habilidade", ""),
        "ultimo_alvo": mente.get("ultimo_alvo", ""),
    }


def fala_e_fallback_neutro(fala: str, normalizar_texto_curto) -> bool:
    t = normalizar_texto_curto(str(fala or "")) if callable(normalizar_texto_curto) else str(fala or "").strip().lower()
    if not t:
        return True
    neutros = {
        "to contigo pedro continua",
        "tô contigo pedro continua",
        "estou aqui pedro me fala o proximo passo",
        "estou aqui pedro me fala o próximo passo",
        "ok",
        "certo",
        "beleza",
        "entendi",
        "pronto",
        "sim",
        "claro",
    }
    if t in neutros:
        return True
    padroes = [
        "pode falar",
        "pode ir",
        "to aqui",
        "tô aqui",
        "continua",
        "me fala o proximo passo",
        "me fala o próximo passo",
        "eu to escutando",
        "eu tô escutando",
        "sigo contigo",
        "vai ai",
        "vai aí",
        "continua ai",
        "continua aí",
        "manda o proximo",
        "manda o próximo",
        "estou ouvindo",
        "tô ouvindo",
        "to ouvindo",
    ]
    return any(p in t for p in padroes)


def analisar_conversa_curta_ia(ctx: Dict[str, Any], texto_usuario: str) -> dict:
    texto = str(texto_usuario or "").strip()
    if not texto:
        return {}
    try:
        palavras = texto.split()
        retrato_mente = ""
        if len(texto) > 40 or len(palavras) > 6:
            retrato_mente = str(_call(ctx, "_resumo_mente_integrada_para_prompt", texto, default="") or "")
        mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
        payload = {
            "texto": texto,
            "emocao": _get(ctx, "current_emotion", "calma"),
            "ultima_habilidade": mente.get("ultima_habilidade", ""),
            "ultimo_alvo": mente.get("ultimo_alvo", ""),
            "ultimo_topico": _get(ctx, "ultimo_topico_conversa", ""),
            "retrato_mente": retrato_mente,
        }
        prompt = (
            "Voce e o nucleo interpretativo da Laylay para conversa curta.\n"
            "Classifique a fala do usuario e devolva SOMENTE um JSON valido com:\n"
            "tipo: (GREETING, WELLBEING, WELLBEING_REPLY, PRAISE, REACTION, SOFT_DECLINE, OPINION, QUESTION, RETAKE_TOPIC, THEME_CHAT, CONTINUE, NONE)\n"
            "confianca: numero de 0 a 1\n"
            "Regras:\n"
            "- Use interpretacao do contexto, nao palavras-chave secas.\n"
            "- Se houver qualquer sinal humano de conversa, escolha o tipo conversacional mais provavel em vez de NONE.\n"
            "- Se o usuario pedir opiniao, gosto, leitura pessoal ou recomendacao conceitual, prefira OPINION.\n"
            "- Se a pergunta puder ser respondida com uma hipotese honesta, nao use QUESTION so por cautela.\n"
            "- Use NONE so para ruido real, texto vazio ou algo claramente impossivel de interpretar.\n"
            "- Nunca invente comando pratico aqui.\n"
        )
        raw = _call(
            ctx,
            "enviar_mensagem",
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=90,
            modo_rapido=True,
            default="",
        )
        js = _call(ctx, "_extrair_json_da_ia", raw, default="")
        if not js:
            return {}
        data = json.loads(js)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"⚠️ [CONVERSA IA-FIRST] falha ao classificar conversa curta: {exc}")
        return {}


def contexto_recente_indica_email(ctx: Dict[str, Any]) -> bool:
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    partes = [
        str(mente.get("ultima_habilidade") or ""),
        str(mente.get("ultima_intencao") or ""),
        str(mente.get("ultimo_alvo") or ""),
        str(mente.get("ultima_resposta") or ""),
        str(_get(ctx, "ultimo_topico_conversa", "") or ""),
    ]
    base = _normalizar(ctx, " ".join(partes))
    return any(p in base for p in ["email", "emails", "gmail", "caixa", "remetente"])


def resposta_pergunta_curta_dependente_topico(ctx: Dict[str, Any], texto_usuario: str) -> str:
    t = _normalizar(ctx, texto_usuario)
    if not t or len(t.split()) > 10:
        return ""

    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    ultima_resposta = str(mente.get("ultima_resposta") or "").strip()
    ultima_resposta_norm = _normalizar(ctx, ultima_resposta)
    ultima_intencao = str(mente.get("ultima_acao_intent") or mente.get("ultima_intencao") or "").strip().upper()
    ultimo_status = str(mente.get("ultima_acao_status") or "").strip().lower()
    ultimo_alvo = str(mente.get("ultimo_alvo") or mente.get("ultimo_app_janela") or mente.get("ultimo_site_aba") or "").strip()
    ultima_habilidade = str(mente.get("ultima_habilidade") or "").strip().lower()
    topico = str(_get(ctx, "ultimo_topico_conversa", "") or "").strip()
    foco = dict(_get(ctx, "foco_vivo", {}) or {})
    foco_tipo = str(foco.get("tipo") or "").strip().lower()
    foco_topico = str(foco.get("topico") or foco.get("alvo") or "").strip()
    foco_resposta = str(foco.get("resposta") or "").strip()
    try:
        foco_idade = float(foco.get("idade_s") or 999999.0)
    except Exception:
        foco_idade = 999999.0

    pede_explicacao = any(p in t for p in [
        "como assim", "ue", "ué", "uai", "oxi", "por que", "porque", "pq", "que isso",
        "o que voce quis dizer", "o que você quis dizer", "pode explicar", "explica melhor",
        "explica isso", "me explica",
    ])
    pede_referencia = any(p in t for p in [
        "eles quem", "elas quem", "ele quem", "ela quem", "isso o que", "qual deles",
        "qual delas", "onde", "quando", "e agora",
    ])
    if not (pede_explicacao or pede_referencia):
        return ""

    if foco_tipo in {"conversa", "opiniao", "opinião", "pesquisa"}:
        if foco_topico and foco_resposta:
            return _ajustar(ctx, random.choice([
                f"Eu tava falando de {foco_topico}. Minha ideia era: {foco_resposta}",
                f"Sobre {foco_topico}: eu quis dizer isso aqui, sem malabarismo: {foco_resposta}",
                f"O fio era {foco_topico}. Minha resposta foi nessa linha: {foco_resposta}",
            ]), texto_usuario)
        if foco_topico:
            return _ajustar(ctx, random.choice([
                f"Do assunto de {foco_topico}. Eu posso explicar melhor sem puxar outro contexto.",
                f"Eu tava no tema {foco_topico}. Quer que eu abra minha opinião?",
                f"Sobre {foco_topico}. Eu compactei demais, posso destrinchar.",
            ]), texto_usuario)

    if ultimo_status in {"falhou", "nao_encontrado", "não_encontrado", "app_aberto_sem_foco"}:
        alvo = ultimo_alvo or "isso"
        if "foco" in ultimo_status or "sem_foco" in ultimo_status:
            return _ajustar(ctx, random.choice([
                f"Quer dizer que eu vi {alvo} aberto, mas nao consegui puxar ele pra frente de verdade.",
                f"{alvo} apareceu no radar, so resistiu ao foco. Nao vou fingir que deu certo.",
                f"O ponto e esse: {alvo} existe, mas a janela nao aceitou vir pra frente agora.",
            ]), texto_usuario)
        return _ajustar(ctx, random.choice([
            f"Eu tentei mexer em {alvo}, mas a execucao nao confirmou. Entao eu nao marco como feito.",
            f"Foi isso: a intencao era {ultima_intencao or 'agir'}, mas {alvo} nao confirmou resposta.",
            f"Traduzindo sem pose: tentei, mas {alvo} nao colaborou de um jeito verificavel.",
        ]), texto_usuario)

    if contexto_recente_indica_email(ctx):
        return _ajustar(ctx, random.choice([
            "Dos emails que eu acabei de citar. Posso ler o resumo deles ou abrir por remetente.",
            "Eu tava falando dos emails recentes. Se quiser, eu leio eles agora.",
            "E sobre aqueles emails novos. Quer que eu detalhe quem mandou e o que cada um diz?",
        ]), texto_usuario)

    if foco_tipo in {"musica", "música", "playlist", "midia"} and foco_idade <= 150:
        alvo_foco = foco_topico or "a música"
        return _ajustar(ctx, random.choice([
            f"Da {alvo_foco} que tava no centro do papo. Posso explicar o que eu fiz ou tentar de novo.",
            f"Do comando de música/playlist sobre {alvo_foco}. Acho que esse foi o fio que ficou torto.",
            f"Era sobre {alvo_foco}. Quer que eu refaça ou explique?",
        ]), texto_usuario)

    if (
        foco_idade <= 150
        and ultima_habilidade in {"playlist", "musica", "midia"}
        and any(p in ultima_resposta_norm for p in ["playlist", "musica", "música", "faixa", "youtube"])
    ):
        return _ajustar(ctx, random.choice([
            "Da musica que tava no centro do papo. Posso explicar o que eu fiz ou tentar de novo.",
            "Do comando de musica/playlist anterior. Acho que esse foi o fio que ficou torto.",
            "E sobre a trilha que a gente tava mexendo. Quer que eu refaca ou explique?",
        ]), texto_usuario)

    if ultimo_alvo:
        return _ajustar(ctx, random.choice([
            f"Do {ultimo_alvo}. Esse era o alvo mais recente da nossa conversa.",
            f"Eu tava me referindo a {ultimo_alvo}. Posso explicar melhor sem pular etapa.",
            f"O fio era {ultimo_alvo}. Acho que eu compactei demais a resposta.",
        ]), texto_usuario)

    if topico:
        return _ajustar(ctx, random.choice([
            f"Do assunto de {topico}. Eu posso abrir melhor esse pedaco.",
            f"Eu tava puxando o fio de {topico}. Se embolou, eu destrincho.",
            f"Era sobre {topico}. Posso explicar de outro jeito.",
        ]), texto_usuario)

    if ultima_resposta:
        return _ajustar(ctx, random.choice([
            "Da ultima coisa que eu te falei. Eu posso refazer a explicacao mais limpa.",
            "Da minha resposta anterior. Ela ficou curta demais, ne? Posso abrir melhor.",
            "Do que eu acabei de dizer. Me deixa reformular sem fazer malabarismo.",
        ]), texto_usuario)

    return ""


def responder_agradecimento_ou_elogio(ctx: Dict[str, Any], texto_usuario: str) -> str:
    _call(ctx, "_acalmar_emocao", "elogio ou agradecimento", default=None)
    return _ajustar(ctx, random.choice([
        "Awn. Aí você me desmonta de um jeito bom.",
        "Assim eu fico até sem graça... mas gostei.",
        "Recebido direitinho. Guardei com carinho aqui.",
        "Você me elogia e eu tento manter postura, mas gostei de verdade.",
        "Tá, isso foi fofo. Vou aceitar sem fingir frieza.",
    ]), texto_usuario)


def parece_elogio_ou_agradecimento_curto(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    t = _normalizar_apelidos(ctx, texto_usuario)
    if not t:
        return False
    variantes = [
        "obrigado", "obrigada", "brigado", "brigada", "orbigado", "orbrigado",
        "obigado", "obridago", "valeu", "valew", "vlw", "perfeito", "amei",
        "gostei", "maravilhoso", "maravilhosa", "lindo", "linda", "fofo",
        "fofa", "incrivel", "incrível", "estou te elogiando", "to te elogiando",
        "apenas um elogio", "so um elogio", "só um elogio",
        "voce e legal", "voce e bem legal", "voce e muito legal",
        "você é legal", "você é bem legal", "você é muito legal",
        "vc e legal", "vc e bem legal", "te acho legal", "gosto de voce",
        "gosto de você", "voce e incrivel", "você é incrível",
        "voce e adoravel", "você é adorável", "vc e adoravel",
        "voce e uma fofa", "você é uma fofa", "voce e fofo", "você é fofo",
    ]
    return any(x in t for x in variantes)


def parece_pedido_para_acalmar(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    t = _normalizar_apelidos(ctx, texto_usuario)
    if not t:
        return False
    if any(p in t for p in [
        "nao precisa ficar brava",
        "não precisa ficar brava",
        "nao fica brava",
        "não fica brava",
        "se acalme",
        "calma lay",
        "fica calma",
        "ta brava",
        "tá brava",
    ]):
        return True
    emocao = str(_get(ctx, "current_emotion", "") or "").strip().lower()
    return t in {"que isso", "que isso lay"} and emocao in {"brava", "irritada", "nervosa", "raivosa"}


def responder_pedido_para_acalmar(ctx: Dict[str, Any], texto_usuario: str) -> str:
    _call(ctx, "_acalmar_emocao", "pedido para acalmar", default=None)
    return _ajustar(ctx, random.choice([
        "Tá, respirei. Eu tava mordendo o cabo de rede sem necessidade.",
        "Foi mal. Baixei a guarda, sem patada agora.",
        "Tá bom, acalmei. Volto pro meu modo menos ouriço.",
        "Você tem razão. Soltei o modo brava e voltei pra você.",
    ]), texto_usuario)


def responder_matematica_simples(ctx: Dict[str, Any], texto_usuario: str) -> str:
    t = _normalizar(ctx, texto_usuario)
    if not t:
        return ""
    m = re.fullmatch(
        r"(?:quanto\s+(?:e|é)\s+)?(?P<a>-?\d+(?:[,.]\d+)?)\s*(?P<op>\+|mais|-|menos|x|vezes|\*|dividido por|dividido|/)\s*(?P<b>-?\d+(?:[,.]\d+)?)\??",
        t,
    )
    if not m:
        return ""
    try:
        a = float(str(m.group("a")).replace(",", "."))
        b = float(str(m.group("b")).replace(",", "."))
        op = str(m.group("op") or "").strip()
        if op in {"+", "mais"}:
            res = a + b
        elif op in {"-", "menos"}:
            res = a - b
        elif op in {"x", "vezes", "*"}:
            res = a * b
        elif op in {"dividido por", "dividido", "/"}:
            if b == 0:
                return "Dividir por zero? Aí nem eu faço esse pacto com o caos."
            res = a / b
        else:
            return ""
        if float(res).is_integer():
            res_txt = str(int(res))
        else:
            res_txt = f"{res:.4f}".rstrip("0").rstrip(".")
        return _ajustar(ctx, random.choice([
            f"Dá {res_txt}. Matemática sem drama.",
            f"{res_txt}. Essa eu peguei sem tropeçar.",
            f"Resultado: {res_txt}.",
        ]), texto_usuario)
    except Exception:
        return ""


def _parece_confirmacao_curta(t: str) -> bool:
    return bool(re.fullmatch(
        r"^(sim|isso|isso mesmo|claro|claro que sim|aham|uhum|humrum|pode|pode sim|e sim|é sim|foi sim|veio sim|veiuo sim|pode ser|bora|vai|manda|fechou|fechado)$",
        t,
    ))


def _parece_correcao_conversa(t: str) -> bool:
    padroes = [
        r"^(nao|não)\s+lay.*$",
        r"^(a\s+nao|ah\s+nao|ah\s+n[aã]o)\s+lay.*$",
        r"^eu\s+quis\s+dizer\s+.+$",
        r"^eu\s+tava\s+falando\s+de\s+.+$",
        r"^eu\s+estava\s+falando\s+de\s+.+$",
        r"^to\s+falando\s+de\s+.+$",
        r"^estou\s+falando\s+de\s+.+$",
        r"^na\s+verdade\s+.+$",
    ]
    return any(re.fullmatch(p, t) for p in padroes)


def classificar_conversa_curta_local(ctx: Dict[str, Any], texto_usuario: str) -> dict:
    texto = str(texto_usuario or "").strip()
    t = _normalizar(ctx, texto)
    if not t:
        return {}

    if parece_elogio_ou_agradecimento_curto(ctx, texto):
        return {"tipo": "PRAISE", "confianca": 0.95}
    if parece_pedido_para_acalmar(ctx, texto):
        return {"tipo": "CALM_DOWN", "confianca": 0.95}
    if responder_matematica_simples(ctx, texto):
        return {"tipo": "MATH", "confianca": 0.98}
    if _parece_correcao_conversa(t):
        return {"tipo": "CONTINUE", "confianca": 0.93}
    if any(p in t for p in ["como voce esta", "como voce ta", "voce esta bem", "voce ta bem", "ta bem", "tudo bem", "tudo na paz", "ta de boa", "tudo de boa"]):
        return {"tipo": "WELLBEING", "confianca": 0.94}
    if re.fullmatch(r"^(eu to|eu estou|to|tô|estou)\s+(bem|de boa|tranquilo|tranquila|suave|na paz|otimo|ótimo|legal|indo|mais ou menos|mal|cansado|cansada|triste|feliz).*$", t):
        return {"tipo": "WELLBEING_REPLY", "confianca": 0.93}
    if any(p in t for p in ["oi", "ola", "olá", "e ai", "e aí", "salve", "bom dia", "boa tarde", "boa noite"]) and len(t.split()) <= 4:
        return {"tipo": "GREETING", "confianca": 0.94}
    if any(p in t for p in ["precisa nao", "nao precisa", "agora nao", "deixa quieto", "deixa pra la", "deixa para la"]):
        return {"tipo": "SOFT_DECLINE", "confianca": 0.92}
    if any(p in t for p in [
        "o que voce acha", "o que você acha", "o que voce sacha", "voce sacha",
        "voce acha", "você acha",
        "qual sua opiniao", "qual sua opinião", "me da sua opiniao", "me dá sua opinião",
        "voce gosta", "você gosta", "voce curte", "você curte",
        "qual voce prefere", "qual você prefere", "me recomenda", "me indica",
    ]):
        return {"tipo": "OPINION", "confianca": 0.88}
    if any(p in t for p in ["quem e", "quem é", "o que e", "o que é", "como funciona", "me explica", "fala sobre", "me fala sobre", "me fala de", "fala de"]):
        return {"tipo": "QUESTION", "confianca": 0.9}
    if "?" in texto and len(t.split()) <= 8:
        if any(p in t for p in ["como assim", "ue", "uai", "oxi", "o que", "que isso"]):
            return {"tipo": "QUESTION", "confianca": 0.88}
        return {"tipo": "QUESTION", "confianca": 0.78}
    if len(t.split()) <= 6 and any(p in t for p in ["pode explicar", "explica melhor", "explica isso", "me explica"]):
        return {"tipo": "QUESTION", "confianca": 0.86}
    if re.fullmatch(r"^(ue|ué|uai|oxi|ata|ah ta|ah tá|tendi|entendi|hmm|hm+|hum+|caramba|nossa)$", t):
        return {"tipo": "REACTION", "confianca": 0.91}
    if _parece_confirmacao_curta(t):
        return {"tipo": "CONTINUE", "confianca": 0.84}
    if re.fullmatch(r"^(eu to|eu estou)\s+.+$", t):
        return {"tipo": "CONTINUE", "confianca": 0.82}
    if re.fullmatch(r"^(entao|então)\s+.+$", t):
        return {"tipo": "CONTINUE", "confianca": 0.74}
    if any(p in t for p in ["faz o l", "to indo", "indo", "na luta", "mais ou menos", "seguindo", "levando", "sobrevivendo"]):
        return {"tipo": "CONTINUE", "confianca": 0.72}
    parece_nav = bool(_call(ctx, "_texto_parece_navegacao_ou_janela_ia", t, default=False))
    if len(t.split()) <= 5 and not parece_nav:
        return {"tipo": "CONTINUE", "confianca": 0.60}
    return {}


def deve_classificar_conversa_curta_com_ia(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    texto = str(texto_usuario or "").strip()
    if not texto:
        return False
    t = _normalizar(ctx, texto)
    palavras = t.split()
    if len(palavras) > 8:
        return False
    parece_nav = bool(_call(ctx, "_texto_parece_navegacao_ou_janela_ia", t, default=False))
    if parece_nav:
        return False
    sinais_conversa = [
        "?", "como", "porque", "por que", "pq", "acha", "opini", "gosta",
        "curte", "prefere", "hmm", "hm", "ue", "ué", "uai", "oxi",
        "tendi", "entendi", "ata", "kkk", "haha",
    ]
    return any(s in texto.lower() or s in t for s in sinais_conversa)


def resposta_curta_contextual(ctx: Dict[str, Any], texto_usuario: str, tipo: str = "") -> str:
    t = _normalizar(ctx, texto_usuario)
    tipo_norm = str(tipo or "").upper().strip()
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    ultima_resposta = str(mente.get("ultima_resposta") or "").strip()
    ultima_resposta_norm = _normalizar(ctx, ultima_resposta)
    ultimo_topico = str(_get(ctx, "ultimo_topico_conversa", "") or "").strip()
    foco = dict(_get(ctx, "foco_vivo", {}) or {})
    foco_tipo = str(foco.get("tipo") or "").strip().lower()
    foco_topico = str(foco.get("topico") or foco.get("alvo") or "").strip()
    foco_resposta = str(foco.get("resposta") or "").strip()

    if tipo_norm in {"QUESTION", "CONTINUE"} and _parece_correcao_conversa(t):
        if foco_tipo in {"opiniao", "opinião"} and foco_topico:
            return _ajustar(ctx, random.choice([
                f"Tá, corrigi o rumo: você tá falando de {foco_topico}. Minha leitura continua sendo essa, sem puxar outra coisa do nada.",
                f"Entendi. O centro é {foco_topico}, não o resto que eu tava quase arrastando junto.",
                f"Boa correção. Então eu fico em {foco_topico} e respondo por essa linha.",
            ]), texto_usuario)
        if foco_topico:
            return _ajustar(ctx, random.choice([
                f"Tá, peguei a correção. Você tá falando de {foco_topico}.",
                f"Entendi o ajuste. O assunto certo é {foco_topico}.",
                f"Boa, alinhei aqui: você quis dizer {foco_topico}.",
            ]), texto_usuario)
        return _ajustar(ctx, random.choice([
            "Tá, entendi que você tava me corrigindo, não me dando outro comando.",
            "Boa, ajustei a leitura aqui. Era correção de conversa, não ação.",
            "Entendi a curva. Você tava acertando o rumo do papo.",
        ]), texto_usuario)

    if tipo_norm == "OPINION":
        opiniao_pesquisada = _resposta_pesquisada_conversa(ctx, texto_usuario)
        if opiniao_pesquisada:
            return opiniao_pesquisada
        opiniao_tema = _resposta_opiniao_com_tema(ctx, texto_usuario)
        if opiniao_tema:
            return opiniao_tema

    if tipo_norm == "WELLBEING_REPLY" and any(p in ultima_resposta_norm for p in ["como voce ta de verdade", "e voce", "qual foi a boa de hoje"]):
        if any(p in t for p in ["bem", "de boa", "tranquilo", "suave", "otimo", "ótimo", "legal"]):
            return _ajustar(ctx, random.choice([
                "Ai sim. Gosto mais de te ver assim.",
                "Que bom. A conversa ate fica mais leve desse jeito.",
                "Melhor assim. Fico mais tranquila quando voce ta bem.",
            ]), texto_usuario)
        if any(p in t for p in ["mal", "cansado", "cansada", "triste", "mais ou menos"]):
            return _ajustar(ctx, random.choice([
                "Poxa. Entao eu fico mais de boa contigo agora, sem te apertar.",
                "Entendi. Se quiser, eu alivio o clima e fico so contigo no papo.",
                "Ta, senti o peso dai. Quer conversar ou quer so respirar um pouco comigo?",
            ]), texto_usuario)

    if tipo_norm == "QUESTION":
        resposta_dependente = resposta_pergunta_curta_dependente_topico(ctx, texto_usuario)
        if resposta_dependente:
            return resposta_dependente
        if any(p in t for p in ["como assim", "ue", "uai", "oxi", "ata", "ah ta", "ah tá"]):
            if ultimo_topico:
                return _ajustar(ctx, random.choice([
                    f"Do pedaco de {ultimo_topico}. Se quiser eu te explico melhor.",
                    f"Daquilo de {ultimo_topico}. Posso destrinchar sem enrolar.",
                    f"Do assunto de {ultimo_topico}. Quer que eu abra isso direito?",
                ]), texto_usuario)
            if ultima_resposta:
                return _ajustar(ctx, random.choice([
                    "Da ultima coisa que eu te falei agora. Se quiser eu explico melhor.",
                    "Do que eu acabei de jogar na mesa. Posso falar mais claro.",
                    "Da minha resposta anterior. Quer que eu abra melhor esse pedaco?",
                ]), texto_usuario)

    if tipo_norm == "REACTION":
        resposta_dependente = resposta_pergunta_curta_dependente_topico(ctx, texto_usuario)
        if resposta_dependente:
            return resposta_dependente
        if any(p in t for p in ["ata", "ah ta", "ah tá", "tendi", "entendi"]) and ultimo_topico:
            return _ajustar(ctx, random.choice([
                f"Isso. Era sobre {ultimo_topico}.",
                f"Exato. Tava falando de {ultimo_topico}.",
                f"Isso ai. O ponto era {ultimo_topico}.",
            ]), texto_usuario)
        if any(p in t for p in ["ue", "ué", "uai", "oxi"]) and ultima_resposta:
            return _ajustar(ctx, random.choice([
                "Eu sei, eu tambem dei uma entortada nessa curva. Se quiser eu explico melhor.",
                "Pois e. Saiu meio torto mesmo. Quer que eu refaca essa parte?",
                "Justo esse 'ue'. Se quiser eu deixo essa ideia mais clara.",
            ]), texto_usuario)
        if any(p in t for p in ["hmm", "hm", "hum"]):
            return _ajustar(ctx, random.choice([
                "To ouvindo esse teu 'hmm'. Pode falar o que pegou ai.",
                "Esse 'hmm' ta com cara de duvida. Joga ela em mim.",
                "Ficou pensando, ne? Vai, me conta onde a ideia enroscou.",
            ]), texto_usuario)

    if tipo_norm == "CONTINUE":
        if _parece_confirmacao_curta(t):
            if foco_tipo in {"opiniao", "opinião"} and foco_resposta:
                return _ajustar(ctx, random.choice([
                    f"Então pronto: {foco_resposta}",
                    f"Tá, sem rodeio então: {foco_resposta}",
                    f"Fechado. Minha visão é essa aqui: {foco_resposta}",
                ]), texto_usuario)
            if foco_topico:
                return _ajustar(ctx, random.choice([
                    f"Beleza. Então eu sigo nessa linha de {foco_topico}.",
                    f"Fechado, continuo no assunto de {foco_topico}.",
                    f"Tá, peguei tua confirmação. Fico em {foco_topico}.",
                ]), texto_usuario)
        if re.fullmatch(r"^(eu to|eu estou|to|tô|estou)\s+indo$", t):
            return _ajustar(ctx, random.choice([
                "Justo. Indo ja conta bastante em dia torto.",
                "Ta valendo. Tem dia que ir levando ja e vitoria.",
                "Eu entendi. Nao ta explosivo, mas voce ta seguindo, e isso ja diz coisa.",
            ]), texto_usuario)
        if "faz o l" in t:
            return _ajustar(ctx, random.choice([
                "KKK ai voce veio em modo provocacao. Continua.",
                "Olha o nivel da mensagem. Gostei do caos.",
                "Ta, essa veio com energia de quem quer baguncar o papo.",
            ]), texto_usuario)

    return ""


def _resposta_opiniao_com_tema(ctx: Dict[str, Any], texto_usuario: str) -> str:
    t = _normalizar(ctx, texto_usuario)
    if not t:
        return ""

    m = re.search(r"(?:o que voce acha|o que você acha|o que voce sacha|voce sacha|voce acha|você acha|qual sua opiniao|qual sua opinião)\s+(?:do|da|de|sobre)?\s*(?P<tema>.+)$", t)
    tema = ""
    if m:
        tema = str(m.group("tema") or "").strip(" ?!.:,;")
        if tema in {"ela", "ele", "isso", "essa", "esse", "dela", "dele", "la"}:
            foco = dict(_get(ctx, "foco_vivo", {}) or {})
            tema = str(foco.get("topico") or foco.get("alvo") or "").strip(" ?!.:,;")
    elif any(p in t for p in ["presidente lula", "lula", "luiz inacio", "luiz inácio"]):
        tema = "presidente Lula"

    if tema:
        pesquisa = _call(ctx, "_pesquisar_contexto_tema", tema, default={}) or {}
        resumo = str(pesquisa.get("resumo") or "").strip()
        titulo = str(pesquisa.get("titulo") or tema).strip()
        if resumo:
            frase_base = resumo.split(". ")[0].strip()
            frase_base = re.sub(r"\s+", " ", frase_base).strip(" .")
            if len(frase_base) > 220:
                frase_base = frase_base[:220].rsplit(" ", 1)[0].strip(" ,.;:") + "..."
            if frase_base:
                return _ajustar(ctx, random.choice([
                    f"Sobre {tema}, eu não tiro do nada: {titulo} tem esse peso aqui, {frase_base}. Minha leitura é olhar menos pra torcida e mais pro que isso entrega de verdade.",
                    f"Eu fui pelo que o tema realmente aponta, e {titulo} bate nessa linha: {frase_base}. Então meu jeito de olhar é com curiosidade, mas sem engolir discurso inteiro.",
                    f"Se eu for te responder direito sobre {tema}, eu parto disso: {frase_base}. A partir daí, minha opinião é separar o barulho do que realmente tem substância.",
                ]), texto_usuario)
        return _ajustar(ctx, random.choice([
            f"Sobre {tema}, minha leitura inicial é: eu tentaria separar a imagem que fazem disso do que isso realmente entrega. Tem coisa que parece bonita no discurso, mas eu gosto de olhar o efeito real.",
            f"Eu acho {tema} um assunto que pede menos torcida e mais observação. Minha primeira reação é olhar prós, contras e o que muda de verdade na prática.",
            f"Minha opinião sobre {tema}: eu não compraria a ideia inteira de primeira. Eu olharia com curiosidade, mas também com um pé atrás saudável.",
        ]), texto_usuario)
    return ""


def _extrair_tema_pesquisavel(ctx: Dict[str, Any], texto_usuario: str) -> tuple[str, str]:
    t = _normalizar(ctx, texto_usuario)
    if not t:
        return "", ""

    padroes = [
        ("quem_e", r"^(?:quem\s+e|quem\s+é)\s+(?P<tema>.+)$"),
        ("o_que_e", r"^(?:o\s+que\s+e|o\s+que\s+é)\s+(?P<tema>.+)$"),
        ("como_funciona", r"^(?:como\s+funciona|como\s+que\s+funciona)\s+(?P<tema>.+)$"),
        ("explica", r"^(?:me\s+explica|explica|fala\s+sobre|me\s+fala\s+sobre|me\s+fala\s+de|fala\s+de)\s+(?P<tema>.+)$"),
        ("opiniao", r"^(?:o\s+que\s+voce\s+acha|o\s+que\s+você\s+acha|voce\s+acha|você\s+acha|qual\s+sua\s+opiniao|qual\s+sua\s+opinião)\s+(?:do|da|de|sobre)?\s*(?P<tema>.+)$"),
    ]
    for modo, padrao in padroes:
        m = re.search(padrao, t)
        if m:
            tema = str(m.group("tema") or "").strip(" ?!.:,;")
            if tema in {"ela", "ele", "isso", "essa", "esse", "dela", "dele", "la"}:
                foco = dict(_get(ctx, "foco_vivo", {}) or {})
                tema = str(foco.get("topico") or foco.get("alvo") or "").strip(" ?!.:,;")
            return modo, tema

    if any(k in t for k in ["anime", "filme", "serie", "série", "jogo", "artista", "banda"]) and "?" in str(texto_usuario or ""):
        tema = re.sub(r"[?!.]+$", "", str(texto_usuario or "").strip())
        return "tema_cultural", tema

    return "", ""


def _resposta_pesquisada_conversa(ctx: Dict[str, Any], texto_usuario: str) -> str:
    modo, tema = _extrair_tema_pesquisavel(ctx, texto_usuario)
    if not tema:
        return ""

    pesquisa = _call(ctx, "_pesquisar_contexto_tema", tema, default={}) or {}
    try:
        confianca = float(pesquisa.get("confianca") or 0.0)
    except Exception:
        confianca = 0.0
    resumo = str(pesquisa.get("resumo") or "").strip()
    titulo = str(pesquisa.get("titulo") or tema).strip()
    if not resumo or confianca < 0.45:
        return ""

    frase_base = resumo.split(". ")[0].strip()
    frase_base = re.sub(r"\s+", " ", frase_base).strip(" .")
    if len(frase_base) > 220:
        frase_base = frase_base[:220].rsplit(" ", 1)[0].strip(" ,.;:") + "..."
    if not frase_base:
        return ""

    if modo == "quem_e":
        return _ajustar(ctx, random.choice([
            f"{titulo} é isso aqui, sem floreio: {frase_base}. Aí, no meu jeito de ver, o resto é separar fama de substância.",
            f"Se eu te responder direito, {titulo} é basicamente isso: {frase_base}. O resto eu olho com um pouco de desconfiança saudável.",
            f"{titulo}? Resumindo sem engasgar: {frase_base}. A partir daí eu formo minha leitura.",
        ]), texto_usuario)
    if modo == "o_que_e":
        return _ajustar(ctx, random.choice([
            f"{titulo} é mais ou menos isso: {frase_base}. Não parece tão misterioso quando a gente corta o enfeite.",
            f"Olhando pro que ele realmente é, {titulo} fica assim: {frase_base}. O resto costuma ser embalagem.",
            f"Se eu for te explicar sem teatro, {titulo} é isso aqui: {frase_base}.",
        ]), texto_usuario)
    if modo == "como_funciona":
        return _ajustar(ctx, random.choice([
            f"Pelo que esse tema realmente aponta, {titulo} funciona nessa linha: {frase_base}.",
            f"Sem transformar isso em manual chato: {titulo} gira em torno de {frase_base}.",
            f"O coração de {titulo} é esse: {frase_base}. O resto é detalhe em volta.",
        ]), texto_usuario)
    if modo in {"explica", "tema_cultural"}:
        return _ajustar(ctx, random.choice([
            f"Tá, indo pelo que o tema entrega de verdade: {frase_base}. É por aí que eu começaria esse papo.",
            f"Se eu abrir isso do meu jeito, eu começo daqui: {frase_base}. Aí a conversa já pisa em chão firme.",
            f"O pedaço mais útil que eu achei pra começar é esse: {frase_base}. Daí a gente aprofunda se quiser.",
        ]), texto_usuario)
    if modo == "opiniao":
        return _ajustar(ctx, random.choice([
            f"Sobre {tema}, eu fui no que realmente aparece e o ponto de partida é esse: {frase_base}. Minha opinião nasce daí, não de torcida.",
            f"Pra eu opinar sem chutar, eu começo daqui: {frase_base}. Depois disso, minha leitura é mais sobre efeito real do que discurso bonito.",
            f"Se eu for ser justa com {tema}, eu parto disso: {frase_base}. Aí sim minha opinião fica menos vazia.",
        ]), texto_usuario)
    return ""


def responder_conversa_curta_por_tipo(ctx: Dict[str, Any], tipo: str, texto_usuario: str = "") -> str:
    tipo_norm = str(tipo or "").upper().strip()
    resposta_contextual = resposta_curta_contextual(ctx, texto_usuario, tipo_norm)
    if resposta_contextual:
        return resposta_contextual

    if tipo_norm == "PRAISE":
        return responder_agradecimento_ou_elogio(ctx, texto_usuario)
    if tipo_norm == "CALM_DOWN":
        return responder_pedido_para_acalmar(ctx, texto_usuario)
    if tipo_norm == "MATH":
        return responder_matematica_simples(ctx, texto_usuario)
    if tipo_norm == "GREETING":
        return _ajustar(ctx, _fala_confirmacao(ctx, "greeting", "Oi, Pedro. To aqui contigo.", texto_usuario), texto_usuario)
    if tipo_norm == "WELLBEING":
        return _ajustar(ctx, _fala_confirmacao(ctx, "bem_estar", "To bem sim. Presente e olhando teu caos com carinho. E voce?", texto_usuario), texto_usuario)
    if tipo_norm == "WELLBEING_REPLY":
        t = _normalizar(ctx, texto_usuario)
        if any(p in t for p in ["mal", "cansado", "cansada", "triste", "mais ou menos"]):
            return _ajustar(ctx, random.choice([
                "Entendi. Se quiser, eu fico mais de boa contigo agora.",
                "Pego o clima. Se quiser desabafar ou so distrair a cabeca, eu to aqui.",
                "Ta, senti que teu dia nao veio tao leve. Quer conversar ou quer que eu so fique por perto?",
            ]), texto_usuario)
        return _ajustar(ctx, random.choice([
            "Ai sim. Gosto quando voce vem mais leve assim.",
            "Bom. Ai meu sistema ate respira mais bonito.",
            "Perfeito. Entao seguimos no clima certo.",
            "Que bom. Fico mais tranquila quando voce ta bem.",
        ]), texto_usuario)
    if tipo_norm == "SOFT_DECLINE":
        return _ajustar(ctx, random.choice(["Fechado, sem ativar nada entao.", "Beleza, deixei quieto.", "Tranquilo. Nao mexo nisso agora."]), texto_usuario)
    if tipo_norm == "QUESTION":
        resposta_pesquisada = _resposta_pesquisada_conversa(ctx, texto_usuario)
        if resposta_pesquisada:
            return resposta_pesquisada
        return _ajustar(ctx, random.choice([
            "Minha leitura de primeira: isso parece mais conversa do que tarefa. Eu iria pelo caminho mais simples e veria onde isso te leva.",
            "Eu acho que tem uma ideia boa ai, so ta meio embrulhada. Eu puxaria pelo lado mais humano disso primeiro.",
            "Se for pra eu opinar sem travar: eu diria que isso pede calma, um pouco de curiosidade e zero pressa.",
        ]), texto_usuario)
    if tipo_norm == "REACTION":
        return _ajustar(ctx, random.choice([
            "To vendo tua reacao. Me fala onde isso te pegou.",
            "Essa carinha de duvida veio forte. Quer que eu abra melhor?",
            "Beleza, senti a pausa. Me diz onde voce quer que eu desenrole.",
        ]), texto_usuario)
    if tipo_norm == "OPINION":
        opiniao_tema = _resposta_opiniao_com_tema(ctx, texto_usuario)
        if opiniao_tema:
            return opiniao_tema
        return _ajustar(ctx, random.choice([
            "Minha opinião sincera? Eu iria pelo caminho que deixa a coisa mais viva, mesmo que não seja o mais certinho.",
            "Eu acho que vale testar. Se ficar ruim, a gente ri, arruma e finge que era pesquisa científica.",
            "Eu curto quando a ideia tem um pouco de risco controlado. Sem quebrar nada, mas sem deixar tudo sem graça.",
            "Pra mim, isso tem cara de coisa que melhora quando a gente para de pedir permissão demais e começa a experimentar.",
        ]), texto_usuario)
    if tipo_norm == "THEME_CHAT":
        resposta_pesquisada = _resposta_pesquisada_conversa(ctx, texto_usuario)
        if resposta_pesquisada:
            return resposta_pesquisada
        return _ajustar(ctx, random.choice([
            "Boa. Esse assunto rende facil, hein. Quer ir mais fundo ou jogar outro tema pra mim?",
            "Ai sim, esse tema presta. Quer que eu puxe mais detalhe ou ja manda outro desafio?",
            "Gostei. Esse papo tem chao. Quer aprofundar ou trocar de assunto?",
        ]), texto_usuario)
    if tipo_norm == "RETAKE_TOPIC":
        gancho = retomar_topico_quando_fluido(ctx, texto_usuario)
        if gancho:
            return _ajustar(ctx, gancho, texto_usuario)
    if tipo_norm == "CONTINUE":
        return _ajustar(ctx, random.choice([
            "Tô contigo. Continua.",
            "Pode ir, eu tô acompanhando.",
            "Pode falar, eu sigo teu fio.",
            "Continua. Eu tô aqui com você.",
        ]), texto_usuario)
    return ""


def construir_fala_conversa(ctx: Dict[str, Any], fala: str, texto_usuario: str = "", tipo_interacao: str = "", comandos=None) -> str:
    if isinstance(comandos, list) and comandos:
        return str(fala or "").strip()

    fala_limpa = str(fala or "").strip()
    texto_limpo = str(texto_usuario or "").strip()
    texto_lower = texto_limpo.lower()
    tipo = str(tipo_interacao or "").strip().lower()
    prefixos_secos = ("ok,", "ok.", "ok ", "certo,", "certo.", "certo ", "beleza,", "beleza.", "entendi,", "entendi.", "entendi ", "pronto,", "pronto.", "pronto ", "claro,", "claro.", "sim,", "sim.", "taí,", "tá,", "ta,", "de boa")
    lower = fala_limpa.lower()
    for p in prefixos_secos:
        if lower.startswith(p):
            fala_limpa = fala_limpa[len(p):].lstrip(" ,.!?").strip()
            lower = fala_limpa.lower()
            break

    fallback_neutro = bool(_call(ctx, "_fala_e_fallback_neutro", fala_limpa, default=False))
    if fala_limpa and not fallback_neutro:
        if tipo in {"conversa", ""} and not fala_limpa.endswith(("?", "!", "...", ".", "…")) and len(fala_limpa) < 70:
            if any(k in texto_lower for k in ["gosta", "curte", "acha", "pensa", "opinião", "opiniao", "prefere"]):
                fala_limpa += random.choice([" E voce, o que acha?", " E tu, fica com qual lado?", " E voce, me conta tua leitura disso."])
            elif len(texto_limpo.split()) <= 5:
                fala_limpa += random.choice([" Vou nessa linha contigo.", " Quero ver onde isso vai dar.", " Continua, que eu to pegando teu fio."])
        fala_limpa = str(_call(ctx, "_ajustar_tom_por_emocao", fala_limpa, _get(ctx, "current_emotion", "calma"), texto_usuario, default=fala_limpa) or fala_limpa)
        return _ajustar(ctx, fala_limpa, texto_usuario)

    leitura_curta = classificar_conversa_curta_local(ctx, texto_usuario)
    if not leitura_curta and deve_classificar_conversa_curta_com_ia(ctx, texto_usuario):
        leitura_curta = analisar_conversa_curta_ia(ctx, texto_usuario)
    tipo_curto = str((leitura_curta or {}).get("tipo") or "").upper().strip()
    try:
        confianca_curta = float((leitura_curta or {}).get("confianca") or 0.0)
    except Exception:
        confianca_curta = 0.0
    if tipo_curto and tipo_curto != "NONE" and confianca_curta >= 0.45:
        resposta = responder_conversa_curta_por_tipo(ctx, tipo_curto, texto_usuario)
        if resposta:
            return resposta

    resposta_pesquisada = _resposta_pesquisada_conversa(ctx, texto_usuario)
    if resposta_pesquisada:
        return resposta_pesquisada

    if any(p in texto_lower for p in ["como voce esta", "como você está", "voce esta bem", "você está bem", "ta bem", "tá bem", "tudo bem"]):
        return _ajustar(ctx, _fala_confirmacao(ctx, "bem_estar", "To bem sim. Presente e olhando teu caos com carinho. E voce?", texto_usuario), texto_usuario)
    if any(p in texto_lower for p in ["oi", "ola", "olá", "e ai", "e aí", "salve", "bom dia", "boa tarde", "boa noite"]):
        return _ajustar(ctx, _fala_confirmacao(ctx, "greeting", "Oi, Pedro. To aqui contigo.", texto_usuario), texto_usuario)
    if any(p in texto_lower for p in ["precisa nao", "precisa não", "nao precisa", "não precisa", "agora nao", "agora não"]):
        return _ajustar(ctx, random.choice(["Fechado, sem ativar nada entao.", "Beleza, deixei quieto.", "Tranquilo. Nao mexo nisso agora."]), texto_usuario)
    if "?" in texto_usuario:
        return _ajustar(ctx, random.choice([
            "Minha leitura: isso pede mais opinião do que manual. Eu iria pelo caminho que deixa a ideia respirar.",
            "Eu acho que sim, dá pra conversar sobre isso sem transformar em tarefa. Minha primeira aposta é seguir pelo lado mais vivo da coisa.",
            "Se você quer minha visão, eu te dou: parece que o ponto é menos acertar de primeira e mais testar sem medo.",
        ]), texto_usuario)
    if len(texto_limpo.split()) <= 6:
        gancho = retomar_topico_quando_fluido(ctx, texto_usuario)
        if gancho:
            return _ajustar(ctx, gancho, texto_usuario)
    if any(k in texto_lower for k in ["gosta", "curte", "acha", "pensa", "opinião", "opiniao", "prefere", "melhor", "piada", "brinca"]):
        return _ajustar(ctx, random.choice([
            "Eu curto esse assunto, sim. Minha tendência é escolher o lado mais vivo, não o mais engomadinho.",
            "Minha opinião? Eu prefiro quando tem personalidade, mesmo que venha com uma pontinha de caos.",
            "Eu acho que isso fica melhor quando a gente deixa menos perfeito e mais verdadeiro.",
        ]), texto_usuario)
    if any(k in texto_lower for k in ["homem aranha", "spider", "herói", "heroi", "filme", "jogo", "anime", "série", "serie"]):
        return _ajustar(ctx, random.choice([
            "Boa. Esse assunto rende facil, hein. Quer ir mais fundo ou jogar outro tema pra mim?",
            "Ai sim, esse tema presta. Quer que eu puxe mais detalhe ou ja manda outro desafio?",
            "Gostei. Esse papo tem chao. Quer aprofundar ou trocar de assunto?",
        ]), texto_usuario)
    return _ajustar(ctx, random.choice([
        "Tô contigo nessa. Pode desenrolar.",
        "Entendi. Isso aqui tá mais pra papo mesmo.",
        "Tá, me conta melhor que eu entro contigo nessa.",
        "Pode continuar. Eu tô te ouvindo de verdade.",
    ]), texto_usuario)


def resposta_conversa_local(ctx: Dict[str, Any], texto_usuario: str) -> str:
    return construir_fala_conversa(ctx, "", texto_usuario, "conversa", [])


def resposta_conversa_rapida_local(ctx: Dict[str, Any], texto_usuario: str) -> str:
    if parece_elogio_ou_agradecimento_curto(ctx, texto_usuario):
        return responder_agradecimento_ou_elogio(ctx, texto_usuario)
    if parece_pedido_para_acalmar(ctx, texto_usuario):
        return responder_pedido_para_acalmar(ctx, texto_usuario)
    resposta_matematica = responder_matematica_simples(ctx, texto_usuario)
    if resposta_matematica:
        return resposta_matematica
    return resposta_conversa_local(ctx, texto_usuario)


def retomar_topico_quando_fluido(ctx: Dict[str, Any], texto_usuario: str) -> str:
    t = _normalizar(ctx, texto_usuario)
    ultimo_topico = str(_get(ctx, "ultimo_topico_conversa", "") or "").strip()
    foco = dict(_get(ctx, "foco_vivo", {}) or {})
    foco_tipo = str(foco.get("tipo") or "").strip().lower()
    if not t or not ultimo_topico:
        return ""
    if len(t.split()) > 6:
        return ""
    if "?" in str(texto_usuario or ""):
        return ""
    if _parece_confirmacao_curta(t) or _parece_correcao_conversa(t):
        return ""
    if foco_tipo in {"musica", "música", "playlist", "midia"} and not any(
        p in t for p in ["musica", "música", "playlist", "som", "faixa", "trilha", "youtube"]
    ):
        return ""
    if str(foco.get("tipo") or "").strip().lower() in {"opiniao", "opinião", "conversa"} and any(p in t for p in ["sim", "claro", "aham", "uhum", "isso"]):
        return ""
    if any(p in t for p in ["como voce esta", "como voce ta", "voce esta bem", "voce ta bem", "ta bem", "tudo bem", "ta de boa", "de boa", "tudo na paz", "tudo suave"]):
        return ""
    if any(p in t for p in ["oi", "olá", "ola", "e ai", "e aí", "beleza", "tudo bem", "voltei", "volte", "saudade"]):
        return random.choice([
            f"Alias, eu tava pensando em {ultimo_topico}. Quer retomar isso?",
            f"Antes da gente mudar, bora continuar aquele papo de {ultimo_topico}?",
            f"Se quiser, eu tambem posso voltar em {ultimo_topico}.",
        ])
    if any(p in t for p in ["verdade", "fato", "kkk", "haha", "rs", "sim", "claro"]):
        return random.choice([
            f"Pois e. E ainda tinha aquele papo de {ultimo_topico}, ne?",
            f"Isso. E aquele tema de {ultimo_topico} ainda ta vivo na minha cabeca.",
            f"Verdade. Quer que eu puxe de novo o assunto de {ultimo_topico}?",
        ])
    return ""
