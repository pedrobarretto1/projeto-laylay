"""Continuidade conversacional, perguntas e ofertas pendentes."""

from __future__ import annotations

import re
import time
from typing import Any, Dict

from mente_laylay.memoria_mental.foco_contexto import extrair_topico_foco_vivo
from mente_laylay.memoria_mental.pendencia import criar_pendencia, limpar_pendencia, registrar_pendencia


def classificar_pergunta_com_proposito(texto: str) -> Dict[str, str]:
    """Classifica apenas perguntas cuja resposta muda o próximo passo."""
    fala = str(texto or "").strip()
    if not fala or "?" not in fala:
        return {}
    perguntas = re.findall(r"([^.!?…]*\?)", fala)
    pergunta = str(perguntas[-1] if perguntas else fala).strip()
    base = pergunta.casefold()
    fala_base = fala.casefold()

    if re.search(
        r"\b(?:posso|quer(?:e?s)?\s+que\s+eu)\s+(?:te\s+)?(?:sugerir|indicar|recomendar)\b"
        r"[^?]{0,140}\b(?:m[uú]sicas?|faixas?|discos?|[aá]lbuns?)\b",
        fala_base,
    ):
        return {
            "pergunta": pergunta,
            "proposito": "recomendacao_musical",
            "resposta_esperada": "sim_ou_nao",
        }

    # Perguntas devolvidas por educação depois de responder ao próprio
    # bem-estar demonstram interesse, mas não abrem uma obrigação contextual.
    # Pedro pode respondê-las; se mudar de assunto ou der um comando, o novo
    # turno continua independente.
    if re.search(
        r"^(?:mas\s+)?e\s+(?:voce|você)\b.*\b(?:como|tudo\s+bem)|"
        r"^(?:e\s+)?(?:do|da)\s+teu\s+lado\b.*\bcomo|"
        r"\bcomo\s+(?:voce|você)\s+(?:ta|tá|esta|está)(?:\s+de\s+verdade)?\?$",
        base,
    ):
        return {
            "pergunta": pergunta,
            "proposito": "cortesia_social",
            "resposta_esperada": "",
        }

    if any(s in base for s in ("o que voce acha", "o que você acha", "qual sua opiniao", "qual sua opinião", "e voce, o que", "e você, o que")):
        return {"pergunta": pergunta, "proposito": "opiniao_usuario", "resposta_esperada": "resposta_livre"}
    if re.fullmatch(r"e\s+voc[eê]\s*\?", base) or any(s in base for s in ("como voce", "como você", "tudo bem", "tudo na paz", "voce esta bem", "você está bem")):
        return {"pergunta": pergunta, "proposito": "bem_estar", "resposta_esperada": "estado_pessoal"}
    if any(s in base for s in (
        "qual foi a boa de hoje", "como foi seu dia", "como foi o seu dia",
        "o que teve de bom hoje", "o que rolou hoje", "como ta seu dia", "como tá seu dia",
    )):
        return {"pergunta": pergunta, "proposito": "dia_usuario", "resposta_esperada": "relato_curto"}
    if any(s in base for s in ("musica", "música")) and any(s in base for s in ("filme", "assistir", "ideia", "fazer")):
        return {"pergunta": pergunta, "proposito": "escolha_atividade", "resposta_esperada": "opcao"}
    if any(s in base for s in ("qual o nome", "qual nome", "que horas", "qual horario", "qual horário", "onde ", "quando ", "para quem", "pra quem")):
        return {"pergunta": pergunta, "proposito": "informacao_faltante", "resposta_esperada": "informacao"}
    if any(s in base for s in ("quer que eu", "posso ", "devo ")) and any(
        verbo in base for verbo in ("abr", "fech", "lig", "deslig", "toc", "execut", "faz", "faç", "apag", "salv", "envi")
    ):
        return {"pergunta": pergunta, "proposito": "confirmacao_acao", "resposta_esperada": "sim_ou_nao"}
    if any(s in base for s in (
        "quer ouvir", "quer escutar", "quer que eu coloque", "quer que eu toque",
    )):
        proposito = "escolha" if any(s in base for s in ("um desses", "uma dessas", "qual deles", "qual delas")) else "confirmacao_musical"
        esperado = "opcao" if proposito == "escolha" else "sim_ou_nao"
        return {"pergunta": pergunta, "proposito": proposito, "resposta_esperada": esperado}
    if any(s in base for s in ("qual voce prefere", "qual você prefere", "qual prefere", "qual deles", "qual delas", "uma ou outra", "ou prefere")):
        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}
    if re.search(
        r"\b(?:voce|você|tu)\s+prefere\b[^?]{0,120}\b"
        r"(?:esquerda\b[^?]{0,60}\bou\b[^?]{0,60}\bdireita|"
        r"direita\b[^?]{0,60}\bou\b[^?]{0,60}\besquerda)\b[^?]*\?\s*$",
        base,
    ):
        return {"pergunta": pergunta, "proposito": "escolha", "resposta_esperada": "opcao"}
    if any(s in base for s in ("quer que eu explique", "quer que eu detalhe", "posso explicar", "posso detalhar", "quer aprofundar", "quer ir mais fundo")):
        return {"pergunta": pergunta, "proposito": "aprofundamento", "resposta_esperada": "sim_ou_nao"}
    return {}


