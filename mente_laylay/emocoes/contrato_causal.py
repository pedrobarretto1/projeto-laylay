"""Contrato canônico de eventos emocionais causais da mente única."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
import time
from typing import Any, Mapping


NATUREZAS_EVIDENCIA_EMOCIONAL = frozenset({
    "fato_observado",
    "inferencia",
    "leitura_social",
    "preferencia_aprendida",
})
RESPONSABILIDADES_EMOCIONAIS = frozenset({
    "sistema", "laylay", "usuario", "ambigua",
})
SENSIBILIDADES_EMOCIONAIS = frozenset({
    "normal", "sensivel", "vulneravel",
})


def _proporcao(valor: Any) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0.0
    if numero > 1.0:
        numero /= 100.0
    return round(max(0.0, min(1.0, numero)), 3)


@dataclass(frozen=True, slots=True)
class EventoEmocionalCausal:
    origem: str
    causa: str
    evidencia_ref: str
    natureza_evidencia: str
    responsabilidade: str
    confianca: float
    relevancia: float
    novidade: float
    intensidade: int
    sensibilidade: str
    alvo: str
    validade: dict[str, Any]
    permite_expressao: bool
    emocao: str
    nivel: int
    motivo_expressao: str
    arco: str
    ts: float
    autoriza_execucao: bool = False
    persistencia_pessoal: bool = False
    versao: int = 1

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


def criar_evento_emocional_causal(
    *,
    origem: str,
    causa: str,
    evidencia_ref: str,
    natureza_evidencia: str,
    responsabilidade: str = "ambigua",
    confianca: float = 0.0,
    relevancia: float = 0.0,
    novidade: float = 0.0,
    intensidade: int = 1,
    sensibilidade: str = "normal",
    alvo: str = "",
    validade_s: float = 120.0,
    permite_expressao: bool = False,
    emocao: str = "calma",
    nivel: int = 1,
    motivo_expressao: str = "evento_neutro_sem_expressao",
    arco: str = "neutro",
    ts: float | None = None,
) -> dict[str, Any]:
    instante = float(time.time() if ts is None else ts)
    origem_limpa = str(origem or "").strip()[:120]
    causa_limpa = str(causa or "").strip()[:300]
    evidencia_limpa = str(evidencia_ref or "").strip()[:240]
    natureza = str(natureza_evidencia or "").strip().casefold()
    confianca_limpa = _proporcao(confianca)
    responsabilidade_limpa = str(
        responsabilidade or "ambigua"
    ).strip().casefold()
    if responsabilidade_limpa not in RESPONSABILIDADES_EMOCIONAIS:
        responsabilidade_limpa = "ambigua"
    if responsabilidade_limpa != "ambigua" and confianca_limpa < 0.90:
        responsabilidade_limpa = "ambigua"
    sensibilidade_limpa = str(sensibilidade or "normal").strip().casefold()
    if sensibilidade_limpa not in SENSIBILIDADES_EMOCIONAIS:
        sensibilidade_limpa = "sensivel"
    try:
        duracao = max(0.0, float(validade_s))
    except (TypeError, ValueError):
        duracao = 0.0
    causa_rastreavel = bool(
        origem_limpa
        and causa_limpa
        and evidencia_limpa
        and natureza in NATUREZAS_EVIDENCIA_EMOCIONAL
        and duracao > 0.0
    )
    validade = {
        "valido": causa_rastreavel,
        "inicio_ts": instante,
        "expira_ts": instante + duracao if causa_rastreavel else instante,
        "motivo": (
            "causa_rastreavel" if causa_rastreavel else "causa_nao_rastreavel"
        ),
    }
    permite = bool(permite_expressao and causa_rastreavel)
    emocao_limpa = str(emocao or "calma").strip().casefold() or "calma"
    nivel_limpo = max(1, min(3, int(nivel or 1)))
    intensidade_limpa = max(0, min(3, int(intensidade or 0)))
    if not causa_rastreavel:
        emocao_limpa, nivel_limpo, intensidade_limpa = "calma", 1, 0

    return EventoEmocionalCausal(
        origem=origem_limpa,
        causa=causa_limpa,
        evidencia_ref=evidencia_limpa,
        natureza_evidencia=(
            natureza if natureza in NATUREZAS_EVIDENCIA_EMOCIONAL else "inferencia"
        ),
        responsabilidade=responsabilidade_limpa,
        confianca=confianca_limpa,
        relevancia=_proporcao(relevancia),
        novidade=_proporcao(novidade),
        intensidade=intensidade_limpa,
        sensibilidade=sensibilidade_limpa,
        alvo=str(alvo or "").strip()[:160],
        validade=validade,
        permite_expressao=permite,
        emocao=emocao_limpa,
        nivel=nivel_limpo,
        motivo_expressao=str(motivo_expressao or "").strip()[:160],
        arco=str(arco or "neutro").strip()[:80],
        ts=instante,
    ).como_dict()


def criar_evento_expressao_solicitada(
    pedido: Mapping[str, Any], *, turno_id: str, ts: float | None = None,
) -> dict[str, Any]:
    """Pedido tipado de encenação, temporário e sem autoridade operacional."""
    dados = dict(pedido or {})
    if (dados.get("natureza") != "expressao_solicitada" or dados.get("alvo") != "laylay"
        or dados.get("autoriza_execucao") is not False or not str(turno_id).strip()
        or not str(dados.get("trecho_evidencia") or "").strip()
        or dados.get("emocao") not in {"calma", "alegre", "triste", "brava", "irritada", "surpresa", "envergonhada", "debochada"}
        or dados.get("nivel") not in {1, 2, 3}):
        return {}
    return criar_evento_emocional_causal(
        origem="pedido_expressao_usuario", causa="expressão solicitada pelo usuário: " + dados["trecho_evidencia"],
        evidencia_ref="turno:" + str(turno_id), natureza_evidencia="fato_observado",
        responsabilidade="usuario", confianca=1.0, relevancia=1.0, novidade=1.0,
        intensidade=dados["nivel"], alvo="laylay", validade_s=60.0,
        permite_expressao=True, emocao=dados["emocao"], nivel=dados["nivel"],
        motivo_expressao="encenacao_pedida_explicitamente", arco="expressao_solicitada", ts=ts,
    )


def evento_tem_causa_rastreavel(evento: Mapping[str, Any] | None) -> bool:
    dados = dict(evento or {})
    validade = dict(dados.get("validade") or {})
    return bool(
        validade.get("valido") is True
        and str(dados.get("origem") or "").strip()
        and str(dados.get("causa") or "").strip()
        and str(dados.get("evidencia_ref") or "").strip()
        and str(dados.get("natureza_evidencia") or "").strip().casefold()
        in NATUREZAS_EVIDENCIA_EMOCIONAL
        and dados.get("autoriza_execucao") is False
    )


def evento_esta_ativo(
    evento: Mapping[str, Any] | None,
    *,
    agora: float | None = None,
) -> bool:
    """Validade temporal é checada no consumo, preservando o registro histórico."""
    if not evento_tem_causa_rastreavel(evento):
        return False
    validade = dict(dict(evento or {}).get("validade") or {})
    instante = float(time.time() if agora is None else agora)
    try:
        inicio = float(validade["inicio_ts"])
        fim = float(validade["expira_ts"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    return inicio <= instante < fim


def evento_pode_alterar_estado(
    evento: Mapping[str, Any] | None,
    *,
    agora: float | None = None,
) -> bool:
    return bool(
        evento_esta_ativo(evento, agora=agora)
        and dict(evento or {}).get("permite_expressao") is True
    )


def criar_evento_feedback_comunicativo(
    tipo: str,
    proveniencia: Mapping[str, Any],
) -> dict[str, Any]:
    """Registra feedback já classificado e validado, sem escolher uma emoção."""
    if tipo not in {"aceitacao", "recusa", "correcao", "repeticao", "silencio"}:
        return {}
    fonte = dict(proveniencia or {})
    campos = ("id_entrega", "dominio", "origem_produtor", "categoria", "alvo")
    if fonte.get("entregue") is not True or any(
        not str(fonte.get(campo) or "").strip() for campo in campos
    ):
        return {}
    referencia = f"feedback:{str(fonte['id_entrega']).strip()}:{tipo}"
    # O contrato base limita referências: uma ocorrência não pode ser truncada
    # e colidir com outra entrega.
    if len(referencia) > 240:
        return {}
    try:
        entrega_ts = float(fonte.get("entrega_ts") or 0.0)
        observado_ts = float(fonte.get("observado_ts") or 0.0)
    except (TypeError, ValueError, OverflowError):
        return {}
    if (
        not all(math.isfinite(valor) for valor in (entrega_ts, observado_ts))
        or entrega_ts <= 0.0 or observado_ts < entrega_ts
    ):
        return {}
    evento = criar_evento_emocional_causal(
        origem="feedback_comunicativo",
        causa=f"feedback_{tipo}_da_emissao_entregue",
        evidencia_ref=referencia,
        natureza_evidencia="inferencia" if tipo == "silencio" else "leitura_social",
        confianca=1.0, intensidade=0, alvo=str(fonte["alvo"]),
        permite_expressao=False, emocao="calma", nivel=1, ts=observado_ts,
        motivo_expressao="feedback_observado_sem_emocao_inferida",
    )
    evento["tipo_feedback"] = tipo
    evento["proveniencia"] = {campo: fonte.get(campo) for campo in (
        *campos, "entrega_ts", "observado_ts", "entregue",
    )}
    return evento


def criar_evento_direcao_social_observada(
    evento: Mapping[str, Any],
    direcao: Mapping[str, Any],
    *,
    turno_id: str,
    ancora_factual: str,
    agora: float | None = None,
) -> dict[str, Any]:
    """Transporta uma decisão social já tomada, sem selecionar outra emoção."""
    observado, social = dict(evento), dict(direcao)
    referencia = str(observado.get("trace_id") or "").strip()
    identidade_turno = str(turno_id or "").strip()
    if not (
        observado.get("natureza") == "evento"
        and observado.get("autoridade_usuario") is False
        and observado.get("permissao_execucao") is False
        and not bool(observado.get("autoriza_execucao"))
        and all(social.get(campo) is False for campo in (
            "autoridade_usuario", "permissao_execucao", "autoriza_execucao"))
        and referencia and identidade_turno and str(ancora_factual or "").strip()
        and str(observado.get("origem") or "").strip()
        and str(social.get("motivo") or "").strip()
    ):
        return {}
    try:
        instante = float(time.time() if agora is None else agora)
        inicio = float(observado.get("timestamp", observado.get("ts", instante)))
        duracao = min(120.0, max(0.0, float(observado.get("validade_s", 120.0))))
        confianca_observada = float(observado.get("confianca") or 0.0)
        confianca_social = float(social.get("confianca") or 0.0)
        nivel = int(social.get("nivel") or 1)
    except (TypeError, ValueError, OverflowError):
        return {}
    if not all(math.isfinite(valor) for valor in (
        instante, inicio, duracao, confianca_observada, confianca_social)):
        return {}
    if not 1 <= nivel <= 3:
        return {}
    if social.get("emocao") not in {
        "calma", "debochada", "envergonhada", "irritada", "brava", "alegre",
        "triste", "surpresa", "acalmando-se",
    }:
        return {}
    confianca = min(_proporcao(confianca_observada), _proporcao(confianca_social))
    permite = bool(confianca >= 0.90 and inicio <= instante < inicio + duracao)
    identidade = hashlib.sha256(f"{referencia}\0{identidade_turno}".encode("utf-8")).hexdigest()[:24]
    causal = criar_evento_emocional_causal(
        origem="direcao_social_evento_observado",
        causa=str(social["motivo"]), evidencia_ref=f"evento_social:{identidade}",
        natureza_evidencia="leitura_social", responsabilidade="ambigua",
        confianca=confianca, relevancia=confianca, novidade=0.0,
        intensidade=nivel if permite else 0,
        sensibilidade="vulneravel" if social.get("objetivo") == "acompanhar_sem_deboche" else "normal",
        alvo=str(social.get("alvo") or ""), validade_s=duracao, ts=inicio,
        permite_expressao=permite, emocao=str(social.get("emocao") or "calma"),
        nivel=nivel, motivo_expressao="direcao_social_com_evidencia" if permite else "evidencia_social_insuficiente",
        arco=str(social.get("objetivo") or "reacao_evento"),
    )
    causal.update(evento_ref=referencia, turno_id=identidade_turno, direcao_social=social)
    return causal


def evento_corresponde_direcao_social_observada(
    causal: Mapping[str, Any] | None,
    observado: Mapping[str, Any],
    direcao: Mapping[str, Any],
    *,
    turno_id: str,
    agora: float | None = None,
) -> bool:
    """Revalida a ocorrência selecionada; um rótulo livre não é causa."""
    if not isinstance(causal, Mapping):
        return False
    try:
        confiancas = [float(fonte.get("confianca") or 0.0) for fonte in (causal, observado, direcao)]
    except (TypeError, ValueError, OverflowError):
        return False
    if not all(math.isfinite(valor) and _proporcao(valor) >= 0.90 for valor in confiancas):
        return False
    referencia = str(observado.get("trace_id") or "").strip()
    identidade_turno = str(turno_id or "").strip()
    identidade = hashlib.sha256(f"{referencia}\0{identidade_turno}".encode("utf-8")).hexdigest()[:24]
    return bool(
        referencia and identidade_turno
        and causal.get("origem") == "direcao_social_evento_observado"
        and causal.get("evento_ref") == referencia
        and causal.get("turno_id") == identidade_turno
        and causal.get("evidencia_ref") == f"evento_social:{identidade}"
        and causal.get("direcao_social") == dict(direcao)
        and causal.get("emocao") == direcao.get("emocao")
        and causal.get("nivel") == direcao.get("nivel")
        and causal.get("persistencia_pessoal") is False
        and observado.get("natureza") == "evento"
        and observado.get("autoridade_usuario") is False
        and observado.get("permissao_execucao") is False
        and not bool(observado.get("autoriza_execucao"))
        and all(direcao.get(campo) is False for campo in (
            "autoridade_usuario", "permissao_execucao", "autoriza_execucao"))
        and evento_pode_alterar_estado(causal, agora=agora)
    )


def criar_evento_reconhecimento_social_usuario(
    *, turno_id: str | int, confianca: float, tipo: str,
) -> dict[str, Any]:
    """Materializa avaliação social já decidida, sem transformar gratidão em causa."""
    referencia = str(turno_id or "").strip()
    avaliacoes = {
        "elogio_pessoal": ("envergonhada", 2, "elogio pessoal explícito dirigido à Laylay"),
        "critica_pessoal": ("triste", 1, "avaliação pessoal negativa dirigida à Laylay"),
        "rejeicao_pessoal": ("triste", 2, "distanciamento explicitamente dirigido à Laylay"),
    }
    tipo_limpo = str(tipo or "").strip().casefold()
    if tipo_limpo not in avaliacoes or not referencia:
        return {}
    confianca_limpa = _proporcao(confianca)
    if confianca_limpa < 0.90:
        return {}
    emocao, nivel, causa = avaliacoes[tipo_limpo]
    return criar_evento_emocional_causal(
        origem="reconhecimento_social_usuario",
        causa=causa,
        evidencia_ref=f"turno:{referencia}:texto_usuario",
        natureza_evidencia="leitura_social",
        responsabilidade="usuario",
        confianca=confianca_limpa,
        relevancia=0.65,
        novidade=0.65,
        intensidade=nivel,
        sensibilidade="normal",
        alvo="laylay",
        validade_s=60.0,
        permite_expressao=True,
        emocao=emocao,
        nivel=nivel,
        motivo_expressao=f"{tipo_limpo}_direto",
        arco="reconhecimento_social",
    )


def criar_evento_leitura_emocional_usuario(
    leitura: Mapping[str, Any] | None,
    *,
    turno_id: str | int,
) -> dict[str, Any]:
    dados = dict(leitura or {})
    emocao_usuario = str(dados.get("emocao") or "").strip()
    if not emocao_usuario:
        return {}
    inferida = dados.get("natureza_evidencia") == "inferencia"
    trecho = str(dados.get("trecho_evidencia") or "").strip()
    causa = str(dados.get("causa") or "").strip()
    if inferida and (not trecho or not causa or trecho.casefold() not in str(dados.get("texto") or "").casefold()):
        return {}
    assinatura = hashlib.sha256(trecho.casefold().encode("utf-8", errors="replace")).hexdigest()[:16] if inferida else ""
    sensiveis = {
        "tristeza", "ansiedade", "medo", "culpa", "esgotamento",
    }
    return criar_evento_emocional_causal(
        origem="inferencia_contextual_usuario" if inferida else "contingencia_lexical_usuario",
        causa=causa if inferida else (
            "sinal emocional reconhecido pela contingência lexical "
            "no turno atual"
        ),
        evidencia_ref=(
            f"turno:{turno_id}:inferencia:{assinatura}"
            if inferida else f"turno:{turno_id}:texto_usuario"
        ),
        natureza_evidencia="inferencia" if inferida else "leitura_social",
        responsabilidade="usuario",
        confianca=float(dados.get("confianca") or 0.0) if inferida else 0.96,
        relevancia=0.95,
        novidade=0.8,
        intensidade=int(dados.get("intensidade") or 1),
        sensibilidade=(
            "vulneravel"
            if emocao_usuario.casefold() in sensiveis
            else "sensivel"
        ),
        alvo=str(dados.get("alvo") or "estado_emocional_usuario"),
        validade_s=120.0,
        permite_expressao=False,
        emocao="calma",
        nivel=1,
        motivo_expressao="leitura_do_usuario_nao_altera_emocao_da_laylay",
        arco="acolhimento",
        ts=float(dados.get("ts") or time.time()),
    )


def criar_evento_leitura_semantica_usuario(
    leitura_semantica: Mapping[str, Any] | None,
    *,
    turno_id: str | int,
) -> dict[str, Any]:
    """Converte somente leitura semântica validada em evento causal."""
    semantica = dict(leitura_semantica or {})
    if semantica.get("origem") == "resposta_reparada":
        return {}
    leitura = (
        dict(semantica.get("leitura_emocional") or {})
        if isinstance(semantica.get("leitura_emocional"), Mapping)
        else {}
    )
    if leitura.get("valida") is not True:
        return {}
    evidencia = str(leitura.get("trecho_evidencia") or "").strip()
    causa = str(leitura.get("causa_expressa") or "").strip()
    estado_usuario = str(leitura.get("estado_usuario") or "").strip().casefold()
    if not evidencia or not causa or not estado_usuario:
        return {}
    assinatura = hashlib.sha256(
        evidencia.casefold().encode("utf-8", errors="replace")
    ).hexdigest()[:16]
    sensiveis = {
        "ansiedade", "culpa", "esgotamento", "medo", "tristeza",
    }
    return criar_evento_emocional_causal(
        origem="leitura_semantica_principal",
        causa=causa,
        evidencia_ref=f"turno:{turno_id}:semantica:{assinatura}",
        natureza_evidencia=str(
            leitura.get("natureza_evidencia") or "inferencia"
        ),
        responsabilidade="usuario",
        confianca=float(leitura.get("confianca") or 0.0),
        relevancia=max(0.8, float(leitura.get("confianca") or 0.0)),
        novidade=0.8,
        intensidade=int(leitura.get("intensidade") or 1),
        sensibilidade=(
            "vulneravel" if estado_usuario in sensiveis else "sensivel"
        ),
        alvo=str(leitura.get("alvo") or "estado_geral"),
        validade_s=120.0,
        permite_expressao=False,
        emocao="calma",
        nivel=1,
        motivo_expressao="leitura_do_usuario_nao_altera_emocao_da_laylay",
        arco="acolhimento",
    )
