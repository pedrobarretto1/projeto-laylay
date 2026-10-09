"""Apresentação de tokens não pode mudar a fonte nem certificar significado."""

from copy import deepcopy
import json
import sys

import pytest

from scripts.analises import sonda_coordenadas_vinculo_v1 as sonda


CASOS, OURO, PARES = sonda.vinculo.carregar_painel()


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
def test_projecao_id_texto_retira_so_offsets_dos_tokens(c):
    host = sonda.vinculo.preparar_entrada(c)
    modelo = sonda.projetar_entrada_modelo(c, modo="tokens_id_texto")
    assert modelo["tokens"] == [{"id": t["id"], "texto": t["texto"]} for t in host["tokens"]]
    assert {k: v for k, v in modelo.items() if k != "tokens"} == {
        k: v for k, v in host.items() if k != "tokens"}
    assert all({"inicio", "fim"} <= t.keys() for t in host["tokens"])


def test_controle_reproduz_entrada_anterior_sem_compartilhar_objetos():
    c = CASOS[0]
    host = sonda.vinculo.preparar_entrada(c)
    modelo = sonda.projetar_entrada_modelo(c, modo="tokens_com_offsets")
    assert modelo == host
    modelo["tokens"].clear()
    modelo["foco"]["texto"] = "alterado"
    assert host == sonda.vinculo.preparar_entrada(c)


def test_modo_desconhecido_recusado():
    with pytest.raises(ValueError, match="modo de coordenadas"):
        sonda.projetar_entrada_modelo(CASOS[0], modo="inventado")


def assert_inerte(r):
    assert all(r[k] is False for k in sonda.BASE)


def test_transporte_igual_exceto_tokens_nao_muda_host_ou_schema():
    chamadas = []
    c = next(c for c in CASOS if c["id"] == "Q05A")
    def consulta(sistema, entrada, formato, **kwargs):
        chamadas.append((sistema, deepcopy(entrada), deepcopy(formato), kwargs))
        assert set(entrada) == {"fonte", "foco", "aspas_sintaticas", "tokens"}
        assert not {"ancoras", "par", "id", "papel"} & entrada.keys()
        entrada["tokens"].clear()
        entrada["foco"].clear()
        formato.clear()
        return {"evidencias": [], "papel": "nome_designacao"}
    rs = [sonda.medir_caso(c, modo=m, consulta=consulta) for m in sonda.MODOS]
    a, b = chamadas
    assert a[0] == b[0] == sonda.vinculo.SISTEMA_VINCULO
    assert a[2] == b[2] == sonda.vinculo.FORMATO_VINCULO
    assert a[3] == b[3] == {"url": "http://127.0.0.1:11434/api/chat", "modelo": "qwen3:4b-instruct"}
    assert {k: v for k, v in a[1].items() if k != "tokens"} == {
        k: v for k, v in b[1].items() if k != "tokens"}
    assert b[1]["tokens"] == [{"id": t["id"], "texto": t["texto"]} for t in a[1]["tokens"]]
    assert rs[0]["entrada"] == rs[1]["entrada"] == sonda.vinculo.preparar_entrada(c)
    assert rs[0]["entrada_modelo"] == a[1] and rs[1]["entrada_modelo"] == b[1]
    assert rs[0]["conferencia"] == rs[1]["conferencia"]
    for r in rs:
        assert_inerte(r)
        assert_inerte(r["conferencia"])


@pytest.mark.parametrize("c", CASOS, ids=lambda c: c["id"])
def test_mesma_proposta_materializa_mesma_evidencia_sem_provar_papel(c):
    host = sonda.vinculo.preparar_entrada(c)
    pistas = [t["id"] for t in host["tokens"] if t["fim"] <= host["foco"]["inicio"]]
    if not pistas:
        pistas = [t["id"] for t in host["tokens"] if t["inicio"] >= host["foco"]["fim"]]
    proposta = {"papel": "indeterminado", "evidencias": [{"inicio": pistas[0], "fim": pistas[-1] + 1}]}
    rs = [sonda.medir_caso(c, modo=m, consulta=lambda *a, **k: deepcopy(proposta)) for m in sonda.MODOS]
    assert rs[0]["conferencia"] == rs[1]["conferencia"]
    assert rs[0]["conferencia"]["evidencia_literal_externa"] is True
    assert_inerte(rs[0]["conferencia"])
    assert_inerte(sonda.vinculo.aferir(rs[0], OURO[c["id"]]))


@pytest.mark.parametrize("item", [{"inicio": False, "fim": 2}, {"inicio": 0.0, "fim": 2},
    {"inicio": 1, "fim": 1}, {"inicio": 3, "fim": 2}, {"inicio": 0, "fim": 99},
    {"inicio": 0, "fim": 2, "fonte_id": "inventada"}])
