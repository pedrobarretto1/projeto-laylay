"""Seleção inconclusiva não pode sustentar classificação de papel posterior."""

from copy import deepcopy
import json
import sys

import pytest

from scripts.analises import sonda_vinculo_duas_etapas_v1 as sonda


CASOS, OURO, PARES = sonda.coordenadas.carregar_painel()


@pytest.mark.parametrize("proposta", [
    {"evidencias": []}, {"evidencias": [{"inicio": 0, "fim": 999}]},
    {"evidencias": [], "papel": "nome_designacao"},
])
def test_selecao_vazia_ou_invalida_nao_consulta_nem_fabrica_papel(proposta):
    chamadas = []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append(formato)
        return proposta if len(chamadas) == 1 else {"papel": "nome_designacao"}
    r = sonda.medir_caso(CASOS[0], modo="duas_etapas", consulta=consulta)
    assert len(chamadas) == 1
    assert r["segunda"] is None
    assert "papel" not in r


def caso(id_caso):
    return next(c for c in CASOS if c["id"] == id_caso)


def intervalo(c, texto, *, ocorrencia=0):
    fonte, inicio = c["texto"], -1
    for _ in range(ocorrencia + 1):
        inicio = fonte.index(texto, inicio + 1)
    tokens = sonda.vinculo.preparar_entrada(c)["tokens"]
    fim = inicio + len(texto)
    return {"inicio": next(t["id"] for t in tokens if t["inicio"] == inicio),
            "fim": next(t["id"] + 1 for t in tokens if t["fim"] == fim)}


def exteriores(c):
    e = sonda.vinculo.preparar_entrada(c)
    antes = [t["id"] for t in e["tokens"] if t["fim"] <= e["foco"]["inicio"]]
    depois = [t["id"] for t in e["tokens"] if t["inicio"] >= e["foco"]["fim"]]
    return [{"inicio": ids[0], "fim": ids[-1] + 1} for ids in (antes, depois) if ids]


def assert_inerte(r):
    assert all(r[k] is False for k in sonda.BASE)


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
@pytest.mark.parametrize("rotulo", sonda.papel.PAPEIS)
def test_guarda_literal_neutra_equivale_ao_historico_sem_papel(c, rotulo):
    host = sonda.vinculo.preparar_entrada(c)
    proposta = {"evidencias": exteriores(c)}
    atual = sonda.conferir_selecao_externa(c, host, proposta)
    antigo = sonda.vinculo.conferir_vinculo(c, host, {**proposta, "papel": rotulo})
    assert atual["estado"] == "selecao_literal_revisao_pendente"
    assert atual["evidencias"] == antigo["evidencias"]
    assert atual["evidencia_literal_externa"] == antigo["evidencia_literal_externa"] is True
    assert not {"papel", "papel_proposto", "referente_id"} & atual.keys()
    assert_inerte(atual)


@pytest.mark.parametrize("item", [
    {"inicio": False, "fim": 2}, {"inicio": 0.0, "fim": 2},
    {"inicio": -1, "fim": 2}, {"inicio": 0, "fim": 999},
    {"inicio": 2, "fim": 2}, {"inicio": 2, "fim": 1},
    {"inicio": 0, "fim": 1, "fonte_id": "outra"},
    {"inicio": 0, "fim": 2}, {"inicio": 1, "fim": 4},
])
@pytest.mark.parametrize("rotulo", sonda.papel.PAPEIS)
def test_negativos_literais_tem_equivalencia_e_rejeicao_atomica(item, rotulo):
    c = CASOS[0]
    host = sonda.vinculo.preparar_entrada(c)
    proposta = {"evidencias": [{"inicio": 0, "fim": 2}, item]}
    atual = sonda.conferir_selecao_externa(c, host, proposta)
    antigo = sonda.vinculo.conferir_vinculo(c, host, {**proposta, "papel": rotulo})
    assert atual["estado"] == antigo["estado"] == "intervalos_invalidos"
    assert atual["evidencias"] == antigo["evidencias"] == []
    assert not {"papel", "papel_proposto"} & atual.keys()
    assert_inerte(atual)


def test_foco_intersectado_nao_materializa_evidencia():
    c = CASOS[0]
    host = sonda.vinculo.preparar_entrada(c)
    r = sonda.conferir_selecao_externa(c, host, {"evidencias": [intervalo(c, "abra o baú")]})
    assert r["estado"] == "evidencia_intersecta_foco" and r["evidencias"] == []


