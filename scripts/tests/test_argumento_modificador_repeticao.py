"""Modificador de operação não integra nem destrói um argumento literal."""
import pytest

from mente_laylay.autonomia.detectores_playlist import detectar_playlist_usuario
from mente_laylay.autonomia.roteador_deterministico import extrair_intencao_abrir_app
from mente_laylay.memoria_mental.playlist_mental import limpar_nome_playlist, extrair_nome_playlist


@pytest.mark.parametrize("sufixo", ["de novo", "novamente", "outra vez", "mais uma vez"])
@pytest.mark.parametrize("nome", ["jazz", "jazz instrumental", "caminho de volta"])
def test_play_de_playlist_separa_modificador_de_operacao(nome, sufixo):
    texto = f"coloca a playlist {nome} {sufixo}"
    r = detectar_playlist_usuario(texto, texto, params_cb=lambda **p: p,
        limpar_nome_playlist=limpar_nome_playlist, extrair_nome_playlist=extrair_nome_playlist)
    assert r == {"intent": "PLAYLIST_PLAY", "params": {"nome_playlist": nome}}


@pytest.mark.parametrize("aspas", [('"', '"'), ('“', '”'), ("'", "'")])
@pytest.mark.parametrize("sufixo", ["", " de novo", " novamente"])
def test_nome_literal_de_playlist_preserva_palavras_de_repeticao(aspas, sufixo):
    texto = f"coloca a playlist {aspas[0]}jazz de novo{aspas[1]}{sufixo}"
    r = detectar_playlist_usuario(texto, texto, params_cb=lambda **p: p,
        limpar_nome_playlist=limpar_nome_playlist, extrair_nome_playlist=extrair_nome_playlist)
    assert r == {"intent": "PLAYLIST_PLAY", "params": {"nome_playlist": "jazz de novo"}}


@pytest.mark.parametrize("nome", ["jazz de novo", "jazz pesado", "rock alternativo", "novamente"])
def test_armazenamento_e_criacao_nao_removem_palavras_do_nome(nome):
    assert limpar_nome_playlist(nome) == nome
    texto = f"cria uma playlist chamada {nome}"
    r = detectar_playlist_usuario(texto, texto, params_cb=lambda **p: p,
        limpar_nome_playlist=limpar_nome_playlist, extrair_nome_playlist=extrair_nome_playlist)
    assert r == {"intent": "PLAYLIST_CREATE", "params": {"nome_playlist": nome}}


@pytest.mark.parametrize("texto,intent,params", [
    ("abre o bloco de notas mais uma vez", "APP_OPEN", {"nome_app": "bloco de notas"}),
    ('abre "ensaio de novo"', "APP_OPEN", {"nome_app": "ensaio de novo"}),
    ('abre o site "ensaio de novo" de novo', "OPEN_URL", {"alvo": "ensaio de novo"}),
])
def test_mesmo_limite_lexical_em_aplicativo_e_site(texto, intent, params):
    r = extrair_intencao_abrir_app(texto, normalizar_texto=lambda s: s.casefold(),
        limpar_destino=lambda s: s, apps_map={}, sites_diretos={})
    assert r == {"intent": intent, "params": params}


def test_sufixo_descritivo_nao_e_repeticao():
    texto = "coloca a playlist jazz instrumental"
    r = detectar_playlist_usuario(texto, texto, params_cb=lambda **p: p,
        limpar_nome_playlist=limpar_nome_playlist, extrair_nome_playlist=extrair_nome_playlist)
    assert r["params"]["nome_playlist"] == "jazz instrumental"


@pytest.mark.parametrize("valor,alvo,repeticao", [
    ('"jazz de novo"', "jazz de novo", False),
    ('"jazz de novo" de novo', "jazz de novo", True),
    ('"jazz de novo', '"jazz de novo', False),
    ("novamente", "novamente", False),
    ("jazz instrumental", "jazz instrumental", False),
    ("jazz outra vez!", "jazz", True),
])
def test_limite_lexical_preserva_literal_e_recusa_delimitador_aberto(valor, alvo, repeticao):
    from mente_laylay.cognicao.referencias_linguagem import separar_alvo_e_repeticao
    assert separar_alvo_e_repeticao(valor) == (alvo, repeticao)


@pytest.mark.parametrize("url", ["https://example.test", "https://example.test/A?Q=A%20B#C",
    "http://example.test:8080/Rota/Arquivo.md?x=1&y=2"])
@pytest.mark.parametrize("moldura", ["abre o site {}", "abre {}", 'abre o site "{}"'])
def test_uri_literal_nao_passa_por_normalizacao_lexical_de_nome(url, moldura):
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
    candidato = extrair_intencao_abrir_app(moldura.format(url), normalizar_texto=normalizar_texto,
        limpar_destino=lambda s: s, apps_map={}, sites_diretos={})
    assert candidato == {"intent": "OPEN_URL", "params": {"alvo": url}}


@pytest.mark.parametrize("url", ["http://[", "https://", "http:///sem_host"])
def test_uri_explicita_invalida_nao_vira_nome_normalizado_ou_excecao(url):
    from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
    assert extrair_intencao_abrir_app("abre o site " + url, normalizar_texto=normalizar_texto,
        limpar_destino=lambda s: s, apps_map={}, sites_diretos={}) is None