def texto_parece_pergunta_aberta(texto: str) -> bool:
    """Detecta perguntas que realmente aguardam uma resposta do Pedro."""
    classificacao = classificar_pergunta_com_proposito(texto)
    return bool(
        classificacao
        and str(classificacao.get("proposito") or "") != "cortesia_social"
    )


def registrar_oferta_pendente(
    estado_atual: Dict[str, Any] | None,
    resposta: str,
    *,
    alvo_contexto: str = "",
) -> Dict[str, Any]:
    """Registra uma oferta na mente única, independentemente da habilidade."""
    estado = dict(estado_atual or {})
    fala = re.sub(r"\s+", " ", str(resposta or "")).strip()
    classificacao = classificar_pergunta_com_proposito(fala)
    proposito = str(classificacao.get("proposito") or "")
    recomendacao_implicita = bool(re.search(
        r"\b(?:minha aposta|eu iria de|eu tentaria|eu arrisco|vou te jogar|m[uú]sica que eu t[oô] indicando)\b",
        fala.casefold(),
    ))
    if proposito not in {"confirmacao_musical", "recomendacao_musical", "escolha"} and not recomendacao_implicita:
        return estado
    if recomendacao_implicita and not proposito:
        proposito = "confirmacao_musical"
        classificacao = {
            "pergunta": fala,
            "proposito": proposito,
            "resposta_esperada": "sim_ou_nao",
        }

    opcoes: list[Dict[str, Any]] = []
    vistos = set()
    fala_extracao = fala
    if recomendacao_implicita:
        fala_extracao = re.sub(
            r"^.*?\b(?:e|é|seria|vai ser)\s+",
            "",
            fala,
            count=1,
            flags=re.IGNORECASE,
        )
    padroes = (
        r'["“](?P<titulo>[^"”]{2,80})["”]\s*(?:[-—]\s*)?(?:de|da|do)\s+(?P<artista>[^.,;!?"“”]{2,70})',
        r'(?P<artista>[^.,;!?"“”]{2,60})\s+-\s+(?P<titulo>[^.,;!?"“”]{2,80})',
    )
    for padrao in padroes:
        for achado in re.finditer(padrao, fala_extracao):
            titulo = str(achado.group("titulo") or "").strip(" .,;:!?")
            artista = str(achado.group("artista") or "").strip(" .,;:!?")
            # Encerra artista capturado antes de conectores de outra opção.
            artista = re.split(r"\s+(?:ou|e)\s+[\"“]", artista, maxsplit=1)[0].strip()
            query = f"{artista} - {titulo}".strip(" -")
            chave = query.casefold()
            if titulo and artista and chave not in vistos:
                vistos.add(chave)
                opcoes.append({"rotulo": titulo, "alvo": query, "params": {"query": query}})
    estado["oferta_pendente"] = {
        "tipo": "musica",
        "intent": "MUSIC_SEARCH",
        "modo": "recomendar_artista" if proposito == "recomendacao_musical" else "tocar_opcao",
        "contexto": str(alvo_contexto or estado.get("assunto_da_fala") or estado.get("ultimo_alvo") or "").strip()[:160],
        "opcoes": opcoes[:4],
        "pergunta": str(classificacao.get("pergunta") or "")[:240],
        "resposta_esperada": str(classificacao.get("resposta_esperada") or ""),
        "ts": time.time(),
    }
    return registrar_pendencia(
        estado,
        criar_pendencia(
            origem="oferta_musical",
            tipo="escolha" if proposito == "escolha" else "confirmacao",
            dominio="musica",
            conteudo=str(classificacao.get("pergunta") or fala),
            opcoes=opcoes[:4],
            resposta_esperada=str(classificacao.get("resposta_esperada") or ""),
            intencao="MUSIC_SEARCH",
            ttl_s=300.0,
            foi_falada=True,
        ),
    )