def test_contexto_interno_a_aspas_externas_e_ocorrencia_repetida():
    c = caso("Q05A")
    r = sonda.conferir_selecao_externa(c, sonda.vinculo.preparar_entrada(c), {
        "evidencias": [intervalo(c, "a peça denominada")]})
    assert r["evidencias"][0]["texto"] == "a peça denominada"
    c = {"id": "controle", "texto": 'nome, nome: o perfil “reinicie o visor”.', "foco_id": "c1"}
    r = sonda.conferir_selecao_externa(c, sonda.vinculo.preparar_entrada(c), {
        "evidencias": [intervalo(c, "nome", ocorrencia=1)]})
    assert r["evidencias"][0]["inicio"] == c["texto"].rindex("nome") > 0


@pytest.mark.parametrize("proposta", [None, {}, {"evidencias": "texto"},
    {"evidencias": [], "papel": "indeterminado"}, {"evidencias": [], "autoriza_efeito": True},
    {"evidencias": [{"inicio": 0, "fim": 2}] * 3}])
def test_primeira_etapa_recusa_campos_semanticos_e_envelopes_invalidos(proposta):
    r = sonda.conferir_selecao_externa(CASOS[0], sonda.vinculo.preparar_entrada(CASOS[0]), proposta)
    assert r["estado"] == "proposta_invalida" and r["evidencias"] == []
    assert "papel_proposto" not in r
    assert_inerte(r)


def test_selecao_vazia_e_abstencao_sem_papel_nem_prova_de_ausencia():
    r = sonda.conferir_selecao_externa(CASOS[0], sonda.vinculo.preparar_entrada(CASOS[0]), {"evidencias": []})
    assert r["estado"] == "selecao_vazia_revisao_pendente"
    assert r["evidencia_literal_externa"] is False
    assert not {"papel_proposto", "ausencia_verificada", "suporte_semantico_verificado"} & r.keys()
    assert_inerte(r)


@pytest.mark.parametrize("tipo", ["bool", "float", "fonte", "foco", "tokens"])
def test_primeira_entrada_host_adulterada_recusada(tipo):
    c = CASOS[0]
    host = sonda.vinculo.preparar_entrada(c)
    if tipo in {"bool", "float"}:
        host["tokens"][0]["inicio"] = False if tipo == "bool" else 0.0
    elif tipo == "fonte":
        host["fonte"]["texto"] = "outra"
    elif tipo == "foco":
        host["foco"]["texto"] = "outro"
    else:
        host["tokens"].reverse()
    r = sonda.conferir_selecao_externa(c, host, {"evidencias": []})
    assert r["estado"] == "entrada_adulterada" and not r["evidencias"]


def test_transporte_fonte_igual_primeira_sem_ouro_e_segunda_so_com_literal():
    c, chamadas = CASOS[0], []
    proposta = {"evidencias": [intervalo(CASOS[0], "tem o nome")]}
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, deepcopy(entrada), deepcopy(formato), kwargs))
        assert not {"ancoras", "par", "id", "ouro"} & entrada.keys()
        entrada["tokens"].clear()
        entrada["fonte"].clear()
        formato.clear()
        if len(chamadas) == 1:
            return {**proposta, "papel": "nome_designacao"}
        return deepcopy(proposta) if len(chamadas) == 2 else {"papel": "nome_designacao"}
    controle = sonda.medir_caso(c, modo="acoplado", consulta=consulta)
    candidato = sonda.medir_caso(c, modo="duas_etapas", consulta=consulta)
    a, b, d = chamadas
    assert a[1] == b[1]
    assert a[3] == b[3] == d[3]
    assert a[0] == sonda.vinculo.SISTEMA_VINCULO and a[2] == sonda.vinculo.FORMATO_VINCULO
    assert b[2] == sonda.FORMATO_SELECAO and d[2] == sonda.papel.FORMATO
    assert "papel" not in b[2]["properties"]
    assert d[1]["evidencias_propostas"] == [{"fonte_id": "f1", "inicio": 8, "fim": 18, "texto": "tem o nome"}]
    assert {k: v for k, v in d[1].items() if k != "evidencias_propostas"} == b[1]
    assert controle["segunda"] is None
    assert candidato["segunda"]["entrada_modelo"] == d[1]
    assert candidato["primeira"]["entrada_modelo"] == b[1]
    assert_inerte(sonda.aferir_caso(c, candidato, OURO[c["id"]]))


