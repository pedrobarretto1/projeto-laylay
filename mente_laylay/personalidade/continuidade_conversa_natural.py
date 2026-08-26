"""Continuidade, referências e resumos da conversa natural."""

from __future__ import annotations

import json
import random
import re
import time
from typing import Any, Dict

from mente_laylay.cognicao.conversa_sobre_capacidades import (
    resposta_continuacao_capacidade_futura,
)
from mente_laylay.memoria_mental.continuidade_conversa import assunto_coerente_com_fala
from mente_laylay.personalidade.base_conversa import (
    _ajustar,
    _call,
    _get,
    _normalizar,
    _topico_para_fala,
)
from mente_laylay.personalidade.leitura_social_conversa import (
    _parece_confirmacao_curta,
    _parece_correcao_conversa,
)

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

def _pede_explicacao_da_fala_anterior(texto_normalizado: str) -> bool:
    """Distingue uma referência elíptica de uma pergunta com assunto novo."""
    t = re.sub(r"\s+", " ", str(texto_normalizado or "")).strip(" .!?;:")
    if not t:
        return False
    if re.fullmatch(
        r"(?:como assim|o que (?:voce|você) quis dizer|"
        r"(?:pode\s+)?(?:me\s+)?explica(?:r)?(?:\s+melhor)?(?:\s+(?:isso|aquilo|"
        r"essa parte|o que (?:voce|você) disse))?(?:\s+(?:melhor|com mais detalhes|"
        r"mais detalhadamente))?)",
        t,
    ):
        return True
    return bool(re.fullmatch(
        r"(?:ue|ué|uai|oxi|que isso|que foi isso|o que foi isso|como assim isso|por que|porque|pq)"
        r"(?:\s+(?:nao|não))?(?:\s+(?:isso|aquilo))?",
        t,
    ))


def _pede_detalhamento_da_fala_anterior(texto_normalizado: str) -> bool:
    """Reconhece pedidos de expansão, inclusive a formulação longa real.

    Não basta identificar que existe uma referência: este pedido precisa usar a
    resposta anterior como fonte, em vez de recair num tópico histórico.
    """
    t = re.sub(r"\s+", " ", str(texto_normalizado or "")).strip(" .!?;:")
    return bool(re.fullmatch(
        r"(?:agora\s+)?(?:pode\s+)?(?:me\s+)?(?:explica|explique|detalha|detalhe)"
        r"(?:\s+(?:isso|aquilo|essa parte|o que (?:voce|você) disse))?"
        r"\s+(?:melhor|com mais detalhes|mais detalhadamente|"
        r"de (?:um )?jeito (?:simples|f[aá]cil|claro)|"
        r"de forma (?:simples|f[aá]cil|clara))",
        t,
    ))


def _expandir_fala_anterior(
    ctx: Dict[str, Any],
    *,
    texto_usuario: str,
    assunto: str,
    fala_anterior: str,
    ideia: str,
) -> str:
    """Pede uma expansão limitada e verificável da fala imediatamente anterior."""
    if not fala_anterior:
        return ""
    payload = {
        "pedido": str(texto_usuario or "").strip(),
        "assunto": str(assunto or "").strip(),
        "fala_anterior": fala_anterior[:900],
        "ponto_central": str(ideia or "").strip()[:500],
    }
    prompt = (
        "Expanda apenas a resposta imediatamente anterior da Laylay, em português. "
        "Preserve o assunto informado e não troque para memórias, comandos ou temas antigos. "
        "Não invente fatos: explique o ponto central com duas ou três frases úteis. "
        "Retorne somente JSON válido: {\"fala\":\"...\"}."
    )
    try:
        bruto = _call(
            ctx,
            "enviar_mensagem",
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            _com_tools=False,
            max_tokens=260,
            modo_rapido=True,
            default="",
        )
        extraido = _call(ctx, "_extrair_json_da_ia", bruto, default=bruto)
        dados = json.loads(extraido) if extraido else {}
        fala = str(dados.get("fala") or "").strip() if isinstance(dados, dict) else ""
        if fala:
            return _ajustar(ctx, fala, texto_usuario)
    except Exception as exc:
        print(f"⚠️ [CONVERSA:CONTINUIDADE] detalhamento local indisponível: {type(exc).__name__}")

    # A degradação preserva explicitamente o mesmo referente. É preferível a
    # uma frase genérica que dê a impressão de ter perdido o fio.
    base = ideia or fala_anterior
    prefixo = f"Sobre {assunto}, " if assunto else "Sobre o que eu acabei de dizer, "
    return _ajustar(
        ctx,
        f"{prefixo}o ponto central é este: {base}. Não quero puxar outro assunto enquanto você está pedindo esse detalhe.",
        texto_usuario,
    )