def oferta_pendente_ativa(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 300.0,
) -> Dict[str, Any] | None:
    oferta = (estado_atual or {}).get("oferta_pendente")
    if not isinstance(oferta, dict) or not oferta.get("intent"):
        return None
    try:
        if time.time() - float(oferta.get("ts") or 0.0) > ttl_s:
            return None
    except Exception:
        return None
    return dict(oferta)


def limpar_oferta_pendente(estado_atual: Dict[str, Any] | None) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["oferta_pendente"] = {}
    if str((estado.get("pendencia_atual") or {}).get("origem") or "") == "oferta_musical":
        estado = limpar_pendencia(estado, motivo="resolvida")
    return estado


def registrar_feedback_musical_conversacional(
    estado_atual: Dict[str, Any] | None,
    texto_usuario: str,
) -> Dict[str, Any]:
    """Aprende gosto explícito usando a oferta presente na mesma mente."""
    estado = dict(estado_atual or {})
    texto = re.sub(r"\s+", " ", str(texto_usuario or "")).strip().casefold()
    if not texto:
        return estado
    negativo = any(s in texto for s in ("odeio", "não gosto", "nao gosto", "não curto", "nao curto", "detesto"))
    positivo = any(s in texto for s in ("adorei", "gostei", "curti", "amo ", "eu amo"))
    if not (negativo or positivo):
        return estado
    delta = -2 if negativo else 1
    oferta = oferta_pendente_ativa(estado, ttl_s=600.0) or {}
    preferencias = dict(estado.get("preferencias_musicais") or {})
    artistas = dict(preferencias.get("artistas") or {})
    faixas = dict(preferencias.get("faixas") or {})
    encontrou_artista = False
    for opcao in oferta.get("opcoes") or []:
        alvo = str(opcao.get("alvo") or "").strip()
        if " - " not in alvo:
            continue
        artista, faixa = [parte.strip() for parte in alvo.split(" - ", 1)]
        if artista.casefold() in texto:
            artistas[artista] = int(artistas.get(artista, 0)) + delta
            faixas[alvo] = int(faixas.get(alvo, 0)) + delta
            encontrou_artista = True
    if negativo and not encontrou_artista:
        achado = re.search(
            r"\b(?:odeio|detesto|n[aã]o\s+gosto\s+(?:de|da|do)|n[aã]o\s+curto)\s+(.+)$",
            texto,
        )
        if achado:
            artista_expresso = re.split(
                r"\s+(?:mas|porque|por que|hoje|agora|nessa|nesta)\b",
                str(achado.group(1) or ""),
                maxsplit=1,
            )[0].strip(" .,;:!?\"")[:80]
            if artista_expresso and 1 <= len(artista_expresso.split()) <= 5:
                nome_artista = artista_expresso.title()
                artistas[nome_artista] = int(artistas.get(nome_artista, 0)) + delta
    preferencias.update({"artistas": artistas, "faixas": faixas})
    estado["preferencias_musicais"] = preferencias
    if negativo:
        estado = limpar_oferta_pendente(estado)
    return estado


