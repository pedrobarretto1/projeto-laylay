"""Nome explícito não apaga formato; seletor conserva a restrição recebida."""
import json
import pytest
from mente_laylay.cognicao.refinamento_pesquisa import refinar_consulta_musical
from mente_laylay.memoria_mental.busca_youtube import extrair_resultados_youtube_busca


def video(id, titulo, duracao):
    return json.dumps({'videoId': id, 'title': {'runs': [{'text': titulo}]},
        'longBylineText': {'runs': [{'text': 'Canal musical'}]},
        'lengthText': {'simpleText': duracao}}, ensure_ascii=False, separators=(',', ':'))


@pytest.mark.parametrize('nome', ['Nevermind', 'In Utero', 'Clube da Esquina'])
def test_formato_album_nao_e_rebaixado_por_query_nomeada(nome):
    p = refinar_consulta_musical(nome, 'pode colocar ele para mim ouvir', {'query': nome, 'formato': 'album'})
    assert p['query'] == nome
    assert p['tipo_resultado'] == 'album'
    html = video('abcdefghijk', nome + ' - Official Audio', '3:50')
    html += video('lmnopqrstuv', nome + ' music mix 1 hour', '1:00:00')
    html += video('wxyz1234567', nome + ' - Full Album', '42:30')
    r = extrair_resultados_youtube_busca(html, p['query'], tipo_resultado=p['tipo_resultado'])
    assert [v['video_id'] for v in r] == ['wxyz1234567']


def test_album_incompativel_nao_cai_em_faixa_ou_mix():
    html = video('abcdefghijk', 'In Utero - Official Audio', '3:50')
    html += video('lmnopqrstuv', 'In Utero music mix 1 hour', '1:00:00')
    assert extrair_resultados_youtube_busca(html, 'In Utero', tipo_resultado='album') == []


def test_album_curto_integral_nao_herda_minimo_de_mix_longo():
    html = video('abcdefghijk', 'Nome de Álbum - Full Album', '15:20')
    r = extrair_resultados_youtube_busca(html, 'Nome de Álbum', tipo_resultado='album')
    assert len(r) == 1


def test_tipo_faixa_continua_rejeitando_album_integral():
    html = video('abcdefghijk', 'In Utero - Full Album', '42:30')
    assert extrair_resultados_youtube_busca(html, 'In Utero', tipo_resultado='faixa') == []


@pytest.mark.parametrize('album_disponivel', [False, True])
def test_executor_conserva_perfil_e_selecao_e_nao_inventa_confirmacao(album_disponivel):
    from mente_laylay.autonomia.executor_musical import executar_intencao_musical, DependenciasExecutorMusical
    html = video('abcdefghijk', 'In Utero - Official Audio', '3:50')
    if album_disponivel:
        html += video('wxyz1234567', 'Nirvana In Utero - Full Album', '42:30')
    selecoes, aberturas, resultados = [], [], []
    def selecionar(query, *, tipo_resultado):
        selecoes.append((query, tipo_resultado))
        itens = extrair_resultados_youtube_busca(html, query, tipo_resultado=tipo_resultado)
        return itens[0] if itens else {}
    def recusar_abertura(url, **kwargs):
        aberturas.append(url)
        return {'ok': False, 'confirmado': False, 'status': 'recusa_controlada'}
    params = {'query': 'In Utero', 'formato': 'album'}
    despacho = executar_intencao_musical('MUSIC_SEARCH', params,
        'pode colocar ele para mim ouvir', {
            '_autonomia_permite_execucao_musical': lambda *a, **k: True,
            '_resolver_query_musical_por_estilo': refinar_consulta_musical,
            '_resolver_primeiro_video_youtube': selecionar},
        DependenciasExecutorMusical(marcar_resultado=lambda s, **k: resultados.append((s,k)),
            abrir_url_musical=recusar_abertura))
    assert selecoes == [('In Utero', 'album')]
    assert despacho.tratado and despacho.retorno is False
    assert aberturas == (['https://www.youtube.com/watch?v=wxyz1234567'] if album_disponivel else [])
    assert resultados and all(not r['executou'] and not r['confirmado'] for _,r in resultados)


