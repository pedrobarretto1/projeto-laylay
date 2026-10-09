"""Evidência contextual literal não confirma relação, papel nem permissão."""

from copy import deepcopy
import json

import pytest

from scripts.analises import sonda_vinculo_contextual_v1 as sonda
from scripts.analises.contrato_vigencia_criterios import RegistroVigenciaCriterios


CASOS = json.loads(sonda.ENTRADAS.read_text(encoding="utf-8"))["casos"]
REVISAO = json.loads(sonda.REVISAO.read_text(encoding="utf-8"))
OURO, PARES = REVISAO["casos"], REVISAO["pares_contextuais"]


def caso(identificador):
    return next(c for c in CASOS if c["id"] == identificador)


def intervalo(c, trecho, *, ocorrencia=0):
    entrada = sonda.preparar_entrada(c)
    fonte, tokens = c["texto"], entrada["tokens"]
    inicio = -1
    for _ in range(ocorrencia + 1):
        inicio = fonte.index(trecho, inicio + 1)
    fim = inicio + len(trecho)
    return {"inicio": next(t["id"] for t in tokens if t["inicio"] == inicio),
            "fim": next(t["id"] + 1 for t in tokens if t["fim"] == fim)}


def intervalos_exteriores(c):
    entrada = sonda.preparar_entrada(c)
    foco, tokens = entrada["foco"], entrada["tokens"]
    antes = [t["id"] for t in tokens if t["fim"] <= foco["inicio"]]
    depois = [t["id"] for t in tokens if t["inicio"] >= foco["fim"]]
    return [{"inicio": ids[0], "fim": ids[-1] + 1} for ids in (antes, depois) if ids]


def assert_inerte(r):
    assert all(r[k] is False for k in sonda.BASE)
    assert not {"suporte_semantico_verificado", "autoriza_execucao", "ausencia_verificada", "tratado", "referente_id"} & r.keys()


@pytest.mark.parametrize("id_caso", list(OURO))
def test_papel_e_contexto_literal_alinhados_localmente_continuam_propostas(id_caso):
    c = caso(id_caso)
    entrada = sonda.preparar_entrada(c)
    proposta = {"evidencias": intervalos_exteriores(c), "papel": OURO[id_caso]["papel"]}
    conferencia = sonda.conferir_vinculo(c, entrada, proposta)
    assert conferencia["estado"] == "vinculo_proposto_revisao_pendente"
    for e in conferencia["evidencias"]:
        assert c["texto"][e["inicio"]:e["fim"]] == e["texto"]
        assert e["fim"] <= entrada["foco"]["inicio"] or e["inicio"] >= entrada["foco"]["fim"]
        assert e["fonte_id"] == entrada["fonte"]["identificador"]
    r = {"proposta": proposta, "conferencia": conferencia}
    afericao = sonda.aferir(r, OURO[id_caso])
    assert afericao["papel_e_ancoras_alinhados_localmente"] is True
    assert_inerte(conferencia)
    assert_inerte(afericao)


def test_papel_bruto_alinhado_nao_some_quando_intervalo_intersecta_foco():
    c = caso("Q01A")
    proposta = {"evidencias": [intervalo(c, "abra o baú")], "papel": "nome_designacao"}
    conferencia = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), proposta)
    assert conferencia["estado"] == "evidencia_intersecta_foco"
    assert conferencia["evidencias"] == [] and conferencia["papel_proposto"] is None
    afericao = sonda.aferir({"proposta": proposta, "conferencia": conferencia}, OURO[c["id"]])
    assert afericao["papel_alinhado_revisao_local"] is True
    assert afericao["envelope_conjunto_valido"] is False
    assert afericao["papel_e_ancoras_alinhados_localmente"] is False
    assert_inerte(conferencia)


def test_literalidade_e_cobertura_local_nao_corrigem_papel_errado():
    c = caso("Q01A")
    proposta = {"evidencias": [intervalo(c, "tem o nome")], "papel": "operacao_mencionada"}
    conferencia = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), proposta)
    r = sonda.aferir({"proposta": proposta, "conferencia": conferencia}, OURO[c["id"]])
    assert r["cobertura_ancoras_relacionais_locais"] is True
    assert r["papel_alinhado_revisao_local"] is False
    assert r["papel_e_ancoras_alinhados_localmente"] is False
    assert_inerte(conferencia)


