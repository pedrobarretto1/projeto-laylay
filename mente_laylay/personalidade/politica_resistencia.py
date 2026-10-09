"""Decisão causal de resistência opcional; não executa nem cria pendências."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Collection, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.modalidade_turno import autoriza_execucao_efetiva
from mente_laylay.emocoes.contrato_causal import evento_pode_alterar_estado


@dataclass(frozen=True, slots=True)
class DecisaoResistencia:
    resistir: bool
    motivo: str
    evidencia_ref: str = ""
    dominio: str = ""
    acao: str = ""


# O avaliador é genérico; somente ações com semântica auditada entram neste
# catálogo. Alternar repetição é reversível pelo mesmo controle e não escreve
# dados nem desliga um dispositivo. A necessidade vem do pedido atual.
_ACOES_OPCIONAIS_REVERSIVEIS = {
    ("MEDIA_CONTROL", "repeat_toggle"): "musica",
}

_DESTINOS_RESISTENCIA = frozenset({"pc_a", "pc_b", "ambos"})
_PARAMS_RESISTENCIA = frozenset({"acao", "target", "platform", "site"})
_PLAYERS_RESISTENCIA = frozenset({"", "music", "musica", "música", "youtube", "youtube_music"})

_NECESSIDADE_PROTEGIDA = re.compile(
    r"\b(?:urgente|urgencia|emergencia|seguranca|acessibilidade|"
    r"saude|socorro|sos|preciso|necessario|necessaria|importante|agora)\b"
)


def validar_pedido_resistencia(pedido: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Valida a identidade operacional transportada, sem importar autoridade.

    O destino já pertence ao resolver canônico. Campos não auditados impedem
    a retomada, em vez de reduzir o pedido a uma ação sobre o alvo padrão.
    """
    if not isinstance(pedido, Mapping) or set(pedido) != {"intent", "params"}:
        return None
    if pedido.get("intent") != "MEDIA_CONTROL":
        return None
    params = pedido.get("params")
    if not isinstance(params, Mapping) or not set(params) <= _PARAMS_RESISTENCIA:
        return None
    if (
        params.get("acao") != "repeat_toggle"
        or not isinstance(params.get("target"), str)
        or params["target"] not in _DESTINOS_RESISTENCIA
    ):
        return None
    for campo in ("platform", "site"):
        if campo in params and (
            not isinstance(params[campo], str)
            or params[campo].strip().casefold() not in _PLAYERS_RESISTENCIA
        ):
            return None
    return {"intent": "MEDIA_CONTROL", "params": dict(params)}


def projetar_pedido_resistencia(
    *, intent: str, params: Mapping[str, Any], destino_resolvido: str,
) -> dict[str, Any] | None:
    """Preserva os parâmetros auditados e o alvo resolvido antes do adiamento."""
    return validar_pedido_resistencia({
        "intent": intent, "params": {**params, "target": destino_resolvido},
    })


def mesma_identidade_pedido_resistencia(
    primeiro: Mapping[str, Any] | None, segundo: Mapping[str, Any] | None,
) -> bool:
    """Distingue alvo/player sem reclassificar a autorização ou a linguagem.

    Os seletores auditados explícitos usam a mesma rota musical do executor.
    Sua ausência pode alcançar a mídia global e permanece uma identidade distinta.
    """
    pedidos = (validar_pedido_resistencia(primeiro), validar_pedido_resistencia(segundo))
    if any(pedido is None for pedido in pedidos):
        return False
    identidades = []
    for pedido in pedidos:
        params = pedido["params"]
        seletor = str(params.get("platform") or params.get("site") or "").strip().casefold()
        identidades.append((pedido["intent"], params["acao"], params["target"], bool(seletor)))
    return identidades[0] == identidades[1]


def avaliar_resistencia_contextual(
    *,
    intent: str,
    params: Mapping[str, Any] | None,
    texto_usuario: str,
    estado_emocional: Mapping[str, Any] | None,
    turno: Mapping[str, Any] | None,
    ultima_referencia_resistida: str = "",
    referencias_resistidas: Collection[str] = (),
) -> DecisaoResistencia:
    """Só adia uma ação classificada como opcional, segura e reversível.

    Ausência, contradição ou vencimento de evidência mantém o pedido no fluxo
    normal. Emoção não altera autorização nem confirma qualquer efeito.
    """
    chave = (str(intent or "").upper(), str((params or {}).get("acao") or "").casefold())
    dominio = _ACOES_OPCIONAIS_REVERSIVEIS.get(chave)
    if not dominio:
        return DecisaoResistencia(False, "acao_sem_classificacao_segura")
    if not autoriza_execucao_efetiva(dict(turno or {})):
        return DecisaoResistencia(False, "turno_sem_autorizacao")
    texto = normalizar_texto_basico(texto_usuario)
    if not re.search(r"\be opcional\b", texto) or re.search(
        r"\bnao\s+e\s+opcional\b", texto
    ):
        return DecisaoResistencia(False, "necessidade_nao_opcional")
    if _NECESSIDADE_PROTEGIDA.search(texto):
        return DecisaoResistencia(False, "necessidade_protegida")
    # O executor expõe um toggle, não um setter de estado. A resistência só
    # retoma pedidos cujo verbo já corresponde a alternar; "ativar" poderia
    # desligar uma repetição ativa após a confirmação.
    if chave[1] == "repeat_toggle" and not re.search(
        r"\balterna\s+(?:(?:a|o)\s+)?(?:repeticao|loop)\b", texto,
    ):
        return DecisaoResistencia(False, "verbo_incompativel_com_toggle")
    estado = dict(estado_emocional or {})
    evento_bruto = estado.get("episodio_emocional")
    if not isinstance(evento_bruto, Mapping):
        return DecisaoResistencia(False, "causa_invalida")
    evento = dict(evento_bruto)
    try:
        confianca = float(evento.get("confianca") or 0.0)
        nivel = int(estado.get("emotion_level") or 0)
    except (TypeError, ValueError, OverflowError):
        return DecisaoResistencia(False, "causa_invalida")
    referencia = str(evento.get("evidencia_ref") or "").strip()
    if not (
        evento_pode_alterar_estado(evento)
        and evento.get("origem") == "resultado_operacional"
        and evento.get("responsabilidade") == "usuario"
        and evento.get("arco") == "bronca_brincalhona"
        and evento.get("emocao") == estado.get("current_emotion") == "brava"
        and nivel == 3
        and math.isfinite(confianca)
        and confianca >= 0.90
        and referencia
    ):
        return DecisaoResistencia(False, "causa_invalida")
    if referencia == str(ultima_referencia_resistida or "") or referencia in referencias_resistidas:
        return DecisaoResistencia(False, "resistencia_ja_usada")
    return DecisaoResistencia(
        True, "pedido_opcional_apos_bronca_causal", referencia, dominio, chave[1],
    )
