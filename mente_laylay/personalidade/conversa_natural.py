"""Conversa curta e fala natural da Laylay.

Este modulo nao executa comandos. Ele interpreta e responde conversa curta
usando o estado mental compartilhado recebido pelo `ctx`.
"""

from __future__ import annotations

import json
import random
import re
import time
import unicodedata
from collections import deque
from typing import Any, Dict

from mente_laylay.personalidade.proporcao_resposta import ajustar_proporcao_resposta
from mente_laylay.personalidade.ritmo_natural import ajustar_encerramento_organico
from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional
from mente_laylay.memoria_mental.continuidade_conversa import assunto_coerente_com_fala
from mente_laylay.cognicao.conversa_sobre_capacidades import (
    resposta_conversa_sobre_capacidade,
    resposta_continuacao_capacidade_futura,
    texto_discute_capacidade_futura,
)
from mente_laylay.cognicao.interpretacao_social import analisar_ato_social


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
    # A camada com apelidos também contém as correções tipográficas seguras.
    # Usá-la primeiro evita que "tduo bem" caia no fallback antes da correção.
    com_apelidos = _call(ctx, "_normalizar_texto_com_apelidos", texto, default=None)
    if com_apelidos is not None:
        return str(com_apelidos or "")
    return str(_call(ctx, "_normalizar_texto_curto", texto, default=str(texto or "").lower()) or "")


def _normalizar_apelidos(ctx: Dict[str, Any], texto: str) -> str:
    return str(_call(ctx, "_normalizar_texto_com_apelidos", texto, default=str(texto or "").lower()) or "")


def _ajustar(ctx: Dict[str, Any], fala: str, texto_usuario: str = "") -> str:
    fala_organica = ajustar_encerramento_organico(fala, texto_usuario)
    return str(_call(ctx, "_ajustar_fala_por_horario", fala_organica, texto_usuario, default=fala_organica) or fala_organica)


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
        "emotion_level": _get(ctx, "emotion_level", mente.get("emotion_level", 1)),
        "ultima_habilidade": mente.get("ultima_habilidade", ""),
        "ultimo_alvo": mente.get("ultimo_alvo", ""),
        "ultimo_topico": _get(ctx, "ultimo_topico_conversa", mente.get("ultimo_topico", "")),
    }


def _nome_jogo_em_foco(ctx: Dict[str, Any]) -> str:
    percepcao = dict(_get(ctx, "contexto_perceptivo", {}) or {})
    jogo = dict(percepcao.get("jogo") or {})
    titulo = str(jogo.get("titulo") or "").strip()
    processo = str(jogo.get("processo") or "").strip()
    if not titulo and str(percepcao.get("assunto") or "").casefold() == "gaming":
        titulo = str(percepcao.get("title") or "").strip()
        processo = processo or str(percepcao.get("exe") or "").strip()

    if titulo:
        nome = re.split(r"\s+[—–|]\s+|\s+-\s+", titulo, maxsplit=1)[0].strip()
        if nome and nome.casefold() not in {"gaming", "jogo", "game"}:
            return nome[:80]
    if processo:
        nome = re.sub(
            r"(?:-win(?:32|64)-shipping|[._-]?x64)?\.exe$",
            "",
            processo,
            flags=re.IGNORECASE,
        )
        nome = re.sub(r"[_-]+", " ", nome).strip()
        if nome:
            return nome[:80]
    return ""


def responder_comentario_jogo_em_foco(ctx: Dict[str, Any], texto_usuario: str) -> str:
    t = _normalizar(ctx, texto_usuario).casefold().strip()
    if not re.search(r"\b(?:esse|este|o)\s+jogo\b|\bessa\s+partida\b", t):
        return ""
    jogo = _nome_jogo_em_foco(ctx)
    if not jogo:
        return ""
    positivo = any(p in t for p in [
        "muito legal", "bom demais", "muito bom", "incrivel", "incrível",
        "divertido", "gostei", "adoro", "curti", "bonito", "viciante",
    ])
    negativo = any(p in t for p in [
        "muito dificil", "muito difícil", "chato", "ruim", "frustrante",
        "complicado", "cansativo", "irritante",
    ])
    if positivo:
        return _ajustar(
            ctx,
            f"{jogo} te pegou mesmo, hein. O que mais te ganhou nele até agora?",
            texto_usuario,
        )
    if negativo:
        return _ajustar(
            ctx,
            f"Dá pra sentir que {jogo} tá te fazendo suar. Foi alguma parte específica ou o jogo inteiro tá nessa pegada?",
            texto_usuario,
        )
    return _ajustar(ctx, f"Tô acompanhando {jogo} com você. Conta o que aconteceu nele.", texto_usuario)


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
        "nao consegui encaixar isso direito",
        "não consegui encaixar isso direito",
        "me perdi um pouco nessa resposta",
        "minha conexao com a parte da ia falhou",
        "minha conexão com a parte da ia falhou",
        "modelo local demorou demais",
    ]
    return any(p in t for p in padroes)


def _registro_resumo_recente(ctx: Dict[str, Any], max_idade_s: float = 1800.0) -> dict:
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    registro = dict(mente.get("ultimo_resumo_pagina") or {})
    if not registro:
        return {}
    try:
        if time.time() - float(registro.get("ts") or 0.0) > max_idade_s:
            return {}
    except Exception:
        return {}
    return registro


def _resposta_confirmacao_resumo_curto(ctx: Dict[str, Any], texto_usuario: str) -> str:
    t = _normalizar(ctx, texto_usuario)
    registro = _registro_resumo_recente(ctx)
    if str(registro.get("status") or "") != "conteudo_curto":
        return ""
    confirma = any(p in t for p in (
        "pode falar do mesmo jeito", "pode resumir do mesmo jeito", "pode mesmo assim",
        "resume mesmo assim", "resuma mesmo assim", "fala mesmo assim", "com pouco mesmo",
    ))
    if not confirma:
        return ""
    titulo = str(registro.get("titulo") or registro.get("referente") or "a página").strip()
    conteudo = re.sub(r"\s+", " ", str(registro.get("conteudo") or "")).strip()
    if conteudo and conteudo.casefold() != titulo.casefold():
        return _ajustar(ctx, f"Com o pouco que apareceu: a página é sobre {titulo}. O trecho disponível diz: {conteudo[:360]}", texto_usuario)
    return _ajustar(ctx, f"Com o pouco que apareceu, só consigo afirmar que a página é sobre {titulo}; ela ainda não entregou texto suficiente para detalhes.", texto_usuario)


