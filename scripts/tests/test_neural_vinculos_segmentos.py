"""Escopo entre segmentos é anotação independente, não permissão operacional."""

from copy import deepcopy

import pytest

from mente_laylay.autonomia.porteiro_acoes import texto_tem_comando_explicito
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.neural.anotacao_escopo import referencia_canonica, validar_anotacao_escopo
from mente_laylay.neural.avaliacao_escopo import avaliar_escopo
from mente_laylay.neural.datasets.gerar_escopo_relacional_v2 import gerar_grade_relacional
from mente_laylay.neural.revisar_vinculos_segmentos import vincular_plano_manual

VARIANTES = {("APP_OPEN", "open"), ("MUSIC_SEARCH", "search"), ("FILE_READ", "read")}


def preparar(dominio="apps", aspas=False):
    caso = next(c for c in gerar_grade_relacional() if c["grupo_entidades"] == "rel_v2_e0"
                and c["grupo_construcao"] == "rel_v2_f1" and c["mecanismo"] == "pedido"
                and c["dominio"] == dominio and c["com_aspas"] == aspas)
    turno = classificar_modalidade_turno(caso["texto_entrada"],
                                        texto_tem_comando_explicito=texto_tem_comando_explicito)
    assert len(turno["segmentos"]) == 2
    acao = deepcopy(caso["segmentos"][0]["acoes"][0])
    # Relação esperada declarada no teste: exclusão no segmento 0, pedido no 1.
    # Não é inferida pelo classificador nem promovida a autorização.
    for papel, indice in (("alvos_solicitados", 1), ("alvos_excluidos", 0)):
        for m in acao[papel]:
            texto = turno["segmentos"][indice]["texto"]
            m.update(segmento=indice, inicio=texto.index(m["texto"]),
                     fim=texto.index(m["texto"]) + len(m["texto"]))
    anotacao = {"versao": 2, "origem": "anotacao_manual",
                "referencia_sha256": referencia_canonica(turno)["sha256"],
                "segmentos": [{"indice": s["indice"], "texto": s["texto"],
                               "acoes": [acao] if s["indice"] == 1 else []}
                              for s in turno["segmentos"]]}
    return caso, turno, anotacao


@pytest.mark.parametrize("dominio", ["apps", "musica", "arquivos"])
@pytest.mark.parametrize("aspas", [False, True])
def test_acao_pode_referenciar_restricao_em_outro_segmento_sem_colar_textos(dominio, aspas):
    _, turno, anotacao = preparar(dominio, aspas)
    antes = deepcopy((turno, anotacao))
    r = validar_anotacao_escopo(anotacao, turno=turno, variantes_permitidas=VARIANTES)
    assert r["versao"] == 2
    assert len(r["referencia"]["leitura_observada"]["segmentos"]) == 2
    assert r["anotacao"]["segmentos"][1]["acoes"][0]["alvos_excluidos"][0]["segmento"] == 0
    assert (turno, anotacao) == antes
    assert r["autoriza_execucao"] is r["treino_permitido"] is r["autoriza_promocao"] is False


@pytest.mark.parametrize("erro", ["origem", "bool", "offset", "sem_origem", "autoridade", "cobertura", "obsoleta"])
def test_vinculo_invalido_aborta_sem_procurar_alvo_em_outro_lugar(erro):
    _, turno, a = preparar()
    mencao = a["segmentos"][1]["acoes"][0]["alvos_excluidos"][0]
    if erro == "origem":
        mencao["segmento"] = 99
    elif erro == "bool":
        mencao["segmento"] = False
    elif erro == "offset":
        mencao["inicio"] += 1
    elif erro == "sem_origem":
        del mencao["segmento"]
    elif erro == "autoridade":
        mencao["autoriza_execucao"] = True
    elif erro == "cobertura":
        a["segmentos"].pop(0)
    else:
        turno["segmentos"][0]["veto_execucao_operacional"] = True
    with pytest.raises(ValueError):
        validar_anotacao_escopo(a, turno=turno, variantes_permitidas=VARIANTES)


def test_medidor_penaliza_alvo_rejeitado_mesmo_vindo_de_outro_segmento():
    caso, turno, a = preparar()
    r = validar_anotacao_escopo(a, turno=turno, variantes_permitidas=VARIANTES)
    c = {"id": caso["id"], "texto_entrada": caso["texto_entrada"], **r}
    p = [{k: deepcopy(s[k]) for k in ("indice", "acoes")} for s in a["segmentos"]]
    medir = lambda pre: avaliar_escopo([c], prever=lambda _: pre, variantes_permitidas=VARIANTES)
    assert medir(p)["taxa_casos_exatos"] == 1  # oráculo do TESTE, não modelo
    acao = p[1]["acoes"][0]
    acao["alvos_solicitados"], acao["alvos_excluidos"] = acao["alvos_excluidos"], acao["alvos_solicitados"]
    medido = medir(p)
    assert medido["totais"]["excluidos_solicitados"] == 1
    assert medido["taxa_casos_exatos"] == 0


