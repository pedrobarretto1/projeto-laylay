"""Fonte imutável capturada pelo decisor antes do efeito, sem novo registro."""
from dataclasses import dataclass, field
import math

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA, ContratoExplicativoAto


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
class MedicaoObservada:
    """Registro numérico do owner, sem interpretar prosa ou conceder efeito.

    Tipagem preserva valor, unidade, método e ressalva; não certifica aferição.
    A origem factual deve ser conferida pelo owner que lê seu próprio histórico.
    """

    ocorrencia_id: str
    owner: str
    grandeza: str
    valor: int | float
    unidade: str
    metodo: str
    limite_observacao: str
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        textos = (self.ocorrencia_id, self.owner, self.grandeza, self.unidade,
                  self.metodo, self.limite_observacao)
        if (any(type(v) is not str or not v or v != v.strip() or len(v) > 240 for v in textos)
                or type(self.valor) not in (int, float) or not math.isfinite(self.valor)):
            raise ValueError("Medição exige origem, valor finito, unidade, método e limite explícitos.")


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
    medicoes: tuple[MedicaoObservada, ...] = ()

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
        if (type(self.medicoes) is not tuple or len(self.medicoes) > 8
                or any(type(m) is not MedicaoObservada or m.ocorrencia_id != self.id
                       or m.owner != self.owner for m in self.medicoes)
                or len({(m.grandeza, m.unidade, m.metodo) for m in self.medicoes}) != len(self.medicoes)):
            raise ValueError("Medições exigem vínculo ao mesmo episódio e owner, sem duplicação.")
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


@dataclass(frozen=True, slots=True)
class ExplicacaoHistoricaAto:
    """Fonte de uma parte já delimitada pelo interpretador, sem herança entre atos."""

    ato: ContratoExplicativoAto
    fonte_textual: SnapshotComandoIA
    ocorrencia: ExplicacaoOcorrencia | None = None
    fala: SnapshotComandoIA | None = None
    falha_fonte: bool = False

    def __post_init__(self) -> None:
        if (type(self.ato) is not ContratoExplicativoAto
                or self.ato.modalidade not in {"pergunta", "deliberacao"}
                or type(self.fonte_textual) is not SnapshotComandoIA
                or (self.ocorrencia is not None and type(self.ocorrencia) is not ExplicacaoOcorrencia)
                or (self.fala is not None and type(self.fala) is not SnapshotComandoIA)
                or type(self.falha_fonte) is not bool
                or (self.ocorrencia is not None and self.fala is not None)
                or (self.falha_fonte and (self.ocorrencia is not None or self.fala is not None))):
            raise ValueError("Ato explicativo exige fonte exclusiva e leitura não operacional.")


@dataclass(frozen=True, slots=True)
class ExplicacoesHistoricasPorAto:
    """Cobertura por ato; conter uma fonte não comprova os outros referentes.

    O host cria este vínculo a partir da segmentação instalada. Tipagem e
    coordenadas não certificam interpretação semântica ou autoria da LLM.
    """

    turno_consulta: str
    texto_consulta: str
    partes: tuple[ExplicacaoHistoricaAto, ...]
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (not isinstance(self.turno_consulta, str) or not self.turno_consulta
                or not isinstance(self.texto_consulta, str) or not self.texto_consulta.strip()
                or type(self.partes) is not tuple or not 2 <= len(self.partes) <= 8
                or any(type(p) is not ExplicacaoHistoricaAto for p in self.partes)):
            raise ValueError("Consulta composta exige identidade e todos os atos ordenados.")
        cursor = 0
        for indice, parte in enumerate(self.partes):
            f = parte.fonte_textual.como_dict()
            intervalo = f.get("intervalo")
            if (parte.ato.indice != indice or f.get("indice_segmento") != indice
                    or f.get("origem") != "segmentacao_canonica"
                    or f.get("autoriza_execucao") is not False or f.get("comprova_efeito") is not False
                    or not isinstance(intervalo, list) or len(intervalo) != 2
                    or any(type(i) is not int for i in intervalo)):
                raise ValueError("Fonte textual não pertence à posição do ato.")
            inicio, fim = intervalo
            if (not cursor <= inicio < fim <= len(self.texto_consulta)
                    or self.texto_consulta[inicio:fim] != f.get("texto_original")
                    or " ".join(f["texto_original"].casefold().split()) != " ".join(parte.ato.texto.casefold().split())):
                raise ValueError("Fonte textual não pertence à consulta composta.")
            cursor = fim
            if parte.ocorrencia is not None and (
                    parte.ocorrencia.turno_consulta != self.turno_consulta
                    or parte.ocorrencia.texto_consulta != f["texto_original"]):
                raise ValueError("Ocorrência pertence a outra consulta ou outro ato.")
