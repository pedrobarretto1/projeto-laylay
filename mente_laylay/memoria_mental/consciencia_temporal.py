"""Linha do tempo, passagem de tempo e pendências vivas da Laylay."""

from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Dict, Iterable

from mente_laylay.memoria_mental.interpretacao_temporal import (
    interpretar_referencia_temporal,
    proxima_ocorrencia,
)


def estado_temporal_inicial() -> Dict[str, Any]:
    return {
        "primeira_interacao_ts": 0.0,
        "ultima_interacao_ts": 0.0,
        "intervalo_desde_ultima_interacao_s": 0.0,
        "ultimo_texto": "",
        "interacoes_total": 0,
        "inicio_sessao_ts": 0.0,
        "ultima_interacao_sessao_ts": 0.0,
        "interacoes_sessao": 0,
        "tempo_vivido_sessao_s": 0.0,
        "tempo_vivido_total_s": 0.0,
        "sessoes_total": 0,
        "linha_do_tempo": [],
        "pendencias_vivas": [],
        "estatisticas_duracao": {},
        "conclusao_ambigua": {},
        "evento_turno": {},
        "proatividade_temporal": {},
        "versao": 2,
    }


def _normalizar(texto: Any) -> str:
    bruto = str(texto or "").casefold()
    sem_acento = unicodedata.normalize("NFKD", bruto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acento).strip()


