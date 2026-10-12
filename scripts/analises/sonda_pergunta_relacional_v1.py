"""P01 offline: pergunta de papel explícita versus argumento sem papel indicado."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter

import requests

from scripts.analises import sonda_argumento_isolado_v1 as anterior

BASE, etapas, schema = anterior.BASE, anterior.etapas, anterior.schema
HASH_ANTERIOR = 'e1248619d2aa15b51d22c40177b14795044d6669e21f3f3fe947623731b9982a'
MODOS = ('controle', 'pergunta')
PERGUNTA_NOME = ('Qual trecho funciona como sujeito da atribuicao de nome? '
                 'Copie a mencao empregada nessa atribuicao, nao resolva seu referente.')
PERGUNTA_TITULO = ('Qual expressao e apresentada como titulo na afirmacao marcada? '
                   'Copie o complemento que informa em que consiste o titulo, '
                   'preservando alternativas abertas, sem incluir uma alternativa negada.')
PERGUNTA_CONTEUDO = ('Qual e o conteudo comunicado pelo autor da acao marcada? '
                     'Copie o complemento de conteudo dessa acao, nao o autor nem o verbo.')
PERGUNTAS = {
    **{k: PERGUNTA_NOME for k in ('U0', 'U1', 'U2')},
    **{k: PERGUNTA_TITULO for k in ('O0', 'O1')},
    **{k: PERGUNTA_CONTEUDO for k in ('N0', 'N1', 'D0', 'C0', 'C1')},
    **{k: ('Qual trecho funciona como sujeito da identificacao do projeto? '
           'Copie a mencao empregada nessa atribuicao, nao resolva seu referente.') for k in ('A0', 'A1')},
    'D1': 'Qual nome e atribuido a exposicao? Copie o complemento de nomeacao, nao a entidade nomeada.',
}
DIRETA = 'O bilhete recomenda “reduza a pressão”; a exposição se chama “abra a janela”.'
ANAFORA = 'O catálogo lista “suba a torre” e “cruze o rio”. '
CITACAO = 'O diário registra “a guia aconselhou \'evite a ponte\' ao grupo”.'
NOVOS = (
    ('D0', DIRETA, 'O bilhete recomenda', ('“reduza a pressão”', 'reduza a pressão')),
    ('D1', DIRETA, 'a exposição se chama', ('“abra a janela”', 'abra a janela')),
    ('A0', ANAFORA + 'A primeira dessas expressões identifica o projeto.',
     'identifica o projeto', ('A primeira dessas expressões', 'primeira dessas expressões')),
    ('A1', ANAFORA + 'A segunda dessas expressões identifica o projeto.',
     'identifica o projeto', ('A segunda dessas expressões', 'segunda dessas expressões')),
    ('C0', CITACAO, 'O diário registra',
     ('“a guia aconselhou \'evite a ponte\' ao grupo”', "a guia aconselhou 'evite a ponte' ao grupo")),
    ('C1', CITACAO, 'a guia aconselhou', ("'evite a ponte'", 'evite a ponte')),
)


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError('controle congelado alterado')
    casos = [{**c, 'grupo': 'conhecido', 'ouro_argumento': list(anterior.OURO[c['id']])}
             for c in anterior.carregar_painel()]
    for identidade, texto, relacao, ouro in NOVOS:
        if texto.count(relacao) != 1:
            raise ValueError('ancora ambigua')
        inicio = texto.index(relacao)
        casos.append(dict(id=identidade, texto=texto, foco_id='c1', grupo='novo',
                          relacao=dict(inicio=inicio, fim=inicio+len(relacao), texto=relacao),
                          ouro_argumento=list(ouro), origem_relacao='fixture_pergunta_relacional'))
    for c in casos:
        c['pergunta_relacional'] = PERGUNTAS[c['id']]
        if any(t not in c['texto'] for t in c['ouro_argumento']):
            raise ValueError('ouro ausente')
    return casos


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError('modo invalido')
    r = anterior.preparar_requisicao(caso, 'copia')
    if modo == 'pergunta':
        entrada = json.loads(r['messages'][1]['content'])
        entrada['pergunta_relacional'] = caso['pergunta_relacional']
        r['messages'][1]['content'] = json.dumps(entrada, ensure_ascii=False)
        r['messages'][0]['content'] += (' Use pergunta_relacional para identificar o papel '
                                       'procurado; a resposta continua sendo uma copia da fonte.')
    return r


def medir(caso: dict, modo: str, rep: int, post=requests.post) -> dict:
    r = {**BASE, 'id': caso['id'], 'modo': modo, 'repeticao': rep,
         'requisicao': preparar_requisicao(caso, modo)}
    inicio = perf_counter()
    try:
        r.update(schema.capturar_http(deepcopy(r['requisicao']), post))
    except Exception as erro:
        r['erro_consulta'] = type(erro).__name__
    r['duracao_consulta_s'] = perf_counter() - inicio
    return r


def aferir(caso: dict, r: dict, modo: str, rep: int) -> dict:
    if (not isinstance(r, dict) or r.get('id') != caso['id'] or r.get('modo') != modo
            or type(r.get('repeticao')) is not int or r['repeticao'] != rep
            or any(r.get(k) is not False for k in BASE)
            or not etapas.iguais_tipados(r.get('requisicao'), preparar_requisicao(caso, modo))):
        raise ValueError('registro adulterado')
    etapas.conferir_registro_consulta({'proposta': None, 'duracao_consulta_s': r.get('duracao_consulta_s')})
    if 'erro_consulta' in r:
        if type(r['erro_consulta']) is not str or 'http_status' in r or 'http_bruto' in r:
            raise ValueError('consulta contraditoria')
        d = {'finalizacao': 'nao_confirmada'}
    else:
        d = schema.decodificar_http(r.get('http_status'), r.get('http_bruto'))
    p = d.get('proposta')
    a = anterior.materializar(caso, p if d['finalizacao'] == 'concluida' else None, 'copia')
    ouro = [{'inicio': caso['texto'].index(t), 'fim': caso['texto'].index(t)+len(t), 'texto': t}
            for t in caso['ouro_argumento']]
    return {**a, 'proposta': p, 'argumento_alinhado_local': bool(a['literal'] and a['trecho'] in ouro)}


def sequencia(casos: list[dict]) -> list[tuple]:
    itens = [(c, m) for i, c in enumerate(casos) for m in (MODOS if i % 2 == 0 else MODOS[::-1])]
    return [(c, m, rep) for rep in (1, 2) for c, m in (itens if rep == 1 else itens[::-1])]


def resumir(registros: list[dict]) -> dict:
    ordem = sequencia(carregar_painel())
    invalido = {**BASE, 'tipo': 'resumo_invalido'}
    if type(registros) is not list or len(registros) != len(ordem):
        return invalido
    a = {}
    try:
        for r, (c, m, rep) in zip(registros, ordem, strict=True):
            a.setdefault(c['id'], {}).setdefault(m, {})[str(rep)] = aferir(c, r, m, rep)
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    return {**BASE, 'tipo': 'resumo_pergunta_relacional', 'por_caso': a,
            'runtime_laylay': False, 'perguntas_geradas_runtime': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    casos = carregar_painel()
    digest = etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open('x', encoding='utf-8') as arquivo:
        def escrever(r: dict) -> None:
            arquivo.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n')
            arquivo.flush()
        escrever({**BASE, 'tipo': 'metadata', 'casos_pre_consulta': casos,
                  'hash_script': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'hash_controle': HASH_ANTERIOR, 'digest_inicio': digest,
                  'ordem': [[c['id'], m, rep] for c, m, rep in sequencia(casos)],
                  'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  'branch': subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip(),
                  'worktree': subprocess.check_output(['git', 'status', '--short'], text=True).splitlines(),
                  'runtime_laylay': False})
        registros = []
        for c, m, rep in sequencia(casos):
            r = medir(c, m, rep)
            escrever(r)
            registros.append(r)
            print(json.dumps({'id': c['id'], 'modo': m, 'rep': rep, 'afericao': aferir(c, r, m, rep)}, ensure_ascii=False), flush=True)
        fim = resumir(registros)
        try:
            fim['digest_final'] = etapas.coordenadas.digest_modelo()
            fim['modelo_igual_entre_leituras'] = fim['digest_final'] == digest
        except Exception as erro:
            fim.update(erro_digest_final=type(erro).__name__, modelo_igual_entre_leituras=False)
        escrever(fim)


if __name__ == '__main__':
    main()
