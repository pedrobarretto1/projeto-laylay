"""Nome catalogado e interrogação não constituem pedido de dados."""
import json
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from mente_laylay.cognicao.normalizacao_linguagem import texto_pede_opiniao
from mente_laylay.memoria_mental.mapa_recursos import MapaRecursosRuntime
from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime


@pytest.fixture
def mapa(tmp_path):
    arquivo = tmp_path / 'playlists.json'
    arquivo.write_text(json.dumps({'rock': [{'titulo': 'Faixa A'}], 'metal': []}), encoding='utf8')
    playlist = PlaylistRuntime(state_file=str(arquivo), legacy_file=str(tmp_path / 'legacy.json'),
                               cache={}, ultima_playlist_getter=lambda: 'rock', log=lambda *_: None)
    mapa = MapaRecursosRuntime()
    mapa.registrar('playlists_usuario', arquivo=str(arquivo), descricao='Catálogo real do teste',
        termos=('playlist', 'musicas salvas'), leitor=playlist.retrato_para_mente,
        objetos_consulta=('musica', 'faixa'),
        intent_consulta='PLAYLIST_LIST', parametro_detalhe='nome_playlist')
    return mapa


@pytest.mark.parametrize('texto', [
    'você gosta de rock?', 'voce gosta de rock', 'você curte rock?', 'gosta de rock?',
    'você prefere rock ou metal?', 'qual é o seu gênero favorito: rock ou metal?',
    'o que você acha de rock?', 'você já ouviu falar de rock?', 'rock é interessante?',
    'por que rock é popular?', 'rock?', 'você sonha com rock?',
    'o que é rock?', 'qual a diferença entre rock e metal?',
    'quais instrumentos são comuns no rock?',
])
def test_assunto_homonimo_nao_inventa_pedido_de_leitura(mapa, texto):
    assert mapa.resolver_consulta(texto) is None, 'nome catalogado substituiu finalidade da pergunta'
    assert mapa.contexto_para_prompt(texto) == '', 'conteúdo da playlist vazou para conversa sobre outro assunto'


@pytest.mark.parametrize('nome,intent', [('rock', 'PLAYLIST_LIST'), ('viagem', 'LISTAR_AGENDAMENTOS'),
                                        ('anotações', 'INBOX_LIST')])
@pytest.mark.parametrize('moldura', ['você gosta de {}?', 'você curte {}?', 'você já sonhou com {}?'])
def test_mesmo_contrato_protege_recursos_de_dominios_diferentes(nome, intent, moldura):
    mapa = MapaRecursosRuntime()
    leituras = []
    def ler(texto):
        leituras.append(texto)
        return {'detalhe': {'nome': nome, 'titulos': ['Dado observado']}}
    mapa.registrar('recurso', arquivo='teste', descricao='Fonte controlada', termos=(nome,),
                   leitor=ler, intent_consulta=intent, parametro_detalhe='alvo')
    assert mapa.resolver_consulta(moldura.format(nome)) is None
    assert leituras == [], 'leitura executável não deveria começar sem pedido de dados'


@pytest.mark.parametrize('texto', ['quantas músicas tem na playlist rock?',
    'quais músicas tem a playlist rock?', 'o que tem em rock?', 'mostra a playlist rock',
    'quais são minhas playlists?'])
def test_pedido_de_dados_mantem_rota_real(mapa, texto):
    r = mapa.resolver_consulta(texto)
    assert r is not None and r['intent'] == 'PLAYLIST_LIST'


@pytest.mark.parametrize('texto', [
    'qual é a definição de playlist?',
    'qual é a diferença entre a playlist rock e um álbum?',
    'quais instrumentos são comuns nas playlists de rock?',
    'mostra a diferença entre a playlist rock e um álbum',
    'quantas pessoas gostam da playlist rock?',
    'quantas pessoas tem na playlist rock?',
    'quais instrumentos tem na playlist rock?',
    'quantas músicas de jazz tem na playlist rock?',
])
def test_namespace_nao_substitui_objeto_do_pedido(mapa, texto):
    assert mapa.resolver_consulta(texto) is None


