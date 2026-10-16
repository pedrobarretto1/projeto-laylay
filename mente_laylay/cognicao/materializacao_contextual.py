"""Liga fonte do ato e publicação qualificada aos resolvers compartilhados."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Mapping

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.cognicao.escopo_autorizacao import (
    AtoAguardandoMaterializacao, AutorizacaoAto, construir_autorizacoes_por_ato,
    vincular_proposta_ao_ato, coletar_atos_aguardando_materializacao, _identidade_operacional,
)
from mente_laylay.memoria_mental.observacao_execucao import ExecucaoObservada
from mente_laylay.memoria_mental.resultado_acao import obter_id_solicitacao


@dataclass(frozen=True, slots=True)
class MaterializacaoAtoContextual:
    """Candidato vinculado, não autorização, receipt novo ou tarefa futura."""
    ato: AtoAguardandoMaterializacao
    indice_antecedente: int
    observacao: ExecucaoObservada
    referencia: SnapshotComandoIA
    pedido: SnapshotComandoIA
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_efeito: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (type(self.ato) is not AtoAguardandoMaterializacao
            or type(self.observacao) is not ExecucaoObservada
            or self.observacao.turno_id != self.ato.turno_id
            or type(self.indice_antecedente) is not int
            or not 0 <= self.indice_antecedente < self.ato.indice
            or type(self.referencia) is not SnapshotComandoIA
            or type(self.pedido) is not SnapshotComandoIA):
            raise ValueError("Materialização exige fonte e invocação anterior vinculadas.")

    def como_dict(self) -> dict:
        return {"ato": self.ato.como_dict(), "indice_antecedente": self.indice_antecedente,
            "observacao": self.observacao.como_dict(), "referencia": self.referencia.como_dict(),
            "pedido": self.pedido.como_dict(), "estado": "materializado_sem_admissao",
            "autoriza_execucao": False, "comprova_efeito": False}


@dataclass(frozen=True, slots=True)
class ExecucaoContextualVinculada:
    """Transporte da admissão e publicação da mesma chamada, não nova permissão.

    O consumidor rederiva a materialização no prefixo atual. JSON, snapshots
    ou o tipo deste objeto sozinhos não certificam uma admissão vigente.
    """
    observacao: ExecucaoObservada
    admissao: AutorizacaoAto
    materializacao: MaterializacaoAtoContextual
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (type(self.observacao) is not ExecucaoObservada
            or type(self.admissao) is not AutorizacaoAto
            or type(self.materializacao) is not MaterializacaoAtoContextual):
            raise ValueError("Vínculo exige contratos nativos da mesma chamada.")
        a, m, o = self.admissao, self.materializacao, self.observacao
        if (a.turno_id != o.turno_id or a.turno_id != m.ato.turno_id
            or a.indice != m.ato.indice or a.texto != m.ato.como_dict()["texto_original"]
            or obter_id_solicitacao(a.pedido.como_dict()) != obter_id_solicitacao(o.pedido.como_dict())
            or _identidade_operacional(a.pedido.como_dict())
                != _identidade_operacional(o.pedido.como_dict())
            or _identidade_operacional(a.pedido.como_dict())
                != _identidade_operacional(m.pedido.como_dict())
            or _identidade_operacional(a.pedido.como_dict()) is None):
            raise ValueError("Vínculo não pertence à fonte/admissão/invocação capturadas.")


def materializar_por_publicacoes(
    ato: AtoAguardandoMaterializacao, turno: Mapping, mental: Mapping,
    observacoes: tuple[ExecucaoObservada | ExecucaoContextualVinculada, ...],
    resolver_ato: Callable[[str, dict], dict | None],
) -> MaterializacaoAtoContextual | None:
    # Memo efêmero só desta revalidação; não guarda autoridade entre chamadas.
    return _materializar_por_publicacoes(ato, turno, mental, observacoes, resolver_ato, {})


def _materializar_por_publicacoes(ato, turno, mental, observacoes, resolver_ato, derivacoes):
    """Não assume que a etapa imediatamente anterior é o referente.

    Receipts são projetados em frame efêmero vazio pelos owners existentes.
    Histórico pessoal/foco vivo não completam lacunas. Mais de um candidato
    compatível é ambiguidade; uma publicação anterior incerta não é ignorada
    para recuperar sucesso velho. Admissão/efeito continuam em outra fronteira.
    """
    from mente_laylay.autonomia.coordenador_intencao import resolver_referencias_da_intencao
    from mente_laylay.memoria_mental.contexto_compartilhado import (
        contrato_confirma_referencia_operacional, registrar_resultado_execucao,
    )
    from mente_laylay.memoria_mental.contexto_imediato import referencia_contextual_imediata

    if type(observacoes) is not tuple or not callable(resolver_ato):
        return None
    autorizacoes = construir_autorizacoes_por_ato(turno, mental, resolver_ato)
    candidatos = []
    pais = {}
    indices_observados = set()
    identidades_observadas = set()
    literal = ato.como_dict()["texto_original"]
    segmento = dict(turno["segmentos"][ato.indice])
    for posicao, transportado in enumerate(observacoes):
        vinculo = transportado if type(transportado) is ExecucaoContextualVinculada else None
        observacao = vinculo.observacao if vinculo is not None else transportado
        if type(observacao) is not ExecucaoObservada or observacao.turno_id != ato.turno_id:
            return None
        # Equivalência operacional pertence ao vínculo canônico por ato.
        # Repetições idênticas não recebem índice por suposição cronológica.
        if vinculo is not None:
            anterior = vinculo.materializacao
            indice_anterior = anterior.ato.indice
            if (indice_anterior >= ato.indice
                or anterior.ato not in coletar_atos_aguardando_materializacao(turno)):
                return None
            chave = (indice_anterior, posicao)
            if chave not in derivacoes:
                derivacoes[chave] = _materializar_por_publicacoes(anterior.ato, turno, mental,
                    observacoes[:posicao], resolver_ato, derivacoes)
            if derivacoes[chave] != anterior:
                return None
            indices = [indice_anterior]
            pais[indice_anterior] = anterior.indice_antecedente
        else:
            indices = [a.indice for a in autorizacoes
                if vincular_proposta_ao_ato(observacao.pedido.como_dict(), turno, (a,), set()) is not None]
        if len(indices) != 1:
            return None
        indice = indices[0]
        if indice >= ato.indice:
            continue
        pedido = observacao.pedido.como_dict()
        identidade = pedido["id_solicitacao"]
        if indice in indices_observados or identidade in identidades_observadas:
            return None
        indices_observados.add(indice)
        identidades_observadas.add(identidade)
        if not observacao.publicacao_recente():
            return None
        # Uma atualização final pode retirar a certeza da publicação anterior.
        receipt = observacao.publicacoes[-1].como_dict()
        if not contrato_confirma_referencia_operacional(intent=receipt["intent"],
            status=receipt["status"], executou=receipt["executou"], confirmado=receipt["confirmado"]):
            return None
        projecao = registrar_resultado_execucao({}, receipt)
        referencia = referencia_contextual_imediata(mente_integrada_estado=projecao,
            foco_vivo={}, texto_atual=literal)
        if not referencia:
            continue
        vinculo = {"tipo": referencia["tipo"], "nome": referencia["alvo"],
                   "dados": dict(referencia.get("params") or {}),
                   "origem": "publicacao_aceita_da_invocacao"}
        projecao["turno_atual"] = {**segmento, "id": turno["id"], "texto": literal,
            "texto_operacional": literal, "segmentos": [segmento], "referencia_resolvida": vinculo}
        projecao["retrato_turno_atual"] = {"referencia_resolvida": vinculo}
        candidato = resolver_referencias_da_intencao(resolver_ato(literal, projecao),
                                                   projecao["retrato_turno_atual"])
        if not candidato:
            continue
        # Nome resolvido não permite trocar silenciosamente a máquina do alvo.
        origem = (receipt.get("params") or {}).get("target", "pc_a")
        destino = (candidato.get("params") or {}).get("target", "pc_a")
        if origem not in {"pc_a", "pc_b"} or destino != origem:
            return None
        candidatos.append(MaterializacaoAtoContextual(ato, indice, observacao,
            SnapshotComandoIA(referencia), SnapshotComandoIA(candidato)))
    # Uma continuação comprovada sucede seu próprio antecedente. Não eliminar
    # outros candidatos pelo nome, pela posição na lista ou por serem antigos.
    ancestrais = set()
    for candidato in candidatos:
        indice = candidato.indice_antecedente
        while indice in pais:
            indice = pais[indice]
            ancestrais.add(indice)
    atuais = [c for c in candidatos if c.indice_antecedente not in ancestrais]
    return atuais[0] if len(atuais) == 1 else None
