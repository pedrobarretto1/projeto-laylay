import json
import pytest

from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
from mente_laylay.cognicao.plano_turno import planejar_turno, verificar_fala_turno
from mente_laylay.cognicao.qualidade_comunicacao import montar_mensagens_reparo_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.fundamentacao_factual import (
    avaliar_candidatos_recomendacao, montar_fundamentacao, validar_resposta_recomendacao,
)


def contrato_para(texto):
    return construir_contrato_semantico_fala(texto, plano=planejar_turno(
        texto, turno=classificar_modalidade_turno(texto)))


def test_recomendacao_sem_fonte_nao_ordena_escolha_de_evidencia_inexistente():
    contrato = contrato_para("pode me recomendar um modelo que seja bom e barato")
    roteiro = contrato["roteiro_concreto"]
    assert not roteiro["autoriza_execucao"]
    assert "somente da evidência factual do turno" not in roteiro["nucleo_resposta"]


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


@pytest.mark.parametrize("texto", [
    "pode me recomendar um modelo que seja bom e barato",
    "oi lay, pode me recomendar um filme?",
    "me recomenda um notebook para estudar",
])
@pytest.mark.parametrize("pesquisa", [
    {},
    {"ok": False, "resumo": "Opção A", "candidatos": ["Opção A"], "fonte": "fonte_teste", "confianca": 0.9},
    {"ok": True, "resumo": "Categoria sem opções.", "fonte": "fonte_teste", "confianca": 0.9},
    {"ok": True, "resumo": "Opção A", "candidatos": ["Opção A"], "fonte": "fonte_teste", "confianca": 0.9, "evidencia_obtida_em": 1, "evidencia_validade_s": 10},
])
def test_resposta_final_sem_candidato_observado_nao_publica_escolha(texto, pesquisa):
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    plano["fundamentacao_factual"] = montar_fundamentacao("categoria", pesquisa)
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, plano=plano)
    resultado = verificar_fala_turno(
        "Recomendo o Modelo Inventado. É barato e tem tudo o que você precisa.",
        plano=plano, origem="resposta_ia",
    )
    assert "Modelo Inventado" not in resultado["fala"]
    assert "opção verificada" in resultado["fala"]
    assert "recomendacao_sem_candidato_verificado" in resultado["problemas"]
    assert resultado["aceita"] is True
    assert not plano["autoriza_execucao"]
    if texto.startswith("oi"):
        assert resultado["fala"].startswith("Oi!")


def test_candidato_observado_nao_comprova_especificacoes_ou_atendimento():
    texto = "me recomenda um notebook para estudar"
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    plano["fundamentacao_factual"] = montar_fundamentacao("notebook", {
        "ok": True, "resumo": "Opção A; Opção B.", "candidatos": ["Opção A", "Opção B"],
        "fonte": "fonte_teste", "confianca": 0.9,
    })
    resultado = verificar_fala_turno(
        "Opção B é perfeita: custa R$ 900, tem 64 GB de RAM e atende a todos os requisitos.",
        plano=plano, origem="resposta_ia",
    )
    assert "Opção B" in resultado["fala"]
    assert "fonte_teste" in resultado["fala"]
    assert "Não confirmei" in resultado["fala"]
    assert "64 GB" not in resultado["fala"]
    assert "900" not in resultado["fala"]
    assert "perfeita" not in resultado["fala"]
    assert "recomendacao_limitada_a_evidencia" in resultado["problemas"]
    comparacao = resultado["comparacao_recomendacao"]
    assert {item["estado_requisitos"] for item in comparacao} == {"nao_comprovado"}
    assert all(item["pedido"] == texto and item["candidato"] in item["trecho"] for item in comparacao)


def test_recomendacao_com_estado_social_nao_inverte_o_falante():
    texto = "estou cansado, pode me recomendar um filme?"
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    plano["contrato_fala"] = construir_contrato_semantico_fala(texto, plano=plano)
    resultado = verificar_fala_turno("Recomendo o Filme Inventado.", plano=plano)
    assert resultado["aceita"] is True
    assert resultado["fala"].startswith("Entendo, você está cansado.")
    assert "opção verificada" in resultado["fala"]
    assert "Filme Inventado" not in resultado["fala"]


@pytest.mark.parametrize("texto", (
    "quero um modelo do modulo dc-dc que possa alimentar um esp32 super mini, 4 motores e uma tela oled alem de uma bateria de litio de 5V",
    "procuro uma opção que rode meus programas",
    "busco uma alternativa para editar vídeos",
))
def test_pedido_de_opcao_com_requisitos_segue_o_mesmo_contrato(texto):
    plano = planejar_turno(texto, turno=classificar_modalidade_turno(texto))
    assert plano["dominio"] == "recomendacao"
    resultado = verificar_fala_turno(
        "O Modelo Inventado é compatível com tudo e resolve seu problema.", plano=plano,
    )
    assert "Modelo Inventado" not in resultado["fala"]
    assert "opção verificada" in resultado["fala"]
    assert not plano["autoriza_execucao"]


@pytest.mark.parametrize("alteracao", (
    {"fonte": ""}, {"confiavel": False}, {"status": "contestado"},
    {"evidencia_dentro_validade": False}, {"candidatos": ["Opção Inventada"]},
    {"candidatos": ["Opç"]}, {"resumo": "Sem nomes observados."},
    {"fontes": [{"url": "https://fonte.test", "trecho": "Outra opção."}]},
))
def test_candidato_exige_nome_inteiro_na_mesma_fonte_valida(alteracao):
    base = montar_fundamentacao("notebook", {
        "ok": True, "resumo": "Opção A.", "candidatos": ["Opção A"],
        "fonte": "fonte_teste", "confianca": 0.9,
    })
    base.update(alteracao)
    assert avaliar_candidatos_recomendacao(base) == []


def test_evidencia_de_lista_estavel_expira_entre_planejamento_e_fala():
    base = montar_fundamentacao("filme", {
        "ok": True, "resumo": "Opção A.", "candidatos": ["Opção A"],
        "fonte": "fonte_teste", "confianca": 0.9,
        "evidencia_obtida_em": 95, "evidencia_validade_s": 10,
    }, agora=100)
    assert avaliar_candidatos_recomendacao(base, agora=100)
    assert avaliar_candidatos_recomendacao(base, agora=105) == []
    assert "Opção A" not in validar_resposta_recomendacao(
        "Recomendo Opção A.", fundamentacao=base, agora=105,
    )["fala"]
