"""Quantidade de perguntas pedidas como entrega do turno conversacional."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import (
    enunciados_discursivos, intervalos_citados, texto_fora_de_citacoes,
)


DESCUMPRIDA = 'quantidade_perguntas_solicitada_descumprida'
DESTINATARIO_DIVERGENTE = 'destinatario_pergunta_divergente'
_QUANTIDADES = {'uma': 1, '1': 1, 'duas': 2, '2': 2, 'tres': 3, '3': 3}
_POR_EXTENSO = {1: 'uma', 2: 'duas', 3: 'três'}
_TOTAIS_ADMITIDOS = ((1,), (2,), (3,), (2, 3), (1, 2), (1, 2, 3))
_NUMERO_PLURAL = r'(?:duas|tres|[23])'
_INTERVALO_PLURAL = (
    rf'(?:{_NUMERO_PLURAL}\s+ou\s+{_NUMERO_PLURAL}'
    rf'|entre\s+{_NUMERO_PLURAL}\s+e\s+{_NUMERO_PLURAL}'
    rf'|de\s+{_NUMERO_PLURAL}\s+a\s+{_NUMERO_PLURAL})'
)
_QUANTIDADE_PLURAL = rf'(?:{_INTERVALO_PLURAL}|{_NUMERO_PLURAL})'
_NUMERO_LIMITE = rf'(?:uma|1|{_NUMERO_PLURAL})'
_LIMITE_SUPERIOR = rf'(?:ate|no maximo)\s+(?P<maximo>{_NUMERO_LIMITE})\s+perguntas?'
_LIMITE_INFERIOR = rf'(?:pelo menos|no minimo|ao menos)\s+(?P<minimo>{_NUMERO_LIMITE})\s+perguntas?'
_DIRETO = (
    r'(?:(?:voce|tu)\s+)?(?:(?:pode|poderia|consegue|conseguiria)\s+)?'
    r'(?:(?:me|nos)\s+)?(?:faca|faz|fazer|formule|formular|crie|criar|proponha|propor|elabore|elaborar|quero|gostaria de)'
    r'(?:(?:-|\s+)(?:me|nos))?\s+(?:(?:so|apenas|somente|exatamente)\s+)?'
    rf'(?:(?P<singular>uma|1)\s+(?:unica\s+)?pergunta|(?P<plural>{_QUANTIDADE_PLURAL})\s+perguntas'
    rf'|{_LIMITE_SUPERIOR}|{_LIMITE_INFERIOR})\b'
)
_FECHO = r'para (?:encerrar|fechar|concluir)(?: (?:nosso|nossa|este|esta|o|a) [\w ]{1,60})?,\s*'
_PREAMBULO = rf'(?:(?:agora|entao|depois|em seguida|por favor|para encerrar)(?:,\s*|\s+)|{_FECHO})*'
_PEDIDO = re.compile(
    rf'(?:^|[.!?;]\s*|(?P<apos_fecho>:)\s*|\be\s+)(?:e\s+)?{_PREAMBULO}(?:{_DIRETO}'
    rf'|(?:(?:qual|que)\s+pergunta|(?:quais|que)\s+(?P<proposta>{_QUANTIDADE_PLURAL})\s+perguntas)'
    r'\s+(?P<modificadores>(?:[a-z]+\s+){0,5}?)(?:(?:voce|tu)\s+)?'
    r'(?:faria|farias|formularia|proporia|gostaria de (?:fazer|formular|propor))\b)'
)
_COMPLEMENTO = (
    r'(?:\s+(?:so|inesperada|engracada|curta|simples|criativa|diferente))?'
    r'(?:\s+(?:sobre|para|ao)\s+(?:(?!(?:e|mas|porque|que|quando|depois)\b)[\w-]+\s*){1,6})?'
    r'(?:,?\s+por favor)?'
)
_PEDIDO_INTEGRAL = re.compile(
    rf'{_PREAMBULO}(?:(?:escolha|sugira|puxe|traga)\s+(?:um|outro)\s+(?:assunto|tema)'
    rf'(?:\s+(?:novo|diferente))?\s+e\s+)?{_DIRETO}{_COMPLEMENTO}[.!?]*'
)
_FRAGMENTO_QUANTIDADE = re.compile(
    rf'{_PREAMBULO}(?:(?P<intervalo>{_INTERVALO_PLURAL})\s+perguntas|{_LIMITE_SUPERIOR}|{_LIMITE_INFERIOR})'
    rf'{_COMPLEMENTO}[.!]*'
)
_ADICAO_PEDIDA = re.compile(
    r'\b(?:e|mais|depois|tambem),?\s+(?:(?:me\s+)?(?:faca|faz|fazer|formule|proponha|mande)\s+)?'
    r'(?:outra|uma outra|mais uma|duas|tres|varias)\b'
)
_SUFIXO_OPCIONAL = re.compile(
    r'[^.!?;]*\bse\s+(?:precisar|quiser|fizer sentido|(?:for )?necessario)\s*(?:[.!?;]|$)'
)
_TROCA_PERGUNTA_LIVRE = re.compile(
    r'(?:vamos trocar de pap(?:el|eis)|(?:agora )?e (?:a )?sua vez)[:,]\s*'
    r'(?:agora\s+)?(?:voce (?:e quem|que) )?(?:me|nos) (?:faca|faz|fara) '
    r'uma pergunta(?: (?:divertida|engracada|inesperada|criativa))? '
    r'sobre (?:qualquer assunto|o que quiser|um assunto de sua escolha)[.!]*'
)
_LIMITE_DA_TROCA = re.compile(
    r'(?:so uma pergunta|uma pergunta so)(?:, nao precisa (?:de fontes(?: nem de executar acoes)?'
    r'|executar acoes))?[.!]*'
)
_REACAO_A_CITACAO = re.compile(r'\[citacao\] e (?:um|uma) [a-z]+(?: [a-z]+){0,3}(?:, lay(?:lay)?)?[.!]+')
_ITEM_LISTA = r'(?:[-*•]|\d+[.)])'
_PROPOSTA_CITADA = re.compile(
    r'(?:^|[.!?;]\s*)(?:e\s+)?'
    r'(?:(?:(?:a|minha|uma)\s+)?pergunta(?:\s+que\s+(?:eu\s+)?(?:faria|proporia|formularia)\b[^.!?;:]*)?'
    r'|(?:(?:as|minhas|duas|tres)\s+)*perguntas(?:\s+(?:para|a|ao|aos)\s+[^.!?;:]+)?'
    r'|(?:eu\s+)?perguntaria(?:\s+[^.!?;:]+)?'
    rf'|(?:ao|aos|para)\s+[^.!?;:]+):\s*(?:{_ITEM_LISTA}\s*)?$'
)
_INTERROGACAO = re.compile(r'\?+')
_SEPARADOR_PROPOSTAS = re.compile(rf'(?:[,.;&]\s*)?(?:e\b\s*)?(?:{_ITEM_LISTA}\s*)?')
_INICIO_INTERROGATIVO = r'(?:e\s+)?(?:como|onde|quando|quem|qual|quais|quanto|por que|o que|que)\s+'
_PERGUNTA_ISOLADA = re.compile(_INICIO_INTERROGATIVO + r'[^?]+[!?]*\?+[!?]*')


def _perguntas(fala: str) -> tuple[tuple[int, int], ...]:
    """Delimita perguntas emitidas e propostas, separando citações narradas."""
    spans = []
    cursor = 0
    proposta_anterior = False
    for inicio, fim in intervalos_citados(fala):
        spans.extend(m.span() for m in _INTERROGACAO.finditer(fala, cursor, inicio))
        moldura = normalizar_texto_basico(fala[cursor:inicio])
        depois = normalizar_texto_basico(fala[fim:].lstrip(' .!?'))
        citacao_direta = inicio == 0 and (not depois or re.match(_INICIO_INTERROGATIVO, depois))
        proposta = bool(_PROPOSTA_CITADA.search(moldura)
                       or (proposta_anterior and _SEPARADOR_PROPOSTAS.fullmatch(moldura)))
        perguntas = list(_INTERROGACAO.finditer(fala, inicio + 1, fim - 1)) if proposta or citacao_direta else []
        spans.extend((m.start(), fim) for m in perguntas)
        proposta_anterior = proposta and bool(perguntas)
        cursor = fim
    spans.extend(m.span() for m in _INTERROGACAO.finditer(fala, cursor))
    return tuple(spans)


def _troca_para_pergunta_livre(texto: str) -> bool:
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido

    partes = [normalizar_texto_basico(re.sub(r'^[^\w\[]+', '', p)) for p in enunciados_discursivos(texto)]
    if partes and _LIMITE_DA_TROCA.fullmatch(partes[-1]):
        partes.pop()
    return bool(partes and _TROCA_PERGUNTA_LIVRE.fullmatch(partes[-1]) and all(
        _REACAO_A_CITACAO.fullmatch(p) or _preambulo_sem_outro_pedido(p) for p in partes[:-1]
    ))


def _destinatario_do_complemento(texto: str) -> str:
    # Complemento do ato pedido, nunca nomes encontrados em exemplos citados.
    texto = re.split(r'[.!?;]', texto, maxsplit=1)[0]
    texto = re.sub(r'^\s*que (?:voce|tu) (?:faria|formularia|proporia)\s+(?:diretamente\s+)?', ' ', texto)
    m = re.fullmatch(r'\s*(?:para (?:o |a )?|ao |a |à )([a-z]+(?: [a-z]+)?)'
                     r'(?: sobre [^.!?;]+)?[.!?]*', texto)
    return m[1] if m else ''


def _destinatario_continuado(base: str) -> str:
    base = re.sub(r'(por exemplo: \[citacao\])\s+(?=agora\b)', r'\1. ', base)
    partes = [re.sub(r'^[^\w\[]+', '', p) for p in enunciados_discursivos(base)]
    continuacao = re.fullmatch(
        r'(?:agora )?(?:invente|crie|formule|elabore) outra pergunta(?: curta| simples)?'
        r'(?: sua)?(?:, como (?P<papel>[^.!?]+))?[.!]*', partes[-1]) if partes else None
    if continuacao is None:
        return ''
    if continuacao['papel']:
        from mente_laylay.cognicao.recordacao_atributo import _identidade
        if not _identidade(continuacao['papel']):
            return ''
    destinos = []
    for parte in partes[:-1]:
        m = re.fullmatch(r'e (?:so|apenas) uma pergunta que voce '
                         r'(?:inventaria|criaria|formularia|faria)(.+)', parte)
        if m:
            destino = _destinatario_do_complemento(m[1])
            if not destino:
                return ''
            destinos.append(destino)
        elif not (re.fullmatch(r'por exemplo: \[citacao\][.!]*', parte)
                  or re.fullmatch(r'nao precisa verificar nada(?:, [a-z]+)?[.!]*', parte)):
            return ''
    return destinos[0] if len(destinos) == 1 else ''


def _destinatario_preservado(fala: str, destinatario: str) -> bool:
    if not destinatario:
        return True
    base = normalizar_texto_basico(fala)
    # O vocativo fixa a segunda pessoa. Menção do destinatário na terceira
    # pessoa não satisfaz o vínculo, mesmo que haja um "você" na pergunta.
    for trecho in enunciados_discursivos(base):
        if '?' not in trecho:
            continue
        corpo = trecho.strip(' «»\"\'')
        corpo = re.sub(r'^(?:\d+[.)]|[-*])\s*', '', corpo)
        moldura = re.match(r'^(?:minhas perguntas para (?:a |o )?|perguntaria (?:a |ao ))'
                           + re.escape(destinatario) + r':\s*', corpo)
        if moldura:
            corpo = corpo[moldura.end():].lstrip(' «»\"\'')
        vocativo = re.match(r'^([a-z]+(?: [a-z]+)?),\s*', corpo)
        if vocativo:
            if vocativo[1] != destinatario:
                return False
            corpo = corpo[vocativo.end():]
        if re.search(r'\b' + re.escape(destinatario) + r'\b', corpo):
            return False
        if not re.search(r'\b(?:voce|tu|seu|sua|teu|tua)\b', corpo):
            return False
    return True


@dataclass(frozen=True, slots=True)
class PerguntaSolicitada:
    turno_id: str
    texto_usuario: str
    quantidades: tuple[int, ...]
    cobre_turno_integral: bool
    minimo: int | None = None
    destinatario: str = ''

    def instrucao(self) -> str:
        if self.minimo is not None or len(self.quantidades) == 1:
            total = self.minimo if self.minimo is not None else self.quantidades[0]
            criterio = 'pelo menos' if self.minimo is not None else 'exatamente'
            nome = 'pergunta' if total == 1 else 'perguntas'
            quantidade = f'{criterio} {_POR_EXTENSO[total]} {nome}'
        elif self.quantidades[0] == 1:
            quantidade = f'até {_POR_EXTENSO[self.quantidades[-1]]} perguntas (pelo menos uma)'
        else:
            quantidade = ' ou '.join(_POR_EXTENSO[n] for n in self.quantidades) + ' perguntas'
        destino = (f'Dirija a pergunta a {self.destinatario}, em segunda pessoa; '
                   'não pergunte ao interlocutor o que essa pessoa faria. ') if self.destinatario else ''
        return (f'Entregue {quantidade}, para o destinatário indicado. ' + destino +
                'Responda também os outros pedidos do turno. Evite perguntas de acompanhamento.')

    def aceita(self, fala: str) -> bool:
        return not self.problema(fala)

    def problema(self, fala: str) -> str:
        total = len(_perguntas(fala))
        quantidade_ok = total >= self.minimo if self.minimo is not None else total in self.quantidades
        if not quantidade_ok:
            return DESCUMPRIDA
        return '' if _destinatario_preservado(fala, self.destinatario) else DESTINATARIO_DIVERGENTE

    def recorte(self, fala: str) -> str:
        """Retém a proposta demarcada se todo o excedente é um sufixo interrogativo."""
        # O prefixo separável só identifica a proposta única. Em uma lista,
        # remover um item sem saber se ele é obrigatório pode mudar a entrega.
        if self.quantidades != (1,):
            return ''
        perguntas = _perguntas(fala)
        if len(perguntas) < 2:
            return ''
        sinal, fim = perguntas[0]
        if not any(inicio < sinal < fim_citado == fim for inicio, fim_citado in intervalos_citados(fala)):
            return ''
        restantes = enunciados_discursivos(fala[fim:])
        if (len(restantes) != len(perguntas) - 1
                or not all(_PERGUNTA_ISOLADA.fullmatch(normalizar_texto_basico(t)) for t in restantes)):
            return ''
        return fala[:fim]


def construir_pergunta_solicitada(texto: str, *, plano: Mapping[str, Any]) -> PerguntaSolicitada | None:
    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    base = normalizar_texto_basico(texto_fora_de_citacoes(texto))
    continuacao = _destinatario_continuado(base)
    if continuacao:
        return PerguntaSolicitada(str(plano['id']), texto, (1,), False, destinatario=continuacao)
    if _troca_para_pergunta_livre(base):
        return PerguntaSolicitada(str(plano['id']), texto, (1,), True)
    fragmento = _FRAGMENTO_QUANTIDADE.fullmatch(base)
    if fragmento is not None:
        pedido = fragmento
        expressao = fragmento['intervalo']
        integral = True
    else:
        pedidos = list(_PEDIDO.finditer(base))
        if len(pedidos) != 1 or _ADICAO_PEDIDA.search(base, pedidos[0].end()):
            return None
        pedido = pedidos[0]
        if pedido['apos_fecho']:
            # Dois-pontos só introduzem este pedido quando pertencem a uma
            # intenção atual de encerrar; relato de terceiro não é solicitação.
            prefixo = base[:pedido.start()]
            fecho = re.search(r'\b(?:quero|gostaria de)\s+(?:fechar|encerrar|concluir)\b[^.!?;:]*$', prefixo)
            if fecho is None or re.search(r'\b(?:nao|nunca|jamais)\s*$', prefixo[:fecho.start()]):
                return None
        modificadores = (pedido['modificadores'] or '').split()
        if modificadores:
            from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia
            if (modificadores[0] == 'e' or modificadores[-1] == 'e'
                    or any(p != 'e' and not (consultar_morfologia(p) or 0) & 2 for p in modificadores)
                    or any(a == b == 'e' for a, b in zip(modificadores, modificadores[1:]))):
                return None
        expressao = pedido['singular'] or pedido['plural'] or pedido['proposta'] or 'uma'
        integral = bool(_PEDIDO_INTEGRAL.fullmatch(base))
    maximo = _QUANTIDADES.get(pedido['maximo'] or '')
    minimo = _QUANTIDADES.get(pedido['minimo'] or '')
    if (minimo is not None or maximo is not None) and _SUFIXO_OPCIONAL.match(base, pedido.end()):
        return None
    if minimo is not None:
        quantidades = ()
    elif maximo is not None:
        quantidades = tuple(range(1, maximo + 1))
    else:
        quantidades = tuple(sorted({_QUANTIDADES[p] for p in expressao.split() if p in _QUANTIDADES}))
    return PerguntaSolicitada(str(plano['id']), texto, quantidades, integral, minimo=minimo,
                             destinatario=_destinatario_do_complemento(base[pedido.end():]))


def pergunta_solicitada_vigente(plano: Mapping[str, Any]) -> PerguntaSolicitada | None:
    contrato = plano.get('contrato_fala') or {}
    pedido = contrato.get('pergunta_solicitada')
    if (type(pedido) is PerguntaSolicitada and pedido.turno_id == str(plano.get('id'))
            and pedido.texto_usuario == plano.get('texto_usuario')
            and (pedido.quantidades in _TOTAIS_ADMITIDOS if pedido.minimo is None
                 else pedido.minimo in _POR_EXTENSO and pedido.quantidades == ())
            and str(contrato.get('turno_id')) == pedido.turno_id and contrato.get('origem') == 'mente_unica'
            and contrato.get('autoriza_execucao') is False and plano.get('autoriza_execucao') is False
            and not plano.get('requer_execucao') and not plano.get('comandos')):
        return pedido
    return None


def pedido_integral_de_pergunta(
    texto: str, *, contrato: Mapping[str, Any], turno_id: Any,
) -> bool:
    """Só o pedido integral deixa de ser candidato a relato informativo."""
    pedido = contrato.get('pergunta_solicitada')
    return bool(type(pedido) is PerguntaSolicitada and pedido.cobre_turno_integral
                and pedido.texto_usuario == texto and pedido.turno_id == str(turno_id)
                and contrato.get('origem') == 'mente_unica'
                and str(contrato.get('turno_id')) == pedido.turno_id
                and contrato.get('autoriza_execucao') is False)
