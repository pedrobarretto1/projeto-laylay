"""Funcoes de contexto compartilhado entre as habilidades da Laylay."""

from __future__ import annotations

import time
import re
from typing import Any, Dict

from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao, normalizar_resultado_acao
from mente_laylay.memoria_mental.pendencia import criar_pendencia, limpar_pendencia, registrar_pendencia

from mente_laylay.memoria_mental.consciencia_temporal import (
    atualizar_consciencia_temporal,
    estado_temporal_inicial,
)
from mente_laylay.memoria_mental.registro_semantico import (
    estado_registro_semantico_inicial,
    registrar_interacao_semantica,
)


def estado_mental_inicial() -> Dict[str, Any]:
    return {
        "ultima_entrada": "",
        "ultima_entrada_ts": 0.0,
        "turno_atual": {},
        "plano_turno_atual": {},
        "avaliacoes_turno": [],
        "metricas_verificador": {},
        "trilha_decisoes_turno": [],
        "diagnostico_metricas": {},
        "diagnostico_falhas": [],
        "diagnostico_decisoes": [],
        "falhas_consecutivas_execucao": {},
        "ultimas_entradas": [],
        "ultima_intencao": "",
        "ultimo_alvo": "",
        "ultimo_app_janela": "",
        "ultimo_site_aba": "",
        "ultima_pasta": "",
        "ultimo_arquivo": "",
        "ultimo_caminho_arquivo": "",
        "ultimo_dispositivo_iot": "",
        "ultimo_ambiente_iot": "",
        "ultimo_estado_iot": None,
        "musica_atual_titulo": "",
        "musica_atual_url": "",
        "musica_atual_status": "",
        "musica_atual_ts": 0.0,
        "conteudo_atual": {},
        "ultima_decisao_semantica": {},
        "aprendizado_continuidade": {
            "preferencias_conflito": {},
            "preferencias_operacao": {},
            "correcoes_alvo": {},
            "correcoes_parametros": {},
            "correcoes": [],
        },
        "correcao_interpretacao_pendente": {},
        "historico_correcoes_interpretacao": [],
        "consciencia_temporal": estado_temporal_inicial(),
        "ultima_estrutura_arquivo_params": {},
        "ultima_estrutura_arquivo_ts": 0.0,
        "ultimo_escopo": "",
        "ultima_habilidade": "",
        "ultima_resposta": "",
        "direcao_fala_atual": {},
        "historico_direcao_fala": [],
        "nome_usuario": "Pedro",
        "ultima_afirmacao": "",
        "ultima_pergunta": "",
        "ultima_opiniao": "",
        "ultima_brincadeira": "",
        "resposta_esperada": "",
        "assunto_da_fala": "",
        "emocao_da_fala": "",
        "emocao_usuario": "",
        "emocao_usuario_intensidade": 0,
        "emocao_usuario_alvo": "",
        "emocao_usuario_pedido_implicito": "",
        "emocao_usuario_necessidade_acao": False,
        "emocao_usuario_texto": "",
        "emocao_usuario_ts": 0.0,
        "continuidade_fala_ts": 0.0,
        "ultima_acao_status": "",
        "ultima_acao_reexecutavel": False,
        "ultima_acao_intent": "",
        "ultima_acao_params": {},
        "ultima_acao_origem": "",
        "ultima_acao_texto": "",
        "ultima_acao_confirmada": None,
        "ultima_acao_ok": None,
        "ultima_acao_alvo": "",
        "ultima_acao_detalhe": "",
        "ultima_promessa_tipo": "",
        "ultima_promessa_texto": "",
        "ultima_promessa_alvo": "",
        "ultima_promessa_conteudo": "",
        "ultima_promessa_ts": 0.0,
        "oferta_pendente": {},
        "pendencia_atual": {},
        "ultima_pendencia_encerrada": {},
        "preferencias_musicais": {"artistas": {}, "faixas": {}, "estilos": {}},
        "alvo_corrigido": "",
        "alvo_corrigido_ts": 0.0,
        "ultima_reparacao_alvo_anterior": "",
        "ultima_reparacao_alvo_novo": "",
        "ultima_reparacao_tipo": "",
        "ultima_reparacao_ts": 0.0,
        "pergunta_aberta_texto": "",
        "pergunta_aberta_topico": "",
        "pergunta_aberta_origem": "",
        "pergunta_aberta_tipo": "",
        "pergunta_aberta_proposito": "",
        "pergunta_aberta_resposta_esperada": "",
        "pergunta_aberta_ts": 0.0,
        "foco_vivo_tipo": "",
        "foco_vivo_alvo": "",
        "foco_vivo_topico": "",
        "foco_vivo_habilidade": "",
        "foco_vivo_intencao": "",
        "foco_vivo_texto": "",
        "foco_vivo_resposta": "",
        "foco_vivo_ts": 0.0,
        "foco_conversacional_tipo": "",
        "foco_conversacional_alvo": "",
        "foco_conversacional_topico": "",
        "foco_conversacional_habilidade": "",
        "foco_conversacional_intencao": "",
        "foco_conversacional_texto": "",
        "foco_conversacional_resposta": "",
        "foco_conversacional_escopo": "",
        "foco_conversacional_ts": 0.0,
        "foco_operacional_tipo": "",
        "foco_operacional_alvo": "",
        "foco_operacional_topico": "",
        "foco_operacional_habilidade": "",
        "foco_operacional_intencao": "",
        "foco_operacional_texto": "",
        "foco_operacional_resposta": "",
        "foco_operacional_escopo": "",
        "foco_operacional_ts": 0.0,
        "focos_por_dominio": {},
        "topico_explicito_atual": "",
        "topico_explicito_origem": "",
        "topico_explicito_ts": 0.0,
        "assunto_estruturado_atual": {},
        "registro_semantico": estado_registro_semantico_inicial(),
        "perfil_proatividade": {},
        "ts": 0.0,
    }


