"""Critério escolhido é declaração de autoria; só a publicação confirma seu registro."""
import json
import hashlib
import time
from dataclasses import replace
import pytest

from scripts.tests.test_opiniao_autoral_conferivel import preparar
from mente_laylay.cognicao.opiniao_autoral import montar_pacote_opiniao
from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral, capturar_suporte_autoria
from mente_laylay.cognicao.contratos_turno import ContratoPropostaPrincipal
from mente_laylay.cognicao.criterio_autoral import CriterioAutoralEmissao, criterio_publicado_da_fala
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, selecionar_fala_observada


def proposta(fala='Eu gosto de indie.', codigo='curiosidade'):
    return {'comandos': [], 'suporte_proposicoes': [{'texto': fala, 'fontes': []}],
            'criterio_autoral': codigo}


def test_emissao_pode_declarar_criterio_sem_oferecer_fonte_factual_falsa():
    texto = 'você gosta de indie?'
    _, plano, _ = preparar(texto)
    pacote = montar_pacote_opiniao(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    pacote = exigir_suporte_no_pacote_autoral(pacote)
    r = pacote.contrato_saida.decodificar_json(json.dumps(proposta()))
    assert r['fala'] == 'Eu gosto de indie.'
    assert r['criterio_autoral'] == 'curiosidade' and not r['suporte_proposicoes'][0]['fontes']


def test_captura_conserva_criterio_como_proposta_sem_prova_ou_autoridade():
    d = proposta()
    d['fala'] = 'Eu gosto de indie.'
    principal = ContratoPropostaPrincipal('autoria', 'você gosta de indie?', json.dumps(d))
    suporte = capturar_suporte_autoria(principal)
    assert suporte is not None
    registro = suporte.declaracao.como_dict()
    assert registro.get('criterio_autoral_proposto') == 'curiosidade'
    assert not suporte.semantica_verificada and not suporte.prova_implicacao and not suporte.autoriza_execucao


def emissao():
    return CriterioAutoralEmissao('autoria', 'você gosta de indie?', 'Eu gosto de indie.',
        'curiosidade', hashlib.sha256(b'emissao').hexdigest())


def publicar(registro=None, fonte=None, *, fala='Eu gosto de indie.', ident='entrega', turno='autoria', agora=None):
    return registrar_fala_observada(registro, ocorrencia_id=ident, turno_id=turno,
        fala=fala, resultados=(), canal='texto_publicado', criterio_autoral=fonte,
        agora=agora)


def test_publicacao_vincula_criterio_sem_provar_fato_ou_causa():
    registro = publicar(fonte=emissao())
    fala = selecionar_fala_observada(registro)
    c = criterio_publicado_da_fala(registro, fala)
    assert c is not None and c.codigo == 'curiosidade' and c.origem_id == 'entrega'
    assert c.natureza == 'criterio_declarado_na_autoria'
    assert not c.prova_factual and not c.prova_causal and not c.autoriza_execucao


@pytest.mark.parametrize('invalido', ['dict', 'texto', 'turno', 'codigo'])
def test_publicacao_recusa_criterio_sem_vinculo(invalido):
    fonte = emissao()
    if invalido == 'dict':
        fonte = {'codigo': 'curiosidade', 'declaracao': 'Eu gosto de indie.'}
    elif invalido == 'texto':
        fonte = replace(fonte, declaracao='Eu gosto de rock.')
    elif invalido == 'turno':
        fonte = replace(fonte, turno_id='outro')
    else:
        fonte = replace(fonte, codigo='porque eu ouvi ontem')
    with pytest.raises((ValueError, TypeError)):
        publicar(fonte=fonte)


def test_explicacao_pode_transportar_vinculo_sem_renovar_o_ttl_original():
    instante = time.time()
    registro = publicar(fonte=emissao(), agora=instante-800)
    c = criterio_publicado_da_fala(registro, selecionar_fala_observada(registro))
    assert c
    registro = publicar(registro, c, fala='Eu gosto de indie. O critério registrado foi curiosidade.',
        ident='explicacao', turno='seguinte', agora=instante)
    outra = criterio_publicado_da_fala(registro, selecionar_fala_observada(registro))
    assert outra and outra.origem_id == 'entrega' and outra.portadora_id == 'explicacao'
    assert outra.ts_origem == instante-800 and outra.ts_portadora == instante
    assert criterio_publicado_da_fala(registro, selecionar_fala_observada(registro), agora=instante+101) is None


def test_segundo_canal_da_mesma_publicacao_preserva_identidade_e_tempo_do_criterio():
    instante = time.time()
    registro = publicar(fonte=emissao(), agora=instante-2)
    outro = registrar_fala_observada(registro, ocorrencia_id='entrega', turno_id='autoria',
        fala='Eu gosto de indie.', resultados=(), canal='audio_reproducao_confirmada',
        criterio_autoral=emissao(), agora=instante)
    fala = selecionar_fala_observada(outro)
    assert fala['canais'] == ['texto_publicado', 'audio_reproducao_confirmada']
    criterio = criterio_publicado_da_fala(outro, fala)
    assert criterio and criterio.ts_origem == instante-2


@pytest.mark.parametrize('campo,valor', [('ts_origem', 'ontem'), ('ts_origem', float('nan')),
    ('emissao_sha256', None), ('codigo', []), ('portadora_id', 'outra')])
def test_metadado_adulterado_e_recusado_sem_excecao(campo, valor):
    registro = publicar(fonte=emissao())
    fala = selecionar_fala_observada(registro)
    fala['criterio_autoral'] = replace(fala['criterio_autoral'], **{campo: valor})
    assert criterio_publicado_da_fala(registro, fala) is None


@pytest.mark.parametrize('invalido', ['sem_raiz', 'origem_alterada', 'texto_apenas'])
def test_texto_ou_transportadora_nao_substituem_a_origem_publicada(invalido):
    registro = publicar(fonte=emissao())
    c = criterio_publicado_da_fala(registro, selecionar_fala_observada(registro))
    registro = publicar(registro, c, fala='Eu gosto de indie. O critério registrado foi curiosidade.',
        ident='explicacao', turno='seguinte')
    if invalido == 'sem_raiz':registro['falas_observadas'].pop(0)
    elif invalido == 'origem_alterada':registro['falas_observadas'][0]['fala'] = 'Eu gosto de jazz.'
    else:registro['falas_observadas'][-1].pop('criterio_autoral')
    assert criterio_publicado_da_fala(registro, selecionar_fala_observada(registro)) is None


@pytest.mark.parametrize('invalido', ['', 'sem_revisao', 'outra_fala', 'outro_turno', 'outra_consulta', 'dict'])
def test_admissao_depende_da_mesma_emissao_revisada(invalido):
    from mente_laylay.cognicao.opiniao_autoral import criterio_para_publicacao
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    texto, fala = 'você gosta de indie?', 'Eu gosto de indie.'
    _, plano, _ = preparar(texto)
    dados = {**proposta(), 'fala': fala}
    suporte = capturar_suporte_autoria(ContratoPropostaPrincipal(plano['id'], texto, json.dumps(dados)))
    assert suporte
    plano['suporte_autoria_proposto'] = suporte
    plano['ultima_verificacao'] = verificar_fala_turno(fala, plano=plano)
    assert plano['ultima_verificacao']['aceita']
    if invalido == 'sem_revisao':plano.pop('ultima_verificacao')
    elif invalido == 'outra_fala':fala = 'Eu não gosto de indie.'
    elif invalido == 'outro_turno':plano['suporte_autoria_proposto'] = replace(suporte, turno_id='outro')
    elif invalido == 'outra_consulta':plano['suporte_autoria_proposto'] = replace(suporte, texto_usuario='você gosta de jazz?')
    elif invalido == 'dict':plano['suporte_autoria_proposto'] = {'criterio_autoral_proposto': 'curiosidade'}
    criterio = criterio_para_publicacao(plano, fala)
    if invalido:
        assert criterio is None
    else:
        assert type(criterio) is CriterioAutoralEmissao
        assert criterio.codigo == 'curiosidade'
        assert not criterio.prova_factual and not criterio.prova_causal


def test_reescrita_declara_criterio_proprio_e_mescla_nao_o_herda():
    from mente_laylay.cognicao.suporte_autoria import AutoriaRevisadaProposta
    dados = {**proposta(), 'fala': 'Eu gosto de indie.'}
    parte = capturar_suporte_autoria(ContratoPropostaPrincipal('autoria', 'você gosta de indie?', json.dumps(dados)))
    assert parte
    reescrita = AutoriaRevisadaProposta('autoria', parte.texto_usuario, 'a'*64, parte.fala_original, (parte,))
    assert reescrita.suporte_composto().declaracao.como_dict()['criterio_autoral_proposto'] == 'curiosidade'
    dados = {**proposta('Eu gosto de rock.', 'simplicidade'), 'fala': 'Eu gosto de rock.'}
    outra = capturar_suporte_autoria(ContratoPropostaPrincipal('autoria', parte.texto_usuario, json.dumps(dados)))
    mescla = AutoriaRevisadaProposta('autoria', parte.texto_usuario, 'a'*64,
        parte.fala_original+' '+outra.fala_original, (parte, outra))
    assert 'criterio_autoral_proposto' not in mescla.suporte_composto().declaracao.como_dict()


def coletar_composicao(perfil, falhar_entrega=False):
    import os, subprocess, sys
    from pathlib import Path
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo = CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    folha = "if 'criterio_autoral' in schema.get('properties',{}):proposta['criterio_autoral']='nao_declarado'"
    assert codigo.count(folha) == 1
    codigo = codigo.replace(folha, """unidade=schema.get('properties',{}).get('suporte_proposicoes',{}).get('items',{})
    opcoes=unidade.get('properties',{}).get('texto',{}).get('enum',[])
    if opcoes:proposta['suporte_proposicoes'][0]['texto']=opcoes[0]
    if 'criterio_autoral' in schema.get('properties',{}):proposta['criterio_autoral']='curiosidade'""")
    codigo += '\nfalhar_entrega='+repr(falhar_entrega)+'\n'
    codigo += """
from dataclasses import asdict
if falhar_entrega:
    root._orquestrador_fala_runtime._observadores_texto_final.clear()
    root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda *a,**k:False)
passos=[]
for pedido in ['você gosta de indie?','por quê?','como assim?','por quê?']:
    root._resposta_ia_runtime.processar(pedido,origem='teste_criterio_autoral')
    mental=estado.snapshot()['mental']
    registro=mental.get('registro_semantico') or {}
    passos.append({'pedido':pedido,'plano':mental.get('plano_turno_atual'),
        'falas':[{'fala':f['fala'],'criterio':asdict(f['criterio_autoral']) if f.get('criterio_autoral') else None}
                 for f in registro.get('falas_observadas',[])]})
sys.__stdout__.write('CRITERIO_JSON='+json.dumps({'passos':passos,'falas':falas,'efeitos':efeitos,
    'voz':False},ensure_ascii=False,default=str)+'\\n')
"""
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(perfil), '[]'],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=90)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    return json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('CRITERIO_JSON=')))


