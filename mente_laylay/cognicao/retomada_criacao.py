"""Retoma uma criação publicada em um recorte de autoria e condição explícitas."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, TYPE_CHECKING

from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto_basico
from mente_laylay.cognicao.referencias_linguagem import (
    enunciados_discursivos, intervalos_citados, texto_fora_de_citacoes,
)

if TYPE_CHECKING:
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta


ABERTURA_RETOMADA_CRIACAO = re.compile(
    r"(?:(?:e|ent[aã]o)\s+)?(?P<transicao>agora),?\s+"
    r"(?:eu\s+)?(?:quero|queria|gostaria\s+de)\s+[^:;.!?]+:\s*",
    re.I,
)
MATRIZ_RETOMADA_CRIACAO = re.compile(
    r"(?:qual|quais|que|o que)\s+(?:era|eram|foi|foram)\s+(?P<objeto>[^:;.!?]+?)"
    r"\s+que\s+(?:voc[eê]|tu)\s+(?:inventou|criou|imaginou|descreveu|escreveu|contou|prop[oô]s)\b"
    r"(?P<destino>[^:;.!?]*)\?",
    re.I,
)
_REACAO = re.compile(r'(?:acertou|boa|certo|[oó]timo|perfeito|isso)[.!]+', re.I)
_FORMA = re.compile(r'(?:conte|diga|explique|responda) com suas palavras[.!]*', re.I)
_DEFINICAO = re.compile(
    r'\bque eu (?:imagino|imaginei|invento|inventei|crio|criei|descrevi|escrevi|propus) '
    r'[ée] (?P<artigo>um|uma) (?P<nome>[^,.!?;:«»"\n]+?)(?=\s+que\b|[.!?]|$)',
    re.I,
)
_COORDENACAO_DA_REGRA = re.compile(r'\b(?:e|ou|mas|por[eé]m|enquanto|ent[aã]o)\b', re.I)
_LIMITE = 'Não lembro dessa versão com segurança. Você lembra de algum detalhe da cena?'


@dataclass(frozen=True, slots=True)
class RetomadaCriacao:
    turno_id: str
    texto_usuario: str
    ancora: tuple[str, ...]
    pede_regra: bool
    fonte: ReferenciaFalaConsulta | None
    alternativas: tuple[ReferenciaFalaConsulta, ...] = ()
    objeto_nomeado: str = ''
    escolha_inicial: str = ''


def recorte_escolha_inicial(texto: str) -> str:
    """Retoma a proposta inicial para um tema explícito, sem validar sua categoria."""
    from mente_laylay.cognicao.fundamentacao_factual import _preambulo_sem_outro_pedido
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel
    if intervalos_citados(texto):
        return ''
    partes = list(enunciados_discursivos(texto))
    if not partes or not re.fullmatch(
        r'(?:quero )?(?:s[oó]|apenas|somente) o nome(?:, sem (?:nenhum comando|explicar))?[.!]*',
        partes[-1], re.I):
        return ''
    partes.pop()
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    if not partes or any(not _preambulo_sem_outro_pedido(p) and (
        '?' in p or classificar_modalidade_turno(p).get('modalidade') not in {'conversa', 'reacao'}
        or classificar_modalidade_turno(p).get('autoriza_execucao')) for p in partes[:-1]):
        return ''
    m = re.fullmatch(
        r'(?:(?:agora )?(?:desafio|teste) de mem[oó]ria:\s*)?'
        r'no (?:come[cç]o|in[ií]cio) d(?:esta|essa) (?:sess[aã]o|conversa),\s*'
        r'qual foi [oa] (?P<categoria>[^:;.!?]+?) que (?:voc[eê]|tu) '
        r'(?:inventou|criou|prop[oô]s) para [oa] (?P<tema>[^:;.!?]+)\?',
        re.sub(r'^[^\w]+', '', partes[-1]), re.I)
    if not m or not grupo_nominal_de_papel(m['categoria']):
        return ''
    grupos = re.split(r'\s+d(?:e|o|a|os|as)\s+', m['tema'])
    return normalizar_texto_basico(m['tema']) if all(grupo_nominal_de_papel(g) for g in grupos) else ''


def _nome_escolha_inicial(fala: str, tema: str) -> str:
    """Só a proposta nominal publicada após a retomada explícita do tema.

    O modo condicional pertence à escolha fictícia registrada. Isso não prova
    criação ou execução externa, nem certifica a categoria proposta na consulta.
    """
    partes = enunciados_discursivos(fala)
    if len(partes) < 2:
        return ''
    topico = normalizar_texto_basico(partes[0]).strip(' ?!.,')
    topico = re.sub(r'^(?:ah,? )?[oa] ', '', topico)
    if not (topico == tema or topico.startswith(tema + ' de ')):
        return ''
    trecho = partes[1]
    aspas = intervalos_citados(trecho)
    if not aspas:
        return ''
    inicio, fim = aspas[0]
    if not re.fullmatch(r'(?:eu )?(?:escolheria|proporia|sugeriria) [oa] ', trecho[:inicio], re.I):
        return ''
    # A continuação deve explicar uma escolha única, não oferecer alternativas.
    if not re.match(r'^\s*(?:[.!?]|$|[—–:]\s)', trecho[fim:]):
        return ''
    nome = trecho[inicio+1:fim-1]
    return nome if re.fullmatch(r'[\w -]{1,100}', nome) else ''


def recorte_nome_publicado(texto: str) -> str:
    """Consulta integral ao nome autorado no diálogo, sem qualificar efeitos.

    A matriz de lembrança e a interrogativa direta têm o mesmo complemento:
    nome/título/apelido criado pela destinatária para um grupo nominal.
    Outros atos, autores ou consultas sobre o mundo não cabem neste recorte.
    """
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    if intervalos_citados(texto):
        return ''
    partes = enunciados_discursivos(texto)
    if partes and re.fullmatch(r'(?:só|so|somente|apenas) o (?:nome|apelido|título|titulo)'
                              r'(?:,? sem explicar)?[.!]*', partes[-1], re.I):
        partes = partes[:-1]
    if len(partes) != 1:
        return ''
    consulta = re.fullmatch(
        r'(?:mudando (?:um pouco|de assunto):\s*)?'
        r'(?:(?:voc[eê] )?(?:ainda )?(?:se )?(?:lembra|recorda) do|qual (?:era|foi) o) '
        r'(?:nome|apelido|t[ií]tulo) que (?:(?:voc[eê]|tu) )?(?:inventou|criou|escolheu|deu) '
        r'para (?:o|a) (?P<objeto>[^:;.!?]+?) (?:nesta|nessa) (?:conversa|sess[aã]o)\?',
        partes[0], re.I)
    if consulta is None:
        return ''
    objeto = consulta['objeto'].casefold()
    grupos = re.split(r'\s+com\s+', objeto)
    if len(grupos) > 2 or not all(grupo_nominal_de_papel(g) for g in grupos):
        return ''
    return normalizar_texto_basico(objeto)


def _nome_publicado(fala: str, objeto: str, *, conferir_qualificador: bool = True) -> str:
    """Extrai só a nomeação assertiva; o restante não vira prova de causa.

    Um qualificador atual pode referir o único objeto antes não qualificado.
    Nunca se apaga qualificador de uma fonte para unificar objetos distintos.
    A unicidade entre publicações é conferida pelo seletor abaixo.
    """
    nomes = []
    for trecho in enunciados_discursivos(fala):
        citacoes = intervalos_citados(trecho)
        if not citacoes:
            continue
        inicio, fim = citacoes[0]
        matriz = normalizar_texto_basico(trecho[:inicio]).rstrip(': ')
        m = re.fullmatch(r'(?:o|a) (.+?) (?:se chama|se chamava|vai se chamar)', matriz)
        if m is None:
            continue
        if conferir_qualificador and m[1] not in {objeto, objeto.partition(' com ')[0]}:
            continue
        if not conferir_qualificador and m[1].split()[0] != objeto.split()[0]:
            continue
        nome = trecho[inicio + 1:fim - 1].strip()
        cauda = trecho[fim:].strip()
        if cauda and not re.match(r'^(?:[.!]$|,\s*(?:porque|pois)\s)', cauda, re.I):
            continue
        if re.fullmatch(r'[\w -]{1,80}', nome):
            nomes.append(nome)
    return nomes[0] if len(nomes) == 1 else ''


@dataclass(frozen=True, slots=True)
class _ConteudoCriacao:
    definicao: str
    pronome: str
    regra: str

    def realizar(self, *, pede_regra: bool) -> tuple[str, str]:
        identidade = f'Era {self.definicao}.'
        if not pede_regra:
            return identidade, 'criacao_publicada'
        if not self.regra:
            return f'{identidade} Não lembro com segurança como {self.pronome} funcionava.', 'identidade_sem_regra'
        if _COORDENACAO_DA_REGRA.search(self.regra):
            return f'{identidade} Naquela versão, eu descrevi assim: «{self.regra}».', 'criacao_publicada'
        # Só se retoma o sujeito já identificado. O predicado, o modalizador
        # e a condição ficam integrais, incluindo polaridade e tempo verbal.
        predicado = self.regra.split(' ', 2)[2]
        return f'{identidade} Naquela versão, {self.pronome} {predicado}.', 'criacao_publicada'


def _recorte_da_consulta(texto: str) -> tuple[tuple[str, ...], bool] | None:
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    if intervalos_citados(texto):
        return None
    partes = list(enunciados_discursivos(texto))
    if partes and _REACAO.fullmatch(partes[0]):
        partes.pop(0)
    if partes and _FORMA.fullmatch(partes[-1]):
        partes.pop()
    if not 1 <= len(partes) <= 2:
        return None
    consulta = MATRIZ_RETOMADA_CRIACAO.fullmatch(ABERTURA_RETOMADA_CRIACAO.sub('', partes[0], count=1))
    if consulta is None:
        return None
    objeto = normalizar_texto_basico(consulta['objeto'])
    nucleo = re.fullmatch(r'(?:o|a|um|uma) ([a-z]+)(?: [a-z]+)*', objeto)
    alvo = re.fullmatch(r'\s+para\s+(?:o|a)\s+(.+)', consulta['destino'])
    if not nucleo or not alvo or not grupo_nominal_de_papel(alvo[1]):
        return None
    ancora = tuple(re.split(r'\s+d(?:o|a)\s+', normalizar_texto_basico(alvo[1]), maxsplit=1))
    if not all(termo and len(termo) >= 3 for termo in ancora):
        return None
    if len(partes) == 2:
        referencia = rf'(?:esse|essa|este|esta|o|a) {re.escape(nucleo[1])}'
        pergunta = rf'(?:e )?(?:o que fazia {referencia} funcionar|como {referencia} funcionava)\?'
        if not re.fullmatch(pergunta, normalizar_texto_basico(partes[1])):
            return None
    return ancora, len(partes) == 2


def _extrair_conteudo(fala: str, *, ancora: tuple[str, ...]) -> _ConteudoCriacao | None:
    from mente_laylay.cognicao.morfologia_oracao import grupo_nominal_de_papel

    def menciona(texto: str, termo: str) -> bool:
        return bool(re.search(rf'\b{re.escape(termo)}\b', normalizar_texto_basico(texto)))

    externo = texto_fora_de_citacoes(fala)
    if not all(menciona(externo, termo) for termo in ancora):
        return None
    partes = enunciados_discursivos(fala)
    # O local precisa estar na mesma declaração que introduz o objeto.
    # O nome do cenário pode aparecer em outra frase, desde que na mesma fala.
    definicoes = [(i, d) for i, trecho in enumerate(partes) if not intervalos_citados(trecho)
                  and not trecho.endswith('?') and menciona(trecho, ancora[0])
                  for d in _DEFINICAO.finditer(trecho)]
    if len(definicoes) != 1:
        return None
    indice, definicao = definicoes[0]
    prefixo = normalizar_texto_basico(partes[indice][:definicao.start()])
    if re.search(r'\b(?:nao|nunca|talvez|supostamente)\b', prefixo):
        return None
    if len(ancora) == 2:
        local, cenario = map(re.escape, ancora)
        if re.search(rf'\b{local}\s+d[oa]\s+(?!{cenario}\b)', prefixo):
            return None
    nome = definicao['nome']
    if not grupo_nominal_de_papel(nome):
        return None
    indefinido = definicao['artigo'].lower()
    artigo, pronome = ('o', 'ele') if indefinido == 'um' else ('a', 'ela')
    entidade = re.escape(nome.split()[0])
    padrao = re.compile(
        rf'(?:^|,\s*e\s+)(?P<regra>{artigo} {entidade} (?:s[oó]|somente|apenas) '
        r'[^.!?;:,«»"“”()\[\]{}—–]+? (?:se|quando) [^.!?;:,«»"“”()\[\]{}—–]+)\.$', re.I,
    )
    regras = {m['regra'] for trecho in partes[indice + 1:] if not intervalos_citados(trecho)
              for m in padrao.finditer(trecho)}
    regra = next(iter(regras)) if len(regras) == 1 else ''
    return _ConteudoCriacao(f'{indefinido} {nome}', pronome, regra)


def construir_retomada_criacao(texto: str, *, plano: Mapping[str, Any],
                              mente: Mapping[str, Any]) -> RetomadaCriacao | None:
    from mente_laylay.cognicao.fundamentacao_factual import classificar_atualidade_factual
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta, selecionar_fala_observada, selecionar_primeira_fala_textual

    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos')):
        return None
    escolha_inicial = recorte_escolha_inicial(texto)
    if escolha_inicial:
        registro = mente.get('registro_semantico') or {}
        observada = selecionar_primeira_fala_textual(registro) if isinstance(registro, Mapping) else {}
        fonte = None
        if observada and not observada.get('resultados') and observada['turno_id'] != str(plano['id']):
            fonte = ReferenciaFalaConsulta(str(plano['id']), texto, observada['id'], observada['turno_id'],
                                          observada['fala'], observada['ts'])
        return RetomadaCriacao(str(plano['id']), texto, (), False, fonte, escolha_inicial=escolha_inicial)
    objeto_nomeado = recorte_nome_publicado(texto)
    if objeto_nomeado:
        turno_id = str(plano['id'])
        registro = mente.get('registro_semantico') or {}
        candidatas = []
        for item in registro.get('falas_observadas', ()) if isinstance(registro, Mapping) else ():
            if not isinstance(item, Mapping) or not isinstance(item.get('id'), str):
                continue
            observada = selecionar_fala_observada(registro, ocorrencia_id=item['id'])
            if (not observada or observada.get('resultados') or observada['turno_id'] == turno_id
                    or not _nome_publicado(observada['fala'], objeto_nomeado, conferir_qualificador=False)):
                continue
            candidatas.append(ReferenciaFalaConsulta(turno_id, texto, observada['id'],
                observada['turno_id'], observada['fala'], observada['ts']))
        fonte = candidatas[0] if len(candidatas) == 1 else None
        return RetomadaCriacao(turno_id, texto, (), False, fonte, objeto_nomeado=objeto_nomeado)
    recorte = _recorte_da_consulta(texto)
    if recorte is None or classificar_atualidade_factual(texto)['depende_atualidade']:
        return None
    ancora, pede_regra = recorte
    turno_id = str(plano['id'])
    registro = mente.get('registro_semantico') or {}
    candidatas = []
    for item in registro.get('falas_observadas', ()) if isinstance(registro, Mapping) else ():
        if not isinstance(item, Mapping) or not isinstance(item.get('id'), str):
            continue
        observada = selecionar_fala_observada(registro, ocorrencia_id=item['id'])
        if not observada or observada.get('resultados') or observada['turno_id'] == turno_id:
            continue
        fonte = ReferenciaFalaConsulta(turno_id, texto, observada['id'], observada['turno_id'],
                                        observada['fala'], observada['ts'])
        if fonte.vigente(texto, turno_id) and _extrair_conteudo(fonte.conteudo, ancora=ancora):
            candidatas.append(fonte)
    fonte = candidatas[0] if len(candidatas) == 1 else None
    alternativas = tuple(candidatas) if len(candidatas) == 2 else ()
    return RetomadaCriacao(turno_id, texto, ancora, pede_regra, fonte, alternativas)


def _realizar_retomada(retomada: RetomadaCriacao) -> tuple[str, str]:
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta

    def conteudo(fonte: ReferenciaFalaConsulta | None) -> _ConteudoCriacao | None:
        if type(fonte) is ReferenciaFalaConsulta and fonte.vigente(retomada.texto_usuario, retomada.turno_id):
            return _extrair_conteudo(fonte.conteudo, ancora=retomada.ancora)
        return None

    if unico := conteudo(retomada.fonte):
        return unico.realizar(pede_regra=retomada.pede_regra)
    if len(retomada.alternativas) == 2:
        primeira, segunda = map(conteudo, retomada.alternativas)
        if primeira and segunda:
            if primeira.definicao != segunda.definicao:
                fala = f'Você quer retomar a versão com {primeira.definicao} ou com {segunda.definicao}?'
                return fala, 'esclarecimento_de_versao'
            if primeira.regra and segunda.regra and primeira.regra != segunda.regra:
                if _COORDENACAO_DA_REGRA.search(primeira.regra + ' ' + segunda.regra):
                    fala = f'Qual regra você quer retomar, «{primeira.regra}» ou «{segunda.regra}»?'
                else:
                    fala = f'Você quer a versão em que {primeira.regra} ou aquela em que {segunda.regra}?'
                return fala, 'esclarecimento_de_versao'
    return '', 'ausente'


def avaliar_retomada_criacao(fala: str, *, plano: Mapping[str, Any]) -> dict[str, Any]:
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta
    contrato = plano.get('contrato_fala') or {}
    retomada = contrato.get('retomada_criacao')
    texto, turno_id = plano.get('texto_usuario'), str(plano.get('id') or '')
    realizacao, cobertura = '', 'ausente'
    limite = _LIMITE
    if (type(retomada) is RetomadaCriacao and retomada.turno_id == turno_id
            and retomada.texto_usuario == texto and contrato.get('origem') == 'mente_unica'
            and str(contrato.get('turno_id')) == turno_id and contrato.get('autoriza_execucao') is False
            and plano.get('autoriza_execucao') is False and not plano.get('comandos')
            and not plano.get('requer_execucao')):
        if retomada.escolha_inicial and retomada.escolha_inicial == recorte_escolha_inicial(texto):
            fonte = retomada.fonte
            if type(fonte) is ReferenciaFalaConsulta and fonte.vigente(texto, turno_id):
                realizacao = _nome_escolha_inicial(fonte.conteudo, retomada.escolha_inicial)
                cobertura = 'escolha_inicial_publicada' if realizacao else 'ausente'
            limite = f'Qual proposta inicial para {retomada.escolha_inicial} você quer retomar?'
        elif retomada.objeto_nomeado and retomada.objeto_nomeado == recorte_nome_publicado(texto):
            from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta
            fonte = retomada.fonte
            if type(fonte) is ReferenciaFalaConsulta and fonte.vigente(texto, turno_id):
                realizacao = _nome_publicado(fonte.conteudo, retomada.objeto_nomeado)
                cobertura = 'nome_publicado' if realizacao else 'ausente'
            limite = f'Qual nome você quer retomar para {retomada.objeto_nomeado}?'
        elif not retomada.objeto_nomeado:
            realizacao, cobertura = _realizar_retomada(retomada)
    esperada = realizacao or limite
    aceita = ' '.join(str(fala or '').split()) == ' '.join(esperada.split())
    return {'fala': esperada, 'problemas': [] if aceita else ['retomada_criacao_sem_apoio'],
            'acao': 'aceita' if aceita else 'ajustada', 'fonte_valida': bool(realizacao),
            'cobertura': cobertura if aceita else 'ausente',
            'prova_semantica_livre': False, 'autoriza_execucao': False}
