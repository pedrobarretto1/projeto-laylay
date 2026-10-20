"""Apoio por regra integral não pode ser um parecer autoaprovado da autora."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from scripts.tests.test_revisao_suporte_fontes import _plano


def _formas(entidade, atributo, valor):
    return (f'O valor do atributo «{atributo}» de «{entidade}» é «{valor}».',
            f'«{valor}» é o valor do atributo «{atributo}» de «{entidade}».')


@pytest.mark.parametrize('entidade,atributo,valor', [
    ('arquivo alfa', 'estado', 'íntegro'), ('tomada delta', 'tensão nominal', '5 V'),
    ('nota beta', 'versão', 'A2')])
@pytest.mark.parametrize('invertida', [False, True])
def test_parafrase_integral_tem_derivacao_dos_papeis_sem_parecer_llm(entidade, atributo, valor, invertida):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    fonte, texto = _formas(entidade, atributo, valor)[::(-1 if invertida else 1)]
    plano = _plano(texto, trecho=fonte)
    r = revisar_suporte_autoria(texto, plano=plano, agora=1001)
    d = r.como_dict()
    unidade = d['proposicoes'][0]
    assert unidade['estado'] == 'parafrase_estrutural_conferida', 'primeira fronteira: revisão só conhece identidade literal, sem derivação conferível'
    prova = unidade['fontes'][0]['derivacao']
    assert prova['regra'] == 'simetria_valor_atributo_v1'
    assert prova['papeis'] == {'entidade': entidade, 'atributo': atributo, 'valor': valor}
    assert prova['fonte_sha256'] == hashlib.sha256(fonte.encode()).hexdigest()
    assert prova['proposicao_sha256'] == hashlib.sha256(texto.encode()).hexdigest()
    assert prova['formas']['fonte'] != prova['formas']['proposicao']
    for nome, completo in [('fonte', fonte), ('proposicao', texto)]:
        for papel, (inicio, fim) in prova['intervalos'][nome].items():
            assert completo[inicio:fim] == prova['papeis'][papel]
    assert prova['apoio_estrutural_conferido'] is True
    assert r.aplicar_limite and texto in r.fala_realizada
    assert 'Parafraseando' in r.fala_realizada and '«' + texto + '»' not in r.fala_realizada
    assert '.. Há' not in r.fala_realizada
    assert d['semantica_verificada'] is d['prova_implicacao'] is d['autoriza_execucao'] is False
    assert d['pode_confirmar_fato_externo'] is False
    prova['papeis']['valor'] = 'adulterado'
    assert r.como_dict()['proposicoes'][0]['fontes'][0]['derivacao']['papeis']['valor'] == valor
    outra = revisar_suporte_autoria(r.fala_realizada, plano=plano, agora=1001)
    assert outra.como_dict() == r.como_dict() and outra.fala_realizada == r.fala_realizada


_FONTE, _PARAFRASE = _formas('objeto alfa', 'estado', 'íntegro')


@pytest.mark.parametrize('fonte,texto', [
    (_FONTE, _PARAFRASE.replace('objeto alfa', 'objeto beta')),
    (_FONTE, _PARAFRASE.replace('estado', 'destino')),
    (_FONTE, _PARAFRASE.replace('íntegro', 'alterado')),
    (_FONTE, _PARAFRASE.replace('íntegro', 'integro')),
    (_FONTE, _PARAFRASE.replace('objeto alfa', 'Objeto alfa')),
    (_FONTE, _PARAFRASE.replace('«estado» de «objeto alfa»', '«objeto alfa» de «estado»')),
    (_FONTE.replace(' é ', ' não é '), _PARAFRASE),
    (_FONTE.replace(' é ', ' pode ser '), _PARAFRASE),
    ('Talvez ' + _FONTE, _PARAFRASE),
    (_FONTE[:-1] + ' apenas após validação.', _PARAFRASE),
    (_FONTE + ' Isso vale somente no cenário simulado.', _PARAFRASE),
    ('A hipótese é que ' + _FONTE, _PARAFRASE),
    ('Se a medição estiver correta, ' + _FONTE, _PARAFRASE),
    ('O relatório nega: ' + _FONTE, _PARAFRASE),
    ('“' + _FONTE + '” é uma afirmação incorreta.', _PARAFRASE),
    (_FONTE, _PARAFRASE[:-1] + ' sempre.'),
    (_FONTE, _PARAFRASE + ' Logo, a ação é segura.'),
    (_FONTE, _PARAFRASE.replace(' é ', ' seria ')),
    (_FONTE.replace('«estado»', '« estado»'), _PARAFRASE),
    (_FONTE.replace('«estado»', '«es\ntado»'), _PARAFRASE),
    (_FONTE.replace('«estado»', '«es\u202etado»'), _PARAFRASE),
    (_FONTE.replace('«estado»', '««estado»»'), _PARAFRASE),
    ('O objeto alfa está íntegro.', 'O objeto alfa está intacto.'),
    (_FONTE, 'O valor do atributo «estado» de «objeto alfa» é «íntegro» ou «alterado».'),
])
def test_regra_integral_nao_remove_escopo_nem_inventa_sinonimo_ou_identidade(fonte, texto):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    r = revisar_suporte_autoria(texto, plano=_plano(texto, trecho=fonte), agora=1001)
    u = r.como_dict()['proposicoes'][0]
    assert u['estado'] != 'parafrase_estrutural_conferida'
    assert all('derivacao' not in f for f in u['fontes'])
    assert texto not in r.fala_realizada


@pytest.mark.parametrize('caso', ['valida', 'outra_fonte', 'expirada', 'nao_admitida', 'sem_referencia'])
def test_cada_fonte_precisa_do_proprio_apoio_atual_sem_emprestimo(caso):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    refs = [] if caso == 'sem_referencia' else ['https://fonte.test/registro', 'https://fonte.test/segunda']
    plano = _plano(_PARAFRASE, trecho=_FONTE, referencias=refs)
    base = plano['fundamentacao_factual']
    base['fontes'].append({'url': 'https://fonte.test/segunda', 'trecho': _PARAFRASE if caso != 'outra_fonte' else 'Registro independente.'})
    if caso == 'expirada':
        base.update(requer_evidencia_recente=True, evidencia_expira_em=999)
    elif caso == 'nao_admitida':
        base['confiavel'] = False
    r = revisar_suporte_autoria(_PARAFRASE, plano=plano, agora=1001)
    assert (r.como_dict()['proposicoes'][0]['estado'] == 'parafrase_estrutural_conferida') is (caso == 'valida')
    assert (_PARAFRASE in r.fala_realizada) is (caso == 'valida')


def test_derivacao_e_recalculada_do_conteudo_e_nao_do_certificado_proposto():
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano = _plano(_PARAFRASE, trecho=_FONTE)
    primeira = revisar_suporte_autoria(_PARAFRASE, plano=plano, agora=1001)
    assert primeira.como_dict()['proposicoes'][0]['estado'] == 'parafrase_estrutural_conferida'
    plano['fundamentacao_factual']['fontes'][0]['trecho'] = _FONTE.replace('íntegro', 'alterado')
    plano['revisao_suporte_autoria'] = primeira.como_dict()
    plano['prova_implicacao'] = True
    segunda = revisar_suporte_autoria(_PARAFRASE, plano=plano, agora=1001)
    assert segunda.como_dict()['proposicoes'][0]['estado'] == 'apoio_semantico_pendente'
    assert _PARAFRASE not in segunda.fala_realizada


def test_proposta_com_certificado_autoatribuido_nao_recebe_derivacao():
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano = _plano(_PARAFRASE, trecho=_FONTE)
    bruto = json.dumps({'fala': _PARAFRASE, 'suporte_proposicoes': [{'texto': _PARAFRASE,
        'fontes': ['https://fonte.test/registro'], 'derivacao': {'regra': 'simetria_valor_atributo_v1', 'aprovada': True}}]})
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria(ContratoPropostaPrincipal('t', 'Consulta?', bruto, True))
    r = revisar_suporte_autoria(_PARAFRASE, plano=plano, agora=1001)
    assert r.como_dict()['estado'] == 'declaracao_sem_cobertura'
    assert r.como_dict()['proposicoes'] == [] and r.prova_implicacao is False


def test_mistura_de_citacao_e_parafrase_preserva_a_ordem_das_unidades():
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    fonte2, parafrase2 = _formas('objeto beta', 'versão', 'A2')
    partes = [_PARAFRASE, 'O registro foi consultado à tarde.', parafrase2]
    urls = ['https://fonte.test/' + str(i) for i in range(3)]
    plano = _plano()
    bruto = json.dumps({'fala': ' '.join(partes), 'suporte_proposicoes': [{'texto': t, 'fontes': [u]} for t, u in zip(partes, urls)]})
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria(ContratoPropostaPrincipal('t', 'Consulta?', bruto, True))
    plano['fundamentacao_factual']['fontes'] = [{'url': u, 'trecho': t} for u, t in zip(urls, [_FONTE, partes[1], fonte2])]
    r = revisar_suporte_autoria(' '.join(partes), plano=plano, agora=1001)
    assert [u['estado'] for u in r.como_dict()['proposicoes']] == ['parafrase_estrutural_conferida', 'literal_integral_na_fonte', 'parafrase_estrutural_conferida']
    assert [r.fala_realizada.index(t) for t in partes] == sorted(r.fala_realizada.index(t) for t in partes)


def test_parafrase_sobre_autorizacao_reportada_nao_autoriza_efeito():
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    fonte, texto = _formas('proposta da IA', 'autorização operacional', 'sim')
    r = revisar_suporte_autoria(texto, plano=_plano(texto, trecho=fonte), agora=1001)
    assert r.como_dict()['proposicoes'][0]['estado'] == 'parafrase_estrutural_conferida'
    assert r.autoriza_execucao is False and r.como_dict()['pode_confirmar_fato_externo'] is False


@pytest.fixture(scope='module')
def parafrases_instaladas(tmp_path_factory):
    pasta = tmp_path_factory.mktemp('parafrases_instaladas')
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        assert not os.environ.get('LAYLAY_SONDA_ESCOPO_BASELINE')
        root = preparar_instalacao_isolada(Path(os.environ['LAYLAY_PARAFRASES_MEMORIA']))
        from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
        cliente_original = ClienteLLMRuntime.executar
        root._voz_runtime.falar = lambda *_a, **_k: False
        root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError('USB proibido'))
        root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError('TCP proibido'))
        estado, runtime = root._estado_compartilhado_runtime, root._resposta_ia_runtime
        contexto_original = runtime._contexto_getter
        textos, casos = [], []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        for dominio, entidade, atributo, valor in [('arquivo', 'arquivo alfa', 'estado', 'íntegro'),
                                                  ('iot', 'tomada delta', 'tensão nominal', '5 V')]:
            for modo in (False, True):
                for variante in ('valida', 'valor_divergente', 'condicional', 'referencia_ausente'):
                    estado.substituir('mental', criar_estado_mental_inicial())
                    estado.atualizar_campos('memoria_conversa', messages=[])
                    url = 'https://fonte.test/' + dominio + '/atributo'
                    fonte = f'O valor do atributo «{atributo}» de «{entidade}» é «{valor}».'
                    parafrase = f'«{valor}» é o valor do atributo «{atributo}» de «{entidade}».'
                    trecho = fonte
                    if variante == 'valor_divergente':
                        trecho = fonte.replace('«' + valor + '»', '«outro valor»')
                    elif variante == 'condicional':
                        trecho = fonte[:-1] + ' somente após validação independente.'
                    fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9, 'resumo': trecho,
                        'fonte': 'pesquisa_simulada', 'fontes': [{'url': url, 'trecho': trecho}]})
                    referencia = url if variante != 'referencia_ausente' else 'https://fonte.test/ausente'
                    pendente = 'Logo, qualquer operação com esse objeto é segura.'
                    dados = {'comandos': [], 'suporte_proposicoes': [{'texto': parafrase, 'fontes': [referencia]},
                                                                   {'texto': pendente, 'fontes': [url]}]}
                    enviados, efeitos = [], []
                    def gerar(self, requisicao):
                        enviados.append({'tipo': requisicao.tipo_chamada, 'payload': dict(requisicao.payload)})
                        return ResultadoModelo(json.dumps(dados, ensure_ascii=False), True)
                    ClienteLLMRuntime.executar = gerar
                    contexto = contexto_original()
                    marcar = contexto['marcar_inicio_turno']
                    def inicio_turno(*a, **k):
                        r = marcar(*a, **k)
                        mental = estado.retrato_dominio('mental')
                        plano = dict(mental['plano_turno_atual'])
                        plano['fundamentacao_factual'] = fundamento
                        estado.atualizar_campos('mental', fundamentacao_factual_turno=fundamento, plano_turno_atual=plano)
                        return r
                    contexto['marcar_inicio_turno'] = inicio_turno
                    contexto['usar_modo_rapido'] = lambda _t: modo
                    def impedir(*a, **k):
                        efeitos.append(True)
                        raise AssertionError('Apoio textual não autoriza execução')
                    contexto['contexto_dispatch_runtime'] = SimpleNamespace(montar=lambda: {'executar_intencao': impedir})
                    runtime._contexto_getter = lambda: contexto
                    inicio = len(textos)
                    runtime.processar('Pode explicar com outras palavras o que o registro informa?', origem='teste_parafrases')
                    caso = {'dominio': dominio, 'modo': modo, 'variante': variante, 'fonte': fonte, 'parafrase': parafrase,
                            'pendente': pendente, 'fundamento': fundamento, 'efeitos': efeitos, 'enviados': enviados,
                            'textos': textos[inicio:], 'mental': estado.retrato_dominio('mental')}
                    if os.environ.get('LAYLAY_PARAFRASES_QWEN_REAL') == '1' and variante == 'valida' and modo == (dominio == 'iot'):
                        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                        selecao, transportes = selecao_local(), []
                        requests.sessions.Session.request = criar_guarda_http_local(selecao, transportes, http_original)
                        ClienteLLMRuntime.executar = cliente_original
                        estado.substituir('mental', criar_estado_mental_inicial())
                        estado.atualizar_campos('memoria_conversa', messages=[])
                        corpo_prompt = root._composicao_contextos_ia_runtime.modelo_corporal_getter
                        root._composicao_contextos_ia_runtime.modelo_corporal_getter = None
                        inicio = len(textos)
                        try:
                            runtime.processar('Pode inverter a ordem da frase do registro, começando pelo valor e preservando o restante? Cite a URL do registro usado.', origem='teste_parafrases_qwen')
                        finally:
                            root._composicao_contextos_ia_runtime.modelo_corporal_getter = corpo_prompt
                        caso['real'] = {'selecao': selecao, 'transportes': transportes, 'textos': textos[inicio:],
                                        'mental': estado.retrato_dominio('mental')}
                    casos.append(caso)
        sys.__stdout__.write('PARAFRASES_INSTALADAS ' + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + '\n')
    ''')
    p = subprocess.run([sys.executable, '-c', codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_PARAFRASES_MEMORIA=str(pasta)),
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-5000:]
    dados = json.loads(next(l.removeprefix('PARAFRASES_INSTALADAS ') for l in p.stdout.splitlines() if l.startswith('PARAFRASES_INSTALADAS ')))
    if destino := os.environ.get('LAYLAY_EVIDENCIA_PARAFRASES'):
        with Path(destino).open('x', encoding='utf-8') as out:
            json.dump(dados, out, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize('indice', range(16))
def test_composicao_instalada_separa_parafrase_com_derivacao_e_conclusao_sem_apoio(parafrases_instaladas, indice):
    c = parafrases_instaladas[indice]
    plano = c['mental']['plano_turno_atual']
    assert plano['suporte_autoria_proposto']
    assert plano['fundamentacao_factual']['fontes'] == c['fundamento']['fontes']
    revisao = plano['ultima_verificacao']['revisao_suporte_autoria']
    unidades = revisao['proposicoes']
    if c['variante'] == 'referencia_ausente':
        declarada = json.loads(plano['suporte_autoria_proposto']['declaracao']['_dados_json'])
        assert declarada['estado'] == 'declaracao_ausente' and not unidades
        assert len(c['textos']) == 1 and c['parafrase'] not in c['textos'][0] and c['pendente'] not in c['textos'][0]
        assert not c['efeitos']
        assert all(a['status'] != 'confirmado_por_fonte' for a in c['mental']['registro_semantico']['alegacoes'] if a['autor'] == 'laylay')
        return
    assert len(unidades) == 2
    assert (unidades[0]['estado'] == 'parafrase_estrutural_conferida') is (c['variante'] == 'valida'), 'primeira fronteira: falta conferir a derivação integral da paráfrase'
    assert unidades[1]['estado'] == 'apoio_semantico_pendente'
    assert len(c['textos']) == 1 and c['pendente'] not in c['textos'][0]
    assert (c['parafrase'] in c['textos'][0]) is (c['variante'] == 'valida')
    if c['variante'] == 'valida':
        assert 'Parafraseando' in c['textos'][0]
        assert unidades[0]['fontes'][0]['derivacao']['apoio_estrutural_conferido'] is True
    assert not c['efeitos']
    assert revisao['semantica_verificada'] is revisao['prova_implicacao'] is revisao['autoriza_execucao'] is False
    assert all(a['status'] != 'confirmado_por_fonte' for a in c['mental']['registro_semantico']['alegacoes'] if a['autor'] == 'laylay')


@pytest.mark.skipif(os.environ.get('LAYLAY_PARAFRASES_QWEN_REAL') != '1', reason='Inferência local opcional')
@pytest.mark.parametrize('indice', [0, 12])
def test_qwen_real_publica_somente_apoio_conferido_pelo_host(parafrases_instaladas, indice):
    r = parafrases_instaladas[indice]['real']
    assert r['transportes'] and all(t.get('status') == 200 for t in r['transportes'])
    v = r['mental']['plano_turno_atual']['ultima_verificacao']
    revisao = v['revisao_suporte_autoria']
    assert revisao['proposicoes'] and r['textos'] == [v['fala']]
    assert revisao['semantica_verificada'] is revisao['prova_implicacao'] is False
    for u in revisao['proposicoes']:
        if u['estado'] == 'parafrase_estrutural_conferida':
            assert u['texto'] in r['textos'][0]
            assert all(f.get('estado') in {'parafrase_estrutural_conferida', 'literal_integral_na_fonte'} for f in u['fontes'])
        elif u['estado'] != 'literal_integral_na_fonte':
            assert u['texto'] not in r['textos'][0]