@pytest.mark.parametrize('texto', [
    'quantas músicas tem em rock?', 'quais músicas tem em rock?',
    'mostra rock', 'lista minhas playlists',
])
def test_consulta_de_conteudo_preserva_fonte_e_alvo(mapa, texto):
    resultado = mapa.resolver_consulta(texto)
    assert resultado is not None and resultado['intent'] == 'PLAYLIST_LIST'
    assert 'rock' in mapa.contexto_para_prompt(texto)


@pytest.mark.parametrize('termo,objeto,intent', [
    ('playlist', 'musica', 'PLAYLIST_LIST'),
    ('agenda', 'compromisso', 'LISTAR_AGENDAMENTOS'),
    ('caderno', 'nota', 'INBOX_LIST'),
])
def test_objeto_e_escopo_tem_contratos_independentes_em_cada_recurso(termo, objeto, intent):
    mapa = MapaRecursosRuntime()
    mapa.registrar('recurso', arquivo='teste', descricao='recurso controlado', termos=(termo,),
        objetos_consulta=(objeto,), intent_consulta=intent, parametro_detalhe='alvo',
        leitor=lambda _: {'detalhe': {'nome': 'pessoal', 'titulos': ['Dado real']}})
    correto = mapa.avaliar_consulta_antecipada(f'quantas {objeto}s tem na {termo} pessoal?')
    assert correto['intent'] == intent and correto['params']['alvo'] == 'pessoal'
    for texto in (f'qual é a definição de {termo}?',
                  f'quantas pessoas tem na {termo} pessoal?',
                  f'quais {objeto}s especiais tem na {termo} pessoal?'):
        assert mapa.resolver_consulta(texto) is None
        decisao = mapa.avaliar_consulta_antecipada(texto)
        assert decisao['destino'] == 'ia' and 'intent' not in decisao


@pytest.mark.parametrize('texto', ['cria a playlist rock', 'apaga a playlist rock',
    'não mostra a playlist rock', 'estou usando minha playlist rock'])
def test_ausencia_de_consulta_nao_usurpa_roteamento_de_outros_atos(mapa, texto):
    assert mapa.avaliar_consulta_antecipada(texto) is None


@pytest.mark.parametrize('texto', ['você gosta de rock?', 'você curte programação?', 'gosta de jazz?'])
def test_interpretacao_da_ia_nao_cria_autorizacao_para_ler_ou_alterar(texto):
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.decisao_turno import filtrar_comandos_pelo_turno
    turno = classificar_modalidade_turno(texto)
    assert turno['autoriza_execucao'] is False
    propostas = [{'intent': i, 'params': {}} for i in (
        'PLAYLIST_LIST', 'INBOX_LIST', 'LISTAR_AGENDAMENTOS', 'PLAYLIST_PLAY', 'APP_OPEN', 'IOT_CONTROL')]
    resultado = filtrar_comandos_pelo_turno(propostas, turno=turno,
        plano={'id': turno['id'], 'requer_execucao': False, 'comandos': []})
    assert resultado['comandos'] == []
    assert len(resultado['rejeitados']) == len(propostas)


@pytest.mark.parametrize('texto', ['quais instrumentos tem na sua primeira playlist?',
    'você gosta da sua primeira playlist?', 'você curte sua segunda playlist?'])
def test_referencia_qualificada_nao_ultrapassa_finalidade_compartilhada(mapa, texto):
    from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
    assert detectar_intencao_deterministica_mente(texto, {
        'resolver_consulta_recurso_local': mapa.avaliar_consulta_antecipada}) is None


@pytest.mark.parametrize('texto,alvo', [('o que tem na sua primeira playlist?', '#1'),
    ('quais músicas tem na sua primeira playlist?', '#1'), ('mostra sua segunda playlist', '#2'),
    ('o que tem na sua 1ª playlist?', '#1'), ('quais músicas tem na sua 2ª playlist?', '#2'),
    ('mostra sua 3ª playlist', '#3')])
