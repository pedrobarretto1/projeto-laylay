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
    from mente_laylay.memoria_mental.registro_semantico import ReferenciaFalaConsulta, selecionar_fala_observada

    if (not plano.get('id') or plano.get('texto_usuario') != texto or plano.get('autoriza_execucao') is not False
            or plano.get('requer_execucao') or plano.get('comandos')):
        return None
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
    contrato = plano.get('contrato_fala') or {}
    retomada = contrato.get('retomada_criacao')
    texto, turno_id = plano.get('texto_usuario'), str(plano.get('id') or '')
    realizacao, cobertura = '', 'ausente'
    if (type(retomada) is RetomadaCriacao and retomada.turno_id == turno_id
            and retomada.texto_usuario == texto and contrato.get('origem') == 'mente_unica'
            and str(contrato.get('turno_id')) == turno_id and contrato.get('autoriza_execucao') is False
            and plano.get('autoriza_execucao') is False and not plano.get('comandos')
            and not plano.get('requer_execucao')):
        realizacao, cobertura = _realizar_retomada(retomada)
    esperada = realizacao or _LIMITE
    aceita = ' '.join(str(fala or '').split()) == ' '.join(esperada.split())
    return {'fala': esperada, 'problemas': [] if aceita else ['retomada_criacao_sem_apoio'],
            'acao': 'aceita' if aceita else 'ajustada', 'fonte_valida': bool(realizacao),
            'cobertura': cobertura if aceita else 'ausente',
            'prova_semantica_livre': False, 'autoriza_execucao': False}
