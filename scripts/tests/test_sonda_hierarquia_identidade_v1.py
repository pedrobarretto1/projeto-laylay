from copy import deepcopy
import json
import sys
from types import SimpleNamespace

import pytest

from scripts.analises import sonda_hierarquia_identidade_v1 as s


CASOS = s.carregar_painel()
IX = {c["id"]: c for c in CASOS}


def medir(c, modo, rep=1, *, p=None):
    proposta = p if p is not None else {"predicado": c["pista"], "papel": c["papel"]}
    return s.medir_caso(c, modo=modo, repeticao=rep, post=lambda *a, **k: SimpleNamespace(
        status_code=200, text=json.dumps({"done": True, "done_reason": "stop",
                                       "message": {"content": json.dumps(proposta)}})))


def test_fatorial_preserva_fonte_offset_schema_sistema_e_respostas_demos():
    for c in CASOS:
        rs = [s.preparar_requisicao(c, m) for m in s.MODOS]
        assert rs[0] == s.anterior.preparar_requisicao(c, "com_exemplos")
        if c["foco_id"] == "c1":
            assert rs[1] == rs[0] and rs[3] == rs[2]
        for r in rs:
            assert r["messages"][0] == rs[0]["messages"][0]
            assert r["messages"][2:-1:2] == rs[0]["messages"][2:-1:2]
            assert {k: v for k, v in r.items() if k != "messages"} == {k: v for k, v in rs[0].items() if k != "messages"}
        for pos in range(1, len(rs[0]["messages"]), 2):
            a, b, h, hi = [json.loads(r["messages"][pos]["content"]) for r in rs]
            esperado = deepcopy(a)
            esperado["foco"]["id"] = "c1"
            assert b == esperado
            assert {k:v for k,v in h.items() if k != "hierarquia_sintatica_do_foco"} == a
            assert {k:v for k,v in hi.items() if k != "hierarquia_sintatica_do_foco"} == b
            for e in (h, hi):
                caminho = e["hierarquia_sintatica_do_foco"]
                assert caminho["ocorrencia"] == e["foco"]
                anterior = ""
                for regiao in caminho["regioes_externa_para_interna"]:
                    assert regiao["pai_id"] == anterior
                    assert e["fonte"]["texto"][regiao["inicio"]:regiao["fim"]] == regiao["texto"]
                    anterior = regiao["id"]


def test_ocorrencias_iguais_nao_sao_fundidas_por_rotulo_de_transporte():
    entradas = []
    for i in ("E05A", "E05B"):
        c = IX[i]
        e = s.anterior.papel.preparar_entrada(c)
        p = s.projetar_entrada(c, e, "hierarquia_id_uniforme")
        assert p["foco"]["id"] == "c1" and p["foco"]["inicio"] == e["foco"]["inicio"]
        caminho = p["hierarquia_sintatica_do_foco"]["regioes_externa_para_interna"]
        assert len(caminho) == 1 and caminho[0]["id"] == e["foco"]["regiao_aspas_id"]
        entradas.append(p)
    assert entradas[0]["foco"]["texto"] == entradas[1]["foco"]["texto"]
    assert entradas[0]["foco"]["inicio"] != entradas[1]["foco"]["inicio"]


@pytest.mark.parametrize("tipo", ["offset_tipo", "pai", "texto", "id"])
def test_projecao_recusa_host_adulterado(tipo):
    c = CASOS[0]
    e = s.anterior.papel.preparar_entrada(c)
    if tipo == "offset_tipo": e["foco"]["inicio"] = float(e["foco"]["inicio"])
    elif tipo == "pai": e["aspas_sintaticas"]["regioes_entre_aspas"][0]["pai_id"] = "q1"
    elif tipo == "texto": e["fonte"]["texto"] += "texto"
    else: e["foco"]["id"] = "c1"
    with pytest.raises(ValueError, match="adulterada"):
        s.projetar_entrada(c, e, "hierarquia")


def test_referencias_nao_entram_na_projecao_e_guarda_canonica_nao_muda():
    c = IX["U04"]
    for modo in s.MODOS:
        r = s.preparar_requisicao(c, modo)
        alterado = {**c, "pista": "GABARITO", "papel": "falso", "justificativa": "SEGREDO"}
        assert s.preparar_requisicao(alterado, modo) == r
        registro = medir(c, modo, p={"predicado": c["pista"], "papel": "expressao_sem_operacao"})
        antes = deepcopy(registro)
        a = s.aferir_caso(c, registro)
        assert registro == antes and a["vinculo"] and a["pista"] and not a["papel_alinhado"]
        assert all(a[k] is False for k in s.BASE)


@pytest.fixture(scope="module")
def completos():
    return [medir(c, modo, rep) for c, modo, rep in s.sequencia(CASOS)]


@pytest.mark.parametrize("tipo", ["ausente", "duplicado", "ordem", "request", "host", "flag", "nan", "contradicao", "rep_bool"])
def test_replay_e_ponte_nao_aceitam_alteracoes(completos, tipo):
    rs = deepcopy(completos)
    if tipo == "ausente": rs.pop()
    elif tipo == "duplicado": rs.append(rs[0])
    elif tipo == "ordem": rs.reverse()
    elif tipo == "request": rs[0]["requisicao"]["messages"][-1]["content"] += "!"
    elif tipo == "host": rs[0]["entrada_host"]["foco"]["id"] = "c1"
    elif tipo == "flag": rs[0]["autoriza_efeito"] = True
    elif tipo == "nan": rs[0]["duracao_consulta_s"] = float("nan")
    elif tipo == "rep_bool": rs[0]["repeticao"] = True
    else: rs[0]["erro_consulta"] = "TimeoutError"
    assert s.resumir(rs)["tipo"] == "resumo_invalido"


def test_resumo_reconta_sem_confiar_em_afericao_salva(completos):
    rs = deepcopy(completos)
    for r in rs: r["afericao"] = {"conjunto": False}
    resumo = s.resumir(rs)
    assert resumo["consultas"] == 80 and resumo["casos"] == 10
    for braco in resumo["bracos"].values():
        assert all(rep["conjunto"] == 10 for rep in braco.values())
    assert all(resumo[k] is False for k in s.BASE)


def test_cli_grava_protocolo_antes_das_consultas_sem_sobrescrever(monkeypatch, tmp_path, completos):
    saida = tmp_path / "hierarquia.jsonl"
    ix = {(r["id"], r["modo"], r["repeticao"]): r for r in completos}
    chamadas = []
    def fake(c, *, modo, repeticao):
        meta = json.loads(saida.read_text(encoding="utf-8").splitlines()[0])
        assert meta["casos_pre_consulta"] == CASOS
        chamadas.append((c["id"], modo, repeticao))
        return deepcopy(ix[chamadas[-1]])
    monkeypatch.setattr(s, "medir_caso", fake)
    monkeypatch.setattr(s.anterior.etapas.coordenadas, "digest_modelo", lambda: "teste")
    monkeypatch.setattr(sys, "argv", ["sonda", "--saida", str(saida)])
    s.main()
    antes = saida.read_bytes()
    assert len(antes.splitlines()) == 82 and len(chamadas) == 80
    assert chamadas == [(c["id"], m, rep) for c, m, rep in s.sequencia(CASOS)]
    with pytest.raises(FileExistsError): s.main()
    assert saida.read_bytes() == antes and len(chamadas) == 80
