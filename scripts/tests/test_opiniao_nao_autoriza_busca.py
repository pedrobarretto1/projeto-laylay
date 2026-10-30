"""Ato de opinião não vira busca pelo verbo ambíguo achar."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.normalizacao_linguagem import texto_pede_opiniao


HISTORICA = ('Já percebi momentos assim em relatos de pessoas, e concordo que uma pausa pode comunicar bastante. '
    'Percebi também que silêncio, tempo e pequenas descobertas sempre aparecem nas suas ideias. '
    'Você costuma voltar a esses temas mesmo quando começamos falando de outra coisa. Acha que isso faz parte do seu estilo?')


@pytest.mark.parametrize('texto', [
    HISTORICA, 'Acha que isso faz parte do seu estilo?', 'Acha que esse arquivo está bem organizado?',
    'Acha que a música combina com a história?', 'Acha sobre esse jogo?',
    'O que você acha do desenho?',
])
def test_consulta_de_opiniao_nao_herda_o_senso_operacional_de_achar(texto):
    if texto != HISTORICA:
        assert texto_pede_opiniao(texto), 'o leitor compartilhado já conhece esta moldura'
    t=classificar_modalidade_turno(texto)
    assert not t['autoriza_execucao'] and not t['texto_operacional']
    assert not any(s['autoriza_execucao'] for s in t['segmentos'])


@pytest.mark.parametrize('texto', [
    'Acha o arquivo notas.txt.', 'Ache uma música de rock.',
    'Acha a pasta de fotos.', 'Encontre o documento relatório.pdf.',
])
def test_busca_direta_mantem_autorizacao_sem_moldura_de_opiniao(texto):
    assert not texto_pede_opiniao(texto)
    assert classificar_modalidade_turno(texto)['autoriza_execucao']


@pytest.mark.parametrize('texto', [
    'Acha que isso faz parte do seu estilo? Abra o aplicativo Calculadora.',
    'Acha que o nome ficou bom? Pausa a música.',
    'Abra o aplicativo Calculadora. Acha que o nome ficou bom?',
])
def test_opiniao_nao_apaga_nem_autoriza_ordem_independente(texto):
    t=classificar_modalidade_turno(texto)
    assert t['autoriza_execucao']
    assert 'acha que' not in t['texto_operacional'].casefold()
    assert any(not s['autoriza_execucao'] for s in t['segmentos'])
    assert any(s['autoriza_execucao'] for s in t['segmentos'])


@pytest.mark.parametrize('texto', [
    'Abre o arquivo "O que você acha.txt".',
    'Abra o aplicativo "Qual a sua opinião".',
    'Acha o arquivo "Acha que isso faz parte do seu estilo.txt".',
])
def test_nome_literal_com_palavras_de_opiniao_nao_altera_o_ato_externo(texto):
    assert not texto_pede_opiniao(texto)
    assert classificar_modalidade_turno(texto)['autoriza_execucao']


def test_composicao_nao_executa_proposta_da_ia_para_pergunta_de_opiniao(tmp_path):
    import json, os, subprocess, sys
    from pathlib import Path
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo=CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    bloco="proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
    assert codigo.count(bloco)==1
    codigo=codigo.replace(bloco,"proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],"
        "'tipo_interacao':'acao','comandos':[{'intent':'APP_OPEN','params':{'nome_app':'Calculadora'}}]}")
    codigo+="\nrascunho='Essa pergunta é sobre o estilo das minhas respostas.'\n"
    codigo+='root._resposta_ia_runtime.processar('+repr(HISTORICA)+",origem='teste_opiniao_sem_busca')\n"
    codigo+='''
p=estado.obter_copia('mental','plano_turno_atual',{})
sys.__stdout__.write('OPINIAO_JSON='+json.dumps({'efeitos':efeitos,'falas':falas,
    'autoriza':p['autoriza_execucao'],'requer':p['requer_execucao']},ensure_ascii=False)+'\\n')
'''
    r=subprocess.run([sys.executable,'-B','-c',codigo,str(tmp_path),'[]'],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ,PYTHONIOENCODING='utf8',LAYLAY_NEURAL_MODE='off'),
        capture_output=True,text=True,encoding='utf8',timeout=45)
    assert r.returncode==0,r.stdout[-2000:]+r.stderr[-2000:]
    d=json.loads(next(l.split('=',1)[1] for l in r.stdout.splitlines() if l.startswith('OPINIAO_JSON=')))
    assert not d['autoriza'] and not d['requer'] and not d['efeitos']
    assert len(d['falas'])==1
