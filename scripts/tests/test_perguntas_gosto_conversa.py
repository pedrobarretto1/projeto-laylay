"""Preferência autoral responde à pergunta; não inicia auditoria nem prova experiência."""
import json
from dataclasses import replace

import pytest

from scripts.tests.test_opiniao_autoral_conferivel import preparar
from mente_laylay.cognicao.referencias_linguagem import consulta_opiniao_propria
from mente_laylay.cognicao.fundamentacao_factual import extrair_tema_fundamentacao
from mente_laylay.cognicao.opiniao_autoral import montar_pacote_opiniao
from mente_laylay.cognicao.plano_turno import verificar_fala_turno
from mente_laylay.cognicao.suporte_autoria import exigir_suporte_no_pacote_autoral


@pytest.mark.parametrize('texto,fala', [
    ('voce tem um jogo favorito?', 'Meu jogo favorito é «Journey».'),
    ('qual é seu filme favorito?', 'Meu filme favorito é «A Rainha do Céu».'),
    ('você tem uma música favorita?', 'Minha música favorita é «Neon Gravitas».'),
])
def test_nome_proposto_sem_alvo_fundamentado_nao_prova_identidade_e_categoria(texto, fala):
    _, plano, _ = preparar(texto)
    assert plano['contrato_fala'].get('opiniao_autoral') is not None
    assert not verificar_fala_turno(fala, plano=plano)['aceita']


def test_publicacao_anterior_livre_nao_qualifica_a_categoria_do_titulo():
    texto = 'voce tem um jogo favorito?'
    fala = 'Meu jogo favorito é «Nome Proposto». '
    _, plano, _ = preparar(texto, fala.strip(), texto)
    assert not verificar_fala_turno(fala.strip(), plano=plano)['aceita']


@pytest.mark.parametrize('texto', [
    'voce tem um jogo favorito?', 'qual é seu filme favorito?',
    'você tem uma música favorita?', 'qual o teu livro preferido?',
    'to so perguntando se voce gosta de algun jogo?',
    'Estou apenas perguntando se você gosta de algum filme?',
    'voce gosta d emusica?', 'você curte d erock?',
])
def test_leitor_compartilhado_reconhece_pergunta_pessoal_integral(texto):
    assert consulta_opiniao_propria(texto) is not None
    assert extrair_tema_fundamentacao(texto, retrato={
        'referencia_resolvida': {'nome': 'Favorito', 'tipo': 'entidade'},
    }) == ''
    turno, plano, _ = preparar(texto)
    assert turno['autoriza_execucao'] is False
    assert plano['contrato_fala'].get('opiniao_autoral') is not None


@pytest.mark.parametrize('texto,fala', [
    ('voce tem um jogo favorito?', 'Ainda não escolhi um jogo favorito.'),
    ('qual é seu filme favorito?', 'Ainda não escolhi um filme favorito.'),
    ('você tem uma música favorita?', 'Ainda não escolhi uma música favorita.'),
    ('qual o teu livro preferido?', 'Ainda não escolhi um livro favorito.'),
    ('to so perguntando se voce gosta de algun jogo?', 'Eu gosto de jogos.'),
    ('voce gosta d emusica?', 'Eu gosto de musica.'),
])
def test_autoria_escolhe_sem_fonte_e_revisao_final_conserva_resposta(texto, fala):
    _, plano, _ = preparar(texto)
    pacote = montar_pacote_opiniao(texto, contrato=plano['contrato_fala'], turno_id=plano['id'])
    assert pacote is not None
    pacote = exigir_suporte_no_pacote_autoral(pacote)
    resposta = pacote.contrato_saida.decodificar_json(json.dumps({
        'suporte_proposicoes': [{'texto': fala, 'fontes': []}],
        'comandos': [], 'criterio_autoral': 'curiosidade',
    }))
    assert resposta['fala'] == fala
    revisao = verificar_fala_turno(fala, plano=plano)
    assert revisao['aceita'] and revisao['fala'] == fala, revisao
    fonte = plano['contrato_fala']['opiniao_autoral']
    assert fonte.prova_factual is False and fonte.autoriza_execucao is False


