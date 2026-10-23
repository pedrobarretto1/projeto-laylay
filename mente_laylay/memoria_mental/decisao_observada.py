"""Fonte imutável capturada pelo decisor antes do efeito, sem novo registro."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, localcontext
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mente_laylay.memoria_mental.registro_semantico import RevisaoAlegacaoConsulta

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA, ContratoExplicativoAto


# Semântica de TURN/ TURNEND: yaw final menos yaw no início do mesmo giro.
# O vínculo ao início concreto é dado também pelo ID da ocorrência.
REFERENCIAL_GIRO_RELATIVO = "giro_imu_yaw_relativo_inicio_esquerda_positiva_v1"


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
    referencial: str = ""
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        textos = (self.ocorrencia_id, self.owner, self.grandeza, self.unidade,
                  self.metodo, self.limite_observacao)
        if (any(type(v) is not str or not v or v != v.strip() or len(v) > 240 for v in textos)
                or type(self.valor) not in (int, float) or not math.isfinite(self.valor)):
            raise ValueError("Medição exige origem, valor finito, unidade, método e limite explícitos.")
        if type(self.referencial) is not str or self.referencial != self.referencial.strip() or len(self.referencial) > 240:
            raise ValueError("Referencial de medição deve ser explícito ou ausente no legado.")


@dataclass(frozen=True, slots=True)
class NaoQualificacaoMedicao:
    """Critério observado do owner para não admitir uma medição, sem causa física."""

    ocorrencia_id: str
    owner: str
    grandeza: str
    unidade: str
    criterio: str
    fonte: str
    codigo: str = ""
    autoriza_execucao: bool = field(default=False, init=False)
    confirma_efeito: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (any(type(v) is not str or not v or v != v.strip() or len(v) > 240 for v in
                (self.ocorrencia_id, self.owner, self.grandeza, self.unidade, self.fonte))
                or type(self.criterio) is not str
                or self.criterio not in {"fonte_nao_correlacionada", "contexto_alterado", "valor_nao_admitido",
                    "criterio_da_fonte_nao_atendido"}
                or type(self.codigo) is not str or self.codigo != self.codigo.strip() or len(self.codigo) > 80):
            raise ValueError("Não qualificação exige identidade, owner, fonte e critério explícitos.")


@dataclass(frozen=True, slots=True)
class ExpectativaResultado:
    """Valor solicitado capturado antes do efeito; não é medição ou permissão."""

    ocorrencia_id: str
    owner: str
    grandeza: str
    valor: int | float
    unidade: str
    fonte: str
    registrada_em: float
    referencial: str = ""
    autoriza_execucao: bool = field(default=False, init=False)
    confirma_efeito: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        textos = (self.ocorrencia_id, self.owner, self.grandeza, self.unidade, self.fonte)
        if (any(type(v) is not str or not v or v != v.strip() or len(v) > 240 for v in textos)
                or type(self.valor) not in (int, float) or not math.isfinite(self.valor)
                or type(self.registrada_em) not in (int, float)
                or not math.isfinite(self.registrada_em) or self.registrada_em < 0):
            raise ValueError("Expectativa exige origem, valor finito, unidade e instante de captura.")
        if type(self.referencial) is not str or self.referencial != self.referencial.strip() or len(self.referencial) > 240:
            raise ValueError("Referencial da meta deve ser explícito ou ausente no legado.")


@dataclass(frozen=True, slots=True)
class ComparacaoResultado:
    """Derivação das fontes do owner, sem tolerância, causa ou prova de efeito.

    Igualdade de nomes/unidades não certifica compatibilidade física: o owner
    precisa declarar o mesmo referencial em ambas as fontes qualificadas.
    """

    expectativa: ExpectativaResultado
    medicao: MedicaoObservada
    autoriza_execucao: bool = field(default=False, init=False)
    confirma_efeito: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        e, m = self.expectativa, self.medicao
        if (type(e) is not ExpectativaResultado or type(m) is not MedicaoObservada
                or not e.referencial or (e.ocorrencia_id, e.owner, e.grandeza, e.unidade, e.referencial)
                != (m.ocorrencia_id, m.owner, m.grandeza, m.unidade, m.referencial)):
            raise ValueError("Comparação exige fontes do mesmo episódio, owner, grandeza, unidade e referencial explícito.")

    @property
    def diferenca(self) -> Decimal:
        """Medido menos solicitado, sobre as representações decimais registradas."""
        a, b = Decimal(str(self.medicao.valor)), Decimal(str(self.expectativa.valor))
        with localcontext() as contexto:
            # Evitar ruído binário e arredondamento da subtração, inclusive
            # com expoentes distintos; não acrescenta precisão ao sensor.
            contexto.prec = max(a.adjusted(), b.adjusted()) - min(a.as_tuple().exponent, b.as_tuple().exponent) + 2
            return a - b


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
    expectativas: tuple[ExpectativaResultado, ...] = ()
    nao_qualificacoes_medicao: tuple[NaoQualificacaoMedicao, ...] = ()

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
        if (type(self.expectativas) is not tuple or len(self.expectativas) > 8
                or any(type(e) is not ExpectativaResultado or e.ocorrencia_id != self.id
                       or e.owner != self.owner or e.registrada_em > self.iniciada_em for e in self.expectativas)
                or len({(e.grandeza, e.unidade) for e in self.expectativas}) != len(self.expectativas)):
            raise ValueError("Expectativas exigem captura anterior do mesmo episódio e owner, sem duplicação.")
        if self.decisao is not None:
            d = self.decisao
            if (type(d) is not DecisaoObservada or d.registrada_em > self.iniciada_em
                    or (d.turno_id, d.sessao, d.intencao_id) !=
                       (self.turno_origem, self.sessao, self.intencao_id)):
                raise ValueError("Decisão não pertence ao episódio observado.")
        elif self.justificativa_registrada:
            raise ValueError("Justificativa exige fonte anterior do decisor.")
        if (type(self.nao_qualificacoes_medicao) is not tuple or len(self.nao_qualificacoes_medicao) > 8
                or any(type(n) is not NaoQualificacaoMedicao or (n.ocorrencia_id, n.owner) != (self.id, self.owner)
                    for n in self.nao_qualificacoes_medicao)
                or len({(n.grandeza, n.unidade, n.fonte) for n in self.nao_qualificacoes_medicao}) != len(self.nao_qualificacoes_medicao)):
            raise ValueError("Não qualificações exigem vínculo ao episódio e owner, sem duplicação.")


@dataclass(frozen=True, slots=True)
class FontesComparacaoResultado:
    """Fontes da mesma execução, sem fabricar um episódio histórico."""
    id: str
    expectativas: tuple[ExpectativaResultado, ...] = ()
    medicoes: tuple[MedicaoObservada, ...] = ()
    iniciada_em: float | None = None
    autoriza_execucao: bool = field(default=False, init=False)
    confirma_efeito: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self.id) is not str or not self.id or self.id != self.id.strip():
            raise ValueError("Fontes exigem identidade da execução.")
        if (self.iniciada_em is not None and (type(self.iniciada_em) not in (int, float)
                or not math.isfinite(self.iniciada_em) or self.iniciada_em < 0)):
            raise ValueError("Início exige instante finito da execução.")
        if (type(self.expectativas) is not tuple or len(self.expectativas) > 8
                or any(type(e) is not ExpectativaResultado or e.ocorrencia_id != self.id
                    or self.iniciada_em is None or e.registrada_em > self.iniciada_em for e in self.expectativas)
                or len({(e.grandeza, e.unidade) for e in self.expectativas}) != len(self.expectativas)):
            raise ValueError("Meta exige captura anterior da mesma execução, sem duplicação.")
        if (type(self.medicoes) is not tuple or len(self.medicoes) > 8
                or any(type(m) is not MedicaoObservada or m.ocorrencia_id != self.id for m in self.medicoes)
                or len({(m.owner, m.grandeza, m.unidade, m.metodo) for m in self.medicoes}) != len(self.medicoes)):
            raise ValueError("Medições exigem vínculo à mesma execução, sem duplicação.")


class FalhaExecucaoComFontes(RuntimeError):
    """Transporta a captura prévia quando não há receipt; a falha permanece."""

    def __init__(self, fontes: FontesComparacaoResultado) -> None:
        if type(fontes) is not FontesComparacaoResultado:
            raise ValueError("Falha observada exige fontes tipadas da execução.")
        self._fontes = fontes
        super().__init__("falha_execucao_com_fontes")

    @property
    def fontes(self) -> FontesComparacaoResultado:
        return self._fontes


@dataclass(frozen=True, slots=True)
class AvaliacaoComparacaoResultado:
    """Disponibilidade derivada das fontes admitidas, nunca um diagnóstico físico.

    A primeira premissa ausente é declarada na ordem fonte, grandeza, unidade,
    referencial e unicidade. Motivo e comparação não são campos autoráveis.
    """

    episodio: EpisodioExplicavel | FontesComparacaoResultado
    expectativa: ExpectativaResultado | None
    autoriza_execucao: bool = field(default=False, init=False)
    confirma_efeito: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (type(self.episodio) not in (EpisodioExplicavel, FontesComparacaoResultado)
                or (self.expectativa is None and self.episodio.expectativas)
                or (self.expectativa is not None and (type(self.expectativa) is not ExpectativaResultado
                    or not any(self.expectativa is e for e in self.episodio.expectativas)))):
            raise ValueError("Avaliação exige o episódio admitido e sua própria meta, ou ausência registrada.")

    @property
    def medicoes_mesma_unidade(self) -> tuple[MedicaoObservada, ...]:
        meta = self.expectativa
        return tuple(m for m in self.episodio.medicoes if meta is not None
            and (m.owner, m.grandeza, m.unidade) == (meta.owner, meta.grandeza, meta.unidade))

    @property
    def medicoes_compativeis(self) -> tuple[MedicaoObservada, ...]:
        meta = self.expectativa
        return tuple(m for m in self.medicoes_mesma_unidade
            if meta is not None and meta.referencial and m.referencial == meta.referencial)

    @property
    def estado(self) -> str:
        meta, medicoes = self.expectativa, self.episodio.medicoes
        if meta is None:
            return "meta_ausente" if medicoes else "fontes_ausentes"
        if not medicoes:
            return "medicao_ausente"
        if not any(m.owner == meta.owner for m in medicoes):
            return "owner_distinto"
        if not any(m.owner == meta.owner and m.grandeza == meta.grandeza for m in medicoes):
            return "grandeza_sem_correspondencia"
        if not self.medicoes_mesma_unidade:
            return "unidade_distinta"
        if not meta.referencial:
            return "referencial_meta_ausente"
        candidatas = self.medicoes_compativeis
        if not candidatas:
            return ("referencial_medicao_ausente" if any(not m.referencial for m in self.medicoes_mesma_unidade)
                    else "referencial_distinto")
        return "comparavel" if len(candidatas) == 1 else "medicao_ambigua"

    @property
    def comparacao(self) -> ComparacaoResultado | None:
        if self.estado != "comparavel":
            return None
        return ComparacaoResultado(self.expectativa, self.medicoes_compativeis[0])


def avaliar_comparacoes_resultado(episodio: EpisodioExplicavel | FontesComparacaoResultado) -> tuple[AvaliacaoComparacaoResultado, ...]:
    """Um owner para elegibilidade e limite de cada meta, sem completar fontes."""
    if type(episodio) not in (EpisodioExplicavel, FontesComparacaoResultado):
        return ()
    return tuple(AvaliacaoComparacaoResultado(episodio, meta) for meta in (episodio.expectativas or (None,)))


def comparacoes_resultado(episodio: EpisodioExplicavel | FontesComparacaoResultado) -> tuple[ComparacaoResultado, ...]:
    """API existente; consome a mesma avaliação que explica a indisponibilidade."""
    return tuple(c for avaliacao in avaliar_comparacoes_resultado(episodio) if (c := avaliacao.comparacao) is not None)


@dataclass(frozen=True, slots=True)
class ExplicacaoOcorrencia:
    """Seleção feita pelo host para esta consulta, nunca pela prosa da LLM."""

    turno_consulta: str
    texto_consulta: str
    episodios: tuple[EpisodioExplicavel, ...]
    referencia: str
    autoriza_execucao: bool = field(default=False, init=False)
    revisoes_proposicoes: tuple[tuple[str, RevisaoAlegacaoConsulta], ...] = ()

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
        if type(self.revisoes_proposicoes) is not tuple:
            raise ValueError("Revisões exigem coleção tipada imutável.")
        if self.revisoes_proposicoes:
            from mente_laylay.memoria_mental.registro_semantico import RevisaoAlegacaoConsulta
            if (len(self.revisoes_proposicoes)>24
                    or self.referencia != "unica"
                    or any(type(i) is not tuple or len(i)!=2 or type(i[0]) is not str
                        or type(i[1]) is not RevisaoAlegacaoConsulta
                        or i[1].turno_consulta!=self.turno_consulta or i[1].texto_consulta!=self.texto_consulta
                        for i in self.revisoes_proposicoes)
                    or len({i[0] for i in self.revisoes_proposicoes})!=len(self.revisoes_proposicoes)):
                raise ValueError("Revisões exigem fonte tipada vinculada à mesma consulta histórica.")


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
