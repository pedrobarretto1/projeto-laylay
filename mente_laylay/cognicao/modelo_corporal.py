"""Corpo no plano da mente: retrato factual, proposta finita e resultado correlacionado.

A emissão principal sugere uma intenção; a concessão permanece no owner USB.
Nenhum texto do modelo concede PWM, sessão, permissão ou prova de deslocamento.
"""
from __future__ import annotations

import json
import math
import secrets
import time
from typing import Any, Mapping

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada

INTENCOES_CORPORAIS = frozenset({"atenta", "interagir", "expressar", "comemorar", "reagir_falha", "explorar", "descansar"})


def _validar_proposta(dados: dict[str, Any]) -> None:
    intencao = dados.get("intencao_corporal")
    if not isinstance(intencao, dict) or set(intencao) != {"nome"}:
        raise ValueError("intenção corporal exige somente nome")
    if not isinstance(intencao["nome"], str) or intencao["nome"] not in INTENCOES_CORPORAIS:
        raise ValueError("intenção corporal não registrada")


_CODEC = ContratoSaidaEstruturada(nome="intencao_corporal_principal", marcador="CORPO", esquema={"type": "object"}, validar=_validar_proposta)


def vincular_intencao_corporal(plano: Mapping[str, Any], proposta: Any, *, agora: float | None = None) -> dict[str, Any]:
    """Chamado dentro da transação canônica, após validar turno/plano/retrato."""
    retrato = plano.get("retrato_corporal") or {}
    if (not isinstance(proposta, ContratoPropostaPrincipal) or not proposta.proveniencia_conhecida
            or str(plano.get("id", "")) != proposta.turno_id
            or retrato.get("turno_id") != proposta.turno_id or not retrato.get("sessao")
            or not retrato.get("concessao_id") or plano.get("intencao_corporal")):
        return {}
    try:
        dados = json.loads(_CODEC.canonizar_json(proposta.resposta_bruta)[len("CORPO "):])
    except (ValueError, TypeError):
        return {}
    agora = time.monotonic() if agora is None else agora
    return {"id": secrets.token_hex(8), "turno_id": proposta.turno_id, "plano_id": str(plano["id"]),
        "nome": dados["intencao_corporal"]["nome"], "estado": "proposta", "origem": "llm_principal",
        "sessao": retrato["sessao"], "concessao_id": retrato["concessao_id"],
        "desde_monotonic": agora, "ate_monotonic": agora + 30, "autoriza_execucao": False}


def proposta_corporal_vigente(plano: Mapping[str, Any], concessao: Mapping[str, Any], *, agora: float) -> dict[str, Any]:
    p = plano.get("intencao_corporal") or {}
    try:
        desde, ate = float(p["desde_monotonic"]), float(p["ate_monotonic"])
        valida = (p.get("origem") == "llm_principal" and p.get("autoriza_execucao") is False
            and p.get("estado") in {"proposta", "executando"} and p.get("nome") in INTENCOES_CORPORAIS
            and p.get("id") and p.get("turno_id") == str(plano.get("id")) == p.get("plano_id")
            and p.get("sessao") == concessao.get("sessao") and p.get("concessao_id") == concessao.get("id")
            and math.isfinite(desde) and math.isfinite(ate) and desde <= agora <= ate and 0 < ate - desde <= 30)
    except (KeyError, TypeError, ValueError, OverflowError):
        valida = False
    return dict(p) if valida else {}


def resultado_operacional_do_plano(plano: Mapping[str, Any], *, sucesso: bool) -> bool:
    """Nunca empresta o sucesso de outro turno ou de um subconjunto do composto."""
    comandos = list(plano.get("comandos") or [])
    if sucesso:
        return bool(comandos and not plano.get("erros") and all(
            isinstance(c, Mapping) and c.get("origem") == "executor" and c.get("id_solicitacao")
            and c.get("executou") is True and c.get("confirmado") is True
            and c.get("evidencia_confirmacao") not in (None, "", "envio_comando", "indisponivel")
            for c in comandos))
    return bool(plano.get("fase") == "falha_execucao" and plano.get("erros") and any(
        isinstance(c, Mapping) and c.get("origem") == "executor" and c.get("id_solicitacao")
        and c.get("confirmado") is False for c in comandos))


def formatar_realidade_corporal(modelo: Mapping[str, Any] | None) -> str:
    """Fatos e limites para qualquer autoria, sem outra proposta ou permissão."""
    if not modelo or modelo.get("origem") != "owner_corpo_usb":
        return ""
    fatos = {k: modelo.get(k) for k in ("conectada", "companhia_ativa", "passeio_ativo", "perfil", "olhos", "emocao_causal", "motor_em_andamento", "atencao_pc", "ultima_experiencia")}
    return (
        "--- MEU CORPO AGORA (estado efêmero observado pelo host) ---\n"
        + json.dumps(fatos, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        + ("\nSou a Laylay do PC e deste corpo robótico conectado, com OLED e motores. " if modelo.get("conectada") is True
           else "\nO corpo robótico não está conectado neste retrato; não alegue acesso atual aos motores ou à tela. ")
        + "Sensações emocionais podem expressar meu estado funcional quando há emoção causal registrada; não precisam virar uma negação de sentimentos. "
        "Já sensações físicas exigem observação: não há sensores de toque, temperatura, esforço, posição, obstáculos ou bordas neste corpo. "
        "Não afirme dor, calor, contato, colisão ou percepção do ambiente como fatos medidos. Humor e metáfora podem ser reconhecíveis como expressão, sem virar evidência. "
        "ACK confirma PWM e parada elétrica, não distância, giro ou percepção sensorial. O resultado anterior conserva seu turno de origem. "
    )


def formatar_modelo_corporal(modelo: Mapping[str, Any] | None) -> str:
    realidade = formatar_realidade_corporal(modelo)
    if not realidade:
        return ""
    return (
        realidade
        + "\n"
        "FORMATO ESTRUTURAL OBRIGATÓRIO DO JSON. Retorne somente o JSON da resposta, sem texto externo. "
        "Preserve os campos do contrato principal; se companhia_ativa=true, posso acrescentar intencao_corporal={\"nome\":\"expressar\"} no objeto externo, fora de fala. "
        "Os nomes das chaves são literais, sem traduzir nem acrescentar acentos. Exemplo de estrutura, preenchendo valores coerentes com o turno: "
        '{"fala":"resposta natural ao usuário","emocao":"calma","nivel_emocao":1,"comandos":[],"intencao_corporal":{"nome":"expressar"}}. '
        "O campo fala contém somente o que digo ao usuário, sem narrar nomes de intenção ou decisões técnicas. "
        "Escolha um nome: atenta (foco), interagir (acompanhar fala), expressar (emoção atual), comemorar (somente após sucesso confirmado do pedido), "
        "reagir_falha (somente após falha do pedido), explorar (somente passeio já ativo), descansar (sossego). "
        "Use uma intenção coerente com a conversa e minha emoção; posso descansar quando convém. "
        "Não escreva parâmetros de motor, permissões ou comandos técnicos nesse campo. A intenção é uma proposta; o executor valida a sessão e o momento. "
        "Não anuncie movimento como feito antes do retorno. Se desconectada, explique a indisponibilidade sem prometer gesto."
    )