@pytest.mark.parametrize('titulo', ['Nirvana - Nevermind Full Album Official Audio',
    'Nirvana - In Utero Full Album Cover', 'Nirvana - In Utero Full Album Mix',
    'Nirvana - In Utero Full Album Instrumental', 'Nirvana - In Utero Full Album Karaoke'])
def test_formato_nao_compensa_alvo_ou_variacao_diferente(titulo):
    html = video('abcdefghijk', titulo, '42:30')
    assert extrair_resultados_youtube_busca(html, 'In Utero', tipo_resultado='album') == []


def test_variacao_explicitamente_solicitada_continua_elegivel():
    html = video('abcdefghijk', 'Nirvana - In Utero Full Album Cover', '42:30')
    assert len(extrair_resultados_youtube_busca(html, 'In Utero cover', tipo_resultado='album')) == 1


@pytest.mark.parametrize('compativel', [False, True])
def test_composicao_instalada_preserva_album_ate_selecao_e_receipt_negativo(tmp_path, compativel):
    import os, sys, subprocess, textwrap
    from pathlib import Path
    codigo = textwrap.dedent(r'''
        import sys, json, requests
        from pathlib import Path
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        from scripts.tests.test_formato_recurso_musical import video
        compativel = sys.argv[2] == '1'
        html = video('abcdefghijk', 'Nirvana Nevermind Full Album Official Audio', '42:30')
        html += video('lmnopqrstuv', 'Nirvana In Utero Full Album Cover', '42:30')
        if compativel: html += video('wxyz1234567', 'Nirvana In Utero Full Album', '42:30')
        consultas, aberturas, publicadas, modelos = [], [], [], []
        def http(self, method, url, **kwargs):
            assert url.startswith('https://www.youtube.com/results?'), url
            assert modelos == [], 'a seleção não depende de geração'
            consultas.append(url)
            r = requests.Response()
            r.status_code = 200
            r._content = html.encode('utf8')
            r.encoding = 'utf8'
            return r
        root = preparar_instalacao_isolada(Path(sys.argv[1]), requisicao_http=http)
        from mente_laylay.autonomia.rota_musical import RotaMusical
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM
        def recusar(self, url, **kwargs):
            assert modelos == [], 'a execução não depende de geração'
            aberturas.append(url)
            return {'ok': False, 'confirmado': False, 'status': 'recusa_controlada'}
        RotaMusical.abrir_detalhado = recusar
        def modelo(self, pedido):
            contrato = dict(root._estado_compartilhado_runtime.mental.get('ultima_acao_contrato') or {})
            modelos.append((pedido.tipo_chamada, len(consultas), list(aberturas), contrato))
            raise ConnectionError('autoria indisponível de forma controlada no teste')
        RegistroModeloLLM.executar = modelo
        root._voz_runtime.falar = lambda *a, **k: False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda fala, *a, **k: publicadas.append(str(fala)) or True)
        root._iniciar_planejamento_turno('nunca escutei o álbum In Utero')
        root._resposta_ia_runtime.processar('pode colocar ele para mim ouvir', origem='teste_album_instalado')
        assert len(consultas) == 1, consultas
        assert aberturas == (['https://www.youtube.com/watch?v=wxyz1234567'] if compativel else []), aberturas
        mental = root._estado_compartilhado_runtime.mental
        contrato = mental['ultima_acao_contrato']
        assert contrato['executou'] is False and contrato['confirmado'] is False, contrato
        assert len(modelos) == 1, modelos
        tipo, consultas_antes, aberturas_antes, receipt_antes = modelos[0]
        assert tipo == 'autoria_operacional', modelos
        assert consultas_antes == 1 and aberturas_antes == aberturas, modelos
        assert receipt_antes['executou'] is False and receipt_antes['confirmado'] is False, modelos
        assert publicadas, 'falha pedida pelo usuário precisa de conclusão observável'
    ''')
    p = subprocess.run([sys.executable, '-c', codigo, str(tmp_path), '1' if compativel else '0'],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding='utf8',
        env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'), timeout=60)
    assert p.returncode == 0, p.stdout[-4000:] + p.stderr[-2500:]
