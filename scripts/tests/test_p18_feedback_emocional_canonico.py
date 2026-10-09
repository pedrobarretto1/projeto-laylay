"""P18: feedback observado tem ocorrência causal neutra além do aprendizado.

Parte de receipt e classificação reais, usa o publisher transacional compartilhado
e SQLite temporária. A instalação da porta no root é validada separadamente.
"""

from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pytest

from mente_laylay.emocoes.contrato_causal import criar_evento_emocional_causal
from scripts.tests.test_personalidade_viva_p18_feedback import (
    _evento_feedback, _feedbacks_compartilhados, _montar_composicao,
    _receber_receipt_entrega,
)


def _composicao(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    chamadas = []
    publicar = partial(
        composicao.estado_contexto.publicar_evento_emocional_causal,
        vincular_plano=False, ocorrencia_unica=True,
    )

    def observar_publicacao(evento):
        chamadas.append(deepcopy(evento))
        return publicar(evento)

    composicao.ponte.conectar_aprendizado(
        registrar_feedback=composicao.adaptadores.registrar_feedback_contextual,
        publicar_evento_emocional=observar_publicacao,
    )
    composicao.publicacoes = chamadas
    return composicao


def _encaminhar(composicao, resultado="aceita", **alteracoes):
    evento = _evento_feedback(composicao)
    evento["contexto_humor"] = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]["contexto_humor"]
    evento["id_evento"] = evento["id_entrega"]
    evento.update(alteracoes)
    aceito = True if resultado == "aceita" else False if resultado == "recusa" else None
    return composicao.ponte._encaminhar_feedback_compartilhado(
        resultado, aceito, {"evento_feedback": evento, "texto_feedback": "feedback observado"},
    )


@pytest.mark.parametrize(("texto", "resultado", "tipo"), (
    ("boa dica, isso ajudou", "aceita", "aceitacao"),
    ("não precisa comentar", "recusa", "recusa"),
    ("essa dica está errada", "correcao", "correcao"),
    ("repete de novo", "repeticao", "repeticao"),
    (None, "silencio", "silencio"),
))
def test_feedback_consumido_publica_causa_neutra_da_ocorrencia(
    tmp_path, monkeypatch, texto, resultado, tipo,
):
    composicao = _composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    plano = {"turno_id": "comando_independente", "autoriza_execucao": False}
    composicao.estado.atualizar_campos("mental", plano_turno_atual=plano)
    if texto is None:
        composicao.agora[0] = 1600.0
        observado = composicao.diretor.registrar_silencio_pendente()
    else:
        observado = composicao.diretor.observar_resposta(texto)
    assert observado["resultado"] == resultado
    assert len(_feedbacks_compartilhados(composicao)) == 1
    quadro = composicao.estado.mental.get("eventos_emocionais_causais") or {}
    evento = quadro.get("atual") or {}
    assert evento, "RED P18: feedback entregue e consumido não publica sua ocorrência causal"
    proveniencia = _evento_feedback(composicao)
    assert evento["evidencia_ref"] == f"feedback:{proveniencia['id_entrega']}:{tipo}"
    assert evento["ts"] == composicao.agora[0]
    assert evento["tipo_feedback"] == tipo
    assert evento["proveniencia"] == proveniencia
    assert evento["natureza_evidencia"] == ("inferencia" if tipo == "silencio" else "leitura_social")
    assert evento["emocao"] == "calma" and evento["nivel"] == 1
    assert evento["intensidade"] == 0
    assert evento["permite_expressao"] is False
    assert evento["autoriza_execucao"] is False
    assert evento["persistencia_pessoal"] is False
    assert quadro["historico"] == [evento]
    assert composicao.estado.mental["plano_turno_atual"] == plano
    assert "estado_emocional" not in composicao.estado.mental
    assert len(composicao.publicacoes) == 1


def test_replay_nao_chama_callback_nem_retrocede_causa_atual(tmp_path, monkeypatch):
    composicao = _composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.diretor.observar_resposta("boa dica, isso ajudou")
    assert len(composicao.publicacoes) == 1, "RED P18: ocorrência ainda não publicada"
    posterior = criar_evento_emocional_causal(
        origem="controle", causa="outra ocorrência", evidencia_ref="posterior:1",
        natureza_evidencia="fato_observado", ts=1001.0,
    )
    composicao.estado_contexto.publicar_evento_emocional_causal(posterior, vincular_plano=False)
    antes = composicao.estado.snapshot()["mental"]["eventos_emocionais_causais"]
    assert _encaminhar(composicao)["status"] == "registrado"
    assert _encaminhar(composicao)["status"] == "registrado"
    assert len(composicao.publicacoes) == 1
    assert composicao.estado.mental["eventos_emocionais_causais"] == antes