def test_elegibilidade_e_literal_nao_consulta_ouro_nem_exige_pista_correta(monkeypatch):
    def proibida(*a, **k):
        pytest.fail("não usar gabarito na elegibilidade")
    monkeypatch.setattr(sonda, "aferir_caso", proibida)
    c, chamadas = CASOS[0], []
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append(entrada)
        return {"evidencias": [intervalo(c, "O botão")]} if len(chamadas) == 1 else {"papel": "indeterminado"}
    r = sonda.medir_caso(c, modo="duas_etapas", consulta=consulta)
    assert len(chamadas) == 2 and r["segunda"]["proposta"] == {"papel": "indeterminado"}
    assert_inerte(r)


@pytest.mark.parametrize("etapa", [1, 2])
def test_falha_de_consulta_nao_fabrica_papel_nem_suporte(etapa):
    c, chamadas = CASOS[0], []
    def consulta(*a, **k):
        chamadas.append(None)
        if len(chamadas) == etapa:
            raise TimeoutError()
        return {"evidencias": exteriores(c)}
    r = sonda.medir_caso(c, modo="duas_etapas", consulta=consulta)
    assert len(chamadas) == etapa
    registro = r["primeira"] if etapa == 1 else r["segunda"]
    assert registro["erro"] == "TimeoutError" and "proposta" not in registro
    afericao = sonda.aferir_caso(c, r, OURO[c["id"]])
    assert afericao["papel_bruto_alinhado"] is False and afericao["papel_e_apoio_locais_alinhados"] is False
    assert afericao["erro_primeira" if etapa == 1 else "erro_segunda"] is True
    assert_inerte(afericao)


@pytest.mark.parametrize("papel_proposto", [None, {}, {"papel": "liberado"},
    {"papel": "nome_designacao", "autoriza_efeito": True}])
def test_papel_segundo_invalido_nao_vira_conclusao_conferida(papel_proposto):
    c, chamadas = CASOS[0], []
    def consulta(*a, **k):
        chamadas.append(None)
        return {"evidencias": exteriores(c)} if len(chamadas) == 1 else papel_proposto
    r = sonda.medir_caso(c, modo="duas_etapas", consulta=consulta)
    afericao = sonda.aferir_caso(c, r, OURO[c["id"]])
    assert afericao["selecao_literal_valida"] is True
    assert afericao["papel_shape_valido"] is False and afericao["papel_e_apoio_locais_alinhados"] is False
    assert_inerte(afericao)


def test_primeira_entrada_de_outra_fonte_nao_avanca():
    c = CASOS[0]
    r = sonda.iniciar_caso(c, modo="duas_etapas", consulta=lambda *a, **k: {"evidencias": exteriores(c)})
    outro = {**c, "texto": c["texto"] + " Mais contexto."}
    with pytest.raises(ValueError, match="adulterada"):
        sonda.concluir_caso(outro, r, consulta=lambda *a, **k: pytest.fail("não consultar"))


def test_segunda_registrada_nao_e_consultada_novamente():
    c = CASOS[0]
    r = sonda.medir_caso(c, modo="duas_etapas", consulta=lambda s, e, f, **k:
        {"evidencias": exteriores(c)} if "evidencias" in f["properties"] else {"papel": "nome_designacao"})
    with pytest.raises(ValueError, match="ja registrada"):
        sonda.concluir_caso(c, r, consulta=lambda *a, **k: pytest.fail("não duplicar"))


@pytest.mark.parametrize("modo", sonda.MODOS)
@pytest.mark.parametrize("texto,foco", [('O nome é “”.', "c1"), ("Fonte inteira.", "c0")])
def test_foco_invalido_impede_primeira_consulta(texto, foco, modo):
    with pytest.raises(ValueError, match="foco citado"):
        sonda.medir_caso({"id": "controle", "texto": texto, "foco_id": foco}, modo=modo,
                        consulta=lambda *a, **k: pytest.fail("não consultar"))


