"""Expressão de posição não depende de palavras isoladas nem prova fatos."""
import pytest

from tests.test_opiniao_autoral_conferivel import preparar
from tests.test_confirmacao_escopo_ato import ABERTURA
from mente_laylay.cognicao.qualidade_comunicacao import avaliar_qualidade_comunicacao
from mente_laylay.cognicao.validacao_contrato_fala import validar_aderencia_contrato_fala
from mente_laylay.cognicao.plano_turno import verificar_fala_turno

POSICOES = [
    ('O que você pensa sobre perdoar?',
     'Eu vejo o perdão como uma escolha possível, sem exigir a recuperação da confiança.'),
    ('O que você pensa sobre perdoar?',
     'Eu considero o perdão uma escolha possível, sem exigir recuperar a confiança.'),
    ('O que você acha de discordar?',
     'Entendo que discordar pode manter uma conversa honesta.'),
    ('O que você acha de discordar?',
     'Defendo que discordar com cuidado é uma atitude válida.'),
    ('O que você pensa sobre perdoar?',
     'Na minha avaliação, perdoar pode ser uma escolha possível.'),
    ('O que você acha de revisar código?',
     'Do meu ponto de vista, revisar código é uma escolha cuidadosa.'),
    ('O que você pensa de estudar à noite?',
     'Para mim, estudar à noite é uma possibilidade válida.'),
    ('O que você acha de pedir ajuda?',
     'Sou favorável a pedir ajuda quando for preciso.'),
    ('O que você pensa sobre perdoar?',
     'Encaro o perdão como uma escolha, sem exigir confiança imediata.'),
    ('O que você pensa sobre perdoar?',
     'Eu vejo o perdão como uma escolha possível, você concorda?'),
    ('O que você pensa sobre perdoar?',
     'Eu vejo o perdão como "uma escolha possível".'),
]


@pytest.mark.parametrize('pergunta,fala', POSICOES)
def test_posicao_com_predicacao_ou_perspectiva_cumpre_ato(pergunta,fala):
    _,plano,_ = preparar(pergunta)
    q = avaliar_qualidade_comunicacao(pergunta,fala,plano=plano)
    assert q['aceita'], q
    v = validar_aderencia_contrato_fala(pergunta,fala,
        contrato_fala=plano['contrato_fala'],turno_id=plano['id'])
    # Critério concreto é observação consultiva, também para o antigo "acho".
    # Aqui se confere a expressão da posição; não se inventa uma justificativa.
    assert not {'ato_opiniao_nao_respondido','opiniao_nao_veio_na_primeira_frase'}.intersection(v['problemas']), v


def test_saudacao_e_opiniao_combinadas_preservam_o_nucleo_tematico():
    fala = 'Oi! '+POSICOES[0][1]
    _,p,_ = preparar(ABERTURA)
    q = avaliar_qualidade_comunicacao(ABERTURA,fala,plano=p)
    assert q['aceita'],q


@pytest.mark.parametrize('fala,trecho', [
    ('Oi! Eu vejo o perdão como uma escolha possível, você concorda?',
     'Eu vejo o perdão como uma escolha possível'),
    ('Oi, eu vejo o perdão como "uma escolha possível".',
     'eu vejo o perdão como "uma escolha possível"'),
])
def test_localizacao_preserva_offsets_da_matriz_externa(fala,trecho):
    from mente_laylay.cognicao.normalizacao_linguagem import localizar_enunciacao_avaliativa
    m = localizar_enunciacao_avaliativa(fala)
    assert m is not None
    assert fala[m.start():m.end()] == trecho


@pytest.mark.parametrize('fala', [
    'Eu vejo a tela aberta.', 'Ele vê o perdão como uma escolha.',
    'Você considera o perdão uma escolha.', 'Na sua opinião, perdoar é uma escolha.',
    'Na minha opinião.', 'Eu considero o perdão.',
    'Oi! Tudo bem?', 'Como você vê o perdão?',
    'A frase "eu considero o perdão uma escolha" é uma oração.',
    'Eu vejo "o perdão como uma escolha possível".',
    'Eu vejo o perdão como qual escolha?',
    '"Eu vejo o perdão como uma escolha possível", você concorda?',
])
def test_percepcao_relato_citacao_pergunta_e_fragmento_nao_substituem_posicao(fala):
    pergunta = 'O que você pensa sobre perdoar?'
    _,p,_ = preparar(pergunta)
    q = avaliar_qualidade_comunicacao(pergunta,fala,plano=p)
    assert not q['aceita'],q


@pytest.mark.parametrize('fala', [
    'Na minha opinião, apaguei o arquivo notas.txt.',
    'Entendo que consegui abrir o Opera.',
    'Eu vejo a exclusão do arquivo como um sucesso. Consegui apagar notas.txt.',
])
def test_expressao_opinativa_nao_e_receipt_nem_causa_confirmada(fala):
    pergunta = 'O que você pensa sobre apagar arquivos?'
    _,p,_ = preparar(pergunta)
    r = verificar_fala_turno(fala,plano=p)
    assert not r['aceita'] or r['fala'] != fala,r


def test_preferencia_sem_escolha_e_evasao_continuam_bloqueadas():
    pergunta = 'Você prefere rock ou metal?'
    _,p,_ = preparar(pergunta)
    for fala in ['São dois estilos musicais conhecidos.',
                 'Não consigo ouvir música, então não tenho preferência.']:
        assert not avaliar_qualidade_comunicacao(pergunta,fala,plano=p)['aceita']


@pytest.mark.parametrize('atividade,juizo', [
    ('discordar','Defendo que discordar com cuidado é uma atitude válida.'),
    ('revisar código','Entendo que revisar código é uma escolha prudente.'),
])
def test_juizo_normativo_sobre_atividade_nao_e_caracteristica_externa(atividade,juizo):
    from mente_laylay.cognicao.fundamentacao_factual import validar_fala_com_fundamentacao
    r = validar_fala_com_fundamentacao(juizo,fundamentacao={'tema':atividade,'confiavel':False},
                                     texto_usuario=f'O que você acha de {atividade}?')
    assert r['fala']==juizo and not r['problemas'],r


@pytest.mark.parametrize('frase', [
    'Defendo que Nirvana nasceu no Brasil.',
    'Entendo que Nirvana lançou um álbum em 2020.',
    'Defendo que revisar código é uma escolha prudente e que o projeto ganhou 7 milhões.',
])
def test_prefixo_de_juizo_nao_isenta_fato_independente_sem_fonte(frase):
    from mente_laylay.cognicao.fundamentacao_factual import validar_fala_com_fundamentacao
    r = validar_fala_com_fundamentacao(frase,fundamentacao={'tema':'Nirvana','confiavel':False},
                                     texto_usuario='O que você pensa sobre isso?')
    assert r['problemas'] and r['fala']!=frase,r


@pytest.mark.parametrize('tema,frase', [
    ('clínica','Defendo que visitar a clínica gratuita é útil.'),
    ('medicamento','Defendo que usar o medicamento inofensivo é prudente.'),
    ('banco','Defendo que confiar no banco solvente é razoável.'),
    ('banco','Defendo que confiar na solvência do banco é razoável.'),
])
def test_juizo_preserva_obrigacao_dos_atributos_e_relacoes_do_objeto(tema,frase):
    from mente_laylay.cognicao.fundamentacao_factual import validar_fala_com_fundamentacao
    r = validar_fala_com_fundamentacao(frase,fundamentacao={'tema':tema,'confiavel':False},
        texto_usuario=f'O que você pensa sobre {tema}?')
    assert r['problemas'] and r['fala']!=frase,r
