"""Contraste offline de interpretação; nenhum avaliador concede autoridade."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from time import perf_counter

import requests

from scripts.analises import sonda_apoio_por_ocorrencia_v1 as local
from scripts.analises import sonda_openrouter_fronteira as remoto

BASE = local.BASE
MODELO = 'google/gemini-3.1-flash-lite'
PROVEDOR = 'google-ai-studio'
HASH_LOCAL = '20486559660a8d923d880db25af4b56d53dfa9198b18f77a628d704a1d00f56d'
HASH_REMOTO = '566679584886163294a9bdf0fc8d04cd03599f634dc2c71db5df6d15a1eb6b64'
HASH_CONTROLE = '0f1c98fee9773f2fc4b921d50342801f8e08ff9bba7ce6a16c600a9e00e56a97'
CONTROLE = Path('resultados_testes/sonda_apoio_por_ocorrencia_v1.jsonl')
LIMITE_USD = 0.10


def carregar_painel() -> list[dict]:
    for modulo, esperado in ((local, HASH_LOCAL), (remoto, HASH_REMOTO)):
        if hashlib.sha256(Path(modulo.__file__).read_bytes()).hexdigest() != esperado:
            raise ValueError('dependencia congelada alterada')
    if hashlib.sha256(CONTROLE.read_bytes()).hexdigest() != HASH_CONTROLE:
        raise ValueError('controle historico alterado')
    return local.carregar_painel()


def preparar_requisicao(caso: dict, ocorrencia: str) -> dict:
    origem = local.preparar_requisicao(caso, ocorrencia)
    return {
        'model': MODELO, 'messages': deepcopy(origem['messages']),
        'response_format': {'type': 'json_schema', 'json_schema': {
            'name': 'fronteira_p01', 'strict': True, 'schema': origem['format']}},
        'provider': {'require_parameters': True, 'only': [PROVEDOR], 'allow_fallbacks': False},
        'max_tokens': 256, 'stream': False, 'temperature': 0,
    }


def medir(caso: dict, ocorrencia: str, repeticao: int, chave: str,
          enviar=requests.post) -> dict:
    esperado = preparar_requisicao(caso, ocorrencia)
    registro = {**BASE, 'id': caso['id'], 'ocorrencia': ocorrencia,
                'repeticao': repeticao, 'requisicao': esperado}

    def capturar(url: str, **kwargs) -> object:
        # A credencial fica somente nos headers de transporte, nunca no artefato.
        if url != remoto.URL or not iguais(kwargs['json'], esperado):
            raise ValueError('adaptador mudou a requisicao congelada')
        resposta = enviar(url, **kwargs)
        registro.update(http_status=resposta.status_code, http_bruto=resposta.text)
        return resposta

    inicio = perf_counter()
    try:
        remoto.consultar_openrouter(
            esperado['messages'][0]['content'],
            json.loads(esperado['messages'][1]['content']),
            esperado['response_format']['json_schema']['schema'],
            modelo=MODELO, chave=chave, temperatura=0, provedor=PROVEDOR, enviar=capturar,
        )
    except remoto.ErroConsultaOpenRouter as erro:
        registro['erro_consulta'] = type(erro).__name__
    registro['duracao_consulta_s'] = perf_counter() - inicio
    return registro


iguais = local.anterior.anterior.etapas.iguais_tipados


def decodificar(registro: dict) -> dict:
    resultado = {'shape': False, 'proposta': None, 'custo_usd': None}
    if 'http_status' not in registro:
        if (registro.get('erro_consulta') != 'ErroConsultaOpenRouter'
                or 'http_bruto' in registro):
            raise ValueError('captura ausente sem erro de transporte')
        return resultado
    status, bruto = registro['http_status'], registro.get('http_bruto')
    if type(status) is not int or not 100 <= status <= 599 or not isinstance(bruto, str):
        raise ValueError('captura invalida')
    if status != 200:
        return resultado
    try:
        recusar = local.anterior.anterior.schema._recusar_constante
        envelope = json.loads(bruto, parse_constant=recusar)
        escolha = envelope['choices'][0]
        custo = envelope.get('usage', {}).get('cost')
        if type(custo) in (int, float) and math.isfinite(custo) and custo >= 0:
            resultado['custo_usd'] = custo
        resultado.update(modelo_recebido=envelope.get('model'),
                         provedor_recebido=envelope.get('provider'),
                         motivo_termino=escolha.get('finish_reason'))
        if (envelope.get('model') != MODELO or envelope.get('provider') != 'Google AI Studio'
                or escolha.get('finish_reason') != 'stop'
                or escolha['message'].get('refusal') or escolha['message'].get('tool_calls')):
            return resultado
        proposta = json.loads(escolha['message']['content'], parse_constant=recusar)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return resultado
    schema = registro['requisicao']['response_format']['json_schema']['schema']
    chave = schema['required'][0]
    valido = (isinstance(proposta, dict) and set(proposta) == {chave}
              and type(proposta[chave]) is str and proposta[chave] in schema['properties'][chave]['enum'])
    return {**resultado, 'shape': valido, 'proposta': proposta[chave] if valido else None}


def aferir(caso: dict, registro: dict, ocorrencia: str, repeticao: int) -> dict:
    if (not isinstance(registro, dict) or registro.get('id') != caso['id']
            or registro.get('ocorrencia') != ocorrencia
            or type(registro.get('repeticao')) is not int or registro['repeticao'] != repeticao
            or any(registro.get(k) is not False for k in BASE)
            or not iguais(registro.get('requisicao'), preparar_requisicao(caso, ocorrencia))):
        raise ValueError('registro adulterado')
    local.anterior.anterior.etapas.conferir_registro_consulta({
        'proposta': None, 'duracao_consulta_s': registro.get('duracao_consulta_s')})
    resultado = decodificar(registro)
    esperado = caso['esperado'] if ocorrencia == 'controle' else local.esperado_par(caso, ocorrencia)
    return {**BASE, **resultado, 'alinhado_local': bool(resultado['shape'] and resultado['proposta'] == esperado)}


def resumir(registros: list[dict]) -> dict:
    casos = carregar_painel()
    ordem = local.sequencia(casos)
    invalido = {**BASE, 'tipo': 'resumo_invalido'}
    if not isinstance(registros, list) or len(registros) != len(ordem):
        return invalido
    avaliacoes = {}
    try:
        for registro, (caso, q, rep) in zip(registros, ordem, strict=True):
            avaliacoes.setdefault(caso['id'], {}).setdefault(str(rep), {})[q] = aferir(caso, registro, q, rep)
    except (ValueError, TypeError, KeyError, OverflowError):
        return invalido
    return {**BASE, 'tipo': 'resumo_apoio_independente', 'por_caso': avaliacoes,
            'runtime_laylay': False, 'agregacao_integrada': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    casos = carregar_painel()
    remoto.carregar_segredo_no_ambiente()
    chave = os.environ.get('OPENROUTER_API_KEY')
    if not chave:
        raise ValueError('credencial indisponivel')
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open('x', encoding='utf-8') as arquivo:
        def escrever(registro: dict) -> None:
            arquivo.write(json.dumps(registro, ensure_ascii=False, allow_nan=False) + '\n')
            arquivo.flush()
        escrever({**BASE, 'tipo': 'metadata', 'casos_pre_consulta': casos,
                  'hash_script': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'hash_local': HASH_LOCAL, 'hash_remoto': HASH_REMOTO, 'hash_controle': HASH_CONTROLE,
                  'ordem': [[c['id'], q, rep] for c, q, rep in local.sequencia(casos)],
                  'modelo': MODELO, 'provedor': PROVEDOR, 'limite_usd': LIMITE_USD,
                  'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  'branch': subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip(),
                  'worktree': subprocess.check_output(['git', 'status', '--short'], text=True).splitlines(),
                  'runtime_laylay': False})
        registros = []
        custo = 0.0
        for caso, q, rep in local.sequencia(casos):
            # Reserva antes da próxima chamada; nunca repetir automaticamente falhas.
            if custo + 0.002 > LIMITE_USD:
                escrever({**BASE, 'tipo': 'interrompido_orcamento', 'custo_usd': custo})
                return
            registro = medir(caso, q, rep, chave)
            escrever(registro)
            registros.append(registro)
            avaliacao = aferir(caso, registro, q, rep)
            print(json.dumps({'id': caso['id'], 'q': q, 'rep': rep,
                              'proposta': avaliacao['proposta']}), flush=True)
            if not avaliacao['shape'] or avaliacao['custo_usd'] is None:
                escrever({**BASE, 'tipo': 'interrompido_consulta', 'consultas': len(registros)})
                return
            custo += avaliacao['custo_usd']
        escrever({**resumir(registros), 'custo_total_usd': custo})


if __name__ == '__main__':
    main()