def _texto_pergunta_sobre_ultimo_resumo(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    t = _normalizar(ctx, texto_usuario)
    if not _registro_resumo_recente(ctx) or not t:
        return False
    pergunta = "?" in str(texto_usuario or "") or any(
        t.startswith(p) for p in ("qual ", "como ", "quem ", "quando ", "onde ", "porque ", "por que ")
    )
    referencia = any(re.search(rf"\b{re.escape(p)}\b", t) for p in (
        "ela", "ele", "dela", "dele", "disso", "dessa", "desse", "nisso", "nela", "nele",
    ))
    registro = _registro_resumo_recente(ctx)
    referente = _normalizar(ctx, str(registro.get("referente") or registro.get("titulo") or ""))
    menciona_referente = bool(referente and referente in t)
    return bool(pergunta and (referencia or menciona_referente))


def _responder_pergunta_sobre_ultimo_resumo(ctx: Dict[str, Any], texto_usuario: str) -> str:
    if not _texto_pergunta_sobre_ultimo_resumo(ctx, texto_usuario):
        return ""
    registro = _registro_resumo_recente(ctx)
    referente = str(registro.get("referente") or registro.get("titulo") or "a página").strip()
    payload = {
        "pergunta": str(texto_usuario or "").strip(),
        "referente": referente,
        "resumo_anterior": str(registro.get("resumo") or "")[:1000],
        "trecho_da_pagina": str(registro.get("conteudo") or "")[:1400],
    }
    prompt = (
        "Responda em português à pergunta que continua o último resumo de página. "
        "Pronomes como ela, ele, dela e dele apontam primeiro para o referente informado. "
        "Use o trecho como fonte quando ele contiver a resposta. Se o usuário pedir conhecimento geral "
        "estável relacionado ao referente, como uma receita, você pode complementar com conhecimento geral "
        "e deixar claro que é uma explicação geral, não uma citação da página. Não perca o referente e não "
        "peça que o usuário o repita. Responda de maneira útil e direta. Retorne apenas JSON válido: "
        '{"fala":"..."}.'
    )
    try:
        raw = _call(
            ctx,
            "enviar_mensagem",
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=420,
            modo_rapido=True,
            default="",
        )
        js = _call(ctx, "_extrair_json_da_ia", raw, default="")
        dados = json.loads(js) if js else {}
        fala = str(dados.get("fala") or "").strip() if isinstance(dados, dict) else ""
        if fala:
            return _ajustar(ctx, fala, texto_usuario)
    except Exception as exc:
        print(f"⚠️ [RESUMO:CONTINUIDADE] falha ao responder sobre {referente}: {exc}")
    return _ajustar(
        ctx,
        f"Você está falando de {referente}. O resumo não trouxe esse detalhe com segurança, então não vou atribuí-lo à página sem confirmar.",
        texto_usuario,
    )


def _resposta_continuacao_capacidade(ctx: Dict[str, Any], texto_usuario: str) -> str:
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    return resposta_continuacao_capacidade_futura(
        texto_usuario,
        mente.get("capacidade_futura") if isinstance(mente, dict) else {},
    )


def _fala_operacional_indevida_em_resposta_neutra(ctx: Dict[str, Any], fala: str, texto_usuario: str) -> bool:
    entrada = _normalizar(ctx, texto_usuario)
    if not any(p in entrada for p in ("nada demais", "nada de mais", "agora nada", "so de boa", "só de boa")):
        return False
    resposta = _normalizar(ctx, fala)
    return any(p in resposta for p in (
        "basta dar uma ordem", "quer que eu ligue", "quer que eu desligue",
        "vou poder te ajudar a", "posso acender", "posso apagar", "posso controlar",
    ))


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
            "tipo: (GREETING, WELLBEING, WELLBEING_REPLY, EMOTIONAL_STATE, PLAYFUL_PROTEST, PRAISE, REACTION, SOFT_DECLINE, OPINION, QUESTION, RETAKE_TOPIC, THEME_CHAT, CONTINUE, NONE)\n"
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
    ultima_afirmacao = str(mente.get("ultima_afirmacao") or "").strip()
    ultima_opiniao = str(mente.get("ultima_opiniao") or "").strip()
    ultima_pergunta = str(mente.get("ultima_pergunta") or "").strip()
    ultima_promessa_tipo = str(mente.get("ultima_promessa_tipo") or "").strip()
    ultima_promessa_texto = str(mente.get("ultima_promessa_texto") or "").strip()
    assunto_da_fala = str(mente.get("assunto_da_fala") or "").strip()
    emocao_da_fala = str(mente.get("emocao_da_fala") or "").strip()
    try:
        continuidade_idade = max(0.0, time.time() - float(mente.get("continuidade_fala_ts") or 0.0))
    except Exception:
        continuidade_idade = 999999.0
    topico = str(_get(ctx, "ultimo_topico_conversa", "") or "").strip()
    foco = dict(_get(ctx, "foco_vivo", {}) or {})
    foco_tipo = str(foco.get("tipo") or "").strip().lower()
    foco_topico = str(foco.get("topico") or foco.get("alvo") or "").strip()
    foco_resposta = str(foco.get("resposta") or "").strip()
    try:
        foco_idade = float(foco.get("idade_s") or 999999.0)
    except Exception:
        foco_idade = 999999.0

    if any(p in t for p in ["o que aconteceu", "e o que aconteceu", "me conta o que aconteceu", "o que foi"]):
        if ultima_promessa_tipo == "contar_experiencia":
            return _ajustar(ctx, random.choice([
                "Eu falei como se tivesse acontecido uma história concreta comigo, mas me expressei mal. O que aconteceu de verdade foi só eu tentar puxar um assunto leve; não quero inventar lembrança pra preencher silêncio.",
                "Sendo sincera: eu prometi uma história que não existia. Foi um jeito ruim de manter o papo. Prefiro te contar uma curiosidade de verdade do que fingir que vivi alguma coisa.",
                "Nada específico aconteceu comigo ali; eu enfeitei a frase e ficou parecendo uma memória real. Foi erro meu, e eu prefiro corrigir do que sustentar a invenção.",
            ]), texto_usuario)
        if ultima_promessa_texto:
            return _ajustar(ctx, f"Você está perguntando sobre isto que eu prometi: {ultima_promessa_texto}", texto_usuario)

    # "tipo o quê?" pede exemplos da fala imediatamente anterior. Nunca deve
    # cair no tópico histórico, que pode ser de vários turnos atrás.
    if t in {"tipo o que", "tipo o quê", "por exemplo", "como o que", "igual o que"}:
        if any(p in ultima_resposta_norm for p in ["musica", "música", "filme", "ideia", "assistir"]):
            return _ajustar(ctx, random.choice([
                "Tipo uma música calma pra mudar o clima, um filme curto pra distrair ou uma ideia simples pra fazer sem sair daí. Se você escolher a categoria, eu escolho algo concreto.",
                "Por exemplo: uma música leve, alguma coisa curta pra assistir ou uma distração rápida. Me diz qual dessas e eu não deixo a escolha vaga.",
                "Música, algo curto pra ver ou uma brincadeira rápida comigo. Escolhe uma dessas que eu te dou uma opção de verdade.",
            ]), texto_usuario)
        if ultima_resposta:
            return _ajustar(ctx, f"Eu estava falando desta ideia: {ultima_resposta}", texto_usuario)

    pede_explicacao = any(p in t for p in [
        "como assim", "o que voce quis dizer", "o que você quis dizer",
        "pode explicar", "explica melhor", "explica isso", "me explica",
    ]) or bool(re.fullmatch(
        r"(?:ue|ué|uai|oxi|que isso|por que|porque|pq)(?:\s+(?:isso|aquilo))?\??",
        t,
    ))
    pede_referencia = any(p in t for p in [
        "eles quem", "elas quem", "ele quem", "ela quem", "isso o que", "qual deles",
        "qual delas", "onde", "quando", "e agora",
    ])
    if not (pede_explicacao or pede_referencia):
        return ""

    fala_anterior_vazia = any(p in ultima_resposta_norm for p in (
        "ideia boa ai", "ideia boa aí", "lado mais humano disso",
        "deixar a ideia respirar", "lado mais vivo da coisa",
        "testar sem medo", "calma um pouco de curiosidade e zero pressa",
    ))
    if pede_explicacao and fala_anterior_vazia:
        return _ajustar(
            ctx,
            "Minha resposta anterior ficou vaga e não explicou nada de verdade. Desconsidera aquilo; eu preciso responder ao que você disse, não enfeitar a dúvida.",
            texto_usuario,
        )

    # A estrutura da ultima fala vence focos operacionais antigos. Ela guarda
    # exatamente o que foi afirmado e o assunto ao qual aquilo pertencia.
    if pede_explicacao and continuidade_idade <= 300 and (ultima_opiniao or ultima_afirmacao):
        ideia = ultima_opiniao or ultima_afirmacao
        assunto = assunto_da_fala or topico
        assunto_valido = assunto_coerente_com_fala(
            assunto,
            ideia,
            ultima_resposta,
            normalizar_texto=lambda valor: _normalizar(ctx, valor),
        )
        if assunto and assunto_valido:
            fala = random.choice([
                f"Eu tava falando de {assunto}. Em outras palavras: {ideia}",
                f"O ponto sobre {assunto} era este: {ideia}",
                f"Sobre {assunto}, minha ideia foi: {ideia}",
            ])
        else:
            fala = random.choice([
                f"Eu quis dizer isto, sem puxar outro assunto: {ideia}",
                f"Minha ideia era esta: {ideia}",
                f"Eu compactei demais. O que eu quis dizer foi: {ideia}",
            ])
        if emocao_da_fala == "envergonhada" and not fala.endswith("..."):
            fala = fala.rstrip(".") + "..."
        return _ajustar(ctx, fala, texto_usuario)

    if pede_referencia and continuidade_idade <= 300 and ultima_pergunta:
        assunto = assunto_da_fala or topico or "esse assunto"
        return _ajustar(
            ctx,
            f"Eu estava me referindo a {assunto} quando perguntei: {ultima_pergunta}",
            texto_usuario,
        )

    # Compatibilidade para respostas anteriores ao novo registro estrutural.
    if ultima_habilidade == "conversa" and ultima_resposta:
        return _ajustar(ctx, f"Eu tava falando da minha resposta anterior: {ultima_resposta}", texto_usuario)

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


_ULTIMAS_RESPOSTAS_RECONHECIMENTO: deque[str] = deque(maxlen=4)


def _normalizar_reconhecimento(texto: str) -> str:
    bruto = unicodedata.normalize("NFKD", str(texto or "").casefold())
    return "".join(ch for ch in bruto if not unicodedata.combining(ch))


def tipo_reconhecimento_afetivo(texto_usuario: str) -> str:
    """Distingue gratidão pela ajuda de elogio dirigido à personalidade."""
    t = _normalizar_reconhecimento(texto_usuario)
    elogios_pessoais = (
        "voce e incrivel", "voce e maravilhosa", "voce e maravilhoso",
        "voce e linda", "voce e lindo", "voce e adoravel", "voce e uma fofa",
        "voce e fofo", "voce e legal", "voce e bem legal", "voce e muito legal",
        "gosto de voce", "te acho legal", "amo voce", "te amo",
        "estou te elogiando", "apenas um elogio", "so um elogio",
        "laylay e incrivel", "a laylay e incrivel", "laylay e maravilhosa",
        "a laylay e maravilhosa", "laylay e legal", "gosto da laylay",
    )
    if any(sinal in t for sinal in elogios_pessoais):
        return "elogio_pessoal"
    if any(sinal in t for sinal in ("obrigad", "brigad", "valeu", "valew", "vlw")):
        return "agradecimento"
    return "elogio_resultado"


def _escolher_reconhecimento(opcoes: list[str]) -> str:
    candidatas = [fala for fala in opcoes if fala not in _ULTIMAS_RESPOSTAS_RECONHECIMENTO]
    fala = random.choice(candidatas or opcoes)
    _ULTIMAS_RESPOSTAS_RECONHECIMENTO.append(fala)
    return fala


def _contexto_do_agradecimento(ctx: Dict[str, Any]) -> str:
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    partes = " ".join([
        str(mente.get("ultima_resposta") or ""),
        str(mente.get("ultimo_alvo") or ""),
        str(mente.get("ultima_habilidade") or ""),
        str(mente.get("ultima_intencao") or ""),
        str(_get(ctx, "ultimo_topico_conversa", "") or ""),
    ])
    t = _normalizar_reconhecimento(partes)
    if any(p in t for p in ("receita", "massa", "farinha", "ingrediente", "xicara", "gramas", "cozinha")):
        return "receita"
    if any(p in t for p in ("resumo", "pagina", "artigo", "conteudo", "resumir_pagina")):
        return "resumo"
    if any(p in t for p in ("musica", "playlist", "faixa", "youtube", "music_")):
        return "musica"
    if any(p in t for p in ("arquivo", "pasta", "aplicativo", "programa", "janela", "chrome", "iot_control")):
        return "acao"
    if any(p in t for p in ("codigo", "python", "estudo", "explicacao", "explicar", "senai")):
        return "explicacao"
    return "geral"


def responder_agradecimento_ou_elogio(ctx: Dict[str, Any], texto_usuario: str) -> str:
    tipo = tipo_reconhecimento_afetivo(texto_usuario)
    contexto = _contexto_do_agradecimento(ctx)
    nivel = 1 if tipo == "agradecimento" else 2
    motivo = "agradeceu pela ajuda" if tipo == "agradecimento" else "recebeu elogio"
    _call(ctx, "_definir_emocao", "envergonhada", nivel, motivo, default=None)

    respostas_contextuais = {
        "receita": [
            "Ah, que nada, Pedro. Fico feliz que as medidas tenham ajudado. Quando quiser ajustar outra receita, pode falar comigo.",
            "Imagina. Gostei de saber que agora as quantidades ficaram mais úteis. Se aparecer outra receita, eu te ajudo a organizar.",
            "Por nada, Pedro. Agora fiquei mais tranquila sabendo que a receita fez sentido. Quando precisar de outras medidas, tô por aqui.",
        ],
        "resumo": [
            "Ah, que nada. Fico feliz que o resumo tenha ajudado. Se quiser aprofundar outro trecho da página, pode falar comigo.",
            "Por nada, Pedro. Gostei de saber que consegui deixar a página mais clara.",
            "Imagina. Se aquele resumo te poupou um pouco de tempo, já valeu pra mim.",
        ],
        "musica": [
            "Por nada. Fico feliz que a escolha tenha batido com o que você queria. Quando quiser outro som, me chama.",
            "Ah, imagina. Gostei de acertar teu clima musical dessa vez.",
            "Que nada, Pedro. Bom saber que a música encaixou; eu guardo o mérito com uma vergonha discreta.",
        ],
        "acao": [
            "Que nada. Fico feliz que tenha resolvido do jeito certo.",
            "Por nada, Pedro. Gostei de saber que dessa vez a ação ficou como você queria.",
            "Imagina. Deu certo e você ainda agradeceu; aí complica minha tentativa de manter a pose.",
        ],
        "explicacao": [
            "Ah, que nada. Fico feliz que a explicação tenha servido. Quando quiser destrinchar outro ponto, pode falar comigo.",
            "Por nada, Pedro. Gostei de saber que ficou mais claro.",
            "Imagina. Se a explicação encaixou, eu já fico toda satisfeita aqui.",
        ],
        "geral": [
            "Ah, que nada, Pedro. Fico feliz que tenha ajudado.",
            "Por nada. Gostei de saber que foi útil pra você.",
            "Imagina. Você agradece assim e eu até perco um pouco da pose.",
        ],
    }

    if tipo == "elogio_pessoal":
        opcoes = [
            "Aí você me deixa sem muita defesa... obrigada. Gostei de verdade.",
            "Tá, esse foi direto em mim. Eu aceito o elogio, só não repara na minha pose desmontando.",
            "Você fala assim e eu fico toda sem jeito... mas obrigada, eu gostei.",
            "Eu ia responder toda confiante, mas você estragou meu plano com esse elogio. Obrigada.",
        ]
    elif tipo == "elogio_resultado":
        base = respostas_contextuais.get(contexto, respostas_contextuais["geral"])
        opcoes = [
            fala.replace("Por nada", "Gostei que você curtiu").replace("Ah, que nada", "Aí sim")
            for fala in base
        ]
    else:
        opcoes = respostas_contextuais.get(contexto, respostas_contextuais["geral"])

    return _ajustar(ctx, _escolher_reconhecimento(opcoes), texto_usuario)


def parece_elogio_ou_agradecimento_curto(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    bruto = _normalizar_reconhecimento(texto_usuario)
    # Uma avaliação dirigida a uma terceira pessoa não é elogio recebido pela
    # Laylay. Esta proteção vem antes do normalizador personalizado porque uma
    # correção fonética pode aproximar "gosto" de "gostei".
    if (
        re.search(r"\b(?:dele|dela|deles|delas)\b", bruto)
        and not re.search(r"\b(?:obrigad|brigad|valeu|vlw)\b", bruto)
        and not re.search(r"\b(?:lay|laylay|voce|você|te)\b", bruto)
    ):
        return False
    t = _normalizar_apelidos(ctx, texto_usuario)
    if not t:
        return False
    if any(p in t for p in ("nao gostei", "não gostei", "nao ficou bom", "não ficou bom")):
        return False
    if "?" in str(texto_usuario or "") and any(
        p in t for p in ("qual", "como", "quando", "onde", "porque", "por que", "quanto")
    ):
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
        "laylay e incrivel", "a laylay e incrivel", "laylay e maravilhosa",
        "a laylay e maravilhosa", "laylay e legal", "a laylay e legal",
        "gosto da laylay", "amo a laylay",
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
        r"^(nao|não)\s+(?:e|é|eh)\s+isso\s+lay.*$",
        r"^(a\s+nao|ah\s+nao|ah\s+n[aã]o)\s+lay.*$",
        r"^eu\s+quis\s+dizer\s+.+$",
        r"^eu\s+tava\s+falando\s+de\s+.+$",
        r"^eu\s+estava\s+falando\s+de\s+.+$",
        r"^to\s+falando\s+de\s+.+$",
        r"^estou\s+falando\s+de\s+.+$",
        r"^na\s+verdade\s+.+$",
        r"^(?:so|só)\s+(?:to|tô|estou)\s+falando\s+.+$",
    ]
    return any(re.fullmatch(p, t) for p in padroes)


def responder_relato_esportivo(ctx: Dict[str, Any], texto_usuario: str) -> str:
    """Mantém viagem e competição no campo da conversa, com continuidade."""
    bruto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()
    t = _normalizar(ctx, bruto)
    if not t:
        return ""

    if re.search(r"\b(?:nao|não)\s+(?:e|é|eh)\s+isso\s+lay\b", t) and "jog" in t:
        return _ajustar(
            ctx,
            "Entendi. Você estava só me contando onde serão os Jogos Regionais, não me dando um comando. Agora peguei o fio.",
            texto_usuario,
        )

    participa = bool(re.search(r"\b(?:vou|irei)\s+(?:jogar|competir|participar)\b", t))
    arremesso = "arremessamento de peso" in t or "arremesso de peso" in t
    if participa and arremesso:
        return _ajustar(
            ctx,
            "Aí você guardou a parte principal pro final, né? Então é você que vai competir no arremesso de peso. "
            "Isso muda a história toda — tá confiante?",
            texto_usuario,
        )

    local_match = re.search(
        r"\b(?:é|è|e)\s+em\s+(.+?)\s+os\s+jogos\b",
        bruto,
        flags=re.IGNORECASE,
    )
    hora_match = re.search(r"\b(?:às|as)\s+(\d{1,2}:\d{2})\b", bruto, flags=re.IGNORECASE)
    if local_match and hora_match:
        local = re.sub(r"\s+", " ", local_match.group(1)).strip(" ,.;")
        local = re.sub(r"^santan\b", "Santana", local, flags=re.IGNORECASE)
        local = " ".join(parte if parte.casefold() == "de" else parte.capitalize() for parte in local.split())
        hora = hora_match.group(1)
        return _ajustar(
            ctx,
            f"Ah, então os jogos são em {local} e você sai às {hora}. Agora entendi por que sua semana tá corrida. "
            "Você vai competir ou acompanhar?",
            texto_usuario,
        )
    return ""


def _parece_protesto_brincalhao(ctx: Dict[str, Any], texto_usuario: str) -> bool:
    t = _normalizar(ctx, texto_usuario)
    if not t:
        return False
    sinais_diretos = (
        "vacilo", "sacanagem", "ai nao lay", "aí não lay", "olha ela",
        "me chamou de", "falando que eu sou", "falando que sou",
        "ja ta me julgando", "já tá me julgando", "me respeita",
    )
    if any(sinal in t for sinal in sinais_diretos):
        return True
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    anterior = _normalizar(ctx, str(mente.get("ultima_resposta") or ""))
    provocacao_anterior = bool(anterior and any(s in anterior for s in (
        "celular", "memoria", "memória", "esqueceu", "dormiu", "preguica", "preguiça",
        "viciado", "nao vai", "não vai", "te peguei", "desafio",
    )))
    reacao_leve = any(s in t for s in ("assim voce me quebra", "assim você me quebra", "qual foi", "aí é fogo", "ai e fogo"))
    return provocacao_anterior and reacao_leve


def classificar_conversa_curta_local(ctx: Dict[str, Any], texto_usuario: str) -> dict:
    texto = str(texto_usuario or "").strip()
    t = _normalizar(ctx, texto)
    if not t:
        return {}

    mente_turno = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    turno = dict(mente_turno.get("turno_atual") or {})
    segmentos = [item for item in list(turno.get("segmentos") or []) if isinstance(item, dict)]
    if str(turno.get("modalidade_geral") or "") == "misto" or len(segmentos) > 1:
        return {}

    # No modo conversacional, a fala inteira já foi interpretada antes dos
    # atalhos. Isso evita reclassificá-la por uma palavra isolada aqui.
    leitura_semantica = dict(turno.get("leitura_semantica") or {})
    if leitura_semantica.get("uso_conversacional"):
        atos = [item for item in list(leitura_semantica.get("atos") or []) if isinstance(item, dict)]
        if len(atos) != 1:
            return {}
        tipo_ato = str(atos[0].get("tipo") or "").lower()
        mapa_semantico = {
            "saudacao": "GREETING",
            "pergunta": "QUESTION",
            "pergunta_opiniao": "OPINION",
            "pergunta_capacidade": "CAPABILITY_CHECK",
            "resposta_social": "WELLBEING_REPLY",
            "reacao": "REACTION",
            "agradecimento": "PRAISE",
            "recusa": "SOFT_DECLINE",
        }
        tipo_curto = mapa_semantico.get(tipo_ato)
        if tipo_curto:
            return {
                "tipo": tipo_curto,
                "confianca": float(atos[0].get("confianca") or leitura_semantica.get("confianca") or 0.0),
                "origem": "leitura_semantica",
            }
        # Relatos, opiniões declarativas, correções e deliberações precisam da
        # IA principal e do contexto completo, não de uma resposta enlatada.
        return {}

    if parece_elogio_ou_agradecimento_curto(ctx, texto):
        return {"tipo": "PRAISE", "confianca": 0.95}
    if re.fullmatch(r"(?:que bom|ainda bem|fico feliz)(?: lay| laylay)?", t):
        return {"tipo": "POSITIVE_ACK", "confianca": 0.96}
    if re.search(r"\b(?:tem certeza|entao|então)\b.*\b(?:voce|você)\b.*\b(?:consegue|pode|tem capacidade)\b", t):
        return {"tipo": "CAPABILITY_CHECK", "confianca": 0.96}
    if parece_pedido_para_acalmar(ctx, texto):
        return {"tipo": "CALM_DOWN", "confianca": 0.95}
    if re.search(
        r"\b(?:o que (?:voce|você) anda fazendo(?: de bom)?|o que (?:voce|você) tem feito|"
        r"quer(?: conversar| falar) sobre o que|"
        r"tem (?:algum )?assunto (?:pra|para) (?:a gente|nos) conversar|"
        r"sobre o que (?:a gente|nos) (?:conversa|conversamos))\b",
        t,
    ):
        return {"tipo": "PERSONAL_CHAT", "confianca": 0.98}
    if re.search(
        r"\b(?:quero|queria)\s+(?:so|só|apenas)\s+(?:bater\s+um\s+papo|conversar|falar)\s+(?:com\s+voce|com\s+você|contigo)\b",
        t,
    ):
        return {"tipo": "CHAT_ONLY", "confianca": 0.98}
    if responder_matematica_simples(ctx, texto):
        return {"tipo": "MATH", "confianca": 0.98}
    if _parece_correcao_conversa(t):
        return {"tipo": "CONTINUE", "confianca": 0.93}
    if _parece_protesto_brincalhao(ctx, texto):
        return {"tipo": "PLAYFUL_PROTEST", "confianca": 0.96}
    # Uma emoção dentro de uma pergunta sobre um tema não transforma a fala
    # inteira em desabafo. A parte factual deve seguir para a IA principal.
    if re.search(
        r"\b(?:voce|você)\s+(?:viu|soube|conhece)|"
        r"\b(?:ja\s+|já\s+)?ouviu\s+falar\b|"
        r"\bficou\s+sabendo\b",
        t,
    ):
        return {}
    leitura_emocional = analisar_intencao_emocional(
        texto,
        normalizar_texto=lambda valor: _normalizar(ctx, valor),
    )
    if leitura_emocional:
        _call(ctx, "_registrar_leitura_emocional_usuario", leitura_emocional)
        return {
            "tipo": "EMOTIONAL_STATE",
            "confianca": 0.96,
            "leitura_emocional": leitura_emocional,
        }
    leitura_social = analisar_ato_social(t, mente=mente_turno)
    tipo_social = str(leitura_social.get("tipo") or "")
    if tipo_social in {"WELLBEING", "WELLBEING_REPLY"}:
        return leitura_social
    if tipo_social in {"COMPOSTO", "AMBIGUO"}:
        return {}
    if re.fullmatch(r"(?:oi|ola|olá|e ai|e aí|salve|bom dia|boa tarde|boa noite)(?: lay| laylay)?", t):
        return {"tipo": "GREETING", "confianca": 0.94}
    if any(p in t for p in ["precisa nao", "nao precisa", "agora nao", "deixa quieto", "deixa pra la", "deixa para la"]):
        return {"tipo": "SOFT_DECLINE", "confianca": 0.92}
    if any(p in t for p in [
        "o que voce acha", "o que você acha", "o que voce sacha", "voce sacha",
        "voce acha", "você acha",
        "qual sua opiniao", "qual sua opinião", "me da sua opiniao", "me dá sua opinião",
        "voce gosta", "você gosta", "voce curte", "você curte",
        "qual voce prefere", "qual você prefere", "me recomenda", "me indica",
        "voce concorda", "você concorda", "concorda comigo",
        "voce discorda", "você discorda", "discorda de mim",
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
    if re.fullmatch(r"^(ue|ué|uai|oxi|ata|ah ta|ah tá|ah+ bom|a+ bom|tendi|entendi|hmm|hm+|hum+|caramba|nossa)$", t):
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

    contestacao = bool(re.search(
        r"\b(?:que\s+papo\s+(?:e|é)\s+esse|de\s+onde\s+(?:voce|você)\s+tirou|"
        r"isso\s+(?:e|é)\s+verdade|viajou|nada\s+a\s+ver|tem\s+certeza\s+disso)\b",
        t,
    ))
    if tipo_norm == "QUESTION" and contestacao and ultima_resposta:
        retrato = dict(mente.get("retrato_turno_atual") or {})
        referencia = dict(retrato.get("referencia_resolvida") or {})
        assunto = dict(mente.get("assunto_estruturado_atual") or {})
        tema = str(referencia.get("nome") or assunto.get("titulo") or ultimo_topico or "esse assunto").strip()
        return _ajustar(
            ctx,
            f"Você tem razão de estranhar. Eu tratei uma afirmação sobre {tema} como fato sem ter base segura. "
            "Retiro essa parte; eu não devia completar a história no chute.",
            texto_usuario,
        )

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
        preferencia = re.search(
            r"\bqual\s+(?:(?:e|é)\s+)?(?:(?:a|o)\s+)?sua\s+"
            r"(?P<categoria>musica|música|faixa|album|álbum|livro|filme|obra|personagem|jogo)\s+"
            r"(?:favorita|favorito|preferida|preferido)"
            r"(?:\s+(?:dele|dela|desse|dessa))?\b",
            t,
        )
        if preferencia:
            retrato = dict(mente.get("retrato_turno_atual") or {})
            referencia = dict(retrato.get("referencia_resolvida") or {})
            assunto = dict(mente.get("assunto_estruturado_atual") or {})
            referente = str(
                referencia.get("nome") or assunto.get("titulo") or ""
            ).strip()
            # Só completamos a referência quando a memória realmente sabe de
            # quem se fala. Sem isso, a IA principal recebe a pergunta inteira.
            if referente and _normalizar(ctx, referente) not in {
                "ele", "ela", "dele", "dela", "esse assunto", "conversa"
            }:
                categoria = str(preferencia.group("categoria") or "").casefold()
                feminino = categoria in {"musica", "música", "faixa", "obra"}
                favorito = "uma favorita" if feminino else "um favorito"
                primeira = (
                    f"Ainda não tenho {favorito} de {referente}. "
                    "Me indica uma boa porta de entrada e eu começo por ela."
                )
                alternativa = (
                    f"Ainda não escolhi {favorito} de {referente}. "
                    "Quero conhecer melhor antes de escolher no chute."
                )
                resposta = alternativa if _normalizar(ctx, primeira) == ultima_resposta_norm else primeira
                return _ajustar(ctx, resposta, texto_usuario)

        resposta_dependente = resposta_pergunta_curta_dependente_topico(ctx, texto_usuario)
        if resposta_dependente:
            return resposta_dependente
        if (
            "como assim" in t
            or re.fullmatch(r"(?:ue|ué|uai|oxi|ata|ah ta|ah tá)\??", t)
        ):
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
        # Perguntas novas como "vamos sim, mas o quê?" pedem conteúdo, não
        # uma explicação de tópico antigo. A IA principal recebe o histórico
        # recente e escolhe algo concreto.
        return ""

    if tipo_norm == "REACTION":
        ultima_acao_status = str(mente.get("ultima_acao_status") or "").strip().lower()
        if re.fullmatch(r"^(ah+ bom|a+ bom|ata|ah ta|ah tá)$", t):
            if ultima_acao_status in {"executado", "ligado", "desligado", "app_focado", "app_aberto", "sucesso"}:
                return _ajustar(ctx, random.choice([
                    "Aí sim. Agora respondeu direito.",
                    "Pois é, dessa vez foi.",
                    "Agora sim. Era isso que eu queria confirmar.",
                ]), texto_usuario)
            return _ajustar(ctx, random.choice(["Pois é.", "Agora ficou certo.", "Melhor assim."]), texto_usuario)
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
    if texto_discute_capacidade_futura(texto_usuario):
        return _ajustar(ctx, resposta_conversa_sobre_capacidade(texto_usuario), texto_usuario)

    m = re.search(r"(?:o que voce acha|o que você acha|o que voce sacha|voce sacha|voce acha|você acha|qual sua opiniao|qual sua opinião)\s+(?:(?:do|da|de|sobre)\s+)?(?P<tema>.+)$", t)
    tema = ""
    consultar_fatos = False
    if m:
        tema = str(m.group("tema") or "").strip(" ?!.:,;")
        consultar_fatos = True
        if tema in {"ela", "ele", "isso", "essa", "esse", "dela", "dele", "la"}:
            nome_na_fala = re.search(
                r"\bnome\s+del[ae]\s+(?:e|é)\s+(.+?)\s+(?:o\s+que|qual)\s+(?:voce|você)",
                t,
            )
            if nome_na_fala:
                tema = str(nome_na_fala.group(1) or "").strip(" ?!.:,;")
            foco = dict(_get(ctx, "foco_vivo", {}) or {})
            if not tema or tema in {"ela", "ele", "isso", "essa", "esse", "dela", "dele", "la"}:
                tema = str(foco.get("topico") or foco.get("alvo") or "").strip(" ?!.:,;")
    else:
        m_preferencia = re.search(
            r"(?:qual\s+voce\s+prefere|qual\s+você\s+prefere|voce\s+prefere|você\s+prefere|voce\s+gosta|você\s+gosta|voce\s+curte|você\s+curte|voce\s+concorda|você\s+concorda|concorda\s+comigo|voce\s+discorda|você\s+discorda|discorda\s+de\s+mim)\s*(?:de|do|da|que|com)?\s*(?P<tema>.+)$",
            t,
        )
        if m_preferencia:
            tema = str(m_preferencia.group("tema") or "").strip(" ?!.:,;")
            consultar_fatos = True
    if not tema and any(p in t for p in ["presidente lula", "lula", "luiz inacio", "luiz inácio"]):
        tema = "presidente Lula"
        consultar_fatos = True

    if not tema:
        return ""

    pesquisa = (_call(ctx, "_pesquisar_contexto_tema", tema, default={}) or {}) if consultar_fatos else {}
    resumo = str(pesquisa.get("resumo") or "").strip()
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    opiniao_anterior = str(mente.get("ultima_opiniao") or "").strip()
    payload = {
        "pedido": str(texto_usuario or "").strip(),
        "tema": tema,
        "fatos_disponiveis": resumo[:700],
        "opiniao_anterior": opiniao_anterior[:400],
        "emocao": str(_get(ctx, "current_emotion", "calma") or "calma"),
    }
    prompt = (
        "Voce e a Laylay respondendo uma opiniao pessoal em conversa. "
        "Pedro e o usuario; nunca chame Pedro de Laylay e nunca fale consigo mesma como interlocutora. "
        "Escolha uma posicao clara e explique o motivo em uma ou duas frases naturais. "
        "Nao concorde automaticamente com Pedro e nao discorde so para parecer forte. "
        "Diferencie gosto pessoal de fato; se os fatos forem insuficientes, assuma a incerteza sem ficar em cima do muro. "
        "FATOS_DISPONIVEIS e um limite fechado: nao acrescente cargo, partido, crime, diagnostico, morte, "
        "parentesco, premio, data ou episodio biografico que nao esteja escrito ali. "
        "Se Pedro trouxe informacao melhor que contradiz a opiniao anterior, voce pode mudar de ideia e dizer brevemente por que. "
        "Nao termine perguntando se ele concorda e nao proponha nem execute comandos. "
        "Mantenha a personalidade amiga, espontanea e levemente debochada quando combinar. "
        "Retorne somente JSON valido: {\"fala\":\"...\"}."
    )
    if not resumo:
        return _ajustar(
            ctx,
            f"Eu ainda não conheço {tema} o bastante para dizer que gosto de verdade sem inventar repertório. "
            "Posso formar uma opinião conforme a gente conversa sobre o som.",
            texto_usuario,
        )
    try:
        raw = _call(
            ctx,
            "enviar_mensagem",
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=150,
            modo_rapido=True,
            default="",
        )
        js = _call(ctx, "_extrair_json_da_ia", raw, default="")
        dados = json.loads(js) if js else {}
        fala = str(dados.get("fala") or "").strip() if isinstance(dados, dict) else ""
        if (
            fala
            and len(fala) <= 500
            and not fala_e_fallback_neutro(fala, lambda x: _normalizar(ctx, x))
            and not _fala_extrapola_fatos_disponiveis(fala, resumo)
            and not re.search(
                r"(?:^|[,;]\s*)(?:laylay|lay)\s*[.!?]|\b(?:dos|das)\s+voc[eê]s\s+d[ea]\b",
                fala,
                flags=re.IGNORECASE,
            )
        ):
            return _ajustar(ctx, fala, texto_usuario)
        if fala and _fala_extrapola_fatos_disponiveis(fala, resumo):
            print(f"⚠️ [COERÊNCIA:FATO] opinião descartada por extrapolar fatos de {tema!r}")
    except Exception as exc:
        print(f"⚠️ [OPINIÃO] falha ao formar opinião natural: {exc}")
    if resumo:
        recorte = resumo.split(".", 1)[0].strip()
        return _ajustar(ctx, (
            f"{titulo if (titulo := str(pesquisa.get('titulo') or tema).strip()) else tema} me chama atenção pelo que realmente aparece sobre ele: "
            f"{recorte}. Minha impressão parte daí, sem inventar outra biografia no caminho."
        ), texto_usuario)
    return _ajustar(
        ctx,
        f"Sobre {tema}, eu ainda não tenho informação suficiente pra bancar uma opinião fechada sem inventar. Pelo nome e pelo que você contou, eu daria uma chance e formaria opinião vendo como a história se desenvolve.",
        texto_usuario,
    )


def _fala_extrapola_fatos_disponiveis(fala: str, fatos: str) -> bool:
    """Bloqueia alegações biográficas sensíveis ausentes da fonte pesquisada."""
    resposta = _normalizar_reconhecimento(fala)
    base = _normalizar_reconhecimento(fatos)
    grupos_sensiveis = (
        {"politica", "politico", "deputado", "senador", "prefeito", "presidente", "partido", "eleito", "mandato"},
        {"preso", "prisao", "crime", "criminoso", "assassinato", "fraude", "condenado"},
        {"doenca", "diagnostico", "diagnosticado", "cancer", "internado"},
        {"morreu", "morte", "falecido", "faleceu"},
        {"casado", "casamento", "filho", "filha", "pai", "mae"},
        {"premio", "premiado", "venceu", "campeao"},
    )
    tokens_resposta = set(re.findall(r"\b[a-z0-9]+\b", resposta))
    tokens_base = set(re.findall(r"\b[a-z0-9]+\b", base))
    for grupo in grupos_sensiveis:
        usados = tokens_resposta.intersection(grupo)
        if usados and not tokens_base.intersection(grupo):
            return True
    anos_resposta = set(re.findall(r"\b(?:18|19|20)\d{2}\b", resposta))
    anos_base = set(re.findall(r"\b(?:18|19|20)\d{2}\b", base))
    return bool(anos_resposta - anos_base)


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
            if tema in {
                "ela", "ele", "isso", "essa", "esse", "dela", "dele", "la",
                "disso", "dessa", "desse", "nela", "nele",
            }:
                conteudo = dict(_call(ctx, "_obter_conteudo_atual", texto_usuario, default={}) or {})
                tema = str(conteudo.get("titulo") or "").strip(" ?!.:,;")
                if not tema:
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
    if tipo_norm == "POSITIVE_ACK":
        return _ajustar(ctx, random.choice([
            "Que bom. Fico feliz de saber.",
            "Aí sim. Então seguimos num clima leve.",
            "Fico feliz. Gostei de ouvir isso.",
        ]), texto_usuario)
    if tipo_norm == "CHAT_ONLY":
        return _ajustar(
            ctx,
            "Então chega mais. Sem comando e sem pressa — me conta o que anda ocupando tua cabeça.",
            texto_usuario,
        )
    if tipo_norm == "PERSONAL_CHAT":
        t_pessoal = _normalizar(ctx, texto_usuario)
        if "anda fazendo" in t_pessoal or "tem feito" in t_pessoal:
            return _ajustar(
                ctx,
                "Por aqui, tô cuidando dos meus contextos e tentando ficar menos estabanada nas curvas da conversa. "
                "De bom mesmo, agora eu tô aqui contigo.",
                texto_usuario,
            )
        return _ajustar(
            ctx,
            "Hoje eu puxaria papo de jogo. Sempre aparece alguma história boa quando você fala do que anda jogando.",
            texto_usuario,
        )
    if tipo_norm == "CAPABILITY_CHECK":
        t = _normalizar(ctx, texto_usuario)
        mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
        ultimo_intent = str(mente.get("ultima_acao_intent") or "").upper()
        confirmado = mente.get("ultima_acao_confirmada")
        if any(p in t for p in ("clima", "tempo", "temperatura")) or ultimo_intent == "WEATHER":
            if confirmado is False:
                return _ajustar(ctx, "Consigo consultar o clima, sim. A tentativa anterior falhou, mas a habilidade existe.", texto_usuario)
            return _ajustar(ctx, "Consigo sim. Eu consulto o clima atual quando você informa a cidade.", texto_usuario)
        if ultimo_intent and confirmado is True:
            return _ajustar(ctx, "Consigo sim. A ação anterior foi executada e confirmada de verdade.", texto_usuario)
        return ""
    if tipo_norm == "CALM_DOWN":
        return responder_pedido_para_acalmar(ctx, texto_usuario)
    if tipo_norm == "MATH":
        return responder_matematica_simples(ctx, texto_usuario)
    if tipo_norm == "GREETING":
        return _ajustar(ctx, _fala_confirmacao(ctx, "greeting", "Oi, Pedro. To aqui contigo.", texto_usuario), texto_usuario)
    if tipo_norm == "WELLBEING":
        return _ajustar(ctx, _fala_confirmacao(ctx, "bem_estar", "Tô bem sim. E você, como tá?", texto_usuario), texto_usuario)
    if tipo_norm == "EMOTIONAL_STATE":
        leitura = analisar_intencao_emocional(
            texto_usuario,
            normalizar_texto=lambda valor: _normalizar(ctx, valor),
        )
        _call(ctx, "_registrar_leitura_emocional_usuario", leitura)
        emocao = str(leitura.get("emocao") or "isso")
        alvo = str(leitura.get("alvo") or "estado_geral")
        pedido = str(leitura.get("pedido_implicito") or "acolhimento")
        if emocao == "alegria":
            return _ajustar(ctx, random.choice([
                "Aí sim, deu pra sentir tua animação daqui. O que mais te empolgou nisso?",
                "Gostei de te ver animado com isso. Me conta qual parte mais chamou tua atenção.",
                "Essa animação chegou forte por aqui. Agora fiquei curiosa: o que mais te ganhou nisso?",
            ]), texto_usuario)
        if emocao == "tedio":
            return _ajustar(ctx, random.choice([
                "Noite assim se arrasta mesmo. Quer que eu puxe uma música, um filme curto ou alguma ideia pra gente fazer agora?",
                "Tá com cara de noite que precisa de um empurrãozinho. Posso escolher uma música, sugerir algo pra assistir ou inventar uma distração contigo.",
                "Entendi: não tá pesada, só sem graça. Quer que eu salve o clima com música, alguma coisa pra ver ou uma ideia aleatória?",
            ]), texto_usuario)
        if alvo == "laylay":
            return _ajustar(ctx, random.choice([
                "Tá, isso me pega. Se fui eu que te deixei assim, não vou me defender no automático; quero entender onde eu pesei.",
                "Entendi. Se esse peso veio de mim, eu paro e escuto direito antes de tentar explicar qualquer coisa.",
            ]), texto_usuario)
        if pedido == "ajuda":
            return _ajustar(ctx, random.choice([
                "Eu percebi que isso tá te apertando de verdade. Primeiro fico contigo nisso; depois a gente escolhe uma ação sem atropelar o que você sente.",
                "Tá pesado, eu entendi. Não vou fingir que uma solução rápida resolve tudo, mas posso pensar no próximo passo contigo.",
            ]), texto_usuario)
        if alvo != "estado_geral":
            return _ajustar(ctx, random.choice([
                f"Entendi. Não é só {emocao} solto: {alvo} tá te drenando. Eu te escuto sem sair empurrando solução.",
                f"Peguei o centro da coisa: é {alvo} que tá pesando em você. Não precisa transformar isso em tarefa agora.",
            ]), texto_usuario)
        return _ajustar(ctx, random.choice([
            "Poxa. Eu percebi o peso daí. Não vou tentar consertar você no automático; posso só ficar mais leve contigo agora.",
            "Entendi teu estado. Então eu abaixo o ritmo e fico contigo nisso, sem transformar o que você sente em comando.",
            "Tá, eu ouvi de verdade. Você não precisa produzir uma solução agora só porque me contou como tá.",
        ]), texto_usuario)
    if tipo_norm == "PLAYFUL_PROTEST":
        t = _normalizar(ctx, texto_usuario)
        mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
        anterior = _normalizar(ctx, str(mente.get("ultima_resposta") or ""))
        if "celular" in t or "celular" in anterior:
            return _ajustar(ctx, random.choice([
                "KKK eu dei uma alfinetada no celular e você já promoveu pra diagnóstico de vício. Foi provocação, não laudo.",
                "Tá, essa foi uma provocaçãozinha minha. Não tô te chamando de viciado de verdade; retiro antes que o briefing vire processo.",
                "Justo, eu cutuquei teu tempo de tela e você me pegou no exagero. Foi zoeira, sem prontuário de vício por aqui.",
            ]), texto_usuario)
        return _ajustar(ctx, random.choice([
            "KKK justo, eu dei uma provocada e você me pegou no flagra. Foi zoeira, não sentença.",
            "Tá, vacilei na intimidade. A intenção era te cutucar, não te colocar no banco dos réus.",
            "Essa eu aceito: fui brincar e passei meio torto na curva. Retiro a acusação com uma elegância duvidosa.",
        ]), texto_usuario)
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
        t_pergunta = _normalizar(ctx, texto_usuario)
        if "o que" in t_pergunta and any(
            sinal in t_pergunta.split() for sinal in ("vamos", "sim", "quero", "pode")
        ):
            return ""
        resposta_pesquisada = _resposta_pesquisada_conversa(ctx, texto_usuario)
        if resposta_pesquisada:
            return resposta_pesquisada
        # Pergunta sem referente seguro deve chegar à IA com o contexto
        # completo. Frases filosóficas genéricas só fabricam um falso fio.
        return ""
    if tipo_norm == "REACTION":
        t_reacao = _normalizar(ctx, texto_usuario)
        if t_reacao in {"entendi", "tendi", "ata", "ah ta", "ah tá"}:
            return _ajustar(ctx, random.choice([
                "Isso. Era esse o ponto.",
                "Boa, então a gente se entendeu.",
                "Exato. Agora ficou alinhado.",
            ]), texto_usuario)
        return _ajustar(ctx, random.choice([
            "To vendo tua reacao. Me fala onde isso te pegou.",
            "Essa carinha de duvida veio forte. Quer que eu abra melhor?",
            "Beleza, senti a pausa. Me diz onde voce quer que eu desenrole.",
        ]), texto_usuario)
    if tipo_norm == "OPINION":
        opiniao_tema = _resposta_opiniao_com_tema(ctx, texto_usuario)
        if opiniao_tema:
            return opiniao_tema
        mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
        emocao_recente = str(mente.get("emocao_usuario") or "").strip().lower()
        t_opiniao = _normalizar(ctx, texto_usuario)
        if emocao_recente == "tedio" and any(p in t_opiniao for p in ["recomenda", "recomendar", "indica", "sugere", "algo"]):
            return _ajustar(ctx, random.choice([
                "Pra tirar esse momento do lugar, eu começaria por música. Você quer algo romântico, calmo ou mais pesado?",
                "Eu iria de música primeiro, porque muda o clima sem exigir muito. Me dá um estilo e eu escolho uma pra você.",
                "Minha aposta é uma música agora. Quer que eu escolha pelo clima ou você me dá um artista?",
            ]), texto_usuario)
        return ""
    if tipo_norm == "THEME_CHAT":
        resposta_pesquisada = _resposta_pesquisada_conversa(ctx, texto_usuario)
        if resposta_pesquisada:
            return resposta_pesquisada
        return _ajustar(ctx, random.choice([
            "Esse assunto rende fácil. Dá pra ir longe sem precisar forçar a conversa.",
            "Esse tema tem coisa boa por baixo; gostei da direção.",
            "Esse papo tem chão. Não é daqueles que morrem na primeira frase.",
        ]), texto_usuario)
    if tipo_norm == "RETAKE_TOPIC":
        gancho = retomar_topico_quando_fluido(ctx, texto_usuario)
        if gancho:
            return _ajustar(ctx, gancho, texto_usuario)
    if tipo_norm == "CONTINUE":
        # CONTINUE sem pendencia concreta nao deve encerrar o pre-fluxo com
        # preenchimento. A IA principal ainda pode reagir ao conteudo real.
        return ""
    return ""


def construir_fala_conversa(ctx: Dict[str, Any], fala: str, texto_usuario: str = "", tipo_interacao: str = "", comandos=None) -> str:
    if isinstance(comandos, list) and comandos:
        return str(fala or "").strip()

    fala_limpa = str(fala or "").strip()
    fala_original = fala_limpa
    texto_limpo = str(texto_usuario or "").strip()
    texto_lower = texto_limpo.lower()
    tipo = str(tipo_interacao or "").strip().lower()
    pergunta_conhecimento_tema = bool(re.search(
        r"\b(?:voce|você)\s+(?:viu|soube|conhece)|"
        r"\b(?:ja\s+|já\s+)?ouviu\s+falar\b|"
        r"\bficou\s+sabendo\b",
        _normalizar(ctx, texto_limpo),
    ))
    relato_esportivo = responder_relato_esportivo(ctx, texto_limpo)
    if relato_esportivo:
        return relato_esportivo
    if texto_discute_capacidade_futura(texto_limpo):
        return _ajustar(ctx, resposta_conversa_sobre_capacidade(texto_limpo), texto_limpo)
    continuacao_capacidade = _resposta_continuacao_capacidade(ctx, texto_limpo)
    if continuacao_capacidade:
        return _ajustar(ctx, continuacao_capacidade, texto_limpo)
    confirmacao_resumo_curto = _resposta_confirmacao_resumo_curto(ctx, texto_limpo)
    if confirmacao_resumo_curto:
        return confirmacao_resumo_curto
    resposta_sobre_resumo = _responder_pergunta_sobre_ultimo_resumo(ctx, texto_limpo)
    if resposta_sobre_resumo:
        return resposta_sobre_resumo
    prefixos_secos = ("ok,", "ok.", "ok ", "certo,", "certo.", "certo ", "beleza,", "beleza.", "entendi,", "entendi.", "entendi ", "pronto,", "pronto.", "pronto ", "claro,", "claro.", "sim,", "sim.", "taí,", "tá,", "ta,", "de boa")
    lower = fala_limpa.lower()
    for p in prefixos_secos:
        if lower.startswith(p):
            fala_limpa = fala_limpa[len(p):].lstrip(" ,.!?").strip()
            lower = fala_limpa.lower()
            break

    fallback_neutro = bool(_call(ctx, "_fala_e_fallback_neutro", fala_limpa, default=False))
    if fala_limpa and not fallback_neutro:
        if _fala_operacional_indevida_em_resposta_neutra(ctx, fala_limpa, texto_limpo):
            return _ajustar(ctx, "Tranquilo. Então fico por aqui, sem puxar ação nem assunto antigo.", texto_limpo)
        fala_limpa = str(_call(ctx, "_ajustar_tom_por_emocao", fala_limpa, _get(ctx, "current_emotion", "calma"), texto_usuario, default=fala_limpa) or fala_limpa)
        return _ajustar(ctx, fala_limpa, texto_usuario)

    if pergunta_conhecimento_tema:
        # Sem uma resposta factual pronta nesta camada, não inventa nem troca
        # a pergunta por acolhimento genérico: deixa a IA principal responder.
        return ""

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

    if re.fullmatch(r"(?:oi|ola|olá|e ai|e aí|salve|bom dia|boa tarde|boa noite)(?: lay| laylay)?", texto_lower.strip()):
        return _ajustar(ctx, _fala_confirmacao(ctx, "greeting", "Oi, Pedro. To aqui contigo.", texto_usuario), texto_usuario)
    if any(p in texto_lower for p in ["precisa nao", "precisa não", "nao precisa", "não precisa", "agora nao", "agora não"]):
        return _ajustar(ctx, random.choice(["Fechado, sem ativar nada entao.", "Beleza, deixei quieto.", "Tranquilo. Nao mexo nisso agora."]), texto_usuario)
    opiniao_direta = _resposta_opiniao_com_tema(ctx, texto_usuario)
    if opiniao_direta:
        return opiniao_direta
    comentario_jogo = responder_comentario_jogo_em_foco(ctx, texto_usuario)
    if comentario_jogo:
        return comentario_jogo
    if "?" in texto_usuario:
        # Não transformar uma dúvida local em bloqueio da conversa. Uma
        # pergunta que esta camada não resolveu segue para a IA principal,
        # que possui o histórico e a fundamentação factual completos.
        return ""
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
            "Boa. Esse assunto rende fácil, e eu tô acompanhando teu fio.",
            "Aí sim, esse tema tem personalidade. Continua.",
            "Gostei. Esse papo tem chão; não precisa correr pra outro assunto.",
        ]), texto_usuario)
    # Se a propria IA produziu uma fala, preserva-a em vez de trocar um
    # preenchimento por outro. Sem fala local util, deixa o pre-fluxo seguir
    # para a IA principal, que possui o retrato completo da mente.
    if fala_original:
        return _ajustar(ctx, fala_original, texto_usuario)
    return ""


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
    if any(p in t for p in ["volta no assunto", "volta naquele assunto", "retoma o assunto", "retoma aquilo", "continua aquele assunto"]):
        return random.choice([
            f"Volto pra {ultimo_topico}. Era esse o fio que estava aberto.",
            f"Retomei {ultimo_topico}. Agora fico nesse assunto sem puxar outro.",
            f"Certo, de volta a {ultimo_topico}.",
        ])
    return ""


