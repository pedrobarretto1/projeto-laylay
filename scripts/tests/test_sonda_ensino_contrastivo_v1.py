from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_ensino_contrastivo_v1 as s


DADOS = s.carregar_painel()
CASOS = DADOS["avaliacao"]
MEDIR = s.medir_caso


def medir(c, modo="sem_exemplos", repeticao=1, *, proposta=None, motivo="stop"):
    p = proposta if proposta is not None else {"predicado": c["pista"], "papel": c["papel"]}
    return MEDIR(c, modo=modo, repeticao=repeticao, post=lambda *a, **k: SimpleNamespace(
        status_code=200, text=json.dumps({"done": True, "done_reason": motivo,
                                       "message": {"content": json.dumps(p)}})))


def registros():
    return [medir(c, m, rep) for c, m, rep in s.sequencia(CASOS)]


def test_baseline_exato_e_demonstracoes_nao_vazam_referencia_de_avaliacao():
    for c in CASOS:
        a, b = [s.preparar_requisicao(c, m) for m in s.MODOS]
        assert a == s.anterior.preparar_requisicao(s.caso_host(c), "predicado_host")
        assert b["messages"][0] == a["messages"][0] and b["messages"][-1] == a["messages"][-1]
        assert len(b["messages"]) == 18 and b["format"] == a["format"] and b["options"] == a["options"]
        assert {k: v for k, v in a.items() if k != "messages"} == {k: v for k, v in b.items() if k != "messages"}
        assert c["justificativa"] not in json.dumps(b, ensure_ascii=False)
        for entrada in b["messages"][1::2]:
            assert entrada["role"] == "user"
            assert set(json.loads(entrada["content"])) == {"fonte", "aspas_sintaticas", "foco"}
        for demo, resposta in zip(DADOS["demonstracoes"], b["messages"][2:-1:2]):
            assert resposta["role"] == "assistant"
            assert json.loads(resposta["content"]) == {k: demo[k] for k in ("predicado", "papel")}
        adulterado = {**c, "papel": "MUDOU", "pista": "VAZOU", "justificativa": "SEGREDO"}
        assert s.preparar_requisicao(adulterado, "com_exemplos") == b


def test_dados_distintos_e_demonstracoes_ancoradas_sem_promocao():
    focos = [{s.papel.preparar_entrada(s.caso_host(c))["foco"]["texto"] for c in DADOS[k]}
             for k in ("demonstracoes", "avaliacao")]
    assert focos[0].isdisjoint(focos[1])
    for c in DADOS["demonstracoes"]:
        v = s.anterior.materializar_vinculo(s.caso_host(c), s.papel.preparar_entrada(s.caso_host(c)),
                                           {k: c[k] for k in ("predicado", "papel")})
        assert v["vinculo_estrutural_valido"] and all(v[k] is False for k in s.BASE)


def test_hash_alterado_aborta_antes_de_consultar(monkeypatch, tmp_path):
    p = tmp_path / "dados.json"
    p.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(s, "DADOS", p)
    with pytest.raises(ValueError, match="congelada"):
        s.carregar_painel()


def test_incerteza_ancorada_nao_corrige_rotulo_errado():
    c = next(c for c in CASOS if c["id"] == "U01")
    p = {"predicado": c["pista"], "papel": "operacao_mencionada"}
    a = s.aferir_caso(c, medir(c, "com_exemplos", proposta=p))
    assert a["pista"] and a["vinculo"] and not a["papel_alinhado"] and not a["conjunto"]
    assert a["papel_proposto"] == "operacao_mencionada" and all(a[k] is False for k in s.BASE)


@pytest.mark.parametrize("tipo", ["vazio", "foco", "extra", "parafrase"])
def test_selecao_invalida_nao_ganha_autoridade_por_exemplo(tipo):
    c = CASOS[0]
    p = {"predicado": c["pista"], "papel": c["papel"]}
    if tipo == "vazio": p["predicado"] = ""
    elif tipo == "foco": p["predicado"] = s.papel.preparar_entrada(c)["foco"]["texto"]
    elif tipo == "extra": p["feito"] = True
    else: p["predicado"] = "isto nomeia uma obra"
    a = s.aferir_caso(c, medir(c, proposta=p))
    assert not a["vinculo"] and not a["conjunto"]
    assert all(a[k] is False for k in s.BASE)


@pytest.fixture(scope="module")
def completos():
    return registros()