def descrever_tempo_relativo(ts: float, *, agora: float | None = None) -> str:
    instante = float(agora if agora is not None else time.time())
    delta = max(0.0, instante - float(ts or instante))
    if delta < 60:
        return "agora há pouco"
    if delta < 3600:
        minutos = max(1, int(delta // 60))
        return f"há {minutos} minuto" + ("s" if minutos != 1 else "")
    if delta < 86400:
        horas = max(1, int(delta // 3600))
        return f"há {horas} hora" + ("s" if horas != 1 else "")
    dias = max(1, int(delta // 86400))
    if dias == 1:
        return "ontem"
    if dias < 7:
        return f"há {dias} dias"
    semanas = dias // 7
    if dias < 35:
        return f"há {semanas} semana" + ("s" if semanas != 1 else "")
    meses = max(1, dias // 30)
    if dias < 365:
        return f"há {meses} mes" + ("es" if meses != 1 else "")
    anos = max(1, dias // 365)
    return f"há {anos} ano" + ("s" if anos != 1 else "")


def _tipo_evento(texto: str) -> str:
    if re.search(r"\b(projeto|sistema|programa|codigo|aplicacao|app)\b", texto):
        return "projeto"
    if re.search(r"\b(planta|muda|vaso|semente)\b", texto):
        return "planta"
    if re.search(r"\b(jogo|game|jogando|zerar|zerei)\b", texto):
        return "jogo"
    if re.search(r"\b(prova|estudo|estudando|curso|apresentacao|trabalho da escola)\b", texto):
        return "estudo"
    if re.search(r"\b(consulta|medico|dentista|reuniao|compromisso|viagem)\b", texto):
        return "evento"
    return ""


def _tokens(texto: str) -> set[str]:
    ignorar = {
        "eu", "uma", "um", "meu", "minha", "novo", "nova", "que", "de", "do", "da", "para", "com", "esse", "essa",
        "comecei", "iniciei", "estou", "fazendo", "jogando", "tenho", "projeto", "sistema", "programa", "jogo", "estudo", "consulta",
    }
    return {t for t in re.findall(r"[a-z0-9_]{3,}", _normalizar(texto)) if t not in ignorar}


def _rotulo_assunto(texto: Any) -> str:
    rotulo = re.sub(
        r"^(?:eu\s+)?(?:comecei|iniciei|estou fazendo|to fazendo|estou jogando|to jogando|comprei|plantei)\s+",
        "", _normalizar(texto),
    ).strip(" .")
    return rotulo or str(texto or "pendência").strip()[:120]


def selecionar_eventos_temporais(
    eventos: Iterable[dict],
    texto_atual: str,
    *,
    agora: float,
    limite: int = 6,
) -> list[dict]:
    """Recência facilita a lembrança, mas uma relação explícita recupera eventos antigos."""
    tokens_atuais = _tokens(texto_atual)
    candidatos = []
    for ordem, evento in enumerate(list(eventos or [])):
        tokens_evento = _tokens(evento.get("assunto") or evento.get("texto") or "")
        sobreposicao = len(tokens_atuais & tokens_evento)
        if tokens_atuais and not sobreposicao:
            continue
        idade_dias = max(0.0, float(agora) - float(evento.get("ts") or 0.0)) / 86400.0
        recencia = 1.0 / (1.0 + idade_dias / 30.0)
        importancia = 0.4 if evento.get("status") in {"concluida", "evidencia_conclusao"} else 0.0
        candidatos.append((sobreposicao * 5.0 + recencia + importancia, ordem, dict(evento)))
    candidatos.sort(key=lambda item: (item[0], item[1]), reverse=True)
    escolhidos = [item[2] for item in candidatos[:max(1, int(limite))]]
    return sorted(escolhidos, key=lambda item: float(item.get("ts") or 0.0))


def _encontrar_pendencia(pendencias: Iterable[dict], texto: str, tipo: str = "") -> int:
    tokens_texto = _tokens(texto)
    lista = list(pendencias)
    melhor_indice, melhor_pontos = -1, 0
    for indice, item in enumerate(lista):
        if str(item.get("status") or "aberta") != "aberta":
            continue
        pontos = len(tokens_texto & _tokens(item.get("assunto") or item.get("texto") or ""))
        if tipo and str(item.get("tipo") or "") == tipo:
            pontos += 1
        if pontos > melhor_pontos:
            melhor_indice, melhor_pontos = indice, pontos
    if melhor_indice < 0 and len([p for p in lista if p.get("status", "aberta") == "aberta"]) == 1:
        return next(i for i, p in enumerate(lista) if p.get("status", "aberta") == "aberta")
    return melhor_indice


def _candidatos_abertos(pendencias: Iterable[dict], texto: str, tipo: str = "") -> list[int]:
    tokens_texto = _tokens(texto)
    pontuados = []
    for indice, item in enumerate(list(pendencias)):
        if str(item.get("status") or "aberta") != "aberta":
            continue
        pontos = len(tokens_texto & _tokens(item.get("assunto") or item.get("texto") or ""))
        if tipo and str(item.get("tipo") or "") == tipo:
            pontos += 1
        pontuados.append((pontos, indice))
    if not pontuados:
        return []
    maior = max(pontos for pontos, _ in pontuados)
    if maior <= 0:
        return [indice for _pontos, indice in pontuados]
    return [indice for pontos, indice in pontuados if pontos == maior]


def _registrar_duracao(estatisticas: Dict[str, Any], tipo: str, duracao_s: float) -> Dict[str, Any]:
    saida = dict(estatisticas or {})
    chave = str(tipo or "evento")
    atual = dict(saida.get(chave) or {})
    amostras = int(atual.get("amostras") or 0) + 1
    media = float(atual.get("media_s") or 0.0)
    duracao = max(0.0, float(duracao_s or 0.0))
    atual.update(
        amostras=amostras,
        media_s=round(media + (duracao - media) / amostras, 2),
        minimo_s=round(min(float(atual.get("minimo_s") or duracao), duracao), 2),
        maximo_s=round(max(float(atual.get("maximo_s") or 0.0), duracao), 2),
        ultima_duracao_s=round(duracao, 2),
    )
    saida[chave] = atual
    return saida


def _concluir_pendencia(
    pendencias: list[dict],
    indice: int,
    linha: list[dict],
    estatisticas: Dict[str, Any],
    *,
    instante: float,
    texto_original: str,
) -> tuple[list[dict], list[dict], Dict[str, Any], dict]:
    item = dict(pendencias[indice])
    inicio = float(item.get("iniciado_em") or instante)
    duracao = max(0.0, instante - inicio)
    tipo = str(item.get("tipo") or "evento")
    estatisticas = _registrar_duracao(estatisticas, tipo, duracao)
    concluida = {
        "id": f"evt-{int(instante * 1000)}",
        "tipo": tipo,
        "assunto": item.get("assunto") or texto_original,
        "texto": texto_original[:300],
        "status": "concluida",
        "ts": instante,
        "duracao_s": duracao,
        "origem_id": item.get("id"),
    }
    linha.append(concluida)
    recorrencia = dict(item.get("recorrencia") or {})
    if recorrencia:
        base = float(item.get("data_alvo_ts") or instante)
        proxima = proxima_ocorrencia(base, recorrencia, depois_de=instante)
        pendencias[indice] = {
            **item,
            "status": "aberta",
            "iniciado_em": instante,
            "ultima_mencao_ts": instante,
            "ultima_conclusao_ts": instante,
            "data_alvo_ts": proxima,
            "ocorrencias_concluidas": int(item.get("ocorrencias_concluidas") or 0) + 1,
            "progresso": 0,
        }
        concluida["proxima_ocorrencia_ts"] = proxima
    else:
        pendencias[indice] = {
            **item, "status": "concluida", "concluida_em": instante,
            "ultima_mencao_ts": instante, "progresso": 100,
        }
    return pendencias, linha, estatisticas, concluida


def atualizar_consciencia_temporal(
    estado_atual: Dict[str, Any] | None,
    texto_usuario: str,
    *,
    resposta_ia: str = "",
    agora: float | None = None,
) -> Dict[str, Any]:
    estado = {**estado_temporal_inicial(), **dict(estado_atual or {})}
    estado["evento_turno"] = {}
    instante = float(agora if agora is not None else time.time())
    texto_original = re.sub(r"\s+", " ", str(texto_usuario or "")).strip()
    texto = _normalizar(texto_original)
    if not texto:
        return estado

    ultima_ts = float(estado.get("ultima_interacao_ts") or 0.0)
    if texto == str(estado.get("ultimo_texto") or "") and ultima_ts and instante - ultima_ts < 2.0:
        return estado

    if not estado.get("primeira_interacao_ts"):
        estado["primeira_interacao_ts"] = instante
    estado["intervalo_desde_ultima_interacao_s"] = max(0.0, instante - ultima_ts) if ultima_ts else 0.0
    estado["interacoes_total"] = int(estado.get("interacoes_total") or 0) + 1
    estado["ultima_interacao_ts"] = instante
    estado["ultimo_texto"] = texto

    ultima_sessao = float(estado.get("ultima_interacao_sessao_ts") or 0.0)
    if not ultima_sessao or instante - ultima_sessao > 1800:
        estado["inicio_sessao_ts"] = instante
        estado["interacoes_sessao"] = 1
        estado["tempo_vivido_sessao_s"] = 0.0
        estado["sessoes_total"] = int(estado.get("sessoes_total") or 0) + 1
    else:
        acrescimo_vivido = min(300.0, instante - ultima_sessao)
        estado["interacoes_sessao"] = int(estado.get("interacoes_sessao") or 0) + 1
        estado["tempo_vivido_sessao_s"] = float(estado.get("tempo_vivido_sessao_s") or 0.0) + acrescimo_vivido
        estado["tempo_vivido_total_s"] = float(estado.get("tempo_vivido_total_s") or 0.0) + acrescimo_vivido
    estado["ultima_interacao_sessao_ts"] = instante

    linha = list(estado.get("linha_do_tempo") or [])
    pendencias = list(estado.get("pendencias_vivas") or [])
    estatisticas = dict(estado.get("estatisticas_duracao") or {})
    tipo = _tipo_evento(texto)
    conclusao = bool(re.search(r"\b(terminei|finalizei|conclui|zerei|passei|deu tudo certo|consegui terminar)\b", texto))

    ambigua = dict(estado.get("conclusao_ambigua") or {})
    if ambigua.get("status") == "aguardando_confirmacao" and not conclusao:
        if re.search(r"\b(?:nenhum|nenhuma|deixa pra la|cancela|esquece)\b", texto):
            estado["conclusao_ambigua"] = {}
            estado["evento_turno"] = {"tipo": "conclusao_cancelada"}
        else:
            ids = {str(item) for item in ambigua.get("candidatos_ids") or []}
            candidatos = [
                indice for indice, item in enumerate(pendencias)
                if str(item.get("id") or "") in ids and item.get("status", "aberta") == "aberta"
            ]
            correspondentes = [
                indice for indice in candidatos
                if _tokens(texto) & _tokens(pendencias[indice].get("assunto") or "")
            ]
            ordinal = 0 if re.search(r"\b(?:primeiro|primeira)\b", texto) else 1 if re.search(r"\b(?:segundo|segunda)\b", texto) else -1
            if not correspondentes and 0 <= ordinal < len(candidatos):
                correspondentes = [candidatos[ordinal]]
            if len(correspondentes) == 1:
                pendencias, linha, estatisticas, concluida = _concluir_pendencia(
                    pendencias, correspondentes[0], linha, estatisticas,
                    instante=instante, texto_original=texto_original,
                )
                estado["conclusao_ambigua"] = {}
                estado["evento_turno"] = {
                    "tipo": "conclusao_confirmada",
                    "assunto": concluida.get("assunto"),
                    "duracao_s": concluida.get("duracao_s"),
                }

    if conclusao:
        candidatos = _candidatos_abertos(pendencias, texto, tipo)
        if len(candidatos) == 1:
            pendencias, linha, estatisticas, concluida = _concluir_pendencia(
                pendencias, candidatos[0], linha, estatisticas,
                instante=instante, texto_original=texto_original,
            )
            estado["conclusao_ambigua"] = {}
            estado["evento_turno"] = {
                "tipo": "conclusao_registrada",
                "assunto": concluida.get("assunto"),
                "duracao_s": concluida.get("duracao_s"),
            }
        elif len(candidatos) > 1:
            itens = [pendencias[indice] for indice in candidatos[:4]]
            estado["conclusao_ambigua"] = {
                "status": "aguardando_confirmacao",
                "candidatos_ids": [item.get("id") for item in itens],
                "candidatos": [_rotulo_assunto(item.get("assunto") or item.get("tipo") or "pendência")[:120] for item in itens],
                "criada_em": instante,
            }
            estado["evento_turno"] = {
                "tipo": "confirmacao_conclusao_necessaria",
                "candidatos": list(estado["conclusao_ambigua"]["candidatos"]),
            }
    else:
        inicio = bool(re.search(r"\b(comecei|iniciei|to fazendo|estou fazendo|to jogando|estou jogando|comprei|plantei|vou comecar|vou iniciar)\b", texto))
        referencia_temporal = interpretar_referencia_temporal(texto, agora=instante)
        futuro_ts = float(referencia_temporal.get("data_alvo_ts") or 0.0)
        recorrencia = dict(referencia_temporal.get("recorrencia") or {})
        futuro = bool(futuro_ts or recorrencia or re.search(r"\b(vou ter|tenho|vai acontecer|esta marcado|ta marcado)\b", texto) and tipo in {"estudo", "evento"})
        if tipo and (inicio or futuro):
            evento = {
                "id": f"evt-{int(instante * 1000)}",
                "tipo": tipo,
                "assunto": texto_original[:180],
                "texto": texto_original[:300],
                "status": "aberta",
                "iniciado_em": instante,
                "ultima_mencao_ts": instante,
                "data_alvo_ts": futuro_ts,
                "recorrencia": recorrencia,
                "referencia_temporal_origem": referencia_temporal.get("origem") or "",
                "referencia_temporal_confianca": float(referencia_temporal.get("confianca") or 0.0),
                "progresso": 0,
                "origem": "conversa",
            }
            duplicada = any(
                p.get("status", "aberta") == "aberta"
                and p.get("tipo") == tipo
                and len(_tokens(p.get("assunto")) & _tokens(texto_original)) >= 1
                for p in pendencias
            )
            if not duplicada:
                pendencias.append(evento)
                linha.append({**evento, "ts": instante})
        elif tipo and re.search(r"\b(migrei|mudei|avancei|testei|arrumei|melhorei|implementei|continuei|voltei|metade|\d{1,3}\s*%)\b", texto):
            indice = _encontrar_pendencia(pendencias, texto, tipo)
            if indice >= 0:
                percentual = re.search(r"\b(\d{1,3})\s*%", texto)
                progresso = int(percentual.group(1)) if percentual else 50 if "metade" in texto else int(pendencias[indice].get("progresso") or 0)
                pendencias[indice] = {
                    **pendencias[indice], "ultima_mencao_ts": instante,
                    "progresso": max(0, min(progresso, 99)),
                }
                linha.append({
                    "id": f"evt-{int(instante * 1000)}",
                    "tipo": tipo,
                    "assunto": pendencias[indice].get("assunto") or texto_original,
                    "texto": texto_original[:300],
                    "status": "progresso",
                    "ts": instante,
                    "origem_id": pendencias[indice].get("id"),
                    "progresso": pendencias[indice].get("progresso", 0),
                })

    estado["linha_do_tempo"] = linha[-120:]
    estado["pendencias_vivas"] = pendencias[-40:]
    estado["estatisticas_duracao"] = estatisticas
    estado["versao"] = 2
    return estado


def registrar_evento_visual_temporal(
    estado_atual: Dict[str, Any] | None,
    descricao: str,
    *,
    memoria_id: str = "",
    contexto: Dict[str, Any] | None = None,
    agora: float | None = None,
) -> Dict[str, Any]:
    """Liga uma memória visual relevante à linha do tempo sem concluir nada sozinha."""
    estado = {**estado_temporal_inicial(), **dict(estado_atual or {})}
    instante = float(agora if agora is not None else time.time())
    texto = _normalizar(descricao)
    tipo = _tipo_evento(texto)
    if not tipo or not re.search(r"\b(projeto|codigo|jogo|estudo|planta|concluiu|finalizou|avancou|programando|jogando)\b", texto):
        return estado
    linha = list(estado.get("linha_do_tempo") or [])
    if memoria_id and any(str(item.get("memoria_visual_id") or "") == memoria_id for item in linha):
        return estado
    status = "evidencia_conclusao" if re.search(
        r"\b(concluiu|concluido|concluida|finalizou|finalizado|finalizada|terminou|terminado|terminada|zerou|zerado|zerada)\b",
        texto,
    ) else "observacao_visual"
    linha.append({
        "id": f"vis-{int(instante * 1000)}",
        "tipo": tipo,
        "assunto": str(descricao or "")[:180],
        "texto": str(descricao or "")[:300],
        "status": status,
        "ts": instante,
        "origem": "memoria_visual",
        "memoria_visual_id": str(memoria_id or "")[:80],
        "aplicativo": str((contexto or {}).get("exe") or (contexto or {}).get("programa") or "")[:80],
    })
    pendencias = list(estado.get("pendencias_vivas") or [])
    indice = _encontrar_pendencia(pendencias, texto, tipo)
    if indice >= 0:
        pendencias[indice] = {
            **pendencias[indice], "ultima_observacao_visual_ts": instante,
            "memoria_visual_id": str(memoria_id or "")[:80],
        }
    estado["linha_do_tempo"] = linha[-120:]
    estado["pendencias_vivas"] = pendencias[-40:]
    return estado


def resumo_temporal_para_prompt(
    estado_atual: Dict[str, Any] | None,
    *,
    texto_usuario: str = "",
    agora: float | None = None,
) -> str:
    estado = {**estado_temporal_inicial(), **dict(estado_atual or {})}
    instante = float(agora if agora is not None else time.time())
    ultima = float(estado.get("ultima_interacao_ts") or 0.0)
    intervalo = float(estado.get("intervalo_desde_ultima_interacao_s") or 0.0)
    linhas = ["--- CONSCIÊNCIA TEMPORAL ---"]
    if ultima:
        if intervalo > 0:
            linhas.append(
                "Intervalo antes desta interação: "
                f"{descrever_tempo_relativo(instante - intervalo, agora=instante)}."
            )
        else:
            linhas.append("Esta é a primeira interação temporal registrada.")
    inicio = float(estado.get("inicio_sessao_ts") or 0.0)
    if inicio:
        duracao = max(0, int(float(estado.get("tempo_vivido_sessao_s") or 0.0) // 60))
        linhas.append(
            f"Tempo de convivência ativa nesta sessão: cerca de {duracao} min, "
            f"{int(estado.get('interacoes_sessao') or 0)} interações."
        )
    tokens_atuais = _tokens(texto_usuario)
    abertas = [p for p in estado.get("pendencias_vivas", []) if p.get("status", "aberta") == "aberta"]
    relevantes = []
    for item in abertas:
        alvo_ts = float(item.get("data_alvo_ts") or 0.0)
        prazo_proximo = bool(alvo_ts and -86400 <= alvo_ts - instante <= 2 * 86400)
        relacionada = bool(tokens_atuais and tokens_atuais & _tokens(item.get("assunto") or item.get("texto") or ""))
        if relacionada or prazo_proximo:
            relevantes.append(item)
    if relevantes:
        partes = []
        for item in relevantes[-5:]:
            idade = descrever_tempo_relativo(float(item.get("iniciado_em") or 0.0), agora=instante)
            alvo_ts = float(item.get("data_alvo_ts") or 0.0)
            prazo = ""
            if alvo_ts:
                delta = alvo_ts - instante
                prazo = " | vencida" if delta < 0 else f" | falta cerca de {max(1, int(delta // 86400))} dia(s)"
            recorrencia = dict(item.get("recorrencia") or {})
            repete = f" | recorrência {recorrencia.get('frequencia')}" if recorrencia else ""
            progresso = int(item.get("progresso") or 0)
            andamento = f" | progresso informado {progresso}%" if progresso else ""
            partes.append(f"{item.get('tipo')}: {item.get('assunto')} ({idade}{prazo}{repete}{andamento})")
        linhas.append("Pendências vivas: " + " || ".join(partes))
        linhas.append(
            "Só retome uma pendência se a fala atual tiver relação com ela ou se o prazo estiver próximo; não cobre assuntos aleatórios."
        )
        estatisticas = dict(estado.get("estatisticas_duracao") or {})
        estimativas = []
        for item in relevantes:
            metrica = dict(estatisticas.get(str(item.get("tipo") or "")) or {})
            if int(metrica.get("amostras") or 0) < 2:
                continue
            dias_medios = float(metrica.get("media_s") or 0.0) / 86400.0
            estimativas.append(
                f"{item.get('tipo')}: média histórica aproximada de {dias_medios:.1f} dia(s) "
                f"em {int(metrica.get('amostras') or 0)} conclusão(ões)"
            )
        if estimativas:
            linhas.append(
                "Duração aprendida: " + " || ".join(estimativas[:3])
                + ". Trate como estimativa, nunca como prazo garantido."
            )
    if tokens_atuais:
        eventos_relacionados = selecionar_eventos_temporais(
            estado.get("linha_do_tempo", []), texto_usuario,
            agora=instante, limite=6,
        )
        if eventos_relacionados:
            linhas.append(
                "Linha do tempo relacionada: "
                + " || ".join(
                    f"{evento.get('status')}: {evento.get('texto') or evento.get('assunto')} "
                    f"({descrever_tempo_relativo(float(evento.get('ts') or 0.0), agora=instante)})"
                    for evento in eventos_relacionados
                )
            )
    ambigua = dict(estado.get("conclusao_ambigua") or {})
    if ambigua.get("status") == "aguardando_confirmacao":
        linhas.append(
            "Conclusão aguardando confirmação: "
            + " | ".join(str(item) for item in ambigua.get("candidatos") or [])
            + ". Não encerre nenhuma delas sem o usuário identificar qual foi."
        )
    return "\n".join(linhas)
