"""Tipo externo não integra o alvo; palavras internas e literais permanecem."""
import pytest

from mente_laylay.autonomia.roteador_deterministico import (
    detectar_musica_ou_playlist_direta, detectar_volume_ou_midia,
)
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.memoria_mental.busca_youtube import normalizar_query_musical


def detectar(texto, *, playlist="", resolver=None):
    return detectar_musica_ou_playlist_direta(
        normalizar_texto(texto), texto_sem_destino=normalizar_texto(texto),
        texto_bruto=texto, params_cb=lambda **p: p,
        detectar_playlist_nome_direto=lambda _texto: playlist,
        normalizar_query_musical=normalizar_query_musical,
        resolver_referencia_pessoal=resolver,
    )


@pytest.mark.parametrize("verbo", ["coloca", "toca", "escuta"])
@pytest.mark.parametrize("tipo", ["a música", "uma faixa", "um som", "a canção"])
@pytest.mark.parametrize("titulo", ["máximo respeito", "antes do amanhecer", "a música de ontem"])
def test_moldura_tipificada_e_removida_uma_vez_sem_remover_palavras_do_titulo(verbo, tipo, titulo):
    assert detectar(f"{verbo} {tipo} {titulo}") == {
        "intent": "MUSIC_SEARCH", "params": {"query": normalizar_texto(titulo)}}


@pytest.mark.parametrize("texto,titulo", [
    ('coloca a música "Música de Ontem"', "Música de Ontem"),
    ('toca "Música Brasileira"', "Música Brasileira"),
    ('escuta uma faixa “O Som do Silêncio”', "O Som do Silêncio"),
    ('coloca a canção "Volume Máximo"', "Volume Máximo"),
    ('coloca a música "Minha Música Favorita"', "Minha Música Favorita"),
    ('vamos ouvir uma música "Canção do Amanhecer"', "Canção do Amanhecer"),
])
def test_literal_preserva_nome_e_nao_vira_referencia_pessoal(texto, titulo):
    chamadas = []
    def resolver(*args, **kwargs):
        chamadas.append((args, kwargs))
        return None
    assert detectar(texto, resolver=resolver) == {
        "intent": "MUSIC_SEARCH", "params": {"query": titulo}}
    assert chamadas == []


@pytest.mark.parametrize("titulo", [
    "vida com musica", "som do silencio", "antes do amanhecer",
    "musica para estudar", "som de chuva",
])
def test_nome_sem_tipo_nao_perde_palavras_internas(titulo):
    assert detectar("toca " + titulo) == {"intent": "MUSIC_SEARCH", "params": {"query": titulo}}


def test_playlist_conhecida_mantem_precedencia():
    assert detectar("coloca música brasileira", playlist="música brasileira") == {
        "intent": "PLAYLIST_PLAY", "params": {"nome_playlist": "música brasileira"}}


def test_referencia_pessoal_nao_literal_ainda_exige_memoria_confirmada():
    assert detectar("coloca minha música favorita") is None
    r = detectar("coloca minha música favorita", resolver=lambda *a, **k: {
        "valor": "Lua de Neon da Anny", "confirmado_usuario": True})
    assert r["params"]["query"] == "Lua de Neon da Anny"
    assert r["params"]["referencia_pessoal"] == "minha musica favorita"


@pytest.mark.parametrize("texto", [
    'não toca a música "Volume Máximo"',
    'como eu faria para tocar a música "Volume Máximo"?',
    "coloca o volume no máximo", "coloca o som no mínimo",
])
def test_outro_ato_ou_parametro_explicito_nao_produz_consulta_musical(texto):
    assert detectar(texto) is None


@pytest.mark.parametrize("operando,tipos,esperado", [
    ('a música "Música de Ontem"', ("música",), ("Música de Ontem", "música", True)),
    ('o arquivo "Arquivo de Hoje.txt"', ("arquivo",), ("Arquivo de Hoje.txt", "arquivo", True)),
    ('o app "App de Novo"', ("app",), ("App de Novo", "app", True)),
    ("a faixa a musica de ontem", ("faixa",), ("a musica de ontem", "faixa", False)),
    ("música para estudar", ("música",), ("música para estudar", "", False)),
    ("som do silencio", ("som",), ("som do silencio", "", False)),
    ('"som do silencio"', ("som",), ("som do silencio", "", True)),
    ("uma faixa", ("faixa",), ("", "faixa", False)),
])
def test_leitura_compartilhada_de_tipo_nome_e_relacao_sem_resolver_entidade(operando, tipos, esperado):
    from mente_laylay.cognicao.referencias_linguagem import separar_tipo_e_alvo_nomeado
    assert separar_tipo_e_alvo_nomeado(operando, tipos) == esperado


@pytest.mark.parametrize("texto", [
    'escuta uma faixa "O Som do Silêncio"', "coloca a música Mudo",
    "toca a faixa Mais Alto", "coloca a canção Desmuta",
    "coloca a faixa Pausa", "toca a música Despausa",
])
def test_controle_midia_nao_le_palavra_interna_de_operando_nomeado(texto):
    assert detectar_volume_ou_midia(normalizar_texto(texto), params_cb=lambda **p: p,
        contexto_musical_ativo=True, contexto_volume_ativo=True) is None
