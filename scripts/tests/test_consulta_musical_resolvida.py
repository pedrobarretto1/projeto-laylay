"""Argumento estruturado não volta a ser fala; busca não é efeito confirmado."""
import pytest

from mente_laylay.autonomia.executor_musical import (
    DependenciasExecutorMusical, executar_intencao_musical,
)
from mente_laylay.cognicao.refinamento_pesquisa import refinar_consulta_musical
from mente_laylay.memoria_mental.busca_youtube import normalizar_query_musical


def pesquisar(params, texto, *, permitir=True, normalizar=normalizar_query_musical):
    consultas, normalizacoes, resultados, falas, aberturas = [], [], [], [], []
    def preparar(texto):
        normalizacoes.append(texto)
        return normalizar(texto)
    def buscar(query, **kw):
        consultas.append(query)
        return {}  # Nenhum vídeo verificado: não simular sucesso/efeito.
    retorno = executar_intencao_musical("MUSIC_SEARCH", params, texto, {
        "_autonomia_permite_execucao_musical": lambda *a, **k: permitir,
        "_normalizar_query_musical": preparar,
        "_resolver_query_musical_por_estilo": refinar_consulta_musical,
        "_resolver_primeiro_video_youtube": buscar,
    }, DependenciasExecutorMusical(
        marcar_resultado=lambda status, **k: resultados.append((status, k)),
        abrir_url_musical=lambda *a, **k: aberturas.append((a, k)),
        falar_por_status=lambda status, fala, **k: falas.append((status, fala)),
    ))
    return retorno, consultas, normalizacoes, resultados, falas, aberturas


@pytest.mark.parametrize("campo", ["query", "musica", "nome"])
@pytest.mark.parametrize("nome", [
    "Música de Ontem", "A Música de Ontem", "O Som do Silêncio",
    "Song of the Wind", "Antes do Amanhecer", "Faixa de Luz",
])
def test_argumento_recebido_mantem_identidade_ate_busca_sem_interpretar_comando(campo, nome):
    params = {campo: nome}
    retorno, consultas, normalizacoes, resultados, falas, aberturas = pesquisar(
        params, f'toca a música "{nome}"')
    assert consultas == [nome]  # Primeira fronteira, antes de estado/fala.
    assert normalizacoes == []
    assert params["consulta_pedida"] == params["consulta_resolvida"] == nome
    assert retorno.tratado and not retorno.retorno
    assert resultados[0][0] == "musica_nao_resolvida"
    assert resultados[0][1]["executou"] is False
    assert resultados[0][1]["confirmado"] is False
    assert falas and not aberturas


def test_consulta_nao_resolvida_na_fala_ainda_usa_porta_legada():
    r = pesquisar({}, "toca a musica Duality")
    assert r[1] == ["duality"]
    assert r[2] == ["toca a musica Duality"]


def test_fala_sem_alvo_materializado_pede_esclarecimento_e_nao_busca():
    r = pesquisar({}, "coloca uma música")
    assert not r[0].retorno and not r[1] and not r[5]
    assert r[3][0][0] == "alvo_ausente"


def test_preservacao_do_argumento_nao_concede_autorizacao():
    r = pesquisar({"query": "Música de Ontem"}, "gosto de Música de Ontem", permitir=False)
    assert not r[0].retorno
    assert not r[1] and not r[2] and not r[5]


def test_refinamento_de_descricao_musical_continua_dono_da_curadoria():
    r = pesquisar({"query": "musica para jogar minecraft"}, "coloca música para jogar minecraft")
    assert r[1] == ["C418 - Sweden Minecraft Volume Alpha"]
    assert r[2] == []


def test_parametro_explicitamente_vazio_nao_reusa_outro_pedido():
    r = pesquisar({"query": ""}, "coloca uma música")
    assert not r[1] and not r[5]
    assert r[3][0][0] == "alvo_ausente"


@pytest.mark.parametrize("campo", ["query", "musica", "nome"])
@pytest.mark.parametrize("valor", ["uma música", "uma faixa", "um som", "a canção", None, ""])
def test_tipo_sem_complemento_nao_e_um_argumento_resolvido(campo, valor):
    r = pesquisar({campo: valor}, "coloca uma música")
    assert not r[1] and not r[5]
    assert r[3][0][0] == "alvo_ausente"


def test_vazio_explicito_nao_toma_alias_com_outro_alvo():
    r = pesquisar({"query": "", "musica": "Duality"}, "toca Duality")
    assert not r[1] and not r[5]
    assert r[3][0][0] == "alvo_ausente"
