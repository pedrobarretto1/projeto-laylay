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
VALIDADE_OBJETIVO_CORPORAL_S = 120
MAX_TURNOS_OBJETIVO_CORPORAL = 8


def continuacao_objetivo_valida(retrato: Mapping[str, Any], objetivo_id: str, *, agora: float) -> bool:
    """Referência semântica da autoria atual a um objetivo observado pelo owner."""
    i = retrato.get("objetivo_para_continuar") or retrato.get("intencao_em_curso") or {}
    if not isinstance(i, Mapping) or type(agora) not in (int, float) or not math.isfinite(agora):
        return False
    try:
        return bool(retrato.get("origem") == "owner_corpo_usb"
            and retrato.get("companhia_ativa") is True
            and i.get("origem") == "owner_companhia_corporal"
            and i.get("sessao_vigente") is True and i.get("continuidade_disponivel") is True
            and i.get("objetivo_id") == objetivo_id and i.get("objetivo_turno_origem")
            and math.isfinite(float(i["objetivo_ate_monotonic"]))
            and agora <= float(i["objetivo_ate_monotonic"])
            and type(i.get("turnos_objetivo")) is int
            and 1 <= i["turnos_objetivo"] < MAX_TURNOS_OBJETIVO_CORPORAL)
    except (TypeError, ValueError, KeyError, OverflowError):
        return False


def _validar_proposta(dados: dict[str, Any]) -> None:
    intencao = dados.get("intencao_corporal")
    if not isinstance(intencao, dict) or "nome" not in intencao or set(intencao) - {"nome", "objetivo_id"}:
        raise ValueError("intenção corporal exige nome e referência opcional ao objetivo")
    if not isinstance(intencao["nome"], str) or intencao["nome"] not in INTENCOES_CORPORAIS:
        raise ValueError("intenção corporal não registrada")
    if "objetivo_id" in intencao:
        ref = intencao["objetivo_id"]
        if not isinstance(ref, str) or len(ref) != 12 or any(c not in "0123456789abcdef" for c in ref):
            raise ValueError("referência de objetivo inválida")


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
    referencia = dados["intencao_corporal"].get("objetivo_id")
    if referencia and not continuacao_objetivo_valida(retrato, referencia, agora=agora):
        return {}
    fonte_objetivo = retrato.get("objetivo_para_continuar") or retrato.get("intencao_em_curso") or {}
    continuidade = ({"objetivo_id": referencia,
                     "objetivo_ate_monotonic": fonte_objetivo["objetivo_ate_monotonic"]}
                    if referencia else {})
    return {"id": secrets.token_hex(8), "turno_id": proposta.turno_id, "plano_id": str(plano["id"]),
        "nome": dados["intencao_corporal"]["nome"], "estado": "proposta", "origem": "llm_principal",
        "sessao": retrato["sessao"], "concessao_id": retrato["concessao_id"],
        "desde_monotonic": agora, "ate_monotonic": agora + 30, "autoriza_execucao": False, **continuidade}


def proposta_corporal_vigente(plano: Mapping[str, Any], concessao: Mapping[str, Any], *, agora: float) -> dict[str, Any]:
    p = plano.get("intencao_corporal") or {}
    try:
        desde, ate = float(p["desde_monotonic"]), float(p["ate_monotonic"])
        valida = (p.get("origem") == "llm_principal" and p.get("autoriza_execucao") is False
            and p.get("estado") in {"proposta", "executando"} and p.get("nome") in INTENCOES_CORPORAIS
            and p.get("id") and p.get("turno_id") == str(plano.get("id")) == p.get("plano_id")
            and p.get("sessao") == concessao.get("sessao") and p.get("concessao_id") == concessao.get("id")
            and math.isfinite(desde) and math.isfinite(ate) and desde <= agora <= ate and 0 < ate - desde <= 30)
        if p.get("objetivo_id"):
            valida = valida and continuacao_objetivo_valida(plano.get("retrato_corporal") or {}, p["objetivo_id"], agora=agora)
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


