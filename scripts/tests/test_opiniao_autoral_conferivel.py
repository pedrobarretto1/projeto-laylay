"""Opinião escolhida não comprova uma experiência ou causa; correção conserva o assunto."""
import pytest
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import replace

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada


def preparar(texto, fala_anterior='', pergunta_anterior=''):
    mente = {}
    if fala_anterior:
        mente['registro_semantico'] = registrar_fala_observada(None,
            ocorrencia_id='entrega_opiniao', turno_id='origem', fala=fala_anterior,
            resultados=(), canal='texto_publicado')
        mente['ultima_resposta'] = fala_anterior
        mente['ultima_entrada'] = pergunta_anterior
    turno = classificar_modalidade_turno(texto)
    mente['turno_atual'] = turno
    plano = planejar_turno(texto, turno=turno, mente=mente)
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    return turno, plano, mente


@pytest.mark.parametrize('texto', ['qual o seu estilo musical?', 'qual é seu gênero musical?', 'qual sua música preferida?'])
def test_pergunta_de_preferencia_propria_recebe_ato_subjetivo(texto):
    _, plano, _ = preparar(texto)
    assert 'opiniao' in plano['contrato_fala']['atos']


@pytest.mark.parametrize('fala', [
    'Meu estilo musical é o que me faz ficar mais próxima de você: sons suaves e melancólicos.',
    'Eu prefiro jazz porque é o que combina com o jeito que você fala.',
    'Não tenho gosto porque não tenho ouvidos nem memória para sons.',
    'Eu prefiro o seu gosto musical.',
])
def test_categoria_subjetiva_nao_admite_vagueza_causa_ou_negacao_de_capacidade(fala):
    _, plano, _ = preparar('qual o seu estilo musical?')
    r = avaliar_qualidade_comunicacao('qual o seu estilo musical?', fala, plano=plano)
    assert not r['aceita'] and r['problemas_bloqueantes']


@pytest.mark.parametrize('fala', [
    'Gosto de indie porque é o que me faz ficar mais próxima de você.',
    'Gosto de indie porque escutei ontem e me emocionei.',
    'Gosto de indie, mas o que define indie é o que você sente.',
    'Não gosto de indie porque não tenho memória.',
])
def test_opiniao_sobre_objeto_nao_e_prova_de_causa_ou_definicao(fala):
    _, plano, _ = preparar('voce gosta de indie?')
    r = avaliar_qualidade_comunicacao('voce gosta de indie?', fala, plano=plano)
    assert not r['aceita'] and r['problemas_bloqueantes']


def test_opiniao_simples_e_suficiente_sem_exigir_justificativa_inventada():
    _, plano, _ = preparar('voce gosta de indie?')
    r = avaliar_qualidade_comunicacao('voce gosta de indie?', 'Eu gosto de indie.', plano=plano)
    assert r['aceita'] and not r['problemas']


@pytest.mark.parametrize('texto', ['estou falando de musica', 'estou falando da musica',
                                   'tô falando do aplicativo', 'estou falando dos arquivos'])
def test_retificacao_de_assunto_nao_depende_da_contracao_da_preposicao(texto):
    turno, _, _ = preparar(texto)
    assert turno['modalidade'] == 'correcao' and turno['autoriza_execucao'] is False


@pytest.mark.parametrize('texto', ['como assim? voce nao tem nenhum em especifico?',
                                   'como assim?', 'estou falando da musica'])
