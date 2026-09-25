from copy import deepcopy
import json

import pytest

from mente_laylay.neural import revalidar_perfil_v4 as r
from mente_laylay.neural.expandir_relacoes_v4 import carregar_base
from mente_laylay.neural.comparar_ocorrencias_v4 import carregar_perfil


@pytest.fixture(scope="module")
def perfil():
    return r.carregar_perfil_revalidado(reprojetar=True)


def caso():
    return json.loads((r.FONTE / "lote.json").read_text(encoding="utf-8"))["casos"][0]


def test_revalidacao_real_preserva_casos_dobras_e_flags(perfil):
    casos, dobras, relatorio = perfil
    assert len(casos) == relatorio["casos_unicos"] == 1176
    assert relatorio["dobras_identicas"] and len(dobras) >= 3
    assert [l["casos"] for l in relatorio["lotes"]] == [672, 1176]
    assert [l["tokens"] for l in relatorio["lotes"]] == [10752, 22320]
    assert all(relatorio[k] is False for k in r.FLAGS)
    assert relatorio["classificador_reavaliado"] is False
    assert relatorio["runtime_validado"] is False
    assert relatorio["compatibilidade_no_corpus"] is False
    assert relatorio["supervisao_literal_preservada"] is True
    assert [l["casos_alterados"] for l in relatorio["lotes"]] == [160, 160]
    assert [l["segmentacoes_alteradas"] for l in relatorio["lotes"]] == [48, 48]


def test_reprojecao_v2_preserva_evidencia_v1_e_explica_novas_recusas(perfil):
    relatorio = perfil[2]
    assert r.HASH_MODALIDADE_REPROJECAO_V1 == (
        "403781e0c8171d6a355c9a9a0a2db6b2d3dab821566f2e64402a124212a4b8b4"
    )
    assert r.SHA_DIVERGENCIAS_REPROJECAO_V1 == (
        "be76d3f3b31429191dd14695a3af01cf2d7fe30a59ae582a5dc98ca97158b312"
    )

    ids = {item["id"] for item in relatorio["lotes"][1]["divergencias"]}
    esperados = {
        f"rel_v4_necessidade_{dominio}_e{entidade}_t{topologia}_q{aspas}_recusa"
        for dominio in ("apps", "arquivos")
        for entidade in (0, 1)
        for topologia in (0, 1)
        for aspas in (0, 1)
    }
    assert len(esperados) == 16
    assert esperados <= ids


def test_replay_estrito_nao_declara_equivalencia_apos_mudanca_real():
    with pytest.raises(ValueError, match="sem revisão"):
        r.carregar_perfil_revalidado()


def test_reprojecao_preserva_gold_e_nao_muta_historico():
    cs = json.loads((r.FONTE / "lote.json").read_text(encoding="utf-8"))["casos"]
    c = next(c for c in cs if c["id"] == "rel_v4_necessidade_apps_e0_t0_q0_recusa_pedido")
    antes = deepcopy(c)
    novos, relatorio = r.reprojetar_casos([c])
    assert c == antes
    assert novos[0]["fonte"] == c["fonte"]
    assert len(novos[0]["alinhado"]["entrada"]["segmentos"]) == 2
    assert [n["ato"] for n in novos[0]["alinhado"]["supervisao"]["nos"]] == ["recusa", "pedido"]
    assert relatorio["alinhamentos_identicos"] is False
    assert all(novos[0]["alinhado"][k] is False for k in r.FLAGS)


@pytest.mark.parametrize("alteracao", ["ato", "alvo", "ancora", "relacao", "autoridade", "referencia"])
def test_reprojecao_nao_apaga_divergencia_de_gold_ou_integridade(alteracao):
    cs = json.loads((r.FONTE / "lote.json").read_text(encoding="utf-8"))["casos"]
    c = deepcopy(next(c for c in cs if c["id"] == "rel_v4_direto_apps_e0_t0_q0_pedido_recusa"))
    a = c["alinhado"]
    if alteracao == "ato":
        a["supervisao"]["nos"][0]["ato"] = "relato"
    elif alteracao == "alvo":
        a["supervisao"]["nos"][0]["alvos_solicitados"][0]["texto"] = "outro"
    elif alteracao == "ancora":
        a["supervisao"]["nos"][0]["ancora"]["inicio"] += 1
    elif alteracao == "relacao":
        a["supervisao"]["relacoes"] = []
    elif alteracao == "autoridade":
        a["autoriza_execucao"] = True
    else:
        a["referencia"]["sha256"] = "adulterado"
    with pytest.raises(ValueError):
        r.reprojetar_casos([c])


def test_compatibilidade_nao_modifica_guarda_historica(perfil):
    assert perfil[2]["guardas_historicas_alteradas"] is False
    with pytest.raises(ValueError, match="dependência"):
        carregar_base()
    with pytest.raises(ValueError, match="dependência"):
        carregar_perfil()


