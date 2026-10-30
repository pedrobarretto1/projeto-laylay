"""Atos discursivos são conferidos pela fonte atual, sem prova de efeito."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from scripts.tests.test_ato_social_conferido import preparar


@pytest.mark.parametrize('usuario,social,tipo', [
    ('Oi, qual disco guarda a cópia?', 'Olá!', 'saudacao'),
    ('Bom dia, qual disco guarda a cópia?', 'Bom dia!', 'saudacao'),
    ('Olá!', 'Oi!', 'saudacao'),
    ('Obrigado, Lay', 'Por nada.', 'agradecimento'),
    ('Valeu!', 'De nada!', 'agradecimento'),
    ('Estou bem, qual disco guarda a cópia?', 'Que bom saber!', 'estado_pessoal'),
    ('EU ESTOU FELIZ, qual disco guarda a cópia?', 'Entendo que você está feliz.', 'estado_pessoal'),
    ('Boa tarde, Lay!', 'Olá.', 'saudacao'),
    ('Boa noite, qual disco guarda a cópia?', 'Boa noite.', 'saudacao'),
    ('Obrigada!', 'Disponha!', 'agradecimento'),
    ('VLW', 'Imagina.', 'agradecimento'),
])
def test_conferencia_usa_ato_reconhecido_e_fonte_original(usuario, social, tipo):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano, fala, fato = preparar(texto=usuario, social=social)
    assert tipo in plano['contrato_fala']['atos'], 'fronteira anterior: ato precisa já estar reconhecido'
    revisao = revisar_suporte_autoria(fala, plano=plano)
    unidade = revisao.como_dict()['proposicoes'][0]
    assert unidade['estado'] == 'ato_social_conferido'
    prova = unidade['conferencia_ato_social']
    i, j = prova['fonte']['intervalo']
    assert usuario[i:j] == prova['fonte']['texto']
    assert prova['ato_conferido'] is True and prova['estado_real_verificado'] is False
    assert prova['pode_confirmar_fato_externo'] is prova['autoriza_execucao'] is False
    assert revisao.fala_realizada.startswith(social) and fato in revisao.fala_realizada


@pytest.fixture(scope='module')
def atos_instalados(tmp_path_factory, request):
    pasta = tmp_path_factory.mktemp('atos_discursivos')
    modo_prova = getattr(request, 'param', 'principal')
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, re, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(Path(os.environ['LAYLAY_ATOS_MEMORIA']))
        from mente_laylay.integracao.cliente_llm_runtime import ClienteLLMRuntime
        from mente_laylay.integracao.registro_conversa_llm import ResultadoModelo
        from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
        from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
        original = ClienteLLMRuntime.executar
        root._voz_runtime.falar = lambda *_a, **_k: False
        root._rosto_oled_runtime.abrir_serial = lambda *_a: (_ for _ in ()).throw(AssertionError('USB proibido'))
        root._rosto_oled_runtime.abrir_tcp = lambda *_a: (_ for _ in ()).throw(AssertionError('TCP proibido'))
        estado, runtime = root._estado_compartilhado_runtime, root._resposta_ia_runtime
        contexto_original = runtime._contexto_getter
        textos, casos, preparadas = [], [], []
        preparar_original = root._preparar_resposta_para_execucao_mente
        def observar(*a, **k):
            r = preparar_original(*a, **k); preparadas.append(r); return r
        root._preparar_resposta_para_execucao_mente = observar
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        for dominio, fonte, pergunta in [
            ('arquivo', 'O disco usado para guardar a cópia é o disco C.', 'qual disco guarda a cópia?'),
            ('iot', 'A tensão nominal informada pelo registro é de 5 V.', 'qual é a tensão nominal informada?')]:
            if os.environ.get('LAYLAY_ATOS_TRECHO_INTEGRAL') == '1':
                fonte += (' O registro distingue o valor descrito de qualquer verificação externa.'
                    ' Sua finalidade é documentar a informação disponível na consulta.'
                    ' A origem e o contexto do dado precisam permanecer associados à descrição.'
                    ' O relato preserva a perspectiva da fonte consultada e seus limites.'
                    ' Esta descrição não comprova execução nem autoriza alteração.')
                assert 300 < len(fonte) <= 500, len(fonte)
            for modo in (False, True):
                for tipo, entrada, social in [('saudacao', 'Oi, ' + pergunta, 'Olá!'),
                    ('periodo', 'Bom dia, ' + pergunta, 'Bom dia!'),
                    ('agradecimento', 'Obrigado, Lay', 'Por nada.')]:
                    estado.substituir('mental', criar_estado_mental_inicial())
                    estado.atualizar_campos('memoria_conversa', messages=[])
                    url = 'https://fonte.test/' + dominio + '/ato-discursivo'
                    fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9, 'resumo': fonte,
                        'fonte': 'pesquisa_simulada', 'fontes': [{'url': url, 'trecho': fonte}]})
                    enviados, efeitos, transportes = [], [], []
                    selecionado_real = ((modo and tipo == 'saudacao')
                        if os.environ.get('LAYLAY_ATOS_TRECHO_INTEGRAL') == '1'
                        else ((dominio == 'arquivo' and not modo and tipo == 'saudacao') or
                              (dominio == 'iot' and modo and tipo == 'periodo')))
                    real = (os.environ.get('LAYLAY_ATOS_QWEN_REAL') == '1'
                        and os.environ.get('LAYLAY_ATOS_REPARO_TOTAL') != '1' and
                        (os.environ.get('LAYLAY_ATOS_TRECHO_INTEGRAL') != '1'
                         or os.environ.get('LAYLAY_ATOS_QWEN_TRECHO_REAL') == '1')
                        and selecionado_real)
                    if real:
                        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                        requests.sessions.Session.request = criar_guarda_http_local(selecao_local(), transportes, http_original)
                    def gerar(self, req):
                        texto_fonte = fonte
                        if os.environ.get('LAYLAY_ATOS_TRECHO_INTEGRAL') == '1':
                            expostos = [m for m in req.payload['messages'] if m['role'] == 'system'
                                and re.search(r'\(' + re.escape(url) + r'\): ([^\n]+)', m['content'])]
                            if not expostos:
                                enviados.append({'tipo': req.tipo_chamada, 'payload': dict(req.payload),
                                    'diagnostico': 'fonte_individual_ausente_no_payload'})
                                raise AssertionError('fonte individual ausente no envio')
                            texto_fonte = re.search(r'\(' + re.escape(url) + r'\): ([^\n]+)', expostos[0]['content']).group(1)
                        unidades = [{'texto': social, 'fontes': [], 'sem_fonte': 'nao_utilizada'}]
                        if tipo != 'agradecimento': unidades.append({'texto': texto_fonte, 'fontes': [url]})
                        if req.payload.get('response_format', {}).get('json_schema', {}).get('name') == 'autoria_por_ato_v5':
                            ramos = req.payload['response_format']['json_schema']['schema']['properties']['suporte_proposicoes']['items']['anyOf']
                            ramo_social = next(r for r in ramos if r['properties']['texto'].get('enum'))
                            ramo_factual = next(r for r in ramos if not r['properties']['texto'].get('enum'))
                            unidades[0]['ato'] = ramo_social['properties']['ato']['const']
                            unidades[1]['ato'] = ramo_factual['properties']['ato']['const']
                        if (os.environ.get('LAYLAY_ATOS_REPARO_TOTAL') == '1' and dominio == 'arquivo'
                            and not modo and tipo == 'saudacao' and req.tipo_chamada == 'principal'):
                            unidades[1].update(texto='Hoje estou comendo um bolo que o Pedro me deu.',
                                               fontes=[], sem_fonte='nao_utilizada')
                        r = (original(self, req) if real else ResultadoModelo(json.dumps({
                            'comandos': [], 'suporte_proposicoes': unidades}, ensure_ascii=False), True))
                        enviados.append({'tipo': req.tipo_chamada, 'resposta': str(r.texto), 'payload': dict(req.payload)})
                        return r
                    ClienteLLMRuntime.executar = gerar
                    contexto = contexto_original()
                    marcar = contexto['marcar_inicio_turno']
                    def iniciar(*a, **k):
                        r = marcar(*a, **k)
                        mental = estado.retrato_dominio('mental')
                        plano = dict(mental['plano_turno_atual']); plano['fundamentacao_factual'] = fundamento
                        estado.atualizar_campos('mental', fundamentacao_factual_turno=fundamento, plano_turno_atual=plano)
                        return r
                    contexto['marcar_inicio_turno'] = iniciar
                    contexto['usar_modo_rapido'] = lambda _t: modo
                    def impedir(*a, **k):
                        efeitos.append(True); raise AssertionError('ato discursivo não autoriza efeito')
                    contexto['contexto_dispatch_runtime'] = SimpleNamespace(montar=lambda: {'executar_intencao': impedir})
                    runtime._contexto_getter = lambda: contexto
                    corpo = root._composicao_contextos_ia_runtime.modelo_corporal_getter
                    if real: root._composicao_contextos_ia_runtime.modelo_corporal_getter = None
                    inicio, ip = len(textos), len(preparadas)
                    try: runtime.processar(entrada, origem='teste_atos_discursivos')
                    finally: root._composicao_contextos_ia_runtime.modelo_corporal_getter = corpo
                    casos.append({'dominio': dominio, 'modo': modo, 'tipo': tipo, 'entrada': entrada,
                        'social': social, 'fonte': fonte, 'real': real, 'enviados': enviados,
                        'efeitos': efeitos, 'transportes': transportes, 'preparadas': preparadas[ip:],
                        'textos': textos[inicio:], 'mental': estado.retrato_dominio('mental')})
        sys.__stdout__.write('ATOS ' + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + '\n')
    ''')
    r = subprocess.run([sys.executable, '-c', codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_ATOS_MEMORIA=str(pasta),
                 LAYLAY_ATOS_REPARO_TOTAL='1' if modo_prova == 'reparo_total' else '0',
                 LAYLAY_ATOS_TRECHO_INTEGRAL='1' if modo_prova == 'trecho_integral' else '0'),
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert r.returncode == 0, r.stdout[-2500:] + r.stderr[-5000:]
    dados = json.loads(next(l.removeprefix('ATOS ') for l in r.stdout.splitlines() if l.startswith('ATOS ')))
    if destino := os.environ.get('LAYLAY_EVIDENCIA_ATOS'):
        caminho = Path(destino)
        if modo_prova != 'principal':
            caminho = caminho.with_name(caminho.stem + '_' + modo_prova + caminho.suffix)
        with caminho.open('x', encoding='utf-8') as f: json.dump(dados, f, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize('indice', range(12))
def test_composicao_confere_ato_ja_reconhecido_sem_apagar_a_resposta(atos_instalados, indice):
    caso = atos_instalados[indice]
    plano = caso['mental']['plano_turno_atual']
    tipo = 'saudacao' if caso['tipo'] == 'periodo' else caso['tipo']
    assert tipo in plano['contrato_fala']['atos']
    autorais = [e for e in caso['enviados'] if e['tipo'] in {'principal', 'reparo_comunicacao', 'reparo_factual'}
        and any(m.get('role') == 'user' and m.get('content') == caso['entrada'] for m in e['payload']['messages'])]
    assert len(autorais) == 1 and autorais[0]['tipo'] == 'principal'
    assert not any(e['tipo'] in {'reparo_comunicacao', 'reparo_factual'} for e in caso['enviados'])
    assert caso['preparadas'][0]['fala']
    if not caso['real']:
        assert caso['preparadas'][0]['fala'].startswith(caso['social'])
    revisao = plano['ultima_verificacao']['revisao_suporte_autoria']
    sociais = [p for p in revisao['proposicoes'] if p['estado'] == 'ato_social_conferido']
    assert sociais, 'primeira fronteira: ato reconhecido é retirado como se exigisse fonte factual externa'
    assert len(caso['textos']) == 1 and not caso['efeitos']
    assert caso['textos'][0].startswith(sociais[0]['texto'])
    if tipo != 'agradecimento':
        assert any(p['estado'] == 'literal_integral_na_fonte' for p in revisao['proposicoes'])
        assert caso['fonte'] in caso['textos'][0]
    assert revisao['pode_confirmar_fato_externo'] is revisao['autoriza_execucao'] is False


@pytest.mark.skipif(os.environ.get('LAYLAY_ATOS_QWEN_REAL') != '1', reason='Inferência local opcional')
@pytest.mark.parametrize('indice', [0, 10])
def test_qwen_real_tem_ato_e_fato_conferidos_independentemente(atos_instalados, indice):
    caso = atos_instalados[indice]
    assert caso['real'] and caso['transportes']
    assert all(t['status'] == 200 for t in caso['transportes'])
    assert all(json.loads(t['resposta_http'])['choices'][0]['finish_reason'] == 'stop' for t in caso['transportes'])
    revisao = caso['mental']['plano_turno_atual']['ultima_verificacao']['revisao_suporte_autoria']
    assert any(p['estado'] == 'ato_social_conferido' for p in revisao['proposicoes'])
    assert any(p['estado'] == 'literal_integral_na_fonte' for p in revisao['proposicoes'])
    assert caso['fonte'] in caso['textos'][0] and not caso['efeitos']


@pytest.mark.parametrize('indice', [0, 1, 3, 4, 6, 7, 9, 10])
def test_envio_instalado_vincula_unidades_aos_atos_da_mesma_ocorrencia(atos_instalados, indice):
    caso = atos_instalados[indice]
    principal = next(e for e in caso['enviados'] if e['tipo'] == 'principal')
    itens = principal['payload']['response_format']['json_schema']['schema']['properties']['suporte_proposicoes']
    assert all('ato' in r['required'] for r in itens['items']['anyOf']), 'primeira fronteira: plano não negocia alvo de cada unidade'
    revisao = caso['mental']['plano_turno_atual']['ultima_verificacao']['revisao_suporte_autoria']
    assert len(revisao['proposicoes']) >= 2
    assert revisao['proposicoes'][0]['estado'] == 'ato_social_conferido'
    assert revisao['proposicoes'][0]['vinculo_ato']['realizacao_social_conferida'] is True
    assert all(p.get('vinculo_ato', {}).get('fonte_atual_identificada') is True for p in revisao['proposicoes'])
    assert len(caso['textos']) == 1 and not caso['efeitos']


@pytest.mark.parametrize('atos_instalados', ['reparo_total'], indirect=True)
def test_reparo_total_instalado_preserva_alvos_e_revisa_suporte_proprio(atos_instalados):
    caso = atos_instalados[0]
    autorais = [e for e in caso['enviados'] if e['tipo'] in {'principal', 'reparo_factual', 'reparo_comunicacao'}]
    assert [e['tipo'] for e in autorais] == ['principal', 'reparo_factual']
    assert all(e['payload']['response_format']['json_schema']['name'] == 'autoria_por_ato_v5' for e in autorais)
    ids = []
    for e in autorais:
        ids.append({r['properties']['ato']['const'] for r in e['payload']['response_format']['json_schema']['schema']['properties']['suporte_proposicoes']['items']['anyOf']})
    assert ids[0] == ids[1]
    plano = caso['mental']['plano_turno_atual']
    assert plano['autoria_revisada_proposta']['partes'][0]['fala_original'] == caso['preparadas'][0]['fala']
    revisao = plano['ultima_verificacao']['revisao_suporte_autoria']
    assert [p['estado'] for p in revisao['proposicoes']] == ['ato_social_conferido', 'literal_integral_na_fonte']
    assert all(p['vinculo_ato']['fonte_atual_identificada'] is True for p in revisao['proposicoes'])
    assert len(caso['textos']) == 1 and caso['fonte'] in caso['textos'][0] and not caso['efeitos']


@pytest.mark.parametrize('atos_instalados', ['trecho_integral'], indirect=True)
@pytest.mark.parametrize('indice', [0, 1, 3, 4, 6, 7, 9, 10])
def test_composicao_entrega_mesmo_trecho_integral_ao_autor_e_revisor(atos_instalados, indice):
    caso = atos_instalados[indice]
    principal = next(e for e in caso['enviados'] if e['tipo'] == 'principal')
    assert 300 < len(caso['fonte']) <= 500
    assert any(caso['fonte'] in m['content'] for m in principal['payload']['messages'] if m['role'] == 'system'), 'primeira fronteira: composição entrega prefixo, revisão exige fonte inteira'
    revisao = caso['mental']['plano_turno_atual']['ultima_verificacao']['revisao_suporte_autoria']
    assert [p['estado'] for p in revisao['proposicoes']] == ['ato_social_conferido', 'literal_integral_na_fonte']
    assert revisao['fontes_lidas'][0]['trecho'] == caso['fonte']
    assert len(caso['textos']) == 1 and caso['fonte'] in caso['textos'][0]
    assert not caso['efeitos'] and revisao['autoriza_execucao'] is False


@pytest.mark.skipif(os.environ.get('LAYLAY_ATOS_QWEN_TRECHO_REAL') != '1', reason='Inferência com trecho longo opcional')
@pytest.mark.parametrize('atos_instalados', ['trecho_integral'], indirect=True)
@pytest.mark.parametrize('indice', [3, 9])
def test_qwen_recebe_snapshot_integral_com_ressalvas(atos_instalados, indice):
    caso = atos_instalados[indice]
    assert caso['real'] and caso['transportes']
    assert 300 < len(caso['fonte']) <= 500
    for t in caso['transportes']:
        assert t['status'] == 200 and json.loads(t['resposta_http'])['choices'][0]['finish_reason'] == 'stop'
        assert any(caso['fonte'] in m['content'] for m in t['payload']['messages'] if m['role'] == 'system')
    assert len(caso['textos']) == 1 and not caso['efeitos']
    revisao = caso['mental']['plano_turno_atual']['ultima_verificacao']['revisao_suporte_autoria']
    assert revisao['proposicoes'] and revisao['autoriza_execucao'] is False
    # Receber a fonte inteira não certifica a redação produzida pelo modelo.
    for p in revisao['proposicoes']:
        assert p['pode_confirmar_fato_externo'] is False


@pytest.mark.parametrize('usuario,social', [
    ('Oi, qual disco guarda a cópia?', 'Olá, seu disco está íntegro.'),
    ('Oi, qual disco guarda a cópia?', 'Oi! Abri o arquivo.'),
    ('Oi, qual disco guarda a cópia?', 'Olá, você parece triste.'),
    ('Oi, qual disco guarda a cópia?', 'Olá! Precisa de algo?'),
    ('Oi, qual disco guarda a cópia?', '“Olá!”'),
    ('Oi, qual disco guarda a cópia?', 'Não vou dizer oi.'),
    ('Bom dia, qual disco guarda a cópia?', 'Boa noite!'),
    ('Obrigado, Lay', 'Por nada, salvei o arquivo.'),
    ('Obrigado, Lay', 'Por nada, sei que funcionou.'),
    ('Obrigado, Lay', 'Obrigado, você me ajudou.'),
    ('Obrigado, Lay', 'Foi um prazer executar seu pedido.'),
    ('Obrigado, Lay', 'De nada! Quer continuar?'),
    ('"Oi", qual disco guarda a cópia?', 'Olá!'),
    ('Se eu disser oi, qual disco guarda a cópia?', 'Olá!'),
    ('Ela disse oi, qual disco guarda a cópia?', 'Olá!'),
    ('Não diga oi, qual disco guarda a cópia?', 'Olá!'),
    ('"Obrigado, Lay"', 'Por nada.'),
    ('Obrigado pelo arquivo salvo', 'Por nada.'),
    ('Qual disco guarda a cópia?', 'Olá!'),
    ('Oi, estou mal; qual disco guarda a cópia?', 'Que bom saber!'),
])
def test_ato_nao_certifica_oracao_extra_moldura_ou_outro_papel(usuario, social):
    from mente_laylay.cognicao.validacao_contrato_fala import conferir_ato_social
    plano, _, _ = preparar(texto=usuario, social=social)
    assert conferir_ato_social(social, plano=plano) is None


@pytest.mark.parametrize('mutacao', ['turno', 'ancora', 'origem', 'sem_ato', 'evento', 'comando',
    'ordem', 'segmento', 'texto_ausente', 'fonte_citada'])
def test_proposta_nao_substitui_fonte_atual_do_ato(mutacao):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    plano, fala, _ = preparar(texto='Oi, qual disco guarda a cópia?', social='Olá!')
    contrato = plano['contrato_fala']
    if mutacao == 'turno': contrato['turno_id'] = 'antigo'
    if mutacao == 'ancora': contrato['roteiro_concreto']['ancora_literal'] = 'outra utterance'
    if mutacao == 'origem': contrato['origem'] = 'llm'
    if mutacao == 'sem_ato': contrato['atos'] = ['pergunta']
    if mutacao == 'evento': plano['natureza_entrada'] = 'evento'
    if mutacao == 'comando': plano['comandos'] = [{'intent': 'APP_OPEN'}]
    if mutacao == 'ordem': plano['atos'][0]['ordem'] = 1
    if mutacao == 'segmento': plano['atos'][0]['tipo'] = 'pergunta'
    if mutacao == 'texto_ausente': plano['atos'][0]['texto'] = 'olá'
    if mutacao == 'fonte_citada': plano['texto_usuario'] = '"Oi", qual disco guarda a cópia?'
    plano['conferencia_ato_social'] = {'ato_conferido': True, 'autoriza_execucao': True}
    revisao = revisar_suporte_autoria(fala, plano=plano)
    assert not any(p['estado'] == 'ato_social_conferido' for p in revisao.como_dict()['proposicoes'])


@pytest.mark.parametrize('usuario,social', [
    ('Oi, qual disco guarda a cópia?', 'Olá!'),
    ('Obrigado, Lay', 'Por nada.'),
])
def test_ato_nao_empresta_suporte_nem_ignora_referencia_invalida(usuario, social):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    from mente_laylay.cognicao.suporte_autoria import montar_autoria_revisada
    from scripts.tests.test_autoria_reescritas import emissao
    inventada = 'A cópia está íntegra porque o disco nunca falha.'
    plano, fala, _ = preparar(texto=usuario, social=social, fato=inventada)
    revisao = revisar_suporte_autoria(fala, plano=plano)
    a, f = revisao.como_dict()['proposicoes']
    assert a['estado'] == 'ato_social_conferido'
    assert f['estado'] == 'apoio_semantico_pendente' and inventada not in revisao.fala_realizada
    assert 'apoio não consegui verificar' in revisao.fala_realizada
    parte = emissao(social, ['https://fonte.test/alheia'], turno=str(plano['id']), consulta=usuario)
    plano['autoria_revisada_proposta'] = montar_autoria_revisada('principal', social, (parte,))
    revisao = revisar_suporte_autoria(social, plano=plano)
    assert revisao.como_dict()['proposicoes'][0]['estado'] == 'fonte_nao_resolvida'
    assert social not in revisao.fala_realizada