def test_referencia_qualificada_legitima_preserva_owner_e_ordem(mapa, texto, alvo):
    from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
    mapa.registrar('curadoria', arquivo='teste', descricao='curadoria própria',
        termos=('sua playlist', 'suas playlists'), objetos_consulta=('musica', 'faixa'),
        intent_consulta='LAYLAY_PLAYLIST_LIST', leitor=lambda _: {'playlists': []})
    decisao = mapa.avaliar_consulta_antecipada(texto)
    assert decisao is not None, 'referência qualificada perdeu a finalidade de leitura'
    assert decisao['destino'] == 'roteador' and 'intent' not in decisao
    resultado = detectar_intencao_deterministica_mente(texto, {
        'resolver_consulta_recurso_local': mapa.avaliar_consulta_antecipada})
    assert resultado['intent'] == 'LAYLAY_PLAYLIST_LIST'
    assert resultado['params']['nome_playlist'] == alvo


@pytest.mark.parametrize('texto', ['quais instrumentos tem na sua primeira playlist?',
    'você gosta da sua primeira playlist?', 'quantas músicas de jazz tem na sua primeira playlist?'])
def test_protecao_da_curadoria_nao_depende_do_registro_generico_irmao(texto):
    from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
    mapa = MapaRecursosRuntime()
    mapa.registrar('curadoria', arquivo='teste', descricao='único recurso registrado',
        termos=('sua playlist', 'suas playlists'), objetos_consulta=('musica', 'faixa'),
        intent_consulta='LAYLAY_PLAYLIST_LIST', leitor=lambda _: {'playlists': []})
    decisao = mapa.avaliar_consulta_antecipada(texto)
    assert decisao is not None, 'recusa de finalidade dependeu de outro recurso registrado'
    assert decisao['destino'] == 'ia'
    assert detectar_intencao_deterministica_mente(texto, {
        'resolver_consulta_recurso_local': mapa.avaliar_consulta_antecipada}) is None


@pytest.mark.parametrize('termo', ['segunda via', 'playlist 3 porquinhos'])
def test_alias_literal_registrado_e_preservado_antes_da_projecao_de_posicao(termo):
    assert MapaRecursosRuntime._termo_mencionado('mostra ' + termo, termo)


@pytest.mark.parametrize('texto', ['você gosta de rock?', 'você curte programação?',
    'gosta de jazz?', 'você prefere Python ou Rust?', 'qual é seu estilo favorito?'])
def test_finalidade_subjetiva_e_compartilhada_com_contrato_autoral(texto):
    assert texto_pede_opiniao(texto) is True


@pytest.mark.parametrize('texto', ['eu gosto de rock', 'ela gosta de rock?',
    'toca Gosta de Mim', 'mostra a playlist "você gosta de rock"',
    'qual é meu gênero favorito?', 'gostaria de ver minhas playlists'])
def test_relato_terceiros_argumento_e_pedido_nao_viram_opiniao_da_assistente(texto):
    assert texto_pede_opiniao(texto) is False


