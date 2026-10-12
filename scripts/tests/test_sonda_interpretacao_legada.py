"""Valida o instrumento; não certifica o interpretador nem mascara os REDs."""
from scripts.analises.sonda_interpretacao_legada import Caso, avaliar, painel


def test_painel_tem_ids_unicos_e_cobertura_multidominio():
    casos = painel()
    assert len(casos) == 100
    assert len({c.id for c in casos}) == 100
    assert {c.dominio for c in casos} == {"app", "midia", "iot", "arquivo", "composto"}
    assert sum(c.dominio == "composto" for c in casos) == 28


def test_instrumento_distingue_autorizacao_de_perda_de_operacao():
    # Expectativa deliberadamente impossível para provar que o instrumento
    # acusa cada contrato, sem usar a saída atual como rótulo correto.
    caso = Caso("controle", "instrumento", "app", "Abre a calculadora.", False, ("conteudo_inexistente",))
    resultado = avaliar(caso)
    assert "autoridade_indevida" in resultado["falhas"]
    assert "operacao_pedida_ausente:conteudo_inexistente" in resultado["falhas"]
    assert resultado["efeito_externo_testado"] is False


def test_literal_impossivel_acusa_as_duas_fronteiras_independentemente():
    caso = Caso("controle", "instrumento", "app", "Abre a calculadora.", True, literais_indivisiveis=('"literal ausente"',))
    resultado = avaliar(caso)
    assert "literal_fragmentado:modalidade" in resultado["falhas"]
    assert "literal_fragmentado:cadeia" in resultado["falhas"]


def test_pares_minimos_condicionais_preservam_expectativa_sem_pontuacao():
    casos = [c for c in painel() if c.familia == "condicao_prefixada"]
    assert len(casos) == 8
    assert all(c.autoriza_agora is False for c in casos)


def test_expectativas_dos_conjuntos_checam_escopo_e_nao_so_rotulo():
    casos = [c for c in painel() if c.familia == "condicao_local"]
    assert casos and all(c.operacoes_presentes and c.operacoes_ausentes for c in casos)
    polidos = [c for c in painel() if c.familia == "polidez_compartilhada"]
    assert polidos and all(len(c.operacoes_presentes) == 2 for c in polidos)