def test_projecao_nao_repara_intervalo_invalido_nem_publica_parte(item):
    c = CASOS[0]
    proposta = {"papel": "nome_designacao", "evidencias": [{"inicio": 0, "fim": 2}, item]}
    for modo in sonda.MODOS:
        r = sonda.medir_caso(c, modo=modo, consulta=lambda *a, **k: deepcopy(proposta))
        assert r["conferencia"]["estado"] == "intervalos_invalidos"
        assert r["conferencia"]["evidencias"] == []
        assert sonda.vinculo.aferir(r, OURO[c["id"]])["papel_alinhado_revisao_local"] is True
        assert_inerte(r["conferencia"])


@pytest.mark.parametrize("modo", sonda.MODOS)
@pytest.mark.parametrize("texto,foco", [('O nome é “”.', "c1"), ("Fonte inteira.", "c0")])
def test_foco_invalido_aborta_antes_da_consulta(texto, foco, modo):
    with pytest.raises(ValueError, match="foco citado"):
        sonda.medir_caso({"id": "controle", "texto": texto, "foco_id": foco}, modo=modo,
                        consulta=lambda *a, **k: pytest.fail("não consultar"))


def resultados_sinteticos():
    return [sonda.medir_caso(c, modo=m, consulta=lambda *a, c=c, **k: {
        "papel": OURO[c["id"]]["papel"], "evidencias": []}) for c in CASOS for m in sonda.MODOS]


def test_resumo_recalcula_metrica_sem_promover_papel_ou_ausencia():
    rs = resultados_sinteticos()
    for r in rs:
        r["afericao"] = {"papel_alinhado_revisao_local": False, "semantica_verificada": True}
    resumo = sonda.resumir(CASOS, rs, OURO, PARES)
    for m in sonda.MODOS:
        assert resumo["bracos"][m]["papel_alinhado_revisao_local"] == 20
        assert resumo["bracos"][m]["pares_contextuais_completos"] == 8
        assert resumo["bracos"][m]["evidencias_vazias"] == 20
        assert resumo["bracos"][m]["papel_e_ancoras_alinhados_localmente"] == 0
    assert resumo["holdout_novo"] is False
    assert_inerte(resumo)


@pytest.mark.parametrize("tipo", ["duplicata", "ausente", "id", "modo_antigo", "tipo_token", "host", "projecao"])
def test_resumo_recusa_cobertura_ou_projecao_adulterada(tipo):
    rs = resultados_sinteticos()
    if tipo == "duplicata":
        rs.append(deepcopy(rs[0]))
    elif tipo == "ausente":
        rs.pop()
    elif tipo == "id":
        rs[0]["id"] = "inventado"
    elif tipo == "modo_antigo":
        rs[0]["modo"] = "rotulo"
    elif tipo == "tipo_token":
        rs[0]["entrada_modelo"]["tokens"][0]["id"] = False
    elif tipo == "host":
        rs[0]["entrada"]["tokens"][0]["inicio"] = 0.0
    else:
        rs[1]["entrada_modelo"]["tokens"][0]["fim"] = 1
    r = sonda.resumir(CASOS, rs, OURO, PARES)
    assert r["tipo"] == "resumo_invalido" and "bracos" not in r
    assert_inerte(r)


def test_falha_de_consulta_fica_observavel_separada_de_evidencia_vazia():
    def falha(*a, **k):
        raise TimeoutError()
    r = sonda.medir_caso(CASOS[0], modo=sonda.MODOS[0], consulta=falha)
    assert r["erro"] == "TimeoutError" and "proposta" not in r
    assert r["conferencia"]["estado"] == "proposta_invalida"
    assert r["entrada_modelo"] == r["entrada"]
    assert_inerte(r)


def test_cli_contrabalanceia_e_preserva_arquivo_exclusivo(monkeypatch, tmp_path):
    original = sonda.medir_caso
    chamadas = []
    def medir(c, *, modo):
        chamadas.append((c["id"], modo))
        return original(c, modo=modo, consulta=lambda *a, **k: {"papel": "indeterminado", "evidencias": []})
    monkeypatch.setattr(sonda, "medir_caso", medir)
    monkeypatch.setattr(sonda, "digest_modelo", lambda: "digest_controle")
    saida = tmp_path / "replay.jsonl"
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    sonda.main()
    assert len(chamadas) == 40 and len(set(chamadas)) == 40
    primeiras = [chamadas[i * 2][1] for i in range(20)]
    assert primeiras.count(sonda.MODOS[0]) == primeiras.count(sonda.MODOS[1]) == 10
    antes = saida.read_bytes()
    linhas = [json.loads(l) for l in antes.splitlines()]
    assert len(linhas) == 42
    assert linhas[0]["holdout_novo"] is False
    assert linhas[0]["offsets_foco_aspas_ainda_visiveis"] is True
    assert linhas[-1]["modelo_inalterado_entre_leituras"] is True
    with pytest.raises(FileExistsError):
        sonda.main()
    assert saida.read_bytes() == antes and len(chamadas) == 40


def test_baseline_e_painel_congelados():
    assert sonda.carregar_painel() == (CASOS, OURO, PARES)
