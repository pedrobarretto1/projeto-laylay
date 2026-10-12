"""P01 offline: remover somente o catálogo de aspas do input do modelo."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter

import requests

from scripts.analises import sonda_pergunta_relacional_v1 as anterior

BASE, etapas, schema = anterior.BASE, anterior.etapas, anterior.schema
HASH_ANTERIOR = '31449aeadb11fe6287a89071b62c2c5cd80eb5767238f5137a07112488a1091c'
MODOS = ('catalogo', 'sem_catalogo')


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(anterior.__file__).read_bytes()).hexdigest() != HASH_ANTERIOR:
        raise ValueError('controle congelado alterado')
    return anterior.carregar_painel()


def entrada_host(caso: dict) -> dict:
    """Mapa completo reconstruído pela cadeia canônica, nunca pelo modelo."""
    return json.loads(anterior.preparar_requisicao(caso, 'pergunta')['messages'][1]['content'])


def preparar_requisicao(caso: dict, modo: str) -> dict:
    if modo not in MODOS:
        raise ValueError('modo invalido')
    r = anterior.preparar_requisicao(caso, 'pergunta')
    if modo == 'sem_catalogo':
        entrada = json.loads(r['messages'][1]['content'])
        # Omissão não equivale à afirmação de que não existem citações.
        del entrada['aspas_sintaticas']['regioes_entre_aspas']
        r['messages'][1]['content'] = json.dumps(entrada, ensure_ascii=False)
    return r


def medir(caso: dict, modo: str, rep: int, post=requests.post) -> dict:
    r = {**BASE, 'id': caso['id'], 'modo': modo, 'repeticao': rep,
         'entrada_host': entrada_host(caso), 'requisicao': preparar_requisicao(caso, modo)}
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
            or not etapas.iguais_tipados(r.get('entrada_host'), entrada_host(caso))
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
    a = anterior.anterior.materializar(caso, p if d['finalizacao'] == 'concluida' else None, 'copia')
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
    return {**BASE, 'tipo': 'resumo_ablacao_catalogo', 'por_caso': a,
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
            a = aferir(c, r, m, rep)
            print(json.dumps({'id': c['id'], 'modo': m, 'rep': rep,
                              'proposta': a['proposta'], 'alinhado': a['argumento_alinhado_local']},
                             ensure_ascii=False), flush=True)
        fim = resumir(registros)
        try:
            fim['digest_final'] = etapas.coordenadas.digest_modelo()
            fim['modelo_igual_entre_leituras'] = fim['digest_final'] == digest
        except Exception as erro:
            fim.update(erro_digest_final=type(erro).__name__, modelo_igual_entre_leituras=False)
        escrever(fim)


if __name__ == '__main__':
    main()