@pytest.fixture(scope='module')
def composicao_instalada(tmp_path_factory):
    """Root real em subprocesso; só modelo/voz/rede e persistência isolados."""
    tmp_path = tmp_path_factory.mktemp('finalidade_instalada')
    codigo = textwrap.dedent('''
        import json, sys
        from pathlib import Path
        from mente_laylay.memoria_mental.playlist_runtime import PlaylistRuntime
        pasta = Path(sys.argv[1])
        original_init = PlaylistRuntime.__init__
        def init(self, **kwargs):
            kwargs.update(state_file=str(pasta / 'playlists.json'),
                          legacy_file=str(pasta / 'legado.json'))
            original_init(self, **kwargs)
        PlaylistRuntime.__init__ = init
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(pasta)
        assert Path(root._playlist_runtime.state_file).resolve().is_relative_to(pasta.resolve())
        assert root._playlist_runtime.save({'rock': [
            {'title': 'Faixa A', 'url': 'https://www.youtube.com/watch?v=teste000001'},
            {'title': 'Faixa B', 'url': 'https://www.youtube.com/watch?v=teste000002'}]})
        root._musica_estado_set('ultima_playlist', 'rock')
        root._voz_runtime.falar = lambda *a, **k: False
        from mente_laylay.autonomia import coordenador_intencao
        original_executor = coordenador_intencao.executar_intencao
        executados = []
        def executar(resultado, texto, contexto):
            executados.append(resultado)
            assert resultado['intent'] == 'PLAYLIST_LIST', 'efeito externo proibido neste teste'
            return original_executor(resultado, texto, contexto)
        coordenador_intencao.executar_intencao = executar
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        chamadas = []
        def modelo(self, pedido):
            chamadas.append(pedido.tipo_chamada)
            return ResultadoModelo(json.dumps({'comandos': [], 'suporte_proposicoes': [
                {'texto': 'Prefiro rock pelas guitarras.', 'fontes': []}]}), True)
        RegistroModeloLLM.executar = modelo
        publicadas = []
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda fala, *a, **k: publicadas.append(str(fala)) or True)
        prioridades = []
        original_contexto = root._resposta_ia_runtime._contexto_getter
        def contexto():
            ctx = original_contexto()
            prioridade = ctx['processar_comandos_prioritarios']
            def capturar(texto):
                r = prioridade(texto)
                prioridades.append(r)
                return r
            ctx['processar_comandos_prioritarios'] = capturar
            return ctx
        root._resposta_ia_runtime._contexto_getter = contexto
        resultados = []
        textos = ['você gosta de rock?', 'você curte rock?', 'gosta de rock?',
                  'qual é a definição de playlist?',
                  'qual é a diferença entre a playlist rock e um álbum?',
                  'quais instrumentos são comuns nas playlists de rock?',
                  'quantas músicas tem na playlist rock?', 'quais músicas tem em rock?',
                  'mostra a playlist rock', 'lista a playlist rock']
        for texto in textos:
            ini = (len(chamadas), len(executados), len(publicadas), len(prioridades))
            root._resposta_ia_runtime.processar(texto, origem='teste_finalidade_recurso')
            resultados.append({'texto': texto, 'consulta': root._resolver_consulta_recurso_local(texto),
                'deterministica': root.detectar_intencao_deterministica(texto),
                'prioridades': prioridades[ini[3]:],
                'modelos': chamadas[ini[0]:],
                'executados': executados[ini[1]:], 'publicadas': publicadas[ini[2]:]})
        (pasta / 'composicao.json').write_text(json.dumps(resultados, ensure_ascii=False), encoding='utf8')
    ''')
    resultado = subprocess.run([sys.executable, '-c', codigo, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, timeout=120)
    (tmp_path / 'runtime.log').write_bytes(resultado.stdout + resultado.stderr)
    assert resultado.returncode == 0, (resultado.stdout + resultado.stderr).decode('utf8', errors='replace')[-6000:]
    return json.loads((tmp_path / 'composicao.json').read_text(encoding='utf8'))


def test_composicao_instalada_entrega_conversa_ao_modelo(composicao_instalada):
    for turno in composicao_instalada[:6]:
        assert not (turno['consulta'] or {}).get('intent') and turno['deterministica'] is None, turno
        assert turno['executados'] == [], turno
        assert turno['modelos'], turno


def test_composicao_instalada_preserva_consulta_explicita(composicao_instalada):
    for turno in composicao_instalada[8:]:
        assert [r['intent'] for r in turno['executados']] == ['PLAYLIST_LIST'], turno
        assert turno['executados'][0]['params']['nome_playlist'] == 'rock', turno
        assert turno['publicadas'] and '2' in ' '.join(turno['publicadas']), turno


# Xfail histórico reproduzido em comunicacao_consulta_natural_20261023/red.xml;
# consulta e barreira de mutação agora têm admissão independente comprovada.
def test_consulta_natural_detectada_deve_alcancar_executor_na_instalacao(composicao_instalada):
    for turno in composicao_instalada[6:8]:
        assert turno['consulta']['intent'] == 'PLAYLIST_LIST', turno
        assert turno['deterministica']['intent'] == 'PLAYLIST_LIST', turno
        assert [r['intent'] for r in turno['executados']] == ['PLAYLIST_LIST'], turno
        assert not turno['modelos'], 'a leitura real não depende de proposta gerada'
        assert turno['publicadas'] and '2' in ' '.join(turno['publicadas']), turno
