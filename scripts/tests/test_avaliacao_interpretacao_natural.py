"""O instrumento não pode confundir formato, significado e admissão."""
from copy import deepcopy
import json

import pytest

from scripts.analises.avaliacao_interpretacao_natural import (
    avaliar_atos, avaliar_comandos, carregar_corpus, preparar_mensagens,
    validar_indicios_pos,
)


def test_gold_familia_e_metadados_nunca_entram_no_prompt():
    caso = {"texto": "abre a calculadora", "contexto": "app",
            "esperados": [{"intent": "MARCADOR_GOLD"}], "familia": "SEGREDO",
            "atos_esperados": [{"tipo": "GABARITO"}]}
    antes = deepcopy(caso)
    mensagens = preparar_mensagens(caso["texto"], {"referencia": "Calculadora"})
    serializado = json.dumps(mensagens, ensure_ascii=False)
    assert all(s not in serializado for s in ("MARCADOR_GOLD", "SEGREDO", "GABARITO"))
    assert mensagens[-1] == {"role": "user", "content": caso["texto"]}
    assert caso == antes


def test_avaliador_preserva_ordem_multiplicidade_e_parametros():
    a = {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 40}}
    b = {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}
    assert avaliar_comandos([a, b], [a, b])["campos_avaliados_corretos"]
    assert not avaliar_comandos([a, b], [b, a])["campos_avaliados_corretos"]
    assert not avaliar_comandos([a, a], [a])["campos_avaliados_corretos"]
    assert not avaliar_comandos([a], [{**a, "params": {"acao": "up", "nivel_volume": 40}}])["campos_avaliados_corretos"]
    assert avaliar_comandos([], [a])["extras"] == 1


def test_tipo_numerico_nao_aceita_booleano_como_um():
    gold = [{"intent": "VOLUME", "params": {"nivel_volume": 1}}]
    resultado = avaliar_comandos(gold, [{"intent": "VOLUME", "params": {"nivel_volume": True}}])
    assert not resultado["campos_avaliados_corretos"]


def test_ato_alvo_operacao_e_dependencia_sao_medidos_separadamente():
    gold = [{"tipo": "pedido_acao", "interpretacao": {
        "operacao": "abrir", "alvo": "Calculadora", "dependencias": []}}]
    observado = [{"tipo": "relato", "interpretacao": {
        "operacao": "abrir", "alvo": "Notepad", "dependencias": [0]}}]
    resultado = avaliar_atos(gold, observado)
    assert resultado["por_campo"]["interpretacao.operacao"] == {"acertos": 1, "avaliados": 1}
    for campo in ("tipo", "interpretacao.alvo", "interpretacao.dependencias"):
        assert resultado["por_campo"][campo] == {"acertos": 0, "avaliados": 1}
    assert resultado["autoriza_execucao"] is resultado["comprova_efeito"] is False


def test_ausencia_de_leitura_nao_parece_acerto_semantico():
    resultado = avaliar_atos([{"tipo": "pedido_acao"}], [])
    assert resultado["ausentes"] == 1
    assert not resultado["campos_avaliados_corretos"]


def test_indicios_pos_exigem_literal_offsets_e_metadados():
    pacote = {"texto": "abre luz", "modelo": "pt_core_news_sm", "versao_modelo": "3.8.0",
        "versao_spacy": "3.8.0", "pipeline": ["parser"], "segundos": 0.02,
        "tokens": [{"texto": "abre", "inicio": 0, "fim": 4,
                    "lemma": "abrir", "pos": "VERB", "dep": "ROOT", "cabeca": 0}]}
    assert validar_indicios_pos("abre luz", pacote) == pacote
    adulterado = deepcopy(pacote)
    adulterado["tokens"][0]["inicio"] = 1
    with pytest.raises(ValueError):
        validar_indicios_pos("abre luz", adulterado)
    with pytest.raises(ValueError):
        validar_indicios_pos("abre outra", pacote)
    del adulterado["versao_modelo"]
    with pytest.raises(ValueError):
        validar_indicios_pos("abre luz", adulterado)


def test_corpus_e_dev_anotacao_ia_nao_reserva_humana(tmp_path):
    caminho = tmp_path / "casos.json"
    corpo = {"versao": 1, "finalidade": "desenvolvimento",
        "anotacao": "IA_nao_revisada_por_humano", "casos": [{"id": "a", "familia": "f",
        "texto": "abre a calculadora", "contexto": "", "esperados": [], "atos_esperados": []}]}
    caminho.write_text(json.dumps(corpo), encoding="utf-8")
    assert carregar_corpus(caminho)["casos"][0]["id"] == "a"
    corpo["casos"].append(deepcopy(corpo["casos"][0]))
    caminho.write_text(json.dumps(corpo), encoding="utf-8")
    with pytest.raises(ValueError, match="identidade"):
        carregar_corpus(caminho)


def test_gold_nao_pode_introduzir_contexto_arbitrario(tmp_path):
    caminho = tmp_path / "casos.json"
    caminho.write_text(json.dumps({"versao": 1, "finalidade": "desenvolvimento",
        "anotacao": "IA_nao_revisada_por_humano", "casos": [{"id": "a", "familia": "f",
        "texto": "oi", "contexto": "copiar_gold_para_prompt", "esperados": [], "atos_esperados": []}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="contexto"):
        carregar_corpus(caminho)


def test_porta_tipificada_entrega_json_validado_sem_marcador():
    from scripts.analises.sonda_ordem_interpretacao import decodificar_resultado_tipificado
    from mente_laylay.integracao.contrato_saida_estruturada import ContratoSaidaEstruturada
    contrato = ContratoSaidaEstruturada("teste", "[TESTE]", {}, lambda dados: None)
    assert decodificar_resultado_tipificado(contrato, '{"a": 1}') == {"a": 1}
    with pytest.raises(ValueError):
        decodificar_resultado_tipificado(contrato, 'prosa {"a": 1}')


def test_alvo_literal_url_nao_e_normalizado_como_nome_de_app():
    gold = [{"intent": "OPEN_URL", "params": {"url": "https://example.test/A"}}]
    mudado = [{"intent": "OPEN_URL", "params": {"url": "https://example.test/a"}}]
    assert not avaliar_comandos(gold, mudado)["campos_avaliados_corretos"]