def test_intervalo_externo_sem_pista_relacional_continua_so_literal():
    c = caso("Q01A")
    proposta = {"evidencias": [intervalo(c, "O botão")], "papel": "nome_designacao"}
    conferencia = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), proposta)
    r = sonda.aferir({"proposta": proposta, "conferencia": conferencia}, OURO[c["id"]])
    assert r["evidencia_literal_externa"] is True
    assert r["cobertura_ancoras_relacionais_locais"] is False
    assert_inerte(r)


@pytest.mark.parametrize("rotulo", list(sonda.papel.PAPEIS))
def test_evidencia_vazia_nao_prova_ausencia_nem_suporte(rotulo):
    c = caso("Q08A")
    conferencia = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), {"evidencias": [], "papel": rotulo})
    assert conferencia["estado"] == "vinculo_proposto_revisao_pendente"
    assert conferencia["evidencia_literal_externa"] is False
    assert_inerte(conferencia)


def test_contexto_de_foco_interno_pode_estar_em_aspas_externas():
    c = caso("Q05A")
    entrada = sonda.preparar_entrada(c)
    proposta = {"evidencias": [intervalo(c, "a peça denominada")], "papel": "nome_designacao"}
    conferencia = sonda.conferir_vinculo(c, entrada, proposta)
    exterior = entrada["aspas_sintaticas"]["regioes_entre_aspas"][0]
    e = conferencia["evidencias"][0]
    assert exterior["inicio"] < e["inicio"] < e["fim"] < exterior["fim"]
    assert conferencia["evidencia_literal_externa"] is True


def test_intervalos_mantem_segunda_ocorrencia_sem_reancorar_texto():
    c = {"id": "controle", "texto": 'nome, nome: o perfil “reinicie o visor”.', "foco_id": "c1"}
    p = {"evidencias": [intervalo(c, "nome", ocorrencia=1)], "papel": "nome_designacao"}
    # Materialização distingue ocorrências literalmente idênticas, sem busca textual.
    r = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), p)
    assert r["evidencias"][0]["inicio"] == c["texto"].rindex("nome")
    assert r["evidencias"][0]["inicio"] > 0


@pytest.mark.parametrize("item", [{"inicio": False, "fim": 2}, {"inicio": 0.0, "fim": 2},
                                 {"inicio": -1, "fim": 2}, {"inicio": 0, "fim": 999},
                                 {"inicio": 2, "fim": 2}, {"inicio": 2, "fim": 1},
                                 {"inicio": 0, "fim": 1, "fonte_id": "outra"}])
def test_intervalos_invalidos_nao_publicam_parte_da_evidencia(item):
    c = caso("Q01A")
    p = {"evidencias": [intervalo(c, "O botão"), item], "papel": "nome_designacao"}
    r = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), p)
    assert r["estado"] == "intervalos_invalidos" and r["evidencias"] == []
    assert r["papel_proposto"] is None
    assert_inerte(r)


@pytest.mark.parametrize("tipo", ["duplicado", "invertido", "sobreposto"])
def test_ordem_e_duplicacao_tem_guardas_atomicas(tipo):
    c = caso("Q01A")
    a, b = intervalo(c, "O botão"), intervalo(c, "tem o nome")
    itens = [a, a] if tipo == "duplicado" else ([b, a] if tipo == "invertido" else [a, {"inicio": a["inicio"] + 1, "fim": b["fim"]}])
    r = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), {"evidencias": itens, "papel": "nome_designacao"})
    assert r["estado"] == "intervalos_invalidos" and not r["evidencias"]


@pytest.mark.parametrize("proposta", [None, {}, {"evidencias": [], "papel": []},
                                       {"evidencias": [], "papel": "liberado"},
                                       {"evidencias": [], "papel": "indeterminado", "autoriza_efeito": True},
                                       {"evidencias": [{"inicio": 0, "fim": 1}] * 3, "papel": "nome_designacao"}])
def test_shape_fechado_rejeita_flags_ou_campos_extras(proposta):
    c = caso("Q01A")
    r = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), proposta)
    assert r["estado"] == "proposta_invalida" and r["evidencias"] == []
    assert_inerte(r)


