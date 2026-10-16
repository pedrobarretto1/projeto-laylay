"""Um mesmo vocabulário sustenta pedido, fronteira e proteção do ato.

Reconhecer o imperativo não prova capacidade, alvo válido ou efeito.
"""
import pytest

from mente_laylay.cognicao.modalidade_turno import (
    _detector_lexical_ancorado,
    _evidencia_ato_operacional,
    classificar_modalidade_turno,
)
from mente_laylay.autonomia.roteador_deterministico import detectar_volume_ou_midia


PEDIDOS = [
    "sobe o volume para 40", "suba o volume para 40",
    "aumente o volume para 40", "abaixe o volume para 40",
    "baixa o volume para 40", "baixe o volume para 40",
    "diminua o volume para 40", "ajusta o brilho da lâmpada para 40",
    "ajuste a janela para a esquerda", "altera a cor da lâmpada para azul",
    "altere a cor da lâmpada para azul", "minimize a janela Calculadora",
    "renomeie o arquivo Resumo.txt para Notas.txt",
    "reduz o volume para 30", "reduza a temperatura para 20",
    "eleva o brilho da lâmpada para 40", "eleve o volume para 80",
]


@pytest.mark.parametrize("texto", PEDIDOS)
def test_imperativo_reconhecido_na_protecao_tambem_publica_pedido_e_fronteira(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["modalidade"] == "comando"
    assert turno["autoriza_execucao"] is True
    assert _evidencia_ato_operacional(texto, normalizar_texto=None)[0] is True
    assert _detector_lexical_ancorado(texto, normalizar_texto=None,
        texto_tem_comando_explicito=lambda _: True) is True


@pytest.mark.parametrize("primeiro", PEDIDOS[:11] + PEDIDOS[-4:])
@pytest.mark.parametrize("inverter", [False, True])
def test_pedidos_conjuntos_nao_dependem_da_ordem_do_verbo_reconhecido(primeiro, inverter):
    segundo = "abre o aplicativo Notepad"
    atos = [segundo, primeiro] if inverter else [primeiro, segundo]
    turno = classificar_modalidade_turno(" e ".join(atos))
    assert [s["texto"] for s in turno["segmentos"]] == [t.casefold() for t in atos]
    assert all(s["autoriza_execucao"] for s in turno["segmentos"])


@pytest.mark.parametrize("verbo,infinitivo,objeto", [
    ("sobe", "subir", "o volume para 40"),
    ("aumente", "aumentar", "o volume para 40"),
    ("ajuste", "ajustar", "o brilho da lâmpada para 40"),
    ("minimize", "minimizar", "a janela Calculadora"),
    ("reduza", "reduzir", "a temperatura para 20"),
    ("eleve", "elevar", "o brilho da lâmpada para 40"),
])
@pytest.mark.parametrize("moldura", [
    "não {verbo} {objeto}", "nunca {verbo} {objeto}",
    "quando eu confirmar, {verbo} {objeto}",
    "ele disse {verbo} {objeto}", '"{verbo} {objeto}"',
    "{verbo} {objeto} significa o quê?", "como posso {infinitivo} {objeto}?",
    "você pode {infinitivo} {objeto}?", "eu vou {infinitivo} {objeto}",
    "se eu quisesse {infinitivo} {objeto}, como faria?",
])
def test_reconhecer_verbo_nao_converte_negacao_mencao_condicao_ou_capacidade_em_permissao(verbo, infinitivo, objeto, moldura):
    texto = moldura.format(verbo=verbo, infinitivo=infinitivo, objeto=objeto)
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is False
    assert _evidencia_ato_operacional(texto, normalizar_texto=None)[0] is False


@pytest.mark.parametrize("texto", [
    "sobe o volume para 40?", "pode subir o volume para 40",
    "por favor, pode aumentar o volume para 40?",
    "pode ajustar o brilho da lâmpada para 40",
    "pode reduzir a temperatura para 20",
    "por favor, pode elevar o brilho da lâmpada para 40?",
])
def test_moldura_diretiva_compartilha_verbo_sem_usar_interrogacao_como_veto(texto):
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is True


def test_detector_de_volume_ja_reconhecia_a_operacao_sem_depender_da_llm():
    candidato = detectar_volume_ou_midia("sobe o volume para 40", params_cb=lambda **p: p)
    assert candidato == {"intent": "VOLUME", "params": {"acao": "set", "nivel_volume": 40}}


@pytest.mark.parametrize("texto", [
    'abre o arquivo "Sobe o volume e ajuste a janela.txt"',
    'toca a música "Sobe o volume e aumenta o som"',
    'abre o arquivo "Reduza a temperatura e eleve o brilho.txt"',
])
def test_verbo_no_nome_literal_nao_cria_outro_ato(texto):
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True
    assert len(turno["segmentos"]) == 1


def test_negacao_posterior_da_mesma_acao_revoga_pedido_nao_cria_nova_autoridade():
    turno = classificar_modalidade_turno("sobe o volume para 40; não sobe o volume")
    assert turno["autoriza_execucao"] is False
    assert turno["veto_execucao_operacional"] is True


@pytest.mark.parametrize("verbo,objeto", [
    ("reduza", "a temperatura para 20"), ("eleve", "o brilho para 40"),
])
def test_negacao_posterior_preserva_veto_nas_familias_de_ajuste(verbo, objeto):
    turno = classificar_modalidade_turno(f"{verbo} {objeto}; não {verbo} {objeto}")
    assert turno["autoriza_execucao"] is False
    assert turno["veto_execucao_operacional"] is True
