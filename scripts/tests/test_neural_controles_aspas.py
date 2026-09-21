from collections import Counter, defaultdict

import pytest
from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.avaliacao import head_aplicavel
from mente_laylay.neural.dataset import validar_exemplo
from mente_laylay.neural.datasets.gerar_controles_aspas_v1 import gerar_controles
from mente_laylay.neural.qualidade import _normalizar_texto
from mente_laylay.neural.representacao_regioes_texto import representar_regioes_texto
from mente_laylay.neural.experimento_regioes_aspas import executar


def test_grade_balanceada_em_cada_ato_e_dominio():
    itens = gerar_controles()
    assert len(itens) == 96
    assert len({i['text'] for i in itens}) == 96
    assert set(Counter((i['domain'], i['ato'], i['com_aspas']) for i in itens).values()) == {4}
    assert all(i['particao'] == 'avaliacao_somente' for i in itens)


def test_irmaos_diferem_apenas_em_aspas_e_nunca_mudam_rotulos():
    pares = defaultdict(list)
    for i in gerar_controles():
        pares[i['pair_id']].append(i)
    assert len(pares) == 48
    for a, b in pares.values():
        assert a['text'] == b['text'].replace('"', '')
        assert _normalizar_texto(a['text']) == _normalizar_texto(b['text'])
        for k in ('intent', 'action', 'negated', 'is_command', 'training_heads', 'validation_group'):
            assert a[k] == b[k]


def test_relato_nao_supervisiona_cabeca_negacao():
    catalogo = intents_registradas()
    for i in gerar_controles():
        v = validar_exemplo(i, intents_permitidas=catalogo)
        if i['ato'] == 'relato':
            assert not head_aplicavel(v, 'negation')
            assert head_aplicavel(v, 'command')
            assert not v['is_command'] and v['intent'] == 'NONE'
        else:
            assert head_aplicavel(v, 'negation')
        assert not head_aplicavel(v, 'intent')


def test_rotulo_nao_e_determinado_pela_palavra_nao_no_titulo():
    casos = [i for i in gerar_controles() if i['domain'] == 'musica' and i['ato'] == 'pedido']
    assert len(casos) == 8
    assert all('Não Volte' in i['text'] and not i['negated'] and i['is_command'] for i in casos)


def test_separacao_preserva_conteudo_em_todos_os_controles():
    for i in gerar_controles():
        r = representar_regioes_texto(i['text'])
        assert ''.join(x['texto'] for x in r['regioes']) == i['text']
        assert any(x['tipo'] == 'citado' for x in r['regioes']) == i['com_aspas']


def test_runner_recusa_destino_existente_antes_de_carregar_modelo(tmp_path):
    with pytest.raises(FileExistsError):
        executar(referencia=tmp_path / 'ausente', historico=tmp_path / 'ausente', destino=tmp_path)