def test_esclarecimento_ou_correcao_preserva_opiniao_publicada_sem_causa_nova(texto):
    _, plano, _ = preparar(texto, 'Eu gosto de indie.', 'voce gosta de indie?')
    fonte = plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is not None
    r = avaliar_qualidade_comunicacao(texto,
        'Não tenho opinião porque não ouço música e não tenho memória de sons.', plano=plano)
    assert not r['aceita']
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
    opcoes = realizacoes_opiniao(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes and all('indie' in f for f in opcoes)


@pytest.mark.parametrize('texto', [
    'você gosta de indie? abre a calculadora',
    'o João gosta de indie?',
    'a frase "você gosta de indie?" é uma pergunta?',
    'qual o meu estilo musical?',
    'você gostava de indie quando ouviu ontem?',
])
def test_ato_estranho_nao_recebe_contrato_de_opiniao_propria(texto):
    _, plano, _ = preparar(texto)
    assert 'opiniao_autoral' not in plano['contrato_fala']


@pytest.mark.parametrize('pedido,positiva,negativa', [
    ('você gosta de programar?', 'Eu gosto de programar.', 'Eu gosto de programar porque executei seu código ontem.'),
    ('você prefere Windows ou Linux?', 'Eu prefiro linux.', 'Eu prefiro linux porque vi seus arquivos.'),
    ('você prefere chá ou café?', 'Eu prefiro café.', 'Eu prefiro café porque provei ontem.'),
])
def test_mesmo_contrato_separa_opiniao_de_experiencia_em_outros_dominios(pedido, positiva, negativa):
    _, plano, _ = preparar(pedido)
    assert avaliar_qualidade_comunicacao(pedido, positiva, plano=plano)['aceita']
    assert not avaliar_qualidade_comunicacao(pedido, negativa, plano=plano)['aceita']


@pytest.mark.parametrize('invalido', ['dict', 'turno', 'texto', 'referencia_expirada'])
def test_fonte_estrangeira_ou_expirada_nao_admite_fala(invalido):
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
    texto = 'como assim?'
    _, plano, _ = preparar(texto, 'Eu gosto de indie.')
    contrato = plano['contrato_fala']
    fonte = contrato['opiniao_autoral']
    if invalido == 'dict':
        contrato['opiniao_autoral'] = {'turno_id': plano['id'], 'declaracoes': ['Eu gosto de indie.']}
    elif invalido == 'turno':
        contrato['opiniao_autoral'] = replace(fonte, turno_id='outro')
    elif invalido == 'texto':
        contrato['opiniao_autoral'] = replace(fonte, texto_usuario='outro')
    else:
        contrato['opiniao_autoral'] = replace(fonte, referencia=replace(fonte.referencia, ts=0))
    assert not realizacoes_opiniao(texto, contrato=contrato, turno_id=plano['id'])


def test_ultima_resposta_sem_publicacao_nao_e_opiniao_observada():
    turno, plano, mente = preparar('como assim?')
    mente['ultima_resposta'] = 'Eu gosto de indie.'
    contrato = construir_contrato_semantico_fala('como assim?', turno=turno, plano=plano, mente=mente)
    assert 'opiniao_autoral' not in contrato


@pytest.mark.parametrize('pedido,anterior', [
    ('estou falando de programar', 'Eu gosto de programar.'),
    ('estou falando do linux', 'Eu prefiro linux.'),
    ('estou falando do café', 'Eu prefiro café.'),
])
def test_correcao_nominal_exata_preserva_o_assunto_em_outros_dominios(pedido, anterior):
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
    _, plano, _ = preparar(pedido, anterior)
    opcoes = realizacoes_opiniao(pedido, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes
    assert all(anterior.casefold() in o.casefold() for o in opcoes)


def test_categoria_nova_na_correcao_nao_reclassifica_a_opiniao_sem_fonte():
    _, plano, _ = preparar('estou falando do aplicativo', 'Eu gosto de indie.')
    assert 'opiniao_autoral' not in plano['contrato_fala']


def test_revisao_direta_reutiliza_a_mesma_decisao_de_opiniao():
    from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
    texto = 'voce gosta de indie?'
    _, plano, _ = preparar(texto)
    r = validar_aderencia_contrato_fala(texto, 'Eu gosto de indie.', contrato_fala=plano['contrato_fala'], turno_id=plano['id'])
    assert r['aceita'] and not r['problemas']
    r = validar_aderencia_contrato_fala(texto, 'Eu gosto de indie porque escutei ontem.', contrato_fala=plano['contrato_fala'], turno_id=plano['id'])
    assert not r['aceita']


def test_lista_adulterada_na_fonte_nativa_nao_se_autovalida():
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
    texto = 'qual o seu estilo musical?'
    _, plano, _ = preparar(texto)
    contrato = plano['contrato_fala']
    contrato['opiniao_autoral'] = replace(contrato['opiniao_autoral'], declaracoes=('Eu prefiro seu estilo porque ouvi ontem.',))
    assert not realizacoes_opiniao(texto, contrato=contrato, turno_id=plano['id'])


@pytest.mark.parametrize('texto', ['você gosta de mim?', 'você gosta de você?',
    'você prefere meu estilo ou seu estilo?', 'você prefere esta música ou aquela música?',
    'você prefere chá ou café ou cerveja?'])
def test_objeto_deitico_nao_e_copiado_com_perspectiva_invertida(texto):
    _, plano, _ = preparar(texto)
    assert 'opiniao_autoral' not in plano['contrato_fala']


@pytest.mark.parametrize('texto', ['voce nao gosta de indie?', 'você não gosta de indie?'])
def test_pergunta_polar_negativa_preserva_ato_com_acentos(texto):
    _, plano, _ = preparar(texto)
    assert 'opiniao_autoral' in plano['contrato_fala']
    assert avaliar_qualidade_comunicacao(texto, 'Eu gosto de indie.', plano=plano)['aceita']


@pytest.mark.parametrize('objeto,declaracao', [('linux', 'Eu prefiro linux.'),
    ('café', 'Eu prefiro café.'), ('programar', 'Eu gosto de programar.')])
def test_esclarecer_a_propria_correcao_continua_ligado_a_declaracao(objeto, declaracao):
    from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
    texto = f'estou falando de {objeto}'
    _, plano, _ = preparar(texto, declaracao)
    fala = realizacoes_opiniao(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])[0]
    _, novo, _ = preparar('como assim?', fala)
    opcoes = realizacoes_opiniao('como assim?', contrato=novo['contrato_fala'], turno_id=novo['id'])
    assert opcoes and all(declaracao.casefold() in o.casefold() for o in opcoes)


@pytest.mark.parametrize('genero', ['jazz', 'rock', 'samba'])
def test_revisao_final_nao_transforma_opiniao_vinculada_em_fato_musical(genero):
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    texto = 'estou falando da música'
    _, plano, _ = preparar(texto, f'Eu não gosto de {genero}.')
    plano['dominio'] = 'musica'
    fala = f'Sim, estou falando de música: eu não gosto de {genero}.'
    r = verificar_fala_turno(fala, plano=plano)
    assert r['aceita'] and r['fala'] == fala, r


def test_revisao_final_continua_recusando_caracteristica_e_causa_extrapoladas():
    from mente_laylay.cognicao.plano_turno import verificar_fala_turno
    texto = 'estou falando da música'
    _, plano, _ = preparar(texto, 'Eu gosto de indie.')
    plano['dominio'] = 'musica'
    fala = 'Eu gosto de indie porque esse gênero tem jazz, rock e instrumentos que escutei ontem.'
    r = verificar_fala_turno(fala, plano=plano)
    assert not r['aceita']


def test_factory_instalada_preserva_opiniao_e_assunto_sem_voz_ou_efeitos(tmp_path):
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo = CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    folha = "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
    assert codigo.count(folha) == 1
    codigo = codigo.replace(folha, folha + "\n"
        "    schema=kwargs['json'].get('response_format',{}).get('json_schema',{}).get('schema',{})\n"
        "    unidade=schema.get('properties',{}).get('suporte_proposicoes',{}).get('items',{})\n"
        "    opcoes=unidade.get('properties',{}).get('texto',{}).get('enum',[])\n"
        "    if opcoes:proposta['suporte_proposicoes'][0]['texto']=next((o for o in opcoes if o in {'Eu prefiro jazz.','Eu gosto de indie.'}),opcoes[0])")
    codigo += """
rascunho='Eu gosto de indie porque é o que me faz ficar próxima de você.'
for pedido in ['qual o seu estilo musical?','como assim? voce nao tem nenhum em especifico?',
               'voce gosta de indie?','estou falando da musica','como assim?']:
    root._resposta_ia_runtime.processar(pedido,origem='teste_opiniao')
    resultados.append({'pedido':pedido,'plano':estado.mental['plano_turno_atual']})
sys.__stdout__.write('OPINIAO_JSON='+json.dumps({'falas':falas,'planos':resultados,'envios':envios,
 'efeitos':efeitos,'voz':False},ensure_ascii=False,default=str)+'\\n')
"""
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(tmp_path), '[]'],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=90)
    assert r.returncode == 0, r.stdout[-1800:] + r.stderr[-1800:]
    d = json.loads(next(l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('OPINIAO_JSON=')))
    assert not d['efeitos'] and not d['voz']
    assert d['falas'] == ['Eu prefiro jazz.', 'Quis dizer que eu prefiro jazz.', 'Eu gosto de indie.',
                          'Sim, estou falando de música: eu gosto de indie.', 'Quis dizer que eu gosto de indie.']
    assert all(not p['plano']['comandos'] and not p['plano']['autoriza_execucao'] for p in d['planos'])
    assert len(d['envios']) == 5, 'a rota primária deveria negociar o ato sem consumir tentativas com prosa rejeitada'
