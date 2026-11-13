"""Qualificação prévia pelo contrato da capacidade, sem conceder autoridade.

O primeiro leitor cobre a entrega textual quantificada. Ato desconhecido não
é classificado aqui como operação nem como incapacidade. Segmentação, negação,
autorização e disponibilidade permanecem nos respectivos owners canônicos.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict, replace
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
    r'(?:(?:s[oó]|apenas|somente) )?'
    rf'(?:(?:(?:em|com) )?(?:[oa]s? )?(?P<quantidade>{QUANTIDADE_EXTENSAO})|(?P<contraida>numa?)) '
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
    conteudo: str = ''
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
    # Uma coordenação de entregas preserva o mesmo canal somente quando
    # cada membro inteiro satisfaz seu próprio contrato do catálogo.
    membros = re.split(rf'\s+e\s+(?=(?:[oa]\s+|{QUANTIDADE_EXTENSAO}\s+))', pedido['nominal'])
    if len(membros) > 1:
        quantidade = pedido['quantidade'] or pedido['contraida'][1:]
        membros[0] = quantidade + ' ' + membros[0]
        qualificacoes = []
        for membro in membros:
            membro = re.sub(r'^o\s+', 'um ', membro)
            membro = re.sub(r'^a\s+', 'uma ', membro)
            q = qualificar_intencao_por_capacidades('Responda com ' + membro)
            if q is None:
                return None
            qualificacoes.extend(q.candidatos)
        return QualificacaoIntencao(texto, tuple(qualificacoes))
    # Complemento de conteúdo não é um adjetivo da unidade de formato.
    # Qualificar ambos no catálogo conserva o mesmo canal sem absorver um
    # destino externo ou um verbo novo. Não há lista privada de assuntos.
    complemento = re.fullmatch(r'(.+?) de ([^\W\d_]+)', pedido['nominal'])
    if complemento:
        quantidade = pedido['quantidade'] or pedido['contraida'][1:]
        forma = qualificar_intencao_por_capacidades('Responda com ' + quantidade + ' ' + complemento[1])
        conteudo = qualificar_intencao_por_capacidades('Responda com um ' + complemento[2])
        if (forma and conteudo and len(forma.candidatos) == len(conteudo.candidatos) == 1
                and forma.candidatos[0].capacidade == 'conversa.formato_resposta'
                and conteudo.candidatos[0].capacidade == 'conversa.conteudo_resposta'):
            return QualificacaoIntencao(texto, (replace(forma.candidatos[0],
                conteudo=conteudo.candidatos[0].unidade),))
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
