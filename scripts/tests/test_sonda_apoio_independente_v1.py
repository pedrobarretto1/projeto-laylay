from copy import deepcopy
import json

import pytest
import requests

from scripts.analises import sonda_apoio_independente_v1 as s


def enviar(proposta, **alteracoes):
    envelope = {'model': s.MODELO, 'provider': 'Google AI Studio', 'usage': {'cost': 0.0001},
                'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(proposta)}}]}
    envelope.update(alteracoes)
    class Resposta:
        status_code = 200
        text = json.dumps(envelope)
        def json(self):
            return deepcopy(envelope)
    return lambda *a, **k: Resposta()


def test_adapter_preserva_fonte_prompt_schema_e_nao_envia_gabarito():
    for c in s.carregar_painel():
        for q in ['controle', *[r['id'] for r in s.local.regioes(c)]]:
            r = s.preparar_requisicao(c, q)
            l = s.local.preparar_requisicao(c, q)
            assert r['messages'] == l['messages']
            assert r['response_format']['json_schema']['schema'] == l['format']
            assert r == s.preparar_requisicao({**c, 'esperado': 'X', 'candidatos_esperados': [], 'situacao_esperada': 'X'}, q)
            registro = s.medir(c, q, 1, 'segredo_de_teste', enviar=enviar({'ligacao': 'sustentada'}))
            assert registro['http_status'] == 200
            assert 'segredo_de_teste' not in json.dumps(registro)


@pytest.fixture(scope='module')
def registros():
    return [s.medir(c, q, rep, 'segredo', enviar=enviar(
        {'ocorrencia_id': c['esperado']} if q == 'controle' else {'ligacao': s.local.esperado_par(c, q)}))
        for c, q, rep in s.local.sequencia(s.carregar_painel())]


@pytest.mark.parametrize('campo', ['ordem', 'flag', 'rep', 'request', 'falta'])
def test_rejeita_artefato_adulterado(registros, campo):
    rs = deepcopy(registros)
    if campo == 'ordem': rs.reverse()
    elif campo == 'flag': rs[0]['autoriza_efeito'] = True
    elif campo == 'rep': rs[0]['repeticao'] = True
    elif campo == 'request': rs[0]['requisicao']['messages'][0]['content'] += '!'
    elif campo == 'falta': rs.pop()
    assert s.resumir(rs)['tipo'] == 'resumo_invalido'


@pytest.mark.parametrize('alteracao', ['length', 'modelo', 'provedor', 'recusa', 'schema', 'nan'])
def test_http_200_nao_basta_para_classificacao(alteracao):
    c = s.carregar_painel()[0]
    r = s.medir(c, 'q0', 1, 'segredo', enviar=enviar({'ligacao': 'sustentada'}))
    b = json.loads(r['http_bruto'])
    if alteracao == 'length': b['choices'][0]['finish_reason'] = 'length'
    elif alteracao == 'modelo': b['model'] = 'outro'
    elif alteracao == 'provedor': b['provider'] = 'outro'
    elif alteracao == 'recusa': b['choices'][0]['message']['refusal'] = 'recusado'
    elif alteracao == 'schema': b['choices'][0]['message']['content'] = '{"ligacao":true}'
    elif alteracao == 'nan': b['choices'][0]['message']['content'] = '{"ligacao":NaN}'
    r['http_bruto'] = json.dumps(b)
    assert s.aferir(c, r, 'q0', 1)['shape'] is False


def test_resumo_recalcula_bruto_sem_promover_autoridade(registros):
    rs = deepcopy(registros)
    r = next(r for r in rs if r['id'] == 'L5' and r['ocorrencia'] == 'q0')
    b = json.loads(r['http_bruto'])
    b['choices'][0]['message']['content'] = '{"ligacao":"sustentada"}'
    r['http_bruto'] = json.dumps(b)
    r['alinhado_local'] = True
    a = s.resumir(rs)
    assert a['por_caso']['L5']['1']['q0']['alinhado_local'] is False
    assert all(a[k] is False for k in s.BASE)
    assert a['agregacao_integrada'] is False


def test_timeout_nao_expoe_segredo_ou_finge_classificacao():
    def falhar(*a, **k):
        raise requests.ReadTimeout('segredo')
    c = s.carregar_painel()[0]
    r = s.medir(c, 'q0', 1, 'segredo', enviar=falhar)
    assert 'segredo' not in json.dumps(r)
    assert s.aferir(c, r, 'q0', 1)['shape'] is False