def classificar_pergunta_com_proposito(texto: str) -> Dict[str, str]:
    """Classifica apenas perguntas cuja resposta muda o próximo passo."""
    fala = str(texto or "").strip()
    if not fala or "?" not in fala:
        return {}
    perguntas = re.findall(r"([^.!?…]*\?)", fala)
    pergunta = str(perguntas[-1] if perguntas else fala).strip()
    base = pergunta.casefold()

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
    if proposito not in {"confirmacao_musical", "escolha"} and not recomendacao_implicita:
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


def intencao_reexecutavel(intent: str) -> bool:
    return str(intent or "").upper().strip() in {
        "APP_OPEN",
        "CLOSE_APP",
        "OPEN_URL",
        "CLOSE_TAB",
        "PLAYLIST_PLAY",
        "MUSIC_SEARCH",
        "VOLUME",
        "MEDIA_CONTROL",
        "WEATHER",
        "EMAIL_READ",
        "EMAIL_SYNC",
        "NOTIFICATIONS",
        "BRIEFING_REPEAT",
        "SITE_ENTER",
        "LAYLAY_PLAYLIST_LIST",
        "PLAYLIST_LIST",
        "IOT_CONTROL",
        "IOT_STATUS",
        "IOT_LIST",
    }


def registrar_resultado_execucao(
    estado_atual: Dict[str, Any] | None,
    resultado: ResultadoAcao | Dict[str, Any] | None = None,
    texto: str = "",
    executou: bool | None = None,
    *,
    origem: str = "",
    status: str = "",
) -> Dict[str, Any]:
    if not isinstance(resultado, (dict, ResultadoAcao)):
        return dict(estado_atual or {})

    estado = dict(estado_atual or {})
    contrato = normalizar_resultado_acao(
        resultado,
        texto=texto,
        executou=executou,
        origem=origem,
        status=status,
    )
    intent = contrato.intent
    params = dict(contrato.params)
    status_final = contrato.status
    registro_generico = not bool(status_final)
    texto_curto = str(texto or "").strip()[:200]
    mesmo_intent = str(estado.get("ultima_acao_intent") or "").strip().upper() == intent
    mesmo_texto = str(estado.get("ultima_acao_texto") or "").strip() == texto_curto
    mesmo_resultado = mesmo_intent and mesmo_texto

    if not status_final:
        status_anterior = str(estado.get("ultima_acao_status") or "").strip().lower()
        if mesmo_resultado and status_anterior:
            status_final = status_anterior
        else:
            status_final = "executado" if contrato.executou is True else "falhou" if contrato.executou is False else "incerto"

    estado["ultima_acao_status"] = status_final
    estado["ultima_acao_reexecutavel"] = bool(intencao_reexecutavel(intent))
    estado["ultima_acao_intent"] = intent
    estado["ultima_acao_params"] = dict(params)
    estado["ultima_acao_origem"] = contrato.origem
    estado["ultima_acao_texto"] = texto_curto
    estado["ultima_acao_confirmada"] = (
        estado.get("ultima_acao_confirmada")
        if mesmo_resultado and (registro_generico or contrato.confirmado is None)
        else contrato.confirmado
    )
    estado["ultima_acao_ok"] = (
        estado.get("ultima_acao_ok")
        if mesmo_resultado and (registro_generico or contrato.ok is None)
        else contrato.ok
    )
    estado["ultima_acao_alvo"] = (
        str(estado.get("ultima_acao_alvo") or "")
        if mesmo_resultado and (registro_generico or not contrato.alvo)
        else contrato.alvo
    )
    estado["ultima_acao_detalhe"] = (
        str(estado.get("ultima_acao_detalhe") or "")
        if mesmo_resultado and (registro_generico or not contrato.detalhe)
        else contrato.detalhe[:300]
    )

    # A troca de dominio precisa acontecer no contrato-base, antes de qualquer
    # enriquecimento opcional. Assim uma ação web recente nunca deixa um app
    # anterior (por exemplo, Steam) vencer referências como "fecha isso".
    if intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"}:
        alvo_site = str(params.get("alvo") or params.get("url") or params.get("site") or "").strip()
        if alvo_site:
            estado["ultimo_site_aba"] = alvo_site
            estado["ultimo_alvo"] = alvo_site
        estado["ultimo_app_janela"] = ""
    elif intent in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
        alvo_app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
        if alvo_app:
            estado["ultimo_app_janela"] = alvo_app
            estado["ultimo_alvo"] = alvo_app
    elif intent in {"IOT_CONTROL", "IOT_STATUS"}:
        alvo_iot = str(params.get("alvo") or params.get("dispositivo") or "").strip()
        if alvo_iot:
            estado["ultimo_dispositivo_iot"] = alvo_iot
            estado["ultimo_alvo"] = alvo_iot
        ambiente_iot = str(params.get("ambiente") or "").strip()
        if ambiente_iot:
            estado["ultimo_ambiente_iot"] = ambiente_iot

    alvo_acao = str(
        params.get("alvo")
        or params.get("url")
        or params.get("site")
        or params.get("nome_app")
        or params.get("app")
        or ""
    ).strip()
    alvo_corrigido = str(estado.get("alvo_corrigido") or "").strip()
    if alvo_acao and alvo_corrigido and alvo_acao.casefold() != alvo_corrigido.casefold():
        estado["alvo_corrigido"] = ""
        estado["alvo_corrigido_ts"] = 0.0

    estado["ts"] = time.time()
    return estado