def test_medidor_nao_injeta_vinculo_esperado_na_entrada_nem_ignora_dono_errado():
    caso, turno, a = preparar()
    r = validar_anotacao_escopo(a, turno=turno, variantes_permitidas=VARIANTES)
    p = [{k: deepcopy(s[k]) for k in ("indice", "acoes")} for s in a["segmentos"]]
    p[0]["acoes"], p[1]["acoes"] = p[1]["acoes"], []
    def prever(entrada):
        assert set(entrada) == {"texto_entrada", "segmentos"}
        assert all(set(s) == {"indice", "texto"} for s in entrada["segmentos"])
        return p
    m = avaliar_escopo([{"id": caso["id"], "texto_entrada": caso["texto_entrada"], **r}],
                       prever=prever, variantes_permitidas=VARIANTES)
    assert m["totais"]["acoes_ausentes"] == m["totais"]["acoes_extras"] == 1
    assert m["taxa_casos_exatos"] == 0


def test_v2_nao_apaga_veto_existente_ou_muda_rotulo_de_recusa():
    _, turno, a = preparar()
    turno["veto_execucao_operacional"] = True
    a["referencia_sha256"] = referencia_canonica(turno)["sha256"]
    r = validar_anotacao_escopo(a, turno=turno, variantes_permitidas=VARIANTES)
    assert r["referencia"]["leitura_observada"]["veto_execucao_operacional"] is True
    assert r["autoriza_execucao"] is False
    acao = a["segmentos"][1]["acoes"][0]
    acao["ato"] = "recusa"
    with pytest.raises(ValueError, match="somente pedido"):
        validar_anotacao_escopo(a, turno=turno, variantes_permitidas=VARIANTES)


def test_plano_manual_muda_apenas_offsets_sem_inferir_dono_ou_papel():
    caso, turno, esperado = preparar()
    antes = deepcopy((caso, turno))
    limite = caso["texto_entrada"].index(", ")
    r = vincular_plano_manual(caso, turno, intervalos={0: (0, limite), 1: (limite + 2, len(caso["texto_entrada"]))},
                             donos={("APP_OPEN", "open"): 1}, variantes_permitidas=VARIANTES)
    assert r["anotacao"] == esperado
    assert (caso, turno) == antes
    assert r["plano_manual"]["donos"] == [{"intent": "APP_OPEN", "action": "open", "segmento": 1}]


@pytest.mark.parametrize("erro", ["dono_ausente", "dono_bool", "dono_inexistente", "intervalo_incompleto", "intervalo_errado", "span_cruzado"])
def test_conversao_nao_resolve_lacunas_do_plano_manual(erro):
    caso, turno, _ = preparar()
    limite = caso["texto_entrada"].index(", ")
    intervalos = {0: (0, limite), 1: (limite + 2, len(caso["texto_entrada"]))}
    donos = {("APP_OPEN", "open"): 1}
    if erro == "dono_ausente":
        donos.clear()
    elif erro == "dono_bool":
        donos[("APP_OPEN", "open")] = True
    elif erro == "dono_inexistente":
        donos[("APP_OPEN", "open")] = 99
    elif erro == "intervalo_incompleto":
        del intervalos[0]
    elif erro == "intervalo_errado":
        intervalos[1] = (limite + 1, len(caso["texto_entrada"]))
    else:
        m = caso["segmentos"][0]["acoes"][0]["alvos_excluidos"][0]
        m.update(fim=limite + 4, texto=caso["texto_entrada"][m["inicio"]:limite + 4])
    with pytest.raises(ValueError):
        vincular_plano_manual(caso, turno, intervalos=intervalos, donos=donos, variantes_permitidas=VARIANTES)


def test_conversao_nao_descarta_negacao_que_sumiu_do_snapshot():
    caso, turno, _ = preparar()
    # Simula uma fronteira anterior perdendo palavras, não um erro do modelo.
    inicio = caso["texto_entrada"].index("pelvora")
    limite = caso["texto_entrada"].index(", ")
    turno["segmentos"][0]["texto"] = "pelvora"
    with pytest.raises(ValueError, match="descartaria conteúdo"):
        vincular_plano_manual(caso, turno,
                             intervalos={0: (inicio, limite), 1: (limite + 2, len(caso["texto_entrada"]))},
                             donos={("APP_OPEN", "open"): 1}, variantes_permitidas=VARIANTES)
