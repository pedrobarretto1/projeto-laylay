"""Preditores artificiais testam o medidor; não são resultados da rede."""

from copy import deepcopy
from pathlib import Path

import pytest

from mente_laylay.neural.auditar_escopo_manual import auditar_piloto
from mente_laylay.neural.avaliacao_escopo import avaliar_escopo

VARIANTES = {("MUSIC_SEARCH", "search"), ("APP_OPEN", "open"),
             ("CLOSE_APP", "close"), ("CLOSE_TAB", "close"), ("FILE_READ", "read")}


@pytest.fixture(scope="module")
def piloto():
    caminho = Path(__file__).parents[2] / "mente_laylay/neural/datasets/escopo_relacional_piloto_v1.json"
    return auditar_piloto(caminho)["casos"]


def saida(caso):
    return [{k: deepcopy(s[k]) for k in ("indice", "acoes")} for s in caso["anotacao"]["segmentos"]]


def medir(casos, prever):
    return avaliar_escopo(casos, prever=prever, variantes_permitidas=VARIANTES)


def test_medidor_reconhece_oraculo_sintetico_sem_chamar_isso_de_modelo(piloto):
    respostas = {c["texto_entrada"]: saida(c) for c in piloto}
    r = medir(piloto, lambda e: respostas[e["texto_entrada"]])
    assert r["totais"]["casos_exatos"] == 16
    assert r["totais"]["acoes_esperadas"] == 17
    assert r["taxa_casos_exatos"] == 1
    assert not r["autoriza_execucao"] and not r["autoriza_promocao"]


def test_excluir_alvo_nao_e_acertar_intencao_e_tocar_o_rejeitado(piloto):
    c = piloto[0]
    p = saida(c)
    acao = p[0]["acoes"][0]
    acao["alvos_solicitados"], acao["alvos_excluidos"] = acao["alvos_excluidos"], acao["alvos_solicitados"]
    r = medir([c], lambda _: p)
    assert r["totais"]["atos_corretos"] == 1
    assert r["totais"]["excluidos_solicitados"] == 1
    assert r["papeis"]["alvos_solicitados"] == {"corretos": 0, "ausentes": 1, "extras": 1}
    assert r["taxa_casos_exatos"] == 0


def test_mencao_em_relato_nao_pode_virar_alvo_pedido(piloto):
    c = next(c for c in piloto if c["id"] == "relato")
    p = saida(c)
    a = p[0]["acoes"][0]
    a.update(ato="pedido", resolucao_alvo="explicito",
             alvos_solicitados=a["alvos_mencionados"], alvos_mencionados=[])
    r = medir([c], lambda _: p)
    assert r["totais"]["mencoes_solicitadas"] == r["totais"]["pedidos_inventados"] == 1


@pytest.mark.parametrize("retorno", [None, {}, [{"indice": 0, "acoes": "inválido"}]])
def test_saida_invalida_conta_como_falha_nao_recusa_correta(piloto, retorno):
    r = medir([piloto[1]], lambda _: retorno)
    assert r["totais"]["casos"] == r["totais"]["falhas_inferencia"] == 1
    assert r["totais"]["casos_exatos"] == 0


def test_excecao_nao_vaza_mensagem_privada_nem_remove_denominador(piloto):
    def falhar(_):
        raise RuntimeError("detalhes privados")
    r = medir(piloto[:2], falhar)
    assert r["totais"]["casos"] == r["totais"]["falhas_inferencia"] == 2
    assert r["totais"]["pedidos_perdidos"] == 1
    assert "detalhes privados" not in str(r)


def test_input_nao_contem_rotulo_catalogo_esperado_spans_ou_autoridade(piloto):
    antes = deepcopy(piloto)
    def espiao(entrada):
        assert set(entrada) == {"texto_entrada", "segmentos"}
        assert all(set(s) == {"indice", "texto"} for s in entrada["segmentos"])
        entrada["segmentos"].clear()
        return []
    r = medir(piloto, espiao)
    assert r["totais"]["acoes_ausentes"] == 17
    assert piloto == antes


def test_todos_os_esperados_sao_validados_antes_de_inferir(piloto):
    casos = deepcopy(piloto[:2])
    casos[1]["autoriza_execucao"] = True
    chamadas = []
    with pytest.raises(ValueError, match="proibir"):
        medir(casos, lambda e: chamadas.append(e))
    assert chamadas == []


def test_acao_extra_e_resolucao_errada_nao_desaparecem(piloto):
    c = piloto[0]
    p = saida(c)
    p[0]["acoes"][0]["resolucao_alvo"] = "contextual"
    extra = deepcopy(p[0]["acoes"][0])
    extra.update(intent="FILE_READ", action="read")
    p[0]["acoes"].append(extra)
    r = medir([c], lambda _: p)
    assert r["totais"]["acoes_extras"] == r["totais"]["pedidos_inventados"] == 1
    assert r["totais"]["resolucoes_corretas"] == 0


def test_ordem_das_acoes_nao_muda_resultado_mas_acao_errada_muda(piloto):
    c = piloto[-1]
    p = saida(c)
    p[0]["acoes"].reverse()
    assert medir([c], lambda _: p)["taxa_casos_exatos"] == 1
    p[0]["acoes"].pop()
    r = medir([c], lambda _: p)
    assert r["totais"]["acoes_ausentes"] == 1
    assert r["taxa_casos_exatos"] == 0


def test_alvo_com_span_inventado_rejeita_previsao_inteira(piloto):
    p = saida(piloto[0])
    p[0]["acoes"][0]["alvos_solicitados"][0]["texto"] = "alvo inventado"
    r = medir(piloto[:1], lambda _: p)
    assert r["totais"]["falhas_inferencia"] == 1
