"""Contexto anterior não torna todas as perguntas consultas históricas de efeito."""
import pytest
import json
import os
from pathlib import Path
import subprocess
import sys

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada


@pytest.mark.parametrize('texto', [
    'como assim? voce nao tem nenhum em especifico?',
    'como assim? você pode ser mais clara?',
    'como assim? você está falando da música?',
])
def test_perguntas_conversacionais_nao_sao_consumidas_por_contrato_historico_sem_fontes_por_ato(texto):
    fala = 'Meu estilo musical mistura sons suaves com samba e jazz.'
    registro = registrar_fala_observada(None, ocorrencia_id='fala_real', turno_id='anterior',
        fala=fala, resultados=(), canal='texto_publicado')
    mente = {'registro_semantico': registro, 'ultima_resposta': fala}
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente=mente)
    contrato = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert len(turno['segmentos']) == 2
    assert all(s['contrato_explicativo']['relacao'] == 'resposta_conversacional' for s in turno['segmentos'])
    assert 'explicacoes_historicas_por_ato' not in contrato, 'fonte global capturou atos sem fonte histórica própria e vai publicar resposta interna de pendência'


def test_factory_publica_resposta_conversacional_em_vez_de_pendencia_historica(tmp_path):
    from scripts.tests.test_modo_pessoal_apoio_relato import CODIGO_FACTORY
    codigo = CODIGO_FACTORY.split('for fonte,pedido,rascunho in casos:')[0]
    assert codigo != CODIGO_FACTORY
    folha = "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}"
    assert codigo.count(folha) == 1
    codigo = codigo.replace(folha, "proposta={'suporte_proposicoes':[{'texto':rascunho,'fontes':[]}],'comandos':[]}\n"
        "    schema=kwargs['json'].get('response_format',{}).get('json_schema',{}).get('schema',{})\n"
        "    unidade=schema.get('properties',{}).get('suporte_proposicoes',{}).get('items',{})\n"
        "    opcoes=unidade.get('properties',{}).get('texto',{}).get('enum',[])\n"
        "    if opcoes:proposta['suporte_proposicoes'][0]['texto']=next((o for o in opcoes if 'jazz' in o.casefold()),opcoes[0])")
    codigo += """
rascunho='Eu prefiro jazz.'
root._resposta_ia_runtime.processar('qual o seu estilo musical?',origem='teste_esclarecimento')
registro_antes=estado.mental['registro_semantico']
rascunho='Quis dizer que prefiro jazz. Esse é o estilo específico.'
root._resposta_ia_runtime.processar('como assim? voce nao tem nenhum em especifico?',origem='teste_esclarecimento')
sys.__stdout__.write('ESCLARECIMENTO_JSON='+json.dumps({'falas':falas,'plano':estado.mental['plano_turno_atual'],
 'registro_antes':registro_antes,'efeitos':efeitos,'voz':False},ensure_ascii=False,default=str)+'\\n')
"""
    r = subprocess.run([sys.executable, '-B', '-c', codigo, str(tmp_path), '[]'],
        cwd=Path(__file__).resolve().parents[2], env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf8', timeout=80)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    d = json.loads(next(l.split('=', 1)[1] for l in r.stdout.splitlines() if l.startswith('ESCLARECIMENTO_JSON=')))
    assert d['registro_antes']['falas_observadas'], 'não houve publicação real da fonte de contexto'
    assert len(d['falas']) == 2 and not d['efeitos'] and not d['voz']
    assert 'explicacoes_historicas_por_ato' not in d['plano']['contrato_fala']
    assert 'jazz' in d['falas'][-1].casefold() and 'ainda não foi respondida' not in d['falas'][-1]
    assert not d['plano']['autoriza_execucao'] and not d['plano']['comandos']
