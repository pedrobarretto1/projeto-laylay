"""Validação de corpus sintético não equivale a acerto do modelo real."""
from collections import Counter
from copy import deepcopy
import hashlib
import json

import pytest

from mente_laylay.neural.preparar_contrastes_piloto import LINHAGEM, executar, gerar_lote
from mente_laylay.neural.protocolo_ajuste_supervisionado import (
    _rotulos_brutos, auditar_corpus, preparar_particao, validar_caso,
)
from mente_laylay.neural.supervisao_relacoes_v4 import FLAGS


def test_cobertura_com_spans_e_projecao_canonicos_sem_inferir_gold():
    casos = gerar_lote()
    assert len(casos) == 33
    assert len({c["texto"] for c in casos}) == 33
    classes = Counter()
    for c in casos:
        validar_caso(c)
        if c["fonte_v4"] is None:
            continue
        n = c["fonte_v4"]["nos"][0]
        rotulo = f"{n['intent']}|{n['action']}|{n['ato']}"
        classes[rotulo] += 1
        assert Counter(_rotulos_brutos(c["fonte_v4"]))[rotulo] == 1
        assert set(_rotulos_brutos(c["fonte_v4"])) == {"ausente", rotulo}
    assert classes == Counter({f"{i}|{a}|{ato}": 3
                              for i, a in [("APP_OPEN", "open"), ("MUSIC_SEARCH", "search"), ("FILE_READ", "read")]
                              for ato in ("pedido", "recusa", "relato")})


def test_negacao_no_nome_nao_muda_o_ato_anotado():
    casos = [c for c in gerar_lote() if "nome_negado" in c["grupo"]]
    assert len(casos) == 9
    for c in casos:
        n = c["fonte_v4"]["nos"][0]
        assert n["alvos"][0]["texto"].casefold().startswith("não ")
        assert any(r.endswith("|" + n["ato"]) for r in _rotulos_brutos(c["fonte_v4"]))


def test_fora_perfil_nao_vira_negativo_ausente_nem_alvo_fabricado():
    fora = [c for c in gerar_lote() if c["enquadramento"] == "fora_perfil"]
    assert len(fora) == 6
    assert all(c["fonte_v4"] is None and c["motivo_fora_perfil"] for c in fora)


def test_lote_conhecido_preserva_origem_linhagem_e_bloqueia_fit():
    casos = gerar_lote()
    for c in casos:
        assert c["origem_texto"] == "sintetico" and c["origem_rotulo"] == "curadoria_ia"
        assert c["conhecido_no_desenvolvimento"] is True
        assert LINHAGEM in c["ancestrais"]
        assert c["particao"] == "desenvolvimento"
        assert all(c[k] is False for k in FLAGS)
    r = auditar_corpus(casos)
    assert r["manifesto_valido"] is True
    assert r["dados_prontos_para_preparacao"] is False
    with pytest.raises(ValueError, match="corpus não pronto"):
        preparar_particao(casos, "treino")


def test_parentesco_impede_dividir_contrastes_em_avaliacoes_independentes():
    casos = gerar_lote()
    casos[0]["particao"] = "treino"
    casos[3]["particao"] = "selecao"
    r = auditar_corpus(casos)
    assert "parentesco_entre_particoes" in r["motivos"]
    assert "exposicao_anterior:selecao" in r["motivos"]


def test_parentesco_historico_reusa_identidade_do_importador_v4():
    from mente_laylay.neural.protocolo_ajuste_supervisionado import importar_desenvolvimento_v4

    casos = gerar_lote()
    # Fixture estrutural: não afirma executar nem revalidar o corpus antigo.
    antigo = importar_desenvolvimento_v4([{
        "id": "historico_fixture", "grupo_validacao": "antigo",
        "grupo_construcao": "vontade", "fonte": deepcopy(casos[0]["fonte_v4"]),
    }])[0]
    antigo["particao"] = "treino"
    r = auditar_corpus([*casos, antigo])
    assert "parentesco_entre_particoes" in r["motivos"]
    assert len(r["parentescos_cruzados"]) == 1
    assert len(r["parentescos_cruzados"][0]["ids"]) == 34


@pytest.mark.parametrize("flag", FLAGS)
def test_anotacao_nao_pode_conceder_autoridade(flag):
    c = gerar_lote()[0]
    c["fonte_v4"][flag] = True
    with pytest.raises(ValueError, match="isolada"):
        validar_caso(c)


def test_alvo_adulterado_e_rejeitado_pelo_validador_real():
    c = deepcopy(gerar_lote()[0])
    c["fonte_v4"]["nos"][0]["alvos"][0]["texto"] = "outro aplicativo"
    with pytest.raises(ValueError, match="intervalo"):
        validar_caso(c)


def test_exportacao_reprodutivel_exclusiva_e_sem_arquivos_de_treino(tmp_path):
    destino = tmp_path / "lote"
    r = executar(destino)
    payload = (destino / "corpus.jsonl").read_bytes()
    assert hashlib.sha256(payload).hexdigest() == r["corpus_sha256"]
    assert [json.loads(l) for l in payload.splitlines()] == gerar_lote()
    assert json.loads((destino / "resumo.json").read_text(encoding="utf-8")) == r
    assert {p.name for p in destino.iterdir()} == {"corpus.jsonl", "resumo.json"}
    with pytest.raises(FileExistsError, match="preservar"):
        executar(destino)
    assert (destino / "corpus.jsonl").read_bytes() == payload
    executar(tmp_path / "repeticao")
    assert (tmp_path / "repeticao" / "corpus.jsonl").read_bytes() == payload