def enriquecer_resultado_execucao_contextual(
    estado_atual: Dict[str, Any] | None,
    resultado: ResultadoAcao | Dict[str, Any] | None,
    texto: str = "",
    executou: bool | None = None,
    *,
    status: str = "",
    normalizar_texto_cb=None,
    atualizar_foco_vivo_cb=None,
) -> Dict[str, Any]:
    """Atualiza alvos recentes e foco vivo depois de uma ação prática."""
    estado = dict(estado_atual or {})
    if not isinstance(resultado, (dict, ResultadoAcao)):
        return estado

    try:
        contrato = normalizar_resultado_acao(
            resultado,
            texto=texto,
            executou=executou,
            status=status,
        )
        if contrato.executou is not True:
            return estado
        intent = contrato.intent
        params = dict(contrato.params)
        apps_sem_janela_contextual = {
            "microsoft store",
            "store",
            "ms store",
            "loja microsoft",
            "loja",
        }

        def normalizar(valor: str) -> str:
            if callable(normalizar_texto_cb):
                return normalizar_texto_cb(valor)
            return str(valor or "").strip().lower()

        if intent in {"APP_OPEN", "MAXIMIZE_WINDOW", "CLOSE_APP"}:
            app = str(params.get("nome_app") or params.get("app") or params.get("nome") or "").strip()
            if app and normalizar(app) not in apps_sem_janela_contextual:
                estado["ultimo_app_janela"] = app
                estado["ultimo_alvo"] = app
            elif app:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = app
                estado["ultimo_alvo"] = app
        elif intent in {"OPEN_URL", "CLOSE_TAB"}:
            alvo_web = str(params.get("alvo") or params.get("url") or params.get("nome_app") or "").strip()
            if alvo_web:
                estado["ultimo_app_janela"] = ""
                estado["ultimo_site_aba"] = alvo_web
        elif intent == "MEDIA_CONTROL":
            estado["ultima_habilidade"] = "midia"
            estado["ultimo_alvo"] = str(params.get("platform") or params.get("acao") or "musica").strip() or "musica"
            estado["ultimo_escopo"] = str(params.get("platform") or "music").strip()
        elif intent == "PLAYLIST_ADD":
            playlist = str(params.get("nome_playlist") or params.get("playlist") or params.get("nome") or "").strip()
            if playlist:
                estado["ultimo_alvo"] = playlist
                estado["ultima_habilidade"] = "playlist"
                estado["ultimo_escopo"] = "playlist"
        elif intent in {"IOT_CONTROL", "IOT_STATUS"}:
            dispositivo = str(params.get("alvo") or params.get("dispositivo") or "").strip()
            if dispositivo:
                estado["ultimo_dispositivo_iot"] = dispositivo
                estado["ultimo_alvo"] = dispositivo
            estado["ultimo_ambiente_iot"] = str(params.get("ambiente") or estado.get("ultimo_ambiente_iot") or "").strip()
            estado["ultima_habilidade"] = "iot"
            estado["ultimo_escopo"] = "casa"

        alvo_foco = str(
            params.get("alvo")
            or params.get("nome_app")
            or params.get("nome_playlist")
            or params.get("query")
            or params.get("nome")
            or params.get("arquivo_nome")
            or params.get("item")
            or estado.get("ultimo_alvo")
            or ""
        ).strip()
        habilidade_foco = {
            "APP_OPEN": "janela",
            "CLOSE_APP": "janela",
            "MAXIMIZE_WINDOW": "janela",
            "OPEN_URL": "site",
            "CLOSE_TAB": "site",
            "SITE_ENTER": "site",
            "SEARCH": "pesquisa",
            "WEATHER": "clima",
            "PLAYLIST_PLAY": "playlist",
            "PLAYLIST_ADD": "playlist",
            "PLAYLIST_LIST": "playlist",
            "MUSIC_SEARCH": "musica",
            "MEDIA_CONTROL": "midia",
            "CREATE_FOLDER": "arquivos",
            "DELETE_ITEM": "arquivos",
            "EMAIL_READ": "email",
            "EMAIL_SYNC": "email",
            "AGENDAR_LEMBRETE": "agenda",
            "AGENDAR_ACAO": "agenda",
            "LISTAR_AGENDAMENTOS": "agenda",
            "BRIEFING_REPEAT": "conversa",
            "IOT_CONTROL": "iot",
            "IOT_STATUS": "iot",
            "IOT_LIST": "iot",
        }.get(intent, str(estado.get("ultima_habilidade") or "").strip())

        if callable(atualizar_foco_vivo_cb):
            estado = atualizar_foco_vivo_cb(
                estado,
                texto=texto,
                resposta=status or ("executado" if executou else "falhou"),
                intencao=intent,
                alvo=alvo_foco,
                habilidade=habilidade_foco,
            )
    except Exception:
        return estado

    return estado


