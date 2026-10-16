"""Contratos do runner diagnóstico, sem chamar modelo/executor externo."""
import json
from pathlib import Path

import pytest

from scripts.analises.runner_diagnostico_laylay import (
    carregar_entradas, pedido_permitido, DiarioDiagnostico, gerar_resumo, sintetizar_entrada, comparar_coletas,
)


@pytest.mark.parametrize("documento", [[], [""], [1], [{"texto": "oi", "id": ""}],
    [{"texto": "oi", "permitidos": [{"action": "*"}]}],
    [{"texto": "oi", "codigo": "executar()"}],
    [{"texto": "oi", "id": "x"}, {"texto": "outra", "id": "x"}]])
def test_formato_invalido_recusa_sem_iniciar_runtime(tmp_path, documento):
    caminho = tmp_path / "entradas.json"
    caminho.write_text(json.dumps(documento), encoding="utf-8")
    with pytest.raises(ValueError):
        carregar_entradas(caminho)


def test_entradas_simples_recebem_identidade_e_nao_recebem_permissao(tmp_path):
    caminho = tmp_path / "entradas.json"
    caminho.write_text('["oi", "coloca ela à esquerda"]', encoding="utf-8")
    entradas = carregar_entradas(caminho)
    assert entradas[0]["id"] == "entrada-001"
    assert entradas[1]["texto"] == "coloca ela à esquerda"
    assert all(e["permitidos"] == [] for e in entradas)


def test_continuacao_apos_silencio_recusada_antes_de_qualquer_execucao(tmp_path):
    from scripts.analises.runner_diagnostico_laylay import executar_coleta
    with pytest.raises(ValueError, match="sem efeitos"):
        executar_coleta(tmp_path / "inexistente.json", tmp_path, "executar", 1,
                        continuar_sem_resposta=True)


def test_gold_nao_autoriza_efeito_e_planejamento_fecha_mesmo_com_permissao():
    pedido = {"intent": "APP_OPEN", "params": {"nome_app": "Calculadora"}}
    entrada = {"permitidos": [], "expectativa": {"intents_all": ["APP_OPEN"]}}
    assert not pedido_permitido(pedido, entrada, "executar")
    entrada["permitidos"] = [pedido]
    assert not pedido_permitido(pedido, entrada, "planejar")
    assert pedido_permitido(pedido, entrada, "executar")
    assert not pedido_permitido({"intent": "APP_OPEN", "params": {"nome_app": "Notepad"}}, entrada, "executar")
    assert not pedido_permitido({"intent": "APP_OPEN", "params": {"nome_app": "Calculadora", "target": "pc_b"}}, entrada, "executar")


def test_journal_fotografa_dados_e_preserva_ordem(tmp_path):
    diario = DiarioDiagnostico(tmp_path / "eventos.jsonl")
    diario.indice = 1
    params = {"nivel": 40}
    diario.registrar("pedido", params=params)
    params["nivel"] = 90
    diario.registrar("fim")
    linhas = [json.loads(l) for l in diario.caminho.read_text(encoding="utf-8").splitlines()]
    assert linhas[0]["params"]["nivel"] == 40
    assert [l["sequencia"] for l in linhas] == [1, 2]


def test_resumo_parcial_nao_inventa_receipt_ou_sucesso(tmp_path):
    diario = DiarioDiagnostico(tmp_path / "eventos.jsonl")
    diario.registrar("entrada", texto="abre o app")
    resumo = gerar_resumo(tmp_path, "timeout", 124, {"fontes_estaveis": True})
    assert not resumo["coleta_concluida"] and resumo["receipts_aceitos"] == 0
    assert resumo["ultima_fronteira_observada"]["tipo"] == "entrada"
    assert (tmp_path / "resumo.md").exists()