def formatar_realidade_corporal(modelo: Mapping[str, Any] | None, *, limite_historico: int = 3) -> str:
    """Fatos e limites para qualquer autoria, sem outra proposta ou permissão."""
    if not modelo or modelo.get("origem") != "owner_corpo_usb":
        return ""
    fatos = {k: modelo.get(k) for k in ("turno_id", "conectada", "companhia_ativa", "passeio_ativo", "perfil", "olhos", "emocao_causal", "motor_em_andamento", "atencao_pc", "condicao", "percepcao_fisica", "intencao_em_curso", "objetivo_para_continuar", "experiencia", "ultima_experiencia") if modelo.get(k) is not None}
    # A mente recebe o fato necessário; metadados elétricos completos ficam no
    # owner e no DEV. Projeção não altera o retrato canônico nem concede controle.
    percepcao = fatos.get("percepcao_fisica") or {}
    sensores = percepcao.get("distancias") or {}
    if sensores:
        p = sensores.get("protecao") or {}
        fatos["percepcao_fisica"] = {"deslocamento": "nao_medido", "contato": "nao_medido",
            "sensores_disponiveis": sensores.get("suportado") is True,
            "recente": sensores.get("recente") is True,
            "leituras": {n: {k:s.get(k) for k in ("estado", "mm", "idade_ms")}
                         for n,s in (sensores.get("leituras") or {}).items()},
            "cobertura": "frente_e_borda_dianteira"}
    else:
        fatos["percepcao_fisica"] = {"deslocamento":"nao_medido", "contato":"nao_medido", "obstaculos":"nao_medido"}
    condicao = dict(fatos.get("condicao") or {})
    p = condicao.get("protecao") or {}
    if p:
        condicao["protecao"] = {k:p.get(k) for k in ("risco", "fase", "incidente_id", "recente", "tentativa_busca", "vigia_ativa") if k in p}
    else:
        condicao.pop("protecao",None)
        condicao.pop("reacao_expressiva",None)
    fatos["condicao"] = condicao
    # A mente recebe evidência necessária, sem duplicar a partitura técnica.
    ultima = fatos.get("ultima_experiencia")
    if isinstance(ultima, Mapping):
        campos = ("id", "objetivo_id", "nome", "turno_id", "resultado", "confirmado", "parada_confirmada", "prova_deslocamento", "pertence_ao_turno_atual")
        fatos["ultima_experiencia"] = {k: ultima[k] for k in campos if k in ultima}
    experiencia = fatos.get("experiencia")
    if isinstance(experiencia, Mapping):
        campos = ("id", "nome", "turno_id", "resultado", "confirmado", "prova_deslocamento", "recuperada_da_memoria")
        historico = list(experiencia.get("historico_recente", []))[-3:]
        incluidos = historico[-limite_historico:] if limite_historico else []
        fatos["experiencia"] = {"historico_recente": [
            {k: e[k] for k in campos if k in e} for e in incluidos],
            "historico_omitido": len(historico) - len(incluidos),
            "aprendizado_conectado": experiencia.get("aprendizado_conectado", False),
            "aprendizado": {k: v for k, v in (experiencia.get("aprendizado") or {}).items()
                            if k in {"origem", "estado_hipotese", "confianca"}},
            "feedback": {k: v for k, v in (experiencia.get("feedback") or {}).items()
                         if k in {"tipo", "aceito", "experiencia_id", "turno_id"}}}
    objetivo = fatos.get("objetivo_para_continuar")
    if isinstance(objetivo, Mapping):
        campos = ("objetivo_id", "nome", "motivo", "continuidade_disponivel", "objetivo_turno_origem", "turnos_objetivo", "objetivo_contexto")
        fatos["objetivo_para_continuar"] = {k: objetivo[k] for k in campos if k in objetivo}
    intencao = fatos.get("intencao_em_curso")
    if isinstance(intencao, Mapping):
        campos = ("id", "objetivo_id", "nome", "motivo", "pontuacoes", "estado", "fase", "turno_id", "resultado", "pertence_ao_turno_atual", "sessao_vigente")
        fatos["intencao_em_curso"] = {k: intencao[k] for k in campos if k in intencao}
    return (
        "--- MEU CORPO AGORA (estado efêmero observado pelo host) ---\n"
        + json.dumps(fatos, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        + ("\nSou a Laylay do PC e deste corpo robótico conectado, com OLED e motores. " if modelo.get("conectada") is True
           else "\nO corpo robótico não está conectado neste retrato; não alegue acesso atual aos motores ou à tela. ")
        + "Emoção é expressiva. Sem sensores de toque, temperatura, esforço ou posição, não invente essas sensações. "
        "Só descreva obstáculo/borda com leituras recentes: cobertura frontal e inferior dianteira, sem traseira/laterais. "
        "Inválida frontal significa desconhecido; medo é reação ao risco. Giro por tempo não mede ângulo. "
        "ACK prova PWM/parada elétrica; deslocamento=false significa NÃO MEDIDO, nunca que não andei. "
        "Resultado estrangeiro permanece no turno original; proposta/aguardando não significa ação executada. "
        "Histórico e aprendizado não restauram permissão. Condição indisponível impede prometer acesso. "
        "Novo turno exige proposta atual; não retoma coreografia interrompida nem herda receipt. "
    )


def formatar_modelo_corporal(modelo: Mapping[str, Any] | None) -> str:
    realidade = formatar_realidade_corporal(modelo)
    if not realidade:
        return ""
    if modelo.get("companhia_ativa") is False:
        # Estado observado permanece inteiro. Uma saída desabilitada não recebe
        # exemplos de proposta; isto não restringe comandos manuais autorizados.
        return realidade + (
            "\nFORMATO ESTRUTURAL OBRIGATÓRIO DO JSON. Retorne só JSON, "
            "preservando os campos do contrato principal. "
            "Não copie o retrato para a saída. Fale naturalmente em fala, sem nomes técnicos. "
            "Com companhia_ativa=false, omita intencao_corporal. "
            "Pedidos manuais continuam sob autorização e validação do executor; "
            "não anuncie movimento como feito antes do retorno."
        )
    referencia = modelo.get("objetivo_para_continuar") or {}
    ref = referencia.get("objetivo_id") if isinstance(referencia, Mapping) else None
    exemplo = {"fala": "resposta natural ao usuário", "emocao": "calma", "nivel_emocao": 1,
               "comandos": [], "intencao_corporal": {"nome": "interagir"}}
    if ref and continuacao_objetivo_valida(modelo, ref, agora=time.monotonic()):
        exemplo["intencao_corporal"]["objetivo_id"] = ref
    exemplo_novo = {"intencao_corporal": {"nome": "atenta"}}
    contrato = (
        "\n"
        "FORMATO ESTRUTURAL OBRIGATÓRIO DO JSON. Retorne só JSON, preservando os campos do contrato principal. "
        "Não copie o retrato para a saída. Fale naturalmente em fala, sem nomes técnicos. "
        "Se companhia_ativa=false, omita intencao_corporal. Caso ativo, inclua a proposta no objeto externo, fora de fala. "
        "Escolha nome: atenta (foco), interagir (conversa), expressar (emoção causal), comemorar (sucesso confirmado deste pedido), "
        "reagir_falha (falha deste pedido), explorar (passeio ativo), descansar (sossego). "
        "Compare o pedido atual ao objetivo_contexto observado; acompanhar uma conversa em geral não basta para herdar o assunto anterior. "
        "Se o turno aprofunda esse mesmo assunto e objetivo_para_continuar.continuidade_disponivel=true, "
        "inclua objetivo_id copiando objetivo_para_continuar.objetivo_id. Em mudança de assunto omita objetivo_id. "
        "Nunca invente identificadores ou repita automaticamente o gesto anterior. "
        "Estrutura para continuidade (use valores coerentes com o turno): "
        + json.dumps(exemplo, ensure_ascii=False, separators=(",", ":"))
        + ". Para assunto independente ou mudança de assunto explícita, a estrutura SEM objetivo_id é: "
        + json.dumps(exemplo_novo, ensure_ascii=False, separators=(",", ":"))
        + ". Sem PWM, permissões ou comandos técnicos na intenção. O executor revalida sessão/momento; não anuncie movimento como feito antes do retorno."
    )
    # Só o histórico opcional cede espaço. Estado corrente, referência, fonte e
    # regras de saída permanecem inteiros no limite do transporte local atual.
    for limite in (3, 2, 1, 0):
        texto = formatar_realidade_corporal(modelo, limite_historico=limite) + contrato
        if len(texto) <= 3800:
            return texto
    return texto