def registrar_mente_curta(
    estado_atual: Dict[str, Any] | None,
    *,
    texto_usuario: str = "",
    resposta_ia: str = "",
    intencao: str = "",
    alvo: str = "",
    escopo: str = "",
    habilidade: str = "",
    ultimo_topico_conversa: str = "",
    emocao_atual: str = "",
    normalizar_texto_cb=None,
    eh_alvo_site_web_cb=None,
    texto_parece_pergunta_aberta_cb=None,
    registrar_pergunta_aberta_cb=None,
    limpar_pergunta_aberta_cb=None,
    registrar_promessa_conversacional_cb=None,
    atualizar_foco_vivo_cb=None,
    log: Any = print,
) -> Dict[str, Any]:
    """Registra entrada/resposta recentes sem isolar a mente dos callbacks centrais."""
    try:
        estado = dict(estado_atual or {})
    except Exception:
        estado = {}

    texto_usuario = str(texto_usuario or "").strip()
    resposta_ia = str(resposta_ia or "").strip()
    intencao = str(intencao or "").strip()
    alvo = str(alvo or "").strip()
    escopo = str(escopo or "").strip()
    habilidade = str(habilidade or "").strip()

    # Uma contestação explícita reduz a confiança da fala anterior. Ela não
    # pode continuar circulando no prompt como se fosse um fato confirmado.
    texto_contestacao = str(texto_usuario or "").casefold()
    if texto_usuario and re.search(
        r"\b(?:que\s+papo\s+(?:e|é)\s+esse|de\s+onde\s+(?:voce|você)\s+tirou|"
        r"isso\s+(?:e|é)\s+verdade|viajou|nada\s+a\s+ver|tem\s+certeza\s+disso)\b",
        texto_contestacao,
    ):
        anterior_contestada = str(estado.get("ultima_resposta") or "").strip()
        if anterior_contestada:
            estado["alegacao_contestada"] = {
                "texto": anterior_contestada[:500],
                "contestacao": texto_usuario[:300],
                "topico": str(estado.get("assunto_da_fala") or ultimo_topico_conversa or "")[:160],
                "status": "nao_confiavel_ate_verificacao",
                "ts": time.time(),
            }

    assunto_semantico = str(
        ((estado.get("assunto_estruturado_atual") or {}).get("titulo")
         if isinstance(estado.get("assunto_estruturado_atual"), dict) else "")
        or estado.get("assunto_da_fala")
        or ultimo_topico_conversa
        or alvo
        or ""
    ).strip()
    fundamentacao_atual = (
        dict(estado.get("fundamentacao_factual_turno") or {})
        if isinstance(estado.get("fundamentacao_factual_turno"), dict)
        else {}
    )
    fonte_factual = str(fundamentacao_atual.get("fonte") or "").strip() if fundamentacao_atual.get("confiavel") else ""
    estado["registro_semantico"] = registrar_interacao_semantica(
        estado.get("registro_semantico"),
        texto_usuario=texto_usuario,
        resposta_laylay=resposta_ia,
        assunto=assunto_semantico,
        # A rota não é fonte. Somente a fundamentação fechada do turno é.
        fonte_resposta=fonte_factual,
    )

    if texto_usuario:
        try:
            from mente_laylay.cognicao.conversa_sobre_capacidades import (
                extrair_registro_capacidade_futura,
            )

            registro_capacidade = extrair_registro_capacidade_futura(texto_usuario)
            if registro_capacidade:
                registro_capacidade["ts"] = time.time()
                estado["capacidade_futura"] = registro_capacidade
        except Exception:
            pass

    if texto_usuario:
        estado = registrar_feedback_musical_conversacional(estado, texto_usuario)
        estado["ultima_entrada_ts"] = time.time()
        estado["consciencia_temporal"] = atualizar_consciencia_temporal(
            estado.get("consciencia_temporal"),
            texto_usuario,
            resposta_ia=resposta_ia,
        )
        estado["ultima_entrada"] = texto_usuario
        entradas = list(estado.get("ultimas_entradas") or [])
        entradas.append(texto_usuario[:160])
        estado["ultimas_entradas"] = entradas[-8:]
    if resposta_ia:
        conteudo_anterior_promessa = str(
            estado.get("ultima_opiniao") or estado.get("ultima_afirmacao") or ""
        ).strip()
        estado["ultima_resposta"] = resposta_ia[:180]
        estado = registrar_continuidade_da_fala(
            estado,
            resposta_ia,
            texto_usuario=texto_usuario,
            assunto=alvo or ultimo_topico_conversa,
            origem=habilidade or intencao,
            emocao=emocao_atual,
        )
        estado = registrar_oferta_pendente(estado, resposta_ia)
        try:
            if callable(texto_parece_pergunta_aberta_cb) and texto_parece_pergunta_aberta_cb(resposta_ia):
                if callable(registrar_pergunta_aberta_cb):
                    estado = registrar_pergunta_aberta_cb(
                        estado,
                        resposta_ia,
                        # O assunto explicito da conversa vence rotulos genericos
                        # como "conversa" e alvos operacionais mais antigos.
                        topico=alvo or ultimo_topico_conversa or habilidade or intencao,
                        origem=habilidade or intencao or "conversa",
                    )
                    log(f"🧠 [PERGUNTA ABERTA] registrada: {estado.get('pergunta_aberta_texto', '')[:90]}")
            elif callable(limpar_pergunta_aberta_cb):
                estado = limpar_pergunta_aberta_cb(estado)
        except Exception as e:
            log(f"⚠️ [PERGUNTA ABERTA] falha ao atualizar memória: {e}")
        try:
            if callable(registrar_promessa_conversacional_cb):
                estado = registrar_promessa_conversacional_cb(
                    estado,
                    resposta_ia,
                    alvo=alvo or estado.get("ultimo_alvo") or "",
                    conteudo=(
                        estado.get("ultima_opiniao")
                        or estado.get("ultima_afirmacao")
                        or conteudo_anterior_promessa
                        or ""
                    ),
                )
        except Exception as e:
            log(f"⚠️ [PROMESSA] falha ao registrar promessa conversacional: {e}")
    if intencao:
        estado["ultima_intencao"] = intencao
    if alvo:
        estado["ultimo_alvo"] = alvo
        alvo_norm = normalizar_texto_cb(alvo) if callable(normalizar_texto_cb) else alvo.lower()
        if any(x in alvo_norm for x in ["steam", "opera", "chrome", "edge", "vscode", "vs code", "visual studio code"]):
            estado["ultimo_app_janela"] = alvo
        if callable(eh_alvo_site_web_cb) and eh_alvo_site_web_cb(alvo_norm):
            estado["ultimo_site_aba"] = alvo
        if habilidade.lower() in {"arquivo", "arquivos", "sistema"} or intencao.upper() in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"}:
            alvo_limpo = str(alvo or "").strip()
            if alvo_limpo:
                import os
                if "." in os.path.basename(alvo_limpo):
                    estado["ultimo_arquivo"] = os.path.basename(alvo_limpo)
                    estado["ultimo_caminho_arquivo"] = alvo_limpo
                else:
                    estado["ultima_pasta"] = alvo_limpo
    if escopo:
        estado["ultimo_escopo"] = escopo
    if habilidade:
        estado["ultima_habilidade"] = habilidade
    if callable(atualizar_foco_vivo_cb):
        estado = atualizar_foco_vivo_cb(
            estado,
            texto=texto_usuario,
            resposta=resposta_ia,
            intencao=intencao,
            alvo=alvo,
            habilidade=habilidade,
            escopo=escopo,
        )
    estado["ts"] = time.time()
    return estado


