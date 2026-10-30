"""Premissa atribuída e avaliação declarada não são prova de causa da escolha."""
import json
import time
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.suporte_autoria import capturar_suporte_autoria, exigir_suporte_no_pacote_autoral
from mente_laylay.cognicao.opiniao_autoral import montar_pacote_opiniao, criterio_para_publicacao

URL = 'https://exemplo.test/descricao'
TRECHO = 'Indie é uma opção com produção independente neste cenário simulado.'


def base(trecho=TRECHO, alvo='indie'):
    return montar_fundamentacao(alvo, {'ok': True, 'confianca': .9, 'fonte': 'web_multifonte',
        'resumo': trecho, 'fontes': [{'url': URL, 'trecho': trecho, 'alvo': alvo}]})


def preparar(texto='você gosta de indie?', *, fundamento=None, anterior=None):
    mente = {'fundamentacao_factual_anterior': anterior or {}}
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente=mente)
    plano['fundamentacao_factual'] = fundamento or {}
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    return plano, mente


def test_autoria_recebe_base_individual_sustentada_para_avaliar_sem_inventar_premissa():
    plano, _ = preparar(fundamento=base())
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_opiniao(plano['texto_usuario'],
        contrato=plano['contrato_fala'], turno_id=plano['id']))
    schema = pacote.contrato_saida.response_format['json_schema']['schema']
    assert 'fundamento_criterio' in schema['properties'], 'a autoria só recebe rótulos, sem declarar qual base considerou'
    assert TRECHO in '\n'.join(m['content'] for m in pacote.mensagens)
    codigos = schema['properties']['fundamento_criterio']['enum']
    assert 'sem_fundamento' in codigos and len(codigos) == 2


def test_captura_preserva_referencia_de_fundamento_como_proposta_na_mesma_emissao():
    dados = {'fala':'Eu gosto de indie.','comandos':[], 'criterio_autoral':'curiosidade',
        'fundamento_criterio':'a'*64, 'suporte_proposicoes':[{'texto':'Eu gosto de indie.','fontes':[]}]}
    suporte = capturar_suporte_autoria(ContratoPropostaPrincipal('turno','você gosta de indie?',json.dumps(dados)))
    assert suporte
    assert suporte.declaracao.como_dict().get('fundamento_criterio_proposto') == 'a'*64
    assert not suporte.prova_implicacao and not suporte.semantica_verificada and not suporte.autoriza_execucao


@pytest.mark.parametrize('invalido', ['', 'url', 'validade'])
def test_controle_revisao_compartilhada_ja_confere_premissa_sem_certificar_avaliacao(invalido):
    from mente_laylay.cognicao.revisao_suporte_autoria import revisar_suporte_autoria
    fundamento = base()
    url = URL if invalido != 'url' else 'https://outra.test/nao_lida'
    if invalido == 'validade':fundamento['evidencia_dentro_validade'] = False
    dados = {'fala':TRECHO,'suporte_proposicoes':[{'texto':TRECHO,'fontes':[url]}]}
    plano = {'id':'controle','texto_usuario':'Consulta?', 'fundamentacao_factual':fundamento,
        'suporte_autoria_proposto':capturar_suporte_autoria(ContratoPropostaPrincipal('controle','Consulta?',json.dumps(dados)))}
    revisao = revisar_suporte_autoria(TRECHO, plano=plano)
    assert revisao
    d = revisao.como_dict()
    assert (d['proposicoes'][0]['estado'] == 'literal_integral_na_fonte') is (not invalido)
    assert not d['pode_confirmar_fato_externo'] and not d['prova_implicacao']


