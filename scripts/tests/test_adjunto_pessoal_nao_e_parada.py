"""Preposição com pronome não vira comando ao separar a oração na vírgula."""
import pytest

from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno, fontes_textuais_dos_segmentos

HISTORICA=('Mudando um pouco de assunto: imagine que duas pessoas defendem opiniões diferentes, mas ambas acham que estão certas. '
    'Para você, o que mostra mais maturidade: manter uma convicção com firmeza ou conseguir mudar de opinião depois de ouvir bons argumentos?')


@pytest.mark.parametrize('texto',[
    HISTORICA, 'Para você, qual estilo combina comigo?', 'Para mim, qual opção parece melhor?',
    'Pra ti, essa ideia faz sentido?', 'Para nós, como seria a história?',
    'Para ela, isso importa?', 'Para vocês, qual é o melhor desenho?',
    'E para você, qual estilo combina comigo?', 'E, para você, qual estilo combina comigo?',
])
def test_adjunto_pessoal_de_pergunta_nao_ganha_autorizacao_de_parada(texto):
    t=classificar_modalidade_turno(texto)
    assert not t['autoriza_execucao'] and not t['texto_operacional']
    assert not any(s['autoriza_execucao'] for s in t['segmentos'])


@pytest.mark.parametrize('texto',[
    'Para a música agora.', 'Pare o ventilador.', 'Para você de falar disso.',
])
def test_pedido_de_parada_continua_operacional(texto):
    assert classificar_modalidade_turno(texto)['autoriza_execucao']


@pytest.mark.parametrize('texto',[
    'Para mim, abre o aplicativo Calculadora.',
    'Para nós, pausa a música.',
    'Para você, qual parece melhor? Abra o aplicativo Calculadora.',
])
def test_adjunto_nao_apaga_a_autoridade_da_matriz_ou_da_ordem_separada(texto):
    t=classificar_modalidade_turno(texto)
    assert t['autoriza_execucao']
    assert any(s['autoriza_execucao'] for s in t['segmentos'])
    assert not any(s['texto'].casefold().strip(' .') in {'para mim','para nós','para você'}
                   and s['autoriza_execucao'] for s in t['segmentos'])


def test_fontes_da_pergunta_preservam_o_adjunto_e_o_literal_completo():
    texto='Para você, qual estilo combina comigo?'
    t=classificar_modalidade_turno(texto)
    assert len(t['segmentos'])==1
    fontes=fontes_textuais_dos_segmentos(texto,t['segmentos'])
    assert len(fontes)==1 and fontes[0].como_dict()['texto_original']==texto


def test_nome_citado_nao_e_matriz_de_opiniao_nem_pedido_de_parada():
    texto='Abra o arquivo "Para você, o que mostra maturidade.txt".'
    assert classificar_modalidade_turno(texto)['autoriza_execucao']
