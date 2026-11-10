"""Escopo da citação sobrevive à revisão; exemplo não é prova ou permissão."""
import json
from pathlib import Path

import pytest

from mente_laylay.cognicao.fundamentacao_factual import (
    classificar_atualidade_factual, extrair_titulos_citados, validar_fala_com_fundamentacao,
)
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.referencias_linguagem import enunciados_discursivos


CASO = json.loads((Path(__file__).parent / 'fixtures/exemplo_citado_integral.json').read_text(encoding='utf8'))
EXEMPLO = (
    'Essa ideia tem um potencial, mas a construção parece um pouco confusa. '
    'Que tal começar pela parte menor? Um ajuste de foco pode deixar a proposta mais clara.'
)


def revisar(fala):
    return validar_fala_com_fundamentacao(fala, fundamentacao=None)


def test_exemplo_historico_chega_inteiro_ao_verificador_de_turno():
    resultado = verificar_fala_turno(CASO['fala'], plano={
        'texto_usuario': CASO['entrada'], 'comandos': [], 'autoriza_execucao': False,
    })
    assert resultado['aceita'], resultado
    assert resultado['fala'] == CASO['fala'], resultado
    assert 'alegacao_especifica_sem_fonte' not in resultado['problemas']


def test_pontuacao_interna_nao_inventa_fronteira_na_oracao_externa():
    exemplo = f'Eu diria: "{EXEMPLO}"'
    citado = ((len('Eu diria: '), len(exemplo)),)
    texto = exemplo + ' O aparelho pesa 70 kg.'
    assert enunciados_discursivos(texto, intervalos_protegidos=citado) == (texto,)


def test_citacao_em_oracao_relativa_nao_encerra_a_consulta_externa():
    texto = 'O presidente que disse "Eu volto!" continua no cargo?'
    assert enunciados_discursivos(texto) == (texto,)
    assert classificar_atualidade_factual(texto)['depende_atualidade']


@pytest.mark.parametrize('condicao', [
    'Se o criador me pedir para avaliar uma ideia dele e achar ruim',
    'Se a diretora pedisse uma sugestão',
    'Se o pesquisador quiser um exemplo para o protótipo de 70 kg',
])
def test_antecedente_condicional_do_exemplo_nao_e_fato_confirmado(condicao):
    fala = f'{condicao}, eu diria: "{EXEMPLO}"'
    resultado = revisar(fala)
    assert resultado['fala'] == fala and not resultado['problemas'], resultado


@pytest.mark.parametrize('verbo', ['diria', 'responderia', 'escreveria'])
@pytest.mark.parametrize('aspas', [('"', '"'), ("'", "'"), ('“', '”'), ('‘', '’')])
def test_exemplo_condicional_longo_e_multipontuado_e_um_enunciado(verbo, aspas):
    texto = EXEMPLO + ' Não afirmaria que esse aparelho foi lançado em 2030 sem conferir.'
    fala = f'Eu {verbo}: {aspas[0]}{texto}{aspas[1]}'
    resultado = revisar(fala)
    assert resultado['fala'] == fala and not resultado['problemas'], resultado
    assert extrair_titulos_citados(fala) == []


@pytest.mark.parametrize('introducao', ['Diga', 'Você pode escrever', 'Peça assim'])
def test_instrucao_citada_longa_preserva_datas_e_medidas_como_dados(introducao):
    texto = ('Em 2030, crie uma nota para a reunião. Inclua a medida de 70 kg como '
             'exemplo e anote que os números desta mensagem são apenas dados do texto.')
    fala = f'{introducao}: "{texto}"'
    resultado = revisar(fala)
    assert resultado['fala'] == fala and not resultado['problemas'], resultado


@pytest.mark.parametrize('externa,problema', [
    ('O filme foi lançado em 2025.', 'data_sem_evidencia'),
    ('O aparelho pesa 70 kg.', 'medida_sem_evidencia'),
    ('Recomendo o filme "Lua que Nunca Existiu".', 'obra_sem_evidencia'),
])
def test_afirmacao_vizinha_nao_herda_o_papel_do_exemplo(externa, problema):
    exemplo = f'Eu diria: "{EXEMPLO.rstrip(".")}".'
    resultado = revisar(exemplo + ' ' + externa)
    assert problema in resultado['problemas'], resultado
    assert resultado['trechos_rejeitados'] == [externa]
    assert resultado['fala'] == exemplo


@pytest.mark.parametrize('introducao', [
    'A pesquisadora disse', 'O relatório afirma', 'Recomendo o filme',
])
def test_aspas_longas_sem_moldura_de_exemplo_nao_isentam_afirmacao(introducao):
    fala = f'{introducao}: "O aparelho foi lançado em 2025. {EXEMPLO}"'
    resultado = revisar(fala)
    assert resultado['problemas'], resultado
    assert resultado['fala'] != fala
    assert any('2025' in trecho for trecho in resultado['trechos_rejeitados'])


def test_fato_fora_da_citacao_na_mesma_frase_nao_e_mascarado():
    fala = f'Eu diria: "{EXEMPLO}", mas o aparelho pesa 70 kg.'
    assert 'medida_sem_evidencia' in revisar(fala)['problemas']


@pytest.mark.parametrize('continua', ['possui bateria removível.', 'POSSUI bateria removível.'])
def test_exemplo_interno_nao_separa_sujeito_de_predicado_factual(continua):
    fala = f'O aparelho que me faz dizer: "Incrível!" {continua}'
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao={
        'tema': 'aparelho', 'confiavel': False,
    })
    assert 'alegacao_especifica_sem_fonte' in resultado['problemas'], resultado


