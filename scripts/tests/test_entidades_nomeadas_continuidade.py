"""Coleção de referentes, unicidade e ambiguidade antes da ação proposta."""
import pytest
from mente_laylay.cognicao.retrato_turno import construir_retrato_turno
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.especialistas.operacional import construir_parecer_operacional
from mente_laylay.memoria_mental.registro_semantico import atualizar_registro_turno


def seguir(texto, *, agora=101):
    retrato, recentes = construir_retrato_turno(texto, turno=classificar_modalidade_turno(texto),
        mente={}, contexto_perceptivo={}, agora=100)
    registro = atualizar_registro_turno({}, texto, retrato=retrato, agora=100)
    pedido = 'pode colocar ele para mim ouvir'
    turno = classificar_modalidade_turno(pedido)
    posterior, _ = construir_retrato_turno(pedido, turno=turno,
        mente={'entidades_recentes': recentes, 'registro_semantico': registro},
        contexto_perceptivo={}, agora=agora)
    return retrato, registro, posterior, construir_parecer_operacional(pedido, turno=turno, retrato=posterior)


@pytest.mark.parametrize('nome', ['Nevermind', 'Clube da Esquina', 'Água e Sol'])
def test_album_unico_mencionado_conserva_identidade_sem_inventar_receipt(nome):
    retrato, registro, posterior, parecer = seguir('nunca escutei o álbum ' + nome)
    assert retrato['entidade_explicita']['nome'] == nome
    assert posterior['referencia_resolvida']['nome'] == nome
    assert posterior['referencia_resolvida']['tipo'] == 'album'
    assert not parecer['requer_esclarecimento']
    assert not registro.get('resultados_execucao')


@pytest.mark.parametrize('texto,nomes', [
    ('o álbum Nevermind ou o álbum In Utero', {'Nevermind', 'In Utero'}),
    ('o álbum Nevermind. O álbum In Utero.', {'Nevermind', 'In Utero'}),
    ('o livro Dom Casmurro ou o livro Quincas Borba', {'Dom Casmurro', 'Quincas Borba'}),
    ('o filme Interestelar. O filme Duna.', {'Interestelar', 'Duna'}),
])
def test_mencoes_concorrentes_nao_se_tornam_um_alvo_unico(texto, nomes):
    retrato, registro, posterior, parecer = seguir(texto)
    assert {e['nome'] for e in retrato['entidades_explicitas']} == nomes
    assert not retrato['entidade_explicita']
    assert not registro['entidade_ativa_id']
    assert not posterior['referencia_resolvida']
    assert parecer['requer_esclarecimento'] and not parecer['autoriza_execucao']


def test_repeticao_do_mesmo_nome_nao_cria_ambiguidade():
    _, _, posterior, parecer = seguir('o álbum Nevermind. O álbum Nevermind.')
    assert posterior['referencia_resolvida']['nome'] == 'Nevermind'
    assert not parecer['requer_esclarecimento']


def test_pronome_sem_fonte_nao_ganha_confianca_de_alvo():
    _, _, posterior, parecer = seguir('não mencionei nenhum alvo')
    assert not posterior['referencia_resolvida']
    assert parecer['requer_esclarecimento'] and not parecer['autoriza_execucao']


def test_album_expirado_exige_esclarecimento():
    _, _, posterior, parecer = seguir('nunca escutei o álbum Nevermind', agora=701)
    assert not posterior['referencia_resolvida']
    assert parecer['requer_esclarecimento']


@pytest.mark.parametrize('texto,tipo,nome', [
    ('conheço a banda Banda do Mar', 'artista', 'Banda do Mar'),
    ('gosto do jogo O Filme dos Sonhos', 'jogo', 'O Filme dos Sonhos'),
    ('li o livro O Cantor e o Livro', 'livro', 'O Cantor e o Livro'),
])
def test_rotulo_dentro_do_nome_nao_abre_outra_mencao(texto,tipo,nome):
    retrato, _, _, _ = seguir(texto)
    assert retrato['entidade_explicita'] == {'tipo': tipo, 'nome': nome, 'origem': 'nome_explicito'}


@pytest.mark.parametrize('texto', ['o cantor Cartola e o álbum Cartola',
    'o filme Duna e o jogo Duna'])
def test_mesmo_nome_em_tipos_distintos_nao_e_identidade_unica(texto):
    retrato, registro, posterior, parecer = seguir(texto)
    assert len(retrato['entidades_explicitas']) == 2
    assert len(registro['entidades']) == 2
    assert not posterior['referencia_resolvida']
    assert parecer['requer_esclarecimento']
    from mente_laylay.memoria_mental.registro_semantico import resolver_referencia_pontuada
    resolucao = resolver_referencia_pontuada('pode colocar ele para mim ouvir',
        registro=registro, entidades_recentes={}, agora=101)
    assert not resolucao['resolvida'], 'projeção do registro também conserva concorrência da mesma menção'


