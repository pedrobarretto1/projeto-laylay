"""Evidência efêmera de uma invocação; não é autorização ou último efeito."""
from dataclasses import dataclass, field
import math
import time

from mente_laylay.cognicao.contratos_turno import SnapshotComandoIA
from mente_laylay.memoria_mental.resultado_acao import obter_id_solicitacao


@dataclass(frozen=True, slots=True)
class ExecucaoObservada:
    """Somente o host coleta publicações aceitas na chamada do executor.

    Identidade/proveniência não provam alvo correto, sucesso, dependência ou
    vigência atual. O bool legado permanece separado dos receipts. Projeções
    JSON são diagnósticas; não podem voltar como este contrato tipado.
    """

    turno_id: str
    pedido: SnapshotComandoIA
    publicacoes: tuple[SnapshotComandoIA, ...]
    retorno_legado: bool
    instantes_publicacao: tuple[float, ...] = ()
    autoriza_execucao: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if (not isinstance(self.turno_id, str) or self.turno_id != self.turno_id.strip()
            or type(self.pedido) is not SnapshotComandoIA
            or type(self.publicacoes) is not tuple or type(self.retorno_legado) is not bool):
            raise ValueError("Observação exige turno capturado e snapshots imutáveis.")
        if (type(self.instantes_publicacao) is not tuple
            or (self.instantes_publicacao and len(self.instantes_publicacao) != len(self.publicacoes))
            or any(type(t) is not float or not math.isfinite(t) or t < 0 for t in self.instantes_publicacao)):
            raise ValueError("Instantes exigem monotonic observado por publicação.")
        pedido = self.pedido.como_dict()
        identidade = obter_id_solicitacao(pedido)
        intent = pedido.get("intent")
        if not identidade or not isinstance(intent, str) or not intent:
            raise ValueError("Observação exige solicitação identificada.")
        for snapshot in self.publicacoes:
            if type(snapshot) is not SnapshotComandoIA:
                raise ValueError("Publicação exige snapshot imutável.")
            receipt = snapshot.como_dict()
            if (obter_id_solicitacao(receipt) != identidade
                or receipt.get("intent") != intent.strip().upper()
                or receipt.get("origem") != "executor"):
                raise ValueError("Publicação não pertence à invocação capturada.")

    def como_dict(self) -> dict:
        return {"turno_id": self.turno_id, "pedido": self.pedido.como_dict(),
                "publicacoes": [p.como_dict() for p in self.publicacoes],
                "retorno_legado": self.retorno_legado,
                "instantes_publicacao": list(self.instantes_publicacao), "autoriza_execucao": False}

    def publicacao_recente(self, *, agora: float | None = None, ttl_s: float = 300.0) -> bool:
        """Idade da última publicação aceita, nunca da projeção contextual."""
        if not self.publicacoes or len(self.instantes_publicacao) != len(self.publicacoes):
            return False
        instante = time.monotonic() if agora is None else agora
        if (type(instante) not in (float, int) or type(ttl_s) not in (float, int)
            or not math.isfinite(instante) or not math.isfinite(ttl_s) or ttl_s <= 0):
            return False
        return 0 <= instante - self.instantes_publicacao[-1] <= ttl_s