def registrar_continuidade_da_fala(
    estado_atual: Dict[str, Any] | None,
    resposta: str,
    *,
    texto_usuario: str = "",
    assunto: str = "",
    origem: str = "",
    emocao: str = "",
) -> Dict[str, Any]:
    """Guarda o significado estrutural da fala mais recente da Laylay."""
    estado = dict(estado_atual or {})
    fala = re.sub(r"\s+", " ", str(resposta or "")).strip()
    if not fala:
        return estado

    partes = [p.strip() for p in re.split(r"(?<=[.!?…])\s+", fala) if p.strip()]
    perguntas = [p for p in partes if "?" in p]
    afirmacoes = [p for p in partes if "?" not in p]
    afirmacao = afirmacoes[-1] if afirmacoes else ""
    pergunta = perguntas[-1] if perguntas else ""
    base = fala.casefold()

    marcadores_opiniao = (
        "eu acho", "minha opinião", "minha opiniao", "minha leitura",
        "pra mim", "para mim", "eu iria", "eu prefiro", "não curto",
        "nao curto", "eu gosto", "não gostei", "nao gostei",
    )
    marcadores_brincadeira = (
        "kkk", "haha", "brincadeira", "tô zoando", "to zoando",
        "sem drama", "modo caos", "cientificamente duvidoso",
    )

    opiniao = fala if any(m in base for m in marcadores_opiniao) else ""
    brincadeira = fala if any(m in base for m in marcadores_brincadeira) else ""

    assunto_limpo = str(assunto or "").strip()
    if not assunto_limpo:
        try:
            assunto_limpo = extrair_topico_foco_vivo(
                texto_usuario,
                alvo="",
                habilidade=origem,
            )
        except Exception:
            assunto_limpo = ""
    if assunto_limpo.lower() in {"conversa", "chat", "opinion", "opiniao", "opinião"}:
        assunto_limpo = ""

    resposta_esperada = ""
    pergunta_memoria = pergunta
    if pergunta:
        classificacao_pergunta = classificar_pergunta_com_proposito(pergunta)
        resposta_esperada = str(classificacao_pergunta.get("resposta_esperada") or "")
        if str(classificacao_pergunta.get("proposito") or "") == "cortesia_social":
            pergunta_memoria = ""

    estado["ultima_afirmacao"] = afirmacao[:300]
    estado["ultima_pergunta"] = pergunta_memoria[:300]
    estado["ultima_opiniao"] = opiniao[:300]
    estado["ultima_brincadeira"] = brincadeira[:300]
    estado["resposta_esperada"] = resposta_esperada
    estado["assunto_da_fala"] = assunto_limpo[:160]
    estado["emocao_da_fala"] = str(emocao or "").strip()[:80]
    estado["continuidade_fala_ts"] = time.time()
    return estado