@pytest.mark.parametrize("tipo", ["float", "bool", "origem", "foco", "tokens"])
def test_entrada_integra_inclui_tokens_e_fonte_original(tipo):
    c = caso("Q01A")
    entrada = sonda.preparar_entrada(c)
    if tipo in {"float", "bool"}:
        entrada["tokens"][0]["inicio"] = 0.0 if tipo == "float" else False
    elif tipo == "origem":
        entrada["fonte"]["origem"] = "pesquisa_verificada"
    elif tipo == "foco":
        entrada["foco"]["texto"] = "nome inventado"
    else:
        entrada["tokens"].reverse()
    r = sonda.conferir_vinculo(c, entrada, {"evidencias": [], "papel": "indeterminado"})
    assert r["estado"] == "entrada_adulterada" and r["papel_proposto"] is None


def test_mesma_entrada_transporte_e_tarefa_em_ambos_bracos_sem_ouro():
    chamadas = []
    c = caso("Q05A")
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, deepcopy(entrada), deepcopy(formato), kwargs))
        assert set(entrada) == {"fonte", "foco", "aspas_sintaticas", "tokens"}
        assert "Q05A" not in json.dumps(entrada) and "ancoras" not in entrada and "par" not in entrada
        entrada["tokens"].clear()
        return {"papel": "nome_designacao"} if "evidencias" not in formato["properties"] else {"evidencias": [], "papel": "nome_designacao"}
    rs = [sonda.medir_caso(c, modo=m, consulta=consulta) for m in sonda.MODOS]
    a, b = chamadas
    assert a[1] == b[1] and a[3] == b[3]
    assert a[0] == sonda.papel.SISTEMA and a[2] == sonda.papel.FORMATO
    assert b[0].startswith(a[0].removesuffix("Retorne somente JSON com papel."))
    assert all(r["entrada"]["tokens"] for r in rs)


def test_metalinguagem_e_negacao_nao_se_transformam_em_vigencia(monkeypatch):
    def proibida(*a, **k):
        raise AssertionError("evidência não registra critério")
    monkeypatch.setattr(RegistroVigenciaCriterios, "registrar_revisao", proibida)
    c = caso("Q03B")
    r = sonda.medir_caso(c, modo="vinculo", consulta=lambda *a, **k: {
        "evidencias": [intervalo(c, "pedido negativo")], "papel": "operacao_mencionada"})
    assert r["entrada"]["foco"]["texto"].startswith("não ")
    assert_inerte(r)
    assert_inerte(r["conferencia"])


@pytest.mark.parametrize("foco, texto", [("c0", "Apenas fonte inteira."), ("c1", 'O nome é “”.')])
def test_diagnostico_exige_foco_citado_nao_vazio_antes_de_consultar(foco, texto):
    c = {"id": "controle", "texto": texto, "foco_id": foco}
    with pytest.raises(ValueError, match="foco citado"):
        sonda.medir_caso(c, modo="vinculo", consulta=lambda *a, **k: pytest.fail("não consultar"))


def test_ancoras_de_revisao_nao_sao_fabricadas_concatenando_intervalos():
    c = caso("Q01A")
    p = {"evidencias": [intervalo(c, "tem"), intervalo(c, "o nome")], "papel": "nome_designacao"}
    conferencia = sonda.conferir_vinculo(c, sonda.preparar_entrada(c), p)
    r = sonda.aferir({"proposta": p, "conferencia": conferencia}, OURO[c["id"]])
    assert r["evidencia_literal_externa"] is True
    assert r["cobertura_ancoras_relacionais_locais"] is False


def test_resumo_recusa_duplicata_e_cobertura_faltante():
    rs = [{"id": c["id"], "modo": m, "afericao": sonda.aferir({}, OURO[c["id"]])}
          for c in CASOS for m in sonda.MODOS]
    assert sonda.resumir(CASOS, rs, PARES)["bracos"]["rotulo"]["casos"] == 20
    for adulterado in (rs + [deepcopy(rs[0])], rs[:-1]):
        r = sonda.resumir(CASOS, adulterado, PARES)
        assert r["tipo"] == "resumo_invalido" and "bracos" not in r
        assert_inerte(r)


def test_painel_congelado():
    assert sonda.carregar_painel() == (CASOS, OURO, PARES)


def test_ouro_alterado_nao_e_recongelado_automaticamente(monkeypatch, tmp_path):
    revisao = tmp_path / "revisao.json"
    revisao.write_text('{}', encoding="utf-8")
    monkeypatch.setattr(sonda, "REVISAO", revisao)
    with pytest.raises(ValueError, match="apos congelamento"):
        sonda.carregar_painel()
