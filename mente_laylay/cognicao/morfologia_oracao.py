"""Evidência morfológica local para conservar oração, nunca para autorizar.

Léxico não prova sentido. O leitor raso exige grupo nominal + indicativo
finito, sem tomar um grupo nominal completo por oração. Não é parser geral.
"""
from __future__ import annotations

import base64
from functools import lru_cache
import hashlib
import re
import zlib

from mente_laylay.cognicao.lexico_morfologico_dados import DADOS_BASE85, SHA256_DADOS
from mente_laylay.cognicao.referencias_linguagem import texto_fora_de_citacoes

_NOME, _ADJETIVO = 1, 2
_ADVERBIO, _INDICATIVO_3S = 64, 256
_ARTIGOS = {'o':1,'a':2,'os':4,'as':8,'um':1,'uma':2,'uns':4,'umas':8}
_TERCEIRA_PESSOA = frozenset({'ele','ela','eles','elas','isso','isto','aquilo','alguém','ninguém'})
_PESSOA_DIRETA = frozenset({'eu','tu','nós','nos','vós','voce','você','vocês'})


def _tokens(texto: str) -> list[str]:
    # O marcador canônico é opaco: não é apagado nem lido como uma palavra.
    return re.findall(r'\[citacao\]|[^\W\d_]+',texto_fora_de_citacoes(texto).casefold())


@lru_cache(maxsize=1)
def _indice() -> bytes | None:
    """Não materializa um dict de 862 mil formas em cada processo."""
    try:
        dados = zlib.decompress(base64.b85decode(DADOS_BASE85))
        return dados if hashlib.sha256(dados).hexdigest()==SHA256_DADOS else None
    except (ValueError,zlib.error):
        return None


@lru_cache(maxsize=4096)
def consultar_morfologia(palavra: str) -> int | None:
    """Bits lexicais documentados no gerador; None é índice indisponível."""
    dados = _indice()
    if dados is None:return None
    chave = palavra.casefold().encode('utf8')
    inicio,fim = 0,len(dados)
    while inicio < fim:
        meio = (inicio+fim)//2
        a = max(inicio,dados.rfind(b'\n',inicio,meio)+1)
        b = dados.find(b'\n',meio)
        if b < 0:b = len(dados)
        nome,valor = dados[a:b].split(b'\t')
        if nome==chave:return int(valor)
        if nome < chave:inicio = b+1
        else:fim = a
    return 0


def _grupo_nominal(palavras: list[str], tipos: list[int]) -> bool:
    if not palavras or len(palavras)>8:return False
    if palavras[0] in _PESSOA_DIRETA:return False
    if len(palavras)==1 and palavras[0] in _TERCEIRA_PESSOA:return True
    concordancia = _ARTIGOS.get(palavras[0],15)
    inicio = int(palavras[0] in _ARTIGOS)
    for cabeca in range(inicio,len(palavras)):
        tipo = tipos[cabeca]
        # Palavra ausente pode ser nome próprio somente num grupo unitário.
        # Adjetivo conhecido não vira nome por capitalização.
        nome_proprio = tipo==0 and len(palavras)==1
        if not tipo&_NOME and not nome_proprio:continue
        compativeis = concordancia & (((tipo>>9)&15) or 15)
        for i in range(inicio,len(palavras)):
            if i==cabeca:continue
            if not tipos[i]&_ADJETIVO:
                compativeis = 0;break
            compativeis &= ((tipos[i]>>13)&15) or 15
        if compativeis:return True
    return False


def continuacao_predicativa_possivel(esquerda: str, direita: str) -> bool | None:
    """Não decide domínio, interlocutor, alvo, autorização ou efeito.

    None é recurso indisponível, não evidência de ordem independente.
    """
    direita_tokens = _tokens(direita)
    if not direita_tokens:return False
    direita_tipo = consultar_morfologia(direita_tokens[0])
    if direita_tipo is None:return None
    if not direita_tipo&_INDICATIVO_3S:return False
    palavras = _tokens(esquerda)
    if not palavras or len(palavras)>256:return False
    # Em contraste com predicado repetido e sujeito elidido, a vírgula não
    # prova nova ordem: "não muda X, muda Y" também é uma declaração. A
    # forma indicativa vem do léxico; cortesia ou forma formal na direita
    # não entram neste recorte. O chamador conserva a proibição do conjunto.
    if (len(palavras)>1 and palavras[0] in {'não','nao'}
        and palavras[1]==direita_tokens[0]):
        return True
    tipos = [128 if p=='[citacao]' else consultar_morfologia(p) or 0 for p in palavras]
    # Avaliação nominal inteira não é evidência de um predicado finito.
    if _grupo_nominal(palavras,tipos):return False
    for i,tipo in enumerate(tipos):
        if i==0 or not tipo&_INDICATIVO_3S:continue
        fim_sujeito = i
        while fim_sujeito and palavras[fim_sujeito-1] in {'se','me','te','nos','vos','lhe','lhes','não','nao'}:
            fim_sujeito -= 1
        inicios = [0]
        for j in range(fim_sujeito):
            if tipos[j]&_ADVERBIO:inicios.append(j+1)
            else:break
        if any(_grupo_nominal(palavras[j:fim_sujeito],tipos[j:fim_sujeito]) for j in inicios):
            return True
    return False
