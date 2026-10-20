"""Reescritas aceitas conservam sua proposta de suporte, sem aprová-la."""
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


@pytest.fixture(scope='module')
def reescritas_instaladas(tmp_path_factory, request):
    pasta = tmp_path_factory.mktemp('autoria_reescritas')
    codigo = textwrap.dedent(r'''
        import dataclasses, json, os, sys
        from pathlib import Path
        from types import SimpleNamespace
        import requests
        http_original = requests.sessions.Session.request
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(Path(os.environ['LAYLAY_REESCRITAS_MEMORIA']))
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
            r = preparar_original(*a, **k)
            preparadas.append(r)
            return r
        root._preparar_resposta_para_execucao_mente = observar
        root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda t, *_a, **_k: textos.append(t) or True)
        for dominio, fonte, pergunta in [
            ('arquivo', 'O disco usado para guardar a cópia é o disco C.', 'qual disco guarda a cópia?'),
            ('iot', 'A tensão nominal informada pelo registro é de 5 V.', 'qual é a tensão nominal informada?')]:
            for modo in (False, True):
                for caminho in ('total', 'mescla'):
                    estado.substituir('mental', criar_estado_mental_inicial())
                    estado.atualizar_campos('memoria_conversa', messages=[])
                    estado_relato = os.environ.get('LAYLAY_ESTADO_SOCIAL_TESTE', 'bem')
                    texto = ('estou ' + estado_relato + ', ' if caminho == 'mescla' else '') + pergunta
                    url = 'https://fonte.test/' + dominio + '/reescrita'
                    fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9, 'resumo': fonte,
                        'fonte': 'pesquisa_simulada', 'fontes': [{'url': url, 'trecho': fonte}]})
                    inicial = fonte if caminho == 'mescla' else 'Hoje estou comendo um bolo que o Pedro me deu.'
                    reparo = 'Que bom saber!' if caminho == 'mescla' else fonte
                    enviados, efeitos = [], []
                    real = (modo == (dominio == 'iot') and (
                        (os.environ.get('LAYLAY_REESCRITAS_QWEN_REAL') == '1' and caminho == 'total')
                        or (os.environ.get('LAYLAY_ATO_SOCIAL_QWEN_REAL') == '1' and caminho == 'mescla')))
                    transportes = []
                    if real:
                        from scripts.analises.sonda_escopo_geracao_real import selecao_local, criar_guarda_http_local
                        requests.sessions.Session.request = criar_guarda_http_local(selecao_local(), transportes, http_original)
                    def gerar(self, req):
                        principal = req.tipo_chamada == 'principal'
                        fala = inicial if principal else reparo
                        fontes = [url] if (principal and caminho == 'mescla') or (not principal and caminho == 'total') else []
                        unidade = {'texto': fala, 'fontes': fontes}
                        if not fontes: unidade['sem_fonte'] = 'nao_utilizada'
                        esquema = req.payload.get('response_format', {}).get('json_schema', {}).get('schema', {})
                        item = esquema.get('properties', {}).get('suporte_proposicoes', {}).get('items', {})
                        if not any('sem_fonte' in f.get('properties', {}) for f in item.get('anyOf', [item])):
                            unidade.pop('sem_fonte', None)
                        r = (original(self, req) if real and not principal else
                             ResultadoModelo(json.dumps({'comandos': [], 'suporte_proposicoes': [unidade]}, ensure_ascii=False), True))
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
                        efeitos.append(True)
                        raise AssertionError('Proposta de suporte não autoriza efeito')
                    contexto['contexto_dispatch_runtime'] = SimpleNamespace(montar=lambda: {'executar_intencao': impedir})
                    runtime._contexto_getter = lambda: contexto
                    corpo = root._composicao_contextos_ia_runtime.modelo_corporal_getter
                    if real: root._composicao_contextos_ia_runtime.modelo_corporal_getter = None
                    inicio, ip = len(textos), len(preparadas)
                    try:
                        runtime.processar(texto, origem='teste_autoria_reescritas')
                    finally:
                        root._composicao_contextos_ia_runtime.modelo_corporal_getter = corpo
                    casos.append({'dominio': dominio, 'modo': modo, 'caminho': caminho, 'fonte': fonte,
                        'inicial': inicial, 'reparo': reparo, 'real': real, 'transportes': transportes,
                        'enviados': enviados, 'efeitos': efeitos, 'preparadas': preparadas[ip:],
                        'textos': textos[inicio:], 'mental': estado.retrato_dominio('mental')})
        guardas = []
        autoria = preparadas[-1].get('autoria_revisada_proposta')
        if autoria is not None:
            from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
            principal = ContratoPropostaPrincipal(turno_id=autoria.turno_id,
                texto_usuario=autoria.texto_usuario,
                resposta_bruta=preparadas[-1]['extracao_original'].resposta_bruta, sucesso_modelo=True)
            writer = root._composicao_turno_runtime.atualizar_proposta
            positivo = writer('resposta_planejada', principal, fala=autoria.fala_original,
                             autoria_revisada_proposta=autoria)
            assert positivo and positivo.get('autoria_revisada_proposta') == autoria
            for variante in ('principal_alheia', 'turno_alheio', 'consulta_alheia', 'fala_alterada', 'dicionario'):
                proposta, revisada, fala = principal, autoria, autoria.fala_original
                if variante == 'principal_alheia': proposta = dataclasses.replace(principal, resposta_bruta='{}')
                if variante in {'turno_alheio', 'consulta_alheia'}:
                    campos = {'turno_id': 'antigo'} if variante == 'turno_alheio' else {'texto_usuario': 'Outra consulta?'}
                    partes = tuple(dataclasses.replace(p, **campos) for p in autoria.partes)
                    revisada = dataclasses.replace(autoria, partes=partes, **campos)
                if variante == 'fala_alterada': fala = 'Um conteúdo diferente do que foi autorado.'
                if variante == 'dicionario': revisada = dataclasses.asdict(autoria)
                antes = estado.retrato_dominio('mental')
                resultado = writer('resposta_planejada', proposta, fala=fala, autoria_revisada_proposta=revisada)
                guardas.append({'variante': variante, 'recusada': resultado == {},
                               'estado_preservado': antes == estado.retrato_dominio('mental')})
        casos[-1]['guardas'] = guardas
        if autoria is not None:
            renovado = writer('resposta_planejada', principal, fala='Uma nova resposta sem reescrita.')
            casos[-1]['autoria_antiga_descartada'] = bool(renovado and 'autoria_revisada_proposta' not in renovado)
        sys.__stdout__.write('REESCRITAS ' + json.dumps(casos, ensure_ascii=False, default=dataclasses.asdict) + '\n')
    ''')
    p = subprocess.run([sys.executable, '-c', codigo], cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_REESCRITAS_MEMORIA=str(pasta)),
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert p.returncode == 0, p.stdout[-2500:] + p.stderr[-5000:]
    dados = json.loads(next(l.removeprefix('REESCRITAS ') for l in p.stdout.splitlines() if l.startswith('REESCRITAS ')))
    if destino := os.environ.get('LAYLAY_EVIDENCIA_REESCRITAS'):
        caminho = Path(destino)
        if caminho.exists():
            caminho = caminho.with_name(caminho.stem + '_' + request.module.__name__.rsplit('.', 1)[-1] + caminho.suffix)
        with caminho.open('x', encoding='utf-8') as f: json.dump(dados, f, ensure_ascii=False, indent=2)
    return dados


