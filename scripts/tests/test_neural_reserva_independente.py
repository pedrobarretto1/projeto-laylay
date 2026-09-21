from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from mente_laylay.especialistas.capacidades import intents_registradas
from mente_laylay.neural.cobertura import carregar_manifesto_variantes
from mente_laylay.neural import auditar_reserva_independente as auditor

RAIZ = Path(__file__).parents[1]
RESERVA = RAIZ / "mente_laylay/neural/datasets/reserva_relacional_independente_v1.json"
DADOS = json.loads(RESERVA.read_text(encoding="utf-8"))
MANIFESTO = carregar_manifesto_variantes(
    RAIZ / "mente_laylay/neural/datasets/catalogo_variantes_v0.json", intents_catalogadas=intents_registradas())
VARIANTES = {(v["intent"], v["action"]) for v in MANIFESTO["variants"]}


@pytest.mark.parametrize("caso", DADOS["casos"], ids=lambda c: c["id"])
def test_reserva_anotada_tem_spans_validos_sem_chamar_classificador(caso):
    dados = {**DADOS, "casos": [deepcopy(caso)]}
    antes = deepcopy(dados)
    auditor.validar_reserva(dados, VARIANTES)
    assert dados == antes
    assert dados["alinhamento_canonico_revisado"] is False


@pytest.mark.parametrize("campo", ["treino_permitido", "autoriza_execucao", "autoriza_promocao", "alinhamento_canonico_revisado"])
def test_reserva_nao_se_declara_treino_execucao_ou_alinhamento_real(campo):
    dados = deepcopy(DADOS)
    dados[campo] = True
    with pytest.raises(ValueError, match="isolada"):
        auditor.validar_reserva(dados, VARIANTES)


def test_destino_existente_aborta_antes_de_ler_reserva(tmp_path):
    with pytest.raises(FileExistsError):
        auditor.executar(raiz=tmp_path, reserva=tmp_path / "ausente", destino=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_reserva_congelada_antes_da_comparacao_e_sem_autorizar_por_green(tmp_path, monkeypatch):
    # Fonte mínima só para testar o fluxo de congelamento; o relatório real
    # cobre o inventário completo, não este corpus de teste.
    fonte = tmp_path / "corpus.jsonl"
    fonte.write_text('{"text":"texto de controle sem relacao"}\n', encoding="utf-8")
    origem = {str(fonte): {"sha256": hashlib.sha256(fonte.read_bytes()).hexdigest(), "registros": 1}}
    monkeypatch.setattr(auditor, "carregar_corpus", lambda _: ([{"text": "texto de controle sem relacao"}], origem))
    destino = tmp_path / "auditoria"
    original = auditor.auditar_leakage_dataset
    def comparar(corpus, novos):
        assert (destino / "protocolo.json").exists()
        assert (destino / "reserva_congelada.json").read_bytes() == RESERVA.read_bytes()
        return original(corpus, novos)  # medidor canônico real
    monkeypatch.setattr(auditor, "auditar_leakage_dataset", comparar)
    r = auditor.executar(raiz=RAIZ, reserva=RESERVA, destino=destino)
    assert r["auditoria_lexical"]["aprovado"]
    assert r["modelo_avaliado"] is r["treino_permitido"] is r["autoriza_promocao"] is False
    assert (destino / "auditoria.json").exists()


def test_corpus_incompleto_nao_e_silenciosamente_aprovado(tmp_path):
    with pytest.raises(ValueError, match="históricos obrigatórios ausentes"):
        auditor.carregar_corpus(tmp_path)


def test_duplicate_id_ou_span_inventado_reprova_reserva():
    dados = deepcopy(DADOS)
    dados["casos"].append(deepcopy(dados["casos"][0]))
    with pytest.raises(ValueError, match="id inválido"):
        auditor.validar_reserva(dados, VARIANTES)
    dados = deepcopy(DADOS)
    dados["casos"][0]["segmentos"][0]["acoes"][0]["alvos_solicitados"][0]["inicio"] += 1
    with pytest.raises(ValueError, match="span"):
        auditor.validar_reserva(dados, VARIANTES)
