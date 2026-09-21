from copy import deepcopy
import hashlib
import json

import pytest

from mente_laylay.neural import revisao_encoder as r
from mente_laylay.neural.curadoria_encoder import preparar_fila
from mente_laylay.neural.experiencias import BufferExperienciasNeurais
from mente_laylay.neural.supervisao_relacoes_v4 import FLAGS


def entrada(tmp_path):
    BufferExperienciasNeurais(tmp_path / "e.jsonl").registrar_resultado(
        texto="Abre o Editor", previsao={"intent": "FILE_READ"},
        resultado={"intent": "FILE_READ"}, executou=True, confirmado=True, origem="executor")
    fila, _ = preparar_fila(tmp_path / "e.jsonl", tmp_path / "r.jsonl")
    grupo = {"indices_fila": [1], "grupo": "abertura", "motivo": "Pedido explícito",
             "enquadramento": "supervisionado", **FLAGS,
             "fonte_v4": {"versao": 4, "texto_entrada": "Abre o Editor", **FLAGS, "relacoes": [],
                 "nos": [{"id": "a", "intent": "APP_OPEN", "action": "open", "ato": "pedido",
                     "trecho": {"inicio": 0, "fim": 13, "texto": "Abre o Editor"},
                     "ancora": {"inicio": 0, "fim": 4, "texto": "Abre"},
                     "alvos": [{"inicio": 7, "fim": 13, "texto": "Editor"}]}]}}
    return fila, {"origem_rotulo": "curadoria_ia", "grupos": [grupo]}


def test_receipt_divergente_nao_define_anotacao_nem_procedencia(tmp_path):
    fila, revisao = entrada(tmp_path)
    antes = deepcopy(fila)
    saida, resumo = r.aplicar_revisao(fila, revisao, {})
    assert fila == antes
    assert saida[0]["anotacao"]["nos"][0]["intent"] == "APP_OPEN"
    assert saida[0]["origem_texto"] == "desconhecida"
    assert saida[0]["particao"] is saida[0]["ancestrais"] is None
    assert saida[0]["revisao_encoder"] == "aguarda_revisao_humana"
    assert saida[0]["conhecido_no_desenvolvimento"] is True
    assert resumo["dados_prontos"] is resumo["particoes_formadas"] is False
    assert all(saida[0][k] is False for k in FLAGS)


def test_cruzamento_ast_nao_executa_roteiro_nem_certifica_origem(tmp_path):
    fila, revisao = entrada(tmp_path)
    script = tmp_path / "roteiro.py"
    script.write_text('raise RuntimeError("não executar")\nCOMANDOS = ["Abre o Editor"]\n', encoding="utf-8")
    exposicoes, hashes = r.cruzar_exposicao(fila, [script])
    assert exposicoes[fila[0]["texto"]][0]["linha"] == 2
    assert hashes[str(script.resolve())] == hashlib.sha256(script.read_bytes()).hexdigest()
    saida, resumo = r.aplicar_revisao(fila, revisao, exposicoes)
    assert resumo["textos_com_exposicao_literal"] == 1
    assert saida[0]["origem_evento_verificada"] is False


def test_correspondencia_literal_preserva_caixa(tmp_path):
    fila, _ = entrada(tmp_path)
    script = tmp_path / "roteiro.py"
    script.write_text('COMANDOS = ["abre o Editor"]', encoding="utf-8")
    exposicoes, _ = r.cruzar_exposicao(fila, [script])
    assert exposicoes[fila[0]["texto"]] == []  # Não implica ineditismo.


@pytest.mark.parametrize("literal", ['"""outra frase\nAbre o Editor\n"""', '"outra frase\\nAbre o Editor\\n"'])
def test_exposicao_em_constante_multilinha_sem_inventar_linha_fisica(tmp_path, literal):
    fila, _ = entrada(tmp_path)
    script = tmp_path / "roteiro.py"
    script.write_text('raise RuntimeError("não executar")\nCOMANDOS = ' + literal, encoding="utf-8")
    exposicoes, _ = r.cruzar_exposicao(fila, [script])
    assert exposicoes[fila[0]["texto"]] == [{"arquivo": str(script.resolve()),
        "linha_constante": 2, "linha_no_valor": 2, "correspondencia": "linha_literal_do_valor"}]


@pytest.mark.parametrize("alteracao", ["falta", "duplicado", "indice_bool", "autoridade", "humana", "texto", "rotulo_fora_perfil", "particao_previa"])
def test_revisao_inconsistente_falha_fechada(tmp_path, alteracao):
    fila, revisao = entrada(tmp_path)
    grupo = revisao["grupos"][0]
    if alteracao == "falta": grupo["indices_fila"] = []
    if alteracao == "duplicado": grupo["indices_fila"] = [1, 1]
    if alteracao == "indice_bool": grupo["indices_fila"] = [True]
    if alteracao == "autoridade": grupo["autoriza_execucao"] = True
    if alteracao == "humana": revisao["origem_rotulo"] = "revisao_humana"
    if alteracao == "texto": grupo["fonte_v4"]["texto_entrada"] = "outro"
    if alteracao == "rotulo_fora_perfil": grupo["enquadramento"] = "fora_perfil"
    if alteracao == "particao_previa": fila[0]["particao"] = "treino"
    with pytest.raises(ValueError): r.aplicar_revisao(fila, revisao, {})


def test_fora_perfil_nao_vira_rotulo_ausente(tmp_path):
    fila, revisao = entrada(tmp_path)
    grupo = revisao["grupos"][0]
    grupo.update(enquadramento="fora_perfil", fonte_v4=None, motivo="Dependência de contexto")
    saida, resumo = r.aplicar_revisao(fila, revisao, {})
    assert saida[0]["anotacao"] is None
    assert resumo["cobertura_anotada_ia"] == {}


def arquivos(tmp_path):
    fila, revisao = entrada(tmp_path)
    f, a = tmp_path / "fila.jsonl", tmp_path / "anotacao.json"
    f.write_text(json.dumps(fila[0]) + "\n", encoding="utf-8")
    revisao["fila_sha256"] = r._hash(f)
    a.write_text(json.dumps(revisao), encoding="utf-8")
    return f, a


def test_exportacao_hash_e_destino_exclusivo(tmp_path):
    f, a = arquivos(tmp_path)
    destino = tmp_path / "saida"
    resumo = r.executar(f, a, [], destino)
    assert resumo["fila_revisada_sha256"] == r._hash(destino / "fila_revisada.jsonl")
    with pytest.raises(FileExistsError): r.executar(f, a, [], destino)


def test_indices_nao_aplicam_em_outra_fila(tmp_path):
    f, a = arquivos(tmp_path)
    f.write_text(f.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="snapshot"):
        r.executar(f, a, [], tmp_path / "saida")
    assert not (tmp_path / "saida").exists()


def test_fonte_ausente_aborta_sem_saida(tmp_path):
    f, a = arquivos(tmp_path)
    with pytest.raises(FileNotFoundError): r.executar(f, a, [tmp_path / "nada.py"], tmp_path / "saida")
    assert not (tmp_path / "saida").exists()


def test_corrida_aborta_sem_saida(tmp_path, monkeypatch):
    f, a = arquivos(tmp_path)
    original = r.cruzar_exposicao
    def alterar(*args):
        resultado = original(*args)
        a.write_text("{}", encoding="utf-8")
        return resultado
    monkeypatch.setattr(r, "cruzar_exposicao", alterar)
    with pytest.raises(RuntimeError, match="mudou"): r.executar(f, a, [], tmp_path / "saida")
    assert not (tmp_path / "saida").exists()
