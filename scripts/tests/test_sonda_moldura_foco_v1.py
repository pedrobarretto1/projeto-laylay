from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_moldura_foco_v1 as s


CASOS = s.carregar_painel()
IX = {c["id"]: c for c in CASOS}


def medir(c, rep=1, *, proposta=None, motivo="stop"):
    p = proposta if proposta is not None else {"predicado": c["pista"], "papel": c["papel"]}
    return s.anterior.medir_caso(c, modo="com_exemplos", repeticao=rep,
        post=lambda *a, **k: SimpleNamespace(status_code=200, text=json.dumps({
            "done": True, "done_reason": motivo, "message": {"content": json.dumps(p)}})))


@pytest.fixture(scope="module")
def completos():
    return [medir(c, rep) for c, rep in s.sequencia(CASOS)]


def test_ablacao_preserva_foco_papel_e_pista_sem_reusar_offsets_antigos():
    for c in CASOS:
        original = IX[c["origem"] + ":original"]
        e, o = [s.anterior.papel.preparar_entrada(x) for x in (c, original)]
        assert e["foco"]["texto"] == o["foco"]["texto"]
        assert c["papel"] == original["papel"] and c["pista"] == original["pista"]
        assert e["fonte"]["texto"] == c["texto"]
        assert c["texto"][e["foco"]["inicio"]:e["foco"]["fim"]] == e["foco"]["texto"]
        if c["variante"] == "citacao_plana":
            assert ": " in c["texto"] and "“" not in c["texto"] and c["foco_id"] == "c1"
        if c["variante"] == "sem_moldura":
            assert not c["texto"].startswith(("O roteiro", "O registro", "A ficha"))


def test_proponente_demos_schema_e_opcoes_nao_mudam_e_metadados_nao_vazam():
    antigos = {c["id"]: c for c in s.anterior.carregar_painel()["avaliacao"]}
    for c in CASOS:
        r = s.anterior.preparar_requisicao(c, "com_exemplos")
        baseline = s.anterior.preparar_requisicao(antigos[c["origem"]], "com_exemplos")
        assert r["messages"][:-1] == baseline["messages"][:-1]
        assert {k: v for k, v in r.items() if k != "messages"} == {k: v for k, v in baseline.items() if k != "messages"}
        assert set(json.loads(r["messages"][-1]["content"])) == {"fonte", "foco", "aspas_sintaticas"}
        if c["variante"] == "original": assert r == baseline
        alterado = {**c, "origem": "SEGREDO", "variante": "VAZAMENTO", "pista": "GABARITO", "papel": "outro"}
        assert s.anterior.preparar_requisicao(alterado, "com_exemplos") == r


def test_resumo_separa_erro_semantico_de_literalidade_e_cobertura(completos):
    rs = deepcopy(completos)
    props = {
        "U04:original": {"predicado": IX["U04:original"]["pista"], "papel": "expressao_sem_operacao"},
        "U02:original": {"predicado": "não sabemos se o autor nomeava uma oficina", "papel": "indeterminado"},
        "N06:original": {"predicado": "informa uma propriedade", "papel": "expressao_sem_operacao"}}
    for i, r in enumerate(rs):
        if r["id"] in props:
            rs[i] = medir(IX[r["id"]], r["repeticao"], proposta=props[r["id"]])
        rs[i]["afericao"] = {"conjunto": True}
    res = s.resumir(rs)
    u, literal, metrica = [res["familias"][i]["original"] for i in ("U04", "U02", "N06")]
    assert u["pista"] == [True, True] and u["papel_alinhado"] == [False, False]
    assert literal["papel_alinhado"] == [True, True] and literal["vinculo"] == [False, False]
    assert metrica["papel_alinhado"] == [True, True] and metrica["vinculo"] == [True, True] and metrica["pista"] == [False, False]
    assert all(res[k] is False for k in s.BASE)


@pytest.mark.parametrize("tipo", ["ausente", "duplicado", "ordem", "rep_bool", "host", "request", "flag", "nan", "contradicao"])
def test_replay_fecha_diante_de_adulteracao(completos, tipo):
    rs = deepcopy(completos)
    if tipo == "ausente": rs.pop()
    elif tipo == "duplicado": rs.append(rs[0])
    elif tipo == "ordem": rs.reverse()
    elif tipo == "rep_bool": rs[0]["repeticao"] = True
    elif tipo == "host": rs[0]["entrada_host"]["foco"]["inicio"] = 0.0
    elif tipo == "request": rs[0]["requisicao"]["messages"][-1]["content"] += "errado"
    elif tipo == "flag": rs[0]["autoriza_efeito"] = True
    elif tipo == "nan": rs[0]["duracao_consulta_s"] = float("nan")
    else: rs[0]["erro_consulta"] = "TimeoutError"
    assert s.resumir(rs)["tipo"] == "resumo_invalido"


def test_repeticao_truncada_nao_conta_como_acerto(completos):
    rs = deepcopy(completos)
    rs[0] = medir(CASOS[0], motivo="length")
    res = s.resumir(rs)
    assert res["consultas"] == 36
    assert res["familias"]["E04A"]["original"]["papel_alinhado"] == [False, True]


def test_cli_congela_variantes_e_preserva_artefato(monkeypatch, tmp_path, completos):
    saida = tmp_path / "ablacao.jsonl"
    indice = {(r["id"], r["repeticao"]): r for r in completos}
    chamadas = []
    def fake(c, *, modo, repeticao):
        meta = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert meta["casos_pre_consulta"] == CASOS and modo == "com_exemplos"
        chamadas.append((c["id"], repeticao))
        return deepcopy(indice[chamadas[-1]])
    monkeypatch.setattr(s, "medir_caso", fake)
    monkeypatch.setattr(s.anterior.etapas.coordenadas, "digest_modelo", lambda: "teste")
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    s.main()
    bruto = saida.read_bytes()
    assert len(bruto.splitlines()) == 38 and len(chamadas) == 36
    assert chamadas == [(c["id"], r) for c, r in s.sequencia(CASOS)]
    with pytest.raises(FileExistsError): s.main()
    assert saida.read_bytes() == bruto and len(chamadas) == 36
