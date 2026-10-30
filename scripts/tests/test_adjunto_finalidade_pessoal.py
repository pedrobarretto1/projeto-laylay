"""Finalidade subordinada não concede autoridade de parada ou de efeito."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno

HISTORICA = (
    'Obrigado pelo papo, Laylay. Hoje conversamos sobre confiança, fatos, incerteza '
    'e a personalidade de uma IA. Gostei de suas melhores respostas e também das '
    'correções. Para nos despedirmos, qual princípio você gostaria de manter nas próximas conversas?'
)


@pytest.mark.parametrize('texto', [
    HISTORICA, 'Para nos despedirmos, qual princípio você manteria?',
    'Para eu entender, qual é a diferença?', 'Para nós conversarmos, qual tema prefere?',
    'Pra não nos confundirmos, qual era o assunto?',
    'E para refletirmos, qual princípio você prefere?',
    'E, para nos despedirmos, qual ideia você guardaria?',
    'Para abrir o arquivo, qual permissão é necessária?',
    'Para ler "notas, agora.txt", qual permissão é necessária?',
])
def test_finalidade_nao_vira_parada_nem_ordem_subordinada(texto):
    t = classificar_modalidade_turno(texto)
    assert not t['autoriza_execucao'], t
    assert not t['texto_operacional']


@pytest.mark.parametrize('prefixo,matriz', [
    ('Para descansarmos', 'pausa a música.'),
    ('Para eu ler o arquivo', 'abre o aplicativo Calculadora.'),
    ('Para apagar o arquivo', 'abra o Firefox.'),
    ('E, para conversarmos', 'para a música.'),
])
def test_so_a_matriz_recebe_autoridade(prefixo, matriz):
    t = classificar_modalidade_turno(prefixo + ', ' + matriz)
    assert t['autoriza_execucao'], t
    assert not t['segmentos'][0]['autoriza_execucao']
    assert t['segmentos'][0]['natureza_acao'] == 'adjunto_finalidade'
    assert t['texto_operacional'].casefold().strip() == matriz.casefold()


@pytest.mark.parametrize('texto', [
    'Para a música agora.', 'Para o ventilador, por favor.', 'Para você de falar disso.',
    'Pare de abrir arquivos.', 'Para de conversar e abre o Firefox.',
])
def test_parada_real_nao_e_reclassificada_como_finalidade(texto):
    assert classificar_modalidade_turno(texto)['autoriza_execucao']


def test_literal_no_adjunto_nao_e_cortado_em_sua_virgula():
    t = classificar_modalidade_turno('Para ler "notas, abre o Firefox.txt", pausa a música.')
    assert t['texto_operacional'].casefold() == 'pausa a música.'
    assert t['segmentos'][0]['texto'].casefold() == 'para ler "notas, abre o Firefox.txt"'.casefold()
