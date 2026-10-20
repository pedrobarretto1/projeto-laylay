"""Identidade de relato observado; não concede execução nem confirma entrega.

O produtor conserva prova e vigência. Identidade distingue acontecimentos com
o mesmo assunto em qualquer domínio; o Diretor exige o owner vivo antes de
aplicar um orçamento de reação em vez do orçamento de rotina.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

INTERVALO_REACAO_CORPORAL_S = 60.0


@dataclass(frozen=True)
class AdmissaoReacaoObservada:
    """Receipt interno do Diretor; nunca permissão para agir ou prova de áudio."""
    trace_id: str
    validar_vigencia: Callable[[], bool]

    def vigente(self) -> bool:
        try:
            return bool(self.trace_id and self.validar_vigencia() is True)
        except Exception:
            return False


def avaliar_relevancia_observada(
    dados: Mapping[str, Any], historico: Sequence[Mapping[str, Any]], *,
    agora: float, perfil: str, pontuacao_feedback: int,
) -> dict[str, Any]:
    """Novidade e saturação contínuas, sem limiar universal de segundos.

    Tempos fazem a saturação decair; não enfileiram relatos para outro minuto.
    Tentativa, inclusive uma que falhou no TTS, tem custo de atenção. Identidade
    nova sozinha não torna novo o assunto. A fonte já foi validada pelo owner.
    """
    fonte = dados.get("observacao_corporal") or {}
    marco = str((dados.get("ocorrencia_observada") or {}).get("marco") or "")
    recuperacao = marco == "recuperacao"
    estado = str(fonte.get("risco_medido") or fonte.get("fase_manuseio") or dados.get("assunto") or "observacao")
    assunto = f"{dados.get('dominio')}:{estado}:{'recuperacao' if recuperacao else 'alerta'}"
    relevancia = 68 if recuperacao else {
        "BORDA":93, "BORDA_SEM_RETORNO":93, "DESORIENTADA":90,
        "SUSTO":84, "RESMUNGO":84,
    }.get(estado, 76)
    identidade = identidade_ocorrencia(dados)
    recentes = [h for h in historico if type(h.get("ts")) in (int,float)
        and 0 <= agora-h["ts"] < 600][-32:]
    repetida = any(h.get("identidade") == identidade for h in recentes)
    pressao = sum(32 * math.exp(-(agora-h["ts"])/20) for h in recentes)
    equivalentes = [h for h in recentes if h.get("assunto") == assunto]
    habituacao = sum(24 * math.exp(-(agora-h["ts"])/120) for h in equivalentes)
    limiar = 55 + (10 if perfil == "silencioso" else 0) + min(20, max(0,-pontuacao_feedback)*5)
    pontos = relevancia-pressao-habituacao
    return {"permitida":not repetida and pontos >= limiar, "identidade":identidade,
        "assunto":assunto, "relevancia":relevancia, "pressao_recente":round(pressao,2),
        "habituacao":round(habituacao,2), "pontuacao":round(pontos,2), "limiar":limiar,
        "motivo":"ocorrencia_ja_considerada" if repetida else "mudanca_relevante" if pontos >= limiar
            else "reacao_sem_novidade_suficiente"}


def identidade_ocorrencia(dados: Mapping[str, Any]) -> str:
    fonte = dados.get("ocorrencia_observada")
    if (not isinstance(fonte, Mapping) or dados.get("executavel") is not False
            or dados.get("autoriza_execucao") is not False):
        return ""
    episodio, marco = fonte.get("episodio_id"), fonte.get("marco")
    if (not isinstance(episodio, str) or not episodio.strip() or len(episodio) > 192
            or not isinstance(marco, str) or not marco.strip() or len(marco) > 96):
        return ""
    return hashlib.sha256(json.dumps([episodio, marco], ensure_ascii=False).encode()).hexdigest()
