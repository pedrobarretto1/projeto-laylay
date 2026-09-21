"""Transporte não pode inventar spans, trocar papéis nem conceder execução."""
from copy import deepcopy
import json

import pytest

from mente_laylay.neural.preparar_lote_relacional_v3 import gerar_lote, alinhar
from mente_laylay.neural.transporte_anotacoes_normalizadas import (
    alinhar_com_proveniencia, construir_mapa, transportar_intervalo, executar,
)
from mente_laylay.neural.avaliacao_escopo import avaliar_escopo
from mente_laylay.neural.preparar_lote_relacional_v3 import VARIANTES


@pytest.mark.parametrize("indice", range(144))
def test_lote_chega_ao_contrato_canonico_sem_alterar_fonte_ou_alvos(indice):
    caso = gerar_lote()[indice]
    antes = deepcopy(caso)
    novo = alinhar_com_proveniencia(caso)
    assert caso == antes
    assert novo["texto_entrada"] == caso["texto_entrada"]
    fonte = caso["segmentos"][0]["acoes"][0]
    acoes = [a for s in novo["anotacao"]["segmentos"] for a in s["acoes"]]
    assert len(acoes) == 1
    acao = acoes[0]
    for k in ("intent", "action", "ato", "resolucao_alvo"):
        assert acao[k] == fonte[k]
    for papel in ("alvos_solicitados", "alvos_excluidos", "alvos_mencionados"):
        assert [m["texto"] for m in acao[papel]] == [m["texto"] for m in fonte[papel]]
        for m in acao[papel]:
            seg = next(s for s in novo["anotacao"]["segmentos"] if s["indice"] == m["segmento"])
            assert seg["texto"][m["inicio"]:m["fim"]] == m["texto"]
    assert novo["treino_permitido"] is novo["autoriza_execucao"] is novo["autoriza_promocao"] is False
    if caso["grupo_construcao"] == "recusa_cancelamento":
        assert acao["ato"] == "recusa"
        assert novo["proveniencia_normalizacao"]["passos"][0]["de"] == "cancele"
        with pytest.raises(ValueError):
            alinhar(caso)  # RED anterior preservado, sem enfraquecer alinhador literal.
    else:
        assert novo["anotacao"] == alinhar(caso)["anotacao"]


@pytest.mark.parametrize("antes,depois", [("proxma", "proxima"), ("abrirr", "abrir"), ("cancele", "cancela")])
def test_mudanca_de_comprimento_desloca_apenas_offsets(antes, depois):
    origem, destino = antes + " nome.txt", depois + " nome.txt"
    mapa = construir_mapa(origem, destino, [{"de": antes, "para": depois, "tipo": "operacional"}])
    assert transportar_intervalo(mapa, len(antes) + 1, len(origem)) == (len(depois) + 1, len(destino))
    assert transportar_intervalo(mapa, len(antes) + 1, len(antes) + 2)[0] == len(depois) + 1


def test_multiplas_transformacoes_preservam_proveniencia_original():
    m = construir_mapa("aa xx alvo", "aaaa x alvo", [
        {"de": "aa", "para": "aaaa", "tipo": "teste"}, {"de": "xx", "para": "x", "tipo": "teste"}])
    assert m["passos"][1]["inicio_fonte"] == 3
    assert m["passos"][1]["inicio_etapa"] == 5
    assert transportar_intervalo(m, 6, 10) == (7, 11)


@pytest.mark.parametrize("fonte,de", [("aa aa alvo", "aa"), ("aaa alvo", "aa"), ("abc alvo", "zz")])
def test_metadados_sem_posicao_rejeitam_ambiguidade_e_ausencia(fonte, de):
    with pytest.raises(ValueError, match="ambígua"):
        construir_mapa(fonte, "irrelevante", [{"de": de, "para": "b", "tipo": "teste"}])


def test_transformacao_nao_registrada_nao_vira_diff_aproximado():
    with pytest.raises(ValueError, match="não registrada"):
        construir_mapa("abra  nome", "abra nome", [])
    with pytest.raises(ValueError, match="não registrada"):
        construir_mapa("abra Nome", "abra nome", [])


def test_alteracao_de_mencao_ou_ancora_aborta_mesmo_com_mesmo_tamanho():
    mapa = construir_mapa("abre alvo", "abra alvo", [{"de": "abre", "para": "abra", "tipo": "teste"}])
    for inicio, fim in [(0, 1), (0, 4), (2, 7)]:
        with pytest.raises(ValueError, match="protegida"):
            transportar_intervalo(mapa, inicio, fim)


def test_eventos_sobrepostos_nao_sao_silenciosamente_compostos():
    with pytest.raises(ValueError, match="sobrepostas"):
        construir_mapa("aa alvo", "cc alvo", [
            {"de": "aa", "para": "bb", "tipo": "teste"},
            {"de": "bb", "para": "cc", "tipo": "teste"}])


@pytest.mark.parametrize("evento", [{}, {"de": "a", "para": "b"},
    {"de": "a", "para": "b", "tipo": "teste", "autoriza_execucao": True},
    {"de": "", "para": "b", "tipo": "teste"}])
def test_evento_incompleto_ou_com_autoridade_aborta(evento):
    with pytest.raises(ValueError):
        construir_mapa("a", "b", [evento])


@pytest.mark.parametrize("a,b", [(True, 2), (0, False), (-1, 1), (0, 10), (1, 1)])
def test_limites_invalidos_nao_apontam_para_outro_caractere(a,b):
    with pytest.raises(ValueError):
        transportar_intervalo(construir_mapa("abc", "abc", []), a,b)


def test_medidor_recebe_fonte_original_e_segmentos_reais_sem_gabarito():
    c = alinhar_com_proveniencia(gerar_lote()[7])
    recebidas = []
    def prever(entrada):
        recebidas.append(entrada)
        return []  # Teste do transporte/denominador, NÃO um modelo neural.
    r = avaliar_escopo([c], prever=prever, variantes_permitidas=VARIANTES)
    assert recebidas[0]["texto_entrada"].startswith("cancele")
    assert recebidas[0]["segmentos"][0]["texto"].startswith("cancela")
    assert set(recebidas[0]) == {"texto_entrada", "segmentos"}
    assert r["totais"]["acoes_ausentes"] == 1
    assert r["totais"]["casos_exatos"] == r["totais"]["falhas_inferencia"] == 0


def test_protocolo_de_outro_lote_nao_autentica_fonte_selecionada(tmp_path):
    (tmp_path / "protocolo.json").write_text(json.dumps({"fontes": {"outro_lote.json": "hash"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="vinculado"):
        executar(tmp_path, tmp_path / "saida")
    assert not (tmp_path / "saida").exists()
