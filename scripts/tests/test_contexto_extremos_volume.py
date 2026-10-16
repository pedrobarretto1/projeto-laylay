"""Contexto qualificado completa ajuste, não transforma palavras em ação."""
import time

import pytest

from mente_laylay.autonomia.orquestrador_deterministico import detectar_intencao_deterministica_mente
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia
from mente_laylay.cognicao.normalizacao_linguagem import normalizar_texto
from mente_laylay.memoria_mental.contexto_compartilhado import estado_mental_inicial, registrar_resultado_execucao
from mente_laylay.memoria_mental.resultado_acao import ResultadoAcao


def estado_volume():
    return registrar_resultado_execucao(estado_mental_inicial(), ResultadoAcao(
        id_solicitacao="extremo-volume", intent="VOLUME", status="volume_ajustado",
        executou=True, confirmado=True, origem="executor", params={"acao": "set", "nivel_volume": 35}),
        "coloca o volume em 35")


@pytest.mark.parametrize("texto", [
    "coloca a musica maximo respeito", "coloca a musica minimo detalhe",
    "abre o arquivo maximo.txt", "me explica o maximo divisor comum",
    "nao coloca no maximo", "como eu faria para deixar no minimo?",
])
def test_palavra_extrema_em_outro_ato_ou_alvo_nao_materializa_volume(texto):
    r = detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado_volume()})
    assert not r or r["intent"] != "VOLUME", r


@pytest.mark.parametrize("texto,nivel", [
    ("coloca no maximo", 100), ("deixa no talo", 100),
    ("abaixa ao minimo", 0), ("coloca o volume no maximo", 100),
    ("deixa o som no minimo", 0),
])
def test_ajuste_extremo_inteiro_preserva_pedido_legitimo(texto, nivel):
    r = detectar_intencao_deterministica_mente(texto, {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado_volume()})
    assert r and r["intent"] == "VOLUME" and r["params"]["nivel_volume"] == nivel


@pytest.mark.parametrize("alteracao", ["vencido", "sem_confirmacao", "id_divergente", "sem_contexto"])
def test_elipse_extrema_nao_herda_contrato_invalido(alteracao):
    estado = estado_volume()
    if alteracao == "vencido": estado["ultima_acao_ts"] = time.time() - 301
    elif alteracao == "sem_confirmacao": estado["ultima_acao_contrato"]["confirmado"] = False
    elif alteracao == "id_divergente": estado["ultima_acao_contrato"]["id_solicitacao"] = "estranho"
    else: estado = estado_mental_inicial()
    assert detectar_intencao_deterministica_mente("coloca no maximo", {
        "normalizar_texto": normalizar_texto, "mente_integrada_estado": estado}) is None


@pytest.mark.parametrize("texto", [
    "coloca a musica maximo respeito", "me explica o volume maximo de um cubo",
    "coloca um som chamado minimo detalhe",
])
def test_detector_de_dominio_nao_confunde_palavra_com_operacao(texto):
    r = detectar_volume_ou_midia(texto, params_cb=lambda **p: p, contexto_volume_ativo=True)
    assert not r or r["intent"] != "VOLUME", r


def test_fallback_nao_inventa_titulo_para_ajuste_extremo_sem_referente():
    from mente_laylay.autonomia.coordenador_intencao import resolver_intencao
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    chamadas = []
    def inventar(texto):
        chamadas.append(texto)
        return {"intent": "MUSIC_SEARCH", "params": {"query": "no maximo"}}
    texto = "coloca no maximo"
    r, rota = resolver_intencao(texto, "teste", {
        "normalizar_texto": normalizar_texto, "turno_atual": classificar_modalidade_turno(texto),
        "detectar_intencao_deterministica": lambda *_: None, "tentar_intencao_ai_primeiro": inventar})
    assert chamadas == [] and r is None and rota == "contexto_parametro_nao_resolvido"