def test_ausencia_de_fronteira_externa_nao_dispensa_fato_depois_do_exemplo():
    fala = f'Eu diria: "{EXEMPLO}" O aparelho pesa 70 kg.'
    assert 'medida_sem_evidencia' in revisar(fala)['problemas']


def test_ponto_e_virgula_nao_desvincula_predicado_de_sujeito_no_revisor_factual():
    fala = ('O aparelho é portátil; possui bateria removível '
            'com autonomia excepcional para qualquer viagem.')
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao={
        'tema': 'aparelho', 'confiavel': False,
    })
    assert resultado['trechos_rejeitados'] == [fala], resultado
    assert 'possui bateria removível' not in resultado['fala']


def test_citacao_nao_fabrica_receipt_operacional():
    fala = f'Eu diria: "{EXEMPLO}" Consegui abrir o Opera.'
    resultado = verificar_fala_turno(fala, plano={
        'texto_usuario': 'Como você responderia a uma ideia ruim?',
        'autoriza_execucao': False, 'comandos': [],
    })
    assert 'Consegui abrir o Opera.' not in resultado['fala']
    assert resultado['problemas']


@pytest.mark.parametrize('tamanho', [99, 100, 101, 1001])
def test_extensao_do_enunciado_nao_muda_seu_papel(tamanho):
    conteudo = 'Em 2030, anote este exemplo: ' + 'a' * tamanho + '. Mais uma frase.'
    fala = f'Diga: "{conteudo}"'
    resultado = revisar(fala)
    assert resultado['fala'] == fala and not resultado['problemas'], resultado


@pytest.mark.parametrize('marcador', ['*', '**'])
def test_exemplo_destacado_em_markdown_tem_o_mesmo_escopo(marcador):
    texto = EXEMPLO + ' Não afirmaria que o aparelho pesa 70 kg sem conferir.'
    fala = f'Eu diria: {marcador}{texto}{marcador}'
    resultado = revisar(fala)
    assert resultado['fala'] == fala and not resultado['problemas'], resultado


@pytest.mark.parametrize('fala,tema', [
    ('O relatório afirma: "Parece interessante. O aparelho possui bateria removível."', 'aparelho'),
    ('A pesquisadora disse: "Acho curioso. Python possui tipagem estática."', 'Python'),
])
def test_opiniao_interna_nao_dispensa_fonte_da_outra_afirmacao_citada(fala, tema):
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao={
        'tema': tema, 'confiavel': False,
    })
    assert 'alegacao_especifica_sem_fonte' in resultado['problemas'], resultado
    assert any('possui' in trecho for trecho in resultado['trechos_rejeitados'])


def test_segunda_medida_na_citacao_nao_herda_fonte_da_primeira():
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    base = montar_fundamentacao(
        'aparelho', {'ok': True, 'resumo': 'O primeiro aparelho pesa 70 kg.',
                    'fonte': 'fonte_teste', 'confianca': 0.95}, agora=100,
    )
    fala = 'O relatório afirma: "O primeiro aparelho pesa 70 kg. O segundo pesa 80 kg."'
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=base, agora=100)
    assert 'medida_sem_evidencia' in resultado['problemas'], resultado
    assert any('80 kg' in t for t in resultado['trechos_rejeitados'])


def test_descricao_na_citacao_nao_herda_fonte_do_candidato_anterior():
    from mente_laylay.cognicao.fundamentacao_factual import montar_fundamentacao
    base = montar_fundamentacao(
        'candidatos de filmes', {'ok': True, 'resumo': 'Obra Observada',
            'candidatos': ['Obra Observada'], 'fonte': 'fonte_teste', 'confianca': 0.95},
        agora=100,
    )
    fala = 'O relatório afirma: "Obra Observada. A atuação é excelente."'
    resultado = validar_fala_com_fundamentacao(fala, fundamentacao=base, agora=100)
    assert 'descricao_obra_sem_evidencia' in resultado['problemas'], resultado


@pytest.mark.parametrize('prefixo', ['Eu diria', 'Eu responderia', 'Diga'])
def test_predicacao_nominal_fora_das_aspas_tipifica_obra(prefixo):
    fala = f'{prefixo}: "Lua Que Nunca Existiu" é um filme.'
    assert extrair_titulos_citados(fala) == ['Lua Que Nunca Existiu']
    assert 'obra_sem_evidencia' in revisar(fala)['problemas']


@pytest.mark.parametrize('entrada,fala', [
    ('Como você responderia a uma ideia ruim sem diminuir a pessoa?',
     f'Eu responderia: "{EXEMPLO}"'),
    ('Como eu poderia pedir para pausar a música?',
     'Você pode dizer: "pausa a música".'),
])
def test_composicao_preserva_exemplo_sem_converte_lo_em_comando(entrada, fala):
    from scripts.tests.test_papo_casual_composicao import coletar, proposta
    dados = coletar({'entrada': entrada, 'historico': []}, [proposta(fala)])
    assert dados['resposta']['texto'] == fala, dados
    assert dados['http'] == 1 and not dados['resposta']['degradada']


def test_composicao_publica_reparo_historico_inteiro_com_historico_real():
    from scripts.tests.test_papo_casual_composicao import coletar, proposta
    dados = coletar(CASO, [proposta(CASO['fala'])])
    assert dados['resposta']['tipo'] == 'resposta', dados
    assert dados['resposta']['texto'] == CASO['fala'], dados
    assert dados['http'] == 1 and not dados['resposta']['degradada']
    assert not dados['orcamento']['chamadas_bloqueadas']
