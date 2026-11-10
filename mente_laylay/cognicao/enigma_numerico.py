"""Realiza pedidos integrais de enigma de código com dedução conferível."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos


_NUMEROS = {nome: n for n, nome in enumerate(
    ('um', 'dois', 'tres', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove'), start=1,
)}
_NUMEROS.update(uma=1, duas=2)
_NUMERO = r'(?:[1-9]|' + '|'.join(_NUMEROS) + ')'
_LARGURA = rf'(?P<largura>{_NUMERO})\s+digitos?'
_QUANTIDADE = rf'(?P<quantidade>{_NUMERO})\s+pistas?(?:\s+(?:claras?|justas?))?'
_CODIGO = r'(?:codigo(?:\s+numerico)?|senha(?:\s+numerica)?|cadeado)'
_PEDIDO_DIRETO = re.compile(
    r'(?:(?:por favor,? |me )?(?:crie|cria|invente|inventa|monte|elabore|faca|proponha)|'
    r'(?:voce )?pode (?:criar|inventar|montar|elaborar|fazer|propor)|me d[eê]) '
    r'um (?:enigma|desafio) '
    rf'(?:(?:de|com) (?:{_CODIGO} (?:de|com) )?|para descobrir (?:uma?|[oa]) {_CODIGO} de )'
    rf'{_LARGURA}(?:,? com (?:{_QUANTIDADE}|pistas claras))?'
    r'(?: para (?:um jogo|uma historia))?[.!?]?'
)
_PEDIDO_NA_CENA = re.compile(
    r'(?:imagine|imagina|suponha) que (?:a|uma) (?P<recipiente>caixa|arca|maleta) (?:tem|tenha) '
    rf'um cadeado de {_LARGURA}[:,] (?:que|quais) {_QUANTIDADE} (?:voce )?'
    r'(?:espalharia|deixaria|colocaria) (?:pel[oa]|n[oa]) (?P<local>quintal|jardim|sala) '
    r'(?:para|pra) (?:(?:o|a) [a-z]+ |(?:ele|ela) )?descobrir '
    r'(?:a senha|o codigo)(?: sozinh[oa])?\?'
)
_ELEMENTO_DE_CENA = r'(?:ideia|cena|enredo|reviravolta|historia|jogo|misterio|caixa|arca|relogio)'
_COMENTARIO_INICIAL = re.compile(
    r'(?:(?:nossa|uau|caramba)[!,]\s*)?'
    r'(?:'
    rf'que {_ELEMENTO_DE_CENA} (?:boa|bom|legal|otim[oa]|criativ[oa])|'
    rf'(?:gostei d[oa]|adorei [oa]|curti [oa]) {_ELEMENTO_DE_CENA}(?: e d[oa] {_ELEMENTO_DE_CENA})?|'
    rf'voce (?:ja )?(?:criou|inventou|imaginou|montou) (?:quase )?(?:[oa]|uma?) {_ELEMENTO_DE_CENA}'
    rf'(?: de (?:uma?|[oa]) {_ELEMENTO_DE_CENA})?(?: inteir[oa])?|'
    r'(?:(?:mas|entao) )?(?:o|esse|este) (?:misterio|desafio|enigma|jogo) '
    r'(?:precisa ter|precisa de|tem que ter) (?:uma )?solucao (?:justa|unica|clara|dedutivel)'
    r')[.!]'
)
_CENARIOS = {'quintal': 'do quintal', 'jardim': 'do jardim', 'sala': 'da sala'}
_LOCAIS_PISTAS = (
    'sob o vaso', 'atrás do relógio', 'junto à caixa', 'no encosto da cadeira',
    'sob o tapete', 'no caderno', 'ao lado da lanterna', 'no banco', 'no envelope',
)
_DESLOCAMENTOS = (-2, 3, -4, 5, -6, 5, -3, 1)


@dataclass(frozen=True, slots=True)
class _Pedido:
    largura: int
    quantidade: int
    local: str = ''
    recipiente: str = ''


@dataclass(frozen=True, slots=True)
class _RegraDigito:
    anterior: int | None
    deslocamento: int

    def enunciado(self, posicao: int) -> str:
        if self.anterior is None:
            return f'o dígito {posicao} é o número de lados de um hexágono'
        operador = 'mais' if self.deslocamento > 0 else 'menos'
        return f'o dígito {posicao} é o dígito {self.anterior} {operador} {abs(self.deslocamento)}'


def _pedido_vigente(texto: str, plano: Mapping[str, Any]) -> _Pedido | None:
    if (not plano.get('id') or plano.get('texto_usuario') != texto
        or plano.get('autoriza_execucao') is not False or plano.get('requer_execucao')
        or plano.get('comandos') or plano.get('misto') or plano.get('texto_operacional')
        or dict(plano.get('atualidade_factual') or {}).get('depende_atualidade')):
        return None
    enunciados = tuple(map(normalizar_texto_basico, enunciados_discursivos(texto)))
    # Reações criativas e critérios podem acompanhar o pedido. Uma segunda
    # pergunta, uma ordem ou outro enunciado permanece no fluxo normal.
    if not enunciados or not all(map(_COMENTARIO_INICIAL.fullmatch, enunciados[:-1])):
        return None
    nucleo = enunciados[-1]
    pedido = _PEDIDO_DIRETO.fullmatch(nucleo) or _PEDIDO_NA_CENA.fullmatch(nucleo)
    if pedido is None:
        return None

    def numero(valor: str) -> int:
        return _NUMEROS[valor] if valor in _NUMEROS else int(valor)

    largura = numero(pedido['largura'])
    quantidade = numero(pedido['quantidade']) if pedido['quantidade'] else largura
    dados_cena = pedido.groupdict()
    return _Pedido(largura, quantidade, dados_cena.get('local', ''), dados_cena.get('recipiente', ''))


def _deduzir_codigo(largura: int, regras: tuple[_RegraDigito, ...]) -> tuple[int, ...] | None:
    if len(regras) != largura:
        return None
    # Cada passo fixa exatamente um dígito a partir de uma constante ou de
    # outro já fixado. Se faltar uma posição ou a igualdade sair de 0 a 9,
    # não há uma dedução inteira com a largura do pedido.
    digitos: list[int] = []
    for regra in regras:
        if regra.anterior is None:
            base = 0
        elif 1 <= regra.anterior <= len(digitos):
            base = digitos[regra.anterior - 1]
        else:
            return None
        digito = base + regra.deslocamento
        if not 0 <= digito <= 9:
            return None
        digitos.append(digito)
    return tuple(digitos)


def _realizar(pedido: _Pedido) -> str | None:
    regras = (_RegraDigito(None, 6), *(
        _RegraDigito(posicao, delta)
        for posicao, delta in enumerate(_DESLOCAMENTOS[:pedido.largura - 1], start=1)
    ))
    digitos = _deduzir_codigo(pedido.largura, regras)
    if digitos is None:
        return None
    grupos = [[] for _ in range(pedido.quantidade)]
    for indice, regra in enumerate(regras):
        grupo = indice * min(pedido.largura, pedido.quantidade) // pedido.largura
        grupos[grupo].append(regra.enunciado(indice + 1))
    for indice in range(pedido.largura, pedido.quantidade):
        posicao = indice % pedido.largura
        parcela = indice - pedido.largura + 1
        grupos[indice].append(
            f'o dígito {posicao + 1} somado a {parcela} dá {digitos[posicao] + parcela}',
        )
    abertura = f'Na cena {_CENARIOS[pedido.local]}' if pedido.local else 'Neste enigma'
    cadeado = f'o cadeado da {pedido.recipiente}' if pedido.recipiente else 'o cadeado'
    digito = 'dígito' if pedido.largura == 1 else 'dígitos, lidos da esquerda para a direita'
    pistas = []
    for indice, grupo in enumerate(grupos, start=1):
        local = f'junto à {pedido.recipiente}' if indice == 3 else _LOCAIS_PISTAS[indice - 1]
        lugar = f', {local}' if pedido.local else ''
        pistas.append(f'Pista {indice}{lugar}: {"; ".join(grupo)}.')
    return f'{abertura}, {cadeado} aceita {pedido.largura} {digito}. ' + ' '.join(pistas)


def realizar_enigma_numerico(texto: str, *, plano: Mapping[str, Any]) -> str | None:
    """Entrega somente a realização da solicitação atual, sem expor o código."""
    pedido = _pedido_vigente(texto, plano)
    return _realizar(pedido) if pedido is not None else None


def avaliar_enigma_numerico(
    texto: str, fala: str, *, plano: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Vincula a fala inteira às mesmas pistas cuja dedução foi conferida."""
    pedido = _pedido_vigente(texto, plano)
    if pedido is None:
        return None
    realizacao = _realizar(pedido)
    aceita = realizacao is not None and fala == realizacao
    problemas = [] if aceita else ['enigma_numerico_sem_solucao_verificada']
    return {
        'aceita': aceita,
        'requer_reparo': not aceita,
        'problemas': problemas,
        'problemas_bloqueantes': problemas,
        'somente_consultiva': False,
        'foco': {},
        'aderencia_contrato': {},
        'contrato_reparo': {},
        'autoriza_execucao': False,
    }