def extrair_refino_contexto_mental(texto: str, resultado: Dict[str, Any] | None = None) -> Dict[str, str]:
    """Extrai campos curtos para refinar a memória mental compartilhada."""
    txt = str(texto or "").strip()
    dados = {
        "texto": txt,
        "intencao": "",
        "alvo": "",
        "escopo": "",
        "habilidade": "",
    }
    if not txt:
        return dados
    if isinstance(resultado, dict):
        dados["intencao"] = str(resultado.get("intent") or resultado.get("acao") or "").strip()
        params = resultado.get("params") if isinstance(resultado.get("params"), dict) else {}
        dados["alvo"] = str(
            params.get("nome_playlist")
            or params.get("nome_app")
            or params.get("query")
            or params.get("url")
            or params.get("alvo")
            or ""
        ).strip()
        dados["escopo"] = str(params.get("target") or params.get("modo") or params.get("platform") or "").strip()
        dados["habilidade"] = str(resultado.get("habilidade") or resultado.get("skill") or "").strip()
    return dados


def inferir_tipo_foco_vivo(
    intencao: str = "",
    habilidade: str = "",
    alvo: str = "",
    texto: str = "",
    resposta: str = "",
    *,
    normalizar_texto_cb=None,
) -> str:
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else lambda v: str(v or "").lower().strip()
    base = normalizar(" ".join([
        str(intencao or ""),
        str(habilidade or ""),
        str(alvo or ""),
        str(texto or ""),
        str(resposta or ""),
    ]))
    intent = str(intencao or "").upper().strip()
    hab = str(habilidade or "").lower().strip()
    if intent in {"CREATE_FOLDER", "DELETE_ITEM", "MOVE_ITEM", "CREATE_FILE"} or hab in {"arquivo", "arquivos"} or any(p in base for p in ["arquivo", "pasta", ".txt"]):
        return "arquivo"
    if intent in {"APP_OPEN", "CLOSE_APP", "MAXIMIZE_WINDOW"} or hab in {"janela", "app"}:
        return "janela"
    if intent in {"OPEN_URL", "CLOSE_TAB", "SITE_ENTER"} or hab in {"site", "navegador"}:
        return "site"
    if intent in {"SEARCH"} or hab in {"pesquisa", "search"}:
        return "pesquisa"
    if intent in {"WEATHER"} or hab in {"clima", "tempo"}:
        return "clima"
    if intent in {"EMAIL_READ", "EMAIL_SYNC", "NOTIFICATIONS"} or "email" in base:
        return "email"
    if intent in {"PLAYLIST_PLAY", "PLAYLIST_ADD", "PLAYLIST_LIST", "MUSIC_SEARCH", "MEDIA_CONTROL"} or hab in {"musica", "música", "playlist", "midia"}:
        return "musica"
    if intent in {"AGENDAR_LEMBRETE", "AGENDAR_ACAO", "LISTAR_AGENDAMENTOS", "CANCELAR_AGENDAMENTO"} or hab == "agenda":
        return "agenda"
    if hab == "conversa" or not intent:
        if any(p in base for p in ["opini", "acha", "presidente", "lula", "política", "politica"]):
            return "opiniao"
        return "conversa"
    return hab or "conversa"


