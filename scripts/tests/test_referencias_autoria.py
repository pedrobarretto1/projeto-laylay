"""Inventário do host e ausência declarada não equivalem a prova de apoio."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest


URL = 'https://fonte.test/registro'
TRECHO = 'O valor do atributo «estado» de «arquivo alfa» é «íntegro».'


def _pacote(*, fontes=None, turno_correto=True, mostrar=True):
    from scripts.tests.test_interpretacao_operacional_por_ato import _prompt_para_turno
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    from mente_laylay.autonomia.contexto_resposta_ia import _formatar_fundamentacao_rapida
    texto = 'O que o registro disponível informa?'
    runtime, estado = _prompt_para_turno(texto)
    fontes = [{'url': URL, 'trecho': TRECHO}] if fontes is None else fontes
    fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9, 'resumo': TRECHO,
        'fonte': 'pesquisa_simulada', 'fontes': fontes})
    estado['fundamentacao_factual_turno'] = fundamento
    mensagens = ([{'role': 'system', 'content': _formatar_fundamentacao_rapida(fundamento)}] if mostrar else [])
    mensagens += [{'role': 'user', 'content': texto}]
    pacote = runtime.preparar_envio_modelo(mensagens, turno_id=estado['turno_atual']['id'] if turno_correto else 'outro')
    return pacote, estado


def _unidades(codec):
    return codec.response_format['json_schema']['schema']['properties']['suporte_proposicoes']['items']


def test_fonte_exposta_chega_como_inventario_finito_no_contrato_autoral():
    pacote, _ = _pacote()
    formas = _unidades(pacote.contrato_saida).get('anyOf', [])
    assert formas, 'primeira fronteira: fontes no texto sem inventário e sem decisão de citação no contrato'
    referencia = next(f for f in formas if f['properties']['fontes'].get('minItems') == 1)
    assert referencia['properties']['fontes']['items']['enum'] == [URL]
    assert any('REFERÊNCIAS DISPONÍVEIS' in m.get('content', '') for m in pacote.mensagens)
    assert pacote.mensagens[-1]['content'] == 'O que o registro disponível informa?'


@pytest.mark.parametrize('fontes', [[], ['https://fonte.test/inventada'], [URL, 'https://fonte.test/inventada']])
def test_codec_nao_aceita_omissao_silenciosa_ou_id_fora_do_inventario(fontes):
    pacote, _ = _pacote()
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'suporte_proposicoes': [{'texto': TRECHO, 'fontes': fontes}]}))


@pytest.mark.parametrize('motivo', ['nao_utilizada', 'insuficiente'])
def test_ausencia_explicita_e_preservada_sem_preencher_fonte_por_proximidade(motivo):
    from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
    from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    pacote, estado = _pacote()
    unidade = {'texto': TRECHO, 'fontes': [], 'sem_fonte': motivo}
    d = pacote.contrato_saida.decodificar_json(json.dumps({'suporte_proposicoes': [unidade]}))
    assert d['suporte_proposicoes'] == [unidade]
    suporte = capturar_suporte_autoria(ContratoPropostaPrincipal('t', 'Consulta?', json.dumps(d), True), fontes_no_contexto=(URL,))
    proposta = suporte.declaracao.como_dict()['proposicoes'][0]
    assert proposta['fontes'] == [] and proposta['sem_fonte_declarada'] == motivo
    plano = {'id': 't', 'texto_usuario': 'Consulta?', 'suporte_autoria_proposto': suporte,
             'fundamentacao_factual': estado['fundamentacao_factual_turno']}
    r = revisar_suporte_autoria(TRECHO, plano=plano)
    assert r.como_dict()['proposicoes'][0]['estado'] == 'sem_fontes_declaradas'
    assert TRECHO not in r.fala_realizada and r.prova_implicacao is False


@pytest.mark.parametrize('unidade', [
    {'texto': TRECHO, 'fontes': [URL], 'sem_fonte': 'nao_utilizada'},
    {'texto': TRECHO, 'fontes': [], 'sem_fonte': 'confirmada'},
    {'texto': TRECHO, 'fontes': [], 'sem_fonte': True},
    {'texto': TRECHO, 'fontes': [URL], 'semantica_verificada': True}])
def test_decisao_contraditoria_ou_autoaprovada_nao_vira_sucesso(unidade):
    pacote, _ = _pacote()
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({'suporte_proposicoes': [unidade]}))


def test_catalogo_nao_inventa_fontes_ocultas_nem_empresta_outra_ocorrencia():
    for opcoes in ({'turno_correto': False}, {'mostrar': False}, {'fontes': []}):
        pacote, _ = _pacote(**opcoes)
        if pacote.contrato_saida is not None:
            assert 'anyOf' not in _unidades(pacote.contrato_saida)
    fontes = [{'url': f'https://fonte.test/{i}', 'trecho': TRECHO, 'alvo': str(i)} for i in range(5)]
    pacote, _ = _pacote(fontes=fontes)
    formas = _unidades(pacote.contrato_saida).get('anyOf', [])
    assert formas
    referencia = next(f for f in formas if f['properties']['fontes'].get('minItems') == 1)
    assert referencia['properties']['fontes']['items']['enum'] == [f['url'] for f in fontes[:3]]


def test_reaplicar_contrato_na_recuperacao_preserva_inventario_e_validator():
    from scripts.tests.test_saida_tipificada_principal import preparador
    from mente_laylay.integracao.cliente_llm_runtime import ServicoModeloLLMRuntime
    from mente_laylay.integracao.registro_conversa_llm import PedidoModelo, ResultadoModelo
    pacote, _ = _pacote()
    vistos = []
    def responder(r):
        vistos.append(r.payload)
        return ResultadoModelo(json.dumps({'suporte_proposicoes': [{'texto': TRECHO, 'fontes': []}]}), True)
    servico = ServicoModeloLLMRuntime(preparador=preparador(), cliente=SimpleNamespace(executar=responder))
    r = servico.executar(PedidoModelo.criar(pacote.mensagens, tipo_chamada='reparo_comunicacao', contrato_saida=pacote.contrato_saida))
    assert vistos[0]['response_format'] == pacote.contrato_saida.response_format
    assert r.sucesso is False and r.rota == 'contrato_saida_invalido'


@pytest.mark.parametrize('caso,limitar', [('fonte_atual', True), ('sem_fonte', False), ('operacional', False)])
def test_fala_transformada_conserva_obrigacao_sem_emprestar_prova_ou_apagar_executor(caso, limitar):
    from scripts.tests.test_revisao_suporte_fontes import _plano
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano = _plano(referencias=[] if caso == 'sem_fonte' else None)
    if caso == 'sem_fonte':
        plano['fundamentacao_factual'] = {}
    elif caso == 'operacional':
        plano['requer_execucao'] = True
    nova = 'A autoria foi transformada antes da revisão.'
    r = revisar_suporte_autoria(nova, plano=plano)
    assert r.como_dict()['estado'] == 'fala_nao_vinculada'
    assert r.aplicar_limite is limitar, 'a perda de vínculo não elimina a obrigação de fonte da conversa'
    assert (r.fala_realizada != nova) is limitar
    assert r.prova_implicacao is False


def test_catalogo_preserva_o_validator_operacional_que_ja_existia():
    from scripts.tests.test_saida_tipificada_principal import envelope
    from mente_laylay.cognicao.saida_interpretacao_principal import criar_contrato_saida_interpretacao_principal
    from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral
    from mente_laylay.integracao.registro_conversa_llm import PacotePrompt
    texto, dados = envelope()
    base = criar_contrato_saida_interpretacao_principal(texto)
    codec = exigir_suporte_no_pacote_autoral(PacotePrompt((), contrato_saida=base), referencias_disponiveis=(URL,)).contrato_saida
    fala = dados.pop('fala')
    dados['suporte_proposicoes'] = [{'texto': fala, 'fontes': [URL]}]
    assert codec.decodificar_json(json.dumps(dados))['fala'] == fala
    dados['comandos'] = [{'intent': 'APP_OPEN', 'params': {}, 'confirmado': True}]
    with pytest.raises(ValueError):
        codec.decodificar_json(json.dumps(dados))


@pytest.fixture(scope='module')
def referencias_instaladas(tmp_path_factory):
    pasta = tmp_path_factory.mktemp('referencias_instaladas')
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        assert not os.environ.get('LAYLAY_SONDA_ESCOPO_BASELINE')
        root = preparar_instalacao_isolada(Path(os.environ['LAYLAY_REFERENCIAS_MEMORIA']))
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
                for variante in ('referencia', 'omissao', 'negativa_explicita', 'referencia_alheia'):
                    estado.substituir('mental', criar_estado_mental_inicial())
                    estado.atualizar_campos('memoria_conversa', messages=[])
                    url = 'https://fonte.test/' + dominio + '/atributo'
                    fonte = f'O valor do atributo «{atributo}» de «{entidade}» é «{valor}».'
                    fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9, 'resumo': fonte,
                        'fonte': 'pesquisa_simulada', 'fontes': [{'url': url, 'trecho': fonte}]})
                    unidade = {'texto': fonte, 'fontes': [url] if variante == 'referencia' else []}
                    if variante == 'negativa_explicita':
                        unidade['sem_fonte'] = 'insuficiente'
                    elif variante == 'referencia_alheia':
                        unidade['fontes'] = ['https://fonte.test/alheia']
                    enviados, efeitos = [], []
                    def gerar(self, requisicao):
                        enviados.append({'tipo': requisicao.tipo_chamada, 'payload': dict(requisicao.payload)})
                        dados = {'comandos': [], 'suporte_proposicoes': [unidade]}
                        if requisicao.tipo_chamada != 'principal':
                            dados['suporte_proposicoes'] = [{'texto': 'Não consegui conferir o apoio da resposta.', 'fontes': []}]
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
                        raise AssertionError('Referência proposta não autoriza efeito')
                    contexto['contexto_dispatch_runtime'] = SimpleNamespace(montar=lambda: {'executar_intencao': impedir})
                    runtime._contexto_getter = lambda: contexto
                    inicio = len(textos)
                    runtime.processar('O que o registro disponível informa?', origem='teste_referencias')
                    caso = {'dominio': dominio, 'modo': modo, 'variante': variante, 'fonte': fonte, 'url': url,
                            'fundamento': fundamento, 'efeitos': efeitos, 'enviados': enviados,
                            'textos': textos[inicio:], 'mental': estado.retrato_dominio('mental')}
                    if os.environ.get('LAYLAY_REFERENCIAS_QWEN_REAL') == '1' and variante == 'referencia' and modo == (dominio == 'iot'):
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
                            runtime.processar('O que o registro disponível informa?', origem='teste_referencias_qwen')
                        finally:
                            root._composicao_contextos_ia_runtime.modelo_corporal_getter = corpo_prompt
                        caso['real'] = {'selecao': selecao, 'transportes': transportes, 'textos': textos[inicio:],
                                        'mental': estado.retrato_dominio('mental')}
                    casos.append(caso)
        sys.__stdout__.write('REFERENCIAS_INSTALADAS ' + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + '\n')
    ''')
    p = subprocess.run([sys.executable, '-c', codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_REFERENCIAS_MEMORIA=str(pasta)),
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-5000:]
    dados = json.loads(next(l.removeprefix('REFERENCIAS_INSTALADAS ') for l in p.stdout.splitlines() if l.startswith('REFERENCIAS_INSTALADAS ')))
    if destino := os.environ.get('LAYLAY_EVIDENCIA_REFERENCIAS'):
        with Path(destino).open('x', encoding='utf-8') as out:
            json.dump(dados, out, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize('indice', range(16))
def test_composicao_negocia_ids_e_nao_converte_omissao_em_apoio(referencias_instaladas, indice):
    c = referencias_instaladas[indice]
    primeiro = c['enviados'][0]['payload']
    formas = primeiro['response_format']['json_schema']['schema']['properties']['suporte_proposicoes']['items'].get('anyOf', [])
    assert formas, 'primeira fronteira: autoria instalada admite omissão silenciosa apesar de fonte exposta'
    assert any(f['properties']['fontes'].get('items', {}).get('enum') == [c['url']] for f in formas)
    assert c['url'] in str(primeiro['messages'])
    for envio in c['enviados'][1:]:
        if envio['tipo'] not in {'reparo_factual', 'reparo_comunicacao', 'reparo_json', 'continuacao'}:
            continue
        esquema_reparo = envio['payload']['response_format']['json_schema']['schema']
        assert esquema_reparo['properties']['suporte_proposicoes']['items'].get('anyOf'), 'recuperação não pode enfraquecer a obrigação de declarar referências'
    plano = c['mental']['plano_turno_atual']
    declarada = json.loads(plano['suporte_autoria_proposto']['declaracao']['_dados_json'])
    assert len(c['textos']) == 1 and not c['efeitos']
    if c['variante'] in {'omissao', 'referencia_alheia'}:
        assert declarada['estado'] == 'declaracao_ausente'
        assert c['fonte'] not in c['textos'][0]
    else:
        assert declarada['estado'] == 'revisao_semantica_pendente'
        assert (c['fonte'] in c['textos'][0]) is (c['variante'] == 'referencia')
        if c['variante'] == 'negativa_explicita':
            assert declarada['proposicoes'][0]['fontes'] == []
            assert declarada['proposicoes'][0]['sem_fonte_declarada'] == 'insuficiente'
    assert all(a['status'] != 'confirmado_por_fonte' for a in c['mental']['registro_semantico']['alegacoes'] if a['autor'] == 'laylay')


@pytest.mark.skipif(os.environ.get('LAYLAY_REFERENCIAS_QWEN_REAL') != '1', reason='Inferência local opcional')
@pytest.mark.parametrize('indice', [0, 12])
def test_qwen_real_declara_referencia_ou_ausencia_sem_aprovacao_propria(referencias_instaladas, indice):
    r = referencias_instaladas[indice]['real']
    assert r['transportes'] and all(t.get('status') == 200 for t in r['transportes'])
    assert len(r['textos']) == 1
    plano = r['mental']['plano_turno_atual']
    declarada = json.loads(plano['suporte_autoria_proposto']['declaracao']['_dados_json'])
    assert declarada['estado'] == 'revisao_semantica_pendente'
    assert declarada['proposicoes']
    assert any(u['fontes'] for u in declarada['proposicoes'])
    for u in declarada['proposicoes']:
        assert u['fontes'] or u.get('sem_fonte_declarada') in {'nao_utilizada', 'insuficiente'}
    revisao = plano['ultima_verificacao']['revisao_suporte_autoria']
    assert revisao['prova_implicacao'] is revisao['semantica_verificada'] is False
    if revisao['estado'] == 'fala_nao_vinculada':
        assert 'suporte_declarado_sem_prova_semantica' in plano['ultima_verificacao']['problemas']
    for u in revisao['proposicoes']:
        if u['estado'] not in {'literal_integral_na_fonte', 'parafrase_estrutural_conferida'}:
            assert u['texto'] not in r['textos'][0]
