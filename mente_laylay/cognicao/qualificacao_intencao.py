"""Qualificação prévia pelo contrato da capacidade, sem conceder autoridade.

O primeiro leitor cobre a entrega textual quantificada. Ato desconhecido não
é classificado aqui como operação nem como incapacidade. Segmentação, negação,
autorização e disponibilidade permanecem nos respectivos owners canônicos.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import re
import unicodedata

from mente_laylay.especialistas.capacidades import contratos_qualificacao_intencao
from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia, grupo_nominal_de_papel

NUMERO_EXTENSAO = r'(?:uma?|dois|duas|tr[eê]s|quatro|cinco|poucas?|\d+)'
QUANTIDADE_EXTENSAO = (
    rf'(?:(?:at[eé]|no m[aá]ximo|pelo menos|ao menos|no m[ií]nimo) {NUMERO_EXTENSAO}'
    rf'|entre {NUMERO_EXTENSAO} e {NUMERO_EXTENSAO}'
    rf'|{NUMERO_EXTENSAO}(?: ou {NUMERO_EXTENSAO})?)'
)
_PEDIDO = re.compile(
    r'(?:(?:agora|por favor)[, ]+)*(?:(?:voc[eê] )?(?:pode|poderia|consegue) (?:me )?)?'
    r'(?:responda|responde|responder) '
    rf'(?:(?:em|com) (?P<quantidade>{QUANTIDADE_EXTENSAO})|(?P<contraida>numa?)) '
    r'(?P<nominal>[^.!?;,:]+)[.!?]*'
)


@dataclass(frozen=True, slots=True)
class CandidatoIntencao:
    capacidade: str
    proprietario: str
    resultado: str
    canal: str
    unidade: str
    quantidade: str
    modificadores: tuple[str, ...]
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_efeito: bool = field(default=False, init=False)


@dataclass(frozen=True, slots=True)
class QualificacaoIntencao:
    texto_ato: str
    candidatos: tuple[CandidatoIntencao, ...]
    origem: str = field(default='contratos_catalogo_capacidades', init=False)
    autoriza_execucao: bool = field(default=False, init=False)
    comprova_efeito: bool = field(default=False, init=False)

    def como_dict(self) -> dict:
        """Diagnóstico serializável; não é entrada de autorização ou receipt."""
        return asdict(self)


def qualificar_intencao_por_capacidades(texto: str) -> QualificacaoIntencao | None:
    """Confronta o ato integral com resultados/canais declarados no catálogo.

    As palavras não bastam: a construção deve pedir uma entrega, o núcleo
    deve ser uma unidade textual catalogada, os modificadores devem formar
    o mesmo grupo nominal e todo o ato precisa ser consumido. Destino externo,
    condição, negação, citação e outro verbo não podem desaparecer do match.
    """
    literal = re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(texto))).strip().casefold()
    pedido = _PEDIDO.fullmatch(literal)
    if pedido is None:
        return None
    palavras = pedido['nominal'].split()
    # Coordenação só entre adjetivos da mesma unidade; jamais entre ordens.
    if any(p == 'e' and (i == 0 or i == len(palavras)-1 or
           not (consultar_morfologia(palavras[i-1]) or 0) & 2 or
           not (consultar_morfologia(palavras[i+1]) or 0) & 2)
           for i, p in enumerate(palavras)):
        return None
    nominal = [p for p in palavras if p != 'e']
    if not grupo_nominal_de_papel(' '.join(nominal)):
        return None
    candidatos = []
    for contrato in contratos_qualificacao_intencao('conversa'):
        if (contrato.get('resultado') != 'autoria_conversacional'
                or contrato.get('canal') != 'conversa_atual'
                or contrato.get('exige_destino_externo') is not False
                or contrato.get('autoriza_execucao') is not False
                or contrato.get('comprova_efeito') is not False):
            continue
        nucleos = [p for p in nominal if p in contrato['unidades']]
        if len(nucleos) != 1:
            continue
        unidade = nucleos[0]
        modificadores = tuple(p for p in nominal if p != unidade)
        if not all((consultar_morfologia(p) or 0) & 2 for p in modificadores):
            continue
        candidatos.append(CandidatoIntencao(
            contrato['id'], contrato['proprietario'], contrato['resultado'], contrato['canal'],
            unidade, pedido['quantidade'] or pedido['contraida'][1:], modificadores))
    return QualificacaoIntencao(texto, tuple(candidatos)) if len(candidatos) == 1 else None
