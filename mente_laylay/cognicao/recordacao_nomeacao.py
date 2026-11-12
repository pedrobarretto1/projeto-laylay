"""Escolhas nominais do enunciador: relação histórica, nunca receipt externo.

Extrai atos explícitos de escolha e sua referência local. Não deduz autoria
da invenção, consenso dos participantes nem existência do objeto escolhido.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Mapping

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos, intervalos_citados

_TIPO = r'(?:nome|apelido|t[ií]tulo)'
_OBJETO = r'(?P<objeto>[^:;.!?]+?)'


def _limpar(texto: str) -> str:
    return re.sub(r'^[^\w\'"«“]+', '', texto).strip()


def _objeto_nominal(texto: str) -> bool:
    from mente_laylay.cognicao.recordacao_atributo import _identidade
    from mente_laylay.cognicao.morfologia_oracao import consultar_morfologia

    # Empréstimos ainda ausentes do léxico podem preencher um único núcleo
    # nominal na matriz explícita. Nunca aceitar uma oração desconhecida.
    return bool(_identidade(texto) or (re.fullmatch(r'[^\W\d_]+', texto)
                                      and not consultar_morfologia(texto)))


def _consultas(texto: str) -> tuple[str, ...]:
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido
    from mente_laylay.cognicao.qualificacao_intencao import qualificar_intencao_por_capacidades
    from mente_laylay.cognicao.recordacao_atributo import _literal

    if intervalos_citados(texto):
        return ()
    partes = list(enunciados_discursivos(texto))
    quantidade = None
    if partes:
        qualificacao = qualificar_intencao_por_capacidades(partes[-1])
        if qualificacao is not None and all(c.unidade in {
            'nome', 'nomes', 'apelido', 'apelidos', 'título', 'títulos',
        } and not c.modificadores for c in qualificacao.candidatos):
            from mente_laylay.cognicao.gramatica_operacional import interpretar_inteiro_literal
            quantidades = {interpretar_inteiro_literal(c.quantidade) for c in qualificacao.candidatos}
            if len(quantidades) != 1 or None in quantidades:
                return ()
            quantidade = quantidades.pop()
            partes.pop()
    if not partes or any(not _preambulo_sem_outro_pedido(p) for p in partes[:-1]):
        return ()
    pergunta = _literal(_limpar(partes[-1]))
    pergunta = re.sub(r'^(?:agora )?(?:nosso |o |um )?teste de mem[oó]ria:\s*', '', pergunta)
    if not pergunta.endswith('?'):
        return ()
    objetos = []
    for parte in re.split(r'\s+e\s+(?=(?:que|qual)\s)', pergunta[:-1]):
        m = re.fullmatch(
            rf'(?:qual (?:foi|era) o {_TIPO} que (?:eu escolhi|escolhemos)|'
            rf'(?:que|qual) {_TIPO} (?:eu dei|eu escolhi|escolhemos)) '
            rf'(?:para [oa]|a[oa]|à) {_OBJETO}', parte)
        if m is None:
            return ()
        objeto = re.sub(r' (?:desta|dessa|nesta|nessa) (?:sess[aã]o|conversa)$', '', m['objeto'])
        if not _objeto_nominal(objeto):
            return ()
        objetos.append(objeto)
    if quantidade is not None and quantidade != len(objetos):
        return ()
    return tuple(objetos)


@dataclass(frozen=True, slots=True)
class EscolhaNominal:
    objeto: str
    nome: str
    indice: int
    sha256: str
    correcao: bool = False
    retirada: bool = False


def _escolhas(texto: str, indice: int) -> tuple[EscolhaNominal, ...]:
    from mente_laylay.cognicao.recordacao_atributo import _literal

    resultado = []
    antecedente = ''
    digest = hashlib.sha256(texto.encode('utf8')).hexdigest()
    for frase in enunciados_discursivos(texto):
        frase = _limpar(frase)
        aspas = intervalos_citados(frase)
        nome = frase[aspas[0][0] + 1:aspas[0][1] - 1] if len(aspas) == 1 else ''
        matriz = frase
        if nome:
            a, b = aspas[0]
            matriz = frase[:a] + 'NOME' + frase[b:]
        matriz = _literal(matriz)
        correcao = bool(re.match(r'^(?:corre[cç][aã]o|corrigindo):\s*', matriz))
        matriz = re.sub(r'^(?:corre[cç][aã]o|corrigindo):\s*', '', matriz)
        # A justificativa não é fonte do nome nem prova da sua causa.
        matriz = re.sub(r', (?:porque|pois) .*$', '', matriz)
        m = re.fullmatch(rf'(?:eu )?(?P<negacao>n[aã]o )?(?:escolho|escolhi) nome para [oa] {_OBJETO}[.!]?', matriz)
        retirada = bool(m and m['negacao'])
        if m is None:
            m = re.fullmatch(rf'(?:vamos fixar|fixo|fixei) (?:esse|este) como {_TIPO} d[oa] {_OBJETO}[.!]?', matriz)
            nome = antecedente if m else ''
        if m and nome and _objeto_nominal(m['objeto']) and len(nome) <= 120:
            resultado.append(EscolhaNominal(m['objeto'], nome, indice, digest, correcao, retirada))
        # Anáfora só da apresentação nominal imediatamente anterior, na mesma
        # mensagem. Citação reportada, pergunta e sugestão não são antecedente.
        antecedente = (frase[aspas[0][0] + 1:aspas[0][1] - 1]
                       if len(aspas) == 1 and re.fullmatch(
                           rf'nome [eé] um {_TIPO}(?: bom| bonito| interessante)?', matriz) else '')
    return tuple(resultado)


@dataclass(frozen=True, slots=True)
class RecordacaoNomeacao:
    turno_id: str
    texto_usuario: str
    objetos: tuple[str, ...]
    valores: tuple[str, ...]
    fontes: tuple[tuple[int, str, str], ...]

    @property
    def valor(self) -> str:
        return '; '.join(self.valores) if all(self.valores) else ''

    @property
    def estado(self) -> str:
        return 'nomes_conferidos' if self.valor else 'nome_nao_conferido'

    def resposta(self) -> str:
        if self.valor:
            return self.valor + '.'
        return ' '.join(v + '.' if v else f'Que nome você escolheu para o {o}?'
                        for o, v in zip(self.objetos, self.valores))

    def aceita(self, fala: str) -> bool:
        from mente_laylay.cognicao.recordacao_atributo import _literal
        return _literal(fala) == _literal(self.resposta())


def construir_recordacao_nomeacao(texto: str, *, plano: Mapping[str, Any],
                                  mente: Mapping[str, Any]) -> RecordacaoNomeacao | None:
    """Chamado pelo owner de recordação após validar turno e não operação."""
    objetos = _consultas(texto)
    if not objetos:
        return None
    from mente_laylay.cognicao.proveniencia_informacao import classificar_proveniencia_informacao

    bloqueadas = {normalizar_texto_basico(str(f.get('texto') or ''))
                  for f in plano.get('relatos_usuario') or () if isinstance(f, dict)
                  and classificar_proveniencia_informacao(f).get('bloqueada')}
    escolhas, fontes = [], []
    for i, mensagem in enumerate(mente.get('messages') or ()):
        if not isinstance(mensagem, dict) or mensagem.get('role') != 'user':
            continue
        original = mensagem.get('content')
        if not isinstance(original, str) or original == texto:
            continue
        relacoes = _escolhas(original, i)
        if not relacoes:
            continue
        fontes.append((i, relacoes[0].sha256, original))
        bloqueada = normalizar_texto_basico(original) in bloqueadas
        escolhas.extend((r, bloqueada) for r in relacoes)
    valores = []
    for objeto in objetos:
        # Uma referência qualificada pode retomar um objeto antes genérico,
        # somente se não houver outro objeto desse núcleo no histórico.
        candidatos = [(r, b) for r, b in escolhas if r.objeto.split()[0] == objeto.split()[0]]
        identidades = {r.objeto for r, _ in candidatos}
        candidatos = [(r, b) for r, b in candidatos if r.objeto == objeto or
                      (len(identidades) == 1 and r.objeto == objeto.split()[0])]
        nomes: set[str] = set()
        for r, bloqueada in candidatos:
            if bloqueada:
                nomes.add('')
                continue
            if r.retirada:
                nomes.discard(r.nome)
                continue
            if r.correcao:
                nomes.clear()
            nomes.add(r.nome)
        valores.append(next(iter(nomes)) if len(nomes) == 1 else '')
    return RecordacaoNomeacao(str(plano['id']), texto, objetos, tuple(valores), tuple(fontes))
