import json
import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno
from mente_laylay.cognicao.qualidade_comunicacao import montar_mensagens_reparo_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao


def contrato_para(texto):
    return construir_contrato_semantico_fala(texto, plano=planejar_turno(
        texto, turno=classificar_modalidade_turno(texto)))


@pytest.mark.xfail(strict=True, reason="RED aberto: pré-condição isolada falhou na sonda real de 13/09; candidato retirado")
def test_recomendacao_sem_fonte_nao_ordena_escolha_de_evidencia_inexistente():
    contrato = contrato_para("pode me recomendar um modelo que seja bom e barato")
    roteiro = contrato["roteiro_concreto"]
    assert not roteiro["autoriza_execucao"]
    assert "somente da evidência factual do turno" not in roteiro["nucleo_resposta"]


@pytest.mark.xfail(strict=True, reason="RED da mesma raiz: falta contrato completo de evidência para recomendação")
@pytest.mark.parametrize("texto", [
    "pode me recomendar um modelo que seja bom e barato",
    "oi lay, pode me recomendar um filme?",
    "me recomenda um notebook para estudar",
])
@pytest.mark.parametrize("pesquisa", [
    {},
    {"ok": False, "resumo": "Opção A", "candidatos": ["Opção A"], "confianca": 0.9},
    {"ok": True, "resumo": "Informação sobre a categoria, sem opções.", "fonte": "fonte_teste", "confianca": 0.9},
    {"ok": True, "resumo": "Opção A", "fonte": "fonte_teste", "candidatos": ["Opção A"], "confianca": 0.9, "evidencia_obtida_em": 1, "evidencia_validade_s": 10},
])
def test_planejamento_sem_candidatos_validos_nao_exige_escolha(texto, pesquisa):
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    plano["fundamentacao_factual"] = montar_fundamentacao("categoria", pesquisa, agora=100)
    roteiro = construir_contrato_semantico_fala(texto, plano=plano)["roteiro_concreto"]
    assert "somente da evidência factual do turno" not in roteiro["nucleo_resposta"]
    assert "nenhum candidato verificado" in roteiro["nucleo_resposta"]
    assert not roteiro["autoriza_execucao"]
    if texto.startswith("oi"):
        assert roteiro["estrategia"] == "resposta_multiacto"


def test_candidatos_com_fundamentacao_valida_permitem_planejar_escolha():
    texto = "me recomenda um filme de romance"
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    plano["fundamentacao_factual"] = montar_fundamentacao("filme de romance", {
        "ok": True, "resumo": "Opção A; Opção B.", "candidatos": ["Opção A", "Opção B"],
        "fonte": "fonte_teste", "confianca": 0.9,
        "evidencia_obtida_em": 95, "evidencia_validade_s": 10,
    }, agora=100)
    roteiro = construir_contrato_semantico_fala(texto, plano=plano)["roteiro_concreto"]
    assert roteiro["estrategia"] == "recomendacao_fundamentada"
    assert "somente da evidência factual do turno" in roteiro["nucleo_resposta"]
    assert not roteiro["autoriza_execucao"]


def test_reparo_de_estado_preserva_dono_e_pergunta_tematica():
    texto = "estou bem, existe painel solar para arduino?"
    contrato = contrato_para(texto)
    avaliacao = validar_aderencia_contrato_fala(
        texto, "Sim, um painel pode fornecer energia usando regulação adequada.",
        contrato_fala=contrato)
    assert "ato_estado_pessoal_nao_reconhecido" in avaliacao["problemas"]
    reparo = avaliacao["contrato_reparo"]
    assert reparo["estado_pessoal_informado"] == {"falante": "usuario", "estado": "bem"}
    mensagens = montar_mensagens_reparo_comunicacao(texto, "Sim, existe.", avaliacao)
    assert json.loads(mensagens[-1]["content"])["mensagem_atual"] == texto
    assert json.loads(mensagens[-1]["content"])["contrato_de_reparo"]["estado_pessoal_informado"]["falante"] == "usuario"


def test_pergunta_sobre_laylay_nao_ganha_estado_do_usuario():
    texto = "como você está?"
    avaliacao = validar_aderencia_contrato_fala(texto, "Estou bem por aqui.", contrato_fala=contrato_para(texto))
    assert "estado_pessoal_informado" not in avaliacao["contrato_reparo"]