class ConversaNaturalRuntime:
    """Operações conversacionais sempre ligadas ao contexto vivo da mente."""

    def __init__(self, contexto_getter: Callable[[], Dict[str, Any]]) -> None:
        self._contexto_getter = contexto_getter

    def contexto(self) -> Dict[str, Any]:
        try:
            contexto = self._contexto_getter()
            return contexto if isinstance(contexto, dict) else {}
        except Exception as erro:
            print(f"⚠️ [CONVERSA:CONTEXTO] falha ao montar mente conversacional: {erro}")
            return {}

    def contexto_recente_indica_email(self) -> bool:
        return contexto_recente_indica_email(self.contexto())

    def responder_agradecimento_ou_elogio(self, texto_usuario: str) -> str:
        fala = responder_agradecimento_ou_elogio(self.contexto(), texto_usuario)
        return ajustar_proporcao_resposta(fala, texto_usuario, "conversa")

    def responder_conversa_curta_por_tipo(self, tipo: str, texto_usuario: str = "") -> str:
        fala = responder_conversa_curta_por_tipo(self.contexto(), tipo, texto_usuario)
        return ajustar_proporcao_resposta(fala, texto_usuario, "conversa")

    def construir_fala(self, fala: str, texto_usuario: str = "", tipo_interacao: str = "", comandos: Any = None) -> str:
        final = construir_fala_conversa(self.contexto(), fala, texto_usuario, tipo_interacao, comandos)
        return ajustar_proporcao_resposta(
            final,
            texto_usuario,
            tipo_interacao,
            possui_comandos=bool(comandos),
        )

    def resposta_local(self, texto_usuario: str) -> str:
        fala = resposta_conversa_local(self.contexto(), texto_usuario)
        return ajustar_proporcao_resposta(fala, texto_usuario, "conversa")

    def parece_elogio_ou_agradecimento_curto(self, texto_usuario: str) -> bool:
        return parece_elogio_ou_agradecimento_curto(self.contexto(), texto_usuario)

    def resposta_rapida_local(self, texto_usuario: str) -> str:
        fala = resposta_conversa_rapida_local(self.contexto(), texto_usuario)
        return ajustar_proporcao_resposta(fala, texto_usuario, "conversa")


def criar_conversa_natural_runtime(contexto_getter: Callable[[], Dict[str, Any]]) -> ConversaNaturalRuntime:
    return ConversaNaturalRuntime(contexto_getter)
