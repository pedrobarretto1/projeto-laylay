"""Qualidade semântica da fala sem substituir a personalidade da Laylay.

O módulo não escreve respostas normais nem decide ações. Ele detecta somente
falhas fortes de comunicação que justificam uma única nova tentativa da LLM:
frase interrompida, promessa sem entrega, fuga de uma pergunta direta e
conselho específico que não foi solicitado.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Iterable, Mapping

from mente_laylay.memoria_mental.memoria_confiavel import (
    extrair_aprendizados_pessoais_explicitos,
    normalizar_texto as normalizar_texto_memoria,
)
from mente_laylay.cognicao.validacao_contrato_fala import (
    validar_aderencia_contrato_fala,
)


_FINAL_INCOMPLETO = re.compile(
    r"(?:\b(?:mas|porque|porém|porem|então|entao|e|ou|que|se|quando|como|"
    r"apesar\s+de|só\s+que|so\s+que)\b|[:;,—-])\s*[.!?…]*$",
    re.IGNORECASE,
)
_RESPOSTA_VAZIA_DISFARCADA = re.compile(
    r"^(?:claro|sim|posso|vamos|beleza|tá|ta|certo|ah|a+h+|entendi)"
    r"[.!?…\s-]*$",
    re.IGNORECASE,
)
_PEDIDO_DE_ENTREGA = re.compile(
    r"\b(?:me\s+(?:manda|mande|mandar|dá|da|dar|mostra|mostre|mostrar|"
    r"explica|explique|explicar|descreve|descreva|descrever|fala|falar|diz|dizer)|"
    r"liste|lista|quais|como\s+funciona|passo\s+a\s+passo|"
    r"resolve|resolva|calcule|faz\s+uma\s+descri[cç][aã]o)\b",
    re.IGNORECASE,
)
_PERGUNTA_DE_POSICAO = re.compile(
    r"\b(?:voc[eê]|tu)\s+(?:gosta|curte|prefere|acha|pensa)\b|"
    r"\b(?:qual|quais)\s+(?:m[uú]sica|filme|jogo|livro).*(?:gosta|prefere)\b|"
    r"\btem\s+algum(?:a)?\s+(?:m[uú]sica|filme|jogo|livro)\b",
    re.IGNORECASE,
)
_MARCADORES_POSICAO = re.compile(
    r"\b(?:sim|n[aã]o|gosto|curto|prefiro|acho|iria|escolheria|conhe[cç]o|"
    r"me\s+parece|me\s+interessa|fico\s+curiosa)\b",
    re.IGNORECASE,
)
_EVASAO_OPINIAO = re.compile(
    r"\b(?:n[aã]o\s+(?:tenho|encontrei|achei)\s+(?:informa[cç][aã]o|dados)|"
    r"n[aã]o\s+posso\s+(?:opinar|dizer)|como\s+uma\s+ia)\b",
    re.IGNORECASE,
)
_RELATO_SEM_PEDIDO = re.compile(
    r"\b(?:eu\s+)?(?:estou|t[oô])\s+(?:pensando|planejando|querendo)\s+em\b|"
    r"\bacho\s+que\s+(?:eu\s+)?vou\b",
    re.IGNORECASE,
)
_CONSELHO_LIMPEZA_ESPECIFICO = re.compile(
    r"\b(?:use|usa|coloque|coloca|adicione|adiciona|misture|mistura|jogue|joga)\b"
    r"[^.!?]{0,100}\b(?:sal|cloro|[aá]gua\s+sanit[aá]ria|vinagre|amon[ií]aco|"
    r"detergente|sab[aã]o|produto|marca)\b",
    re.IGNORECASE,
)
_MARCADORES_MUSICA = re.compile(
    r"\b(?:m[uú]sica|faixa|som|banda|artista|cantor|cantora|[aá]lbum|rock|"
    r"metal|grunge|guitarra|vocal|refr[aã]o|discografia)\b",
    re.IGNORECASE,
)
_DERIVA_FILOSOFICA = re.compile(
    r"\b(?:estado\s+de\s+paz|ilumina[cç][aã]o|liberta[cç][aã]o|sofrimento|"
    r"budismo|espiritual|consci[eê]ncia|equil[ií]brio\s+interior)\b",
    re.IGNORECASE,
)
_RECONHECIMENTO_PESSOAL = re.compile(
    r"\b(?:boa|legal|justo|faz\s+sentido|combina|anotado|"
    r"gosto\s+respeit[aá]vel|n[aã]o\s+[ée]\s+muito\s+a\s+sua)\b",
    re.IGNORECASE,
)
_PREFERENCIA_DE_TERCEIRO = re.compile(
    r"\b(?:minha|meu)\s+(?:namorad[oa]|esposa|marido|amig[oa]|irm[aã]o|"
    r"irm[aã]|m[aã]e|pai|prim[oa])\s+gosta\s+(?:de|do|da|dos|das)\s+"
    r"(?P<valor>[^,.!?]{2,80})",
    re.IGNORECASE,
)
_REFERENTE_SEM_ANCORA = re.compile(
    r"\b(?:o|a)\s+outr[oa]\s+que\b|"
    r"\b(?:esse|essa|isso)\s+(?:neg[oó]cio|coisa|tro[cç]o)\b",
    re.IGNORECASE,
)
_PEDIDO_DE_CLAREZA = re.compile(
    r"^\s*(?:como\s+assim|por\s+qu[eê]|o\s+que\s+(?:voc[eê]\s+)?quis\s+dizer|"
    r"n[aã]o\s+entendi|explica\s+(?:isso\s+)?melhor)\s*[?!.…]*\s*$",
    re.IGNORECASE,
)
_EXPLICACAO_NEBULOSA = re.compile(
    r"\b(?:[ée]\s+s[oó]\s+uma\s+vibe|[ée]\s+como\s+se|tipo\s+uma\s+coisa|"
    r"som\s+de\s+aparelho|energia\s+do\s+universo)\b",
    re.IGNORECASE,
)
_MARCADORES_EXPLICACAO_LITERAL = re.compile(
    r"\b(?:quis\s+dizer|em\s+outras\s+palavras|falando\s+direto|"
    r"de\s+forma\s+simples|literalmente|o\s+ponto\s+[ée])\b",
    re.IGNORECASE,
)
_ESTADO_PESSOAL = re.compile(
    r"\b(?:eu\s+)?(?:estou|to|tô)\s+(?:um\s+pouco\s+|meio\s+)?"
    r"(?P<estado>cansad[oa]|triste|mal|preocupad[oa]|ansios[oa]|feliz|animad[oa])\b",
    re.IGNORECASE,
)
_RECONHECIMENTO_ESTADO = re.compile(
    r"\b(?:cans|trist|preocup|ansios|feliz|animad|imagino|poxa|pesou|"
    r"pesado|entendo|pega\s+leve|vai\s+com\s+calma|descans|bom\s+saber|"
    r"que\s+bom|eu\s+ouvi)\b",
    re.IGNORECASE,
)
_NARRACAO_MECANICA = re.compile(
    r"\b(?:a\s+pergunta\s+[ée]|a\s+resposta\s+direta\s+[ée]|"
    r"como\s+uma\s+ia|sou\s+s[oó]\s+uma\s+conversa|"
    r"t[oô]\s+aqui\s+no\s+terminal|o\s+sistema\s+(?:quer|est[aá])\s+responder)\b",
    re.IGNORECASE,
)
_CONTEXTO_TECNICO_USUARIO = re.compile(
    r"\b(?:terminal|python|prompt|sistema|ia|intelig[eê]ncia\s+artificial|c[oó]digo)\b",
    re.IGNORECASE,
)
_ENFEITE_POETICO = re.compile(
    r"\b(?:alma|universo|neblina|estrelas?|poema|sil[eê]ncio\s+com\s+sabor|"
    r"cora[cç][aã]o\s+batendo|luz\s+da\s+lua|mundo\s+se\s+curva)\b",
    re.IGNORECASE,
)
_PEDIDO_CRIATIVO = re.compile(
    r"\b(?:poema|poesia|hist[oó]ria|conto|criativ[oa]|met[aá]fora|descri[cç][aã]o\s+art[ií]stica|"
    r"letra\s+de\s+m[uú]sica|imagina|imagine)\b",
    re.IGNORECASE,
)
_PERGUNTA_SOCIAL_LAYLAY = re.compile(
    r"\b(?:tudo\s+bem\s+(?:com\s+)?voc[eê]|como\s+(?:voc[eê]|a\s+laylay)\s+"
    r"(?:est[aá]|vai)|e\s+(?:voc[eê]|a\s+laylay))\b",
    re.IGNORECASE,
)
_CONSELHO_PRESCRITIVO = re.compile(
    r"\b(?:respira|respire|fa[cç]a|faz\s+isso|tenta|tente|voc[eê]\s+(?:precisa|deveria)|"
    r"segura\s+\d+|expira|inspire|medite|beba\s+[aá]gua)\b",
    re.IGNORECASE,
)


def _normalizar(texto: Any) -> str:
    return re.sub(r"\s+", " ", str(texto or "")).strip()


def _foco_do_plano(plano: Mapping[str, Any] | None) -> Dict[str, Any]:
    contrato = dict(plano or {})
    referencia = dict(contrato.get("referencia_resolvida") or {})
    if referencia.get("nome"):
        return {
            "nome": str(referencia.get("nome") or "").strip(),
            "tipo": str(referencia.get("tipo") or "").strip().casefold(),
            "dominio": str(contrato.get("dominio") or "conversa").strip().casefold(),
            "origem": str(referencia.get("origem") or "referencia_resolvida"),
        }
    entidades = dict(contrato.get("entidades") or {})
    musica_tipos = ("artista", "banda", "cantor", "cantora", "musica")
    for chave in musica_tipos:
        item = entidades.get(chave)
        if isinstance(item, Mapping) and item.get("nome"):
            return {
                "nome": str(item.get("nome") or "").strip(),
                "tipo": str(item.get("tipo") or chave).strip().casefold(),
                "dominio": "musica",
                "origem": str(item.get("origem") or "entidades_turno"),
            }
    return {}


def avaliar_qualidade_comunicacao(
    texto_usuario: str,
    fala: str,
    *,
    plano: Mapping[str, Any] | None = None,
    ultima_resposta: str = "",
) -> Dict[str, Any]:
    """Retorna problemas fortes; não corrige estilo nem conteúdo por conta própria."""
    usuario = _normalizar(texto_usuario)
    resposta = _normalizar(fala)
    problemas: list[str] = []
    foco = _foco_do_plano(plano)
    resposta_anterior = _normalizar(ultima_resposta)
    plano_atual = dict(plano or {})
    aderencia_contrato = {
        "avaliado": False,
        "aceita": True,
        "requer_reparo": False,
        "problemas": [],
        "estrategia": "",
        "contrato_reparo": {},
        "autoriza_execucao": False,
    }

    if not resposta:
        problemas.append("fala_vazia")
    else:
        palavras = re.findall(r"[\wÀ-ÿ]+", resposta, flags=re.UNICODE)
        if _FINAL_INCOMPLETO.search(resposta) or _RESPOSTA_VAZIA_DISFARCADA.fullmatch(resposta):
            problemas.append("resposta_incompleta")
        if _PEDIDO_DE_ENTREGA.search(usuario) and len(palavras) < 7:
            problemas.append("entrega_prometida_ausente")
        if (
            _PERGUNTA_DE_POSICAO.search(usuario)
            and not _MARCADORES_POSICAO.search(resposta)
        ):
            problemas.append("pergunta_direta_nao_respondida")
        if _PERGUNTA_DE_POSICAO.search(usuario) and _EVASAO_OPINIAO.search(resposta):
            problemas.append("opiniao_evitada_sem_necessidade")
        if (
            _RELATO_SEM_PEDIDO.search(usuario)
            and "?" not in usuario
            and _CONSELHO_LIMPEZA_ESPECIFICO.search(resposta)
        ):
            problemas.append("conselho_especifico_nao_solicitado")

        tipo_foco = str(foco.get("tipo") or "")
        dominio_foco = str(foco.get("dominio") or "")
        foco_musical = dominio_foco == "musica" or tipo_foco in {
            "artista", "banda", "cantor", "cantora", "musica",
            "referencia_nomeada",
        }
        if (
            foco_musical
            and _PERGUNTA_DE_POSICAO.search(usuario)
            and _DERIVA_FILOSOFICA.search(resposta)
            and not _MARCADORES_MUSICA.search(resposta)
        ):
            problemas.append("deriva_de_dominio")

        # Uma declaração pessoal simples precisa ser reconhecida literalmente.
        # Criatividade sem citar o gosto ou sem um reconhecimento claro soa como
        # uma associação aleatória, mesmo quando a frase está gramaticalmente inteira.
        preferencias = extrair_aprendizados_pessoais_explicitos(usuario)
        if preferencias:
            valores = [
                normalizar_texto_memoria(item.get("valor"))
                for item in preferencias
                if str(item.get("valor") or "").strip()
            ]
            resposta_semantica = normalizar_texto_memoria(resposta)
            reconheceu_valor = any(
                valor and valor in resposta_semantica
                for valor in valores
            )
            if not reconheceu_valor and not _RECONHECIMENTO_PESSOAL.search(resposta):
                problemas.append("preferencia_pessoal_nao_reconhecida")

        terceiro = _PREFERENCIA_DE_TERCEIRO.search(usuario)
        if terceiro:
            valor_terceiro = normalizar_texto_memoria(terceiro.group("valor"))
            resposta_semantica = normalizar_texto_memoria(resposta)
            atribuiu_ao_usuario = bool(re.search(
                rf"\b(?:voce|tu)\b.{{0,35}}\b(?:gosta|curte|ama|tem|ta\s+com)\b"
                rf".{{0,25}}\b{re.escape(valor_terceiro)}\b",
                resposta_semantica,
            ))
            if atribuiu_ao_usuario:
                problemas.append("preferencia_de_terceiro_atribuida_ao_usuario")

        # Pronomes como "o outro que..." sem um substantivo identificável são
        # uma fonte recorrente de frases que parecem espirituosas, mas não dizem nada.
        if _REFERENTE_SEM_ANCORA.search(resposta):
            problemas.append("referente_indefinido_na_resposta")

        # Ao pedir esclarecimento, o usuário precisa receber uma paráfrase literal
        # da fala anterior. Empilhar outra metáfora só aprofunda a confusão.
        if (
            _PEDIDO_DE_CLAREZA.fullmatch(usuario)
            and resposta_anterior
            and _EXPLICACAO_NEBULOSA.search(resposta)
            and not _MARCADORES_EXPLICACAO_LITERAL.search(resposta)
        ):
            problemas.append("explicacao_permaneceu_nebulosa")

        estado_pessoal = _ESTADO_PESSOAL.search(usuario)
        if estado_pessoal and not _RECONHECIMENTO_ESTADO.search(resposta):
            problemas.append("estado_pessoal_nao_reconhecido")

        if resposta.count("?") > 1:
            problemas.append("perguntas_em_excesso")

        if _NARRACAO_MECANICA.search(resposta) and not _CONTEXTO_TECNICO_USUARIO.search(usuario):
            problemas.append("narracao_mecanica_da_resposta")

        enfeites = _ENFEITE_POETICO.findall(resposta)
        assunto_poetico = bool(_PEDIDO_CRIATIVO.search(usuario) or _ENFEITE_POETICO.search(usuario))
        if len(enfeites) >= 2 and not assunto_poetico:
            problemas.append("poesia_decorativa_sem_contexto")

        if _PERGUNTA_SOCIAL_LAYLAY.search(usuario):
            if _CONSELHO_PRESCRITIVO.search(resposta):
                problemas.append("conselho_nao_solicitado_em_pergunta_social")
            frases_sociais = [
                parte for parte in re.split(r"(?<=[.!?…])\s+", resposta)
                if parte.strip()
            ]
            if len(frases_sociais) > 3 or len(resposta.split()) > 48:
                problemas.append("resposta_social_desproporcional")

        aderencia_contrato = validar_aderencia_contrato_fala(
            usuario,
            resposta,
            contrato_fala=plano_atual.get("contrato_fala"),
            ultima_resposta=resposta_anterior,
        )
        problemas.extend(aderencia_contrato.get("problemas") or [])

    problemas = list(dict.fromkeys(problemas))
    return {
        "aceita": not problemas,
        "requer_reparo": bool(problemas),
        "problemas": problemas,
        "foco": foco,
        "ultima_resposta": resposta_anterior[:700],
        "pontuacao": max(0.0, 1.0 - (0.25 * len(problemas))),
        "aderencia_contrato": aderencia_contrato,
        "contrato_reparo": dict(aderencia_contrato.get("contrato_reparo") or {}),
    }


def selecionar_contexto_imediato(
    mensagens: Iterable[Mapping[str, Any]] | None,
    *,
    limite: int = 4,
) -> list[dict[str, str]]:
    """Seleciona só a troca recente; memória longa não entra no reparo."""
    uteis: list[dict[str, str]] = []
    for item in list(mensagens or []):
        if not isinstance(item, Mapping):
            continue
        papel = str(item.get("role") or "").strip().casefold()
        conteudo = _normalizar(item.get("content"))
        if papel not in {"user", "assistant"} or not conteudo:
            continue
        uteis.append({"role": papel, "content": conteudo[:700]})
    return uteis[-max(1, int(limite or 4)):]


def montar_mensagens_reparo_comunicacao(
    texto_usuario: str,
    fala_rejeitada: str,
    avaliacao: Mapping[str, Any],
    *,
    mensagens: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, str]]:
    """Cria uma única tentativa de reparo, pequena e sem autorização prática."""
    payload = {
        "mensagem_atual": _normalizar(texto_usuario)[:900],
        "rascunho_rejeitado": _normalizar(fala_rejeitada)[:1200],
        "problemas": list(avaliacao.get("problemas") or []),
        "foco_confirmado": dict(avaliacao.get("foco") or {}),
        "fala_anterior": _normalizar(avaliacao.get("ultima_resposta"))[:700],
        "contrato_de_reparo": dict(avaliacao.get("contrato_reparo") or {}),
        "troca_recente": selecionar_contexto_imediato(mensagens),
    }
    instrucao = (
        "Você está reparando uma resposta da Laylay, não iniciando outro assunto. "
        "Responda à mensagem atual de forma natural, completa e proporcional. Preserve "
        "o foco confirmado e use a troca recente apenas quando ela for relevante. Não "
        "invente lembranças, experiências físicas, títulos, artistas, produtos, marcas ou "
        "conselhos específicos. Não prometa responder depois e não termine só com uma "
        "introdução. Não execute nem sugira comandos. Mantenha a personalidade carismática, "
        "atenta e debochada com carinho quando combinar; uma tirada basta e nunca substitui "
        "a resposta. Reconheça literalmente preferências e relatos pessoais antes de reagir. "
        "Se o usuário contar como está, reconheça esse estado com palavras concretas. "
        "Nomeie os assuntos em vez de usar referentes soltos como 'o outro'. Se a mensagem "
        "pedir esclarecimento, diga primeiro em linguagem direta o que a fala anterior quis "
        "dizer; não tente explicar uma metáfora com outra. Não narre o ato de responder, não "
        "fale do terminal sem ter sido perguntada e faça no máximo uma pergunta. Evite poesia "
        "decorativa fora de pedidos criativos. A resposta deve continuar clara "
        "mesmo sem tom de voz. Se o payload trouxer contrato_de_reparo, cumpra o núcleo "
        "já na primeira frase, siga a sequência indicada e não ultrapasse max_frases. "
        "Quando a estratégia for resposta_multiacto, cada item de atos_obrigatorios "
        "e da sequência é obrigatório: não responda apenas à primeira parte da mensagem. "
        "Retorne somente JSON válido no "
        'formato {"fala":"resposta completa","comandos":[]}.'
    )
    return [
        {"role": "system", "content": instrucao},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def contingencia_comunicacao(
    texto_usuario: str,
    *,
    foco: Mapping[str, Any] | None = None,
    contrato_reparo: Mapping[str, Any] | None = None,
) -> str:
    """Último recurso contextual quando a única tentativa de reparo também falha."""
    texto = _normalizar(texto_usuario)
    nome = str(dict(foco or {}).get("nome") or "").strip()
    contrato = dict(contrato_reparo or {})
    estrategia = str(contrato.get("estrategia") or "").strip()
    atos = {str(item or "").casefold() for item in contrato.get("atos_obrigatorios") or []}
    referente = str(contrato.get("referente") or "").strip()

    # Em uma fala composta, a contingência não pode escolher só a saudação ou
    # o estado pessoal e abandonar a pergunta seguinte. Se até o reparo único
    # falhou, preservamos todos os atos e declaramos somente a incerteza real.
    if estrategia == "resposta_multiacto":
        reconhecimento = "Que bom saber. " if "estado_pessoal" in atos else ""
        if "opiniao" in atos and referente:
            opcoes = [
                parte.strip(" .,!?:;\"'")
                for parte in re.split(r"\s+ou\s+", referente, flags=re.I)
                if parte.strip(" .,!?:;\"'")
            ]
            if len(opcoes) >= 2:
                # A contingência ainda representa a personalidade da Laylay.
                # Uma assinatura estável torna a escolha consistente mesmo se
                # o usuário inverter a ordem das opções em outro turno.
                canonicas = sorted(opcoes, key=str.casefold)
                assinatura = "laylay|" + "|".join(
                    opcao.casefold() for opcao in canonicas
                )
                indice = hashlib.sha256(assinatura.encode("utf-8")).digest()[0]
                escolhida = canonicas[indice % len(canonicas)]
                return (
                    f"{reconhecimento}Eu prefiro {escolhida}, porque combina mais "
                    "com meu jeito direto e ainda dá espaço para bastante variedade."
                )
            return (
                f"{reconhecimento}Eu gosto mais de {referente}, porque é o que "
                "mais combina com meu jeito direto."
            )
        return (
            f"{reconhecimento}Eu não consegui concluir todas as partes dessa resposta "
            "sem inventar; prefiro assumir isso a ignorar metade do que você disse."
        )
    estado_pessoal = _ESTADO_PESSOAL.search(texto)
    if estado_pessoal:
        estado = str(estado_pessoal.group("estado") or "").casefold()
        if estado.startswith("cans"):
            return "Poxa, então pega mais leve hoje. Você não precisa funcionar no máximo o tempo todo."
        if estado.startswith("trist") or estado == "mal":
            return "Poxa. Eu ouvi que você não tá bem; não vou tentar cobrir isso com frase bonita."
        if estado.startswith("preocup") or estado.startswith("ansios"):
            return "Entendo. Parece que isso tá ocupando espaço demais na sua cabeça hoje."
        if estado.startswith("feliz") or estado.startswith("animad"):
            return "Boa, dá pra sentir que você tá num dia melhor."
    preferencias = extrair_aprendizados_pessoais_explicitos(texto)
    if preferencias:
        regra = str(preferencias[0].get("regra") or "").strip()
        if regra:
            return f"Peguei: {regra}."
    preferencia_terceiro = re.search(
        r"\b(?:minha|meu)\s+(?P<relacao>namorada|namorado|esposa|marido|"
        r"amiga|amigo|irma|irmã|irmao|irmão)\s+gosta\s+(?:de|do|da|dos|das)\s+"
        r"(?P<valor>[^,.!?;]{2,80})",
        texto,
        re.I,
    )
    if preferencia_terceiro:
        relacao = str(preferencia_terceiro.group("relacao") or "essa pessoa").strip()
        valor = str(preferencia_terceiro.group("valor") or "").strip()
        return f"Entendi — sua {relacao} gosta de {valor}."
    if re.search(r"\b(?:tudo\s+bem|como\s+(?:voc[eê]|vai\s+voc[eê]))\b", texto, re.I):
        return "Tô bem por aqui. E você, como tá?"
    if re.search(r"\b(?:eu\s+)?(?:estou|t[oô])\s+bem\b", texto, re.I):
        return "Que bom. Fico feliz de saber."
    if _PERGUNTA_DE_POSICAO.search(texto) and nome:
        return f"{nome} me interessa, mas não vou inventar um detalhe só para deixar a resposta bonita."
    if _PEDIDO_DE_ENTREGA.search(texto):
        return "Eu não consegui fechar essa resposta com a qualidade que você pediu. Prefiro não te entregar só metade."
    if re.search(r"\b(?:obrigad[oa]|valeu|vlw)\b", texto, re.I):
        return "Imagina. Fico feliz que tenha ajudado."
    if re.search(r"(?:\bkk+k*\b|\brsrs+\b|😂|🤣)", texto, re.I):
        return "Kkkkk, tá bom, essa me pegou."
    if re.search(r"\b(?:faz sentido|concordo|justo)\b", texto, re.I):
        return "Justo. Dessa vez a gente tá na mesma página."
    if re.search(r"\bdiscordo\b|\bn[aã]o concordo\b", texto, re.I):
        return "Justo. Você não precisa concordar comigo pra conversa continuar boa."
    if "?" in texto:
        return "Pera, minha resposta saiu torta e eu não vou inventar uma resposta só pra preencher o silêncio."
    return "Pera, eu li isso, mas minha resposta saiu torta. Não vou fingir que encaixou."