def test_delta_nao_revisado_aborta_mesmo_com_gold_identico(tmp_path, monkeypatch):
    original = r.reprojetar_casos

    def delta_novo(casos):
        novos, relatorio = original(casos)
        relatorio["divergencias_sha256"] = "mudanca_na_leitura_nao_revisada"
        return novos, relatorio

    monkeypatch.setattr(r, "reprojetar_casos", delta_novo)
    with pytest.raises(ValueError, match="fora da reprojeção revisada"):
        r.executar(tmp_path / "saida.json", reprojetar=True)
    assert not (tmp_path / "saida.json").exists()


@pytest.mark.parametrize("nome", list(r.REPROJECAO_REVISADA))
def test_reprojecao_nao_aceita_outra_revisao_de_dependencia(nome):
    antigo, _ = r.REPROJECAO_REVISADA[nome]
    with pytest.raises(ValueError, match="sem revisão"):
        r.conferir_dependencias(
            {nome: antigo}, {str((r.BASE / nome).resolve()): "mudanca_futura"}, reprojetar=True,
        )


@pytest.mark.parametrize("problema", ["duplicado", "reserva"])
def test_reprojecao_mantem_isolamento_e_identidades(problema):
    c = caso()
    if problema == "reserva":
        c["particao"] = "reserva"
    with pytest.raises(ValueError, match="duplicadas|desenvolvimento"):
        r.reprojetar_casos([c, deepcopy(c)] if problema == "duplicado" else [c])


def test_publicacao_explicita_nao_certifica_modelo_nem_sobrescreve(tmp_path):
    destino = tmp_path / "reprojecao.json"
    resultado = r.executar(destino, reprojetar=True)
    assert json.loads(destino.read_text(encoding="utf-8")) == resultado
    assert resultado["perfil"] == "reprojecao_literal_v4_20260921_recusa_declarativa_v2"
    assert resultado["compatibilidade_no_corpus"] is False
    assert all(resultado[k] is False for k in r.FLAGS)
    with pytest.raises(FileExistsError):
        r.executar(destino, reprojetar=True)


@pytest.mark.parametrize("campo", ["entrada", "supervisao", "referencia", "proveniencia"])
def test_diferenca_no_alinhamento_nao_se_esconde_em_labels_iguais(campo):
    c = caso()
    c["alinhado"][campo] = {}
    with pytest.raises(ValueError, match="alinhamento divergiu"):
        r.conferir_casos([c])


@pytest.mark.parametrize("campo", list(r.FLAGS))
def test_alinhamento_nao_pode_receber_autoridade(campo):
    c = caso()
    c["alinhado"][campo] = True
    with pytest.raises(ValueError):
        r.conferir_casos([c])


def test_reserva_nao_e_aberta_pela_revalidacao():
    c = caso()
    c["particao"] = "reserva"
    with pytest.raises(ValueError, match="desenvolvimento"):
        r.conferir_casos([c])


def test_ids_duplicados_nao_inflam_cobertura():
    c = caso()
    with pytest.raises(ValueError, match="duplicadas"):
        r.conferir_casos([c, deepcopy(c)])


def test_caso_original_nao_e_mutado():
    c = caso()
    antes = deepcopy(c)
    assert r.conferir_casos([c])["alinhamentos_identicos"]
    assert c == antes


def test_fonte_alterada_aborta_antes_de_comparar(tmp_path, monkeypatch):
    fonte = tmp_path / "fonte"
    fonte.mkdir()
    (fonte / "protocolo.json").write_bytes((r.FONTE / "protocolo.json").read_bytes())
    (fonte / "lote.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(r, "FONTE", fonte)
    with pytest.raises(ValueError, match="lote histórico mudou"):
        r.executar(tmp_path / "saida.json", reprojetar=True)
    assert not (tmp_path / "saida.json").exists()


def test_fonte_mudando_durante_comparacao_aborta(tmp_path, monkeypatch):
    original = r._hash
    contagem = {}
    def hash_variavel(p):
        chave = str(p)
        contagem[chave] = contagem.get(chave, 0) + 1
        if p == r.FONTE / "lote.json" and contagem[chave] > 1:
            return "fonte_mudou"
        return original(p)
    monkeypatch.setattr(r, "_hash", hash_variavel)
    with pytest.raises(RuntimeError, match="fontes mudaram"):
        r.executar(tmp_path / "saida.json", reprojetar=True)
    assert not (tmp_path / "saida.json").exists()


def test_relatorio_anterior_nao_e_sobrescrito(tmp_path):
    destino = tmp_path / "resultado.json"
    destino.write_text("preservar", encoding="utf-8")
    with pytest.raises(FileExistsError):
        r.executar(destino)
    assert destino.read_text(encoding="utf-8") == "preservar"


@pytest.mark.parametrize("nome, antigo, atual", [
    (r.NORMALIZADOR_REVISADO, r.HASHES_REVISADOS[0], "mudanca_futura"),
    (r.NORMALIZADOR_REVISADO, "outra_base", r.HASHES_REVISADOS[1]),
    ("mente_laylay/cognicao/modalidade_turno.py", *r.HASHES_REVISADOS),
])
def test_mudanca_nao_revisada_nao_recebe_compatibilidade(nome, antigo, atual):
    with pytest.raises(ValueError, match="sem revisão"):
        r.conferir_dependencias({nome: antigo}, {str((r.BASE / nome).resolve()): atual})