def registrar_pergunta_aberta(
    estado_atual: Dict[str, Any] | None,
    pergunta: str,
    *,
    topico: str = "",
    origem: str = "",
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    pergunta_limpa = str(pergunta or "").strip()
    classificacao = classificar_pergunta_com_proposito(pergunta_limpa)
    if not classificacao:
        return limpar_pergunta_aberta(estado)

    estado["pergunta_aberta_texto"] = str(classificacao.get("pergunta") or pergunta_limpa)[:240]
    estado["pergunta_aberta_topico"] = str(topico or "").strip()[:120]
    estado["pergunta_aberta_origem"] = str(origem or "").strip()[:80]
    proposito = str(classificacao.get("proposito") or "").strip()
    resposta_esperada = str(classificacao.get("resposta_esperada") or "").strip()
    if proposito == "bem_estar":
        estado["pergunta_aberta_tipo"] = "bem_estar"
    elif resposta_esperada == "sim_ou_nao":
        estado["pergunta_aberta_tipo"] = "confirmacao"
    else:
        estado["pergunta_aberta_tipo"] = "resposta_curta"
    estado["pergunta_aberta_proposito"] = proposito
    estado["pergunta_aberta_resposta_esperada"] = resposta_esperada
    estado["pergunta_aberta_ts"] = time.time()
    return registrar_pendencia(
        estado,
        criar_pendencia(
            origem="pergunta_aberta",
            tipo=proposito or "pergunta",
            dominio="conversa",
            conteudo=estado["pergunta_aberta_texto"],
            resposta_esperada=resposta_esperada,
            ttl_s=300.0,
            foi_falada=True,
        ),
    )


def limpar_pergunta_aberta(estado_atual: Dict[str, Any] | None) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["pergunta_aberta_texto"] = ""
    estado["pergunta_aberta_topico"] = ""
    estado["pergunta_aberta_origem"] = ""
    estado["pergunta_aberta_tipo"] = ""
    estado["pergunta_aberta_proposito"] = ""
    estado["pergunta_aberta_resposta_esperada"] = ""
    estado["pergunta_aberta_ts"] = 0.0
    if str((estado.get("pendencia_atual") or {}).get("origem") or "") == "pergunta_aberta":
        estado = limpar_pendencia(estado, motivo="resolvida")
    return estado


def registrar_promessa_conversacional(
    estado_atual: Dict[str, Any] | None,
    resposta: str,
    *,
    alvo: str = "",
    conteudo: str = "",
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    fala = str(resposta or "").strip()
    base = fala.lower()
    tipo = ""
    if any(p in base for p in [
        "quer que eu abra minha opinião",
        "quer que eu abrir minha opinião",
        "quer que eu abra melhor",
        "quer que eu explique",
        "quer que eu detalhe",
        "posso explicar melhor",
        "posso abrir minha opinião",
    ]):
        tipo = "explicar_opiniao"
    elif any(p in base for p in [
        "quer que eu te explique",
        "quer que eu explique melhor",
        "quer que eu detalhe isso",
        "posso te explicar",
    ]):
        tipo = "explicar"
    elif any(p in base for p in [
        "posso te contar uma coisa", "posso contar uma coisa",
        "te conto uma coisa", "quer que eu te conte",
    ]) and any(p in base for p in ["aconteceu comigo", "aconteceu hoje", "do meu dia"]):
        tipo = "contar_experiencia"

    if not tipo:
        return estado

    estado["ultima_promessa_tipo"] = tipo
    estado["ultima_promessa_texto"] = fala[:240]
    estado["ultima_promessa_alvo"] = str(alvo or estado.get("ultimo_alvo") or "").strip()[:160]
    estado["ultima_promessa_conteudo"] = str(conteudo or "").strip()[:500]
    estado["ultima_promessa_ts"] = time.time()
    return registrar_pendencia(
        estado,
        criar_pendencia(
            origem="promessa_conversacional",
            tipo="promessa",
            dominio="conversa",
            conteudo=fala,
            resposta_esperada="confirmacao_ou_cobranca",
            ttl_s=180.0,
            foi_falada=True,
        ),
    )


def limpar_promessa_conversacional(estado_atual: Dict[str, Any] | None) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["ultima_promessa_tipo"] = ""
    estado["ultima_promessa_texto"] = ""
    estado["ultima_promessa_alvo"] = ""
    estado["ultima_promessa_conteudo"] = ""
    estado["ultima_promessa_ts"] = 0.0
    if str((estado.get("pendencia_atual") or {}).get("origem") or "") == "promessa_conversacional":
        estado = limpar_pendencia(estado, motivo="resolvida")
    return estado


def promessa_conversacional_ativa(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 180.0,
) -> Dict[str, Any] | None:
    estado = dict(estado_atual or {})
    tipo = str(estado.get("ultima_promessa_tipo") or "").strip()
    if not tipo:
        return None
    try:
        ts = float(estado.get("ultima_promessa_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return None
    return {
        "tipo": tipo,
        "texto": str(estado.get("ultima_promessa_texto") or "").strip(),
        "alvo": str(estado.get("ultima_promessa_alvo") or "").strip(),
        "conteudo": str(estado.get("ultima_promessa_conteudo") or "").strip(),
        "idade_s": max(0.0, time.time() - ts),
    }


def registrar_alvo_corrigido(estado_atual: Dict[str, Any] | None, alvo: str) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    estado["alvo_corrigido"] = str(alvo or "").strip()[:160]
    estado["alvo_corrigido_ts"] = time.time()
    return estado


def alvo_corrigido_ativo(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 120.0,
) -> str:
    estado = dict(estado_atual or {})
    alvo = str(estado.get("alvo_corrigido") or "").strip()
    if not alvo:
        return ""
    try:
        ts = float(estado.get("alvo_corrigido_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return ""
    return alvo


def registrar_estrutura_arquivo_recente(
    estado_atual: Dict[str, Any] | None,
    params: Dict[str, Any] | None,
) -> Dict[str, Any]:
    estado = dict(estado_atual or {})
    dados = dict(params or {}) if isinstance(params, dict) else {}
    estado["ultima_estrutura_arquivo_params"] = dados
    estado["ultima_estrutura_arquivo_ts"] = time.time() if dados else 0.0
    return estado


def estrutura_arquivo_recente(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 900.0,
) -> Dict[str, Any] | None:
    estado = dict(estado_atual or {})
    dados = estado.get("ultima_estrutura_arquivo_params")
    if not isinstance(dados, dict) or not dados:
        return None
    try:
        ts = float(estado.get("ultima_estrutura_arquivo_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return None
    return dict(dados)


def pergunta_aberta_ativa(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 120.0,
) -> Dict[str, Any] | None:
    estado = dict(estado_atual or {})
    pergunta = str(estado.get("pergunta_aberta_texto") or "").strip()
    if not pergunta:
        return None
    try:
        ts = float(estado.get("pergunta_aberta_ts") or 0.0)
    except Exception:
        ts = 0.0
    if not ts or time.time() - ts > ttl_s:
        return None
    return {
        "pergunta": pergunta,
        "topico": str(estado.get("pergunta_aberta_topico") or "").strip(),
        "origem": str(estado.get("pergunta_aberta_origem") or "").strip(),
        "tipo": str(estado.get("pergunta_aberta_tipo") or "").strip(),
        "proposito": str(estado.get("pergunta_aberta_proposito") or "").strip(),
        "resposta_esperada": str(estado.get("pergunta_aberta_resposta_esperada") or "").strip(),
        "idade_s": max(0.0, time.time() - ts),
    }


def texto_parece_resposta_curta_a_pergunta(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(str(texto or ""))
    if not t:
        return False
    palavras = t.split()
    if len(palavras) > 12:
        return False
    if "?" in str(texto or ""):
        return False
    # Perguntas faladas/digitadas frequentemente chegam sem ponto de
    # interrogacao. Elas iniciam um turno novo e nao podem ser consumidas como
    # resposta a uma pergunta antiga da Laylay.
    inicio = t.split()
    if inicio and inicio[0] in {
        "como", "qual", "quais", "quem", "quando", "onde", "porque", "porquê",
        "quanto", "quantos", "quantas", "cadê", "cade",
    }:
        return False
    if len(inicio) > 1 and inicio[0] in {"e", "mas", "entao", "então"} and inicio[1] in {
        "como", "qual", "quais", "quem", "quando", "onde", "porque", "porquê",
        "quanto", "quantos", "quantas", "cadê", "cade",
    }:
        return False
    if "o que" in t and any(verbo in t.split() for verbo in ("vamos", "fazer", "fazemos")):
        return False
    sinais_comando = [
        "abre", "abrir", "abra", "entra", "entrar", "fecha", "fechar",
        "coloca", "colocar", "toca", "tocar", "playlist", "musica", "música",
        "volume", "spotify", "youtube", "netflix",
        "cria", "criar", "apaga", "apagar", "move", "mover", "email",
        "le ", "lê ", "ler ", "site", "aba", "janela", "foco",
        "pausa", "pause", "despausa", "retoma", "continua", "próxima", "proxima",
        "anterior", "maximiza", "maximizar", "tela cheia", "fullscreen",
    ]
    if any(s in f" {t} " for s in sinais_comando):
        return False
    return True
