"""Fonte imutável capturada pelo decisor antes do efeito, sem novo registro."""
from dataclasses import dataclass, field
import math

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA


@dataclass(frozen=True, slots=True)
class DecisaoObservada:
    """Relata a regra e evidências usadas pelo owner; não lê a mente da LLM.

    O owner cria esta fonte antes de chamar o executor e a ocorrência existente
    conserva sua projeção. Resultado, receipt e autoridade têm donos distintos.
    IDs de proposta e decisão podem diferir. Ausência de fonte nunca autoriza
    reconstruí-la a partir da intenção corrente ou do resultado posterior.
    """

    id: str
    owner: str
    nome: str
    motivo: str
    turno_id: str
    sessao: str
    intencao_id: str
    objetivo_id: str
    registrada_em: float
    evidencias: SnapshotComandoIA
    criterios: tuple[tuple[str, int], ...] = ()
    autoriza_execucao: bool = field(default=False, init=False)
    confirma_efeito: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        essenciais = (self.id, self.owner, self.nome, self.motivo)
        identidades = (self.turno_id, self.sessao, self.intencao_id, self.objetivo_id)
        if (any(not isinstance(v, str) or not v or v != v.strip() for v in essenciais)
                or any(not isinstance(v, str) or v != v.strip() for v in identidades)
                or type(self.evidencias) is not SnapshotComandoIA
                or type(self.registrada_em) not in (int, float)
                or not math.isfinite(self.registrada_em) or self.registrada_em < 0):
            raise ValueError("Decisão exige owner, identidade, motivo e evidências congeladas.")
        if (type(self.criterios) is not tuple
                or any(type(c) is not tuple or len(c) != 2 or not isinstance(c[0], str)
                       or not c[0] or type(c[1]) is not int for c in self.criterios)
                or len({c[0] for c in self.criterios}) != len(self.criterios)):
            raise ValueError("Critérios exigem nomes únicos e pontuações inteiras observadas.")

    def como_dict(self) -> dict:
        return {"id": self.id, "owner": self.owner, "nome": self.nome, "motivo": self.motivo,
                "turno_id": self.turno_id, "sessao": self.sessao, "intencao_id": self.intencao_id,
                "objetivo_id": self.objetivo_id, "registrada_em": self.registrada_em,
                "evidencias": self.evidencias.como_dict(), "criterios": dict(self.criterios),
                "autoriza_execucao": False, "confirma_efeito": False}


@dataclass(frozen=True, slots=True)
class EpisodioExplicavel:
    """O owner entrega uma observação histórica; projeção JSON não reentra.

    Motivo, tentativa e escopo de confirmação são dimensões independentes.
    Uma proposta pode ter identidade conhecida sem justificativa registrada.
    """

    id: str
    owner: str
    nome: str
    turno_origem: str
    sessao: str
    iniciada_em: float
    encerrada_em: float
    intencao_id: str
    decisao: DecisaoObservada | None
    justificativa_registrada: bool
    confirmado: bool | None
    escopo_confirmacao: str
    limite_observacao: str

    def __post_init__(self) -> None:
        if (any(not isinstance(v, str) or not v or v != v.strip() for v in
                (self.id, self.owner, self.nome, self.escopo_confirmacao, self.limite_observacao))
                or any(not isinstance(v, str) for v in (self.turno_origem, self.sessao, self.intencao_id))
                or any(type(t) not in (int, float) or not math.isfinite(t) or t < 0
                       for t in (self.iniciada_em, self.encerrada_em))
                or self.encerrada_em < self.iniciada_em
                or type(self.justificativa_registrada) is not bool
                or (self.confirmado is not None and type(self.confirmado) is not bool)):
            raise ValueError("Episódio exige observação identificada e confirmação independente.")
        if self.decisao is not None:
            d = self.decisao
            if (type(d) is not DecisaoObservada or d.registrada_em > self.iniciada_em
                    or (d.turno_id, d.sessao, d.intencao_id) !=
                       (self.turno_origem, self.sessao, self.intencao_id)):
                raise ValueError("Decisão não pertence ao episódio observado.")
        elif self.justificativa_registrada:
            raise ValueError("Justificativa exige fonte anterior do decisor.")


@dataclass(frozen=True, slots=True)
class ExplicacaoOcorrencia:
    """Seleção feita pelo host para esta consulta, nunca pela prosa da LLM."""

    turno_consulta: str
    texto_consulta: str
    episodios: tuple[EpisodioExplicavel, ...]
    referencia: str
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (not isinstance(self.turno_consulta, str) or not self.turno_consulta
                or not isinstance(self.texto_consulta, str) or not self.texto_consulta.strip()
                or type(self.episodios) is not tuple or len(self.episodios) > 12
                or any(type(e) is not EpisodioExplicavel for e in self.episodios)
                or len({e.id for e in self.episodios}) != len(self.episodios)
                or self.referencia not in {"unica", "ambigua", "ausente"}
                or (self.referencia == "unica" and len(self.episodios) != 1)
                or (self.referencia == "ambigua" and len(self.episodios) < 2)
                or (self.referencia == "ausente" and self.episodios)):
            raise ValueError("Explicação exige consulta e seleção explícita de ocorrências.")
