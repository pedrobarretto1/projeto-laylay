from copy import deepcopy
import json
import pytest

from scripts.analises import sonda_contrastes_escopo_v1 as s
from scripts.tests.test_sonda_apoio_independente_v1 import enviar
from scripts.tests.test_sonda_transferencia_papel_isolado_v1 import post


def test_contrastes_preservam_fonte_ou_alteram_apenas_informacao_de_interesse():
    cs = {c['id']: c for c in s.carregar_painel()}
    assert len(cs) == 7
    assert cs['N0']['texto'] == cs['N1']['texto']
    assert cs['N0']['esperado'] == 'q0' and cs['N1']['esperado'] == 'q1'
    assert s.local.regioes(cs['N1'])[1]['pai_id'] == 'q0'
    assert cs['O0']['texto'].replace(' ou ', ', não ') == cs['O1']['texto']
    assert cs['O0']['esperado'] == 'indeterminado' and cs['O1']['esperado'] == 'q0'
    assert cs['U1']['texto'].replace('primeira', 'segunda') == cs['U2']['texto']
    assert all(cs[i]['texto'].startswith(s.PREFIXO) for i in ('U0', 'U1', 'U2'))


def test_projecao_nao_envia_gold_e_mantem_prompts_schemas_anteriores():
    for c in s.carregar_painel():
        for q in ['controle', *[r['id'] for r in s.local.regioes(c)]]:
            l = s.local.preparar_requisicao(c, q)
            e = s.externo.preparar_requisicao(c, q)
            assert l['messages'] == e['messages']
            assert l['format'] == e['response_format']['json_schema']['schema']
            assert json.loads(l['messages'][1]['content'])['fonte']['texto'] == c['texto']
            assert l == s.local.preparar_requisicao({**c, 'esperado': 'X', 'candidatos_esperados': [], 'situacao_esperada': 'X'}, q)


@pytest.fixture(scope='module')
def registros():
    rs = []
    for c, q, b, rep in s.sequencia(s.carregar_painel()):
        p = {'ocorrencia_id': c['esperado']} if q == 'controle' else {'ligacao': s.local.esperado_par(c, q)}
        r = s.local.medir(c, q, rep, post=post(p)) if b == 'local' else s.externo.medir(c, q, rep, 'segredo', enviar=enviar(p))
        rs.append({**r, 'backend': b})
    return rs


@pytest.mark.parametrize('mudanca', ['backend', 'ordem', 'flag', 'rep', 'request', 'falta'])
def test_adulteracao_nao_gera_placar(registros, mudanca):
    rs = deepcopy(registros)
    if mudanca == 'backend': rs[0]['backend'] = 'externo'
    elif mudanca == 'ordem': rs.reverse()
    elif mudanca == 'flag': rs[0]['autoriza_efeito'] = True
    elif mudanca == 'rep': rs[0]['repeticao'] = True
    elif mudanca == 'request': rs[0]['requisicao']['messages'][0]['content'] += '!'
    elif mudanca == 'falta': rs.pop()
    assert s.resumir(rs)['tipo'] == 'resumo_invalido'


def test_sucesso_local_nao_promove_autoridade_e_bruto_errado_nao_e_mascarado(registros):
    assert len(registros) == 76
    a = s.resumir(registros)
    assert all(a[k] is False for k in s.BASE)
    assert a['agregacao_integrada'] is False
    rs = deepcopy(registros)
    r = next(r for r in rs if r['id'] == 'O0' and r['ocorrencia'] == 'q0' and r['backend'] == 'externo')
    bruto = json.loads(r['http_bruto'])
    bruto['choices'][0]['message']['content'] = '{"ligacao":"sustentada"}'
    r['http_bruto'] = json.dumps(bruto)
    r['alinhado_local'] = True
    assert s.resumir(rs)['por_backend']['externo']['O0']['1']['q0']['alinhado_local'] is False