def sinteticos(*, vazia=False):
    rs = []
    for c in CASOS:
        for modo in sonda.MODOS:
            def consulta(s, e, f, *, c=c, **k):
                p = {}
                if "evidencias" in f["properties"]:
                    p["evidencias"] = [] if vazia else exteriores(c)
                if "papel" in f["properties"]:
                    p["papel"] = OURO[c["id"]]["papel"]
                return p
            rs.append(sonda.medir_caso(c, modo=modo, consulta=consulta))
    return rs


def test_resumo_recalcula_cadeia_com_denominador_integral_e_custo():
    rs = sinteticos()
    for r in rs:
        r["afericao"] = {"papel_bruto_alinhado": False, "autoriza_efeito": True}
    resumo = sonda.resumir(CASOS, rs, OURO, PARES)
    for modo in sonda.MODOS:
        b = resumo["bracos"][modo]
        assert b["casos"] == 20 and b["selecao_literal_valida"] == 20
        assert b["papel_e_apoio_locais_alinhados"] == 20
        assert b["pares_papel_bruto_completos"] == 8
    assert resumo["bracos"]["acoplado"]["consultas_totais"] == 20
    assert resumo["bracos"]["duas_etapas"]["consultas_totais"] == 40
    assert resumo["holdout_novo"] is False
    assert_inerte(resumo)


def test_casos_abstidos_nao_somem_nem_recebem_indeterminado_imputado():
    resumo = sonda.resumir(CASOS, sinteticos(vazia=True), OURO, PARES)
    b = resumo["bracos"]["duas_etapas"]
    assert b["casos"] == b["selecao_vazia"] == b["consultas_totais"] == 20
    assert b["papel_bruto_valido"] == b["segunda_consulta"] == b["papel_bruto_alinhado"] == 0
    assert b["papel_e_apoio_locais_alinhados"] == 0


@pytest.mark.parametrize("etapa", ["primeira", "segunda"])
@pytest.mark.parametrize("valor", [None, "1", True, -1, float("nan"), float("inf"), float("-inf"), 10**400])
def test_resumo_recusa_duracao_invalida_sem_quebrar_a_afericao(etapa, valor):
    rs = sinteticos()
    rs[1][etapa]["duracao_consulta_s"] = valor
    assert sonda.resumir(CASOS, rs, OURO, PARES)["tipo"] == "resumo_invalido"


@pytest.mark.parametrize("etapa", ["primeira", "segunda"])
def test_resumo_recusa_duracao_ausente(etapa):
    rs = sinteticos()
    del rs[1][etapa]["duracao_consulta_s"]
    assert sonda.resumir(CASOS, rs, OURO, PARES)["tipo"] == "resumo_invalido"


def test_duracao_invalida_da_primeira_nao_permite_segunda_consulta():
    c = CASOS[0]
    r = sonda.iniciar_caso(c, modo="duas_etapas", consulta=lambda *a, **k: {"evidencias": exteriores(c)})
    r["primeira"]["duracao_consulta_s"] = float("nan")
    with pytest.raises(ValueError, match="duracao"):
        sonda.concluir_caso(c, r, consulta=lambda *a, **k: pytest.fail("não consultar"))


def test_duracoes_validas_nao_podem_transbordar_no_total():
    rs = sinteticos()
    for r in rs:
        r["primeira"]["duracao_consulta_s"] = 1e308
    assert sonda.resumir(CASOS, rs, OURO, PARES)["tipo"] == "resumo_invalido"


def test_duracao_zero_e_fracionaria_sao_validas():
    rs = sinteticos()
    for r in rs:
        r["primeira"]["duracao_consulta_s"] = 0
        if r["segunda"] is not None:
            r["segunda"]["duracao_consulta_s"] = 0.25
    resumo = sonda.resumir(CASOS, rs, OURO, PARES)
    assert resumo["bracos"]["acoplado"]["duracao_consultas_s"] == 0
    assert resumo["bracos"]["duas_etapas"]["duracao_consultas_s"] == 5


@pytest.mark.parametrize("tipo", ["duplicata", "ausente", "id", "modo", "segunda_ausente", "segunda_controle",
    "evidencia_segunda", "bool_segunda", "host", "projecao", "contradicao"])