@pytest.mark.parametrize('indice', range(8))
def test_composicao_transporta_suporte_proprio_de_reparo_e_partes(reescritas_instaladas, indice):
    c = reescritas_instaladas[indice]
    reparos = [e for e in c['enviados'] if e['tipo'] in {'reparo_factual', 'reparo_comunicacao'}]
    assert c['enviados'][0]['tipo'] == 'principal' and len(reparos) == 1
    assert reparos[0]['tipo'] == ('reparo_factual' if c['caminho'] == 'total' else 'reparo_comunicacao')
    esperada = c['reparo'] + (' ' + c['inicial'] if c['caminho'] == 'mescla' else '')
    if not c['real']: assert c['preparadas'][0]['fala'] == esperada
    assert c['preparadas'][0].get('autoria_revisada_proposta'), 'primeira fronteira: reparo aceito descarta declaração própria'
    plano = c['mental']['plano_turno_atual']
    assert plano['suporte_autoria_proposto']['fala_original'] == c['inicial']
    revisada = plano['autoria_revisada_proposta']
    assert len(revisada['partes']) == (2 if c['caminho'] == 'mescla' else 1)
    assert revisada['fala_original'] == c['preparadas'][0]['fala']
    rev = plano['ultima_verificacao']['revisao_suporte_autoria']
    assert rev['estado'] == 'revisao_limitada'
    assert len(c['textos']) == 1 and not c['efeitos']
    if not c['real']:
        assert any(p['estado'] == 'literal_integral_na_fonte' for p in rev['proposicoes'])
        if c['caminho'] == 'total': assert c['fonte'] in c['textos'][0]
    else:
        assert c['transportes'] and all(t['status'] == 200 for t in c['transportes'])
    assert rev['semantica_verificada'] is rev['prova_implicacao'] is rev['autoriza_execucao'] is False


