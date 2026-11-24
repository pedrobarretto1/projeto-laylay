"""Limite textual de um título destinado a uma locução breve."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, intervalos_citados


_SEGUNDOS = dict(zip(('um', 'dois', 'tres', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove', 'dez'), range(1, 11)))
_MIDIA = r'(?:vinheta|chamada|abertura|locucao|anuncio)'
_PEDIDO = re.compile(
    r'(?:(?:qual|que) (?:nome|titulo)(?: (?:curto|breve|engracado|criativo))? '
    r'(?:caberia|cabe|funcionaria) (?:numa?|em uma?)|'
    r'(?:sugira|proponha|invente|escolha) um (?:nome|titulo) para (?:uma?|a|o)) '
    rf'{_MIDIA} de (?:ate )?(?P<tempo>\d{{1,2}}|{"|".join(_SEGUNDOS)}) segundos?[?!.]*',
)
_PREFERENCIA_PREPARATORIA = re.compile(
    r'(?:se fosse [^,;.!?]+, )?(?:voce|tu) preferiria um (?:nome|titulo) '
    r'(?:mais )?(?:curto|curtinho|breve)\?',
)
_PALAVRA = r'[^\W\d_]+'
_VOGAIS = frozenset('aeiou')


def segundos_titulo_oral(texto: str) -> int | None:
    """A restrição pertence à proposta, com preâmbulo apenas preparatório."""
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido

    if intervalos_citados(texto):
        return None
    partes = enunciados_discursivos(texto)
    pedido = _PEDIDO.fullmatch(normalizar_texto_basico(partes[-1])) if partes else None
    if pedido is None:
        return None
    for parte in partes[:-1]:
        if _PREFERENCIA_PREPARATORIA.fullmatch(normalizar_texto_basico(parte)):
            continue
        if not _preambulo_sem_outro_pedido(re.sub(r'^\W+', '', parte)):
            return None
    tempo = pedido['tempo']
    segundos = int(tempo) if tempo.isdecimal() else _SEGUNDOS[tempo]
    return segundos if 1 <= segundos <= 30 else None


@dataclass(frozen=True, slots=True)
class FormatoOral:
    turno_id: str
    texto_usuario: str
    segundos: int

    @property
    def limite_vogais(self) -> int:
        # Margem textual conservadora. A pronúncia e o tempo real dependem
        # da voz, do ritmo, das pausas e da gravação usada na vinheta.
        return 3 * self.segundos

    def instrucao(self) -> str:
        return (f'Proponha um título para locução de até {self.segundos} s, com no máximo {self.limite_vogais} '
                'vogais. Use Eu chamaria de «nome». Evite números, siglas e slogans adicionais. '
                'O tempo é uma estimativa textual.')

    def aceita(self, fala: str) -> bool:
        from mente_laylay.cognicao.fundamentacao_factual import _MOLDURA_NOME_PROPOSTO

        fala = fala.strip()
        citacoes = intervalos_citados(fala)
        if len(citacoes) != 1:
            return False
        inicio, fim = citacoes[0]
        if fala[fim:] not in {'', '.'} or not _MOLDURA_NOME_PROPOSTO.fullmatch(fala[:inicio]):
            return False
        titulo = fala[inicio + 1:fim - 1]
        if not re.fullmatch(rf'{_PALAVRA}(?:[ -]{_PALAVRA})*', titulo):
            return False
        palavras = re.findall(_PALAVRA, titulo)
        contagens = [sum(letra in _VOGAIS for letra in normalizar_texto_basico(p)) for p in palavras]
        return (all(contagens) and not any(p.isupper() and len(p) > 1 for p in palavras)
                and sum(contagens) <= self.limite_vogais)


def construir_formato_oral(texto: str, *, plano: Mapping[str, Any]) -> FormatoOral | None:
    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    segundos = segundos_titulo_oral(texto)
    return FormatoOral(str(plano['id']), texto, segundos) if segundos is not None else None


def formato_oral_vigente(plano: Mapping[str, Any]) -> FormatoOral | None:
    contrato = plano.get('contrato_fala') or {}
    limite = contrato.get('formato_oral')
    if (type(limite) is FormatoOral and limite.turno_id == str(plano.get('id'))
            and limite.texto_usuario == plano.get('texto_usuario') and 1 <= limite.segundos <= 30
            and str(contrato.get('turno_id')) == limite.turno_id and contrato.get('origem') == 'mente_unica'
            and contrato.get('autoriza_execucao') is False and plano.get('autoriza_execucao') is False
            and not plano.get('requer_execucao') and not plano.get('comandos')):
        return limite
    return None
