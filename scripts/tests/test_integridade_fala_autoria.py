"""Higiene não pode inferir truncamento pela última letra da autoria."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize('texto', [
    'O registro disponível informa que a tensão nominal da tomada delta é de 5 V.',
    'A corrente de saída informada pelo registro é de 2 A.',
    'O disco usado para guardar a cópia é o disco C.',
    'A classificação atribuída pelo relatório a esta nota é B.',
    'O identificador final publicado no registro é X.',
    'O autor citado pelo relatório se chama J. R.',
    'A vitamina registrada nesse campo do relatório é D.',
    'O token literal registrado depois desta sentença é H.',
])
@pytest.mark.parametrize('caminho', ['compartilhado', 'operacional', 'decodificacao'])
def test_higiene_preserva_termos_finais_sem_lista_de_unidades_ou_dominios(texto, caminho):
    from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais, limpar_fala_operacional
    from mente_laylay.personalidade.resposta_conversacional_runtime import RespostaConversacionalRuntime
    from mente_laylay.autonomia.higiene_resposta_ia import decodificar_resposta_da_ia
    if caminho == 'compartilhado':
        resultado = remover_residuos_operacionais(texto)
    elif caminho == 'operacional':
        resultado = limpar_fala_operacional(texto)
    else:
        runtime = RespostaConversacionalRuntime(namespace_getter=lambda: {}, estado_runtime_getter=lambda: None,
            fallback_fala='Sem resposta.')
        bruto = json.dumps({'fala': texto, 'comandos': []})
        decodificada = decodificar_resposta_da_ia(bruto, limpar_texto_fala_cb=runtime.limpar_texto_fala_ia)
        assert decodificada.extracao.metodo == 'json_objeto'
        assert decodificada.extracao.resposta_bruta == bruto and not decodificada.comandos
        resultado = decodificada.fala
    assert resultado == texto, 'primeira fronteira: higiene remove conteúdo só pela forma da última letra'


@pytest.mark.parametrize('residuo', ['[abrir arquivo]', '[comandos]: []', 'DADOS_ITEM_JSON: {"slot":"x"'])
def test_residuo_estrutural_continua_sendo_retirado_sem_apagar_o_termo_anterior(residuo):
    from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
    fonte = 'A tensão nominal informada no registro é de 5 V.'
    assert remover_residuos_operacionais(fonte + ' ' + residuo) == fonte


def test_quantidade_de_palavras_nao_decide_se_o_identificador_existe():
    from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
    for t in ['5 V.', 'O registro informa tensão nominal de 5 V.']:
        assert remover_residuos_operacionais(t) == t


def test_fragmento_sem_recibo_de_interrupcao_nao_e_cortado_como_fato():
    from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
    t = 'Dreamcore mistura lugares familiares com uma nostalgia estranha. H.'
    assert remover_residuos_operacionais(t) == t


@pytest.fixture(scope='module')
def integridade_instalada(tmp_path_factory):
    pasta = tmp_path_factory.mktemp('integridade_autoria_instalada')
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        assert not os.environ.get('LAYLAY_SONDA_ESCOPO_BASELINE')
        root = preparar_instalacao_isolada(Path(os.environ['LAYLAY_INTEGRIDADE_MEMORIA']))
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
        textos, casos, limpezas, preparacoes = [], [], [], []
        preparar_original = root._preparar_resposta_para_execucao_mente
        def preparar_observando(texto, bruto, **kwargs):
            limpar_original = kwargs['limpar_texto_fala_cb']
            def limpar_observando(t):
                r = limpar_original(t)
                limpezas.append({'antes': t, 'depois': r})
                return r
            kwargs['limpar_texto_fala_cb'] = limpar_observando
            r = preparar_original(texto, bruto, **kwargs)
            preparacoes.append({'bruto_recebido': bruto, 'fala_preparada': r['fala'],
                                'metodo': r['extracao_original'].metodo})
            return r
        root._preparar_resposta_para_execucao_mente = preparar_observando
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        for dominio, fonte in [
            ('iot', 'O registro disponível informa que a tensão nominal da tomada delta é de 5 V.'),
            ('arquivo', 'O disco usado para guardar a cópia é o disco C.'),
            ('nota', 'A classificação atribuída pelo relatório a esta nota é B.')]:
            for modo in (False, True):
                for variante in ('limpa', 'metadado'):
                    estado.substituir('mental', criar_estado_mental_inicial())
                    estado.atualizar_campos('memoria_conversa', messages=[])
                    url = 'https://fonte.test/' + dominio + '/integridade'
                    fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9, 'resumo': fonte,
                        'fonte': 'pesquisa_simulada', 'fontes': [{'url': url, 'trecho': fonte}]})
                    autoria = fonte + (' [comandos]: []' if variante == 'metadado' else '')
                    enviados, efeitos = [], []
                    def gerar(self, requisicao):
                        enviados.append({'tipo': requisicao.tipo_chamada, 'payload': dict(requisicao.payload)})
                        return ResultadoModelo(json.dumps({'comandos': [], 'suporte_proposicoes': [
                            {'texto': autoria, 'fontes': [url]}]}, ensure_ascii=False), True)
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
                        raise AssertionError('Autoria preservada não autoriza efeito')
                    contexto['contexto_dispatch_runtime'] = SimpleNamespace(montar=lambda: {'executar_intencao': impedir})
                    runtime._contexto_getter = lambda: contexto
                    inicio, il, ip = len(textos), len(limpezas), len(preparacoes)
                    runtime.processar('O que o registro disponível informa?', origem='teste_integridade_autoria')
                    caso = {'dominio': dominio, 'modo': modo, 'variante': variante, 'fonte': fonte, 'autoria': autoria,
                            'efeitos': efeitos, 'enviados': enviados, 'limpezas': limpezas[il:],
                            'preparacoes': preparacoes[ip:], 'textos': textos[inicio:], 'mental': estado.retrato_dominio('mental')}
                    if os.environ.get('LAYLAY_INTEGRIDADE_QWEN_REAL') == '1' and variante == 'limpa' and dominio in {'iot', 'arquivo'} and modo == (dominio == 'iot'):
                        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                        selecao, transportes = selecao_local(), []
                        requests.sessions.Session.request = criar_guarda_http_local(selecao, transportes, http_original)
                        ClienteLLMRuntime.executar = cliente_original
                        estado.substituir('mental', criar_estado_mental_inicial())
                        estado.atualizar_campos('memoria_conversa', messages=[])
                        corpo_prompt = root._composicao_contextos_ia_runtime.modelo_corporal_getter
                        root._composicao_contextos_ia_runtime.modelo_corporal_getter = None
                        inicio, il, ip = len(textos), len(limpezas), len(preparacoes)
                        try:
                            runtime.processar('O que o registro disponível informa?', origem='teste_integridade_qwen')
                        finally:
                            root._composicao_contextos_ia_runtime.modelo_corporal_getter = corpo_prompt
                        caso['real'] = {'selecao': selecao, 'transportes': transportes,
                            'limpezas': limpezas[il:], 'preparacoes': preparacoes[ip:],
                            'textos': textos[inicio:], 'mental': estado.retrato_dominio('mental')}
                    casos.append(caso)
        sys.__stdout__.write('INTEGRIDADE_INSTALADA ' + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + '\n')
    ''')
    p = subprocess.run([sys.executable, '-c', codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_INTEGRIDADE_MEMORIA=str(pasta)),
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert p.returncode == 0, p.stdout[-3500:] + p.stderr[-5000:]
    dados = json.loads(next(l.removeprefix('INTEGRIDADE_INSTALADA ') for l in p.stdout.splitlines() if l.startswith('INTEGRIDADE_INSTALADA ')))
    if destino := os.environ.get('LAYLAY_EVIDENCIA_INTEGRIDADE'):
        with Path(destino).open('x', encoding='utf-8') as out:
            json.dump(dados, out, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize('indice', range(12))
def test_composicao_localiza_primeira_alteracao_e_preserva_autoria_sem_reancorar(integridade_instalada, indice):
    c = integridade_instalada[indice]
    assert c['preparacoes'] and c['limpezas']
    recebido = json.loads(c['preparacoes'][0]['bruto_recebido'])
    assert recebido['fala'] == c['autoria']
    assert c['preparacoes'][0]['metodo'] == 'json_objeto'
    assert c['limpezas'][0]['antes'] == c['autoria']
    assert c['limpezas'][0]['depois'] == c['fonte'], 'primeira fronteira: callback compartilhado apaga termo final antes da revisão'
    assert c['preparacoes'][0]['fala_preparada'] == c['fonte']
    plano = c['mental']['plano_turno_atual']
    declarada = plano['suporte_autoria_proposto']
    assert declarada['fala_original'] == c['autoria']
    revisao = plano['ultima_verificacao']['revisao_suporte_autoria']
    assert len(c['textos']) == 1 and not c['efeitos']
    if c['variante'] == 'limpa':
        assert revisao['estado'] == 'revisao_limitada'
        assert revisao['proposicoes'][0]['estado'] == 'literal_integral_na_fonte'
        assert c['fonte'] in c['textos'][0]
    else:
        assert revisao['estado'] == 'fala_nao_vinculada'
        assert c['fonte'] not in c['textos'][0] and '[comandos]' not in c['textos'][0]
    assert revisao['semantica_verificada'] is revisao['prova_implicacao'] is revisao['autoriza_execucao'] is False


@pytest.mark.skipif(os.environ.get('LAYLAY_INTEGRIDADE_QWEN_REAL') != '1', reason='Inferência local opcional')
@pytest.mark.parametrize('indice', [2, 4])
def test_qwen_real_preserva_autoria_e_mantem_limites_de_apoio(integridade_instalada, indice):
    c = integridade_instalada[indice]
    r = c['real']
    assert r['transportes'] and all(t.get('status') == 200 for t in r['transportes'])
    assert r['limpezas'] and r['preparacoes'] and len(r['textos']) == 1
    assert r['limpezas'][0]['antes'] == r['limpezas'][0]['depois']
    plano = r['mental']['plano_turno_atual']
    assert plano['suporte_autoria_proposto']['fala_original'] == r['preparacoes'][0]['fala_preparada']
    revisao = plano['ultima_verificacao']['revisao_suporte_autoria']
    assert revisao['estado'] == 'revisao_limitada' and revisao['proposicoes']
    # A geração real pode citar, parafrasear ou declarar ausência de fonte.
    # O contrato de integridade não exige que o modelo copie a fonte.
    literais = {p['texto'] for p in revisao['proposicoes'] if p['estado'] == 'literal_integral_na_fonte'}
    for p in revisao['proposicoes']:
        assert p['pode_confirmar_fato_externo'] is False
        if p['texto'] in literais:
            assert p['texto'] == c['fonte'] and p['texto'] in r['textos'][0]
        else:
            assert p['texto'] not in r['textos'][0]
    assert not c['efeitos']
    assert revisao['semantica_verificada'] is revisao['pode_confirmar_fato_externo'] is False
    assert revisao['prova_implicacao'] is revisao['autoriza_execucao'] is False