def test_composicao_instalada_nao_aceita_proposta_de_escolha_entre_dois_alvos(tmp_path):
    import subprocess, sys, os, textwrap
    from pathlib import Path
    codigo = textwrap.dedent(r'''
        import sys, json
        from pathlib import Path
        from scripts.analises.sonda_escopo_propostas_mistas import preparar_instalacao_isolada
        root = preparar_instalacao_isolada(Path(sys.argv[1]))
        from mente_laylay.autonomia import coordenador_intencao
        from mente_laylay.integracao.registro_conversa_llm import RegistroModeloLLM, ResultadoModelo
        executores, publicadas = [], []
        root._voz_runtime.falar = lambda *a, **k: False
        root._orquestrador_fala_runtime.registrar_observador_texto_final(
            lambda fala, *a, **k: publicadas.append(str(fala)) or True)
        coordenador_intencao.executar_intencao = lambda *a, **k: executores.append(a) or False
        root._iniciar_planejamento_turno('estou em dúvida entre o álbum Nevermind ou o álbum In Utero')
        root._interpretacao_intencao_runtime.analisar = lambda *a, **k: {
            'intent': 'MUSIC_SEARCH', 'params': {'query': 'Nevermind'}}
        RegistroModeloLLM.executar = lambda *a, **k: ResultadoModelo(json.dumps({
            'comandos': [{'intent': 'MUSIC_SEARCH', 'params': {'query': 'Nevermind'}}],
            'suporte_proposicoes': [{'texto': 'Qual dos dois álbuns você quer ouvir?', 'fontes': []}]}), True)
        root._resposta_ia_runtime.processar('pode colocar ele para mim ouvir', origem='teste_ambiguidade')
        mental = root._estado_compartilhado_runtime.mental
        assert not mental['turno_atual']['referencia_resolvida']
        assert executores == [], 'proposta não pode escolher um dos alvos concorrentes'
        assert publicadas, 'pedido não deve desaparecer sem conclusão'
    ''')
    p = subprocess.run([sys.executable, '-c', codigo, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True,
        encoding='utf8', env=dict(os.environ, PYTHONIOENCODING='utf-8', LAYLAY_NEURAL_MODE='off'), timeout=60)
    assert p.returncode == 0, p.stdout[-3500:] + p.stderr[-2500:]


@pytest.mark.parametrize('texto,tipo,nome', [
    ('li o livro "O Cantor e o Livro dos Sonhos"', 'livro', 'O Cantor e o Livro dos Sonhos'),
    ('conheço o álbum “A Música e o Filme da Vida”', 'album', 'A Música e o Filme da Vida'),
    ('li o livro «O Cantor, o Livro. E o Filme»', 'livro', 'O Cantor, o Livro. E o Filme'),
])
def test_titulo_delimitado_e_um_objeto_atomico(texto, tipo, nome):
    retrato, _, _, _ = seguir(texto)
    assert retrato['entidades_explicitas'] == [{'tipo': tipo, 'nome': nome, 'origem': 'nome_explicito'}]


def test_titulos_delimitados_distintos_continuam_concorrentes():
    retrato, _, posterior, parecer = seguir('o livro "O Cantor e o Livro dos Sonhos" ou o livro "Duna"')
    assert {e['nome'] for e in retrato['entidades_explicitas']} == {'O Cantor e o Livro dos Sonhos', 'Duna'}
    assert not posterior['referencia_resolvida'] and parecer['requer_esclarecimento']


@pytest.mark.parametrize('somente_registro', [False, True])
@pytest.mark.parametrize('escolha', ['Nevermind', 'In Utero'])
def test_escolha_explicita_renova_identidade_e_encerra_grupo_anterior(somente_registro, escolha):
    estado = {}
    for indice, texto in enumerate(['o álbum Nevermind ou o álbum In Utero',
        'eu quis dizer o álbum ' + escolha]):
        retrato, recentes = construir_retrato_turno(texto, turno=classificar_modalidade_turno(texto),
            mente=estado, contexto_perceptivo={}, agora=100 + indice)
        estado = {'entidades_recentes': recentes,
            'registro_semantico': atualizar_registro_turno(estado.get('registro_semantico'), texto,
                retrato=retrato, agora=100 + indice)}
    if somente_registro:
        estado['entidades_recentes'] = {}
    pedido = 'pode colocar ele para mim ouvir'
    turno = classificar_modalidade_turno(pedido)
    posterior, _ = construir_retrato_turno(pedido, turno=turno, mente=estado,
        contexto_perceptivo={}, agora=102)
    assert posterior['referencia_resolvida']['nome'] == escolha
    assert not construir_parecer_operacional(pedido, turno=turno, retrato=posterior)['requer_esclarecimento']