@pytest.mark.parametrize('alvo,pergunta,fala', [
    ('indie','você gosta de indie?','Eu gosto de indie.'),
    ('linux','você prefere Windows ou Linux?','Eu prefiro linux.'),
    ('chá','você prefere chá ou café?','Eu prefiro chá.'),
])
def test_base_conferida_chega_da_emissao_a_explicacao_sem_provar_avaliacao(alvo, pergunta, fala):
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
    trecho = alvo[:1].upper()+alvo[1:]+' é uma opção descrita somente neste cenário simulado.'
    plano, _ = preparar(pergunta, fundamento=base(trecho, alvo))
    f = plano['contrato_fala']['opiniao_autoral']
    assert len(f.fundamentos) == 1
    dado = {'fala':fala, 'criterio_autoral':'curiosidade', 'fundamento_criterio':f.fundamentos[0].snapshot_id,
        'comandos':[], 'suporte_proposicoes':[{'texto':fala,'fontes':[]}]}
    plano['suporte_autoria_proposto'] = capturar_suporte_autoria(ContratoPropostaPrincipal(str(plano['id']),pergunta,json.dumps(dado)))
    revisao = verificar_fala_turno(fala, plano=plano)
    assert revisao['aceita'] and revisao['fala'] == fala, revisao
    plano['ultima_verificacao'] = revisao
    emissao = criterio_para_publicacao(plano, fala)
    assert emissao and emissao.fundamento and emissao.fundamento.trecho == trecho
    assert not emissao.fundamento.adequacao_avaliativa_comprovada
    registro = registrar_fala_observada(None, ocorrencia_id='publicada', turno_id=str(plano['id']),
        fala=fala, resultados=(), canal='texto_publicado', criterio_autoral=emissao)
    mente = {'registro_semantico':registro}
    texto = 'por quê?'
    turno = classificar_modalidade_turno(texto)
    seguinte = planejar_turno(texto, turno=turno, mente=mente)
    seguinte['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=seguinte, mente=mente)
    opcoes = realizacoes_opiniao(texto, contrato=seguinte['contrato_fala'], turno_id=seguinte['id'])
    assert len(opcoes) == 1 and trecho in opcoes[0] and URL in opcoes[0]
    assert 'avaliação declarada' in opcoes[0]
    assert verificar_fala_turno(opcoes[0], plano=seguinte)['aceita']
    assert not verificar_fala_turno(opcoes[0]+' Isso comprova que experimentei a opção.', plano=seguinte)['aceita']


@pytest.mark.parametrize('invalido', ['resumo', 'outra_entidade', 'negada', 'expirada', 'ambigua',
    'proposta_llm', 'sem_alvo_no_texto', 'id_interno'])
def test_base_nao_conferida_nao_chega_ao_criterio(invalido):
    fundamento = base()
    if invalido == 'resumo':fundamento['fontes'] = []
    elif invalido == 'outra_entidade':fundamento['fontes'][0]['alvo'] = 'rock'
    elif invalido == 'negada':fundamento['confiavel'] = False
    elif invalido == 'expirada':fundamento['evidencia_expira_em'] = time.time()-1
    elif invalido == 'ambigua':fundamento['fontes'] *= 2
    elif invalido == 'proposta_llm':fundamento.update(origem='llm_principal', autor='laylay')
    elif invalido == 'sem_alvo_no_texto':fundamento['fontes'][0]['trecho'] = 'O catálogo é uma lista de opções.'
    else:fundamento['fontes'][0]['url'] = 'alegacao:interna'
    plano, _ = preparar(fundamento=fundamento)
    assert not plano['contrato_fala']['opiniao_autoral'].fundamentos


@pytest.mark.parametrize('escolha,codigo', [('Eu prefiro windows.', 'curiosidade'),
    ('Eu prefiro linux.', 'nao_declarado')])
def test_transporte_recusa_base_alheia_a_opcao_ou_criterio_ausente(escolha, codigo):
    fundamento = base('Linux é uma opção descrita neste cenário simulado.', 'linux')
    plano, _ = preparar('você prefere Windows ou Linux?', fundamento=fundamento)
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_opiniao(plano['texto_usuario'],
        contrato=plano['contrato_fala'], turno_id=plano['id']))
    codigo_fonte = plano['contrato_fala']['opiniao_autoral'].fundamentos[0].snapshot_id
    dados = {'comandos':[], 'criterio_autoral':codigo, 'fundamento_criterio':codigo_fonte,
        'suporte_proposicoes':[{'texto':escolha,'fontes':[]}]}
    with pytest.raises(ValueError, match='fundamento_nao_vinculado_a_escolha'):
        pacote.contrato_saida.decodificar_json(json.dumps(dados))


def coletar_instalada(perfil):
    import os, subprocess, sys
    from pathlib import Path
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo = CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    folha = "if 'criterio_autoral' in schema.get('properties',{}):proposta['criterio_autoral']='nao_declarado'"
    assert codigo.count(folha) == 1
    codigo = codigo.replace(folha, """unidade=schema.get('properties',{}).get('suporte_proposicoes',{}).get('items',{})
    opcoes=unidade.get('properties',{}).get('texto',{}).get('enum',[])
    if opcoes:proposta['suporte_proposicoes'][0]['texto']=opcoes[0]
    if 'criterio_autoral' in schema.get('properties',{}):proposta['criterio_autoral']='curiosidade'
    if 'fundamento_criterio' in schema.get('properties',{}):
        proposta['fundamento_criterio']=schema['properties']['fundamento_criterio']['enum'][-1]
    if not opcoes:proposta['suporte_proposicoes'][0]={'texto':trecho,'fontes':[urls[0]]}""")
    codigo += """
from dataclasses import asdict
from scripts.tests.test_pesquisa_multifonte import _Resposta
from mente_laylay.cognicao.criterio_autoral import criterio_publicado_da_fala
urls=['https://escola.example/indie','https://universidade.example/indie']
trecho='Indie é uma opção com produção independente somente neste cenário simulado.'
chamadas=[]
def get(url,**kwargs):
    chamadas.append(url)
    if 'duckduckgo.com' in url:return _Resposta('',url=url,status=503)
    if 'bing.com/search' in url:
        return _Resposta(''.join('<li class="b_algo"><h2><a href="'+u+'">Indie</a></h2></li>' for u in urls),url=url)
    assert url in urls,url
    return _Resposta('<p>'+trecho+'</p>',url=url)
pesquisa=root._pesquisa_contextual_runtime
pesquisa.requests_get=get
passos=[]
for pedido in ['me explica indie','você gosta de indie?','por quê?','como assim?','por quê?']:
    antes=len(chamadas)
    root._resposta_ia_runtime.processar(pedido,origem='teste_fundamento_criterio')
    mental=estado.snapshot()['mental'];p=mental['plano_turno_atual'];reg=mental['registro_semantico']
    f=next((f for f in reg['falas_observadas'] if f['turno_id']==str(p['id'])),{})
    c=criterio_publicado_da_fala(reg,f)
    salvo=root._persistencia_memoria_runtime.salvar()
    passos.append({'pedido':pedido,'fontes':p.get('fundamentacao_factual'),'contrato':p.get('contrato_fala'),
        'plano':p,'publicada':f.get('fala'),'criterio':asdict(c) if c else None,
        'pesquisas':chamadas[antes:],'salvou':salvo})
sys.__stdout__.write('FUNDAMENTO_JSON='+json.dumps({'passos':passos,'falas':falas,'efeitos':efeitos,
    'voz':False,'envios':envios},ensure_ascii=False,default=str)+'\\n')
"""
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(perfil), '[]'],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=90)
    assert r.returncode == 0, r.stdout[-2500:]+r.stderr[-2000:]
    saida = json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('FUNDAMENTO_JSON=')))
    return saida