@pytest.mark.parametrize("alteracoes", (
    {"entregue": False}, {"id_evento": "outro"}, {"dominio": "outra"},
    {"origem_produtor": "outra"}, {"categoria": "outra"}, {"alvo": "outro"},
    {"observado_ts": 1001.0}, {"observado_ts": float("nan")},
    {"entrega_ts": 0.0}, {"entrega_ts": float("inf")},
))
def test_proveniencia_ou_receipt_invalido_nao_publica_causa(tmp_path, monkeypatch, alteracoes):
    composicao = _composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    monkeypatch.setattr(composicao.diretor, "registrar_feedback", lambda *_args, **_kwargs: {})
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou")["resultado"] == "aceita"
    retorno = _encaminhar(composicao, **alteracoes)
    assert retorno["status"] == "rejeitado"
    assert composicao.publicacoes == []
    assert not composicao.estado.mental.get("eventos_emocionais_causais")


@pytest.mark.parametrize("entregue", (False, None))
def test_sem_entrega_confirmada_nao_gera_causa(tmp_path, monkeypatch, entregue):
    composicao = _composicao(tmp_path, monkeypatch)
    if entregue is not None:
        _receber_receipt_entrega(composicao, entregue)
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou") == {}
    assert composicao.diretor.registrar_silencio_pendente() == {}
    assert composicao.publicacoes == []
    assert not composicao.estado.mental.get("eventos_emocionais_causais")


def test_observacao_causal_independe_de_persistencia_do_aprendizado(tmp_path, monkeypatch):
    composicao = _composicao(tmp_path, monkeypatch)
    composicao.ponte.conectar_aprendizado(registrar_feedback=lambda **_dados: None)
    _receber_receipt_entrega(composicao, True)
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou")["resultado"] == "aceita"
    assert _feedbacks_compartilhados(composicao) == []
    assert len(composicao.publicacoes) == 1, "RED P18: falta de persistência não apaga observação confirmada"


def test_porta_causal_instalada_no_root_publica_sem_conexao_manual(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    assert composicao.diretor.observar_resposta("essa dica está errada")["resultado"] == "correcao"
    evento = composicao.estado.mental["eventos_emocionais_causais"]["atual"]
    assert evento["tipo_feedback"] == "correcao"
    assert evento["proveniencia"] == _evento_feedback(composicao)
    assert evento["permite_expressao"] is False


@pytest.mark.parametrize(("instante", "silencio"), ((1599.99, True), (1600.01, False)))
def test_feedback_fora_da_janela_nao_cria_ocorrencia(tmp_path, monkeypatch, instante, silencio):
    composicao = _composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.agora[0] = instante
    retorno = (composicao.diretor.registrar_silencio_pendente() if silencio
               else composicao.diretor.observar_resposta("boa dica, isso ajudou"))
    assert retorno == {}
    assert composicao.publicacoes == []
    assert not composicao.estado.mental.get("eventos_emocionais_causais")


def test_duplo_invocador_concorrente_da_ponte_publica_uma_vez(tmp_path, monkeypatch):
    composicao = _composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    monkeypatch.setattr(composicao.diretor, "registrar_feedback", lambda *_args, **_kwargs: {})
    assert composicao.diretor.observar_resposta("boa dica, isso ajudou")["resultado"] == "aceita"
    with ThreadPoolExecutor(max_workers=2) as executor:
        futuros = [executor.submit(_encaminhar, composicao) for _ in range(2)]
        assert all(futuro.result()["status"] == "registrado" for futuro in futuros)
    assert len(composicao.publicacoes) == 1
    assert len(composicao.estado.mental["eventos_emocionais_causais"]["historico"]) == 1
    compartilhados = _feedbacks_compartilhados(composicao)
    assert len(compartilhados) == 1
    assert len(composicao.memoria.listar_eventos_aprendizado(compartilhados[0]["chave"])) == 1


def test_referencia_reutilizada_com_fonte_alterada_preserva_causa_original(tmp_path, monkeypatch):
    composicao = _composicao(tmp_path, monkeypatch)
    _receber_receipt_entrega(composicao, True)
    composicao.diretor.observar_resposta("boa dica, isso ajudou")
    antes = composicao.estado.snapshot()["mental"]["eventos_emocionais_causais"]
    presenca = composicao.estado.snapshot()["mental"]["presenca_contextual"]
    presenca["ultima_emissao"]["origem"] = "outra_fonte"
    composicao.estado.atualizar_campos("mental", presenca_contextual=presenca)
    _encaminhar(composicao)
    assert len(composicao.publicacoes) == 1
    assert composicao.estado.mental["eventos_emocionais_causais"] == antes
