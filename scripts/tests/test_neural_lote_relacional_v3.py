"""Cobertura e proveniência do lote; verde não elimina alinhamentos pendentes."""
from collections import Counter
from copy import deepcopy

import pytest

from mente_laylay.neural.preparar_lote_relacional_v3 import (
    MOLDES, agrupar_sem_leakage, alinhar, executar, gerar_lote, preencher,
    classificar_modalidade_turno, texto_tem_comando_explicito,
)


@pytest.fixture(scope="module")
def casos():
    return gerar_lote()


def test_lote_balanceia_formas_e_conserva_irmaos(casos):
    assert len(casos) == len({c["id"] for c in casos}) == 144
    assert Counter(c["ato"] for c in casos) == {"pedido": 48, "recusa": 48, "relato": 48}
    assert Counter(c["dominio"] for c in casos) == {"apps": 48, "musica": 48, "arquivos": 48}
    assert set(Counter(c["grupo_construcao"] for c in casos).values()) == {12}
    assert set(Counter(c["grupo_contraste"] for c in casos).values()) == {2}
    assert len(MOLDES) == 12
    assert all(c["particao"] == "desenvolvimento" for c in casos)


@pytest.mark.parametrize("indice", range(144))
def test_anotacao_conserva_papeis_e_offsets_ou_rejeita_transformacao(casos, indice):
    c = casos[indice]
    antes = deepcopy(c)
    turno = classificar_modalidade_turno(c["texto_entrada"], texto_tem_comando_explicito=texto_tem_comando_explicito)
    transformado = any(s["texto"] not in c["texto_entrada"] for s in turno["segmentos"])
    if transformado:
        # Não é sucesso de alinhamento: a origem transformada exige um mapa.
        with pytest.raises(ValueError, match="posição literal única"):
            alinhar(c)
    else:
        a = alinhar(c)
        acao = next(acao for s in a["anotacao"]["segmentos"] for acao in s["acoes"])
        fonte = c["segmentos"][0]["acoes"][0]
        assert (acao["intent"], acao["action"], acao["ato"], acao["resolucao_alvo"]) == (
            fonte["intent"], fonte["action"], fonte["ato"], fonte["resolucao_alvo"])
        for papel in ("alvos_solicitados", "alvos_excluidos", "alvos_mencionados"):
            assert [m["texto"] for m in acao[papel]] == [m["texto"] for m in fonte[papel]]
            for m in acao[papel]:
                s = next(s for s in a["anotacao"]["segmentos"] if s["indice"] == m["segmento"])
                assert s["texto"][m["inicio"]:m["fim"]] == m["texto"]
        assert a["treino_permitido"] is a["autoriza_execucao"] is a["autoriza_promocao"] is False
    assert c == antes


def test_ancora_explicita_nao_e_substituida_pela_modalidade_do_classificador(casos):
    c = casos[0]
    a = alinhar(c)
    assert a["anotacao"]["segmentos"][0]["acoes"] == []
    assert a["anotacao"]["segmentos"][1]["acoes"][0]["ato"] == "pedido"
    assert a["anotacao"]["segmentos"][1]["acoes"][0]["alvos_excluidos"][0]["segmento"] == 0
    errado = deepcopy(c)
    errado["ancora_dono"] = -1
    with pytest.raises(ValueError, match="âncora"):
        alinhar(errado)


@pytest.mark.parametrize("molde", ["{verbo} {a}", "{dono}{dono}{verbo} {a}", "{dono}{verbo} {a} {a}"])
def test_autoria_ausente_ou_ambigua_aborta(molde):
    with pytest.raises(ValueError):
        preencher(molde, {"verbo": "abra", "a": "o aplicativo zafrin"}, {"a": "zafrin"})


def test_agrupamento_fecha_transitividade_e_nao_separa_parentes():
    casos = [
        {"id": "a", "grupo_construcao": "f1", "texto_entrada": "não abra o aplicativo lilas"},
        {"id": "b", "grupo_construcao": "f2", "texto_entrada": "não abra o aplicativo lilas"},
        {"id": "c", "grupo_construcao": "f2", "texto_entrada": "ontem choveu muito na cidade"},
        {"id": "d", "grupo_construcao": "f3", "texto_entrada": "ontem choveu muito na cidade"},
        {"id": "e", "grupo_construcao": "f4", "texto_entrada": "sol e mar"},
    ]
    grupos, a = agrupar_sem_leakage(casos)
    assert len({grupos[k] for k in "abcd"}) == 1
    assert grupos["e"] != grupos["a"]
    assert a["independencia_semantica_certificada"] is False
    assert agrupar_sem_leakage(list(reversed(casos)))[0] == grupos


def test_destino_existente_nao_e_sobrescrito(tmp_path):
    with pytest.raises(FileExistsError):
        executar(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_relatorio_mantem_falhas_no_denominador_e_nao_libera_treino(tmp_path):
    r = executar(tmp_path / "novo")
    assert r["total"] == 144
    assert r["alinhados"] == 132 and len(r["falhas"]) == 12
    assert r["alinhados"] + len(r["falhas"]) == r["total"]
    assert len({a["id"] for a in r["casos"]} | {f["id"] for f in r["falhas"]}) == 144
    assert all("recusa_cancelamento" in f["id"] for f in r["falhas"])
    assert r["treino_permitido"] is r["modelo_avaliado"] is r["reserva_usada"] is False
    assert r["autoriza_execucao"] is r["autoriza_promocao"] is False
    assert all(set(s["atos_treino"]) == {"pedido", "recusa", "relato"}
               and 1 in s["donos_treino"] for s in r["suporte_leave_group_out"])