def test_resumo_recusa_cadeia_adulterada_ou_cobertura_faltante(tipo):
    rs = sinteticos()
    if tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "ausente":
        rs.pop()
    elif tipo == "id":
        rs[0]["id"] = "outro"
    elif tipo == "modo":
        rs[0]["modo"] = "rotulo"
    elif tipo == "segunda_ausente":
        rs[1]["segunda"] = None
    elif tipo == "segunda_controle":
        rs[0]["segunda"] = deepcopy(rs[1]["segunda"])
    elif tipo == "evidencia_segunda":
        rs[1]["segunda"]["entrada_modelo"]["evidencias_propostas"][0]["texto"] = "inventada"
    elif tipo == "bool_segunda":
        rs[1]["segunda"]["entrada_modelo"]["evidencias_propostas"][0]["inicio"] = False
    elif tipo == "host":
        rs[0]["primeira"]["entrada"]["tokens"][0]["inicio"] = 0.0
    elif tipo == "projecao":
        rs[1]["primeira"]["entrada_modelo"]["tokens"][0]["fim"] = 1
    else:
        rs[1]["primeira"]["erro"] = "TimeoutError"
    r = sonda.resumir(CASOS, rs, OURO, PARES)
    assert r["tipo"] == "resumo_invalido" and "bracos" not in r
    assert_inerte(r)


def test_resumo_sem_pares_nao_reduz_denominador():
    assert sonda.resumir(CASOS, sinteticos(), OURO, [])["tipo"] == "resumo_invalido"


def test_consulta_contraditoria_nao_avanca_para_segundo_papel():
    c = CASOS[0]
    r = sonda.iniciar_caso(c, modo="duas_etapas", consulta=lambda *a, **k: {"evidencias": exteriores(c)})
    r["primeira"]["erro"] = "TimeoutError"
    with pytest.raises(ValueError, match="contraditorio"):
        sonda.concluir_caso(c, r, consulta=lambda *a, **k: pytest.fail("não consultar"))


def test_segunda_consulta_indebida_de_caso_abstido_recusada_no_resumo():
    rs = sinteticos(vazia=True)
    rs[1]["segunda"] = sinteticos()[1]["segunda"]
    assert sonda.resumir(CASOS, rs, OURO, PARES)["tipo"] == "resumo_invalido"


def test_modo_desconhecido_nao_consulta():
    with pytest.raises(ValueError, match="modo de etapas"):
        sonda.medir_caso(CASOS[0], modo="rotulo", consulta=lambda *a, **k: pytest.fail("não consultar"))


def test_cli_primeiras_antes_de_segundas_e_arquivo_exclusivo(monkeypatch, tmp_path):
    original_iniciar, original_concluir = sonda.iniciar_caso, sonda.concluir_caso
    chamadas = []
    def iniciar(c, *, modo):
        chamadas.append((1, c["id"], modo))
        return original_iniciar(c, modo=modo, consulta=lambda s, e, f, **k:
            {"evidencias": exteriores(c), **({"papel": OURO[c["id"]]["papel"]} if modo == "acoplado" else {})})
    def concluir(c, r):
        chamadas.append((2, c["id"], r["modo"]))
        return original_concluir(c, r, consulta=lambda *a, **k: {"papel": OURO[c["id"]]["papel"]})
    monkeypatch.setattr(sonda, "iniciar_caso", iniciar)
    monkeypatch.setattr(sonda, "concluir_caso", concluir)
    monkeypatch.setattr(sonda.coordenadas, "digest_modelo", lambda: "digest_controle")
    saida = tmp_path / "etapas.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    assert len(chamadas) == 60
    assert all(x[0] == 1 for x in chamadas[:40]) and all(x[0] == 2 for x in chamadas[40:])
    assert sum(chamadas[i * 2][2] == "acoplado" for i in range(20)) == 10
    antes = saida.read_bytes()
    registros = [json.loads(l) for l in antes.splitlines()]
    assert len(registros) == 62
    assert sum(r["tipo"] == "primeira" for r in registros) == 40
    assert sum(r["tipo"] == "segunda" for r in registros) == 20
    assert registros[0]["orcamento_igual"] is False
    assert registros[-1]["modelo_inalterado_entre_leituras"] is True
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 60


def test_dependencias_e_paineis_congelados():
    assert sonda.carregar_painel() == (CASOS, OURO, PARES)
