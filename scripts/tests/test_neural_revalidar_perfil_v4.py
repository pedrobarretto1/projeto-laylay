from copy import deepcopy
import json

import pytest

from mente_laylay.neural import revalidar_perfil_v4 as r
from mente_laylay.neural.expandir_relacoes_v4 import carregar_base


@pytest.fixture(scope="module")
def perfil():
    return r.carregar_perfil_revalidado()


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


def test_compatibilidade_nao_modifica_guarda_historica(perfil):
    assert perfil[2]["guardas_historicas_alteradas"] is False
    with pytest.raises(ValueError, match="dependência"):
        carregar_base()


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
        r.executar(tmp_path / "saida.json")
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
        r.executar(tmp_path / "saida.json")
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
