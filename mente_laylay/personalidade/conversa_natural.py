"""Conversa curta e fala natural da Laylay.

Este modulo nao executa comandos. Ele interpreta e responde conversa curta
usando o estado mental compartilhado recebido pelo `ctx`.
"""

from __future__ import annotations

import json
import random
import re
import time
from typing import Any, Callable, Dict

from mente_laylay.personalidade.proporcao_resposta import ajustar_proporcao_resposta
from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
from mente_laylay.emocoes.leitura_usuario import analisar_intencao_emocional
from mente_laylay.memoria_mental.continuidade_conversa import assunto_coerente_com_fala
from mente_laylay.cognicao.conversa_sobre_capacidades import (
    resposta_conversa_sobre_capacidade,
    resposta_continuacao_capacidade_futura,
    texto_discute_capacidade_futura,
)
from mente_laylay.cognicao.interpretacao_social import analisar_ato_social
from mente_laylay.personalidade.classificacao_conversa import (
    analisar_conversa_curta_ia,
    classificar_conversa_curta_local,
    deve_classificar_conversa_curta_com_ia,
    ha_pendencia_operacional_ativa as _ha_pendencia_operacional_ativa,
    recusa_tem_continuacao as _recusa_tem_continuacao,
)
from mente_laylay.personalidade.continuidade_conversa_natural import (
    _fala_operacional_indevida_em_resposta_neutra,
    _registro_resumo_recente,
    _responder_pergunta_sobre_ultimo_resumo,
    _resposta_confirmacao_resumo_curto,
    _resposta_continuacao_capacidade,
    contexto_recente_indica_email,
    resposta_pergunta_curta_dependente_topico,
    retomar_topico_quando_fluido,
)


from mente_laylay.personalidade.base_conversa import (
    _ajustar,
    _call,
    _fala_confirmacao,
    _get,
    _normalizar,
    _normalizar_apelidos,
    _topico_para_fala,
    contexto_fala_curta,
)

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
    padroes_genericos = [
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
    # Esses marcadores identificam falha real mesmo quando a frase inclui um
    # pequeno complemento. Já expressões como "tô aqui" só são genéricas se
    # forem o começo de uma resposta curta; procurá-las em qualquer posição
    # descartava falas boas como "Tudo certo... tô aqui pra escutar você".
    marcadores_falha = [
        "nao consegui encaixar isso direito",
        "não consegui encaixar isso direito",
        "me perdi um pouco nessa resposta",
        "minha conexao com a parte da ia falhou",
        "minha conexão com a parte da ia falhou",
        "modelo local demorou demais",
    ]
    if any(p in t for p in marcadores_falha):
        return True
    palavras = t.split()
    return len(palavras) <= 12 and any(
        re.match(rf"^{re.escape(padrao)}(?:\b|[.!?,;:])", t)
        for padrao in padroes_genericos
    )


from mente_laylay.personalidade.leitura_social_conversa import (
    _normalizar_reconhecimento,
    parece_elogio_ou_agradecimento_curto,
    parece_pedido_para_acalmar,
    tipo_reconhecimento_afetivo,
)
from mente_laylay.personalidade.respostas_afetivas import (
    responder_agradecimento_ou_elogio,
    responder_pedido_para_acalmar,
)


from mente_laylay.personalidade.contingencias_conversa import (
    resolver_equacao_linear_local,
    responder_matematica_simples,
)


from mente_laylay.personalidade.leitura_social_conversa import (
    _parece_confirmacao_curta,
    _parece_correcao_conversa,
    texto_parece_correcao_conversacional,
)


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


def resposta_curta_contextual(ctx: Dict[str, Any], texto_usuario: str, tipo: str = "") -> str:
    t = _normalizar(ctx, texto_usuario)
    tipo_norm = str(tipo or "").upper().strip()
    mente = dict(_get(ctx, "mente_integrada_estado", {}) or {})
    ultima_resposta = str(mente.get("ultima_resposta") or "").strip()
    ultima_resposta_norm = _normalizar(ctx, ultima_resposta)
    ultimo_topico = str(_get(ctx, "ultimo_topico_conversa", "") or "").strip()
    foco = dict(_get(ctx, "foco_vivo", {}) or {})
    foco_tipo = str(foco.get("tipo") or "").strip().lower()
    foco_topico = _topico_para_fala(foco.get("topico") or foco.get("alvo") or "")
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
        "A outra pessoa é o usuário; nunca a chame de Laylay e nunca fale consigo mesma como interlocutora. "
        "Escolha uma posicao clara e explique o motivo em uma ou duas frases naturais. "
        "Nao concorde automaticamente com o usuário e nao discorde so para parecer forte. "
        "Diferencie gosto pessoal de fato; se os fatos forem insuficientes, assuma a incerteza sem ficar em cima do muro. "
        "FATOS_DISPONIVEIS e um limite fechado: nao acrescente cargo, partido, crime, diagnostico, morte, "
        "parentesco, premio, data ou episodio biografico que nao esteja escrito ali. "
        "Se o usuário trouxe informacao melhor que contradiz a opiniao anterior, voce pode mudar de ideia e dizer brevemente por que. "
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
        return _ajustar(ctx, _fala_confirmacao(ctx, "greeting", "Oi. To aqui contigo.", texto_usuario), texto_usuario)
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
        if emocao == "culpa":
            return _ajustar(ctx, random.choice([
                "Essa culpa sem um motivo claro pesa mesmo. Não vou te absolver nem te culpar no automático; quando esse peso começou a apertar?",
                "Entendi. Antes de dizer que você tem ou não tem culpa, quero separar a sensação do que aconteceu. Você lembra quando isso começou?",
                "Eu ouvi esse peso. Não quero preencher o que falta com suposição; teve algum momento específico que trouxe essa culpa?",
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
        if _recusa_tem_continuacao(texto_usuario) or not _ha_pendencia_operacional_ativa(ctx):
            return ""
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
    if bool(_get(ctx, "_voz_unica_llm", False)):
        # No fluxo de voz única, o Python não estiliza, encurta, completa ou
        # substitui uma conversa válida. Ele remove somente resíduos técnicos;
        # personalidade, emoção e escolha de palavras pertencem à LLM.
        fala_limpa = remover_residuos_operacionais(fala_limpa)
        if not fala_limpa or bool(
            _call(ctx, "_fala_e_fallback_neutro", fala_limpa, default=False)
        ):
            return ""
        return fala_limpa
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
        return _ajustar(ctx, _fala_confirmacao(ctx, "greeting", "Oi. To aqui contigo.", texto_usuario), texto_usuario)
    if (
        any(p in texto_lower for p in ["precisa nao", "precisa não", "nao precisa", "não precisa", "agora nao", "agora não"])
        and not _recusa_tem_continuacao(texto_lower)
        and _ha_pendencia_operacional_ativa(ctx)
    ):
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
    if texto_parece_correcao_conversacional(texto_usuario):
        return ""
    if parece_elogio_ou_agradecimento_curto(ctx, texto_usuario):
        return responder_agradecimento_ou_elogio(ctx, texto_usuario)
    if parece_pedido_para_acalmar(ctx, texto_usuario):
        return responder_pedido_para_acalmar(ctx, texto_usuario)
    resposta_matematica = responder_matematica_simples(ctx, texto_usuario)
    if resposta_matematica:
        return resposta_matematica
    return resposta_conversa_local(ctx, texto_usuario)


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
