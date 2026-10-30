"""Citação fiel não substitui a relação com o conteúdo consultado."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.tests.test_retomada_usuario_preserva_autoria import plano_com_fonte
from mente_laylay.cognicao.fundamentacao_factual import avaliar_nucleo_retomada_usuario, realizacoes_retomada_usuario
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno


CASOS = [
    ('eu gosto de rock', 'eu não gosto de chá', 'eu contei que não gosto de rock?'),
    ('eu uso Obsidian', 'eu uso Blender', 'eu falei que uso Obsidian?'),
    ('eu trabalho no hospital', 'eu trabalho no laboratório', 'eu mencionei que trabalho no hospital?'),
    ('Meu cachorro fica em casa.', 'Meu gato fica no quintal.', 'o que eu disse sobre meu cachorro?'),
    ('eu estudo física', 'eu estudo química', 'o que eu contei a respeito de física?'),
    ('eu viajei para Recife', 'eu viajei para Salvador', 'o que eu comentei acerca de Recife?'),
]


def plano_duas_fontes(fonte, distrator, pedido):
    plano = plano_com_fonte(fonte, pedido, f'Você contou: «{distrator}».')
    plano['relatos_usuario'].append({'id': 'dialogo:usuario:3:' + hashlib.sha256(distrator.encode()).hexdigest(),
        'texto': distrator, 'autor': 'usuario', 'origem': 'historico_conversa', 'status': 'relatado_pelo_usuario'})
    return plano


@pytest.mark.parametrize('fonte,distrator,pedido', CASOS)
def test_nucleo_fiel_de_outro_assunto_nao_responde_ao_conteudo_consultado(fonte, distrator, pedido):
    plano = plano_duas_fontes(fonte, distrator, pedido)
    ruim = f'Você contou: «{distrator}».'
    boa = f'Você contou: «{fonte}».'
    assert avaliar_nucleo_retomada_usuario(boa, plano=plano)['admissivel']
    r = avaliar_nucleo_retomada_usuario(ruim, plano=plano)
    assert not r['admissivel'], 'existência no histórico foi aceita como resposta à pergunta de outro assunto'
    assert 'retomada_usuario_sem_nucleo_conferido' in avaliar_qualidade_comunicacao(pedido, ruim, plano=plano)['problemas_bloqueantes']
    assert verificar_fala_turno(ruim, plano=plano)['fala'] != ruim
    assert boa in realizacoes_retomada_usuario(plano=plano)
    assert ruim not in realizacoes_retomada_usuario(plano=plano)


def test_parafrase_atribuida_tambem_precisa_corresponder_ao_conteudo_da_pergunta():
    plano = plano_duas_fontes(*CASOS[0])
    assert not avaliar_nucleo_retomada_usuario('Você disse que não gosta de chá.', plano=plano)['admissivel']
    assert avaliar_nucleo_retomada_usuario('Você disse que gosta de rock.', plano=plano)['admissivel']


@pytest.mark.parametrize('conector', ['e ', 'então '])
@pytest.mark.parametrize('fonte,distrator,pedido', CASOS)
def test_abertura_discursiva_preserva_o_mesmo_conteudo_consultado(conector, fonte, distrator, pedido):
    test_nucleo_fiel_de_outro_assunto_nao_responde_ao_conteudo_consultado(fonte, distrator, conector + pedido)


@pytest.mark.parametrize('topico', ['Recife', 'física', 'meu cachorro'])
def test_coincidencia_parcial_de_nome_nao_estabelece_o_topico(topico):
    fonte = f'Falamos sobre {topico}.'
    distrator = f'Falamos sobre {topico}extra.'
    pedido = f'o que eu disse sobre {topico}?'
    plano = plano_duas_fontes(fonte, distrator, pedido)
    assert not avaliar_nucleo_retomada_usuario(f'Você contou: «{distrator}».', plano=plano)['admissivel']


@pytest.mark.parametrize('fonte', ['eu gosto de rock', 'eu não gosto de rock'])
def test_negacao_na_pergunta_nao_e_assumida_como_preferencia_declarada(fonte):
    plano = plano_duas_fontes(fonte, 'eu gosto de jazz', CASOS[0][2])
    r = avaliar_nucleo_retomada_usuario(f'Você contou: «{fonte}».', plano=plano)
    assert r['admissivel']
    assert not any(r[k] for k in ['semantica_verificada', 'prova_implicacao', 'autoriza_execucao', 'pode_confirmar_fato_externo'])


def coletar_factory(perfil: Path, positivo: bool):
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    casos = [(f, p, fala) for f, d, p in CASOS[:4]
             for fala in [f'Você contou: «{d}».', f'Você contou: «{f}».']]
    codigo = CODIGO_FACTORY
    bloco = "historico=[{'role':'user','content':fonte},"
    assert codigo.count(bloco) == 1
    codigo = codigo.replace(bloco, bloco + "{'role':'user','content':" + repr({p: d for _, d, p in CASOS}) + ".get(pedido,'')},")
    if positivo:
        folha = "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
        assert codigo.count(folha) == 1
        codigo = codigo.replace(folha, "texto_proposto=rascunho\n"
            "    try:tarefa=json.loads(kwargs['json']['messages'][-1]['content'])\n"
            "    except (ValueError,TypeError):tarefa={}\n"
            "    if isinstance(tarefa,dict) and 'retomada_usuario_sem_nucleo_conferido' in tarefa.get('problemas',[]):\n"
            "        texto_proposto=" + repr({p: f'Você contou: «{f}».' for f, _, p in CASOS}) + ".get(tarefa.get('mensagem_atual'),rascunho)\n"
            "    proposta={'suporte_proposicoes':[{'texto':texto_proposto,'fontes':[]}],'comandos':[]}")
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(perfil), json.dumps(casos)],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=100)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return json.loads(next(l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('MODO_PESSOAL_JSON=')))


@pytest.mark.parametrize('positivo', [False, True])
def test_factory_confere_pergunta_e_fonte_antes_de_publicar_uma_resposta(positivo, tmp_path):
    d = coletar_factory(tmp_path, positivo)
    assert not d['efeitos'] and not d['audio_gerado']
    for i, c in enumerate(d['casos']):
        fonte, distrator, _ = CASOS[i // 2]
        assert any(f['texto'] == fonte for f in c['plano']['relatos_usuario'])
        assert any(f['texto'] == distrator for f in c['plano']['relatos_usuario'])
        assert len(c['respostas']) == 1
        if i % 2 == 0:
            assert c['respostas'] != [f'Você contou: «{distrator}».'], 'factory publicou fonte fiel porém alheia à pergunta'
            if positivo: assert c['respostas'] == [f'Você contou: «{fonte}».']
        else:
            assert c['respostas'] == [c['rascunho']]
        assert not c['plano']['autoriza_execucao'] and not c['plano']['comandos']