def test_receipt_recusado_e_log_nao_sao_efeito_confirmado(tmp_path):
    diario = DiarioDiagnostico(tmp_path / "eventos.jsonl")
    receipt = {"executou": True, "confirmado": True}
    diario.registrar("executor_admissao_runner", permitido=True, pedido={})
    diario.registrar("receipt", aceito=False, receipt=receipt)
    diario.registrar("receipt", aceito=True, receipt={"executou": True, "confirmado": None})
    resumo = gerar_resumo(tmp_path, "finalizado", 0, {})
    assert resumo["receipts_aceitos"] == 1
    assert resumo["efeitos_confirmados_por_executor"] == 0
    assert not resumo["coleta_concluida"]  # ausência de relatório concluído


def test_publicacao_final_incerta_revoga_contagem_anterior_de_sucesso(tmp_path):
    diario = DiarioDiagnostico(tmp_path / "eventos.jsonl")
    diario.registrar("receipt", aceito=True, receipt={"id_solicitacao": "r1", "executou": True, "confirmado": True})
    diario.registrar("receipt", aceito=True, receipt={"id_solicitacao": "r1", "executou": True, "confirmado": None})
    resumo = gerar_resumo(tmp_path, "finalizado", 0, {})
    assert resumo["receipts_aceitos"] == 2 and resumo["solicitacoes_com_receipt"] == 1
    assert resumo["efeitos_confirmados_por_executor"] == 0


def test_publicacao_tardia_conserva_entrada_capturada_pelo_observador(tmp_path):
    diario = DiarioDiagnostico(tmp_path / "eventos.jsonl")
    diario.indice = 2
    diario.registrar("receipt", entrada=1, aceito=True, receipt={})
    assert diario.eventos[-1]["entrada"] == 1


def test_primeiro_alerta_preserva_cadeia_e_nao_declara_raiz():
    entrada = {"eventos": [
        {"sequencia": 1, "tipo": "modelo_resultado", "sucesso": False},
        {"sequencia": 2, "tipo": "executor_admissao_runner", "permitido": False}],
        "contexto_antes": {"ultimo_app_janela": ""},
        "contexto_depois": {"ultimo_app_janela": "Calculadora"}}
    diagnostico = sintetizar_entrada(entrada)
    assert diagnostico["primeiro_alerta_observado"]["motivo"] == "geracao_sem_sucesso"
    assert "ultimo_app_janela" in diagnostico["campos_contextuais_alterados"]
    assert diagnostico["raiz_causal"].startswith("não inferida")


def test_bloqueio_planejado_sem_comando_nao_e_alerta_operacional():
    diagnostico = sintetizar_entrada({"eventos": [
        {"tipo": "dispatch_bloqueado_runner", "sequencia": 1, "quantidade_comandos": 0}]})
    assert diagnostico["primeiro_alerta_observado"] is None


def test_falha_de_journal_nao_altera_receipt_ja_publicado(tmp_path, monkeypatch):
    diario = DiarioDiagnostico(tmp_path / "eventos.jsonl")
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: (_ for _ in ()).throw(PermissionError()))
    assert diario.registrar("receipt", aceito=True, receipt={"id_solicitacao": "r1"}) is False
    assert diario.eventos[-1]["aceito"] is True and diario.falhas


def test_erro_de_serializacao_e_diagnostico_nao_excecao_no_executor(tmp_path):
    diario = DiarioDiagnostico(tmp_path / "eventos.jsonl")
    circular = []
    circular.append(circular)
    assert diario.registrar("receipt", receipt=circular) is False
    assert diario.falhas and diario.eventos[-1]["tipo"] == "erro_serializacao_diagnostica"


def test_comparacao_nao_promove_condicoes_diferentes_a_melhoria(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    primeiro = {"modo": "planejar", "modelo": "qwen", "entradas": [{"id": "x", "texto": "oi"}]}
    segundo = {"modo": "executar", "modelo": "qwen", "entradas": [{"id": "x", "texto": "outra frase"}]}
    (a / "relatorio.json").write_text(json.dumps(primeiro), encoding="utf-8")
    (b / "relatorio.json").write_text(json.dumps(segundo), encoding="utf-8")
    comparacao = comparar_coletas(a, b)
    assert not comparacao["mesmo_modo"] and not comparacao["melhoria_comprovada"]
    assert not comparacao["diferencas"][0]["mesma_entrada_literal"]