@pytest.mark.parametrize("tipo", ["ausente", "duplicado", "ordem", "repeticao_bool", "host", "request", "flag", "nan", "contradicao"])
def test_replay_recusa_envelope_ou_conjunto_adulterado(completos, tipo):
    rs = deepcopy(completos)
    if tipo == "ausente": rs.pop()
    elif tipo == "duplicado": rs.append(rs[0])
    elif tipo == "ordem": rs[0], rs[1] = rs[1], rs[0]
    elif tipo == "repeticao_bool": rs[0]["repeticao"] = True
    elif tipo == "host": rs[0]["entrada_host"]["foco"]["inicio"] = 1.0
    elif tipo == "request": rs[0]["requisicao"]["messages"][0]["content"] += "muda"
    elif tipo == "flag": rs[0]["autoriza_efeito"] = True
    elif tipo == "nan": rs[0]["duracao_consulta_s"] = float("nan")
    else: rs[0]["erro_consulta"] = "TimeoutError"
    assert s.resumir(rs)["tipo"] == "resumo_invalido"


def test_resumo_reconta_brutos_e_nao_chama_empate_de_ganho(completos):
    rs = deepcopy(completos)
    for r in rs: r["afericao"] = {"conjunto": False}
    resumo = s.resumir(rs)
    for b in resumo["bracos"].values():
        assert b["papeis_validos_iguais_nas_duas"] == 24 and b["conjunto_nas_duas"] == 24
        assert all(r["conjunto"] == 24 and r["pares_papel"] == 6 for r in b["repeticoes"].values())
    assert not resumo["criterio_predefinido_atendido"]
    assert all(resumo[k] is False for k in s.BASE)


def test_truncamento_e_falsa_abstencao_permanecem_no_denominador(completos):
    rs = deepcopy(completos)
    for i, r in enumerate(rs):
        if r["id"] != CASOS[0]["id"] or r["modo"] != "com_exemplos": continue
        rs[i] = medir(CASOS[0], r["modo"], r["repeticao"],
            proposta={"predicado": CASOS[0]["pista"], "papel": "indeterminado"},
            motivo="stop" if r["repeticao"] == 1 else "length")
    b = s.resumir(rs)["bracos"]["com_exemplos"]
    assert b["conjunto_nas_duas"] == 23 and b["papeis_validos_iguais_nas_duas"] == 23
    assert b["repeticoes"]["1"]["falso_indeterminado"] == 1
    assert b["repeticoes"]["2"]["falso_indeterminado"] == 0
    assert b["repeticoes"]["2"]["casos"] == 24 and b["repeticoes"]["2"]["shape"] == 23


def test_criterio_exige_ganho_repetido_sem_sacrificar_classe_conclusiva(completos):
    rs = deepcopy(completos)
    ix = {c["id"]: c for c in CASOS}
    for i, r in enumerate(rs):
        if r["modo"] == "sem_exemplos" and r["id"].startswith("U"):
            c = ix[r["id"]]
            rs[i] = medir(c, r["modo"], r["repeticao"],
                proposta={"predicado": c["pista"], "papel": "operacao_mencionada"})
    resumo = s.resumir(rs)
    assert resumo["criterio_predefinido_atendido"]
    assert all(resumo[k] is False for k in s.BASE)
    for i, r in enumerate(rs):
        if r["modo"] == "com_exemplos" and r["id"] == "E01A" and r["repeticao"] == 2:
            rs[i] = medir(ix[r["id"]], r["modo"], 2,
                proposta={"predicado": ix[r["id"]]["pista"], "papel": "expressao_sem_operacao"})
    assert not s.resumir(rs)["criterio_predefinido_atendido"]


def test_cli_congela_antes_de_96_chamadas_e_nao_sobrescreve(monkeypatch, tmp_path, completos):
    saida = tmp_path / "coleta.jsonl"
    chamadas = []
    ix = {(r["id"], r["modo"], r["repeticao"]): r for r in completos}
    def fake(c, *, modo, repeticao):
        meta = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert meta["dados_pre_consulta"] == DADOS
        chamadas.append((c["id"], modo, repeticao))
        return deepcopy(ix[chamadas[-1]])
    monkeypatch.setattr(s, "medir_caso", fake)
    monkeypatch.setattr(s.etapas.coordenadas, "digest_modelo", lambda: "teste")
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    s.main()
    bruto = saida.read_bytes()
    assert len(bruto.splitlines()) == 98 and len(chamadas) == 96
    assert chamadas == [(c["id"], m, r) for c, m, r in s.sequencia(CASOS)]
    with pytest.raises(FileExistsError): s.main()
    assert saida.read_bytes() == bruto and len(chamadas) == 96
