"""Contrato offline de revisão de vigência e cobertura de contexto.

O registro pertence ao revisor confiável, nunca ao proponente. Registrar uma
decisão pressupõe revisão externa real; texto, ID ou um dict da LLM não
substituem essa revisão. A sonda automática exige revisão quando não cobre
o contexto posterior. Não interpreta revogações nem está ligada ao runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Mapping, Sequence

from scripts.analises.grafo_premissas_didaticas import (
    FonteDidatica, PremissaDidatica, ReferenteAncorado,
    RegraDidatica, conferir_grafo_premissas, conferir_qualificacao_na_conversa,
)


@dataclass(frozen=True)
class RetratoVigencia:
    """Identifica todo o objeto revisado, não só o ID reutilizável da fonte."""

    chave: str
    escopo: str
    regra_id: str


def retratar_vigencia(
    fontes: tuple[FonteDidatica, ...],
    referentes: tuple[ReferenteAncorado, ...],
    premissas: tuple[PremissaDidatica, ...],
    regras: tuple[RegraDidatica, ...],
    *, escopo: str, regra_id: str, texto_atual: str,
    mensagens: Sequence[object],
) -> RetratoVigencia:
    """Sela conteúdo, ordem e alvo; não interpreta texto nem aprova vigência."""
    estrutura = conferir_grafo_premissas(
        fontes, referentes, premissas, regras, escopo=escopo,
    )
    if (estrutura["estado"] != "estrutura_ancorada_revisao_pendente"
            or not isinstance(regra_id, str)
            or regra_id not in {r.identificador for r in regras}
            or not isinstance(texto_atual, str)
            or not isinstance(mensagens, Sequence)
            or isinstance(mensagens, (str, bytes))):
        raise ValueError("retrato de vigência inválido")
    # Não usar set nem texto truncado: repetição, posição e complemento final
    # podem mudar a revisão. Só falas do usuário têm autoridade neste adaptador.
    historico = [item["content"] for item in mensagens
                 if isinstance(item, Mapping)
                 and str(item.get("role", "")).casefold() == "user"
                 and isinstance(item.get("content"), str)]
    observado = {*historico, texto_atual}
    if any(f.origem != "usuario" or f.texto not in observado for f in fontes):
        raise ValueError("fonte sem observação integral do usuário")
    payload = {
        "versao": 1, "escopo": escopo, "regra_id": regra_id,
        "fontes": [asdict(f) for f in fontes],
        "referentes": [asdict(r) for r in referentes],
        "premissas": [asdict(p) for p in premissas],
        "regras": [asdict(r) for r in regras],
        "historico_usuario_integral": historico, "texto_atual": texto_atual,
    }
    chave = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return RetratoVigencia(chave, escopo, regra_id)


class RegistroVigenciaCriterios:
    """Owner de decisões revisadas em memória, sem porta para JSON de modelo.

    Esta API de escrita é exclusiva do revisor confiável. Uma implantação
    futura exige conexão com esse owner real; não basta a LLM dizer que reviu.
    Revisões conflitantes do mesmo retrato ficam indeterminadas, sem escolher
    silenciosamente a última. Mudança no retrato requer nova revisão.
    """

    def __init__(self) -> None:
        self._revisoes: dict[RetratoVigencia, set[str]] = {}

    def registrar_revisao(self, retrato: RetratoVigencia, *, estado: str) -> None:
        if (type(retrato) is not RetratoVigencia
                or not isinstance(estado, str)
                or estado not in {"vigente", "revogado", "indeterminado"}):
            raise ValueError("revisão inválida")
        self._revisoes.setdefault(retrato, set()).add(estado)

    def consultar(self, retrato: RetratoVigencia) -> str:
        estados = self._revisoes.get(retrato, set())
        if not estados:
            return "sem_revisao"
        if len(estados) != 1:
            return "revisoes_conflitantes"
        return next(iter(estados))


def conferir_qualificacao_com_vigencia(
    fontes: tuple[FonteDidatica, ...],
    referentes: tuple[ReferenteAncorado, ...],
    premissas: tuple[PremissaDidatica, ...],
    regras: tuple[RegraDidatica, ...],
    *, registro: RegistroVigenciaCriterios, escopo: str, premissa_id: str,
    regra_id: str, rotulo: str, texto_atual: str, mensagens: Sequence[object],
) -> dict[str, object]:
    """Só consulta o registro host; não registra/revoga por uma frase isolada."""
    base = {"estado": "vigencia_fonte_pendente", "comparacao_numerica": False,
            "vigencia": "sem_revisao", "relacao_semantica_verificada": False,
            "aprovado_para_compor": False, "autoriza_efeito": False}
    if type(registro) is not RegistroVigenciaCriterios:
        return {**base, "estado": "registro_vigencia_invalido"}
    try:
        retrato = retratar_vigencia(
            fontes, referentes, premissas, regras, escopo=escopo,
            regra_id=regra_id, texto_atual=texto_atual, mensagens=mensagens,
        )
    except (ValueError, TypeError, KeyError, AttributeError):
        return {**base, "estado": "retrato_vigencia_invalido"}
    vigencia = registro.consultar(retrato)
    if vigencia != "vigente":
        return {**base, "vigencia": vigencia,
                "estado": "criterio_revogado" if vigencia == "revogado"
                else "vigencia_fonte_pendente"}
    resultado = conferir_qualificacao_na_conversa(
        fontes, referentes, premissas, regras, escopo=escopo,
        premissa_id=premissa_id, regra_id=regra_id, rotulo=rotulo,
        texto_atual=texto_atual, mensagens=mensagens, registro_vigencia=registro,
    )
    return {**resultado, "vigencia": "revisada_no_retrato"}


def conferir_contexto_criterio(
    fontes: tuple[FonteDidatica, ...], referentes: tuple[ReferenteAncorado, ...],
    premissas: tuple[PremissaDidatica, ...], regras: tuple[RegraDidatica, ...],
    *, escopo: str, premissa_id: str, regra_id: str, texto_atual: str,
    mensagens: Sequence[object], registro: object = None,
) -> dict[str, object]:
    """Não confunde falta de revisão com revogação confirmada.

    Sem revisor, somente uma leitura numérica integral representada pela
    premissa pode seguir a regra. Outras falas posteriores requerem revisão
    do contexto. É cobertura literal estreita, não certificado de vigência.
    """
    base = {"estado": "contexto_criterio_pendente", "vigencia": "nao_demonstrada",
            "comparacao_numerica": False, "relacao_semantica_verificada": False,
            "aprovado_para_compor": False, "autoriza_efeito": False}
    try:
        retrato = retratar_vigencia(
            fontes, referentes, premissas, regras, escopo=escopo,
            regra_id=regra_id, texto_atual=texto_atual, mensagens=mensagens,
        )
    except (ValueError, TypeError, KeyError, AttributeError):
        return {**base, "estado": "retrato_vigencia_invalido"}
    if registro is not None:
        if type(registro) is not RegistroVigenciaCriterios:
            return {**base, "estado": "registro_vigencia_invalido"}
        estado = registro.consultar(retrato)
        if estado == "vigente":
            return {**base, "estado": "contexto_conferido", "vigencia": "revisada_no_retrato"}
        return {**base, "estado": "criterio_revogado" if estado == "revogado"
                else "vigencia_fonte_pendente", "vigencia": estado}
    regra = next(r for r in regras if r.identificador == regra_id)
    premissa = next((p for p in premissas if p.identificador == premissa_id), None)
    if premissa is None:
        return {**base, "estado": "selecao_invalida"}
    fonte_regra = next(f.texto for f in fontes if f.identificador == regra.fonte_id)
    fonte_medida = next(f.texto for f in fontes if f.identificador == premissa.fonte_id)
    historico = [m["content"] for m in mensagens if isinstance(m, Mapping)
                 and str(m.get("role", "")).casefold() == "user"
                 and isinstance(m.get("content"), str)]
    historico.append(texto_atual)
    # Primeira ocorrência: repetir a regra após uma alteração não a restaura
    # automaticamente. Não usar a ordem da lista proposta de fontes.
    indice = historico.index(fonte_regra)

    def leitura_integral(texto: str) -> bool:
        if texto != fonte_medida or not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?", premissa.valor):
            return False
        # Superfície estrita da observação: não basta citar um número dentro
        # de uma frase maior que também revoga/corrige a regra.
        atributo = re.escape(premissa.atributo)
        return re.fullmatch(
            rf"\s*(?:(?:o|a)\s+)?(?:sensor\s+de\s+)?{atributo}\s+"
            rf"(?:foi|mediu|leu|marcou)\s+{re.escape(premissa.valor)}\s*"
            rf"{re.escape(premissa.unidade)}\.?\s*", texto, re.IGNORECASE,
        ) is not None

    pendentes = [i for i in range(indice + 1, len(historico))
                 if historico[i].strip() and historico[i] != fonte_regra
                 and not leitura_integral(historico[i])]
    if pendentes:
        return {**base, "indices_contexto_pendente": pendentes}
    return {**base, "estado": "contexto_conferido",
            "vigencia": "sem_contexto_posterior_pendente"}
