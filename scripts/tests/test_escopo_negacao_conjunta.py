"""Fronteira de ato não concede autoridade nem resolve cancelamento ambíguo."""
import pytest

from mente_laylay.cognicao.modalidade_turno import (
    autoriza_execucao_efetiva,
    bloqueia_execucao_operacional_prioritaria,
    classificar_modalidade_turno,
)
from mente_laylay.cognicao.revisao_turno import resolver_revisao_intra_turno


@pytest.mark.parametrize("separador", ["; ", ", ", ". ", " e ", " mas "])
@pytest.mark.parametrize("pedido,proibicao", [
    ("abre o app chamado Arquivo Vivo", "não liga a lampada do quarto"),
    ("liga a luz do quarto", "não abre o aplicativo calculadora"),
    ("pausa a música", "nunca apaga o arquivo notas.txt"),
    ("abre o site exemplo.com", "jamais toca a música Oceano"),
    ("abre o arquivo notas.txt", "não coloca a playlist Favoritas"),
])
def test_negacao_de_recurso_independente_nao_revoga_pedido_de_outro_tipo(pedido, proibicao, separador):
    texto = pedido + separador + proibicao
    turno = classificar_modalidade_turno(texto)
    assert len(turno["segmentos"]) == 2, "primeira fronteira: proibição absorvida pelo pedido"
    permitido, vetado = turno["segmentos"]
    assert autoriza_execucao_efetiva(permitido)
    assert not autoriza_execucao_efetiva(vetado)
    assert vetado["veto_execucao_operacional"]
    assert turno["texto_operacional"] == permitido["texto"]
    assert bloqueia_execucao_operacional_prioritaria(texto, classificacao=turno) is False
    assert not resolver_revisao_intra_turno(texto)["detectada"], "owner de revisão não deve substituir atos independentes"


@pytest.mark.parametrize("texto", [
    "não liga a luz e abre o aplicativo calculadora",
    "não liga a luz e o ventilador",
    "abre o app calculadora; não abre o app calculadora",
    "abre o app calculadora; não abre esse aplicativo",
    "abre o app calculadora; não abre",
    "abre o app calculadora; não faz isso",
    "abre o app calculadora; não liga ela",
    "abre o app calculadora; não liga esse aparelho",
    "quando eu confirmar, abre o app calculadora e não liga a luz",
    'escreve "abre o app calculadora; não liga a luz" na conversa',
    'abre o app "Arquivo Vivo; não liga a luz',
    "abre o app calculadora e não liga a luz significa o quê?",
])
def test_negacao_sem_independencia_comprovada_continua_fechada(texto):
    turno = classificar_modalidade_turno(texto)
    assert not autoriza_execucao_efetiva(turno)
    assert not any(autoriza_execucao_efetiva(ato) for ato in turno["segmentos"])


def test_negacao_atomica_e_ordem_posterior_ja_possuem_escopos_distintos():
    turno = classificar_modalidade_turno("não liga a luz; abre o aplicativo calculadora")
    assert [autoriza_execucao_efetiva(ato) for ato in turno["segmentos"]] == [False, True]


def test_negacao_dentro_de_nome_citado_nao_cria_ato_externo():
    turno = classificar_modalidade_turno('abre o app "Arquivo Vivo; não liga a luz"')
    assert len(turno["segmentos"]) == 1


def test_proibicao_posterior_nao_perde_escopo_apos_ato_intermediario():
    turno = classificar_modalidade_turno(
        "abre o app calculadora; não liga a luz; abre o arquivo notas.txt; não abre o app calculadora"
    )
    autorizados = [a["texto"] for a in turno["segmentos"] if autoriza_execucao_efetiva(a)]
    assert autorizados == ["abre o arquivo notas.txt"], "cancelamento posterior não pode liberar abertura anterior"


@pytest.mark.parametrize("texto", [
    "abre o app calculadora; não abre o app calculadora",
    "abre o app calculadora; não abre",
    "abre o app calculadora; não, melhor abre o app bloco de notas",
])
def test_revisao_ainda_reconhece_revogacao_ou_substituicao_do_pedido(texto):
    assert resolver_revisao_intra_turno(texto)["detectada"]
