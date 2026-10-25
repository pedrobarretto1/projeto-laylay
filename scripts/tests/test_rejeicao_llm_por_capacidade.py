"""HTTP 400 é recusa da requisição, não evidência de serviço fora do ar."""
import pytest
import requests
import os
from pathlib import Path
import subprocess
import sys
import textwrap
import threading

from mente_laylay.integracao.llm_http import executar_chat_llm
from mente_laylay.cognicao.estado_tecnico_llm import categoria_estado_tecnico_llm
from mente_laylay.personalidade.contingencia_natural import fala_falha_geracao


def test_recusa_de_capacidade_sem_schema_nao_repete_nem_abre_circuito():
    from mente_laylay.integracao.llm_http import post_chat_llm
    r = requests.Response()
    r.status_code = 400
    r._content = b'request (4155 tokens) exceeds the available context size (4096 tokens)'
    chamadas = []
    resposta, circuito = post_chat_llm({}, {'messages': [{'role': 'user', 'content': 'pedido'}]},
        base_url='http://localhost:11434/v1', local_timeout=8, remote_timeout=30,
        bad_request_until=0, lock=threading.Lock(),
        requests_post=lambda *a, **k: chamadas.append(k['json']) or r, print_fn=lambda *a: None)
    assert chamadas == [{'messages': [{'role': 'user', 'content': 'pedido'}]}]
    assert resposta is r and circuito == 0


def test_capacidade_recusada_no_retry_preserva_resposta_sem_abrir_circuito():
    from mente_laylay.integracao.llm_http import post_chat_llm
    respostas = []
    for corpo in (b'unknown parameter', b'request (4155 tokens) exceeds the available context size (4096 tokens)'):
        r = requests.Response()
        r.status_code = 400
        r._content = corpo
        respostas.append(r)
    chamadas = []
    def post(*a, **k):
        chamadas.append(k['json'])
        return respostas[len(chamadas)-1]
    resposta, circuito = post_chat_llm({}, {'messages': [{'role': 'user', 'content': 'pedido'}]},
        base_url='http://localhost:11434/v1', local_timeout=8, remote_timeout=30,
        bad_request_until=0, lock=threading.Lock(), requests_post=post, print_fn=lambda *a: None)
    assert len(chamadas) == 2
    assert resposta is respostas[-1] and circuito == 0


@pytest.mark.parametrize('erro,categoria', [
    ('request (4155 tokens) exceeds the available context size (4096 tokens)', 'limite_contexto'),
    ('request (9000 tokens) exceeds the available context size (8192 tokens)', 'limite_contexto'),
    ('invalid schema', 'requisicao_recusada'), ('bad request', 'requisicao_recusada')])
def test_recusa_de_requisicao_conserva_causa_sem_anunciar_indisponibilidade(erro, categoria):
    r = requests.Response()
    r.status_code = 400
    r._content = erro.encode()
    r.url = 'http://localhost:11434/v1/chat/completions'
    falhas = []
    sentinela = executar_chat_llm({}, post_chat=lambda *_a, **_k: r,
        interpretar_payload=lambda _: '', api_key='', http_referer='', app_title='Laylay',
        endpoint_local=True, log=lambda _: None, registrar_falha=lambda *a, **k: falhas.append((a, k)))
    assert categoria_estado_tecnico_llm(sentinela) == categoria
    fala = fala_falha_geracao(categoria)
    assert fala and 'indisponível' not in fala and '__LAYLAY' not in fala
    assert falhas[0][0][1] == categoria


def test_recusa_http_preserva_causa_ate_publicacao_na_composicao_instalada(tmp_path):
    codigo = textwrap.dedent(r'''
        from pathlib import Path
        import sys, requests
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        chamadas = []
        corpo = ['request (4155 tokens) exceeds the available context size (4096 tokens)']
        def http(*args, **kwargs):
            chamadas.append(kwargs.get('json'))
            resposta = requests.Response()
            resposta.status_code = 400
            resposta._content = corpo[0].encode()
            resposta.url = 'http://localhost:11434/v1/chat/completions'
            return resposta
        root = preparar_instalacao_isolada(Path(sys.argv[1]), requisicao_http=http)
        from mente_laylay.autonomia import coordenador_intencao
        executores, falas = [], []
        coordenador_intencao.executar_intencao = lambda *args, **kwargs: executores.append(args) or False
        root._voz_runtime.falar = lambda *args, **kwargs: False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda fala, *args, **kwargs: falas.append(str(fala)) or True)
        root._resposta_ia_runtime._contexto()['estado_conversa'].substituir([
            {'role': 'user', 'content': 'nunca escutei Nevermind'},
            {'role': 'assistant', 'content': 'Estávamos conversando sobre Nevermind.'}])
        for texto, erro, esperado in [
            ('pode colocar ele para mim ouvir', corpo[0], 'acomodar'),
            ('vamos continuar conversando sobre música', 'invalid schema', 'preparação')]:
            corpo[0] = erro
            antes = len(chamadas), len(falas)
            root._resposta_ia_runtime.processar(texto, origem='teste_recusa_http')
            # O pedido prático agora alcança o intérprete, antes da autoria.
            # São duas requisições distintas, cada uma sem retry permissivo.
            novas = chamadas[antes[0]:]
            assert len(novas) == (2 if texto.startswith('pode colocar') else 1)
            assert novas[-1].get('response_format', {}).get('type') == 'json_schema'
            if len(novas) == 2:
                assert not novas[0].get('response_format')
                assert novas[0]['messages'] != novas[1]['messages']
            assert len(falas) == antes[1] + 1, 'turno consumido precisa de conclusão'
            assert esperado in falas[-1] and 'indisponível' not in falas[-1], falas[-1]
            assert '__LAYLAY' not in falas[-1] and executores == []
    ''')
    processo = subprocess.run([sys.executable, '-c', codigo, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2],
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'),
        capture_output=True, text=True, encoding='utf-8', timeout=60)
    assert processo.returncode == 0, processo.stdout[-2500:] + processo.stderr[-2500:]