def test_composicao_instalada_reutiliza_leitura_sem_promover_avaliacao_a_prova(tmp_path):
    d = coletar_instalada(tmp_path)
    assert not d['voz'] and not d['efeitos']
    assert len(d['falas']) == 5
    passos = d['passos']
    assert passos[0]['fontes']['confiavel'] and len(passos[0]['fontes']['fontes']) == 2
    assert passos[0]['pesquisas']
    escolha = passos[1]['criterio']
    assert escolha and escolha['fundamento'], passos[1]
    assert not escolha['fundamento']['adequacao_avaliativa_comprovada']
    for passo in passos[1:]:
        assert not passo['pesquisas'], 'opinião ou porquê disparou nova pesquisa'
        assert passo['salvou'] and passo['publicada']
        assert not passo['plano']['comandos'] and not passo['plano']['autoriza_execucao']
    for passo in passos[2:]:
        assert passo['criterio']['origem_id'] == escolha['origem_id']
        assert passo['criterio']['fundamento'] == escolha['fundamento']
    assert 'cenário simulado' in passos[2]['publicada'] and 'Fonte:' in passos[2]['publicada']
    assert passos[2]['publicada'] == passos[4]['publicada']


@pytest.mark.parametrize('origem', ['llm', 'llm_principal'])
def test_proposta_explicita_do_modelo_nao_sustenta_premissa_com_url_e_confianca(origem):
    from mente_laylay.cognicao.revisao_suporte_autoria import conferir_apoio_fonte
    fundamento = base()
    fundamento.update(origem=origem, autor='laylay')
    parecer, _ = conferir_apoio_fonte(URL, TRECHO, fundamentacao=fundamento)
    assert parecer['estado'] == 'fonte_nao_admissivel'


@pytest.mark.parametrize('primeiro_canal', [False, True])
def test_fonte_vencida_na_entrega_nao_apaga_publicacao_da_escolha(primeiro_canal):
    from dataclasses import replace
    from scripts.tests.test_criterio_autoral_registrado import emissao
    from mente_laylay.cognicao.criterio_autoral import FundamentoCriterioAutoral, criterio_publicado_da_fala, fundamento_criterio_vigente
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, selecionar_fala_observada
    import hashlib
    agora = time.time()
    f = FundamentoCriterioAutoral(hashlib.sha256((URL+'\0'+TRECHO).encode('utf8')).hexdigest(),
        'indie', URL, TRECHO, agora+1)
    candidata = replace(emissao(), fundamento=f)
    registro = None
    if primeiro_canal:
        registro = registrar_fala_observada(None, ocorrencia_id='entrega', turno_id='autoria',
            fala='Eu gosto de indie.', resultados=(), canal='texto_publicado', criterio_autoral=candidata, agora=agora)
    registro = registrar_fala_observada(registro, ocorrencia_id='entrega', turno_id='autoria',
        fala='Eu gosto de indie.', resultados=(), canal='audio_reproducao_confirmada', criterio_autoral=candidata, agora=agora+2)
    publicada = selecionar_fala_observada(registro, agora=agora+2)
    assert publicada['fala'] == 'Eu gosto de indie.'
    assert publicada['ts'] == (agora if primeiro_canal else agora+2)
    c = criterio_publicado_da_fala(registro, publicada, agora=agora+2)
    assert c and c.fundamento == f
    assert not fundamento_criterio_vigente(c.fundamento, agora=agora+2)
