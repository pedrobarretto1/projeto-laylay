"""Declarar um gosto não registra sua causa; a pergunta posterior deve conservar esse limite."""
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

from scripts.tests.test_opiniao_autoral_conferivel import preparar
from mente_laylay.cognicao.opiniao_autoral import realizacoes_opiniao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno


@pytest.mark.parametrize('anterior,pedido,inventada', [
    ('Eu não gosto de indie.', 'por que você não gosta de indie?',
     'Eu não gosto de indie porque não tenho opinião sobre gêneros musicais.'),
    ('Eu gosto de rock.', 'por que você gosta de rock?',
     'Eu gosto de rock porque escutei ontem e me emocionei.'),
    ('Eu prefiro linux.', 'por que você prefere Linux?',
     'Eu prefiro linux porque ele é mais leve, mais seguro e dá mais controle.'),
    ('Eu prefiro chá.', 'por quê?',
     'Eu prefiro chá porque provei e achei mais gostoso.'),
])
def test_pergunta_de_motivo_exige_apoio_distinto_da_posicao(anterior, pedido, inventada):
    _, plano, _ = preparar(pedido, anterior)
    fonte = plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is not None and fonte.modo == 'explicacao_gosto'
    opcoes = realizacoes_opiniao(pedido, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes and all(anterior.casefold() in o.casefold() for o in opcoes)
    assert all('motivo' in o.casefold() and 'não' in o.casefold() for o in opcoes)
    r = verificar_fala_turno(inventada, plano=plano)
    assert not r['aceita'], 'a preferência foi usada como prova de sua própria causa'
    for opcao in opcoes:
        r = verificar_fala_turno(opcao, plano=plano)
        assert r['aceita'] and r['fala'] == opcao, r


@pytest.mark.parametrize('pedido', ['por que você gosta de jazz?', 'por que você prefere indie?',
                                   'por que você gosta de indie?'])
def test_premissa_diferente_nao_muda_o_gosto_publicado(pedido):
    _, plano, _ = preparar(pedido, 'Eu não gosto de indie.')
    opcoes = realizacoes_opiniao(pedido, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes and all('não' in o.casefold() for o in opcoes)
    assert 'Eu gosto de jazz.' not in opcoes and 'Eu gosto de indie.' not in opcoes
    assert not verificar_fala_turno('Eu gosto de jazz porque é tranquilo.', plano=plano)['aceita']


@pytest.mark.parametrize('pedido', ['por que você gosta de indie?'])
def test_sem_publicacao_nao_inventa_gosto_nem_a_causa(pedido):
    _, plano, _ = preparar(pedido)
    opcoes = realizacoes_opiniao(pedido, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes and all('não' in o.casefold() for o in opcoes)
    assert all('gosto de indie' not in o.casefold() for o in opcoes)


@pytest.mark.parametrize('anterior', ['', 'A luz foi ligada.', 'O arquivo foi salvo.'])
def test_por_que_eliptico_sem_gosto_vinculado_nao_captura_owner_de_acao(anterior):
    _, plano, _ = preparar('por quê?', anterior)
    fonte = plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is None or fonte.modo != 'explicacao_gosto'


@pytest.mark.parametrize('pedido', ['por que você abriu o arquivo?', 'por que você tocou rock?',
    'por que João gosta de indie?', 'a frase "por que você gosta de indie?" é uma pergunta?',
    'por que você gosta de indie? abre a calculadora'])
def test_explicacao_de_gosto_nao_captura_acao_terceiro_citacao_ou_composto(pedido):
    _, plano, _ = preparar(pedido, 'Eu gosto de indie.')
    assert 'opiniao_autoral' not in plano['contrato_fala']


def test_causa_textual_antiga_nao_vira_justificativa_comprovada():
    pedido = 'por que você gosta de indie?'
    _, plano, _ = preparar(pedido, 'Eu gosto de indie porque ouvi ontem e me emocionei.')
    opcoes = realizacoes_opiniao(pedido, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes and all('ouvi' not in o and 'emocionei' not in o for o in opcoes)


def test_repetir_a_pergunta_de_motivo_preserva_o_mesmo_limite():
    _, plano, _ = preparar('por quê?', 'Eu prefiro chá.')
    opcoes = realizacoes_opiniao('por quê?', contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes
    _, novo, _ = preparar('por quê?', opcoes[0])
    outras = realizacoes_opiniao('por quê?', contrato=novo['contrato_fala'], turno_id=novo['id'])
    assert outras and all('Eu prefiro chá.' in o for o in outras)


def test_apoio_de_outro_turno_nao_justifica_opiniao():
    _, plano, _ = preparar('por quê?', 'Eu prefiro chá.')
    fonte = plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is not None
    plano['contrato_fala']['opiniao_autoral'] = replace(fonte, turno_id='outro')
    assert not realizacoes_opiniao('por quê?', contrato=plano['contrato_fala'], turno_id=plano['id'])


def coletar_factory(perfil):
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo = CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    folha = "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
    assert codigo.count(folha) == 1
    codigo = codigo.replace(folha, folha + "\n"
        "    schema=kwargs['json'].get('response_format',{}).get('json_schema',{}).get('schema',{})\n"
        "    unidade=schema.get('properties',{}).get('suporte_proposicoes',{}).get('items',{})\n"
        "    opcoes=unidade.get('properties',{}).get('texto',{}).get('enum',[])\n"
        "    if opcoes:proposta['suporte_proposicoes'][0]['texto']=next((o for o in opcoes if o=='Eu não gosto de indie.'),opcoes[0])")
    codigo += """
from mente_laylay.autonomia import processamento_resposta_ia
avaliar_original=processamento_resposta_ia.avaliar_qualidade_comunicacao
tracos=[]
def observar_qualidade(texto,fala,**kwargs):
    r=avaliar_original(texto,fala,**kwargs)
    tracos.append({'texto':texto,'fala':fala,'parecer':r})
    return r
processamento_resposta_ia.avaliar_qualidade_comunicacao=observar_qualidade
rascunho=''
for pedido in ['você gosta de indie?','por que você não gosta de indie?']:
    root._resposta_ia_runtime.processar(pedido,origem='teste_motivo')
sys.__stdout__.write('MOTIVO_JSON='+json.dumps({'falas':falas,'tracos':tracos,'envios':envios,
 'plano':estado.mental['plano_turno_atual'],'efeitos':efeitos,'voz':False},ensure_ascii=False,default=str)+'\\n')
"""
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(perfil), '[]'],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=90)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return json.loads(next(l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('MOTIVO_JSON=')))


def test_factory_publica_limite_da_explicacao_sem_inventar_causa(tmp_path):
    d = coletar_factory(tmp_path)
    assert not d['efeitos'] and not d['voz']
    assert len(d['falas']) == 2
    assert d['falas'][-1] == 'Eu não gosto de indie. Essa fala não trouxe um motivo para a preferência.', d['tracos']


def test_realizacao_do_limite_chega_integra_pela_higiene_compartilhada():
    from mente_laylay.personalidade.higiene_fala import remover_residuos_operacionais
    pedido = 'por quê?'
    _, plano, _ = preparar(pedido, 'Eu prefiro chá.')
    opcoes = realizacoes_opiniao(pedido, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert opcoes
    assert all(remover_residuos_operacionais(o) == o for o in opcoes)


@pytest.mark.parametrize('fala', ['Eu gosto de indie porque sim.',
    'Eu gosto de jazz pois anima.', 'Eu prefiro linux porque sim.',
    'Eu gosto de jazz por relaxar.', 'Eu prefiro chá para relaxar.'])
def test_oracao_causal_curta_nao_e_tratada_como_nome_do_objeto(fala):
    _, plano, _ = preparar('por quê?', fala)
    opcoes = realizacoes_opiniao('por quê?', contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert not opcoes or all(fala not in o for o in opcoes)


@pytest.mark.parametrize('pedido', ['por quê?', 'porquê?', 'porque?', 'por que?',
                                   'porque você prefere Linux?'])
def test_grafias_da_pergunta_de_motivo_mantem_o_mesmo_contrato(pedido):
    _, plano, _ = preparar(pedido, 'Eu prefiro linux.')
    fonte = plano['contrato_fala'].get('opiniao_autoral')
    assert fonte is not None and fonte.modo == 'explicacao_gosto'