def test_composicao_instalada_publica_criterio_e_preserva_a_origem_na_continuidade(tmp_path):
    d = coletar_composicao(tmp_path)
    assert not d['efeitos'] and not d['voz']
    assert len(d['falas']) == 4
    raiz = d['passos'][0]['falas'][-1]['criterio']
    assert raiz and raiz['codigo'] == 'curiosidade'
    for passo in d['passos'][1:]:
        publicada = passo['falas'][-1]
        assert publicada['criterio'], passo
        assert publicada['criterio']['origem_id'] == raiz['origem_id']
        assert publicada['criterio']['ts_origem'] == raiz['ts_origem']
        assert not publicada['criterio']['prova_factual'] and not publicada['criterio']['prova_causal']
    assert 'critério que registrei' in d['falas'][1] and 'curiosidade' in d['falas'][3]
    assert all(not p['plano']['comandos'] and not p['plano']['autoriza_execucao'] for p in d['passos'])


def test_composicao_sem_entrega_nao_registra_proposta_como_criterio_publicado(tmp_path):
    d = coletar_composicao(tmp_path, falhar_entrega=True)
    assert not d['efeitos'] and not d['voz'] and not d['falas']
    assert all(not p['falas'] for p in d['passos'])


def test_persistencia_projeta_criterio_descritivo_sem_reconstruir_prova_nativa():
    from mente_laylay.memoria_mental.persistencia_memoria import PersistenciaMemoriaRuntime
    registro = publicar(fonte=emissao())
    runtime = PersistenciaMemoriaRuntime(memoria_sqlite=None, base_system_prompt='',
        estado_obter=lambda dominio, chave, padrao=None: registro if (dominio,chave)==('mental','registro_semantico') else padrao,
        estado_atualizar=lambda *a,**k:None)
    salvo = json.loads(json.dumps(runtime.snapshot()))['registro_semantico']
    assert salvo['falas_observadas'][0]['criterio_autoral']['codigo'] == 'curiosidade'
    assert criterio_publicado_da_fala(salvo, selecionar_fala_observada(salvo)) is None
    assert criterio_publicado_da_fala(registro, selecionar_fala_observada(registro)) is not None


