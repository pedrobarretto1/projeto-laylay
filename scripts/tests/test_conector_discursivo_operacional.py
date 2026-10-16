"""Conector inicial é moldura discursiva, nunca permissão ou parte do alvo."""
from copy import deepcopy

import pytest

from mente_laylay.cognicao.modalidade_turno import (
    classificar_modalidade_turno, extrair_nucleo_pedido_operacional,
    fontes_textuais_dos_segmentos,
)
from mente_laylay.autonomia.roteador_deterministico import normalizar_pedido_natural
from scripts.tests.test_escopo_ato_unico import resolver_real
from scripts.tests.test_escopo_autorizacao_por_ato import _runtime


@pytest.mark.parametrize("pedido", ["liga o ventilador", "pausa a musica", "abre a calculadora",
    "coloca o volume em 40", "abre o site github", "apaga o arquivo notas.txt",
    'toca a música "E Hoje"', "pode abrir a calculadora"])
@pytest.mark.parametrize("conector", ["e ", "E ", "e, "])
def test_conector_inicial_preserva_modalidade_diretiva_e_fonte_original(pedido, conector):
    texto = conector + pedido
    controle = classificar_modalidade_turno(pedido)
    assert controle["autoriza_execucao"] is True
    turno = classificar_modalidade_turno(texto)
    assert turno["autoriza_execucao"] is True, "primeiro limite: conector não pode apagar a diretiva"
    assert len(turno["segmentos"]) == len(controle["segmentos"]) == 1
    fonte = fontes_textuais_dos_segmentos(texto, turno["segmentos"])
    assert len(fonte) == 1 and fonte[0].como_dict()["texto_original"] == texto
    assert turno["texto"] == texto


@pytest.mark.parametrize("pedido", ["não liga o ventilador", "como eu faria para ligar a luz?",
    "se eu quisesse abrir a calculadora?", "você pode abrir a calculadora?",
    'a frase "liga a luz" significa o quê?', "eu vou abrir a calculadora",
    "quando eu confirmar, abre a calculadora",
    "preciso que você não ligue a luz", "preciso saber como abrir a calculadora"])
@pytest.mark.parametrize("conector", ["e ", "E, "])
def test_conector_nao_transforma_negacao_pergunta_relato_condicao_ou_citacao_em_ordem(pedido, conector):
    assert classificar_modalidade_turno(pedido)["autoriza_execucao"] is False
    texto = conector + pedido
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is False
    assert extrair_nucleo_pedido_operacional(texto) is None


@pytest.mark.parametrize("texto,nucleo", [
    ("e liga o ventilador", "liga o ventilador"),
    ("e pausa a musica", "pausa a musica"),
    ('E toca a música "E Hoje"', 'toca a música "E Hoje"'),
    ('e pode abrir o arquivo "Meu E Relatório.TXT"', 'abrir o arquivo "Meu E Relatório.TXT"'),
])
def test_projecao_operacional_reusa_moldura_sem_reescrever_o_argumento(texto, nucleo):
    assert extrair_nucleo_pedido_operacional(texto) == nucleo
    assert normalizar_pedido_natural(texto) == (nucleo, "pedido")


@pytest.mark.parametrize("texto", ["e abre a calculadora e pausa a música",
    "e coloca o volume em 40 e abre a calculadora"])
def test_conector_inicial_nao_impede_segmentar_duas_ordens_independentes(texto):
    turno = classificar_modalidade_turno(texto)
    assert len(turno["segmentos"]) == 2
    assert all(s["autoriza_execucao"] is True for s in turno["segmentos"])
    fontes = fontes_textuais_dos_segmentos(texto, turno["segmentos"])
    assert len(fontes) == 2
    pedidos = [resolver_real(f.como_dict()["texto_original"], {}) for f in fontes]
    assert all(pedidos)
    validar, estado = _runtime(texto, resolver_real)
    antes = estado.snapshot()
    resultado = validar([*pedidos, deepcopy(pedidos[0])])
    assert resultado["comandos"] == pedidos
    assert resultado["atos_autorizados_vinculados"] == [0, 1]
    assert len(resultado["rejeitados"]) == 1 and estado.snapshot() == antes


def test_conector_nao_apaga_veto_da_ordem_posterior_do_mesmo_recurso():
    turno = classificar_modalidade_turno("e abre a calculadora; não abre a calculadora")
    assert turno["autoriza_execucao"] is False
    assert turno["veto_execucao_operacional"] is True


@pytest.mark.parametrize("texto", ["e o ventilador", "e", "E", '"E liga a luz"',
    "é bom ligar a luz", "ela liga a luz", "email recebido", "e-mail recebido"])
def test_palavra_incompleta_nome_ou_copula_nao_sao_diretiva(texto):
    assert classificar_modalidade_turno(texto)["autoriza_execucao"] is False
    assert extrair_nucleo_pedido_operacional(texto) is None


@pytest.mark.parametrize("texto", ["não liga o ventilador", "não abre a calculadora",
    "como eu faria para ligar a luz?", "você pode ligar a luz?",
    "quando eu confirmar, liga a luz", 'a frase "liga a luz" significa o quê?'])
@pytest.mark.parametrize("conector", ["e ", "E, "])
def test_guarda_compartilhada_dos_especialistas_tambem_preserva_modalidade_com_conector(texto, conector):
    from mente_laylay.cognicao.modalidade_turno import analisar_protecao_operacional
    controle = analisar_protecao_operacional(texto)
    assert controle["bloqueia_execucao"] is True
    resultado = analisar_protecao_operacional(conector + texto)
    assert resultado == controle, "não abrir uma segunda interpretação permissiva na porta do especialista"


@pytest.mark.parametrize("texto,nivel", [("e coloca em 40", 40), ("e aumenta para 100", 100),
    ("E, deixa em quarenta", 40), ("e coloca no máximo", 100)])
def test_conector_na_elipse_preserva_referente_confirmado_e_nao_abre_busca_musical(texto, nivel):
    from scripts.tests.test_regressoes_contexto_operacional import _volume_confirmado_para_continuacao
    estado = _volume_confirmado_para_continuacao()
    pedido = resolver_real(texto, estado)
    assert pedido and pedido["intent"] == "VOLUME", "primeira fronteira vizinha: moldura perdida na porta contextual"
    assert pedido["params"]["acao"] == "set" and pedido["params"]["nivel_volume"] == nivel
    validar, compartilhado = _runtime(texto, resolver_real)
    for chave in ("turno_atual", "plano_turno_atual", "retrato_turno_atual"):
        estado.pop(chave, None)
    compartilhado.atualizar_campos("mental", **estado)
    errado = {"intent": "MUSIC_SEARCH", "params": {"query": "em 40"}}
    assert validar([errado, pedido])["comandos"] == [pedido]


@pytest.mark.parametrize("texto", ["e coloca em 40", "e aumenta para 100", "e coloca em 5.5",
    "e coloca em quarenta e onze", "e coloca em quarenta minutos"])
def test_conector_nao_materializa_elipse_sem_base_ou_com_valor_invalido(texto):
    from scripts.tests.test_regressoes_contexto_operacional import _volume_confirmado_para_continuacao
    estado = _volume_confirmado_para_continuacao()
    estado["ultima_acao_ts"] = 0.0
    assert resolver_real(texto, estado) is None
    validar, _ = _runtime(texto, resolver_real)
    errado = {"intent": "MUSIC_SEARCH", "params": {"query": "em 40"}}
    assert validar([errado])["comandos"] == []