@pytest.mark.parametrize('fala', [
    'Meu jogo favorito é Hollow Knight porque joguei ontem.',
    'Meu jogo favorito é Hollow Knight.',
    'Meu jogo favorito é Hollow Knight e joguei ontem.',
    'Meu jogo favorito é Hollow Knight e tenho acesso agora.',
    'Meu jogo favorito é Hollow Knight e é muito bom.',
    'Meu jogo favorito é «Hollow Knight» e joguei ontem.',
    'Meu jogo favorito é Hollow Knight. Vejo sua tela agora.',
    'Meu filme favorito é Hollow Knight.',
    'Não consegui verificar se as fontes citadas sustentam essas afirmações.',
    'Não tenho experiência com jogos, só consigo ver o que você está jogando.',
    'Meu jogo favorito é «' + 'A'*190 + '».',
])
def test_preferencia_nao_autoriza_causa_capacidade_ou_desvio_tecnico(fala):
    texto = 'voce tem um jogo favorito?'
    _, plano, _ = preparar(texto)
    assert plano['contrato_fala'].get('opiniao_autoral') is not None
    assert not verificar_fala_turno(fala, plano=plano)['aceita']


@pytest.mark.parametrize('texto', [
    'O João tem um jogo favorito?', 'qual é o meu filme favorito?',
    'Você tem um jogo favorito? Abre ele.',
    'Estou só perguntando se você gosta de jogos e apaga meus arquivos.',
    'A frase "você tem um jogo favorito?" está correta?',
    'Você gosta d eminem?',
])
def test_leitor_nao_empresta_perspectiva_nem_corrige_fronteira_ambigua(texto):
    assert consulta_opiniao_propria(texto) is None


def test_preferencia_nomeada_publicada_permanece_na_pergunta_equivalente():
    texto = 'voce tem um jogo favorito?'
    fala = 'Ainda não escolhi um jogo favorito.'
    _, plano, _ = preparar(texto, fala, texto)
    assert plano['contrato_fala'].get('opiniao_autoral') is not None
    assert verificar_fala_turno(fala, plano=plano)['aceita']
    assert not verificar_fala_turno('Meu jogo favorito é «Celeste».', plano=plano)['aceita']


def test_opiniao_sem_favorito_preserva_vinculo_de_turno_e_recusa_fonte_proposta():
    texto = 'voce tem um jogo favorito?'
    _, plano, _ = preparar(texto)
    contrato = plano['contrato_fala']
    assert contrato.get('opiniao_autoral') is not None
    pacote = exigir_suporte_no_pacote_autoral(montar_pacote_opiniao(
        texto, contrato=contrato, turno_id=plano['id']))
    with pytest.raises(ValueError):
        pacote.contrato_saida.decodificar_json(json.dumps({
            'suporte_proposicoes': [{'texto': 'Ainda não escolhi um jogo favorito.', 'fontes': ['inventada']}],
            'comandos': [], 'criterio_autoral': 'curiosidade',
        }))
    contrato['opiniao_autoral'] = replace(contrato['opiniao_autoral'], turno_id='outro')
    assert not verificar_fala_turno('Ainda não escolhi um jogo favorito.', plano=plano)['aceita']


def test_favorito_publicado_continua_apos_explicacao_com_criterio_nativo():
    from mente_laylay.cognicao.criterio_autoral import CriterioAutoralEmissao, criterio_publicado_da_fala
    from mente_laylay.memoria_mental.registro_semantico import registrar_fala_observada, selecionar_fala_observada
    from mente_laylay.cognicao.modalidade_turno import classificar_modalidade_turno
    from mente_laylay.cognicao.plano_turno import planejar_turno
    from mente_laylay.cognicao.contrato_fala import construir_contrato_semantico_fala
    fala = 'Ainda não escolhi um jogo favorito.'
    emissao = CriterioAutoralEmissao('origem', 'voce tem um jogo favorito?', fala, 'curiosidade', 'a'*64)
    registro = registrar_fala_observada(None, ocorrencia_id='primeira', turno_id='origem',
        fala=fala, resultados=(), canal='texto_publicado', criterio_autoral=emissao)
    criterio = criterio_publicado_da_fala(registro, selecionar_fala_observada(registro))
    explicacao = fala + ' O critério que registrei para essa escolha foi curiosidade.'
    registro = registrar_fala_observada(registro, ocorrencia_id='segunda', turno_id='explicacao',
        fala=explicacao, resultados=(), canal='texto_publicado', criterio_autoral=criterio)
    texto = 'qual é seu jogo favorito?'
    mente = {'registro_semantico': registro}
    turno = classificar_modalidade_turno(texto)
    plano = planejar_turno(texto, turno=turno, mente=mente)
    plano['contrato_fala'] = construir_contrato_semantico_fala(texto, turno=turno, plano=plano, mente=mente)
    assert montar_pacote_opiniao(texto, contrato=plano['contrato_fala'], turno_id=plano['id']) is not None
    assert verificar_fala_turno(fala, plano=plano)['aceita']
    assert not verificar_fala_turno('Meu jogo favorito é «Hollow Knight».', plano=plano)['aceita']
