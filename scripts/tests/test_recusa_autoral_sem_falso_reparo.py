"""Ato de abstenção e referência a pergunta não são afirmações de efeito."""
import json

import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.autonomia.processamento_resposta_ia import preparar_resposta_para_execucao


def _plano(texto):
    turno = classificar_modalidade_turno(texto)
    assert not turno["autoriza_execucao"]
    plano = planejar_turno(texto, turno=turno, mente={})
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente={})
    assert plano["contrato_fala"]["roteiro_concreto"]["estrategia"] == "negacao_operacional_sem_efeito"
    return plano


CASOS = (
    ("preciso que você não pause a música", "Não vou pausar a música."),
    ("preciso que você não pause a música", "Entendido, não vou pausar a música."),
    ("preciso que você não pause a música", "Não farei pausa na música."),
    ("não ligue a lâmpada", "Não vou ligar a lâmpada."),
    ("não apague o arquivo notas.txt", "Não vou apagar o arquivo notas.txt."),
    ("não abra a calculadora", "Não irei abrir a calculadora."),
    ("eu não perguntei se o Discord está aberto", "Você não perguntou se o Discord está aberto."),
    ("eu não perguntei se o Opera está fechado", "Entendi, você não perguntou se o Opera está fechado."),
    ("eu não perguntei se o Discord está aberto", "Você não perguntou se o Discord continua aberto."),
    ("eu não perguntei se o arquivo foi salvo", "Você não perguntou se o arquivo foi salvo."),
    ("eu não perguntei se o e-mail foi enviado", "Você não perguntou se o e-mail foi enviado."),
    ("eu não perguntei se a lâmpada está ligada", "Você não perguntou se a lâmpada está ligada."),
    ("eu não perguntei se o Discord está aberto", "Você tem razão, não vou verificar se o Discord está aberto."),
    ("eu não perguntei se o Opera está fechado", "Não vou consultar se o Opera está fechado."),
)


@pytest.mark.parametrize("texto, fala", CASOS)
def test_resposta_valida_atravessa_validadores_sem_reparo(texto, fala):
    plano = _plano(texto)
    avaliacao = avaliar_qualidade_comunicacao(texto, fala, plano=plano)
    assert avaliacao["aceita"], avaliacao["problemas"]
    assert not avaliacao["requer_reparo"], avaliacao["problemas"]

    def nao_reparar(*args, **kwargs):
        pytest.fail("a fala válida não deve consumir outra chamada de modelo")

    resultado = preparar_resposta_para_execucao(
        texto, json.dumps({"fala": fala, "comandos": []}, ensure_ascii=False),
        enviar_mensagem_cb=nao_reparar, limpar_texto_fala_cb=lambda t: t,
        fallback_fala="Contingência", memoria_sqlite=None,
        contexto_comunicacao={"plano_turno": plano}, log=lambda _: None,
    )
    assert not resultado["comandos"]
    assert resultado["fala"] == fala
    final = verificar_fala_turno(fala, plano=plano, origem="ia_final")
    assert final["aceita"], final
    assert final["fala"] == fala


@pytest.mark.parametrize("fala", (
    "Você não perguntou, então o Discord está aberto.",
    "Você não perguntou se o Discord está aberto, mas o Opera está fechado.",
    "Você não perguntou se o Discord está aberto; o Opera está fechado.",
    "Você não perguntou se o Discord está aberto e o Opera está fechado.",
    "Você não perguntou se o Discord está aberto porque o Opera está fechado.",
    "Você não perguntou se o Discord está aberto logo o Opera está fechado.",
    "Você não perguntou se o Discord está aberto ou o Opera está fechado.",
    "Você não perguntou se o Discord está aberto. Ele está fechado.",
    "Você não perguntou, o Discord continua aberto.",
    "Não vou verificar se o Discord está aberto, mas o Opera está fechado.",
    "Não vou verificar, o Discord está aberto.",
))
def test_referencia_a_pergunta_nao_libera_afirmacao_independente(fala):
    from mente_laylay.cognicao.guardiao_alegacoes import detectar_resultados_operacionais_sem_evidencia
    texto = "eu não perguntei se o Discord está aberto"
    plano = _plano(texto)
    assert detectar_resultados_operacionais_sem_evidencia(fala, plano=plano)
    assert not avaliar_qualidade_comunicacao(texto, fala, plano=plano)["aceita"]


@pytest.mark.parametrize("fala", (
    "A música continua rodando.",
    "Não posso pausar a música.",
    "Não vou conseguir pausar a música.",
))
def test_estado_ou_incapacidade_nao_e_reconhecimento_da_decisao(fala):
    assert not avaliar_qualidade_comunicacao(
        "preciso que você não pause a música", fala,
        plano=_plano("preciso que você não pause a música"),
    )["aceita"]


@pytest.mark.parametrize("texto, fala", (
    ("eu não perguntei se o arquivo foi salvo", "Você não perguntou se o arquivo foi salvo, mas o e-mail foi enviado."),
    ("eu não perguntei se a lâmpada está ligada", "Você não perguntou se a lâmpada está ligada; o ventilador está ligado."),
))
def test_subordinada_nao_empresta_prova_a_outro_dominio(texto, fala):
    final = verificar_fala_turno(fala, plano=_plano(texto), origem="ia_final")
    assert not final["aceita"], final
