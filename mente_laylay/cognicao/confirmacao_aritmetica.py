"""Confirmação breve de uma conclusão aritmética expressa no turno."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import (
    normalizar_texto_basico, pede_confirmacao_breve_ou_correcao,
)
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, intervalos_citados


_N = r'[0-9]{1,6}'
_EXPRESSAO = rf'{_N}(?:\s*[+\-−]\s*{_N}){{1,7}}'
_UNIDADE = r'[^\W\d_]+'
_CONTA = re.compile(
    r'(?:(?:[^:;.!?]{0,120}\b(?:questao|exercicio|problema) de matematica|'
    r'(?:e|era) (?:so|apenas) (?:um calculo|uma conta)(?:, [a-z]+)?):\s*)?'
    rf'(?P<expressao>{_EXPRESSAO})\s*=\s*(?P<total>{_N})\s+(?P<unidade>{_UNIDADE})'
    rf'(?:,\s*e\s+(?P<base>{_N})\s*(?P<operador>[+\-−])\s*(?P<parcela>{_N})'
    rf'\s*=\s*(?P<resto>{_N}))?[.!]',
)
_CONFIRMACAO = re.compile(
    rf'(?:voce concorda que|esta certo que|e correto dizer que) '
    rf'(?:restam|sobram|sobraram|ficaram) (?P<valor>{_N}) (?P<unidade>{_UNIDADE})\?',
)
_CONFIRMACAO_NUMERICA = re.compile(
    rf'(?:voce concorda com (?:a resposta|o resultado)|(?:a resposta|o resultado) (?:e|seria)) (?P<valor>{_N})\?',
)
_LIMITE_DISCURSIVO = re.compile(r'(?:sem (?:comando|acao) para executar|nao ha comandos? para executar)[.!]')
_ALINHAMENTO_NARRATIVO = re.compile(
    r'(?:(?:gostaria de|quero) (?:entender|saber|conferir) se )?estamos '
    r'(?:pensando na|falando da) mesma (?:historia|cena)[.!?]',
)


@dataclass(frozen=True, slots=True)
class ConfirmacaoAritmetica:
    turno_id: str
    texto_usuario: str
    valor: int
    unidade: str
    confirmada: bool
    alinhamento_narrativo: bool = False

    def resposta(self) -> str:
        if self.alinhamento_narrativo:
            polaridade = 'Sim' if self.confirmada else 'Não'
            return f'{polaridade}. Nesse trecho da nossa história, sobram {self.valor} {self.unidade}.'
        return 'Sim.' if self.confirmada else f'Não. Restam {self.valor} {self.unidade}.'

    def aceita(self, fala: str) -> bool:
        esperada = normalizar_texto_basico(self.resposta()).removesuffix('.')
        return normalizar_texto_basico(fala).removesuffix('.') == esperada

    def instrucao(self) -> str:
        return f'A conta foi conferida no turno. Entregue só esta confirmação ou correção breve: {self.resposta()}'


def construir_confirmacao_aritmetica(texto: str, *, plano: Mapping[str, Any]) -> ConfirmacaoAritmetica | None:
    from mente_laylay.personalidade.contingencias_conversa import resolver_aritmetica_simples

    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos') or plano.get('texto_operacional')):
        return None
    partes = enunciados_discursivos(texto)
    if len(partes) not in (3, 4):
        return None
    alinhamento = _ALINHAMENTO_NARRATIVO.fullmatch(normalizar_texto_basico(partes[-1])) is not None
    if len(partes) == 4 and not (alinhamento and _LIMITE_DISCURSIVO.fullmatch(normalizar_texto_basico(partes[1]))):
        return None
    if not alinhamento and not pede_confirmacao_breve_ou_correcao(partes[-1]):
        return None
    conta_bruta, pergunta_bruta = partes[0], partes[-2]
    if any(intervalos_citados(parte) for parte in (conta_bruta, pergunta_bruta)):
        return None
    # A normalização de linguagem pode converter ² em 2. A expressão
    # aritmética só admite os algarismos literais desta gramática.
    if any(c.isnumeric() and c not in '0123456789' for parte in (conta_bruta, pergunta_bruta) for c in parte):
        return None
    conta = _CONTA.fullmatch(normalizar_texto_basico(conta_bruta))
    pergunta_normalizada = normalizar_texto_basico(pergunta_bruta)
    pergunta = _CONFIRMACAO.fullmatch(pergunta_normalizada)
    if conta is None or (pergunta and conta['unidade'] != pergunta['unidade']):
        return None
    if pergunta is not None:
        unidade_literal = re.search(rf'(?P<unidade>{_UNIDADE})\?$', pergunta_bruta)
    else:
        expressao_bruta = conta_bruta.rpartition(':')[2]
        unidade_literal = re.search(rf'=\s*{_N}\s+(?P<unidade>{_UNIDADE})', expressao_bruta)
    if pergunta is None and alinhamento:
        pergunta = _CONFIRMACAO_NUMERICA.fullmatch(pergunta_normalizada)
    if pergunta is None or unidade_literal is None:
        return None
    termos = re.findall(r'[0-9]+|[+\-]', conta['expressao'].replace('−', '-'))
    valor = int(termos[0])
    for operador, parcela in zip(termos[1::2], termos[2::2]):
        valor = int(resolver_aritmetica_simples(f'{valor} {operador} {parcela}', exato=True))
    if valor != int(conta['total']):
        return None
    if conta['resto'] is not None:
        if int(conta['base']) != valor:
            return None
        operador = conta['operador'].replace('−', '-')
        valor = int(resolver_aritmetica_simples(f"{valor} {operador} {conta['parcela']}", exato=True))
        if valor != int(conta['resto']):
            return None
    return ConfirmacaoAritmetica(str(plano['id']), texto, valor, unidade_literal['unidade'],
                                 valor == int(pergunta['valor']), alinhamento)


def confirmacao_aritmetica_vigente(plano: Mapping[str, Any]) -> ConfirmacaoAritmetica | None:
    contrato = plano.get('contrato_fala') or {}
    confirmacao = contrato.get('confirmacao_aritmetica')
    if (type(confirmacao) is ConfirmacaoAritmetica and confirmacao.turno_id == str(plano.get('id'))
            and confirmacao.texto_usuario == plano.get('texto_usuario')
            and str(contrato.get('turno_id')) == confirmacao.turno_id and contrato.get('origem') == 'mente_unica'
            and contrato.get('autoriza_execucao') is False and plano.get('autoriza_execucao') is False
            and not plano.get('requer_execucao') and not plano.get('comandos') and not plano.get('texto_operacional')):
        return confirmacao
    return None


def realizar_confirmacao_aritmetica_composta(texto: str, *, plano: Mapping[str, Any]) -> str | None:
    """Realiza os dois atos quando ambos são verificáveis no próprio turno."""
    confirmacao = confirmacao_aritmetica_vigente(plano)
    if confirmacao and confirmacao.alinhamento_narrativo and confirmacao.texto_usuario == texto:
        return confirmacao.resposta()
    return None