@pytest.mark.parametrize('pedido', ['por que você gosta de rock?', 'por que você não gosta de indie?'])
def test_recusa_de_premissa_diferente_e_publicada_sem_transportar_criterio_alheio(pedido):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao, criterio_para_publicacao
    registro = publicar(fonte=emissao())
    mente = {'registro_semantico':registro}
    turno = classificar_modalidade_turno(pedido)
    plano = planejar_turno(pedido, turno=turno, mente=mente)
    plano['contrato_fala'] = construir_contrato_semantico_fala(pedido, turno=turno, plano=plano, mente=mente)
    opcoes = realizacoes_opiniao(pedido, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert len(opcoes) == 1 and 'Não tenho uma declaração' in opcoes[0]
    plano['ultima_verificacao'] = verificar_fala_turno(opcoes[0], plano=plano)
    assert plano['ultima_verificacao']['aceita']
    criterio = criterio_para_publicacao(plano, opcoes[0])
    assert criterio is None
    novo = publicar(registro, criterio, fala=opcoes[0], ident='recusa', turno=str(plano['id']))
    assert selecionar_fala_observada(novo)['id'] == 'recusa'


@pytest.mark.parametrize('mudanca', ['ausente', 'causa_livre', 'fonte_falsa', 'campo_prova'])
def test_transporte_nao_admite_criterio_como_causa_livre_ou_fonte_factual(mudanca):
    texto = 'você gosta de indie?'
    _, plano, _ = preparar(texto)
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_opiniao(texto,
        contrato=plano['contrato_fala'], turno_id=plano['id']))
    dados = proposta()
    if mudanca == 'ausente':dados.pop('criterio_autoral')
    elif mudanca == 'causa_livre':dados['criterio_autoral'] = 'ouvi e me emocionei'
    elif mudanca == 'fonte_falsa':dados['suporte_proposicoes'][0]['fontes'] = ['curiosidade']
    else:dados['prova_causal'] = True
    with pytest.raises((ValueError, KeyError)):
        pacote.contrato_saida.decodificar_json(json.dumps(dados))


@pytest.mark.parametrize('acrescimo', [' É um gênero mais profundo.',
    ' Eu escutei ontem e me emocionei.', ' Esse critério comprova minha causa psicológica.'])
def test_criterio_declarado_nao_libera_fatos_experiencias_ou_causas(acrescimo):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
    texto = 'por que você gosta de indie?'
    mente = {'registro_semantico':publicar(fonte=emissao())}
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente=mente)
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    opcoes = realizacoes_opiniao(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert len(opcoes) == 1 and 'curiosidade' in opcoes[0]
    assert verificar_fala_turno(opcoes[0], plano=plano)['aceita']
    assert not verificar_fala_turno(opcoes[0]+acrescimo, plano=plano)['aceita']
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_opiniao(texto,
        contrato=plano['contrato_fala'], turno_id=plano['id']))
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps(proposta(opcoes[0], 'simplicidade')))
