from types import SimpleNamespace
import pytest

from mente_laylay.autonomia.roteador_deterministico import extrair_intencao_abrir_app, detectar_abrir_app_ou_site
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.autonomia.executor_navegador import executar_intencao_navegador
from tests.test_executor_navegador import _dependencias


def extrair(texto):
    return extrair_intencao_abrir_app(texto, normalizar_texto=normalizar_texto,
        limpar_destino=lambda x: x, apps_map={"opera": "opera"}, sites_diretos={"google": "https://google.com"})


@pytest.mark.parametrize("texto,tema", [
    ("pode abrir um site sobre módulo de conversão dc-dc", "modulo de conversao dc dc"),
    ("abra um site sobre jardinagem", "jardinagem"),
])
def test_abertura_por_assunto_preserva_proposito_no_adaptador(texto, tema):
    resultado = detectar_abrir_app_ou_site(texto, params_cb=lambda **k: k, extrair_intencao_abrir_app=extrair)
    assert resultado == {"intent": "SITE_ENTER", "params": {"tema": tema}}


@pytest.mark.parametrize("busca_ok,resultado_ok", [(True, True), (False, True), (True, False)])
def test_site_por_assunto_precisa_confirmar_busca_antes_de_abrir_resultado(busca_ok, resultado_ok):
    eventos = []
    chamadas = []
    def abrir(url, **kwargs):
        chamadas.append(("busca", url, kwargs))
        return busca_ok
    def resultado(query):
        chamadas.append(("resultado", query))
        return resultado_ok
    executar_intencao_navegador("SITE_ENTER", {"tema": "jardinagem"},
        "abra um site sobre jardinagem", "pc_a",
        {"_registro_navegador_operacoes_runtime": SimpleNamespace(abrir_primeiro_resultado=resultado)},
        _dependencias(eventos, abrir=abrir))
    assert chamadas[0][0] == "busca"
    assert chamadas[0][2]["auto_click"] is False
    assert (len(chamadas) == 2) is busca_ok
    receipt = next(e for e in eventos if e[0] == "resultado")
    assert receipt[2]["confirmado"] is (busca_ok and resultado_ok)
    assert receipt[1] == ("resultado_web_aberto" if busca_ok and resultado_ok else "falha_execucao")


def test_site_nomeado_e_app_preservados():
    assert extrair("abra o site google")["intent"] == "OPEN_URL"
    assert extrair("abra o opera")["intent"] == "APP_OPEN"


def test_busca_remota_nao_pode_clicar_resultado_local():
    eventos, chamadas = [], []
    executar_intencao_navegador("SITE_ENTER", {"tema": "jardinagem"},
        "abra um site sobre jardinagem no outro computador", "pc_b",
        {"_registro_navegador_operacoes_runtime": SimpleNamespace(abrir_primeiro_resultado=lambda q: chamadas.append(q))},
        _dependencias(eventos, abrir=lambda *a, **k: chamadas.append(a)))
    assert not chamadas
    assert eventos[0][2]["confirmado"] is False


def test_excecao_do_navegador_tem_conclusao_sem_sucesso_falso():
    eventos = []
    def falhar(query):
        raise RuntimeError("ponte indisponível")
    executar_intencao_navegador("SITE_ENTER", {"tema": "jardinagem"},
        "abra um site sobre jardinagem", "pc_a",
        {"_registro_navegador_operacoes_runtime": SimpleNamespace(abrir_primeiro_resultado=falhar)},
        _dependencias(eventos))
    assert eventos[0][1] == "falha_execucao"
    assert eventos[0][2]["confirmado"] is False
    assert eventos[1][0] == "fala_status"
