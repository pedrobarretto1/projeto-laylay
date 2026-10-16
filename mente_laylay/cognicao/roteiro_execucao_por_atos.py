"""Ordem efêmera da fonte admitida; não é fila autônoma ou permissão durável."""
from dataclasses import dataclass

from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal, SnapshotComandoIA
from mente_laylay.cognicao.escopo_autorizacao import AtoAguardandoMaterializacao


@dataclass(frozen=True, slots=True)
class EtapaExecucaoPrincipal:
    indice: int
    texto: str
    pedido: SnapshotComandoIA | None = None
    obrigacao: AtoAguardandoMaterializacao | None = None

    def __post_init__(self) -> None:
        if (type(self.indice) is not int or self.indice < 0
            or not isinstance(self.texto, str) or not self.texto.strip()
            or (self.pedido is None) == (self.obrigacao is None)
            or (self.pedido is not None and type(self.pedido) is not SnapshotComandoIA)
            or (self.obrigacao is not None and (type(self.obrigacao) is not AtoAguardandoMaterializacao
                                               or self.obrigacao.indice != self.indice
                                               or self.obrigacao.como_dict()["texto_original"] != self.texto))):
            raise ValueError("Etapa exige índice e pedido admitido ou obrigação não executável.")


@dataclass(frozen=True, slots=True)
class RoteiroExecucaoPrincipal:
    proposta: ContratoPropostaPrincipal
    etapas: tuple[EtapaExecucaoPrincipal, ...]

    def __post_init__(self) -> None:
        if (type(self.proposta) is not ContratoPropostaPrincipal or not self.proposta.proveniencia_conhecida
            or type(self.etapas) is not tuple or not self.etapas
            or any(type(e) is not EtapaExecucaoPrincipal for e in self.etapas)):
            raise ValueError("Roteiro exige fonte capturada e etapas imutáveis.")
        indices = [e.indice for e in self.etapas]
        if indices != sorted(set(indices)) or any(e.obrigacao is not None and (
            e.obrigacao.turno_id != self.proposta.turno_id
            or e.obrigacao.fonte_textual != self.proposta.texto_usuario) for e in self.etapas):
            raise ValueError("Roteiro exige ordem inequívoca da fonte atual.")
