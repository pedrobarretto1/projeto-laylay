from pathlib import Path

import pytest

from mente_laylay.neural import curadoria_encoder as c
from mente_laylay.neural.experiencias import BufferExperienciasNeurais, RegistroRevisoesCorrecoesNeurais


def registrar(pasta, texto="Abre o Chrome"):
    return BufferExperienciasNeurais(pasta / "experiencias.jsonl").registrar_resultado(
        texto=texto, previsao={"intent": "APP_OPEN"}, resultado={"intent": "APP_OPEN"},
        executou=True, confirmado=True, origem="executor")


def test_receipt_real_agrupado_nao_vira_label(tmp_path):
    registrar(tmp_path); registrar(tmp_path)
    fila, r = c.preparar_fila(tmp_path / "experiencias.jsonl", tmp_path / "revisoes.jsonl")
    assert len(fila) == 1 and len(fila[0]["referencias"]) == 2
    assert fila[0]["anotacao"] is fila[0]["particao"] is fila[0]["ancestrais"] is None
    assert fila[0]["origem_texto"] == "desconhecida"
    assert fila[0]["treino_permitido"] is False
    assert "APP_OPEN" not in str(fila)
    assert r["registros_validos"] == 2 and r["fontes_sha256"]["revisoes"] is None


def test_correcao_aprovada_nao_fabrica_anotacao_encoder(tmp_path):
    e = BufferExperienciasNeurais(tmp_path / "experiencias.jsonl").registrar_correcao(
        texto_original="abra isso", intent_errada="FILE_READ", intent_correta="APP_OPEN",
        params_corretos={}, texto_correcao="queria outro", confirmada_por_execucao=True)
    RegistroRevisoesCorrecoesNeurais(tmp_path / "revisoes.jsonl").registrar_decisao(
        correcao_id=e["id"], decisao="aprovada")
    fila, r = c.preparar_fila(tmp_path / "experiencias.jsonl", tmp_path / "revisoes.jsonl")
    assert r["classificacao_ledger"]["aprovadas"] == 1
    assert fila[0]["referencias"][0]["decisao_ledger"] == "aprovada"
    assert fila[0]["anotacao"] is None and fila[0]["revisao_encoder"] == "pendente"


def test_texto_bruto_nao_perde_caixa_acentos(tmp_path):
    for t in ("Abre música", "abre música", "abre musica"):
        registrar(tmp_path, t)
    fila, _ = c.preparar_fila(tmp_path / "experiencias.jsonl", tmp_path / "r.jsonl")
    assert [f["texto"] for f in fila] == ["Abre música", "abre música", "abre musica"]


def test_linha_corrompida_nao_e_reparada(tmp_path):
    registrar(tmp_path)
    p = tmp_path / "experiencias.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write('\x00{"text": "não importar"}\n')
    antes = p.read_bytes()
    fila, r = c.preparar_fila(p, tmp_path / "r.jsonl")
    assert len(fila) == 1 and r["registros_invalidos_nao_recuperados"] == 1
    assert p.read_bytes() == antes


def test_corrida_de_fonte_aborta(tmp_path, monkeypatch):
    registrar(tmp_path)
    original = c.ler_jsonl_tolerante
    def mudar(p):
        r = original(p)
        if p.name == "experiencias.jsonl": registrar(tmp_path, "outra entrada")
        return r
    monkeypatch.setattr(c, "ler_jsonl_tolerante", mudar)
    with pytest.raises(RuntimeError, match="mudaram"):
        c.executar(tmp_path / "experiencias.jsonl", tmp_path / "r.jsonl", tmp_path / "saida")
    assert not (tmp_path / "saida").exists()


def test_saida_exclusiva_e_hash_conferem(tmp_path):
    registrar(tmp_path)
    d = tmp_path / "saida"
    r = c.executar(tmp_path / "experiencias.jsonl", tmp_path / "r.jsonl", d)
    assert c._hash(d / "fila.jsonl") == r["fila_sha256"]
    with pytest.raises(FileExistsError):
        c.executar(tmp_path / "experiencias.jsonl", tmp_path / "r.jsonl", d)


def test_fonte_ausente_nao_vira_corpus_vazio(tmp_path):
    with pytest.raises(FileNotFoundError):
        c.preparar_fila(tmp_path / "nada", tmp_path / "revisoes")