def extrair_topico_foco_vivo(
    texto: str = "",
    resposta: str = "",
    alvo: str = "",
    habilidade: str = "",
    intencao: str = "",
    *,
    normalizar_texto_cb=None,
) -> str:
    alvo_limpo = str(alvo or "").strip()
    if alvo_limpo:
        return alvo_limpo[:120]
    normalizar = normalizar_texto_cb if callable(normalizar_texto_cb) else lambda v: str(v or "").lower().strip()
    t = normalizar(texto)
    for padrao in [
        r"(?:o que voce acha|o que você acha|voce acha|você acha|qual sua opiniao|qual sua opinião)\s+(?:do|da|de|sobre)?\s*(?P<tema>.+)$",
        r"(?:quem\s+e|quem\s+é|o\s+que\s+e|o\s+que\s+é|como\s+funciona|como\s+que\s+funciona|me\s+explica|explica|me\s+fala\s+sobre|fala\s+sobre|me\s+fala\s+de|fala\s+de)\s+(?P<tema>.+)$",
        r"(?:como assim|por que|porque|pq)\s+(?P<tema>.+)$",
    ]:
        m = re.search(padrao, t, flags=re.IGNORECASE)
        if m:
            tema = str(m.group("tema") or "").strip(" ?!.:,;")
            if tema:
                return tema[:120]
    if "lula" in t:
        return "presidente Lula"
    if "presidente" in t:
        return "presidente"
    hab = str(habilidade or "").strip()
    intent = str(intencao or "").strip()
    if hab:
        return hab[:120]
    if intent:
        return intent[:120]
    resp = str(resposta or "").strip()
    return resp[:120]