def resposta_pergunta_curta_dependente_topico(ctx: Dict[str, Any], texto_usuario: str) -> str:
    t = _normalizar(ctx, texto_usuario)
    pede_detalhamento = _pede_detalhamento_da_fala_anterior(t)
    pede_explicacao = _pede_explicacao_da_fala_anterior(t) or pede_detalhamento
    if not t or (len(t.split()) > 10 and not pede_explicacao):
        return ""

    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    ultima_resposta = str(mente.get("ultima_resposta") or "").strip()
    ultima_resposta_norm = _normalizar(ctx, ultima_resposta)
    ultima_intencao = str(mente.get("ultima_acao_intent") or mente.get("ultima_intencao") or "").strip().upper()
    ultimo_status = str(mente.get("ultima_acao_status") or "").strip().lower()
    ultimo_alvo = str(
        mente.get("ultima_acao_alvo")
        or mente.get("ultimo_alvo")
        or mente.get("ultimo_app_janela")
        or mente.get("ultimo_site_aba")
        or ""
    ).strip()
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
    foco_topico = _topico_para_fala(foco.get("topico") or foco.get("alvo") or "")
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

    # Repara localmente a tirada específica que motivou esta regressão. O
    # esclarecimento precisa explicar a intenção e retirar a acusação implícita,
    # não apenas repetir a mesma piada com outras palavras.
    brincadeira_codigo_torta = (
        "bug" in ultima_resposta_norm
        and any(termo in ultima_resposta_norm for termo in ("codigo", "código"))
        and any(
            trecho in ultima_resposta_norm
            for trecho in (
                "nao consigo ler", "não consigo ler",
                "nem eu consigo ler", "vai virar",
            )
        )
    )
    if pede_explicacao and continuidade_idade <= 300 and brincadeira_codigo_torta:
        return _ajustar(ctx, random.choice([
            "Foi uma brincadeira meio torta. Eu quis dizer que mexer no meu código pode revelar bugs ou trechos confusos. Não estava dizendo que você vai estragar alguma coisa.",
            "Eu forcei a piada e ela ficou parecendo uma crítica. O ponto era só que mexer no meu código pode expor bugs e partes difíceis de ler, não que a culpa seria sua.",
            "Aquilo foi uma tirada mal colocada. Eu estava brincando com os bugs que podem aparecer no meu código, não dizendo que você escreve código ruim.",
        ]), texto_usuario)

    if pede_detalhamento and continuidade_idade <= 300 and ultima_resposta:
        assunto = assunto_da_fala or topico
        assunto_valido = assunto_coerente_com_fala(
            assunto,
            ultima_opiniao or ultima_afirmacao,
            ultima_resposta,
            normalizar_texto=lambda valor: _normalizar(ctx, valor),
        )
        return _expandir_fala_anterior(
            ctx,
            texto_usuario=texto_usuario,
            assunto=assunto if assunto_valido else "",
            fala_anterior=ultima_resposta,
            ideia=ultima_opiniao or ultima_afirmacao,
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

    status_falhou = (
        ultimo_status in {
            "falhou", "falha_execucao", "nao_encontrado", "não_encontrado",
            "app_aberto_sem_foco", "alvo_ambiguo", "alvo_ausente",
            "referencia_nao_resolvida", "indisponivel",
        }
        or any(marcador in ultimo_status for marcador in ("falha", "erro", "indispon"))
    )
    if status_falhou:
        alvo = ultimo_alvo or "isso"
        if ultimo_status == "alvo_ambiguo":
            return _ajustar(
                ctx,
                f"Porque encontrei mais de um item que poderia ser {alvo}. Não apaguei nada sem um caminho exato.",
                texto_usuario,
            )
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

