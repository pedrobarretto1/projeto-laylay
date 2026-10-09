"""Fato emocional local de uma violação original demonstrada pelo dono do turno.

O produtor não interpreta linguagem, reclassifica a decisão nem confirma efeito.
A revalidação da restrição vigente pertence à ponte que publica o evento.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from mente_laylay.cognicao.contratos_turno import (
    ContratoPropostaPrincipal,
    ViolacaoPropostaPrincipal,
)
from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal


def criar_evento_erro_proposta(
    prova: ViolacaoPropostaPrincipal,
    principal: ContratoPropostaPrincipal,
    *,
    agora: float,
) -> dict[str, Any]:
    """Projeta a prova tipada, sem expor emissão, parâmetros ou alvo externo."""
    if (
        type(prova) is not ViolacaoPropostaPrincipal
        or type(principal) is not ContratoPropostaPrincipal
        or principal.proveniencia_conhecida is not True
        or principal.sucesso_modelo is not True
        or principal.estado != "recebida"
        or principal.origem != "llm_principal"
        or prova.origem != "contrato_proposta_principal"
        or prova.owner != "validador_comandos_turno"
        or prova.autoriza_execucao is not False
        or prova.comprova_efeito_externo is not False
        or principal.autoriza_execucao is not False
        or prova.turno_id != principal.turno_id
        or isinstance(agora, bool)
        or not isinstance(agora, (int, float))
    ):
        return {}
    try:
        instante = float(agora)
    except (ValueError, OverflowError):
        return {}
    if not math.isfinite(instante) or instante <= 0.0:
        return {}
    identidade = json.dumps([
        principal.turno_id, principal.texto_usuario, principal.resposta_bruta,
        prova.indice_comando, prova.intent, prova.motivo,
        prova.proprietario, prova.operacao_explicita,
    ], ensure_ascii=True, separators=(",", ":"))
    referencia = hashlib.sha256(identidade.encode("utf-8")).hexdigest()
    return criar_evento_emocional_causal(
        origem="contrato_proposta_principal",
        causa="a proposta original da Laylay violou o contrato do turno",
        evidencia_ref=f"proposta_original:{referencia}",
        natureza_evidencia="fato_observado",
        responsabilidade="laylay",
        confianca=1.0,
        relevancia=0.8,
        novidade=0.6,
        intensidade=1,
        sensibilidade="normal",
        alvo="proposta_principal",
        validade_s=45.0,
        permite_expressao=True,
        emocao="envergonhada",
        nivel=1,
        motivo_expressao="violacao_proposta_original_comprovada",
        arco="autorreparo",
        ts=instante,
    )


def evento_corresponde_erro_proposta(
    evento: Mapping[str, Any] | None,
    prova: ViolacaoPropostaPrincipal,
    principal: ContratoPropostaPrincipal,
) -> bool:
    """Exige a projeção inteira da mesma prova, inclusive tipos e instante."""
    if not isinstance(evento, Mapping):
        return False
    esperado = criar_evento_erro_proposta(prova, principal, agora=evento.get("ts"))
    if not esperado:
        return False
    try:
        # Igualdade de dict permitiria True == 1. A representação JSON mantém
        # essa distinção e recusa tipos não transportáveis, ciclos e NaN/Inf.
        recebido = json.dumps(dict(evento), sort_keys=True, allow_nan=False)
        canonico = json.dumps(esperado, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return False
    return recebido == canonico