def atualizar_foco_vivo(
    estado: Dict[str, Any] | None,
    *,
    texto: str = "",
    resposta: str = "",
    intencao: str = "",
    alvo: str = "",
    habilidade: str = "",
    escopo: str = "",
    normalizar_texto_cb=None,
) -> Dict[str, Any]:
    estado = dict(estado or {})
    tipo = inferir_tipo_foco_vivo(
        intencao,
        habilidade,
        alvo,
        texto,
        resposta,
        normalizar_texto_cb=normalizar_texto_cb,
    )
    topico = extrair_topico_foco_vivo(
        texto,
        resposta,
        alvo,
        habilidade,
        intencao,
        normalizar_texto_cb=normalizar_texto_cb,
    )
    agora = time.time()
    tipos_conversacionais = {"conversa", "opiniao", "opinião"}
    dominio = "conversacional" if tipo in tipos_conversacionais else "operacional"
    prefixo = f"foco_{dominio}"
    topico_limpo = str(topico or "").strip()
    alvo_limpo = str(alvo or "").strip()
    topicos_genericos = {"", "conversa", "chat", "opinion", "opiniao", "opinião"}

    # Uma resposta conversacional genérica atualiza a fala, mas preserva o
    # assunto explícito que foi identificado na entrada imediatamente anterior.
    if dominio == "conversacional" and topico_limpo.lower() in topicos_genericos:
        topico_limpo = str(estado.get(f"{prefixo}_topico") or "").strip()
        if not alvo_limpo:
            alvo_limpo = str(estado.get(f"{prefixo}_alvo") or "").strip()

    possui_conteudo = bool(topico_limpo or alvo_limpo or resposta or intencao or habilidade)
    if dominio == "conversacional" and not possui_conteudo:
        return estado

    campos = {
        "tipo": tipo,
        "alvo": str(alvo_limpo or topico_limpo or "").strip()[:160],
        "topico": topico_limpo[:160],
        "habilidade": str(habilidade or tipo or "").strip()[:80],
        "intencao": str(intencao or "").strip()[:80],
        "texto": str(texto or "").strip()[:180],
        "resposta": str(resposta or "").strip()[:180],
        "escopo": str(escopo or "").strip()[:80],
    }
    for chave, valor in campos.items():
        estado[f"{prefixo}_{chave}"] = valor
        # Fachada de compatibilidade: continua representando o foco atualizado
        # mais recentemente para consumidores ainda não migrados.
        estado[f"foco_vivo_{chave}"] = valor
    estado[f"{prefixo}_ts"] = agora
    estado["foco_vivo_ts"] = agora
    estado["ts"] = agora

    dominio_especifico = {
        "janela": "app",
        "app": "app",
        "site": "site",
        "navegador": "site",
        "musica": "musica",
        "música": "musica",
        "playlist": "musica",
        "midia": "musica",
        "arquivo": "arquivo",
        "arquivos": "arquivo",
        "iot": "iot",
    }.get(str(tipo or "").strip().lower())
    if dominio_especifico:
        focos = dict(estado.get("focos_por_dominio") or {})
        focos[dominio_especifico] = {**campos, "ts": agora}
        estado["focos_por_dominio"] = focos

    entrada_norm = str(texto or "").strip().lower()
    referencia_generica = entrada_norm in {
        "como assim", "como assim?", "isso", "essa", "esse", "ela", "ele",
        "pode explicar", "explica melhor", "continua", "pode continuar",
    }
    if (alvo_limpo or (topico_limpo and topico_limpo.lower() not in topicos_genericos)) and not referencia_generica:
        estado["topico_explicito_atual"] = str(alvo_limpo or topico_limpo)[:160]
        estado["topico_explicito_origem"] = dominio
        estado["topico_explicito_ts"] = agora
    return estado


def foco_por_dominio(
    estado_atual: Dict[str, Any] | None,
    dominio: str,
    *,
    ttl_s: float = 900.0,
) -> Dict[str, Any]:
    """Retorna o último foco de uma habilidade sem competir com outros domínios."""
    try:
        estado = dict(estado_atual or {})
        chave = str(dominio or "").strip().lower()
        foco = dict((estado.get("focos_por_dominio") or {}).get(chave) or {})
        ts = float(foco.get("ts") or 0.0)
        if not ts or time.time() - ts > ttl_s:
            return {}
        foco["dominio"] = chave
        foco["idade_s"] = max(0.0, time.time() - ts)
        return foco
    except Exception:
        return {}


