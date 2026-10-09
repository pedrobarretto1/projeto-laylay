"""P20: feedback social literal não é correção factual nem autorização.

Qualificação local no interpretador canônico; ligação com entrega é verificada
separadamente pela Ponte, com os owners e SQLite reais da composição P18.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from mente_laylay.cognicao import interpretador_continuidade as interpretador
from scripts.tests.test_personalidade_viva_p18_feedback import (
    _montar_composicao, _receber_receipt_entrega,
)


def _qualificar(texto):
    qualificar = getattr(interpretador, "qualificar_feedback_humor", None)
    assert callable(qualificar), "o owner canônico precisa qualificar o alvo social do feedback"
    return qualificar(texto)


@pytest.mark.parametrize(("texto", "tipo", "direcao"), (
    ("Não, Lay. Essa piada passou do ponto.", "correcao", "leve"),
    ("Essa brincadeira foi pesada demais.", "correcao", "leve"),
    ("Você pegou pesado nessa piada.", "correcao", "leve"),
    ("Não gostei dessa piada.", "recusa", "leve"),
    ("Para com essas brincadeiras.", "recusa", "leve"),
    ("Gostei dessa piada.", "aceitacao", "mais_humor"),
    ("Essa brincadeira foi boa.", "aceitacao", "mais_humor"),
    ("Gostei do seu tom de brincadeira.", "aceitacao", "mais_humor"),
    ("Repete essa piada.", "repeticao", "mais_humor"),
    ("Pode repetir essa brincadeira.", "repeticao", "mais_humor"),
))
def test_feedback_de_humor_requer_avaliacao_literal_do_estilo(texto, tipo, direcao):
    assert _qualificar(texto) == {
        "alvo_feedback": "humor", "tipo": tipo, "direcao": direcao,
        "evidencia_literal": texto,
    }
    classificacao = "aceita" if tipo == "aceitacao" else tipo
    assert interpretador.classificar_feedback_comunicativo(texto) == classificacao


@pytest.mark.parametrize("texto", (
    "Não, Lay. O número da dica está errado.",
    "Essa dica está errada.", "Boa dica, isso ajudou.", "Não precisa comentar.",
    "Repete de novo.", "Pode me zoar mais.", "Pega leve hoje.",
    '"Não, Lay. Essa piada passou do ponto."',
    'Se eu disser "essa piada passou do ponto", o que significa?',
    'A frase "gostei dessa piada" é um exemplo.',
    "Ele disse que essa piada passou do ponto.",
    'Crie um arquivo chamado "Gostei dessa piada".',
    "Estou triste, essa piada passou do ponto.",
    "Essa piada foi boa?", "Essa piada tem o número errado.",
))
def test_sem_alvo_social_literal_nao_aprende_tolerancia(texto):
    assert _qualificar(texto) == {}


def test_correcao_factual_e_social_preservam_tipo_mas_nao_compartilham_alvo():
    # Falsifica atribuir o defeito a classificação geral ou ao prefixo 'Não, Lay'.
    factual = "Não, Lay. O número da dica está errado."
    social = "Não, Lay. Essa piada passou do ponto."
    assert interpretador.classificar_feedback_comunicativo(factual) == "correcao"
    assert interpretador.classificar_feedback_comunicativo(social) == "correcao"
    assert _qualificar(factual) == {}
    assert _qualificar(social)["alvo_feedback"] == "humor"


def _preparar_envio(composicao, texto, *, contexto="jogo", tipo="correcao"):
    _receber_receipt_entrega(composicao, True)
    emissao = composicao.estado.mental["presenca_contextual"]["ultima_emissao"]
    emissao.update({"contexto_humor": contexto, "feedback_registrado": True,
                    "feedback": "aceita" if tipo == "aceitacao" else tipo,
                    "feedback_ts": 1001.0})
    evento = {
        "id_entrega": emissao["id_entrega"], "id_evento": emissao["id_entrega"],
        "dominio": emissao["dominio"], "origem_produtor": emissao["origem"],
        "categoria": emissao["categoria"], "alvo": emissao["chave"],
        "entrega_ts": emissao["ts"], "observado_ts": 1001.0, "entregue": True,
        "contexto_humor": contexto,
    }
    envios = []
    composicao.ponte.conectar_aprendizado(
        registrar_feedback=lambda **dados: envios.append(deepcopy(dados)) or {"chave": "controle"},
    )
    resultado = "aceita" if tipo == "aceitacao" else tipo
    aceito = True if tipo == "aceitacao" else False if tipo == "recusa" else None
    return resultado, aceito, {"evento_feedback": evento, "texto_feedback": texto}, envios


def test_ponte_transporta_qualificacao_e_contexto_da_entrega_nao_do_turno(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    texto = "Não, Lay. Essa piada passou do ponto."
    resultado, aceito, dados, envios = _preparar_envio(composicao, texto)
    # O estado corrente já mudou; somente o retrato da emissão define o escopo.
    composicao.estado.atualizar_campos("mental", modo_jogo_ativo=False)
    retorno = composicao.ponte._encaminhar_feedback_compartilhado(resultado, aceito, dados)
    assert retorno["status"] == "registrado"
    assert len(envios) == 1
    envio = envios[0]
    assert envio["id_evento"] == dados["evento_feedback"]["id_entrega"]
    assert envio["proveniencia"]["contexto_humor"] == "jogo"
    assert envio["proveniencia"]["feedback_humor"] == _qualificar(texto)
    assert envio["proveniencia"]["entrega_ts"] == 1000.0
    assert envio["proveniencia"]["observado_ts"] == 1001.0


@pytest.mark.parametrize("alteracoes", (
    {"contexto_humor": "conversa"}, {"contexto_humor": "geral"},
    {"id_evento": "outra"}, {"entregue": False}, {"observado_ts": 1002.0},
))
def test_ponte_rejeita_qualificacao_com_proveniencia_divergente(tmp_path, monkeypatch, alteracoes):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    resultado, aceito, dados, envios = _preparar_envio(
        composicao, "Não, Lay. Essa piada passou do ponto.",
    )
    dados["evento_feedback"].update(alteracoes)
    assert composicao.ponte._encaminhar_feedback_compartilhado(resultado, aceito, dados)["status"] == "rejeitado"
    assert envios == []


def test_ponte_feedback_factual_nao_ganha_qualificacao_social(tmp_path, monkeypatch):
    composicao = _montar_composicao(tmp_path, monkeypatch)
    resultado, aceito, dados, envios = _preparar_envio(
        composicao, "Não, Lay. O número da dica está errado.",
    )
    assert composicao.ponte._encaminhar_feedback_compartilhado(resultado, aceito, dados)["status"] == "registrado"
    assert "feedback_humor" not in envios[0]["proveniencia"]