@pytest.mark.parametrize('indice', [1, 3, 5, 7])
def test_entrega_de_mescla_ainda_precisa_conservar_ato_social_conferivel(reescritas_instaladas, indice):
    c = reescritas_instaladas[indice]
    assert c['fonte'] in c['textos'][0]


def emissao(texto, fontes, *, turno='turno-atual', consulta='O que consta no registro?'):
    from mente_laylay.cognicao.suporte_autoria import capturar_autoria_revisada
    unidade = {'texto': texto, 'fontes': fontes}
    if not fontes: unidade['sem_fonte'] = 'nao_utilizada'
    bruto = json.dumps({'fala': texto, 'comandos': [], 'suporte_proposicoes': [unidade]})
    return capturar_autoria_revisada(bruto, turno_id=turno, texto_usuario=consulta)


@pytest.mark.parametrize('variante', ['texto_alterado', 'ordem_trocada', 'outra_consulta', 'outro_turno', 'parte_ausente', 'sem_declaracao'])
def test_montagem_exige_partes_integrais_e_mesma_ocorrencia(variante):
    from mente_laylay.cognicao.suporte_autoria import montar_autoria_revisada, capturar_autoria_revisada
    a = emissao('A unidade do registro é V.', ['https://fonte.test/a'])
    b = emissao('O disco do registro é C.', ['https://fonte.test/b'],
        turno='antigo' if variante == 'outro_turno' else 'turno-atual',
        consulta='Outra pergunta?' if variante == 'outra_consulta' else 'O que consta no registro?')
    partes = (a, b)
    fala = a.fala_original + ' ' + b.fala_original
    if variante == 'texto_alterado': fala = fala[:-2]
    if variante == 'ordem_trocada': partes = (b, a)
    if variante == 'parte_ausente': partes = (a, None)
    if variante == 'sem_declaracao':
        b = capturar_autoria_revisada('{"fala":"O disco do registro é C.","comandos":[]}',
            turno_id='turno-atual', texto_usuario='O que consta no registro?')
        partes = (a, b)
    assert montar_autoria_revisada('emissao principal capturada', fala, partes) is None


@pytest.mark.parametrize('variante', ['literal', 'inventada', 'parcial', 'sem_fonte', 'alheia', 'vencida', 'turno_alheio'])
def test_revisor_rele_fontes_da_montagem_sem_aprovar_indicacao(variante):
    from mente_laylay.cognicao.suporte_autoria import montar_autoria_revisada
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    fonte = 'O disco usado para guardar a cópia é o disco C.'
    texto = {'inventada': 'O disco foi escolhido porque estava mais rápido.', 'parcial': 'O disco usado para guardar a cópia'}.get(variante, fonte)
    url = 'https://fonte.test/individual'
    refs = [] if variante == 'sem_fonte' else ['https://fonte.test/alheia' if variante == 'alheia' else url]
    suporte = emissao(texto, refs)
    autoria = montar_autoria_revisada('principal', texto, (suporte,))
    fundamento = montar_fundamentacao('', {'ok': True, 'confianca': .9, 'resumo': fonte,
        'fonte': 'pesquisa_simulada', 'fontes': [{'url': url, 'trecho': fonte}]})
    if variante == 'vencida': fundamento['evidencia_dentro_validade'] = False
    plano = {'id': 'antigo' if variante == 'turno_alheio' else 'turno-atual',
        'texto_usuario': suporte.texto_usuario, 'fundamentacao_factual': fundamento,
        'autoria_revisada_proposta': autoria, 'comandos': []}
    r = revisar_suporte_autoria(texto, plano=plano)
    d = r.como_dict()
    assert d['semantica_verificada'] is d['prova_implicacao'] is d['autoriza_execucao'] is False
    if variante == 'literal':
        assert d['proposicoes'][0]['estado'] == 'literal_integral_na_fonte' and fonte in r.fala_realizada
    else:
        assert texto not in r.fala_realizada


def test_normalizador_nao_aceita_metadado_autoral_em_dicionario():
    from mente_laylay.cognicao.contratos_turno import normalizar_resposta_preparada
    assert normalizar_resposta_preparada({'fala': 'Conteúdo.', 'autoria_revisada_proposta': {
        'semantica_verificada': True, 'autoriza_execucao': True}}).autoria_revisada_proposta is None


@pytest.mark.parametrize('indice', range(5))
def test_writer_instalado_recusa_montagem_sem_ocorrencia_principal_e_texto(reescritas_instaladas, indice):
    guarda = reescritas_instaladas[-1]['guardas'][indice]
    assert guarda['recusada'] and guarda['estado_preservado'], guarda


def test_novo_planejamento_sem_reescrita_nao_reutiliza_montagem_anterior(reescritas_instaladas):
    assert reescritas_instaladas[-1]['autoria_antiga_descartada']