def foco_vivo_atual(
    estado_atual: Dict[str, Any] | None,
    *,
    ttl_s: float = 480.0,
    dominio: str = "auto",
) -> Dict[str, Any]:
    try:
        estado = dict(estado_atual or {})
        dominio_norm = str(dominio or "auto").strip().lower()
        if dominio_norm in {"conversa", "conversacional"}:
            prefixo = "foco_conversacional"
        elif dominio_norm in {"operacao", "operação", "operacional"}:
            prefixo = "foco_operacional"
        else:
            ts_conversa = float(estado.get("foco_conversacional_ts") or 0.0)
            ts_operacao = float(estado.get("foco_operacional_ts") or 0.0)
            prefixo = "foco_conversacional" if ts_conversa >= ts_operacao else "foco_operacional"

        ts = float(estado.get(f"{prefixo}_ts") or 0.0)
        if not ts:
            # Compatibilidade com memórias gravadas antes da separação C2.
            tipo_legado = str(estado.get("foco_vivo_tipo") or "").strip().lower()
            legado_conversa = tipo_legado in {"conversa", "opiniao", "opinião"}
            if dominio_norm in {"conversa", "conversacional"} and not legado_conversa:
                return {}
            if dominio_norm in {"operacao", "operação", "operacional"} and legado_conversa:
                return {}
            prefixo = "foco_vivo"
            ts = float(estado.get("foco_vivo_ts") or 0.0)
        if not ts or time.time() - ts > ttl_s:
            return {}
        return {
            "tipo": str(estado.get(f"{prefixo}_tipo") or "").strip(),
            "alvo": str(estado.get(f"{prefixo}_alvo") or "").strip(),
            "topico": str(estado.get(f"{prefixo}_topico") or "").strip(),
            "habilidade": str(estado.get(f"{prefixo}_habilidade") or "").strip(),
            "intencao": str(estado.get(f"{prefixo}_intencao") or "").strip(),
            "texto": str(estado.get(f"{prefixo}_texto") or "").strip(),
            "resposta": str(estado.get(f"{prefixo}_resposta") or "").strip(),
            "escopo": str(estado.get(f"{prefixo}_escopo") or "").strip(),
            "dominio": "conversacional" if "conversacional" in prefixo else "operacional" if "operacional" in prefixo else "legado",
            "idade_s": max(0.0, time.time() - ts),
        }
    except Exception:
        return {}


def texto_pede_repeticao_curta(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(str(texto or ""))
    if not t or len(t.split()) > 8:
        return False
    gatilhos = [
        "tenta de novo",
        "de novo",
        "tenta novamente",
        "novamente",
        "vai de novo",
        "faz de novo",
        "outra vez",
        "mais uma vez",
        "tenta outra vez",
    ]
    return any(g in t for g in gatilhos)


def resolver_repeticao_ultima_acao(
    texto: str,
    estado_atual: Dict[str, Any] | None,
    normalizar_texto_cb,
):
    if not texto_pede_repeticao_curta(texto, normalizar_texto_cb):
        return None
    estado = dict(estado_atual or {})
    if not bool(estado.get("ultima_acao_reexecutavel")):
        return None
    intent = str(estado.get("ultima_acao_intent") or "").strip().upper()
    params = estado.get("ultima_acao_params")
    if not intent or not isinstance(params, dict):
        return None
    return {"intent": intent, "params": dict(params)}


def contexto_musical_ativo(ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        if str(ultima_playlist or "").strip():
            return True
        if str(playlist_state.get("name") or "").strip():
            return True
        if str(playlist_state.get("last_url") or "").strip():
            return True
    except Exception:
        pass
    return False


def contexto_mental_ativo(mente_integrada_estado: Dict[str, Any], ultima_playlist: Any, playlist_state: Dict[str, Any]) -> bool:
    try:
        estado = dict(mente_integrada_estado or {})
        if str(estado.get("ultima_entrada") or "").strip():
            return True
        if str(estado.get("ultima_intencao") or "").strip():
            return True
        if str(estado.get("ultimo_alvo") or "").strip():
            return True
        if str(estado.get("ultima_habilidade") or "").strip():
            return True
    except Exception:
        pass
    return contexto_musical_ativo(ultima_playlist, playlist_state)


def texto_depende_de_contexto(texto: str, normalizar_texto_cb) -> bool:
    t = normalizar_texto_cb(texto)
    if not t:
        return False
    palavras = t.split()
    if len(palavras) > 7:
        return False
    gatilhos = [
        "essa", "esse", "isso", "ele", "ela", "aqui", "ali", "tambem", "também",
        "de novo", "mais uma", "mais um", "essa tambem", "esse tambem",
        "essa também", "esse também", "essa aqui", "esse aqui", "essa ai", "esse ai",
    ]
    return any(g in t for g in gatilhos)


def fluxo_prioritario_da_ia(texto: str, normalizar_texto_cb, texto_depende_de_contexto_cb) -> bool:
    t = normalizar_texto_cb(texto)
    if not t:
        return False
    if any(p in t for p in ["playlist", "música", "musica", "site", "web", "aba", "janela", "foco", "tela cheia", "fullscreen", "opera", "chrome", "edge", "vscode"]):
        if texto_depende_de_contexto_cb(t):
            return True
        if any(p in t for p in ["coloca", "toca", "abre", "abra", "entra", "vai", "mostra", "lista", "quais"]):
            return True
    return False
