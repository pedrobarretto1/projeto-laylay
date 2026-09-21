import json

import pytest

from mente_laylay.neural import curadoria_shadow_encoder as c
from mente_laylay.neural.shadow import RelatorioShadowNeural
from mente_laylay.neural.revisao_encoder import aplicar_revisao
from mente_laylay.neural.supervisao_relacoes_v4 import FLAGS


def fontes(tmp_path):
    anterior = tmp_path / "anterior.jsonl"
    anterior.write_text(json.dumps({"texto": "texto anterior"}) + "\n", encoding="utf-8")
    return tmp_path / "shadow_eventos.jsonl", anterior


def registrar(tmp_path, texto, divergente=True):
    return RelatorioShadowNeural(tmp_path).registrar_turno(
        texto=texto, previsao={"intent": "FILE_READ", "is_command": False},
        turno={"autoriza_execucao": divergente})


def test_coletor_real_nao_reconstroi_texto_nem_converte_previsao_em_gold(tmp_path):
    shadow, anterior = fontes(tmp_path)
    registrar(tmp_path, "  Abre   o Editor  ")
    registrar(tmp_path, "sem divergência", False)
    fila, resumo = c.preparar_fila(shadow, anterior)
    assert fila[0]["texto"] == "Abre o Editor"
    assert fila[0]["fidelidade_texto"] == "literal_do_log_nao_transcricao_bruta"
    assert fila[0]["anotacao"] is fila[0]["particao"] is None
    assert "FILE_READ" not in str(fila)
    assert resumo["eventos_sem_texto"] == 1
    assert all(fila[0][k] is False for k in FLAGS)


def test_repetidos_agrupam_referencias_sem_usar_hash_como_id_de_turno(tmp_path):
    shadow, anterior = fontes(tmp_path)
    registrar(tmp_path, "Abre o Editor"); registrar(tmp_path, "Abre o Editor")
    registrar(tmp_path, "abre o Editor"); registrar(tmp_path, "texto anterior")
    fila, resumo = c.preparar_fila(shadow, anterior)
    assert len(fila) == 2 and len(fila[0]["referencias"]) == 2
    assert fila[0]["referencias"][0]["texto_hash_declarado"] == fila[1]["referencias"][0]["texto_hash_declarado"]
    assert resumo["eventos_sobrepostos"] == resumo["textos_sobrepostos"] == 1


def test_truncamento_do_coletor_explicitado(tmp_path):
    shadow, anterior = fontes(tmp_path)
    registrar(tmp_path, "x" * 520)
    fila, _ = c.preparar_fila(shadow, anterior)
    assert len(fila[0]["texto"]) == 500
    assert fila[0]["referencias"][0]["texto_pode_estar_truncado"] is True


def test_corrupcao_nao_repara_fonte_e_indice_e_de_registro_valido(tmp_path):
    shadow, anterior = fontes(tmp_path)
    registrar(tmp_path, "primeira")
    with shadow.open("a", encoding="utf-8") as f: f.write("\x00{}\n")
    registrar(tmp_path, "segunda")
    antes = shadow.read_bytes()
    fila, resumo = c.preparar_fila(shadow, anterior)
    assert resumo["linhas_invalidas"] == 1
    assert fila[1]["referencias"][0]["indice_registro_valido"] == 2
    assert shadow.read_bytes() == antes


def test_tipo_desconhecido_nao_entra_como_texto_de_turno(tmp_path):
    shadow, anterior = fontes(tmp_path)
    shadow.write_text(json.dumps({"tipo": "outro", "texto": "não coletar"}), encoding="utf-8")
    fila, resumo = c.preparar_fila(shadow, anterior)
    assert not fila and resumo["eventos_tipo_desconhecido"] == 1


@pytest.mark.parametrize("falha", ["ausente", "corrompida", "vazia", "sem_texto"])
def test_base_de_sobreposicao_invalida_aborta(tmp_path, falha):
    shadow, anterior = fontes(tmp_path)
    registrar(tmp_path, "um comando")
    if falha == "ausente": anterior = tmp_path / "ausente"
    else: anterior.write_text({"corrompida": "{", "vazia": "", "sem_texto": "{}"}[falha], encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)): c.executar(shadow, anterior, tmp_path / "saida")
    assert not (tmp_path / "saida").exists()


def test_corrida_de_fonte_aborta_exportacao(tmp_path, monkeypatch):
    shadow, anterior = fontes(tmp_path)
    registrar(tmp_path, "um comando")
    ler = c.ler_jsonl_tolerante
    def mudar(p):
        resultado = ler(p)
        if p == shadow: registrar(tmp_path, "outro comando")
        return resultado
    monkeypatch.setattr(c, "ler_jsonl_tolerante", mudar)
    with pytest.raises(RuntimeError, match="mudou"): c.executar(shadow, anterior, tmp_path / "saida")
    assert not (tmp_path / "saida").exists()


def test_exportacao_preserva_artefato_e_alimenta_revisor_existente(tmp_path):
    shadow, anterior = fontes(tmp_path)
    registrar(tmp_path, "sem alvo")
    destino = tmp_path / "saida"
    resumo = c.executar(shadow, anterior, destino)
    assert c._hash(destino / "fila.jsonl") == resumo["fila_sha256"]
    fila, _ = c.ler_jsonl_tolerante(destino / "fila.jsonl")
    revisada, _ = aplicar_revisao(fila, {"origem_rotulo": "curadoria_ia", "grupos": [{
        "indices_fila": [1], "grupo": "contexto", "enquadramento": "fora_perfil",
        "motivo": "Contexto ausente", "fonte_v4": None, **FLAGS}]}, {})
    assert revisada[0]["fidelidade_texto"] == fila[0]["fidelidade_texto"]
    assert revisada[0]["origem_texto"] == "desconhecida"
    with pytest.raises(FileExistsError): c.executar(shadow, anterior, destino)
