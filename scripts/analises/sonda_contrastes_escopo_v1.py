"""Contrastes novos de escopo, sem alterar prompts ou promover interpretação."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from scripts.analises import sonda_apoio_independente_v1 as externo

local = externo.local
BASE = local.BASE
HASH_EXTERNO = '364284d5037de19eb3cd4d0915ed18115323e53576b6c7898b3752b2cfd9053c'
MODELOS = ('local', 'externo')
# Revisão local pré-consulta. Os labels não entram nas requisições.
PREFIXO = 'A ficha lista “polir o sino” e “trocar a corda”. '
ANINHADA = 'A cronista escreveu “a capitã ordenou \'recolha a vela\' no convés”.'
CASOS = (
    ('U0', PREFIXO + 'Não se sabe qual dessas expressões é o nome da oficina.',
     'é o nome da oficina', ['q0', 'q1'], 'indeterminado'),
    ('U1', PREFIXO + 'A primeira dessas expressões é o nome da oficina.',
     'é o nome da oficina', ['q0'], 'unico'),
    ('U2', PREFIXO + 'A segunda dessas expressões é o nome da oficina.',
     'é o nome da oficina', ['q1'], 'unico'),
    ('O0', 'O título é a expressão desta página ou uma expressão da página ausente. A única expressão desta página é “varra o cais”.',
     'O título', ['q0'], 'indeterminado'),
    ('O1', 'O título é a expressão desta página, não uma expressão da página ausente. A única expressão desta página é “varra o cais”.',
     'O título', ['q0'], 'unico'),
    ('N0', ANINHADA, 'A cronista escreveu', ['q0'], 'unico'),
    ('N1', ANINHADA, 'a capitã ordenou', ['q1'], 'unico'),
)


def carregar_painel() -> list[dict]:
    if hashlib.sha256(Path(externo.__file__).read_bytes()).hexdigest() != HASH_EXTERNO:
        raise ValueError('adaptador externo congelado alterado')
    externo.carregar_painel()  # Confere também dependências e controle histórico.
    casos = []
    for identidade, texto, relacao, candidatos, situacao in CASOS:
        if texto.count(relacao) != 1:
            raise ValueError('relacao nao unica')
        inicio = texto.index(relacao)
        casos.append(dict(id=identidade, texto=texto, foco_id='c1',
                          relacao=dict(inicio=inicio, fim=inicio+len(relacao), texto=relacao),
                          candidatos_esperados=list(candidatos), situacao_esperada=situacao,
                          esperado=candidatos[0] if situacao == 'unico' else situacao,
                          origem_relacao='fixture_contraste_escopo_nova'))
    return casos


def sequencia(casos: list[dict]) -> list[tuple]:
    primeira = [(c, q) for c, q, rep in local.sequencia(casos) if rep == 1]
    itens = [(c, q, backend) for i, (c, q) in enumerate(primeira)
             for backend in (MODELOS if i % 2 == 0 else MODELOS[::-1])]
    return [(c, q, backend, rep) for rep in (1, 2)
            for c, q, backend in (itens if rep == 1 else itens[::-1])]


def aferir(caso: dict, registro: dict, q: str, backend: str, rep: int) -> dict:
    if backend not in MODELOS or registro.get('backend') != backend:
        raise ValueError('backend adulterado')
    bruto = {k: v for k, v in registro.items() if k != 'backend'}
    if backend == 'externo':
        return externo.aferir(caso, bruto, q, rep)
    a = local.aferir(caso, bruto, q, rep)
    return {**a, 'proposta': a.get('ocorrencia_proposta') if q == 'controle' else a.get('ligacao_proposta'),
            'alinhado_local': a['alvo_alinhado_local'] if q == 'controle' else a['par_alinhado_local']}


def resumir(registros: list[dict]) -> dict:
    casos = carregar_painel()
    ordem = sequencia(casos)
    invalido = {**BASE, 'tipo': 'resumo_invalido'}
    if not isinstance(registros, list) or len(registros) != len(ordem):
        return invalido
    a = {}
    try:
        for r, (c, q, b, rep) in zip(registros, ordem, strict=True):
            a.setdefault(b, {}).setdefault(c['id'], {}).setdefault(str(rep), {})[q] = aferir(c, r, q, b, rep)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return invalido
    return {**BASE, 'tipo': 'resumo_contrastes_escopo', 'por_backend': a,
            'runtime_laylay': False, 'agregacao_integrada': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    casos = carregar_painel()
    externo.remoto.carregar_segredo_no_ambiente()
    chave = os.environ.get('OPENROUTER_API_KEY')
    if not chave:
        raise ValueError('credencial indisponivel')
    digest = local.anterior.anterior.etapas.coordenadas.digest_modelo()
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open('x', encoding='utf-8') as arquivo:
        def escrever(r: dict) -> None:
            arquivo.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n')
            arquivo.flush()
        escrever({**BASE, 'tipo': 'metadata', 'casos_pre_consulta': casos,
                  'hash_script': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'hash_externo': HASH_EXTERNO, 'digest_inicio': digest,
                  'ordem': [[c['id'], q, b, rep] for c, q, b, rep in sequencia(casos)],
                  'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  'branch': subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip(),
                  'worktree': subprocess.check_output(['git', 'status', '--short'], text=True).splitlines(),
                  'runtime_laylay': False, 'limite_usd': externo.LIMITE_USD})
        registros = []
        custo = 0.0
        for c, q, b, rep in sequencia(casos):
            if b == 'externo' and custo + 0.002 > externo.LIMITE_USD:
                escrever({**BASE, 'tipo': 'interrompido_orcamento'})
                return
            r = local.medir(c, q, rep) if b == 'local' else externo.medir(c, q, rep, chave)
            r['backend'] = b
            escrever(r)
            registros.append(r)
            a = aferir(c, r, q, b, rep)
            print(json.dumps({'id': c['id'], 'q': q, 'backend': b, 'rep': rep, 'proposta': a['proposta']}), flush=True)
            if not a['shape'] or (b == 'externo' and a['custo_usd'] is None):
                escrever({**BASE, 'tipo': 'interrompido_consulta'})
                return
            if b == 'externo':
                custo += a['custo_usd']
        fim = resumir(registros)
        try:
            fim['digest_final'] = local.anterior.anterior.etapas.coordenadas.digest_modelo()
            fim['modelo_igual_entre_leituras'] = fim['digest_final'] == digest
        except Exception as erro:
            fim.update(erro_digest_final=type(erro).__name__, modelo_igual_entre_leituras=False)
        escrever({**fim, 'custo_total_usd': custo})


if __name__ == '__main__':
    main()
