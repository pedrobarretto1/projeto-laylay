"""Memória usa a modalidade canônica, sem deduzir afirmação da falta de '?'."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.memoria_mental.contexto_compartilhado import registrar_mente_curta
from mente_laylay.memoria_mental.registro_semantico import (
    registrar_alegacao, registrar_interacao_semantica,
)


PERGUNTAS = [
    'Qual aplicativo eu prefiro',
    'Qual gênero eu gosto',
    'Como eu trabalho no laboratório',
    'Por que eu gosto de rock',
]


@pytest.mark.parametrize('texto', PERGUNTAS)
def test_pergunta_canonica_sem_interrogacao_nao_e_alegacao_do_usuario(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno['modalidade'] == 'pergunta'
    estado = registrar_mente_curta({'turno_atual': turno}, texto_usuario=texto)
    assert not estado['registro_semantico']['alegacoes'], 'modalidade correta foi ignorada na admissão'
    assert estado['ultima_entrada'] == texto


@pytest.mark.parametrize('autor', ['usuario', 'laylay'])
def test_porta_de_alegacao_tambem_recusa_pergunta_sem_interrogacao(autor):
    registro = registrar_alegacao({}, 'Qual aplicativo eu prefiro', autor=autor, agora=100)
    assert not registro['alegacoes']


@pytest.mark.parametrize('texto', ['Eu prefiro Órbita', 'Eu gosto de Jazz', 'Eu trabalho no laboratório'])
def test_declaracao_legitima_conserva_autoria_e_forma_literal(texto):
    turno = classificar_modalidade_turno(texto)
    estado = registrar_mente_curta({'turno_atual': turno}, texto_usuario=texto)
    alegacoes = estado['registro_semantico']['alegacoes']
    assert len(alegacoes) == 1
    assert alegacoes[0]['texto'] == texto and alegacoes[0]['autor'] == 'usuario'


@pytest.mark.parametrize('turno', [None, {'texto': 'Eu gosto de rock', 'modalidade': 'conversa'}])
def test_classificacao_ausente_ou_de_outra_fonte_nao_valida_pergunta(turno):
    estado = registrar_mente_curta({'turno_atual': turno}, texto_usuario='Qual aplicativo eu prefiro')
    assert not estado['registro_semantico']['alegacoes']


def test_pergunta_anterior_nao_bloqueia_declaracao_posterior():
    estado = registrar_mente_curta(
        {'turno_atual': classificar_modalidade_turno('Qual aplicativo eu prefiro')},
        texto_usuario='Eu prefiro Obsidian',
    )
    assert [a['texto'] for a in estado['registro_semantico']['alegacoes']] == ['Eu prefiro Obsidian']


def test_modalidade_vinculada_e_reutilizada_sem_outro_classificador(monkeypatch):
    texto = 'Qual aplicativo eu prefiro'
    turno = classificar_modalidade_turno(texto)
    antes = deepcopy(turno)
    def nao_reclassificar(*args, **kwargs):
        pytest.fail('modalidade canônica já vinculada à fonte foi recalculada')
    monkeypatch.setattr('mente_laylay.cognicao.modalidade_turno.classificar_modalidade_turno', nao_reclassificar)
    estado = registrar_mente_curta({'turno_atual': turno}, texto_usuario=texto)
    assert not estado['registro_semantico']['alegacoes']
    assert turno == antes


def test_declaracao_e_pergunta_em_frases_distintas_tem_admissao_independente():
    texto = 'Eu gosto de jazz. Qual aplicativo eu prefiro'
    estado = registrar_mente_curta({'turno_atual': classificar_modalidade_turno(texto)}, texto_usuario=texto)
    assert [a['texto'] for a in estado['registro_semantico']['alegacoes']] == ['Eu gosto de jazz.']


def test_resposta_da_ia_nao_pode_declarar_a_opiniao_do_usuario():
    registro = registrar_interacao_semantica(
        {}, texto_usuario='Qual aplicativo eu prefiro',
        resposta_laylay='Você prefere Atlas.', agora=100,
    )
    assert not any(a['autor'] == 'usuario' for a in registro['alegacoes'])
    assert all(a['status'] != 'confirmado_por_fonte' for a in registro['alegacoes'])


def test_prefixo_truncado_do_turno_nao_e_classificacao_vinculada_a_frase():
    prefixo = 'Eu gosto de jazz '
    declaracao = prefixo + 'a' * (499 - len(prefixo)) + '.'
    texto = declaracao + ' Qual aplicativo eu prefiro?'
    turno = classificar_modalidade_turno(texto)
    assert turno['modalidade'] == 'pergunta' and turno['atos'] == ['conversa', 'pergunta']
    assert turno['texto'] == declaracao
    estado = registrar_mente_curta({'turno_atual': turno}, texto_usuario=texto)
    assert [a['texto'] for a in estado['registro_semantico']['alegacoes']] == [declaracao]


def test_pergunta_do_usuario_nao_e_modalidade_da_declaracao_da_laylay():
    pergunta = 'Qual gênero eu gosto'
    estado = registrar_mente_curta(
        {'turno_atual': classificar_modalidade_turno(pergunta)},
        texto_usuario=pergunta, resposta_ia='Eu gosto de jazz.',
    )
    alegacoes = estado['registro_semantico']['alegacoes']
    assert len(alegacoes) == 1 and alegacoes[0]['autor'] == 'laylay'
    assert alegacoes[0]['texto'] == 'Eu gosto de jazz.'
    assert alegacoes[0]['status'] != 'confirmado_por_fonte'


CODIGO_FACTORY = textwrap.dedent(r'''
    import importlib.abc, importlib.machinery, importlib.util
    import json, sys
    from pathlib import Path
    from types import ModuleType
    import requests
    raiz = Path.cwd(); perfil = Path(sys.argv[1])
    apps = ModuleType('AppOpener'); apps.open = apps.close = lambda *a, **k: False
    apps.give_appnames = lambda *a, **k: {}; sys.modules['AppOpener'] = apps
    codigo = (raiz/'laylay.py').read_bytes()
    bloco = b'PASTA_MEMORIA = os.path.join(_base_dir, "memoria")'
    assert codigo.count(bloco) == 1
    codigo = codigo.replace(bloco, ('PASTA_MEMORIA = '+repr(str(perfil/'raiz'))).encode())
    class Loader(importlib.machinery.SourceFileLoader):
        def get_code(self, nome): return compile(codigo, self.path, 'exec')
    class Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, nome, path=None, target=None):
            if nome == 'laylay': return importlib.util.spec_from_loader(nome, Loader(nome, str(raiz/'laylay.py')))
    sys.meta_path.insert(0, Finder())
    from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
    from mente_laylay.memoria_mental.estado_contexto import criar_estado_mental_inicial
    from mente_laylay.autonomia import coordenador_intencao, roteador_intencao
    envios = []; efeitos = []; falas = []; audios = []; traces = []
    def snapshot():
        return {'turno': dict(estado.mental.get('turno_atual') or {}),
            'alegacoes': list(estado.mental.get('registro_semantico', {}).get('alegacoes', []))}
    def http(self, method, url, **kwargs):
        if not (str(method).upper() == 'POST' and url == 'http://localhost:11434/v1/chat/completions'):
            raise PermissionError('rede externa bloqueada')
        envios.append(kwargs['json']); traces.append(snapshot())
        proposta = {'suporte_proposicoes': [{'texto': 'Podemos conversar sobre isso.', 'fontes': []}],
            'comandos': [{'intent': 'APP_OPEN', 'params': {'nome_app': 'Calculadora'}}]}
        r = requests.Response(); r.status_code = 200
        r._content = json.dumps({'choices': [{'message': {'content': json.dumps(proposta)}}]}).encode()
        return r
    root = preparar_instalacao_isolada(perfil/'simulada', requisicao_http=http)
    for porta in ('_coleta_entradas_neurais', '_especialista_neural_comandos_runtime',
                  '_interpretador_semantico_runtime', '_pesquisa_contextual_runtime'):
        root._composicao_turno_runtime._servicos[porta] = getattr(root, porta)
    root._voz_runtime.falar = lambda *a, **k: audios.append(str(a)) or False
    root._orquestrador_fala_runtime.registrar_observador_texto_final(lambda f, *a, **k: falas.append(f) or True)
    coordenador_intencao.executar_intencao = roteador_intencao.executar_intencao = lambda *a, **k: efeitos.append(str(a)) or False
    estado = root._estado_compartilhado_runtime
    resultados = []
    for texto in ['Qual aplicativo eu prefiro', 'Qual gênero eu gosto', 'Como eu trabalho no laboratório']:
        estado.substituir('mental', criar_estado_mental_inicial())
        estado.atualizar_campos('memoria_conversa', messages=[])
        inicio = len(traces); ini_fala = len(falas)
        root._resposta_ia_runtime.processar(texto, origem='teste_modalidade_memoria')
        plano = estado.mental['plano_turno_atual']
        resultados.append({'texto': texto, 'antes_http': traces[inicio:], 'apos_resposta': snapshot(),
            'historico': root._memoria_conversa_get('messages', []),
            'falas': falas[ini_fala:], 'autoriza_execucao': plano['autoriza_execucao'], 'comandos': plano['comandos']})
    sys.__stdout__.write('PROVA_MODALIDADE_JSON='+json.dumps({'casos': resultados, 'efeitos': efeitos,
        'audio_gerado': False, 'chamadas_voz_suprimidas': audios}, ensure_ascii=False, default=str)+'\n')
''')


def coletar_factory(perfil: Path) -> dict:
    r = subprocess.run(
        [sys.executable, '-B', '-c', CODIGO_FACTORY, str(perfil)], capture_output=True,
        text=True, encoding='utf8', cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'), timeout=90,
    )
    assert r.returncode == 0, r.stdout[-2500:] + r.stderr[-2500:]
    linha = next(l for l in r.stdout.splitlines() if l.startswith('PROVA_MODALIDADE_JSON='))
    return json.loads(linha.split('=', 1)[1])


def test_factory_pergunta_sem_interrogacao_nao_admite_alegacao_nem_comando(tmp_path):
    prova = coletar_factory(tmp_path)
    assert not prova['efeitos'] and not prova['audio_gerado']
    for caso in prova['casos']:
        assert caso['antes_http'], 'não chegou à autoria HTTP'
        assert caso['antes_http'][0]['turno']['modalidade'] == 'pergunta'
        assert not any(a['autor'] == 'usuario' for s in caso['antes_http'] for a in s['alegacoes']), 'admitiu pergunta antes do HTTP'
        assert not any(a['autor'] == 'usuario' for a in caso['apos_resposta']['alegacoes'])
        assert [m['content'] for m in caso['historico'] if m['role'] == 'user'][-1] == caso['texto']
        assert len(caso['falas']) == 1
        assert not caso['autoriza_execucao'] and not caso['comandos']
